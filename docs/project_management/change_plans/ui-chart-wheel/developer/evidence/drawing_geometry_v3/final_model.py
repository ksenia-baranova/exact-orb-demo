"""Float32/grid precision is part of placement, before testing constraints."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast,struct
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());third=json.loads((B/'spec_C.json').read_text());OLD=B.parent/'task_d005_feasibility/analytic';deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
assert not (B/'spec_F.json').exists()
proposal={'variant':'F','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'post-layout rounding of D/E breaks tight contacts; instead quantize each seed before domain/pair/order validation','reference':'same explicitly physical Af32 proposal as E, A_ideal retained; C0 membership must match published default semantics','construction':'B joint radial-lane beam seeds, CSP forward-checking only if beam fails; placement tests quantized final seed values; at most existing96 beam / existing CSP15s/cell','precision':'grid1/1024 CSS px before checks, SVG binary32 origins, exact full binary decimal output, integer origin in local browser harness; full actual measurement separately','compression':'only representable axis contacts, max24 sweeps, exact tightness verifier distinguishes residual fail/unproven; no unrestricted chord position accepted','thresholds':'unchanged 0.5/2/1/16/12; selected contour included; no SVG focus/hit; same annuli/clip/source rows/longitudes; no product fallback','limits':'one fresh finite construction, parent90min; no new dependencies, full zodiac/palette or runtime integration'}
(B/'spec_F.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def loaddefs(file):
 code=(B/file).read_text(encoding='utf-8');exec(compile(ast.Module(body=[n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)],type_ignores=[]),file+' definitions','exec'),globals())
loaddefs('build.py');loaddefs('csp.py');loaddefs('stable.py')
xy_unrounded=xy
def xy(t,r,C):return stable([round(x*1024)/1024 for x in xy_unrounded(t,r,C)])
order_ok=shape_order
out=B/'models';idx=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-F.json')for x in idx['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  checktime();d=json.loads((out/f'{name}-{S}-BASE.json').read_text());d['variant']='F';gs=d['groups'];original={g['key']for g in gs if g['C0']};start=time.monotonic()
  for g in gs:g['A_ideal']=g['A'][:];g['A']=stable(g['A']);g['P']=g['A'][:]
  c0={g['key']for g in gs if any(h is not g and not apart(item(g,g['A']),item(h,h['A']))for h in gs)};assert c0==original
  found,stats=search(d,'B');d['F_search']={'beam_found':found,'beam':stats}
  if not found:
   found,stats=solve(d);d['F_search']['CSP']=stats
  d['F_search']['found']=found;d['F_compaction']=axis_compact(gs,S)if found else []
  for g in gs:
   g['leader']=any(float(p)!=a for p,a in zip(g['P'],g['A']));g['A']=[str(Decimal.from_float(a))for a in g['A']];g['P']=[str(Decimal.from_float(float(p)))for p in g['P']]
  d['elapsed_seconds_F']=time.monotonic()-start;file=f'{name}-{S}-F.json';write(out/file,d);idx['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',idx)
  print('V3_FINAL',file,'found',found,'seconds',round(d['elapsed_seconds_F'],2),flush=True)
print('V3_FINAL_COMPLETE cells=12')
