# Промт 6 — post-closeout corrections каталога мест

## Что исправляем и зачем

Устранить подтверждённые замечания после closeout M1-5, не расширяя каталог
HTTP/UI-функциями и не меняя schema/ranking/lifecycle ownership:

1. перенести точную семантику normalizer из исторического промта 1.1 в
   действующие требования;
2. сделать обе версии `tzdata` видимыми в реально форматируемом WARNING;
3. не маскировать дефекты worker-кода как retryable недоступность каталога;
4. закрепить тестами и документацией решения, которые до ревью оставались
   неявными.

## Источники истины и исходное состояние

- [AGENTS.md](../../../AGENTS.md).
- [Требования каталога](../../../docs/requirements/component_responsibilities/exact-orb_place_catalog.md).
- [План реализации](../../../docs/project_management/implementation_plans/place_catalog_implementation_plan.md).
- [Промт 1.1](../../2026-09-21/place-catalog/01.1-contracts-and-normalization-code.md),
  [промт 3.1](03.1-sqlite-lifecycle-and-lookup-code.md) и
  [промт 4.1](04.1-indexed-place-search-code.md).
- Текущие `exact_orb.birth.places`, `exact_orb.birth.adapters.sqlite` и
  принятые place-catalog tests.

Перед изменениями подтвердить ветку `feat/place-catalog`, HEAD `0dda195` и
сохранить все посторонние untracked-файлы.

## Нормализация: нормативная фиксация без изменения production

В §4.2 требований явно записать:

- raw control означает только Unicode General Category `Cc`; `Cf`, включая
  U+00AD SOFT HYPHEN, не считается `CONTROL_CHARACTERS` и сохраняется в
  search key, если NFKC не меняет символ;
- длина измеряется у итогового ключа после NFKC, whitespace folding,
  `casefold()` и `ё → е`;
- наличие searchable-символа определяется ровно `str.isalnum()`, включая
  поддерживаемые Python категории Unicode numbers `Nl`/`No`;
- pure normalizer не имеет отдельного raw-size guard. M1-6 обязан ограничить
  HTTP query/body до вызова каталога; не добавлять многомегабайтный timing-test
  или произвольный второй лимит в M1-5.

Добавить contract tests для принятого `Cf`-поведения, `Nl`/`No` и
идемпотентности успешной нормализации. Существующие коды и порядок исходов не
менять.

## Runtime errors search/lookup

Разделить отказ постановки worker-задачи и результат worker:

- `RuntimeError` непосредственно из `run_in_executor(...)` преобразовать в
  `PlaceCatalogUnavailableError` с причиной и сообщением `could not be
  scheduled`;
- `CancelledError` ожидания распространять без преобразования;
- только `sqlite3.Error`, полученный из выполненной `_sync_search` или
  `_sync_lookup`, преобразовывать в `PlaceCatalogUnavailableError`;
- неожиданные `AssertionError`, `ValueError`, `TypeError` и другие дефекты
  worker/model-кода не преобразовывать в retryable availability failure.

Не менять широкую startup/cleanup классификацию `open()` и `aclose()` этой
карточкой: там typed startup/cleanup boundary охватывает path, metadata,
timezone validation и cleanup.

Добавить позитивный control реального SQLite read failure и regression tests,
где внедрённый `AssertionError` из `_sync_search`/`_sync_lookup` выходит без
преобразования. Зафиксировать, что query type и limit валидируются до lifecycle:
invalid limit на unopened/closed adapter даёт `ValueError` без worker submission.

## tzdata startup и WARNING

Сохранить `tzdata` обязательной direct dependency:

- отсутствие distribution metadata не является version mismatch и остаётся
  typed startup failure; системная timezone database не заменяет обязательную
  версию воспроизводимого окружения;
- mismatch при установленном пакете остаётся WARNING и не останавливает
  startup, если все зоны разрешимы;
- message итоговой log-записи обязан содержать event name и обе пары
  `catalog_tzdata_version=...`, `runtime_tzdata_version=...` посредством
  позиционного форматирования; structured `extra` сохранить.

Обновить тест mismatch так, чтобы он проверял `LogRecord.getMessage()`, и
добавить тест `PackageNotFoundError` как startup failure.

## Зафиксированные решения без рефакторинга

В требованиях или журнале плана отметить:

- builder валидирует минимальную физическую структуру каждой непустой строки
  `alternateNamesV2` до фильтра `relevant_ids`; повреждённая нерелевантная
  строка останавливает сборку как повреждение обязательного входа;
- producer и consumer намеренно имеют независимые schema-v1 expectations;
  общий модуль констант не вводится, чтобы несогласованное изменение builder-а
  не принималось adapter-ом автоматически;
- `PRAGMA table_info` получает только фиксированные имена из schema constants;
  пользовательский ввод интерполироваться в SQL не может;
- размещение AC-B6 уже отражено журналом 4.2 и не требует дублирующего теста;
- существующие singleton module lists являются tuple и не изменяются.

## Разрешённые файлы

- этот prompt-файл;
- `src/exact_orb/birth/adapters/sqlite.py`;
- `tests/test_place_search_contracts.py`;
- `tests/test_place_catalog_sqlite.py`;
- `tests/test_place_catalog_search.py`;
- `docs/requirements/component_responsibilities/exact-orb_place_catalog.md`;
- `docs/project_management/implementation_plans/place_catalog_implementation_plan.md`.

## Запреты

Не менять `exact_orb.birth.places`, builder, schema/indexes, fixtures/raw data,
resolver/application/bootstrap, HTTP/UI, dependencies, ADR и соседние
requirements/diagrams. Не вводить общий schema-модуль, raw-size threshold,
отклонение `Cf`, fallback на системную timezone database или новые error codes.

Не создавать commit, push или PR без отдельного указания владельца.

## Проверки

Последовательно выполнить:

```powershell
.\.venv\Scripts\python.exe -B -m py_compile src/exact_orb/birth/adapters/sqlite.py tests/test_place_search_contracts.py tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/test_place_catalog_sqlite.py tests/test_place_catalog_search.py -q
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_place_catalog_builder.py tests/application/test_place_catalog_integration.py tests/test_module_boundaries.py tests/test_birth_places.py tests/test_birth_resolver.py -q
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
git diff --check
```

Проверить относительные Markdown-ссылки prompt, requirements и плана. В журнал
плана записать фактические изменения, команды и результаты, а также решения,
оставленные M1-6. Generated SQLite и посторонние untracked-файлы не затрагивать.
