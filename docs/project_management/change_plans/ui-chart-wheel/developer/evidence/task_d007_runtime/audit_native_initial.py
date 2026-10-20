"""Independent native bbox/coordinate audit. Does not call the layout algorithm."""
from pathlib import Path
from fractions import Fraction as F
import json,math,sys,re
B=Path(__file__).resolve().parent
run=sys.argv[1]
data=json.loads((B/run/'actual.json').read_text(encoding='utf8'))
source=json.loads((B/'../column_full_composition_v1/data.json').read_text(encoding='utf8'))
def rect(b):return [F(v) for v in b]
def gap2(a,b):
    dx=max(a[0]-b[2],b[0]-a[2],0);dy=max(a[1]-b[3],b[1]-a[3],0)
    return dx*dx+dy*dy
def moved(b,p):return [b[0]+p[0],b[1]+p[1],b[2]+p[0],b[3]+p[1]]
def union(parts):return [min(b[0] for b in parts),min(b[1] for b in parts),max(b[2] for b in parts),max(b[3] for b in parts)]
def shared(a,b,c,d):
    v=[b[0]-a[0],b[1]-a[1]]
    if v==[0,0] or any(v[0]*(p[1]-a[1])-v[1]*(p[0]-a[0])!=0 for p in [c,d]):return False
    k=0 if v[0] else 1
    return min(max(a[k],b[k]),max(c[k],d[k]))>max(min(a[k],b[k]),min(c[k],d[k]))
controls=[('gap_equal',gap2([0,0,10,10],[12,0,20,10])==4),
('below_gap',gap2([0,0,10,10],[F('11.984375'),0,20,10])<4),
('diagonal_345',gap2([0,0,10,10],[13,14,20,20])==25),
('diagonal_reject',gap2([0,0,10,10],[11,11,20,20])<4),
('shared_20_5',shared([0,0],[30,0],[F('9.5'),0],[40,0])),
('crossing_not_shared',not shared([0,0],[30,0],[15,-10],[15,10])),
('touch_not_shared',not shared([0,0],[30,0],[30,0],[40,0]))]
results=[]
for record in data['cases']:
    a=record.get('actual',{});errors=[];gaps=[];contacts=0
    if not a.get('svg') or not record.get('pass'):errors.append('runtime/configuration failed')
    else:
        W,H=F(a['width']),F(a['height'])
        groups=[{**g,'P':[F(v) for v in g['origin']],'parts':[rect(b) for b in g['parts']]} for g in a['groups']]
        anchors={v['key']:rect(v['box']) for v in a['anchors']}
        for i,g in enumerate(groups):
            for b in g['parts']:
                if not(0<=b[0]<=b[2]<=W and 0<=b[1]<=b[3]<=H):errors.append('clip '+g['key'])
                for o in groups[i+1:]:
                    for c in o['parts']:
                        gg=gap2(b,c);gaps.append(gg)
                        if gg<4:errors.append('gap '+g['key']+' / '+o['key']+' '+str(float(gg)))
                for key,c in anchors.items():
                    if key!=g['key'] and gap2(b,c)<4:errors.append('foreign-anchor '+g['key']+' / '+key)
        # C0 is rebuilt from ACTUAL component metrics and actual true marks, before displacement.
        defaults=[]
        for g in groups:
            if g['kind']=='sign':continue
            center=anchors[g['key']]
            A=[(center[0]+center[2])/2,(center[1]+center[3])/2]
            # Column names are a presentation addition; default point = glyph + optional R.
            n=1
            if g['kind']=='point':
                n=2 if any(t['id']==g['key']+':1' and t['text']=='R' for t in a['texts']) else 1
            else:n=len(g['parts'])
            local=[moved(b,[-g['P'][0],-g['P'][1]]) for b in g['parts'][:n]]
            defaults.append({**g,'A':A,'local':local,'default':[moved(b,A) for b in local]})
        fixed=[g for g in groups if g['kind']=='sign'];c0=set()
        for i,g in enumerate(defaults):
            if any(gap2(b,c)<4 for b in g['default'] for o in fixed for c in o['parts']):c0.add(g['key'])
            if any(gap2(b,c)<4 for b in g['default'] for key,c in anchors.items() if key!=g['key']):c0.add(g['key'])
            for o in defaults[i+1:]:
                if any(gap2(b,c)<4 for b in g['default'] for c in o['default']):c0.update([g['key'],o['key']])
        for g in defaults:
            if g['kind']=='point':
                if (g['column']=='true')!=(g['key'] in c0):errors.append('C0 column '+g['key'])
                if g['column']!='true' and g['P']!=g['A']:errors.append('nonconflicting point moved '+g['key'])
            elif g['key'] not in c0 and g['P']!=g['A']:errors.append('frozen auxiliary moved '+g['key'])
            if g['kind'] in ['angle','marker'] and g['P']!=g['A']:
                v=[g['A'][i]-g['P'][i] for i in range(2)]
                obstacles=[c for o in groups if o['key']!=g['key'] for c in o['parts']]+[c for key,c in anchors.items() if key!=g['key']]
                proof=False
                for b in g['parts']:
                    for c in obstacles:
                        dy=max(b[1]-c[3],c[1]-b[3],0);dx=max(b[0]-c[2],c[0]-b[2],0)
                        if dy==0 and ((b[2]+2==c[0] and v[0]>0) or (c[2]+2==b[0] and v[0]<0)):proof=True
                        if dx==0 and ((b[3]+2==c[1] and v[1]>0) or (c[3]+2==b[1] and v[1]<0)):proof=True
                if proof:contacts+=1
                else:errors.append('no whole-prefix blocking contact '+g['key'])
        # Native column order and L2 contiguous-shift certificate.
        chart=record.get('chart') or source.get(record['fixture'],{}).get('chart')
        if chart:
            ordered=sorted(chart['points'],key=lambda p:(p['longitude'],p['id']))
            if ordered:
                gaps_c=[(ordered[(i+1)%len(ordered)]['longitude']-p['longitude'])%360 for i,p in enumerate(ordered)]
                cut=(gaps_c.index(max(gaps_c))+1)%len(ordered)
                ordered=ordered[cut:]+ordered[:cut]
            by_id={g['key']:g for g in defaults if g['column']=='true'}
            rows=[by_id[p['id']] for p in ordered if p['id'] in by_id]
            if [g['key'] for g in sorted(rows,key=lambda g:g['P'][1])]!=[g['key'] for g in rows]:errors.append('column order')
            if rows:
                for i in range(len(rows)):
                    for j in range(i,len(rows)):
                        for step in [F(1,64),F(-1,64)]:
                            probe=[]
                            for k,g in enumerate(rows):
                                shift=[0,step if i<=k<=j else 0]
                                probe.append([moved(b,shift) for b in g['parts']])
                            legal=all(b[1]>=8 and b[3]<=H-8 for ps in probe for b in ps) and all(gap2(b,c)>=4 for k,ps in enumerate(probe) for other in probe[k+1:] for b in ps for c in other)
                            if legal:
                                before=sum((g['P'][1]-g['A'][1])**2 for g in rows)
                                after=sum((g['P'][1]+(step if i<=k<=j else 0)-g['A'][1])**2 for k,g in enumerate(rows))
                                if after<before:errors.append('improvable column rows '+str((i,j,step)))
            origin=chart['angles']['asc']['longitude'] if chart['kind']=='natal' else 0
            C=a['frame']['C'];R=a['frame']['R']
            reach=max([0]+[math.hypot(float(x),float(y)) for g in defaults if g['kind']=='point' for b in g['local'] for x,y in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]])
            pointR=R-26-reach-2
            for point in chart['points']:
                mark=anchors[point['id']];actual=[float((mark[0]+mark[2])/2),float((mark[1]+mark[3])/2)]
                t=math.radians(point['longitude']-origin);expected=[C[0]-pointR*math.cos(t),C[1]+pointR*math.sin(t)]
                if math.dist(actual,expected)>0.5:errors.append('anchor error '+point['id'])
                if point['retrograde']!=any(t['id']==point['id']+':1' and t['text']=='R' for t in a['texts']):errors.append('R '+point['id'])
        segments=[]
        for l in a['leaders']:
            vertices=[[F(v) for v in pair.split()] for pair in re.findall(r'[ML]([^ML]+)',l['d'])]
            if any(not(0<=p[0]<=W and 0<=p[1]<=H) for p in vertices):errors.append('leader clip '+l['key'])
            segments.extend([(l['key'],x,y) for x,y in zip(vertices,vertices[1:])])
        for i,(owner,x,y) in enumerate(segments):
            for other,c,d in segments[i+1:]:
                if owner!=other and shared(x,y,c,d):errors.append('shared leaders '+owner+' / '+other)
    results.append({'id':record['id'],'pass':not errors,'errors':sorted(set(errors)),'min_gap_squared':float(min(gaps)) if gaps else None,'blocking_contacts':contacts})
summary={'method':'Fraction from actual native binary64 boxes; independent C0, order, contiguous row shifts, whole-prefix contacts and shared routes; layout function not called',
'controls':[{'id':k,'pass':v} for k,v in controls],'cases':results,'pass':sum(r['pass'] for r in results),'total':len(results)}
(B/(run+'-independent.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NATIVE_INDEPENDENT',summary['pass'],'/',summary['total'],'controls',sum(v for _,v in controls),'/',len(controls))
for r in results:
    if not r['pass']:print(r['id'],r['errors'])
raise SystemExit(0 if all(v for _,v in controls) and all(r['pass'] for r in results) else 1)
