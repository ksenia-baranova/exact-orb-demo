# M1-5.2: сохранённая карта в сессии — implementation plan

**Дата исходной сверки:** 2026-09-27.

**Ревизия:** 2026-09-27 — порядок работ, проверки отрицательных требований
и журнал свидетельств уточнены после ревью плана.

**Статус:** промты 01–08 выполнены 2026-09-27; компонентная приёмка M1-5.2
закрыта, публичный HTTP bootstrap остаётся M1-6.

**Ветка:** существующая `feat/session-stored-chart`; исходный HEAD `e7327bf`.
Рабочее дерево содержит несвязанные и ещё не зафиксированные изменения:
каждый промт проверяет текущую базу заново и сохраняет чужую работу.

**Разбиение:** восемь последовательных промтов. Этот документ задаёт их
границы и приёмку; отдельные prompt-файлы создаются по следующему запросу.
Промт включает реализацию и необходимые для неё тесты. Отдельной церемонии
RED/GREEN нет.

## 1. Цель и результат ветки

После подтверждённого `BuildNatal` полный `ChartArtifact` сохраняется как
`StoredChart` внутри агрегата сессии. `ApplicationOrchestrator` остаётся
единственным владельцем вызова `ContextService.save`: Handler получает
артефакт, подготавливает полную `StateDelta` и возвращает её, но не пишет в
session storage. CAS одной операцией сохраняет или отклоняет состояние и
карту. Повторный вход в живую сессию получает тот же артефакт из snapshot
после рестарта процесса и при пустом расчётном кэше.

Результат ветки — рабочие session contracts, InMemory/SQLite persistence,
запись карты при build, чистая проекция `application/session_view`,
компонентные и сквозные тесты. HTTP bootstrap, cookie и публичный DTO
потребляют эти компоненты в M1-6.

## 2. Источники и исходное состояние

Приоритет: [AGENTS.md](../../../AGENTS.md),
[ADR-0041](../../requirements/decisions/0041-stored-chart-in-session.md),
[спецификация поведения сессии](../../requirements/session/stored-chart-session-behavior.md),
действующие [session requirements](../../requirements/component_responsibilities/exact-orb_session_requirements.md)
и [roadmap](../roadmap.md). Поведение по сценариям сверяется с
[session sequence](../../sequence_diagrams/session/README.md) и
[Build Natal sequence](../../sequence_diagrams/build_natal/README.md).
Приложенный черновик `variant-d-action-plan.md` использован для порядка работ,
но при расхождении действует текущая спецификация: ERROR-лог
`chart_unavailable` принадлежит будущему transport, а совместимость
golden-фикстуры проверяется декодированием и идентичностью без побайтового
сравнения с новой сериализацией.

| Область | Код на исходной сверке | Что требуется |
|---|---|---|
| Сессия | `SessionState` хранит ввод, разрешённые данные и `ChartRef`; `StateDelta` содержит три поля, `SessionSnapshot` — state и dialog | Добавить `StoredChart`, обязательное четвёртое поле дельты и согласованный snapshot |
| Persistence | InMemory держит state/dialog под одним lock; SQLite имеет session component v1 | Сохранять chart в том же агрегате, добавить SQLite v2 и проверку схемы |
| Build | Handler вызывает `ensure_chart`, затем возвращает дельту без карты; Orchestrator уже выполняет CAS | Добавить `to_stored` и карту в дельту, не меняя владельца commit |
| Восстановление | `application/session_view` отсутствует | Добавить чистую проекцию snapshot без resolver, cache и engine calls |
| Проверки | Есть session conformance, SQLite golden v1/v2, application integration и module boundaries | Расширить их по новым инвариантам, сохранить старые frozen-данные без перегенерации |

`state_json.payload_version` остаётся 2. SQLite session component получает
миграцию v2, но это другая версия. Старые SQLite-тесты, вставляющие
`base_chart` без дочерней карты в уже открытую новую базу, после изменения
контракта должны ожидать отказ чтения агрегата; frozen payload-файлы при
этом не переписываются.

## 3. Границы реализации

- Не вводить отдельное хранилище или TTL карты, restore-handler,
  `GET /charts/current`, новую координацию через resolver и прямой доступ
  transport к доменному resolver.
- Сессионные модели и адаптеры трактуют payload как opaque `bytes` и не
  импортируют расчётный кодек. `ChartArtifactResolver.to_stored` кодирует,
  Handler создаёт `StoredChart`, Orchestrator подтверждает запись через CAS.
- `session_view` получает готовый `SessionSnapshot` и текущую версию расчёта;
  она не загружает сессию, не пишет журнал и не выполняет I/O.
- `AlreadyApplied` не переписывает победившую карту, `Superseded` не
  применяет дельту, `StateCommitFailed` не доказывает отсутствие записи.
  Точный retry сохраняет исходную expected version и ту же дельту.
- Сжатый payload ограничен 1…1 048 576 байт в `StoredChart`; SQL `CHECK`
  защищает запись повторно. Не добавлять третий лимит в resolver.
- Полные DEBUG-сообщения сохраняются на разрешённых границах, но
  `StoredChart` показывается только форматом, ключом, версией и размером.
  Исключения подготовки карты и форматированный traceback не содержат байт
  payload или Pydantic `input_value`.
- Отложены до M1-6: FastAPI, middleware/cookie, HTTP DTO и статусы,
  транспортные INFO-пары для bootstrap и ERROR-лог `chart_unavailable`.
  UI и синхронизация вкладок push-событиями сюда не входят.

## 4. Карта промтов и зависимостей

| ID | Срез | Зависимость | Основная приёмка |
|---|---|---|---|
| 01 | Артефактный формат, `to_stored` и frozen payload | Текущий код | Кодирование, безопасная ошибка, golden decode |
| 02 | Session contracts и сквозная адаптация конструкторов | 01 | Инварианты моделей и `RESET_DELTA` |
| 03 | BuildNatal → `StoredChart` → Orchestrator CAS на fake-портах | 01–02 | Передача полной дельты владельцу commit, типизированные отказы, журнал |
| 04 | Чистая `session_view` | 01–02 | `empty`/`chart_ready`/`chart_unavailable`, stale, границы |
| 05 | InMemory aggregate | 02 | CAS/touch/reset/delete/reaper под одним lock |
| 06 | SQLite v2 migration и проверка схемы | 02 | Атомарная миграция, удаление прежних сессий, rollback |
| 07 | SQLite aggregate, `ContextService.load` и DEBUG | 05–06 | Атомарный CAS/touch, структурные отказы, conformance |
| 08 | Сквозная приёмка и согласование документов | 01–07 | Рестарт, две вкладки, неуспех, полный pytest |

Рекомендуемый порядок: `01 → 02 → 03 → 04 → 05 → 06 → 07 → 08`.
Промты 03 и 04 независимы друг от друга и от SQLite: после контрактов их
можно выполнять раньше адаптеров. SQLite-интеграция Handler относится к 08.
После 02 связанные наборы могут оставаться красными из-за ещё не переведённых
потребителей; application unit tests получают шанс стать зелёными после 03–04,
полный набор — после 07–08. Каждая карточка заканчивается зелёными **своими**
целевыми тестами и списком оставшихся падений с причиной; статус прежних
запусков не переносится на новый состав дерева. Полный `pytest` обязателен
в 08. Временные default-значения, compatibility aliases и ослабление тестов
границ ради промежуточного зелёного состояния не нужны.

## 5. Карточки промтов

### Промт 01 — формат карты и артефактный порт

**Результат:** расчётный слой может детерминированно подготовить сохранённый
payload, не зная сессионной модели.

**Файлы:** `src/exact_orb/calculation/codec.py`,
`calculation/artifacts.py`, `calculation/errors.py`,
`application/ports.py`; связанные
`tests/test_chart_artifact_codec.py`, `tests/test_chart_artifact_resolver.py`,
`tests/application/stubs.py`, `tests/application/orchestrator_fakes.py` и
новая frozen-фикстура под `tests/golden/`.

**Работа:**

- Определить текущий `payload_format=1` и набор поддерживаемых форматов
  рядом с кодеком. `ChartArtifactPort.to_stored(artifact)` и resolver
  возвращают формат и те же детерминированные gzip JSON байты, что
  существующий кодек кэша; в session storage они ничего не пишут.
- Ожидаемые ошибки сериализации переводить в
  `ChartArtifactEncodingError(CHART_ARTIFACT_ENCODE_FAILED)` с безопасным
  текстом и подавленной форматируемой цепочкой (`from None`).
- Зафиксировать один payload формата 1 вместе с ожидаемыми ключом, версией,
  spec и расчётным входом. Golden-тест **декодирует** старые байты и
  проверяет идентичность; он не сравнивает их с новой сериализацией.
  Детерминизм текущего кодирования проверяется отдельно на одном артефакте.
- Дополнить существующие fake-порты методом `to_stored`, не добавляя
  сессионную модель в расчётный слой.

**Готово, когда:** целевые codec/resolver tests проходят; прежний
`ensure_chart`, cache hit/miss и single-flight не изменили поведение.

### Промт 02 — сессионный контракт

**Результат:** immutable контракты выражают полную замену state+chart.

**Файлы:** `src/exact_orb/session/state.py`, `session/persistence.py`,
`session/store.py`, `session/__init__.py`, `tests/session/test_state.py`,
`tests/session/test_contracts.py`; существующие тестовые конструкторы
`StateDelta`/`SessionSnapshot` и общие fixtures только по необходимости.

**Работа:**

- Перед изменением пересчитать использования `StateDelta(` и
  `SessionSnapshot(` в коде и тестах. На исходной сверке найдено 23 и 14
  вхождений соответственно, включая намеренно невалидные конструкторы
  негативных тестов; их не исправлять механически.
- Добавить `StoredChart` с положительным форматом, непустыми ключом/версией
  и размером `payload` 1…1 048 576 байт. Session layer не декодирует bytes.
- Сделать `base_chart_payload` обязательным nullable-полем `StateDelta`;
  все четыре поля задаются вместе или все равны `None`. `RESET_DELTA`
  содержит четыре `None`; `matches_intent` по-прежнему не сравнивает байты.
- Добавить обязательное поле `SessionSnapshot.chart` и инвариант
  `state.base_chart is None` ⇔ `chart is None`. Обновить конструкторы без
  совместимых default-полей: populated snapshot требует chart.
- Описать CAS state+chart в порте, не меняя текущий публичный метод.

**Готово, когда:** `test_state.py` и `test_contracts.py` проходят, включая
границы размера, reset и обе стороны snapshot-инварианта. Упавшие до
перевода адаптеров/application тесты перечислены, а не объявлены успешными.

### Промт 03 — запись карты при BuildNatal

**Результат:** Handler готовит `StoredChart`; только Orchestrator передаёт
полную дельту в `ContextService.save`. Здесь граница проверяется на fake-портах,
без зависимости от ещё не готового SQLite.

**Файлы:** `src/exact_orb/application/handlers/build_natal.py`,
`application/results.py`, при необходимости узкая внутренняя ошибка
application-слоя и formatter для `StateDelta`; связанные
`tests/application/test_build_natal_handler.py`,
`test_build_natal_logging.py`, `test_application_results.py`,
тесты Orchestrator с `RecordingContext` и fake-порты.

**Работа:**

- После `ensure_chart` вызвать `to_stored`, создать `StoredChart` из
  артефакта и полную `StateDelta`. Валидатор `BuildNatalSuccess` сверяет
  ключ и версию envelope с артефактом вместе с действующими spec/input
  проверками. Handler не импортирует кодек и не вызывает `save`.
- Отказ кодирования/модели до CAS превращать в безопасный
  `StoredChartPreparationError(ENCODE_FAILED | PAYLOAD_SIZE_INVALID |
  ENVELOPE_INVALID)` с `raise ... from None`. Orchestrator сохраняет
  действующий `ApplicationInternalFailure` с `UNEXPECTED_FAILURE/LOADED`
  без вызова save; его код не переписывается. Положительный контроль успешного
  пути показывает, что именно Orchestrator вызывает `RecordingContext.save`
  с полной дельтой, возвращённой Handler.
- INFO содержит send/receive для `to_stored` с peer/type/run_id; исключение
  завершает путь terminal/error без ложного receive. DEBUG не содержит
  `StoredChart.payload`. Тест реального пути Handler → Orchestrator
  форматирует `logger.exception` и проверяет отсутствие `input_value`,
  исходного текста валидации и префикса payload.

**Готово, когда:** успешный build передаёт полную дельту в `save` через
Orchestrator, отказ до CAS не вызывает `save`; целевые application unit tests
и существующий `test_module_boundaries.py` проходят без ослабления правил.
Фактическая SQLite-запись пары и `Superseded` проверяются в промте 08.

### Промт 04 — чистая проекция `session_view`

**Результат:** snapshot превращается в компонентное представление для
будущего transport без нового пути координации.

**Файлы:** новый `src/exact_orb/application/session_view.py`, новый
`tests/application/test_session_view.py`,
`tests/test_module_boundaries.py`.

**Работа:**

- Реализовать `empty`, `chart_ready {artifact, chart_stale}` и
  `chart_unavailable {birth_input, canonical_place, safe_reason}` по §4
  спецификации. Проверять формат, строгий decode, равенство envelope,
  spec/расчётного входа и **только затем** текущую `CalculationVersion`.
  Дополнительный пересчёт ключа из состояния не нужен: это следует из
  внутренних проверок `ChartArtifact` и сравнений проекции.
- Проверить каждый достижимый `safe_reason`: unsupported format, три
  decode-ошибки, несовпадение ключа/версии/spec/входа. Проекция не пишет
  ERROR, не вызывает resolver/cache/engine и не меняет snapshot.
- Добавить регрессию прямых импортов с положительным контролем: кодек,
  ключи и `calculation.types` разрешены; concrete resolver/cache/engine,
  session I/O, adapters и transport запрещены. Транзитивный импорт
  расчётных моделей через `calculation.types` допустим; чистота означает
  отсутствие I/O и вызовов расчёта.

**Готово, когда:** все варианты проекции и граница модулей проверены;
ERROR-лог вызывающего transport остаётся в M1-6.

### Промт 05 — InMemory aggregate

**Результат:** InMemory хранит состояние, диалог и карту под прежним общим
lock и отдаёт согласованный snapshot.

**Файлы:** `src/exact_orb/session/adapters/in_memory.py`,
`tests/session/conformance.py`, `tests/session/test_in_memory.py`.

**Работа:**

- CAS одной секцией меняет state и chart, конфликт не пишет ни одно из них.
  При reset очистить chart и dialog; delete и reaper удаляют chart вместе
  с родительской сессией.
- Touch под тем же lock возвращает state/dialog/chart и продлевает TTL без
  изменения `state_version` и предметного содержимого.
- Расширить общий conformance: новая карта, конфликт, `AlreadyApplied` без
  переписывания победителя, reset, delete, reaper, touch. Использовать
  общие fixtures, не размножая бинарные данные по тестам.

**Готово, когда:** InMemory tests и применимая к нему часть conformance
проходят; SQLite-часть ожидает промты 06–07.

**Уточнение исполнения 2026-09-27:** упоминание reaper в lifecycle относится
к SQLite. Действующие session requirements (§ P2/P4) оставляют истёкшую
InMemory-запись физически на месте; публичного `reap_expired` у этого адаптера
нет. В 05 проверяются логическое истечение и удаление карты при `delete`, а
SQLite reaper с дочерней картой проверяется в 07.

### Промт 06 — SQLite schema v2 и миграция

**Результат:** SQLite открывается только с проверенной схемой session
component v2; переход с v1 атомарен.

**Файлы:** `src/exact_orb/session/adapters/sqlite.py`,
`tests/session/test_sqlite.py`.

**Работа:**

- Добавить `session_charts` точно по §9 спецификации: одна дочерняя строка,
  `ON DELETE CASCADE`, ограничения формата, ключа, версии и размера BLOB.
- Миграция v2 в одной транзакции создаёт таблицу, удаляет **все** прежние
  сессии с диалогами и фиксирует запись в `schema_migrations`; при отказе
  схема и данные остаются исходными. Другие компоненты базы не затрагивать.
- После миграции и при каждом открытии v2 проверять форму таблицы,
  обязательные `CHECK`, FK и согласованность с ledger; несовместимость —
  `SESSION_SQLITE_SCHEMA_INCOMPATIBLE` до обслуживания сессий.
- Не менять `_STATE_PAYLOAD_VERSION=2` и frozen v1/v2 payload-файлы.
  Скорректировать тесты, которые ожидали чтения старых сессий после
  теперь намеренно очищающей миграции.

**Готово, когда:** тесты schema/migration/rollback проходят. Проверки
прикладного CAS и touch относятся к промту 07.

### Промт 07 — SQLite aggregate и сессионный журнал

**Результат:** одна SQLite-транзакция атомарно пишет state+chart и читает
согласованный snapshot; ошибка структуры имеет типизированный исход.

**Файлы:** `src/exact_orb/session/adapters/sqlite.py`, при необходимости
`session/context.py` и существующий formatter компонентного журнала;
`tests/session/conformance.py`, `tests/session/test_sqlite.py`,
`tests/session/test_context.py`.

**Работа:**

- В `_sync_compare_and_set` вместе с state записывать, заменять или удалять
  chart. Конфликт версий, неподтверждённый commit и точный retry сохраняют
  действующую классификацию; частичная пара state/chart недопустима.
- `_sync_touch` читает chart в той же read-and-renew транзакции. Отсутствие
  дочерней строки при `base_chart` и лишняя строка при пустом `base_chart`
  дают `StateReadError(SESSION_SQLITE_DATA_CORRUPT)` до commit touch;
  ожидаемый Pydantic `ValidationError` snapshot адаптер переводит туда же.
  `ContextService.load` отдаёт `StateReadFailed`, не создавая сессию заново.
- Reset удаляет chart с dialog, delete/reaper используют FK cascade.
  DEBUG-проекции `StoredChart` содержат только формат, ключ, версию и размер,
  никогда бинарный payload.
- Тесты инъецируют оба вида рассогласования, отказ commit и проверяют
  отсутствие частичной записи и непродлённый TTL при ошибке touch.

**Готово, когда:** общий session conformance проходит для обоих адаптеров;
SQLite schema, corruption, lifecycle и ContextService tests зелёные.

### Промт 08 — сквозная приёмка и закрытие ветки

**Результат:** компонентная ветка доказана по пользовательским сценариям,
документы соответствуют реализованному пути.

**Файлы:** существующие
`tests/application/test_application_bootstrap_integration.py`,
`test_orchestrator_sqlite_integration.py`, связанные session/application
tests; только затронутые актуальные requirements, ADR и sequence diagrams
при обнаруженном расхождении. Roadmap получает фактический статус после
успешной приёмки.

**Работа и приёмка:**

1. Build → закрыть runtime → новый runtime с тем же SQLite и пустым кэшем
   → `ContextService.load` + `session_view`: тот же артефакт, без вызова
   resolver/cache/engine; другая версия даёт `chart_stale`.
2. Пустая первая сессия и повторный вход после reset дают `empty`. Отказ
   первого build до CAS оставляет пустую сессию; повторный вход не
   восстанавливает неуспешный ввод.
3. Две вкладки одной сессии: B подтверждает N+1, A видит её только после
   следующего load; отдельно конкурентные команды с одним expected version
   через управляемые barrier/Event, без `sleep` как доказательства порядка.
4. Неопределённый commit и точный retry показывают только согласованную
   пару либо её отсутствие; `AlreadyApplied` не перезаписывает победителя.
5. Реальный путь Handler → Orchestrator → SQLite подтверждает атомарную
   запись пары; `Superseded` не пишет карту. Это интеграционная часть приёмки
   раннего промта 03.
6. Сопоставить существенные стрелки sequence с INFO send/receive или
   terminal/error и DEBUG. Сверить действующие документы с поведением;
   не переписывать не затронутые документы и исторические `prompts/**`.

**Готово, когда:** целевые и связанные тесты, затем полный локальный
`pytest` проходят; требования S-01–S-12 на компонентной границе закрыты.
Публичный HTTP bootstrap проверяется отдельно в M1-6.

## 6. Покрытие требований и сценариев

| Требования / сценарий | Промты |
|---|---|
| S-01–S-03: пустая сессия, TTL, согласованный load | 02, 05–08; cookie остаётся M1-6 |
| S-04, S-08–S-09: restore, stale, unavailable, структурный отказ | 01–02, 04, 07–08 |
| S-05–S-07: build, полная delta, CAS, retry/AlreadyApplied | 02–03, 05, 07–08 |
| S-10: две вкладки и конкурентные команды | 03, 07–08 |
| S-11–S-12: reset/delete/reaper и миграция | 05–08 |
| Sequence 001/002: первый build и повторный вход | 03–04, 08 |
| Sequence 003/005: commit uncertainty и CAS | 03, 05, 07–08 |
| Sequence 004/006/007: reset, две вкладки, первая неудача | 03–05, 07–08 |
| INFO/DEBUG, отсутствие payload в traceback | 03, 07–08 |

**Свидетельство закрытия S-01–S-12 на компонентной границе:**

| Требование | Исполняемое свидетельство | Граница |
|---|---|---|
| S-01–S-03 | `test_empty_first_return_failed_build_and_reset_remain_empty`; общий `tests/session/conformance.py` и `tests/session/test_context.py` проверяют create, TTL и согласованный load | Генерация ID и cookie остаются transport M1-6. |
| S-04, S-08–S-09 | `test_runtime_restart_restores_identical_chart_without_calculation`, `tests/application/test_session_view.py`, `test_structural_chart_corruption_blocks_touch_and_context_load` | Restore использует snapshot; transport ERROR при `chart_unavailable` остаётся M1-6. |
| S-05–S-07 | `test_runtime_build_natal_miss_then_hit_commits_same_session`, две SQLite CAS-гонки, `test_chart_write_failure_rolls_back_parent_and_retry_commits_pair`, `test_lost_chart_commit_acknowledgement_preserves_pair_and_retry_winner` | Неопределённый commit читается как unknown до нового load. |
| S-10 | `test_second_tab_commit_appears_on_first_tabs_next_load` и две гонки в `test_orchestrator_sqlite_integration.py` с `asyncio.Barrier` | Автоматическая доставка между вкладками не требуется. |
| S-11–S-12 | `tests/session/test_in_memory.py`, `tests/session/test_sqlite.py`: reset/delete/reaper, `test_v1_to_v2_clears_legacy_sessions_and_preserves_foreign_component`, `test_v2_migration_failure_after_delete_rolls_back_every_change` | Проверен локальный SQLite, без сетевого deployment. |

Sequence 001/005/006/007 и Build Natal sequence сверены с реальным путём
Handler → Orchestrator → ContextService → SQLite: INFO-пары `load`, `handle`,
`resolve_birth_data`, `ensure_chart`, `to_stored`, `save` и terminal outcome
наблюдаются в интеграционных тестах. DEBUG показывает вход/выход компонентов
и безопасную проекцию `StoredChart`. Sequence 002/003/004 содержат будущие
стрелки transport bootstrap; их HTTP-журнал проверяется в M1-6. Действующие
ADR-0041 и спецификация §8–10 не потребовали ревизии.

## 7. Чувствительность отрицательных проверок

Для каждого правила ниже сначала нужен положительный контроль, доказывающий,
что проверяемый путь действительно исполняется. Затем в пределах указанного
промта временно внести **одно намеренное нарушение** или управляемую инъекцию
отказа и показать, что соответствующий тест падает по нужной причине.
Вернуть код в требуемое состояние и повторить тест с успешным результатом.
Мутанты не входят в итоговый diff; точные команды и исходы записываются в
журнал §8. Отдельных промтов и дублирующих тестов ради этой процедуры нет.

| Отрицательное правило | Промт | Положительный контроль и чувствительность |
|---|---|---|
| Конфликт CAS не записывает карту | 05, затем 07 для SQLite | Подтверждённый CAS меняет state+chart; временная запись chart на конфликте должна обрушить conformance |
| `AlreadyApplied` не перезаписывает победителя | 05/07, итог 08 | Первый commit сохраняет победителя; временная перезапись при точном retry должна провалить проверку сохранённой пары |
| Отказ подготовки до CAS не вызывает `save` | 03 | Успешный build вызывает `RecordingContext.save` через Orchestrator; временный `save` на ошибке должен провалить тест |
| Restore не вызывает resolver/cache/engine | 04 и 08 | `chart_ready` получен из snapshot; 04 ловит временный запрещённый прямой импорт, 08 — временный вызов одного из портов через инструментированный runtime |
| Повреждённый snapshot не продлевает TTL | 07 | Валидный touch продлевает TTL; временный renew до проверки целостности должен провалить тест с fake clock |
| Откат неуспешной миграции сохраняет исходные данные | 06 | Успешная миграция создаёт v2; управляемый отказ после удаления сессий, до фиксации ledger, должен доказать rollback |
| Payload не попадает в журнал и traceback | 03, при SQLite-журнале 07 | Терминальное событие ошибки присутствует; временное раскрытие маркерных байт в исключении или DEBUG должно провалить проверку форматированного журнала |

Для общего conformance отрицательные правила проверяются на обоих адаптерах.
Инъекция или мутант доказывают чувствительность конкретного теста, а не
корректность всего набора. Конкурентный порядок подтверждается barrier/Event
и наблюдаемыми исходами; timeout служит только защитой от зависания.

## 8. Статус, журнал свидетельств и передача в M1-6

Статус обновляется после каждого промта. «Пройдено» относится только к
указанному checkout и составу тестов; после изменения контрактов старый
результат не считается подтверждением нового дерева. Журнал ниже содержит
фактические запуски промтов 01–09b; команды после таблицы служат образцом для
повторной проверки.

| Промт | Статус | Целевые проверки | Связанные проверки и открытое окно |
|---|---|---|---|
| 01 | Выполнен | Codec/resolver: 88 passed | Cache/integration/port/boundary: 97 passed; application/CalculationVersion: 954 passed. Запись в session storage остаётся промтам 02–08. |
| 02 | Выполнен | `test_state.py` + `test_contracts.py`: 110 passed | Связанный набор: 327 passed; 1499 session/application тестов собраны. InMemory и Handler ещё требуют промтов 05 и 03; независимое ревью границ остаётся отдельным контрольным шагом. |
| 03 | Выполнен | Handler/Orchestrator/logging/contracts/boundary: 820 passed | Расширенный application-набор: 949 passed, 14 failed на ещё не переведённых InMemory/SQLite адаптерах; SQLite aggregate и restart остаются 05–08. |
| 04 | Выполнен | `test_session_view.py` + module boundaries: 62 passed | Связанный codec/session/application-набор: 262 passed; чувствительность границы подтверждена временным запрещённым импортом. InMemory/SQLite и restart остаются 05–08. |
| 05 | Выполнен | `test_in_memory.py`: 124 passed | Связанный session/application/boundary-набор: 312 passed. SQLite `touch` ещё не передаёт chart; schema/adapter/reaper и restart остаются 06–08. |
| 06 | Выполнен | SQLite schema/migration/constraints: 26 passed | Связанный SQLite/boundary-набор: 71 passed. Полный SQLite-файл остановлен после 83 passed, 12 failed на прежнем `touch` без `chart`; aggregate, reaper и restart остаются 07–08. |
| 07 | Выполнен | SQLite/ContextService адресно: 12 passed; session и module boundaries: 661 passed | SQLite CAS/touch/chart, отказ commit, повреждение, reset/delete/reaper и безопасные DEBUG-проекции подтверждены. Дополнительный application-набор: 240 passed, 1 failed на устаревшем ожидании `to_stored` в сквозном тесте карточки 08. |
| 08 | Выполнен | Сквозная выборка: 8 passed; поведенческий мутант: 1 expected failure, после удаления 1 passed | Session/application/boundary: 1600 passed; полный локальный `pytest`: 2649 passed. M1-6 ещё должен проверить HTTP bootstrap/cookie и транспортный журнал. |
| 09a | Выполнен | Resolver/Handler/logging/Orchestrator: 108 passed | Application/resolver/module boundaries: 1040 passed; полный локальный `pytest`: 2652 passed. Восстановлена классификация ADR-0027; frozen payload и документы статуса остаются 09b. |
| 09b | Выполнен | Codec и frozen payload: 39 passed; старая `.bin` byte-for-byte сохранена | Session/application/codec/resolver/module boundaries: 1695 passed; полный локальный `pytest`: 2656 passed. HTTP bootstrap и транспорт остаются M1-6. |

Журнал заполняется фактическими запусками, включая намеренно падающий мутант
и последующий зелёный повтор. Для каждого запуска записать команду целиком,
дату и HEAD, точный состав тестов, код возврата, результат и **предел
свидетельства**: какие пути и свойства эта проверка подтверждает, какие ещё
не проверены. Падения от незавершённых следующих промтов фиксировать отдельно
от дефектов текущего среза.

| Дата / HEAD | Промт и состав дерева | Команда / набор | Код и фактический результат | Предел свидетельства / оставшееся |
|---|---|---|---|---|
| 2026-09-27 / `e7327bf` | 01, первый состав | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_chart_artifact_codec.py tests/test_chart_artifact_resolver.py -q` | 0; 88 passed | Подтверждены frozen decode, формат, `to_stored`, безопасная ошибка и прежние resolver-сценарии; session persistence не проверяется. |
| 2026-09-27 / `e7327bf` | 01, до правки теста сигнатур | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_calculation_cache.py tests/test_calculation_block_integration.py tests/application/test_contracts.py tests/test_module_boundaries.py -q` | 1; 96 passed, 1 failed: тест требовал async от нового синхронного `to_stored` | Дефект теста соответствия порта; реализация `to_stored` по контракту синхронна. |
| 2026-09-27 / `e7327bf` | 01, исправленный тест сигнатур | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_calculation_cache.py tests/test_calculation_block_integration.py tests/application/test_contracts.py tests/test_module_boundaries.py -q` | 0; 97 passed | Подтверждены прежние cache hit/miss, расчётная интеграция и границы импортов; запись карты в сессию не проверяется. |
| 2026-09-27 / `e7327bf` | 01, расширенный application-набор | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_calculation_version.py -q` | 1; 950 passed, 4 errors при создании `tmp_path_factory` | Проверки поведения, которые исполнились, прошли; 4 place-catalog integration tests не стартовали из-за отказа доступа к системному temp. |
| 2026-09-27 / `e7327bf` | 01, temp внутри checkout | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-01 tests/application tests/test_calculation_version.py -q` | 1; 950 passed, 4 errors и отказ cleanup временного каталога | Право доступа к временному каталогу ограничено песочницей даже в checkout; результат не считать полным проходом. |
| 2026-09-27 / `e7327bf` | 01, тот же набор вне песочницы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-01-escalated tests/application tests/test_calculation_version.py -q` | 0; 954 passed | Подтверждена совместимость текущих application и CalculationVersion тестов; full `pytest`, session contracts и persistence остаются до промтов 02–08. Временные каталоги удалены. |
| 2026-09-27 / `e7327bf` | 01, финальный состав | `git diff --check` | 0; ошибок пробелов нет, есть предупреждения Git о будущей замене LF на CRLF в существующих файлах | Проверены отслеживаемые изменения рабочего дерева; новые prompt/plan/golden-файлы дополнительно проверены чтением и целевым тестом, но команда `git diff --check` их не охватывает. |
| 2026-09-27 / `e7327bf` | 02, первая версия контрактных тестов | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_state.py tests/session/test_contracts.py -q` | 0; 109 passed | Проверены модели и инварианты до отдельного теста игнорирования chart bytes в `matches_intent`; adapter/Handler пути не проверены. |
| 2026-09-27 / `e7327bf` | 02, добавлен тест намерения | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_state.py tests/session/test_contracts.py -q` | 0; 110 passed | Подтверждены границы 1…1 048 576 байт, обязательность полей, 14 частичных дельт, reset, обе стороны snapshot-инварианта и сравнение намерения без payload. |
| 2026-09-27 / `e7327bf` | 02, связанные fake-пути | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_context.py tests/application/test_contracts.py tests/application/test_orchestrator_routing.py tests/application/test_orchestrator_load.py tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_concurrency.py tests/application/test_orchestrator_commit.py tests/test_module_boundaries.py -q` | 0; 217 passed | Подтверждены обновлённые тестовые конструкторы и прежние портовые/архитектурные границы; реальные persistence adapters и Handler не охвачены. |
| 2026-09-27 / `e7327bf` | 02, InMemory до промта 05 | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py -q --maxfail=3` | 1; 88 passed, 3 failed, затем остановка | Три failure показывают, что `InMemorySessionPersistence.touch` ещё создаёт `SessionSnapshot` без обязательного `chart`; полный набор не выполнялся. Это ожидаемый долг промта 05. |
| 2026-09-27 / `e7327bf` | 02, Handler до промта 03 | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_build_natal_handler.py -q --maxfail=3` | 1; 3 failed, затем остановка | Успешные пути Handler ещё создают `StateDelta` без обязательного `base_chart_payload`; полный файл не выполнялся. Это ожидаемый долг промта 03. |
| 2026-09-27 / `e7327bf` | 02, проверка сбора | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session tests/application --collect-only -q` | 0; 1499 tests collected | Подтверждён сбор session/application после адаптации тестовых конструкторов; не подтверждено исполнение этих 1499 тестов. |
| 2026-09-27 / `e7327bf` | 02, итоговый связанный набор | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_state.py tests/session/test_contracts.py tests/session/test_context.py tests/application/test_contracts.py tests/application/test_orchestrator_routing.py tests/application/test_orchestrator_load.py tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_concurrency.py tests/application/test_orchestrator_commit.py tests/test_module_boundaries.py -q` | 0; 327 passed | Зелёные тесты текущего контрактного среза и fake-путей; не включает реальные адаптеры, успешный Handler, SQLite или restart. |
| 2026-09-27 / `e7327bf` | 02, финальная проверка diff | `git diff --check` | 0; ошибок пробелов нет, Git сообщает о возможной конверсии LF в CRLF в существующих файлах | Отслеживаемый diff корректен по пробелам; untracked prompt/plan/fixture не охватываются этой Git-командой. |
| 2026-09-27 / `e9e3145` | 03, новые отказные проверки | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_stored_chart_build.py -q --tb=line --show-capture=no` | 0; 6 passed | Fake-порты подтверждают передачу той же дельты в save и отсутствие save при ошибках кодирования, размера и envelope; SQLite/InMemory здесь не используются. |
| 2026-09-27 / `e9e3145` | 03, текущий целевой состав | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_build_natal_handler.py tests/application/test_build_natal_logging.py tests/application/test_build_natal_integration.py tests/application/test_stored_chart_build.py tests/application/test_contracts.py tests/application/test_application_results.py tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py tests/test_module_boundaries.py -q --tb=line --show-capture=no` | 0; 820 passed | Подтверждены Handler, Orchestrator на fake-портах, реальный расчётный путь, безопасный traceback, INFO/DEBUG и границы импортов; реальный session aggregate ещё не проверен. |
| 2026-09-27 / `e9e3145` | 03, расширенный application-набор в песочнице | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_module_boundaries.py -q --tb=short --maxfail=15` | 1; 897 passed, 12 failed, 3 errors; остановка на 15 отказах | Три error вызваны запретом доступа к системному pytest temp. Большинство failure до Handler вызваны `SessionSnapshot` без chart в старых адаптерах; состав дерева тогда ещё включал старое ожидание количества DEBUG-сообщений в `test_build_natal_integration.py`, которое затем исправлено. Этот запуск не подтверждает полный набор. |
| 2026-09-27 / `e9e3145` | 03, расширенный application-набор вне песочницы после исправления ожиданий журнала | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_module_boundaries.py -q --tb=line --show-capture=no` | 1; 949 passed, 14 failed | Все оставшиеся failure — application-интеграции с InMemory/SQLite: адаптеры ещё строят `SessionSnapshot` без обязательного chart; это работа промтов 05–07. Запуск не доказывает сквозное сохранение или восстановление. |
| 2026-09-27 / `e9e3145` | 03, финальный diff | `git diff --check` | 0; ошибок пробелов нет, Git предупредил о возможной конверсии LF в CRLF | Проверен tracked diff; новый prompt и новый тест дополнительно проверены на хвостовые пробелы, но не охватываются этой Git-командой до добавления в индекс. |
| 2026-09-27 / `156bd30` | 04, первая версия тестовой spec-фикстуры | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_session_view.py tests/test_module_boundaries.py -q --tb=short` | 1; 57 passed, 5 failed | Тестовый `house_system="K"` не проходил валидацию `NatalChartSpec` до вызова проекции; это ошибка тестовой фикстуры, не отказ реализации. Заменён на допустимое отличие `near_interception_threshold`. |
| 2026-09-27 / `156bd30` | 04, исправленная фикстура | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_session_view.py tests/test_module_boundaries.py -q --tb=short` | 0; 62 passed | Проверены empty/ready/stale, восемь safe_reason, порядок, отсутствие мутации и ERROR, а также граница прямых импортов. Реальные storage и runtime-порты здесь не участвуют. |
| 2026-09-27 / `156bd30` | 04, первая связанная проверка | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_session_view.py tests/application/test_contracts.py tests/application/test_build_natal_handler.py tests/application/test_stored_chart_build.py tests/test_chart_artifact_codec.py tests/session/test_state.py tests/session/test_contracts.py tests/test_module_boundaries.py -q --tb=short` | 0; 262 passed | Совместимость проекции с codec, session contracts и BuildNatal на fake-портах; InMemory/SQLite и restart не проверены. |
| 2026-09-27 / `156bd30` | 04, временный запрещённый прямой импорт `calculation.engine` | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_module_boundaries.py::test_application_session_view_has_only_pure_contract_direct_imports -q --tb=short` | 1; 1 failed по `exact_orb.calculation.engine` | Подтверждена чувствительность теста к прямому импорту движка; мутант сразу удалён и в итоговый diff не входит. Это не доказывает отсутствие любых динамических вызовов через будущий runtime. |
| 2026-09-27 / `156bd30` | 04, после удаления мутанта | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_module_boundaries.py::test_application_session_view_has_only_pure_contract_direct_imports -q --tb=short` | 0; 1 passed | Подтверждено восстановление границы в рабочем дереве; затем тест усилен проверкой, что из `session.persistence` импортируется только `SessionSnapshot`. |
| 2026-09-27 / `156bd30` | 04, финальный связанный состав с усиленной границей | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_session_view.py tests/application/test_contracts.py tests/application/test_build_natal_handler.py tests/application/test_stored_chart_build.py tests/test_chart_artifact_codec.py tests/session/test_state.py tests/session/test_contracts.py tests/test_module_boundaries.py -q --tb=short` | 0; 262 passed | Подтверждены результаты карточки 04 и совместимость затронутых контрактов на финальном коде. Полный `pytest`, адаптеры сессии, restart и transport остаются вне этого набора. |
| 2026-09-27 / `156bd30` | 04, финальные пробелы | `git diff --check`; `rg -n '[ \t]+$' prompts/2026-09-27/session-stored-chart/04-session-view.md src/exact_orb/application/session_view.py tests/application/test_session_view.py tests/test_module_boundaries.py` | 0 для Git; 1 для `rg` без совпадений | Tracked diff без ошибок пробелов; `rg` дополнительно проверил хвостовые пробелы в новых файлах. Содержимое untracked-файлов `git diff --check` не охватывает. |
| 2026-09-27 / `4eb0f51` | 05, исходный InMemory до изменений | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py -q --maxfail=5 --tb=short` | 1; 88 passed, 5 failed, остановка на 5 | Пять отказов возникают при `touch`: прежний InMemory adapter создаёт `SessionSnapshot` без обязательного `chart`. Полный исходный набор не запускался. |
| 2026-09-27 / `4eb0f51` | 05, первая реализация InMemory и conformance | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py -q --tb=short` | 0; 122 passed | Подтверждены state+chart CAS, конфликт, `AlreadyApplied`, touch, reset/delete и физическая очистка chart по InMemory; дополнительные проверки перестроения и пустого touch добавлены позже. |
| 2026-09-27 / `4eb0f51` | 05, мутант: проигравшая дельта записывает chart при VersionConflict | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py::TestInMemorySessionPersistence::test_cas_conflict_returns_atomic_actual_without_mutation tests/session/test_in_memory.py::TestInMemorySessionPersistence::test_already_applied_keeps_first_committed_chart -q --tb=short` | 1; 3 failed | Два conflict-варианта и точный retry с `AlreadyApplied` обнаруживают перезапись карты проигравшим. Положительный CAS с `CHART` был подтверждён в целевом наборе. Мутант удалён. |
| 2026-09-27 / `4eb0f51` | 05, после удаления мутанта | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py::TestInMemorySessionPersistence::test_cas_conflict_returns_atomic_actual_without_mutation tests/session/test_in_memory.py::TestInMemorySessionPersistence::test_already_applied_keeps_first_committed_chart -q --tb=short` | 0; 3 passed | Подтверждена чувствительность отрицательных правил и возвращение корректной конфликтной ветки; SQLite не охвачен. |
| 2026-09-27 / `4eb0f51` | 05, первый связанный состав | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py tests/session/test_context.py tests/application/test_build_natal_integration.py tests/application/test_build_natal_handler.py tests/application/test_orchestrator_commit.py tests/test_module_boundaries.py -q --tb=short` | 0; 310 passed | Совместимость InMemory с ContextService, BuildNatal и модульными границами; до двух дополнительных conformance-проверок. |
| 2026-09-27 / `4eb0f51` | 05, добавлены перестроение и пустой touch | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py -q --tb=short` | 0; 124 passed | Подтверждены все сценарии карточки на InMemory, включая замену карты и отсутствие chart в новой пустой сессии. SQLite и restart не охвачены. |
| 2026-09-27 / `4eb0f51` | 05, адресный SQLite-контроль будущего среза | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py::TestSqliteSessionPersistence::test_populated_cas_commits_version_and_chart_reference -q --tb=short` | 1; 1 failed | Ожидаемый долг 06–07: SQLite `touch` ещё создаёт `SessionSnapshot` без `chart`; этот запуск не опровергает InMemory-результат и не подтверждает SQLite aggregate. |
| 2026-09-27 / `4eb0f51` | 05, финальный связанный состав | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py tests/session/test_context.py tests/application/test_build_natal_integration.py tests/application/test_build_natal_handler.py tests/application/test_orchestrator_commit.py tests/test_module_boundaries.py -q --tb=short` | 0; 312 passed | Подтверждены изменения InMemory, общие контракты, ContextService и затронутые application-пути на финальном коде; SQLite schema/adapter/reaper и restart остаются 06–08. |
| 2026-09-27 / `4eb0f51` | 05, пробелы | `git diff --check`; `rg -n '[ \t]+$' prompts/2026-09-27/session-stored-chart/05-in-memory-aggregate.md src/exact_orb/session/adapters/in_memory.py tests/session/conformance.py tests/session/test_in_memory.py` | 0 для Git; 1 для `rg` без совпадений | Tracked diff без ошибок пробелов; новый untracked prompt дополнительно проверен `rg`. Полный `pytest` сознательно оставлен до завершения 06–08. |
| 2026-09-27 / `5d3a369` | 06, целевая схема и миграция | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py -q -k "schema or migration or chart_table or initialization or foreign_migration or database_constraints" --tb=short` | 0; 26 passed, 230 deselected | Новая база, v1→v2, очистка старых сессий/диалогов, чужой компонент, rollback после удаления, несовместимые schema/ledger, SQL constraints и повторное открытие. Прикладной aggregate CAS/touch не охвачен. |
| 2026-09-27 / `5d3a369` | 06, расширенный SQLite-файл | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py -q --maxfail=12 --tb=line --show-capture=no` | 1; 83 passed, 12 failed; остановка на 12 отказах | Все 12 показанных отказов связаны с тем, что SQLite `touch` создаёт `SessionSnapshot` без обязательного `chart` (строка 1042); это работа 07. Полный SQLite-файл не завершился; этот запуск не подтверждает aggregate/reaper. |
| 2026-09-27 / `5d3a369` | 06, связанный набор и модульные границы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py tests/test_module_boundaries.py -q -k "schema or migration or chart_table or initialization or foreign_migration or database_constraints or module_boundaries" --tb=short` | 0; 71 passed, 230 deselected | Схема/миграция и действующие модульные границы проходят вместе; SQLite CAS/touch, полный `pytest` и restart остаются вне проверки. |
| 2026-09-27 / `5d3a369` | 06, пробелы | `git diff --check`; `rg -n '[ \t]+$' prompts/2026-09-27/session-stored-chart/06-sqlite-schema-v2-migration.md src/exact_orb/session/adapters/sqlite.py tests/session/test_sqlite.py docs/project_management/implementation_plans/session_stored_chart_implementation_plan.md` | 0 для Git; 1 для `rg` без совпадений | Tracked diff без ошибок пробелов; новый untracked prompt дополнительно проверен `rg`. Git предупредил о возможной конверсии LF в CRLF. |
| 2026-09-27 / `1235d36` | 07, первый полный SQLite-файл | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py -q --maxfail=12 --tb=line --show-capture=no` | 1; 255 passed, 1 failed | Старый frozen-v1-payload тест вставлял заполненное state в v2-базу без обязательной дочерней карты; тестовый helper дополнен строкой chart, frozen-файлы не менялись. Это не отказ текущего декодера. |
| 2026-09-27 / `1235d36` | 07, проверка границы импортов | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_in_memory.py tests/session/test_sqlite.py tests/session/test_context.py tests/test_module_boundaries.py -q --tb=short` | 1; 531 passed, 2 failed | Прямой импорт общего `component_logging` из `session.context` нарушил действующий allowlist; безопасная проекция перенесена в сессионный formatter без ослабления boundary-теста. |
| 2026-09-27 / `1235d36` | 07, целевые SQLite и ContextService | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py tests/session/test_context.py -q -k "chart_corruption or invalid_stored_chart or chart_write_failure or lost_chart_commit or physically_removed or reaper_deletes_only or context_save_debug or context_load_debug or context_info" --tb=short` | 0; 12 passed, 352 deselected | Обе разновидности повреждения, непродлённый TTL, типизированный ContextService-исход, rollback, неопределённый commit с сохранённой парой, физическая очистка и DEBUG без payload. Остальной session-набор этой командой не охвачен. |
| 2026-09-27 / `1235d36` | 07, мутант: проигравшая CAS-дельта пишет chart | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py::TestSqliteSessionPersistence::test_cas_conflict_returns_atomic_actual_without_mutation tests/session/test_sqlite.py::TestSqliteSessionPersistence::test_already_applied_keeps_first_committed_chart -q --tb=line --show-capture=no` | 1; 2 failed, 1 passed | Conflict и `AlreadyApplied` обнаружили перезапись payload проигравшей дельты. Положительная запись проверена целевым набором; мутант удалён. |
| 2026-09-27 / `1235d36` | 07, мутант: DEBUG раскрывает StoredChart.payload | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_context.py::test_context_save_debug_input_redacts_stored_chart -q --tb=line --show-capture=no` | 1; 1 failed | Проверка поймала raw payload вместо размера и метаданных; мутант удалён. |
| 2026-09-27 / `1235d36` | 07, после удаления мутантов | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session/test_sqlite.py::TestSqliteSessionPersistence::test_cas_conflict_returns_atomic_actual_without_mutation tests/session/test_sqlite.py::TestSqliteSessionPersistence::test_already_applied_keeps_first_committed_chart tests/session/test_context.py::test_context_save_debug_input_redacts_stored_chart -q --tb=short` | 0; 4 passed | Подтверждены восстановленные конфликтная ветка и DEBUG-проекция; это адресный набор, а не весь SQLite adapter. |
| 2026-09-27 / `1235d36` | 07, финальный session-набор и модульные границы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session tests/test_module_boundaries.py -q --tb=short` | 0; 661 passed | Оба адаптера, общий conformance, SQLite schema/corruption/lifecycle, ContextService и границы импортов прошли на финальном коде. Сквозной runtime restart и полный `pytest` остаются 08. |
| 2026-09-27 / `1235d36` | 07, дополнительный application-набор | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap_integration.py tests/application/test_build_natal_integration.py tests/application/test_build_natal_logging.py tests/application/test_orchestrator_logging.py tests/application/test_session_view.py -q --tb=short` | 1; 240 passed, 1 failed | `test_runtime_build_natal_miss_then_hit_commits_same_session` ожидает старый список Handler-событий без пары `to_stored`; сценарий фактически дошёл до двух `Committed`. Обновление этого сквозного теста и отдельная restart-приёмка принадлежат 08; результат application-набора не объявлен зелёным. |
| 2026-09-27 / `1235d36` | 07, финальные пробелы и отдельная сверка diff | `git diff --check`; `rg -n '[ \t]+$' prompts/2026-09-27/session-stored-chart/07-sqlite-aggregate-and-session-logging.md src/exact_orb/session/adapters/sqlite.py src/exact_orb/session/context.py tests/session/test_context.py tests/session/test_sqlite.py docs/project_management/implementation_plans/session_stored_chart_implementation_plan.md` | 0 для Git; 1 для `rg` без совпадений | Финальный diff без ошибок пробелов; untracked prompt проверен отдельно. Повторная сверка ADR-0041, §8–10 и sequence 004/005 не выявила нового конфликта: структурный отказ предшествует renew, конфликтный CAS не меняет chart, payload скрыт в DEBUG. |
| 2026-09-27 / `6dc385d` | 08, сквозные сценарии и два SQLite outcome | `.\.venv\Scripts\python.exe -m pytest -q tests/application/test_application_bootstrap_integration.py tests/application/test_orchestrator_sqlite_integration.py tests/session/test_sqlite.py -k "runtime or sqlite_cas_race or chart_write_failure_rolls_back_parent_and_retry_commits_pair or lost_chart_commit_acknowledgement_preserves_pair_and_retry_winner"` | 0; 8 passed, 260 deselected | Проверены новый runtime и пустой cache, отказ первого build, reset/return, поздний load вкладки A, атомарная пара, `Superseded` и unknown commit/retry. Остальные тесты этой командой не запускались. |
| 2026-09-27 / `6dc385d` | 08, первая связанная проверка | `.\.venv\Scripts\python.exe -m pytest -q tests/session tests/application tests/test_module_boundaries.py` | 1; 1599 passed, 1 failed | Старый локальный тестовый порт в `test_session_deleted_after_real_handler_is_reported_as_lost` не имел нового `to_stored`; проверяемая ветка не дошла до удаления. Порт дополнен делегированием реальному resolver, production-код не менялся. |
| 2026-09-27 / `6dc385d` | 08, связанный набор после исправления | `.\.venv\Scripts\python.exe -m pytest -q tests/application/test_orchestrator_integration.py::test_session_deleted_after_real_handler_is_reported_as_lost tests/session tests/application tests/test_module_boundaries.py` | 0; 1600 passed | Повторно прошли session/application и архитектурные границы. Один адресный тест указан вместе с полным application-набором и запускается дважды. |
| 2026-09-27 / `6dc385d` | 08, полный локальный набор | `.\.venv\Scripts\python.exe -m pytest -q` | 0; 2649 passed | Подтверждён текущий локальный checkout без сетевых и платных smoke-тестов; HTTP, cookie и межверсионный `AlreadyApplied` остаются отдельными границами. |
| 2026-09-27 / `6dc385d` | 08, временный вызов cache через инструментированный runtime | `.\.venv\Scripts\python.exe -m pytest -q tests/application/test_application_bootstrap_integration.py::test_runtime_restart_restores_identical_chart_without_calculation --tb=short` | 1; 1 failed с `AssertionError: restore called a calculation component` | Временный запрещённый `cache.get` после установки ловушки обнаружен нужным тестом. Вызов удалён, в итоговом diff мутанта нет. |
| 2026-09-27 / `6dc385d` | 08, после удаления мутанта | `.\.venv\Scripts\python.exe -m pytest -q tests/application/test_application_bootstrap_integration.py::test_runtime_restart_restores_identical_chart_without_calculation` | 0; 1 passed | Восстановление снова проходит без доступа к cache/resolver/engine. |
| 2026-09-27 / `6dc385d` | 08, итоговое дерево после документации и удаления мутанта | `.\.venv\Scripts\python.exe -m pytest -q` | 0; 2649 passed | Повторно проверен итоговый код. Локальные ссылки изменённых Markdown-файлов разрешаются; `git diff --check` — 0, `rg -n '[ \t]+$' prompts/2026-09-27/session-stored-chart/08-end-to-end-acceptance.md` — 1 без совпадений. PlantUML PNG не рендерились. |
| 2026-09-27 / `fca9fba` | 09a, целевые тесты | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_stored_chart_build.py tests/test_chart_artifact_resolver.py tests/application/test_build_natal_handler.py tests/application/test_build_natal_logging.py -q --tb=short` | 0; 108 passed | Проверены ожидаемый/неожиданный отказ кодирования, `cause_type`, исключение `MemoryError`, исходный `ValidationError` идентичности и форматированный traceback реального Handler → Orchestrator; SQLite и restart здесь не проверялись. |
| 2026-09-27 / `fca9fba` | 09a, связанный набор в песочнице | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_chart_artifact_resolver.py tests/test_module_boundaries.py -q --tb=short` | 1; 1036 passed, 4 errors | Четыре place-catalog integration tests не стартовали: `PermissionError` на системном каталоге pytest temp. Повтор с `--basetemp .pytest-session-stored-09a` тоже завершился отказом доступа при cleanup; это не подтверждение полного прохода. |
| 2026-09-27 / `fca9fba` | 09a, связанный набор вне песочницы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-09a-escalated tests/application tests/test_chart_artifact_resolver.py tests/test_module_boundaries.py -q --tb=short` | 0; 1040 passed | Все application, resolver и module-boundary тесты прошли; session storage и остальные модули этим запуском не охвачены. |
| 2026-09-27 / `fca9fba` | 09a, полный локальный набор вне песочницы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-09a-full -q --tb=short` | 0; 2652 passed | Проверено дерево после 09a; frozen payload и статусы документов ещё ждут 09b. Сетевые и платные smoke-тесты не запускались. |
| 2026-09-27 / `fca9fba` | 09b, одноразовая генерация frozen payload | `.\.venv\Scripts\python.exe -B -m scripts.generate_stored_chart_fixtures` | 0; две новые пары `.bin`/`.json` | Использован текущий код с vendored эфемеридами. Скрипт хранит дату, координаты, тестовую версию и timezone; pytest не генерирует эталоны. Первый запуск показал `SyntaxWarning` в docstring скрипта; docstring исправлен без изменения данных. |
| 2026-09-27 / `fca9fba` | 09b, совместимость атрибутов и старого blob | `git check-attr -a -- tests/golden/chart_artifact_format_1.bin tests/golden/chart_artifact_format_1_natal_1985.bin tests/golden/chart_artifact_format_1_cosmogram_1985.bin`; `git hash-object tests/golden/chart_artifact_format_1.bin`; `git rev-parse HEAD:tests/golden/chart_artifact_format_1.bin` | 0; все три файла `binary: set`, `text: unset`; оба хэша `d4d314412ac847a27124b8d14e687ce5247ad6ee` | Атрибуты исключают текстовую конверсию; прежняя `.bin` не менялась. Команды не проверяют содержимое новых моделей — это делает следующий тест. |
| 2026-09-27 / `fca9fba` | 09b, целевой codec | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_chart_artifact_codec.py -q --tb=short` | 0; 39 passed | Для всех frozen payload проверена структурная полнота; натал сверён с human-эталоном, космограмма с областью неизвестного времени. Не охвачены application/session. |
| 2026-09-27 / `fca9fba` | 09b, связанный набор вне песочницы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-09b-related tests/test_chart_artifact_codec.py tests/test_chart_artifact_resolver.py tests/session tests/application tests/test_module_boundaries.py -q --tb=short` | 0; 1695 passed | Проверены кодек, session/application и архитектурные границы; прочие модули охвачены следующим полным запуском. |
| 2026-09-27 / `fca9fba` | 09b, полный локальный набор вне песочницы | `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp .pytest-session-stored-09b-full -q --tb=short` | 0; 2656 passed | Проверено итоговое поведение после 09a/09b. Сетевые и платные smoke-тесты не запускались; HTTP bootstrap остаётся M1-6. |
| 2026-09-27 / `fca9fba` | 09a/09b, пробелы и окончания строк | `git diff --check`; `git ls-files --eol -- .gitattributes docs/project_management/implementation_plans/session_stored_chart_implementation_plan.md docs/requirements/decisions/0041-stored-chart-in-session.md docs/requirements/decisions/README.md docs/requirements/session/stored-chart-session-behavior.md src/exact_orb/application/handlers/build_natal.py src/exact_orb/calculation/artifacts.py src/exact_orb/calculation/errors.py tests/application/test_build_natal_handler.py tests/application/test_build_natal_logging.py tests/application/test_stored_chart_build.py tests/test_chart_artifact_codec.py tests/test_chart_artifact_resolver.py` | 0; ошибок пробелов нет, все 13 изменённых отслеживаемых текстовых файлов `i/lf w/crlf` | Рабочее дерево не содержит смешанных LF/CRLF в целевых отслеживаемых файлах. Это не проверка новых untracked файлов; шесть изменённых Markdown-файлов дополнительно проверены на локальные ссылки: 28 существующих целей. |

После 02, 07 и перед закрытием 08 провести независимое ревью спорных границ
контрактов, атомарности и сквозного сценария. Подтверждённые находки и их
исправления внести в журнал; само ревью не заменяет исполняемые проверки.

Из корня репозитория использовать проектный interpreter:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/session -q
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_chart_artifact_codec.py tests/test_chart_artifact_resolver.py tests/test_module_boundaries.py -q
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
git diff --check
```

Запускать поэтапно: в каждой карточке сначала её целевые тесты, затем
связанный набор, после сборки всех срезов — полный `pytest`. Эти команды
здесь **план**, а не отчёт о выполненных проверках. Сетевые и платные
smoke-тесты не требуются. Результаты проверки, оставшиеся ограничения и
непроверенные части фиксируются при исполнении соответствующего промта.

M1-6 получает готовые `ApplicationRuntime.context`,
`ApplicationRuntime.calculation_version`, `ApplicationRuntime.orchestrator` и
`application/session_view`. Transport сам ведёт cookie/bootstrap и пишет
ERROR с `safe_reason` при `chart_unavailable`. Отдельное согласование
артефакта ответа `AlreadyApplied` при смешанных версиях и источник карты
для M2-интерпретации остаются отложенными решениями ADR-0041.

Этот план не разрешает создание коммитов, новой ветки, push или PR без
отдельного запроса.
