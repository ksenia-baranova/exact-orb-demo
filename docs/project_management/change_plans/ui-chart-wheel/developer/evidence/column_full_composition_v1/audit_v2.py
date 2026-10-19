from pathlib import Path
import json, math, fractions, sys
F=fractions.Fraction
R=Path(r'C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered')
B=R/'docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1'
run=sys.argv[1] if len(sys.argv)>1 else 'run01'
data=json.loads((B/'data.json').read_text(encoding='utf8'));idx=json.loads((B/run/'index.json').read_text(encoding='utf8'))
def ff(x):return F.from_float(x) if isinstance(x,float) else F(x)
def d2(a,b):
    dx=max(ff(a[0])-ff(b[2]),ff(b[0])-ff(a[2]),F(0));dy=max(ff(a[1])-ff(b[3]),ff(b[1])-ff(a[3]),F(0))
    return dx*dx+dy*dy
records=[]
for meta in idx['records']:
    r=json.loads((B/run/(meta['id']+'.json')).read_text(encoding='utf8'))
    if 'actual' not in r:records.append({'id':r['id'],'errors':[r.get('error','not measured')]});continue
    a=r['actual'];s=a['state'];chart=data[r['fixture']]['chart'];errors=[];text=[]
    for t in a['texts']:
        owner=next(g for g in s['groups']+s['fixed'] if g['key']==t['owner'])
        i=int(t['key'].rsplit(':',1)[1]);contour=owner.get('draw',[{}]*len(owner['parts']))[i].get('contour',False) if 'draw' in owner else False
        b=[ff(x) for x in t['css']];p=F(3,4) if contour else F(0);b=[b[0]-p,b[1]-p,b[2]+p,b[3]+p]
        text.append((t,b))
        if b[0]<0 or b[1]<0 or b[2]>s['width'] or b[3]>s['H']:errors.append(['CLIP',t['key'],list(map(float,b))])
        em=t['size']*min(t['matrix']);threshold=16 if t['size']==16 else 12
        if em<threshold:errors.append(['EM',t['key'],em,threshold])
    gaps=[]
    for i,(t,b) in enumerate(text):
        for u,c in text[i+1:]:
            if t['owner']==u['owner']:continue
            dist=d2(b,c)
            if dist<4:errors.append(['GAP',t['key'],u['key'],math.sqrt(float(dist))])
            gaps.append(float(dist))
    keys=[g['key'] for g in s['groups'] if g['kind']=='point'];expected=[p['id'] for p in chart['points']]
    if set(keys)!=set(expected) or len(keys)!=len(expected) or a['pointCount']!=len(expected):errors.append(['POINTS'])
    if not a['sourceUnchanged'] or a['svgTargets'] or a['overflow']:errors.append(['SOURCE_INTERACTION_OVERFLOW',a['sourceUnchanged'],a['svgTargets'],a['overflow']])
    if a['signCount']!=12 or a['houseCount']!=len(chart['houses'] or []) or a['angleCount']!=len(chart['angles'] or {}):errors.append(['FULL_LAYERS'])
    expected_r=sum(p['retrograde'] for p in chart['points']);actual_r=sum(t['text']=='R' for t in a['texts'])
    if expected_r!=actual_r:errors.append(['R',expected_r,actual_r])
    frozen=0
    for g in s['groups']:
        if not g['C0']:
            frozen+=1
            if g['P']!=g['A']:errors.append(['FROZEN',g['key']])
        if g['kind']=='point' and g['column']!=g['C0']:errors.append(['POINT_COLUMN_C0',g['key']])
    anchors={p['key']:p for p in a['anchors']};max_anchor_error=0
    for t,b in text:
        for k,p in anchors.items():
            if k==t['owner']:continue
            if d2(b,[p['cx']-1,p['cy']-1,p['cx']+1,p['cy']+1])<4:errors.append(['ANCHOR_OBSCURED',t['key'],k])
    endpoint={p['id']:p['longitude'] for p in chart['points']};endpoint.update({k:v['longitude'] for k,v in (chart['angles'] or {}).items()})
    def ideal(lng,radius):
        t=(lng-s['origin'])*math.pi/180
        return [s['C'][0]-radius*math.cos(t),s['C'][1]+radius*math.sin(t)]
    for g in s['groups']:
        if g['key'] not in anchors:continue
        p=anchors[g['key']]
        if 'pointR' not in s:reference=g['A']
        elif g['kind']=='point':reference=ideal(endpoint[g['key']],s['pointR'])
        elif g['kind']=='angle':reference=ideal(endpoint[g['key'][6:]],s['R']*.48)
        else:
            key=g['key'][5:];aspect=next(v for v in s['aspects'] if v['key']==key);aa=ideal(endpoint[aspect['from']],s['R']*.27);bb=ideal(endpoint[aspect['to']],s['R']*.27);reference=[(aa[i]+bb[i])/2 for i in range(2)]
        err=math.hypot(p['cx']-reference[0],p['cy']-reference[1]);max_anchor_error=max(err,max_anchor_error)
        if err>.5:errors.append(['ANCHOR',g['key'],err])
    missing=[l['key'] for l in s['leaders'] if l['path'] is None]
    if missing:errors.append(['LEADER_ROUTE',missing])
    residual=[]
    # Independent local directional probe; does not call placement or use its candidates.
    allgroups=s['groups']+s['fixed']+s.get('anchorObstacles',[])
    def valid(g,P):
        bounds=[[p[0]+P[0],p[1]+P[1],p[2]+P[0],p[3]+P[1]] for p in g['parts']]
        if any(math.hypot(x-s['C'][0],y-s['C'][1])>s['R']-24 for b in bounds for x,y in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]):return False
        return all(d2(b,[p[0]+o['P'][0],p[1]+o['P'][1],p[2]+o['P'][0],p[3]+o['P'][1]])>=4 for b in bounds for o in allgroups if o['key']!=g['key'] and o.get('owner')!=g['key'] for p in o['parts'])
    for g in s['groups']:
        if not g['moved'] or g['column']:continue
        d=math.dist(g['P'],g['A']);step=min(1,d);P=[g['P'][i]+step*(g['A'][i]-g['P'][i])/d for i in range(2)]
        if valid(g,P):residual.append({'key':g['key'],'probe_css':step,'P':P})
    certificates=[]
    for c in s.get('auxCertificates',[]):
        g=next(g for g in s['groups'] if g['key']==c['key'])
        if c['kind']=='unmoved':certificates.append({'key':c['key'],'result':'UNMOVED','pass':g['P']==g['A']});continue
        if c['kind']!='frozen-axis-contact':certificates.append({'key':c['key'],'result':'UNPROVEN','pass':False});continue
        i=g['parts'].index(c['ownComponent']);own=next((b for t,b in text if t['key']==g['key']+':'+str(i)),None)
        if own is None:certificates.append({'key':c['key'],'result':'NOT_VISIBLE_IN_THIS_MODE','pass':True});continue
        if c['obstacle'].startswith('anchor:'):
            p=anchors.get(c['obstacle'][7:])
            # Some marker true anchors are suppressed in the selected-aspect view; their model positions still reserve geometry.
            if p:foreign=list(map(ff,[p['cx']-1,p['cy']-1,p['cx']+1,p['cy']+1]))
            else:foreign=list(map(ff,c['foreignBox']))
        else:
            options=[b for t,b in text if t['owner']==c['obstacle']]
            foreign=next((b for b in options if list(map(float,b))==c['foreignBox']),None)
            if foreign is None:certificates.append({'key':c['key'],'result':'FOREIGN_COMPONENT_UNPROVEN','pass':False});continue
        axis=c['axis'];sgn=c['sign'];gap=(foreign[axis]-own[axis+2]) if sgn==1 else (own[axis]-foreign[axis+2])
        other=1-axis;projection=max(own[other]-foreign[other+2],foreign[other]-own[other+2],F(0))
        derivative=(ff(g['A'][axis])-ff(g['P'][axis]))*sgn
        ok=gap==2 and projection==0 and derivative>0 and valid(g,g['P'])
        certificates.append({'key':c['key'],'result':'EXACT_CONTACT_BLOCKS_EVERY_POSITIVE_PREFIX' if ok else 'UNPROVEN','pass':ok,'axis_gap':float(gap),'cross_projection_gap':float(projection),'closing_derivative':float(derivative),'frozen_obstacle':c['obstacle']})
    fonts=sorted(set(f['familyName'] for row in r['platformFonts'] for f in row if f['glyphCount']))
    result={'id':r['id'],'errors':errors,'static_pass':not errors,'texts':len(text),'points':len(expected),'R':actual_r,'signs':a['signCount'],'houses':a['houseCount'],'angles':a['angleCount'],'markers':a['markerCount'],'drawn_aspects':len(s['drawn']),'column_points':len(s['column']['order']),'frozen_labels':frozen,'height_css':s['H'],'wheel_css':s['D'],'column_width_css':s['colWidth'],'min_foreign_component_gap_css':math.sqrt(min(gaps)) if gaps else None,'max_anchor_error_css':max_anchor_error,'missing_leaders':missing,'aux_1px_return_witnesses':residual,'aux_certificates':certificates,'aux_certificates_pass':all(c['pass'] for c in certificates),'actual_fonts':fonts}
    records.append(result)
    print(r['id'],'PASS' if not errors else 'FAIL', 'column',result['column_points'],'routefail',len(missing),'gap',result['min_foreign_component_gap_css'],'aux return',len(residual),str(errors[:3]))
controls=[{'id':'gap-equality','actual':d2([0,0,2,2],[4,0,6,2])>=4,'expected':True},{'id':'gap-below','actual':d2([0,0,2,2],[F(399,100),0,6,2])>=4,'expected':False},{'id':'diagonal-equality','actual':d2([0,0,2,2],[F(16,5),F(18,5),6,6])>=4,'expected':True},{'id':'diagonal-below','actual':d2([0,0,2,2],[3,3,6,6])>=4,'expected':False}]
result={'author':'Codex / Developer','run':run,'native_predicate':'exact binary64-as-rational squared Euclidean AABB distance >=4; no tolerance','records':records,'measured':len(records),'static_pass':sum(r.get('static_pass',False) for r in records),'analytic_controls':controls,'boundary':json.loads((B/run/'boundary.json').read_text(encoding='utf8'))['controls']}
(B/(run+'-audit.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('COLUMN_AUDIT',result['static_pass'],'/',len(records),'CONTROLS',sum(c['actual']==c['expected'] for c in controls),'/',len(controls))
