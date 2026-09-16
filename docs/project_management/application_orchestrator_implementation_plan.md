# ApplicationOrchestrator — план реализации и карта приёмки

**Дата исходной сверки:** 2026-09-16, этап 0.1. **Журнал выполнения:** §1.3, обновлён 2026-09-16.
**Контракт:** R3.2. **Рабочие этапы:** 36 основных промтов в 10 группах и дополнительная карточка 1.R1; номера основных карточек сохранены.
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

#### 1.3.1. Статусы на 2026-09-16

| Этап | Статус | Граница подтверждения |
|---|---|---|
| 0.1 | Выполнен | Исходная сверка и план; тесты в этом этапе не запускались |
| 1.1 | Тесты deadline написаны; проверены после 1.2 | До реализации было содержательное падение, после реализации новые и прежние случаи прошли |
| 1.2 | Выполнен | Поле/default/UTC-валидация deadline; application retry и AC-14 этим не закрыты |
| 1.3 | Тесты logging написаны; исполняемая проверка отложена | AST проверен, но L останавливается на импорте отсутствующего operation_logging.py; assertions не исполнялись |
| 1.R1 | Выполнен | Независимые тестовые константы, четыре новых UTC-случая started_at, docstring и журнал; production-код не менялся |
| Остальные основные карточки, включая 1.4 | Запланированы, не выполнялись | Формулировка «закрывает» в карточке означает будущую обязанность |

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

После завершения 1.3–1.4, до группы 3, требуется подготовить отдельный срез
неизменяемости RunContext: явно закрепить требование и проверить присваивание
полям. Это follow-up, не уже принятое/реализованное требование frozen.
Политика неизвестных полей (`extra`) остаётся отдельным решением.

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
