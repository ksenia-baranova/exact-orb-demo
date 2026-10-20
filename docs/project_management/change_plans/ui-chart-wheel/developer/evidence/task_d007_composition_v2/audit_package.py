"""Audit final composition package without mutating index or historical evidence."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,re,subprocess
B=Path(__file__).resolve().parent;R=B.parents[6];D=B.parent.parent
baseline=json.loads((B/"baseline.json").read_text(encoding="utf8"))
errors=[]
def hashfile(p,lf=False):
 raw=p.read_bytes()
 return hashlib.sha256(raw.replace(b"\r\n",b"\n") if lf else raw).hexdigest()
for name,expected in baseline["protected_raw"].items():
 if hashfile(R/name)!=expected:errors.append("Historical evidence changed: "+name)
run_paths=["native03","focus05","compact01","angle01"]
native=0;assertions=0;frames=0;min_gap=None
for run in run_paths:
 data=json.loads((B/run/"actual.json").read_text(encoding="utf8"))
 for name,expected in data["sources"].items():
  if hashfile(R/"src/exact_orb/http_api/ui"/name,True)!=expected:errors.append("Source differs "+run+"/"+name)
 for case in data["cases"]:
  if not case["pass"]:errors.append("FAIL "+run+"/"+case["id"])
  assertions+=len(case.get("checks",[]))
  for frame_name in ["normal","selected"]:
   if frame_name not in case:continue
   frame=case[frame_name];W,H=F(frame["width"]),F(frame["height"]);groups=frame["groups"];frames+=1
   for i,g in enumerate(groups):
    for raw in g["parts"]:
     b=list(map(F,raw))
     if not(0<=b[0]<=b[2]<=W and 0<=b[1]<=b[3]<=H):errors.append("Clip "+run+"/"+case["id"]+"/"+g["key"])
     for other in groups[i+1:]:
      for raw_c in other["parts"]:
       c=list(map(F,raw_c));dx=max(b[0]-c[2],c[0]-b[2],0);dy=max(b[1]-c[3],c[1]-b[3],0);gap=dx*dx+dy*dy
       min_gap=gap if min_gap is None else min(min_gap,gap)
       if gap<4:errors.append("Gap "+run+"/"+case["id"]+"/"+frame_name+"/"+g["key"]+"/"+other["key"])
 native+=len(data["cases"])
 if "boundary" in data and not all(c["pass"] for c in data["boundary"]["controls"]):errors.append("Boundary FAIL")
geometry=json.loads((B/"native03-independent.json").read_text(encoding="utf8"))
if geometry["pass"]!=35 or not all(c["pass"] for c in geometry["controls"]):errors.append("Independent geometry FAIL")
docs=[D/"full_wheel_implementation_plan.md",D/"drawing_adr_column_draft.md",
 D/"prompts/06-owner-composition-aspect-view.md",D.parent/"developer_artifact.md",B/"README.md"]
links=0
for p in docs:
 text=p.read_text(encoding="utf8")
 for target in re.findall(r"\[[^\]]*\]\(([^)\n]+)\)",text):
  target=target.strip("<>").split("#",1)[0]
  if not target or re.match(r"^[a-zA-Z]+:",target):continue
  links+=1;dest=(p.parent/target).resolve()
  if dest!=B/"audit.json" and not dest.exists():errors.append("Broken link "+str(p)+":"+target)
for name in ["004-column-layout-revision.puml","006-aspect-reading-mode.puml"]:
 text=(D/"sequence_diagrams/ui"/name).read_text(encoding="utf8")
 if text.count("@startuml")!=1 or text.count("@enduml")!=1:errors.append("Diagram delimiters "+name)
 if len(re.findall(r"^alt\b",text,re.M))!=len(re.findall(r"^end$",text,re.M)):errors.append("Diagram alt "+name)
 if len(re.findall(r"^note\b",text,re.M))!=len(re.findall(r"^end note$",text,re.M)):errors.append("Diagram note "+name)
index=R/"docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md"
prefix=index.read_text(encoding="utf8").split("\n## TASK-D-007 — исправления по замечаниям Owner20.10",1)[0]
if hashlib.sha256(prefix.encode("utf8")).hexdigest()!=baseline["source_lf"][index.relative_to(R).as_posix()]:errors.append("Role history prefix changed")
def git(*args):return subprocess.check_output(["git",*args],cwd=R,text=True,encoding="utf8").strip()
head=git("rev-parse","HEAD");branch=git("branch","--show-current");staged=git("diff","--cached","--name-only")
if head!=baseline["InputSHA"] or branch!="dev/ui-chart-wheel":errors.append("HEAD/branch changed")
if staged:errors.append("Index changed")
paths=git("diff","--name-only","HEAD").splitlines()+git("ls-files","--others","--exclude-standard").splitlines()
for path in paths:
 if not(path.startswith(("src/exact_orb/http_api/ui/","tests/ui/","docs/project_management/change_plans/ui-chart-wheel/developer/")) or path in ["docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md","tests/http_api/test_ui_delivery.py"]):errors.append("Outside role scope "+path)
check=subprocess.run(["git","diff","--check"],cwd=R,capture_output=True,text=True)
if check.returncode:errors.append(check.stdout+check.stderr)
for path in paths:
 p=R/path
 if not p.is_file() or p.suffix==".png":continue
 for i,line in enumerate(p.read_text(encoding="utf8").splitlines(),1):
  if line.rstrip()!=line:errors.append("Whitespace "+path+":"+str(i))
result={"pass":not errors,"errors":errors,"head":head,"branch":branch,"index":"EMPTY" if not staged else staged,
 "preserved_raw_files":len(baseline["protected_raw"]),"native_cases":native,"mode_assertions":assertions,
 "exact_mode_bbox_frames":frames,"mode_min_gap_squared":float(min_gap),"independent_geometry":"35/35+7/7",
 "local_links":links,"diagrams":2,"diff_check_exit":check.returncode,"changed_or_new_files":paths}
(B/"audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("COMPOSITION_V2_OK" if not errors else "COMPOSITION_V2_FAIL","cases="+str(native),"assertions="+str(assertions),"bbox_frames="+str(frames),"links="+str(links),"preserved="+str(len(baseline["protected_raw"])))
for error in errors:print(error)
raise SystemExit(bool(errors))
