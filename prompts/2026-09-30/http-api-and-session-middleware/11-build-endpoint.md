# Промт 11. Build endpoint и ApplicationResult mapping

**Статус:** не начато. **Зависимость:** промты 07–08 и 10.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 11.

## Что и зачем делаем

Явный POST строит либо заменяет карту в живой сессии. Ответ должен показывать только подтверждённый результат: неопределённый commit требует сверки current GET, а AlreadyApplied не может вернуть артефакт проигравшего запроса.

## Задача

После build admission создай owner task для одного принятого `execute`, независимый от отправки ответа. В обычном пути его terminal outcome (Committed, AlreadyApplied, Superseded, InputRequired, typed/unexpected failure) освобождает свой permit ровно один раз; release выполняется в owner terminal path, а не в socket/response `finally`. Это действует уже после промта 11 для последовательных build. Промт 12 добавляет отмену, retained single-flight leader/leaf, protected commit и watchdog без преждевременного release.

После transport validation и admission создай один RunContext с run_id=request_id, UTC started_at и deadline +30 секунд. Вызови ApplicationOrchestrator.execute(BuildNatalCommand, session_id, run) ровно один раз; transport не загружает state ради build и не повторяет resolver/CAS. Реализуй §8 mapping всех ApplicationResult, cookie renew/clear/unchanged, safe INTERNAL_FAILURE и whitelist ChartDTO для Committed. AlreadyApplied возвращает только статус/version. StateCommitFailed сохраняет retryable=true с Retry-After:1, но не допускает automatic POST; BUILD_TIMEOUT и disconnect обрабатывает промт 12.

Проверяй fresh server load на каждом явном rebuild, две вкладки, конкурирующие intents, InputRequired и typed failures. Для AS-HTTP-12: валидный JSON без cookie даёт 409, а ранний отказ build не вызывает admission/Orchestrator; добавь позитивный контроль. Не вводи клиентский state_version/idempotency key или скрытый GET.

## Приёмка

Целевые маршрутные AS-HTTP-11/12/13–20 и обычные последовательные build AS-HTTP-21 зелёные в части доступного поведения; timeout/disconnect/retained work ждут 12, обязательные логовые assertions — 13. Сценарий 10 sessions × 5 build не застревает после пятого завершившегося запроса. У каждого отрицательного mapping есть успешный typed контроль. Журнал и тест подтверждают один execute. Запиши точные команды и оставшиеся RED проверки.
