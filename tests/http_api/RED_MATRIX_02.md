# Промт 02 — ожидаемый RED до реализации HTTP transport

Параметризации перечислены одной строкой: каждый параметр проверяет те же
приоритет, public code и запрет нижнего component call. Импорт `create_app`
выполняется внутри `app_client`; импорт чистого `project_chart` — внутри
projector-тестов. Поэтому отсутствие transport не ломает collection.

| Тест | AS / требование | Конкретный будущий GREEN; причина текущего RED | Промт |
| --- | --- | --- | --- |
| `test_places_success_and_empty_have_exact_whitelist_without_session_access` | 08; §6.3, §7.1 | `/places` отдаёт только четыре поля item, empty `items=[]`, не читает session; сейчас отсутствует `create_app` | 05, 09 |
| `test_place_limit_boundaries_and_default_reach_search` | 09; §4.2, §6.3 | 1/20/default 10 доходят до `PlaceSearch.search`; нет app/route | 06, 09 |
| `test_invalid_limit_grammar_stops_before_catalog_with_positive_control` | 09; §4.2 | Нестандартные limit дают `LIMIT_INVALID` до search; нет request boundary | 06, 09 |
| `test_missing_duplicate_or_extra_query_parameter_stops_before_catalog` | 09; §4.2, §6.3 | Query cardinality и whitelist останавливают request до catalog; нет boundary | 06, 09 |
| `test_raw_query_length_is_checked_in_unicode_code_points_before_catalog` | 09; §4.3 | 513 decoded code points дают `QUERY_TOO_LONG` до normalization; нет boundary | 06, 09 |
| `test_place_component_outcomes_map_to_safe_http_and_keep_positive_control` | 10; §6.3 | `InvalidPlaceQuery`/catalog unavailable/unexpected различаются как 422/503/500; нет place route/mapping | 07, 09 |
| `test_wrong_origin_blocks_current_and_places_but_not_health` | 08, 12; §4.4 | Origin gate предшествует load/search, health его минует; нет boundary/routes | 05–06, 08–09 |
| `test_post_media_and_charset_are_strict_with_valid_control` | 12; §4.2 | Только JSON с отсутствующим/UTF-8 charset доходит до create; нет boundary | 06, 08 |
| `test_any_content_encoding_is_rejected_before_session_create` | 12; §4.2 | Любой Content-Encoding даёт 415 до create; нет boundary | 06, 08 |
| `test_matched_route_validation_priority_stops_before_lower_layers` | 12, 23; §4.1–4.3 | Матрица 503 > 400 > 403 > 415 > 408/413 > 422 с raw receive и управляемым scheduler; нет boundary и lifecycle | 05–06, 08, 12 |
| `test_place_id_code_point_boundaries_and_positive_build_path` | 12; §4.3, §6.4 | 0/129 отклонены, 1/128 проходят без приведения типов; нет build route/schema | 06, 11 |
| `test_build_schema_rejects_malformed_or_extra_fields_before_orchestrator` | 12–13; §4.2, §7.3 | Дата, время и extra field дают точные issue field IDs до execute; нет build schema | 06, 11 |
| `test_malformed_or_nonobject_json_precedes_missing_cookie` | 12; §4.1 | 422 до 409, valid JSON без cookie даёт 409; нет boundary/build route | 06, 08, 11 |
| `test_build_never_coerces_nonstring_json_values` | 12; §4.2 | Число, boolean, array не становятся строкой; нет schema | 06, 11 |
| `test_calendar_valid_domain_dates_reach_application_as_typed_issues` | 13; §4.2, §8.1 | Future/outside/skipped date проходят schema и возвращают typed issues; нет route/mapping | 06, 11 |
| `test_valid_ephemeris_boundary_dates_reach_real_resolver_after_schema` | 13; §4.2 | Валидные граничные даты достигают настоящего Handler и resolver stub; нет route | 06, 11 |
| `test_input_required_keeps_typed_issues_and_renews_cookie` | 14; §8.1 | Unknown place/ambiguous time сохраняют issue и renew; нет result mapping | 08, 11 |
| `test_application_typed_failures_keep_allowed_fields_and_cookie_policy` | 14; §8.1 | Resolution/calculation/read/commit typed failures имеют верные status/detail/cookie; нет result mapping | 08, 11 |
| `test_internal_application_subtypes_are_hidden_by_safe_500` | 15; §8.1 | Internal subtype скрыт; typed calculation detail сохранён; нет safe mapping | 07, 11 |
| `test_forbidden_angle_aspect_in_stored_chart_is_safe_500_with_valid_control` | 15, 28; §7.2 | Engine-valid, но запрещённая для DTO ссылка на `dsc` даёт safe 500 при GET current; валидная карта проходит; нет projector/route | 07, 10 |
| `test_http_build_commits_state_and_stored_chart_atomically_with_real_orchestrator` | 11; §6.4, ADR-0041 | Natal/cosmogram сохраняют одну согласованную пару в реальном SQLite, ранняя 422 ничего не пишет; нет build route | 07, 11 |
| `test_chart_dto_exact_golden_and_no_internal_fields` | 28; §7.2 | Точный golden/whitelist natal и cosmogram; нет `project_chart` | 07 |
| `test_all_published_point_ids_have_fixed_order_and_12_sign_dictionary` | 28; §7.2 | 16 ID и 12 знаков в утверждённом порядке/регистре; нет projector | 07 |
| `test_unknown_engine_point_and_field_are_not_published` | 28; §7.2 | Неизвестное engine поле/точка не попадают в DTO; нет projector | 07 |
| `test_invalid_aspect_owner_or_endpoint_is_refused_with_valid_control` | 28; §7.2 | Transit, hidden point, `dsc/ic` ссылки отклоняются; нет projector | 07 |
| `test_opposite_angles_copy_saved_minutes_at_rounding_boundary` | 28; §7.2 | `dsc/ic` берут знак по `sign_index`, сохраняют minute и нормализуют longitude; нет projector | 07 |

Независимые проверки `test_chart_sample_goldens_are_model_validated_without_transport`,
`test_stored_forbidden_angle_aspect_reaches_projector_validation` и
`test_full_baseline_artifact_is_accepted_by_real_build_handler` проходят сейчас:
они подтверждают, что входные артефакты и leaf-fixtures пригодны. Одинаковый
`ModuleNotFoundError` app-зависимых тестов сам по себе не подтверждает их
поведение; наблюдаемые assertions и позитивные контроли перечислены выше.

`AS-HTTP-28`: чистый projector-тест использует `model_copy` для недопустимой
DTO-ссылки и требует отказа. Ссылка на `dsc` существует в engine angles и
проходит codec/session_view, поэтому отдельный HTTP-тест проверяет safe 500.
Ссылка на отсутствующий даже для engine point отклоняется раньше, при
`decode_chart_artifact`, как `chart_unavailable`; этот случай не может
проверить projector через сохранённую карту.

## Фактические проверки перед test-only коммитом

| Команда | Результат |
| --- | --- |
| `python -m compileall -q tests/http_api` | exit 0 |
| `python -m pytest tests/http_api -q --tb=no -p no:cacheprovider` | 7 passed, 104 failed: ожидаемый RED до появления transport |
| `python -m pytest tests/http_api -q --tb=line -p no:cacheprovider` | 104 failure с `ModuleNotFoundError: No module named 'exact_orb.http_api'`, 7 passed |

Из семи независимых проходов три относятся к session/G0, четыре — к
chart/projector fixtures (параметризованный handler даёт два случая).
App-зависимые проверки ещё не подтверждают HTTP-поведение; их позитивные
контроли станут исполняемыми после соответствующих implementation-промтов.
