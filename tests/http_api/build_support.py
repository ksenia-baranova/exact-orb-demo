"""Shared real SQLite/orchestrator and cancellable leaf seams for HTTP tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.birth.types import ResolvedBirthData
from exact_orb.calculation.codec import decode_chart_artifact
from exact_orb.session.outcomes import StateCommitFailed
from exact_orb.session.persistence import SessionSnapshot
from tests.application.stubs import StubBirthDataResolver, StubChartArtifactPort
from tests.http_api.conftest import RuntimeSpy
from tests.http_api.shared import input_required as _input_required


GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden"


class ObservedContext:
    """Observe real SQLite load/CAS; optionally lose both save acknowledgements."""

    def __init__(self, inner: Any, *, lost_commit: bool | None = None) -> None:
        self.inner = inner
        self.lost_commit = lost_commit
        self.load_versions: list[int | None] = []
        self.save_expected: list[int] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    async def load(self, session_id: str):
        result = await self.inner.load(session_id)
        self.load_versions.append(result.state.state_version
                                  if isinstance(result, SessionSnapshot) else None)
        return result

    async def save(self, session_id: str, expected_state_version: int, delta):
        self.save_expected.append(expected_state_version)
        if self.lost_commit is not None:
            if self.lost_commit and len(self.save_expected) == 1:
                await self.inner.save(session_id, expected_state_version, delta)
            return StateCommitFailed(error_code="SESSION_SQLITE_WRITE_FAILED")
        return await self.inner.save(session_id, expected_state_version, delta)


class CountingOrchestrator:
    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.calls: list[tuple[BuildNatalCommand, str, Any]] = []

    async def execute(self, command, *, session_id: str, run):
        self.calls.append((command, session_id, run))
        return await self.inner.execute(command, session_id=session_id, run=run)


class BarrierHandler:
    def __init__(self, inner: Any, expected: int = 2) -> None:
        self.inner = inner
        self.expected = expected
        self.entered: list[int] = []
        self.condition = asyncio.Condition()
        self.release = asyncio.Event()

    async def handle(self, command, state, run):
        async with self.condition:
            self.entered.append(state.state_version)
            self.condition.notify_all()
        await self.release.wait()
        return await self.inner.handle(command, state, run)

    async def wait_entered(self) -> None:
        async with self.condition:
            await self.condition.wait_for(lambda: len(self.entered) >= self.expected)


def real_orchestrator(runtime: RuntimeSpy, utc_clock, *,
                       barrier: bool = False, lost_commit: bool | None = None):
    artifact = decode_chart_artifact(
        (GOLDEN_DIR / "chart_artifact_format_1_natal_1985.bin").read_bytes()
    )
    chart = artifact.chart
    resolved = ResolvedBirthData(
        utc_datetime=chart.datetime_utc,
        latitude=chart.latitude,
        longitude=chart.longitude,
        tz_id="Europe/Moscow",
        utc_offset_seconds=14400,
        canonical_place="Москва",
        time_unknown=False,
        birth_time_domain=None,
        warnings=(),
    )
    observed = ObservedContext(runtime.context, lost_commit=lost_commit)
    runtime.context = observed
    class IntentResolver(StubBirthDataResolver):
        async def resolve(self, birth_input, *, run=None):
            result = await super().resolve(birth_input, run=run)
            if isinstance(result, ResolvedBirthData) and birth_input.place_id != "524901":
                return result.model_copy(update={
                    "canonical_place": f"Тестовое место {birth_input.place_id}",
                })
            return result

    leaf = BuildNatalHandler(
        resolver=IntentResolver(resolved),
        artifacts=StubChartArtifactPort(artifact),
    )
    handler = BarrierHandler(leaf) if barrier else leaf
    orchestrator = CountingOrchestrator(ApplicationOrchestrator(
        context=observed, handlers={BuildNatalCommand: handler}, clock=utc_clock,
    ))
    runtime.orchestrator = orchestrator
    runtime.calculation_version = artifact.calculation_version
    return artifact, observed, orchestrator, handler


class BlockedOrchestrator:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, str, Any]] = []
        self.releases: list[asyncio.Event] = []
        self.condition = asyncio.Condition()

    async def execute(self, command, *, session_id: str, run):
        gate = asyncio.Event()
        async with self.condition:
            self.calls.append((command, session_id, run))
            self.releases.append(gate)
            self.condition.notify_all()
        await gate.wait()
        return _input_required(run)

    async def wait_count(self, count: int) -> None:
        async with self.condition:
            await self.condition.wait_for(lambda: len(self.calls) >= count)

    def release_all(self) -> None:
        for gate in self.releases:
            gate.set()


class RetainedBlockedOrchestrator(BlockedOrchestrator):
    """The accepted leaf keeps running after its HTTP waiter is cancelled."""

    async def execute(self, command, *, session_id: str, run):
        gate = asyncio.Event()
        async with self.condition:
            self.calls.append((command, session_id, run))
            self.releases.append(gate)
            self.condition.notify_all()
        while not gate.is_set():
            try:
                await gate.wait()
            except asyncio.CancelledError:
                continue
        return _input_required(run)


class TerminalHeldOrchestrator:
    """An accepted operation may persist and still not report a terminal result."""

    def __init__(self, inner: Any | None) -> None:
        self.inner = inner
        self.calls = 0
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.completed = asyncio.Event()

    async def execute(self, command, *, session_id: str, run):
        self.calls += 1
        result = (await self.inner.execute(command, session_id=session_id, run=run)
                  if self.inner is not None else _input_required(run))
        self.entered.set()
        while not self.release.is_set():
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                # Simulates an owned native/executor operation surviving waiter cancellation.
                continue
        self.completed.set()
        return result
