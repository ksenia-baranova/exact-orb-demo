// TASK-D-007 CH-01/04, AS-WHEEL-18…22/30: real accept owner, controlled HTTP.
import assert from "node:assert/strict";
import { test } from "node:test";
import { harness, ready, committed, response, failure, currentPath, buildPath, deferred } from "./fixtures/session.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
function fields(form,birth) {
 form.setDate(birth.birth_date); form.setTime(birth.birth_time??"");form.setUnknownTime(birth.time_unknown);
 form.selectPlace({...birth.place,admin1_name:null,country_code:"RU"});form.acknowledge(true);
}
test("acceptance sequence changes only on valid acceptance, not phase/clear/render; attempt is immutable",async()=>{
 const h=harness(),initial=ready();h.queue(currentPath,response(initial));await h.coordinator.open();
 assert.equal(h.coordinator.snapshot().acceptance.seq,1);
 fields(h.form,initial.birth);h.form.setDate("1990-01-01");
 const pending=deferred();h.queue(buildPath,pending.promise);const submit=h.coordinator.submit();
 assert.equal(h.coordinator.snapshot().acceptance.seq,1);
 const intent=h.coordinator.snapshot().submittedIntent;
 h.form.setDate("2000-01-01");pending.resolve(response(committed()));await submit;
 const event=h.coordinator.snapshot().acceptance;
 assert.equal(event.seq,2);assert.equal(event.cause,"own_committed");assert.equal(event.reset,true);
 assert.equal(event.submitted.birth_date,"1990-01-01");assert.deepEqual(event.submitted,intent);
 h.coordinator.clearFieldError("date");assert.equal(h.coordinator.snapshot().acceptance.seq,2);
 assert.ok(h.changes.filter(s=>s.source==="build").length>=2,"positive repeated publication control");
 assert.equal(new Set(h.changes.filter(s=>s.source==="build").map(s=>s.acceptance.seq)).size,1);
 h.coordinator.dispose();
});
test("same birth but changed chart identity does not reset an own committed target",async()=>{
 const h=harness(),initial=ready();h.queue(currentPath,response(initial));await h.coordinator.open();fields(h.form,initial.birth);
 const result=committed();result.chart.chart_identity+="-new";h.queue(buildPath,response(result));await h.coordinator.submit();
 assert.equal(h.coordinator.snapshot().acceptance.reset,false);assert.equal(h.coordinator.snapshot().acceptance.allowCollapse,true);
 h.coordinator.dispose();
});
test("fresh matched recovery consumes the active changed-birth target once; later matched is automatic",async()=>{
 const h=harness(),a=ready();h.queue(currentPath,response(a));await h.coordinator.open();fields(h.form,a.birth);h.form.setDate("1990-01-01");
 const b=ready();b.birth.birth_date="1990-01-01";b.chart.chart_identity+="-B";
 h.queue(buildPath,new Error("lost"));h.queue(currentPath,response(b));await h.coordinator.submit();
 const first=h.coordinator.snapshot().acceptance;
 assert.equal(first.cause,"matched_recovery");assert.equal(first.reset,true);assert.equal(first.submitted.birth_date,"1990-01-01");
 h.queue(currentPath,response(b));await h.coordinator.foreground();
 const later=h.coordinator.snapshot().acceptance;
 assert.equal(later.cause,"automatic_current");assert.equal(later.reset,false);assert.equal(later.allowCollapse,false);
 assert.equal(later.attemptId,null);assert.equal(h.builds().length,1);h.coordinator.dispose();
});
test("stale match and failed safe GET do not consume pending goal; fresh positive control later does",async()=>{
 const h=harness(),a=ready();h.queue(currentPath,response(a));await h.coordinator.open();fields(h.form,a.birth);h.form.setDate("1990-01-01");
 const b=ready(true);b.birth.birth_date="1990-01-01";
 h.queue(buildPath,new Error("lost"));h.queue(currentPath,response(b));await h.coordinator.submit();
 assert.equal(h.coordinator.snapshot().acceptance.reset,false);
 const seq=h.coordinator.snapshot().acceptance.seq;
 h.queue(currentPath,new Error("GET failed"));await h.coordinator.recheck();
 assert.equal(h.coordinator.snapshot().acceptance.seq,seq);
 b.chart_stale=false;h.queue(currentPath,response(b));await h.coordinator.recheck();
 assert.equal(h.coordinator.snapshot().acceptance.cause,"matched_recovery");assert.equal(h.coordinator.snapshot().acceptance.reset,true);
 h.coordinator.dispose();
});
// Owner A006,20.10.2026: GET confirms the local target once, never POST provenance.
for(const changed of [false,true])test("already_applied fresh target confirms once, changed="+changed,async()=>{
 const h=harness(),a=ready();h.queue(currentPath,response(a));await h.coordinator.open();fields(h.form,a.birth);
 if(changed)h.form.setDate("1990-01-01");
 const b=ready();if(changed)b.birth.birth_date="1990-01-01";b.chart.chart_identity+="-already";
 h.queue(buildPath,response({status:"already_applied",state_version:2}));h.queue(currentPath,response(b));await h.coordinator.submit();
 const event=h.coordinator.snapshot().acceptance;
 assert.equal(event.cause,"already_applied_target_confirmed");assert.equal(event.reset,changed);
 assert.equal(event.allowCollapse,true);assert.equal(event.attemptId,1);
 assert.equal(event.submitted.birth_date,b.birth.birth_date);
 assert.equal(h.coordinator.snapshot().source,"current");assert.equal(h.coordinator.snapshot().resultSummary,null);
 h.queue(currentPath,response(b));await h.coordinator.foreground();
 const again=h.coordinator.snapshot().acceptance;
 assert.equal(again.cause,"automatic_current");assert.equal(again.reset,false);assert.equal(again.allowCollapse,false);assert.equal(again.attemptId,null);
 assert.equal(h.builds().length,1);h.coordinator.dispose();
});
for(const first of ["stale","different","failed"])test("already_applied "+first+" GET does not consume live target; fresh later confirms",async()=>{
 const h=harness(),a=ready();h.queue(currentPath,response(a));await h.coordinator.open();fields(h.form,a.birth);h.form.setDate("1990-01-01");
 const b=ready(first==="stale");b.birth.birth_date=first==="different"?"2000-01-01":"1990-01-01";
 h.queue(buildPath,response({status:"already_applied",state_version:2}));
 h.queue(currentPath,first==="failed"?new Error("GET failed"):response(b));await h.coordinator.submit();
 assert.equal(h.coordinator.snapshot().acceptance.reset,false);assert.equal(h.coordinator.snapshot().acceptance.allowCollapse,first==="failed");
 b.birth.birth_date="1990-01-01";b.chart_stale=false;
 h.queue(currentPath,response(b));await h.coordinator.recheck();
 assert.equal(h.coordinator.snapshot().acceptance.cause,"already_applied_target_confirmed");
 assert.equal(h.coordinator.snapshot().acceptance.reset,true);assert.equal(h.coordinator.snapshot().acceptance.attemptId,1);
 h.coordinator.dispose();
});
test("RESULT_SUPERSEDED never confirms own target even when GET matches",async()=>{
 const h=harness(),a=ready();h.queue(currentPath,response(a));await h.coordinator.open();fields(h.form,a.birth);h.form.setDate("1990-01-01");
 const b=ready();b.birth.birth_date="1990-01-01";
 h.queue(buildPath,response(failure("RESULT_SUPERSEDED"),409));h.queue(currentPath,response(b));await h.coordinator.submit();
 const e=h.coordinator.snapshot().acceptance;
 assert.equal(e.cause,"superseded_current");assert.equal(e.reset,false);assert.equal(e.allowCollapse,false);
 assert.equal(e.attemptId,null);assert.equal(e.submitted,null);h.coordinator.dispose();
});
test("mounted editor collapses once; opening it and repeated publish never hide it again",async()=>{
 const h=harness();h.queue(currentPath,response(ready()));const document=documentPort();
 const app=mountBirthForm(document,{apiClient:h.apiClient,clock:h.clock});await app.ready;
 const editor=document.getElementById("birth-editor"),edit=document.getElementById("birth-edit");
 assert.equal(editor.hidden,true);edit.click();assert.equal(editor.hidden,false);
 app.session.clearFieldError("date");assert.equal(editor.hidden,false);
 assert.equal(edit.getAttribute("aria-expanded"),"true");app.dispose();
});
test("submitted B with draft C remains open; edit then revert before acceptance can collapse once",async()=>{
 for(const mode of ["commit","already_applied"])for(const revert of [false,true]){
  const h=harness();h.queue(currentPath,response(ready()));const document=documentPort(),app=mountBirthForm(document,{apiClient:h.apiClient,clock:h.clock});await app.ready;
  const date=document.getElementById("birth-date"),edit=document.getElementById("birth-edit");
  edit.click();date.value="1990-01-01";date.emit("input");app.form.acknowledge(true);
  const pending=deferred();h.queue(buildPath,pending.promise);const work=app.session.submit();
  date.value="2000-01-01";date.emit("input");if(revert){date.value="1990-01-01";date.emit("input")}
  if(mode==="already_applied"){
   const b=ready();b.birth.birth_date="1990-01-01";h.queue(currentPath,response(b));
   pending.resolve(response({status:"already_applied",state_version:2}));
  }else pending.resolve(response(committed()));await work;
  assert.equal(document.getElementById("birth-editor").hidden,revert);
  assert.match(document.getElementById("chart-birth-summary").textContent,/1990-01-01/);
  edit.click();app.session.clearFieldError("time");
  assert.equal(document.getElementById("birth-editor").hidden,!revert);
  app.dispose();
 }
});
