# G0 — контракт тестового шва HTTP API

**Статус:** действующий тестовый шов; уточнён промтом 07a после независимого ревью другой моделью. Обязательный Tester review отменён пользователем.
**Ветка:** `dev/http-api-and-session-middleware`.
**Основание:** [implementation plan](http_api_and_session_middleware_implementation_plan.md) §4,
[HTTP requirements](../../requirements/http_api.md) §7.1, §9.1, §13.

## Что фиксируем до промта 01

Публичная точка сборки — `exact_orb.http_api.app.create_app`. Для тестового
шва её вызывают с именованными параметрами `settings`, `runtime_factory`,
`catalog_factory`, `utc_clock`, `scheduler`, `limiter_policy=None`. Фабрики
вызываются при входе в lifespan: `catalog_factory() -> catalog | Awaitable[catalog]`,
затем `runtime_factory(catalog) -> runtime | Awaitable[runtime]`. В runtime
передаётся тот же открытый каталог, который используют HTTP-маршруты;
владельцем его закрытия остаётся lifespan. Отсутствующая
`limiter_policy` означает утверждённые production defaults §9.1; переданная
immutable policy разрешена только в тестах. Сигнатура runtime factory
уточнена после независимого ревью промтов 05–07; компонентные API не менялись.

Общий тестовый построитель `http_settings(**changes)` в `tests/http_api/conftest.py`
передаёт всем app-сценариям одинаковые значения: `allowed_origins=("https://testserver",)`,
`trusted_proxy_cidrs=()`, `public_origin="https://testserver"`,
`body_timeout_seconds=5`, `build_timeout_seconds=30`,
`shutdown_grace_seconds=30`, `reaper_interval_seconds=900`,
`max_body_bytes=16 * 1024`, `expose_schema=False`. Отдельные тесты меняют
только явно названные поля. Это тестовые значения, не новый набор
production defaults. Недопустимые app settings и limiter policy дают
типизированный `HttpAppConfigurationError(ValueError)` до открытия ресурсов;
исключение из вызываемой фабрики после cleanup сохраняет свой тип.

Чистый ChartDTO projector при нарушении ссылочной целостности аспекта выдаёт
`ChartProjectionError(ValueError)`; HTTP boundary превращает его в безопасный
`500 INTERNAL_FAILURE`. Это тестовый контракт ошибки projector, не новое
публичное поле ответа.

`tests/http_api/conftest.py` предоставляет fixture для фабрики приложения,
HTTPS ASGI-клиента, raw ASGI receive/peer/headers, UTC clock, управляемого
monotonic scheduler и отдельного persistent SQLite restart harness. Импорт
`create_app` выполняется **внутри fixture**, после её создания; на collection
tests не падают из-за отсутствующего transport. Fixture не подменяет
проверяемый route, admission или projector. Чистые unit-срезы DTO/limiter
запускаются независимо от app fixture. До промта 05 тесты, которым нужно
приложение, ожидаемо падают на setup с одинаковым `ModuleNotFoundError`;
перенос импорта в fixture предотвращает только ошибку collection. Такой RED
доказывает отсутствие app, но не проверяемое поведение. Доказательство до
реализации дополняют таблица `тест → AS → ожидаемая причина RED → промт GREEN`
и независимо запускаемые unit-срезы. Позитивные контроли закладываются в
тесты 01–04 и проверяются по мере появления app и маршрутов после промта 05.

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

Исторически Tester должен был сверить этот тестовый шов с контрактом, таблицу
причин RED, независимые unit-срезы и позитивные контроли; обязательный review
пользователь отменил. Одинаковый setup failure app-зависимых
тестов до промта 05 не считается достаточным RED evidence.
Фактические изменения и проверки G0 записываются в implementation plan;
наличие этой карточки само по себе не доказывает реализацию.
