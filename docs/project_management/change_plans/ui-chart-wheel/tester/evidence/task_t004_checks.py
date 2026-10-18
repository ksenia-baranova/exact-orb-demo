"""TASK-T-004: independent read-only audit of pinned D003 evidence.
No renderer/placement imports; archived outputs never rewritten. New snapshots and
unmodified replay sources may be written ONLY below tester/evidence/task_t004_*.
"""
from pathlib import Path
from functools import cache
from itertools import combinations,product
from collections import Counter
from datetime import datetime
import hashlib,json,math,re,struct,subprocess,sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/".git").exists())
R="docs/project_management/change_plans/ui-chart-wheel/"
E=R+"developer/evidence/task_d003_research/"
OWN=R+"tester/evidence/task_t004_"
PINS={"head":"f6c555c39e3371c8ed925b980cd0ce480e521dbf",
"review_input":"030826fd4e6bfa9613ad84ba7ed32adc15fddcd9",
"package":"d24a24e04be32d0522674735388e9d2ea3e65c93",
"developer_input":"8fb25770169166a3a4e94110eee684bd8b116474",
"criteria":"f6f289cda25e7f228dff064175805130cc770b63",
"analyst":"2634b224894b1046113557bfe241f0a5f2d46f8c",
"main":"535551026af6eedaf2a0aa5c0daa96fa94655ec1"}
lf=lambda b:b.replace(b"\r\n",b"\n")
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(["git","-C",str(ROOT),*args])
@cache
def blob(ref,path):return git("show",ref+":"+path)
def read(p):return (ROOT/p).read_bytes()
def load(p):return json.loads(read(p).decode("utf-8"))
def gl(p):return json.loads(blob(PINS["package"],E+p))
def hash_encoding(data,h):
 if sha(lf(data))==h:return "LF"
 if sha(lf(data).replace(b"\n",b"\r\n"))==h:return "CRLF"
 raise AssertionError(("source hash mismatch",h))
def close(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8)
# close() checks arithmetic/serialized record agreement only. Criterion decisions
# below use the original 0.5/2/16/12/44 values, with no added drawing tolerance.
def separation(a,b):
 total=0
 for lo,hi in (("left","right"),("top","bottom")):
  if a[hi]<b[lo]:total+=(b[lo]-a[hi])**2
  elif b[hi]<a[lo]:total+=(a[lo]-b[hi])**2
 return math.sqrt(total)
def ugap(a,b):return min(separation(x,y) for x in a for y in b)
def move(boxes,p):return [{k:v+p["x" if k in ("left","right") else "y"] for k,v in b.items()} for b in boxes]
def overlap(a,b):return min(a["right"],b["right"])>max(a["left"],b["left"]) and min(a["bottom"],b["bottom"])>max(a["top"],b["top"])
def ring_margin(b,C,ring):
 nearest=separation(b,dict(left=C[0],right=C[0],top=C[1],bottom=C[1]))
 farthest=max(math.dist((x,y),C) for x,y in product((b["left"],b["right"]),(b["top"],b["bottom"])))
 return min(nearest-ring["inner"],ring["outer"]-farthest)
def group_margins(g,boxes,m):
 other=[h["boxes"] for h in m["groups"] if h["key"]!=g["key"]]+[h["boxes"] for h in m["obstacles"]]
 vals=[ugap(boxes,b)-2 for b in other]
 for b in boxes:
  vals += [ring_margin(b,m["frame"]["C"],m["frame"][g["kind"]]),
   b["left"],b["top"],m["frame"]["size"]-b["right"],m["frame"]["size"]-b["bottom"]]
 return vals
def cyclic(groups,field,kind):
 seq=sorted([g for g in groups if g["kind"]==kind],key=lambda g:(g[field]%(2*math.pi),g["index"]))
 return [g["key"] for g in seq]
def same_cycle(a,b):
 return not a or any(a==b[k:]+b[:k] for k in range(len(b)))
def diffs(a,b,p=""):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return [z for k in sorted(a.keys()|b.keys()) for z in (diffs(a[k],b[k],p+"/"+k) if k in a and k in b else [p+"/"+k])]
 if isinstance(a,list):return [z for i,(x,y) in enumerate(zip(a,b)) for z in diffs(x,y,p+"/"+str(i))]+([p+"/length"] if len(a)!=len(b) else [])
 return [] if a==b else [p]

def package_audit():
 assert git("branch","--show-current").decode().strip()=="test/ui-chart-wheel"
 # The recorded review baseline stays pinned after its Tester-only publication.
 git("merge-base","--is-ancestor",PINS["head"],"HEAD")
 for p in PINS.values():git("merge-base","--is-ancestor",p,PINS["head"])
 assert set(git("show","-s","--format=%P",PINS["review_input"]).decode().split())=={PINS["developer_input"],PINS["package"]}
 assert git("show","-s","--format=%P",PINS["head"]).decode().strip()==PINS["review_input"]
 manifest=gl("package_manifest.json");entries=manifest["files"];assert len(entries)==164
 for e in entries:
  p=e["path"];data=blob(PINS["package"],p)
  canonical=data if p.endswith(".png") else lf(data)
  assert sha(canonical)==e["sha256_lf_or_binary"],p
  assert (read(p) if p.endswith(".png") else lf(read(p)))==canonical,p
 scope=set(git("diff","--name-only",PINS["developer_input"],PINS["package"]).decode().splitlines())
 assert scope=={x["path"] for x in entries}|{E+"package_manifest.json"} and len(scope)==165
 shared=["src","tests","docs/requirements","docs/sequence_diagrams","docs/development_approach","pyproject.toml","AGENTS.md"]
 assert not git("diff","--name-only",PINS["main"],PINS["head"],"--",*shared).strip()
 inp=gl("inputs_manifest_v2.json");encodings={}
 for p,h in inp["sources"].items():
  encodings[p]=hash_encoding(blob(PINS["developer_input"],p),h)
 for p,h in inp["inputs"].items():encodings[p]=hash_encoding(blob(PINS["package"],E+p),h)
 fixtures=gl("fixtures_v2.json");v1=gl("fixtures.json");spec=gl("experiment_spec_v2.json");spec1=gl("experiment_spec.json")
 delta=diffs(v1,fixtures)
 assert all(p.startswith("/F3/angles/") or p.startswith("/F3-max/angles/") for p in delta)
 assert fixtures["F3"]["angles"]==fixtures["F1"]["angles"]
 a=fixtures["F3-max"]["angles"];assert close((a["asc"]["longitude"]+180)%360,a["dsc"]["longitude"]) and close((a["mc"]["longitude"]+180)%360,a["ic"]["longitude"])
 assert all(p in ["/schema","/fixture_correction","/recorded_before_first_matrix_run_utc"] for p in diffs(spec1,spec))
 # Source snapshots differ only by input filenames and the output namespace.
 for before,after in [("run02/source_harness.mjs","harness.mjs"),("run02/source_run_browser.cjs","run_browser.cjs")]:
  b=lf(blob(PINS["package"],E+before)).decode()
  for old,new in [("fixtures.json","fixtures_v2.json"),("experiment_spec.json","experiment_spec_v2.json"),("inputs_manifest.json","inputs_manifest_v2.json"),("??'run02'","??'run03'")]:b=b.replace(old,new)
  assert b==lf(blob(PINS["package"],E+after)).decode(),after
 assert spec["font_point"]==16 and spec["font_aux"]==12 and spec["hit_css"]==44 and spec["gap_css"]==2 and spec["anchor_error_css"]==.5 and spec["return_probe_css"]==1
 f1=json.loads(blob(PINS["developer_input"],"tests/ui/fixtures/natal_1985_chart_dto.json"))
 assert fixtures["F1"]==f1
 ids=spec["ids"];assert len(ids)==len(set(ids))==16
 for f in fixtures.values():assert [p["id"] for p in f["points"]]==ids
 for id,lng in zip(["mercury","venus","mars","jupiter","saturn"],[359.7,359.85,0,.15,.3]):
  p=next(p for p in fixtures["F3"]["points"] if p["id"]==id);assert p["retrograde"] and p["longitude"]==lng
 # All previous Tester payload and its index prefix remain untouched.
 old=git("ls-tree","-r","--name-only",PINS["head"],"--",R+"tester").decode().splitlines()
 for p in old:assert lf(read(p))==lf(blob(PINS["head"],p)),p
 index=R+"tester_artifact.md";assert lf(read(index)).startswith(lf(blob(PINS["head"],index)))
 return {"manifest_payloads":len(entries),"package_scope":len(scope),"source_hashes":len(inp["sources"]),
 "input_hash_encodings":dict(Counter(encodings.values())),"previous_tester_files":len(old),
 "previous_index_prefix_sha256_lf":sha(lf(blob(PINS["head"],index))),"fixture_delta":delta,
 "spec_delta":diffs(spec1,spec),"shared_contract_code_tests":"UNCHANGED"}

def matrix_audit():
 idx=gl("run03/browser_matrix.json");refs=idx["records"]
 expected=set(product(["sparse","F1","F3","F3-max"],[1440,768,360],["default","candidate"]))
 assert len(refs)==24 and {(r["name"],r["viewport"],r["layout"]) for r in refs}==expected
 spec=gl("experiment_spec_v2.json");fixtures=gl("fixtures_v2.json");rows=[];maxerr=0;shots=set();platform=Counter();saved={}
 for p,h in idx["meta"]["inputs_sha256"].items():hash_encoding(blob(PINS["package"],E+p),h)
 assert datetime.fromisoformat(spec["recorded_before_first_matrix_run_utc"])<datetime.fromisoformat(idx["meta"]["started"].replace("Z","+00:00"))
 for ref in refs:
  path=E+"run03/"+ref["file"];assert sha(lf(blob(PINS["package"],path)))==ref["sha256"]
  d=load(path);m=d["measurement"];v=d["verifier"];gs=m["groups"];dto=fixtures[d["name"]];frame=spec["frames"][str(d["viewport"])]
  saved[d["name"],d["viewport"],d["layout"]]=d
  assert m["frame"]==frame and m["zoom"]==m["dpr"]==1 and m["unchanged"]
  assert m["matrix"][:4]==[1,0,0,1]
  assert len({g["key"] for g in gs})==len(gs)
  longs={p["id"]:p["longitude"] for p in dto["points"]}|{k:p["longitude"] for k,p in (dto["angles"] or {}).items()}
  expkeys=[p["id"] for p in dto["points"]]
  for a in dto["aspects"]:
   if a["category"]!="background" and a["type"]=="conjunction":
    key=json.dumps([a["from"],a["to"],a["type"]],separators=(",",":"));expkeys.append(key)
    diff=(longs[a["to"]]-longs[a["from"]]+180)%360-180
    if diff==-180:diff=180
    longs[key]=longs[a["from"]]+diff/2
  assert [g["key"] for g in gs]==expkeys
  origin=dto["angles"]["asc"]["longitude"] if dto["kind"]=="natal" else 0
  C=frame["C"];M=m["matrix"]
  c0=[];movable_ok=True;metrics=0
  for g in gs:
   theta=math.radians(longs[g["key"]]-origin);r=frame[g["kind"]]["r"]
   A={"x":C[0]-r*math.cos(theta),"y":C[1]+r*math.sin(theta)}
   ex=(M[0]*A["x"]+M[2]*A["y"]+M[4],M[1]*A["x"]+M[3]*A["y"]+M[5])
   err=math.dist(ex,(g["anchorCSS"]["x"],g["anchorCSS"]["y"]));maxerr=max(maxerr,err)
   assert err<=.5 and close(A["x"],g["default"]["x"]) and close(A["y"],g["default"]["y"])
   for component,b in zip(move(g["components"],g["p"]),g["boxes"]):assert all(close(component[k],b[k]) for k in b)
   for component,b in zip(move(g["components"],g["default"]),g["defaultBoxes"]):assert all(close(component[k],b[k]) for k in b)
   other=[h["defaultBoxes"] for h in gs if h["key"]!=g["key"]]+[h["boxes"] for h in m["obstacles"]]
   if any(ugap(g["defaultBoxes"],h)<2 for h in other):c0.append(g["key"])
   for t in g["metrics"]:
    em=math.hypot(M[2]*t["size"],M[3]*t["size"]);assert em>=(16 if t["id"].startswith("glyph-") else 12);metrics+=1
   inks=[t["ink"] for t in g["metrics"]]
   focus={"left":min(b["left"] for b in inks)-3,"top":min(b["top"] for b in inks)-3,"right":max(b["right"] for b in inks)+3,"bottom":max(b["bottom"] for b in inks)+3}
   assert all(close(focus[k],g["components"][-1][k]) for k in focus)
   # Actual CSS focus outline paint: envelope expanded 2, stroke width 2.
   # Its component AABB also encloses every selected glyph stroke (0.75).
   assert all(focus["left"]<=b["left"]-.75 and focus["top"]<=b["top"]-.75 and focus["right"]>=b["right"]+.75 and focus["bottom"]>=b["bottom"]+.75 for b in inks)
   if min(group_margins(g,g["boxes"],m))<0:movable_ok=False
   if not g["C0"] and g["delta"]!=0:movable_ok=False
   if g["leader"]!=(g["delta"]!=0):movable_ok=False
  assert c0==v["C0"] and all(g["C0"]==(g["key"] in c0) for g in gs)
  order={kind:same_cycle(cyclic(gs,"defaultTheta",kind),cyclic(gs,"theta",kind)) for kind in ["point","marker"]}
  if not all(order.values()):movable_ok=False
  assert movable_ok==v["geometryPass"],(path,movable_ok,v["geometryPass"])
  fixed=[{"keys":[a["key"],b["key"]],"gap":ugap(a["boxes"],b["boxes"])} for a,b in combinations(m["obstacles"],2) if ugap(a["boxes"],b["boxes"])<2]
  hit=wrong=probes=0;before=(m["selected"] or {}).get("key")
  for i,(g,h) in enumerate(zip(gs,v["hit"])):
   q=g["hit"];assert q==h["Q"] and h["key"]==g["key"]
   blocked=any(overlap(q,o["hit"]) for o in gs[i+1:])
   clipped=q["left"]<0 or q["top"]<0 or q["right"]>frame["size"] or q["bottom"]>frame["size"]
   passed=not blocked and not clipped;hit+=passed;assert passed==(h["certificate"]=="RECT_CONTAINMENT_PASS")
   for s in h["sampling"]:
    delivered=s["delivered"];actual=(s["selected"] or {}).get("key")
    owner=delivered.get("owner")==g["key"];outcome=actual==(None if before==g["key"] else g["key"])
    assert owner==s["correctOwner"] and outcome==s["correctOutcome"]
    assert delivered["trusted"];wrong+=not owner or not outcome;probes+=1;before=actual
  keyboard=[k for k in d["keyboard"] if "activation" in k];keyfail=[]
  assert [k["key"] for k in keyboard]==[g["key"] for g in gs]
  for k in keyboard:
   a=k["activation"];b=(a["before"]["selected"] or {}).get("key");x=(a["after"]["selected"] or {}).get("key");y=(a["toggle"]["selected"] or {}).get("key")
   ex=None if b==k["key"] else k["key"];ex2=k["key"] if ex is None else None
   ok=x==ex and y==ex2 and k["connected"] and k["visible"]
   ok=ok and all(a[z]["connected"] and a[z]["active"]==k["id"] for z in ["after","toggle"])
   ok=ok and a["before"]["calls"]==a["after"]["calls"]==a["toggle"]["calls"] and a["before"]["scroll"]==a["after"]["scroll"]==a["toggle"]["scroll"]
   if not ok:keyfail.append(k["key"])
  shot=E+"run03/"+d["screenshot"];raw=blob(PINS["package"],shot)
  assert sha(raw)==d["screenshot_sha256"] and raw[:8]==b"\x89PNG\r\n\x1a\n"
  assert struct.unpack(">II",raw[16:24])==(frame["size"],frame["size"]);shots.add(shot)
  for f in d["platformFonts"]:
   assert f["fonts"] and sum(x["glyphCount"] for x in f["fonts"])>0
   platform.update(x["familyName"] for x in f["fonts"])
  if d["name"]=="sparse":assert not c0 and all(g["delta"]==0 and not g["leader"] for g in gs)
  rows.append({"fixture":d["name"],"viewport":d["viewport"],"layout":d["layout"],"record":path,
   "C0":len(c0),"moved":sum(g["delta"]!=0 for g in gs),"movable_geometry":movable_ok,
   "fixed_collisions":fixed,"complete_geometry":movable_ok and not fixed,"order":order,
   "hit_certified":hit,"targets":len(gs),"native_wrong":wrong,"native_probes":probes,
   "keyboard_targets":len(keyboard),"keyboard_failed":len(keyfail),"font_runs":metrics,"screenshot":shot})
 allshots=git("ls-tree","-r","--name-only",PINS["package"],"--",E+"run03/screenshots").decode().splitlines()
 assert len(allshots)==25 and len(shots)==24 and E+"run03/screenshots/lifecycle-focus.png" in allshots
 totals={k:sum(r[field] for r in rows) for k,field in [("native_probes","native_probes"),("native_wrong","native_wrong"),("keyboard_targets","keyboard_targets"),("keyboard_failed","keyboard_failed"),("complete_geometry_cells","complete_geometry")]}
 totals["cells"]=len(rows);assert totals=={k:v for k,v in gl("drawing_audit_v2.json")["totals"].items() if k!="full_matrix_pass"}
 assert totals==dict(native_probes=7446,native_wrong=1679,keyboard_targets=438,keyboard_failed=0,complete_geometry_cells=6,cells=24)
 witness=load(E+"run03/F3-max-1440-candidate.json");m=witness["measurement"];g=next(g for g in m["groups"] if g["key"]=="sun")
 t=.25;start=min(group_margins(g,g["boxes"],m));angle=g["theta"]-math.copysign(t/g["r"],g["delta"])
 P={"x":m["frame"]["C"][0]-g["r"]*math.cos(angle),"y":m["frame"]["C"][1]+g["r"]*math.sin(angle)}
 end=min(group_margins(g,move(g["components"],P),m))
 direction=-1 if g["delta"]>0 else 1
 order_distance=min(((direction*(h["theta"]-g["theta"]))%(2*math.pi))*g["r"] for h in m["groups"] if h["kind"]==g["kind"] and h["key"]!=g["key"])
 assert start>t and end>0 and order_distance>t
 post=gl("return_probe_audit.json")["records"]
 for rec in post:
  data=saved[rec["fixture"],rec["viewport"],rec["layout"]];mm=data["measurement"];gg=next(g for g in mm["groups"] if g["key"]==rec["key"])
  arc=abs(gg["delta"])*gg["r"];step=min(1,arc);aa=gg["theta"]-math.copysign(step/gg["r"],gg["delta"])
  qp={"x":mm["frame"]["C"][0]-gg["r"]*math.cos(aa),"y":mm["frame"]["C"][1]+gg["r"]*math.sin(aa)}
  sm=min(group_margins(gg,gg["boxes"],mm));em=min(group_margins(gg,move(gg["components"],qp),mm))
  order_ok=all(same_cycle(cyclic(mm["groups"],"defaultTheta",kind),cyclic(mm["groups"],"theta",kind)) for kind in ["point","marker"])
  verdict="CANDIDATE_INADMISSIBLE" if sm<0 else "LOCAL_STEP_PASS_ENDPOINT_VIOLATION" if em<0 else "LOCAL_STEP_FAIL_PREFIX_CERTIFIED" if sm>step and order_ok else "FULL_PREFIX_UNPROVEN"
  assert verdict==rec["verdict"] and close(sm,rec["start_min_margin"]) and close(em,rec["endpoint_min_margin"]),rec["key"]
 assert len(post)==127
 return {"totals":totals,"screenshots":len(allshots),"anchor_error_max":maxerr,"platform_fonts":dict(platform),"matrix":rows,
 "local_witness":{"fixture":"F3-max","viewport":1440,"key":"sun","return_css":t,"start_margin":start,"end_margin":end,
 "nearest_reference_crossing_distance":order_distance,"arc_displacement":abs(g["delta"])*g["r"],
 "scope":"one label, fixed measured component boxes; Lipschitz prefix bound; independent fixed-fixed violations remain, so no whole-map feasibility claim"},
 "return_post_audit_records":dict(Counter(x["verdict"] for x in post)),"return_post_audit_independently_recomputed":len(post)}

REPLAY_SOURCES=["source_audit.py","orientation_audit.py","source_controls.mjs","run_followup.cjs","lifecycle.html","fixtures.json"]
def prepare():
 target=ROOT/(OWN+"replay");target.mkdir(exist_ok=True)
 copied=[]
 for p in REPLAY_SOURCES:
  data=blob(PINS["package"],E+p);out=target/p
  if out.exists():assert out.read_bytes()==data,p
  else:out.write_bytes(data)
  copied.append({"source":E+p,"target":out.relative_to(ROOT).as_posix(),"sha256":sha(data)})
 meta={"package_sha":PINS["package"],"purpose":"fresh selective source/followup replay; not archived run03 or a new layout","copies_unmodified":copied}
 (target/"provenance.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("TASK_T004_REPLAY_PREPARED sources=6 unmodified Git blobs; output namespace tester/evidence/task_t004_replay")


def replay_audit():
 base=OWN+"replay/"
 provenance=load(base+"provenance.json");execution=load(base+"execution.json")
 assert provenance["package_sha"]==PINS["package"] and execution["actual_checkout_head"]==PINS["head"]
 for e in provenance["copies_unmodified"]:assert lf(read(e["target"]))==lf(blob(PINS["package"],e["source"])) and sha(lf(read(e["target"])))==e["sha256"]
 for command in execution["commands"]:assert command["exit_code"]==0
 paths=["source_audit.json","orientation_audit.json","source_controls.json","followup02/controls.json"]
 for p in paths:assert load(base+p)==gl(p),p
 src={r["id"]:r for r in load(base+"source_audit.json")["records"]}
 for kind,n in [("natal",46),("cosmogram",13)]:
  normal=src["G02-"+kind+"-codec-projector"];duplicate=src["G02-"+kind+"-duplicate-restore"]
  assert normal["round_trip_exact"] and normal["aspects"]==normal["unique_directed"]==normal["unique_undirected"]==n
  assert duplicate["accepted_by_current_codec_projector"] and duplicate["rows"]==n+1 and duplicate["unique"]==n
 assert src["G02-natal-codec-projector"]["nonlexical_direction"]==28 and src["G02-natal-codec-projector"]["angle_endpoints"]==15
 assert src["G02-cosmogram-codec-projector"]["angle_endpoints"]==0
 orientation=load(base+"orientation_audit.json");assert len(orientation)==4
 assert all(r["accepted"]==(r["configs"]=="empty") for r in orientation)
 controls=load(base+"source_controls.json")["records"];ctl={r["id"]:r for r in controls}
 for key,want in [("G03-source-build-repeats",3),("G03-no-extra-post-from-publish",1),
  ("G03-submitted-snapshot","14:30"),("G03-summary-not-late-draft","14:30"),("G03-late-draft","15:45"),
  ("G03-recovery-is-current","current"),("G03-fresh-birth-match","matched")]:
  assert ctl[key]["actual"]==want
 actual_count=sum(r["level"].startswith("actual ") for r in controls)
 assert actual_count==8 and len(controls)==26
 follow=load(base+"followup02/controls.json");f=follow["records"];assert len(f)==6
 a,b,c=f[0]["actual"],f[1]["actual"],f[2]["actual"]
 assert a["selected"]=="sun" and b["identity"]==b["summary"]=="controlled-B-confirmed"
 assert "sun12.251215Ariesfalse" in b["point"] and "2.75" in b["html"] and b["imageCount"]==0 and b["error"]
 assert any(t["event"]=="fault-hook" for t in b["trace"]) and any(t["event"]=="late-ignored" for t in b["trace"])
 assert c["imageCount"]==1 and c["selected"] is None and f[2]["inputUnchanged"]
 assert f[3]["actual"]=={"same":True,"connected":True,"selection":"sun"}
 sizes={t["id"]:t for t in f[4]["actual"]}
 for key,limit,want in [("t16",16,True),("tbelow",16,False),("t12",12,True),("tbelow12",12,False)]:
  rec=sizes[key];em=math.hypot(rec["M"][2]*rec["font"],rec["M"][3]*rec["font"]);assert (em>=limit)==want
 events=f[5]["actual"]
 assert any(x["type"]=="pointerdown" and x["x"]==304 and x["target"]!="bad" for x in events)
 assert any(x["type"]=="pointerdown" and x["x"]==299.5 and x["target"]=="good" for x in events)
 assert any(x["type"]=="click" and x["x"]==299 and x["target"]=="good" for x in events)
 matching_png=0
 for p in ["B-fault-html.png","B-alternate.png","clip-positive-negative.png"]:
  matching_png+=sha(read(base+"followup02/"+p))==sha(blob(PINS["package"],E+"followup02/"+p))
 assert matching_png==3
 browser=gl("run03/browser_controls.json")
 hit=browser["controls"];assert len(hit)==25
 for variant,x,want in [("solid44",22,True),("solid44",33,True),("without-overlay",33,True),
  ("narrow",22,True),("narrow",33,False),("overlay",22,True),("overlay",33,False),("clip43",43.5,False)]:
  record=next(r for r in hit if r["variant"]==variant and r["requested"]["x"]==x)
  assert (record["actual"]["target"]=="target")==want and record["actual"]["trusted"]
 focus=browser["focus"]
 assert focus["retained"]["same"] and focus["retained"]["connected"] and focus["retained"]["callsSince"]==0
 assert not focus["detach"]["oldConnected"] and focus["detach"]["active"]=="BODY"
 assert focus["clone"]["selected"]==focus["retained"]["selected"]
 assert focus["reconcile"]["connected"] and focus["reconcile"]["key"]=="sun"
 assert focus["collapse"]=={"active":"edit","editorHidden":True,"recoveryVisible":True}
 assert focus["recovery"]=={"kind":"recovery-get-model","post":0}
 stop=gl("experiment_stop.json");session=gl("research_session.json")
 elapsed=(datetime.fromisoformat(stop["stopped_utc"])-datetime.fromisoformat(stop["started_utc"])).total_seconds()/3600
 assert close(elapsed,stop["elapsed_hours_including_harness_data_repairs_measurements"]) and elapsed<=6
 assert session["budget_hours"]==[20,28]
 return {"fresh_replay_verified_utc":execution["verified_utc"],"environment":execution["environment"],
 "source_codec_records":8,"orientation_records":4,"coordinator_controls":26,"actual_component_records_in_coordinator_controls":8,
 "coordinator_models":17,"indistinguishability_arguments":1,"browser_followup_records":6,"screenshots":3,"screenshots_identical_to_archive":matching_png,
 "json_payloads_identical_to_archive":len(paths),"archived_hit_controls":len(hit),
 "archived_focus_control_scope":"retained/detach/same-key clone/reconcile/collapse; recovery callback is model, not HTTP",
 "experiment_elapsed_hours":elapsed,"session_elapsed_reported":session["current_session_elapsed_hours"],
 "execution_record":base+"execution.json","copied_sources":"6 unmodified Git blobs; replay has own namespace / actual HEAD"}

def anchors(text):
 out=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
 for h in re.findall(r"^#{1,6}\s+(.+)$",text,re.M):
  h=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",h);slug=re.sub(r"\s","-",re.sub(r"[^\w\s-]","",h.lower()))
  n=counts.get(slug,0);counts[slug]=n+1;out.add(slug if not n else slug+"-"+str(n))
 return out
def doc_audit():
 from urllib.parse import unquote
 paths=[R+"tester_artifact.md",R+"tester/task_t004_review.md"];links=tables=0
 for p in paths:
  text=lf(read(p)).decode();assert text.endswith("\n") and not text.endswith("\n\n")
  assert all(x==x.rstrip() for x in text.splitlines()),p
  cols=None
  for line in text.splitlines():
   if line.startswith("|"):
    n=len(re.split(r"(?<!\\)\|",line))
    if cols is None:tables+=1
    assert cols is None or cols==n,(p,line)
    cols=n
   else:cols=None
  for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",text):
   if re.match(r"^[A-Za-z]+:",dest):continue
   part,_,anchor=unquote(dest).partition("#");target=((ROOT/p).parent/part).resolve() if part else ROOT/p
   assert target.exists(),(p,dest)
   if anchor and target.suffix==".md":assert anchor in anchors(target.read_text(encoding="utf-8")),(p,dest)
   links+=1
 changed={line[3:] for line in git("status","--porcelain","--untracked-files=all").decode().splitlines()}
 changed.update(git("diff","--name-only",PINS["head"],"HEAD").decode().splitlines())
 assert all(p in paths or p.startswith(OWN) for p in changed),changed
 assert not git("diff","--cached","--name-only").strip()
 outputs={p:sha(read(p) if p.endswith(".png") else lf(read(p))) for p in changed if p!=OWN+"review.json"}
 return {"documents":2,"local_links":links,"tables":tables,"anchors":"VALID","changed_paths":len(changed),"scope":"pinned HEAD to checkout plus worktree","index":"EMPTY","output_sha256_lf_or_raw":outputs}

def run(write=False):
 inputs=package_audit();matrix=matrix_audit();replay=replay_audit()
 result={"task_id":"TASK-T-004","author":"Codex / Tester","pins":PINS,"input_audit":inputs,"archived_run03_independent_audit":matrix,
 "criterion_numbers_unchanged":[.5,2,1,16,12,44],"full_matrix_browser_replay":"NOT_RUN",
 "not_proven":["general curved-path verifier","whole-map feasibility","production integration/acceptance","global layout impossibility","new Owner fallback","full visual readability/touch"]}
 result.update({"started_utc":"2026-10-18T15:28:08Z","estimate_hours":[3,5],"confidence":"MEDIUM","target_workdays":1,"fresh_selective_replay":replay,
  "historical_evidence":"PINNED_SHA_LF_TEXT_RAW_PNG; originals not rewritten","publication":{
   "authorization":"Owner separately requested commit/push to test/ui-chart-wheel then merge into change/ui-chart-wheel",
   "pre_authorization_snapshot":{"commit":"NOT_CREATED","push":"NOT_RUN","pr":"NOT_CREATED"},
   "source_sha_resolver":"git log --reverse --format=%H -G '^### Публикация и интеграция review TASK-T-004$' -- docs/project_management/change_plans/ui-chart-wheel/tester_artifact.md (first line)",
   "verification":"Verify local and remote test SHA; normal Git merge preserves current change; verify SourceSHA ancestry, merge parents/tree, remote refs and clean worktree; report actual SHAs to Owner",
   "change_before_integration":"4057d6ed37b24e082a2a4089eb7104da80d17ee5",
   "change_delta_from_review_head":["docs/project_management/change_plans/ui-chart-wheel/analyst_artifact.md"]}})
 if (ROOT/(R+"tester/task_t004_review.md")).exists():
  result["document_audit"]=doc_audit();result["verdict"]="RESEARCH_EVIDENCE_SUFFICIENT_WITH_LIMITS";result["blocking_returns"]=[]
 if write:(ROOT/(OWN+"review.json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 elif "document_audit" in result:assert load(OWN+"review.json")==result,"own current snapshot differs; inspect before update"
 print("TASK_T004_PACKAGE_OK manifest=164/164 scope=165 source_hashes="+str(inputs["source_hashes"])+" shared=UNCHANGED")
 print("TASK_T004_RUN03_OK "+json.dumps(matrix["totals"])+" screenshots=25")
 print("TASK_T004_RETURN_WITNESS_OK "+json.dumps(matrix["local_witness"]))
 print("TASK_T004_REPLAY_OK source=8 orientation=4 coordinator=26 (actual=8/model=17/argument=1) browser_followup=6 PNG=3/3_MATCH")
 if "document_audit" in result:print("TASK_T004_DOCS_OK "+json.dumps({k:v for k,v in result["document_audit"].items() if k!="output_sha256_lf_or_raw"}))
 if write:print("TASK_T004_SNAPSHOT_WRITTEN own Tester JSON only")
if __name__=="__main__":
 if "--prepare-replay" in sys.argv:prepare()
 else:run("--write" in sys.argv)
