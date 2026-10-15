"""Static validation of the Tester consultation; never executes product tests."""

import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
CHANGE = ROOT / "docs/project_management/change_plans/ui-chart-wheel"
INPUT = "2b846077b317e33dd892565419942c4db8517b1e"
MAIN = "535551026af6eedaf2a0aa5c0daa96fa94655ec1"
ANALYST = "683bdd0c1f5a0e65735f4e48127d408300ec697c"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def source(path, sha=INPUT):
    return git("show", f"{sha}:{path}")


def norm(data):
    return data.replace(b"\r\n", b"\n")


assert git("rev-parse", "HEAD").decode().strip() == INPUT
assert git("branch", "--show-current").decode().strip() == "test/ui-chart-wheel"
assert git("rev-parse", "origin/change/ui-chart-wheel").decode().strip() == INPUT
assert git("rev-parse", "origin/main").decode().strip() == MAIN
changed = git("diff", "--name-only", MAIN, INPUT).decode().splitlines()
assert len(changed) == 12 and all(p.startswith("docs/project_management/change_plans/ui-chart-wheel/") for p in changed)

# Record immutable sources and verify that role-owned input files are untouched.
paths = changed + [
    "docs/requirements/current/ui/birth-form-and-facts.md",
    "docs/requirements/current/ui/scenarios.md",
    "docs/requirements/http_api.md",
    "docs/project_management/technical_debt.md",
    "src/exact_orb/http_api/ui/main.mjs",
    "src/exact_orb/http_api/ui/facts.mjs",
    "src/exact_orb/http_api/ui/session.mjs",
    "src/exact_orb/http_api/ui/response.mjs",
    "tests/ui/facts.test.mjs",
    "tests/ui/session.test.mjs",
    "tests/ui/recovery.test.mjs",
]
hashes = {}
for path in paths:
    original = source(path)
    assert norm((ROOT / path).read_bytes()) == norm(original), path
    hashes[path] = hashlib.sha256(original).hexdigest()

manifest_path = "docs/project_management/change_plans/ui-chart-wheel/analyst/package_manifest.json"
manifest = json.loads(source(manifest_path, ANALYST))
for entry in manifest["files"]:
    assert hashlib.sha256(source(entry["path"], ANALYST)).hexdigest() == entry["sha256"], entry["path"]
    assert source(entry["path"], ANALYST) == source(entry["path"]), entry["path"]

# A proposal for the one canonical registry; do not mutate Manager-owned content.
recommendations = {
    "010": "Replacement/error control: реальная страница и coordinator, принятый F1 / identity; успешный render, leaf fault колеса с доступными HTML / сводкой и сообщением, затем успешная замена на тех же фактах. Нужен наблюдаемый seam без смены HTTP/session/calculation; выбранный Owner локальный fallback не пересматривается. AS-WHEEL-24; T-WHEEL-11.",
    "011": "Данные для oracle: разрежённый контроль, конфликтующая группа + далёкая точка, пять R через 0 градусов и 16 IDs / несколько conjunction на 360 px. Проверить zero shift/leader без конфликта, только конфликтующие элементы, true anchors и циклический порядок. Developer формализует collision/minimality/bounds; Owner подтверждает наблюдаемый предел/fallback. TEST-FIND-WHEEL-002; T-WHEEL-05.",
    "012": "Проверить семь type x три category, exact/working одного type и одинаково округлённого orb: категория берётся из DTO. Выбор сохраняет штрих/цвет, меняет толщину; grayscale/keyboard/text/legend и адресация нескольких conjunction. Для category/selection у маркера conjunction нужен окончательный oracle. TEST-FIND-WHEEL-002; T-WHEEL-04/12.",
    "013": "Нужны 0/1/4/5/6/46 аспектов и 0/1/5/6 аспектов выбранной планеты, независимые кнопки домов/аспектов, filter/reset/resize и отсутствие scroll/focus transfer. Контрпример: Луна выбрана, на колесе активирован Солнце->MC вне отбора; какой переход делает строку видимой? Отдельно определить доступное снятие aspect-only без отклонённой кнопки. TEST-FIND-WHEEL-003; T-WHEEL-06/07/08/09/12. Актуализировать Analyst v1 по Owner decisions; TEST-FIND-WHEEL-001.",
    "014": "Выбор Owner уже ACCEPTED; не открывать вопрос повторно. Независимый oracle: anchor ASC для natal / 0 Aries для cosmogram; относительные 0/90/180/270 градусов дают left/bottom/right/top при CCW, плюс контроль стыка 359.99/0/0.01. Не использовать prototype ref=100 или production helper для expected. Актуализировать AS-WHEEL-25 / sequences. T-WHEEL-02; TEST-FIND-WHEEL-001.",
}
manager_rel = "docs/project_management/change_plans/ui-chart-wheel/manager_artifact.md"
manager = source(manager_rel).decode("utf-8")
proposed = []
found = set()
for line in manager.splitlines(keepends=True):
    match = re.match(r"^\| `DP-O-(01[0-4])` \|", line)
    if match:
        key = match.group(1)
        cells = line.rstrip("\r\n").split("|")
        assert len(cells) == 12, (key, len(cells))
        cells[8] = cells[8].rstrip() + "<br>Tester / Codex, 2026-10-15, TASK-T-001 (ID предложен, регистрация ожидается): " + recommendations[key] + " Рекомендация, не решение Owner / approval. "
        line = "|".join(cells) + "\n"
        found.add(key)
    proposed.append(line)
assert found == set(recommendations)
# Zero context avoids whitespace-only context lines inside this tracked patch.
# Apply/check with --unidiff-zero against the pinned Manager baseline.
patch = "".join(difflib.unified_diff(manager.splitlines(keepends=True), proposed, fromfile="a/" + manager_rel, tofile="b/" + manager_rel, n=0))
(CHANGE / "tester/decision_input.patch").write_text(patch, encoding="utf-8", newline="\n")

docs = [CHANGE / "tester_artifact.md", *sorted((CHANGE / "tester").glob("*.md"))]
assert len(docs) == 5
links = tables = 0
for path in docs:
    body = path.read_text(encoding="utf-8")
    assert "\ufffd" not in body
    assert body.endswith("\n"), path
    assert all(line == line.rstrip(" \t") for line in body.splitlines()), path
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", body):
        if re.match(r"[a-z]+://", target):
            continue
        file_part, _, anchor = unquote(target).partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        if dest == CHANGE / "tester/evidence/review.json" and not dest.exists():
            links += 1
            continue  # Generated below after the other checks succeed.
        assert dest.is_file(), (path.name, target)
        if anchor:
            text = dest.read_text(encoding="utf-8")
            anchors = set(re.findall(r'<a id="([^"]+)"', text))
            for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.M):
                anchors.add(re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-"))
            assert anchor in anchors, (path.name, target)
        links += 1
    width = None
    for line in body.splitlines() + [""]:
        if line.startswith("|"):
            count = len(line.split("|"))
            if width is None:
                width = count
                tables += 1
            assert count == width, (path.name, line)
        else:
            width = None

matrix = (CHANGE / "tester/coverage_matrix.md").read_text(encoding="utf-8")
rows = [line for line in matrix.splitlines() if line.startswith("| ") and re.match(r"\| (?:\[)?REQ-(?:WHEEL|UI)-\d{2}", line)]
expected = {f"REQ-{group}-{i:02}" for group in ("WHEEL", "UI") for i in range(1, 12)}
assert len(rows) == 22
assert {re.search(r"REQ-(?:WHEEL|UI)-\d{2}", row)[0] for row in rows} == expected
assert sum("| PARTIAL |" in row for row in rows) == 16
assert sum("| MISSING |" in row for row in rows) == 6
assert all("| NOT RUN |" in row for row in rows)
scope = "\n".join(rows)
assert set(re.findall(r"AS-WHEEL-\d{2}", scope)) == {f"AS-WHEEL-{i:02}" for i in range(1, 26)}
assert set(re.findall(r"AS-UI-\d{2}", scope)) == {f"AS-UI-{i:02}" for i in range(1, 24)}
plan = (CHANGE / "tester/test_plan.md").read_text(encoding="utf-8")
assert set(re.findall(r'<a id="t-wheel-(\d{2})"', plan)) == {f"{i:02}" for i in range(1, 15)}

fixtures = {}
for relative in ("tests/http_api/golden/chart_dto.json", "tests/ui/fixtures/natal_1985_chart_dto.json"):
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    charts = value if "natal" in value else {"full_natal": value}
    fixtures[relative] = {name: {"points": len(chart["points"]), "aspects": len(chart["aspects"]), "houses": None if chart["houses"] is None else len(chart["houses"])} for name, chart in charts.items()}

result = {
    "author": "Codex / Tester", "date": "2026-10-15", "version": "v1-local-consultation",
    "proposed_task_id": "TASK-T-001", "manager_registration": "pending", "review_sha": INPUT,
    "main_baseline": MAIN, "analyst_package_sha": ANALYST, "candidate_sha": None, "tested_sha": None,
    "worktree": str(ROOT), "branch": "test/ui-chart-wheel", "source_git_sha256": hashes,
    "analyst_manifest_verified": len(manifest["files"]), "main_to_input_changed_paths": changed,
    "static_checks": {"markdown_files": len(docs), "local_links": links, "tables": tables, "requirements": 22, "partial": 16, "missing": 6, "as_wheel": 25, "as_ui": 23, "planned_t_wheel": 14, "dp_proposals": sorted(found), "source_files_unchanged": len(hashes)},
    "fixture_inventory_only": fixtures,
    "not_run": ["pytest", "node --test", "browser acceptance", "HTTPS smoke", "PlantUML rendering", "renderer replacement", "post-acceptance transfer verification"],
    "limitations": ["Static document/assertion review only; fixture inventory is not a renderer test", "Analyst v1 not approved or synchronized with current Owner decisions", "No product PASS/FAIL/readiness or Manager lifecycle transition", "Pre-publication validation snapshot; subsequent Git publication is recorded in tester_artifact.md; Manager approval and registration remain separate"],
}
(CHANGE / "tester/evidence/review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("TESTER_REVIEW_OK " + json.dumps(result["static_checks"], ensure_ascii=False))
