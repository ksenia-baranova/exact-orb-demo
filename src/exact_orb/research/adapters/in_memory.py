"""Process-local implementation of the Research corpus contract."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from exact_orb.research.models import (
    ResearchQualityEvent,
    ResearchRecord,
    event_content_digest,
    record_content_digest,
)
from exact_orb.research.outcomes import (
    QualityAlreadyStored,
    QualityEventIdConflict,
    QualityStored,
    ResearchAlreadyStored,
    ResearchIdConflict,
    ResearchRecordAbsent,
    ResearchStored,
)


@dataclass(frozen=True, slots=True)
class _StoredRecord:
    record: ResearchRecord
    digest: str


@dataclass(frozen=True, slots=True)
class _StoredEvent:
    event: ResearchQualityEvent
    digest: str


class _InMemoryResearchBackend:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.records: dict[UUID, _StoredRecord] = {}
        self.events: dict[UUID, _StoredEvent] = {}
        self.record_critical_entries = 0
        self.event_critical_entries = 0


class InMemoryResearchCorpus:
    """One facade over an explicitly shared process-local backend."""

    def __init__(self, backend: _InMemoryResearchBackend, /) -> None:
        self._backend = backend

    async def put_record(
        self,
        record: ResearchRecord,
        /,
    ) -> ResearchStored | ResearchAlreadyStored | ResearchIdConflict:
        digest = record_content_digest(record)
        async with self._backend.lock:
            self._backend.record_critical_entries += 1
            existing = self._backend.records.get(record.research_id)
            if existing is not None:
                if existing.digest == digest:
                    return ResearchAlreadyStored(research_id=record.research_id)
                return ResearchIdConflict(research_id=record.research_id)

            self._backend.records[record.research_id] = _StoredRecord(
                record=record,
                digest=digest,
            )
            return ResearchStored(research_id=record.research_id)

    async def put_quality_event(
        self,
        event: ResearchQualityEvent,
        /,
    ) -> (
        QualityStored
        | QualityAlreadyStored
        | QualityEventIdConflict
        | ResearchRecordAbsent
    ):
        digest = event_content_digest(event)
        async with self._backend.lock:
            self._backend.event_critical_entries += 1
            existing = self._backend.events.get(event.event_id)
            if existing is not None:
                if existing.digest == digest:
                    return QualityAlreadyStored(
                        event_id=event.event_id,
                        research_id=event.research_id,
                    )
                return QualityEventIdConflict(event_id=event.event_id)

            if event.research_id not in self._backend.records:
                return ResearchRecordAbsent(
                    event_id=event.event_id,
                    research_id=event.research_id,
                )

            self._backend.events[event.event_id] = _StoredEvent(
                event=event,
                digest=digest,
            )
            return QualityStored(
                event_id=event.event_id,
                research_id=event.research_id,
            )


__all__ = ["InMemoryResearchCorpus"]
