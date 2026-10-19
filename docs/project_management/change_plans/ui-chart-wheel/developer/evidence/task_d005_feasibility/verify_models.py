"""Independent Fraction geometry; consumes records, never imports/calls placement."""
from fractions import Fraction as F
from pathlib import Path
from math import isqrt,atan2,pi,hypot,cos,sin
import hashlib,json
B=Path(__file__).parent
def f(x):return F(str(x))
def rect(r):return tuple(map(f,r))
def boxes(g,at=None):
 p=list(map(f,at or g['P']))
 return [(a+p[0],b+p[1],c+p[0],d+p[1])for a,b,c,d in map(rect,g['components'])]
def gap2(a,b):return max(a[0]-b[2],b[0]-a[2],0)**2+max(a[1]-b[3],b[1]-a[3],0)**2
def overlap(a,b):return max(a[0],b[0])<min(a[2],b[2])and max(a[1],b[1])<min(a[3],b[3])
def inside(a,b):return a[0]>=b[0]and a[1]>=b[1]and a[2]<=b[2]and a[3]<=b[3]
def radial_range(a,C):
 lo=max(a[0]-C[0],C[0]-a[2],0)**2+max(a[1]-C[1],C[1]-a[3],0)**2
 hi=max((x-C[0])**2+(y-C[1])**2 for x in [a[0],a[2]]for y in [a[1],a[3]])
 return lo,hi
def minimum_piecewise_squared(xlines,ylines,end):
 # Each component distance is max of finitely many affine expressions.
 if end==0:return max(a for a,b in xlines)**2+max(a for a,b in ylines)**2,F(0)
 cuts={F(0),end}
 for lines in [xlines,ylines]:
  for i,(a,b)in enumerate(lines):
   for c,d in lines[i+1:]:
    if b!=d:
     u=(c-a)/(b-d)
     if 0<u<end:cuts.add(u)
 cuts=sorted(cuts);best=None
 for l,r in zip(cuts,cuts[1:]):
  m=(l+r)/2;xa,xb=max(xlines,key=lambda z:z[0]+z[1]*m);ya,yb=max(ylines,key=lambda z:z[0]+z[1]*m)
  aa=xb*xb+yb*yb;bb=2*(xa*xb+ya*yb);cc=xa*xa+ya*ya
  candidates=[l,r]
  if aa and l<=-bb/(2*aa)<=r:candidates.append(-bb/(2*aa))
  for u in candidates:
   v=aa*u*u+bb*u+cc
   if best is None or v<best[0]:best=(v,u)
 return best or(F(0),F(0))
def min_moving_gap(a,b,v,end):
 return minimum_piecewise_squared([(a[0]-b[2],v[0]),(b[0]-a[2],-v[0]),(F(0),F(0))],[(a[1]-b[3],v[1]),(b[1]-a[3],-v[1]),(F(0),F(0))],end)
def prefix(g,others,C,clip,end):
 v=[f(g['A'][i])-f(g['P'][i])for i in [0,1]];rs=boxes(g);r0,r1=map(f,g['annulus'])
 for a in rs:
  dest=(a[0]+end*v[0],a[1]+end*v[1],a[2]+end*v[0],a[3]+end*v[1])
  if not inside(a,clip)or not inside(dest,clip):return False,{'predicate':'clip','u':str(end)}
  low,u=minimum_piecewise_squared([(a[0]-C[0],v[0]),(C[0]-a[2],-v[0]),(F(0),F(0))],[(a[1]-C[1],v[1]),(C[1]-a[3],-v[1]),(F(0),F(0))],end)
  if low<r0*r0 or max(radial_range(a,C)[1],radial_range(dest,C)[1])>r1*r1:return False,{'predicate':'annulus','u':str(u)}
  for h in others:
   for b in boxes(h):
    val,u=min_moving_gap(a,b,v,end)
    if val<4:return False,{'predicate':'gap','other':h['key'],'gap2':str(val),'u':str(u)}
 # A chord can cross a frozen neighbor ray only at a root of the affine cross product.
 p=[f(g['P'][i])-C[i]for i in [0,1]]
 for h in others:
  if h['kind']!=g['kind']:continue
  n=[f(h['P'][i])-C[i]for i in [0,1]];a=p[0]*n[1]-p[1]*n[0];b=v[0]*n[1]-v[1]*n[0]
  if a==0:return None,{'predicate':'order_tie','other':h['key']}
  if b:
   u=-a/b
   if 0<u<end and (p[0]+u*v[0])*n[0]+(p[1]+u*v[1])*n[1]>0:return False,{'predicate':'cyclic_order','other':h['key'],'u':str(u)}
 return True,{'predicate':'whole_prefix_gap_annulus_clip_order','u':str(end)}
def local(g,gs,C,clip):
 v=[f(g['A'][i])-f(g['P'][i])for i in [0,1]];d2=sum(z*z for z in v)
 if not d2:return {'key':g['key'],'displacement':0,'step':'N/A','tight':'N/A'}
 others=[h for h in gs if h is not g]
 initial,why=prefix(g,others,C,clip,F(0))
 if not initial:return {'key':g['key'],'step':'N/A_INITIAL_INVALID','tight':'N/A_INITIAL_INVALID','detail':why}
 scale=10**30;k=isqrt(d2.numerator*scale*scale//d2.denominator);dl=F(k,scale);du=F(k+1,scale)
 low=F(1)if d2<=1 else 1/du;high=F(1)if d2<=1 else 1/dl
 lp,lwhy=prefix(g,others,C,clip,low);hp,hwhy=prefix(g,others,C,clip,high)
 step='LOCAL_STEP_PASS'if lp is False else 'LOCAL_STEP_FAIL'if hp is True else 'LOCAL_STEP_UNPROVEN'
 # An exact rational parameter with distance <=1 proves an admissible positive prefix.
 witness=min(F(1,2),1/(2*du));wp,wwhy=prefix(g,others,C,clip,witness)
 tight='LOCAL_TIGHT_FAIL'if wp is True else 'LOCAL_TIGHT_UNPROVEN'
 return {'key':g['key'],'displacement_interval':[str(dl),str(du)],'step':step,'step_parameter_interval':[str(low),str(high)],'step_detail':lwhy if lp is False else hwhy,'tight':tight,'positive_prefix_parameter':str(witness)if wp is True else None,'witness_distance_squared':str(d2*witness*witness)if wp is True else None,'prefix_detail':wwhy}
controls=[]
def control(name,actual,expected):
 assert actual==expected,(name,actual,expected);controls.append({'id':name,'actual':actual,'expected':expected})
control('diagonal-gap-equality',gap2(rect([0,0,10,10]),rect(['11.2','11.6','12.2','12.6']))==4,True)
control('diagonal-gap-below',gap2(rect([0,0,10,10]),rect(['11.19','11.6','12.2','12.6']))>=4,False)
control('zero-prefix-keeps-initial-gap',min_moving_gap(rect([18,0,34,16]),rect([0,0,16,16]),[F(-1),F(0)],F(0))[0]==4,True)
control('clipped44-negative',inside(rect([-1,0,43,44]),rect([0,0,100,100])),False)
control('intact44-boundary',inside(rect([0,0,44,44]),rect([0,0,44,44])),True)
for x,expected in [(18,False),(19,True),(20,True)]:
 control('local-horizontal-'+str(x),min_moving_gap(rect([x,0,x+16,16]),rect([0,0,16,16]),[F(-1),F(0)],F(1))[0]>=4,expected)
control('fraction-prefix-positive',min_moving_gap(rect(['18.5',0,'34.5',16]),rect([0,0,16,16]),[F(-1),F(0)],F(1,2))[0]>=4,True)
packing=[]
for S in [720,448,328]:
 n=S//44;qs=[(F(x*44),F(y*44),F(x*44+44),F(y*44+44))for y in range(n)for x in range(n)]
 assert all(inside(q,(0,0,S,S))for q in qs)
 assert all(not overlap(q,r)for i,q in enumerate(qs)for r in qs[i+1:])
 packing.append({'frame':S,'rectangles':n*n,'lower_bound_only':True,'square_xywh':[[int(q[0]),int(q[1]),44,44]for q in qs],'model':'unconstrained clip rectangle only; NOT actual glyph positions or wheel annuli; not optimum/continuous upper bound'})
idx=json.loads((B/'analytic/index.json').read_text());results=[]
for ref in idx['cells']:
 raw=(B/'analytic'/ref['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256']
 d=json.loads(raw);gs=d['groups'];C=list(map(f,d['C']));clip=rect(d['clip']);errors=[]
 defaults={g['key']:boxes(g,g['A'])for g in gs}
 c0={g['key']for g in gs if any(h is not g and min(gap2(a,b)for a in defaults[g['key']]for b in defaults[h['key']])<4 for h in gs)}
 if c0!={g['key']for g in gs if g['C0']}:errors.append({'predicate':'C0','expected':sorted(c0)})
 for i,g in enumerate(gs):
  if not g['C0']and g['P']!=g['A']:errors.append({'predicate':'frozen','key':g['key']})
  r0,r1=map(f,g['annulus'])
  for a in boxes(g):
   if not inside(a,clip):errors.append({'predicate':'clip','key':g['key'],'bounds':list(map(str,a))})
   lo,hi=radial_range(a,C)
   if lo<r0*r0 or hi>r1*r1:errors.append({'predicate':'annulus','key':g['key'],'min2':str(lo),'max2':str(hi),'radii':[str(r0),str(r1)]})
  for h in gs[i+1:]:
   v=min(gap2(a,b)for a in boxes(g)for b in boxes(h))
   if v<4:errors.append({'predicate':'gap','left':g['key'],'right':h['key'],'gap2':str(v)})
 for kind,order in d['orders'].items():
  subset=[g for g in gs if g['kind']==kind];seam=order['seam']
  ranked=sorted(subset,key=lambda g:((atan2(g['P'][1]-float(C[1]),float(C[0])-g['P'][0])-seam)%(2*pi),g['index']))
  expected=order['keys'];actual=[g['key']for g in ranked]
  # Compare cyclic sequences independent of which member lands exactly on the seam.
  good=any(actual==expected[k:]+expected[:k]for k in range(len(expected)))
  if not good:errors.append({'predicate':'cyclic_order','kind':kind,'actual':actual,'expected_cyclic':expected})
 targets=[g for g in gs if g['kind']!='angle'];hit=[]
 native={}
 for g in targets:
  # Q is specified by left/top plus native width/height=44; rounded right/bottom are diagnostic only.
  x,y=map(f,g['Q'][:2]);q=(x,y,x+44,y+44);native[g['key']]=[q]+boxes(g)
 for i,g in enumerate(targets):
  q=native[g['key']][0];block=[]
  for h in targets[i+1:]:
   if any(overlap(q,t)for t in native[h['key']]):block.append(h['key'])
  good=inside(q,clip)and not block
  hit.append({'key':g['key'],'Q_xywh':[str(q[0]),str(q[1]),'44','44'],'clip_contained':inside(q,clip),'later_target_occluders':block,'conditional_rectangle_certificate':good,'scope':'declared rectangle union and paint order; native browser confirmation separate'})
 anchors=[]
 for g in gs:
  if g['kind']=='point':lng=next(p['longitude']for p in d['chart']['points']if p['id']==g['key'])
  elif g['kind']=='angle':lng=d['chart']['angles'][g['key'].split(':')[1]]['longitude']
  else:
   left,right,_=json.loads(g['key']);ends={p['id']:p['longitude']for p in d['chart']['points']}|{k:p['longitude']for k,p in(d['chart'].get('angles')or{}).items()};delta=(ends[right]-ends[left]+540)%360-180
   if delta==-180:delta=180
   lng=ends[left]+delta/2
  angle=(lng-d['origin'])*pi/180;expected=[float(C[0])-g['r']*cos(angle),float(C[1])+g['r']*sin(angle)]
  anchors.append({'key':g['key'],'error':hypot(expected[0]-g['A'][0],expected[1]-g['A'][1]),'pass':hypot(expected[0]-g['A'][0],expected[1]-g['A'][1])<=.5})
 loc=[local(g,gs,C,clip)for g in gs]
 results.append({'fixture':d['fixture'],'frame':d['size'],'variant':d['variant'],'source':ref['file'],'C0':len(c0),'moved':sum(g['leader']for g in gs),'static_visual_pass':not errors,'counterexamples':errors,'anchors':anchors,'hit':hit,'local_return':loc,'all_predicates_pass':not errors and all(h['conditional_rectangle_certificate']for h in hit)and all(a['pass']for a in anchors)and all(x['tight']in['N/A','LOCAL_TIGHT_PASS']for x in loc),'conclusion':'bounded construction only; failures are not product impossibility'})
out={'spec_sha256':idx['spec_sha256'],'controls':controls,'unconstrained_Q_packing':packing,'cells':results,'summary':{'cells':len(results),'static_visual_pass':sum(r['static_visual_pass']for r in results),'all_predicates_pass':sum(r['all_predicates_pass']for r in results),'independent_controls':len(controls)}}
(B/'analytic/verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('D005_ANALYTIC_VERIFIED '+json.dumps(out['summary']))
for r in results:print(r['fixture'],r['frame'],r['variant'],'visual='+str(r['static_visual_pass']),'Q='+str(sum(x['conditional_rectangle_certificate']for x in r['hit']))+'/'+str(len(r['hit'])),'errors='+str(len(r['counterexamples'])))
