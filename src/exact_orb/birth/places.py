"""Place catalog contracts and local JSONL implementation."""

from __future__ import annotations

import json
import os
import unicodedata
from collections.abc import Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError


ALLOWED_ALTERNATE_LANGUAGES = frozenset({"ru"})

PlaceQueryErrorCode = Literal[
    "EMPTY",
    "TOO_LONG",
    "CONTROL_CHARACTERS",
    "NO_SEARCHABLE_CHARACTERS",
]


class PlaceSuggestion(BaseModel):
    """Place identity and display labels without trusted calculation facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    place_id: str
    display_name: str
    admin1_name: str | None
    country_code: str


class PlaceSuggestions(BaseModel):
    """Successful search results, including an empty collection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[PlaceSuggestion, ...]


class InvalidPlaceQuery(BaseModel):
    """A structurally invalid search query, distinct from no matches."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: PlaceQueryErrorCode


PlaceSearchOutcome = PlaceSuggestions | InvalidPlaceQuery


class PlaceSearch(Protocol):
    """Search port for place suggestions from untrusted user text."""

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> PlaceSearchOutcome: ...


def normalize_place_query(query: str) -> str | InvalidPlaceQuery:
    """Build one canonical search key for catalog names and runtime queries."""

    # Check before whitespace folding so controls cannot silently disappear.
    if any(unicodedata.category(char) == "Cc" for char in query):
        return InvalidPlaceQuery(code="CONTROL_CHARACTERS")

    normalized = unicodedata.normalize("NFKC", query)
    normalized = " ".join(normalized.split())
    normalized = normalized.casefold().replace("ё", "е")

    if not normalized:
        return InvalidPlaceQuery(code="EMPTY")
    if len(normalized) > 200:
        return InvalidPlaceQuery(code="TOO_LONG")
    if not any(char.isalnum() for char in normalized):
        return InvalidPlaceQuery(code="NO_SEARCHABLE_CHARACTERS")
    return normalized


class ResolvedPlace(BaseModel):
    """Canonical place facts needed for birth-data resolution."""

    place_id: str
    canonical_name: str
    latitude: float
    longitude: float
    tz_id: str


class PlaceNotFound(BaseModel):
    """The supplied place_id was not present in the catalog."""

    place_id: str


PlaceResolution = ResolvedPlace | PlaceNotFound


class PlaceCatalogUnavailableError(RuntimeError):
    """The place catalog is unavailable: a technical error, not user input."""


class PlaceCatalog(Protocol):
    """Lookup port for trusted place facts by untrusted place_id."""

    async def lookup(self, place_id: str) -> PlaceResolution: ...


class LocalPlaceCatalog:
    """In-memory place catalog loaded from a GeoNames-derived JSONL file."""

    def __init__(self, places: Mapping[str, ResolvedPlace]) -> None:
        self._places = dict(places)

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "LocalPlaceCatalog":
        places: dict[str, ResolvedPlace] = {}
        source = os.fspath(path)

        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON in {source} on line {line_number}"
                    ) from exc

                if not isinstance(record, dict):
                    raise ValueError(
                        f"Invalid place record in {source} on line {line_number}: "
                        "expected JSON object"
                    )

                tz_id = record.get("tz_id")
                if not tz_id:
                    continue

                place = _build_place_record(record, source, line_number)
                places[place.place_id] = place

        return cls(places)

    async def lookup(self, place_id: str) -> PlaceResolution:
        place = self._places.get(place_id)
        if place is None:
            return PlaceNotFound(place_id=place_id)
        return place


def _build_place_record(
    record: dict[str, Any],
    source: str,
    line_number: int,
) -> ResolvedPlace:
    try:
        return ResolvedPlace(
            place_id=str(record["place_id"]),
            canonical_name=record["name"],
            latitude=record["latitude"],
            longitude=record["longitude"],
            tz_id=record["tz_id"],
        )
    except KeyError as exc:
        field = exc.args[0]
        raise ValueError(
            f"Invalid place record in {source} on line {line_number}: "
            f"missing field {field}"
        ) from exc
    except (TypeError, ValidationError) as exc:
        raise ValueError(
            f"Invalid place record in {source} on line {line_number}: {exc}"
        ) from exc


__all__ = [
    "ALLOWED_ALTERNATE_LANGUAGES",
    "InvalidPlaceQuery",
    "LocalPlaceCatalog",
    "PlaceCatalog",
    "PlaceCatalogUnavailableError",
    "PlaceNotFound",
    "PlaceQueryErrorCode",
    "PlaceResolution",
    "PlaceSearch",
    "PlaceSearchOutcome",
    "PlaceSuggestion",
    "PlaceSuggestions",
    "ResolvedPlace",
    "normalize_place_query",
]
