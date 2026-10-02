"""Pure, explicit projections from application values to public HTTP DTOs."""

from __future__ import annotations

from datetime import date, time

from pydantic import ValidationError

from exact_orb.application.session_view import (
    ChartReadySessionView, ChartUnavailableSessionView, EmptySessionView,
    SessionBirthView, SessionView,
)
from exact_orb.birth.places import PlaceSuggestions
from exact_orb.calculation.types import ChartArtifact
from exact_orb.engine.ephemeris.types import ZODIAC_SIGNS, ZodiacPosition
from exact_orb.http_api.dto import (
    AngleDTO, AnglesDTO, AspectDTO, BirthPlaceDTO, BirthViewDTO, BirthWarningDTO,
    BuildAlreadyAppliedDTO, BuildReadyDTO, ChartDTO, ErrorDTO, HouseDTO,
    PlaceSuggestionDTO, PlaceSuggestionsDTO, PointDTO, SessionBootstrapDTO,
    SessionEmptyDTO, SessionReadyDTO, SessionUnavailableDTO, SessionViewDTO,
)


_POINT_ORDER = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
    "neptune", "pluto", "chiron", "true_node", "south_node", "mean_apog",
    "selena", "pars_fortune",
)
_ANGLE_ASPECT_IDS = frozenset({"asc", "mc", "vertex"})


class ProjectionError(ValueError):
    """A saved or component value violates its approved public DTO."""


class ChartProjectionError(ProjectionError):
    """An artifact cannot be represented as the approved public chart."""


class BirthProjectionError(ProjectionError):
    """Saved birth facts violate the public minute-precision contract."""


def _sign(position: ZodiacPosition) -> str:
    if not isinstance(position.sign_index, int) or not 0 <= position.sign_index < 12:
        raise ChartProjectionError("invalid saved zodiac sign")
    try:
        expected = ZODIAC_SIGNS[position.sign_index]
    except (IndexError, TypeError) as exc:
        raise ChartProjectionError("invalid saved zodiac sign") from exc
    if position.sign != expected:
        raise ChartProjectionError("inconsistent saved zodiac sign")
    return expected


def _angle(position: ZodiacPosition, longitude: float) -> AngleDTO:
    return AngleDTO(
        longitude=longitude,
        sign=_sign(position),
        degree=position.degree,
        minute=position.minute,
    )


def _opposite(position: ZodiacPosition, longitude: float) -> AngleDTO:
    return AngleDTO(
        longitude=(longitude + 180.0) % 360.0,
        sign=ZODIAC_SIGNS[(position.sign_index + 6) % 12],
        degree=position.degree,
        minute=position.minute,
    )


def project_chart(artifact: ChartArtifact) -> ChartDTO:
    """Publish only approved chart fields and validate every aspect endpoint."""

    chart = artifact.chart
    kind = chart.chart_kind
    if kind not in {"natal", "cosmogram"}:
        raise ChartProjectionError("unsupported chart kind")
    bodies = chart.bodies or {}
    points = []
    try:
        for name in _POINT_ORDER:
            body = bodies.get(name)
            if body is None:
                continue
            points.append(PointDTO(
                id=name,
                longitude=body.longitude,
                sign=_sign(body.zodiac),
                degree=body.zodiac.degree,
                minute=body.zodiac.minute,
                house=body.house if kind == "natal" else None,
                retrograde=body.retrograde,
            ))

        if kind == "natal":
            if chart.angles is None or chart.cusps is None:
                raise ChartProjectionError("natal chart lacks angles or houses")
            try:
                asc = chart.angles["asc"]
                mc = chart.angles["mc"]
                vertex = chart.angles["vertex"]
            except KeyError as exc:
                raise ChartProjectionError("natal chart lacks a public angle") from exc
            angles = AnglesDTO(
                asc=_angle(asc.zodiac, asc.longitude),
                mc=_angle(mc.zodiac, mc.longitude),
                vertex=_angle(vertex.zodiac, vertex.longitude),
                dsc=_opposite(asc.zodiac, asc.longitude),
                ic=_opposite(mc.zodiac, mc.longitude),
            )
            houses = tuple(
                HouseDTO(
                    number=cusp.house,
                    cusp_longitude=cusp.longitude,
                    sign=_sign(cusp.zodiac),
                    degree=cusp.zodiac.degree,
                    minute=cusp.zodiac.minute,
                )
                for cusp in sorted(chart.cusps, key=lambda item: item.house)
            )
            house_system = chart.house_system
        else:
            angles = None
            houses = None
            house_system = None

        published_ids = {point.id for point in points}
        if kind == "natal":
            published_ids.update(_ANGLE_ASPECT_IDS)
        aspects = []
        for aspect in chart.aspects or ():
            source = aspect.from_point
            target = aspect.to_point
            if (source.chart != "natal" or target.chart != "natal"
                    or source.body not in published_ids or target.body not in published_ids):
                raise ChartProjectionError("aspect refers to an unpublished point")
            aspects.append(AspectDTO.model_validate({
                "from": source.body,
                "to": target.body,
                "type": aspect.aspect_type.value,
                "orb": aspect.orb,
                "category": aspect.category.value,
            }))

        return ChartDTO(
            chart_identity=artifact.calculation_key,
            kind=kind,
            zodiac="tropical",
            house_system=house_system,
            points=tuple(points),
            angles=angles,
            houses=houses,
            aspects=tuple(aspects),
        )
    except ValidationError as exc:
        raise ChartProjectionError("invalid public chart value") from exc


def project_birth(birth: SessionBirthView) -> BirthViewDTO:
    """Publish saved minute-precision birth facts without noon-anchor details."""

    saved_time = birth.birth_time
    if type(birth.birth_date) is not date or (
        saved_time is not None and type(saved_time) is not time
    ):
        raise BirthProjectionError("saved birth date or time is invalid")
    if birth.time_unknown != (saved_time is None):
        raise BirthProjectionError("saved time_unknown does not match birth input")
    if saved_time is not None and (
        saved_time.second != 0 or saved_time.microsecond != 0 or saved_time.tzinfo is not None
    ):
        raise BirthProjectionError("saved birth time is not minute precision")
    try:
        return BirthViewDTO(
            birth_date=birth.birth_date.isoformat(),
            birth_time=saved_time.strftime("%H:%M") if saved_time is not None else None,
            place=BirthPlaceDTO(
                place_id=birth.place_id,
                display_name=birth.canonical_place,
            ),
            tz_id=birth.tz_id,
            utc_offset_seconds=None if birth.time_unknown else birth.utc_offset_seconds,
            time_unknown=birth.time_unknown,
            warnings=tuple(
                BirthWarningDTO(source="time", code=warning.code)
                for warning in birth.warnings
                if warning.source == "time" and warning.code == "pre_1970_offset_unverified"
            ),
        )
    except ValidationError as exc:
        raise BirthProjectionError("invalid saved birth value") from exc


def project_session_view(view: SessionView) -> SessionViewDTO:
    if isinstance(view, EmptySessionView):
        return SessionEmptyDTO(state_version=view.state_version)
    if isinstance(view, ChartReadySessionView):
        return SessionReadyDTO(
            state_version=view.state_version,
            birth=project_birth(view.birth),
            chart=project_chart(view.artifact),
            chart_stale=view.chart_stale,
        )
    if isinstance(view, ChartUnavailableSessionView):
        return SessionUnavailableDTO(
            state_version=view.state_version,
            birth=project_birth(view.birth),
        )
    raise ProjectionError("unsupported session view")


def project_places(result: PlaceSuggestions) -> PlaceSuggestionsDTO:
    try:
        return PlaceSuggestionsDTO(items=tuple(
            PlaceSuggestionDTO(
                place_id=item.place_id,
                display_name=item.display_name,
                admin1_name=item.admin1_name,
                country_code=item.country_code,
            )
            for item in result.items
        ))
    except ValidationError as exc:
        raise ProjectionError("invalid public place suggestion") from exc


def project_bootstrap(state_version: int) -> SessionBootstrapDTO:
    return SessionBootstrapDTO(state_version=state_version)


def project_build_ready(state_version: int, artifact: ChartArtifact) -> BuildReadyDTO:
    return BuildReadyDTO(state_version=state_version, chart=project_chart(artifact))


def project_build_already_applied(state_version: int) -> BuildAlreadyAppliedDTO:
    return BuildAlreadyAppliedDTO(state_version=state_version)


def internal_failure() -> ErrorDTO:
    """Safe response payload for unexpected projector failure (HTTP 500)."""

    return ErrorDTO(
        code="INTERNAL_FAILURE",
        detail_code=None,
        user_message="Произошла внутренняя ошибка.",
        retryable=False,
    )


__all__ = [
    "BirthProjectionError", "ChartProjectionError", "ProjectionError", "internal_failure", "project_birth",
    "project_bootstrap", "project_build_already_applied", "project_build_ready",
    "project_chart", "project_places", "project_session_view",
]
