# ApplicationOrchestrator — план реализации и карта приёмки

**Дата исходной сверки:** 2026-09-16, этап 0.1. **Журнал выполнения:** §1.3, обновлён 2026-09-17.
**Контракт:** R3.2 с уточнением 2026-09-17. **Рабочие этапы:** 36 основных промтов в 10 группах и дополнительные карточки 1.R1, 2.R2, 3.R1 и 3.R2; номера основных карточек сохранены.
**Ветка исходной сверки:** `docs/adr-birth-data-and-terms-of-use`.
**HEAD исходной сверки:** `dc069fc6e3f41e97b27fcbeb066516e5e913f491`.

## 1. Основание и границы сверки

План подготовлен по [промту 0.1](../../prompts/2026-09-16/00-application-orchestrator-plan/00.1-baseline-and-acceptance-map.md).
В этапе 0.1 сверялось рабочее дерево, включая изменённые документы и untracked
R3.2/диаграммы 009–010. HEAD сам по себе не содержит всего актуального контракта.
До начала работы в дереве уже были staged, modified и untracked файлы;
их содержимое сохранено. Результатом этапа 0.1 был только настоящий документ.
Исходные свидетельства этой сверки сохранены в §1.1–1.2; последующее выполнение
и его ограничения записываются отдельно в §1.3.

Источники:

- [AGENTS.md](../../AGENTS.md).
- [ApplicationOrchestrator R3.2](../requirements/component_responsibilities/exact-orb_application_orchestrator_requirements.md):
  §1.3–1.6, FR-01–FR-27, §6, §8–12, §15.
- [ADR-0006](../requirements/decisions/0006-application-orchestrator.md), ревизии
  2026-09-15/16: входной RunContext, отдельный session lifecycle, события операции.
- [Session requirements](../requirements/component_responsibilities/exact-orb_session_requirements.md):
  §7–8, P3-AC-11/12; [ADR-0009](../requirements/decisions/0009-context-yes-profiles-later.md)
  и [ADR-0014](../requirements/decisions/0014-explicit-state-mutations.md).
- [Handler requirements](../requirements/handlers/exact_orb_build_natal_handler_requirements.md)
  и [Build Natal components](../requirements/component_responsibilities/exact-orb_build_natal_components.md).
- [ADR-0012](../requirements/decisions/0012-bootstrap-request-response-streaming.md)
  и [ADR-0020](../requirements/decisions/0020-agent-runtime-behind-handlers.md):
  request/response, отсутствие Agent Runtime в Build Natal.
- [ADR-0025](../requirements/decisions/0025-debug-component-boundary-messages.md),
  [ADR-0026](../requirements/decisions/0026-compact-chart-boundary-logging.md),
  [ADR-0028](../requirements/decisions/0028-full-debug-component-boundary-payloads.md)
  и [ADR-0034](../requirements/decisions/0034-birth-data-and-terms-of-use.md).
  ADR-0028 явно заменил режим payload ADR-0026; новый lifecycle-журнал следует R3.2.
- [Индекс диаграмм](../sequence_diagrams/build_natal/README.md),
  [000](../sequence_diagrams/build_natal/000-build_natal_end_to_end.puml),
  [006](../sequence_diagrams/build_natal/006-build_natal_superseded_cas.puml),
  [007](../sequence_diagrams/build_natal/007-build_natal_commit_failure_and_session_expired.puml),
  [009](../sequence_diagrams/build_natal/009-build_natal_commit_cancellation.puml),
  [010](../sequence_diagrams/build_natal/010-build_natal_application_observability.puml).

### 1.1. Исходное состояние на этапе 0.1

Все упомянутые существующие тесты **прочитаны, но не запускались в этапе 0.1**.
Наличие кода и теста не означает доказанного прохождения приёмки.

| Компонент | Подтверждённое исходное состояние | Свидетельство |
|---|---|---|
| RunContext | Реализованы run_id, started_at, new() и UTC-валидация started_at. deadline отсутствует | [run_context.py](../../src/exact_orb/run_context.py), E1 |
| Command и Handler protocol | Frozen Command/BuildNatalCommand и handle(command, state, run) существуют | [commands.py](../../src/exact_orb/application/commands.py), [ports.py](../../src/exact_orb/application/ports.py) |
| Handler outcomes | results.py занят BuildNatalSuccess/BuildNatalOutcome; общий CalculationFailed.error_code — str | [results.py](../../src/exact_orb/application/results.py), [outcomes.py](../../src/exact_orb/outcomes.py), E2 |
| BuildNatalHandler | Реализованы resolver → artifact → delta, технические исходы и собственные события | [build_natal.py](../../src/exact_orb/application/handlers/build_natal.py), E3/E4 |
| ContextService | Реальные create/load/save; save делает один CAS и классифицирует его результат. Автоматического retry нет | [context.py](../../src/exact_orb/session/context.py), E5/E6 |
| Сессионные контракты | Frozen SessionState, StateDelta, SessionSnapshot и typed outcomes существуют | [state.py](../../src/exact_orb/session/state.py), [persistence.py](../../src/exact_orb/session/persistence.py), [outcomes.py](../../src/exact_orb/session/outcomes.py) |
| Persistence | InMemory и file-backed SQLite реализованы. SQLite работает через executor; сравнение версий и запись атомарны внутри адаптера | [in_memory.py](../../src/exact_orb/session/adapters/in_memory.py), [sqlite.py](../../src/exact_orb/session/adapters/sqlite.py), E7 |
| Логирование | Штатный logging и component_message существуют; четырёх application lifecycle events пока нет | [component_logging.py](../../src/exact_orb/component_logging.py), [logging_setup.py](../../src/exact_orb/logging_setup.py), E4 |
| ApplicationOrchestrator и ApplicationResult | Целевые; соответствующие файлы ещё отсутствуют. Переносить существующий внешний union неоткуда | [application-пакет](../../src/exact_orb/application/__init__.py), R3.2 |
| Agent orchestration | Самостоятельный каркас Orchestrator с NotImplementedError, не application coordinator | [orchestrator.py](../../src/exact_orb/orchestration/orchestrator.py), [types.py](../../src/exact_orb/orchestration/types.py) |
| Composition, транспорт, клиентская монотонность | Нужного application wiring и клиентского contract test пока нет | R3.2, components §9; AC-34 — внешний срез |
| Admission и application load harness | Реализация ограничителя в src/tests/scripts не найдена. Есть отдельный session benchmark | [bench_session_sqlite.py](../../scripts/bench_session_sqlite.py); AC-36 имеет внешнюю предпосылку |

Поиск реализации admission: `rg -n 'admission|Semaphore|max_concurrent|queue_limit' src tests scripts`
не дал совпадений. Session benchmark не доказывает application throughput.

### 1.2. Реестр исходных свидетельств этапа 0.1

Идентификаторы E1–E8 ниже относятся к файлам и функциям, существовавшим при
сверке 0.1, а не к новым или пройденным тогда тестам. Это историческая таблица,
не текущий статус приёмки. Параметризация в node id не раскрыта.

| ID | Существующие проверки | Чего они ещё не доказывают |
|---|---|---|
| E1 | [tests/test_run_context.py](../../tests/test_run_context.py): `test_run_context_new_uses_uuid_and_utc_started_at`, `test_run_context_rejects_naive_started_at` | Контракт deadline и injected clock Orchestrator |
| E2 | [tests/application/test_contracts.py](../../tests/application/test_contracts.py): `test_build_natal_command_inherits_frozen_config_from_command`, `test_build_natal_success_accepts_an_explicit_consistent_pair` | Внешний ApplicationResult, его union и связи полей |
| E3 | [tests/application/test_build_natal_handler.py](../../tests/application/test_build_natal_handler.py): `test_resolution_outcomes_short_circuit_with_the_same_object`, `test_empty_input_required_passes_through_unchanged`, `test_artifact_cancellation_propagates_unchanged` | Запрет save, application-нормализацию и terminal event Orchestrator |
| E4 | [tests/application/test_build_natal_logging.py](../../tests/application/test_build_natal_logging.py): `test_started_is_debug_and_precedes_exactly_one_terminal_event`, `test_cancellation_logs_warning_and_propagates` | Четыре новых lifecycle events всего execute; Handler started остаётся DEBUG |
| E5 | [tests/session/test_context.py](../../tests/session/test_context.py): `test_load_returns_snapshot_by_identity_without_facet_reads`, `test_load_maps_any_persistence_error_to_read_failed`, `test_save_passes_original_expected_delta_and_now_by_identity`, `test_save_classifies_same_intent_without_an_extra_get` | Порядок application стадий, автоматический retry и преобразование в ApplicationResult |
| E6 | [tests/session/test_context.py](../../tests/session/test_context.py): `test_two_same_intent_saves_commit_once_without_rebase`, `test_sequential_retry_keeps_original_expected_and_commits_once`, `test_old_retry_is_superseded_after_a_different_intent` | Второй тест получает Committed, затем вручную вызывает save; потеря подтверждения и retry внутри execute не воспроизведены |
| E7 | [tests/session/test_sqlite.py](../../tests/session/test_sqlite.py): `test_commit_exception_is_unknown_without_retry_or_readback`; унаследованный `TestSqliteSessionPersistence::test_concurrent_cas_commits_once_and_reports_winner` из [conformance.py](../../tests/session/conformance.py) | Первый тест теряет подтверждение create, а не application CAS; второй не собирает Orchestrator/Handler |
| E8 | [tests/application/test_build_natal_integration.py](../../tests/application/test_build_natal_integration.py): `test_real_natal_path_caches_and_correlates_run_id`, `test_real_unknown_time_path_builds_cosmogram`, `test_real_polar_calculation_fails_and_is_not_cached` | Реальный путь заканчивается Handler outcome; session commit и ApplicationResult отсутствуют |

Переиспользуемые данные: [tests/fixtures/calculation.py](../../tests/fixtures/calculation.py),
[places.jsonl](../../tests/fixtures/places.jsonl), [application/stubs.py](../../tests/application/stubs.py).
Общие [conftest.py](../../tests/conftest.py) и [pyproject.toml](../../pyproject.toml)
задают pytest-asyncio, src layout, эфемериды и workspace-local tmp_path.
`.venv/Scripts/python.exe` существует; версия/работоспособность интерпретатора
и наличие всех runtime-зависимостей в 0.1 запуском не проверялись.
[tests/test_module_boundaries.py](../../tests/test_module_boundaries.py) сохраняется без ослабления.

### 1.3. Текущие статусы и журнал выполнения

#### 1.3.1. Статусы на 2026-09-18

| Этап | Статус | Граница подтверждения |
|---|---|---|
| 0.1 | Выполнен | Исходная сверка и план; тесты в этом этапе не запускались |
| 1.1 | Тесты deadline написаны; проверены после 1.2 | До реализации было содержательное падение, после реализации новые и прежние случаи прошли |
| 1.2 | Выполнен | Поле/default/UTC-валидация deadline; application retry и AC-14 этим не закрыты |
| 1.3 | Тесты logging проверены после 1.4 | Все 106 случаев исполнились; два намеренных нарушения обнаружены. В тесты добавлены только docstring, AST без них и node IDs сохранены |
| 1.4 | Функции записи событий реализованы и проверены | Целевой набор: 106 passed; R: 1233 passed; F: 2152 passed. Проверен формат функций, не порядок событий execute; журнал §1.3.11 |
| 1.R1 | Выполнен | Независимые тестовые константы, четыре новых UTC-случая started_at, docstring и журнал; production-код не менялся |
| 2.1 | Тесты написаны и проверены после 2.2 | Все 27 случаев исполнились и прошли; историческая ошибка импорта сохранена в §1.3.5 |
| 2.2 | Реализован; целевые и последующие общие проверки прошли | Чистая политика отказов: 27 passed; историческая блокировка R/F снята в 1.4, новая контрольная точка — §1.3.11 |
| 2.3 | Тесты трёх моделей написаны и проверены после 2.4 | Все 125 случаев исполнились и прошли без изменения тестового файла; историческая ошибка импорта сохранена в §1.3.7 |
| 2.4 | Три модели реализованы; целевые и последующие общие проверки прошли | 125 passed; историческая блокировка R/F снята в 1.4, новая контрольная точка — §1.3.11 |
| 2.5 | Тесты семи моделей и полного union проверены после 2.6 | Весь файл дал 417 passed; прежние и новые assertions исполнились. Требования указаны внутри всех 39 тестовых функций; историческая ошибка импорта сохранена в §1.3.9 |
| 2.6 | Полный ApplicationResult реализован; целевые и последующие общие проверки прошли | 417 passed без изменения тестов; результаты карточки — §1.3.10. Последующие R/F прошли в 1.4, §1.3.11 |
| 3.1 | Ранняя выборка пройдена; отложенный success/commit прошёл в 6.4 | Текущий общий результат §1.3.36; история импорта и фикстуры — §1.3.13/15, прежний red — §1.3.29 |
| 3.2 | Конструктор и unknown-command ветка прошли; сквозной success/commit прошёл в 6.4 | Текущий общий результат §1.3.36; история 3.R2 — §1.3.18, прежний red — §1.3.29 |
| 3.R1 | Выполнен | Четыре замены в тесте; две logging-проверки прошли без изменения assertions и production-кода. R содержит только семь подтверждённых отложенных failures; F не запускался. Журнал §1.3.17 |
| 3.R2 | Согласованные поправки реализованы; результаты в §1.3.18 | Frozen RunContext, строгая версия и точный текст результата, проверка аргументов политики, terminal из ApplicationResult и JSON events |
| 2.R2 | Отдельная карточка подготовлена, не выполнена | Граница глубокой неизменяемости Issue/ChartArtifact требует согласования с artifact-контрактом; AC-24 целиком не закрыт |
| 4.1 | Тестовая карточка выполнена; оба отложенных Superseded прошли в 6.4 | Текущий общий результат §1.3.36; история исходного red — §1.3.20 |
| 4.2 | Ветка load выполнена; отложенные commit-зависимые проверки прошли в 6.4 | Текущий общий результат §1.3.36; история — §1.3.22/29 |
| 5.1 | Десять non-success случаев и отложенный positive save прошли | Identity/result/events/no-save подтверждены для непустых issues; K3 оставлен открытым; текущий общий результат §1.3.36 |
| 5.2 | Штатные ветки Handler и success→commit прошли | Текущий общий результат §1.3.36; K3 остаётся открытым; история — §1.3.29 |
| 5.3 | Пять тестов ранних ошибок и отмены прошли; §1.3.29 | 5 passed после 5.2/5.4; история тестовой карточки — §1.3.26 |
| 5.4 | Ошибки и отмена до commit реализованы; §1.3.29 | 5 случаев 5.3 passed; сквозной success/commit и общий AC-29 остаются группе 6; история частичного выполнения — §1.3.28 |
| 6.1 | Три тестовых случая прошли после 6.2 | Обычный `Committed` при original expected 0/7 и отмена после входа в save; текущий результат — §1.3.33, исходное падение — §1.3.31 |
| 6.2 | Реализован путь первой защищённой попытки с `Committed` | Целевой набор: 3 passed; R: 1426 passed, 2 отложенных Superseded failed; текущий результат — §1.3.33 |
| 6.3 | Все десять случаев commit-файла прошли после 6.4 | Текущий результат §1.3.36; исходный red — §1.3.35, подготовка — §1.3.34 |
| 6.4 | Выполнены все исходы первой защищённой попытки без retry | Целевой набор: 226 passed; R: 1436 passed; F: 2355 passed. Retry и полная R3.2-приёмка остаются группе 7 и далее; §1.3.36 |
| 7.1 | Тестовая матрица создана внутри выполнения 7.2; отдельный промт сохранён позднее | Исходный red: 11 failed, 1 passed (§1.3.37). Текущий прогон: 12 passed, R: 1448 passed, F: 2367 passed; §1.3.38 |
| 7.2 | Один точный retry реализован и проверен | Целевой набор: 23 passed; R: 1448 passed; F: 2367 passed. Реальный lost-CAS и повторная отмена остаются отдельными этапами; §1.3.37 |
| 8.1 | Сквозная последовательность lifecycle проверена через `execute()` | 13 новых случаев; целевой файл: 189 passed, R: 1461 passed, F: 2380 passed. Состав полей и длительности остаются 8.2; §1.3.39 |
| 8.2 | Состав lifecycle-событий и длительности проверены через `execute()` | 10 новых случаев; целевой файл: 199 passed, R: 1471 passed, F: 2390 passed. Гонки повторной отмены и интеграция остаются поздним карточкам; §1.3.40 |
| Остальные основные карточки | Запланированы, не выполнялись | Начиная с 9.1; формулировка «закрывает» в карточке означает будущую обязанность |

По запросу пользователя 2026-09-16 подготовлен
[промт 2.1](../../prompts/2026-09-16/02-application-results/02.1-application-failure-policy-tests.md)
до реализации 1.4. Это допустимый независимый срез с зависимостью только от 0.1.
Тестовая карточка выполнена отдельно; фактические результаты и граница
свидетельства записаны в §1.3.5. Отсутствие operation_logging.py тогда блокировало
общий набор application; блокировка снята выполнением 1.4, §1.3.11.
Номера карточек и зависимости не изменены.

[Промт 1.R1](../../prompts/2026-09-16/01-application-foundations/01.R1-test-isolation-and-execution-record.md)
выполнен между 1.3 и 1.4 как дополнительная корректирующая карточка.
Его область: новый [telemetry.py](../../tests/fixtures/telemetry.py), импорты
и тесты started_at в [test_run_context.py](../../tests/test_run_context.py),
только источник/имена констант в
[test_orchestrator_logging.py](../../tests/application/test_orchestrator_logging.py)
и настоящий журнал/правила плана. Номера, зависимости и распределение AC
основных карточек не изменены.

Расчётные fixtures сохранены. Новый модуль констант использует только
стандартную библиотеку. В test_run_context.py по-прежнему есть проверки
BirthDataResolver и общий conftest; весь файл не объявляется изолированным
тестом одной модели. Новых application AC эта корректировка не закрывает.

Предусмотренный после 1.3–1.4 срез неизменяемости RunContext выполнен в 3.R2:
требование закреплено, присваивание полям запрещено и проверено.
Политика неизвестных полей (`extra`) сохранена и остаётся отдельным решением.
По явному поручению пользователя 2026-09-17 карточка 3.1 выполнена независимо
от предварительных корректировок; они не закрыты этим действием (§1.3.13).

#### 1.3.2. Команды журнала

Обозначения T/L/B/I/A ниже соответствуют точным командам. R/F определены в
§4.2. Все команды запускаются из корня репозитория.

```powershell
# T — RunContext
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py -q

# L — lifecycle logging
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q

# B — RunContext и архитектурные ограничения
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/test_module_boundaries.py -q

# I — независимый импорт новых констант
.\.venv\Scripts\python.exe -B -c "import sys; import tests.fixtures.telemetry; assert not any(n == 'exact_orb' or n.startswith('exact_orb.') for n in sys.modules); print('telemetry fixtures: isolated import OK')"

# A — синтаксис двух тестовых файлов и нового fixture-модуля
.\.venv\Scripts\python.exe -B -c "import ast,pathlib; paths=['tests/test_run_context.py','tests/application/test_orchestrator_logging.py','tests/fixtures/telemetry.py']; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in paths]; print('AST OK: 3 files')"
```

#### 1.3.3. Исторические результаты 1.1–1.3

Источник: предыдущие отчёты выполнения в этой сессии, сведённые в §3.2 промта
1.R1; исходное падение также зафиксировано в
[промте 1.2](../../prompts/2026-09-16/01-application-foundations/01.2-run-context-deadline-field.md).
Это перенос исторических свидетельств, не новые запуски и не воспроизведение
старого состояния checkout. Времена изменения файлов не служат доказательством
порядка test-first.

| Дата | Этап / состояние | Команда | Результат | Exit code | Ограничение / причина |
|---|---|---|---|---|---|
| 2026-09-16 | 1.1 до реализации deadline | T | 10 failed, 11 passed | 1 | Семь случаев: отсутствует атрибут deadline; три: нет ожидаемого отказа валидации; не ошибка импорта |
| 2026-09-16 | 1.2, проверка до изменения модели | T | 10 failed, 11 passed | 1 | Повторно подтверждены те же причины до добавления поля |
| 2026-09-16 | 1.2 после реализации | T | 21 passed | 0 | Новые и прежние проверки RunContext/resolver |
| 2026-09-16 | 1.2, связанный набор | R | 679 passed | 0 | Состав тестов до 1.3 |
| 2026-09-16 | 1.2, полный набор | F | 1598 passed | 0 | Состояние после 1.2 и до добавления тестов 1.3 |
| 2026-09-16 | 1.3, тесты написаны | L | 1 error during collection | 1 | ModuleNotFoundError: exact_orb.application.operation_logging; assertions не исполнялись |

В 1.3 дополнительно успешно выполнен `ast.parse` тестового файла (exit 0).
Проверка синтаксиса не подтверждает формат событий, их частоты или порядок
вызовов execute. Прежние **1598 passed не являются свидетельством прохождения
текущего полного набора**, содержащего тесты ещё не реализованного модуля.

#### 1.3.4. Фактические результаты 1.R1

Источник: непосредственные запуски при выполнении 1.R1 в текущем checkout.
В отличие от §1.3.3, следующие результаты получены в самой корректирующей
карточке; исторические числа под новый состав тестов не переписывались.

| Дата | Состояние / проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | До изменений | T | 21 passed | 0 | Свежий baseline |
| 2026-09-16 | После изменений | T | 25 passed | 0 | Добавлены 2 положительных и 2 отрицательных случая started_at; прежние случаи сохранены |
| 2026-09-16 | Архитектурные ограничения | B | 61 passed | 0 | Это названный набор, не полный R/F |
| 2026-09-16 | Изоляция telemetry fixtures | I | isolated import OK | 0 | Новый процесс не загрузил пакет exact_orb |
| 2026-09-16 | Синтаксис изменённых Python-файлов | A | AST OK: 3 files | 0 | Статическая проверка не заменяет выполнение logging assertions |
| 2026-09-16 | Lifecycle logging | L | 1 error during collection | 1 | Тот же ModuleNotFoundError: exact_orb.application.operation_logging |

Импорты нового fixture-модуля проверены: только datetime/uuid. В двух тестовых
файлах импорт calculation fixtures заменён на telemetry. R/F в 1.R1 не
запускались: они отложены до 1.4 из-за известной ошибки сборки L. Тесты не
исключались через ignore/skip/xfail и не заменялись заглушками.

#### 1.3.5. Фактические результаты 2.1

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Источник: непосредственные запуски при выполнении сохранённого промта 2.1.
Создан [test_application_failure_policy.py](../../tests/application/test_application_failure_policy.py).
Production-модуль failure_policy.py не добавлялся: это отдельная карточка 2.2.

| Требование / граница | Тест | Описано случаев |
|---|---|---:|
| FR-23, §9–10: четыре поля каждой реакции, точный текст, обе причины absence при commit | `test_failure_reactions_match_requirement_rows` | 18 |
| Открытые calculation/resolution/persistence-коды сохраняются в detail_code и не подставляются в user_message | `test_open_error_codes_keep_details_and_safe_messages` | 5 |
| Синхронный keyword-only API с указанными аргументами/defaults | `test_describe_failure_has_a_synchronous_keyword_only_api` | 1 |
| Чередование кодов не изменяет ранее полученные описания | `test_interleaved_calls_preserve_previous_descriptions` | 1 |
| Чистая политика не пишет события для известного и неизвестного calculation-кода; захват имеет положительный контроль | `test_describe_failure_does_not_log` | 2 |

Число **27** получено статическим чтением параметризаций, а не успешной
сборкой или выполнением pytest. Ожидаемые сообщения заданы в тестах независимо
от production; статическая сверка 18 основных примеров с 17 строками §10
подтвердила совпадение code/message/retryable. Строка absence при commit
развёрнута в два случая. Это не проверка фактического поведения функции.

Команды из корня репозитория:

```powershell
# P2.1 — целевой набор
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_failure_policy.py -q

# S2.1 — синтаксис при заблокированном импорте
.\.venv\Scripts\python.exe -B -c "import ast,pathlib; p=pathlib.Path('tests/application/test_application_failure_policy.py'); ast.parse(p.read_text(encoding='utf-8'), filename=str(p)); print('AST OK')"
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | Целевые тесты после написания | P2.1 | 1 error during collection | 1 | ModuleNotFoundError: exact_orb.application.failure_policy; assertions не исполнялись |
| 2026-09-16 | Синтаксис нового файла | S2.1 | AST OK | 0 | Статическая проверка не заменяет pytest |
| 2026-09-16 | Связанный и полный наборы | R/F (§4.2) | Не запускались | — | Отложены до реализации 2.2 и успешного целевого прогона; общий набор также зависит от незавершённой 1.4 |

Проверки не пропускались через skip/xfail/importorskip; подмена отсутствующего
модуля не использовалась. Маркер no_ephemeris_autoinit отключает только
инициализацию эфемерид общей fixture, не исполнение тестов. Расчётные fixtures
и компоненты не импортируются новым тестовым файлом.

На момент завершения 2.1 AC-21/25/33 целиком не закрыты: не проверены исполняемые реакции политики,
фактический WARN Orchestrator, нормализация реальных исключений и весь
application-flow. Следующим шагом было выполнение
[сохранённого промта 2.2](../../prompts/2026-09-16/02-application-results/02.2-application-failure-policy.md).
Промт подготовлен 2026-09-16; при подготовке реализация не выполнялась.
Последующее выполнение 2.2 зафиксировано отдельно ниже; результаты запусков
самого тестового этапа 2.1 остаются историческими.

#### 1.3.6. Фактические результаты 2.2

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Источник: непосредственные запуски при выполнении сохранённого промта 2.2.
Добавлен [failure_policy.py](../../src/exact_orb/application/failure_policy.py):
синхронная keyword-only функция describe_failure, локальный Literal FailureKind
и frozen dataclass FailureDescription с четырьмя полями реакции.

Тексты и retryable соответствуют §10 R3.2. Открытые технические коды сохраняются
в detail_code; неизвестные calculation-коды получают общий fallback. Различены
load/commit и обе причины SessionAbsent. Статические таблицы защищены
MappingProxyType, сообщения не формируются из payload. Модуль использует
только стандартную библиотеку; logging, I/O и обработка operation-flow отсутствуют.

Целевая команда до и после реализации — P2.1 из §1.3.5. Связанный набор R
запущен без исключения logging-тестов:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_failure_policy.py -q
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | До добавления модуля | P2.1 | 1 error during collection | 1 | Повторно подтверждён ModuleNotFoundError: exact_orb.application.failure_policy |
| 2026-09-16 | После реализации | P2.1 | 27 passed | 0 | Assertions реально исполнились; тестовый файл 2.1 не изменён |
| 2026-09-16 | Связанный набор | R | 1 error during collection | 1 | ModuleNotFoundError: exact_orb.application.operation_logging из незавершённой 1.4; выполнение связанного набора не состоялось |
| 2026-09-16 | Полный pytest | F (§4.2) | Не запускался | — | Отложен до устранения ошибки сборки R |

Проверены поля и точные тексты реакций, оба resolution retryable, все сочетания
стадии/reason отсутствия сессии, fallback, keyword-only API, сохранность
предыдущих результатов и отсутствие логирования в двух calculation-сценариях
с положительным контролем захвата. Тесты, fixtures и соседние production-модули
не менялись. Ошибка сборки R не скрывалась через ignore/skip/xfail.

Простые проверки необходимых аргументов функции не объявляются отдельным
проверенным контрактом для всех невалидных сочетаний: это вне набора 2.1.
AC-21/25/33 целиком не закрыты. Остались фактический WARN Orchestrator,
нормализация реальных исключений, безопасность всего application-flow и
прохождение общего набора. Следующая карточка раздела 2 — подготовка 2.3.

#### 1.3.7. Фактические результаты 2.3

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Сохранён и выполнен [промт 2.3](../../prompts/2026-09-16/02-application-results/02.3-application-results-tests.md).
Добавлен [test_application_results.py](../../tests/application/test_application_results.py):
тесты ApplicationCommitted, ApplicationAlreadyApplied и ApplicationSuperseded
по FR-22, §8–10 и §12 R3.2. Production-модуль application_results.py не добавлялся.

Подготовленное покрытие (assertions пока не исполнялись):

| Требование | Тесты в test_application_results.py |
|---|---|
| Полная корректная запись, оба UUID | test_valid_results_preserve_the_complete_contract |
| Чужие статусы, code, detail_code и retryable | test_results_reject_each_alternative_status; test_results_reject_contradictory_reaction_fields |
| Границы версии и обязательный run_id | test_results_preserve_versions_including_the_lower_bound; test_results_require_a_version_within_the_model_bound; test_results_require_a_valid_run_id |
| Обязательный artifact успеха, запрет artifact у Superseded | test_success_results_require_a_valid_artifact; test_superseded_rejects_an_artifact_argument |
| Сообщения успеха и Superseded | test_success_results_reject_a_user_message; test_superseded_requires_a_user_message; корректный текст в test_valid_results_preserve_the_complete_contract |
| Frozen при допустимом новом значении | test_results_are_frozen_even_for_valid_field_assignments; test_success_results_reject_replacing_a_valid_artifact |
| Публичные поля и сохранение None в model_dump | test_result_dump_contains_only_the_public_fields |

В негативных проверках исходный набор аргументов сначала конструирует валидную
модель, затем меняется одно поле. Для заморозки допустимость нового значения
проверяется на отдельном экземпляре. Используются существующие artifact helper
и telemetry UUID; нет расчёта, session-flow, заглушек или подмены предмета теста.

**P2.3 — целевой набор:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

**S2.3 — синтаксис без импорта отсутствующего модуля:**

```powershell
.\.venv\Scripts\python.exe -B -c "import ast; from pathlib import Path; ast.parse(Path('tests/application/test_application_results.py').read_text(encoding='utf-8-sig'))"
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | Целевой набор | P2.3 | 1 error during collection, 0.29 s | 1 | ModuleNotFoundError: exact_orb.application.application_results; реализация относится к 2.4 |
| 2026-09-16 | Синтаксис | S2.3 | ast.parse завершился без ошибок | 0 | Не проверяет импорт, параметризацию pytest или assertions |
| 2026-09-16 | Связанный и полный наборы | R и F (§4.2) | Не запускались | — | Отложены до успешного целевого набора после 2.4; также остаётся известное ограничение незавершённой 1.4 |

Источник свидетельства — непосредственные запуски этих команд, не прежние
результаты соседних тестов. Ошибка импорта не скрыта через skip/xfail или
fallback. Тесты написаны, но их чувствительность и поведение моделей ещё
не доказаны. AC-19/23/24/26/27 целиком не закрыты; полный union, runtime
нормализация, CAS и execute остаются вне этого этапа.

Предшествующие production-файлы, тесты и fixtures сохранены. Следующая
карточка — подготовка 2.4, реализация трёх моделей; автоматически не выполнялась.

#### 1.3.8. Фактические результаты 2.4

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Сохранён и выполнен [промт 2.4](../../prompts/2026-09-16/02-application-results/02.4-application-result-models.md).
По запросу пользователя в начало промта добавлен раздел «Что реализует этот
этап»: назначение трёх ответов, польза для интерфейса и граница текущей работы.

Добавлен [application_results.py](../../src/exact_orb/application/application_results.py)
с ApplicationCommitted, ApplicationAlreadyApplied и ApplicationSuperseded.
Три явные модели используют ConfigDict(frozen=True, extra="forbid"), Literal
для статусов/code/retryable, обязательный UUID и Field с нижней границей версии.
У двух успешных вариантов обязателен ChartArtifact; Superseded его не принимает.
Сообщение Superseded передаёт вызывающий, таблица failure_policy не дублируется.
В модуле нет I/O, классификации commit outcomes или полного ApplicationResult
union; application/results.py и экспорты соседних __init__.py сохранены.

**P2.4 — целевой набор до и после реализации:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

**R — связанный набор после успешного P2.4:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | До добавления модуля | P2.4 | 1 error during collection, 0.36 s | 1 | Повторно подтверждён ModuleNotFoundError: exact_orb.application.application_results |
| 2026-09-16 | После реализации | P2.4 | 125 passed, 0.38 s | 0 | Все assertions тестов 2.3 исполнились; тестовый файл не изменён |
| 2026-09-16 | Связанный набор | R | 1 error during collection, 0.78 s | 1 | ModuleNotFoundError: exact_orb.application.operation_logging; незавершённый этап 1.4 |
| 2026-09-16 | Полный pytest | F (§4.2) | Не запускался | — | Отложен до успешного R; logging-тесты не исключались |

Проверены полные корректные записи, альтернативные статусы и противоречивые
поля реакции, обязательные UUID/версии/artifact, границы версии, отсутствие
artifact у Superseded, frozen и публичный model_dump. Связь требования с
именем теста сохранена в таблице §1.3.7; исторический запуск 2.3 не переписан.

Это подтверждение трёх моделей, а не полного application-flow. AC-19/26/27
ещё требуют преобразования runtime outcomes в execute; AC-23/24 относятся
также к оставшимся моделям. Полный union, session semantics, сквозной run_id
и прохождение общего набора не доказаны. Политика strict/coercion и глубокая
неизменяемость вложенного артефакта этим набором не устанавливаются.

Тесты и fixtures, failure_policy.py, прежние production-модули и Git index
сохранены. Следующая карточка — подготовка 2.5, тесты остальных моделей и
полного union; автоматически не выполнялась.

#### 1.3.9. Фактические результаты 2.5

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Сохранён и выполнен [промт 2.5](../../prompts/2026-09-16/02-application-results/02.5-application-results-union-tests.md).
В начале промта объяснены семь ситуаций для пользователя, польза согласованных
ответов для интерфейса и граница этапа: сначала проверки, реализация — в 2.6.

Расширен [test_application_results.py](../../tests/application/test_application_results.py):
добавлены 26 тестовых функций с отдельными таблицами и helpers. Подготовлены
20 корректных failure-записей, включая четыре варианта SessionAbsent, четыре
варианта InternalFailure и два неизвестных calculation-кода. Вместе с тремя
прежними моделями они используются для проверки выбора конкретного типа
через TypeAdapter(ApplicationResult). Проверка множества статусов перебирает
240 сочетаний для каждой из 23 исходных записей и требует ровно 12 допустимых
троек; её assertions ещё не исполнились.

| Требование | Добавленные проверки в целевом файле |
|---|---|
| Полная корректная запись, два UUID и сохранение реакции | `test_failure_models_preserve_complete_records` |
| Непустые структурированные issues, порядок и содержимое | `test_input_required_preserves_ordered_structured_issues`, `test_input_required_rejects_missing_empty_or_invalid_issues` |
| Связь calculation-кода и retryable; фиксированные значения остальных моделей | `test_calculation_failure_rejects_retryability_inconsistent_with_code`, `test_failure_models_reject_contradictory_fixed_retryability` |
| Обязательный технический код и запрет лишней причины | `test_technical_failure_models_require_a_detail_code`, `test_failure_models_without_technical_reason_reject_detail_code` |
| Противоречивые коды и статусы отдельных моделей | `test_failure_models_reject_success_code`, `test_failure_models_reject_incompatible_and_unknown_statuses` |
| Прочитанная версия обязательна; неизвестная версия не подменяется числом | `test_loaded_failures_preserve_known_nonnegative_version`, `test_loaded_failures_require_known_nonnegative_version`, `test_failures_without_known_state_reject_numeric_version` |
| UUID и переданный текст сообщения | `test_failure_models_require_a_valid_run_id`, `test_failure_models_preserve_supplied_message_and_reject_none` |
| Причина и стадия отсутствия сессии | `test_session_absent_rejects_code_for_other_reason_or_stage`, `test_session_absent_requires_a_known_reason` |
| Полная разрешённая запись внутренней ошибки | `test_handler_not_registered_code_is_rejected_after_load`, `test_internal_failure_rejects_incompatible_status_pairs` |
| Artifact запрещён, frozen и точный публичный набор полей | `test_failure_models_reject_artifact_even_when_none`, `test_failure_models_are_frozen_for_valid_field_assignments`, `test_failure_specific_fields_cannot_be_replaced_with_valid_values`, `test_failure_dump_contains_exact_public_fields_including_none` |
| Состав union, конкретные типы, ровно 12 троек и неизвестные статусы | `test_application_result_union_contains_exactly_ten_models`, `test_application_result_union_selects_concrete_models_and_preserves_records`, `test_application_result_union_accepts_exactly_the_required_status_triples`, `test_application_result_union_rejects_unknown_status_values` |

**P2.5 — целевой набор до и после изменения:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

**S2.5 — синтаксис при остановке pytest на импорте:**

```powershell
.\.venv\Scripts\python.exe -B -c 'import ast; from pathlib import Path; ast.parse(Path(''tests/application/test_application_results.py'').read_text(encoding=''utf-8-sig''))'
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | До изменения тестов | P2.5 | 125 passed, 0.37 s | 0 | Повторно проверены исходные три модели |
| 2026-09-16 | После добавления тестов | P2.5 | 1 error during collection, 0.38 s | 1 | ImportError: cannot import name 'ApplicationCalculationFailure' from 'exact_orb.application.application_results' |
| 2026-09-16 | Синтаксис | S2.5 | ast.parse завершился без ошибки | 0 | Не заменяет исполнение тестов |
| 2026-09-16 | Связанный и полный наборы | R/F (§4.2) | Не запускались | — | Отложены до реализации 2.6 и успешного целевого набора; отсутствие operation_logging.py из 1.4 также остаётся ограничением R |

После добавления прямых импортов pytest не исполнил ни новые assertions,
ни прежние тесты этого файла. Исходный успешный запуск записан отдельно;
ошибка импорта не доказывает чувствительность новых проверок. Реализация
семи моделей и union не добавлялась, обходов импорта и skip/xfail нет.

Дополнительное AST-сопоставление с исходным текстом подтвердило сохранность
всех 16 прежних функций (13 тестовых и три fixture/helper) и восьми присваиваний,
включая параметризации, MODELS, SUCCESS_MODELS и STATUS_VALUES. Импорты и
docstring расширены для 2.5. Production-модули, остальные тесты, fixtures,
исторические промты и Git index сохранены; вне §1.3 план не изменялся.

K3 остаётся открытым: внешний ApplicationInputRequired обязан отклонять пустой
issues, но преобразование допустимого пустого outcome Handler здесь не выбрано.
AC-19–27 целиком не закрыты. Runtime-flow, WARN, реальные исключения, повторы
commit и session persistence не проверялись; глубокая неизменяемость Issue
не устанавливается. Следующий этап — подготовка 2.6, автоматически не выполнялся.

#### 1.3.10. Фактические результаты 2.6

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Сохранён и выполнен [промт 2.6](../../prompts/2026-09-16/02-application-results/02.6-application-results-union.md).
В начале промта дано объяснение для менеджмента: какие семь ответов добавляются,
зачем интерфейсу согласованные поля и что структура ответа ещё не выполняет
пользовательскую операцию. Используется формулировка «проверка согласованности полей».

В [application_results.py](../../src/exact_orb/application/application_results.py)
добавлены ApplicationInputRequired, ApplicationResolutionFailure,
ApplicationCalculationFailure, ApplicationSessionAbsent, ApplicationStateReadFailure,
ApplicationStateCommitFailure и ApplicationInternalFailure. Реализован обычный union
ApplicationResult из десяти моделей; обновлены docstring модуля и __all__.

Все новые модели frozen и отклоняют неизвестные поля. InputRequired требует
непустой tuple существующих Issue. CalculationFailure проверяет retryable через
публичную describe_failure; открытые технические коды и переданные сообщения
сохраняются. SessionAbsent проверяет четыре сочетания стадии, причины и кода;
InternalFailure — четыре полные записи, включая правило версии. Противоречия
отклоняются, автоматическое исправление значений не выполняется.

Три прежние модели сохранены без изменения. Нет нового I/O, logging, обработки
исключений, вызовов Handler/session или реализации retry. K3 о пустом issues
Handler остаётся открытым; внешний ответ сейчас требует непустой список.

Перед 2.6 по отдельному запросу пользователя внутри всех 39 тестовых функций
добавлены docstrings со ссылками на FR, разделы R3.2, AC и границы проверки.
При выполнении 2.6 весь [test_application_results.py](../../tests/application/test_application_results.py)
сохранён без изменений, включая эти описания, assertions, helpers и параметризации.

**P2.6 — целевой набор до и после реализации:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

**R — связанный набор после успешного P2.6:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
```

| Дата | Проверка | Команда | Результат | Exit code | Ограничение |
|---|---|---|---|---|---|
| 2026-09-16 | До реализации | P2.6 | 1 error during collection, 0.37 s | 1 | ImportError: cannot import name 'ApplicationCalculationFailure' from 'exact_orb.application.application_results'; assertions не исполнились |
| 2026-09-16 | После реализации | P2.6 | 417 passed, 0.86 s | 0 | Все случаи целевого файла, включая проверки 2.5, исполнились; тесты не изменены |
| 2026-09-16 | Связанный набор | R | 1 error during collection, 0.84 s | 1 | ModuleNotFoundError: No module named 'exact_orb.application.operation_logging'; незавершённый этап 1.4 |
| 2026-09-16 | Полный pytest | F (§4.2) | Не запускался | — | Отложен до успешного R; logging-тесты не исключались |

**Связь требований с реализацией и тестами.** Во всех строках ниже результат
«прошли» относится только к P2.6. Точные ссылки на требования каждой из 39 функций
также находятся непосредственно в её docstring; таблица группирует основные проверки.

| Требование | Реализация / что проверено | Тесты в test_application_results.py | Результат | Что остаётся проверить |
|---|---|---|---|---|
| FR-22, §8–9, AC-19 | Десять согласованных моделей и выбор конкретного типа через union | `test_valid_results_preserve_the_complete_contract`, `test_failure_models_preserve_complete_records`, `test_application_result_union_selects_concrete_models_and_preserves_records` | Прошли | Выбор ответа из runtime outcomes в execute |
| §9, AC-20, AC-23 | Четыре записи SessionAbsent; код соответствует стадии и reason | `test_failure_models_preserve_complete_records`, `test_session_absent_rejects_code_for_other_reason_or_stage`, `test_session_absent_requires_a_known_reason` | Прошли | Исчезновение реальной сессии между load и commit |
| FR-22, §8–9, AC-22 | Ровно десять членов union и точное множество 12 допустимых троек | `test_application_result_union_contains_exactly_ten_models`, `test_application_result_union_accepts_exactly_the_required_status_triples`, `test_application_result_union_rejects_unknown_status_values` | Прошли | Требование о модельном множестве подтверждено; runtime-flow не проверялся |
| FR-22, §9, AC-23 | Противоречивые code/detail_code/retryable отклоняются; обязательные технические причины сохранены | `test_results_reject_contradictory_reaction_fields`, `test_failure_models_reject_success_code`, `test_technical_failure_models_require_a_detail_code`, `test_failure_models_without_technical_reason_reject_detail_code`, `test_failure_models_reject_contradictory_fixed_retryability` | Прошли | Нормализация реальных отказов нижележащих компонентов |
| FR-22, §9, §12, AC-23 | Непустые структурированные issues; artifact есть только в успешных ответах; публичные поля соответствуют модели | `test_input_required_preserves_ordered_structured_issues`, `test_input_required_rejects_missing_empty_or_invalid_issues`, `test_success_results_require_a_valid_artifact`, `test_superseded_rejects_an_artifact_argument`, `test_failure_models_reject_artifact_even_when_none`, `test_failure_dump_contains_exact_public_fields_including_none` | Прошли | K3: решение о преобразовании пустого issues Handler |
| FR-22–23, §9–10, AC-23 | Calculation retryability проверяется существующей политикой, включая неизвестные коды | `test_calculation_failure_rejects_retryability_inconsistent_with_code`, `test_failure_models_preserve_complete_records` | Прошли | Фактический повтор операции; WARN неизвестного кода |
| FR-22, §9, AC-23 | InternalFailure связывает code, статусы и допустимую версию | `test_handler_not_registered_code_is_rejected_after_load`, `test_internal_failure_rejects_incompatible_status_pairs`, `test_loaded_failures_require_known_nonnegative_version`, `test_failures_without_known_state_reject_numeric_version` | Прошли | Перехват реального исключения и выбор стадии в execute |
| FR-22, §9, AC-24 | Присваивание допустимых значений полям созданных моделей запрещено | `test_results_are_frozen_even_for_valid_field_assignments`, `test_success_results_reject_replacing_a_valid_artifact`, `test_failure_models_are_frozen_for_valid_field_assignments`, `test_failure_specific_fields_cannot_be_replaced_with_valid_values` | Прошли | Глубокая неизменяемость вложенных Issue/ChartArtifact здесь не устанавливается |
| FR-23, §10, AC-25 — поля ответа | Поля готовой реакции, точные тексты и fallback сохраняются в модели | `test_failure_models_preserve_complete_records`, `test_valid_results_preserve_the_complete_contract` | Прошли | Запись WARN; нормализация исключений и AC-21 |
| §12, AC-26 — модельная часть | Два переданных UUID сохраняются; отсутствие или невалидный UUID отклоняются | `test_valid_results_preserve_the_complete_contract`, `test_failure_models_preserve_complete_records`, `test_results_require_a_valid_run_id`, `test_failure_models_require_a_valid_run_id` | Прошли | Сквозной run_id в execute и событиях |
| §9, §12, AC-27 — модельная часть | Версия обязательна после наблюдения состояния; для остальных ответов только None | `test_results_preserve_versions_including_the_lower_bound`, `test_results_require_a_version_within_the_model_bound`, `test_loaded_failures_preserve_known_nonnegative_version`, `test_loaded_failures_require_known_nonnegative_version`, `test_failures_without_known_state_reject_numeric_version` | Прошли | Получение версии из реальных snapshot/commit outcomes |

417 случаев — результат реального pytest, а не число функций или статическая
оценка параметризаций. Набор включает прежние 125 случаев и новые 292 случая.
Проверка union перебрала по 240 сочетаний статусов для 23 корректных исходных
записей; все принятые тройки совпали с §8.

Сравнение исходного состояния подтвердило сохранность тестов, fixtures,
failure_policy.py, остальных production-файлов, исторических промтов и Git index.
AST трёх прежних классов не изменён. План изменён только в §1.3. Следующий шаг —
подготовка 1.4; до раздела 3 также остаётся предусмотренный планом срез
неизменяемости RunContext. Эти этапы автоматически не выполнялись.

#### 1.3.11. Фактические результаты 1.4

Окружение этой исторической записи — локальный Windows checkout. Результат
F: 2152 passed не является свидетельством переносимости на Linux. В ревью
2026-09-17 сообщён Linux/Python 3.12: 2151 passed, 1 failed в artifact baseline;
это внешний отчёт, здесь такой прогон не воспроизведён. ОС как единственная
причина различия не установлена; baseline и вычисления в 3.R2 не менялись.

**Дата:** 2026-09-16. **Ветка:** `feat/application-orchestrator`.
Исправлен по согласованным замечаниям, сохранён и выполнен
[промт 1.4](../../prompts/2026-09-16/01-application-foundations/01.4-lifecycle-logging-functions.md).
Уточнены формат getMessage(), коллекции кодов и типы значений, общий запрет
traceback, различие уровней Handler/Orchestrator и два независимых эксперимента
для проверки чувствительности тестов. Понятное описание результата находится
в начале промта.

Добавлен [operation_logging.py](../../src/exact_orb/application/operation_logging.py):
пять синхронных keyword-only функций штатного logger, четыре вида событий,
отдельные формы terminal result/cancelled, WARNING для второй попытки,
опциональная известная версия у stage/attempt и полный набор nullable-полей
у результата. История ошибок передаётся литералом tuple, сохраняя порядок
и повторы. Длительности и другие факты готовит вызывающий код.

Сначала реализация прошла неизменённый тестовый файл. После экспериментов
в десять функций [test_orchestrator_logging.py](../../tests/application/test_orchestrator_logging.py)
добавлены только русские docstring с требованиями и границами проверки.
Assertions, параметризации, fixtures и helpers не изменены.

**Команды этого этапа** (из корня репозитория):

```powershell
# L1.4 — целевой набор
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
# A1.4 — запрет аргумента payload
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py::test_payload_keywords_are_rejected_after_valid_call_positive_control -q
# B1.4 — точный набор полей started
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py::test_started_records_command_type_and_run_id_at_info -q
# C1.4 — список собранных тестов до и после docstring
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py --collect-only -q
# R — связанные проверки
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# F — полный pytest
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

| Проверка 2026-09-16 | Команда | Фактический результат | Exit code |
|---|---|---|---|
| До реализации | L1.4 | 1 error during collection, 0.42 s; ModuleNotFoundError: exact_orb.application.operation_logging | 1 |
| Реализация на неизменённых тестах | L1.4 | 106 passed, 0.32 s | 0 |
| Временно разрешён payload у log_operation_started | A1.4 | 1 failed, 29 passed, 0.27 s; DID NOT RAISE TypeError | 1 |
| После точного восстановления модуля | A1.4 | 30 passed, 0.21 s | 0 |
| Лишнее поле payload в started, сигнатура сохранена | B1.4 | 4 failed, 0.55 s; actual.keys() != expected.keys() | 1 |
| После точного восстановления модуля | B1.4 | 4 passed, 0.18 s | 0 |
| Весь набор после обоих экспериментов | L1.4 | 106 passed, 0.29 s | 0 |
| До / после добавления docstring | C1.4 | 106 tests collected, 0.17 / 0.18 s; списки всех node IDs совпали | 0 / 0 |
| После docstring | L1.4 | 106 passed, 0.27 s | 0 |
| Связанный набор | R | 1233 passed, 12.65 s | 0 |
| Полный pytest | F | 2152 passed, 39.52 s | 0 |

Оба эксперимента выполнялись отдельно с восстановлением исходных байтов
production-файла в finally. После каждого сравнение байтов и SHA-256 подтвердило
восстановление; намеренных ошибок и резервных файлов в репозитории не осталось.
Эксперимент A упал в случае `[log_operation_started-arguments0-payload]`,
эксперимент B — во всех четырёх сочетаниях command_type/run_id на сравнении
наборов полей. Ошибок импорта или синтаксиса вместо этих assertions не было.
Это свидетельства чувствительности двух конкретных проверок, не общий аудит PII.

До docstring SHA-256 тестового файла совпал с исходным. После добавления
docstring AST без строк документации совпал с исходным; diff содержит только
десять вставок docstring. Все 106 node IDs сохранены.

| Требование | Тесты в test_orchestrator_logging.py | Результат и граница |
|---|---|---|
| Карточки 1.3–1.4; FR-27, §11.5 | `test_logging_api_accepts_only_explicit_keyword_arguments` | Прошёл; форма API, не весь application-flow |
| FR-26–27, §11.5; AC-26/29/33 частично | `test_started_records_command_type_and_run_id_at_info` | Прошёл; поля, run_id и INFO одного вызова. Лишнее поле обнаружено экспериментом B |
| FR-26, §11.5; AC-26/30 частично | `test_stage_records_typed_and_unexpected_outcomes` | Прошёл; уровни, версия 0 и отсутствие неизвестной версии. Реальный load/Handler не вызывался |
| FR-26, §11.5; AC-26/31 частично | `test_commit_attempt_fields_and_warning_for_every_second_attempt` | Прошёл; номер, nullable detail_code, версия и WARNING попытки 2. Retry не выполнялся |
| FR-26, §11.5 | `test_duration_values_and_default_omission_of_unknown_version` | Прошёл; передача готовых допустимых длительностей, не измерение времени |
| FR-26, §11.5; AC-26/29 частично | `test_result_terminal_fields_and_levels_for_consistent_statuses` | Прошёл; поля результата и уровни, не валидация ApplicationResult |
| FR-26, §11.5 | `test_result_preserves_retry_history_and_supplied_total_duration` | Прошёл; порядок/дубли кодов и переданная сумма, не накопление в execute |
| FR-26, §11.5 | `test_delivery_cancellation_keeps_successful_result_terminal` | Прошёл; delivery_cancelled сохраняет успешный результат, shield не проверялся |
| FR-26, §11.5; AC-26/29 частично | `test_cancelled_terminal_omits_result_fields_with_result_positive_control` | Прошёл; форма отмены с позитивным контролем результата, не настоящий CancelledError |
| FR-27, §11.5; AC-33 частично | `test_payload_keywords_are_rejected_after_valid_call_positive_control` | Прошёл; запрещённый аргумент не создаёт запись. Расширение API обнаружено экспериментом A |

**Новая контрольная точка:** R = 1233 passed, F = 2152 passed для текущего
состава проекта. Прежние 1598 passed из §1.3.3 и ошибки импорта в §1.3.3–1.3.10
сохраняются как исторические результаты. Текущие общие прогоны включили
ранее проверявшиеся отдельно 27 случаев политики и 417 случаев моделей.

План вне §1.3, прежние production-файлы, остальные тесты/fixtures, исторические
промты, несвязанные пользовательские файлы и Git index сохранены.
Проверены новый модуль и новый промт, git diff --check и Markdown-ссылки.

AC-26 и AC-29–33 целиком не закрыты. Подключение событий к execute, их порядок,
соответствие фактическим save, retry, shield, реальные отмены и отсутствие PII
во всём flow этим этапом не проверялись. Следующие корректирующие срезы моделей
и RunContext до группы 3 автоматически не выполнялись; K3/X1/X2 сохраняются.

#### 1.3.12. Подготовка промта 3.1 — 2026-09-17

По запросу пользователя сохранён
[промт 3.1 — тесты входа и выбора обработчика команды](../../prompts/2026-09-16/03-entry-and-routing/03.1-orchestrator-entry-and-routing-tests.md).
В начале объяснено, что проверяем и зачем: обязательный контекст операции,
точное назначение Handler, отказ неизвестной команды до чтения сессии,
защитная копия реестра и связь отказа с журналом по исходному run_id.

Промт сверён с карточками 3.1–3.2, R3.2, ADR-0006, связанными диаграммами,
текущими моделями, logging-функциями и существующими тестовыми helpers.
Разделены проверки отказа, доступные после 3.2, положительные контроли
после 4.2/5.2 и полный успешный unit-сценарий после 6.4.
В тестах предусмотрены docstrings со связью требований и проверяемого поведения.

Это подготовка задания, а не выполнение 3.1: production-код и тесты не менялись,
pytest не запускался, новые AC не закрыты. Отдельные корректирующие срезы
политики/моделей и RunContext перед группой 3 не выполнены этим действием;
их статус требуется сверить перед исполнением промта. Вопрос K3 сохранён.
Обновлён общий README серии; номера карточек, зависимости и матрица AC сохранены.

Проверки подготовки: `git diff --check` — exit code 0; отдельная структурная
проверка трёх документов через `.\.venv\Scripts\python.exe -B -` — exit code 0,
92 локальные ссылки существуют, блоки кода парные, whitespace нового промта
и разделение имён ранних/поздних тестов проверены. Git сообщил только о
будущем преобразовании LF в CRLF; ошибок whitespace не обнаружено.

#### 1.3.13. Фактические результаты 3.1 — 2026-09-17

**Основание запуска:** после подготовки промта пользователь явно поручил
«Сохрани и выполни промт». Это разрешение выполнить тестовую карточку 3.1
независимо от предварительных корректировок 2.R1 и RunContext. Их область,
frozen/extra и вопрос K3 не решались и остаются открытыми.

**Ветка:** `feat/application-orchestrator`.
**HEAD:** `4c289a673efb0fb21eaed83f58ea205564f6d2e6`.
Сохранённый промт 3.1 не изменялся. Созданы:

- [test_orchestrator_routing.py](../../tests/application/test_orchestrator_routing.py):
  11 тестовых функций; по исходным параметризациям предусмотрено 13 случаев.
  Это статический подсчёт, не результат pytest collection;
- [orchestrator_fakes.py](../../tests/application/orchestrator_fakes.py):
  context и Handler с явно заданными typed outcomes и общим журналом обращений
  одного теста. Аргументы записываются по identity; CAS и расчёт не имитируются.

У каждой тестовой функции есть русский docstring с назначением проверки,
ссылкой на R3.2 и границей подтверждения. Отрицательные routing-сценарии
дополнены положительными вызовами зарегистрированных Handler; добавление,
удаление и замена внешнего назначения проверяются через публичный execute.
Один положительный unit-сценарий проходит до Committed. Lifecycle-проверка
отказа использует настоящие logging-записи и два разных входных UUID.

Команды выполнены из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -q
.\.venv\Scripts\python.exe -B -c "import ast,pathlib; paths=['tests/application/test_orchestrator_routing.py','tests/application/orchestrator_fakes.py']; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8-sig'), filename=p) for p in paths]; print('syntax OK')"
git diff --check
```

| Проверка | Фактический результат | Exit code |
|---|---|---:|
| Целевой pytest | `ModuleNotFoundError: No module named 'exact_orb.application.orchestrator'`; `1 error in 0.41s`, остановка при collection | 1 |
| AST двух новых файлов | `syntax OK` | 0 |
| Дополнительная статическая проверка через `.\.venv\Scripts\python.exe -B -` | 11 функций с requirement-docstrings; 5 ранних и 6 поздних функций; прямой импорт API, без skip/xfail/подмен; синтаксис и whitespace проверены | 0 |
| `git diff --check` | Ошибок whitespace нет; предупреждение о будущем преобразовании LF → CRLF в документах | 0 |

**Исполнено 0 тестовых функций и 0 assertions routing.** Ошибка ожидаема:
production-модуль вводится в 3.2. Она не доказывает чувствительность тестов,
валидность runtime-подготовки данных или выполнение проверяемых AC.
Связанный R и полный F не запускались по §4.2: целевой набор пока не может
исполниться. Исторические результаты 1.4 и группы 2 остаются прежними.

| Требование | Что проверяется | Точные имена тестов | Фактический результат | Что остаётся проверить и когда |
|---|---|---|---|---|
| §1.3, FR-01, AC-1 | Обязательный keyword-only run и TypeError до вызовов зависимостей | `test_execute_requires_run` | Не исполнился: импорт API | После 3.2; позитивный вызов — после 5.2 |
| UC-11, FR-03–04, AC-4, части AC-5/26 | Полный ответ HANDLER_NOT_REGISTERED до load, без чужого Handler | `test_unknown_command_returns_failure_before_load` | Не исполнился: импорт API | После 3.2 |
| FR-04, AC-3 | Подкласс не получает Handler базового типа без отдельного назначения | `test_subclass_without_exact_registration_is_rejected` | Не исполнился: импорт API | Отказ — 3.2; положительные пары — 5.2 |
| FR-02, FR-04, FR-06–08, AC-2/3, часть AC-5 | Точный выбор базового/дочернего Handler, порядок load → handle, identity аргументов | `test_exact_type_reaches_handler`, `test_explicit_child_registration_selects_own_handler` | Не исполнились: импорт API | После 4.2/5.2 |
| FR-05 | Внешнее добавление не влияет на старый экземпляр; новый принимает назначение | `test_registry_addition_does_not_change_existing_instance`, `test_new_instance_accepts_added_type` | Не исполнились: импорт API | Отрицательная часть — 3.2; положительная — 5.2 |
| FR-05 | Внешние удаление и замена сохраняют исходный Handler | `test_external_mapping_removal_keeps_original_handler`, `test_external_mapping_replacement_keeps_original_handler` | Не исполнились: импорт API | После 5.2; полнота production registry остаётся 10.1–10.2 |
| §1.4, FR-11, AC-3/5, части AC-10/26 | Полный положительный unit-путь, original version и delta в одном save | `test_known_command_completes_with_commit` | Не исполнился: импорт API | После 6.4; реальный CAS и persistence — последующие integration-этапы |
| FR-26, §11.5, §12, части AC-26/29 | Один started/terminal до возврата, исходный UUID, отсутствие незапущенных стадий | `test_unknown_command_logs_one_start_and_terminal_before_return` | Не исполнился: импорт API | Routing-ветка — 3.2; остальные ветки и сквозные AC — позже |

Ранняя выборка 3.2 содержит 5 функций (6 предусмотренных параметризованных
случаев); поздние имена и ids не попадают в её `-k`. Остальные 6 функций
предусматривают 7 случаев. Весь routing-файл требуется повторить в 6.4.
Критерии приёмки по этой записи не объявляются закрытыми.

Production-код, прежние тесты/fixtures и исторические промты не менялись.
Изменения плана ограничены §1.3; README обновлён по фактическому статусу.
Контроль SHA-256 подтвердил сохранность 420 предшествующих файлов вне
allowlist, Git index и текста плана вне §1.3. Проверены 94 локальные ссылки
README/плана и парность блоков кода; статически подтверждено разделение
13 предусмотренных случаев на 6 ранних и 7 поздних, exit code 0.
Следующий основной этап — 3.2; его реализация автоматически не выполнялась.

#### 1.3.14. Подготовка промта 3.2 — 2026-09-17

По запросу пользователя сохранён
[промт 3.2 — конструктор координатора и отказ для неизвестной команды](../../prompts/2026-09-16/03-entry-and-routing/03.2-orchestrator-constructor-and-routing-failure.md).
В начале объяснены назначение координатора, обязательный контекст операции,
фиксация назначений Handler и отказ до чтения сессии. Техническая часть сверена
с R3.2, ADR-0006, карточкой 3.2, существующими тестами 3.1 и logging helpers.

Область исполнения — новый application/orchestrator.py, журнал §1.3 и README.
Тесты и fakes должны сохраниться без изменений. Промт требует исполнить
раннюю выборку, затем весь routing-файл и связанный R с классификацией
отложенных положительных случаев; F запускается только после успешного R.

Для неполного flow групп 3–6 в промте явно предложена временная остановка
зарегистрированной команды через NotImplementedError непосредственно в execute.
Это техническая граница промежуточного модуля, не целевой application-ответ:
модуль не подключается к транспорту, lifecycle-контракт известной ветки ещё
не выполнен, точку продолжения заменяет настоящий load в 4.2. Фиктивные
результаты и скрытое закрытие положительных проверок запрещены.

Это только подготовка задания. Production-код, тесты, исходный промт 3.1,
номера карточек и матрица AC не менялись; pytest и реализация 3.2 не запускались.
Статус корректировок 2.R1, RunContext и вопроса K3 сохранён. README дополнен
ссылкой на промт и его текущим статусом.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0, 98 локальных ссылок,
парные блоки кода, whitespace нового промта и соответствие пяти названных
тестов исходному файлу. Статически подтверждены 6 ранних и 7 поздних случаев.
SHA-256 подтвердил сохранность 422 файлов вне области подготовки, Git index
и текста плана вне §1.3. Эти проверки не являются запуском тестов координатора.

#### 1.3.15. Выполнение 3.2 — 2026-09-17

**Основание:** пользователь поручил сохранить и выполнить подготовленный промт 3.2.
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `4c289a673efb0fb21eaed83f58ea205564f6d2e6`.

Создан [application/orchestrator.py](../../src/exact_orb/application/orchestrator.py):
обязательные зависимости конструктора, shallow copy назначений Handler,
обязательный RunContext, lookup по точному type(command). Неизвестная команда
получает ApplicationInternalFailure/HANDLER_NOT_REGISTERED до любого обращения
к сессии. Реакция берётся из failure_policy; started и terminal записываются
существующими logging-функциями с исходным run_id.

В соответствии с §5 исполняемого промта найденный Handler приводит к явно
обозначенному временному NotImplementedError. Load/handle/save не реализованы,
положительный lifecycle ещё не завершён; модуль не подключён к транспорту.
Это ограничение промежуточной сборки, не новый публичный application outcome.

Ранняя команда выполнена до и после создания модуля:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
```

| Момент | Результат | Exit code |
|---|---|---:|
| До реализации | `ModuleNotFoundError: No module named 'exact_orb.application.orchestrator'`; `1 error in 0.50s` | 1 |
| После реализации, исходные тесты сохранены | `2 failed, 4 passed, 7 deselected in 0.41s` | 1 |

Прошли `test_execute_requires_run`,
`test_unknown_command_returns_failure_before_load`,
`test_subclass_without_exact_registration_is_rejected` и
`test_registry_addition_does_not_change_existing_instance`.

Два сбоя:

```text
tests/application/test_orchestrator_routing.py::test_unknown_command_logs_one_start_and_terminal_before_return[first-run]
tests/application/test_orchestrator_routing.py::test_unknown_command_logs_one_start_and_terminal_before_return[second-run]
```

**Корневая причина:** созданная в 3.1 фикстура `operation_records` возвращает
`caplog.records` во время setup. Pytest перед call вызывает
`LogCaptureHandler.reset()` и заменяет список через `self.records = []`.
Тест продолжает читать прежний пустой список. В отчёте `Captured log call`
присутствуют настоящий INFO started и WARNING terminal с корректным run_id;
ошибка не вызвана отсутствием production logging.

Причина подтверждена чтением установленного `.venv/Lib/site-packages/_pytest/logging.py`:
`LogCaptureHandler.reset` (строка 401), `LogCaptureFixture.records` (472),
`LoggingPlugin._runtest_for` (828). Точная диагностическая команда:

```powershell
.\.venv\Scripts\python.exe -B -c "import inspect,_pytest.logging as log; print(log.__file__); print(inspect.getsource(log.LogCaptureHandler.reset)); print(inspect.getsource(log.LogCaptureFixture.records.fget)); print(inspect.getsource(log.LoggingPlugin._runtest_for))"
```

Команда завершилась с exit code 0. Минимальная подготовленная корректировка:
передавать из фикстуры сам `caplog`, читать его актуальное `.records` в тесте
и уточнить две аннотации — четыре строки, без изменения assertions и сценариев.
Промт 3.2 запрещает менять тесты, поэтому отдельно запрошено разрешение на эту
правку; до ответа исходный тестовый файл сохранён.

Весь routing-файл, R и F пока не запускались: ранняя выборка не прошла,
а эти запуски по промту выполняются после неё. Семь положительных случаев
ещё не проверены этим запуском. Результаты 1.4 и группы 2 не переименованы
в текущие результаты. AC-26/29 не закрыты по визуальному наличию записей.

Проверка синтаксиса нового модуля и `git diff --check` дали exit code 0.
SHA-256 подтвердил сохранность 423 предшествующих файлов вне allowlist,
Git index и текста плана вне §1.3. Предварительные вопросы 2.R1, RunContext
и K3 не решались. Следующая основная карточка 4.1 не выполнялась.

#### 1.3.16. Подготовка корректирующего промта 3.R1 — 2026-09-17

По запросу «Напиши следующий промт» подготовлен отдельный
[промт 3.R1 — исправить захват логов и завершить проверку 3.2](../../prompts/2026-09-16/03-entry-and-routing/03.R1-caplog-fixture-and-routing-verification.md).
Корректировка поставлена перед основной карточкой 4.1, поскольку ранняя
приёмка 3.2 блокируется установленным дефектом фикстуры 3.1.

В начале промта человеческим языком объяснён ложный отказ: тест сохраняет
список setup, а реальные события попадают в новый список call. Техническая
часть задаёт четыре точные замены для передачи caplog и чтения его актуального
records, сохранность assertions/параметризаций и команды повторной проверки.
Причина сверена с текущим тестом и исходниками установленного pytest.

Будущее исполнение 3.R1 имеет собственный узкий allowlist тестового файла,
§1.3 плана и README; production-код и исторический промт 3.2 сохраняются.
Приёмка различает исправление двух logging-проверок, раннюю выборку 3.2,
семь ещё не реализованных положительных случаев и результаты R/F.

Сейчас промт только сохранён: тестовая фикстура не исправлялась, pytest не
запускался, результаты §1.3.15 остаются текущими. Обновлены индекс README,
запись в журнале и перечисление дополнительных карточек в шапке плана.
Нумерация 36 основных карточек, их зависимости и матрица AC не изменены.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0, 101 локальная ссылка,
парные блоки кода и корректный whitespace нового промта. Четыре замены
применены только к строке в памяти: синтаксис корректен, узлы assert совпадают,
тестовый файл не записывался. SHA-256 подтвердил сохранность 424 файлов вне
области подготовки, Git index и плана вне §1.3 и строки перечня карточек.

#### 1.3.17. Выполнение 3.R1 — 2026-09-17

**Основание:** пользователь поручил сохранить и выполнить подготовленный
[промт 3.R1](../../prompts/2026-09-16/03-entry-and-routing/03.R1-caplog-fixture-and-routing-verification.md).
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `4c289a673efb0fb21eaed83f58ea205564f6d2e6`.

**Результат:** тест читает журнал текущего выполнения. Два ложных отказа
устранены, ранняя приёмка 3.2 прошла. Координатор уже записывал нужные события;
ошибка была в сохранении тестовой фикстурой списка записей фазы setup.
Pytest заменяет этот список перед call, поэтому тест видел пустой старый список.
Причина повторно подтверждена диагностической командой inspect из §1.3.15,
exit code 0: `reset()` заменяет `self.records`, а свойство `caplog.records`
возвращает текущий список обработчика.

В [test_orchestrator_routing.py](../../tests/application/test_orchestrator_routing.py)
изменены ровно четыре строки: фикстура передаёт `caplog`, тест читает
`operation_records.records` непосредственно после `await execute(...)`,
две аннотации уточнены до `pytest.LogCaptureFixture`. Настройка и восстановление
logger, assertions, сценарии и production-код сохранены.

Точные команды запускались из корня репозитория последовательно:

```powershell
# Два проблемных случая: одна и та же команда до и после исправления
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "unknown_command_logs_one_start_and_terminal_before_return" -q

# Ранняя выборка 3.2 после исправления
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q

# Весь routing-файл
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -q

# Связанный набор R
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
```

| Запуск | Фактический результат | Exit code |
|---|---|---:|
| Два случая до исправления | `2 failed, 11 deselected in 0.35s` | 1 |
| Те же случаи после исправления | `2 passed, 11 deselected in 0.27s` | 0 |
| Ранняя выборка 3.2 | `6 passed, 7 deselected in 0.30s` | 0 |
| Весь routing-файл | `7 failed, 6 passed in 0.45s` | 1 |
| R | `7 failed, 1239 passed in 13.89s` | 1 |

До исправления падали оба точных node ID:

```text
tests/application/test_orchestrator_routing.py::test_unknown_command_logs_one_start_and_terminal_before_return[first-run]
tests/application/test_orchestrator_routing.py::test_unknown_command_logs_one_start_and_terminal_before_return[second-run]
```

Оба падали на сравнении пустого списка с ожидаемыми started/terminal, при
наличии настоящих INFO/WARNING событий в `Captured log call`. После правки
оба случая прошли со всеми прежними assertions.

В полном routing-файле и R совпали все семь failures:

```text
tests/application/test_orchestrator_routing.py::test_exact_type_reaches_handler
tests/application/test_orchestrator_routing.py::test_explicit_child_registration_selects_own_handler[base]
tests/application/test_orchestrator_routing.py::test_explicit_child_registration_selects_own_handler[child]
tests/application/test_orchestrator_routing.py::test_external_mapping_removal_keeps_original_handler
tests/application/test_orchestrator_routing.py::test_external_mapping_replacement_keeps_original_handler
tests/application/test_orchestrator_routing.py::test_new_instance_accepts_added_type
tests/application/test_orchestrator_routing.py::test_known_command_completes_with_commit
```

Причина каждого — `NotImplementedError` в `application/orchestrator.py:86`:
`Registered command execution will be implemented in steps 4–6`.
Все семь тестов дошли до `execute`; создание `BuildNatalSuccess` в последнем
случае прошло. Ошибок импорта, невалидных данных и новых сбоев фикстуры нет.
Первые шесть случаев ожидают load/Handler в 4.2/5.2, последний — полный
unit-путь с commit в 6.4. Это реальные падения, а не skip/xfail или успешный R.

**F не запускался:** R не прошёл; по условию карточки полный набор выполняется
только после успешного R. Исторические результаты F из §1.3.11 не являются
проверкой текущего состава проекта. Сетевые и платные smoke-тесты не запускались.

| Проверяемое правило | Тесты | До исправления | После исправления | Граница подтверждения |
|---|---|---|---|---|
| Актуальные события доступны после execute | Два случая `test_unknown_command_logs_one_start_and_terminal_before_return` | 2 failed, 11 deselected | 2 passed, 11 deselected | Регрессионное покрытие ошибки фикстуры |
| Исходный run_id и один started/terminal | Те же два случая | Наблюдение блокировалось старым списком | Все assertions порядка, уровней, UUID и terminal-полей исполнились и прошли | Только routing-часть AC-26/29 |
| Прежние правила входа и отказа сохранены | Остальные четыре ранних теста 3.1 | 4 passed в запуске 3.2, §1.3.15 | Все четыре снова прошли в выборке из 6 passed | Полнота позитивного routing ещё не доказана |
| Положительный flow | Семь перечисленных поздних случаев | Не исполнялись в первом раннем прогоне 3.2 | Каждый падает на явно незавершённой зарегистрированной ветке, NotImplementedError | Ожидают 4.2/5.2 и 6.4 |

Проверка сохранности через `.\.venv\Scripts\python.exe -B -` сопоставила
исходные байты untracked-теста с результатом четырёх замен: совпадение точное,
без нормализации остального файла. По AST совпали все 46 узлов assert,
имена, декораторы, параметризации, ids и docstrings 11 тестовых функций;
состав 13 случаев сохранён. Полный AST изменился только в разрешённых местах.
SHA-256 подтвердил сохранность 424 файлов вне allowlist, включая production,
fakes, другие тесты и прежние промты, а также Git index и текста плана вне §1.3.

`git diff --check` — exit code 0. Scoped diff и `git status --short` просмотрены;
untracked-тест дополнительно сопоставлен с исходным снимком. Веток, коммитов,
push и PR не создавалось. Исторические записи §1.3.13/15/16 сохранены.

Исправление фикстуры не закрывает целиком AC-3, FR-05, AC-5, AC-26/29,
конкурентность и сохранение сессии. Вопросы 2.R1, неизменяемости/extra
RunContext и K3 остаются открытыми. Следующий основной шаг — **4.1, тесты
load и исходной версии**; он автоматически не выполнялся.

#### 1.3.18. Выполнение 3.R2 — 2026-09-17

**Основание:** пользователь поручил написать промт и исправить согласованные
замечания ревью. Сохранён и выполнен
[промт 3.R2](../../prompts/2026-09-16/03-entry-and-routing/03.R2-orchestrator-contract-hardening.md).
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `4c289a673efb0fb21eaed83f58ea205564f6d2e6`.
**Окружение:** Windows 11, Python 3.14.0, Pydantic 2.13.5, pytest 9.1.1.

**Причина:** прежние тесты подтверждали корректные входы и frozen верхнего
уровня. Присваивание обходило UTC-валидацию RunContext; модели принимали
приводимые версии и произвольные сообщения; logging повторно принимал поля
ответа и кодировал открытые строки неоднозначным key=value.

Теперь RunContext запрещает присваивание трём полям. ApplicationResult
отклоняет bool/string/float вместо версии, пустой persistence detail_code и
сообщение, не совпадающее с политикой. Политика отклоняет нерелевантные для
kind аргументы не None. Предопределённые тексты, retryable и fallback сохранены.

Result-terminal получает ApplicationResult, проецирует только разрешённые
поля и не может получить отдельные противоречащие им аргументы. Lifecycle
message имеет вид `<event> <JSON object>` в одной строке; строки сохраняются
при JSON round-trip без инъекции полей и новых записей. Проверяются конечные
неотрицательные длительности, диапазоны попыток и версии commit outcomes;
ошибки контракта отклоняются через LifecycleEventError до записи.
Время, порядок событий, история реальных save и обработка ошибки logging
после состоявшегося commit остаются обязанностями будущего execute, не
доказанными свойствами ещё отсутствующей commit-ветки.

Изменены RunContext, policy/results/logging, один вызов terminal в координаторе
и пять соответствующих тестовых файлов. Ранее допускавший произвольный текст
тест изменён намеренно вместе с контрактом; независимые эталонные тексты
сохранены. Первые 106 logging-случаев прошли после адаптации API, затем
добавлено 70 регрессионных случаев. Routing проверяет тот же набор полей,
порядок и уровни через JSON; семь будущих сценариев не ослаблялись.
Требования R3.2, ревизия ADR-0006 и diagram 010 синхронизированы.

| Правило | Покрытие | Фактическое подтверждение |
|---|---|---|
| RunContext нельзя переприсвоить | `test_run_context_rejects_assignment_without_changing_original` | 4 случая: корректные новые значения и naive deadline отклонены; исходный объект сохранён |
| Версия строго int | Дополнены существующие version-bound tests | bool, string и float отклонены при сохранённых положительных границах |
| Persistence code непустой, сообщение точно по политике | `test_persistence_failure_rejects_empty_detail_code`, `test_failure_models_require_the_policy_message`, `test_superseded_requires_exact_policy_message` | Корректные записи проходят, пустой код и произвольные сообщения отклонены |
| Аргументы политики соответствуют kind | `test_irrelevant_policy_arguments_are_rejected`, `test_persistence_policy_requires_nonempty_code` | Положительные вызовы и None сохранены; нерелевантные содержательные значения и пустой persistence code отклонены |
| Terminal соответствует ответу | Прежние terminal cases и `test_terminal_cannot_override_the_returned_result` | Поля извлечены из настоящей модели; отдельные override keywords запрещены |
| Строки не меняют структуру события | `test_strings_cannot_inject_fields_or_physical_records` | 4 вида записи: кавычки, слеши, key=value, CR/LF/tab/U+2028 сохраняются внутри одного JSON-значения |
| Недопустимые числовые метаданные не пишутся | `test_invalid_durations_are_rejected_before_logging`, `test_attempt_numbers_are_checked_at_runtime`, `test_attempt_version_matches_its_outcome` | Отрицательные/NaN/Infinity, неверные попытки и версии отклонены после положительных контролей |

Точные команды и результаты:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application/test_application_failure_policy.py tests/application/test_application_results.py -q
# 552 passed in 1.01s; exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
# После адаптации: 106 passed in 0.52s; после регрессий: 176 passed in 0.57s; exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
# 6 passed, 7 deselected in 0.29s; exit code 0

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# 7 failed, 1392 passed in 16.39s; exit code 1

.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# 7 failed, 2311 passed in 42.32s; exit code 1

git diff --check
# exit code 0
```

В R и F совпадают ровно семь node IDs из §1.3.17: exact type, два случая
explicit child registration, removal/replacement mapping, new instance и
known command with commit. Каждый падает только на явном NotImplementedError
в `application/orchestrator.py:80`. Новых failures нет. R/F остаются
непройденными. Полный набор выполнен по явной проверке этой корректировки
после классификации R: изменение RunContext затрагивает потребителей вне R.
Локальный artifact baseline прошёл в составе F; его эталон не изменялся.
Linux-прогон не выполнялся, причинность ОС не доказана.

**Отдельно подготовлена, не выполнена**
[карточка 2.R2](../../prompts/2026-09-16/02-application-results/02.R2-nested-result-immutability-decision.md).
Глубокая неизменяемость Issue/ChartArtifact требует выбора границы с учётом
действующего artifact-контракта §6.1.4. В 3.R2 эти общие модели не менялись;
глубокая часть AC-24 не закрыта. Политика extra RunContext, K3 и семантика
retryable чтения сессии сохранены. Discriminator и расчётный baseline не менялись.

Структурная проверка через `.\.venv\Scripts\python.exe -B -` дала exit code 0:
6 Markdown-файлов, 107 локальных ссылок, парные code fences, start/end,
note/end note и box/end box диаграммы. SHA-256 подтвердил сохранность
412 файлов вне allowlist и Git index; новых файлов вне области нет.
Scoped diff и статус просмотрены. Java/PlantUML в текущем окружении не найдены; диаграмма
не рендерилась. Сетевые и платные smoke не запускались. Коммитов, веток,
push и PR не создавалось. Следующая основная карточка — 4.1, автоматически
не выполнялась.

#### 1.3.19. Подготовка промта 4.1 — 2026-09-17

По запросу «Напиши следующий промт» сохранён
[промт 4.1 — тесты загрузки сессии и исходной версии](../../prompts/2026-09-16/04-session-load/04.1-orchestrator-session-load-tests.md).
Он продолжает основной план после 3.2 и выполненной корректировки 3.R2.
Во вводной части для менеджеров объяснены различия между отсутствующей
сессией и ошибкой чтения, запрет запуска Handler при этих отказах и роль
исходной версии в защите более свежих данных от устаревшего результата.

Область будущего выполнения — новый `test_orchestrator_load.py`, необходимые
дополнения существующих recording fakes и обновление журнала/индекса.
Зафиксированы typed отказы, unexpected/invalid load, реальные JSON-события,
положительный snapshot-контроль и наблюдаемый аргумент original expected
на save без повторного load и изменения frozen state.

Границы готовности разделены: отказы и их события — после 4.2; передача
snapshot.state и возврат non-success — после 5.2; исходная версия на save —
после 6.4. Отмена незавершённого load остаётся 5.3–5.4. Подготовка промта
не закрывает AC, 2.R2, K3 или вопрос extra RunContext.

Карточка **не выполнялась**: тестовый файл не создавался, production и
существующие тесты не менялись. Pytest не запускался. Последние фактические
результаты остаются в §1.3.18. Обновлены только этот журнал, README серии
и новый промт. Следующий шаг — отдельное выполнение 4.1, затем 4.2.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0: 3 Markdown-файла,
116 локальных ссылок, парные code fences, тестовый файл не создан.
SHA-256 подтвердил сохранность 427 файлов вне области подготовки, Git index
и текста плана вне §1.3. Коммитов, веток, push и PR не создавалось.

#### 1.3.20. Выполнение промта 4.1 — 2026-09-17

**Основание:** явное поручение «Выполни промт 4.1».
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `a2dbc5fc441f0d8b1ba93966cd06faf014181c42`.
Создан [test_orchestrator_load.py](../../tests/application/test_orchestrator_load.py):
6 тестовых функций, 11 случаев, фактически собранных и запущенных pytest.
Сохранённый промт 4.1 и общие `orchestrator_fakes.py` не изменены.

Тесты используют настоящий execute, имеющиеся RecordingContext/RecordingHandler
и общие telemetry/calculation fixtures. Специальные варианты load с исключением,
невалидным outcome и Handler с заменой доступного snapshot локальны новому файлу.
Ни CAS, ни расчётный движок не имитируются внутри координатора.

Для original expected готовится валидный BuildNatalSuccess. Handler заменяет
ссылку fake-контекста на snapshot версии N+2, не меняя исходный frozen state.
Проверяется наблюдаемый аргумент N на единственном save и identity delta;
fake возвращает Superseded с более свежим несовместимым состоянием.
Это будущая проверка передачи версии, не свидетельство реального CAS.

Lifecycle-проверки читают реальные JSON-сообщения и текущие caplog.records,
разделяют техническую exception-запись и единственный terminal. Проверяются
точные поля, уровни, порядок, исходный run_id, допустимые длительности и
согласованность terminal с возвращённой моделью. Тексты отказов заданы
независимо от production-политики. Положительные контроли предназначены
для проверки отсутствия Handler/save при отказах, но сами ещё не прошли.

Фактический окончательный прогон:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -q
# 11 failed in 0.49s; exit code 1
git diff --check
# exit code 0
```

Все 11 случаев завершились одним и тем же `NotImplementedError` в
`src/exact_orb/application/orchestrator.py:80`, до вызова load. Импорт,
fixtures и подготовка данных до execute не дали ошибок. Assertions результата,
вызовов зависимостей и событий после execute **не исполнились**. Их
чувствительность и соответствующие AC пока не подтверждены.

Ниже указаны имена node IDs внутри `tests/application/test_orchestrator_load.py`:

| Требование | Тест и фактические cases | Результат / оставшаяся зависимость |
|---|---|---|
| FR-06/26; части AC-5/6/19/20/26/27/29/30 | `test_absent_load_returns_reason_without_handler_or_save[expired]`, `[not_found]` | 2 failed до load; после 4.2 |
| FR-06/26; части AC-5/6/19/26/27/29/30 | `test_read_failed_preserves_code_without_handler_or_retry[SQLITE_BUSY]`, `[SYNTHETIC_READ_FAILURE]` | 2 failed до load; после 4.2 |
| FR-25/26; части AC-19/21/26/27/29/30 | `test_unexpected_load_exception_is_logged_and_normalized` | 1 failed до load; после 4.2 |
| FR-25/26, §7–12; части AC-19/21/26/27/29/30 | `test_unexpected_invalid_outcome_from_load_is_internal_failure[none]`, `[foreign_outcome]` | 2 failed до load; после 4.2 |
| FR-06–08/26; части AC-5/7/26/27/29/30 | `test_snapshot_reaches_handler_with_loaded_version[0]`, `[7]` | 2 failed до load; завершение после 5.2 |
| FR-07/11/13/16/26; части AC-5/7/19/26/27/29/30 | `test_save_uses_original_version_when_available_snapshot_changes[0]`, `[7]` | 2 failed до load; завершение после 6.4 |

Имена первых семи случаев соответствуют выборке 4.2
`-k "absent or read_failed or unexpected"`; она отдельно не запускалась.
Общий routing-файл не запускался: shared fakes не менялись. R/F не запускались,
поскольку целевой набор не прошёл, согласно §4.2 плана и промту 4.1.
Прежние общие результаты не пересчитываются по числу новых тестов.

Production, существующие тесты, требования, ADR, диаграммы и исторические
промты сохранены. Отмена load остаётся 5.3–5.4, глубокая неизменяемость — 2.R2;
K3 и политика extra RunContext этим этапом не решены. Следующий шаг — 4.2;
реализация следующих карточек, ветки, коммиты, push/PR и сетевые smoke
в рамках 4.1 не выполнялись.

Структурная проверка через `.\.venv\Scripts\python.exe -B -` прошла:
AST нового файла, docstrings всех 6 тестовых функций, отсутствие лишних
пробелов в новом файле, 3 Markdown-документа, 117 локальных ссылок и парные
code fences. SHA-256 подтвердил сохранность 428 файлов вне allowlist,
общих fakes, Git index, HEAD и текста плана вне §1.3. Изменения выполнения
ограничены новым тестовым файлом, журналом и README серии.

#### 1.3.21. Подготовка промта 4.2 — 2026-09-17

По запросу «Напиши промт 4.2» сохранён
[промт 4.2 — загрузка сессии и понятные отказы](../../prompts/2026-09-16/04-session-load/04.2-orchestrator-session-load-and-failures.md).
Вводная часть для менеджеров объясняет различие истёкшей/отсутствующей сессии,
технического отказа чтения и непредвиденной ошибки, а также назначение
исходной версии для защиты более свежих данных при будущем сохранении.

Промт сверён с карточкой плана, текущими R3.2/ADR-0006, session API,
диаграммами 000/008/010, реализацией и тестами 4.1. Область будущего выполнения:
`application/orchestrator.py`, журнал §1.3 и README; тесты и shared fakes
сохраняются. Зафиксированы единственный load после routing, typed отказы,
unexpected/invalid outcome, политика сообщений, монотонные длительности,
реальные JSON-события и terminal из возвращаемого ApplicationResult.

Успешный snapshot сохраняется с исходной версией локально. Существующий
NotImplementedError переносится на ещё не готовое продолжение после load
и остаётся вне обработки исключений чтения. Handler/commit не реализуются,
фиктивный результат или terminal для незавершённой ветки не создаётся.
CancelledError не превращается в failure; полный cancelled lifecycle
остаётся 5.3–5.4. K3, 2.R2 и extra RunContext не решаются этой карточкой.

Ожидаемая ранняя приёмка в нынешнем составе — семь случаев отказов load;
четыре положительных случая 4.1 и семь routing-случаев остаются зависимыми
от следующих этапов. Это ожидание, а не результат нового прогона.
**Промт не выполнялся:** production, тесты и fixtures не менялись, pytest
не запускался. Последние результаты 4.1 сохранены в §1.3.20.
Обновлены только новый промт, README и этот журнал; следующий шаг —
отдельное выполнение 4.2. Коммитов, веток, push и PR не создавалось.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0: 3 Markdown-файла,
123 локальные ссылки, парные code fences и whitespace нового промта.
SHA-256 подтвердил сохранность 430 файлов вне области подготовки,
Git index, HEAD и текста плана вне §1.3.

#### 1.3.22. Выполнение промта 4.2 — 2026-09-18

**Основание:** явное поручение «реализуй промт» после подготовки 4.2.
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `a2dbc5fc441f0d8b1ba93966cd06faf014181c42`.
Реализация ограничена `application/orchestrator.py`; тесты 4.1, shared fakes,
модели, политика отказов и функции журналирования не менялись.

После точного выбора Handler координатор один раз вызывает `context.load` с
исходным `session_id` и измеряет длительность монотонными часами. Typed
`SessionAbsent` возвращает исходную причину и соответствующий код; отказ чтения
сохраняет `error_code`, не объявляя сессию потерянной. Исключение загрузки и
неверный тип outcome дают общий `InternalFailure`, отдельную техническую запись
с traceback и безопасное пользовательское сообщение. Для каждого завершённого
load пишется один stage event; для отказа после него пишется terminal из того же
`ApplicationResult`. Handler и save при отказе не вызываются.

При `SessionSnapshot` локально сохраняются исходный объект и
`original_expected_state_version`, включая версию 0; событие `load/loaded`
содержит версию. Затем сохраняется явный `NotImplementedError` перед Handler
без фиктивного ответа или terminal. Обработка `Exception` охватывает только
вызов load; отмена незавершённого load не нормализуется в application failure.

Фактические проверки из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -k "absent or read_failed or unexpected" -q
# 7 passed, 4 deselected in 0.44s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
# 6 passed, 7 deselected in 0.44s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# 1399 passed, 11 failed in 28.07s; exit code 1
```

| Требование | Тестовые node IDs | Подтверждение / зависимость |
|---|---|---|
| FR-06/26, части AC-5/6/19/20/26/27/29/30 | `test_orchestrator_load.py::test_absent_load_returns_reason_without_handler_or_save[expired]`, `test_orchestrator_load.py::test_absent_load_returns_reason_without_handler_or_save[not_found]` | 2 passed: причина, код, отсутствие Handler/save и связка started → stage → terminal |
| FR-06/26, части AC-5/6/19/26/27/29/30 | `test_orchestrator_load.py::test_read_failed_preserves_code_without_handler_or_retry[SQLITE_BUSY]`, `test_orchestrator_load.py::test_read_failed_preserves_code_without_handler_or_retry[SYNTHETIC_READ_FAILURE]` | 2 passed: исходный detail_code, отсутствие потери сессии и повтора load |
| FR-25/26, части AC-19/21/26/27/29/30 | `test_orchestrator_load.py::test_unexpected_load_exception_is_logged_and_normalized` | 1 passed: traceback технической записи, фиксированный внешний текст и lifecycle |
| FR-25/26, части AC-19/21/26/27/29/30 | `test_orchestrator_load.py::test_unexpected_invalid_outcome_from_load_is_internal_failure[none]`, `test_orchestrator_load.py::test_unexpected_invalid_outcome_from_load_is_internal_failure[foreign_outcome]` | 2 passed: нарушение контракта отделено от typed отказа |
| FR-03/04, часть AC-3 | `test_orchestrator_routing.py` с выборкой `requires_run or unknown_command or subclass or registry` | 6 passed: ранний routing сохранён; семь положительных случаев требуют Handler/commit |
| FR-06–08/26, части AC-5/7/26/27/29/30 | `test_orchestrator_load.py::test_snapshot_reaches_handler_with_loaded_version[0]`, `test_orchestrator_load.py::test_snapshot_reaches_handler_with_loaded_version[7]` | 2 failed на явной границе после `load/loaded`; передача state ожидает 5.2 |
| FR-07/11/13/16/26, части AC-5/7/19/26/27/29/30 | `test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes[0]`, `test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes[7]` | 2 failed на той же границе; реальный аргумент save ожидает 6.4 |

Остальные семь failures R —
`test_orchestrator_routing.py::test_exact_type_reaches_handler`,
`test_orchestrator_routing.py::test_explicit_child_registration_selects_own_handler[base]`,
`test_orchestrator_routing.py::test_explicit_child_registration_selects_own_handler[child]`,
`test_orchestrator_routing.py::test_external_mapping_removal_keeps_original_handler`,
`test_orchestrator_routing.py::test_external_mapping_replacement_keeps_original_handler`,
`test_orchestrator_routing.py::test_new_instance_accepts_added_type`,
`test_orchestrator_routing.py::test_known_command_completes_with_commit`.
Все 11 случаев остановились на `NotImplementedError` после единственного load и
`load/loaded`, с корректной версией 0 или 7 в двух snapshot-контролях; других
failures в R нет. Это незакрытые сценарии, а не успешная приёмка сквозного AC.
F не запускался из-за непройденного R согласно §4.2 плана. Отмена остаётся
5.3–5.4; K3, 2.R2 и политика extra RunContext не решались. Следующая основная
карточка — 5.1. Коммит, ветка, push и PR не создавались.

`git diff --check` завершился с exit code 0. Структурная проверка двух
изменённых Markdown-файлов подтвердила 111 локальных ссылок и парность code
fences. SHA-256 до/после подтвердил неизменность 426 файлов вне allowlist,
Git index, HEAD и текста плана вне §1.3. Полный F, сетевые и платные smoke
не выполнялись.

#### 1.3.23. Подготовка промта 5.1 — 2026-09-18

По запросу «пиши промт 5.1» сохранён
[промт 5.1 — тесты вызова Handler и его штатных исходов](../../prompts/2026-09-16/05-handler-execution/05.1-orchestrator-handler-outcomes-tests.md).
Вводная часть для менеджеров объясняет, зачем Handler должен получать исходные
command/state/run, почему потребность исправить ввод отличается от технической
недоступности и ошибки расчёта, и почему ни один из этих трёх исходов не
разрешает сохранять новое состояние сессии.

Промт сверён с R3.2/ADR-0006, карточками 5.1–5.4/6.4, диаграммами
004/005/010, действующими моделями, policy, recording fakes и тестами 4.1.
При будущем выполнении разрешены новый `test_orchestrator_handler.py`, лишь
необходимые дополнения общих fakes, этот журнал и README серии. Production,
старые тесты, требования, ADR, диаграммы и исторические промты не входят в
allowlist. Положительный контроль сохранения опирается прежде всего на уже
имеющиеся routing/load-тесты, чтобы не дублировать их сценарии.

**K3 остаётся открытым:** Handler принимает `InputRequired(issues=())`, а
`ApplicationInputRequired` требует непустые `issues`. Промт разрешает
подготовить независимые тесты с непустыми issues, но запрещает молча выбрать
реакцию на пустой исход; без решения владельца контракта 5.1 может быть только
частично выполнена, AC-8 целиком не закрывается. Это не изменение принятого
плана или публичного контракта.

В тестовом задании разделены identity и порядок `load → handle`, три
non-success ветки и точные поля ответа, fallback/WARN неизвестного calculation
code, события завершённого Handler и границы будущего success/commit. Отмена
load и Handler остаётся 5.3–5.4; в будущей карточке 5.4 должна быть явно
проверена обработка отмены именно вокруг load.

**Карточка не выполнялась:** тестовый файл не создавался, production и
существующие тесты не менялись, pytest не запускался. Результаты 4.2 остаются
в §1.3.22; новый промт не делает их зелёными задним числом. Следующий шаг —
отдельное выполнение 5.1 с явным учётом K3. Коммит, ветка, push и PR не
создавались.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
трёх Markdown-файлов подтвердила 121 локальную ссылку и парные code fences.
SHA-256 до/после подтвердил неизменность 428 файлов вне allowlist, Git index,
HEAD и текста плана вне §1.3. Новый тестовый файл ещё отсутствует.

#### 1.3.24. Выполнение тестовой части промта 5.1 — 2026-09-18

**Основание:** явное поручение «сохрани и выполни промт» после подготовки 5.1.
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `24aa5e9a32d1a299399d9fdbdef373727ece7651`.
Создан только `tests/application/test_orchestrator_handler.py` из тестовой
области промта. Общие recording fakes оказались достаточны и не менялись;
production, требования, ADR, диаграммы и сохранённый промт 5.1 не изменялись.

Четыре тестовые функции дают десять случаев: `InputRequired` с двумя
упорядоченными issues и версиями 0/7, `ResolutionUnavailable` с обоими
значениями retryable, пять известных calculation-кодов и один неизвестный.
После реализации 5.2 каждый случай должен проверить исходные объекты
command/state/run по identity, единственную последовательность load → handle
без save, точную модель результата и реальный JSON-журнал started → load →
handler → terminal. Для неизвестного кода отдельно проверяется диагностический
WARN, для известных — его отсутствие. Тексты и retryable заданы независимо
от вызова policy в тесте.

Фактические проверки из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -q --tb=no
# 10 failed in 0.38s; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py --collect-only -q
# 10 tests collected in 0.26s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -k "absent or read_failed or unexpected" -q
# 7 passed, 4 deselected in 0.28s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
# 6 passed, 7 deselected in 0.26s; exit code 0
```

Первый запуск с `--tb=line` до сокращения имён параметров также дал 10 failed,
все на `NotImplementedError` в `orchestrator.py:125` после `load/loaded`.
Повторный запуск после изменения только test IDs подтвердил те же десять
отложенных случаев. Ошибок импорта, fixtures и тестовых данных не было.

| Требование | Node IDs `test_orchestrator_handler.py::…` | Подтверждение / зависимость |
|---|---|---|
| FR-02/05–08/26, AC-2/5/7/8/26/29/30/33 | `test_input_required_preserves_handler_identity_issues_and_events[0]`, `[7]` | 2 failed после load; identity, порядок issues, no-save и terminal пока не проверены; 5.2. Пустые issues — K3 |
| FR-10/25–26, AC-8/21/26/27/29/30/33 | `test_resolution_failure_keeps_handler_retryability_without_save[retryable]`, `[non_retryable]` | 2 failed после load; обе реакции Handler → ApplicationResult ждут 5.2 |
| FR-10/25–26, AC-8/21/25–27/29/30/33 | `test_known_calculation_failure_uses_exact_policy_without_save[EPHEMERIS_UNAVAILABLE]`, `[HOUSES_DEGENERATE]`, `[SPEC_INVALID]`, `[GEOGRAPHY_INVALID]`, `[ENGINE_UNEXPECTED]` | 5 failed после load; известные тексты, retryable и отсутствие диагностического WARN ждут 5.2 |
| FR-10/25–26, AC-8/21/25–27/29/30/33 | `test_unknown_calculation_code_uses_fallback_and_diagnostic_warn` | 1 failed после load; fallback и отдельный WARN ждут 5.2 |
| AC-8/10, AC-5/7 | `test_orchestrator_routing.py::test_known_command_completes_with_commit`, `test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes[0]`, `[7]` | Существующие положительные контроли save не дублировались; завершатся в 6.4 |

Таким образом, 5.1 **частично выполнена как подготовка тестов**, но ни одно
новое утверждение после `execute` пока не подтверждено. K3 остаётся открытым:
допустимый `InputRequired(issues=())` нельзя поместить в действующий внешний
`ApplicationInputRequired`; реакция на него не назначалась, AC-8 полностью не
закрыт. Основная следующая карточка — 5.2 после решения K3 для этой ветки.
Отмена load/Handler остаётся 5.3–5.4. R и F не запускались, поскольку целевой
набор ожидаемо красный до реализации 5.2 (§4.2); сетевые и платные smoke не
выполнялись. Коммит, ветка, push и PR не создавались.

`git diff --check` завершился с exit code 0. Структурная проверка плана,
README и сохранённого промта подтвердила 121 локальную ссылку без потерь и
парные code fences; новый Python-файл собрался в pytest без ошибок импорта.
SHA-256 до/после подтвердил сохранность 428 файлов вне разрешённой области,
общих fakes, Git index, HEAD и текста плана вне §1.3.

#### 1.3.25. Подготовка промта 5.3 — 2026-09-18

По запросу «напиши промт 5.3» сохранён
[промт 5.3 — тесты нарушений Handler и отмены до сохранения](../../prompts/2026-09-16/05-handler-execution/05.3-orchestrator-handler-failures-and-early-cancellation-tests.md).
Его вводная часть объясняет для менеджеров, почему неверный ответ или
исключение Handler нельзя показывать как ошибку пользовательского ввода и
почему отменённый load обязан оставить один terminal, но не ложный finished
stage. Подготовлены отдельные сценарии `None`/чужого типа, настоящего
исключения и управляемой отмены на load/Handler через `asyncio.Event`.

Промт сверён с R3.2 UC-12/14, FR-25/26, §11.5, ADR-0006, диаграммой 010,
карточками 5.1–5.4, действующими моделями, logging helpers и тестами. При
будущем выполнении allowlist ограничен тестами `test_orchestrator_handler.py`,
при отдельном доказанном пробеле — `test_orchestrator_logging.py`, журналом
§1.3 и README. Production и общие fakes не разрешены этой тестовой карточкой.
Тесты будут проверять результат, фактическое отсутствие save, отдельную
диагностику, точный lifecycle, один cancelled terminal и проброс
`CancelledError`; отмена после начала commit остаётся группе 6.

**Зависимость пока не выполнена:** в текущем checkout 5.2 не реализована;
после load остаётся `NotImplementedError`. Сохранение задания 5.3 не означает
его исполнения и не закрывает AC-9/17/21/26/29/30/32/33. K3 остаётся
открытым, но не изменяет смысл независимых сценариев 5.3. Следующий основной
шаг в последовательности плана — 5.2, затем тестовая 5.3 и реализация 5.4.
Тесты и production при подготовке не менялись, pytest не запускался; коммит,
ветка, push и PR не создавались.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
плана, README и нового промта подтвердила 120 локальных ссылок без потерь,
парные code fences и отсутствие trailing whitespace в новом промте.
SHA-256 подтвердил сохранность 428 файлов вне области подготовки, общих fakes,
Git index, HEAD и текста плана вне §1.3.

#### 1.3.26. Частичное выполнение тестовой части промта 5.3 — 2026-09-18

**Основание:** явное поручение «Сохрани и реализуй промт 5.3» после его
подготовки. **Ветка:** `feat/application-orchestrator`.
**HEAD:** `24aa5e9a32d1a299399d9fdbdef373727ece7651`.
Сохранённый промт 5.3 не редактировался. В пределах его тестового allowlist
дополнен `tests/application/test_orchestrator_handler.py`: два случая неверного
outcome (`None`/чужой typed объект), настоящее исключение с техническим
маркером и два управляемых `asyncio.Event` сценария отмены во время load и
Handler. Тесты используют настоящий `execute`, recording fakes и реальные
JSON LogRecord; `sleep`, `skip` и `xfail` не применяются. Отдельный
`test_orchestrator_logging.py` уже покрывает helpers и не менялся; production,
shared fakes и остальные тесты не менялись.

Фактические проверки из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py -q --tb=no
# 15 failed, 176 passed in 0.61s; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "invalid_handler or handler_exception or cancel_during" -q --tb=line
# 5 failed, 10 deselected in 0.33s; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py --collect-only -q
# 15 tests collected in 0.26s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -k "absent or read_failed or unexpected" -q
# 7 passed, 4 deselected in 0.28s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
# 6 passed, 7 deselected in 0.26s; exit code 0
```

| Требование | Node IDs `test_orchestrator_handler.py::…` | Подтверждение / зависимость |
|---|---|---|
| UC-12, AC-9/21/26/29/30/32/33 | `test_invalid_handler_outcome_is_internal_failure_without_save[none-version-zero]`, `[foreign-type]` | 2 failed на `NotImplementedError` после load; Handler ещё не вызван, преобразование и отсутствие save ждут 5.2/5.4 |
| UC-12, FR-25, AC-21/26/29/30/32/33 | `test_handler_exception_has_real_traceback_and_safe_result` | 1 failed на той же границе; реальный traceback, безопасный ответ и события ждут 5.2/5.4 |
| UC-14, AC-17/26/29/30/32/33 | `test_cancel_during_load_writes_one_cancelled_terminal` | Event подтвердил вход в load; `CancelledError` дошёл вызывающему, Handler/save не вызваны, но после `started` нет terminal. Один конкретный дефект для 5.4 воспроизведён |
| UC-14, AC-17/26/29/30/32/33 | `test_cancel_during_handler_writes_one_cancelled_terminal` | 1 failed на `NotImplementedError` до входа Handler; проверка отмены ждёт 5.2/5.4 |
| FR-26, модели/формат событий | `test_orchestrator_logging.py` | 176 passed для функций записи, не подтверждают вызов cancelled terminal из `execute` |

Прежние десять случаев 5.1 также failed на том же `NotImplementedError`, без
новой регрессии в этих тестах. Новые тесты **написаны и собраны**, но 5.3 не
может считаться выполненной или принятой: 5.2 отсутствует, четыре новых
сценария не достигли своих assertions, а отменённый load выявил отсутствие
terminal. Поэтому AC-9/17/21/26/29/30/32/33 целиком не закрыты; AC-17
дополнительно требует Event-контроля защищённого commit в группе 6. K3 о пустых
issues остаётся открытым. Следующий основной шаг по последовательности — 5.2,
затем 5.4 после проверки 5.3. R и F не запускались при красном целевом наборе
согласно §4.2; сетевые и платные smoke не выполнялись. Коммит, ветка, push и
PR не создавались.

`git diff --check` завершился с exit code 0. Структурная проверка плана,
README и сохранённого промта подтвердила 121 локальную ссылку без потерь и
парные code fences; в изменённом тестовом файле нет trailing whitespace.
SHA-256 до/после подтвердил сохранность 428 файлов вне области выполнения,
общих fakes, Git index, HEAD и текста плана вне §1.3.

#### 1.3.27. Подготовка промта 5.4 — 2026-09-18

По запросу «Пиши промт 5.4» сохранён
[промт 5.4 — ошибки Handler и отмена до commit](../../prompts/2026-09-16/05-handler-execution/05.4-orchestrator-handler-errors-and-precommit-cancellation.md).
Его вводная часть объясняет менеджерам, зачем превращать нарушение контракта
Handler или его исключение в безопасный внутренний отказ и почему отмена во
время load/Handler обязана оставить один terminal event до проброса отмены.

Промт согласован с R3.2 UC-12/14, FR-25/26 и §11.5, ADR-0006, диаграммой 010,
карточками 5.2–5.4 и уже написанными тестами 5.3. Для будущей реализации
разрешён только `src/exact_orb/application/orchestrator.py`, а для записи
фактического результата — §1.3 плана и README серии. Неверный outcome и
исключение Handler требуют `ApplicationInternalFailure` с исходной loaded
version, отдельной диагностики, законченного handler stage и result-terminal;
отмена незавершённого load/Handler требует cancelled terminal без ложного
stage-finished, результата и save. Защищённый commit остаётся группе 6.

**Зависимость открыта:** 5.2 отсутствует в текущем checkout. Промт допускает
отдельную реализацию и проверку отмены load до 5.2, но не позволяет считать
5.4 принятой до выполнения Handler-веток и тестов 5.3. K3 о пустом `issues`
остаётся открытым. При подготовке production и тесты не изменялись, pytest
не запускался; AC не закрыты, коммит, ветка, push и PR не создавались.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
трёх Markdown-файлов — exit code 0, 125 локальных ссылок разрешаются, code
fences парные, trailing whitespace нет. Pytest при подготовке не запускался.

#### 1.3.28. Частичное выполнение промта 5.4 — 2026-09-18

**Основание:** поручение «выполни промт» после сохранения 5.4.
**Ветка:** `feat/application-orchestrator`.
**HEAD:** `24aa5e9a32d1a299399d9fdbdef373727ece7651`.
На входе 5.2 отсутствовала: после успешного load `execute` по-прежнему
останавливался на `NotImplementedError`. Согласно сохранённому промту
выполнена только независимая часть 5.4 — отмена незавершённого load.

В `src/exact_orb/application/orchestrator.py` добавлен отдельный перехват
`asyncio.CancelledError` непосредственно вокруг `await context.load`.
Перед повторным пробросом исходной отмены он вызывает существующий
`log_operation_cancelled` с переданным `run_id`, `cancelled_stage="load"` и
`None` для длительностей незавершённого load и не начатого Handler. Событие
завершения load, `ApplicationResult`, Handler и save в этой ветке не создаются.
Обработка typed отказов load и настоящего `Exception` сохранена; тесты,
logging helper, модели, требования, ADR и диаграммы не менялись.

Фактические проверки из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py::test_cancel_during_load_writes_one_cancelled_terminal -q --tb=short
# до правки: 1 failed; после started отсутствовал terminal; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py::test_cancel_during_load_writes_one_cancelled_terminal -q
# после правки: 1 passed; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -k "absent or read_failed or unexpected" -q
# 7 passed, 4 deselected; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
# 6 passed, 7 deselected; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
# 176 passed; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "invalid_handler or handler_exception or cancel_during" -q --tb=line
# 4 failed, 1 passed, 10 deselected; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py -q --tb=no
# 14 failed, 177 passed; exit code 1
```

| Требование | Node ID `test_orchestrator_handler.py::…` | Фактическая граница |
|---|---|---|
| UC-14, FR-26, AC-17/26/29/30/32/33 | `test_cancel_during_load_writes_one_cancelled_terminal` | Passed: один started и один cancelled terminal до наблюдения `CancelledError`; нет stage-finished и save. Доказана только отмена load, не полный AC |
| UC-12, FR-25/26, AC-9/21/26/29/30/32/33 | `test_invalid_handler_outcome_is_internal_failure_without_save[none-version-zero]`, `[foreign-type]`; `test_handler_exception_has_real_traceback_and_safe_result` | 3 failed на `NotImplementedError` после load; Handler не вызывался, нормализация ждёт 5.2/оставшуюся часть 5.4 |
| UC-14, FR-26, AC-17/26/29/30/32/33 | `test_cancel_during_handler_writes_one_cancelled_terminal` | Failed на том же `NotImplementedError` до входа Handler; ждёт 5.2/оставшуюся часть 5.4 |
| Штатные исходы Handler, AC-8/21/25–30/33 | 10 прежних случаев 5.1 | Failed после load на `NotImplementedError`; ждут 5.2, K3 остаётся открытым |
| Формат функций lifecycle logging | `test_orchestrator_logging.py` | 176 passed; не доказывают вызов Handler или terminal из его веток |

Итог 5.4 — **частично выполнена**, полная приёмка не пройдена. После
отдельного выполнения 5.2 нужно вернуться к неверному результату, исключению
и отмене Handler по сохранённому промту 5.4. R и F при красном целевом
Handler-наборе не запускались по §4.2. Сетевые и платные smoke не выполнялись;
коммит, ветка, push и PR не создавались.

`git diff --check` — exit code 0. Структурная проверка плана, README и
сохранённого промта — exit code 0: 125 локальных ссылок разрешаются, code
fences парные, trailing whitespace нет. Сравнение diff подтверждает, что
production-правка ограничена перехватом отмены load, а план изменён только
в §1.3; посторонние файлы рабочего дерева оставлены без изменений.

#### 1.3.29. Реализация 5.2 и завершение ранних веток 5.4 — 2026-09-18

**Основание:** поручение «реализуй 5.2 промт же был» после частичного
выполнения 5.4. Карточка 5.2 действительно есть в §5 этого плана;
отдельный файл 05.2 в каталоге промтов не создавался. Предыдущее утверждение
об отсутствии задания было ошибочным: отсутствовал только отдельный файл и
реализация. **Ветка:** `feat/application-orchestrator`.
**HEAD:** `24aa5e9a32d1a299399d9fdbdef373727ece7651`.

В `src/exact_orb/application/orchestrator.py` после успешного load Handler
получает исходные `command`, `snapshot.state` и `run` по identity. Его
`InputRequired` с непустыми issues, `ResolutionUnavailable` и
`CalculationFailed` преобразуются в проверяемые `ApplicationResult` через
`describe_failure`; перед возвратом пишутся завершение стадии Handler и один
terminal из созданной модели. Save на этих путях не вызывается. Неизвестный
calculation code сохраняется как `detail_code`, получает fallback policy и
отдельный WARN; множество известных кодов берётся из действующих typed
calculation errors. Успешный `BuildNatalSuccess` создаёт handler/success event
и останавливается на явной границе commit без фиктивного save: commit — 6.4.

После появления вызова Handler закончены ранее разрешённые ветки 5.4:
неверный outcome и настоящее исключение дают безопасный
`ApplicationInternalFailure` с загруженной версией, отдельную техническую
диагностику, handler stage и result-terminal; отмена Handler даёт один
cancelled terminal перед повторным пробросом `CancelledError`, без ложного
stage-finished и save. Искусственное исключение для невалидного outcome не
создаётся. Тесты, policy, модели, logging helpers, требования, ADR и диаграммы
не менялись: код исполняет ранее принятый контракт, не пересматривая его.

**K3 оставлен открытым по явному выбору пользователя в этом выполнении.**
Handler contract разрешает `InputRequired(issues=())`, внешняя модель
отклоняет его. Код не добавляет фиктивный issue, не ослабляет модель и не
выбирает новый public outcome; этот случай не принят, полный AC-8 не закрыт.
До решения K3 такой outcome нельзя считать поддержанным завершённым путём.

Фактические проверки из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "identity or non_success or unknown_calculation" -q
# 3 passed, 12 deselected; exit code 0; точная выборка карточки 5.2
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "input_required_preserves or resolution_failure or known_calculation or unknown_calculation" -q --tb=short
# 10 passed, 5 deselected; exit code 0; все случаи 5.1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "invalid_handler or handler_exception or cancel_during" -q --tb=short
# 5 passed, 10 deselected; exit code 0; все случаи 5.3
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py -q
# 191 passed; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -q --tb=no
# 2 failed, 9 passed; exit code 1; оба failure — save после success, группа 6
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -q --tb=no
# 1 failed, 12 passed; exit code 1; failure — commit после success, группа 6
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q --tb=no
# R: 3 failed, 1422 passed; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes tests/application/test_orchestrator_routing.py::test_known_command_completes_with_commit -q --tb=line
# те же 3 failed на NotImplementedError после handler/success; exit code 1
```

| Требование | Node IDs | Свидетельство и остаток |
|---|---|---|
| AC-2/5/7/8/26/29/30/33 | `test_orchestrator_handler.py::test_input_required_preserves_handler_identity_issues_and_events[0]`, `[7]` | 2 passed: identity, loaded version, issues, no-save и четыре события; пустые issues — K3 |
| AC-8/21/25–27/29/30/33 | `test_resolution_failure_keeps_handler_retryability_without_save[retryable]`, `[non_retryable]`; `test_known_calculation_failure_uses_exact_policy_without_save[EPHEMERIS_UNAVAILABLE]`, `[HOUSES_DEGENERATE]`, `[SPEC_INVALID]`, `[GEOGRAPHY_INVALID]`, `[ENGINE_UNEXPECTED]`; `test_unknown_calculation_code_uses_fallback_and_diagnostic_warn` | 8 passed: точные поля результата, тексты/retryability, fallback/WARN, отсутствие save |
| UC-12/14, FR-25/26, AC-9/17/21/26/29/30/32/33 | `test_invalid_handler_outcome_is_internal_failure_without_save[none-version-zero]`, `[foreign-type]`; `test_handler_exception_has_real_traceback_and_safe_result`; `test_cancel_during_load_writes_one_cancelled_terminal`; `test_cancel_during_handler_writes_one_cancelled_terminal` | 5 passed: безопасный result или отмена, один terminal, нет save и ложного finished event; commit-cancellation остаётся группе 6 |
| AC-7/10/19/26/27/29/30 | `test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes[0]`, `[7]`; `test_orchestrator_routing.py::test_known_command_completes_with_commit` | 3 failed после handler/success на явном `NotImplementedError`; save/commit и terminal ждут 6.4 |

R содержит только три заранее отложенных success/commit сценария; неожиданных
падений нет. F не запускался при красном R согласно §4.2. Сетевые и платные
smoke не выполнялись; коммит, ветка, push и PR не создавались. Следующий
основной этап — группа 6, при открытом K3 и неполной сквозной приёмке AC.

`git diff --check` — exit code 0. Структурная проверка плана, README и
сохранённого промта 5.4 — exit code 0: 124 локальные ссылки разрешаются,
code fences парные, trailing whitespace нет. Git index пуст по staged diff;
посторонние файлы рабочего дерева сохранены.

#### 1.3.30. Подготовка промта 6.1 — 2026-09-18

По запросу написать промт 6.1 с понятным объяснением для менеджеров сохранён
[промт 6.1 — тесты одной защищённой попытки сохранения](../../prompts/2026-09-16/06-protected-commit/06.1-orchestrator-protected-commit-tests.md).
Вводная объясняет, почему готовый расчёт ещё не означает сохранение и почему
после начала записи отмена доставки ответа должна ждать исхода записи и
итогового события. Результат карточки — тесты, реализация остаётся 6.2.

Промт сверен с R3.2 UC-01/15, FR-10–13/17/20/26, §11.4–11.5/12,
ADR-0006, session-контрактом, диаграммами 009/010, текущим Orchestrator и
существующими routing/load/Handler/logging-тестами. На момент подготовки
ветка — `feat/application-orchestrator`, HEAD —
`f3bbf4961f9a2f3831bb3d018878d42f91534884`. В коде подтверждены ранние
ветки 5.2/5.4 и `NotImplementedError` перед commit; прежние числа прохождения
из §1.3.29 не являются новым запуском.

Для будущего исполнения разрешены два новых файла commit/cancellation-тестов,
минимальное расширение `orchestrator_fakes.py`, §1.3 плана и README серии.
Проверки используют настоящий execute, typed `Committed` и Event внутри
save. Требуется наблюдать незавершённый caller после обработки отмены,
затем commit-attempt и result-terminal до доставки `CancelledError`.
События разбираются как JSON; существующие positive-контроли не копируются.
Остальные outcomes, retry и повторная отмена остаются последующим карточкам.

K3 и 2.R2 сохранены открытыми; независимый success/commit-срез их не решает.
Подготовка промта не закрывает AC. Production и тесты не изменялись,
pytest не запускался; ветка, коммит, push и PR не создавались.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0: у трёх Markdown-файлов
разрешаются 126 локальных ссылок, code fences парные, trailing whitespace
отсутствует, статус 6.1 согласован. Новый untracked-промт проверен напрямую.
Git index пуст; посторонние файлы сохранены.

#### 1.3.31. Выполнение тестовой карточки 6.1 — 2026-09-18

По поручению выполнить подготовленный промт 6.1 созданы
`tests/application/test_orchestrator_commit.py` и
`tests/application/test_orchestrator_cancellation.py`.
Общий управляемый fake ContextService находится в новом commit-тесте;
`orchestrator_fakes.py` не изменялся. Два параметризованных обычных случая
используют original expected 0/7 и typed `Committed` с версиями 4/19,
которые намеренно не вычисляются как expected+1: это unit-проверка передачи
ответа зависимости, не сценарий реального CAS. Третий случай задаёт одну
отмену после входа в save. Во всех случаях настроены реальные вызовы execute,
валидный `BuildNatalSuccess`, управляемые `asyncio.Event`, реальные JSON
lifecycle-записи и уборка задач.

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
# 3 failed in 0.41s; exit code 1; первый прогон показал NotImplementedError через cleanup
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q --tb=short
# 3 failed in 0.34s; exit code 1; первичное место падения видно напрямую
```

После первого прогона исправлен только helper уборки теста: он больше не
заслоняет первичное исключение повторным ожиданием уже завершённого caller.
Все три финальных node IDs собраны и исполнились:

| Требование | Node ID | Фактический результат и граница |
|---|---|---|
| FR-10/11/13/17/26, AC-7/10/19/26/27/29–32 | `tests/application/test_orchestrator_commit.py::test_one_confirmed_save_waits_and_returns_committed[0-4]` | Failed: `orchestrator.py:237` выбрасывает `NotImplementedError` до входа в save; ожидание и assertions после save ждут 6.2 |
| Те же FR/AC; ненулевая original expected | `tests/application/test_orchestrator_commit.py::test_one_confirmed_save_waits_and_returns_committed[7-19]` | Failed по той же причине; отдельная версия подтверждённого outcome пока не наблюдалась |
| UC-15, FR-20/26, AC-16/17/26/29/31/32 | `tests/application/test_orchestrator_cancellation.py::test_cancel_after_save_entry_waits_for_commit_and_terminal` | Failed по той же причине; отмена внутри уже начатого save пока не исполнялась |

Ошибка не относится к collection, fixture или синхронизации: traceback обоих
файлов проходит настоящий `execute`, достигает успешной Handler-ветки и
останавливается на ранее оставленной границе commit. Наличие тестов и этот
ожидаемый red не закрывают перечисленные AC; downstream assertions ещё не
исполнялись. Ранее отложенные три success/commit случая §1.3.29 остаются
ожидающими 6.4. K3 и 2.R2 не решались. R и F не запускались при красном целевом
наборе; production, требования, ADR и диаграммы не менялись.

Проверки целостности: `git diff --check` — exit code 0; прямой запуск
`.\.venv\Scripts\python.exe -B -` со stdin-проверкой двух новых файлов —
exit code 0: UTF-8, Python syntax, завершающий newline и отсутствие trailing
whitespace. Новые untracked-тесты проверены напрямую, так как обычный git diff
их не показывает. Git index пуст; файлы вне allowlist сохранены. Коммит, ветка,
push и PR не создавались. Следующий отдельный этап — 6.2.

#### 1.3.32. Подготовка промта 6.2 — 2026-09-18

По запросу «пиши следующий промт» сохранён
[промт 6.2 — защищённое сохранение с первой попытки](../../prompts/2026-09-16/06-protected-commit/06.2-orchestrator-protected-first-commit.md).
Вводная для менеджеров объясняет, почему завершённый расчёт ещё не означает
сохранение и почему после отмены запроса уже начатую запись нужно дождаться
и зафиксировать её итог до передачи отмены.

Карточка опирается на три тестовых случая 6.1 и текущий `NotImplementedError`
перед `save`; она разрешает только production-ветку `orchestrator.py` и
фактический журнал/README. Первая попытка использует original expected и ту
же delta, подтверждённая версия приходит из `Committed`; один отменённый
caller ждёт inner task, attempt и result-terminal с `delivery_cancelled=true`.
Иные commit outcomes, retry/deadline и повторная отмена оставлены 6.3–6.4,
7.1–7.2 и 9.1. Промт отдельно требует не считать известные `Superseded`
падения в связанном R завершённой приёмкой, даже если три случая 6.1 пройдут.

На момент подготовки ветка `feat/application-orchestrator`, HEAD
`f3bbf4961f9a2f3831bb3d018878d42f91534884`; статус 6.1 из §1.3.31
исторический, новых запусков pytest для подготовки 6.2 не было. Production,
тесты и сохранённый промт 6.1 не менялись; K3 и 2.R2 открыты. Коммит, ветка,
push и PR не создавались.

Проверки подготовки: `git diff --check` — exit code 0; структурная проверка
через `.\.venv\Scripts\python.exe -B -` — exit code 0: в трёх Markdown-файлах
132 локальные ссылки разрешаются, code fences парные, trailing whitespace
отсутствует, статус 6.2 согласован. Новый untracked-промт проверен напрямую;
Git index пуст, посторонние файлы рабочего дерева сохранены.

#### 1.3.33. Реализация первой защищённой попытки 6.2 — 2026-09-18

По поручению выполнить промт 6.2 в `src/exact_orb/application/orchestrator.py`
заменена заглушка после `handler/success` для одного typed `Committed`.
`execute` создаёт локальную задачу `ContextService.save` с исходными
`session_id`, expected и той же delta, удерживает её через `asyncio.shield`,
а после внешней отмены продолжает ожидание завершения. Повторная отмена
ожидания не отрывает локальную ссылку; отдельная проверка этой гонки остаётся
9.1. Версия успешного ответа берётся из `Committed`, не вычисляется по
expected. После save пишутся attempt=1 и result-terminal, затем результат
возвращается либо пробрасывается наблюдённый `CancelledError`.

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q --tb=short
# baseline до правки: 3 failed in 0.39s; exit code 1; NotImplementedError до save
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
# после правки: 3 passed in 0.29s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q --tb=short
# R: 2 failed, 1426 passed in 13.20s; exit code 1
```

| Требование | Node ID | Фактическое свидетельство / остаток |
|---|---|---|
| FR-10/11/13/17/26, AC-7/10/19/26/27/29–32 | `tests/application/test_orchestrator_commit.py::test_one_confirmed_save_waits_and_returns_committed[0-4]`, `[7-19]` | 2 passed: один save после Handler, original expected 0/7, delta по identity, версия 4/19 из typed `Committed`, результат и пять событий до возврата |
| UC-15, FR-20/26, AC-16/17/26/29/31/32 | `tests/application/test_orchestrator_cancellation.py::test_cancel_after_save_entry_waits_for_commit_and_terminal` | 1 passed: caller остаётся незавершённым после отмены при заблокированном save; запись не отменена, attempt и result-terminal с `delivery_cancelled=true` предшествуют наблюдаемому `CancelledError` |
| Остальные commit outcomes, AC-19 полностью | `tests/application/test_orchestrator_load.py::test_save_uses_original_version_when_available_snapshot_changes[0]`, `[7]` | 2 failed в R после фактически начатого save: явный `NotImplementedError` для `Superseded`; mapping, attempt/terminal этого исхода остаются 6.3–6.4 |

Положительный routing-контроль `test_known_command_completes_with_commit`
прошёл в R. Других failures в связанном наборе нет. Полный F при красном R
не запускался. 6.2 подтверждает только `Committed` и одну внешнюю отмену после
входа в save; остальные typed/internal outcomes, retry/deadline, повторная
отмена и полная приёмка AC-19/29/31/32 остаются последующим карточкам. K3 и
2.R2 открыты. Тесты, shared fakes, Handler, session, модели, logging helpers,
requirements, ADR и диаграммы не менялись; контракт их не пересматривался.

Проверки целостности: `git diff --check` — exit code 0; структурная проверка
плана и README через `.\.venv\Scripts\python.exe -B -` — exit code 0:
122 локальные ссылки разрешаются, code fences парные, trailing whitespace
отсутствует. Git index пуст; посторонние файлы сохранены. Коммит, ветка,
push и PR не создавались. Следующая отдельная карточка — 6.3.

#### 1.3.34. Подготовка промта 6.3 — 2026-09-18

По запросу пользователя сохранён
[промт 6.3](../../prompts/2026-09-16/06-protected-commit/06.3-orchestrator-commit-outcomes-tests.md)
для тестов оставшихся исходов первой попытки `ContextService.save`. Основание:
6.2 подтвердил `Committed` и одну отмену после входа в save, но два связанных
`Superseded`-теста по-прежнему падают на явном `NotImplementedError` (§1.3.33).
Новая карточка разделяет `AlreadyApplied`, `Superseded`, оба reason
`SessionAbsent` на стадии commit, окончательный `StateCommitFailed` и
unexpected Exception. Для каждого исхода требуется проверить полную связку
результата, ровно один фактический save, attempt/terminal до возврата и
отсутствие повторного load/Handler. Существующие тесты `Committed` остаются
положительным контролем. Для отказа записи задан истёкший deadline, чтобы
ожидание одной попытки сохраняло смысл после появления retry в 7.2.

Это **подготовка инструкции**, а не выполнение 6.3: новые тесты и production
не менялись, целевой pytest и R/F в этой записи не запускались. Границы
6.3/6.4/7 сохранены: mapping остальных исходов относится к 6.4, retry — к
группе 7. Изменены только новый файл промта, этот журнал и README;
посторонние изменения рабочего дерева и Git index сохранены. Следующий
отдельный этап — выполнение тестовой карточки 6.3.

Проверки подготовки: `git diff --check` — exit code 0 (предупреждения
LF/CRLF для ранее изменённых файлов); прямой структурный контроль промта,
README и плана — 129 разрешающихся локальных ссылок, парные code fences и
отсутствие trailing whitespace. `git diff --cached --name-only` не вывел
файлов. Новый untracked-промт проверен напрямую; pytest не запускался.

#### 1.3.35. Выполнение тестовой карточки 6.3 — 2026-09-18

По поручению выполнить промт 6.3 дополнен только
`tests/application/test_orchestrator_commit.py`: восемь новых случаев для
`AlreadyApplied` с версиями 0/13, `Superseded` с actual версиями 0/21,
`SessionAbsent` с reason `expired`/`not_found`, окончательного
`StateCommitFailed` при уже истёкшем deadline и unexpected Exception из save.
Локальный fake отмечает завершение save и записывает его вызов. Общий helper
проверяет `load → handle → save`, original expected, delta по identity и
отсутствие повторных вызовов даже при текущем исключении. После будущей 6.4
тесты должны проверить полную модель ответа, stage/attempt/terminal,
длительности, уровни, порядок до возврата, отсутствие payload в compact logs
и отдельный traceback для unexpected Exception. Существующий положительный
`Committed`-тест 6.1 не изменён.

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py -q
# первый прогон: 8 failed, 2 passed in 0.51s; exit code 1
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py -q --tb=line
# после локального уточнения typing/helper: 8 failed, 2 passed in 0.32s; exit code 1
```

| Требование | Node ID | Фактический результат / остаток |
|---|---|---|
| FR-10/11/13/17/26, AC-7/10/19/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_one_confirmed_save_waits_and_returns_committed[0-4]`, `[7-19]` | 2 passed; положительный `Committed`-контроль сохранён |
| FR-14/15/26, AC-19/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_already_applied_returns_success_without_another_save[0]`, `[13]` | 2 failed: после одного save `orchestrator.py:258` выбрасывает `NotImplementedError`; mapping и события ждут 6.4 |
| FR-14/16/26, AC-19/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_superseded_returns_actual_version_without_artifact_or_retry[0]`, `[21]` | 2 failed по той же границе; actual version/artifact и terminal ещё не проверены успешным выполнением |
| FR-14/26, AC-19/20/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_absent_during_save_uses_commit_stage_code[expired]`, `[not_found]` | 2 failed по той же границе; commit-stage reason/code ждут 6.4 |
| FR-14/18/26, AC-19/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_commit_failure_after_expired_deadline_has_one_attempt` | Failed по той же границе; первый save состоялся, deadline не делает его второй попыткой; окончательный ответ ждёт 6.4 |
| FR-25/26, AC-19/21/26/27/31/32 | `tests/application/test_orchestrator_commit.py::test_unexpected_save_exception_is_logged_and_returns_internal_failure` | Failed: `RuntimeError` из save проброшен наружу; безопасный ответ и exception-запись ждут 6.4 |

Восемь новых тестов собраны и дошли до одного фактического save: helper
подтверждает это до проброса текущей ошибки. Проверки результата и событий
после `await execute` пока не исполнились; наличие тестов и ожидаемый red не
закрывают AC-19/20/21/26/27/31/32. R и F при красном целевом наборе не
запускались. Production, shared fakes, тест отмены, contracts, ADR, диаграммы
и сохранённые промты не менялись. Retry с открытым deadline остаётся группе 7;
K3 и 2.R2 не решались. Следующая отдельная карточка — 6.4.

Проверки целостности: `git diff --check` — exit code 0, только предупреждения
LF/CRLF для ранее изменённых файлов; прямой AST/newline/trailing-whitespace
контроль untracked-теста — exit code 0. У README и плана разрешаются 124
локальные ссылки, code fences парные, trailing whitespace нет. Staged index
пуст; посторонние файлы рабочего дерева сохранены. Коммит, ветка, push и PR
не создавались.

#### 1.3.36. Промт и реализация 6.4 — 2026-09-18

По запросу сохранить и выполнить следующий промт создан
[промт 6.4](../../prompts/2026-09-16/06-protected-commit/06.4-orchestrator-commit-outcome-mapping.md).
В `src/exact_orb/application/orchestrator.py` после единственной защищённой
попытки `save` теперь классифицируются `Committed`, `AlreadyApplied`,
`Superseded`, оба reason `SessionAbsent`, `StateCommitFailed` и unexpected
`Exception`. Версия берётся только из typed результата `save`; при
`COMMIT_FAILED` не публикуется artifact или версия. Непредвиденное исключение
получает отдельную exception-запись с traceback и безопасный
`ApplicationInternalFailure`. Невалидный возвращённый тип также
нормализуется в commit-stage internal failure. На завершённый save пишутся
один attempt и один terminal до возврата либо проброса ранее полученного
`CancelledError`; защищённая task остаётся локальной и ожидаемой.

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
# 11 passed in 0.32s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py tests/application/test_orchestrator_load.py tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py tests/application/test_orchestrator_logging.py -q
# 226 passed in 0.80s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# R: 1436 passed in 13.21s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# F: 2355 passed in 39.90s; exit code 0
```

| Требование | Node IDs / набор | Фактическое свидетельство и остаток |
|---|---|---|
| FR-10–18/26, AC-10/19/20/26/27/31/32 | 2 `test_one_confirmed_save_waits_and_returns_committed`, 2 `test_already_applied_returns_success_without_another_save`, 2 `test_superseded_returns_actual_version_without_artifact_or_retry`, 2 `test_absent_during_save_uses_commit_stage_code` | 8 passed: typed версии 0/ненулевые, artifact только при success, причина потери сессии и code на commit, один save и связанные события |
| FR-18/25/26, AC-19/21/26/27/31/32 | `test_commit_failure_after_expired_deadline_has_one_attempt`; `test_unexpected_save_exception_is_logged_and_returns_internal_failure` | 2 passed: окончательный однопопыточный failure и безопасный internal failure с отдельным traceback; retry с открытым бюджетом ждёт группу 7 |
| UC-15, FR-20/26, AC-16/17/26/29/31/32 | `test_cancel_after_save_entry_waits_for_commit_and_terminal` | 1 passed: отмена после входа в save ждёт запись и terminal до проброса; повторная отмена остаётся 9.1 |
| AC-5–10/19/29–32, ранее отложенные success/Superseded | Шесть целевых application-файлов, в том числе `test_save_uses_original_version_when_available_snapshot_changes[0]` и `[7]` | 226 passed; прежние два Superseded и положительный routing/save больше не падают |

Это первый зелёный однопопыточный application-flow, а не полная приёмка R3.2.
Вторая попытка после `StateCommitFailed`, её deadline/cancellation-правила и
ошибки второй попытки относятся к 7.1–7.2. Проверка отдельной гонки повторной
отмены остаётся 9.1. K3 о пустых issues, 2.R2 о вложенной неизменяемости и
внешние AC-34/36 не закрывались. Новых тестов и изменений контрактов/ADR/
диаграмм в 6.4 не было; существующие 6.1/6.3 прошли без правок. Следующая
отдельная карточка — 7.1.

Проверки целостности: `git diff --check` — exit code 0 (только прежние
предупреждения LF/CRLF); AST/newline/trailing-whitespace для production —
exit code 0. У нового untracked-промта, README и плана разрешаются 131
локальная ссылка, code fences парные, trailing whitespace нет. Staged index
пуст; посторонние файлы рабочего дерева сохранены. Коммит, ветка, push и PR
не создавались.

#### 1.3.37. Промт и выполнение 7.2 вместе с тестовой матрицей 7.1 — 2026-09-18

По запросу сохранён [промт 7.2](../../prompts/2026-09-16/07-commit-retry/07.2-orchestrator-exact-retry.md).
Предпосылка 7.1 к началу работы отсутствовала: `test_orchestrator_retry.py` не
существовал. Поэтому в границы 7.2 явно включено создание этой матрицы перед
production-правкой; отдельный файл промта 7.1 не создавался. В тесте реальный
`ApplicationOrchestrator` вызывается с локальным управляемым fake `ContextService`:
два ответа `save`, исходный expected и delta по identity, один load/Handler,
fake UTC clock и `asyncio.Event` для отмены. Двух заданных ответов fake
недостаточно, чтобы подтвердить применённый CAS с потерянным ответом — это 10.4.

В `src/exact_orb/application/orchestrator.py` только первый typed
`StateCommitFailed` может вызвать ровно второй защищённый `save`. Если отмена
уже наблюдалась или непустой deadline `<=` injected clock после первого отказа,
возвращается первый failure без второй записи. Повтор получает те же
`session_id`, original expected и объект delta; повторного load/Handler нет.
Исход второй попытки классифицируется по той же typed-таблице; при двух
отказах `detail_code` относится ко второму. Каждая завершённая попытка даёт
attempt event, terminal содержит фактическое число попыток, упорядоченные
error codes и сумму длительностей. После наблюдённой отмены уже начатая
задача дожидается завершения, затем пишется terminal и пробрасывается
исходный `CancelledError`.

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_retry.py -q --tb=line
# До production-правки: 11 failed, 1 passed in 0.39s; exit code 1.
# Девять случаев требовали второго save (первое падение — test_orchestrator_retry.py:152),
# два случая deadline equal/past ожидали чтение clock (строка 430).
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_retry.py tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
# 23 passed in 0.40s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# R: 1448 passed in 13.40s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# F: 2367 passed in 39.35s; exit code 0
```

| Контракт | Node IDs новой матрицы | Фактическое свидетельство |
|---|---|---|
| FR-19/26, AC-11–13/19/26/27/31/32 | `test_retry_success_uses_original_delta_and_typed_version[committed]`, `[already_applied]`; `test_retry_superseded_stops_without_artifact`; `test_retry_session_absent_preserves_reason[expired]`, `[not_found]` | Пять вторых typed outcomes, ровно два save с исходными аргументами, корректные результаты/версии/artifact и события |
| FR-18/19/25/26, AC-11/13/19/21/26/27/31/32 | `test_retry_second_commit_failure_uses_last_error_code`; `test_retry_unexpected_exception_is_internal_failure_without_third_save` | Окончательный код второго failure, упорядоченный список двух кодов либо безопасный internal failure и отдельный traceback |
| FR-19/21/26, AC-11/14/26/31/32 | `test_deadline_controls_only_second_save[none]`, `[future]`, `[equal]`, `[past]` | Граница `deadline <= now`, один вызов fake clock при deadline, просроченный deadline допускает первый save |
| FR-19/20/26, AC-15–17/26/31/32 | `test_cancellation_after_first_save_entry_forbids_retry` | Event/checkpoint доказывают наблюдённую отмену при выполняющемся первом save; один attempt и terminal предшествуют пробросу отмены, второго save нет |

Это unit-свидетельство точного orchestration retry, а не полная приёмка R3.2.
Повторная отмена и гонки после старта второго save относятся к 9.1,
реально применённый CAS с потерянным подтверждением — к 10.4, K3 и 2.R2
остаются открытыми; внешние AC не проверялись. Следующая отдельная карточка —
8.1. Контракты, ADR, диаграммы, другие production-файлы и прежние тесты
не изменялись. Staged index оставлен пустым, посторонние untracked-файлы
сохранены; коммит, ветка, push и PR не создавались. `git diff --check` —
exit code 0 (только предупреждения LF/CRLF). AST для двух Python-файлов,
концевые переводы строк/trailing whitespace пяти затронутых файлов, парность
Markdown fences и локальные ссылки проверены: exit code 0.

#### 1.3.38. Отдельный промт и повторная проверка 7.1 — 2026-09-18

По отдельному запросу сохранён
[промт 7.1](../../prompts/2026-09-16/07-commit-retry/07.1-orchestrator-retry-tests.md).
Тестовая матрица `tests/application/test_orchestrator_retry.py` уже была создана
при выполнении 7.2 (§1.3.37), поэтому промт не выдаётся за документ,
предшествовавший реализации. Сверка карточки 7.1 с текущим файлом подтвердила
12 тестовых случаев: все вторые typed outcomes и `Exception`,
исходные аргументы и identity delta, четыре границы deadline, отмена до
повтора, реальные lifecycle-события и отсутствие третьего save. Новых тестов
ради повторного исполнения не добавлено; production-файл и прежние тесты
в этом действии не менялись. Исходное содержательное падение до реализации
7.2 — 11 failed, 1 passed — остаётся в §1.3.37 и не воспроизводилось
откатом рабочего кода.

Текущие фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_retry.py -q
# 12 passed in 0.32s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# R: 1448 passed in 35.90s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# F: 2367 passed in 87.69s; exit code 0
```

Это повторная проверка unit-контракта 7.1 в уже реализованном 7.2 checkout,
а не отдельное новое integration-доказательство. Реально применённый CAS
с потерянным подтверждением остаётся 10.4, гонки повторной отмены — 9.1;
K3, 2.R2 и внешние AC также не закрывались. Следующий этап по плану — 8.1.
В этом действии изменены только новый промт 7.1, этот журнал и индекс
промтов; прочие пользовательские и незакоммиченные изменения сохранены.
`git diff --check` — exit code 0 (только предупреждения LF/CRLF);
UTF-8, концевые переводы строк, trailing whitespace, парность Markdown fences
и локальные ссылки трёх документов проверены с exit code 0. Staged index
пуст. Коммит, ветка, push и PR не создавались.

#### 1.3.39. Промт и выполнение 8.1 — 2026-09-18

Сохранён [промт 8.1](../../prompts/2026-09-16/08-lifecycle-events/08.1-orchestrator-lifecycle-sequence-tests.md).
Прежние тесты routing/load/Handler/commit/retry/cancellation уже проверяли
события отдельных веток, но `test_orchestrator_logging.py` проверял функции
записи, не границы последовательных вызовов `execute()`. Добавлено 13
сквозных случаев с настоящим `ApplicationOrchestrator` и локальными fake
зависимостями. Шесть DEBUG-сценариев выполняются по два раза с одним `run_id`,
но проверяют отдельные диапазоны реальных `LogRecord` и по одному started/
terminal на каждый вызов. Журнал вызовов и общий timeline связывают
завершённые load/Handler/save с последующими stage/attempt events и фиксируют
terminal до выхода caller. Отмена при незавершённом load/Handler управляется
`asyncio.Event` и проверена при DEBUG и INFO; незавершённая стадия и save
не получают вымышленного события. При effective INFO видны started/terminal,
а WARNING-попытки повтора остаются видимыми при скрытых DEBUG-событиях.

Новые node IDs в `tests/application/test_orchestrator_logging.py`:

| Срез | Node IDs | Свидетельство |
|---|---|---|
| Шесть последовательностей DEBUG | `test_execute_debug_lifecycle_is_bounded_per_invocation[routing]`, `[load_absent]`, `[handler_input]`, `[commit]`, `[commit_denied]`, `[retry]` | Раздельные границы двух execute с тем же `run_id`; 0/1/2 save, точные stage/attempt и terminal до caller |
| Отмена незавершённой стадии | `test_execute_cancelled_stage_has_no_completion_event[load-debug]`, `[load-info]`, `[handler-debug]`, `[handler-info]` | Event-gate подтверждает вход, отсутствует событие незавершённой стадии, `terminal_kind=cancelled` предшествует `CancelledError` |
| Effective INFO | `test_execute_effective_info_keeps_invocation_boundaries[routing]`, `[commit]`, `[retry]` | Ровно started/terminal при INFO; DEBUG stage/успешный первый save скрыты, WARNING attempts повтора видны |

Фактические команды из корня репозитория:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q -k test_execute_
# 13 passed, 176 deselected in 0.39s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
# 189 passed in 0.79s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py --collect-only -q -k test_execute_
# 13/189 collected; exit code 0; точные IDs выше
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# R: 1461 passed in 33.29s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# F: 2380 passed in 103.00s; exit code 0
```

Это доказательство порядка и границ lifecycle в локальном `execute()`, а не
проверка всех разрешённых полей, числовых длительностей и payload — они
остаются 8.2. Гонки повторной отмены остаются 9.1, реальная потеря
подтверждения CAS — 10.4; K3, 2.R2 и внешние AC не закрывались. Изменены
только новый промт, `test_orchestrator_logging.py`, этот журнал и README;
production/ADR/requirements/диаграммы не менялись. Следующий этап — 8.2.
`git diff --check` — exit code 0 (только предупреждения LF/CRLF). AST
тестового файла, UTF-8, концевые переводы строк, trailing whitespace,
парность Markdown fences и локальные ссылки четырёх затронутых файлов
проверены с exit code 0. Staged index пуст. Коммит, ветка, push и PR не
создавались; посторонние untracked-файлы сохранены.

#### 1.3.40. Промт и выполнение 8.2 — 2026-09-18

Сохранён [промт 8.2](../../prompts/2026-09-16/08-lifecycle-events/08.2-orchestrator-lifecycle-fields-and-durations.md).
Существующие тесты проверяли отдельные функции записи и последовательность
событий `execute()`; недоставало сквозной проверки, что фактические исходы и
измеренные длительности переходят в точные поля настоящих `LogRecord`.
Добавлено 10 случаев в `test_orchestrator_logging.py`. Пять веток сверяют
точные наборы полей и уровни started/stage/attempt/terminal, включая
отсутствующие длительности, достоверную версию и соответствие terminal
возвращённому `ApplicationResult`. Управляемый `perf_counter` подменяется
только в модуле Orchestrator и не затрагивает deadline-clock либо глобальные
часы pytest.

При двух фактических save с разными `StateCommitFailed` журнал сохраняет
порядок обоих кодов: 11 и 13 мс в attempt events дают 24 мс в terminal.
Два случая отмены проверяют `null` для незавершённой стадии без ложных полей
результата. На успешном пути положительный контроль подтверждает доставку
команды с birth data и уникальным маркером в Handler и вызов save; все
компактные сообщения исключают birth date/time/place, маркер и полный
`session_id`. Неизвестный calculation code возвращает fallback-текст и
отдельный диагностический `WARNING`; terminal тоже имеет `WARNING`, а
payload в нём отсутствует. Ранее существовавшие проверки прямого API
логирования и Handler не копировались целиком.

Новые node IDs в `tests/application/test_orchestrator_logging.py`:

| Срез | Node IDs | Свидетельство |
|---|---|---|
| Точные поля и управляемые длительности | `test_execute_projects_exact_fields_levels_and_measured_durations[routing]`, `[load_absent]`, `[handler_input]`, `[commit]`, `[commit_denied]` | Пять исходов, exact levels, версии и `None` для отсутствующих шагов |
| Две разные ошибки сохранения | `test_execute_preserves_distinct_commit_errors_and_sums_attempt_durations` | Два save, порядок кодов и сумма измеренных attempt durations |
| Отмена | `test_execute_cancelled_terminal_has_only_completed_durations[load]`, `[handler]` | Отсутствие длительности прерванной стадии и полей результата |
| Payload и неизвестный код | `test_execute_compact_messages_exclude_real_input_and_session_payload`, `test_execute_unknown_calculation_code_warns_without_payload` | Входные маркеры подтверждены положительно; compact сообщения их исключают, неизвестный код даёт fallback/WARN |

Фактические команды из корня репозитория после исправления двух неверных
ожиданий новых тестов (уровня terminal для отсутствующей сессии и двойного
захвата диагностического logger):

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
# 199 passed in 0.59s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py --collect-only -q -k "test_execute_projects_exact_fields_levels_and_measured_durations or test_execute_preserves_distinct_commit_errors_and_sums_attempt_durations or test_execute_cancelled_terminal_has_only_completed_durations or test_execute_compact_messages_exclude_real_input_and_session_payload or test_execute_unknown_calculation_code_warns_without_payload"
# 10/199 tests collected (189 deselected) in 0.34s; exit code 0; IDs выше
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
# R: 1471 passed in 29.35s; exit code 0
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
# F: 2390 passed in 84.75s; exit code 0
```

Первый целевой прогон дал 2 failed, 197 passed из-за неверных ожиданий новых
тестов: `SESSION_ABSENT` завершается на INFO, а ручной обработчик дублировал
диагностическую запись, уже захваченную `caplog`. Исправлены только тесты;
итоговые T/R/F выше повторены после присвоения читаемых IDs. Production,
ADR, requirements и диаграммы не менялись. Полная приёмка R3.2 этим срезом
не объявляется: повторная отмена остаётся 9.1, реальное потерянное
подтверждение CAS — 10.4; K3, 2.R2 и внешние AC остаются открытыми.
`git diff --check` — exit code 0 (только предупреждения о LF/CRLF);
локальные Markdown-ссылки и парность code fences трёх затронутых документов
проверены с exit code 0. Staged index пуст. Посторонние modified/untracked
файлы сохранены; коммит, ветка, push и PR не создавались.

## 2. Принятые границы

1. RunContext принадлежит входной границе. execute требует готовый объект,
   Handler получает его по identity. deadline добавляется с default None,
   UTC-правилом started_at и допустимым значением раньше started_at.
   Сигнатура RunContext.new() сохраняется.
2. Exact lookup по type(command) идёт до load. Orchestrator копирует mapping
   при создании; полнота поддерживаемых команд проверяется composition.
3. Handler владеет предметной работой, ContextService — session semantics.
   Application не вычисляет версии, CAS или matches_intent и не делает rebase.
4. Внешние immutable модели находятся в новом application_results.py.
   results.py и общий outcomes.py не меняются; CalculationFailed.error_code
   остаётся str. Agent-каркас не переименовывается и не удаляется.
5. failure_policy.py — чистая таблица/функция без logging. Неизвестный
   calculation code сохраняется и получает fallback; WARN пишет Orchestrator.
   Модели самостоятельно отклоняют противоречивые поля.
6. operation_logging.py содержит обычные функции штатного logger. Нет
   telemetry port, recorder в конструкторе, глобального run registry или
   counters. Каждый реализованный путь сразу пишет свои события.
7. Commit с первой реализации — отдельная защищённая единица исполнения:
   strong reference, ожидание inner task после отмены, классификация,
   terminal event, затем исходный CancelledError. Повторная отмена проверяется
   отдельно; shield без ожидания не удовлетворяет контракту.
8. Retry максимум один, только после StateCommitFailed, с прежними expected
   и delta по identity. Отмена до retry или истёкший deadline его запрещают.
9. state_version означает подтверждённое наблюдение, а не вечную актуальность.
   При COMMIT_FAILED наружу идёт None, при LOADED — прочитанная версия.
10. Session bootstrap/restore, cookie, HTTP mapping, клиентские версии,
    admission controller, durable jobs, BuildAttempt и key-idempotency —
    внешние/отложенные срезы. Заголовок Idempotency-Key не резервируется.
11. Нагрузочный профиль 1 независим от admission controller; профиль 2 требует
    реального внешнего ограничения активных запросов и очереди.
12. Приёмка новых compact events не меняет logging defaults и существующий
    DEBUG boundary flow. Уже принятый privacy-долг не открывается заново.

## 3. Конфликты и внешние зависимости

| ID | Свидетельство и влияние | Действие / зависимые этапы |
|---|---|---|
| K1 — устранён 2026-09-16 | При исходной сверке прежний deadline-промт и README назначали 01.1 реализации, тесты — позже. План закрепил обратный порядок. Прежний файл 01.1-run-context-deadline-contract.md в текущем дереве отсутствует | Подготовлены и выполнены отдельные 1.1 (тесты) и 1.2 (реализация). [Общий README серии](../../prompts/2026-09-16/README.md) актуализирован; все промты раздела 1 собраны в 01-application-foundations. Старый идентификатор не считается дополнительной карточкой |
| K2 | Handler requirements §2, таблица модулей, всё ещё называет application.results для ApplicationResult; components §7.3 и R3.2 назначают application.application_results | В 2.3–2.6 использовать уже принятое новое размещение. Устаревшую строку согласовать в docs-срезе 10.8; код Handler/results не переносить |
| K3 | Handler requirements §12.2, пункт 8, и E3 явно допускают InputRequired(issues=()). R3.2 §9 требует non-empty issues у ApplicationInputRequired. Для этого допустимого Handler outcome внешний результат не определён | До завершения 5.1/5.2 требуется явное решение о нормализации пустого issues или пересмотре внешнего ограничения. Не подставлять фиктивный issue, не менять общий outcomes.py/Handler и не выбирать InternalFailure молча. 2.5/2.6 могут реализовать текущую валидацию non-empty; приёмка всего AC-8 остаётся неполной до решения |
| X1 | AC-34 требует поведения клиента, которого в текущем срезе нет | Внешний client contract test в одном session lifecycle: новый ответ применён, старый затем проигнорирован; новый lifecycle рассматривается отдельно. Не закрывать серверным тестом |
| X2 | Конечный transport/composition admission controller не реализован | Блокируется выполнение 10.7 и закрытие AC-36. До 10.7 отдельный срез должен дать API, реальные пути конфигурации, конечные limits и queue/rejection policy. Его реализация не входит в этот план |
| X3 | HTTP/session bootstrap и deployment startup являются внешней композицией | 10.2 собирает только минимальный application-flow. Интеграционные тесты подменяют входную границу прямым вызовом; они не доказывают cookie, HTTP statuses или production deployment |
| X4 | Компонентный документ в шапке ссылается на R3.1; детальная текущая редакция — R3.2 | Использовать R3.2 для событий/отмены. В 10.8 синхронизировать статус и ссылки затронутых документов по фактическим результатам |

K3 не блокирует подготовку плана, deadline, logging helpers и остальные
независимые ветки. Этот документ фиксирует вопрос, но не изменяет контракт.

## 4. Порядок и правила проверки

Каждая карточка ниже задаёт один результат, зависимости, AC/FR, точный
allowlist, запреты и проверку. Все будущие новые пути помечены как
**планируемые**; существующие файлы из allowlist разрешается менять только
в названной части. Общее правило для всех карточек: не трогать файлы вне
allowlist, не ослаблять прежние проверки, не менять соседние контракты,
не добавлять зависимости и не создавать commit без отдельной задачи.

При подготовке каждого следующего исполняемого промта в его allowlist явно
добавляется обновление §1.3 этого плана: статус, дата, точная команда,
фактический результат/exit code, источник и ограничение свидетельства.
Это разрешение ограничено журналом выполнения; другие карточки и матрица AC
не меняются автоматически. Исторические промты и их allowlist сохраняются.

- 1.1 → 1.2; 1.3 → 1.4; 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6.
- 3.1 → 3.2 → 4.1 → 4.2 → 5.1 → 5.2 → 5.3 → 5.4.
- 6.1 → 6.2 → 6.3 → 6.4 → 7.1 → 7.2.
- 8.1–8.2 проверяют уже встроенные события; 9.1–9.2 — дополнительные гонки.
- 10.1 → 10.2 → 10.3 → 10.4 → 10.5 → 10.6.
- 10.7 требует X2, но не блокирует запуск 10.6. 10.8 сводит достигнутое и
  сохраняет статус внешних/непройденных AC; общий R3.2 нельзя объявить закрытым
  при незакрытых X1/X2/K3.

### 4.1. Контрольные точки

| Точка | Что впервые можно проверить полностью |
|---|---|
| 1.2 / 1.4 / 2.2 / 2.4 / 2.6 | Соответствующие листья: deadline, формирование событий, mapping, модели |
| 3.2 | Unknown routing через execute, отказ до I/O и защитная копия registry; позитивный полный путь ещё не собран |
| 4.2 | Отказы load; полный порядок load → Handler требует 5.2 |
| 5.2 / 5.4 | Non-success и exception/cancel до commit; положительный контроль save ещё требует 6.4 |
| 6.4 | Первый собранный execute со всеми однопопыточными commit outcomes и основной отменой; retry ещё не реализован |
| 7.2 | Полный целевой retry/deadline flow; теперь запускаются все накопленные unit-проверки |
| 8.1–9.2 | Общие logging/cancellation/concurrency свойства поверх готового execute |
| 10.3–10.5 | Реальные связи application, Handler и session, включая потерянное подтверждение CAS |
| 10.6 / 10.7 | Раздельные нагрузочные свидетельства; у 10.7 внешняя предпосылка |

Тестовые промты выполняются до реализации. Ожидаемое падение фиксируется
по причине, а не как «тест пройден». Ошибка импорта отсутствующего API означает
«тест пока нельзя исполнить», а не доказанную чувствительность негативного
assertion. После реализации обязательны положительные контроли и фактический
прогон всех ранее отложенных проверок.

Промты 3–6 собирают одну ещё не готовую операцию: промежуточный red допустим,
фиктивные success/no-op save, skip/xfail ради зелёного CI — нет.
До 6.4 flow не подключается к транспорту. После появления retry тест
окончательного первого StateCommitFailed должен использовать истёкший
deadline; он не должен закреплять отсутствие retry при открытом бюджете.

Внутри пакета 3–6 связанные прогоны могут показывать заранее обозначенные
отложенные проверки. Они фиксируются как red и не блокируют следующую
карточку сборки. Неожиданное падение уже реализованного поведения требует
исправления у владельца. В 6.4, затем в 7.2 накопленных необъяснённых
падений оставаться не должно; X1/X2 при этом не превращаются в skip-тесты.

Если новый тест обнаруживает дефект прежнего этапа, исправление возвращается
в карточку-владелец с её allowlist. Тестовый промт не получает разрешения
попутно менять production-код.

### 4.2. Команды

В этапе 0.1 команды этого раздела и карточек не выполнялись.
Последующие фактические прогоны перечислены в §1.3; остальные остаются
планируемыми. Наличие команды в карточке само по себе не означает её выполнения.
Рабочая директория — корень репозитория. В каждой карточке указана точная
целевая команда; после зелёного результата выполняется соответствующий
связанный набор, затем полный pytest. При ожидаемом red сначала завершается
парная реализация; полный прогон не подменяет отсутствующий целевой тест.

**R — связанные проверки application/session:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py tests/application tests/session tests/test_module_boundaries.py -q
```

**F — полный pytest после успешного целевого и связанного набора:**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

Команды с файлом, которого ещё нет, становятся исполнимыми после соответствующего
тестового промта. Не добавляются Ruff/mypy/coverage gates. Сетевые и платные
smoke-тесты не входят в последовательность. Для конкурентных unit-тестов:
Event/barrier/fake clock, timeout только как защита от зависания.

## 5. Карточки 36 рабочих промтов

Текущие статусы карточек приведены в §1.3.1, результаты запусков — в §1.3.3–1.3.4.
«Закрывает» описывает обязанность карточки, а не автоматически полученное
свидетельство. Исходные номера и зависимости 36 основных карточек сохранены;
дополнительная корректирующая карточка 1.R1 учтена в §1.3 отдельно.

### Промт 1.1 — Тесты deadline

- **Результат:** Default при пропуске и None; UTC принимается, naive/non-zero offset отвергаются; deadline раньше started_at допустим; new() сохраняет прежний вызов.
- **Зависимости:** 0.1; K1 учтён.
- **Закрывает:** FR-21, §11.1; основа AC-14.
- **Разрешено менять:**
  - `tests/test_run_context.py`.
- **Запрещено менять/делать:** Production-код, прежние assertion started_at, семантику UUID/new().
- **Проверка готовности:** До 1.2 ожидаемый red по новому полю. После 1.2 все случаи проверяют модель; отрицательным UTC-случаям соответствует положительный UTC-контроль.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 1.2 — Поле RunContext.deadline

- **Результат:** Добавить только deadline и UTC-валидацию по правилу started_at.
- **Зависимости:** 1.1.
- **Закрывает:** FR-21, §11.1; основа AC-14.
- **Разрешено менять:**
  - `src/exact_orb/run_context.py`.
- **Запрещено менять/делать:** Сигнатуру new(), автоматический timeout, сравнение deadline со started_at и существующие тесты.
- **Проверка готовности:** Зелёные тесты 1.1; старые вызовы new() работают, истёкший deadline хранится без отказа.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_run_context.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 1.3 — Контракт функций lifecycle logging

- **Результат:** Тесты четырёх видов записи, обязательных полей и уровней R3.2 §11.5; result/cancelled terminal shapes; конечные неотрицательные duration и None для незавершённых стадий.
- **Зависимости:** 0.1; штатный logger изучен.
- **Закрывает:** AC-26, 29–33 на уровне формата; FR-26.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_logging.py`.
- **Запрещено менять/делать:** Orchestrator, настройки logging и создание telemetry port/recorder. Частоты событий execute пока не доказаны.
- **Проверка готовности:** Новый планируемый файл. До 1.4 возможна ошибка импорта; после 1.4 caplog проверяет записи, включая WARNING второй попытки и отсутствие выдуманных полей у cancelled.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 1.4 — Функции записи событий

- **Результат:** Реализовать компактные функции штатного logger по тестам 1.3. У каждой записи event/run_id и только разрешённые поля; request-specific накопление остаётся в execute.
- **Зависимости:** 1.3.
- **Закрывает:** AC-26, 29–33: формирование; FR-26.
- **Разрешено менять:**
  - `src/exact_orb/application/operation_logging.py`.
- **Запрещено менять/делать:** Глобальные counters, active-run registry, dependency injection телеметрии, переиспользование полного component_message для lifecycle payload.
- **Проверка готовности:** Планируемый модуль; форматы и уровни проходят тесты. Единичность/порядок на execute проверяются позже, а не объявляются готовыми здесь.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.1 — Тесты политики отказов

- **Результат:** Табличный тест каждой строки R3.2 §10: code/detail_code/message/retryable, оба resolution retryable, обе стадии absence, известные и неизвестный calculation code.
- **Зависимости:** 0.1.
- **Закрывает:** AC-21, 25, 33; FR-23.
- **Разрешено менять:**
  - `tests/application/test_application_failure_policy.py`.
- **Запрещено менять/делать:** Models, runtime logging, значения общих Handler outcomes; неизвестный код нельзя делать ValidationError.
- **Проверка готовности:** Планируемый файл; после 2.2 точные тексты и безопасный fallback. Здесь проверяется описание неизвестного кода, фактический WARN — 5.2/8.2.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_failure_policy.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.2 — Чистая политика отказов

- **Результат:** Одна таблица/чистая функция для моделей и Orchestrator; возвращает согласованную реакцию, сохраняет неизвестный detail_code, не пишет события.
- **Зависимости:** 2.1.
- **Закрывает:** AC-21, 25, 33; FR-23.
- **Разрешено менять:**
  - `src/exact_orb/application/failure_policy.py`.
- **Запрещено менять/делать:** Общий outcomes.py, logging, I/O, локализационный framework.
- **Проверка готовности:** Планируемый модуль; тесты всех строк зелёные, одинаковый вход даёт одинаковые поля без побочных эффектов.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_failure_policy.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.3 — Тесты успешных моделей и Superseded

- **Результат:** Committed, AlreadyApplied, Superseded: статусы, code, retryable, version bounds, payload, run_id и frozen. Позитивные валидные образцы и каждая запрещённая связка.
- **Зависимости:** 2.2.
- **Закрывает:** AC-19, 23, 24, 26, 27.
- **Разрешено менять:**
  - `tests/application/test_application_results.py`.
- **Запрещено менять/делать:** BuildNatalSuccess и CalculationFailed; критерий равенства всего union ещё не закрывается.
- **Проверка готовности:** Планируемый файл; Committed требует version>=1, остальные >=0; Superseded не принимает artifact. Полное прохождение после 2.4.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.4 — Три модели результатов

- **Результат:** Реализовать ApplicationCommitted, ApplicationAlreadyApplied, ApplicationSuperseded в отдельном модуле; frozen и согласованные поля.
- **Зависимости:** 2.3.
- **Закрывает:** AC-19, 23, 24, 26, 27: эти три варианта.
- **Разрешено менять:**
  - `src/exact_orb/application/application_results.py`.
- **Запрещено менять/делать:** application/results.py, перенос Handler outcomes, export через соседние __init__.py, объявление неполного union окончательным.
- **Проверка готовности:** Планируемый модуль; тесты 2.3 проходят, existing Handler contracts сохраняются в связанном наборе R.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.5 — Тесты остальных моделей и полного union

- **Результат:** Оставшиеся семь моделей, точное множество status triples §8, связи reason/stage/code, versions, messages, issues, frozen. У InternalFailure запрещены неверные code/detail/version сочетания.
- **Зависимости:** 2.4; K3 записан.
- **Закрывает:** AC-19–25, 27; FR-22.
- **Разрешено менять:**
  - `tests/application/test_application_results.py`.
- **Запрещено менять/делать:** Production-код, ослабление non-empty требования R3.2 ради совместимости с пустым Handler issues; выбор runtime-реакции K3.
- **Проверка готовности:** После 2.6 все 10 моделей проверены. Таблица §8 даёт множество из 12 уникальных троек: две её строки имеют одну тройку; нельзя сверять число строк с числом моделей.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 2.6 — Полный ApplicationResult

- **Результат:** Остальные модели и union с Literal там, где значение фиксировано; полная валидация fields, state_version и payload, frozen. Calculation retryable зависит от сохранённого error_code через policy.
- **Зависимости:** 2.5.
- **Закрывает:** AC-19–25, 27; FR-22.
- **Разрешено менять:**
  - `src/exact_orb/application/application_results.py`.
- **Запрещено менять/делать:** Открытый общий error_code, Handler outcomes, пустые issues в публичной модели без принятой правки R3.2.
- **Проверка готовности:** Все модельные проверки проходят; K3 остаётся вопросом преобразования Handler → application, не скрывается валидатором.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_results.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 3.1 — Тесты входа и routing

- **Результат:** Обязательный run, точный тип/подкласс, unknown command до load, defensive copy registry. Запись порядка обращений в recording fake и положительный контроль известной команды.
- **Зависимости:** 1.2, 1.4, 2.6.
- **Закрывает:** AC-1, 3–5, 26, 29; FR-05.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_routing.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Реализацию Orchestrator, MRO/isinstance fallback; не проверять только отсутствие вызова без позитивной ветки.
- **Проверка готовности:** Оба файла планируемые. Unknown command проверяется после 3.2; положительный load/Handler-контроль зависит от 4.2/5.2, success-контроль — от 6.4.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 3.2 — Конструктор и отказ routing

- **Результат:** Ввести context, copied handlers, clock и обязательную execute signature. Exact lookup до I/O; корректный отказ unknown command, started и terminal с исходным run_id.
- **Зависимости:** 3.1.
- **Закрывает:** AC-1, 3, 4, 26, 29; FR-05.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Fallback RunContext/Handler, mutable request fields, runtime registration, save или фиктивный success для ещё не собранной ветки.
- **Проверка готовности:** Планируемый модуль. Новые тесты назвать с этими устойчивыми фрагментами; выбранный набор обязан содержать реальные тесты. Полный routing-файл повторить на 6.4.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py -k "requires_run or unknown_command or subclass or registry" -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 4.1 — Тесты load и original expected

- **Результат:** Порядок load, передача session_id, snapshot.state, фиксация version; absence/read failure/exception не запускают Handler, корректны result и события.
- **Зависимости:** 3.2.
- **Закрывает:** AC-5–7, 19–21, 26, 27, 29, 30.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_load.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** ContextService/store implementation и новое чтение ради теста expected.
- **Проверка готовности:** Планируемый test-файл. Отказы проверяются после 4.2; передача state — 5.2; expected на реальном вызове save — 6.4. Spy проверяет наблюдаемый вызов, не private local.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 4.2 — Load и его отказы

- **Результат:** Вызвать ContextService.load, обработать три typed outcomes и unexpected Exception; зафиксировать snapshot/version один раз; писать события завершённого load.
- **Зависимости:** 4.1.
- **Закрывает:** AC-5–7, 19–21, 26, 27, 29, 30.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Прямой SessionStore, отдельный get/touch, вызов Handler при отказе, перевод CancelledError в InternalFailure.
- **Проверка готовности:** Новые тесты используют указанные имена. Отказ load завершает операцию; known success path проверится после 5.2/6.4. Измерение duration не добавляет wall-clock зависимость для deadline.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_load.py -k "absent or read_failed or unexpected" -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 5.1 — Тесты вызова Handler и non-success

- **Результат:** Identity command/state/run; InputRequired с issues, ResolutionUnavailable, CalculationFailed не сохраняются; unknown calculation code получает fallback/WARN; положительный контроль success достигает commit.
- **Зависимости:** 4.2, 2.6; K3 решён для пустого issues.
- **Закрывает:** AC-2, 5, 7, 8, 21, 25–27, 29, 30, 33.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_handler.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Shared outcomes и Handler; нельзя молча исключить пустой issues из полноты AC-8.
- **Проверка готовности:** Планируемый test-файл. Обычные non-success проверки проходят после 5.2; положительный commit-контроль — 6.4. Сценарий K3 готовится только по явному решению.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 5.2 — Вызов и классификация Handler

- **Результат:** Передать исходные command/snapshot.state/run, классифицировать штатные исходы через модели/policy; stage/terminal events и WARN unknown code встроены сразу.
- **Зависимости:** 5.1; явное решение K3 для соответствующей ветки.
- **Закрывает:** AC-2, 5, 7, 8, 21, 25–27, 29, 30, 33.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Handler persistence, новый run, изменение session state, save после non-success.
- **Проверка готовности:** После реализации обычные ветки зелёные; имена тестов включают эти фрагменты. Непустой InputRequired не закрывает вопрос K3, success-control завершается в 6.4.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py -k "identity or non_success or unknown_calculation" -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 5.3 — Тесты нарушений Handler и ранней отмены

- **Результат:** None/чужой тип, unexpected Exception и CancelledError до commit, включая отменённый load. Нет save; raw exception не в user_message; cancelled terminal без фиктивных статусов/finished стадии.
- **Зависимости:** 5.2; общие fakes уже готовы.
- **Закрывает:** AC-9, 17, 21, 26, 29, 30, 32, 33; FR-25.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_handler.py`.
  - `tests/application/test_orchestrator_logging.py`.
- **Запрещено менять/делать:** Перехват всех BaseException как application failure; tests на KeyboardInterrupt/SystemExit не должны прерывать весь pytest runner.
- **Проверка готовности:** Event фиксирует вход в стадию; после cancel нет save, наружу выходит отмена, terminal предшествует её наблюдению вызывающим. До 5.4 новые сценарии могут быть red.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 5.4 — Ошибки Handler и отмена до commit

- **Результат:** Нормализовать invalid outcome/Exception в InternalFailure с loaded version. CancelledError журналируется как cancelled и пробрасывается; KeyboardInterrupt/SystemExit не нормализуются.
- **Зависимости:** 5.3.
- **Закрывает:** AC-9, 21, 26, 29, 30, 32, 33; FR-25.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Bare except/BaseException → InternalFailure, save на отказе, подмена ошибки InputRequired.
- **Проверка готовности:** Новые ранние ветки проходят тесты. Завершённая стадия имеет один event; прерванная — только cancelled terminal. Общий success-контроль добавляет 6.4.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 6.1 — Тесты одной защищённой попытки commit

- **Результат:** Один save только после Handler success; точные session_id/expected/delta; Event о входе в save, cancel request, разрешение save, классификация/terminal, затем CancelledError.
- **Зависимости:** 5.4.
- **Закрывает:** AC-7, 10, 16, 17, 19, 26, 27, 31, 32.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_commit.py`.
  - `tests/application/test_orchestrator_cancellation.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Обычный sleep вместо синхронизации; нельзя считать создание inner task доказательством начатого save.
- **Проверка готовности:** Планируемые test-файлы. До 6.2 red. Caller не завершается до освобождения save; после освобождения есть результат commit в журнале и наблюдаемая отмена доставки.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 6.2 — Защищённая commit-стадия с первой попыткой

- **Результат:** Сразу реализовать task lifetime/strong reference/ожидание после отмены; один save, Committed, attempt event и terminal. Общую форму ожидания сохранить для retry.
- **Зависимости:** 6.1.
- **Закрывает:** AC-7, 10, 16, 17, 19, 26, 27, 31, 32; FR-20.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Shield без drain inner task, background fire-and-forget, cancellation status в ApplicationResult, изменение CAS.
- **Проверка готовности:** Пройден Event-тест первого commit после отмены; готовность всего commit mapper наступает в 6.4. События не откладываются до группы 8.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 6.3 — Тесты остальных commit outcomes

- **Результат:** AlreadyApplied, Superseded, SessionAbsent по обоим reason, окончательный StateCommitFailed и unexpected Exception; нельзя повторять Handler/load/save после definitive outcome.
- **Зависимости:** 6.2.
- **Закрывает:** AC-10, 19–21, 26, 27, 31, 32.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_commit.py`.
- **Запрещено менять/делать:** Переписывание нормального теста 6.1 и production-кода; mock самого ContextService допустим здесь только как unit boundary.
- **Проверка готовности:** StateCommitFailed после одной попытки проверяется с истёкшим deadline, чтобы тест оставался верен после 7.2. Положительный контроль Committed обязателен.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_commit.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 6.4 — Полный execute без retry

- **Результат:** Собрать все однопопыточные commit outcomes, stage-aware internal failure и отсутствие artifact в Superseded/failure. Terminal гарантирован до возврата или отложенного cancel.
- **Зависимости:** 6.3, 3.1–6.2; K3 для полноты flow.
- **Закрывает:** AC-5–10, 16, 19–21, 26, 27, 29–32.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Rebase, matches_intent, вычисление state_version, новая session, ослабление negative spies.
- **Проверка готовности:** Первый полный публичный flow и все накопленные позитивные контроли. Retry ещё отсутствует, поэтому полная R3.2-приёмка не заявляется.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_routing.py tests/application/test_orchestrator_load.py tests/application/test_orchestrator_handler.py tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 7.1 — Тесты retry, deadline и отмены

- **Результат:** Матрица первого StateCommitFailed и всех вторых typed outcomes/Exception; delta identity, original expected, отсутствие load/Handler/rebase, максимум два save. Deadline None/будущий/равен clock/прошлый; отмена до старта второго save.
- **Зависимости:** 6.4, 1.2.
- **Закрывает:** AC-11–17, 19, 25–27, 31, 32; FR-19–21.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_retry.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Реальное ожидание deadline; утверждение, что мок с двумя failure доказывает отсутствие двойной записи.
- **Проверка готовности:** Планируемый файл. Fake UTC clock проверяет границу <= now; Event подтверждает наблюдённую отмену до разрешения первого save. Retry open-budget — позитивный контроль.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_retry.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 7.2 — Один точный retry

- **Результат:** Добавить вторую попытку внутрь защищённой стадии. Перед стартом проверить наблюдённую отмену и injected clock при deadline; при запрете вернуть первый failure; сохранять error codes обеих попыток.
- **Зависимости:** 7.1.
- **Закрывает:** AC-11–16, 19, 25–27, 31, 32; FR-19–21.
- **Разрешено менять:**
  - `src/exact_orb/application/orchestrator.py`.
- **Запрещено менять/делать:** Второй Handler/load, fresh expected, третья попытка, timeout Handler, retry unexpected Exception вместо typed StateCommitFailed.
- **Проверка готовности:** Матрица зелёная; окончательный detail_code — последней фактической попытки. R прогоняет все ранее отложенные unit-сценарии.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_retry.py tests/application/test_orchestrator_commit.py tests/application/test_orchestrator_cancellation.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 8.1 — Сквозная последовательность событий

- **Результат:** Проверить через execute routing/load/Handler/commit/failure/cancel: ровно started и terminal, только завершённые stage events, одна запись на каждый save и порядок до выхода caller.
- **Зависимости:** 7.2, 1.4.
- **Закрывает:** AC-26, 29–32.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_logging.py`.
- **Запрещено менять/делать:** Позднее внедрение всей instrumentation и production fixes в тестовом промте; count по одному run_id без границ invocation недостаточен.
- **Проверка готовности:** Caplog/spy связывают события с каждым вызовом; effective INFO сохраняет started/finished. Debug проверка видит промежуточные записи. При дефекте возврат в владельца 3.2–7.2.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 8.2 — Состав lifecycle events и длительности

- **Результат:** Проверить разрешённые поля, exact levels, unknown-code WARN, отсутствие birth/session payload в compact events/messages. Обе различные ошибки commit сохраняются по порядку; total commit duration равна сумме attempts.
- **Зависимости:** 8.1.
- **Закрывает:** AC-21, 25–27, 31–33; FR-26/27.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_logging.py`.
- **Запрещено менять/делать:** Глобальную logging policy, DEBUG payload соседних компонентов, реальное время как числовой эталон.
- **Проверка готовности:** Управляемый источник duration в модуле через тестовый seam/monkeypatch; это не clock deadline. None для незавершённого этапа, finite >=0, sentinel payload обнаруживается положительным контролем.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_logging.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 9.1 — Повторная отмена и вторая попытка

- **Результат:** Детерминированно отменить request повторно во время ожидания inner task; отдельно отменить уже начавшийся save attempt=2. Дождаться исхода и cleanup, потом наблюдать исходный CancelledError.
- **Зависимости:** 7.2, 8.1.
- **Закрывает:** AC-15–18, 29, 31, 32.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_cancellation.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** sleep, отмену самой inner task как подмену внешней отмены, third retry, проверку только финального task.done().
- **Проверка готовности:** Events различают границы: второй save уже начат либо ещё запрещаем. Нет orphan task, terminal ровно один. Дефект lifetime возвращается в 6.2; retry race — в 7.2.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_cancellation.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 9.2 — Изоляция параллельных execute

- **Результат:** На одном экземпляре Orchestrator чередовать разные session_id, команды, run_id, snapshot versions и delta. Отдельно гонка одной сессии. Проверить аргументы каждого save и принадлежность результата/событий.
- **Зависимости:** 7.2, 8.1; общие recording fakes.
- **Закрывает:** AC-28; FR-24, §6.1.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_concurrency.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Instance current_* поля, mutex ради прохождения теста, одинаковые данные во всех запросах, скрывающие смешение.
- **Проверка готовности:** Планируемый файл. Barrier доказывает одновременное нахождение двух операций в стадии до освобождения любой; timeout только страховка. Сверяются разные marker/version/delta по identity.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_concurrency.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.1 — Тест полноты registry в composition

- **Результат:** Минимальная поддерживаемая команда — BuildNatalCommand. Проверить полный и неполный реестр, startup failure до пользовательского execute; отсутствие неявного fallback.
- **Зависимости:** 6.4; целевой интерфейс composition фиксируется в тесте.
- **Закрывает:** FR-05; поддержка AC-3/4.
- **Разрешено менять:**
  - `tests/application/test_application_composition.py`.
- **Запрещено менять/делать:** Реестр tool/LLM, общий DI-framework, новый transport, проверку полноты только первым пользовательским запросом.
- **Проверка готовности:** Планируемый файл. Использовать локальную функцию проверки registry в composition и сборку с явно переданными зависимостями; полный mapping — позитивный контроль. До 10.2 red.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_composition.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.2 — Минимальная application composition

- **Результат:** Собрать application coordinator из предоставленных context/clock и реального BuildNatalHandler с resolver/artifact dependencies; проверить registry по поддерживаемым типам при startup.
- **Зависимости:** 10.1, 7.2.
- **Закрывает:** FR-05; основа AC-35.
- **Разрешено менять:**
  - `src/exact_orb/application/composition.py`.
- **Запрещено менять/делать:** HTTP server, сессионный bootstrap, глобальные singleton, новый runtime/DI и production admission controller.
- **Проверка готовности:** Планируемый модуль. Не переносить настройку Swiss runtime и catalog/deployment policy из владеющих компонентов. Startup не запускает пользовательский flow.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_composition.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.3 — Реальная интеграция application, Handler и session

- **Результат:** Входная граница тестовая; Orchestrator, ContextService, InMemory persistence и BuildNatalHandler реальные. Natal/cosmogram, non-success, cache hit/miss, committed state/version и run_id проверяются вместе.
- **Зависимости:** 10.2, 8.1, 9.2; K3 решён для полноты.
- **Закрывает:** AC-2, 5–10, 19, 20, 25–27; интеграционное подтверждение.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_integration.py`.
  - `tests/fixtures/application.py`.
  - `tests/application/test_build_natal_integration.py`.
- **Запрещено менять/делать:** Мок Orchestrator/ContextService/Handler, изменение engine/golden. Старый test_build_natal_integration.py разрешён только для переноса сборки _stand в общую fixture и обновления её вызовов, без изменения assertions.
- **Проверка готовности:** Первые два пути планируемые. Переиспользовать calculation.py, places.jsonl и existing EngineService/ChartArtifactResolver. Новый tests/fixtures/application.py экспортирует test stand; для технических отказов изменяются только leaf seams.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_integration.py tests/application/test_build_natal_integration.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.4 — Потерянное подтверждение применённого CAS

- **Результат:** Реальный persistence сначала применяет CAS, тестовая обёртка sessions facet однократно бросает SessionPersistenceError после записи. Реальный ContextService возвращает failure, execute автоматически повторяет и получает AlreadyApplied.
- **Зависимости:** 10.3, 7.2.
- **Закрывает:** AC-11–13, 19, 26, 27, 31; session P3-AC-12.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_integration.py`.
  - `tests/application/orchestrator_fakes.py`.
- **Запрещено менять/делать:** Сценарий из двух заданных ответов ContextService, fault до записи, изменение adapters/context, конкурирующую запись в этом конкретном тесте.
- **Проверка готовности:** Планируемый node test_lost_ack_after_applied_cas_retries_without_second_mutation. Две попытки CAS/save с identity delta, один Handler, version N+1 за обе попытки; нижележащий touch один в измеряемом execute.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_integration.py -k lost_ack -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.5 — Интеграция с SQLite и CAS-гонки

- **Результат:** Реальные ContextService и два независимых SQLite handles одного файла; реальные Handler и application. Barrier после исходного load: одинаковые намерения → Committed/AlreadyApplied, разные → Committed/Superseded.
- **Зависимости:** 10.3, 10.4, 9.1/9.2.
- **Закрывает:** AC-12, 19, 20, 26–28; session P3-AC-11.
- **Разрешено менять:**
  - `tests/application/test_orchestrator_sqlite_integration.py`.
- **Запрещено менять/делать:** Изменение SQLite/ContextService и reuse одного in-memory state вместо file-backed CAS; искусственный sleep; дублирование всего session conformance.
- **Проверка готовности:** Планируемый test-файл; helpers из tests/fixtures/application.py и orchestrator_fakes.py читаются. Финальная версия N+1 и state победителя; проверка после завершения через отдельный read не считается rebase внутри execute.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_orchestrator_sqlite_integration.py tests/session/test_sqlite.py -q
```

После зелёного целевого набора: R → F (§4.2); при ожидаемом red — парная реализация.

### Промт 10.6 — Штатный application load profile

- **Результат:** Создать отдельный harness и отчёт: 5 RPS, >=60 секунд подачи, >=300 завершившихся операций, effective INFO, drain, peak active, результаты по статусам, cache hit/miss, смешанные отдельные/общие сессии.
- **Зависимости:** 10.2–10.5; admission controller не требуется.
- **Закрывает:** AC-35; нагрузочное подтверждение AC-26, 28, 29; §6.3/6.5.
- **Разрешено менять:**
  - `scripts/bench_application_orchestrator.py`.
  - `docs/project_management/application_orchestrator_load_profile_1.md`.
- **Запрещено менять/делать:** Production admission, session benchmark, SLA p95, фиктивные handler/context. Измерение только принятых запросов не считается throughput.
- **Проверка готовности:** Оба пути планируемые. Реальные application/Handler/session и calculation stack; стенд/данные из tests/fixtures/application.py. Нужны фактические counts, полезные исходы, throughput, duration подачи/drain и оценка dialog overhead с явно указанной методикой.

Точная команда normal profile приведена в §8.1. До нагрузки — R, затем F; нагрузка запускается только в этапе 10.6.

### Промт 10.7 — Деградационный profile

- **Результат:** После готовности внешнего admission API подключить его к harness; управляемо задержать leaf resolver либо persistence и измерить предел active/queue, admission outcomes, attempts/terminal на каждое принятое execute.
- **Зависимости:** 10.6 и X2; до X2 выполнять нельзя.
- **Закрывает:** AC-36; §6.2/6.4.
- **Разрешено менять:**
  - `scripts/bench_application_orchestrator.py`.
  - `docs/project_management/application_orchestrator_load_profile_2.md`.
- **Запрещено менять/делать:** Создание нового admission controller внутри тестового стенда как замена production/composition компонента; блокирование 10.6; отсутствие лимита очереди.
- **Проверка готовности:** Отчёт планируемый, harness продолжает 10.6. Пределы 8 активных/16 очереди — предлагаемая конфигурация стенда, не production defaults. Внешний компонент принимается как зависимость; его файлы не входят в allowlist. Пока X2 открыт — только статус blocked, без выдуманных измерений.

Точная команда degraded profile приведена в §8.2. Пока X2 открыт, команду не запускать. После готовности X2 — целевой профиль, R и F.

### Промт 10.8 — Итоговая приёмка и статус документации

- **Результат:** Свести результаты точных прогонов, заполнить матрицу evidence, синхронизировать только затронутые целевые/реализованные утверждения; сохранить открытые K3/X1/X2 при отсутствии решений/тестов.
- **Зависимости:** Пройденные 1.1–10.6; 10.7 при готовности X2. Непройденное явно остаётся открытым.
- **Закрывает:** Сводка AC-1–36, FR-05/21, P3-AC-11/12; не заменяет проверки.
- **Разрешено менять:**
  - `docs/project_management/application_orchestrator_implementation_plan.md`.
  - `docs/requirements/component_responsibilities/exact-orb_application_orchestrator_requirements.md`.
  - `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`.
  - `docs/requirements/handlers/exact_orb_build_natal_handler_requirements.md`.
  - `docs/requirements/component_responsibilities/exact-orb_applicationOrchestrator_agentOrchestrator.md`.
  - `docs/requirements/overview.md`.
  - `docs/requirements/scenarios.md`.
  - `docs/sequence_diagrams/build_natal/README.md`.
  - `docs/sequence_diagrams/build_natal/000-build_natal_end_to_end.puml`.
  - `docs/sequence_diagrams/build_natal/001-build_natal_positive_cache_miss.puml`.
  - `docs/sequence_diagrams/build_natal/002-build_natal_cache_hit.puml`.
  - `docs/sequence_diagrams/build_natal/003-build_cosmogram_time_unknown.puml`.
  - `docs/sequence_diagrams/build_natal/004-build_natal_input_required.puml`.
  - `docs/sequence_diagrams/build_natal/005-build_natal_technical_failures.puml`.
  - `docs/sequence_diagrams/build_natal/006-build_natal_superseded_cas.puml`.
  - `docs/sequence_diagrams/build_natal/007-build_natal_commit_failure_and_session_expired.puml`.
  - `docs/sequence_diagrams/build_natal/008-build_natal_application_unavailable.puml`.
  - `docs/sequence_diagrams/build_natal/009-build_natal_commit_cancellation.puml`.
  - `docs/sequence_diagrams/build_natal/010-build_natal_application_observability.puml`.
- **Запрещено менять/делать:** Production/tests, изменение принятых ADR и архитектурных правил, расширение требований под получившуюся реализацию. Правка каждой диаграммы допустима только при реально изменившемся статусе/потоке.
- **Проверка готовности:** Целевые application/session/boundary тесты → R → F; doc links/fences/git diff --check. Статусы отмечаются по фактам, не все файлы allowlist обязаны измениться. Итог готовности разделён на application core, внешние AC и deployment.

Команды R и F из §4.2, затем документальные проверки §9. Повторять нагрузку только при изменениях, способных сделать прежний отчёт неактуальным.

## 6. Матрица приёмки R3.2

Ни один AC не отмечен закрытым в этапе 0.1. Формулировки AC ниже скопированы
из R3.2 §15 без изменения слов; переносы строк свёрнуты.
Все имена test_*.py в колонке «Свидетельство» — **планируемые** файлы
`tests/application/` из соответствующих карточек, если не указано E1–E8.
Ссылки E1–E8 обозначают только соседнее существующее покрытие §1.2.
Первый gate разделяет проверку моделей и поведения execute.

| AC | Точная формулировка R3.2 | Реализация | Тестовые этапы → первый gate | Свидетельство / предел существующего покрытия | Текущий статус |
|---|---|---|---|---|---|
| AC-1 | `execute()` без `run` не вызывается по сигнатуре; fallback отсутствует. | 3.2 | 3.1 → 3.2 | test_orchestrator_routing.py: requires_run; E1 не проверяет execute | Целевой |
| AC-2 | Handler получает тот же объект `RunContext` по identity. | 5.2 | 5.1 → 5.2; success-контроль 6.4 | test_orchestrator_handler.py: identity; E3 — только нижняя граница | Целевой |
| AC-3 | Точный тип команды маршрутизируется; подкласс не матчится. | 3.2 | 3.1 → 5.2/6.4 с позитивным контролем | test_orchestrator_routing.py: exact type/subclass | Целевой |
| AC-4 | Unknown command не вызывает load и даёт `HANDLER_NOT_REGISTERED`. | 3.2 | 3.1 → 3.2 | test_orchestrator_routing.py: unknown_command + call journal | Целевой |
| AC-5 | Routing предшествует load; load предшествует Handler. | 3.2, 4.2, 5.2 | 3.1/4.1/5.1 → 6.4 | test_orchestrator_load.py: порядок; E5 знает только load | Целевой |
| AC-6 | `SessionAbsent`/`StateReadFailed` не запускают Handler. | 4.2 | 4.1 → 4.2 | test_orchestrator_load.py: typed refusals; E5 — session outcome | Целевой |
| AC-7 | Handler получает `snapshot.state`; original version фиксируется до Handler. | 4.2, 5.2, 6.2 | 4.1/5.1/6.1 → 6.4 | test_orchestrator_handler.py и test_orchestrator_commit.py: identity/expected; E5 | Целевой |
| AC-8 | Три non-success Handler outcome не вызывают save. | 5.2 | 5.1 → 6.4 с success-контролем | test_orchestrator_handler.py: no save; E3 подтверждает пустой issues | Целевой; K3 открыт |
| AC-9 | Невалидный тип outcome не вызывает save и даёт internal failure. | 5.4 | 5.3 → 5.4; позитивный save 6.4 | test_orchestrator_handler.py: None/чужой тип + no save | Целевой |
| AC-10 | Обычный успешный commit вызывает один save. | 6.2 | 6.1 → 6.2; интеграция 10.3 | test_orchestrator_commit.py: одна запись после success; E5 — один session CAS | Целевой |
| AC-11 | Первый `StateCommitFailed` запускает не более одного повтора. | 7.2 | 7.1 → 7.2; 10.4 | test_orchestrator_retry.py: call count; E6 не выполняет auto retry | Целевой |
| AC-12 | Повтор использует ту же delta по identity и тот же original expected; между попытками нет load. | 6.2, 7.2 | 7.1 → 7.2; 10.4 | test_orchestrator_retry.py: identity/no load; E5/E6 покрывают нижнюю границу | Целевой |
| AC-13 | Повторный typed outcome классифицируется по общей таблице. | 6.4, 7.2 | 7.1 → 7.2 | test_orchestrator_retry.py: все вторые typed outcomes | Целевой |
| AC-14 | Истёкший deadline запрещает повтор; результат содержит первый failure. | 1.2, 7.2 | 1.1 и 7.1 → 7.2 | test_orchestrator_retry.py: injected clock, граница deadline; E1 без deadline | Целевой |
| AC-15 | Отмена до старта повтора также запрещает повтор. | 6.2, 7.2 | 7.1 → 7.2; 9.1 | test_orchestrator_retry.py и test_orchestrator_cancellation.py: cancel до attempt 2 | Целевой |
| AC-16 | Отмена уже начатого commit не отменяет inner task; terminal event пишется до проброса `CancelledError`. | 6.2, 6.4, 7.2 | 6.1 → 6.4; 9.1 для attempt 2 | test_orchestrator_cancellation.py: finish inner → terminal → caller cancel; E3 не покрывает commit | Целевой |
| AC-17 | Тест отмены использует `asyncio.Event` и доказывает порядок без `sleep`. | 6.2/7.2: поведение; 6.1/9.1: метод теста | 6.1 → 6.2; расширение 9.1 | test_orchestrator_cancellation.py: Event handshake; отсутствие sleep как доказательства | Целевой |
| AC-18 | Повторная отмена не оставляет commit task без strong reference/ожидания. | 6.2; 7.2 для retry | 9.1 → 9.1 | test_orchestrator_cancellation.py: repeat cancel/drain/no orphan | Целевой |
| AC-19 | `Committed`, `AlreadyApplied`, `Superseded`, absence и failures дают заданные модели и полную связку полей. | 2.4/2.6; 4.2/5.2/5.4/6.4/7.2: runtime | 2.3/2.5 → 2.6 модели; 6.3/7.1 → 7.2 runtime | test_application_results.py и test_orchestrator_commit.py; E2 — Handler, не application | Целевой |
| AC-20 | Исчезновение сессии после Handler отличается кодом и handler status. | 2.6, 4.2, 6.4 | 4.1/6.3 → 6.4; 10.5 | test_orchestrator_load.py и test_orchestrator_commit.py: stage/reason/code | Целевой |
| AC-21 | Raw exception text отсутствует в `user_message`. | 2.2, 4.2, 5.4, 6.4 | 2.1/5.3/6.3 → 6.4; аудит 8.2 | test_application_failure_policy.py и test_orchestrator_logging.py; E4 относится к Handler | Целевой |
| AC-22 | Множество status triples union точно равно §8. | 2.4, 2.6 | 2.5 → 2.6 | test_application_results.py: точное множество 12 троек | Целевой |
| AC-23 | Для каждой модели отклоняются противоречивые `code`, `retryable`, `detail_code`, `state_version` и payload. | 2.4, 2.6 | 2.3/2.5 → 2.6 | test_application_results.py: полная связка и позитивный валидный образец каждого варианта | Целевой |
| AC-24 | Модели immutable после создания. | 2.4, 2.6 | 2.3/2.5 → 2.6 | test_application_results.py: mutation rejected; E2 не проверяет новые модели | Целевой |
| AC-25 | Все известные failure-коды возвращают точный текст; неизвестный calculation code даёт fallback и WARN. | 2.2/2.6: mapping/models; 5.2: WARN | 2.1/2.5 → 2.6; 5.1 → 5.2; 8.2 | test_application_failure_policy.py, test_application_results.py, test_orchestrator_logging.py | Целевой |
| AC-26 | `run_id` совпадает с входным во всех результатах/events. | 2.4/2.6, 1.4, 3.2–7.2 | По веткам; полный набор 8.1, интеграция 10.3 | test_orchestrator_logging.py: result/events с входным id; E8 только до Handler | Целевой |
| AC-27 | `state_version` присутствует и отсутствует строго по §12. | 2.4/2.6, 4.2–7.2 | Модели 2.6; runtime 7.2; общий аудит 8.2 | test_application_results.py и test_orchestrator_commit.py; E5 session versions | Целевой |
| AC-28 | Параллельные execute не разделяют request state. | 3.2–7.2: только locals | 9.2; интеграция 10.5 | test_orchestrator_concurrency.py: разные аргументы и marker; E6 только ContextService | Целевой |
| AC-29 | На execute приходится ровно один `application_operation_started` и один `application_operation_finished`: result либо cancelled. | 1.4 и каждая ветка 3.2–7.2 | Частично по веткам; полнота 8.1 | test_orchestrator_logging.py: one started/terminal на invocation; E4 — другой logger | Целевой |
| AC-30 | Завершённые load и Handler создают соответствующий stage event; отменённая незавершённая стадия его не создаёт. | 1.4, 4.2, 5.2, 5.4 | 4.1/5.3 → 5.4; полный набор 8.1 | test_orchestrator_logging.py: finished vs interrupted stage | Целевой |
| AC-31 | Каждая фактически начатая попытка save создаёт ровно один commit-attempt event с правильным номером; запрещённый retry не создаёт attempt 2. | 1.4, 6.2, 6.4, 7.2 | 6.1/6.3/7.1 → 7.2; аудит 8.1/9.1 | test_orchestrator_logging.py: attempt count = actual save count | Целевой |
| AC-32 | Terminal event пишется после последнего stage/attempt event и до возврата результата либо проброса `CancelledError`. | 3.2–7.2: финализация каждой ветки | 6.1/7.1 → 7.2; полный 8.1/9.1 | test_orchestrator_logging.py: ordered recorder + caller marker | Целевой |
| AC-33 | Compact events и сообщения не содержат birth data и полный session ID. | 1.4, 2.2, 3.2–7.2 | 2.1; по веткам; полный 8.2 | test_orchestrator_logging.py: compact-only sentinel checks; E4 не доказывает новые events | Целевой |
| AC-34 | Клиентский contract test не применяет ответ с версией ниже локальной. | Внешний клиентский срез | За пределами 36 карточек; учёт 10.8 | Планируемый внешний client test: newer response → older response, один lifecycle; файла клиента ещё нет | Внешний; X1 открыт |
| AC-35 | Профиль 1 подтверждает не только приём, но завершение 300 операций и drain. | 3.2–7.2, 10.2; harness 10.6 | 10.6 после core integration | scripts/bench_application_orchestrator.py, профиль normal; existing session benchmark недостаточен | Целевой; admission не нужен |
| AC-36 | Профиль 2 выполняется с конечным admission limit и не превышает одного повтора commit на операцию. | 7.2 и внешний admission; harness 10.7 | 10.7 только после X2 | scripts/bench_application_orchestrator.py, профиль degraded; evidence отсутствует | Внешняя предпосылка; X2 открыт |

### 6.1. Дополнительные требования без нового номера application AC

| Требование | Реализация | Тест / первая полная проверка | Существующее и отсутствующее свидетельство |
|---|---|---|---|
| FR-05: defensive copy, отсутствие runtime registration | 3.2 | 3.1 → 6.4: внешний mapping меняется после создания, routing не меняется; публичного метода регистрации нет | Целевое; нет готового Orchestrator |
| FR-05: полнота registry в composition | 10.2 | 10.1 → 10.2: full registry принят, пропущенный поддерживаемый Command отвергнут до execute | Целевое; mapping exact type не заменяет startup-проверку |
| FR-21 / §11.1: deadline default и UTC | 1.2 | 1.1 → 1.2, `tests/test_run_context.py` | E1 покрывает только прежний started_at |
| FR-21: clock только для решения о retry, срок не обрывает Handler | 7.2 | 7.1 → 7.2; уже истёкший deadline допускает load/Handler/первый save и запрещает второй | Целевое; собственного timeout-result нет |
| Session P3-AC-11, N7 | Готовые CAS/ContextService плюс 6.4 | 10.5: две реальные application операции с одинаковым исходным expected и intent → Committed/AlreadyApplied, общий рост версии +1 | E6 проверяет это ниже application, E7 — store conformance; новый тест связывает весь flow |
| Session P3-AC-12, N8 | Готовые CAS/ContextService плюс 7.2 | 10.4: applied CAS → lost ack → exact retry → AlreadyApplied | E6 проверяет два последовательных save без потери ack; E7 теряет ack create, а не application CAS |

## 7. Как проверять потерянное подтверждение CAS

Сценарий 10.4 является отдельным от простого unit-теста «получены два
StateCommitFailed». Он должен подтверждать persisted state.

1. Собрать реальные Orchestrator, Handler, ContextService и InMemory persistence.
   Создать сессию до измеряемого execute; запомнить исходную версию N.
2. Обернуть только `persistence.sessions.compare_and_set`. Первый реальный
   CAS получает original expected=N и исходную delta и успешно возвращает
   новую версию. После этого wrapper **однократно** бросает
   `SessionPersistenceError` с безопасным synthetic error_code.
   Ошибка до применения CAS не воспроизводит нужный сценарий.
3. Остальные методы wrapper делегируют реальному persistence. Fault-arm и
   журнал вызовов принадлежат экземпляру теста, не глобальному состоянию.
4. Реальный ContextService преобразует исключение в StateCommitFailed.
   Его save нельзя подменять списком заранее придуманных результатов.
5. Orchestrator без повторного Handler/load вызывает save с прежним expected
   и тем же объектом delta; настоящий CAS видит конфликт и реальный
   ContextService возвращает AlreadyApplied.
6. Внешний результат — ApplicationAlreadyApplied с версией N+1. За весь execute
   Handler вызван один раз, save/CAS дважды, touch один раз; третьей попытки нет.
   В журнале две attempt-записи и один terminal.
7. Отдельный read после завершения подтверждает N+1 и рассчитанное намерение.
   Setup и verification reads находятся вне измеряемой последовательности
   execute и не смешиваются с проверкой запрета промежуточного load.

В этом сценарии нет конкурирующего другого intent. Вариант с чужим commit
проверяется отдельно как Superseded, а не ослабляет ожидание AlreadyApplied.

Существующий E7 показывает, как adapter сообщает неизвестный исход после
настоящей записи. Его не нужно переписывать или дублировать в session tests.
10.4 закрывает именно связку Orchestrator → ContextService → повтор CAS.

## 8. Нагрузочная приёмка и внешние срезы

### 8.1. Профиль 1, карточка 10.6

Планируемые новые артефакты:

- `scripts/bench_application_orchestrator.py` — отдельный application harness;
- `docs/project_management/application_orchestrator_load_profile_1.md` — фактический отчёт.

Планируемая CLI-команда (реализовать в 10.6, сейчас её нет):

```powershell
.\.venv\Scripts\python.exe -B scripts/bench_application_orchestrator.py --profile normal --rate 5 --duration 60 --operations 300 --log-level INFO --report docs/project_management/application_orchestrator_load_profile_1.md
```

Стенд собирает реальные application, Handler, ContextService, SQLite,
resolver, artifact/cache и engine; поток HTTP заменён вызовами execute.
В отчёте перечисляются компоненты и все используемые тестовые обёртки.
Session create/setup, настройка эфемерид и прогрев явно отделяются от подачи.
Тестовые данные берутся из уже имеющихся fixtures; executor и database
закрываются после drain.

Отчёт содержит environment/HEAD, команду, submission/finish counts,
распределение outcomes, полезные успешные завершения, времена подачи/завершения
и drain, измеренный throughput, peak active, cache hit/miss и CAS-сценарии.
При недостаточной производительности отчёт фиксирует непрохождение;
300 быстрых infrastructure failures не считаются доказательством полезных 5 RPS.
Порог отдельного latency SLA не изобретается.

Event stream при INFO проверяет started/finished. Отдельные unit/integration
тесты с DEBUG проверяют все промежуточные события; профиль 1 не требует
включения DEBUG. Максимум active считает harness, не Orchestrator.

Измерение dialog: перед прогоном явно задать размер/состав dialog и контрольную
пустую выборку. Зафиксировать долю размера сериализованного dialog в snapshot
и сравнительную оценку времени touch с пустым/заполненным dialog.
Оценку времени назвать оценкой overhead, указать число измерений и разброс:
один общий таймер load не позволяет точно приписать время только dialog.
Обход touch и изменение SessionPersistence этим измерением не разрешаются.

Нормальная подача по таймеру используется для задания RPS; доказательства
порядка, конкуренции и CAS используют Event/barrier. Отсутствие глобального
mutex проверяется 9.2 и допускаемым перекрытием application стадий,
а не одним значением latency или последовательным запуском 300 запросов.
**Admission controller не является зависимостью 10.6.**

### 8.2. Профиль 2, карточка 10.7

X2 пока открыт: нельзя объявить конечную конкурентность доказанной до
появления реального ограничителя внешнего слоя. В allowlist 10.7 входят
только существующий к тому моменту harness и новый отчёт:

- `scripts/bench_application_orchestrator.py`;
- `docs/project_management/application_orchestrator_load_profile_2.md`.

У существующего на дату 0.1 checkout нет файла admission-конфигурации,
поэтому вымышленный путь не добавляется в allowlist. Отдельный внешний срез
должен предоставить компонент и способ передать параметры в harness;
точная ссылка на него фиксируется перед подготовкой промта 10.7.
Если потребуется изменять его production-файлы, это отдельная задача.

Целевой CLI после готовности X2 (параметры стенда, не новые deployment defaults):

```powershell
.\.venv\Scripts\python.exe -B scripts/bench_application_orchestrator.py --profile degraded --rate 5 --duration 60 --operations 300 --log-level INFO --admission-limit 8 --queue-limit 16 --report docs/project_management/application_orchestrator_load_profile_2.md
```

Замедление листовой зависимости управляется Event, освобождение зависит от
зафиксированного состояния стенда. Нужны конечный admission, конечная очередь
и явная реакция overflow; одна Semaphore без ограниченной очереди недостаточна.
Rejected до execute запросы учитываются отдельно: для них нет требования
создать application terminal event, если execute не был начат.
Для принятых операций: один started/terminal, <=2 save и <=1 retry;
attempt event проверяется recording-наблюдением вызовов/событий, а не
предположением из числа запросов. INFO stream сохраняет WARNING retry.
Внутренний DEBUG контракт attempt=1 проверяется отдельными тестами, без
включения полных boundary payload в нагрузочном прогоне.

### 8.3. Клиент и транспорт

AC-34 проверяется на клиенте, когда появится его реализация. Серверные
state_version, Superseded и модельные тесты — предпосылки, но не замена
client contract test. Файл будущего клиента сейчас не придумывается.

Session lifecycle остаётся у входного слоя: create/restore до команды,
trust boundary session_id, HTTP/cookie/status mapping — отдельная работа.
Резервирование Idempotency-Key, BuildAttempt и durable recovery в этот план
не возвращаются.

## 9. Проверка выполнения 0.1

В этом этапе не запускались pytest, collection, нагрузка, сетевые smoke,
рендер PlantUML или runtime-пробы. Никаких результатов прохождения будущих
AC и количества прошедших pytest-тестов документ не утверждает.

Фактически выполнены baseline-команды:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
```

После создания документа выполнены:

```powershell
git diff --check
git diff -- docs/project_management/application_orchestrator_implementation_plan.md
git status --short
```

Дополнительная прямая проверка нового untracked-файла подтвердила: 36 уникальных карточек,
точный набор AC-1–AC-36 и равенство формулировок R3.2, ссылки на существующие
файлы, парность code fences, отсутствие trailing whitespace.
Обычный git diff не показывает содержимое untracked-файла.
Контроль содержимого 399 существующих tracked/untracked файлов по SHA-256
не выявил изменений относительно baseline. Единственное добавление — этот
документ. Проверки ссылок и whitespace прошли; git diff --check завершился
с кодом 0, только с предупреждениями LF/CRLF в ранее изменённых документах.
Пустой git diff для самого плана ожидаем: файл ещё untracked и в index не добавлялся.

**Итог 0.1:** план и трассировка подготовлены. Реализация R3.2 не начата.
Следующий независимый рабочий этап — 1.1, тесты RunContext.deadline.
K3 требует отдельного решения перед завершением соответствующей Handler-ветки;
AC-34 и AC-36 сохраняют внешние зависимости.
