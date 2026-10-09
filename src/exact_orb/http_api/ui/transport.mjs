/**
 * Транспортный клиент существующего HTTP API на том же origin.
 * HTTP-ответ сохраняет статус, JSON (либо исходный текст ответа прокси) и заголовки.
 * Сетевой исход означает отсутствие полного ответа, в том числе обрыв чтения тела.
 * Cookie управляет браузер; клиент не повторяет запросы и не координирует восстановление.
 */
export function createApiClient({ fetchFn = (...args) => globalThis.fetch(...args) } = {}) {
  function metadata(response) {
    return {
      status: response?.status ?? null,
      requestId: response?.headers.get("X-Request-ID") ?? null,
      retryAfter: response?.headers.get("Retry-After") ?? null,
    };
  }

  async function request(path, method, body, signal) {
    const options = { method, credentials: "same-origin", cache: "no-store", signal };
    if (body !== undefined) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }

    let response;
    let text;
    try {
      response = await fetchFn(path, options);
      text = await response.text();
    } catch (error) {
      return {
        kind: "network_error",
        aborted: error?.name === "AbortError",
        ...metadata(response),
      };
    }

    let parsed = text === "" ? null : text;
    if (text !== "") {
      try {
        parsed = JSON.parse(text);
      } catch (error) {
        if (!(error instanceof SyntaxError)) throw error;
      }
    }
    return { kind: "http", body: parsed, ...metadata(response) };
  }

  return Object.freeze({
    bootstrap({ signal } = {}) {
      return request("/session/bootstrap", "POST", {}, signal);
    },
    current({ signal } = {}) {
      return request("/charts/current", "GET", undefined, signal);
    },
    searchPlaces(query, { limit, signal } = {}) {
      const parameters = new URLSearchParams({ query });
      if (limit !== undefined) parameters.set("limit", String(limit));
      return request(`/places?${parameters}`, "GET", undefined, signal);
    },
    buildNatal({ birth_date, birth_time, place_id }, { signal } = {}) {
      return request("/charts/natal", "POST", { birth_date, birth_time, place_id }, signal);
    },
  });
}
