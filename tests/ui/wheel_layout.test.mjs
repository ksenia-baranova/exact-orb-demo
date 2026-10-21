// REQ-WHEEL-05/09: independent geometry calibrations and deterministic order.
import assert from "node:assert/strict";
import { test } from "node:test";
import { boxGap, cyclicOrder, sharedSegment, layoutWheel, WheelLayoutError, houseSectors } from "../../src/exact_orb/http_api/ui/wheel_layout.mjs";
test("gap includes equality, rejects diagonal near-overlap and handles fractional coordinates", () => {
  assert.equal(boxGap([0,0,10,10],[12,0,20,10]),2);
  assert.ok(boxGap([0,0,10,10],[11.984375,0,20,10])<2);
  assert.equal(boxGap([0,0,10,10],[13,14,20,20]),5);
  assert.ok(boxGap([0,0,10,10],[11,11,20,20])<2);
});
test("cyclic cut crosses 0 degrees and exact ties use canonical IDs, independent of input/locale", () => {
  const points=[{id:"venus",longitude:1},{id:"sun",longitude:359},{id:"moon",longitude:359},{id:"mars",longitude:0}];
  assert.deepEqual(cyclicOrder(points).map(p=>p.id),["moon","sun","mars","venus"]);
  assert.deepEqual(cyclicOrder(points.toReversed()),cyclicOrder(points));
  assert.deepEqual(cyclicOrder([]),[]);
});
test("shared route regression: positive length is forbidden, crossing/touch/parallel remain distinct", () => {
  assert.equal(sharedSegment([0,0],[30,0],[9.5,0],[40,0]),true); // 20.5px witness
  assert.equal(sharedSegment([0,0],[30,0],[15,-10],[15,10]),false);
  assert.equal(sharedSegment([0,0],[30,0],[30,0],[40,0]),false);
  assert.equal(sharedSegment([0,0],[30,0],[0,0.5],[30,0.5]),false);
});
test("invalid viewport and missing real measurements report typed local layout errors", () => {
  assert.throws(()=>layoutWheel({},()=>{},NaN),WheelLayoutError);
  const empty={kind:"cosmogram",points:[],angles:null,houses:null,aspects:[]};
  assert.throws(()=>layoutWheel(empty,()=>({x:0,y:0,w:0,h:0}),328),/font-measurement/);
  const layout=layoutWheel(empty,()=>({x:0,y:-8,w:8,h:16}),328);
  assert.equal(layout.fixed.length,12);
  assert.equal(layout.D,328);
  assert.equal(layout.points.length,0);
  assert.equal(layout.groups.length,0);
});

test("numbered house sectors cross zero using consecutive published cusps, not point longitudes",()=>{
 const houses=[{number:2,cusp_longitude:20},{number:1,cusp_longitude:350}];
 const sectors=houseSectors(houses);
 assert.deepEqual(sectors,[{number:1,start:350,end:20,middle:5},{number:2,start:20,end:350,middle:185}]);
 assert.deepEqual(houseSectors(null),[]);
 assert.deepEqual(houses,[{number:2,cusp_longitude:20},{number:1,cusp_longitude:350}]);
});

// Owner20.10 / REQ-WHEEL-02/05/09: glyphs may move, published facts may not.
const metrics=(text,size)=>({x:0,y:-size*.8,w:text==='R'?7:12,h:size});
const natal=()=>({kind:'natal',angles:{asc:{longitude:350}},houses:Array.from({length:12},(_,i)=>({number:i+1,cusp_longitude:(350+i*30)%360})),points:[
 {id:'sun',longitude:359,house:1,retrograde:false},{id:'moon',longitude:359.2,house:1,retrograde:true},
 {id:'mercury',longitude:.2,house:1,retrograde:true},{id:'venus',longitude:1,house:1,retrograde:false}],aspects:[]});
const bounds=(g,b)=>[g.P[0]+b[0],g.P[1]+b[1],g.P[0]+b[2],g.P[1]+b[3]];
for(const width of [720,448,328])test('internal house rows contain complete glyph/R bounds across 0 at '+width,()=>{
 const chart=natal(),saved=structuredClone(chart),layout=layoutWheel(chart,metrics,width);
 assert.deepEqual(chart,saved);assert.equal(layout.width,width);assert.equal(layout.D,width);
 assert.equal('column' in layout,false);assert.equal(layout.points.length,4);
 for(const g of layout.points){
  assert.equal(g.house,1);assert.deepEqual(g.A,layout.xy(chart.points.find(p=>p.id===g.key).longitude,layout.R-31));
  for(const raw of g.parts){const b=bounds(g,raw);for(const [x,y]of[[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]]){
   const angle=(350+Math.atan2(y-layout.C[1],layout.C[0]-x)*180/Math.PI+720)%360;
   const rel=(angle-350+360)%360;assert.ok(rel<30,'entire glyph stays in source house');
   assert.ok(Math.hypot(x-layout.C[0],y-layout.C[1])<=layout.R-28);
  }}
 }
 for(let i=0;i<layout.points.length;i++)for(let j=i+1;j<layout.points.length;j++)for(const a of layout.points[i].parts)for(const b of layout.points[j].parts)assert.ok(boxGap(bounds(layout.points[i],a),bounds(layout.points[j],b))>=2);
 assert.equal(layout.leaders.some(l=>layout.points.some(p=>p.key===l.key)),false);
 if(width===328)assert.ok(new Set(layout.points.map(p=>p.row)).size>1,'crowding uses multiple internal rows');
 const reverse=layoutWheel({...chart,points:chart.points.toReversed()},metrics,width);
 assert.deepEqual(layout.points.map(p=>[p.key,p.P,p.row]).sort(),reverse.points.map(p=>[p.key,p.P,p.row]).sort());
});
test('published house controls placement even if source longitude is across a cusp',()=>{
 const chart=natal();chart.points=[{...chart.points[0],longitude:40,house:1}];const layout=layoutWheel(chart,metrics,448);
 const g=layout.points[0],angle=(350+Math.atan2(g.P[1]-layout.C[1],layout.C[0]-g.P[0])*180/Math.PI+720)%360;
 assert.ok((angle-350+360)%360<30);assert.equal(layout.endpoint.get('sun'),40);assert.equal(chart.points[0].longitude,40);
});
test('cosmogram clusters use internal rows without inventing houses',()=>{
 const chart={kind:'cosmogram',houses:null,angles:null,aspects:[],points:natal().points.map(p=>({...p,house:null}))};
 const layout=layoutWheel(chart,metrics,328);assert.equal(layout.sectors.length,0);assert.ok(layout.points.every(p=>p.house===null));assert.equal(layout.points.length,4);
});
