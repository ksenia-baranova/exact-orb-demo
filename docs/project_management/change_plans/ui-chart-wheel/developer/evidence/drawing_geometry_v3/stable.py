"""Pixel-stable physical-reference alternative; not a change to engine facts."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast,struct
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());OLD=B.parent/'task_d005_feasibility/analytic';deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
assert not (B/'spec_E.json').exists()
new={'variant':'E','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'real SVG transform rounding makes exact contacts fail and flips near-collinear same-kind origins in D','reference':'physical default reference Af32 = IEEE binary32 rendering of ideal A, compared against same physical default, ideal anchor retained separately; max error <=0.5; recompute C0 and assert unchanged membership','grid':'moved seed positions quantized to 1/1024 CSS px, representable by SVG binary32 within tested frames; fixed positions remain physical default','order':'avoid nearly equal polar rays using 0.0001 rad constructive separation when repairing seed; not a new acceptance tolerance','repair':'up to48 passes; candidate grid offsets up to0.25 CSS px around an invalid group; no moving non-C0; full predicates remain strict','compression':'only exactly representable axis contacts, at most24 sweeps; no epsilon substitutes for local tightness','input':'D verified seeds; no new source fact, font/annulus/2px gap altered','browser':'integer SVG origin and 1:1 scale, record real CTM; explicit limit, not cross-platform/zoom proof','serialization':'full exact decimal spelling of binary positions; native actual verification uses exact IEEE binary64 rational, no tolerance'}
(B/'spec_E.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
defs=[n for n in ast.parse((B/'build.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=defs,type_ignores=[]),'V3_common_construction','exec'))
def f32(x):return struct.unpack('f',struct.pack('f',float(x)))[0]
def stable(p):return [f32(x)for x in p]
def shape_order(gs,S):
 for kind in ['point','marker','angle']:
  subset=[g for g in gs if g['kind']==kind]
  if not subset:continue
  expect=[g['key']for g in sorted(subset,key=lambda g:g['rank'])]
  actual=[g['key']for g in sorted(subset,key=lambda g:(ranked(g,g['P'],S),g['index']))]
  if not any(actual==expect[k:]+expect[:k]for k in range(len(expect))):return False
 return True
order_ok=shape_order
def violations(gs,S):
 bad=set()
 for i,g in enumerate(gs):
  if not domain(g,g['P'],S):bad.add(g['key'])
  for h in gs[i+1:]:
   if not apart(item(g,g['P']),item(h,h['P'])):bad.update([g['key'],h['key']])
 return bad
def fix_seed(gs,S):
 # Restore strictly ordered rays before tiny per-group gap repair.
 for kind in ['point','marker','angle']:
  seq=sorted([g for g in gs if g['kind']==kind],key=lambda g:g['rank']);last=None
  for g in seq:
   p=list(map(float,g['P']));theta=math.atan2(p[1]-S/2,S/2-p[0]);theta=g['unwrapped']+((theta-g['unwrapped']+math.pi)%(2*math.pi)-math.pi)
   if last is not None and theta<last+.0001 and g['C0']:
    theta=last+.0001;g['P']=stable(xy(theta,math.hypot(p[0]-S/2,p[1]-S/2),S/2))
   last=theta
 # Candidate construction uses a small numeric safety margin only for a seed;
 # acceptance always checks >=2, and no margin is claimed as tightness.
 log=[]
 for sweep in range(48):
  checktime();bad=violations(gs,S)
  if not bad and order_ok(gs,S):return True,log
  count=0
  for g in gs:
   if not g['C0']or g['key']not in bad:continue
   base=list(map(float,g['P']));best=None
   offsets=[0,-1/1024,1/1024,-1/512,1/512,-1/256,1/256,-1/128,1/128,-1/64,1/64,-1/32,1/32,-1/16,1/16,-1/8,1/8,-1/4,1/4]
   for dx in offsets:
    for dy in offsets:
     p=stable([base[0]+dx,base[1]+dy]);cost=sum((p[i]-base[i])**2 for i in [0,1])
     if best is not None and cost>=best[0]:continue
     if valid(g,p,gs,S):best=(cost,p)
   if best:g['P']=best[1];count+=1
  log.append({'sweep':sweep,'bad':sorted(bad),'changed':count})
  if not count:break
 return not violations(gs,S)and order_ok(gs,S),log
def axis_compact(gs,S):
 log=[]
 for sweep in range(24):
  changed=0
  for g in sorted(gs,key=lambda g:sum((float(p)-a)**2 for p,a in zip(g['P'],g['A'])),reverse=True):
   if not g['C0']:continue
   P=list(map(float,g['P']));A=g['A'];old=sum((x-a)**2 for x,a in zip(P,A))
   if not old:continue
   if valid(g,A,gs,S):g['P']=A[:];changed+=1;continue
   # Retain the first obstruction as a candidate contact neighborhood.
   n=max(1,math.ceil(math.sqrt(old)/.5));lo=0;hi=1
   for k in range(1,n+1):
    t=k/n;p=[P[i]+t*(A[i]-P[i])for i in [0,1]]
    if not valid(g,p,gs,S):hi=t;break
    lo=t
   for _ in range(30):
    t=(lo+hi)/2;p=[P[i]+t*(A[i]-P[i])for i in [0,1]]
    if valid(g,p,gs,S):lo=t
    else:hi=t
   boundary=[P[i]+lo*(A[i]-P[i])for i in [0,1]];candidate=contact_candidate(g,boundary,gs,S)
   if candidate is not None:
    p=stable(candidate)
    if valid(g,p,gs,S)and sum((p[i]-A[i])**2 for i in [0,1])<old-1e-12:g['P']=p;changed+=1
  log.append({'sweep':sweep,'changed':changed})
  if not changed:break
 return log
out=B/'models';idx=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-E.json')for x in idx['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  checktime();d=json.loads((out/f'{name}-{S}-D.json').read_text());d['variant']='E';gs=d['groups'];original={g['key']for g in gs if g['C0']};start=time.monotonic()
  for g in gs:
   g['A_ideal']=g['A'][:];g['A']=stable(g['A']);g['P']=g['A'][:]if not g['leader']else stable([round(float(x)*1024)/1024 for x in g['P']])
  c0={g['key']for g in gs if any(h is not g and not apart(item(g,g['A']),item(h,h['A']))for h in gs)};assert c0==original,(name,S,'C0 changed')
  found,repair=fix_seed(gs,S);d['search_E']={'found':found,'repair':repair};d['return_history_E']=axis_compact(gs,S)if found else []
  for g in gs:
   g['leader']=any(float(p)!=a for p,a in zip(g['P'],g['A']));g['A']=[str(Decimal.from_float(a))for a in g['A']];g['P']=[str(Decimal.from_float(float(p)))for p in g['P']]
  d['elapsed_seconds_E']=time.monotonic()-start;file=f'{name}-{S}-E.json';write(out/file,d);idx['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',idx)
  print('V3_STABLE',file,'found',found,'seconds',round(d['elapsed_seconds_E'],2),'repair',len(repair),flush=True)
print('V3_STABLE_COMPLETE cells=12')
