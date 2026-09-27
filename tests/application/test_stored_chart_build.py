"""BuildNatal stored chart handoff and pre-commit failures on real coordinators."""

from __future__ import annotations

from datetime import date, time
import logging
import traceback

import pytest

from exact_orb.application.application_results import ApplicationCommitted, ApplicationInternalFailure
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.handlers.build_natal import (
    BuildNatalHandler,
    StoredChartPreparationError,
)
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.types import BirthInput
from exact_orb.calculation.codec import decode_chart_artifact
from exact_orb.calculation.errors import ChartArtifactEncodingError
from exact_orb.component_logging import serialize_component_message
from exact_orb.session.outcomes import Committed
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import apply_delta, new_session
from tests.application.orchestrator_fakes import Call, RecordingContext
from tests.application.stubs import StubBirthDataResolver, StubChartArtifactPort
from tests.fixtures.calculation import BASE_UTC, resolved_birth_data, run_context


SESSION_ID = "stored-chart-build"
SENSITIVE = "input_value=private-chart-payload-prefix"


def _command() -> BuildNatalCommand:
    return BuildNatalCommand(birth_input=BirthInput(
        birth_date=date(1990, 9, 2), birth_time=time(14, 30), place_id="524901",
    ))


class CapturingHandler(BuildNatalHandler):
    result: BuildNatalSuccess | None = None

    async def handle(self, command, state, run):
        outcome = await super().handle(command, state, run)
        if isinstance(outcome, BuildNatalSuccess):
            self.result = outcome
        return outcome


async def test_success_passes_the_same_complete_delta_from_handler_to_save(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="exact_orb.application")
    state = new_session(SESSION_ID, now=BASE_UTC)
    snapshot = SessionSnapshot(state=state, dialog=(), chart=None)
    journal: list[Call] = []
    context = RecordingContext(
        journal, load_result=snapshot, save_result=Committed(state_version=1),
    )
    artifacts = StubChartArtifactPort()
    handler = CapturingHandler(
        resolver=StubBirthDataResolver(resolved_birth_data()), artifacts=artifacts,
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: handler}, clock=lambda: BASE_UTC,
    )
    run = run_context()

    result = await orchestrator.execute(_command(), session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationCommitted)
    assert handler.result is not None
    assert artifacts.calls == artifacts.to_stored_calls == 1
    assert artifacts.received_artifact is handler.result.artifact
    assert journal == [
        Call(context, "load", (SESSION_ID,)),
        Call(context, "save", (SESSION_ID, 0, handler.result.delta)),
    ]
    assert journal[1].args[2] is handler.result.delta
    stored = handler.result.delta.base_chart_payload
    assert stored is not None
    assert stored.calculation_key == result.artifact.calculation_key
    assert stored.calculation_version == result.artifact.calculation_version
    assert decode_chart_artifact(stored.payload) == result.artifact
    assert state.base_chart is None

    handoff = [record.getMessage() for record in caplog.records
               if "operation=to_stored" in record.getMessage()
               and record.getMessage().startswith("application_message ")]
    assert len(handoff) == 2
    assert "direction=send" in handoff[0]
    assert "message_type=ToStoredRequest" in handoff[0]
    assert "peer=StubChartArtifactPort" in handoff[0]
    assert "direction=receive" in handoff[1]
    assert "message_type=StoredChartEncoding" in handoff[1]
    assert "peer=StubChartArtifactPort" in handoff[1]
    assert all(f"run_id={run.run_id}" in message for message in handoff)

    populated = apply_delta(state, handler.result.delta, now=BASE_UTC)
    projection = serialize_component_message(SessionSnapshot(
        state=populated, dialog=(), chart=stored,
    ))
    assert '"payload_size":' in projection
    assert '"calculation_key":' in projection
    assert stored.payload[:12].decode("utf-8", errors="backslashreplace") not in projection


@pytest.mark.parametrize(
    ("stored_result", "expected_reason"),
    [
        (ChartArtifactEncodingError("CHART_ARTIFACT_ENCODE_FAILED"), "ENCODE_FAILED"),
        (RuntimeError(SENSITIVE), "ENCODE_FAILED"),
        ((1, b""), "PAYLOAD_SIZE_INVALID"),
        ((1, b"x" * 1_048_577), "PAYLOAD_SIZE_INVALID"),
        ((0, SENSITIVE.encode()), "ENVELOPE_INVALID"),
    ],
    ids=("typed-encoding", "unexpected-encoding", "empty", "oversize", "invalid-envelope"),
)
async def test_preparation_failure_is_safe_and_never_reaches_save(
    stored_result: object,
    expected_reason: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="exact_orb.application")
    state = new_session(SESSION_ID, now=BASE_UTC)
    journal: list[Call] = []
    context = RecordingContext(
        journal,
        load_result=SessionSnapshot(state=state, dialog=(), chart=None),
        save_result=Committed(state_version=1),
    )
    artifacts = StubChartArtifactPort(stored_result=stored_result)
    handler = BuildNatalHandler(
        resolver=StubBirthDataResolver(resolved_birth_data()), artifacts=artifacts,
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: handler}, clock=lambda: BASE_UTC,
    )
    run = run_context()

    result = await orchestrator.execute(_command(), session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationInternalFailure)
    assert (result.handler_status, result.context_status) == (
        "UNEXPECTED_FAILURE", "LOADED",
    )
    assert result.code == "INTERNAL_FAILURE"
    assert journal == [Call(context, "load", (SESSION_ID,))]
    assert artifacts.calls == artifacts.to_stored_calls == 1
    assert state.base_chart is None
    diagnostics = [record for record in caplog.records
                   if record.name == "exact_orb.application.orchestrator"
                   and record.exc_info is not None]
    assert len(diagnostics) == 1
    error = diagnostics[0].exc_info[1]
    assert isinstance(error, StoredChartPreparationError)
    assert error.reason == expected_reason
    assert error.__suppress_context__ is True
    formatted = "\n".join(
        logging.Formatter().format(record) for record in caplog.records
    )
    assert expected_reason in formatted
    assert "StoredChartPreparationError" in formatted
    assert SENSITIVE not in formatted
    assert "input_value" not in formatted
    assert SENSITIVE not in "".join(traceback.format_exception(error))
    handoff = [record.getMessage() for record in caplog.records
               if "operation=to_stored" in record.getMessage()
               and record.getMessage().startswith("application_message ")]
    assert len(handoff) == (1 if expected_reason == "ENCODE_FAILED" else 2)
    assert "direction=send" in handoff[0]
    if expected_reason == "ENCODE_FAILED":
        assert all("direction=receive" not in message for message in handoff)
    terminal = [record.getMessage() for record in caplog.records
                if record.getMessage().startswith("build_natal_failed ")]
    assert len(terminal) == 1
    assert "exception_type=StoredChartPreparationError" in terminal[0]
