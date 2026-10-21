// Research only. No app imports, network calls, live host or production API.
const NS='http://www.w3.org/2000/svg';
const names={sun:'Солнце',moon:'Луна',mercury:'Меркурий',venus:'Венера',mars:'Марс',jupiter:'Юпитер',saturn:'Сатурн',uranus:'Уран',neptune:'Нептун',pluto:'Плутон',chiron:'Хирон',true_node:'Сев. узел',south_node:'Южн. узел',mean_apog:'Лилит',selena:'Селена',pars_fortune:'Парс Ф.'};
const signs=['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓'];
const colors={conjunction:'#385f8a',sextile:'#277566',square:'#ad3e42',trine:'#386bb0',quincunx:'#8a632f',opposition:'#944e82'};
export const el=(tag,a={},text)=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(a))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e};
const plus=(p,q)=>[p[0]+q[0],p[1]+q[1]],box=(b,p)=>[b[0]+p[0],b[1]+p[1],b[2]+p[0],b[3]+p[1]];
export const distance=(a,b)=>Math.hypot(Math.max(a[0]-b[2],b[0]-a[2],0),Math.max(a[1]-b[3],b[1]-a[3],0));
const collide=(a,b)=>a.parts.some(x=>b.parts.some(y=>distance(box(x,a.P),box(y,b.P))<2));
const union=parts=>[Math.min(...parts.map(x=>x[0])),Math.min(...parts.map(x=>x[1])),Math.max(...parts.map(x=>x[2])),Math.max(...parts.map(x=>x[3]))];
const pairkey=a=>[...([a.from,a.to].sort()),a.type].join('|');
const norm=a=>(a%360+360)%360;
function cyclic(points){
 const v=[...points].sort((a,b)=>a.longitude-b.longitude||a.id.localeCompare(b.id));if(!v.length)return [];
 let cut=0,gap=-1;for(let i=0;i<v.length;i++){const d=norm(v[(i+1)%v.length].longitude-v[i].longitude);if(d>gap){gap=d;cut=(i+1)%v.length}}
 return [...v.slice(cut),...v.slice(0,cut)];
}
export async function compose(mount,input,{width=328,font='"Segoe UI Symbol", "Segoe UI", sans-serif',selection=null}={}){
 const chart=structuredClone(input.chart),saved=JSON.stringify(chart),glyphs=input.glyphs;
 const svg=el('svg',{width,height:width,viewBox:`0 0 ${width} ${width}`,role:'img','aria-label':'Карта: положения, дома и аспекты; управление в таблицах',xmlns:NS});mount.append(svg);
 svg.style.fontFamily=font;svg.style.overflow='hidden';svg.style.display='block';
 const metrics={},measure=(text,size)=>{
  const k=text+'@'+size;if(metrics[k])return metrics[k];const t=el('text',{'font-size':size,x:0,y:0},text);svg.append(t);const b=t.getBBox();t.remove();
  return metrics[k]={x:b.x,y:b.y,w:b.width,h:b.height,size,text};
 };
 const part=(text,size,x=0,y=0,contour=false)=>{const m=measure(text,size);return {text,size,x:x-m.x-m.w/2,y:y-m.y-m.h/2,b:[x-m.w/2-(contour?.75:0),y-m.h/2-(contour?.75:0),x+m.w/2+(contour?.75:0),y+m.h/2+(contour?.75:0)],contour}};
 const pointparts=(p,column=false)=>{const a=[part(glyphs[p.id]||p.id,16,0,0,true)];const right=a[0].b[2];if(p.retrograde){const r=measure('R',12);a.push(part('R',12,right+2+r.w/2,3))}if(column){const b=union(a.map(x=>x.b)),m=measure(names[p.id]||p.id,12);a.push(part(names[p.id]||p.id,12,b[2]+5+m.w/2,0))}return a};
 const ca=new Map;for(const a of chart.aspects)ca.set(pairkey(a),(ca.get(pairkey(a))||0)+1);
 const indexed=chart.aspects.map((a,i)=>({...a,key:pairkey(a),sourceIndex:i,unique:ca.get(pairkey(a))===1}));
 const eligible=indexed.filter(a=>a.unique&&a.category!=='background');
 const selected=selection?.kind==='aspect'?indexed.find(a=>a.key===selection.key&&a.unique):null;
 const drawn=selected?(selected.category==='background'?[]:[selected]):eligible;
 const order=cyclic(chart.points),rank=new Map(order.map((p,i)=>[p.id,i]));
 const origin=chart.kind==='natal'?chart.angles.asc.longitude:0;
 const colSpecs=chart.points.map(p=>({p,parts:pointparts(p,true)}));
 const allColWidth=Math.ceil(Math.max(...colSpecs.map(g=>{const b=union(g.parts.map(p=>p.b));return b[2]-b[0]}))+8);
 function defaults(D,left=0,H=D){
  const C=[left+D/2,H/2],R=D/2-4;
  const xy=(lng,r)=>{const t=(lng-origin)*Math.PI/180;return [C[0]-r*Math.cos(t),C[1]+r*Math.sin(t)]};
  const mk=(key,kind,A,draw)=>({key,kind,A:[...A],P:[...A],draw,parts:draw.map(x=>x.b),moved:false});
  const fixed=signs.map((s,i)=>mk('sign:'+i,'sign',xy(i*30+15,R-12),[part(s,16)]));
  const points=chart.points.map(p=>({...mk(p.id,'point',xy(p.longitude,R-40),pointparts(p)),longitude:p.longitude,rank:rank.get(p.id)}));
  const endpoint=new Map([...chart.points.map(p=>[p.id,p.longitude]),...Object.entries(chart.angles||{}).map(([k,v])=>[k,v.longitude])]);
  const angles=Object.entries(chart.angles||{}).map(([id,v])=>mk('angle:'+id,'angle',xy(v.longitude,R*.48),[part(id==='vertex'?'Vx':id.toUpperCase(),12)]));
  const markers=eligible.filter(a=>a.type==='conjunction').map(a=>{const x=xy(endpoint.get(a.from),R*.27),y=xy(endpoint.get(a.to),R*.27);return {...mk('conj:'+a.key,'marker',[(x[0]+y[0])/2,(x[1]+y[1])/2],[part('☌',16,0,0,true)]),aspect:a}});
  const all=[...points,...angles,...markers],C0=new Set;
  for(let i=0;i<all.length;i++){for(const f of fixed)if(collide(all[i],f))C0.add(all[i].key);for(let j=i+1;j<all.length;j++)if(collide(all[i],all[j])){C0.add(all[i].key);C0.add(all[j].key)}}
  return {C,R,xy,points,angles,markers,fixed,all,C0,endpoint,D,left,H};
 }
 let state=defaults(width),withColumn=state.points.some(g=>state.C0.has(g.key)),colWidth=withColumn?allColWidth:0;
 let D=withColumn?width-colWidth-12:width;
 if(D<176)throw Error('width cannot hold measured column and readable wheel');
 state=defaults(D,withColumn?colWidth+12:0);
 const movedPoints=state.points.filter(g=>state.C0.has(g.key)).sort((a,b)=>a.rank-b.rank);
 if(!movedPoints.length)withColumn=false;
 // Column spacing is measured, not a fixed glyph count or an angular threshold.
 const cr=movedPoints.map(g=>{const p=chart.points.find(p=>p.id===g.key),draw=pointparts(p,true),b=union(draw.map(x=>x.b));return {g,draw,b,h:b[3]-b[1],A:g.A}});
 const H=Math.max(D,cr.reduce((s,g)=>s+g.h,0)+Math.max(0,cr.length-1)*2+16);
 state=defaults(D,withColumn?colWidth+12:0,H);
 const liveByKey=new Map(state.all.map(g=>[g.key,g]));
 const starts=[];let off=0;for(let i=0;i<cr.length;i++){if(i)off+=(cr[i-1].h+cr[i].h)/2+2;starts.push(off)}
 // PAV computes the L2 projection y[i]-starts[i] onto non-decreasing sequences.
 const blocks=[];for(let i=0;i<cr.length;i++){const v=liveByKey.get(cr[i].g.key).A[1]-starts[i];blocks.push({a:i,b:i,sum:v,n:1});while(blocks.length>1){const b=blocks.at(-1),a=blocks.at(-2);if(a.sum/a.n<=b.sum/b.n)break;blocks.splice(-2,2,{a:a.a,b:b.b,sum:a.sum+b.sum,n:a.n+b.n})}}
 const top=cr.length?8+cr[0].h/2:0,bottom=cr.length?H-8-cr.at(-1).h/2-starts.at(-1):H;
 const ys=[];for(const b of blocks){const z=Math.max(top,Math.min(bottom,Math.round(b.sum/b.n*64)/64));for(let i=b.a;i<=b.b;i++)ys[i]=z+starts[i]}
 for(let i=0;i<cr.length;i++){const g=liveByKey.get(cr[i].g.key),b=cr[i].b;g.draw=cr[i].draw;g.parts=g.draw.map(x=>x.b);g.P=[colWidth-4-b[2],ys[i]];g.moved=true;g.column=true}
 const fixed=[...state.fixed,...state.all.filter(g=>!state.C0.has(g.key)||g.column)];
 const inside=g=>g.parts.every(b=>{const a=box(b,g.P);return [[a[0],a[1]],[a[2],a[1]],[a[2],a[3]],[a[0],a[3]]].every(p=>Math.hypot(p[0]-state.C[0],p[1]-state.C[1])<=state.R-24)});
 const fits=(g,obstacles)=>inside(g)&&obstacles.every(o=>o.key===g.key||!collide(g,o));
 const aux=state.all.filter(g=>g.kind!=='point'&&state.C0.has(g.key));
 const candidates=new Map;
 for(const g of aux){const list=[];for(let x=state.C[0]-state.R+24;x<=state.C[0]+state.R-24;x+=4)for(let y=state.C[1]-state.R+24;y<=state.C[1]+state.R-24;y+=4){const p=[x,y],test={...g,P:p};if(fits(test,fixed))list.push(p)}list.sort((a,b)=>Math.hypot(a[0]-g.A[0],a[1]-g.A[1])-Math.hypot(b[0]-g.A[0],b[1]-g.A[1])||a[1]-b[1]||a[0]-b[0]);candidates.set(g.key,list)}
 let nodes=0;
 function search(todo,placed){
  if(!todo.length)return true;if(++nodes>100000)return false;
  let chosen,allowed;for(const g of todo){const c=candidates.get(g.key).filter(p=>fits({...g,P:p},placed));if(!c.length)return false;if(!allowed||c.length<allowed.length){chosen=g;allowed=c}}
  for(const p of allowed){chosen.P=p;if(search(todo.filter(x=>x!==chosen),[...placed,chosen]))return true}return false;
 }
 if(!search(aux,fixed))throw Error('bounded auxiliary layout failed: '+aux.map(g=>g.key).join(','));
 for(const g of aux)g.moved=g.P[0]!==g.A[0]||g.P[1]!==g.A[1];
 svg.setAttribute('height',H);svg.setAttribute('viewBox',`0 0 ${width} ${H}`);
 const {C,R,xy}=state;
 const circle=(r,a={})=>svg.append(el('circle',{cx:C[0],cy:C[1],r,fill:'none',stroke:'#c6d4df','stroke-width':.7,...a}));
 for(let i=0;i<12;i++){
  const a=xy(i*30,R),b=xy((i+1)*30,R),c=xy((i+1)*30,R-26),d=xy(i*30,R-26);
  svg.append(el('path',{d:`M${a} A${R} ${R} 0 0 0 ${b} L${c} A${R-26} ${R-26} 0 0 1 ${d} Z`,fill:i%2?'#eef4f7':'#f8fafc',stroke:'#bdcdd9','stroke-width':.5,'data-sector':i}));
 }
 circle(R);circle(R-26);circle(R*.27);
 for(const h of chart.houses||[]){const a=xy(h.cusp_longitude,R*.27),b=xy(h.cusp_longitude,R-26);svg.append(el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#aebfc9','stroke-width':.7,'data-house':h.number}))}
 for(const a of drawn.filter(a=>a.type!=='conjunction')){const p=xy(state.endpoint.get(a.from),R*.27),q=xy(state.endpoint.get(a.to),R*.27);svg.append(el('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:colors[a.type]||'#52687c','stroke-width':selected?2.5:1,'stroke-dasharray':a.category==='working'?'4 3':'none','data-aspect':a.key,'data-source-index':a.sourceIndex}))}
 const all=[...state.fixed,...state.all],leaders=[];
 // Route through a rectilinear visibility graph around label obstacles. Crossings between
 // leaders use an explicit white underlay; they never form a shared semantic branch.
 function route(g,end){
  const obs=all.filter(o=>o.key!==g.key).flatMap(o=>o.parts.map(b=>box(b,o.P)));
  const start=g.A,valid=(a,b)=>obs.every(v=>{const k=[v[0]-2,v[1]-2,v[2]+2,v[3]+2];let lo=0,hi=1;for(let j=0;j<2;j++){const t=b[j]-a[j];if(t===0){if(a[j]<k[j]||a[j]>k[j+2])return true}else{let u=(k[j]-a[j])/t,w=(k[j+2]-a[j])/t;if(u>w)[u,w]=[w,u];lo=Math.max(lo,u);hi=Math.min(hi,w);if(lo>hi)return true}}return false});
  if(valid(start,end))return [start,end];
  // An anchor can itself be hidden by a different label at the exact same longitude.
  // Preserve and report this counterexample rather than silently moving true anchors.
  if(obs.some(b=>start[0]>b[0]-2&&start[0]<b[2]+2&&start[1]>b[1]-2&&start[1]<b[3]+2))return null;
  const pts=[start,end];for(const b of obs){for(const x of [b[0]-2.25,b[2]+2.25])for(const y of [b[1]-2.25,b[3]+2.25])if(x>=1&&x<=width-1&&y>=1&&y<=H-1)pts.push([x,y])}
  const cost=pts.map(()=>Infinity),prev=pts.map(()=>-1),done=new Set;cost[0]=0;
  for(let i=0;i<pts.length;i++){let at=-1;for(let j=0;j<pts.length;j++)if(!done.has(j)&&(at<0||cost[j]<cost[at]))at=j;if(at<0||!isFinite(cost[at]))break;if(at===1){const out=[];for(let k=1;k>=0;k=prev[k])out.push(pts[k]);return out.reverse()}done.add(at);for(let j=0;j<pts.length;j++)if(!done.has(j)&&valid(pts[at],pts[j])){const c=cost[at]+Math.hypot(pts[at][0]-pts[j][0],pts[at][1]-pts[j][1]);if(c<cost[j]){cost[j]=c;prev[j]=at}}}
  return null;
 }
 const markerDrawn=new Set(drawn.filter(a=>a.type==='conjunction').map(a=>'conj:'+a.key));
 for(const g of state.all){
  if(g.kind==='marker'&&!markerDrawn.has(g.key))continue;
  if(g.moved){const b=union(g.parts);const end=g.column?[g.P[0]+b[2],g.P[1]]:g.P;const path=route(g,end);leaders.push({key:g.key,A:g.A,end,path});if(path){const d=path.map((p,i)=>(i?'L':'M')+p.join(' ')).join(' ');svg.append(el('path',{d,fill:'none',stroke:'white','stroke-width':3.5,'data-leader-bridge':g.key}));svg.append(el('path',{d,fill:'none',stroke:'#6e8798','stroke-width':.75,'data-leader':g.key}))}}
 }
 for(const g of all){
  if(g.kind==='marker'&&!markerDrawn.has(g.key))continue;
  const selectedPoint=selection?.kind==='point'?g.key===selection.id:selected&&(g.key===selected.from||g.key===selected.to||g.key==='conj:'+selected.key);
  const group=el('g',{'data-label':g.key,'data-kind':g.kind,transform:`translate(${g.P[0]} ${g.P[1]})`,'aria-label':g.kind==='point'?`${names[g.key]||g.key}${chart.points.find(p=>p.id===g.key).retrograde?', ретроградная':''}`:g.key});svg.append(group);
  for(const [i,p] of g.draw.entries()){
   // Solid white background prevents decorative cusps/leaders from obscuring glyph ink.
   group.append(el('rect',{x:p.b[0],y:p.b[1],width:p.b[2]-p.b[0],height:p.b[3]-p.b[1],rx:1,fill:'white',opacity:.94}));
   if(p.contour&&selectedPoint)group.append(el('rect',{x:p.b[0]+.75,y:p.b[1]+.75,width:p.b[2]-p.b[0]-1.5,height:p.b[3]-p.b[1]-1.5,rx:2,fill:'none',stroke:'#21475d','stroke-width':1.5,'data-selected':g.key}));
   group.append(el('text',{x:p.x,y:p.y,'font-size':p.size,fill:g.kind==='marker'?(colors[g.aspect.type]):'#193e55','data-component':g.key+':'+i},p.text));
  }
  if(g.kind!=='sign')svg.append(el('circle',{cx:g.A[0],cy:g.A[1],r:1,fill:'#305b75','data-anchor':g.key}));
 }
 const serialized=state.all.map(g=>({key:g.key,kind:g.kind,A:g.A,P:g.P,parts:g.parts,C0:state.C0.has(g.key),moved:g.moved,column:!!g.column,rank:g.rank,draw:g.draw}));
 return {svg,chart,state:{width,H,D,C,R,origin,withColumn,colWidth,C0:[...state.C0],groups:serialized,fixed:state.fixed.map(g=>({key:g.key,kind:g.kind,P:g.P,parts:g.parts})),leaders,metrics,auxNodes:nodes,column:{order:cr.map(x=>x.g.key),offsets:starts,ys,blocks,top,bottom},selection,aspects:indexed,drawn:drawn.map(a=>a.key),sourceUnchanged:saved===JSON.stringify(chart)}};
}
