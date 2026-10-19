"""Third, bounded CSP alternative. No production or external solver."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());third=json.loads((B/'spec_C.json').read_text());OLD=B.parent/'task_d005_feasibility/analytic';deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
source=(B/'build.py').read_text(encoding='utf-8');defs=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=defs,type_ignores=[]),'V3_constructor_shared_functions','exec'))
def solve(d):
 gs=d['groups'];S=d['size'];moved=[g for g in gs if g['C0']];fixed=[item(g,g['P'],g['unwrapped'])for g in gs if not g['C0']]
 candidates=[]
 def ordered(a,b):
  if a['g']['kind']!=b['g']['kind']:return True
  delta=a['t']-b['t']
  return (-2*math.pi<delta<0)if a['g']['rank']<b['g']['rank']else (0<delta<2*math.pi)
 for g in moved:
  cs=[]
  for delta in [-.06,-.04,-.02,0,.02,.04,.06]:
   r=g['r']+S*delta
   if r<=0:continue
   for degree in range(-179,180):
    t=g['unwrapped']+math.radians(degree);p=g['A'][:]if delta==0 and degree==0 else xy(t,r,S/2)
    if not domain(g,p,S):continue
    c=item(g,p,t)
    if any(not ordered(c,f)or not apart(c,f,2.000001)for f in fixed):continue
    cs.append(c)
  cs.sort(key=lambda c:(c['cost'],c['t'],float(c['P'][0]),float(c['P'][1])));candidates.append(cs)
 stats=[];cellstart=time.monotonic();cache={};nodes=0
 def compat(i,ci,j):
  key=i,ci,j
  if key not in cache:
   c=candidates[i][ci];mask=0
   for cj,h in enumerate(candidates[j]):
    if ordered(c,h)and apart(c,h,2.000001):mask|=1<<cj
   cache[key]=mask
  return cache[key]
 def walk(domains,chosen):
  nonlocal nodes
  nodes+=1
  if nodes>third['node_cap_per_distance']or time.monotonic()-cellstart>third['wall_cap_per_cell_seconds']:raise TimeoutError('CSP_BOUNDED_SEARCH')
  if not domains:return chosen
  i=min(domains,key=lambda i:(domains[i].bit_count(),0 if moved[i]['kind']=='point'else 1,moved[i]['rank']))
  mask=domains[i]
  while mask:
   bit=mask&-mask;ci=bit.bit_length()-1;mask-=bit;new={};bad=False
   for j,allowed in domains.items():
    if j==i:continue
    remainder=allowed&compat(i,ci,j)
    if not remainder:bad=True;break
    new[j]=remainder
   if not bad:
    result=walk(new,chosen|{i:ci})
    if result is not None:return result
  return None
 for cap in third['displacement_caps']:
  checktime();nodes=0;domains={i:sum(1<<j for j,c in enumerate(cs)if c['cost']<=cap*cap)for i,cs in enumerate(candidates)}
  try:chosen=None if any(not mask for mask in domains.values())else walk(domains,{})
  except TimeoutError:stats.append({'cap':cap,'nodes':nodes,'result':'BOUNDED_STOP','wall_seconds':time.monotonic()-cellstart});return False,stats
  stats.append({'cap':cap,'nodes':nodes,'result':'FOUND'if chosen is not None else 'NO_DISCRETE_SOLUTION_AT_CAP','wall_seconds':time.monotonic()-cellstart})
  if chosen is not None:
   for i,ci in chosen.items():moved[i]['P']=candidates[i][ci]['P']
   return True,stats
 return False,stats
out=B/'models';index=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-C.json')for x in index['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  d=prep(name,S);d['variant']='C';d['viewport']=int(viewport);start=time.monotonic();found,stats=solve(d)
  d['search']={'found':found,'method':'CSP_MRV_forward_checking','stages':stats};d['return_history']=tighten(d)if found else []
  for g in d['groups']:g['leader']=any(float(x)!=a for x,a in zip(g['P'],g['A']))
  d['elapsed_seconds']=time.monotonic()-start;file=f'{name}-{S}-C.json';write(out/file,d)
  index['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',index)
  print('V3_CSP',file,'found',found,'time',round(d['elapsed_seconds'],2),'stages',stats,flush=True)
print('V3_CSP_COMPLETE cells=12')
