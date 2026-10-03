# Tester: HTTP API and Session Middleware

**Роль:** Tester<br>
**Дата:** 2026-10-02<br>
**Статус evidence:** PARTIAL; реальный локальный HTTPS проверен с обходом найденного дефекта стенда<br>
**Tested commit:** `5df58a0be6aeaab577664d6bfd6248f908dadbf7` (`change/http-api-and-session-middleware`; live-прогон начат на `test/*` с тем же HEAD, затем checkout переключён на указанную `change/*` без изменения файлов)<br>
**Requirements baseline:** [HTTP API](../../requirements/http_api.md) @ `5df58a0`<br>
**Decision register baseline:** единый файл реестра `DP-*` отсутствует в этом commit. Решения `DP-HTTP-01…06` и ограничения `FIND-HTTP-*` находятся в [HTTP requirements §3, §15](../../requirements/http_api.md); это текущий доступный baseline, а не подтверждение обновления строк реестра.<br>
**Другие входы:** [change plan](../../project_management/change_plans/http-api-and-session-middleware.md), [implementation plan](../../project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), [HTTP sequences](../../sequence_diagrams/http_api/README.md), ADR-0039/0040/0041, [локальный runbook](../../runbooks/http_api_local_https.md).

## Testability review

**Статус:** TESTABLE WITH LOCAL HOST LIMITATION.

AS-HTTP-01…29 задают наблюдаемые ответы, границы, recovery и lifecycle. Для конкуренции и времени есть управляемый scheduler, barriers и отдельные SQLite-backed app/runtime instances; для существенных отрицательных проверок в тестах есть успешный контроль. Технические вопросы предыдущего review T-A1…T-A4 имеют исполняемые проверки в текущем наборе. Само прохождение этих проверок не доказывает работу реального Caddy, браузерной cookie jar или внешнего supervisor.

Сценарии, сформированные из требований до сверки с тестами Developer: повторная/невалидная cookie и отказ создания новой сессии; граница rolling window и одновременный rate/capacity отказ; потеря ответа commit с последующим чтением из нового runtime; отменённый waiter при живом single-flight leader; медленный body с быстрым положительным контролем; unmatched route без событий запроса при успешном `/places` с событиями. Сверка с тестами показала покрытие этих сценариев; дублирующий regression-тест не добавлен.

**Оценка оставшейся работы Tester:** 0,5–1 рабочего дня после исправления `FIND-TEST-HTTP-001`; confidence medium. Осталось повторить M-02…M-11 обычным локальным HTTPS-клиентом/Postman и, если это требуется acceptance, проверить браузерную cookie policy. Эта оценка не меняет Lead-owned Gantt.

**Decision register updates:** не выполнены: в tested commit нет реестра, в котором можно дополнить строки `DP-HTTP-01…06`. Change Manager должен определить baseline/место единого реестра и перенести Tester evidence при согласовании handoff; Tester не создаёт альтернативный источник решений.

## Acceptance evidence

### Среда и точные запуски

Windows 11, Python 3.14.0; FastAPI 0.121.2, Starlette 0.49.3, Pydantic 2.12.4, Uvicorn 0.38.0, httpx 0.28.1, pytest 9.0.2. Первые пять строк ниже выполнены на неизменённом `5df58a0`; последующие — на рабочем дереве поверх этого HEAD с исправлением `FIND-TEST-HTTP-003`. Автоматический набор использует ASGI-клиент `https://testserver` без реального TLS. Отдельный локальный HTTPS-прогон выполнен 2026-10-02 через Caddy v2.11.6 и mkcert v1.4.4; платные/внешние сетевые smoke не запускались.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/http_api -q --tb=short -p no:cacheprovider` | PASS: 292 passed in 17.77s |
| `python -m pytest tests/application tests/session tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` | Среда: 1601 passed, 4 setup errors; pytest не смог читать `C:\Users\KateUser\AppData\Local\Temp\pytest-of-KateUser` (`PermissionError`), HTTP assertion не падал |
| Та же команда с `--basetemp C:\Users\KateUser\.codex\visualizations\2026\10\02\01a0fd03-c043-7030-8697-cacb26eee8a2\pytest-http-tester` | Среда: тот же `PermissionError` при чтении созданного каталога; не является PASS |
| `python -m pytest tests/application tests/session tests/test_module_boundaries.py -q --tb=short -p no:cacheprovider` вне sandbox | PASS: 1605 passed in 62.83s |
| `python -m pytest -q --tb=short -p no:cacheprovider` вне sandbox | PASS: 2952 passed in 115.11s |
| `python -m pytest tests/session/test_sqlite.py::test_chart_write_failure_rolls_back_parent_and_retry_commits_pair tests/session/test_sqlite.py::test_lost_chart_commit_acknowledgement_preserves_pair_and_retry_winner -q --tb=short -p no:cacheprovider` после исправления | PASS: 2 passed in 0.55s |
| `python -m pytest tests/application/test_build_natal_logging.py tests/session/test_context.py tests/session/test_sqlite.py tests/http_api -q --tb=short -p no:cacheprovider` после исправления | Первая попытка: 674 passed, 1 failed из-за прежнего утверждения о выключенном локальном DEBUG; после обновления ожидаемого профиля PASS: 675 passed in 20.54s |
| `python -m pytest -q --tb=short -p no:cacheprovider` после исправления | PASS: 2952 passed in 118.51s |
| `python -m pytest tests/http_api/test_place_dto.py::test_build_schema_rejects_malformed_or_extra_fields_before_orchestrator -q --tb=short -p no:cacheprovider` после добавления combined-invalid case | PASS: 6 passed in 0.56s |
| `python -m pytest tests/http_api -q --tb=short -p no:cacheprovider` после добавления combined-invalid case | PASS: 293 passed in 13.07s |
| `python -m pytest -q --tb=short -p no:cacheprovider` после добавления combined-invalid case | PASS: 2953 passed in 113.63s |

Причина двух неуспешных попыток связанного набора — запрет перечисления временных каталогов внутри sandbox; вне sandbox те же 4 setup cases прошли. Это ограничение среды запуска, не воспроизведённый дефект приложения.

### Requirement → scenario → evidence

`PASS` ниже означает успешную автоматизированную проверку в `tests/http_api` на baseline commit; полный набор дополнительно повторён после исправления DEBUG-логирования. Таблица сопоставляет сценарии с ключевыми тестами; набор содержит и дополнительные параметризованные случаи.

| AS | Проверяемое поведение | Ключевое evidence | Статус |
| --- | --- | --- | --- |
| 01 | bootstrap, Secure cookie, empty current | `test_session.py::test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation` | PASS |
| 02 | restore на новом runtime и том же SQLite | `test_session.py::test_restart_uses_same_sqlite_file_with_new_runtime_and_empty_cache` | PASS |
| 03 | stale/unavailable/empty, structural corruption | `test_session.py::test_current_projects_stale_unavailable_or_empty_without_mutation`, `test_structural_sqlite_chart_corruption_is_503_not_unavailable` | PASS |
| 04 | absent/read failure и cookie policy | `test_session.py::test_absent_current_clears_cookie_and_bootstrap_replaces_it`, `test_state_read_failure_preserves_cookie_and_never_creates_session` | PASS |
| 05 | duplicate cookie | `test_session.py::test_duplicate_raw_cookie_is_replaced_by_bootstrap_without_loading_it`, `test_build_admission.py::test_invalid_or_duplicate_build_cookie_stops_before_admission_and_execute` | PASS |
| 06 | три ID collision и create failure | `test_session.py::test_three_id_conflicts_stop_without_foreign_load_or_fourth_id`, `test_create_storage_failure_does_not_issue_cookie_and_success_is_control` | PASS |
| 07 | creation rolling limit | `test_session.py::test_creation_rolling_hour_limit_restore_and_exact_expiry_boundary` | PASS |
| 08 | place results без доступа к session | `test_place_dto.py::test_places_success_and_empty_have_exact_whitelist_without_session_access` | PASS |
| 08 + [place catalog §4.3](../../requirements/component_responsibilities/exact-orb_place_catalog.md#43-поиск-и-ранжирование) | Префиксы `Н`, `Но`, `Нов` на полном каталоге, default limit 10, разные города и exact match | [M-12…M-14](manual-tests.md#полный-каталог-m-12m-14), `live_https_checks.py place_prefixes` | PASS для трёх live data cases; полнота каталога не доказана |
| 09 | query/limit grammar и длина | `test_place_dto.py::test_invalid_limit_grammar_stops_before_catalog_with_positive_control`, `test_raw_query_length_is_checked_in_unicode_code_points_before_catalog` | PASS |
| 10 | typed catalog outcomes | `test_place_dto.py::test_place_component_outcomes_map_to_safe_http_and_keep_positive_control` | PASS |
| 11 | natal/cosmogram и атомарный StoredChart | `test_place_dto.py::test_http_build_commits_state_and_stored_chart_atomically_with_real_orchestrator` | PASS |
| 12 | validation priority, early rejection | `test_place_dto.py::test_matched_route_validation_priority_stops_before_lower_layers`, `test_build_schema_rejects_malformed_or_extra_fields_before_orchestrator` | PASS |
| 12–13 | Одновременно неверные дата и время, без запуска build | `test_place_dto.py::test_build_schema_rejects_malformed_or_extra_fields_before_orchestrator[invalid-date-and-time]` | PASS: `422 INVALID_REQUEST`, `birth.date`, Orchestrator/Context не вызваны; корректный контроль дошёл до Orchestrator |
| 13 | calendar schema/domain boundary | `test_place_dto.py::test_calendar_valid_domain_dates_reach_application_as_typed_issues`, `test_valid_ephemeris_boundary_dates_reach_stub_resolver_after_schema` | PASS |
| 14 | InputRequired и dependency mapping | `test_place_dto.py::test_input_required_keeps_typed_issues_and_renews_cookie`, `test_application_typed_failures_keep_allowed_fields_and_cookie_policy` | PASS |
| 15 | safe internal failure mapping | `test_place_dto.py::test_internal_application_subtypes_are_hidden_by_safe_500` | PASS |
| 16 | явный rebuild с fresh version | `test_build_admission.py::test_explicit_rebuild_uses_fresh_version_and_does_not_echo_old_chart_on_failure` | PASS |
| 17 | поздний POST второй вкладки | `test_build_admission.py::test_late_tab_post_fresh_loads_newer_version_without_client_precondition` | PASS, серверная часть |
| 18 | concurrent CAS и AlreadyApplied | `test_build_admission.py::test_concurrent_sqlite_intents_map_committed_already_applied_and_superseded` | PASS |
| 19 | uncertain commit и timeout recovery | `test_build_admission.py::test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart`, `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state` | PASS, серверная часть |
| 20 | исчезнувшая session во время build | `test_build_admission.py::test_build_session_absent_clears_cookie_without_creating_or_replaying_build` | PASS |
| 21 | session/IP windows, tie, CGNAT | `test_build_admission.py::test_later_ip_daily_bucket_dominates_session_hourly_and_recovers_at_boundary`, `test_default_cgnat_many_sessions_and_three_hundred_ip_builds` | PASS |
| 22 | capacity и 30-секундный watchdog | `test_build_admission.py::test_rate_wins_over_full_capacity_and_neither_rejection_spends_quota`, `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state` | PASS, модель restart |
| 23 | slow body и быстрый контроль | `test_lifecycle.py::test_slow_body_uses_first_event_deadline_and_fast_same_size_succeeds` | PASS |
| 24 | disconnect, retained leader/commit/futures | `test_lifecycle.py::test_two_waiters_one_real_leader_keep_separate_permits_after_disconnect`, `test_cancelled_catalog_lookup_keeps_five_permits_and_shutdown_owner`, `test_disconnect_during_protected_commit_is_visible_after_restart` | PASS |
| 25 | reaper cadence, failure, shutdown | `test_lifecycle.py::test_reaper_waits_from_completion_survives_failures_and_shutdown_waits` | PASS |
| 26 | startup, health и close ordering | `test_lifecycle.py::test_health_ready_and_shutdown_gate_have_real_business_control`, `test_shutdown_grace_fail_fast_preserves_active_build_and_open_resources` | PASS, без внешнего supervisor |
| 27 | headers, Retry-After и события | `test_lifecycle.py::test_required_headers_matrix_and_exact_retry_after`, `test_four_http_sequences_emit_ordered_messages_and_one_safe_terminal` | PASS |
| 28 | exact DTO whitelist и golden | `test_projectors.py::test_chart_dto_exact_golden_and_no_internal_fields`, `test_session_view_dto_matches_birth_golden_without_private_warnings` | PASS |
| 29 | routes, HEAD/OPTIONS, schema, proxy IP | `test_lifecycle.py::test_route_method_head_options_and_hidden_schema_are_exact`, `test_untrusted_spoofed_forwarding_uses_each_direct_peer_bucket` | PASS |

### Локальный HTTPS и exploratory check

Пошаговая процедура и матрица фактических ответов M-01…M-11 находятся в [manual-tests.md](manual-tests.md). Стенд: Caddy с доверенным локальным mkcert CA → один Uvicorn `127.0.0.1:8000`, настоящие эфемериды `ephe`, отдельная session SQLite и каталог из репозиторных GeoNames fixtures (5 places, 13 names, включая Москву `524901`). Сертификат проверялся `httpx` по `rootCA.pem`; TLS verification не отключалась. Для API-запросов после обнаруженного `FIND-TEST-HTTP-001` тестовый клиент привязан к `127.0.0.2`, чтобы Caddy видел недоверенный адрес клиента. Это реальный HTTPS/API/proxy/process прогон, но не проверка Postman UI или браузера.

M-01 и M-02…M-11 при указанном адресе клиента **PASS**; обычный локальный клиент с `127.0.0.1` стабильно получает `400 FORWARDED_HEADER_INVALID` уже на bootstrap. Штатная остановка PID `27768` и старт нового PID `25592` с той же SQLite-базой проверены. M-11 вернул прежние `state_version=2` и `chart_identity`; события `request_id=158937d7-ec32-47f0-b688-241f43b56fd0` и `311daa95-d809-43d6-a786-647597111954` содержат только `ContextService.load`/`session_view`, без `ApplicationOrchestrator.execute`. Дополнительные проверки: current без cookie → `409 SESSION_REQUIRED`; current продлил одну cookie с тем же ID. Дублирующаяся cookie проверена автоматически; в Postman её вручную не воспроизводили.

После прогона Uvicorn и Caddy штатно остановлены; listener на портах `80`, `443`, `8000` нет. Сертификат, доверенный локальный CA, fixture-каталог и отдельная SQLite-база сохранены в `%LOCALAPPDATA%` для повторного запуска; временный файл с session cookie удалён.

### Повторный DEBUG-прогон журнала

После включения локального DEBUG повторён `python docs/testing/http-api-and-session-middleware/live_https_checks.py phase1` с отдельной `sessions-debug.sqlite3`; M-01…M-10 прошли. В локальном `logs/http-api/local.log` запрос natal `470ed13d-c8ca-4cb3-b9a6-66d4904f4c79` дал полный `component_message direction=out operation=build_natal` с картой (строка 313, 38 050 символов), затем `session_sqlite_cas_committed` с `state_version=1`, `chart_action=upsert` и тем же `calculation_key` (строка 318). Для cosmogram `0076937d-9298-450f-bf55-51bd81184e49` соответствующие строки 3290 и 3295, `state_version=2`. Номера строк относятся к файлу сразу после этого прогона и могут сместиться при следующем запуске/ротации. `StoredChart.payload` в SQL-событие не выводится. Оба процесса остановлены, временный cookie-файл удалён. Журнал локален и не входит в Git.

### Полный каталог и три новых HTTPS-проверки

Ранее собранный GeoNames artifact скопирован в игнорируемый Git `data/places.sqlite` этой ветки; источник `C:\Users\KateUser\PycharmProjects\exact-orb-recovered\data\places.sqlite`, SHA-256 обеих копий `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD`, 16 329 мест и 36 648 имён. Запущен один Uvicorn с `EXACT_ORB_PLACES_DB=data/places.sqlite` и отдельной `logs/http-api/sessions-prefix.sqlite3`, Caddy прошёл `validate`; ответы проверены через TLS с доверенным `mkcert` CA и исходным адресом клиента `127.0.0.2`. При startup есть предупреждение `catalog_tzdata_version=2026.3`, `runtime_tzdata_version=2025.2`; каталог открывается и поиск работает, но это ограничение среды для birth-time расчётов с данным артефактом.

Команда `python -X utf8 docs/testing/http-api-and-session-middleware/live_https_checks.py place_prefixes` → **PASS, 3 live cases** на рабочем дереве поверх `5df58a0` с исправлением logging. [Пошаговые M-12…M-14 и фактические ответы](manual-tests.md#полный-каталог-m-12m-14): `Н` → `200`, 10 мест (`Новосибирск`, `Нижний Новгород`, `Нальчик`), request ID `bb960151-67ec-41f9-8d2f-a833a3a2c801`; `Но` → `200`, 10 мест (`Новосибирск`, `Новокузнецк`, `Новомосковск`, `Носовка`, без `Нижнего Новгорода`), `82982754-3b38-48ec-b455-a83be66d31c5`; `Нов` → `200`, 10 мест (точное `Нов` первым, `Новосибирск`, `Новокузнецк`, без `Носовки`), `275c7749-869c-41ee-88df-bff8005f1bad`. Уникальность `place_id`, точный набор публичных полей и отсутствие `Set-Cookie` проверены в каждом ответе. Локальный журнал содержит `http_request_started` → `PlaceSearch` → `PlaceSuggestions` → `http_request_finished status=200` для всех трёх IDs. После проверки Caddy и Uvicorn штатно остановлены; listeners `80`, `443`, `8000` отсутствуют. Полный каталог проверен на этих запросах, а не исчерпывающе по географии или качеству имён.

### Повторный полный ручной API-прогон с отдельными логами

На той же ветке и tested commit повторно выполнены **M-01…M-14** на полном каталоге GeoNames (SHA-256 `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD`) через Caddy/mkcert HTTPS с доверенным CA и тестовым исходным адресом `127.0.0.2`. Последовательность `phase1` → штатный перезапуск Uvicorn с той же session SQLite → `phase2` → `supplemental` → `place_prefixes` → `proxy_control` дала **PASS для всех 14 сценариев**. [Пошаговая процедура и точные результаты](manual-tests.md#повторный-полный-прогон-журнал-вызовов-m-01m-14).

[run.log](../../../logs/http-api/manual-20261002T203646Z/run.log) содержит все 25 вызовов endpoint с методом, URL, HTTP status и request ID; значения session cookie туда не записаны. [app.log](../../../logs/http-api/manual-20261002T203646Z/app.log) — отдельный локальный DEBUG-журнал, содержащий 22 `http_request_finished` для 22 бизнес-запросов, оба результата `build_natal` и оба `session_sqlite_cas_committed`. Два внутренних health-запроса обходят бизнес-журнал, а внешний health `404` возвращает Caddy. Обычный loopback-клиент снова воспроизвёл `FIND-TEST-HTTP-001`: bootstrap → `400 FORWARDED_HEADER_INVALID`, request ID `edd7fb53-810b-4b48-a54f-953ba996719d`. `app.log` содержит данные сессии и карты; оба файла находятся только в игнорируемом Git `logs/` текущей рабочей копии. После прогона процессы завершены, порты `80`, `443`, `8000` свободны, временный cookie-файл удалён. Postman UI и браузерная cookie policy этим прогоном не проверялись.

### Уточнение M-12…M-14: читаемый запрос и страна (`FIND-TEST-HTTP-005`)

Пользовательская проверка показала недостаток представления в тестовом журнале: `%D0%9D` в URL — UTF-8 кодировка `Н`, а старая строка `names=[...]` скрывала уже присутствующий в `/places` `country_code`. Helper теперь печатает декодированный `query` рядом с URL и все поля каждой подсказки. Повторный HTTPS-прогон M-12…M-14 на полном каталоге — **3 PASS**, 3 HTTP-вызова и 3 `http_request_finished`: [run.log](../../../logs/http-api/place-readable-20261003T113439Z/run.log), [app.log](../../../logs/http-api/place-readable-20261003T113439Z/app.log). Для `Н` первым пришёл `Нью-Йорк` `5128581`, регион `Нью-Йорк`, страна `US`; это результат глобального поиска, а не отсутствие страны в DTO. Старый журнал сохранён. Новый журнал и DEBUG-файл локальны, не входят в Git; после проверки Caddy и Uvicorn остановлены.

## Findings, ограничения и handoff

- **FIND-TEST-HTTP-001 — дефект локальной интеграции, blocker для обычного localhost/Postman-прогона.** [Runbook](../../runbooks/http_api_local_https.md) и [Caddyfile](../../runbooks/http_api_local.Caddyfile) направляют локального клиента с `127.0.0.1` через Caddy на Uvicorn. `http_server.py` доверяет `127.0.0.1/32`, а `proxy.py::client_ip` требует хотя бы один недоверенный адрес в `X-Forwarded-For` + ASGI peer. Оба адреса оказываются `127.0.0.1`; `POST /session/bootstrap` возвращает `400 FORWARDED_HEADER_INVALID` (повторный `X-Request-ID: d1868dab-fe18-4ddf-b465-edcbfce73716`). Позитивный контроль: тот же HTTPS-запрос с источника `127.0.0.2` → `200`, после чего M-02…M-11 проходят. Исправление конфигурации/контракта доверенных proxy требует решения Developer/Lead; Tester production code не менял. После исправления повторить обычный локальный клиент и regression-проверку.
- **FIND-TEST-HTTP-002 — bug публичного контракта: техническое имя `admin1_name` в подсказке места; P3, OPEN.**
  - Воспроизведение: выполнить M-04 (`GET /places?query=Москва&limit=10`) и посмотреть ключи первого `items[]`.
  - Факт: ответ `200` содержит `admin1_name` (для Москвы — `"Москва"`); [HTTP requirements §6.3](../../requirements/http_api.md) и `PlaceSuggestionDTO` закрепляют это имя.
  - Ожидание: понятное клиенту имя поля региона, например `region_name`. Это предложение к решению, пока не утверждённый контракт.
  - Позитивный контроль и evidence: поиск возвращает Москву `place_id=524901` с корректными `display_name`/`country_code`; `X-Request-ID: 2c3a62fd-4f40-42a8-8738-29de9f1d7af2`. Данные и поиск работают.
  - Влияние: термин GeoNames `admin1` попадает в публичный API и UI, хотя [UI requirements](../../ui_ux/requirements.md) называют это регионом; позднее переименование затронет клиентов. Это дефект согласованного DP-HTTP-01/DTO-контракта, а не отклонение реализации от действующих требований.
  - Owner и закрытие: Functional Analyst предлагает ревизию контракта, Lead принимает решение, Developer меняет DTO/projector/tests после approval. Закрыть finding после решения по DP-HTTP-01: согласовать имя и синхронизировать requirements/UI/tests/implementation либо явно принять текущее имя с обоснованием.
- **FIND-TEST-HTTP-003 — bug наблюдаемости локального HTTP-пути: не видны полная карта и подтверждённая запись в SQLite; P2, FIXED / TESTER VERIFIED.**
  - Воспроизведение до исправления: запустить локальный стенд с прежним `http_api_local_logging.json`, выполнить M-05 `POST /charts/natal` и искать в `logs/http-api/local.log` полную карту и исход атомарной записи `session_states` + `session_charts`.
  - Факт: `exact_orb` и file handler были на INFO, поэтому существующие DEBUG-сообщения с картой фильтровались; SQLite-адаптер не писал отдельного события подтверждённого commit. Позитивный контроль исходного прогона: build `X-Request-ID: a6ebb9f9-4a43-43cc-be2c-d82a2d361285` вернул `200`, журнал показал `ApplicationCommitted`, а M-06 прочитал ту же карту. Отсутствие детализации не объясняется пропуском расчёта или сохранения.
  - Ожидание: на локальном диагностическом стенде полный `ChartArtifact` доступен при DEBUG по ADR-0028; после подтверждённого SQL commit есть отдельное событие с таблицами, версией, действием над картой и `calculation_key`. Удалённый M1-профиль остаётся INFO по ADR-0034; бинарный `StoredChart.payload` не печатается по ADR-0041.
  - Причина и исправление: локальному logger и file handler установлен DEBUG; после успешного CAS commit адаптер пишет `session_sqlite_cas_committed`. При откате, конфликте или неподтверждённом commit это событие не создаётся. Runbook и проверки обновлены.
  - Проверка: повторный live build `470ed13d-c8ca-4cb3-b9a6-66d4904f4c79` записал полную карту и SQL-событие с одинаковым `calculation_key` (локальный `local.log`, строки 313/318); cosmogram — строки 3290/3295. Два целевых теста, связанные 675 и полный набор 2952 прошли.
  - Owner и закрытие: Developer; исправление и Tester verification выполнены в этой рабочей ветке. Публикация и acceptance Change Manager отдельно не подтверждены; финальное закрытие finding после интеграционного review.
- **FIND-TEST-HTTP-004 — requirement/UX gap широких префиксов на полном каталоге; OPEN.**
  - Сценарии: M-12…M-14 на артефакте с SHA-256 `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD`; запросы без `limit` используют 10, максимальный разрешённый `limit` — 20.
  - Факт: на `Н` первые 10 включают `Нальчик`, `Нижний Новгород`, `Новосибирск`, но не `Нарьян-Мар` и `Новороссийск`; на `Но`/`Нов` первые 10 включают несколько городов, но не `Новороссийск`, `Новочеркасск`, `Новошахтинск`. Даже `limit=20` не включает эти отсутствующие примеры. Позитивный контроль: поиск каждого полного имени отдельно вернул `200` и соответствующий `place_id` (`523392`, `518255`, `518970`, `517963`).
  - Причина: [действующий контракт §4.3](../../requirements/component_responsibilities/exact-orb_place_catalog.md#43-поиск-и-ранжирование) ранжирует current preferred aliases выше прочих актуальных имён, затем по населению, и ограничивает выдачу; при русском префиксе глобальные preferred-совпадения занимают первые позиции. Это не отклонение реализации от утверждённого порядка.
  - Влияние и следующий шаг: если пользовательское ожидание состоит в появлении перечисленных городов уже после 1–3 символов, критерий не выполняется. Functional Analyst и Lead должны решить, нужен ли иной порядок, контекст страны или UX для коротких префиксов; Tester обновит expected result после решения. Production code и requirements в этом проходе не менялись.
- **FIND-TEST-HTTP-005 — bug тестового журнала, найденный человеком; severity minor, priority P3 (предложение), FIXED / TESTER VERIFIED.**
  - Сценарий и источник: пользователь просмотрел сохранённый `run.log` полного прогона M-12 `GET /places?query=Н` на tested commit `5df58a0be6aeaab577664d6bfd6248f908dadbf7` и полном локальном каталоге через Caddy/mkcert HTTPS. Повторение: выполнить `python -u -X utf8 docs/testing/http-api-and-session-middleware/live_https_checks.py place_prefixes` старым helper и прочитать строку `HTTP` и список `names` для M-12.
  - Факт до исправления: в строке вызова было только `query=%D0%9D`, а в результатах — названия без страны и региона. `Нью-Йорк` выглядел неоднозначно. `%D0%9D` — корректная URL-кодировка `Н`; дефектом было отсутствие читаемого значения рядом с URL и потеря полей в тестовом выводе.
  - Ожидание и позитивный контроль: журнал ручного прогона должен позволять человеку сопоставить запрос `Н` с результатами и различить одноимённые места по `place_id`, `admin1_name`, `country_code`. [HTTP API §6.3](../../requirements/http_api.md#63-get-places) уже требует эти поля; старый helper проверял их наличие в ответе. Следовательно, это баг **тестового evidence**, а не публичного API или percent-encoding.
  - Причина и исправление: `trace_response` печатал только закодированный URL, а `place_prefixes` сводил ответ к `display_name`. Helper теперь дополнительно печатает декодированный `query` и четыре публичных поля каждого item; URL сохраняется для точной диагностики. Owner: Tester. API, ранжирование и каталог не изменены.
  - Ретест: повторный HTTPS-прогон M-12…M-14 — **3 PASS**, 3 вызова и 3 соответствующих `http_request_finished`; [читаемый run.log](../../../logs/http-api/place-readable-20261003T113439Z/run.log) содержит 30 строк с `country`, в том числе `Нью-Йорк` `5128581`, `country=US`. `python -m py_compile docs/testing/http-api-and-session-middleware/live_https_checks.py` и `git diff --check` прошли. Старый журнал оставлен как исходное evidence.
  - Blocks: не блокирует поведение API; ухудшал проверяемость журнала. Условие закрытия по работе Tester выполнено и проверено локально; логи игнорируются Git и доступны только в этой рабочей копии.
- **Процессное расхождение (Change Manager):** `change/*` и `test/*` уже указывают на merge `5df58a0` (#38), но [change plan](../../project_management/change_plans/http-api-and-session-middleware.md) и [журнал Experiment 002](../../project_management/experiments/experiment-002-log.md) всё ещё описывают разработку/интеграцию как ожидаемую. Уточнить статус FIND-HTTP-020 и переход к Testing на основании Git и approval; Tester не меняет документы владельца change.
- **Принятые ограничения:** `FIND-HTTP-017/018/023/024` из [requirements §15](../../requirements/http_api.md) и условия M1-12 из change plan. Они не объявляются новыми дефектами.
- **Не проверено:** Postman UI и браузерная cookie jar, исчерпывающая полнота GeoNames и качество всех имён, внешний supervisor/ACL и принудительный kill после fail-fast, публикация из этого рабочего дерева. Штатный process restart и настоящий TLS/Caddy проверены. Первый end-to-end сценарий с Москвой прошёл на fixture-каталоге; повторный полный прогон M-01…M-14 прошёл на полном локальном каталоге.
- **Предел независимости:** автоматические HTTP assertions подготовлены на этапе Development. Этот проход сверил их с требованиями и выполнил заново; отдельный live HTTPS-прогон выполнен Tester, но запросы отправлялись скриптом `httpx`, а не вручную через Postman.

**Readiness recommendation:** **NOT READY FOR FINAL ACCEPTANCE** до закрытия `FIND-TEST-HTTP-001`, повторного обычного localhost/Postman-прогона, решения по `FIND-TEST-HTTP-002` в рамках DP-HTTP-01 и уточнения Change Manager процессного статуса. Исправления `FIND-TEST-HTTP-003/005` проверены локально; автоматизированная часть AS-HTTP-01…29 на `5df58a0` и live HTTPS с источника `127.0.0.2` прошли. Финальное решение о change принимает Lead.
