# TASK-T-007 — проверка evidence feasibility v2

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы получай только через Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [Manager §2.18](../../manager_artifact.md) и связанные DP.

- Общий InputSHA: `072fc291f8b0db24aaa34ad7a29abc96b472162a`; версия постановки — первый опубликованный Manager commit, добавляющий §2.18 и этот промт. Фактический HEAD / AssignmentSHA запиши отдельно.
- Пакет D003: `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; Analyst A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; Tester T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17`.
- [Сводка полученного R001 r2](../review_inputs/task-r-001-r2-summary.md) — дополнительный Manager-вход из сообщения Owner. Исходный reviewer package ещё не опубликован; это не его OutputSHA и не независимо проверенные scripts/logs. По получении исходного OutputSHA Manager закрепляет его отдельно; предмет самовольно не подменяй.

Общие критерии / прежние предстартовые approvals не пересогласуются. Новый API, зависимости приложения, production implementation, изменение Owner choices / общих требований / Manager-статусов этим поручением не разрешены. Пороги 0,5 / 2 / 1 / 16 / 12 / 44 сохраняются; радиусы / движение — явные технические гипотезы до запуска, а не скрытая подгонка.
Используй [skill Tester](../../../../../development_approach/skills/tester/SKILL.md), ветку `test/ui-chart-wheel`. Это review нового результата D005, прежний T004 DONE / APPROVED сохраняется.

Статус BLOCKED, ResumeStatus=NOT_STARTED: отсутствуют опубликованный D005 и закреплённый Manager TechnicalPackageV2SHA. До снятия зависимости допустимо прочитать постановку и дать собственную оценку; STARTED review / runtime PASS не объявляй. Manager снимает блокировку после проверки точной передачи. Выходов-заполнителей не создавай.

После получения точного SHA независимо проверь только заявленные результаты D005: различие новой модели и прежней, предфиксацию входов, certificates / counterexamples на 720/448/328, C0 / fixed+movable / order / leaders / fonts, Q44 effective containment и native owner, keyboard / focused resize. Числа / радиусы, sampling / proof и discrete / continuous выводы различай. Проверяй сохранность run03 и границы negative outcomes.

Успешный production layout не является условием приёмки корректного отрицательного bounded research. Исходные факты R001 65 PASS / 1 FAIL сохраняй как reported с неизвестной причиной; если этот projector/codec запуск нужен для твоего вывода, сравни source baseline и package в одном окружении. Новое исправление или env-объяснение без evidence не выбирай.

Выход: `tester/task_t007_review.md`, собственный evidence при необходимости, signed `tester_artifact.md`. Один адресный verdict по достаточности evidence либо конкретный возврат по ошибке доказательства. Новую раскладку не разрабатывай; TEST-FIND-WHEEL-002 закрывается только по его полному критерию, не автоматически.

T007 и R002 могут работать параллельно на одном опубликованном пакете после снятия зависимости; это не независимое тестирование production кандидата после G4.
Передай подписанный handoff: TaskId / автор / точные input/output SHA, рассмотренные REQ-AS-DP, команды / фактические результаты / NOT RUN, вывод / ограничения / owners / следующий шаг Manager. Reviewer отчёта — Manager по полноте / версиям / traceability; предметное заключение сохраняет авторство.

Оценку, срок исполнения и возможность target ответа 1 рабочий день укажи для этого задания; чужую оценку не присваивай. Эскалация Manager → Owner через 1 рабочий день просрочки, заместителя нет. Календарные даты не выдумывай.

Проверь ссылки, таблицы, scope и `git diff --check`. Исторические evidence / manifests сохраняй. Commit / push / PR / сообщения другим чатам выполняются по отдельным поручениям; публикация Manager-пакета сама по себе их не разрешает.
