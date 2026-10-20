// Independent Tester: actual page/modules, loopback HTTP leaves, native input.
// No placement helper, renderer verifier or Developer assertions are imported.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto"),cp=require("node:child_process");
const {chromium}=require("C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const ROOT=path.resolve(__dirname,"../../../../../../.."),UI=path.join(ROOT,"src/exact_orb/http_api/ui");
const PIN="0da99518ada67603b08ab4220d337e3a5e3aae60",out=path.join(__dirname,"native02");
const fixtures=JSON.parse(fs.readFileSync(path.join(ROOT,"docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/data.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(ROOT,"tests/http_api/golden/session_view.json"),"utf8"));
const hash=x=>crypto.createHash("sha256").update(x).digest("hex"),clone=structuredClone;
if(cp.execFileSync("git",["rev-parse","HEAD"],{cwd:ROOT,encoding:"utf8"}).trim()!==PIN)throw Error("Wrong HEAD");
if(fs.existsSync(out))throw Error("Refuse overwrite native evidence");fs.mkdirSync(out);fs.mkdirSync(path.join(out,"screenshots"));
const report={tested_sha:PIN,author:"Codex / Tester",started_utc:new Date().toISOString(),sources:{},cases:[],scope:"Actual application; HTTP controlled; geometry oracle independent of placement helper"};
for(const f of fs.readdirSync(UI))if(/\.(mjs|css|html)$/.test(f))report.sources[f]=hash(fs.readFileSync(path.join(UI,f),"utf8").replaceAll("\r\n","\n"));
let browser,server;
const save=()=>fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(report,null,2)+"\n");
function check(record,name,condition,actual,expected){record.checks.push({name,pass:!!condition,actual,expected});}
const box=b=>({x:b.x,y:b.y,width:b.width,height:b.height});
async function measure(page){
 return page.evaluate(()=>{
  const rect=n=>{const b=n.getBoundingClientRect();return {left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height}};
  const svg=document.querySelector("#chart-wheel svg"),host=document.querySelector("#chart-wheel");
  const rows=id=>[...document.querySelectorAll("#"+id+" tbody tr")].filter(n=>!n.hidden).map(n=>[...n.children].map(n=>n.textContent));
  const info={svg:!!svg,error:document.querySelector("#wheel-error")?.textContent,errorVisible:!document.querySelector("#wheel-error")?.hidden,
   identity:document.querySelector("#chart-result")?.dataset.chartIdentity,summary:document.querySelector("#chart-birth-summary")?.textContent,
   scrollX:scrollX,scrollY:scrollY,width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth,
   editorHidden:document.querySelector("#birth-editor")?.hidden,active:document.activeElement?.id,
   points:rows("points-table"),houses:rows("houses-table"),angles:rows("angles-table"),aspects:rows("aspects-table"),
   warnings:document.querySelector("#aspect-warnings")?.textContent,
   legend:[...document.querySelectorAll(".aspect-legend-item")].map(n=>({type:n.dataset.aspectType,text:n.textContent})),
   enabledTargets:[...document.querySelectorAll(".fact-select:not(:disabled)")].filter(n=>!n.closest("tr").hidden).map(n=>({label:n.getAttribute("aria-label"),bounds:rect(n)}))};
  if(!svg)return info;
  const first=svg.querySelector("circle"),M=svg.getScreenCTM();
  const svgBox=n=>{const b=n.getBBox(),m=n.getCTM();return [[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]].map(p=>[m.a*p[0]+m.c*p[1]+m.e,m.b*p[0]+m.d*p[1]+m.f]);};
  return {...info,frame:rect(svg),matrix:{a:M.a,b:M.b,c:M.c,d:M.d},C:[first.cx.baseVal.value,first.cy.baseVal.value],R:first.r.baseVal.value,
   sectors:svg.querySelectorAll("[data-sector]").length,houseCount:svg.querySelectorAll("[data-house]").length,
   labels:[...svg.querySelectorAll("[data-label]")].map(g=>({key:g.dataset.label,kind:g.dataset.kind,house:g.dataset.pointHouse,
    parts:[...g.children].filter(n=>n.localName==="rect"&&!n.hasAttribute("data-selected")).map(svgBox),
    components:[...g.querySelectorAll("[data-component]")].map(n=>({key:n.dataset.component,text:n.textContent,size:parseFloat(getComputedStyle(n).fontSize),bounds:svgBox(n)}))})),
   anchors:[...svg.querySelectorAll("[data-anchor]")].map(n=>({key:n.dataset.anchor,x:n.cx.baseVal.value,y:n.cy.baseVal.value})),
   lines:[...svg.querySelectorAll("[data-aspect]")].map(n=>({key:n.dataset.aspect,sourceIndex:+n.dataset.sourceIndex,tag:n.localName,stroke:n.getAttribute("stroke"),dash:n.getAttribute("stroke-dasharray")})),
   passiveTargets:svg.querySelectorAll("a,[tabindex],[onclick],[role=button]").length,
   glyphVectors:[...svg.querySelectorAll("[data-symbol]")].map(n=>({id:n.dataset.symbol,bounds:rect(n),shapes:n.querySelectorAll("path,circle,line").length})),
   selection:[...svg.querySelectorAll("[data-selected]")].map(n=>n.dataset.selected),leaders:[...svg.querySelectorAll("[data-leader]")].map(n=>n.dataset.leader)};
 });
}
function auditGeometry(rec,m,chart){
 if(!m.svg)return;
 const norm=x=>(x%360+360)%360;
 const parts=m.labels.flatMap(g=>g.parts.map(points=>({key:g.key,kind:g.kind,house:g.house,points,
  b:[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]})));
 const gap=(a,b)=>Math.hypot(Math.max(a[0]-b[2],b[0]-a[2],0),Math.max(a[1]-b[3],b[1]-a[3],0));
 const collisions=[];let min=Infinity;
 for(let i=0;i<parts.length;i++)for(let j=i+1;j<parts.length;j++)if(parts[i].key!==parts[j].key){const d=gap(parts[i].b,parts[j].b);min=Math.min(min,d);if(d<2-1e-7)collisions.push({a:parts[i].key,b:parts[j].key,gap:d});}
 check(rec,"native padded component gap >=2",collisions.length===0,{minimum:min,violations:collisions},"2 CSS px (1e-7 serialization arithmetic allowance only)");
 const clipping=parts.filter(p=>p.b[0]<0||p.b[1]<0||p.b[2]>m.frame.width+1e-7||p.b[3]>m.frame.height+1e-7);
 check(rec,"component bounds inside SVG",!clipping.length,clipping,[]);
 const origin=chart.kind==="natal"?chart.angles.asc.longitude:0;
 const wrongHouse=[];
 for(const g of m.labels.filter(g=>g.kind==="point")){
  const source=chart.points.find(p=>p.id===g.key);
  if(String(source.house??"none")!==g.house)wrongHouse.push({key:g.key,reason:"published house differs"});
  if(chart.kind!=="natal")continue;
  const houses=chart.houses.slice().sort((a,b)=>a.number-b.number),i=houses.findIndex(h=>h.number===source.house),a=houses[i].cusp_longitude,b=houses[(i+1)%houses.length].cusp_longitude,span=norm(b-a);
  for(const p of parts.filter(p=>p.key===g.key).flatMap(p=>p.points)){
   const lng=norm(origin+Math.atan2(p[1]-m.C[1],m.C[0]-p[0])*180/Math.PI);
   if(norm(lng-a)>span+1e-7)wrongHouse.push({key:g.key,lng,house:source.house,start:a,end:b});
  }
 }
 check(rec,"glyph and R corners stay in published house",wrongHouse.length===0,wrongHouse,[]);
 const anchorErrors=[];
 for(const anchor of m.anchors){
  const source=chart.points.find(p=>p.id===anchor.key);if(!source)continue;
  const t=(source.longitude-origin)*Math.PI/180,r=Math.hypot(anchor.x-m.C[0],anchor.y-m.C[1]);
  anchorErrors.push({id:source.id,error:Math.hypot(anchor.x-(m.C[0]-r*Math.cos(t)),anchor.y-(m.C[1]+r*Math.sin(t)))});
 }
 check(rec,"true point anchor follows source longitude",anchorErrors.every(x=>x.error<=.5),anchorErrors,"<=0.5 CSS px");
 check(rec,"no external planet leaders",!m.leaders.some(k=>chart.points.some(p=>p.id===k)),m.leaders,"auxiliary only");
 rec.geometry={minimumGap:min,collisions,wrongHouse,anchorErrors};
}
async function openPage(chart,width,height=1000,options={}){
 const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:options.dpr||1}),requests=[],errors=[];
 let current=clone(views.known_ready),failGet=false;current.chart=clone(chart);
 if(chart.kind==="cosmogram"){current.birth.time_unknown=true;current.birth.birth_time=null;current.birth.utc_offset_seconds=null;}
 page.on("pageerror",e=>errors.push(String(e)));
 await page.route("**/session/bootstrap",route=>{requests.push({path:"bootstrap",method:route.request().method()});return route.fulfill({json:{status:"ready",state_version:1}});});
 await page.route("**/charts/current",route=>{requests.push({path:"current",method:route.request().method(),identity:current.chart?.chart_identity});return failGet?route.fulfill({status:503,json:{code:"STATE_READ_FAILED"}}):route.fulfill({json:current});});
 await page.route("**/charts/natal",route=>{requests.push({path:"build",method:route.request().method()});return route.fulfill({status:503,json:{code:"STATE_READ_FAILED"}});});
 await page.goto(base);
 await page.waitForFunction(()=>document.querySelector("#chart-wheel svg")||document.querySelector("#wheel-error:not([hidden])"),null,{timeout:25000});
 return {page,requests,errors,get current(){return current},set current(v){current=v},set fail(v){failGet=v}};
}
let base;
async function refresh(h,view){
 const count=h.requests.filter(r=>r.path==="current").length;if(view)h.current=view;
 await h.page.evaluate(()=>window.dispatchEvent(new Event("online")));
 await h.page.waitForFunction(()=>document.querySelector("#birth-form").getAttribute("aria-busy")==="false");
 if(h.requests.filter(r=>r.path==="current").length===count)await h.page.waitForResponse(r=>r.url().endsWith("/charts/current"));
 await h.page.waitForFunction(id=>document.querySelector("#chart-result")?.dataset.chartIdentity===id||!id,h.current.chart?.chart_identity);
 await h.page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
}
async function main(){
 server=http.createServer((req,res)=>{
  const url=new URL(req.url,"http://localhost");let file;
  if(url.pathname==="/")file=path.join(UI,"index.html");
  else if(/^\/(ui|actual)\/[a-z_]+\.(mjs|html|css)$/.test(url.pathname))file=path.join(UI,path.basename(url.pathname));
  else {res.writeHead(404).end();return;}
  let body=fs.readFileSync(file);
  if(url.pathname==="/ui/wheel_svg.mjs")body=Buffer.from("import {createWheelRenderer as actual} from '/actual/wheel_svg.mjs';export function createWheelRenderer(surface){const leaf=actual(surface);return {dispose(){return leaf.dispose()},update(...args){window.__testerLeafCalls=(window.__testerLeafCalls||0)+1;if(window.__testerLeafFault)throw new Error('tester-leaf-fault');return leaf.update(...args)}}}");
  res.setHeader("Content-Type",file.endsWith(".mjs")?"text/javascript":file.endsWith(".css")?"text/css":"text/html");res.end(body);
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:"C:/Program Files/Google/Chrome/Application/chrome.exe"});
 report.browser=browser.version();report.harness_revision="browser_v2.cjs: bootstrap POST excluded from build counter; other predicates unchanged, initial FAIL preserved";
 report.wrapper="Only renderer leaf instrumentation: positive delegates unchanged production; fault injection selected by flag; all owners/main/session/HTML/layout/SVG are actual";
 const jobs=["sparse","F1","F3","F3-max","published-natal","cosmogram","S1-control","palette-control"].flatMap(name=>[1440,768,360].map(width=>({name,width})));
 for(const {name,width} of jobs){
  const rec={id:name+"-"+width,checks:[]};let h;
  try{
   const chart=fixtures[name].chart;h=await openPage(chart,width);const {page}=h,m=await measure(page);rec.initial=m;rec.fixture_sha256=hash(JSON.stringify(chart));rec.requests=h.requests;rec.errors=h.errors;
   check(rec,"SVG rendered",m.svg,{error:m.error},true);
   if(m.svg){
    check(rec,"all source point IDs",JSON.stringify(m.labels.filter(g=>g.kind==="point").map(g=>g.key).sort())===JSON.stringify(chart.points.map(p=>p.id).sort()),m.labels.filter(g=>g.kind==="point").map(g=>g.key),chart.points.map(p=>p.id));
    check(rec,"all HTML points and first five aspects/houses",m.points.length===chart.points.length&&m.aspects.length===Math.min(5,chart.aspects.length)&&m.houses.length===Math.min(5,chart.houses?.length||0),[m.points.length,m.aspects.length,m.houses.length],[chart.points.length,Math.min(5,chart.aspects.length),Math.min(5,chart.houses?.length||0)]);
    check(rec,"12 zodiac sectors and source houses",m.sectors===12&&m.houseCount===(chart.houses?.length||0),[m.sectors,m.houseCount],[12,chart.houses?.length||0]);
    check(rec,"passive SVG",m.passiveTargets===0,m.passiveTargets,0);
    check(rec,"no page horizontal overflow",!m.overflow,m.overflow,false);
    check(rec,"native CSS scale retained",Math.abs(m.matrix.a-1)<1e-8&&Math.abs(m.matrix.d-1)<1e-8,m.matrix,"scale=1");
    const badFont=m.labels.flatMap(g=>g.components.filter(c=>c.size<(g.kind==="point"&&!c.text.includes("R")?16:12)).map(c=>({g:g.key,c})));
    check(rec,"glyph em16 / auxiliary and R em12",badFont.length===0,badFont,[]);
    check(rec,"HTML controls bbox >=44",m.enabledTargets.every(t=>t.bounds.width>=44&&t.bounds.height>=44),m.enabledTargets.filter(t=>t.bounds.width<44||t.bounds.height<44),[]);
    check(rec,"circle fully inside initial 1000px viewport",m.frame.top>=0&&m.frame.bottom<=1000+1e-6,m.frame,"0 <= top; bottom <=1000");
    check(rec,"seven type legend",m.legend.length===7,m.legend,7);
    auditGeometry(rec,m,chart);
    if(chart.points.some(p=>p.id==="sun")){
     const sun=page.locator('[data-point-id="sun"]');await sun.scrollIntoViewIfNeeded();await sun.focus();
     await page.evaluate(()=>{window.__testerSun=document.querySelector('[data-point-id="sun"]');window.__testerClicks=[];window.__testerSun.addEventListener("click",e=>window.__testerClicks.push({trusted:e.isTrusted,x:e.clientX,y:e.clientY}));});
     const before=await page.evaluate(()=>({y:scrollY,x:scrollX}));
     await page.keyboard.press("Enter");await page.waitForFunction(()=>document.querySelector('[data-point-id="sun"]').getAttribute("aria-pressed")==="true");
     const focus=await page.evaluate(()=>({same:document.activeElement===window.__testerSun,connected:window.__testerSun.isConnected,x:scrollX,y:scrollY,clicks:window.__testerClicks}));
     rec.planetFocus=focus;check(rec,"planet keyboard retains live focus and scroll",focus.same&&focus.connected&&focus.x===before.x&&focus.y===before.y,focus,{same:true,connected:true,x:before.x,y:before.y});
     check(rec,"planet filter reads every source occurrence",await page.locator("#aspects-table tbody tr:visible").count()===chart.aspects.filter(a=>a.from==="sun"||a.to==="sun").length,await page.locator("#aspects-table tbody tr:visible").count(),chart.aspects.filter(a=>a.from==="sun"||a.to==="sun").length);
     const b=await sun.boundingBox(),x=b.x+b.width/2,y=b.y+b.height/2;const hits=[];
     for(const dx of [-21.5,0,21.5])for(const dy of [-21.5,0,21.5])hits.push(await page.evaluate(({x,y})=>{const n=document.elementFromPoint(x,y);return {x,y,hit:n?.closest('[data-point-id="sun"]')===window.__testerSun};},{x:x+dx,y:y+dy}));
     rec.sunStyle=await sun.evaluate(n=>{const s=getComputedStyle(n),b=n.getBoundingClientRect();return {width:b.width,height:b.height,left:b.left,top:b.top,bottom:b.bottom,right:b.right,borderRadius:s.borderRadius,padding:s.padding,overflow:s.overflow,border:s.border,boxSizing:s.boxSizing}});
     await page.mouse.click(x,y);rec.nativeHit={sampledSquareSide:43,scope:"9 probes; does not certify all points in a 44 CSS px square",probes:hits,events:await page.evaluate(()=>window.__testerClicks)};
     check(rec,"representative native hit probes and trusted click",hits.every(h=>h.hit)&&rec.nativeHit.events.some(e=>e.trusted),rec.nativeHit,"9 sampled points + trusted activation; 44px certificate requires separate check");
     check(rec,"repeat point restores first five",await sun.getAttribute("aria-pressed")==="false"&&await page.locator("#aspects-table tbody tr:visible").count()===Math.min(5,chart.aspects.length),await page.locator("#aspects-table tbody tr:visible").count(),Math.min(5,chart.aspects.length));
    }
   }
   check(rec,"local actions do not build",!h.requests.some(r=>r.path==="build"),h.requests,"GET/bootstrap only");check(rec,"no uncaught browser errors",h.errors.length===0,h.errors,[]);
   if(name==="F3-max"||name==="cosmogram")await page.screenshot({path:path.join(out,"screenshots",rec.id+".png"),fullPage:true});
  }catch(e){rec.error=String(e.stack||e);check(rec,"scenario completed",false,rec.error,true);}
  rec.pass=rec.checks.every(c=>c.pass);report.cases.push(rec);save();console.log(rec.pass?"PASS":"FAIL",rec.id,rec.checks.filter(c=>!c.pass).map(c=>c.name).join("; "));await h?.page.close();
 }
 // Addressed lifecycle scenario uses real mounted application and native events.
 for(const width of [1440,768,360]){
  const rec={id:"lifecycle-"+width,checks:[]};let h;
  try{
   h=await openPage(fixtures.F1.chart,width);const p=h.page;
   await p.locator("#aspects-show-all").click();await p.locator("#houses-show-all").click();
   const all=fixtures.F1.chart.aspects.length;
   await p.locator('[data-point-id="sun"]').scrollIntoViewIfNeeded();await p.locator('[data-point-id="sun"]').click();
   await p.locator("#birth-edit").click();await p.locator("#birth-time").fill("15:45");
   const next=clone(h.current);next.chart.chart_identity+="-B";next.birth.birth_time="14:31";await refresh(h,next);
   check(rec,"automatic new identity preserves point/draft/houses",await p.locator('[data-point-id="sun"]').getAttribute("aria-pressed")==="true"&&await p.locator("#birth-time").inputValue()==="15:45"&&await p.locator("#houses-table tbody tr:visible").count()===12,{sun:await p.locator('[data-point-id="sun"]').getAttribute("aria-pressed"),draft:await p.locator("#birth-time").inputValue(),houses:await p.locator("#houses-table tbody tr:visible").count()},"sun selected; draft15:45;12houses");
   await p.setViewportSize({width:width===360?400:width-40,height:800});
   check(rec,"resize preserves point and draft",await p.locator('[data-point-id="sun"]').getAttribute("aria-pressed")==="true"&&await p.locator("#birth-time").inputValue()==="15:45",await p.locator("#birth-time").inputValue(),"15:45");
   await p.locator('[data-point-id="sun"]').click();await p.locator("#aspects-show-all").click();
   const source=fixtures.F1.chart.aspects;const unique=i=>source.filter(a=>[a.from,a.to].sort().join("|")=== [source[i].from,source[i].to].sort().join("|")&&a.type===source[i].type).length===1;
   const i=source.findIndex((a,i)=>unique(i)&&a.category!=="background");const row=p.locator("#aspects-table tbody tr").nth(i).locator("button");
   await row.scrollIntoViewIfNeeded();await row.focus();await p.keyboard.press("Enter");
   await p.waitForFunction(()=>document.querySelector("#chart-result").dataset.aspectFocus==="true");await p.waitForFunction(()=>document.querySelector("#chart-wheel svg"));
   const aspect=source[i],selected=await measure(p);rec.aspect=selected;
   const endpoints=fixtures.F1.chart.points.filter(x=>[aspect.from,aspect.to].includes(x.id));
   const houseCount=new Set(endpoints.map(x=>x.house).filter(x=>x!==null)).size;
   check(rec,"aspect view focuses live HTML wheel with endpoint facts",selected.active==="chart-wheel"&&selected.points.length===endpoints.length&&selected.houses.length===houseCount&&selected.aspects.length===1, {active:selected.active,points:selected.points.length,houses:selected.houses.length,aspects:selected.aspects.length},{active:"chart-wheel",points:endpoints.length,houses:houseCount,aspects:1});
   await p.keyboard.press("Escape");
   check(rec,"Escape restores all source rows and live origin focus",await p.locator("#aspects-table tbody tr:visible").count()===all&&await row.evaluate(n=>n===document.activeElement&&n.isConnected),{rows:await p.locator("#aspects-table tbody tr:visible").count(),focus:await row.evaluate(n=>n===document.activeElement&&n.isConnected)}, {rows:all,focus:true});
   const dup=clone(h.current);dup.chart.chart_identity+="-ambiguous";dup.chart.aspects.push(clone(dup.chart.aspects[i]));await refresh(h,dup);
   const disabled=await p.locator("#aspects-table tbody button:disabled").count();
   check(rec,"S1 counts full-source duplicates with unaffected enabled control",disabled>=2&&await p.locator("#aspects-table tbody tr:visible").count()===all+1&&await p.locator("#aspects-table tbody button:enabled").count()>0,{disabled,rows:await p.locator("#aspects-table tbody tr:visible").count(),warning:await p.locator("#aspect-warnings").textContent()},"all+1 rows;2 disabled;positive enabled unaffected");
   await p.evaluate(()=>window.__testerLeafFault=true);const faulty=clone(h.current);faulty.chart.chart_identity+="-faultB";await refresh(h,faulty);
   await p.waitForFunction(()=>!document.querySelector("#wheel-error").hidden);
   check(rec,"leaf fault keeps accepted HTML B",await p.locator("#chart-wheel svg").count()===0&&await p.locator("#points-table tbody tr:visible").count()===16&&await p.locator("#chart-result").getAttribute("data-chart-identity")===faulty.chart.chart_identity,{svg:await p.locator("#chart-wheel svg").count(),points:await p.locator("#points-table tbody tr:visible").count(),identity:await p.locator("#chart-result").getAttribute("data-chart-identity")},"0SVG;16points;B identity");
   await p.evaluate(()=>window.__testerLeafFault=false);const ok=clone(h.current);ok.chart.chart_identity+="-restored";await refresh(h,ok);await p.waitForFunction(()=>document.querySelector("#chart-wheel svg"));
   check(rec,"positive leaf recovery restores real SVG",await p.locator("#chart-wheel svg").count()===1,await p.locator("#chart-wheel svg").count(),1);
   const empty=clone(views.empty);await refresh(h,empty);await p.waitForFunction(()=>document.querySelector("#chart-result").hidden);
   check(rec,"confirmed empty removes old numerical view",await p.locator("#chart-wheel svg").count()===0&&await p.locator("#birth-editor").isVisible(),{svg:await p.locator("#chart-wheel svg").count(),editor:await p.locator("#birth-editor").isVisible()},"no SVG;editor visible");
   check(rec,"no build from local/current/fault/resize actions",!h.requests.some(r=>r.path==="build"),h.requests,"no POST");rec.requests=h.requests;rec.errors=h.errors;
  }catch(e){rec.error=String(e.stack||e);check(rec,"lifecycle completed",false,rec.error,true);}
  rec.pass=rec.checks.every(c=>c.pass);report.cases.push(rec);save();console.log(rec.pass?"PASS":"FAIL",rec.id,rec.checks.filter(c=>!c.pass).map(c=>c.name).join("; "));await h?.page.close();
 }
 report.finished_utc=new Date().toISOString();report.summary={cases:report.cases.length,failed:report.cases.filter(r=>!r.pass).length,checks:report.cases.reduce((n,r)=>n+r.checks.length,0),failed_checks:report.cases.flatMap(r=>r.checks.filter(c=>!c.pass).map(c=>({id:r.id,...c})))};
 save();console.log(JSON.stringify(report.summary));process.exitCode=report.summary.failed?1:0;
}
main().catch(e=>{report.fatal=String(e.stack||e);save();console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r());});
