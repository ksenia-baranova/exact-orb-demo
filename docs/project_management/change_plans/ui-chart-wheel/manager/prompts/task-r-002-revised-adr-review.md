# TASK-R-002 — review исправленного DRAFT ADR и новой technical proposal

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы получай только через Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [Manager §2.18](../../manager_artifact.md) и связанные DP.

- Общий InputSHA: `072fc291f8b0db24aaa34ad7a29abc96b472162a`; версия постановки — первый опубликованный Manager commit, добавляющий §2.18 и этот промт. Фактический HEAD / AssignmentSHA запиши отдельно.
- Пакет D003: `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; Analyst A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; Tester T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17`.
- [Сводка полученного R001 r2](../review_inputs/task-r-001-r2-summary.md) — дополнительный Manager-вход из сообщения Owner. Исходный reviewer package ещё не опубликован; это не его OutputSHA и не независимо проверенные scripts/logs. По получении исходного OutputSHA Manager закрепляет его отдельно; предмет самовольно не подменяй.

Общие критерии / прежние предстартовые approvals не пересогласуются. Новый API, зависимости приложения, production implementation, изменение Owner choices / общих требований / Manager-статусов этим поручением не разрешены. Пороги 0,5 / 2 / 1 / 16 / 12 / 44 сохраняются; радиусы / движение — явные технические гипотезы до запуска, а не скрытая подгонка.
Используй роль Technical Reviewer по roles.md §7 в отдельном сеансе от автора D005; другая модель рекомендуется. Это новый review изменённого пакета, а не повтор R001 по старой версии.

Статус BLOCKED, ResumeStatus=NOT_STARTED: D005 / точный TechnicalPackageV2SHA ещё отсутствуют. До опубликованной передачи допустима собственная оценка по постановке; содержательное review / STARTED не объявляй. После проверки входов Manager снимает блокировку. Пустого отчёта не создавай.

Проверь изменения по R001-01…05: согласованный порядок revoke / removal / HTML / guarded dispose; async DOM writes и settlement; sync/async leaf failures; retained HTML/SVG controls; once-cause и policy со ссылкой на опубликованный A006 либо явный unresolved item. Уточни технические alternatives и соблюдение архитектурных границ.

Сопоставь новый drawing proposal / certificates / ограничения с D005 и принятыми критериями. Не требуй положительного результата там, где передан корректный counterexample. Не выдавай grid upper bound за continuous proof; F/E — сравниваемые варианты, не заранее выбранное продуктовое исключение.

Выход: `manager/task_r002_technical_review.md` с авторством Technical Reviewer, точным SHA, адресным verdict по ревизии / остаткам, условиями принятия ADR владельцем и следующими implementation checks. T007 независимо проверяет evidence; его verdict для начала своей независимой части не жди.

ADR остаётся DRAFT до явного решения архитектурного владельца / DP-O-010; Owner choices / бюджет / G3 за владельца не принимай.
Передай подписанный handoff: TaskId / автор / точные input/output SHA, рассмотренные REQ-AS-DP, команды / фактические результаты / NOT RUN, вывод / ограничения / owners / следующий шаг Manager. Reviewer отчёта — Manager по полноте / версиям / traceability; предметное заключение сохраняет авторство.

Оценку, срок исполнения и возможность target ответа 1 рабочий день укажи для этого задания; чужую оценку не присваивай. Эскалация Manager → Owner через 1 рабочий день просрочки, заместителя нет. Календарные даты не выдумывай.

Проверь ссылки, таблицы, scope и `git diff --check`. Исторические evidence / manifests сохраняй. Commit / push / PR / сообщения другим чатам выполняются по отдельным поручениям; публикация Manager-пакета сама по себе их не разрешает.
