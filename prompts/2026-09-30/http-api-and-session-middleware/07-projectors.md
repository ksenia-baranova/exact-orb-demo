# Промт 07. Чистая birth projection и публичные DTO

**Статус:** не начато. **Зависимость:** промт 05; может идти параллельно 06 в той же ветке без одновременного редактирования файлов.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 07.

## Что и зачем делаем

После restart текущая карта собирается из сохранённого snapshot. Пользователю нужны дата, место и карта, но transport не должен публиковать внутренние расчётные или сессионные поля и заново обращаться к resolver.

## Задача

Расширь только чистую application/session_view проекцией birth из state.birth_input и state.birth_resolved. Сохрани empty/ready/unavailable, проверку StoredChart, stale и отсутствие I/O. В transport создай строго типизированные SessionViewDTO, ChartDTO, BuildChartResponseDTO и ErrorDTO с explicit whitelist: порядок points, houses, aspects, natal/cosmogram null-инварианты, warning source/code без message, safe 500 при dangling aspect. Для неизвестного времени не выдавай технический noon offset как точное пользовательское время.

Реализуй только утверждённую Analysis/Lead форму §7: angle `{longitude, sign, degree, minute}`, строковые `aspects[].from/to`, словарь `Aries`…`Pisces` в точном регистре, ссылки с `chart == "natal"` на реально опубликованные ID из 16 points плюс `asc/mc/vertex`. Другой chart, dangling ID или `dsc/ic` в аспекте дают безопасный 500. Для `dsc/ic` сдвинь сохранённый `ZodiacPosition.sign_index` asc/mc на шесть, сохрани degree/minute без повторного округления и нормализуй долготу из сохранённой долготы. В cosmogram `angles=null`, aspect IDs принадлежат опубликованным points. Если утверждённый §7 отличается, останови зависимый DTO-срез и оформи finding; не добавляй новую семантику только в коде. Не используй model_dump внутреннего artifact как HTTP-ответ.

## Приёмка

Существующие и новые tests/application/test_session_view.py и HTTP projector tests зелёные; module-boundary tests не ослаблены. Проверены exact whitelist, новый engine field/point, unknown time, stale/unavailable, отсутствие resolver/cache/engine и мутации snapshot. Запиши команды и фактический результат.
