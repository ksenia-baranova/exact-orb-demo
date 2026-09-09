# Устранение повторной сериализации карты в DEBUG-журнале

## Задача

Исправь журналирование пути построения натальной карты:

1. перестань полностью сериализовать одну и ту же карту на выходе каждого
   внутреннего компонента;
2. сохрани наблюдаемость всех входящих и исходящих сообщений компонентов;
3. оставь одну полную DEBUG-копию результата на прикладной границе;
4. для поиска используй уже существующие `run_id` и `calculation_key`;
5. не вводи новый отдельный идентификатор карты и не меняй ради этой задачи
   модели результата расчёта или формат Calculation Cache.

Не ограничивайся визуальным сокращением строк. Исправление должно устранить
повторную полную DEBUG-сериализацию большого графа карты и закрепить это
тестами.

`prompts/**` — исторический журнал. Существующие промты не редактировать.

## Наблюдаемая проблема

Сейчас при успешном cache miss один и тот же большой результат попадает в
полный JSON как минимум в четырёх оболочках:

```text
NatalChart
→ CalculationResult
→ ChartArtifact
→ BuildNatalSuccess
```

В реальном интеграционном DEBUG-журнале эти четыре представления дают
основную часть размера файла. На cache hit остаются ещё две полные копии:
`ChartArtifact` и `BuildNatalSuccess`.

Корневая причина — универсальные обёртки `component_logging`, которые
безусловно сериализуют полный `request` и полный `result` каждой границы.

Техническую сериализацию `ChartArtifact` в gzip для Calculation Cache не
считать лишней DEBUG-сериализацией: это отдельная обязательная операция
хранения. Цель этой задачи — убрать повторное построение полного JSON карты
для журнала.

## Перед изменениями

1. Прочитай `AGENTS.md`.
2. Выполни и зафиксируй исходное состояние:

   ```text
   git branch --show-current
   git status --short
   git rev-parse HEAD
   ```

3. Не переключай и не создавай ветки.
4. Сохрани пользовательские и несвязанные изменения рабочего дерева.
5. Не создавай commit, push или PR без отдельного запроса.

## Источники истины

До проектирования изменения изучи как минимум:

```text
AGENTS.md
README.md
docs/requirements/decisions/README.md
docs/requirements/decisions/0017-calculation-cache-and-chartspec.md
docs/requirements/decisions/0021-modular-monolith-service-seams.md
docs/requirements/decisions/0025-debug-component-boundary-messages.md
docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md
docs/requirements/component_responsibilities/exact-orb_build_natal_components.md
docs/requirements/handlers/exact_orb_build_natal_handler_requirements.md
docs/requirements/overview.md
docs/architecture/service_ready_architecture.md
docs/architecture/exact_orb_architecture.puml
docs/architecture/exact_orb_high_level_abstraction.puml
docs/sequence_diagrams/chart_artifacts/README.md
docs/sequence_diagrams/chart_artifacts/*.puml
docs/sequence_diagrams/build_natal/README.md
docs/sequence_diagrams/build_natal/*.puml
src/exact_orb/component_logging.py
src/exact_orb/run_context.py
src/exact_orb/application/results.py
src/exact_orb/application/handlers/build_natal.py
src/exact_orb/birth/resolver.py
src/exact_orb/calculation/engine.py
src/exact_orb/calculation/artifacts.py
src/exact_orb/calculation/types.py
src/exact_orb/calculation/codec.py
src/exact_orb/calculation/keys.py
src/exact_orb/engine/charts/natal.py
tests/test_logging.py
tests/test_run_context.py
tests/test_calculation_engine.py
tests/test_calculation_engine_integration.py
tests/test_chart_artifact_codec.py
tests/test_chart_artifact_resolver.py
tests/test_calculation_block_integration.py
tests/application/test_build_natal_logging.py
tests/application/test_build_natal_integration.py
tests/test_module_boundaries.py
```

Сначала сопоставь новый контракт с существующим покрытием. Не ослабляй
архитектурные тесты и не подменяй требования текущей реализацией.

## Идентификаторы и поиск

Используй только существующие идентификаторы с разной семантикой:

| Поле | Назначение |
|---|---|
| `run_id` | связывает одну попытку прикладного запроса и её прохождение по компонентам |
| `calculation_key` | связывает одну каноническую карту по численно значимым входам, `ChartSpec` и `CalculationVersion`, включая cache hit |

Обязательные правила:

1. Не создавай дополнительный UUID, content hash, sequence number или иной ID
   результата карты.
2. Не добавляй поля идентичности в `NatalChart`, `CalculationResult`,
   `ChartArtifact`, `BuildNatalSuccess`, `ChartRef` или cache payload.
3. Не меняй семантику и формат `calculation_key`.
4. Не передавай cache identity в `EngineService`: движок по-прежнему не знает
   ключа Calculation Cache.
5. До получения артефакта поиск конкретного выполнения идёт по `run_id`.
6. После получения артефакта downstream-события содержат одновременно
   `run_id` и полный `calculation_key`.
7. На cache hit новый `run_id` связывается с тем же `calculation_key`.
8. При single-flight разные waiter `run_id` связываются с общим
   `calculation_key` на выходе resolver и handler.
9. Не добавляй `run_id` в аргументы детерминированной функции
   `calculate_natal()` и не используй скрытое mutable-состояние ради
   корреляции её внутренних логов.

`calculation_key` должен быть полным отдельным индексируемым полем в тех
событиях, где слой его достоверно знает. Short prefix можно сохранить как
дополнительное поле для чтения человеком, но он не заменяет полный ключ для
поиска.

## Контракт DEBUG-журнала

### 1. Все границы остаются видимыми

Сохрани парные события `direction=in` / `direction=out` для реализованных
границ:

```text
BuildNatalHandler.handle
BirthDataResolver.resolve
ChartArtifactResolver.ensure_chart
EngineService.calculate
calculate_natal
```

Нельзя просто удалить внутренние boundary-события. По журналу по-прежнему
должно быть видно:

- какой компонент получил сообщение;
- направление;
- операция;
- тип сообщения;
- успешный или ошибочный исход;
- `run_id`, если он доступен этому слою;
- `calculation_key`, если он уже известен этому слою;
- полный payload или компактная проекция записана.

### 2. Явный формат envelope

Расширь единый формат как минимум следующими полями:

```text
component_message
component=<stable component name>
direction=<in|out>
operation=<operation>
run_id=<uuid|->
calculation_key=<full key|->
status=<ok|error>
payload_mode=<full|summary|error>
message_type=<type>
message=<single-line JSON>
```

Если `component` уже гарантирован formatter/filter как отдельное поле
`LogRecord`, не создавай второй расходящийся источник. Но фактическая строка в
файловом журнале должна позволять однозначно определить компонент.

До вычисления ключа пиши `calculation_key=-`. Не пытайся вычислять ключ ещё
раз в logging helper: его создаёт и знает `ChartArtifactResolver`.

### 3. Полный payload карты — один раз

Для одной успешной обработки `BuildNatalHandler.handle` записывай полный
`BuildNatalSuccess`, включая `ChartArtifact` и карту, ровно один раз — в
финальном `direction=out` события handler с `payload_mode=full`.

На внутренних выходах не сериализуй полный граф карты:

- `calculate_natal` → `NatalChartSummary`;
- `EngineService.calculate` → `CalculationResultSummary`;
- `ChartArtifactResolver.ensure_chart` → `ChartArtifactSummary` с полным
  `calculation_key`, версией и признаком cache outcome;
- `BuildNatalHandler.handle` → полный `BuildNatalSuccess` один раз.

Минимальная полезная summary-проекция успешной карты должна включать:

```text
chart_kind
warning_count
body_count
aspect_count
configuration_count
has_houses
has_strength
```

Для артефакта дополнительно:

```text
calculation_key      # полный, не только short prefix
calculation_version
cache_outcome        # hit|miss, если слой это достоверно знает
```

Не включай в summary `bodies`, `cusps`, `angles`, `aspects`,
`configurations`, `strength` или вложенный полный `chart`.

Полные входные сообщения, которые не содержат рассчитанную карту, можно
оставить в DEBUG, поскольку это нужно для локальной разработки. Ошибки также
остаются полными компактными JSON-объектами с `payload_mode=error`.

### 4. Технические события

Добавь полный `calculation_key` во все технические и итоговые события после
его вычисления, где это не нарушает границы владения, включая как минимум:

```text
cache_miss
cache_hit
cache_stale
cache_corrupt
singleflight_join
build_natal_completed outcome=success
```

На cache hit выход artifact resolver и выход handler должны содержать тот же
ключ. На single-flight каждый waiter имеет свой `run_id`, но получает общий
ключ.

Не передавай ключ в `EngineService` только ради того, чтобы добавить его в
`calculation_started` или `calculation_finished`. Эти события связываются с
artifact resolver по `run_id`. Ошибки до вычисления ключа используют только
`run_id`.

### 5. Реализация сериализации

Универсальные `log_async_component_call` и `log_sync_component_call` не должны
безусловно сериализовать произвольный полный результат. Дай вызывающей
границе явный способ выбрать:

- full payload;
- summary projection;
- error projection;
- получение `calculation_key` из успешного результата там, где это допустимо.

Предпочти явные чистые проекторы/адаптеры сообщений с типизированным
контрактом. Не определяй режим по строковому имени класса, размеру JSON,
поиску ключа `bodies` в уже сериализованной строке или иной эвристике.

Не решай проблему:

- глобальным dedup-набором;
- TTL;
- кэшированием строк в mutable singleton;
- подавлением логов после первого совпадения;
- повторным `model_dump()` для построения summary;
- предварительной полной сериализацией с последующим усечением.

Summary должна строиться напрямую из типизированного результата и счётчиков,
не проходя по всему графу карты.

## Сохранение контрактов

В этой задаче не должны меняться:

```text
NatalChart
CalculationResult
ChartArtifact
BuildNatalSuccess
ChartRef
Calculation Cache payload schema
calculation_key format and semantics
CalculationVersion semantics
public error codes
numeric chart result
```

Если для сокращения логов требуется изменить одну из этих моделей или формат
кэша, остановись и сначала докажи необходимость: выбранное решение, вероятно,
находится не на ответственном logging-слое.

## Ошибки и конкурентность

Сохрани существующие типизированные ошибки и lifecycle:

- `ChartCalculationError` и `CalculationUnavailableError` проходят по
  действующему контракту;
- неизвестные runtime-исключения преобразуются ответственным слоем;
- отмена waiter не отменяет single-flight leader;
- не добавляй `sleep` и случайные задержки;
- cache hit не вызывает движок;
- single-flight возвращает независимые копии одного артефакта;
- уменьшение логов не добавляет глобального mutable-состояния.

## Тесты

Не дублируй существующие тесты. Расширь ближайшее покрытие и добавь
регрессионные проверки только там, где нового контракта ещё нет.

### Журналирование и сериализация

Проверь:

1. у каждой заявленной границы остались события `in` и `out`;
2. envelope содержит компонент, `run_id`, `calculation_key`, `payload_mode`,
   тип, направление и статус;
3. до вычисления ключа используется `calculation_key=-`;
4. artifact resolver и успешный handler output содержат полный ключ;
5. cache miss, hit, stale, corrupt и single-flight события содержат полный
   ключ, поскольку resolver его уже знает;
6. полный JSON `BuildNatalSuccess` появляется ровно один раз на успешный
   handler call;
7. внутренние `NatalChartSummary`, `CalculationResultSummary` и
   `ChartArtifactSummary` не содержат полный `bodies`/`aspects`/`chart`;
8. summary содержит корректные счётчики;
9. cache hit не порождает повторную полную сериализацию карты до финального
   ответа handler;
10. разные single-flight `run_id` можно связать с одним полным
    `calculation_key`;
11. error output остаётся полезным и не пытается сериализовать частичный
    результат карты.

Не доказывай отсутствие лишней сериализации только сравнением размера строки
или файла. Добавь spy/counter на явный full-payload serializer либо тестовый
объект, который фиксирует обращение к полной сериализации. Тест обязан
различать:

- одну разрешённую полную сериализацию для DEBUG-ответа handler;
- отдельную обязательную сериализацию кодеком для сохранения в Calculation
  Cache;
- построение компактных summary без полной сериализации карты.

Сохрани позитивный контроль: тест должен доказать, что финальная полная карта
действительно присутствует и пригодна для восстановления данных, а не только
что внутренние копии исчезли.

### Контракты и архитектурные границы

Добавь негативные проверки, что новая задача не изменила публичные модели и
cache payload. Существующие round-trip/golden-тесты должны пройти без
перегенерации ожидаемых данных.

`tests/test_module_boundaries.py` остаётся архитектурным инвариантом. Не
ослабляй deny-list, не добавляй прямой импорт `swisseph` и не передавай cache
identity в engine.

## Документация и ADR

Это изменение пересматривает принятое ADR-0025: там явно требуется полный
payload на каждой внутренней границе. Не исправляй противоречие молча и не
переписывай историю задним числом.

Создай новый ADR со следующим решением:

- он заменяет часть ADR-0025 о полном payload на каждой внутренней границе;
- все boundary-события сохраняются, но внутренние большие результаты
  переходят на summary;
- полный результат карты журналируется один раз на прикладной границе;
- для корреляции используются существующие `run_id` и `calculation_key`;
- движок не получает cache identity;
- модели карты, расчётного результата и артефакта не меняются;
- сохраняется ранее принятый локальный DEBUG/privacy режим; не расширяй эту
  задачу до privacy-hardening.

Обнови индекс ADR и только реально затронутые актуальные документы:

```text
README.md
docs/requirements/decisions/README.md
docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md
docs/requirements/component_responsibilities/exact-orb_build_natal_components.md
docs/requirements/handlers/exact_orb_build_natal_handler_requirements.md
docs/requirements/overview.md
docs/architecture/service_ready_architecture.md
docs/sequence_diagrams/chart_artifacts/*.puml
docs/sequence_diagrams/chart_artifacts/README.md
docs/sequence_diagrams/build_natal/*.puml
docs/sequence_diagrams/build_natal/README.md
```

Проверь `docs/architecture/exact_orb_architecture.puml` и
`docs/architecture/exact_orb_high_level_abstraction.puml`; меняй их только
если они показывают затронутый logging flow. Не перерисовывай диаграммы и не
меняй оформление без необходимости.

Исторические `docs/sequence_diagrams/build_charts/*.puml`, старые review-файлы
и существующие `prompts/**` не изменять.

## Что не делать

- не вводить новый идентификатор карты;
- не менять численные алгоритмы и golden-значения карты;
- не менять `NatalChart`, `CalculationResult`, `ChartArtifact` и
  `BuildNatalSuccess`;
- не менять codec и cache payload;
- не добавлять `run_id` в аргументы `calculate_natal()`;
- не передавать `calculation_key` в engine;
- не хранить карту или correlation-данные в глобальном mutable registry;
- не вводить сеть, очередь, отдельный сервис или новую внешнюю зависимость;
- не ослаблять модульные границы;
- не менять публичные коды ошибок;
- не добавлять обязательные отсутствующие quality gates;
- не запускать платные или сетевые smoke-тесты;
- не заниматься попутным рефакторингом или privacy-hardening;
- не менять исторические промты.

## Порядок проверок при выполнении промта

Запускай проверки поэтапно и указывай реальные результаты:

```text
python -m pytest -q tests/test_logging.py
python -m pytest -q tests/test_calculation_engine.py tests/test_calculation_engine_integration.py
python -m pytest -q tests/test_chart_artifact_codec.py tests/test_chart_artifact_resolver.py
python -m pytest -q tests/application/test_build_natal_logging.py tests/application/test_build_natal_integration.py
python -m pytest -q tests/test_calculation_block_integration.py tests/test_run_context.py
python -m pytest -q tests/test_module_boundaries.py
python -m pytest -q
git diff --check
```

Если имена тестов или размещение изменились, адаптируй только команды, а не
обязательный объём проверки. Не заявляй прохождение команды, которую не
запускал.

Если PlantUML уже доступен, отрендери изменённые диаграммы во временный
каталог вне рабочего дерева и визуально проверь их. Ничего не устанавливай
только ради рендера.

## Критерии готовности

- новые идентификаторы и поля моделей не добавлены;
- `run_id` связывает конкретное выполнение по существующим границам;
- полный `calculation_key` связывает артефакт, cache-события и downstream
  события, включая cache hit и single-flight;
- один successful handler call содержит одну полную DEBUG-копию карты;
- внутренние границы остаются видимыми через типизированные summary;
- summary строятся без полной сериализации карты;
- техническая cache-сериализация учитывается отдельно;
- модели, codec, cache payload и численные результаты не изменены;
- требования, новый ADR и актуальные диаграммы синхронизированы;
- все целевые, архитектурные и полные тесты проходят;
- несвязанные пользовательские изменения сохранены.

## Итоговый отчёт

Начни с результата. Затем кратко укажи:

1. корневую причину четырёх полных DEBUG-сериализаций;
2. новый контракт full/summary boundary-событий;
3. как используются `run_id` и `calculation_key` для поиска;
4. фактическое число полных сериализаций карты для DEBUG на cache miss и hit;
5. отдельно учтённую сериализацию для Calculation Cache;
6. подтверждение неизменности моделей и cache payload;
7. изменённые код, тесты, ADR, требования и диаграммы;
8. точные команды и реальные результаты проверок;
9. что не проверялось, оставшиеся ограничения и риски.
