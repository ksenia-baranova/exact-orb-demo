# Промт 04. Контрактные тесты receive, lifecycle, routes и логов

**Статус:** не начато. **Зависимость:** промты 01–03.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 04.

## Что и зачем делаем

Соединение может оборваться, тело приходить медленно, а native расчёт пережить отмену ожидающего запроса. Тесты должны показать, кто владеет реальной работой и когда процесс обязан стать unhealthy, прежде чем появится код shutdown.

## Задача

Сверь HTTP requirements §4.3, §9.3, §11–13, AS-HTTP-23…27/29 и принятое после S0 правило удержания permit; прочитай runtime.drain, ChartArtifactResolver._ensure_singleflight и тест отменённого waiter с живым leader. Через fake ASGI receive, вручную продвигаемый deadline scheduler из G0 и Event/barrier проверь 5-секундный body timeout, disconnect до/после protected commit, живой shielded leader после отмены execute, двух waiters одного leader с отдельными permit, отмену во время SQLite session load и catalog lookup с ещё работающим executor future, 30-секундный watchdog, оба health 503, модель supervisor restart, reaper без overlap и shutdown без close под активной задачей. Публичный oracle permit — при пяти занятых слотах шестой build получает `503 BUILD_CAPACITY_EXHAUSTED`, пока общий расчёт или отправленный leaf ещё жив; после завершения удерживаемой работы и фактического release новый build проходит. Unrelated leader вправе задержать release отменённого waiter, если S0 подтвердит консервативный snapshot; тест не требует раннего release. Приватный счётчик только дополнительный. `runtime.drain()` можно проверять как кандидат на безопасный общий snapshot и механизм shutdown, но не как точный per-request signal и не как сигнал для SQLite/catalog futures. Для AS-HTTP-26 новый app/runtime использует тот же временный SQLite-файл. Отдельно зафиксируй route/HEAD/OPTIONS/schema, malformed/spoofed XFF и общий bucket для IPv4-mapped IPv6 и IPv4.

Сопоставь обязательные http_message send/receive и terminal log с четырьмя HTTP sequence. Проверь ровно один terminal event на запрос, WARNING для 5xx/timeout/cancellation, и отсутствие уникальных sentinel cookie/IP/даты рождения/query во всех INFO записях. Для AS-HTTP-27 проверь таблицу no-store, X-Request-ID и точных Retry-After на 200/4xx/5xx; для AS-HTTP-29 добавь корректную trusted chain как positive control. Не позволяй тесту пройти, если компонент вообще не вызван. Не добавляй произвольных timeouts как доказательство порядка.

## Приёмка

Запусти целевые тесты, перечисли ожидаемые падения с таблицей `тест → AS/требование → причина RED → implementation-промт` и передай тесты 01–04 на короткий Tester review до production code. Test-only commit предусмотрен Experiment 002, но без отдельной команды пользователя его не создавай.
