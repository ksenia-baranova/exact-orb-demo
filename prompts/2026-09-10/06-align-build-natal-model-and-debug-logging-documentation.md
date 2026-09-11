# Промт 6 — синхронизация документации после нормализации модели и полного DEBUG-логирования

## Контекст

Завершены компонентные изменения по устранению множественных источников истины в потоке `build_natal`.

Реализованные этапы:

1. Исследованы повторяющиеся данные и отсутствующие инварианты.
2. `CalculationResult` нормализован до одного канонического поля:

   ```python
   class CalculationResult(BaseModel):
       chart: NatalChart
   ```

3. `EngineService` проверяет соответствие результата разрешённым данным рождения, `ChartSpec`, виду карты, системе домов и составу вычислительных блоков.
4. `ChartArtifact` нормализован до структуры:

   ```python
   class ChartArtifact(BaseModel):
       calculation_key: str
       spec: ChartSpec
       calculation_version: str
       chart: ArtifactNatalChart
   ```

5. Из `ChartArtifact` удалены верхнеуровневые дубликаты `chart_kind` и `warnings`.
6. `ChartArtifact` проверяет соответствие карты спецификации, состав вычислительных блоков и соответствие `calculation_key` карте, спецификации и версии.
7. Cache hit проверяет, что декодированный артефакт относится к текущему нормализованному `CalculationInput`.
8. `BuildNatalSuccess` стал агрегатной границей, проверяющей согласованность полностью заполненного `StateDelta`, `BirthInput`, `ResolvedBirthData`, `ChartSpec`, карты, версии и ключа.
9. Все пять публичных компонентных границ записывают полные входящие и исходящие сообщения только при включённом `DEBUG`: `BuildNatalHandler.handle`, `BirthDataResolver.resolve`, `ChartArtifactResolver.ensure_chart`, `EngineService.calculate` и `calculate_natal`.
10. Удалены `NatalChartSummary`, `CalculationResultSummary`, `ChartArtifactSummary`, `payload_mode=summary` и параметр `result_payload_mode`.
11. `artifact_schema_version` намеренно не вводился.

Связанные коммиты для изучения фактических изменений:

```text
30eb1f3 fix(calculation): validate chart result identity
e975871 fix(calculation): validate chart artifact identity
645bb4e fix(application): validate build natal result identity
babeb09 feat(logging): log full component payloads in debug
```

Коммиты являются источником истории изменений, но окончательным источником фактического контракта остаётся текущий код и тесты.

## Цель

Синхронизировать действующую документацию с реализованной моделью и logging-политикой:

1. зафиксировать архитектурное решение о канонических источниках данных и сквозных инвариантах;
2. зафиксировать отказ от отдельного `artifact_schema_version`;
3. заменить решение ADR-0026 о внутренних summary;
4. восстановить полный DEBUG-payload на всех компонентных границах;
5. обновить актуальные requirements и component responsibilities;
6. обновить диаграммы потока, артефактов и классов;
7. закрыть запись о проблеме, обнаруженной человеком;
8. удалить устаревшие утверждения из действующей документации;
9. сохранить исторические документы как историю, а не переписывать их задним числом.

## Режим работы

В рамках этого этапа изменять только документацию.

Разрешено изменять `docs/requirements/decisions/**`, актуальные requirements, component responsibilities, актуальные scenarios и overview, архитектурные и sequence diagrams, их README и запись о проблеме в `docs/development_approach/problems_detected_by_human/**`.

Запрещено изменять production-код, тесты, fixtures, конфигурацию, схемы сериализации, зависимости, `pyproject.toml`, старые файлы в `prompts/**` и исторические requirement review-файлы.

Не создавать коммит без отдельной команды пользователя. Сохранить несвязанные пользовательские изменения и существующие untracked-файлы.

## Обязательное предварительное исследование

Перед редактированием перечитать:

- `AGENTS.md`;
- текущую реализацию `application/results.py`, `calculation/engine.py`, `calculation/types.py`, `calculation/chart_contract.py`, `calculation/keys.py`, `calculation/artifacts.py`, `calculation/codec.py`, `component_logging.py`, `birth/resolver.py`, `session/state.py`;
- связанные regression- и integration-тесты;
- ADR-0017, ADR-0025, ADR-0026 и индекс ADR;
- актуальные requirements и component responsibilities;
- диаграммы `build_natal`, chart artifacts и архитектурную диаграмму классов;
- `docs/development_approach/problems_detected_by_human/001-build-natal-model-multiple-sources-of-truth.md`.

ADR-0010 читать только как заменённое историческое решение. Не восстанавливать его требования и не менять его статус. Не считать файлы из `prompts/**` действующим контрактом.

## Новые ADR

Создать две отдельные записи. Перед созданием проверить, что номера `0027` и `0028` свободны.

### ADR-0027 — нормализованная модель результата расчёта и сквозная идентичность

Создать:

```text
docs/requirements/decisions/0027-normalized-chart-result-identity.md
```

с заголовком:

```text
ADR-0027. Нормализованный результат карты и сквозные инварианты идентичности
```

ADR должен зафиксировать отдельное архитектурное решение, дополняющее ADR-0017. Не объявлять ADR-0017 полностью заменённым: его решения о воспроизводимом кэше, `ChartSpec`, `CalculationInput`, `CalculationVersion` и opaque `bytes` сохраняются.

Описать обнаруженный дефект: дубликаты в `CalculationResult` и `ChartArtifact`, возможность объединить отдельно валидные `StateDelta` и `ChartArtifact` от разных расчётов и недостаточность исправления fixture.

Зафиксировать канонические источники:

| Значение | Канонический источник |
|---|---|
| рассчитанная карта | `CalculationResult.chart`, затем `ChartArtifact.chart` |
| фактический вид карты | `NatalChart.chart_kind` |
| запрошенный вид карты | `ChartSpec.chart_kind` |
| предупреждения расчёта | `NatalChart.warnings` |
| предупреждения разрешения | `ResolvedBirthData.warnings` |
| разрешённый расчётный вход | `calculation_input_from(ResolvedBirthData)` |
| вход карты | `calculation_input_from_chart(NatalChart)` |
| спецификация состояния | `StateDelta.base_chart_spec` |
| спецификация артефакта | `ChartArtifact.spec` |
| версия расчёта | `ChartArtifact.calculation_version` |
| идентичность артефакта | `ChartArtifact.calculation_key` |

Объяснить, что `delta.base_chart_spec` и `artifact.spec`, а также `delta.birth_resolved` и `artifact.chart` остаются в разных bounded context с разными потребителями, но связаны обязательными инвариантами.

Зафиксировать локальные инварианты `CalculationResult`, `EngineService` и `ChartArtifact`, а также сквозные проверки `BuildNatalSuccess`:

```text
artifact.spec == delta.base_chart_spec
```

```text
expected_chart_kind =
    "cosmogram" if delta.birth_resolved.time_unknown else "natal"
delta.base_chart_spec.chart_kind == expected_chart_kind
```

```text
(delta.birth_input.birth_time is None)
    == delta.birth_resolved.time_unknown
```

```text
calculation_input_from(delta.birth_resolved)
    == calculation_input_from_chart(artifact.chart)
```

```text
artifact.calculation_key == calculation_key(
    calculation_input_from(delta.birth_resolved),
    delta.base_chart_spec,
    artifact.calculation_version,
)
```

Указать, что нарушения дают Pydantic `ValidationError`, handler не преобразует их в `CalculationFailed`, ошибка логируется со `stage=build_result`, а `StateDelta` не получает зависимости от `ChartArtifact`.

Описать два уровня cache hit validation: локальную самосогласованность декодированного `ChartArtifact` и соответствие текущему ключу, spec, version и нормализованному `CalculationInput`.

Явно зафиксировать отказ от `artifact_schema_version`: отдельное поле не входит ни в `ChartArtifact`, ни в `calculation_key`; несовместимая cache-запись отклоняется и пересчитывается; численно значимые изменения покрываются `ChartSpec` или `CalculationVersion`; `SCHEMA_VERSION = "v1"` в ключе не является версией payload артефакта.

### ADR-0028 — полный payload всех компонентных границ в DEBUG

Создать:

```text
docs/requirements/decisions/0028-full-debug-component-boundary-payloads.md
```

с заголовком:

```text
ADR-0028. Полные сообщения всех компонентных границ только в DEBUG
```

ADR-0028 должен полностью заменить ADR-0026.

Зафиксировать, что summary сохранял факт прохождения границы, но скрывал значения карты и не позволял локализовать рассинхронизацию. При effective DEBUG все пять границ пишут полные входящие и исходящие сообщения:

| Граница | Полный успешный выход |
|---|---|
| `BuildNatalHandler.handle` | `BuildNatalSuccess` |
| `BirthDataResolver.resolve` | полный resolution outcome |
| `ChartArtifactResolver.ensure_chart` | публичный `ChartArtifact` |
| `EngineService.calculate` | `CalculationResult` |
| `calculate_natal` | `NatalChart` |

Успех использует `payload_mode=full`, ошибка — `payload_mode=error`; `payload_mode=summary` больше не действует.

Сохранить envelope `direction`, `operation`, `run_id`, `calculation_key`, `status`, `payload_mode`, `message_type`, `message`; корреляцию по `run_id` и `calculation_key`; `run_id=-` для `calculate_natal`; отсутствие ключа в Engine API; отсутствие отдельного UUID карты; компактность обычных технических событий.

Не вводить отдельный logging-флаг: режим определяется effective log level. Полный payload не сериализуется ниже DEBUG. `result_projector` допустим только для преобразования `_EnsuredChart` в полный публичный `ChartArtifact`.

Зафиксировать эксплуатационную границу: полный DEBUG-payload намеренно содержит дату, время, место, координаты, timezone-данные, предупреждения и результат расчёта локального стенда; до публичного развёртывания нужны отдельные решения о masking, routing, retention и доступе; ADR-0023 не изменяется.

## Статусы существующих ADR

ADR-0025: сохранить историю, но обновить статус — ADR-0026 временно частично заменял полные внутренние выходы, ADR-0028 восстановил полный payload и уточнил envelope.

ADR-0026: не удалять и не переписывать историческое содержание; пометить `Заменено ADR-0028`.

ADR-0017: не объявлять заменённым; при необходимости добавить ссылку на ADR-0027 без изменения решения о воспроизводимом кэше.

В `docs/requirements/decisions/README.md` добавить ADR-0027 и ADR-0028, обновить статусы 0025/0026 и удалить из актуального поясняющего текста утверждения о summary.

## Таблица повторяющихся данных

Добавить в ADR-0027 либо problem record итоговую таблицу:

| Значение | Места хранения | Классификация | Канонический источник | Итоговое решение |
|---|---|---|---|---|
| `chart_kind` | `ChartSpec.chart_kind`, `NatalChart.chart_kind`, `StateDelta.base_chart_spec.chart_kind` через spec | разные bounded context | запрос — `ChartSpec`; факт — `NatalChart` | верхнеуровневые дубликаты удалены |
| `warnings` | `ResolvedBirthData.warnings`, `NatalChart.warnings` | разные значения | соответствующая стадия | не объединять и не сравнивать |
| `ChartSpec` | `ChartArtifact.spec`, `StateDelta.base_chart_spec` | разные bounded context | оба представления | требовать точного равенства |
| UTC-время и координаты | `ResolvedBirthData`, `NatalChart` | разрешённый вход и аудит результата | сравнение через `CalculationInput` | сохранять оба и проверять после нормализации |
| `calculation_key` | `ChartArtifact`, cache key и logging envelope | identity плюс технические ссылки | `ChartArtifact.calculation_key` | пересчитывать чистой функцией |
| аспекты | `NatalChart.aspects`, cache payload | каноническое значение и техническая копия | `NatalChart.aspects` | не дублировать в wrapper-моделях |
| конфигурации | `NatalChart.configurations`, cache payload | каноническое значение и техническая копия | `NatalChart.configurations` | не дублировать |
| позиции | `NatalChart.bodies`, cache payload | каноническое значение и техническая копия | `NatalChart.bodies` | не дублировать |
| производные позиции | элементы `NatalChart.bodies` и derived-модели внутри карты | материализованное представление | `NatalChart` | сохранить как часть результата |
| `CalculationVersion` | resolver и `ChartArtifact.calculation_version` | runtime-конфигурация и аудит | соответствующий context | сохранять и проверять |
| сериализованный артефакт | модель и gzip JSON bytes | техническая копия | валидированная модель | cache остаётся opaque `bytes` |

Использовать классификации: 1 — необоснованный источник истины; 2 — производное материализованное представление; 3 — разные bounded context; 4 — техническая копия.

## Запись о проблеме

Обновить `docs/development_approach/problems_detected_by_human/001-build-natal-model-multiple-sources-of-truth.md`.

Сохранить историю обнаружения и некорректного fixture, изменить статус на решённый с датой завершения, добавить итог исследования, выполненные изменения, канонические источники, матрицу инвариантов, таблицу повторений, regression-покрытие и ссылки на ADR-0027/0028.

Исправить устаревшие утверждения: верхнеуровневых `warnings`/`chart_kind` в артефакте больше нет; ключ, cache hit и `BuildNatalSuccess` проверяются сквозным образом. Исторический результат `1427 passed` не переписывать; новый результат добавить отдельно.

## Актуальные requirements

Обновить только действующие документы.

### Calculation responsibilities

В `docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md` зафиксировать актуальную форму `CalculationResult`, отсутствие собственных `chart_kind`/`warnings`, ответственность `chart_contract.py`, проекцию `calculation_input_from_chart`, проверки EngineService, полный `CalculationResult` в DEBUG и отсутствие ключа в engine.

### Chart artifacts responsibilities

В `docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md` зафиксировать четырёхполевую форму `ChartArtifact`, отсутствие дубликатов, внутренние проверки, `ArtifactNatalChart`, cache hit validation, fail-open несовместимых payload, отсутствие `artifact_schema_version`, полный DEBUG-выход и opaque `bytes`.

### Build Natal responsibilities

В `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md` исправить model snippets и псевдокод на `CalculationResult(chart)`, `ChartArtifact(calculation_key, spec, calculation_version, chart)` и `BuildNatalSuccess(artifact, delta)`. Удалить `chart_kind=result.chart_kind` и `warnings=result.warnings`, описать локальные/сквозные инварианты и полный DEBUG всех пяти границ.

### Handler requirements

В `docs/requirements/handlers/exact_orb_build_natal_handler_requirements.md` исправить таблицы `ChartArtifact`, warnings, `BuildNatalSuccess`, порядок validator-проверок, критерии готовности, test mapping и logging contract. Чужой валидный артефакт должен отклоняться на `BuildNatalSuccess` и логироваться как `stage=build_result`.

### Overview и scenarios

Минимально обновить `docs/requirements/overview.md` и `docs/requirements/scenarios.md`: нормализованную модель, многоуровневую identity validation, полный DEBUG, positive build и cache hit.

## Архитектурная документация

Минимально обновить `docs/architecture/service_ready_architecture.md` и `docs/architecture/exact_orb_class_diagram.puml`.

Class diagram должна показывать `CalculationResult.chart`, четырёхполевый `ChartArtifact`, `BuildNatalSuccess.artifact/delta`, локальный инвариант артефакта и сквозной инвариант success. Удалить устаревшие поля и несуществующий `artifact_schema_version`.

## Sequence diagrams

Проверить все диаграммы в `docs/sequence_diagrams/build_natal/**` и `docs/sequence_diagrams/chart_artifacts/**`.

Обязательно обновить файлы с устаревшими моделями или summary:

```text
docs/sequence_diagrams/build_natal/README.md
docs/sequence_diagrams/build_natal/000-build_natal_end_to_end.puml
docs/sequence_diagrams/build_natal/001-build_natal_positive_cache_miss.puml
docs/sequence_diagrams/build_natal/002-build_natal_cache_hit.puml
docs/sequence_diagrams/build_natal/003-build_cosmogram_time_unknown.puml
docs/sequence_diagrams/chart_artifacts/README.md
docs/sequence_diagrams/chart_artifacts/001-ensure_chart_miss.puml
docs/sequence_diagrams/chart_artifacts/002-ensure_chart_hit.puml
docs/sequence_diagrams/chart_artifacts/004-single_flight_concurrent_miss.puml
```

Другие диаграммы изменять только при прямом противоречии.

Cache miss должен показывать `ResolvedBirthData → CalculationInput → calculation_key → EngineService → CalculationResult(chart) → ChartArtifact(key, spec, version, chart) → codec/cache → BuildNatalSuccess validation` и полные DEBUG-выходы.

Cache hit должен показывать декодирование bytes, локальную валидацию артефакта, проверку текущих key/spec/version/input, полный `ChartArtifact`, отсутствие engine, сквозную validation и полный handler output.

Cosmogram должен показывать `birth_time is None → time_unknown=True → chart_kind="cosmogram"` и проверку связи в `BuildNatalSuccess`.

Single-flight сохраняет семантику; каждый waiter логирует полный публичный артефакт со своим `run_id` и общим ключом.

## Исторические документы

Не редактировать `docs/requirements/build_chart/*review*.md` и старые `prompts/**`. ADR-0026 сохранить как заменённую историческую запись; слова `summary` внутри него допустимы.

## Терминология и поиск

В актуальном контракте не должны использоваться как действующие:

```text
NatalChartSummary
CalculationResultSummary
ChartArtifactSummary
payload_mode=summary
artifact_schema_version
artifact.chart_kind
artifact.warnings
result.chart_kind
result.warnings
```

Допустимые исключения: заменённый ADR-0026, исторические review, новый ADR/problem record при явном описании удалённого решения и промт.

Проверить согласованность структуры моделей, `CalculationInput`, ключа, cache hit validation, отсутствия artifact schema version, полного DEBUG и отсутствия component messages ниже DEBUG.

## Проверка диаграмм

Если в проекте уже есть локальная команда PlantUML, использовать её. Не добавлять зависимость или quality gate. Если runtime отсутствует, вручную проверить `@startuml`/`@enduml`, ссылки и participants и указать отсутствие рендера в отчёте.

## Тестирование

Запустить архитектурные тесты, полный `pytest`, `git diff --check` и `git status --short`. Не запускать сетевые и платные smoke-тесты.

## Порядок работы

1. Проверить ветку и status.
2. Убедиться, что четыре компонентных коммита присутствуют.
3. Составить список противоречий.
4. Создать ADR-0027 и ADR-0028.
5. Обновить статусы ADR-0025/0026 и индекс.
6. Обновить problem record.
7. Обновить calculation, artifact, build-natal и handler requirements.
8. Обновить overview/scenarios.
9. Обновить architecture и только затронутые sequence diagrams.
10. Найти устаревшие термины.
11. Проверить PlantUML.
12. Запустить архитектурные и полные тесты.
13. Выполнить `git diff --check` и итоговый status.
14. Не создавать коммит без отдельной команды.

## Критерии готовности

- ADR-0027 фиксирует нормализованную модель и сквозные инварианты.
- ADR-0028 заменяет ADR-0026.
- Статусы и индекс ADR синхронизированы.
- Актуальные requirements описывают `CalculationResult(chart)` и четырёхполевый `ChartArtifact`.
- `BuildNatalSuccess` документирован как агрегатная граница.
- Проверки времени, координат, spec, chart kind и ключа описаны точно.
- Cache hit validation отделена от локальной валидации артефакта.
- Отсутствие `artifact_schema_version` обосновано, `SCHEMA_VERSION` ключа с ним не смешан.
- Полный payload всех пяти границ разрешён только в DEBUG.
- Summary-типы отсутствуют в актуальной документации.
- ADR-0026 сохранён исторически.
- Диаграммы соответствуют коду.
- Problem record закрыт.
- Старые prompts/review не изменены.
- Код и тесты не изменены.
- Проверки проходят.

## Итоговый отчёт

Предоставить список ADR, канонические источники и матрицу инвариантов, обоснование отсутствия `artifact_schema_version`, контракт DEBUG, перечень requirements и диаграмм, статус problem record, изменённые файлы, команды и результаты проверок, статус PlantUML, непроверенное и подтверждение неизменности кода, тестов, cache/key formats и исторических файлов.
