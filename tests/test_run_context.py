"""Tests for RunContext correlation logging in birth resolution."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from exact_orb.birth import (
    BirthDataResolver,
    BirthInput,
    LocalPlaceCatalog,
    ResolvedBirthData,
)
from exact_orb.outcomes import InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext


MOSCOW_ID = "524901"
BROKEN_TZ_ID = "9000001"
UNKNOWN_PLACE_ID = "999999999"
TODAY = date(2026, 8, 27)
MIN_DATE = date(1800, 1, 1)
MAX_DATE = date(2399, 12, 31)
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "places.jsonl"
RESOLVER_LOGGER = "exact_orb.birth.resolver"


@pytest.fixture
def resolver() -> BirthDataResolver:
    return BirthDataResolver(
        places=LocalPlaceCatalog.from_file(FIXTURE_PATH),
        min_birth_date=MIN_DATE,
        max_birth_date=MAX_DATE,
        today_provider=lambda: TODAY,
    )


def test_run_context_new_uses_uuid_and_utc_started_at() -> None:
    run = RunContext.new()

    assert isinstance(run.run_id, UUID)
    assert run.started_at.utcoffset() == timezone.utc.utcoffset(run.started_at)


def test_run_context_new_generates_distinct_run_ids() -> None:
    first = RunContext.new()
    second = RunContext.new()

    assert first.run_id != second.run_id


def test_run_context_rejects_naive_started_at() -> None:
    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        RunContext(run_id=RunContext.new().run_id, started_at=datetime(2026, 8, 28))


async def test_resolve_without_run_matches_resolve_with_run(
    resolver: BirthDataResolver,
) -> None:
    birth_input = BirthInput(
        birth_date=date(1990, 9, 2),
        birth_time=time(14, 30),
        place_id=MOSCOW_ID,
    )

    without_run = await resolver.resolve(birth_input)
    with_run = await resolver.resolve(birth_input, run=RunContext.new())

    assert without_run == with_run


async def test_success_logs_start_and_resolved_with_run_id(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    run = RunContext.new()

    with _capture_resolver_logs(caplog):
        result = await resolver.resolve(
            BirthInput(
                birth_date=date(1990, 9, 2),
                birth_time=time(14, 30),
                place_id=MOSCOW_ID,
            ),
            run=run,
        )

    assert isinstance(result, ResolvedBirthData)
    messages = _resolver_messages(caplog)
    assert len(messages) == 4
    assert f"run_id={run.run_id}" in messages[0]
    assert "direction=in" in messages[0]
    assert "message_type=BirthResolutionRequest" in messages[0]
    assert "event=start" in messages[1]
    assert f"run_id={run.run_id}" in messages[2]
    assert "outcome=resolved" in messages[2]
    assert "tz_id=Europe/Moscow" in messages[2]
    assert "direction=out" in messages[3]
    assert "message_type=ResolvedBirthData" in messages[3]


async def test_input_required_logs_run_id_and_issues(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    run = RunContext.new()

    with _capture_resolver_logs(caplog):
        result = await resolver.resolve(
            BirthInput(birth_date=date(1990, 9, 2), place_id=UNKNOWN_PLACE_ID),
            run=run,
        )

    assert isinstance(result, InputRequired)
    messages = _resolver_messages(caplog)
    assert len(messages) == 4
    assert f"run_id={run.run_id}" in messages[0]
    assert "direction=in" in messages[0]
    assert "event=start" in messages[1]
    assert f"run_id={run.run_id}" in messages[2]
    assert "outcome=input_required" in messages[2]
    assert "issues=birth.place:INVALID" in messages[2]
    assert "direction=out" in messages[3]
    assert "message_type=InputRequired" in messages[3]


async def test_resolution_unavailable_logs_run_id_and_error_code(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    run = RunContext.new()

    with _capture_resolver_logs(caplog):
        result = await resolver.resolve(
            BirthInput(birth_date=date(1990, 9, 2), place_id=BROKEN_TZ_ID),
            run=run,
        )

    assert isinstance(result, ResolutionUnavailable)
    messages = _resolver_messages(caplog)
    assert len(messages) == 4
    assert f"run_id={run.run_id}" in messages[0]
    assert "direction=in" in messages[0]
    assert "event=start" in messages[1]
    assert f"run_id={run.run_id}" in messages[2]
    assert "outcome=resolution_unavailable" in messages[2]
    assert "error_code=UNKNOWN_TIMEZONE" in messages[2]
    assert "direction=out" in messages[3]
    assert "message_type=ResolutionUnavailable" in messages[3]


async def test_logs_without_run_keep_run_id_placeholder(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with _capture_resolver_logs(caplog):
        await resolver.resolve(
            BirthInput(
                birth_date=date(1990, 9, 2),
                birth_time=time(14, 30),
                place_id=MOSCOW_ID,
            )
        )

    messages = _resolver_messages(caplog)
    assert messages
    assert all("run_id=-" in message for message in messages)


async def test_birth_resolution_boundary_messages_include_complete_payloads(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with _capture_resolver_logs(caplog):
        await resolver.resolve(
            BirthInput(
                birth_date=date(1990, 9, 2),
                birth_time=time(14, 30),
                place_id=MOSCOW_ID,
            ),
            run=RunContext.new(),
        )

    messages = _resolver_messages(caplog)
    boundary = "\n".join(
        message for message in messages if message.startswith("component_message ")
    )
    technical = "\n".join(
        message for message in messages if message.startswith("birth_resolution ")
    )
    for value in (
        "55.75222",
        "37.61556",
        "1990-09-02",
        "14:30",
        "Москва",
        MOSCOW_ID,
    ):
        assert value in boundary
        assert value not in technical


async def test_distinct_run_ids_do_not_change_resolved_birth_data(
    resolver: BirthDataResolver,
) -> None:
    birth_input = BirthInput(
        birth_date=date(1990, 9, 2),
        birth_time=time(14, 30),
        place_id=MOSCOW_ID,
    )

    first = await resolver.resolve(birth_input, run=RunContext.new())
    second = await resolver.resolve(birth_input, run=RunContext.new())

    assert isinstance(first, ResolvedBirthData)
    assert isinstance(second, ResolvedBirthData)
    assert first == second


async def test_terminal_records_carry_duration(
    resolver: BirthDataResolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Терминальная запись несёт duration_ms, начальная — нет.

    Длительность живёт в исходе, как в cli.py: это и есть причина,
    по которой начальная запись остаётся на DEBUG и не дублируется
    в general. Без duration_ms по general нельзя отличить резолв
    за две миллисекунды от резолва за две секунды.
    """

    with _capture_resolver_logs(caplog):
        await resolver.resolve(
            BirthInput(
                birth_date=date(1990, 9, 2),
                birth_time=time(14, 30),
                place_id=MOSCOW_ID,
            ),
            run=RunContext.new(),
        )

    messages = [
        message
        for message in _resolver_messages(caplog)
        if message.startswith("birth_resolution ")
    ]
    assert "duration_ms=" not in messages[0]
    assert "duration_ms=" in messages[-1]

    value = float(messages[-1].split("duration_ms=")[1].split()[0])
    assert value >= 0.0

@contextmanager
def _capture_resolver_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    logger = logging.getLogger(RESOLVER_LOGGER)
    old_handlers = list(logger.handlers)
    old_level = logger.level
    old_propagate = logger.propagate
    logger.handlers[:] = [caplog.handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    caplog.set_level(logging.DEBUG, logger=RESOLVER_LOGGER)
    caplog.clear()
    try:
        yield
    finally:
        logger.handlers[:] = old_handlers
        logger.setLevel(old_level)
        logger.propagate = old_propagate


def _resolver_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == RESOLVER_LOGGER
    ]
