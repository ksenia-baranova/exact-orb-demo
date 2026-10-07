// Существующие HTTP golden и настоящие form/coordinator/transport; заменена только листовая сеть.
import { readFileSync } from "node:fs";
import { createBirthForm } from "../../../src/exact_orb/http_api/ui/form.mjs";
import { createApiClient } from "../../../src/exact_orb/http_api/ui/transport.mjs";
import { createSessionCoordinator } from "../../../src/exact_orb/http_api/ui/session.mjs";

export const views = JSON.parse(readFileSync(new URL("../../http_api/golden/session_view.json", import.meta.url), "utf8"));
export const charts = JSON.parse(readFileSync(new URL("../../http_api/golden/chart_dto.json", import.meta.url), "utf8"));
const placeFixture = JSON.parse(readFileSync(new URL("../../fixtures/places.jsonl", import.meta.url), "utf8").split("\n")[0]);
export const place = { place_id: placeFixture.place_id, display_name: placeFixture.name,
  admin1_name: placeFixture.admin1, country_code: placeFixture.country };
export const bootstrapPath = "/session/bootstrap", currentPath = "/charts/current", buildPath = "/charts/natal";
export const ready = (stale = false, unknown = false) => ({ ...structuredClone(views[unknown ? "unknown_ready" : "known_ready"]),
  chart: structuredClone(charts[unknown ? "cosmogram" : "natal"]), chart_stale: stale });
export const committed = (chart = charts.natal) => ({ status: "chart_ready", state_version: 2, chart });
export function response(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "X-Request-ID": "controlled-request", ...extra } });
}
export function failure(code, issues = null) {
  return { code, detail_code: null, user_message: "Проверьте введённые данные.", retryable: false, issues };
}
export function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
export function fakeClock() {
  let now = 0, id = 0;
  const tasks = new Map();
  return { now: () => now,
    set(callback, milliseconds) { const handle = ++id; tasks.set(handle, { at: now + milliseconds, callback }); return handle; },
    clear(handle) { tasks.delete(handle); },
    advance(milliseconds) {
      now += milliseconds;
      const jobs = [];
      for (const [handle, task] of [...tasks]) if (task.at <= now) { tasks.delete(handle); jobs.push(task.callback()); }
      return Promise.all(jobs);
    } };
}
export function harness() {
  const form = createBirthForm();
  form.setDate("1985-09-02"); form.setTime("14:30"); form.selectPlace(place); form.acknowledge(true);
  const queues = new Map(), calls = [], changes = [], clock = fakeClock(), observers = new Map();
  const apiClient = createApiClient({ fetchFn: async (path, options) => {
    calls.push({ path, options: { ...options }, body: options.body ? JSON.parse(options.body) : null });
    observers.get(path)?.resolve(); observers.delete(path);
    const next = queues.get(path)?.shift();
    if (next instanceof Error) throw next;
    if (next !== undefined) return await next;
    if (path === bootstrapPath) return response({ status: "ready", state_version: 99 });
    if (path === currentPath) return response(views.empty);
    if (path === buildPath) return response(committed());
    throw new Error(`Unexpected leaf request ${path}`);
  } });
  const coordinator = createSessionCoordinator({ apiClient, form, clock, onChange: (state) => changes.push(state) });
  return { form, calls, changes, coordinator, clock, apiClient,
    entered(path) { const event = deferred(); observers.set(path, event); return event.promise; },
    queue(path, ...items) { queues.set(path, [...(queues.get(path) ?? []), ...items]); },
    builds: () => calls.filter((call) => call.path === buildPath),
  };
}
