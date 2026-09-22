# exact-orb — каталог мест: поиск подсказок и lookup выбранного place_id

**Статус:** контракт и catalog core M1-5 `feat/place-catalog` реализованы и
приняты: `PlaceSearch`, SQLite builder, `SqlitePlaceCatalog`, search/lookup и
сквозная интеграция с `BirthDataResolver`. HTTP endpoint остаётся M1-6, UI —
M1-7, доставка generated `places.sqlite` — M1-12.
**Дата:** 2026-09-21, ревизия 2026-09-22 — M1-5 выполнен.
**Область:** два независимых сценария над одним офлайн-каталогом:
`Place Search API → PlaceSearch.search(text)` и
`BirthDataResolver → PlaceCatalog.lookup(place_id)`.
**Основание:** ADR-0005, ADR-0019, roadmap M1-5 и действующий контракт
[`exact-orb_birth_data_resolution.md`](exact-orb_birth_data_resolution.md).
**Диаграммы:**
[`docs/sequence_diagrams/place_catalog/`](../../sequence_diagrams/place_catalog/README.md).

---

## 1. Цель и границы

Каталог предоставляет один серверный источник истины для выбора и повторной
проверки места рождения:

```text
поисковый текст → ограниченные подсказки с place_id
place_id        → координаты + tz_id + каноническое имя
```

Это два разных публичных контракта одного concrete-компонента:

```text
                         ┌─ PlaceSearch.search(text)
SqlitePlaceCatalog ──────┤
                         └─ PlaceCatalog.lookup(place_id)
                                  │
                             places.sqlite
```

`SqlitePlaceCatalog` открывается один раз на process lifecycle и реализует оба
порта над одним неизменяемым выпуском `places.sqlite`. Верхнеуровневая process
composition передаёт тот же экземпляр endpoint поиска и `BirthDataResolver`.

Каталог владеет географическими фактами: названием, страной, регионом,
координатами и `tz_id`. Он не вычисляет историческое UTC-смещение.
`utc_offset_seconds` получает `BirthDataResolver` через timezone-слой по
`tz_id`, локальной дате и времени рождения.

### 1.1. Статусы компонентов

| Компонент | Статус после M1-5 | Следующий владелец |
|---|---|---|
| `PlaceCatalog.lookup` и `ResolvedPlace` | уже реализованы; контракт сохраняется | — |
| `LocalPlaceCatalog` из JSONL | остаётся тестовым adapter над вручную поддерживаемой fixture | — |
| `PlaceSearch`, search outcomes | реализованы и приняты в M1-5 | HTTP mapping — M1-6 |
| `SqlitePlaceCatalog` | реализован и принят в M1-5 | lifecycle wiring — M1-6 |
| сборка `places.sqlite` из GeoNames | реализована и проверена на полных локальных данных | deployment M1-12 доставляет артефакт |
| `GET /places` и mapping исходов | только целевой контракт здесь | M1-6 |
| autocomplete и хранение выбранного ID | только целевой контракт здесь | M1-7 |

### 1.2. Состав ветки M1-5

В ветку входят:

- search-контракты, immutable outcomes и единственная pure-функция
  `normalize_place_query` в `exact_orb.birth.places`;
- leaf-adapter `exact_orb.birth.adapters.sqlite`, реализующий `PlaceSearch` и
  существующий `PlaceCatalog`;
- перевод `scripts/build_place_catalog.py` на воспроизводимую SQLite-сборку из
  трёх обязательных GeoNames-файлов;
- небольшие synthetic GeoNames fixtures и тесты сборщика, search, lookup,
  lifecycle, cancellation, module boundaries и интеграции с реальным
  `BirthDataResolver`;
- синхронизация этих требований и sequence diagrams.

Ветка не добавляет HTTP endpoint, middleware, UI, `places_db_path` в
`BootstrapSettings` или production lifespan wiring. Она также не меняет
семантику timezone resolution, существующие JSONL/golden fixtures и
calculation key.

---

## 2. Данные и производный артефакт

### 2.1. Источники

Сборка читает локальные дампы без сетевых запросов:

```text
cities1000.txt
admin1CodesASCII.txt
alternateNamesV2.txt
```

`cities1000.txt` предоставляет GeoNames ID, основные и ASCII-названия,
координаты, feature code, страну, admin1 code, население и `tz_id`.
`admin1CodesASCII.txt` предоставляет ASCII-подпись региона и GeoNames ID
региона из четвёртой колонки. Русская подпись региона выбирается по этому ID
из `alternateNamesV2.txt`; ASCII-подпись остаётся fallback.
`alternateNamesV2.txt` также нужен для выбора русского preferred-имени города
по явному language code и для индексации русских альтернативных названий.
Эвристика «первая строка с кириллическим символом» запрещена: на реальном
дампе она выбирает для Москвы `Məskeү`, а не `Москва`.

Все три файла обязательны для продуктовой сборки M1-5. Их отсутствие приводит
к явной ошибке сборщика до создания итогового SQLite-файла; тихий fallback на
эвристику выбора кириллицы запрещён.

Allow-list языков альтернативных имён в M1-5 содержит ровно один элемент:
`ALLOWED_ALTERNATE_LANGUAGES = frozenset({"ru"})`. Поэтому импортируются
только строки с `isolanguage="ru"`. Пустые значения и псевдоязыки GeoNames
(`link`, `wkdt`, `post`, `iata`, `icao`, `faac`, `abbr`, `phon`, `piny`,
`tcid`, `unlc`) приведены как пояснение и всегда находятся вне allow-list.
Расширение списка является изменением контракта выбора display-name и требует
явной ревизии требований.

Сборка выполняется потоково в следующем порядке:

1. прочитать небольшой `admin1CodesASCII.txt` и связать `country.admin1` с
   GeoNames ID региона;
2. одним проходом по `cities1000.txt` отфильтровать места и собрать множества
   нужных place ID и admin1 GeoNames ID;
3. одним проходом по `alternateNamesV2.txt` обработать только имена этих ID;
4. детерминированно записать места и имена в SQLite.

Полный `alternateNamesV2.txt` и все его строки в память не загружаются.

В каталог входят только записи:

- `feature class = P`;
- feature code не равен `PPLX`, `PPLH` или `PPLW`;
- `tz_id` непустой и присутствует в наборе IANA keys установленного Python
  distribution `tzdata`;
- `place_id` уникален внутри выпуска;
- страна и население проходят параметры сборки.

Сборщик не использует системную timezone database хоста для отбора строк.
Набор допустимых ключей берётся из package resources установленного direct
dependency `tzdata`, а его версия — через `importlib.metadata`. Неразрешимый
`tz_id`, включая `Nowhere/Fake`, отбрасывается и учитывается в итоговой
статистике сборки. Версия `tzdata` является явным входом воспроизводимости и
записывается в `build_parameters`.

Текущий baseline сборщика включает все записи `cities1000` для
`RU, UA, BY, KZ, MD, AM, GE, AZ, KG, UZ, TJ, TM, LT, LV, EE`, а для остальных
стран — записи с населением не меньше `100000`. Параметры входят в metadata
выпуска и не меняются скрыто между сборками.

### 2.2. Покрытие данных

Название `cities1000` задаёт нижнюю границу исходного дампа: населённые пункты
меньше примерно 1000 жителей могут отсутствовать даже для стран полного
покрытия. Для остальных стран дополнительный порог `100000` делает каталог
ещё уже. Пустая выдача поэтому означает «нет в этом выпуске каталога», а не
«такого места не существует в мире».

Система не пытается вычислить ближайший населённый пункт. Если поиск пуст,
форма предлагает человеку самостоятельно выбрать ближайший известный ему
город.

### 2.3. Имена

Имя из `alternateNamesV2.txt` считается актуальным для display-кандидатов,
если `isHistoric != 1` и колонка `to` пуста. Для поискового индекса
`historic = true`, если `isHistoric = 1` **или** `to` непусто. Колонка `from`
не сравнивается с датой сборки, чтобы результат не зависел от часов машины.
`isColloquial` и `isShortName` не меняют приоритеты первой версии.

Основное отображаемое имя выбирается детерминированно:

1. актуальное `ru`-имя с `isPreferredName`;
2. другое актуальное `ru`-имя;
3. исходное `name` из `cities1000.txt`;
4. `name_ascii` как последний fallback.

Если один уровень содержит несколько кандидатов, побеждает запись с
минимальным числовым `alternateNameId`. То же правило используется для
русского `admin1_name`; если русского актуального имени региона нет,
используется ASCII-подпись из `admin1CodesASCII.txt`.

Историческое имя не становится `display_name`, но может участвовать в поиске
с более низким приоритетом. Например, ввод «Ленинград» может вернуть текущее
место «Санкт-Петербург», если оба имени принадлежат одному GeoNames ID.

В первой версии индексируются:

- русское preferred-имя и русские актуальные варианты;
- русские исторические варианты с пониженным приоритетом;
- исходное GeoNames `name`;
- `name_ascii`.

Полный multilingual-поиск по всем альтернативам не входит в M1-5.

### 2.4. Координаты и timezone

Координаты рабочего каталога нормализуются до продуктовой точности `0.01°`.
Сборщик читает исходный текст через `Decimal` и применяет
`quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`, после чего хранит
координаты как целое количество сотых градуса. Adapter возвращает
`latitude_e2 / 100` и `longitude_e2 / 100` в существующие `float`-поля
`ResolvedPlace`. Python `round()` и округление уже разобранного binary float
не используются.

Пользователь не вводит и не корректирует координаты напрямую. `tz_id` берётся
из GeoNames и валидируется при сборке против зафиксированной версии Python
distribution `tzdata`. Готовый UTC-offset в базе не хранится, потому что он
зависит от даты и времени.

Версия `tzdata` в metadata описывает окружение сборки, но не является частью
валидности географической записи. Исторические правила применяет runtime
timezone-слой после lookup; изменение этих правил отражается в вычисленном
`utc_datetime`, а не в содержимом `PlaceCatalog`.

### 2.5. SQLite и metadata

Минимальное логическое представление:

```text
places
  place_id TEXT PRIMARY KEY NOT NULL
  display_name
  name_ascii
  country_code
  admin1_code
  admin1_name NULLABLE
  latitude_e2 INTEGER
  longitude_e2 INTEGER
  tz_id
  population

place_names
  place_id REFERENCES places
  name
  search_key
  language NULLABLE
  preferred
  historic

catalog_metadata
  schema_version
  source_checksums
  build_parameters, включая tzdata_version
```

Остальные SQL-типы и имена индексов являются деталями реализации. Обязательны:

- уникальность `places.place_id`;
- индексированный prefix lookup по `place_names.search_key` с `BINARY`
  collation;
- детерминированный порядок результатов;
- schema version и SHA-256 исходных файлов;
- запись фактических фильтров стран, населения и версии `tzdata`.

Сборщик пишет временную базу в каталоге рядом с целевым файлом, проверяет
схему и инварианты, закрывает все её дескрипторы и только затем выполняет
`os.replace` итогового `places.sqlite`. Временный файл и цель находятся на
одном томе; незавершённая сборка не повреждает прежний выпуск. SQLite —
производный артефакт: миграции для него не создаются, несовместимая схема
требует пересборки.

`source_checksums` содержит только SHA-256 содержимого трёх входных файлов.
`build_parameters.tzdata_version` содержит версию установленного Python
distribution `tzdata`. Metadata не включает mtime, время сборки или иное
значение, меняющееся при одинаковых входах, параметрах и версии `tzdata`.
Воспроизводимость означает логическое равенство строк, их нормативного порядка
и metadata; байтовое равенство SQLite-файлов не является контрактом.

Raw-дампы и готовая база не входят в Python wheel и не коммитятся. Каталог
доставляется как read-only слой или том deployment-окружения. Атрибуция
GeoNames обязательна в пользовательском интерфейсе; точная редакция лицензии
проверяется перед релизом.

### 2.6. Локальная сборка

Builder импортирует `normalize_place_query` из установленного пакета
`exact_orb`, поэтому перед локальным запуском рабочая копия устанавливается в
editable mode:

```text
python -m pip install -e .
python scripts/build_place_catalog.py --cities cities/cities1000.txt --admin1 cities/admin1CodesASCII.txt --alternate-names cities/alternateNamesV2.txt --out data/places.sqlite
```

Автономная stdlib-only работа скрипта после M1-5 не является контрактом.

---

## 3. Общие типы и порты

### 3.1. Подсказка

```python
class PlaceSuggestion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    place_id: str
    display_name: str
    admin1_name: str | None
    country_code: str
```

Подсказка намеренно не содержит `latitude`, `longitude` или `tz_id`.
Frontend возвращает выбранный `place_id`, а backend повторно получает
расчётные факты через `lookup`.

### 3.2. Исход поиска

```python
PlaceQueryErrorCode = Literal[
    "EMPTY",
    "TOO_LONG",
    "CONTROL_CHARACTERS",
    "NO_SEARCHABLE_CHARACTERS",
]


class PlaceSuggestions(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[PlaceSuggestion, ...]


class InvalidPlaceQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: PlaceQueryErrorCode


PlaceSearchOutcome = PlaceSuggestions | InvalidPlaceQuery
```

Пустой `PlaceSuggestions(items=())` — успешный поиск без совпадений.
Он принципиально отличается от `InvalidPlaceQuery`.

### 3.3. Порт поиска

```python
class PlaceSearch(Protocol):
    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> PlaceSearchOutcome: ...
```

`PlaceSearch`, `PlaceSuggestion`, `PlaceSuggestions` и `InvalidPlaceQuery`
реэкспортируются из `exact_orb.birth` как публичные контракты компонента.
Concrete SQLite-adapter через этот пакет не реэкспортируется.

`limit` обязан быть настоящим `int` в диапазоне `1..20`; `bool` не является
допустимым `int`. UI использует `10`. Нарушение программного контракта limit
не является пользовательским исходом поиска, отклоняется `ValueError` до SQL
и не достигает HTTP mapping при корректной валидации endpoint.

Технический отказ открытия или чтения каталога поднимается как существующий
типизированный `PlaceCatalogUnavailableError`. `CancelledError` не
перехватывается и не преобразуется в доменный исход.

### 3.4. Существующий lookup-контракт

```python
class ResolvedPlace(BaseModel):
    place_id: str
    canonical_name: str
    latitude: float
    longitude: float
    tz_id: str


class PlaceNotFound(BaseModel):
    place_id: str


PlaceResolution = ResolvedPlace | PlaceNotFound


class PlaceCatalog(Protocol):
    async def lookup(self, place_id: str) -> PlaceResolution: ...
```

Этот контракт сохраняется. В него не добавляются search-методы, HTTP-типы,
список кандидатов или данные исходного пользовательского текста.

GeoNames `place_id` состоит из ASCII-цифр. Пустая строка, строка длиннее 32
code points или строка с другими символами считается отсутствующим ID:
`lookup` возвращает `PlaceNotFound(place_id=...)` до SQL, а не исключение и не
отдельный пользовательский outcome. Типы кроме `str` остаются нарушением
Python-контракта порта и не нормализуются adapter-ом.

### 3.5. Concrete adapter и lifecycle

`SqlitePlaceCatalog` реализует `PlaceSearch` и `PlaceCatalog`, но каждый
потребитель зависит только от нужного ему порта.

```python
class SqlitePlaceCatalog:
    @classmethod
    async def open(
        cls,
        db_path: str | Path,
        /,
        *,
        executor: ThreadPoolExecutor,
    ) -> Self: ...

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> PlaceSearchOutcome: ...

    async def lookup(self, place_id: str) -> PlaceResolution: ...

    async def aclose(self) -> None: ...
```

`open` принимает только путь к file-backed SQLite, открывает его read-only и
не создаёт отсутствующий файл. После `Path.resolve(strict=True)` путь
преобразуется через `Path.as_uri()`, к URI добавляется `mode=ro`, а
`sqlite3.connect` вызывается с `uri=True`. Строковая склейка `file:` с путём и
`immutable=1` запрещены: первая ломает Windows/non-ASCII/`?`/`#` paths, второй
разрешает SQLite предполагать неизменность файла сильнее принятого lifecycle.
`aclose` идемпотентен; вызов `search` или `lookup` до успешного `open` либо
после `aclose` отклоняется типизированной ошибкой доступности каталога.

Контракты, outcomes и `LocalPlaceCatalog` остаются в лёгком модуле
`exact_orb.birth.places`. Concrete adapter располагается в leaf-модуле
`exact_orb.birth.adapters.sqlite` и импортируется напрямую только в точке
composition. Он не реэкспортируется из `exact_orb.birth.__init__` или
`exact_orb.birth.adapters.__init__`: импорт `exact_orb.birth` и контрактных
модулей не должен загружать `sqlite3`.

`tests/test_module_boundaries.py` фиксирует эту границу статически и в
изолированном процессе. Положительный контроль доказывает, что прямой импорт
`exact_orb.birth.adapters.sqlite` действительно загружает `sqlite3`, а импорт
`exact_orb.birth`, `exact_orb.birth.types` и `exact_orb.birth.places` — нет.
Adapter может импортировать birth contracts, но не зависит от `session`,
`application`, `calculation`, `engine`, `swiss_backend`, `agent`, `llm`,
`cli` или HTTP transport; этот allow-list также закрепляется boundary-тестом.

Последовательность process startup:

1. composition до приёма запросов вызывает `SqlitePlaceCatalog.open()` для
   `places.sqlite`;
2. `open()` открывает файл read-only и проверяет schema version, metadata,
   обязательные таблицы и индексы;
3. `open()` сравнивает `build_parameters.tzdata_version` с установленным
   distribution `tzdata`; при различии один раз пишет `WARNING`, но продолжает
   startup;
4. `open()` проверяет разрешимость всех различных `tz_id` эффективным runtime
   `ZoneInfo`; хотя бы один неразрешимый ID останавливает startup;
5. передаёт один экземпляр endpoint поиска и в
   `build_application_runtime(..., places=catalog, ...)`;
6. прекращает приём запросов и ждёт активные request tasks;
7. закрывает каталог один раз после остановки зависимых путей.

Таким образом, шаги 2–4 принадлежат `SqlitePlaceCatalog.open()` уже в M1-5.
Роль будущего composition из M1-6 — вызвать `open()` до приёма запросов и не
запускать HTTP server при его типизированном отказе.

`ApplicationRuntime` продолжает принимать внешний `PlaceCatalog` и не
становится владельцем каталога в M1-5. Владение принадлежит верхнему process
lifespan, который одновременно собирает HTTP search и Build path.

SQLite disk I/O не выполняется в event-loop thread. Adapter использует явно
внедрённый выделенный `ThreadPoolExecutor(max_workers=1)`; верхний process
lifespan владеет им и закрывает после каталога. Соединение создаётся на этом
worker с обычным `check_same_thread=True`; `open`, `search`, `lookup` и
`aclose` исполняются на том же worker последовательно. Глобальный executor,
скрытый `asyncio.to_thread`, `check_same_thread=False` и общий connection между
разными worker не являются частью контракта. Одновременные read-вызовы могут
ожидать worker, но получают отдельные result-модели; adapter не возвращает
один mutable экземпляр нескольким вызывающим.

Отказ `open()` поднимает `PlaceCatalogUnavailableError` до запуска HTTP server
и тем самым останавливает startup; это не HTTP-ответ и не application outcome.
Та же типизированная ошибка из `search` или `lookup` после успешного startup
маппится вызывающим слоем в runtime failure по сценариям ниже. Отмена task во
время ожидания worker распространяется как `CancelledError`; adapter не
преобразует её в `PlaceCatalogUnavailableError`. Перед `aclose` process
lifespan прекращает приём запросов и дожидается активных request tasks.

Несовпадение версий пишет ровно одно компактное событие
`place_catalog_tzdata_version_mismatch` уровня `WARNING` с полями
`catalog_tzdata_version` и `runtime_tzdata_version`. Оно не содержит данных
пользователя. Если вслед за ним найдена неразрешимая зона, startup завершается
ошибкой; если все зоны разрешимы, каталог считается пригодным.

Файл не заменяется под работающим процессом. Новый выпуск активируется только
при следующем старте. Благодаря этому любой `place_id`, возвращённый поиском,
обязан успешно разрешаться тем же каталогом в пределах process lifecycle.

---

## 4. Сценарий 1 — endpoint поиска мест

### 4.1. HTTP-контракт

Целевой M1-6 endpoint:

```http
GET /places?query=Москва&limit=10
```

Успешный ответ, включая пустую выдачу:

```json
{
  "items": [
    {
      "place_id": "524901",
      "display_name": "Москва",
      "admin1_name": "Москва",
      "country_code": "RU"
    }
  ]
}
```

Mapping:

| Результат `PlaceSearch` | HTTP | Тело |
|---|---:|---|
| `PlaceSuggestions(items=(...))` | 200 | `{ "items": [...] }` |
| `PlaceSuggestions(items=())` | 200 | `{ "items": [] }` |
| `InvalidPlaceQuery(code)` | 422 | `{ "code": "INVALID_PLACE_QUERY", "detail_code": code }` |
| `PlaceCatalogUnavailableError` | 503 | `{ "code": "PLACE_CATALOG_UNAVAILABLE", "retryable": true }` |

Endpoint не вызывает `ApplicationOrchestrator`, не загружает сессию и не
создаёт `BuildNatalCommand`. Session middleware может существовать на уровне
HTTP-приложения, но результат поиска не зависит от `SessionState`.

### 4.2. Нормализация и валидация

Единственная реализация — объект `exact_orb.birth.places.normalize_place_query`.
И `scripts/build_place_catalog.py`, и `exact_orb.birth.adapters.sqlite`
импортируют именно этот объект; локальные копии функции запрещены. Сначала raw
query проверяется на Unicode control characters; затем:

```python
def normalize_place_query(query: str) -> str | InvalidPlaceQuery: ...
```

Успешный результат — готовый `search_key`. Builder не индексирует source-name,
для которого функция вернула `InvalidPlaceQuery`, и учитывает такую строку в
статистике отклонённых имён.

1. Unicode NFKC;
2. trim и схлопывание Unicode whitespace до одного пробела;
3. `casefold()`;
4. `ё → е` для русского поиска.

Правила исходов:

- управляющий символ в raw query → `CONTROL_CHARACTERS`;
- пустая строка → `EMPTY`;
- длина больше 200 Unicode code points → `TOO_LONG`;
- нет ни одной Unicode-буквы или цифры → `NO_SEARCHABLE_CHARACTERS`.

Отсутствующий query или значение не строкового типа отклоняются схемой HTTP
endpoint до вызова `PlaceSearch`. `query=` с пустой строкой достигает каталога
и возвращает `InvalidPlaceQuery(code="EMPTY")`.

Допустимый алфавит не ограничивается кириллицей и латиницей. Диакритика,
дефисы и апострофы допустимы в реальных географических названиях. SQL всегда
параметризован; пользовательская строка не становится частью SQL-текста.

Общего accent folding нет: NFKC не превращает `ö` в `o` или `ł` в `l`.
Латинский поиск без диакритики работает только там, где GeoNames предоставляет
соответствующее `name_ascii`, которое индексируется отдельным alias. Например,
пользователь должен вводить именно опубликованную GeoNames-транслитерацию;
каталог не порождает дополнительные варианты самостоятельно.

### 4.3. Поиск и ранжирование

Поиск префиксный по нормализованному `search_key`. Fuzzy search, исправление
опечаток и произвольный substring search не выполняются.

Для индексного префикса используется бинарный диапазон
`search_key >= :lower AND search_key < :upper`, где `lower` — нормализованный
query, а `upper = lower + "\U0010FFFF"`. `LIKE` не является нормативной
реализацией: для Unicode-префикса SQLite может выбрать полный scan. Символы
`%` и `_` в query поэтому остаются обычными символами, а не wildcard.

Сначала по всем совпавшим именам вычисляется лучший ранг каждого `place_id`
(`GROUP BY place_id` и минимум rank или эквивалентная детерминированная
операция), затем уникальные места сортируются, и только после этого применяется
`LIMIT`. `LIMIT` до дедупликации запрещён.

Одна запись `place_id` возвращается не больше одного раза. Порядок:

1. точное совпадение нормализованного имени;
2. совпадение с текущим preferred-именем;
3. совпадение с актуальным именем перед историческим;
4. население по убыванию;
5. `place_id` как стабильный tie-breaker.

Подпись содержит `display_name`, регион при наличии и ISO country code, чтобы
различать одноимённые города. Поисковый alias не подменяет текущее
`display_name`.

### 4.4. Клиентское поведение

UI хранит отдельно текст поля и выбранный `place_id`. Любое изменение текста
после выбора сбрасывает ID. Build submit заблокирован, пока текущему тексту не
соответствует выбранная подсказка.

Для пустой выдачи UI сообщает, что место отсутствует в каталоге, и предлагает
выбрать ближайший известный пользователю город. Эта подсказка не создаёт
`place_substituted` и не меняет backend-контракт.

Debounce и отдельный rate limit endpoint принадлежат M1-6/M1-7. Они не
реализуются внутри `SqlitePlaceCatalog` и не заменяют индексированный поиск.

---

## 5. Сценарий 2 — BirthDataResolver резолвит place_id

### 5.1. Вход

Build API принимает:

```text
BirthInput {
    birth_date: date
    birth_time: time | None
    place_id: str
}
```

Свободного текста места, координат, `tz_id` и UTC-offset во входе нет.
`place_id` остаётся недоверенным, даже если ранее был получен из endpoint
подсказок: клиент может его изменить, а после перезапуска мог активироваться
новый выпуск каталога.

### 5.2. Путь вызова

```text
Build API
  → ApplicationOrchestrator
  → BuildNatalHandler
  → BirthDataResolver
  → PlaceCatalog.lookup(place_id)
  → SqlitePlaceCatalog
  → places.sqlite
```

Orchestrator выполняет существующие routing и session load до Handler.
Поиск по тексту в этом flow не вызывается.

### 5.3. Успешный lookup

`lookup(place_id)` возвращает ровно одну `ResolvedPlace`. Затем
`BirthDataResolver` использует `tz_id` вместе с локальной датой и временем для
исторического timezone resolution и формирует `ResolvedBirthData`.

В первой версии `ResolvedPlace.canonical_name` равен `places.display_name`.
Регион и country code используются в подписи подсказки для различения мест,
но не добавляются в `canonical_name`.

Контрольный сценарий:

```text
place_id = "524901"
birth_date = 1990-09-02
birth_time = 14:30

lookup → Москва, 55.75, 37.62, Europe/Moscow
timezone resolution → utc_offset_seconds = 14400
                    → utc_datetime = 1990-09-02 10:30Z
```

Переименование display-name в новом выпуске каталога не меняет
`calculation_key`, если координаты и UTC-момент не изменились.

### 5.4. ID отсутствует

Неизвестный, устаревший или подделанный ID даёт:

```text
PlaceNotFound(place_id)
  → InputRequired {
        issues: [{field: "birth.place", code: "INVALID"}]
    }
  → ApplicationInputRequired
```

Расчёт и commit не выполняются. Backend не запускает текстовый поиск повторно
и не выбирает другой город автоматически. UI должен потребовать новый выбор
из актуальных подсказок.

Это отличается от пустого результата search: там `place_id` ещё не был
выбран, поэтому `BirthDataResolver` вообще не вызывается.

### 5.5. Каталог недоступен

Ошибки SQLite, из-за которых lookup нельзя достоверно завершить, переводятся
adapter-слоем в `PlaceCatalogUnavailableError`. Resolver возвращает:

```text
ResolutionUnavailable(
    error_code="PLACE_CATALOG_UNAVAILABLE",
    retryable=True,
)
```

Handler поднимает исход без сохранения состояния, Orchestrator возвращает
`ApplicationResolutionFailure`. Ошибка зависимости не превращается в
`InputRequired`: изменение корректного пользовательского ввода её не исправит.

### 5.6. Накопление issues

Существующий порядок `BirthDataResolver` сохраняется: проверка даты и lookup
места выполняются до возврата пользовательских issues, чтобы неверные дата и
место могли быть показаны за один запрос. Timezone resolution начинается
только после успешного lookup и отсутствия накопленных issues.

---

## 6. Инварианты согласованности

1. Search и lookup читают один `places.sqlite` через один process-local
   `SqlitePlaceCatalog`.
2. Любой ID из `PlaceSuggestions` разрешается через `lookup` в том же process
   lifecycle.
3. Frontend не является источником координат, `tz_id` или UTC-offset.
4. Build API принимает только `place_id` и повторно проверяет его.
5. Каталог read-only во время работы процесса; hot reload отсутствует.
6. Результаты и внутренние записи не передаются вызывающим как общее mutable
   состояние.
7. Никаких runtime-сетевых запросов или fallback к RemoteGeocoder нет.
8. SQL параметризован, размер запроса и выдачи ограничен.
9. Ни search, ни lookup не обращаются к LLM, Agent Runtime или calculation
   engine.
10. Search не проходит через `ApplicationOrchestrator`; Build path проходит.

---

## 7. Ограничения первой версии

- Каталог ограничен составом `cities1000` и параметрами population filter.
- Нет населённых пунктов без пригодного `tz_id`.
- Нет fuzzy search, исправления опечаток, морфологии и произвольного substring.
- Нет определения ближайшего города по тексту или координатам пользователя.
- Нет ручного ввода координат и часового пояса.
- Нет runtime RemoteGeocoder и сетевого fallback.
- Нет hot reload: новый выпуск требует перезапуска процесса.
- Нет полной локализации на все языки; приоритет — русский, source name и ASCII.
- Нет общего accent folding; поддерживается только `name_ascii`, который уже
  опубликован GeoNames.
- Endpoint, debounce, rate limit и UI реализуются в M1-6/M1-7, не в M1-5.
- Сценарий устаревшего ID после смены выпуска механически возвращает INVALID;
  продуктовый recovery для уже сохранённой карты остаётся отложенным R-20.
- Каталог не является CalculationVersion и не входит в calculation key. Если
  обновление меняет координаты или `tz_id`, следующий Build естественно
  получает другой `CalculationInput` и другой ключ.
- `tests/fixtures/places.jsonl` остаётся вручную поддерживаемой тестовой
  fixture старого `LocalPlaceCatalog` с существующей точностью координат.
  Production builder после M1-5 создаёт только SQLite и не перезаписывает эту
  fixture. Поэтому JSONL и SQLite могут намеренно давать разные calculation
  keys; существующие golden-файлы в этой ветке не меняются.
- Production wiring пути к `places.sqlite` и создание общего экземпляра в
  HTTP lifespan входят в M1-6. В M1-5 adapter создаётся напрямую в тестах, а
  `build_application_runtime(..., places=...)` продолжает принимать каталог
  извне.

---

## 8. Приёмочные критерии

### 8.1. Сборка и данные

- **AC-P1:** сборщик создаёт SQLite из трёх локальных GeoNames-файлов без сети.
- **AC-P2:** две сборки из одинаковых входов, параметров и версии `tzdata`
  дают логически одинаковые строки, порядок и metadata.
- **AC-P3:** metadata содержит schema version, SHA-256 источников, параметры
  country/population filters и `tzdata_version`.
- **AC-P4:** Москва имеет `place_id="524901"`, русское display-name `Москва`,
  координаты `55.75/37.62` и `tz_id="Europe/Moscow"`; `Məskeү` не выбирается
  как display-name.
- **AC-P5:** несовместимая схема, повреждённая metadata, неразрешимый catalog
  `tz_id` или отсутствующий обязательный индекс останавливают startup до
  приёма запросов.
- **AC-P6:** `isolanguage != "ru"` не попадает в индекс; singleton allow-list
  нельзя расширить без явной ревизии требований. Две одинаково ранжированные
  русские записи выбираются по минимальному `alternateNameId`.
- **AC-P7:** русское имя admin1 выбирается через GeoNames ID региона, а при его
  отсутствии используется ASCII fallback.
- **AC-P8:** ошибка сборки оставляет предыдущий целевой файл неизменным;
  временная база создаётся рядом с ним и не остаётся активным выпуском.
- **AC-P9:** мини-дамп для проверки Москвы содержит `Москва`, `Məskeү`,
  non-preferred русское имя и псевдоязыковой alias, чтобы выбор и фильтрация
  не могли пройти вакуумно.
- **AC-P10:** запись с `tz_id="Nowhere/Fake"` не попадает в каталог, увеличивает
  счётчик отфильтрованных timezone и не делает готовый выпуск невалидным.
- **AC-P11:** несовпадение catalog/runtime `tzdata_version` пишет одно
  `WARNING` с обеими версиями и не останавливает startup, если каждый catalog
  `tz_id` разрешается runtime `ZoneInfo`.

### 8.2. Search

- **AC-S1:** `Москва`, `москва` и `МОСКВА` находят `524901`.
- **AC-S2:** `Moscow` находит тот же ID.
- **AC-S3:** одноимённые места имеют различимые регион и country code.
- **AC-S4:** один ID не дублируется из-за нескольких совпавших aliases.
- **AC-S5:** точное совпадение выше префиксного, затем применяется population
  ranking и стабильный tie-breaker.
- **AC-S6:** `###@@@` возвращает `InvalidPlaceQuery` и не выполняет SQL;
  счётчик запросов имеет отдельный позитивный контроль на корректном query.
- **AC-S7:** корректный неизвестный запрос выполняет SQL и возвращает
  `PlaceSuggestions(items=())`.
- **AC-S8:** prefix query использует индекс; приёмка не опирается на случайное
  время выполнения локальной машины.
- **AC-S9:** SQL metacharacters `%`, `_` и `'` не получают wildcard- или
  исполняемую семантику.
- **AC-S10:** ошибка чтения после startup становится
  `PlaceCatalogUnavailableError`, cancellation распространяется наружу.
- **AC-S11:** `limit=0`, `limit=21` и `limit=True` дают `ValueError` до SQL;
  пропущенный limit равен `10`.
- **AC-S12:** `PlaceSuggestions(items=())` остаётся успешным исходом и не
  равен `InvalidPlaceQuery`.
- **AC-S13:** `LIMIT` применяется после дедупликации; выдача содержит до limit
  различных place ID даже при нескольких совпавших aliases одного места.
- **AC-S14:** конкурентные `search` и `lookup` возвращают отдельные
  result-модели и не разделяют изменяемый экземпляр.

### 8.3. Lookup и интеграция

- **AC-L1:** каждый ID из результата search успешно разрешается lookup того же
  экземпляра каталога.
- **AC-L2:** неизвестный ID возвращает `PlaceNotFound`.
- **AC-L3:** реальная цепочка
  `search("Москва") → place_id → BirthDataResolver` для 02.09.1990 14:30
  возвращает `utc_offset_seconds=14400` и `10:30Z`.
- **AC-L4:** неизвестный ID даёт `InputRequired { birth.place, INVALID }`; ни
  timezone resolution, ни calculation, ни commit не выполняются.
- **AC-L5:** недоступный каталог даёт retryable
  `ResolutionUnavailable(PLACE_CATALOG_UNAVAILABLE)`, а не `InputRequired`.
- **AC-L6:** поиск не обращается к Orchestrator/ContextService, а Build path
  использует существующую цепочку Orchestrator → Handler → Resolver.
- **AC-L7:** `lookup("")`, lookup строки длиной 10 000 символов и нечислового
  ID возвращает `PlaceNotFound` без SQL и без runtime-исключения.

### 8.4. Границы модуля и lifecycle

- **AC-B1:** импорт `exact_orb.birth`, `exact_orb.birth.types` и
  `exact_orb.birth.places` не загружает `sqlite3`; прямой импорт
  `exact_orb.birth.adapters.sqlite` загружает его и служит позитивным
  контролем теста границ.
- **AC-B2:** `open`, чтение и `aclose` реально исполняются на внедрённом
  однопоточном executor, а event-loop thread не выполняет SQLite I/O.
- **AC-B3:** ошибка `open` не допускает запуск serving lifecycle; ошибка
  чтения после успешного `open` даёт runtime typed failure.
- **AC-B4:** adapter не создаёт и не завершает переданный executor; `aclose`
  проходит через тот же worker и завершается до shutdown executor владельцем.
- **AC-B5:** `aclose` идемпотентен; операции до успешного `open` и после
  закрытия не выполняют SQL и дают `PlaceCatalogUnavailableError`.
- **AC-B6:** AST-проверка подтверждает, что builder и SQLite-adapter импортируют
  `normalize_place_query` из `exact_orb.birth.places` и не определяют локальной
  функции; runtime-проверка подтверждает тождество импортированного объекта в
  обоих модулях canonical normalizer-у.
- **AC-B7:** read-only open использует `Path.as_uri()`, `mode=ro` и `uri=True`;
  отсутствующий файл и допустимые на текущей ОС пути с пробелами, non-ASCII и
  URI-special символами проверяются без создания или подмены файла.

---

## 9. Не входит в M1-5

- реализация FastAPI endpoint и HTTP middleware;
- UI autocomplete, debounce и browser acceptance;
- изменение standalone calculation CLI;
- RemoteGeocoder или другой сетевой сервис;
- автоматическое скачивание GeoNames;
- генерация JSONL production builder-ом;
- background refresh или миграции `places.sqlite`;
- профили пользователей и сохранение исходного текста места;
- автоматический выбор ближайшего населённого пункта;
- изменение timezone resolution, `BirthInput`, `ResolvedBirthData` или
  calculation key schema.
