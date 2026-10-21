# Implementation Plan: ui-chart-wheel

> **18.10.2026 / TASK-D-003:** исторический consultation v2 ниже сохранён. [Исследовательский report](task_d003_research_report.md) содержит фактический STARTED, контрпримеры и предлагаемую замену полного прогноза8–12 на9–14чд; это не утверждённое увеличение бюджета. Production DEV-WHEEL-02…04 не начинались, G3 не подтверждён.
**Автор:** Codex / Developer, `TASK-D-002`, 2026-10-16; consultation v2 по Analyst v3.
**InputSHA / DP baseline:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`, [Manager §3](../manager_artifact.md#3-единый-реестр-dp); применимы DP-O-001…014. Старый Developer input @ 04be207 уже зарегистрирован Manager; новый подписанный [patch](decision_input.patch) к DP-O-010…014 подготовлен, но не применялся.
**Сводка / назначение:** [TASK-D-002](../manager_artifact.md#27-task-d-002--повторная-developer-consultation-по-analyst-v3); состояния ведёт Manager.
**Исходный нормативный контракт:** [UI requirements](../../../../requirements/current/ui/birth-form-and-facts.md), [AS-UI-01…23](../../../../requirements/current/ui/scenarios.md), [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto), ADR-0029/0030/0032/0034/0040/0041 @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`. Requirements, ADR, code / tests / общие sequences совпадают с InputSHA по scoped diff; актуальный remote main этим проходом не обновлялся.
**Контракт change для консультации:** [requirements](../analyst/requirements.md), [scenarios](../analyst/scenarios.md), [findings](../analyst/findings.md), [sources](../analyst/sources.md), [behavioral sequences](../analyst/sequence_diagrams/ui/) v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; интеграция `859718ae9e209ee18a0e24e44f765e24e58b4045`. Пакет включает FULL колеса, DELTA UI, AS-WHEEL-01…30 и MODIFY AS-UI-22. Это вход review, не approved контракт для реализации.
**Заключение:** FEASIBLE WITH DECISIONS на InputSHA. **Estimate:** предварительно 8–12 чд Developer, уверенность ниже средней до SVG measurements / решений DP-O-010…013. Старый план сохранён @ `04be207627de1049deac2e069574e01b62536607`.

## Оценка и границы

| Состав | Чд | Включено |
|---|---|---|
| Графика / интеграция | 5–7 | Отдельно назначенный bounded spike, drawing ADR / technical sequences, geometry / endpoints / SVG natal-cosmogram, R/☌/legend, local failure, Developer checks |
| Выбор / форма / recovery | 3–5 | Result controller, сохранение / снятие выбора на новом DTO, 5/all/one/filter, keyboard, сводка / editor, сопоставление snapshot и причины принятия результата, mounted regression / handoff |
| Разработка всего | 8–12 | Один Developer; без повторного суммирования checks и spike |
| Повторная консультация / эта документальная актуализация | 0,5–0,75 | Отдельная оценка TASK-D-002, не прибавлена автоматически к 8–12 и не объявлена фактическими затратами / согласованным сроком |

Предполагаются native SVG и текущие ES modules без нового framework / API / зависимости; согласованный v3 и доступные Reviewer / Tester / стенд для назначенных этапов. Вне оценки: Analyst rework, независимый Tester, Owner acceptance, ожидание ответов, deployment / HTTPS setup, M1-8.1 / M1-9 и существенный пересмотр scope. Roadmap 5 дней не является текущим бюджетом. Верхняя граница 12 условна до измерений; при неуспехе spike нужна переоценка, а не молчаливое принятие плотности. Сроки исполнения / ответа / эскалации Manager ещё не согласованы; календарное обещание не дано.

## Изменения v1 → v3 и влияние на план

| Новый согласованный expected result | Затронутый work item / дополнительный контроль |
|---|---|
| Либо point, либо аспект; аспект даёт одну строку и одну графическую пару | DEV-WHEEL-02/03, AS-WHEEL-28; включая unrelated pair вне прежнего point filter и background без линии / ☌ |
| Point toggle возвращает первые 5; aspect toggle — прежнее раскрытие общего списка без point filter | DEV-WHEEL-03, AS-WHEEL-13/29; normal-list expansion хранится отдельно от selection и houses |
| Automatic current сохраняет существующий выбор даже на другой identity, снимает только исчезнувший | DEV-WHEEL-03/04, AS-WHEEL-30; обновить факты и category, не держать старые координаты / row index / ссылку на DTO |
| F5 и новый принятый явный build по изменённым birth data сбрасывают выбор / раскрытие | DEV-WHEEL-03/04, AS-WHEEL-02/14/19…22; причина принятия важнее HTTP-метода ответа |
| Collapse после build только при совпадении текущих полей со snapshot; late draft остаётся открытым | DEV-WHEEL-04, AS-WHEEL-01/18/21; простого historical dirty-флага недостаточно |
| Все points сразу, angles отдельной таблицей; MODIFY AS-UI-22 отменяет глобальный hidden gate | DEV-WHEEL-03/04, AS-WHEEL-03/26/27; сохранить весь прежний нормативный baseline кроме явной дельты |
| ☌ имеет подпись категории; при выборе усилен контур только символа | DEV-WHEEL-01/02, AS-WHEEL-07/08; оформление выбрано Owner, palette / интервалы / measured bounds ещё требуют technical input |

Нового продуктового противоречия не найдено. Разрыв DEV-FIND-WHEEL-001 устранён в документальной части; это не закрытие независимого review / измерений и не approval пакета. Рекомендации v1 о reset любой новой identity или ином оформлении ☌ заменены принятыми правилами v3; вопросы о toggle / collapse / позиции углов повторно Owner не задаются.

## Техническая граница — предложение для DP-O-010 / Technical Reviewer

Result controller владеет `selection = none | point(id) | aspect(key)`, раскрытием обычного списка aspects и независимым раскрытием houses. Renderer получает immutable подтверждённый ChartDTO / актуальную identity и presentation selection; сообщает canonical activation intents, не выполняет HTTP / session / engine / cache. Кандидат port — mount/update/dispose, имена и точный тип исходов ещё не утверждены. Это локальное разделение текущего UI, без новой сервисной прослойки.

При automatic current controller разрешает point ID / aspect key заново в новом DTO и только затем строит оба представления. Кандидат aspect key — `(from,to,type)` в каноническом порядке API; category / orb / индекс строки / identity не входят в ключ сохранения. Перед утверждением проверить уникальность и порядок ссылок по публичному контракту / projector; не считать одинаковую пару с другим type тем же аспектом без принятого правила. Прямой AS-WHEEL-30 проверяет сохранённую пару с изменившейся category=background и исчезновение natal moon→asc в cosmogram. При отсутствующем выборе очистить только selection, сохранив раскрытие.

Ожидаемый отказ SVG имеет явный локальный исход: HTML / сводка принятой B доступны, SVG A удалена, видимо сообщение отказа B. Такой исход не должен попадать в общий `session.publish` как ошибка всего ответа и включать requiresReconciliation. Неожиданные общие ошибки по-прежнему имеют действующий fallback; подавления исключений без видимого исхода нет. Проверяемые controls: успешный renderer, альтернативный renderer на том же port, затем принудительный локальный отказ на новой карте.

Различать принятие собственного build и автоматическое чтение через существующие intent / source / request_id / recovery данные. HTTP GET сам по себе не задаёт preserve: recovery может подтвердить новый результат собственного изменённого намерения. Reset выполнять один раз на подтверждённое событие принятия, не при каждом publish/render или смене identity. Если существующий шов недостаточен, Developer доказывает конкретный пробел и согласует узкую правку coordinator; перепроектирование session не разрешено этим планом.

Обычные внутренние детали — чистые helpers, event wiring и размещение state внутри утверждённой границы. Существенная граница заменяемости / failure ownership / drawing rules требуют отдельного Technical Reviewer и ADR до кода. Вклад Manager — [DP patch](decision_input.patch), текущий реестр здесь не дублируется.

## Проверенные швы и покрытие

| Источник / existing tests | Использование и пробел |
|---|---|
| [facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs), facts.test.mjs | readChartFacts исключает longitude / cusp_longitude, renderFacts пересоздаёт строки, identity change закрывает details. Эти механизмы нельзя без изменения перенести на v3 preserve. Переиспользовать проверку порядка / immutable DTO / angle endpoints; дополнить новым selection / focus behavior. |
| [main.mjs](../../../../../src/exact_orb/http_api/ui/main.mjs), session.test.mjs | Уже различены current birth, immutable submitted summary и draft; controls находятся внутри birth-form. Сравнивать snapshot перед collapse, держать feedback / safe read вне сворачиваемых полей. |
| [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs), recovery.test.mjs | Общий render failure включает reconciliation; есть recovery relation, late-response / dispose / coalescing guards. Добавить mounted assertions нового UI, а не копировать весь coordinator suite. |
| [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto), tests/http_api/test_projectors.py | Достаточно existing ChartDTO; from/to допускают points и asc/mc/vertex, dsc/ic только позиции. F0/F1 переиспользуются, API не расширяется. |
| [DOM port](../../../../../tests/ui/fixtures/dom.mjs), test_ui_delivery.py | Порт проверяет wiring / события, не bbox / SVG focus / layout. Новые SVG API добавлять только как листовые seams; modules включать в UI_RESOURCES, упаковка уже поддерживает .mjs. |

Tests в этой консультации только прочитаны. Наличие прежнего PASS M1-7 не доказывает новое SVG/selection поведение. Boundary tests, golden и допуски не ослабляются.

## Предлагаемое отдельное задание spike

**Вопрос:** достижимы ли согласованные collision / readability / hit критерии при default без разноса и минимальном смещении конфликтов на 360 px? До запуска назначить предмет и критерии с Analyst / Tester, не выдумывать acceptance из прототипа.

**Данные / сравнение:** разрежённый контроль, F1, контролируемые F3 / F3-max из AS-WHEEL-09/10; реальные шрифт / glyph bounds, пять R через 0°, 16 IDs, несколько подписанных ☌, близкие angles. Сравнить истинные положения и только конфликтующее смещение, сохранить циклический порядок и leader lines только при сдвиге. Viewports 1440/768/360, pointer / keyboard, actual scale / font фиксируются.

**Timebox / stop:** до 0,75 чд, включено в 5–7 чд графики. Остановить по получению воспроизводимого evidence либо по timebox; не расширять работу молча. При недостижимости согласованного критерия вернуть Manager / Owner конкретный контрпример и варианты предела / fallback / изменения оценки. Скрытие объектов, пересечение как норма или уменьшение шрифта без предела не разрешены.

**Выход:** размеры / screenshots / критерий→actual, контроль сохранности anchors / IDs / порядка, различение glyph и hit bounds; подписанная рекомендация DP-O-011/012/013, draft drawing ADR / sequence только по отдельному назначению и уточнённый estimate. Сейчас spike, ADR и технические sequences не выполняются / не создаются.

## Оставшиеся решения и инварианты

- DP-O-010: точный port, tagged outcomes / failure isolation и replacement evidence; Manager назначает Technical Reviewer.
- DP-O-011: измеримые collision / minimality / hit bounds, предельная плотность и fallback; данные готовит Developer, проверяемость — Tester, изменение наблюдаемого предела принимает Owner через Analyst.
- DP-O-012: palette / contrast / legend layout / размещение нескольких подписанных ☌ и contour width. Категория / подпись / контур уже выбраны Owner.
- DP-O-013: конкретный keyboard order, focus при обновлении / скрытии строки, мобильные цели, доступное расположение recovery controls. Toggle / automatic current / collapse больше не открытые продуктовые вопросы.
- DP-O-014: ориентация уже принята и отражена в v3; остаются drawing ADR / geometric evidence, не новый выбор Owner.

Только опубликованные факты из принятого ChartDTO; geometry не пересчитывает sign / degree / minute / house / category / orb. Background никогда не получает линию / ☌. Локальные выбор / resize / reveal / render failure не отправляют POST. Manual unchecked gate, Retry-After/restart, draft protection и late guards сохраняются. Нет новых aliases, dependencies, сети, framework / runtime logger и чужих role edits.

## Work items

Все work items ниже — будущие предлагаемые срезы. Консультация TASK-D-002 их не запускает; точные approved SHA / разрешение фиксируются перед соответствующим этапом.

### DEV-WHEEL-01. Проверенная граница и drawing rules

- Связи: REQ-WHEEL-01/02/05/06/10/11; AS-WHEEL-03/04/07…10/16/23/24/25; DP-O-010…014. [Промт 01](prompts/01-renderer-decisions-and-spike.md).
- Подход: документальные проверки + отдельно назначенный bounded spike; тесты не выбирают продуктовую семантику. Existing fixtures — F0/F1; плотность / bbox не покрыты Node tests.
- Материалы: developer/evidence/ и technical sequences, проект нового drawing ADR и необходимые ссылки / render checks только после отдельного назначения. Сейчас они не создаются.
- Completion: измерения / counterexamples, рекомендации DP и reviewed technical boundary; после этого повторная оценка и применимый G3 до кода. Observability: accepted DTO → controller → HTML / SVG → outcome, canonical intents и локальный отказ.

### DEV-WHEEL-02. SVG той же опубликованной карты

- Связи: REQ-WHEEL-01…06/09…11; AS-WHEEL-01…10/15/16/24/25 и graphical branch AS-WHEEL-28/30. [Промт 02](prompts/02-svg-renderer.md).
- Подход: тесты → реализация чистой геометрии / resolver / category; DOM сборка → mounted tests. Existing facts/projector assertions не покрывают SVG; проверять стороны и canonical endpoints, а не snapshots самой реализации.
- Files: новые ui/wheel*.mjs по принятому ADR, минимальное подключение main/facts/styles; tests/ui/wheel*.test.mjs, leaf DOM / controlled fixtures, UI_RESOURCES в test_ui_delivery.py.
- Checks: F0 moon→asc, F1 16/12/46 и 15 angle aspects, F3 R/☌, cardinals, empty/cosmogram, selected single-pair / background, alternate/failing renderer. Glyph / contour / targets — отдельно real browser.
- Completion: согласованные drawing rules, target / related results, видимый локальный failure при доступном HTML B без SVG A; DEV-WHEEL-01 и G3. Точные команды — промт 02.

### DEV-WHEEL-03. Согласованный выбор колеса и таблиц

- Связи: REQ-WHEEL-04/07/08/09/10/11, REQ-UI-04/05/06/10; AS-WHEEL-04/07/11…15/23/26…30, MODIFY AS-UI-22; DP-O-008/010/012/013. [Промт 03](prompts/03-selection-and-tables.md).
- Подход: тесты → реализация transitions; реальный result controller / renderer, fake только листовые DOM/network. Переиспользовать immutable DTO / order controls; selection tests новые.
- Files: local result/selection ui modules по port, facts/styles; новый tests/ui/selection.test.mjs, точечные facts tests и DOM seams.
- Checks: none/point/aspect, related/unrelated / background, 5/all/one/filter, разное снятие planet/aspect, все points / отдельные angles, AS-WHEEL-30 с новой category / исчезнувшей парой, focus / keyboard / no HTTP с положительным явным build.
- Completion: preserved selection разрешается по новому DTO, отдельные expansion states, one-pair graphic / строка, адресуемые angles, browser focus/targets; DEV-WHEEL-02 и принятые технические остатки DP. Actor / key / identity / порядок / оба DOM исхода наблюдаемы без нового logger.

### DEV-WHEEL-04. Сводка, редактор и recovery в новом представлении

- Связи: REQ-WHEEL-01/08/09/11; REQ-UI-01/03/08/09/10/11; AS-WHEEL-01/02/12/14…22/24/30, AS-UI-22; DP-O-001…003/010/013. [Промт 04](prompts/04-page-form-and-recovery.md).
- Подход: соединение существующих компонентов → mounted tests; подтверждённый программный defect требует отдельного deterministic regression. Recovery suite не дублировать без assertions нового UI.
- Files: main/facts/index/styles и mounted session/recovery/facts tests, delivery resources. Coordinator менять только при доказанном недостатке acceptance seam и согласованном узком влиянии.
- Checks: source / cause accepted event, own build против automatic current включая recovery GET, snapshot match / поздний dirty draft, stale / rejected build / failed read / timeout / restart / two tabs / dispose; feedback виден при collapse.
- Completion: target Node → все Node → HTTP delivery/projector/boundary → full pytest на назначенном CandidateSHA до G4, воспроизводимый Developer handoff и реальные browser ограничения. Серверные события / request_id дополняются локальным ordered evidence, не доказывают render сами по себе.

## Порядок и завершение

Документальная TASK-D-002 / TASK-T-002 на общем InputSHA → регистрация рекомендаций / approvals и Change Plan Manager → отдельно разрешённые DEV-WHEEL-01 spike / ADR → уточнённый estimate / решения / G3 → 02 → 03 → 04 → checks на CandidateSHA → G4 → независимый Tester. Текущие сроки / G1 / статусы регистрирует Manager; прямое Owner-разрешение текущей редакции не является разрешением следующих этапов.

При неоднозначном expected result вернуть вопрос Analyst через Manager; при недостижимой плотности — конкретный контрпример Owner и переоценку. Независимую уже разрешённую работу продолжать. Никакого скрытия фактов или статичного fallback вместо принятого интерактивного scope без решения Owner. Технические sequences переносятся после acceptance по отдельному назначению; публикация этой редакции разрешена отдельным поручением Owner в корневом Developer-индексе; PR / merge и запуск work items не поручены.


## DEV-WHEEL-01 — исследовательский результат TASK-D-003

Фактическая постановка — [Manager §2.16 / start prompt](../manager/prompts/task-d-003-research-start.md) @8fb2577; исторический prompt01 @f9c70f7 не переписан. Входы/критерии/STARTED и выполненные карточки — [план D003](task_d003_implementation_plan.md). [Report](task_d003_research_report.md), [DRAFT drawing ADR](drawing_adr_draft.md), [technical sequences](sequence_diagrams/ui/001-result-renderer-lifecycle.puml), [checks](checks.md) передают один bounded research package. Тесты production renderer не созданы; собственные isolated scripts находятся только в evidence. Результат не закрывает DP-O-010…013 / TEST-FIND-WHEEL-002.

Рекомендация дальнейшего порядка: TASK-T-004 / TASK-R-001 на одном опубликованном TechnicalPackageSHA → адресный Analyst ответ по новому G03 случаю → Manager/Owner решения по конкретным последствиям → отдельный G3 / work item. Техническую hypothesis внутри принятого поведения можно исследовать без повторения прежнего предстартового круга; новый fallback/API не выбирается Developer. Общая переоценка и её непересекающиеся блоки находятся в report, не складываются с прежними8–12 и не вычитают неизвестный прошлый расход.


## TASK-D-005 — актуализация собственного плана 19.10.2026

Исторические консультация v2 / D003 и их evidence выше сохранены. Актуальные inputs: AssignmentSHA0046ac7 / AnalystContractSHA2736e28 (принятый v3+S1), InputSHA34f187a. Owner согласовал16–24 часа и experiment≤12 внутри; STARTED19.10.2026 00:15:25 MSK, передача до конца21.10.2026. [D005 plan/results](task_d005_implementation_plan.md), [report](task_d005_feasibility_report.md), [findings](task_d005_findings.md).

Техническая граница уточнена в [DRAFT ADR](drawing_adr_draft.md): revoke/removal/HTMLB до guarded dispose/draw, DOM write authority у revision gateway до async settlement, keyed HTML/focus. Aspect index — **unordered endpoints + published type по полному accepted DTO**, не исторический directed candidate; cardinality0/1/>1 и S1 не выбирают first match и не дедуплицируют source rows. A005 active matched goal принят; A006 already_applied условный отдельный policy input. Production не реализован.

Новая order-preserving construction и Q geometry имеют конкретные отрицательные witnesses на720/448/328;14/24 partial geometry,241/438 Q,238/2190 native mismatch и256 compactness failures не дают feasible drawing. Успешные isolated boundary/HTML controls и438 keyboard traces поддерживают проект шва, не acceptance. Forecast9–14 не подтверждён до выбора drawing; HTML-presenter6–10 внутри controller, D005 design1–2 внутри4–6, D00516–24 не прибавляется повторно. Unknown D003 остаток не восстановлен.

Следующий шаг после отдельной публикации D005 — T007/R002 на точном TechnicalPackageV2SHA, Manager/Owner выбирают следующий drawing work item при необходимости. Дополнительный эксперимент/implementation/new dependencies не разрешены молча; G3 остаётся отдельным. Старые критерии/план D003 не изменены, прежний report/run03/manifests неизменны.


## TASK-D-006 — первый этап после выбора пассивного SVG

Актуальное поручение/InputSHA/AssignmentSHA 07bb56ba5d49ec76de64df41ad80d175fbe90a2d, Manager §2.22/2.23. Owner принял HTML-only selection / passive SVG; новый AnalystContractSHA A008 ожидается,2736e28 остаётся baseline исследования. [Конкретный CH-01…05 план/оценка/зависимости](task_d006_controller_html_plan.md) и [handoff D006](../developer_artifact.md#task-d-006--подготовка-первого-controllerhtml-этапа).

Подготовка 0,5–1,5 ч / STARTED 19.10.2026 13:01:09 MSK, high confidence / ответ в этом проходе. Future implementation 14–22 ч / до 3 рабочих дней от отдельного STARTED — предложение, confidence medium. Первый scope controller/canonical state/retained HTML/editor/recovery, без SVG renderer/geometry/hit/callback API/full writer. A006 блокирует только затронутую cause-policy; A008/применимые решения/G3 нужны для допуска, новый общий review D006 не назначен. Старые D005 планы/evidence/ADR не переписываются; исторические оценки не являются остатком, полная9–14 не подтверждена. Реализация/commit/push/PR текущим documentary проходом не выполнялись; Manager-owned статусы/gates сохранены.


## Геометрия v3 — отдельное прямое поручение Owner, 19.10.2026

После D006 Owner прямо поручил переработать геометрию и предложить альтернативы. [Новый proposal / сравнение / exact controls и native evidence](drawing_geometry_v3.md) сохраняет D003/D005/D006, прежние manifests и submitted versions. Это не STARTED controller/HTML implementation и не новый Manager TaskId.

V3-H: real component boxes, joint radial placement, bounded CSP и precision-aware coordinates; geometry/annulus/clip/order12/12 native, local tight108/110, полные изученные predicates10/12. Остались F3/720 Jupiter и F3-max/720 true_node, каждый с допустимым full prefix0,5px и LOCAL_STEP_FAIL. Не принимать drawing целиком; новая техническая основа / два адресных исправления вместо общего исследования. Внешние callout-подписи — NOT RUN / отдельное Owner domain/composition решение.

Исследование остановлено по достаточности в пределах90мин; дальнейший post-audit без новых моделей. D00614–22ч остаётся предложением своего scope, full9–14 не подтверждён и неизвестный остаток не пересчитан. Геометрия не препятствует разрешению независимых CH-02/03 по текущему контракту и ограниченному G3. Production / gates / Manager / чужие артефакты не изменены.


## Решение Owner — условная выносная колонка, 19.10.2026

[Прямое подтверждение Owner / точный scope / влияние на DP-O-011/012](owner_decision_drawing_2026-10-19.md) supersedes прежнее ожидание продуктового выбора внешней колонки и подписи категории. Содержание выбора хранится в source evidence для интеграции в единый Manager-реестр, не дублируется этим планом.

Следующая адресная проработка: новая область вынесенных меток / её bounds/clip/order/resize и локальные ☌/angle controls, затем соответствующая ревизия technical proposal и сравнение по актуальному контракту. Старые H certificates не переиспользуются как PASS нового domain; прежние отчёты/FAIL сохраняются. Оценка или implementation STARTED этим документальным обновлением не назначены, независимый D006 controller/HTML scope не расширен. Manager-owned сводка/DP/gates/requirements Analyst и production не менялись.


## Полное колесо — колонка, композиция и renderer, прямое поручение Owner

Codex / Developer,19.10.2026. InputSHA07bb56ba5d49ec76de64df41ad80d175fbe90a2d; fetch change exit0, HEAD тот же, index сохранён. [Правила/полная матрица/граница](column_renderer_design_v1.md), [DRAFT ADR](drawing_adr_column_draft.md), [полный план40–64ч](full_wheel_implementation_plan.md), [постановка05](prompts/05-full-wheel-passive-column.md). Это завершённая подготовка по прямому поручению, не STARTED production или новый Manager TaskId.

Финал run07:29/29 измеренных configurations и C0/order/row/clip/no-shared-route checks,28/28 isolated renderer controls,13 native+7 analytic controls. Предыдущие shared-route/validator/fallback контрпримеры и остановки сохранены; целиком применим только новый DRAFT column domain, не старые annular certificates. Окончательный stop71,8126мин wall в90мин, не timesheet.

Прогноз оставшейся реализации всего scope40–64ч /5–8чд, confidence medium, передача≤8 рабочих дней от отдельного STARTED — предложение Owner. Уже включает D00614–22 и поднабор7–10, текущая подготовка повторно не начисляется; unknown D003 остаток и lifetime9–14 не вычисляются. Exact target contract/узкая дельта/technical owner/G3 и затронутый A006 нужны для соответствующей реализации. Manager/DP/gates/чужие материалы/production не менялись, публикация не поручена.
