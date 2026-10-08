// REQ-UI-09, AS-UI-14/23: политика зависит от реально полученного outcome.
import { validError } from "./response.mjs";
// HTTP §8.1: эти отказы имеют известный исход без публикации новой карты.
const ordinaryFailures = {
  500: new Set(["RESOLUTION_UNAVAILABLE", "CALCULATION_FAILED"]),
  503: new Set(["BUILD_CAPACITY_EXHAUSTED", "SERVICE_SHUTTING_DOWN", "STATE_READ_FAILED",
    "RESOLUTION_UNAVAILABLE", "CALCULATION_FAILED"]),
};
export function planRecovery(outcome, intent, previousView, placeName = "") {
  let kind;
  const code = validError(outcome.body) ? outcome.body.code : null;
  if (outcome.kind === "network_error") kind = "network";
  else if (outcome.status === 503 && code === "STATE_COMMIT_FAILED") kind = "commit_failed";
  else if (outcome.status === 504 && code === "BUILD_TIMEOUT") kind = "timeout";
  else if (outcome.status === 200 || outcome.status >= 500 && outcome.status < 600
    && !ordinaryFailures[outcome.status]?.has(code)) kind = "unconfirmed_response";
  else return null;
  return { kind, status: kind === "timeout" ? "restart_required" : "waiting", intent: Object.freeze({ ...intent }),
    placeName, previousIdentity: previousView?.chart?.chart_identity ?? null,
    originalRequestId: outcome.requestId ?? null, retryAfter: outcome.retryAfter ?? null,
    checkRequestId: null, bootstrapRequestId: null, restartConfirmed: false };
}

export function intentMatchesBirth(intent, birth) {
  return Boolean(intent && birth && intent.birth_date === birth.birth_date
    && intent.place_id === birth.place?.place_id && intent.birth_time === birth.birth_time
    && (intent.birth_time === null) === birth.time_unknown);
}

export function recoveredStatus(recovery, view) {
  if (view.status === "chart_ready" && intentMatchesBirth(recovery.intent, view.birth)) return view.chart_stale ? "stale" : "matched";
  if (view.status !== "chart_ready" || view.chart.chart_identity === recovery.previousIdentity) return "old_or_empty";
  return "different";
}

export function recoveryMessage(recovery) {
  if (!recovery) return "";
  if (recovery.status === "check_failed") return "Не удалось проверить текущую карту. Введённые данные сохранены. Повторите безопасную проверку карты.";
  if (recovery.status === "matched") return "Текущая карта соответствует отправленным данным.";
  if (recovery.status === "stale") return "Сохранённая карта соответствует отправленным данным, но устарела. Свежий результат не подтверждён. Её можно явно пересчитать или повторить проверку карты.";
  if (recovery.status === "different") return "Показана актуальная карта с другими данными. Ваш черновик сохранён.";
  if (recovery.status === "old_or_empty") return recovery.kind === "network" || recovery.kind === "unconfirmed_response"
    ? "Что-то пошло не так. Новый результат пока не появился. Введённые данные сохранены. Вы можете построить карту ещё раз; предыдущий расчёт может завершиться позже"
    : "Новый результат не подтверждён. Введённые данные сохранены. Вы можете явно построить карту ещё раз.";
  if (recovery.kind === "timeout" && !recovery.restartConfirmed) return "Расчёт не завершился вовремя. Исход построения пока неизвестен. После перезапуска и восстановления работы сервера нажмите «Проверить после перезапуска».";
  if (recovery.kind === "network") return "Не удалось получить ответ о построении карты. Проверяем текущую карту";
  return "Не удалось подтвердить результат построения. Проверяем текущую карту. Введённые данные сохранены.";
}
