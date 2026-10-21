// Real app/renderer. HTTP is the only fake. Owner20.10 composition + aspect mode.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const {chromium}=require("C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../../../../../.."),ui=path.join(root,"src/exact_orb/http_api/ui");
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,"../column_full_composition_v1/data.json"),"utf8"));
fixtures.cosmogram={chart:JSON.parse(fs.readFileSync(path.join(root,"tests/http_api/golden/chart_dto.json"),"utf8")).cosmogram};
const views=JSON.parse(fs.readFileSync(path.join(root,"tests/http_api/golden/session_view.json"),"utf8"));
const out=path.join(__dirname,process.argv[2]||"focus01");if(fs.existsSync(out))throw Error("Refuse overwrite");fs.mkdirSync(out);
const output={started:new Date().toISOString(),subject:"Numbered house composition and Owner aspect focus",cases:[],sources:{}};
for(const name of fs.readdirSync(ui))if(/\.(mjs|html|css)$/.test(name))output.sources[name]=crypto.createHash("sha256").update(fs.readFileSync(path.join(ui,name),"utf8").replaceAll("\r\n","\n")).digest("hex");
const key=a=>JSON.stringify([...[a.from,a.to].sort(),a.type]);
let server,browser;
async function main(){
 server=http.createServer((req,res)=>{const name=req.url==="/"?"/ui/index.html":new URL(req.url,"http://localhost").pathname;
 if(!/^\/ui\/[a-z_]+\.(?:mjs|css|html)$/.test(name)){res.writeHead(404).end();return}
 const file=path.join(ui,path.basename(name));res.setHeader("Content-Type",file.endsWith(".mjs")?"text/javascript":file.endsWith(".css")?"text/css":"text/html");res.end(fs.readFileSync(file))});
 await new Promise(r=>server.listen(0,"127.0.0.1",r));const base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:"C:/Program Files/Google/Chrome/Application/chrome.exe"});output.browser=browser.version();
 for(const fixture of ["published-natal","F3-max","cosmogram","palette-control"])for(const width of [1440,768,360]){
  const page=await browser.newPage({viewport:{width,height:1000}}),id=fixture+"-"+width,record={id,width,fixture,checks:[],requests:[],errors:[]};
  const check=(name,actual,expected)=>{const pass=JSON.stringify(actual)===JSON.stringify(expected);record.checks.push({name,actual,expected,pass});assert.deepEqual(actual,expected,name)};
  const chart=structuredClone(fixtures[fixture].chart);record.chart=structuredClone(chart);const current={...structuredClone(views.known_ready),chart,chart_stale:false};let readFailure=false;
  if(chart.kind==="cosmogram"){current.birth.birth_time=null;current.birth.time_unknown=true;current.birth.utc_offset_seconds=null}
  page.on("pageerror",e=>record.errors.push(String(e)));
  await page.route("**/session/bootstrap",r=>{record.requests.push("bootstrap");return r.fulfill({json:{status:"ready",state_version:1}})});
  await page.route("**/charts/current",r=>{record.requests.push("current");return readFailure?r.fulfill({status:503,json:{code:"STATE_READ_FAILED",detail_code:null,user_message:"Controlled safe-read failure",retryable:false,issues:null}}):r.fulfill({json:current})});
  await page.route("**/charts/natal",()=>{throw Error("Unexpected POST")});
  const normalReady=()=>page.waitForFunction(n=>document.querySelectorAll('#chart-wheel [data-kind="point"]').length===n&&document.querySelector("#chart-wheel svg"),chart.points.length);
  try{
   await page.goto(base);await normalReady();
   record.normal=await page.evaluate(()=>{
    const svg=document.querySelector("#chart-wheel svg"),box=svg.getBoundingClientRect(),circles=[...svg.querySelectorAll("circle")];
    const groups=[...svg.querySelectorAll("[data-label]")].map(g=>({key:g.getAttribute("data-label"),parts:[...g.querySelectorAll("rect")].filter(n=>!n.hasAttribute("data-selected")).map(n=>{const b=n.getBoundingClientRect();return[b.left-box.left,b.top-box.top,b.right-box.left,b.bottom-box.top]})}));
    return{groups,width:box.width,height:box.height,houseNumbers:[...svg.querySelectorAll("[data-house-number]")].map(n=>+n.getAttribute("data-house-number")).sort((a,b)=>a-b),
    cuspCount:svg.querySelectorAll("[data-house]").length,ticks:svg.querySelectorAll("[data-degree-tick]").length,aspectRatio:circles[2].r.baseVal.value/circles[0].r.baseVal.value,
    overflow:document.documentElement.scrollWidth>innerWidth,zoom:visualViewport.scale,formHidden:document.getElementById("birth-form").hidden};
   });
   check("numbered-houses",record.normal.houseNumbers,chart.houses?Array.from({length:12},(_,i)=>i+1):[]);
   check("published-cusps",record.normal.cuspCount,chart.houses?.length??0);check("ruler",record.normal.ticks,360);check("no-page-overflow",record.normal.overflow,false);
   check("collapsed-form-does-not-duplicate-summary",record.normal.formHidden,true);
   if(record.normal.width>600)check("useful-aspect-area",record.normal.aspectRatio>.55,true);
   await page.locator(".chart-composition").screenshot({path:path.join(out,id+"-full.png")});
   const counts=new Map();for(const a of chart.aspects)counts.set(key(a),(counts.get(key(a))||0)+1);
   const ids=new Set(chart.points.map(p=>p.id));
   const chosenIndex=chart.aspects.findIndex(a=>counts.get(key(a))===1&&ids.has(a.from)&&ids.has(a.to)&&a.category!=="background");
   assert.ok(chosenIndex>=0,"positive source aspect fixture");
   const chosen=chart.aspects[chosenIndex],ends=new Set([chosen.from,chosen.to]),houses=[...new Set(chart.points.filter(p=>ends.has(p.id)).map(p=>p.house).filter(h=>h!==null))].sort((a,b)=>a-b);
   if(await page.locator("#aspects-show-all").isVisible())await page.locator("#aspects-show-all").click();
   const button=page.locator("#aspects-table tbody tr").nth(chosenIndex).locator("button"),before=record.requests.length;
   await button.focus();await page.keyboard.press("Enter");
   await page.waitForFunction(()=>document.querySelector("#chart-result").dataset.aspectFocus==="true"&&document.querySelectorAll('#chart-wheel [data-kind="point"]').length===2);
   record.selected=await page.evaluate(()=>{
    const svg=document.querySelector("#chart-wheel svg"),box=svg.getBoundingClientRect(),visibleRows=id=>[...document.querySelectorAll("#"+id+" tbody tr")].filter(n=>!n.hidden);
    return{width:box.width,height:box.height,groups:[...svg.querySelectorAll("[data-label]")].map(g=>({key:g.getAttribute("data-label"),parts:[...g.querySelectorAll("rect")].filter(n=>!n.hasAttribute("data-selected")).map(n=>{const b=n.getBoundingClientRect();return[b.left-box.left,b.top-box.top,b.right-box.left,b.bottom-box.top]})})),
     focus:document.activeElement.id,scrollTop:box.top,scrollBottom:box.bottom,viewportHeight:innerHeight,toolbarBottom:document.querySelector(".aspect-toolbar").getBoundingClientRect().bottom,
     aspectRows:visibleRows("aspects-table").length,pointIds:visibleRows("points-table").map(n=>n.querySelector("button").dataset.pointId).sort(),
     houses:visibleRows("houses-table").map(n=>+n.querySelector("th").textContent).sort((a,b)=>a-b),houseNumbers:[...svg.querySelectorAll("[data-house-number]")].map(n=>+n.getAttribute("data-house-number")).sort((a,b)=>a-b),
     graphicPoints:[...svg.querySelectorAll('[data-kind="point"]')].map(n=>n.getAttribute("data-label")).sort(),formHidden:document.getElementById("birth-form").hidden,
     headingHidden:document.getElementById("birth-page-heading").hidden,summaryHidden:document.querySelector(".chart-summary").hidden,
     lines:svg.querySelectorAll("[data-aspect]").length,markers:svg.querySelectorAll('[data-kind="marker"]').length};
   });
   check("focus-wheel",record.selected.focus,"chart-wheel");check("aspect-only-row",record.selected.aspectRows,1);
   check("two-point-rows",record.selected.pointIds,[...ends].sort());check("two-graphic-points",record.selected.graphicPoints,[...ends].sort());
   check("published-houses-only",record.selected.houses,houses);check("graphic-house-numbers-only",record.selected.houseNumbers,houses);
   check("focused-page",[record.selected.formHidden,record.selected.headingHidden,record.selected.summaryHidden],[true,true,true]);
   check("only-chosen-graphic",[record.selected.lines,record.selected.markers],chosen.type==="conjunction"?[0,1]:[1,0]);
   check("view-scrolls-to-wheel",record.selected.scrollTop>=0&&record.selected.scrollBottom<=record.selected.viewportHeight&&record.selected.toolbarBottom<=record.selected.scrollTop,true);
   check("activation-no-HTTP",record.requests.length,before);
   await page.screenshot({path:path.join(out,id+"-selected.png"),fullPage:true});
   if(width===360)await page.keyboard.press("Escape");else await page.locator("#aspect-close").click();await normalReady();
   check("close-restores-native-source-focus",await button.evaluate(n=>document.activeElement===n&&n.isConnected),true);
   check("close-restores-all-points",await page.locator("#points-table tbody tr:visible").count(),chart.points.length);
   const backgroundIndex=chart.aspects.findIndex(a=>a.category==="background"&&counts.get(key(a))===1&&ids.has(a.from)&&ids.has(a.to));
   if(backgroundIndex>=0){
    const bg=page.locator("#aspects-table tbody tr").nth(backgroundIndex).locator("button");await bg.focus();await page.keyboard.press("Space");
    await page.waitForFunction(()=>document.querySelectorAll('#chart-wheel [data-kind="point"]').length===2);
    check("background-no-line-marker",await page.locator('#chart-wheel [data-aspect],#chart-wheel [data-kind="marker"]').count(),0);
    await page.locator("#aspect-close").click();await normalReady();
   }
   // Failed safe read while in focus mode must keep recovery reachable.
   await button.focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-result[data-aspect-focus="true"]');
   readFailure=true;await page.evaluate(()=>window.dispatchEvent(new Event("online")));await page.waitForSelector("#form-error:not([hidden])");
   check("safe-recovery-stays-reachable",await page.getByRole("button",{name:"Повторить проверку карты",exact:true}).isVisible(),true);
   readFailure=false;await page.getByRole("button",{name:"Повторить проверку карты",exact:true}).click();
   await page.waitForFunction(()=>document.querySelector("#form-error").hidden&&document.querySelector("#chart-wheel svg"));
   check("recovery-positive-keeps-aspect-mode",await page.locator("#chart-result").getAttribute("data-aspect-focus"),"true");
   check("recovery-focus-is-live-wheel",await page.evaluate(()=>document.activeElement===document.getElementById("chart-wheel")),true);
   // A later full-source duplicate invalidates selection and returns a complete map.
   current.chart.aspects.push({...chosen,from:chosen.to,to:chosen.from});current.chart.chart_identity+="-S1";await page.evaluate(()=>window.dispatchEvent(new Event("online")));
   await page.waitForSelector('#chart-result[data-aspect-focus="false"]');await normalReady();
   check("S1-returns-whole-map",await page.locator("#aspect-warnings").isVisible(),true);
   check("S1-source-rows",await page.locator("#aspects-table tbody tr").count(),current.chart.aspects.length);
   check("zero-page-errors",record.errors,[]);record.pass=true;
  }catch(e){record.pass=false;record.error=String(e);console.log("FAIL",id,record.error);await page.screenshot({path:path.join(out,id+"-failure.png"),fullPage:true})}
  output.cases.push(record);fs.writeFileSync(path.join(out,id+".json"),JSON.stringify(record,null,2)+"\n");console.log(record.pass?"PASS":"FAIL",id,record.checks.length);await page.close();
 }
 output.finished=new Date().toISOString();fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");if(output.cases.some(c=>!c.pass))process.exitCode=1;
}
main().catch(e=>{output.error=String(e);fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r())});
