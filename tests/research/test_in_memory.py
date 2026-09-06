"""InMemory Research corpus conformance and lifecycle invariants."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

import exact_orb.research.adapters as public_adapters
from exact_orb.research import (
    QualityAlreadyStored,
    QualityEventIdConflict,
    QualityStored,
    ResearchAlreadyStored,
    ResearchIdConflict,
    ResearchStored,
)
from exact_orb.research.adapters import InMemoryResearchCorpus
from tests.research.conformance import (
    EVENT_ID,
    RESEARCH_ID,
    ResearchCorpusConformance,
    ResearchCorpusFactory,
    make_event,
    make_in_memory_factory,
    make_record,
    race,
)


class TestInMemoryResearchCorpus(ResearchCorpusConformance):
    def make_factory(self, tmp_path: Path) -> ResearchCorpusFactory:
        _ = tmp_path
        return make_in_memory_factory()


def test_concrete_suite_collects_inherited_tests_and_only_overrides_factory() -> None:
    inherited = {
        name
        for name in dir(TestInMemoryResearchCorpus)
        if name.startswith("test_") and name not in TestInMemoryResearchCorpus.__dict__
    }
    assert inherited
    declared = {
        name for name in TestInMemoryResearchCorpus.__dict__ if not name.startswith("__")
    }
    assert declared == {"make_factory"}


def test_constructor_requires_private_positional_only_backend() -> None:
    with pytest.raises(TypeError):
        InMemoryResearchCorpus()
    with pytest.raises(TypeError):
        InMemoryResearchCorpus(backend=object())
    assert not hasattr(public_adapters, "InMemoryResearchBackend")
    assert not hasattr(public_adapters, "create_in_memory_backend")


async def test_distinct_factory_backends_are_isolated() -> None:
    first_factory = make_in_memory_factory()
    second_factory = make_in_memory_factory()
    async with first_factory() as first, second_factory() as second:
        assert isinstance(await first.primary.put_record(make_record()), ResearchStored)
        assert isinstance(await second.primary.put_record(make_record()), ResearchStored)


async def test_facades_are_distinct_and_share_one_private_backend() -> None:
    async with make_in_memory_factory()() as handles:
        assert handles.primary is not handles.peer
        assert handles.primary._backend is handles.peer._backend


@pytest.mark.parametrize("conflicting", [False, True], ids=["same", "different"])
async def test_record_race_enters_critical_section_twice(conflicting: bool) -> None:
    async with make_in_memory_factory()() as handles:
        backend = handles.primary._backend
        before = backend.record_critical_entries
        left_record = make_record(focus="general")
        right_record = make_record(focus="love") if conflicting else left_record
        results = await race(
            lambda: handles.primary.put_record(left_record),
            lambda: handles.peer.put_record(right_record),
        )
        assert backend.record_critical_entries - before == 2
        expected_retry = ResearchIdConflict if conflicting else ResearchAlreadyStored
        assert {type(item) for item in results} == {ResearchStored, expected_retry}


@pytest.mark.parametrize("conflicting", [False, True], ids=["same", "different"])
async def test_event_race_enters_critical_section_twice_and_snapshot_is_append_only(
    conflicting: bool,
) -> None:
    async with make_in_memory_factory()() as handles:
        await handles.primary.put_record(make_record())
        backend = handles.primary._backend
        before = backend.event_critical_entries
        left_event = make_event(rating=1)
        right_event = make_event(rating=5) if conflicting else left_event
        results = await race(
            lambda: handles.primary.put_quality_event(left_event),
            lambda: handles.peer.put_quality_event(right_event),
        )
        assert backend.event_critical_entries - before == 2
        expected_retry = QualityEventIdConflict if conflicting else QualityAlreadyStored
        assert {type(item) for item in results} == {QualityStored, expected_retry}
        assert set(backend.records) == {RESEARCH_ID}
        assert set(backend.events) == {EVENT_ID}
        assert backend.records[RESEARCH_ID].record == make_record()
        assert backend.events[EVENT_ID].event in {left_event, right_event}


@pytest.mark.parametrize("method_name", ["put_record", "put_quality_event"])
def test_critical_section_contains_no_await_after_entry(method_name: str) -> None:
    source = inspect.getsource(getattr(InMemoryResearchCorpus, method_name))
    function = ast.parse(inspect.cleandoc(source)).body[0]
    critical_sections = [node for node in ast.walk(function) if isinstance(node, ast.AsyncWith)]
    assert len(critical_sections) == 1
    assert not any(
        isinstance(node, ast.Await)
        for statement in critical_sections[0].body
        for node in ast.walk(statement)
    )


def test_private_backend_is_constructed_only_by_conformance_factory() -> None:
    source_root = Path(__file__).parents[2] / "src" / "exact_orb" / "research"
    test_root = Path(__file__).parent
    occurrences: list[str] = []
    for path in (*source_root.rglob("*.py"), *test_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "_InMemoryResearchBackend":
                    occurrences.append(path.name)
    assert occurrences == ["conformance.py"]
