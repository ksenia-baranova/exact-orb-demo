"""Verify current Tester evidence without rerunning or rewriting historical audits."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
from urllib.parse import unquote
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/".git").exists())
R="docs/project_management/change_plans/ui-chart-wheel/"
PIN="0da99518ada67603b08ab4220d337e3a5e3aae60"
DOCS=[R+"tester_artifact.md",R+"tester/runtime_review_2026_10_20.md",R+"tester/defects.md",R+"tester/coverage_matrix.md"]
def git(*args):return subprocess.check_output(["git","-C",str(ROOT),*args]).decode("utf8").strip()
def lf(b):return b.replace(b"\r\n",b"\n")
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):return json.loads((HERE/name).read_text(encoding="utf8"))
git("merge-base","--is-ancestor",PIN,"HEAD")
assert git("branch","--show-current")=="test/ui-chart-wheel"
assert not git("diff","--cached","--name-only"),"Index must remain empty"
assert not git("diff","--name-only","--","src","tests","pyproject.toml",R+"developer",R+"analyst",R+"manager_artifact.md","docs/development_approach","AGENTS.md")
status=subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain","--untracked-files=all"]).decode("utf8").splitlines()
allowed=set(DOCS);prefix=HERE.relative_to(ROOT).as_posix()+"/"
scope={line[3:] for line in status}
scope.update(git("diff","--name-only",PIN,"HEAD").splitlines())
assert all(p in allowed or p.startswith(prefix) for p in scope),scope
stashes=git("stash","list","--format=%H")
assert all(s in stashes for s in ["0c2eb3ba6e9b6d191830da6a0d1c132a34762679","d936068b2806107cbe21499538b4f038780cc7fb"])
for p in git("ls-tree","-r","--name-only",PIN,"--",R+"tester").splitlines():
 if p in allowed:continue
 assert lf((ROOT/p).read_bytes())==lf(subprocess.check_output(["git","-C",str(ROOT),"show",PIN+":"+p])),p
index=R+"tester_artifact.md"
assert lf((ROOT/index).read_bytes()).startswith(lf(subprocess.check_output(["git","-C",str(ROOT),"show",PIN+":"+index])))
def anchors(text):
 out=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
 for h in re.findall(r"^#{1,6}\s+(.+)$",text,re.M):
  h=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",h)
  slug=re.sub(r"\s","-",re.sub(r"[^\w\s-]","",h.lower()))
  n=counts.get(slug,0);counts[slug]=n+1;out.add(slug if not n else slug+"-"+str(n))
 return out
links=tables=0
for name in DOCS:
 data=(ROOT/name).read_text(encoding="utf8");assert data.endswith("\n") and not data.endswith("\n\n"),name
 assert all(line==line.rstrip() for line in data.splitlines()),name
 columns=None
 for line in data.splitlines():
  if line.startswith("|"):
   count=len(re.split(r"(?<!\\)\|",line))
   if columns is None:tables+=1
   assert columns is None or count==columns,(name,line)
   columns=count
  else:columns=None
 for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",data):
  if re.match(r"^[A-Za-z]+:",dest):continue
  part,_,anchor=unquote(dest).partition("#");target=((ROOT/name).parent/part).resolve() if part else ROOT/name
  assert target.exists(),(name,dest)
  if anchor and target.suffix==".md":assert anchor in anchors(target.read_text(encoding="utf8")),(name,dest)
  links+=1
suites=load("suites.json");assert suites["tested_sha"]==PIN and suites["head_after"]==PIN and not suites["production_delta_after"]
assert len(suites["commands"])==5 and all(r["exit_code"]==0 for r in suites["commands"])
for r in suites["commands"]:
 assert sha((HERE/r["log"]).read_bytes())==r["log_sha256"]
 name=(HERE/r["log"]).relative_to(ROOT).as_posix()
 published=subprocess.run(["git","-C",str(ROOT),"cat-file","-e","HEAD:"+name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
 if published:assert sha(subprocess.check_output(["git","-C",str(ROOT),"show","HEAD:"+name]))==r["log_sha256"],"published raw log bytes differ: "+name
tokens={"node_target":"# pass 39","node_all_ui":"# pass 227","python_target":"53 passed","python_http_api":"300 passed","python_full":"2959 passed, 1 skipped"}
for r in suites["commands"]:assert tokens[r["name"]].encode() in (HERE/r["log"]).read_bytes()
sources=suites["source_sha256_lf"]
for p,h in sources.items():
 assert sha(lf((ROOT/p).read_bytes()))==h
 assert sha(lf(subprocess.check_output(["git","-C",str(ROOT),"show",PIN+":"+p])))==h,p
for name in ["native01/actual.json","native02/actual.json","probe01/actual.json","probe02/actual.json"]:
 d=load(name);assert d["tested_sha"]==PIN and not d.get("fatal"),name
 assert d["sources"]=={Path(p).name:h for p,h in sources.items()},name
native=load("native02/actual.json");assert len(native["cases"])==27
assert sum(len(r["checks"]) for r in native["cases"])==555
failed=[(r["id"],c["name"]) for r in native["cases"] for c in r["checks"] if not c["pass"]]
assert len(failed)==27
assert sum("native hit" in n for _,n in failed)==24
assert sum("component gap" in n for _,n in failed)==3
assert all(r["pass"] for r in native["cases"] if r["id"].startswith("lifecycle-"))
probes=load("probe02/actual.json")["cases"];assert len(probes)==3
for r in probes:
 assert not r["containedSquare44Possible"] and r["calibrationPass"]
 assert r["positiveCenterSelected"]=="true" and r["afterCornerSelected"]=="true"
 assert r["measure"]["box"]["height"]==44
 assert next(v["longest"] for v in r["measure"]["rows"] if v["offset"]==43)<44
viewport=[r for r in load("probe01/actual.json")["cases"] if r["id"].startswith("viewport-")]
assert len(viewport)==6 and all(r["pass"] for r in viewport)
payloads={p.relative_to(ROOT).as_posix():sha(p.read_bytes() if p.suffix==".png" else lf(p.read_bytes())) for p in sorted(HERE.rglob("*")) if p.is_file() and p.name!="verification.json"}
for p in DOCS:payloads[p]=sha(lf((ROOT/p).read_bytes()))
result={"author":"Codex / Tester","tested_sha":PIN,"branch":"test/ui-chart-wheel","verdict":"FAIL_EFFECTIVE_H44",
"confirmed_findings":["TEST-FIND-WHEEL-004"],"existing_requirement_gap":"TEST-FIND-WHEEL-002 OPEN",
"regression":{"node_target":39,"node_all_ui":227,"python_target":53,"python_http_api":300,"python_full":2959,"known_skips":1,"sets_nested":True},
"native":{"cases":27,"checks":555,"pass":528,"raw_fail":27,"unique_effective44_defects":1,"native_numeric_gap_indeterminate_cases":3,"lifecycle_pass":3},
"target_proofs":3,"independent_calibration":{"positive44":3,"negative43":3},"viewport_height_pass":6,
"docs":{"documents":4,"links":links,"tables":tables,"anchors":"VALID"},"index":"EMPTY","foreign_production_delta":"NONE","stashes":"PRESERVED",
"historical_evidence":"NOT_REWRITTEN; original Tester payloads protected except explicitly updated index/defects/coverage",
"payloads_sha256_lf_or_raw_png":payloads,"changed_paths":len(scope),"scope":"pinned TestedSHA to checkout plus worktree",
"publication":{"authorization":"Owner separately requested commit/push to test then merge into change",
"pre_authorization_snapshot":"NOT_PERFORMED_CURRENT_TASK",
"source_sha_resolver":"git log --reverse --format=%H -G '^### Публикация runtime-тестирования — 2026-10-20$' -- docs/project_management/change_plans/ui-chart-wheel/tester_artifact.md (first line)",
"change_before_integration":"3c2744ee2ecfe64ebe1d2f5b306a23d008d5064d",
"later_change_delta_paths":29,"later_change_runtime_retest":"NOT_RUN; original TestedSHA and results unchanged",
"verification":"Verify remote refs, merge parents/tree, preserved later change paths, SourceSHA ancestry and clean role worktree; report actual SHAs to Owner"}}
if "--write" in sys.argv:(HERE/"verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
else:assert load("verification.json")==result,"Evidence changed after verification; inspect before updating"
print("TESTER_EVIDENCE_OK sources="+str(len(sources))+" logs=5 historical=PROTECTED")
print("TESTER_NATIVE_VERIFIED cases=27 checks=555 pass=528 raw_fail=27 target_defects=1 gap_indeterminate=3 lifecycle=3/3")
print("TESTER_TARGET_CONTROL_OK proofs=3 positive44=3 negative43=3 viewport=6/6")
print("TESTER_DOCS_OK "+json.dumps(result["docs"])+" payload_hashes="+str(len(payloads)))
print("TESTER_SCOPE_OK TestedSHA="+PIN+" index=EMPTY foreign_delta=NONE stashes=PRESERVED publication=SEPARATELY_AUTHORIZED")
