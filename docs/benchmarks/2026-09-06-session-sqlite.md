# Session SQLite adapter benchmark — 2026-09-06

Дата и время прогона: 2026-09-06 00:41–00:43 MSK (`UTC+03:00`).

Команда:

```text
python scripts/bench_session_sqlite.py --samples 200 --workers 4
```

Результат: exit code `0`; каждая серия содержит ровно 200 измеряемых samples
после 20 warmup-операций.

## Окружение

| Параметр | Значение |
|---|---|
| Git revision | `9d8d207298b77f6b922e2a9fa05ca4498023d126` + dirty worktree |
| Python | CPython 3.14.0 |
| SQLite | 3.50.4 |
| ОС | Windows 11 (`10.0.26200`) |
| Файловая система | NTFS, fixed local drive |
| Database path class | isolated temporary file-backed DB под workspace-local `logs/` |
| Executor | caller-owned `ThreadPoolExecutor(max_workers=4)` |
| Samples / warmup | 200 / 20 на серию |
| Busy timeout | 5000 ms |
| Journal / durability | WAL / `synchronous=NORMAL` |
| Foreign keys | включены, read-back = 1 |

Dirty marker существенен: измерялся незакоммиченный P4-код поверх указанной
ревизии, поэтому один commit hash не воспроизводит содержимое прогона.

## Payload

| Payload | Размер |
|---|---:|
| `state_json` | 767 bytes |
| `turns_json` | 3388 bytes |
| Текст representative dialog | 3200 characters |

## Результаты полного пути

Все значения — миллисекунды. Public-operation серии включают coroutine,
executor dispatch, connect, production PRAGMA с read-back, codec, транзакцию,
commit и close. Setup следующего lifecycle выполнялся вне timed interval.

| Серия | p50, ms | p95, ms |
|---|---:|---:|
| Cold initialization + migrations | 24.575350 | 42.274080 |
| Steady connect/configure/read-back/close | 6.512050 | 12.423565 |
| Successful CAS | 17.536350 | 25.894650 |
| `VersionConflict` | 7.023850 | 13.345190 |
| Append | 19.453200 | 34.020270 |
| Clear | 17.298950 | 27.107180 |
| Touch | 17.013050 | 30.273830 |
| Reset | 16.906200 | 27.799760 |
| Delete | 16.374850 | 21.991915 |
| Competing writers, two handles | 16.203200 | 30.075820 |

В competing-writer серии `SESSION_SQLITE_BUSY` наблюдался `0` раз из 200:
при `busy_timeout=5000 ms` обе записи успевали сериализоваться. Это не означает,
что BUSY невозможен; его numeric classification отдельно проверяется held-lock
тестом с timeout `0`.

## Конфигурация соединения

Initialization connection выполнял в порядке: `foreign_keys=ON` и read-back,
`busy_timeout=5000` и read-back, чтение текущего `journal_mode`, условный
переход в WAL с проверкой возвращённого значения, `synchronous=NORMAL` и
read-back. Steady-state connection повторял всё, кроме работы с persistent
journal mode. Effective read-back: foreign keys `1`, busy timeout `5000`,
journal mode `wal`, synchronous `1` (`NORMAL`).

## Ограничения результата

- Это machine-specific evidence, не SLA и не capacity-гарантия.
- Нельзя сравнивать эти значения напрямую с прежним bare-SQL замером: здесь
  измеряется полный adapter path и в каждой операции присутствует стоимость
  connect и трёх steady-state групп PRAGMA/read-back; initialization
  дополнительно включает переключение и read-back WAL.
- Конкурирующие writers используют два aggregate handles и разные session rows;
  scheduler, filesystem cache и состояние машины остаются host-specific.
- Прогон проверяет process restart в тестах, но не power-loss durability.
- `synchronous=NORMAL` допускает потерю последних транзакций при потере питания;
  выбор режима для стенда остаётся отдельной эксплуатационной проверкой.
- Runtime этого прогона использует SQLite 3.50.4. Официальная документация
  SQLite относит эту версию к затронутым редким WAL-reset race и указывает
  исправленный backport 3.50.7; перед стендом runtime следует обновить. Этот
  performance-прогон не является проверкой отсутствия такой corruption race:
  [SQLite WAL-reset bug](https://sqlite.org/wal.html#the_wal_reset_bug).
