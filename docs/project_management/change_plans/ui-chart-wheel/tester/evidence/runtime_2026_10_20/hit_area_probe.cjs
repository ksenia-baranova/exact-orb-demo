// Independent native hit-area calibration and short-viewport checks; no production edits.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require("C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const ROOT=path.resolve(__dirname,"../../../../../../.."),UI=path.join(ROOT,"src/exact_orb/http_api/ui"),OUT=path.join(__dirname,"probe01");
const fixtures=JSON.parse(fs.readFileSync(path.join(ROOT,"docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/data.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(ROOT,"tests/http_api/golden/session_view.json"),"utf8"));
if(fs.existsSync(OUT))throw Error("Refuse overwrite");fs.mkdirSync(OUT);
const data={tested_sha:"0da99518ada67603b08ab4220d337e3a5e3aae60",author:"Codex / Tester",started_utc:new Date().toISOString(),sources:{},cases:[]};
for(const f of fs.readdirSync(UI))if(/\.(mjs|css|html)$/.test(f))data.sources[f]=crypto.createHash("sha256").update(fs.readFileSync(path.join(UI,f),"utf8").replaceAll("\r\n","\n")).digest("hex");
let server,browser,base;
const save=()=>fs.writeFileSync(path.join(OUT,"actual.json"),JSON.stringify(data,null,2)+"\n");
async function open(width,height,chart){
 const p=await browser.newPage({viewport:{width,height}}),view=structuredClone(views.known_ready);view.chart=structuredClone(chart);
 await p.route("**/session/bootstrap",r=>r.fulfill({json:{status:"ready",state_version:1}}));
 await p.route("**/charts/current",r=>r.fulfill({json:view}));
 await p.route("**/charts/natal",()=>{throw Error("Unexpected build");});
 await p.goto(base);await p.waitForFunction(()=>document.querySelector("#chart-wheel svg")||document.querySelector("#wheel-error:not([hidden])"));
 return p;
}
async function main(){
 server=http.createServer((req,res)=>{
  let u=new URL(req.url,"http://localhost").pathname;if(u==="/")u="/ui/index.html";
  if(!/^\/ui\/[a-z_]+\.(mjs|css|html)$/.test(u)){res.writeHead(404).end();return}
  const f=path.join(UI,path.basename(u));res.setHeader("Content-Type",f.endsWith(".mjs")?"text/javascript":f.endsWith(".css")?"text/css":"text/html");res.end(fs.readFileSync(f));
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:"C:/Program Files/Google/Chrome/Application/chrome.exe"});data.browser=browser.version();
 for(const width of [1440,768,360]){
  const p=await open(width,900,fixtures.F1.chart),r={id:"target-"+width};const sun=p.locator('[data-point-id="sun"]');await sun.scrollIntoViewIfNeeded();
  r.measure=await sun.evaluate(n=>{
   const b=n.getBoundingClientRect(),s=getComputedStyle(n),rows=[];
   for(const offset of [1,2,22,42,43]){
    let run=0,longest=0;const probes=[];
    for(let x=b.left-1;x<=b.right+1;x+=.25){const hit=document.elementFromPoint(x,b.top+offset)?.closest('[data-point-id="sun"]')===n;probes.push({x,hit});run=hit?run+.25:0;longest=Math.max(longest,run)}
    rows.push({offset,longest,probes});
   }
   window.__probeEvents=[];n.addEventListener("click",e=>window.__probeEvents.push({trusted:e.isTrusted,x:e.clientX,y:e.clientY}));
   return {box:{x:b.x,y:b.y,width:b.width,height:b.height},radius:s.borderRadius,rows};
  });
  const b=r.measure.box;await p.mouse.click(b.x+b.width/2,b.y+b.height/2);
  r.positiveCenterSelected=await sun.getAttribute("aria-pressed");
  await p.mouse.click(b.x+1,b.y+1);r.afterCornerSelected=await sun.getAttribute("aria-pressed");r.events=await p.evaluate(()=>window.__probeEvents);
  r.containedSquare44Possible=b.height>44||(b.height===44&&r.measure.rows[0].longest>=44);
  r.proof="The actual box height is exactly44. Any contained axis-aligned square44 must use the full vertical extent; its section at top+1 must therefore have width>=44. Native scan interval0.25 gives a strictly smaller horizontal aperture. Center actual trusted click is the independent positive control.";
  await p.evaluate(()=>{for(const [id,w,left] of [["positive",44,4],["negative",43,70]]){const b=document.createElement("button");b.id="probe-"+id;b.textContent=id;
   b.style.cssText="all:initial;box-sizing:border-box;position:fixed;z-index:99999;top:4px;left:"+left+"px;width:"+w+"px;height:44px;background:white;color:black;display:block;border-radius:0;pointer-events:auto";document.body.append(b)}});
  r.calibration=await p.evaluate(()=>["positive","negative"].map(id=>{const n=document.getElementById("probe-"+id),b=n.getBoundingClientRect();let span=0;for(let x=b.left+.125;x<b.right;x+=.25)if(document.elementFromPoint(x,b.top+1)===n)span+=.25;return {id,width:b.width,height:b.height,span}}));
  r.calibrationPass=r.calibration[0].span===44&&r.calibration[1].span===43;
  await p.screenshot({path:path.join(OUT,r.id+".png")});await p.close();data.cases.push(r);save();console.log(r.id,JSON.stringify({height:b.height,width:b.width,slice:r.measure.rows[0].longest,calibration:r.calibrationPass,possible44:r.containedSquare44Possible}));
 }
 for(const [width,height] of [[1440,720],[768,720],[360,720],[1440,600],[768,600],[360,640]]){
  const p=await open(width,height,fixtures["F3-max"].chart),r={id:"viewport-"+width+"x"+height};
  r.actual=await p.evaluate(()=>{const n=document.querySelector("#chart-wheel svg"),b=n?.getBoundingClientRect();return {svg:!!n,error:document.querySelector("#wheel-error")?.textContent,frame:b?{left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height}:null,overflow:document.documentElement.scrollWidth>innerWidth,viewport:[innerWidth,innerHeight]};});
  r.pass=r.actual.svg&&r.actual.frame.top>=0&&r.actual.frame.bottom<=height&&!r.actual.overflow;
  await p.screenshot({path:path.join(OUT,r.id+".png")});await p.close();data.cases.push(r);save();console.log(r.id,r.pass?"PASS":"FAIL",JSON.stringify(r.actual));
 }
 data.finished_utc=new Date().toISOString();save();
}
main().catch(e=>{data.fatal=String(e.stack||e);save();console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r());});
