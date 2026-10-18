from pathlib import Path
import json,hashlib,math,collections,datetime
base=Path(__file__).parent
idx=json.loads((base/'run02/browser_matrix.json').read_text())
rows=[]
for ref in idx['records']:
    p=base/'run02'/ref['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
    d=json.loads(p.read_text());v=d['verifier'];obs=d['measurement']['obstacles']
    def gap(a,b):return math.hypot(max(a['left']-b['right'],b['left']-a['right'],0),max(a['top']-b['bottom'],b['top']-a['bottom'],0))
    fixed=[{'left':a['key'],'right':b['key'],'gap':min(gap(x,y) for x in a['boxes'] for y in b['boxes'])}for i,a in enumerate(obs)for b in obs[i+1:]if min(gap(x,y)for x in a['boxes']for y in b['boxes'])<2]
    samples=[s for h in v['hit']for s in h['sampling']]
    keyboard=[k for k in d['keyboard']if 'activation'in k]
    keyfail=[k['id']for k in keyboard if not(k['activation']['after']['selected'] and k['activation']['after']['selected']['key']==k['key'] and k['activation']['toggle']['selected'] is None and k['activation']['after']['active']==k['id'] and k['activation']['toggle']['active']==k['id'] and k['activation']['toggle']['connected'])]
    # Keyboard starts after pointer state. First activation can legally toggle a preselected key OFF.
    badkeyboard=[]
    for k in keyboard:
        x=k['activation'];before=x['before']['selected'];after=x['after']['selected'];toggle=x['toggle']['selected']
        expected=None if before and before['key']==k['key'] else k['key']
        expected2=k['key'] if expected is None else None
        if (after or {}).get('key')!=expected or (toggle or {}).get('key')!=expected2 or not x['toggle']['connected'] or x['after']['active']!=k['id'] or x['toggle']['active']!=k['id'] or x['before']['calls']!=x['toggle']['calls']:badkeyboard.append(k['id'])
    fonts=collections.Counter(x['familyName']for t in d['platformFonts']for x in t['fonts'])
    row={'name':d['name'],'viewport':d['viewport'],'layout':d['layout'],'record':str(p.relative_to(base)).replace('\\','/'),'C0':len(v['C0']),'moved':len(v['moved']),'movable_geometry_pass':v['geometryPass'],'fixed_collisions':fixed,'complete_geometry_pass':v['geometryPass'] and not fixed,'hit_certified':sum(h['certificate']=='RECT_CONTAINMENT_PASS'for h in v['hit']),'targets':len(v['hit']),'native_probes':len(samples),'native_wrong':sum(not s['correctOwner'] or not s['correctOutcome']for s in samples),'keyboard_targets':len(keyboard),'keyboard_fail':badkeyboard,'font_families':dict(fonts),'anchor_error_max':max(a['error']for a in v['anchors']),'minimality':v['minimality'],'full_drawing_acceptance':'NOT_PROVEN (zodiac/sign labels and full styles not implemented by isolated geometry harness)'}
    rows.append(row)
controls=json.loads((base/'followup02/controls.json').read_text())['records'];a=controls[0]['actual'];b=controls[1]['actual'];alt=controls[2]['actual']
assert a['selected']=='sun' and b['identity']=='controlled-B-confirmed' and 'sun12.251215Ariesfalse' in b['point'] and b['imageCount']==0
assert any(t['event']=='late-ignored'for t in b['trace'])
assert alt['identity']=='controlled-B-confirmed' and alt['imageCount']==1 and alt['selected'] is None # same sun toggles the preserved intent
assert controls[2]['inputUnchanged']
ctl={'G01_actual_B_preserved':True,'G01_old_callback_ignored':True,'G01_alternate_live_toggle':True,'G01_scope':'isolated proposed boundary; actual production coordinator not mounted to this port','fixed_obstacle_correction':'runner geometry verdict excluded fixed-fixed collisions; this audit adds them without changing prior records','partial_run01':'10 saved cells, filesystem UNKNOWN during large JSON rewrite; kept as partial, not the complete matrix','followup01':'aborted on research snapshot selector TypeError before evidence result; fixed in followup02','source_audit_first_attempt':'metadata JSON mistaken for binary payload, ValidationError; rerun on .bin; golden untouched'}
summary={'matrix':rows,'totals':{'cells':len(rows),'native_probes':sum(r['native_probes']for r in rows),'native_wrong':sum(r['native_wrong']for r in rows),'keyboard_targets':sum(r['keyboard_targets']for r in rows),'keyboard_failed':sum(len(r['keyboard_fail'])for r in rows),'complete_geometry_cells':sum(r['complete_geometry_pass']for r in rows),'full_matrix_pass':False},'controls':ctl,'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(base/'drawing_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# TASK-D-003 — numeric matrix, independent post-audit','','Full drawing/production PASS is not claimed. Fixed angle/angle collisions are included here; initial runner geometry covered movable-vs-all only.','', '| Fixture | CSS width | Layout | C0 / moved | Movable geometry | Fixed overlaps | Hit Q44 | Native wrong / probes | Keyboard failures / targets | Minimality |','|---|---|---|---|---|---|---|---|---|---|']
for r in rows:lines.append(f"| {r['name']} | {r['viewport']} | {r['layout']} | {r['C0']} / {r['moved']} | {r['movable_geometry_pass']} | {len(r['fixed_collisions'])} | {r['hit_certified']}/{r['targets']} | {r['native_wrong']}/{r['native_probes']} | {len(r['keyboard_fail'])}/{r['keyboard_targets']} | {r['minimality']} |")
lines+=['','All numeric records / actual coordinates / event paths / exact file hashes: [run02 index](run02/browser_matrix.json). [Drawing audit](drawing_audit.json) corrects the scope of earlier per-cell geometry verdicts.','', 'Raw source and controls are immutable evidence of their run; a new run uses a new D003_RUN / D003_FOLLOWUP name.']
(base/'matrix.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('D003_DRAWING_AUDIT_OK',json.dumps(summary['totals']))
