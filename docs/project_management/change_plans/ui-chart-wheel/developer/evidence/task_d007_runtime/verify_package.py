"""D007 local package/source/link audit. Does not mutate index or historical evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[6]
DEV = ROOT / "docs/project_management/change_plans/ui-chart-wheel/developer"
INDEX = DEV.parent / "developer_artifact.md"
DOCS = [INDEX, DEV / "full_wheel_implementation_plan.md",
        DEV / "drawing_adr_column_draft.md", DEV / "owner_decision_already_applied_2026-10-20.md", BASE / "README.md"]
DIAGRAMS = [DEV / "sequence_diagrams/ui" / name for name in
            ["003-passive-copy-install.puml", "004-column-layout-revision.puml", "005-accepted-once-editor.puml"]]
RUNTIME = "docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/"
ALLOWED = {
 "docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md",
 "docs/project_management/change_plans/ui-chart-wheel/developer/full_wheel_implementation_plan.md",
 "docs/project_management/change_plans/ui-chart-wheel/developer/drawing_adr_column_draft.md",
 "docs/project_management/change_plans/ui-chart-wheel/developer/owner_decision_already_applied_2026-10-20.md",
 *[p.relative_to(ROOT).as_posix() for p in DIAGRAMS],
 *["src/exact_orb/http_api/ui/" + name for name in
   ["facts.mjs","main.mjs","session.mjs","styles.css","result_controller.mjs","wheel_layout.mjs","wheel_svg.mjs"]],
 "tests/http_api/test_ui_delivery.py","tests/ui/accepted_chart.test.mjs","tests/ui/wheel_layout.test.mjs"
}
def git(*args):
 return subprocess.check_output(["git",*args],cwd=ROOT).decode("utf8").strip()
def lf_bytes(path):
 raw=path.read_bytes()
 if path.suffix.lower() in {".md",".mjs",".cjs",".css",".html",".py",".puml",".json"}:
  return raw.replace(b"\r\n",b"\n")
 return raw
errors=[]
head=git("rev-parse","HEAD")
if head!="e0daa0e814d3d1fd34cadb8c17d064f19c4810f5":errors.append("Unexpected HEAD "+head)
branch=git("branch","--show-current")
if branch!="dev/ui-chart-wheel":errors.append("Unexpected branch "+branch)
staged=git("diff","--cached","--name-only")
if staged:errors.append("Index is no longer empty: "+staged)
changed=git("diff","--name-only","HEAD").splitlines()
untracked=git("ls-files","--others","--exclude-standard").splitlines()
for name in changed+untracked:
 if name not in ALLOWED and not name.startswith(RUNTIME):errors.append("Outside scope "+name)
# Historical role index and implementation plan are append-only this execution.
for p in [INDEX,DEV/"full_wheel_implementation_plan.md"]:
 old=subprocess.check_output(["git","show","HEAD:"+p.relative_to(ROOT).as_posix()],cwd=ROOT).replace(b"\r\n",b"\n")
 if not lf_bytes(p).startswith(old):errors.append("Historical prefix changed "+str(p))
links=0
for p in DOCS:
 s=p.read_text(encoding="utf8")
 for target in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)",s):
  target=target.strip("<>").split("#",1)[0]
  if not target or re.match(r"^[a-zA-Z]+:",target):continue
  links+=1
  if not (p.parent/target).resolve().exists():errors.append("Missing link "+str(p.relative_to(ROOT))+": "+target)
for p in DIAGRAMS:
 s=p.read_text(encoding="utf8")
 if s.count("@startuml")!=1 or s.count("@enduml")!=1:errors.append("Diagram delimiters "+p.name)
 if len(re.findall(r"^note\b",s,re.M))!=len(re.findall(r"^end note$",s,re.M)):errors.append("Diagram note balance "+p.name)
 # All diagrams in this package use alt/end only.
 if len(re.findall(r"^alt\b",s,re.M))!=len(re.findall(r"^end$",s,re.M)):errors.append("Diagram alt balance "+p.name)
for run in ["run05/actual.json","integration06/actual.json"]:
 data=json.loads((BASE/run).read_text(encoding="utf8"))
 for name,expected in data["sources"].items():
  actual=hashlib.sha256(lf_bytes(ROOT/"src/exact_orb/http_api/ui"/name)).hexdigest()
  if actual!=expected:errors.append("Source differs from "+run+": "+name)
 if not all(c["pass"] for c in data["cases"]):errors.append("Native FAIL "+run)
 if "boundary" in data and not all(c["pass"] for c in data["boundary"]["controls"]):errors.append("Boundary FAIL "+run)
for p in [ROOT/name for name in changed+untracked if not name.endswith(".png")]:
 if not p.is_file():continue
 for line_no,line in enumerate(p.read_text(encoding="utf8").splitlines(),1):
  if line.rstrip()!=line:errors.append("Trailing whitespace "+str(p.relative_to(ROOT))+":"+str(line_no))
check=subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,text=True)
if check.returncode:errors.append("git diff --check: "+check.stdout+check.stderr)
result={"head":head,"branch":branch,"index":"EMPTY" if not staged else staged,
 "changed_tracked":changed,"new_files":untracked,"local_links":links,"diagrams_structural":len(DIAGRAMS),
 "source_lf_matches":["run05","integration06"],"diff_check_exit":check.returncode,"errors":errors,"pass":not errors}
(BASE/"package_checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
entries={}
paths=set([ROOT/name for name in changed+untracked if (ROOT/name).is_file()])
paths.discard(BASE/"manifest.json");paths.discard(BASE/"package_checks.json")
for p in sorted(paths):
 entries[p.relative_to(ROOT).as_posix()]=hashlib.sha256(lf_bytes(p)).hexdigest()
(BASE/"manifest.json").write_text(json.dumps({"method":"SHA256; CRLF normalized to LF for text; PNG raw bytes",
 "exclusions":["manifest.json","package_checks.json"],"files":entries},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("D007_PACKAGE_OK" if not errors else "D007_PACKAGE_FAIL", "files="+str(len(entries)), "links="+str(links), "diagrams="+str(len(DIAGRAMS)))
for error in errors:print(error)
raise SystemExit(bool(errors))
