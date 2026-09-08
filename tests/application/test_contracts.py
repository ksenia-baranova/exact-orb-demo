"""Contracts for application commands, ports, and build results."""

from __future__ import annotations

import ast
from datetime import date, time
from inspect import Parameter, iscoroutinefunction, signature
from pathlib import Path
from typing import get_type_hints

import pytest
from pydantic import ValidationError

import exact_orb.application.commands as commands_module
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.ports import (
    BirthDataResolverPort,
    ChartArtifactPort,
    Handler,
)
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.resolver import BirthDataResolver
from exact_orb.birth.types import BirthInput
from exact_orb.calculation.artifacts import ChartArtifactResolver
from exact_orb.calculation.engine import NatalTechniqueAdapter, TechniqueAdapter
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.session.state import RESET_DELTA, StateDelta
from tests.fixtures.calculation import artifact, chart_spec, resolved_birth_data


def _birth_input() -> BirthInput:
    return BirthInput(
        birth_date=date(1990, 9, 2),
        birth_time=time(14, 30),
        place_id="moscow-ru",
    )


def _populated_delta(spec: NatalChartSpec) -> StateDelta:
    return StateDelta(
        birth_input=_birth_input(),
        birth_resolved=resolved_birth_data(),
        base_chart_spec=spec,
    )


def test_build_natal_command_inherits_frozen_config_from_command() -> None:
    birth_input = _birth_input()
    command = BuildNatalCommand(birth_input=birth_input)

    assert command.birth_input == birth_input
    assert BuildNatalCommand.model_config.get("frozen") is True

    source_path = Path(commands_module.__file__ or "")
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    config_owners = [
        node.name
        for node in module.body
        if isinstance(node, ast.ClassDef)
        for statement in node.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "model_config"
            for target in statement.targets
        )
    ]
    assert config_owners == ["Command"]

    with pytest.raises(ValidationError) as exc_info:
        command.birth_input = birth_input  # type: ignore[misc]

    assert exc_info.value.errors()[0]["type"] == "frozen_instance"


def test_build_natal_success_accepts_an_explicit_consistent_pair() -> None:
    spec = chart_spec(chart_kind="natal")
    chart_artifact = artifact(spec=spec)
    delta = _populated_delta(spec)

    result = BuildNatalSuccess(artifact=chart_artifact, delta=delta)

    assert result.artifact == chart_artifact
    assert result.delta == delta


def test_build_natal_success_rejects_reset_delta_as_unpopulated() -> None:
    spec = chart_spec(chart_kind="natal")
    chart_artifact = artifact(spec=spec)

    with pytest.raises(
        ValidationError,
        match="successful build requires a fully populated StateDelta",
    ):
        BuildNatalSuccess(artifact=chart_artifact, delta=RESET_DELTA)


@pytest.mark.parametrize(
    ("artifact_kind", "delta_kind"),
    [
        ("natal", "cosmogram"),
        ("cosmogram", "natal"),
    ],
)
def test_build_natal_success_rejects_explicit_mismatched_specs(
    artifact_kind: str,
    delta_kind: str,
) -> None:
    artifact_spec = chart_spec(chart_kind=artifact_kind)
    delta_spec = chart_spec(chart_kind=delta_kind)
    chart_artifact = artifact(spec=artifact_spec)
    delta = _populated_delta(delta_spec)

    assert artifact_spec != delta_spec
    with pytest.raises(
        ValidationError,
        match=r"artifact\.spec must equal delta\.base_chart_spec",
    ):
        BuildNatalSuccess(artifact=chart_artifact, delta=delta)


def test_application_ports_are_not_runtime_checkable() -> None:
    assert isinstance(NatalTechniqueAdapter(), TechniqueAdapter)

    for port in (Handler, BirthDataResolverPort, ChartArtifactPort):
        with pytest.raises(TypeError):
            isinstance(object(), port)


@pytest.mark.parametrize(
    ("implementation_method", "port_method", "parameter_names", "run_default"),
    [
        (
            BirthDataResolver.resolve,
            BirthDataResolverPort.resolve,
            ("self", "birth_input", "run"),
            None,
        ),
        (
            ChartArtifactResolver.ensure_chart,
            ChartArtifactPort.ensure_chart,
            ("self", "spec", "resolved", "run"),
            Parameter.empty,
        ),
    ],
)
def test_implemented_dependencies_match_port_signatures(
    implementation_method: object,
    port_method: object,
    parameter_names: tuple[str, ...],
    run_default: object,
) -> None:
    implementation_parameters = signature(implementation_method).parameters
    port_parameters = signature(port_method).parameters

    assert iscoroutinefunction(implementation_method)
    assert iscoroutinefunction(port_method)
    assert tuple(implementation_parameters) == parameter_names
    assert tuple(port_parameters) == parameter_names

    for name, implementation_parameter in implementation_parameters.items():
        port_parameter = port_parameters[name]
        assert implementation_parameter.kind is port_parameter.kind
        assert implementation_parameter.default == port_parameter.default

    assert implementation_parameters["run"].kind is Parameter.KEYWORD_ONLY
    assert implementation_parameters["run"].default is run_default
    assert port_parameters["run"].default is run_default
    assert get_type_hints(implementation_method) == get_type_hints(port_method)
