"""Typed outcomes for idempotent Research writes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, UUID4


class _FrozenOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ResearchStored(_FrozenOutcome):
    research_id: UUID4


class ResearchAlreadyStored(_FrozenOutcome):
    research_id: UUID4


class ResearchIdConflict(_FrozenOutcome):
    research_id: UUID4


class QualityStored(_FrozenOutcome):
    event_id: UUID4
    research_id: UUID4


class QualityAlreadyStored(_FrozenOutcome):
    event_id: UUID4
    research_id: UUID4


class QualityEventIdConflict(_FrozenOutcome):
    event_id: UUID4


class ResearchRecordAbsent(_FrozenOutcome):
    event_id: UUID4
    research_id: UUID4


__all__ = [
    "QualityAlreadyStored",
    "QualityEventIdConflict",
    "QualityStored",
    "ResearchAlreadyStored",
    "ResearchIdConflict",
    "ResearchRecordAbsent",
    "ResearchStored",
]
