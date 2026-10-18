# TASK-A-007 — узкая дельта требований по выбранному Owner S1

Сначала обнови существующую ветку `analysis/ui-chart-wheel` из опубликованной `change/ui-chart-wheel` через Git; сохрани несвязанные изменения / index. Чужие материалы получай только через Git.

Используй [skill Functional Analyst](../../../../../development_approach/skills/functional-analyst/SKILL.md), [process.md](../../../../../development_approach/process/process.md) и [Manager §2.19 / DP-O-013](../../manager_artifact.md).

InputSHA: `0e590fa23d6c3f31d59a59cd0f7cb5be3509d160`. Дополнительный вход — явный ответ Owner «S1» в текущем диалоге, зарегистрированный в §2.19 / поле решения DP-O-013; версия постановки — первый опубликованный commit с §2.19 и этим промтом. До публикации Manager-поручения не представляй локальную запись как опубликованную. Фактические HEAD / AssignmentSHA сохрани отдельно.

A005 @ `4057d6ed37b24e082a2a4089eb7104da80d17ee5` остаётся DONE / APPROVED. Это новая дельта по принятому продуктовому решению, не REWORK A005. A006 по already_applied сохраняет свой отдельный предмет.

Задача: внести ровно выбранное правило S1 из DP-O-013 в собственную change-редакцию `analyst/requirements.md`, `analyst/scenarios.md` и затронутую behavioral sequence 002; при реальной необходимости адресно синхронизировать другие собственные ссылки. Допиши signed A007 в analyst_artifact.md. Нормативный current/ и main ADR не переносить на этом этапе.

Трассировка: REQ-WHEEL-04/07/08 и доступное сообщение REQ-WHEEL-10, исходные факты REQ-UI-06; AS-WHEEL-28/29/30 и связанные controls. Покажи точную дельту и влияние, сохрани прочие принятые Owner choices.

Различающие сценарии: unique / duplicate / reversed duplicate / mixed category-orb; pair+type и иной type; unique selected aspect → ambiguous; planet selection при неоднозначных её аспектах; accepted DTO против failed read; natal / cosmogram; обычные five/all и planet-filter; сохранение expansion / draft и unaffected pairs. Все source rows / DTO order / from-to / значения сохраняются. Не подменять ambiguity исчезновением или whole-wheel failure; новое исключение S1 описывается явно.

Выбор S1 повторно у Owner не запрашивай и S2 не внедряй. Новая API identity / validation / frontend recalculation / deduplication и production code не входят. Вопросы drawing feasibility, budget и already_applied не расширяют это задание.

Reviewer результата — Codex / Manager по полноте, точным версиям и REQ-AS-DP traceability. Completion: новая адресная редакция / signed handoff / явные scenario expected / source Owner evidence / точные изменённые пути; старые A005 / A006 результаты и история сохранены. Собственное соответствие сценариев принятому S1 обоснуй, runtime PASS не объявляй.

Статус NOT_STARTED. До STARTED сообщи собственную оценку / confidence / возможность целевого ответа за 1 рабочий день; затем зафиксируй фактический STARTED. Эскалация Manager → Owner через +1 рабочий день просрочки, заместителя нет; абсолютный рабочий календарь не выдумывай. Работа независима от геометрии D005.

Проверь ссылки / anchors / таблицы / git diff --check. В конце укажи следующий шаг Manager и фактические проверки / NOT RUN. Commit / push / PR / сообщения другим чатам требуют отдельного поручения.
