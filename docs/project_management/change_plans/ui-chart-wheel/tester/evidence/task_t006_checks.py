"""TASK-T-006 independent analytic witnesses; no renderer/browser/placement imports.
Expected values fixed before reading Developer controls on 2026-10-18 10:50:13 UTC.
Sources: T005 R01..R03/N01, A003 C01..C03 and pinned v2 G/L/F/H definitions.
This checker certifies only the listed synthetic inputs, never a general curved path.
"""
from fractions import Fraction as Q
from pathlib import Path
import json

def rect(*v):
    return tuple(Q(str(x)) for x in v)  # left, top, right, bottom

def distance2(a,b):
    # Projection separation of closed intervals, independently of placement.
    total=Q(0)
    for lo,hi in ((0,2),(1,3)):
        if a[hi]<b[lo]: total+=(b[lo]-a[hi])**2
        elif b[hi]<a[lo]: total+=(a[lo]-b[hi])**2
    return total

def union_distance2(a,b):
    return min(distance2(x,y) for x in a for y in b)

def region(v,inner,outer):
    near=distance2(v,rect(0,0,0,0))
    far=max(x*x+y*y for x in (v[0],v[2]) for y in (v[1],v[3]))
    return near>=inner*inner and far<=outer*outer

def contained(v,clip):
    return all((v[0]>=clip[0],v[1]>=clip[1],v[2]<=clip[2],v[3]<=clip[3]))

def horizontal_certificate(default_x,current_x):
    # Fixed obstacle right=16 and gap=2 => admissible current left >=18.
    # The whole straight return prefix t is feasible iff 0<=t<=current_x-18.
    d=Q(str(current_x))-Q(str(default_x))
    slack=Q(str(current_x))-18
    if d<0 or slack<0: return ("INFEASIBLE","N/A","N/A")
    if d==0: return ("FEASIBLE","N/A","N/A")
    step=min(Q(1),d)
    return ("FEASIBLE","STEP_FAIL" if slack>=step else "STEP_PASS",
            "TIGHT_FAIL" if slack>0 else "TIGHT_PASS")

def effective_hit(q,shape,clip,overlays):
    # All inputs here are declared half-open rectangles. Partition by every
    # boundary; constant membership on each cell gives a finite containment proof.
    if q[2]-q[0]<44 or q[3]-q[1]<44: return False
    xs=sorted({q[0],q[2],*(x for r in [shape,clip,*overlays] for x in (r[0],r[2]) if q[0]<x<q[2])})
    ys=sorted({q[1],q[3],*(y for r in [shape,clip,*overlays] for y in (r[1],r[3]) if q[1]<y<q[3])})
    inside=lambda p,r:r[0]<=p[0]<r[2] and r[1]<=p[1]<r[3]
    return all(inside((x,y),shape) and inside((x,y),clip) and not any(inside((x,y),r) for r in overlays)
               for x in xs[:-1] for y in ys[:-1])

def analytic_controls():
    rows=[]
    def case(name,expected,actual):
        if expected!=actual: raise AssertionError((name,expected,actual))
        rows.append({"id":name,"expected":expected,"actual":actual,"status":"PASS_ANALYTIC_ONLY"})
    A=rect(0,0,16,16)
    case("G-anchor-0.5",True,Q("0.5")**2<=Q("0.5")**2)
    case("G-anchor-diagonal-outside",False,Q("0.4")**2+Q("0.4")**2<=Q("0.5")**2)
    case("G-anchor-3-4-5",True,Q("0.3")**2+Q("0.4")**2<=Q("0.5")**2)
    case("G-affine-css-frame",(24,5),(2*7+10,2*5-5))
    case("G-diagonal-squared","9/2",str(distance2(A,rect("17.5","17.5","33.5","33.5"))))
    case("G-gap-boundary",True,distance2(A,rect(18,0,34,16))>=4)
    case("G-gap-1.99",False,distance2(A,rect("17.99",0,"33.99",16))>=4)
    case("G-touch",0,distance2(A,rect(16,0,32,16)))
    U=[rect(0,0,4,16),rect(0,0,16,4)]
    case("G-union-hole",(16,0),(union_distance2(U,[rect(8,8,12,12)]),distance2(A,rect(8,8,12,12))))
    case("G-selected-contour",False,distance2(rect(0,0,17,16),rect(18,0,34,16))>=4)
    case("G-region-boundary",True,region(rect(6,0,8,6),4,10))
    case("G-region-outer",False,region(rect(9,0,11,2),4,10))
    case("G-region-inner",False,region(rect(1,0,3,1),4,10))
    clip=rect(0,0,300,100)
    case("G-svg-clip",False,contained(rect(292,10,308,26),clip))
    case("G-svg-clip-edge",True,contained(rect(284,10,300,26),clip))
    case("G-page-vs-svg",(True,False),(contained(rect(292,10,308,26),rect(0,0,360,100)),contained(rect(292,10,308,26),clip)))
    default={"a":[A],"b":[rect(8,0,24,16)],"c":[rect(100,0,116,16)]}
    c0=sorted(i for i,v in default.items() if any(i!=j and union_distance2(v,w)<4 for j,w in default.items()))
    case("G-frozen-original-conflict-set",["a","b"],c0)
    sparse={"a":[A],"b":[rect(18,0,34,16)]}
    case("G-hit-overlap-not-visual-conflict",[],[i for i,v in sparse.items() if any(i!=j and union_distance2(v,w)<4 for j,w in sparse.items())])
    for name,default,x,expected in [
        ("L-18",0,18,("FEASIBLE","STEP_PASS","TIGHT_PASS")),
        ("L-20",0,20,("FEASIBLE","STEP_FAIL","TIGHT_FAIL")),
        ("L-19",0,19,("FEASIBLE","STEP_FAIL","TIGHT_FAIL")),
        ("L-fraction",8,"18.5",("FEASIBLE","STEP_PASS","TIGHT_FAIL")),
        ("L-subpixel-tight","17.5",18,("FEASIBLE","STEP_PASS","TIGHT_PASS")),
        ("L-subpixel-excess","17.75","18.25",("FEASIBLE","STEP_PASS","TIGHT_FAIL")),
        ("L-zero",18,18,("FEASIBLE","N/A","N/A")),
    ]: case(name,expected,horizontal_certificate(default,x))
    u=Q(1,200)
    arc_point=(200*u/(1+u*u),100*(1-u*u)/(1+u*u))
    case("L-rational-circle-prefix",True,sum(v*v for v in arc_point)==10000 and arc_point[0]>0 and 200*u<=1)
    # atan(u)<u for u>0 => actual positive arc length=200*atan(u)<1.
    case("L-chord-prefix-invalid",False,Q("0.5")**2+Q("99.5")**2==10000)
    for name,em,limit,want in [
        ("F-glyph-equality",16,16,True),("F-R-equality",12,12,True),
        ("F-glyph-below","15.99",16,False),("F-R-below","11.99",12,False),
        ("F-scale-half",16*Q("0.5"),16,False),("F-em16-ink12",16,16,True),
    ]: case(name,want,Q(str(em))>=limit)
    case("F-translation-keeps-em",256,(0*16)**2+(1*16)**2)
    def font_record(em,font,present):
        if not present:return "READABILITY_FAIL"
        if font is None:return "UNPROVEN"
        return "SIZE_PASS" if em>=16 else "SIZE_FAIL"
    case("F-tofu-readability","READABILITY_FAIL",font_record(16,"known",False))
    case("F-unknown-font","UNPROVEN",font_record(16,None,True))
    case("F-recorded-supported-fallback","SIZE_PASS",font_record(16,"recorded-fallback",True))
    full=rect(0,0,44,44)
    for name,shape,c,overlays,want in [
        ("H-full44",full,full,[],True),
        ("H-width43",full,rect(0,0,43,44),[],False),
        ("H-narrow",rect(20,0,24,44),full,[],False),
        ("H-overlay-off-centre",full,full,[rect(30,0,44,44)],False),
        ("H-no-overlay-pair",full,full,[],True),
        ("H-tiny-overlay-between-samples",full,full,[rect("30.1","30.1","30.2","30.2")],False),
    ]: case(name,want,effective_hit(full,shape,c,overlays))
    case("H-half-open-edge",(True,False),(full[0]<=0<full[2],full[0]<=44<full[2]))
    case("H-wrong-owner",False,"j"=="i")
    # Predicate records below are logical classification, NOT executed font/events/DOM.
    for name,cause,same_node,live,programmatic,want in [
        ("H-focus-retained","planet",True,True,False,True),
        ("H-focus-recreated-same-key","planet",False,True,True,False),
        ("H-focus-detached","planet",True,False,False,False),
        ("H-focus-forbidden-transfer","planet",True,True,True,False),
        ("H-focus-external-same-key","reconcile",False,True,True,True),
        ("H-focus-removed-fallback","external-removed",False,True,True,True),
    ]:
        actual=live and (cause!="planet" or (same_node and not programmatic))
        case(name,want,actual)
    return rows


# Source/document checks use immutable Git objects; historical evidence is never
# recomputed against the current HEAD. This section was added after the first
# independent analytical run and Developer --calibrations-only replay.
import hashlib
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT=next(p for p in Path(__file__).resolve().parents if (p/".git").exists())
R="docs/project_management/change_plans/ui-chart-wheel/"
PINS={
 "head":"8b94195b8aa1c101b356ae860ebeb60a29c9b88a",
 "review_input":"8a05b73c2af2c36043f9ede04834dd3867f4a686",
 "criteria":"f6f289cda25e7f228dff064175805130cc770b63",
 "developer_input":"aa067201dc509f19bbe670778a9fa9470cf0bfb0",
 "v1":"11a703ed6a01eb368f0f0ba23dc23f1e90fac81f",
 "tester_t005":"71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe",
 "analyst_a003":"4055a9cb2bb18919c776c9d4e8585e2408a638c7",
 "analyst_v3":"2634b224894b1046113557bfe241f0a5f2d46f8c",
 "main":"535551026af6eedaf2a0aa5c0daa96fa94655ec1",
 "tester_t003":"c59cc3f68e7769841134801dc125633decade032",
 "developer_consultation":"f9c70f75ea815b2f3bf7e01426ee5afe65b31606",
}
PLAN=R+"developer/task_d003_implementation_plan.md"
DEVINDEX=R+"developer_artifact.md"
DEVSCRIPT=R+"developer/evidence/task_d004_controls.py"
DEVAUDIT=R+"developer/evidence/task_d004_controls.json"
INDEX=R+"tester_artifact.md"
REPORT=R+"tester/task_t006_review.md"
SCRIPT=R+"tester/evidence/task_t006_checks.py"
OUTPUT=R+"tester/evidence/task_t006_review.json"
ALLOWED=[INDEX,REPORT,SCRIPT,OUTPUT]
norm=lambda b:b.replace(b"\r\n",b"\n")
digest=lambda b:hashlib.sha256(norm(b)).hexdigest()
def git(*args):return norm(subprocess.check_output(["git","-C",str(ROOT),*args]))
def blob(sha,path):return git("show",sha+":"+path)
def read(path):return norm((ROOT/path).read_bytes())
def js(value):
    if isinstance(value,Q):return value.numerator if value.denominator==1 else str(value)
    if isinstance(value,dict):return {k:js(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [js(v) for v in value]
    return value

def sources_audit():
    current_head=git("rev-parse","HEAD").decode().strip()
    git("merge-base","--is-ancestor",PINS["head"],current_head)
    committed=set(git("diff","--name-only",PINS["head"],current_head).decode().splitlines())
    worktree={line[3:] for line in git("status","--porcelain","--untracked-files=all").decode().splitlines()}
    assert (committed|worktree)<=set(ALLOWED),(committed,worktree)
    assert git("branch","--show-current").decode().strip()=="test/ui-chart-wheel"
    for sha in PINS.values():git("merge-base","--is-ancestor",sha,PINS["head"])
    assert git("show","-s","--format=%P",PINS["head"]).decode().strip()==PINS["review_input"]
    assert set(git("show","-s","--format=%P",PINS["review_input"]).decode().split())=={PINS["developer_input"],PINS["criteria"]}
    manager_paths={R+p for p in ["manager_artifact.md","manager/render_gantt.py","manager/gantt.svg","manager/prompts/task-t-006-criteria-v2-review.md","manager/prompts/task-a-004-criteria-v2-semantics.md"]}
    assert set(git("diff","--name-only",PINS["review_input"],PINS["head"]).decode().splitlines())==manager_paths
    assert set(git("diff","--name-only",PINS["developer_input"],PINS["criteria"]).decode().splitlines())=={PLAN,DEVINDEX,DEVSCRIPT,DEVAUDIT}
    published=git("log","--reverse","--format=%H","-G","^# TASK-T-006",PINS["head"],"--",R+"manager/prompts/task-t-006-criteria-v2-review.md").decode().splitlines()
    assert published[0]==PINS["head"]
    v2=json.loads(blob(PINS["criteria"],DEVAUDIT))
    for path,h in v2["output_payload_sha256_lf"].items():assert digest(blob(PINS["criteria"],path))==h and read(path)==blob(PINS["criteria"],path),path
    assert len(v2["output_payload_sha256_lf"])==3
    assert digest(blob(PINS["v1"],PLAN))==v2["v1_plan_sha256_lf"]
    assert blob(PINS["developer_input"],PLAN)==blob(PINS["v1"],PLAN)
    assert digest(blob(PINS["developer_input"],DEVINDEX))==v2["prior_index_sha256_lf"]
    assert blob(PINS["criteria"],DEVINDEX).startswith(blob(PINS["developer_input"],DEVINDEX))
    for p,h in v2["historical_developer_files_preserved"].items():
        assert digest(blob(PINS["developer_input"],p))==h
        assert blob(PINS["criteria"],p)==blob(PINS["developer_input"],p)==read(p)
    histories={}
    for name,sha,path in [
        ("T005",PINS["tester_t005"],R+"tester/evidence/task_t005_review.json"),
        ("T003",PINS["tester_t003"],R+"tester/evidence/task_t003_review.json")]:
        d=json.loads(blob(sha,path))
        for e in d["sources"]:assert digest(blob(e["sha"],e["path"]))==e["sha256_lf"]
        for p,h in d["output_sha256_lf"].items():assert digest(blob(sha,p))==h,(name,p)
        histories[name]={"source_hashes":len(d["sources"]),"output_hashes":len(d["output_sha256_lf"]),"output_sha":sha}
    prep=json.loads(blob(PINS["v1"],R+"developer/evidence/task_d003_preparation.json"))
    for p,h in prep["preparation_outputs_sha256_lf"].items():assert digest(blob(PINS["v1"],p))==h
    histories["preparation_output_hashes_at_v1"]=len(prep["preparation_outputs_sha256_lf"])
    manifests={}
    for role,sha in [("analyst",PINS["analyst_v3"]),("developer",PINS["developer_consultation"])]:
        m=json.loads(blob(sha,R+role+"/package_manifest.json"))
        items=m["files"]
        pairs=[(e["path"],e["sha256"]) for e in items] if isinstance(items,list) else [(R+p,h) for p,h in items.items()]
        for p,h in pairs:assert digest(blob(sha,p))==h,p
        assert len(pairs)==9
        manifests[role]=len(pairs)
    shared=["src","tests","docs/requirements","docs/sequence_diagrams","docs/development_approach","pyproject.toml","AGENTS.md"]
    assert not git("diff","--name-only",PINS["main"],PINS["head"],"--",*shared).strip()
    src=[]
    groups=[
     (PINS["head"],["AGENTS.md","docs/development_approach/skills/tester/SKILL.md","docs/development_approach/process/process.md","docs/development_approach/roles.md","docs/development_approach/development-approach.md",R+"manager_artifact.md",R+"manager/prompts/task-t-006-criteria-v2-review.md"]),
     (PINS["criteria"],[PLAN,DEVINDEX,DEVSCRIPT,DEVAUDIT]),
     (PINS["tester_t005"],[INDEX,R+"tester/task_t005_review.md",R+"tester/evidence/task_t005_review.json"]),
     (PINS["analyst_a003"],[R+"analyst_artifact.md"]),
     (PINS["analyst_v3"],[R+"analyst/"+p for p in ["requirements.md","scenarios.md","findings.md","package_manifest.json","sequence_diagrams/ui/001-chart-presentation.puml","sequence_diagrams/ui/002-wheel-table-selection.puml","sequence_diagrams/ui/003-edit-and-recovery.puml"]]),
     (PINS["main"],["docs/requirements/README.md","docs/requirements/http_api.md","docs/requirements/current/ui/birth-form-and-facts.md","docs/requirements/current/ui/scenarios.md"])
    ]
    for sha,paths in groups:
        for path in paths:
            b=blob(sha,path)
            if path in [INDEX,R+"analyst_artifact.md"]:assert read(path).startswith(b)
            else:assert read(path)==b,path
            src.append({"sha":sha,"path":path,"sha256_lf":digest(b)})
    prior=blob(PINS["head"],INDEX)
    assert read(INDEX).startswith(prior)
    old=git("ls-tree","-r","--name-only",PINS["head"],"--",R+"tester").decode().splitlines()
    for p in old:assert read(p)==blob(PINS["head"],p),p
    records=v2["calibrations"]
    assert len(records)==50 and all(e["actual"]==e["expected"] for e in records)
    byid={e["id"]:e["actual"] for e in records}
    literal={
     "G-gap-boundary":True,"G-gap-below":False,"G-forbidden-outer":False,"G-forbidden-inner":False,
     "G-region-boundary":True,"G-anchor-boundary":True,"G-anchor-diagonal":True,"G-anchor-fail":False,
     "L-chord-invalid-probe":True,"F-em-vs-ink":True,"F-tofu":False,"F-fallback":True,
     "H-full-44":True,"H-narrow":False,"H-overlay":False,"H-overlay-paired-positive":True,
     "H-clip":False,"H-neighbour-at-excluded-edge":True,"H-wrong-owner":False,
     "K-planet-retained":True,"K-planet-recreated":False,"K-planet-transfer":False,
     "K-current-recreated":True,"K-current-missing-fallback":True,"K-current-wrong-fallback":False,
     "K-current-no-valid-fallback":False,"K-current-detached":False,"K-collapse-outside":True,
     "K-collapse-inside-to-editor":True,"K-collapse-late-draft":False,"K-hidden-recovery":False,
    }
    for k,want in literal.items():assert byid[k]==want,k
    assert byid["G-diagonal-gap"]=={"squared_gap":"9/2","gap_pass":True}
    assert byid["G-union-not-envelope"]=={"union_gap_squared":"16","envelope_gap_squared":"0"}
    for name,want in [("G-SVG-clipping",False),("G-SVG-clip-positive",True)]:
        assert byid[name]=={"page_contained":True,"clip_contained":want}
    expected_lines=[("L-18",0,18),("L-20",0,20),("L-19",0,19),("L-fraction",8,"18.5"),("L-subpixel-tight","17.5",18),("L-subpixel-excess","17.75","18.25")]
    for name,origin,left in expected_lines:
        f,step,tight=horizontal_certificate(origin,left)
        d=Q(str(left))-Q(str(origin)); slack=Q(str(left))-18
        want={"feasible":f=="FEASIBLE","probe_length":str(min(Q(1),d)),
              "probe_gap":str(Q(str(left))-16-min(Q(1),d)),
              "step_pass":step=="STEP_PASS","tight_pass":tight=="TIGHT_PASS",
              "admissible_return_prefix":str(min(d,slack))}
        assert byid[name]==want,name
    assert byid["L-zero-sparse"]=={"conflict":False,"displacement":"0","leader":False,"probe":"N/A"}
    assert byid["L-arc-positive-prefix"]=={"radius_squared":"10000","closer_to_A":True,"positive_prefix":True}
    for name,e,threshold in [("F-glyph-boundary","16",16),("F-R-boundary","12",12),("F-glyph-below","15.99",16),("F-category-below","11.99",12),("F-scale","8",16)]:
        assert byid[name]=={"effective_em":str(Q(e)),"size_pass":Q(e)>=threshold},name
    assert byid["H-off-centre-sensitive"]=={"centre_intercepted":False,"off_centre_intercepted":True}
    assert byid["H-boundary-half-open"]=={"left_top":True,"right":False,"bottom":False}
    covered=set(literal)|{x[0] for x in expected_lines}|{"G-diagonal-gap","G-union-not-envelope","G-SVG-clipping","G-SVG-clip-positive","L-zero-sparse","L-arc-positive-prefix","F-glyph-boundary","F-R-boundary","F-glyph-below","F-category-below","F-scale","H-off-centre-sensitive","H-boundary-half-open"}
    assert covered==set(byid)
    return {"sources":src,"historical_checks":histories,"manifests":manifests,
      "d004_payload_hashes":3,"d004_historical_developer_files":len(v2["historical_developer_files_preserved"]),
      "previous_tester_files":len(old),"previous_index_prefix_sha256_lf":digest(prior),
      "developer_records_independently_compared":len(covered),"shared_contract_code_tests":"UNCHANGED",
      "manager":"UNCHANGED","registration_paths":5,"developer_scope_paths":4,"tester_scope_paths":len(committed|worktree)}

def anchor_set(text):
    out=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
    for title in re.findall(r"^#{1,6}\s+(.+)$",text,re.M):
        title=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",title)
        slug=re.sub(r"\s","-",re.sub(r"[^\w\s-]","",title.lower()))
        n=counts.get(slug,0);counts[slug]=n+1;out.add(slug if not n else slug+"-"+str(n))
    return out

def docs_audit():
    links=tables=0
    for p in [INDEX,REPORT]:
        text=read(p).decode("utf-8")
        assert text.endswith("\n") and not text.endswith("\n\n"),p
        assert all(l==l.rstrip() for l in text.splitlines()),p
        width=None
        for line in text.splitlines():
            if line.startswith("|"):
                n=len(re.split(r"(?<!\\)\|",line))
                if width is None:tables+=1
                assert width is None or n==width,(p,line)
                width=n
            else:width=None
        for dest in re.findall(r"\[[^\]]+\]\(([^)]+)\)",text):
            if re.match(r"^[A-Za-z]+:",dest):continue
            part,_,anchor=unquote(dest).partition("#")
            target=((ROOT/p).parent/part).resolve() if part else ROOT/p
            assert target.exists(),(p,dest)
            if anchor and target.suffix==".md":assert anchor in anchor_set(target.read_text(encoding="utf-8")),(p,dest)
            links+=1
    report=read(REPORT).decode("utf-8")
    for token in ["T005-R01","T005-R02","T005-R03","T005-N01","FEASIBLE","LOCAL_STEP","LOCAL_TIGHT","UNPROVEN","TASK-T-004","TEST-FIND-WHEEL-002"]:
        assert token in report,token
    return {"result":"TASK_T006_DOCS_OK","documents":2,"local_links":links,"tables":tables,"anchors":"VALID"}

def run_audit(write=False):
    source=sources_audit();docs=docs_audit();rows=analytic_controls()
    evidence={"task_id":"TASK-T-006","author":"Codex / Tester","date":"2026-10-18",
     "started_utc":"2026-10-18T10:48:35Z","started_msk":"2026-10-18 13:48:35",
     "estimate_hours":[2,4],"confidence":"MEDIUM","target_workdays":1,"feasible_confirmed_before_start":True,
     "deadline":"one working day after exact handoff; working calendar not specified",
     "verdict":"SUITABLE_FOR_BOUNDED_RESEARCH_IN_TESTER_SCOPE","pins":PINS,
     "independent_expected_order":"51 own analytic controls executed before first Developer controls source read / replay; definitions from T005/A003/pinned v2, no Developer imports",
     "input_audit":source,"independent_controls":js(rows),
     "independent_control_count":len(rows),"developer_calibrations_replay":{"command":"python -X utf8 "+DEVSCRIPT+" --calibrations-only","exit_code":0,"actual":"TASK_D004_ANALYTICAL_OK cases=50/50 no_layout_algorithm no_SVG no_browser"},
     "docs":docs,"output_sha256_lf":{p:digest(read(p)) for p in [INDEX,REPORT,SCRIPT]},
     "owner_numbers_preserved":[0.5,2,1,16,12,44],
     "documentary_return_items":{"T005-R01":"DEFINITION_RESOLVED","T005-R02":"DEFINITION_RESOLVED","T005-R03":"MEASURABLE_DEFINITION_RESOLVED; semantic choice remains A004","T005-N01":"PROTOCOL_DEFINED; native evidence future"},
     "not_run":["SVG/browser experiment","general curved-path verifier","actual fonts / glyph bounds","native pointer / keyboard","live DOM focus","production / mounted UI","Node / pytest / HTTPS","PUML rendering"],
     "remaining_evidence_owners":{"Developer_TASK_D003":"fixed fixture frame/radii/fonts, path certificate, full matrix / measurements and technical package","Analyst_TASK_A004":"compatibility of G/L/F/H choices with v3 / Owner scope","Manager":"register exact publication; decide D003 dependency only after positive T006/A004 and input/environment readiness","Tester_TASK_T004":"separate post-research review; TEST-FIND-WHEEL-002 remains OPEN"},
     "task_d003":"BLOCKED; ResumeStatus=NOT_STARTED; T0 absent",
     "publication":{
       "authorization":"Owner separately requested commit/push to test/ui-chart-wheel then merge into change/ui-chart-wheel",
       "pre_authorization_snapshot":{"commit":"NOT_CREATED","push":"NOT_RUN","pr":"NOT_CREATED"},
       "source_sha_resolver":"git log --reverse --format=%H -G '^### Публикация и интеграция review TASK-T-006$' -- docs/project_management/change_plans/ui-chart-wheel/tester_artifact.md (first line)",
       "verification":"Compare local/remote test SHA; record PR and merge SHA; verify result SourceSHA is ancestor of origin/change/ui-chart-wheel; report actual results to Owner",
       "change_before_integration":"5de9e66c26496880f714f61f78126972dee4fbdd",
       "change_delta_from_review_input":["docs/project_management/change_plans/ui-chart-wheel/analyst_artifact.md"]},
     "historical_evidence":"CHECKED_AT_RECORDED_SHAS_NOT_REBASED","foreign_files_changed":False}
    if write:(ROOT/OUTPUT).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:assert json.loads(read(OUTPUT))==evidence,"new evidence differs; inspect instead of rebasing historical inputs"
    print("TASK_T006_SOURCE_AUDIT_OK sources="+str(len(source["sources"]))+" D004_payload=3/3 historical_T005=16/16 T003=42/42 manifests=9/9+9/9")
    print("TASK_T006_INDEPENDENT_CONTROLS_OK cases="+str(len(rows))+" Developer_records=50/50 MATCH analytic_only")
    print(json.dumps(docs,ensure_ascii=False))
    print("TASK_T006_EVIDENCE_OK output_hashes=3 historical=PINNED D003=BLOCKED T0=ABSENT runtime=NOT_RUN")

if __name__=="__main__":
    if "--sources-only" in sys.argv:
        a=sources_audit()
        print(json.dumps({k:v for k,v in a.items() if k!="sources"},ensure_ascii=False))
    elif "--audit" in sys.argv:run_audit("--write" in sys.argv)
    else:
        rows=analytic_controls()
        print(json.dumps({"result":"TASK_T006_INDEPENDENT_CONTROLS_OK","cases":len(rows),
          "cases_by_prefix":{k:sum(r["id"].startswith(k+"-") for r in rows) for k in ("G","L","F","H")},
          "limits":"Synthetic geometry and scalar/model records only; no general curved-path verifier, actual font, native events or live DOM.",
          "records":js(rows)},ensure_ascii=False))
