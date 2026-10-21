"""Reproduce documentary checks; never alter Tester evidence or Git refs/index.

--write exports Manager checks, a registry-only patch and an integration plan.
The output is an author check, not an independent Tester verdict.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
CHANGE = HERE.parent
INPUT = "72ab4e30321884ddabe4205505216a7595d8bfeb"
TESTER = "583d635559862edc25e271f68053038c38fe088d"
TRANSFER = "c7219e485917366f67159c9a08e3c78dc4e69372"
RUNTIME = "99741958b4bbee8884505920f4a02f2f19dea3e3"
MAIN = "bba8d6cfb22f586f86c3035423f2535ede158b9f"
ORIGINAL_MAIN = "535551026af6eedaf2a0aa5c0daa96fa94655ec1"
DEBT = "docs/project_management/technical_debt.md"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(data):
    return data.replace(b"\r\n", b"\n")


def digest(data):
    return hashlib.sha256(normalized(data)).hexdigest()


def tree(ref):
    result = {}
    for item in git("ls-tree", "-rz", ref).split(b"\0"):
        if item:
            meta, path = item.split(b"\t", 1)
            result[path.decode("utf-8")] = meta.split()[2].decode()
    return result


def anchors(path):
    source = path.read_text(encoding="utf-8")
    result = set(re.findall(r'<a\s+id="([^"]+)"', source))
    for heading in re.findall(r"^#{1,6}\s+(.+)$", source, re.M):
        heading = re.sub(r"[^\w\- ]", "", heading.replace("`", "").lower())
        result.add(heading.replace(" ", "-"))
    return result


def run(write=False):
    head = git("rev-parse", "HEAD").decode().strip()
    assert git("merge-base", "--is-ancestor", INPUT, head) == b"", "Unrelated checkout"
    assert git("merge-base", "--is-ancestor", INPUT, "origin/change/ui-chart-wheel") == b""
    assert git("rev-parse", "origin/main").decode().strip() == MAIN, "Refresh the main assessment"
    assert git("rev-parse", MAIN + "^{tree}") == git("rev-parse", ORIGINAL_MAIN + "^{tree}")
    assert git("merge-base", "--is-ancestor", TESTER, INPUT) == b""
    scenarios = text("docs/requirements/current/ui/scenarios.md")
    as09 = scenarios.split('### AS-WHEEL-09.', 1)[1].split('### AS-WHEEL-10.', 1)[0]
    assert "набор F3" in as09 and "sparse" in as09 and "F2 проверяет" in as09
    assert "DEBT-UI-004" in as09 and "внутреннем ряду" in as09
    old_as = git("show", TRANSFER + ":docs/requirements/current/ui/scenarios.md").decode()
    assert "Исходный seam/R набор F2" in old_as, "Negative control no longer represents the reviewed bug"
    as28 = scenarios.split('### AS-WHEEL-28.', 1)[1].split('### AS-WHEEL-29.', 1)[0]
    assert all(s in as28 for s in ("F5", "U/R/D/V/M/L/T/P", "#as-wheel-23", "#as-wheel-30"))
    manager = (CHANGE / "manager_artifact.md").read_text(encoding="utf-8")
    assert "[behavioral sequences](../../../sequence_diagrams/ui/README.md)" in manager
    assert "[behavioral sequences](analyst/sequence_diagrams/ui/)" not in manager
    assert len(re.findall(r'^### AS-(?:UI|WHEEL)-\d+\.', scenarios, re.M)) == 53
    reqs = "\n".join(text("docs/requirements/current/ui/" + name) for name in ("birth-form-and-facts.md", "chart-wheel.md"))
    assert len(set(re.findall(r'^### (REQ-(?:UI|WHEEL)-\d+)\.', reqs, re.M))) == 22
    manifest = json.loads((HERE / "transfer_manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["targets"]:
        assert digest((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
    source_paths = {entry["source"] for entry in manifest["moves"]}
    tracked = set(git("ls-files", "-z").decode().split("\0")) - {""}
    new = set(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""}
    candidate = {path for path in tracked | new if (ROOT / path).is_file()}
    if write:
        # These deterministic exports are produced below and verified on the next run.
        candidate.update((HERE / name).relative_to(ROOT).as_posix() for name in
                         ("main_integration_plan.md", "registry-publication.patch", "session_closure_checks.json"))
    assert len(source_paths) == 13 and not (source_paths & candidate)
    assert not any(path.startswith("docs/project_management/change_plans/ui-chart-wheel/analyst/sequence_diagrams/ui/") for path in candidate)
    for entry in manifest["moves"]:
        assert digest(git("show", manifest["source_sha"] + ":" + entry["source"])) == entry["source_git_sha256_lf"]
    for path in manifest["historical_reports_preserved"]:
        assert digest((ROOT / path).read_bytes()) == digest(git("show", INPUT + ":" + path)), path
    assert not git("diff", "--name-only", RUNTIME, "HEAD", "--", "src", "tests").strip()
    assert not git("diff", "--name-only", "HEAD", "--", "src", "tests").strip()
    assert not any(path.startswith(("src/", "tests/")) for path in new)
    runtime_files = git("ls-tree", "-r", "--name-only", RUNTIME, "src/exact_orb/http_api/ui").decode().splitlines()
    for path in runtime_files:
        assert digest((ROOT / path).read_bytes()) == digest(git("show", RUNTIME + ":" + path)), path
    changed = (set(git("diff", "--name-only", INPUT, "HEAD").decode().splitlines())
               | set(git("diff", "--name-only", "HEAD").decode().splitlines()) | new)
    assert all(path.startswith("docs/") or path == "README.md" for path in changed)
    # Resolve links against files in the would-be Git candidate, not empty local dirs.
    def exists(relative):
        return relative in candidate or any(p.startswith(relative.rstrip("/") + "/") for p in candidate)
    retired = "docs/project_management/change_plans/ui-chart-wheel/analyst/sequence_diagrams/ui"
    assert not exists(retired), "Negative directory control unexpectedly exists"
    errors, count = [], 0
    for relative in sorted(path for path in changed if path.endswith(".md")):
        path = ROOT / relative
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding="utf-8")):
            if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", link):
                continue
            count += 1
            base, _, anchor = unquote(link.strip("<>")).partition("#")
            target = (path.parent / base).resolve() if base else path
            target_rel = target.relative_to(ROOT).as_posix()
            if not exists(target_rel):
                errors.append([relative, link, "not in candidate Git files"])
            elif anchor and target.suffix == ".md" and anchor not in anchors(target):
                errors.append([relative, link, "anchor missing"])
    known = {(e[0], e[1]) for e in manifest["validation"]["preexisting_link_errors"]}
    inherited = [e for e in errors if (e[0], e[1]) in known]
    for relative, link, _ in inherited:
        assert link in git("show", INPUT + ":" + relative).decode()
    errors = [e for e in errors if (e[0], e[1]) not in known]
    assert not errors, json.dumps(errors, ensure_ascii=False, indent=2)
    puml = [entry["path"] for entry in manifest["targets"] if entry["path"].endswith(".puml")]
    assert len(puml) == 11
    for path in puml:
        source = text(path)
        assert source.count("@startuml") == source.count("@enduml") == 1
    svg = ET.parse(HERE / "gantt.svg").getroot()
    metadata = json.loads(svg.find("{http://www.w3.org/2000/svg}metadata").text)
    assert metadata["snapshot_version"] == 17
    assert metadata["next_tasks"]["TASK-T-008"]["status"] == "DONE"
    assert metadata["next_tasks"]["TASK-D-008"]["status"] == "DONE"
    assert metadata["next_tasks"]["TASK-D-008"]["owner_accepted"] is True
    adr = text("docs/requirements/decisions/0042-passive-chart-renderer.md")
    assert "Статус: принято Owner" in adr and "Активное колесо — будущая фича" in adr
    base_sha = git("merge-base", MAIN, head).decode().strip()
    base, main, current = tree(base_sha), tree(MAIN), tree(head)
    conflicts = [{"path": p, "base_blob": oid, "change_blob": current[p], "resolution": "KEEP_CURRENT_CHANGE"}
                 for p, oid in sorted(base.items()) if p not in main and p in current and current[p] != oid]
    assert len(conflicts) == 16 and all(c["path"].startswith("docs/") for c in conflicts)
    debt = text(DEBT)
    ids = re.findall(r"^## (DEBT-[A-Z]+-\d+)", debt, re.M)
    assert len(ids) == len(set(ids)), "Duplicate DebtId"
    old_debt = git("show", MAIN + ":" + DEBT).decode()
    # Header status/date changed in c7219e4; preserve all existing registry sections.
    old_sections = old_debt[old_debt.index("\n## "):].rstrip()
    sections = debt[debt.index("\n## "):]
    assert sections.startswith(old_sections), "Existing main registry entries changed"
    for suffix in ("002", "003", "004"):
        block = debt.split('## DEBT-UI-' + suffix, 1)[1].split('\n## ', 1)[0]
        assert all(s in block for s in ("OPEN", "Owner", "Developer", "возврат", "P2" if suffix == "004" else "P3"))
        for ref, path in re.findall(r'https://github.com/ksenia-baranova/exact-orb-demo/blob/([0-9a-f]{40})/([^\s)#]+)', block):
            git("cat-file", "-e", ref + ":" + unquote(path))
    patch = "".join(difflib.unified_diff(old_debt.splitlines(True), debt.splitlines(True),
                                      fromfile="a/" + DEBT, tofile="b/" + DEBT, n=0))
    with tempfile.TemporaryDirectory(prefix="ui-chart-registry-") as scratch:
        scratch_root = Path(scratch).resolve()
        assert scratch_root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        scratch_debt = scratch_root / DEBT
        scratch_debt.parent.mkdir(parents=True)
        scratch_debt.write_text(old_debt, encoding="utf-8", newline="\n")
        for flags in (("--check",), ()):
            subprocess.run(["git", "apply", "--unidiff-zero", *flags, "-"],
                           cwd=scratch_root, input=patch.encode(), check=True)
        assert digest(scratch_debt.read_bytes()) == digest(debt.encode())
    result = {"author": "Codex / Manager; author checks, not independent Tester", "input_sha": INPUT, "checkout_head_sha": head,
              "main_sha": MAIN, "transfer_sha": TRANSFER, "tester_output_sha": TESTER,
              "original_tester_verdict": "TRANSFER_REWORK_REQUIRED", "corrections": ["T008-R01", "T008-R02", "T008-N01"],
              "independent_corrected_review": "NOT RUN / TASK-T-009", "adr_0042": "ACCEPTED by Owner for current passive M1-8",
              "active_wheel": "FUTURE FEATURE; not canceled, no current implementation/estimate authorized",
              "requirements": 22, "scenarios": 53, "puml_structure_pass": len(puml), "plantuml_render": "NOT RUN",
              "target_hashes_pass": len(manifest["targets"]), "removed_sources": len(source_paths),
              "historical_reports_unchanged": len(manifest["historical_reports_preserved"]),
              "runtime_files_unchanged": len(runtime_files), "src_tests": "UNCHANGED", "local_links_checked": count,
              "link_errors": errors, "preexisting_link_errors": inherited,
              "negative_controls": ["old AS09 F2 detected", "retired Git directory absent"],
              "node_command": "node --test tests/ui/*.test.mjs", "node_observed_result": "229 passed / 0 failed",
              "browser_https_full_pytest": "NOT RUN in this session", "gantt_snapshot": 17,
              "registry_patch": {"base_sha": MAIN, "candidate_sha256_lf": digest(debt.encode()), "existing_main_entries": "UNCHANGED",
                                 "check_and_apply_in_scratch": "PASS; exact candidate reconstructed", "apply_option": "--unidiff-zero"},
              "merge_base": base_sha, "documentary_modify_delete": conflicts, "code_intersection": False,
              "git_publication": "OWNER AUTHORIZED commit/push everything to change only; PR/merge/role dispatch NOT AUTHORIZED", "merge_sha": None}
    if write:
        (HERE / "registry-publication.patch").write_text(patch, encoding="utf-8", newline="\n")
        plan = ("# Подготовка интеграции ui-chart-wheel в main\n\n"
                f"Проверенная база `{MAIN}`, change `{INPUT}`, merge-base `{base_sha}`.\n"
                "Main tree равен исходному5355510; кодовых пересечений нет. Никакой настоящий merge не выполнялся.\n\n"
                "После разрешённой публикации исправлений, адресного T009, решения ADR и отдельного registry PR:\n\n"
                "1. Повторить fetch; при движении main заново классифицировать пересечение и обновить этот план.\n"
                "2. В согласованном change checkout интегрировать main; сохранить актуальные версии следующих16 документов вместо удалений прежнего revert.\n"
                "3. Сохранить опубликованный main-реестр (не вернуть его устаревшую копию); сравнить итоговый tree с проверенным change и registry SHA.\n"
                "4. Зафиксировать CandidateSHA, выполнить нужные проверки; старые runtime results остаются на9974195, применимость подтверждается diff.\n"
                "5. После разрешённого final PR/merge проверить main tree, записать PR/MergeSHA; только затем «Поставка: интегрирована».\n\n"
                "| Путь | Сохранить Git blob change |\n|---|---|\n")
        for c in conflicts:
            plan += f"| `{c['path']}` | `{c['change_blob']}` |\n"
        plan += "\nДля уже изменённых в этой сессии документов сохранить новую опубликованную редакцию; blob выше фиксирует исходный72ab4e3, не разрешает откат локальных исправлений.\n"
        (HERE / "main_integration_plan.md").write_text(plan, encoding="utf-8", newline="\n")
        (HERE / "session_closure_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"SESSION_CLOSURE_CHECKS_OK req=22 as=53 puml=11 targets={len(manifest['targets'])} runtime={len(runtime_files)} links={count} conflicts=16")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    run(parser.parse_args().write)
