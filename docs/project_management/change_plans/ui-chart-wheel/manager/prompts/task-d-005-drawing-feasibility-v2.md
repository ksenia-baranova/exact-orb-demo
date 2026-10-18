# TASK-D-005 — drawing feasibility v2 и ревизия DRAFT ADR

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы получай только через Git. Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [Manager §2.18](../../manager_artifact.md) и связанные DP.

- Общий InputSHA: `072fc291f8b0db24aaa34ad7a29abc96b472162a`; версия постановки — первый опубликованный Manager commit, добавляющий §2.18 и этот промт. Фактический HEAD / AssignmentSHA запиши отдельно.
- Пакет D003: `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; Analyst A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; Tester T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17`.
- [Сводка полученного R001 r2](../review_inputs/task-r-001-r2-summary.md) — дополнительный Manager-вход из сообщения Owner. Исходный reviewer package ещё не опубликован; это не его OutputSHA и не независимо проверенные scripts/logs. По получении исходного OutputSHA Manager закрепляет его отдельно; предмет самовольно не подменяй.

Общие критерии / прежние предстартовые approvals не пересогласуются. Новый API, зависимости приложения, production implementation, изменение Owner choices / общих требований / Manager-статусов этим поручением не разрешены. Пороги 0,5 / 2 / 1 / 16 / 12 / 44 сохраняются; радиусы / движение — явные технические гипотезы до запуска, а не скрытая подгонка.
Используй [skill Developer](../../../../../development_approach/skills/developer/SKILL.md), существующую ветку `dev/ui-chart-wheel`. D003 остаётся отдельным завершённым по исполнению исследованием на review; его результат / elapsed / старый бюджет не переписывай.

Первое действие — собственная оценка D005: диапазон часов/чд, confidence, предпосылки, timebox experiment, stop conditions, состав результата, предлагаемый срок от отдельного STARTED D005. Отдельно укажи включение нового этапа в прогноз 9–14, слот HTML-presenter и неизвестность фактического остатка D003. Ориентир Reviewer 1,25–2,25 чд — вход, не твой согласованный бюджет.

Подготовка оценки / плана поручена сейчас. Исполнение нового spike и ревизии ADR начинается после явного согласования Owner scope / твоей оценки / срока: запиши источник допуска и отдельный STARTED. Назначение задания / прошлое разрешение D003 / текущий commit не расширяют бюджет автоматически. Owner выбрал S1 (§2.19 / DP-O-013); узкая дельта поручена A007. A006 / A007 не блокируют оценку или независимую геометрию. Источник выбора — первый опубликованный Manager commit с §2.19; до публикации не подменяй его прежним InputSHA.

Разрешённый будущий research scope после допуска:
1. Ревизия собственных `developer/drawing_adr_draft.md` / technical sequences / Implementation Plan по R001-01…04: revoke / removal / HTML B / guarded dispose; защита DOM от старой async revision; sync/async local failure; retained HTML controls. Предлагай механизм с инвариантами, а не принимай конкретный AbortSignal как уже утверждённый ADR.
2. Другая order-preserving раскладка конфликтующих групп и отдельное размещение angle labels. Сравни F (радиусы) и E (геометрия целей) там, где glyph-centred вариант не проходит. Фиксируй новую модель / разрешённое движение / bounds / fixtures до измерений; допускаемые изменения относительно D004 описываются явно. Fixed-ring 16°/40° не дорабатывай.
3. Сначала аналитические certificates либо точные контрпримеры для 720 / 448 / 328 × sparse / F1 / F3 / F3-max: fixed+movable geometry, C0, cyclic order/0°, gap/clip, Q44 containment, minimality. Grid optimum не выдаётся за continuous bound; успешная раскладка — lower bound, не доказательство максимума.
4. Затем ограниченный новый browser run04 в собственном `developer/evidence/task_d005_feasibility/`, native owner/outcome / keyboard / resize focused target / парные positive-negative controls. Если E меняет наблюдаемый смысл, останови только browser-часть E до адресного Analyst/Owner ответа; независимую часть продолжай.

Отрицательный исход отдельной рамки допустим с корректным evidence и точным пределом. Полная production реализация, mounted acceptance и неограниченный подбор параметров не входят. Не вводи scipy/solver/app dependencies автоматически из reviewer-среды.

Выход после допуска / исполнения: `developer/task_d005_feasibility_report.md`, собственный evidence, обновлённый DRAFT ADR / technical sequences / Implementation Plan и signed `developer_artifact.md`. Сохраняй d24a24e / run03 неизменными; новый пакет имеет собственный OutputSHA. Свяжи реальные Owner choices / A006 только по опубликованным версиям, unresolved policy оставь явно условной.

После передачи пакета назначены T007 (evidence) и R002 (исправленный ADR / boundary). Они проверяют полученный результат, не проводят новый общий предстартовый review. Точный TechnicalPackageV2SHA закрепляет Manager; G3 / production этим не разрешаются.
Передай подписанный handoff: TaskId / автор / точные input/output SHA, рассмотренные REQ-AS-DP, команды / фактические результаты / NOT RUN, вывод / ограничения / owners / следующий шаг Manager. Reviewer отчёта — Manager по полноте / версиям / traceability; предметное заключение сохраняет авторство.

Оценку, срок исполнения и возможность target ответа 1 рабочий день укажи для этого задания; чужую оценку не присваивай. Эскалация Manager → Owner через 1 рабочий день просрочки, заместителя нет. Календарные даты не выдумывай.

Проверь ссылки, таблицы, scope и `git diff --check`. Исторические evidence / manifests сохраняй. Commit / push / PR / сообщения другим чатам выполняются по отдельным поручениям; публикация Manager-пакета сама по себе их не разрешает.
