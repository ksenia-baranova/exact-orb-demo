// REQ-UI-02/10: сеть и монотонный таймер — листовые швы для управляемого поиска.
const browserClock = {
  now: () => performance.now(),
  set: (callback, milliseconds) => setTimeout(callback, milliseconds),
  clear: (handle) => clearTimeout(handle),
};

function copyItem(item) {
  return { place_id: item.place_id, display_name: item.display_name,
    admin1_name: item.admin1_name, country_code: item.country_code };
}

export function createPlaceSearch({ searchPlaces, clock = browserClock, debounceMs = 250,
  onChange, onSelect } = {}) {
  let state = { query: "", status: "idle", items: [], activeIndex: -1, open: false,
    selection: null, error: null, requestId: null, retryAfter: null };
  let generation = 0;
  let debounceTimer = null;
  let cooldownTimer = null;
  let controller = null;
  let retryAt = 0;
  let disposed = false;
  const searchable = () => Array.from(state.query.trim()).length >= 3;
  function snapshot() {
    return { ...state, items: state.items.map(copyItem),
      selection: state.selection === null ? null : copyItem(state.selection),
      error: state.status !== "error" || state.error === null ? null : { ...state.error },
      canRetry: state.status === "error" && searchable() && clock.now() >= retryAt,
      retryInSeconds: Math.max(0, Math.ceil((retryAt - clock.now()) / 1000)) };
  }
  function publish() { if (!disposed && onChange) onChange(snapshot()); }
  function cancelSearch() {
    generation += 1;
    if (debounceTimer !== null) clock.clear(debounceTimer);
    debounceTimer = null;
    controller?.abort();
    controller = null;
  }
  function cooldown() {
    if (cooldownTimer !== null) clock.clear(cooldownTimer);
    cooldownTimer = null;
    if (retryAt > clock.now()) {
      cooldownTimer = clock.set(() => { cooldownTimer = null; publish(); }, retryAt - clock.now());
    }
  }
  async function runSearch(token, query) {
    if (disposed || token !== generation) return;
    debounceTimer = null;
    controller = new AbortController();
    state.status = "loading";
    publish();
    let outcome;
    try {
      outcome = await searchPlaces(query, { signal: controller.signal });
    } catch {
      outcome = { kind: "network_error", requestId: null, retryAfter: null };
    }
    if (disposed || token !== generation) return;
    controller = null;
    state.requestId = outcome.requestId ?? null;
    state.retryAfter = outcome.retryAfter ?? null;
    const items = outcome.body?.items;
    if (outcome.kind === "http" && outcome.status === 200 && Array.isArray(items)
      && items.every((item) => item !== null && typeof item === "object"
        && ["place_id", "display_name", "country_code"].every((key) => typeof item[key] === "string")
        && (item.admin1_name === null || typeof item.admin1_name === "string")
        && item.place_id !== "" && item.display_name !== "")) {
      state.items = items.map(copyItem);
      state.status = items.length === 0 ? "empty" : "results";
      state.open = items.length > 0;
      state.activeIndex = -1;
      state.error = null;
      retryAt = 0;
    } else {
      const invalidInput = outcome.kind === "http" && outcome.status === 422;
      state.items = [];
      state.open = false;
      state.activeIndex = -1;
      state.status = "error";
      state.error = { kind: outcome.kind, code: outcome.body?.code ?? null, invalidInput,
        message: invalidInput ? "Проверьте название места." : "Поиск временно недоступен." };
      const seconds = /^[0-9]+$/.test(outcome.retryAfter ?? "") ? Number(outcome.retryAfter) : 0;
      retryAt = Number.isSafeInteger(seconds) ? clock.now() + seconds * 1000 : clock.now();
    }
    cooldown();
    publish();
  }
  function select(index) {
    const item = state.items[index];
    if (disposed || !item) return null;
    cancelSearch();
    state = { ...state, query: item.display_name, status: "selected", items: [],
      activeIndex: -1, open: false, selection: copyItem(item), error: null };
    if (onSelect) onSelect(copyItem(item));
    publish();
    return copyItem(item);
  }
  return Object.freeze({
    snapshot,
    setQuery(query) {
      if (disposed) return;
      cancelSearch();
      state = { ...state, query, items: [], activeIndex: -1, open: false, selection: null };
      if (!searchable()) {
        state.status = "idle";
        if (clock.now() >= retryAt) state.error = null;
      }
      else if (clock.now() < retryAt) { state.status = "error"; cooldown(); }
      else {
        state.status = "debouncing";
        state.error = null;
        state.requestId = null;
        state.retryAfter = null;
        const token = generation;
        debounceTimer = clock.set(() => runSearch(token, query), debounceMs);
      }
      publish();
    },
    select,
    handleKey(key) {
      if (disposed) return false;
      if (key === "Escape" && state.open) {
        state.open = false; state.activeIndex = -1; publish(); return true;
      }
      if (state.items.length === 0) return false;
      if (key === "ArrowDown" || key === "ArrowUp") {
        const step = key === "ArrowDown" ? 1 : -1;
        state.activeIndex = state.activeIndex === -1 ? (step === 1 ? 0 : state.items.length - 1)
          : (state.activeIndex + step + state.items.length) % state.items.length;
        state.open = true;
        publish(); return true;
      }
      if (key === "Enter" && state.open) {
        if (state.activeIndex >= 0) select(state.activeIndex);
        return true;
      }
      return false;
    },
    close() { state.open = false; state.activeIndex = -1; publish(); },
    retry() {
      if (disposed || !searchable() || clock.now() < retryAt || state.status !== "error") return false;
      cancelSearch();
      void runSearch(generation, state.query);
      return true;
    },
    dispose() {
      cancelSearch();
      if (cooldownTimer !== null) clock.clear(cooldownTimer);
      disposed = true;
    },
  });
}
