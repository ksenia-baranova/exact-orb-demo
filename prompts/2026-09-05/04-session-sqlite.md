# Блок сессий, P4: SQLite, схема, транзакции и reaper

Работай в ветке `feat/session-context`.

P1 ввёл immutable-модели, outcomes, типизированные persistence errors, чистые
правила и порты. P2 реализовал `InMemorySessionPersistence` и общий
conformance-набор. P2.1 закрепил публичную UTC-валидацию. P3 реализовал
`ContextService`.

В этой задаче реализуй только SQLite-адаптеры портов блока сессий, схему и
миграции, сериализацию, транзакционную семантику, one-shot reaper,
SQLite-specific тесты и evidence benchmark.

Application-команды, handlers, orchestrator, `bootstrap.py`, Research Corpus,
расчётные и интерпретационные кэши сюда не входят.

## 0. Preflight

Прочитай корневой `AGENTS.md` и выполни:

```text
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log -8 --oneline
```

Если каталог не является Git-репозиторием, активна другая ветка либо в истории
нет P1–P3, остановись. Не выполняй `git init` и не реконструируй репозиторий.

Убедись, что существуют:

```text
src/exact_orb/session/adapters/_time.py
src/exact_orb/session/adapters/in_memory.py
src/exact_orb/session/context.py
tests/session/conformance.py
tests/session/test_in_memory.py
```

До изменений запусти:

```text
python -m pytest -q tests/session tests/test_module_boundaries.py
```

Если baseline падает, зафиксируй падения и не исправляй посторонние дефекты.

Изучи:

- все модули `src/exact_orb/session/`;
- `tests/session/conformance.py` и текущие session-тесты;
- `tests/test_module_boundaries.py`;
- session requirements и build natal component responsibilities;
- ADR-0009, ADR-0014, ADR-0024 и `decisions/README.md`;
- текущую реализацию thread offload в `EngineService`.

Для SQLite-семантики опирайся на официальную документацию: [`PRAGMA`](https://www.sqlite.org/pragma.html),
[transactions](https://sqlite.org/lang_transaction.html),
[WAL](https://www.sqlite.org/wal.html) и
[Python `sqlite3`](https://docs.python.org/3.11/library/sqlite3.html).

`prompts/**` — исторический журнал. Старые промты не редактируй.

Сохрани пользовательские и несвязанные изменения в рабочем дереве.

## 1. Цель и допустимые файлы

Создай:

```text
src/exact_orb/session/adapters/sqlite.py
tests/session/test_sqlite.py
scripts/bench_session_sqlite.py
docs/benchmarks/YYYY-MM-DD-session-sqlite.md
```

`YYYY-MM-DD` — фактическая локальная календарная дата benchmark-прогона, а не
дата написания промта.

При необходимости измени только:

```text
tests/test_module_boundaries.py
docs/requirements/component_responsibilities/exact-orb_session_requirements.md
docs/requirements/component_responsibilities/exact-orb_build_natal_components.md
docs/requirements/decisions/0024-sqlite-storage-implementation.md
docs/requirements/decisions/README.md
```

Не изменяй:

```text
tests/session/conformance.py
src/exact_orb/session/store.py
src/exact_orb/session/dialog.py
src/exact_orb/session/persistence.py
src/exact_orb/session/state.py
src/exact_orb/session/context.py
src/exact_orb/session/adapters/in_memory.py
tests/conftest.py
```

SQLite-типы не экспортируй из `exact_orb.session` или
`exact_orb.session.adapters`. Concrete implementation импортируется явно:

```text
from exact_orb.session.adapters.sqlite import (
    SqliteDialogStore,
    SqliteSessionPersistence,
    SqliteSessionStore,
)
```

Корневой session package и `session.adapters` при обычном импорте не должны
загружать `sqlite3`.

## 2. Публичная конструкция и конфигурация

Поддерживаемый способ создания aggregate:

```python
await SqliteSessionPersistence.open(
    db_path,
    executor=executor,
    busy_timeout_ms=5_000,
)
```

Точная форма:

```python
@classmethod
async def open(
    cls,
    db_path: str | Path,
    /,
    *,
    executor: ThreadPoolExecutor,
    busy_timeout_ms: int = 5_000,
) -> Self
```

`open` полностью инициализирует схему до возврата aggregate. Ленивые DDL и
migrations внутри операций портов запрещены.

### Валидация конфигурации

`busy_timeout_ms` обязан иметь точный тип `int` и значение не меньше нуля.
`bool`, нецелое и отрицательное значение дают `ValueError` до executor submit,
filesystem I/O, открытия connection и schema lookup. Ноль допустим и
используется held-lock тестами.

Поддерживается только file-backed database. Пустой путь, `:memory:` и SQLite
URI отвергаются через `ValueError` до I/O. Ошибка открытия корректного file path
является persistence failure, а не validation error.

Адаптер не читает environment, config или рабочий каталог и не выбирает путь
самостоятельно.

### Private backend и facets

Внутри модуля допустим private `_SqliteBackend`, содержащий канонический путь,
executor и SQLite-настройки.

Фасеты требуют backend единственным positional-only аргументом:

```python
SqliteSessionStore(backend, /)
SqliteDialogStore(backend, /)
```

Direct-конструктор aggregate следует той же дисциплине и используется только
`open`.

Обязательно:

- zero-argument construction concrete типов даёт `TypeError`;
- только aggregate создаёт backend и facets;
- `.sessions` и `.dialogs` стабильны по identity;
- оба facets разделяют один backend aggregate;
- независимо открытые aggregate имеют разные backend objects;
- public backend/config factory отсутствует;
- поддерживаемую пару facets нельзя независимо собрать над разными backend.

Не добавляй `close`, `aclose` или sync/async context-manager API. Aggregate не
хранит connection и не владеет executor, поэтому закрывать ему нечего.
Executor закрывает composition root или тестовая factory.

Не добавляй public debug/dump API, connection property, fault switches или
production test hooks.

## 3. Executor и connection lifecycle

`sqlite3` блокирующий. Каждая операция выполняет всю синхронную работу ровно
одной задачей injected executor:

```text
connection open
connection configuration
BEGIN
SELECT/DML
decode
pure transition
encode
COMMIT/ROLLBACK
connection close
```

Нельзя отправлять `BEGIN`, чтение, запись и `COMMIT` разными executor jobs.

Connection создаётся внутри worker, целиком используется тем же worker,
закрывается в `finally`, не сохраняется между вызовами, использует
`check_same_thread=True`, `isolation_level=None` и явные транзакции.

`with sqlite3.connect(...) as connection` недостаточно: такой context manager
управляет транзакцией, но не закрывает connection.

Между `primary` и `peer` не должно быть process-global lock, `asyncio.Lock` или
Python mutex. Межсоединительную корректность обеспечивает SQLite.

Executor обязателен, не создаётся и не закрывается адаптером, не импортируется
из `EngineService` и может быть разделён с другими компонентами только будущим
composition root.

### Валидация `now`

Все восемь now-bearing операций — `create`, `get`, `compare_and_set`, `append`,
`read`, `clear`, `touch`, `reset` — вызывают
`session.adapters._time.validate_now(now)` в coroutine до executor submit,
connection open и любого I/O. `reap_expired` следует тому же правилу отдельно.

Invalid `now` даёт ровно `ValueError` и не превращается в persistence error.
`reset` может валидировать `now`, а затем делегировать CAS, который валидирует
его повторно. Не закрепляй точное число вызовов validator; закрепи отсутствие
submit и I/O при невалидном входе.

`delete` не принимает и не читает `now`. Скрытые `datetime.now`, `utcnow`,
`time.time`, monotonic clock или default clock запрещены.

## 4. Строгий порядок connection configuration

После `sqlite3.connect(..., timeout=0, isolation_level=None)` выполняй строго:

1. `PRAGMA foreign_keys = ON`;
2. read-back `PRAGMA foreign_keys` обязан вернуть `1`;
3. `PRAGMA busy_timeout = <busy_timeout_ms>`;
4. read-back обязан вернуть переданное значение;
5. только при initialization — `PRAGMA journal_mode = WAL`;
6. возвращённое значение обязано быть `wal`;
7. `PRAGMA synchronous = NORMAL`;
8. read-back обязан вернуть SQLite-значение `1`;
9. только после всех проверок допускается `BEGIN`, `BEGIN DEFERRED` или
   `BEGIN IMMEDIATE`.

Ни один из этих PRAGMA не выполняется внутри `BEGIN` или `SAVEPOINT`.

Это особенно важно для `foreign_keys`, который внутри транзакции становится
no-op, и `journal_mode=WAL`, который сам требует database lock. При concurrent
`open` busy handler должен быть установлен до переключения WAL.

На operation connection шаг `journal_mode=WAL` не повторяется: WAL persistent
для файла и устанавливается initialization path. Остальные connection-level
настройки применяются к каждой новой connection.

Тесты проверяют effective значения и наблюдаемое поведение, а не ищут
SQL-строки в исходнике.

## 5. Schema и migrations

Не используй глобальный `PRAGMA user_version`. Введи component-scoped ledger:

```text
schema_migrations {
    component: text
    version:   integer
    primary key(component, version)
}
```

P4 владеет только namespace `component = "session"`. Не добавляй `applied_at`:
migration runner не должен читать wall clock.

Session schema version 1:

```text
session_states {
    session_id:          text primary key
    state_version:       integer not null
    created_at_us:       integer not null
    expires_at_us:       integer not null
    hard_expires_at_us:  integer not null
    payload_version:     integer not null
    state_json:          text not null
}

session_dialogs {
    session_id:       text primary key
                      references session_states(session_id)
                      on delete cascade
    expires_at_us:    integer not null
    payload_version:  integer not null
    turns_json:       text not null
}
```

Database constraints:

```text
length(session_id) > 0
state_version >= 0
payload_version >= 1
created_at_us <= expires_at_us
expires_at_us <= hard_expires_at_us
```

Создай TTL-индекс только `session_states(expires_at_us)`. Не создавай
expiry-индекс по `session_dialogs`: dialog deadline не участвует в выборе
reaper и не является источником liveness.

`state_version`, `payload_version` и migration version — независимые
пространства версий.

### Migration runner

Initialization открывает connection, выполняет configuration в порядке §4,
включает WAL до транзакции, затем выполняет `BEGIN IMMEDIATE`, создаёт ledger,
читает namespace `session`, проверяет точный префикс известных migrations,
применяет недостающие migrations по порядку и записывает version в той же
транзакции.

Неизвестная будущая версия и разрыв последовательности отвергаются. Успех
возвращается только после подтверждённого `COMMIT`. Failure до commit
откатывает DDL и ledger вместе. Connection всегда закрывается.

Чужие component namespaces сохраняются и игнорируются. Initialization
идемпотентна и корректна при двух concurrent `open` одного нового файла.

Не создавай migrations для P5, кэшей и application.

## 6. Codec и lossless round-trip

Используй Pydantic JSON serialization/validation. Не используй pickle,
`calculation.codec`, artifact payloads или ручную реконструкцию вложенных
моделей.

Все state timestamps дополнительно хранятся как целое число микросекунд от
Unix epoch. Запрещены SQLite `REAL` и float round-trip через
`datetime.timestamp()`. Преобразование lossless, decode возвращает
timezone-aware UTC.

Точность пользовательского времени рождения не расширяй: микросекунды
проверяются только для lifecycle timestamps и `DialogTurn.created_at`.

### State codec

`state_json` содержит полный `SessionState`, `payload_version = 1`. Не исключай
`None`, defaults или пустые tuples только ради уменьшения payload.

При чтении проверь поддерживаемую payload version, декодируй полный
`SessionState` и проверь равенство payload и SQL metadata: `session_id`,
`state_version`, `created_at`, `expires_at`, `hard_expires_at`. Затем модель
проверяет all-or-none content, `ChartRef` version и timestamp invariants.

Не требуй `hard_expires_at == created_at + текущий HARD_TTL`. Историческая
запись читается, если выполняется
`created_at <= expires_at <= hard_expires_at`.

### Dialog codec

`turns_json` содержит JSON-array ходов в порядке successful append. Decode
возвращает `tuple[DialogTurn, ...]` и проверяет persisted limits: не больше 50
ходов, 8 000 Unicode code points в одном ходе и 120 000 суммарно.

Decode не обрезает повреждённые данные. Ограничение применяет
`append_dialog_turn` до записи. Повторный `turn_id` допустим, `created_at` не
определяет порядок, marker не сверяется с текущей state version.

### Критерий round-trip

Критерий — равенство полных моделей:

```text
loaded_state == expected_state
loaded_dialog == expected_dialog
type(loaded_dialog) is tuple
conflict.actual == state_before_conflict
```

Fixture покрывает `RulershipScheme`, нормализованный tuple `include`, непустой
tuple `ResolutionWarning`, `warnings=()`, defaults, `birth_time=None`, Unicode
и astral code points, оба dialog status, независимый `truncated`, микросекунды
lifecycle/dialog и исторически допустимый `hard_expires_at`.

Expected создаётся до чтения, а не из считанного JSON или SQL row.

## 7. Lookup, lifecycle и expiry

Ни одна lifecycle-операция не скрывает expired row SQL-предикатом.

Для `get`, CAS precheck, `read`, `append`, `clear` и `touch` parent выбирается
по `session_id` без `expires_at_us > ?`, `hard_expires_at_us > ?` или
эквивалентного фильтра.

Порядок классификации:

1. SELECT parent по `session_id`;
2. отсутствие row → `SessionAbsent("not_found")`;
3. decode и проверка полного `SessionState`;
4. `is_expired(state, now=now)` → `SessionAbsent("expired")`;
5. только live state допускает version check, dialog read или mutation.

Expiry проверяется раньше CAS version mismatch. `create` определяет конфликт
по существованию primary key независимо от logical expiry.

Lookup expired row не удаляет её, не превращает в `not_found` и не позволяет
повторному create перезаписать ID. SQL-предикат по `expires_at_us` разрешён
только reaper.

## 8. Read snapshots и write transactions

`SessionStore.get`, использующий один SELECT, может полагаться на snapshot
этого statement. После fetch cursor завершается до закрытия connection.

`DialogStore.read` всегда выполняется в явной read transaction:

```text
BEGIN DEFERRED
SELECT parent
SELECT optional dialog
ROLLBACK
```

Допустим один `LEFT JOIN`, но он всё равно выполняется внутри
`BEGIN DEFERRED`. Все read statements видят один SQLite snapshot. Перед любым
success, absence или error return read transaction закрывается `ROLLBACK`.

CAS, append, clear, touch, create, delete, reaper и migration выполняют
`BEGIN IMMEDIATE` до первого SELECT/DML. В частности, touch не читает до
write transaction и не повышает deferred transaction до write.

Все необходимые state/dialog reads и writes происходят внутри одной
`BEGIN IMMEDIATE … COMMIT`.

## 9. Семантика операций

### `create`

Используй targeted `INSERT ... ON CONFLICT(session_id) DO NOTHING` и direct
cursor `rowcount`: `1` даёт `SessionCreated`, `0` — `SessionIdConflict`, другое
значение — persistence invariant failure. Коллизия не определяется через текст
исключения или широкий `IntegrityError`. Существующая row конфликтует
независимо от expiry и не читается.

### `get`

Отсутствующая row даёт `not_found`, существующая expired — `expired`, live —
полный `SessionState`. Операция не продлевает TTL и не удаляет row.

### `compare_and_set`

В одной `BEGIN IMMEDIATE`: прочитай parent только по `session_id`, классифицируй
missing/expired, верни `VersionConflict(actual)` из locked snapshot при
version mismatch, иначе примени `apply_delta`, выполни guarded parent update,
проверь общий rowcount invariant, для `RESET_DELTA` удали dialog, иначе обнови
deadline существующего dialog, commit и только после него верни новую версию.

### `read`

Следует §7–§8. Missing/expired определяется parent. Live parent без dialog row
означает `()`. Dialog deadline не участвует в liveness.

### `append`

В одной `BEGIN IMMEDIATE`: прочитай live parent и dialog, примени
`append_dialog_turn`, вычисли `touched`, guarded-update parent без изменения
версии, проверь rowcount, upsert dialog с bounded turns и тем же deadline,
commit. Concurrent append сохраняются в порядке линеаризации.

### `clear`

В одной `BEGIN IMMEDIATE`: проверь live parent, вычисли `touched`, guarded-update
parent, проверь rowcount, удали dialog, commit. Отсутствующий dialog нормален.

### `touch`

В одной `BEGIN IMMEDIATE`: прочитай live parent и optional dialog, декодируй,
вычисли touched state, guarded-update parent, проверь rowcount, синхронизируй
deadline существующего dialog, commit и верни `SessionSnapshot`. Любой renewal
failure закрывает load без snapshot.

### `reset`

Aggregate только делегирует
`sessions.compare_and_set(session_id, expected_state_version, RESET_DELTA,
now=now)`. Не пиши второй reset algorithm.

### `delete`

В `BEGIN IMMEDIATE` удаляет parent и полагается на `ON DELETE CASCADE`.
Операция идемпотентна. Отдельный предварительный DELETE dialog запрещён.

## 10. Общий guarded parent update invariant

После live precheck CAS, append, clear и touch обновляют parent по
`session_id + state_version` locked snapshot. `Cursor.rowcount` именно этого
parent UPDATE обязан быть ровно `1`.

`0`, `>1` или `-1` дают `SESSION_SQLITE_INVARIANT_VIOLATION`, rollback всей
транзакции, отсутствие повторного SELECT/retry и `StateReadError` для touch
либо `StateWriteError` для CAS/append/clear.

Используй direct cursor rowcount, а не `Connection.total_changes`.

Правило не переносится механически на остальные DML: отсутствие dialog при
clear/reset и отсутствие parent при idempotent delete допустимы; reaper
возвращает любое неотрицательное число parent rows.

## 11. Parent liveness и dialog deadline drift

`SessionState` — единственный источник `missing/live/expired`.

`DialogStore.read` не сравнивает dialog deadline с `now`, не требует equality
dialog/state deadline, не превращает drift в typed error, не ремонтирует row и
остаётся read-only.

Drift естественно устраняют successful non-reset CAS, append, touch,
clear/reset через удаление dialog и delete/reaper через удаление aggregate.

Мягкая политика относится только к dialog deadline. Payload version, state
metadata и model invariants остаются жёсткими.

## 12. Закрытое пространство error codes

Все коды — фиксированные adapter constants с префиксом `SESSION_SQLITE_` и не
экспортируются из `exact_orb.session`.

| Код | Случай |
|---|---|
| `SESSION_SQLITE_BUSY` | Numeric `SQLITE_BUSY` или `SQLITE_LOCKED` |
| `SESSION_SQLITE_OPEN_FAILED` | `open` не смог открыть DB либо установить/подтвердить WAL/PRAGMA |
| `SESSION_SQLITE_READ_FAILED` | Прочий SQLite/OSError в read-class операции |
| `SESSION_SQLITE_WRITE_FAILED` | Прочий SQLite/OSError в mutating операции |
| `SESSION_SQLITE_DATA_CORRUPT` | Известная payload version, но JSON, metadata или модель невалидны; SQLite corrupt/not-a-database |
| `SESSION_SQLITE_PAYLOAD_UNSUPPORTED` | Persisted payload version не поддерживается codec |
| `SESSION_SQLITE_SCHEMA_INCOMPATIBLE` | Ledger/schema новее реализации, имеет gap или несовместимую форму |
| `SESSION_SQLITE_MIGRATION_FAILED` | Known migration DDL/DML отказала до commit |
| `SESSION_SQLITE_INVARIANT_VIOLATION` | Нарушен persistence postcondition, включая guarded rowcount |
| `SESSION_SQLITE_COMMIT_UNKNOWN` | Вызов commit выбросил исключение |

`SessionIdConflict`, `SessionAbsent` и `VersionConflict` остаются normal
outcomes.

### Numeric SQLite classification

Не анализируй `str(exc)`. Для `sqlite3.Error` используй:

```python
code = getattr(exc, "sqlite_errorcode", None)
name = getattr(exc, "sqlite_errorname", None)
primary_code = code & 0xFF if isinstance(code, int) else None
```

Extended BUSY/LOCKED распознаются по primary code. `sqlite_errorname` допустим
для диагностики, но не становится public code.

Create collision определяется `ON CONFLICT + rowcount`. Если constraint
exception всё же классифицируется, коллизией может считаться только точный
`SQLITE_CONSTRAINT_PRIMARYKEY`. Остальные integrity failures становятся write
failure. Synthetic exception с текстом `database is locked`, но без numeric
metadata, не является BUSY.

### Error subclass

`get/read/touch` дают `StateReadError(code)`. Create/CAS/append/clear/reset/
delete/reaper/open/migrate дают `StateWriteError(code)`.

### Приоритет классификации

1. commit вызван и выбросил исключение → `COMMIT_UNKNOWN`;
2. numeric BUSY/LOCKED → `BUSY`;
3. unsupported payload version → `PAYLOAD_UNSUPPORTED`;
4. известный payload повреждён → `DATA_CORRUPT`;
5. несовместимая schema/ledger → `SCHEMA_INCOMPATIBLE`;
6. known migration не выполнилась → `MIGRATION_FAILED`;
7. initialization connection/PRAGMA/WAL не состоялся → `OPEN_FAILED`;
8. нарушен persistence postcondition → `INVARIANT_VIOLATION`;
9. остальное → `READ_FAILED` или `WRITE_FAILED`.

Ошибка best-effort rollback не заменяет исходный code. Не включай exception
text, SQL, path, session ID, birth data или dialog text. Не лови blanket
`Exception`, `BaseException`, `CancelledError`, programming errors или public
validation failures.

## 13. Commit uncertainty

Failure до commit откатывает транзакцию и возвращает обычный typed failure.
Если `commit()` был вызван, но подтверждение выбросило исключение, фактический
outcome неизвестен и даётся `SESSION_SQLITE_COMMIT_UNKNOWN`.

Адаптер не перечитывает базу, не повторяет операцию, не пытается определить
фактический commit и всегда закрывает connection. Retry-классификация остаётся
`ContextService`.

Для fault tests допустим module-private leaf seam connection factory/wrapper.
Он не входит в public API или `__all__`.

## 14. Concrete reaper

Не расширяй `SessionPersistence` Protocol. Reaper — concrete API aggregate:

```python
async def reap_expired(self, *, now: datetime) -> int
```

Метод валидирует `now` до executor/I/O, выполняется одной executor-задачей,
открывает `BEGIN IMMEDIATE`, выполняет
`DELETE FROM session_states WHERE expires_at_us <= ?`, полагается на cascade,
возвращает direct rowcount parent rows только после commit и всегда закрывает
connection.

Failure до commit откатывается. Commit uncertainty даёт
`StateWriteError("SESSION_SQLITE_COMMIT_UNKNOWN")`.

Expiry predicate в WHERE допустим здесь, потому что reaper удаляет физические
rows и не должен различать expired/not_found.

Не добавляй DELETE из `session_dialogs`, predicate по dialog deadline,
отдельный hard predicate, dialog expiry index, tombstones, retry, hidden clock,
background loop, scheduler или sleep.

## 15. Concrete conformance factory

`tests/session/conformance.py` не изменяй. Добавь
`TestSqliteSessionPersistence(SessionPersistenceConformance)` с override
`make_factory(tmp_path)`.

Каждый вход factory создаёт новый изолированный file-backed backend,
test-owned `ThreadPoolExecutor(max_workers=4)`, разные `primary` и `peer` над
одним path и `busy_timeout_ms=1_000`. Для вложенных contexts используй
deterministic локальный counter имён файлов.

Задай `SQLITE_TEST_EXECUTOR_WORKERS = 4` и проверь значение не меньше четырёх.
Не читай private `executor._max_workers`.

После `yield` factory вызывает только `executor.shutdown(wait=True)`. До этого
освободи test barriers и заверши submitted jobs.

## 16. Доказательство executor offload и конкурентности

Invalid-now и invalid-config тесты используют:

1. `RecordingExecutor`, считающий `submit`, но делегирующий настоящему
   `ThreadPoolExecutor`;
2. module-private connection seam, считающий фактические открытия connection
   внутри worker.

После initialization зафиксируй baseline counters. Для invalid-вызова оба
delta равны нулю. Положительный валидный контроль даёт положительные delta и
`connection_thread_id != event_loop_thread_id`.

Recording executor не выполняет callable inline. Private connector вызывается
в worker и там же создаёт connection; заранее открытая event-loop connection
запрещена. Seam не является public constructor argument.

Для реальной параллельности после initialization установи one-shot worker
probe: две executor-задачи входят в `threading.Barrier(2)` и обе проходят его
до SQLite-операций. Timeout — только защита от зависания.

Held-lock test использует raw `BEGIN IMMEDIATE`, synchronization event/barrier
и adapter с timeout 0. Реальный BUSY/LOCKED даёт `SESSION_SQLITE_BUSY`.

Не используй sleep, randomness, retry loops или предположение о scheduler
order.

## 17. Read-snapshot regression

Добавь управляемый regression для `DialogStore.read`: read начинает
`BEGIN DEFERRED`, читает parent, private seam/barrier останавливает его, peer
commit изменяет dialog, затем исходный read продолжает второй SELECT и должен
вернуть snapshot до peer commit.

Используй worker-side events/barrier, не timing. Если реализация использует
один join, всё равно сохрани `BEGIN DEFERRED`; тест проверяет целый snapshot без
промежуточного seam.

Touch этим тестом не покрывается: он начинает `BEGIN IMMEDIATE` до чтения.

## 18. Обязательная SQLite-specific матрица

Помимо inherited conformance проверь минимум:

1. Сигнатуры `open`, constructors и reaper.
2. Zero-argument construction и invalid config.
3. Stable facets, shared aggregate backend и отсутствие close/backend factory.
4. Разные handles одного файла и изолированные factory contexts.
5. Schema v1, migration ledger, idempotent/concurrent initialization.
6. Чужой namespace, future/gapped schema и migration rollback.
7. Отдельные `OPEN_FAILED` и `MIGRATION_FAILED`.
8. Effective WAL/NORMAL/FK/busy timeout и working cascade.
9. Parent expiry index и отсутствие dialog expiry index.
10. Нулевые submit/connect deltas для invalid now/config и валидный positive
    control вне event-loop thread.
11. Numeric BUSY и synthetic text-only negative control.
12. Create collision против другой integrity failure.
13. Full-model round-trip, Unicode, enums, tuples, defaults, None и timestamps.
14. Historical hard expiry.
15. DATA_CORRUPT против PAYLOAD_UNSUPPORTED.
16. Metadata mismatch.
17. Различение missing/expired, exact boundary, отсутствие physical delete и
    конфликт create с expired row.
18. Deferred read snapshot и BEGIN IMMEDIATE до write reads.
19. Deadline drift policy и последующий repair write.
20. Persisted deadline equality после CAS/append/touch.
21. Clear/reset/delete physical dialog removal.
22. Parent rowcount invariant для CAS/append/clear/touch и rollback faults.
23. Clear без dialog и delete missing.
24. Reaper boundary/count/live preservation/cascade.
25. Reaper не использует dialog/hard predicates.
26. Fault между state/dialog writes откатывает обе части.
27. COMMIT_UNKNOWN без retry/readback.
28. Connection closure на всех success/failure paths.
29. Worker barrier и все inherited same/cross-handle races.
30. Race reaper с CAS/append без partial aggregate.
31. Raw SQLite/OSError не пересекает persistence boundary.

Не проверяй реализацию поиском SQL-текста. Используй schema introspection,
effective PRAGMA, observable state, numeric error metadata, barriers и fault
effects.

## 19. Restart и Windows

Используй существующий workspace-local `tmp_path`. Не меняй
`tests/conftest.py`. Запрещены `/tmp`, открытый `NamedTemporaryFile`, `fork`,
POSIX-only locking и удаление/копирование только основного SQLite-файла.

Restart test использует writer и reader как независимые процессы:

```python
env = dict(os.environ)
env["PYTHONPATH"] = str(SRC_ROOT)

subprocess.run(
    [sys.executable, "-c", script, str(database_path)],
    cwd=str(tmp_path),
    env=env,
    capture_output=True,
    text=True,
    check=False,
)
```

Не наследуй ambient `PYTHONPATH`. Database path передаётся через `sys.argv`,
не интерполируется в source. Не используй `shell=True`.

Writer и reader сами создают и закрывают executor/aggregate; reader имеет
другой PID и читает полные модели. Проверяй return code, stderr, PID и
positive-control JSON обоих процессов.

Между процессами не трогай `-wal` и `-shm`. Их наличие после закрытия последней
connection не является assertion WAL. Тест доказывает normal restart, но не
power loss или kill во время commit.

Перед cleanup дождись subprocess, освободи barriers, выполни
`executor.shutdown(wait=True)` и закрой raw connections/cursors.

Добавь Windows-sensitive positive control: после teardown directory SQLite
backend можно переименовать и вернуть обратно. Tolerant `rmtree` остаётся
страховкой, но не доказательством отсутствия leaked handles.

## 20. Module boundaries

Добавь `exact_orb.session.adapters.sqlite` в полное обнаружение adapter source
files. SQLite adapter импортирует из проекта только `exact_orb.session.*`, не
читает environment, скрытые часы, UUID или randomness и не импортирует private
contract names.

Subprocess imports проверяют:

1. `exact_orb.session` не загружает adapters/context/sqlite3;
2. `exact_orb.session.adapters` загружает InMemory API, но не SQLite/sqlite3;
3. явный `exact_orb.session.adapters.sqlite` загружает concrete types и
   `sqlite3`, но не edge/runtime/calculation/native слои.

Для третьего теста используй отдельный forbidden-list с positive controls.

## 21. Benchmark CLI и методика

`scripts/bench_session_sqlite.py` использует `argparse`:

```text
--samples N    default=200, N >= 100
--workers N    default=4, N >= 2
```

Допустимы `--warmup` default 20, `--busy-timeout-ms` default 5000 и
`--database-dir`. Все фактические значения печатаются. Invalid CLI даёт
ненулевой exit code.

Скрипт не импортирует tests helpers, использует реальный injected executor,
изолированный file-backed backend, не перезаписывает существующую базу и
закрывает resources при ошибке. Неполная серия даёт non-zero exit.

Раздели измерения initialization, steady connect/configure/close и full public
operation. Не пиши механически «четыре PRAGMA»: перечисли фактические
production statements; init-only WAL не входит в steady-state path.

Используй `perf_counter_ns`, одну percentile-функцию, warmup и минимум 200
samples в фактическом P4-прогоне. Измерь p50/p95 successful CAS,
VersionConflict, append, clear, touch, reset, delete и competing writers через
два handles. Setup следующего lifecycle выполняется вне timed interval.

Вывод содержит Python/SQLite/OS, workers, samples/warmup, busy timeout,
effective PRAGMA, path class, payload/dialog size, p50/p95 и typed busy count.

Не вводи SLA и не сравнивай полный path напрямую с bare SQL `0.016 ms`.

## 22. Benchmark report и документация

Фактический прогон:

```text
python scripts/bench_session_sqlite.py --samples 200 --workers 4
```

После него создай `docs/benchmarks/YYYY-MM-DD-session-sqlite.md`; дата в имени
равна дню фактического прогона.

Report содержит дату/timezone, точную команду, Git revision и dirty marker,
Python/SQLite/OS/filesystem, WAL/synchronous/busy timeout, workers/samples,
payload/dialog size, p50/p95, competing writers и явные ограничения результата.

В ADR-0024 и session requirements добавь ссылку на report. Machine-specific
числа не копируй в requirements или ADR: числа живут только в report, требования
сохраняют методику.

Точечно уточни parent-only liveness, dialog deadline как persisted mirror,
parent-only reaper, cascade, drift policy, one-shot reaper, per-operation
connections и то, что P4 реализует только session ports. Обнови revision
ADR-0024 и `decisions/README.md`, не меняя исходную дату принятия ADR.

Application diagrams не меняй.

## 23. Предупреждение о времени тестов

На текущем baseline одна concrete implementation получает 109 inherited
conformance cases. Для SQLite каждый case использует file-backed DB, два open,
migrations, executor на четыре workers и per-operation connect/configure/close.

На Windows SQLite target, session suite и полный pytest могут выполняться
несколько минут. Это ожидаемая цена покрытия, а не признак зависания сама по
себе. Сначала выполняй collect-only, затем target, session suite и full pytest.

Не ускоряй тесты через `:memory:`, удаление параметризаций, shared DB между
contexts, persistent connection, отключение cross-handle cases или global lock.
Число 109 — текущий baseline, не вечный контракт; сообщи фактический count.

## 24. Что не входит

Не реализуй P5/caches/application/bootstrap/transport, background reaper,
Postgres/Redis/aiosqlite, новые зависимости, network calls, compatibility
aliases, idempotency keys, lifecycle epochs, dialog deduplication, гарантию
отмены уже работающего worker или переименование `orchestration/` → `agent/`.

Не создавай commit, push или PR без отдельной команды.

## 25. Проверки

Запускай поэтапно и давай долгим Windows-командам завершиться:

```text
python -m pytest --collect-only -q tests/session/test_sqlite.py
python -m pytest -q tests/session/test_sqlite.py tests/test_module_boundaries.py
python -m pytest -q tests/session tests/test_module_boundaries.py
python -m pytest -q
python scripts/bench_session_sqlite.py --samples 200 --workers 4
git diff --check
```

Не запускай отсутствующие quality gates, платные, сетевые или LLM smoke tests.

## 26. Acceptance P4

P4 завершён, когда SQLite без изменения реализует session persistence ports;
общий conformance подключён без изменения `conformance.py`; реальные
cross-handle/executor races доказаны; PRAGMA выполняются в заданном порядке;
expired/not-found не схлопнуты; read имеет единый deferred snapshot; writes
начинают `BEGIN IMMEDIATE` до чтения; invalid time/config не submit'ят работу;
connections принадлежат одному worker job; aggregate не владеет executor;
facets требуют private backend; migrations component-scoped; full-model
round-trip lossless; unsupported payload отделён от corruption; error codes
имеют `SESSION_SQLITE_` prefix; open/migration failure разделены; guarded
rowcount проверяется для CAS/append/clear/touch; drift не блокирует чтение;
reaper удаляет только parent rows; failure rollback и commit uncertainty
проверены; restart и Windows cleanup доказаны; benchmark измеряет production
path; датированный report создан и связан с требованиями; все проверки реально
запущены; P5/application не реализованы; commit без команды не создан.

## 27. Итоговый отчёт

Начни с результата. Укажи concrete types/construction; backend/facets/executor;
порядок PRAGMA; schema/migrations/codecs; expired lookup; transaction boundaries;
guarded rowcount; drift; полную таблицу error codes; commit uncertainty; reaper;
offload/concurrency; restart/Windows; round-trip; документы/report; collect
counts; точные команды и результаты; benchmark p50/p95; сохранённые user
changes и непроверенные power-loss/capacity/cancellation ограничения.

Не называй P5, все пять SQLite-хранилищ ADR-0024 или application-слой
реализованными.
