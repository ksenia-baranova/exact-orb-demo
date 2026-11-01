// Промты 01/02: настоящий UI; заменены только листовые DOM и fetch.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { harness, bootstrapPath, currentPath, buildPath, response, ready, committed, failure, deferred } from "./fixtures/session.mjs";

async function mounted(saved = true) {
  const h = harness(), document = documentPort();
  if (saved) h.queue(currentPath, response(saved === true ? ready() : saved));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  await ui.ready;
  return { h, document, ui, get: id => document.getElementById(id) };
}
function input(m, id, value, type = "input") {
  const field = m.get(id);
  if (type === "change") field.checked = value;
  else field.value = value;
  field.emit(type);
}
function draft(m) {
  const { acknowledged, errors, ...values } = m.ui.form.snapshot();
  return { values, raw: ["birth-date", "birth-place", "birth-time"].map(id => m.get(id).value),
    unknown: m.get("time-unknown").checked };
}
function open(m) {
  let prevented = false;
  m.get("terms-link").emit("click", { preventDefault() { prevented = true; } });
  assert.equal(prevented, true, "native anchor stays in the current document");
  assert.equal(m.get("terms-page").hidden, false);
  assert.equal(m.get("birth-page").hidden, true);
  assert.equal(m.document.activeElement, m.get("terms-page-heading"));
}
function returned(m, action, checked) {
  m.get(`terms-${action}`).click();
  assert.equal(m.get("terms-page").hidden, true);
  assert.equal(m.get("birth-page").hidden, false);
  assert.equal(m.get("birth-form").hidden, false);
  assert.equal(m.get("birth-editor").hidden, false);
  assert.equal(m.document.activeElement, m.get("terms-link"));
  assert.equal(m.get("terms-acknowledged").checked, checked);
  assert.equal(m.ui.form.snapshot().acknowledged, checked);
}

for (const checked of [false, true]) for (const action of ["agree", "back"]) {
  test(`T: ${checked} / ${action} preserves draft, opens editor and sends no build`, async () => {
    const m = await mounted();
    input(m, "terms-acknowledged", checked, "change");
    const before = draft(m), view = m.ui.session.snapshot().view, calls = m.h.calls.length;
    open(m);
    assert.equal(m.ui.form.snapshot().acknowledged, checked);
    returned(m, action, action === "agree" || checked);
    assert.deepEqual(draft(m), before);
    assert.deepEqual(m.ui.session.snapshot().view, view);
    m.get("terms-agree").click(); m.get("terms-back").click();
    assert.equal(m.ui.form.snapshot().acknowledged, action === "agree" || checked, "closed returns are no-ops");
    assert.equal(m.h.calls.length, calls);
    assert.equal(m.h.builds().length, 0);
    m.ui.dispose();
  });
}

const cases = [
  ...["00:00", "12:00", "23:59"].map(time => ["D1 " + time, true, m => input(m, "birth-time", time)]),
  ...["", "12:00"].map(time => ["D2 " + JSON.stringify(time), true, m => {
    input(m, "birth-time", time); input(m, "time-unknown", true, "change");
  }]),
  ["D3 empty", false, () => {}],
  ["D3 incomplete time", true, m => input(m, "birth-time", "12:6")],
  ["D3 place text without ID", true, m => input(m, "birth-place", "Невыбранное место")],
  ["D3 edited draft with accepted chart", true, m => {
    input(m, "birth-date", "2000-02-29"); input(m, "birth-time", "23:59");
  }],
];
for (const [name, saved, setup] of cases) for (const action of ["agree", "back"]) {
  test(`${name} / ${action} preserves raw values, ID, name and unknown-time flag`, async () => {
    const m = await mounted(saved); setup(m);
    if (name.startsWith("D3")) await m.get("birth-form").emit("submit");
    const before = draft(m), view = m.ui.session.snapshot().view;
    const dateNode = m.get("birth-date"), form = m.ui.form;
    open(m); returned(m, action, action === "agree");
    assert.deepEqual(draft(m), before);
    assert.equal(m.ui.form, form); assert.equal(m.get("birth-date"), dateNode);
    assert.deepEqual(m.ui.session.snapshot().view, view);
    assert.equal(m.h.builds().length, 0);
    m.ui.dispose();
  });
}

test("repeated reading after manual uncheck uses the current checkbox", async () => {
  const m = await mounted();
  open(m); returned(m, "agree", true);
  input(m, "terms-acknowledged", false, "change");
  open(m); returned(m, "back", false);
  open(m); returned(m, "agree", true);
  assert.equal(m.h.builds().length, 0); m.ui.dispose();
});

for (const acknowledgement of ["manual", "agree"]) {
  test(`${acknowledgement}: only an explicit valid submit sends exactly three API fields`, async () => {
    const m = await mounted(), before = m.ui.form.snapshot();
    await m.get("birth-form").emit("submit");
    assert.ok(m.ui.form.snapshot().errors.acknowledged);
    assert.equal(m.h.builds().length, 0);
    open(m); returned(m, "back", false);
    await m.get("birth-form").emit("submit");
    assert.equal(m.h.builds().length, 0, "reading and back do not grant acknowledgement");
    if (acknowledgement === "manual") input(m, "terms-acknowledged", true, "change");
    else { open(m); returned(m, "agree", true); }
    assert.equal(m.h.builds().length, 0, "acknowledging does not submit");
    await m.get("birth-form").emit("submit");
    assert.equal(m.h.builds().length, 1);
    assert.deepEqual(m.h.builds()[0].body, {
      birth_date: before.date, birth_time: before.time, place_id: before.place.place_id,
    });
    m.ui.dispose();
  });
}

test("dispose removes all new terms handlers", async () => {
  const m = await mounted(); open(m); m.ui.dispose();
  m.get("terms-agree").click(); m.get("terms-back").click();
  assert.equal(m.get("terms-page").hidden, false);
  assert.equal(m.ui.form.snapshot().acknowledged, false);
  const fresh = await mounted(); fresh.ui.dispose(); fresh.get("terms-link").click();
  assert.equal(fresh.get("terms-page").hidden, true);
});


// Промт 02: события листовой сети задают порядок; реальное время не используется.
function visibleFocus(m, expected) {
  assert.ok(m.document.activeElement === expected, `expected focus ${expected.id}, got ${m.document.activeElement?.id}`);
  for (let at = expected; at; at = at.parentNode) assert.equal(at.hidden, false, `focus hidden by ${at.id}`);
}
function reading(m, focus) {
  assert.equal(m.get("terms-page").hidden, false);
  assert.equal(m.get("birth-page").hidden, true);
  assert.equal(m.get("page-main").getAttribute("data-page-mode"), "terms");
  visibleFocus(m, focus);
}
function mountPendingCurrent() {
  const h = harness(), document = documentPort(), pending = deferred();
  h.queue(currentPath, pending.promise);
  const entered = h.entered(currentPath);
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  return { h, document, ui, pending, entered, get: id => document.getElementById(id) };
}

for (const action of ["agree", "back"]) for (const afterReturn of [false, true]) for (const empty of [false, true]) {
  test(`late initial current: ${action}, afterReturn=${afterReturn}, empty=${empty} preserves draft`, async () => {
    const m = mountPendingCurrent(); await m.entered;
    if (!empty) {
      input(m, "birth-date", "2000-02-29"); input(m, "birth-place", "Место без выбора");
      input(m, "birth-time", "12:6"); input(m, "time-unknown", true, "change");
    }
    const before = draft(m), posts = m.h.builds().length, saved = ready();
    open(m);
    if (afterReturn) returned(m, action, action === "agree");
    const focus = m.document.activeElement;
    m.pending.resolve(response(saved)); await m.ui.ready;
    assert.deepEqual(draft(m), before);
    assert.deepEqual(m.ui.session.snapshot().view, saved, "actual map is still accepted");
    assert.equal(m.ui.result.element.dataset.chartIdentity, saved.chart.chart_identity);
    if (afterReturn) {
      assert.equal(m.get("birth-editor").hidden, false);
      visibleFocus(m, focus);
    } else { reading(m, focus); returned(m, action, action === "agree"); }
    assert.deepEqual(draft(m), before);
    assert.equal(m.h.builds().length, posts);
    m.ui.dispose();
  });
}

test("initial current without terms still hydrates birth, collapses once and leaves checkbox unchecked", async () => {
  const m = mountPendingCurrent(); await m.entered;
  const saved = ready(); m.pending.resolve(response(saved)); await m.ui.ready;
  assert.equal(m.ui.form.snapshot().date, saved.birth.birth_date);
  assert.equal(m.ui.form.snapshot().place.place_id, saved.birth.place.place_id);
  assert.equal(m.get("birth-time").value, saved.birth.birth_time);
  assert.equal(m.get("birth-editor").hidden, true);
  assert.equal(m.get("terms-acknowledged").checked, false);
  assert.equal(m.ui.form.snapshot().acknowledged, false);
  assert.equal(m.h.builds().length, 0); m.ui.dispose();
});

for (const action of ["agree", "back"]) for (const outcome of ["committed", "field error", "already_applied", "lost response"]) {
  test(`pending build / ${outcome} / ${action} accepts real outcome without leaving terms or focus`, async () => {
    const m = await mounted(); m.ui.result.editButton.click();
    input(m, "birth-date", "1990-01-01"); input(m, "terms-acknowledged", true, "change");
    const pending = deferred(), before = draft(m), oldIdentity = m.ui.result.element.dataset.chartIdentity;
    m.h.queue(buildPath, pending.promise);
    const entered = m.h.entered(buildPath), submitting = m.get("birth-form").emit("submit"); await entered;
    const posts = m.h.builds().length;
    assert.equal(posts, 1); open(m);
    const focus = m.get("terms-back"); focus.focus();
    await m.get("birth-form").emit("submit");
    assert.equal(m.h.builds().length, posts, "G1: repeat while pending cannot POST");
    const actual = ready(); actual.birth.birth_date = "1990-01-01"; actual.chart.chart_identity += "-actual";
    let expectedCalls = [buildPath];
    if (outcome === "committed") pending.resolve(response(committed(actual.chart)));
    if (outcome === "field error") pending.resolve(response(failure("VALIDATION_ERROR", [
      { field: "birth.time", code: "AMBIGUOUS" },
    ]), 422));
    if (outcome === "already_applied" || outcome === "lost response") {
      const check = deferred(), checking = m.h.entered(currentPath); m.h.queue(currentPath, check.promise);
      pending.resolve(outcome === "already_applied" ? response({ status: "already_applied", state_version: 2 }) : new Error("lost response"));
      await checking; reading(m, focus);
      assert.equal(m.h.builds().length, posts);
      check.resolve(response(actual));
      expectedCalls = outcome === "already_applied" ? [buildPath, currentPath] : [buildPath, bootstrapPath, currentPath];
    }
    await submitting; reading(m, focus); assert.deepEqual(draft(m), before);
    assert.deepEqual(m.h.calls.slice(2).map(call => call.path), expectedCalls);
    const state = m.ui.session.snapshot();
    if (outcome === "field error") {
      assert.equal(state.fieldIssues.time[0].code, "AMBIGUOUS");
      assert.equal(m.ui.result.element.dataset.chartIdentity, oldIdentity);
    } else {
      assert.equal(state.view.chart.chart_identity, actual.chart.chart_identity);
      assert.equal(m.ui.result.element.dataset.chartIdentity, actual.chart.chart_identity);
      assert.match(m.get("chart-birth-summary").textContent, /1990-01-01/);
      assert.equal(state.acceptance.allowCollapse, true);
      assert.equal(state.acceptance.reset, true);
      assert.equal(state.acceptance.cause, { committed: "own_committed", already_applied: "already_applied_target_confirmed",
        "lost response": "matched_recovery" }[outcome]);
    }
    returned(m, action, true); visibleFocus(m, m.get("terms-link"));
    assert.deepEqual(draft(m), before);
    if (outcome === "field error") {
      assert.equal(m.get("time-error").hidden, false);
      assert.match(m.get("time-error").textContent, /неоднозначно/);
    } else {
      m.ui.session.clearFieldError("time");
      assert.equal(m.get("birth-editor").hidden, false, "accepted-once collapse stays consumed after return");
    }
    m.get("terms-agree").click(); m.get("terms-back").click();
    assert.equal(m.h.builds().length, posts); m.ui.dispose();
  });
}

for (const action of ["agree", "back"]) {
  test(`safe recovery with Retry-After stays visible after ${action} and remains usable`, async () => {
    const m = await mounted(); m.ui.result.editButton.click();
    input(m, "terms-acknowledged", true, "change");
    const before = draft(m), oldIdentity = m.ui.result.element.dataset.chartIdentity;
    const pending = deferred(); m.h.queue(buildPath, pending.promise);
    const submitting = m.get("birth-form").emit("submit"), posts = m.h.builds().length;
    open(m); const focus = m.document.activeElement;
    pending.resolve(response(failure("STATE_COMMIT_FAILED"), 503, { "Retry-After": "1" }));
    await submitting; reading(m, focus);
    assert.equal(m.ui.result.element.dataset.chartIdentity, oldIdentity);
    const calls = m.h.calls.length;
    await m.h.clock.advance(999); assert.equal(m.h.calls.length, calls);
    m.h.queue(currentPath, response(failure("STATE_READ_FAILED"), 503));
    await m.h.clock.advance(1); reading(m, focus);
    assert.equal(m.ui.session.snapshot().recovery.status, "check_failed");
    assert.deepEqual(m.h.calls.slice(2).map(call => call.path), [buildPath, currentPath]);
    returned(m, action, true); assert.deepEqual(draft(m), before);
    const recheck = m.get("birth-form").querySelectorAll("button").find(node => node.textContent === "Повторить проверку карты");
    assert.equal(recheck.hidden, false); assert.equal(recheck.disabled, false);
    recheck.focus(); visibleFocus(m, recheck);
    const actual = ready(); actual.birth.birth_date = "2000-02-29"; actual.chart.chart_identity += "-different";
    m.h.queue(currentPath, response(actual)); await recheck.click();
    assert.equal(m.ui.session.snapshot().recovery.status, "different");
    assert.equal(m.ui.result.element.dataset.chartIdentity, actual.chart.chart_identity);
    assert.match(m.get("chart-birth-summary").textContent, /2000-02-29/);
    assert.deepEqual(draft(m), before); assert.equal(m.h.builds().length, posts);
    assert.equal(m.get("birth-editor").hidden, false); visibleFocus(m, recheck);
    m.ui.dispose();
  });
}

for (const saved of [false, true]) for (const acknowledgement of ["manual", "agree"]) {
  test(`new mount after ${acknowledgement}, saved=${saved} clears checkbox despite retained DOM value`, async () => {
    const m = await mounted(saved);
    if (saved) m.ui.result.editButton.click();
    if (acknowledgement === "manual") input(m, "terms-acknowledged", true, "change");
    else { open(m); returned(m, "agree", true); }
    assert.equal(m.ui.form.snapshot().acknowledged, true); assert.equal(m.get("terms-acknowledged").checked, true);
    const oldResult = m.ui.result.element; m.ui.dispose();
    // Новый документ сохраняет лишь восстановленное браузером значение control.
    const document = documentPort(); document.getElementById("terms-acknowledged").checked = true;
    const h = harness(); if (saved) h.queue(currentPath, response(ready()));
    const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock }); await ui.ready;
    assert.equal(document.getElementById("terms-acknowledged").checked, false);
    assert.equal(ui.form.snapshot().acknowledged, false);
    assert.equal(ui.session.snapshot().view.status, saved ? "chart_ready" : "empty");
    assert.notEqual(ui.result.element, oldResult); assert.equal(h.builds().length, 0); ui.dispose();
  });
}

test("dispose during initial current leaves terms focus and draft untouched and removes page/foreground handlers", async () => {
  const m = mountPendingCurrent(); await m.entered; open(m);
  const before = draft(m), focus = m.document.activeElement, calls = m.h.calls.length;
  m.ui.dispose(); m.pending.resolve(response(ready())); await m.ui.ready;
  m.get("terms-agree").click(); m.get("terms-back").click();
  await m.document.emit("visibilitychange"); await m.document.defaultView.emit("online");
  reading(m, focus); assert.deepEqual(draft(m), before);
  assert.equal(m.h.calls.length, calls); assert.equal(m.ui.form.snapshot().acknowledged, false);
});


for (const action of ["agree", "back"]) {
  test(`automatic current while reading retains selection and three disclosures after ${action}`, async () => {
    const saved = ready();
    saved.chart = JSON.parse(readFileSync(new URL("./fixtures/natal_1985_chart_dto.json", import.meta.url), "utf8"));
    const m = await mounted(saved); m.ui.result.editButton.click();
    const point = m.get("points-table").querySelector('[data-point-id="moon"]');
    const controls = ["points-show-all", "houses-show-all", "aspects-show-all"].map(id => m.get(id));
    for (const control of controls) {
      assert.equal(control.hidden, false); control.click();
      assert.equal(control.getAttribute("aria-expanded"), "true");
    }
    point.click(); assert.equal(point.getAttribute("aria-pressed"), "true");
    input(m, "birth-time", "12:6"); const before = draft(m);
    const pending = deferred(); m.h.queue(currentPath, pending.promise);
    const entered = m.h.entered(currentPath), work = m.document.defaultView.emit("online"); await entered;
    open(m); const focus = m.document.activeElement;
    pending.resolve(response(saved)); await work; reading(m, focus);
    returned(m, action, action === "agree"); assert.deepEqual(draft(m), before);
    assert.ok(m.get("points-table").querySelector('[data-point-id="moon"]') === point);
    assert.equal(point.getAttribute("aria-pressed"), "true");
    for (const control of controls) assert.equal(control.getAttribute("aria-expanded"), "true");
    assert.equal(m.h.builds().length, 0); m.ui.dispose();
  });
}

test("render failure during terms retains visible focus and exposes working safe recheck after return", async () => {
  const m = await mounted(); m.ui.result.editButton.click();
  input(m, "terms-acknowledged", true, "change"); const before = draft(m);
  const form = m.get("birth-form"), originalSet = form.setAttribute, pending = deferred();
  m.h.queue(buildPath, pending.promise);
  const submitting = form.emit("submit"); open(m); const focus = m.document.activeElement;
  let failed = false;
  form.setAttribute = (name, value) => {
    if (!failed && name === "aria-busy" && value === "false") {
      failed = true; throw new Error("controlled leaf render failure");
    }
    return originalSet(name, value);
  };
  pending.resolve(response(committed())); await submitting;
  assert.equal(failed, true); assert.equal(m.ui.session.snapshot().requiresReconciliation, true);
  reading(m, focus); returned(m, "back", true); assert.deepEqual(draft(m), before);
  assert.match(m.get("form-error").textContent, /Не удалось показать ответ/);
  const recheck = form.querySelectorAll("button").find(node => node.textContent === "Повторить проверку карты");
  assert.equal(recheck.hidden, false); assert.equal(recheck.disabled, false);
  m.h.queue(currentPath, response(ready())); await recheck.click();
  assert.equal(m.ui.session.snapshot().requiresReconciliation, false);
  assert.equal(m.ui.result.element.dataset.chartIdentity, ready().chart.chart_identity);
  assert.equal(m.h.builds().length, 1); m.ui.dispose();
});
