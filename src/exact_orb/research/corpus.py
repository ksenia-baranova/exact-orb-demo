"""Write-only port for the de-identified Research corpus."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from exact_orb.research.models import ResearchQualityEvent, ResearchRecord
from exact_orb.research.outcomes import (
    QualityAlreadyStored,
    QualityEventIdConflict,
    QualityStored,
    ResearchAlreadyStored,
    ResearchIdConflict,
    ResearchRecordAbsent,
    ResearchStored,
)


@runtime_checkable
class ResearchCorpus(Protocol):
    async def put_record(
        self,
        record: ResearchRecord,
        /,
    ) -> ResearchStored | ResearchAlreadyStored | ResearchIdConflict:
        """Append or classify one immutable base record."""

        ...

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
        """Append or classify one event without creating its parent."""

        ...


__all__ = ["ResearchCorpus"]
