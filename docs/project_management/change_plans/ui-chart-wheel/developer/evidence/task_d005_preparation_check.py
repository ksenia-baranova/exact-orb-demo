"""Document-only TASK-D-005 preparation audit. No geometry/solver/browser or application imports."""
from pathlib import Path
from hashlib import sha256
from urllib.parse import unquote
import json,re,subprocess,sys

ROOT=Path(__file__).resolve().parents[6]
R='docs/project_management/change_plans/ui-chart-wheel/'
PLAN=R+'developer/task_d005_implementation_plan.md'
INDEX=R+'developer_artifact.md'
SCRIPT=R+'developer/evidence/task_d005_preparation_check.py'
OUTPUT=R+'developer/evidence/task_d005_preparation.json'
PROMPT=R+'manager/prompts/task-d-005-drawing-feasibility-v2.md'
SUMMARY=R+'manager/review_inputs/task-r-001-r2-summary.md'
HEAD='0046ac75bd6582089b68a640f98fa65468c0607a'
CONTRACT='2736e2848c977ec4c770a9a4dec2a0d7c1b62a71'
PACKAGE='d24a24e04be32d0522674735388e9d2ea3e65c93'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.PIPE)
def read(path):
    value=(ROOT/path).read_bytes()
    return value if path.endswith('.png')else value.replace(b'\r\n',b'\n')
def blob(sha,path):return git('show',sha+':'+path)
def digest(value):return sha256(value).hexdigest()
assert git('branch','--show-current').decode().strip()=='dev/ui-chart-wheel'
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert not git('diff','--cached','--binary').strip(),'original EMPTY index must remain EMPTY'
assignment=git('log','-1','--format=%H',HEAD,'--',PROMPT).decode().strip();assert assignment==HEAD
initial=git('log','--reverse','--format=%H',HEAD,'--',PROMPT).decode().splitlines()[0];assert initial=='0e590fa23d6c3f31d59a59cd0f7cb5be3509d160'
summary_sha=git('log','-1','--format=%H',HEAD,'--',SUMMARY).decode().strip();assert summary_sha==initial
pins={'AssignmentSHA':assignment,'AnalystContractSHA':CONTRACT,'TechnicalPackageSHA_D003':PACKAGE,'CriteriaSHA':'f6f289cda25e7f228dff064175805130cc770b63','AnalystV3':'2634b224894b1046113557bfe241f0a5f2d46f8c','A005':'4057d6ed37b24e082a2a4089eb7104da80d17ee5','T004':'ad5206e30d855e44a9535f89dced1d8fe4699d17','S1Owner':'b4418ae1c531ff4726be2769422056d8b059b96d','ManagerR001SummarySHA':summary_sha,'MainBaseline':'535551026af6eedaf2a0aa5c0daa96fa94655ec1'}
for pin in pins.values():git('merge-base','--is-ancestor',pin,HEAD)
contract_paths=[R+'analyst/requirements.md',R+'analyst/scenarios.md']+[R+f'analyst/sequence_diagrams/ui/{n}'for n in ['001-chart-presentation.puml','002-wheel-table-selection.puml','003-edit-and-recovery.puml']]
for p in contract_paths:assert read(p)==blob(CONTRACT,p),p
sources=[PROMPT,SUMMARY,R+'manager_artifact.md',R+'analyst_artifact.md',R+'tester/task_t004_review.md',R+'developer/drawing_adr_draft.md',R+'developer/task_d003_research_report.md',R+'developer/implementation_plan.md',R+'developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml',R+'developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml','AGENTS.md','docs/development_approach/skills/developer/SKILL.md','docs/development_approach/process/process.md','docs/development_approach/roles.md','docs/development_approach/artifacts/developer.md','docs/development_approach/artifacts/developer-prompt.md','docs/requirements/decisions/README.md','src/exact_orb/http_api/ui/facts.mjs','src/exact_orb/http_api/ui/main.mjs','src/exact_orb/http_api/ui/session.mjs','src/exact_orb/http_api/ui/recovery.mjs','tests/ui/facts.test.mjs','tests/ui/session.test.mjs','tests/ui/recovery.test.mjs']+contract_paths
source_hashes={p:digest(blob(HEAD,p))for p in sources}
for p,h in source_hashes.items():assert digest(read(p))==h,p
# Published D003 package is immutable. INDEX gains only a new role-owned handoff.
old_manifest=json.loads(blob(PACKAGE,R+'developer/evidence/task_d003_research/package_manifest.json'))
for row in old_manifest['files']:
    p=row['path'];b=blob(PACKAGE,p);assert digest(b)==row['sha256_lf_or_binary'],p
    if p==INDEX:assert read(p).startswith(b),p
    else:assert read(p)==b,('D003 payload modified',p)
for p in git('ls-tree','-r','--name-only',HEAD,'--',R+'developer').decode().splitlines():assert read(p)==blob(HEAD,p),('old Developer material modified',p)
assert read(INDEX).startswith(blob(HEAD,INDEX))
assert not git('diff','--name-only',PACKAGE,HEAD,'--','src','tests','docs/requirements','docs/sequence_diagrams','docs/development_approach').strip()
allowed={PLAN,INDEX,SCRIPT,OUTPUT}
changed=set(git('diff','--name-only',HEAD).decode().splitlines())|set(git('ls-files','--others','--exclude-standard').decode().splitlines())
assert changed|{OUTPUT}==allowed,changed
assert set(git('diff','--name-only',HEAD).decode().splitlines())=={INDEX}
# Arithmetic of the documentary estimate only; no certificate or runtime control is evaluated.
phases={'input_model_preparation':[3,4],'analytical_comparison':[3,4],'browser_and_harness':[3,4],'draft_ADR_sequences_HTML_design':[4,6],'package_handoff':[3,6]}
estimate=[sum(v[i]for v in phases.values())for i in [0,1]];assert estimate==[16,24]
experiment=[sum(phases[k][i]for k in ['input_model_preparation','analytical_comparison','browser_and_harness'])for i in [0,1]];assert experiment==[9,12]
forecast={'D003_historical_preparation':[20,28],'drawing_including_D005':[28,44],'controller_including_HTML_and_D005':[16,24],'integration_docs_including_D005':[8,16]};assert [sum(v[i]for v in forecast.values())for i in [0,1]]==[72,112]
def anchors(text):
    result=set(re.findall(r'<a\s+id="([^"]+)"',text));counts={}
    for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title);slug=re.sub(r'\s','-',re.sub(r'[^\w\s-]','',title.lower()));n=counts.get(slug,0);counts[slug]=n+1;result.add(slug if n==0 else f'{slug}-{n}')
    return result
documents=list((ROOT/R).rglob('*.md'));links=tables=0
for path in documents:
    t=path.read_text(encoding='utf-8');width=None;fence=False
    for line in t.splitlines():
        assert line==line.rstrip(),('whitespace',str(path.relative_to(ROOT)))
        if line.startswith('```'):fence=not fence
        if not fence and line.startswith('|'):
            count=len(re.split(r'(?<!\\)\|',re.sub(r'`[^`]+`','CODE',line)))
            if width is None:tables+=1
            assert width is None or count==width,(path,line);width=count
        else:width=None
    for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',t):
        if re.match(r'^[a-zA-Z]+:',dest):continue
        part,_,anchor=unquote(dest).partition('#');target=(path.parent/part).resolve()if part else path
        assert target.exists()or('--write'in sys.argv and target==(ROOT/OUTPUT).resolve()),(str(path.relative_to(ROOT)),dest)
        if anchor and target.suffix=='.md':assert anchor in anchors(target.read_text(encoding='utf-8')),(str(path.relative_to(ROOT)),dest,'anchor')
        links+=1
plan=read(PLAN).decode();handoff=read(INDEX)[len(blob(HEAD,INDEX)):].decode()
assert 'STARTED D005 не объявлен'in plan and 'STARTED D005 не объявлен'in handoff
for code in ['R001-01','R001-02','R001-03','R001-04','720','448','328','HTML-presenter','16–24','S1','A006','T007','R002']:assert code in plan,code
check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
report={'task':'TASK-D-005','author':'Codex / Developer','revision':'assessment-v1-DRAFT-before-execution-approval','original_head':PACKAGE,'actual_head':HEAD,'AssignmentSHA':assignment,'initial_assignment_sha':initial,'pins':pins,'reviewer_OutputSHA':None,'R001_provenance':'published Manager summary only, no original reviewer package','source_hashes_lf':source_hashes,'contract_hashes_verified':5,'D003_manifest_payloads_verified':len(old_manifest['files']),'D003_run03_old_ADR_sequences':'UNCHANGED','index_original':'EMPTY','index_after':'EMPTY','own_paths':sorted(allowed),'estimate_hours':estimate,'estimate_person_days':[2,3],'confidence':'medium bounded result; below medium positive 328 feasibility','phase_hours':phases,'experiment_including_preparation_analytics_browser_hours_cap':12,'analytic_hours_cap':4,'browser_harness_hours_cap':4,'whole_forecast_hours':forecast,'whole_forecast_person_days':[9,14],'HTML_presenter_parent':'controller','HTML_presenter_total_hours':[6,10],'HTML_presenter_D005_design_hours':[1,2],'D003_actual_remaining_hours':None,'started_D005':False,'deadline':'end of working day 3 from separate approved STARTED; no absolute calendar deadline','execution_approval':'REQUIRED from Owner for scope/estimate/timebox/deadline plus explicit start','local_links':links,'markdown_documents':len(documents),'markdown_tables':tables,'git_diff_check_exit':check.returncode,'scope':'4 own Developer files; Manager/foreign roles/production/normative contracts unchanged','output_sha':'NOT_CREATED; local preparation','not_run':['SVG/browser/run04','F/E analytical certificates or solver','runtime F5/S1','ADR/sequence revision','Node/pytest/production/HTTPS','PUML render'],'output_payload_sha256_lf':{p:digest(read(p))for p in [PLAN,INDEX,SCRIPT]}}
if '--write'in sys.argv:(ROOT/OUTPUT).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:assert json.loads(read(OUTPUT))==report,'preparation record drift; inspect before rewriting'
print(f'D005_PREPARATION_OK paths=4 estimate=16-24h experiment<=12h browser<=4h docs={len(documents)} links={links} tables={tables} source_hashes={len(source_hashes)} contract=5/5 D003=164/164_UNCHANGED index=EMPTY STARTED=NO spike=NOT_RUN ADR_revision=NOT_RUN diff_check=0')
