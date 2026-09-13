# Нормализация орбиса на floating-point границе

Работай только в ветке `fix/aspect-orb-boundary-normalization`. Перед
изменениями убедись, что это текущая ветка; если нет — остановись.

Ветка `fix/aspect-orb-boundary-normalization` уже создана от актуальной
`main`, содержащей merge-коммит `81b0515` с предыдущими исправлениями
аспектной модели. Работай в ней; не создавай и не переключай ветку. Исходный
`ENGINE_VERSION` равен `"5"`.

Не создавай новую ветку, коммит, push или PR. Сохрани все пользовательские и
несвязанные изменения рабочего дерева.

`prompts/**` — исторический журнал. Не изменяй этот или другие сохранённые
промты.

## Исходное состояние и воспроизводимый дефект

Полный `pytest` после предыдущего PR дал:

```text
1577 passed, 1 failed
```

Падает property-тест
`test_property_orbs_are_nonnegative_and_within_max` на точном примере:

```text
longitudes = [7.0, 89.99999999999994]
```

Для этой пары:

```text
angular_distance = 82.99999999999994
aspect_type      = square
exact_angle      = 90.0
raw_orb          = 7.000000000000057
allowed_orb      = 7.0
ORB_EPSILON      = 1e-9
```

`_closest_allowed_aspect()` правильно считает запись допустимой по правилу
Т-АСП-4:

```text
raw_orb <= allowed_orb + ORB_EPSILON
```

Но затем возвращает наружу исходный `raw_orb`. В результате опубликованный
`Aspect.orb` больше эффективного лимита, хотя аспект принят именно как
лежащий на этом лимите. Одновременно нарушаются:

- инвариант `Aspect.orb <= resolve_orb(...)`;
- property-тест максимума контекста;
- честность сериализованного DTO;
- согласованность категорий, если эффективный лимит совпадает с границей
  `working=3°`.

Это не случайный flaky-тест и не повод увеличить допуск. Корневая причина —
разные значения для решения о допустимости и для опубликованного результата.

## Цель и принятое техническое решение

Сохранить существующую абсолютную tolerance-семантику Т-АСП-4, но
канонизировать орбис уже принятого кандидата:

```text
если raw_orb <= allowed_orb:
    published_orb = raw_orb
если allowed_orb < raw_orb <= allowed_orb + ORB_EPSILON:
    published_orb = allowed_orb
если raw_orb > allowed_orb + ORB_EPSILON:
    кандидат отклоняется
```

После изменения каждый опубликованный аспект обязан удовлетворять:

```text
0 <= Aspect.orb <= resolve_orb(
    Aspect.aspect_type,
    from_point,
    to_point,
    active_orbs,
)
```

Нормализация применяется только к микроскопическому превышению эффективного
orb-limit, уже принятому существующим `ORB_EPSILON`. Она:

- не расширяет множество допустимых аспектов;
- не уменьшает обычные орбисы внутри лимита;
- не округляет все значения до фиксированного числа знаков;
- не притягивает значения к границам категорий `1°` и `3°`;
- не меняет `ORB_EPSILON=1e-9`;
- не меняет правила выбора ближайшего типа аспекта.

Это небольшой самостоятельный bug fix. Одного промта и одного отдельного
коммита достаточно.

## Перед изменениями

1. Выполни:

   ```text
   git branch --show-current
   git status --short
   git log -5 --oneline
   ```

2. Убедись, что:

   - текущая ветка — `fix/aspect-orb-boundary-normalization`;
   - её база содержит merge-коммит `81b0515`;
   - `src/exact_orb/engine/__init__.py::ENGINE_VERSION == "5"`;
   - несвязанные modified/untracked-файлы зафиксированы и не будут включены в
     работу.

3. Зафиксируй baseline:

   ```text
   pytest tests/test_aspects.py::test_property_orbs_are_nonnegative_and_within_max -q
   pytest tests/test_aspects.py -q
   pytest tests/test_calculation_version.py tests/test_chart_artifact_codec.py -q
   ```

   Локальная Hypothesis database может воспроизвести найденный пример, а в
   чистом окружении 30 случайных примеров могут его не выбрать. Поэтому pass
   property-теста до исправления не опровергает дефект.

4. До production-правки добавь ближайший детерминированный regression-тест с
   точными долготами `7.0` и `89.99999999999994`. Убедись, что он падает по
   причине `Aspect.orb > allowed_orb`, а не потому, что finder не выполнялся.

5. Изучи действующие источники истины:

   - `AGENTS.md`;
   - Т-АСП-1…Т-АСП-7, Т-АСП-12 и Т-ДЕТ-3 в
     `docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md`;
   - раздел CalculationVersion в том же документе;
   - ADR-0017 только как действующее решение о `CalculationVersion`;
   - `src/exact_orb/engine/aspects/finder.py`;
   - `src/exact_orb/engine/aspects/orbs.py`;
   - `src/exact_orb/engine/aspects/categories.py`;
   - `src/exact_orb/engine/aspects/types.py`;
   - пути, использующие `find_aspects()` в natal, cosmogram, transit и
     station-aspects;
   - `src/exact_orb/calculation/version.py` и
     `src/exact_orb/engine/__init__.py`;
   - ближайшие tests, fixtures и artifact baseline.

6. Через `rg` найди все употребления:

   ```text
   ORB_EPSILON
   _closest_allowed_aspect
   resolve_orb
   categorize_orb
   find_aspects(
   Aspect.orb
   max_orb
   ENGINE_VERSION
   profiles_digest
   ```

Не исправляй тест ослаблением assertion до
`orb <= max_orb + ORB_EPSILON`: публичный DTO не должен сообщать значение,
которое больше лимита, послужившего основанием для его публикации.

## 1. Нормализация принятого кандидата

Исправь ответственный слой в `engine/aspects/finder.py`.

Для каждого типа аспекта отдельно вычисляются:

```text
raw_orb = abs(distance - exact_angle)
allowed_orb = resolve_orb(...)
```

Сохрани существующий порядок:

1. `allowed_orb <= 0` исключает кандидат;
2. `raw_orb > allowed_orb + ORB_EPSILON` исключает кандидат;
3. допустимый кандидат участвует в выборе ближайшего аспекта;
4. при равенстве действует прежний `ASPECT_PRIORITY`.

Выбор победителя выполняй по исходному геометрическому `raw_orb`, а не по
предварительно обрезанному значению. Только после выбора победившего
кандидата выведи:

```text
published_orb = min(raw_orb, allowed_orb)
```

Так решение «какой аспект ближе» остаётся геометрическим, а наружное значение
становится согласованным с эффективным лимитом.

Можно ввести небольшой приватный helper или расширить внутренний candidate
tuple. Не создавай публичный DTO, новый конфигурационный параметр или общий
модуль численной математики ради одной операции.

Не применяй `round()`, `Decimal`, относительный `math.isclose()` или
нормализацию всех орбисов. Действующий абсолютный epsilon уже является частью
контракта; требуется только согласовать его с возвращаемым значением.

## 2. Категория и downstream-пути

`categorize_orb()` должен получать `published_orb`.

Следствия:

- если effective `allowed_orb=3°`, значение
  `3° < raw_orb <= 3° + ORB_EPSILON` публикуется как ровно `3°` и получает
  `working` по действующему Т-АСП-7;
- если effective limit равен `7°`, граничный аспект публикуется как `7°` и
  остаётся `background`;
- если effective limit больше `3°`, значение немного выше `3°` не
  нормализуется к порогу категории и остаётся `background`;
- граница `exact` остаётся строгой: `orb < 1°`; не превращай значение около
  `1°` в `exact` общей epsilon-эвристикой.

Не добавляй special-case в:

- natal/cosmogram aggregation;
- configuration finder;
- transit или station finder;
- artifact codec;
- Research projection.

Все эти пути должны получить единое исправленное значение из универсального
`find_aspects()`. Конфигурации и устойчивые аспекты космограммы продолжают
использовать опубликованные канонические рёбра.

## 3. Версионирование

Исправление может изменить сериализованный `Aspect.orb`, его категорию на
эффективной границе `3°`, производные конфигурации и итоговый artifact для
пограничного входа. Поэтому используй существующий механизм
`CalculationVersion`:

```text
ENGINE_VERSION  "5" -> "6"
```

Не создавай новый ADR: исправление уточняет и исполняет уже действующий
Т-АСП-4, а не вводит новую предметную методику.

Не меняй:

- `AspectConfig`, `CategoryThresholds` и orb profiles;
- `profiles_digest`;
- calculation-key schema/prefix `v2`;
- `CALCULATION_VERSION_SCHEMA`;
- `ChartSpec`;
- artifact, state, dialog или Research schema versions;
- `feature_schema_version`;
- `ORB_EPSILON`.

Regression-тест CalculationVersion должен доказать:

- текущее значение `engine_version == "6"`;
- доизменённая запись с `engine_version == "5"` отличается только этим
  полем;
- `profiles_digest` не изменился;
- итоговый calculation-version fingerprint изменился.

Если normalized artifact baseline меняется только из-за нового
CalculationVersion, сначала проверь структуру и ожидаемые system/version
поля, затем обнови digest. Не подгоняй SHA вместо смысловых assertions.

## 4. Обязательные regression-тесты

Расширяй ближайшие тесты в `tests/test_aspects.py`; не создавай новый
параллельный файл.

Обязательное доказательство:

1. Точный найденный контрпример
   `[7.0, 89.99999999999994]` возвращает один квадрат с
   `orb == 7.0`, `orb <= resolve_orb(...)` и категорией `background`.
2. Ровно граничное значение без floating excess по-прежнему включается.
3. Значение внутри лимита и дальше epsilon от границы сохраняет исходный
   орбис без обрезания.
4. Значение в интервале
   `(allowed_orb, allowed_orb + ORB_EPSILON]` включается и публикуется как
   `allowed_orb`.
5. Значение строго выше `allowed_orb + ORB_EPSILON` исключается.
6. Нормализация доказана отдельно минимум для:

   - глобального `max_orb`;
   - лимита типа аспекта, например `semisextile=1°`;
   - обычного body limit, например `mars=3°`;
   - `aspect_body_overrides`, например квадрат к Плутону `3°`.

7. При effective limit `3°` нормализованный аспект имеет категорию
   `working`.
8. При общем лимите `7°` значение немного выше category boundary `3°` не
   притягивается к `3°` и имеет категорию `background`.
9. Существующий приоритет ближайшего аспекта и ориентация пары не меняются.
10. Property-инвариант усиливается: для каждого опубликованного аспекта
    проверяется не только общий `max_orb`, но и его фактический
    `resolve_orb()` с учётом типа и обоих endpoints.
11. Натальный reference output, не попадающий на epsilon-границу, не меняет
    состав аспектов, орбисы, категории, конфигурации и `applying=None`.
12. Universal finder остаётся name-agnostic и одинаково работает для natal и
    transit config.

Негативные тесты обязательно дополняй позитивным контролем, чтобы они не
проходили из-за того, что finder вернул пустой список для всех случаев.

Для значений вокруг epsilon используй детерминированные литералы или
вычисления, фактический порядок которых проверен в Python. Не используй
случайный Hypothesis example как единственное доказательство regression.

## 5. Актуальная документация

Обнови только
`docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md`:

- в Т-АСП-4 явно укажи, что tolerance применяется к решению о допустимости,
  а принятое микроскопическое превышение публикуется как effective
  `allowed_orb`;
- закрепи инвариант `Aspect.orb <= resolve_orb(...)`;
- в разделе CalculationVersion отрази `ENGINE_VERSION "5" -> "6"` и
  неизменность profiles/schema versions;
- при необходимости уточни строку покрытия Т-АСП-4 существующим
  `tests/test_aspects.py`.

Не создавай ADR, diagram или отдельный finding. Это локальное исправление
реализации уже принятого численного контракта. Не редактируй исторические ADR
и review-документы.

## Жёсткие ограничения

- Не увеличивай `ORB_EPSILON` и не вводи новый tolerance.
- Не ослабляй property-тест добавлением epsilon в публичный инвариант.
- Не удаляй tolerance полностью: точная floating-point граница должна
  оставаться включённой.
- Не округляй все орбисы и не меняй их обычную точность.
- Не выбирай тип аспекта по уже обрезанному значению.
- Не притягивай орбис к category thresholds `1°` или `3°`, если они не
  являются effective limit данного кандидата.
- Не меняй `categorize_orb()` и правила `<1°`, `<=3°`, `>3°`.
- Не меняй aspect angles, priority, sort order, orb profiles или body
  overrides.
- Не меняй состав аспектной сетки, ось узлов, конфигурационные паттерны или
  семантику неизвестного времени.
- Не меняй `applying=None`.
- Не исправляй `pars_fortune-asc`, angle-angle аспекты, интерцепционные
  проекции или `degree_flags`.
- Не создавай новый ADR: рост реестра ADR не оправдан локальным выполнением
  уже действующего инварианта.
- Не меняй key/state/Research schema versions и не вводи
  `artifact_schema_version`.
- Не добавляй dependencies, services, network calls или общий numerical
  framework.
- Не меняй полное DEBUG-логирование component boundaries.
- Не редактируй исторические `prompts/**`.
- Не выполняй попутный рефакторинг.
- Не запускай платные или сетевые smoke-тесты.
- Не создавай коммит, push или PR.

## Проверки

Запускай поэтапно и сообщай только фактические результаты.

### 1. Целевые

```text
pytest tests/test_aspects.py -q
pytest tests/test_calculation_version.py tests/test_chart_artifact_codec.py -q
```

### 2. Связанные aspect consumers

```text
pytest tests/test_configurations.py tests/test_transits.py -q
pytest tests/test_natal_include_gating.py tests/test_calculation_engine.py tests/test_calculation_engine_integration.py -q
pytest tests/test_calculation_block_integration.py tests/application/test_build_natal_integration.py -q
pytest tests/test_cli_render.py tests/research/test_projection.py tests/test_module_boundaries.py -q
```

### 3. Полный набор

```text
pytest -q
git diff --check
```

Полный `pytest` должен завершиться без прежнего failure. Не считай задачу
готовой только потому, что Hypothesis в новом запуске не сгенерировал
контрпример: детерминированный regression-тест обязателен.

### 4. Статические проверки

Через `rg` и diff проверь:

- `ORB_EPSILON` остался `1e-9` и используется только как абсолютный допуск
  включения;
- победитель по-прежнему выбирается по `raw_orb` и `ASPECT_PRIORITY`;
- наружу не может выйти `Aspect.orb > resolve_orb(...)`;
- `categorize_orb()` получает нормализованный опубликованный орбис;
- `ENGINE_VERSION == "6"`;
- `profiles_digest`, key schema, `CALCULATION_VERSION_SCHEMA`, state и
  Research versions не изменились;
- не появились новый ADR, diagram, dependency или special-case в consumer-
  слоях.

Просмотри полный `git diff` и `git status --short`. В diff должны быть только:

- `src/exact_orb/engine/aspects/finder.py`;
- `src/exact_orb/engine/__init__.py`;
- ближайшие aspect/version/artifact tests и только фактически изменившийся
  baseline;
- `exact-orb_calculation_requirements.md`.

Если понадобился другой production-файл, сначала докажи необходимость в
итоговом отчёте. Не включай несвязанные пользовательские файлы.

## Итоговый отчёт

Начни с результата, затем кратко укажи:

- корневую причину расхождения accepted и published orb;
- точный исходный контрпример и его результат после исправления;
- формулу нормализации и сохранённую границу `ORB_EPSILON`;
- почему выбор ближайшего аспекта остаётся по `raw_orb`;
- поведение ровно на границе, внутри epsilon и сразу за epsilon;
- проверки global, aspect, body и override limits;
- влияние нормализации на category boundary `3°` и отсутствие общего
  притягивания к `1°/3°`;
- подтверждение неизменности обычных reference-аспектов, конфигураций и
  `applying=None`;
- изменение `ENGINE_VERSION` и неизменность profiles/schema versions;
- почему новый ADR не создан;
- фактически изменённые production-файлы, тесты, baseline и requirement;
- точные команды и реальные результаты целевых, связанных и полного pytest;
- результат `git diff --check` и статических проверок;
- что не проверялось;
- подтверждение, что `pars_fortune-asc`, angle-angle аспекты, интерцепционные
  проекции и `degree_flags` остались вне этой работы.
