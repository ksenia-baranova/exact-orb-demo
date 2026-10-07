// REQ-UI-01/03/08/09, AS-UI-01/03/04/06/10/11/12/16/17/20/21.
// Контракт: docs/requirements/changes/ui-birth-form-and-facts/{requirements,scenarios}.md @ ce25dd0.
// Настоящие form/session/transport; заменена только листовая сеть, ожидание управляется Promise.
import assert from "node:assert/strict";
import { test } from "node:test";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { documentPort } from "./fixtures/dom.mjs";

import { charts, views, place, placeWithoutRegion, ready, committed, response, failure, deferred, harness,
  bootstrapPath, currentPath, buildPath } from "./fixtures/session.mjs";

function mountSession(h) {
  const document = documentPort(), ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  const get = (id) => document.getElementById(id);
  return { document, ui, get, submit: () => get("birth-form").emit("submit"),
    gate(value) { get("terms-acknowledged").checked = value; get("terms-acknowledged").emit("change"); } };
}

// DEV-UI-08, TEST-FIND-UI-010; REQ-UI-03/08 / AS-UI-03/04/10/22.
for (const unknown of [false, true]) {
  test(`committed ${unknown ? "unknown" : "known"} time summary belongs to the submitted snapshot despite pending draft edits`, async () => {
    const h = harness(); h.queue(currentPath, response(ready())); const m = mountSession(h); await m.ui.ready;
    m.get("time-unknown").checked = unknown; m.get("time-unknown").emit("change"); m.gate(true);
    const sent = m.ui.form.prepareSubmission().intent, sentPlace = m.get("birth-place").value;
    const pending = deferred(); h.queue(buildPath, pending.promise); const submitting = m.submit();
    m.get("birth-date").value = "1990-01-01"; m.get("birth-date").emit("input");
    m.get("birth-time").value = "00:00"; m.get("birth-time").emit("input");
    m.ui.form.selectPlace(placeWithoutRegion); const draft = m.ui.form.snapshot();
    pending.resolve(response(committed(charts[unknown ? "cosmogram" : "natal"]))); await submitting;
    const text = m.get("session-status").textContent;
    assert.ok(text.includes(sent.birth_date)); assert.ok(text.includes(sentPlace));
    assert.match(text, unknown ? /Точное время неизвестно/ : /Время: 14:30/);
    assert.doesNotMatch(text, /1990-01-01|00:00|Гонконг|12:00|undefined/);
    assert.deepEqual(m.ui.form.snapshot(), draft); assert.deepEqual(h.builds()[0].body, sent);
    assert.equal(m.ui.session.snapshot().view.birth, null, "summary must not fabricate timezone/offset/warnings DTO");
    assert.equal(h.calls.length, 3, "no extra GET just to build a summary");
    // Сводка не меняется от последующих событий редактирования и caller snapshots.
    m.get("birth-date").value = "2000-02-29"; m.get("birth-date").emit("input");
    assert.equal(m.get("session-status").textContent, text); m.ui.dispose();
  });
}

test("a rejected later build keeps the summary of the previously displayed committed chart", async () => {
  const h = harness(); h.queue(currentPath, response(ready())); const m = mountSession(h); await m.ui.ready; m.gate(true);
  await m.submit(); const shown = m.get("session-status").textContent;
  m.get("birth-date").value = "1990-01-01"; m.get("birth-date").emit("input");
  h.queue(buildPath, response(failure("INPUT_REQUIRED"), 422)); await m.submit();
  assert.equal(m.get("session-status").textContent, shown);
  assert.ok(shown.includes(ready().birth.birth_date)); assert.doesNotMatch(shown, /1990-01-01/);
  assert.equal(h.builds().length, 2); m.ui.dispose();
});

test("foreground summary reads actual current birth instead of a previous successful build intent", async () => {
  const h = harness(); h.queue(currentPath, response(ready())); const m = mountSession(h); await m.ui.ready; m.gate(true);
  await m.submit(); const actual = ready(false, true); actual.birth.birth_date = "1990-01-01";
  h.queue(currentPath, response(actual)); await m.document.defaultView.emit("online");
  const text = m.get("session-status").textContent;
  assert.match(text, /1990-01-01/); assert.match(text, /Точное время неизвестно/); assert.doesNotMatch(text, /1985-09-02|14:30/);
  assert.equal(m.ui.session.snapshot().view.chart.chart_identity, actual.chart.chart_identity);
  assert.equal(m.get("birth-date").value, ready().birth.birth_date); assert.equal(h.builds().length, 1); m.ui.dispose();
});

// TEST-FIND-UI-012; REQ-UI-02/08/10 / AS-UI-02/10/19: только edit снимает ID.
for (const saved of [ready(), ready(false, true), views.known_unavailable]) {
  test(`restored ${saved.status}/${saved.birth.time_unknown} place survives focus/blur then edit and explicit new selection`, async () => {
    const h = harness(); h.queue(currentPath, response(saved)); const m = mountSession(h); await m.ui.ready;
    const input = m.get("birth-place"), status = m.get("place-status"), label = status.textContent;
    input.focus(); input.emit("focus"); assert.equal(status.textContent, label);
    input.emit("blur"); assert.equal(status.textContent, label); assert.doesNotMatch(label, /undefined/);
    assert.equal(m.ui.form.snapshot().place.place_id, saved.birth.place.place_id);
    assert.equal(h.calls.length, 2, "focus/blur do not fetch missing catalogue metadata");
    input.value = "Гонк"; input.emit("input");
    assert.equal(m.ui.form.snapshot().place, null); assert.ok(!status.textContent.includes(saved.birth.place.display_name));
    m.gate(true); await m.submit(); assert.equal(h.builds().length, 0);
    h.queue("/places?query=" + encodeURIComponent("Гонк"), response({ items: [placeWithoutRegion] }));
    await h.clock.advance(250); m.ui.places.select(0);
    input.emit("focus"); input.emit("blur"); assert.match(status.textContent, /Гонконг/); assert.doesNotMatch(status.textContent, /undefined/);
    await m.submit(); assert.equal(h.builds().length, 1); assert.equal(h.builds()[0].body.place_id, placeWithoutRegion.place_id);
    m.ui.dispose();
  });
}

// DEV-UI-07, REQ-UI-02/03/10, AS-UI-02/18/19/20; TEST-FIND-UI-005.
test("mounted nullable-region selection renders a dash and sends only the selected ID after the gate", async () => {
  const h = harness(), document = documentPort();
  h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
  const path = "/places?query=" + encodeURIComponent("Гонк");
  h.queue(path, response({ items: [placeWithoutRegion, place] }));
  const input = document.getElementById("birth-place"); input.focus(); input.value = "Гонк";
  input.emit("input"); await h.clock.advance(250);
  const options = document.getElementById("place-list").children;
  assert.equal(options.length, 2);
  assert.match(options[0].textContent, /Регион: — · Страна: HK/);
  assert.ok(options[1].textContent.includes(place.admin1_name));
  ui.places.select(0);
  assert.match(document.getElementById("place-status").textContent, /Регион: —/);
  await document.getElementById("birth-form").emit("submit"); assert.equal(h.builds().length, 0);
  const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds().length, 1);
  assert.equal(h.builds()[0].body.place_id, placeWithoutRegion.place_id);
  assert.deepEqual(Object.keys(h.builds()[0].body).sort(), ["birth_date", "birth_time", "place_id"]);
  ui.dispose();
});

// REQ-UI-03/08/09/10, AS-UI-15/17/23; TEST-FIND-UI-011.
const damagedCharts = [
  ["points null", (chart) => { chart.points = null; }],
  ["point null", (chart) => { chart.points[0] = null; }],
  ["point degree outside range", (chart) => { chart.points[0].degree = 30; }],
  ["point minute wrong type", (chart) => { chart.points[0].minute = "15"; }],
  ["point retrograde wrong type", (chart) => { chart.points[0].retrograde = "false"; }],
  ["houses not array", (chart) => { chart.houses = {}; }],
  ["house null", (chart) => { chart.houses[0] = null; }],
  ["missing angle", (chart) => { delete chart.angles.asc; }],
  ["aspects null", (chart) => { chart.aspects = null; }],
  ["aspect null", (chart) => { chart.aspects[0] = null; }],
  ["aspect orb wrong type", (chart) => { chart.aspects[0].orb = "1"; }],
];
for (const [name, damage] of damagedCharts) {
  test(`malformed POST ${name} preserves the confirmed view and reconciles without a second POST`, async () => {
    const h = harness(), document = documentPort(), saved = ready();
    h.queue(currentPath, response(saved));
    const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
    ui.form.acknowledge(true); const draft = ui.form.snapshot();
    const bad = structuredClone(charts.natal); damage(bad);
    h.queue(buildPath, response(committed(bad), 200, { "X-Request-ID": "bad-post" }));
    h.queue(currentPath, response(failure("STATE_READ_FAILED"), 503, { "X-Request-ID": "failed-check" }));
    await assert.doesNotReject(() => document.getElementById("birth-form").emit("submit"));
    const state = ui.session.snapshot();
    assert.equal(state.recovery?.kind, "unconfirmed_response");
    assert.equal(state.recovery.status, "check_failed");
    assert.equal(state.recovery.originalRequestId, "bad-post");
    assert.equal(state.recovery.checkRequestId, "failed-check");
    assert.equal(state.canSubmit, false); assert.equal(state.busy, false);
    assert.deepEqual(state.view, saved); assert.deepEqual(ui.form.snapshot(), draft);
    assert.ok(document.getElementById("form-error").textContent);
    assert.equal(h.builds().length, 1);
    assert.deepEqual(h.calls.map((call) => call.path),
      [bootstrapPath, currentPath, buildPath, bootstrapPath, currentPath]);
    h.queue(currentPath, response(saved)); assert.equal(await ui.session.recheck(), true);
    assert.equal(ui.session.snapshot().canSubmit, true, "valid current recovers availability");
    assert.equal(h.builds().length, 1); ui.dispose();
  });
}
for (const [name, damage] of [
  ["points null", (view) => { view.chart.points = null; }],
  ["birth time wrong format", (view) => { view.birth.birth_time = "0045"; }],
  ["place ID wrong type", (view) => { view.birth.place.place_id = 42; }],
  ["cosmogram with houses", (view) => { view.chart.kind = "cosmogram"; }],
]) {
  test(`malformed foreground current ${name} cannot replace the confirmed view`, async () => {
    const h = harness(), document = documentPort(), saved = ready();
    h.queue(currentPath, response(saved));
    const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
    const draft = ui.form.snapshot(), bad = structuredClone(saved); damage(bad);
    h.queue(currentPath, response(bad, 200, { "X-Request-ID": "bad-current" }));
    await assert.doesNotReject(() => document.defaultView.emit("online"));
    const state = ui.session.snapshot();
    assert.deepEqual(state.view, saved); assert.deepEqual(ui.form.snapshot(), draft);
    assert.equal(state.busy, false); assert.equal(state.canSubmit, false);
    assert.equal(state.error.requestId, "bad-current");
    assert.ok(document.getElementById("form-error").textContent);
    assert.equal(h.builds().length, 0);
    h.queue(currentPath, response(saved)); assert.equal(await ui.session.recheck(), true);
    assert.equal(ui.session.snapshot().error, null); ui.dispose();
  });
}

test("malformed bootstrap is visible, blocks current/build and can be safely retried", async () => {
  const h = harness(), document = documentPort();
  h.queue(bootstrapPath, response({ status: "ready", state_version: "1" }));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  assert.equal(await ui.ready, false);
  assert.equal(ui.session.snapshot().canSubmit, false);
  assert.ok(document.getElementById("form-error").textContent);
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath]);
  assert.equal(await ui.session.recheck(), true);
  assert.equal(ui.session.snapshot().view.status, "empty"); ui.dispose();
});

test("malformed issue candidates do not reject the mounted submission handler", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
  ui.form.acknowledge(true);
  h.queue(buildPath, response(failure("INPUT_REQUIRED",
    [{ field: "birth.time", code: "INVALID", candidates: { length: 1 } }]), 422));
  await assert.doesNotReject(() => document.getElementById("birth-form").emit("submit"));
  assert.ok(document.getElementById("form-error").textContent);
  assert.equal(ui.session.snapshot().error.status, 422);
  assert.equal(ui.session.snapshot().requiresReconciliation, false);
  assert.equal(ui.session.snapshot().busy, false); assert.equal(h.builds().length, 1); ui.dispose();
});

for (const action of ["open", "foreground", "submit"]) {
  test(`unexpected renderer failure during ${action} becomes a visible safe-read-only error`, async () => {
    const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
    const originalCreate = document.createElement;
    const breakRenderer = () => {
      document.createElement = () => { throw new Error("controlled DOM failure"); };
    };
    // mount creates the result skeleton before open; damage only the dynamic table renderer.
    const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
    if (action === "open") breakRenderer();
    else {
      await ui.ready; ui.form.acknowledge(true);
      const next = ready(); next.chart.chart_identity += "-new";
      h.queue(action === "foreground" ? currentPath : buildPath,
        response(action === "foreground" ? next : committed(next.chart)));
      breakRenderer();
    }
    const operation = action === "open" ? ui.ready : action === "foreground"
      ? document.defaultView.emit("online") : document.getElementById("birth-form").emit("submit");
    await assert.doesNotReject(() => operation);
    assert.equal(ui.session.snapshot().busy, false); assert.equal(ui.session.snapshot().canSubmit, false);
    assert.match(document.getElementById("form-error").textContent, /показать|отобразить|обновить/i);
    assert.equal(document.getElementById("birth-form").getAttribute("aria-busy"), "false");
    document.createElement = originalCreate;
    h.queue(currentPath, response(ready())); assert.equal(await ui.session.recheck(), true);
    assert.equal(ui.session.snapshot().error, null);
    assert.equal(document.getElementById("chart-facts").querySelectorAll("table").length, 4);
    ui.dispose();
  });
}

test("renderer fallback preserves the BUILD_TIMEOUT restart confirmation and Retry-After gate", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
  ui.form.acknowledge(true);
  const element = document.getElementById("birth-form"), originalSet = element.setAttribute;
  let fail = true;
  element.setAttribute = (name, value) => {
    if (fail && name === "aria-busy" && value === "false") {
      fail = false; throw new Error("controlled render failure after timeout");
    }
    return originalSet(name, value);
  };
  h.queue(buildPath, response(failure("BUILD_TIMEOUT"), 504, { "Retry-After": "5" }));
  await assert.doesNotReject(() => element.emit("submit"));
  assert.ok(document.root.querySelectorAll("button").some((node) => node.textContent === "Проверить после перезапуска"));
  assert.equal(ui.session.snapshot().recovery.restartConfirmed, false);
  assert.equal(await ui.session.recheck({ restartConfirmed: true }), false);
  await h.clock.advance(5000);
  assert.equal(await ui.session.recheck(), false);
  assert.equal(h.calls.length, 3, "neither renderer fallback nor cooldown confirms server restart");
  h.queue(currentPath, response(ready()));
  assert.equal(await ui.session.recheck({ restartConfirmed: true }), true);
  assert.equal(h.calls.length, 5); assert.equal(h.builds().length, 1); ui.dispose();
});

test("bootstrap ready/version never supplies a chart; current determines empty without build", async () => {
  const h = harness(), boot = deferred();
  h.queue(bootstrapPath, boot.promise);
  const opening = h.coordinator.open();
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath]);
  assert.equal(h.coordinator.snapshot().view, null);
  boot.resolve(response({ status: "ready", state_version: 99 }));
  assert.equal(await opening, true);
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath]);
  assert.deepEqual(h.calls[0].body, {});
  assert.deepEqual(h.coordinator.snapshot().view, views.empty);
  assert.equal(h.builds().length, 0);
  assert.ok(h.calls.every((call) => call.options.credentials === "same-origin" && call.options.cache === "no-store"));
});

test("explicit build has one immutable three-field intent; double click cannot create another POST", async () => {
  const h = harness(); await h.coordinator.open();
  const pending = deferred(); h.queue(buildPath, pending.promise);
  const first = h.coordinator.submit(), second = h.coordinator.submit();
  assert.equal(h.builds().length, 1);
  const intent = h.coordinator.snapshot().submittedIntent;
  assert.equal(Object.isFrozen(intent), true);
  assert.deepEqual(intent, { birth_date: "1985-09-02", birth_time: "14:30", place_id: place.place_id });
  h.form.setDate("1990-01-01"); h.form.setTime("00:00");
  assert.deepEqual(h.builds()[0].body, intent);
  assert.equal(await second, false);
  pending.resolve(response(committed()));
  assert.equal(await first, true);
  assert.equal(h.coordinator.snapshot().view.chart.chart_identity, charts.natal.chart_identity);
  assert.equal(h.form.snapshot().date, "1990-01-01");
  assert.equal(h.coordinator.snapshot().phase, "idle");
});

test("no build before successful bootstrap/current or manual gate; explicit valid control succeeds", async () => {
  const h = harness();
  assert.equal(await h.coordinator.submit(), false);
  assert.equal(h.builds().length, 0);
  await h.coordinator.open(); h.form.acknowledge(false);
  assert.equal(await h.coordinator.submit(), false);
  assert.ok(h.form.snapshot().errors.acknowledged);
  assert.equal(h.builds().length, 0);
  h.form.acknowledge(true);
  assert.equal(await h.coordinator.submit(), true);
  assert.equal(h.builds().length, 1);
});

test("unknown time reaches real transport as null and returns the published cosmogram", async () => {
  const h = harness(); await h.coordinator.open(); h.form.setUnknownTime(true);
  h.queue(buildPath, response(committed(charts.cosmogram)));
  assert.equal(await h.coordinator.submit(), true);
  assert.equal(h.builds()[0].body.birth_time, null);
  assert.deepEqual(h.coordinator.snapshot().view.chart, charts.cosmogram);
  assert.equal(h.form.snapshot().time, "14:30");
});

test("server time AMBIGUOUS remains a field issue with candidates; draft and previous chart survive", async () => {
  const h = harness(); h.queue(currentPath, response(ready())); await h.coordinator.open();
  const draft = h.form.snapshot();
  h.queue(buildPath, response(failure("INPUT_REQUIRED", [{ field: "birth.time", code: "AMBIGUOUS", candidates: [0, 3600] }]), 422));
  assert.equal(await h.coordinator.submit(), false);
  const state = h.coordinator.snapshot();
  assert.equal(state.fieldIssues.time[0].code, "AMBIGUOUS");
  assert.deepEqual(state.fieldIssues.time[0].candidates, [0, 3600]);
  assert.equal(state.error.userMessage, "Проверьте введённые данные.");
  assert.deepEqual(h.form.snapshot(), draft);
  assert.deepEqual(state.view, ready());
  h.form.setTime("00:00"); h.coordinator.clearFieldError("time");
  assert.equal(h.coordinator.snapshot().fieldIssues.time, undefined);
  assert.equal(await h.coordinator.submit(), true);
  assert.equal(h.builds()[1].body.birth_time, "00:00");
});

test("date/place issues retain constraints; unknown fields and user_message have a general fallback", async () => {
  const h = harness(); await h.coordinator.open();
  const issues = [{ field: "birth.date", code: "UNSUPPORTED", constraints: { min_year: 1900 } },
    { field: "birth.place", code: "INVALID" }, { field: "request.future", code: "UNSUPPORTED" }];
  h.queue(buildPath, response(failure("INVALID_REQUEST", issues), 422));
  assert.equal(await h.coordinator.submit(), false);
  const state = h.coordinator.snapshot();
  assert.deepEqual(state.fieldIssues.date[0].constraints, { min_year: 1900 });
  assert.equal(state.fieldIssues.place[0].field, "birth.place");
  assert.deepEqual(state.error.generalIssues, [issues[2]]);
  assert.ok(state.error.message.includes("Проверьте введённые данные."));
});

for (const result of ["already_applied", "RESULT_SUPERSEDED"]) {
  test(`${result} reads actual current and never treats the POST as a new chart`, async () => {
    // TEST-FIND-UI-010; REQ-UI-08/09 / AS-UI-10/16: сводка actual birth, не intent проигравшего POST.
    const h = harness(); h.queue(currentPath, response(ready())); const m = mountSession(h); await m.ui.ready; m.gate(true);
    const winner = ready(true); winner.chart.chart_identity = "persisted-winner";
    winner.birth.birth_date = "1990-01-01"; winner.birth.birth_time = "00:00";
    winner.birth.place.display_name = "Другое сохранённое место";
    h.queue(currentPath, response(winner));
    h.queue(buildPath, result === "already_applied" ? response({ status: result, state_version: 3 })
      : response(failure(result), 409));
    await m.submit(); assert.deepEqual(m.ui.session.snapshot().view, winner);
    assert.match(m.get("session-status").textContent, /1990-01-01.*Другое сохранённое место.*00:00/);
    assert.doesNotMatch(m.get("session-status").textContent, /1985-09-02|14:30/);
    assert.equal(m.get("birth-date").value, ready().birth.birth_date);
    assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, currentPath]);
    assert.equal(h.builds().length, 1); m.ui.dispose();
  });
}

for (const code of ["SESSION_REQUIRED", "SESSION_EXPIRED", "SESSION_NOT_FOUND"]) {
 for (const current of [views.empty, ready()]) {
  test(`${code} recovers ${current.status} with visible new-action explanation and intact draft`, async () => {
    // TEST-FIND-UI-008; REQ-UI-03/09/10 / AS-UI-12/19.
    const h = harness(); h.queue(currentPath, response(ready())); const m = mountSession(h); await m.ui.ready; m.gate(true);
    const draft = m.ui.form.snapshot(); h.queue(currentPath, response(current));
    h.queue(buildPath, response(failure(code), 409));
    await m.submit();
    assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, bootstrapPath, currentPath]);
    assert.equal(h.builds().length, 1);
    assert.deepEqual(m.ui.session.snapshot().view, current); assert.deepEqual(m.ui.form.snapshot(), draft);
    assert.match(m.get("session-status").textContent, /Сессия обновлена.*построения.*отклонён.*нажмите/);
    m.gate(false); await m.submit(); assert.equal(h.builds().length, 1);
    m.gate(true); await m.submit(); assert.equal(h.builds().length, 2);
    assert.doesNotMatch(m.get("session-status").textContent, /Сессия обновлена/); m.ui.dispose();
  });
 }
}

for (const failedAt of [bootstrapPath, currentPath]) {
  test(`session-loss check failed at ${failedAt} never announces success and a later safe read explains the new action`, async () => {
    const h = harness(), saved = ready(); h.queue(currentPath, response(saved)); const m = mountSession(h); await m.ui.ready; m.gate(true);
    const draft = m.ui.form.snapshot();
    h.queue(buildPath, response(failure("SESSION_EXPIRED"), 409)); h.queue(failedAt, response(failure("STATE_READ_FAILED"), 503));
    await m.submit(); assert.deepEqual(m.ui.session.snapshot().view, saved); assert.deepEqual(m.ui.form.snapshot(), draft);
    assert.doesNotMatch(m.get("session-status").textContent, /Сессия обновлена/);
    assert.equal(m.get("form-error").hidden, false); assert.equal(m.get("build-button").disabled, true);
    await m.submit(); assert.equal(h.builds().length, 1);
    h.queue(currentPath, response(views.empty)); assert.equal(await m.ui.session.recheck(), true);
    assert.match(m.get("session-status").textContent, /Сессия обновлена.*нажмите/);
    assert.equal(h.builds().length, 1); m.ui.dispose();
  });
}

test("a current session refusal performs one bounded recovery; repeated 409 never loops", async () => {
  const h = harness(); h.queue(currentPath, response(failure("SESSION_REQUIRED"), 409), response(failure("SESSION_EXPIRED"), 409));
  assert.equal(await h.coordinator.open(), false);
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, bootstrapPath, currentPath]);
  assert.equal(h.coordinator.snapshot().sessionReady, false);
  assert.equal(await h.coordinator.submit(), false);
  assert.equal(h.builds().length, 0);
});

test("stale retains exact stored facts; unavailable/empty remove chart and do not build", async () => {
  const h = harness();
  for (const view of [ready(true), views.known_unavailable, views.empty, ready(false, true)]) {
    h.queue(currentPath, response(view));
    assert.equal(await h.coordinator.open(), true);
    assert.deepEqual(h.coordinator.snapshot().view, view);
    assert.equal(h.builds().length, 0);
  }
  assert.equal(h.coordinator.snapshot().view.birth.utc_offset_seconds, null);
});

test("bootstrap failure suppresses current/build and keeps draft; safe explicit read later succeeds", async () => {
  const h = harness(), draft = h.form.snapshot(); h.queue(bootstrapPath, response(failure("STATE_READ_FAILED"), 503, { "Retry-After": "5" }));
  assert.equal(await h.coordinator.open(), false);
  assert.equal(h.coordinator.snapshot().error.retryAfter, "5");
  assert.equal(await h.coordinator.submit(), false);
  assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath]);
  assert.deepEqual(h.form.snapshot(), draft);
  assert.equal(await h.coordinator.open(), false);
  h.clock.advance(5000);
  assert.equal(await h.coordinator.open(), true);
  assert.equal(await h.coordinator.submit(), true);
});

for (const code of ["STATE_COMMIT_FAILED", "BUILD_TIMEOUT"]) {
  test(`${code} blocks a new build before delayed check or restart confirmation`, async () => {
    const h = harness(); await h.coordinator.open(); const draft = h.form.snapshot();
    h.queue(buildPath, response(failure(code), code === "BUILD_TIMEOUT" ? 504 : 503, { "Retry-After": "5" }));
    assert.equal(await h.coordinator.submit(), false);
    assert.equal(h.coordinator.snapshot().requiresReconciliation, true);
    assert.deepEqual(h.form.snapshot(), draft);
    assert.equal(await h.coordinator.submit(), false);
    assert.equal(h.builds().length, 1);
    assert.equal(h.calls.length, 3);
  });
}

test("text proxy error and incomplete success cannot masquerade as a committed chart", async () => {
  // TEST-FIND-UI-006/011: 502 сначала сверяется, неполный 200 по-прежнему требует safe read.
  const h = harness(); h.queue(currentPath, response(ready())); await h.coordinator.open();
  h.queue(currentPath, response(failure("STATE_READ_FAILED"), 503));
  h.queue(buildPath, new Response("Bad gateway", { status: 502 }), response({ status: "chart_ready", state_version: 2 }));
  assert.equal(await h.coordinator.submit(), false);
  assert.deepEqual(h.coordinator.snapshot().view, ready());
  assert.ok(h.coordinator.snapshot().error.message);
  assert.equal(await h.coordinator.submit(), false); assert.equal(h.builds().length, 1);
  h.queue(currentPath, response(ready())); assert.equal(await h.coordinator.recheck(), true);
  h.queue(currentPath, response(ready()));
  assert.equal(await h.coordinator.submit(), false);
  assert.deepEqual(h.coordinator.snapshot().view, ready());
  assert.equal(h.coordinator.snapshot().source, "current");
  assert.equal(h.coordinator.snapshot().recovery.status, "old_or_empty");
  assert.equal(h.builds().length, 2);
});

test("snapshots do not share mutable charts, issues or request intent with callers", async () => {
  const h = harness(); h.queue(currentPath, response(ready())); await h.coordinator.open();
  const state = h.coordinator.snapshot(); state.view.chart.points[0].minute = 59;
  assert.deepEqual(h.coordinator.snapshot().view, ready());
});

for (const [status, code] of [[429, "BUILD_SESSION_RATE_LIMITED"], [503, "BUILD_CAPACITY_EXHAUSTED"]]) {
  test(`${code} respects Retry-After; expiry only permits an explicit build`, async () => {
    const h = harness(); await h.coordinator.open();
    h.queue(buildPath, response(failure(code), status, { "Retry-After": "2" }));
    assert.equal(await h.coordinator.submit(), false);
    assert.equal(h.coordinator.snapshot().error.requestId, "controlled-request");
    assert.equal(h.coordinator.snapshot().retryInSeconds, 2);
    assert.equal(await h.coordinator.submit(), false);
    h.clock.advance(1999);
    assert.equal(await h.coordinator.submit(), false);
    h.clock.advance(1);
    assert.equal(h.builds().length, 1);
    assert.equal(h.coordinator.snapshot().canSubmit, true);
    assert.equal(await h.coordinator.submit(), true);
    assert.equal(h.builds().length, 2);
  });
}

test("read and build cannot overlap or let an older read replace a committed result", async () => {
  const h = harness(), read = deferred(); h.queue(currentPath, read.promise);
  const opening = h.coordinator.open();
  assert.equal(await h.coordinator.open(), false);
  assert.equal(await h.coordinator.submit(), false);
  read.resolve(response(views.empty));
  await opening;
  const pending = deferred(); h.queue(buildPath, pending.promise);
  const building = h.coordinator.submit();
  assert.equal(await h.coordinator.open(), false);
  pending.resolve(response(committed())); await building;
  assert.equal(h.calls.length, 3);
  assert.equal(h.coordinator.snapshot().source, "build");
});

test("failed current reconciliation does not replay POST or replace a confirmed chart", async () => {
  const h = harness(); h.queue(currentPath, response(ready())); await h.coordinator.open();
  h.queue(buildPath, response({ status: "already_applied", state_version: 2 }));
  h.queue(currentPath, response(failure("STATE_READ_FAILED"), 503));
  assert.equal(await h.coordinator.submit(), false);
  assert.deepEqual(h.coordinator.snapshot().view, ready());
  assert.equal(await h.coordinator.submit(), false);
  assert.equal(h.builds().length, 1);
  assert.equal(await h.coordinator.open(), true);
  assert.deepEqual(h.coordinator.snapshot().view, views.empty);
});

test("dispose ignores a late network response without claiming server cancellation", async () => {
  const h = harness(), read = deferred(); h.queue(currentPath, read.promise);
  const entered = h.entered(currentPath);
  const opening = h.coordinator.open();
  await entered;
  h.coordinator.dispose(); const count = h.changes.length;
  read.resolve(response(ready())); await opening;
  assert.equal(h.coordinator.snapshot().view, null);
  assert.equal(h.changes.length, count);
  assert.equal(await h.coordinator.submit(), false);
});

test("mounted form opens real coordinator, restores unavailable birth and requires a manual gate", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(views.known_unavailable));
  const ui = mountBirthForm(document, { apiClient: h.apiClient });
  assert.equal(document.getElementById("build-button").disabled, true);
  await ui.ready;
  assert.equal(document.getElementById("birth-date").value, views.known_unavailable.birth.birth_date);
  assert.equal(ui.form.snapshot().place.place_id, views.known_unavailable.birth.place.place_id);
  assert.equal(document.getElementById("terms-acknowledged").checked, false);
  assert.equal(document.getElementById("build-button").textContent, "Построить заново");
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds().length, 0);
  const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds().length, 1);
  assert.deepEqual(Object.keys(h.builds()[0].body).sort(), ["birth_date", "birth_time", "place_id"]);
  assert.equal(ui.session.snapshot().view.chart.chart_identity, charts.natal.chart_identity);
  ui.places.dispose(); ui.session.dispose();
});

test("mounted server time issue appears next to time, focuses it and clears on correction", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient }); await ui.ready;
  const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
  h.queue(buildPath, response(failure("INPUT_REQUIRED", [{ field: "birth.time", code: "AMBIGUOUS", candidates: [0, 3600] }]), 422));
  await document.getElementById("birth-form").emit("submit");
  assert.ok(document.getElementById("time-error").textContent.includes("неоднозначно"));
  const time = document.getElementById("birth-time");
  assert.equal(document.activeElement, time);
  assert.equal(time.getAttribute("aria-invalid"), "true");
  time.value = "00:00"; time.emit("input");
  assert.equal(document.getElementById("time-error").hidden, true);
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds()[1].body.birth_time, "00:00");
  ui.places.dispose(); ui.session.dispose();
});

test("user input while initial current is pending survives late saved birth", async () => {
  const h = harness(), document = documentPort(), current = deferred(); h.queue(currentPath, current.promise);
  const ui = mountBirthForm(document, { apiClient: h.apiClient });
  const date = document.getElementById("birth-date"); date.value = "2000-02-29"; date.emit("input");
  current.resolve(response(ready())); await ui.ready;
  assert.equal(date.value, "2000-02-29");
  assert.equal(ui.form.snapshot().date, "2000-02-29");
  assert.equal(ui.form.snapshot().place, null);
  assert.equal(ui.session.snapshot().view.chart.chart_identity, charts.natal.chart_identity);
  ui.places.dispose(); ui.session.dispose();
});

// Регрессия пользовательского дефекта: ввод 0045 должен быть виден как 00:45.
test("typing four time digits inserts the separator, preserves caret and sends HH:MM", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient }); await ui.ready;
  const time = document.getElementById("birth-time");
  for (const [raw, formatted, caret] of [["0", "0", 1], ["00", "00", 2], ["004", "00:4", 4], ["00:45", "00:45", 5]]) {
    time.value = raw; time.setSelectionRange(raw.length, raw.length, "none"); time.emit("input");
    assert.equal(time.value, formatted);
    assert.equal(ui.form.snapshot().time, formatted);
    assert.equal(time.selectionStart, caret);
    assert.equal(h.builds().length, 0);
  }
  const unknown = document.getElementById("time-unknown"); unknown.checked = true; unknown.emit("change");
  assert.equal(time.disabled, true);
  unknown.checked = false; unknown.emit("change");
  assert.equal(time.value, "00:45");
  const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds().length, 1);
  assert.equal(h.builds()[0].body.birth_time, "00:45");
  ui.places.dispose(); ui.session.dispose();
});

for (const [raw, formatted] of [["0045", "00:45"], ["0000", "00:00"], ["1200", "12:00"], ["2359", "23:59"]]) {
  test(`pasted time ${raw} displays ${formatted} without losing leading zeroes`, async () => {
    const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
    const ui = mountBirthForm(document, { apiClient: h.apiClient }); await ui.ready;
    const time = document.getElementById("birth-time");
    time.value = raw; time.setSelectionRange(4, 4, "none"); time.emit("input");
    assert.equal(time.value, formatted);
    assert.equal(ui.form.snapshot().time, formatted);
    assert.equal(time.selectionStart, 5);
    const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
    await document.getElementById("birth-form").emit("submit");
    assert.equal(h.builds()[0].body.birth_time, formatted);
    ui.places.dispose(); ui.session.dispose();
  });
}

test("time formatting keeps editing/clearing and rejects partial, seconds and invalid ranges", async () => {
  const h = harness(), document = documentPort(); h.queue(currentPath, response(ready()));
  const ui = mountBirthForm(document, { apiClient: h.apiClient }); await ui.ready;
  const time = document.getElementById("birth-time");
  const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
  for (const [raw, formatted] of [["", ""], ["004", "00:4"], ["2400", "24:00"], ["1460", "14:60"], ["00:45:00", "00:45:00"], ["ab:cd", "ab:cd"]]) {
    time.value = raw; time.emit("input");
    assert.equal(time.value, formatted);
    await document.getElementById("birth-form").emit("submit");
    assert.equal(h.builds().length, 0);
    assert.equal(document.getElementById("time-error").hidden, false);
    assert.equal(ui.form.snapshot().timeUnknown, false);
  }
  time.value = "0045"; time.setSelectionRange(1, 3, "forward"); time.emit("input");
  assert.equal(time.selectionStart, 1);
  assert.equal(time.selectionEnd, 4);
  assert.equal(time.selectionDirection, "forward");
  await document.getElementById("birth-form").emit("submit");
  assert.equal(h.builds().length, 1);
  assert.equal(h.builds()[0].body.birth_time, "00:45");
  ui.places.dispose(); ui.session.dispose();
});
