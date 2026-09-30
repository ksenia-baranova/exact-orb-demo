# Промт 09. Поиск места

**Статус:** не начато. **Зависимость:** промты 06–07; IP admission подключается в 10.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 09.

## Что и зачем делаем

Пользователь ищет место по каталогу, но координаты и timezone остаются внутренними фактами resolver. Поиск не требует cookie и не должен касаться session storage.

## Задача

Реализуй GET /places с обязательным query, raw query length до нормализации, строгим limit 1..20 и default 10. Вызови PlaceSearch.search ровно один раз; PlaceSuggestions, InvalidPlaceQuery и PlaceCatalogUnavailableError переведи в §6.3/§8 ответы. Projector публикует только place_id, display_name, admin1_name, country_code. Не повторяй нормализацию в transport и не выполняй lookup для suggestions.

Подключи place IP window после промта 10; до него не объявляй AS-HTTP-21 полностью прошедшим. Добавь негативный контроль отсутствия cookie/session/Orchestrator и позитивный реальный вызов search.

## Приёмка

AS-HTTP-08…10 целевого пути зелёные, кроме честно отмеченного limiter до промта 10. Запиши команды, outcome и отсутствие координат/tz в JSON.
