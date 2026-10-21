const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const{chromium}=require('C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../../../../../..'),ui=path.join(root,'src/exact_orb/http_api/ui'),out=path.join(__dirname,process.argv[2]||'native01');
if(fs.existsSync(out))throw Error('Refuse overwrite');fs.mkdirSync(out);
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/data.json'),'utf8'));
const views=JSON.parse(fs.readFileSync(path.join(root,'tests/http_api/golden/session_view.json'),'utf8'));
const record={author:'Codex / Developer',kind:'Native H44 regression; real modules; controlled HTTP',cases:[],sources:{}};
for(const f of fs.readdirSync(ui))if(/\.(mjs|css|html)$/.test(f))record.sources[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(ui,f),'utf8').replaceAll('\r\n','\n')).digest('hex');
let server;
async function measure(locator){
 await locator.scrollIntoViewIfNeeded();
 return locator.evaluate(n=>{
  const b=n.getBoundingClientRect(),s=getComputedStyle(n),q={x:b.x+(b.width-44)/2,y:b.y+(b.height-44)/2,size:44},failed=[],offsets=[.25,...Array.from({length:21},(_,i)=>2.25+2*i),43.75];let hits=0;
  for(const dx of offsets)for(const dy of offsets){const x=q.x+dx,y=q.y+dy,hit=document.elementFromPoint(x,y),ok=hit===n||n.contains(hit);if(ok)hits++;else if(failed.length<20)failed.push({x,y,hit:hit?.tagName,id:hit?.id});}
  return {label:n.textContent,box:{x:b.x,y:b.y,width:b.width,height:b.height},q,radius:s.borderRadius,clip:s.clipPath,visibility:s.visibility,grid:offsets.length**2,hits,failed,containsCandidate:b.width>=44&&b.height>=44&&hits===offsets.length**2};
 });
}
(async()=>{
 server=http.createServer((req,res)=>{const name=req.url==='/'?'index.html':path.basename(req.url);if(!/^[a-z_]+\.(mjs|css|html)$/.test(name)){res.writeHead(404).end();return}res.setHeader('Content-Type',name.endsWith('.mjs')?'text/javascript':name.endsWith('.css')?'text/css':'text/html');res.end(fs.readFileSync(path.join(ui,name)))});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 for(const[vendor,executablePath]of[['Chrome','C:/Program Files/Google/Chrome/Application/chrome.exe'],['Yandex','C:/Users/KateUser/AppData/Local/Yandex/YandexBrowser/Application/browser.exe']]){
 if(process.argv.includes('--red')&&vendor!=='Chrome')continue;const browser=await chromium.launch({headless:true,executablePath});
 try{for(const width of(process.argv.includes('--red')?[1440]:[1440,768,360])){
 const page=await browser.newPage({viewport:{width,height:900}}),c={vendor,width,version:browser.version(),checks:[],controls:[],requests:[],errors:[]};record.cases.push(c);
 const check=(name,ok,actual)=>{c.checks.push({name,pass:!!ok,actual});};page.on('pageerror',e=>c.errors.push(String(e)));page.on('request',r=>{if(/\/(session|charts)\//.test(r.url()))c.requests.push(r.method()+' '+new URL(r.url()).pathname)});
 const current={...structuredClone(views.known_ready),chart:structuredClone(fixtures.F1.chart)};
 await page.route('**/session/bootstrap',r=>r.fulfill({json:{status:'ready',state_version:1}}));await page.route('**/charts/current',r=>r.fulfill({json:current}));await page.route('**/charts/natal',r=>r.abort());
 try{
 await page.goto('http://127.0.0.1:'+server.address().port);await page.waitForFunction(()=>document.querySelector('#chart-wheel svg'));
 const requests=c.requests.length;
 for(const id of['points-show-all','aspects-show-all'])if(await page.locator('#'+id).isVisible())await page.locator('#'+id).click();
 const controls=await page.locator('.fact-select:visible:enabled').all();
 for(let index=0;index<controls.length;index++){const m=await measure(controls[index]);c.controls.push(m);check('actual-Q44-'+index,m.containsCandidate,m.failed);}
 const sun=page.locator('[data-point-id="sun"]');await sun.scrollIntoViewIfNeeded();
 await sun.evaluate(n=>{window.__hitEvents=[];n.addEventListener('click',e=>window.__hitEvents.push({trusted:e.isTrusted,x:e.clientX,y:e.clientY}));});
 for(const[dx,dy]of[[22,22],[.25,.25],[43.75,.25],[.25,43.75],[43.75,43.75]]){
  const m=await measure(sun),before=await sun.getAttribute('aria-pressed');await page.mouse.click(m.q.x+dx,m.q.y+dy);
  check('trusted-coordinate-toggle-'+dx+'-'+dy,await sun.getAttribute('aria-pressed')!==before,{x:m.q.x+dx,y:m.q.y+dy});
 }
 c.events=await page.evaluate(()=>window.__hitEvents);check('five-trusted-events',c.events.length===5&&c.events.every(e=>e.trusted),c.events);
 await sun.focus();const selected=await sun.getAttribute('aria-pressed');await sun.press('Enter');check('keyboard-enter',await sun.getAttribute('aria-pressed')!==selected);await sun.press('Space');check('keyboard-space',await sun.getAttribute('aria-pressed')===selected);check('planet-focus-live',await sun.evaluate(n=>document.activeElement===n&&n.isConnected));
 if(await sun.getAttribute('aria-pressed')==='true')await sun.press('Enter');
 if(await page.locator('#aspects-show-all').getAttribute('aria-expanded')==='false')await page.locator('#aspects-show-all').click();
 const aspect=page.locator('#aspects-table .fact-select:visible:enabled').first(),am=await measure(aspect);await page.mouse.click(am.q.x+.25,am.q.y+.25);
 check('aspect-coordinate-activation',await page.locator('#chart-details').count()===0&&await page.locator('#aspect-close').isVisible());check('aspect-focus',await page.locator('#chart-wheel').evaluate(n=>document.activeElement===n));
 if(!await page.locator('#aspect-close').isVisible()){await aspect.click();check('positive-center-aspect',await page.locator('#aspect-close').isVisible());}c.selectedAspect=await measure(page.locator('#aspects-table .fact-select:visible:enabled').first());check('selected-aspect-Q44',c.selectedAspect.containsCandidate,c.selectedAspect);
 await page.locator('#aspect-close').click();check('no-interaction-HTTP',c.requests.length===requests,c.requests);
 await page.evaluate(()=>{for(const[id,w,x]of[['positive',44,4],['negative',43,70],['overlay',44,130],['clip',44,190]]){
 const host=document.createElement('div');host.style.cssText='position:fixed;left:'+x+'px;top:4px;width:'+(id==='clip'?43:w)+'px;height:44px;z-index:999999;overflow:hidden';
 const n=document.createElement('button');n.id='cal-'+id;n.textContent=id;n.style.cssText='all:initial;display:block;box-sizing:border-box;width:'+w+'px;height:44px;border-radius:0;background:white';host.append(n);
 if(id==='overlay'){const mask=document.createElement('div');mask.style.cssText='position:absolute;top:0;right:0;width:10px;height:44px;background:red';host.append(mask);}document.body.append(host);
 }});
 c.calibration={};for(const id of['positive','negative','overlay','clip'])c.calibration[id]=await measure(page.locator('#cal-'+id));
 check('paired-44-43-controls',c.calibration.positive.containsCandidate&&!c.calibration.negative.containsCandidate,c.calibration);
 check('same-bbox-overlay-control',!c.calibration.overlay.containsCandidate,c.calibration.overlay);check('clip-control',!c.calibration.clip.containsCandidate,c.calibration.clip);
 await page.evaluate(()=>document.querySelectorAll('[id^="cal-"]').forEach(n=>n.parentElement.remove()));
 await sun.scrollIntoViewIfNeeded();c.layout=await sun.evaluate(n=>({rowHeight:n.closest('tr').getBoundingClientRect().height,overflow:document.documentElement.scrollWidth>innerWidth}));
 check('no-page-overflow',!c.layout.overflow,c.layout);if(width>700)check('compact-row',c.layout.rowHeight<=56,c.layout);
 await page.screenshot({path:path.join(out,vendor+'-'+width+'.png')});check('no-page-errors',c.errors.length===0,c.errors);
 }catch(e){c.error=String(e)}
 c.pass=!c.error&&c.checks.every(check=>check.pass);console.log(c.pass?'PASS':'FAIL',vendor,width,c.error||c.checks.filter(v=>!v.pass).map(v=>v.name).join(','));fs.writeFileSync(path.join(out,'actual.json'),JSON.stringify(record,null,2)+'\n');await page.close();
 }}finally{await browser.close()}
 }
 if(record.cases.some(c=>!c.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>server?.close());