// Real production main/session/controller/HTML/SVG; only HTTP is controlled.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require(process.env.WHEEL_PLAYWRIGHT||"C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../../../../../.."),ui=path.join(root,"src/exact_orb/http_api/ui");
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,"../column_full_composition_v1/data.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(root,"tests/http_api/golden/session_view.json"),"utf8"));
const run=process.argv[2]||"run01",out=path.join(__dirname,run);
if(fs.existsSync(out))throw Error("Refuse overwrite "+run);
fs.mkdirSync(out);fs.mkdirSync(path.join(out,"screenshots"));
const output={subject:"TASK-D-007 full application SVG integration",started:new Date().toISOString(),cases:[],sources:{}};
for(const file of fs.readdirSync(ui))if(/\.(mjs|css|html)$/.test(file))output.sources[file]=crypto.createHash("sha256").update(fs.readFileSync(path.join(ui,file),"utf8").replaceAll("\r\n","\n")).digest("hex");
let browser,server;
const controls=[];
async function main(){
 server=http.createServer((req,res)=>{
   const url=new URL(req.url,"http://localhost");let file;
   if(url.pathname==="/")file=path.join(ui,"index.html");
   else if(/^\/(?:ui|actual)\/[a-z_]+\.(?:mjs|css|html)$/.test(url.pathname))file=path.join(ui,path.basename(url.pathname));
   else if(/^\/controls\/[a-z_]+\.(?:mjs|html)$/.test(url.pathname))file=path.join(__dirname,path.basename(url.pathname));
   else{res.writeHead(404).end();return}
   try{res.setHeader("Content-Type",file.endsWith(".mjs")?"text/javascript":file.endsWith(".css")?"text/css":"text/html");res.end(fs.readFileSync(file))}catch{res.writeHead(404).end()}
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));
 const base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:process.env.WHEEL_BROWSER||"C:/Program Files/Google/Chrome/Application/chrome.exe"});
 output.browser=browser.version();
 fixtures["exact-tie"]=structuredClone(fixtures.F1);
 fixtures["exact-tie"].chart.chart_identity="native-exact-tie";
 for(const p of fixtures["exact-tie"].chart.points.filter(p=>["sun","moon"].includes(p.id))){p.longitude=359;p.sign="Pisces";p.degree=29;p.minute=0}
 const jobs=["sparse","F1","F3","F3-max","published-natal","cosmogram","multigroup-control","S1-control","palette-control","empty-cosmogram","exact-tie"]
  .flatMap(fixture=>[1440,768,360].map(width=>({fixture,width,dpr:1,font:"normal"})));
 jobs.push({fixture:"F3-max",width:360,dpr:2,font:"normal"},{fixture:"F3-max",width:360,dpr:1,font:"fallback"});
 if(process.argv.includes("--boundary-only"))jobs.length=0;
 for(const {fixture,width,dpr,font} of jobs){
  const page=await browser.newPage({viewport:{width,height:1000},deviceScaleFactor:dpr}),errors=[],requests=[],id=fixture+"-"+width+(dpr!==1?"-dpr"+dpr:"")+(font!=="normal"?"-"+font:"");
  const record={id,fixture,width,dpr,font,errors,requests};const chart=structuredClone(fixtures[fixture].chart);
  record.chart=structuredClone(chart);
  let current=structuredClone(views.known_ready);current.chart=chart;current.chart_stale=false;
  if(chart.kind==="cosmogram"){current.birth.time_unknown=true;current.birth.birth_time=null;current.birth.utc_offset_seconds=null}
  page.on("pageerror",e=>errors.push(String(e)));
  await page.route("**/session/bootstrap",r=>{requests.push("bootstrap");return r.fulfill({json:{status:"ready",state_version:1}})});
  await page.route("**/charts/current",r=>{requests.push("current");return r.fulfill({json:current})});
  await page.route("**/charts/natal",()=>{throw Error("Unexpected build")});
  try{
   await page.goto(base);await page.waitForFunction(()=>document.querySelector("#chart-wheel svg")||document.querySelector("#wheel-error:not([hidden])"));
   if(font==="fallback"){
    await page.addStyleTag({content:'svg { font-family: sans-serif !important; }'});
    await page.evaluate(()=>document.fonts.dispatchEvent(new Event("loadingdone")));
    await page.waitForFunction(()=>getComputedStyle(document.querySelector("#chart-wheel svg")).fontFamily==="sans-serif");
   }
   record.actual=await page.evaluate(()=>{
    const svg=document.querySelector("#chart-wheel svg");
    const warning=document.querySelector("#wheel-error");
    if(!svg)return {svg:false,error:warning?.textContent,html:document.querySelector("#chart-facts")?.textContent};
    const frameCircle=svg.querySelector("circle"); const outer=svg.getBoundingClientRect(),relative=b=>[b.left-outer.left,b.top-outer.top,b.right-outer.left,b.bottom-outer.top];
    return {svg:true,rendering:{devicePixelRatio,zoom:visualViewport.scale,font:getComputedStyle(svg).fontFamily},frame:{C:[frameCircle.cx.baseVal.value,frameCircle.cy.baseVal.value],R:frameCircle.r.baseVal.value},width:outer.width,height:outer.height,overflow:document.documentElement.scrollWidth>innerWidth,
     signs:svg.querySelectorAll("[data-sector]").length,points:[...svg.querySelectorAll('[data-kind="point"]')].map(n=>n.getAttribute("data-label")),
     houses:svg.querySelectorAll("[data-house]").length,angles:svg.querySelectorAll('[data-kind="angle"]').length,
     targets:svg.querySelectorAll("[tabindex],[onclick],[role=button]").length,
     texts:[...svg.querySelectorAll("[data-component]")].map(n=>({id:n.getAttribute("data-component"),text:n.textContent,size:getComputedStyle(n).fontSize,ctm:[n.getScreenCTM().a,n.getScreenCTM().d],box:relative(n.getBoundingClientRect())})),
     groups:[...svg.querySelectorAll("[data-label]")].map(g=>({key:g.getAttribute("data-label"),kind:g.getAttribute("data-kind"),origin:[g.transform.baseVal.consolidate().matrix.e,g.transform.baseVal.consolidate().matrix.f],column:g.getAttribute("data-column"),parts:[...g.querySelectorAll("rect")].filter(n=>!n.hasAttribute("data-selected")).map(n=>relative(n.getBoundingClientRect()))})),
     anchors:[...svg.querySelectorAll("[data-anchor]")].map(n=>({key:n.getAttribute("data-anchor"),box:relative(n.getBoundingClientRect())})),
     lines:[...svg.querySelectorAll("[data-aspect]")].map(n=>({key:n.getAttribute("data-aspect"),dash:n.getAttribute("stroke-dasharray"),stroke:n.getAttribute("stroke"),from:[n.getAttribute("x1"),n.getAttribute("y1")],to:[n.getAttribute("x2"),n.getAttribute("y2")]})),
     leaders:[...svg.querySelectorAll("[data-leader]")].map(n=>({key:n.getAttribute("data-leader"),d:n.getAttribute("d")})),
     markers:[...svg.querySelectorAll('[data-kind="marker"]')].map(n=>n.getAttribute("data-label")),
     focusTargets:[...document.querySelectorAll(".fact-select:not(:disabled)")].filter(n=>!n.closest("tr").hidden).map(n=>{const b=n.getBoundingClientRect();return {width:b.width,height:b.height}})
    };
   });
   assert.equal(record.actual.svg,true,record.actual.error);
   assert.equal(record.actual.signs,12);assert.equal(record.actual.targets,0);
   assert.deepEqual([...record.actual.points].sort(),chart.points.map(p=>p.id).sort());
   assert.equal(record.actual.houses,chart.houses?.length??0);assert.equal(record.actual.angles,Object.keys(chart.angles??{}).length);
   assert.equal(record.actual.overflow,false);assert.ok(record.actual.texts.every(t=>Number.parseFloat(t.size)>=12&&t.ctm[0]===1&&t.ctm[1]===1));
   assert.ok(record.actual.focusTargets.every(t=>t.width>=44&&t.height>=44));
   assert.ok(record.actual.texts.every(t=>!["точный","рабочий"].includes(t.text.toLowerCase())));
   if(fixture==="F3-max"){
    const cdp=await page.context().newCDPSession(page);await cdp.send("DOM.enable");await cdp.send("CSS.enable");
    const root=(await cdp.send("DOM.getDocument")).root.nodeId;
    const ids=(await cdp.send("DOM.querySelectorAll",{nodeId:root,selector:"#chart-wheel [data-component]"})).nodeIds;
    record.platformFonts=[];for(const nodeId of ids)record.platformFonts.push((await cdp.send("CSS.getPlatformFontsForNode",{nodeId})).fonts);
    await cdp.detach();
   }
   const before=requests.length,moon=page.locator('[data-point-id="moon"]');
   if(await moon.count()){
    await moon.focus();await page.keyboard.press("Enter");
    await page.waitForFunction(()=>document.querySelector('#chart-wheel [data-selected="moon"]'));
    assert.equal(await moon.getAttribute("aria-pressed"),"true");
    assert.equal(await moon.evaluate(n=>document.activeElement===n),true);
    assert.equal(requests.length,before);
   }
   record.pass=true;
   if(fixture==="F3-max")await page.locator(".chart-composition").screenshot({path:path.join(out,"screenshots",id+"-composition.png")});
   await page.screenshot({path:path.join(out,"screenshots",id+".png"),fullPage:true});
  }catch(e){record.pass=false;record.error=String(e);console.log("FAIL",id,record.error)}
  output.cases.push(record);fs.writeFileSync(path.join(out,id+".json"),JSON.stringify(record,null,2)+"\n");console.log(record.pass?"PASS":"FAIL",id);await page.close();
 }
 if(fs.existsSync(path.join(__dirname,"controls.html"))){
  const page=await browser.newPage({viewport:{width:768,height:900}});
  await page.goto(base+"/controls/controls.html");
  await page.waitForFunction(()=>window.boundaryReady);
  output.boundary=await page.evaluate(chart=>window.runBoundary(chart),fixtures.F1.chart);
  await page.close();
 }
 output.finished=new Date().toISOString();output.node=process.version;output.platform=process.platform;
 fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");
 if(output.cases.some(c=>!c.pass)||output.boundary?.controls.some(c=>!c.pass))process.exitCode=1;
}
main().catch(e=>{output.error=String(e);fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r())});
