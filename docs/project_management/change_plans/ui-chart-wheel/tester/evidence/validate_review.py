"""Validate TASK-T-002 documents; never execute product tests or mutate Manager."""

import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
CHANGE = ROOT / "docs/project_management/change_plans/ui-chart-wheel"
PREFIX = CHANGE.relative_to(ROOT).as_posix() + "/"
INPUT = "543b7ec726ee96c951dc0abbf1067ca6ad47a1ba"
MAIN = "535551026af6eedaf2a0aa5c0daa96fa94655ec1"
PUBLISHED_MAIN = "bba8d6cfb22f586f86c3035423f2535ede158b9f"
ANALYST = "2634b224894b1046113557bfe241f0a5f2d46f8c"
DEVELOPER = "04be207627de1049deac2e069574e01b62536607"
OWN_PATHS = {PREFIX + name for name in (
    "tester_artifact.md", "tester/testability_review.md", "tester/test_plan.md",
    "tester/coverage_matrix.md", "tester/defects.md", "tester/decision_input.patch",
    "tester/evidence/review.json", "tester/evidence/validate_review.py",
    "tester/evidence/validation.txt",
)}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def source(path, sha=INPUT):
    return git("show", f"{sha}:{path}").replace(b"\r\n", b"\n")


head = git("rev-parse", "HEAD").decode().strip()
subprocess.run(["git", "merge-base", "--is-ancestor", INPUT, head], cwd=ROOT, check=True)
assert git("branch", "--show-current").decode().strip() == "test/ui-chart-wheel"
assert set(git("diff", "--name-only", INPUT, head).decode().splitlines()) <= OWN_PATHS
resolver = git("log", "--reverse", "--format=%H", "-G",
               "^### 2[.]6[.] Общий вход повторных консультаций", INPUT, "--",
               PREFIX + "manager_artifact.md").decode().splitlines()[0]
assert resolver == INPUT
assert git("rev-parse", MAIN + "^{tree}").strip() == git("rev-parse", PUBLISHED_MAIN + "^{tree}").strip()
assert not git("diff", "--name-only", MAIN, INPUT, "--",
               "src", "tests", "docs/requirements", "docs/development_approach").strip()
changed = git("diff", "--name-only", MAIN, INPUT).decode().splitlines()
paths = sorted({p for p in changed if p not in OWN_PATHS} | {
    "AGENTS.md", "docs/requirements/current/ui/birth-form-and-facts.md",
    "docs/requirements/current/ui/scenarios.md", "docs/requirements/http_api.md",
    "docs/project_management/technical_debt.md",
    "src/exact_orb/http_api/ui/main.mjs", "src/exact_orb/http_api/ui/facts.mjs",
    "src/exact_orb/http_api/ui/session.mjs", "src/exact_orb/http_api/ui/response.mjs",
    "tests/ui/facts.test.mjs", "tests/ui/session.test.mjs", "tests/ui/recovery.test.mjs",
})
hashes = {}
for path in paths:
    original = source(path)
    assert (ROOT / path).read_bytes().replace(b"\r\n", b"\n") == original, path
    hashes[path] = hashlib.sha256(original).hexdigest()

manifest_counts = {}
for role, sha in (("analyst", ANALYST), ("developer", DEVELOPER)):
    manifest = json.loads(source(PREFIX + role + "/package_manifest.json"))
    entries = manifest["files"]
    if isinstance(entries, dict):
        entries = [{"path": PREFIX + k, "sha256": v} for k, v in entries.items()]
    for entry in entries:
        original = source(entry["path"], sha)
        assert hashlib.sha256(original).hexdigest() == entry["sha256"], entry["path"]
        assert original == source(entry["path"]), entry["path"]
    manifest_counts[role] = len(entries)

recommendations = {
    "010": "V3 и локальный SVG fallback сверены. Нужен replacement/failure seam: реальные page/coordinator/renderer, HTML и summary нового принятого DTO доступны при leaf fault SVG, затем успешная замена на тех же фактах. HTTP/session/calculation не меняются. AS-WHEEL-24, T-WHEEL-11; technical port еще OPEN.",
    "011": "TEST-FIND-WHEEL-002 OPEN только по измерительным условиям. Разреженный контроль, конфликтующая группа и далекая точка, пять R через 0 градусов, F3-max 16 IDs/несколько conjunction на 360 px. Developer формализует bbox/collision/minimality/bounds; Owner принимает наблюдаемый предел/fallback по evidence. Zero shift/leader без конфликта, true anchors / циклический порядок. T-WHEEL-05.",
    "012": "Подпись категории и контур только выбранного символа conjunction уже определены. Нужны семь type x три category, сохранение рисунка/цвета выбранной линии, selected-only pair, background без линии/маркера, grayscale/keyboard/text/legend. Открыты palette/layout/измеренное размещение/интервалы, не продуктовая семантика. T-WHEEL-04/12, TEST-FIND-WHEEL-002.",
    "013": "TEST-FIND-WHEEL-001/003 CLOSED по документальной сверке v3 с зарегистрированным Owner evidence. AS-WHEEL-28/29: point/aspect exclusivity, unrelated pair, repeat aspect clear с прежним раскрытием без фильтра планеты. AS-WHEEL-30: новый DTO, preserve существующего / clear только исчезнувшего выбора без сброса раскрытия; dirty draft не скрывается. F5 и accepted explicit build по измененным birth data reset отдельно; resize preserve. T-WHEEL-06/07/08/09/12; runtime NOT RUN. Нужны technical mobile targets/keyboard order/recovery layout.",
    "014": "Принятые anchor ASC для natal, 0 Aries для cosmogram и CCW перенесены в v3. Независимые относительные 0/90/180/270 градусов: left/bottom/right/top; seam 359.99/0/0.01, истинные anchors/endpoints. Не выводить expected из prototype ref=100 или production helper. Drawing ADR и geometry execution еще впереди. T-WHEEL-02.",
}
manager_rel = PREFIX + "manager_artifact.md"
manager = source(manager_rel).decode("utf-8")
proposed, found = [], set()
signature = "Tester / Codex, 2026-10-16, TASK-T-002:"
assert signature not in manager
for line in manager.splitlines(keepends=True):
    match = re.match(r"^\| \x60DP-O-(01[0-4])\x60 \|", line)
    if match:
        key = match.group(1)
        cells = line.rstrip("\n").split("|")
        assert len(cells) == 12
        cells[8] = cells[8].rstrip() + "<br>" + signature + " " + recommendations[key] + " Условное testability, не решение Owner / допуск реализации. "
        line = "|".join(cells) + "\n"
        found.add(key)
    proposed.append(line)
assert found == set(recommendations)
patch = "".join(difflib.unified_diff(manager.splitlines(keepends=True), proposed,
                 fromfile="a/" + manager_rel, tofile="b/" + manager_rel, n=0))
assert all(line == line.rstrip(" \t") for line in patch.splitlines())
(CHANGE / "tester/decision_input.patch").write_text(patch, encoding="utf-8", newline="\n")

docs = [CHANGE / "tester_artifact.md", *sorted((CHANGE / "tester").glob("*.md"))]
assert len(docs) == 5
links = tables = 0
for path in docs:
    body = path.read_text(encoding="utf-8")
    assert "\ufffd" not in body and body.endswith("\n"), path
    assert all(line == line.rstrip(" \t") for line in body.splitlines()), path
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", body):
        if re.match(r"[a-z]+://", target):
            continue
        file_part, _, anchor = unquote(target).partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        assert dest.exists(), (path.name, target)
        if anchor:
            text = dest.read_text(encoding="utf-8")
            anchors = set(re.findall(r'<a id="([^"]+)"', text))
            anchors.update(re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-")
                           for h in re.findall(r"^#{1,6}\s+(.+)$", text, re.M))
            assert anchor in anchors, (path.name, target)
        links += 1
    width = None
    for line in body.splitlines() + [""]:
        if line.startswith("|"):
            count = len(line.split("|"))
            tables += int(width is None)
            width = count if width is None else width
            assert count == width, (path.name, line)
        else:
            width = None

matrix = (CHANGE / "tester/coverage_matrix.md").read_text(encoding="utf-8")
rows = [line for line in matrix.splitlines() if re.match(r"\| (?:\[)?REQ-(?:WHEEL|UI)-\d{2}", line)]
assert len(rows) == 22
assert {re.search(r"REQ-(?:WHEEL|UI)-\d{2}", row)[0] for row in rows} == {
    f"REQ-{group}-{i:02}" for group in ("WHEEL", "UI") for i in range(1, 12)}
assert sum("| PARTIAL |" in row for row in rows) == 16
assert sum("| MISSING |" in row for row in rows) == 6
assert all("| NOT RUN |" in row for row in rows)
scope = "\n".join(rows)
assert set(re.findall(r"AS-WHEEL-\d{2}", scope)) == {f"AS-WHEEL-{i:02}" for i in range(1, 31)}
assert set(re.findall(r"AS-UI-\d{2}", scope)) == {f"AS-UI-{i:02}" for i in range(1, 24)}
plan = (CHANGE / "tester/test_plan.md").read_text(encoding="utf-8")
assert set(re.findall(r'<a id="t-wheel-(\d{2})"', plan)) == {f"{i:02}" for i in range(1, 15)}
assert all(name in plan for name in ("001-chart-presentation.puml", "002-wheel-table-selection.puml",
                                    "003-edit-and-recovery.puml"))
defects = (CHANGE / "tester/defects.md").read_text(encoding="utf-8")
states = {}
for number, state in (("001", "CLOSED"), ("002", "OPEN"), ("003", "CLOSED")):
    section = defects.split(f'<a id="test-find-wheel-{number}"></a>')[1].split('<a id="test-find-wheel-')[0]
    assert re.search(r"\*\*Статус:\*\* (\w+)", section)[1] == state
    assert "**Обоснование статуса:**" in section
    states["TEST-FIND-WHEEL-" + number] = state

fixtures = {}
for relative in ("tests/http_api/golden/chart_dto.json", "tests/ui/fixtures/natal_1985_chart_dto.json"):
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    charts = value if "natal" in value else {"full_natal": value}
    fixtures[relative] = {name: {
        "points": len(chart["points"]), "aspects": len(chart["aspects"]),
        "houses": None if chart["houses"] is None else len(chart["houses"]),
    } for name, chart in charts.items()}
golden = json.loads((ROOT / "tests/http_api/golden/chart_dto.json").read_text(encoding="utf-8"))
assert any(a["from"] == "moon" and a["to"] == "asc" for a in golden["natal"]["aspects"])
assert golden["cosmogram"]["angles"] is None
assert not any("asc" in (a["from"], a["to"]) for a in golden["cosmogram"]["aspects"])
stats = {
    "markdown_files": len(docs), "local_links": links, "tables": tables, "requirements": 22,
    "partial": 16, "missing": 6, "as_wheel": 30, "as_ui": 23, "as_ui_modify": "AS-UI-22",
    "planned_t_wheel": 14, "sequences_mapped": 3, "dp_proposals": sorted(found),
    "source_files_unchanged": len(hashes), "manifest_payloads": manifest_counts, "finding_states": states,
}
result = {
    "author": "Codex / Tester", "date": "2026-10-16", "version": "consultation-v2-pre-publication",
    "task_id": "TASK-T-002", "manager_registration": "assignment registered; new result pending",
    "review_sha": INPUT, "main_baseline": MAIN, "published_main_snapshot": PUBLISHED_MAIN,
    "published_main_tree_matches_baseline": True, "analyst_package_sha": ANALYST,
    "developer_package_sha": DEVELOPER, "new_developer_consultation": None,
    "candidate_sha": None, "tested_sha": None, "accepted_sha": None,
    "worktree": str(ROOT), "branch": "test/ui-chart-wheel",
    "source_hash_basis": "canonical LF Git input bytes", "source_git_sha256": hashes,
    "main_to_input_changed_paths": changed, "static_checks": stats, "fixture_inventory_only": fixtures,
    "testability": "TESTABLE WITH CLARIFICATIONS",
    "estimate_independent_testing_days": [3, 5], "estimate_consultation_days": [0.5, 0.75],
    "estimate_confidence": "medium",
    "not_run": ["pytest", "node --test", "browser acceptance", "HTTPS smoke", "PlantUML rendering",
                "density spike", "renderer replacement", "post-acceptance transfer verification"],
    "limitations": [
        "Document review only; CLOSED requirement gaps do not mean runtime PASS",
        "Remaining numerical/layout/replacement/mobile criteria are in existing DP-O-010..013",
        "Reviewers have not accepted this local result; Manager lifecycle and approvals unchanged",
        "Previous evidence is preserved in Git at 9dd8b96; it is not a run on this InputSHA",
        "Pre-publication validation snapshot; subsequent authorized commit/push is recorded in tester_artifact.md; PR not requested",
    ],
}
(CHANGE / "tester/evidence/review.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("TESTER_REVIEW_V2_OK " + json.dumps(stats, ensure_ascii=False))
