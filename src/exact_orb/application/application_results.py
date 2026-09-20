"""Immutable application responses and their complete public result union.

Handler outcomes remain in application.results. These models validate response
fields without executing handlers, session persistence or recovery.
"""

from __future__ import annotations

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from exact_orb.application.failure_policy import FailureDescription, describe_failure
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import Issue


def _require_policy_message(message: str, reaction: FailureDescription) -> None:
    if message != reaction.user_message:
        raise ValueError("user_message must match the failure policy")


class ApplicationCommitted(BaseModel):
    """A chart saved in the confirmed state version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["SUCCESS"] = "SUCCESS"
    handler_status: Literal["SUCCESS"] = "SUCCESS"
    context_status: Literal["COMMITTED"] = "COMMITTED"
    code: Literal["OK"] = "OK"
    detail_code: None = None
    user_message: None = None
    retryable: Literal[False] = False

    run_id: UUID
    state_version: int = Field(ge=1, strict=True)
    artifact: ChartArtifact


class ApplicationAlreadyApplied(BaseModel):
    """A chart whose intended state was already observed as applied."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["SUCCESS"] = "SUCCESS"
    handler_status: Literal["SUCCESS"] = "SUCCESS"
    context_status: Literal["ALREADY_APPLIED"] = "ALREADY_APPLIED"
    code: Literal["OK"] = "OK"
    detail_code: None = None
    user_message: None = None
    retryable: Literal[False] = False

    run_id: UUID
    state_version: int = Field(ge=0, strict=True)
    artifact: ChartArtifact


class ApplicationSuperseded(BaseModel):
    """An unapplied result with the state version observed at the conflict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["SUPERSEDED"] = "SUPERSEDED"
    handler_status: Literal["SUCCESS"] = "SUCCESS"
    context_status: Literal["SUPERSEDED"] = "SUPERSEDED"
    code: Literal["RESULT_SUPERSEDED"] = "RESULT_SUPERSEDED"
    detail_code: None = None
    user_message: str
    retryable: Literal[False] = False

    run_id: UUID
    state_version: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def _message_must_match_policy(self) -> Self:
        _require_policy_message(self.user_message, describe_failure(kind="superseded"))
        return self


class ApplicationInputRequired(BaseModel):
    """Actionable input issues associated with the state read by the operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["INPUT_REQUIRED"] = "INPUT_REQUIRED"
    handler_status: Literal["INPUT_REQUIRED"] = "INPUT_REQUIRED"
    context_status: Literal["LOADED"] = "LOADED"
    code: Literal["INPUT_REQUIRED"] = "INPUT_REQUIRED"
    detail_code: None = None
    user_message: str
    retryable: Literal[False] = False

    run_id: UUID
    state_version: int = Field(ge=0, strict=True)
    issues: tuple[Issue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _message_must_match_policy(self) -> Self:
        _require_policy_message(self.user_message, describe_failure(kind="input_required"))
        return self


class ApplicationResolutionFailure(BaseModel):
    """Resolution failed with the retry decision supplied by the handler."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["FAILURE"] = "FAILURE"
    handler_status: Literal["RESOLUTION_UNAVAILABLE"] = "RESOLUTION_UNAVAILABLE"
    context_status: Literal["LOADED"] = "LOADED"
    code: Literal["RESOLUTION_UNAVAILABLE"] = "RESOLUTION_UNAVAILABLE"
    detail_code: str
    user_message: str
    retryable: bool

    run_id: UUID
    state_version: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def _message_must_match_policy(self) -> Self:
        _require_policy_message(self.user_message, describe_failure(
            kind="resolution_unavailable", error_code=self.detail_code,
            retryable=self.retryable,
        ))
        return self


class ApplicationCalculationFailure(BaseModel):
    """Calculation failed with retryability constrained by the failure policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["FAILURE"] = "FAILURE"
    handler_status: Literal["CALCULATION_FAILED"] = "CALCULATION_FAILED"
    context_status: Literal["LOADED"] = "LOADED"
    code: Literal["CALCULATION_FAILED"] = "CALCULATION_FAILED"
    detail_code: str
    user_message: str
    retryable: bool

    run_id: UUID
    state_version: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def _retryability_must_match_policy(self) -> Self:
        reaction = describe_failure(
            kind="calculation_failed", error_code=self.detail_code,
        )
        if self.retryable != reaction.retryable:
            raise ValueError("retryable must match the calculation failure policy")
        _require_policy_message(self.user_message, reaction)
        return self


class ApplicationSessionAbsent(BaseModel):
    """An absent session distinguished by its reason and the reached stage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["SESSION_ABSENT"] = "SESSION_ABSENT"
    handler_status: Literal["NOT_STARTED", "SUCCESS"]
    context_status: Literal["SESSION_ABSENT"] = "SESSION_ABSENT"
    code: Literal["SESSION_EXPIRED", "SESSION_NOT_FOUND", "SESSION_LOST_DURING_OPERATION"]
    detail_code: None = None
    user_message: str
    retryable: Literal[False] = False

    run_id: UUID
    state_version: None = None
    reason: Literal["expired", "not_found"]

    @model_validator(mode="after")
    def _code_must_match_stage_and_reason(self) -> Self:
        allowed = {
            ("NOT_STARTED", "expired", "SESSION_EXPIRED"),
            ("NOT_STARTED", "not_found", "SESSION_NOT_FOUND"),
            ("SUCCESS", "expired", "SESSION_LOST_DURING_OPERATION"),
            ("SUCCESS", "not_found", "SESSION_LOST_DURING_OPERATION"),
        }
        if (self.handler_status, self.reason, self.code) not in allowed:
            raise ValueError("session absence code must match the stage and reason")
        _require_policy_message(self.user_message, describe_failure(
            kind="session_absent", reason=self.reason,
            stage="load" if self.handler_status == "NOT_STARTED" else "commit",
        ))
        return self


class ApplicationStateReadFailure(BaseModel):
    """Persistence did not provide a state snapshot to the operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["FAILURE"] = "FAILURE"
    handler_status: Literal["NOT_STARTED"] = "NOT_STARTED"
    context_status: Literal["READ_FAILED"] = "READ_FAILED"
    code: Literal["STATE_READ_FAILED"] = "STATE_READ_FAILED"
    detail_code: str = Field(min_length=1)
    user_message: str
    retryable: Literal[True] = True

    run_id: UUID
    state_version: None = None

    @model_validator(mode="after")
    def _message_must_match_policy(self) -> Self:
        _require_policy_message(self.user_message, describe_failure(
            kind="state_read_failed", error_code=self.detail_code,
        ))
        return self


class ApplicationStateCommitFailure(BaseModel):
    """State persistence was not confirmed, so no result version is published."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["FAILURE"] = "FAILURE"
    handler_status: Literal["SUCCESS"] = "SUCCESS"
    context_status: Literal["COMMIT_FAILED"] = "COMMIT_FAILED"
    code: Literal["STATE_COMMIT_FAILED"] = "STATE_COMMIT_FAILED"
    detail_code: str = Field(min_length=1)
    user_message: str
    retryable: Literal[True] = True

    run_id: UUID
    state_version: None = None

    @model_validator(mode="after")
    def _message_must_match_policy(self) -> Self:
        _require_policy_message(self.user_message, describe_failure(
            kind="state_commit_failed", error_code=self.detail_code,
        ))
        return self


class ApplicationInternalFailure(BaseModel):
    """An internal failure whose code and observed state match the reached stage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orch_status: Literal["FAILURE"] = "FAILURE"
    handler_status: Literal["NOT_STARTED", "SUCCESS", "UNEXPECTED_FAILURE"]
    context_status: Literal["NOT_ACCESSED", "LOADED", "COMMIT_FAILED"]
    code: Literal["INTERNAL_FAILURE", "HANDLER_NOT_REGISTERED"]
    detail_code: None = None
    user_message: str
    retryable: Literal[False] = False

    run_id: UUID
    state_version: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def _fields_must_match_stage(self) -> Self:
        allowed = {
            ("HANDLER_NOT_REGISTERED", "NOT_STARTED", "NOT_ACCESSED"),
            ("INTERNAL_FAILURE", "NOT_STARTED", "NOT_ACCESSED"),
            ("INTERNAL_FAILURE", "UNEXPECTED_FAILURE", "LOADED"),
            ("INTERNAL_FAILURE", "SUCCESS", "COMMIT_FAILED"),
        }
        if (self.code, self.handler_status, self.context_status) not in allowed:
            raise ValueError("internal failure code and statuses must match the stage")
        if self.context_status == "LOADED":
            if self.state_version is None:
                raise ValueError("loaded internal failure requires state_version")
        elif self.state_version is not None:
            raise ValueError("internal failure without confirmed state requires no version")
        _require_policy_message(self.user_message, describe_failure(
            kind=("handler_not_registered"
                  if self.code == "HANDLER_NOT_REGISTERED" else "internal_failure"),
        ))
        return self


ApplicationResult = (
    ApplicationCommitted
    | ApplicationAlreadyApplied
    | ApplicationInputRequired
    | ApplicationResolutionFailure
    | ApplicationCalculationFailure
    | ApplicationSessionAbsent
    | ApplicationStateReadFailure
    | ApplicationStateCommitFailure
    | ApplicationSuperseded
    | ApplicationInternalFailure
)


__all__ = [
    "ApplicationCommitted",
    "ApplicationAlreadyApplied",
    "ApplicationSuperseded",
    "ApplicationInputRequired",
    "ApplicationResolutionFailure",
    "ApplicationCalculationFailure",
    "ApplicationSessionAbsent",
    "ApplicationStateReadFailure",
    "ApplicationStateCommitFailure",
    "ApplicationInternalFailure",
    "ApplicationResult",
]
