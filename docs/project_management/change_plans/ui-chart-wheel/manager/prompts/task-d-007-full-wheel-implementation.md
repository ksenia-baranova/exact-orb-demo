# TASK-D-007 — реализация полного пассивного колеса с условной колонкой

**Актуальное прямое поручение Owner, 19.10.2026:** «Отходим от процесса / Давай стартовать разработку». По [Manager §2.25](../../manager_artifact.md#225-прямой-старт-разработки-по-решению-owner) прежнее ожидание G3 / A008 / T007 / R002 снято как условие начала. **D007 IN_PROGRESS / DRAFT, STARTED19.10.2026 22:11:37MSK**, первый scope CH-02/03 внутри FW-01. Оценки — ориентиры, отсутствующий численный budget approval не приписывается Owner. Дальнейшие смысловые gaps локализуются; прежняя постановка ниже сохраняет исторические предстартовые условия, заменённые этим прямым решением.


Сначала обнови `dev/ui-chart-wheel` из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Используй [Developer skill](../../../../../development_approach/skills/developer/SKILL.md), AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [Manager §2.24](../../manager_artifact.md#224-пакет-полного-колеса-и-переход-к-реализации).

**Текущий статус IN_PROGRESS / DRAFT.** Owner прямо разрешил начать и продолжить реализацию FW-01…06 вне прежнего ожидания формального G3 / A008 / T007 / R002. Основание — дословное решение в Manager §2.25, а не вывод Developer по одному merge. Отдельный вопрос о разрешении начать по пакету502589d уже разрешён этим более поздним поручением; повторять его не нужно. Формальный G3 / чужие approvals не объявляй полученными.

## Входы / допуск

- InputSHA / TechnicalPackageSHA подготовки: `502589dbadd382fbe39e3cf1fd763abb52ffc620`. Первый package5fdc477 и raw runs сохранены.
- [Полный FW plan](../../developer/full_wheel_implementation_plan.md), [design](../../developer/column_renderer_design_v1.md), [DRAFT ADR](../../developer/drawing_adr_column_draft.md), [готовая исполняемая постановка05](../../developer/prompts/05-full-wheel-passive-column.md), [Owner source](../../developer/owner_decision_drawing_2026-10-19.md).
- Содержательный вход: baseline v3+S1@2736e28 и более поздние подтверждённые Owner-дельты table-only / условной колонки / удаления SVG-текста категорий. A008 / T007 / R002 идут параллельно и по прямому решению Owner не блокируют начало кода. Отсутствующие TargetContractSHA / architecture approval не выдумывай; конкретные новые противоречия локализуй по затронутому work item.
- Developer предлагает **40–64 рабочих часа /5–8чд**, передача **до конца восьмого рабочего дня от отдельного STARTED**; это оставшаяся реализация, HTML/D006 внутри, исследования не начисляются заново. Диапазон сохраняется оценкой Developer; Owner разрешил код без дополнительного численного согласования до старта. CH-02/03 7–10ч уже находятся внутри, повторно не прибавлять. До прогнозируемого превышения сообщи Owner влияние; ожидание формального G3 на остальные независимые FW снято прямым решением §2.25.
- Ревизия поручения — первый опубликованный Manager commit с §2.24 / этим файлом. Фактический HEAD / AssignmentSHA, TargetContractSHA, TechnicalSHA и SourceRef допуска запиши отдельно.

Продолжай реализацию по текущему заданию и полному промту05, не заменяя её новым планом / исследованием. D007 уже STARTED19.10 22:11:37MSK в Manager-чате. Зафиксируй принятие передачи / свой resume event в Developer-сеансе с фактическим InputSHA; исходный STARTED не переписывай. Состояние D007 остаётся IN_PROGRESS, повторный общий допуск не требуется.

## Передаваемый первый участок

В этом же commit опубликованы реальные chart_state.mjs / retained facts.mjs / CSS / main.dispose и регрессии CH-02/03. [Подписанный результат / ограничения](../../developer/full_wheel_implementation_plan.md#7-task-d-007--фактическое-начало--первый-участок-ch-0203), [native evidence](../../developer/evidence/task_d007_html/README.md). Сначала сверяй полученный код и существующие tests, затем переиспользуй его; не реализуй заново уже выполненные selection/S1/five-all/live-focus.

Фактические проверки передаваемого участка:200 Node UI PASS; target Python53 passed; full pytest2959 passed,1 skipped (DEBT-CALC-001); Chrome155/Windows widths1440/768/360 PASS. Это checks первого локального участка, не whole-wheel acceptance. Native actual.json содержит raw и LF-normalized SHA-256 проверенных UI-файлов; после CRLF checkout сверяй source_lf_sha256, не объявляй различие только перевода строк новой реализацией. Точный OutputSHA — commit этой передачи, сообщённый Manager после push.

Не готовы CH-01/04 accepted cause / once / changed-birth reset / summary/editor/recovery integration и FW-02/03/04 SVG/boundary/wiring. Текущий facts.update делает сохраняющий reconcile; завершённым весь REQ-WHEEL-08 / FW-01 не объявляй. A006 блокирует только неустановленную already_applied-policy; остальные реальные work items выполняются независимо.

## Продолжение реализации по прямому разрешению Owner

1. FW-01: начать с реальных CH-02/03 — canonical source index/S1/selection и retained HTML points/aspects, five/all, houses/angles, pointer/keyboard44/live focus. Переиспользовать имеющиеся facts/session/recovery tests и fixtures. Никаких source dedup / first-match / новых domain calculations.
2. FW-03 / FW-02: настоящий passive renderer и проверенный column layout в принятых domain/criteria. Все source IDs/R, true anchors, zodiac/cusps/angles, exact/working/☌, selected/background/S1. Метки «точный/рабочий» из SVG исключены; category/type/orb остаются в HTML. Конфликтующая группа в колонку, остальные frozen; не переносить все points и не уменьшать шрифты / gap.
3. Граница renderer: настоящий leaf и живой host-owner, revision-local measure/copy-install, stale/current/fault/dispose/reentrant controls; production whitelist по принятой технической версии. Research harness не копировать целиком, generic frame system или fake/no-op renderer не вводить.
4. CH-01 / CH-04 / FW-04: A006 already_applied блокирует только затронутую cause wiring. Не выдумывать reset/preserve/provenance. Пока она отсутствует — продолжай независимые разрешённые state/HTML/geometry/boundary work items и сообщай влияние на срок; полную интеграцию готовой не объявляй.
5. FW-05 / FW-06: целевые→связанные→full Node UI и pytest по плану; delivery/module boundaries и installed resources; native browser1440/768/360 с HTML activation/focus/44, resize/font, SVG faults/late B, S1/background/source rows. Обновить собственные итоговые docs / sequences / evidence по факту.

Разрешённые пути — фактически используемые src/exact_orb/http_api/ui modules/styles/index, соответствующие tests/ui и test_ui_delivery.py / узкие helpers и собственные Developer artifacts. Engine/API/projector/golden/deps/logging semantics / whole V2 / LLM / экспорт / публичный deployment вне scope. Новые модули должны реально использоваться. Для valid counterexample — source/expected/actual и адресный возврат Manager до превышения40–64 / срока; не заменять систематический layout FAIL local-error сообщением.

## Completion / передача

Реальное принятое поведение и необходимые checks на точной версии, source/переход/исход по integration evidence, честные NOT RUN / остатки. Handoff с REQ-AS-DP, command/actual, scope/рисками, точным package / CandidateSHA только после разрешённой публикации. Reviewer полноты — Manager; независимая проверка реализации после применимого G4 назначается отдельно, исследовательский T007 не подменяет её. Owner acceptance / G4 / G5 за владельцев не объявляй.

При первичном triage / риске — ответ не позднее одного рабочего дня; эскалация Manager→Owner через +1 рабочий день просрочки, заместителя нет. Commit / push / PR / merge / сообщения другим чатам — по отдельным поручениям.
