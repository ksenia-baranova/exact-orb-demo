"""Exact public HTTP response shapes. Internal models are never serialized here."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


Sign: TypeAlias = Literal[
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
AspectKind: TypeAlias = Literal[
    "conjunction", "semisextile", "sextile", "square", "trine",
    "quincunx", "opposition",
]
AspectCategory: TypeAlias = Literal["exact", "working", "background"]


class PublicDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)


class SessionBootstrapRequestDTO(PublicDTO):
    """OpenAPI shape; raw body validation stays in RequestBoundary."""


class BuildNatalRequestDTO(PublicDTO):
    birth_date: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    birth_time: str | None = Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
    place_id: str = Field(min_length=1, max_length=128)


class BirthPlaceDTO(PublicDTO):
    place_id: str
    display_name: str


class BirthWarningDTO(PublicDTO):
    source: Literal["place", "time"]
    code: str


class BirthViewDTO(PublicDTO):
    birth_date: str
    birth_time: str | None
    place: BirthPlaceDTO
    tz_id: str
    utc_offset_seconds: int | None
    time_unknown: bool
    warnings: tuple[BirthWarningDTO, ...]


class PointDTO(PublicDTO):
    id: str
    longitude: float
    sign: Sign
    degree: int = Field(ge=0, le=29)
    minute: int = Field(ge=0, le=59)
    house: int | None = Field(default=None, ge=1, le=12)
    retrograde: bool


class AngleDTO(PublicDTO):
    longitude: float
    sign: Sign
    degree: int = Field(ge=0, le=29)
    minute: int = Field(ge=0, le=59)


class AnglesDTO(PublicDTO):
    asc: AngleDTO
    mc: AngleDTO
    vertex: AngleDTO
    dsc: AngleDTO
    ic: AngleDTO


class HouseDTO(PublicDTO):
    number: int = Field(ge=1, le=12)
    cusp_longitude: float
    sign: Sign
    degree: int = Field(ge=0, le=29)
    minute: int = Field(ge=0, le=59)


class AspectDTO(PublicDTO):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    type: AspectKind
    orb: float
    category: AspectCategory


class ChartDTO(PublicDTO):
    chart_identity: str
    kind: Literal["natal", "cosmogram"]
    zodiac: Literal["tropical"]
    house_system: str | None
    points: tuple[PointDTO, ...]
    angles: AnglesDTO | None
    houses: tuple[HouseDTO, ...] | None
    aspects: tuple[AspectDTO, ...]

    @model_validator(mode="after")
    def _kind_shape(self) -> "ChartDTO":
        if self.kind == "cosmogram":
            if self.house_system is not None or self.angles is not None or self.houses is not None:
                raise ValueError("cosmogram has no houses or angles")
            if any(point.house is not None for point in self.points):
                raise ValueError("cosmogram points have no house")
        elif self.house_system is None or self.angles is None or self.houses is None:
            raise ValueError("natal chart requires houses and angles")
        return self


class SessionBootstrapDTO(PublicDTO):
    status: Literal["ready"] = "ready"
    state_version: int


class SessionEmptyDTO(PublicDTO):
    status: Literal["empty"] = "empty"
    state_version: int
    birth: None = None
    chart: None = None
    chart_stale: None = None


class SessionReadyDTO(PublicDTO):
    status: Literal["chart_ready"] = "chart_ready"
    state_version: int
    birth: BirthViewDTO
    chart: ChartDTO
    chart_stale: bool


class SessionUnavailableDTO(PublicDTO):
    status: Literal["chart_unavailable"] = "chart_unavailable"
    state_version: int
    birth: BirthViewDTO
    chart: None = None
    chart_stale: None = None


SessionViewDTO: TypeAlias = SessionEmptyDTO | SessionReadyDTO | SessionUnavailableDTO


class PlaceSuggestionDTO(PublicDTO):
    place_id: str
    display_name: str
    admin1_name: str | None
    country_code: str


class PlaceSuggestionsDTO(PublicDTO):
    items: tuple[PlaceSuggestionDTO, ...]


class BuildReadyDTO(PublicDTO):
    status: Literal["chart_ready"] = "chart_ready"
    state_version: int
    chart: ChartDTO


class BuildAlreadyAppliedDTO(PublicDTO):
    status: Literal["already_applied"] = "already_applied"
    state_version: int


BuildChartResponseDTO: TypeAlias = BuildReadyDTO | BuildAlreadyAppliedDTO


class IssueDTO(PublicDTO):
    field: str
    code: Literal["MISSING", "AMBIGUOUS", "INVALID", "UNSUPPORTED"]
    candidates: tuple[int | str, ...] | None = None
    constraints: dict[str, int | float | str] | None = None


class ErrorDTO(PublicDTO):
    code: str
    detail_code: str | None
    user_message: str
    retryable: bool
    state_version: int | None = None
    issues: tuple[IssueDTO, ...] | None = None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump(*args, **kwargs)


__all__ = [
    "AngleDTO", "AnglesDTO", "AspectDTO", "BirthViewDTO", "BuildAlreadyAppliedDTO",
    "BuildChartResponseDTO", "BuildNatalRequestDTO", "BuildReadyDTO", "ChartDTO", "ErrorDTO", "HouseDTO",
    "IssueDTO", "PlaceSuggestionDTO", "PlaceSuggestionsDTO", "PointDTO",
    "SessionBootstrapDTO", "SessionBootstrapRequestDTO", "SessionEmptyDTO", "SessionReadyDTO", "SessionUnavailableDTO",
    "SessionViewDTO",
]
