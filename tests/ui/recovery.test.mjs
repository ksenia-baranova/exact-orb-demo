// REQ-UI-03/08/09, AS-UI-12/13/14/16/23, DP-UI-09 @ ce25dd0/64934fc.
// docs/requirements/changes/ui-birth-form-and-facts/{requirements,scenarios}.md.
// Настоящий coordinator/transport/form; controlled responses и fake clock, без sleep.
import assert from "node:assert/strict";
import { test } from "node:test";
import { planRecovery, recoveredStatus, recoveryMessage } from "../../src/exact_orb/http_api/ui/recovery.mjs";
import { createBirthForm } from "../../src/exact_orb/http_api/ui/form.mjs";
import { createApiClient } from "../../src/exact_orb/http_api/ui/transport.mjs";
import { createSessionCoordinator } from "../../src/exact_orb/http_api/ui/session.mjs";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { charts, views, place, ready, committed, response, failure, deferred, harness, bootstrapPath, currentPath, buildPath } from "./fixtures/session.mjs";

const intent = () => ({ birth_date: "1985-09-02", birth_time: "14:30", place_id: place.place_id });
function currentFor(input = intent(), identity = "chart-A", stateVersion = 1) {
  const view = ready(false, input.birth_time === null);
  view.birth.birth_date = input.birth_date; view.birth.birth_time = input.birth_time;
  view.birth.place.place_id = input.place_id; view.chart.chart_identity = identity; view.state_version = stateVersion;
  return view;
}
const rejection = () => new Error("Response lost before HTTP status");

test("policy distinguishes received failures, missing headers and ordinary HTTP refusal", () => {
  const network = planRecovery({ kind: "network_error" }, intent(), null);
  assert.equal(network.kind, "network"); assert.equal(network.retryAfter, null);
  assert.equal(network.originalRequestId, null); assert.equal(Object.isFrozen(network.intent), true);
  const timeout = planRecovery({ kind: "http", status: 504, body: failure("BUILD_TIMEOUT"), retryAfter: "5" }, intent(), null);
  assert.equal(timeout.kind, "timeout"); assert.equal(timeout.restartConfirmed, false);
  assert.match(recoveryMessage(timeout), /перезапуск/);
  const commit = planRecovery({ kind: "http", status: 503, body: failure("STATE_COMMIT_FAILED"), retryAfter: "1" }, intent(), null);
  assert.equal(commit.kind, "commit_failed"); assert.equal(commit.retryAfter, "1");
  assert.equal(planRecovery({ kind: "http", status: 503, body: failure("BUILD_CAPACITY_EXHAUSTED") }, intent(), null), null);
});

test("current relation uses birth intent and identity, never bootstrap state_version", () => {
  const planned = planRecovery({ kind: "network_error" }, intent(), currentFor({ ...intent(), birth_date: "1970-01-01" }, "old"));
  assert.equal(recoveredStatus(planned, currentFor()), "matched");
  assert.equal(recoveredStatus(planned, currentFor({ ...intent(), birth_date: "1970-01-01" }, "old")), "old_or_empty");
  assert.equal(recoveredStatus(planned, currentFor({ ...intent(), birth_date: "1990-01-01" }, "B", 99)), "different");
  assert.equal(recoveredStatus(planned, views.empty), "old_or_empty");
  const unknown = { ...intent(), birth_time: null }, unknownPlan = planRecovery({ kind: "network_error" }, unknown, null);
  assert.equal(recoveredStatus(unknownPlan, currentFor(unknown)), "matched");
  assert.equal(recoveredStatus(unknownPlan, currentFor()), "different");
});

test("lost build response automatically checks bootstrap/current and shows a committed matching map", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, rejection()); h.queue(currentPath, response(currentFor(), 200, { "X-Request-ID": "check-A" }));
  const draft = h.form.snapshot(); await h.coordinator.submit();
  assert.equal(h.calls.length, 5, "one build must be followed by bootstrap/current");
  const state = h.coordinator.snapshot();
  assert.equal(state.source, "current"); assert.equal(state.view.chart.chart_identity, "chart-A");
  assert.equal(state.recovery.status, "matched"); assert.equal(state.requiresReconciliation, false);
  assert.equal(state.recovery.retryAfter, null); assert.equal(state.recovery.checkRequestId, "check-A");
  assert.deepEqual(h.form.snapshot(), draft); assert.equal(h.builds().length, 1);
  assert.ok(h.changes.some((change) => change.recovery?.message?.includes("Не удалось получить ответ")));
});

for (const initial of [views.empty, currentFor({ ...intent(), birth_date: "1970-01-01" }, "old")]) {
  test(`lost response with ${initial.status} permits only a gated explicit retry after successful check`, async () => {
    const h = harness(); h.queue(currentPath, response(initial)); await h.coordinator.open();
    h.queue(buildPath, rejection()); h.queue(currentPath, response(initial)); await h.coordinator.submit();
    assert.equal(h.calls.length, 5, "successful read-only reconciliation must run");
    let state = h.coordinator.snapshot(); assert.equal(state.recovery.status, "old_or_empty");
    assert.equal(state.requiresReconciliation, false); assert.equal(state.canSubmit, true);
    assert.match(state.recovery.message, /предыдущий расчёт может завершиться позже/);
    h.form.acknowledge(false); assert.equal(await h.coordinator.submit(), false); assert.equal(h.builds().length, 1);
    h.form.acknowledge(true); assert.equal(await h.coordinator.submit(), true); assert.equal(h.builds().length, 2);
    assert.deepEqual(h.builds()[0].body, h.builds()[1].body);
  });
}

for (const failedAt of [bootstrapPath, currentPath]) {
  test(`a failed ${failedAt} recovery preserves draft/confirmed map and blocks build until safe retry succeeds`, async () => {
    const h = harness(), old = currentFor({ ...intent(), birth_date: "1970-01-01" }, "old");
    h.queue(currentPath, response(old)); await h.coordinator.open(); const draft = h.form.snapshot();
    h.queue(buildPath, rejection()); h.queue(failedAt, response(failure("STATE_READ_FAILED"), 503, { "Retry-After": "2" }));
    await h.coordinator.submit();
    assert.ok(h.calls.length > 3, "safe reconciliation must actually execute");
    assert.equal(h.coordinator.snapshot().recovery.status, "check_failed");
    assert.equal(h.coordinator.snapshot().canSubmit, false); assert.deepEqual(h.coordinator.snapshot().view, old);
    assert.deepEqual(h.form.snapshot(), draft); assert.equal(await h.coordinator.submit(), false);
    assert.equal(await h.coordinator.recheck(), false);
    const failedCalls = h.calls.length; await h.clock.advance(2000); const count = h.calls.length;
    assert.equal(count, failedCalls, "failed safe check must not start an automatic retry loop");
    assert.equal(h.builds().length, 1); h.queue(currentPath, response(currentFor()));
    assert.equal(await h.coordinator.recheck(), true); assert.ok(h.calls.length > count);
    assert.equal(h.coordinator.snapshot().recovery.status, "matched"); assert.equal(h.builds().length, 1);
  });
}

test("STATE_COMMIT_FAILED waits exact Retry-After then reads only current with separate request identity", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, response(failure("STATE_COMMIT_FAILED"), 503, { "Retry-After": "1", "X-Request-ID": "post-1" }));
  h.queue(currentPath, response(currentFor(), 200, { "X-Request-ID": "current-2" }));
  await h.coordinator.submit(); assert.equal(h.calls.length, 3);
  await h.clock.advance(999); assert.equal(h.calls.length, 3); assert.equal(await h.coordinator.submit(), false);
  await h.clock.advance(1);
  assert.equal(h.calls.length, 4, "expiry performs one safe GET, never bootstrap or POST");
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, currentPath]);
  const state = h.coordinator.snapshot(); assert.equal(state.recovery.status, "matched");
  assert.equal(state.recovery.originalRequestId, "post-1"); assert.equal(state.recovery.checkRequestId, "current-2");
  assert.equal(h.builds().length, 1);
});

test("BUILD_TIMEOUT needs explicit restart confirmation and successful safe read; expiry never probes health", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, response(failure("BUILD_TIMEOUT"), 504, { "Retry-After": "5" })); await h.coordinator.submit();
  assert.ok(h.coordinator.snapshot().recovery, "timeout must retain its distinct policy");
  assert.equal(h.coordinator.snapshot().recovery.kind, "timeout");
  await h.clock.advance(5000); assert.equal(h.calls.length, 3);
  assert.equal(await h.coordinator.foreground(), false); assert.equal(await h.coordinator.recheck(), false);
  assert.equal(await h.coordinator.submit(), false);
  h.queue(bootstrapPath, response(failure("SERVICE_SHUTTING_DOWN"), 503, { "Retry-After": "30" }));
  assert.equal(await h.coordinator.recheck({ restartConfirmed: true }), false);
  assert.equal(h.coordinator.snapshot().canSubmit, false);
  await h.clock.advance(30000); assert.equal(h.builds().length, 1);
  h.queue(currentPath, response(views.empty)); assert.equal(await h.coordinator.recheck({ restartConfirmed: true }), true);
  assert.equal(h.coordinator.snapshot().canSubmit, true);
  assert.ok(h.calls.every((call) => !call.path.startsWith("/health")));
  assert.equal(await h.coordinator.submit(), true); assert.equal(h.builds().length, 2);
});

test("recovery stores immutable first intent while draft edits and a later POST have their own snapshot", async () => {
  const h = harness(); await h.coordinator.open();
  const check = deferred(); h.queue(buildPath, rejection()); h.queue(currentPath, check.promise);
  const entered = h.entered(bootstrapPath); const submitting = h.coordinator.submit();
  // Вход в листовую сеть доказывает начало recovery без предположений о задержках.
  const bootstrapObserved = await Promise.race([entered.then(() => true), submitting.then(() => false)]);
  assert.equal(bootstrapObserved, true, "failed build must enter safe bootstrap");
  h.form.setDate("1990-01-01"); h.form.setTime("00:00");
  assert.deepEqual(h.coordinator.snapshot().submittedIntent, intent());
  assert.equal(await h.coordinator.submit(), false);
  check.resolve(response(views.empty)); await submitting;
  assert.equal(h.form.snapshot().date, "1990-01-01");
  await h.coordinator.submit();
  assert.deepEqual(h.builds()[1].body, { ...intent(), birth_date: "1990-01-01", birth_time: "00:00" });
  assert.deepEqual(h.builds()[0].body, intent());
});

test("foreground arriving during a build is coalesced and reads only after its committed response", async () => {
  const h = harness(); await h.coordinator.open();
  const pending = deferred(); h.queue(buildPath, pending.promise); h.queue(currentPath, response(currentFor(intent(), "B", 2)));
  const submitting = h.coordinator.submit();
  assert.equal(await h.coordinator.foreground(), false); assert.equal(await h.coordinator.foreground(), false);
  assert.equal(h.calls.length, 3);
  pending.resolve(response(committed({ ...charts.natal, chart_identity: "B" }))); await submitting;
  assert.equal(h.calls.length, 5, "one queued foreground performs bootstrap/current after build");
  assert.equal(h.coordinator.snapshot().view.chart.chart_identity, "B"); assert.equal(h.builds().length, 1);
});

test("dispose cancels scheduled recovery without claiming server cancellation", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, response(failure("STATE_COMMIT_FAILED"), 503, { "Retry-After": "1" })); await h.coordinator.submit();
  assert.ok(h.coordinator.snapshot().recovery, "timer must belong to an actual recovery policy");
  h.coordinator.dispose(); await h.clock.advance(1000);
  assert.equal(h.calls.length, 3); assert.equal(await h.coordinator.recheck(), false);
});

test("commit check encountering SESSION_REQUIRED has one bounded bootstrap/current recovery", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, response(failure("STATE_COMMIT_FAILED"), 503, { "Retry-After": "1" }));
  h.queue(currentPath, response(failure("SESSION_REQUIRED"), 409), response(failure("SESSION_EXPIRED"), 409));
  await h.coordinator.submit(); await h.clock.advance(1000);
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, currentPath, bootstrapPath, currentPath]);
  assert.equal(h.coordinator.snapshot().recovery.status, "check_failed");
  assert.equal(await h.coordinator.submit(), false); assert.equal(h.builds().length, 1);
  const count = h.calls.length; await h.clock.advance(100000); assert.equal(h.calls.length, count);
  h.queue(currentPath, response(views.empty)); assert.equal(await h.coordinator.recheck(), true);
  assert.equal(await h.coordinator.submit(), true); assert.equal(h.builds().length, 2);
});

test("interrupted response body retains real headers and delay without inventing an ErrorDTO", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, { status: 503, headers: new Headers({ "Retry-After": "1", "X-Request-ID": "partial-post" }),
    text: async () => { throw rejection(); } });
  await h.coordinator.submit();
  const state = h.coordinator.snapshot();
  assert.equal(state.error.status, 503); assert.equal(state.error.code, null);
  assert.equal(state.recovery.kind, "network"); assert.equal(state.recovery.originalRequestId, "partial-post");
  assert.equal(state.recovery.retryAfter, "1"); assert.equal(h.calls.length, 3);
  await h.clock.advance(999); assert.equal(h.calls.length, 3);
  await h.clock.advance(1);
  assert.deepEqual(h.calls.slice(3).map((call) => call.path), [bootstrapPath, currentPath]);
  assert.equal(h.coordinator.snapshot().recovery.status, "old_or_empty"); assert.equal(h.builds().length, 1);
});

test("timeout matching current requires both delay and explicit external restart confirmation", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, response(failure("BUILD_TIMEOUT"), 504, { "Retry-After": "5" }));
  h.queue(currentPath, response(currentFor())); await h.coordinator.submit();
  assert.equal(await h.coordinator.recheck({ restartConfirmed: true }), false);
  assert.equal(h.coordinator.snapshot().recovery.restartConfirmed, false);
  await h.clock.advance(5000); assert.equal(h.calls.length, 3);
  assert.equal(await h.coordinator.recheck({ restartConfirmed: true }), true);
  assert.equal(h.coordinator.snapshot().recovery.status, "matched"); assert.equal(h.builds().length, 1);
  assert.deepEqual(h.calls.slice(3).map((call) => call.path), [bootstrapPath, currentPath]);
});

test("dispose during recovery aborts its read and drops queued foreground without overwriting the last map", async () => {
  const h = harness(), old = ready(), pending = deferred();
  h.queue(currentPath, response(old)); await h.coordinator.open();
  h.queue(buildPath, rejection()); h.queue(currentPath, pending.promise);
  const entered = h.entered(currentPath), submitting = h.coordinator.submit(); await entered;
  await h.coordinator.foreground(); const count = h.calls.length;
  const reading = h.calls.at(-1); assert.equal(reading.options.signal.aborted, false);
  h.coordinator.dispose(); const changes = h.changes.length;
  assert.equal(reading.options.signal.aborted, true);
  pending.resolve(response(currentFor())); await submitting;
  assert.deepEqual(h.coordinator.snapshot().view, old);
  assert.equal(h.calls.length, count); assert.equal(h.changes.length, changes);
});

// Общая листовая сеть хранит опубликованный серверный current; coordinator остаётся настоящим.
function twoTabs() {
  let current = structuredClone(views.empty), version = 0, heldBuild = null;
  const calls = [];
  function tab(name, input) {
    const form = createBirthForm(); form.setDate(input.birth_date); form.setTime(input.birth_time);
    form.selectPlace(place); form.acknowledge(true);
    const apiClient = createApiClient({ fetchFn: async (path, options) => {
      const body = options.body ? JSON.parse(options.body) : null; calls.push({ name, path, options, body });
      if (path === bootstrapPath) return response({ status: "ready", state_version: 99 });
      if (path === currentPath) return response(structuredClone(current));
      if (path === buildPath) {
        if (name === "A" && heldBuild) return heldBuild.promise;
        current = currentFor(body, `chart-${name}`, ++version);
        return response({ ...committed(current.chart), state_version: version }, 200, { "X-Request-ID": `post-${name}` });
      }
      throw new Error(`Unexpected leaf ${path}`);
    } });
    return { form, coordinator: createSessionCoordinator({ form, apiClient }) };
  }
  return { A: tab("A", intent()), B: tab("B", { ...intent(), birth_date: "1990-01-01", birth_time: "00:00" }), calls,
    holdA() { heldBuild = deferred(); return heldBuild; } };
}

test("two tabs: foreground reads B's published map while retaining A's draft and three-field request contract", async () => {
  const h = twoTabs(); await h.A.coordinator.open(); await h.B.coordinator.open();
  const draftA = h.A.form.snapshot(); await h.B.coordinator.submit();
  assert.equal(h.A.coordinator.snapshot().view.status, "empty");
  const count = h.calls.length; await h.A.coordinator.foreground();
  assert.deepEqual(h.calls.slice(count).map((call) => call.path), [bootstrapPath, currentPath]);
  assert.equal(h.A.coordinator.snapshot().source, "current");
  assert.equal(h.A.coordinator.snapshot().view.chart.chart_identity, "chart-B");
  assert.deepEqual(h.A.form.snapshot(), draftA);
  assert.equal(h.calls.filter((call) => call.path === buildPath).length, 1);
  assert.ok(h.calls.every((call) => call.options.credentials === "same-origin" && !Object.hasOwn(call.options.headers ?? {}, "Cookie")));
  await h.A.coordinator.submit();
  const postA = h.calls.filter((call) => call.name === "A" && call.path === buildPath);
  assert.equal(postA.length, 1); assert.deepEqual(postA[0].body, intent());
});

for (const outcome of ["RESULT_SUPERSEDED", "already_applied"]) {
  test(`two concurrent intents: ${outcome} shows actual B current instead of attributing it to A's POST`, async () => {
    const h = twoTabs(); await h.A.coordinator.open(); await h.B.coordinator.open();
    const pending = h.holdA(), buildingA = h.A.coordinator.submit();
    await h.B.coordinator.submit();
    pending.resolve(outcome === "already_applied" ? response({ status: outcome, state_version: 1 }) : response(failure(outcome), 409));
    await buildingA;
    const state = h.A.coordinator.snapshot();
    assert.equal(state.source, "current"); assert.equal(state.view.chart.chart_identity, "chart-B");
    assert.equal(state.view.birth.birth_date, "1990-01-01"); assert.deepEqual(state.submittedIntent, intent());
    assert.equal(h.A.form.snapshot().date, "1985-09-02");
    assert.equal(h.calls.filter((call) => call.name === "A" && call.path === buildPath).length, 1);
    assert.equal(h.calls.at(-1).path, currentPath);
  });
}

test("late first commit during the explicit second intent stays actual current, never a fabricated second artifact", async () => {
  const h = harness(); await h.coordinator.open();
  h.queue(buildPath, rejection()); await h.coordinator.submit();
  const first = h.coordinator.snapshot().recovery.intent;
  assert.equal(h.coordinator.snapshot().recovery.status, "old_or_empty");
  h.form.setDate("1990-01-01"); h.form.setTime("00:00");
  const pending = deferred(); h.queue(buildPath, pending.promise);
  const second = h.coordinator.submit();
  assert.equal(h.builds().length, 2); assert.deepEqual(h.builds()[0].body, first);
  // Первый запуск завершает protected commit; сервер возвращает superseded второму запуску.
  h.queue(currentPath, response(currentFor(first, "late-first", 1), 200, { "X-Request-ID": "late-first-read" }));
  pending.resolve(response(failure("RESULT_SUPERSEDED"), 409, { "X-Request-ID": "second-post" }));
  await second;
  const state = h.coordinator.snapshot();
  assert.equal(state.source, "current"); assert.equal(state.view.chart.chart_identity, "late-first");
  assert.equal(state.view.birth.birth_date, first.birth_date);
  assert.equal(state.submittedIntent.birth_date, "1990-01-01"); assert.equal(state.requestId, "late-first-read");
  assert.equal(h.form.snapshot().date, "1990-01-01"); assert.equal(h.builds().length, 2);
});

function mountHarness(h) {
  const document = documentPort(), ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  const get = (id) => document.getElementById(id);
  const check = ui.session.snapshot;
  return { document, ui, get, check, submit: () => get("birth-form").emit("submit"),
    gate(value) { get("terms-acknowledged").checked = value; get("terms-acknowledged").emit("change"); } };
}

test("mounted lost-response warning keeps original intent visible; edits/gate never trigger a hidden POST", async () => {
  const h = harness(); h.queue(currentPath, response(currentFor())); const m = mountHarness(h); await m.ui.ready;
  const selectedPlaceName = m.ui.form.snapshot().place.display_name;
  m.gate(true); h.queue(buildPath, rejection()); h.queue(currentPath, response(views.empty)); await m.submit();
  assert.match(m.get("session-status").textContent, /предыдущий расчёт может завершиться позже/);
  assert.equal(m.get("build-button").textContent, "Построить ещё раз");
  assert.match(m.get("submitted-intent").textContent, /1985-09-02.*14:30/);
  assert.ok(m.get("submitted-intent").textContent.includes(selectedPlaceName));
  assert.equal(m.get("birth-date").value, "1985-09-02");
  m.gate(false); await m.submit(); assert.equal(h.builds().length, 1);
  const date = m.get("birth-date"); date.value = "1990-01-01"; date.emit("input");
  assert.equal(m.get("build-button").textContent, "Построить карту");
  assert.match(m.get("submitted-intent").textContent, /1985-09-02/);
  assert.equal(h.builds().length, 1); m.gate(true); await m.submit();
  assert.equal(h.builds().length, 2); assert.equal(h.builds()[1].body.birth_date, "1990-01-01");
  m.ui.dispose();
});

test("mounted failed check offers a working safe read; timeout button explicitly confirms restart after Retry-After", async () => {
  const h = harness(); h.queue(currentPath, response(currentFor())); const m = mountHarness(h); await m.ui.ready;
  m.gate(true); h.queue(buildPath, rejection()); h.queue(bootstrapPath, response(failure("STATE_READ_FAILED"), 503));
  await m.submit(); const readAgain = m.document.root.querySelectorAll("button").find((button) => button.textContent === "Повторить проверку карты");
  assert.equal(readAgain.hidden, false); assert.equal(m.get("build-button").disabled, true);
  h.queue(currentPath, response(views.empty)); await readAgain.click();
  assert.equal(m.get("build-button").disabled, false); assert.equal(h.builds().length, 1);
  h.queue(buildPath, response(failure("BUILD_TIMEOUT"), 504, { "Retry-After": "5" })); await m.submit();
  assert.equal(readAgain.textContent, "Проверить после перезапуска"); assert.equal(readAgain.disabled, true);
  await readAgain.click(); assert.equal(m.check().recovery.restartConfirmed, false);
  await h.clock.advance(5000); assert.equal(readAgain.disabled, false);
  h.queue(currentPath, response(currentFor())); await readAgain.click();
  assert.equal(m.check().recovery.restartConfirmed, true); assert.equal(m.check().recovery.status, "matched");
  assert.equal(h.builds().length, 2); assert.equal(readAgain.hidden, true); m.ui.dispose();
});

test("mounted lost response with a different current shows it separately from the original intent and editable draft", async () => {
  const h = harness(); h.queue(currentPath, response(currentFor())); const m = mountHarness(h); await m.ui.ready;
  m.gate(true); const draft = m.ui.form.snapshot();
  h.queue(buildPath, rejection()); h.queue(currentPath, response(currentFor({ ...intent(), birth_date: "1990-01-01" }, "chart-B", 2)));
  await m.submit();
  assert.equal(m.check().source, "current"); assert.equal(m.check().view.chart.chart_identity, "chart-B");
  assert.equal(m.check().recovery.status, "different");
  assert.match(m.get("session-status").textContent, /актуальная карта с другими данными/);
  assert.deepEqual(m.check().recovery.intent, intent()); assert.equal(Object.isFrozen(m.check().recovery.intent), true);
  assert.match(m.get("submitted-intent").textContent, /1985-09-02/);
  assert.equal(m.get("birth-date").value, "1985-09-02"); assert.deepEqual(m.ui.form.snapshot(), draft);
  assert.equal(h.builds().length, 1); m.ui.dispose();
});

test("mounted visibility/online are readonly, coalesce during build, preserve draft and unsubscribe on dispose", async () => {
  const h = harness(); h.queue(currentPath, response(currentFor())); const m = mountHarness(h); await m.ui.ready;
  const date = m.get("birth-date"); date.value = "2000-02-29"; date.emit("input");
  const count = h.calls.length; m.document.visibilityState = "hidden"; await m.document.emit("visibilitychange");
  assert.equal(h.calls.length, count);
  h.queue(currentPath, response(currentFor({ ...intent(), birth_date: "1990-01-01" }, "B")));
  m.document.visibilityState = "visible"; await m.document.emit("visibilitychange");
  assert.equal(m.check().view.chart.chart_identity, "B"); assert.equal(date.value, "2000-02-29");
  assert.equal(h.builds().length, 0);
  m.gate(true); const pending = deferred(); h.queue(buildPath, pending.promise); const submitting = m.submit();
  await m.document.defaultView.emit("online"); await m.document.emit("visibilitychange"); const duringBuild = h.calls.length;
  pending.resolve(response(committed())); h.queue(currentPath, response(currentFor())); await submitting;
  assert.equal(h.calls.length, duringBuild + 2); assert.equal(h.builds().length, 1);
  assert.equal(date.value, "2000-02-29"); m.ui.dispose(); const finalCount = h.calls.length;
  await m.document.defaultView.emit("online"); await m.document.emit("visibilitychange");
  assert.equal(h.calls.length, finalCount);
});
