"""Checks current dark palette evidence; preserves prior runtime snapshots."""
import hashlib,json,subprocess
from pathlib import Path
B=Path(__file__).resolve().parent
R=B.parents[6]
base=json.loads((B/"baseline.json").read_text(encoding="utf8"))
run=json.loads((B/"run01/actual.json").read_text(encoding="utf8"))
old=json.loads((B.parent/"task_d007_runtime/run05/actual.json").read_text(encoding="utf8"))
def sha(path,lf=False):
 data=path.read_bytes()
 return hashlib.sha256(data.replace(b"\r\n",b"\n") if lf else data).hexdigest()
errors=[]
for name,expected in base["protected_raw_sha256"].items():
 if sha(R/name)!=expected:errors.append("Old runtime evidence changed: "+name)
for name,expected in run["sources"].items():
 if sha(R/"src/exact_orb/http_api/ui"/name,True)!=expected:errors.append("Current source differs: "+name)
changed=[name for name,value in run["sources"].items() if old["sources"].get(name)!=value]
if sorted(changed)!=["styles.css","wheel_layout.mjs","wheel_svg.mjs"]:errors.append("Unexpected source delta: "+str(changed))
if len(run["cases"])!=9 or not all(c["pass"] and c["geometryUnchanged"] for c in run["cases"]):errors.append("Native cases fail")
prefix=(R/"docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md").read_bytes().replace(b"\r\n",b"\n").split(b"\n## TASK-D-007 \xe2\x80\x94 \xd1\x87\xd1\x91\xd1\x80\xd0\xbd\xd0\xb0\xd1\x8f \xd1\x82\xd0\xb5\xd0\xbc\xd0\xb0 Owner",1)[0]
if hashlib.sha256(prefix).hexdigest()!=base["before_lf_sha256"]["docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md"]:errors.append("Role handoff history changed")
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip()
if head!=base["inputSHA"]:errors.append("HEAD changed")
staged=subprocess.check_output(["git","diff","--cached","--name-only"],cwd=R,text=True).strip()
if staged:errors.append("Index no longer empty")
diff=subprocess.run(["git","diff","--check"],cwd=R,capture_output=True,text=True)
if diff.returncode:errors.append(diff.stdout+diff.stderr)
result={"pass":not errors,"errors":errors,"native_pass":sum(c["pass"] for c in run["cases"]),"old_evidence_preserved":len(base["protected_raw_sha256"]),"source_changed":changed,"head":head,"index":"EMPTY" if not staged else staged,"diff_check_exit":diff.returncode}
(B/"audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("DARK_THEME_OK" if not errors else "DARK_THEME_FAIL",json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(errors))
