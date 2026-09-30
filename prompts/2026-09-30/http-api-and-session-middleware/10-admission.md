# Промт 10. Process-local admission

**Статус:** не начато. **Зависимость:** промт 06.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 10.

## Что и зачем делаем

Лимиты должны защищать один расчётный слот движка и честно объяснять отказ пользователю. Быстрый отказ по capacity не должен расходовать rate quota, а потеря сокета не возвращает уже потраченный запрос.

## Задача

Реализуй §9.1: session create 300/час на IP; build 20/час и 100/24ч на session, 300/час и 1500/24ч на IP; place 120/мин на IP; active build 5 на process. Используй `now()` единого injected monotonic scheduler из G0, атомарную reservation всех build windows+capacity, inclusive expiry boundary, удаление неактивных buckets и exact Retry-After как ceil до момента, когда все исчерпанные buckets пропускают запрос. Для тестов допустима инъекция малой immutable limiter policy; отдельный тест проверяет production defaults §9.1. Не добавляй пользовательский/env override этих значений без решения DP-HTTP-02. Capacity refusal не расходует rate; admitted request расходует его независимо от cache hit/error/timeout/disconnect.

Подключи creation/place limit к промтам 08–09 и выдачу typed rejection. Permit release пока вызывай только из owner terminal path, который промт 12 завершит; не освобождай из response/socket finally. Не добавляй persistent limiter или multi-worker поддержку.

## Приёмка

Все численные boundaries, NAT/CGNAT, независимость IP buckets, приоритет session/IP limit, шестой active build и positive control проходят с fake clock/barriers. AS-HTTP-07/21/22 зелёные в части admission; запиши точные команды и оставшиеся lifecycle проверки для 12.
