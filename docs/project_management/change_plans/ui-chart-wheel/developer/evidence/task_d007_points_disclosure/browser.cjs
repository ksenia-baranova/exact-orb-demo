const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../../../../../..'),ui=path.join(root,'src/exact_orb/http_api/ui'),out=path.join(__dirname,process.argv[2]||'run01');
if(fs.existsSync(out))throw Error('Refuse overwrite');fs.mkdirSync(out);
const chart=JSON.parse(fs.readFileSync(path.join(root,'tests/ui/fixtures/natal_1985_chart_dto.json'),'utf8'));
const views=JSON.parse(fs.readFileSync(path.join(root,'tests/http_api/golden/session_view.json'),'utf8'));
const record={kind:'Real app; controlled HTTP leaf, published DTO; no real build',sources:{},cases:[]};
for(const name of fs.readdirSync(ui))if(/\.(mjs|html|css)$/.test(name))record.sources[name]=crypto.createHash('sha256').update(fs.readFileSync(path.join(ui,name),'utf8').replaceAll('\r\n','\n')).digest('hex');
let server;
(async()=>{
 server=http.createServer((req,res)=>{const name=req.url==='/'?'index.html':path.basename(req.url);if(!/^[a-z_]+\.(mjs|css|html)$/.test(name)){res.writeHead(404).end();return}res.setHeader('Content-Type',name.endsWith('.mjs')?'text/javascript':name.endsWith('.css')?'text/css':'text/html');res.end(fs.readFileSync(path.join(ui,name)))});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 for(const [vendor,executablePath]of [['Chrome','C:/Program Files/Google/Chrome/Application/chrome.exe'],['Yandex','C:/Users/KateUser/AppData/Local/Yandex/YandexBrowser/Application/browser.exe']]){
 const browser=await chromium.launch({headless:true,executablePath});
 try{for(const width of [1440,360]){
  const page=await browser.newPage({viewport:{width,height:900}}),checks=[],errors=[],requests=[];
  const item={vendor,width,version:browser.version(),checks,errors};record.cases.push(item);
  const check=(name,ok,actual)=>{checks.push({name,pass:!!ok,actual});if(!ok)throw Error(name+': '+JSON.stringify(actual))};
  page.on('pageerror',e=>errors.push(String(e)));page.on('request',req=>{if(/\/(session|charts)\//.test(req.url()))requests.push(req.method()+' '+new URL(req.url()).pathname)});
  const current={...structuredClone(views.known_ready),chart:structuredClone(chart),chart_stale:false};
  await page.route('**/session/bootstrap',route=>route.fulfill({json:{status:'ready',state_version:1}}));
  await page.route('**/charts/current',route=>route.fulfill({json:current}));
  await page.route('**/charts/natal',route=>route.abort());
  const count=()=>page.locator('#points-table tbody tr:visible').count();
  try{
   await page.goto('http://127.0.0.1:'+server.address().port);
   await page.waitForFunction(()=>document.querySelector('#chart-wheel svg')&&[...document.querySelectorAll('#points-table tbody tr')].filter(n=>!n.hidden).length===5);
   check('initial-first-five',await count()===5,await count());
   const ids=await page.locator('#points-table tbody tr:visible button').evaluateAll(nodes=>nodes.map(n=>n.dataset.pointId));
   check('canonical-first-five',JSON.stringify(ids)===JSON.stringify(chart.points.slice(0,5).map(p=>p.id)),ids);
   check('wheel-keeps-all-points',await page.locator('#chart-wheel svg [data-kind="point"]').count()===chart.points.length);
   const reveal=page.locator('#points-show-all'),before=requests.length;
   await reveal.focus();await reveal.press('Enter');
   check('keyboard-reveal-all',await count()===chart.points.length,await count());
   check('reveal-retains-focus',await reveal.evaluate(n=>document.activeElement===n));
   check('aria-expanded',await reveal.getAttribute('aria-expanded')==='true');
   check('other-tables-independent',await page.locator('#houses-table tbody tr:visible').count()===5&&await page.locator('#aspects-table tbody tr:visible').count()===5);
   const late=chart.points.at(-1).id,point=page.locator('#points-table [data-point-id="'+late+'"]');
   await point.focus();await point.press('Enter');
   check('late-planet-selection-no-focus-move',await point.evaluate(n=>document.activeElement===n)&&await point.getAttribute('aria-pressed')==='true');
   await point.press('Enter');await reveal.focus();await reveal.press('Space');
   check('keyboard-collapse-five',await count()===5,await count());
   await page.locator('#aspects-show-all').click();
   const index=chart.aspects.findIndex(a=>a.from===late||a.to===late);check('positive-late-endpoint-fixture',index>=0,index);
   const chosen=page.locator('#aspects-table tbody tr').nth(index).locator('button');await chosen.click();
   const ends=new Set([chart.aspects[index].from,chart.aspects[index].to]);
   const actual=await page.locator('#points-table tbody tr:visible button').evaluateAll(nodes=>nodes.map(n=>n.dataset.pointId));
   check('aspect-bypasses-five-limit',JSON.stringify(actual)===JSON.stringify(chart.points.filter(p=>ends.has(p.id)).map(p=>p.id)),actual);
   check('aspect-hides-points-disclosure',!await reveal.isVisible());
   await page.locator('#aspect-close').click();check('exit-restores-collapsed',await count()===5,await count());
   check('interaction-no-HTTP',requests.length===before,requests);
   await reveal.click();current.chart.chart_identity+='-automatic';current.state_version+=1;
   await page.evaluate(()=>window.dispatchEvent(new Event('online')));
   await page.waitForFunction(identity=>document.querySelector('[data-chart-identity]')?.dataset.chartIdentity===identity,current.chart.chart_identity);
   check('automatic-update-preserves-expansion',await count()===chart.points.length,await count());
   check('positive-current-request',JSON.stringify(requests.slice(before))===JSON.stringify(['POST /session/bootstrap','GET /charts/current']),requests);
   await reveal.click();await page.locator('#facts-points').scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(out,vendor+'-'+width+'.png')});
   check('no-page-errors',errors.length===0,errors);
  }catch(error){item.error=String(error)}
  item.passed=!item.error&&checks.every(c=>c.pass);console.log(item.passed?'PASS':'FAIL',vendor,width,item.error||'');
  fs.writeFileSync(path.join(out,'actual.json'),JSON.stringify(record,null,2)+'\n');await page.close();
 }}finally{await browser.close()}
 }
 if(record.cases.some(c=>!c.passed))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>server?.close());