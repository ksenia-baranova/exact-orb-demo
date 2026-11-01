// Промт 01: T1…T4/D1…D3, настоящий UI; заменены только листовые DOM и fetch.
import assert from "node:assert/strict";
import { test } from "node:test";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { harness, currentPath, response, ready } from "./fixtures/session.mjs";

async function mounted(saved = true) {
  const h = harness(), document = documentPort();
  if (saved) h.queue(currentPath, response(ready()));
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
