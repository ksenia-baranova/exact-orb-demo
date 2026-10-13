# Источники и наблюдаемость: ui-chart-wheel

**Автор:** Analyst / Codex, TASK-A-001, 2026-10-13.
**InputSHA:** `5188b523089acc8081585e869c482ee0d343cfba`; **MainBaseline:** `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.
`git diff --name-status MainBaseline InputSHA` содержит только добавленный Manager-файл. Нормативные/code/test источники ниже одинаковы на этих двух commits. Чтение исходников не равно выполнению tests или live acceptance.

## Проверенные источники

| Источник | Прочитанный предмет / вывод |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md), [метод](../../../../development_approach/development-approach.md), [роли](../../../../development_approach/roles.md), [процесс](../../../../development_approach/process/process.md) | Scope/ownership; G0/G1/G3 и ручные handoffs; §6 Git отдельно, §7 каталоги. Использованы относящиеся части; алгоритм сборщика не реализуется. |
| [Skill](../../../../development_approach/skills/functional-analyst/SKILL.md), [шаблоны](../../../../development_approach/artifacts/functional-analyst.md), [правила требований](../../../../requirements/README.md) | FULL новой области, DELTA старой, findings, точные версии; current/ после final approvals. |
| [Manager](../manager_artifact.md) @ InputSHA | Brief v1, §2.1 задание, 9 accepted Owner choices, DP-O-010…013 OPEN; назначения/STARTED ещё не зарегистрированы в этом входе. Текущее прямое поручение Owner — источник начала работы. |
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
| [UI/UX](../../../../ui_ux/README.md), [кандидат требований](../../../../ui_ux/requirements.md) §§6/7/9/10, [решения](../../../../ui_ux/decisions.md), [render review](../../../../ui_ux/render_review.md), [prototype](../../../../ui_ux/web-prototype.html) pt/spread/wheel/selection | Визуальные кандидаты, demo ref/℞/legend/отсутствующие API факты не нормативны. |
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
| Point/aspect activation → согласованное выделение → снятие | Серверных N нет: локальные действия не инициируют запрос | Actor, выбранный canonical ID/пара, обе стороны, порядок, снятие и network count; closed-table поведение после DP-O-013 |
| Resize / form reveal / renderer failure | Локальных серверных N нет; safe recheck при назначенном действии использует N current | Сохранность фактов/draft, focus, отсутствие POST; render failure не приписывается успешному UI outcome |

В PUML роль «Колесо» — наблюдаемый участник, точная техническая граница ожидает DP-O-010. Не вводятся новые сервисы/слои или сетевой обмен между UI participants. Реализация внутренних calls/log seams и технические sequences принадлежат Developer. Tester сопоставляет N и U на CandidateSHA; исходники N сейчас прочитаны, live logs не собирались.

## Передача предложений DP

[decision_input.patch](decision_input.patch) — применимое текстовое предложение изменений **единственного** Manager-реестра @ InputSHA: подписанный Analyst input DP-O-010…013 и новая OPEN строка DP-O-014. Это не второй реестр, не фактическая правка Manager и не Owner choice. Manager должен просмотреть patch, зарегистрировать его в своём файле и сохранить точную версию; выбор/статусы accepted DP-O-001…009 сохранены. Requirements/handoff ссылаются на IDs и baseline, подробности предложения находятся только в patch для целевого реестра.
