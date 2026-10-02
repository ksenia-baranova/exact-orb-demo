# Промт 02. Контрактные тесты place, validation и DTO

**Статус:** не начато. **Зависимость:** промт 01.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 02.

## Что и зачем делаем

HTTP-ответ должен содержать только разрешённые поля, а плохой запрос должен остановиться до вызова компонентов. Тесты заранее закрепляют границу между transport validation, компонентным результатом и публичным представлением карты.

## Задача

Используй общий scheduler [G0](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_g0.md) для 408 в матрице §4.1. Отдельный AS-HTTP-11 доказывает атомарное сохранение state и StoredChart для natal и cosmogram; отказ ранней validation не пишет ни одно из них.

Сверь HTTP requirements §4, §6–8, §13 и AS-HTTP-08…15/28, PlaceSearch, ApplicationResult и текущий ChartArtifact. Добавь тесты place success/empty/error, limit и query grammar, build schema/date/domain priority, typed failures и безопасный internal 500. Параметризованная матрица проверяет §4.1 для matched route: shutdown 503 раньше XFF 400, XFF раньше Origin 403, Origin раньше media/encoding 415, 415 раньше body 408/413, body раньше schema 422; ранний отказ не вызывает нижний слой. Для GET current/places чужой Origin даёт 403 без load/search, health Origin не проверяет. POST принимает absent/utf-8 charset, отвергает другой и любой Content-Encoding; `place_id` на 0/1/128/129 code points и лишнее поле с `request.<name>` имеют точный результат.

Новый golden `ChartDTO` в `tests/http_api/` проверяет утверждённую в §7.2 форму angle `{longitude, sign, degree, minute}`, строковые `aspects[].from/to`, whitelist, порядок points/houses/aspects, cosmogram null-поля, unknown engine field/point и dangling aspect reference. Для знаков проверь утверждённый словарь из 12 `Aries`…`Pisces` и регистр, для аспектов — `chart == "natal"`, ссылку только на реально опубликованный ID из 16 points плюс `asc/mc/vertex`, запрет `dsc/ic`. На границе минуты `dsc/ic` получают противоположный sign из сохранённого `sign_index`, а degree/minute без нового округления; долгота нормализуется из сохранённой долготы. Существующие golden не меняй. Проверяй позитивный проход рядом с каждым отрицательным случаем.

Используй уже утверждённые JSON-типы §7.1/§7.2 и реальные компонентные модели/существующие fixtures. Новую публичную форму в тесте не выбирай.

## Приёмка

Тестовые изменения только в tests/http_api/ и необходимых общих fixtures. Запусти целевой набор, перечисли ожидаемые падения от ещё не созданного transport по каждому тесту и проверь git diff --check. Чистый projector unit-срез не зависит от app factory. Код приложения, существующие golden-файлы и прежние промты не правь.
