// Production controller/validator/leaf, real connected SVG; no mock of the subject.
import {createDrawingController,validatePassiveSvg} from "/ui/result_controller.mjs";
import {createWheelRenderer} from "/ui/wheel_svg.mjs";
const NS="http://www.w3.org/2000/svg",$=id=>document.getElementById(id);
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return{promise,resolve,reject}};
const svg=(surface,label)=>{
 const root=document.createElementNS(NS,"svg");for(const[k,v]of Object.entries({width:328,height:80,viewBox:"0 0 328 80",role:"img"}))root.setAttribute(k,v);
 const text=document.createElementNS(NS,"text");text.setAttribute("x",10);text.setAttribute("y",30);text.setAttribute("font-size",16);text.textContent=label;root.append(text);surface.append(root);return root;
};
window.runBoundary=async chart=>{
 const controls=[],trace=[],fatal=[];
 const check=(id,actual,expected)=>{const pass=JSON.stringify(actual)===JSON.stringify(expected);controls.push({id,actual,expected,pass});if(!pass)throw Error(id+": "+JSON.stringify(actual))};
 let factory=surface=>({update(s,p){p(svg(surface,s.chart.chart_identity))},dispose(){}});
 const dynamicFactory=surface=>factory(surface);
 const controller=createDrawingController({document,imageHost:$("image"),measureHost:$("measure"),factory:dynamicFactory,
  onEvent:e=>trace.push(e),onUnavailable:e=>{$("warning").textContent=e?.kind??""},onFatal:e=>fatal.push(String(e))});
 let seq=0;
 const present=(id,f,replace=true)=>{if(f)factory=f;return controller.present(()=>{$("html").textContent="HTML "+id;return{chart:{...chart,chart_identity:id},width:328,fontRevision:0,acceptanceSeq:++seq,selection:null}},{replace,rendererFactory:dynamicFactory})};
 const slow=deferred();let rootA,sinkA,surfaceA,disposals=0;
 await Promise.resolve();const a=present("A",surface=>({update(s,p){surfaceA=surface;rootA=svg(surface,"A");sinkA=p;p(rootA);return slow.promise},dispose(){disposals++;throw Error("dispose-controlled")}}));
 check("copy-distinct",$("image").firstElementChild===rootA,false);
 rootA.firstElementChild.textContent="mutation";check("current-original-cannot-mutate-copy",$("image").textContent,"A");
 const start=trace.length;await present("B",surface=>({update(s,p){p(svg(surface,"B"))},dispose(){disposals++}}));
 check("order-revoke-remove-html-dispose-draw",trace.slice(start).filter(e=>["revoke","remove","html","dispose-fault","draw"].includes(e.event)).map(e=>e.event),["revoke","remove","html","dispose-fault","draw"]);
 check("new-HTML-survives-dispose-fault",$("html").textContent,"HTML B");check("old-surface-detached",surfaceA.isConnected,false);
 check("late-before-settlement",sinkA(rootA),false);slow.resolve();await a;check("late-after-settlement",sinkA(rootA),false);check("late-keeps-B",$("image").textContent,"B");
 let original,sink,liveSurface;
 await present("current",surface=>({update(s,p){liveSurface=surface;sink=p;original=svg(surface,"current");p(original)},dispose(){}}));
 check("surface-alive-after-settlement",liveSurface.isConnected,true);original.firstElementChild.textContent="font callback";
 check("current-late-publish",sink(original),true);check("current-late-content",$("image").textContent,"font callback");
 const invalid=deferred();let staleSame,oldSame;
 const same={update(s,p,surface){if(s.chart.chart_identity==="same-A"){oldSame=svg(surface,"same-A");staleSame=p;return invalid.promise}p(svg(surface,"same-B"))},dispose(){throw Error("same instance must not dispose for revision")}};
 const sameA=present("same-A",()=>same);await present("same-B",null,false);
 check("same-instance-old-revision",staleSame(oldSame),false);invalid.reject(Error("old same"));await sameA;check("stale-rejection-keeps-new",$("image").textContent,"same-B");
 for(const [id,f]of [["factory",()=>{throw Error("factory")}],["sync",()=>({update(){throw Error("sync")},dispose(){}})],["async",()=>({update(){return Promise.reject(Error("async"))},dispose(){}})],["invalid",()=>3]]){
  await present(id,f);check("local-"+id,[$("html").textContent,$("image").childElementCount,$("warning").textContent],["HTML "+id,0,"svg_unavailable"]);
 }
 let failedSink,failedRoot;await present("reject-after-publish",surface=>({update(s,p){failedSink=p;failedRoot=svg(surface,"bad");p(failedRoot);return Promise.reject(Error("after"))},dispose(){}}));
 check("rejection-revokes-lease",failedSink(failedRoot),false);
 for(const[id,mutate]of [["event",r=>r.setAttribute("onclick","alert(1)")],["positioning",r=>r.style.position="fixed"],["external-href",r=>r.setAttribute("href","https://example.invalid")],["external-paint",r=>r.setAttribute("fill","url(#outside)")],["id",r=>r.setAttribute("id","outside")],["infinite",r=>r.setAttribute("width","Infinity")],["font-scale",r=>r.setAttribute("transform","scale(.5)")],["bad-font",r=>r.firstElementChild.setAttribute("font-size",15.99)],["active-tag",r=>r.append(document.createElementNS(NS,"foreignObject"))]]){
  await present("unsafe-"+id,surface=>({update(s,p){const r=svg(surface,id);mutate(r);p(r)},dispose(){}}));
  check("whitelist-"+id,[$("image").childElementCount,$("warning").textContent],[0,"svg_unavailable"]);
 }
 const source={...chart,chart_identity:"immutable"};await controller.present(()=>({chart:source,width:328,selection:null,acceptanceSeq:++seq}),{replace:true,rendererFactory:surface=>({update(s,p){try{s.chart.points[0].longitude=999}catch{}p(svg(surface,String(s.chart.points[0].longitude)))},dispose(){}})});
 check("deep-frozen-source",source.points[0].longitude,chart.points[0].longitude);
 let result;await present("reentrant",surface=>({update(s,p){const r=svg(surface,"retired"),clone=r.cloneNode.bind(r);r.cloneNode=()=>{present("new-during-clone",s=>({update(_,publish){publish(svg(s,"new"))},dispose(){}}));return clone(true)};result=p(r)},dispose(){}}));
 check("recheck-after-reentrant-clone",result,false);check("reentrant-new-kept",$("image").textContent,"new");
 await controller.present(()=>{ $("html").textContent="HTML real";return{chart,width:328,selection:null,fontRevision:0,acceptanceSeq:++seq}},{replace:true,rendererFactory:createWheelRenderer});
 check("real-positive-SVG",$("image").querySelectorAll('[data-kind="point"]').length,chart.points.length);
 $("html").focus();let rootReal=$("image").firstElementChild;
 check("real-copy-no-focus-targets",rootReal.querySelectorAll("[tabindex],[onclick],[role=button]").length,0);
 const html=$("html");await controller.present(()=>({chart,width:328,selection:{kind:"point",id:"moon"},fontRevision:0,acceptanceSeq:seq}),{rendererFactory:createWheelRenderer});
 check("real-keeps-live-HTML-focus",document.activeElement===html&&html.isConnected,true);
 // Unexpected host-owner errors must remain fatal, not become a misleading leaf error.
 const install=$("image").replaceChildren.bind($("image"));let installations=0,thrown=false;
 $("image").replaceChildren=(...nodes)=>{if(++installations===2){thrown=true;throw Error("host-owner-fault")}return install(...nodes)};
 await controller.present(()=>({chart,width:328,selection:null,acceptanceSeq:++seq}),{rendererFactory:surface=>({async update(s,p){await Promise.resolve();p(svg(surface,"fatal"))},dispose(){}})});
 $("image").replaceChildren=install;check("controller-error-partition",[thrown,fatal.some(s=>s.includes("host-owner-fault"))],[true,true]);
 await present("alternate-after-fault",surface=>({update(s,p){p(svg(surface,"alternate"))},dispose(){disposals++}}));
 check("independent-positive-after-fault",$("image").textContent,"alternate");
 // A delayed rethrow of an owner failure from retired A must not clear accepted B.
 const holdFault=deferred(),caughtFault=deferred(),fatalBefore=fatal.length;let ownerCalls=0;
 $("image").replaceChildren=(...nodes)=>{if(++ownerCalls===2)throw Error("retired-owner-fault");return install(...nodes)};
 const retiredFault=present("late-owner-A",surface=>({async update(s,p){
  try{p(svg(surface,"A-fatal"))}catch(error){caughtFault.resolve();await holdFault.promise;throw error}
 },dispose(){}}));
 await caughtFault.promise;$("image").replaceChildren=install;
 await present("after-owner-B",surface=>({update(s,p){p(svg(surface,"B-positive"))},dispose(){}}));
 holdFault.resolve();await retiredFault;
 check("retired-owner-failure-keeps-B",[$("html").textContent,$("image").textContent,fatal.length-fatalBefore],["HTML after-owner-B","B-positive",0]);
 controller.close();controller.close();check("idempotent-close",$("image").childElementCount,0);
 return{controls,trace,fatal};
};
window.boundaryReady=true;
