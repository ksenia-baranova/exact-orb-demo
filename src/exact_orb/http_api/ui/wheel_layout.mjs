// REQ-WHEEL-02/04/05: pure presentation geometry; no DOM, network or domain calculations.
import { aspectKey } from "./chart_state.mjs";

export class WheelLayoutError extends Error {
  constructor(code, detail = "") { super(code + (detail ? ": " + detail : "")); this.name = "WheelLayoutError"; this.code = code; }
}
export const POINT_GLYPHS = Object.freeze({sun:"☉",moon:"☽",mercury:"☿",venus:"♀",mars:"♂",jupiter:"♃",saturn:"♄",uranus:"♅",neptune:"♆",pluto:"♇",chiron:"⚷",true_node:"☊",south_node:"☋",mean_apog:"⚸",selena:"☽+",pars_fortune:"⊗"});

// R3 shape geometry in native CSS pixels. These three marks do not depend on font fallback.
export const POINT_VECTORS=Object.freeze({
 chiron:{label:'Хирон',shapes:[['circle',{cx:0,cy:4,r:2.7}],['path',{d:'M0 -7 L0 1.3 M-2.5 -5 L2.5 -5 M0 -1.5 L4.5 -5.5'}]]},
 pars_fortune:{label:'Парс Фортуны',shapes:[['circle',{cx:0,cy:0,r:6.5}],['path',{d:'M-4.6 -4.6 L4.6 4.6 M-4.6 4.6 L4.6 -4.6'}]]},
 selena:{label:'Селена',shapes:[['path',{d:'M1.5 -6.3 A6.5 6.5 0 1 0 1.5 6.3 A5.6 5.6 0 0 1 1.5 -6.3 Z',solid:true}],['path',{d:'M5 -7 L5 -1 M2 -4 L8 -4'}]]}
});
// Keep shared symbol definitions immutable across renderer instances.
for(const symbol of Object.values(POINT_VECTORS)) {
 for(const shape of symbol.shapes){Object.freeze(shape[1]);Object.freeze(shape)}
 Object.freeze(symbol.shapes);Object.freeze(symbol);
}

const signs=['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓'];
const colors={conjunction:'#93b9f2',semisextile:'#e7b578',sextile:'#70c7ad',square:'#ef7d84',trine:'#79a9ed',quincunx:'#b1c978',opposition:'#d397d1'};
const plus=(p,q)=>[p[0]+q[0],p[1]+q[1]],box=(b,p)=>[b[0]+p[0],b[1]+p[1],b[2]+p[0],b[3]+p[1]];
export const boxGap=(a,b)=>Math.hypot(Math.max(a[0]-b[2],b[0]-a[2],0),Math.max(a[1]-b[3],b[1]-a[3],0));
const collide=(a,b)=>a.parts.some(x=>b.parts.some(y=>boxGap(box(x,a.P),box(y,b.P))<2));
const union=parts=>[Math.min(...parts.map(x=>x[0])),Math.min(...parts.map(x=>x[1])),Math.max(...parts.map(x=>x[2])),Math.max(...parts.map(x=>x[3]))];
const pairkey = aspectKey;
const norm=a=>(a%360+360)%360;
export function cyclicOrder(points){
 const v=[...points].sort((a,b)=>a.longitude-b.longitude||(a.id < b.id ? -1 : a.id > b.id ? 1 : 0));if(!v.length)return [];
 let cut=0,gap=-1;for(let i=0;i<v.length;i++){const d=norm(v[(i+1)%v.length].longitude-v[i].longitude);if(d>gap){gap=d;cut=(i+1)%v.length}}
 return [...v.slice(cut),...v.slice(0,cut)];
}

// Presentation sectors between consecutive published cusps; never infer point membership.
export function houseSectors(houses) {
 const ordered=[...(houses??[])].sort((a,b)=>a.number-b.number);
 return ordered.map((house,i)=>({number:house.number,start:house.cusp_longitude,
  end:ordered[(i+1)%ordered.length].cusp_longitude,
  middle:norm(house.cusp_longitude+norm(ordered[(i+1)%ordered.length].cusp_longitude-house.cusp_longitude)/2)}));
}

// Metrics are actual native SVG boxes at 16/12 CSS px, supplied by the leaf.
export function layoutWheel(input, nativeMeasure, width, { selectedAspectKey = null } = {}) {
 if (!Number.isFinite(width) || width < 176) throw new WheelLayoutError("viewport-width");
 const chart=structuredClone(input),glyphs=POINT_GLYPHS,metrics={};
 const measure=(text,size)=>{
   const key=text+"@"+size;
   if(!metrics[key]) {
     const m=nativeMeasure(text,size);
     if(!m || ![m.x,m.y,m.w,m.h].every(Number.isFinite) || m.w<0 || m.h<=0) throw new WheelLayoutError("font-measurement",text);
     metrics[key]={...m,size,text};
   }
   return metrics[key];
 };
 const part=(text,size,x=0,y=0,contour=false)=>{const m=measure(text,size);return {text,size,x:x-m.x-m.w/2,y:y-m.y-m.h/2,b:[x-m.w/2-(contour?.75:0),y-m.h/2-(contour?.75:0),x+m.w/2+(contour?.75:0),y+m.h/2+(contour?.75:0)],contour}};
 const pointparts=p=>{
  const a=[part(glyphs[p.id]||p.id,16,0,0,true)];
  if(p.retrograde){
   const sector=houseSectors(chart.houses).find(h=>h.number===p.house);
   const angle=((sector?.middle??p.longitude)-(chart.kind==='natal'?chart.angles.asc.longitude:0))*Math.PI/180;
   const direction=[Math.cos(angle),-Math.sin(angle)],r=part('R',12);
   let lo=0,hi=64;for(let i=0;i<32;i++){const d=(lo+hi)/2;if(boxGap(a[0].b,box(r.b,direction.map(v=>v*d)))<2)lo=d;else hi=d}
   a.push(part('R',12,direction[0]*hi,direction[1]*hi));
  }
  return a;
 };
 const ca=new Map;for(const a of chart.aspects)ca.set(pairkey(a),(ca.get(pairkey(a))||0)+1);
 const indexed=chart.aspects.map((a,i)=>({...a,key:pairkey(a),sourceIndex:i,unique:ca.get(pairkey(a))===1}));
 const selected=indexed.find(a=>a.unique&&a.key===selectedAspectKey);
 const selectedEndpoints=new Set(selected?[selected.from,selected.to]:[]);
 const displayPoints=selected?chart.points.filter(p=>selectedEndpoints.has(p.id)):chart.points;
 const selectedHouses=new Set(displayPoints.map(p=>p.house).filter(h=>h!==null));
 const sourceSectors=houseSectors(chart.houses);
 const sectors=sourceSectors.filter(h=>!selected||selectedHouses.has(h.number));
 const eligible=indexed.filter(a=>a.unique&&a.category!=='background'&&(!selected||a.key===selected.key));
 const order=cyclicOrder(displayPoints),rank=new Map(order.map((p,i)=>[p.id,i]));
 const origin=chart.kind==='natal'?chart.angles.asc.longitude:0;
 const D=width,H=width;
 function defaults(aspectInset=66){
  const C=[D/2,H/2],R=D/2-4;
  const xy=(lng,r)=>{const t=(lng-origin)*Math.PI/180;return [C[0]-r*Math.cos(t),C[1]+r*Math.sin(t)]};
  const mk=(key,kind,A,draw)=>({key,kind,A:[...A],P:[...A],draw,parts:draw.map(x=>x.b),moved:false});
  const fixed=signs.map((s,i)=>mk('sign:'+i,'sign',xy(i*30+15,R-12),[part(s,16)]));
  const pointReach=Math.max(0,...displayPoints.flatMap(p=>pointparts(p).slice(0,1).flatMap(k=>[[k.b[0],k.b[1]],[k.b[2],k.b[1]],[k.b[2],k.b[3]],[k.b[0],k.b[3]]].map(a=>Math.hypot(...a)))));
  const pointR=R-28-pointReach;
  const aspectR=Math.max(R*.22,pointR-aspectInset),houseR=aspectR+12;
  const points=displayPoints.map(p=>({...mk(p.id,'point',xy(p.longitude,R-31),pointparts(p)),
   P:xy(p.longitude,pointR),reference:xy(p.longitude,pointR),longitude:p.longitude,house:p.house,rank:rank.get(p.id)}));
  const endpoint=new Map([...chart.points.map(p=>[p.id,p.longitude]),...Object.entries(chart.angles||{}).map(([k,v])=>[k,v.longitude])]);
  const angles=Object.entries(chart.angles||{}).filter(([id])=>!selected||selectedEndpoints.has(id)).map(([id,v])=>mk('angle:'+id,'angle',xy(v.longitude,aspectR*.72),[part(id==='vertex'?'Vx':id.toUpperCase(),12)]));
  const houses=sectors.map(h=>({...mk('house:'+h.number,'house',xy(h.middle,houseR),[part(String(h.number),D>=480?16:12)]),number:h.number}));
  const markers=eligible.filter(a=>a.type==='conjunction').map(a=>{const x=xy(endpoint.get(a.from),aspectR),y=xy(endpoint.get(a.to),aspectR);return {...mk('conj:'+a.key,'marker',[(x[0]+y[0])/2,(x[1]+y[1])/2],[part('☌',16,0,0,true)]),aspect:a}});
  return {C,R,pointR,aspectR,houseR,sectors,xy,points,angles,markers,houses,fixed,endpoint,D,H};
 }
 // The house is a published fact, never inferred from longitude. Only glyph positions move.
 function packPoints(state){
  const {C,R,pointR,houseR,xy}=state;
  const step=4,choices=new Map;
  for(const g of state.points){
   const sector=chart.kind==='natal'?sourceSectors.find(h=>h.number===g.house):null;
   if(chart.kind==='natal'&&!sector)throw new WheelLayoutError('point-house',g.key);
   const span=sector?norm(sector.end-sector.start):360,mid=sector?.middle??g.longitude;
   const offset=lng=>norm(lng-mid+180)-180;
   const desired=Math.max(-span/2,Math.min(span/2,offset(g.longitude)));
   g.sector=sector;g.houseOffset=desired;
   const fitsSector=(p)=>g.parts.every(b=>{const a=box(b,p);
    const nearest=[Math.max(a[0],Math.min(a[2],C[0])),Math.max(a[1],Math.min(a[3],C[1]))];
    if(Math.hypot(nearest[0]-C[0],nearest[1]-C[1])<houseR+11)return false;
    return [[a[0],a[1]],[a[2],a[1]],[a[2],a[3]],[a[0],a[3]]].every(q=>{
    const radius=Math.hypot(q[0]-C[0],q[1]-C[1]);
    const lng=origin+Math.atan2(q[1]-C[1],C[0]-q[0])*180/Math.PI;
    return radius<=R-28&&radius>=houseR+11&&(!sector||Math.abs(offset(lng))<span/2);
   })});
   const list=[];
   for(let row=0,r=pointR;r>houseR+11;row++,r-=step){
    const angles=[desired,0];for(let a=-span/2;a<=span/2;a+=1)angles.push(a);
    const seen=new Set;
    for(const a of angles){const token=a.toFixed(6);if(seen.has(token))continue;seen.add(token);
     const P=xy(mid+a,r);if(fitsSector(P))list.push({P,row,offset:a,cost:Math.abs(a-desired)});
    }
   }
   list.sort((a,b)=>a.row-b.row||a.cost-b.cost||a.offset-b.offset);choices.set(g.key,list);
  }
  const ordered=[...state.points].sort((a,b)=>(a.house??0)-(b.house??0)||a.houseOffset-b.houseOffset||(a.key<b.key?-1:1));
  const compatible=(g,c,o)=>!collide({...g,P:c.P},o)&&(!(g.house!==null&&g.house===o.house&&c.row===o.row)||
   (ordered.indexOf(g)<ordered.indexOf(o)?c.offset<o.offset:c.offset>o.offset));
  let nodes=0;
  function place(todo,placed){
   if(!todo.length)return true;if(++nodes>50000)return false;
   let chosen,available;
   for(const g of todo){const list=choices.get(g.key).filter(c=>placed.every(o=>compatible(g,c,o)));
    if(!list.length)return false;if(!available||list.length<available.length){chosen=g;available=list}
   }
   for(const c of available){Object.assign(chosen,c);if(place(todo.filter(g=>g!==chosen),[...placed,chosen]))return true}
   return false;
  }
  if(!place(ordered,[]))return false;
  for(const g of state.points)g.moved=Math.hypot(g.P[0]-g.reference[0],g.P[1]-g.reference[1])>1e-7;
  return true;
 }
 let state;
 for(const inset of [66,86,106,146,206,306,506]){state=defaults(inset);if(packPoints(state))break;state=null}
 if(!state)throw new WheelLayoutError('house-rows-capacity');
 state.all=[...state.points,...state.angles,...state.markers,...state.houses];
 state.C0=new Set;
 state.anchorObstacles=[...state.angles,...state.markers,...state.houses].map(g=>({key:'anchor:'+g.key,owner:g.key,P:g.A,parts:[[-1,-1,1,1]]}));
 const auxiliary=[...state.angles,...state.markers,...state.houses];
 for(const g of auxiliary){for(const o of [...state.fixed,...state.points,...auxiliary,...state.anchorObstacles])if(o.key!==g.key&&o.owner!==g.key&&collide(g,o))state.C0.add(g.key)}
 const fixed=[...state.fixed,...state.points,...auxiliary.filter(g=>!state.C0.has(g.key)),...state.anchorObstacles];
 const inside=g=>g.parts.every(b=>{const a=box(b,g.P);return [[a[0],a[1]],[a[2],a[1]],[a[2],a[3]],[a[0],a[3]]].every(p=>Math.hypot(p[0]-state.C[0],p[1]-state.C[1])<=state.R-24)});
 const fits=(g,obstacles)=>inside(g)&&obstacles.every(o=>o.key===g.key||o.owner===g.key||!collide(g,o));
 const aux=auxiliary.filter(g=>state.C0.has(g.key));
 const candidates=new Map;
 for(const g of aux){const list=[];for(let x=state.C[0]-state.R+24;x<=state.C[0]+state.R-24;x+=4)for(let y=state.C[1]-state.R+24;y<=state.C[1]+state.R-24;y+=4){const p=[x,y],test={...g,P:p};if(fits(test,fixed))list.push(p)}list.sort((a,b)=>Math.hypot(a[0]-g.A[0],a[1]-g.A[1])-Math.hypot(b[0]-g.A[0],b[1]-g.A[1])||a[1]-b[1]||a[0]-b[0]);candidates.set(g.key,list)}
 let nodes=0;
 function search(todo,placed){
  if(!todo.length)return true;if(++nodes>100000)return false;
  let chosen,allowed;for(const g of todo){const c=candidates.get(g.key).filter(p=>fits({...g,P:p},placed));if(!c.length)return false;if(!allowed||c.length<allowed.length){chosen=g;allowed=c}}
  for(const p of allowed){chosen.P=p;if(search(todo.filter(x=>x!==chosen),[...placed,chosen]))return true}return false;
 }
 if(!search(aux,fixed))throw new WheelLayoutError('auxiliary-search',aux.map(g=>g.key).join(','));
 // Find an exact axis contact with a frozen obstacle. A closing derivative proves
 // no positive continuous prefix toward A; this is stronger than a failed 1px probe.
 const certificates=[];
 const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
 for(let contactPass=0;contactPass<=aux.length;contactPass++)for(const g of aux){
  const existing=certificates.find(c=>c.key===g.key);if(existing&&existing.kind!=='unproven-grid-seed')continue;
  const contactTargets=[...fixed,...aux.filter(o=>o!==g&&certificates.some(c=>c.key===o.key&&c.kind!=='unproven-grid-seed'))];
  const obstacles=[...fixed,...aux.filter(o=>o!==g)];const list=[];
  if(fits({...g,P:g.A},obstacles)){g.P=[...g.A];certificates.push({key:g.key,kind:'unmoved'});continue}
  for(const o of contactTargets){if(o.owner===g.key||o.key===g.key)continue;for(const b of g.parts)for(const raw of o.parts){const a=box(raw,o.P),cand=[
   {P:[a[0]-2-b[2],clamp(g.A[1],a[1]-b[3],a[3]-b[1])],axis:0,sign:1},
   {P:[a[2]+2-b[0],clamp(g.A[1],a[1]-b[3],a[3]-b[1])],axis:0,sign:-1},
   {P:[clamp(g.A[0],a[0]-b[2],a[2]-b[0]),a[1]-2-b[3]],axis:1,sign:1},
   {P:[clamp(g.A[0],a[0]-b[2],a[2]-b[0]),a[3]+2-b[1]],axis:1,sign:-1}
  ];for(const c of cand)if((g.A[c.axis]-c.P[c.axis])*c.sign>0&&fits({...g,P:c.P},obstacles))list.push({...c,obstacle:o.key,ownComponent:b,foreignBox:a,distance:Math.hypot(c.P[0]-g.A[0],c.P[1]-g.A[1])})}}
  list.sort((a,b)=>a.distance-b.distance||a.P[1]-b.P[1]||a.P[0]-b.P[0]);if(existing)certificates.splice(certificates.indexOf(existing),1);if(list.length){g.P=list[0].P;certificates.push({key:g.key,kind:'frozen-axis-contact',...list[0]})}else certificates.push({key:g.key,kind:'unproven-grid-seed'});
 }
 for(const g of aux)g.moved=g.P[0]!==g.A[0]||g.P[1]!==g.A[1];

 if(certificates.some(c=>c.kind==="unproven-grid-seed")) throw new WheelLayoutError("auxiliary-contact",certificates.filter(c=>c.kind==="unproven-grid-seed").map(c=>c.key).join(","));
 const all=[...state.fixed,...state.all],leaders=[];
 function route(g,end){
  const obs=all.filter(o=>o.key!==g.key).flatMap(o=>o.parts.map(b=>box(b,o.P)));
  const shared=(a,b,c,d)=>{const v=[b[0]-a[0],b[1]-a[1]],cross=p=>v[0]*(p[1]-a[1])-v[1]*(p[0]-a[0]);if((!v[0]&&!v[1])||cross(c)!==0||cross(d)!==0)return false;const axis=v[0]?0:1;return Math.min(Math.max(a[axis],b[axis]),Math.max(c[axis],d[axis]))>Math.max(Math.min(a[axis],b[axis]),Math.min(c[axis],d[axis]))};
  const priorSegments=leaders.filter(l=>l.path).flatMap(l=>l.path.slice(1).map((p,i)=>[l.path[i],p]));
  const start=g.A,valid=(a,b)=>!priorSegments.some(([c,d])=>shared(a,b,c,d))&&obs.every(v=>{const k=[v[0]-2,v[1]-2,v[2]+2,v[3]+2];let lo=0,hi=1;for(let j=0;j<2;j++){const t=b[j]-a[j];if(t===0){if(a[j]<k[j]||a[j]>k[j+2])return true}else{let u=(k[j]-a[j])/t,w=(k[j+2]-a[j])/t;if(u>w)[u,w]=[w,u];lo=Math.max(lo,u);hi=Math.min(hi,w);if(lo>hi)return true}}return false});
  if(valid(start,end))return [start,end];
  // An anchor can itself be hidden by a different label at the exact same longitude.
  // Preserve and report this counterexample rather than silently moving true anchors.
  if(obs.some(b=>start[0]>b[0]-2&&start[0]<b[2]+2&&start[1]>b[1]-2&&start[1]<b[3]+2))return null;
  const clearance=2.25+leaders.length*1.5;
  const pts=[start,end],add=p=>{if(p[0]>=1&&p[0]<=width-1&&p[1]>=1&&p[1]<=H-1)pts.push(p)};
  for(const b of obs)for(const margin of [2.25,clearance])for(const x of [b[0]-margin,b[2]+margin])for(const y of [b[1]-margin,b[3]+margin])add([x,y]);
  // A shared graph edge does not imply an impossible route. Offer nearby detour
  // vertices and keep original narrow-corridor corners available to every owner.
  for(const [a,b]of priorSegments){const dx=b[0]-a[0],dy=b[1]-a[1],d=Math.hypot(dx,dy);if(!d)continue;for(const offset of [-3,-1.5,1.5,3])add([Math.round(((a[0]+b[0])/2-dy/d*offset)*64)/64,Math.round(((a[1]+b[1])/2+dx/d*offset)*64)/64])}
  const cost=pts.map(()=>Infinity),prev=pts.map(()=>-1),done=new Set;cost[0]=0;
  for(let i=0;i<pts.length;i++){let at=-1;for(let j=0;j<pts.length;j++)if(!done.has(j)&&(at<0||cost[j]<cost[at]))at=j;if(at<0||!isFinite(cost[at]))break;if(at===1){const out=[];for(let k=1;k>=0;k=prev[k])out.push(pts[k]);return out.reverse()}done.add(at);for(let j=0;j<pts.length;j++)if(!done.has(j)&&valid(pts[at],pts[j])){const c=cost[at]+Math.hypot(pts[at][0]-pts[j][0],pts[at][1]-pts[j][1]);if(c<cost[j]){cost[j]=c;prev[j]=at}}}
  return null;
 }

 for(const g of aux) if(g.moved) {
   const path=route(g,g.P);
   if(!path) throw new WheelLayoutError("leader-route",g.key);
   leaders.push({key:g.key,path});
 }
 return {...state,width,H,D,chart,groups:state.all,leaders,metrics,aspects:indexed,eligible,auxCertificates:certificates};
}

export function sharedSegment(a,b,c,d) {
 const v=[b[0]-a[0],b[1]-a[1]],cross=p=>v[0]*(p[1]-a[1])-v[1]*(p[0]-a[0]);
 if((!v[0]&&!v[1])||cross(c)!==0||cross(d)!==0)return false;
 const k=v[0]?0:1;
 return Math.min(Math.max(a[k],b[k]),Math.max(c[k],d[k]))>Math.max(Math.min(a[k],b[k]),Math.min(c[k],d[k]));
}
export const ASPECT_COLORS = Object.freeze(colors);
