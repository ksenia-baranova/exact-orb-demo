# Промт 03 — покрытие и ожидаемый RED

Тесты используют `create_app` только при входе в `app_client`, а production
defaults — при вызове отдельного unit-теста. Поэтому collection и три
независимых контроля работают до реализации transport. Для parametrized
сценариев каждая строка ниже относится к каждому parameter case.

| Тест | AS / контракт | Ожидаемый GREEN и причина текущего RED | Промт |
| --- | --- | --- | --- |
| `test_production_admission_defaults_match_approved_windows` | 21; §9.1 | Значения 300/20/100/300/1500/120 и capacity 5 доступны через immutable `DEFAULT_POLICY`; нет `exact_orb.http_api.admission` | 10 |
| `test_pure_limiter_window_arithmetic_without_app_factory` | 21; §9.1, FIND-HTTP-022 | Чистый `AdmissionController` считает hourly/daily expiry, ceil Retry-After и tie без app; нет `exact_orb.http_api.admission` | 10 |
| `test_explicit_rebuild_uses_fresh_version_and_does_not_echo_old_chart_on_failure` | 16; §6.4, §9.2 | Два явных POST коммитят N+1 с fresh expected, ранняя ошибка не подменяет current; нет app/build route | 05, 11 |
| `test_late_tab_post_fresh_loads_newer_version_without_client_precondition` | 17; §6.4 | Поздний POST вкладки A загружает N+1 и делает CAS N+2; нет app/build route | 05, 11 |
| `test_concurrent_sqlite_intents_map_committed_already_applied_and_superseded` | 18; §8.1 | Реальный SQLite CAS даёт Committed+AlreadyApplied или Committed+Superseded, точное тело `already_applied` без artifact; нет app/build route | 05, 11 |
| `test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart` | 19; §8.1, §9.2 | Оба исхода lost acknowledgement: один execute, внутренний retry save, current на новом runtime и только явный новый POST с fresh expected; нет app/build route | 05, 08, 11 |
| `test_build_session_absent_clears_cookie_without_creating_or_replaying_build` | 20; §8.1 | Отсутствие при load/commit даёт 409+clear, bootstrap создаёт сессию без replay; нет app/routes | 05, 08, 11 |
| `test_small_session_hour_and_day_windows_have_exact_inclusive_boundaries` | 21; §9.1 | Hourly/daily session code, detail, Retry-After и inclusive expiry; нет app/admission | 05, 10–11 |
| `test_small_ip_hour_and_day_windows_share_ip_across_sessions` | 21; §9.1 | Hourly/daily IP limits агрегируют разные session и принимают точно на expiry; нет app/admission | 05, 10–11 |
| `test_later_ip_daily_bucket_dominates_session_hourly_and_recovers_at_boundary` | 21; FIND-HTTP-022 | Более поздний IP daily bucket определяет code/detail/Retry-After; отказ не расходует quota; нет app/admission | 05, 10–11 |
| `test_equal_admission_time_chooses_session_then_daily` | 21; FIND-HTTP-022 | При равенстве момента session раньше IP, daily раньше hourly; нет app/admission | 05, 10–11 |
| `test_place_and_creation_ip_windows_reject_without_consuming_quota` | 21; §9.1 | Оба single-bucket route лимита дают точный Retry-After и допускают на expiry; нет app/routes/admission | 05, 08–10 |
| `test_default_cgnat_many_sessions_and_three_hundred_ip_builds` | 21; §9.1 | 10×5 и 300 build проходят, 301-й блокируется общим IP bucket; нет app/admission | 05, 10–11 |
| `test_direct_peer_ip_buckets_are_independent` | 21; §9.1, §10 | Разные direct peer имеют независимые IP bucket; нет app/admission | 05, 10–11 |
| `test_rate_wins_over_full_capacity_and_neither_rejection_spends_quota` | 21–22; §9.1 | При пяти permits rate даёт 429 первым; на expiry capacity даёт быстрый 503; после terminal release новый build принят; нет app/admission | 05, 10–11 |
| `test_inactive_admission_bucket_storage_is_reaped_after_max_window` | 21; §9.1 | Прошедшие max window ключи удалены; `active_bucket_count` — только lifecycle introspection в тесте, public route подтверждает новый допуск; нет app/admission | 05, 10 |
| `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state` | 19, 22; §9.2–9.3 | 504/unchanged cookie/один execute, unhealthy, новый app/runtime/cache на том же SQLite видит persisted либо empty и допускает новый явный build; нет app/watchdog/routes | 05, 08, 11–12 |
| `test_disconnect_sends_no_headers_and_keeps_owned_permit_until_work_finishes` | 22, 24; §9.3 | До terminal owned work ответа нет, второй build видит занятый permit; после release положительный контроль проходит; нет app/ownership | 05, 10–12 |

`AdmissionController.reserve_build`, `AdmissionRejection` и `DEFAULT_POLICY` —
внутренний тестовый шов для промта 10, не новый публичный HTTP/env contract.

Сейчас проходят `test_window_oracle_is_inclusive_and_selects_latest_bucket_with_ties`,
`test_recovery_result_samples_are_real_typed_application_models` и
`test_real_sqlite_orchestrator_fixture_commits_without_http`. Они подтверждают
арифметику тестовых ожиданий, типизированные образцы и реальный SQLite path;
одинаковый `ModuleNotFoundError` app-тестов сам по себе не доказывает поведение.

Серверный oracle AS-HTTP-17 — fresh load/CAS. Локальное состояние экрана двух
вкладок принадлежит UI M1-7. Серверный oracle AS-HTTP-19 — один `execute` в
принятом POST и новый app/runtime для recovery; отсутствие автоматического
второго POST на стороне клиента также принадлежит UI M1-7.
