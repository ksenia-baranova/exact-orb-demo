# Блок Research, P5a: контракты корпуса, проекция признаков и InMemory

Работай в ветке `feat/session-context`.

P1–P4 реализовали session contracts, InMemory persistence, `ContextService` и
SQLite session persistence. P4.1 исправил lifecycle SQLite connection, WAL
recovery, payload compatibility и runtime-import boundary.

В этой задаче реализуй **только контрактную половину** `Research Corpus`:
строгие модели de-identified категориальных признаков, чистую проекцию из
`ChartArtifact`, write-only порт, InMemory-реализацию и общий conformance-
набор, параметризуемый реализацией.

Термин de-identified здесь означает только отсутствие прямых и восстановимых
идентификаторов в схеме. Полный feature vector и UTC hour остаются потенциально
linkable; P5a не объявляет корпус анонимным или unlinkable.

SQLite-адаптер, схема, миграции, индексы, aggregation evidence, restart и
benchmark — это **P5b**, отдельная задача. Application handlers, orchestrator,
`bootstrap.py`, transport, UI feedback, consented corpus и consent-flow не
входят ни в P5a, ни в P5b.

Граница между P5a и P5b проведена по обратимости: состав бессрочно записываемых
полей, их гранулярность, канонизация и digest format фиксируются до схемы.
Место хранения, индексы и форма транзакции остаются задачей P5b.

## 0. Preflight

Прочитай корневой `AGENTS.md` и выполни:

```text
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log -10 --oneline
```

Если каталог не является Git-репозиторием, активна другая ветка либо в истории
нет P1–P4 и P4.1, остановись и сообщи.

Убедись, что существуют:

```text
src/exact_orb/session/context.py
src/exact_orb/session/adapters/in_memory.py
src/exact_orb/session/adapters/sqlite.py
src/exact_orb/calculation/types.py
tests/session/conformance.py
tests/fixtures/calculation.py

docs/requirements/decisions/0023-research-corpora-and-consent.md
docs/architecture/exact_orb_research_component.puml
docs/sequence_diagrams/research/001-record-and-quality.puml
```

До изменений запусти:

```text
python -m pytest -q tests/session tests/test_module_boundaries.py
python -c "import sys, pydantic; print(sys.version, pydantic.VERSION)"
```

Зафиксируй baseline. Посторонние дефекты не исправляй. Сохрани пользовательские
и несвязанные изменения рабочего дерева; если изменяемый файл уже dirty,
изучи diff и правь только относящиеся к P5a фрагменты.

Изучи перед изменением:

```text
docs/requirements/decisions/0023-research-corpora-and-consent.md
docs/requirements/decisions/0015-demo-vs-subscription-capability.md
docs/requirements/decisions/0018-interpretation-query-untrusted.md
docs/requirements/decisions/0021-modular-monolith-service-seams.md
docs/requirements/component_responsibilities/exact-orb_research_corpus.md
docs/requirements/component_responsibilities/exact-orb_session_requirements.md   (§6, §12–§15)
docs/architecture/service_ready_architecture.md
docs/architecture/exact_orb_research_component.puml
docs/sequence_diagrams/research/README.md
docs/sequence_diagrams/research/001-record-and-quality.puml

src/exact_orb/calculation/types.py
src/exact_orb/engine/ephemeris/types.py
src/exact_orb/engine/charts/natal.py
src/exact_orb/engine/aspects/types.py
src/exact_orb/engine/configurations/types.py
src/exact_orb/engine/configurations/patterns/**
src/exact_orb/engine/strength/types.py
src/exact_orb/engine/strength/balance.py
src/exact_orb/engine/strength/lunar_phase.py

src/exact_orb/session/adapters/in_memory.py
tests/session/conformance.py
tests/fixtures/calculation.py
tests/test_module_boundaries.py
```

Если один из перечисленных путей отсутствует из-за другой фактической раскладки,
найди источник через `rg --files`, зафиксируй соответствие в отчёте и не меняй
engine ради удобства P5a.

`prompts/**` — исторический журнал. Старые промты не редактируй и не считай их
выше действующих ADR и requirements.

## 1. Нормативные решения

ADR-0023 уже ревизован до начала P5a. Не переписывай решение повторно.
Реализация обязана соответствовать следующим пунктам.

### 1.1. Проверяемая privacy-граница

Research v1 гарантирует через модели, whitelist-проекцию и boundary-тесты:

1. нет `session_id`, cookie, IP, `run_id`, account ID и другого subject ID;
2. нет `calculation_key` и производного от birth data идентификатора;
3. нет birth input, места, координат, точного времени, JD, градусов, орбисов,
   скоростей и ephemeris provenance;
4. нет query text, response text, `ChartSpec`, полного `ChartArtifact`, warnings
   и generic metadata;
5. компонент не создаёт скрыто UUID, время или randomness.

Это не доказывает unlinkability: полный вектор, UTC hour, selection, model и
recipe version могут использоваться для корреляции. Не добавляй в код или
документы утверждение, что «идентификатора нет, значит удалить/сопоставить
нечего». Бессрочный retention и отсутствие session-delete — отдельное принятое
решение ADR-0023.

Каждое новое поле имеет ненулевую предельную privacy-стоимость. `DegreeFlag`
запрещён целиком: его булевы значения являются индикаторами точного градуса.

По тому же правилу знаки вспомогательных углов не входят в v1. `ANGLE_INDICES`
содержит восемь углов, но интерпретационно используются `asc` и `mc`; знаки
`armc`, `vertex`, `equatorial_ascendant`, `co_ascendant_koch`,
`co_ascendant_munkasey` и `polar_ascendant` вместе доопределяют время рождения
точнее, чем один Асцендент, и почти не имеют исследовательской ценности. `v1`
хранит знак только для `asc` и `mc`. `vertex` при этом остаётся допустимым
концом аспекта, потому что входит в `AspectConfig.natal_points`; его знак не
записывается.

### 1.2. Граница Research v1

ADR-0015 сохраняет продуктовый vocabulary
`topic ∈ {natal, transit}`. Research schema v1 уже:

```text
topic = natal
focus ∈ {general, career, money, love}
chart_kind ∈ {natal, cosmogram}
```

`topic=transit` не отвергается продуктом, но P5a его не принимает и не
записывает. Transit research требует контракта для natal base + transit chart.
Не представляй transit-ответ одной неуточнённой `ChartFeatures`.

Свободные Unicode-строки и `session.Selection` в бессрочный корпус не
принимаются. В session fixtures встречается `focus="relationships"`; это не
расширяет Research vocabulary и не меняет ADR-0015. Назови расхождение в
отчёте, не исправляя session.

### 1.3. Текст и consent

Always-on `ResearchRecord` не содержит query/response text и полный artifact.
Не утверждай, что эти поля уже принадлежат конкретной модели `RawQueryRecord`:
точный consented payload откладывается до отдельного решения. Не добавляй
nullable-поля «на будущее».

### 1.4. Append-only quality events

Базовая запись создаётся при готовности ответа. Rating, regenerate, copy и
время чтения имеют отдельные caller-owned ID и приходят позже. Они сохраняются
append-only событиями, не мутируют base record и не создают parent.

### 1.5. Совместимость

`feature_schema_version = 1` и content digest format v1 — persisted contracts.
Экспортируй `RESEARCH_DIGEST_FORMAT_VERSION: Final[Literal[1]] = 1`; это
версия алгоритма, а не второе поле каждой записи.
Их изменение требует явного решения и миграционной стратегии. P5a фиксирует
их golden fixtures до реализации SQLite.

Если обнаружено противоречие этих решений с действующим ADR или requirement,
остановись и сообщи. Не разрешай его молча кодом или ослаблением теста.

## 2. Цель и допустимые файлы

Создай:

```text
src/exact_orb/research/__init__.py
src/exact_orb/research/errors.py
src/exact_orb/research/models.py
src/exact_orb/research/outcomes.py
src/exact_orb/research/corpus.py
src/exact_orb/research/projection.py
src/exact_orb/research/adapters/__init__.py
src/exact_orb/research/adapters/in_memory.py

tests/research/__init__.py
tests/research/conformance.py
tests/research/test_models.py
tests/research/test_projection.py
tests/research/test_in_memory.py
tests/research/golden/research_digest_v1.json
```

При необходимости точечно измени только для фиксации реализованной границы:

```text
tests/test_module_boundaries.py
docs/requirements/decisions/0023-research-corpora-and-consent.md
docs/requirements/decisions/README.md
docs/requirements/component_responsibilities/exact-orb_research_corpus.md
docs/requirements/component_responsibilities/exact-orb_session_requirements.md
docs/architecture/service_ready_architecture.md
docs/architecture/exact_orb_research_component.puml
docs/sequence_diagrams/research/README.md
docs/sequence_diagrams/research/001-record-and-quality.puml
```

Документация уже актуализирована. Не переписывай её стилистически; меняй
только если реализация обнаружила конкретное противоречие, и назови его.

Не изменяй:

```text
src/exact_orb/session/**
src/exact_orb/calculation/**
src/exact_orb/engine/**
src/exact_orb/llm/**
src/exact_orb/interpretation/**
src/exact_orb/intent/**
src/exact_orb/orchestration/**
src/exact_orb/tools/**
tests/session/**
tests/conftest.py
tests/fixtures/**
docs/requirements/decisions/0024-sqlite-storage-implementation.md
docs/benchmarks/**
prompts/**
```

ADR-0024 не трогай: SQLite-решение относится к P5b.

## 3. Граница пакета

Стрелка означает «импортирует»:

```text
research.__init__              -> errors, models, outcomes, corpus
research.corpus                -> models, outcomes
research.adapters.in_memory    -> errors, models, outcomes, corpus
research.projection            -> calculation.types, errors, models
```

Требования:

- `exact_orb.research` экспортирует только contract API: модели, outcomes,
  ошибки, порт, `floor_to_utc_hour` и digest-функции;
- обычный импорт `exact_orb.research` не загружает projection, adapters,
  `sqlite3`, `calculation.types`, engine или `swisseph`;
- contract-модулям разрешены stdlib и Pydantic, но запрещены проектные импорты
  вне `exact_orb.research.*`;
- `research.projection` импортируется явно и является единственным Research-
  модулем, которому разрешён `exact_orb.calculation.types`;
- импорт `research.projection` в текущем графе ожидаемо загружает engine и
  `swisseph` через `calculation.types`; это positive control, а не разрешение
  contract/adapters зависеть от engine;
- adapters принимают уже санитизированные Research-модели, не видят
  `ChartArtifact` и не импортируют projection/calculation;
- `session/` ничего не знает о Research; его allowlist не расширяется;
- Research не импортирует session, application, LLM, orchestration, tools,
  CLI или edge;
- потребители Research contracts не импортируют их приватные имена.

## 4. Закрытые vocabulary v1

Все значения перечисляются в `research.models` явно. Модели не импортируют
engine; дублирование сознательное и контролируется drift-тестами §10.

### 4.1. Основные значения

```text
chart_kind = {natal, cosmogram}
topic      = {natal}
focus      = {general, career, money, love}

zodiac_sign = {
  Aries, Taurus, Gemini, Cancer, Leo, Virgo,
  Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces
}

aspect_type = {
  conjunction, semisextile, sextile, square, trine, quincunx, opposition
}
aspect_category = {exact, working, background}

configuration_type = {
  t_square, yod, bisextile, grand_cross, grand_trine, trapeze
}
configuration_category = {tight, moderate, loose}

dignity_system = {traditional, modern}
dignity_status = {domicile, exaltation, detriment, fall, peregrine}
strength_category = {strong, moderate, weak}
house_type = {angular, succedent, cadent}

element = {fire, earth, air, water}
modality = {cardinal, fixed, mutable}
balance_state = {deficit, balanced, excess}

quality_kind = {rating, regenerate, copy, reading_time}
```

Фаза Луны хранится только номером восьмифазной системы Рудьяра:

```text
lunar_phase_number ∈ 1..8
```

`PHASE_NAMES` из `engine/strength/lunar_phase.py` в корпус не переносится.
Имена русские и относятся к слою отображения: их редактирование стало бы
изменением формата бессрочного корпуса, а отображение номер ↔ имя биективно и
восстановимо. Drift-тест §10 проверяет, что система осталась восьмифазной.

### 4.2. Точки

```text
BODY_FEATURE_POINTS = {
  sun, moon, mercury, venus, mars, jupiter, saturn,
  uranus, neptune, pluto, chiron, true_node, mean_apog,
  south_node, pars_fortune, selena
}

ANGLE_FEATURE_POINTS = {asc, mc}

STRENGTH_POINTS = {
  sun, moon, mercury, venus, mars,
  jupiter, saturn, uranus, neptune, pluto
}

RELATIONAL_POINTS = BODY_FEATURE_POINTS ∪ {asc, mc, vertex}
```

`RELATIONAL_POINTS` совпадает с `AspectConfig.natal_points` после канонизации
имён и содержит ровно те точки, которые могут стать концом аспекта. Пять
вспомогательных углов в аспектах не участвуют и в vocabulary не входят.

### 4.2.1. Одно каноническое написание точки

`_natal_aspect_points` берёт долготу по raw-имени, но выпускает
`PositionedPoint.body = point_aliases.get(name, name)`. При значении по
умолчанию аспекты и конфигурации несут `north_node`, `lilith` и `pars`, а
`bodies` — `true_node`, `mean_apog` и `pars_fortune`. `point_aliases` —
поле конфигурации, поэтому при `point_aliases={}` те же аспекты придут с
raw-именами.

Хранить обе формы нельзя: в бессрочном корпусе одна точка окажется под двумя
именами, и `GROUP BY from_point` молча разделит Лилит надвое.

Поэтому проекция **канонизирует к raw-имени** тела:

```text
north_node -> true_node
lilith     -> mean_apog
pars       -> pars_fortune
```

Модели хранят только канонические имена; alias-набор существует исключительно
как входное отображение проекции. Появление alias в поле модели — ошибка
валидации, а не альтернативное написание.

### 4.3. Роли конфигураций

Роль не является свободной строкой. Точный набор зависит от типа:

```text
t_square    -> {apex, base_1, base_2}
yod         -> {apex, base_1, base_2}
bisextile   -> {center, wing_1, wing_2}
grand_trine -> {point_1, point_2, point_3}
grand_cross -> {axis_1_a, axis_1_b, axis_2_a, axis_2_b}
trapeze     -> {opposition_1, opposition_2, base_1, base_2}
```

Модель конфигурации отвергает отсутствующие, лишние и повторные роли, а также
повтор одного point в нескольких ролях.

### 4.4. Bounded identifiers

`calculation_version`, `recipe_version` и `model` имеют длину `1..128` и
соответствуют ASCII regex:

```text
^[A-Za-z0-9][A-Za-z0-9._:/+@~\-]{0,127}$
```

Пробелы, Unicode, control characters и пустая строка запрещены.

`@` и `~` входят в класс сознательно: gateway построен на litellm, а часть
провайдерских идентификаторов содержит `@` (например `text-bison@002`).
Отвергнутый `model` означал бы, что успешный ответ не удалось записать.

## 5. Контрактные модели

Все модели — Pydantic v2 с:

```text
ConfigDict(frozen=True, extra="forbid")
```

Вложенные коллекции — только tuple и другие immutable-типы.

### 5.1. Feature models

```text
BodyFeature {
    point: BODY_FEATURE_POINTS
    sign
    house: 1..12 | None
    retrograde: bool
}

AngleFeature {
    point: ANGLE_FEATURE_POINTS
    sign
}

AspectFeature {
    from_point: RELATIONAL_POINTS
    to_point: RELATIONAL_POINTS
    aspect_type
    category
}

ConfigurationPointFeature {
    role
    point: RELATIONAL_POINTS
}

ConfigurationFeature {
    configuration_type
    category
    points: tuple[ConfigurationPointFeature, ...]
    element: element | None
    modality: modality | None
}

DignityFeature {
    point: STRENGTH_POINTS
    system
    status
}

StrengthFeature {
    point: STRENGTH_POINTS
    category
    house_type
}

ElementBalanceFeature {
    axis = element
    bucket: element
    state
}

ModalityBalanceFeature {
    axis = modality
    bucket: modality
    state
}

BalanceFeature = ElementBalanceFeature | ModalityBalanceFeature

LunarPhaseFeature {
    phase_number: 1..8
}

ChartFeatures {
    feature_schema_version: Literal[1] = 1
    chart_kind
    bodies:         tuple[BodyFeature, ...] | None
    angles:         tuple[AngleFeature, ...] | None
    aspects:        tuple[AspectFeature, ...] | None
    configurations: tuple[ConfigurationFeature, ...] | None
    dignities:      tuple[DignityFeature, ...] | None
    strengths:      tuple[StrengthFeature, ...] | None
    balance:        tuple[BalanceFeature, ...] | None
    lunar_phase:    LunarPhaseFeature | None
}
```

Инварианты моделей:

- `None` означает «семейство не вычислялось», пустой tuple — «вычислялось,
  результатов нет»;
- balance axis и bucket согласованы типом union;
- configuration имеет точный role set из §4.3, уникальные роли и уникальные
  points;
- body/angle/strength point принадлежит своему множеству; alias
  (`north_node`, `lilith`, `pars`) отвергается везде;
- endpoints аспекта канонически ориентированы и не совпадают;
- bodies и angles уникальны по point;
- dignities уникальны по point, strengths — по point, balance — по
  `(axis, bucket)`;
- все `DignityFeature` одной `ChartFeatures` имеют одинаковый `system`:
  `NatalStrength.dignity_system` задан на карту целиком, поэтому смешанный
  набор engine произвести не может и модель его не принимает;
- дубликаты aspects/configurations не удаляются без отдельного решения.

Углы дают только знак. Куспиды домов, координаты углов, `HouseRulers`,
`Interception` и `DegreeFlag` не переносятся.

Осознанно не входят в v1: dispositor chains, mutual receptions, hemisphere и
house-type balance.

### 5.2. Канонический порядок

Модели нормализуют неупорядоченные feature tuples при создании, а не только в
projection. Поэтому напрямую созданный `ResearchRecord` и запись из artifact
имеют одну семантику.

Сортировка выполняется явной sort key, а не прямым сравнением кортежей:
`None` и значение не сравнимы между собой, и наивный `sorted()` по кортежу с
`house: int | None` или `element: str | None` бросит `TypeError`. Используй
ключ вида `(value is not None, value)` для каждого nullable-поля, чтобы `None`
шёл первым.

Сортировка лексикографическая по полному содержимому feature:

```text
bodies          -> point, sign, house(None before int), retrograde
angles          -> point, sign
aspects         -> from_point, to_point, aspect_type, category
config points   -> role, point
configurations  -> type, category, canonical points,
                   element(None before string), modality(None before string)
dignities       -> point, system, status
strengths       -> point, category, house_type
balance         -> axis, bucket, state
```

Сортировка стабильна, но не удаляет полностью одинаковые элементы.

### 5.3. Research record

```text
ResearchSelection {
    topic: Literal["natal"]
    focus: general | career | money | love
}

ResearchRecord {
    research_id: UUID4
    created_at: aware UTC hour
    calculation_version: bounded identifier
    chart_features: ChartFeatures
    selection: ResearchSelection
    recipe_version: bounded identifier
    model: bounded identifier
    tokens_in:  int >= 0 | None
    tokens_out: int >= 0 | None
    cost_usd:   finite float >= 0 | None
    latency_ms: finite float >= 0
}
```

`feature_schema_version` хранится ровно один раз — внутри `ChartFeatures`.
P5b может денормализовать его в индексируемую колонку, но не добавляет второй
независимый источник истины в модель.

Нулевые floats нормализуются к `+0.0`; NaN, Infinity и отрицательные значения
отвергаются. Не добавляй generic metadata, `dict[str, Any]`, `ChartSpec`,
warnings, provider response или исходный artifact.

### 5.4. Quality events

Используй явный discriminator `kind`:

```text
RatingEvent {
    kind: Literal["rating"]
    event_id: UUID4
    research_id: UUID4
    observed_at: aware UTC hour
    rating: 1..5
}

RegenerateEvent {
    kind: Literal["regenerate"]
    event_id: UUID4
    research_id: UUID4
    observed_at: aware UTC hour
}

CopyEvent {
    kind: Literal["copy"]
    event_id: UUID4
    research_id: UUID4
    observed_at: aware UTC hour
}

ReadingTimeEvent {
    kind: Literal["reading_time"]
    event_id: UUID4
    research_id: UUID4
    observed_at: aware UTC hour
    reading_time_ms: int >= 0
}

ResearchQualityEvent = Annotated[
    RatingEvent | RegenerateEvent | CopyEvent | ReadingTimeEvent,
    Field(discriminator="kind"),
]
```

У события ровно один смысл; extra-поля запрещены.

### 5.5. Время и скрытые входы

```text
def floor_to_utc_hour(value: datetime, /) -> datetime
```

Функция:

- принимает только aware datetime с `utcoffset() == timedelta(0)`;
- не конвертирует ненулевой offset;
- нормализует допустимый zero-offset tzinfo к `datetime.timezone.utc`;
- обнуляет minute, second и microsecond;
- не читает системные часы.

Поля моделей принимают только aware zero-offset datetime уже на границе часа,
нормализуют tzinfo к `timezone.utc` и отвергают ненулевые minute/second/
microsecond.

Research package может импортировать immutable-типы `UUID` и `datetime`, но
не вызывает `uuid4()`, `datetime.now()`, `datetime.utcnow()`, `date.today()`,
`time.time()`, `random`, не читает `os.environ`, `getenv` и environment.

## 6. Content digest format v1

Публичные чистые функции:

```text
RESEARCH_DIGEST_FORMAT_VERSION: Final[Literal[1]] = 1
def record_content_digest(record: ResearchRecord, /) -> str
def event_content_digest(event: ResearchQualityEvent, /) -> str
```

Правила byte-for-byte:

1. `record_content_digest` сериализует все поля, кроме `research_id`.
2. `event_content_digest` сериализует все поля, кроме `event_id`.
   `research_id`, `kind`, `observed_at` и payload входят обязательно.
3. Перед сериализацией применена модельная канонизация §5.2.
4. Enum сериализуется как `.value`, UUID — lowercase hyphenated string,
   datetime — `YYYY-MM-DDTHH:00:00Z`, tuple — JSON array, `None` — `null`.
5. JSON строится эквивалентом:

   ```text
   json.dumps(
       payload,
       ensure_ascii=False,
       allow_nan=False,
       sort_keys=True,
       separators=(",", ":"),
   ).encode("utf-8")
   ```

6. Результат — `hashlib.sha256(bytes).hexdigest()`: lowercase 64 hex chars.
7. Никакой salt, process state, model repr и Pydantic-internal JSON encoder в
   контракт не входят.

Создай `tests/research/golden/research_digest_v1.json`. Он содержит:

- полный canonical record payload без `research_id`;
- canonical payload каждого из четырёх event kinds без `event_id`;
- точные UTF-8 JSON strings;
- ожидаемые SHA-256 digests;
- diagnostic metadata о Python/Pydantic только как справку, не как часть
  digest.

Golden читается обеими сторонами теста; expected digest не вычисляй тем же
helper, который проверяется. Смена любого байта требует явного решения о
digest format и будущей P5b migration.

## 7. Проекция признаков

Публичная функция явного модуля:

```text
def project_chart_features(artifact: ChartArtifact, /) -> ChartFeatures
```

Функция чистая, детерминированная, ничего не мутирует и не читает часы.

Проекция строится только по whitelist. Не используй whole-object
`model_dump()` с последующим удалением запрещённых ключей.

Переносятся ровно поля §5.1. Не переносятся:

```text
calculation_key
ChartSpec
datetime_utc
julian_day_ut
latitude / longitude
longitude / latitude / distance и все speed
zodiac longitude, degree_in_sign, degree, minute, second, sign_index
orb / exact_angle / max_orb / thresholds
applying
scores / percentages / contributors / total_weight
house cusps и их координаты
angle longitudes
house_rulers, interceptions, near_interception, remaining_arc
degree flags и critical degrees
lunar phase elongation, boundaries, distances
dispositor chains, mutual receptions
hemisphere и house-type balance
swe_id / retflags / source / method / ephemeris flags и provenance
warnings
birth data
session identifiers, cookie, IP, run_id
query text, response text, generic metadata
```

Также не переносятся знаки вспомогательных углов (`armc`, `vertex`,
`equatorial_ascendant`, `co_ascendant_koch`, `co_ascendant_munkasey`,
`polar_ascendant`) и имя фазы Луны.

Перед построением моделей проекция канонизирует имена точек по §4.2.1:
alias из `AspectConfig.point_aliases` заменяется raw-именем тела. Углы
`asc`, `mc` и `vertex` алиасов не имеют и переносятся как есть. Аспект с
концом `vertex` проецируется, но `AngleFeature` для `vertex` не создаётся.

Порядок нормализуется моделями по §5.2. Симметричные концы аспекта сначала
приводятся к лексикографической ориентации. Дубликаты aspects/configurations
не удаляются.

Неизвестное categorical-значение даёт typed `ResearchProjectionError` с
`error_code="RESEARCH_PROJECTION_UNSUPPORTED_VALUE"`. Само неизвестное
значение, artifact content и backend exception не попадают в текст ошибки.

`calculation_version` не является частью `ChartFeatures`; caller будущего
application path обязан скопировать его из того же `ChartArtifact` в
`ResearchRecord`. P5a не создаёт скрытую record factory, которая генерирует ID
или время.

## 8. Порт, outcomes и ошибки

В `research.corpus`:

```text
@runtime_checkable
class ResearchCorpus(Protocol):
    async def put_record(
        self, record: ResearchRecord, /,
    ) -> ResearchStored | ResearchAlreadyStored | ResearchIdConflict: ...

    async def put_quality_event(
        self, event: ResearchQualityEvent, /,
    ) -> (
        QualityStored
        | QualityAlreadyStored
        | QualityEventIdConflict
        | ResearchRecordAbsent
    ): ...
```

Все outcomes — frozen Pydantic models с `extra="forbid"`:

```text
ResearchStored        {research_id}
ResearchAlreadyStored {research_id}
ResearchIdConflict    {research_id}

QualityStored          {event_id, research_id}
QualityAlreadyStored   {event_id, research_id}
QualityEventIdConflict {event_id}
ResearchRecordAbsent   {event_id, research_id}
```

Outcomes не содержат digest, backend exception и произвольный текст.

Семантика record:

- новый ID → `ResearchStored`;
- существующий ID и тот же digest → `ResearchAlreadyStored`;
- существующий ID и другой digest → `ResearchIdConflict`;
- conflict никогда не переписывает исходную запись.

Семантика event и порядок классификации:

1. сначала ищется `event_id`;
2. существующий ID с тем же digest → `QualityAlreadyStored`;
3. существующий ID с другим digest → `QualityEventIdConflict`, независимо от
   наличия parent, указанного в конфликтующем payload;
4. только для нового `event_id` проверяется `research_id`;
5. отсутствующий parent → `ResearchRecordAbsent` без создания строки;
6. существующий parent и новый ID → `QualityStored`.

Ошибки:

```text
ResearchProjectionError(error_code)
ResearchPersistenceError(error_code)
ResearchWriteError(ResearchPersistenceError)
```

Стабильные коды P5a:

```text
RESEARCH_PROJECTION_UNSUPPORTED_VALUE
RESEARCH_WRITE_FAILED
```

`error_code` непустой. Текст исключения безопасен и не включает неизвестное
значение, record/event content, путь или raw backend exception. InMemory не
должен создавать искусственный failure path только ради проверки ошибки;
SQLite mapping проверит P5b adapter-specific suite.

Порт намеренно не содержит `get`, `list`, `delete`, `delete_by_session`,
`touch`, TTL, reaper, consent и analytics reader. Публичного чтения ради
тестов не добавляй.

## 9. Тесты моделей, digest и проекции

### 9.1. `test_models.py`

Покрой:

- frozen, `extra="forbid"` и deep immutability каждой модели;
- точные закрытые vocabulary;
- границы house/rating/phase/metrics и отказ NaN/Infinity;
- нормализацию `-0.0`;
- UUID4;
- точный identifier regex и длину 1/128/129, включая приём `@` и `~` в
  провайдерских идентификаторах вида `text-bison@002`;
- отказ naive, non-UTC и неокруглённого времени;
- нормализацию разных zero-offset tzinfo к `timezone.utc`;
- `floor_to_utc_hour` на границах часа;
- отказ `topic=transit`, произвольных topic/focus и session-значения
  `relationships`;
- discriminator quality union и отказ extra/mixed payload;
- границы `phase_number` и отсутствие поля имени фазы;
- balance axis/bucket;
- configuration role matrix;
- point subsets и uniqueness rules;
- отказ alias-имён `north_node`, `lilith`, `pars` во всех point-полях;
- отказ `armc` и прочих вспомогательных углов в `AngleFeature` при приёме
  `vertex` как конца аспекта;
- единый `system` у всех `DignityFeature` одной записи;
- canonical tuple order при прямом создании модели, включая nullable-поля;
- различие `None` и пустого tuple;
- стабильность digest при перестановке неупорядоченных features;
- изменение `research_id` **не меняет** record digest;
- изменение `event_id` **не меняет** event digest;
- изменение `research_id`, `kind`, `observed_at` или payload **меняет** event
  digest;
- точное соответствие golden canonical JSON и SHA-256.

Не проверяй «validation failure не меняет backend»: нормальная Pydantic-
валидация происходит до вызова `ResearchCorpus`, а поведение `model_construct`
не является публичным контрактом.

### 9.2. `test_projection.py`

Создай богатый artifact локально в тесте, не меняя `tests/fixtures/**`.
Все разрешённые семейства непусты.

Обязательно:

- точный ожидаемый `ChartFeatures`, построенный литерально;
- positive control для bodies, angles, aspects, configurations, dignities,
  strengths, balance и lunar phase;
- изменение каждого разрешённого categorical-признака меняет результат;
- изменение каждого forbidden-семейства при неизменных категориях результат
  не меняет;
- `None` и пустой tuple различаются;
- порядок исходных dict/collections не влияет;
- artifact не мутируется;
- неизвестное categorical-значение даёт безопасный typed error;
- cosmogram сохраняет `house=None`, не создаёт angles/house-dependent
  strength и не превращается в transit;
- аспект с endpoint-углом `asc`, `mc` или `vertex` проецируется, при этом
  `AngleFeature` создаётся только для `asc` и `mc`;
- artifact, построенный с `point_aliases` по умолчанию, и artifact с
  `point_aliases={}` дают **одинаковые** `AspectFeature` и
  `ConfigurationFeature`: канонизация §4.2.1 приводит оба к raw-именам. Это
  ключевой тест, без него две конфигурации engine дадут два написания одной
  точки в бессрочном корпусе.

Собери poisoned artifact с уникальными валидными sentinels в
`calculation_key`, datetime, координатах, JD, longitude,
degree/minute/second, orb/max_orb, scores/percentages, warnings и ephemeris
metadata. Рекурсивно проверь отсутствие sentinels в `ChartFeatures`,
`ResearchRecord` и их сериализации. Негативную проверку дополни positive
control по каждому feature family, чтобы всегда-пустая проекция не прошла.

## 10. Drift закрытых словарей

`test_projection.py` — единственный Research test module, которому разрешены
engine imports. Проверь, что источники engine являются подмножеством либо
точно соответствуют Research v1:

- `ChartKind` через `typing.get_args`;
- `AspectType`, `AspectCategory`;
- `ConfigurationType`, `ConfigurationCategory`;
- `DignityStatus`, `StrengthCategory`, `HouseType`, `BalanceState`;
- dignity system literals `traditional/modern`;
- `ZODIAC_SIGNS`;
- `DEFAULT_BODY_IDS`;
- derived names `south_node`, `pars_fortune`, `selena` из natal builder;
- `AspectConfig.natal_points` после канонизации — совпадает с
  `RELATIONAL_POINTS`;
- `ConfigurationConfig.points` после канонизации — подмножество
  `RELATIONAL_POINTS`;
- `DEFAULT_POINT_ALIASES`: ключи ⊆ `BODY_FEATURE_POINTS`, значения не входят
  ни в одно vocabulary модели и известны только карте канонизации;
- `ELEMENTS`, `MODALITIES` из **обоих** источников engine —
  `strength/balance.py` и `configurations/patterns/common.py`;
- `len(PHASE_NAMES) == 8`: система остаётся восьмифазной, сами имена в корпус
  не переносятся;
- role sets всех configuration patterns.

Углы проверяются по отдельному правилу, потому что Research v1 сознательно
уже `ANGLE_INDICES`:

```text
ANGLE_FEATURE_POINTS  = {asc, mc}
EXCLUDED_ANGLE_POINTS = {armc, vertex, equatorial_ascendant,
                         co_ascendant_koch, co_ascendant_munkasey,
                         polar_ascendant}

set(ANGLE_INDICES) == ANGLE_FEATURE_POINTS | EXCLUDED_ANGLE_POINTS
```

Новый угол в engine не попадёт ни в одно множество и уронит тест, требуя
явного решения. `vertex` при этом входит в `RELATIONAL_POINTS`: он участвует
в аспектах, но своего знака не даёт.

Тест должен явно показать направление канонизации:

```text
north_node -> true_node
lilith     -> mean_apog
pars       -> pars_fortune
```

Rich artifact не считается доказательством полноты vocabulary. Он проверяет
проекцию, а drift suite — декларативные engine-источники. Не меняй engine ради
совпадения; новый источник должен сначала вызвать fail-closed тест и явное
решение о Research schema.

## 11. Conformance и InMemory

### 11.1. Harness

Оформи `tests/research/conformance.py` так, чтобы P5b подключил factory без
изменения файла:

```text
ResearchHandles:
    primary: ResearchCorpus
    peer: ResearchCorpus

ResearchCorpusFactory:
    () -> AsyncContextManager[ResearchHandles]

class ResearchCorpusConformance:
    def make_factory(self, tmp_path: Path) -> ResearchCorpusFactory: ...
```

Каждый вход factory создаёт изолированный backend и гарантирует cleanup.
`primary is not peer` обязательно для каждой реализации; обе фасеты одного
factory разделяют один backend. Так cross-handle не схлопывается в same-handle.

Из этого следует единственное сознательное исключение из правила «тесты не
трогают приватные имена»: чтобы построить две фасеты над одним backend, не
вводя публичную backend-фабрику, InMemory-override создаёт
`_InMemoryBackend()` напрямую. Исключение ограничено телом `make_factory` в
`conformance.py`, сопровождается комментарием с этим обоснованием и не
распространяется на тесты и на реализацию. P5b в нём не нуждается: два handle
получаются двумя вызовами `open()` над одним файлом.

Concrete-класс `TestInMemoryResearchCorpus` переопределяет только
`make_factory`, не имеет `__init__` и собирается pytest. Meta-test доказывает
ненулевое число унаследованных `test_*` и факт переопределения factory.

Все samples/builders объявлены один раз в `conformance.py`.

### 11.2. Общая матрица

1. новый record → Stored;
2. точный retry → AlreadyStored;
3. тот же record ID с другим содержимым → conflict;
4. после conflict retry исходного record → AlreadyStored, конфликтующего →
   снова conflict: это доказывает сохранность без `get`;
5. новый quality event → Stored;
6. точный retry event → AlreadyStored;
7. тот же event ID с другим содержимым → conflict;
8. collision event ID имеет приоритет над absence нового parent;
9. новый event для отсутствующего record → ResearchRecordAbsent;
10. последующая вставка record с этим `research_id` → Stored: event не создал
    parent;
11. два разных события одного record сохраняются; retry каждого даёт
    AlreadyStored;
12. события разных видов сосуществуют;
13. concurrent same-ID record race → один Stored и один AlreadyStored;
14. concurrent conflicting-record race → один Stored и один conflict;
15. concurrent same-ID event race → один Stored и один AlreadyStored;
16. concurrent conflicting-event race → один Stored и один conflict;
17. публичного read/delete/TTL/reaper/consent API нет.

Record и event races параметризуются `same-handle` и `cross-handle`.

### 11.3. Управление гонками

В generic conformance внешний start gate/barrier доказывает, что обе coroutine
запущены и готовы вызвать публичный метод до одновременного release. После
release проверяется полный multiset outcomes и повторными writes — сохранённое
содержимое.

Не утверждай, что generic harness доказал физический overlap внутри private
critical section: порт такого наблюдения не предоставляет. Реальную worker/
transaction конкуренцию P5b докажет SQLite-specific seam.

Timeout — только защита от зависания. Никаких `sleep`, случайных задержек и
retry loops.

### 11.4. InMemory-specific

В `test_in_memory.py` проверь:

- `InMemoryResearchCorpus(_backend, /)` требует private positional-only
  backend; zero-argument constructor даёт `TypeError`;
- публичной фабрики backend нет; единственное место, где backend создаётся
  напрямую, — `make_factory` в `conformance.py` (§11.1);
- primary и peer — разные фасеты одного private backend;
- два разных backend изолированы;
- проверка ID/digest/parent и вставка находятся в одной backend-scoped
  критической секции для record и event;
- instrumented synchronous entry counter доказывает, что обе ветви каждой
  гонки действительно прошли critical section;
- после входа в critical section нет `await`; barrier внутрь неё не ставится;
- private snapshot допустим только в InMemory-specific тесте lifecycle-
  инварианта и не превращается в публичный read API.

Generic conformance не требует искусственного technical failure. Форму
`ResearchWriteError` тестируй как контракт; mapping реального backend failure
добавит P5b.

## 12. Границы модулей

Добавь discovery-наборы:

```text
RESEARCH_CONTRACT_MODULES
RESEARCH_PROJECTION_MODULES
RESEARCH_ADAPTER_MODULES
```

Проверь:

- contract-модули входят в backend-free contract layer;
- они импортируют из проекта только `exact_orb.research.*`; stdlib/Pydantic
  разрешены;
- их declared import graph ацикличен;
- projection объявляет `exact_orb.calculation.types`, но не application, LLM,
  session, adapters, `sqlite3` или edge;
- InMemory adapter импортирует только Research contracts и stdlib;
- adapters не импортируют projection/calculation;
- Research consumers не импортируют приватные contract names;
- session boundary sets не изменены и не ослаблены.

AST-проверка скрытых входов запрещает вызовы/доступ:

```text
uuid4
datetime.now / datetime.utcnow / date.today
time.time
random.*
os.environ / os.getenv / getenv
```

Она не запрещает импорт и использование immutable-типов `UUID`, `datetime`,
`timezone`, `timedelta`.

Subprocess-импорты используют модель P4.1
`REQUIRED ⊆ loaded ⊆ REQUIRED ∪ KNOWN_TRANSITIVE_DEBT`:

1. `import exact_orb.research` загружает contract API, но не projection,
   adapters, `sqlite3`, `swisseph`, calculation, engine, config или edge;
2. `import exact_orb.research.adapters` загружает InMemory API, но не
   projection, calculation или `sqlite3`;
3. `import exact_orb.research.projection` загружает `calculation.types`, engine
   и `swisseph` как positive control, но не application, LLM, session adapters,
   `sqlite3` или edge.

У каждой негативной runtime-проверки есть позитивный контроль по публичному
символу соответствующего сценария.

## 13. Документация

До реализации уже синхронизированы:

- ADR-0023: threat model, v1 scope, отсутствие response text, append-only
  events, caller-owned identity/time и digest format v1;
- decisions README;
- Research component requirements;
- session requirements §6;
- service-ready architecture;
- component diagram;
- Research sequence diagram.

Проверь, что реализация им соответствует. Если понадобилась нормативная
правка, измени только конкретно затронутый фрагмент и объясни конфликт.
Application sequence diagrams не меняй: producer path ещё не реализован.

Если локальный PlantUML renderer доступен, отрендери изменённые диаграммы.
Не заявляй render без фактического запуска.

## 14. Что не входит

Не реализуй в P5a:

- SQLite-адаптер, схему, миграции, индексы, транзакции, aggregation evidence,
  restart и benchmark — P5b;
- `RawQueryRecord`, `Consent`, revoke, delete-by-consent;
- query/response text и полный artifact в долгосрочном хранилище;
- freeform input;
- application commands, handlers, orchestrator, bootstrap;
- HTTP, cookies, UI feedback;
- durable outbox, background delivery, write-always/fail-open policy;
- Analytics, History, публичный analytics reader или export API;
- `chart_group_id`;
- `topic=transit`, transit projection и несколько карт в записи;
- schema v2 features: dispositors, mutual receptions, hemisphere и house-type
  balance;
- изменение calculation, engine, LLM или session behavior;
- compatibility aliases;
- скрытую генерацию времени и ID;
- искусственный backend failure API только ради P5a-теста.

P5a даёт контракт. Утверждение «каждый ответ стенда записан» становится
проверяемым только после P5b и отдельной application-задачи.

Не создавай commit, push или PR без отдельной команды.

## 15. Проверки

```text
python -m pytest --collect-only -q tests/research
python -m pytest -q tests/research/test_models.py tests/research/test_projection.py
python -m pytest -q tests/research/test_in_memory.py
python -m pytest -q tests/research tests/test_module_boundaries.py
python -m pytest -q tests/session tests/research tests/test_module_boundaries.py
python -m pytest -q
git diff --check
git status --short
```

Приведи фактические числа collected/passed. Не запускай отсутствующие
Ruff/mypy/coverage gates, сетевые, платные и LLM smoke tests.

## 16. Acceptance P5a

P5a завершён, когда:

1. Реализация соответствует актуальному ADR-0023; найденные противоречия
   названы, а не разрешены молча.
2. Research — отдельный sibling-пакет; session isolation не ослаблена.
3. Корневой import не загружает projection/adapters/native/runtime.
4. Explicit projection import имеет ожидаемый positive control engine/swisseph.
5. Все модели frozen, deeply immutable и `extra="forbid"`.
6. Vocabulary v1 перечислен явно и fail-closed; точка имеет ровно одно
   каноническое написание, alias отвергается моделью.
7. `topic=transit` отвергается Research v1, не притворяется single-chart.
8. Cross-field invariants phase, balance, roles и point subsets проверяются.
9. Feature tuples канонизируются моделями; `None` и empty различимы.
10. UTC hour и caller-owned UUID/time соблюдены; скрытых входов нет.
11. `feature_schema_version` имеет один источник истины.
12. Digest byte-for-byte соответствует format v1 и frozen golden.
13. Event digest включает parent ID и kind; исключает только event ID.
14. Projection — whitelist; forbidden sentinels не проходят.
15. Query/response text и полный artifact отсутствуют.
16. Base record и events имеют раздельный append-only lifecycle.
17. Outcome shapes, precedence и error codes стабильны.
18. Conformance доказывает поведение через публичные writes без test-only get.
19. Primary/peer — разные handles одного backend; cross-handle невырожден.
20. Generic race не выдаётся за доказательство physical overlap; InMemory и
    будущий SQLite имеют adapter-specific controls.
21. Drift suite покрывает enums, направление канонизации aliases, derived
    points, `natal_points`, разбиение `ANGLE_INDICES` на включённые и
    исключённые углы, восьмифазность и roles.
22. Документы и диаграммы не расходятся с реализацией.
23. Полный pytest фактически запущен, результаты приведены.
24. P5b, consented corpus, transit и application не объявлены реализованными.

## 17. Итоговый отчёт

Начни с результата. Укажи:

- фактическую границу пакета и import graph;
- точный vocabulary v1, канонизацию alias и состав включённых углов;
- cross-field invariants и canonical ordering;
- состав `ChartFeatures` и семантику None/empty;
- whitelist и forbidden projection fields;
- digest format, golden fixture и точные hashes;
- record/event lifecycle, outcome precedence и error codes;
- конструкцию InMemory и невырожденный conformance factory;
- что именно generic races доказывают и чего не доказывают;
- результат полного drift suite;
- boundary checks и positive controls;
- точные команды и реальные числа tests;
- сохранённые пользовательские изменения;
- остаточный linkage-риск как принятый риск, а не обещание unlinkability;
- отложенное: P5b, consented payload, transit/multi-chart, schema v2,
  application wiring;
- расхождение session `relationships` против Research `love`.
