# TASK-R-002 — review пассивного renderer и критериев колонки перед реализацией

Сначала получи актуальную `change/ui-chart-wheel` через Git в отдельную reviewer-копию https://github.com/ksenia-baranova/exact-orb-demo.git. Используй роль Technical Reviewer по [roles.md §7](../../../../../development_approach/roles.md#7-technical-reviewer), в отдельном сеансе от автора; другая модель рекомендуется. Сохрани несвязанные изменения / index; чужие материалы только из опубликованного Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [Manager §2.24](../../manager_artifact.md#224-пакет-полного-колеса-и-переход-к-реализации).

**Статус NOT_STARTED. Manager явно обновил не начатое поручение на новый предмет; это не verdict старого review.** Прежняя версия задания / research subject D005 @8b8c4c8 сохранены в истории @07bb56b; исследовать весь D005 заново для старта нового кода не требуется. Если уже есть локальная работа по прежнему предмету, сохрани её отдельно и явно оцени применимость; не выдавай её за review нового SHA.

- **ReviewInputSHA / TechnicalPackageSHA: `502589dbadd382fbe39e3cf1fd763abb52ffc620`.** Первый package commit 5fdc4771d97307b2803fbe0f20a4833abfec645b; follow-up 502589d меняет только publication helper / metadata / handoff, не raw research.
- Ролевой InputSHA подготовки 07bb56ba5d49ec76de64df41ad80d175fbe90a2d; исходный AnalystContractSHA 2736e2848c977ec4c770a9a4dec2a0d7c1b62a71. Точный TargetContractSHA A008 ещё ожидается; поздние Owner choices уже подтверждены, см. [source](../../developer/owner_decision_drawing_2026-10-19.md).
- Ревизия поручения — первый опубликованный Manager commit с §2.24 / этой редакцией. Фактический HEAD / AssignmentSHA фиксируй отдельно от предмета.
- Прочитай [design](../../developer/column_renderer_design_v1.md), [DRAFT ADR](../../developer/drawing_adr_column_draft.md), [FW plan](../../developer/full_wheel_implementation_plan.md), [signed publication handoff](../../developer_artifact.md#публикация-подготовки-полного-колеса--отдельное-поручение-owner), [evidence README](../../developer/evidence/column_full_composition_v1/README.md).
- Git text=auto менял CRLF→LF. [Publication map](../../developer/evidence/column_full_composition_v1/publication_2026-10-19.json) / [read-only publication audit](../../developer/evidence/column_full_composition_v1/publication_audit.py) восстанавливают raw hash в памяти; не переписывай manifests / snapshots ради checkout.

Работай параллельно второй проверке / адресной дельте A008. Не ожидай результата другого reviewer для своей независимой части. После появления точного A008 оцени только затронутую semantic applicability; новую общую предстартовую проверку не назначай. До STARTED сообщи собственную оценку / confidence / выполнимость target ответа в один рабочий день. Если невозможно — назови конкретный срок; эскалация Manager→Owner через +1 рабочий день просрочки, заместителя нет.

Проверь техническую пригодность текущего проекта:
1. Revision-local measurement surface / guarded clone-install: lifecycle, current/stale/reentrant, token повторно после clone, failed-lease revoke, sync/async local failure, dispose idempotence, граница HTML/controller faults. Full attribute/value whitelist и отсутствие global DOM обходов — обязательные implementation checks, не готовый sanitizer из harness.
2. Достаточность / стоимость более простого passive SVG protocol по сравнению с прежним value-frame draft. Нет входящих SVG selection intents, SVG Q44 или отдельного SVG-focus; HTML selection / S1 / accepted snapshot и async write isolation сохраняются.
3. Technical column domain / row objective / aux compactness / routing bridges, сохранение Owner rules и numeric thresholds. Укажи настоящие условия принятия ADR / DP-O-010/011/012; не требуй старый annular return для нового выбранного domain.
4. В одном verdict выдели блокеры именно FW-01…06 и независимость CH-02/03 от renderer / A006. Дай применимые implementation checks и точные условия принятия технической версии. Без нового общего исследования / третьего proposal; реальный дефект эскалируй адресно.

Выход — `manager/task_r002_technical_review.md`, автор / модель / независимость, exact SHA, рассмотренные REQ-AS-DP, verdict / limitations / conditions. Не переписывай чужой ADR, Owner choices / budget / lifecycle. ADR остаётся DRAFT до явного решения владельца; G3 подтверждает Manager после всех применимых условий.

В handoff укажи команды / actual / NOT RUN, точные версии и следующий шаг Manager. Commit / push / PR / сообщения другим чатам — по отдельным поручениям.
