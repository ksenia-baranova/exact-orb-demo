"""Typed errors exposed by the Research contract layer."""

from __future__ import annotations


RESEARCH_PROJECTION_UNSUPPORTED_VALUE = "RESEARCH_PROJECTION_UNSUPPORTED_VALUE"
RESEARCH_WRITE_FAILED = "RESEARCH_WRITE_FAILED"


class _ResearchError(Exception):
    error_code: str

    def __init__(self, error_code: str) -> None:
        if not isinstance(error_code, str) or not error_code:
            raise ValueError("error_code must be a non-empty string")
        self.error_code = error_code
        super().__init__(error_code)


class ResearchProjectionError(_ResearchError):
    """A chart artifact cannot be projected into the closed Research schema."""


class ResearchPersistenceError(_ResearchError):
    """Base class for infrastructure failures in Research persistence."""


class ResearchWriteError(ResearchPersistenceError):
    """A Research write could not be completed by its backend."""


__all__ = [
    "RESEARCH_PROJECTION_UNSUPPORTED_VALUE",
    "RESEARCH_WRITE_FAILED",
    "ResearchPersistenceError",
    "ResearchProjectionError",
    "ResearchWriteError",
]
