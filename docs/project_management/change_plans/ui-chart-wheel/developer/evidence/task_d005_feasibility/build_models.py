"""One deterministic construction. Independent verifier does not import this module."""
from pathlib import Path
import datetime,hashlib,json,math
BASE=Path(__file__).parent
OLD=BASE.parent/'task_d003_research'
spec=json.loads((BASE/'model_spec.json').read_text(encoding='utf-8'))
fixtures=json.loads((OLD/'fixtures_v2.json').read_text(encoding='utf-8'))
def gap(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def shifted(rect,p):return [rect[0]+p[0],rect[1]+p[1],rect[2]+p[0],rect[3]+p[1]]
def allboxes(g,default=False):return [shifted(b,g['A']if default else g['P'])for b in g['components']]
def mingap(a,b,default=False):return min(gap(x,y)for x in allboxes(a,default)for y in allboxes(b,default))
def xy(theta,r,C):return [C-r*math.cos(theta),C+r*math.sin(theta)]
def pointtheta(p,C):return math.atan2(p[1]-C,C-p[0])%(2*math.pi)
def rect(x):return [x['left'],x['top'],x['right'],x['bottom']]
def make(name,S):
 chart=fixtures[name];old=json.loads((OLD/f'run03/{name}-1440-default.json').read_text(encoding='utf-8'))['measurement']
 C=S/2;groups=[];origin=chart['angles']['asc']['longitude']if chart['kind']=='natal'else 0
 for source in old['groups']:
  kind=source['kind'];radius=S*spec['F'][kind+'_radius_ratio'];theta=source['defaultTheta']%(2*math.pi)
  components=[rect(b)for b in source['components']]
  # Selected contour is included for points as well, unlike the old point default.
  ink=rect(source['metrics'][0]['ink']);selected=[ink[0]-.75,ink[1]-.75,ink[2]+.75,ink[3]+.75]
  if selected not in components:components.append(selected)
  groups.append({'key':source['key'],'kind':kind,'index':source['index'],'theta0':theta,'theta':theta,'r':radius,'A':xy(theta,radius,C),'P':xy(theta,radius,C),'components':components,'metrics':source['metrics'],'annulus':[S*x for x in spec['F'][kind+'_annulus']]})
 if chart.get('angles'):
  for i,(key,angle)in enumerate(chart['angles'].items()):
   source=next(x for x in old['obstacles']if x['key']==key);oldp=xy((angle['longitude']-origin)*math.pi/180,720*.13,360)
   b=source['boxes'][0];local=[b['left']-oldp[0],b['top']-oldp[1],b['right']-oldp[0],b['bottom']-oldp[1]]
   theta=((angle['longitude']-origin)*math.pi/180)%(2*math.pi);radius=S*spec['F']['angle_radius_ratio']
   groups.append({'key':'angle:'+key,'kind':'angle','index':i,'theta0':theta,'theta':theta,'r':radius,'A':xy(theta,radius,C),'P':xy(theta,radius,C),'components':[local],'metrics':[],'annulus':[0,S*.25]})
 C0={g['key']for g in groups if any(h is not g and mingap(g,h,True)<2 for h in groups)}
 notes=[];orders={}
 for kind in ['point','marker','angle']:
  gs=[g for g in groups if g['kind']==kind]
  if not gs:continue
  gs.sort(key=lambda g:(g['theta0'],g['index']))
  largest=max(range(len(gs)),key=lambda i:((gs[(i+1)%len(gs)]['theta0']-gs[i]['theta0'])%(2*math.pi),-i))
  gs=gs[largest+1:]+gs[:largest+1];seam=gs[0]['theta0']
  ts=[(g['theta0']-seam)%(2*math.pi)+seam for g in gs]
  hs=[]
  for g in gs:
   rho=max(math.hypot(x,y)for b in g['components']for x in [b[0],b[2]]for y in [b[1],b[3]])
   ratio=(rho+1)/g['r']
   if ratio>=1:notes.append({'key':g['key'],'kind':'circumdisk_construction_not_applicable','ratio':ratio})
   hs.append(math.asin(min(1,ratio)))
  for _ in range(spec['limits']['projection_sweeps']):
   for i in range(len(gs)):
    j=(i+1)%len(gs);right=ts[j]+(2*math.pi if j==0 else 0);deficit=hs[i]+hs[j]-(right-ts[i])
    if deficit<=0:continue
    l=gs[i]['key']in C0;r=gs[j]['key']in C0
    if l and r:ts[i]-=deficit/2;ts[j]+=deficit/2
    elif l:ts[i]-=deficit
    elif r:ts[j]+=deficit
  orders[kind]={'seam':seam,'keys':[g['key']for g in gs],'original_unwrapped':[g['theta0']for g in gs]}
  for g,t in zip(gs,ts):
   if g['key']in C0:g['theta']=t;g['P']=xy(t,g['r'],C)
 for g in groups:g['C0']=g['key']in C0;g['leader']=g['P']!=g['A']
 return {'fixture':name,'size':S,'C':[C,C],'clip':[0,0,S,S],'origin':origin,'groups':groups,'orders':orders,'construction_notes':notes,'chart':chart}
out=BASE/'analytic';out.mkdir(exist_ok=True)
index={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'spec_sha256':hashlib.sha256((BASE/'model_spec.json').read_bytes()).hexdigest(),'cells':[]}
for name in spec['fixtures']:
 for viewport,S in spec['viewport_to_frame'].items():
  model=make(name,S)
  for variant in ['F','E']:
   cell=json.loads(json.dumps(model));cell['variant']=variant;cell['viewport']=int(viewport)
   for g in cell['groups']:
    if g['kind']=='angle':continue
    x,y=g['P'];dx=x-S/2;dy=y-S/2;norm=math.hypot(dx,dy);offset=0 if variant=='F'else 12
    hx=x+offset*dx/norm;hy=y+offset*dy/norm
    g['Q']=[hx-22,hy-22,hx+22,hy+22]
    g['T']=[g['Q']]+allboxes(g)
   file=f'{name}-{S}-{variant}.json';(out/file).write_text(json.dumps(cell,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   index['cells'].append({'fixture':name,'size':S,'viewport':int(viewport),'variant':variant,'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()})
(out/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print('D005_MODEL_BUILD cells='+str(len(index['cells']))+' spec='+index['spec_sha256']+' no_parameter_tuning=true')
