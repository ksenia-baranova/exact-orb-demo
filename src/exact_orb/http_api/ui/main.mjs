import { createApiClient } from "./transport.mjs";
import { createBirthForm } from "./form.mjs";
import { createPlaceSearch } from "./places.mjs";

// Загрузка модуля собирает клиент; запросы выполняются только при вызове его методов.
export const api = createApiClient();

export function mountBirthForm(document, { apiClient = api } = {}) {
  const element = document.getElementById("birth-form");
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
  let places;

  function renderErrors() {
    const draft = form.snapshot();
    for (const [name, input] of Object.entries(fields)) {
      const message = draft.errors[name] ?? "";
      const error = document.getElementById(`${name}-error`);
      error.textContent = message;
      error.hidden = message === "";
      input.setAttribute("aria-invalid", String(Boolean(message
        || (name === "place" && places?.snapshot().error?.invalidInput))));
    }
    overallError.hidden = Object.keys(draft.errors).length === 0;
    overallError.textContent = overallError.hidden ? "" : "Проверьте отмеченные поля.";
    time.disabled = draft.timeUnknown;
    time.required = !draft.timeUnknown;
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
  renderErrors();
  date.addEventListener("input", () => { form.setDate(date.value); renderErrors(); });
  time.addEventListener("input", () => { form.setTime(time.value); renderErrors(); });
  unknown.addEventListener("change", () => { form.setUnknownTime(unknown.checked); renderErrors(); });
  acknowledged.addEventListener("change", () => { form.acknowledge(acknowledged.checked); renderErrors(); });
  place.addEventListener("input", () => {
    form.editPlace(place.value);
    places.setQuery(place.value);
    renderErrors();
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
  element.addEventListener("submit", (event) => {
    event.preventDefault();
    const result = form.prepareSubmission();
    renderErrors();
    if (!result.ok) {
      fields[Object.keys(result.errors)[0]].focus();
      return;
    }
    // Форма выдаёт проверенный intent; session/build coordinator подключается в DEV-UI-03.
    element.dispatchEvent(new document.defaultView.CustomEvent("birth-intent", { bubbles: true, detail: result.intent }));
  });
  return Object.freeze({ form, places });
}

if (globalThis.document) mountBirthForm(globalThis.document);
