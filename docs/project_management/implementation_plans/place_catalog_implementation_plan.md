# Каталог мест — план реализации и карточки промтов

**Дата исходной сверки:** 2026-09-21.

**Статус:** запланировано; ни одна карточка реализации не выполнялась.

**Ветка:** `feat/place-catalog`.

**HEAD исходной сверки:** `4d3c7953e5cdaa2f7b885028438714185d238661`.

**Плановое разбиение:** десять рабочих промтов. Первые четыре функциональные
группы идут парами production-код → отдельный промт с тестами; после готовности
всего кода следуют два сквозных приёмочных промта. RED/GREEN и test-first
порядок не используются.

## 1. Цель ветки

Ветка должна предоставить один read-only SQLite-каталог мест для двух разных
сценариев:

1. `PlaceSearch.search(query)` возвращает ограниченные подсказки для будущего
   HTTP endpoint и UI.
2. `BirthDataResolver` повторно разрешает выбранный недоверенный `place_id`
   через существующий `PlaceCatalog.lookup(place_id)`.

Оба сценария используют один process-local `SqlitePlaceCatalog` и один выпуск
`places.sqlite`. Каталог хранит координаты и `tz_id`, но не хранит
`utc_offset_seconds`: историческое смещение остаётся ответственностью
timezone-слоя.

Результатом ветки являются контракты поиска, воспроизводимый builder,
SQLite-adapter, индексный поиск, lifecycle и доказательства интеграции с
`BirthDataResolver`. FastAPI, middleware, UI и production wiring остаются
M1-6/M1-7.

## 2. Источники истины

- [AGENTS.md](../../../AGENTS.md).
- [Требования каталога мест](../../requirements/component_responsibilities/exact-orb_place_catalog.md).
- [Требования BirthDataResolver](../../requirements/component_responsibilities/exact-orb_birth_data_resolution.md).
- [Сценарии](../../requirements/scenarios.md) и
  [sequence diagrams](../../sequence_diagrams/place_catalog/README.md).
- [Roadmap M1-5](../roadmap.md).
- [ADR-0005](../../requirements/decisions/0005-resolve-in-intent-layer.md),
  [ADR-0017](../../requirements/decisions/0017-calculation-cache-and-chartspec.md)
  и [ADR-0019](../../requirements/decisions/0019-defer-nl-birth-data.md).
- [Тесты архитектурных границ](../../../tests/test_module_boundaries.py).
- Текущие `src/exact_orb/birth/places.py`, `birth/resolver.py`,
  `application/bootstrap.py`, `scripts/build_place_catalog.py` и существующие
  birth/application tests.

Рабочие untracked-требования и диаграммы этой ветки являются актуальным
целевым контрактом. Исторические `prompts/**` не заменяют их и не изменяются.

## 3. Исходное состояние

| Область | Состояние на исходной сверке | Следствие |
|---|---|---|
| `PlaceCatalog`, `ResolvedPlace`, `PlaceNotFound` | Реализованы в `birth/places.py` | Сигнатура lookup сохраняется |
| `LocalPlaceCatalog` | Читает JSONL и используется fixtures/tests | JSONL и golden-файлы не меняются |
| `BirthDataResolver` | Уже вызывает `PlaceCatalog.lookup` и типизированно обрабатывает недоступность | Новая семантика resolver не нужна |
| `PlaceSearch` и search outcomes | Отсутствуют | Вводятся карточкой 1.1 |
| Builder | Создаёт JSONL и выбирает первую кириллицу эвристически | Полностью переводится на SQLite карточкой 2.1 |
| `SqlitePlaceCatalog` | Отсутствует | Вводится leaf-adapter без eager import |
| Production composition | `build_application_runtime(..., places=...)` получает порт извне | M1-5 не добавляет `places_db_path` и HTTP lifespan |
| GeoNames inputs | Локально присутствуют обязательные `cities1000.txt`, `admin1CodesASCII.txt`, `alternateNamesV2.txt`; также скачан необязательный `iso-languagecodes.txt` | Полный local-data smoke готов к запуску; `iso-languagecodes.txt` не расширяет singleton allow-list `{"ru"}` |

## 4. Правило «code then tests»

Для пар `.1/.2` действует один порядок:

1. Карточка `.1` реализует только заявленный production-результат. Новые тесты
   в ней не пишутся. Разрешено запускать существующую регрессию и статические
   проверки. Карточка 2.1 также создаёт явно перечисленные data-only fixtures
   для ручного прогона builder; исполняемые тесты по ним появляются только в
   2.2.
2. Карточка `.2` добавляет тесты к уже существующей реализации. Production-код
   в ней не меняется.
3. Если тестовая карточка обнаруживает дефект реализации, работа возвращается
   в предыдущую code-карточку либо оформляется узкая correction-карточка.
   Тестовый промт не получает скрытого разрешения исправлять production.

Карточка не обязана становиться отдельным коммитом. Commit, push и PR требуют
отдельного указания пользователя. При подготовке будущих prompt-файлов
используются пути `prompts/2026-09-21/place-catalog/<ID>-<topic>.md`; сам этот
план prompt-файлы не создаёт.

## 5. Последовательность и зависимости

Будущие карточки создаются только по отдельному запросу:

| ID | Файл внутри `prompts/2026-09-21/place-catalog/` | Статус |
|---|---|---|
| 1.1 | `01.1-contracts-and-normalization-code.md` | planned |
| 1.2 | `01.2-contracts-and-normalization-tests.md` | planned |
| 2.1 | `02.1-geonames-sqlite-builder-code.md` | planned |
| 2.2 | `02.2-geonames-sqlite-builder-tests.md` | planned |
| 3.1 | `03.1-sqlite-lifecycle-and-lookup-code.md` | planned |
| 3.2 | `03.2-sqlite-lifecycle-and-lookup-tests.md` | planned |
| 4.1 | `04.1-indexed-place-search-code.md` | planned |
| 4.2 | `04.2-indexed-place-search-tests.md` | planned |
| 5.1 | `05.1-place-catalog-end-to-end-tests.md` | planned |
| 5.2 | `05.2-place-catalog-closeout.md` | planned |

```text
1.1 contracts/normalizer code
  → 1.2 contracts/normalizer tests
  → 2.1 GeoNames SQLite builder code
  → 2.2 builder tests
  → 3.1 SQLite lifecycle/lookup code
  → 3.2 lifecycle/lookup tests
  → 4.1 indexed search code
  → 4.2 search tests
  → 5.1 end-to-end and boundary acceptance
  → 5.2 full verification and documentation closeout
```

Порядок обязателен. Builder и adapter должны использовать уже принятый объект
`normalize_place_query`; search строится поверх уже проверенных schema и
lifecycle; сквозной Build Natal выполняется только после готовности обоих
портов concrete-adapter.

## 6. Карточки промтов

### Промт 1.1 — contracts and canonical normalization — code

**Единственный результат:** в лёгком contract-модуле появляются search-типы и
одна pure-функция нормализации, пригодная и для runtime search, и для builder.

**Зависимости:** действующие `PlaceCatalog`/`LocalPlaceCatalog`; целевой
контракт §3–4 требований.

**Сделать:**

- добавить `PlaceSuggestion`, `PlaceSuggestions`, `InvalidPlaceQuery`,
  `PlaceSearchOutcome` и `PlaceSearch`;
- добавить `ALLOWED_ALTERNATE_LANGUAGES = frozenset({"ru"})`;
- реализовать `normalize_place_query(query) -> str | InvalidPlaceQuery` в
  порядке raw control check → NFKC → whitespace → casefold → `ё → е`;
- сохранить `PlaceSuggestions(items=())` отдельным успешным исходом;
- реэкспортировать `PlaceSearch`, `PlaceSuggestion`, `PlaceSuggestions` и
  `InvalidPlaceQuery` из `exact_orb.birth`;
- сохранить поведение существующего JSONL-adapter.

**Разрешено менять:**

- `src/exact_orb/birth/places.py`;
- `src/exact_orb/birth/__init__.py` только для четырёх перечисленных
  search-контрактов.

**Запрещено менять:** resolver/timezone, builder, SQLite-adapters, tests,
HTTP/application code. `birth/__init__.py` не импортирует concrete adapter и
не должен начать eager-загрузку `sqlite3`.

**Закрывает:** контрактную часть AC-S6, AC-S12 и основу AC-B6.

**Проверка готовности:** модуль компилируется; существующие
`tests/test_birth_places.py` и `tests/test_birth_resolver.py` проходят без
изменения.

### Промт 1.2 — contracts and normalization — tests

**Единственный результат:** тесты доказывают точный порядок нормализации,
валидационные исходы и immutable search-модели.

**Зависимости:** 1.1.

**Разрешено менять:**

- новый `tests/test_place_search_contracts.py`.

**Запрещено менять:** весь `src/**`, builder, существующие fixtures/goldens и
архитектурные тесты.

**Проверки:** NFKC, Unicode whitespace, регистр, `Ё/ё`, control characters,
пустая/длинная/непоисковая строка, непустой Unicode query, различие пустой
выдачи и invalid outcome, frozen/extra-forbid модели, публичные импорты четырёх
search-контрактов из `exact_orb.birth`.

**Закрывает:** AC-S6 в части нормализации и AC-S12.

### Промт 2.1 — deterministic GeoNames SQLite builder — code

**Единственный результат:** `scripts/build_place_catalog.py` создаёт
проверенный `places.sqlite` из трёх локальных GeoNames-файлов и больше не
производит production JSONL.

**Зависимости:** 1.1–1.2; установленный пакет (`pip install -e .`); локальная
`tzdata` dependency.

**Сделать:**

- реализовать потоковый порядок admin1 → cities → alternate names → SQLite;
- отбирать feature class/codes, страны, population и допустимые timezone;
- брать список IANA keys и версию из Python distribution `tzdata`, без
  системной timezone database для состава каталога;
- выбирать русские place/admin1 display names по singleton allow-list,
  current/preferred flags и `alternateNameId`;
- индексировать source, ASCII, текущие и исторические русские aliases;
- округлять координаты через `Decimal`/`ROUND_HALF_UP` и хранить целые сотые;
- создать versioned schema, metadata, индексы и foreign keys;
- использовать canonical normalizer из `exact_orb.birth.places`;
- создать минимальные текстовые GeoNames fixtures с обязательными случаями
  карточки 2.2 для ручного прогона builder;
- до фиксации schema одним локальным SQL-запросом на synthetic SQLite
  подтвердить, что она выражает все пять уровней ranking из §4.3 требований и
  дедупликацию по `place_id` до `LIMIT`, не реализуя runtime `search`;
- писать temp рядом с целью, валидировать, закрывать и выполнять `os.replace`;
- оставить прежний target неизменным при любом отказе;
- выдавать детерминированную статистику, включая отфильтрованные timezone.

**Разрешено менять:**

- `scripts/build_place_catalog.py`;
- новые data-only fixtures внутри `tests/fixtures/place_catalog/`.

**Запрещено менять:** runtime package, исполняемые test-файлы, существующий
JSONL fixture, golden-файлы, загружать данные по сети или автоматически
изменять `cities/`.

**Закрывает:** код для AC-P1–P4 и AC-P6–P10; builder-часть AC-B6.

**Проверка готовности:** `--help`, компиляция скрипта и небольшой локальный
ручной вызов на созданных synthetic-файлах завершаются успешно. В журнале
фиксируются команда и результат SQL-проверки ranking/dedup; runtime search и
исполняемые тесты в этой карточке отсутствуют.

### Промт 2.2 — builder determinism and data rules — tests

**Единственный результат:** synthetic GeoNames-данные доказывают правила
сборки и воспроизводимость SQLite-артефакта.

**Зависимости:** 2.1.

**Разрешено менять:**

- новый `tests/test_place_catalog_builder.py`.

**Запрещено менять:** `src/**`, builder, созданные в 2.1 fixtures, реальные
`cities/**`, JSONL/goldens. Если fixture обнаружен неверным, работа сначала
возвращается в 2.1; тестовая карточка не исправляет входные данные скрыто.

**Обязательные fixture-случаи:** `Москва`, `Məskeү`, второй non-preferred
русский вариант, псевдоязык, два равных preferred-кандидата, историческое имя,
admin1 GeoNames ID и русский регион, `Nowhere/Fake`, координаты на half-boundary,
места внутри/вне country/population filters.

**Проверки:** две сборки сравниваются логически через упорядоченные SELECT и
metadata; failure-before-replace сохраняет прежнюю цель; SQLite-файл не
сравнивается побайтно. AST-проверка builder запрещает локальное определение
`normalize_place_query`, а runtime-проверка подтверждает identity импортированного
builder-объекта и canonical normalizer из `exact_orb.birth.places`.

**Закрывает:** AC-P1–P4, AC-P6–P10 и builder-половину AC-B6.

### Промт 3.1 — SQLite lifecycle and lookup — code

**Единственный результат:** leaf-adapter открывает готовый каталог read-only,
валидирует startup, разрешает `place_id` и корректно закрывается.

**Зависимости:** 2.1–2.2 и зафиксированная builder schema.

**Сделать:**

- создать `SqlitePlaceCatalog.open(..., executor=...)`, `lookup` и `aclose`;
- использовать один внешний `ThreadPoolExecutor(max_workers=1)` и одно
  соединение с `check_same_thread=True` на его worker;
- открыть resolved `Path.as_uri()` через `mode=ro`, `uri=True`, без
  `immutable=1`;
- проверить schema version, metadata, tables, columns и required indexes;
- на mismatch `tzdata_version` написать одно компактное WARNING и продолжить;
- hard-fail startup при любом неразрешимом catalog `tz_id`;
- не преобразовывать `CancelledError`;
- возвращать fresh `ResolvedPlace`/`PlaceNotFound`, включая syntactically
  invalid IDs без SQL;
- обеспечить idempotent `aclose` и typed failure операций вне lifecycle.

**Разрешено менять:**

- новый `src/exact_orb/birth/adapters/__init__.py`;
- новый `src/exact_orb/birth/adapters/sqlite.py`.

**Запрещено менять:** `birth/__init__.py`, contracts, resolver, builder,
application/bootstrap, tests. `birth/adapters/__init__.py` не реэкспортирует
SQLite-модуль.

**Закрывает:** код для AC-P5, AC-P11, AC-L2, AC-L7, AC-B1–B5 и AC-B7.

**Проверка готовности:** новые модули компилируются; импорт `exact_orb.birth`
по ручной проверке не загружает `sqlite3`; существующие birth/module-boundary
тесты не регрессируют.

### Промт 3.2 — SQLite lifecycle and lookup — tests

**Единственный результат:** тесты подтверждают lifecycle, thread ownership,
startup validation, lookup и архитектурную изоляцию adapter.

**Зависимости:** 3.1.

**Разрешено менять:**

- новый `tests/test_place_catalog_sqlite.py`;
- `tests/test_module_boundaries.py`.

**Запрещено менять:** `src/**`, builder, builder tests/fixtures, session
boundary allow-lists в сторону ослабления.

**Проверки:** read-only path cases, отсутствующий файл, schema/metadata/index
drift, tzdata warning, unresolved timezone hard fail, worker thread,
cancellation, caller-owned executor, double close, before-open/after-close,
fresh results, unknown и pathological IDs, positive control прямого sqlite
import.

**Закрывает:** AC-P5, AC-P11, AC-L2, AC-L7, AC-B1–B5 и AC-B7; lifecycle-часть
AC-S10 и AC-S14.

### Промт 4.1 — indexed prefix search — code

**Единственный результат:** тот же `SqlitePlaceCatalog` реализует полный
`PlaceSearch` без изменения lookup/lifecycle.

**Зависимости:** 1.1–1.2 и 3.1–3.2.

**Сделать:**

- валидировать strict `limit` `1..20` до SQL;
- вызывать canonical `normalize_place_query` и возвращать invalid outcome без
  SQL;
- выполнять BINARY range query `lower <= search_key < upper`, без `LIKE`;
- агрегировать лучший rank по `place_id`, дедуплицировать до `LIMIT`;
- ранжировать exact/current preferred/current/historic, population и ID;
- возвращать immutable suggestions без координат и timezone;
- переводить только ожидаемые SQLite read failures в
  `PlaceCatalogUnavailableError` и пропускать cancellation.

**Разрешено менять:**

- `src/exact_orb/birth/adapters/sqlite.py`.

**Запрещено менять:** contracts, builder/schema, resolver, tests, HTTP/UI,
Orchestrator/ContextService.

**Закрывает:** код для AC-S1–S14 и AC-L1; adapter-часть AC-B6.

**Проверка готовности:** модуль компилируется, прежние lifecycle/lookup tests
проходят неизменёнными, ручной smoke на synthetic SQLite возвращает Москву.

### Промт 4.2 — indexed prefix search — tests

**Единственный результат:** тесты доказывают наблюдаемую search-семантику и
использование индекса.

**Зависимости:** 4.1.

**Разрешено менять:**

- новый `tests/test_place_catalog_search.py`;
- `tests/test_module_boundaries.py` только для AC-B6.

**Запрещено менять:** весь production-код, builder tests/fixtures, resolver и
application tests.

**Проверки:** Москва в трёх регистрах, Moscow, одноимённые места, historical
alias, стабильный ranking, dedup-before-limit, пустая выдача, invalid query без
SQL с позитивным query-counter control, `%/_/'`, invalid limits, EXPLAIN QUERY
PLAN, read failure, cancellation и отсутствие shared mutable result.

AST-проверка запрещает локальное определение normalizer в adapter; runtime-
проверка подтверждает identity canonical normalizer в contract-модуле,
builder и adapter. Builder-половина AST/identity уже доказана в 2.2 и здесь
включается в общую контрольную точку без дублирования её частных сценариев.

**Закрывает:** AC-S1–S14, AC-L1 и AC-B6.

### Промт 5.1 — end-to-end catalog acceptance — tests

**Единственный результат:** реальная цепочка builder → search → lookup →
`BirthDataResolver` и application flow подтверждена без изменения production.

**Зависимости:** 1.1–4.2.

**Разрешено менять:**

- новый `tests/application/test_place_catalog_integration.py`.

Существующие helpers переиспользуются без изменения. Если их недостаточно,
allowlist сначала явно ревизуется в этом плане; тестовый промт не расширяет
scope самостоятельно.

**Запрещено менять:** `src/**`, builder, ранее принятые tests, HTTP/UI,
production bootstrap ownership.

**Проверки:**

- `search("Москва") → "524901" → BirthDataResolver` для 02.09.1990 14:30
  даёт `utc_offset_seconds=14400` и `10:30Z`;
- неизвестный ID даёт `InputRequired {birth.place, INVALID}` без timezone,
  calculation и commit;
- runtime read failure даёт retryable resolution failure, не input failure;
- search вызывается напрямую и не затрагивает Orchestrator/ContextService;
- Build path с тем же catalog instance проходит существующую цепочку
  Orchestrator → Handler → Resolver;
- ID из каждой suggestion разрешается lookup того же выпуска.

**Закрывает:** AC-L1–L6 и сквозное подтверждение AC-P4.

### Промт 5.2 — regression, real-data smoke and documentation closeout

**Единственный результат:** вся ветка проверена, статусы документов отражают
фактическую реализацию, а оставшиеся ограничения названы без завышения статуса.

**Зависимости:** 5.1 и наличие всех трёх локальных GeoNames-файлов для
real-data smoke.

**Разрешено менять:**

- `docs/project_management/implementation_plans/place_catalog_implementation_plan.md`;
- `docs/requirements/component_responsibilities/exact-orb_place_catalog.md`;
- `docs/requirements/component_responsibilities/exact-orb_birth_data_resolution.md`;
- `docs/requirements/overview.md`;
- `docs/requirements/scenarios.md`;
- `docs/sequence_diagrams/place_catalog/README.md` и только изменившиеся
  place-catalog diagrams;
- `docs/project_management/roadmap.md`.

**Запрещено менять:** production/tests, исторические prompts, соседние ADR,
goldens, raw dumps и generated SQLite в Git.

**Проверки:** targeted suites → birth/application related suite → полный
`pytest`; `git diff --check`; Markdown links; PlantUML structural/render check
по доступности renderer; полный локальный build из `cities/` в ignored
`data/places.sqlite` и smoke Москвы. После первого успешного полного build в
журнале выполнения фиксируются SHA-256 трёх источников и точное число
импортированных мест; это число становится ожидаемым якорем для повторной
сборки из тех же файлов.

Если полный набор падает по внешней причине, документ фиксирует точную команду,
node IDs и границу влияния. Карточка не объявляет ветку готовой только по
targeted tests.

## 7. Матрица требований и владельцев

| Требования | Production-владелец | Test-владелец | Первая полная контрольная точка |
|---|---|---|---|
| AC-P1–P4 | 2.1 | 2.2; P4 дополнительно 5.1 | 2.2 / 5.1 |
| AC-P5 | 3.1 | 3.2 | 3.2 |
| AC-P6–P10 | 2.1 | 2.2 | 2.2 |
| AC-P11 | 3.1 | 3.2 | 3.2 |
| AC-S1–S5 | 4.1 | 4.2 | 4.2 |
| AC-S6 | 1.1 + 4.1 | 1.2 + 4.2 | 4.2 |
| AC-S7–S11 | 4.1 | 4.2 | 4.2 |
| AC-S12 | 1.1 + 4.1 | 1.2 + 4.2 | 4.2 |
| AC-S13–S14 | 4.1 | 4.2 | 4.2 |
| AC-L1 | 4.1 | 4.2 + 5.1 | 5.1 |
| AC-L2 | 3.1 | 3.2 | 3.2 |
| AC-L3–L4 | существующий resolver + 2.1/3.1/4.1 | 5.1 | 5.1 |
| AC-L5 | 3.1 + существующий resolver | 3.2 + 5.1 | 5.1 |
| AC-L6 | существующий application flow | 5.1 | 5.1 |
| AC-L7 | 3.1 | 3.2 | 3.2 |
| AC-B1–B5 | 3.1 | 3.2 | 3.2 |
| AC-B6 | 1.1 + 2.1 + 4.1 | 2.2 (builder) + 4.2 (adapter и общая identity) | 2.2 / 4.2 |
| AC-B7 | 3.1 | 3.2 | 3.2 |

Ни один AC не переносится в M1-6. M1-6 потребляет готовые порты и отвечает за
HTTP mapping/lifespan wiring; browser autocomplete остаётся M1-7.

## 8. Команды проверки по этапам

Команды уточняются по фактическим именам файлов, но порядок сохраняется:

```text
# После 1.2
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py -q

# После 2.2
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_builder.py -q

# После 3.2
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_sqlite.py tests/test_module_boundaries.py tests/test_birth_places.py tests/test_birth_resolver.py -q

# После 4.2
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_place_catalog_builder.py tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py tests/test_module_boundaries.py -q

# После 5.1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_place_catalog_integration.py tests/application tests/test_birth_resolver.py tests/test_birth_tz.py -q

# Финал
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
git diff --check
```

Timeout в concurrency/cancellation tests служит только защитой от зависания.
Порядок доказывается `asyncio.Event`, barrier и наблюдаемым worker identity;
`sleep` и реальные задержки запрещены.

## 9. Общие запреты ветки

- Не добавлять FastAPI, middleware, UI, debounce или rate limit.
- Не добавлять RemoteGeocoder, сеть, автоматическое скачивание GeoNames или
  background refresh.
- Не передавать свободный текст, координаты или timezone с клиента в Build.
- Не хранить `utc_offset_seconds` в каталоге.
- Не добавлять `sqlite3` в eager import `exact_orb.birth`.
- Не использовать `asyncio.to_thread`, global executor,
  `check_same_thread=False`, `LIKE` для Unicode prefix или `immutable=1`.
- Не менять JSONL fixture, calculation keys, golden-файлы и timezone resolver.
- Не ослаблять `tests/test_module_boundaries.py` ради нового adapter.
- Не включать raw dumps, ZIP или generated SQLite в Git.
- Не исправлять соседние замечания и не создавать общий DI/repository layer.

## 10. Готовность к старту и Definition of Done

### 10.1. Готовность первой карточки

- Ветка — `feat/place-catalog`.
- Текущие requirements/diagrams доступны в рабочем дереве.
- Существующие birth tests проходят либо известен их точный исходный отказ.
- Unrelated modified/untracked files перечислены и не включаются в scope.

Карточка 2.1 дополнительно требует установленного editable package и `tzdata`.
Карточка 5.2 требует локальных `cities1000.txt`, `admin1CodesASCII.txt` и
`alternateNamesV2.txt`.

### 10.2. Definition of Done ветки

- Все десять карточек выполнены в указанном порядке.
- Все AC-P1–P11, AC-S1–S14, AC-L1–L7 и AC-B1–B7 имеют прошедшее evidence.
- Targeted, related и полный pytest фактически запускались, результаты записаны.
- Полный local-data build и Москва smoke прошли без добавления артефакта в Git.
- Актуальные requirements, scenarios, diagrams, overview и roadmap отражают
  реализованный статус, а M1-6/M1-7 остаются target/deferred.
- `git diff --check` и проверки ссылок/диаграмм прошли.
- Не осталось скрытых решений по schema, timezone, ranking, lifecycle или
  ownership executor.

## 11. Журнал выполнения

До исполнения карточек раздел остаётся пустым. Каждая выполненная карточка
добавляет дату, фактические файлы, команды, результаты, отклонения от плана и
оставшиеся зависимости. Статус не повышается по факту написания кода или
наличия тестового файла: требуется исполненное наблюдаемое evidence.
