# exact-orb — требования к HTTP API и Session Middleware

- **Статус:** требования Functional Analyst приняты в `change/*` через PR #37;
  решения DP-HTTP-01…06, ограничения M1 и уточнение FIND-HTTP-021
  подтверждены владельцем change 2026-09-30. Developer подготовил draft
  implementation plan; код, Gate A и проверка lifecycle ещё не выполнены.
- **Change:** `change/http-api-and-session-middleware`, roadmap M1-6.
- **Входной commit анализа:** `27ae072e5e99cea72f7575cd35ef45ca3eeb829e`.
- **Рабочая ветка:** `analysis/http-api-and-session-middleware`.
- **Дата:** 2026-09-30.

Документ определяет наблюдаемый HTTP-контракт для анонимной сессии, чтения
текущей карты, поиска места и построения натальной карты. Он не выбирает
внутреннюю структуру FastAPI-модулей.

## 1. Основания и приоритеты

Источники требований:

- [change plan](../project_management/change_plans/http-api-and-session-middleware.md)
  и [roadmap](../project_management/roadmap.md), M1-6;
- [ADR-0006](decisions/0006-application-orchestrator.md),
  [ADR-0009](decisions/0009-context-yes-profiles-later.md),
  [ADR-0012](decisions/0012-bootstrap-request-response-streaming.md),
  [ADR-0013](decisions/0013-token-abuse-protection.md),
  [ADR-0032](decisions/0032-unknown-birth-time-aspect-semantics.md),
  [ADR-0036](decisions/0036-application-orchestrator-coordination-info-events.md),
  [ADR-0037](decisions/0037-context-boundary-and-handler-coordination-logs.md),
  [ADR-0039](decisions/0039-https-in-all-environments.md),
  [ADR-0040](decisions/0040-session-bootstrap-and-current-chart.md) и
  [ADR-0041](decisions/0041-stored-chart-in-session.md);
- [требования к сессии](component_responsibilities/exact-orb_session_requirements.md),
  [stored chart](session/stored-chart-session-behavior.md) и
  [каталогу мест](component_responsibilities/exact-orb_place_catalog.md);
- фактические контракты `ApplicationRuntime`, `ContextService`,
  `ApplicationOrchestrator`, `ApplicationResult`, `PlaceSearch` и
  `application/session_view` на входном commit.

## 2. Область и endpoint

| Метод и URL                    | Назначение                                              | Успех                       | Координация                                        |
| ------------------------------ | ------------------------------------------------------- | --------------------------- | -------------------------------------------------- |
| `POST /session/bootstrap`      | создать либо восстановить анонимную сессию; без карты   | `200 SessionBootstrapDTO`   | transport → `ContextService.create/load`           |
| `GET /charts/current`          | прочитать текущую сохранённую карту                     | `200 SessionViewDTO`        | transport → `ContextService.load` → `session_view` |
| `GET /places?query=…&limit=10` | подсказки населённых пунктов                            | `200 PlaceSuggestionsDTO`   | transport → `PlaceSearch.search`                   |
| `POST /charts/natal`           | первое построение либо явное перестроение текущей карты | `200 BuildChartResponseDTO` | transport → admission → `ApplicationOrchestrator`  |
| `GET /health/live`             | внутренний liveness процесса                            | `200`                       | transport only                                     |
| `GET /health/ready`            | внутренняя готовность принимать бизнес-запросы          | `200` или `503`             | transport lifecycle state                          |

В M1-6 также входят cookie middleware, строгая HTTP-валидация, mapping typed
outcomes, admission, deadline, reaper, startup/shutdown и transport
observability.

В M1-6 не входят UI, SSE, LLM, интерпретации, durable jobs и polling build.
Transport не выдаёт клиенту `run_id`, не предоставляет endpoint состояния
build и не позволяет возобновить получение ответа после разрыва соединения:
`RunContext.run_id` остаётся только внутренним correlation ID для журналов.
Аккаунты и публичное развёртывание также не входят. Endpoint reset и удаления
сессии тоже не входят: `DeleteMyDataCommand`, aggregate `reset/delete` и
гашение cookie остаются действующим component contract ADR-0009, но их
публичные URL и authorization/confirmation flow определяются отдельным change.

Архитектурные границы:

- bootstrap и current chart вызывают `ContextService` напрямую;
- только current chart вызывает чистый `session_view`;
- place search не читает сессию;
- build создаёт `RunContext` и вызывает `ApplicationOrchestrator.execute`
  ровно один раз;
- transport не повторяет resolver, calculation, CAS или persistence;
- `session_id` существует только в `__Host-` cookie и не попадает в URL/JSON;
- build принимает только `birth_date`, `birth_time`, `place_id`.

## 3. Decision points и значения по умолчанию

| ID         | Предложение Functional Analyst                                                                                                        | Статус                                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| DP-HTTP-01 | четыре business endpoint и два health endpoint из §2; DTO и mapping ниже                                                              | согласовано Lead 2026-09-30; точные схемы фиксируются при реализации |
| DP-HTTP-02 | session create 300/час на IP; build 20/час и 100/24ч на session, 300/час и 1500/24ч на IP; place search 120/мин на IP; 5 active build | согласовано всеми ролями; принято Lead в review PR #37                                                             |
| DP-HTTP-03 | доверять только `X-Forwarded-For`/`X-Forwarded-Proto` от peer из CIDR allowlist; алгоритм §10                                         | Developer review выполнен; согласовано Lead 2026-09-30; исходный ASGI peer обязателен |
| DP-HTTP-04 | body receive 5 с, build response deadline 30 с, shutdown grace 30 с; task ownership §9 и §11                                          | решение Lead: M1-6 — вариант C, target state — вариант A; Developer подтверждает реализацией и deterministic tests |
| DP-HTTP-05 | четыре HTTP sequence и синхронизация session 001–003/006                                                                              | согласовано Lead 2026-09-30; реализация и сверка журналов впереди |
| DP-HTTP-06 | расширить чистую `session_view` только проекцией birth из готового snapshot | scope согласован Lead; Developer подтвердил реализуемость; код и тесты впереди |

Build IP-limit пересчитан для общего NAT/CGNAT. Демо на 10 человек по пять
построений даёт 50 запросов; прежний предел 60/час оставлял 10 запросов на
ошибки и повторные действия всей группе. Предел 300/час даёт шестикратный
запас этому сценарию, а злоупотребление по-прежнему ограничивают session quota,
creation quota и пять active build. Это конфигурация контролируемого M1-стенда,
не SLA; изменение чисел требует evidence и approval, но не меняет error codes.

## 4. Общие правила HTTP

### 4.1. Порядок обработки и приоритет ошибок

Для совпавшего route проверки выполняются строго в следующем порядке:

1. присвоить server `request_id`, записать `http_request_started`;
2. проверить lifecycle gate: во время shutdown business endpoint получает
   `503 SERVICE_SHUTTING_DOWN`; health endpoint обрабатывается отдельно;
3. определить client IP и проверить trusted forwarding headers — `400`;
4. проверить `Origin` — `403 ORIGIN_NOT_ALLOWED`;
5. для POST проверить `Content-Encoding`, media type и charset — `415`;
6. ограничить время получения и wire-size body — `408` либо `413`;
7. разобрать JSON/query и проверить публичную схему — `422`;
8. проверить cardinality и синтаксис cookie, затем требование session;
9. выполнить соответствующий admission check;
10. вызвать application/component boundary.

Route resolution происходит до этой цепочки: неизвестный path даёт `404`,
известный path с недопустимым методом — `405` и `Allow`. Поэтому при работающем
сервисе невалидный JSON без cookie получает schema `422`, а не `409`; неверный
Origin имеет приоритет над content type и body; `415` имеет приоритет над
`413`, а `413` — над JSON parse.

Bootstrap не требует cookie: отсутствие, одно непригодное либо дублирующееся
значение переводит его в ветку создания. Для `GET /charts/current` и build те
же случаи дают `409 SESSION_REQUIRED` после успешной transport validation.

### 4.2. Формат и строгая грамматика

- JSON и ответы используют UTF-8. POST принимает только
  `application/json` с отсутствующим charset либо `charset=utf-8`; любой
  `Content-Encoding` запрещён.
- Неизвестные JSON-поля и query parameters отклоняются. Числа, boolean и
  массивы не преобразуются в строки.
- `birth_date` — ровно `YYYY-MM-DD`; несуществующая календарная дата вроде
  `1990-02-30` является schema `422 INVALID_REQUEST` с field `birth.date`.
- Будущая дата и дата вне настроенного диапазона эфемерид синтаксически
  валидны, доходят до `BirthDataResolver` и возвращаются как
  `422 INPUT_REQUIRED`, issue `birth.date/UNSUPPORTED` с `min/max`.
- Локальная дата, которой не было в выбранном timezone, возвращается resolver
  как `INPUT_REQUIRED`, issue `birth.date/INVALID`.
- `birth_time` — `HH:MM` либо `null`; секунды, offset и timezone запрещены.
- Query `limit` отсутствует либо соответствует ASCII regex
  `(?:[1-9]|1[0-9]|20)`. `010`, `+5`, `5.0`, whitespace и повтор параметра
  дают `422 INVALID_REQUEST`, `detail_code=LIMIT_INVALID`.

### 4.3. Размеры, медленный клиент и корреляция

- Максимальный POST body — 16 KiB wire bytes до JSON parse.
- Всё тело должно быть получено не позднее 5 секунд после первого ASGI body
  event; timeout даёт `408 REQUEST_TIMEOUT`. Серверные header/keep-alive
  timeouts дополнительно задаются deployment, но не заменяют этот тестируемый
  application limit.
- Raw `query` места — не более 512 Unicode code points после URL decode и до
  нормализации; `place_id` — 1..128 code points.
- Server генерирует UUID `request_id`; клиентский `X-Request-ID` не
  переиспользуется. Ответ всегда содержит `X-Request-ID`.
- Для build `run_id == request_id`. Идентификатор служит корреляции, а не
  idempotency key или resumable handle.

### 4.4. Origin, кэш и обязательные заголовки

Базовый режим same-origin. Если `Origin` присутствует, transport проверяет
его у каждого business endpoint, включая `GET /charts/current` и поиск мест;
чужой origin получает 403 до body, cookie, admission и component call.
Отсутствующий `Origin` допустим для non-browser клиента. Внутренние health
endpoint не проходят Origin-проверку. Credentialed CORS включается только для
точного allowlist; wildcard запрещён.

Каждый ответ приложения, включая `4xx/5xx`, содержит
`Cache-Control: no-store` и `X-Request-ID`. Это явно проверяется для `413`,
`429` и `500`. `Retry-After` — целое число секунд со следующими точными
правилами:

| Условие                                                                                           |                                                                           `Retry-After` | Разрешённое следующее действие                                                               |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------: | -------------------------------------------------------------------------------------------- |
| rolling-window `429`                                                                              | ceil до первого момента, когда все исчерпанные bucket снова допускают запрос, минимум 1 | повторить исходный запрос после задержки                                                     |
| `408 BODY_RECEIVE_TIMEOUT`                                                                        |                                                                                       1 | повторить исходный запрос: admission ещё не было                                             |
| `503 BUILD_CAPACITY_EXHAUSTED`                                                                    |                                                                                       1 | повторить исходный POST после задержки                                                       |
| `503 SERVICE_SHUTTING_DOWN`                                                                       |                                                                                      30 | повторить исходный запрос после перезапуска                                                  |
| retryable storage/catalog/dependency `503`, включая `SESSION_CREATE_FAILED` и `STATE_READ_FAILED` |                                                                                       5 | повторить безопасную операцию; для POST — только если code-specific policy не требует сверки |
| `503 STATE_COMMIT_FAILED`                                                                         |                                                                                       1 | только `GET /charts/current`, исходный POST автоматически не повторять                       |
| `504 BUILD_TIMEOUT`                                                                               |                                                                                       5 | только `GET /charts/current`; это задержка до сверки, не до повтора POST                     |

Одна секунда для capacity не создаёт серверную очередь и даёт ближайшему
освободившемуся permit принять запрос; пять секунд предотвращают hot loop при
локальном dependency/storage отказе и дают retained task время до первой
сверки; 30 секунд совпадают с shutdown grace. Для 504 header планирует только
current-check. Это M1 defaults: изменение значений требует approval DP-HTTP-02/04.

## 5. HTTPS и session cookie

По ADR-0039 браузер обращается к API по HTTPS во всех окружениях. Локальная
разработка использует reverse proxy и сертификат локального CA; приложение не
поддерживает браузерный режим `http://localhost`. ASGI-тесты используют
`base_url="https://testserver"` без настоящего TLS.

Cookie:

```text
__Host-exact_orb_session=<43 URL-safe base64 chars>;
HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=604800
```

`Domain` отсутствует. Значение создаётся из 32 случайных байтов без padding и
при чтении проверяется regex `[A-Za-z0-9_-]{43}`. Допускается ровно одно
значение cookie с этим именем. Cookie остаётся opaque lookup key, не логируется
и не принимается из body/query/path.

Lifecycle cookie:

1. create выдаёт новую cookie; live load обновляет Max-Age;
2. `StateReadFailed` сохраняет cookie без renew/clear;
3. `SessionAbsent` в current/build гасит cookie и даёт 409; только bootstrap
   может после этого создать новый ID;
4. invalid/duplicate cookie в current/build гасится и даёт
   `SESSION_REQUIRED`; bootstrap может заменить её после creation admission;
5. если bootstrap после `SessionAbsent`, invalid/duplicate либо missing дошёл
   до creation admission, но admission/create отказали, новая cookie не
   выдаётся; прежнее absent/invalid/duplicate значение гасится даже при отказе,
   missing остаётся без cookie;
6. потеря cookie в браузере не удаляет server record: её удаляет reaper либо
   будущий явный delete endpoint.

Sliding TTL store — 7 дней, hard TTL — 30 дней. Cookie Max-Age не доказывает,
что запись ещё существует.

## 6. Business endpoint

### 6.1. `POST /session/bootstrap`

Запрос — ровно `{}`. Успех:

```json
{"status":"ready","state_version":0}
```

| Условие                                  | Действие и результат                                                                                           |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| cookie отсутствует/invalid/duplicate     | session-create limit по client IP → fresh ID → insert-only `ContextService.create`; `200 ready` и новая cookie |
| live cookie                              | `ContextService.load`; вернуть только `state_version`, не вызывать `session_view`; `200 ready` и renew cookie  |
| `SessionAbsent`                          | clear old cookie → creation admission → fresh ID/create; `200 ready` и один новый `Set-Cookie`                 |
| `StateReadFailed`                        | `503 STATE_READ_FAILED`; cookie unchanged; create запрещён                                                     |
| три последовательных `SessionIdConflict` | `503 SESSION_CREATE_FAILED`, detail `SESSION_ID_COLLISION_RETRY_EXHAUSTED`; чужие записи не читать             |
| `StateCommitFailed` create               | `503 SESSION_CREATE_FAILED` с safe storage detail; новая cookie не выдаётся                                    |
| creation limit                           | `429 SESSION_CREATE_RATE_LIMITED`; `Retry-After`; create/ID generation не выполняются                          |

Creation quota расходуется один раз на HTTP-запрос, а не на каждую внутреннюю
collision attempt. Успешный restore live cookie quota не расходует.
`http_cookie_replaced` пишется для `missing`, `invalid`, `duplicate`,
`expired`, `not_found` только после успешного create, непосредственно перед
выдачей новой cookie; при admission/create failure этого event нет. Значение
cookie в event отсутствует.

Bootstrap не возвращает birth/chart/status карты, не делает CAS и не вызывает
Orchestrator, resolver, cache, engine или `session_view`.

### 6.2. `GET /charts/current`

Endpoint требует ровно одну синтаксически пригодную cookie.

| Исход                            | HTTP | Cookie                      | Тело                                             |
| -------------------------------- | ---: | --------------------------- | ------------------------------------------------ |
| live empty snapshot              |  200 | renew                       | `SessionViewDTO empty`                           |
| valid stored chart               |  200 | renew                       | `chart_ready`, `chart_stale` true/false          |
| safe decode/projector refusal    |  200 | renew                       | `chart_unavailable` с birth, без internal reason |
| `SessionAbsent`                  |  409 | clear                       | `SESSION_EXPIRED` или `SESSION_NOT_FOUND`        |
| `StateReadFailed`                |  503 | unchanged                   | typed storage error                              |
| invalid/missing/duplicate cookie |  409 | clear if present            | `SESSION_REQUIRED`                               |
| unexpected projector failure     |  500 | renew after successful load | `INTERNAL_FAILURE`                               |

`ContextService.load` выполняет read-and-renew. Затем чистый `session_view`
декодирует `StoredChart` с сохранённой `CalculationVersion`; изменение текущей
версии только ставит `chart_stale=true`. Resolver/cache/engine не вызываются,
state не меняется.

Структурная рассинхронизация агрегата (state с chart ref без строки chart либо
наоборот) является `StateReadFailed`, а не `chart_unavailable`. Safe
`chart_unavailable` пишет отдельное ERROR-событие без payload/данных рождения.

### 6.3. `GET /places`

`query` обязателен и передаётся один раз. `limit` по умолчанию 10 и следует
грамматике §4.2. Cookie не читается и не обновляется.

| Исход                               | HTTP | Тело                                                   |
| ----------------------------------- | ---: | ------------------------------------------------------ |
| suggestions, включая пустой список  |  200 | `{ "items": [...] }`                                   |
| `InvalidPlaceQuery(code)`           |  422 | compact error `INVALID_PLACE_QUERY` + component detail |
| raw query >512                      |  422 | `INVALID_REQUEST`, `QUERY_TOO_LONG`                    |
| invalid/missing limit/query grammar |  422 | `INVALID_REQUEST`, `LIMIT_INVALID`/`QUERY_REQUIRED`    |
| catalog unavailable                 |  503 | `PLACE_CATALOG_UNAVAILABLE`                            |
| IP limit                            |  429 | `PLACE_SEARCH_RATE_LIMITED` + `Retry-After`            |

Публичный item содержит только `place_id`, `display_name`, `admin1_name`,
`country_code`; координаты и `tz_id` не публикуются. Пустой результат — 200.

### 6.4. `POST /charts/natal`

Запрос:

```json
{"birth_date":"1990-09-02","birth_time":"14:30","place_id":"524901"}
```

`birth_time:null` строит cosmogram. Endpoint используется и для первого build,
и для явного rebuild поверх существующей карты. Клиентский `state_version` не
принимается: Orchestrator загружает актуальную server version внутри каждого
execute. Поэтому поздний build вкладки A может осознанно заменить карту вкладки
B; concurrent CAS остаётся защищённым.

После transport validation и cookie transport атомарно резервирует rate и
capacity, создаёт:

```text
RunContext(
  run_id=request_id,
  started_at=<UTC now>,
  deadline=started_at + 30 seconds
)
```

и ровно один раз вызывает `ApplicationOrchestrator.execute`. `run.deadline`
обязан ограничивать внутренний retry commit, но сам по себе не является
таймаутом execute. Transport также применяет 30-секундный monotonic response
deadline ко всей операции.

`ApplicationCommitted` возвращает 200:

```json
{
  "status":"chart_ready",
  "state_version":3,
  "chart":{"chart_identity":"eo:calc:v2:...","kind":"natal"}
}
```

`ApplicationAlreadyApplied` не публикует artifact текущего запроса, потому что
в mixed-`CalculationVersion` rollout он может отличаться от фактически
сохранённого winner:

```json
{"status":"already_applied","state_version":3}
```

Клиент после `already_applied` вызывает `GET /charts/current`. M1 допускает
только один web process и одну `CalculationVersion`; rolling mixed-version
deployment запрещён до отдельного решения. Это ограничение не используется как
основание отдавать потенциально несохранённый artifact.

Если response deadline истёк, transport отвечает `504 BUILD_TIMEOUT` и не
запускает второй execute. До restart принятая application task остаётся в task
registry, а capacity permit не объявляется освобождённым. Если начался
защищённый commit, его inner task не отсоединяется от ownership. По выбранному
для M1-6 варианту C процесс закрывает admission, становится unhealthy и
перезапускается внешним supervisor; target state A переносит расчёт в отдельный
worker process. Bounded timeouts leaf-операций применяются там, где они
поддерживаются, но `wait_for` вокруг неотменяемого native вызова сам по себе не
считается lifecycle ownership.

## 7. Публичные DTO и projector

### 7.1. Основные формы

```ts
type SessionBootstrapDTO = { status: "ready"; state_version: number };

type SessionViewDTO =
  | { status: "empty"; state_version: number; birth: null; chart: null;
      chart_stale: null }
  | { status: "chart_ready"; state_version: number; birth: BirthViewDTO;
      chart: ChartDTO; chart_stale: boolean }
  | { status: "chart_unavailable"; state_version: number;
      birth: BirthViewDTO; chart: null; chart_stale: null };

type BuildChartResponseDTO =
  | { status: "chart_ready"; state_version: number; chart: ChartDTO }
  | { status: "already_applied"; state_version: number };
```

```ts
type BirthViewDTO = {
  birth_date: string; // YYYY-MM-DD из birth_input
  birth_time: string | null; // HH:MM из birth_input; null ⇔ time_unknown
  place: { place_id: string; display_name: string };
  tz_id: string;
  utc_offset_seconds: number | null; // null ⇔ time_unknown
  time_unknown: boolean;
  warnings: { source: "place" | "time"; code: string }[];
};
```

`place_id` берётся из `birth_input`, `display_name` — из
`birth_resolved.canonical_place`. `tz_id` публикуется всегда. При
`time_unknown=true` поля `birth_time` и `utc_offset_seconds` равны JSON `null`:
смещение и UTC-момент технического noon anchor не публикуются ни в одном поле.
При известном времени `birth_time` имеет формат `HH:MM`, а
`utc_offset_seconds` содержит сохранённое целое смещение. Это одинаково для
`chart_ready` и `chart_unavailable`.

Предупреждения сохраняют порядок resolver и публикуются только по allowlist:
`pre_1970_offset_unverified` с `source="time"` публикуется;
`noon_anchor_adjusted`, `noon_anchor_ambiguous` и неизвестные коды не
публикуются. Внутренние тексты предупреждений не входят в DTO. Несовпадение
`time_unknown` с условием `birth_input.birth_time is None` либо ненулевые
секунды/микросекунды сохранённого времени — unexpected projector failure:
`500 INTERNAL_FAILURE` с renew cookie по §6.2.

`session_view` на входном commit не публикует весь этот набор. Решением Lead
по DP-HTTP-06/FIND-HTTP-019 в M1-6 включена только чистая application projection
из `state.birth_input` и `state.birth_resolved` одного уже загруженного
snapshot; новых I/O, application ports и
transport типов в application layer нет.
Build success не требует birth projection: committed artifact и version уже
есть в `ApplicationResult`, а полная восстановленная форма читается через
`GET /charts/current`. Это закрывает прежний разрыв без второго скрытого load
внутри POST.

### 7.2. `ChartDTO`

Projector использует явный whitelist; `model_dump()` внутреннего artifact
запрещён.

| Поле             | Контракт                                                                     |
| ---------------- | ---------------------------------------------------------------------------- |
| `chart_identity` | opaque `calculation_key`                                                     |
| `kind`           | `natal` или `cosmogram`                                                      |
| `zodiac`         | `tropical` в M1                                                              |
| `house_system`   | код для natal; `null` для cosmogram                                          |
| `points[]`       | `id`, `longitude`, `sign`, `degree`, `minute`, `house`, `retrograde`         |
| `angles`         | `asc`, `mc`, `vertex`, `dsc`, `ic` как `AngleDTO`; `null` для cosmogram       |
| `houses[]`       | `number`, `cusp_longitude`, `sign`, `degree`, `minute`; `null` для cosmogram |
| `aspects[]`      | `from`, `to`, `type`, `orb`, `category`                                      |

Порядок points фиксирован:
`sun`, `moon`, `mercury`, `venus`, `mars`, `jupiter`, `saturn`, `uranus`,
`neptune`, `pluto`, `chiron`, `true_node`, `south_node`, `mean_apog`, `selena`,
`pars_fortune`. Неизвестный новый engine point не публикуется автоматически.
Houses сортируются по number; aspects сохраняют канонический порядок engine.

`AngleDTO = {longitude: number, sign: string, degree: integer, minute: integer}`;
других полей нет. `sign` в `points[]`, `houses[]` и `AngleDTO` имеет ровно
одно из значений `Aries`, `Taurus`, `Gemini`, `Cancer`, `Leo`, `Virgo`,
`Libra`, `Scorpio`, `Sagittarius`, `Capricorn`, `Aquarius`, `Pisces` в
указанном регистре. `degree` — целое 0…29, `minute` — целое 0…59.
Для `dsc` и `ic` projector нормализует противоположную долготу из
сохранённой долготы `asc` и `mc`, сдвигает сохранённый
`ZodiacPosition.sign_index` на шесть знаков, а `degree/minute` копирует
без повторного округления из сохранённого `ZodiacPosition`.

`aspects[].from/to` — строковые ID. Исходная `AspectPointRef` каждого конца
обязана иметь `chart == "natal"` и `body`, равный реально опубликованному
ID из 16 `points[]` выше либо `asc`, `mc`, `vertex`. `dsc/ic` не входят в
аспектные ID. Другая chart ownership, недопустимый или dangling ID —
projector defect с безопасным 500, а не частичной картой. Для cosmogram
`house_system`, `angles`, `houses` и `points[].house` равны null; публикуются
только устойчивые аспекты ADR-0032 между реально опубликованными points.
Поле `time_dependent` не синтезируется.

В DTO не входят `CalculationVersion`, `ChartSpec`, координаты, Julian day,
ephemeris flags/path, raw warnings, stored payload, strength, configurations,
rulers и interceptions.

### 7.3. Error DTO

```json
{
  "code":"INPUT_REQUIRED",
  "detail_code":null,
  "user_message":"Проверьте введённые данные и исправьте отмеченные поля.",
  "retryable":false,
  "state_version":0,
  "issues":[{"field":"birth.place","code":"INVALID"}]
}
```

Schema issues используют стабильные field IDs: `birth_date → birth.date`,
`birth_time → birth.time`, `place_id → birth.place`, malformed body →
`request.body`, extra field → `request.<name>`. Raw Pydantic detail, input,
stack trace, cookie, run/application statuses не публикуются.

`retryable=true` означает, что причина считается временной и для данного
`code` существует recovery policy. Поле само по себе не разрешает повторить
тот же HTTP-запрос. До admission клиент может повторить запрос после
`Retry-After`; после неопределённого результата commit применяется только
code-specific сверка из §9.2. Поэтому жёсткое
`ApplicationStateCommitFailure.retryable=true` передаётся без искажения, но
никогда не означает автоматический повтор `POST /charts/natal`.

## 8. Mapping ошибок

### 8.1. `ApplicationResult` build

| Result                           | HTTP | Cookie                  | Публичный результат                                |
| -------------------------------- | ---: | ----------------------- | -------------------------------------------------- |
| `ApplicationCommitted`           |  200 | renew                   | `chart_ready` + committed artifact                 |
| `ApplicationAlreadyApplied`      |  200 | renew                   | `already_applied`; без artifact; затем GET current |
| `ApplicationInputRequired`       |  422 | renew                   | application code/message/version/issues            |
| retryable resolution failure     |  503 | renew                   | safe application fields                            |
| non-retryable resolution failure |  500 | renew                   | safe application fields                            |
| `EPHEMERIS_UNAVAILABLE`          |  503 | renew                   | safe application fields                            |
| other calculation failure        |  500 | renew                   | safe application fields                            |
| `ApplicationSessionAbsent`       |  409 | clear                   | session code/reason                                |
| `ApplicationStateReadFailure`    |  503 | unchanged               | storage code/detail                                |
| `ApplicationStateCommitFailure`  |  503 | renew                   | `STATE_COMMIT_FAILED`; outcome unknown             |
| `ApplicationSuperseded`          |  409 | renew                   | `RESULT_SUPERSEDED`, actual version                |
| any `ApplicationInternalFailure` |  500 | according to load state | public `INTERNAL_FAILURE` only                     |

`HANDLER_NOT_REGISTERED`, application internal subtype, traceback и internal
detail остаются только в журнале. Правило сохранения application fields не
распространяется на internal failures. Для `ApplicationStateCommitFailure`
публичное `retryable=true` сохраняет application contract, а разрешённое
действие ограничено сверкой current chart по §9.2.

### 8.2. Transport/admission errors

| HTTP | `code`                        | `detail_code`                                    | `user_message`                                             | retryable |
| ---: | ----------------------------- | ------------------------------------------------ | ---------------------------------------------------------- | --------: |
|  400 | `FORWARDED_HEADER_INVALID`    | null                                             | `Некорректные данные доверенного прокси.`                  |     false |
|  403 | `ORIGIN_NOT_ALLOWED`          | null                                             | `Источник запроса не разрешён.`                            |     false |
|  404 | `NOT_FOUND`                   | null                                             | `Адрес не найден.`                                         |     false |
|  405 | `METHOD_NOT_ALLOWED`          | null                                             | `Метод запроса не поддерживается.`                         |     false |
|  408 | `REQUEST_TIMEOUT`             | `BODY_RECEIVE_TIMEOUT`                           | `Не удалось получить запрос вовремя.`                      |      true |
|  409 | `SESSION_REQUIRED`            | null                                             | `Сначала откройте или восстановите сессию.`                |     false |
|  413 | `REQUEST_TOO_LARGE`           | null                                             | `Запрос превышает допустимый размер.`                      |     false |
|  415 | `UNSUPPORTED_MEDIA_TYPE`      | null                                             | `Отправьте запрос в формате JSON UTF-8.`                   |     false |
|  422 | `INVALID_REQUEST`             | stable validation detail or null                 | `Проверьте формат запроса и значения полей.`               |     false |
|  429 | `SESSION_CREATE_RATE_LIMITED` | `IP_HOURLY_LIMIT`                                | `Слишком много новых сессий. Попробуйте позже.`            |      true |
|  429 | `BUILD_SESSION_RATE_LIMITED`  | `SESSION_HOURLY_LIMIT` или `SESSION_DAILY_LIMIT` | `Лимит построений для этой сессии исчерпан.`               |      true |
|  429 | `BUILD_IP_RATE_LIMITED`       | `IP_HOURLY_LIMIT` или `IP_DAILY_LIMIT`           | `Слишком много построений из этой сети. Попробуйте позже.` |      true |
|  429 | `PLACE_SEARCH_RATE_LIMITED`   | `IP_MINUTE_LIMIT`                                | `Слишком много запросов поиска. Попробуйте позже.`         |      true |
|  500 | `INTERNAL_FAILURE`            | null                                             | `Произошла внутренняя ошибка.`                             |     false |
|  503 | `BUILD_CAPACITY_EXHAUSTED`    | null                                             | `Все слоты расчёта заняты. Попробуйте позже.`              |      true |
|  503 | `SESSION_CREATE_FAILED`       | storage code или collision exhausted             | `Не удалось создать сессию. Попробуйте ещё раз.`           |      true |
|  503 | `SERVICE_SHUTTING_DOWN`       | null                                             | `Сервис перезапускается. Попробуйте ещё раз.`              |      true |
|  504 | `BUILD_TIMEOUT`               | `OPERATION_DEADLINE_EXCEEDED`                    | `Расчёт не завершился вовремя. Проверьте текущую карту.`   |     false |

Admission errors не имеют `state_version/issues`; все содержат полный ErrorDTO,
`Retry-After` по §4.4, `Cache-Control: no-store`, `X-Request-ID`.
`BUILD_TIMEOUT` возвращается без `Set-Cookie`: cookie остаётся unchanged,
потому что transport не имеет подтверждённого load/outcome для её renew или
clear. Его `retryable=false` запрещает повтор POST; `Retry-After: 5` задаёт
момент первой сверки через current GET.

## 9. Admission, deadlines и recovery

### 9.1. Лимиты

| Scope                      |             Window/capacity | Code                          |
| -------------------------- | --------------------------: | ----------------------------- |
| session create / client IP |       300 за скользящий час | `SESSION_CREATE_RATE_LIMITED` |
| build / session            |   20 за час; 100 за 24 часа | `BUILD_SESSION_RATE_LIMITED`  |
| build / client IP          | 300 за час; 1500 за 24 часа | `BUILD_IP_RATE_LIMITED`       |
| active build / process     |                           5 | `BUILD_CAPACITY_EXHAUSTED`    |
| place search / client IP   |               120 за минуту | `PLACE_SEARCH_RATE_LIMITED`   |

Transport-invalid запрос quota не расходует. Build session/IP windows и
capacity резервируются атомарно. После проверки cookie transport в одной
критической секции без мутации оценивает четыре build rate bucket
(session/IP × 1 час/24 часа) и capacity:

1. Если исчерпан хотя бы один rate bucket, ответ `429`; ни bucket, ни permit не
   расходуется. Публичные code и `detail_code` берутся по доминирующему bucket:
   его следующий момент допуска позже остальных исчерпанных bucket. При равном
   моменте session раньше IP, а окно 24 часа раньше часового. `Retry-After`
   соответствует этому самому позднему моменту по §4.4.
2. Если rate допускает запрос, но заняты все пять permits, ответ
   `503 BUILD_CAPACITY_EXHAUSTED` с `Retry-After: 1`; rate не расходуется.
3. Иначе одна атомарная операция увеличивает все четыре bucket и резервирует
   один permit.

В `http_admission_rejected` записываются `class=rate|capacity`, scope и
detail доминирующего bucket при rate-отказе и `retry_after`; список всех
исчерпанных bucket в компактный INFO не добавляется. У создания сессии и
поиска мест по одному bucket; отказ admission квоту не расходует.
После admission учитываются cache hit, `INPUT_REQUIRED`, typed failure,
Superseded, timeout и disconnect. Creation collision attempts считаются одним
запросом. Окна используют injected monotonic clock, boundary inclusive для
нового запроса после expiry, `Retry-After` округляется вверх минимум до 1.
Неактивные buckets удаляются не позже максимального окна.

Counters M1 process-local и допускают ровно один web process. Multi-worker
deployment и rolling versions требуют общего limiter/coordination решения в
deployment change; запуск нескольких workers с M1-конфигурацией запрещён.

Отдельный application-limit на `ContextService.load` по синтаксически валидной
cookie в M1-6 не вводится. Analysis предлагает принять это как низкий риск
контролируемого одно-worker стенда: случайный opaque ID вызывает индексированный
SQLite lookup/touch до creation admission. До публичного M1-12 reverse proxy
обязан ограничивать общую частоту business requests на IP; evidence перегрузки
или переход к нескольким workers является условием добавить отдельный shared
read limiter. Риск для контролируемого M1-стенда принят Lead 2026-09-30.

### 9.2. Неопределённый build outcome

Orchestrator может выполнить один exact retry save внутри того же `execute` с
исходными delta и expected version, пока не истёк `run.deadline`. Это не
является повтором HTTP-запроса.

`STATE_COMMIT_FAILED` означает неопределённый результат завершившегося commit.
Он сохраняет application `retryable=true`, но code-specific recovery — только
`GET /charts/current` после `Retry-After: 1`; автоматического POST нет.

`BUILD_TIMEOUT` означает, что transport deadline истёк и запускается выбранный
для M1-6 fail-fast flow C. Ответ содержит `retryable=false`, `Retry-After: 5` и
unchanged cookie. До завершения supervisor restart клиент не повторяет POST;
business request может получить 503. После восстановления readiness клиент
выполняет bootstrap и только затем `GET /charts/current`:

- current birth соответствует отправленному intent — показать сохранённую
  карту и считать действие завершённым;
- current отличается — показать актуальную карту/конфликт;
- current empty/старый после restart означает, что старый process больше не
  владеет задачей; можно предложить человеку явный новый POST.

Для `STATE_COMMIT_FAILED` recovery остаётся прежним: current проверяется после
`Retry-After: 1`; empty/старый current допускает только явный новый POST.
Каждый новый POST делает свежий load и использует новую expected version. Если
предыдущий commit всё-таки состоялся, повтор может записать то же намерение ещё
раз и увеличить `state_version`; обещание «original expected» между
HTTP-запросами не переносится. Отсутствие status endpoint принято как M1
ограничение варианта C; target state A изолирует ownership в worker process.

### 9.3. Disconnect и timeout

Disconnect не откатывает admission quota. Каждый принятый build удерживает
собственный permit. До commit операция отменяется; после старта protected commit
inner task удерживается и ожидается. Если commit подтвердился после
disconnect/504, последующий bootstrap + current GET видит карту.
Permit не освобождается раньше завершения всей работы, к которой запрос
присоединился: его `execute`, общего single-flight расчёта и protected
commit, если он начат. Завершение сокета или отменённого `execute` само по
себе не является сигналом release.

В M1-6 для отменённого waiter разрешён консервативный release: ждать
завершения всех resolver leaders, активных на момент отмены. Поэтому
посторонний leader может задержать освобождение permit; точный per-request
release не обещается. Отправленные SQLite и catalog executor futures, которые
могут пережить отмену await, удерживаются отдельно: общий
`ApplicationRuntime.drain()` охватывает resolver leaders, но не эти futures.
При пяти удерживаемых permits шестой build получает
`503 BUILD_CAPACITY_EXHAUSTED`, пока общий расчёт жив.

Для M1-6 Lead выбрал вариант C: если принятая build-задача не получила terminal
outcome к 30-секундному deadline, процесс атомарно закрывает admission и
переходит в unhealthy. Оба health endpoint возвращают 503, а внешний supervisor
перезапускает весь web process. Старый процесс не сообщает ложное освобождение
permit; незавершённые запросы обрываются, а состояние после restart проверяется
через bootstrap и `GET /charts/current`. Target state — вариант A: расчёт
переносится в отдельный calculation worker, запущенный в отдельном process,
который можно завершить и заменить без перезапуска HTTP process.
30 секунд ограничивают время до перехода здорового процесса в unhealthy,
а не обещают фактическое освобождение permit или момент внешнего restart.

## 10. Client IP и trusted proxy

Direct mode: client IP равен ASGI peer; forwarding headers игнорируются.

Proxy mode включается только с непустым CIDR allowlist trusted peers:

1. если непосредственный peer не trusted, все forwarding headers игнорируются;
2. от trusted peer принимаются ровно по одному `X-Forwarded-For` и
   `X-Forwarded-Proto`; proto обязан быть `https`;
3. XFF содержит не более 10 comma-separated IP literal без port, empty item,
   zone id или hostname;
4. transport добавляет peer справа и идёт справа налево, отбрасывая trusted
   hops; первый untrusted IP становится client IP;
5. если untrusted hop нет либо header malformed, запрос получает
   `400 FORWARDED_HEADER_INVALID` до admission;
6. IPv4, IPv6 и IPv4-mapped IPv6 приводятся к канонической форме до bucket key.

Приложение не стартует, если proxy mode включён без allowlist/origin HTTPS.
Raw IP и forwarding chain не пишутся на INFO; допускается keyed digest для
метрик только после отдельного privacy решения.

## 11. Startup, health, reaper и shutdown

### 11.1. Startup и health

Settings проверяются до открытия ресурсов. Ошибка origin, proxy, limit,
deadline, interval, каталога мест, SQLite/runtime composition или обязательной
CalculationVersion завершает startup; уже открытые ресурсы закрываются в
обратном порядке.

`GET /health/live` возвращает 200, пока event loop обслуживает запрос и
fail-fast watchdog не перевёл process в unhealthy. После такого перехода live
возвращает 503 до перезапуска внешним supervisor. `GET /health/ready` возвращает
200 только после успешной сборки runtime, открытия PlaceSearch и запуска reaper
ownership; с начала shutdown либо unhealthy — 503. Health не читает
SQLite/каталог на каждый вызов и не принимает cookie.

Оба endpoint служат только reverse proxy/orchestrator на loopback либо
внутренней сети. Публичный proxy не маршрутизирует `/health/*`; внешний запрос
получает его 404. Внутренний listener не требует cookie или Origin, а доступ к
нему ограничивает deployment. Эта экспозиция является обязательной границей
M1-6; конкретные network ACL и manifest принадлежат M1-12.

### 11.2. Reaper

Одна periodic task вызывает `runtime.reap_expired()` каждые 15 минут по
monotonic clock. Следующий run планируется от завершения предыдущего, поэтому
параллельных runs нет. Ошибка одного run журналируется и не убивает task;
следующий run остаётся запланирован. Shutdown отменяет ожидание следующего run
и дожидается активного run.

### 11.3. Shutdown

1. atomic flag закрывает admission; readiness становится 503;
2. новые business requests получают `SERVICE_SHUTTING_DOWN`;
3. reaper wait/task останавливается и ожидается;
4. task registry ждёт до 30 секунд все принятые business requests, включая
   bootstrap, current, places и build, а также отправленные ими SQLite/catalog
   executor futures, которые могут пережить отмену ожидающего await;
5. по grace expiry отменяются задачи, которые не начали protected commit;
   commit tasks сохраняют ownership и ожидаются по Orchestrator contract;
6. после нулевого active count requests и retained futures вызывается
   `ApplicationRuntime.aclose()`;
7. внешний `SqlitePlaceCatalog`/executor закрывается последним.

Если по истечении shutdown grace остаётся protected/native task или
SQLite/catalog executor future без terminal outcome, применяется выбранный для
M1-6 вариант C: process становится unhealthy,
`ApplicationRuntime.aclose()` под активной задачей не вызывается, внешний
supervisor завершает и перезапускает process. Нельзя молча освободить permit,
оставив неучтённую работу, либо подавить cancellation/error. Developer обязан
доказать этот порядок детерминированными тестами до acceptance DP-HTTP-04.

### 11.4. Routing, HEAD/OPTIONS и schema UI

- Неизвестный path — JSON 404; known path/wrong method — JSON 405 + `Allow`.
- `HEAD` поддержан только для `/health/live` и `/health/ready` и возвращает тот
  же status/headers без body. Для business endpoint — 405, без session touch.
- В базовом same-origin режиме `OPTIONS` business endpoint — 405. При отдельно
  утверждённом CORS allowlist preflight обрабатывается до business pipeline.
- `/docs`, `/redoc`, `/openapi.json` в production не зарегистрированы и дают
  404. В local/test schema route может включаться отдельным settings flag;
  OpenAPI contract tests используют `app.openapi()` без публикации route.

## 12. Наблюдаемость

| Event                             | Level        | Обязательные поля                                                        |
| --------------------------------- | ------------ | ------------------------------------------------------------------------ |
| `http_request_started`            | INFO         | request_id, method, route template                                       |
| `http_message` send/receive       | INFO         | request_id, run_id для build, peer, operation, message_type; без payload |
| `http_admission_rejected`         | INFO         | request/run ID, class, scope, public code, detail, retry_after           |
| `http_cookie_replaced`            | INFO         | request ID, reason; без cookie/session ID                                |
| `chart_unavailable`               | ERROR        | request ID, safe_reason; без payload/birth/session ID                    |
| `http_request_finished`           | INFO/WARNING | IDs, outcome, HTTP status если отправлен, public code, duration_ms       |
| `session_reaper_started/finished` | INFO/WARNING | reaper_run_id, schedule, deleted_count либо safe error, duration         |
| `http_shutdown_started/finished`  | INFO         | active count, outcome, duration                                          |

`http_message` покрывает фактические переходы: bootstrap ↔ create/load;
current chart ↔ load и → session_view; places ↔ search; build ↔ admission и
Orchestrator. `send` предшествует вызову, `receive` пишется только после typed
result. Existing application/component events сохраняются.

INFO не содержит body, query text, cookie, session ID, IP, birth data или
ChartDTO. `http_request_finished` имеет INFO для 2xx/4xx, WARNING для 5xx,
timeout, unexpected exception и cancellation; terminal event ровно один.

## 13. Acceptance scenarios

Каждый negative scenario содержит positive control, доказывающий, что
проверяемый путь вообще выполняется.

### AS-HTTP-01 — первый bootstrap и current empty

Без cookie bootstrap создаёт ровно одну session, возвращает `ready/0`, Secure
cookie и `http_cookie_replaced(missing)`. Следующий GET current возвращает
`empty/0`; Orchestrator/engine не вызваны.

### AS-HTTP-02 — restore после restart

Live cookie и persisted StoredChart при пустом runtime cache: bootstrap
возвращает только `ready/N`; отдельный GET current возвращает тот же
chart_identity. Resolver/cache/engine не вызваны, version не меняется.

### AS-HTTP-03 — stale, unavailable и empty current chart

Три snapshots дают соответственно `chart_ready/stale=true`,
`chart_unavailable` с ERROR event и `empty`. Ни один путь не делает CAS или
расчёт; structural aggregate corruption даёт 503, не unavailable.

### AS-HTTP-04 — session absent и read failure

Current GET для expired/not-found даёт 409 и clear cookie; StateReadFailed даёт
503 с unchanged cookie. Bootstrap после absent может создать новую session;
если creation admission/create отказывает, старая absent cookie всё равно
гасится, новая не выдаётся. После StateReadFailed bootstrap session не создаёт.

### AS-HTTP-05 — duplicate cookie

Два значения cookie: bootstrap проходит creation quota и заменяет их одним
новым значением; current/build дают 409 SESSION_REQUIRED и не вызывают store
load/Orchestrator. Один валидный cookie является positive control.

### AS-HTTP-06 — три collision и create failure

Три сгенерированных ID последовательно дают `SessionIdConflict`: четвёртый ID
не генерируется, чужие records не читаются, ответ 503 с collision detail и без
новой cookie. Отдельный first-attempt success создаёт одну session.

### AS-HTTP-07 — session creation limit

300-й create за rolling hour проходит, 301-й получает 429/Retry-After и не
генерирует ID/не вызывает create. Live-cookie bootstrap не расходует quota;
точная expiry boundary снова допускает запрос.

### AS-HTTP-08 — place success и empty

Valid query возвращает suggestions, другой valid query — `items=[]`; session
не читается, координаты/tz не публикуются.

### AS-HTTP-09 — limit/query grammar

`limit=1`, `20` и omitted проходят; `010`, `+5`, duplicate и `21` дают
`LIMIT_INVALID`; raw query 513 code points даёт `QUERY_TOO_LONG`. Invalid path
не достигает SQL; valid запрос подтверждает вызов search.

### AS-HTTP-10 — component place errors

`InvalidPlaceQuery` даёт compact 422 с component detail, catalog unavailable —
503. Unexpected error становится 500, а не retryable catalog failure.

### AS-HTTP-11 — build natal и cosmogram

Known time даёт committed natal chart; null time — cosmogram с null houses,
angles, house_system и point houses. Оба сохраняют state+StoredChart атомарно.

### AS-HTTP-12 — validation priority build

Отдельные запросы доказывают 403 Origin, 415 media type, 413 size и schema 422.
Schema issues имеют `birth.date/time/place`; malformed JSON без cookie даёт
422, valid JSON без cookie — 409. Ни один rejected request не вызывает
admission/Orchestrator.

### AS-HTTP-13 — дата: schema против domain

`1990-02-30` → INVALID_REQUEST/birth.date; future и outside ephemeris range →
INPUT_REQUIRED/birth.date/UNSUPPORTED с min/max; skipped timezone date →
INPUT_REQUIRED/INVALID. Valid boundary dates проходят resolver.

### AS-HTTP-14 — InputRequired и dependency failures

Unknown place/ambiguous local time дают typed issues и renew cookie. Resolver
unavailable, ephemeris unavailable, read/commit failures соблюдают §8; failure
не публикуется как InputRequired.

### AS-HTTP-15 — internal code не утекает

`HANDLER_NOT_REGISTERED` и другой ApplicationInternalFailure дают публичный
500 `INTERNAL_FAILURE`; журнал сохраняет internal subtype. Positive typed
calculation failure сохраняет разрешённый public code/detail.

### AS-HTTP-16 — явный rebuild

POST поверх существующей карты загружает N, сохраняет новую карту как N+1 и
возвращает committed artifact. Ошибка до/во время unconfirmed commit не
подменяет подтверждённую текущую карту в ответе.

### AS-HTTP-17 — две вкладки

Обе вкладки первоначально читают N. B rebuild-ит N+1. Серверная проверка:
поздний явный POST A делает fresh load N+1 и использует эту версию как CAS
expected; отображаемый вкладкой N не является серверным precondition.
Обновление экрана A проверяется в [приёмке UI M1-7](../ui_ux/requirements.md#13-приёмка).

### AS-HTTP-18 — concurrent intents и AlreadyApplied

Два execute с одним original N: одинаковый intent даёт Committed и
AlreadyApplied, разные — Committed и Superseded. AlreadyApplied response не
содержит request artifact; GET current возвращает фактически сохранённый winner.

### AS-HTTP-19 — recovery после неопределённого build outcome

Для `STATE_COMMIT_FAILED` lost acknowledgement проверяется в двух вариантах:
commit состоялся и не состоялся. Сервер возвращает `retryable=true` и
`Retry-After: 1`; один принятый HTTP POST вызывает `execute` ровно один раз.
После отдельного GET current явный новый POST доказывает fresh load/expected
и допускает новое увеличение version. Порядок действий клиента и отсутствие
автоматического второго POST проверяются в
[приёмке UI M1-7](../ui_ux/requirements.md#13-приёмка).

Для `BUILD_TIMEOUT` серверная проверка включает `retryable=false`,
`Retry-After: 5`, отсутствие `Set-Cookie` и ровно один `execute` для
принятого POST. В одном тесте commit успевает подтвердиться до завершения
старого process, и current после restart видит карту; в другом commit не
происходит и current остаётся empty. Restart проверяется двумя app/runtime
instances с пустым process-local cache поверх одного реального SQLite-файла
сессий. Старый process не сообщает terminal task или освобождение permit.
Original expected между HTTP requests не переносится. Отсутствие
автоматического повторного POST и условие явного повтора проверяются в
[приёмке UI M1-7](../ui_ux/requirements.md#13-приёмка).

### AS-HTTP-20 — session потеряна на build

Absent при load/commit даёт соответствующий 409 и clear cookie; build не
создаёт session. Новый bootstrap создаёт session, но не повторяет build.

### AS-HTTP-21 — rate limits и CGNAT

Boundary tests всех session/IP hourly/daily windows и place window проверяют
codes/details/Retry-After. Сценарий 10 sessions × 5 build с одним IP проходит;
300 hourly IP build проходят, 301-й отклоняется. Rejected request не входит
в Orchestrator. При одновременно исчерпанных часовом session и суточном IP
bucket с разными моментами допуска ответ `BUILD_IP_RATE_LIMITED` /
`IP_DAILY_LIMIT`, а `Retry-After` указывает поздний IP-момент. При равенстве
моментов выбирается session, а внутри одного scope — 24-часовое окно. Если
rate и capacity исчерпаны одновременно, ответ 429; ни один bucket/permit не
меняется. Ровно в момент допуска запрос проходит и расходует все четыре
bucket и один permit. Отдельный случай свободного rate и занятой capacity
проверяется в AS-HTTP-22.

### AS-HTTP-22 — capacity и deadline

Пять barrier-controlled tasks удерживают permits; шестая получает быстрый 503
с `Retry-After: 1` и не расходует rate. Never-finishing fake operation достигает
504 с `retryable=false`, `Retry-After: 5` и unchanged cookie, после чего process
атомарно закрывает admission, а live/ready возвращают 503. Старый process не
сообщает освобождение permit. Fake supervisor перезапускает process; новый
build после restart проходит.

### AS-HTTP-23 — slow body

Fake ASGI receive не отдаёт следующий body chunk: через 5 секунд fake clock
получен 408, body не парсится. Быстрый body той же длины проходит. `sleep` не
используется.

### AS-HTTP-24 — disconnect после admission

Disconnect до commit отменяет без мутации. Disconnect после старта protected
commit не теряет inner task; после подтверждения bootstrap + current GET видят
карту. Два принятых запроса, присоединившиеся к одному single-flight leader,
удерживают два permit. Если один waiter отменён, его permit остаётся занятым,
пока общий расчёт жив. При пяти занятых permit шестой build получает
`503 BUILD_CAPACITY_EXHAUSTED`; после завершения удерживаемой работы и
фактического release следующий build допускается. Посторонний resolver leader
может задержать release отменённого запроса. Отдельные barrier-проверки
доказывают удержание SQLite/catalog executor futures после отмены await.
Если retained work достигает 30-секундного deadline, применяется тот же
unhealthy/supervisor restart flow C, после чего current становится
authoritative; старый process не сообщает фиктивного release.

### AS-HTTP-25 — reaper

Fake clock доказывает 15-минутную периодичность от завершения run, отсутствие
overlap через barrier, продолжение после одного typed/unexpected failure и
ожидание active run на shutdown.

### AS-HTTP-26 — startup/readiness/shutdown

Каждая invalid setting и обязательная dependency failure завершает startup и
закрывает уже открытые resources. Ready становится 200 только после полной
сборки и 503 до/во время shutdown. Overdue build по варианту C переводит оба
health endpoint в 503; fake supervisor restart создаёт новый healthy process.
Internal proxy видит health, публичный route не опубликован. Active
request/commit ordering проверяется events/barriers.

### AS-HTTP-27 — обязательные headers

Таблично проверить 200, 403, 409, 413, 415, 422, 429, 500, 503, 504:
`Cache-Control:no-store` и server `X-Request-ID` везде. Проверить exact
`Retry-After` из §4.4: rolling-window calculation, 1 для body/capacity/commit
recovery, 5 для dependency/504 и 30 для shutdown.

### AS-HTTP-28 — projector contract

Golden artifact проверяет точный whitelist и порядок points/houses/aspects.
Новый unknown engine field/point не появляется. Dangling aspect reference даёт
500. Golden фиксирует точный словарь и регистр 12 `sign`, `AngleDTO` со
строго четырьмя полями, строковые `aspects[].from/to` и только разрешённые
реально опубликованные ID. Ссылка на другую chart, `dsc/ic` как endpoint
аспекта и dangling ID дают безопасный 500. На границе округления `dsc/ic`
сохраняют `degree/minute` исходных `asc/mc` и сдвигают знак на шесть.
Cosmogram invariant проверяет все null-поля и устойчивые аспекты.
Golden `SessionViewDTO` для `chart_ready` и `chart_unavailable` проверяет
точный whitelist `BirthViewDTO` в двух состояниях: известное время `HH:MM`,
сохранённый числовой offset и разрешённый `pre_1970_offset_unverified` для
старой даты; неизвестное время с `birth_time=null`,
`utc_offset_seconds=null`, сохранённым `tz_id` и без `noon_anchor_*`.
Рассинхронизация `time_unknown`/`birth_input.birth_time` и ненулевые секунды
сохранённого времени дают safe 500 с renew cookie; рядом есть успешный
контроль. Новые внутренние поля и warning codes не появляются в JSON.

### AS-HTTP-29 — routes, HEAD, OPTIONS и production schema

Unknown route → 404; wrong method и HEAD business route → 405/Allow без session
touch; HEAD health mirrors status; OPTIONS same-origin → 405. Production не
регистрирует docs/redoc/openapi, local flag регистрирует schema. Malformed
trusted `X-Forwarded-For` → 400 до cookie/admission; корректная цепочка даёт
канонический client IP. Для недоверенного peer spoofed XFF/XFP игнорируются:
два разных непосредственных peer с одинаковым spoofed XFF расходуют два
раздельных IP bucket, а ASGI peer остаётся ключом каждого bucket.

## 14. Gate Analysis → Development

- Developer подтвердил DTO/mapping, trusted proxy algorithm, limits, leaf
  timeouts, task registry и shutdown ownership.
- Tester подтвердил deterministic coverage AS-HTTP-01…29 без `sleep`.
- Lead утвердил DP-HTTP-01…06 и численные значения DP-HTTP-02/04.
- OpenAPI фиксирует exact schemas, extra forbid и response variants.
- HTTP и session diagrams согласованы с документом.
- Не остаётся blocker, позволяющий admitted task держать capacity бесконечно.

После реализации запускаются target HTTP tests, связанные
application/session/catalog tests, `tests/test_module_boundaries.py`, затем
полный `pytest`. Документационный анализ сам по себе эти проверки не заменяет.

## 15. Findings и ограничения

| ID            | Тип                              | Состояние/решение                                                                                                                                                                | Статус                                                                   |
| ------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| FIND-HTTP-001 | projection gap | расширить чистый `session_view` birth projection без I/O | Lead включил в M1-6; Developer реализует и проверяет |
| FIND-HTTP-002 | accepted M1 limitation           | current birth place содержит только id/display name                                                                                                                              | принято Lead 2026-09-30 |
| FIND-HTTP-003 | proxy decision                   | точный алгоритм предложен в §10                                                                                                                                                  | Developer review выполнен; принято Lead; реализация впереди |
| FIND-HTTP-004 | lifecycle decision               | для M1-6 выбран fail-fast restart process; target state — отдельный calculation worker/process                                                                                   | решение Lead; Developer предоставляет implementation evidence            |
| FIND-HTTP-005 | deployment limitation            | process-local counters, один worker/CalculationVersion                                                                                                                           | принято Lead 2026-09-30 |
| FIND-HTTP-006 | UI alignment                     | UI синхронизирован с separate current GET и whitelist                                                                                                                            | resolved in analysis draft                                               |
| FIND-HTTP-007 | former build projection blocker  | build DTO больше не требует birth view; current GET является явной операцией                                                                                                     | resolved by ADR-0040 revision                                            |
| FIND-HTTP-008 | deferred public API              | reset/delete endpoint отсутствует в M1-6                                                                                                                                         | explicit scope; future change                                            |
| FIND-HTTP-009 | native timeout risk              | вариант C ограничивает ущерб restart всего process; вариант A изолирует расчёт в target state                                                                                    | решение выбрано; acceptance блокируется до deterministic evidence        |
| FIND-HTTP-010 | provenance                       | ADR-0039 восстановлен из reflog commit `cf16d41`; точный файл ADR-0040 не найден, текст восстановлен                                                                             | формулировка согласована Lead 2026-09-30 |
| FIND-HTTP-011 | retry semantics                  | `retryable` определён как transient + code-specific policy; `STATE_COMMIT_FAILED=true` требует current GET, `BUILD_TIMEOUT=false`, cookie unchanged; §9.2 и AS-HTTP-19 дополнены | контракт принят в DP-HTTP-01; реализация впереди |
| FIND-HTTP-012 | ADR provenance                   | реестр сохраняет исходный вариант C от 24.09; ADR-0040 содержит ревизию 29.09 C → D после ADR-0041                                                                               | ревизия согласована Lead 2026-09-30 |
| FIND-HTTP-013 | acceptance gap                   | AS-HTTP-29 проверяет ignored spoofed XFF и разные bucket для двух untrusted peer                                                                                                 | resolved in analysis                                                     |
| FIND-HTTP-014 | contract gap                     | любой присутствующий Origin проверяется у всех business endpoint, включая GET; health исключён                                                                                   | resolved in §4.4                                                         |
| FIND-HTTP-015 | text/diagram mismatch            | absent/invalid/duplicate cookie гасится и при отказе bootstrap creation; missing остаётся без cookie                                                                             | resolved in §5 and AS-HTTP-04                                            |
| FIND-HTTP-016 | Retry-After values               | rolling 429 вычисляется; body/capacity/commit = 1, dependency/504 = 5, shutdown = 30                                                                                             | resolved in §4.4; Developer verifies implementation                      |
| FIND-HTTP-017 | accepted M1 risk, low | отдельного live-cookie read limiter нет; controlled single-worker, общий proxy IP-limit обязателен до public M1-12                                                               | принято Lead 2026-09-30; proxy limit перед public M1-12 |
| FIND-HTTP-018 | deployment boundary              | health доступны только internal reverse proxy/orchestrator; public proxy не маршрутизирует `/health/*`                                                                           | Developer review выполнен; принято Lead; ACL/manifest в M1-12 |
| FIND-HTTP-019 | scope/estimate | чистая birth-проекция `session_view` входит в M1-6; исходная оценка 0,5+1,5+1+1=4 дня сохранена | решение Lead 2026-09-30; реализация и проверка впереди |
| FIND-HTTP-020 | process gate | старый ADR-0040 path исправлен; scope расширен; Gantt сохраняет подтверждённую исходную оценку | Lead-owned правки в рабочем плане подготовлены; интеграция в `change/*` ожидается |
| FIND-HTTP-021 | Development Finding | нижняя граница permit при shared leader, точные AngleDTO/aspect IDs, разделение серверных и UI-доказательств AS-HTTP-17/19 | направления согласованы владельцем change; контракт уточнён в §7.2/§9.3 и AS-HTTP-17/19/24/28; S0 и исполняемое evidence ещё требуются |
| FIND-HTTP-022 | Development Finding | приоритет одновременных rate/capacity отказов и точная форма BirthViewDTO при неизвестном времени | согласовано пользователем; контракт уточнён в §7.1/§9.1 и AS-HTTP-21/28; golden и исполняемое evidence ещё требуются |

### 15.1. Классификация после review PR #37 от 2026-09-30

- Для FIND-HTTP-004/009 Lead выбрал вариант C в M1-6 и вариант A как target
  state. Выбор больше не блокирует начало реализации; acceptance блокируется до
  deterministic evidence fail-fast, health и supervisor restart.
- FIND-HTTP-011, 013–016 исправлены в контракте и согласованы Lead; реализация
  и тестовая проверка впереди. FIND-HTTP-017/018 приняты как границы M1/deployment.
- FIND-HTTP-001/019 закрыты решением Lead от 2026-09-30: чистая birth-проекция
  входит в M1-6, исходная оценка Gantt сохраняется. Developer проверяет
  реализуемость выбранного варианта C; новые findings оформляются отдельно.
  Формулировка ADR-0040 по FIND-HTTP-010/012 согласована Lead.
- FIND-HTTP-020 остаётся процессным gate: изменения Lead-owned change plan
  подготовлены на текущей ветке, Gantt сохраняет подтверждённую оценку;
  документ должен вернуться в `change/*` по процессу ролей.
- FIND-HTTP-021 подтверждён пользователем: §7.2/§9.3 и AS-HTTP-17/19/24/28
  фиксируют контракт, UI M1-7 получает клиентские проверки; техническое
  доказательство S0 и deterministic tests ещё требуются.
- FIND-HTTP-022 подтверждён пользователем: §9.1 выбирает доминирующий
  исчерпанный rate bucket до capacity, §7.1 скрывает offset noon anchor и
  задаёт чистую birth-проекцию; AS-HTTP-21/28 требуют отдельного evidence.

### 15.2. Решение по FIND-HTTP-009 / DP-HTTP-04

Суть: у каждой принятой задачи build должна быть доказанная верхняя граница
времени жизни. `asyncio` отменяет только в точках `await`; нативный вызов
эфемерид в worker thread отменить нельзя, он продолжает держать
процессный `RLock` (ADR-0013). Поэтому `wait_for` вокруг `execute()` даёт
клиенту 504, но не освобождает ни поток, ни lock.

Наблюдаемые последствия без решения:

1. **Таймаут без остановки.** Зависший вызов после 504 продолжает держать
   `RLock`; все следующие build ждут его, а bootstrap и поиск работают.
2. **Слот по сокету.** Если permit освобождать по 504, счётчик показывает
   свободные слоты при десятке живых потоков — лимит 5 становится фикцией.
   Если освобождать по terminal outcome (как требует §9.3), пять зависших
   задач навсегда занимают capacity до рестарта.
3. **Shutdown при protected commit.** Застрявший commit нельзя отменить без
   риска неопределённого агрегата; бесконечное ожидание ведёт к SIGKILL.

Lead зафиксировал в review PR #37: для M1-6 применяется вариант C, а
target state использует вариант A. Остальные варианты сохранены как история
рассмотренных альтернатив.

| Вариант                                 | Суть                                                                                                 | Цена                                                                      | Статус                  |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------- |
| A. Отдельный calculation worker/process | зависший worker завершается и заменяется; HTTP process продолжает работу                             | IPC и сериализация `ChartArtifact`, новая точка отказа                    | target state после M1-6 |
| B. Bounded leaf-операции                | таймауты на открытие эфемерид, SQLite busy timeout и т. п.; доказательство, что сам расчёт ограничен | работает только там, где у leaf есть таймаут; нужен анализ каждого вызова | не выбран               |
| C. Fail-fast restart web process        | build без terminal outcome к 30 секундам → unhealthy → restart по health внешним supervisor          | теряются все активные запросы; нужен внешний supervisor                   | выбран для M1-6         |
| D. Принятая деградация                  | ADR фиксирует допустимость деградации до restart + alert и runbook                                   | риск остаётся до ручного restart                                          | не выбран               |

Для выбранной эволюции нужны детерминированные тесты без `sleep`:
never-finishing fake operation; старый process не сообщает освобождение permit;
shutdown не закрывает runtime под активным commit; fake supervisor restart для
варианта C и kill/replace worker для target state A возвращают build capacity.

Содержательные решения документа согласованы Lead 2026-09-30. Для DP-HTTP-04
в M1-6 выбран вариант C, а A оставлен target state; реализация и
детерминированные lifecycle-тесты ещё требуются. Чистая birth-проекция
`session_view` входит в M1-6, исходная оценка Gantt 0,5+1,5+1+1=4 дня сохранена.
Предложение Analysis о 4 днях Development и 2 днях Testing не принято.

## 16. Sequence diagrams

- [`http_api/001-session-bootstrap.puml`](../sequence_diagrams/http_api/001-session-bootstrap.puml);
- [`http_api/002-place-search.puml`](../sequence_diagrams/http_api/002-place-search.puml);
- [`http_api/003-build-natal.puml`](../sequence_diagrams/http_api/003-build-natal.puml);
- [`http_api/004-current-chart.puml`](../sequence_diagrams/http_api/004-current-chart.puml).

Session 001–003 и 006 показывают тот же split flow и retry semantics. Детали
calculation/CAS остаются в component diagrams и не дублируются transport слоем.
