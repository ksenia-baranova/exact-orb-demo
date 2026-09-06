# FIX — Блок сессий, P4.1: lifecycle SQLite connection, WAL recovery, payload compatibility и runtime-import boundary

Работай в ветке `feat/session-context`.

Это точечное исправление P4 и усиление одной границы P1/P2. P5 `Research
Corpus`, application-слой, `bootstrap.py` и переименование
`orchestration/` → `agent/` сюда не входят.

## 0. Preflight

Прочитай корневой `AGENTS.md` и выполни:

```text
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log -8 --oneline
```

Если каталог не является Git-репозиторием, активна другая ветка либо в истории
нет P1, P2, P2.1, P3 и P4, остановись и сообщи. Не выполняй `git init` и не
восстанавливай репозиторий вручную.

В рабочем дереве уже могут находиться пользовательские и несвязанные изменения.
Не откатывай, не перезаписывай и не форматируй их. Если изменяемый этой задачей
файл уже dirty, сначала изучи diff и меняй только относящиеся к P4.1 фрагменты.
Если безопасно разделить изменения нельзя — остановись и сообщи.

Убедись, что существуют:

```text
src/exact_orb/session/adapters/sqlite.py
src/exact_orb/session/context.py
tests/session/conformance.py
tests/session/test_sqlite.py
tests/test_module_boundaries.py
scripts/bench_session_sqlite.py
docs/benchmarks/2026-09-06-session-sqlite.md
```

До изменений запусти:

```text
python -m pytest --collect-only -q tests/session
python -m pytest -q tests/session tests/test_module_boundaries.py
python -c "import sys, sqlite3, pydantic; print(sys.version, sqlite3.sqlite_version, pydantic.VERSION)"
```

Ожидаемый исходный baseline:

```text
tests/session: 524 collected
tests/session + test_module_boundaries.py: 549 collected (524 + 25), все зелёные
```

Расхождение зафиксируй и не подгоняй. Посторонние дефекты не исправляй.

Версии Python, SQLite и Pydantic запиши в отчёт. Эта задача вводит замороженный
payload fixture, и через полгода именно они позволят отличить «изменилась
модель» от «изменилось представление в Pydantic». Зависимость объявлена как
`pydantic>=2` без lock-файла.

Изучи перед изменением:

```text
src/exact_orb/session/adapters/sqlite.py
src/exact_orb/session/adapters/in_memory.py
src/exact_orb/session/context.py
src/exact_orb/session/state.py
src/exact_orb/session/dialog.py
src/exact_orb/birth/types.py
src/exact_orb/calculation/spec.py
tests/session/test_sqlite.py
tests/test_module_boundaries.py
docs/requirements/component_responsibilities/exact-orb_session_requirements.md
docs/requirements/decisions/0024-sqlite-storage-implementation.md
docs/requirements/decisions/README.md
prompts/2026-09-05/04-session-sqlite.md
```

`prompts/**` — исторический журнал. Старые промты не редактируй и не используй
как более приоритетный источник по сравнению с действующими requirements и ADR.

## 1. Подтверждённые причины

### 1.1. Результат операции теряется при отказе `close()`

`_close_preserving_active_error` вызывается из `finally` в `_run_connection`,
`_run_immediate` и `_sync_initialize`. Если `connection.close()` бросает после
уже подтверждённого результата, исключение из `finally` отбрасывает этот
результат.

Для mutating-операции это может дать `SESSION_SQLITE_WRITE_FAILED` после
подтверждённого commit. Для read-операции полностью прочитанные данные
превращаются в `StateReadError`.

Классификация дополнительно зависит от `sys.exc_info()`: один и тот же вызов
ведёт себя по-разному в зависимости от того, был ли он сделан внутри чужого
`except`.

### 1.2. No-commit rollback не отделён от освобождения connection

Штатные `SessionAbsent`, `VersionConflict` и `SessionIdConflict` требуют
закрыть `BEGIN IMMEDIATE` без commit. Сейчас исключение из `rollback()` может
заменить normal outcome. То же относится к `DialogStore.read`: его explicit
`BEGIN DEFERRED` завершается `connection.rollback()` и на успешной ветке, то
есть отказ rollback уничтожает полностью прочитанный диалог.

При этом нельзя безусловно подавлять одновременно отказ rollback и отказ
close: тогда транзакция и write lock могут остаться неразрешёнными.

### 1.3. WAL recovery распознаёт не все допустимые проявления гонки

Initialization повторяет configuration только после numeric
`SQLITE_BUSY`/`SQLITE_LOCKED`. Если `PRAGMA journal_mode = WAL` вернул значение,
отличное от `wal`, без исключения, `_AdapterFailure` проходит мимо разрешённой
одной повторной попытки.

### 1.4. Payload version не закреплена compatibility-тестом

State codec читает полный `SessionState`, включая вложенные модели. Dialog
codec читает `DialogTurn` и применяет три persisted-инварианта:

```text
MAX_DIALOG_TURNS
MAX_DIALOG_TURN_CHARS
MAX_DIALOG_CHARS
```

Изменение модели, сериализации, валидатора или лимита может сделать старые
строки нечитаемыми при прежнем `payload_version`.

Хеш `model_json_schema()` не является достаточным доказательством: он может
измениться из-за версии Pydantic и не обязан меняться при изменении custom
validator или serializer. Проект использует незакреплённую зависимость
`pydantic>=2`, поэтому hardcoded schema hash не вводить.

### 1.5. Runtime-граница импортов допускает неназванный транзитивный рост

Чистый `import exact_orb.session` выполняет `birth/__init__.py` и
`calculation/__init__.py`, поэтому загружает дополнительные project-модули.
Текущий forbidden-list ловит известные опасные пакеты, но не любой новый
транзитивный импорт.

Точное равенство всему текущему `sys.modules` тоже не является хорошим
постоянным контрактом: оно будет ломаться даже при полезном удалении лишнего
импорта. Нужна верхняя граница разрешённого множества и отдельный список
известного транзитивного долга.

## 2. Допустимые изменения

Измени только:

```text
src/exact_orb/session/adapters/sqlite.py
tests/session/test_sqlite.py
tests/test_module_boundaries.py
tests/session/golden/session_sqlite_payload_v1.json
docs/requirements/component_responsibilities/exact-orb_session_requirements.md
docs/requirements/decisions/0024-sqlite-storage-implementation.md
docs/requirements/decisions/README.md
```

Fixture и каталог `tests/session/golden/` можно создать, если их ещё нет. Блок
сессий держит свои артефакты в `tests/session/`; не размещай fixture в
`tests/fixtures/`, который является пакетом calculation/natal-данных. Других
новых файлов и модулей не создавай.

Не изменяй:

```text
tests/session/conformance.py
tests/session/test_context.py
tests/session/test_in_memory.py
tests/session/test_state.py
tests/session/test_dialog.py
tests/session/test_contracts.py
tests/conftest.py
src/exact_orb/session/state.py
src/exact_orb/session/dialog.py
src/exact_orb/session/store.py
src/exact_orb/session/persistence.py
src/exact_orb/session/outcomes.py
src/exact_orb/session/errors.py
src/exact_orb/session/context.py
src/exact_orb/session/adapters/in_memory.py
src/exact_orb/session/adapters/_time.py
src/exact_orb/session/adapters/__init__.py
src/exact_orb/birth/**
src/exact_orb/calculation/**
scripts/bench_session_sqlite.py
docs/benchmarks/**
prompts/**
```

Публичный API, `__all__`, сигнатуры, Protocol и пространство из десяти
`SESSION_SQLITE_*` error codes не меняются. Новые runtime-зависимости не
добавляй.

## 3. Fix 1 — исход операции отдельно от cleanup

### 3.1. Два ортогональных факта вместо одного детектора

Удали использование `sys.exc_info()` для определения исхода: оно связывает
классификацию с контекстом вызова.

Lifecycle обязан явно нести три вещи:

1. **Исход операции** — вычисленный normal outcome либо исключение.
2. **Разрешение транзакции** — `resolved` или `unresolved`.
3. **Результат cleanup** — `close()` вернулся успешно или бросил.

Транзакция считается `resolved`, если выполнено одно из условий:

* `commit()` вернулся успешно;
* `rollback()` вернулся успешно;
* `rollback()` бросил, но последующий `close()` вернулся успешно и тем самым
  освободил connection вместе с незавершённой транзакцией;
* транзакция не открывалась (например, одиночный SELECT в `get`).

Все правила §3.2–§3.5 формулируются только через эти три факта. Не вводи
дополнительных состояний и не выводи их из стека вызовов.

Порядок исполнения даёт нужное поведение бесплатно: `finally` выполняется до
того, как возвращаемое значение уходит вызывающему коду, поэтому отказ cleanup
способен превратить уже вычисленный normal outcome в ошибку там, где это
требуется §3.4.

### 3.2. Отказ close после завершённой операции

Если normal outcome вычислен и транзакция `resolved`, исключение
`sqlite3.Error` или `OSError` из `close()`:

* не заменяет результат;
* не становится `WRITE_FAILED`, `READ_FAILED` или `COMMIT_UNKNOWN`;
* записывается как безопасный warning через module logger;
* warning не содержит exception text, SQL, database path, session ID,
  birth data или dialog text.

`COMMIT_UNKNOWN` означает только исключение непосредственно из вызова
`commit()`.

`sqlite3.ProgrammingError` из `close()` не подавляется и не переводится в
persistence error: это programming defect.

### 3.3. Ошибка операции имеет приоритет над cleanup

Если операция уже завершилась исключением, последующий `sqlite3.Error` или
`OSError` из `close()` не заменяет исходную ошибку. Подавленный cleanup failure
фиксируется безопасным warning.

`sqlite3.ProgrammingError` остаётся неподавляемым.

То же правило действует при отказе configuration в
`_open_configured_connection`: ошибка закрытия не должна заменить исходную
ошибку configuration.

### 3.4. No-commit rollback

Правило распространяется на:

* `result.commit is False` в `_run_immediate`;
* normal return из explicit `BEGIN DEFERRED` в `DialogStore.read`, включая
  успешную ветку с прочитанным диалогом.

Если `rollback()` бросил `sqlite3.Error` или `OSError`:

1. сохрани normal outcome;
2. обязательно попытайся закрыть connection;
3. если `close()` вернулся успешно, верни normal outcome и запиши safe warning
   об отказе rollback;
4. если `close()` тоже бросил `sqlite3.Error`, кроме `ProgrammingError`, либо
   `OSError`, транзакция не считается разрешённой: подними существующий typed
   persistence error соответствующего operation class;
5. для классификации используй numeric SQLite metadata rollback failure, а при
   её отсутствии — существующий default `READ_FAILED` или `WRITE_FAILED`;
6. новых error codes не вводи.

Если rollback или последующий close бросил `sqlite3.ProgrammingError`, не
подавляй и не типизируй его: он выходит наружу как programming defect. Это
правило имеет приоритет над typed-классификацией двойного cleanup failure.

Нельзя утверждать, что normal outcome завершён, если и rollback, и close не
подтверждены.

### 3.5. Initialization

После подтверждённого commit миграций отказ `close()` не превращает успешный
`open` в `OPEN_FAILED` или `COMMIT_UNKNOWN`. Верни aggregate и запиши safe
warning.

Не добавляй `close`, `aclose`, context manager или connection pool в публичный
API aggregate. Он по-прежнему открывает connection на каждую операцию и не
владеет executor.

## 4. Fix 2 — bounded WAL recovery

Введи отдельный private способ обозначить только состояние «initialization не
подтвердила `journal_mode = wal`». Не используй для этого общий
`_AdapterFailure(OPEN_FAILED)`, иначе retry может случайно распространиться на
прочие PRAGMA failures.

Разрешена ровно одна свежая configuration attempt, если первая попытка:

* получила numeric `SQLITE_BUSY`/`SQLITE_LOCKED` во время initialization
  configuration;
* либо `PRAGMA journal_mode = WAL` вернул не-`wal` без исключения.

Требования:

* первая connection закрывается до второй попытки;
* вторая попытка использует новую connection;
* sleep, retry loop, process-global lock и `asyncio.Lock` запрещены;
* migration transaction не повторяется;
* operation connections не переключают journal mode;
* `foreign_keys`, `busy_timeout` и `synchronous` по-прежнему устанавливаются и
  проверяются на каждой connection;
* mismatch любого другого PRAGMA не запускает retry;
* повторный не-`wal` даёт `SESSION_SQLITE_OPEN_FAILED`;
* повторный numeric `BUSY`/`LOCKED` сохраняет `SESSION_SQLITE_BUSY`;
* третьей попытки нет.

Контракт остаётся ограниченным двумя concurrent first-open. Не расширяй его до
произвольного числа участников в рамках P4.1.

## 5. Fix 3 — golden compatibility gate для payload v1

Создай фиксированный, вручную обозримый fixture:

```text
tests/session/golden/session_sqlite_payload_v1.json
```

Fixture не генерируется во время теста из текущих Pydantic-моделей.

### 5.1. Состав fixture

Fixture хранит:

* номер state payload version;
* минимум один empty state v1;
* полные state v1 с заполненными вложенными `BirthInput`, `ResolvedBirthData`,
  `ResolutionWarning`, `ChartRef` и `ChartSpec`;
* варианты `birth_time=None`, warnings empty/non-empty и нормализованного
  `include`;
* номер dialog payload version;
* dialog v1 с `Selection`, `complete`/`partial`, `truncated`, Unicode и
  несколькими ходами;
* значения трёх dialog limits, действовавшие для v1;
* диагностический `reference_environment` с версиями Python, SQLite и
  Pydantic, в которых fixture был записан; эти значения не участвуют в
  compatibility-assertion и не ограничивают поддерживаемые версии;
* **relational metadata каждой строки**: для state —`session_id`,
  `state_version`, `created_at_us`, `expires_at_us`, `hard_expires_at_us`,
  `payload_version`; для dialog — `session_id`, `expires_at_us`,
  `payload_version`;
* **три референсных `now`** в aware UTC: один для live read, отдельный
  `touch_now`, при котором `now + SLIDING_TTL <= expires_at` и deadline не
  меняется, и один, при котором строки уже expired.

Relational metadata и три `now` обязательны: без них замороженную строку нечем
вставить в базу и нечем прогнать через публичный порт, а cross-check payload
против колонок, стабильный touch и классификация expiry останутся
неисполненными.

### 5.2. Как проверяется

Раздели read- и write-совместимость.

**Read compatibility:** вставь frozen relational rows и JSON напрямую через
`sqlite3`, затем прочитай их через публичные `get`, `read` и `touch`. Не
вызывай `_decode_state_row` или `_decode_dialog_row` напрямую. Используй
`touch_now` из fixture: `touch` обязан пройти state encoder, но не менять
deadline или семантический state.

**Write compatibility:** через публичную последовательность
`create → compare_and_set → append` построй те же state и dialog, затем
прочитай persisted JSON напрямую через `sqlite3` и сравни с frozen fixture.
Именно `append` обязан доказать работу dialog encoder: `touch` обновляет только
dialog deadline и не перекодирует `turns_json`.

Прямой SQL допустим только для fixture injection и read-back persisted bytes.
Наблюдаемое поведение codec проверяется через публичные порты.

Ожидаемые `SessionState`, `ChartRef`, `ChartSpec`, `BirthInput`,
`ResolvedBirthData`, `ResolutionWarning`, `DialogTurn` и `Selection`
конструируются **литерально в коде теста**. Строить ожидание разбором того же
fixture запрещено: такой тест доказывает только самосогласованность JSON.

Проверки обязаны доказывать:

1. Текущий v1 decoder читает frozen state payload и получает целиком ожидаемую
   `SessionState`.
2. Текущий v1 decoder читает frozen dialog payload и получает ожидаемый tuple
   `DialogTurn`.
3. Публичные write-пути кодируют соответствующие текущие модели в тот же
   семантический JSON: сравнивай разобранную JSON-структуру, а не порядок
   ключей или whitespace. State encoder исполняется через CAS и touch, dialog
   encoder — через append.
4. Relational metadata и JSON metadata проходят существующие проверки
   равенства, а рассинхрон любого из пяти полей по-прежнему даёт
   `DATA_CORRUPT`.
5. На втором референсном `now` те же замороженные строки классифицируются как
   `SessionAbsent("expired")`, а строка физически не удаляется.
6. Текущие `_STATE_PAYLOAD_VERSION` и `_DIALOG_PAYLOAD_VERSION` соответствуют
   версиям fixture.
7. Три текущих dialog limits соответствуют manifest v1.
8. Existing tests для `PAYLOAD_UNSUPPORTED` и `DATA_CORRUPT` не ослаблены.

Сначала сопоставь пункты 4, 5 и 8 с существующими metadata, corruption и
expiry-тестами. Переиспользуй или точечно расширь их; не создавай дубликаты,
если frozen fixture не добавляет новую исполняемую ветку.

### 5.3. Сообщение о несовпадении

Сообщение при несовпадении должно объяснять допустимые действия:

* изменение обратно совместимо для чтения старых строк — обновить fixture с
  явным обоснованием;
* изменение несовместимо — поднять payload version и добавить decoder старой
  версии или migration;
* изменилось только нерелевантное представление тестовых данных или версия
  Pydantic — доказать это и обновить fixture.

Не используй `model_json_schema()` hash как единственный или обязательный gate.
Не добавляй runtime fingerprint, будущие миграции и новые payload versions в
этой задаче.

## 6. Fix 4 — runtime upper-bound импортов

Сохрани существующие AST allowlist и runtime forbidden-проверки.

Для четырёх чистых subprocess-сценариев:

```text
import exact_orb.session
import exact_orb.session.adapters
import exact_orb.session.adapters.sqlite
import exact_orb.session.context
```

зафиксируй отдельно:

* `REQUIRED` — модули, без которых соответствующий публичный импорт не
  считается выполненным;
* `KNOWN_TRANSITIVE_DEBT` — текущие лишние модули из eager `birth/__init__.py`
  и `calculation/__init__.py`;
* фактически загруженное множество `exact_orb` и `exact_orb.*`.

Проверяй:

```text
missing = REQUIRED - loaded
unexpected = loaded - REQUIRED - KNOWN_TRANSITIVE_DEBT
```

Оба множества должны быть пустыми.

### 6.1. Базовый `REQUIRED`

Родительские пакеты обязаны входить в `REQUIRED`: импорт submodule в Python
неизбежно исполняет `__init__` каждого родителя, и без них любая реализация
получит непустой `unexpected` на первом же прогоне.

Базовый набор, общий для всех четырёх сценариев:

```text
exact_orb
exact_orb.session
exact_orb.session.errors
exact_orb.session.state
exact_orb.session.outcomes
exact_orb.session.dialog
exact_orb.session.store
exact_orb.session.persistence
exact_orb.birth
exact_orb.birth.types
exact_orb.calculation
exact_orb.calculation.spec
exact_orb.domain
```

`exact_orb.domain` относится к `REQUIRED`, а не к долгу: это реальная
контрактная зависимость `calculation.spec`.

Добавления по сценариям:

```text
adapters:         exact_orb.session.adapters
                  exact_orb.session.adapters._time
                  exact_orb.session.adapters.in_memory
adapters.sqlite:  всё из adapters + exact_orb.session.adapters.sqlite
context:          exact_orb.session.context
```

### 6.2. `KNOWN_TRANSITIVE_DEBT`

Текущий долг:

```text
exact_orb.birth.places
exact_orb.birth.resolver
exact_orb.birth.tz
exact_orb.calculation.cache
exact_orb.calculation.keys
exact_orb.outcomes
exact_orb.run_context
```

Это семь submodule, устранимых ленивым `__init__` в чужих пакетах, в отличие от
родительских пакетов из §6.1, которые устранить нельзя.

Удаление модуля из `KNOWN_TRANSITIVE_DEBT` не должно ломать тест. Новый
неназванный project-модуль должен ломать его с читаемым выводом `unexpected`.

### 6.3. Позитивные контроли

Для каждого subprocess оставь позитивный контроль публичных символов,
относящихся к сценарию:

```text
SessionState
SessionSnapshot
SessionStore
DialogStore
SessionPersistence
InMemorySessionStore
InMemoryDialogStore
InMemorySessionPersistence
SqliteSessionStore
SqliteDialogStore
SqliteSessionPersistence
ContextService
```

Проверки `sqlite3`, `swisseph`, `aiosqlite`, `redis`, native stack и edge-слоёв
не ослабляй.

В P4.1 не исправляй eager `__init__`, не вводи `__getattr__` и не переноси
контрактные типы. Тест является upper-bound и сигнализацией долга, а не
объявлением этих транзитивных импортов желательной архитектурой.

## 7. Обязательная тестовая матрица

Новые тесты размещай только в `tests/session/test_sqlite.py` и
`tests/test_module_boundaries.py`, кроме JSON fixture.

Используй существующий `_CONNECTION_FACTORY`, `monkeypatch`, workspace-local
`tmp_path`, события и барьеры. Не используй `sleep`, случайные задержки,
реальное время, сеть и поиск SQL-текста в исходнике.

### 7.1. Close после завершённой операции

Параметризованно закрой все публичные пути:

```text
open
create
get
compare_and_set
append
read
clear
touch
reset
delete
reap_expired
```

Fault connection должна вызвать реальный `close()`, а затем ровно один раз
бросить `OperationalError`. Seam вооружается только на целевую операцию и
отключается до проверки состояния.

Для каждого применимого пути докажи:

* публично наблюдаемый outcome эквивалентен baseline;
* для моделей используется model equality, а не «побайтовое» сравнение;
* для `open` проверяются тип aggregate, стабильные facets и возможность
  следующей операции после восстановления factory;
* состояние базы эквивалентно baseline;
* typed persistence error не поднят;
* close seam действительно сработал;
* записан safe warning без чувствительных данных.

Этот seam всегда реально освобождает connection, поэтому допущение §3.1
«`close()` бросил ⇒ handle мог остаться удержанным» им не проверяется. Это
осознанное ограничение объёма: сценарий «бросил до освобождения handle»
проверяет поведение ОС, а не семантику адаптера. Назови ограничение в отчёте
и не выдавай матрицу за его доказательство.

### 7.2. Ошибки и cleanup

Проверь:

1. `ProgrammingError` из close выходит наружу.
2. Failure до commit сохраняет прежний typed code и откатывает обе части.
3. Исключение непосредственно из `commit()` даёт только `COMMIT_UNKNOWN`, без
   readback и retry.
4. Close failure во время уже активной ошибки не заменяет исходную ошибку.
5. Вызов изнутри чужого `except` классифицируется так же, как обычный вызов.
6. Rollback failure плюс успешный close сохраняет:
   * `VersionConflict(actual)` для CAS;
   * `SessionAbsent` для touch;
   * `SessionIdConflict` для create;
   * результат или absence для `DialogStore.read`, включая успешную ветку с
     непустым диалогом.
7. Rollback failure плюс close failure не возвращает normal outcome, а даёт
   существующий typed error; третьей cleanup-попытки нет.
8. Для seam, который делегирует реальный close перед исключением, другая
   connection может получить write lock. Это проверка hygiene тестовой
   инфраструктуры, а не доказательство поведения ОС после настоящего
   незавершённого close.
9. Все fault connections закрыты или безопасно освобождены до удаления
   `tmp_path`, включая Windows.

### 7.3. WAL

Проверь:

1. Первый WAL set/read-back возвращает не-`wal`, второй — `wal`: `open`
   успешен, connections ровно две.
2. Обе попытки возвращают не-`wal`: `OPEN_FAILED`, connections ровно две.
3. Вторая попытка бросает numeric BUSY/LOCKED: наружу выходит `BUSY`,
   connections ровно две.
4. Mismatch `foreign_keys`, `busy_timeout` или `synchronous` не получает WAL
   retry.
5. Existing BUSY/concurrent-first-open tests остаются зелёными без ослабления.
6. Позитивный контроль доказывает, что вторая попытка действительно дошла до
   WAL read-back.

### 7.4. Payload и imports

Проверь golden payload v1 по §5 и четыре subprocess upper-bound сценария по
§6. Диагностика boundary failure печатает отдельно `missing` и `unexpected`.

Inherited conformance не меняй и не сокращай.

## 8. Документация

Обнови точечно.

### `exact-orb_session_requirements.md`

Зафиксируй:

* подтверждённый outcome операции не заменяется cleanup failure;
* `COMMIT_UNKNOWN` относится только к исключению из `commit()`;
* normal no-commit outcome возвращается после подтверждённого rollback либо
  успешного close;
* двойной отказ rollback и close является persistence failure;
* persisted compatibility закреплена frozen v1 payload fixtures, читаемыми
  через публичный порт;
* модели, serializers, validators и dialog limits входят в решение о
  совместимости payload;
* runtime-import boundary использует required upper-bound и явно названный
  transitive debt.

### ADR-0024

Обнови ревизию текущей датой и зафиксируй перечисленное ниже. Если ADR уже
содержит ревизию с этой датой, расширь её; не создавай вторую строку ревизии с
той же датой.

* разделение transaction outcome и connection cleanup;
* политику rollback/close;
* расширенное, но однократное WAL recovery;
* golden payload compatibility gate;
* относительный `db_path` канонизируется через `Path.resolve()` в момент
  `open`, поэтому зависит от cwd вызывающего процесса.

Уточни прежнюю фразу: адаптер не выбирает путь и не читает environment/config,
но caller-provided relative path разрешается относительно текущего cwd.
Исходную дату принятия ADR не меняй.

### `decisions/README.md`

Синхронизируй только описание ревизии ADR-0024. Не затрагивай посторонние
пользовательские изменения файла.

Benchmark не перезапускай и датированный benchmark-отчёт не меняй: steady-state
путь не должен измениться. Если он всё же изменился, остановись и сообщи.

## 9. Что не входит

Не меняй в P4.1:

* write amplification `touch`;
* per-operation connection;
* полную материализацию диалога;
* `SessionSnapshot` и публичные порты;
* владельца periodic reaper;
* отсутствие reaper у тестового InMemory;
* `NOT NULL` ledger — это требует отдельной v2 migration;
* `StateReadError` для commit uncertainty внутри `touch`;
* `ChartSpec = NatalChartSpec`;
* фактическую eager-загрузку `birth` и `calculation`;
* P5, application, bootstrap и transport;
* новые зависимости, Postgres, Redis или aiosqlite.

Не выдавай эти уже известные ограничения за новые находки P4.1.

## 10. Проверки

Запускай поэтапно:

```text
python -m pytest --collect-only -q tests/session/test_sqlite.py
python -m pytest -q tests/session/test_sqlite.py tests/test_module_boundaries.py
python -m pytest -q tests/session tests/test_module_boundaries.py
python -m pytest -q
git diff --check
git status --short
```

Приведи фактические числа до и после. Не запускай отсутствующие quality gates,
сетевые, платные и LLM smoke tests.

## 11. Acceptance

P4.1 завершён, когда:

1. Подтверждённый commit и завершённое чтение не теряются из-за close failure.
2. `COMMIT_UNKNOWN` возникает только из исключения `commit()`.
3. Классификация не зависит от `sys.exc_info()` и чужого `except`.
4. No-commit outcome сохраняется, если rollback либо последующий close
   подтвердили завершение транзакции, включая успешную ветку
   `DialogStore.read`.
5. Двойной отказ rollback и close не объявляется успешным завершением.
6. Подавленные cleanup failures наблюдаемы безопасным warning.
7. WAL non-`wal` получает не более одной свежей попытки.
8. Остальные PRAGMA failures не получают retry.
9. Frozen payload v1 читается текущим codec через публичный порт и совпадает с
   ожидаемыми моделями, построенными в коде теста.
10. Dialog limits связаны с manifest payload v1.
11. Runtime import upper-bound ловит новые project-модули, но допускает
    удаление известного долга; родительские пакеты входят в `REQUIRED`.
12. Публичный API, Protocol, error codes и conformance не изменены.
13. Документы синхронизированы, benchmark не переписан.
14. Все проверки фактически запущены.
15. P5 и application не реализованы.
16. Commit, push и PR без отдельной команды не созданы.

## 12. Итоговый отчёт

Начни с результата. Затем укажи:

1. Как разделены outcome, transaction resolution и cleanup.
2. Как обрабатываются четыре комбинации rollback/close.
3. Чем заменён `sys.exc_info()`.
4. Какие public paths покрыты close fault matrix и какое допущение §3.1
   осталось непроверенным.
5. Как классифицируется повторная WAL-неудача.
6. Какие frozen payload входят в v1 compatibility gate и как доказано, что
   ожидания не выведены из самого fixture.
7. Какие runtime-import модули являются required, unexpected и known debt.
8. Какие документы изменены.
9. Точные команды, реальные результаты тестов и версии Python, SQLite,
   Pydantic.
10. Какие пользовательские изменения сохранены.
11. Какие ограничения из §9 остались вне задачи.

Не создавай commit, push или PR без отдельной команды.
