# Архитектура exact-orb

Статус документа: рабочий, версия 2.7 (2026-09-22).
Заменяет версию 1.0, описывавшую систему как чистый веб-чат.
Область: прикладной и агентский слои, их расчётные контракты и хранение данных.

Ревизия 2026-09-14: разделены текущая реализация и целевые потоки; уточнены
координация, восстановление карты, контракты резолва, Research Corpus и
решения ADR-0027–0033. Startup wiring остаётся отдельным этапом C3.

Ревизия 2026-09-15: целевой application-flow согласован с ADR-0006 и
требованиями `ApplicationOrchestrator`; routing выполняется до session load,
а готовый `RunContext` принадлежит входной границе.

Ревизия 2026-09-19: application core для `BuildNatalCommand`, внешний
`ApplicationResult`, CAS commit/retry/cancellation, lifecycle logging,
минимальная composition и normal load profile сверены с реализацией. HTTP/UI,
session bootstrap, admission и deployment composition остаются внешними.

Ревизия 2026-09-21: process runtime composition M1-5.1 реализована и принята
сквозными сценариями Build Natal и остановки с живым расчётом; FastAPI lifespan
M1-6 и production/deployment policy M1-12 остаются отдельными этапами.

Ревизия 2026-09-22: M1-5 catalog core реализован и принят — offline GeoNames
builder, `PlaceSearch`, `SqlitePlaceCatalog`, индексированные search/lookup и
сквозная application-интеграция. HTTP/lifespan, UI и доставка артефакта
остаются M1-6/M1-7/M1-12.

Документ описывает принятую архитектуру; наличие требования не означает
наличия реализации. Текущая готовность приведена в §2.1. Подробные контракты
задаются component requirements и действующими [ADR](decisions/README.md);
overview не заменяет и не отменяет их.

---

## 1. Назначение системы

Цель exact-orb — расчёт и интерпретация астрологических техник. Первый
application-срез ограничен натальной картой и космограммой. Расчёт транзитов
уже доступен в ядре и standalone CLI; транзиты в application-flow, соляр и
синастрия относятся к дальнейшему развитию.

В целевом интерфейсе пользователь входит в систему **через форму**: вводит дату, время
и место рождения и сразу получает карту. Дальше он взаимодействует с картой
кнопками `topic + focus`, а в режиме подписки — ещё и свободным вопросом - режим чата.

**Свободный вопрос доступен только по подписке.** Этот путь требует отдельного
понимания запроса, policy и контроля недоверенного текста. В анонимном режиме
интерпретация ограничена preset-кнопками. Подписка регулирует доступ и расход;
архитектурные ограничения текста действуют независимо от тарифа.

**Данные рождения меняются только через форму.** Дата, названная в чате, карту
не пересчитывает; система распознаёт такую попытку и явно просит воспользоваться
формой. Молча отвечать про сохранённую карту нельзя — это подмена субъекта,
которую пользователь не заметит.

**Расход ограничен с обеих сторон.** Ограничивается и длина вопроса на входе,
и объём ответа на выходе, а суммарный расход сессии считается в деньгах, а не
в токенах: вход и выход тарифицируются по-разному. Сессионный лимит защищает
от честного перерасхода; от злоупотребления защищают лимит по IP и глобальный
дневной потолок. Предварительные значения задаются с первого дня, уточняются
по результатам тестирования MVP на фокус-группе — фокус-группа показывает,
сколько нужно пользователю, потолок считается из юнит-экономики.

Впоследствии появятся два типа сессий — анонимная и с регистрацией
(платная подписка) — с разными лимитами и разным набором доступных операций.

Ключевое свойство: **вероятностное только по краям**. Языковая модель участвует
на выходе (изложение) и, в режиме подписки, на входе свободного текста. Всё, что
между — резолв места и времени, решение о том, что считать, сам расчёт и отбор
фактов — детерминировано, воспроизводимо и покрывается обычными тестами.

Второе ключевое свойство: **воспроизводимость**. Любой рассчитанный артефакт
адресуется контентным ключом и может быть удалён и посчитан заново без потери
пользовательских данных.

---

## 2. Верхнеуровневая декомпозиция

| Блок | Компоненты | Природа | Назначение |
|---|---|---|---|
| КЛИЕНТ | Frontend, Birth Form, Location Dropdown, Controls, Chart Renderer | транспорт | ввод и отображение |
| API | FastAPI, Session Middleware, Build / Selection / Message API | транспорт | приём запроса, JSON и SSE |
| КООРДИНАЦИЯ | ApplicationOrchestrator, application handlers | детерминированное | lifecycle операции, routing и commit |
| СЕССИЯ | ContextService, SessionPersistence, Session Store, Dialog Store | состояние | сессия с TTL, пока анонимная |
| РЕЗОЛВ | BirthDataResolver, PlaceSearch, PlaceCatalog, Historical TZ | детерминированное | текст места → выбранный ID → расчётные параметры и домен времени |
| ПОНИМАНИЕ | ActionContractBuilder, InputGuard, IntentService, ContractValidator | смешанное | вход → контракт |
| POLICY | CapabilityService, PolicyService, AdmissionControl | детерминированное | допуск, права, бюджет |
| РАНТАЙМ | Agent Runtime, Planner, ScenarioRegistry, ToolExecutor, ToolRegistry, Tools | детерминированное | план и исполнение интерпретационного сценария |
| АРТЕФАКТЫ | ChartArtifactResolver, calculation_key, CalculationVersion, CalculationCache | состояние | воспроизводимые результаты |
| РАСЧЁТ | EngineService, charts, ephemeris, aspects, configurations, strength | детерминированное | предметное ядро |
| ИНТЕРПРЕТАЦИЯ | InterpretationService, DataSelector, PromptBuilder, Gateway, OutputGuard | смешанное | факты → текст |
| ИССЛЕДОВАНИЕ | project_chart_features, ResearchCorpus, quality events | детерминированное | проекция результата и отдельный исследовательский контур |
| ПЛАТФОРМА | swiss_backend, ephemeris_runtime, config, logging | инфраструктура | native backend, конфигурация и диагностика |
| ВНЕШНЕЕ | LLM Provider; RemoteGeocoder после MVP | внешние зависимости | генерация текста; будущий сетевой резолв |

В MVP блок ПОНИМАНИЕ работает детерминированно: `IntentService` относится
к подписочному пути и не вызывается.

Система остаётся **модульным монолитом**. Swiss Ephemeris исполняется внутри
процесса; сеть между внутренними компонентами не вводится. Порты сохраняют
границы ответственности, а выделение сервиса требует наблюдаемого основания
и нового решения (ADR-0021).

Схемы: [компоненты](../architecture/exact_orb_architecture.puml),
[верхнеуровневая декомпозиция](../architecture/exact_orb_high_level_abstraction.puml).
Архитектурная рамка: [service-ready architecture](../architecture/service_ready_architecture.md).

### 2.1 Текущая готовность

Сверено повторно 2026-09-22. Подробные реестры application core и runtime
composition — в [плане ApplicationOrchestrator](../project_management/implementation_plans/application_orchestrator_implementation_plan.md)
и [плане bootstrap composition](../project_management/implementation_plans/bootstrap_composition_implementation_plan.md).

| Область | Реализовано | Остаётся |
|---|---|---|
| Standalone CLI и ядро | natal, cosmogram, transit | развитие техник; CLI не является HTTP-приложением |
| Build Natal | `BuildNatalCommand`, `BuildNatalHandler`, `BuildNatalOutcome`, `ApplicationOrchestrator`, внешний `ApplicationResult`, CAS commit/retry/cancellation, lifecycle logging, минимальная composition, process-local `ApplicationRuntime` и его сквозная приёмка | HTTP mapping, client monotonicity X1, admission X2 и deployment policy |
| Резолв и артефакты | `PlaceSearch`, `PlaceCatalog`, JSONL test adapter, GeoNames SQLite builder, `SqlitePlaceCatalog`, индексированные search/lookup, lifecycle/startup validation, historical TZ, resolver, spec, key v2, version, engine, codec, InMemory cache, artifact resolver и сквозная catalog/application приёмка | HTTP/lifespan wiring M1-6, UI autocomplete M1-7 и доставка `places.sqlite` M1-12 |
| Сессия | contracts, `ContextService`, InMemory и SQLite adapters, TTL/CAS, runtime-owned SQLite executor и one-shot reaper | подключение к HTTP/session lifecycle и периодическое расписание reaper |
| Клиент и HTTP API | — | форма, renderer, middleware, JSON/SSE endpoints |
| Agent Runtime | интерфейсы, реестры, синхронный `NatalTool`; `orchestration.Orchestrator` — каркас | interpretation handlers, целевой runtime, async Tool, общий путь через артефакты |
| Интерпретация и допуск | contracts/каркас интерпретации, LLM Gateway transport | `InterpretationService`, recipes, cache, streaming, guards, capabilities, policy и admission |
| Research Corpus | модели, whitelist-проекция, append-only port и InMemory adapter | SQLite adapter и application producer wiring |

Статус относится к компонентам в текущем checkout, а не к готовности
сквозного пользовательского сценария. Плановый состав MVP приведён в §8.

### 2.2 Основные потоки

Реализованный handler принимает `BuildNatalCommand`, `SessionState` и `RunContext`:

```text
BuildNatalHandler
  → BirthDataResolver → ResolvedBirthData / InputRequired / ResolutionUnavailable
  → NatalChartSpec
  → ChartArtifactResolver → cache hit / EngineService → ChartArtifact
  → BuildNatalSuccess(artifact, delta) / CalculationFailed
```

Handler формирует `StateDelta`, но не сохраняет её. Реализованный application
core:

```text
Typed input boundary → ApplicationOrchestrator → route by type(command) → ContextService.load
  → handler → ContextService.save(original expected_state_version, delta)
  → ApplicationResult
```

Успешная пользовательская операция требует подтверждённого commit либо
`AlreadyApplied`. Успешный расчёт сам по себе этого не доказывает.
Этот поток подтверждён прямыми application/integration-тестами. HTTP JSON,
cookie/session bootstrap и UI ещё не реализованы;
[Build Natal sequence diagrams](../sequence_diagrams/build_natal/README.md)
явно отделяют реализованный application core от целевого transport/client.
Точный контракт первого use case зафиксирован в
[требованиях ApplicationOrchestrator](component_responsibilities/exact-orb_application_orchestrator_requirements.md).

Целевой поток интерпретации использует второй уровень координации:

```text
ApplicationOrchestrator → InterpretSelectionHandler / InterpretMessageHandler
  → Agent Runtime → Planner / ScenarioRegistry → PolicyService → ToolExecutor
  → InterpretationService → interpretation cache / budget / LLM → SSE
```

Agent Runtime вызывается только interpretation handlers. Build Natal
не использует Planner, Tools или LLM (ADR-0006, ADR-0020).

---

## 3. Сквозные инварианты

Правила принятой архитектуры. Для будущих компонентов это требования к
реализации; для существующих учитываются явно зафиксированные ограничения
и исключения ADR. Наличие правила не означает, что весь целевой путь уже
проверяется исполняемым тестом. Краткие обоснования — в §3.1.

**И-1. Детерминированный path не получает пользовательский текст.**
`Planner`, `Tool`, `EngineService`, `Calculation Cache` и `ScenarioRegistry`
не видят сырого текста никогда. В режиме подписки нормализованный
`InterpretationQuery` доходит только до `PromptBuilder` как недоверенные данные
в отдельном слоте и не влияет на выбор инструментов, параметры расчёта и policy.
Никакая обработка текста не переводит его в разряд доверенных (ADR-0018).

**И-2. Сценарий = один промпт = один вызов LLM.**
Сколько бы инструментов ни отработало, наружу уходит один `PromptBundle`
(ADR-0003).

**И-3. `tools[]` и `topics[]` — разные списки.**
Натал может быть служебной зависимостью транзита, а не темой ответа (ADR-0004).

**И-4. Оркестратор не хранит пользовательское состояние между запросами.**
Состояние передаётся через session persistence; контекст одного прогона живёт
в памяти до его завершения. Правило относится к координатору: оно не запрещает
InMemory adapters и кэши и не обещает взаимозаменяемость процессов без общего
хранилища (ADR-0006, ADR-0021, ADR-0024).

**И-5. Способ исполнения зависимости скрыт за портом/адаптером.**
Сейчас `CalculationEnginePort` реализует локальный `EngineService`, а
`SqlitePlaceCatalog` реализует `PlaceCatalog` и `PlaceSearch` над одним
read-only выпуском. `LocalPlaceCatalog` сохранён для тестовой JSONL fixture.
Сетевые реализации не вводятся заранее (ADR-0002, ADR-0021).

**И-6. Исследовательский корпус не является источником данных горячего пути.**
`ResearchCorpus` — write-only порт для application producer; исследовательское
чтение вынесено отдельно. Эксплуатационная аналитика и диалог сессии имеют
собственные контракты (ADR-0023, заменивший ADR-0010).

**И-7. Предупреждения расчёта обязаны доходить до промпта.**
В целевом interpretation-flow сохраняются предупреждения и явный вид карты;
`time_uncertainty` нельзя превращать в точные аспекты или терять при отборе
фактов. Отдельные предупреждения о смене знака/направления остаются известным
пробелом §10 (ADR-0008, ADR-0032).

**И-8. Вид карты — явное поле.**
`chart_kind` проставляется движком в результате расчёта и передаётся дальше как
данные; выводить вид по отсутствию домов запрещено (ADR-0008).

**И-9. Реестры заполняются на старте и дальше только читаются.**
`ScenarioRegistry`, `PromptRegistry`, `ToolRegistry` наполняются при инициализации;
регистрация чего-либо во время обработки запроса запрещена. Согласованность
реестров проверяется на старте (ADR-0020).

**И-10. Ошибка после начала стрима доставляется событием внутри потока.**
После отдачи 200 и первого события HTTP-код уже не изменить (ADR-0012).

**И-11. Недостаточность данных выражается одним типом.**
`InputRequired` содержит `issues[]`; каждый issue задаёт `field` как путь
в контракт и `code`. Тип используется resolver и предусмотрен для будущих
`ContractValidator` и `Planner`; технические отказы имеют отдельные исходы
(ADR-0007).

**И-12. Кэш расчётов воспроизводим.**
Запись можно удалить без потери пользовательского ввода: сессия сохраняет
`ResolvedBirthData` и `ChartSpec`, а ключ строится из `CalculationInput`, spec
и `CalculationVersion`. Для космограммы input включает digest домена времени.
Изменение версии расчёта даёт новый ключ (ADR-0017, ADR-0032).

**И-13. Состояние меняется только явной типизированной командой.**
Построение/изменение карты начинается со структурированного ввода формы;
реализованный handler принимает `BuildNatalCommand` и возвращает дельту.
Целевой flow передаёт её в CAS с исходной версией; упоминание даты в диалоге
не мутирует состояние. Полный reset использует тот же механизм версий.
`SetActiveView` вернётся вместе с производными картами после первого среза
(ADR-0014, ADR-0016).

**И-14. Сроки жизни данных определяются их контуром хранения.**
Session state и dialog ограничены TTL; долговременной пользовательской History
нет. Calculation Cache хранит сериализованный полный артефакт по собственной
LRU/TTL policy и не очищается автоматически при удалении сессии. Research
Corpus хранит разрешённую проекцию бессрочно по ADR-0023; будущий сырой
consented-корпус требует отдельного проверяемого opt-in. Полный локальный
DEBUG-журнал является принятым исключением по ADR-0025/0028. Границы
удалённого стенда и публичного трафика задаёт ADR-0034 и §4.12.

**И-15. Дорогая операция не начинается без резервации.**
Вызов модели выполняется только после атомарного резервирования бюджета и только
при промахе кэша интерпретаций. Резервация имеет lease с TTL (ADR-0013).

---

## 3.1 Обоснования

### И-1 — почему текст не идёт вниз

Нормализация вопроса ограничивает формат и стоимость, но не превращает текст
в доверенные инструкции. Интерпретационная модель не управляет расчётом,
инструментами, секретами или чужим состоянием. Вопрос передаётся отдельным
слотом; результат проверяет `OutputGuard`. Подписка регулирует доступ и расход,
но не заменяет эту границу (ADR-0018).

### И-4 — что следует из stateful-прогона

Внутри операции application coordinator держит исходную версию состояния
и результат handler, Agent Runtime — план и результаты tools, а interpretation
pipeline — поток и резервацию бюджета. Это состояние одного прогона.
Резервация обязана иметь lease с TTL на случай падения процесса (ADR-0013).
`run_id` служит корреляции, а не возобновлению: durable recovery незавершённого
прогона в MVP отсутствует (ADR-0012).

### И-8 — почему вид карты хранится, а не выводится

`ChartSpec.chart_kind` фиксирует намерение, `NatalChart.chart_kind` — вид
полученного результата. Их согласованность проверяется на границах, а поле
передаётся в artifact, Evidence и UI без повторного вывода по составу данных
(ADR-0008, ADR-0027).

Текущий контракт требует `houses` для натала и запрещает `houses`, `rulers`,
`strength` для космограммы. Натал с исключёнными домами не является допустимым
примером. Явный вид определяет правила расчёта, рецепты и ограничения ответа.

### И-9 — почему реестры неизменяемы и проверяются на старте

Изменение реестра во время запроса делает поведение зависимым от истории
обращений. Поэтому целевой runtime загружает и проверяет реестры на старте:
каждый tool, recipe и используемый mode существуют; отсутствующая зависимость
блокирует startup, recipe без ссылок даёт предупреждение (ADR-0020).
Наличие текущих классов реестров не означает готовности всей этой проверки.

### И-12 — почему кэш, а не хранилище

Ключ является хэшем и сам не позволяет восстановить карту. В MVP сессия хранит
`birth_resolved` и `base_chart.spec`; из них и текущей `CalculationVersion`
можно повторить расчёт. `ChartSpec` описывает методику и состав результата,
но не содержит дату и координаты рождения. При смене версии строится новый
артефакт под новым ключом; старый числовой результат без прежнего окружения
не обещается (ADR-0017).

Девятикомпонентный отпечаток учитывает код, расчётные профили, native backend
и эфемериды. `ApplicationRuntime` вычисляет его при startup и передаёт в
resolver; сквозной cache miss → hit подтверждает этот production wiring.
Research Corpus — отдельная разрешённая проекция для исследования, а не
хранилище полных карт для восстановления (ADR-0023).

### И-13 — почему мутация только явная

В диалоге пользователь называет даты по разным причинам: исправляет свои,
спрашивает гипотетически, говорит о другом человеке, приводит дату события.
Автоматическая перезапись при каждом обнаружении даты сделала бы состояние
нестабильным: «а что изменилось бы, если бы я родилась в 01:15?» не означает
`base_birth_time = 01:15`.

Явная команда даёт ещё одно свойство — предсказуемый момент инкремента
`state_version`, а значит проверяемую защиту от stale-записи, когда медленный
запрос завершается после более свежего изменения.

---

## 4. Компоненты

### 4.1 Клиент

**Birth Form** — единственный источник данных рождения (ADR-0019).
Обязательны дата и место, время опционально. Город выбирается из подсказок,
наружу уходит `place_id`; координаты, `tz_id` и смещение определяет backend.
M1 добавляет отдельную страницу условий и неотмеченный по умолчанию checkbox:
до подтверждения ознакомления UI не отправляет build request. Отметка является
presentation gate, не входит в доменную команду и не сохраняется; она не
доказывает отдельного юридического согласия (ADR-0034).

**Chart page** — визуализация, базовые данные, явные контролы их изменения,
preset-действия, чат при наличии capability. Переключение вида появится вместе
с производными картами после первого MVP-среза (ADR-0016).

**Chart Renderer** — `Chart DTO → SVG`. Чистая функция, живёт на клиенте.

**Статус:** клиент не реализован.

### 4.2 API

**Session Middleware** — устойчивая `HttpOnly` cookie (`Secure`, `SameSite`)
→ анонимный `session_id`. Закрытие страницы сессию не уничтожает.

**Три бизнес-операции** соответствуют трём классам стоимости (ADR-0013, ADR-0015):
`Build Chart` (без LLM), `Selection` (preset), `Message` (free-form, подписка).

**CLI (`cli.py`)** — параллельная ветка прямого расчёта, минующая агентский стек.
Инструмент разработчика; natal/cosmogram/transit доступны без HTTP и сессии.
Его локальная диагностика относится к исключению §4.12.
**Статус:** CLI реализован; HTTP API и Session Middleware не реализованы.

### 4.3 Координация

**ApplicationOrchestrator** — загрузить контекст → выбрать и вызвать handler
→ сохранить дельту → классифицировать исход → завершить операцию.
Он сохраняет исходную `expected_state_version`, передаёт её в
`ContextService.save` и координирует lifecycle канала для streaming-операций.
Не выбирает tools и не принимает policy-решений (ADR-0006, ADR-0020).
**Статус:** application core реализован в
`exact_orb.application.orchestrator`; минимальная сборка для
`BuildNatalCommand` находится в `exact_orb.application.composition`. Каркас
`exact_orb.orchestration.Orchestrator` относится к агентскому слою.

**BuildNatalHandler** — резолв → выбор natal/cosmogram → получение артефакта
→ `BuildNatalOutcome`. Успех содержит `artifact` и подготовленную `StateDelta`;
handler не выполняет commit. **Статус:** реализован.

**InterpretSelectionHandler / InterpretMessageHandler** — целевые владельцы
интерпретационных flow, вызывающие Agent Runtime. **Статус:** не реализованы;
message-путь отложен до подписки.

Внешний `ApplicationResult` реализован как union десяти моделей. После расчёта
он различает успех/`AlreadyApplied`, `Superseded`, отсутствие сессии и
типизированный технический отказ commit.
Retry неподтверждённого commit повторяет исходные expected и delta без rebase
(ADR-0014). [Подробный контракт Build Natal](component_responsibilities/exact-orb_build_natal_components.md).

### 4.4 Сессия

**ContextService** — application-граница session persistence: `create`, `load`,
`save`, `append_turn`, `clear_dialog`, `reset_all`, `delete`. Получает один
`SessionPersistence`; `load` выполняет агрегатный `touch`, а `save` передаёт
исходные `expected_state_version` и `StateDelta` в CAS.

```text
SessionState {
session_id
birth_input: BirthInput | None
birth_resolved: ResolvedBirthData | None
state_version
base_chart: { state_version, spec: ChartSpec } | None
created_at
expires_at
hard_expires_at
}
```

Хранятся оба представления данных рождения: только `birth_input` означал бы,
что обновление `tzdata` молча сдвинет карту, только `birth_resolved` — что нечего
показать в форме.

**Session Store** — состояние с TTL и compare-and-set. **Dialog Store** хранит
ходы отдельно: append/clear не меняют `state_version`. Агрегат
`SessionPersistence` владеет общими `touch`, `reset` и `delete`. Производных
полей в MVP нет; сессия хранит только `base_chart` (ADR-0016).

Долговременного `Profile DB` нет.
**Статус:** contracts, `ContextService`, InMemory и SQLite adapters реализованы.

### 4.5 Резолв места и времени

**BirthDataResolver** — вызывается до planning и calculation. В текущем
Build-пути вход — `BirthInput(birth_date, birth_time?, place_id)`, без
`place_text` и других типов intent-слоя. Свободный текст места относится
только к отложенному natural-language пути. Выход — `ResolvedBirthData`,
`InputRequired` либо `ResolutionUnavailable`. Техническая недоступность
зависимости не превращается в просьбу исправить ввод. В состояние resolver
не пишет: результат обрабатывает handler.

**PlaceCatalog** — реализованный async-порт
`lookup(place_id) → ResolvedPlace | PlaceNotFound`. Production leaf-adapter
`SqlitePlaceCatalog` читает generated SQLite; `LocalPlaceCatalog` остаётся
test-adapter над JSONL fixture. Форма передаёт выбранный ID: список кандидатов
и `RemoteGeocoder` не входят в текущий build-контракт. Технический отказ
каталога передаётся типизированной ошибкой.

**PlaceSearch** — реализованный отдельный async-порт подсказок. Он не расширяет
`PlaceCatalog` и не проходит через `ApplicationOrchestrator`.
`SqlitePlaceCatalog` реализует оба порта над одним read-only выпуском данных:
будущий endpoint поиска получает ограниченные подсказки, а
`BirthDataResolver` повторно проверяет выбранный недоверенный `place_id`.
Контракты, ограничения и приёмка зафиксированы в
[требованиях каталога мест](component_responsibilities/exact-orb_place_catalog.md).

**Historical TZ Resolver** — `zoneinfo`/`tzdata`: декретное время, летнее и зимнее,
отмены 2011 и 2014 годов. Несуществующее и удвоенное локальное время дают явный
исход, а не исключение и не молчаливую догадку.
Проверочный кейс: 02.09.1990, Москва → UTC+4, локальные 14:30 = 10:30 UTC.
При неизвестном времени birth/timezone-слой формирует `BirthTimeDomain` из
всех валидных минут локальной даты; расчётный слой получает готовый UTC-домен
и не резолвит timezone повторно (ADR-0032).
**Статус:** catalog core M1-5 реализован и принят; HTTP wiring и UI остаются
M1-6/M1-7.
[Контракты резолва](component_responsibilities/exact-orb_birth_data_resolution.md),
[контракты каталога мест](component_responsibilities/exact-orb_place_catalog.md).

### 4.6 Понимание запроса

**ActionContractBuilder** — `topic + focus` и базовая карта текущего
`SessionState` → `ContractDraft`. Отдельный выбор `active_view` появится только
вместе с производными картами.
Вероятностного шага нет. Основной путь MVP.

**InputGuard** — нормализация, **лимит длины входа**, детект инъекций
→ `GuardVerdict` как отдельный объект, а не поле запроса.

**IntentService** — свободный текст → `UnderstandingResult { contract_fields,
interpretation_query }`. Только подписочный путь. Данные рождения не извлекаются
(ADR-0019). Rule-based understanding и детектор попытки изменить данные рождения
относятся к будущему пути; детектор должен вернуть `InputRequired` с кодом
`UNSUPPORTED`. Это требование, а не существующая реализация.

**ContractValidator** — схема и семантика → `ResolvedContract` либо `InputRequired`.
**Статус:** всё новое.

### 4.7 Policy, capabilities и admission

**CapabilityService** — сессия/аккаунт/тариф → `CapabilitySet`. В demo возвращает
набор без `freeform_interpretation`; его точка вызова должна присутствовать
уже в demo-flow (ADR-0020).

**PolicyService** — заменяет прежний `ToolPolicy`. Покрывает и допустимость
инструментов с аргументами, и допустимость пользовательского вопроса:
→ `AuthorizedPlan` | `AuthorizedInterpretationQuery` | `PolicyDenied`.

**AdmissionControl** — три точки вызова: access и IP rate limit на транспорте;
abuse-сигналы перед пониманием; атомарная резервация бюджета перед LLM (И-15).
Лимиты различают классы операций: `calculation` требует собственных ограничений
по сессии, IP и одновременной нагрузке на сериализованный движок.
Глобальный дневной потолок стоимости обязателен (ADR-0013; §7).
**Статус:** новое.

### 4.8 Agent Runtime

Каркас закладывается сразу, логика минимальна: дорого стоит не логика,
а точки вызова (ADR-0020).

**ScenarioRegistry** — литеральный словарь. Обязан содержать минимум два сценария
с различающимися `tools[]` и `topics[]`, иначе И-3 не проверена.

**Planner** — поиск по реестру и проверка required fields → `InterpretationPlan`
либо `InputRequired`. Разрешения графа зависимостей нет: связывание шагов
декларативно в записи сценария.

**Tool** — agent-facing порт общей детерминированной capability.
Требование следующего runtime-этапа — **асинхронный порт сразу** (ADR-0020).
Текущий `Tool.run` синхронный; `NatalTool` вызывает `calculate_natal()` напрямую.
Перевод на общий `ChartArtifactResolver` и async-контракт ещё не выполнен.
`RemoteTool` отложен; сеть внутри монолита не вводится.

**ToolExecutor** — последовательный цикл с передачей результата предыдущего шага
в аргументы следующего. Таймауты и лимит шагов — позже.
**Статус:** интерфейс Planner, orchestration-каркас, Tool/Prompt registries и
`NatalTool` существуют. Целевые `ScenarioRegistry`, `ToolExecutor`, pipeline и
startup-проверка согласованности реестров ещё не реализованы.

### 4.9 Артефакты и кэши

**ChartArtifactResolver** — `get → miss → calculate → put`. Не репозиторий:
любой объект удаляем без потери пользовательских данных (И-12).
Cache hit проверяется на соответствие запросу; повреждённый payload приводит
к пересчёту. Отказ кэша не блокирует доступный расчёт. Одновременные запросы
одного ключа разделяют одну задачу расчёта в пределах resolver/event loop
(single-flight), но получают независимые экземпляры результата.

**`calculation_input_from` / `calculation_key`** — чистая проекция
`ResolvedBirthData → CalculationInput`, затем
`(CalculationInput, ChartSpec, CalculationVersion) → key`.
В input входят UTC-момент, `latitude`, `longitude` и
`birth_time_domain_digest` (обязателен для космограммы, `None` для натала).
Формат ключа — `eo:calc:v2:<sha256>`; имя места и presentation-данные в ключ
не входят. Одного `ChartSpec` для построения ключа недостаточно.

**CalculationCache** хранит opaque `bytes`. Кодирование и валидация принадлежат
артефактному слою. Реализован InMemory LRU/TTL cache; SQLite для кэша — отдельный
этап по ADR-0024, Redis не вводится.

`CalculationResult` содержит только рассчитанный `chart`; `ChartArtifact` —
только `calculation_key`, `spec`, `calculation_version` и artifact-safe chart.
Артефакт локально проверяет chart/spec/key, cache hit — соответствие текущему
запросу, а `BuildNatalSuccess` сквозным validator связывает resolved data,
spec, chart, key и delta (ADR-0027). Отдельная версия схемы артефакта не
вводится.

**CalculationVersion** — отпечаток кода движка, версии `swisseph`
и его Python-дистрибутива/native module, содержимого расчётных профилей и
файлов `ephe/*.se1`, замороженных методики Селены, набора тел и флагов.
Сбор record и startup-логирование отделены от чистого хэширования; module-level
вычисленного значения нет. Механизм, wiring в `ApplicationRuntime` и сквозной
cache miss → hit через публичную runtime-границу реализованы и приняты.

**Interpretation Cache** — целевой отдельный кэш. Для preset ключ
`calculation_key + topic + focus + recipe_version + model`; запись разделяема
между пользователями и живёт вне session store (ADR-0013). Для free-form ключ
дополнительно включает `session_id` и хэш вопроса, запись живёт не дольше сессии;
по существу это защита от повторного списания при двойном клике и refresh,
а не экономия.
**Статус:** расчётные spec/input/key/version, engine, codec, cache и resolver
реализованы; process runtime wiring также реализован. Interpretation Cache и
подключение runtime к HTTP lifecycle не реализованы.
[Требования к артефактам](component_responsibilities/exact-orb_chart_artifacts.md).

### 4.10 Расчёт — EngineService

`EngineService` реализует async `CalculationEnginePort`: принимает
`ChartSpec + ResolvedBirthData` и `RunContext`, возвращает
`CalculationResult(chart)`. `ChartArtifact` формирует resolver выше.
Расчёт исполняется через переданный executor внутри процесса; Swiss Ephemeris
защищён процессным `RLock`. Единственный импорт `swisseph` — `swiss_backend`.
Контракты не передают native-объекты; типизированные отказы маппируются
в `CalculationFailed` на уровне handler. **Статус:** реализовано.

**`engine/ephemeris`** — `types.py` (модели, таблицы) и `calc.py` (операции),
зависимость однонаправленная. Ничего не знает о технике; метку
`BodyPosition.chart` получает от chart-level вызывающего кода.
**Статус:** реализовано.

**`engine/charts/natal.py`** — `calculate_natal()` с обязательным
`chart_kind: Literal["natal", "cosmogram"]`. `include` — белый список из
`DEFAULT_INCLUDE = {positions, houses, rulers, aspects, configurations, strength}`;
незнакомые имена дают `ValueError`, невключённые блоки становятся `None`.
Космограмма — `include = {positions, aspects, configurations}`; `strength`
исключён, так как требует `houses`.
Натал требует `houses`; `configurations` требует `aspects` у обоих видов карт.

Для космограммы обязателен `BirthTimeDomain`. Позиции относятся к опорному
моменту, но аспекты проверяются на всём множестве допустимых минут: публикуются
только отношения с неизменным типом и категорией, `orb` равен максимальному
орбису. Неустойчивые пары описывает `NatalChart.time_uncertainty`, а конфигурации
строятся из устойчивых аспектов. Отсутствующая на всём домене пара не создаёт
ни аспект, ни запись неопределённости (ADR-0032).
**Статус:** реализовано.

**`engine/charts/transit.py`** — `calculate_transit()` принимает отдельный
`moment` расчёта позиций и именованный `exact_window` поиска точных дат и
станций (ADR-0001). Требует домов и углов базовой карты; для космограммы
этот путь недоступен. **Статус:** ядро и CLI реализованы; application-путь
транзитов и `TransitChartSpec` отложены по ADR-0016.

**`aspects` / `configurations` / `strength`** — детерминированные расчётные блоки.
Текущий контракт включает единые идентификаторы точек (ADR-0029), `true_node`
как представителя оси в отношениях при сохранении позиции `south_node`
(ADR-0030), целостность вложенных аспектов и топологии конфигураций (ADR-0031).
`StrengthConfig.dignity_system` одинаково управляет достоинствами,
диспозиторами и взаимными рецепциями; `ChartSpec.rulership` относится к
управителям домов и интерцепциям (ADR-0033).
**Статус:** реализовано. [Расчётные требования](component_responsibilities/exact-orb_calculation_requirements.md).

### 4.11 Интерпретация

**InterpretationService** — владеет конвейером целиком: `Evidence` →
`PromptBundle` → кэш → резервация → LLM → `OutputGuard` → кэш. Вынос конвейера
сюда — противоядие от god-object в оркестраторе (ADR-0006).

**DataSelector** — `InterpretationPlan + ToolResults → Evidence`. Фокусы работают
здесь и только здесь; расчёт о них не знает. При нескольких фокусах наборы
объединяются с дедупликацией. Обязан переносить `warnings` (И-7).

**PromptBuilder** — один `PromptBundle`. Принимает только
авторизованный свободный вопрос (`AuthorizedInterpretationQuery`) и помещает
его в отдельный делимитированный слот вместе с остальными данными промпта.
Слот присутствует в рецептах с первого дня и в demo пуст.

**PromptRegistry** — рецепты, читаемые с диска на старте (И-9).
Рецепт физически — файл с заголовком (`id`, `topic`, `focus`, `mode`,
`chart_kind`, `evidence`, `forbids`, `max_tokens`) и телом промпта;
`recipe version` из ключа кэша равен хэшу содержимого, поэтому правка
формулировки инвалидирует кэш сама. Рецепты **композиционные**:
`base.<topic> + focus.<focus> + mode.<mode> + kind.<chart_kind>`, иначе матрица
комбинаций растёт до двух десятков независимо написанных промптов, которые
неизбежно разъедутся по тону. `forbids` — одновременно инструкция модели
и проверяемое утверждение для теста и `OutputGuard`.

**LLM Gateway** — транспорт. Требует: профилей по назначению, метода
`complete_stream()` рядом с `complete()`, потолка `max_tokens`. Сейчас
`_reject_ambiguous_kwargs` явно запрещает `stream=True`. Полные локальные
логи промптов/ответов относятся к принятому ограничению §4.12.

**OutputGuard** — вход недоверен, значит недоверен и выход: в free-form режиме
обязателен.
**Статус:** скелеты, Gateway реализован и требует расширения.
Текущий `InterpretationPlan` в `intent/types.py` также относится к раннему
каркасу: он ещё не реализует целевой контракт `tools[]`/`topics[]` из §5.

### 4.12 Платформа

**`config.py`** — цепочка «аргумент → env → `[tool.exact_orb]` → дефолт».
Расширяется конфигурацией инструментов, профилями моделей и лимитами.
**Статус:** реализовано.

**`logging_setup.py` / `component_logging.py`** — общий envelope помечает
компонент, `run_id`, доступный `calculation_key`, статус, тип сообщения и режим
payload. Путь Build Natal по ADR-0025/0028 сохраняет полные входящие и
исходящие сообщения всех пяти границ только на DEBUG; summary-режима нет.
ADR-0035 добавляет отдельную полную DEBUG-запись входа в
`ApplicationOrchestrator.execute` до вызова Handler.
ADR-0036 добавляет INFO-записи отправки и получения прямых сообщений
Orchestrator с ContextService и Handler без тел сообщений.
ADR-0037 добавляет парные DEBUG-сообщения `ContextService` и INFO-сообщения
Handler о прямых вызовах resolver и artifact resolver.
При отключённом DEBUG payload и logging-проекции не сериализуются. Это сознательная
диагностика локального стенда; она сохраняет birth-data и итоговую карту за
пределами TTL сессии.

ADR-0034 выбирает для будущего контролируемого удалённого M1-стенда effective
`INFO`: полный boundary payload ADR-0028 при этом не формируется, но это не
доказывает отсутствие персональных данных во всех INFO/WARNING-событиях и
других контурах. Локальный CLI сохраняет default `DEBUG`. Серверная настройка
и guard от случайного `DEBUG` относятся к M1-12 и ещё не реализованы;
маскирование или защищённая маршрутизация остаются M3-8 и возвращаются раньше
при включении `DEBUG` на сервере.
**Статус:** полный локальный журнал реализован; серверный INFO-profile и
privacy-hardening не реализованы.

**Хранилища** развиваются за отдельными портами: InMemory для тестов,
SQLite для стенда, PostgreSQL при появлении условия перехода (ADR-0024).
SQLite сейчас реализован для session persistence; это не означает готовности
SQLite-кэшей и Research Corpus. `ApplicationRuntime` M1-5.1 владеет lifecycle
executor'ов и предоставляет one-shot session reaper с единым UTC clock.
Периодическое расписание reaper принадлежит FastAPI lifespan M1-6.

### 4.13 Research Corpus

Отдельный контур качества интерпретаций по ADR-0023, заменившему ADR-0010.
`project_chart_features` строит whitelist-проекцию `ChartArtifact → ChartFeatures`;
`ResearchCorpus` принимает базовые записи и append-only quality events.
Research v1 ограничен natal/cosmogram и фокусами `general`, `career`, `money`,
`love`; транзитная запись требует отдельного контракта.

Always-on корпус не содержит прямых ID, birth input, точных координат/времени,
`calculation_key`, query/response text или полного артефакта. Это de-identification
с принятым остаточным linkage-риском, а не обещание анонимности. Бессрочный
retention и отсутствие удаления по кнопке сессии заданы отдельно в ADR-0023.
Будущий consented-корпус с сырым контентом требует opt-in и отдельной схемы.

**Статус:** contracts, whitelist-проекция и InMemory adapter реализованы.
SQLite и application producer wiring отложены; утверждение «каждый готовый
ответ записан» текущая реализация не обеспечивает.
[Требования Research Corpus](component_responsibilities/exact-orb_research_corpus.md).

---

## 5. Контракты данных

### 5.1 Реализованные контракты

| Контракт | Граница | Ключевое |
|---|---|---|
| `BirthInput` / `BuildNatalCommand` | Caller → Handler → Resolver | `birth_date`, `birth_time?`, `place_id`; команда содержит `birth_input`, `session_id` в неё не входит |
| `ResolvedBirthData` | Resolver → Handler / ArtifactResolver / Engine | `canonical_place`, `latitude`, `longitude`, `tz_id`, `utc_offset_seconds`, `utc_datetime`, `time_unknown`, `birth_time_domain`, `warnings` |
| `BirthTimeDomain` | Birth/timezone → Calculation | каноническое множество допустимых UTC-моментов с шагом в минуту |
| `InputRequired` | Resolver → Handler | `issues[{field, code, candidates?, constraints?}]`; `AMBIGUOUS` на build-пути относится к времени |
| `ResolutionUnavailable` / `CalculationFailed` | Компоненты → Caller handler | технические исходы с `error_code`; не заменяются `InputRequired` |
| `RunContext` | Caller → компоненты операции | `run_id`, `started_at`; модуль `exact_orb.run_context` |
| `ChartSpec = NatalChartSpec` | Handler → ArtifactResolver / Engine | техника, вид карты, include и параметры расчёта; данные рождения передаются отдельно |
| `CalculationInput` | Проекция resolved → key | UTC, координаты, digest домена времени; вместе со spec и version определяет key v2 |
| `CalculationResult` | Engine → ArtifactResolver | только `chart: NatalChart` |
| `ChartArtifact` | ArtifactResolver → Handler | `calculation_key`, `spec`, `calculation_version`, artifact-safe `chart` |
| `BuildNatalSuccess` / `BuildNatalOutcome` | Handler → Caller | успех: `artifact + delta`; union также включает `InputRequired`, `ResolutionUnavailable`, `CalculationFailed` |
| `StateDelta` | Handler → будущий Orchestrator → ContextService | полная замена `birth_input`, `birth_resolved`, `base_chart_spec` либо all-None reset; expected version отдельно |
| `SessionState` / `SessionSnapshot` | Session persistence → ContextService → Caller | состояние с TTL/CAS; snapshot объединяет state и отдельный dialog |
| `ToolRequest` / `ToolResult` | Текущий Tool port | `tool_name + args`; результат: `tool_name`, `data`, `warnings`, `meta`; текущий вызов синхронный |
| `PromptBundle` | Контракт подготовки промпта | `system`, `user`, `recipe_id`; модель существует, полный pipeline ещё не собран |
| `ChartFeatures`, `ResearchRecord`, quality events | Producer → ResearchCorpus | закрытая проекция и отдельные append-only события без session/calculation IDs |

### 5.2 Целевые контракты

Эта таблица описывает требования к ещё не реализованным потокам. Существующий
`intent.types.InterpretationPlan` имеет раннюю форму с `required_tools`,
`data_selectors`, `prompt_recipe` и пока не соответствует целевой строке ниже.

| Контракт | Граница | Ключевое |
|---|---|---|
| Transport DTO | Form ↔ HTTP API | отображение ввода/карты и типизированных исходов; HTTP-слой ещё не реализован |
| `ApplicationResult` | ApplicationOrchestrator → API | результат всей операции после commit: успех, `AlreadyApplied`, `Superseded`, отсутствие сессии или типизированный отказ |
| `UnderstandingResult` | IntentService → Handler | `contract_fields`, `interpretation_query` |
| `GuardVerdict` | InputGuard → Admission / Policy | `decision`, `reasons`, `rules` |
| `InterpretationQuery` | Understanding → Policy | `normalized_text`, `language`; недоверенные данные |
| `AuthorizedInterpretationQuery` | Policy → PromptBuilder | разрешённый policy текст остаётся недоверенным |
| `CapabilitySet` | CapabilityService → application flow | разрешённые классы операций и лимиты |
| `ResolvedContract` | Validator → Agent Runtime | проектируется от free-form; preset заполняет подмножество. **Сырого текста нет** |
| `ScenarioDefinition` | Registry → Planner | `id`, `required_fields[]`, `tools[]`, `topics[]` |
| `InterpretationPlan` | Planner → Agent Runtime | `scenario_id`, `tool_requests[]`, `topics[]` как список `{tool, recipe, mode}` |
| `Evidence` | DataSelector → PromptBuilder | факты по темам, предупреждения и ограничения точности |
| `StreamEvent` | Application flow → канал | `status` / `input_required` / `token` / `done` / `error` |

---

## 6. Транспорт и стриминг

Целевой транспорт по ADR-0012: операции без LLM — обычный request/response,
операции с генерацией — SSE. HTTP endpoints и streaming Gateway ещё не
реализованы; готовый `BuildNatalHandler` сам HTTP-ответ не формирует.

События: `status`, `input_required`, `token`, `done`, `error`.
Событие `clarification` из версии 1.0 переименовано в `input_required` вслед
за ADR-0007.

Внутри хода клиент привязан к реплике; `run_id` — корреляционный идентификатор
для наблюдаемости, не хэндл возобновления (§3.1, И-4).
`BuildAttempt`, `build_revision` и durable recovery относятся к
[отложенным сценариям](../sequence_diagrams/deferred/build_attempt/README.md).
Актуальность build-результата в целевом MVP обеспечивается CAS по `state_version`.

Финализация после конца потока: накопленный текст пишется в ходы сессии.
При обрыве со стороны пользователя полученное сохраняется — токены уже оплачены.

---

## 7. Стоимость и лимиты

Ниже — требования ADR-0013 к будущему admission/budget flow, а не уже
подключённые ограничения. Бюджет расходуют interpretation operations;
`InputRequired` и расчёт карты не требуют LLM. Повторный расчёт берётся из
кэша при наличии валидной записи, иначе выполняется заново.

| Класс | LLM | Доступен | Расходует бюджет |
|---|---|---|---|
| `calculation` | нет | всем | нет |
| `preset_interpretation` | да | всем | да |
| `freeform_interpretation` | да | по подписке | да |

Класс `calculation` имеет собственные ограничения: 20 построений в час и
100 в сутки на сессию, отдельный IP-лимит и потолок одновременных расчётов
с быстрым `503` при перегрузке. Значение IP-лимита определяется при реализации
HTTP-транспорта. Процессный `RLock` обеспечивает корректность Swiss Ephemeris,
но не заменяет admission и не увеличивает пропускную способность.

**Ограничения ставятся с обеих сторон.** Длина вопроса ограничивается
`InputGuard` на входе, объём ответа — `max_tokens` на выходе. Учёт расхода
ведётся в стоимости, а не в токенах: вход и выход тарифицируются по-разному.

**Иерархия защиты, от мягкой к жёсткой:**

1. лимит длины входа и `max_tokens` на ответ — на каждый вызов;
2. кэш интерпретаций — повтор не оплачивается дважды;
3. лимит стоимости на сессию — защищает от честного перерасхода, но **не
   является защитой от злоупотребления**: сессия анонимна и сбрасывается
   вместе с cookie;
4. лимит по IP с привязкой к классу операций и CAPTCHA при необходимости — против массового обхода;
5. **глобальный дневной потолок** — единственная мера, которую нельзя обойти,
   с деградацией сервиса при достижении.

**Значения.** Предварительные лимиты задаются с первого дня: публичное demo
без них выкатывать нельзя. Потолок считается из юнит-экономики — стоимость одной
интерпретации × приемлемый дневной расход. Фокус-группа на MVP уточняет другое:
хватает ли пользователю сессионного лимита для осмысленной работы. Эти два числа
приходят из разных источников и совпадать не обязаны.

---

## 8. Объём MVP

Плановый пользовательский MVP: построение одной базовой natal/cosmogram карты
и preset-интерпретация. Наличие компонента в этом списке не означает его
готовности; фактические статусы — §2.1.

**Входит:** клиент с формой и renderer, Session Middleware, Build API,
ApplicationOrchestrator, BuildNatalHandler, BirthDataResolver,
`SqlitePlaceCatalog` (`LocalPlaceCatalog` только для тестов), Historical TZ,
ContextService, Session Store, Dialog Store,
ChartArtifactResolver, calculation_key, CalculationVersion, Calculation Cache,
EngineService, Selection API, InterpretSelectionHandler, ActionContractBuilder,
ContractValidator, каркас рантайма, InterpretationService, Gateway, OutputGuard,
AdmissionControl с бюджетными и расчётными ограничениями §7.

**Минимальная целевая реализация:** CapabilityService возвращает набор без
free-form, PolicyService выполняет правила demo, InputGuard ограничивает длину
и управляющие символы. Точки вызова должны появиться при сборке этого flow;
сейчас эти компоненты не реализованы (ADR-0020).

**Отложено:** IntentService и весь free-form путь до появления подписки,
RemoteGeocoder, RemoteTool, распознавание данных рождения в тексте (ADR-0019).
Транзиты в application-срезе, `derived_chart`, `active_view` и `SetActiveView`
возвращаются вместе по ADR-0016. Research v1 подготовлен для natal/cosmogram;
его durable persistence и подключение producer остаются отдельными задачами.

**Качество интерпретаций требует отдельной работы.** Для natal предусмотрены
фокусы `general`, `career`, `money`, `love` и ограничения natal/cosmogram.
Расширение матрицы на транзиты относится к следующему срезу. Правила отбора
фактов и рецепты требуют eval-набора и проверки человеком: технический проход
pipeline сам по себе не доказывает качество ответа по выбранному фокусу.

---

## 9. Порядок работ

Порядок актуализирован 2026-09-14 по [roadmap](../project_management/roadmap.md).
Выполненные части сохраняются в плане и повторно не ставятся в очередь.

**Выполненная основа.** Расчётное ядро и прямой CLI; резолв рождения;
расчётный кэш, артефакты и `CalculationVersion`; session contracts,
`ContextService`, InMemory и SQLite persistence; Research P5a; функциональный
`BuildNatalHandler`; `ApplicationOrchestrator`, `ApplicationResult`,
commit/retry/cancellation/lifecycle flow, минимальная composition и реальный
интеграционный путь с SQLite; process-local `ApplicationRuntime`, strict
bootstrap settings, фактическая `CalculationVersion` и owned executors;
GeoNames SQLite builder, `PlaceSearch`, `SqlitePlaceCatalog`, индексированные
search/lookup и их сквозная application-приёмка.
Также реализованы нормализация результата и DEBUG-диагностика ADR-0027/0028,
семантика точек/оси узлов/конфигураций ADR-0029–0031, неизвестное время и
key v2 по ADR-0032, единая strength-система ADR-0033 и нормализация орбиса
на epsilon-границе. Обязательный import-boundary тест `BuildNatalHandler`
интегрирован в M1-4. LLM Gateway предоставляет синхронный transport.

**M1. Первый сценарий с UI на удалённом сервере.** Остаются: FastAPI и Session
Middleware, HTTP wiring готового каталога; первый UI с autocomplete; условия и
presentation checkbox по ADR-0034; отображение
рассчитанной карты; серверный INFO-profile, деплой и браузерная приёмка.
Build-путь не требует LLM или Agent Runtime.

**M2. Первая интерпретация.** На основе готового Gateway реализовать
`InterpretationService`, первый рецепт и прямой вызов из interpretation
handler, затем подключить API/UI. Предложенный короткий путь и ответ целиком
оформляются отдельным ADR до реализации: действующий целевой контракт
§2.2/§5 предусматривает Agent Runtime и SSE.

**M3. Runtime и остальное.** Agent Runtime, async Tool через общий
артефактный путь, согласованные реестры, полный interpretation pipeline,
расширенные рецепты и eval, cache/budget/streaming; дальнейшие работы по
эксплуатации, Research SQLite и producer wiring, CLI и развитию UI.

**Граница публичного запуска.** M1 описывает контролируемый удалённый стенд,
а не юридически готовый публичный сервис. До реального публичного трафика по
ADR-0034 должны быть отдельно определены правовое основание и роль оператора,
пользовательские документы, доказательство согласия, если оно требуется,
retention/delete для logs и session/cache, доступ к журналам и сторонние
получатели. Требования §7 также выполняются независимо от номера этапа.
Исторические замеры расчётов и выполненный benchmark SQLite P4 сохраняются
как факт; актуальные natal/cosmogram/transit и целевая серверная нагрузка
требуют отдельной проверки.

---

## 10. Открытые вопросы

- **Космограмма + транзиты.** Текущий `calculate_transit` требует домов и углов.
  Путь без них остаётся открытым; до его появления переход к derived-карте
  при базовой космограмме недоступен (ADR-0016, ADR-0032).
- **Предупреждения неизвестного времени.** Устойчивые аспекты реализованы по
  ADR-0032. Отдельные предупреждения ADR-0008 о смене знака и направления
  движения остаются ранее зафиксированным пробелом в
  [требованиях Build Natal, §4.6](component_responsibilities/exact-orb_build_natal_components.md).
- Место синастрии: `engine/charts` или отдельный слой сравнения карт.
- Граница возможного выноса в сервис обсуждается только при появлении
  наблюдаемого триггера. Сейчас действует модульный монолит по ADR-0021.
- Связность `AdmissionControl`: разделять ли на `RateLimiter`
  и `BudgetReservation`.
- Конкретное отображение типизированных application-исходов в HTTP и SSE
  предстоит реализовать на транспортной границе. После начала SSE технический
  отказ передаётся событием `error`, а не сменой HTTP-кода (ADR-0012).
- Пропускная способность: процессная сериализация Swiss Ephemeris уже
  реализована. Открыты целевой p95, настройки admission и необходимость
  масштабирования по результатам актуальных замеров.
- Пересмотр отказа от профилей при появлении регистрации и подписки.

---
