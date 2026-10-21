"""Bounded all-label search. Static/return certificates live in another program."""
from pathlib import Path
import json,math,hashlib,time,heapq,itertools,datetime
from decimal import Decimal
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':
 B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());OLD=B.parent/'task_d005_feasibility/analytic'
deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
def checktime():
 if time.time()>deadline:raise TimeoutError('OWNER_REWORK_TIMEBOX')
def xy(t,r,C):return [C-r*math.cos(t),C+r*math.sin(t)]
def bxs(g,p=None):
 p=list(map(float,p or g['P']));return [(a+p[0],b+p[1],c+p[0],d+p[1])for a,b,c,d in g['components']]
def env(bs):return [min(a[0]for a in bs),min(a[1]for a in bs),max(a[2]for a in bs),max(a[3]for a in bs)]
def g2(a,b):return max(a[0]-b[2],b[0]-a[2],0)**2+max(a[1]-b[3],b[1]-a[3],0)**2
def domain(g,p,S):
 C=S/2;r0,r1=g['annulus']
 for a in bxs(g,p):
  if a[0]<0 or a[1]<0 or a[2]>S or a[3]>S:return False
  lo=max(a[0]-C,C-a[2],0)**2+max(a[1]-C,C-a[3],0)**2
  hi=max((x-C)**2+(y-C)**2 for x in [a[0],a[2]]for y in [a[1],a[3]])
  if lo<r0*r0 or hi>r1*r1:return False
 return True
def apart(a,b,gap=2):
 if g2(a['box'],b['box'])>=gap*gap:return True
 return all(g2(x,y)>=gap*gap for x in a['boxes']for y in b['boxes'])
def item(g,p,t=None):
 bs=bxs(g,p);return {'g':g,'P':p,'boxes':bs,'box':env(bs),'t':t,'cost':sum((float(x)-y)**2 for x,y in zip(p,g['A']))}
def ranked(g,p,S):return (math.atan2(float(p[1])-S/2,S/2-float(p[0]))-g['seam'])%(2*math.pi)
def order_ok(gs,S):
 for kind in ['point','marker','angle']:
  gg=[g for g in gs if g['kind']==kind]
  a=[g['key']for g in sorted(gg,key=lambda g:(ranked(g,g['P'],S),g['index']))]
  e=[g['key']for g in sorted(gg,key=lambda g:g['rank'])]
  if not any(a==e[k:]+e[:k]for k in range(len(e))):return False
 return True
def valid(g,p,gs,S,margin=0):
 if not domain(g,p,S):return False
 c=item(g,p)
 if any(not apart(c,item(h,h['P']),2+margin) for h in gs if h is not g):return False
 before=g['P'];g['P']=p;good=order_ok(gs,S);g['P']=before;return good
def prep(name,S):
 d=json.loads((OLD/f'{name}-{S}-F.json').read_text());gs=d['groups']
 for g in gs:
  if g['metrics']:
   m=g['metrics'];g['components']=[[x['ink'][k]for k in ['left','top','right','bottom']]for x in m]
   a=g['components'][0];g['components'][0]=[a[0]-.75,a[1]-.75,a[2]+.75,a[3]+.75]
  g['P']=g['A'][:];g.pop('Q',None);g.pop('T',None)
 c0={g['key']for g in gs if any(h is not g and not apart(item(g,g['A']),item(h,h['A']))for h in gs)}
 for kind in ['angle','marker','point']:
  seq=sorted([g for g in gs if g['kind']==kind],key=lambda g:(g['theta0'],g['index']))
  if not seq:continue
  i=max(range(len(seq)),key=lambda i:((seq[(i+1)%len(seq)]['theta0']-seq[i]['theta0'])%(2*math.pi),-i))
  seq=seq[i+1:]+seq[:i+1];seam=seq[0]['theta0']
  for rank,g in enumerate(seq):g['rank']=rank;g['seam']=seam;g['unwrapped']=(g['theta0']-seam)%(2*math.pi)+seam
 for g in gs:g['C0']=g['key']in c0
 d['variant']='BASE';d['passive']=True;d['orders']={};return d
def search(d,variant):
 gs=d['groups'];S=d['size'];width=spec['search']['beam_width'];counter=itertools.count()
 fixed=[item(g,g['A'],g['unwrapped'])for g in gs if not g['C0']]
 movable=sorted([g for g in gs if g['C0']],key=lambda g:({'angle':0,'marker':1,'point':2}[g['kind']],g['rank']))
 beam=[(0,[],{})];stats=[]
 for g in movable:
  checktime();candidates=[]
  radii=[g['r']]if variant=='A'else [g['r'],g['r']-S*.06,g['r']+S*.06]
  for r in radii:
   if r<=0:continue
   for degree in range(-179,180):
    t=g['unwrapped']+math.radians(degree);p=xy(t,r,S/2)
    if degree==0 and r==g['r']:p=g['A'][:]
    if not domain(g,p,S):continue
    c=item(g,p,t)
    if any(not apart(c,f,2.000001)for f in fixed):continue
    # Frozen neighbors constrain this seed to the same unwrapped cycle.
    fk=[f for f in fixed if f['g']['kind']==g['kind']]
    if any((f['g']['rank']<g['rank']and f['t']>=t)or(f['g']['rank']>g['rank']and f['t']<=t)for f in fk):continue
    candidates.append(c)
  candidates.sort(key=lambda c:(c['cost'],abs(c['t']-g['unwrapped']),c['t']))
  pool=[];checked=0
  for cost,placed,last in sorted(beam,key=lambda x:x[0]):
   for c in candidates:
    total=cost+c['cost']
    if len(pool)>=width and total>-pool[0][0]:break
    t=c['t'];prev=last.get(g['kind'])
    if prev is not None and t<=prev:continue
    # Wrap consistency: no group can overtake the first assigned same-kind label.
    same=[x for x in placed if x['g']['kind']==g['kind']]
    if same and t>=same[0]['t']+2*math.pi:continue
    checked+=1
    if any(not apart(c,p,2.000001)for p in placed):continue
    state=(total,placed+[c],last|{g['kind']:t});entry=(-total,next(counter),state)
    if len(pool)<width:heapq.heappush(pool,entry)
    elif total<-pool[0][0]:heapq.heapreplace(pool,entry)
  stats.append({'key':g['key'],'candidates':len(candidates),'pair_checks':checked,'beam':len(pool)})
  if not pool:return False,stats
  beam=[entry[2]for entry in pool]
 best=min(beam,key=lambda x:x[0]);
 for c in best[1]:c['g']['P']=c['P']
 return True,stats
def contact_candidate(g,base,gs,S):
 # Seek an exactly recorded axis contact near a chord boundary. One coordinate is
 # constructed with Decimal arithmetic, avoiding a false tolerance-based certificate.
 best=None
 for h in gs:
  if h is g:continue
  hp=list(map(lambda x:Decimal(str(x)),h['P']))
  for a in g['components']:
   for b in h['components']:
    for axis in [0,1]:
     for sign in [-1,1]:
      if sign==1:q=hp[axis]+Decimal(str(b[axis+2]))+2-Decimal(str(a[axis]))
      else:q=hp[axis]+Decimal(str(b[axis]))-2-Decimal(str(a[axis+2]))
      if abs(float(q)-base[axis])>1:continue
      for delta in [0,-.25,.25,-.5,.5]:
       p=list(base);p[axis]=str(q);p[1-axis]=round((base[1-axis]+delta)*4)/4
       cost=sum((float(x)-y)**2 for x,y in zip(p,g['A']))
       if best is not None and cost>=best[0]:continue
       if not valid(g,p,gs,S):continue
       # Returning toward A must immediately close this exact gap, while the
       # other coordinate has positive overlap. Final verifier proves independently.
       av=bxs(g,p)[g['components'].index(a)];bv=bxs(h)[h['components'].index(b)]
       orth=1-axis
       if max(av[orth],bv[orth])>=min(av[orth+2],bv[orth+2]):continue
       if (g['A'][axis]-float(p[axis]))*sign>=0:continue
       best=(cost,p)
 return best[1]if best else None
def tighten(d):
 gs=d['groups'];S=d['size'];history=[]
 for sweep in range(spec['search']['return_sweeps']):
  changed=0
  for g in sorted(gs,key=lambda g:sum((float(x)-a)**2 for x,a in zip(g['P'],g['A'])),reverse=True):
   if not g['C0']or g['P']==g['A']:continue
   checktime();P=list(map(float,g['P']));A=g['A'];old=sum((x-a)**2 for x,a in zip(P,A))
   if valid(g,A,gs,S):g['P']=A[:];changed+=1;continue
   # Prefix stops at the first obstruction using 0.5px coarse steps; bisection
   # only refines that first interval. Independent verifier checks entire path.
   dist=math.sqrt(old);n=max(1,math.ceil(dist/.5));lo=0;hi=1
   for k in range(1,n+1):
    t=k/n;p=[P[i]+t*(A[i]-P[i])for i in [0,1]]
    if not valid(g,p,gs,S,1e-9):hi=t;break
    lo=t
   for _ in range(35):
    t=(lo+hi)/2;p=[P[i]+t*(A[i]-P[i])for i in [0,1]]
    if valid(g,p,gs,S,1e-9):lo=t
    else:hi=t
   proposed=[P[i]+lo*(A[i]-P[i])for i in [0,1]]
   contact=contact_candidate(g,proposed,gs,S)
   if contact is not None and sum((float(x)-a)**2 for x,a in zip(contact,A))<old:proposed=contact
   if valid(g,proposed,gs,S)and sum((float(x)-a)**2 for x,a in zip(proposed,A))<old-1e-12:g['P']=proposed;changed+=1
  history.append({'sweep':sweep,'changed':changed})
  if not changed:break
 return history
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out=B/'models';assert not out.exists();out.mkdir();index={'spec_sha256':hashlib.sha256((B/'spec.json').read_bytes()).hexdigest(),'records':[]}
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  base=prep(name,S)
  for variant in ['BASE','A','B']:
   checktime();d=json.loads(json.dumps(base));d['variant']=variant;d['viewport']=int(viewport);start=time.monotonic()
   if variant!='BASE':
    found,stats=search(d,variant);d['search']={'found':found,'stages':stats};d['return_history']=tighten(d)if found else []
   for g in d['groups']:g['leader']=any(float(x)!=a for x,a in zip(g['P'],g['A']))
   d['elapsed_seconds']=time.monotonic()-start;file=f'{name}-{S}-{variant}.json';write(out/file,d)
   index['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',index)
   print('V3_MODEL',name,S,variant,'found',d.get('search',{}).get('found'),'seconds',round(d['elapsed_seconds'],2),flush=True)
print('V3_MODELS_COMPLETE',len(index['records']))
