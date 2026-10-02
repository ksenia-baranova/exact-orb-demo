"""Explicit local-only composition for the HTTPS proxy runbook."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import os
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI

from exact_orb.application.bootstrap import BootstrapSettings, build_application_runtime
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import PlaceResolution, PlaceSearchOutcome
from exact_orb.config import get_selena_method_name
from exact_orb.http_api.app import MonotonicScheduler, create_app


class _OwnedCatalog:
    """Close the caller-owned SQLite executor after its catalog connection."""

    def __init__(self, catalog: SqlitePlaceCatalog, executor: ThreadPoolExecutor) -> None:
        self._catalog = catalog
        self._executor = executor

    async def lookup(self, place_id: str) -> PlaceResolution:
        return await self._catalog.lookup(place_id)

    async def search(self, query: str, *, limit: int = 10) -> PlaceSearchOutcome:
        return await self._catalog.search(query, limit=limit)

    async def aclose(self) -> None:
        try:
            await self._catalog.aclose()
        finally:
            await asyncio.to_thread(self._executor.shutdown, wait=True)


def _required(source: Mapping[str, str], name: str) -> str:
    value = source.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required for local HTTP startup")
    return value


def create_local_app(env: Mapping[str, str] | None = None) -> FastAPI:
    """Compose one runtime and catalog; Uvicorn calls this as a factory."""

    source = os.environ if env is None else env
    origin = _required(source, "EXACT_ORB_HTTP_ORIGIN")
    catalog_path = Path(_required(source, "EXACT_ORB_PLACES_DB"))
    schema_flag = source.get("EXACT_ORB_HTTP_EXPOSE_SCHEMA", "0")
    if schema_flag not in {"0", "1"}:
        raise ValueError("EXACT_ORB_HTTP_EXPOSE_SCHEMA must be 0 or 1")
    runtime_settings = BootstrapSettings(
        ephemeris_path=Path(_required(source, "EXACT_ORB_EPHEMERIS_PATH")),
        selena_method=get_selena_method_name(
            _required(source, "EXACT_ORB_SELENA_METHOD"),
        ),
        session_db_path=Path(_required(source, "EXACT_ORB_SESSION_DB")),
        sqlite_busy_timeout_ms=250,
        sqlite_max_workers=1,
        min_birth_date=date(1800, 1, 1),
        max_birth_date=date(2399, 12, 31),
        cache_max_entries=32,
        cache_ttl_seconds=None,
        engine_slow_threshold_ms=3_000.0,
        degraded_log_interval_s=60.0,
    )
    http_settings = SimpleNamespace(
        allowed_origins=(origin,),
        trusted_proxy_cidrs=("127.0.0.1/32",),
        public_origin=origin,
        body_timeout_seconds=5.0,
        build_timeout_seconds=30.0,
        shutdown_grace_seconds=30.0,
        reaper_interval_seconds=900.0,
        max_body_bytes=16 * 1024,
        expose_schema=schema_flag == "1",
    )

    async def open_catalog() -> _OwnedCatalog:
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="exact-orb-place")
        try:
            catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        except BaseException:
            await asyncio.to_thread(executor.shutdown, wait=True)
            raise
        return _OwnedCatalog(catalog, executor)

    def utc_clock() -> datetime:
        return datetime.now(timezone.utc)

    return create_app(
        settings=http_settings,
        runtime_factory=lambda catalog: build_application_runtime(
            settings=runtime_settings, places=catalog, clock=utc_clock,
        ),
        catalog_factory=open_catalog,
        utc_clock=utc_clock,
        scheduler=MonotonicScheduler(),
    )
