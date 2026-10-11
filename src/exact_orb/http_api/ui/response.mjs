// DEV-UI-07, REQ-UI-03/08/09: проверка HTTP DTO перед accept/render, без расчёта.
// docs/requirements/http_api.md §§7.1–7.3; неизвестные поля не используются.
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const text = (value) => typeof value === "string" && value.length > 0;
const integer = (value, min, max = Number.MAX_SAFE_INTEGER) =>
  Number.isSafeInteger(value) && value >= min && value <= max;
const signs = new Set(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]);
const aspectTypes = new Set(["conjunction", "semisextile", "sextile", "square", "trine", "quincunx", "opposition"]);
const categories = new Set(["exact", "working", "background"]);
const position = (item) => object(item) && signs.has(item.sign)
  && integer(item.degree, 0, 29) && integer(item.minute, 0, 59);
const angle = (item) => position(item) && Number.isFinite(item.longitude);
const house = (value) => value === null || integer(value, 1, 12);
export const validVersion = (body) => object(body) && integer(body.state_version, 0);

export function validChart(chart) {
  if (!object(chart) || !text(chart.chart_identity) || !["natal", "cosmogram"].includes(chart.kind)
    || chart.zodiac !== "tropical" || !Array.isArray(chart.points) || !Array.isArray(chart.aspects)) return false;
  if (!chart.points.every((point) => angle(point) && text(point.id) && house(point.house)
    && typeof point.retrograde === "boolean")) return false;
  if (!chart.aspects.every((aspect) => object(aspect) && text(aspect.from) && text(aspect.to)
    && aspectTypes.has(aspect.type) && categories.has(aspect.category)
    && Number.isFinite(aspect.orb) && aspect.orb >= 0)) return false;
  if (chart.kind === "cosmogram") return chart.house_system === null && chart.houses === null
    && chart.angles === null && chart.points.every((point) => point.house === null);
  return text(chart.house_system) && Array.isArray(chart.houses)
    && chart.houses.every((item) => position(item) && integer(item.number, 1, 12) && Number.isFinite(item.cusp_longitude))
    && object(chart.angles) && ["asc", "mc", "vertex", "dsc", "ic"].every((id) => angle(chart.angles[id]));
}

function validBirth(birth) {
  if (!object(birth) || typeof birth.birth_date !== "string"
    || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(birth.birth_date) || !object(birth.place)
    || !text(birth.place.place_id) || !text(birth.place.display_name)
    || !text(birth.tz_id) || typeof birth.time_unknown !== "boolean"
    || !Array.isArray(birth.warnings) || !birth.warnings.every((warning) => object(warning)
      && ["place", "time"].includes(warning.source) && text(warning.code))) return false;
  return birth.time_unknown ? birth.birth_time === null && birth.utc_offset_seconds === null
    : typeof birth.birth_time === "string" && /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(birth.birth_time)
      && Number.isSafeInteger(birth.utc_offset_seconds);
}

export function validCurrent(body) {
  if (!validVersion(body)) return false;
  if (body.status === "empty") return body.birth === null && body.chart === null && body.chart_stale === null;
  if (!validBirth(body.birth)) return false;
  if (body.status === "chart_unavailable") return body.chart === null && body.chart_stale === null;
  return body.status === "chart_ready" && typeof body.chart_stale === "boolean" && validChart(body.chart)
    && body.birth.time_unknown === (body.chart.kind === "cosmogram");
}
export const validBootstrap = (body) => validVersion(body) && body.status === "ready";
export const validBuild = (body) => validVersion(body) && body.status === "chart_ready" && validChart(body.chart);

function validIssue(issue) {
  return object(issue) && text(issue.field) && ["MISSING", "AMBIGUOUS", "INVALID", "UNSUPPORTED"].includes(issue.code)
    && (issue.candidates == null || Array.isArray(issue.candidates)
      && issue.candidates.every((value) => typeof value === "string" || Number.isSafeInteger(value)))
    && (issue.constraints == null || object(issue.constraints)
      && Object.values(issue.constraints).every((value) => typeof value === "string" || Number.isFinite(value)));
}
export function validError(body) {
  return object(body) && text(body.code) && (body.detail_code === null || typeof body.detail_code === "string")
    && typeof body.user_message === "string" && typeof body.retryable === "boolean"
    && (body.issues == null || Array.isArray(body.issues) && body.issues.every(validIssue));
}
