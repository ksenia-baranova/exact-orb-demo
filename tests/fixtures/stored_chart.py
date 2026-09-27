"""Test-only construction of a stored envelope for a chart artifact."""

from __future__ import annotations

from exact_orb.calculation.codec import CHART_ARTIFACT_PAYLOAD_FORMAT, encode_chart_artifact
from exact_orb.calculation.types import ChartArtifact
from exact_orb.session.state import StoredChart


def stored_chart_for(artifact: ChartArtifact) -> StoredChart:
    return StoredChart(
        payload_format=CHART_ARTIFACT_PAYLOAD_FORMAT,
        calculation_key=artifact.calculation_key,
        calculation_version=artifact.calculation_version,
        payload=encode_chart_artifact(artifact),
    )


__all__ = ["stored_chart_for"]
