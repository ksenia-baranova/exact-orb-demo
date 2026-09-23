# ADR-0006. Application Orchestrator — единый координатор application-flow; stateless между запросами

Дата: 2026-08-21.  
Ревизия: 2026-08-26 — отменено ограничение редакции 2026-08-25 «Orchestrator только для потоков с интерпретацией»; разделены `Application Orchestrator` и `Agent Runtime`; построение и перестроение карты снова проходят через Application Orchestrator, но не через Agent Runtime.  
Ревизия: 2026-09-06 — терминология session-flow приведена к ADR-0009 и
ADR-0014: `SessionState`, `StateDelta`, CAS-предикат передаётся отдельно;
`ProfileService` не вводится. `SetActiveView` отмечен как post-MVP по ADR-0016.
Ревизия: 2026-09-15 — уточнены границы application coordination: обязательный
`RunContext` принадлежит входной границе; routing предшествует load; прямой
доступ транспорта к `ContextService` ограничен session bootstrap/restore.
Прежняя возможность создавать fallback correlation context внутри
Orchestrator исключена. Два уровня оркестрации сохраняются.
Ревизия: 2026-09-16 — уточнён observability-контракт: Application
Orchestrator пишет компактные lifecycle-события стадий и ровно одно terminal
event через штатный structured logging. Реестр активных `run_id`, глобальные
счётчики и отдельный telemetry port не вводятся; метрики выводятся из событий,
а concurrency/queue принадлежат transport/composition admission controller.
Ревизия: 2026-09-17 — уточнены гарантии общей границы: RunContext frozen,
поля terminal event извлекаются из ApplicationResult, сообщения lifecycle
кодируются одним JSON object после имени события. Числовые метаданные проверяются
до записи; ошибка logging не меняет подтверждённый persistence outcome.
Статус: принято.

## Контекст

Исходная архитектура рассматривала Orchestrator как единую точку координации пользовательского запроса.

В редакции 2026-08-25 область Orchestrator была сужена только до потоков, включающих интерпретацию: детерминированное построение карты предлагалось выполнять отдельным application service напрямую из API.

После проработки lifecycle построения карты такое разделение признано искусственным.

Даже операция без LLM состоит не только из вызова расчётного ядра. Application-flow может включать:

- загрузку сессионного контекста;
- маршрутизацию типизированной команды;
- correlation через `run_id`;
- вызов соответствующего handler;
- проверку актуальности результата;
- применение `StateDelta`;
- atomic state transition;
- классификацию результата и отказа;
- observability.

Одновременно внутри interpretation-flow существует другой уровень координации: planning, выбор scenario, последовательность tools и исполнение agent-сценария.

Эти ответственности необходимо разделить.

## Решение

В системе существуют **два уровня оркестрации**:

1. `Application Orchestrator`;
2. `Agent Runtime` / `Agent Orchestrator`.

Они отвечают за разные lifecycle.

```text
                         ┌─ BuildNatalHandler
                         │
API → Application ───────┼─ InterpretSelectionHandler
      Orchestrator       │
                         └─ InterpretMessageHandler
                                      │
                                      ▼
                                 Agent Runtime
```

## Application Orchestrator

`Application Orchestrator` — единая точка координации типизированных
application-команд после транспортного слоя.

Он отвечает на вопрос:

> Как провести конкретную пользовательскую операцию через систему?

На вход он получает уже типизированную application-команду.

Например:

```text
BuildNatalCommand
UpdateBirthDataCommand
SetActiveViewCommand  // после MVP, вместе с производными картами
InterpretSelectionCommand
InterpretMessageCommand
```

Выбор handler выполняется детерминированно по точному типу команды и не
требует LLM. Routing предшествует загрузке состояния: отсутствие handler
завершает команду до обращения Orchestrator к `ContextService`.

Пример:

```text
BuildNatalCommand
    → BuildNatalHandler

InterpretSelectionCommand
    → InterpretSelectionHandler

InterpretMessageCommand
    → InterpretMessageHandler
```

### Ответственности Application Orchestrator

Application Orchestrator:

1. принимает обязательный `RunContext`, подготовленный входной границей;
2. выбирает handler по типу команды до обращения к сессии;
3. загружает необходимый application context;
4. запускает handler;
5. принимает результат handler'а и `StateDelta`;
6. координирует сохранение состояния;
7. контролирует application-level completion;
8. приводит outcomes компонентов к контракту application/API;
9. обеспечивает единый observability scope;
10. для streaming-операций координирует lifecycle канала.

Предметное решение остаётся внутри handler'а и специализированных services.

### Входная граница и session bootstrap

Входная граница — HTTP transport, CLI либо адаптер другого способа запуска.
Она создаёт `RunContext` или получает уже созданный контекст **той же
операции**, разрешает доверенный `session_id` и передаёт оба значения
Orchestrator отдельно от команды. CLI и тесты следуют тому же правилу:
отсутствие HTTP не переносит создание контекста внутрь Orchestrator.

Создание сессии и восстановление её состояния при bootstrap транспорт
выполняет через `ContextService` напрямую. Это разрешённая вторая
application-зависимость транспорта; handler для bootstrap не требуется.
При отсутствующей или истёкшей сессии транспорт гасит старую cookie и
создаёт новую сессию со свежим серверным ID по ADR-0009.

Исключение ограничено **create/restore**. `ResetSessionCommand`,
`DeleteMyDataCommand` и другие application-команды проходят через
Orchestrator; транспорт не выполняет их предметные изменения самостоятельно.
Допуск таких команд этим ADR не означает их реализацию в первом Build Natal
срезе. Orchestrator остаётся владельцем загрузки snapshot для самой команды:
bootstrap/restore не заменяет её обязательный load.

### Build path

Построение базовой карты проходит через Application Orchestrator:

```text
API
→ Application Orchestrator
→ BuildNatalHandler
→ BirthDataResolver
→ ChartArtifactResolver
→ EngineService
→ StateDelta
→ Application Orchestrator
→ ContextService
```

При этом данный flow **не является agent-flow**.

Он не проходит через:

```text
Planner
ScenarioRegistry
ToolExecutor
ToolRegistry
InterpretationService
LLM
```

### Interpretation path

Интерпретационный flow использует второй уровень координации:

```text
API
→ Application Orchestrator
→ InterpretSelectionHandler / InterpretMessageHandler
→ Agent Runtime
→ Planner
→ tools
→ InterpretationService
```

Таким образом `Agent Runtime` находится **за Application Orchestrator**, а не заменяет его.

## Agent Runtime

Agent Runtime отвечает на другой вопрос:

> Какие capabilities нужны для данного agent-сценария, в каком порядке их выполнить и как передать результаты между шагами?

В его область входят:

```text
Planner
ScenarioRegistry
ToolExecutor
ToolRegistry
Tools
```

Application Orchestrator не знает topology agent tools.

Названия компонентов должны явно различать application coordination и
agent execution. Существование двух уровней оркестрации допустимо и
предусмотрено этим решением. Переименование существующего agent-каркаса
является отдельным изменением; его удаление не является условием реализации
`ApplicationOrchestrator`.

Особенно важный инвариант:

> **Application Orchestrator знает handlers, но не знает конкретных tools и их зависимостей.**

Например он не знает, что для transit-сценария сначала требуется natal tool.

Это является знанием ScenarioRegistry / Agent Runtime.

## Владение interpretation pipeline

Внутренняя связка:

```text
interpretation cache get
→ budget reserve
→ LLM
→ OutputGuard
→ cache put
→ commit | cancel
```

по-прежнему принадлежит `InterpretationService`.

Agent Runtime может вызвать `InterpretationService`, но не забирает внутрь себя ответственность за реализацию этого pipeline.

Application Orchestrator тем более не управляет отдельными шагами этого конвейера.

## Владение состоянием

`ContextService` остаётся владельцем persistence.

Handler принимает `SessionState`, выполняет предметное решение и возвращает
all-set `StateDelta`. Отдельный `ProfileService` не вводится.

Application Orchestrator координирует применение дельты через `ContextService`,
передавая отдельно исходный `expected_state_version` как CAS-предикат.

Сам Application Orchestrator предметных решений о содержимом профиля не принимает.

## Значение stateless

Application Orchestrator не хранит пользовательское состояние **между запросами**.

Следующий запрос может обслужить другая реплика.

Внутри одного run Orchestrator является stateful coordinating frame.

Он может временно удерживать:

- загруженный context;
- выбранный handler;
- handler result;
- `StateDelta`;
- correlation metadata;
- application outcome;
- открытый SSE-stream для interpretation-flow.

Это не противоречит stateless deployment.

Durable state находится вне процесса.

## `run_id`

`run_id` является correlation identifier.

Его единственный владелец — входная граница операции. Контекст создаётся
до первых стадий её correlation scope, включая транспортные проверки.
`ApplicationOrchestrator` получает обязательный `RunContext`, не создаёт
новый `run_id`, не подменяет объект и передаёт тот же объект Handler.
Fallback вида `run = run or RunContext.new()` запрещён.

RunContext неизменяем после создания: run_id, started_at и deadline нельзя
переприсваивать, даже другим допустимым значением. Это сохраняет correlation
и UTC-инвариант между компонентами без копирования передаваемого объекта.

Result-terminal получает тот же ApplicationResult, который подготовлен для
возврата. Logging проецирует только статусы, code/detail_code, run_id и версию;
полный payload и user_message не записываются. Метаданные времени и попыток
принадлежат execute. Формат сообщения — имя события и однострочный JSON object,
чтобы открытая строка кода не могла создавать дополнительные поля или события.
Ошибка контракта метаданных не классифицируется как ошибка persistence и
не опровергает уже подтверждённый commit. Глубокая неизменяемость вложенного
payload здесь не вводится; она требует отдельного согласования моделей.

Один operation-flow, включая разрешённый повтор commit, сохраняет один
`run_id`. Самостоятельный новый запрос получает новый контекст; повторная
доставка того же намерения не делает `run_id` ключом идемпотентности.

Он используется для связывания:

```text
API
→ handler
→ Agent Runtime
→ Tool
→ Engine
→ cache
→ state commit
→ response
```

`run_id` сам по себе не является handle возобновления незавершённой операции.

Если позже появится durable asynchronous build или resumable execution, для этого потребуется отдельный контракт состояния.

### Observability operation-flow

Application Orchestrator владеет observability всей координируемой операции и
пишет через штатный structured logger:

```text
application_operation_started
application_stage_finished             # load / handler
application_commit_attempt_finished    # на каждый начатый save
application_operation_finished         # ровно один terminal event
```

Компоненты продолжают владеть собственными внутренними и boundary-событиями.
Lifecycle-запись Orchestrator описывает стадию application-flow и не копирует
payload Handler, resolver, engine, cache или `ContextService`.
Исключение для полного входа `execute()` на DEBUG принято в ADR-0035;
компактные lifecycle-события этим не изменены.
ADR-0036 добавляет отдельные INFO-события `application_message direction=send|receive`
для прямых вызовов `ContextService` и выбранного Handler без тела сообщения.

Request-specific observability state хранится только в локальных переменных
одного `execute()`: длительности, число commit attempts, их безопасные error
codes и признак отменённой доставки. Orchestrator не хранит registry активных
`run_id`, историю операций или общие counters между вызовами.

Счётчики результатов и retry выводятся из event stream. Активные операции
определяются парой started/finished; максимум конкурентности и очередь
измеряются transport/composition admission controller и нагрузочным стендом.
Конкретный metrics backend не входит в Application Orchestrator.

## Чего Application Orchestrator не делает

Application Orchestrator:

- не рассчитывает карту;
- не содержит астрологической предметной логики;
- не знает Swiss Ephemeris;
- не строит prompts;
- не обращается непосредственно к LLM;
- не выбирает agent tools;
- не разрешает зависимости tools;
- не реализует agent loop;
- не выполняет DataSelector;
- не принимает policy-решения вместо PolicyService;
- не определяет стоимость вместо AdmissionControl;
- не создаёт `RunContext`, session ID или сессию;
- не управляет cookie и session bootstrap/restore;
- не мутирует `SessionState` самостоятельно.

## Чего Agent Runtime не делает

Agent Runtime:

- не является API entry point;
- не управляет session cookie;
- не определяет верхнеуровневый тип application command;
- не владеет Session Store;
- не применяет `StateDelta`;
- не создаёт предметное состояние пользователя;
- не реализует астрологические расчёты.

## Альтернативы

### Build Chart в обход Application Orchestrator

Отвергнуто.

Хотя execution path детерминирован, application lifecycle остаётся общим с другими пользовательскими операциями. Обход создаёт второй coordination path с собственными правилами context, errors, state commit и observability.

### Application Orchestrator одновременно является Agent Runtime

Отвергнуто.

Компонент начал бы одновременно знать sessions, handlers, scenarios, tools, их зависимости, prompts и state lifecycle и быстро стал бы god-object.

### Все запросы проводить через Agent Runtime

Отвергнуто.

Явный детерминированный Build Chart не требует Planner, ScenarioRegistry или ToolExecutor.

## Последствия

- Все типизированные application-команды имеют единую coordination boundary;
  session bootstrap/restore выполняется транспортом через `ContextService`.
- Build Chart остаётся полностью под контролем общего application lifecycle.
- Детерминированный build не превращается в agent-flow.
- Agent Runtime может эволюционировать независимо от API и session lifecycle.
- Новые tools не требуют изменений Application Orchestrator.
- Новый application use case требует явного handler либо явной маршрутизации.
- Application lifecycle наблюдаем через единый поток событий с одним started
  и одним terminal event на вызов; события связываются входным `run_id`.
- Метрики не требуют хранения operation state между вызовами Orchestrator.
- Число зависимостей Application Orchestrator необходимо контролировать как метрику риска god-object.
- Разделение Application Orchestrator и Agent Runtime становится архитектурным инвариантом.

## Связанные требования

Подробный контракт первого use case, статусы, ошибки, повторы, отмена и
acceptance-сценарии описываются в
[требованиях ApplicationOrchestrator](../component_responsibilities/exact-orb_application_orchestrator_requirements.md).
Рабочий статус требований не означает реализацию целевого API и не изменяет
принятые границы настоящего ADR.
