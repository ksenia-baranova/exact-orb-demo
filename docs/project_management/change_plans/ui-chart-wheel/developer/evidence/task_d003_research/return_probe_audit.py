"""Independent post-measurement arc-return audit. No browser or placement invocation."""
from pathlib import Path
import json,math
base=Path(__file__).parent;index=json.loads((base/'run03/browser_matrix.json').read_text());records=[]
def gap(a,b):return math.hypot(max(a['left']-b['right'],b['left']-a['right'],0),max(a['top']-b['bottom'],b['top']-a['bottom'],0))
for ref in index['records']:
    d=json.loads((base/'run03'/ref['file']).read_text());m=d['measurement'];frame=m['frame']
    for g in m['groups']:
        if not g['delta']:continue
        distance=abs(g['delta'])*g['r'];s=min(1,distance);theta=g['theta']-math.copysign(s/g['r'],g['delta']);q={'x':frame['C'][0]-g['r']*math.cos(theta),'y':frame['C'][1]+g['r']*math.sin(theta)}
        boxes=[{k:b[k]+q['x'if k in ['left','right']else'y']for k in b}for b in g['components']]
        frozen=[b for h in m['groups']if h['key']!=g['key']for b in h['boxes']]+[b for o in m['obstacles']for b in o['boxes']]
        def margins(boxes):
            ring=frame[g['kind']];values=[min(gap(a,b)for a in boxes for b in frozen)-2]
            for b in boxes:
                x,y=frame['C'];low=math.hypot(max(b['left']-x,x-b['right'],0),max(b['top']-y,y-b['bottom'],0));high=max(math.hypot(xx-x,yy-y)for xx in [b['left'],b['right']]for yy in[b['top'],b['bottom']]);values += [low-ring['inner'],ring['outer']-high,b['left'],b['top'],frame['size']-b['right'],frame['size']-b['bottom']]
            return values
        end=margins(boxes);start=margins(g['boxes']);v='FULL_PREFIX_UNPROVEN'
        if min(start)<0:v='CANDIDATE_INADMISSIBLE'
        elif min(end)<0:v='LOCAL_STEP_PASS_ENDPOINT_VIOLATION'
        elif min(start)>s and all(x['pass']for x in d['verifier']['order']):v='LOCAL_STEP_FAIL_PREFIX_CERTIFIED'
        records.append({'fixture':d['name'],'viewport':d['viewport'],'layout':d['layout'],'key':g['key'],'distance_arc_css':distance,'probe_arc_css':s,'q':q,'q_boxes':boxes,'start_min_margin':min(start),'endpoint_min_margin':min(end),'verdict':v,'method':'independent analytic arc formula; Lipschitz translation <= arc; whole-prefix certified only with margin > s and valid cyclic order; no global optimum claim'})
(base/'return_probe_audit.json').write_text(json.dumps({'records':records,'precision':'binary64 post-analysis; no new tolerance; near-boundary / uncertified prefix -> UNPROVEN','browser':'NOT_RUN by this post-audit'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
from collections import Counter
print('D003_RETURN_AUDIT_OK',len(records),dict(Counter(r['verdict']for r in records)))
