"""Run the normal ApplicationOrchestrator load profile and write its evidence report.

This is a local acceptance harness, not an HTTP benchmark or an SLA tool. It
uses real application, calculation and SQLite components. A test-only load
barrier coordinates selected shared-session pairs after both real SQLite
``touch`` calls so their CAS outcomes are observable without replacing them.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
import json
import logging
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for import_root in (PROJECT_ROOT, SRC_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from exact_orb.application.application_results import (  # noqa: E402
    ApplicationAlreadyApplied,
    ApplicationCommitted,
    ApplicationResult,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand  # noqa: E402
from exact_orb.application.composition import build_application_orchestrator  # noqa: E402
from exact_orb.application.orchestrator import ApplicationOrchestrator  # noqa: E402
from exact_orb.birth.types import BirthInput  # noqa: E402
from exact_orb.config import configure_ephemeris  # noqa: E402
from exact_orb.run_context import RunContext  # noqa: E402
from exact_orb.session.adapters.sqlite import SqliteSessionPersistence  # noqa: E402
from exact_orb.session.context import ContextService  # noqa: E402
from exact_orb.session.dialog import DialogTurn, Selection  # noqa: E402
from exact_orb.session.outcomes import SessionAbsent, SessionCreated, VersionConflict  # noqa: E402
from exact_orb.session.persistence import SessionPersistence, SessionSnapshot  # noqa: E402
from exact_orb.session.state import SessionState  # noqa: E402
from tests.fixtures.application import application_test_stand  # noqa: E402


APPLICATION_LOGGER = "exact_orb.application"
LIFECYCLE_START = "application_operation_started"
LIFECYCLE_FINISH = "application_operation_finished"
BATCH_SIZE = 2
SHARED_SESSION_COUNT = 6
OPERATION_TIMEOUT_SECONDS = 30.0
DIALOG_TURNS = 20
DIALOG_CHARS_PER_TURN = 1_000
DIALOG_SAMPLES = 100


class HarnessInvariantError(RuntimeError):
    """The acceptance harness observed an internally inconsistent result."""


@dataclass(frozen=True)
class OperationPlan:
    index: int
    batch_index: int
    session_id: str
    session_kind: str
    command: BuildNatalCommand
    run: RunContext


@dataclass(frozen=True)
class OperationObservation:
    plan: OperationPlan
    result: ApplicationResult
    elapsed_ms: float


@dataclass
class ActivityTracker:
    submitted: int = 0
    completed: int = 0
    active: int = 0
    peak_active: int = 0
    completion_times: list[float] = field(default_factory=list)


class LifecycleCollector(logging.Handler):
    """Count INFO-visible start/terminal events without printing 600 records."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.started: Counter[str] = Counter()
        self.finished: Counter[str] = Counter()
        self.finish_fields: dict[str, dict[str, object]] = {}
        self.parse_errors: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            event, separator, payload = record.getMessage().partition(" ")
            if event not in (LIFECYCLE_START, LIFECYCLE_FINISH):
                return
            if separator != " ":
                raise ValueError("missing lifecycle JSON payload")
            fields = json.loads(payload)
            run_id = fields["run_id"]
            if not isinstance(run_id, str):
                raise TypeError("run_id must be a string")
            if event == LIFECYCLE_START:
                self.started[run_id] += 1
            else:
                self.finished[run_id] += 1
                self.finish_fields[run_id] = fields
        except Exception as exc:  # pragma: no cover - evidence path, reported below
            self.parse_errors.append(f"{type(exc).__name__}: {exc}")


class PairedLoadBarrierPersistence:
    """Delegate real persistence and synchronize only explicitly armed load pairs."""

    def __init__(self, delegate: SessionPersistence) -> None:
        self._delegate = delegate
        self.sessions = delegate.sessions
        self.dialogs = delegate.dialogs
        self._gates: dict[str, asyncio.Barrier] = {}
        self.pairs_armed = 0
        self.pairs_released = 0

    def arm(self, session_id: str) -> None:
        if session_id in self._gates:
            raise HarnessInvariantError(f"load barrier already armed for {session_id}")
        self._gates[session_id] = asyncio.Barrier(2)
        self.pairs_armed += 1

    async def touch(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionSnapshot | SessionAbsent:
        result = await self._delegate.touch(session_id, now=now)
        gate = self._gates.get(session_id)
        if gate is None:
            return result
        position = await gate.wait()
        if position == 0 and self._gates.get(session_id) is gate:
            self._gates.pop(session_id)
            self.pairs_released += 1
        return result

    async def reset(
        self,
        session_id: str,
        expected_state_version: int,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        return await self._delegate.reset(
            session_id,
            expected_state_version,
            now=now,
        )

    async def delete(self, session_id: str) -> None:
        await self._delegate.delete(session_id)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _command_variant(index: int) -> BuildNatalCommand:
    day = 2 + (index % 6)
    hour = 8 + (index % 7)
    minute = (index * 11) % 60
    return BuildNatalCommand(
        birth_input=BirthInput(
            birth_date=date(1990, 9, day),
            birth_time=time(hour, minute),
            place_id="524901",
        )
    )


def _build_plans(operations: int) -> tuple[OperationPlan, ...]:
    plans: list[OperationPlan] = []
    for batch_index, first_index in enumerate(range(0, operations, BATCH_SIZE)):
        remaining = min(BATCH_SIZE, operations - first_index)
        mode = batch_index % 5
        if remaining == 1 or mode >= 2:
            for offset in range(remaining):
                index = first_index + offset
                plans.append(OperationPlan(
                    index=index,
                    batch_index=batch_index,
                    session_id=f"profile-distinct-{index:04d}",
                    session_kind="distinct",
                    command=_command_variant(index),
                    run=RunContext.new(),
                ))
            continue

        shared_id = f"profile-shared-{batch_index % SHARED_SESSION_COUNT}"
        first_command = _command_variant(batch_index)
        second_command = (
            _command_variant(batch_index)
            if mode == 0
            else _command_variant(batch_index + 1)
        )
        session_kind = "shared_same_intent" if mode == 0 else "shared_different_intent"
        plans.extend((
            OperationPlan(
                index=first_index,
                batch_index=batch_index,
                session_id=shared_id,
                session_kind=session_kind,
                command=first_command,
                run=RunContext.new(),
            ),
            OperationPlan(
                index=first_index + 1,
                batch_index=batch_index,
                session_id=shared_id,
                session_kind=session_kind,
                command=second_command,
                run=RunContext.new(),
            ),
        ))
    return tuple(plans)


async def _create_sessions(
    persistence: SqliteSessionPersistence,
    session_ids: Sequence[str],
) -> None:
    for session_id in session_ids:
        created = await persistence.sessions.create(session_id, now=_utc_now())
        if not isinstance(created, SessionCreated):
            raise HarnessInvariantError(f"session setup failed for {session_id}: {created}")


async def _execute_one(
    orchestrator: ApplicationOrchestrator,
    plan: OperationPlan,
    tracker: ActivityTracker,
) -> OperationObservation:
    loop = asyncio.get_running_loop()
    tracker.active += 1
    tracker.peak_active = max(tracker.peak_active, tracker.active)
    started = loop.time()
    try:
        result = await asyncio.wait_for(
            orchestrator.execute(
                plan.command,
                session_id=plan.session_id,
                run=plan.run,
            ),
            timeout=OPERATION_TIMEOUT_SECONDS,
        )
        return OperationObservation(
            plan=plan,
            result=result,
            elapsed_ms=(loop.time() - started) * 1_000.0,
        )
    finally:
        tracker.active -= 1
        tracker.completed += 1
        tracker.completion_times.append(loop.time())


async def _submit_profile(
    orchestrator: ApplicationOrchestrator,
    persistence: PairedLoadBarrierPersistence,
    plans: tuple[OperationPlan, ...],
    *,
    rate: float,
    duration: float,
) -> tuple[
    list[OperationObservation],
    list[BaseException],
    ActivityTracker,
    dict[str, float | int],
]:
    loop = asyncio.get_running_loop()
    tracker = ActivityTracker()
    tasks: list[asyncio.Task[OperationObservation]] = []
    batch_interval = BATCH_SIZE / rate
    batch_count = math.ceil(len(plans) / BATCH_SIZE)
    planned_window = max(duration, batch_count * batch_interval)
    submission_started = loop.time()
    max_schedule_lag = 0.0

    for batch_index in range(batch_count):
        target = submission_started + batch_index * batch_interval
        await asyncio.sleep(max(0.0, target - loop.time()))
        max_schedule_lag = max(max_schedule_lag, loop.time() - target)
        batch = plans[batch_index * BATCH_SIZE:(batch_index + 1) * BATCH_SIZE]
        if (
            len(batch) == 2
            and batch[0].session_id == batch[1].session_id
            and batch[0].session_kind.startswith("shared_")
        ):
            persistence.arm(batch[0].session_id)
        for plan in batch:
            tracker.submitted += 1
            tasks.append(asyncio.create_task(_execute_one(orchestrator, plan, tracker)))

    window_target = submission_started + planned_window
    await asyncio.sleep(max(0.0, window_target - loop.time()))
    submission_finished = loop.time()
    completed_at_submission_stop = tracker.completed
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    drain_finished = loop.time()

    observations = [item for item in gathered if isinstance(item, OperationObservation)]
    exceptions = [item for item in gathered if isinstance(item, BaseException)]
    timing: dict[str, float | int] = {
        "planned_submission_duration_s": planned_window,
        "submission_duration_s": submission_finished - submission_started,
        "completed_at_submission_stop": completed_at_submission_stop,
        "drain_duration_s": drain_finished - submission_finished,
        "total_duration_s": drain_finished - submission_started,
        "max_schedule_lag_ms": max_schedule_lag * 1_000.0,
    }
    return observations, exceptions, tracker, timing


def _serialize_dialog(turns: tuple[DialogTurn, ...]) -> bytes:
    payload = [turn.model_dump(mode="json") for turn in turns]
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _timing_summary(samples_ns: list[int]) -> dict[str, float | int]:
    samples_ms = [value / 1_000_000.0 for value in samples_ns]
    return {
        "samples": len(samples_ms),
        "mean_ms": statistics.fmean(samples_ms),
        "min_ms": min(samples_ms),
        "max_ms": max(samples_ms),
        "spread_ms": max(samples_ms) - min(samples_ms),
    }


async def _measure_dialog_overhead(
    persistence: SqliteSessionPersistence,
    orchestrator: ApplicationOrchestrator,
) -> dict[str, object]:
    empty_id = "dialog-empty-profile"
    populated_id = "dialog-full-profile"
    for session_id in (empty_id, populated_id):
        result = await orchestrator.execute(
            _command_variant(0),
            session_id=session_id,
            run=RunContext.new(),
        )
        if not isinstance(result, ApplicationCommitted):
            raise HarnessInvariantError(f"dialog setup commit failed: {result}")

    selection = Selection(topic="natal", focus="load-profile")
    for index in range(DIALOG_TURNS):
        turn = DialogTurn(
            turn_id=f"profile-turn-{index:02d}",
            created_at=_utc_now(),
            selection=selection,
            state_version_at_answer=1,
            status="complete",
            text="D" * DIALOG_CHARS_PER_TURN,
        )
        appended = await persistence.dialogs.append(
            populated_id,
            turn,
            now=_utc_now(),
        )
        if appended is not None:
            raise HarnessInvariantError(f"dialog setup append failed: {appended}")

    timings: dict[str, list[int]] = {"empty": [], "populated": []}
    snapshots: dict[str, SessionSnapshot] = {}
    for index in range(DIALOG_SAMPLES):
        order = (
            (("empty", empty_id), ("populated", populated_id))
            if index % 2 == 0
            else (("populated", populated_id), ("empty", empty_id))
        )
        for label, session_id in order:
            started_ns = perf_counter_ns()
            snapshot = await persistence.touch(session_id, now=_utc_now())
            timings[label].append(perf_counter_ns() - started_ns)
            if not isinstance(snapshot, SessionSnapshot):
                raise HarnessInvariantError(f"dialog touch failed: {snapshot}")
            snapshots[label] = snapshot

    empty = snapshots["empty"]
    populated = snapshots["populated"]
    state_bytes = len(populated.state.model_dump_json().encode("utf-8"))
    empty_dialog_bytes = len(_serialize_dialog(empty.dialog))
    populated_dialog_bytes = len(_serialize_dialog(populated.dialog))
    combined_bytes = state_bytes + populated_dialog_bytes
    empty_timing = _timing_summary(timings["empty"])
    populated_timing = _timing_summary(timings["populated"])
    mean_delta_ms = (
        float(populated_timing["mean_ms"])
        - float(empty_timing["mean_ms"])
    )
    mean_delta_percent = (
        mean_delta_ms / float(empty_timing["mean_ms"]) * 100.0
        if float(empty_timing["mean_ms"]) > 0
        else 0.0
    )
    return {
        "turns": len(populated.dialog),
        "characters": sum(len(turn.text) for turn in populated.dialog),
        "state_bytes": state_bytes,
        "empty_dialog_bytes": empty_dialog_bytes,
        "populated_dialog_bytes": populated_dialog_bytes,
        "dialog_share_percent": populated_dialog_bytes / combined_bytes * 100.0,
        "empty_touch": empty_timing,
        "populated_touch": populated_timing,
        "mean_delta_ms": mean_delta_ms,
        "mean_delta_percent": mean_delta_percent,
    }


def _git_value(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip()


def _profile_command(args: argparse.Namespace) -> str:
    command = (
        ".\\.venv\\Scripts\\python.exe -B scripts/bench_application_orchestrator.py "
        f"--profile {args.profile} --rate {args.rate:g} --duration {args.duration:g} "
        f"--operations {args.operations} --log-level {args.log_level} "
        f"--report {args.report.as_posix()}"
    )
    if args.allow_short:
        command += " --allow-short"
    return command


def _counter_table(counter: Counter[Any], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "|---|---:|"]
    for key, value in sorted(counter.items(), key=lambda item: str(item[0])):
        rendered = " / ".join(key) if isinstance(key, tuple) else str(key)
        lines.append(f"| `{rendered}` | {value} |")
    return lines


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _render_report(metrics: dict[str, object]) -> str:
    status = str(metrics["status"])
    args = metrics["args"]
    assert isinstance(args, argparse.Namespace)
    timing = metrics["timing"]
    dialog = metrics["dialog"]
    cache = metrics["cache"]
    lifecycle = metrics["lifecycle"]
    integrity = metrics["integrity"]
    criteria = metrics["criteria"]
    session_outcomes = metrics["session_outcomes"]
    assert isinstance(timing, dict)
    assert isinstance(dialog, dict)
    assert isinstance(cache, dict)
    assert isinstance(lifecycle, dict)
    assert isinstance(integrity, dict)
    assert isinstance(criteria, list)
    assert isinstance(session_outcomes, dict)

    outcome_counter = metrics["outcomes"]
    status_counter = metrics["status_triples"]
    assert isinstance(outcome_counter, Counter)
    assert isinstance(status_counter, Counter)

    lines = [
        "# ApplicationOrchestrator — штатный load profile 1",
        "",
        f"**Статус:** {status}.",
        f"**Дата прогона:** {metrics['generated_at']}.",
        "",
        "## Результат для менеджеров",
        "",
    ]
    if status == "PASS":
        lines.extend((
            "Application-ядро завершило весь заданный поток 5 операций в секунду:",
            f"подано и завершено {metrics['submitted']} операций, необработанных исключений нет,",
            f"drain составил {_fmt(float(timing['drain_duration_s']))} с. Все ответы были",
            "полезными штатными исходами сохранения или CAS-конфликта.",
        ))
    elif status == "DIAGNOSTIC":
        lines.extend((
            "Выполнен сокращённый диагностический прогон harness. Он проверяет сборку и",
            "формат отчёта, но не является свидетельством AC-35.",
        ))
    else:
        lines.extend((
            "Профиль не прошёл один или несколько обязательных критериев. Подробности",
            "приведены в таблице приёмки ниже.",
        ))

    lines.extend((
        "",
        "## Команда и окружение",
        "",
        "```powershell",
        str(metrics["command"]),
        "```",
        "",
        "| Параметр | Значение |",
        "|---|---|",
        f"| Git HEAD | `{metrics['git_head']}` |",
        f"| Рабочее дерево | {'dirty' if metrics['git_dirty'] else 'clean'} |",
        f"| Python | `{platform.python_version()}` |",
        f"| Платформа | `{platform.platform()}` |",
        f"| CPU | `{platform.processor() or 'unavailable'}`; logical CPUs: {os.cpu_count()} |",
        f"| Ephemeris | `{metrics['ephemeris_path']}`; mode `{metrics['ephemeris_mode']}` |",
        f"| Logging | requested `{args.log_level}`, effective `{lifecycle['effective_level']}` |",
        f"| Profile | `{args.profile}` |",
        "",
        "## Состав стенда",
        "",
        "Реальные компоненты: `ApplicationOrchestrator`, `BuildNatalHandler`,",
        "`ContextService`, `SqliteSessionPersistence`, `BirthDataResolver`,",
        "`ChartArtifactResolver`, `EngineService`, `InMemoryCalculationCache` и",
        "Swiss calculation backend. HTTP/transport заменён прямым `execute`.",
        "Calculation fixture 10.3 предоставляет resolver/engine/cache; его InMemory",
        "session stack в измеряемом пути не используется.",
        "",
        "Test-only wrapper `PairedLoadBarrierPersistence` полностью делегирует",
        "SQLite. Для пар общих сессий он выпускает оба `touch` через",
        "`asyncio.Barrier(2)` только после завершения реальных чтений. CAS outcomes",
        "не подменяются. Admission controller отсутствует и профилю 1 не требуется.",
        "",
        "Session setup, открытие SQLite, инициализация эфемерид и один warm-up",
        "выполнены до запуска таймера. Verification reads и dialog measurement",
        "выполнены после drain. Executor и временная база закрыты после проверок.",
        "",
        "## Подача и завершение",
        "",
        "| Метрика | Значение |",
        "|---|---:|",
        f"| Настроенный входящий поток | {_fmt(float(args.rate))} ops/s |",
        f"| Плановая длительность подачи | {_fmt(float(timing['planned_submission_duration_s']))} с |",
        f"| Фактическое окно подачи | {_fmt(float(timing['submission_duration_s']))} с |",
        f"| Подано | {metrics['submitted']} |",
        f"| Завершено к остановке подачи | {timing['completed_at_submission_stop']} |",
        f"| Завершено после drain | {metrics['completed']} |",
        f"| Drain | {_fmt(float(timing['drain_duration_s']))} с |",
        f"| Полное время подачи + drain | {_fmt(float(timing['total_duration_s']))} с |",
        f"| Завершённый throughput по окну подачи | {_fmt(float(metrics['completed_throughput']))} ops/s |",
        f"| Максимальное отставание таймера подачи | {_fmt(float(timing['max_schedule_lag_ms']))} мс |",
        f"| Peak active | {metrics['peak_active']} |",
        f"| Active после drain | {metrics['active_after_drain']} |",
        f"| Необработанные исключения | {metrics['unhandled_exceptions']} |",
        "",
        "Подача выполнена парами по таймеру: две операции каждые 0.4 с при 5 RPS.",
        "Это средний входящий поток 5 RPS; barrier используется для доказательства",
        "CAS-пересечения общих пар, а не для задания скорости.",
        "",
        "## Результаты операций",
        "",
    ))
    lines.extend(_counter_table(outcome_counter, ("ApplicationResult", "Количество")))
    lines.extend(("", "### Status triples", ""))
    lines.extend(_counter_table(status_counter, ("orch / handler / context", "Количество")))
    lines.extend(("", "### По типу сессии", ""))
    session_counter = Counter({
        f"{kind} → {outcome}": count
        for kind, outcomes in session_outcomes.items()
        for outcome, count in outcomes.items()
    })
    lines.extend(_counter_table(session_counter, ("Сценарий", "Количество")))

    lines.extend((
        "",
        "## Lifecycle при effective INFO",
        "",
        "| Метрика | Значение |",
        "|---|---:|",
        f"| `application_operation_started` | {lifecycle['started']} |",
        f"| `application_operation_finished` | {lifecycle['finished']} |",
        f"| Started без terminal | {lifecycle['missing_finished']} |",
        f"| Terminal без started | {lifecycle['missing_started']} |",
        f"| Duplicate started/terminal | {lifecycle['duplicates']} |",
        f"| Ошибки разбора records | {lifecycle['parse_errors']} |",
        "",
        "Множества lifecycle `run_id` совпали с поданными операциями и с `run_id`",
        "возвращённых результатов; payload команд и session ID для подсчёта не нужны.",
        "",
        "## Cache и CAS/state integrity",
        "",
        "| Метрика | Значение |",
        "|---|---:|",
        f"| Cache hits | {cache['hits']} ({_fmt(float(cache['hit_percent']))}%) |",
        f"| Cache misses | {cache['misses']} ({_fmt(float(cache['miss_percent']))}%) |",
        f"| Cache put ok | {cache['put_ok']} |",
        f"| Shared load barriers armed/released | {integrity['barriers_armed']} / {integrity['barriers_released']} |",
        f"| AlreadyApplied | {integrity['already_applied']} |",
        f"| Superseded | {integrity['superseded']} |",
        f"| Проверено persisted sessions | {integrity['sessions_checked']} |",
        f"| Нарушения версии/state | {integrity['violations']} |",
        "",
        "Для каждой сессии итоговая `state_version` равна числу её результатов",
        "`Committed`; chart state совпадает с command/artifact последнего commit.",
        "Это проверка отсутствия lost update после завершения всех операций.",
        "",
        "## Оценка overhead dialog snapshot",
        "",
        f"Заполненный dialog: {dialog['turns']} turns, {dialog['characters']} символов.",
        "Размеры вычислены как UTF-8 bytes компактных JSON-представлений state и",
        "массива dialog из реально возвращённого `SessionSnapshot`.",
        "",
        "| Размер | Bytes |",
        "|---|---:|",
        f"| State | {dialog['state_bytes']} |",
        f"| Пустой dialog | {dialog['empty_dialog_bytes']} |",
        f"| Заполненный dialog | {dialog['populated_dialog_bytes']} |",
        f"| Доля dialog в state + dialog | {_fmt(float(dialog['dialog_share_percent']))}% |",
        "",
        "| Touch | Samples | Mean, ms | Min, ms | Max, ms | Spread, ms |",
        "|---|---:|---:|---:|---:|---:|",
    ))
    for label, title in (("empty_touch", "Пустой dialog"), ("populated_touch", "20 × 1000 chars")):
        item = dialog[label]
        assert isinstance(item, dict)
        lines.append(
            f"| {title} | {item['samples']} | {_fmt(float(item['mean_ms']))} | "
            f"{_fmt(float(item['min_ms']))} | {_fmt(float(item['max_ms']))} | "
            f"{_fmt(float(item['spread_ms']))} |"
        )
    lines.extend((
        "",
        f"Разница средних: {_fmt(float(dialog['mean_delta_ms']))} мс "
        f"({_fmt(float(dialog['mean_delta_percent']))}%). Это сравнительная оценка",
        "полного `SessionPersistence.touch`: общий таймер включает SQLite transaction,",
        "decode и scheduler overhead, поэтому разницу нельзя приписать только dialog.",
        "",
        "## Критерии приёмки",
        "",
        "| Критерий | Результат |",
        "|---|---|",
    ))
    for label, passed in criteria:
        lines.append(f"| {label} | {'PASS' if passed else 'FAIL'} |")

    lines.extend((
        "",
        "## Ограничения",
        "",
        "- Это application/core profile без HTTP, client и deployment overhead.",
        "- Admission controller отсутствует; конечный active/queue profile относится к 10.7.",
        "- Отдельный latency SLA и p95/p99 не устанавливались.",
        "- Измерения зависят от машины и текущего рабочего дерева; они не являются SLA.",
        "- Последовательная повторная доставка вне конкурентной пары остаётся отдельной",
        "  семантикой без idempotency key и может создать новый commit.",
        "",
    ))
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> tuple[dict[str, object], bool]:
    ephemeris_status = configure_ephemeris(
        PROJECT_ROOT / "ephe",
        selena_method="true_perigee",
    )
    if ephemeris_status.missing_files:
        raise HarnessInvariantError(
            "ephemeris setup is incomplete: "
            + ", ".join(ephemeris_status.missing_files)
        )
    plans = _build_plans(args.operations)
    session_ids = sorted({plan.session_id for plan in plans})
    setup_ids = [
        *session_ids,
        "profile-warmup",
        "dialog-empty-profile",
        "dialog-full-profile",
    ]
    generated_at = _utc_now().isoformat()
    git_head = _git_value("rev-parse", "HEAD")
    git_dirty = bool(_git_value("status", "--porcelain"))

    with (
        TemporaryDirectory(
            prefix=".exact-orb-application-profile-",
            dir=PROJECT_ROOT,
        ) as temp_dir,
        application_test_stand() as components,
        ThreadPoolExecutor(max_workers=4) as sqlite_executor,
    ):
        database_path = Path(temp_dir) / "application-profile.sqlite3"
        persistence = await SqliteSessionPersistence.open(
            database_path,
            executor=sqlite_executor,
        )
        await _create_sessions(persistence, setup_ids)
        barrier_persistence = PairedLoadBarrierPersistence(persistence)
        context = ContextService(persistence=barrier_persistence, clock=_utc_now)
        orchestrator = build_application_orchestrator(
            context=context,
            clock=_utc_now,
            resolver=components.resolver,
            artifacts=components.artifacts,
        )

        warmup = await orchestrator.execute(
            _command_variant(0),
            session_id="profile-warmup",
            run=RunContext.new(),
        )
        if not isinstance(warmup, ApplicationCommitted):
            raise HarnessInvariantError(f"warm-up failed: {warmup}")
        cache_before = (
            components.artifacts.hits,
            components.artifacts.misses,
            components.artifacts.put_ok,
        )

        collector = LifecycleCollector()
        application_logger = logging.getLogger(APPLICATION_LOGGER)
        previous_handlers = list(application_logger.handlers)
        previous_level = application_logger.level
        previous_propagate = application_logger.propagate
        requested_level = getattr(logging, args.log_level.upper())
        application_logger.handlers = [collector]
        application_logger.setLevel(requested_level)
        application_logger.propagate = False
        effective_level = logging.getLevelName(application_logger.getEffectiveLevel())
        try:
            observations, exceptions, tracker, timing = await _submit_profile(
                orchestrator,
                barrier_persistence,
                plans,
                rate=args.rate,
                duration=args.duration,
            )
        finally:
            application_logger.handlers = previous_handlers
            application_logger.setLevel(previous_level)
            application_logger.propagate = previous_propagate

        cache_after = (
            components.artifacts.hits,
            components.artifacts.misses,
            components.artifacts.put_ok,
        )
        cache_hits = cache_after[0] - cache_before[0]
        cache_misses = cache_after[1] - cache_before[1]
        cache_put_ok = cache_after[2] - cache_before[2]

        expected_run_ids = {str(plan.run.run_id) for plan in plans}
        returned_run_ids = {str(item.result.run_id) for item in observations}
        started_ids = set(collector.started)
        finished_ids = set(collector.finished)
        duplicates = sum(value - 1 for value in collector.started.values() if value > 1)
        duplicates += sum(value - 1 for value in collector.finished.values() if value > 1)

        outcomes: Counter[str] = Counter(type(item.result).__name__ for item in observations)
        status_triples: Counter[tuple[str, str, str]] = Counter(
            (
                item.result.orch_status,
                item.result.handler_status,
                item.result.context_status,
            )
            for item in observations
        )
        session_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
        for item in observations:
            session_outcomes[item.plan.session_kind][type(item.result).__name__] += 1

        useful_types = (ApplicationCommitted, ApplicationAlreadyApplied, ApplicationSuperseded)
        useful_count = sum(isinstance(item.result, useful_types) for item in observations)
        committed_by_session: Counter[str] = Counter()
        last_commit: dict[str, OperationObservation] = {}
        for item in observations:
            if isinstance(item.result, ApplicationCommitted):
                committed_by_session[item.plan.session_id] += 1
                previous = last_commit.get(item.plan.session_id)
                if previous is None or item.result.state_version > previous.result.state_version:
                    last_commit[item.plan.session_id] = item

        integrity_violations: list[str] = []
        for session_id in session_ids:
            stored = await persistence.sessions.get(session_id, now=_utc_now())
            if not isinstance(stored, SessionState):
                integrity_violations.append(f"{session_id}: {stored}")
                continue
            expected_version = committed_by_session[session_id]
            if stored.state_version != expected_version:
                integrity_violations.append(
                    f"{session_id}: version {stored.state_version} != commits {expected_version}"
                )
                continue
            winner = last_commit.get(session_id)
            if winner is None:
                integrity_violations.append(f"{session_id}: no committed winner")
                continue
            if (
                stored.birth_input != winner.plan.command.birth_input
                or stored.base_chart is None
                or stored.base_chart.spec != winner.result.artifact.spec
                or stored.base_chart.state_version != stored.state_version
            ):
                integrity_violations.append(f"{session_id}: final state does not match winner")

        dialog = await _measure_dialog_overhead(persistence, orchestrator)

    cache_total = cache_hits + cache_misses
    submission_duration = float(timing["submission_duration_s"])
    completed_throughput = tracker.completed / submission_duration
    lifecycle = {
        "effective_level": effective_level,
        "started": sum(collector.started.values()),
        "finished": sum(collector.finished.values()),
        "missing_finished": len(started_ids - finished_ids),
        "missing_started": len(finished_ids - started_ids),
        "duplicates": duplicates,
        "parse_errors": len(collector.parse_errors),
    }
    integrity = {
        "barriers_armed": barrier_persistence.pairs_armed,
        "barriers_released": barrier_persistence.pairs_released,
        "already_applied": outcomes["ApplicationAlreadyApplied"],
        "superseded": outcomes["ApplicationSuperseded"],
        "sessions_checked": len(session_ids),
        "violations": len(integrity_violations),
        "violation_details": integrity_violations,
    }
    criteria: list[tuple[str, bool]] = [
        ("Настроено не менее 5 RPS", args.rate >= 5.0),
        ("Подача длилась не менее 60 секунд", submission_duration >= 60.0),
        ("Подано не менее 300 операций", tracker.submitted >= 300),
        ("Все поданные операции завершены", tracker.completed == tracker.submitted),
        ("После drain active = 0", tracker.active == 0),
        ("Наблюдалось одновременное выполнение", tracker.peak_active > 1),
        ("Необработанных исключений нет", not exceptions),
        ("Все outcomes полезны и допустимы", useful_count == tracker.submitted),
        ("Lifecycle started/terminal полон и уникален", (
            started_ids == finished_ids == expected_run_ids == returned_run_ids
            and duplicates == 0
            and not collector.parse_errors
        )),
        ("Cache hit/miss учёл все Handler success", cache_total == tracker.submitted),
        ("Обе CAS-классификации наблюдались", (
            outcomes["ApplicationAlreadyApplied"] > 0
            and outcomes["ApplicationSuperseded"] > 0
        )),
        ("Все load barriers завершены", (
            barrier_persistence.pairs_armed == barrier_persistence.pairs_released
        )),
        ("Persisted версии и state согласованы", not integrity_violations),
        ("Logging effective INFO", effective_level == "INFO"),
    ]
    acceptance_passed = all(passed for _, passed in criteria)
    status = "DIAGNOSTIC" if args.allow_short else ("PASS" if acceptance_passed else "FAIL")
    metrics: dict[str, object] = {
        "status": status,
        "args": args,
        "generated_at": generated_at,
        "command": _profile_command(args),
        "git_head": git_head,
        "git_dirty": git_dirty,
        "ephemeris_path": ephemeris_status.path,
        "ephemeris_mode": ephemeris_status.mode,
        "submitted": tracker.submitted,
        "completed": tracker.completed,
        "peak_active": tracker.peak_active,
        "active_after_drain": tracker.active,
        "unhandled_exceptions": len(exceptions),
        "completed_throughput": completed_throughput,
        "timing": timing,
        "outcomes": outcomes,
        "status_triples": status_triples,
        "session_outcomes": dict(session_outcomes),
        "cache": {
            "hits": cache_hits,
            "misses": cache_misses,
            "put_ok": cache_put_ok,
            "hit_percent": cache_hits / cache_total * 100.0 if cache_total else 0.0,
            "miss_percent": cache_misses / cache_total * 100.0 if cache_total else 0.0,
        },
        "lifecycle": lifecycle,
        "integrity": integrity,
        "dialog": dialog,
        "criteria": criteria,
    }
    return metrics, acceptance_passed


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the normal ApplicationOrchestrator load profile.",
    )
    parser.add_argument("--profile", choices=("normal",), required=True)
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--operations", type=int, required=True)
    parser.add_argument("--log-level", choices=("INFO",), required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--allow-short",
        action="store_true",
        help="Permit a diagnostic run below profile-1 thresholds; never reports PASS.",
    )
    args = parser.parse_args()
    if not math.isfinite(args.rate) or args.rate <= 0:
        parser.error("--rate must be a finite positive number")
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration must be a finite positive number")
    if args.operations <= 0:
        parser.error("--operations must be positive")
    minimum_window = math.ceil(args.operations / BATCH_SIZE) * BATCH_SIZE / args.rate
    if args.duration + 1e-9 < minimum_window:
        parser.error("--duration is too short for --operations at the configured rate")
    if not args.allow_short and (
        args.rate < 5.0 or args.duration < 60.0 or args.operations < 300
    ):
        parser.error("normal profile requires rate >= 5, duration >= 60, operations >= 300")
    return args


def main() -> int:
    args = _parse_arguments()
    try:
        metrics, acceptance_passed = asyncio.run(_run(args))
        report = _render_report(metrics)
        report_path = args.report
        if not report_path.is_absolute():
            report_path = PROJECT_ROOT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8", newline="\n")
        print(json.dumps({
            "status": metrics["status"],
            "submitted": metrics["submitted"],
            "completed": metrics["completed"],
            "peak_active": metrics["peak_active"],
            "drain_duration_s": metrics["timing"]["drain_duration_s"],  # type: ignore[index]
            "report": str(report_path),
        }, ensure_ascii=False, separators=(",", ":")))
        return 0 if acceptance_passed or args.allow_short else 1
    except (HarnessInvariantError, OSError, ValueError) as exc:
        print(f"application load profile failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
