# Промт 01. Контрактные тесты bootstrap и current

**Статус:** не начато. **Ветка:** dev/http-api-and-session-middleware. **Зависимость:** закрытый Gate A (Analysis → Development) implementation plan после S0/G0.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 01.

## Что и зачем делаем

Пользователь должен получить живую анонимную сессию и отдельно прочитать сохранённую карту после возврата. Тесты фиксируют разделение операций до появления HTTP-кода: bootstrap не должен скрыто считать карту или подменять ошибку чтения созданием новой сессии.

## Задача

Используй [карточку G0](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_g0.md): `conftest.py` создаёт fixture с импортом `create_app` внутри неё, заданными точками инъекции и общим scheduler. Чистые unit-тесты не зависят от отсутствующего transport.

Сверь план, HTTP requirements §4–8 и AS-HTTP-01…07, ADR-0040/0041, session sequence 001–003/006, ContextService, session_view и существующие application/session tests. Создай только тестовую инфраструктуру tests/http_api/ и проверки AS-HTTP-01…07. Production code не меняй. Сохрани существующие правки дерева; не создавай commit, branch, push или PR.

Проверь первый create и live restore, persisted chart после restart и empty/stale/unavailable current, SessionAbsent против StateReadFailed, duplicate/invalid cookie, три collision и creation rate. Structural aggregate corruption даёт 503, а не `chart_unavailable`. Если старая cookie указывает на SessionAbsent, гаси её даже при последующем отказе creation admission/create; новую не выдавай. Для AS-HTTP-02 создай два приложения с новыми runtime/cache поверх одного временного SQLite-файла сессий; fake ContextService здесь не доказывает restart. Spy на resolver/cache/engine подтверждает отсутствие пересчёта. Для остальных случаев управляемые fake context/clock отмечают точные вызовы. Для каждого отказа добавь успешный контроль того же пути. Проверяй отсутствие Orchestrator, resolver, cache, engine и CAS на чтении.

Cookie проверяй как raw `Set-Cookie`: имя `__Host-exact_orb_session`, 43 URL-safe символа, `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=604800`, без `Domain`. Для duplicate отключи client cookie jar и передай сырой `Cookie` header с двумя значениями. Отдельно проверь unexpected projector failure в current: safe 500 с renew cookie, не `chart_unavailable`; успешный current служит positive control.

Добавь golden `SessionViewDTO` для `chart_ready` и `chart_unavailable` с известным временем (`HH:MM`, числовой offset, допустимый `pre_1970_offset_unverified`) и неизвестным временем (оба поля `null`, `tz_id` есть, `noon_anchor_*` нет). Exact whitelist сравни с §7.1/AS-HTTP-28. Рассинхронизация `time_unknown` и ненулевые секунды сохранённого времени дают safe 500 с renew cookie; рядом проверяй успешный current.

## Приёмка

Покажи точную команду целевых тестов и ожидаемые падения из-за отсутствующего transport, а не skip. Для каждого теста зафиксируй AS/требование, конкретную причину RED и будущий implementation-промт; одинаковый setup import failure не является достаточным evidence. Зафиксируй карту AS-HTTP-01…07 и BirthViewDTO части AS-HTTP-28 в плане/журнале. Логовые assertions `http_cookie_replaced(missing)` AS-HTTP-01 и ERROR `chart_unavailable` AS-HTTP-03 остаются RED до промта 13. Перед production code тесты 01–04 передаются Tester; test-only commit только после отдельного разрешения пользователя.
