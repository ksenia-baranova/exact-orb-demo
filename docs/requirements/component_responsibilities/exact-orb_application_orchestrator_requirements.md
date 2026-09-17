# exact-orb — требования к `ApplicationOrchestrator`

**Статус:** R3.2, рабочая версия требований
**Дата:** 2026-09-16
**Уточнение:** 2026-09-17 — неизменяемый RunContext, строгие поля ответа и однозначное кодирование lifecycle-событий (3.R2).
**Область:** application coordination
**Целевой модуль:** `src/exact_orb/application/orchestrator.py`
**Внешний контракт:** `ApplicationResult` в
`src/exact_orb/application/application_results.py`
**Первый поддерживаемый use case:** `BuildNatalCommand`

**Основание:** ADR-0006, ADR-0009, ADR-0012, ADR-0014, ADR-0020,
ADR-0025, ADR-0026, ADR-0028, ADR-0034; требования к
`BuildNatalHandler`, `session_requirements` §7–8 и P3-acceptance, актуальные
sequence diagrams Build Natal.

Документ описывает целевой контракт. На 2026-09-17 реализованы модели
`ApplicationResult`, политика отказов, logging-функции и ранняя ветка отказа
`ApplicationOrchestrator`. Load/Handler/commit, transport wiring и нагрузочная
приёмка остаются последующим этапам; фактические проверки указаны в журнале плана.

## 0. Решения редакции R3.2

R3.2 сохраняет основной поток R3.1 и уточняет observability-контракт:

1. Владение `RunContext`, routing до load и session bootstrap согласованы с
   ревизией ADR-0006 от 2026-09-15.
2. `asyncio.shield()` сам по себе не считается достаточной реализацией
   защищённого commit: после отмены request-задачи Orchestrator обязан
   дождаться commit-задачи, классифицировать исход и записать terminal event.
3. Отмена до commit получает отдельный observability outcome и не создаёт
   фиктивный `ApplicationResult`.
4. Если отмена замечена до старта второй попытки commit, повтор не начинается;
   уже начатая попытка доводится до классифицированного исхода.
5. Окончательный `StateCommitFailed` возможен после одной либо двух попыток:
   повтор зависит от отмены и `run.deadline`.
6. Проверяются согласованные комбинации всех полей результата, а не только
   тройки статусов; модели результата immutable.
7. Calculation `error_code` остаётся строкой, как в действующем handler
   contract; известные коды имеют фиксированную реакцию, неизвестный код —
   безопасный fallback.
8. `state_version=None` при неподтверждённом commit сохранён; уточнена семантика
   поля и добавлено общее клиентское правило монотонности версии.
9. Владелец ограничения одновременно обслуживаемых запросов — transport /
   composition; это явная предпосылка деградационного профиля.
10. Резервирование `Idempotency-Key` без гарантий удалено. Полноценная
    идемпотентность остаётся отложенной вместе с `BuildAttempt`.
11. Переименование существующего agent-каркаса отделено от реализации
    application-flow; два уровня оркестрации сохраняются.
12. Orchestrator пишет компактные lifecycle-события: начало операции,
    завершение load/Handler, исход каждой начатой попытки commit и ровно одно
    terminal event.
13. События пишутся через штатный structured logging. Отдельный telemetry
    port, глобальный реестр активных `run_id` и внутренние счётчики в R3.2 не
    вводятся; метрики выводятся из событий, а concurrency/queue измеряет
    transport/composition admission controller.

## 1. Назначение и границы

### 1.1. Назначение

`ApplicationOrchestrator` — единая точка координации типизированных
application-команд после транспортного слоя.

```text
Transport / другая входная граница
    │ command + trusted session_id + RunContext
    ▼
ApplicationOrchestrator
    ├─ select Handler by type(command)
    ├─ ContextService.load()
    ├─ Handler.handle()
    └─ ContextService.save()       # только после BuildNatalSuccess
    ▼
ApplicationResult
```

Orchestrator не выполняет предметную работу и не владеет session bootstrap.
Создание сессии и отдельный restore-flow принадлежат transport-слою и
выполняются через `ContextService` по ADR-0006/0009.

### 1.2. Граница Handler и ContextService

Между `BuildNatalHandler` и `ContextService` нет прямого взаимодействия.

Handler:

- получает типизированную команду, immutable `SessionState` и `RunContext`;
- возвращает `BuildNatalOutcome`;
- не получает `session_id`, `ContextService`, `expected_state_version` или
  commit outcome;
- не выполняет persistence, CAS и классификацию commit.

`ContextService`:

- не знает Handler и `BuildNatalCommand`;
- применяет `StateDelta` и классифицирует persistence outcomes;
- не управляет расчётом карты.

Связь проходит только через `ApplicationOrchestrator`.

### 1.3. Публичный контракт

```python
class ApplicationOrchestrator:
    def __init__(
        self,
        *,
        context: ContextService,
        handlers: Mapping[type[Command], Handler],
        clock: Callable[[], datetime],
    ) -> None:
        ...

    async def execute(
        self,
        command: Command,
        *,
        session_id: str,
        run: RunContext,
    ) -> ApplicationResult:
        ...
```

Все входы обязательны. `session_id` разрешён доверенной входной границей.
`run` уже создан; Orchestrator не создаёт fallback, не заменяет объект и
передаёт его Handler по identity.

`RunContext` использует `ConfigDict(frozen=True)`: после создания нельзя
переприсвоить `run_id`, `started_at` или `deadline`, даже корректным значением.
UTC-валидация выполняется при создании; новая операция получает новый объект.
Это не меняет default deadline=None, new() и действующую политику extra.

`clock` возвращает timezone-aware UTC и нужен только для детерминированной
проверки `run.deadline` перед возможным commit retry. Он не подменяет clock
`ContextService`: каждый компонент владеет временем своей операции.

Отдельная telemetry-зависимость в конструктор не передаётся. Orchestrator
пишет безопасные структурированные lifecycle-события через штатный logger;
их контракт определён в FR-26 и §11.5.

### 1.4. Основная последовательность

```text
1. Входная граница подготавливает RunContext и доверенный session_id.
2. Orchestrator пишет `application_operation_started`.
3. Orchestrator выбирает Handler точным dict lookup по type(command).
4. Нет Handler → HANDLER_NOT_REGISTERED; load не вызывается.
5. ContextService.load(session_id).
6. Завершённый load получает `application_stage_finished(stage=load)`.
7. SessionAbsent / StateReadFailed → Handler не запускается.
8. SessionSnapshot → фиксируется original expected_state_version.
9. handler.handle(command, snapshot.state, run).
10. Завершённый Handler получает `application_stage_finished(stage=handler)`.
11. Failure/InputRequired outcome → save не вызывается.
12. BuildNatalSuccess → защищённая commit-стадия.
13. save(session_id, original expected, outcome.delta).
14. Каждая начатая попытка save получает
    `application_commit_attempt_finished`.
15. StateCommitFailed → не более одного точного повтора, если он разрешён.
16. Commit outcome нормализуется в ApplicationResult.
17. Пишется ровно один `application_operation_finished`.
18. Результат возвращается transport; при отложенной отмене вместо возврата
    результата пробрасывается `CancelledError` после шагов 14–17.
```

Routing предшествует load намеренно: конфигурационная ошибка не маскируется
исходом сессии и не вызывает I/O.

### 1.5. Завершение операции

Для команды, изменяющей состояние, успешный Handler не означает успешную
пользовательскую операцию. `SUCCESS` возможен только после `Committed` либо
`AlreadyApplied`.

```text
Handler → BuildNatalSuccess
Context → StateCommitFailed

orch_status    = FAILURE
handler_status = SUCCESS
context_status = COMMIT_FAILED
```

### 1.6. Stateless между запросами

Request-specific значения живут только в frame одного `execute()`. Их нельзя
хранить в mutable instance fields. Реестр Handler неизменяем после startup;
сами Handler и `ContextService` обязаны поддерживать заявленную конкурентность.

Orchestrator не хранит реестр активных `run_id`, историю операций или общие
счётчики. Длительности, число commit attempts, их error codes и признак
отменённой доставки являются локальными значениями текущего `execute()` и
освобождаются после его завершения.

## 2. Сценарии использования

### UC-01. Новый commit

`SessionSnapshot(N) → BuildNatalSuccess → Committed(N+1)` даёт
`SUCCESS / SUCCESS / COMMITTED`, артефакт и версию `N+1`.

### UC-02. Намерение уже применено

`AlreadyApplied(N)` даёт `SUCCESS / SUCCESS / ALREADY_APPLIED`. Дополнительной
записи, load, Handler или retry нет.

### UC-03. Требуются данные

`InputRequired` даёт `INPUT_REQUIRED / INPUT_REQUIRED / LOADED`, issues и
прочитанную версию. Save не вызывается. Не сохраняются `DialogTurn` или
`BuildAttempt`; введённые значения остаются на клиенте.

### UC-04. Resolution недоступен

`ResolutionUnavailable(error_code, retryable)` даёт
`FAILURE / RESOLUTION_UNAVAILABLE / LOADED`. `detail_code` сохраняет код
Handler, пользовательский текст выбирается с учётом `retryable`.

### UC-05. Ошибка расчёта

`CalculationFailed(error_code)` даёт
`FAILURE / CALCULATION_FAILED / LOADED`. Ошибка не превращается в
`InputRequired`; save не вызывается.

### UC-06. Сессия отсутствует при load

`SessionAbsent(reason)` даёт
`SESSION_ABSENT / NOT_STARTED / SESSION_ABSENT` и код
`SESSION_EXPIRED` либо `SESSION_NOT_FOUND`.

### UC-07. Ошибка чтения

`StateReadFailed(error_code)` даёт `FAILURE / NOT_STARTED / READ_FAILED`.
Один read failure не доказывает утрату persisted-сессии.

### UC-08. Сессия исчезла при commit

После успешного Handler `SessionAbsent(reason)` даёт
`SESSION_ABSENT / SUCCESS / SESSION_ABSENT` и
`SESSION_LOST_DURING_OPERATION`. Клиент заново проходит session bootstrap и
может повторно отправить сохранённые поля только с новой живой сессией.

### UC-09. Commit не подтверждён

После `StateCommitFailed` Orchestrator проверяет отмену и deadline. Если
повтор разрешён, он выполняется один раз с той же delta и исходным expected.
Повторный `StateCommitFailed` окончателен. Если повтор запрещён, первый
`StateCommitFailed` окончателен. В обоих случаях итог —
`FAILURE / SUCCESS / COMMIT_FAILED`, без артефакта в результате.

При разных `error_code` двух попыток `detail_code` результата содержит код
последней попытки; `application_commit_attempt_finished` фиксирует исход
каждой попытки, а terminal event содержит сводный список кодов обеих попыток.

### UC-10. Результат superseded

`Superseded(actual)` даёт `SUPERSEDED / SUCCESS / SUPERSEDED` и
`actual.state_version`. Запрещены retry, rebase, повтор Handler, новый load и
применение старой delta. Артефакт может остаться в calculation cache.

### UC-11. Handler не зарегистрирован

Load не вызывается. Возвращается `ApplicationInternalFailure` с
`HANDLER_NOT_REGISTERED` и `FAILURE / NOT_STARTED / NOT_ACCESSED`.

### UC-12. Исключение или невалидный outcome Handler

Неожиданное исключение Handler либо объект вне `BuildNatalOutcome` даёт
`ApplicationInternalFailure` с
`FAILURE / UNEXPECTED_FAILURE / LOADED`. Save не вызывается, сырой текст
исключения наружу не передаётся. `CancelledError` нормализации не подлежит.

### UC-13. Исключение вне Handler

| Стадия | `orch_status` | `handler_status` | `context_status` |
|---|---|---|---|
| routing / до load | `FAILURE` | `NOT_STARTED` | `NOT_ACCESSED` |
| вызов load без typed outcome | `FAILURE` | `NOT_STARTED` | `NOT_ACCESSED` |
| commit | `FAILURE` | `SUCCESS` | `COMMIT_FAILED` |

Код — `INTERNAL_FAILURE`; исключение журналируется с `run_id`. Обещание
`ContextService` о typed persistence errors не распространяется на programming
defects, invalid clock и нарушение его публичного контракта.

### UC-14. Отмена до commit

`CancelledError` пробрасывается. Save не начинается, `ApplicationResult` не
создаётся. Orchestrator пишет `application_operation_finished` с
`terminal_kind=cancelled` и достигнутой стадией. Отмена не становится
`InternalFailure`.

### UC-15. Отмена после начала commit

Начатая попытка commit доводится до typed либо internal outcome. Если отмена
наблюдалась до старта повтора, повтор не начинается. Если вторая попытка уже
началась, она также доводится до исхода. Orchestrator классифицирует результат,
пишет `application_commit_attempt_finished` для завершившейся попытки и
`application_operation_finished` с `delivery_cancelled=true`, затем
пробрасывает исходный `CancelledError`.

## 3. Функциональные требования

### FR-01–FR-09. Вход, routing и Handler

- **FR-01.** `RunContext` обязателен; fallback запрещён.
- **FR-02.** Входная граница владеет correlation context; Handler получает тот
  же объект.
- **FR-03.** Routing выполняется до load.
- **FR-04.** Handler ищется точным lookup `handlers.get(type(command))`.
  `isinstance`, MRO, строки, LLM и fallback Handler запрещены.
- **FR-05.** Реестр Handler передаётся при создании Orchestrator и не мутирует
  после startup. Orchestrator делает defensive copy входного mapping и не
  предоставляет runtime registration/replacement. Полнота относительно
  поддерживаемых Command проверяется в composition.
- **FR-06.** После routing выполняется `context.load(session_id)`.
- **FR-07.** После `SessionSnapshot` один раз фиксируется
  `original_expected_state_version = snapshot.state.state_version`.
- **FR-08.** Handler вызывается как
  `await handler.handle(command, snapshot.state, run)`.
- **FR-09.** Handler не получает session persistence и CAS metadata.

### FR-10–FR-18. Outcome и commit

- **FR-10.** `BuildNatalSuccess` ведёт к save; остальные члены
  `BuildNatalOutcome` — нет. Иной тип — internal failure без save.
- **FR-11.** Save получает `session_id`, original expected и `outcome.delta`.
- **FR-12.** Original expected и delta не меняются между попытками.
- **FR-13.** Orchestrator не реализует CAS, `matches_intent`, применение delta,
  назначение версии или дополнительный get.
- **FR-14.** Различаются `Committed`, `AlreadyApplied`, `Superseded`,
  `SessionAbsent`, `StateCommitFailed`.
- **FR-15.** `AlreadyApplied` является успехом без новой записи.
- **FR-16.** `Superseded` запрещает retry и rebase.
- **FR-17.** Handler success напрямую не становится application success.
- **FR-18.** `StateCommitFailed` никогда не превращается в success без typed
  успешного результата последующей попытки.

### FR-19. Точный повтор commit

После `StateCommitFailed` разрешено не более одной второй попытки:

- та же delta и тот же original expected;
- без load и rebase;
- повтор начинается, только если отмена ещё не наблюдалась и deadline не
  истёк;
- результат классифицируется по общей таблице;
- если повтор не начат, исход первой попытки становится окончательным.

### FR-20. Защищённая commit-стадия

Первая попытка, уже начатая вторая попытка, классификация и terminal event не
прерываются внешней отменой request-задачи. Реализация сохраняет сильную ссылку
на commit-задачу и после получения `CancelledError` дожидается её завершения.
Обернуть coroutine только в `asyncio.shield()` без последующего ожидания
недостаточно.

Повторные запросы отмены также не должны оставить commit-задачу без ожидания.
Точный механизм является деталью реализации, но observable порядок закреплён
acceptance-тестом на `asyncio.Event`, без `sleep`.

### FR-21. Бюджет операции

`RunContext` расширяется полем `deadline: datetime | None = None`, UTC aware.
`None` означает отсутствие application deadline. Уже истёкший deadline не
мешает load или Handler в R3.2, но запрещает вторую попытку commit.

Для детерминированной проверки срока Orchestrator получает injected UTC clock.
Clock читается для решения о повторе после первого `StateCommitFailed`; wall
clock напрямую из метода `execute()` не читается. Orchestrator не прерывает
Handler по deadline и не вводит timeout-result.

### FR-22. Статусы и валидность результата

Каждый `ApplicationResult` содержит три уровня статуса. Все конкретные модели
immutable (`ConfigDict(frozen=True)`). Нельзя сконструировать противоречивую
связку:

```text
statuses ↔ code ↔ detail_code ↔ retryable ↔ state_version ↔ payload
```

Проверка одной только тройки статусов недостаточна.

### FR-23. Failure contract

Outcome, требующий реакции, содержит `code`, `detail_code`, `user_message` и
`retryable`. Сырые exception messages не выходят наружу. Открытые множества
resolution/persistence-кодов сохраняются в `detail_code` и используют общий
безопасный текст. Неизвестный calculation-код получает fallback, а его
фактическое значение пишется в WARN.

`retryable=false` запрещает приглашать повторить тот же запрос без изменения
условий. Текст может предлагать другое действие: исправить поля, начать новую
сессию или обратиться позже без обещания успешного повтора.

### FR-24. Отсутствие shared mutable request state

Конкурентные `execute()` не используют общие mutable command, session, run,
snapshot, delta, outcome или result fields.

### FR-25. Неизвестные исключения

Неожиданное исключение журналируется и нормализуется в `InternalFailure` в
соответствии с достигнутой стадией. `CancelledError`, `KeyboardInterrupt` и
`SystemExit` не нормализуются в application failure.

### FR-26. Observability

Все события используют переданный `run.run_id`; второй `run_id` не создаётся.
Orchestrator пишет собственные lifecycle-события через штатный structured
logger. Он не дублирует payload и внутренние события Handler, resolver, engine,
cache или `ContextService`, а фиксирует положение этих вызовов в общем
application-flow.

На каждый начатый `execute()` приходится:

```text
application_operation_started                   # ровно одно
application_stage_finished stage=load            # если load завершился
application_stage_finished stage=handler         # если Handler завершился
application_commit_attempt_finished attempt=N    # на каждый начатый save
application_operation_finished                   # ровно одно
```

`application_operation_started` содержит `run_id` и `command_type` и пишется
на `INFO`. Успешные `application_stage_finished` и успешная первая попытка
commit пишутся на `DEBUG`. `StateCommitFailed`, непредвиденное исключение
commit и выполняемый вслед за ними retry отражаются на `WARNING`; отдельное
событие `retry_scheduled` не требуется, поскольку `attempt=2` однозначно
доказывает начатый повтор.

`application_commit_attempt_finished` содержит `run_id`, номер попытки
`1 | 2`, нормализованный outcome, безопасный `detail_code`, длительность и
достоверный `state_version`, если commit outcome его предоставляет. Событие
появляется только для фактически начатого save. Поэтому отмена или истёкший
deadline до повтора не создают фиктивную вторую попытку.

Каждый вызов `execute()` создаёт ровно один
`application_operation_finished` одного из видов:

```text
result:
  terminal_kind=result, run_id, statuses, code, detail_code,
  state_version, stage durations, commit_attempts, commit_error_codes,
  delivery_cancelled

cancelled-before-commit:
  terminal_kind=cancelled, run_id, cancelled_stage,
  stage durations, commit_attempts=0
```

Terminal event пишется на `INFO` для нормальных application outcomes и на
`WARNING` для `orch_status=FAILURE`. Непредвиденное исключение дополнительно
получает отдельную exception-запись со stack trace по FR-25, но terminal event
всё равно остаётся один. У cancelled-before-commit нет фиктивной тройки
`ApplicationResult`.

Terminal event записывается до возврата `ApplicationResult` или проброса
исходного `CancelledError`. Длительности, commit attempts и error codes
накапливаются только в локальных переменных текущего `execute()`.

Structured events являются источником observability-фактов R3.2. Счётчики
операций по статусам, отмен по стадии, `Superseded`, `StateCommitFailed` и
начатых retry выводятся из event stream. Число активных операций определяется
парой started/finished; максимум конкурентности и очередь принадлежат
transport/composition admission controller и нагрузочному стенду. Orchestrator
не хранит registry активных `run_id`, глобальные counters и не зависит от
конкретного metrics backend.

### FR-27. Персональные данные

Во всех компактных lifecycle events отсутствуют `birth_input`,
разрешённые координаты/время и полный `session_id`. В `user_message` PII нет
никогда. Полные payload доступны только в DEBUG-контракте ADR-0025/0028.
Удалённый M1-профиль по ADR-0034 использует INFO; локальный CLI сохраняет
действующий default DEBUG. Нагрузочная приёмка выполняется при INFO.

## 4. Границы компонентов

### 4.1. Transport → Orchestrator

Transport отвечает за HTTP, cookie, доверенное разрешение и создание
`session_id`, session bootstrap/restore, rate limiting, admission control,
создание/восстановление `RunContext`, transport DTO, serialization и HTTP
status mapping.

Bootstrap/restore — отдельные lifecycle-операции через `ContextService`; они не
заменяют load, принадлежащий выполняемой application-команде. Transport не
вызывает `ContextService` напрямую для reset/delete и других команд.

`Idempotency-Key` в R3.2 не резервируется и гарантий по нему нет.

### 4.2. Orchestrator → ContextService

Используется только публичный `ContextService.load/save`. Прямой доступ к
`SessionStore`, `DialogStore`, adapter или SQLite запрещён.

### 4.3. Orchestrator ↔ BuildNatalHandler

Handler получает команду, immutable state snapshot и тот же `RunContext`.
Возвращает:

```text
BuildNatalSuccess | InputRequired | ResolutionUnavailable | CalculationFailed
```

### 4.4. Orchestrator → Transport

Нормализованный `ApplicationResult` является единственным внешним application
контрактом. Transport не восстанавливает семантику по внутренним outcome.

### 4.5. Agent Runtime

Build Natal не проходит через Agent Runtime, Planner, ToolExecutor или LLM.
Существующий `exact_orb/orchestration/` является отдельным agent-каркасом.
Его возможное переименование не входит в реализацию R3.2.

## 5. Вне ответственности

Orchestrator не отвечает за HTTP/cookie/status mapping; session ID и session
bootstrap; предметный расчёт; resolution; `ChartSpec`; calculation key/cache;
Swiss Ephemeris; применение delta; CAS и новую версию; storage adapters;
Agent Runtime; prompts/LLM; admission policy; durable jobs; `BuildAttempt`;
возобновление после restart; автоматический rebase.

Полноценная идемпотентность по ключу отложена. Последовательный дубль вне
гонки может дать новый `Committed` и увеличить версию. Решение требует
транзакционного хранения ключа и исхода и относится к будущему `BuildAttempt`.

Неуспешные попытки не сохраняются. Deadline передаётся вниз, но Handler в R3.2
Orchestrator по нему не прерывает.

## 6. Нагрузка и ограничение конкурентности

### 6.1. Цель

Build Natal application-flow принимает и завершает не менее 5 operations/s
при штатных зависимостях. Orchestrator не вводит глобальную блокировку или
session mutex. Корректность одной сессии обеспечивает CAS; разные сессии не
разделяют request state.

### 6.2. Владелец admission limit

Ограниченный transport/composition admission controller является
предпосылкой деградационного профиля. Он задаёт конечный предел одновременно
выполняемых application operations и конечную очередь/политику отказа.
Конкретные числовые пределы выбираются deployment configuration и фиксируются
в отчёте прогона.

Orchestrator не создаёт дополнительные фоновые операции, кроме ограниченной
защищённой commit-задачи текущего вызова, и не владеет общей очередью. Без
настроенного admission limit утверждение «конкурентность не растёт
неограниченно» не считается доказанным.

### 6.3. Профиль 1 — штатные зависимости

```text
входящий поток:        5 RPS
длительность подачи:   не менее 60 секунд
подано:                не менее 300 операций
logging:               effective INFO
```

Приёмка фиксирует число поданных и завершённых операций, продолжительность
drain после прекращения подачи и максимум одновременно активных операций.
Все 300 операций должны завершиться допустимым outcome; один лишь факт их
приёма или возврата типизированных failure не доказывает throughput 5 RPS.
Число начатых и завершённых операций и текущая разность между ними выводятся
из `application_operation_started` / `application_operation_finished` при
effective `INFO`; максимум конкурентности дополнительно фиксирует admission
controller либо нагрузочный harness.

Проверяются отсутствие необработанных исключений, смешения `run_id`/delta/
expected между запросами и lost update; корректные CAS-исходы одной сессии;
отсутствие глобальной сериализации Orchestrator. Отчёт указывает долю cache
hit/miss и реальные/fake зависимости прогона.

### 6.4. Профиль 2 — деградация зависимости

Тот же входящий поток выполняется с управляемо замедленным resolver или
persistence при включённом admission limit. Проверяются конечный максимум
активных операций и очереди, заданная реакция admission controller, не более
одного commit retry на операцию, по одному commit-attempt event на фактически
начатый save и ровно один terminal event на вызов.

Отдельные p50/p95/p99 в R3.2 не фиксируются. Профиль не использует `sleep` как
доказательство порядка; задержка управляется fake-компонентом и событиями.

### 6.5. Overhead dialog snapshot

`SessionPersistence.touch` возвращает `SessionSnapshot {state, dialog}`.
Build Natal использует только state. Профиль 1 измеряет долю времени и объёма
dialog. Значимый overhead является условием отдельного state-only контракта
`SessionPersistence`, а не локального обхода в Orchestrator.

## 7. Статусная модель

```text
orch_status:
  SUCCESS | INPUT_REQUIRED | SUPERSEDED | SESSION_ABSENT | FAILURE

handler_status:
  NOT_STARTED | SUCCESS | INPUT_REQUIRED | RESOLUTION_UNAVAILABLE |
  CALCULATION_FAILED | UNEXPECTED_FAILURE

context_status:
  NOT_ACCESSED | LOADED | READ_FAILED | SESSION_ABSENT | COMMITTED |
  ALREADY_APPLIED | SUPERSEDED | COMMIT_FAILED
```

`NOT_ACCESSED` означает, что операция не получила typed session state:
load не вызывался либо вызов завершился исключением до typed outcome.

## 8. Допустимые тройки статусов

| Сценарий | `orch_status` | `handler_status` | `context_status` |
|---|---|---|---|
| Новый commit | `SUCCESS` | `SUCCESS` | `COMMITTED` |
| Намерение уже применено | `SUCCESS` | `SUCCESS` | `ALREADY_APPLIED` |
| Нужны данные | `INPUT_REQUIRED` | `INPUT_REQUIRED` | `LOADED` |
| Resolution недоступен | `FAILURE` | `RESOLUTION_UNAVAILABLE` | `LOADED` |
| Calculation failed | `FAILURE` | `CALCULATION_FAILED` | `LOADED` |
| Session absent при load | `SESSION_ABSENT` | `NOT_STARTED` | `SESSION_ABSENT` |
| State read failed | `FAILURE` | `NOT_STARTED` | `READ_FAILED` |
| Session absent при commit | `SESSION_ABSENT` | `SUCCESS` | `SESSION_ABSENT` |
| Commit не подтверждён | `FAILURE` | `SUCCESS` | `COMMIT_FAILED` |
| Stale result | `SUPERSEDED` | `SUCCESS` | `SUPERSEDED` |
| Handler exception / invalid outcome | `FAILURE` | `UNEXPECTED_FAILURE` | `LOADED` |
| Handler отсутствует / exception до typed load | `FAILURE` | `NOT_STARTED` | `NOT_ACCESSED` |
| Exception на commit | `FAILURE` | `SUCCESS` | `COMMIT_FAILED` |

Таблица является проекцией union §9. Тест проверяет равенство множества троек
и отдельно отклонение противоречивых сочетаний остальных полей.

## 9. Типовая модель результата

```python
ApplicationResult = (
    ApplicationCommitted
    | ApplicationAlreadyApplied
    | ApplicationInputRequired
    | ApplicationResolutionFailure
    | ApplicationCalculationFailure
    | ApplicationSessionAbsent
    | ApplicationStateReadFailure
    | ApplicationStateCommitFailure
    | ApplicationSuperseded
    | ApplicationInternalFailure
)
```

| Модель | `code` | `detail_code` | `retryable` | `state_version` | Payload |
|---|---|---|---:|---|---|
| `ApplicationCommitted` | `OK` | `None` | false | `>= 1` | `artifact` |
| `ApplicationAlreadyApplied` | `OK` | `None` | false | `>= 0` | `artifact` |
| `ApplicationInputRequired` | `INPUT_REQUIRED` | `None` | false | loaded `>= 0` | non-empty `issues` |
| `ApplicationResolutionFailure` | `RESOLUTION_UNAVAILABLE` | Handler code | Handler value | loaded `>= 0` | — |
| `ApplicationCalculationFailure` | `CALCULATION_FAILED` | Handler code | по §10 | loaded `>= 0` | — |
| `ApplicationSessionAbsent` | по стадии/reason | `None` | false | `None` | `reason` |
| `ApplicationStateReadFailure` | `STATE_READ_FAILED` | persistence code | true | `None` | — |
| `ApplicationStateCommitFailure` | `STATE_COMMIT_FAILED` | последний persistence code | true | `None` | — |
| `ApplicationSuperseded` | `RESULT_SUPERSEDED` | `None` | false | actual `>= 0` | — |
| `ApplicationInternalFailure` | `INTERNAL_FAILURE` или `HANDLER_NOT_REGISTERED` | `None` | false | по стадии | — |

Все модели используют `ConfigDict(frozen=True)`. Значения статусов, `code` и
предопределённый `retryable` закрепляются `Literal`. Если одна модель покрывает
несколько строк таблицы, validator проверяет полную разрешённую запись, а не
только пару статусов.

Ненулевая либо нулевая допустимая `state_version` — строгий int: bool, float
и числовые строки отклоняются без приведения. Нижние границы и допустимость
None сохраняются по таблице. Persistence `detail_code` имеет min_length=1,
как error_code исходных session outcomes; открытое множество кодов сохраняется.
`user_message` failure-модели сверяется с точным текстом §10 через единую
политику для её code, reason, стадии и retryable. Произвольная строка,
в том числе иной безопасный текст, не является допустимой заменой.

Глубокая неизменяемость вложенных Issue/ChartArtifact пока не установлена.
Её граница требует отдельного согласования с artifact-контрактом §6.1.4,
который допускает mutable-вложения при глубокой копии на выходе resolver.
До выполнения корректировки 2.R2 AC-24 подтверждён только для присваивания
полям верхнего уровня; его целевая глубокая гарантия не объявляется выполненной.

Пример полного правила для `ApplicationInternalFailure`:

```text
HANDLER_NOT_REGISTERED:
  NOT_STARTED / NOT_ACCESSED
  detail_code=None, state_version=None, retryable=false

INTERNAL_FAILURE до typed load:
  NOT_STARTED / NOT_ACCESSED
  detail_code=None, state_version=None, retryable=false

INTERNAL_FAILURE в Handler:
  UNEXPECTED_FAILURE / LOADED
  detail_code=None, state_version=<loaded>, retryable=false

INTERNAL_FAILURE на commit:
  SUCCESS / COMMIT_FAILED
  detail_code=None, state_version=None, retryable=false
```

`ApplicationSessionAbsent` также связывает стадию и код:

```text
NOT_STARTED → SESSION_EXPIRED | SESSION_NOT_FOUND по reason
SUCCESS     → SESSION_LOST_DURING_OPERATION при любом reason
```

## 10. Человекочитаемые ошибки

`describe_failure` принимает только относящиеся к kind содержательные аргументы:
resolution — error_code/retryable, calculation и persistence — error_code,
session_absent — stage/reason, статические реакции — без дополнительных данных.
Нерелевантное значение не None отклоняется, а не игнорируется. Это не меняет
тексты, retryable чтения/сохранения или fallback неизвестного calculation-кода.

| Условие | `code` | `retryable` | `user_message` |
|---|---|---:|---|
| `InputRequired` | `INPUT_REQUIRED` | false | `Проверьте введённые данные и исправьте отмеченные поля.` |
| Resolution, retryable | `RESOLUTION_UNAVAILABLE` | true | `Не удалось определить данные места и времени. Попробуйте ещё раз.` |
| Resolution, non-retryable | `RESOLUTION_UNAVAILABLE` | false | `Не удалось определить данные места и времени для указанного ввода.` |
| `EPHEMERIS_UNAVAILABLE` | `CALCULATION_FAILED` | true | `Расчёт временно недоступен. Попробуйте ещё раз.` |
| `HOUSES_DEGENERATE` | `CALCULATION_FAILED` | false | `Для выбранных данных невозможно рассчитать дома в текущей системе домов.` |
| `SPEC_INVALID` | `CALCULATION_FAILED` | false | `Не удалось подготовить параметры расчёта карты.` |
| `GEOGRAPHY_INVALID` | `CALCULATION_FAILED` | false | `Не удалось выполнить расчёт карты для выбранного места.` |
| `ENGINE_UNEXPECTED` | `CALCULATION_FAILED` | false | `Не удалось рассчитать карту из-за внутренней ошибки.` |
| Unknown calculation code | `CALCULATION_FAILED` | false | `Не удалось рассчитать карту.` |
| `StateReadFailed` | `STATE_READ_FAILED` | true | `Не удалось загрузить данные сессии. Попробуйте ещё раз.` |
| Final `StateCommitFailed` | `STATE_COMMIT_FAILED` | true | `Не удалось подтвердить сохранение карты. Обновите страницу, чтобы проверить актуальное состояние.` |
| Absent/expired при load | `SESSION_EXPIRED` | false | `Сессия истекла. Введите данные рождения заново.` |
| Absent/not_found при load | `SESSION_NOT_FOUND` | false | `Сессия не найдена. Начните заново.` |
| Absent при commit | `SESSION_LOST_DURING_OPERATION` | false | `Сессия была потеряна до сохранения карты. Введите данные рождения заново.` |
| `Superseded` | `RESULT_SUPERSEDED` | false | `Результат этого запроса уже не актуален. Текущая карта не изменена.` |
| Handler отсутствует | `HANDLER_NOT_REGISTERED` | false | `Не удалось выполнить запрос из-за внутренней ошибки.` |
| Unexpected exception / invalid outcome | `INTERNAL_FAILURE` | false | `Произошла внутренняя ошибка.` |

`CalculationFailed.error_code` в действующем handler contract имеет тип
`str`. Таблица известных кодов определяет `retryable` и текст. Неизвестный код
остаётся `detail_code`, получает fallback и WARN. Добавление известного кода
требует расширить эту таблицу и тесты, но не ломает входной handler contract.

Тексты находятся в application-слое как принятый долг до второго клиента или
языка.

## 11. Контракты сообщений

### 11.1. `RunContext`

```text
run_id: UUID
started_at: datetime              # UTC aware
deadline: datetime | None = None  # UTC aware
```

Валидация `deadline` совпадает с UTC-правилом `started_at`. Deadline может быть
раньше `started_at`: такой запрос допустим, но commit retry запрещён.

### 11.2. Load

```text
ContextService.load(session_id)
  → SessionSnapshot {state, dialog}
  | SessionAbsent {reason: expired | not_found}
  | StateReadFailed {error_code: str}
```

`state.state_version >= 0` сохраняется как original CAS predicate.

### 11.3. Handler

```text
handler.handle(command, snapshot.state, run)
  → BuildNatalSuccess {artifact, delta}
  | InputRequired {issues}
  | ResolutionUnavailable {error_code: str, retryable: bool}
  | CalculationFailed {error_code: str}
```

`Issue.code` использует действующее закрытое множество
`MISSING | AMBIGUOUS | INVALID | UNSUPPORTED`.

### 11.4. Save

```text
ContextService.save(session_id, original_expected_state_version, delta)
  → Committed {state_version >= 1}
  | AlreadyApplied {state_version >= 0}
  | Superseded {actual: SessionState}
  | SessionAbsent {reason}
  | StateCommitFailed {error_code: str}
```

### 11.5. Lifecycle events Orchestrator

Сообщение штатного logger имеет формат `<event> <JSON object>` в одной
физической строке. Имена событий и полей сохраняются; UUID — JSON-строка,
commit_error_codes — массив строк, None — null. Строковые значения, включая
открытые error_code, экранируются стандартным JSON-кодированием; пробелы,
кавычки и управляющие символы не создают новых полей либо записей. Потребитель
разбирает JSON object после имени события, а не ищет key=value регулярным выражением.

`log_operation_finished` получает сам `ApplicationResult` и извлекает только
разрешённые ниже поля. Отдельные status/code/version/run_id для этой функции
не передаются; payload результата и user_message не сериализуются в событие.
Длительности, commit_attempts, commit_error_codes и delivery_cancelled
передаются отдельно; их связь с реально выполненными действиями обеспечивает execute.

Общие поля всех событий:

```text
event: str
run_id: UUID
```

Допустимые события и обязательные поля:

| `event` | Уровень | Поля |
|---|---|---|
| `application_operation_started` | `INFO` | `command_type` |
| `application_stage_finished` | `DEBUG` или `WARNING` | `stage=load\|handler`, `outcome`, `duration_ms`, опционально достоверный `state_version` |
| `application_commit_attempt_finished` | `DEBUG` или `WARNING` | `attempt=1\|2`, `outcome`, `detail_code`, `duration_ms`, опционально достоверный `state_version` |
| `application_operation_finished` | `INFO` или `WARNING` | `terminal_kind` и поля ниже |

Вторая commit attempt и любая попытка с `StateCommitFailed` либо unexpected
exception пишутся на `WARNING`; успешная первая попытка — на `DEBUG`.

Stage event пишется после typed результата, невалидного возвращённого outcome
или нормализованного non-cancellation exception. Ожидаемый typed outcome имеет
уровень `DEBUG`; нарушение контракта и unexpected failure — `WARNING` плюс
отдельная exception-запись по FR-25. Стадия, прерванная `CancelledError`, не
получает ложного finished event.

Result terminal event:

```text
terminal_kind=result
orch_status, handler_status, context_status
code, detail_code, state_version
load_duration_ms, handler_duration_ms, commit_duration_ms
commit_attempts, commit_error_codes
delivery_cancelled
```

Cancelled-before-commit terminal event:

```text
terminal_kind=cancelled
cancelled_stage
load_duration_ms, handler_duration_ms
commit_attempts=0
```

Незавершённая стадия не получает `application_stage_finished`. Длительность
может быть `None`, если стадия не начиналась или не завершилась; отрицательные
и не конечные значения запрещены. `commit_duration_ms` является суммой
длительностей фактически завершённых commit attempts; отдельные attempt events
сохраняют их индивидуальные значения. `commit_error_codes` сохраняет порядок
фактически завершённых попыток и не содержит фиктивных элементов.

Logging-функции проверяют конечность/неотрицательность переданных длительностей,
целочисленные номера attempt=1/2 и commit_attempts=0/1/2 без bool-приведения.
В attempt event committed требует state_version>=1, already_applied/superseded
требуют >=0, остальные commit outcomes не публикуют версию. Некорректные
метаданные вызывают `LifecycleEventError` до записи; значения не обрезаются
и не заменяются фиктивными. Проверка не доказывает соответствия журналу реальных save.

Ошибка подготовки события не является persistence outcome. В будущей
commit-ветке она не должна отменять подтверждённый исход или превращать
Committed/AlreadyApplied в ложный StateCommitFailure. Проверка этого поведения
при сборке commit остаётся отдельной обязанностью этапов 6/8.

Lifecycle events не содержат command payload, `StateDelta`, `ChartArtifact`,
полный `session_id` или персональные данные. Полные boundary payload остаются
отдельными DEBUG-событиями владеющих компонентов по ADR-0025/0028.

## 12. Контракт `ApplicationResult`

Общие поля:

```text
orch_status, handler_status, context_status
code, detail_code, user_message, retryable
run_id, state_version
```

`state_version` — версия, подтверждённая наблюдением, на котором основан
результат:

- `COMMITTED` — новая подтверждённая версия;
- `ALREADY_APPLIED` и `SUPERSEDED` — версия атомарного actual outcome;
- `LOADED` — версия snapshot, на котором работал Handler;
- `NOT_ACCESSED`, `READ_FAILED`, `SESSION_ABSENT`, `COMMIT_FAILED` — `None`.

При `COMMIT_FAILED` исходная прочитанная версия известна внутри операции, но
она не публикуется как версия результата: фактический исход записи неизвестен.
Никакая опубликованная версия не гарантирует отсутствия более позднего
конкурентного commit.

Клиент применяет единое правило для всех ответов с состоянием:

> В пределах одного session lifecycle ответ с меньшим `state_version` не
> заменяет уже показанное состояние с большей версией.

`ApplicationCommitted` и `ApplicationAlreadyApplied` содержат `artifact`.
`ApplicationInputRequired` содержит `issues`. `ApplicationSuperseded` артефакт
не содержит. `ApplicationSessionAbsent` содержит `reason`.

## 13. Application codes

```text
OK
INPUT_REQUIRED
RESOLUTION_UNAVAILABLE
CALCULATION_FAILED
STATE_READ_FAILED
STATE_COMMIT_FAILED
SESSION_EXPIRED
SESSION_NOT_FOUND
SESSION_LOST_DURING_OPERATION
RESULT_SUPERSEDED
HANDLER_NOT_REGISTERED
INTERNAL_FAILURE
```

`OPERATION_CANCELLED` не входит в `ApplicationCode`, поскольку отмена до
commit не создаёт `ApplicationResult`; это значение `terminal_kind` /
`cancelled_stage` observability event.

## 14. Основные инварианты

1. `RunContext` создаётся до Orchestrator и не заменяется.
2. Routing выполняется точным lookup до load.
3. Handler и `ContextService` не взаимодействуют напрямую.
4. Handler получает immutable snapshot и не знает expected version.
5. Save вызывается только после `BuildNatalSuccess`.
6. Original expected и delta неизменны во всех попытках.
7. Orchestrator не реализует CAS или rebase.
8. Success возможен только после `Committed`/`AlreadyApplied`.
9. `Superseded` и `AlreadyApplied` не вызывают retry.
10. После `StateCommitFailed` начинается не более одного повтора.
11. Начатый commit не оставляется без классификации из-за отмены.
12. Отмена до commit не становится application failure.
13. Модель исключает противоречивые сочетания всех полей результата.
14. Build Natal не вызывает Agent Runtime.
15. Orchestrator не разделяет mutable request state между вызовами.
16. Ограничение общей конкурентности принадлежит transport/composition.
17. Compact operation events и `user_message` не содержат PII.
18. Клиент не заменяет более новое session state ответом меньшей версии.
19. Каждый `execute()` пишет ровно один started event и ровно один terminal
    event с тем же `run_id`.
20. Stage и commit-attempt events соответствуют только фактически завершённым
    стадиям и начатым попыткам.
21. Lifecycle observability не требует registry активных `run_id`, глобальных
    counters или telemetry-зависимости Orchestrator.

## 15. Acceptance criteria

1. `execute()` без `run` не вызывается по сигнатуре; fallback отсутствует.
2. Handler получает тот же объект `RunContext` по identity.
3. Точный тип команды маршрутизируется; подкласс не матчится.
4. Unknown command не вызывает load и даёт `HANDLER_NOT_REGISTERED`.
5. Routing предшествует load; load предшествует Handler.
6. `SessionAbsent`/`StateReadFailed` не запускают Handler.
7. Handler получает `snapshot.state`; original version фиксируется до Handler.
8. Три non-success Handler outcome не вызывают save.
9. Невалидный тип outcome не вызывает save и даёт internal failure.
10. Обычный успешный commit вызывает один save.
11. Первый `StateCommitFailed` запускает не более одного повтора.
12. Повтор использует ту же delta по identity и тот же original expected;
    между попытками нет load.
13. Повторный typed outcome классифицируется по общей таблице.
14. Истёкший deadline запрещает повтор; результат содержит первый failure.
15. Отмена до старта повтора также запрещает повтор.
16. Отмена уже начатого commit не отменяет inner task; terminal event пишется
    до проброса `CancelledError`.
17. Тест отмены использует `asyncio.Event` и доказывает порядок без `sleep`.
18. Повторная отмена не оставляет commit task без strong reference/ожидания.
19. `Committed`, `AlreadyApplied`, `Superseded`, absence и failures дают
    заданные модели и полную связку полей.
20. Исчезновение сессии после Handler отличается кодом и handler status.
21. Raw exception text отсутствует в `user_message`.
22. Множество status triples union точно равно §8.
23. Для каждой модели отклоняются противоречивые `code`, `retryable`,
    `detail_code`, `state_version` и payload.
24. Модели immutable после создания.
25. Все известные failure-коды возвращают точный текст; неизвестный
    calculation code даёт fallback и WARN.
26. `run_id` совпадает с входным во всех результатах/events.
27. `state_version` присутствует и отсутствует строго по §12.
28. Параллельные execute не разделяют request state.
29. На execute приходится ровно один `application_operation_started` и один
    `application_operation_finished`: result либо cancelled.
30. Завершённые load и Handler создают соответствующий stage event; отменённая
    незавершённая стадия его не создаёт.
31. Каждая фактически начатая попытка save создаёт ровно один commit-attempt
    event с правильным номером; запрещённый retry не создаёт attempt 2.
32. Terminal event пишется после последнего stage/attempt event и до возврата
    результата либо проброса `CancelledError`.
33. Compact events и сообщения не содержат birth data и полный session ID.
34. Клиентский contract test не применяет ответ с версией ниже локальной.
35. Профиль 1 подтверждает не только приём, но завершение 300 операций и drain.
36. Профиль 2 выполняется с конечным admission limit и не превышает одного
    повтора commit на операцию.

## 16. Итоговый Build Natal flow

```text
Input boundary
  ├─ create/restore RunContext
  ├─ resolve/create trusted session lifecycle
  └─ admission control
          │
          ▼
ApplicationOrchestrator.execute(command, session_id, run)
  ├─ INFO application_operation_started
  ├─ exact routing
  │    └─ absent → HANDLER_NOT_REGISTERED, no load
  ├─ ContextService.load
  │    ├─ SessionAbsent
  │    ├─ StateReadFailed
  │    ├─ SessionSnapshot + original expected
  │    └─ application_stage_finished(stage=load) after completed call
  ├─ BuildNatalHandler.handle(command, state, same run)
  │    ├─ InputRequired / ResolutionUnavailable / CalculationFailed
  │    ├─ BuildNatalSuccess(artifact, delta)
  │    └─ application_stage_finished(stage=handler) after completed call
  └─ protected ContextService.save(original expected, same delta)
       ├─ Committed / AlreadyApplied / Superseded / SessionAbsent
       ├─ StateCommitFailed
       │    └─ at most one exact retry if not cancelled/deadline-expired
       └─ application_commit_attempt_finished for each started save
                    │
                    ▼
          INFO/WARNING application_operation_finished
          → ApplicationResult
          or → original CancelledError
```

Главное разделение ответственности:

- входная граница владеет transport/session bootstrap, admission и
  correlation context;
- `ApplicationOrchestrator` владеет последовательностью application-команды и
  её нормализованным завершением;
- Handler владеет предметным use case;
- `ContextService` владеет session semantics и persistence outcome;
- Agent Runtime владеет только будущим agent execution за соответствующим
  interpretation handler.
