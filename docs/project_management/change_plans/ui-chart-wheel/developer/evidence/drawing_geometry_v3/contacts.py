"""Certificate-preserving local axis-contact repair, no acceptance relaxation."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast,struct
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
assert not (B/'spec_G.json').exists()
proposal={'variant':'G','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'F removes collisions/precision failures but12 moved labels lack exact directional compactness','construction':'local certificate-preserving axis contacts; only original C0, preserve all previously tight groups; propagate one axis along its exact-contact dependency component when needed, then verify every geometric constraint','bound':'max8px per coordinate correction from current F; <=25 successful repairs/cell; no extra retries after fixed-point/no candidate','objective':'choose feasible correction closest to current placement; exact local tightness only, no global optimality claim; total displacement may rise slightly','unchanged':'same physical reference, C0, true anchors/DTO/order/clip/annuli/16/12/gap2/passive SVG; zero tolerance, float32-exact coordinates','verification':'separate Fraction verifier and new browser-run03; no inherited F PASS by assertion'}
(B/'spec_G.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def loaddefs(name):
 code=(B/name).read_text(encoding='utf-8');exec(compile(ast.Module(body=[n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)],type_ignores=[]),name+' definitions','exec'),globals())
loaddefs('build.py');loaddefs('stable.py');order_ok=shape_order
def guards(g,gs):
 P=list(map(float,g['P']));A=list(map(float,g['A']));v=[A[i]-P[i]for i in [0,1]];found=[]
 for h in gs:
  if h is g:continue
  for a in bxs(g):
   for b in bxs(h):
    for axis in [0,1]:
     k=1-axis
     if max(a[k],b[k])>=min(a[k+2],b[k+2]):continue
     if (a[axis]-b[axis+2]==2 and v[axis]<0)or(b[axis]-a[axis+2]==2 and v[axis]>0):found.append((axis,h['key']))
 return found
def isdefault(g):return g['P']==g['A']
def component(key,axis,links):
 out={key};todo=[key]
 while todo:
  current=todo.pop()
  for nxt in links[axis].get(current,[]):
   if nxt not in out:out.add(nxt);todo.append(nxt)
 return out
def allvalid(gs,S,protected):
 if not order_ok(gs,S):return False
 for i,g in enumerate(gs):
  if not domain(g,g['P'],S):return False
  for h in gs[i+1:]:
   if not apart(item(g,g['P']),item(h,h['P'])):return False
 for g in gs:
  if g['key']in protected and not isdefault(g)and not guards(g,gs):return False
 return True
def repair(gs,S):
 history=[];bykey={g['key']:g for g in gs}
 for turn in range(25):
  checktime();protected={g['key']for g in gs if isdefault(g)or guards(g,gs)};pending=[g for g in gs if g['C0']and g['key']not in protected]
  if not pending:break
  links=[{},{}]
  for g in gs:
   proof=guards(g,gs)
   if not proof:continue
   axis,other=proof[0]
   links[axis].setdefault(g['key'],set()).add(other);links[axis].setdefault(other,set()).add(g['key'])
  successful=False
  for g in pending:
   old={h['key']:h['P'][:]for h in gs};P=g['P'];best=None
   comps=[component(g['key'],axis,links)for axis in [0,1]]
   locked=[any(not bykey[k]['C0']or isdefault(bykey[k])for k in comp)for comp in comps]
   # Increasing radii are search effort only; all candidates still use exact gap2.
   for radius in [1,4,8]:
    for h in gs:
     if h is g:continue
     for a in g['components']:
      for b in h['components']:
       for axis in [0,1]:
        orth=1-axis
        if locked[axis]or h['key']in comps[axis]:continue
        for sign in [-1,1]:
         if sign==1:target=h['P'][axis]+b[axis+2]+2-a[axis]
         else:target=h['P'][axis]+b[axis]-2-a[axis+2]
         delta=target-P[axis]
         if abs(delta)>radius:continue
         options=[0]if locked[orth]else sorted({0,*[k/4 for k in range(-radius*4,radius*4+1)]},key=abs)
         for dy in options:
          score=(delta*delta*len(comps[axis])+dy*dy*len(comps[orth]))
          if best is not None and score>=best[0]:continue
          touched=comps[axis]|comps[orth]
          for key in touched:
           q=old[key][:]
           if key in comps[axis]:q[axis]=f32(q[axis]+delta)
           if key in comps[orth]:q[orth]=f32(q[orth]+dy)
           bykey[key]['P']=q
          if guards(g,gs)and allvalid(gs,S,protected):best=(score,{key:bykey[key]['P'][:]for key in touched})
          for key in touched:bykey[key]['P']=old[key][:]
    if best is not None:break
   if best is not None:
    for key,p in best[1].items():bykey[key]['P']=p
    history.append({'target':g['key'],'protected_before':len(protected),'correction_score':best[0],'changed_keys':sorted(best[1])});successful=True;break
  if not successful:history.append({'stop':'no certificate-preserving candidate within8px','remaining':[g['key']for g in pending]});break
 return history
out=B/'models';idx=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-G.json')for x in idx['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  checktime();d=json.loads((out/f'{name}-{S}-F.json').read_text());d['variant']='G';gs=d['groups'];start=time.monotonic()
  for g in gs:g['A']=list(map(float,g['A']));g['P']=list(map(float,g['P']))
  d['G_repairs']=repair(gs,S);d['G_remaining']=[g['key']for g in gs if not isdefault(g)and not guards(g,gs)]
  assert allvalid(gs,S,{g['key']for g in gs if not g['key']in d['G_remaining']})
  for g in gs:g['leader']=g['P']!=g['A'];g['A']=[str(Decimal.from_float(a))for a in g['A']];g['P']=[str(Decimal.from_float(p))for p in g['P']]
  d['elapsed_seconds_G']=time.monotonic()-start;file=f'{name}-{S}-G.json';write(out/file,d);idx['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',idx)
  print('V3_CONTACT',file,'remaining',len(d['G_remaining']),'time',round(d['elapsed_seconds_G'],3),'repairs',len(d['G_repairs']),flush=True)
print('V3_CONTACT_COMPLETE cells=12')
