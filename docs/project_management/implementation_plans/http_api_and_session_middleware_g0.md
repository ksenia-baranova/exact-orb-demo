# G0 — контракт тестового шва HTTP API

**Статус:** проект решения Developer для review Tester; Gate A не закрыт.
**Ветка:** `dev/http-api-and-session-middleware`.
**Основание:** [implementation plan](http_api_and_session_middleware_implementation_plan.md) §4,
[HTTP requirements](../../requirements/http_api.md) §7.1, §9.1, §13.

## Что фиксируем до промта 01

Публичная точка сборки — `exact_orb.http_api.app.create_app`. Для тестового
шва её вызывают с именованными параметрами `settings`, `runtime_factory`,
`catalog_factory`, `utc_clock`, `scheduler`, `limiter_policy=None`. Фабрики
без аргументов возвращают готовые runtime и каталог при входе в lifespan;
`runtime_factory` может замыкать открытый каталог. Отсутствующая
`limiter_policy` означает утверждённые production defaults §9.1; переданная
immutable policy разрешена только в тестах. Конкретные внутренние типы
фабрик и модулей уточняются в промте 05 без изменения этих точек инъекции.

`tests/http_api/conftest.py` предоставляет fixture для фабрики приложения,
HTTPS ASGI-клиента, raw ASGI receive/peer/headers, UTC clock, управляемого
monotonic scheduler и отдельного persistent SQLite restart harness. Импорт
`create_app` выполняется **внутри fixture**, после её создания; на collection
tests не падают из-за отсутствующего transport. Fixture не подменяет
проверяемый route, admission или projector. Чистые unit-срезы DTO/limiter
запускаются независимо от app fixture. До появления production app тесты
падают на соответствующем assertion/исполняемом шве, а не одним общим
`ImportError` в `conftest`.

Scheduler имеет ровно два обязательных действия: `now() -> float` возвращает
monotonic время, `wait_until(deadline: float)` ожидает заданный абсолютный
момент и допускает отмену. Тестовый scheduler продвигается вручную и будит
ожидающие задачи; UTC clock задаётся отдельно. Один scheduler обслуживает
5-секундный body receive, 30-секундный build watchdog и ожидание reaper до
15 минут после **завершения** предыдущего run. Тесты порядка используют
`asyncio.Event`/barrier; `sleep`, реальное время и patch event loop не служат
доказательством.

HTTPS-клиент вызывает ASGI app без сетевого listener. Отдельная raw ASGI
fixture сохраняет повторяющиеся Cookie/XFF/XFP заголовки и исходный peer до
framework parsing. Для AS-HTTP-02/19/22/26 два последовательных приложения
имеют разные runtime/cache, но один временный SQLite-файл; fake ContextService
не доказывает восстановление persisted state. Никаких production-заглушек
будущих маршрутов для проверки §4.1 не создаётся: до появления route тесты
проверяют общий boundary на уже зарегистрированном route или тестовом route
в fixture; полный 404/405/Allow проверяется после промтов 08/09/11.

## Утверждённые JSON-фикстуры до RED-тестов

Промт 01 создаёт golden `SessionViewDTO` для `chart_ready` и
`chart_unavailable` в вариантах с известным и неизвестным временем по §7.1.
Промт 02 создаёт golden `ChartDTO` по §7.2. Оба проверяют exact whitelist;
BirthViewDTO также проверяет `null` для неизвестного времени, фильтрацию
`noon_anchor_*`, `tz_id` и safe 500 при рассинхронизации данных. Существующие
golden не меняются. Промт 03 фиксирует порядок отказов и доминирующий bucket
по §9.1 через малую тестовую policy.

## Условие завершения G0

Tester сверяет этот тестовый шов с контрактом и подтверждает, что отдельные
RED-тесты 01–04 можно запустить/проанализировать без общего import failure.
Результат review и закрытие G0 записываются в журнале change; наличие этой
карточки само по себе не закрывает Gate A и не доказывает реализацию.
