"""Minimal composition root for the supported application commands."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime

from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.ports import (
    BirthDataResolverPort,
    ChartArtifactPort,
    Handler,
)
from exact_orb.session.context import ContextService


_SUPPORTED_COMMAND_TYPES: frozenset[type[Command]] = frozenset({BuildNatalCommand})


def _validate_handler_registry(
    handlers: Mapping[type[Command], Handler],
) -> None:
    """Reject a registry missing an exact assignment for a supported command."""
    missing = _SUPPORTED_COMMAND_TYPES.difference(handlers)
    if missing:
        names = ", ".join(sorted(command_type.__name__ for command_type in missing))
        raise ValueError(f"handler registry is missing supported commands: {names}")


def build_application_orchestrator(
    *,
    context: ContextService,
    clock: Callable[[], datetime],
    resolver: BirthDataResolverPort,
    artifacts: ChartArtifactPort,
) -> ApplicationOrchestrator:
    """Build the coordinator from explicitly provided application dependencies."""
    handlers: dict[type[Command], Handler] = {
        BuildNatalCommand: BuildNatalHandler(
            resolver=resolver,
            artifacts=artifacts,
        ),
    }
    _validate_handler_registry(handlers)
    return ApplicationOrchestrator(
        context=context,
        handlers=handlers,
        clock=clock,
    )


__all__ = ["build_application_orchestrator"]
