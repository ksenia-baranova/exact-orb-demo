# Bootstrap composition — план реализации и карта приёмки

**Дата исходной сверки:** 2026-09-21.

**Статус:** промт 1 выполнен; промты 2–3 не начаты.

**Ветка:** `chore/bootstrap-composition`.

**HEAD исходной сверки:** `74b8423b63179b413763a4e4a03734627ebe24d8`.

**Плановое разбиение:** три содержательных промта без отдельных RED/GREEN-карточек.

## 1. Цель ветки

Ветка должна добавить одну process-local точку сборки готового application runtime.
Она связывает уже существующие production-компоненты Build Natal, вычисляет фактическую
`CalculationVersion`, владеет созданными ею executor'ами и SQLite persistence и задаёт
явный контракт остановки.

После этой ветки M1-6 получает полностью собранный runtime и занимается только FastAPI,
lifespan, request-task lifecycle, HTTP-контрактом и периодическим запуском reaper. M1-12
остаётся владельцем production/deployment policy. Таким образом, server composition не
дублируется в M1-6, а deployment-проверки не смешиваются с механикой сборки.

План не переоткрывает завершённую минимальную композицию M1-3:
[build_application_orchestrator](../../src/exact_orb/application/composition.py) остаётся
фабрикой application-координатора из готовых зависимостей. Новый bootstrap вызывает её,
но не переносит в неё инфраструктурную сборку.

## 2. Источники и исходное состояние

### 2.1. Источники истины

- [AGENTS.md](../../AGENTS.md).
- [Roadmap](roadmap.md): последовательность M1-5 → bootstrap composition → M1-6 и
  отдельный production/deployment этап M1-12.
- [ApplicationOrchestrator — план реализации](application_orchestrator_implementation_plan.md):
  завершённая минимальная composition и принятый application-контракт.
- [ADR-0006](../requirements/decisions/0006-application-orchestrator.md): роль
  `ApplicationOrchestrator`.
- [ADR-0012](../requirements/decisions/0012-bootstrap-request-response-streaming.md):
  граница bootstrap/request/response и будущий transport lifecycle.
- [Chart artifacts](../requirements/component_responsibilities/exact-orb_chart_artifacts.md):
  cache, single-flight и контракт артефактного слоя.
- [Birth-data resolution](../requirements/component_responsibilities/exact-orb_birth_data_resolution.md):
  диапазон даты рождения и семантика `today_provider`.
- [Session requirements](../requirements/component_responsibilities/exact-orb_session_requirements.md)
  и [ADR-0024](../requirements/decisions/0024-sqlite-storage-implementation.md): SQLite,
  expiry, reaper и migration seam.
- [Deployment](../architecture/deployment.md): рабочая рамка M1-12. На момент исходной
  сверки файл не отслеживается Git и сам по себе не становится действующим контрактом
  этой ветки.
- [Module boundaries](../../tests/test_module_boundaries.py): архитектурные ограничения,
  которые нельзя ослаблять ради bootstrap.

### 2.2. Подтверждённая реализационная база

| Область | Текущее состояние | Следствие для ветки |
|---|---|---|
| Application composition | [composition.py](../../src/exact_orb/application/composition.py) собирает registry, `BuildNatalHandler` и `ApplicationOrchestrator` из готовых `context`, `resolver`, `artifacts`, `clock` | Функция переиспользуется без переноса инфраструктуры внутрь неё |
| Calculation identity | [version.py](../../src/exact_orb/calculation/version.py) уже предоставляет `CalculationVersionRecord`, fingerprint и startup logging | Bootstrap вычисляет record один раз из фактической конфигурации и возвращает record вместе со строкой версии |
| Ephemeris configuration | [config.py](../../src/exact_orb/config.py) замораживает process-global путь и метод Селены; повтор тех же значений идемпотентен, несовпадение типизировано | Публичный reset не добавляется; тесты учитывают autouse-конфигурацию процесса |
| Artifact layer | [artifacts.py](../../src/exact_orb/calculation/artifacts.py) реализует cache, single-flight и `drain()` текущих leader-задач | Промт 1 закрыл component lifecycle seam; runtime вызовет его в промте 2 |
| Calculation engine | [engine.py](../../src/exact_orb/calculation/engine.py) требует положительный `slow_threshold_ms`; `NatalTechniqueAdapter` принимает синхронный calculator | Bootstrap принимает необязательный синхронный calculator override для детерминированного интеграционного теста |
| Birth resolver | [resolver.py](../../src/exact_orb/birth/resolver.py) требует границы дат и `today_provider` | Все значения становятся явными bootstrap settings/dependencies |
| Cache | [cache.py](../../src/exact_orb/calculation/cache.py) требует `max_entries` и `ttl_seconds` | Оба параметра входят в typed settings |
| SQLite | [sqlite.py](../../src/exact_orb/session/adapters/sqlite.py) открывается с внешним executor, busy timeout и необязательным migrator; `reap_expired` уже реализован | Runtime владеет executor'ом, передаёт production migrator и предоставляет one-shot reaper method |
| Session clock | [state.py](../../src/exact_orb/session/state.py) предоставляет `require_utc`, экспортированный публичным session-пакетом | Один внедрённый UTC clock используется orchestration, resolver и reaper |

Наличие этих компонентов не означает, что полный runtime уже существует. В исходной
точке нет публичной фабрики, которая собирает их вместе, выполняет startup cleanup и
гарантирует порядок остановки.

## 3. Границы владения

### 3.1. Эта ветка владеет

- строгими типизированными bootstrap settings;
- process-local `ApplicationRuntime`;
- настройкой эфемерид и чтением их фактического статуса;
- вычислением и логированием `CalculationVersionRecord` и строки версии;
- созданием реальных resolver, cache, engine, SQLite persistence, `ContextService` и
  `ApplicationOrchestrator`;
- executor'ами, созданными runtime;
- очисткой частично собранного runtime;
- one-shot `reap_expired()`;
- ожиданием текущих single-flight leader-задач через `ChartArtifactResolver.drain()`;
- тестируемым порядком штатной остановки;
- синхронизацией актуальных requirements/roadmap по изменённым контрактам.

### 3.2. M1-6 владеет

- FastAPI application и lifespan;
- прекращением приёма новых запросов;
- учётом и ожиданием всех уже начатых request tasks, включая отменённые запросы;
- вызовом готового runtime из lifespan;
- периодическим расписанием `runtime.reap_expired()`;
- HTTP/cookie/SSE/transport-метриками.

M1-6 не создаёт повторно resolver, cache, engine, SQLite, context или orchestrator.

### 3.3. M1-12 владеет

- production fail-fast, если `EphemerisStatus.mode != "files"`;
- запретом небезопасного DEBUG-режима для публичного развёртывания;
- переменными окружения, deployment manifest и health/readiness policy;
- операционным расписанием и retention policy поверх one-shot reaper.

До M1-12 fallback mode остаётся допустимым механизмом библиотечной сборки. Текущий
`pytest.exit` защищает только тестовый стенд и не считается production-политикой.

### 3.4. Вне скоупа

- FastAPI, HTTP, cookies, SSE, UI и CLI;
- LLM/Agent Runtime и интерпретация;
- admission control и load shedding;
- сеть, очереди или отдельные сервисы;
- новый публичный reset process-global ephemeris configuration;
- фоновый reaper и планировщик;
- изменение схемы SQLite;
- переработка calculation/session-компонентов за пределами явно названных seams;
- production deployment policy M1-12.

## 4. Целевой публичный контракт

### 4.1. Модуль и фабрика

Новый модуль: `src/exact_orb/application/bootstrap.py`.

Он предоставляет три публичных имени:

```python
BootstrapSettings
ApplicationRuntime
build_application_runtime(...)
```

Импорт через `exact_orb.application.bootstrap` является публичным путём. Экспорт из
`exact_orb.application.__init__` не обязателен и не должен добавляться, если он создаёт
eager imports инфраструктуры или нарушает текущую границу пакета.

Фабрика принимает:

```python
async def build_application_runtime(
    *,
    settings: BootstrapSettings,
    places: PlaceCatalog,
    clock: Callable[[], datetime],
    natal_calculator: Callable[..., NatalChart] = calculate_natal,
) -> ApplicationRuntime: ...
```

Точная аннотация calculator должна повторять существующий контракт
`NatalTechniqueAdapter`, не вводя второй несовместимый protocol. `places` передаётся как
порт; bootstrap не читает каталог из файла и не выбирает concrete catalog adapter.

### 4.2. Strict settings

`BootstrapSettings` фиксирует только значения, необходимые создаваемым компонентам:

| Поле | Назначение и обязательная проверка |
|---|---|
| `ephemeris_path` | Путь к эфемеридным файлам; без скрытого production default |
| `selena_method` | Явный метод Селены; валидируется существующим config-контрактом |
| `session_db_path` | Форма пути SQLite; родительский каталог не создаётся и не обязан существовать во время чистой валидации |
| `sqlite_busy_timeout_ms` | Правила зеркалируют SQLite validator, включая запрет `bool` как `int` |
| `sqlite_max_workers` | Строго положительное целое, `bool` запрещён |
| `min_birth_date` | Нижняя поддерживаемая граница даты рождения |
| `max_birth_date` | Верхняя конфигурационная граница даты рождения; не раньше `min_birth_date` |
| `cache_max_entries` | Обязательное строго положительное целое, `bool` запрещён |
| `cache_ttl_seconds` | Обязательное конечное положительное число |
| `engine_slow_threshold_ms` | Обязательное конечное положительное число |
| `degraded_log_interval_s` | Обязательное конечное положительное число |

Модель запрещает неявное coercion и лишние поля. Предварительная проверка должна
зеркалировать действующие validators компонентов, а не придумывать другие пределы.
Все ошибки settings возникают до создания executor'ов и открытия SQLite.

`body_ids`, `ephemeris_flags`, размер calculation executor и migration function не
являются настройками ветки:

- CalculationVersion и engine используют фактические `DEFAULT_BODY_IDS` и
  `DEFAULT_EPHEMERIS_FLAGS`.
- Calculation executor создаётся с `max_workers=2`, как требует действующий runtime
  контракт.
- SQLite получает `resolve_unknown_birth_time_for_migration`.

### 4.3. Единый источник времени

Каждый вызов внедрённого `clock` проходит `require_utc`. Наивный `datetime` должен
отклоняться на публичной границе до использования значения.

Из clock выводится `utc_today`: `clock().date()` после UTC-проверки. Его использует
`BirthDataResolver.today_provider`. Это намеренное изменение относительно локального
`date.today()`: верхняя динамическая граница определяется UTC-датой процесса. Контракт
должен быть явно отражён в birth-data requirements. Поддержка пользовательской локальной
даты потребует отдельного продуктового решения и не входит в эту ветку.

Тот же clock используется:

- `ApplicationOrchestrator`;
- `ContextService`;
- `BirthDataResolver.today_provider`;
- `ApplicationRuntime.reap_expired(now=None)`.

### 4.4. ApplicationRuntime

Runtime предоставляет read-only поля:

| Поле | Публичная цель |
|---|---|
| `orchestrator` | Выполнение application commands |
| `context` | Явный session lifecycle для транспорта |
| `artifacts` | Cache metrics и lifecycle seam для M1-6 и приёмочных тестов |
| `ephemeris_status` | Фактический startup status для будущих health/readiness проверок |
| `calculation_version_record` | Один уже вычисленный record без повторного хэширования `*.se1` |
| `calculation_version` | Каноническая строка версии для сессий и наблюдаемости |

Persistence и оба executor'а остаются внутренними owned resources. Runtime также
реализует:

```python
async def drain(self) -> None: ...
async def reap_expired(self, *, now: datetime | None = None) -> int: ...
async def aclose(self) -> None: ...
async def __aenter__(self) -> ApplicationRuntime: ...
async def __aexit__(...) -> None: ...
```

`reap_expired(now=None)` получает время из внедрённого UTC clock. Явно переданный `now`
тоже проходит UTC-валидацию.

`aclose()` идемпотентен. После закрытия runtime не обещает повторное выполнение команд.
Отдельный public close/gate у cache, resolver или orchestrator не добавляется.

## 5. Порядок startup

Порядок является частью плана и тестируемого контракта:

1. Валидировать весь `BootstrapSettings` без захвата ресурсов.
2. Вызвать `configure_ephemeris(ephemeris_path, selena_method)`.
3. Прочитать фактические `EphemerisStatus.path` и имя метода Селены.
4. Получить фактические `DEFAULT_BODY_IDS` и `DEFAULT_EPHEMERIS_FLAGS`.
5. Вычислить `CalculationVersionRecord` по фактическим значениям.
6. Получить каноническую строку `calculation_version`.
7. Записать startup log версии.
8. Только после этого начать создавать owned resources под `AsyncExitStack` или
   эквивалентным механизмом обратной очистки:
   1. SQLite executor и его cleanup;
   2. `SqliteSessionPersistence.open(...)` с busy timeout и
      `resolve_unknown_birth_time_for_migration`;
   3. calculation executor и его cleanup;
   4. `NatalTechniqueAdapter(calculator=natal_calculator)` и `EngineService`;
   5. `InMemoryCalculationCache` и `ChartArtifactResolver`;
   6. `BirthDataResolver` и `ContextService`;
   7. существующий `build_application_orchestrator(...)`;
   8. передать ownership успешно собранному `ApplicationRuntime`.

Дешёвые и потенциально падающие действия предшествуют owned resources. Тем не менее
ошибка `SqliteSessionPersistence.open()` происходит уже после создания SQLite executor,
поэтому partial-start cleanup остаётся обязательным.

Повторная сборка с теми же process-global ephemeris path/method допустима. Сборка с
другим путём или методом поднимает существующую typed configuration error. Bootstrap не
обходит и не размораживает это правило.

## 6. Контракт drain и остановки

### 6.1. ChartArtifactResolver.drain()

`ChartArtifactResolver.drain()` входит в эту ветку как единственное намеренное изменение
поведения существующего calculation-компонента. Запрет на попутный рефакторинг относится
ко всем остальным изменениям компонента.

Метод:

- ожидает leader-задачи single-flight, существующие на момент drain;
- не принимает новые lifecycle-решения и не добавляет глобальный gate;
- не отменяет leader-задачи;
- допускает завершение через success, cancellation или exception и не оставляет
  необработанное исключение detached task;
- безопасен, когда активных leader-задач нет.

Приёмка фиксирует наблюдаемое поведение, а не конкретное приватное устройство. Текущий
`_inflight` может использоваться, если детерминированный тест доказывает, что drain не
возвращается до фактического `Task.done()`. Отдельный task set с удалением в
`add_done_callback` вводится только если без него этот контракт не выполняется. Само
наличие дополнительного набора не является AC.

### 6.2. Полная граница остановки

Полный порядок с транспортом будет таким:

1. M1-6 прекращает принимать новые запросы.
2. M1-6 дожидается всех уже начатых request tasks, включая отменённые запросы.
3. `ApplicationRuntime.aclose()` вызывает `runtime.drain()` и ждёт detached
   single-flight leaders.
4. После drain закрывается calculation executor.
5. Последним закрывается SQLite executor.

Внутренний protected commit уже удерживается и ожидается `ApplicationOrchestrator`; новый
commit-drain не добавляется. Ветка обязана доказать runtime-часть порядка, а M1-6 позднее
добавит transport/request boundary.

## 7. Критерии приёмки

### AC-1. Полный runtime

Фабрика возвращает `ApplicationRuntime` с реальными `orchestrator`, `context`,
`artifacts`, SQLite persistence, calculation engine и всеми объявленными metadata.

### AC-2. Реальный Build Natal и cache

Один реальный Build Natal проходит через runtime и SQLite. Первый расчёт даёт artifact
cache miss и успешный put; повтор того же расчёта даёт hit. Наблюдение выполняется через
публичное `runtime.artifacts`, без monkeypatch приватных полей.

### AC-3. Фактическая CalculationVersion

Runtime возвращает тот же record и fingerprint, которые получаются из фактического
ephemeris status, метода Селены, `DEFAULT_BODY_IDS` и `DEFAULT_EPHEMERIS_FLAGS`. Версия
не задаётся тестовой константой и не пересчитывается при чтении поля.

Под pytest нельзя фиксировать полный fingerprint: autouse fixture использует
репозиторный `ephe` и `true_perigee`, тогда как production default может отличаться.
Проверяются префикс, непустота и стабильность двух сборок в одном процессе.

### AC-4. Внешний PlaceCatalog

Переданный `PlaceCatalog` используется resolver по identity/наблюдаемому вызову.
Bootstrap не читает конкретный JSON/SQLite-каталог.

### AC-5. Предварительная валидация

Каждое невалидное setting, включая `bool` вместо integer, неfinite или неположительные
таймауты/TTL/thresholds и обратный диапазон дат, отклоняется до создания executor'ов.
Тест содержит положительный контроль, что валидные значения проходят эту стадию.

### AC-6. Process-global ephemeris contract

Повтор той же конфигурации успешен. Несовпадающие path и method поднимают соответствующие
существующие typed errors. Публичный reset не появляется.

Тесты сборки либо передают autouse-значения (`repo ephe`, `true_perigee`), либо имеют
`@pytest.mark.no_ephemeris_autoinit`. Mismatch не используется как trigger cleanup-теста.

### AC-7. Partial-start cleanup

`tmp_path / "missing-parent" / "session.sqlite3"` проходит чистую проверку формы пути,
но падает внутри SQLite initialization после создания backend/executor.
`SqliteSessionPersistence.open()` **поднимает** публичный `StateWriteError` с
`error_code == "SESSION_SQLITE_OPEN_FAILED"`. Bootstrap закрывает уже созданный executor
и повторно поднимает тот же exception без замены сырым `sqlite3.OperationalError`.

### AC-8. Штатное закрытие без активных операций

`aclose()` и async context manager закрывают owned resources в заявленном порядке и
повторный `aclose()` безопасен. Этот AC не объявляется доказательством сценария живого
отменённого waiter: он закрывается отдельно AC-9.

### AC-9. Отменённый waiter и живой leader

Через публичный `natal_calculator` seam расчёт удерживается детерминированным barrier.
Запрос-waiter отменяется, но shielded leader продолжает работу. `runtime.aclose()` не
завершается, пока barrier не отпущен и leader task фактически не закончен; только затем
закрываются executors. В тесте нет `sleep`, а timeout используется только как защита от
зависания.

### AC-10. SQLite migration seam

Runtime открывает SQLite с `resolve_unknown_birth_time_for_migration`. Проверка доказывает
передачу существующего seam и не воспроизводит всю migration suite.

### AC-11. Runtime metadata

Публичные `ephemeris_status`, `calculation_version_record` и `calculation_version`
согласованы друг с другом и доступны после сборки без обращения к приватным полям.

### AC-12. Application registry

Собранный orchestrator поддерживает точный текущий registry application commands через
существующий `build_application_orchestrator`. Bootstrap не создаёт альтернативный
handler registry.

## 8. Сквозной приёмочный сценарий Build Natal

Тест AC-2 задаёт однозначные application outcomes:

1. Создать новую сессию с `state_version == 0`.
2. Выполнить первый `BuildNatalCommand` и полностью дождаться результата.
3. Ожидать `ApplicationCommitted(state_version=1)`.
4. Ожидать `misses == 1`, `put_ok == 1`, `hits == 0`.
5. Повторить ту же команду для той же сессии после завершения первого вызова.
6. Второй `execute()` сам загружает актуальный snapshot версии 1.
7. Ожидать `ApplicationCommitted(state_version=2)`.
8. Ожидать `hits == 1`, `misses == 1`, `put_ok == 1`.

`ApplicationAlreadyApplied` здесь не ожидается: это последовательный повтор с новым
актуальным expected version, а не потеря подтверждения или конкурентный CAS. Сценарии
`AlreadyApplied` и `Superseded` уже принадлежат существующей orchestration/CAS suite.

## 9. Разбиение на три промта

Будущие карточки создаются в новом каталоге, не изменяя исторические промты:

```text
prompts/2026-09-21/bootstrap-composition/
  01-bootstrap-contract-and-resolver-drain.md
  02-build-application-runtime.md
  03-bootstrap-integration-acceptance-and-status.md
```

Каждый промт содержит production/documentation change вместе с необходимыми тестами.
Отдельные RED/GREEN-промты и обязательный предварительный падающий запуск не создаются.

### 9.1. Промт 1 — контракт и resolver drain — выполнен

**Предмет доказательства:** новая lifecycle-примитива и документальные границы владения.

Работы:

- синхронизировать roadmap/актуальные requirements: bootstrap находится между M1-5 и
  M1-6; M1-6 потребляет runtime; M1-12 владеет fallback/DEBUG production policy;
- зафиксировать UTC-date semantics birth resolver;
- зафиксировать, что one-shot reaper принадлежит runtime, а scheduler — M1-6;
- реализовать `ChartArtifactResolver.drain()`;
- сузить устаревшую шапку `Known debt until CalculationVersion exists` в
  `artifacts.py`, поскольку этот файл уже находится в allowlist промта;
- добавить детерминированный resolver-тест с управляемым асинхронным
  `CalculationEnginePort`, `asyncio.Event` и проверкой фактического завершения leader.

Границы:

- runtime/settings ещё не создаются;
- не добавляются gate, cancel-all или resolver close;
- не меняются cache semantics и artifact codec;
- тест работает с async port напрямую. Его нельзя заменять синхронным
  `natal_calculator`: это разные контрактные seams.

Результат промта: lifecycle-примитива доказана независимо от большой сборки; актуальные
документы больше не назначают композицию одновременно bootstrap-ветке и M1-6.

Фактическая проверка 2026-09-21: resolver `51 passed`, module boundaries
`36 passed`, связанный resolver/codec/cache/version набор `153 passed`.
PlantUML source прошёл структурную проверку; PNG не перегенерирован, потому что
локальные `plantuml` и `java` отсутствуют.

### 9.2. Промт 2 — сборка ApplicationRuntime

**Зависимость:** промт 1 завершён; M1-5 предоставляет согласованный `PlaceCatalog` port/
adapter, но bootstrap продолжает принимать только порт.

**Унаследованная lifecycle-проверка:** до реализации `aclose()` добавить
детерминированный тест отмены самого `drain()` одновременно с ошибкой leader
через loop exception handler. Поведение shield-логгера зависит от версии
CPython; cleanup меняется только при наблюдаемом шуме. Этот случай намеренно
не объявлен закрытым тестами промта 1.

**Предмет доказательства:** корректная сборка, startup identity и владение ресурсами.

Работы:

- добавить `BootstrapSettings`, `ApplicationRuntime`, `build_application_runtime`;
- реализовать строгую предварительную валидацию;
- реализовать точный startup order из §5;
- передать optional синхронный `natal_calculator` в `NatalTechniqueAdapter`;
- открыть SQLite с migration seam;
- собрать реальный cache/resolver/engine/context/orchestrator;
- вернуть публичные `artifacts` и metadata;
- реализовать `reap_expired`, `drain`, `aclose` и async context manager;
- обеспечить обратную очистку partial startup;
- сузить устаревшую `Known debt` шапку в `engine.py`;
- добавить unit/component tests для AC-1, AC-3–AC-8, AC-10–AC-12.

Partial-start cleanup принадлежит только этому промту. Stable trigger — SQLite path с
несуществующим родительским каталогом; ожидание — поднятый `StateWriteError`, как указано
в AC-7.

Результат промта: полная production assembly доступна и доказывает normal shutdown без
активных операций, идемпотентное закрытие и partial-start cleanup. Этот этап реализует
порядок остановки, но ещё не объявляет доказанным ожидание живого leader после отмены
waiter; такое сквозное доказательство принадлежит промту 3.

### 9.3. Промт 3 — сквозная приёмка и статусы

**Зависимость:** промты 1–2 завершены.

**Предмет доказательства:** поведение собранного runtime, которое нельзя подтвердить на
уровне отдельных компонентов.

Работы:

- добавить реальный последовательный Build Natal сценарий из §8 с SQLite и cache
  miss → hit;
- добавить runtime shutdown сценарий AC-9 с отменённым waiter и живым leader;
- для AC-9 использовать синхронный `natal_calculator` с thread-safe barrier/bridge,
  поскольку `NatalTechniqueAdapter` отклоняет coroutine `calculate`;
- не дублировать startup failure и normal no-active shutdown тесты промта 2;
- обновить status/journal плана и затронутых актуальных документов по фактически
  пройденной приёмке;
- выполнить целевые, связанные и полный pytest.

Результат промта: AC-2 и AC-9 доказаны через публичную поверхность runtime, после чего
ветка может считаться готовой для потребления M1-6.

## 10. Матрица покрытия

| Критерий | Основной промт | Проверка |
|---|---:|---|
| AC-1 Полный runtime | 2 | Публичные поля и реальные component types |
| AC-2 Build Natal/cache | 3 | Два последовательных execute, точные outcomes и counters |
| AC-3 CalculationVersion | 2 | Record/fingerprint из фактической конфигурации |
| AC-4 Injected PlaceCatalog | 2 | Публичный fake/spy port и positive use |
| AC-5 Prevalidation | 2 | Параметризованные invalid settings плюс positive control |
| AC-6 Ephemeris freeze | 2 | Same-config success и typed mismatch errors |
| AC-7 Partial cleanup | 2 | Missing-parent SQLite path, exact `StateWriteError`, executor shutdown |
| AC-8 Normal close | 2 | No-active close order, idempotence, async context manager |
| AC-9 Cancelled waiter/live leader | 3 | Synchronous calculator barrier и runtime close ordering |
| AC-10 Migration seam | 2 | Передача production migrator |
| AC-11 Metadata | 2 | Public record/status/version consistency |
| AC-12 Registry | 2 | Existing composition builder/current supported commands |
| Resolver drain primitive | 1 | Async engine port + Event, no sleep |

## 11. Тестовая стратегия

### 11.1. Общие правила

- Тестируется публичное наблюдаемое поведение. Приватное состояние допустимо только там,
  где иначе нельзя доказать lifecycle-инвариант executor/task cleanup.
- Для конкурентности применяются `asyncio.Event`, barrier и fake clock; `sleep` запрещён.
- Timeout служит только защитой от зависания.
- Интеграционные тесты собирают реальные компоненты проверяемого пути. Мокаются только
  внешние/листовые seams: clock, PlaceCatalog и calculator barrier.
- Autouse ephemeris fixture учитывается явно; значения полного fingerprint не хардкодятся.
- `tests/test_module_boundaries.py` не ослабляется. Если новый composition root требует
  разрешённого импорта, сначала доказывается, что это именно composition-root boundary,
  а не обход архитектуры.

### 11.2. Последовательность проверок

Промт 1:

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_chart_artifact_resolver.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_module_boundaries.py -q
```

Промт 2:

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_composition.py tests/test_calculation_version.py tests/test_ephemeris_runtime_config.py tests/session/test_sqlite.py tests/test_module_boundaries.py -q
```

Промт 3:

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap_integration.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_chart_artifact_resolver.py tests/test_calculation_version.py tests/test_ephemeris_runtime_config.py tests/session -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

Для каждой карточки дополнительно выполняются:

```powershell
git diff --check
git status --short
```

Отсутствующие project gates вроде Ruff, mypy или coverage не вводятся этой веткой.

## 12. Документационные изменения в реализации

Меняются только документы, контракт которых действительно затронут:

- `roadmap.md` — отдельная bootstrap-задача и потребительская роль M1-6;
- chart-artifact requirements — `drain()` и граница single-flight shutdown;
- birth-data requirements — UTC-date semantics;
- session/runtime requirements — one-shot reaper и владелец scheduler;
- этот план — фактический journal и матрица AC.

Устаревшие шапки в `artifacts.py` и `engine.py` не удаляются целиком. Их нужно сузить:
bootstrap path после ветки получает реальную CalculationVersion, тогда как CLI и
отдельные тестовые стенды могут по-прежнему собирать компоненты с упрощённой версией.

Исторические `prompts/**` не редактируются. Deployment-документ меняется только в M1-12
или отдельной явно согласованной документационной задаче.

## 13. Риски и контроль границ

| Риск | Контроль |
|---|---|
| Два владельца composition | Roadmap явно назначает bootstrap единственным владельцем runtime; M1-6 только потребляет его |
| Скрытые defaults в production | Все обязательные constructor values входят в strict settings; engine defaults участвуют в CalculationVersion |
| Локальная дата сервера меняет birth support | UTC semantics записана как намеренный контракт и покрыта fake clock |
| Startup оставляет executor после SQLite failure | Обратная очистка регистрируется сразу после создания каждого owned resource; AC-7 использует post-acquisition failure |
| Отменённый HTTP waiter оставляет живой leader | Resolver `drain()` плюс request tracking M1-6; runtime-часть проверяет AC-9 |
| Тест меряет ephemeris fixture вместо cleanup | Cleanup trigger — SQLite open failure, не config mismatch |
| Fingerprint зависит от pytest Selena method | Проверяется структура и стабильность, а не production-specific hash |
| Тесты закрепляют приватную реализацию | `artifacts` и calculator seam публичны; отдельный task set не предписан |
| Reaper никогда не вызывается | Runtime предоставляет one-shot operation; периодический вызов остаётся явным deliverable M1-6 |
| Fallback попадает в production | Отдельный fail-fast остаётся именованным deliverable M1-12, а не растворяется в bootstrap |

## 14. Условия готовности и завершения

### 14.1. Готовность к выполнению

- текущая ветка — `chore/bootstrap-composition`;
- M1-5 завершён или его публичный `PlaceCatalog` contract стабилен и доступен;
- нет неразрешённого изменения `ApplicationOrchestrator`, SQLite или CalculationVersion
  contract;
- unrelated изменения в рабочем дереве зафиксированы и не попадают в allowlist;
- три новые prompt-карточки созданы из этого плана, а не путём правки исторических.

### 14.2. Definition of done ветки

- выполнены AC-1–AC-12;
- prompt 1 доказывает resolver lifecycle primitive;
- prompt 2 доказывает assembly, startup identity и ресурсное владение;
- prompt 3 доказывает реальный Build Natal/cache и cancelled-waiter shutdown;
- актуальные requirements и roadmap согласованы с фактической реализацией;
- целевые и связанные тесты прошли;
- полный pytest прошёл без новых failures;
- `git diff --check` чист;
- в diff нет HTTP, UI, LLM, admission или deployment policy;
- M1-6 может создать lifespan, используя один готовый `ApplicationRuntime`.

## 15. Журнал выполнения

| Этап | Статус | Подтверждение |
|---|---|---|
| План | Подготовлен 2026-09-21 | Зафиксированы контракт, владельцы, AC-1–AC-12 и три review boundary |
| Промт 1 | Выполнен 2026-09-21 | Добавлен `ChartArtifactResolver.drain()`; синхронизированы roadmap v3.4 и актуальные requirements; 51 target, 36 boundary и 153 related tests passed |
| Промт 2 | Не начат | Заполняется после реализации и фактических запусков |
| Промт 3 | Не начат | Заполняется после реализации и фактических запусков |

Исходная подготовка плана не меняла production-код и тесты. Фактические
изменения и проверки промта 1 записаны выше; команды промтов 2–3 ещё не
запускались.
