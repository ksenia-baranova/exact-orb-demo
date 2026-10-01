# Промт 08. Cookie, bootstrap и current chart

**Статус:** не начато. **Зависимость:** промты 06–07.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 08.

## Что и зачем делаем

Открытие приложения восстанавливает живую сессию, а отдельный GET показывает persisted chart. Пользователь не должен терять старую сессию при временном сбое чтения или получать новый ID при каждом refresh.

## Задача

Реализуй __Host-exact_orb_session из 32 случайных байт, точные cookie attributes и проверку ровно одного значения в сырых заголовках. POST /session/bootstrap принимает только {}, делает create или ContextService.load без session_view; три collision attempts максимум. GET /charts/current делает ContextService.load, затем чистый session_view, без Orchestrator и пересчёта. Отрази SessionAbsent, StateReadFailed, corrupt StoredChart, structural aggregate failure и unexpected projector failure точными HTTP/cookie действиями §5–8.

Creation admission подключает только промт 10. Здесь не подменяй его заглушкой и держи соответствующие тесты RED до 10. Логовые assertions `http_cookie_replaced(missing)` и ERROR `chart_unavailable` остаются RED до 13. Не создавай transport session cache и не передавай session_id вне cookie.

## Приёмка

Маршрутные и cookie части AS-HTTP-01…07 зелёные; creation rate ждёт промт 10, события AS-HTTP-01/03 — промт 13. Перечисли эти RED assertions явно. Positive restore доказывает отсутствие resolver/cache/engine, failed read не создаёт новую session. Проверь raw Set-Cookie/clear/unchanged и точные команды тестов.
