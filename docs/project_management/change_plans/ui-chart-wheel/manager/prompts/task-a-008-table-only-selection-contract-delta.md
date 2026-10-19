# TASK-A-008 — выбор только через таблицы, неинтерактивное SVG

Сначала обнови `analysis/ui-chart-wheel` из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы — только опубликованный Git.

Используй [skill Functional Analyst](../../../../../development_approach/skills/functional-analyst/SKILL.md), AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [Manager §2.23](../../manager_artifact.md#223-owner-выбор-только-через-таблицы-и-адресная-дельта-a008) / DP-O-008 (ревизия Owner от 19.10.2026). Повторного выбора способа управления не требуется.

- InputSHA: `dff5757e1b7b4896f8e1e9395fe61aaaaa4327e3`; прежний опубликованный AnalystContractSHA (v3 + S1) `2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`; D005 `8b8c4c818147b037cb90f93a42e64eb86d809183`.
- Источник нового Owner-решения — первый опубликованный Manager commit с §2.23 / ревизией DP-O-008; фактический HEAD / AssignmentSHA фиксируй отдельно. Старый AnalystContractSHA — baseline, новая адресная версия пока не создана.
- A007 DONE / APPROVED сохраняется для своей версии. A008 — связанное новое задание по изменению входного scope, не REWORK корректного A007 и не повтор полной Analysis. A006 already_applied не расширяй.

Подготовь узкую дельту собственных change requirements / scenarios / затронутых behavioral sequences, signed handoff в `analyst_artifact.md`. Нормативные current/ / main ADR / src / tests и чужие artifacts не меняй.

Область дельты:
1. Выбор планеты / однозначного аспекта и снятие выбора выполняются только через HTML-таблицы, pointer и keyboard. SVG отображает состояние выбора, но его points / линии / ☌ не создают selection от click / tap / Enter / Space и не являются отдельными keyboard controls.
2. Сохрани все прежние правила: взаимоисключающий planet/aspect selection, повторное снятие, отбор всех аспектов планеты, одна строка выбранного аспекта, five/all / независимые houses, точные опубликованные данные / порядок, background, S1, reset / accepted reconcile / draft / resize / отсутствие автоматической прокрутки и переноса фокуса при активации.
3. Сохрани визуальную обратную связь на колесе: подсветку выбранного point / пары, оформление линии / ☌, точные долготы, R и читаемые метки, минимальный разнос только конфликтующих элементов / order / leaders. Выбор с таблиц и ошибка SVG не меняют расчёт / HTTP и не скрывают HTML.
4. SVG-цели нажатия Q44, проверки native owner/outcome и отдельной SVG keyboard/focus-навигации исключаются из целевого интерактивного scope. У таблиц остаются доступное управление / видимый focus / согласованные размеры целей; у SVG — текстовое название / описание и доступные факты. Не ослабляй автоматически шрифты / gap / anchor / читаемость / visual displacement или S1.
5. Пройди связанные REQ-WHEEL-04/07/08/10, REQ-UI-06 и все AS / sequences, где действие «с колеса», hit target или SVG-focus влияет на expected. Перечень affected установи по источникам, не ограничивайся заменой одной фразы. Сохрани unaffected пункты и IDs / историю. Новые данные не генерируй ради старых исследований; D003/D005 evidence не редактируй.

В handoff: точная дельта REQ-AS-DP и affected/unaffected, подтверждение соответствия Owner-выбору, различающие expected (выбор из HTML обновляет SVG; SVG activation ничего не выбирает; keyboard только в доступных HTML controls; S1 / failed-read / reset сохраняются), точные версии / команды / actual / NOT RUN. Старая ошибка попадания SVG не становится PASS: это исторический результат исключённой функции.

Reviewer — Manager: полнота / exact version / traceability / отсутствие изменения сохраняемого поведения. Результат после публикации получает новый AnalystContractSHA для D006 / применимых частей T007/R002. Независимые reviews старого D005 и подготовка оценки не ждут этой дельты; финальный G3 требует актуальных применимых версий.

До STARTED сообщи собственную оценку / confidence и возможность target ответа за один рабочий день; не присваивай прежние сроки. Эскалация Manager → Owner через +1 рабочий день просрочки, заместителя нет. В конце явно назови следующий шаг Manager.

Проверь ссылки, таблицы, scope и `git diff --check`. Старые handoffs / manifests сохраняй; новый evidence checker не обязателен для документальной дельты. Commit / push / PR / сообщения другим чатам — по отдельным поручениям.
