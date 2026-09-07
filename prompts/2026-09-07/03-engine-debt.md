# Engine debt: имя транзитной техники, окно поиска, `BodyPosition.chart`

Задача: закрыть три долга движка. Числовое поведение не меняется, но публичный
Python-контракт намеренно меняется в трёх местах: имя транзитной функции,
формы аргументов её окна и обязательность `BodyPosition.chart`.

Работай в ветке:

`refactor/engine-debt`

Предусловие: база ветки содержит результат A2 — `calculation/version.py`,
`DEFAULT_EPHEMERIS_FLAGS` и fail-fast на неоднозначном биндинге. На момент
подготовки задачи это HEAD `feat/calculation-version` (`55f0f03`). Если ветки
`refactor/engine-debt` ещё нет, создай её от этого HEAD; не начинай A3 от
`main`, пока A2 туда не влит. Если A2 в базе отсутствует, остановись и сообщи
об этом вместо частичной реализации.

Не создавай коммит, push или PR. Сохрани пользовательские и несвязанные
изменения рабочего дерева.

Основание: ADR-0001 (раздел «Последствия»), `overview.md` §4.10 и §9,
`roadmap.md` блок A строка A3, Т-ТРН-2, Т-ТРН-14.

Не реализовывать: конкретный член `DerivedSpec` для транзита (включая возможный
`TransitChartSpec`), `TransitTechniqueAdapter`, `ensure_derived`, сам
`DerivedSpec`, регистрацию транзита в `SUPPORTED_TECHNIQUES`, изменение
`CalculationResult`, `ChartArtifact`, `ChartKind` и кодека.

**Главный критерий приёмки: числа и сериализуемые значения не меняются.**
Золотой файл
`tests/golden/natal_1985_human.txt` обязан остаться байт-в-байт, сериализация
артефакта для зафиксированной натальной карты — прежней. Это рефакторинг имён
и типов, а не расчётной математики. Ломающие изменения Python API перечислены
выше и являются сознательно принятой частью ADR-0001; compatibility aliases
не добавлять.

## 1. Три долга

1. `calculate_transits` названа во множественном числе, возвращая одну
   `TransitChart`, а окно поиска передаётся голым `int` в месяцах и
   перегружает параметр `moment`.
2. `BodyPosition.chart: Literal["natal"]` — примитивный эфемеридный слой
   называет технику. ADR-0001: «Примитив не должен называть технику;
   подлежит правке».
3. `transit.py` берёт дефолт флагов напрямую из `swe`, хотя A2 ввела
   `DEFAULT_EPHEMERIS_FLAGS`.

Плюс задача синхронизирует с ADR-0016 и `chart_artifacts.md` уже известный,
намеренно отложенный пробел расчётной границы как Т-ГРН-9 (§5) и правит
документы, которые она делает ложными (§6). Т-ГРН-9 эта ветка не закрывает.

## 2. `calculate_transit` и `exact_window`

### 2.1. Что не так сейчас

```python
def calculate_transits(
    natal: NatalChart,
    moment: datetime | tuple[datetime, datetime] | TransitDateRange,
    ...
    exact_window_months: int = DEFAULT_EXACT_WINDOW_MONTHS,
) -> TransitChart
```

`moment` несёт три формы и одновременно задаёт диапазон поиска; ширина окна
живёт отдельным `int`. При диапазоне позиции считаются на его начало, и это
правило нигде не выражено — оно спрятано в `_normalize_moment`.

ADR-0001 формулирует цель: «Техника производит карту **на момент**; окно —
параметр поиска точных дат и станций. Поэтому `calculate_transits` →
`calculate_transit`, диапазон переезжает в именованный `exact_window`».

### 2.2. Целевая сигнатура

```python
def calculate_transit(
    natal: NatalChart,
    moment: datetime,
    location: TransitLocation | Mapping | Sequence | None = None,
    *,
    exact_window: ExactWindow = DEFAULT_EXACT_WINDOW,
    body_ids: Mapping[str, int] | None = None,
    ephemeris_flags: int = DEFAULT_EPHEMERIS_FLAGS,
    max_orb: float = DEFAULT_ASPECT_ORB,
    station_body_ids: Mapping[str, int] | None = None,
    station_aspect_orb: float = DEFAULT_STATION_ASPECT_ORB,
    ephemeris_path: str | None = None,
) -> TransitChart
```

`moment` становится **только** `datetime`. Кортеж и `TransitDateRange` в этом
параметре больше не принимаются: диапазон — это окно, а не момент.

Аннотация Python не обеспечивает runtime-валидацию. Поэтому публичная обёртка
до входа в `ephemeris_session()` обязана явно проверить:

```text
moment не datetime
    -> TypeError("moment must be a datetime")
exact_window не RelativeExactWindow и не TransitDateRange
    -> TypeError("exact_window must be a RelativeExactWindow or TransitDateRange")
```

`@validate_call` ради этого не добавлять: две явные проверки сохраняют
предсказуемый контракт исключений и не вводят неявное coercion-поведение на
остальных аргументах.

### 2.3. `ExactWindow`

ADR-0001 оставил форму на выбор при миграции. Выбирается вариант «отдельный
член union»:

```python
class RelativeExactWindow(BaseModel):
    """Симметричное окно вокруг момента."""
    model_config = ConfigDict(frozen=True)
    months: int = Field(ge=0)

ExactWindow = RelativeExactWindow | TransitDateRange

DEFAULT_EXACT_WINDOW = RelativeExactWindow(months=DEFAULT_EXACT_WINDOW_MONTHS)
```

`TransitDateRange` уже существует и переиспользуется как абсолютный вариант.
Новую модель для него не заводить. Оба члена union являются value objects:
добавить `model_config = ConfigDict(frozen=True)` также в `TransitDateRange`,
чтобы у вариантов не расходился контракт изменяемости. Валидатор порядка
границ при этом не добавлять.

Семантика сохраняется ровно как в Т-ТРН-2 и Т-ТРН-14:

```text
RelativeExactWindow(months=N)  -> окно [moment - N мес., moment + N мес.]
RelativeExactWindow(months=0)  -> точечное окно [moment, moment]
TransitDateRange(start, end)   -> окно [start, end], требует end > start
```

Точечное окно выражается **только** относительным вариантом; `TransitDateRange`
сохраняет требование `end > start`, как и сегодня. Это и есть «отдельный
вариант» из ADR-0001.

Обе границы включительны, как и сейчас. Отрицательный `months` отвергается
валидатором `RelativeExactWindow`, а не проверкой внутри нормализатора.
`TransitDateRange` переиспользуется без изменения своей схемы: порядок границ,
как и сегодня, проверяется при нормализации окна, а не при отдельном создании
модели.

Абсолютное окно — независимый параметр поиска и не обязано содержать `moment`.
Это явное следствие разделения двух понятий: позиции всегда считаются на
`moment`, а точные даты и станции ищутся только внутри `[start, end]`.
Дополнительную проверку `start <= moment <= end` не добавлять. Эквивалентная
миграция прежнего диапазона всё равно использует `moment=start`. Независимость
момента и абсолютного окна зафиксировать в ревизии ADR-0001 и Т-ТРН-2.

### 2.4. Позиции считаются на `moment`

Сегодня при диапазоне позиции считаются на `start`, и это неявно. После правки
позиции считаются на `moment` всегда. Прежний вызов

```python
calculate_transits(natal, (start, end))
```

мигрирует в

```python
calculate_transit(natal, start, exact_window=TransitDateRange(start=start, end=end))
```

то есть прежнее правило становится видимым в точке вызова. Числа при
эквивалентной миграции обязаны совпасть с baseline, снятым **до правки кода**
(§9).

### 2.5. Объём миграции

Замер по текущему дереву: `calculate_transits` встречается 19 раз в
`tests/test_transits.py`, 4 раза в `tests/test_ephemeris_runtime_config.py`
(импорт, имя теста и два вызова) и 3 раза в `transit.py`;
`exact_window_months` — 12 раз в `tests/test_transits.py` и 10 раз в модуле.
`tests/test_transit_root_search.py` публичную функцию не вызывает. Вне
`engine/charts/transit.py` в `src/` вызовов нет.

Изменение `BodyPosition.chart`, `calculate_bodies` и протокола Selena также
требует согласованной миграции существующих прямых вызовов в:

```text
tests/test_selena.py
tests/test_calculation_engine.py
tests/research/test_projection.py
```

Это часть задачи, а не попутный рефакторинг. `tests/test_ephemeris_runtime_config.py`
тоже входит в обязательный объём переименования транзитной функции.

**ADR-0001 в разделе «Последствия» утверждает, что правка затрагивает `cli.py`
и `tools/`. Это неверно на текущем дереве** — там вызовов нет. Строку
поправить (§6).

Приватную `_calculate_transits` переименовать согласованно. `_normalize_moment`
заменить функцией, имя которой отражает нормализацию `moment` вместе с
`exact_window`, например `_normalize_exact_window`; старые tuple/range-ветки
из `moment` удалить.

Алиаса `calculate_transits` для совместимости не оставлять. Отсутствие
внутрирепозиторных production-вызовов не доказывает отсутствие внешних
потребителей; ломающий rename допустим потому, что он прямо принят ADR-0001
на текущем дорелизном этапе. README обновляется как публичный пример миграции.

## 3. `BodyPosition.chart`

### 3.1. Что делать

```python
chart: Literal["natal"] = "natal"   →   chart: str = Field(..., min_length=1)
```

Поле становится обязательным и передаётся техникой. Примитив перестаёт знать
имя техники, но продолжает нести метку, которую ему дали.

Метку надо протащить параметром до мест конструирования. Конструируется
`BodyPosition` в четырёх местах:

```text
engine/ephemeris/calc.py:102      внутри calculate_bodies
engine/ephemeris/selena.py:106    внутри _calculate_perigee_selena
engine/charts/natal.py:695        south_node
engine/charts/natal.py:759        производная точка
```

`calculate_bodies` и стратегии Селены получают keyword-only параметр
`chart: str`. Протокол `SelenaMethod.calculate` меняется согласованно с обеими
реализациями. Значение во всех случаях приходит из `calculate_natal` и равно
`"natal"`. Это метка **техники**, а не `chart_kind`: даже при
`chart_kind="cosmogram"` значение обязано остаться `"natal"`, иначе изменится
существующая сериализация.

Докстроку `engine/ephemeris/points.py` — «Derived deterministic points for
natal charts» — привести к формулировке без имени техники.

### 3.2. Почему не удалять поле

Проверено: **`BodyPosition.chart` сегодня не читает никто.** Дискриминатором
карт служат `PositionedPoint.chart` и `AspectPointRef.chart`, они уже объявлены
как `str`, и `configurations/patterns/common.py` уже схлопывает набор в
`"mixed"` по Т-КНФ-9.

Удаление поля выглядит чище, но меняет сериализацию `ChartArtifact`, а эта
ветка обязана оставить payload неизменным. Поэтому вариант «удалить» здесь
отвергается и остаётся отдельным решением на момент, когда появится синастрия
и станет видно, нужна ли метка в примитиве вообще. Записать это одной фразой
в ревизии ADR-0001.

`model_dump(mode="json")` после правки обязан давать то же значение, а
`model_dump_json()` и JSON payload `ChartArtifact` — те же байты для
зафиксированной входной карты. Значение остаётся `"natal"`, меняется только
схема и обязательность поля. Проверка описана в §9.

## 4. `DEFAULT_EPHEMERIS_FLAGS`

`engine/charts/transit.py` использует `ephemeris_flags: int =
swiss_backend.swe.FLG_SWIEPH`. A2 ввела `DEFAULT_EPHEMERIS_FLAGS` в
`engine/ephemeris/types.py`, и `natal.py` уже на неё перешёл. Перевести
`transit.py` на ту же константу: у одного дефолта не должно быть двух
написаний.

Это инвариант кодовой базы, а не инвариант calculation fingerprint: транзитной
техники в реестре пока нет, поэтому её дефолт не участвует в компоненте 9
`CALCULATION_VERSION`. Существующий тест натального дефолта в
`tests/test_calculation_version.py` оставить без изменений и без импорта
транзитного модуля. Отдельный тест в `tests/test_transits.py` через инспекцию
сигнатуры обязан подтвердить, что дефолт `calculate_transit.ephemeris_flags`
равен `DEFAULT_EPHEMERIS_FLAGS`.

## 5. Известный отложенный пробел Т-ГРН-9

Добавить в `exact-orb_calculation_requirements.md` §8 после Т-ГРН-8. Нумерацию
Т-ГРН-1…Т-ГРН-8 не менять.

Пометить пункт **«Пробел / намеренно отложено»** и сослаться на ADR-0016 и §4
`exact-orb_chart_artifacts.md`. Это не новое архитектурное решение и не долг,
обнаруженный впервые в A3: целевой `ensure_derived` уже описан, но текущая
натально-специфичная расчётная граница не перечислена в calculation
requirements одним проверяемым пунктом.

Смысл: переименование объявляет шаблон «одна функция на технику», но текущая
расчётная граница этот шаблон пока не держит. Т-ГРН-9 фиксирует ограничение
явно и не создаёт впечатления, что один rename подключил транзит к приложению.

Пункт обязан перечислить проверяемые места:

```text
CalculationResult.chart      объявлен как NatalChart
ChartArtifact.chart          объявлен как ArtifactNatalChart
ArtifactNatalChart           натально-специфичен: подменяет EphemerisStatus
                             на ArtifactEphemerisStatus
ChartKind                    Literal["natal", "cosmogram"], транзита нет
_validate_identity           сравнивает chart.chart_kind, которого
                             у TransitChart нет
decode_chart_artifact        декодирует в один тип, дискриминатора нет
SUPPORTED_TECHNIQUES         frozenset({"natal"})
```

Следствие сформулировать так: техника, отличная от натальной, через
`EngineService` и `ChartArtifactResolver` не проходит, сколько бы ни было
переименовано в `engine/charts`.

Требование: форма результата, спеки и артефакта производной техники выбирается
**вместе** с реализацией `ensure_derived`, а не отдельно, потому что ключ
композита выводится из ключей баз (§4 `chart_artifacts.md`), а сужение сессии
до одной базовой карты снимается тем же решением (ADR-0016).

Условие закрытия: появление `DerivedSpec`, конкретного члена этой спеки для
транзита и отдельного решения, является ли `transit` значением `chart_kind`
или только `technique`. Имя `TransitChartSpec` этой задачей не фиксировать:
если оно потребуется, оно принимается вместе с производным контрактом.

В §10 «Что покрыто тестами» добавить Т-ГРН-9 в строку непокрытых рядом с
Т-ТРН-13 и Т-ЭФ-24.

## 6. Документы, которые эта ветка делает ложными

Правится только то, что становится неверным из-за этой работы. Накопленная
синхронизация после A2 (контракт §4.1 `build_natal_components.md`, статусы
README, оценки roadmap) в область **не входит** и перечисляется в отчёте.

| Файл | Что |
|---|---|
| `docs/requirements/decisions/0001-split-natal-ephemeris-charts.md` | ревизия: правка имени и сигнатуры окна выполнена, форма `ExactWindow` выбрана; зафиксировать независимость `moment` от абсолютного окна; «известное нарушение слоя» закрыто; убрать неверное упоминание `cli.py` и `tools/` в «Последствиях»; одной фразой зафиксировать, что удаление `BodyPosition.chart` осталось отдельным решением |
| `docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md` | Т-ГРН-9 как известный отложенный пробел со ссылками на ADR-0016 и `chart_artifacts.md`; Т-ТРН-2 — новый контракт `moment`/`exact_window`, `RelativeExactWindow(months=0)`, проверка границ и независимость `moment` от абсолютного окна; §10 |
| `docs/requirements/overview.md` §4.10 | снять «требует переименования» и «Статус: реализовано, требует правки имени»; снять «Известное нарушение: `BodyPosition.chart`…» |
| `docs/requirements/overview.md` §9 | из «Отдельными задачами» убрать переименование `calculate_transits` и правку `BodyPosition.chart`; маскирование логов и бенчмарк оставить |
| `docs/requirements/roadmap.md` | строка A3 в таблице блока A — отметить выполненной по принятому в документе способу |
| `README.md` | четыре упоминания: строка про `calculate_transits()` принимающую `NatalChart`, строка таблицы `engine/charts/`, импорт и вызов в примере быстрого старта |
| `docs/architecture/exact_orb_class_diagram.puml` | `BodyPosition.chart: str`; keyword-only `chart` в Selena API; `RelativeExactWindow`/`ExactWindow`; связь `calculate_transit()` вместо `calculate_transits()` |

README правится только в этих четырёх местах: пример обязан оставаться
запускаемым. Остальная его неактуальность — отдельная задача.

## 7. Дистрибутив `swisseph` — проверка, не правка

Строка A3 в roadmap упоминает «один дистрибутив `swisseph`, зафиксированный в
`pyproject.toml`». Пункт уже закрыт: объявлено `pysweph>=2.10.3.4`, а A2
добавила fail-fast на неоднозначности биндинга.

`pyproject.toml` **не менять**. В отчёте зафиксировать факт и назвать
единственный оставшийся открытый вопрос: отсутствие верхней границы допускает
будущий `2.11` со сменой API `houses_ex`/`calc_ut` (§8.6
`chart_artifacts.md`). Решение о границе принимает человек отдельно.

## 8. Запреты

- не менять математику: никаких правок в поиске корней, станций, орбисов,
  выборе шага сканирования;
- не менять `CalculationResult`, `ChartArtifact`, `ArtifactNatalChart`,
  `ChartKind`, `decode_chart_artifact`, `SUPPORTED_TECHNIQUES`;
- не добавлять транзит в спеку, реестр техник или адаптеры;
- не удалять `BodyPosition.chart`;
- не оставлять алиас `calculate_transits`;
- не добавлять `@validate_call`; runtime-проверки двух изменённых аргументов
  выполнить явно по §2.2;
- не добавлять model-validator в `TransitDateRange`: проверка `end > start`
  остаётся в нормализации окна;
- не менять `pyproject.toml`;
- не трогать `calculation/version.py` и результаты A2, включая
  `tests/test_calculation_version.py`; этот файл только запускается как
  положительный контроль, но A3 его не редактирует;
- не исправлять Т-СИЛ-9 (русские имена фаз Луны), Т-НАТ-11 (таблица
  управителей) и Т-ЭФ-24 (Селена в fallback): блок A их исключает;
- не выполнять попутную синхронизацию документов вне §6.

## 9. Тесты

### 9.1. Baseline до изменения кода

До первого изменения `transit.py`, `BodyPosition` или мест его конструирования
снять два воспроизводимых baseline с текущей реализации A2. Значения baseline
зафиксировать в тестовых константах с комментарием:

```text
baseline: 55f0f03 + вендоренные ephe/*.se1; пересчитывается только при
осознанном обновлении эфемерид или сериализуемой схемы в отдельной задаче,
но не под новый результат этого рефакторинга
```

Оба SHA-256 зависят от содержимого repo `ephe/*.se1`. Их падение после
осознанного обновления эфемерид ожидаемо и не означает дефект A3; без такого
обновления ожидаемые значения не менять.

1. **Явный диапазон транзита.** На данных `tests/fixtures/natal_1985.py`
   вызвать старый `calculate_transits(natal, TransitDateRange(start, end), ...)`
   с фиксированными небольшими `body_ids`, `station_body_ids`, `max_orb` и
   диапазоном. Из `model_dump(mode="json")` убрать только runtime provenance
   `ephemeris.path` и `ephemeris.source`, канонизировать через
   `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
   и зафиксировать SHA-256 константой в `tests/test_transits.py`.
2. **Натальный artifact JSON payload.** Построить реальный reference
   `NatalChart`, обернуть его в `ChartArtifact` с фиксированными spec,
   `calculation_key` и `calculation_version`, затем зафиксировать SHA-256 от
   `artifact.model_dump_json().encode("utf-8")`. Нормализация в
   `ArtifactNatalChart` удаляет `ephemeris.path/source`, поэтому baseline не
   зависит от пути checkout. Константа и regression-тест принадлежат
   `tests/test_chart_artifact_codec.py`; его модульный маркер запрещает только
   autoinit, поэтому reference-расчёт должен явно вызвать `configure_ephemeris`
   для repo `ephe/`. Codec не менять; существующий тест его детерминированных
   gzip-байтов остаётся положительным контролем.

Если baseline не был снят до изменения кода, восстановить его запуском
исходного `55f0f03`, а не вычислять ожидаемое значение новой реализацией.

### 9.2. Миграция и новые контракты

`tests/test_transits.py` и `tests/test_ephemeris_runtime_config.py` мигрируются
целиком на новое имя. Прямые вызовы изменённых ephemeris/Selena API и прямое
конструирование `BodyPosition` мигрируются в файлах из §2.5. Дополнительно:

**Эквивалентность миграции.** Прежняя пара «диапазон как `moment`» и новая
пара «`moment=start` плюс `TransitDateRange`» дают одинаковую каноническую
проекцию полного `TransitChart`: новый результат обязан совпасть с SHA-256,
снятым в §9.1. Это ключевой regression-тест ветки; сравнение двух вызовов уже
новой функции не считается доказательством эквивалентности старому API.

**Окно.**

- `RelativeExactWindow(months=0)` даёт точечное окно `[moment, moment]`;
- `RelativeExactWindow(months=N)` даёт `[moment - N, moment + N]`;
- обе модели `ExactWindow` frozen;
- отрицательный `months` отвергается валидатором модели;
- `TransitDateRange` с `end <= start` отвергается нормализатором/публичным
  вызовом, а не конструктором модели;
- абсолютное окно до или после `moment` допускается: позиции остаются на
  `moment`, а `window_start_utc`/`window_end_utc` совпадают с переданным окном;
- кортеж или `TransitDateRange`, переданные в `moment`, дают ровно оговорённый
  `TypeError` до захвата `ephemeris_session()`;
- посторонний тип в `exact_window` даёт оговорённый `TypeError` до захвата
  `ephemeris_session()`.

**`BodyPosition.chart`.**

- поле обязательно: конструирование без него — `ValidationError`;
- `calculate_natal` проставляет `"natal"` всем телам, включая `south_node`,
  Селену и прочие производные точки;
- космограмма также сохраняет `BodyPosition.chart == "natal"`, потому что это
  метка техники, а не `chart_kind`;
- SHA-256 JSON payload реального натального `ChartArtifact` совпадает с
  baseline §9.1; существующие codec-тесты подтверждают детерминированность
  кодирования тех же JSON-данных в bytes.

**Дефолт флагов.** Новый тест в `tests/test_transits.py` подтверждает дефолт
`calculate_transit`; неизменённый существующий тест
`tests/test_calculation_version.py` продолжает подтверждать натальный дефолт.
Вместе они фиксируют использование одного `DEFAULT_EPHEMERIS_FLAGS`, не
смешивая транзитный API с контрактом calculation fingerprint.

**Золотой файл.** `test_cli_render.py` против
`tests/golden/natal_1985_human.txt` — без изменений в самом файле.

## 10. Проверки

1. `pytest tests/test_transits.py tests/test_transit_root_search.py tests/test_ephemeris_runtime_config.py -q`
2. `pytest tests/test_ephemeris.py tests/test_selena.py tests/test_calculation_engine.py tests/research/test_projection.py tests/test_chart_artifact_codec.py tests/test_cli_render.py tests/test_calculation_version.py tests/test_module_boundaries.py -q`
3. `pytest -q`
4. `rg -n "calculate_transits" src tests docs README.md` —
   остаться должны только исторические упоминания в ADR-0001, явно
   обозначенные как прошлое имя
5. `rg -n "exact_window_months" src tests docs README.md` — результатов нет
6. `rg -n -F 'chart: Literal["natal"]' src/exact_orb/engine/ephemeris/types.py` —
   результатов нет; проверка намеренно ограничена примитивом `BodyPosition`.
   Более широкий поиск по `engine/` найдёт chart-level
   `NatalPointRef.chart: Literal["natal"]`; это техническая ссылка аспекта,
   а не долг примитивного слоя
7. `git diff --exit-code -- tests/golden/natal_1985_human.txt` — файл не менялся
8. `git diff --check`
9. `git status --short` и полный diff всех файлов задачи; несвязанные изменения
   явно отделить в отчёте

Сетевые и платные smoke-тесты не запускать.

## 11. Приёмка

- `calculate_transit` с `moment: datetime` и `exact_window`;
- `RelativeExactWindow` добавлен, `TransitDateRange` переиспользован,
  `ExactWindow` объявлен union;
- точечное окно выражается `months=0`, `TransitDateRange` сохраняет
  `end > start`, а абсолютное окно не обязано содержать `moment`;
- неверные runtime-типы `moment` и `exact_window` отвергаются явно до захвата
  эфемеридной сессии;
- новый вызов с явным диапазоном совпадает с baseline старого вызова;
- `BodyPosition.chart` — обязательный `str`, метка приходит от техники,
  натальный artifact JSON payload совпадает с baseline;
- докстрока `points.py` без имени техники;
- `transit.py` использует `DEFAULT_EPHEMERIS_FLAGS`;
- обе chart-level функции имеют этот дефолт в сигнатуре;
- Т-ГРН-9 добавлен как известный отложенный пробел, нумерация Т-ГРН-1…8 не
  тронута и имя будущей transit-спеки не предрешено;
- документы §6 и диаграмма классов поправлены, пример в README использует
  новое имя;
- `pyproject.toml` не изменён;
- золотой файл байт-в-байт прежний;
- полный `pytest` зелёный.

В итоговом отчёте:

- выбранная форма `ExactWindow` и почему точечное окно только относительное;
- выбранный runtime-контракт типов и независимость `moment` от абсолютного
  окна;
- сохранённое старое сообщение `birth_datetime must be timezone-aware` для
  naive-границ окна: оно приходит из общего `to_utc` и остаётся вне области;
- подтверждение эквивалентности миграции по заранее снятому baseline;
- подтверждение неизменности натального artifact JSON payload;
- явное указание, что оба baseline привязаны к `55f0f03` и текущему содержимому
  вендоренных `ephe/*.se1`;
- точные команды и реальные результаты проверок 1–9;
- состояние пункта про дистрибутив и открытый вопрос верхней границы;
- перечень накопленной документационной рассинхронизации, оставленной вне
  области: контракт §4.1 `build_natal_components.md` после A2, статусы README,
  оценки roadmap.

Коммит не создавай — он будет подготовлен отдельной командой после проверки
результата.
