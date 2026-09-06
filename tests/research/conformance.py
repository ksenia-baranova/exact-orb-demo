"""Reusable black-box conformance suite for Research corpus adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from exact_orb.research import (
    ChartFeatures,
    CopyEvent,
    QualityAlreadyStored,
    QualityEventIdConflict,
    QualityStored,
    RatingEvent,
    ReadingTimeEvent,
    RegenerateEvent,
    ResearchAlreadyStored,
    ResearchCorpus,
    ResearchFocus,
    ResearchIdConflict,
    ResearchQualityEvent,
    ResearchRecord,
    ResearchRecordAbsent,
    ResearchSelection,
    ResearchStored,
)


NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)
RESEARCH_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_RESEARCH_ID = UUID("22222222-2222-4222-8222-222222222222")
EVENT_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")


def make_record(
    research_id: UUID = RESEARCH_ID,
    *,
    focus: ResearchFocus | str = ResearchFocus.GENERAL,
    model: str = "provider/model@v1",
) -> ResearchRecord:
    return ResearchRecord(
        research_id=research_id,
        created_at=NOW,
        calculation_version="calculation-v1",
        chart_features=ChartFeatures(chart_kind="natal"),
        selection=ResearchSelection(topic="natal", focus=focus),
        recipe_version="recipe-v1",
        model=model,
        tokens_in=10,
        tokens_out=20,
        cost_usd=0.125,
        latency_ms=42.5,
    )


def make_event(
    kind: str = "rating",
    event_id: UUID = EVENT_ID,
    *,
    research_id: UUID = RESEARCH_ID,
    rating: int = 5,
    reading_time_ms: int = 1_500,
) -> ResearchQualityEvent:
    common = {
        "event_id": event_id,
        "research_id": research_id,
        "observed_at": NOW,
    }
    if kind == "rating":
        return RatingEvent(kind="rating", rating=rating, **common)
    if kind == "regenerate":
        return RegenerateEvent(kind="regenerate", **common)
    if kind == "copy":
        return CopyEvent(kind="copy", **common)
    if kind == "reading_time":
        return ReadingTimeEvent(
            kind="reading_time",
            reading_time_ms=reading_time_ms,
            **common,
        )
    raise AssertionError(f"unsupported test event kind: {kind}")


@dataclass(frozen=True)
class ResearchHandles:
    primary: ResearchCorpus
    peer: ResearchCorpus


ResearchCorpusFactory = Callable[[], AbstractAsyncContextManager[ResearchHandles]]


def make_in_memory_factory() -> ResearchCorpusFactory:
    """Test seam: the sole direct construction of the private InMemory backend."""

    from exact_orb.research.adapters.in_memory import (
        InMemoryResearchCorpus,
        _InMemoryResearchBackend,
    )

    @asynccontextmanager
    async def factory():
        # Two facades need one backend without promoting that backend to public API.
        backend = _InMemoryResearchBackend()
        yield ResearchHandles(
            primary=InMemoryResearchCorpus(backend),
            peer=InMemoryResearchCorpus(backend),
        )

    return factory


def _pair(
    handles: ResearchHandles,
    pair_kind: str,
) -> tuple[ResearchCorpus, ResearchCorpus]:
    if pair_kind == "same-handle":
        return handles.primary, handles.primary
    assert pair_kind == "cross-handle"
    return handles.primary, handles.peer


async def race(
    left: Callable[[], Coroutine[Any, Any, object]],
    right: Callable[[], Coroutine[Any, Any, object]],
) -> tuple[object, object]:
    start = asyncio.Barrier(2)

    async def run(operation: Callable[[], Coroutine[Any, Any, object]]) -> object:
        await start.wait()
        return await operation()

    left_result, right_result = await asyncio.wait_for(
        asyncio.gather(run(left), run(right)),
        timeout=5,
    )
    return left_result, right_result


class ResearchCorpusConformance:
    """Inherited public-write tests shared by every Research implementation."""

    def make_factory(self, tmp_path: Path) -> ResearchCorpusFactory:
        raise NotImplementedError

    @pytest.fixture
    def corpus_factory(self, tmp_path: Path) -> ResearchCorpusFactory:
        return self.make_factory(tmp_path)

    async def test_handles_share_backend_without_collapsing_identity(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        async with corpus_factory() as handles:
            assert handles.primary is not handles.peer
            assert isinstance(handles.primary, ResearchCorpus)
            assert isinstance(handles.peer, ResearchCorpus)
            assert isinstance(await handles.primary.put_record(make_record()), ResearchStored)
            assert isinstance(await handles.peer.put_record(make_record()), ResearchAlreadyStored)

    async def test_factory_contexts_are_isolated(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        async with corpus_factory() as first:
            assert isinstance(await first.primary.put_record(make_record()), ResearchStored)
        async with corpus_factory() as second:
            assert isinstance(await second.primary.put_record(make_record()), ResearchStored)

    async def test_record_store_retry_and_conflict_preserve_first_content(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        original = make_record()
        conflicting = make_record(focus="career")
        async with corpus_factory() as handles:
            corpus = handles.primary
            assert await corpus.put_record(original) == ResearchStored(research_id=RESEARCH_ID)
            assert await corpus.put_record(original) == ResearchAlreadyStored(research_id=RESEARCH_ID)
            assert await corpus.put_record(conflicting) == ResearchIdConflict(research_id=RESEARCH_ID)
            assert await corpus.put_record(original) == ResearchAlreadyStored(research_id=RESEARCH_ID)
            assert await corpus.put_record(conflicting) == ResearchIdConflict(research_id=RESEARCH_ID)

    async def test_event_store_retry_and_conflict_preserve_first_content(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        original = make_event()
        conflicting = make_event(rating=1)
        async with corpus_factory() as handles:
            corpus = handles.primary
            await corpus.put_record(make_record())
            assert await corpus.put_quality_event(original) == QualityStored(
                event_id=EVENT_ID,
                research_id=RESEARCH_ID,
            )
            assert await corpus.put_quality_event(original) == QualityAlreadyStored(
                event_id=EVENT_ID,
                research_id=RESEARCH_ID,
            )
            assert await corpus.put_quality_event(conflicting) == QualityEventIdConflict(
                event_id=EVENT_ID
            )
            assert isinstance(await corpus.put_quality_event(original), QualityAlreadyStored)
            assert isinstance(await corpus.put_quality_event(conflicting), QualityEventIdConflict)

    async def test_event_id_collision_precedes_missing_parent(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        async with corpus_factory() as handles:
            corpus = handles.primary
            await corpus.put_record(make_record())
            await corpus.put_quality_event(make_event())
            result = await corpus.put_quality_event(
                make_event(research_id=OTHER_RESEARCH_ID, rating=1)
            )
            assert result == QualityEventIdConflict(event_id=EVENT_ID)

    async def test_absent_parent_does_not_create_record_or_event(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        event = make_event(research_id=OTHER_RESEARCH_ID)
        async with corpus_factory() as handles:
            corpus = handles.primary
            assert await corpus.put_quality_event(event) == ResearchRecordAbsent(
                event_id=EVENT_ID,
                research_id=OTHER_RESEARCH_ID,
            )
            assert isinstance(await corpus.put_record(make_record(OTHER_RESEARCH_ID)), ResearchStored)
            assert isinstance(await corpus.put_quality_event(event), QualityStored)

    async def test_distinct_events_and_kinds_coexist(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        async with corpus_factory() as handles:
            corpus = handles.primary
            await corpus.put_record(make_record())
            events = (
                make_event("rating", EVENT_ID),
                make_event("copy", OTHER_EVENT_ID),
                make_event("regenerate", UUID("55555555-5555-4555-8555-555555555555")),
                make_event("reading_time", UUID("66666666-6666-4666-8666-666666666666")),
            )
            for event in events:
                assert isinstance(await corpus.put_quality_event(event), QualityStored)
            for event in events:
                assert isinstance(await corpus.put_quality_event(event), QualityAlreadyStored)

    @pytest.mark.parametrize("pair_kind", ["same-handle", "cross-handle"])
    async def test_concurrent_same_record_is_stored_once(
        self,
        corpus_factory: ResearchCorpusFactory,
        pair_kind: str,
    ) -> None:
        async with corpus_factory() as handles:
            left, right = _pair(handles, pair_kind)
            results = await race(
                lambda: left.put_record(make_record()),
                lambda: right.put_record(make_record()),
            )
            assert sum(isinstance(item, ResearchStored) for item in results) == 1
            assert sum(isinstance(item, ResearchAlreadyStored) for item in results) == 1

    @pytest.mark.parametrize("pair_kind", ["same-handle", "cross-handle"])
    async def test_concurrent_conflicting_records_keep_one_winner(
        self,
        corpus_factory: ResearchCorpusFactory,
        pair_kind: str,
    ) -> None:
        first = make_record(focus="general")
        second = make_record(focus="love")
        async with corpus_factory() as handles:
            left, right = _pair(handles, pair_kind)
            results = await race(
                lambda: left.put_record(first),
                lambda: right.put_record(second),
            )
            assert sum(isinstance(item, ResearchStored) for item in results) == 1
            assert sum(isinstance(item, ResearchIdConflict) for item in results) == 1
            retries = (
                await handles.primary.put_record(first),
                await handles.primary.put_record(second),
            )
            assert sum(isinstance(item, ResearchAlreadyStored) for item in retries) == 1
            assert sum(isinstance(item, ResearchIdConflict) for item in retries) == 1

    @pytest.mark.parametrize("pair_kind", ["same-handle", "cross-handle"])
    async def test_concurrent_same_event_is_stored_once(
        self,
        corpus_factory: ResearchCorpusFactory,
        pair_kind: str,
    ) -> None:
        async with corpus_factory() as handles:
            await handles.primary.put_record(make_record())
            left, right = _pair(handles, pair_kind)
            results = await race(
                lambda: left.put_quality_event(make_event()),
                lambda: right.put_quality_event(make_event()),
            )
            assert sum(isinstance(item, QualityStored) for item in results) == 1
            assert sum(isinstance(item, QualityAlreadyStored) for item in results) == 1

    @pytest.mark.parametrize("pair_kind", ["same-handle", "cross-handle"])
    async def test_concurrent_conflicting_events_keep_one_winner(
        self,
        corpus_factory: ResearchCorpusFactory,
        pair_kind: str,
    ) -> None:
        first = make_event(rating=1)
        second = make_event(rating=5)
        async with corpus_factory() as handles:
            await handles.primary.put_record(make_record())
            left, right = _pair(handles, pair_kind)
            results = await race(
                lambda: left.put_quality_event(first),
                lambda: right.put_quality_event(second),
            )
            assert sum(isinstance(item, QualityStored) for item in results) == 1
            assert sum(isinstance(item, QualityEventIdConflict) for item in results) == 1
            retries = (
                await handles.primary.put_quality_event(first),
                await handles.primary.put_quality_event(second),
            )
            assert sum(isinstance(item, QualityAlreadyStored) for item in retries) == 1
            assert sum(isinstance(item, QualityEventIdConflict) for item in retries) == 1

    async def test_port_exposes_only_write_operations(
        self,
        corpus_factory: ResearchCorpusFactory,
    ) -> None:
        forbidden = {
            "get",
            "list",
            "delete",
            "delete_by_session",
            "touch",
            "reap_expired",
            "consent",
            "read",
        }
        async with corpus_factory() as handles:
            assert forbidden.isdisjoint(dir(handles.primary))
        assert forbidden.isdisjoint(ResearchCorpus.__dict__)


__all__ = [
    "EVENT_ID",
    "NOW",
    "OTHER_EVENT_ID",
    "OTHER_RESEARCH_ID",
    "RESEARCH_ID",
    "ResearchCorpusConformance",
    "ResearchCorpusFactory",
    "ResearchHandles",
    "make_event",
    "make_in_memory_factory",
    "make_record",
    "race",
]
