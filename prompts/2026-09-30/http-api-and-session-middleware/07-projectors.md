# Промт 07. Чистая birth projection и публичные DTO

**Статус:** не начато. **Зависимость:** промт 05; может идти параллельно 06 в той же ветке без одновременного редактирования файлов.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 07.

## Что и зачем делаем

После restart текущая карта собирается из сохранённого snapshot. Пользователю нужны дата, место и карта, но transport не должен публиковать внутренние расчётные или сессионные поля и заново обращаться к resolver.

## Задача

Расширь только чистую application/session_view проекцией birth из state.birth_input и state.birth_resolved одного snapshot. Сохрани empty/ready/unavailable, проверку StoredChart, stale и отсутствие I/O. В transport создай строго типизированные SessionBootstrapDTO, SessionViewDTO, BirthViewDTO, ChartDTO, PlaceSuggestionsDTO, BuildChartResponseDTO и ErrorDTO с explicit whitelist: порядок points, houses, aspects, natal/cosmogram null-инварианты, warning source/code без message, safe 500 при dangling aspect. BirthViewDTO берёт дату/время/place_id из `birth_input`, display_name из `birth_resolved.canonical_place`; `tz_id` публикуется всегда. При `time_unknown=true` `birth_time` и `utc_offset_seconds` — JSON `null`, без технического noon offset/UTC anchor. При известном времени — `HH:MM` и сохранённое целое смещение. Публикуй только `pre_1970_offset_unverified` с `source="time"` в порядке resolver; `noon_anchor_*` и неизвестные коды исключи. Рассинхронизация time_unknown с отсутствием времени или ненулевые секунды/микросекунды — safe 500 с renew cookie по §7.1/§6.2.

Реализуй только утверждённую Analysis/Lead форму §7: angle `{longitude, sign, degree, minute}`, строковые `aspects[].from/to`, словарь `Aries`…`Pisces` в точном регистре, ссылки с `chart == "natal"` на реально опубликованные ID из 16 points плюс `asc/mc/vertex`. Другой chart, dangling ID или `dsc/ic` в аспекте дают безопасный 500. Для `dsc/ic` сдвинь сохранённый `ZodiacPosition.sign_index` asc/mc на шесть, сохрани degree/minute без повторного округления и нормализуй долготу из сохранённой долготы. В cosmogram `angles=null`, aspect IDs принадлежат опубликованным points. Если утверждённый §7 отличается, останови зависимый DTO-срез и оформи finding; не добавляй новую семантику только в коде. Не используй model_dump внутреннего artifact как HTTP-ответ.

## Приёмка

Существующие и новые tests/application/test_session_view.py и HTTP projector tests, включая четыре BirthViewDTO golden промта 01, зелёные; module-boundary tests не ослаблены. Проверены exact whitelist, новый engine field/point, known/unknown time, stale/unavailable, рассинхронизация, отсутствие resolver/cache/engine и мутации snapshot. Запиши команды и фактический результат.
