"""Unit tests for immutable session state and pure transitions."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest
from pydantic import ValidationError

import exact_orb.session.state as state_module
from exact_orb.birth.types import BirthInput, ResolutionWarning, ResolvedBirthData
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.session.errors import (
    ExpiredSessionTransitionError,
    SessionPersistenceError,
)
from exact_orb.session.state import (
    HARD_TTL,
    RESET_DELTA,
    SLIDING_TTL,
    ChartRef,
    SessionState,
    StateDelta,
    StoredChart,
    apply_delta,
    is_expired,
    matches_intent,
    new_session,
    require_utc,
    touched,
)


NOW = datetime(2026, 9, 5, 12, tzinfo=UTC)
BIRTH_INPUT = BirthInput(
    birth_date=date(1990, 9, 2),
    birth_time=time(12, 30),
    place_id="moscow",
)
OTHER_BIRTH_INPUT = BirthInput(
    birth_date=BIRTH_INPUT.birth_date,
    birth_time=BIRTH_INPUT.birth_time,
    place_id="same-resolved-place-alias",
)
WARNING = ResolutionWarning(source="place", code="NORMALIZED", message="normalized")
RESOLVED = ResolvedBirthData(
    utc_datetime=datetime(1990, 9, 2, 8, 30, tzinfo=UTC),
    latitude=55.75,
    longitude=37.62,
    tz_id="Europe/Moscow",
    utc_offset_seconds=14_400,
    canonical_place="Moscow",
    time_unknown=False,
    birth_time_domain=None,
    warnings=(WARNING,),
)
OTHER_RESOLVED = ResolvedBirthData(
    utc_datetime=datetime(1990, 9, 2, 9, 30, tzinfo=UTC),
    latitude=55.75,
    longitude=37.62,
    tz_id="Europe/Moscow",
    utc_offset_seconds=14_400,
    canonical_place="Moscow",
    time_unknown=False,
    birth_time_domain=None,
)
SPEC = NatalChartSpec(chart_kind="natal")
OTHER_SPEC = NatalChartSpec(chart_kind="cosmogram")
STORED_CHART = StoredChart(
    payload_format=1,
    calculation_key="key-1",
    calculation_version="version-1",
    payload=b"opaque-chart",
)
DELTA = StateDelta(
    birth_input=BIRTH_INPUT,
    birth_resolved=RESOLVED,
    base_chart_spec=SPEC,
    base_chart_payload=STORED_CHART,
)


def _populated_state(
    *,
    state_version: int = 1,
    created_at: datetime = NOW,
    expires_at: datetime = NOW + SLIDING_TTL,
    hard_expires_at: datetime = NOW + HARD_TTL,
) -> SessionState:
    return SessionState(
        session_id="session-1",
        birth_input=BIRTH_INPUT,
        birth_resolved=RESOLVED,
        state_version=state_version,
        base_chart=ChartRef(state_version=state_version, spec=SPEC),
        created_at=created_at,
        expires_at=expires_at,
        hard_expires_at=hard_expires_at,
    )


def _empty_state_values() -> dict[str, object]:
    return {
        "session_id": "session-1",
        "birth_input": None,
        "birth_resolved": None,
        "state_version": 0,
        "base_chart": None,
        "created_at": NOW,
        "expires_at": NOW + SLIDING_TTL,
        "hard_expires_at": NOW + HARD_TTL,
    }


@pytest.mark.parametrize(
    ("model", "field", "new_value"),
    [
        (BIRTH_INPUT, "place_id", "changed"),
        (WARNING, "message", "changed"),
        (RESOLVED, "canonical_place", "changed"),
        (ChartRef(state_version=1, spec=SPEC), "state_version", 2),
        (_populated_state(), "state_version", 2),
        (DELTA, "base_chart_spec", OTHER_SPEC),
        (STORED_CHART, "payload_format", 2),
    ],
)
def test_contract_models_are_frozen(model: object, field: str, new_value: object) -> None:
    with pytest.raises(ValidationError, match="frozen"):
        setattr(model, field, new_value)


@pytest.mark.parametrize("state_version", [0, -1])
def test_chart_ref_requires_positive_state_version(state_version: int) -> None:
    with pytest.raises(ValidationError):
        ChartRef(state_version=state_version, spec=SPEC)


def test_session_state_rejects_empty_id_and_negative_version() -> None:
    values = _empty_state_values()
    values["session_id"] = ""
    with pytest.raises(ValidationError):
        SessionState(**values)

    values = _empty_state_values()
    values["state_version"] = -1
    with pytest.raises(ValidationError):
        SessionState(**values)


@pytest.mark.parametrize(
    ("birth_input", "birth_resolved", "base_chart"),
    [
        (BIRTH_INPUT, None, None),
        (None, RESOLVED, None),
        (None, None, ChartRef(state_version=1, spec=SPEC)),
        (BIRTH_INPUT, RESOLVED, None),
        (BIRTH_INPUT, None, ChartRef(state_version=1, spec=SPEC)),
        (None, RESOLVED, ChartRef(state_version=1, spec=SPEC)),
    ],
)
def test_session_state_rejects_partial_content(
    birth_input: BirthInput | None,
    birth_resolved: ResolvedBirthData | None,
    base_chart: ChartRef | None,
) -> None:
    values = _empty_state_values()
    values.update(
        birth_input=birth_input,
        birth_resolved=birth_resolved,
        state_version=1,
        base_chart=base_chart,
    )
    with pytest.raises(ValidationError, match="all set or all None"):
        SessionState(**values)


def test_empty_state_may_keep_a_nonzero_version_after_reset() -> None:
    values = _empty_state_values()
    values["state_version"] = 4

    state = SessionState(**values)

    assert state.state_version == 4
    assert state.birth_input is state.birth_resolved is state.base_chart is None


def test_session_state_rejects_chart_from_another_version() -> None:
    values = _empty_state_values()
    values.update(
        birth_input=BIRTH_INPUT,
        birth_resolved=RESOLVED,
        state_version=2,
        base_chart=ChartRef(state_version=1, spec=SPEC),
    )
    with pytest.raises(ValidationError, match="base_chart.state_version"):
        SessionState(**values)


@pytest.mark.parametrize("field", ["created_at", "expires_at", "hard_expires_at"])
@pytest.mark.parametrize(
    "invalid_timestamp",
    [
        datetime(2026, 9, 5, 12),
        datetime(2026, 9, 5, 15, tzinfo=timezone(timedelta(hours=3))),
    ],
)
def test_session_state_requires_utc_timestamps(
    field: str,
    invalid_timestamp: datetime,
) -> None:
    values = _empty_state_values()
    values[field] = invalid_timestamp
    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        SessionState(**values)


@pytest.mark.parametrize(
    ("created_at", "expires_at", "hard_expires_at"),
    [
        (NOW + timedelta(days=2), NOW + timedelta(days=1), NOW + HARD_TTL),
        (NOW, NOW + HARD_TTL, NOW + timedelta(days=29)),
    ],
)
def test_session_state_requires_ordered_timestamps(
    created_at: datetime,
    expires_at: datetime,
    hard_expires_at: datetime,
) -> None:
    values = _empty_state_values()
    values.update(
        created_at=created_at,
        expires_at=expires_at,
        hard_expires_at=hard_expires_at,
    )
    with pytest.raises(ValidationError, match="created_at <= expires_at"):
        SessionState(**values)


def test_persisted_state_does_not_require_current_hard_ttl_formula() -> None:
    values = _empty_state_values()
    values.update(
        expires_at=NOW + timedelta(days=3),
        hard_expires_at=NOW + timedelta(days=10),
    )

    state = SessionState(**values)

    assert state.hard_expires_at == NOW + timedelta(days=10)


def test_state_delta_fields_are_required() -> None:
    with pytest.raises(ValidationError, match="Field required"):
        StateDelta()

    assert StateDelta.model_fields["base_chart_payload"].is_required()


@pytest.mark.parametrize("size", (1, 1_048_576))
def test_stored_chart_accepts_opaque_payload_at_size_boundaries(size: int) -> None:
    chart = StoredChart(
        payload_format=1,
        calculation_key="key-1",
        calculation_version="version-1",
        payload=b"\x00" * size,
    )

    assert chart.payload == b"\x00" * size


@pytest.mark.parametrize("size", (0, 1_048_577))
def test_stored_chart_rejects_payload_outside_size_boundaries(size: int) -> None:
    with pytest.raises(ValidationError, match="payload"):
        StoredChart(
            payload_format=1,
            calculation_key="key-1",
            calculation_version="version-1",
            payload=b"x" * size,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("payload_format", 0),
        ("payload_format", -1),
        ("payload_format", True),
        ("calculation_key", ""),
        ("calculation_version", ""),
        ("payload", "not bytes"),
    ),
)
def test_stored_chart_rejects_invalid_envelope(field: str, value: object) -> None:
    with pytest.raises(ValidationError, match=field):
        StoredChart.model_validate({**STORED_CHART.model_dump(), field: value})


@pytest.mark.parametrize("present_mask", range(1, 15))
def test_state_delta_rejects_partial_replacement(present_mask: int) -> None:
    values = (BIRTH_INPUT, RESOLVED, SPEC, STORED_CHART)
    selected = tuple(
        value if present_mask & (1 << index) else None
        for index, value in enumerate(values)
    )

    with pytest.raises(ValidationError, match="all set or all None"):
        StateDelta(
            birth_input=selected[0],
            birth_resolved=selected[1],
            base_chart_spec=selected[2],
            base_chart_payload=selected[3],
        )


def test_reset_delta_is_an_explicit_immutable_full_replacement() -> None:
    assert RESET_DELTA == StateDelta(
        birth_input=None,
        birth_resolved=None,
        base_chart_spec=None,
        base_chart_payload=None,
    )
    with pytest.raises(ValidationError, match="frozen"):
        RESET_DELTA.birth_input = BIRTH_INPUT


def test_new_session_sets_exact_initial_version_and_lifetimes() -> None:
    state = new_session("new-session", now=NOW)

    assert state.session_id == "new-session"
    assert state.state_version == 0
    assert state.birth_input is state.birth_resolved is state.base_chart is None
    assert state.created_at == NOW
    assert state.expires_at == NOW + SLIDING_TTL
    assert state.hard_expires_at == NOW + HARD_TTL


def test_require_utc_returns_the_same_aware_utc_object() -> None:
    assert require_utc(NOW) is NOW


@pytest.mark.parametrize(
    "invalid_timestamp",
    [
        datetime(2026, 9, 5, 12),
        datetime(2026, 9, 5, 15, tzinfo=timezone(timedelta(hours=3))),
    ],
    ids=["naive", "non-zero-offset"],
)
def test_require_utc_rejects_invalid_timestamps_with_the_supplied_name(
    invalid_timestamp: datetime,
) -> None:
    with pytest.raises(ValueError) as caught:
        require_utc(invalid_timestamp, name="port time")

    assert type(caught.value) is ValueError
    assert str(caught.value) == "port time must be timezone-aware UTC"


def test_require_utc_uses_timestamp_as_the_default_name() -> None:
    with pytest.raises(ValueError) as caught:
        require_utc(datetime(2026, 9, 5, 12))

    assert type(caught.value) is ValueError
    assert str(caught.value) == "timestamp must be timezone-aware UTC"


def test_require_utc_is_exported_by_the_state_module() -> None:
    assert "require_utc" in state_module.__all__


@pytest.mark.parametrize(
    "invalid_now",
    [
        datetime(2026, 9, 5, 12),
        datetime(2026, 9, 5, 15, tzinfo=timezone(timedelta(hours=3))),
    ],
)
def test_transition_functions_require_utc_now(invalid_now: datetime) -> None:
    state = _populated_state()

    with pytest.raises(ValueError, match="timezone-aware UTC"):
        new_session("new-session", now=invalid_now)
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        is_expired(state, now=invalid_now)
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        touched(state, now=invalid_now)
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        apply_delta(state, DELTA, now=invalid_now)


def test_apply_delta_replaces_content_and_increments_version_once() -> None:
    state = _populated_state(state_version=3)
    changed = StateDelta(
        birth_input=OTHER_BIRTH_INPUT,
        birth_resolved=OTHER_RESOLVED,
        base_chart_spec=OTHER_SPEC,
        base_chart_payload=STORED_CHART,
    )

    candidate = apply_delta(state, changed, now=NOW + timedelta(days=1))

    assert candidate.session_id == state.session_id
    assert candidate.birth_input == OTHER_BIRTH_INPUT
    assert candidate.birth_resolved == OTHER_RESOLVED
    assert candidate.state_version == 4
    assert candidate.base_chart == ChartRef(state_version=4, spec=OTHER_SPEC)
    assert candidate.created_at == state.created_at
    assert candidate.expires_at == NOW + timedelta(days=8)
    assert candidate.hard_expires_at == state.hard_expires_at


def test_apply_reset_clears_content_but_never_resets_version_to_zero() -> None:
    state = _populated_state(state_version=4)

    candidate = apply_delta(state, RESET_DELTA, now=NOW + timedelta(days=1))

    assert candidate.state_version == 5
    assert (
        candidate.birth_input
        is candidate.birth_resolved
        is candidate.base_chart
        is None
    )


def test_renewal_never_shortens_and_never_exceeds_hard_expiration() -> None:
    state = _populated_state(
        expires_at=NOW + timedelta(days=20),
        hard_expires_at=NOW + timedelta(days=21),
    )

    early_touch = touched(state, now=NOW + timedelta(days=1))
    capped_touch = touched(state, now=NOW + timedelta(days=15))

    assert early_touch.expires_at == state.expires_at
    assert capped_touch.expires_at == state.hard_expires_at
    assert capped_touch.hard_expires_at == state.hard_expires_at


def test_touched_changes_only_sliding_expiration() -> None:
    state = _populated_state(state_version=3)

    candidate = touched(state, now=NOW + timedelta(days=1))

    assert candidate.expires_at == NOW + timedelta(days=8)
    assert candidate.model_copy(update={"expires_at": state.expires_at}) == state


def test_is_expired_at_sliding_boundary() -> None:
    state = _populated_state()

    assert not is_expired(state, now=state.expires_at - timedelta(microseconds=1))
    assert is_expired(state, now=state.expires_at)


def test_is_expired_at_hard_boundary_even_with_later_sliding_expiration() -> None:
    values = _empty_state_values()
    values.update(
        expires_at=NOW + timedelta(days=30),
        hard_expires_at=NOW + timedelta(days=30),
    )
    state = SessionState(**values)

    assert is_expired(state, now=state.hard_expires_at)


@pytest.mark.parametrize("transition", ["apply", "touch"])
def test_expired_state_cannot_transition(transition: str) -> None:
    state = _populated_state()

    with pytest.raises(ExpiredSessionTransitionError) as caught:
        if transition == "apply":
            apply_delta(state, DELTA, now=state.expires_at)
        else:
            touched(state, now=state.expires_at)

    assert caught.value.error_code == "SESSION_EXPIRED"
    assert isinstance(caught.value, ValueError)
    assert not isinstance(caught.value, SessionPersistenceError)


def test_matches_intent_for_applied_delta() -> None:
    actual = apply_delta(new_session("session-1", now=NOW), DELTA, now=NOW)

    assert matches_intent(actual, DELTA)


def test_matches_intent_rejects_different_resolved_data_or_spec() -> None:
    actual = apply_delta(new_session("session-1", now=NOW), DELTA, now=NOW)
    different_resolved = StateDelta(
        birth_input=BIRTH_INPUT,
        birth_resolved=OTHER_RESOLVED,
        base_chart_spec=SPEC,
        base_chart_payload=STORED_CHART,
    )
    different_spec = StateDelta(
        birth_input=BIRTH_INPUT,
        birth_resolved=RESOLVED,
        base_chart_spec=OTHER_SPEC,
        base_chart_payload=STORED_CHART,
    )

    assert not matches_intent(actual, different_resolved)
    assert not matches_intent(actual, different_spec)


def test_matches_intent_excludes_original_birth_input() -> None:
    actual = apply_delta(new_session("session-1", now=NOW), DELTA, now=NOW)
    same_calculation_intent = StateDelta(
        birth_input=OTHER_BIRTH_INPUT,
        birth_resolved=RESOLVED,
        base_chart_spec=SPEC,
        base_chart_payload=STORED_CHART,
    )

    assert matches_intent(actual, same_calculation_intent)


def test_matches_intent_does_not_compare_stored_chart_bytes() -> None:
    actual = apply_delta(new_session("session-1", now=NOW), DELTA, now=NOW)
    different_payload = DELTA.model_copy(
        update={
            "base_chart_payload": STORED_CHART.model_copy(update={"payload": b"other-chart"})
        }
    )

    assert matches_intent(actual, different_payload)


def test_matches_intent_for_reset_delta_distinguishes_empty_and_populated_state() -> None:
    empty = new_session("empty-session", now=NOW)
    populated = _populated_state()

    assert matches_intent(empty, RESET_DELTA)
    assert not matches_intent(populated, RESET_DELTA)
