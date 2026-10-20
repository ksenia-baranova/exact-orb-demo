// Owner20.10: aspect-only view, native wheel focus, source endpoint houses (no membership calculation).
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";
import {mountChartResult} from "../../src/exact_orb/http_api/ui/facts.mjs";
import {mountBirthForm} from "../../src/exact_orb/http_api/ui/main.mjs";
import {documentPort} from "./fixtures/dom.mjs";
import {harness,currentPath,response,ready} from "./fixtures/session.mjs";
const natal=JSON.parse(readFileSync(new URL("./fixtures/natal_1985_chart_dto.json",import.meta.url),"utf8"));
const rows=(d,id)=>[...d.getElementById(id).querySelector("tbody").children].filter(n=>!n.hidden);
const mount=chart=>{const document=documentPort(),result=mountChartResult(document);document.root.append(result.element);result.update({status:"chart_ready",chart,chart_stale:false});return{document,result}};
test("Owner aspect view focuses wheel, shows source endpoints/houses only, and restores full tables on exit",()=>{
 const chart=structuredClone(natal),{document,result}=mount(chart),aspect=chart.aspects[0],ends=new Set([aspect.from,aspect.to]);
 const all=document.getElementById("aspects-show-all");all.click();document.getElementById("houses-show-all").click();
 const button=rows(document,"aspects-table")[0].querySelector("button");button.focus();button.click();
 assert.equal(document.activeElement===document.getElementById("chart-wheel"),true);
 assert.equal(result.element.dataset.aspectFocus,"true");
 assert.equal(rows(document,"aspects-table").length,1);
 assert.deepEqual(rows(document,"points-table").map(n=>n.querySelector("button").dataset.pointId),chart.points.filter(p=>ends.has(p.id)).map(p=>p.id));
 const houses=new Set(chart.points.filter(p=>ends.has(p.id)).map(p=>p.house).filter(h=>h!==null));
 assert.deepEqual(rows(document,"houses-table").map(n=>Number(n.children[0].textContent)),chart.houses.filter(h=>houses.has(h.number)).map(h=>h.number));
 const close=document.getElementById("aspect-close");assert.equal(close.hidden,false);
 document.getElementById("chart-wheel").emit("keydown",{key:"Escape"});
 assert.equal(result.element.dataset.aspectFocus,"false");assert.equal(document.activeElement===button,true);
 assert.equal(rows(document,"points-table").length,chart.points.length);assert.equal(rows(document,"houses-table").length,12);
 assert.equal(rows(document,"aspects-table").length,chart.aspects.length);result.dispose();
});
test("Owner aspect view does not invent a house for unknown time or an angle",()=>{
 for(const cosmogram of [false,true]){
  const chart=structuredClone(natal);chart.aspects=[{from:"sun",to:cosmogram?"moon":"asc",type:"trine",category:"exact",orb:0}];
  if(cosmogram){chart.kind="cosmogram";chart.houses=null;chart.angles=null;chart.house_system=null;chart.points.forEach(p=>p.house=null)}
  const {document,result}=mount(chart);rows(document,"aspects-table")[0].querySelector("button").click();
  assert.equal(rows(document,"points-table").length,cosmogram?2:1);assert.equal(rows(document,"houses-table").length,cosmogram?0:1);
  if(cosmogram)assert.match(result.element.textContent,/Для домов нужно время рождения/);
  else assert.match(document.getElementById("facts-houses").parentNode.textContent,/угла.*дом не назначается/);
  result.dispose();
 }
});
test("mounted aspect view hides unrelated form; planet activation still keeps native focus and no HTTP",async()=>{
 const h=harness(),document=documentPort(),view=ready();view.chart=structuredClone(natal);h.queue(currentPath,response(view));
 const app=mountBirthForm(document,{apiClient:h.apiClient,clock:h.clock});await app.ready;
 const requests=h.calls.length,moon=document.getElementById("points-table").querySelector('[data-point-id="moon"]');moon.focus();moon.click();
 assert.equal(document.activeElement===moon,true);
 const chosen=rows(document,"aspects-table").find(n=>!n.querySelector("button").disabled).querySelector("button");chosen.click();
 assert.equal(document.getElementById("birth-form").hidden,true);assert.equal(document.activeElement===document.getElementById("chart-wheel"),true);
 document.getElementById("aspect-close").click();assert.equal(app.result.element.dataset.aspectFocus,"false");
 app.result.editButton.click();assert.equal(document.getElementById("birth-form").hidden,false);
 assert.equal(h.calls.length,requests);app.dispose();
});
