"""TASK-D-003 documentary/package audit; --write records final local manifest, default verifies it."""
from pathlib import Path
from urllib.parse import unquote
from hashlib import sha256
from fractions import Fraction
import sys,re,json,subprocess,shutil

ROOT=Path(__file__).resolve().parents[7];R='docs/project_management/change_plans/ui-chart-wheel/';DEV=R+'developer/';EV=DEV+'evidence/task_d003_research/';INPUT='8fb25770169166a3a4e94110eee684bd8b116474'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.PIPE)
def lf(b):return b.replace(b'\r\n',b'\n')
def read(p):return lf((ROOT/p).read_bytes())
def blob(sha,p):return git('show',sha+':'+p)
def digest(b):return sha256(b).hexdigest()
def jsonread(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
assert git('branch','--show-current').decode().strip()=='dev/ui-chart-wheel'
assert git('rev-parse','HEAD').decode().strip()==INPUT
assert not git('diff','--cached','--name-only').strip(),'index must remain empty'
pins=['f6f289cda25e7f228dff064175805130cc770b63','435337f49b200ca308ae9620efa9902adf1677f9','5de9e66c26496880f714f61f78126972dee4fbdd','2634b224894b1046113557bfe241f0a5f2d46f8c','c59cc3f68e7769841134801dc125633decade032']
for pin in pins:git('merge-base','--is-ancestor',pin,INPUT)
allowed_modified={R+'developer_artifact.md',DEV+'implementation_plan.md',DEV+'task_d003_implementation_plan.md',DEV+'findings.md',DEV+'checks.md'}
newdocs={DEV+'task_d003_research_report.md',DEV+'drawing_adr_draft.md',DEV+'sequence_diagrams/ui/001-result-renderer-lifecycle.puml',DEV+'sequence_diagrams/ui/002-acceptance-selection-focus.puml'}
modified=set(git('diff','--name-only',INPUT).decode().splitlines());assert modified==allowed_modified,modified
untracked=set(git('ls-files','--others','--exclude-standard').decode().splitlines());assert all(p in newdocs or p.startswith(EV) for p in untracked),untracked-newdocs
assert newdocs<=untracked
assert not git('diff','--name-only',INPUT,'--','src','tests','docs/requirements','docs/sequence_diagrams','docs/development_approach',R+'manager_artifact.md',R+'analyst_artifact.md',R+'tester_artifact.md').strip()
for path in [R+'developer_artifact.md',DEV+'findings.md',DEV+'checks.md']:assert read(path).startswith(blob(INPUT,path)),('historical prefix',path)
for role,pin in [('developer','f9c70f75ea815b2f3bf7e01426ee5afe65b31606'),('analyst','2634b224894b1046113557bfe241f0a5f2d46f8c')]:
    p=R+role+'/package_manifest.json';assert read(p)==blob(INPUT,p)
    data=json.loads(blob(pin,p))['files'];pairs=[(x['path'],x['sha256'])for x in data]if isinstance(data,list)else[(R+k,v)for k,v in data.items()]
    assert len(pairs)==9
    for path,h in pairs:assert digest(blob(pin,path))==h,path
for path in git('ls-tree','-r','--name-only',INPUT,'--',DEV).decode().splitlines():
    if path not in allowed_modified:assert read(path)==blob(INPUT,path),('old evidence changed',path)
# Pin start-time source snapshots; only the Developer plan was subsequently updated.
m=jsonread(EV+'inputs_manifest.json')
for path,h in m['sources'].items():
    if path in allowed_modified:
        b=blob(INPUT,path);assert h in [digest(b),digest(b.replace(b'\n',b'\r\n'))],path
    else:assert sha256((ROOT/path).read_bytes()).hexdigest()==h,path
for name in ['inputs_manifest.json','inputs_manifest_v2.json']:
    for p,h in jsonread(EV+name)['inputs'].items():assert sha256((ROOT/EV/p).read_bytes()).hexdigest()==h,p
fixture=jsonread(EV+'fixtures_v2.json');assert fixture['F3']['angles']==fixture['F1']['angles']
for key,lng in dict(mercury=359.7,venus=359.85,mars=0,jupiter=.15,saturn=.3).items():
    p=next(p for p in fixture['F3']['points']if p['id']==key);assert p['longitude']==lng and p['retrograde']
assert len(fixture['F3-max']['points'])==16
for a,b in [('asc','dsc'),('mc','ic')]:assert (Fraction(str(fixture['F3-max']['angles'][b]['longitude']))-Fraction(str(fixture['F3-max']['angles'][a]['longitude'])))%360==180
idx=jsonread(EV+'run03/browser_matrix.json');assert len(idx['records'])==24
for ref in idx['records']:
    p=EV+'run03/'+ref['file'];assert digest((ROOT/p).read_bytes())==ref['sha256'];d=jsonread(p)
    assert digest((ROOT/(EV+'run03/'+d['screenshot'])).read_bytes())==d['screenshot_sha256']
    assert d['measurement']['unchanged'];assert d['verifier']['anchorPass'] and d['verifier']['C0Matches'] and d['verifier']['sizePass']
    for k in d['keyboard']:
        if 'activation'in k:
            a=k['activation'];assert a['before']['scroll']==a['toggle']['scroll'];assert a['before']['calls']==a['toggle']['calls']
totals=jsonread(EV+'drawing_audit_v2.json')['totals'];assert totals=={'cells':24,'native_probes':7446,'native_wrong':1679,'keyboard_targets':438,'keyboard_failed':0,'complete_geometry_cells':6,'full_matrix_pass':False},totals
stop=jsonread(EV+'experiment_stop.json');assert 0<stop['elapsed_hours_including_harness_data_repairs_measurements']<=6
def anchors(text):
    result=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
    for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title);slug=re.sub(r'\s','-',re.sub(r'[^\w\s-]','',title.lower()));n=counts.get(slug,0);counts[slug]=n+1;result.add(slug if n==0 else f'{slug}-{n}')
    return result
manifest_path=ROOT/(EV+'package_manifest.json')
if '--write'in sys.argv and not manifest_path.exists():manifest_path.write_text('{}\n',encoding='utf-8')
documents=list((ROOT/R).rglob('*.md'));links=tables=0
for path in documents:
    text=path.read_text(encoding='utf-8');width=None;fenced=False
    for line in text.splitlines():
        if line.startswith('```'):fenced=not fenced
        if not fenced and line.startswith('|'):
            n=len(re.split(r'(?<!\\)\|',re.sub(r'`[^`]+`','CODE',line)))
            if width is None:tables+=1
            assert width is None or n==width,(str(path.relative_to(ROOT)),line);width=n
        else:width=None
        assert line==line.rstrip(),('trailing whitespace',str(path.relative_to(ROOT)))
    for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z]+:',dest):continue
        part,_,anchor=unquote(dest).partition('#');target=(path.parent/part).resolve()if part else path
        assert target.exists(),(path.relative_to(ROOT).as_posix(),dest)
        if anchor and target.suffix=='.md':assert anchor in anchors(target.read_text(encoding='utf-8')),(path.relative_to(ROOT).as_posix(),dest,'anchor')
        links+=1
pumls=[]
for name in ['001-result-renderer-lifecycle.puml','002-acceptance-selection-focus.puml']:
    path=ROOT/(DEV+'sequence_diagrams/ui/'+name);s=path.read_text(encoding='utf-8');assert s.count('@startuml')==s.count('@enduml')==1 and 'DRAFT'in s
    actors=set();stack=[];notes=0
    for line in s.splitlines():
        line=line.strip();decl=re.match(r'^(?:participant|control|actor|boundary|collections)\s+(?:"[^"]+"\s+as\s+)?(\w+)$',line)
        if decl:actors.add(decl[1])
        edge=re.match(r'^(\w+)\s*[-.]+[<>][-.<>]*\s*(\w+)\s*:',line)
        if edge:assert edge[1]in actors and edge[2]in actors,(name,line)
        if re.match(r'^(alt|opt|loop|group|critical|par|break)\b',line):stack.append(line)
        if line=='end':assert stack,(name,'unmatched end');stack.pop()
        if line.startswith('note '):notes+=1
        if line=='end note':notes-=1
    assert not stack and notes==0,name;pumls.append(name)
adr_numbers=[int(p.name[:4])for p in(ROOT/'docs/requirements/decisions').glob('[0-9][0-9][0-9][0-9]-*.md')];assert max(adr_numbers)==41
check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
results={'task':'TASK-D-003','input_sha':INPUT,'branch':'dev/ui-chart-wheel','published':False,'pins_ancestry':len(pins),'historical_manifests':'9/9 + 9/9 at source Git commits; manifests unchanged','sources':len(m['sources']),'docs':len(documents),'links':links,'tables':tables,'puml_structural':pumls,'puml_render':'NOT_RUN; Java/PlantUML unavailable in inspected environment','adr_current_max':41,'scope':'Developer only; Manager/foreign roles/production/contracts/golden unchanged','index':'EMPTY','git_diff_check':{'exit':check.returncode,'stdout':check.stdout,'stderr':check.stderr},'matrix':totals,'experiment_hours':stop['elapsed_hours_including_harness_data_repairs_measurements'],'limitations':'see report; no production acceptance or global layout impossibility claim'}
output=ROOT/(EV+'validation_results.json')
if '--write'in sys.argv:output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:assert jsonread(EV+'validation_results.json')==results,'validation result drift'
paths=sorted(modified|set(git('ls-files','--others','--exclude-standard').decode().splitlines()))
paths=[p for p in paths if p!=EV+'package_manifest.json']
payload={'task':'TASK-D-003','author':'Codex / Developer','input_sha':INPUT,'technical_package_sha':'NOT_CREATED; local uncommitted worktree','state':'DRAFT local technical research, not G3','encoding':'sha256_lf for text, raw for PNG; manifest excludes itself','files':[{'path':p,'sha256_lf_or_binary':digest((ROOT/p).read_bytes()if p.endswith('.png')else read(p))}for p in paths]}
if '--write'in sys.argv:manifest_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:assert json.loads(manifest_path.read_text(encoding='utf-8'))==payload,'package hash drift'
print(f'D003_PACKAGE_AUDIT_OK paths={len(paths)+1} docs={len(documents)} links={links} tables={tables} source_hashes={len(m["sources"])} PUML=2_STRUCTURE_ONLY manifests=9/9+9/9 index=EMPTY foreign=UNCHANGED diff_check=0 local_DRAFT')
