from pathlib import Path
import json,math,fractions,sys
F=fractions.Fraction
B=Path(__file__).resolve().parent
assert (B/'stop.json').exists()
run=sys.argv[1] if len(sys.argv)>1 else 'run07-ports';idx=json.loads((B/run/'index.json').read_text(encoding='utf8'));records=[]
def f(x):return F.from_float(x) if isinstance(x,float) else F(x)
def d2(a,b):return max(f(a[0])-f(b[2]),f(b[0])-f(a[2]),F(0))**2+max(f(a[1])-f(b[3]),f(b[1])-f(a[3]),F(0))**2
def shared(a,b,c,d):
    v=[f(b[i])-f(a[i]) for i in range(2)]
    def cross(p):return v[0]*(f(p[1])-f(a[1]))-v[1]*(f(p[0])-f(a[0]))
    if v==[0,0] or cross(c) or cross(d):return False
    j=0 if v[0] else 1
    return min(max(a[j],b[j]),max(c[j],d[j]))>max(min(a[j],b[j]),min(c[j],d[j]))
for meta in idx['records']:
    a=json.loads((B/run/(meta['id']+'.json')).read_text(encoding='utf8'))['actual'];s=a['state'];groups=[]
    for g in s['groups']:
        parts=g['parts']
        if g['kind']=='point' and g['column']:parts=parts[:-1] # name is only present after movement; glyph/R local offsets are unchanged.
        groups.append({'key':g['key'],'P':g['A'],'parts':parts})
    def boxes(g):return [[f(b[0])+f(g['P'][0]),f(b[1])+f(g['P'][1]),f(b[2])+f(g['P'][0]),f(b[3])+f(g['P'][1])] for b in g['parts']]
    C0=set()
    for i,g in enumerate(groups):
        gb=boxes(g)
        for h in s['fixed']+s['anchorObstacles']:
            if h.get('owner')==g['key']:continue
            if any(d2(b,c)<4 for b in gb for c in boxes(h)):C0.add(g['key'])
        for h in groups[i+1:]:
            if any(d2(b,c)<4 for b in gb for c in boxes(h)):C0.update([g['key'],h['key']])
    c0pass=C0==set(s['C0'])
    order=s['column']['order'];cg=[next(g for g in s['groups'] if g['key']==k) for k in order]
    cyclicpass=[g['rank'] for g in cg]==sorted(g['rank'] for g in cg)
    ys=[f(g['P'][1]) for g in cg];targets=[f(g['A'][1]) for g in cg];offsets=list(map(f,s['column']['offsets']));z=[y-o for y,o in zip(ys,offsets)]
    top=f(s['column']['top']);bottom=f(s['column']['bottom']);baseline=sum((y-t)**2 for y,t in zip(ys,targets));improvements=[]
    # Independent finite variations; no placement, MRV or PAV call.
    for lo in range(len(z)):
        for hi in range(lo,len(z)):
            for delta in [F(-1,64),F(1,64)]:
                zz=[v+(delta if lo<=i<=hi else 0) for i,v in enumerate(z)]
                if any(v<top or v>bottom for v in zz) or any(zz[i]>zz[i+1] for i in range(len(zz)-1)):continue
                yy=[v+o for v,o in zip(zz,offsets)];cost=sum((y-t)**2 for y,t in zip(yy,targets))
                if cost<baseline:improvements.append([lo,hi,float(delta),float(cost-baseline)])
    routeclip=all(l['path'] is not None and all(F(3,4)<=f(p[0])<=f(s['width'])-F(3,4) and F(3,4)<=f(p[1])<=f(s['H'])-F(3,4) for p in l['path']) for l in s['leaders'])
    merges=[]
    ls=[l for l in s['leaders'] if l['path']]
    for i,l in enumerate(ls):
        for m in ls[i+1:]:
            for aa,bb in zip(l['path'],l['path'][1:]):
                for cc,dd in zip(m['path'],m['path'][1:]):
                    if shared(aa,bb,cc,dd):merges.append([l['key'],m['key'],aa,bb,cc,dd])
    records.append({'id':meta['id'],'independent_C0':c0pass,'C0':sorted(C0),'cyclic_column_order':cyclicpass,'no_improving_contiguous_1_64_row_shift':not improvements,'improvements':improvements,'visible_leader_stroke_in_clip':routeclip,'shared_positive_length_segments':merges})
control_inputs=[('shared-segment',[[0,0],[10,0],[2,0],[8,0]],True),('single-crossing',[[0,0],[10,10],[0,10],[10,0]],False),('endpoint-touch',[[0,0],[10,0],[10,0],[15,0]],False)]
controls=[{'id':k,'actual':shared(*p),'expected':e,'pass':shared(*p)==e} for k,p,e in control_inputs]
result={'author':'Codex / Developer','run':run,'scope':'independent audit of saved records only, no placement/browser call','records':records,'C0_pass':sum(r['independent_C0'] for r in records),'column_order_pass':sum(r['cyclic_column_order'] for r in records),'row_objective_local_pass':sum(r['no_improving_contiguous_1_64_row_shift'] for r in records),'leader_clip_pass':sum(r['visible_leader_stroke_in_clip'] for r in records),'no_shared_segments_pass':sum(not r['shared_positive_length_segments'] for r in records),'route_controls':controls,'limits':'Row check concerns proposed column slots/producer precision, not global geometry optimality or old annular chord return. Discrete crossings use bridges; no-shared-centerline check is independent, not a no-crossing/psychophysical readability proof.'}
(B/(run+'-post-audit.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('POST_AUDIT',run,len(records),'C0',result['C0_pass'],'order',result['column_order_pass'],'row',result['row_objective_local_pass'],'leaderclip',result['leader_clip_pass'],'no_shared',result['no_shared_segments_pass'])
if any(not r['independent_C0'] or not r['cyclic_column_order'] or r['improvements'] or not r['visible_leader_stroke_in_clip'] or r['shared_positive_length_segments'] for r in records):raise SystemExit(1)
