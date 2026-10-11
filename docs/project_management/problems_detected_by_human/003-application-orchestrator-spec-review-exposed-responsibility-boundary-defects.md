## Ручное ревью требований ApplicationOrchestrator выявило размывание границ ответственности и неполные outcome-контракты

- **Дата обнаружения:** 2026-09-15
- **Кем обнаружено:** владельцем проекта при ручном ревью первой версии требований `ApplicationOrchestrator`
- **Тип:** дефекты спецификации, размывание границ ответственности и неполный контракт обработки исходов
- **Статус:** обнаружено до реализации; требования отправлены на переработку

Связанные документы:

- `docs/requirements/decisions/0006-application-orchestrator.md`
- `docs/requirements/decisions/0014-explicit-state-mutations.md`
- `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`
- `docs/sequence_diagrams/build_natal/000-build_natal_end_to_end.puml`
- `docs/sequence_diagrams/build_natal/006-build_natal_superseded_cas.puml`

### Основная проблема

При подготовке первой отдельной спецификации `ApplicationOrchestrator` формально были учтены основные архитектурные решения проекта: типизированная маршрутизация команд, загрузка состояния, вызов handler, CAS commit и формирование итогового application outcome.

Однако ручное ревью владельцем проекта выявило несколько дефектов самой спецификации.

Проблема была не в отсутствии компонентов, а в том, что описание начинало **незаметно перераспределять уже определённые ответственности между ними** и оставляло ряд важных runtime-сценариев без однозначно заданного поведения.

Были обнаружены пять классов проблем:

1. текст спецификации создавал ложное впечатление связи `Handler → ContextService`;
2. для `Superseded` был определён статус, но не определено действие после его получения;
3. для failure outcomes отсутствовал полный пользовательский контракт;
4. `RunContext` получил двух потенциальных владельцев;
5. итоговый `ApplicationResult` не позволял однозначно восстановить, на каком уровне завершилась или сломалась операция;
6. граница `ApplicationOrchestrator ↔ BuildNatalHandler` была описана недостаточно явно.

Особенно показателен случай с `run_id`: предлагаемая спецификация добавляла в Orchestrator ответственность, которая уже принадлежит внешней границе приложения и при дальнейшем развитии системы всё равно должна находиться вне Orchestrator.

---

## 1. Ложная связь между Handler и ContextService

### Обнаруженная формулировка

В первой версии требований общий поток был представлен в виде:

```text
HandlerOutcome
    ↓
ContextService.save()
```

Такое изображение семантически связывает результат handler непосредственно с сохранением состояния.

Из текста можно сделать вывод, что handler:

- определяет необходимость записи;
- участвует в session lifecycle;
- либо по крайней мере находится в прямом потоке взаимодействия с `ContextService`.

Это противоречит уже принятой архитектуре.

### Фактическая граница

`BuildNatalHandler` и `ContextService` друг о друге не знают.

Правильная схема:

```text
                    ┌──► ContextService.load()
                    │
Application         │
Orchestrator ───────┤
                    │
                    └──► BuildNatalHandler
                              │
                              │ BuildNatalOutcome
                              ▼
                    ApplicationOrchestrator
                              │
                              └──► ContextService.save()
                                   только если это требуется
```

Handler получает:

```text
BuildNatalCommand
SessionState
RunContext
```

и возвращает:

```text
BuildNatalOutcome
```

В успешной ветке:

```text
BuildNatalSuccess {
    artifact
    delta
}
```

Но handler:

- не получает `ContextService`;
- не получает `SessionStore`;
- не сохраняет `StateDelta`;
- не знает `expected_state_version`;
- не выполняет CAS;
- не знает результат commit.

Решение вызвать `ContextService.save()` принадлежит исключительно `ApplicationOrchestrator`.

### Почему это важно

Это не косметическая неточность диаграммы.

Если такая формулировка перейдёт в implementation prompt, агент может совершенно логично:

- передать `ContextService` в handler;
- добавить persistence port в handler;
- заставить handler самостоятельно сохранять результат;
- либо связать handler outcome с persistence через callback.

Каждый из вариантов разрушит существующую границу ответственности.

---

## 2. `Superseded` был описан как состояние, но не как поведение

### Обнаруженная проблема

Первая версия требований предусматривала:

```text
ContextService.save(...)
    → Superseded
```

но фактически отвечала только на вопрос:

> Как называется этот outcome?

Она не отвечала на более важный вопрос:

> Что система должна сделать после его получения?

Статус без заданной реакции оставляет реализацию неоднозначной.

Возможны принципиально разные варианты:

```text
retry
reload + retry
rebase
ignore
return failure
return success
restore actual state
```

Для конкурентного state-management такие различия критичны.

### Требуемая семантика

`Superseded` означает:

> результат данного run корректен как расчёт, но больше не соответствует актуальному пользовательскому состоянию.

Пример:

```text
run A:
    load state_version = 5

run B:
    load state_version = 5

run B:
    commit
    state_version = 6

run A:
    calculation success
    save(expected = 5)
        → Superseded(actual.state_version = 6)
```

После получения `Superseded` Orchestrator обязан:

```text
1. не повторять save;
2. не перечитывать состояние для rebase;
3. не запускать Handler повторно;
4. не применять StateDelta;
5. не заменять актуальную карту рассчитанным artifact данного run;
6. вернуть типизированный Superseded application outcome;
7. передать вызывающему слою информацию о текущей версии состояния.
```

Расчётный артефакт при этом не является некорректным и может остаться в `CalculationCache`.

Некорректным является только его применение к данной версии пользовательского состояния.

### Почему автоматический retry запрещён

Retry с новым `expected_state_version` изменил бы смысл операции:

```text
старое пользовательское намерение
```

превратилось бы в:

```text
новую запись поверх состояния,
которое появилось уже после начала операции
```

То есть Orchestrator фактически выполнил бы скрытый rebase пользовательского намерения.

Такого поведения в системе быть не должно.

---

## 3. Failure outcomes не имели полного пользовательского контракта

### Обнаруженная проблема

В требованиях были перечислены технические результаты:

```text
InputRequired
ResolutionUnavailable
CalculationFailed
StateReadFailed
StateCommitFailed
SessionAbsent
InternalFailure
```

но для них не было систематически определено:

```text
что делает Orchestrator;
можно ли повторить операцию;
что должен увидеть пользователь;
какой стабильный машинный код должен получить transport.
```

Часть поведения была описана косвенно, например для `ContextService.load`, но общей таблицы реакции не существовало.

Это оставляет presentation-layer право самостоятельно интерпретировать внутренние технические outcomes.

### Требование

Для каждого внешнего failure/application outcome должны быть определены как минимум:

```text
code
user_message
retryable
```

Дополнительно при необходимости:

```text
issues
actual_state_version
```

Сырые exception messages через application boundary не проходят.

### Минимальная таблица поведения

| Внутренний исход | Действие Orchestrator | Retry | Пользовательский смысл |
|---|---|---:|---|
| `InputRequired` | commit не выполнять | нет | необходимо исправить или дополнить ввод |
| `ResolutionUnavailable` | commit не выполнять | зависит от outcome | временно не удалось разрешить данные |
| `CalculationFailed` | commit не выполнять | зависит от `error_code` | карта не рассчитана |
| `StateReadFailed` | Handler не запускать | да | состояние сессии временно недоступно |
| `StateCommitFailed` | success не возвращать | да | расчёт завершён, но сохранение не подтверждено |
| `SessionAbsent(expired)` | дальнейшую обработку прекратить | нет | сессия истекла |
| `SessionAbsent(not_found)` | дальнейшую обработку прекратить | нет | сессия отсутствует |
| `Superseded` | старый результат отбросить | нет | появился более актуальный результат |
| unexpected exception | обработку прекратить | возможно | внутренняя ошибка |

Таким образом failure contract должен отвечать не только на вопрос:

> Что произошло внутри системы?

но и:

> Что с этим должен сделать следующий слой?

---

## 4. Предложение создавать `RunContext` внутри Orchestrator размыло ownership

### Обнаруженная формулировка

Первая версия контракта предлагала:

```python
async def execute(
    command,
    *,
    session_id,
    run: RunContext | None = None,
):
    run = run or RunContext.new()
```

То есть `RunContext` мог:

1. создаваться transport-слоем;
2. либо создаваться `ApplicationOrchestrator`.

Владелец проекта отклонил этот вариант.

### Почему решение выглядит удобным

На первый взгляд fallback полезен:

- тестам проще вызывать Orchestrator;
- CLI может не создавать telemetry context самостоятельно;
- Orchestrator всегда гарантированно имеет `run_id`.

Локально это уменьшает количество обязательных аргументов.

Но эта локальная простота достигается ценой размытия архитектурной границы.

### Первая проблема: одна ответственность получает двух владельцев

При такой модели невозможно однозначно ответить:

> Кто отвечает за начало correlation scope?

Ответ становится:

```text
обычно transport,
но иногда ApplicationOrchestrator.
```

Это плохая граница.

Один и тот же lifecycle-факт создаётся на двух разных архитектурных уровнях.

В результате:

- появляются два пути инициализации;
- тесты могут покрывать один, production использовать другой;
- свойства `started_at` начинают зависеть от точки входа;
- невозможно формально потребовать, чтобы correlation существовала до входа в Orchestrator.

### Вторая проблема: correlation начинается раньше Orchestrator

В текущем HTTP-flow до ApplicationOrchestrator уже происходят:

```text
HTTP request
→ session cookie resolution
→ rate limit
→ ApplicationOrchestrator
```

Если `run_id` создаётся только внутри Orchestrator, события:

```text
session resolution
rate limiting
transport validation
```

не могут быть частью того же correlation scope.

Следовательно, правильная граница создания находится **выше ApplicationOrchestrator**.

Текущая модель:

```text
Transport / middleware
    ↓
create RunContext
    ↓
ApplicationOrchestrator
    ↓
Handler
    ↓
Resolver
    ↓
Engine
```

позволяет одному `run_id` сопровождать всю операцию от входной границы.

### Третья проблема: Orchestrator получает лишнюю ответственность

Назначение ApplicationOrchestrator:

> координировать application operation.

Создание telemetry identity является другой ответственностью:

> создать correlation envelope входящей операции.

Если добавить её в Orchestrator, компонент начинает отвечать не только за application lifecycle, но и за часть edge/observability lifecycle.

Само по себе добавление одной строки:

```python
RunContext.new()
```

выглядит незначительным.

Но архитектурно это расширение полномочий компонента.

Для Orchestrator это особенно опасно, потому что он уже находится в естественной точке притяжения большого количества обязанностей:

```text
context
routing
handlers
commit
outcome normalization
observability
```

Поэтому каждое дополнительное действие должно иметь сильное основание.

### Четвёртая проблема: будущий event-driven вход всё равно потребует вынести ответственность обратно

При переходе от прямого HTTP request/response к event-driven архитектуре correlation обычно существует до application handler.

Например:

```text
message
{
    correlation_id
    causation_id
    event_id
    ...
}
    ↓
consumer / middleware
    ↓
ApplicationOrchestrator
```

Или:

```text
broker
→ consumer middleware
→ telemetry context
→ ApplicationOrchestrator
```

В такой модели Orchestrator не должен создавать новый `run_id`, потому что это оборвёт связь с входящим событием.

Следовательно, если сегодня положить создание correlation context внутрь Orchestrator, при переходе к event-driven эту ответственность всё равно придётся переносить наружу.

Это означает создание заранее известного архитектурного долга без текущей необходимости.

### Принятое направление

`RunContext` должен приходить в Orchestrator готовым:

```python
async def execute(
    self,
    command: Command,
    *,
    session_id: str,
    run: RunContext,
) -> ApplicationResult:
    ...
```

`run` обязателен.

В HTTP-flow его создаёт transport/middleware.

В тестах его явно создаёт тест.

Если в будущем появится другой entry point:

```text
CLI
consumer
scheduler
internal API
```

соответствующий entry adapter создаёт или восстанавливает `RunContext` до вызова Orchestrator.

Таким образом правило формулируется не как:

> `run_id` создаёт HTTP API,

а шире:

> **correlation context создаётся или восстанавливается на входной границе операции и передаётся ApplicationOrchestrator готовым.**

Это переживает смену transport-модели.

---

## 5. `ApplicationResult` не показывал, на каком уровне завершилась операция

### Обнаруженная проблема

Первая версия пыталась нормализовать множество внутренних outcomes в один верхнеуровневый статус:

```text
Success
InputRequired
Superseded
InfrastructureFailure
InternalFailure
...
```

Такой контракт удобен клиенту, но теряет важную диагностическую информацию.

Например:

```text
BuildNatalHandler → success
ContextService    → StateCommitFailed
```

и:

```text
BuildNatalHandler → CalculationFailed
ContextService    → save не вызывался
```

могли в обоих случаях превратиться просто в:

```text
InfrastructureFailure
```

Хотя операционные состояния совершенно различны.

В первом случае:

```text
расчёт состоялся;
commit не подтверждён.
```

Во втором:

```text
расчёт не состоялся;
commit даже не начинался.
```

### Требуемая модель

Внешний результат должен отдельно отражать три уровня:

```text
orch_status
build_status
context_status
```

### `orch_status`

Чем закончилась пользовательская операция целиком.

### `build_status`

Чем закончился `BuildNatalHandler`.

### `context_status`

Что произошло с session state в рамках операции.

Пример:

```text
orch_status    = FAILURE
build_status   = SUCCESS
context_status = COMMIT_FAILED
```

сразу показывает:

> предметная операция завершилась, но application operation не была подтверждена.

А:

```text
orch_status    = FAILURE
build_status   = CALCULATION_FAILED
context_status = LOADED
```

означает:

> состояние было успешно загружено, но расчёт не состоялся и commit не требовался.

## Опасность свободных комбинаций

Простое добавление трёх enum создаёт новую проблему: появляются бессмысленные комбинации.

Например:

```text
orch_status    = SUCCESS
build_status   = CALCULATION_FAILED
context_status = COMMITTED
```

Такое состояние не должно существовать.

Поэтому допустимые комбинации должны быть:

- описаны явной матрицей;
- либо лучше сделаны невозможными типовой моделью через отдельные result-типы с `Literal` значениями.

Например:

```text
CommittedResult:
    orch_status    = SUCCESS
    build_status   = SUCCESS
    context_status = COMMITTED

SupersededResult:
    orch_status    = SUPERSEDED
    build_status   = SUCCESS
    context_status = SUPERSEDED

CalculationFailureResult:
    orch_status    = FAILURE
    build_status   = CALCULATION_FAILED
    context_status = LOADED
```

Таким образом тип результата сам является доказательством допустимости комбинации.

---

## 6. Граница Orchestrator ↔ Handler была недостаточно формальной

### Обнаруженная проблема

Первая версия содержала схему:

```text
BuildNatalCommand
    ↓
BuildNatalHandler
    ↓
BuildNatalOutcome
```

но для component requirements этого недостаточно.

Не было явно зафиксировано:

- какие данные Orchestrator передаёт;
- какие из них являются business input, а какие execution context;
- что Handler имеет право делать с `SessionState`;
- полный union возвращаемых результатов;
- в каких ветках после Handler вызывается `ContextService.save`;
- какие session-понятия Handler вообще не должен видеть.

### Требуемый входной контракт

Orchestrator передаёт:

```text
BuildNatalHandlerInput {
    command: BuildNatalCommand
    state:   SessionState
    run:     RunContext
}
```

При этом:

```text
command
```

содержит пользовательское намерение;

```text
state
```

является immutable snapshot;

```text
run
```

является telemetry context.

Handler не получает:

```text
session_id
expected_state_version
ContextService
SessionStore
StateCommit outcome
```

### Требуемый выходной контракт

Handler возвращает:

```text
BuildNatalOutcome =
      BuildNatalSuccess
    | InputRequired
    | ResolutionUnavailable
    | CalculationFailed
```

Именно Orchestrator после получения результата принимает решение:

```text
BuildNatalSuccess
    → ContextService.save(delta)

InputRequired
    → no save

ResolutionUnavailable
    → no save

CalculationFailed
    → no save
```

Это правило должно быть частью спецификации Orchestrator, а не следствием, которое разработчик обязан восстановить по sequence diagram.

---

## Почему эти проблемы не были оставлены «на усмотрение реализации»

Каждая из найденных неточностей допускает несколько технически работоспособных реализаций.

Например, агент мог бы:

- создать `RunContext` внутри Orchestrator;
- передать `ContextService` в Handler;
- автоматически retry `Superseded`;
- свести все технические ошибки к одному `InfrastructureFailure`;
- вернуть свободную комбинацию трёх статусов;
- самостоятельно придумать пользовательские тексты ошибок.

Каждый вариант мог бы пройти локальные unit-тесты.

Проблема состоит в том, что они по-разному распределяют ответственность между компонентами и задают разные свойства системы при конкурентности и дальнейшем развитии.

Поэтому эти вопросы нельзя оставлять implementation-agent.

Они должны быть решены на уровне требований до написания implementation prompt.

---

## Почему особенно важен случай `run_id`

Случай с `run_id` показателен тем, что предлагаемое решение не выглядело ошибочным на уровне кода.

Конструкция:

```python
run = run or RunContext.new()
```

короткая, удобная и полностью работоспособная.

Дефект становится виден только при рассмотрении системы как набора границ ответственности.

Ручное ревью выявило сразу три свойства, которых локальный код не показывает:

1. correlation scope начинается до Orchestrator;
2. одна ответственность не должна иметь двух владельцев;
3. при смене transport-модели ownership всё равно должен остаться на входной границе.

Таким образом решение было отклонено не потому, что оно технически не работает, а потому, что оно ухудшает архитектурную устойчивость системы.

Это именно тот класс проблем, для которого в spec-driven разработке остаётся необходимым человеческое архитектурное решение.

---

## Итог

Ручное ревью первой версии требований `ApplicationOrchestrator` выявило не ошибки синтаксиса или реализации, а ошибки **распределения ответственности и полноты поведенческого контракта**.

До передачи задачи implementation-agent требования необходимо дополнить:

```text
1. явным отсутствием связи Handler → ContextService;

2. полным алгоритмом реакции на Superseded;

3. таблицей реакции на каждый failure outcome;

4. единым владельцем RunContext:
   entry boundary, а не ApplicationOrchestrator;

5. трёхуровневой моделью результата:
   orch_status
   build_status
   context_status;

6. ограничением допустимых комбинаций этих статусов;

7. явным входным и выходным контрактом
   ApplicationOrchestrator ↔ BuildNatalHandler.
```

Основной вывод:

> **Компилируемая или даже локально корректная спецификация ещё не гарантирует корректной архитектурной границы.**

В данном случае человеческое ревью остановило расширение ответственности `ApplicationOrchestrator` до начала реализации и обнаружило несколько мест, где implementation-agent иначе был бы вынужден самостоятельно принимать архитектурные решения.