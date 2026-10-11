"""AS-UI-06 controlled catalog leaf: reuse Apia from tests/fixtures/places.jsonl.

The packaged snapshot has no Pacific/Apia place. Only that extra lookup/search
fixture is supplied here; real runtime, resolver, handler, engine, SQLite session,
HTTP validation and projectors run unchanged. Never use as a product factory.
"""
from __future__ import annotations

import json
from pathlib import Path

from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import (PlaceSuggestion, PlaceSuggestions, ResolvedPlace,
                                    normalize_place_query)
from exact_orb.http_server import create_local_app

ROOT = Path(__file__).resolve().parents[3]
APIA = next(json.loads(line) for line in (ROOT / "tests/fixtures/places.jsonl").read_text(
    encoding="utf-8").splitlines() if json.loads(line)["place_id"] == "4035413")
REAL_OPEN = SqlitePlaceCatalog.open


class ApiaFixtureCatalog:
    def __init__(self, catalog):
        self.catalog = catalog

    async def lookup(self, place_id):
        if place_id != APIA["place_id"]:
            return await self.catalog.lookup(place_id)
        return ResolvedPlace(place_id=APIA["place_id"], canonical_name=APIA["name"],
            latitude=round(APIA["latitude"], 2), longitude=round(APIA["longitude"], 2), tz_id=APIA["tz_id"])

    async def search(self, query, *, limit=10):
        normalized = normalize_place_query(query)
        if isinstance(normalized, str) and any(name.casefold().startswith(normalized)
                                              for name in (APIA["name"], APIA["name_ascii"])):
            return PlaceSuggestions(items=(PlaceSuggestion(place_id=APIA["place_id"],
                display_name=APIA["name"], admin1_name=APIA["admin1"], country_code=APIA["country"]),))
        return await self.catalog.search(query, limit=limit)

    async def aclose(self):
        await self.catalog.aclose()


async def open_fixture(*args, **kwargs):
    return ApiaFixtureCatalog(await REAL_OPEN(*args, **kwargs))


def create_fixture_app():
    SqlitePlaceCatalog.open = staticmethod(open_fixture)
    return create_local_app()
