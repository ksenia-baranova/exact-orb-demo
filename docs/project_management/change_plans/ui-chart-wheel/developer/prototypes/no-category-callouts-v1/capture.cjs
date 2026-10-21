const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const{chromium}=require('C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const B=__dirname,out=path.join(B,'render01');if(fs.existsSync(out))throw Error('preserve existing preview render');fs.mkdirSync(out);
let browser,server;const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function main(){
 server=http.createServer((req,res)=>{const file=path.resolve(B,'.'+decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(B+path.sep)){res.writeHead(403).end();return}try{res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':'application/json; charset=utf-8');res.end(fs.readFileSync(file))}catch{res.writeHead(404).end()}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});const context=await browser.newContext({viewport:{width:360,height:900},deviceScaleFactor:2});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));const records=[];
 for(const[fixture,variant]of [['F1','inside'],['F3-max','inside'],['F3-max','callouts']]){
  await page.goto(`http://127.0.0.1:${server.address().port}/prototype.html?variant=${variant}&fixture=${fixture}`);await page.waitForFunction(()=>window.previewReady);await page.evaluate(()=>document.fonts.ready);const state=await page.evaluate(()=>previewState());
  if(state.removedText||!state.sourceUnchanged||state.overflow||state.svgTargets||state.points.length!==16||new Set(state.points).size!==16||state.R!==state.expectedR||state.conjunctions!==state.expectedConjunctions||errors.length)throw Error('preview check '+JSON.stringify({state,errors}));
  if(state.nameBounds.some(b=>b.x+b.width>107))throw Error('column label exceeds allocated width');
  const filename=`${fixture}-${variant}.png`;await page.locator('.prototype').screenshot({path:path.join(out,filename)});records.push({fixture,variant,state,screenshot:filename,sha256:sha(path.join(out,filename))});
  console.log('PREVIEW_OK',fixture,variant,'points',state.points.length,'R',state.R,'conjunctions',state.conjunctions,'categoryText',state.removedText);
 }
 const result={author:'Codex / Developer',purpose:'Owner visual revision, no full geometry feasibility claim',browser:browser.version(),viewport:[360,900],DPR:2,htmlSHA256:sha(path.join(B,'prototype.html')),dataSHA256:sha(path.join(B,'data.json')),records,checks:'content/DTO/IDs/R/conjunctions/removed words/no SVG targets/no whole-page overflow; not annulus/gap/minimality/production acceptance'};fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(result,null,2)+'\n');console.log('PREVIEWS_COMPLETE 3');
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close();server?.close()});
