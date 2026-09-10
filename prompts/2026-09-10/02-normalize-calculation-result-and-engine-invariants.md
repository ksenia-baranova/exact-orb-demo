# Промт 2 — нормализация `CalculationResult` и усиление границы `EngineService`

## Режим работы

Выполни изменение calculation-компонента.

На этом этапе:

- изменяй расчётную модель, адаптер и необходимые непосредственные потребители нового контракта;
- добавь и обнови тесты calculation-компонента;
- не изменяй документацию, ADR и диаграммы — для них будет отдельная задача;
- не реализуй пока новый режим полного DEBUG-логирования;
- не меняй схему `ChartArtifact`, алгоритм `calculation_key`, codec/cache-инварианты, `BuildNatalSuccess` и `StateDelta`, кроме минимальной адаптации к новому контракту `CalculationResult`;
- не редактируй существующие файлы `prompts/**`;
- не создавай compatibility aliases или дублирующие свойства для удалённых полей.

Перед изменениями зафиксируй:

```text
git status --short
git diff --name-only
```

Сохрани все существующие пользовательские изменения и untracked-файлы.

## Контекст

Предварительное исследование подтвердило, что `CalculationResult` хранит:

```text
chart_kind
chart
warnings
```

При этом:

```text
CalculationResult.chart_kind == CalculationResult.chart.chart_kind
CalculationResult.warnings == CalculationResult.chart.warnings
```

Эти значения передаются независимо и могут рассинхронизироваться.

`EngineService._validate_result()` проверяет только `chart_kind`, но не доказывает, что возвращённая адаптером карта относится к переданным `ResolvedBirthData` и `ChartSpec`.

Синтетический adapter смог вернуть карту с:

- правильным `chart_kind`;
- чужим `datetime_utc`;
- чужими координатами;

после чего `EngineService` принял результат, а `ChartArtifactResolver` сохранил его в кэш.

## Цель

Нормализовать calculation boundary так, чтобы:

1. `NatalChart` являлся единственным источником фактического `chart_kind` и calculation warnings;
2. `CalculationResult` не содержал независимых копий этих значений;
3. `EngineService` проверял, что карта соответствует фактическому запросу расчёта;
4. дефектный `TechniqueAdapter` не мог вернуть формально успешную карту для других времени, координат или спецификации;
5. существующее корректное поведение natal/cosmogram не изменилось.

## Обязательные источники

Перед реализацией изучи:

- `AGENTS.md`;
- `src/exact_orb/calculation/engine.py`;
- `src/exact_orb/calculation/spec.py`;
- `src/exact_orb/calculation/keys.py`;
- `src/exact_orb/calculation/types.py`;
- `src/exact_orb/calculation/artifacts.py`;
- `src/exact_orb/birth/types.py`;
- `src/exact_orb/engine/charts/natal.py`;
- модели блоков, входящих в `NatalChart`;
- `tests/test_calculation_engine.py`;
- `tests/test_chart_artifact_resolver.py`;
- `tests/test_chart_artifact_codec.py`;
- calculation/build-natal integration tests;
- архитектурные ограничения в `tests/test_module_boundaries.py`.

Старые файлы `prompts/**` не считай действующим контрактом.

## Требуемые изменения

### 1. Нормализовать `CalculationResult`

Сохрани тип `CalculationResult` как явный результат calculation port, но оставь в нём только:

```python
class CalculationResult(BaseModel):
    chart: NatalChart
```

Требования:

- модель остаётся frozen;
- передача удалённых полей `chart_kind` и `warnings` не должна молча игнорироваться;
- не добавляй свойства-алиасы `chart_kind` и `warnings`;
- канонические значения доступны только как:
  - `result.chart.chart_kind`;
  - `result.chart.warnings`.

Если фактический анализ всех потребителей докажет, что оболочка `CalculationResult` вообще не имеет самостоятельной ответственности, остановись и зафиксируй это как решение, требующее расширения задачи. Не удаляй весь тип молча: текущая задача предусматривает сохранение calculation port envelope.

### 2. Обновить `NatalTechniqueAdapter`

Adapter должен создавать:

```python
CalculationResult(chart=chart)
```

Он не должен отдельно извлекать и передавать `chart_kind` или `warnings`.

Не меняй:

- параметры вызова `calculate_natal`;
- значения по умолчанию;
- способ передачи `ChartSpec`;
- границу `swisseph`;
- обработку исключений;
- executor и locking.

### 3. Усилить `EngineService` result validation

После возврата адаптера и до публикации успешного результата проверь как минимум:

```text
chart.chart_kind соответствует spec.chart_kind
chart.datetime_utc соответствует resolved.utc_datetime
chart.latitude соответствует resolved.latitude
chart.longitude соответствует resolved.longitude
chart.house_system соответствует spec.house_system
```

Правила сравнения:

- используй существующие доменные нормализаторы там, где они уже определяют эквивалентность значений;
- не вводи approximate equality или новые допуски;
- не расширяй допустимый диапазон координат;
- не меняй в этой задаче формат или алгоритм `calculation_key`;
- не маскируй существенное различие нормализацией, которой нет в действующем calculation-контракте.

Также сопоставь `spec.include` с фактически присутствующими блоками `NatalChart`.

Проверяй только однозначно выводимые соответствия, закреплённые существующим контрактом `calculate_natal`, например:

- positions;
- houses/angles;
- rulers;
- interceptions;
- aspects;
- configurations;
- strength;
- ограничения cosmogram.

Не изобретай проверку параметра, если его фактическое значение нельзя доказать из `NatalChart`. Такой пробел перечисли в итоговом отчёте.

### 4. Типизированный отказ

Любое несоответствие результата запросу должно выходить через существующий calculation error contract:

```text
ChartCalculationError
error_code = ENGINE_UNEXPECTED
run_id сохранён
```

Требования:

- не выпускать наружу `ValueError`, `AssertionError` или `ValidationError`;
- не анализировать текст исключения;
- не включать персональные данные в INFO/WARNING terminal events;
- сохранить существующую классификацию остальных ошибок;
- не превращать дефект адаптера в ошибку пользовательского ввода.

### 5. Адаптировать непосредственных потребителей

Обнови потребителей удалённых полей:

- сборку `ChartArtifact`;
- calculation result summary;
- component logging projector;
- тестовые helpers и fake adapters.

Они должны читать:

```text
result.chart.chart_kind
result.chart.warnings
```

При этом на этом этапе не меняй публичную форму `ChartArtifact`: его верхнеуровневые дубликаты будут удалены отдельной задачей.

Не добавляй временные aliases в `CalculationResult`.

### 6. Сохранить текущую logging-семантику

На этом этапе разрешена только механическая адаптация summary projector к новой форме результата.

Сохрани:

- парные `component_message`;
- текущий `message_type`;
- текущий `payload_mode`;
- полный request;
- компактный успешный output `EngineService`;
- отсутствие полной карты в текущем internal summary;
- существующую обработку error/cancellation.

Явный режим полного DEBUG-логирования всех компонентных сообщений будет реализован отдельным промтом.

## Обязательные regression-тесты

Добавь минимальные недублирующиеся тесты.

### Контракт `CalculationResult`

Проверь:

- модель принимает `chart`;
- модель frozen;
- `chart_kind` и `warnings` отсутствуют в `model_fields`;
- передача удалённых полей отклоняется, а не игнорируется;
- сериализация содержит единственный экземпляр этих данных внутри `chart`.

### Корректный adapter

Проверь:

- adapter возвращает `CalculationResult(chart=...)`;
- все параметры `ChartSpec` по-прежнему передаются в `calculate_natal`;
- natal и cosmogram проходят позитивный контроль.

### Дефектный adapter

Отдельными параметризованными случаями проверь отклонение результата, если adapter возвращает:

- другой `chart_kind`;
- другое `datetime_utc`;
- другую latitude;
- другую longitude;
- другой `house_system`;
- несовместимую с `spec.include` структуру блоков;
- запрещённые блоки cosmogram.

Для каждого негативного случая нужен позитивный контроль, доказывающий, что adapter действительно был вызван и корректный результат проходит.

Проверяй:

```text
ChartCalculationError
code == ENGINE_UNEXPECTED
run_id сохранён
```

Не проверяй приватные поля, если это не требуется для lifecycle-инварианта.

### Потребители

Обнови существующие тесты `ChartArtifactResolver`, чтобы они создавали новый `CalculationResult` без удалённых полей.

Не ослабляй существующие проверки:

- cache hit/miss;
- single-flight;
- isolation deep copies;
- codec round trip;
- logging summary;
- error mapping.

## Явно вне области задачи

Не выполнять:

- удаление `ChartArtifact.chart_kind`;
- удаление `ChartArtifact.warnings`;
- изменение `ChartArtifact` JSON schema;
- изменение key namespace;
- изменение нормализации времени или координат в ключе;
- усиление cache-hit проверки;
- изменение `BuildNatalSuccess`;
- изменение `StateDelta`;
- глубокую заморозку всего графа `NatalChart`;
- нормализацию аспектов, конфигураций, strength или zodiac-представлений;
- новый logging configuration flag;
- изменение ADR, requirements или диаграмм;
- попутный рефакторинг.

Если корректное выполнение требует выйти за эти границы, сначала докажи необходимость и остановись с отчётом, не расширяя изменение самостоятельно.

## Порядок работы

1. Зафиксируй исходный status.
2. Найди все определения и потребителей `CalculationResult`.
3. Сопоставь существующие тесты с новым контрактом.
4. Добавь regression-тесты, воспроизводящие дефектный adapter.
5. Измени модель и adapter.
6. Усиль `EngineService` validation.
7. Адаптируй непосредственных потребителей.
8. Запусти целевые тесты.
9. Запусти связанные интеграционные и архитектурные тесты.
10. Запусти полный `pytest`.
11. Проверь `git diff --check` и итоговый status.

## Минимальные проверки

Запусти как минимум:

```text
python -m pytest -q -p no:cacheprovider tests/test_calculation_engine.py
python -m pytest -q -p no:cacheprovider tests/test_chart_artifact_resolver.py tests/test_chart_artifact_codec.py
python -m pytest -q -p no:cacheprovider tests/application/test_build_natal_handler.py tests/application/test_build_natal_integration.py
python -m pytest -q -p no:cacheprovider tests/test_calculation_block_integration.py tests/test_module_boundaries.py
python -m pytest -q -p no:cacheprovider
git diff --check
git status --short
```

Не заявляй прохождение проверки, если команда фактически не запускалась.

## Критерии завершения

Задача завершена, если:

- `CalculationResult` больше не хранит `chart_kind` и `warnings`;
- удалённые поля нельзя передать незаметно;
- все потребители используют канонические значения из `NatalChart`;
- `EngineService` отклоняет карту для других времени или координат;
- проверяются однозначно выводимые связи `ChartSpec → NatalChart`;
- ошибки остаются типизированными;
- logging-поведение изменено только механически;
- целевые, связанные и полные тесты проходят;
- документация и остальные компоненты не изменены;
- все не относящиеся к задаче пользовательские изменения сохранены.

## Итоговый отчёт

Начни с результата. Затем укажи:

- корневую причину;
- изменённый контракт `CalculationResult`;
- добавленные result-инварианты;
- список изменённых файлов;
- фактические команды и результаты тестов;
- что намеренно осталось для следующих промтов;
- обнаруженные конфликты или ограничения;
- итоговый `git status --short`.
