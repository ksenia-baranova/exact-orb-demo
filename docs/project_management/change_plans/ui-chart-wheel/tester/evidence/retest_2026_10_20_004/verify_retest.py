"""Verify only the new independent retest; historical payloads stay at recorded SHAs."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
from urllib.parse import unquote
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/".git").exists())
R="docs/project_management/change_plans/ui-chart-wheel/"
PIN="99741958b4bbee8884505920f4a02f2f19dea3e3"
DOCS=[R+"tester_artifact.md",R+"tester/defects.md",R+"tester/coverage_matrix.md",R+"tester/retest_2026_10_20_004.md"]
OUT=HERE/"verification.json"
def git(*args):return subprocess.check_output(["git","-C",str(ROOT),*args])
def lf(b):return b.replace(b"\r\n",b"\n")
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((HERE/p).read_text(encoding="utf8"))
def blob(p,ref=PIN):return git("show",ref+":"+p)
git("merge-base","--is-ancestor",PIN,"HEAD")
assert git("branch","--show-current").decode().strip()=="test/ui-chart-wheel"
assert not git("diff","--cached","--name-only").strip()
prefix=HERE.relative_to(ROOT).as_posix()+"/";allowed=set(DOCS)
paths={line[3:] for line in git("status","--porcelain","--untracked-files=all").decode("utf8").splitlines()}
paths.update(git("diff","--name-only",PIN,"HEAD").decode("utf8").splitlines())
paths.add(prefix+"verification.json")
assert all(p in allowed or p.startswith(prefix) for p in paths),paths
assert not git("diff","--name-only","--","src","tests","pyproject.toml","AGENTS.md","docs/development_approach",R+"developer",R+"analyst",R+"manager_artifact.md").strip()
stashes=git("stash","list","--format=%H").decode()
assert all(x in stashes for x in ["0c2eb3ba6e9b6d191830da6a0d1c132a34762679","d936068b2806107cbe21499538b4f038780cc7fb"])
protected=0
for p in git("ls-tree","-r","--name-only",PIN,"--",R+"tester").decode().splitlines():
 if p in allowed:continue
 actual=(ROOT/p).read_bytes();expected=blob(p)
 assert (actual==expected if p.endswith((".png",".log",".gz")) else lf(actual)==lf(expected)),p
 protected+=1
assert lf((ROOT/(R+"tester_artifact.md")).read_bytes()).startswith(lf(blob(R+"tester_artifact.md")))
suites=load("suites.json")
assert suites["tested_sha"]==PIN and suites["head_after"]==PIN and not suites["production_delta_after"]
assert len(suites["commands"])==4 and all(c["exit_code"]==0 for c in suites["commands"])
tokens={"node_target":"# pass 41","python_target":"53 passed","node_all_ui":"# pass 229","python_full":"2959 passed, 1 skipped"}
for c in suites["commands"]:
 data=(HERE/c["log"]).read_bytes();assert sha(data)==c["log_sha256"] and tokens[c["name"]].encode() in data
sources=suites["source_sha256_lf"]
assert len(sources)==14
for p,h in sources.items():assert sha(lf((ROOT/p).read_bytes()))==h==sha(lf(blob(p))),p
native_sources={Path(p).name:h for p,h in sources.items()}
old_css_sha=sha(lf(blob("src/exact_orb/http_api/ui/styles.css","3b95934c884caa9f40ea70e935991457058b87b9")))
style_sha=sources["src/exact_orb/http_api/ui/styles.css"]
assert style_sha=="e4b4539fbe051e66c9f8226bc6834828e925eb3b12aea6f93e6fdfa20d53bfec"
executions=[]
for script,folder,exit_code in [
 ("native_retest.cjs","red01",1),("native_retest_v2.cjs","red02",1),
 ("native_retest_v2.cjs","green01",1),("native_retest_v3.cjs","red03",1),
 ("native_retest_v3.cjs","green02",0)]:
 d=load(folder+"/actual.json")
 assert d["retested_sha"]==PIN and not d.get("fatal") and d["source_sha256_lf"]==native_sources
 assert d["served_css_sha256_lf"]==(old_css_sha if d["old_css_sensitivity"] else style_sha)
 assert bool(d["summary"]["failed"])==(exit_code!=0)
 executions.append({"script":prefix+script,"output":prefix+folder+"/actual.json","old_css":d["old_css_sensitivity"],
  "exit_code":exit_code,"cases":d["summary"]["cases"],"checks":d["summary"]["checks"],"failures":len(d["summary"]["failed"]),
  "started_utc":d["started_utc"],"finished_utc":d["finished_utc"]})
green=load("green02/actual.json");summary=green["summary"]
assert summary["cases"]==summary["passed"]==6 and summary["checks"]==672 and not summary["failed"]
assert summary["normalControls"]==372 and summary["selectedControls"]==36
assert {(r["vendor"],r["width"]) for r in green["cases"]}=={(v,w) for v in ["Chrome","Yandex"] for w in [1440,768,360]}
for r in green["cases"]:
 assert r["pass"] and not r["errors"] and len(r["checks"])==112 and len(r["controls"])==62
 assert len(r["pointerEvents"])==5 and all(e["trusted"] for e in r["pointerEvents"])
 assert len(r["selectedControls"])==6
 assert sum(v["path"]=="build" for v in r["requests"])==1
 assert not r["compactness"]["overflow"]
 if r["width"]>700:assert r["compactness"]["row"]==55
 for m in [*r["controls"],*r["selectedControls"]]:
  assert m["pass"] and m["certificate"] and m["native"] and m["shape"]
  assert m["hits"]==m["probes"]==121 and not m["unsupported"] and not m["clips"] and not m["partitionFailures"]
  assert m["radii"]==["0px"]*4 and m["box"]["width"]>=46 and m["box"]["height"]>=46 and m["q"]["size"]==44
  q,b=m["q"],m["box"]
  assert q["left"]>=b["left"]+1 and q["top"]>=b["top"]+1 and q["right"]<=b["left"]+b["width"]-1 and q["bottom"]<=b["top"]+b["height"]-1
 cal=r["calibration"];assert cal["positive"]["pass"] and cal["restored"]["pass"]
 assert all(not cal[k]["pass"] for k in ["negative43","overlay","clip43","thinOverlay"])
 assert cal["thinOverlay"]["native"] and not cal["thinOverlay"]["certificate"] and cal["thinOverlay"]["partitionFailures"]
 after=r["acceptance"]["after"]
 assert after["points"]==after["houses"]==5 and after["sun"]=="false"
 assert after["editorHidden"]==(r["width"]!=1440)
 assert "1990-01-01" in after["summary"] and "15:45" in after["summary"]
red=load("red03/actual.json")
assert len(red["summary"]["failed"])==53
assert any(c["id"]=="H44 Солнце" and not c["pass"] for c in red["cases"][0]["checks"])
assert all(c["pass"] for c in red["cases"][0]["checks"] if "calibration" in c["id"] or "overlay" in c["id"])
replay=load("probe02/actual.json")
assert replay["tested_sha"]==PIN and replay["sources"]==native_sources and len(replay["cases"])==3 and not replay.get("fatal")
for r in replay["cases"]:
 assert r["measure"]["box"]["height"]==46 and r["measure"]["radius"]=="0px" and r["calibrationPass"]
 assert r["positiveCenterSelected"]=="true" and r["afterCornerSelected"]=="false" and len(r["events"])==2 and all(e["trusted"] for e in r["events"])
 assert r["proof"].startswith("Legacy necessary-condition")
fixture_paths=[R+"developer/evidence/column_full_composition_v1/data.json","tests/http_api/golden/session_view.json"]
fixture_hashes={}
for p in fixture_paths:
 assert lf((ROOT/p).read_bytes())==lf(blob(p));fixture_hashes[p]=sha(lf(blob(p)))
def anchors(text):
 out=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
 for h in re.findall(r"^#{1,6}\s+(.+)$",text,re.M):
  h=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",h);slug=re.sub(r"\s","-",re.sub(r"[^\w\s-]","",h.lower()))
  i=counts.get(slug,0);counts[slug]=i+1;out.add(slug if i==0 else slug+"-"+str(i))
 return out
links=tables=0
for p in DOCS:
 text=(ROOT/p).read_text(encoding="utf8")
 assert text.endswith("\n") and not text.endswith("\n\n") and all(l==l.rstrip() for l in text.splitlines()),p
 columns=None
 for line in text.splitlines():
  if line.startswith("|"):
   n=len(re.split(r"(?<!\\)\|",line))
   if columns is None:tables+=1
   assert columns is None or n==columns,(p,line)
   columns=n
  else:columns=None
 for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",text):
  if re.match(r"^[A-Za-z]+:",dest):continue
  part,_,anchor=unquote(dest).partition("#");target=((ROOT/p).parent/part).resolve() if part else ROOT/p
  assert target.exists() or ("--write" in sys.argv and target==OUT),(p,dest)
  if anchor and target.suffix==".md":assert anchor in anchors(target.read_text(encoding="utf8")),(p,dest)
  links+=1
defects=(ROOT/(R+"tester/defects.md")).read_text(encoding="utf8")
section=defects.split('## TEST-FIND-WHEEL-004.',1)[1]
assert "CLOSED / независимый retest9974195 PASS" in section
assert "| P2, PROPOSED | CLOSED | Нет по004" in defects
assert "**Статус:** OPEN." in defects.split("## TEST-FIND-WHEEL-002.",1)[1].split("## TEST-FIND-WHEEL-003.",1)[0]
payloads={p.relative_to(ROOT).as_posix():sha(p.read_bytes() if p.suffix in (".png",".log") else lf(p.read_bytes()))
 for p in sorted(HERE.rglob("*")) if p.is_file() and p!=OUT}
for p in DOCS:payloads[p]=sha(lf((ROOT/p).read_bytes()))
result={"author":"Codex / Tester","retested_sha":PIN,"finding":"TEST-FIND-WHEEL-004","status":"CLOSED / RETEST_PASS",
"first_five":"PASS in tested six native cases; other scope unchanged","source_sha256_lf":sources,"fixture_sha256_lf":fixture_hashes,
"regression":{"target_node":41,"all_ui_node":229,"target_python":53,"full_pytest":2959,"known_skips":1,"sets_nested":True},
"native":{"cases":6,"checks":672,"failed":0,"normal_controls":372,"selected_controls":36,"native_grid_per_record":121,
"trusted_pointer":30,"keyboard_activations":12,"paired_controls_per_case":6,"old_css_sensitivity":"RED_EXPECTED_53_FAILURES; hybrid old CSS/current modules; calibrations reached",
"versions":{r["vendor"]:r["version"] for r in green["cases"]}},
"browser_executions":executions,"legacy_replay":"3/3 new metadata; diagnostic possible44 is not a certificate",
"remaining":"TEST-FIND-WHEEL-002 OPEN; native gap2 precision INDETERMINATE; radial/whole geometry not certified",
"docs":{"documents":4,"links":links,"tables":tables,"anchors":"VALID"},"historical_protected_files":protected,
"index":"EMPTY","foreign_worktree_delta":"NONE","stashes":"PRESERVED",
"publication":{"owner_authorization":"2026-10-21: commit/push test then merge change",
"audit_phase":"PACKAGE_PRE_STAGING; actual push/merge verified separately after execution",
"fetched_change_base":PIN,"fetched_test_base":"1cfbe3156761da1cfba1ef66133febd7c7bae265",
"source_sha_resolver":"first git log --reverse --format=%H -G '^### Публикация ретеста004 — 2026-10-21$' -- "+R+"tester_artifact.md"},
"scope_paths":len(paths),"payload_sha256_lf_text_raw_logs_png":payloads}
if "--write" in sys.argv:OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
else:assert load("verification.json")==result,"New retest snapshot changed; inspect before regeneration"
print("RETEST_004_SOURCE_OK sha="+PIN+" UI=14 fixtures=2 protected="+str(protected)+" logs=4")
print("RETEST_004_NATIVE_OK cases=6/6 checks=672/672 normal=372 selected=36 pointer=30 keyboard=12 calibrations=PASS")
print("RETEST_004_RED_OK oldCSS=EXPECTED_FAIL calibrations=REACHED legacy_replay=3/3")
print("RETEST_004_DOCS_OK "+json.dumps(result["docs"])+" payloads="+str(len(payloads)))
print("RETEST_004_FINAL_OK CLOSED first_five=PASS 002=OPEN gap_precision=INDETERMINATE index=EMPTY foreign=NONE stash=PRESERVED publication_audit=PRE_STAGING")
