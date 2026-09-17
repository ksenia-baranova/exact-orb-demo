"""Minimal dependency fakes recording the public application call sequence."""

from __future__ import annotations

from dataclasses import dataclass

from exact_orb.application.commands import Command
from exact_orb.application.results import BuildNatalOutcome
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import (
    AlreadyApplied,
    Committed,
    SessionAbsent,
    StateCommitFailed,
    StateReadFailed,
    Superseded,
)
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta


LoadOutcome = SessionSnapshot | SessionAbsent | StateReadFailed
SaveOutcome = Committed | AlreadyApplied | Superseded | SessionAbsent | StateCommitFailed


@dataclass(frozen=True)
class Call:
    """Keep the original dependency and arguments, without copying payloads."""

    target: object
    method: str
    args: tuple[object, ...]


class RecordingContext:
    """Record load/save and return explicitly configured typed outcomes."""

    def __init__(
        self,
        journal: list[Call],
        *,
        load_result: LoadOutcome,
        save_result: SaveOutcome | None = None,
    ) -> None:
        self.journal = journal
        self.load_result = load_result
        self.save_result = save_result

    async def load(self, session_id: str) -> LoadOutcome:
        self.journal.append(Call(self, "load", (session_id,)))
        return self.load_result

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> SaveOutcome:
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        if self.save_result is None:
            raise AssertionError("save outcome was not configured for this test")
        return self.save_result


class RecordingHandler:
    """Record handle arguments by identity, with no domain processing."""

    def __init__(self, journal: list[Call], *, result: BuildNatalOutcome) -> None:
        self.journal = journal
        self.result = result

    async def handle(
        self, command: Command, state: SessionState, run: RunContext,
    ) -> BuildNatalOutcome:
        self.journal.append(Call(self, "handle", (command, state, run)))
        return self.result
