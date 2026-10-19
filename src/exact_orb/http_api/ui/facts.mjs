import { createChartSelection } from "./chart_state.mjs";

// REQ-UI-04/05: только опубликованные позиции, без вычисления из longitude.
const pointNames = {
  sun: "Солнце", moon: "Луна", mercury: "Меркурий", venus: "Венера", mars: "Марс",
  jupiter: "Юпитер", saturn: "Сатурн", uranus: "Уран", neptune: "Нептун", pluto: "Плутон",
  chiron: "Хирон", true_node: "Северный узел", south_node: "Южный узел (производная позиция)",
  mean_apog: "Лилит", selena: "Селена", pars_fortune: "Парс Фортуны",
};
const signNames = {
  Aries: "Овен", Taurus: "Телец", Gemini: "Близнецы", Cancer: "Рак", Leo: "Лев", Virgo: "Дева",
  Libra: "Весы", Scorpio: "Скорпион", Sagittarius: "Стрелец", Capricorn: "Козерог",
  Aquarius: "Водолей", Pisces: "Рыбы",
};
const label = (names, code) => Object.hasOwn(names, code) ? names[code] : code;
const angleNames = { asc: "ASC — Асцендент", mc: "MC — Середина неба", vertex: "Vertex — Вертекс",
  dsc: "DSC — Десцендент", ic: "IC — Надир" };
const aspectNames = { conjunction: "Соединение", semisextile: "Полусекстиль", sextile: "Секстиль",
  square: "Квадрат", trine: "Трин", quincunx: "Квинконс", opposition: "Оппозиция" };
const categoryNames = { exact: "Точный", working: "Рабочий", background: "Фоновый" };
const endpointName = (id) => Object.hasOwn(angleNames, id) ? angleNames[id] : label(pointNames, id);
const position = (item) => ({ sign: label(signNames, item.sign), position: formatPosition(item) });
const group = (rows, message) => ({ state: rows === null ? "not_applicable" : rows.length ? "available" : "empty", rows, message });

export function formatPosition({ degree, minute }) {
  return `${String(degree).padStart(2, "0")}°${String(minute).padStart(2, "0")}′`;
}

export function formatOrb(orb) {
  const lowerMinute = Math.floor(orb * 60);
  // Проверяем половину в исходных градусах: 1.025 * 60 может дать 61.49999999999999.
  const total = lowerMinute + (orb >= (lowerMinute + 0.5) / 60 ? 1 : 0);
  return `${Math.floor(total / 60)}°${String(total % 60).padStart(2, "0")}′`;
}

export function readChartFacts(chart) {
  if (chart === null) return null;
  const byId = new Map(chart.points.map((item) => [item.id, item]));
  const points = Object.keys(pointNames).filter((id) => byId.has(id)).map((id) => {
    const point = byId.get(id);
    return { id, name: pointNames[id], ...position(point),
      house: point.house === null ? "Не определяется без времени" : String(point.house),
      retrograde: point.retrograde, movement: point.retrograde ? "R — ретроградная" : "—" };
  });
  const houses = chart.houses === null ? null : [...chart.houses].sort((a, b) => a.number - b.number)
    .map((item) => ({ number: item.number, ...position(item) }));
  const angles = chart.angles === null ? null : Object.keys(angleNames).filter((id) => Object.hasOwn(chart.angles, id))
    .map((id) => ({ id, name: angleNames[id], ...position(chart.angles[id]) }));
  const aspects = chart.aspects.map((item) => ({ from: item.from, to: item.to, type: item.type,
    category: item.category, fromName: endpointName(item.from), toName: endpointName(item.to),
    typeLabel: label(aspectNames, item.type), categoryLabel: label(categoryNames, item.category), orb: formatOrb(item.orb) }));
  const unknown = chart.kind === "cosmogram";
  return { identity: chart.chart_identity, kind: chart.kind,
    title: unknown ? "Космограмма" : "Натальная карта", zodiac: chart.zodiac === "tropical" ? "Тропический зодиак" : chart.zodiac,
    houseSystem: chart.house_system === null ? null : chart.house_system === "P" ? "Плацидус" : chart.house_system,
    note: unknown ? "Точное время неизвестно. Положения точек приведены для технического якоря, а не точного момента рождения." : "",
    points: group(points, "Опубликованные точки отсутствуют"),
    houses: { ...group(houses, houses === null ? "Для домов нужно время рождения" : "Опубликованные дома отсутствуют"), angles },
    aspects: { ...group(aspects, "Аспекты не найдены"), note: unknown
      ? "Показаны устойчивые аспекты. Орбисы — консервативные максимальные значения по допустимым минутам даты." : "" } };
}

// REQ-WHEEL-07/09/10, AS-UI-22 MODIFY: facts visible immediately; HTML owns activation.
export function mountChartResult(document) {
  const make = (tag, text = "", className = "") => {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = className;
    return node;
  };
  const setText = (node, value) => { if (node.textContent !== value) node.textContent = value; };
  const element = make("section", "", "chart-result");
  element.id = "chart-result";
  element.hidden = true;
  element.setAttribute("aria-labelledby", "chart-result-title");
  const title = make("h2"); title.id = "chart-result-title";
  const metadata = make("p", "", "chart-meta");
  const note = make("p", "", "chart-note");
  const chatButton = make("button", "Открыть чат", "secondary-button");
  chatButton.type = "button"; chatButton.disabled = true; chatButton.tabIndex = -1;
  chatButton.setAttribute("aria-describedby", "chart-chat-hint");
  const chatHint = make("p", "Чат пока недоступен.", "hint"); chatHint.id = "chart-chat-hint";
  const details = make("div", "", "chart-facts"); details.id = "chart-facts";
  element.append(title, metadata, note, chatButton, chatHint, details);
  const state = createChartSelection();
  let currentFacts = null, lastKey = null, disposed = false;

  function table(captionText, columns, id, activation) {
    const node = make("table", "", "facts-table");
    node.id = id;
    node.setAttribute("role", "table");
    const caption = make("caption", captionText);
    node.append(caption);
    const head = make("thead"), header = make("tr"), body = make("tbody");
    head.setAttribute("role", "rowgroup"); header.setAttribute("role", "row"); body.setAttribute("role", "rowgroup");
    for (const [, name] of columns) {
      const cell = make("th", name);
      cell.setAttribute("scope", "col"); cell.setAttribute("role", "columnheader");
      header.append(cell);
    }
    head.append(header); node.append(head, body);
    const records = new Map();
    function patch(rows) {
      const keep = new Set(rows.map((row) => row.key));
      for (const [key, record] of records) if (!keep.has(key)) {
        record.dispose();
        body.removeChild(record.node);
        records.delete(key);
      }
      rows.forEach((row, index) => {
        let record = records.get(row.key);
        if (!record) {
          const line = make("tr"), cells = [], button = activation ? make("button", "", "fact-select") : null;
          line.setAttribute("role", "row");
          for (const [i, [key, name]] of columns.entries()) {
            const cell = make(i === 0 ? "th" : "td");
            cell.setAttribute("role", i === 0 ? "rowheader" : "cell");
            if (i === 0) cell.setAttribute("scope", "row");
            cell.dataset.label = name;
            if (key === "position" || key === "orb") cell.className = "angular-value";
            if (i === 0 && button) cell.append(button);
            line.append(cell); cells.push(cell);
          }
          record = { node: line, cells, button, current: row };
          const click = () => { if (!disposed) activation(record.current); };
          if (button) { button.type = "button"; button.addEventListener("click", click); }
          record.dispose = () => { button?.removeEventListener("click", click); };
          records.set(row.key, record);
        }
        record.current = row;
        columns.forEach(([key], i) => setText(i === 0 && record.button ? record.button : record.cells[i], String(row.data[key])));
        record.node.hidden = row.hidden ?? false;
        if (record.button) {
          record.button.disabled = row.disabled ?? false;
          record.button.setAttribute("aria-pressed", String(Boolean(row.selected)));
          record.button.setAttribute("aria-label", row.label);
          if (activation === activatePoint) record.button.dataset.pointId = row.data.id;
          if (row.warningId) record.button.setAttribute("aria-describedby", row.warningId);
          else record.button.removeAttribute("aria-describedby");
        }
        // Do not detach/reinsert retained controls for selection/reveal/unchanged order.
        const before = body.children[index] ?? null;
        if (before !== record.node) {
          if (body.moveBefore && record.node.parentNode === body) body.moveBefore(record.node, before);
          else body.insertBefore(record.node, before);
        }
      });
      node.hidden = rows.length === 0;
    }
    return { node, caption, patch, dispose() { for (const record of records.values()) record.dispose(); } };
  }
  function activatePoint(row) { state.activatePoint(row.data.id); renderFacts(); }
  function activateAspect(row) { state.activateAspect(row.aspectKey); renderFacts(); }
  function section(id, heading) {
    const node = make("section", "", "facts-group"), headingNode = make("h3", heading);
    headingNode.id = "facts-" + id;
    node.setAttribute("aria-labelledby", headingNode.id); node.dataset.factGroup = headingNode.id;
    const info = make("p", "", "chart-note"), empty = make("p", "", "chart-note");
    node.append(headingNode, info, empty); details.append(node);
    return { node, headingNode, info, empty, heading };
  }
  const points = section("points", "Планеты и точки");
  const pointTable = table("Положения планет и точек",
    [["name", "Название"], ["sign", "Знак"], ["position", "Положение"], ["house", "Дом"], ["movement", "Движение"]],
    "points-table", activatePoint);
  points.node.append(pointTable.node);
  const houses = section("houses", "Дома");
  const houseTable = table("Куспиды домов", [["number", "Номер"], ["sign", "Знак"], ["position", "Куспид"]], "houses-table");
  const angleTable = table("Углы карты", [["name", "Угол"], ["sign", "Знак"], ["position", "Положение"]], "angles-table");
  const aspects = section("aspects", "Аспекты");
  const warnings = make("div", "", "chart-note"); warnings.id = "aspect-warnings";
  warnings.setAttribute("role", "status"); warnings.setAttribute("aria-live", "polite");
  const aspectTable = table("Все опубликованные аспекты",
    [["fromName", "От"], ["toName", "К"], ["typeLabel", "Вид"], ["categoryLabel", "Категория"], ["orb", "Орбис"]],
    "aspects-table", activateAspect);
  const warningNodes = new Map();
  function disclosure(group, target, toggle) {
    const button = make("button", "Показать все", "secondary-button");
    button.id = group + "-show-all"; button.type = "button";
    button.setAttribute("aria-controls", target);
    const click = () => { if (!disposed) { toggle(); renderFacts(); } };
    button.addEventListener("click", click);
    return { button, dispose: () => button.removeEventListener("click", click) };
  }
  const houseDisclosure = disclosure("houses", "houses-table", () => state.toggleHouses());
  const aspectDisclosure = disclosure("aspects", "aspects-table", () => state.toggleAspects());
  houses.node.append(houseTable.node, houseDisclosure.button, angleTable.node);
  aspects.node.append(warnings, aspectTable.node, aspectDisclosure.button);

  function setSection(group, data) {
    setText(group.headingNode, group.heading + (data.rows === null ? "" : " · " + data.rows.length));
    setText(group.info, data.note ?? ""); group.info.hidden = !data.note;
    setText(group.empty, data.message); group.empty.hidden = data.state === "available";
  }
  function setDisclosure(control, count, expanded, enabled = true) {
    control.button.hidden = count <= 5 || !enabled;
    control.button.setAttribute("aria-expanded", String(expanded));
    setText(control.button, expanded ? "Показать первые 5" : "Показать все");
  }
  function renderFacts() {
    if (!currentFacts) return;
    const facts = currentFacts, snapshot = state.snapshot(), selected = snapshot.selection;
    setSection(points, facts.points); setSection(houses, facts.houses); setSection(aspects, facts.aspects);
    pointTable.patch(facts.points.rows.map((row) => ({ key: row.id, data: row,
      selected: selected?.kind === "point" && selected.id === row.id, label: "Выбрать точку: " + row.name })));
    houseTable.patch((facts.houses.rows ?? []).map((row, index) => ({ key: row.number, data: row,
      hidden: !snapshot.housesExpanded && index >= 5 })));
    angleTable.patch((facts.houses.angles ?? []).map((row) => ({ key: row.id, data: row })));
    setDisclosure(houseDisclosure, facts.houses.rows?.length ?? 0, snapshot.housesExpanded);
    const visible = new Set(snapshot.visibleAspectIndices);
    const warned = new Map(snapshot.ambiguousGroups.map(({ key, indices }) => [key, indices]));
    for (const [key, entry] of warningNodes) if (!warned.has(key)) {
      warnings.removeChild(entry.node); warningNodes.delete(key);
    }
    for (const [key, indices] of warned) {
      let entry = warningNodes.get(key);
      if (!entry) {
        const node = make("p");
        // Stable within this mount; source row occurrence is never an aspect address.
        node.id = "aspect-warning-" + (++warningSequence);
        entry = { node }; warningNodes.set(key, entry); warnings.append(node);
      }
      const row = facts.aspects.rows[indices[0]];
      setText(entry.node, row.fromName + " — " + row.toName + ", " + row.typeLabel
        + ": получено несколько записей (" + indices.length + "). Все строки сохранены; выбор и графическое обозначение этой группы недоступны.");
    }
    warnings.hidden = warned.size === 0;
    const occurrence = new Map();
    aspectTable.patch(snapshot.sourceRows.map((row) => {
      const n = occurrence.get(row.key) ?? 0; occurrence.set(row.key, n + 1);
      const data = facts.aspects.rows[row.index];
      return { key: row.selectable ? row.key : row.key + ":" + n, aspectKey: row.key, data,
        hidden: !visible.has(row.index), disabled: !row.selectable, selected: row.selected,
        label: "Выбрать аспект: " + data.fromName + " — " + data.toName + ", " + data.typeLabel + ", " + data.categoryLabel,
        warningId: warningNodes.get(row.key)?.node.id };
    }));
    setDisclosure(aspectDisclosure, facts.aspects.rows.length, snapshot.aspectsExpanded, selected === null);
    setText(aspectTable.caption, selected?.kind === "point"
      ? "Аспекты: " + facts.points.rows.find(({ id }) => id === selected.id).name
      : selected?.kind === "aspect" ? "Выбранный аспект" : "Все опубликованные аспекты");
    if (selected?.kind === "point" && visible.size === 0) {
      setText(aspects.empty, "У выбранной точки нет опубликованных аспектов");
      aspects.empty.hidden = false;
    }
  }
  let warningSequence = 0;
  const tables = [pointTable, houseTable, angleTable, aspectTable];
  return Object.freeze({ element,
    update(view) {
      if (disposed) return;
      const facts = view?.status === "chart_ready" && view.chart ? readChartFacts(view.chart) : null;
      const key = JSON.stringify([facts, view?.chart_stale]);
      if (key === lastKey) return;
      // A partial failed patch invalidates even the previously rendered cache entry.
      lastKey = null;
      state.accept(facts === null ? null : view.chart);
      currentFacts = facts;
      element.hidden = facts === null;
      if (facts === null) {
        for (const table of tables) table.patch([]);
        for (const { node } of warningNodes.values()) warnings.removeChild(node);
        warningNodes.clear(); warnings.hidden = true;
        for (const group of [points, houses, aspects]) {
          setText(group.headingNode, group.heading); setText(group.info, ""); setText(group.empty, "");
        }
        setText(title, ""); setText(metadata, ""); setText(note, "");
        delete element.dataset.chartIdentity;
        lastKey = key;
        return;
      }
      element.dataset.chartIdentity = facts.identity;
      setText(title, view.chart_stale ? facts.title + " — сохранённая карта устарела" : facts.title + " готова");
      setText(metadata, facts.zodiac + (facts.houseSystem === null ? " · Без домов" : " · Дома: " + facts.houseSystem));
      setText(note, facts.note); note.hidden = facts.note === "";
      renderFacts();
      // A failed DOM patch must be retried even if the safe read returns identical facts.
      lastKey = key;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const table of tables) table.dispose();
      houseDisclosure.dispose(); aspectDisclosure.dispose();
    },
  });
}
