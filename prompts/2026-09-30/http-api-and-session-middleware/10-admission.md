# Промт 10. Process-local admission

**Статус:** не начато. **Зависимость:** промт 06 и route-срезы 08–09.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 10.

## Что и зачем делаем

Лимиты должны защищать один расчётный слот движка и честно объяснять отказ пользователю. Быстрый отказ по capacity не должен расходовать rate quota, а потеря сокета не возвращает уже потраченный запрос.

## Задача

При одновременном исчерпании сначала оцени rate без мутации, затем capacity. Для нескольких exhausted rate bucket выбери поздний момент допуска; при равенстве session раньше IP, сутки раньше часа. Code/detail и `Retry-After` относятся к доминирующему bucket (§9.1/FIND-HTTP-022). Отказ 429/503 ничего не расходует; после допуска атомарно расходуются все четыре build bucket и permit.

Реализуй §9.1: session create 300/час на IP; build 20/час и 100/24ч на session, 300/час и 1500/24ч на IP; place 120/мин на IP; active build 5 на process. Используй `now()` единого injected monotonic scheduler из G0, атомарную reservation всех build windows+capacity, inclusive expiry boundary, удаление неактивных buckets и exact Retry-After как ceil до момента, когда все исчерпанные buckets пропускают запрос. Для тестов допустима инъекция малой immutable limiter policy; отдельный тест проверяет production defaults §9.1. Не добавляй пользовательский/env override этих значений без решения DP-HTTP-02. Capacity refusal не расходует rate; admitted request расходует его независимо от cache hit/error/timeout/disconnect.

Подключи creation/place limit к готовым маршрутам 08–09 и выдачу typed rejection. Подготовь явный permit handle для owner task промта 11: обычный terminal release реализуется в 11, cancellation/retained work — в 12. Не освобождай permit из response/socket finally. Не добавляй persistent limiter или multi-worker поддержку.

## Приёмка

Численные boundaries, NAT/CGNAT, независимость IP buckets, доминирующий bucket §9.1, шестой active build и positive control проходят на unit-срезе с fake clock/barriers; creation/place route limits работают после интеграции. Последовательные build и 10 sessions × 5 build AS-HTTP-21 ждут terminal release 11; cancel/deadline AS-HTTP-22 ждут 12. Запиши точные команды и оставшиеся RED проверки.
