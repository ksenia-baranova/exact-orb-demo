# Промт 07a. Поправки transport и lifecycle после независимого ревью 05–07

**Статус:** исполнен до промта 08; evidence в implementation plan §16. **Ветка:** `dev/http-api-and-session-middleware`.
**Источник:** ревью промтов 05–07 другой моделью, переданное пользователем 2026-10-01. Пользователь отдельно выбрал вариант A передачи каталога. Формальный Tester review ранее отменён; этот промт не объявляет его выполненным.
**Основание:** [implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), [G0](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_g0.md), HTTP requirements §4.1–4.4, §5, §7.3, §8.2, §11 и AS-HTTP-26/27/29.

## Что исправить

1. Закрепи выбранный вариант A в G0 и `create_app`: lifespan сначала открывает каталог, затем вызывает `runtime_factory(catalog)` с этим же экземпляром. Сохрани обратное закрытие, включая отказ runtime startup. Обнови все тестовые фабрики; тест async factory проверяет identity аргумента. Реальный single-flight тест использует один каталог для runtime и приложения. Публичный `build_application_runtime(places=...)` не меняй.
2. Для 404, 405 и необработанного исключения выдавай безопасный `ErrorDTO` через `JSONResponse(dto.model_dump(mode="json"))` с `Cache-Control: no-store` и новым серверным `X-Request-ID`; 405 сохраняет `Allow`. Не публикуй `detail`, traceback и входные данные. `RequestValidationError`, если возникнет из FastAPI, также отображай в безопасный 422 `INVALID_REQUEST`. Route resolution по-прежнему предшествует business boundary.
3. Замени искусственный `asyncio.CancelledError` при `http.disconnect` отдельным типизированным `ClientDisconnected`. Обработай его без HTTP-ответа; настоящий task cancellation должен остаться различимым и не подавляться. Детерминированно проверь disconnect до первого и между body events и положительный запрос без disconnect.
4. Отклоняй непустой query string у POST после media/body/schema validation, до cookie/admission. Позитивный POST без query должен проходить.
5. Если reaper task уже завершилась исключением, shutdown логирует безопасный исход и завершает освобождение ресурсов, устанавливая `STOPPED` и terminal log без повторного выброса того же исключения. Не поглощай внешнюю отмену. Ошибки отдельных `reap_expired` runs продолжают допускать следующий run. Health-политику при поломке scheduler не меняй молча: требования §11.1 описывают live 503 через fail-fast watchdog, а код сейчас делает то же при аварии reaper task. Зафиксируй конфликт как открытый для Analysis. Неограниченное ожидание зависшего active reaper передай в промт 12 вместе с общим shutdown grace/fail-fast решением; не добавляй отдельный произвольный timeout.
6. Зафиксируй прямые import-границы: `http_api` не импортирует `swiss_backend`, session/birth adapters; `application` не импортирует `http_api`. Допустимый импорт `engine.ephemeris.types` в projector сохрани. Дополни docstring `SessionBirthView`: при неизвестном времени сохранённый offset относится к техническому anchor и отсекается публичным projector.
7. В `error_response` используй `clear_cookie` для invalid/duplicate required-session cookie с атрибутами `__Host-` cookie. Маршруты 08–11 обязаны принимать только `Request`, не позволять FastAPI повторно читать body и рендерить все `ErrorDTO` непосредственно через JSONResponse. Отдельно зафиксируй это как критерий будущих маршрутов; не создавай их сейчас.

## Границы и приёмка

- Исторические промты 05–07 и 04a не редактируй; это отдельный поправочный срез. Не создавай бизнес-маршруты, admission, сетевые вызовы, compatibility aliases или новый ресурсный слой.
- Не принимай без решения Analysis новый публичный код для unhealthy, отсутствие `birth_time` и отсутствие ASGI peer. Порядок первого невалидного поля `_build_body` допустим. Одиночный сбой tzdata при полном pytest сохрани в evidence как известное ограничение до промта 13.
- Добавь regression-тесты с позитивными контролями для исправленных дефектов. Запусти целевые тесты 05–07, module boundaries и `git diff --check`; полный pytest — если нужен для проверки новых рисков, с точным разделением ожидаемых RED будущих маршрутов.
- Запиши фактические результаты и оставшиеся ограничения в implementation plan. Коммит, push и PR не создавай без отдельного указания.
