// Owner20.10 / DEV-FIND-WHEEL-004..008: visible legend, label and source invariants.
import assert from 'node:assert/strict';import{test}from'node:test';import{readFileSync}from'node:fs';
import{mountChartResult,readChartFacts}from'../../src/exact_orb/http_api/ui/facts.mjs';import{ASPECT_COLORS}from'../../src/exact_orb/http_api/ui/wheel_layout.mjs';import{documentPort}from'./fixtures/dom.mjs';
const chart=JSON.parse(readFileSync(new URL('./fixtures/natal_1985_chart_dto.json',import.meta.url),'utf8'));
test('006: seven visible legend entries identify the actual type palette, conjunction and stroke categories',()=>{
 const d=documentPort(),r=mountChartResult(d);d.root.append(r.element);r.update({status:'chart_ready',chart,chart_stale:false});const legend=d.getElementById('aspect-legend');assert.ok(legend,'color legend exists');
 const entries=legend.querySelectorAll('[data-aspect-type]');assert.equal(entries.length,7);for(const n of entries){const type=n.getAttribute('data-aspect-type');assert.match(n.getAttribute('style'),new RegExp(ASPECT_COLORS[type]));assert.ok(n.textContent.trim().length>2)}
 assert.match(legend.textContent,/Соединение/);assert.match(legend.textContent,/Сплошная/);assert.match(legend.textContent,/Пунктир/);r.dispose();
});
test('007: southern-node label is concise and published point facts/order are preserved',()=>{
 const before=structuredClone(chart),facts=readChartFacts(chart),node=facts.points.rows.find(p=>p.id==='south_node');assert.equal(node.name,'Южный узел');assert.equal(node.house,String(chart.points.find(p=>p.id==='south_node').house));assert.deepEqual(chart,before);assert.equal(facts.points.rows.length,chart.points.length);
});
