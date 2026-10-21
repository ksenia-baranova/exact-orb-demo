"""Independent TASK-T-008 audit. Reads pinned Git inputs; never reruns historical manifests."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys
from urllib.parse import unquote
ROOT=next(p for p in Path(__file__).resolve().parents if (p/".git").exists())
HERE=Path(__file__).resolve().parent
R="docs/project_management/change_plans/ui-chart-wheel/"
S="883b6d3a47f7113e44ede73c9ad16b40f15bbdaf"
T="c7219e485917366f67159c9a08e3c78dc4e69372"
RUNTIME="99741958b4bbee8884505920f4a02f2f19dea3e3"
OUTPUT="f930c864d6a416acff8a49081585950853b931f9"
def git(*a): return subprocess.check_output(["git","-C",str(ROOT),*a])
cache={}
def blob(ref,path):
 key=(ref,path)
 if key not in cache: cache[key]=git("show",ref+":"+path)
 return cache[key]
def lf(b): return b.replace(b"\r\n",b"\n")
def sha(b): return hashlib.sha256(b).hexdigest()
def text(ref,path): return lf(blob(ref,path)).decode("utf8")
def listed(ref,*paths): return git("ls-tree","-r","--name-only",ref,"--",*paths).decode().splitlines()
def blocks(t,prefix):
 matches=list(re.finditer(r"(?m)^### ("+prefix+r"-\d{2})[. ]([^\n]*)",t));out={}
 for m in matches:
  end=re.search(r"(?m)^#{1,3} ",t[m.end():])
  b=t[m.start():m.end()+end.start()] if end else t[m.start():]
  b=re.sub(r'<a id="[^"]+"></a>\s*',"",b).strip()
  assert m[1] not in out,m[1]
  out[m[1]]=b
 return out
def ids(prefix,n): return {prefix+"-"+str(i).zfill(2) for i in range(1,n+1)}
m=json.loads(blob(T,R+"manager/transfer_manifest.json"))
assert m["source_sha"]==S and len(m["moves"])==13 and m["removed_source_count"]==13
for ref in (S,T,RUNTIME,OUTPUT): assert git("cat-file","-t",ref).strip()==b"commit"
assert git("branch","--show-current").decode().strip()=="test/ui-chart-wheel"
git("merge-base","--is-ancestor",T,"HEAD")
assert not git("diff","--cached","--name-only").strip()
git("merge-base","--is-ancestor",S,T)
moves=[]
tree_paths=set(listed(T))
for move in m["moves"]:
 p=move["source"];dst=move["target"];a=lf(blob(S,p));b=lf(blob(T,dst))
 assert p not in tree_paths and dst in tree_paths,p
 assert sha(a)==move["source_git_sha256_lf"]
 projections=[a,a.replace(b"\n",b"\r\n")]
 legacy=next((x for x in projections if sha(x)==move["source_sha256"] and len(x)==move["source_bytes"]),None)
 assert legacy is not None,p
 assert sha(b)==move["target_sha256"],dst
 moves.append({"source":p,"target":dst,"source_git_sha256_lf":sha(a),"source_snapshot_sha256":sha(legacy),
               "source_snapshot_eol":"CRLF" if legacy!=a else "LF","target_sha256_lf":sha(b),"source_absent":True})
targets=[]
for obj in m["targets"]:
 data=lf(blob(T,obj["path"]));assert sha(data)==obj["sha256"],obj["path"]
 targets.append({"path":obj["path"],"sha256_lf":sha(data)})
birth="docs/requirements/current/ui/birth-form-and-facts.md"
wheel="docs/requirements/current/ui/chart-wheel.md";scenarios="docs/requirements/current/ui/scenarios.md"
assert sha(lf(blob(S,birth)))==m["original_birth_sha256"]
req_old=blocks(text(S,R+"analyst/requirements.md"),r"REQ-(?:UI|WHEEL)")
req_baseline=blocks(text(S,birth),"REQ-UI")
req_new={**blocks(text(T,birth),"REQ-UI"),**blocks(text(T,wheel),"REQ-WHEEL")}
as_old={**blocks(text(S,scenarios),"AS-UI"),**blocks(text(S,R+"analyst/scenarios.md"),"AS-WHEEL")}
ui22_delta=blocks(text(S,R+"analyst/scenarios.md"),"AS-UI")["AS-UI-22"]
as_new={**blocks(text(T,scenarios),"AS-UI"),**blocks(text(T,scenarios),"AS-WHEEL")}
assert set(req_new)==ids("REQ-UI",11)|ids("REQ-WHEEL",11)
assert set(as_new)==ids("AS-UI",23)|ids("AS-WHEEL",30)
for id in ["REQ-UI-02","REQ-UI-07"]: assert req_new[id]==req_baseline[id],id
for id in sorted(ids("AS-UI",23)-{"AS-UI-22"}): assert as_old[id]==as_new[id],id
req_rows=[]
for id,new in sorted(req_new.items()):
 original=req_old.get(id,req_baseline.get(id))
 assert original,id
 req_rows.append({"id":id,"source":R+"analyst/requirements.md" if id in req_old else birth,
                  "source_sha256_lf":sha(original.encode()),"target":birth if id.startswith("REQ-UI") else wheel,
                  "target_sha256_lf":sha(new.encode()),"unchanged_body":original==new})
as_rows=[{"id":id,"source":scenarios if id.startswith("AS-UI") else R+"analyst/scenarios.md",
          "source_sha256_lf":sha(as_old[id].encode()),"target":scenarios,"target_sha256_lf":sha(new.encode()),
          "unchanged_body":as_old[id]==new} for id,new in sorted(as_new.items())]
def puml_structure(p,t):
 assert t.count("@startuml")==t.count("@enduml")==1,p
 assert t.strip().startswith("@startuml") and t.strip().endswith("@enduml"),p
 stack=[]
 for number,line in enumerate(t.splitlines(),1):
  line=line.strip()
  if not line or line.startswith("'"): continue
  if re.match(r"^(alt|opt|loop|group|par|critical|break)\b",line): stack.append(("block",number))
  elif re.match(r"^(note|ref)\b",line) and ":" not in line: stack.append((line.split()[0],number))
  elif line=="end":
   assert stack and stack[-1][0]=="block",(p,number,stack)
   stack.pop()
  elif line in ("end note","end ref"):
   assert stack and stack[-1][0]==line.split()[1],(p,number,stack)
   stack.pop()
 assert not stack,(p,stack)
 assert "!include" not in t,p
seq=[]
for move in m["moves"]:
 p=move["target"]
 if not p.endswith(".puml"):continue
 a=text(S,move["source"]);b=text(T,p);puml_structure(p,b)
 archive="/research/" in p
 if archive:
  assert "ARCHIVED / SUPERSEDED" in b
  assert "\n".join(b.splitlines()[:1]+b.splitlines()[3:])+"\n"==a
 elif "/technical/" in p:
  assert "DRAFT" in b
  assert "\n".join(b.splitlines()[:1]+b.splitlines()[3:])+"\n"==a
 else:
  assert "Passive" in b or "passive" in b
 seq.append({"source":move["source"],"target":p,"status":"ARCHIVED" if archive else "CURRENT",
             "structure":"PASS (limited block syntax; not PlantUML compiler)","body_unchanged":archive or "/technical/" in p})
assert len(seq)==11 and sum(s["status"]=="CURRENT" for s in seq)==8
source_png=[]
for move in m["moves"]:
 if move["source"].endswith(".puml"):
  png=move["source"][:-5]+".png"
  if png in set(listed(S,png)):source_png.append(png)
assert not source_png
protected=[]
for p in m["historical_reports_preserved"]:
 assert blob(S,p)==blob(T,p),p
 protected.append(p)
raw_paths=list(dict.fromkeys(listed(S,R+"tester/evidence",R+"developer/evidence")))
assert not git("diff","--name-only",S,T,"--",R+"tester/evidence",R+"developer/evidence").strip()
for name in ("src","tests"):
 assert git("rev-parse",S+":"+name)==git("rev-parse",T+":"+name)==git("rev-parse",RUNTIME+":"+name)
suites=json.loads(blob(OUTPUT,R+"tester/evidence/retest_2026_10_20_004/suites.json"))
assert suites["tested_sha"]==RUNTIME and len(suites["source_sha256_lf"])==14
for p,h in suites["source_sha256_lf"].items():
 assert sha(lf(blob(T,p)))==h==sha(lf(blob(RUNTIME,p))),p
v=json.loads(blob(OUTPUT,R+"tester/evidence/retest_2026_10_20_004/verification.json"))
navigation_delta=[];transfer_payloads=0
for p,h in v["payload_sha256_lf_text_raw_logs_png"].items():
 original=blob(S,p)
 assert sha(original if p.endswith((".png",".log")) else lf(original))==h,p
 data=blob(T,p)
 if sha(data if p.endswith((".png",".log")) else lf(data))==h:transfer_payloads+=1
 else:navigation_delta.append(p)
assert navigation_delta==[R+"tester_artifact.md"],navigation_delta
def navigation_neutral(t):
 t=re.sub(r"(?m)^\*\*Навигационная запись Manager21\.10[^\n]+\n\n","",t)
 return re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",t)
assert navigation_neutral(text(S,R+"tester_artifact.md"))==navigation_neutral(text(T,R+"tester_artifact.md"))
def anchors(t):
 out=set(re.findall(r'<a\s+id="([^"]+)"',t));counts={}
 for h in re.findall(r"^#{1,6}\s+(.+)$",t,re.M):
  h=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",h)
  slug=re.sub(r"\s","-",re.sub(r"[^\w\s-]","",h.lower()))
  n=counts.get(slug,0);counts[slug]=n+1;out.add(slug if not n else slug+"-"+str(n))
 return out
changed=git("diff","--name-only",S,T).decode().splitlines()
mds=sorted(p for p in changed if p.endswith(".md") and p in tree_paths)
def audit_links(ref,paths):
 errors=[];count=tables=0;present=set(listed(ref))
 entries=present|{str(parent).replace("\\","/") for path in present for parent in Path(path).parents if str(parent)!="."}
 for p in paths:
  if p not in present:continue
  t=text(ref,p);columns=None
  for line in t.splitlines():
   if line.startswith("|"):
    n=len(re.split(r"(?<!\\)\|",line))
    if columns is None:tables+=1
    if columns is not None and n!=columns:errors.append([p,"table","column count"])
    columns=n
   else: columns=None
  for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",t):
   if re.match(r"^[A-Za-z]+:",dest):continue
   if "<" in dest or ">" in dest:continue
   part,_,anchor=unquote(dest).partition("#")
   target=((ROOT/p).parent/part).resolve() if part else ROOT/p
   try:rel=target.relative_to(ROOT).as_posix()
   except ValueError:errors.append([p,dest,"outside root"]);continue
   count+=1
   if rel not in entries:errors.append([p,dest,"missing"])
   elif anchor and rel.endswith(".md") and anchor not in anchors(text(ref,rel)):errors.append([p,dest,"anchor"])
 return {"documents":len(paths),"links":count,"tables":tables,"errors":errors}
links=audit_links(T,mds);old_links=audit_links(S,mds)
old_errors={tuple(e) for e in old_links["errors"]}
new_errors=[e for e in links["errors"] if tuple(e) not in old_errors]
assert new_errors==[[R+"manager_artifact.md","analyst/sequence_diagrams/ui/","missing"]],new_errors
assert len(protected)==17 and len(v["payload_sha256_lf_text_raw_logs_png"])==40
issues=[
 {"id":"T008-N01","type":"nonblocking traceability clarification","scenario":"AS-WHEEL-28",
  "source_has_initial_matrix":"S1 controls U/R/D/V/M/L/T/P" in as_old["AS-WHEEL-28"],
  "target_has_initial_matrix":"S1 controls U/R/D/V/M/L/T/P" in as_new["AS-WHEEL-28"],
  "retained_elsewhere":"F5 inputs and expected plus unaffected positive controls, REQ-WHEEL-04/08/10 and AS-WHEEL-23/30 survive; no whole-package S1 loss",
  "recommendation":"Make AS-WHEEL-28 point explicitly to preserved F5 and related scenarios; not a new runtime blocker"},
 {"id":"T008-R01","type":"transfer data reference","scenario":"AS-WHEEL-09",
  "source_precondition":next(l for l in as_old["AS-WHEEL-09"].splitlines() if "Предусловия" in l),
  "target_precondition":next(l for l in as_new["AS-WHEEL-09"].splitlines() if "Предусловия" in l),
 "fixture_F2":"session view/state fixture","fixture_F3":"five R through zero"},
 {"id":"T008-R02","type":"new broken navigation link","errors":new_errors,
 "baseline_directory_existed":True,"transfer_directory_removed":True}
]
assert issues[0]["source_has_initial_matrix"] and not issues[0]["target_has_initial_matrix"]
assert "F2" in issues[1]["target_precondition"] and "F3" in issues[1]["source_precondition"]
scope={line[3:] for line in git("status","--porcelain","--untracked-files=all").decode().splitlines()}
scope.update(git("diff","--name-only",T,"HEAD").decode().splitlines())
allowed={R+"tester_artifact.md",R+"tester/transfer_review.md",R+"tester/defects.md"}
assert all(p in allowed or p.startswith(R+"tester/evidence/task_t008/") for p in scope),scope
stashes=git("stash","list","--format=%H").decode()
assert all(h in stashes for h in ["0c2eb3ba6e9b6d191830da6a0d1c132a34762679","d936068b2806107cbe21499538b4f038780cc7fb"])
main=git("rev-parse","origin/main").decode().strip()
main_debt=text(main,"docs/project_management/technical_debt.md")
own_docs=[R+"tester/transfer_review.md",R+"tester_artifact.md",R+"tester/defects.md"]
own_link_errors=[];own_links=own_tables=0
baseline_own_errors={tuple(e) for e in audit_links(T,[p for p in own_docs if p in tree_paths])["errors"]}
for p in own_docs:
 t=(ROOT/p).read_text(encoding="utf8")
 assert t.endswith("\n") and not t.endswith("\n\n") and all(l==l.rstrip() for l in t.splitlines()),p
 columns=None
 for line in t.splitlines():
  if line.startswith("|"):
   n=len(re.split(r"(?<!\\)\|",line))
   if columns is None:own_tables+=1
   assert columns is None or n==columns,(p,line)
   columns=n
  else:columns=None
 for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",t):
  if re.match(r"^[A-Za-z]+:",dest):continue
  if "<" in dest or ">" in dest:continue
  part,_,anchor=unquote(dest).partition("#")
  target=((ROOT/p).parent/part).resolve() if part else ROOT/p
  own_links+=1
  if not target.exists():own_link_errors.append([p,dest,"missing"])
  elif anchor and target.suffix==".md" and anchor not in anchors(target.read_text(encoding="utf8")):own_link_errors.append([p,dest,"anchor"])
own_new_errors=[e for e in own_link_errors if tuple(e) not in baseline_own_errors]
assert not own_new_errors,own_new_errors
assert lf((ROOT/(R+"tester_artifact.md")).read_bytes()).startswith(lf(blob(T,R+"tester_artifact.md")))
current_defects=(ROOT/(R+"tester/defects.md")).read_text(encoding="utf8")
assert "| P2, PROPOSED | CLOSED | Нет по004" in current_defects
assert "**Статус:** OPEN." in current_defects.split("## TEST-FIND-WHEEL-002.")[1].split("## TEST-FIND-WHEEL-003.")[0]
own_hashes={p:sha(lf((ROOT/p).read_bytes())) for p in own_docs}
own_hashes[HERE.relative_to(ROOT).as_posix()+"/verify_transfer.py"]=sha(lf(Path(__file__).read_bytes()))
result={"author":"Codex / Tester","task":"TASK-T-008","input_head":T,"assignment_sha":T,"transfer_sha":T,
"source_sha":S,"retested_sha":RUNTIME,"tester_output_sha":OUTPUT,"estimate":"2-4h; medium-high; 2026-10-21 18:00 MSK",
"started_msk":"2026-10-21 14:01","method":"Independent Git source reads and semantic review; not a rerun of Manager validation",
"moves":moves,"targets":targets,"requirements":req_rows,"scenarios":as_rows,"sequences":seq,
"as_ui_22_delta":{"source":R+"analyst/scenarios.md#as-ui-22","sha256_lf":sha(ui22_delta.encode()),
"late_owner":"first-five points decision 2026-10-20; source all-points-now replaced explicitly"},
"counts":{"req":len(req_rows),"as":len(as_rows),"puml":len(seq),"current_puml":8,"archived_puml":3,
"removed_sources":13,"source_png":0,"historical_reports":17,"raw_evidence_files":len(raw_paths)},
"links":links,"baseline_link_errors":old_links["errors"],"new_link_errors":new_errors,
"own_documents":{"documents":len(own_docs),"links":own_links,"tables":own_tables,"new_link_errors":own_new_errors,
"inherited_historical_links":len(own_link_errors),"payload_sha256_lf":own_hashes},
"runtime":{"src_tree_equal":True,"tests_tree_equal":True,"source_fingerprints":14,"source_payload_hashes":40,
"transfer_payload_hashes":transfer_payloads,"intentional_navigation_delta":navigation_delta,"old_verdict_text_preserved":True,
"applicable":True,"new_runtime":"NOT RUN; documentation only; no implementation mismatch reproduced",
"recorded_results":{"node_target":41,"node_all":229,"python_target":53,"pytest":2959,"skipped":1,"native_cases":6,"native_checks":672}},
"renderer":{"plantuml":shutil.which("plantuml"),"java":shutil.which("java"),"dot":shutil.which("dot"),
"render":"NOT RUN; no local PlantUML command or repository jar found"},
"debt":{"002":"OPEN","precision":"INDETERMINATE","004":"CLOSED / RETEST_PASS","debt":"DEBT-UI-004",
"main_ref":main,"main_contains_004":bool(re.search(r"^## DEBT-UI-004\b",main_debt,re.M)),"registry_publication_confirmed":False},
"issues":issues,"verdict":"TRANSFER_REWORK_REQUIRED; hashes/IDs/PUML structure and S1 semantics PASS; one fixture reference and one navigation correction",
"index":"EMPTY","stashes":"PRESERVED","foreign_changes":"NONE",
"publication":{"owner_authorization":"2026-10-21: commit/push test then merge change",
"audit_phase":"PACKAGE_PRE_STAGING; actual remote publication checked separately after execution",
"fetched_change_base":T,"fetched_test_base":OUTPUT,
"source_sha_resolver":"first git log --reverse --format=%H -G '^### Публикация TASK-T-008 — 2026-10-21$' -- "+R+"tester_artifact.md"}}
out=HERE/"review.json"
if "--write" in sys.argv:out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
else:assert json.loads(out.read_text(encoding="utf8"))==result,"Audit inputs or local scope changed; inspect before regeneration"
print("T008_GIT_OK removed=13 moves=13 targets="+str(len(targets))+" historical=17 raw="+str(len(raw_paths)))
print("T008_IDS_OK req=22 as=53 puml=11 current=8 archived=3 unchanged_UI=2 unchanged_AS_UI=22")
print("T008_HASH_OK source_Git_LF=13 snapshot_projection=13 targets=16 source_UI=14 source_payloads=40 transfer_payloads="+str(transfer_payloads)+" navigation_only=1")
print("T008_LINKS_REWORK "+json.dumps({k:v for k,v in links.items() if k!="errors"})+" inherited_errors="+str(len(old_links["errors"]))+" new_errors="+str(len(new_errors)))
print("T008_RUNTIME_APPLICABLE retested="+RUNTIME+" src/tests=UNCHANGED new_runtime=NOT_RUN")
print("T008_OWN_DOCS_OK docs=3 links="+str(own_links)+" tables="+str(own_tables)+" new_errors=0 payloads=4 index=EMPTY stashes=PRESERVED")
print("T008_VERDICT TRANSFER_REWORK_REQUIRED T008-R01 T008-R02; T008-N01 advisory; 004=CLOSED 002=OPEN precision=INDETERMINATE")
