"""TASK-T-02: execute independent JS checks against the real UI composition."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.no_ephemeris_autoinit
@pytest.mark.parametrize("scenario", [
    pytest.param("roundtrips", marks=pytest.mark.req("REQ-TERMS-01", "REQ-TERMS-02", "REQ-TERMS-03", "REQ-TERMS-04", "REQ-TERMS-05")),
    pytest.param("isolation", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-05")),
    pytest.param("gates", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-07")),
    pytest.param("payload", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-02", "REQ-TERMS-05", "REQ-TERMS-07")),
    pytest.param("current", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-04", "REQ-TERMS-05")),
    pytest.param("recovery", marks=pytest.mark.req("REQ-UI-03")),
    pytest.param("issues", marks=pytest.mark.req("REQ-UI-03")),
])
def test_terms_composition(scenario):
    # Given записаны оракулы и примеры в T-02…18/T-29 до чтения реализации
    node = shutil.which("node")
    assert node, "Node is required; missing runtime is not PASS"
    # When выполняются независимые проверки публичного mount/form/session/transport
    result = subprocess.run([node, "tests/acceptance/terms_acceptance.mjs", scenario],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=90)
    # Then каждая строка примеров соответствует источнику ожидаемого в плане
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status":"PASS"' in result.stdout
    print(result.stdout.strip())


@pytest.mark.no_ephemeris_autoinit
@pytest.mark.parametrize("scenario", [
    pytest.param("presentation", marks=pytest.mark.req("REQ-TERMS-01", "REQ-TERMS-06")),
    pytest.param("keyboard", marks=pytest.mark.req("REQ-TERMS-01", "REQ-TERMS-02", "REQ-TERMS-03", "REQ-TERMS-08")),
    pytest.param("targets", marks=pytest.mark.req("REQ-TERMS-08")),
    pytest.param("reload", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-02", "REQ-TERMS-07")),
    pytest.param("builds", marks=pytest.mark.req("REQ-UI-03", "REQ-TERMS-01", "REQ-TERMS-02", "REQ-TERMS-04", "REQ-TERMS-05")),
])
def test_terms_browser(scenario, tmp_path):
    # Given настоящий Chrome, production assets и только управляемая листовая HTTP-сеть
    node = shutil.which("node")
    assert node, "Node is required"
    environment = os.environ.copy()
    # Use an existing runtime installation; no dependency installation or network.
    bundled = Path(node).parent.parent / "node_modules"
    if bundled.is_dir():
        environment["NODE_PATH"] = str(bundled)
    output = Path(environment.get("TERMS_EVIDENCE_DIR", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    # When пользователь выполняет сценарий T-01/T-19…28 доверенным вводом
    result = subprocess.run([node, "tests/acceptance/terms_browser.cjs", scenario, str(output)],
                            cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=150)
    # Then сравниваются текст, focus, overflow, реальные hit recipients и новая загрузка
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status":"PASS"' in result.stdout
    print(result.stdout.strip())
