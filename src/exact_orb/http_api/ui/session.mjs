// REQ-UI-01/03/08/09: текущая карта и изменяемый черновик имеют разные источники.
import { planRecovery, recoveredStatus, recoveryMessage } from "./recovery.mjs";
import { validVersion, validCurrent, validBootstrap, validBuild, validError } from "./response.mjs";
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

export function createSessionCoordinator({ apiClient, form, onChange, onRenderError, clock = browserClock } = {}) {
  let state = { phase: "idle", sessionReady: false, view: null, source: null, submittedIntent: null,
    fieldIssues: {}, error: null, requiresReconciliation: false, requestId: null, recovery: null };
  let disposed = false, controller = null, retryAt = 0, retryTimer = null, pendingForeground = false;
  let submittedPlaceName = "";
  const busy = () => state.phase !== "idle";
  function snapshot() {
    const copy = structuredClone(state);
    if (copy.submittedIntent) Object.freeze(copy.submittedIntent);
    if (copy.recovery) {
      Object.freeze(copy.recovery.intent);
      copy.recovery.message = recoveryMessage(copy.recovery);
    }
    return { ...copy, busy: busy(), canSubmit: !disposed && !busy() && state.sessionReady
      && !state.requiresReconciliation && clock.now() >= retryAt,
      canRecheck: !disposed && !busy() && clock.now() >= retryAt,
      retryInSeconds: Math.max(0, Math.ceil((retryAt - clock.now()) / 1000)) };
  }
  function publish() {
    if (disposed || !onChange) return true;
    try { onChange(snapshot()); return true; }
    catch {
      // Ошибка renderer имеет видимый исход; восстановление только безопасным чтением.
      state.error = { message: "Не удалось показать ответ сервера. Введённые данные сохранены. Повторите проверку карты.",
        userMessage: null, code: null, detailCode: null, status: null, retryable: false,
        generalIssues: [], requestId: state.requestId, retryAfter: null };
      state.requiresReconciliation = true;
      if (state.recovery) state.recovery.status = "check_failed";
      if (onRenderError) onRenderError(snapshot());
      return false;
    }
  }
  function phase(value) { state.phase = value; return publish(); }
  function cooldown(outcome) {
    if (retryTimer !== null) clock.clear(retryTimer);
    retryTimer = null;
    const raw = outcome.retryAfter ?? "";
    const seconds = /^[0-9]+$/.test(raw) ? Number(raw) : 0;
    retryAt = clock.now() + (Number.isSafeInteger(seconds) ? seconds * 1000 : 0);
    if (retryAt > clock.now()) retryTimer = clock.set(() => {
      retryTimer = null; publish();
      // Только один безопасный check после исходного отказа; failed check сам не повторяется.
      if (state.recovery?.status === "waiting" && !busy()) { pendingForeground = false; return recheck(); }
      if (pendingForeground && !busy()) { pendingForeground = false; return foreground(); }
    }, retryAt - clock.now());
  }
  function error(outcome, checking = false) {
    const body = validError(outcome.body) ? outcome.body : null;
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
    if (checking && state.recovery) {
      state.recovery.status = "check_failed";
      state.requiresReconciliation = true;
    }
    cooldown(outcome);
    return false;
  }
  function accept(outcome, source) {
    state.view = structuredClone(outcome.body);
    state.source = source;
    state.requestId = outcome.requestId ?? null;
    state.error = null;
    state.fieldIssues = {};
    state.requiresReconciliation = false;
    if (state.recovery && source === "current") state.recovery.status = recoveredStatus(state.recovery, state.view);
    cooldown({});
    return true;
  }
  async function call(method, intent) {
    let outcome;
    try {
      outcome = await (method === "buildNatal" ? apiClient.buildNatal(intent, { signal: controller.signal })
        : apiClient[method]({ signal: controller.signal }));
    } catch {
      outcome = { kind: "network_error", status: null, requestId: null, retryAfter: null };
    }
    if (!disposed && state.recovery) {
      if (method === "bootstrap") state.recovery.bootstrapRequestId = outcome.requestId ?? null;
      if (method === "current") state.recovery.checkRequestId = outcome.requestId ?? null;
    }
    return outcome;
  }
  const missingSession = (outcome) => outcome.kind === "http" && outcome.status === 409 && sessionErrors.has(outcome.body?.code);
  async function read(allowRecovery) {
    if (!phase("reading")) return false;
    const outcome = await call("current");
    if (disposed) return false;
    if (missingSession(outcome) && allowRecovery) return bootstrapAndRead(false);
    if (outcome.kind === "http" && outcome.status === 200 && validCurrent(outcome.body)) {
      state.sessionReady = true;
      return accept(outcome, "current");
    }
    state.sessionReady = false;
    return error(outcome, true);
  }
  async function bootstrapAndRead(allowRecovery) {
    state.sessionReady = false;
    if (!phase("bootstrapping")) return false;
    const outcome = await call("bootstrap");
    if (disposed) return false;
    if (outcome.kind !== "http" || outcome.status !== 200 || !validBootstrap(outcome.body)) return error(outcome, true);
    return read(allowRecovery);
  }
  function begin() {
    controller = new AbortController();
    state.fieldIssues = {}; state.error = null;
  }
  async function finish() {
    if (disposed) return false;
    controller = null;
    const rendered = phase("idle");
    if (!rendered) pendingForeground = false;
    if (rendered && pendingForeground && clock.now() >= retryAt) {
      pendingForeground = false;
      await foreground();
    }
    return rendered;
  }
  const restartRequired = () => state.recovery?.kind === "timeout" && !state.recovery.restartConfirmed;
  async function checkRecovery() {
    state.recovery.status = "checking";
    return state.recovery.kind === "commit_failed" ? read(true) : bootstrapAndRead(true);
  }
  async function readSession(asForeground = false) {
    if (disposed || busy() || clock.now() < retryAt || restartRequired()) return false;
    begin();
    if (state.recovery) state.recovery.status = "checking";
    let accepted, rendered;
    try {
      accepted = state.recovery && !asForeground ? await checkRecovery() : await bootstrapAndRead(true);
    } finally { rendered = await finish(); }
    return accepted && rendered;
  }
  async function recheck({ restartConfirmed = false } = {}) {
    if (disposed || busy() || clock.now() < retryAt) return false;
    if (restartRequired()) {
      if (!restartConfirmed) return false;
      state.recovery.restartConfirmed = true;
    }
    return readSession();
  }
  async function foreground() {
    if (disposed || restartRequired()) return false;
    if (busy() || clock.now() < retryAt) { pendingForeground = true; return false; }
    return readSession(true);
  }
  return Object.freeze({
    snapshot,
    open: () => readSession(), recheck, foreground,
    async submit() {
      if (!snapshot().canSubmit) return false;
      const prepared = form.prepareSubmission();
      if (!prepared.ok) { publish(); return false; }
      begin();
      state.recovery = null;
      state.submittedIntent = Object.freeze({ ...prepared.intent });
      submittedPlaceName = form.snapshot().place.display_name;
      let accepted = false, rendered;
      try {
        if (phase("building")) {
          const outcome = await call("buildNatal", state.submittedIntent);
          if (disposed) return false;
          if (missingSession(outcome)) accepted = await bootstrapAndRead(false);
          else if (outcome.kind === "http" && ((outcome.status === 200 && outcome.body?.status === "already_applied" && validVersion(outcome.body))
            || (outcome.status === 409 && outcome.body?.code === "RESULT_SUPERSEDED"))) accepted = await read(true);
          else if (outcome.kind === "http" && outcome.status === 200 && validBuild(outcome.body)) {
            accepted = accept({ ...outcome, body: { ...outcome.body, birth: null, chart_stale: false } }, "build");
          } else {
            state.recovery = planRecovery(outcome, state.submittedIntent, state.view, submittedPlaceName);
            state.requiresReconciliation = state.recovery !== null;
            error(outcome);
            if (state.recovery && !restartRequired() && clock.now() >= retryAt) await checkRecovery();
          }
        }
      } finally { rendered = await finish(); }
      return accepted && rendered;
    },
    clearFieldError(field) { delete state.fieldIssues[field]; publish(); },
    dispose() {
      disposed = true;
      controller?.abort();
      if (retryTimer !== null) clock.clear(retryTimer);
      pendingForeground = false;
    },
  });
}
