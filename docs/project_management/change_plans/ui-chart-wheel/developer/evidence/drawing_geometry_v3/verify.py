"""Exact independent predicates: reads output only, never imports placement."""
from pathlib import Path
from fractions import Fraction as F
from math import isqrt,atan2,pi,hypot,cos,sin
import json,hashlib,ast
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
# Reuse only the published, independent D005 rational verifier definitions.
# AST extraction avoids its top-level runs/writes and records their provenance.
source=(B.parent/'task_d005_feasibility/verify_models.py').read_text(encoding='utf-8')
functions=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)]
exec(compile(ast.Module(body=functions,type_ignores=[]),'published_D005_verifier_functions','exec'))
def exact_contact(g,others):
 v=[f(a)-f(p)for a,p in zip(g['A'],g['P'])]
 for h in others:
  for a in boxes(g):
   for b in boxes(h):
    for axis in [0,1]:
     k=1-axis
     if max(a[k],b[k])>=min(a[k+2],b[k+2]):continue
     distance=a[axis]-b[axis+2]
     if distance==2 and v[axis]<0:return {'predicate':'axis_gap2_contact_closing','other':h['key'],'axis':axis,'signed_velocity':str(v[axis])}
     distance=b[axis]-a[axis+2]
     if distance==2 and v[axis]>0:return {'predicate':'axis_gap2_contact_closing','other':h['key'],'axis':axis,'signed_velocity':str(v[axis])}
 return None
checks=[]
def ctl(id,actual,expected):
 assert actual==expected,(id,actual,expected);checks.append({'id':id,'actual':actual,'expected':expected})
ctl('diagonal-gap-equality',gap2(rect([0,0,10,10]),rect(['11.2','11.6','12.2','12.6']))==4,True)
ctl('diagonal-gap-below',gap2(rect([0,0,10,10]),rect(['11.19','11.6','12.2','12.6']))>=4,False)
for x,want in [(18,False),(19,True),(20,True)]:ctl('calibration-'+str(x),min_moving_gap(rect([x,0,x+16,16]),rect([0,0,16,16]),[F(-1),F(0)],F(1))[0]>=4,want)
fake={'components':[[0,0,16,16]],'P':[18,0],'A':[0,0]};other={'key':'fixed','components':[[0,0,16,16]],'P':[0,0]}
ctl('exact-tight-positive',bool(exact_contact(fake,[other])),True)
ctl('tiny-slack-not-tight',bool(exact_contact(fake|{'P':['18.00000001',0]},[other])),False)
ctl('axis-certificate-with-unrelated-ray',bool(exact_contact(fake,[other,{'key':'opposite','components':[[0,0,1,1]],'P':[-18,0]}])),True)
ctl('clip-equality',inside(rect([0,0,44,44]),rect([0,0,44,44])),True)
ctl('clip-negative',inside(rect([-1,0,43,44]),rect([0,0,44,44])),False)
rows=[]
idx=json.loads((B/'models/index.json').read_text())
for ref in idx['records']:
 raw=(B/'models'/ref['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256'];d=json.loads(raw)
 gs=d['groups'];C=list(map(f,d['C']));clip=rect(d['clip']);errors=[];localrows=[]
 default={g['key']:boxes(g,g['A'])for g in gs}
 c0={g['key']for g in gs if any(h is not g and min(gap2(a,b)for a in default[g['key']]for b in default[h['key']])<4 for h in gs)}
 if c0!={g['key']for g in gs if g['C0']}:errors.append({'predicate':'C0_mismatch'})
 for i,g in enumerate(gs):
  if not g['C0']and list(map(f,g['P']))!=list(map(f,g['A'])):errors.append({'predicate':'frozen','key':g['key']})
  r0,r1=map(f,g['annulus'])
  for a in boxes(g):
   if not inside(a,clip):errors.append({'predicate':'clip','key':g['key']})
   lo,hi=radial_range(a,C)
   if lo<r0*r0 or hi>r1*r1:errors.append({'predicate':'annulus','key':g['key']})
  for h in gs[i+1:]:
   val=min(gap2(a,b)for a in boxes(g)for b in boxes(h))
   if val<4:errors.append({'predicate':'gap','left':g['key'],'right':h['key'],'gap2':str(val)})
 for kind in ['point','marker','angle']:
  group=[g for g in gs if g['kind']==kind]
  expected=[g['key']for g in sorted(group,key=lambda g:g['rank'])]
  actual=[g['key']for g in sorted(group,key=lambda g:((atan2(float(g['P'][1])-float(C[1]),float(C[0])-float(g['P'][0]))-g['seam'])%(2*pi),g['index']))]
  if expected and not any(actual==expected[k:]+expected[:k]for k in range(len(expected))):errors.append({'predicate':'cyclic_order','kind':kind})
 moved=[g for g in gs if list(map(f,g['P']))!=list(map(f,g['A']))]
 for g in moved:
  others=[h for h in gs if h is not g]
  proof=exact_contact(g,others)
  initial,why=prefix(g,others,C,clip,F(0))
  if not errors and proof:r={'key':g['key'],'step':'LOCAL_STEP_PASS','tight':'LOCAL_TIGHT_PASS','certificate':proof,'initial_geometry':'entire cell independently valid'}
  elif initial is not True:r={'key':g['key'],'tight':'INVALID_OR_UNPROVEN','detail':why}
  else:
   r=local(g,gs,C,clip)
   if r['tight']=='LOCAL_TIGHT_UNPROVEN':
    for u in [F(1,10**8),F(1,10**12)]:
     good,detail=prefix(g,others,C,clip,u)
     if good is True:r.update(tight='LOCAL_TIGHT_FAIL',positive_prefix_parameter=str(u),prefix_detail=detail);break
  localrows.append(r)
 displacement=[hypot(float(g['P'][0])-float(g['A'][0]),float(g['P'][1])-float(g['A'][1]))for g in gs]
 rows.append({'file':ref['file'],'fixture':d['fixture'],'frame':d['size'],'variant':d['variant'],'found':d.get('F_search',d.get('search_E',d.get('search',{}))).get('found'),'C0':len(c0),'moved':len(moved),'max_displacement':max(displacement,default=0),'sum_displacement':sum(displacement),'geometry_pass':not errors,'errors':errors,'local':localrows,'local_tight_pass':sum(r['tight']=='LOCAL_TIGHT_PASS'for r in localrows),'local_tight_fail':sum(r['tight']=='LOCAL_TIGHT_FAIL'for r in localrows),'local_tight_unproven':sum(r['tight']not in ['LOCAL_TIGHT_PASS','LOCAL_TIGHT_FAIL']for r in localrows),'full_declared_visual_pass':not errors and all(r['tight']=='LOCAL_TIGHT_PASS'for r in localrows)})
summary={v:{'cells':sum(r['variant']==v for r in rows),'geometry_pass':sum(r['variant']==v and r['geometry_pass']for r in rows),'tight_cells':sum(r['variant']==v and r['full_declared_visual_pass']for r in rows),'moved':sum(r['moved']for r in rows if r['variant']==v),'tight_pass':sum(r['local_tight_pass']for r in rows if r['variant']==v),'tight_fail':sum(r['local_tight_fail']for r in rows if r['variant']==v),'tight_unproven':sum(r['local_tight_unproven']for r in rows if r['variant']==v)}for v in sorted({r['variant']for r in rows})}
output={'source_D005_verifier_sha256':hashlib.sha256(source.encode()).hexdigest(),'controls':checks,'cells':rows,'summary':summary,'limits':'exact supplied coordinates and component rectangles only; independent browser actual follows; no global optimum'}
(B/'verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V3_EXACT_VERIFICATION',json.dumps(summary),flush=True)
for r in rows:
 if r['variant']!='BASE':print(r['file'],'geometry',r['geometry_pass'],'moved',r['moved'],'tight',r['local_tight_pass'],r['local_tight_fail'],r['local_tight_unproven'],'max',round(r['max_displacement'],3),'errors',r['errors'][:2],flush=True)
