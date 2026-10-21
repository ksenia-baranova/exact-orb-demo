"""Independent rendered bbox/house/source audit, without importing runtime layout."""
from pathlib import Path
from fractions import Fraction as F
import json,math,sys,hashlib
B=Path(__file__).resolve().parent
raw=json.loads((B/sys.argv[1]/'actual.json').read_text(encoding='utf8'))
def gap(a,b):
 dx=max(F(a[0])-F(b[2]),F(b[0])-F(a[2]),0);dy=max(F(a[1])-F(b[3]),F(b[1])-F(a[3]),0)
 return dx*dx+dy*dy
assert gap([0,0,10,10],[12,0,20,10])==4
assert gap([0,0,10,10],[11,11,20,20])<4
assert gap([0,0,10,10],[13,14,20,20])==25
results=[]
max_anchor_error=0
assert math.dist([0,0],[.5,0])<=.5
assert math.dist([0,0],[.500001,0])>.5
for case in raw['cases']:
 a=case['actual'];assert case['pass'] and a['svg'],case['id']; chart=case['chart'];groups=a['groups'];C=a['frame']['C'];R=a['frame']['R']; errors=[]
 def check(v,label):
  if not v:errors.append(label)
 for i,g in enumerate(groups):
  for h in groups[i+1:]:
   for b in g['parts']:
    for c in h['parts']:check(gap(b,c)>=F('3.99999999'),'gap:'+g['key']+':'+h['key'])
  for b in g['parts']:check(b[0]>=0 and b[1]>=0 and b[2]<=a['width'] and b[3]<=a['height'],'clipping:'+g['key'])
  if g['kind']!='point':continue
  source=next(p for p in chart['points'] if p['id']==g['key']); check(g['house']==str(source['house']) if source['house'] is not None else g['house']=='none','published-house')
  if chart['kind']=='natal':
   houses=sorted(chart['houses'],key=lambda h:h['number']);idx=next(i for i,h in enumerate(houses) if h['number']==source['house']);start=houses[idx]['cusp_longitude'];end=houses[(idx+1)%len(houses)]['cusp_longitude'];span=(end-start)%360
   for b in g['parts']:
    for x,y in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]:
     lng=(chart['angles']['asc']['longitude']+math.degrees(math.atan2(y-C[1],C[0]-x)))%360
     check((lng-start)%360<span,'house-bounds:'+g['key'])
  anchor=next(v for v in a['anchors'] if v['key']==g['key'])['box'];lng=source['longitude'];origin=chart['angles']['asc']['longitude'] if chart['kind']=='natal' else 0;t=math.radians(lng-origin)
  expected=[C[0]-(R-31)*math.cos(t),C[1]+(R-31)*math.sin(t)]
  error=math.dist([(anchor[0]+anchor[2])/2,(anchor[1]+anchor[3])/2],expected);max_anchor_error=max(max_anchor_error,error)
  check(error<=.5,'true-anchor:'+g['key'])
 check(not any(l['key'] in {p['id'] for p in chart['points']} for l in a['leaders']),'no-point-leaders')
 # All aspect chord endpoints retain source longitude, independent of displayed glyph offsets.
 endpoint={p['id']:p['longitude'] for p in chart['points']};endpoint.update({k:v['longitude'] for k,v in (chart['angles'] or {}).items()})
 for line in a['lines']:
  pair=json.loads(line['key']);source=next(x for x in chart['aspects'] if sorted([x['from'],x['to']])==pair[:2] and x['type']==pair[2])
  for coords,key in [(line['from'],source['from']),(line['to'],source['to'])]:
   x,y=map(float,coords);lng=(origin+math.degrees(math.atan2(y-C[1],C[0]-x)))%360
   check(abs((lng-endpoint[key]+180)%360-180)<.00001,'aspect-endpoint')
 results.append({'id':case['id'],'pass':not errors,'errors':errors,'rows':sorted({int(g['row']) for g in groups if g['kind']=='point'})})
root=B.parents[6];sources={f:hashlib.sha256((root/'src/exact_orb/http_api/ui'/f).read_text(encoding='utf8').replace('\r\n','\n').encode()).hexdigest() for f in raw['sources']}
assert sources==raw['sources'],'stale source fingerprints'
out={'cases':results,'controls':5,'max_anchor_error_css_px':max_anchor_error,'source_fingerprints_match':True};(B/(sys.argv[1]+'-audit.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
for result in results:
 if not result['pass']:print(result)
print('HOUSE_ROWS_AUDIT',sum(r['pass'] for r in results),'/',len(results),'controls=5 max_anchor_error='+str(max_anchor_error))
assert all(r['pass'] for r in results)
