# Промт 04 — coverage и ожидаемый RED

Все app-зависимые импорты находятся внутри fixture или теста. Пока
`exact_orb.http_api` не реализован, они падают на `ModuleNotFoundError`;
этот одинаковый RED не доказывает поведения. Независимый контроль scheduler
работает без transport. Для параметризованных тестов строка относится ко
всем случаям.

| Тест | AS / требование | Ожидаемый GREEN и причина текущего RED | Implementation |
| --- | --- | --- | --- |
| `test_scheduler_control_has_exact_deadline_and_no_wall_clock` | G0; §4.3/11.2 | Проходит: scheduler ждёт абсолютный monotonic срок и управляется вручную | 05/06/12 используют seam |
| `test_slow_body_uses_first_event_deadline_and_fast_same_size_succeeds` | 23; §4.3 | 5 секунд отсчитываются от первого body event, 408 не вызывает create, быстрый body работает; нет app | 05–06, 08 |
| `test_reaper_waits_from_completion_survives_failures_and_shutdown_waits` | 25; §11.2/12 | Runs в 900/1860/2760/3660, без overlap, typed/unexpected error не останавливают цикл, shutdown ждёт active run и журнал содержит оба события; нет app | 05 |
| `test_invalid_settings_fail_before_any_resource_opens` | 26; §10/11.1 | Невалидные origin/CIDR/deadline/interval/body cap не открывают ресурсы; нет app | 05 |
| `test_runtime_startup_failure_closes_previously_opened_catalog` | 26; §11.1 | Ошибка сборки runtime закрывает уже открытый каталог; нет app | 05 |
| `test_missing_calculation_version_fails_startup_and_closes_resources` | 26; §11.1 | Отсутствующая версия закрывает runtime и каталог в обратном порядке; нет app | 05 |
| `test_catalog_startup_failure_never_opens_runtime` | 26; §11.1 | Ошибка каталога не начинает сборку runtime; нет app | 05 |
| `test_invalid_admission_limit_fails_before_resources_open` | 26; §9.1/11.1 | Нулевой capacity отклонён до открытия; нет app | 05, 10 |
| `test_health_ready_and_shutdown_gate_have_real_business_control` | 26; §11.1/11.3 | Ready/live 200 после сборки, ready/HEAD 503 на shutdown, новый business запрос 503/30; нет app | 05, 12 |
| `test_route_method_head_options_and_hidden_schema_are_exact` | 29; §11.4 | JSON 404, 405/Allow до component, HEAD только health, OPTIONS 405, prod schema скрыта; положительный поиск проходит; нет app | 05, 08–11 |
| `test_local_schema_flag_exposes_only_explicitly_enabled_route` | 29; §11.4 | Schema route только по local/test flag, `app.openapi()` доступен отдельно; нет app | 05 |
| `test_malformed_trusted_forwarding_stops_before_catalog_and_quota` | 29; §10 | Invalid/duplicate XFF/XFP дают 400 до search/limit, затем valid control 200; нет app | 06, 09–10 |
| `test_trusted_chain_and_mapped_ipv6_share_canonical_ip_bucket` | 29; §10 | Trusted chain выбирает первый untrusted hop, mapped IPv6/IPv4 делят bucket; нет app | 06, 09–10 |
| `test_untrusted_spoofed_forwarding_uses_each_direct_peer_bucket` | 29; §10 | Spoofed headers игнорируются, два direct peer имеют отдельные bucket; нет app | 06, 09–10 |
| `test_required_headers_matrix_and_exact_retry_after` | 27; §4.4 | Таблица 200/403/409/413/415/422/429/500/503/504: no-store, server UUID, exact Retry-After; нет app | 06, 08–12 |
| `test_four_http_sequences_emit_ordered_messages_and_one_safe_terminal` | 27; §12, HTTP sequences 001–004 | Реальные component calls, пары send/receive, run_id==request_id, один terminal, без sentinels в HTTP INFO; нет app | 08–11 |
| `test_5xx_timeout_and_disconnect_have_one_warning_terminal_each` | 24/27; §12 | 503/504/cancellation дают ровно один WARNING terminal; нет app | 09, 11–12 |
| `test_shutdown_waits_accepted_nonbuild_request_before_runtime_and_catalog` | 26; §11.3 | Bootstrap/current/places остаются owned до terminal, readiness 503, close runtime→catalog; нет app | 08–09, 12 |
| `test_disconnect_before_commit_cancels_without_sqlite_mutation` | 24; §9.3 | Handler остановлен до save, нет ответа, новый runtime видит empty в том же SQLite; нет app | 11–12 |
| `test_disconnect_during_protected_commit_is_visible_after_restart` | 24/26; §9.3/11.3 | Shielded CAS завершается без ответа в старом socket, новый runtime видит chart_ready; нет app | 11–12 |
| `test_two_waiters_one_real_leader_keep_separate_permits_after_disconnect` | 24; §9.3 | Реальный single-flight leader один для пяти запросов, каждый держит permit; шестой 503 до release, потом новый POST проходит; нет app | 10–12 |
| `test_cancelled_sqlite_session_load_future_blocks_shutdown_close` | 24/26; §9.3/11.3 | После cancel отправленный SQLite future остаётся owned до terminal, новый runtime того же SQLite читает empty; нет app | 12 |
| `test_cancelled_catalog_search_future_blocks_shutdown_close` | 26; §11.3 | Принятый /places и отправленный catalog executor future задерживают close; нет app | 09, 12 |
| `test_cancelled_catalog_lookup_keeps_five_permits_and_shutdown_owner` | 24/26; §9.3/11.3 | Во время живого lookup future пять build держат capacity, шестой 503; shutdown ждёт leaf, новый app/runtime на том же SQLite healthy; нет app | 11–12 |

Для валидируемых deadline/interval/body-capacity значений тест задаёт внутренние
атрибуты `settings` (`body_timeout_seconds`, `build_timeout_seconds`,
`shutdown_grace_seconds`, `reaper_interval_seconds`, `max_body_bytes`).
Это тестовый seam G0 для промта 05, а не утверждение имён env-переменных или
публичного HTTP API. `expose_schema` — local/test flag §11.4.

В `test_two_waiters_one_real_leader_keep_separate_permits_after_disconnect`
используется реальный `ApplicationRuntime`, `ChartArtifactResolver`,
executor-backed calculator и SQLite, а не замена самого single-flight. Уже
существующий
`tests/application/test_application_bootstrap_integration.py::test_runtime_close_waits_for_cancelled_waiter_live_leader`
служит низкоуровневым контролем `runtime.drain()`: он доказывает snapshot
живого leader для одного отменённого waiter, но не ownership HTTP permit,
protected commit или SQLite/catalog futures. Тесты выше проверяют эти границы
раздельно. Они допускают консервативную задержку permit из-за unrelated leader.

30-секундный watchdog, оба unhealthy health и restart поверх одного SQLite уже
проверяет
`test_build_admission.py::test_timeout_is_one_execute_and_restarts_against_same_sqlite_state`.
Тесты промта 04 дополняют его disconnect, leaf и shutdown. Внешний supervisor
и публичный proxy ACL принадлежат deployment M1-12; локальный ASGI harness
проверяет две последовательные app/runtime инстанции, а не процесс ОС.
