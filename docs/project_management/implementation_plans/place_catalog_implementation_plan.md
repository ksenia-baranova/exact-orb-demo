# Каталог мест — план реализации и карточки промтов

**Дата исходной сверки:** 2026-09-21.

**Статус:** выполняется; карточки 1.1–4.2 реализованы и проверены в границах
своих этапов. SQLite builder, lifecycle/lookup adapter, индексированный search
и его исполняемая приёмка готовы. Карточки 5.1–5.2 не выполнялись.

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
отдельного указания пользователя. Исходный путь prompt-файлов —
`prompts/2026-09-21/place-catalog/<ID>-<topic>.md`; выполненные 22 сентября
карточки 2.1–3.1 находятся в текущей папке `prompts/2026-09-22/`. Сам этот план
prompt-файлы не создаёт.

## 5. Последовательность и зависимости

Будущие карточки создаются только по отдельному запросу:

| ID | Prompt-файл | Статус |
|---|---|---|
| 1.1 | `prompts/2026-09-21/place-catalog/01.1-contracts-and-normalization-code.md` | выполнено 2026-09-21; code, существующая регрессия пройдена |
| 1.2 | `prompts/2026-09-21/place-catalog/01.2-contracts-and-normalization-tests.md` | выполнено 2026-09-22; 30 targeted, полный pytest пройден |
| 2.1 | `prompts/2026-09-22/place-catalog/02.1-geonames-sqlite-builder-code.md` | выполнено 2026-09-22; synthetic build/schema smoke, полный pytest пройден |
| 2.2 | `prompts/2026-09-22/place-catalog/02.2-geonames-sqlite-builder-tests.md` | выполнено 2026-09-22; 10 targeted, связанный и полный pytest пройдены |
| 3.1 | `prompts/2026-09-22/place-catalog/03.1-sqlite-lifecycle-and-lookup-code.md` | выполнено 2026-09-22; lifecycle/lookup smoke, полный pytest пройден |
| 3.2 | `prompts/2026-09-22/place-catalog/03.2-sqlite-lifecycle-and-lookup-tests.md` | выполнено 2026-09-22; 26 targeted, связанный и полный pytest пройдены |
| 4.1 | `prompts/2026-09-22/place-catalog/04.1-indexed-place-search-code.md` | выполнено 2026-09-22; indexed search smoke, существующая и полная регрессия пройдены |
| 4.2 | `prompts/2026-09-22/place-catalog/04.2-indexed-place-search-tests.md` | выполнено 2026-09-22; 16 targeted, связанный и полный pytest пройдены |
| 5.1 | `prompts/2026-09-21/place-catalog/05.1-place-catalog-end-to-end-tests.md` | planned |
| 5.2 | `prompts/2026-09-21/place-catalog/05.2-place-catalog-closeout.md` | planned |

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

Каждая выполненная карточка добавляет дату, фактические файлы, команды,
результаты, отклонения от плана и оставшиеся зависимости. Статус не повышается
по факту написания кода или наличия тестового файла: требуется исполненное
наблюдаемое evidence.

### 11.1. Карточка 1.1 — 2026-09-21

**Результат:** создан и выполнен
[промт 1.1](../../../prompts/2026-09-21/place-catalog/01.1-contracts-and-normalization-code.md).
Добавлены immutable search-модели, `PlaceSearch`, alias исходов, singleton
allow-list `{"ru"}` и единственная pure-функция `normalize_place_query`.
Нормализация проверяет raw Unicode `Cc` до преобразований, затем выполняет
NFKC → whitespace → casefold → `ё → е`; пустота, предел 200 code points и
наличие букв/цифр проверяются на готовом ключе. Пустая выдача остаётся
успешным исходом. Четыре search-контракта доступны из `exact_orb.birth`.

**Фактические файлы:**

- `src/exact_orb/birth/places.py`;
- `src/exact_orb/birth/__init__.py` — только четыре новых реэкспорта;
- `prompts/2026-09-21/place-catalog/01.1-contracts-and-normalization-code.md`;
- этот план — статус 1.1 и журнал выполнения.

**Исходная готовность:** ветка `feat/place-catalog`; requirements и diagrams
присутствуют и уже отслеживаются Git. До изменения кода целевые тесты дали
`41 passed in 0.41s`.

Существовавшие до начала работы untracked-пути сохранены без изменений:

```text
Claude outputs/
_local/
docs/architecture/deployment.md
prompts/2026-08-22/10-data-selector.md
prompts/2026-08-22/10-include-gates-computation.md
prompts/2026-08-22/11-include-gates-computation-tests.md
prompts/2026-08-26/
prompts/2026-08-27/05-run-id-correlation.md
prompts/2026-09-04/
prompts/2026-09-06/03-research-corpus-fixes.md
prompts/2026-09-08/00-build-natal-handler-plan-decisions.md
prompts/2026-09-08/05-align-build-natal-docs.md
prompts/2026-09-09/02-align-build-natal-documentation.md
```

**Фактические проверки после изменения кода:**

```powershell
.\.venv\Scripts\python.exe -B -m compileall -q src/exact_orb/birth/places.py src/exact_orb/birth/__init__.py
# exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_birth_places.py tests/test_birth_resolver.py -q
# 41 passed in 0.35s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_birth_tz.py tests/test_module_boundaries.py tests/application -q
# 1003 passed in 29.53s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2448 passed in 113.09s (0:01:53)

.\.venv\Scripts\python.exe -B -c 'import sys; from exact_orb.birth import PlaceSearch, PlaceSuggestion, PlaceSuggestions, InvalidPlaceQuery; assert "sqlite3" not in sys.modules; print("Four public imports OK; sqlite3 not loaded")'
# Four public imports OK; sqlite3 not loaded

.\.venv\Scripts\python.exe -B -c 'import re; from pathlib import Path; p = Path("prompts/2026-09-21/place-catalog/01.1-contracts-and-normalization-code.md"); links = re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")); missing = [link for link in links if not (p.parent / link.split("#", 1)[0]).exists()]; print({"links": len(links), "missing": missing}); assert not missing'
# {'links': 8, 'missing': []}

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** production-scope карточки соблюдён; JSONL, resolver,
timezone, builder, adapters и tests не изменены. Новые тесты не создавались;
специализированное покрытие normalizer и immutable моделей остаётся 1.2.
Контрактная часть AC-S6/AC-S12 реализована, основа AC-B6 добавлена; полная
приёмка этих AC требует последующих test-карточек. SQLite search, builder и
сквозной каталог ещё не реализованы и здесь не проверялись. Общая актуализация
статусов requirements/diagrams остаётся 5.2. Commit, push и PR не выполнялись.

### 11.2. Карточка 1.2 — 2026-09-22

**Результат:** создан и выполнен
[промт 1.2](../../../prompts/2026-09-21/place-catalog/01.2-contracts-and-normalization-tests.md).
Новый test-модуль закрепляет NFKC, Unicode whitespace, casefold, `Ё/ё`,
непустые Unicode-названия и границу 200 code points. Перекрывающиеся случаи
доказывают порядок raw `Cc` → normalization → `EMPTY` → `TOO_LONG` →
`NO_SEARCHABLE_CHARACTERS`, включая увеличение длины после NFKC.

Для search-моделей проверены точные поля, tuple выдачи, четыре допустимых кода,
Pydantic `frozen_instance`, `extra_forbidden` и `literal_error`. Пустой
`PlaceSuggestions` доказан как успешный исход, отличный от
`InvalidPlaceQuery`; четыре публичных реэкспорта сверены по identity, а
language allow-list закреплён как `frozenset({"ru"})`.

**Фактические файлы:**

- `tests/test_place_search_contracts.py` — единственное изменение
  исполняемого кода;
- `prompts/2026-09-21/place-catalog/01.2-contracts-and-normalization-tests.md`;
- этот план — статус 1.2 и журнал выполнения.

**Исходная готовность:** ветка `feat/place-catalog`, HEAD `840daaa` с
реализацией 1.1. До добавления тестов существующая birth-регрессия дала
`41 passed in 0.44s`. Посторонние untracked-пути, перечисленные в §11.1,
оставлены без изменений.

**Фактические проверки после добавления тестов:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py -q
# 30 passed in 0.22s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py -q
# 71 passed in 0.44s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_birth_tz.py tests/test_module_boundaries.py tests/application -q
# 1003 passed in 11.36s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2478 passed in 43.04s

git diff --check
# exit code 0; ошибок whitespace нет
```

PowerShell-проверка относительных Markdown-ссылок обоих актуальных документов
нашла 17 ссылок и 0 отсутствующих целей. Отдельная проверка трёх изменённых
файлов не нашла trailing whitespace.

**Границы результата:** `src/**`, builder, adapters, существующие tests,
fixtures/goldens и архитектурные проверки не изменены. Отклонений от карточки
нет. AC-S6 закрыт в части pure-нормализации, AC-S12 — на уровне контрактных
исходов. Доказательство отсутствия SQL для invalid query остаётся 4.2; builder,
SQLite lifecycle/search и сквозная интеграция остаются карточкам 2.1–5.1.
Общий documentation closeout остаётся 5.2. Commit, push и PR не выполнялись.

### 11.3. Карточка 2.1 — 2026-09-22

**Результат:** создан и выполнен
[промт 2.1](../../../prompts/2026-09-22/place-catalog/02.1-geonames-sqlite-builder-code.md).
`scripts/build_place_catalog.py` больше не создаёт production JSONL: builder
обязательными потоковыми проходами читает admin1 → cities → alternate names,
фильтрует данные и атомарно публикует проверенный SQLite schema v1.

IANA keys прочитаны из `tzdata/zones`, версия `2026.3` — через metadata Python
distribution; системная timezone database не используется. Координаты
округляются `Decimal/ROUND_HALF_UP` и хранятся целыми сотыми. Русские place и
admin1 names выбираются по current/preferred и минимальному числовому
`alternateNameId`; source, ASCII, текущие и исторические русские aliases
нормализуются объектом из `exact_orb.birth.places`.

Schema содержит `places`, `place_names`, singleton `catalog_metadata`,
`user_version=1`, foreign keys и индексы `idx_place_names_search_key` с BINARY
collation и `idx_place_names_place_id`. Metadata состоит из канонического JSON
с SHA-256 трёх входов и фактическими build parameters без времени, mtime и
путей. Перед `os.replace` builder выполняет integrity/foreign-key/schema/index/
metadata/count/timezone validation и закрывает connection.

**Фактические файлы:**

- `scripts/build_place_catalog.py`;
- `tests/fixtures/place_catalog/cities1000.txt`;
- `tests/fixtures/place_catalog/admin1CodesASCII.txt`;
- `tests/fixtures/place_catalog/alternateNamesV2.txt`;
- `prompts/2026-09-22/place-catalog/02.1-geonames-sqlite-builder-code.md`;
- этот план — путь prompt, статус 2.1 и журнал выполнения.

**Исходная готовность:** ветка `feat/place-catalog`, HEAD `947c106` с
карточками 1.1–1.2. Установлен editable package и `tzdata 2026.3`; локально
доступны все три обязательных real-data источника. Посторонние untracked-пути
из §11.1 сохранены без изменений. По явному указанию владельца prompt 2.1
создан в папке с текущей датой 22 сентября, а не в исходной папке плана.

**Synthetic fixtures:** 4 admin1 строки, 10 city строк и 15 alternate-name
строк. Admin1/cities содержат `4/19` колонок; alternate names логически имеют
10 колонок, но пустые конечные `from/to` опущены (`8/10` физических колонок),
чтобы не хранить trailing tabs. Набор содержит
Москву, `Məskeү`, два preferred и non-preferred русские имена, псевдоязык,
исторические варианты по flag и `to`, русские admin1, `Nowhere/Fake`,
half-boundary, population/country filters, PPLX, другой feature class и пустую
timezone.

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B scripts/build_place_catalog.py --help
# exit code 0; обязательны --cities, --admin1, --alternate-names, --out

.\.venv\Scripts\python.exe -B -m py_compile scripts/build_place_catalog.py
# exit code 0

.\.venv\Scripts\python.exe -B scripts/build_place_catalog.py --cities tests/fixtures/place_catalog/cities1000.txt --admin1 tests/fixtures/place_catalog/admin1CodesASCII.txt --alternate-names tests/fixtures/place_catalog/alternateNamesV2.txt --out logs/place-catalog-card-2.1/places.sqlite
# 4 admin1, 10 cities, 15 alternate names; 5 places, 13 names
# filtered: language=2, population=1, feature class=1, feature code=1,
# timezone=2; rejected_names=1

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py -q
# 71 passed in 0.42s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2478 passed in 110.75s
```

Read-only SQL smoke подтвердил три таблицы и два обязательных индекса. Москва
получила `display_name="Москва"`, `admin1_name="Москва"`, координаты
`5575/3762` и `Europe/Moscow`; `Məskeү`, псевдоязык и `###@@@` не попали в
индекс. Half-boundary дала `1235/-4568`. `Nowhere/Fake`, пустая timezone,
PPLX, другой feature class и место ниже внешнего population threshold
отсутствуют. Две независимые сборки логически совпали: `[5, 13, 1]` строк в
`places/place_names/catalog_metadata`.

Failure-smoke с отсутствующим `alternate-names` завершился кодом `1` и сохранил
прежний target с тем же SHA-256
`6DE7C18BC2194574B6F95851EF27FC1CBEA15B15E04AF8822A8845E866935CE0`.
Ручная identity-проверка подтвердила, что builder использует именно canonical
`normalize_place_query` и `ALLOWED_ALTERNATE_LANGUAGES` из contract-модуля.

**Ranking/dedup schema check:** в in-memory SQLite через `_create_schema` были
вставлены семь совпадающих aliases для шести place IDs. Один параметризованный
range query вычислил лучший alias rank через `GROUP BY place_id`, затем применил
`ORDER BY rank, population DESC, place_id` и только после этого `LIMIT 6`.
Фактический результат:

```text
place_ids = ["1", "2", "3", "5", "6", "4"]
rows = [["1",3,100], ["2",4,100000], ["3",6,900],
        ["5",6,500], ["6",6,500], ["4",7,999999]]
unique_place_ids = 6
```

Он подтверждает exact → current preferred → current перед historic →
population DESC → ID tie-breaker и дедупликацию до limit без реализации
runtime `search`.

**Границы результата:** `src/**`, исполняемые tests, существующий JSONL,
goldens, requirements/ADR/diagrams и `cities/` не изменены. Generated SQLite
находится только в ignored `logs/` и не включается в Git. Полный 785-MB
real-data build не запускался: он принадлежит 5.2. Исполняемая приёмка AC-P1–P4
и AC-P6–P10 остаётся 2.2; startup validation AC-P5/P11 — 3.x, runtime search —
4.x. Commit, push и PR не выполнялись.

### 11.4. Карточка 2.2 — 2026-09-22

**Результат:** создан и выполнен
[промт 2.2](../../../prompts/2026-09-22/place-catalog/02.2-geonames-sqlite-builder-tests.md).
Новый `tests/test_place_catalog_builder.py` добавляет исполняемую synthetic-
приёмку builder карточки 2.1, не меняя production-код и data fixtures.

Десять тестовых сценариев используют настоящий `build()`/`main()`, SQLite и
три GeoNames fixtures. Они подтверждают:

- положительное наличие всех обязательных fixture-случаев до отрицательных
  утверждений о фильтрации;
- статистику `4/10/15` прочитанных строк, 5 places, 13 names и точные счётчики
  каждой причины фильтрации;
- итоговые IDs `498817`, `524901`, `900001`, `900003`, `900005`, московские
  display/admin1 names, `5575/3762`, half-boundary `1235/-4568`, внешний
  population threshold и full-country inclusion;
- отбрасывание `Məskeү`, псевдоязыка, invalid normalized name,
  `Nowhere/Fake`, пустой timezone, PPLX, другого feature class и места ниже
  внешнего population threshold;
- выбор минимального числового `alternateNameId`, current/historic semantics,
  русский admin1 по GeoNames ID и ASCII fallback;
- schema/user version, integrity/foreign keys, обязательные индексы с BINARY
  collation, canonical metadata, SHA-256 fixtures и `tzdata_version` project
  `.venv`;
- логическое равенство двух независимых сборок через упорядоченные SELECT без
  побайтового сравнения SQLite-файлов;
- обязательность каждого из трёх inputs и сохранение прежней цели при
  управляемом отказе `os.replace` после полной валидации временной базы;
- AST import canonical normalizer/allow-list без локальной копии и runtime
  identity обоих объектов с `exact_orb.birth.places`;
- exit code и фиксированный порядок CLI JSON-статистики.

В failure-сценарии fault injection ограничен leaf seam `os.replace`: parsing,
SQLite, schema validation и сам `build()` выполняются реально. Временный файл
создаётся рядом с target, доступен как валидный закрытый SQLite перед
публикацией и удаляется после отказа; прежние bytes target сохраняются.

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_builder.py -q
# 10 passed in 0.33s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_builder.py tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py tests/test_module_boundaries.py -q
# 117 passed in 3.33s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2488 passed in 106.43s

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** `src/**`, builder, fixtures, существующие tests,
реальные `cities/**`, JSONL/goldens, requirements/ADR/diagrams и зависимости
не изменены. Полный real-data build не запускался. Карточка даёт исполняемые
доказательства AC-P1–P4, AC-P6–P10 и builder-половины AC-B6. Startup validation
AC-P5/P11 остаётся 3.x, runtime search — 4.x. Commit, push и PR не выполнялись.

### 11.5. Карточка 3.1 — 2026-09-22

**Результат:** создан и выполнен
[промт 3.1](../../../prompts/2026-09-22/place-catalog/03.1-sqlite-lifecycle-and-lookup-code.md).
Добавлен leaf-adapter `exact_orb.birth.adapters.sqlite.SqlitePlaceCatalog` и
пустой package boundary `exact_orb.birth.adapters` без реэкспорта concrete
adapter.

`open()` принимает только file-backed path и внешний
`ThreadPoolExecutor(max_workers=1)`. На worker выполняются
`Path.resolve(strict=True)`, `Path.as_uri()`, read-only SQLite open через
`mode=ro`, schema/metadata/index validation, сравнение версии `tzdata` и
проверка всех distinct timezone эффективным runtime `ZoneInfo`. Adapter не
создаёт и не завершает executor, не использует `asyncio.to_thread`,
`check_same_thread=False`, `immutable=1` или write connection.

Startup validation фиксирует schema v1: точные обязательные колонки трёх
таблиц, оба индекса и BINARY search key, singleton metadata, три lowercase
SHA-256 и shape build parameters. Mismatch версии пишет ровно одно событие
`place_catalog_tzdata_version_mismatch` уровня WARNING с catalog/runtime
версиями и не останавливает startup; неразрешимая timezone останавливает.

`lookup()` проверяет lifecycle и Python-type, возвращает pathological string
IDs как fresh `PlaceNotFound` без SQL, а допустимый ID разрешает одним
параметризованным exact query на worker. `ResolvedPlace.canonical_name`
получает `display_name`, координаты переводятся из целых сотых. Технические
отказы становятся `PlaceCatalogUnavailableError`; `CancelledError` не
преобразуется. `aclose()` идемпотентен, разделяет один close future между
повторными вызовами и завершает начатое закрытие перед распространением
cancellation.

**Фактические файлы:**

- `src/exact_orb/birth/adapters/__init__.py`;
- `src/exact_orb/birth/adapters/sqlite.py`;
- `prompts/2026-09-22/place-catalog/03.1-sqlite-lifecycle-and-lookup-code.md`;
- этот план — путь/status 3.1 и журнал выполнения.

**Ручной synthetic smoke:** builder создал ignored
`logs/place-catalog-card-3.1/places.sqlite` из 4 admin1, 10 cities и 15
alternate-name строк: 5 places и 13 names. На реальном executor adapter вернул
для `524901` новую модель Москвы `55.75/37.62`, `Europe/Moscow`; повторный
lookup дал равную, но не тождественную модель. Unknown, non-numeric ID и
строка длиной 10 000 дали `PlaceNotFound`; lookup до open и после двойного
close дал typed unavailable.

Отдельные копии базы подтвердили:

```text
schema_drift typed_unavailable _CatalogValidationError
bad_timezone typed_unavailable _CatalogValidationError
version_mismatch_warning WARNING 0.invalid 2026.3
```

Три изолированных import-smoke дали:

```text
import exact_orb.birth                  -> sqlite3_loaded=False
import exact_orb.birth.adapters         -> sqlite3_loaded=False; no re-export
import exact_orb.birth.adapters.sqlite  -> sqlite3_loaded=True
```

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B -m py_compile src/exact_orb/birth/adapters/__init__.py src/exact_orb/birth/adapters/sqlite.py
# exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_builder.py tests/test_place_search_contracts.py tests/test_birth_places.py tests/test_birth_resolver.py tests/test_module_boundaries.py -q
# 117 passed in 3.42s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2488 passed in 108.57s

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** `exact_orb.birth.__init__`, contracts, resolver,
builder, fixtures, tests, application/bootstrap, dependencies,
requirements/ADR/diagrams и реальные `cities/**` не изменены. `search()` и
ranking SQL не добавлялись; они остаются 4.1. Исполняемая приёмка lifecycle,
thread ownership, startup drift, cancellation и path cases остаётся 3.2.
Production composition остаётся M1-6. Commit, push и PR не выполнялись.

### 11.6. Карточка 3.2 — 2026-09-22

**Результат:** создан и выполнен
[промт 3.2](../../../prompts/2026-09-22/place-catalog/03.2-sqlite-lifecycle-and-lookup-tests.md).
Новый `tests/test_place_catalog_sqlite.py` добавляет 26 тестовых сценариев для
готового adapter 3.1 на реальной временной schema v1 базе из существующих
synthetic fixtures; production-код не изменён.

Проверки подтверждают:

- read-only URI через `Path.as_uri()` для Windows-пути с пробелом, Unicode и
  `#`, точные `mode=ro`, `uri=True`, `check_same_thread=True`, отсутствие
  `immutable=1`, включённый `PRAGMA query_only` и фактический запрет записи;
- открытие, lookup и close на одном injected single worker вне event-loop
  thread; executor остаётся рабочим после close и завершается только
  владельцем;
- unopened/closed lifecycle, единственный close при конкурентных вызовах и
  отсутствие SQL для invalid IDs и non-string Python-contract violation;
- точную модель Москвы, fresh положительные и отрицательные outcomes,
  неизвестный допустимый ID и pathological IDs длиной 10 000/Unicode/
  non-ASCII;
- typed open failure для отсутствующего файла, каталога и malformed SQLite
  без создания или удержания файла;
- hard failure при drift `user_version`, колонок, обязательного индекса,
  JSON/shape/cardinality metadata и при пустой/неразрешимой timezone;
- ровно один structured WARNING при несовпадении `tzdata_version` с успешным
  startup для разрешимых зон;
- typed runtime failure после startup и прямое распространение cancellation
  из open/lookup/close, включая завершённый cleanup соединения;
- AST/runtime identity canonical `normalize_place_query`.

`tests/test_module_boundaries.py` дополнен отдельными birth-adapter
инвариантами. AST проверяет полный набор adapter-файлов, project allow-list,
запрещённые зависимости и отсутствие реэкспорта concrete adapter. Два
изолированных process probes доказывают, что лёгкие birth imports не загружают
`sqlite3`, а прямой импорт `exact_orb.birth.adapters.sqlite` загружает его и
предоставляет `SqlitePlaceCatalog` как положительный контроль. Существующие
session allow-lists не менялись.

**Фактические файлы:**

- `tests/test_place_catalog_sqlite.py`;
- `tests/test_module_boundaries.py`;
- `prompts/2026-09-22/place-catalog/03.2-sqlite-lifecycle-and-lookup-tests.md`;
- этот план — путь/status 3.2 и журнал выполнения.

**Исходная готовность:** ветка `feat/place-catalog`, HEAD `36d3e5e` с
реализацией 3.1. Посторонние untracked-пути из §11.1 сохранены без изменений.
Первый запуск targeted pytest внутри restricted sandbox не получил доступ к
системному `%TEMP%`; это был environment setup error до выполнения зависящих
от `tmp_path` сценариев. Та же команда вне файлового ограничения выполнила все
тесты успешно.

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B -m py_compile tests/test_place_catalog_sqlite.py tests/test_module_boundaries.py
# exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_sqlite.py -q
# 26 passed in 0.53s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_sqlite.py tests/test_module_boundaries.py tests/test_birth_places.py tests/test_birth_resolver.py -q
# 109 passed in 4.01s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2520 passed in 113.55s (0:01:53)

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** `src/**`, builder, builder tests/fixtures, contracts,
requirements/ADR/diagrams, application/bootstrap и зависимости не изменены.
Новых дефектов production-кода 3.1 тесты не обнаружили. Карточка даёт
исполняемые доказательства AC-P5, AC-P11, AC-L2, AC-L7, AC-B1–B5 и AC-B7,
lookup/lifecycle-части AC-S10/AC-S14 и adapter-половины AC-B6. Индексированный
search остаётся 4.1–4.2, сквозной resolver/application — 5.1, общий closeout —
5.2. Commit, push и PR не выполнялись.

### 11.7. Карточка 4.1 — 2026-09-22

**Результат:** создан и выполнен
[промт 4.1](../../../prompts/2026-09-22/place-catalog/04.1-indexed-place-search-code.md).
Существующий leaf-adapter `SqlitePlaceCatalog` теперь реализует полный
`PlaceSearch` поверх того же read-only connection и caller-owned single-worker
executor, не изменяя lookup и lifecycle.

`search()` отклоняет non-string query и strict limit вне `1..20` до worker,
проверяет открытый lifecycle и вызывает canonical `normalize_place_query`.
`InvalidPlaceQuery` возвращается без SQL. Для валидного ключа adapter выполняет
один параметризованный BINARY range query
`lower <= search_key < lower + U+10FFFF` через
`idx_place_names_search_key`; `LIKE` и интерполяция пользовательского ввода не
используются.

CTE сначала вычисляет минимальный rank для каждого `place_id`: exact → current
preferred → current → historical. После `GROUP BY place_id` результат
присоединяется к `places`, сортируется по rank, population DESC и place ID;
параметризованный `LIMIT` применяется только после дедупликации. Наружу
возвращаются fresh immutable `PlaceSuggestions`/`PlaceSuggestion` с
`place_id`, canonical `display_name`, `admin1_name` и `country_code`, без
координат, timezone, population и matched alias. Технические отказы worker
становятся `PlaceCatalogUnavailableError`, cancellation распространяется без
преобразования.

**Фактические файлы:**

- `src/exact_orb/birth/adapters/sqlite.py`;
- `prompts/2026-09-22/place-catalog/04.1-indexed-place-search-code.md`;
- этот план — путь/status 4.1 и журнал выполнения.

**Исходная готовность:** ветка `feat/place-catalog`, HEAD `024be68` с
реализацией и тестами карточек 1.1–3.2. Посторонние untracked-пути из §11.1
сохранены без изменений. Tests/fixtures, contracts, builder и schema в
code-карточке не менялись.

**Ручной synthetic smoke:** использован catalog
`logs/place-catalog-card-3.1/places.sqlite`, собранный из принятых fixtures.
На реальном executor один экземпляр adapter дал:

```text
Москва / москва / МОСКВА / Moscow / Моск -> [524901]
Санкт -> [498817]
Ленинград -> [498817]
Несуществующий город -> PlaceSuggestions(items=())
###@@@ -> InvalidPlaceQuery(NO_SEARCHABLE_CHARACTERS), без worker submission
limit 0 / 21 / True -> ValueError, без worker submission
мос% / мос_ / SQL-like apostrophe input -> пустой успешный outcome
```

Повторный `search("Москва")` вернул равные, но не тождественные outcome/item
модели; выданный `524901` успешно разрешился прежним `lookup()`. Query plan
подтвердил:

```text
SEARCH place_names USING INDEX idx_place_names_search_key
    (search_key>? AND search_key<?)
```

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B -m py_compile src/exact_orb/birth/adapters/sqlite.py
# exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_sqlite.py tests/test_place_search_contracts.py tests/test_place_catalog_builder.py tests/test_module_boundaries.py tests/test_birth_places.py tests/test_birth_resolver.py -q
# 149 passed in 4.92s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2520 passed in 117.82s (0:01:57)

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** contracts и public re-exports, builder/schema/indexes,
resolver, tests/fixtures, application/bootstrap, requirements/ADR/diagrams,
dependencies и HTTP/UI не изменены. Сетевой fallback, fuzzy/substring search,
hot reload, write mode и новый executor не добавлялись. Карточка предоставляет
production-код для AC-S1–S14 и AC-L1, а также adapter-часть AC-B6; их полная
исполняемая приёмка принадлежит 4.2. Сквозной resolver/application остаётся
5.1, production composition и HTTP endpoint — M1-6. Commit, push и PR не
выполнялись.

### 11.8. Карточка 4.2 — 2026-09-22

**Результат:** создан и выполнен
[промт 4.2](../../../prompts/2026-09-22/place-catalog/04.2-indexed-place-search-tests.md).
Новый `tests/test_place_catalog_search.py` добавляет 16 исполняемых test nodes
для production search карточки 4.1. Тесты используют настоящий builder,
schema v1, `SqlitePlaceCatalog` и single-worker executor; production-код,
builder и fixtures не изменены.

Synthetic catalog подтверждает `Москва`/`москва`/`МОСКВА`/`Moscow`, prefix
`Моск`, current `Санкт` и historical `Ленинград`. Подсказка всегда содержит
canonical `display_name`, регион и страну из `places`, не раскрывает
координаты/timezone/population/matched alias, а каждый найденный ID успешно
разрешается `lookup()` того же экземпляра.

Управляемые строки в копиях готовой базы доказывают:

- exact → current preferred → current → historical;
- population DESC внутри rank и стабильный `place_id` tie-breaker;
- различимость одноимённых мест через `admin1_name` и `country_code`;
- дедупликацию нескольких aliases до `LIMIT`;
- default `limit=10` и разрешённые границы `1`/`20`.

Submission counter фиксирует отсутствие worker/SQL для всех четырёх
`InvalidPlaceQuery`, non-string query и invalid limits, а валидный неизвестный
query служит позитивным контролем SQL и возвращает пустой
`PlaceSuggestions`. `%`, `_` и apostrophe/SQL-like текст остаются обычными
символами и не получают wildcard или исполняемую семантику.

Тест query plan устанавливает trace callback на owning worker, захватывает
фактически исполненный production statement и запускает `EXPLAIN QUERY PLAN`
для него без копирования SQL из adapter. Наблюдаемое evidence:

```text
COLLATE BINARY
search_key >= lower AND search_key < upper
no LIKE
SEARCH place_names USING INDEX idx_place_names_search_key
```

Отдельно подтверждены search вне event-loop thread, typed failure до open/
после close и при реальном read failure, прямое распространение cancellation,
корректное последующее закрытие и fresh модели при конкурентных search/lookup.

**Фактические файлы:**

- `tests/test_place_catalog_search.py`;
- `prompts/2026-09-22/place-catalog/04.2-indexed-place-search-tests.md`;
- этот план — путь/status 4.2 и журнал выполнения.

`tests/test_module_boundaries.py` не изменялся: AC-B6 уже имеет adapter
allow-list/import boundary, а AST/runtime identity canonical normalizer
проверяются принятыми `tests/test_place_catalog_sqlite.py` и
`tests/test_place_catalog_builder.py`. Эти тесты включены в общую targeted-
команду; дублирующий assertion не добавлялся.

**Исходная готовность:** ветка `feat/place-catalog`, HEAD `e1ae261` с
production search 4.1. Посторонние untracked-пути из §11.1 сохранены без
изменений.

**Фактические проверки:**

```powershell
.\.venv\Scripts\python.exe -B -m py_compile tests/test_place_catalog_search.py tests/test_module_boundaries.py
# exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_search.py -q
# 16 passed in 0.70s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_place_catalog_builder.py tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py tests/test_module_boundaries.py tests/test_birth_places.py tests/test_birth_resolver.py -q
# 165 passed in 4.45s

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 2536 passed in 45.42s

git diff --check
# exit code 0; ошибок whitespace нет
```

**Границы результата:** `src/**`, contracts/public re-exports, builder/schema/
indexes, прежние tests/fixtures, resolver, application/bootstrap,
requirements/ADR/diagrams, dependencies и HTTP/UI не изменены. Карточка даёт
исполняемые доказательства AC-S1–S14, AC-L1 и общей контрольной точки AC-B6.
Сквозной builder → search → lookup → resolver/application flow остаётся 5.1;
production composition и HTTP endpoint — M1-6. Commit, push и PR не
выполнялись.
