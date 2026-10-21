// Tester independent H44 certificate / native outcome / first-five regression.
// Real production modules; only controlled HTTP and optional old CSS from published Git.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto"),cp=require("node:child_process");
const {chromium}=require("C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const ROOT=path.resolve(__dirname,"../../../../../../.."),UI=path.join(ROOT,"src/exact_orb/http_api/ui"),PIN="99741958b4bbee8884505920f4a02f2f19dea3e3";
const oldCss=process.argv.includes("--old-css"),name=process.argv[2]||"native01";
if(!/^[a-z][a-z0-9_-]*$/.test(name))throw Error("Invalid output name");
if(cp.execFileSync("git",["rev-parse","HEAD"],{cwd:ROOT,encoding:"utf8"}).trim()!==PIN)throw Error("Wrong checkout");
const OUT=path.join(__dirname,name);if(fs.existsSync(OUT))throw Error("Refuse overwrite");fs.mkdirSync(OUT);
const fixtures=JSON.parse(fs.readFileSync(path.join(ROOT,"docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/data.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(ROOT,"tests/http_api/golden/session_view.json"),"utf8")),chart=fixtures.F1.chart,clone=structuredClone;
const cssBefore=oldCss?cp.execFileSync("git",["show","3b95934c884caa9f40ea70e935991457058b87b9:src/exact_orb/http_api/ui/styles.css"],{cwd:ROOT}):null;
const hash=b=>crypto.createHash("sha256").update(b).digest("hex");
const result={author:"Codex / Tester",retested_sha:PIN,started_utc:new Date().toISOString(),old_css_sensitivity:oldCss,
 css_source:oldCss?"Git 3b95934 CSS + current actual modules (hybrid sensitivity control, not full old checkout)":"Actual checkout",
 harness_revision:"v2: exclude page paint provably below direct-body fixed calibration root; original v1/RED preserved",source_sha256_lf:{},cases:[],scope:"Independent rect/rounded-rect Q44 containment; ancestor clips; rectangular paint-interceptor partition plus native grid. No placement helper/Developer verifier imported."};
for(const f of fs.readdirSync(UI))if(/\.(mjs|css|html)$/.test(f))result.source_sha256_lf[f]=hash(fs.readFileSync(path.join(UI,f),"utf8").replaceAll("\r\n","\n"));
result.served_css_sha256_lf=hash((cssBefore||fs.readFileSync(path.join(UI,"styles.css"))).toString("utf8").replaceAll("\r\n","\n"));
let server,browser,base;
const save=()=>fs.writeFileSync(path.join(OUT,"actual.json"),JSON.stringify(result,null,2)+"\n");
const check=(r,id,pass,actual,expected)=>r.checks.push({id,pass:!!pass,actual,expected});
async function certificate(locator){
 await locator.scrollIntoViewIfNeeded();
 return locator.evaluate(n=>{
  const b=n.getBoundingClientRect(),s=getComputedStyle(n),q={left:b.left+(b.width-44)/2,top:b.top+(b.height-44)/2,size:44};
  q.right=q.left+44;q.bottom=q.top+44;
  const containsOwner=hit=>hit===n||n.contains(hit);
  let fixedRoot=null;
  for(let a=n;a&&a!==document.body;a=a.parentElement){const c=getComputedStyle(a);if(a.parentElement===document.body&&c.position==="fixed"&&/^\\d+$/.test(c.zIndex))fixedRoot={node:a,z:Number(c.zIndex)};}
  const radiusKeys=["borderTopLeftRadius","borderTopRightRadius","borderBottomRightRadius","borderBottomLeftRadius"];
  const radii=radiusKeys.map(k=>s[k]),supportedRadii=radii.every(v=>/^\d+(?:\.\d+)?px$/.test(v))&&new Set(radii).size===1;
  const radius=Math.min(parseFloat(radii[0]),b.width/2,b.height/2);
  function rounded(x,y){
   if(x<b.left||x>b.right||y<b.top||y>b.bottom)return false;
   const cx=x<b.left+radius?b.left+radius:x>b.right-radius?b.right-radius:null;
   const cy=y<b.top+radius?b.top+radius:y>b.bottom-radius?b.bottom-radius:null;
   return cx===null||cy===null||(x-cx)**2+(y-cy)**2<=radius**2;
  }
  const corners=[[q.left,q.top],[q.right,q.top],[q.right,q.bottom],[q.left,q.bottom]];
  const shape=supportedRadii&&b.width>=44&&b.height>=44&&corners.every(([x,y])=>rounded(x,y));
  const unsupported=[],clips=[],obstructions=[],xs=new Set([q.left,q.right]),ys=new Set([q.top,q.bottom]);
  if(s.clipPath!=="none"||s.maskImage!=="none")unsupported.push("target clip/mask");
  for(let a=n;a;a=a.parentElement){
   const cs=getComputedStyle(a),v=a.getBoundingClientRect();
   if(cs.clipPath!=="none"||cs.maskImage!=="none")unsupported.push(a.tagName+":clip/mask");
   if(cs.transform!=="none"||!["normal","1"].includes(cs.zoom))unsupported.push(a.tagName+":transform/zoom");
   const clip={tag:a.tagName,ox:cs.overflowX,oy:cs.overflowY,left:v.left+a.clientLeft,top:v.top+a.clientTop};
   clip.right=clip.left+a.clientWidth;clip.bottom=clip.top+a.clientHeight;
   if(/hidden|clip|scroll|auto/.test(cs.overflowX)&&!(q.left>=clip.left&&q.right<=clip.right))clips.push(clip);
   if(/hidden|clip|scroll|auto/.test(cs.overflowY)&&!(q.top>=clip.top&&q.bottom<=clip.bottom))clips.push(clip);
  }
  if(q.left<0||q.right>innerWidth||q.top<0||q.bottom>innerHeight)clips.push({tag:"viewport"});
  for(const other of document.querySelectorAll("*")){
   if(other===n||other.contains(n)||n.contains(other))continue;
   const cs=getComputedStyle(other);if(cs.display==="none"||cs.visibility!=="visible"||cs.pointerEvents==="none")continue;
   // A direct-body fixed calibration root is above ordinary page stacking contexts.
   if(fixedRoot&&!fixedRoot.node.contains(other)){
    let possibleAbove=false;for(let a=other;a&&a!==document.body;a=a.parentElement){const c=getComputedStyle(a);if(c.position!=="static"&&/^\\d+$/.test(c.zIndex)&&Number(c.zIndex)>=fixedRoot.z)possibleAbove=true;}
    if(!possibleAbove)continue;
   }
   const r=other.getBoundingClientRect(),l=Math.max(q.left,r.left),t=Math.max(q.top,r.top),right=Math.min(q.right,r.right),bottom=Math.min(q.bottom,r.bottom);
   if(!(l<right&&t<bottom))continue;
   xs.add(l);xs.add(right);ys.add(t);ys.add(bottom);
   obstructions.push({tag:other.tagName,id:other.id,left:l,top:t,right,bottom,radius:cs.borderRadius,clip:cs.clipPath});
  }
  const xx=[...xs].sort((a,b)=>a-b),yy=[...ys].sort((a,b)=>a-b),partitionFailures=[];
  for(let i=0;i<xx.length-1;i++)for(let j=0;j<yy.length-1;j++){
   const x=(xx[i]+xx[i+1])/2,y=(yy[j]+yy[j+1])/2,hit=document.elementFromPoint(x,y);
   if(!containsOwner(hit))partitionFailures.push({x,y,tag:hit?.tagName,id:hit?.id});
  }
  // Real page / controls use axis-aligned rectangles; arbitrary shapes remain unsupported.
  if(obstructions.some(o=>o.radius!=="0px"||o.clip!=="none"))unsupported.push("nonrectangular potential interceptor");
  const offsets=[.25,1,2,5,11,22,33,41,43,43.5,43.75],failures=[];let hits=0;
  for(const dx of offsets)for(const dy of offsets){const x=q.left+dx,y=q.top+dy,hit=document.elementFromPoint(x,y);
   if(containsOwner(hit))hits++;else if(failures.length<24)failures.push({x,y,tag:hit?.tagName,id:hit?.id});
  }
  const cert=shape&&!clips.length&&!unsupported.length&&!partitionFailures.length;
  return {text:n.textContent,q,box:{left:b.left,top:b.top,width:b.width,height:b.height},radii,shape,
   clips,unsupported,potentialInterceptors:obstructions,partitionCells:(xx.length-1)*(yy.length-1),partitionFailures,
   offsets,probes:offsets.length**2,hits,failures,certificate:cert,native:failures.length===0,pass:cert&&failures.length===0};
 });
}
async function open(width){
 const page=await browser.newPage({viewport:{width,height:900}}),requests=[],errors=[];
 let view=clone(views.known_ready);view.chart=clone(chart);
 let post=route=>route.fulfill({status:500,json:{code:"TESTER_UNEXPECTED_BUILD"}});
 page.on("pageerror",e=>errors.push(String(e)));
 await page.route("**/session/bootstrap",route=>{requests.push({actor:"HTTP",path:"bootstrap",method:route.request().method()});return route.fulfill({json:{status:"ready",state_version:1}})});
 await page.route("**/charts/current",route=>{requests.push({actor:"HTTP",path:"current",method:route.request().method(),identity:view.chart?.chart_identity,stale:view.chart_stale});return route.fulfill({json:view})});
 await page.route("**/charts/natal",route=>{requests.push({actor:"HTTP",path:"build",method:route.request().method(),body:route.request().postDataJSON()});return post(route)});
 await page.goto(base);await page.waitForFunction(()=>document.querySelector("#chart-wheel svg")||document.querySelector("#wheel-error:not([hidden])"));
 return {page,requests,errors,get view(){return view},set view(v){view=v},set post(fn){post=fn}};
}
const ids=async p=>p.locator("#points-table tbody tr:visible button").evaluateAll(ns=>ns.map(n=>n.dataset.pointId));
const visibleCount=(p,id)=>p.locator("#"+id+" tbody tr:visible").count();
async function expand(p,id){
 const l=p.locator("#"+id);if(await l.isVisible()&&await l.getAttribute("aria-expanded")==="false")await l.click();
}
async function online(h){
 const response=h.page.waitForResponse(r=>r.url().endsWith("/charts/current"));
 await h.page.evaluate(()=>window.dispatchEvent(new Event("online")));await response;
 await h.page.waitForFunction(()=>document.querySelector("#birth-form").getAttribute("aria-busy")==="false");
}
const address=a=>JSON.stringify([[a.from,a.to].sort(),a.type]);
const aspectIndex=chart.aspects.findIndex((a,i)=>a.category!=="background"&&chart.points.some(p=>p.id===a.from)&&chart.points.some(p=>p.id===a.to)
 &&chart.points.some((p,j)=>j>=5&&[a.from,a.to].includes(p.id))&&chart.aspects.filter(b=>address(a)===address(b)).length===1);
if(aspectIndex<0)throw Error("No required published aspect fixture");
async function aspectCheck(h,r,expanded,label){
 const p=h.page;await expand(p,"aspects-show-all");
 const button=p.locator("#aspects-table tbody tr").nth(aspectIndex).locator("button");
 await button.scrollIntoViewIfNeeded();await button.evaluate(n=>window.__originAspect=n);
 const m=await certificate(button);await p.mouse.click(m.q.left+1,m.q.top+1);
 if(!await p.locator("#aspect-close").isVisible())await button.click(); // reached-path positive if old CSS corner fails
 await p.waitForFunction(()=>document.querySelector("#chart-result").dataset.aspectFocus==="true");
 const a=chart.aspects[aspectIndex],points=chart.points.filter(pt=>[a.from,a.to].includes(pt.id)),houses=new Set(points.map(pt=>pt.house).filter(v=>v!==null));
 check(r,label+": source endpoint rows incl beyond-five",JSON.stringify(await ids(p))===JSON.stringify(points.map(pt=>pt.id)),await ids(p),points.map(pt=>pt.id));
 check(r,label+": selected source houses",await visibleCount(p,"houses-table")===houses.size,await visibleCount(p,"houses-table"),houses.size);
 check(r,label+": passive region focus",await p.locator("#chart-wheel").evaluate(n=>n===document.activeElement),await p.evaluate(()=>document.activeElement?.id),"chart-wheel");
 check(r,label+": one aspect row",await visibleCount(p,"aspects-table")===1,await visibleCount(p,"aspects-table"),1);
 const active=p.locator(".fact-select:visible:enabled");r.selectedControls??=[];
 for(const item of await active.all()){const c=await certificate(item);r.selectedControls.push(c);check(r,label+": selected H44 "+c.text,c.pass,{certificate:c.certificate,hits:c.hits,probes:c.probes},true)}
 await p.keyboard.press("Escape");
 check(r,label+": prior points disclosure restored",(await ids(p)).length===(expanded?chart.points.length:5),await ids(p),expanded?chart.points.length:5);
 check(r,label+": original focus live",await p.evaluate(()=>document.activeElement===window.__originAspect&&window.__originAspect.isConnected),await p.evaluate(()=>({active:document.activeElement?.textContent,connected:window.__originAspect.isConnected})),true);
}
async function calibrate(p,r){
 await p.evaluate(()=>{
  for(const [id,w,left] of [["positive",44,4],["negative43",43,65],["overlay",44,125],["clip43",44,185],["thinOverlay",44,245]]){
   const host=document.createElement("div");host.dataset.retestCalibration=id;
   host.style.cssText="position:fixed;z-index:999999;left:"+left+"px;top:4px;width:"+(id==="clip43"?43:44)+"px;height:44px;overflow:hidden";
   const b=document.createElement("button");b.id="retest-"+id;b.textContent=id;
   b.style.cssText="all:initial;display:block;box-sizing:border-box;width:"+w+"px;height:44px;border-radius:0;background:white;color:black;pointer-events:auto";
   host.append(b);
   if(id==="overlay"||id==="thinOverlay"){const mask=document.createElement("div");mask.id="mask-"+id;
    mask.style.cssText="position:absolute;left:"+(id==="overlay"?30:8)+"px;top:"+(id==="overlay"?0:8)+"px;width:"+(id==="overlay"?14:1)+"px;height:"+(id==="overlay"?44:1)+"px;background:red;pointer-events:auto";host.append(mask)}
   document.body.append(host);
  }
 });
 r.calibration={};
 for(const id of ["positive","negative43","overlay","clip43","thinOverlay"]){
  const m=await certificate(p.locator("#retest-"+id));r.calibration[id]=m;
  check(r,"independent calibration "+id,m.pass===(id==="positive"),{pass:m.pass,hits:m.hits,probes:m.probes,shape:m.shape,clips:m.clips,partition:m.partitionFailures},id==="positive");
 }
 check(r,"thin overlay defeats grid-only oracle",r.calibration.thinOverlay.native&&!r.calibration.thinOverlay.certificate,{native:r.calibration.thinOverlay.native,certificate:r.calibration.thinOverlay.certificate},true);
 await p.evaluate(()=>document.querySelector("#mask-thinOverlay").remove());
 const restored=await certificate(p.locator("#retest-thinOverlay"));r.calibration.restored=restored;
 check(r,"paired overlay removal restores certificate",restored.pass,restored.pass,true);
 await p.evaluate(()=>document.querySelectorAll("[data-retest-calibration]").forEach(n=>n.remove()));
}
async function acceptedReset(h,r,width){
 const p=h.page;await expand(p,"points-show-all");await expand(p,"houses-show-all");
 const sun=p.locator('[data-point-id="sun"]');if(await sun.getAttribute("aria-pressed")!=="true")await sun.click();
 if(await p.locator("#birth-editor").isHidden())await p.locator("#birth-edit").click();
 await p.locator("#birth-time").fill("15:45");
 const b=clone(h.view);b.chart.chart_identity+="-automatic-B";b.birth.birth_time="14:31";h.view=b;await online(h);
 check(r,"automatic current preserves point/all/draft",await sun.getAttribute("aria-pressed")==="true"&&(await ids(p)).length===16&&await p.locator("#birth-time").inputValue()==="15:45",{selected:await sun.getAttribute("aria-pressed"),rows:(await ids(p)).length,draft:await p.locator("#birth-time").inputValue()},true);
 await p.locator("#birth-date").fill("1990-01-01");await p.locator("#terms-acknowledged").check();
 let release,observed;const gate=new Promise(resolve=>release=resolve),posted=new Promise(resolve=>observed=resolve);
 const next=clone(h.view);next.chart.chart_identity+="-changed-goal";next.birth.birth_date="1990-01-01";next.birth.birth_time="15:45";next.chart_stale=width===360;
 const mode=width===1440?"committed":"already_applied",lateDraft=width===1440;
 h.post=async route=>{observed();await gate;h.view=next;return route.fulfill({json:mode==="committed"?{status:"chart_ready",state_version:2,chart:next.chart}:{status:"already_applied",state_version:2}})};
 await p.locator('#birth-form button[type="submit"]').click();await posted;
 if(lateDraft)await p.locator("#birth-time").fill("16:15");
 release();await p.waitForFunction(()=>document.querySelector("#birth-form").getAttribute("aria-busy")==="false");
 if(width===360){
  check(r,"stale match preserves unconsumed goal disclosure",(await ids(p)).length===16&&await sun.getAttribute("aria-pressed")==="true",{points:(await ids(p)).length,selected:await sun.getAttribute("aria-pressed")},true);
  next.chart_stale=false;h.view=next;await online(h);
 }
 const after={points:(await ids(p)).length,houses:await visibleCount(p,"houses-table"),sun:await sun.getAttribute("aria-pressed"),
  editorHidden:await p.locator("#birth-editor").evaluate(n=>n.hidden),draft:await p.locator("#birth-time").inputValue(),summary:await p.locator("#chart-birth-summary").textContent()};
 r.acceptance={mode,lateDraft,after};
 check(r,"accepted changed goal resets first-five once",after.points===5&&after.houses===5&&after.sun==="false",after,{points:5,houses:5,sun:"false"});
 check(r,"collapse only when draft matches accepted goal",after.editorHidden===!lateDraft&&after.draft===(lateDraft?"16:15":"15:45"),after,!lateDraft);
 check(r,"summary belongs to submitted/fresh GET B",after.summary.includes("1990-01-01")&&after.summary.includes("15:45")&&!after.summary.includes("16:15"),after.summary,"1990-01-01 /15:45");
 if(after.editorHidden)await p.locator("#birth-edit").click();await expand(p,"points-show-all");await expand(p,"houses-show-all");await sun.click();await online(h);
 check(r,"later current preserves reopened editor/all/selection",(await ids(p)).length===16&&await visibleCount(p,"houses-table")===12&&await sun.getAttribute("aria-pressed")==="true"&&await p.locator("#birth-editor").isVisible(),
  {points:(await ids(p)).length,houses:await visibleCount(p,"houses-table"),sun:await sun.getAttribute("aria-pressed"),editor:await p.locator("#birth-editor").isVisible()},true);
 check(r,"one explicit build, no automatic POST",h.requests.filter(v=>v.path==="build").length===1,h.requests,1);
}
async function main(){
 server=http.createServer((req,res)=>{
  let u=new URL(req.url,"http://localhost").pathname;if(u==="/")u="/ui/index.html";
  if(!/^\/ui\/[a-z_]+\.(mjs|css|html)$/.test(u)){res.writeHead(404).end();return}
  const f=path.join(UI,path.basename(u));res.setHeader("Content-Type",f.endsWith(".mjs")?"text/javascript":f.endsWith(".css")?"text/css":"text/html");
  res.end(oldCss&&u==="/ui/styles.css"?cssBefore:fs.readFileSync(f));
 });await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));base="http://127.0.0.1:"+server.address().port;
 const vendors=oldCss?[["Chrome","C:/Program Files/Google/Chrome/Application/chrome.exe"]]:
  [["Chrome","C:/Program Files/Google/Chrome/Application/chrome.exe"],["Yandex","C:/Users/KateUser/AppData/Local/Yandex/YandexBrowser/Application/browser.exe"]];
 for(const [vendor,executablePath] of vendors){
  browser=await chromium.launch({headless:true,executablePath});
  for(const width of oldCss?[1440]:[1440,768,360]){
   const r={id:vendor+"-"+width,vendor,width,version:browser.version(),checks:[],controls:[]};let h;
   try{
    h=await open(width);const p=h.page;r.requests=h.requests;r.errors=h.errors;
    check(r,"initial first-five canonical points",JSON.stringify(await ids(p))===JSON.stringify(chart.points.slice(0,5).map(p=>p.id)),await ids(p),chart.points.slice(0,5).map(p=>p.id));
    check(r,"full SVG point set is unchanged",await p.locator('#chart-wheel [data-kind="point"]').count()===16,await p.locator('#chart-wheel [data-kind="point"]').count(),16);
    check(r,"initial houses/aspects five",await visibleCount(p,"houses-table")===5&&await visibleCount(p,"aspects-table")===5,[await visibleCount(p,"houses-table"),await visibleCount(p,"aspects-table")],[5,5]);
    if(!oldCss)await aspectCheck(h,r,false,"collapsed-aspect");
    await expand(p,"points-show-all");
    check(r,"points reveal retains all source IDs/order",JSON.stringify(await ids(p))===JSON.stringify(chart.points.map(p=>p.id)),await ids(p),chart.points.map(p=>p.id));
    check(r,"points disclosure independent of houses",await visibleCount(p,"houses-table")===5,await visibleCount(p,"houses-table"),5);
    await expand(p,"aspects-show-all");await expand(p,"houses-show-all");
    const controls=p.locator(".fact-select:visible:enabled");
    check(r,"all source point/aspect controls reached",await controls.count()===chart.points.length+chart.aspects.length,await controls.count(),chart.points.length+chart.aspects.length);
    for(const item of await controls.all()){
     const c=await certificate(item);r.controls.push(c);
     check(r,"H44 "+c.text,c.pass,{certificate:c.certificate,hits:c.hits,probes:c.probes,unsupported:c.unsupported,clips:c.clips,failures:c.failures},true);
    }
    const sun=p.locator('[data-point-id="sun"]');await sun.scrollIntoViewIfNeeded();
    await sun.evaluate(n=>{window.__sunRef=n;window.__retestClicks=[];n.addEventListener("click",e=>window.__retestClicks.push({trusted:e.isTrusted,x:e.clientX,y:e.clientY}))});
    for(const [dx,dy] of [[22,22],[.5,.5],[43.5,.5],[.5,43.5],[43.5,43.5]]){
     const c=await certificate(sun),before=await sun.getAttribute("aria-pressed");await p.mouse.click(c.q.left+dx,c.q.top+dy);
     check(r,"trusted coordinate toggle "+dx+","+dy,await sun.getAttribute("aria-pressed")!==before,{before,after:await sun.getAttribute("aria-pressed"),x:c.q.left+dx,y:c.q.top+dy},true);
    }
    r.pointerEvents=await p.evaluate(()=>window.__retestClicks);
    check(r,"five actual trusted pointer events",r.pointerEvents.length===5&&r.pointerEvents.every(e=>e.trusted),r.pointerEvents,5);
    await sun.focus();const pressed=await sun.getAttribute("aria-pressed"),scroll=await p.evaluate(()=>[scrollX,scrollY]);
    await p.keyboard.press("Enter");check(r,"keyboard Enter toggles",await sun.getAttribute("aria-pressed")!==pressed,await sun.getAttribute("aria-pressed"),pressed!=="true");
    await p.keyboard.press("Space");check(r,"keyboard Space toggles back",await sun.getAttribute("aria-pressed")===pressed,await sun.getAttribute("aria-pressed"),pressed);
    check(r,"planet live focus and scroll retained",await p.evaluate(([x,y])=>document.activeElement===window.__sunRef&&window.__sunRef.isConnected&&scrollX===x&&scrollY===y,scroll),await p.evaluate(()=>({active:document.activeElement?.dataset.pointId,scroll:[scrollX,scrollY]})),true);
    if(await sun.getAttribute("aria-pressed")==="true")await p.keyboard.press("Enter");
    if(!oldCss)await aspectCheck(h,r,true,"expanded-aspect");
    await calibrate(p,r);
    await sun.scrollIntoViewIfNeeded();r.compactness=await sun.evaluate(n=>({row:n.closest("tr").getBoundingClientRect().height,overflow:document.documentElement.scrollWidth>innerWidth}));
    check(r,"no horizontal page overflow",!r.compactness.overflow,r.compactness,false);
    if(width>700)check(r,"compact desktop short row <=56",r.compactness.row<=56,r.compactness.row,"<=56");
    check(r,"no build from selection/disclosure/calibration",h.requests.filter(v=>v.path==="build").length===0,h.requests,0);
    if(!oldCss)await acceptedReset(h,r,width);
    check(r,"no uncaught page errors",h.errors.length===0,h.errors,[]);
    await p.screenshot({path:path.join(OUT,r.id+".png")});
   }catch(e){r.error=String(e.stack||e);check(r,"scenario completed",false,r.error,true)}
   r.pass=r.checks.every(c=>c.pass);result.cases.push(r);save();
   console.log(r.pass?"PASS":"FAIL",r.id,"checks="+r.checks.length,r.checks.filter(c=>!c.pass).map(c=>c.id).join("; "));await h?.page.close();
  }
  await browser.close();browser=null;
 }
 result.finished_utc=new Date().toISOString();
 result.summary={cases:result.cases.length,passed:result.cases.filter(r=>r.pass).length,checks:result.cases.reduce((n,r)=>n+r.checks.length,0),
  failed:result.cases.flatMap(r=>r.checks.filter(c=>!c.pass).map(c=>({id:r.id,...c}))),normalControls:result.cases.reduce((n,r)=>n+r.controls.length,0),selectedControls:result.cases.reduce((n,r)=>n+(r.selectedControls?.length||0),0)};
 save();console.log(JSON.stringify({cases:result.summary.cases,passed:result.summary.passed,checks:result.summary.checks,failures:result.summary.failed.length,normalControls:result.summary.normalControls,selectedControls:result.summary.selectedControls}));
 process.exitCode=result.summary.failed.length?1:0;
}
main().catch(e=>{result.fatal=String(e.stack||e);save();console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(resolve=>server?server.close(resolve):resolve());});
