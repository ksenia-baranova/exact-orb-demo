# M1-6 — HTTP API and Session Middleware: implementation plan

**Дата:** 2026-09-30. **Ветка:** dev/http-api-and-session-middleware от f11275c.
**Статус:** тестовые промты 01–04 и поправки 04a подготовлены в `dev/http-api-and-session-middleware`. Production HTTP-код ещё отсутствует. Исторический Tester review Analysis/test design описан ниже; обязательный формальный Tester review пользователь отменил отдельным указанием.
**Оценка:** действующий Gantt не меняется: Lead 0,5, Analysis 1,5, Development 1, Testing 1 рабочего дня; всего 4.

Четыре дня — сохранённая Lead календарная оценка, а не оценка Developer по 13 промтам. **Предварительная оценка Developer для review: минимум 4 дня разработки и 2 дня тестирования** (с учётом четырёх маршрутов, DTO, admission, cancellation/ownership, watchdog, локального HTTPS и 29 acceptance scenarios); вместе с Lead 0,5 и Analysis 1,5 это минимум 8 рабочих дней. Это не изменение Gantt. Нижняя граница предполагает, что ранний S0 не потребует нового публичного component API, отдельного worker или переработки ownership. После S0 Developer уточняет оценку и передаёт Lead расхождение с действующим 1+1 и влияние на критический путь. Только Lead меняет Gantt отдельным решением; прежние 4 дня не выдаются за технически подтверждённый срок.

## 1. Что и зачем делаем

Добавляем локальную HTTP-границу модульного монолита: браузер получает анонимную сессию, читает сохранённую карту, ищет место и явно запускает построение карты. Существующие ApplicationRuntime, ContextService, ApplicationOrchestrator и PlaceSearch остаются владельцами своих операций. Transport отвечает за валидацию, cookie, admission, публичные DTO, deadline, lifecycle и корреляционные события.

Результат M1-6 — работающий FastAPI app с четырьмя business endpoint и двумя внутренними health endpoint, локальный HTTPS-proxy path, автоматизированные AS-HTTP-01…29, доказанный shutdown и fail-fast restart process по DP-HTTP-04. Отдельный calculation worker остаётся целевым состоянием и здесь не реализуется.

## 2. Источники, решения и состояние интеграции

Источники: [AGENTS.md](../../../AGENTS.md), [Experiment 002](../../development_approach/experiment-002-role-based-change-development.md), [HTTP requirements](../../requirements/http_api.md), [ADR-0039](../../requirements/decisions/0039-https-in-all-environments.md), [ADR-0040](../../requirements/decisions/0040-session-bootstrap-and-current-chart.md), [ADR-0041](../../requirements/decisions/0041-stored-chart-in-session.md), [HTTP sequence](../../sequence_diagrams/http_api/README.md), [session sequence](../../sequence_diagrams/session/README.md) и Lead-owned [change plan](../change_plans/http-api-and-session-middleware.md). При расхождении по HTTP-поведению действуют согласованные `http_api.md` и ADR; change plan задаёт scope, этапы и Gantt, но его версия в `f11275c` содержит старый ADR path и статусы. Для фактических интерфейсов используются текущий код и тесты на входном HEAD, а не исторические prompts.

На входном `f11275c` журнал содержит только LEAD-HTTP-001…004; DP-HTTP-03/05/06, FIND-HTTP-019 и Lead-owned change plan ещё открыты. После прямых решений владельца change записаны LEAD-HTTP-005…007, обновлены `http_api.md`, ADR-0040 и change plan; план и промты сохранены в `c7e794a` на `dev/*`. Пользователь затем подтвердил все связанные решения, включая FIND-HTTP-021/022; требования, UI-приёмка и build sequence синхронизированы на текущей ветке. Это ещё не означает возврат правок в `change/*` или наличие исполняемого evidence S0/Tester. FIND-HTTP-020 остаётся процессным gate до интеграции Lead-owned правок.

| Решение / finding | Влияние на план |
| --- | --- |
| DP-HTTP-01/02 | Четыре business endpoint, два health endpoint, whitelist DTO, typed errors, точные лимиты §9.1. |
| DP-HTTP-03 | Только raw ASGI peer; forwarding headers читаются самим transport после проверки trusted CIDR. Встроенное переписывание peer сервером должно быть выключено. |
| DP-HTTP-04, FIND-HTTP-004/009 | 30-секундный monotonic response deadline, process unhealthy и внешний supervisor restart; реальный task/leaf ownership до освобождения permit. |
| DP-HTTP-05 | Sequence задают порядок вызовов и INFO-пары, а не новый контракт. |
| DP-HTTP-06, FIND-HTTP-001/019 | Чистая birth projection из готового SessionSnapshot входит в M1-6 без I/O и новых application ports. |
| FIND-HTTP-017/018 | M1 один web process; отдельного live-cookie limiter нет. Health доступны через internal route; общая защита public traffic и ACL относятся к соответствующему deployment gate. |
| FIND-HTTP-020 | Текущие Lead-owned правки change plan ещё должны вернуться в change/* по PR; этот план их не коммитит. |

ADR-0040 пересмотрел свой исторический вариант C (`GET /charts/current` через Orchestrator/`ensure_chart`) в действующую ревизию D после ADR-0041: current читает сохранённую карту через `ContextService.load` и чистую `session_view`. Буква C в DP-HTTP-04 относится к другой таблице альтернатив — fail-fast restart process. Далее план называет этот lifecycle-механизм словами, чтобы не смешивать решения.

**Техническая находка Developer и предмет раннего S0:** при отмене ожидающего запроса ChartArtifactResolver сохраняет shielded calculation leader, хотя ApplicationOrchestrator уже может завершиться. Это подтверждается существующим тестом tests/application/test_application_bootstrap_integration.py::test_runtime_close_waits_for_cancelled_waiter_live_leader. Пользователь выбрал консервативный вариант: permit отменённого запроса удерживается до завершения всех single-flight leaders, активных на момент отмены, даже если среди них есть unrelated leader. `runtime.drain()` делает такой snapshot и потому является кандидатом на безопасный сигнал, но S0 должен доказать, что он захватывает работу, к которой присоединился запрос, а также учесть protected commit и executor futures вне resolver. Это не требование точного per-request release. Если безопасный сигнал без изменения публичного component API невозможен, оформить Development Finding для Analysis/Lead. Промт 12 реализует подтверждённое после S0 решение; при достижении 30-секундного deadline процесс уходит в fail-fast restart.

## 3. Границы и карта файлов

**Разрешено:** новый transport package src/exact_orb/http_api/, узкая чистая birth projection в src/exact_orb/application/session_view.py, необходимые зависимости FastAPI/ASGI test client в pyproject.toml, новые tests/http_api/, точечные regression tests для существующих компонентов, локальный HTTPS proxy config и runbook. Узкие изменения leaf cancellation допустимы только при подтверждённом тестом orphaned executor future и требуются для DP-HTTP-04.

**Запрещено:** менять расчётные формулы, persisted session schema, CAS-семантику, публичные component API без доказанной необходимости, добавлять распределённую координацию, отдельный worker process, аккаунты, UI, SSE, interpretation, reset/delete HTTP endpoint, скрытый второй execute/load, новые compatibility aliases или ослаблять tests/test_module_boundaries.py. Кодек StoredChart остаётся в artifact layer; transport видит только готовый artifact и безопасную проекцию.

Предлагаемая раскладка package — настройка/app factory и lifespan, request boundary, cookie, DTO/projector, admission, routes и logging. Имена внутренних модулей не являются публичным контрактом: на каждом промте можно выбрать более простой расклад, сохраняя проверяемые границы.

| Промты | Предполагаемые файлы/компоненты |
| --- | --- |
| S0/G0 | S0: read-only spike по `bootstrap.py`, `artifacts.py`, adapter/executor cancellation и существующим lifecycle-тестам. G0: [карточка тестового шва](http_api_and_session_middleware_g0.md), DTO и admission в требованиях до контрактных тестов. |
| 01–04 | tests/http_api/conftest.py и отдельные test_session.py, test_place_dto.py, test_build_admission.py, test_lifecycle.py; существующие fixtures только по необходимости. |
| 05 | pyproject.toml с совместимыми версиями FastAPI, uvicorn и test client; src/exact_orb/http_api/app.py, settings.py, lifespan.py; tests/http_api/test_lifespan.py. |
| 06 | src/exact_orb/http_api/request_boundary.py и proxy.py; tests/http_api/test_request_boundary.py. |
| 07 | src/exact_orb/application/session_view.py; src/exact_orb/http_api/dto.py и projectors.py; tests/application/test_session_view.py, tests/http_api/test_projectors.py, tests/test_module_boundaries.py. |
| 08–09 | src/exact_orb/http_api/cookie.py, routes/session.py и routes/places.py; tests/http_api/test_session.py и test_place.py. |
| 10–11 | src/exact_orb/http_api/admission.py, routes/charts.py и result_mapping.py; tests/http_api/test_admission.py и test_build.py. |
| 12 | src/exact_orb/http_api/task_registry.py и lifespan.py; при доказанной необходимости узкий cancellation seam в session/birth adapter либо `SqlitePlaceCatalog.lookup/search` / `_SqliteBackend.run`; tests/http_api/test_lifecycle.py и существующие component regression tests. |
| 13 | src/exact_orb/http_api/operation_logging.py; локальный Caddy config и runbook для mkcert, запуска и ручного restart, затронутые HTTP/session sequence и tests/http_api/test_integration.py. |

## 4. Порядок и зависимости

| Промт | Срез | Зависит от | Сценарии / критерий |
| --- | --- | --- | --- |
| S0 | Ранний read-only spike по cancellation, shared leader и leaf futures | Входной код | Доказать нижнюю границу удержания permit через snapshot активных leaders и остальные retained work; уточнить техническую оценку |
| G0 | Уточнить публичные DTO, admission и [контракт тестовой фикстуры](http_api_and_session_middleware_g0.md) | Входные модели и требования; параллельно S0 | §7.1/§9.1 и FIND-HTTP-022 внесены в `http_api.md`; app factory/client/runtime и общий scheduler для body, watchdog и reaper определены до тестов; обязательный review Tester позднее отменён пользователем |
| Gate A — Analysis → Development | Исторический review Analysis/test design и §14 HTTP requirements | S0, G0 | Первоначальный формальный порядок описан в §7; пользователь прямо разрешил 01–04 и отменил обязательный Tester review. Фактические результаты тестов и ограничения — в §10–11 |
| [01](../../../prompts/2026-09-30/http-api-and-session-middleware/01-contract-tests-session.md) | Контрактные тесты сессии и current | Gate A, G0 | AS-HTTP-01…07 и BirthViewDTO golden для обоих chart statuses; restore без расчёта |
| [02](../../../prompts/2026-09-30/http-api-and-session-middleware/02-contract-tests-place-dto.md) | Контрактные тесты place, validation, DTO | 01, G0 | AS-HTTP-08…15, 28; whitelist и ошибки |
| [03](../../../prompts/2026-09-30/http-api-and-session-middleware/03-contract-tests-build-admission.md) | Контрактные тесты build, recovery, admission | 01–02 и S0/AS-HTTP-24 через Gate A | AS-HTTP-16…22; races, limits, unknown outcome |
| [04](../../../prompts/2026-09-30/http-api-and-session-middleware/04-contract-tests-lifecycle.md) | Контрактные тесты receive, lifecycle, routes и logs | 01–03 и S0/AS-HTTP-24 через Gate A | AS-HTTP-23…27, 29; disconnect, watchdog, reaper |
| [04a](../../../prompts/2026-09-30/http-api-and-session-middleware/04a-review-corrections.md) | Поправки RED-тестов после независимого ревью другой моделью | 01–04 | Устранить ложные RED и слабые доказательства до production code; результаты записать ниже |
| Gate T | Самопроверка requirements, AS-HTTP-01…29, тестов и positive controls | 01–04, 04a | Замечания независимого ревью другой моделью обработаны в 04a; формальный Tester review отменён прямым указанием пользователя; test-only commit только по разрешению пользователя |
| [05](../../../prompts/2026-09-30/http-api-and-session-middleware/05-app-lifespan.md) | App factory, settings, startup, reaper, health | T | Typed startup failure, ownership resources |
| [06](../../../prompts/2026-09-30/http-api-and-session-middleware/06-request-boundary.md) | Raw peer/proxy, route, Origin, body/query validation | 05 | Приоритет ошибок, security и 5-секундный receive |
| [07](../../../prompts/2026-09-30/http-api-and-session-middleware/07-projectors.md) | Birth projection, ChartDTO, ErrorDTO и schema | 05 | Exact whitelist, unknown-time offset, no I/O |
| [07a](../../../prompts/2026-09-30/http-api-and-session-middleware/07a-review-corrections-05-07.md) | Поправки после ревью 05–07 другой моделью | 05–07 | Явная передача каталога, safe errors, disconnect, POST query, reaper shutdown и границы импортов |
| [08](../../../prompts/2026-09-30/http-api-and-session-middleware/08-session-endpoints.md) | Cookie, bootstrap, current GET | 06–07a для route; 10 для rate; 13 для логов | Create/restore/read failure без Orchestrator; creation IP-limit подключён в 10, события 01/03 — в 13 |
| [09](../../../prompts/2026-09-30/http-api-and-session-middleware/09-place-endpoint.md) | Place search endpoint | 06–07 для route; 10 для rate | Нет session access; typed outcomes и safe 500; place IP-limit подключён в 10 |
| [10](../../../prompts/2026-09-30/http-api-and-session-middleware/10-admission.md) | Sliding limits и capacity; интеграция в готовые routes 08–09 | 06 и route-срезы 08–09 | Creation/place IP-limit, build reservation, доминирующий bucket §9.1; полный AS-HTTP-21 после обычного release в 11 |
| [11](../../../prompts/2026-09-30/http-api-and-session-middleware/11-build-endpoint.md) | Build endpoint, обычный owner terminal/release и mapping | 07–08, 10 | Один execute, release permit при terminal outcome, AS-HTTP-12 и последовательные build; cancellation в 12 |
| [12](../../../prompts/2026-09-30/http-api-and-session-middleware/12-deadline-shutdown.md) | Task registry всех принятых requests, disconnect, watchdog/shutdown | S0, 05, 10–11 | Build permit/leader ownership, все активные request/leaf и зависший active reaper до close, fail-fast restart |
| [13](../../../prompts/2026-09-30/http-api-and-session-middleware/13-integration-handoff.md) | Logs, Caddy/mkcert HTTPS path, OpenAPI и полная приёмка | 05–12 | AS-HTTP-01…29, один web process, ручной restart без supervisor, module boundaries, pytest, evidence |

S0 исследует cancellation до первого промта: перечислить точки отмены `execute`, shielded calculation leader, protected commit, SQLite и catalog executor futures; для каждой указать наблюдаемый terminal signal, владельца permit и допустимость `runtime.aclose()`. Для двух waiters одного leader каждый принятый запрос имеет свой permit. При отмене одного waiter проверить консервативный вариант: после завершения `execute` взять snapshot всех активных resolver leaders и удержать permit до их terminal outcome; unrelated leader вправе задержать release. Доказать, что snapshot не пропускает собственный leader при гонке отмены, и отдельно учесть protected commit и оставшиеся executor futures. `runtime.drain()` разрешён как кандидат на этот общий snapshot, но не выдаётся за точный per-request signal. Сверить existing cancelled-waiter test и перечислить недостающие доказательства для 04/12; в read-only S0 production и тестовый код не менять. Результат — записка в плане/журнале с безопасным release condition, тестовыми условиями и влиянием на оценку. Если нижнюю границу нельзя обеспечить без изменения публичного API или границ, оформить Development Finding и не объявлять Gate A пройденным. Не переносить решение в промт 12.

**Промежуточный read-only результат S0 (2026-09-30):** `ChartArtifactResolver._ensure_singleflight` защищает leader через `asyncio.shield`; `ApplicationRuntime.drain()` вызывает `ChartArtifactResolver.drain()`, который snapshot-ит все текущие `_inflight` tasks. Это позволяет консервативно ожидать общий расчёт без нового публичного API. Существующий `test_runtime_close_waits_for_cancelled_waiter_live_leader` доказывает этот путь только для одного отменённого waiter при shutdown. `ApplicationOrchestrator` уже удерживает `commit_task` при отмене и ждёт его terminal outcome. **Оставшийся gap:** `SqlitePlaceCatalog.lookup/search` и `_SqliteBackend.run` session persistence ожидают `run_in_executor` без удержания future при отмене; их native работа может пережить `execute`, а `runtime.drain()` её не видит. S0 рекомендует узкий internal cancellation seam: после отмены сохранить и дождаться отправленного executor future, затем повторно поднять `CancelledError`; при повторной отмене future остаётся учтённым до terminal outcome либо наступает process fail-fast. Публичные component signatures не меняются. До Gate A нужно согласовать этот технический способ и сформулировать для промтов 04/12 deterministic barrier tests: cancel во время catalog lookup и SQLite load, отдельный shared leader, protected commit, пять permits и шестой 503. Код и тесты в этом read-only проходе не менялись; работоспособность seam ещё не доказана исполняемым тестом, поэтому T-A2 и Gate A открыты.

G0 до тестов фиксирует test seam: публичная точка входа `exact_orb.http_api.app.create_app`; `tests/http_api/conftest.py` создаёт приложение с подменяемыми runtime/catalog factories и UTC clock, вручную запускает ASGI lifespan и использует HTTPS `httpx.AsyncClient`/`ASGITransport` с контролируемым raw `scope["client"]`. Для cookie cardinality тесты отключают cookie jar и передают сырые `Cookie` headers. Для rate windows, обоих deadline и reaper нужен один внедряемый monotonic scheduler с `now()` и ожидаемым до абсолютного срока `wait_until(deadline)`; fake scheduler вручную продвигает время и будит waiters. Production timer может опираться на event loop, но 5-секундный body receive, 30-секундный watchdog и 15-минутный reaper не должны обходить этот seam через `asyncio.wait_for`, `asyncio.sleep(900)` или неподменяемый framework timeout. Конкретные signatures фиксируются в [G0](http_api_and_session_middleware_g0.md); тесты не патчат event loop и не используют реальный `sleep`.

Импорт будущего app factory выполняется внутри фикстуры, поэтому отсутствие production-модуля даёт ожидаемый RED на setup, а не ошибку collection. Такой RED сам по себе недостаточен: к Gate T для каждого теста записываются AS, причина падения и промт, который сделает его зелёным; чистые unit-срезы XFF, admission windows и projector запускаются отдельно и не зависят от app factory. Contract tests содержат meaningful assertions и positive controls. Промт 05 реализует согласованные в G0 именованные точки инъекции без отдельного сервисного слоя; 01–04 не выбирают разные сигнатуры независимо.

До промта 01 G0 фиксирует BirthViewDTO golden и точку входа fixture; до промта 02 — ChartDTO golden/OpenAPI assertions. Публичные JSON-типы уже записаны в `http_api.md` §7.1/§7.2/AS-HTTP-28 с подтверждением пользователя: angle содержит `longitude`, `sign`, `degree`, `minute`; `from/to` — строковый ID опубликованной точки. `sign` — одно из 12 английских имён `Aries`…`Pisces` в регистре engine `ZODIAC_SIGNS`; допустимые ID — 16 points §7.2 плюс `asc`, `mc`, `vertex`, только если они реально опубликованы. Для каждой ссылки нужен `chart == "natal"`; другое значение или dangling ID даёт безопасный 500. `dsc/ic` не участвуют в аспектах: их знак получают сдвигом `sign_index` сохранённых `ZodiacPosition` asc/mc на шесть, `degree/minute` копируют без нового округления; долготу противоположного угла нормализуют из сохранённой долготы. Для cosmogram `angles=null`, а аспектные ID ссылаются только на опубликованные points. Исполняемые schema assertions ещё не написаны.

Gate A отделён от тестового Gate T: перед промтом 01 сверить §14 `http_api.md`, review Developer и Tester по Analysis, согласование DP-HTTP-01…06 Lead, точные DTO/OpenAPI schemas и diagrams, а также вывод S0 по отсутствию бесконечно занятого permit. Получен Tester review требований и тест-дизайна, **не** ещё не написанных тестов: вердикт «принять с доработками», четыре блокера T-A1…T-A4 ниже. Пользователь подтвердил решения и контракт FIND-HTTP-021 внесён в требования; это не является доказательством исправления cancellation seam или прохождения исполняемых проверок. FIND-HTTP-020 ждёт интеграции Lead-owned правок в `change/*`. Нельзя выдавать review тестов 01–04 после Gate A за review Analysis; при существенном контрактном или архитектурном вопросе вернуться на analysis/decision stage по Experiment 002.

Промты 01–04 создают тесты раньше production code по Experiment 002 §13.1. Они должны иметь реальные положительные контроли; отсутствие transport ожидаемо делает их неуспешными, пропуск/skip не считается доказательством. Первоначальный протокол предусматривал отдельный test-only commit и короткий review Tester до промта 05; пользователь отменил обязательный review и отдельным сообщением запросил коммит после 04a. Создание самого плана не разрешает commit, branch, push или PR.

Промты 05–12 проверяют зелёные тесты уже реализованной части своего среза; интеграционные тесты, зависящие от следующих промтов, перечисляются как ожидаемо красные. Routes bootstrap и places можно проверить после 08–09, но AS-HTTP-07/21 и их полная приёмка ждут подключения creation/place IP admission в 10. После каждого среза проверить уже реализованные пути, не переписывать contract tests ради прохождения. Промт 13 запускает целевые → связанные application/session/catalog и module-boundary → полный pytest. Платные и сетевые smoke-тесты не запускать.

## 5. Интеграционные инварианты

1. Route resolution → lifecycle → raw peer/proxy → Origin → POST media/body → schema → cookie → admission → component call. Ошибка с более высоким приоритетом не допускает побочных вызовов следующего слоя.
2. Cookie существует только как 43-символьный opaque ключ в __Host-exact_orb_session. Для duplicate cookie смотреть сырые Cookie headers; типовые parser convenience API могут скрыть дубликат.
3. Bootstrap/current напрямую вызывают ContextService; лишь current вызывает session_view. Places не читает cookie/session. Build создаёт один RunContext с run_id=request_id и один execute.
4. Публичные DTO собираются whitelist-проекцией. Unknown engine point не публикуется, dangling aspect даёт safe 500; corrupted StoredChart даёт chart_unavailable, структурно повреждённый aggregate — StateReadFailed.
5. Пять active build — process-local ceiling. Rate windows считаются injected monotonic clock; отказ capacity не расходует квоты. Каждый принятый build резервирует свой permit; shared single-flight leader может удерживать permit нескольких запросов. Нижняя граница release: permit не освобождается раньше завершения работы, к которой присоединился запрос, включая shared leader и protected commit. Для отменённого waiter выбран консервативный snapshot всех активных resolver leaders; unrelated leader может задержать release. Завершение сокета или `execute` само по себе недостаточно. 30-секундный deadline ограничивает жизнь здорового process; при его истечении admission закрывается и требуется fail-fast restart, а не фиктивное освобождение permit. Публичный oracle: при пяти занятых permits шестой build получает `503 BUILD_CAPACITY_EXHAUSTED` до завершения общего расчёта; после завершения удерживаемой работы и фактического release новый build проходит. Приватный счётчик только дополнительный lifecycle assertion.
6. После response deadline process сразу закрывает admission и оба health отвечают 503; старый process не объявляет permit свободным. External supervisor restart — dependency окружения; локальный deterministic harness проверяет его модель. Для AS-HTTP-02/19/22/26 restart означает два последовательно созданных приложения с разными process-local runtime/cache поверх **одного и того же временного SQLite-файла** сессий; resolver/cache/engine проверяются spy или управляемыми leaf, а fake ContextService не доказывает сохранение после restart. Без supervisor локальный runbook требует сохранить диагностические логи, принудительно завершить старый PID при незавершённом leaf, запустить один новый web process и сверить current chart до нового POST; самоисцеление после 503 не обещается.
7. Shutdown: закрыть admission → stop/wait reaper → дождаться всех принятых requests (bootstrap/current/places/build) и их отправленных SQLite/catalog executor futures → отменить допустимые pre-commit задачи → runtime.aclose() только при нулевой активности → внешний каталог последним. Build capacity permit принадлежит только build; обычный terminal `execute` освобождает его уже в 11, а 12 расширяет правило на cancellation/retained work. Если task/leaf не терминален после grace, применить fail-fast restart process по DP-HTTP-04, не блокируя event loop синхронным close executor.
8. INFO `http_message` фиксирует фактические send/receive на стрелках HTTP sequence; receive нет после исключения. Это transport event; существующий `application_message` принадлежит application layer и сохраняет своё имя. Payload, cookie, birth data и IP не добавлять в компактные INFO.

## 6. Gates, риски и приёмка плана

- **Перед промтом 01 — Gate A:** S0 доказал безопасный консервативный release и уточнил оценку Developer; G0 в [отдельной карточке](http_api_and_session_middleware_g0.md) зафиксировал app factory, HTTPS ASGI-клиент, raw cookie/peer, runtime/catalog injection, UTC clock, общий scheduler для body/watchdog/reaper и DTO/OpenAPI assertions. Утверждённые пользователем §9.3/AS-HTTP-24, §7.1/§9.1/FIND-HTTP-022, DTO и разделение AS-HTTP-17/19 внесены в требования и UI-приёмку, build sequence обновлена. Доказательство cancellation seam, условия §14 и интеграция документов в `change/*` остаются предметом фактической проверки; обязательный review Tester пользователь отменил. Техническая проверка §9.3/AS-HTTP-24 зависит от S0; DTO и admission от S0 не зависят.
- **Перед промтом 02:** golden tests используют уже утверждённые типы DTO; никаких новых форм публичного JSON в промте не выбирать.
- **Перед production code — Gate T:** после 01–04 и поправок 04a сверить контрактные тесты, positive controls и таблицу `test → AS/требование → ожидаемая причина RED → промт GREEN`. Одинаковое падение всех тестов на fixture setup не считается достаточным RED evidence. Пользователь отменил обязательный формальный Tester review; результаты независимого ревью другой моделью и фактические поправки фиксируются в §11. Test-only commit требует отдельного указания пользователя.
- **Перед acceptance DP-HTTP-04:** доказать тестами disconnect при живом shielded leader, blocked leaf future, protected commit, 30-секундный watchdog и shutdown без преждевременного close/permit release.
- **Перед Development PR:** целевые `python -m pytest tests/http_api -q`, связанные `python -m pytest tests/application tests/session tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py tests/test_module_boundaries.py -q`, затем `python -m pytest -q`; `git diff --check` и проверка новых файлов, ссылок и изменённых diagrams. Реальный список команд и результатов записать в журнале. PlantUML rendering не объявлять выполненным без запуска.
- **Локальный runbook в промте 13:** Caddy завершает HTTPS с сертификатом mkcert и передаёт XFF/XFP; Uvicorn запускается с выключенным встроенным proxy-header rewrite и ровно одним web process. Указать проверенную команду, установленную комбинацию версий FastAPI/uvicorn/httpx, проверку числа web process и health через internal route. При unhealthy без внешнего supervisor описать сохранение логов, принудительное завершение старого PID, запуск нового процесса и сверку current; не выдавать 503 за автоматически восстановимое состояние.
- **Перед public deployment:** общий proxy IP-limit для valid live-cookie reads, internal-only health, один web process, HTTPS и внешний supervisor с принудительным завершением старого процесса. M1-6 поставляет локальный config/runbook; production ACL/manifest остаются M1-12.

Статус каждой карточки при создании плана — «не начато». Готовность плана к review не означает готовность реализации или выполнение тестов. После завершения карточки фиксировать фактические файлы, команды, исходы и ограничения; историю промтов не переписывать.

## 7. Полученный Tester review Analysis и тест-дизайна

Tester проверил `http_api.md` в рабочем дереве, этот план и промты 01–04/12. Исполняемых `tests/http_api/` пока нет; это review Analysis для Gate A, **не** Gate T. Вердикт: «принять с доработками». Все AS-HTTP-01…29 распределены между промтами 01–04 без пропусков, но следующие блокеры не позволяют объявить Gate A закрытым:

| ID | Блокер и ответственный артефакт | Условие закрытия |
| --- | --- | --- |
| T-A1 | G0 / Developer: fake значение `monotonic` не управляет `asyncio.wait_for` и таймаутами event loop. | Один внедряемый `now()/wait_until(deadline)` scheduler управляет body receive 5 с, build watchdog 30 с и reaper 15 мин от завершения run; fake продвигается вручную; промты 04/05/06/12 проверяют путь без `sleep`/patch loop. |
| T-A2 | S0 + Analysis/Lead: shared single-flight leader и permit меняют наблюдаемую доступность шестого build; §9.3/AS-HTTP-24 теперь фиксируют нижнюю границу. | Контракт подтверждён пользователем и внесён. S0 ещё доказывает безопасность общего snapshot и удержание executor futures при отмене; Tester проверяет обновлённый сценарий до промтов 03/04/12. Точный release при unrelated leader не требуется. |
| T-A3 | Промты 03/04/12: внутренний счётчик permit сам по себе не проверяет публичное поведение. | При пяти занятых permits шестой build получает `503 BUILD_CAPACITY_EXHAUSTED`; после terminal release одного permit новый build проходит. Приватный счётчик лишь дополнительный. |
| T-A4 | Промты 01/03/04: fake context не доказывает restore после restart. | AS-HTTP-02/19/22/26 создают новое app/runtime поверх того же временного SQLite-файла, с пустым process-local cache; spies подтверждают отсутствие лишнего resolver/engine вызова. |

Дополнительное покрытие существующих требований распределяется до Gate T так:

| Требование / замечание Tester | Промт и проверяемый результат |
| --- | --- |
| §4.1 priority | 02/04: параметризованная попарная матрица `503 shutdown > 400 XFF > 403 Origin > 415 media/encoding > 408 body timeout или 413 size > 422 schema`, с позитивным контролем и отсутствием component/admission call при раннем отказе. |
| §4.4 Origin | 02: чужой Origin на `GET /charts/current` и `GET /places` не вызывает load/search; health обрабатывается без Origin gate. |
| §5 cookie | 01: raw `Set-Cookie` проверяет имя `__Host-`, `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=604800`, отсутствие `Domain` и 43 символа значения; duplicate проверяется сырыми Cookie headers без cookie jar. |
| §4.2–4.3 POST | 02: запрет любого `Content-Encoding`, charset absent/utf-8 против другого, `place_id` на 0/1/128/129 code points и `request.<name>` для лишнего поля. |
| §6.2 current projector | 01: unexpected projector failure даёт safe 500 с renew cookie, без подмены на `chart_unavailable`; успешный current рядом. |
| §12 observability | 04: ровно одно terminal event, WARNING для 5xx/timeout/cancellation, отсутствие sentinel cookie/IP/date/query во всех INFO записях и порядок фактических send/receive. |
| §9/§10/§6.4 прочее | 03: малые лимиты через тестовую инъекцию immutable limiter policy плюс отдельная проверка утверждённых production defaults, eviction неактивных buckets, exact `already_applied` body; 04: IPv4-mapped IPv6 и IPv4 имеют один bucket. Тестовая policy не становится поддерживаемой конфигурацией стенда без решения DP-HTTP-02. |
| AS-HTTP-17/19 client-only фразы | Functional Analyst оставляет в HTTP серверный oracle: свежий load N+1 для позднего POST A; для timeout — `retryable=false`, `Retry-After: 5`, отсутствие `Set-Cookie`, ровно один `execute` в одном запросе и восстановление через новый app/runtime на той же SQLite. Поведение вкладки и запрет автоматического второго POST передаются ссылкой в приёмку UI M1-7; действующие UI rules находятся в `docs/ui_ux/requirements.md` §5 и `decisions.md` §1.1. |

Новый golden `ChartDTO` в `tests/http_api/` разрешён после утверждения точных DTO-типов; существующие golden-файлы не менять. Для RED 01–04 составить таблицу тестов с AS/требованием, ожидаемой причиной падения и соответствующим implementation-промтом; тесты чистых unit-срезов запускать независимо от отсутствующей app factory. Риск календарного Testing 1 день сообщить Lead вместе с предварительной оценкой Developer минимум 2 дня; само review срок не меняет.

FIND-HTTP-022 закрывает ещё два недоопределённых публичных правила до RED-тестов:
при одновременных отказах build действует доминирующий rate bucket до capacity
(§9.1/AS-HTTP-21); `BirthViewDTO` берёт дату/время/id из `birth_input`, имя,
timezone и offset из `birth_resolved`, скрывает noon anchor и проверяется
golden для `chart_ready`/`chart_unavailable` (§7.1/AS-HTTP-28). G0 фиксирует
тестовый шов, а Tester проверяет его до закрытия Gate A. Исполняемые тесты
и implementation evidence по этим правилам ещё отсутствуют.

## 8. Development Finding для повторной Analysis

**FIND-HTTP-021 (Development Finding).** Обнаружил Developer при подготовке Gate A. Тип: недоопределённый публичный контракт и проверяемость acceptance. Затронуты `http_api.md` §7.2, §9.3, AS-HTTP-17/19/24/28, HTTP build sequence, промты 02–04/07/12. Статус: **контракт подтверждён пользователем и внесён в requirements/UI/diagram; техническое evidence S0 и проверка Tester остаются**.

Принятые формулировки и технические границы:

1. **§9.3 и AS-HTTP-24.** Каждый принятый build удерживает собственный permit. При отмене ожидающего запроса permit не освобождается раньше завершения работы, к которой запрос присоединился: его `execute`, общего single-flight расчёта и protected commit, если он начат. Для M1-6 допустимо консервативно ждать завершения всех resolver leaders, активных на момент отмены; unrelated leader может задержать release. При пяти удерживаемых permits шестой запрос получает `503 BUILD_CAPACITY_EXHAUSTED`, пока общий расчёт жив. 30-секундный deadline завершает работу **здорового процесса**: он закрывает admission, отвечает 503 на health и требует перезапуска supervisor; старый процесс не заявляет, что permit освободился. S0 должен подтвердить захват joined leader общим snapshot; protected commit и surviving SQLite/catalog executor futures удерживаются отдельно и не входят в `runtime.drain()`. Нельзя называть 30 секунд верхней границей фактического release или обещать restart без supervisor.
2. **§7.2 и AS-HTTP-28.** `angles` для natal содержит `asc/mc/vertex/dsc/ic`; значение каждого — объект с числовым `longitude`, строковым `sign`, целыми `degree` и `minute`. `sign` — ровно одно из `Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces`. Для cosmogram `angles=null`. `aspects[].from/to` — строковые ID только реально опубликованных 16 points §7.2 и `asc/mc/vertex`; у каждой исходной `AspectPointRef` обязательно `chart="natal"`. `dsc/ic` не являются допустимыми концами аспекта. Другая chart ownership или dangling ID — safe 500. Знаки `dsc/ic` сдвигаются на шесть от сохранённых `ZodiacPosition.sign_index` asc/mc, `degree/minute` копируются без нового округления; противоположная долгота нормализуется из сохранённой долготы.
3. **AS-HTTP-17/19 и UI M1-7.** В HTTP AS-17 проверять, что поздний явный POST вкладки A делает fresh load N+1 и использует эту версию как CAS expected; отображаемый вкладкой N не поступает в серверный CAS. В HTTP AS-19 проверять точный ответ `STATE_COMMIT_FAILED`/`BUILD_TIMEOUT`, один `execute` на принятый POST и восстановление через новый app/runtime на том же SQLite-файле. Проверки того, когда вкладка обновит экран и что frontend не выполнит автоматический повтор POST, передать ссылкой в приёмку UI M1-7; поведенческая основа уже находится в `docs/ui_ux/requirements.md` §5 и `decisions.md` §1.1. Разделение доказательств не меняет существующее поведение.

Пункты 2 и 3 записаны в публичном контракте независимо от S0. Пункт 1 утверждён как нижняя граница, а техническое доказательство leaf/snapshot ещё зависит от S0. Единый Gate A остаётся открытым до проверки Tester, технического evidence и интеграции документов в `change/*`; эта зависимость не блокирует подготовку независимых частей G0.

## 9. FIND-HTTP-022: admission и BirthViewDTO

**Статус:** публичные правила подтверждены пользователем и внесены в
`http_api.md` §7.1/§9.1, AS-HTTP-21/28; Tester review G0 и исполняемое evidence
ещё требуются. При одновременном исчерпании build rate/capacity transport
возвращает 429 по bucket с наиболее поздним моментом допуска; tie-breaker —
session перед IP, сутки перед часом. Ни отказ 429, ни 503 capacity не
расходует квоту. `BirthViewDTO` публикует `utc_offset_seconds=null` при
неизвестном времени, не раскрывает noon anchor; дату/время/id берёт из
`birth_input`, resolved имя/timezone из `birth_resolved`. Эти решения не зависят
от S0. G0 и промты 01/03/07/10 задают проверки до реализации.

## 10. Промт 01 — test-only RED evidence (2026-10-01)

Добавлены `tests/http_api/conftest.py`, `test_session.py` и golden
`golden/session_view.json`. Production-код HTTP не менялся. Прямое поручение
пользователя выполнить промт 01 позволило подготовить тесты при открытом Gate A;
формальный Gate A, G0 review и Gate T этим не объявляются закрытыми.

| Тест / набор | AS и требование | Ожидаемая причина RED сейчас | GREEN-промт |
| --- | --- | --- | --- |
| `test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation` | 01; §5, §6.1–6.2 | Нет app factory/routes | 05, 08, 10 |
| `test_bootstrap_logs_cookie_replacement_after_success` | 01; §12 | Нет app; отдельное событие после успешного create | 13 |
| `test_restart_uses_same_sqlite_file_with_new_runtime_and_empty_cache` | 02; §6.1–6.2, ADR-0041 | Нет app factory/routes; SQLite harness и два отдельных runtime готовы | 05, 07–08 |
| `test_current_projects_stale_unavailable_or_empty_without_mutation` | 03; §6.2 | Нет app/current projector | 07–08 |
| `test_unavailable_current_emits_error_event` | 03; §12 | Нет app; отдельное ERROR-событие при unavailable | 13 |
| `test_structural_sqlite_chart_corruption_is_503_not_unavailable` | 03; §6.2 | Нет app/current mapping; реальный SQLite повреждается удалением child row | 05, 08 |
| `test_absent_current_clears_cookie_and_bootstrap_replaces_it` | 04; §5, §6.1–6.2 | Нет cookie/current/bootstrap routes | 06, 08 |
| `test_state_read_failure_preserves_cookie_and_never_creates_session` | 04; §5, §6.1–6.2 | Нет typed error mapping/routes | 08 |
| `test_absent_cookie_is_cleared_even_when_bootstrap_creation_fails` | 04; §5, §6.1 | Нет creation route/admission; старую cookie требуется погасить при 429/503 | 08, 10 |
| `test_missing_invalid_or_duplicate_cookie_requires_session_for_current` | 05; §4.1, §5 | Нет raw cookie validation/current route | 06, 08 |
| `test_duplicate_raw_cookie_is_replaced_by_bootstrap_without_loading_it`, `test_invalid_cookie_bootstrap_creates_fresh_id_without_load` | 05; §4.1, §5 | Нет raw cookie validation/bootstrap route | 06, 08 |
| `test_live_bootstrap_does_not_project_unavailable_chart` | 01, 03; §6.1–6.2 | Нет bootstrap/current routes; bootstrap должен возвращать только liveness/version | 08 |
| `test_three_id_conflicts_stop_without_foreign_load_or_fourth_id`, `test_create_storage_failure_does_not_issue_cookie_and_success_is_control` | 06; §6.1 | Нет insert-only creation/retry mapping | 08 |
| `test_creation_rolling_hour_limit_restore_and_exact_expiry_boundary` | 07; §6.1, §9.1 | Нет create limiter; monotonic boundary задаётся вручную | 10 |
| `test_collision_attempts_consume_one_creation_quota_for_http_request` | 06–07; §6.1, §9.1 | Нет retry/create limiter; две collision внутри 300-го HTTP-запроса не должны тратить отдельные quota | 08, 10 |
| `test_session_view_birth_golden_exact_whitelist` | 28; §7.1 | Нет чистой birth projection и HTTP DTO; ChartDTO полностью фиксируется промтом 02 | 07–08; ChartDTO — 02/07 |
| `test_invalid_saved_birth_projection_is_safe_500_with_renew_and_success_control` | 28; §6.2, §7.1 | Нет projector и safe 500 mapping | 07–08 |

Независимые `test_chart_fixture_has_distinct_ready_and_unavailable_pure_views`,
`test_scheduler_is_manually_advanced_without_wall_time` и
`test_sqlite_restart_harness_preserves_chart_without_http` подтверждают
входные snapshots, единый управляемый scheduler и реальное сохранение карты
через два последовательных SQLite runtime без HTTP.
Все app-зависимые тесты импортируют `create_app` внутри fixture; одинаковый
`ModuleNotFoundError` сейчас является только признаком отсутствующего transport,
а не доказательством HTTP-поведения. Тесты содержат отдельные позитивные
контроли и перечисленные выше наблюдаемые assertions для будущего GREEN.

Фактические проверки на 2026-10-01:

| Команда | Результат |
| --- | --- |
| `python -m pytest tests/http_api/test_session.py::test_chart_fixture_has_distinct_ready_and_unavailable_pure_views tests/http_api/test_session.py::test_scheduler_is_manually_advanced_without_wall_time tests/http_api/test_session.py::test_sqlite_restart_harness_preserves_chart_without_http -q -p no:cacheprovider` | 3 passed |
| `python -m pytest tests/http_api/test_session.py -q --tb=no -p no:cacheprovider` | 3 passed, 28 failed (ожидаемый RED: transport package отсутствует; отдельный запуск с `--tb=line` показал `ModuleNotFoundError: No module named 'exact_orb.http_api'` у app-зависимых тестов) |
| `python -m compileall -q tests/http_api` | exit 0 |
| `git diff --check` | exit 0; Git предупредил о штатной нормализации LF → CRLF в working copy плана |

Полный `pytest`, связанные component suites и PlantUML rendering на этом
test-only RED-срезе не запускались. Tester review исполняемых тестов не проведён.

## 11. Промт 04a — поправки после ревью другой моделью (2026-10-01)

Пользователь передал замечания к исполняемым тестам 01–04, подготовленные
**другой моделью**. Developer сверил их с текущим кодом и `http_api.md`, затем
выполнил [поправочный промт 04a](../../../prompts/2026-09-30/http-api-and-session-middleware/04a-review-corrections.md).
Это не формальное Tester approval; обязательный Tester review пользователь
ранее отменил.

| Область | Исправление и проверяемое требование |
| --- | --- |
| AS-HTTP-16/18, §7.1 | Разные `place_id` дают разные resolved-намерения в real SQLite CAS; build сравнивает полный `ChartDTO` с projector и current GET. Пример §6.4 помечен сокращённым |
| AS-HTTP-05/24 | Повторяющиеся Cookie передаются парным headers; добавлен invalid/duplicate build с позитивным контролем; для retained permit используется работа, переживающая отмену, без требования финального ответа после disconnect |
| G0, AS-HTTP-25/26 | Общие девять настроек во всех app fixtures, исходные фабрики без аргументов; GET shutdown тесты проверяют ожидание futures без неподтверждённого запрета ответа после disconnect; начальный срок reaper уточнён |
| AS-HTTP-01/03/21 | Логовые проверки вынесены в отдельные тесты; отказ на `t=3` не должен сдвигать допуск на `t=7`; два конкурентных POST борются за один слот; renew/clear cookie проверяются по значению и атрибутам |
| AS-HTTP-09/28 и ошибки | Повторный `query` уточнён как `QUERY_REQUIRED`; nonempty `excluded_aspects` проверяются на полном валидном артефакте без изменения golden; projector/startup тесты ждут типизированные исключения; helpers вынесены из тест-модулей |

`active_bucket_count` оставлен только как вспомогательная проверка очистки
внутреннего хранилища, не как публичный G0 API. Текстовый формат логов и имя
логгера также не закреплены в G0. Прямой dev dependency на `httpx` добавлен.
На момент 04a трактовка регистра в `charset=UTF-8` оставалась отдельным
вопросом публичной грамматики §4.2; решение и проверка записаны в §13.

| Команда | Фактический результат |
| --- | --- |
| `python -m compileall -q tests/http_api` | exit 0 |
| `python -m pytest tests/http_api/test_session.py::test_chart_fixture_has_distinct_ready_and_unavailable_pure_views tests/http_api/test_session.py::test_scheduler_is_manually_advanced_without_wall_time tests/http_api/test_session.py::test_sqlite_restart_harness_preserves_chart_without_http tests/http_api/test_build_admission.py::test_window_oracle_is_inclusive_and_selects_latest_bucket_with_ties tests/http_api/test_build_admission.py::test_recovery_result_samples_are_real_typed_application_models tests/http_api/test_build_admission.py::test_real_sqlite_orchestrator_fixture_commits_without_http tests/http_api/test_lifecycle.py::test_scheduler_control_has_exact_deadline_and_no_wall_clock -q -p no:cacheprovider` | 7 passed |
| `python -m pytest tests/http_api -q --tb=no -p no:cacheprovider` | 11 passed, 182 failed: ожидаемый RED до появления `exact_orb.http_api` |
| `$lines = python -m pytest tests/http_api -q --tb=line -p no:cacheprovider 2>&1; $lines \| Select-String '^E   ' \| Group-Object -Property Line \| Select-Object Count,Name` | 182 раза `ModuleNotFoundError: No module named 'exact_orb.http_api'`, других типов ошибок нет |
| `git diff --check` | exit 0; Git сообщил только о нормализации LF → CRLF в working copy |

Независимый запуск `cosmogram_sample()` и
`cosmogram_with_excluded_aspects()` подтвердил соответственно 0 и 20
исключённых аспектов в валидных артефактах. Тесты app-поведения останутся
непроверенными до реализации HTTP transport. Полный `pytest`, связанные
component suites и PlantUML rendering в промте 04a не запускались.

## 12. Промт 05 — app lifespan, reaper и health (2026-10-01)

Создан `src/exact_orb/http_api/app.py` с согласованной G0 точкой
`create_app(settings, runtime_factory, catalog_factory, utc_clock, scheduler,
limiter_policy=None)`. Настройки и тестовая limiter policy проверяются до
открытия ресурсов; async/sync фабрики открывают сначала внешний каталог, затем
один process-local runtime. Lifespan закрывает runtime и каталог в обратном
порядке также при ошибке startup. Health читает только lifecycle phase;
readiness переходит в 503 с начала shutdown, live — при unhealthy. Reaper
ожидает абсолютный monotonic deadline через внедрённый scheduler, планирует
новый запуск от завершения предыдущего, переживает ошибки run и удерживает
ресурсы до завершения активного run при shutdown. HTTPS origin с wildcard или
пробелом отвергается до открытия ресурсов. Добавлены прямые зависимости
FastAPI и uvicorn; `httpx` уже был объявлен как dev dependency в 04a.

Настройки и lifespan помещены в `app.py` вместе с app factory: в этом срезе
они не образуют отдельный сервисный слой. Для детерминированного shutdown
test fixture ожидает явный lifecycle signal перед проверкой 503. Добавлены
узкие тесты health-состояний и async-фабрик. Бизнес-маршруты, request boundary,
projector и admission остаются задачами промтов 06–12; общий тест health +
`/places` поэтому ещё RED, хотя health-only срез GREEN.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_lifecycle.py -q -k "health_tracks_startup_shutdown or async_runtime_factory_reuses_open_catalog or reaper_waits_from_completion or invalid_settings_fail_before_any_resource_opens or runtime_startup_failure_closes_previously_opened_catalog or missing_calculation_version_fails_startup_and_closes_resources or catalog_startup_failure_never_opens_runtime or invalid_admission_limit_fails_before_resources_open" -p no:cacheprovider` | 17 passed, 37 deselected после уточнения HTTPS origin |
| `python -m pytest tests/application/test_application_bootstrap.py tests/application/test_application_bootstrap_integration.py tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 123 passed вне sandbox. Внутри sandbox 39 setup errors из-за `PermissionError` временного каталога pytest; попытка `--basetemp` в рабочем дереве дала ту же ошибку доступа |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2681 passed, 170 failed: 169 ожидаемых RED будущих HTTP-срезов и один `test_tzdata_version_mismatch_warns_once_and_allows_open` |
| `python -m pytest -q --tb=short -p no:cacheprovider --ignore=tests/http_api` | 2655 passed, 1 failed: тот же tzdata test; logger в worker пишет в закрытый stream, поэтому `caplog` видит 0 записей. Ошибка воспроизводится без HTTP-тестов |
| `python -m pytest tests/test_place_catalog_sqlite.py::test_tzdata_version_mismatch_warns_once_and_allows_open -q --tb=short -p no:cacheprovider` | 1 passed отдельно |
| `python -m compileall -q src/exact_orb/http_api tests/http_api/test_lifecycle.py`; `git diff --check` | exit 0; Git предупредил о нормализации LF → CRLF в working copy теста |

Проверки с `tmp_path` выполнены вне ограниченной песочницы после ошибки её
доступа к каталогу pytest. Сетевые/платные smoke-тесты, PlantUML rendering и
реальный HTTPS listener не запускались. Полный прогон выполнен до последней
узкой правки, разрешающей пустой Origin allowlist, дополнительной health
assertion и строгой проверки HTTPS origin; после них повторены целевые 17
тестов и diff check. На момент завершения промта 05 коммит, push и PR не
создавались; коммит готовится по отдельному запросу пользователя.

## 13. Промт 06 — raw request boundary и trusted proxy (2026-10-01)

В `proxy.py` добавлена проверка исходного ASGI peer и сырых XFF/XFP только
для trusted peer: дубликаты, malformed chain и отсутствие untrusted hop дают
`400`, а поля от untrusted peer игнорируются. IPv4, IPv6 и mapped IPv6
нормализуются до ключа лимитера. В `request_boundary.py` порядок проверок
совпадает с §4.1: lifecycle → IP/proxy → Origin → POST media/encoding →
body deadline/size → JSON/query schema → raw Cookie. Body deadline
отсчитывается от первого ASGI body event общим scheduler `now()/wait_until`;
отказы имеют safe transport fields, no-store и server `X-Request-ID`.
`app.py` создаёт общий boundary, но production business routes до промтов
08/09/11 не регистрируются. Проверки идут через test-only `/_probe/*`
routes, которые фиксируют отсутствие component call при раннем отказе.

По прямому уточнению пользователя непустой trusted CIDR allowlist сам
включает proxy mode; отдельного флага нет. Пустой список означает direct
mode. Также `charset=UTF-8` принимается без учёта регистра. Оба уточнения
внесены в §4.2/§10 `http_api.md`; отдельный ADR не требуется, поскольку они
конкретизируют уже принятые правила без смены решения. Диаграммы не
изображают регистр charset или переключатель proxy mode, поэтому не менялись.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_request_boundary.py -q -p no:cacheprovider` | 42 passed, включая nested JSON regression после последней правки |
| `python -m pytest tests/http_api/test_lifecycle.py -q -k "health_tracks_startup_shutdown or async_runtime_factory_reuses_open_catalog or reaper_waits_from_completion or invalid_settings_fail_before_any_resource_opens or runtime_startup_failure_closes_previously_opened_catalog or missing_calculation_version_fails_startup_and_closes_resources or catalog_startup_failure_never_opens_runtime or invalid_admission_limit_fails_before_resources_open" -p no:cacheprovider` | 17 passed, 37 deselected до последней правки JSON parser |
| `python -m pytest tests/test_module_boundaries.py -q -p no:cacheprovider` | 45 passed до последней правки JSON parser |
| `python -m pytest tests/http_api -q --tb=no -p no:cacheprovider` | 69 passed, 169 failed до последнего nested JSON regression; ожидаемый RED для будущих business routes/projectors/admission/task registry/logging |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2725 passed, 170 failed после последней правки: 169 ожидаемых HTTP RED и один `test_tzdata_version_mismatch_warns_once_and_allows_open` |
| `python -m pytest tests/test_place_catalog_sqlite.py::test_tzdata_version_mismatch_warns_once_and_allows_open -q --tb=short -p no:cacheprovider` | 1 passed отдельно; в полном прогоне остаётся прежний конфликт logger/caplog, описанный в §12 |
| `python -m compileall -q src/exact_orb/http_api tests/http_api/test_request_boundary.py`; `git diff --check` | exit 0; Git предупредил только о нормализации LF → CRLF в working copy |

Полная таблица 404/405/Allow для production routes, build admission и
component mapping станет проверяемой после промтов 08/09/11; projector DTO —
после 07, журнальные события — после 13. Поддерживаемый HTTPS launch path
с отключённым встроенным Uvicorn proxy-header rewrite остаётся в промте 13,
где расположен runbook. Тесты с `tmp_path` выполнены вне sandbox из-за
воспроизводимого `PermissionError` внутри него. Сетевые/платные smoke-тесты,
PlantUML rendering и реальный HTTPS listener не запускались. Коммит, push и
PR этим промтом не разрешены.

## 14. Промт 07 — чистая birth projection и публичные DTO (2026-10-01)

`application/session_view.py` дополнен неизменяемой `SessionBirthView` из
`birth_input` и `birth_resolved` одного `SessionSnapshot`. Она содержит
сохранённые дату, время, place ID, имя места, timezone, offset, флаг
неизвестного времени и порядок warning source/code без внутреннего message.
Проверка StoredChart, empty/ready/unavailable, stale и отсутствие I/O
сохранены. Старые поля application view оставлены, поскольку уже входят в
используемый компонентный результат.

В `http_api/dto.py` созданы типизированные формы §7 с запретом лишних полей;
`projectors.py` строит их явным whitelist. Chart projection фиксирует порядок
16 point ID, сортировку домов и сохранённый порядок аспектов, не публикует
unknown engine fields/points и excluded aspects. Aspect endpoint обязан
ссылаться на опубликованный point или допустимый natal angle; чужой chart,
`dsc/ic` и dangling ID дают `ChartProjectionError`. `dsc/ic` строятся из
сохранённых asc/mc longitude и sign_index с копированием degree/minute.
Birth projection скрывает noon anchor, offset неизвестного времени, raw warning
message и все warning codes вне allowlist; рассинхронизация time_unknown и
точности времени даёт `BirthProjectionError`. Эти типизированные ошибки
предназначены для safe 500 с renew cookie в маршруте 08. Общий request
boundary теперь сериализует ранние transport-отказы через `ErrorDTO`.

Контракт §7 и HTTP sequence 004 уже задают эти правила, поэтому requirements,
ADR и диаграммы в этом промте не менялись. Четыре HTTP golden-теста
`GET /charts/current` остаются RED до маршрута 08; тот же DTO проверен
четырьмя pure golden-тестами без transport.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_request_boundary.py tests/http_api/test_projectors.py tests/application/test_session_view.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 132 passed после добавления real Snapshot regression, до финального ErrorDTO test |
| `python -m pytest tests/application/test_session_view.py tests/application/test_stored_chart_build.py tests/http_api/test_projectors.py tests/http_api/test_request_boundary.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 141 passed после всех code/test правок |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2750 passed, 160 failed: 159 ожидаемых RED будущих HTTP routes/admission/lifecycle/logging и один `test_tzdata_version_mismatch_warns_once_and_allows_open` |
| `python -m pytest tests/test_place_catalog_sqlite.py::test_tzdata_version_mismatch_warns_once_and_allows_open -q --tb=short -p no:cacheprovider` | 1 passed отдельно |
| `python -m compileall -q src/exact_orb/application/session_view.py src/exact_orb/http_api tests/application/test_session_view.py tests/http_api/test_projectors.py`; `git diff --check` | exit 0; Git предупредил только о нормализации LF → CRLF в working copy |

Полный pytest запущен вне sandbox: внутри него `tmp_path` ранее давал
`PermissionError`. Отдельный tzdata-тест в промте 06 прошёл, а при полном
прогоне по-прежнему конфликтует с logger/caplog (§12). Сетевые/платные smoke-тесты и
PlantUML rendering не запускались. Коммит, push и PR не создавались.

## 15. Уточнение G0 после независимого ревью промтов 05–07 (2026-10-01)

Другая модель указала, что открытый HTTP lifespan каталог не передаётся
`runtime_factory()` явно. Пользователь выбрал вариант A: после
`catalog_factory()` lifespan вызывает `runtime_factory(catalog)` с тем же
экземпляром. Карточка G0 и тесты композиции обновлены. В частности,
`test_async_runtime_factory_reuses_open_catalog_and_closes_in_reverse_order`
проверяет identity аргумента, а тест двух waiters теперь использует один
каталог и для реального runtime, и для приложения. Владение и порядок
закрытия ресурсов остаются у lifespan; `build_application_runtime(places=...)`
сохраняет существующий компонентный API. Исторический промт 04a не менялся.

Остальные замечания этого ревью рассмотрены отдельно перед промтом 08:
общие JSON-обработчики 404/405/500, отдельный сигнал disconnect и проверка
query у POST относятся к transport boundary; сбой scheduler/reaper и
ограниченное shutdown ожидание требуют согласования с §11.1–11.3 и промтом 12.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_lifecycle.py -q -k "health_tracks_startup_shutdown or async_runtime_factory_reuses_open_catalog or reaper_waits_from_completion or invalid_settings_fail_before_any_resource_opens or runtime_startup_failure_closes_previously_opened_catalog or missing_calculation_version_fails_startup_and_closes_resources or catalog_startup_failure_never_opens_runtime or invalid_admission_limit_fails_before_resources_open" --tb=short -p no:cacheprovider` | 17 passed, 37 deselected |
| `python -m pytest tests/http_api/test_request_boundary.py -q --tb=short -p no:cacheprovider` | 42 passed |
| `python -m pytest tests/http_api/test_request_boundary.py tests/http_api/test_lifecycle.py -q --tb=short -p no:cacheprovider` | 60 passed, 36 failed: lifecycle-тесты будущих HTTP routes/admission/shutdown/logging остаются RED |

## 16. Промт 07a — поправки после ревью другой моделью (2026-10-01)

Независимое ревью промтов 05–07 другой моделью передано пользователем.
Пользователь выбрал вариант A передачи каталога; поправочный
[промт 07a](../../../prompts/2026-09-30/http-api-and-session-middleware/07a-review-corrections-05-07.md)
сохранён отдельно от исторических промтов 05–07 и исполнен перед 08.

Общий app handler теперь выдаёт safe `ErrorDTO` и обязательные headers для
404/405/500, сохраняет `Allow` у 405, отображает framework
`RequestValidationError` в safe 422. Disconnect во время body receive имеет
отдельный `ClientDisconnected`, не подделывает task cancellation и завершает
ASGI вызов без ответа. POST с непустым query отклоняется до cookie/admission.
`error_response` гасит invalid/duplicate required-session cookie со всеми
`__Host-` атрибутами. Ошибка reaper task наблюдается и логируется, но больше
не прерывает штатную очистку при shutdown; после освобождения ресурсов
lifespan переходит в `STOPPED` и пишет terminal event. AST-тест закрепил
прямые границы импортов HTTP/application. Docstring `SessionBirthView`
уточняет технический noon-anchor offset неизвестного времени.

Непосредственные маршруты 08–11 обязаны принимать `Request`, использовать
подготовленное тело без повторного framework parse и сериализовать `ErrorDTO`
через `JSONResponse(dto.model_dump(mode="json"))`; transport handler служит
страховкой от framework validation. Новые business routes здесь не создавались.

**Открыто для Analysis:** §11.1 описывает live 503 после fail-fast watchdog,
а текущий callback также переводит процесс в unhealthy при падении scheduler
reaper. Политика health в 07a не менялась. Зависший active `reap_expired`
сейчас может задержать shutdown до завершения leaf; согласованный grace и
fail-fast для reaper необходимо реализовать в промте 12, без отдельного
произвольного timeout. Код/Retry-After для business-запроса в unhealthy,
обязательность отсутствующего `birth_time` и отсутствие ASGI peer не
переопределялись. Одиночный flaky tzdata logging test остаётся известным
ограничением до итогового промта 13.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_request_boundary.py tests/http_api/test_projectors.py tests/application/test_session_view.py tests/application/test_stored_chart_build.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 147 passed |
| `python -m pytest tests/http_api/test_lifecycle.py -q -k "health_tracks_startup_shutdown or async_runtime_factory_reuses_open_catalog or reaper_waits_from_completion or reaper_scheduler_failure_does_not_abort_shutdown_cleanup or invalid_settings_fail_before_any_resource_opens or runtime_startup_failure_closes_previously_opened_catalog or missing_calculation_version_fails_startup_and_closes_resources or catalog_startup_failure_never_opens_runtime or invalid_admission_limit_fails_before_resources_open" --tb=short -p no:cacheprovider` | 18 passed, 37 deselected |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2757 passed, 160 failed: 159 ожидаемых RED следующих HTTP routes/admission/lifecycle/logging, один `test_tzdata_version_mismatch_warns_once_and_allows_open` |
| `python -m pytest tests/http_api/test_request_boundary.py::test_post_query_is_rejected_before_cookie_and_positive_body_is_accepted -q --tb=short -p no:cacheprovider` | 1 passed после усиления проверки приоритета query перед cookie |
| `git diff --check`; проверка ссылки плана на промт 07a через `Test-Path` | exit 0; `True` (Git сообщил только о будущей LF → CRLF нормализации working copy) |

Сетевые/платные smoke-тесты и PlantUML rendering не запускались. Коммит,
push и PR не создавались.

## 17. Исполнение промта 08 — cookie, bootstrap, current (2026-10-01)

Реализованы `POST /session/bootstrap` и `GET /charts/current`. Cookie создаётся
из 32 случайных байтов и выдаётся/гасится с атрибутами §5. Bootstrap вызывает
только `ContextService.create/load`, ограничивает collision retries тремя и
возвращает `SessionBootstrapDTO`; current вызывает `ContextService.load`,
чистый `session_view` и явный DTO projector. `SessionAbsent`,
`StateReadFailed`, create failure и unexpected projection failure отображаются
с действиями над cookie из §5–8. Тестовый natal snapshot дополнен валидными
углами/домами: прежний generic artifact имел пустые `angles` и не мог быть
публичной `chart_ready` картой по §7.2. Проверка отказа create с invalid и
duplicate cookie добавлена с успешным контролем.

Перед исполнением пользователь передал дополнительное замечание по 500 после
`prepare`: новый ID в общем обработчике нарушал корреляцию ответа и
`http_unhandled_exception`. `prepare` теперь записывает ID в `request.state`,
а обработчики ошибок берут его оттуда; до `prepare` они создают и сохраняют
один новый ID. Регрессии проверяют равенство ID в ответе и журнале после
позднего исключения и ошибки проекции current. Для 500 тестовый
`httpx.ASGITransport` использует `raise_app_exceptions=False`, поскольку
Starlette ServerErrorMiddleware повторно поднимает исключение после отправки
ответа. Это учтено при исполнении 08, исторический текст промта не менялся.

Creation admission и события `http_cookie_replaced`/`chart_unavailable`
оставлены промтам 10 и 13 по их назначению. Пять соответствующих проверок
`test_session.py` остаются RED: `test_bootstrap_logs_cookie_replacement_after_success`,
`test_unavailable_current_emits_error_event`,
`test_absent_cookie_is_cleared_even_when_bootstrap_creation_fails[rate]`,
`test_creation_rolling_hour_limit_restore_and_exact_expiry_boundary`,
`test_collision_attempts_consume_one_creation_quota_for_http_request`.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_session.py -q --tb=short -p no:cacheprovider` | 30 passed, 5 failed; все пять отказов перечислены выше |
| `python -m pytest tests/http_api/test_session.py -q -k "not bootstrap_logs_cookie_replacement_after_success and not unavailable_current_emits_error_event and not creation_rolling_hour_limit_restore_and_exact_expiry_boundary and not collision_attempts_consume_one_creation_quota_for_http_request and not absent_cookie_is_cleared_even_when_bootstrap_creation_fails" --tb=short -p no:cacheprovider` | 29 passed, 6 deselected после всех правок |
| `python -m pytest tests/http_api/test_session.py tests/http_api/test_request_boundary.py tests/http_api/test_projectors.py tests/application/test_session_view.py tests/application/test_stored_chart_build.py tests/test_module_boundaries.py -q -k "not bootstrap_logs_cookie_replacement_after_success and not unavailable_current_emits_error_event and not creation_rolling_hour_limit_restore_and_exact_expiry_boundary and not collision_attempts_consume_one_creation_quota_for_http_request and not absent_cookie_is_cleared_even_when_bootstrap_creation_fails" --tb=short -p no:cacheprovider` | 177 passed, 6 deselected при проверке перед коммитом |
| `python -m pytest tests/http_api/test_request_boundary.py -q --tb=short -p no:cacheprovider` | 48 passed |
| `python -m pytest tests/http_api/test_place_dto.py -q --tb=short -p no:cacheprovider` | 15 passed, 52 failed: отсутствуют routes 09/11 и их mapping/admission |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2805 passed, 115 failed: ожидаемые RED будущих HTTP-срезов, пять проверок 08 и известный `test_tzdata_version_mismatch_warns_once_and_allows_open` |
| `python -m pytest tests/test_place_catalog_sqlite.py::test_tzdata_version_mismatch_warns_once_and_allows_open -q --tb=short -p no:cacheprovider` | 1 passed отдельно вне sandbox; первая попытка внутри sandbox дала `PermissionError` на системный pytest temp |
| `python -m compileall -q src/exact_orb/http_api tests/http_api/test_session.py tests/http_api/test_request_boundary.py`; `git diff --check` | exit 0; Git предупредил только о будущей LF → CRLF нормализации working copy |

Сетевые/платные smoke-тесты не запускались. Коммит, push и PR не создавались.

## 18. Исполнение промта 09 — поиск мест (2026-10-01)

Добавлен `GET /places`. Маршрут использует существующий request boundary для
проверки `query` и `limit`, вызывает `PlaceSearch.search` ровно один раз и
сериализует только четыре публичных поля каждого найденного места через
`project_places`. `InvalidPlaceQuery` отображается в safe 422 с кодом
компонента, `PlaceCatalogUnavailableError` — в 503 с `Retry-After: 5`;
неожиданные ошибки проходят через общий safe 500 обработчик приложения.
Маршрут не читает session cookie и не обращается к session/context,
orchestrator или `lookup` каталога. При пустом результате возвращается
`200 {"items": []}`.

Новый интеграционный тест собирает временный SQLite-каталог из существующих
fixture-файлов и проверяет реальный поиск `МОСКВА`, точную форму DTO и
игнорирование невалидной session cookie. Существующие тесты с управляемым
каталогом проверяют единственность поиска, границы query/limit, пустой ответ,
типизированные ошибки и отсутствие побочных вызовов. Контракты §4.2, §6.3,
§7 и §8 не менялись, поэтому requirements, ADR и sequence diagram не
редактировались. IP admission `/places` остаётся за промтом 10, журнальные
события — за промтом 13.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_place_dto.py -q -k "places_success_and_empty or places_uses_real_sqlite_search or place_limit_boundaries or invalid_limit_grammar or missing_duplicate_or_extra_query_parameter or raw_query_length or place_component_outcomes or wrong_origin_blocks_current_and_places" --tb=short -p no:cacheprovider` | 21 passed, 47 deselected |
| `python -m pytest tests/http_api/test_request_boundary.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 94 passed |
| `python -m pytest tests/http_api/test_lifecycle.py -q -k "malformed_trusted_forwarding_stops_before_catalog_and_quota" --tb=short -p no:cacheprovider` | 8 passed, 47 deselected |
| `python -m pytest tests/test_place_catalog_search.py tests/http_api/test_request_boundary.py tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | 112 passed вне sandbox; первая попытка внутри sandbox дала 94 passed, 18 errors из-за `PermissionError` на системный pytest temp |
| `python -m pytest tests/http_api/test_place_dto.py -q --tb=short -p no:cacheprovider` | 36 passed, 32 failed: остаются проверки будущего `POST /charts/natal` (промт 11) |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2839 passed, 82 failed: ожидаемые RED будущих admission/build/shutdown/logging и известный `test_tzdata_version_mismatch_warns_once_and_allows_open` |

Полный pytest запускался вне sandbox из-за воспроизводимого ограничения
доступа к системному pytest temp. Сетевые/платные smoke-тесты и PlantUML
rendering не запускались. Коммит, push и PR не создавались.

## 19. Исполнение промта 10 — process-local admission (2026-10-01)

Добавлен process-local `AdmissionController` с неизменяемыми production defaults
§9.1 и тестовой инъекцией малой policy через существующий G0-шов. Все окна
считаются от `scheduler.now()`; событие истекает включительно на границе
окна. При каждом admission истёкшие события и пустые buckets удаляются.
Отказ rate/capacity не добавляет событий. Для build одна критическая секция
сначала оценивает четыре rate bucket, выбирает самый поздний момент допуска
с приоритетом session → IP и сутки → час при равенстве, затем проверяет пять
process permits и только после допуска резервирует все четыре окна и один
явный `BuildPermit`. Permit освобождается только вызовом его владельца;
обычный terminal owner подключит промт 11, а cancellation/retained work — 12.

После transport validation `POST /session/bootstrap` расходует одну creation
квоту на запрос, который создаёт новую сессию, независимо от внутренних
collision attempts; live-cookie restore не расходует её. При отказе 429
сохранено гашение старой invalid/expired cookie. `GET /places` теперь
резервирует IP quota до `PlaceSearch.search` и выдаёт typed 429 без обращения
к каталогу. Коды, detail, сообщения и вычисленный `Retry-After` следуют §8.2
и §9.1. Публичные component API, требования, ADR и sequence diagrams не
изменялись: новые операции уже описаны там. Persistent limiter, multi-worker
coordination и пользовательский/env override не добавлены.

Добавлены чистые детерминированные тесты: пять удерживаемых permits и шестой
отказ, приоритет rate, отсутствие расхода quota при capacity refusal,
атомарная конкуренция за последний слот, доминирующий IP daily bucket,
очистка истёкших buckets и отказ в середине окна без сдвига границы для
creation/place. Численные production defaults проверяет существующий тест.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api/test_admission.py tests/http_api/test_build_admission.py -q -k "test_admission or production_admission_defaults or pure_limiter_window_arithmetic" --tb=short -p no:cacheprovider` | 7 passed, 27 deselected после последних двух pure cases |
| `python -m pytest tests/http_api/test_session.py tests/http_api/test_build_admission.py tests/http_api/test_lifecycle.py -q -k "creation_rolling_hour_limit or collision_attempts_consume_one or absent_cookie_is_cleared_even_when_bootstrap_creation_fails or place_and_creation_ip_windows or malformed_trusted_forwarding_stops_before_catalog_and_quota or trusted_chain_and_mapped_ipv6_share_canonical_ip_bucket or untrusted_spoofed_forwarding_uses_each_direct_peer_bucket" --tb=short -p no:cacheprovider` | 15 passed, 104 deselected: creation/place quota и proxy-IP precedence |
| `python -m pytest tests/http_api/test_build_admission.py tests/http_api/test_lifecycle.py tests/http_api/test_session.py tests/http_api/test_place_dto.py -q -k "production_admission_defaults or pure_limiter_window_arithmetic or place_and_creation_ip_windows or invalid_admission_limit_fails_before_resources_open or malformed_trusted_forwarding_stops_before_catalog_and_quota or trusted_chain_and_mapped_ipv6_share_canonical_ip_bucket or untrusted_spoofed_forwarding_uses_each_direct_peer_bucket or creation_rolling_hour_limit or collision_attempts_consume_one or absent_cookie_is_cleared_even_when_bootstrap_creation_fails or places_success_and_empty or places_uses_real_sqlite_search or place_limit_boundaries or invalid_limit_grammar or missing_duplicate_or_extra_query_parameter or raw_query_length or place_component_outcomes" --tb=short -p no:cacheprovider` | 38 passed, 149 deselected: затронутые маршруты и прежний поиск |
| `python -m pytest tests/http_api/test_request_boundary.py tests/test_module_boundaries.py tests/http_api/test_admission.py tests/http_api/test_build_admission.py tests/http_api/test_lifecycle.py -q -k "not test_build_admission and not test_lifecycle" --tb=short -p no:cacheprovider` | 97 passed, 84 deselected: boundary, module rules и pure admission до последних двух cases |
| `python -m pytest tests/http_api/test_session.py -q --tb=short -p no:cacheprovider` | 33 passed, 2 failed: только `http_cookie_replaced` и `chart_unavailable` logging промта 13 |
| `python -m pytest -q --tb=no -p no:cacheprovider` | 2851 passed, 73 failed до последних двух pure cases: RED будущих build/terminal release (11), shutdown/deadline (12), logging/schema (13) и известный tzdata logging test |
| `python -m compileall -q src/exact_orb/http_api tests/http_api/test_admission.py`; `git diff --check` | exit 0; Git предупредил только о будущей LF → CRLF нормализации working copy |

Широкий mixed-прогон route/lifecycle также дал 169 passed, 16 failed, 32
deselected: отказы относятся к отсутствующему build route и будущим
shutdown/schema/logging проверкам. Полный pytest запускался вне sandbox из-за
системного pytest temp. Сетевые/платные smoke-тесты и PlantUML rendering не
запускались. Коммит, push и PR не создавались.
