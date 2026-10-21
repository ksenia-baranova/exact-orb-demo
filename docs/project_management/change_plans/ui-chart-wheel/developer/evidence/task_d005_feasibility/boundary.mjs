// Research contract: renderer holds no live DOM; immutable descriptions cross a guarded sink.
const $=id=>document.getElementById(id),trace=[],deferred=()=>{let resolve,reject;const promise=new Promise((r,j)=>{resolve=r;reject=j});return {promise,resolve,reject}};
let epoch=0,instance=0,current,selected=null;const controls=[];
function record(id,actual,expected){controls.push({id,actual,expected,pass:JSON.stringify(actual)===JSON.stringify(expected)});if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error(id)}
class Boundary{
 async accept(identity,factory,{reuse=false}={}){
  const prior=current;if(prior)prior.valid=false;trace.push({event:'revoke',identity,prior:prior?.identity});
  $('image').replaceChildren();trace.push({event:'remove-imagery',identity});
  $('html').textContent='HTML '+identity;trace.push({event:'html-published',identity,html:$('html').textContent});
  $('warning').textContent='';
  if(prior&&!reuse&&!prior.disposed){prior.disposed=true;try{prior.leaf?.dispose?.();trace.push({event:'dispose',identity:prior.identity})}catch(error){trace.push({event:'dispose-fault',identity:prior.identity,error:error.message,html:$('html').textContent})}}
  const lease={epoch:++epoch,instance:reuse?prior.instance:++instance,identity,valid:true,disposed:false};current=lease;
  const sink=frame=>{
   const copy=structuredClone(frame);if(!lease.valid||current!==lease){trace.push({event:'stale-write-refused',identity,epoch:lease.epoch});return false}
   const b=document.createElement('button');b.id='live-frame';b.textContent=copy.label;b.onclick=()=>{if(!lease.valid||current!==lease){trace.push({event:'stale-intent-refused'});return}selected=copy.key;trace.push({event:'native-intent',identity,key:copy.key})};$('image').replaceChildren(b);trace.push({event:'frame-published',identity,epoch:lease.epoch});return true;
  };
  lease.sink=sink;
  try{lease.leaf=reuse?prior.leaf:factory();trace.push({event:'draw-entered',identity});await lease.leaf.update(Object.freeze({identity}),sink);if(lease.valid&&current===lease)trace.push({event:'rendered',identity})}
  catch(error){if(lease.valid&&current===lease){$('image').replaceChildren();$('warning').textContent='Колесо недоступно: '+identity;trace.push({event:'local-svg-unavailable',identity,error:error.message,html:$('html').textContent})}else trace.push({event:'stale-rejection-diagnostic',identity,error:error.message})}
 }
}
const boundary=new Boundary();
async function run(){
 const old=deferred();let oldSink;const pa=boundary.accept('A',()=>({update(_,sink){oldSink=sink;sink({label:'A',key:'sun'});return old.promise},dispose(){throw new Error('controlled dispose throw')}}));
 await boundary.accept('B',()=>({update(_,sink){sink({label:'B',key:'moon'})},dispose(){}}));
 record('R001-01-HTML-before-dispose-fault',trace.find(e=>e.event==='dispose-fault').html,'HTML B');
 record('R001-02-write-before-old-settlement',oldSink({label:'stale A before settle',key:'sun'}),false);
 record('R001-02-live-B-survives',$('image').textContent,'B');old.resolve();await pa;
 record('R001-02-write-after-old-settlement',oldSink({label:'stale A after settle',key:'sun'}),false);
 const order=trace.filter(e=>e.identity==='B').map(e=>e.event);record('R001-01-order',order.slice(0,4),['revoke','remove-imagery','html-published','draw-entered']);
 const late=deferred();let revisionSink;const reused={update(s,sink){if(s.identity==='C'){revisionSink=sink;return late.promise}sink({label:s.identity,key:'venus'})},dispose(){}};
 const pc=boundary.accept('C',()=>reused);const oldInstance=current.instance;await boundary.accept('D',()=>{}, {reuse:true});
 record('R001-02-same-instance-new-revision',current.instance,oldInstance);record('R001-02-old-revision-write',revisionSink({label:'late C',key:'sun'}),false);
 late.reject(new Error('controlled stale reject'));await pc;record('R001-03-stale-rejection-keeps-D',[$('html').textContent,$('image').textContent,$('warning').textContent],['HTML D','D','']);
 await boundary.accept('E-sync',()=>({update(){throw new Error('controlled sync update')},dispose(){}}));record('R001-03-sync-local',[$('html').textContent,$('image').childElementCount,$('warning').textContent],['HTML E-sync',0,'Колесо недоступно: E-sync']);
 await boundary.accept('F-async',()=>({update(){return Promise.reject(new Error('controlled async reject'))},dispose(){}}));record('R001-03-async-local',[$('html').textContent,$('image').childElementCount,$('warning').textContent],['HTML F-async',0,'Колесо недоступно: F-async']);
 await boundary.accept('G-factory',()=>{throw new Error('controlled factory throw')});record('R001-03-factory-local',[$('html').textContent,$('warning').textContent],['HTML G-factory','Колесо недоступно: G-factory']);
 await boundary.accept('H-alternate',()=>({update(_,sink){sink({label:'H alternative',key:'mars'})},dispose(){}}));
 record('alternate-positive',[$('html').textContent,$('image').textContent],['HTML H-alternate','H alternative']);
 return {controls,trace,selected,html:$('html').textContent};
}
window.boundary={ready:true,run,trace,controls,snapshot:()=>({html:$('html').textContent,image:$('image').textContent,warning:$('warning').textContent,selected})};
