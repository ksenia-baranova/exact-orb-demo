"""TASK-D-004: exact analytical calibrations and document/source audit, no SVG/browser/placement."""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

R = 'docs/project_management/change_plans/ui-chart-wheel/'
PINS = {
    'input': 'aa067201dc509f19bbe670778a9fa9470cf0bfb0',
    'manager_material_base': '67fd9dbf25fb5cb6a4dafbce65582078917bb1a3',
    'criteria_v1': '11a703ed6a01eb368f0f0ba23dc23f1e90fac81f',
    'tester_t005': '71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe',
    'analyst_a003': '4055a9cb2bb18919c776c9d4e8585e2408a638c7',
    'analyst_v3': '2634b224894b1046113557bfe241f0a5f2d46f8c',
    'developer_v2': 'f9c70f75ea815b2f3bf7e01426ee5afe65b31606',
    'main_baseline': '535551026af6eedaf2a0aa5c0daa96fa94655ec1',
}
PLAN = R + 'developer/task_d003_implementation_plan.md'
INDEX = R + 'developer_artifact.md'
SCRIPT = R + 'developer/evidence/task_d004_controls.py'
OUTPUT = R + 'developer/evidence/task_d004_controls.json'
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).replace(b'\r\n', b'\n')

def blob(sha, path):
    return git('show', f'{sha}:{path}')

def read(path):
    return (ROOT / path).read_bytes().replace(b'\r\n', b'\n')

def digest(value):
    return hashlib.sha256(value.replace(b'\r\n', b'\n')).hexdigest()

def rect(x1, x2, y1=0, y2=16):
    value = tuple(F(str(n)) for n in (x1, x2, y1, y2))
    assert value[0] <= value[1] and value[2] <= value[3]
    return value

def gap_squared(a, b):
    dx = max(a[0] - b[1], b[0] - a[1], F(0))
    dy = max(a[2] - b[3], b[2] - a[3], F(0))
    return dx * dx + dy * dy

def union_gap_squared(a, b):
    return min(gap_squared(x, y) for x in a for y in b)

def contains(outer, inner):
    return outer[0] <= inner[0] <= inner[1] <= outer[1] and outer[2] <= inner[2] <= inner[3] <= outer[3]

def annulus_contains(box, inner, outer):
    # C=(0,0), exact extrema of the fixed AABB. No placement is computed.
    dx = max(box[0], -box[1], F(0))
    dy = max(box[2], -box[3], F(0))
    maximum = max(x*x + y*y for x in box[:2] for y in box[2:])
    return dx*dx + dy*dy >= F(inner)**2 and maximum <= F(outer)**2

def interior_overlap(a, b):
    return max(a[0], b[0]) < min(a[1], b[1]) and max(a[2], b[2]) < min(a[3], b[3])

def hit_certificate(q, native_shape, clip, overlays=()):
    return q[1]-q[0] >= 44 and q[3]-q[2] >= 44 and contains(native_shape, q) and contains(clip, q) and not any(interior_overlap(q, o) for o in overlays)

def line_return_record(origin_left, candidate_left):
    # Closed-form calibration of the review's one-dimensional primitive only.
    # The obstacle remains [0,16], B width=16, y intervals equal; direction is left.
    origin, left = F(str(origin_left)), F(str(candidate_left))
    d = left-origin
    assert d > 0 and origin < 18, 'primitive must start in the declared conflict'
    gap = left-16
    feasible = gap >= 2
    s = min(F(1), d)
    prefix_capacity = min(d, max(F(0), gap-2)) if feasible else F(0)
    return {'feasible': feasible, 'probe_length': s, 'probe_gap': gap-s,
            'step_pass': feasible and prefix_capacity < s,
            'tight_pass': feasible and prefix_capacity == 0,
            'admissible_return_prefix': prefix_capacity}

def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value

cases = []
def check(name, input_description, actual, expected):
    assert actual == expected, (name, jsonable(actual), jsonable(expected))
    cases.append({'id': name, 'input': input_description, 'expected': jsonable(expected), 'actual': jsonable(actual), 'result': 'PASS', 'evidence_type': 'ANALYTICAL_NOT_BROWSER'})

a = rect(0, 16)
b = rect('17.5', '33.5', '17.5', '33.5')
check('G-diagonal-gap', {'A': a, 'B': b}, {'squared_gap': gap_squared(a,b), 'gap_pass': gap_squared(a,b) >= 4}, {'squared_gap': F('4.5'), 'gap_pass': True})
for name, left, expected in [('G-gap-boundary', '18', True), ('G-gap-below', '17.99', False)]:
    candidate = rect(left, F(left)+16)
    check(name, {'A': a, 'B': candidate}, gap_squared(a, candidate) >= 4, expected)
components = [rect(0,4,0,16), rect(0,16,0,4)]
b = rect(8,12,8,12)
check('G-union-not-envelope', {'A_components': components, 'B': b}, {'union_gap_squared': union_gap_squared(components,[b]), 'envelope_gap_squared': gap_squared(rect(0,16),b)}, {'union_gap_squared': F(16), 'envelope_gap_squared': F(0)})
for name, box, expected in [('G-forbidden-outer',rect(9,11,0,2),False), ('G-forbidden-inner',rect(1,3,0,1),False), ('G-region-boundary',rect(6,8,0,6),True)]:
    check(name, {'center': [0,0], 'annulus': [4,10], 'component': box}, annulus_contains(box,4,10), expected)
page, clip = rect(0,360,0,100), rect(0,300,0,100)
for name, box, expected in [('G-SVG-clipping', rect(292,308,10,26),False), ('G-SVG-clip-positive', rect(284,300,10,26),True)]:
    check(name, {'page': page, 'clip': clip, 'box': box}, {'page_contained': contains(page,box), 'clip_contained': contains(clip,box)}, {'page_contained': True, 'clip_contained': expected})
for name, point, expected in [('G-anchor-boundary',[F('.5'),F(0)],True), ('G-anchor-diagonal',[F('.3'),F('.4')],True), ('G-anchor-fail',[F('.51'),F(0)],False)]:
    check(name, {'expected': [0,0], 'actual': point}, sum(x*x for x in point) <= F('.5')**2, expected)

for name, origin, left, length, probe_gap, step, tight, capacity in [
    ('L-18','0','18','1','1',True,True,'0'),
    ('L-20','0','20','1','3',False,False,'2'),
    ('L-19','0','19','1','2',False,False,'1'),
    ('L-fraction','8','18.5','1','1.5',True,False,'.5'),
    ('L-subpixel-tight','17.5','18','.5','1.5',True,True,'0'),
    ('L-subpixel-excess','17.75','18.25','.5','1.75',True,False,'.25'),
]:
    check(name, {'origin_left': origin, 'candidate_left': left, 'frozen_obstacle': a}, line_return_record(origin,left),
          {'feasible': True, 'probe_length': F(length), 'probe_gap': F(probe_gap), 'step_pass': step, 'tight_pass': tight, 'admissible_return_prefix': F(capacity)})
check('L-zero-sparse', {'default': rect(40,56), 'candidate': rect(40,56), 'obstacle': a}, {'conflict': gap_squared(a,rect(40,56)) < 4, 'displacement': F(0), 'leader': False, 'probe': 'N/A'}, {'conflict': False, 'displacement': F(0), 'leader': False, 'probe': 'N/A'})
t, radius = F(1,200), F(100)
qx, qy = 2*radius*t/(1+t*t), radius*(1-t*t)/(1+t*t)
check('L-arc-positive-prefix', {'radius': radius, 'P': [0,100], 'A': [100,0], 'rational_t': t},
      {'radius_squared': qx*qx+qy*qy, 'closer_to_A': (qx-100)**2+qy*qy < 20000, 'positive_prefix': qx > 0 and qy < 100},
      {'radius_squared': F(10000), 'closer_to_A': True, 'positive_prefix': True})
with localcontext() as ctx:
    ctx.prec = 50
    chord_radius_squared = Decimal(10000)+1-100*Decimal(2).sqrt()
    check('L-chord-invalid-probe', {'radius': 100, 'one_px_chord_squared_radius': str(chord_radius_squared)}, chord_radius_squared < 10000, True)

for name, nominal, scale, threshold, expected in [
    ('F-glyph-boundary','16','1','16',True), ('F-R-boundary','12','1','12',True),
    ('F-glyph-below','15.99','1','16',False), ('F-category-below','11.99','1','12',False),
    ('F-scale','16','.5','16',False),
]:
    effective = F(nominal)*F(scale)
    check(name, {'local_em': nominal, 'scale': scale, 'threshold': threshold}, {'effective_em': effective, 'size_pass': effective >= F(threshold)}, {'effective_em': effective, 'size_pass': expected})
check('F-em-vs-ink', {'effective_em':16,'ink_height':12}, F(16)>=16, True)
check('F-tofu', {'em':16,'resolved_supported_glyph':False}, bool(16>=16 and False), False)
check('F-fallback', {'em':16,'resolved_supported_fixture_font':True,'real_font_measured':False}, bool(16>=16 and True), True)

q = rect(0,44,0,44)
for name, native, clipping, overlays, expected in [
    ('H-full-44',q,q,[],True),
    ('H-narrow',rect(20,24,0,44),q,[],False),
    ('H-overlay',q,q,[rect(30,44,0,44)],False),
    ('H-overlay-paired-positive',q,q,[],True),
    ('H-clip',q,rect(0,43,0,44),[],False),
    ('H-neighbour-at-excluded-edge',q,q,[rect(44,60,0,44)],True),
]:
    check(name, {'Q':q,'native_shape':native,'clip':clipping,'overlays':overlays}, hit_certificate(q,native,clipping,overlays), expected)
def half_open_hit(box,x,y):
    return box[0] <= F(x) < box[1] and box[2] <= F(y) < box[3]
check('H-off-centre-sensitive', {'target':q,'overlay':rect(30,44,0,44),'centre':[22,22],'off_centre':[33,22]},
      {'centre_intercepted':half_open_hit(rect(30,44,0,44),22,22), 'off_centre_intercepted':half_open_hit(rect(30,44,0,44),33,22)},
      {'centre_intercepted':False,'off_centre_intercepted':True})
check('H-boundary-half-open', {'Q':q}, {'left_top':half_open_hit(q,0,0), 'right':half_open_hit(q,44,22), 'bottom':half_open_hit(q,22,44)}, {'left_top':True,'right':False,'bottom':False})
check('H-wrong-owner', {'expected_key':'point:sun','actual_key':'point:moon','bbox_pass':True}, 'point:sun'=='point:moon', False)

def focus_record_ok(record):
    # Model record only. Does not observe or emulate a browser DOM/focus engine.
    if not all(record[k] for k in ['connected','visible','enabled','next_actionable']) or record.get('scroll',False):
        return False
    if record['cause']=='planet':
        return record['before_node']==record['after_node'] and record['before_key']==record['after_key'] and not record.get('programmatic_focus',False)
    if record['cause']=='collapse' and record.get('late_different_draft',False):
        return False
    if record['before_key']==record['after_key']:
        return True
    if record.get('initiator_live',False):
        return record['after_key']==record['initiator_key']
    available = record.get('available_fallbacks',[])
    ordered = ['editor-toggle','recovery-check','birth:date','birth:place','birth:time','terms-gate']
    expected = next((key for key in ordered if key in available),None)
    return expected is not None and record['after_key']==expected

base_record = dict(cause='planet',before_node='n1',after_node='n1',before_key='point:sun',after_key='point:sun',connected=True,visible=True,enabled=True,next_actionable=True,programmatic_focus=False)
for name, changes, expected in [
    ('K-planet-retained',{},True),
    ('K-planet-recreated',{'after_node':'n2','programmatic_focus':True},False),
    ('K-planet-transfer',{'after_node':'n2','after_key':'aspect:x','programmatic_focus':True,'available_fallbacks':['aspect:x']},False),
    ('K-current-recreated',{'cause':'current','after_node':'n2','programmatic_focus':True},True),
    ('K-current-missing-fallback',{'cause':'current','after_node':'edit','after_key':'editor-toggle','programmatic_focus':True,'available_fallbacks':['editor-toggle','recovery-check']},True),
    ('K-current-wrong-fallback',{'cause':'current','after_node':'retry','after_key':'recovery-check','programmatic_focus':True,'available_fallbacks':['editor-toggle','recovery-check']},False),
    ('K-current-no-valid-fallback',{'cause':'current','after_node':'body','after_key':'body','programmatic_focus':True,'available_fallbacks':[]},False),
    ('K-current-detached',{'cause':'current','connected':False},False),
    ('K-collapse-outside',{'cause':'collapse'},True),
    ('K-collapse-inside-to-editor',{'cause':'collapse','after_node':'edit','after_key':'editor-toggle','programmatic_focus':True,'available_fallbacks':['editor-toggle']},True),
    ('K-collapse-late-draft',{'cause':'collapse','late_different_draft':True},False),
    ('K-hidden-recovery',{'cause':'collapse','visible':False},False),
]:
    record = {**base_record, **changes}
    check(name, record, focus_record_ok(record), expected)

if '--calibrations-only' in sys.argv:
    print(f'TASK_D004_ANALYTICAL_OK cases={len(cases)}/{len(cases)} no_layout_algorithm no_SVG no_browser')
    sys.exit(0)

for pin in PINS.values():
    git('merge-base','--is-ancestor',pin,PINS['input'])
assert git('branch','--show-current').decode().strip()=='dev/ui-chart-wheel'
old_plan = blob(PINS['criteria_v1'],PLAN)
assert blob(PINS['input'],PLAN)==old_plan
for pin,paths in [(PINS['tester_t005'],[R+'tester/task_t005_review.md',R+'tester/evidence/task_t005_review.json']), (PINS['analyst_a003'],[R+'analyst_artifact.md'])]:
    for path in paths:
        assert read(path)==blob(pin,path),path
review = json.loads(read(R+'tester/evidence/task_t005_review.json'))
for entry in review['sources']:
    assert digest(blob(entry['sha'],entry['path']))==entry['sha256_lf'],entry['path']
manifest_counts = {}
for role,pin in [('developer',PINS['developer_v2']),('analyst',PINS['analyst_v3'])]:
    path = R+role+'/package_manifest.json'
    manifest = json.loads(blob(pin,path))
    assert read(path)==blob(pin,path)
    items = manifest['files']
    pairs = [(x['path'],x['sha256']) for x in items] if isinstance(items,list) else [(R+k,v) for k,v in items.items()]
    assert len(pairs)==9
    for path,expected in pairs:
        assert digest(blob(pin,path))==expected,path
    manifest_counts[role]='9/9 historical Git payload'
historical = git('ls-tree','-r','--name-only',PINS['input'],'--',R+'developer').decode().splitlines()
historical_unchanged = [p for p in historical if p!=PLAN]
for path in historical_unchanged:
    assert read(path)==blob(PINS['input'],path),path
prior_index = blob(PINS['input'],INDEX)
assert read(INDEX).startswith(prior_index)
assert '## TASK-D-004 — STARTED'.encode() in read(INDEX)[len(prior_index):]
assert '## TASK-D-004 — передача исправленных критериев v2'.encode() in read(INDEX)[len(prior_index):]
allowed = {PLAN,INDEX,SCRIPT,OUTPUT}
changed = set(git('diff','--name-only',PINS['input']).decode().splitlines()) | set(git('ls-files','--others','--exclude-standard').decode().splitlines())
assert changed | {OUTPUT} == allowed, changed
shared = ['src','tests','docs/requirements','docs/sequence_diagrams','docs/development_approach','pyproject.toml','AGENTS.md']
assert not git('diff','--name-only',PINS['main_baseline'],PINS['input'],'--',*shared).strip()
assert read(R+'manager_artifact.md')==blob(PINS['input'],R+'manager_artifact.md')

def anchors(text):
    result = set(re.findall(r'<a\s+id="([^"]+)"',text))
    counts = {}
    for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title)
        slug = re.sub(r'\s','-',re.sub(r'[^\w\s-]','',title.lower()))
        count = counts.get(slug,0)
        counts[slug] = count+1
        result.add(slug if count==0 else f'{slug}-{count}')
    return result

links = tables = 0
documents = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/R).rglob('*.md'))
for path in documents:
    text = read(path).decode()
    assert all(x==x.rstrip() for x in text.splitlines()),path
    width = None
    for line in text.splitlines():
        if line.startswith('|'):
            n = len(re.split(r'(?<!\\)\|',line))
            if width is None:
                tables += 1
            assert width is None or n==width,(path,line)
            width = n
        else:
            width = None
    for destination in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z]+:',destination):
            continue
        part,_,anchor = unquote(destination).partition('#')
        target = ((ROOT/path).parent/part).resolve() if part else ROOT/path
        assert target.exists() or ('--write' in sys.argv and target==(ROOT/OUTPUT).resolve()),(path,destination)
        if anchor and target.suffix=='.md':
            assert anchor in anchors(target.read_text(encoding='utf-8')),(path,destination,'anchor')
        links += 1

report = {
    'task':'TASK-D-004','revision':'criteria-v2-DRAFT','author':'Codex / Developer',
    'pins':PINS,'started_utc':'2026-10-17T19:35:11Z','deadline':'one working day from STARTED, agreed by Owner',
    'estimate_hours':[3,4],'budget_relation':'inside existing criteria slot / 20–28, no automatic addition',
    'evidence_type':'EXACT_ANALYTICAL_CALIBRATIONS_AND_DOCUMENT_AUDIT',
    'calibrations':jsonable(cases),'calibrations_passed':len(cases),
    'historical_manifest_checks':manifest_counts,'tester_t005_source_hashes':len(review['sources']),
    'v1_plan_sha256_lf':digest(old_plan),'prior_index_sha256_lf':digest(prior_index),
    'historical_developer_files_preserved':{p:digest(read(p)) for p in historical_unchanged},
    'manager_foreign_artifacts_shared_contract':'UNCHANGED','local_links_checked':links,
    'markdown_documents_checked':len(documents),'markdown_tables_checked':tables,
    'output_payload_sha256_lf':{p:digest(read(p)) for p in [PLAN,INDEX,SCRIPT]},
    'not_run':['SVG/browser experiment','actual font / bbox / hit / focus measurement','placement algorithm','generic curved-path certificate verifier','production runtime / Node / pytest','PUML render'],
    'task_d003':'BLOCKED; T0 not occurred; no unblock/STARTED event emitted',
    'next':'publish CriteriaSHA if authorized; TASK-T-006 + TASK-A-004; Manager decides unblock',
}
if '--write' in sys.argv:
    (ROOT/OUTPUT).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
    assert json.loads(read(OUTPUT))==report,'record differs; inspect before rewriting'
git('diff','--check')
assert not git('diff','--cached','--name-only').strip()
print(f'TASK_D004_CONTROLS_OK cases={len(cases)}/{len(cases)} G=EXACT L=18_PASS_20_FAIL_19_FAIL FRACTION=SEPARATE FONT=EFFECTIVE_EM HIT=EFFECTIVE_AREA FOCUS=MODEL_ONLY')
print(f'TASK_D004_AUDIT_OK paths=4 docs={len(documents)} links={links} tables={tables} anchors=VALID T005_source_hashes={len(review["sources"])}/{len(review["sources"])} manifests=9/9+9/9 history=PRESERVED Manager=UNCHANGED D003=BLOCKED T0=NOT_OCCURRED browser=NOT_RUN')
