"""Structural ports used by application handlers."""

from __future__ import annotations

from typing import Protocol, TypeVar

from exact_orb.application.commands import Command
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.spec import ChartSpec
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext
from exact_orb.session.state import SessionState


CommandT = TypeVar("CommandT", bound=Command, contravariant=True)
OutcomeT = TypeVar("OutcomeT", covariant=True)


class Handler(Protocol[CommandT, OutcomeT]):
    """Handle one typed application command."""

    async def handle(
        self,
        command: CommandT,
        state: SessionState,
        run: RunContext,
    ) -> OutcomeT: ...


class BirthDataResolverPort(Protocol):
    """Resolve structured birth input for a build operation."""

    async def resolve(
        self,
        birth_input: BirthInput,
        *,
        run: RunContext | None = None,
    ) -> ResolvedBirthData | InputRequired | ResolutionUnavailable: ...


class ChartArtifactPort(Protocol):
    """Return a reproducible chart artifact for resolved input."""

    async def ensure_chart(
        self,
        spec: ChartSpec,
        resolved: ResolvedBirthData,
        *,
        run: RunContext,
    ) -> ChartArtifact: ...


__all__ = [
    "BirthDataResolverPort",
    "ChartArtifactPort",
    "CommandT",
    "Handler",
    "OutcomeT",
]
