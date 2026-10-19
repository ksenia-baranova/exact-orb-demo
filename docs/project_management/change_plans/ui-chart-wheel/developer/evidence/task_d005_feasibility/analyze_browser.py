"""Read-only raw measurement post-audit; does not call construction or browser."""
from pathlib import Path
from fractions import Fraction as F
import collections,hashlib,json,math
B=Path(__file__).parent
RUN='run04-delivery'
idx=json.loads((B/RUN/'index.json').read_text(encoding='utf-8'))
analytic=json.loads((B/'analytic/verification.json').read_text(encoding='utf-8'));rows=[];fonts=collections.Counter();metric_deltas=[]
def f(x):return F(str(x))
def rect(b):return [f(b[k])for k in ['left','top','right','bottom']]
def gap2(a,b):return max(a[0]-b[2],b[0]-a[2],0)**2+max(a[1]-b[3],b[1]-a[3],0)**2
for ref in idx['records']:
 p=B/RUN/ref['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
 d=json.loads(p.read_text(encoding='utf-8'));m=d['measurement'];cell=json.loads((B/'analytic'/d['ref']['file']).read_text(encoding='utf-8'));S=cell['size'];C=f(S)/2
 assert m['frame']==S and m['dpr']==1 and m['zoom']==1 and m['matrix'][:4]==[1,0,0,1]
 assert m['svgRect']['width']==S and m['chartUnchanged']
 actual={};text={t['id']:t for t in m['text']};bounds_drift=[];containment=[]
 for i,g in enumerate(cell['groups']):
  if g['kind']=='angle':local=[rect(text['text-'+str(i)]['ink'])]
  else:
   met=[text[f'text-{i}-{k}']for k in range(len(g['metrics']))];local=[rect(t['ink'])for t in met]
   for k,t in enumerate(met):
    assert t['text']==g['metrics'][k]['text'];expected=rect(g['metrics'][k]['ink']);difference=[str(a-b)for a,b in zip(local[k],expected)]
    if any(F(x)!=0 for x in difference):bounds_drift.append({'key':g['key'],'part':k,'delta_actual_minus_pinned':difference})
   l=min(b[0]for b in local)-3;t=min(b[1]for b in local)-3;r=max(b[2]for b in local)+3;b=max(b[3]for b in local)+3
   local.append([l,t,r,b]);ink=local[0];local.append([ink[0]-F(3,4),ink[1]-F(3,4),ink[2]+F(3,4),ink[3]+F(3,4)])
  px,py=map(f,g['P']);actual[g['key']]=[[a+px,b+py,c+px,d+py]for a,b,c,d in local]
  r0,r1=map(f,g['annulus'])
  for left,top,right,bottom in actual[g['key']]:
   if min(left,top)<0 or max(right,bottom)>S:containment.append({'key':g['key'],'predicate':'clip'})
   low=max(left-C,C-right,0)**2+max(top-C,C-bottom,0)**2;high=max((x-C)**2+(y-C)**2 for x in [left,right]for y in [top,bottom])
   if low<r0*r0 or high>r1*r1:containment.append({'key':g['key'],'predicate':'annulus'})
 gaps=[];keys=list(actual)
 for i,key in enumerate(keys):
  for other in keys[i+1:]:
   v=min(gap2(a,b)for a in actual[key]for b in actual[other])
   if v<4:gaps.append({'left':key,'right':other,'actual_gap2':str(v)})
 for font in d['platformFonts']:
  assert font['fonts'],'unknown resolved font'
  for x in font['fonts']:fonts[x['familyName']]+=x['glyphCount']
 assert all(t['effectiveEm']>=(16 if t['size']==16 else 12)for t in m['text'])
 anchor_errors=[math.hypot(a['actualCSS'][0]-(a['local'][0]+m['matrix'][4]),a['actualCSS'][1]-(a['local'][1]+m['matrix'][5]))for a in m['anchors']]
 a=next(a for a in analytic['cells']if(a['fixture'],a['frame'],a['variant'])==(cell['fixture'],S,cell['variant']))
 wrong=[x for x in d['native']if not x['correctOwner']or not x['correctOutcome']]
 assert all(any(e['type']=='click'for e in x['deliveredEvents'])for x in d['native'])
 rows.append({'fixture':cell['fixture'],'frame':S,'variant':cell['variant'],'record':ref['file'],'static_measured_component_pass':not gaps and not containment,'gap_counterexamples':gaps,'containment_counterexamples':containment,'pinned_point_marker_ink_drift':bounds_drift,'conditional_Q_certified':sum(x['conditional_rectangle_certificate']for x in a['hit']),'targets':len(a['hit']),'native_wrong':len(wrong),'native_probes':len(d['native']),'keyboard_fail':sum(not x['pass']for x in d['keyboard']),'keyboard_targets':len(d['keyboard']),'anchor_css_error_max':max(anchor_errors),'LOCAL_TIGHT_FAIL':sum(x['tight']=='LOCAL_TIGHT_FAIL'for x in a['local_return']),'LOCAL_TIGHT_UNPROVEN':sum(x['tight']=='LOCAL_TIGHT_UNPROVEN'for x in a['local_return']),'scope':'measured point/R/conjunction/category/angle union only; zodiac/sign text/full palette NOT MODELLED; no whole drawing/production PASS'})
 metric_deltas.extend(bounds_drift)
totals={'cells':len(rows),'native_probes':sum(r['native_probes']for r in rows),'native_wrong':sum(r['native_wrong']for r in rows),'keyboard_targets':sum(r['keyboard_targets']for r in rows),'keyboard_fail':sum(r['keyboard_fail']for r in rows),'measured_component_geometry_pass':sum(r['static_measured_component_pass']for r in rows),'max_anchor_css_error':max(r['anchor_css_error_max']for r in rows),'point_marker_ink_drift_records':len(metric_deltas),'conditional_Q_certified':sum(r['conditional_Q_certified']for r in rows),'target_occurrences':sum(r['targets']for r in rows),'local_tight_fail_records':sum(r['LOCAL_TIGHT_FAIL']for r in rows),'local_tight_unproven_records':sum(r['LOCAL_TIGHT_UNPROVEN']for r in rows),'browser_controls':len(idx['controls']),'boundary_controls':len(idx['boundary']['controls']),'whole_drawing_PASS':False}
assert len(rows)==24 and not idx.get('failure')and not idx['pageErrors']
assert all(c['pass']for c in idx['controls'])and all(c['pass']for c in idx['boundary']['controls'])
out={'author':'Codex / Developer','rows':rows,'totals':totals,'resolved_font_glyph_counts':dict(fonts),'scope':'independent measured-component verification, no placement/browser calls','unverified':['whole zodiac/sign text/palette','production mounted page','HTTPS/recovery integration','runtime F5/S1','cross-platform/touch/zoom','global optimum or general impossibility']}
(B/'browser_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('D005_BROWSER_AUDIT '+json.dumps(totals))
for r in rows:print(r['fixture'],r['frame'],r['variant'],'actual_component_geometry='+str(r['static_measured_component_pass']),'native='+str(r['native_wrong'])+'/'+str(r['native_probes']))
