"""Pure restoration projection for a stored chart."""

from __future__ import annotations

from datetime import date, time
import gzip
import json
import logging

import pytest

from exact_orb.application.session_view import (
    ChartReadySessionView,
    ChartUnavailableSessionView,
    EmptySessionView,
    session_view,
)
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.spec import ChartSpec
from exact_orb.calculation.types import ChartArtifact
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import StateDelta, StoredChart, apply_delta, new_session
from tests.fixtures.calculation import (
    BASE_UTC,
    OTHER_VERSION,
    VERSION,
    artifact,
    resolved_birth_data,
)
from tests.fixtures.stored_chart import stored_chart_for


BIRTH_INPUT = BirthInput(
    birth_date=date(1990, 9, 2), birth_time=time(14, 30), place_id="524901"
)


def _snapshot(
    chart: ChartArtifact,
    *,
    stored: StoredChart | None = None,
    spec: ChartSpec | None = None,
    resolved: ResolvedBirthData | None = None,
) -> SessionSnapshot:
    stored = stored if stored is not None else stored_chart_for(chart)
    state = apply_delta(
        new_session("session-view", now=BASE_UTC),
        StateDelta(
            birth_input=BIRTH_INPUT,
            birth_resolved=resolved if resolved is not None else resolved_birth_data(),
            base_chart_spec=spec if spec is not None else chart.spec,
            base_chart_payload=stored,
        ),
        now=BASE_UTC,
    )
    return SessionSnapshot(state=state, dialog=(), chart=stored)


def test_empty_snapshot_projects_only_state_version() -> None:
    snapshot = SessionSnapshot(
        state=new_session("session-view", now=BASE_UTC), dialog=(), chart=None
    )

    result = session_view(snapshot, VERSION)

    assert result == EmptySessionView(state_version=0)
    assert result.status == "empty"


@pytest.mark.parametrize("current_version, stale", [(VERSION, False), (OTHER_VERSION, True)])
def test_valid_stored_chart_is_restored_without_changing_snapshot(
    current_version: str, stale: bool
) -> None:
    original = artifact()
    snapshot = _snapshot(original)
    before = snapshot.model_copy(deep=True)

    result = session_view(snapshot, current_version)

    assert isinstance(result, ChartReadySessionView)
    assert result.status == "chart_ready"
    assert result.state_version == 1
    assert result.birth_input == BIRTH_INPUT
    assert result.canonical_place == "Moscow"
    assert result.artifact == original
    assert result.artifact is not original
    assert result.chart_stale is stale
    assert snapshot == before


@pytest.mark.parametrize(
    "payload, reason",
    [
        (b"not gzip", "DECODE_GZIP_FAILED"),
        (gzip.compress(b"\xff", mtime=0), "DECODE_UTF8_FAILED"),
        (gzip.compress(b"{}", mtime=0), "DECODE_VALIDATION_FAILED"),
    ],
)
def test_decode_failures_return_safe_reason_and_preserve_form(
    payload: bytes, reason: str, caplog: pytest.LogCaptureFixture
) -> None:
    chart = artifact()
    stored = stored_chart_for(chart).model_copy(update={"payload": payload})
    snapshot = _snapshot(chart, stored=stored)
    before = snapshot.model_copy(deep=True)
    caplog.set_level(logging.ERROR)

    result = session_view(snapshot, OTHER_VERSION)

    assert isinstance(result, ChartUnavailableSessionView)
    assert result.status == "chart_unavailable"
    assert result.safe_reason == reason
    assert (result.state_version, result.birth_input, result.canonical_place) == (
        1, BIRTH_INPUT, "Moscow"
    )
    assert snapshot == before
    assert caplog.records == []


def test_unsupported_format_precedes_decode_and_preserves_snapshot() -> None:
    chart = artifact()
    stored = stored_chart_for(chart).model_copy(
        update={"payload_format": 99, "payload": b"not gzip"}
    )
    snapshot = _snapshot(chart, stored=stored)
    before = snapshot.model_copy(deep=True)

    result = session_view(snapshot, VERSION)

    assert isinstance(result, ChartUnavailableSessionView)
    assert result.safe_reason == "UNSUPPORTED_PAYLOAD_FORMAT"
    assert snapshot == before


def test_invalid_artifact_identity_is_a_decode_validation_failure() -> None:
    chart = artifact()
    stored = stored_chart_for(chart)
    document = json.loads(gzip.decompress(stored.payload))
    document["calculation_key"] = "different-internal-key"
    tampered = stored.model_copy(update={
        "payload": gzip.compress(json.dumps(document).encode("utf-8"), mtime=0)
    })

    result = session_view(_snapshot(chart, stored=tampered), VERSION)

    assert isinstance(result, ChartUnavailableSessionView)
    assert result.safe_reason == "DECODE_VALIDATION_FAILED"


@pytest.mark.parametrize(
    "case, reason",
    [
        ("key", "CALCULATION_KEY_MISMATCH"),
        ("version", "CALCULATION_VERSION_MISMATCH"),
        ("spec", "SPEC_MISMATCH"),
        ("input", "CALCULATION_INPUT_MISMATCH"),
    ],
)
def test_consistency_checks_return_their_own_reason(
    case: str, reason: str
) -> None:
    chart = artifact()
    stored = stored_chart_for(chart)
    spec = chart.spec
    resolved = resolved_birth_data()
    if case == "key":
        stored = stored.model_copy(update={"calculation_key": "other-key"})
    elif case == "version":
        stored = stored.model_copy(update={"calculation_version": OTHER_VERSION})
    elif case == "spec":
        spec = chart.spec.model_copy(update={"near_interception_threshold": 2.0})
    else:
        resolved = resolved_birth_data(latitude=56.0)

    result = session_view(
        _snapshot(chart, stored=stored, spec=spec, resolved=resolved), OTHER_VERSION
    )

    assert isinstance(result, ChartUnavailableSessionView)
    assert result.safe_reason == reason


@pytest.mark.parametrize(
    "payload, key, version, spec_changed, input_changed, reason",
    [
        (b"not gzip", "wrong", OTHER_VERSION, True, True, "DECODE_GZIP_FAILED"),
        (None, "wrong", OTHER_VERSION, True, True, "CALCULATION_KEY_MISMATCH"),
        (None, None, OTHER_VERSION, True, True, "CALCULATION_VERSION_MISMATCH"),
        (None, None, None, True, True, "SPEC_MISMATCH"),
        (None, None, None, False, True, "CALCULATION_INPUT_MISMATCH"),
    ],
)
def test_first_failed_check_wins_before_staleness(
    payload: bytes | None,
    key: str | None,
    version: str | None,
    spec_changed: bool,
    input_changed: bool,
    reason: str,
) -> None:
    chart = artifact()
    updates: dict[str, object] = {}
    if payload is not None:
        updates["payload"] = payload
    if key is not None:
        updates["calculation_key"] = key
    if version is not None:
        updates["calculation_version"] = version
    stored = stored_chart_for(chart).model_copy(update=updates)
    snapshot = _snapshot(
        chart,
        stored=stored,
        spec=(chart.spec.model_copy(update={"near_interception_threshold": 2.0})
              if spec_changed else chart.spec),
        resolved=resolved_birth_data(latitude=56.0) if input_changed else None,
    )

    result = session_view(snapshot, OTHER_VERSION)

    assert isinstance(result, ChartUnavailableSessionView)
    assert result.safe_reason == reason
