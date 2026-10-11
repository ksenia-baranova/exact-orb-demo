## Ручное ревью реализации ApplicationOrchestrator выявило потерю terminal-события при внутренних сбоях commit-flow

- **Дата обнаружения:** 2026-09-19
- **Кем обнаружено:** владельцем проекта при ручном ревью реализации `ApplicationOrchestrator`
- **Тип:** дефекты реализации observability и нормализации внутренних ошибок
- **Статус:** подтверждены воспроизведением и исправлены корректировкой 9.R1

Связанные источники:

- `docs/requirements/component_responsibilities/exact-orb_application_orchestrator_requirements.md`: UC-13, FR-25, FR-26, AC-29/31/32;
- `src/exact_orb/application/orchestrator.py`;
- `src/exact_orb/application/operation_logging.py`;
- `docs/project_management/application_orchestrator_implementation_plan.md`.

### Основная проблема

Текущая реализация правильно защищает уже созданную commit-задачу от внешней
отмены, но две операции самого координатора находятся между покрытыми
обработчиками исключений:

1. вызов `ContextService.save(...)` и передача результата в
   `asyncio.create_task(...)`;
2. чтение injected clock и сравнение времени перед второй попыткой.

Если в этих точках возникает обычное исключение, оно покидает `execute()`.
Started, load, handler и иногда commit-attempt события уже записаны, но
terminal-событие отсутствует. По потоку lifecycle такая операция остаётся
активной навсегда.

### Дефект 1. Ошибка запуска save-задачи

Вызов `self._context.save(...)` вычисляется до входа в цикл, который ловит
ошибки самой commit-задачи. Нарушение публичного контракта зависимости может:

- бросить исключение непосредственно при вызове `save`;
- вернуть объект, который `asyncio.create_task` не может принять.

Настоящий `ContextService.save` объявлен через `async def`, поэтому его тело
не исполняется при создании coroutine. Тем не менее UC-13 и FR-25 прямо
относят programming defects и нарушения публичного контракта зависимости к
нормализуемым внутренним ошибкам.

Фактическое воспроизведение на `e53404a`:

```text
escaped: RuntimeError("driver misconfigured")
commit attempts: 0
terminal events: 0
```

### Дефект 2. Ошибка clock после первой попытки

После первого `StateCommitFailed` commit-attempt уже записан. Решение о
повторе сравнивает `run.deadline` с результатом `self._clock()` вне защиты.
Naive datetime, значение другого типа или исключение clock приводят к выходу
без результата и terminal-события.

Фактическое воспроизведение на `e53404a`:

```text
escaped: TypeError("can't compare offset-naive and offset-aware datetimes")
saves: 1
commit attempts: 1
terminal events: 0
```

### Корневая причина

Обработка ошибок построена вокруг `await` внешних стадий, но не вокруг всего
commit control-flow. Код предполагает, что создание task и решение о retry не
могут отказать, хотя контракт UC-13 требует нормализовать ошибки координатора
и некорректных зависимостей по достигнутой стадии.

### Принятое исправление 9.R1

1. Ошибка вызова `save` или создания task считается одной фактически начатой
   попыткой commit и получает `unexpected_failure` attempt event.
2. Результат — stage-aware `ApplicationInternalFailure` с
   `handler_status=SUCCESS` и `context_status=COMMIT_FAILED`.
3. Ошибка clock после первого `StateCommitFailed` не создаёт фиктивную вторую
   попытку. Terminal сохраняет одну завершённую попытку и её error code.
4. В обоих случаях пишется ровно один terminal до возврата результата.
5. `CancelledError`, strong reference на начатую commit-задачу и запрет retry
   после отмены не меняются.

### Что этим исправлением не решается

Не принимается общий `except Exception` вокруг всего `execute()`. Ошибка после
подтверждённого `Committed` или `AlreadyApplied` не должна превращать
сохранённую карту в ложный `INTERNAL_FAILURE`. Сбой самого terminal writer
также нельзя гарантированно исправить повторным вызовом того же writer.

Отдельными задачами остаются:

- декомпозиция 407-строчного `execute()`;
- устранение дублирования известных calculation-кодов;
- типизация и runtime-валидация словаря lifecycle outcomes;
- унификация технического traceback для invalid outcomes;
- полнота Handler registry в composition 10.1–10.2.

`run=None` не включён: `RunContext` является обязательным входом доверенной
границы, а без `run_id` невозможно сформировать корректное correlated событие.
Сортировка импортов Ruff также не включена: Ruff не настроен как project gate.

### Критерии подтверждения исправления

- сбой непосредственного вызова `save` нормализован;
- не-awaitable результат `save` нормализован;
- clock exception, naive datetime и значение другого типа нормализованы;
- на каждом пути ровно один started и один terminal;
- после clock failure есть ровно один attempt и нет второго save;
- обычный retry и cancellation-регрессии остаются зелёными.

### Результат исправления

В `ApplicationOrchestrator` защищены вызов `save` вместе с созданием task и
чтение/валидация UTC clock перед retry. Оба пути используют один безопасный
commit-stage `ApplicationInternalFailure`. Реально завершённый
`StateCommitFailed` остаётся в истории первой попытки; clock failure завершает
операцию, не начиная вторую.

Добавлены пять regression-случаев в
`tests/application/test_orchestrator_internal_failures.py`. До исправления все
пять воспроизводили сырые исключения без terminal. После исправления:

```text
target:  5 passed
related commit/retry/cancellation/logging: 226 passed
R:       1482 passed
F:       2401 passed
```

Общий catch, post-commit ошибка terminal writer, декомпозиция `execute()` и
P3-hardening не объявляются исправленными этой записью.
