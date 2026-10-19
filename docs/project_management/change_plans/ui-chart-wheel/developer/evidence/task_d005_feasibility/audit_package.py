"""Document/package/provenance audit. No browser, placement or experiment execution."""
from pathlib import Path
from hashlib import sha256
import ast,datetime,json,re,shutil,subprocess,sys
B=Path(__file__).parent;ROOT=B.parents[6];R='docs/project_management/change_plans/ui-chart-wheel/'
BASE='34f187aa81ddad7760089f54c1dc23d4d9e59d59';D003='d24a24e04be32d0522674735388e9d2ea3e65c93'
OUT=B/'package_audit.json';MANIFEST=B/'package_manifest.json';WRITING='--write'in sys.argv
own={R+p for p in ['developer_artifact.md','developer/task_d005_implementation_plan.md','developer/implementation_plan.md','developer/drawing_adr_draft.md','developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml','developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml','developer/task_d005_feasibility_report.md','developer/task_d005_findings.md']}
prefix=R+'developer/evidence/task_d005_feasibility/'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.PIPE)
def val(*args):return git(*args).decode().strip()
def normalized(path):
 raw=path.read_bytes();return raw if path.suffix.lower()in{'.png','.bin','.sqlite','.db','.jpg','.jpeg','.ico'}else raw.replace(b'\r\n',b'\n')
def digest(raw):return sha256(raw).hexdigest()
assert val('branch','--show-current')=='dev/ui-chart-wheel'
assert val('rev-parse','HEAD')==BASE
assert not val('diff','--cached','--binary'),'preserve original EMPTY index'
assert val('log','-1','--format=%H',BASE,'--',R+'manager/prompts/task-d-005-drawing-feasibility-v2.md')=='0046ac75bd6582089b68a640f98fa65468c0607a'
start=json.loads((B/'execution_start.json').read_text(encoding='utf-8'))
mutated=own-{R+'developer/task_d005_findings.md',R+'developer/task_d005_feasibility_report.md'}
baseline_checked=0
for path,h in start['baseline_hashes'].items():
 if path in mutated:continue
 assert digest(normalized(ROOT/path))==h,('unrelated/baseline changed',path);baseline_checked+=1
for path in [R+'developer_artifact.md',R+'developer/implementation_plan.md']:
 assert normalized(ROOT/path).startswith(git('show',BASE+':'+path)),('historical prefix',path)
assert git('show',BASE+':'+R+'developer/task_d005_implementation_plan.md')in normalized(ROOT/(R+'developer/task_d005_implementation_plan.md'))
old=json.loads(git('show',D003+':'+R+'developer/evidence/task_d003_research/package_manifest.json'))
for row in old['files']:assert digest(git('show',D003+':'+row['path']))==row['sha256_lf_or_binary'],('D003 archive',row['path'])
tracked=set(val('diff','--name-only','HEAD').splitlines());untracked=set(val('ls-files','--others','--exclude-standard').splitlines());changed=tracked|untracked
assert own<=changed,('missing own output',own-changed)
assert all(p in own or p.startswith(prefix)for p in changed),('scope',changed-own-{p for p in changed if p.startswith(prefix)})
assert tracked==mutated,tracked
spec_hash=digest((B/'model_spec.json').read_bytes());aidx=json.loads((B/'analytic/index.json').read_text());assert spec_hash==aidx['spec_sha256']
oldfixtures=json.loads((B.parent/'task_d003_research/fixtures_v2.json').read_text(encoding='utf-8'))
for ref in aidx['cells']:
 raw=(B/'analytic'/ref['file']).read_bytes();assert digest(raw)==ref['sha256'];d=json.loads(raw);assert d['chart']==oldfixtures[d['fixture']]
analysis=json.loads((B/'analytic/verification.json').read_text(encoding='utf-8'));assert len(analysis['controls'])==9
assert all(c['actual']==c['expected']for c in analysis['controls'])
browser={};pointer_checks=keyboard_checks=0
for run in ['run04','run04-delivery']:
 idx=json.loads((B/run/'index.json').read_text(encoding='utf-8'));assert len(idx['records'])==24 and not idx.get('failure')and not idx['pageErrors'];assert spec_hash==idx['meta']['spec_sha256']
 for source,h in idx['meta']['sources'].items():
  candidates=[B/source,B/'sources-run04-initial'/source]
  assert any(p.exists()and digest(p.read_bytes())==h for p in candidates),(run,'source provenance',source)
 for ref in idx['records']:
  raw=(B/run/ref['file']).read_bytes();assert digest(raw)==ref['sha256'];d=json.loads(raw)
  assert digest((B/run/d['screenshot']).read_bytes())==d['screenshot_sha256']
  if run!='run04-delivery':continue
  for x in d['native']:
   events=x['deliveredEvents'];assert any(e['type']=='pointerdown'for e in events)and any(e['type']=='click'for e in events)
   assert x['before']['calls']==x['after']['calls'],'program focus/scroll during pointer activation'
   pointer_checks+=1
  for k in d['keyboard']:
   a,c,t=k['before'],k['after'],k['toggle']
   assert a['active']==c['active']==t['active']==k['expectedId']and a['token']==c['token']==t['token']
   assert c['selected']==k['key']and t['selected']is None and c['connected']and t['connected']and t['visible']
   assert a['calls']==c['calls']==t['calls']and a['scroll']==c['scroll']==t['scroll']
   keyboard_checks+=1
 assert all(c['actual']==c['expected']and c['pass']for c in idx['controls'])and len(idx['controls'])==12
 assert all(c['actual']==c['expected']and c['pass']for c in idx['boundary']['controls'])and len(idx['boundary']['controls'])==12
 browser[run]={'records':len(idx['records']),'source_hashes':len(idx['meta']['sources']),'controls':12,'boundary_controls':12,'wall_seconds':idx['meta']['browserWallSeconds']}
assert pointer_checks==2190 and keyboard_checks==438
actual=json.loads((B/'browser_audit.json').read_text(encoding='utf-8'))['totals']
assert actual['native_wrong']==238 and actual['keyboard_fail']==0 and actual['whole_drawing_PASS']is False
stop=json.loads((B/'experiment_stop_final.json').read_text(encoding='utf-8'));assert stop['wall_within_12h_from_STARTED']and stop['browser_wall_seconds']<4*3600
# The manifest is LF-normalized for text and raw for PNG; it excludes its own two generated metadata files.
payload=sorted(changed-{str(OUT.relative_to(ROOT)).replace('\\','/'),str(MANIFEST.relative_to(ROOT)).replace('\\','/')})
manifest={'task':'TASK-D-005','author':'Codex / Developer','InputSHA':BASE,'AssignmentSHA':start['AssignmentSHA'],'AnalystContractSHA':start['AnalystContractSHA'],'TechnicalPackageV2SHA':'NOT_CREATED; local DRAFT','excluded_self_metadata':['package_audit.json','package_manifest.json'],'files':[{'path':p,'sha256_lf_or_binary':digest(normalized(ROOT/p)),'bytes':len(normalized(ROOT/p))}for p in payload]}
def anchors(text):
 result=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title);slug=re.sub(r'\s','-',re.sub(r'[^\w\s-]','',title.lower()));n=counts.get(slug,0);counts[slug]=n+1;result.add(slug if n==0 else f'{slug}-{n}')
 return result
docs=list((ROOT/R).rglob('*.md'));links=tables=0
for p in docs:
 text=p.read_text(encoding='utf-8');width=None;fence=False
 for line in text.splitlines():
  assert line==line.rstrip(),('whitespace',p)
  if line.startswith('```'):fence=not fence
  if not fence and line.startswith('|'):
   count=len(re.split(r'(?<!\\)\|',re.sub(r'`[^`]+`','CODE',line)))
   if width is None:tables+=1
   assert width is None or count==width,('table',p,line);width=count
  else:width=None
 for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
  if re.match(r'^[a-zA-Z]+:',dest):continue
  from urllib.parse import unquote
  path,_,anchor=unquote(dest).partition('#');target=(p.parent/path).resolve()if path else p
  assert target.exists()or WRITING and target in[OUT.resolve(),MANIFEST.resolve()],('link',p,dest)
  if anchor and target.suffix=='.md':assert anchor in anchors(target.read_text(encoding='utf-8')),('anchor',p,dest)
  links+=1
assert '<!-- MATRIX -->'not in(ROOT/(R+'developer/task_d005_feasibility_report.md')).read_text(encoding='utf-8')
python_sources=list(B.rglob('*.py'))
for p in python_sources:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
node='C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
for name in ['harness.mjs','boundary.mjs','run_browser.cjs']:subprocess.run([node,'--check',str(B/name)],check=True,capture_output=True)
for name in ['001-result-renderer-lifecycle.puml','002-acceptance-selection-focus.puml']:
 text=(ROOT/R/'developer/sequence_diagrams/ui'/name).read_text(encoding='utf-8');assert text.count('@startuml')==text.count('@enduml')==1;stack=[]
 for line in text.splitlines():
  if re.match(r'^\s*(alt|opt|loop|group|critical|par)\b',line):stack.append(line)
  if line.strip()=='end':assert stack;stack.pop()
 assert not stack,(name,stack)
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert diff.returncode==0,diff.stdout+diff.stderr
report={'task':'TASK-D-005','author':'Codex / Developer','InputSHA':BASE,'AssignmentSHA':start['AssignmentSHA'],'AnalystContractSHA':start['AnalystContractSHA'],'branch':'dev/ui-chart-wheel','state':'LOCAL_DRAFT_EXECUTION_COMPLETE','STARTED':start['started_at'],'deadline':start['deadline'],'original_index':'EMPTY','current_index':'EMPTY','output_sha':'NOT_CREATED','changed_paths':sorted(changed|{str(OUT.relative_to(ROOT)).replace('\\','/'),str(MANIFEST.relative_to(ROOT)).replace('\\','/')}),'payload_files':len(payload),'payload_bytes':sum(x['bytes']for x in manifest['files']),'unchanged_baseline_payloads':baseline_checked,'D003_archived_manifest_blobs':len(old['files']),'D003_run03_report_old_manifests_current':'UNCHANGED; current DRAFT ADR/sequences explicitly D005 revisions','Manager_foreign_roles_production':'UNCHANGED','spec_sha256':spec_hash,'analytical_cells':24,'analytical_controls':9,'browser_runs':browser,'authoritative_native_complete_deliveries':pointer_checks,'authoritative_live_keyboard_controls':keyboard_checks,'actual':actual,'markdown_documents':len(docs),'local_links':links,'tables':tables,'python_AST_files':len(python_sources),'node_syntax_files':3,'PUML_structure_files':2,'PUML_render':'NOT_RUN; no renderer used','java_available':shutil.which('java')is not None,'plantuml_available':shutil.which('plantuml')is not None,'diff_check_exit':diff.returncode,'experiment_final_stop':stop,'scope':'eight own documents plus new task_d005_feasibility evidence; no publish/gates/foreign status','not_run':['production/mounted HTTP/HTTPS','runtime F5/S1','whole zodiac/sign palette','whole page overflow predicate','cross-platform/touch/zoom/missing-glyph negative','full product pytest/Node suite','full SVG value-frame writer','PUML render','global optimality/general impossibility']}
if WRITING:
 MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
 assert json.loads(MANIFEST.read_text(encoding='utf-8'))==manifest,'manifest drift'
 assert json.loads(OUT.read_text(encoding='utf-8'))==report,'audit drift'
print(f"D005_PACKAGE_OK payloads={len(payload)} baseline={baseline_checked} D003_archive={len(old['files'])} native=2190 keyboard=438 controls=9+12+12 docs={len(docs)} links={links} tables={tables} AST={len(python_sources)} node=3 PUML_structure=2 diff_check=0 index=EMPTY publication=NOT_RUN")
