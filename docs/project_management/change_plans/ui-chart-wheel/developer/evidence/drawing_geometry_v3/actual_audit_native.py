"""Audit actual browser data with exact independent predicates; no placement."""
from pathlib import Path
from fractions import Fraction as F
from math import isqrt,atan2,pi,hypot,cos,sin
import json,hashlib,ast,copy
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
source=(B.parent/'task_d005_feasibility/verify_models.py').read_text(encoding='utf-8');exec(compile(ast.Module(body=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'published_independent_verifier','exec'))
idx=json.loads((B/'browser-run01/index.json').read_text());assert not idx.get('error');assert len(idx['records'])==60;assert all(x['actual']==x['expected']for x in idx['controls'])
# Native DOM numbers are IEEE binary64, not exact decimal input literals.
# Preserve their exact value with Fraction.from_float; no epsilon is added.
def f(x):return F.from_float(x)if isinstance(x,float)else F(str(x))
rows=[];fontnames=set();small=[]
for ref in idx['records']:
 raw=(B/'browser-run01'/ref['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256'];r=json.loads(raw);d=json.loads((B/'models'/ref['file']).read_text());m=r['measurement'];assert m['chartUnchanged']and m['interactiveSVG']==0 and not r['pageErrors']
 assert hashlib.sha256((B/'browser-run01'/r['screenshot']).read_bytes()).hexdigest()==r['screenshotSHA256']
 for item in r['fonts']:
  for font in item['fonts']:fontnames.add(font['familyName'])
 actual=copy.deepcopy(d);gs=actual['groups'];C=list(map(f,d['C']));clip=rect(d['clip']);errors=[];drift=0;anchor=[]
 for g,measured in zip(gs,m['groups']):
  assert g['key']==measured['key'];drift=max(drift,hypot(float(g['P'][0])-measured['P'][0],float(g['P'][1])-measured['P'][1]));g['P']=measured['P'];g['components']=measured['components']
  a=measured['actualAnchorCSS'];e=measured['expectedAnchorCSS'];anchor.append(hypot(a[0]-e[0],a[1]-e[1]))
 for i,g in enumerate(gs):
  r0,r1=map(f,g['annulus'])
  for a in boxes(g):
   if not inside(a,clip):errors.append({'predicate':'clip','key':g['key']})
   lo,hi=radial_range(a,C)
   if lo<r0*r0 or hi>r1*r1:errors.append({'predicate':'annulus','key':g['key']})
  for h in gs[i+1:]:
   val=min(gap2(a,b)for a in boxes(g)for b in boxes(h))
   if val<4:errors.append({'predicate':'gap','left':g['key'],'right':h['key'],'gap2':str(val),'gap_px':float(val)**.5})
 for kind in ['point','marker','angle']:
  subset=[g for g in gs if g['kind']==kind];expected=[g['key']for g in sorted(subset,key=lambda g:g['rank'])]
  act=[g['key']for g in sorted(subset,key=lambda g:((atan2(float(g['P'][1])-float(C[1]),float(C[0])-float(g['P'][0]))-g['seam'])%(2*pi),g['index']))]
  if expected and not any(act==expected[k:]+expected[:k]for k in range(len(expected))):errors.append({'predicate':'order','kind':kind})
 sizes=[t['effectiveEm']>= (16 if t['fontSize']>=16 else 12)for t in m['texts']]
 row={'file':ref['file'],'fixture':d['fixture'],'frame':d['size'],'variant':d['variant'],'geometry_pass':not errors,'errors':errors,'component_drift':m['maxComponentDrift'],'SVG_translation_drift':drift,'anchor_max_error':max(anchor,default=0),'anchor_pass':all(e<=.5 for e in anchor),'font_size_pass':all(sizes),'page_overflow':m['pageOverflow'],'svg_no_controls':m['interactiveSVG']==0,'DPR':m['DPR'],'zoom':m['zoom'],'screenshot':r['screenshot']}
 rows.append(row)
 if d['variant']=='D':print('V3_ACTUAL',ref['file'],'geometry',not errors,'errors',errors[:3],'P_drift',drift,flush=True)
summary={v:{'cells':sum(r['variant']==v for r in rows),'geometry_pass':sum(r['variant']==v and r['geometry_pass']for r in rows),'anchor_pass':sum(r['variant']==v and r['anchor_pass']for r in rows),'size_pass':sum(r['variant']==v and r['font_size_pass']for r in rows)}for v in sorted({r['variant']for r in rows})}
out={'summary':summary,'actual_fonts':sorted(fontnames),'browser':idx['browser'],'controls':idx['controls'],'cells':rows,'acceptance_epsilon':0,'coordinate_policy':'exact IEEE binary64 native coordinates, exact decimal model strings','limits':'Strict rational test of actual finite coordinates; normal/selected component union only, full zodiac/palette/live application not tested. Tiny failures remain FAIL.'}
(B/'actual_native_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V3_BROWSER_ACTUAL_AUDIT',json.dumps(summary),'fonts',sorted(fontnames),flush=True)
