import { createApiClient } from "./transport.mjs";
import { createBirthForm, formatTimeInput } from "./form.mjs";
import { createPlaceSearch } from "./places.mjs";
import { createSessionCoordinator, issueMessage } from "./session.mjs";
import { mountChartResult } from "./facts.mjs";

// Загрузка модуля собирает клиент; запросы выполняются только при вызове его методов.
export const api = createApiClient();

export function mountBirthForm(document, { apiClient = api } = {}) {
  const element = document.getElementById("birth-form");
  const result = mountChartResult(document);
  element.after(result.element);
  const form = createBirthForm();
  const date = document.getElementById("birth-date");
  const place = document.getElementById("birth-place");
  const time = document.getElementById("birth-time");
  const unknown = document.getElementById("time-unknown");
  const acknowledged = document.getElementById("terms-acknowledged");
  const list = document.getElementById("place-list");
  const status = document.getElementById("place-status");
  const retry = document.getElementById("place-retry");
  const overallError = document.getElementById("form-error");
  const fields = { date, place, time, acknowledged };
  const build = element.querySelector('button[type="submit"]');
  const sessionStatus = document.createElement("p");
  sessionStatus.id = "session-status";
  sessionStatus.className = "hint";
  sessionStatus.setAttribute("role", "status");
  sessionStatus.setAttribute("aria-live", "polite");
  const readAgain = document.createElement("button");
  readAgain.type = "button";
  readAgain.className = "secondary-button";
  readAgain.textContent = "Повторить проверку карты";
  readAgain.hidden = true;
  element.insertBefore(sessionStatus, overallError);
  element.insertBefore(readAgain, overallError);
  let places, session, sessionState;
  let draftEdited = false, birthRestored = false;

  function renderErrors() {
    const draft = form.snapshot();
    for (const [name, input] of Object.entries(fields)) {
      const message = draft.errors[name] ?? sessionState?.fieldIssues[name]?.map(issueMessage).join(" ") ?? "";
      const error = document.getElementById(`${name}-error`);
      error.textContent = message;
      error.hidden = message === "";
      input.setAttribute("aria-invalid", String(Boolean(message
        || (name === "place" && places?.snapshot().error?.invalidInput))));
    }
    let generalMessage = Object.keys(draft.errors).length ? "Проверьте отмеченные поля." : sessionState?.error?.message ?? "";
    if (sessionState?.retryInSeconds > 0) generalMessage += ` Следующее действие доступно через ${sessionState.retryInSeconds} с.`;
    overallError.hidden = generalMessage === "";
    overallError.textContent = generalMessage;
    time.disabled = draft.timeUnknown;
    time.required = !draft.timeUnknown;
  }

  function renderSession(state) {
    sessionState = state;
    const view = state.view;
    // Восстановление не затирает ввод, сделанный во время запроса или после него.
    if (state.source === "current" && view?.birth && !draftEdited && !birthRestored) {
      const birth = view.birth;
      form.setDate(birth.birth_date);
      form.setTime(birth.birth_time ?? "");
      form.setUnknownTime(birth.time_unknown);
      // BirthViewDTO содержит подтверждённый сервером ID; метаданные каталога не выдумываются.
      form.selectPlace(birth.place);
      date.value = birth.birth_date;
      time.value = birth.birth_time ?? "";
      unknown.checked = birth.time_unknown;
      place.value = birth.place.display_name;
      status.textContent = `Сохранённое место: ${birth.place.display_name}.`;
      birthRestored = true;
    }
    let message = "";
    if (view?.status === "empty") message = "Сохранённой карты пока нет.";
    if (view?.status === "chart_ready") {
      message = view.chart_stale ? "Сохранённая карта устарела. Её можно явно пересчитать." : "Карта доступна.";
    }
    if (view?.status === "chart_unavailable") message = "Сохранённую карту не удалось открыть. Данные рождения сохранены; карту можно построить заново.";
    if (view?.birth) message += ` Дата: ${view.birth.birth_date}. Место: ${view.birth.place.display_name}. ${view.birth.time_unknown ? "Точное время неизвестно." : `Время: ${view.birth.birth_time}.`}`;
    if (state.phase === "bootstrapping") message = "Открываем сессию…";
    if (state.phase === "reading") message = "Проверяем текущую карту…";
    if (state.phase === "building") message = "Строим карту…";
    sessionStatus.textContent = message;
    build.disabled = !state.canSubmit;
    build.textContent = state.phase === "building" ? "Строим карту…" : view?.chart_stale ? "Пересчитать"
      : view?.status === "chart_unavailable" ? "Построить заново" : "Построить карту";
    element.setAttribute("aria-busy", String(state.busy));
    readAgain.hidden = !state.error || state.sessionReady || state.requiresReconciliation;
    readAgain.disabled = state.busy || state.retryInSeconds > 0;
    result.update(view);
    renderErrors();
  }

  function edited(field) {
    draftEdited = true;
    session.clearFieldError(field);
    renderErrors();
  }

  function renderPlaces(state) {
    const open = state.open && document.activeElement === place;
    list.replaceChildren();
    state.items.forEach((item, index) => {
      const option = document.createElement("li");
      option.id = `place-option-${index}`;
      option.dataset.placeIndex = String(index);
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", String(index === state.activeIndex));
      const name = document.createElement("strong");
      name.textContent = item.display_name;
      const region = document.createElement("span");
      region.textContent = `Регион: ${item.admin1_name || "—"} · Страна: ${item.country_code}`;
      option.append(name, region);
      list.append(option);
    });
    list.hidden = !open;
    place.setAttribute("aria-expanded", String(open));
    place.setAttribute("aria-busy", String(state.status === "loading" || state.status === "debouncing"));
    if (open && state.activeIndex >= 0) {
      place.setAttribute("aria-activedescendant", `place-option-${state.activeIndex}`);
      list.children[state.activeIndex].scrollIntoView({ block: "nearest" });
    } else {
      place.removeAttribute("aria-activedescendant");
    }
    let message = "";
    if (state.status === "loading" || state.status === "debouncing") message = "Ищем место…";
    if (state.status === "empty") message = "Место не найдено.";
    if (state.status === "results") message = `Найдено вариантов: ${state.items.length}. Выберите место из списка.`;
    if (state.status === "selected") {
      message = `Выбрано: ${state.selection.display_name}. Регион: ${state.selection.admin1_name || "—"}. Страна: ${state.selection.country_code}.`;
    }
    if (state.status === "error") {
      message = state.error.message;
      if (state.retryInSeconds > 0) message += ` Повторить поиск можно через ${state.retryInSeconds} с.`;
    }
    status.textContent = message;
    retry.hidden = state.status !== "error";
    retry.disabled = !state.canRetry;
    renderErrors();
  }

  places = createPlaceSearch({ searchPlaces: apiClient.searchPlaces, onChange: renderPlaces,
    onSelect(item) {
      form.selectPlace(item);
      place.value = item.display_name;
      renderErrors();
    } });
  date.value = "";
  place.value = "";
  time.value = "";
  unknown.checked = false;
  acknowledged.checked = false;
  session = createSessionCoordinator({ apiClient, form, onChange: renderSession });
  renderSession(session.snapshot());
  date.addEventListener("input", () => { form.setDate(date.value); edited("date"); });
  time.addEventListener("input", () => {
    const formatted = formatTimeInput(time.value);
    if (formatted !== time.value) {
      const start = time.selectionStart, end = time.selectionEnd, direction = time.selectionDirection;
      time.value = formatted;
      // Новое двоеточие сдвигает только ту часть выделения, которая была после часов.
      if (typeof start === "number" && typeof end === "number") {
        time.setSelectionRange(start + Number(start > 2), end + Number(end > 2), direction);
      }
    }
    form.setTime(time.value);
    edited("time");
  });
  unknown.addEventListener("change", () => { form.setUnknownTime(unknown.checked); edited("time"); });
  acknowledged.addEventListener("change", () => { form.acknowledge(acknowledged.checked); edited("acknowledged"); });
  place.addEventListener("input", () => {
    form.editPlace(place.value);
    places.setQuery(place.value);
    edited("place");
  });
  place.addEventListener("keydown", (event) => { if (places.handleKey(event.key)) event.preventDefault(); });
  place.addEventListener("focus", () => renderPlaces(places.snapshot()));
  place.addEventListener("blur", () => places.close());
  list.addEventListener("pointerdown", (event) => {
    if (event.target.closest("[data-place-index]")) event.preventDefault();
  });
  list.addEventListener("click", (event) => {
    const option = event.target.closest("[data-place-index]");
    if (option) places.select(Number(option.dataset.placeIndex));
  });
  retry.addEventListener("click", () => { places.retry(); });
  readAgain.addEventListener("click", () => { void session.open(); });
  element.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!session.snapshot().canSubmit) return;
    const result = form.prepareSubmission();
    renderErrors();
    if (!result.ok) {
      fields[Object.keys(result.errors)[0]].focus();
      return;
    }
    await session.submit();
    const issueField = Object.keys(session.snapshot().fieldIssues)[0];
    if (issueField) fields[issueField].focus();
  });
  const ready = session.open();
  return Object.freeze({ form, places, session, result, ready });
}

if (globalThis.document) mountBirthForm(globalThis.document);
