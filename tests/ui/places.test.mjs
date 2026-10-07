// REQ-UI-02/10, AS-UI-02/18: настоящий поиск, управляемые таймер и сеть; без sleep.
// Контракт: docs/requirements/changes/ui-birth-form-and-facts/requirements.md @ ce25dd0.
import assert from "node:assert/strict";
import { test } from "node:test";
import { createPlaceSearch } from "../../src/exact_orb/http_api/ui/places.mjs";
import { createBirthForm } from "../../src/exact_orb/http_api/ui/form.mjs";
import { createApiClient } from "../../src/exact_orb/http_api/ui/transport.mjs";
import { placeWithoutRegion } from "./fixtures/session.mjs";

const north = { place_id: "ki-north", display_name: "Кировск", admin1_name: "Мурманская область", country_code: "RU" };
const south = { place_id: "ki-south", display_name: "Кировск", admin1_name: "Луганская область", country_code: "UA" };
const success = (items, requestId = "place-request") => ({ kind: "http", status: 200,
  body: { items }, requestId, retryAfter: null });

// REQ-UI-02/10, AS-UI-02/18/19; TEST-FIND-UI-005, найдено другой моделью.
test("a nullable region preserves the entire mixed result and confirmed selection", async () => {
  const timer = clock(), form = createBirthForm();
  const search = createPlaceSearch({ clock: timer, onSelect: form.selectPlace,
    searchPlaces: async () => success([placeWithoutRegion, north]) });
  search.setQuery("Гонк"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().status, "results");
  assert.deepEqual(search.snapshot().items, [placeWithoutRegion, north]);
  search.select(0); assert.equal(form.snapshot().place.place_id, placeWithoutRegion.place_id);
  assert.equal(form.snapshot().place.admin1_name, null);
  search.setQuery("Кир"); await Promise.all(timer.tick(250)); search.select(1);
  assert.equal(form.snapshot().place.admin1_name, north.admin1_name, "string-region positive control");
});
function clock() {
  let time = 0;
  let id = 0;
  const tasks = new Map();
  return {
    now: () => time,
    set(callback, delay) { tasks.set(++id, { callback, due: time + delay }); return id; },
    clear(handle) { tasks.delete(handle); },
    callbacks: () => [...tasks.values()].map(({ callback }) => callback),
    tick(milliseconds) {
      const target = time + milliseconds;
      const jobs = [];
      while (true) {
        const next = [...tasks].filter(([, task]) => task.due <= target).sort((a, b) => a[1].due - b[1].due)[0];
        if (!next) break;
        tasks.delete(next[0]); time = next[1].due;
        const result = next[1].callback();
        if (result?.then) jobs.push(result);
      }
      time = target;
      return jobs;
    },
  };
}
function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

test("K → Ki → Kir → Kiro → Ki respects threshold and cancels debounce", async () => {
  const timer = clock();
  const calls = [];
  const search = createPlaceSearch({ clock: timer, searchPlaces: async (query) => {
    calls.push(query); return success([north]);
  } });
  for (const query of ["К", "Ки", "   "]) {
    search.setQuery(query); await Promise.all(timer.tick(250));
    assert.equal(calls.length, 0);
    assert.equal(search.snapshot().items.length, 0);
  }
  search.setQuery("Кир");
  await Promise.all(timer.tick(249));
  assert.equal(calls.length, 0);
  await Promise.all(timer.tick(1));
  assert.deepEqual(calls, ["Кир"]);
  assert.equal(search.snapshot().items[0].place_id, north.place_id);
  search.setQuery("Киро");
  search.setQuery("Ки");
  await Promise.all(timer.tick(250));
  assert.deepEqual(calls, ["Кир"]);
  assert.equal(search.snapshot().status, "idle");
  search.setQuery("Кировск"); await Promise.all(timer.tick(250));
  assert.deepEqual(calls, ["Кир", "Кировск"]);
});

test("late Kir response cannot overwrite a newer Kiro result even if abort is ignored", async () => {
  const timer = clock();
  const calls = [];
  const requests = [];
  const search = createPlaceSearch({ clock: timer, searchPlaces: (query, { signal }) => {
    const response = deferred(); calls.push(query); requests.push({ ...response, signal }); return response.promise;
  } });
  search.setQuery("Кир"); const [first] = timer.tick(250);
  search.setQuery("Киро"); const [second] = timer.tick(250);
  assert.equal(requests[0].signal.aborted, true);
  requests[1].resolve(success([south], "new-id")); await second;
  assert.equal(search.snapshot().items[0].place_id, south.place_id);
  requests[0].resolve(success([north], "old-id")); await first;
  assert.equal(search.snapshot().query, "Киро");
  assert.equal(search.snapshot().items[0].place_id, south.place_id);
  assert.equal(search.snapshot().requestId, "new-id");
  assert.deepEqual(calls, ["Кир", "Киро"]);
});

for (const query of ["Ки", "", "   "]) {
  test(`late response after shortening/clearing ${JSON.stringify(query)} stays hidden`, async () => {
    const timer = clock();
    const response = deferred();
    const search = createPlaceSearch({ clock: timer, searchPlaces: () => response.promise });
    search.setQuery("Кир"); const [pending] = timer.tick(250);
    search.setQuery(query);
    response.resolve(success([north])); await pending;
    assert.equal(search.snapshot().status, "idle");
    assert.deepEqual(search.snapshot().items, []);
    assert.equal(search.snapshot().selection, null);
  });
}

test("a canceled timer firing late cannot make a stale request", async () => {
  const timer = clock();
  const calls = [];
  const search = createPlaceSearch({ clock: timer, searchPlaces: async (query) => {
    calls.push(query); return success([north]);
  } });
  search.setQuery("Кир");
  const [canceledCallback] = timer.callbacks();
  search.setQuery("Киро");
  await canceledCallback();
  assert.deepEqual(calls, []);
  await Promise.all(timer.tick(250));
  assert.deepEqual(calls, ["Киро"]);
});

test("keyboard and mouse choose a concrete duplicate-name ID without another request", async () => {
  const timer = clock();
  const form = createBirthForm();
  const calls = [];
  const search = createPlaceSearch({ clock: timer, onSelect: form.selectPlace,
    searchPlaces: async (query) => { calls.push(query); return success([north, south]); } });
  search.setQuery("Кировск"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().selection, null);
  assert.equal(search.handleKey("Enter"), true);
  assert.equal(search.snapshot().selection, null);
  search.handleKey("ArrowDown"); search.handleKey("ArrowDown");
  assert.equal(search.snapshot().activeIndex, 1);
  search.handleKey("Enter");
  assert.equal(form.snapshot().place.place_id, south.place_id);
  assert.equal(form.snapshot().place.admin1_name, south.admin1_name);
  assert.equal(form.snapshot().place.country_code, "UA");
  assert.deepEqual(calls, ["Кировск"]);
  form.editPlace("Кир"); search.setQuery("Кир");
  assert.equal(form.snapshot().place, null);
  assert.equal(search.snapshot().selection, null);
  await Promise.all(timer.tick(250));
  assert.equal(search.select(0).place_id, north.place_id);
  assert.equal(form.snapshot().place.place_id, north.place_id);
  assert.deepEqual(calls, ["Кировск", "Кир"]);
});

test("Escape closes suggestions, arrows reopen them and selection wraps", async () => {
  const timer = clock();
  const search = createPlaceSearch({ clock: timer, searchPlaces: async () => success([north, south]) });
  search.setQuery("Кир"); await Promise.all(timer.tick(250));
  assert.equal(search.handleKey("Escape"), true);
  assert.equal(search.snapshot().open, false);
  assert.equal(search.handleKey("ArrowUp"), true);
  assert.equal(search.snapshot().open, true);
  assert.equal(search.snapshot().activeIndex, 1);
  search.handleKey("ArrowDown");
  assert.equal(search.snapshot().activeIndex, 0);
  search.close();
  assert.equal(search.snapshot().open, false);
});

test("empty, invalid-input and unavailable outcomes keep no invented selection", async () => {
  const timer = clock();
  const outcomes = [success([]), { kind: "http", status: 422, body: { code: "INVALID_PLACE_QUERY" } },
    { kind: "network_error" }, success([north])];
  const search = createPlaceSearch({ clock: timer, searchPlaces: async () => outcomes.shift() });
  search.setQuery("Нет"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().status, "empty");
  assert.equal(search.snapshot().selection, null);
  search.setQuery("###"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().error.message, "Проверьте название места.");
  search.setQuery("Кир"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().error.message, "Поиск временно недоступен.");
  assert.equal(search.snapshot().selection, null);
  search.setQuery("Кировск"); await Promise.all(timer.tick(250));
  assert.equal(search.select(0).place_id, north.place_id);
});

test("Retry-After prevents early requests and expiration does not retry automatically", async () => {
  const timer = clock();
  let calls = 0;
  const search = createPlaceSearch({ clock: timer, searchPlaces: async () => {
    calls += 1;
    return calls === 1 ? { kind: "http", status: 503, body: { code: "PLACE_CATALOG_UNAVAILABLE" },
      requestId: "unavailable-id", retryAfter: "5" } : success([north]);
  } });
  search.setQuery("Кир"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().requestId, "unavailable-id");
  assert.equal(search.snapshot().retryAfter, "5");
  assert.equal(search.snapshot().canRetry, false);
  assert.equal(search.retry(), false);
  search.setQuery("Киро"); await Promise.all(timer.tick(250));
  assert.equal(calls, 1);
  await Promise.all(timer.tick(4750));
  assert.equal(search.snapshot().canRetry, true);
  assert.equal(calls, 1);
  assert.equal(search.retry(), true);
  await Promise.resolve();
  assert.equal(calls, 2);
  assert.equal(search.snapshot().items[0].place_id, north.place_id);
});

test("query remains raw, Unicode threshold counts characters and actual transport is used", async () => {
  const timer = clock();
  const calls = [];
  const api = createApiClient({ fetchFn: async (path, options) => {
    calls.push({ path, options });
    return new Response(JSON.stringify({ items: [north] }), { status: 200, headers: { "X-Request-ID": "real-leaf-id" } });
  } });
  const search = createPlaceSearch({ clock: timer, searchPlaces: api.searchPlaces });
  search.setQuery("🙂🙂"); await Promise.all(timer.tick(250));
  assert.equal(calls.length, 0);
  search.setQuery("  ＭОС + & "); await Promise.all(timer.tick(250));
  assert.equal(calls.length, 1);
  assert.equal(new URL(calls[0].path, "https://testserver").searchParams.get("query"), "  ＭОС + & ");
  assert.equal(calls[0].options.credentials, "same-origin");
  assert.equal(search.snapshot().requestId, "real-leaf-id");
});

test("shortening and retyping during Retry-After retains a usable error and blocks early GET", async () => {
  const timer = clock();
  let calls = 0;
  const search = createPlaceSearch({ clock: timer, searchPlaces: async () => {
    calls += 1;
    return calls === 1 ? { kind: "http", status: 503, body: { code: "PLACE_CATALOG_UNAVAILABLE" },
      requestId: "cooldown-id", retryAfter: "5" } : success([north]);
  } });
  search.setQuery("Кир"); await Promise.all(timer.tick(250));
  search.setQuery("Ки");
  assert.equal(search.snapshot().status, "idle");
  assert.equal(search.snapshot().error, null);
  search.setQuery("Киро");
  assert.equal(search.snapshot().status, "error");
  assert.equal(search.snapshot().error?.message, "Поиск временно недоступен.");
  assert.equal(search.snapshot().requestId, "cooldown-id");
  assert.equal(search.snapshot().retryAfter, "5");
  await Promise.all(timer.tick(250));
  assert.equal(calls, 1);
  await Promise.all(timer.tick(4750));
  assert.equal(search.retry(), true);
  await Promise.resolve();
  assert.equal(search.snapshot().items[0].place_id, north.place_id);
});

test("malformed success and caller mutation cannot manufacture a usable place", async () => {
  const timer = clock();
  let calls = 0;
  const search = createPlaceSearch({ clock: timer, searchPlaces: async () => {
    calls += 1; return success(calls === 1 ? [{ display_name: "wrong" }] : [north]);
  } });
  search.setQuery("Кир"); await Promise.all(timer.tick(250));
  assert.equal(search.snapshot().status, "error");
  assert.equal(search.select(0), null);
  search.setQuery("Киро"); await Promise.all(timer.tick(250));
  search.snapshot().items[0].place_id = "changed";
  assert.equal(search.select(0).place_id, north.place_id);
  const item = search.snapshot().selection; item.place_id = "changed";
  assert.equal(search.snapshot().selection.place_id, north.place_id);
});

test("dispose prevents both scheduled requests and completion publication", async () => {
  const timer = clock();
  const response = deferred();
  let calls = 0;
  const notices = [];
  const search = createPlaceSearch({ clock: timer, onChange: (state) => notices.push(state.status),
    searchPlaces: () => { calls += 1; return response.promise; } });
  search.setQuery("Кир"); const [pending] = timer.tick(250);
  search.dispose();
  response.resolve(success([north])); await pending;
  assert.equal(calls, 1);
  assert.deepEqual(notices, ["debouncing", "loading"]);
  search.setQuery("Киро"); await Promise.all(timer.tick(250));
  assert.equal(calls, 1);
});
