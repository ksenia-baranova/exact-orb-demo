// REQ-UI-01/03/08/09: текущая карта и изменяемый черновик имеют разные источники.
const sessionErrors = new Set(["SESSION_REQUIRED", "SESSION_EXPIRED", "SESSION_NOT_FOUND"]);
const fields = { "birth.date": "date", "birth.time": "time", "birth.place": "place" };
const browserClock = { now: () => performance.now(),
  set: (callback, milliseconds) => setTimeout(callback, milliseconds), clear: (handle) => clearTimeout(handle) };

export function issueMessage(issue) {
  const messages = { MISSING: "Заполните поле.", INVALID: "Некорректное значение.",
    AMBIGUOUS: "Значение неоднозначно. Уточните введённые данные.", UNSUPPORTED: "Значение не поддерживается." };
  let message = issue.field === "birth.time" && issue.code === "AMBIGUOUS"
    ? "Указанное местное время неоднозначно для выбранного места." : messages[issue.code] ?? "Проверьте значение поля.";
  if (issue.field === "birth.time" && issue.code === "AMBIGUOUS") message += " Укажите другое время либо отметьте, что точное время неизвестно.";
  else if (issue.candidates?.length) message += ` Варианты: ${issue.candidates.join(", ")}.`;
  if (issue.constraints) {
    const labels = { min: "от", max: "до", min_year: "первый допустимый год", max_year: "последний допустимый год" };
    message += ` Ограничения: ${Object.entries(issue.constraints).map(([key, value]) => `${labels[key] ?? key}: ${value}`).join(", ")}.`;
  }
  return message;
}

export function createSessionCoordinator({ apiClient, form, onChange, clock = browserClock } = {}) {
  let state = { phase: "idle", sessionReady: false, view: null, source: null, submittedIntent: null,
    fieldIssues: {}, error: null, requiresReconciliation: false, requestId: null };
  let disposed = false, controller = null, retryAt = 0, retryTimer = null;
  const busy = () => state.phase !== "idle";
  function snapshot() {
    const copy = structuredClone(state);
    if (copy.submittedIntent) Object.freeze(copy.submittedIntent);
    return { ...copy, busy: busy(), canSubmit: !disposed && !busy() && state.sessionReady
      && !state.requiresReconciliation && clock.now() >= retryAt,
      retryInSeconds: Math.max(0, Math.ceil((retryAt - clock.now()) / 1000)) };
  }
  function publish() { if (!disposed && onChange) onChange(snapshot()); }
  function phase(value) { state.phase = value; publish(); }
  function cooldown(outcome) {
    if (retryTimer !== null) clock.clear(retryTimer);
    retryTimer = null;
    const raw = outcome.retryAfter ?? "";
    const seconds = /^[0-9]+$/.test(raw) ? Number(raw) : 0;
    retryAt = clock.now() + (Number.isSafeInteger(seconds) ? seconds * 1000 : 0);
    if (retryAt > clock.now()) retryTimer = clock.set(() => { retryTimer = null; publish(); }, retryAt - clock.now());
  }
  function error(outcome) {
    const body = outcome.body;
    const userMessage = typeof body?.user_message === "string" ? body.user_message : null;
    state.fieldIssues = {};
    const generalIssues = [];
    for (const issue of Array.isArray(body?.issues) ? body.issues : []) {
      const field = Object.hasOwn(fields, issue?.field) ? fields[issue.field] : null;
      if (field && outcome.status === 422) (state.fieldIssues[field] ??= []).push(structuredClone(issue));
      else generalIssues.push(structuredClone(issue));
    }
    state.error = { message: userMessage || (outcome.kind === "network_error"
      ? "Нет связи с сервером. Введённые данные сохранены." : "Не удалось выполнить запрос. Введённые данные сохранены."),
      userMessage, code: body?.code ?? null, detailCode: body?.detail_code ?? null,
      status: outcome.status ?? null, retryable: body?.retryable === true, generalIssues,
      requestId: outcome.requestId ?? null, retryAfter: outcome.retryAfter ?? null };
    state.requestId = outcome.requestId ?? null;
    cooldown(outcome);
    return false;
  }
  const version = (body) => Number.isSafeInteger(body?.state_version) && body.state_version >= 0;
  const chart = (body) => body?.chart && typeof body.chart.chart_identity === "string" && body.chart.chart_identity !== ""
    && ["natal", "cosmogram"].includes(body.chart.kind);
  function validCurrent(body) {
    if (!version(body)) return false;
    if (body.status === "empty") return body.birth === null && body.chart === null && body.chart_stale === null;
    const birth = body.birth;
    if (!birth || typeof birth.birth_date !== "string" || !birth.place?.place_id || typeof birth.place.display_name !== "string"
      || typeof birth.time_unknown !== "boolean" || (birth.time_unknown ? birth.birth_time !== null : typeof birth.birth_time !== "string")) return false;
    return body.status === "chart_ready" ? Boolean(chart(body)) && typeof body.chart_stale === "boolean"
      : body.status === "chart_unavailable" && body.chart === null && body.chart_stale === null;
  }
  function accept(outcome, source) {
    state.view = structuredClone(outcome.body);
    state.source = source;
    state.requestId = outcome.requestId ?? null;
    state.error = null;
    state.fieldIssues = {};
    cooldown({});
    return true;
  }
  async function call(method, intent) {
    try {
      return await (method === "buildNatal" ? apiClient.buildNatal(intent, { signal: controller.signal })
        : apiClient[method]({ signal: controller.signal }));
    } catch {
      return { kind: "network_error", status: null, requestId: null, retryAfter: null };
    }
  }
  const missingSession = (outcome) => outcome.kind === "http" && outcome.status === 409 && sessionErrors.has(outcome.body?.code);
  async function read(allowRecovery) {
    phase("reading");
    const outcome = await call("current");
    if (disposed) return false;
    if (missingSession(outcome) && allowRecovery) return bootstrapAndRead(false);
    if (outcome.kind === "http" && outcome.status === 200 && validCurrent(outcome.body)) {
      state.sessionReady = true;
      return accept(outcome, "current");
    }
    state.sessionReady = false;
    return error(outcome);
  }
  async function bootstrapAndRead(allowRecovery) {
    state.sessionReady = false;
    phase("bootstrapping");
    const outcome = await call("bootstrap");
    if (disposed) return false;
    if (outcome.kind !== "http" || outcome.status !== 200 || outcome.body?.status !== "ready" || !version(outcome.body)) return error(outcome);
    return read(allowRecovery);
  }
  function begin() {
    controller = new AbortController();
    state.fieldIssues = {}; state.error = null;
  }
  function finish() { if (!disposed) { controller = null; phase("idle"); } }
  return Object.freeze({
    snapshot,
    async open() {
      if (disposed || busy() || state.requiresReconciliation || clock.now() < retryAt) return false;
      begin();
      try { return await bootstrapAndRead(true); } finally { finish(); }
    },
    async submit() {
      if (!snapshot().canSubmit) return false;
      const prepared = form.prepareSubmission();
      if (!prepared.ok) { publish(); return false; }
      begin();
      state.submittedIntent = Object.freeze({ ...prepared.intent });
      phase("building");
      try {
        const outcome = await call("buildNatal", state.submittedIntent);
        if (disposed) return false;
        if (missingSession(outcome)) return await bootstrapAndRead(false);
        if (outcome.kind === "http" && ((outcome.status === 200 && outcome.body?.status === "already_applied" && version(outcome.body))
          || (outcome.status === 409 && outcome.body?.code === "RESULT_SUPERSEDED"))) return await read(true);
        if (outcome.kind === "http" && outcome.status === 200 && outcome.body?.status === "chart_ready" && version(outcome.body) && chart(outcome.body)) {
          return accept({ ...outcome, body: { ...outcome.body, birth: null, chart_stale: false } }, "build");
        }
        state.requiresReconciliation = outcome.kind === "network_error" || outcome.status === 200
          || ["STATE_COMMIT_FAILED", "BUILD_TIMEOUT"].includes(outcome.body?.code);
        error(outcome);
        if (state.requiresReconciliation) state.error.message = "Не удалось подтвердить результат построения. Текущая карта требует сверки. Введённые данные сохранены.";
        return false;
      } finally { finish(); }
    },
    clearFieldError(field) { delete state.fieldIssues[field]; publish(); },
    dispose() {
      disposed = true;
      controller?.abort();
      if (retryTimer !== null) clock.clear(retryTimer);
    },
  });
}
