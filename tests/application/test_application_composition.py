"""Startup composition contract for the supported application commands."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import exact_orb.application.composition as composition
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator


pytestmark = pytest.mark.no_ephemeris_autoinit


class UnwiredCommand(Command):
    """A supported test command intentionally absent from the built registry."""


def test_complete_supported_registry_is_accepted() -> None:
    """The current MVP registry has one exact, valid Build Natal assignment.

    Требования: R3.2, FR-05; позитивный контроль полноты composition registry.
    """
    handler = object()

    assert composition._SUPPORTED_COMMAND_TYPES == frozenset({BuildNatalCommand})
    assert (
        composition._validate_handler_registry({BuildNatalCommand: handler}) is None
    )


def test_missing_supported_command_fails_at_startup() -> None:
    """An empty registry is rejected before any user execute can begin.

    Требования: R3.2, FR-05; startup failure для неполной конфигурации.
    """
    with pytest.raises(ValueError, match=r"\bBuildNatalCommand\b"):
        composition._validate_handler_registry({})


def test_base_command_registration_is_not_an_implicit_fallback() -> None:
    """A base Command registration cannot satisfy exact-type routing.

    Требования: R3.2, FR-04/05; поддержка AC-3/4.
    """
    with pytest.raises(ValueError, match=r"\bBuildNatalCommand\b"):
        composition._validate_handler_registry({Command: object()})


def test_builder_wires_explicit_dependencies_and_checks_completeness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public builder wires Build Natal and validates before returning.

    Требования: R3.2, FR-05; основа application composition из карточки 10.2.
    """
    context = object()
    clock = lambda: datetime(2026, 9, 19, 9, 0, tzinfo=UTC)
    resolver = object()
    artifacts = object()

    orchestrator = composition.build_application_orchestrator(
        context=context,
        clock=clock,
        resolver=resolver,
        artifacts=artifacts,
    )

    assert isinstance(orchestrator, ApplicationOrchestrator)
    assert orchestrator._context is context
    assert orchestrator._clock is clock
    assert set(orchestrator._handlers) == {BuildNatalCommand}
    handler = orchestrator._handlers[BuildNatalCommand]
    assert isinstance(handler, BuildNatalHandler)
    assert handler._resolver is resolver
    assert handler._artifacts is artifacts

    monkeypatch.setattr(
        composition,
        "_SUPPORTED_COMMAND_TYPES",
        frozenset({BuildNatalCommand, UnwiredCommand}),
    )
    with pytest.raises(ValueError, match=r"\bUnwiredCommand\b"):
        composition.build_application_orchestrator(
            context=context,
            clock=clock,
            resolver=resolver,
            artifacts=artifacts,
        )
