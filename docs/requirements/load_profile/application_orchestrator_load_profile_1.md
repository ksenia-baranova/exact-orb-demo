# ApplicationOrchestrator — штатный load profile 1

**Статус:** PASS.
**Дата прогона:** 2026-09-19T13:20:15.945293+00:00.

## Результат для менеджеров

Application-ядро завершило весь заданный поток 5 операций в секунду:
подано и завершено 300 операций, необработанных исключений нет,
drain составил 0.001 с. Все ответы были
полезными штатными исходами сохранения или CAS-конфликта.

## Команда и окружение

```powershell
.\.venv\Scripts\python.exe -B scripts/bench_application_orchestrator.py --profile normal --rate 5 --duration 60 --operations 300 --log-level INFO --report docs/project_management/application_orchestrator_load_profile_1.md
```

| Параметр | Значение |
|---|---|
| Git HEAD | `d62b0060fa4adc04bb9f337add922720ee58c69d` |
| Рабочее дерево | dirty |
| Python | `3.14.0` |
| Платформа | `Windows-11-10.0.26200-SP0` |
| CPU | `Intel64 Family 6 Model 186 Stepping 2, GenuineIntel`; logical CPUs: 16 |
| Ephemeris | `C:\Users\KateUser\PycharmProjects\exact-orb-recovered\ephe`; mode `files` |
| Logging | requested `INFO`, effective `INFO` |
| Profile | `normal` |

## Состав стенда

Реальные компоненты: `ApplicationOrchestrator`, `BuildNatalHandler`,
`ContextService`, `SqliteSessionPersistence`, `BirthDataResolver`,
`ChartArtifactResolver`, `EngineService`, `InMemoryCalculationCache` и
Swiss calculation backend. HTTP/transport заменён прямым `execute`.
Calculation fixture 10.3 предоставляет resolver/engine/cache; его InMemory
session stack в измеряемом пути не используется.

Test-only wrapper `PairedLoadBarrierPersistence` полностью делегирует
SQLite. Для пар общих сессий он выпускает оба `touch` через
`asyncio.Barrier(2)` только после завершения реальных чтений. CAS outcomes
не подменяются. Admission controller отсутствует и профилю 1 не требуется.

Session setup, открытие SQLite, инициализация эфемерид и один warm-up
выполнены до запуска таймера. Verification reads и dialog measurement
выполнены после drain. Executor и временная база закрыты после проверок.

## Подача и завершение

| Метрика | Значение |
|---|---:|
| Настроенный входящий поток | 5.000 ops/s |
| Плановая длительность подачи | 60.000 с |
| Фактическое окно подачи | 60.006 с |
| Подано | 300 |
| Завершено к остановке подачи | 300 |
| Завершено после drain | 300 |
| Drain | 0.001 с |
| Полное время подачи + drain | 60.007 с |
| Завершённый throughput по окну подачи | 4.999 ops/s |
| Максимальное отставание таймера подачи | 640.348 мс |
| Peak active | 12 |
| Active после drain | 0 |
| Необработанные исключения | 0 |

Подача выполнена парами по таймеру: две операции каждые 0.4 с при 5 RPS.
Это средний входящий поток 5 RPS; barrier используется для доказательства
CAS-пересечения общих пар, а не для задания скорости.

## Результаты операций

| ApplicationResult | Количество |
|---|---:|
| `ApplicationAlreadyApplied` | 30 |
| `ApplicationCommitted` | 240 |
| `ApplicationSuperseded` | 30 |

### Status triples

| orch / handler / context | Количество |
|---|---:|
| `SUCCESS / SUCCESS / ALREADY_APPLIED` | 30 |
| `SUCCESS / SUCCESS / COMMITTED` | 240 |
| `SUPERSEDED / SUCCESS / SUPERSEDED` | 30 |

### По типу сессии

| Сценарий | Количество |
|---|---:|
| `distinct → ApplicationCommitted` | 180 |
| `shared_different_intent → ApplicationCommitted` | 30 |
| `shared_different_intent → ApplicationSuperseded` | 30 |
| `shared_same_intent → ApplicationAlreadyApplied` | 30 |
| `shared_same_intent → ApplicationCommitted` | 30 |

## Lifecycle при effective INFO

| Метрика | Значение |
|---|---:|
| `application_operation_started` | 300 |
| `application_operation_finished` | 300 |
| Started без terminal | 0 |
| Terminal без started | 0 |
| Duplicate started/terminal | 0 |
| Ошибки разбора records | 0 |

Множества lifecycle `run_id` совпали с поданными операциями и с `run_id`
возвращённых результатов; payload команд и session ID для подсчёта не нужны.

## Cache и CAS/state integrity

| Метрика | Значение |
|---|---:|
| Cache hits | 6 (2.000%) |
| Cache misses | 294 (98.000%) |
| Cache put ok | 266 |
| Shared load barriers armed/released | 60 / 60 |
| AlreadyApplied | 30 |
| Superseded | 30 |
| Проверено persisted sessions | 186 |
| Нарушения версии/state | 0 |

Для каждой сессии итоговая `state_version` равна числу её результатов
`Committed`; chart state совпадает с command/artifact последнего commit.
Это проверка отсутствия lost update после завершения всех операций.

## Оценка overhead dialog snapshot

Заполненный dialog: 20 turns, 20000 символов.
Размеры вычислены как UTF-8 bytes компактных JSON-представлений state и
массива dialog из реально возвращённого `SessionSnapshot`.

| Размер | Bytes |
|---|---:|
| State | 755 |
| Пустой dialog | 2 |
| Заполненный dialog | 24041 |
| Доля dialog в state + dialog | 96.955% |

| Touch | Samples | Mean, ms | Min, ms | Max, ms | Spread, ms |
|---|---:|---:|---:|---:|---:|
| Пустой dialog | 100 | 8.110 | 3.243 | 19.277 | 16.034 |
| 20 × 1000 chars | 100 | 8.449 | 3.350 | 18.675 | 15.325 |

Разница средних: 0.338 мс (4.172%). Это сравнительная оценка
полного `SessionPersistence.touch`: общий таймер включает SQLite transaction,
decode и scheduler overhead, поэтому разницу нельзя приписать только dialog.

## Критерии приёмки

| Критерий | Результат |
|---|---|
| Настроено не менее 5 RPS | PASS |
| Подача длилась не менее 60 секунд | PASS |
| Подано не менее 300 операций | PASS |
| Все поданные операции завершены | PASS |
| После drain active = 0 | PASS |
| Наблюдалось одновременное выполнение | PASS |
| Необработанных исключений нет | PASS |
| Все outcomes полезны и допустимы | PASS |
| Lifecycle started/terminal полон и уникален | PASS |
| Cache hit/miss учёл все Handler success | PASS |
| Обе CAS-классификации наблюдались | PASS |
| Все load barriers завершены | PASS |
| Persisted версии и state согласованы | PASS |
| Logging effective INFO | PASS |

## Ограничения

- Это application/core profile без HTTP, client и deployment overhead.
- Admission controller отсутствует; конечный active/queue profile относится к 10.7.
- Отдельный latency SLA и p95/p99 не устанавливались.
- Измерения зависят от машины и текущего рабочего дерева; они не являются SLA.
- Последовательная повторная доставка вне конкурентной пары остаётся отдельной
  семантикой без idempotency key и может создать новый commit.
