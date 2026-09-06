"""Immutable contracts for de-identified Research records and quality events."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
import json
import math
from types import MappingProxyType
from typing import Annotated, Any, Final, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator, model_validator


RESEARCH_DIGEST_FORMAT_VERSION: Final[Literal[1]] = 1
FEATURE_SCHEMA_VERSION: Final[Literal[1]] = 1
IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:/+@~\-]{0,127}$"
BoundedIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN),
]


class ResearchChartKind(str, Enum):
    NATAL = "natal"
    COSMOGRAM = "cosmogram"


class ResearchTopic(str, Enum):
    NATAL = "natal"


class ResearchFocus(str, Enum):
    GENERAL = "general"
    CAREER = "career"
    MONEY = "money"
    LOVE = "love"


class ZodiacSign(str, Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


class BodyPoint(str, Enum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    CHIRON = "chiron"
    TRUE_NODE = "true_node"
    MEAN_APOG = "mean_apog"
    SOUTH_NODE = "south_node"
    PARS_FORTUNE = "pars_fortune"
    SELENA = "selena"


class AnglePoint(str, Enum):
    ASC = "asc"
    MC = "mc"


class StrengthPoint(str, Enum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"


class RelationalPoint(str, Enum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    CHIRON = "chiron"
    TRUE_NODE = "true_node"
    MEAN_APOG = "mean_apog"
    SOUTH_NODE = "south_node"
    PARS_FORTUNE = "pars_fortune"
    SELENA = "selena"
    ASC = "asc"
    MC = "mc"
    VERTEX = "vertex"


BODY_FEATURE_POINTS: Final[frozenset[BodyPoint]] = frozenset(BodyPoint)
ANGLE_FEATURE_POINTS: Final[frozenset[AnglePoint]] = frozenset(AnglePoint)
STRENGTH_POINTS: Final[frozenset[StrengthPoint]] = frozenset(StrengthPoint)
RELATIONAL_POINTS: Final[frozenset[RelationalPoint]] = frozenset(RelationalPoint)


class AspectType(str, Enum):
    CONJUNCTION = "conjunction"
    SEMISEXTILE = "semisextile"
    SEXTILE = "sextile"
    SQUARE = "square"
    TRINE = "trine"
    QUINCUNX = "quincunx"
    OPPOSITION = "opposition"


class AspectCategory(str, Enum):
    EXACT = "exact"
    WORKING = "working"
    BACKGROUND = "background"


class ConfigurationType(str, Enum):
    T_SQUARE = "t_square"
    YOD = "yod"
    BISEXTILE = "bisextile"
    GRAND_CROSS = "grand_cross"
    GRAND_TRINE = "grand_trine"
    TRAPEZE = "trapeze"


class ConfigurationCategory(str, Enum):
    TIGHT = "tight"
    MODERATE = "moderate"
    LOOSE = "loose"


class ConfigurationRole(str, Enum):
    APEX = "apex"
    BASE_1 = "base_1"
    BASE_2 = "base_2"
    CENTER = "center"
    WING_1 = "wing_1"
    WING_2 = "wing_2"
    POINT_1 = "point_1"
    POINT_2 = "point_2"
    POINT_3 = "point_3"
    AXIS_1_A = "axis_1_a"
    AXIS_1_B = "axis_1_b"
    AXIS_2_A = "axis_2_a"
    AXIS_2_B = "axis_2_b"
    OPPOSITION_1 = "opposition_1"
    OPPOSITION_2 = "opposition_2"


CONFIGURATION_ROLE_SETS: Final[Mapping[ConfigurationType, frozenset[ConfigurationRole]]] = MappingProxyType({
    ConfigurationType.T_SQUARE: frozenset(
        {ConfigurationRole.APEX, ConfigurationRole.BASE_1, ConfigurationRole.BASE_2}
    ),
    ConfigurationType.YOD: frozenset(
        {ConfigurationRole.APEX, ConfigurationRole.BASE_1, ConfigurationRole.BASE_2}
    ),
    ConfigurationType.BISEXTILE: frozenset(
        {ConfigurationRole.CENTER, ConfigurationRole.WING_1, ConfigurationRole.WING_2}
    ),
    ConfigurationType.GRAND_TRINE: frozenset(
        {ConfigurationRole.POINT_1, ConfigurationRole.POINT_2, ConfigurationRole.POINT_3}
    ),
    ConfigurationType.GRAND_CROSS: frozenset(
        {
            ConfigurationRole.AXIS_1_A,
            ConfigurationRole.AXIS_1_B,
            ConfigurationRole.AXIS_2_A,
            ConfigurationRole.AXIS_2_B,
        }
    ),
    ConfigurationType.TRAPEZE: frozenset(
        {
            ConfigurationRole.OPPOSITION_1,
            ConfigurationRole.OPPOSITION_2,
            ConfigurationRole.BASE_1,
            ConfigurationRole.BASE_2,
        }
    ),
})


class DignitySystem(str, Enum):
    TRADITIONAL = "traditional"
    MODERN = "modern"


class DignityStatus(str, Enum):
    DOMICILE = "domicile"
    EXALTATION = "exaltation"
    DETRIMENT = "detriment"
    FALL = "fall"
    PEREGRINE = "peregrine"


class StrengthCategory(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class HouseType(str, Enum):
    ANGULAR = "angular"
    SUCCEDENT = "succedent"
    CADENT = "cadent"


class Element(str, Enum):
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class Modality(str, Enum):
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


class BalanceState(str, Enum):
    DEFICIT = "deficit"
    BALANCED = "balanced"
    EXCESS = "excess"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BodyFeature(_FrozenModel):
    point: BodyPoint
    sign: ZodiacSign
    house: int | None = Field(default=None, ge=1, le=12)
    retrograde: bool


class AngleFeature(_FrozenModel):
    point: AnglePoint
    sign: ZodiacSign


class AspectFeature(_FrozenModel):
    from_point: RelationalPoint
    to_point: RelationalPoint
    aspect_type: AspectType
    category: AspectCategory

    @model_validator(mode="before")
    @classmethod
    def _orient_endpoints(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data
        values = dict(data)
        left = values.get("from_point")
        right = values.get("to_point")
        left_value = left.value if isinstance(left, Enum) else left
        right_value = right.value if isinstance(right, Enum) else right
        if isinstance(left_value, str) and isinstance(right_value, str) and left_value > right_value:
            values["from_point"], values["to_point"] = right, left
        return values

    @model_validator(mode="after")
    def _endpoints_must_differ(self) -> "AspectFeature":
        if self.from_point is self.to_point:
            raise ValueError("aspect endpoints must differ")
        return self


class ConfigurationPointFeature(_FrozenModel):
    role: ConfigurationRole
    point: RelationalPoint


class ConfigurationFeature(_FrozenModel):
    configuration_type: ConfigurationType
    category: ConfigurationCategory
    points: tuple[ConfigurationPointFeature, ...]
    element: Element | None = None
    modality: Modality | None = None

    @field_validator("points")
    @classmethod
    def _canonical_points(
        cls,
        value: tuple[ConfigurationPointFeature, ...],
    ) -> tuple[ConfigurationPointFeature, ...]:
        return tuple(sorted(value, key=lambda item: (item.role.value, item.point.value)))

    @model_validator(mode="after")
    def _roles_and_points_must_match_type(self) -> "ConfigurationFeature":
        roles = tuple(item.role for item in self.points)
        points = tuple(item.point for item in self.points)
        if len(set(roles)) != len(roles):
            raise ValueError("configuration roles must be unique")
        if frozenset(roles) != CONFIGURATION_ROLE_SETS[self.configuration_type]:
            raise ValueError("configuration roles do not match configuration_type")
        if len(set(points)) != len(points):
            raise ValueError("configuration points must be unique")
        return self


class DignityFeature(_FrozenModel):
    point: StrengthPoint
    system: DignitySystem
    status: DignityStatus


class StrengthFeature(_FrozenModel):
    point: StrengthPoint
    category: StrengthCategory
    house_type: HouseType


class ElementBalanceFeature(_FrozenModel):
    axis: Literal["element"]
    bucket: Element
    state: BalanceState


class ModalityBalanceFeature(_FrozenModel):
    axis: Literal["modality"]
    bucket: Modality
    state: BalanceState


BalanceFeature = Annotated[
    ElementBalanceFeature | ModalityBalanceFeature,
    Field(discriminator="axis"),
]


class LunarPhaseFeature(_FrozenModel):
    phase_number: int = Field(ge=1, le=8)


def _none_before(value: int | str | None) -> tuple[int, int | str]:
    return (0, 0) if value is None else (1, value)


_T = TypeVar("_T")


def _ensure_unique(
    values: tuple[_T, ...],
    *,
    key: Any,
    label: str,
) -> tuple[_T, ...]:
    observed = [key(value) for value in values]
    if len(set(observed)) != len(observed):
        raise ValueError(f"{label} must be unique")
    return values


class ChartFeatures(_FrozenModel):
    feature_schema_version: Literal[1] = FEATURE_SCHEMA_VERSION
    chart_kind: ResearchChartKind
    bodies: tuple[BodyFeature, ...] | None = None
    angles: tuple[AngleFeature, ...] | None = None
    aspects: tuple[AspectFeature, ...] | None = None
    configurations: tuple[ConfigurationFeature, ...] | None = None
    dignities: tuple[DignityFeature, ...] | None = None
    strengths: tuple[StrengthFeature, ...] | None = None
    balance: tuple[BalanceFeature, ...] | None = None
    lunar_phase: LunarPhaseFeature | None = None

    @field_validator("bodies")
    @classmethod
    def _canonical_bodies(
        cls,
        value: tuple[BodyFeature, ...] | None,
    ) -> tuple[BodyFeature, ...] | None:
        if value is None:
            return None
        canonical = tuple(
            sorted(
                value,
                key=lambda item: (
                    item.point.value,
                    item.sign.value,
                    _none_before(item.house),
                    item.retrograde,
                ),
            )
        )
        return _ensure_unique(canonical, key=lambda item: item.point, label="body points")

    @field_validator("angles")
    @classmethod
    def _canonical_angles(
        cls,
        value: tuple[AngleFeature, ...] | None,
    ) -> tuple[AngleFeature, ...] | None:
        if value is None:
            return None
        canonical = tuple(sorted(value, key=lambda item: (item.point.value, item.sign.value)))
        return _ensure_unique(canonical, key=lambda item: item.point, label="angle points")

    @field_validator("aspects")
    @classmethod
    def _canonical_aspects(
        cls,
        value: tuple[AspectFeature, ...] | None,
    ) -> tuple[AspectFeature, ...] | None:
        if value is None:
            return None
        return tuple(
            sorted(
                value,
                key=lambda item: (
                    item.from_point.value,
                    item.to_point.value,
                    item.aspect_type.value,
                    item.category.value,
                ),
            )
        )

    @field_validator("configurations")
    @classmethod
    def _canonical_configurations(
        cls,
        value: tuple[ConfigurationFeature, ...] | None,
    ) -> tuple[ConfigurationFeature, ...] | None:
        if value is None:
            return None
        return tuple(
            sorted(
                value,
                key=lambda item: (
                    item.configuration_type.value,
                    item.category.value,
                    tuple((point.role.value, point.point.value) for point in item.points),
                    _none_before(item.element.value if item.element is not None else None),
                    _none_before(item.modality.value if item.modality is not None else None),
                ),
            )
        )

    @field_validator("dignities")
    @classmethod
    def _canonical_dignities(
        cls,
        value: tuple[DignityFeature, ...] | None,
    ) -> tuple[DignityFeature, ...] | None:
        if value is None:
            return None
        canonical = tuple(
            sorted(value, key=lambda item: (item.point.value, item.system.value, item.status.value))
        )
        return _ensure_unique(
            canonical,
            key=lambda item: item.point,
            label="dignity points",
        )

    @field_validator("strengths")
    @classmethod
    def _canonical_strengths(
        cls,
        value: tuple[StrengthFeature, ...] | None,
    ) -> tuple[StrengthFeature, ...] | None:
        if value is None:
            return None
        canonical = tuple(
            sorted(value, key=lambda item: (item.point.value, item.category.value, item.house_type.value))
        )
        return _ensure_unique(canonical, key=lambda item: item.point, label="strength points")

    @field_validator("balance")
    @classmethod
    def _canonical_balance(
        cls,
        value: tuple[BalanceFeature, ...] | None,
    ) -> tuple[BalanceFeature, ...] | None:
        if value is None:
            return None
        canonical = tuple(
            sorted(value, key=lambda item: (item.axis, item.bucket.value, item.state.value))
        )
        return _ensure_unique(
            canonical,
            key=lambda item: (item.axis, item.bucket.value),
            label="balance axis/bucket pairs",
        )

    @model_validator(mode="after")
    def _dignities_must_share_one_system(self) -> "ChartFeatures":
        if self.dignities is not None and len({item.system for item in self.dignities}) > 1:
            raise ValueError("dignities must use one system")
        return self


class ResearchSelection(_FrozenModel):
    topic: ResearchTopic
    focus: ResearchFocus


def _utc_hour(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must have zero UTC offset")
    if value.minute or value.second or value.microsecond:
        raise ValueError("timestamp must be rounded to the UTC hour")
    return value.replace(tzinfo=timezone.utc)


def floor_to_utc_hour(value: datetime, /) -> datetime:
    """Round an aware zero-offset timestamp down to an exact UTC hour."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must have zero UTC offset")
    return value.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _non_negative_finite(value: float) -> float:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("metric must be finite and non-negative")
    return 0.0 if value == 0.0 else value


class ResearchRecord(_FrozenModel):
    research_id: UUID4
    created_at: datetime
    calculation_version: BoundedIdentifier
    chart_features: ChartFeatures
    selection: ResearchSelection
    recipe_version: BoundedIdentifier
    model: BoundedIdentifier
    tokens_in: int | None = Field(default=None, ge=0)
    tokens_out: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    latency_ms: float = Field(ge=0.0, allow_inf_nan=False)

    @field_validator("created_at")
    @classmethod
    def _created_at_must_be_utc_hour(cls, value: datetime) -> datetime:
        return _utc_hour(value)

    @field_validator("cost_usd")
    @classmethod
    def _normalize_optional_metric(cls, value: float | None) -> float | None:
        return None if value is None else _non_negative_finite(value)

    @field_validator("latency_ms")
    @classmethod
    def _normalize_required_metric(cls, value: float) -> float:
        return _non_negative_finite(value)


class _QualityEvent(_FrozenModel):
    event_id: UUID4
    research_id: UUID4
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def _observed_at_must_be_utc_hour(cls, value: datetime) -> datetime:
        return _utc_hour(value)


class RatingEvent(_QualityEvent):
    kind: Literal["rating"]
    rating: int = Field(ge=1, le=5)


class RegenerateEvent(_QualityEvent):
    kind: Literal["regenerate"]


class CopyEvent(_QualityEvent):
    kind: Literal["copy"]


class ReadingTimeEvent(_QualityEvent):
    kind: Literal["reading_time"]
    reading_time_ms: int = Field(ge=0)


ResearchQualityEvent = Annotated[
    RatingEvent | RegenerateEvent | CopyEvent | ReadingTimeEvent,
    Field(discriminator="kind"),
]


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        normalized = _utc_hour(value)
        return normalized.strftime("%Y-%m-%dT%H:00:00Z")
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, float):
        return _non_negative_finite(value)
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _canonical_value(payload),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def record_content_digest(record: ResearchRecord, /) -> str:
    """Return the v1 content digest, excluding only ``research_id``."""

    payload = record.model_dump(mode="python", exclude={"research_id"})
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def event_content_digest(event: ResearchQualityEvent, /) -> str:
    """Return the v1 content digest, excluding only ``event_id``."""

    payload = event.model_dump(mode="python", exclude={"event_id"})
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


__all__ = [
    "ANGLE_FEATURE_POINTS",
    "BODY_FEATURE_POINTS",
    "CONFIGURATION_ROLE_SETS",
    "FEATURE_SCHEMA_VERSION",
    "IDENTIFIER_PATTERN",
    "RELATIONAL_POINTS",
    "RESEARCH_DIGEST_FORMAT_VERSION",
    "STRENGTH_POINTS",
    "AngleFeature",
    "AnglePoint",
    "AspectCategory",
    "AspectFeature",
    "AspectType",
    "BalanceFeature",
    "BalanceState",
    "BodyFeature",
    "BodyPoint",
    "ChartFeatures",
    "ConfigurationCategory",
    "ConfigurationFeature",
    "ConfigurationPointFeature",
    "ConfigurationRole",
    "ConfigurationType",
    "CopyEvent",
    "DignityFeature",
    "DignityStatus",
    "DignitySystem",
    "Element",
    "ElementBalanceFeature",
    "HouseType",
    "LunarPhaseFeature",
    "Modality",
    "ModalityBalanceFeature",
    "RatingEvent",
    "ReadingTimeEvent",
    "RegenerateEvent",
    "RelationalPoint",
    "ResearchChartKind",
    "ResearchFocus",
    "ResearchQualityEvent",
    "ResearchRecord",
    "ResearchSelection",
    "ResearchTopic",
    "StrengthCategory",
    "StrengthFeature",
    "StrengthPoint",
    "ZodiacSign",
    "event_content_digest",
    "floor_to_utc_hour",
    "record_content_digest",
]
