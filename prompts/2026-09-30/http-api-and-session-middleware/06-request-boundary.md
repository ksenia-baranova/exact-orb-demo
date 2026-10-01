# Промт 06. Raw request boundary, trusted proxy и validation

**Статус:** не начато. **Зависимость:** промт 05.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 06.

## Что и зачем делаем

Одинаковый запрос должен получать одинаковый отказ до вызова базы или расчёта. Клиентский IP для лимитов можно брать только из исходного peer и строго проверенной цепочки trusted proxy.

## Задача

До появления business routes не создавай production-заглушек будущих endpoint. Общий pipeline §4.1 проверяй unit-срезом либо test-only route в fixture; полную таблицу 404/405/Allow для реальных маршрутов заверши после 08/09/11. HEAD на health отражает статус GET, HEAD business route и OPTIONS дают 405 с корректным `Allow`. Health исключён из Origin gate. `408 BODY_RECEIVE_TIMEOUT` содержит `Retry-After: 1`; клиентский `X-Request-ID` не переиспользуется. Startup отвергает включённый proxy mode без allowlist trusted CIDR.

Реализуй порядок HTTP requirements §4.1 и §10: route resolution, lifecycle gate, raw ASGI peer, XFF/XFP только от trusted CIDR, Origin для всех business endpoints, media/encoding, wire-size и 5-секундный body receive, JSON/query grammar. Body deadline отсчитывай через внедрённый в G0 `now()/wait_until(deadline)` scheduler от первого ASGI body event; не обходи его `asyncio.wait_for` или неподменяемым framework timeout. Проверяй именно raw headers: дубликаты XFF/XFP и Cookie не должны теряться в framework parser. Для недоверенного peer игнорируй spoofed forwarding headers. Нормализуй IPv4/IPv6/mapped IPv6 перед bucket key. Серверный proxy-header rewrite отключается в поддерживаемом launch path.

Покрой ошибочный приоритет 404/405, 503 shutdown, 400 XFF, 403 Origin, 415 encoding/media/charset, 408/413 body и 422 schema попарной матрицей; ни один ранний отказ не должен вызвать admission или компонент. В тестах используй fake ASGI receive и вручную продвигаемый scheduler; timeout не доказывай sleep. Общие no-store/X-Request-ID и safe ErrorDTO используй из проектора после промта 07 либо временно проверяй только уже доступные поля без заглушек будущего поведения.

## Приёмка

Целевые tests AS-HTTP-12/23/27/29 зелёные в части общего boundary; route-specific 404/405/Allow, build AS-HTTP-12, DTO и логовые assertions остаются RED до 08/09/11/13. Позитивный trusted/untrusted контроль проходит. Не вводи CORS wildcard, IP в INFO или серверную очередь. Отчитайся о командах и оставшихся красных тестах следующих промтов.
