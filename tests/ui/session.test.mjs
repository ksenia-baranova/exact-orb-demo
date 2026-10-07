// REQ-UI-01/03/08/09, AS-UI-01/03/04/06/10/11/12/16/17/20/21.
// Контракт: docs/requirements/changes/ui-birth-form-and-facts/{requirements,scenarios}.md @ ce25dd0.
// Настоящие form/session/transport; заменена только листовая сеть, ожидание управляется Promise.
import assert from "node:assert/strict";
import { test } from "node:test";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { documentPort } from "./fixtures/dom.mjs";

import { charts, views, place, ready, committed, response, failure, deferred, harness,
  bootstrapPath, currentPath, buildPath } from "./fixtures/session.mjs";

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
    const h = harness(); await h.coordinator.open();
    const winner = ready(true); winner.chart.chart_identity = "persisted-winner";
    h.queue(currentPath, response(winner));
    h.queue(buildPath, result === "already_applied" ? response({ status: result, state_version: 3 })
      : response(failure(result), 409));
    assert.equal(await h.coordinator.submit(), true);
    assert.deepEqual(h.coordinator.snapshot().view, winner);
    assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, currentPath]);
    assert.equal(h.builds().length, 1);
  });
}

for (const code of ["SESSION_REQUIRED", "SESSION_EXPIRED", "SESSION_NOT_FOUND"]) {
  test(`${code} recovers bootstrap/current with draft intact; a new POST needs a new action`, async () => {
    const h = harness(); await h.coordinator.open(); const draft = h.form.snapshot();
    h.queue(buildPath, response(failure(code), 409));
    assert.equal(await h.coordinator.submit(), true);
    assert.deepEqual(h.calls.map((call) => call.path), [bootstrapPath, currentPath, buildPath, bootstrapPath, currentPath]);
    assert.equal(h.builds().length, 1);
    assert.deepEqual(h.coordinator.snapshot().view, views.empty);
    assert.deepEqual(h.form.snapshot(), draft);
    assert.equal(await h.coordinator.submit(), true);
    assert.equal(h.builds().length, 2);
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
  const h = harness(); h.queue(currentPath, response(ready())); await h.coordinator.open();
  h.queue(buildPath, new Response("Bad gateway", { status: 502 }), response({ status: "chart_ready", state_version: 2 }));
  assert.equal(await h.coordinator.submit(), false);
  assert.deepEqual(h.coordinator.snapshot().view, ready());
  assert.ok(h.coordinator.snapshot().error.message);
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
