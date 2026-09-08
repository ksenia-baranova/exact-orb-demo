"""Recording stubs shared by application-handler tests."""

from __future__ import annotations

from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.spec import ChartSpec
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext
from tests.fixtures.calculation import artifact


BirthResolution = ResolvedBirthData | InputRequired | ResolutionUnavailable


class StubBirthDataResolver:
    """Return or raise a configured value while recording the port call."""

    def __init__(self, result: BirthResolution | BaseException) -> None:
        self.result = result
        self.calls = 0
        self.received_birth_input: BirthInput | None = None
        self.received_run: RunContext | None = None

    async def resolve(
        self,
        birth_input: BirthInput,
        *,
        run: RunContext | None = None,
    ) -> BirthResolution:
        self.calls += 1
        self.received_birth_input = birth_input
        self.received_run = run
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class StubChartArtifactPort:
    """Build, return, or raise a configured value and record the port call."""

    def __init__(
        self,
        result: ChartArtifact | BaseException | None = None,
    ) -> None:
        self.result = result
        self.calls = 0
        self.received_spec: ChartSpec | None = None
        self.received_resolved: ResolvedBirthData | None = None
        self.received_run: RunContext | None = None

    async def ensure_chart(
        self,
        spec: ChartSpec,
        resolved: ResolvedBirthData,
        *,
        run: RunContext,
    ) -> ChartArtifact:
        self.calls += 1
        self.received_spec = spec
        self.received_resolved = resolved
        self.received_run = run
        if isinstance(self.result, BaseException):
            raise self.result
        if self.result is not None:
            return self.result
        return artifact(spec=spec, resolved=resolved)


__all__ = ["BirthResolution", "StubBirthDataResolver", "StubChartArtifactPort"]
