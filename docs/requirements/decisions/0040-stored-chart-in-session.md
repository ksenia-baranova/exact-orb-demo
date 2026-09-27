# ADR-0040. Построенная карта хранится в агрегате сессии

Дата: 2026-09-26.
**Статус: принято; компонентная реализация M1-5.2 выполнена в ветке
`feat/session-stored-chart` 2026-09-27; HTTP bootstrap остаётся M1-6.**

Частично изменяет ADR-0017: источником показа уже построенной карты после
возврата пользователя становится сохранённый артефакт, а не повторный расчёт
по `ChartSpec`. Дополняет ADR-0009 и ADR-0024 третьей записью агрегата сессии.
Устанавливает узкое исключение из ADR-0025/0028/0037 для бинарного payload
`StoredChart` в DEBUG-сообщениях. ADR-0006, ADR-0012, ADR-0014 и ADR-0027
сохраняют свои решения о bootstrap, подтверждённом commit, CAS и проверках
идентичности.

## Контекст

На момент принятия решения `SessionState` хранил введённые и разрешённые
данные рождения и `ChartRef { state_version, spec }`, но не построенную карту.
Расчётный кэш живёт в памяти процесса и пуст после рестарта. Поэтому
возврат пользователя с живой cookie потребовал бы нового обращения к
расчётному пути; обновление `CalculationVersion`, эфемерид или `tzdata`
могло бы изменить показанную карту без действия пользователя. Открытие
страницы также зависело бы от доступности
движка и слота расчёта.

ADR-0017 отверг отдельный `ChartRepository`: самостоятельное хранилище
производных персональных данных потребовало бы своего срока жизни и удаления.
Здесь такого хранилища нет. ADR-0027 уже различает опасные независимые
источники истины и проверяемые технические копии разных контекстов.

## Решение

**Сохранённая карта — факт подтверждённого построения.** Пока сессия жива,
повторное открытие показывает именно этот результат. `birth_resolved` и
`base_chart.spec` остаются источником расчётного намерения, проверки
согласованности и явного нового построения. `Calculation Cache` остаётся
удаляемой копией для ускорения; его eviction не влияет на восстановление.

`SessionState` не раздувается полным артефактом. В агрегате сессии рядом с
родительской записью состояния и записью диалога хранится одна дочерняя
запись `session_charts` с `StoredChart`:

```text
StoredChart {
    payload_format: int
    calculation_key: str
    calculation_version: str
    payload: bytes
}

SessionSnapshot { state: SessionState, dialog: tuple[DialogTurn, ...],
                  chart: StoredChart | None }
```

`payload` — gzip JSON `ChartArtifact` текущего строгого кодека. Сессионный
слой считает байты непрозрачными и не импортирует модели или кодек расчёта.
Начальный `payload_format` равен 1; длина сжатого payload — от 1 байта до
1 МиБ. Этот формат независим от версии `state_json`, которая остаётся 2.
`StoredChart` не имеет отдельного TTL: живость определяется родительским
`SessionState`. SQLite использует внешний ключ на `session_states` с
`ON DELETE CASCADE`; InMemory обеспечивает то же поведение под общим lock.

`StateDelta` получает обязательное nullable-поле `base_chart_payload`.
`birth_input`, `birth_resolved`, `base_chart_spec` и `base_chart_payload`
задаются все вместе либо все равны `None`. Снимок соблюдает инвариант
`state.base_chart is None` тогда и только тогда, когда `chart is None`.
Сравнение намерения при CAS по-прежнему использует `birth_resolved` и spec,
а не байты карты.

`BuildNatalHandler` после `ChartArtifactPort.ensure_chart` получает пару
`(payload_format, payload)` через новый `ChartArtifactPort.to_stored(artifact)`
и собирает `StoredChart` с ключом и версией из артефакта. Форматом владеет
`ChartArtifactResolver`; для того же артефакта метод детерминированно выдаёт
те же байты, что кодек расчётного кэша. Handler не импортирует кодек напрямую.
`BuildNatalSuccess` проверяет равенство ключа и версии артефакта и
`StoredChart` вместе с действующими инвариантами входа и spec. Отказ
кодирования или превышение лимита — внутренняя ошибка до вызова CAS.

Подтверждённый `Committed` записывает состояние и карту одной CAS-транзакцией.
Конфликт версий не меняет ни одну запись; `AlreadyApplied` не выполняет новую
запись. `RESET_DELTA` в том же CAS удаляет карту и диалог вместе со сбросом
состояния. Aggregate `delete` и reaper удаляют карту вместе с родительской
сессией. Если commit не подтвердился, `StateCommitFailed` не доказывает
отсутствие записи: фактически могли сохраниться обе записи или ни одна.
Точный retry передаёт ту же дельту и исходную expected version, без rebase.

`ContextService.load` возвращает карту внутри согласованного
`SessionSnapshot` одним обязательным read-and-renew. При чтении не вызываются
движок, `ChartArtifactResolver` и расчётный кэш; `state_version` не меняется.
Application без I/O собирает внутреннее представление сессии из snapshot и
текущей `CalculationVersion`. Сначала проверяется `payload_format`, затем строгий
decode и равенство ключа, версии, spec и расчётного входа состоянию. Ключ
проверяется по **сохранённой** версии расчёта; сравнение с текущей версией
делается только после проверки целостности и задаёт `chart_stale`.

`application/session_view` — чистая проекция уже полученного
`SessionSnapshot` и переданной текущей `CalculationVersion`. Она не загружает
сессию, не выбирает handler, не вызывает `ChartArtifactResolver`, кэш или
движок, не сохраняет состояние и не выполняет I/O. При bootstrap транспорт
по-прежнему делает только create/restore через `ContextService` по ADR-0006,
а затем использует эту проекцию для сборки ответа. Проекция не является
самостоятельным application use case или вторым координатором и не открывает
транспорту доступ к расчётному домену. Если восстановление потребует вызова
resolver или иной координации, для такого пути понадобится отдельное
архитектурное решение; исключение ADR-0006 на него не распространяется.

- Пустое состояние даёт `empty`.
- Корректная карта даёт `chart_ready`. Различие сохранённой и текущей
  `CalculationVersion` даёт `chart_stale = true`, но не запускает пересчёт.
- Неподдерживаемый формат, нечитаемый payload или нарушение предметных
  инвариантов дают `chart_unavailable` с сохранёнными `birth_input` и
  `canonical_place`. Содержимое состояния, его версия и cookie не меняются;
  обязательный `touch` при этом мог продлить TTL. Безопасная причина
  фиксируется на ERROR без бинарного payload и данных рождения.
- Отказ обязательного `touch` или структурно несогласованный persistence
  snapshot остаётся `StateReadFailed`; он не заменяется пустой сессией или
  `chart_unavailable`.

DEBUG-проекции границ, содержащие `StoredChart`, выводят только ключ, версию,
формат и размер payload, без самих байтов. Это исключение относится к
storage envelope, а не отменяет действующие полные DEBUG-сообщения о
`ChartArtifact` на расчётных границах. Новый прямой вызов handler →
`to_stored` виден как парные компактные INFO-события с `run_id`, адресатом,
операцией и исходом.

До первого публичного развёртывания новая компонентная миграция SQLite
создаёт `session_charts` и в той же транзакции удаляет существующие сессии:
их построенные карты восстановить из самого session storage нельзя.
Диалоги удаляются каскадом, другие компоненты базы не затрагиваются.
Неуспешная миграция откатывается целиком. Это последняя миграция сессий,
которой разрешена потеря данных; после M1-13 миграции обязаны их сохранять.

## Альтернативы

- Повторный `BuildNatal` при открытии страницы изменял бы `state_version`,
  снова разрешал место и время и расходовал бы лимит построений.
- Вызов resolver из `ContextService` смешал бы хранение с расчётом и создал
  зависимость session → calculation. Прямой вызов resolver транспортом
  добавил бы второго координатора восстановления.
- Отдельный `GET /charts/current` требовал бы второго запроса и сверки
  версий на клиенте, сохраняя зависимость открытия страницы от движка.
- Самостоятельный `ChartRepository` сохранил бы проблему отдельного
  жизненного цикла и удаления из ADR-0017.

## Последствия и границы

Построенная карта переживает рестарт процесса при живой SQLite-сессии и
пустом расчётном кэше. За это платим одной ограниченной BLOB-записью на
сессию, проверкой формата/целостности и миграцией. Несовместимое изменение
модели `ChartArtifact` требует поднять `payload_format`; декодеры старых
форматов в MVP не поддерживаются. Такая карта становится недоступной, а
пользователь может построить её заново явным действием.

`AlreadyApplied` сохраняет прежний application-контракт: результат содержит
артефакт этого handler, а сохранённой остаётся карта ранее подтверждённой
операции. При одновременной работе процессов с разными
`CalculationVersion` эти артефакты могут различаться. Согласование ответа с
persisted-победителем перед смешанным развёртыванием требует отдельного
решения; настоящее ADR не утверждает их байтовое равенство.

В этой ветке не определяются URL, cookie, публичный `ChartDTO`, admission и
UI. HTTP bootstrap в M1-6 использует готовый сборщик представления; состав
публичного ответа остаётся отдельным контрактом транспорта.

Отложенный M2-путь `ensure_natal` при интерпретации сейчас нарисован как
повторное получение карты по spec. После смены `CalculationVersion` он мог бы
интерпретировать результат, отличный от показанного `StoredChart`. Перед M2
нужно отдельно согласовать источник артефакта для интерпретации; ADR-0040
утверждает только build, хранение и восстановление карты для показа.

Компонентная реализация подтверждена следующими проверками; HTTP bootstrap
остаётся задачей M1-6. Подробные команды и результаты приведены в
[журнале плана M1-5.2](../../project_management/implementation_plans/session_stored_chart_implementation_plan.md#8-статус-журнал-свидетельств-и-передача-в-m1-6):

- общий session conformance для InMemory и SQLite: атомарный CAS state+chart,
  конфликт без записи chart, reset/delete/reaper и согласованный touch —
  `tests/session/conformance.py::test_populated_cas_commits_version_and_chart_reference`,
  `test_cas_conflict_returns_atomic_actual_without_mutation`,
  `test_already_applied_keeps_first_committed_chart`,
  `test_touch_returns_consistent_renewed_snapshot`,
  `test_direct_reset_delta_clears_state_and_dialog`,
  `test_delete_is_idempotent_for_missing_and_live_or_expired` и
  `tests/session/test_sqlite.py::test_reaper_deletes_only_expired_parents_at_exact_boundary`;
- неподтверждённый commit: обе записи появляются вместе или обе отсутствуют;
  точный retry с original expected сохраняет прежнюю классификацию —
  `tests/session/test_sqlite.py::test_chart_write_failure_rolls_back_parent_and_retry_commits_pair`
  и `test_lost_chart_commit_acknowledgement_preserves_pair_and_retry_winner`;
- миграция удаляет прежние сессии и откатывается целиком при отказе —
  `tests/session/test_sqlite.py::test_v1_to_v2_clears_legacy_sessions_and_preserves_foreign_component`
  и `test_v2_migration_failure_after_delete_rolls_back_every_change`;
- build → закрытие runtime → новый runtime с пустым кэшем → чтение той же
  карты без вызова движка и без cache miss; различие версии даёт `chart_stale` —
  `tests/application/test_application_bootstrap_integration.py::test_runtime_restart_restores_identical_chart_without_calculation`;
- неподдерживаемый формат и повреждённый payload дают `chart_unavailable`
  без мутации содержимого; отказ touch остаётся `StateReadFailed` —
  `tests/application/test_session_view.py::test_unsupported_format_precedes_decode_and_preserves_snapshot`,
  `test_first_failed_check_wins_before_staleness` и
  `tests/session/test_sqlite.py::test_structural_chart_corruption_blocks_touch_and_context_load`;
- DEBUG-проекции `StoredChart` не содержат payload, а прямой вызов
  `to_stored` виден в парных INFO-событиях —
  `tests/session/test_context.py::test_context_save_debug_input_redacts_stored_chart`
  и `tests/application/test_build_natal_logging.py::test_started_is_debug_and_precedes_exactly_one_terminal_event`,
  `test_handler_logs_complete_input_and_output_component_messages`.
