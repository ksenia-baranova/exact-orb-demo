import { createChartSelection } from "./chart_state.mjs";
import { createDrawingController } from "./result_controller.mjs";
import { createWheelRenderer } from "./wheel_svg.mjs";
import { ASPECT_COLORS } from "./wheel_layout.mjs";

// REQ-UI-04/05: только опубликованные позиции, без вычисления из longitude.
const pointNames = {
  sun: "Солнце", moon: "Луна", mercury: "Меркурий", venus: "Венера", mars: "Марс",
  jupiter: "Юпитер", saturn: "Сатурн", uranus: "Уран", neptune: "Нептун", pluto: "Плутон",
  chiron: "Хирон", true_node: "Северный узел", south_node: "Южный узел",
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
export function mountChartResult(document, { rendererFactory = createWheelRenderer, onFatal, onDrawingEvent, onAspectModeChange = () => {} } = {}) {
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
  const composition = make("div", "", "chart-composition");
  const summary = make("div", "", "chart-summary");
  const birthSummary = make("p", "", "birth-summary");
  birthSummary.id = "chart-birth-summary";
  const editButton = make("button", "Изменить данные", "secondary-button");
  editButton.id = "birth-edit"; editButton.type = "button";
  const wheel = make("div", "", "wheel-panel");
  const imageHost = make("div", "", "wheel-image"); imageHost.id = "chart-wheel";
  imageHost.setAttribute("tabindex", "-1"); imageHost.setAttribute("role", "region");
  imageHost.setAttribute("aria-label", "Колесо карты");
  const aspectToolbar = make("div", "", "aspect-toolbar"); aspectToolbar.hidden = true;
  const aspectTitle = make("h2"); aspectTitle.id = "aspect-view-title";
  const aspectClose = make("button", "Вернуться к полной карте", "secondary-button");
  aspectClose.id = "aspect-close"; aspectClose.type = "button"; aspectClose.hidden = true;
  aspectToolbar.append(aspectTitle, aspectClose);
  const imageError = make("p", "", "chart-note"); imageError.id = "wheel-error";
  imageError.setAttribute("role", "status"); imageError.hidden = true;
  const legend = make("p", "Линии: точные — сплошные, рабочие — пунктирные. Вид, пара и орбис каждого аспекта — в таблице.", "wheel-legend");
  const measureHost = make("div", "", "wheel-measure");
  measureHost.setAttribute("aria-hidden", "true"); measureHost.setAttribute("inert", "");
  summary.append(title, birthSummary, metadata, note, editButton, chatButton, chatHint);
  const colorLegend=make('section','','aspect-legend');colorLegend.id='aspect-legend';
  colorLegend.setAttribute('aria-label','Легенда аспектов');
  colorLegend.append(make('h3','Легенда аспектов'));
  const colorList=make('ul','','aspect-colors');
  for(const [type,color]of Object.entries(ASPECT_COLORS)){
    const item=make('li','','aspect-legend-item');item.dataset.aspectType=type;item.setAttribute('style','--aspect-color:'+color);
    const sample=make('span',type==='conjunction'?'☌':'','aspect-sample'+(type==='conjunction'?' conjunction-sample':''));sample.setAttribute('aria-hidden','true');
    item.append(sample,make('span',aspectNames[type]));colorList.append(item);
  }
  const styles=make('div','','aspect-styles');
  for(const [kind,text]of[['exact','Сплошная — точный аспект'],['working','Пунктир — рабочий аспект']]){
    const item=make('span','','aspect-style');const sample=make('span','','aspect-sample '+kind);sample.setAttribute('aria-hidden','true');item.append(sample,make('span',text));styles.append(item);
  }
  colorLegend.append(colorList,styles);
  wheel.append(aspectToolbar, imageHost, imageError, colorLegend, legend);
  composition.append(summary, wheel); element.append(composition, details, measureHost);
  const state = createChartSelection();
  let currentFacts = null, currentChart = null, lastKey = null, disposed = false;
  let acceptanceSeq = 0, consumedSeq = null, fontRevision = 0, lastWidth = 0, pending = Promise.resolve(true);
  const drawing = createDrawingController({ document, imageHost, measureHost, factory: rendererFactory,
    onEvent: onDrawingEvent,
    onFatal,
    onUnavailable(error) {
      imageError.hidden = error === null;
      setText(imageError, error ? "Не удалось показать колесо. Все подтверждённые данные доступны в таблицах." : "");
    } });
  function drawingSnapshot() {
    if (!currentChart) return null;
    const measured = imageHost.getBoundingClientRect?.().width ?? 328;
    lastWidth = Math.floor(measured || 328);
    return { chart: currentChart, selection: state.snapshot().selection, width: lastWidth, fontRevision, acceptanceSeq };
  }
  function redraw(patch = () => {}, options) {
    if (disposed) return;
    pending = drawing.present(() => { patch(); return drawingSnapshot(); }, options);
    // Only unexpected controller errors use the existing safe-read route.
    pending.catch(error => { if (!disposed && onFatal) onFatal(error); });
    return pending;
  }
  const resize = () => {
    if (!disposed && currentChart && Math.floor(imageHost.getBoundingClientRect?.().width || 328) !== lastWidth) redraw();
  };
  const Observer = document.defaultView?.ResizeObserver;
  const observer = Observer ? new Observer(resize) : null;
  observer?.observe(imageHost);
  const fontChanged = () => { if (!disposed && currentChart) { fontRevision++; redraw(); } };
  document.fonts?.addEventListener("loadingdone", fontChanged);

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
  function activatePoint(row) { redraw(() => { state.activatePoint(row.data.id); renderFacts(); }); }
  let aspectReturn = null;
  function activateAspect(row) {
    aspectReturn = [...aspectTable.node.querySelectorAll("button")].find(node => node === document.activeElement) ?? aspectReturn;
    const frame = redraw(() => { state.activateAspect(row.aspectKey); renderFacts(); });
    if (state.snapshot().selection?.kind === "aspect") {
      imageHost.focus({ preventScroll: true });
      const scroll = () => {
        if (imageHost.style && aspectToolbar.getBoundingClientRect) {
          imageHost.style.scrollMarginTop = Math.ceil(aspectToolbar.getBoundingClientRect().height) + 24 + "px";
        }
        imageHost.scrollIntoView?.({ block: "start", behavior: "auto" });
      };
      scroll();
      // Reflow after the accepted frame can change page height. Do not steal focus
      // or scroll after the user has left the wheel or the selection has changed.
      frame?.then(current => {
        if (current && !disposed && document.activeElement === imageHost
          && state.snapshot().selection?.key === row.aspectKey) scroll();
      }, () => {}); // redraw already forwards owner failures to onFatal.
    }
  }
  function closeAspect() {
    const selected = state.snapshot().selection;
    if (selected?.kind !== "aspect") return;
    redraw(() => { state.activateAspect(selected.key); renderFacts(); });
    if (available(aspectReturn)) aspectReturn.focus();
    else aspectTable.node.querySelector("button")?.focus();
  }
  aspectClose.addEventListener("click", closeAspect);
  const wheelKey = event => { if (event.key === "Escape" && state.snapshot().selection?.kind === "aspect") {
    event.preventDefault(); closeAspect();
  } };
  imageHost.addEventListener("keydown", wheelKey);
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
  const pointDisclosure = disclosure("points", "points-table", () => state.togglePoints());
  points.node.append(pointDisclosure.button);
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
  const within = (node, parent) => { for(let at=node;at;at=at.parentNode)if(at===parent)return true;return false; };
  const available = node => {
    if(!node || node.disabled || !within(node,element))return false;
    for(let at=node;at;at=at.parentNode)if(at.hidden)return false;
    return true;
  };
  function renderFacts() {
    if (!currentFacts) return;
    const active=document.activeElement, ownedFocus=within(active,element);
    const facts = currentFacts, snapshot = state.snapshot(), selected = snapshot.selection;
    const aspect = selected?.kind === "aspect" ? currentChart.aspects[snapshot.visibleAspectIndices[0]] : null;
    const endpoints = new Set(aspect ? [aspect.from, aspect.to] : []);
    const endpointPoints = currentChart.points.filter(point => endpoints.has(point.id));
    const endpointHouses = new Set(endpointPoints.map(point => point.house).filter(house => house !== null));
    element.dataset.aspectFocus = String(Boolean(aspect));
    summary.hidden = Boolean(aspect); aspectToolbar.hidden = !aspect; aspectClose.hidden = !aspect;
    imageHost.setAttribute("aria-label", aspect ? "Аспект: " + endpointName(aspect.from) + " — " + endpointName(aspect.to) : "Колесо карты");
    setText(aspectTitle, aspect ? endpointName(aspect.from) + " — " + endpointName(aspect.to) + " · " + label(aspectNames, aspect.type) : "");
    onAspectModeChange(Boolean(aspect));
    setSection(points, facts.points); setSection(houses, facts.houses); setSection(aspects, facts.aspects);
    pointTable.patch(facts.points.rows.map((row, index) => ({ key: row.id, data: row,
      hidden: aspect ? !endpoints.has(row.id) : !snapshot.pointsExpanded && index >= 5,
      selected: selected?.kind === "point" && selected.id === row.id, label: "Выбрать точку: " + row.name })));
    houseTable.patch((facts.houses.rows ?? []).map((row, index) => ({ key: row.number, data: row,
      hidden: aspect ? !endpointHouses.has(row.number) : !snapshot.housesExpanded && index >= 5 })));
    angleTable.patch((facts.houses.angles ?? []).filter(row => !aspect || endpoints.has(row.id)).map((row) => ({ key: row.id, data: row })));
    setDisclosure(pointDisclosure, facts.points.rows.length, snapshot.pointsExpanded, !aspect);
    setDisclosure(houseDisclosure, facts.houses.rows?.length ?? 0, snapshot.housesExpanded, !aspect);
    if (aspect) {
      setText(aspects.headingNode, "Выбранный аспект");
      setText(points.headingNode, "Планеты аспекта · " + endpointPoints.length);
      points.empty.hidden = endpointPoints.length > 0;
      if (!endpointPoints.length) setText(points.empty, "В этом аспекте участвуют углы карты.");
      setText(houses.headingNode, "Дома планет аспекта · " + endpointHouses.size);
      const angleIds = [...endpoints].filter(id => Object.hasOwn(currentChart.angles ?? {}, id));
      if (angleIds.length) {
        setText(houses.info, "Для угла " + angleIds.map(endpointName).join(", ") + " дом не назначается.");
        houses.info.hidden = false;
      }
      if (facts.houses.rows !== null) {
        houses.empty.hidden = endpointHouses.size > 0;
        if (!endpointHouses.size) setText(houses.empty, "Для участников аспекта дома не опубликованы.");
      }
    }
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
    warnings.hidden = warned.size === 0 || Boolean(aspect);
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
    if(ownedFocus && !available(active)) {
      const candidates=[aspectClose,pointDisclosure.button,aspectDisclosure.button,houseDisclosure.button,...aspectTable.node.querySelectorAll("button"),
        ...pointTable.node.querySelectorAll("button"),editButton];
      candidates.find(available)?.focus();
    }
    const legendHost=aspect?wheel:summary;
    if(colorLegend.parentNode!==legendHost)legendHost.append(colorLegend);
    const graphical=snapshot.sourceRows.filter(row=>row.selectable && currentChart.aspects[row.index].category!=="background").length;
    setText(legend, selected?.kind==="aspect" && currentChart.aspects[snapshot.visibleAspectIndices[0]]?.category==="background"
      ? "Выбран фоновый аспект: показаны два конца без линии. Все числовые факты — в таблице."
      : graphical ? "Точные аспекты — сплошные линии, рабочие — пунктирные. Соединение — ☌. Пара, тип и орбис — в таблице."
      : "Графических аспектов в этой карте нет. Положения и все опубликованные строки доступны в таблицах.");
    setText(legend, "Значки могут быть сдвинуты внутри дома для читаемости. Точные положения — в таблице. " + legend.textContent);
    if (aspect) setText(legend, legend.textContent + " Escape — вернуться к полной карте.");
  }
  let warningSequence = 0;
  const tables = [pointTable, houseTable, angleTable, aspectTable];
  return Object.freeze({ element,
    update(view, { acceptance = null, summary: summaryText = "" } = {}) {
      if (disposed) return;
      const facts = view?.status === "chart_ready" && view.chart ? readChartFacts(view.chart) : null;
      const key = JSON.stringify([view?.chart, view?.status, view?.chart_stale, acceptance?.seq, summaryText]);
      if (key === lastKey) return;
      // A partial failed patch invalidates even the previously rendered cache entry.
      lastKey = null;
      const replace = acceptance ? acceptance.seq !== consumedSeq : view?.chart !== currentChart;
      const apply = () => {
      if (acceptance && acceptance.seq !== consumedSeq) {
        if (acceptance.reset) state.accept(null);
        consumedSeq = acceptance.seq; acceptanceSeq = acceptance.seq;
      }
      state.accept(facts === null ? null : view.chart);
      currentChart = facts === null ? null : structuredClone(view.chart);
      setText(birthSummary, summaryText); birthSummary.hidden = summaryText === "";
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
        element.dataset.aspectFocus = "false"; summary.hidden = false;
        aspectToolbar.hidden = true; aspectClose.hidden = true; onAspectModeChange(false);
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
      };
      return redraw(apply, { replace });
    },
    editButton,
    get settled() { return pending; },
    dispose() {
      if (disposed) return;
      disposed = true;
      drawing.close(); observer?.disconnect(); document.fonts?.removeEventListener("loadingdone", fontChanged);
      for (const table of tables) table.dispose();
      pointDisclosure.dispose(); houseDisclosure.dispose(); aspectDisclosure.dispose(); aspectClose.removeEventListener("click", closeAspect); imageHost.removeEventListener("keydown", wheelKey);
    },
  });
}
