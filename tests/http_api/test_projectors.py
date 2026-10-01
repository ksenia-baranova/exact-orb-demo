"""Pure ChartDTO contract checks; these do not need the HTTP app factory."""

from __future__ import annotations

import json
from datetime import date, time
from pathlib import Path

import pytest

from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.codec import (
    ChartArtifactDecodeError,
    decode_chart_artifact,
    encode_chart_artifact,
)
from exact_orb.engine.ephemeris.types import ZodiacPosition
from exact_orb.session.state import new_session
from tests.application.stubs import StubBirthDataResolver, StubChartArtifactPort
from tests.fixtures.calculation import run_context
from tests.http_api.chart_samples import (
    cosmogram_sample, cosmogram_with_excluded_aspects, natal_sample,
)
from tests.http_api.conftest import NOW


GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "chart_dto.json").read_text(encoding="utf-8")
)
POINT_IDS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
    "neptune", "pluto", "chiron", "true_node", "south_node", "mean_apog",
    "selena", "pars_fortune",
)
SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _project(artifact):
    from exact_orb.http_api.projectors import project_chart

    result = project_chart(artifact)
    return result.model_dump(mode="json") if hasattr(result, "model_dump") else result


@pytest.mark.parametrize("kind,sample", (("natal", natal_sample), ("cosmogram", cosmogram_sample)))
def test_chart_dto_exact_golden_and_no_internal_fields(kind: str, sample) -> None:
    artifact = sample()
    before = artifact.model_copy(deep=True)

    result = _project(artifact)

    assert result == GOLDEN[kind]
    assert artifact == before
    assert set(result) == {
        "chart_identity", "kind", "zodiac", "house_system", "points",
        "angles", "houses", "aspects",
    }
    forbidden = (
        "calculation_version", "spec", "latitude", "longitude_speed", "julian_day",
        "ephemeris", "warnings", "payload", "strength", "rulers", "interceptions",
        "configurations", "time_uncertainty", "time_dependent", "retflags", "applying",
    )
    rendered = json.dumps(result)
    assert all(f'"{field}"' not in rendered for field in forbidden)


def test_cosmogram_excluded_aspects_remain_private() -> None:
    artifact = cosmogram_with_excluded_aspects()
    excluded = artifact.chart.time_uncertainty.excluded_aspects
    assert excluded
    result = _project(artifact)
    rendered_pairs = {frozenset((item["from"], item["to"]))
                      for item in result["aspects"]}
    for aspect in excluded:
        pair = frozenset((aspect.from_point.body, aspect.to_point.body))
        assert pair not in rendered_pairs
    assert "excluded_aspects" not in json.dumps(result)


def test_all_published_point_ids_have_fixed_order_and_12_sign_dictionary() -> None:
    baseline = decode_chart_artifact(
        (Path(__file__).resolve().parents[1] / "golden" /
         "chart_artifact_format_1_natal_1985.bin").read_bytes()
    )
    bodies = dict(baseline.chart.bodies)
    for index, name in enumerate(POINT_IDS[:12]):
        old = bodies[name]
        zodiac = ZodiacPosition(
            longitude=index * 30.0 + 5.25,
            sign_index=index,
            sign=SIGNS[index],
            degree_in_sign=5.25,
            degree=5,
            minute=15,
            second=0,
        )
        bodies[name] = old.model_copy(update={"longitude": zodiac.longitude, "zodiac": zodiac})
    # Input order deliberately differs from the public whitelist order.
    scrambled = dict(reversed(list(bodies.items())))
    artifact = baseline.model_copy(update={
        "chart": baseline.chart.model_copy(update={"bodies": scrambled})
    })

    result = _project(artifact)

    assert [point["id"] for point in result["points"]] == list(POINT_IDS)
    assert [point["sign"] for point in result["points"][:12]] == list(SIGNS)
    assert all(set(point) == {"id", "longitude", "sign", "degree", "minute", "house", "retrograde"}
               for point in result["points"])
    assert set(point["sign"] for point in result["points"]) <= set(SIGNS)


def test_unknown_engine_point_and_field_are_not_published() -> None:
    original = natal_sample()
    sample_body = original.chart.bodies["sun"]
    bodies = dict(original.chart.bodies)
    bodies["future_point"] = sample_body.model_copy(update={"name": "future_point"})
    altered_chart = original.chart.model_copy(update={"bodies": bodies, "future_private": "secret"})
    altered = original.model_copy(update={"chart": altered_chart})

    assert _project(altered) == GOLDEN["natal"]
    assert _project(original) == GOLDEN["natal"]


@pytest.mark.parametrize("bad_chart,bad_body", (
    ("transit", "moon"),
    ("natal", "future_point"),
    ("natal", "dsc"),
    ("natal", "ic"),
))
def test_invalid_aspect_owner_or_endpoint_is_refused_with_valid_control(
    bad_chart: str, bad_body: str
) -> None:
    original = natal_sample()
    aspect = original.chart.aspects[0]
    bad_ref = aspect.from_point.model_copy(update={"chart": bad_chart, "body": bad_body})
    bad_aspect = aspect.model_copy(update={"from_point": bad_ref})
    bodies = dict(original.chart.bodies)
    if bad_body == "future_point":
        bodies["future_point"] = bodies["sun"].model_copy(update={"name": "future_point"})
    altered = original.model_copy(update={
        "chart": original.chart.model_copy(update={
            "bodies": bodies, "aspects": (bad_aspect,)
        })
    })

    from exact_orb.http_api.projectors import project_chart

    from exact_orb.http_api.projectors import ChartProjectionError

    with pytest.raises(ChartProjectionError):
        project_chart(altered)
    assert _project(original) == GOLDEN["natal"]


def test_opposite_angles_copy_saved_minutes_at_rounding_boundary() -> None:
    original = natal_sample()
    angles = dict(original.chart.angles)
    for name, sign_index, longitude in (("asc", 3, 119.999999), ("mc", 11, 359.999999)):
        old = angles[name]
        zodiac = ZodiacPosition(
            longitude=longitude,
            sign_index=sign_index,
            sign=SIGNS[sign_index],
            degree_in_sign=29.999999,
            degree=29,
            minute=59,
            second=59,
        )
        angles[name] = old.model_copy(update={"longitude": longitude, "zodiac": zodiac})
    altered = original.model_copy(update={
        "chart": original.chart.model_copy(update={"angles": angles})
    })

    result = _project(altered)["angles"]

    assert result["dsc"]["longitude"] == pytest.approx(299.999999, abs=1e-10)
    assert result["ic"]["longitude"] == pytest.approx(179.999999, abs=1e-10)
    assert {name: (result[name]["sign"], result[name]["degree"], result[name]["minute"])
            for name in ("dsc", "ic")} == {
        "dsc": ("Capricorn", 29, 59), "ic": ("Virgo", 29, 59)
    }
    assert set(result) == {"asc", "mc", "vertex", "dsc", "ic"}
    assert all(set(angle) == {"longitude", "sign", "degree", "minute"}
               for angle in result.values())
    assert _project(original) == GOLDEN["natal"]


def test_chart_sample_goldens_are_model_validated_without_transport() -> None:
    """Passing control ensures RED projector tests use real component artifacts."""
    natal = natal_sample()
    cosmogram = cosmogram_sample()
    assert (natal.chart.chart_kind, cosmogram.chart.chart_kind) == ("natal", "cosmogram")
    assert len(natal.chart.aspects) == 3
    assert len(cosmogram.chart.aspects) == 1
    assert natal.chart.angles is not None
    assert cosmogram.chart.angles is None


def test_stored_forbidden_angle_aspect_reaches_projector_validation() -> None:
    original = natal_sample()
    aspect = original.chart.aspects[0]
    bad_ref = aspect.from_point.model_copy(update={"body": "dsc"})
    bad_aspect = aspect.model_copy(update={"from_point": bad_ref})
    invalid = original.model_copy(update={
        "chart": original.chart.model_copy(update={"aspects": (bad_aspect,)})
    })

    assert decode_chart_artifact(encode_chart_artifact(invalid)) == invalid
    assert decode_chart_artifact(encode_chart_artifact(original)) == original

    truly_dangling = aspect.from_point.model_copy(update={"body": "never_present"})
    broken_aspect = aspect.model_copy(update={"from_point": truly_dangling})
    broken = original.model_copy(update={
        "chart": original.chart.model_copy(update={"aspects": (broken_aspect,)})
    })
    with pytest.raises(ChartArtifactDecodeError) as error:
        decode_chart_artifact(encode_chart_artifact(broken))
    assert error.value.reason == "validation"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ("natal", "cosmogram"))
async def test_full_baseline_artifact_is_accepted_by_real_build_handler(kind: str) -> None:
    """Passing control proves AS-HTTP-11 uses compatible leaf fixtures."""
    baseline = decode_chart_artifact(
        (Path(__file__).resolve().parents[1] / "golden" /
         f"chart_artifact_format_1_{kind}_1985.bin").read_bytes()
    )
    chart = baseline.chart
    resolved = ResolvedBirthData(
        utc_datetime=chart.datetime_utc,
        latitude=chart.latitude,
        longitude=chart.longitude,
        tz_id="Europe/Moscow",
        utc_offset_seconds=14400,
        canonical_place="Москва",
        time_unknown=kind == "cosmogram",
        birth_time_domain=(chart.time_uncertainty.domain
                           if chart.time_uncertainty is not None else None),
        warnings=(),
    )
    artifacts = StubChartArtifactPort(baseline)
    resolver = StubBirthDataResolver(resolved)
    handler = BuildNatalHandler(resolver=resolver, artifacts=artifacts)
    command = BuildNatalCommand(birth_input=BirthInput(
        birth_date=date(1985, 9, 2),
        birth_time=time(0, 45) if kind == "natal" else None,
        place_id="524901",
    ))

    result = await handler.handle(command, new_session("fixture", now=NOW), run_context())

    assert isinstance(result, BuildNatalSuccess)
    assert result.artifact == baseline
    assert resolver.calls == artifacts.calls == artifacts.to_stored_calls == 1
