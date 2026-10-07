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
  const total = Math.round(orb * 60);
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

// REQ-UI-03/10, AS-UI-22: навигация только внутри уже подтверждённого ChartDTO.
export function mountChartResult(document) {
  const make = (tag, text = "", className = "") => {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = className;
    return node;
  };
  const element = make("section", "", "chart-result");
  element.id = "chart-result";
  element.hidden = true;
  element.setAttribute("aria-labelledby", "chart-result-title");
  const title = make("h2"); title.id = "chart-result-title";
  const metadata = make("p", "", "chart-meta");
  const note = make("p", "", "chart-note");
  const actions = make("div", "", "result-actions");
  const detailsButton = make("button", "Показать подробности карты", "primary-button");
  detailsButton.id = "chart-details-button";
  detailsButton.type = "button";
  detailsButton.setAttribute("aria-controls", "chart-facts");
  detailsButton.setAttribute("aria-expanded", "false");
  const chatButton = make("button", "Открыть чат", "secondary-button");
  chatButton.type = "button";
  chatButton.disabled = true;
  chatButton.tabIndex = -1;
  chatButton.setAttribute("aria-describedby", "chart-chat-hint");
  const chatHint = make("p", "Чат пока недоступен.", "hint"); chatHint.id = "chart-chat-hint";
  actions.append(detailsButton, chatButton);
  const details = make("div", "", "chart-facts"); details.id = "chart-facts";
  details.hidden = true;
  element.append(title, metadata, note, actions, chatHint, details);
  let currentFacts = null, lastKey = null;

  function table(captionText, columns, rows) {
    const node = make("table", "", "facts-table");
    // Сохраняем табличную семантику и при мобильной раскладке строк через grid.
    node.setAttribute("role", "table");
    node.append(make("caption", captionText));
    const head = make("thead"), header = make("tr");
    head.setAttribute("role", "rowgroup"); header.setAttribute("role", "row");
    for (const [, name] of columns) {
      const cell = make("th", name); cell.setAttribute("scope", "col");
      cell.setAttribute("role", "columnheader"); header.append(cell);
    }
    head.append(header);
    const body = make("tbody");
    body.setAttribute("role", "rowgroup");
    for (const row of rows) {
      const line = make("tr");
      line.setAttribute("role", "row");
      columns.forEach(([key, name], index) => {
        const cell = make(index === 0 ? "th" : "td", String(row[key]));
        cell.setAttribute("role", index === 0 ? "rowheader" : "cell");
        if (index === 0) cell.setAttribute("scope", "row");
        cell.dataset.label = name;
        if (key === "position" || key === "orb") cell.className = "angular-value";
        line.append(cell);
      });
      body.append(line);
    }
    node.append(head, body);
    return node;
  }
  function section(id, heading, data, columns, captionText) {
    const node = make("section", "", "facts-group");
    const headingNode = make("h3", `${heading}${data.rows === null ? "" : ` · ${data.rows.length}`}`);
    headingNode.id = id;
    node.setAttribute("aria-labelledby", id);
    node.dataset.factGroup = id;
    node.append(headingNode);
    if (data.note) node.append(make("p", data.note, "chart-note"));
    if (data.state === "available") node.append(table(captionText, columns, data.rows));
    else node.append(make("p", data.message, "chart-note"));
    return node;
  }
  function renderFacts(facts) {
    const points = section("facts-points", "Планеты и точки", facts.points,
      [["name", "Название"], ["sign", "Знак"], ["position", "Положение"], ["house", "Дом"], ["movement", "Движение"]], "Положения планет и точек");
    const houses = section("facts-houses", "Дома", facts.houses,
      [["number", "Номер"], ["sign", "Знак"], ["position", "Куспид"]], "Куспиды домов");
    if (facts.houses.angles?.length) houses.append(table("Углы карты",
      [["name", "Угол"], ["sign", "Знак"], ["position", "Положение"]], facts.houses.angles));
    const aspects = section("facts-aspects", "Аспекты", facts.aspects,
      [["fromName", "От"], ["toName", "К"], ["typeLabel", "Вид"], ["categoryLabel", "Категория"], ["orb", "Орбис"]], "Все опубликованные аспекты");
    details.replaceChildren(points, houses, aspects);
  }
  detailsButton.addEventListener("click", () => {
    if (!currentFacts) return;
    details.hidden = !details.hidden;
    detailsButton.setAttribute("aria-expanded", String(!details.hidden));
    detailsButton.textContent = details.hidden ? "Показать подробности карты" : "Скрыть подробности карты";
  });
  return Object.freeze({ element,
    update(view) {
      const facts = view?.status === "chart_ready" && view.chart ? readChartFacts(view.chart) : null;
      const key = JSON.stringify([facts, view?.chart_stale]);
      if (key === lastKey) return;
      if (facts?.identity !== currentFacts?.identity) {
        details.hidden = true;
        detailsButton.setAttribute("aria-expanded", "false");
        detailsButton.textContent = "Показать подробности карты";
      }
      element.hidden = facts === null;
      detailsButton.disabled = facts === null;
      if (facts === null) {
        details.replaceChildren();
        title.textContent = ""; metadata.textContent = ""; note.textContent = "";
        delete element.dataset.chartIdentity;
        currentFacts = null; lastKey = key;
        return;
      }
      element.dataset.chartIdentity = facts.identity;
      title.textContent = view.chart_stale ? `${facts.title} — сохранённая карта устарела` : `${facts.title} готова`;
      metadata.textContent = `${facts.zodiac}${facts.houseSystem === null ? " · Без домов" : ` · Дома: ${facts.houseSystem}`}`;
      note.textContent = facts.note;
      note.hidden = facts.note === "";
      renderFacts(facts);
      currentFacts = facts; lastKey = key;
    },
  });
}
