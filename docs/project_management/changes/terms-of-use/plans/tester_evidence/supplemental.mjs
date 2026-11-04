// Explicit cross-product checks supplement shared component regression (T-02/08/15/16).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {mountBirthForm} from '../../../../../../src/exact_orb/http_api/ui/main.mjs';
import {documentPort} from '../../../../../../tests/ui/fixtures/dom.mjs';
import {harness,ready,views,charts,response,committed,deferred,currentPath,buildPath} from '../../../../../../tests/ui/fixtures/session.mjs';
const full = JSON.parse(readFileSync(new URL('../../../../../../tests/ui/fixtures/natal_1985_chart_dto.json',import.meta.url),'utf8'));
// Distinct opaque response identity is fixed before execution; numeric facts stay golden.
full.chart_identity = 'eo:calc:v2:' + 'b'.repeat(64);
let examples=0;
async function mounted(saved=true) {
  const h=harness(),document=documentPort();if(saved)h.queue(currentPath,response(ready()));
  const ui=mountBirthForm(document,{apiClient:h.apiClient,clock:h.clock});await ui.ready;
  const get=id=>document.getElementById(id);
  function edit(id,value){const n=get(id),check=typeof value==='boolean';n[check?'checked':'value']=value;n.emit(check?'change':'input');}
  function acknowledge(method){if(method==='manual')edit('terms-acknowledged',true);else{get('terms-link').click();get('terms-agree').click();}}
  return {h,ui,get,edit,acknowledge};
}
for(const checked of [false,true]) {
  const m=await mounted(false);m.edit('birth-place','Моск');m.edit('birth-time','12:6');m.edit('terms-acknowledged',checked);
  const before=m.ui.form.snapshot();m.get('terms-link').click();assert.equal(m.get('terms-page').hidden,false);m.get('terms-back').click();
  assert.deepEqual(m.ui.form.snapshot(),before);assert.equal(m.h.builds().length,0);m.ui.dispose();examples++;
}
for(const method of ['manual','page'])for(const unknown of [false,true])for(const edited of [false,true]) {
  const m=await mounted();m.acknowledge(method);m.edit('time-unknown',unknown);
  const chart=unknown?charts.cosmogram:full,pending=deferred(),entered=m.h.entered(buildPath);
  m.h.queue(buildPath,pending.promise);const sending=m.get('birth-form').emit('submit');await entered;
  if(edited)m.edit('birth-date','2000-02-29');pending.resolve(response(committed(chart)));await sending;
  assert.equal(m.ui.result.element.dataset.chartIdentity,chart.chart_identity);
  assert.deepEqual(m.ui.session.snapshot().view.chart,chart);
  assert.equal(m.get('birth-editor').hidden,!edited);
  assert.equal(m.get('terms-acknowledged').checked,true);
  if(!unknown)for(const [group,total]of[['points',chart.points.length],['houses',chart.houses.length],['aspects',chart.aspects.length]]){
    const rows=()=>m.get(group+'-table').querySelectorAll('tbody tr');
    assert.equal(rows().filter(n=>!n.hidden).length,Math.min(5,total));m.get(group+'-show-all').click();
    assert.equal(rows().filter(n=>!n.hidden).length,total);
  }
  else assert.equal(m.get('houses-table').hidden,true);
  const chat=m.ui.result.element.querySelectorAll('button').find(n=>n.textContent==='Открыть чат');assert.equal(chat.disabled,true);chat.click();
  assert.equal(m.h.builds().length,1);m.ui.dispose();examples++;
}
for(const method of ['manual','page'])for(const kind of ['ready','empty','unavailable']) {
  const m=await mounted();m.acknowledge(method);m.edit('birth-date','1990-09-02');
  const view=kind==='empty'?structuredClone(views.empty):ready();
  if(kind!=='empty'){view.birth.birth_date='2001-01-01';view.chart=kind==='ready'?structuredClone(full):null;view.chart_stale=kind==='ready'?false:null;view.status=kind==='ready'?'chart_ready':'chart_unavailable';}
  const pending=deferred(),entered=m.h.entered(currentPath);m.h.queue(buildPath,response({status:'already_applied',state_version:3}));m.h.queue(currentPath,pending.promise);
  const sending=m.get('birth-form').emit('submit');await entered;assert.notEqual(m.ui.result.element.dataset.chartIdentity,full.chart_identity);
  pending.resolve(response(view));await sending;assert.deepEqual(m.ui.session.snapshot().view,view);
  assert.equal(m.get('birth-date').value,'1990-09-02');assert.equal(m.get('terms-acknowledged').checked,true);
  assert.equal(m.ui.result.element.hidden,kind!=='ready');if(kind!=='empty')assert.ok(m.get('session-status').textContent.includes('2001-01-01'));
  assert.equal(m.h.builds().length,1);m.ui.dispose();examples++;
}
for(const action of ['agree','back'])for(const checked of [false,true])for(const value of ['', '12:00']) {
  const m=await mounted();m.edit('birth-time',value);m.edit('time-unknown',true);m.edit('terms-acknowledged',checked);
  m.get('terms-link').click();m.get('terms-'+action).click();m.edit('time-unknown',false);
  assert.equal(m.get('birth-time').value,value);assert.equal(m.get('terms-acknowledged').checked,action==='agree'||checked);assert.equal(m.h.builds().length,0);
  m.ui.dispose();examples++;
}
console.log(JSON.stringify({status:'PASS',examples,cards:['T-02','T-08','T-15','T-16']}));
