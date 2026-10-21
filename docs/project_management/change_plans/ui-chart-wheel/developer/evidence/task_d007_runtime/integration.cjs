// Actual main/session/form/controller/SVG. Only HTTP and the leaf fault are controlled.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require(process.env.WHEEL_PLAYWRIGHT||"C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../../../../../.."),ui=path.join(root,"src/exact_orb/http_api/ui");
const chart=JSON.parse(fs.readFileSync(path.join(root,"tests/ui/fixtures/natal_1985_chart_dto.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(root,"tests/http_api/golden/session_view.json"),"utf8"));
const out=path.join(__dirname,process.argv[2]||"integration01");if(fs.existsSync(out))throw Error("Refuse overwrite");fs.mkdirSync(out);
const output={subject:"TASK-D-007 mounted application integration",started:new Date().toISOString(),cases:[],sources:{}};
for(const name of fs.readdirSync(ui))if(/\.(mjs|css|html)$/.test(name))output.sources[name]=crypto.createHash("sha256").update(fs.readFileSync(path.join(ui,name),"utf8").replaceAll("\r\n","\n")).digest("hex");
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve}};
const shim=[
'import {createWheelRenderer as actual} from "/actual/wheel_svg.mjs";',
'window.capturedLeaves=new Map();window.drawingTimings=[];',
'export function createWheelRenderer(surface){const real=actual(surface);return{',
'update(snapshot,publish,currentSurface){',
'if(window.rejectCurrentLeaf){window.rejectCurrentLeaf=false;return Promise.reject(Error("controlled-leaf-fault"))}',
'const start=performance.now();let copyMs=0;return Promise.resolve(real.update(snapshot,root=>{window.capturedLeaves.set(snapshot.chart.chart_identity,{root,publish,surface:currentSurface});const t=performance.now(),ok=publish(root);copyMs+=performance.now()-t;return ok},currentSurface)).finally(()=>window.drawingTimings.push({identity:snapshot.chart.chart_identity,selected:snapshot.selection,totalMs:performance.now()-start,copyMs}));',
'},dispose(){real.dispose()}}}'
].join("\n");
let server,browser;
async function main(){
 server=http.createServer((req,res)=>{
  const name=req.url==="/"?"/ui/index.html":new URL(req.url,"http://localhost").pathname;
  if(!/^\/(?:ui|actual)\/[a-z_]+\.(?:html|css|mjs)$/.test(name)){res.writeHead(404).end();return}
  const file=path.join(ui,path.basename(name));res.setHeader("Content-Type",file.endsWith(".mjs")?"text/javascript":file.endsWith(".css")?"text/css":"text/html");res.end(fs.readFileSync(file));
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));const base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:process.env.WHEEL_BROWSER||"C:/Program Files/Google/Chrome/Application/chrome.exe"});
 output.browser=browser.version();
 for(const width of [1440,768,360]){
  const page=await browser.newPage({viewport:{width,height:1000}}),record={width,checks:[],requests:[],errors:[]};
  const check=(id,actual,expected)=>{record.checks.push({id,actual,expected,pass:JSON.stringify(actual)===JSON.stringify(expected)});assert.deepEqual(actual,expected,id)};
  let current={...structuredClone(views.known_ready),chart:structuredClone(chart)},permit=deferred(),entered=deferred(),posted,buildMode="commit";
  page.on("pageerror",e=>record.errors.push(String(e)));
  await page.route("**/ui/wheel_svg.mjs",r=>r.fulfill({contentType:"text/javascript",body:shim}));
  await page.route("**/session/bootstrap",r=>{record.requests.push({method:"bootstrap"});return r.fulfill({json:{status:"ready",state_version:1}})});
  await page.route("**/charts/current",r=>{record.requests.push({method:"current",identity:current.chart?.chart_identity});return r.fulfill({json:current,headers:{"X-Request-ID":"current-"+record.requests.length}})});
  await page.route("**/charts/natal",async r=>{
   posted=r.request().postDataJSON();record.requests.push({method:"build",body:posted});entered.resolve();await permit.promise;
   if(buildMode==="already_applied")return r.fulfill({json:{status:"already_applied",state_version:2}});
   return r.fulfill({json:{status:"chart_ready",state_version:2,chart:{...structuredClone(chart),chart_identity:"own-B"}},headers:{"X-Request-ID":"build-B"}});
  });
  try{
   await page.goto(base);await page.waitForSelector("#chart-wheel svg");
   check("initial-editor-collapsed",await page.locator("#birth-editor").isHidden(),true);
   check("manual-gate-unchecked",await page.locator("#terms-acknowledged").isChecked(),false);
   // Actual coordinate hit testing, including a deliberately occluded negative control.
   const pointer=page.locator('[data-point-id="sun"]');await pointer.scrollIntoViewIfNeeded();
   const hit=await pointer.evaluate(n=>{
    const b=n.getBoundingClientRect(),square={left:Math.floor((b.left+b.right)/2-22),top:Math.floor(b.top),size:44},x=square.left+22,y=square.top+22,coords=[];
    // Test a 44 CSS px square by actual hit coordinates; bbox-centred probes can
    // straddle Chrome's fractional raster boundary. No target size is relaxed.
    for(const dx of [-21.99,0,21.99])for(const dy of [-21.99,0,21.99])coords.push({x:x+dx,y:y+dy,hit:document.elementFromPoint(x+dx,y+dy)?.closest("button")===n,element:document.elementFromPoint(x+dx,y+dy)?.outerHTML.slice(0,180)});
    const cover=document.createElement("div");Object.assign(cover.style,{position:"fixed",left:(x-22)+"px",top:(y-22)+"px",width:"44px",height:"44px",zIndex:"9999"});document.body.append(cover);
    const occluded=document.elementFromPoint(x,y)?.closest("button")!==n;cover.remove();
    n.style.clipPath="inset(50%)";const clipped=document.elementFromPoint(x,y)?.closest("button")!==n;n.style.removeProperty("clip-path");
    const scan=[];for(let dy=-23;dy<=23;dy+=.25)scan.push([dy,document.elementFromPoint(x,y+dy)?.closest("button")===n]);
    return{width:b.width,height:b.height,coords,occluded,clipped,square,x,y,scan,rect:b.toJSON(),parent:n.parentNode.getBoundingClientRect().toJSON()};
   });record.pointerHit=hit;check("pointer-44-native-hit",hit.width>=44&&hit.height>=44&&hit.coords.every(p=>p.hit)&&hit.occluded&&hit.clipped,true);
   const beforeInput=record.requests.length;
   await page.mouse.click(hit.x,hit.y);await page.waitForSelector('#chart-wheel [data-selected="sun"]');
   check("coordinate-activation",await pointer.getAttribute("aria-pressed"),"true");
   await page.mouse.click(hit.x,hit.y);await page.waitForFunction(()=>!document.querySelector('#chart-wheel [data-selected="sun"]'));
   check("coordinate-no-HTTP",record.requests.length,beforeInput);
   await page.locator("#aspects-show-all").click();await page.locator("#houses-show-all").click();
   const backgroundIndex=chart.aspects.findIndex(a=>a.category==="background");
   if(backgroundIndex<0)throw Error("Missing positive background fixture");
   const background=page.locator("#aspects-table tbody tr").nth(backgroundIndex).locator("button");
   const positions=()=>page.locator('#chart-wheel [data-label]').evaluateAll(nodes=>nodes.filter(n=>n.getAttribute("data-kind")!=="marker").map(n=>[n.getAttribute("data-label"),n.getAttribute("transform")]));
   const positionsBefore=await positions();await background.focus();await page.keyboard.press("Enter");
   await page.waitForFunction(()=>document.querySelector("#chart-wheel svg")&&!document.querySelector("#chart-wheel [data-aspect]"));
   check("background-no-line-or-conjunction",await page.locator('#chart-wheel [data-aspect],#chart-wheel [data-kind="marker"]').count(),0);
   check("background-two-endpoints",await page.locator("#chart-wheel [data-selected]").count()>=2,true);
   check("background-layout-frozen",await positions(),positionsBefore);
   await page.keyboard.press("Enter");await page.waitForSelector("#chart-wheel [data-aspect]");

   await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-wheel [data-selected="moon"]');
   await page.locator("#birth-edit").click();await page.locator("#birth-date").fill("1990-01-01");await page.locator("#terms-acknowledged").check();
   await page.locator('button[type="submit"]').click();await entered.promise;await page.locator("#birth-date").fill("2000-01-01");permit.resolve();
   await page.waitForFunction(()=>document.querySelector("#chart-result").dataset.chartIdentity==="own-B"&&document.querySelector("#chart-wheel svg"));
   check("POST-snapshot-B",posted.birth_date,"1990-01-01");
   check("draft-C-open",[await page.locator("#birth-date").inputValue(),await page.locator("#birth-editor").isHidden()],["2000-01-01",false]);
   check("summary-B",await page.locator("#chart-birth-summary").textContent().then(t=>t.includes("1990-01-01")&&!t.includes("2000-01-01")),true);
   check("changed-B-reset",[await page.locator('[data-point-id="moon"]').getAttribute("aria-pressed"),await page.locator("#houses-table tbody tr:visible").count()],["false",5]);
   const stale=await page.evaluate(id=>{const a=window.capturedLeaves.get(id);a.root.querySelector("text").textContent="late corruption";return[a.publish(a.root),a.surface.isConnected]},chart.chart_identity);
   check("stale-A-refused",stale,[false,false]);
   await page.locator("#houses-show-all").click();await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-wheel [data-selected="moon"]');
   current={...structuredClone(views.known_ready),chart:{...structuredClone(chart),chart_identity:"own-B"}};current.birth.birth_date="1990-01-01";
   await page.evaluate(()=>window.dispatchEvent(new Event("online")));
   await page.waitForFunction(()=>document.querySelector("#birth-form").getAttribute("aria-busy")==="false"&&document.querySelector("#chart-wheel svg"));
   check("automatic-preserves",[await page.locator('[data-point-id="moon"]').getAttribute("aria-pressed"),await page.locator("#houses-table tbody tr:visible").count()],["true",12]);
   check("automatic-keeps-C",await page.locator("#birth-date").inputValue(),"2000-01-01");
   await page.setViewportSize({width:width===360?768:360,height:1000});
   await page.waitForFunction(()=>{const s=document.querySelector("#chart-wheel svg");return s&&Math.floor(s.getBoundingClientRect().width)===Math.floor(document.getElementById("chart-wheel").getBoundingClientRect().width)});
   check("resize-keeps-selection",await page.locator('[data-point-id="moon"]').getAttribute("aria-pressed"),"true");
   await page.setViewportSize({width,height:1000});await page.waitForSelector("#chart-wheel svg");
   await page.locator(".chart-composition").screenshot({path:path.join(out,"accepted-B-"+width+".png")});
   current.chart.chart_identity="current-C";await page.evaluate(()=>{window.rejectCurrentLeaf=true;window.dispatchEvent(new Event("online"))});await page.waitForSelector("#wheel-error:not([hidden])");
   check("leaf-fault-retains-new-HTML",[await page.locator("#chart-result").getAttribute("data-chart-identity"),await page.locator("#points-table tbody tr").count(),await page.locator("#chart-wheel svg").count()],["current-C",chart.points.length,0]);
   check("leaf-fault-local",await page.locator("#form-error").isHidden(),true);
   current.chart.chart_identity="current-D";await page.evaluate(()=>{const h=document.getElementById("chart-wheel"),replace=h.replaceChildren.bind(h);h.replaceChildren=(...n)=>{h.replaceChildren=replace;throw Error("controlled-controller-owner")};window.dispatchEvent(new Event("online"))});
   await page.waitForSelector("#form-error:not([hidden])");
   check("controller-fault-safe-read",await page.getByRole("button",{name:"Повторить проверку карты",exact:true}).isVisible(),true);
   await page.getByRole("button",{name:"Повторить проверку карты",exact:true}).click();
   await page.waitForFunction(()=>document.querySelector("#chart-result").dataset.chartIdentity==="current-D"&&document.querySelector("#chart-wheel svg"));
   check("safe-read-positive",await page.locator("#form-error").isHidden(),true);
   await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");
   const row=page.locator("#aspects-table tbody tr:visible button:not(:disabled)").first(),sourceIndex=await row.evaluate(n=>[...n.closest("tbody").children].indexOf(n.closest("tr")));
   await row.focus();await page.keyboard.press("Space");
   current.chart.chart_identity="S1-current";current.chart.aspects.push({...current.chart.aspects[sourceIndex],from:current.chart.aspects[sourceIndex].to,to:current.chart.aspects[sourceIndex].from,category:"background"});
   await page.evaluate(()=>window.dispatchEvent(new Event("online")));await page.waitForFunction(()=>document.querySelector("#chart-result").dataset.chartIdentity==="S1-current");
   check("S1-warning",await page.locator("#aspect-warnings").isVisible(),true);
   check("S1-live-focus",await page.evaluate(()=>document.activeElement.tagName==="BUTTON"&&document.activeElement.isConnected&&!document.activeElement.disabled&&!document.activeElement.closest("[hidden]")),true);
   check("S1-all-rows",await page.locator("#aspects-table tbody tr").count(),current.chart.aspects.length);
   await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");
   current={status:"empty",state_version:4,birth:null,chart:null,chart_stale:null};await page.evaluate(()=>window.dispatchEvent(new Event("online")));await page.waitForSelector("#chart-result[hidden]",{state:"attached"});
   check("empty-removes-SVG",await page.locator("#chart-wheel svg").count(),0);
   check("empty-live-editor-focus",await page.evaluate(()=>document.activeElement===document.getElementById("birth-date")&&!document.getElementById("birth-editor").hidden),true);
   check("one-explicit-POST",record.requests.filter(r=>r.method==="build").length,1);check("no-page-errors",record.errors,[]);
   for(const draft of ["B","C"]){
    current={...structuredClone(views.known_ready),chart:structuredClone(chart)};buildMode="already_applied";permit=deferred();entered=deferred();
    await page.goto(base);await page.waitForSelector("#chart-wheel svg");
    await page.locator("#houses-show-all").click();await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-wheel [data-selected="moon"]');
    await page.locator("#birth-edit").click();await page.locator("#birth-date").fill("1990-01-01");await page.locator("#terms-acknowledged").check();
    await page.locator('button[type="submit"]').click();await entered.promise;
    if(draft==="C")await page.locator("#birth-date").fill("2000-01-01");
    current={...structuredClone(views.known_ready),chart:{...structuredClone(chart),chart_identity:"already-B-"+draft}};
    current.birth.birth_date="1990-01-01";permit.resolve();
    await page.waitForFunction(id=>document.querySelector("#chart-result").dataset.chartIdentity===id&&document.querySelector("#chart-wheel svg"),current.chart.chart_identity);
    check("already-"+draft+"-reset-once",[await page.locator('[data-point-id="moon"]').getAttribute("aria-pressed"),await page.locator("#houses-table tbody tr:visible").count()],["false",5]);
    check("already-"+draft+"-collapse-iff-matched",await page.locator("#birth-editor").isHidden(),draft==="B");
    check("already-"+draft+"-summary-from-GET",await page.locator("#chart-birth-summary").textContent().then(t=>t.includes("1990-01-01")&&!t.includes("2000-01-01")),true);
    if(draft==="B")await page.locator("#birth-edit").click();
    await page.locator("#houses-show-all").click();await page.locator('[data-point-id="moon"]').focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-wheel [data-selected="moon"]');
    await page.evaluate(()=>window.dispatchEvent(new Event("online")));await page.waitForFunction(()=>document.querySelector("#birth-form").getAttribute("aria-busy")==="false"&&document.querySelector("#chart-wheel svg"));
    check("already-"+draft+"-automatic-no-second-reset",[await page.locator('[data-point-id="moon"]').getAttribute("aria-pressed"),await page.locator("#houses-table tbody tr:visible").count(),await page.locator("#birth-editor").isHidden()],["true",12,false]);
   }
   record.timings=await page.evaluate(()=>window.drawingTimings);
   check("exact-explicit-POST-count",record.requests.filter(r=>r.method==="build").length,3);
   check("final-no-page-errors",record.errors,[]);
   record.pass=true;
  }catch(e){record.pass=false;record.error=String(e);await page.screenshot({path:path.join(out,"failure-"+width+".png"),fullPage:true});console.log("FAIL",width,record.error)}
  output.cases.push(record);fs.writeFileSync(path.join(out,"case-"+width+".json"),JSON.stringify(record,null,2)+"\n");console.log(record.pass?"PASS":"FAIL","integration",width,record.checks.length);await page.close();
 }
 output.finished=new Date().toISOString();fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");if(output.cases.some(c=>!c.pass))process.exitCode=1;
}
main().catch(e=>{output.error=String(e);fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r())});
