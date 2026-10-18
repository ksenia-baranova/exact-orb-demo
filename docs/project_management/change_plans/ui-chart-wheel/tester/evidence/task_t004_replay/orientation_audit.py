from pathlib import Path
import sys,json
root=Path(__file__).resolve().parents[7];sys.path.insert(0,str(root/'src'))
from exact_orb.calculation.codec import decode_chart_artifact
from exact_orb.calculation.types import ChartArtifact
from exact_orb.http_api.projectors import project_chart
from pydantic import ValidationError
rows=[]
for kind in ['natal','cosmogram']:
    artifact=decode_chart_artifact((root/f'tests/golden/chart_artifact_format_1_{kind}_1985.bin').read_bytes())
    payload=json.loads(artifact.model_dump_json())
    for a in payload['chart']['aspects']:a['from_point'],a['to_point']=a['to_point'],a['from_point']
    for configs in ['saved','empty']:
        if configs=='empty':payload['chart']['configurations']=[]
        try:
            a=ChartArtifact.model_validate(payload);dto=project_chart(a).model_dump(mode='json');rows.append({'kind':kind,'configs':configs,'accepted':True,'first':dto['aspects'][0]})
        except ValidationError as e:rows.append({'kind':kind,'configs':configs,'accepted':False,'errors':[{'loc':list(x['loc']),'type':x['type'],'msg':x['msg']}for x in e.errors(include_url=False,include_context=False,include_input=False)][:3]})
Path(__file__).with_name('orientation_audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('D003_ORIENTATION_AUDIT_OK',json.dumps(rows,ensure_ascii=False))
