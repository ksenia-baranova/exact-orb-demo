// REQ-UI-03–07/10, AS-UI-07/08/09/15/19/22; approved contract @ ce25dd0.
// docs/requirements/changes/ui-birth-form-and-facts/{requirements,scenarios}.md.
// Oracle — existing HTTP golden; UI не использует внутренний artifact или расчёт.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { formatOrb, formatPosition, readChartFacts, mountChartResult } from "../../src/exact_orb/http_api/ui/facts.mjs";
import { createApiClient } from "../../src/exact_orb/http_api/ui/transport.mjs";
import { mountBirthForm } from "../../src/exact_orb/http_api/ui/main.mjs";
import { validChart } from "../../src/exact_orb/http_api/ui/response.mjs";
import { documentPort } from "./fixtures/dom.mjs";
import { harness, response, bootstrapPath, currentPath } from "./fixtures/session.mjs";

const charts = JSON.parse(readFileSync(new URL("../http_api/golden/chart_dto.json", import.meta.url), "utf8"));
// project_chart(decode_chart_artifact(tests/golden/chart_artifact_format_1_natal_1985.bin)).
// Public-only fixture: исходные числа не пересчитываются и golden не изменяется.
const fullNatal = JSON.parse(readFileSync(new URL("./fixtures/natal_1985_chart_dto.json", import.meta.url), "utf8"));
const natal = () => structuredClone(charts.natal);
const cosmogram = () => structuredClone(charts.cosmogram);
const views = JSON.parse(readFileSync(new URL("../http_api/golden/session_view.json", import.meta.url), "utf8"));
const placeFixture = JSON.parse(readFileSync(new URL("../fixtures/places.jsonl", import.meta.url), "utf8").split("\n")[0]);
const ready = (chart = natal(), stale = false) => ({ ...structuredClone(views[chart.kind === "cosmogram" ? "unknown_ready" : "known_ready"]),
  chart, chart_stale: stale });

for (const [orb, expected] of [[0, "0°00′"], [0.008, "0°00′"], [0.009, "0°01′"],
  [0.999, "1°00′"], [1.5, "1°30′"], [1 / 120, "0°01′"], [3 / 120, "0°02′"],
  // TEST-FIND-UI-013, AS-UI-07: половина, ближайшие Number по её сторонам и перенос минуты.
  [1.024, "1°01′"], [1.0249999999999997, "1°01′"], [1.025, "1°02′"],
  [1.0250000000000001, "1°02′"], [1.026, "1°02′"],
  [0.9916666666666666, "0°59′"], [59.5 / 60, "1°00′"]]) {
  test(`REQ-UI-04 orb ${orb} rounds half-up with minute carry to ${expected}`, () => {
    assert.equal(formatOrb(orb), expected);
  });
}

test("REQ-UI-04 / AS-UI-07 / TEST-FIND-UI-013: mounted current orb 1.025 rounds half-up without changing DTO or requests", async () => {
  const h = harness(), document = documentPort(), current = ready();
  current.chart.aspects[0].orb = 1.025;
  assert.equal(validChart(current.chart), true);
  const before = structuredClone(current.chart);
  h.queue(currentPath, response(current));
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  try {
    assert.equal(await ui.ready, true);
    assert.deepEqual(h.calls.map(({ path }) => path), [bootstrapPath, currentPath]);
    assert.deepEqual(ui.session.snapshot().view.chart, before);
    document.getElementById("chart-details-button").click();
    const table = document.getElementById("chart-facts").querySelectorAll("table")
      .find((node) => node.querySelector("caption").textContent === "Все опубликованные аспекты");
    const rows = table.querySelector("tbody").children;
    assert.equal(rows.length, before.aspects.length);
    assert.ok(rows[0].textContent);
    assert.equal(before.aspects[0].category, "exact");
    assert.equal(rows[0].children[3].textContent, "Точный");
    assert.deepEqual(ui.session.snapshot().view.chart, before);
    assert.deepEqual(current.chart, before);
    assert.deepEqual(h.calls.map(({ path }) => path), [bootstrapPath, currentPath]);
    assert.equal(rows[0].children[4].textContent, "1°02′");
  } finally {
    ui.dispose();
  }
});

test("published positions keep zeroes and sign boundaries, independent of longitude", () => {
  for (const [degree, minute, expected] of [[0, 0, "00°00′"], [0, 59, "00°59′"], [29, 0, "29°00′"], [29, 59, "29°59′"]]) {
    assert.equal(formatPosition({ degree, minute, longitude: 359.9999 }), expected);
  }
  const original = natal(), changed = natal();
  for (const point of changed.points) point.longitude = 0;
  for (const house of changed.houses) house.cusp_longitude = 0;
  for (const angle of Object.values(changed.angles)) angle.longitude = 0;
  const first = readChartFacts(original), second = readChartFacts(changed);
  assert.ok(first.points.rows.length > 0);
  assert.deepEqual(first, second);
});

test("reader uses canonical point order and localizes every published point/sign", () => {
  const pointIds = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
    "neptune", "pluto", "chiron", "true_node", "south_node", "mean_apog", "selena", "pars_fortune"];
  const signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  const russian = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"];
  const chart = natal();
  chart.points = pointIds.map((id, index) => ({ ...chart.points[0], id, sign: signs[index % 12],
    degree: index % 30, minute: index % 60, retrograde: index % 2 === 1 })).reverse();
  const facts = readChartFacts(chart);
  assert.deepEqual(facts.points.rows.map((row) => row.id), pointIds);
  assert.deepEqual(facts.points.rows.slice(0, 12).map((row) => row.sign), russian);
  assert.ok(facts.points.rows.every((row) => row.name !== row.id));
  assert.ok(facts.points.rows.every((row, index) => row.retrograde === (index % 2 === 1)
    && row.movement === (index % 2 === 1 ? "R — ретроградная" : "—")));
  assert.match(facts.points.rows.find((row) => row.id === "south_node").name, /производная/);
});

test("natal houses sort numerically; five published angles belong to the houses group", () => {
  const chart = natal(); chart.houses.reverse();
  const facts = readChartFacts(chart);
  assert.ok(facts.houses, "houses group must be present");
  assert.equal(facts.houses.state, "available");
  assert.deepEqual(facts.houses.rows.map((row) => row.number), [1, 2, 3]);
  assert.deepEqual(facts.houses.angles.map((row) => row.id), ["asc", "mc", "vertex", "dsc", "ic"]);
  assert.deepEqual(facts.houses.angles[0], { id: "asc", name: "ASC — Асцендент", sign: "Рак", position: "08°06′" });
  assert.equal(facts.houseSystem, "Плацидус");
});

test("all aspect rows retain endpoint/type/category and DTO order without recalculation", () => {
  const chart = natal(), before = structuredClone(chart);
  chart.aspects[0].orb = 0.999; chart.aspects[0].category = "exact";
  const facts = readChartFacts(chart);
  assert.ok(facts.aspects, "aspects group must be present");
  assert.equal(facts.aspects.rows.length, chart.aspects.length);
  assert.deepEqual(facts.aspects.rows.map(({ from, to, type, category }) => ({ from, to, type, category })),
    chart.aspects.map(({ from, to, type, category }) => ({ from, to, type, category })));
  assert.equal(facts.aspects.rows[0].orb, "1°00′");
  assert.equal(facts.aspects.rows[0].categoryLabel, "Точный");
  assert.equal(facts.aspects.rows[0].fromName, "Луна");
  assert.equal(facts.aspects.rows[0].toName, "ASC — Асцендент");
  assert.equal(facts.aspects.rows[0].typeLabel, "Квадрат");
  assert.equal(chart.aspects[0].category, "exact");
  assert.deepEqual(chart.points, before.points);
});

test("cosmogram displays only published points/stable aspects and inapplicable houses", () => {
  const chart = cosmogram(), facts = readChartFacts(chart);
  assert.ok(facts.houses && facts.aspects, "both groups must be present");
  assert.equal(facts.houses.state, "not_applicable");
  assert.equal(facts.houses.rows, null); assert.equal(facts.houses.angles, null);
  assert.equal(facts.houses.message, "Для домов нужно время рождения");
  assert.equal(facts.houseSystem, null);
  assert.deepEqual(facts.points.rows.map((row) => row.house), ["Не определяется без времени", "Не определяется без времени"]);
  assert.equal(facts.aspects.rows.length, chart.aspects.length);
  assert.match(facts.aspects.note, /консервативные/);
  assert.match(facts.note, /технического якоря/);
  assert.doesNotMatch(JSON.stringify(facts), /offset|time_dependent|noon|excluded_aspects/);
});

test("empty calculated aspects are distinct from missing/unavailable chart", () => {
  const chart = natal(); chart.aspects = [];
  const facts = readChartFacts(chart);
  assert.ok(facts.aspects, "calculated aspects group must be present");
  assert.equal(facts.aspects.state, "empty"); assert.deepEqual(facts.aspects.rows, []);
  assert.equal(facts.aspects.message, "Аспекты не найдены");
  assert.ok(facts.points.rows.length && facts.houses.rows.length);
  assert.equal(readChartFacts(null), null);
});

test("reader does not mutate DTO or share mutable rows across callers", () => {
  const chart = natal(), before = structuredClone(chart);
  const first = readChartFacts(chart); first.points.rows[0].position = "changed";
  assert.deepEqual(chart, before);
  assert.equal(readChartFacts(chart).points.rows[0].position, "09°20′");
});

test("all seven public aspect types and three categories retain stable localized labels", () => {
  const chart = natal();
  const types = ["conjunction", "semisextile", "sextile", "square", "trine", "quincunx", "opposition"];
  chart.aspects = types.map((type, index) => ({ ...chart.aspects[0], type,
    category: ["exact", "working", "background"][index % 3] }));
  const rows = readChartFacts(chart).aspects.rows;
  assert.deepEqual(rows.map((row) => row.type), types);
  assert.deepEqual(rows.map((row) => row.typeLabel), ["Соединение", "Полусекстиль", "Секстиль", "Квадрат", "Трин", "Квинконс", "Оппозиция"]);
  assert.deepEqual(rows.slice(0, 3).map((row) => row.categoryLabel), ["Точный", "Рабочий", "Фоновый"]);
});

test("DOM reader has three accessible groups and a native details button; future data stays private", () => {
  const document = documentPort(), result = mountChartResult(document);
  document.root.append(result.element);
  const chart = natal(); chart.strength = "PRIVATE_STRENGTH"; chart.configurations = "PRIVATE_CONFIGURATION";
  result.update(ready(chart));
  const root = result.element, button = root.querySelector("#chart-details-button"), details = root.querySelector("#chart-facts");
  assert.equal(root.hidden, false);
  assert.equal(root.dataset.chartIdentity, chart.chart_identity);
  assert.equal(button.type, "button"); assert.equal(button.disabled, false);
  assert.equal(button.getAttribute("aria-expanded"), "false"); assert.equal(details.hidden, true);
  button.click();
  assert.equal(button.getAttribute("aria-expanded"), "true"); assert.equal(details.hidden, false);
  assert.deepEqual(details.querySelectorAll("section").map((item) => item.dataset.factGroup), ["facts-points", "facts-houses", "facts-aspects"]);
  assert.equal(details.querySelectorAll("table").length, 4); // Углы внутри группы домов.
  assert.ok(details.querySelectorAll("table").every((item) => item.getAttribute("role") === "table"));
  assert.ok(details.querySelectorAll("caption").every((item) => item.textContent.length > 0));
  assert.ok(details.querySelectorAll("thead th").every((item) => item.getAttribute("scope") === "col"));
  assert.ok(details.querySelectorAll("tbody th").every((item) => item.getAttribute("scope") === "row"));
  assert.ok(details.textContent.includes("09°20′") && details.textContent.includes("Луна") && details.textContent.includes("Точный"));
  assert.doesNotMatch(root.textContent, /PRIVATE_|Конфигурации|Сила|Особые градусы|Стихии/);
  button.click(); assert.equal(details.hidden, true);
});

for (const kind of ["natal", "cosmogram"]) {
  test(`AS-UI-22 ${kind}: build and reload details show the same identity/facts without chat or extra requests`, async () => {
    const chart = structuredClone(charts[kind]), calls = [];
    let current = structuredClone(views.empty);
    const apiClient = createApiClient({ fetchFn: async (path, options) => {
      calls.push({ path, body: options.body ? JSON.parse(options.body) : null });
      let body;
      if (path === "/session/bootstrap") body = { status: "ready", state_version: 1 };
      else if (path === "/charts/current") body = current;
      else if (path === "/charts/natal") {
        current = ready(chart);
        body = { status: "chart_ready", state_version: 1, chart };
      } else throw new Error(`Unexpected leaf request ${path}`);
      return new Response(JSON.stringify(body), { status: 200 });
    } });
    const document = documentPort(), ui = mountBirthForm(document, { apiClient }); await ui.ready;
    assert.equal(ui.result.element.hidden, true);
    for (const [id, value] of [["birth-date", "1985-09-02"], ["birth-time", "00:45"]]) {
      const input = document.getElementById(id); input.value = value; input.emit("input");
    }
    ui.form.selectPlace({ place_id: placeFixture.place_id, display_name: placeFixture.name,
      admin1_name: placeFixture.admin1, country_code: placeFixture.country });
    if (kind === "cosmogram") {
      const unknown = document.getElementById("time-unknown"); unknown.checked = true; unknown.emit("change");
    }
    const gate = document.getElementById("terms-acknowledged"); gate.checked = true; gate.emit("change");
    await document.getElementById("birth-form").emit("submit");
    assert.equal(calls.filter((call) => call.path === "/charts/natal").length, 1);
    const sent = calls.find((call) => call.path === "/charts/natal").body;
    assert.deepEqual(sent, { birth_date: "1985-09-02", birth_time: kind === "cosmogram" ? null : "00:45", place_id: placeFixture.place_id });
    current.birth.birth_date = sent.birth_date; current.birth.birth_time = sent.birth_time;
    const before = structuredClone(calls);
    function checkResult(root) {
      assert.equal(root.hidden, false); assert.equal(root.dataset.chartIdentity, chart.chart_identity);
      const buttons = root.querySelectorAll("button"), chat = buttons.find((button) => button.textContent === "Открыть чат");
      assert.equal(chat.disabled, true); assert.equal(chat.tabIndex, -1);
      chat.click(); chat.emit("keydown", { key: "Enter" }); chat.emit("keydown", { key: " " });
      assert.equal(root.querySelectorAll("dialog").length, 0);
      root.querySelector("#chart-details-button").focus();
      root.querySelector("#chart-details-button").click();
      assert.equal(root.querySelector("#chart-facts").hidden, false);
      const factsText = root.querySelector("#chart-facts").textContent;
      assert.ok(factsText.includes(kind === "natal" ? "09°20′" : "14°00′"));
      const aspectRows = root.querySelector("#facts-aspects").parentNode.querySelectorAll("tbody tr");
      assert.equal(aspectRows.length, chart.aspects.length);
      return factsText;
    }
    const afterBuild = checkResult(ui.result.element);
    assert.deepEqual(calls, before);
    ui.places.dispose(); ui.session.dispose();
    const reloadDocument = documentPort(), reloaded = mountBirthForm(reloadDocument, { apiClient }); await reloaded.ready;
    const afterRead = structuredClone(calls);
    assert.equal(checkResult(reloaded.result.element), afterBuild);
    assert.deepEqual(calls, afterRead);
    assert.deepEqual(calls.slice(-2).map((call) => call.path), ["/session/bootstrap", "/charts/current"]);
    assert.equal(calls.filter((call) => call.path === "/charts/natal").length, 1);
    reloaded.places.dispose(); reloaded.session.dispose();
  });
}

test("switching identity closes details and removes old rows instead of mixing two charts", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  result.update(ready());
  const button = result.element.querySelector("#chart-details-button"); button.click();
  assert.ok(result.element.querySelector("#chart-facts").textContent.includes("09°20′"));
  result.update(ready(cosmogram()));
  assert.equal(result.element.dataset.chartIdentity, charts.cosmogram.chart_identity);
  assert.equal(result.element.querySelector("#chart-facts").hidden, true);
  button.click();
  assert.ok(result.element.querySelector("#chart-facts").textContent.includes("14°00′"));
  assert.ok(!result.element.querySelector("#chart-facts").textContent.includes("09°20′"));
});

test("empty/unavailable/current removal hides result and clears all numeric facts", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  for (const view of [views.empty, views.known_unavailable, null]) {
    result.update(ready()); result.element.querySelector("#chart-details-button").click();
    assert.equal(result.element.hidden, false);
    result.update(view);
    assert.equal(result.element.hidden, true);
    assert.equal(result.element.dataset.chartIdentity, undefined);
    assert.equal(result.element.querySelectorAll("table").length, 0);
    assert.equal(result.element.querySelector("#chart-details-button").disabled, true);
    assert.ok(!result.element.textContent.includes("09°20′"));
  }
});

test("stale current keeps original facts and local details without implying a new build", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  result.update(ready()); result.element.querySelector("#chart-details-button").click();
  const before = result.element.querySelector("#chart-facts").textContent;
  result.update(ready(natal(), true));
  assert.match(result.element.querySelector("#chart-result-title").textContent, /устарела/);
  assert.equal(result.element.querySelector("#chart-facts").hidden, false);
  assert.equal(result.element.querySelector("#chart-facts").textContent, before);
});

test("DOM cosmogram distinguishes inapplicable houses and calculated empty aspects", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  const chart = cosmogram(); chart.aspects = []; result.update(ready(chart));
  result.element.querySelector("#chart-details-button").click();
  const houses = result.element.querySelector("#facts-houses").parentNode;
  assert.ok(houses.textContent.includes("Для домов нужно время рождения")); assert.equal(houses.querySelectorAll("table").length, 0);
  const aspects = result.element.querySelector("#facts-aspects").parentNode;
  assert.ok(aspects.textContent.includes("Аспекты не найдены")); assert.equal(aspects.querySelectorAll("table").length, 0);
  assert.ok(result.element.querySelector("#facts-points").parentNode.querySelectorAll("tbody tr").length > 0);
  assert.match(result.element.textContent, /консервативные/);
  assert.doesNotMatch(result.element.textContent, /ASC|UTC|полдень/);
});

test("DTO strings render as text, never as executable HTML", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  const chart = natal(); chart.house_system = '<img src=x onerror="alert(1)">';
  chart.aspects[0].type = '<script>alert(1)</script>';
  result.update(ready(chart)); result.element.querySelector("#chart-details-button").click();
  assert.ok(result.element.textContent.includes(chart.house_system));
  assert.ok(result.element.textContent.includes(chart.aspects[0].type));
  assert.equal(result.element.querySelectorAll("img").length, 0); assert.equal(result.element.querySelectorAll("script").length, 0);
});

test("full golden natal renders every published point, all twelve houses and every aspect", () => {
  const document = documentPort(), result = mountChartResult(document); document.root.append(result.element);
  const before = structuredClone(fullNatal);
  result.update(ready(fullNatal)); result.element.querySelector("#chart-details-button").click();
  const points = result.element.querySelector("#facts-points").parentNode.querySelectorAll("tbody tr");
  assert.equal(points.length, 16);
  const houses = result.element.querySelector("#facts-houses").parentNode.querySelectorAll("table")[0].querySelectorAll("tbody tr");
  assert.deepEqual(houses.map((row) => row.children[0].textContent), ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]);
  assert.ok(fullNatal.aspects.length > 3);
  const aspects = result.element.querySelector("#facts-aspects").parentNode.querySelectorAll("tbody tr");
  assert.equal(aspects.length, fullNatal.aspects.length);
  const expected = readChartFacts(fullNatal).aspects.rows;
  assert.deepEqual(aspects.map((row) => row.children.map((cell) => cell.textContent)), expected.map((row) =>
    [row.fromName, row.toName, row.typeLabel, row.categoryLabel, row.orb]));
  const retrogradeCount = fullNatal.points.filter((row) => row.retrograde).length;
  assert.ok(retrogradeCount > 0);
  assert.equal(points.filter((row) => row.children[4].textContent === "R — ретроградная").length, retrogradeCount);
  assert.deepEqual(fullNatal, before);
});
