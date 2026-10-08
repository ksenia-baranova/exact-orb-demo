// REQ-UI-02/03/10, AS-UI-04/05/06/20: проверяем настоящий черновик и intent.
// Контракт: docs/requirements/changes/ui-birth-form-and-facts/requirements.md @ ce25dd0.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createBirthForm } from "../../src/exact_orb/http_api/ui/form.mjs";
import { createApiClient } from "../../src/exact_orb/http_api/ui/transport.mjs";

const fixture = JSON.parse(readFileSync(new URL("../fixtures/places.jsonl", import.meta.url), "utf8").split("\n")[0]);
const place = { place_id: fixture.place_id, display_name: fixture.name,
  admin1_name: fixture.admin1, country_code: fixture.country };
function validForm(time = "12:00") {
  const form = createBirthForm();
  form.setDate("2000-02-29");
  form.setTime(time);
  form.selectPlace(place);
  form.acknowledge(true);
  return form;
}

for (const time of ["00:00", "12:00", "23:59"]) {
  test(`known ${time} remains HH:MM and never becomes unknown`, () => {
    const result = validForm(time).prepareSubmission();
    assert.equal(result.ok, true);
    assert.deepEqual(result.intent, { birth_date: "2000-02-29", birth_time: time, place_id: place.place_id });
  });
}

for (const time of ["", "24:00", "12:60", "1:00", "12:00:00", " 12:00 "]) {
  test(`invalid time ${JSON.stringify(time)} blocks submission and preserves the draft`, () => {
    const form = validForm(time);
    assert.equal(form.prepareSubmission().ok, false);
    assert.ok(form.snapshot().errors.time);
    assert.equal(form.snapshot().timeUnknown, false);
    assert.equal(form.snapshot().date, "2000-02-29");
    assert.equal(form.snapshot().place.place_id, place.place_id);
    form.setTime("00:00");
    assert.equal(form.prepareSubmission().intent.birth_time, "00:00");
  });
}

test("explicit unknown time sends null and toggling preserves other fields and entered time", () => {
  const form = validForm();
  form.setUnknownTime(true);
  assert.equal(form.prepareSubmission().intent.birth_time, null);
  assert.equal(form.snapshot().time, "12:00");
  form.setUnknownTime(false);
  assert.equal(form.prepareSubmission().intent.birth_time, "12:00");
  form.setTime("");
  assert.equal(form.prepareSubmission().ok, false);
  form.setUnknownTime(true);
  assert.deepEqual(form.prepareSubmission().intent,
    { birth_date: "2000-02-29", birth_time: null, place_id: place.place_id });
});

for (const date of ["", "2023-02-29", "1900-02-29", "2000-04-31", "0000-01-01", "2000-13-01", "2000-01-00", "29.02.2000"]) {
  test(`invalid calendar date ${JSON.stringify(date)} requires correction`, () => {
    const form = validForm();
    form.setDate(date);
    assert.equal(form.prepareSubmission().ok, false);
    assert.ok(form.snapshot().errors.date);
    form.setDate("2000-02-29");
    assert.equal(form.prepareSubmission().ok, true);
  });
}

test("calendar validation does not invent domain range or browser timezone rules", () => {
  for (const date of ["1800-01-01", "2399-12-31", "0001-01-01", "9999-12-31"]) {
    const form = validForm();
    form.setDate(date);
    assert.equal(form.prepareSubmission().intent.birth_date, date);
  }
});

test("typing or editing even the same place text clears confirmation immediately", () => {
  const form = validForm();
  form.editPlace(place.display_name);
  assert.equal(form.snapshot().place, null);
  assert.equal(form.prepareSubmission().ok, false);
  assert.ok(form.snapshot().errors.place);
  form.selectPlace(place);
  assert.equal(form.prepareSubmission().intent.place_id, place.place_id);
  form.editPlace("");
  assert.equal(form.snapshot().place, null);
});

test("unchecked gate prevents POST; manual acknowledgement permits exactly three fields", async () => {
  const form = validForm();
  form.acknowledge(false);
  const calls = [];
  const api = createApiClient({ fetchFn: async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ status: "chart_ready" }), { status: 200 });
  } });
  async function submit() {
    const result = form.prepareSubmission();
    if (result.ok) await api.buildNatal(result.intent);
    return result;
  }
  assert.equal((await submit()).ok, false);
  assert.ok(form.snapshot().errors.acknowledged);
  assert.equal(calls.length, 0);
  assert.equal(form.snapshot().place.place_id, place.place_id);
  form.acknowledge(true);
  assert.equal((await submit()).ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/charts/natal");
  assert.deepEqual(JSON.parse(calls[0].options.body),
    { birth_date: "2000-02-29", birth_time: "12:00", place_id: place.place_id });
});

test("every new form starts unchecked; snapshots and submitted intent do not share mutable data", () => {
  const first = validForm();
  const snapshot = first.snapshot();
  snapshot.place.place_id = "changed";
  snapshot.acknowledged = false;
  const intent = first.prepareSubmission().intent;
  assert.equal(Object.isFrozen(intent), true);
  assert.equal(intent.place_id, place.place_id);
  first.setDate("2001-01-01");
  assert.equal(intent.birth_date, "2000-02-29");
  const second = createBirthForm();
  assert.equal(second.snapshot().acknowledged, false);
  assert.equal(second.snapshot().place, null);
  assert.equal(second.snapshot().date, "");
});
