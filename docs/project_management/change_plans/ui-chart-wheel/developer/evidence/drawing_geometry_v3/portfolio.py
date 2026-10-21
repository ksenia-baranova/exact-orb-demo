"""Explicit fourth alternative: verified seed portfolio + converging local return."""
from pathlib import Path
from decimal import Decimal
import json,math,hashlib,time,heapq,itertools,datetime,ast,shutil
B=Path(__file__).resolve().parent
if B.name!='drawing_geometry_v3':B=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered/docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3')
spec=json.loads((B/'spec.json').read_text());OLD=B.parent/'task_d005_feasibility/analytic';deadline=datetime.datetime.fromisoformat(spec['deadline_utc']).timestamp()
assert not (B/'spec_D.json').exists()
fourth={'variant':'D','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':'choose only independently geometry-verified A/B/C seeds; minimize maximum displacement, then sum; deterministic fixture-independent rule','reason':'beam and CSP are complementary; independent verification prevents publishing a failed search seed','return_sweeps':24,'stop':'no changes or cap24 or parent90min; every residual positive prefix remains failure','unchanged':'spec.json thresholds/radii/annuli/clip/C0/passive SVG; no new dependencies or production; no claim of global optimum'}
(B/'spec_D.json').write_text(json.dumps(fourth,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(B/'verification.json',B/'verification_ABC.json')
defs=[n for n in ast.parse((B/'build.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=defs,type_ignores=[]),'V3_shared_constructor_functions','exec'))
verification=json.loads((B/'verification_ABC.json').read_text());spec['search']['return_sweeps']=24
out=B/'models';idx=json.loads((out/'index.json').read_text());assert not any(x['file'].endswith('-D.json')for x in idx['records'])
for name in spec['fixtures']:
 for viewport,S in spec['frames'].items():
  checktime();eligible=[r for r in verification['cells']if r['fixture']==name and r['frame']==S and r['variant']in ['A','B','C']and r['geometry_pass']]
  assert eligible,(name,S)
  seed=min(eligible,key=lambda r:(r['max_displacement'],r['sum_displacement'],r['variant']))
  d=json.loads((out/seed['file']).read_text());d['seed_variant']=d['variant'];d['variant']='D';start=time.monotonic();d['return_history_D']=tighten(d);d['elapsed_seconds_D']=time.monotonic()-start
  for g in d['groups']:g['leader']=any(float(x)!=a for x,a in zip(g['P'],g['A']))
  file=f'{name}-{S}-D.json';write(out/file,d);idx['records'].append({'file':file,'sha256':hashlib.sha256((out/file).read_bytes()).hexdigest()});write(out/'index.json',idx)
  print('V3_D',file,'seed',d['seed_variant'],'sweeps',len(d['return_history_D']),'seconds',round(d['elapsed_seconds_D'],2),flush=True)
# Summary must enumerate the actually present variants, not hardcode A/B only.
p=B/'verify.py';text=p.read_text(encoding='utf-8');old="for v in ['BASE','A','B']}";assert old in text;text=text.replace(old,"for v in sorted({r['variant']for r in rows})}");p.write_text(text,encoding='utf-8')
print('V3_D_COMPLETE cells=12')
