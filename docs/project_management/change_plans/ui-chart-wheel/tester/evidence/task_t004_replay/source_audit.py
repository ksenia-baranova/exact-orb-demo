"""Read-only source / codec evidence. Does not calculate a chart or edit golden files."""
from pathlib import Path
import sys,json,gzip,collections,logging
root=Path(__file__).resolve().parents[7]
sys.path.insert(0,str(root/'src'))
from exact_orb.calculation.types import ChartArtifact
from exact_orb.calculation.codec import encode_chart_artifact,decode_chart_artifact
from exact_orb.http_api.projectors import project_chart
from exact_orb.engine.aspects import AspectConfig,PositionedPoint,find_aspects
logging.disable(logging.CRITICAL)
records=[]
for kind in ['natal','cosmogram']:
    p=root/f'tests/golden/chart_artifact_format_1_{kind}_1985.bin'
    artifact=decode_chart_artifact(p.read_bytes())
    restored=decode_chart_artifact(encode_chart_artifact(artifact))
    before=project_chart(artifact).model_dump(mode='json'); after=project_chart(restored).model_dump(mode='json')
    assert before==after
    directed=[(a['from'],a['to'],a['type']) for a in after['aspects']]
    undirected=[(tuple(sorted([a['from'],a['to']])),a['type']) for a in after['aspects']]
    assert len(directed)==len(set(directed))==len(set(undirected))
    records.append({'id':f'G02-{kind}-codec-projector','round_trip_exact':True,'aspects':len(directed),'unique_directed':len(set(directed)),'unique_undirected':len(set(undirected)),'nonlexical_direction':sum(a>b for a,b,_ in directed),'angle_endpoints':sum(a in {'asc','mc','vertex'} or b in {'asc','mc','vertex'} for a,b,_ in directed),'key_order_preserved':True})
    payload=json.loads(artifact.model_dump_json());payload['chart']['aspects'].append(payload['chart']['aspects'][0])
    try:
        dup=decode_chart_artifact(gzip.compress(json.dumps(payload).encode()))
        projected=project_chart(dup).model_dump(mode='json')
        keys=[(a['from'],a['to'],a['type']) for a in projected['aspects']]
        records.append({'id':f'G02-{kind}-duplicate-restore','accepted_by_current_codec_projector':True,'rows':len(keys),'unique':len(set(keys)),'meaning':'validation-admissible storage counterexample, not demonstrated normal producer output / new API obligation'})
    except Exception as exc:
        records.append({'id':f'G02-{kind}-duplicate-restore','accepted_by_current_codec_projector':False,'error':type(exc).__name__,'message':str(exc)[:300]})
    # Reverse all endpoints together: order may change conceptually; codec only copies saved order.
    payload=json.loads(artifact.model_dump_json())
    for a in payload['chart']['aspects']:a['from_point'],a['to_point']=a['to_point'],a['from_point']
    try:
        reverse=project_chart(decode_chart_artifact(gzip.compress(json.dumps(payload).encode()))).model_dump(mode='json')
        records.append({'id':f'G02-{kind}-reverse-restore','accepted':True,'first':reverse['aspects'][0],'meaning':'stored endpoints are preserved, lexical orientation is not a validated boundary'})
    except Exception as exc:records.append({'id':f'G02-{kind}-reverse-restore','accepted':False,'error':type(exc).__name__,'message':str(exc)[:300]})
config=AspectConfig.natal();assert len(config.natal_points)==len(set(config.natal_points))
records.append({'id':'G02-default-config','points':list(config.natal_points),'unique':True,'proof':'finite default list; i<j enumerates pair once, closest_allowed emits at most one type; stable cosmogram refs validated unique and same order'})
points=[PositionedPoint(chart='natal',body='sun',longitude=0),PositionedPoint(chart='natal',body='moon',longitude=.1)]
one=find_aspects(points,None,config);two=find_aspects(points[::-1],None,config)
records.append({'id':'G02-finder-direction','forward':[(a.from_point.body,a.to_point.body) for a in one],'reverse_input':[(a.from_point.body,a.to_point.body) for a in two],'meaning':'direction follows input order; independent from result sort'})
out=Path(__file__).with_name('source_audit.json');out.write_text(json.dumps({'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'D003_SOURCE_AUDIT_OK records={len(records)} golden=UNCHANGED calculation=NOT_RUN')
