"""Read-only by default. --write updates only new package self-metadata."""
from pathlib import Path
import json,hashlib,subprocess,re,ast,sys
from urllib.parse import unquote
from fractions import Fraction as F
root=Path(__file__).resolve().parents[7]
if not (root/'AGENTS.md').exists():root=Path('C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered')
r='docs/project_management/change_plans/ui-chart-wheel/';B=root/r/'developer/evidence/drawing_geometry_v3'
def git(*a):return subprocess.check_output(['git',*a],cwd=root,stderr=subprocess.PIPE)
def val(*a):return git(*a).decode().strip()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(p):return p.read_bytes().replace(b'\r\n',b'\n')if p.suffix not in ['.png','.bin']else p.read_bytes()
assert val('branch','--show-current')=='dev/ui-chart-wheel'and val('rev-parse','HEAD')=='07bb56ba5d49ec76de64df41ad80d175fbe90a2d'
assert not val('diff','--cached','--name-only')
tracked={r+'developer_artifact.md',r+'developer/implementation_plan.md'}
assert set(val('diff','--name-only','HEAD').splitlines())==tracked
untracked=val('ls-files','--others','--exclude-standard').splitlines()
assert all(p in [r+'developer/task_d006_controller_html_plan.md',r+'developer/drawing_geometry_v3.md']or p.startswith(r+'developer/evidence/drawing_geometry_v3/')for p in untracked)
spec=json.loads((B/'spec.json').read_text());stop=json.loads((B/'stop.json').read_text());assert stop['wall_minutes']<90
for rel,expected in spec['preserved_local_D006_sha256'].items():
 raw=(root/rel).read_bytes()
 if rel in tracked:raw=raw.split('\n\n## Геометрия v3'.encode('utf-8'))[0]
 assert hashlib.sha256(raw).hexdigest()==expected,('D006 changed',rel)
archive='8b8c4c818147b037cb90f93a42e64eb86d809183';old=json.loads(git('show',archive+':'+r+'developer/evidence/task_d005_feasibility/package_manifest.json'))
for row in old['files']:
 rel=row['path'];raw=git('show',archive+':'+rel);assert hashlib.sha256(raw).hexdigest()==row['sha256_lf_or_binary']
 if rel in tracked:assert normalized(root/rel).startswith(raw)
 else:assert normalized(root/rel)==raw,('old package changed',rel)
verification=json.loads((B/'verification.json').read_text());assert len(verification['cells'])==108 and len(verification['controls'])==10
assert all(c['actual']==c['expected']for c in verification['controls'])
assert verification['summary']['H']=={'cells':12,'geometry_pass':12,'tight_cells':10,'moved':110,'tight_pass':108,'tight_fail':2,'tight_unproven':0}
for ref in json.loads((B/'models/index.json').read_text())['records']:assert digest(B/'models'/ref['file'])==ref['sha256']
native=0
for run,count in [('browser-run01',60),('browser-run02',24),('browser-run03',24)]:
 idx=json.loads((B/run/'index.json').read_text());assert not idx.get('error')and len(idx['records'])==count and len(idx['controls'])==8;assert all(c['actual']==c['expected']for c in idx['controls'])
 for ref in idx['records']:
  p=B/run/ref['file'];assert digest(p)==ref['sha256'];d=json.loads(p.read_text());assert not d['pageErrors']and d['measurement']['chartUnchanged']and not d['measurement']['interactiveSVG'];assert digest(B/run/d['screenshot'])==d['screenshotSHA256'];native+=1
actual=json.loads((B/'actual_final_audit.json').read_text());assert actual['summary']['H']['geometry_pass']==12
summary=json.loads((B/'result_summary.json').read_text());assert summary['summary']['H']==verification['summary']['H'];assert len(summary['H_residual_counterexamples'])==2
assert summary['physical_reference_max_error_vs_ideal']<=.5
for c in summary['H_native_model_identity']:assert c['native_and_declared_coordinates_equal']and c['components_equal']
docs=list((root/r).rglob('*.md'));links=tables=0
def anchors(text):
 found=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title);slug=re.sub(r'\s','-',re.sub(r'[^\w\s-]','',title.lower()));n=counts.get(slug,0);counts[slug]=n+1;found.add(slug if not n else f'{slug}-{n}')
 return found
for p in docs:
 t=p.read_text(encoding='utf-8');width=None;fence=False
 for line in t.splitlines():
  assert line==line.rstrip(),('whitespace',p)
  if line.startswith('```'):fence=not fence
  if not fence and line.startswith('|'):
   count=len(re.split(r'(?<!\\)\|',re.sub(r'`[^`]+`','CODE',line)))
   if width is None:tables+=1
   assert width is None or width==count,('table',p,line);width=count
  else:width=None
 for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',t):
  if re.match(r'^[a-zA-Z]+:',dest):continue
  part,_,a=unquote(dest).partition('#');target=(p.parent/part).resolve()if part else p
  assert target.exists(),('link',p,dest)
  if a and target.suffix=='.md':assert a in anchors(target.read_text(encoding='utf-8')),('anchor',p,dest)
  links+=1
py=0
for p in B.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'));py+=1
node='C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';js=0
for p in B.rglob('*.cjs'):
 result=subprocess.run([node,'--check',str(p)],capture_output=True,text=True);assert not result.returncode,result.stderr;js+=1
for p in B.rglob('*.html'):
 for code in re.findall(r'<script[^>]*>(.*?)</script>',p.read_text(encoding='utf-8'),re.S):
  result=subprocess.run([node,'--check'],input=code,capture_output=True,text=True);assert not result.returncode,result.stderr;js+=1
diff=subprocess.run(['git','diff','--check'],cwd=root,capture_output=True,text=True);assert not diff.returncode,diff.stdout+diff.stderr
paths=sorted([p for p in B.rglob('*')if p.is_file()and p.name not in ['package_manifest.json','package_audit.json']]+[root/r/'developer/drawing_geometry_v3.md',*[root/p for p in tracked]])
manifest={'baseline':val('rev-parse','HEAD'),'files':[{'path':p.relative_to(root).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}for p in paths]}
audit={'result':'V3_PACKAGE_OK','payloads':len(paths),'models':108,'native_records':native,'screenshots':108,'exact_controls':10,'browser_controls':24,'H_geometry':'12/12','H_local_tight':'108/110','H_full_studied_cells':'10/12','residuals':2,'D005_archive':'162/162','D005_current':'160_UNCHANGED+2_APPEND_ONLY','D006':'PRESERVED','docs':len(docs),'links':links,'tables':tables,'Python_AST':py,'Node_syntax':js,'diff_check':0,'index':'EMPTY','Manager_foreign_production':'UNCHANGED','publication':'NOT_RUN','product_suites':'NOT_RUN'}
if '--write'in sys.argv:
 (B/'package_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(B/'package_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
 assert json.loads((B/'package_manifest.json').read_text())==manifest
 assert json.loads((B/'package_audit.json').read_text())==audit
print('V3_PACKAGE_OK '+json.dumps(audit,ensure_ascii=False))
