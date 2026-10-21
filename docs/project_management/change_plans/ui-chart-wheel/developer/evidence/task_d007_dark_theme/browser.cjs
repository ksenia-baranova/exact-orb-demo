// Actual application, current source, controlled HTTP only. Dark palette regression.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),http=require("node:http"),crypto=require("node:crypto");
const {chromium}=require("C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const root=path.resolve(__dirname,"../../../../../../.."),ui=path.join(root,"src/exact_orb/http_api/ui");
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,"../column_full_composition_v1/data.json"),"utf8"));
const views=JSON.parse(fs.readFileSync(path.join(root,"tests/http_api/golden/session_view.json"),"utf8"));
const prior=JSON.parse(fs.readFileSync(path.join(__dirname,"../task_d007_runtime/run05/actual.json"),"utf8"));
const out=path.join(__dirname,process.argv[2]||"run01");if(fs.existsSync(out))throw Error("Refuse overwrite");fs.mkdirSync(out);
const output={subject:"D007 Owner black wheel palette",started:new Date().toISOString(),cases:[],sources:{}};
for(const name of fs.readdirSync(ui))if(/\.(mjs|css|html)$/.test(name))output.sources[name]=crypto.createHash("sha256").update(fs.readFileSync(path.join(ui,name),"utf8").replaceAll("\r\n","\n")).digest("hex");
const rgb=hex=>/^#[0-9a-f]{6}$/i.test(hex)?[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)):hex.match(/[\d.]+/g)?.slice(0,3).map(Number);
const luminance=color=>{const v=rgb(color).map(n=>{const s=n/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4});return v[0]*.2126+v[1]*.7152+v[2]*.0722};
const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
let server,browser;
async function main(){
 server=http.createServer((req,res)=>{const name=req.url==="/"?"/ui/index.html":new URL(req.url,"http://localhost").pathname;
  if(!/^\/ui\/[a-z_]+\.(?:mjs|css|html)$/.test(name)){res.writeHead(404).end();return}
  const file=path.join(ui,path.basename(name));res.setHeader("Content-Type",file.endsWith(".mjs")?"text/javascript":file.endsWith(".css")?"text/css":"text/html");res.end(fs.readFileSync(file));
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));const base="http://127.0.0.1:"+server.address().port;
 browser=await chromium.launch({headless:true,executablePath:"C:/Program Files/Google/Chrome/Application/chrome.exe"});output.browser=browser.version();
 for(const fixture of ["F3-max","palette-control","cosmogram"])for(const width of [1440,768,360]){
  const id=fixture+"-"+width,page=await browser.newPage({viewport:{width,height:1000}}),record={id,fixture,width,errors:[],requests:[]};
  const current=structuredClone(views.known_ready);current.chart=structuredClone(fixtures[fixture].chart);current.chart_stale=false;
  if(current.chart.kind==="cosmogram"){current.birth.time_unknown=true;current.birth.birth_time=null;current.birth.utc_offset_seconds=null}
  page.on("pageerror",e=>record.errors.push(String(e)));
  await page.route("**/session/bootstrap",r=>{record.requests.push("bootstrap");return r.fulfill({json:{status:"ready",state_version:1}})});
  await page.route("**/charts/current",r=>{record.requests.push("current");return r.fulfill({json:current})});
  await page.route("**/charts/natal",()=>{throw Error("Unexpected POST")});
  try{
   await page.goto(base);await page.waitForSelector("#chart-wheel svg");
   record.actual=await page.evaluate(async()=>{
    const svg=document.querySelector("#chart-wheel svg"),outer=svg.getBoundingClientRect(),relative=b=>[b.left-outer.left,b.top-outer.top,b.right-outer.left,b.bottom-outer.top];
    return {background:getComputedStyle(document.getElementById("chart-wheel")).backgroundColor,
     overflow:document.documentElement.scrollWidth>innerWidth,width:outer.width,height:outer.height,
     groups:[...svg.querySelectorAll("[data-label]")].map(g=>({key:g.getAttribute("data-label"),kind:g.getAttribute("data-kind"),origin:[g.transform.baseVal.consolidate().matrix.e,g.transform.baseVal.consolidate().matrix.f],column:g.getAttribute("data-column"),parts:[...g.querySelectorAll("rect")].filter(n=>!n.hasAttribute("data-selected")).map(n=>relative(n.getBoundingClientRect()))})),
     textPaints:[...svg.querySelectorAll("[data-component]")].map(n=>({text:n.textContent,fill:getComputedStyle(n).fill})),
     labelPaints:[...svg.querySelectorAll("[data-label] rect")].map(n=>getComputedStyle(n).fill),
     rings:[...svg.querySelectorAll("[data-sector]")].map(n=>getComputedStyle(n).fill),
     strokes:[...svg.querySelectorAll("path,line,circle")].filter(n=>!n.hasAttribute("data-leader-bridge")).map(n=>getComputedStyle(n).stroke).filter(c=>c!=="none"),
     palette:(await import("/ui/wheel_layout.mjs")).ASPECT_COLORS};
   });
   assert.equal(record.actual.background,"rgb(8, 7, 6)");
   assert.ok(record.actual.labelPaints.every(p=>p==="rgb(8, 7, 6)"));
   assert.ok(record.actual.rings.every(p=>["rgb(17, 17, 17)","rgb(24, 24, 24)"].includes(p)));
   assert.equal(record.actual.overflow,false);
   record.textMinContrast=Math.min(...record.actual.textPaints.map(p=>contrast(p.fill,record.actual.background)));
   record.aspectMinContrast=Math.min(...Object.values(record.actual.palette).map(c=>contrast(c,"#181818")));
   record.strokeMinContrast=Math.min(...record.actual.strokes.map(c=>contrast(c,"#181818")));
   assert.ok(record.textMinContrast>=4.5);assert.ok(record.aspectMinContrast>=4.5);assert.ok(record.strokeMinContrast>=3);
   assert.equal(new Set(Object.values(record.actual.palette)).size,7);
   const old=prior.cases.find(c=>c.id===id);assert.ok(old);
   assert.deepEqual(record.actual.groups,old.actual.groups,"Theme must not change native geometry");
   record.geometryUnchanged=true;
   const requests=record.requests.length,moon=page.locator('[data-point-id="moon"]');
   await moon.focus();await page.keyboard.press("Enter");await page.waitForSelector('#chart-wheel [data-selected="moon"]');
   record.selectionStroke=await page.locator('#chart-wheel [data-selected="moon"]').first().getAttribute("stroke");
   assert.equal(record.selectionStroke,"#f0cd73");assert.equal(await moon.evaluate(n=>document.activeElement===n),true);
   assert.equal(record.requests.length,requests);assert.deepEqual(record.errors,[]);
   await page.locator("#chart-wheel").screenshot({path:path.join(out,id+".png")});record.pass=true;
  }catch(e){record.pass=false;record.error=String(e);console.log("FAIL",id,record.error)}
  fs.writeFileSync(path.join(out,id+".json"),JSON.stringify(record,null,2)+"\n");output.cases.push(record);console.log(record.pass?"PASS":"FAIL",id);await page.close();
 }
 output.finished=new Date().toISOString();fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");if(output.cases.some(c=>!c.pass))process.exitCode=1;
}
main().catch(e=>{output.error=String(e);fs.writeFileSync(path.join(out,"actual.json"),JSON.stringify(output,null,2)+"\n");console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();await new Promise(r=>server?server.close(r):r())});
