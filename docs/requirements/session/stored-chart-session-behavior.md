# Поведение сессии с сохранённой картой — M1-5.2

Дата: 2026-09-26. Ревизия: 2026-09-27.
**Статус: компонентный контракт M1-5.2 реализован и проверен 2026-09-27;
HTTP bootstrap и транспорт остаются M1-6.**

Нормативное решение — [ADR-0041](../decisions/0041-stored-chart-in-session.md).
Действующий контракт жизненного цикла, TTL и CAS —
[требования к блоку сессии](../component_responsibilities/exact-orb_session_requirements.md).
Настоящий документ уточняет пользовательское поведение первой ветки
`feat/session-stored-chart`. HTTP-реализация bootstrap относится к следующей
ветке M1-6; ниже для неё задан внутренний контракт с готовыми компонентами.
Существующий код хранит `StoredChart` рядом с `SessionState` и `ChartRef`;
чистая проекция `application/session_view` восстанавливает его из snapshot.

## 1. Что делаем и зачем

После подтверждённого построения натальной карты сохраняем её полный
`ChartArtifact` в агрегате анонимной сессии как `StoredChart`. При повторном
открытии вкладки возвращаем сохранённую карту, даже если процесс перезапущен
и расчётный кэш пуст. Открытие страницы не должно заново разрешать место и
время рождения или вызывать расчётный движок. Пользователь видит результат
того построения, которое было подтверждено записью в сессию.

«Сессионный контекст» здесь означает согласованный агрегат
`SessionState + DialogTurn[] + StoredChart?`, а не новую сохраняемую сущность
или отдельный сервис. Сессия создаётся **при первом bootstrap до ввода
данных**. Успешное построение заполняет уже созданную сессию; неудачная
первая попытка не создаёт частичный контекст с данными рождения.

## 2. Функциональные требования

| ID | Требование |
|---|---|
| S-01 | Доверенный transport генерирует `session_id`; при отсутствии живой сессии `ContextService.create` создаёт пустой `SessionState` с `state_version=0`, без данных рождения, `base_chart`, диалога и `StoredChart`. `session_id` из body/query/path не принимается. |
| S-02 | Срок жизни состояния: sliding TTL 7 суток с абсолютным пределом 30 суток от создания. Закрытие вкладки не удаляет сессию. `StoredChart` не имеет собственного TTL и удаляется с родителем. |
| S-03 | `ContextService.load` выполняет обязательный атомарный read-and-renew и возвращает `SessionSnapshot {state, dialog, chart}` одной согласованной версии. Успешный load может продлить TTL, но не меняет `state_version` и предметное содержимое. |
| S-04 | Восстановление карты использует только сохранённый snapshot и текущую `CalculationVersion`: без `BirthDataResolver`, `ChartArtifactResolver`, расчётного кэша и движка. `application/session_view` — чистая проекция без I/O и второй координации. |
| S-05 | Успешный `BuildNatalHandler` получает артефакт, вызывает `ChartArtifactPort.to_stored(artifact)`, формирует `StoredChart` и полную `StateDelta`. Только `Committed` одной CAS-операции делает вместе текущими состояние и карту и увеличивает `state_version`. До подтверждения commit клиент не заменяет прежнюю карту новым результатом. |
| S-06 | Четыре поля `StateDelta` — `birth_input`, `birth_resolved`, `base_chart_spec`, `base_chart_payload` — все заполнены либо все `None`. В snapshot выполняется `state.base_chart is None` ⇔ `chart is None`. Отказ resolve, расчёта, кодирования или проверки `StoredChart` до CAS не записывает ни ввод, ни карту. |
| S-07 | `AlreadyApplied` не делает новой записи. `Superseded` не применяет проигравшую дельту. `StateCommitFailed` означает неопределённый исход. Только внутренний retry save в том же `execute` использует ту же delta и original expected. Новый HTTP POST создаёт новый `execute`, делает fresh load и может увеличить version ещё раз; клиент сначала вызывает `GET /charts/current` и повторяет POST только явно, если нужная карта не сохранена. |
| S-08 | Корректная сохранённая карта даёт `chart_ready`. Различие её `calculation_version` и текущей версии даёт `chart_stale=true`, но не пересчитывает карту. Строгий декодер проверяет внутреннюю идентичность артефакта по сохранённой версии; затем проекция сверяет ключ и версию с `StoredChart`, spec и расчётный вход — с состоянием. |
| S-09 | Неподдерживаемый формат, нечитаемый payload или нарушение предметных инвариантов артефакта дают `chart_unavailable` с кодом `safe_reason`: прежние `birth_input` и `canonical_place` доступны для явного нового построения, содержимое сессии не меняется. Если `base_chart` есть без строки карты или строка карты есть без `base_chart`, SQLite-адаптер возвращает `StateReadError(SESSION_SQLITE_DATA_CORRUPT)`; `ContextService.load` переводит его в `StateReadFailed`. Отказ обязательного touch также даёт `StateReadFailed`. Ни один из этих случаев не создаёт пустую сессию. |
| S-10 | Все вкладки с одной cookie обращаются к одной серверной сессии. Если вкладка B успешно перестроила карту, вкладка A получает новую карту при следующем bootstrap/явной загрузке. Автоматической доставки изменения в A нет. Новая команда A читает актуальную серверную версию в начале команды; версия, ранее показанная в A, не передаётся как CAS-precondition. Поэтому явный build из необновлённой A может затем сохранить ещё одну версию поверх результата B. |
| S-11 | `RESET_DELTA` очищает состояние, карту и диалог в одной backend-секции. `delete` и reaper удаляют дочернюю карту вместе с сессией. Пустая живая сессия возвращает `empty`, независимо от того, создана она впервые или очищена reset. |
| S-12 | SQLite-миграция session component v2 создаёт `session_charts` и в той же транзакции удаляет **все** существующие сессии: до миграции ни одна из них не содержит сохранённую карту. Другие компоненты базы не затрагиваются; при отказе миграция целиком откатывается. `state_json.payload_version` остаётся 2. |

## 3. Какие компоненты разрабатываем

| Компонент | Работа в M1-5.2 | Граница ответственности |
|---|---|---|
| `session` contracts | `StoredChart`, поле `SessionSnapshot.chart`, поле `StateDelta.base_chart_payload` и инварианты полного обновления | Сессионный слой хранит `payload: bytes` как непрозрачное значение; не импортирует кодек и модели расчёта. |
| `SessionPersistence`, `SessionStore`, InMemory и SQLite adapters | Атомарные touch/snapshot и CAS state+chart; общий lifecycle reset/delete/reaper; SQLite-миграция | Согласованность и TTL принадлежат одному session aggregate. |
| `ChartArtifactPort` / `ChartArtifactResolver` | `to_stored(artifact) -> (payload_format, payload)` в build; типизированный `ChartArtifactEncodingError` | Resolver владеет кодированием и детерминированно выдаёт те же gzip JSON байты, что кодек расчётного кэша. Он не импортирует `StoredChart`, не проверяет сессионный лимит размера и не пишет в session storage. Ошибка кодирования принадлежит артефактному слою; объект resolver при bootstrap не вызывается. |
| Кодек артефакта | Хранит начальный формат `1`, набор поддерживаемых `payload_format` и строгий decode для `session_view`; используется `to_stored` | Константы формата расположены рядом с кодеком, например в `exact_orb.calculation.codec`, и не дублируются в проекции. Сессионная модель проверяет положительное значение формата, но не решает, поддерживается ли он текущим кодом. |
| `BuildNatalHandler` и `BuildNatalSuccess` | Сборка `StoredChart`, полной дельты и проверка идентичности артефакта/дельты до CAS; внутренняя ошибка `StoredChartPreparationError` | Handler вызывает resolver и порт артефакта за `ApplicationOrchestrator`. Ошибка подготовки принадлежит application-границе. Модель `StoredChart` первой проверяет размер payload 1…1 048 576 байт; SQL `CHECK` защищает хранилище дополнительно. |
| `application/session_view` | Чистое формирование `empty`, `chart_ready` или `chart_unavailable` из snapshot и текущей версии расчёта | Проекция не загружает сессию, не вызывает resolver и не сохраняет состояние. |
| `ApplicationRuntime` | Предоставляет составленные зависимости и фактическую `CalculationVersion` вызывающему коду | В M1-6 transport использует этот runtime, не создавая второй расчётный контур. |
| Доверенный transport M1-6 | Позже соединяет cookie, `ContextService.create/load` и `session_view` | URL, middleware и публичный DTO разрабатываются во второй ветке; в M1-5.2 проверяется компонентный контракт. |

Граница прямых импортов `application/session_view` закрепляется в
`tests/test_module_boundaries.py` с положительным контролем разрешённых
зависимостей. Для проекции допустимы контракты `SessionSnapshot`/состояния,
`calculation.codec`, `calculation.keys`, `calculation.chart_contract`,
`calculation.types` и типы birth. `calculation.types` транзитивно загружает
модели движка и нативный расчётный стек; этот импорт разрешён. Здесь
«чистая проекция» означает отсутствие I/O и вызовов расчётных компонентов,
а тест границ проверяет именно прямые импорты. Запрещены прямые импорты
`calculation.artifacts`, `calculation.cache`, `calculation.engine`,
`birth.resolver`, `session.context`, `session.adapters`, `session.store`,
`engine`, `swiss_backend` и transport. Отдельный поведенческий тест проверяет,
что restore после рестарта не вызывает resolver, кэш и движок: запрет
импортов сам по себе не доказывает отсутствие I/O.

## 4. Компонентный контракт bootstrap/restore

Вход будущего bootstrap: опциональный непрозрачный `session_id`, полученный
**только из доверенной cookie**, и текущая `CalculationVersion`, переданная
в чистую проекцию. Transport не обращается к доменному resolver. Построение
карты остаётся типизированной командой через `ApplicationOrchestrator`.

| Условие | Вызовы компонентов | Внутренний результат и действие transport |
|---|---|---|
| Cookie отсутствует | Сгенерировать новый ID → `ContextService.create(new_id)` | `SessionCreated(state_version=0)` → пустая форма, новая cookie. При `SessionIdConflict` сгенерировать другой ID; чужую запись не загружать и не перезаписывать. |
| Cookie указывает на живую сессию | `ContextService.load(id)` → `SessionSnapshot` → `application/session_view(snapshot, current_version)` | `empty`, `chart_ready` или `chart_unavailable`; cookie сохраняется. Для ready передать артефакт, данные для заполнения формы, `state_version`, `chart_stale`. |
| Cookie указывает на отсутствующую или истёкшую сессию | `load(id)` → `SessionAbsent(reason=not_found\|expired)` → новый ID → `create(new_id)` | Удалить старую cookie, выдать новую, показать пустую форму. Старый ID не переиспользовать. |
| Обязательный read-and-renew не завершился | `load(id)` → `StateReadFailed(error_code)` | Ошибка восстановления; cookie не стирать и новую сессию не создавать. |
| Создание не завершилось | `create(new_id)` → `StateCommitFailed(error_code)` | Ошибка bootstrap; не утверждать, что сессия создана, и не выдавать её как готовую. |

`SessionCreated` уже содержит пустое состояние; отдельное чтение после create
не требуется. `SessionSnapshot` содержит frozen state, dialog и chart.
Чистая проекция проверяет сохранённую карту и возвращает один из внутренних
вариантов:

| Вариант | Обязательные сведения | Условие |
|---|---|---|
| `empty` | `state_version` | `base_chart=None` и `chart=None`. |
| `chart_ready` | `state_version`, `birth_input`, `canonical_place`, `artifact`, `chart_stale` | Сохранённый артефакт целостен; `chart_stale` — результат сравнения версий после проверки. |
| `chart_unavailable` | `state_version`, `birth_input`, `canonical_place`, безопасная причина | Запись карты есть, но формат или артефакт нельзя принять; пользователь может явно построить заново. |

`safe_reason` — внутренний фиксированный код, без payload и персональных данных.
Его значения и порядок определения:

1. `UNSUPPORTED_PAYLOAD_FORMAT` — формат отсутствует в наборе поддерживаемых
   форматов кодека.
2. `DECODE_GZIP_FAILED`, `DECODE_UTF8_FAILED`, `DECODE_VALIDATION_FAILED` —
   соответствующие причины строгого декодера. Валидация `ChartArtifact`
   проверяет, что его ключ вычисляется из собственной карты, spec и
   собственной версии; нарушение этого инварианта даёт
   `DECODE_VALIDATION_FAILED`.
3. `CALCULATION_KEY_MISMATCH` или `CALCULATION_VERSION_MISMATCH` — декодированный
   артефакт не совпал с одноимёнными полями `StoredChart`.
4. `SPEC_MISMATCH` или `CALCULATION_INPUT_MISMATCH` — spec или расчётный вход
   артефакта не совпал с `state.base_chart.spec` или проекцией
   `state.birth_resolved`.

При нескольких нарушениях возвращается причина первой неуспешной проверки
в указанном порядке; внутри пунктов 3 и 4 сначала проверяются ключ и spec.
Повторное вычисление ключа из состояния после пунктов 2–4 не требуется:
равенство уже следует из проверенных инвариантов.
После этих проверок сравнение с текущей `CalculationVersion` задаёт только
`chart_stale`; оно не даёт `chart_unavailable`. Неверная форма самого
`StoredChart` или отсутствие одной из двух частей snapshot — ошибка чтения
агрегата, а не одна из причин `chart_unavailable`. Проекция возвращает код
вызывающему слою без записи в журнал. Публичность и представление этого кода
в HTTP описаны проектом требований [M1-6 HTTP API](../http_api.md) и вступают
в силу после review и approval.

Состав публичного `SessionViewDTO`, URL и HTTP-коды предложены в
[требованиях M1-6](../http_api.md); component-контракт этого документа не
меняется до принятия анализа. По ADR-0040 bootstrap возвращает только
liveness/version, а `GET /charts/current` вызывает эту проекцию. Оба пути
не выполняют CAS, не меняют `state_version` и не запускают build.

## 5. Пользовательские сценарии и sequence

1. **Первый вход, вкладка открыта впервые.** Cookie нет. Bootstrap создаёт
   пустую сессию версии 0 и показывает форму. Карты и данных рождения нет.
   Sequence: [001 — создание и первая карта](../../sequence_diagrams/session/001-natal-session-lifecycle.puml).
2. **Ввод данных и успешное построение.** `BuildNatalCommand` проходит через
   Orchestrator, Handler разрешает ввод и получает артефакт; CAS одной
   операцией сохраняет ввод, разрешённые данные, ссылку и карту. Только после
   `Committed` клиент показывает карту и получает версию 1.
   Sequence: [001 — первая карта](../../sequence_diagrams/session/001-natal-session-lifecycle.puml).
3. **Закрытие после расчёта и повторный вход с той же cookie.** Живая сессия
   читается вместе с картой и TTL продлевается. Даже после рестарта с пустым
   кэшем карта берётся из session storage. Смена версии расчёта обозначается
   `chart_stale`, не запускает пересчёт.
   Sequence: [002 — восстановление](../../sequence_diagrams/session/002-session-restore-on-return.puml).
4. **Две вкладки одной сессии, перестроение во второй.** Обе могут сначала
   показать версию N. Вкладка B строит карту; её команда читает актуальную
   серверную версию и после `Committed` сохраняет N+1. Вкладка A продолжает
   локально показывать N до собственного bootstrap/явного обновления, затем
   получает N+1. Если две команды построения действительно пересеклись и
   обе прочитали N, исход определяет CAS: одна дельта записывается, другая
   получает `Superseded` или `AlreadyApplied` по намерению.
   Если A без обновления явно запускает новый build позже B, её команда
   начинает с серверной N+1 и может записать N+2.
   Sequence: [006 — две вкладки](../../sequence_diagrams/session/006-two-tabs-rebuild-and-restore.puml),
   [005 — CAS](../../sequence_diagrams/session/005-compare-and-set.puml).
5. **Повторный вход в живую сессию без карты.** Так бывает до первого
   успешного build или после reset. Snapshot содержит пустое состояние и
   `chart=None`; bootstrap возвращает `empty` и форму ввода, не вызывает
   расчёт. После reset версия может быть больше нуля.
   Sequence: [002 — ветка empty](../../sequence_diagrams/session/002-session-restore-on-return.puml),
   [004 — reset](../../sequence_diagrams/session/004-session-reset-and-delete.puml).
6. **Первое построение не удалось до CAS.** Ошибка валидации/разрешения,
   расчёта или `to_stored` не вызывает `save`. Созданная при bootstrap
   сессия остаётся пустой версии 0: `birth_input=None`,
   `birth_resolved=None`, `base_chart=None`, `chart=None`, диалог пуст.
   Текущий текст формы может оставаться только в открытой вкладке.
   Sequence: [007 — отказ и возврат](../../sequence_diagrams/session/007-first-build-fails-then-return.puml),
   [BuildNatal 005 — технические отказы](../../sequence_diagrams/build_natal/005-build_natal_technical_failures.puml).
7. **Повторный вход после сценария 6.** Load возвращает пустую живую сессию;
   форма снова просит ввести данные. Сервер не восстанавливает неуспешный
   ввод. Если исход был `StateCommitFailed` после вызова CAS, это уже иной
   случай: запись могла состояться, поэтому следующий вход обязан читать
   фактический snapshot и может показать карту.
   Sequence: [007 — отказ и возврат](../../sequence_diagrams/session/007-first-build-fails-then-return.puml),
   [003 — неопределённый commit](../../sequence_diagrams/session/003-session-store-read-failure.puml).

## 6. Что не делаем в M1-5.2

- Не реализуем FastAPI, cookie middleware, URL, HTTP DTO, admission и UI:
  это M1-6/M1-7. Сценарии описывают поведение, которому эти слои должны
  соответствовать позднее.
- Не сохраняем черновик формы и неуспешный ввод в сессии; не восстанавливаем
  его после закрытия вкладки.
- Не добавляем push-синхронизацию вкладок и клиентский
  `expected_state_version` для предотвращения последовательной перезаписи.
- Не согласуем артефакт ответа `AlreadyApplied` с артефактом ранее
  подтверждённой записи при одновременной работе процессов с разными
  `CalculationVersion`; этот риск ADR-0041 оставляет отдельным решением до
  смешанного развёртывания.
- Не создаём отдельный `ChartRepository`, отдельный TTL карты, сервис
  bootstrap-координации или путь к resolver из transport/`ContextService`.
- Не меняем M2-интерпретацию, диалоговый tool, derived charts и транзиты.
  Источник артефакта интерпретации после смены `CalculationVersion` требует
  отдельного решения до M2.
- Не вводим декодеры прежних `payload_format`: несовместимую карту показываем
  как `chart_unavailable` до явного нового построения.

## 7. Входные и выходные сообщения компонентов

Имена `Context*Request` и `ToStoredRequest` ниже служат для типизированной
диагностической проекции вызова; они не требуют новых публичных DTO. Внутренние
варианты `SessionView` также не предрешают HTTP-схему.

| Переход | Вход: сообщение и атрибуты | Выход: сообщение и атрибуты |
|---|---|---|
| transport → `ContextService.create` | `ContextCreateRequest {session_id}` — новый серверный ID | `SessionCreated {state}` с пустой версией 0; либо `SessionIdConflict {session_id}`, `StateCommitFailed {error_code}`. |
| transport/Orchestrator → `ContextService.load` | `ContextLoadRequest {session_id}` | `SessionSnapshot {state: SessionState, dialog: tuple[DialogTurn,...], chart: StoredChart\|None}`; либо `SessionAbsent {reason}`, `StateReadFailed {error_code}`. |
| transport → `application/session_view` | `SessionViewRequest {snapshot, current_calculation_version}` | `empty {state_version}`; `chart_ready {state_version, birth_input, canonical_place, artifact, chart_stale}`; `chart_unavailable {state_version, birth_input, canonical_place, safe_reason}`. Не вызывает I/O. |
| transport → `ApplicationOrchestrator` | `BuildNatalCommand {birth_input: BirthInput}` + отдельно доверенные `session_id`, `RunContext {run_id, started_at, deadline?}` | `ApplicationCommitted` / `ApplicationAlreadyApplied {run_id, state_version, artifact, statuses, code}`; `ApplicationSuperseded {run_id, state_version, code}`; `ApplicationInputRequired {run_id, state_version, issues}` или технический `Application*Failure {run_id, code, detail_code?, retryable}`. Текущие application outcomes сохраняются. |
| Orchestrator → `BuildNatalHandler` | `BuildNatalRequest {command, state, run}` | `BuildNatalSuccess {artifact, delta}`; либо `InputRequired`, `ResolutionUnavailable`, `CalculationFailed` / `StoredChartPreparationError` до CAS. Последний переводится Orchestrator в `ApplicationInternalFailure`. |
| Handler → `BirthDataResolver` | `BirthResolutionRequest {birth_input, run}` | `ResolvedBirthData` либо `InputRequired` / `ResolutionUnavailable`. |
| Handler → `ChartArtifactPort.ensure_chart` | `EnsureChartRequest {spec, resolved, run}` | `ChartArtifact {spec, calculation_key, calculation_version, chart}` либо типизированная ошибка расчёта. |
| Handler → `ChartArtifactPort.to_stored` | `ToStoredRequest {artifact}` | `(payload_format=1, payload: bytes)` либо `ChartArtifactEncodingError {error_code=CHART_ARTIFACT_ENCODE_FAILED, cause_type}` для ожидаемого отказа сериализации. Неожиданное исключение порта Handler классифицирует как `ENCODE_UNEXPECTED`. Лимит размера этот метод не проверяет. |
| Handler → Orchestrator → `ContextService.save` | `ContextSaveRequest {session_id, expected_state_version, delta}`; `StateDelta {birth_input, birth_resolved, base_chart_spec, base_chart_payload: StoredChart}` | `Committed {state_version}`; `AlreadyApplied {state_version}`; `Superseded {actual: SessionState}`; `SessionAbsent {reason}`; `StateCommitFailed {error_code}`. |

`StoredChart {payload_format:int, calculation_key:str, calculation_version:str,
payload:bytes}` содержит ключ и версию из того же `ChartArtifact`. Размер
`payload` — 1…1 048 576 байт. `SessionState` содержит `session_id`,
`state_version`, `birth_input?`, `birth_resolved?`, `base_chart?`,
`created_at`, `expires_at`, `hard_expires_at`. При успешном CAS
`base_chart.state_version` равен новой версии состояния. Бинарный payload
никогда не передаётся как публичный ответ bootstrap.

`to_stored` переводит ожидаемый отказ сериализации в типизированный
`ChartArtifactEncodingError` с безопасным именем исходного типа
`cause_type`, не раскрывая байты или исходный текст ошибки наружу. Другие
исключения resolver не маскирует. Handler переводит типизированный отказ в
`StoredChartPreparationError {reason=ENCODE_FAILED, cause_type}`, а другое
`Exception` из порта — в `{reason=ENCODE_UNEXPECTED, cause_type}`. `MemoryError`
и `BaseException` вне `Exception` не классифицируются. Отказ валидации
создаваемого `StoredChart`/`StateDelta` даёт `ENVELOPE_INVALID`;
`ValidationError` при сборке `BuildNatalSuccess` сохраняет исходный тип и
`stage=build_result` согласно ADR-0027. `PAYLOAD_SIZE_INVALID`
относится к сжатым байтам вне диапазона 1…1 048 576; положительность
`payload_format` и непустые ключ/версия относятся к `ENVELOPE_INVALID`.
Основная проверка лимита выполняется моделью `StoredChart` при сборке
дельты; SQL `CHECK` — защита при записи. Resolver не делает отдельную
проверку этого сессионного лимита. `StoredChartPreparationError` возникает
**до** `ContextService.save`. Действующий Orchestrator переводит исключение
Handler в `ApplicationInternalFailure {orch_status=FAILURE,
handler_status=UNEXPECTED_FAILURE, context_status=LOADED,
code=INTERNAL_FAILURE}` без вызова CAS и без нового публичного outcome.
Причина подготовки остаётся во внутренней диагностике и не становится
публичным текстом ошибки. Текст типизированных исключений содержит только
безопасный код/причину и `cause_type` для двух отказов кодирования. При
преобразовании ошибок сериализации и валидации исходное исключение не
включается в поля или текст новой ошибки;
цепочка в форматируемом traceback подавляется (`raise ... from None`). Это
необходимо и для `StoredChartPreparationError`: Orchestrator журналирует
отказ Handler через `logger.exception`, а исходный Pydantic
`ValidationError` модели `StoredChart` может содержать `input_value` с
началом бинарного payload. `BuildNatalSuccess` скрывает входы в тексте ошибок;
полный форматированный traceback его валидации проверяется тестом.

Атрибуты вложенных сообщений, существенные для этого сценария:

| Сообщение | Атрибуты |
|---|---|
| `BirthInput` | `birth_date: date`, `birth_time: time\|None`, `place_id: str`; свободный текст места и координаты не входят. |
| `ResolvedBirthData` | `utc_datetime`, `latitude`, `longitude`, `tz_id`, `utc_offset_seconds`, `canonical_place`, `time_unknown`, `birth_time_domain?`, `warnings`. |
| `ChartArtifact` | `calculation_key`, `spec`, `calculation_version`, `chart`. |
| `SessionState` | `session_id`, `state_version`, `birth_input?`, `birth_resolved?`, `base_chart? {state_version, spec}`, `created_at`, `expires_at`, `hard_expires_at`. |
| `SessionSnapshot` | `state`, `dialog: tuple[DialogTurn,...]`, `chart: StoredChart\|None`; один атомарный результат touch. |
| `StateDelta` | `birth_input`, `birth_resolved`, `base_chart_spec`, `base_chart_payload`; все четыре обязательные nullable-поля, заполненные вместе либо все `None`. |
| `StoredChart` | `payload_format`, `calculation_key`, `calculation_version`, `payload: bytes`; сессионный слой не интерпретирует bytes. |
| Отказы до CAS | `InputRequired {issues: tuple[Issue,...]}`, где `Issue {field, code, candidates?, constraints?}`; `ResolutionUnavailable {error_code, retryable}`; `CalculationFailed {error_code}`; `ChartArtifactEncodingError {error_code, cause_type?}`; `StoredChartPreparationError {reason, cause_type?}`. Причины Handler: `ENCODE_FAILED`, `ENCODE_UNEXPECTED`, `PAYLOAD_SIZE_INVALID`, `ENVELOPE_INVALID`. |

## 8. Логирование и восстановимость последовательности

INFO фиксирует **фактическую передачу управления** парой событий, а не
только начало и итог операции (ADR-0036/0037). Формат для каждого прямого
вызова:

```text
application_message direction=<send|receive> run_id=<id|->
                    peer=<actual component class> operation=<operation>
                    message_type=<request or actual result type> attempt=<1|2|->
```

В `send` указан входной тип, в `receive` — фактический тип результата,
включая типизированный отказ. `peer` — реальный адресат вызова. Для
Orchestrator обязательны пары вокруг `ContextService.load`,
`BuildNatalHandler.handle`, `ContextService.save`; для Handler — вокруг
`BirthDataResolver.resolve`, `ChartArtifactResolver.ensure_chart` и нового
`ChartArtifactPort.to_stored` (фактический `peer=ChartArtifactResolver`).
`attempt=1|2` относится к точному retry
`save`. `receive` пишется только после возврата; исключение или отмена
сопровождаются terminal/error событием без ложного `receive`. INFO не содержит
тело сообщения, данные рождения, `session_id` или бинарные байты.

Когда M1-6 добавит transport, его прямые bootstrap-вызовы
`ContextService.create/load` и локальный вызов чистой `session_view` должны
быть видны как `send`/`receive` с фактическим `peer` (класс или функция),
`operation`, `message_type` и доступной корреляцией. Это наблюдение вызова,
а не новый координатор или обращение к resolver. В M1-5.2 пары
`application_message` проверяются на компонентном пути build;
транспортных событий пока нет.

При effective DEBUG `ContextService` пишет парные
`component_message direction=in|out operation=context_<method>` с
`message_type`, `status`, `payload_mode` и полным однострочным JSON сообщения;
у него `run_id=-`. Расчётные границы и Handler показывают полные сообщения
по ADR-0025/0028. **Единственное узкое исключение:** в любой DEBUG-проекции
`StoredChart` показываются только `payload_format`, `calculation_key`,
`calculation_version` и размер payload, но не сами байты. Это касается
`StateDelta`, `SessionSnapshot`, входа/выхода ContextService и Handler;
полный `ChartArtifact` на расчётной границе сохраняет действующий режим
DEBUG. Для `to_stored` DEBUG-вход содержит полный артефакт, а выход — формат
и размер бинарного результата без его байтов. В M1-5.2 проекция только
возвращает `safe_reason`; она не пишет ERROR и не делает I/O. В M1-6
вызывающая transport-граница после `chart_unavailable` пишет ERROR с этим
кодом, без payload и данных рождения. Проверка этого ERROR-события относится
к M1-6. Ниже DEBUG сериализация полного сообщения не выполняется.

Для отказа подготовки `StoredChart` сведения об ошибке в журналах Handler и
Orchestrator, включая форматированный traceback `logger.exception`,
ограничиваются типом исключения и безопасным кодом/причиной: без
`input_value`, исходной ошибки валидации или фрагмента payload.
Событие `build_natal_failed` явно содержит `reason` и `cause_type`; для
отказов, у которых их нет, оба поля имеют значение `-`. Для
`ENCODE_FAILED` и `ENCODE_UNEXPECTED` traceback показывает только эти два
значения, без исходного текста исключения порта.

При проверке логов прямым стрелкам координации Orchestrator/Handler на
sequence должны соответствовать наблюдаемые отправка и приём либо
отправка и terminal/error при исключении. DEBUG показывает вход и исход
`ContextService`; M1-6 добавит такую видимость для bootstrap. В частности,
должны различаться `ensure_chart → to_stored → save` и
`load → session_view`.

## 9. Схема SQLite: таблица `session_charts`

Это новая таблица session component v2; `session_states` остаётся родителем.

```sql
CREATE TABLE session_charts (
    session_id TEXT PRIMARY KEY
        REFERENCES session_states(session_id) ON DELETE CASCADE,
    payload_format INTEGER NOT NULL CHECK (payload_format >= 1),
    calculation_key TEXT NOT NULL CHECK (length(calculation_key) > 0),
    calculation_version TEXT NOT NULL CHECK (length(calculation_version) > 0),
    payload BLOB NOT NULL CHECK (length(payload) BETWEEN 1 AND 1048576)
);
```

`session_id` задаёт отношение 0..1 карта к 1 сессия; отдельный индекс,
`expires_at` и `state_version` в дочерней таблице не нужны. Родительский
`session_states.state_json` по-прежнему хранит `birth_input`,
`birth_resolved` и `base_chart(spec)`, но не бинарный артефакт. CAS заменяет
родительское состояние и дочернюю строку в одной транзакции; touch читает
согласованный snapshot. Декодер поддерживает `payload_format=1`, но SQL
позволяет отличить более новый формат и вернуть `chart_unavailable`.

При открытии существующей базы и после миграции SQLite-адаптер проверяет
схему `session_charts` так же, как принадлежащие ему таблицы v1: точные
столбцы, типы, `NOT NULL` и первичный ключ, обязательные `CHECK` для формата,
ключа, версии и размера payload, а также единственный FK
`session_id → session_states(session_id) ON DELETE CASCADE`. Несовместимая
схема отклоняется с `SESSION_SQLITE_SCHEMA_INCOMPATIBLE` до обслуживания
сессий. Таблица при отсутствии записи v2 в `schema_migrations` также не
принимается как уже мигрированная. Отсутствие строки карты при непустом
`base_chart` и лишняя строка карты при пустом `base_chart` определяются при
атомарном read-and-renew как
`StateReadError(SESSION_SQLITE_DATA_CORRUPT)`. Ожидаемые ошибки валидации
`SessionSnapshot` адаптер переводит в тот же `StateReadError`, не выпускает
сырой `ValidationError` наружу; touch при таком отказе не фиксируется.
`ContextService.load` возвращает
`StateReadFailed`, а не `chart_unavailable` или новую пустую сессию.

Миграция v2 в одной транзакции создаёт таблицу, удаляет все прежние
`session_states` (их `session_dialogs` удаляются каскадом) и фиксирует новую
версию в `schema_migrations`. Неуспех оставляет исходную схему и данные без
частичного перехода. После M1-13 потери данных при будущих миграциях сессии
не допускаются.

## 10. Проверка принятого поведения

- Общий conformance для InMemory и SQLite: пустая create, атомарный
  state+chart CAS, read-and-renew, reset/delete/reaper, конфликт без записи
  карты и `AlreadyApplied` без переписывания победителя.
- Успешный build, остановка runtime, запуск нового runtime с пустым кэшем,
  bootstrap той же живой сессии: тот же артефакт без вызова расчёта; при
  другой версии расчёта — `chart_stale=true`.
- Первая ошибка до CAS и повторный вход: в сессии нет введённых данных и
  карты. Отдельно проверить неопределённый commit: возможна только
  согласованная пара state+chart или отсутствие обеих.
- Две вкладки: последовательное перестроение B и поздний refresh A;
  отдельно конкурентные команды с одним expected version.
- Нечитаемая карта даёт `chart_unavailable` без мутации содержания;
  структурный отказ/touch даёт `StateReadFailed`. INFO и DEBUG проверяются
  по требованиям §8, без бинарного payload в журнале.
- Отдельные SQLite-тесты создают оба вида структурного рассогласования
  state/child row и подтверждают `StateReadFailed` с кодом
  `SESSION_SQLITE_DATA_CORRUPT`; тест схемы отклоняет изменение формы,
  обязательного `CHECK` или FK `session_charts` при открытии базы.
- Отказы кодирования и размера проверяются до CAS: типы исключений,
  `ApplicationInternalFailure` с `UNEXPECTED_FAILURE/LOADED`, отсутствие
  вызова `save` и неизменность ранее сохранённых state+chart. Тестовые
  реализации `ChartArtifactPort` в `tests/application/stubs.py` и
  `tests/application/orchestrator_fakes.py` получают `to_stored`. Отдельный
  тест выполняет реальный путь Handler → Orchestrator с отказом валидации
  `StoredChart` и проверяет полный форматированный журнал с traceback:
  в нём нет `input_value`, исходного текста `ValidationError` и узнаваемого
  префикса payload.
- Замороженные golden-фикстуры содержат байты `StoredChart` формата 1:
  прежний минимальный артефакт, полный натал 1985 года и космограмму той же
  даты с `time_uncertainty`. Пока формат 1 поддерживается, критерий
  совместимости — успешное декодирование, сверка ключа, версии, spec и
  расчётного входа, а также структурная полнота для **каждой** фикстуры,
  включая прежнюю: `decode(bin).model_dump(mode="json")` должен равняться
  словарю `json.loads(gzip.decompress(bin))`. Сравниваются словари, без
  сравнения с заново закодированными байтами. Структурное расхождение по
  умолчанию требует нового `payload_format`, если поле не внесено явно в
  список допустимых аддитивных. Сейчас этот список пуст. Эталоны не
  перегенерируют вслед за изменением
  модели. При намеренном несовместимом формате 2 добавляют новую фикстуру,
  а старые сохраняют для проверки
  `chart_unavailable`, если декодер формата 1 удалён. `to_stored` выдаёт
  текущий формат из единого набора форматов кодека.
- Тесты проекции проверяют все коды `safe_reason`, порядок проверок и то,
  что только различие с текущей `CalculationVersion` даёт `chart_stale`.
  Граница импортов и поведенческий restore-тест запрещают зависимость
  проекции от resolver, кэша, движка и session I/O. Тест ERROR-лога
  вызывающего transport относится к M1-6.
