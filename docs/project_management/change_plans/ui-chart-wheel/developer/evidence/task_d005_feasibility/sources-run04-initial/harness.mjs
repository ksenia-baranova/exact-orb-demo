// Isolated candidate only. No production imports, network/API, S1 execution or placement.
const ns='http://www.w3.org/2000/svg',$=id=>document.getElementById(id),trace=[],calls=[];
const tokenMap=new WeakMap();let nextToken=0,model,svg,selected=null,all=false,housesAll=false,sourceBefore;
const points=new Map(),rows=new Map(),graphic=new Map();
for(const proto of [HTMLElement.prototype,SVGElement.prototype]){const original=proto.focus;if(original)proto.focus=function(...a){calls.push({kind:'focus',id:this.id});return original.apply(this,a)}}
const scrollOriginal=window.scrollTo;window.scrollTo=function(...a){calls.push({kind:'scrollTo',a});return scrollOriginal.apply(this,a)};
function token(n){if(!n)return null;if(!tokenMap.has(n))tokenMap.set(n,++nextToken);return tokenMap.get(n)}
const canonical=g=>g.kind==='point'?g.key:JSON.stringify([...JSON.parse(g.key).slice(0,2).sort(),JSON.parse(g.key)[2]]);
const aspect=a=>JSON.stringify(...[[...[a.from,a.to].sort(),a.type]]);
function n(tag,attrs={},text){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e}
function bounds(r){return {left:r.left??r.x,top:r.top??r.y,right:r.right??r.x+r.width,bottom:r.bottom??r.y+r.height,width:r.width,height:r.height}}
function snap(){const e=document.activeElement,r=e?.getBoundingClientRect();return {selected,active:e?.id,key:e?.dataset?.canonical,token:token(e),connected:e?.isConnected,visible:!!r&&r.width>0&&r.height>0&&!e.closest('[hidden]'),calls:calls.length,scroll:[scrollX,scrollY],all,housesAll,draft:$('draft').value}}
function activate(key,event){const before=snap();selected=selected===key?null:key;if(model.chart.points.some(p=>p.id===key)&&before.selected===key)all=false;refresh();trace.push({kind:'activate',key,eventTarget:event?.target?.id,eventType:event?.type,client:event?[event.clientX,event.clientY]:null,path:event?.composedPath().filter(x=>x.id).map(x=>x.id),before,after:snap()})}
function refresh(){
 for(const[key,e]of graphic)e.classList.toggle('selected',selected===e.dataset.canonical);
 let visible=model.chart.aspects.map((a,i)=>i);if(selected){const p=model.chart.points.some(p=>p.id===selected);visible=visible.filter(i=>p?[model.chart.aspects[i].from,model.chart.aspects[i].to].includes(selected):aspect(model.chart.aspects[i])===selected)}else if(!all)visible=visible.slice(0,5);
 for(const[i,e]of rows)e.hidden=!visible.includes(i);
 $('reveal').hidden=!!selected||all||model.chart.aspects.length<=5;$('houses').textContent=`${model.chart.houses?.length??0} домов; раскрытие=${housesAll}`;
}
function html(){
 for(const p of model.chart.points){let e=points.get(p.id);if(!e){e=document.createElement('button');e.id='html-'+p.id;e.dataset.canonical=p.id;e.onclick=ev=>activate(p.id,ev);points.set(p.id,e);$('points').append(e)}e.textContent=`${p.id}: ${p.degree}°${p.minute} ${p.sign} ${p.retrograde?'R':''}`}
 for(const[id,e]of points)if(!model.chart.points.some(p=>p.id===id)){e.remove();points.delete(id)}
 model.chart.aspects.forEach((a,i)=>{let e=rows.get(i);if(!e){e=document.createElement('button');e.id='row-'+i;rows.set(i,e);$('aspects').append(e)}e.dataset.canonical=aspect(a);e.textContent=`${a.from} → ${a.to}: ${a.type} / ${a.category} / ${a.orb}`;e.onclick=ev=>activate(aspect(a),ev)});
 for(const[i,e]of rows)if(i>=model.chart.aspects.length){e.remove();rows.delete(i)}
 refresh();
}
function draw(data,{retain=false}={}){
 model=structuredClone(data);sourceBefore=JSON.stringify(model.chart);if(!retain){selected=null;all=false;housesAll=false;graphic.clear();$('mount').replaceChildren();svg=n('svg',{id:'wheel',role:'group','aria-label':'Исследовательское колесо'});$('mount').append(svg)}
 const S=model.size,C=S/2;svg.setAttribute('width',S);svg.setAttribute('height',S);svg.setAttribute('viewBox',`0 0 ${S} ${S}`);
 svg.querySelectorAll('.decoration').forEach(x=>x.remove());
 for(const r of [.49,.40,.29,.22,.11])svg.insertBefore(n('circle',{class:'decoration',cx:C,cy:C,r:S*r,fill:'none',stroke:'#bccbd9','pointer-events':'none'}),svg.firstChild);
 const xy=(lng,r)=>{const a=(lng-model.origin)*Math.PI/180;return [C-r*Math.cos(a),C+r*Math.sin(a)]};
 for(const h of model.chart.houses??[]){const p=xy(h.cusp_longitude,S*.27),q=xy(h.cusp_longitude,S*.49);svg.insertBefore(n('line',{class:'decoration',x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#d5dce3','pointer-events':'none'}),svg.firstChild)}
 const ep=new Map([...model.chart.points.map(p=>[p.id,p.longitude]),...Object.entries(model.chart.angles??{}).map(([id,p])=>[id,p.longitude])]);
 for(const a of model.chart.aspects.filter(a=>a.category!=='background'&&a.type!=='conjunction')){const p=xy(ep.get(a.from),S*.27),q=xy(ep.get(a.to),S*.27);svg.insertBefore(n('line',{class:'decoration',x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#32765e','pointer-events':'none'}),svg.firstChild)}
 for(let i=0;i<model.groups.length;i++){
  const g=model.groups[i];let e=graphic.get(g.key);
  if(!e){e=n('g',{id:'target-'+i});e.dataset.sourceKey=g.key;if(g.kind!=='angle'){e.setAttribute('role','button');e.setAttribute('tabindex','0');e.setAttribute('aria-label',g.key);e.dataset.target=g.key;e.dataset.canonical=canonical(g);e.onclick=ev=>activate(e.dataset.canonical,ev);e.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();activate(e.dataset.canonical,ev)}}}graphic.set(g.key,e);svg.append(e)}
  e.setAttribute('transform',`translate(${g.P[0]} ${g.P[1]})`);e.replaceChildren();
  if(g.kind!=='angle'){
   e.append(n('rect',{x:g.Q[0]-g.P[0],y:g.Q[1]-g.P[1],width:44,height:44,fill:'transparent','pointer-events':'all'}));
   g.components.forEach(b=>e.append(n('rect',{x:b[0],y:b[1],width:b[2]-b[0],height:b[3]-b[1],fill:'transparent','pointer-events':'all'})));
   g.metrics.forEach((m,k)=>e.append(n('text',{id:`text-${i}-${k}`,'data-measure':'true',class:k===0?'glyph':'aux',x:k===0?-8:8,y:k===0?6:10,'font-size':m.size},m.text)));
   const inks=g.metrics.map(m=>m.ink),l=Math.min(...inks.map(b=>b.left))-3,t=Math.min(...inks.map(b=>b.top))-3,r=Math.max(...inks.map(b=>b.right))+3,b=Math.max(...inks.map(b=>b.bottom))+3;
   e.append(n('rect',{class:'focus',x:l+1,y:t+1,width:r-l-2,height:b-t-2}));
  }else e.append(n('text',{id:'text-'+i,'data-measure':'true',x:0,y:0,'font-size':12},g.key.slice(6).toUpperCase()));
  svg.insertBefore(n('circle',{class:'decoration',cx:g.A[0],cy:g.A[1],r:1.5,fill:'#216b94','data-anchor':g.key,'pointer-events':'none'}),svg.firstChild);
  if(g.leader)svg.insertBefore(n('line',{class:'decoration',x1:g.A[0],y1:g.A[1],x2:g.P[0],y2:g.P[1],stroke:'#566677','pointer-events':'none'}),svg.firstChild);
 }
 for(const[key,e]of graphic)if(!model.groups.some(g=>g.key===key)){e.remove();graphic.delete(key)}
 $('summary').textContent=`${model.fixture} / ${model.variant} / frame ${S} / ${model.chart.chart_identity}`;html();return snap();
}
function measure(){const M=svg.getScreenCTM(),svgRect=svg.getBoundingClientRect();return {frame:model.size,matrix:[M.a,M.b,M.c,M.d,M.e,M.f],svgRect:bounds(svgRect),zoom:visualViewport.scale,dpr:devicePixelRatio,chartUnchanged:sourceBefore===JSON.stringify(model.chart),text:[...svg.querySelectorAll('[data-measure]')].map(e=>{const s=getComputedStyle(e),c=document.createElement('canvas').getContext('2d');c.font=`${s.fontSize} ${s.fontFamily}`;const m=c.measureText(e.textContent),x=+e.getAttribute('x'),y=+e.getAttribute('y');return {id:e.id,text:e.textContent,font:s.fontFamily,size:parseFloat(s.fontSize),effectiveEm:Math.hypot(M.c*parseFloat(s.fontSize),M.d*parseFloat(s.fontSize)),ink:{left:x-m.actualBoundingBoxLeft,top:y-m.actualBoundingBoxAscent,right:x+m.actualBoundingBoxRight,bottom:y+m.actualBoundingBoxDescent},bbox:bounds(e.getBBox()),rect:bounds(e.getBoundingClientRect())}}),anchors:model.groups.map(g=>{const a=[...svg.querySelectorAll('[data-anchor]')].find(e=>e.dataset.anchor===g.key).getBoundingClientRect();return {key:g.key,local:g.A,actualCSS:[(a.left+a.right)/2,(a.top+a.bottom)/2]}}),targets:model.groups.filter(g=>g.kind!=='angle').map(g=>({id:graphic.get(g.key).id,sourceKey:g.key,canonical:canonical(g),Q:g.Q,rect:bounds(graphic.get(g.key).getBoundingClientRect())})),snapshot:snap()}}
function collapse(){if($('editor').contains(document.activeElement))$('edit').focus({preventScroll:true});$('editor').hidden=true;return snap()}
$('reveal').onclick=()=>{all=true;refresh()};$('reveal-houses').onclick=()=>{housesAll=!housesAll;refresh()};$('edit').onclick=()=>{$('editor').hidden=false};$('recover').onclick=()=>trace.push({kind:'recovery-control-native',post:0});
window.research={ready:true,draw,measure,snap,trace,calls,collapse,clear:()=>{selected=null;refresh()},domToken:id=>token($(id)),top:(x,y)=>{const e=document.elementFromPoint(x,y);return {target:e?.id,key:e?.closest('[data-target]')?.dataset.target,canonical:e?.closest('[data-target]')?.dataset.canonical}},get model(){return model}};
