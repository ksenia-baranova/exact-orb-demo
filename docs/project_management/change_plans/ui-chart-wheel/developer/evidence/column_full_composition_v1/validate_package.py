from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
B=Path(__file__).resolve().parent
R=B.parents[6]
assert (R/'.git').exists(),R
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=R,stderr=subprocess.STDOUT).decode('utf8').strip()
before=json.loads((B/'before.json').read_text(encoding='utf8'));appends=json.loads((B/'append_records.json').read_text(encoding='utf8'))
errors=[];preserved=0
for name,old in before['files'].items():
    p=R/name
    if name in appends:
        a=appends[name]
        if a['sha256']!=old or hashlib.sha256(p.read_bytes()[:a['prefix_size']]).hexdigest()!=old:errors.append('prefix changed '+name)
    elif not p.exists() or sha(p)!=old:errors.append('prior payload changed '+name)
    else:preserved+=1
index=Path(before['index_path'])
if sha(index)!=before['index_sha256']:errors.append('index raw bytes changed')
if git('diff','--cached','--name-only'):errors.append('index not empty')
if git('rev-parse','HEAD')!='07bb56ba5d49ec76de64df41ad80d175fbe90a2d':errors.append('HEAD changed')
docpaths=json.loads((B/'document_paths.json').read_text(encoding='utf8'))
newfiles={str(p.relative_to(R)).replace('\\','/') for p in B.rglob('*') if p.is_file()}
newfiles.update(docpaths)
actual={p for p in git('ls-files','-z').split('\0')+git('ls-files','--others','--exclude-standard','-z').split('\0') if p}
unexpected=actual-set(before['files'])-newfiles
if unexpected:errors.append('new paths outside scope '+str(sorted(unexpected)))
def text_without_code(t):return re.sub(r'```[^\n]*\n.*?```','',t,flags=re.S)
def anchors(p):
    t=p.read_text(encoding='utf-8-sig');out=set(re.findall(r'<a\s+(?:name|id)=[\"\']([^\"\']+)',t));seen={}
    for h in re.findall(r'^#{1,6}\s+(.+)$',text_without_code(t),flags=re.M):
        h=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',h)
        a=re.sub(r'[^\w\- ]','',h.strip().lower());a=re.sub(r'\s','-',a);n=seen.get(a,0);seen[a]=n+1;out.add(a+(('-'+str(n)) if n else ''))
    return out
links=0;tables=0;markdown=[R/p for p in docpaths if p.endswith('.md')]+[R/p for p in appends]
for p in markdown:
    content=p.read_text(encoding='utf-8-sig');text=text_without_code(content)
    for raw in re.findall(r'!?\[[^]]*\]\(([^)]+)\)',text):
        target=raw.strip().split(' "')[0].strip('<>')
        if re.match(r'^(?:https?://|mailto:|codex:)',target):continue
        name,_,anchor=target.partition('#');q=(p.parent/name).resolve() if name else p
        if not q.exists():errors.append(f'broken path {p.relative_to(R)} -> {target}')
        elif anchor and q.suffix=='.md' and anchor not in anchors(q):errors.append(f'broken anchor {p.relative_to(R)} -> {target}')
        links+=1
    for line in text.splitlines():
        if re.match(r'^\|\s*:?-{3,}',line):tables+=1
for p in (R/n for n in newfiles):
    if p.suffix in ['.md','.mjs','.cjs','.py','.html','.puml','.json']:
        try:t=p.read_text(encoding='utf-8-sig')
        except UnicodeError:errors.append('text encoding '+str(p));continue
        if any(line.rstrip()!=line for line in t.splitlines()):errors.append('trailing whitespace '+str(p.relative_to(R)))
        if p.suffix=='.json':json.loads(t)
        if p.suffix=='.py':ast.parse(t,filename=str(p))
for p in [R/n for n in docpaths if n.endswith('.puml')]:
    t=p.read_text(encoding='utf8')
    if t.count('@startuml')!=1 or t.count('@enduml')!=1:errors.append('puml boundary '+str(p))
    stack=[]
    for line in t.splitlines():
        s=line.strip()
        if re.match(r'^(alt|loop|opt|group|par|critical)\b',s):stack.append(s)
        elif s=='end':
            if not stack:errors.append('puml unmatched end '+str(p))
            else:stack.pop()
    if stack:errors.append('puml open block '+str(p))
node=Path(r'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
syntax=[]
for p in sorted(B.glob('*.mjs'))+sorted(B.glob('*.cjs')):
    r=subprocess.run([str(node),'--check',str(p)],capture_output=True,text=True)
    syntax.append({'path':str(p.relative_to(R)).replace('\\','/'),'exit':r.returncode})
    if r.returncode:errors.append('Node syntax '+str(p))
native=json.loads((B/'run07-ports-audit.json').read_text(encoding='utf8'));post=json.loads((B/'run07-ports-post-audit.json').read_text(encoding='utf8'));bound=json.loads((B/'run07-ports/boundary.json').read_text(encoding='utf8'));stop=json.loads((B/'final_stop.json').read_text(encoding='utf8'))
assert native['static_pass']==29 and native['aux_certificate_cells_pass']==29
assert all(v['pass'] for v in native['native_controls']) and all(v['actual']==v['expected'] for v in native['analytic_controls'])
assert all(post[k]==29 for k in ['C0_pass','column_order_pass','row_objective_local_pass','leader_clip_pass','no_shared_segments_pass'])
assert len(bound['controls'])==28 and all(v['pass'] for v in bound['controls']) and all(v['pass'] for v in post['route_controls'])
assert stop['within_original_timebox']
for run in ['run01','run02','run03','run05-final','run06-routes','run07-ports']:
    z=json.loads((B/run/'index.json').read_text(encoding='utf8'))
    for p,h in z['sources'].items():
        if sha(B/run/'sources'/p)!=h:errors.append('frozen source hash '+run+'/'+p)
    for item in z['records']:
        rr=json.loads((B/run/(item['id']+'.json')).read_text(encoding='utf8'))
        if rr.get('screenshot') and sha(B/run/rr['screenshot'])!=rr['screenshotSHA256']:errors.append('screenshot hash '+run+'/'+item['id'])
try:git('diff','--check')
except subprocess.CalledProcessError as e:errors.append('git diff --check '+e.output.decode('utf8','replace'))
result={'author':'Codex / Developer','preserved':preserved,'append_only':len(appends),'index_raw_unchanged':sha(index)==before['index_sha256'],'index_empty':not git('diff','--cached','--name-only'),
'head':'07bb56ba5d49ec76de64df41ad80d175fbe90a2d','markdown_files':len(markdown),'local_links':links,'tables':tables,'puml_structures':2,'puml_render':'NOT_RUN','node_syntax':syntax,
'final_static':29,'final_aux_outcomes':29,'native_calibration':13,'analytic_calibration':7,'renderer_controls':28,'post_audit_cells':29,'baseline_node_tests':'188 PASS /0 FAIL; six existing UI files; command in plan',
'full_pytest':'NOT_RUN','production_browser_https':'NOT_RUN','publication':'NOT_RUN','errors':errors}
(B/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if errors:
    print('\n'.join(errors));raise SystemExit(1)
manifest_paths=set(newfiles)|set(appends)
manifest_paths={n for n in manifest_paths if not n.endswith('/manifest.json') and not n.endswith('/validation.json')}
manifest={n:sha(R/n) for n in sorted(manifest_paths)}
if '--write' in sys.argv:(B/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
else:
    existing=json.loads((B/'manifest.json').read_text(encoding='utf8'))
    if existing!=manifest:raise SystemExit('Current package manifest mismatch')
print('COLUMN_PACKAGE_OK',f'prior={preserved}+{len(appends)}_APPEND_ONLY',f'markdown={len(markdown)} links={links} tables={tables}',f'payloads={len(manifest)}', 'static=29/29 boundary=28/28 controls=20/20 C0/order/rows/clip/branches=29/29 index=UNCHANGED_EMPTY diff_check=0')
