# Промт 03. Контрактные тесты build, recovery и admission

**Статус:** не начато. **Зависимость:** промты 01–02.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 03.

## Что и зачем делаем

Построение карты имеет лимиты, конкурентный CAS и исходы, которые нельзя безопасно повторять автоматически. Тесты фиксируют поведение до реализации, чтобы один HTTP-запрос не превратился в два execute, а неопределённый commit не был объявлен неуспешным.

## Задача

Для AS-HTTP-21 через малую policy проверь разные моменты допуска исчерпанных session/IP bucket, выбор позднего bucket, равенство с tie-breaker session перед IP и сутки перед часом, одновременный rate+capacity с ответом 429 без расхода, а также допуск ровно на границе со списанием всех четырёх bucket и permit (§9.1/FIND-HTTP-022).

Сверь HTTP requirements §6.4, §8–9, AS-HTTP-16…22, ADR-0013 и действующие orchestrator tests. Добавь контрактные тесты explicit rebuild, две вкладки, Committed/AlreadyApplied/Superseded с точным телом `already_applied`, SessionAbsent, StateCommitFailed и BUILD_TIMEOUT recovery. Серверный oracle AS-HTTP-17 — поздний POST A делает fresh load N+1; локальный экран вкладки относится к приёмке UI M1-7 по `docs/ui_ux/requirements.md` §5. Для AS-HTTP-19 сервер доказывает один `execute` на принятый POST и recovery через новый app/runtime поверх того же SQLite; отсутствие автоматического второго POST проверяется UI M1-7. Включи все session/IP rolling windows, CGNAT, пять active permit и шестой быстрый отказ, атомарную reservation, удаление неактивных buckets и точный Retry-After. Границы больших окон проверяй через инъекцию малой immutable limiter policy в тесте, отдельно утверждай production defaults §9.1; тестовая policy не становится поддерживаемым env override. Используй управляемый deadline scheduler из G0, Event/barrier и typed application results.

Отрицательные проверки дополни позитивным вызовом того же пути. Публичный oracle capacity: при пяти занятых permits шестой build получает `503 BUILD_CAPACITY_EXHAUSTED`, а после terminal release одного permit новый build проходит; приватный счётчик только дополнение. Для timeout ответа проверяй ровно один `execute` в принятом POST, `retryable=false`, `Retry-After: 5` и отсутствие `Set-Cookie`; при disconnect ответа нет — проверяй удержание owner/work без HTTP headers. Для AS-HTTP-19/22 restart создай новое приложение/runtime/cache поверх того же временного SQLite-файла; fake supervisor управляет заменой process, но fake ContextService не заменяет persisted state. Не используй sleep, случайное время или реальную сеть.

## Приёмка

Запусти целевой набор, запиши ожидаемые падения до реализации по каждому тесту, точные команды и AS-HTTP-16…22 coverage. Чистую арифметику окон проверяй отдельно от app factory. Не меняй production code, исторические prompts или существующие golden.
