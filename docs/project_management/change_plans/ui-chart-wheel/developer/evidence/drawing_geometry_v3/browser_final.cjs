// Isolated passive SVG measurement, no production imports or dependencies added.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),os=require('node:os'),crypto=require('node:crypto');
const {chromium}=require('C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const B=__dirname,read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const spec=read(path.join(B,'spec.json')),out=path.join(B,'browser-run03');if(fs.existsSync(out))throw Error('immutable run');fs.mkdirSync(out);fs.mkdirSync(path.join(out,'screenshots'));
const index={started:new Date().toISOString(),node:process.version,os:os.platform()+' '+os.release(),specSHA256:sha(path.join(B,'spec.json')),records:[],controls:[]};let browser,server;
async function main(){
 server=http.createServer((req,res)=>{const file=path.resolve(B,'.'+decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(B+path.sep)){res.writeHead(403).end();return}try{res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');res.end(fs.readFileSync(file))}catch{res.writeHead(404).end()}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--force-device-scale-factor=1']});index.browser=browser.version();index.browserPath='C:/Program Files/Google/Chrome/Application/chrome.exe';
 const context=await browser.newContext({viewport:{width:1440,height:1050},deviceScaleFactor:1});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/geometry.html`);await page.waitForFunction(()=>window.geometryReady===true);const cdp=await context.newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 for(const ref of read(path.join(B,'models/index.json')).records.filter(r=>/-[GH]\.json$/.test(r.file))){
  if(Date.now()>Date.parse(spec.deadline_utc))throw Error('PARENT_STOP');
  const model=read(path.join(B,'models',ref.file));await page.setViewportSize({width:model.viewport,height:1050});await page.evaluate(d=>window.drawGeometry(d),model);await page.evaluate(()=>document.fonts.ready);
  const measurement=await page.evaluate(()=>window.measureGeometry());const doc=await cdp.send('DOM.getDocument');const nodes=await cdp.send('DOM.querySelectorAll',{nodeId:doc.root.nodeId,selector:'svg text'});const fonts=[];
  for(const nodeId of nodes.nodeIds){const attributes=await cdp.send('DOM.getAttributes',{nodeId});const found=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});fonts.push({attributes:attributes.attributes,fonts:found.fonts})}
  const screenshot=`screenshots/${ref.file.replace('.json','.png')}`;await page.screenshot({path:path.join(out,screenshot),fullPage:false});const record={model:ref,measurement,fonts,pageErrors:[...errors],screenshot,screenshotSHA256:sha(path.join(out,screenshot))};fs.writeFileSync(path.join(out,ref.file),JSON.stringify(record,null,2)+'\n');index.records.push({file:ref.file,sha256:sha(path.join(out,ref.file))});
  if(model.variant==='H')console.log('V3_BROWSER',ref.file,'groups',measurement.groups.length,'interactiveSVG',measurement.interactiveSVG,'drift',measurement.maxComponentDrift);
 }
 const controls=await page.evaluate(()=>window.geometryControls());index.controls=controls;if(controls.some(c=>c.actual!==c.expected))throw Error('browser control failed');index.ended=new Date().toISOString();fs.writeFileSync(path.join(out,'index.json'),JSON.stringify(index,null,2)+'\n');console.log('V3_BROWSER_COMPLETE records='+index.records.length+' controls='+controls.length+' pageErrors='+errors.length);
}
main().catch(e=>{index.error=String(e);fs.writeFileSync(path.join(out,'index.json'),JSON.stringify(index,null,2)+'\n');console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();server?.close()});
