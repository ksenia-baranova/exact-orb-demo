# TASK-T-008 — независимая сверка переноса ui-chart-wheel

Сначала обнови свой Tester checkout из опубликованной `change/ui-chart-wheel` через Git. Репозиторий: https://github.com/ksenia-baranova/exact-orb-demo.git. Сохрани свои local/index/stash; не используй reset/force/clean и не читай чужие worktrees. Работай в `test/ui-chart-wheel` по Tester skill `docs/development_approach/skills/tester/SKILL.md` и процессу `docs/development_approach/process/process.md`.

**Назначение:** TASK-T-008. Reviewer — Manager по полноте и точным версиям; независимый verdict принадлежит Tester. Прочитай [Manager §2.28](../../manager_artifact.md#228-перенос-требований-и-sequences-по-прямому-поручению-owner) / [§2.29](../../manager_artifact.md#229-публикация-переноса-и-точный-вход-t008). Статус NOT_STARTED до фактического STARTED; до него сообщи собственную оценку, confidence и срок передачи. При влиянии на срок адресат — Manager/Owner.

## Закреплённые входы

- **TransferSHA / AssignmentSHA:** коммит публикации, содержащий эту редакцию поручения и Manager §2.29; полный SHA передан Owner в чате после push. Зафиксируй его отдельно от более позднего HEAD. Более новые commits не меняют предмет сверки автоматически.
- **SourceSHA:** `883b6d3a47f7113e44ede73c9ad16b40f15bbdaf` — состояние до переноса; AnalystContractSHA2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 плюс уже полученные поздние Owner-решения.
- **RetestedSHA:** `99741958b4bbee8884505920f4a02f2f19dea3e3`. **Tester OutputSHA:** `f930c864d6a416acff8a49081585950853b931f9`.
- `analyst/transfer_map.md` и `manager/transfer_manifest.json` относительно папки change: source→target, хеши, сохранённые IDs, отделение архивных схем.
- Owner19–21.10 / Manager §2.27, подписанные `developer/owner_decision_*2026-10-20.md`, исходные тексты требований и схем через `git show SourceSHA:<path>`. Их рабочие копии уже удалены из change.

## Предмет сверки

Проверь существующие целевые файлы, не жди нового создания A008 или повторного переноса sequences из D008:

- `docs/requirements/current/ui/chart-wheel.md` — REQ-WHEEL-01…11.
- `docs/requirements/current/ui/birth-form-and-facts.md` — REQ-UI-01…11; 02/07 сохранены, остальные перечисленные дельты применены.
- `docs/requirements/current/ui/scenarios.md` — AS-UI-01…23 + AS-WHEEL-01…30; только AS-UI-22 меняется в исходном наборе M1-7.
- `docs/sequence_diagrams/ui/` — три behavioral и пять актуальных technical PUML; `docs/sequence_diagrams/research/ui-chart-wheel/` — три ARCHIVED/SUPERSEDED, не текущий контракт.

Сопоставь каждый перенесённый REQ/AS/sequence с исходником и явными поздними решениями Owner. Это синхронизация принятых изменений, а не побайтовый перенос всего старого v3. Особо проверь passive SVG / HTML-only выбор; internal house rows вместо колонки; отсутствие SVG-слов категорий; отдельное чтение аспекта с участниками/их опубликованными домами и возвратом focus; first-five/all трёх таблиц; одинаковое once-подтверждение fresh matched live target и already_applied при fresh GET birth=B, collapse только при draft=B; S1 до любого subset/filter. Source факты, DTO/order, HTTP recovery и неизменённые обязательства M1-7 не должны потеряться.

Независимо проверь полноту source→target, IDs/anchors/ссылки, отсутствие13 source-копий, корректность разделения8 текущих/3 исторических схем и сохранность raw evidence/manifests. Проверь структурный синтаксис PUML; renderer используй, если доступен, иначе явно NOT RUN. Не приписывай результат своей проверки старому manifest validation.

## Evidence и границы

- Сверь `git diff SourceSHA..TransferSHA -- src tests` и применимость14 source fingerprints к RetestedSHA9974195. Runtime ранее проверен:229 UI tests /2959 pytest +1legacy DEBT-CALC-001 skip; native Chrome/Yandex1440/768/360,6/6 cases /672checks.
- Если изменения действительно только документальные и прежние runtime checks применимы, новый полный runtime-цикл не обязателен. Реальное изменение expected behavior или расхождение с кодом требует конкретного finding и обоснованного адресного retest; не маскируй его под механический перенос.
- TEST-FIND-WHEEL-004 остаётся CLOSED по retest. TEST-FIND-WHEEL-002 / geometry precision остаются OPEN/INDETERMINATE, разрешённая отсрочка — DEBT-UI-004. Не превращай долг в PASS и не открывай004 без нового воспроизводимого дефекта.
- Технический ADR остаётся отдельным DRAFT / неполученным решением: перенос PUML не равен принятию ADR. Дай отдельные выводы о fidelity переноса, применимости runtime evidence и оставшихся условиях merge. Сверка переноса не ждёт создания ADR.
- При необходимости обнови собственный defects-реестр ссылкой на решение Owner / DEBT-UI-004; registry SHA в main не выдумывай.

## Результат

`docs/project_management/change_plans/ui-chart-wheel/tester/transfer_review.md` и signed handoff в `tester_artifact.md`: точные TransferSHA/SourceSHA/RetestedSHA, REQ/AS/sequence→source→target→verdict, команды/actual, ограничения и конкретные исправления либо их отсутствие.

Не меняй production, требования, Developer/Manager или общий реестр вместо владельцев; не заявляй Owner acceptance / G5 / universal geometry PASS. Commit/push/merge и сообщения другим чатам отдельно. Передай Manager готовый результат и после разрешённой публикации точный OutputSHA.
