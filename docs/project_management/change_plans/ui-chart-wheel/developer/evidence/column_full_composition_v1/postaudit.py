from pathlib import Path
import json,math,fractions
F=fractions.Fraction
B=Path(r'C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1')
assert (B/'stop.json').exists()
run='run05-final';idx=json.loads((B/run/'index.json').read_text(encoding='utf8'));records=[]
def f(x):return F.from_float(x) if isinstance(x,float) else F(x)
def d2(a,b):return max(f(a[0])-f(b[2]),f(b[0])-f(a[2]),F(0))**2+max(f(a[1])-f(b[3]),f(b[1])-f(a[3]),F(0))**2
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
    routeclip=all(all(F(3,8)<=f(p[0])<=f(s['width'])-F(3,8) and F(3,8)<=f(p[1])<=f(s['H'])-F(3,8) for p in l['path']) for l in s['leaders'])
    records.append({'id':meta['id'],'independent_C0':c0pass,'C0':sorted(C0),'cyclic_column_order':cyclicpass,'no_improving_contiguous_1_64_row_shift':not improvements,'improvements':improvements,'visible_leader_stroke_in_clip':routeclip})
result={'author':'Codex / Developer','scope':'post-audit of frozen records only, no new placement/browser iteration','records':records,'C0_pass':sum(r['independent_C0'] for r in records),'column_order_pass':sum(r['cyclic_column_order'] for r in records),'row_objective_local_pass':sum(r['no_improving_contiguous_1_64_row_shift'] for r in records),'leader_clip_pass':sum(r['visible_leader_stroke_in_clip'] for r in records),'limits':'Row check is for proposed column slots and producer precision, not global geometry optimality or old annular chord return. Route identity is explicit ownership; bridges permit crossings, not a no-crossing proof.'}
(B/'post-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('POST_AUDIT',len(records),'C0',result['C0_pass'],'order',result['column_order_pass'],'row',result['row_objective_local_pass'],'leaderclip',result['leader_clip_pass'])
if any(not r['independent_C0'] or not r['cyclic_column_order'] or r['improvements'] or not r['visible_leader_stroke_in_clip'] for r in records):raise SystemExit(1)
