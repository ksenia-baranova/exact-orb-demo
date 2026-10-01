# Промт 05. App factory, startup, reaper и health

**Статус:** не начато. **Зависимость:** промты 01–04 и Tester review.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 05.

## Что и зачем делаем

HTTP-приложение должно принимать запросы только после готовности runtime и каталога мест, а при остановке сохранить порядок владения ресурсами. Начинаем с composition и наблюдаемого health, чтобы дальнейшие endpoint использовали один жизненный цикл.

## Задача

Сверь HTTP requirements §11, ADR-0039, ApplicationRuntime/BootstrapSettings, SqlitePlaceCatalog.open/aclose и тесты bootstrap. Добавь FastAPI dependency и только необходимые ASGI test/launch dependencies в pyproject.toml. Создай app factory по [G0](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_g0.md) с внедряемыми runtime/catalog factories, UTC clock и единым monotonic scheduler (`now()`/`wait_until(deadline)`), settings validation до открытия ресурсов, один process-local runtime, внешний PlaceSearch/catalog и reaper каждые 15 минут от завершения предыдущего запуска. Reaper ждёт через `wait_until`, а не `asyncio.sleep(900)`; fake scheduler проверяет период, ошибки и shutdown без ожидания реального времени. Ready 200 только после полной сборки; live/ready не читают SQLite на каждом вызове. Ошибка startup закрывает открытое в обратном порядке. Не добавляй второй runtime или скрытые service layers.

Не пытайся доказать весь fail-fast restart здесь: owner registry и watchdog принадлежат промту 12. Для health предусмотрите lifecycle state, который затем сможет перейти в unhealthy. Используй fake clock и управляемый active reaper для проверки overlap/error/stop.

## Приёмка

Целевые startup/health/reaper tests зелёные; invalid settings и dependency failure не оставляют ресурсы открытыми. Запиши команды и фактические результаты. Сохрани несвязанные правки, не делай commit/branch/push/PR без отдельного указания.
