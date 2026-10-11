// REQ-UI-01/09, AS-UI-01/12/23: транспорт; приёмка браузера и сессии выполняется отдельно.
// Контракт: docs/requirements/changes/ui-birth-form-and-facts/requirements.md @ ce25dd0.
import assert from "node:assert/strict";
import { test } from "node:test";
import { createApiClient } from "../../src/exact_orb/http_api/ui/transport.mjs";

const intent = { birth_date: "2000-01-02", birth_time: null, place_id: "geonames:524901" };

function jsonResponse(body, status = 200, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

test("existing endpoints use same-origin cookies, no-store and exact request bodies", async () => {
  const calls = [];
  const api = createApiClient({ fetchFn: async (path, options) => {
    calls.push({ path, options });
    return jsonResponse({ ok: true });
  } });
  await api.bootstrap();
  await api.current();
  await api.searchPlaces("Кир & +?", { limit: 20 });
  await api.buildNatal({ ...intent, state_version: 42, name: "Не отправлять" });

  assert.equal(calls.length, 4);
  assert.deepEqual(calls.map(({ path }) => path.split("?")[0]), [
    "/session/bootstrap", "/charts/current", "/places", "/charts/natal",
  ]);
  assert.deepEqual(calls.map(({ options }) => options.method), ["POST", "GET", "GET", "POST"]);
  for (const { options } of calls) {
    assert.equal(options.credentials, "same-origin");
    assert.equal(options.cache, "no-store");
    assert.equal(new Headers(options.headers).has("Cookie"), false);
    assert.equal(new Headers(options.headers).has("X-Request-ID"), false);
  }
  assert.equal(calls[0].options.body, "{}");
  assert.equal(calls[1].options.body, undefined);
  assert.equal(calls[2].options.body, undefined);
  assert.deepEqual(JSON.parse(calls[3].options.body), intent);
  assert.equal(calls[3].options.headers["Content-Type"], "application/json");
  const query = new URL(calls[2].path, "https://testserver").searchParams;
  assert.equal(query.get("query"), "Кир & +?");
  assert.equal(query.get("limit"), "20");
});

test("place search preserves server default limit", async () => {
  let received;
  const api = createApiClient({ fetchFn: async (path) => {
    received = new URL(path, "https://testserver");
    return jsonResponse({ items: [] });
  } });
  assert.deepEqual((await api.searchPlaces("Москва")).body, { items: [] });
  assert.equal(received.searchParams.get("query"), "Москва");
  assert.equal(received.searchParams.has("limit"), false);
});

test("HTTP ErrorDTO and network rejection are distinct, neither repeats a POST", async () => {
  const errorDTO = { code: "SESSION_REQUIRED", detail_code: null,
    user_message: "Нужна сессия", retryable: false };
  const calls = [];
  const api = createApiClient({ fetchFn: async (path, options) => {
    calls.push({ path, method: options.method });
    if (calls.length === 1) return jsonResponse(errorDTO, 409, { "X-Request-ID": "http-error-id" });
    if (calls.length === 2) throw new TypeError("Failed to fetch");
    return jsonResponse({ status: "empty", birth: null, chart: null });
  } });
  assert.deepEqual(await api.buildNatal(intent), {
    kind: "http", status: 409, body: errorDTO, requestId: "http-error-id", retryAfter: null,
  });
  assert.equal(calls.length, 1);
  assert.deepEqual(await api.buildNatal(intent), {
    kind: "network_error", aborted: false, status: null, requestId: null, retryAfter: null,
  });
  assert.equal(calls.length, 2);
  // Позитивный контроль: следующий явно вызванный read действительно выполняется.
  assert.equal((await api.current()).body.status, "empty");
  assert.deepEqual(calls, [
    { path: "/charts/natal", method: "POST" },
    { path: "/charts/natal", method: "POST" },
    { path: "/charts/current", method: "GET" },
  ]);
});

test("HTTP success and failure preserve status, body and diagnostic headers", async () => {
  for (const status of [200, 429, 503, 504]) {
    const body = status === 200 ? { status: "committed", chart: { chart_identity: "chart-id" } }
      : { code: "STATE_READ_FAILED", detail_code: "SQLITE_BUSY", user_message: "Повторите позже",
        retryable: true };
    const api = createApiClient({ fetchFn: async () => jsonResponse(body, status, {
      "X-Request-ID": `request-${status}`, "Retry-After": "5",
    }) });
    assert.deepEqual(await api.current(), {
      kind: "http", status, body, requestId: `request-${status}`, retryAfter: "5",
    });
  }
});

test("a proxy text response remains HTTP and is not invented into ErrorDTO", async () => {
  const api = createApiClient({ fetchFn: async () => new Response("upstream timeout", { status: 504 }) });
  assert.deepEqual(await api.current(), {
    kind: "http", status: 504, body: "upstream timeout", requestId: null, retryAfter: null,
  });
});

test("an empty HTTP response is not a network failure", async () => {
  const api = createApiClient({ fetchFn: async () => new Response(null, { status: 204 }) });
  assert.deepEqual(await api.current(), {
    kind: "http", status: 204, body: null, requestId: null, retryAfter: null,
  });
});

test("an interrupted body is a network outcome retaining already received headers", async () => {
  const body = new ReadableStream({ start(controller) { controller.error(new TypeError("Connection lost")); } });
  const api = createApiClient({ fetchFn: async () => new Response(body, {
    status: 200, headers: { "X-Request-ID": "partial-response-id" },
  }) });
  assert.deepEqual(await api.buildNatal(intent), {
    kind: "network_error", aborted: false, status: 200, requestId: "partial-response-id", retryAfter: null,
  });
});

test("caller AbortSignal is forwarded without adding timers or a retry", async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  const api = createApiClient({ fetchFn: async (_path, { signal }) => {
    calls += 1;
    assert.equal(signal, controller.signal);
    throw signal.reason;
  } });
  assert.equal((await api.searchPlaces("Москва", { signal: controller.signal })).aborted, true);
  assert.equal(calls, 1);
});

test("separate requests and clients do not share a mutable result", async () => {
  const fetchFn = async () => jsonResponse({ items: [{ place_id: "one" }] });
  const first = createApiClient({ fetchFn });
  const second = createApiClient({ fetchFn });
  const result = await first.searchPlaces("Москва");
  result.body.items[0].place_id = "changed";
  assert.equal((await first.searchPlaces("Москва")).body.items[0].place_id, "one");
  assert.equal((await second.searchPlaces("Москва")).body.items[0].place_id, "one");
});

test("loading the page entry point makes no requests; its real client can then perform a read", async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (path, options) => {
    calls.push({ path, options });
    return jsonResponse({ status: "empty", birth: null, chart: null });
  };
  try {
    const { api } = await import("../../src/exact_orb/http_api/ui/main.mjs");
    assert.deepEqual(calls, []);
    assert.equal((await api.current()).body.status, "empty");
    assert.equal(calls.length, 1);
    assert.equal(calls[0].path, "/charts/current");
    assert.equal(calls[0].options.method, "GET");
  } finally {
    globalThis.fetch = original;
  }
});
