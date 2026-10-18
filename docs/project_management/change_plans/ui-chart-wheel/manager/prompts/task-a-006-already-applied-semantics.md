# TASK-A-006 — согласованное поведение already_applied и recovery

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы получай только через Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [Manager §2.18](../../manager_artifact.md) и связанные DP.

- Общий InputSHA: `072fc291f8b0db24aaa34ad7a29abc96b472162a`; версия постановки — первый опубликованный Manager commit, добавляющий §2.18 и этот промт. Фактический HEAD / AssignmentSHA запиши отдельно.
- Пакет D003: `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; Analyst A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; Tester T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17`.
- [Сводка полученного R001 r2](../review_inputs/task-r-001-r2-summary.md) — дополнительный Manager-вход из сообщения Owner. Исходный reviewer package ещё не опубликован; это не его OutputSHA и не независимо проверенные scripts/logs. По получении исходного OutputSHA Manager закрепляет его отдельно; предмет самовольно не подменяй.

Общие критерии / прежние предстартовые approvals не пересогласуются. Новый API, зависимости приложения, production implementation, изменение Owner choices / общих требований / Manager-статусов этим поручением не разрешены. Пороги 0,5 / 2 / 1 / 16 / 12 / 44 сохраняются; радиусы / движение — явные технические гипотезы до запуска, а не скрытая подгонка.
Используй [skill Functional Analyst](../../../../../development_approach/skills/functional-analyst/SKILL.md), существующую ветку `analysis/ui-chart-wheel`. Это новое задание по новому входу R001-05. TASK-A-005 DONE / APPROVED сохраняется.

Разбери ровно одну адресную связь: `already_applied → safe GET` с fresh birth, совпавшим с submitted B, против fresh matched recovery B после lost response. A005 подтверждает второй случай через активную неопределённую локальную pending-цель и отдельно не расширяет known already_applied; Reviewer предлагает согласованную policy обеих target-confirmed ветвей.

По [A005](../../analyst_artifact.md), requirements/scenarios v3, `session.mjs`, `recovery.mjs`, server outcomes и существующим tests составь cause → active local intent → freshness/match → reset → collapse → once-consumption. Различи own committed, already_applied same/different birth, superseded current, automatic current без pending, stale / failed GET, повтор publish, draft C и edit→revert. Подтверждение логической цели не доказывает автора server commit; не объявляй POST уже построившим новую карту.

Если действующий контракт даёт expected — обоснуй его без нового Owner-вопроса. При реальном новом выборе сформулируй один конкретный вопрос с различающими сценариями / последствиями. Существующий Owner-вопрос S1/S2 по ambiguity не повторяй; ответ за Owner не выбирай.

Допиши собственный `analyst_artifact.md` подписанным A006; при необходимости предложи узкую дельту в `analyst/`. Принятые requirements / sequences до разрешённого изменения не переписывай. Отсутствие R001 OutputSHA не мешает этому адресному анализу опубликованной Manager-сводки.

Статус назначения NOT_STARTED. После собственной оценки / подтверждения возможности срока зафиксируй STARTED и выполняй адресный анализ. Это не повторная полная Analysis или возврат корректного A005.
Передай подписанный handoff: TaskId / автор / точные input/output SHA, рассмотренные REQ-AS-DP, команды / фактические результаты / NOT RUN, вывод / ограничения / owners / следующий шаг Manager. Reviewer отчёта — Manager по полноте / версиям / traceability; предметное заключение сохраняет авторство.

Оценку, срок исполнения и возможность target ответа 1 рабочий день укажи для этого задания; чужую оценку не присваивай. Эскалация Manager → Owner через 1 рабочий день просрочки, заместителя нет. Календарные даты не выдумывай.

Проверь ссылки, таблицы, scope и `git diff --check`. Исторические evidence / manifests сохраняй. Commit / push / PR / сообщения другим чатам выполняются по отдельным поручениям; публикация Manager-пакета сама по себе их не разрешает.
