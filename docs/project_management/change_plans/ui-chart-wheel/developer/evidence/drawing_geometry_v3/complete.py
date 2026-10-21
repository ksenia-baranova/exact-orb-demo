"""Try the alternate CSP seed only where a prior geometry-valid seed is not tight."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast,struct
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());third=json.loads((B/'spec_C.json').read_text());deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
assert not (B/'spec_H.json').exists()
proposal={'variant':'H','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'G is tight in10/12 cells; six remaining labels all in720px cells require a different seed, not loosening constraints','construction':'retain G if all directional certificates exist; otherwise run alternative precision-aware CSP seed with per-distance15000-node stop continuing to next distance cap while total15s/cell remains; same exact-contact compaction/repair; choose fewer unproved groups then lower max displacement','unchanged':'all spec_F/G precision/C0/annuli/clip/gap/font/order/source/physical-reference constraints; no product fallback','stop':'one alternative seed per unresolved cell then stop irrespective of outcome; parent90min, no further iterations','production':'research candidate only; independent rational and fresh native verification required'}
(B/'spec_H.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def loaddefs(name):
 text=(B/name).read_text(encoding='utf-8');exec(compile(ast.Module(body=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)],type_ignores=[]),name+' definitions','exec'),globals())
loaddefs('build.py');loaddefs('stable.py');loaddefs('contacts.py');order_ok=shape_order
raw=(B/'csp.py').read_text(encoding='utf-8');old="except TimeoutError:stats.append({'cap':cap,'nodes':nodes,'result':'BOUNDED_STOP','wall_seconds':time.monotonic()-cellstart});return False,stats"
assert old in raw
raw=raw.replace(old,"except TimeoutError:\n   stats.append({'cap':cap,'nodes':nodes,'result':'PER_DISTANCE_BOUNDED_STOP','wall_seconds':time.monotonic()-cellstart})\n   if time.monotonic()-cellstart>third['wall_cap_per_cell_seconds']:return False,stats\n   continue")
exec(compile(ast.Module(body=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'CSP next-distance bounded policy','exec'),globals())
xy_original=xy
def xy(t,r,C):return stable([round(x*1024)/1024 for x in xy_original(t,r,C)])
def finish(d):
 gs=d['groups'];S=d['size'];d['H_axis_compaction']=axis_compact(gs,S);d['H_contact_repairs']=repair(gs,S);d['H_remaining']=[g['key']for g in gs if not isdefault(g)and not guards(g,gs)]
 return d
def score(d):
 gs=d['groups'];remaining=sum(not isdefault(g)and not guards(g,gs)for g in gs)
 dist=[math.hypot(float(g['P'][0])-float(g['A'][0]),float(g['P'][1])-float(g['A'][1]))for g in gs]
 return (remaining,max(dist,default=0),sum(dist))
out=B/'models';idx=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-H.json')for x in idx['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  checktime();d=json.loads((out/f'{name}-{S}-G.json').read_text());d['variant']='H';start=time.monotonic()
  for g in d['groups']:g['A']=list(map(float,g['A']));g['P']=list(map(float,g['P']))
  if score(d)[0]:
   alternate=json.loads(json.dumps(d))
   for g in alternate['groups']:g['P']=g['A'][:]
   found,stats=solve(alternate);d['H_alternative_search']={'found':found,'stages':stats}
   if found:
    alternate=finish(alternate);alternate['H_alternative_search']=d['H_alternative_search']
    if score(alternate)<score(d):d=alternate;d['H_selected_seed']='alternate_CSP'
  d['H_remaining']=[g['key']for g in d['groups']if not isdefault(g)and not guards(g,d['groups'])];assert allvalid(d['groups'],S,set())
  for g in d['groups']:g['leader']=g['P']!=g['A'];g['A']=[str(Decimal.from_float(a))for a in g['A']];g['P']=[str(Decimal.from_float(p))for p in g['P']]
  d['elapsed_seconds_H']=time.monotonic()-start;file=f'{name}-{S}-H.json';write(out/file,d);idx['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',idx)
  print('V3_COMPLETE',file,'remaining',len(d['H_remaining']),'seconds',round(d['elapsed_seconds_H'],2),'alternate',d.get('H_alternative_search'),flush=True)
print('V3_H_COMPLETE cells=12')
