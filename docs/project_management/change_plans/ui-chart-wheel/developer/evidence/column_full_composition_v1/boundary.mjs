import {compose,el} from './composition.mjs';
const $=id=>document.getElementById(id),trace=[],controls=[];let current=null,instance=0,revision=0,epoch=0;
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject}};
const check=(id,actual,expected)=>{const pass=JSON.stringify(actual)===JSON.stringify(expected);controls.push({id,actual,expected,pass});if(!pass)throw Error(id+': '+JSON.stringify(actual))};
const validSvg=root=>{const tags=new Set(['svg','g','circle','path','line','rect','text','title','desc','polygon','polyline','ellipse']);if(root.localName!=='svg')throw Error('not-svg');for(const n of [root,...root.querySelectorAll('*')]){if(!tags.has(n.localName))throw Error('active-node');for(const a of n.attributes){if(/^on/i.test(a.name)||['href','tabindex','autofocus','class'].includes(a.localName)||/url\s*\(/i.test(a.value)||a.name==='role'&&a.value!=='img')throw Error('active-attribute');if(a.name==='style')for(const property of Array.from(n.style)){if(!['font-family','overflow','overflow-x','overflow-y','display'].includes(property))throw Error('layout-style:'+property);if(property.startsWith('overflow')&&n.style[property]!=='hidden'||property==='display'&&n.style[property]!=='block')throw Error('layout-style-value')}}}};
const deepFreeze=x=>{if(x&&typeof x==='object'){Object.freeze(x);for(const v of Object.values(x))deepFreeze(v)}return x};
function safeError(e){return {kind:'svg_unavailable',reason:e.message}}
async function accept(identity,factory,{reuse=false,snapshot={}}={}){
 const prior=current;if(prior){prior.valid=false;prior.surface?.remove()}trace.push({event:'revoke',identity,revision:prior?.revision});$('image').replaceChildren();trace.push({event:'remove',identity});
 $('html').textContent='HTML '+identity;trace.push({event:'html',identity});$('warning').textContent='';
 if(prior&&!reuse&&!prior.disposed){prior.disposed=true;try{prior.leaf?.dispose();trace.push({event:'dispose',identity})}catch(e){trace.push({event:'dispose-fault',identity,html:$('html').textContent})}}
 const lease={valid:true,instance:reuse?prior.instance:++instance,revision:++revision,epoch:++epoch,identity,disposed:false};current=lease;
 const surface=document.createElement('div');$('measure').append(surface);lease.surface=surface;
 const publish=root=>{if(!lease.valid||current!==lease){trace.push({event:'stale-refused',identity});return false}validSvg(root);const copy=root.cloneNode(true);if(!lease.valid||current!==lease)return false;$('image').replaceChildren(copy);trace.push({event:'install-copy',identity});return true};lease.publish=publish;
 try{lease.leaf=reuse?prior.leaf:factory(surface);trace.push({event:'draw',identity});await lease.leaf.update(deepFreeze(structuredClone({identity,...snapshot})),publish,surface);return {kind:lease.valid&&current===lease?'rendered':'revoked'}}
 catch(e){if(lease.valid&&current===lease){lease.valid=false;$('image').replaceChildren();$('warning').textContent='Колесо недоступно '+identity;trace.push({event:'local-fault',identity,html:$('html').textContent});return safeError(e)}trace.push({event:'stale-rejection',identity});return {kind:'revoked'}}
 finally{if(!lease.valid||current!==lease)surface.remove()}
}
function passive(surface,label){const root=el('svg',{width:200,height:50,role:'img','aria-label':label});root.append(el('text',{x:10,y:30},label));surface.append(root);return root}
window.runBoundary=async()=>{
 const old=deferred();let rootA,sinkA,disposeCount=0;
 const pa=accept('A',surface=>({update(_,sink){rootA=passive(surface,'A');sinkA=sink;sink(rootA);return old.promise},dispose(){disposeCount++;throw Error('dispose-controlled')}}));
 check('COPY-installed-is-distinct',$('image').firstElementChild===rootA,false);rootA.firstElementChild.textContent='mutated-own-A';check('COPY-current-original-mutation',$('image').textContent,'A');
 await accept('B',surface=>({update(_,sink){sink(passive(surface,'B'))},dispose(){disposeCount++}}));
 check('ORDER-revoke-remove-HTML-dispose-draw',trace.filter(t=>t.identity==='B').map(t=>t.event).slice(0,5),['revoke','remove','html','dispose-fault','draw']);
 check('DISPOSE-fault-sees-new-HTML',trace.find(t=>t.event==='dispose-fault').html,'HTML B');
 rootA.firstElementChild.textContent='late-before-settlement';check('STALE-before-settlement',sinkA(rootA),false);check('STALE-original-reference-keeps-B',$('image').textContent,'B');old.resolve();await pa;
 check('STALE-after-settlement',sinkA(rootA),false);
 const late=deferred();let oldSink,oldRoot;
 const reused={update(s,sink,surface){if(s.identity==='C'){oldSink=sink;oldRoot=passive(surface,'C');return late.promise}sink(passive(surface,s.identity))},dispose(){}};
 const pc=accept('C',()=>reused);const priorInstance=current.instance;await accept('D',()=>{}, {reuse:true});
 check('REVISION-same-instance',current.instance,priorInstance);check('REVISION-old-revision-refused',oldSink(oldRoot),false);late.reject(Error('late-C'));await pc;
 check('STALE-rejection-locality',[$('html').textContent,$('image').textContent,$('warning').textContent],['HTML D','D','']);
 for(const [id,factory]of [['factory',()=>{throw Error('factory')}],['sync',()=>({update(){throw Error('sync')},dispose(){}})],['async',()=>({update(){return Promise.reject(Error('async'))},dispose(){}})]]){const r=await accept(id,factory);check('FAULT-'+id,[r.kind,$('html').textContent,$('image').childElementCount],['svg_unavailable','HTML '+id,0])}
 let activeSink,activeRoot;await accept('failed-later',surface=>({update(_,sink){activeSink=sink;activeRoot=passive(surface,'bad');sink(activeRoot);return Promise.reject(Error('then-failed'))},dispose(){}}));check('FAULT-revokes-current-authority',activeSink(activeRoot),false);
 await accept('unsafe',surface=>({update(_,sink){const r=passive(surface,'unsafe');r.setAttribute('onclick','alert(1)');sink(r)},dispose(){}}));check('VALIDATION-event-attribute-local',[$('image').childElementCount,$('html').textContent],[0,'HTML unsafe']);
 await accept('unsafe-layout',surface=>({update(_,sink){const r=passive(surface,'unsafe');r.style.position='fixed';sink(r)},dispose(){}}));check('VALIDATION-cannot-overlay-HTML',[$('image').childElementCount,$('html').textContent],[0,'HTML unsafe-layout']);
 const immutableInput={chart:{points:[{id:'sun',longitude:1}]}};await accept('IMMUTABLE',surface=>({update(snapshot,sink){try{snapshot.chart.points[0].longitude=999}catch{}sink(passive(surface,String(snapshot.chart.points[0].longitude)))},dispose(){}}),{snapshot:immutableInput});check('SNAPSHOT-deep-immutable-copy',[immutableInput.chart.points[0].longitude,$('image').textContent],[1,'1']);
 let lifetimeSurface,lifetimeSink,lifetimeRoot;await accept('LIFETIME',surface=>({update(_,sink){lifetimeSurface=surface;lifetimeSink=sink;lifetimeRoot=passive(surface,'measurement alive');sink(lifetimeRoot)},dispose(){}}));check('SURFACE-kept-after-success',lifetimeSurface.isConnected,true);lifetimeRoot.firstElementChild.textContent='current font callback';check('CURRENT-publish-after-settlement',[lifetimeSink(lifetimeRoot),$('image').textContent],[true,'current font callback']);
 let reentrantResult;await accept('REENTRANT',surface=>({update(_,sink){const r=passive(surface,'retired during clone'),clone=r.cloneNode.bind(r);r.cloneNode=()=>{accept('REENTRANT-B',s=>({update(_,publish){publish(passive(s,'new revision'))},dispose(){}}));return clone(true)};reentrantResult=sink(r)},dispose(){}}));check('GUARD-rechecked-after-clone',[reentrantResult,$('image').textContent],[false,'new revision']);check('SURFACE-retired-is-detached',lifetimeSurface.isConnected,false);
 const data=await fetch('./data.json').then(r=>r.json());let realOriginal;
 await accept('REAL-F1',surface=>({async update(_,sink){const r=await compose(surface,data.F1,{width:328});realOriginal=r.svg;sink(r.svg)},dispose(){}}));
 check('REAL-SVG-16-source-points',$('image').querySelectorAll('[data-kind=point]').length,16);check('REAL-SVG-no-interactive-targets',$('image').querySelectorAll('[tabindex],[role=button],[onclick]').length,0);
 const liveBefore=$('image').innerHTML;realOriginal.replaceChildren(el('text',{},'late root corruption'));check('REAL-SVG-copy-isolation',$('image').innerHTML,liveBefore);
 const button=$('point');button.focus();const priorButton=button;await accept('REAL-B',surface=>({async update(_,sink){const r=await compose(surface,data['F3-max'],{width:328});sink(r.svg)},dispose(){}}));check('HTML-focus-live-retained',[document.activeElement===priorButton,priorButton.isConnected],[true,true]);
 // Final disposal revokes before any leaf callback and is idempotent at the controller seam.
 const final=current;let leafDisposals=0;final.leaf.dispose=()=>{leafDisposals++};function close(){if(!current)return;const l=current;l.valid=false;current=null;l.surface?.remove();$('image').replaceChildren();if(!l.disposed){l.disposed=true;try{l.leaf?.dispose()}catch{}}}close();close();check('DISPOSE-controller-idempotent',leafDisposals,1);check('DISPOSE-revoked-final-sink',final.publish(realOriginal),false);
 // Positive independent alternative after all failures and dispose.
 await accept('ALTERNATE',surface=>({update(_,sink){sink(passive(surface,'Alternative renderer'))},dispose(){}}));check('ALTERNATE-recovers',[$('html').textContent,$('image').textContent],['HTML ALTERNATE','Alternative renderer']);
 return {controls,trace,limits:'isolated real SVG clone seam; no production controller/session; same-origin contract not security boundary',disposeCount};
};window.boundaryDebug=()=>({trace,controls,html:$('html').textContent,warning:$('warning').textContent});window.boundaryReady=true;
