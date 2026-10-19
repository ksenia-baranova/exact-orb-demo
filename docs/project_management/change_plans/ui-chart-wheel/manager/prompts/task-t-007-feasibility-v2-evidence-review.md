# TASK-T-007 — проверка опубликованной полной композиции / критериев колонки

Сначала обнови `test/ui-chart-wheel` из опубликованной `change/ui-chart-wheel` через Git. Используй [skill Tester](../../../../../development_approach/skills/tester/SKILL.md). Сохрани несвязанные изменения / index; чужие материалы только из опубликованного Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [Manager §2.24](../../manager_artifact.md#224-пакет-полного-колеса-и-переход-к-реализации).

**Статус NOT_STARTED. Manager явно обновил не начатое поручение на новый предмет; это не verdict старого review.** Прежняя версия задания / research subject D005 @8b8c4c8 сохранены в истории @07bb56b; исследовать весь D005 заново для старта нового кода не требуется. Если уже есть локальная работа по прежнему предмету, сохрани её отдельно и явно оцени применимость; не выдавай её за review нового SHA.

- **ReviewInputSHA / TechnicalPackageSHA: `502589dbadd382fbe39e3cf1fd763abb52ffc620`.** Первый package commit 5fdc4771d97307b2803fbe0f20a4833abfec645b; follow-up 502589d меняет только publication helper / metadata / handoff, не raw research.
- Ролевой InputSHA подготовки 07bb56ba5d49ec76de64df41ad80d175fbe90a2d; исходный AnalystContractSHA 2736e2848c977ec4c770a9a4dec2a0d7c1b62a71. Точный TargetContractSHA A008 ещё ожидается; поздние Owner choices уже подтверждены, см. [source](../../developer/owner_decision_drawing_2026-10-19.md).
- Ревизия поручения — первый опубликованный Manager commit с §2.24 / этой редакцией. Фактический HEAD / AssignmentSHA фиксируй отдельно от предмета.
- Прочитай [design](../../developer/column_renderer_design_v1.md), [DRAFT ADR](../../developer/drawing_adr_column_draft.md), [FW plan](../../developer/full_wheel_implementation_plan.md), [signed publication handoff](../../developer_artifact.md#публикация-подготовки-полного-колеса--отдельное-поручение-owner), [evidence README](../../developer/evidence/column_full_composition_v1/README.md).
- Git text=auto менял CRLF→LF. [Publication map](../../developer/evidence/column_full_composition_v1/publication_2026-10-19.json) / [read-only publication audit](../../developer/evidence/column_full_composition_v1/publication_audit.py) восстанавливают raw hash в памяти; не переписывай manifests / snapshots ради checkout.

Работай параллельно второй проверке / адресной дельте A008. Не ожидай результата другого reviewer для своей независимой части. После появления точного A008 оцени только затронутую semantic applicability; новую общую предстартовую проверку не назначай. До STARTED сообщи собственную оценку / confidence / выполнимость target ответа в один рабочий день. Если невозможно — назови конкретный срок; эскалация Manager→Owner через +1 рабочий день просрочки, заместителя нет.

Проверь достаточность опубликованного evidence перед реализацией:
1. Заявленные 29/29 full measured compositions, independent C0/order/row/leader/clip/no-shared-segments; реальность 13 native +4 analytic +3 route controls и negative runs. Отличи 29 configurations от 29 независимых domain charts.
2. Gap≥2 / em16/12 / anchor≤0,5 / frozen labels / source IDs/R/☌ / условный trigger колонки / seam0 / selected/default/background. Точные predicates / новый column domain и compactness не подменяют old annular return молча.
3. Render boundary28/28 и предел isolated стенда. Baseline Node188 PASS не является feature testing будущего колеса. HTML44 / runtime S1 / реальная session integration ещё должны проверяться после реализации.
4. Покрытие обязательных критериев и достаточность будущих Developer checks FW-01…06, применение A008. Existing gaps классифицируй: ошибка доказательства текущего пакета, конкретное implementation check или настоящее продуктовое противоречие. Полного mounted production PASS от исследовательского пакета не требуй.

Выход — `tester/task_t007_review.md`, собственный evidence при необходимости и signed `tester_artifact.md`. Один адресный verdict о достаточности / условиях применения; при блокере — точные source / expected / actual / затронутый FW и условие исправления. Старые FAIL остаются историческими; TEST-FIND-WHEEL-002 не закрывай без его критерия. Повторные запуски делай в собственном каталоге с provenance, не `--write` в чужом evidence.

В handoff укажи команды / actual / NOT RUN, точные версии и следующий шаг Manager. Commit / push / PR / сообщения другим чатам — по отдельным поручениям.
