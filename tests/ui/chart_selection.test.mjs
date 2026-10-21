// TASK-D-007 / CH-02/03: REQ-WHEEL-04/07/08/09/10, AS-WHEEL-11/13/28/29/30.
// Source facts and order come from the public DTO fixture, never from a finder.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { mountChartResult } from "../../src/exact_orb/http_api/ui/facts.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { aspectKey, createChartSelection } from "../../src/exact_orb/http_api/ui/chart_state.mjs";
import { harness, response, currentPath } from "./fixtures/session.mjs";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";

const natal = JSON.parse(readFileSync(new URL("./fixtures/natal_1985_chart_dto.json", import.meta.url), "utf8"));
const ready = (chart) => ({ status: "chart_ready", chart, chart_stale: false });
const visibleRows = (root, group) => root.querySelector(`#facts-${group}`).parentNode
  .querySelector("tbody").children.filter((row) => !row.hidden);
const point = (root, id) => root.querySelector(`[data-point-id="${id}"]`);

function mounted(chart = structuredClone(natal)) {
  const document = documentPort(), result = mountChartResult(document);
  document.root.append(result.element);
  result.update(ready(chart));
  return { document, result, root: result.element, chart };
}

test("Owner: all three fact tables have independent first-five disclosure", () => {
  const { root, chart } = mounted();
  assert.equal(root.querySelector("#chart-facts").hidden, false);
  assert.equal(root.querySelector("#chart-details-button"), null);
  assert.equal(visibleRows(root, "points").length, 5);
  assert.deepEqual(visibleRows(root, "points").map(row => row.querySelector("button").dataset.pointId), chart.points.slice(0,5).map(row => row.id));
  const points = root.querySelector("#points-show-all");
  assert.equal(points.getAttribute("aria-controls"), "points-table");
  assert.equal(points.getAttribute("aria-expanded"), "false");
  points.click();
  assert.equal(visibleRows(root, "points").length, chart.points.length);
  assert.equal(points.getAttribute("aria-expanded"), "true");
  assert.equal(visibleRows(root, "aspects").length, 5);
  assert.equal(visibleRows(root, "houses").length, 5);
  root.querySelector("#aspects-show-all").click();
  assert.equal(visibleRows(root, "aspects").length, chart.aspects.length);
  assert.equal(visibleRows(root, "houses").length, 5);
  root.querySelector("#houses-show-all").click();
  assert.equal(visibleRows(root, "houses").length, 12);
  points.click();
  assert.equal(visibleRows(root, "points").length, 5);
  assert.equal(visibleRows(root, "houses").length, 12);
  assert.equal(visibleRows(root, "aspects").length, chart.aspects.length);
});

test("AS-WHEEL-11/13: one point replaces another; toggle resets only the general aspects disclosure", () => {
  const { root, chart, document } = mounted();
  const houses = root.querySelector("#houses-show-all");
  assert.ok(houses, "houses have an independent disclosure control");
  houses.click();
  root.querySelector("#aspects-show-all").click();
  const moon = point(root, "moon");
  assert.ok(moon, "published Moon has a native HTML selection control");
  moon.focus();
  moon.click();
  assert.equal(document.activeElement, moon);
  assert.equal(moon.getAttribute("aria-pressed"), "true");
  assert.equal(visibleRows(root, "aspects").length,
    chart.aspects.filter((row) => row.from === "moon" || row.to === "moon").length);
  point(root, "sun").click();
  assert.equal(moon.getAttribute("aria-pressed"), "false");
  assert.equal(point(root, "sun").getAttribute("aria-pressed"), "true");
  point(root, "sun").click();
  assert.equal(visibleRows(root, "aspects").length, 5);
  assert.equal(visibleRows(root, "houses").length, 12);
});

test("AS-WHEEL-28: S1 counts the full DTO before filtering; all source rows survive", () => {
  const chart = structuredClone(natal);
  const first = chart.aspects[0];
  chart.aspects.push({ ...first, from: first.to, to: first.from, category: "background", orb: 2.25 });
  const before = structuredClone(chart), { root } = mounted(chart);
  const firstButton = visibleRows(root, "aspects")[0].querySelector("button");
  assert.ok(firstButton, "the row exposes an explicit unavailable selection control");
  assert.equal(firstButton.disabled, true);
  const warning = root.querySelector("#aspect-warnings");
  assert.equal(warning.hidden, false);
  assert.match(warning.textContent, /несколько записей/);
  root.querySelector("#aspects-show-all").click();
  assert.equal(visibleRows(root, "aspects").length, chart.aspects.length);
  assert.deepEqual(chart, before);
});

test("AS-WHEEL-12/13: a unique aspect focuses its wheel; closing it restores general five/all", () => {
  const { root, document, chart } = mounted();
  root.querySelector("#aspects-show-all").click();
  point(root, "moon").click();
  const chosenRow = visibleRows(root, "aspects").find((row) => !row.querySelector("button").disabled);
  const chosen = chosenRow.querySelector("button"); chosen.focus(); chosen.click();
  assert.equal(visibleRows(root, "aspects").length, 1);
  assert.equal(visibleRows(root, "aspects")[0], chosenRow);
  assert.equal(document.activeElement === root.querySelector("#chart-wheel"), true);
  assert.equal(chosen.getAttribute("aria-pressed"), "true");
  assert.equal(point(root, "moon").getAttribute("aria-pressed"), "false");
  root.querySelector("#aspect-close").click();
  assert.equal(visibleRows(root, "aspects").length, chart.aspects.length);
  assert.equal(document.activeElement, chosen);
  assert.equal(chosen.getAttribute("aria-pressed"), "false");
  assert.equal(root.querySelector("#aspects-show-all").getAttribute("aria-expanded"), "true");
});

test("AS-WHEEL-30: automatic accepted DTO reconciles unordered pair/type and displays its new facts", () => {
  const chart = structuredClone(natal), { result, root, document } = mounted(chart);
  root.querySelector("#houses-show-all").click();
  const selected = visibleRows(root, "aspects")[0].querySelector("button");
  selected.focus(); selected.click();
  const next = structuredClone(chart), row = next.aspects[0];
  [row.from, row.to] = [row.to, row.from]; row.category = "background"; row.orb = 1.025;
  next.chart_identity += "-automatic";
  result.update(ready(next));
  const current = visibleRows(root, "aspects");
  assert.equal(current.length, 1);
  assert.equal(current[0].querySelector("button"), selected);
  assert.equal(document.activeElement === root.querySelector("#chart-wheel"), true);
  assert.equal(current[0].children[3].textContent, "Фоновый");
  assert.equal(current[0].children[4].textContent, "1°02′");
  const endpoints=new Set([row.from,row.to]);
  const endpointHouses=new Set(next.points.filter(p=>endpoints.has(p.id)).map(p=>p.house).filter(n=>n!==null));
  assert.equal(visibleRows(root, "houses").length, endpointHouses.size);
  root.querySelector("#aspect-close").click();
  assert.equal(visibleRows(root, "houses").length, 12);
  assert.deepEqual(chart, natal);
});

test("AS-WHEEL-29/30: duplicate/reversed/category variants disable only their full-source group", () => {
  for (const variant of ["identical", "reverse", "category", "orb"]) {
    const chart = structuredClone(natal), state = createChartSelection();
    state.accept(chart); state.toggleAspects(); state.toggleHouses();
    const key = aspectKey(chart.aspects[0]); state.activateAspect(key);
    const duplicate = { ...chart.aspects[0] };
    if (variant === "reverse") [duplicate.from, duplicate.to] = [duplicate.to, duplicate.from];
    if (variant === "category") duplicate.category = "background";
    if (variant === "orb") duplicate.orb += 1;
    chart.aspects.push(duplicate); state.accept(chart);
    const view = state.snapshot();
    assert.equal(view.selection, null, variant);
    assert.equal(view.aspectsExpanded, true); assert.equal(view.housesExpanded, true);
    assert.equal(view.sourceRows.length, chart.aspects.length);
    assert.deepEqual(view.ambiguousGroups[0].indices, [0, chart.aspects.length - 1]);
    state.activatePoint(chart.aspects[0].from);
    const pointSelection = state.snapshot().selection;
    state.activateAspect(key); assert.deepEqual(state.snapshot().selection, pointSelection);
    const unique = view.sourceRows.find((row) => row.selectable);
    assert.ok(unique, "unaffected address remains selectable");
    state.activateAspect(unique.key); assert.equal(state.snapshot().selection.key, unique.key);
    state.activateAspect(key); assert.equal(state.snapshot().selection.key, unique.key);
    chart.aspects.pop(); state.accept(chart);
    assert.equal(state.snapshot().ambiguousGroups.length, 0);
    assert.equal(state.snapshot().selection.key, unique.key, "unique recovery does not auto-select the old address");
  }
});

test("AS-WHEEL-28: different published type is a different address; sole reverse and background are ordinary", () => {
  const chart = structuredClone(natal);
  chart.aspects = [{ from: "moon", to: "sun", type: "square", category: "background", orb: 1 },
    { from: "sun", to: "moon", type: "trine", category: "exact", orb: 0 }];
  const { root } = mounted(chart);
  assert.equal(root.querySelector("#aspect-warnings").hidden, true);
  for (const row of visibleRows(root, "aspects")) assert.equal(row.querySelector("button").disabled, false);
  visibleRows(root, "aspects")[0].querySelector("button").click();
  assert.equal(visibleRows(root, "aspects").length, 1);
  assert.equal(visibleRows(root, "aspects")[0].children[3].textContent, "Фоновый");
});

test("AS-WHEEL-11/28: point filter includes background, angles and ambiguous occurrences in DTO order", () => {
  const chart = structuredClone(natal);
  chart.aspects = [{ from: "sun", to: "moon", type: "trine", category: "background", orb: 1 },
    { from: "moon", to: "asc", type: "square", category: "exact", orb: 0 },
    { from: "moon", to: "sun", type: "trine", category: "working", orb: 2 },
    { from: "sun", to: "mc", type: "sextile", category: "exact", orb: 0 }];
  const { root } = mounted(chart); point(root, "moon").click();
  const rows = visibleRows(root, "aspects");
  assert.equal(rows.length, 3);
  assert.deepEqual(rows.map((row) => row.children[3].textContent), ["Фоновый", "Точный", "Рабочий"]);
  assert.deepEqual(rows.map((row) => row.querySelector("button").disabled), [true, false, true]);
  assert.match(rows[1].textContent, /ASC/);
  assert.equal(point(root, "moon").getAttribute("aria-pressed"), "true");
});

test("AS-WHEEL-30: absent selection alone clears on acceptance; point selection and expansions otherwise persist", () => {
  const chart = structuredClone(natal), state = createChartSelection(); state.accept(chart);
  state.toggleAspects(); state.toggleHouses(); state.activatePoint("moon");
  state.accept({ ...chart, chart_identity: "automatic-B" });
  assert.deepEqual(state.snapshot().selection, { kind: "point", id: "moon" });
  state.accept({ ...chart, points: chart.points.filter(({ id }) => id !== "moon") });
  assert.equal(state.snapshot().selection, null);
  assert.equal(state.snapshot().aspectsExpanded, true); assert.equal(state.snapshot().housesExpanded, true);
  state.accept(null);
  assert.equal(state.snapshot().aspectsExpanded, false); assert.equal(state.snapshot().housesExpanded, false);
  assert.equal(state.snapshot().sourceRows.length, 0);
});

test("accepted addressing state does not share mutable DTO or snapshots", () => {
  const chart = structuredClone(natal), state = createChartSelection(); state.accept(chart);
  const key = aspectKey(chart.aspects[0]);
  chart.aspects[0].type = "mutated"; chart.points.length = 0;
  state.activateAspect(key); const first = state.snapshot();
  first.selection.key = "mutated"; first.sourceRows.length = 0;
  assert.equal(state.snapshot().selection.key, key);
  assert.equal(state.snapshot().sourceRows.length, natal.aspects.length);
  state.activatePoint("moon"); assert.equal(state.snapshot().selection.id, "moon");
});

test("AS-WHEEL-23/30: point controls and focus survive updates; detached/disposed callbacks cannot select B", () => {
  const { result, root, document, chart } = mounted();
  const moon = point(root, "moon"); moon.focus(); moon.click();
  const next = structuredClone(chart); next.points.find(({ id }) => id === "moon").degree = 11;
  result.update(ready(next));
  assert.equal(point(root, "moon"), moon); assert.equal(document.activeElement, moon);
  assert.match(moon.parentNode.parentNode.textContent, /11°/);
  const oldAspect = visibleRows(root, "aspects")[0].querySelector("button");
  result.update(ready({ ...next, aspects: [] }));
  oldAspect.click(); assert.equal(moon.getAttribute("aria-pressed"), "true");
  assert.match(root.textContent, /У выбранной точки нет опубликованных аспектов/);
  result.dispose(); moon.click(); assert.equal(moon.getAttribute("aria-pressed"), "true");
});

test("REQ-WHEEL-11: mounted HTML activation and reveal perform no HTTP or draft changes", async () => {
  const h = harness(), document = documentPort();
  const view = JSON.parse(readFileSync(new URL("../http_api/golden/session_view.json", import.meta.url), "utf8")).known_ready;
  view.chart = structuredClone(natal); h.queue(currentPath, response(view));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  try {
    assert.equal(await ui.ready, true);
    const requests = () => h.calls.map(({ path, body }) => ({ path, body }));
    const calls = structuredClone(requests()), draft = ui.form.snapshot();
    const root = ui.result.element;
    root.querySelector("#aspects-show-all").click(); point(root, "moon").click();
    visibleRows(root, "aspects").find((row) => !row.querySelector("button").disabled).querySelector("button").click();
    root.querySelector("#houses-show-all").click();
    assert.deepEqual(requests(), calls); assert.deepEqual(ui.form.snapshot(), draft);
  } finally { ui.dispose(); }
});


test("Owner points disclosure: preserve automatic updates and aspect endpoints; reset new accepted birth once", () => {
  const chart=structuredClone(natal),{root,result,document}=mounted(chart);
  const reveal=root.querySelector("#points-show-all");
  assert.ok(reveal,"points expose their own native disclosure");
  reveal.focus(); reveal.click();
  assert.equal(document.activeElement,reveal);
  result.update(ready({...chart,chart_identity:"automatic-update"}),{acceptance:{seq:1,reset:false}});
  assert.equal(visibleRows(root,"points").length,chart.points.length);
  assert.equal(root.querySelector("#points-show-all"),reveal);
  reveal.click();
  const late=chart.points[chart.points.length-1].id;
  root.querySelector("#aspects-show-all").click();
  const chosen=visibleRows(root,"aspects").find(row=>{
    const index=root.querySelector("#aspects-table").querySelector("tbody").children.indexOf(row);
    const aspect=chart.aspects[index]; return aspect.from===late || aspect.to===late;
  });
  assert.ok(chosen,"positive late-point aspect exists in source fixture");
  chosen.querySelector("button").click();
  assert.equal(reveal.hidden,true);
  assert.ok(visibleRows(root,"points").some(row=>row.querySelector("button").dataset.pointId===late));
  root.querySelector("#aspect-close").click();
  assert.equal(visibleRows(root,"points").length,5);
  reveal.click();
  result.update(ready({...chart,chart_identity:"new-birth"}),{acceptance:{seq:2,reset:true}});
  assert.equal(visibleRows(root,"points").length,5);
  reveal.click();
  result.update(ready({...chart,chart_identity:"new-birth"}),{acceptance:{seq:2,reset:true}});
  assert.equal(visibleRows(root,"points").length,chart.points.length,"same accepted event does not collapse twice");
  result.dispose(); reveal.click();
  assert.equal(visibleRows(root,"points").length,chart.points.length,"disposed disclosure has no listener");
});

test("Owner points disclosure: no redundant button for five or fewer and safe focus after collapse", () => {
  for(const count of [0,2,5]) {
    const chart=structuredClone(natal); chart.points=chart.points.slice(0,count); chart.aspects=[];
    const {root,result}=mounted(chart);
    assert.equal(visibleRows(root,"points").length,count);
    assert.equal(root.querySelector("#points-show-all").hidden,true);
    result.dispose();
  }
  const {root,result,document,chart}=mounted(),reveal=root.querySelector("#points-show-all");
  reveal.click();
  const late=point(root,chart.points[chart.points.length-1].id); late.focus(); late.click();
  assert.equal(document.activeElement,late,"planet selection does not move focus");
  reveal.click();
  assert.equal(document.activeElement,reveal,"hidden focused row falls back to live disclosure");
  assert.equal(late.getAttribute("aria-pressed"),"true","collapsing presentation preserves selection");
  result.dispose();
});
