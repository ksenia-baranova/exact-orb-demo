"""Immutable commands accepted by the application layer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from exact_orb.birth.types import BirthInput


class Command(BaseModel):
    """Marker base type for application-command routing."""

    model_config = ConfigDict(frozen=True)


class BuildNatalCommand(Command):
    """Request to build a base chart from structured birth data."""

    birth_input: BirthInput


__all__ = ["BuildNatalCommand", "Command"]
