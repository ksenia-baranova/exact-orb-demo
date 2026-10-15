# Источники и наблюдаемость: ui-chart-wheel

**Автор:** Analyst / Codex, TASK-A-001, актуализация 2026-10-15; исходное исследование 2026-10-13.
**InputSHA актуализации:** `2169845b770754e11ae8b5cb1e13ffcd780784c8`; исходный Analysis InputSHA `5188b52`; **MainBaseline:** `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.
От v1 @ 683bdd0 до 2b84607 изменились Manager и добавились process_notes.md; пакет v1 интегрирован PR #63 / bc9a4fb. Исходные code / tests / current requirements / ADR не изменились от MainBaseline. Ни чтение sources, ни текущая документальная синхронизация не являются выполнением implementation tests или live acceptance.

## Текущая сверка v3

На входе подготовки v3 после fetch HEAD Analyst / origin/change совпали на 2169845; origin/analysis был cb25422. SHA публикации v3 определяется корневым handoff и историей Git. Локальная change, указанная Owner в передаче как d51bbcb, не используется как более свежий source: remote 2169845 включает Tester PR #68. После cb25422 в change пришли консультации Developer @ 04be207 / Tester @ 9dd8b96; production / tests / нормативный MainBaseline не изменились.

Новый источник — передача Owner 2026-10-15 из чата owner change/ui-chart-wheel (ThreadId 01a13458-36ca-7021-9246-a73b3d3b2b0d), сделанная по прямому поручению человека «Передай анлитику все принятые решения если больше нет открытых вопросов». Передача содержит исходные ответы / уточнения; финальные уточнения имеют приоритет над ранними широкими формулировками. Дополнительно Owner в чате Analyst прямо подтвердил снятие только исчезнувшего выбора при automatic current. Эти новые evidence ещё не отражены в Manager @ InputSHA. Подписанное предложение регистрации — [decision_input.patch](decision_input.patch), только дополнение DP-O-012/013, без смены статусов; отдельный реестр решений не создаётся.

Визуальные примеры, названные в Owner-передаче: `chart-angles-layout.html`, вариант «Таблица», и `conjunction-marker.html`, вариант «Контур символа», в каталоге `C:/Users/KateUser/.codex/visualizations/2026/10/13/01a13458-36ca-7021-9246-a73b3d3b2b0d/`. Они передают выбранную композицию, не нормативные палитру / координаты / толщины. Rendering этих примеров Analyst в текущем проходе не выполнял; источник выбора — Owner evidence.

Runtime-основа контрпримера проверена чтением main.mjs: visible / online вызывают session.foreground; recovery.test.mjs содержит mounted visibility/online control с новой identity B и сохранённым draft. F0 natal публикует moon→asc, F0 cosmogram angles=null: это различающий controlled переход AS-WHEEL-30. Тесты прочитаны, команды runtime checks не запускались.

## Проверенные источники

| Источник | Прочитанный предмет / вывод |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md), [метод](../../../../development_approach/development-approach.md), [роли](../../../../development_approach/roles.md), [процесс](../../../../development_approach/process/process.md) | Scope/ownership; G0/G1/G3 и ручные handoffs; §6 Git отдельно, §7 каталоги. Использованы относящиеся части; алгоритм сборщика не реализуется. |
| [Skill](../../../../development_approach/skills/functional-analyst/SKILL.md), [шаблоны](../../../../development_approach/artifacts/functional-analyst.md), [правила требований](../../../../requirements/README.md) | FULL новой области, DELTA старой, findings, точные версии; current/ после final approvals. |
| [Manager](../manager_artifact.md) и [process_notes.md](../process_notes.md) @ InputSHA | Brief v1 / §2.1, регистрация назначения / STARTED / передачи v1 в §2.4; G0 подтверждён, v1 имеет review-статусы в сводке. DP-O-014 ACCEPTED; DP-O-010…013 OPEN с перечисленными подтверждёнными частями. G1 неполон, консультации не назначены. Эти записи относятся к v1, а не к approval новой редакции. |
| [UI requirements](../../../../requirements/current/ui/birth-form-and-facts.md), [AS-UI-01…23](../../../../requirements/current/ui/scenarios.md) | Прочитаны нормативные пункты формы/фактов/сводки/current/recovery, исходные IDs и карта coverage. Новое колесо не получает прежний PASS. |
| [HTTP](../../../../requirements/http_api.md) §§6/7.2/9/12/13; [dto.py](../../../../../src/exact_orb/http_api/dto.py), [projectors.py](../../../../../src/exact_orb/http_api/projectors.py) | Публичные поля, whitelist, nullable cosmogram, from/to points/asc/mc/vertex; POST не возвращает BirthViewDTO, UI summary snapshot не расширяет API. Projector — относящиеся projection/endpoint guards. |
| [ADR-0029](../../../../requirements/decisions/0029-canonical-chart-point-identifiers.md), [0030](../../../../requirements/decisions/0030-lunar-node-axis-representative.md), [0032](../../../../requirements/decisions/0032-unknown-birth-time-aspect-semantics.md) | Canonical ID, производная позиция south_node, устойчивые аспекты/минутный домен. Предметные численные правила не меняются. |
| [ADR-0034](../../../../requirements/decisions/0034-birth-data-and-terms-of-use.md), [0040](../../../../requirements/decisions/0040-session-bootstrap-and-current-chart.md), [0041](../../../../requirements/decisions/0041-stored-chart-in-session.md) | Manual gate, bootstrap отдельно от current, чтение StoredChart без расчёта; known debt не новая находка. |
| [Chart Artifacts responsibilities](../../../../requirements/component_responsibilities/exact-orb_chart_artifacts.md) §1 и относящиеся to_stored/identity | Расчётный артефакт и renderer имеют разные обязанности; wheel не управляет ensure_chart/cache. |
| [main.mjs](../../../../../src/exact_orb/http_api/ui/main.mjs), [facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs), [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs), [response.mjs](../../../../../src/exact_orb/http_api/ui/response.mjs) | renderSession: защита draft; summary из actual birth/immutable submitted snapshot; facts details/identity; accept/submit/publish, response validation. Wheel/selection отсутствуют. |
| [index.html](../../../../../src/exact_orb/http_api/ui/index.html), [styles.css](../../../../../src/exact_orb/http_api/ui/styles.css) | Form/gate, hidden/focus/адаптивность. Большая часть session/recovery controls вставляется внутрь form. |
| [operation_logging.py](../../../../../src/exact_orb/http_api/operation_logging.py), [routes/session.py](../../../../../src/exact_orb/http_api/routes/session.py), [routes/build.py](../../../../../src/exact_orb/http_api/routes/build.py) | log event names, recorded_call, load/create/session_view/admission/execute; сопоставление с HTTP sequences. |
| [UI tests](../../../../../tests/ui/), [fixtures](../../../../../tests/ui/fixtures/), [HTTP tests](../../../../../tests/http_api/), [boundaries](../../../../../tests/test_module_boundaries.py) | Имена/тела относящихся facts/session/recovery/projector/delivery cases; real coordinator, leaf fake network/deferred/fakeClock; прямые Python import invariants не ослабляются. |
| [Current sequence](../../../../sequence_diagrams/http_api/004-current-chart.puml), [build sequence](../../../../sequence_diagrams/http_api/003-build-natal.puml), [bootstrap sequence](../../../../sequence_diagrams/http_api/001-session-bootstrap.puml) | Existing HTTP участники и события; новые UI sequences не заменяют серверные technical paths. |
| [UI/UX](../../../../ui_ux/README.md), [кандидат требований](../../../../ui_ux/requirements.md) §§6/7/9/10, [решения](../../../../ui_ux/decisions.md), [render review](../../../../ui_ux/render_review.md), [prototype](../../../../ui_ux/web-prototype.html) pt/spread/wheel/selection | Визуальные кандидаты; конкретные ref / spread values / ℞ / legend не нормативны. Принятые 0° / ASC слева и направление — по DP-O-014, условный минимальный разнос — по подтверждённой части DP-O-011. |
| [Р5](../../../../ui_ux/renders/r5-chart-detail.png), [Э7 mobile](../../../../ui_ux/mobile/e7-chart-detail.png) | Визуально просмотрены: Р5 колесо слева, mobile краткие карточки планет ниже колеса; Owner принял иную привязку относительно краткой сводки рождения. Числа PNG не проверочный эталон. |
| [Roadmap M1-8](../../../Roadmap/roadmap.md), [общий долг](../../../technical_debt.md) | Drawing ADR до кода, отдельные M1-8.1/M1-9; старые estimates не новый бюджет и known debts не findings M1-8. |

## Наблюдаемость

N — существующий серверный trace @ MainBaseline; U — упорядоченное UI/network evidence, требуемое для новых наблюдаемых путей. Новые события N не выдумываются. U означает browser evidence либо deterministic integration наблюдение на согласованном шве, не обязательный runtime logger/передачу телеметрии.

| Behavioral переход | Фактические события baseline N | Evidence UI U / предел |
|---|---|---|
| Page → bootstrap → Context create/load → ready | http_request_started; http_message send/receive ContextService.create/load; http_request_finished; X-Request-ID | Network порядок bootstrap перед current, ready не рисует колесо |
| Current → Context load → session_view → chart_ready/empty/unavailable | http_message send/receive load и session_view под request_id; ERROR chart_unavailable для safe unavailable; terminal | Принятая identity/source=current; колесо/сводка/таблицы совпали либо убраны |
| Явный build → admission → Orchestrator → committed | http_message AdmissionControl.reserve/release, ApplicationOrchestrator.execute, application/component events, run_id=request_id; terminal | Submitted snapshot, единственный POST, source=build и та же identity у обоих представлений |
| Refusal / lost response / recovery → safe read | Реальные terminal/code/Retry-After, если получены; каждое новое чтение имеет отдельный request_id. При потере клиентского ответа нельзя вывести его status из отсутствия DTO | Recovery intent отдельно от confirmed chart/draft; safe-read sequence; gated explicit retry; log первого build при наличии серверного evidence |
| Accepted state → колесо и HTML | Серверные N заканчиваются HTTP исходом, не доказывают DOM render | Приёмка DTO → передача обоим представлениям → видимый результат/отказ; identity и сохранность данных |
| Выбор планеты / аспекта → HTML и графика → повторное снятие планеты | Серверных N нет: локальные действия не инициируют запрос | Actor, выбранный canonical ID / пара, весь отбор aspects и категории, порядок / повторное снятие, network count; первые пять / отдельное раскрытие, отсутствие scroll/focus transfer. В v3 выбор планеты / аспекта взаимоисключающий, аспект оставляет одну строку; повтор снимает его с возвратом общего раскрытия. U отдельно отличает automatic current, F5 и исчезнувшую пару |
| Resize / form reveal / renderer failure | Локальных серверных N нет; safe recheck при назначенном действии использует N current | Сохранность фактов / draft; при resize выбранная планета / раскрытие сохранены. При render failure HTML той же карты доступен и есть сообщение ошибки, автоматического POST нет; это не successful SVG outcome |

В PUML роль «Колесо» — наблюдаемый участник, точная техническая граница ожидает DP-O-010. Не вводятся новые сервисы/слои или сетевой обмен между UI participants. Реализация внутренних calls/log seams и технические sequences принадлежат Developer. Tester сопоставляет N и U на CandidateSHA; исходники N сейчас прочитаны, live logs не собирались.

## Историческое сопоставление Manager и пакета v2 @ 2b84607

| Источник @ 2b84607 | Применённый контракт / сценарии | Что осталось открытым |
|---|---|---|
| DP-O-014 ACCEPTED | REQ-WHEEL-02/03, AS-WHEEL-25, sequence 001: ASC / 0° слева, рост против часовой стрелки | Drawing ADR / реализация / geometry evidence, полный closure FIND-WHEEL-001 |
| DP-O-010, подтверждённый локальный отказ | REQ-WHEEL-10/11, AS-WHEEL-04/24, sequence 001/003: HTML / данные доступны, сообщение отказа SVG | Техническая граница / интерфейс / ownership выбора / замена, consultations |
| DP-O-011, четыре правила | REQ-WHEEL-05, AS-WHEEL-07/09/10: без разноса по умолчанию; минимально только конфликтующие; выноски только смещённым; порядок | Численный критерий / algorithm / R/☌ / предел / fallback |
| DP-O-012, стиль линий | REQ-WHEEL-06/07, AS-WHEEL-08: exact сплошной, working пунктир, тип цвет + текст, выбор толще при прежнем цвете / рисунке | Палитра / legend layout / категория и выбор ☌ |
| DP-O-013, выбор / таблицы | REQ-WHEEL-07/08/09/10, DELTA REQ-UI-03/04/05/06, AS-WHEEL-11…14/16/18/23/26/27, sequence 002/003 | Повторный current той же карты, смешанный аспектный выбор / его снятие, остальная композиция facts / angles, keyboard order / mobile targets и форма |
| process_notes.md, заметки 3…6 | Учтён факт регистрации v1; снято уже зарегистрированное proposal-приложение; новые choices включены в requirements / AS | Сам процесс, назначения Developer / Tester и их estimates принадлежат Manager / ролям, не изменены Analyst |

## История предложений DP

Manager §2.4 @ 2b84607 подтверждает регистрацию вклада DP-O-010…013 и DP-O-014 из Git-версии `683bdd0:docs/project_management/change_plans/ui-chart-wheel/analyst/decision_input.patch`. Предложение уже применено по смыслу к единственному реестру; повторное применение к новому Manager не требуется и может конфликтовать с принятыми ответами Owner. В пакете v2 этот patch удалён как завершённое приложение, исходные bytes и история v1 сохранены в Git. Отдельного нового реестра Analysis не создаётся. Проверяется актуальный Manager baseline и отражение его решений, а не применимость старого patch к изменившемуся файлу.

## Граница новой редакции

Предыдущая таблица сопоставления v2 и история patch v1 — snapshots прежних входов, а не перечень нынешних нерешённых подпунктов. В v3 явно перенесены ответы о взаимоисключающем выборе / одной паре, повторном снятии аспекта / прежнем раскрытии, F5 отдельно от automatic current, исчезнувшем выборе, форме / draft, всех positions / таблице angles и подписи / контуре ☌. Не разрешены exact renderer interface / ownership; измеренные collision/hit bounds, пределы / fallback / R / несколько ☌; палитра / legend layout / расположение маркеров; mobile targets / keyboard order и доступное размещение recovery controls. Весь DP-O-010…013 не закрывается отдельным Owner ответом.
