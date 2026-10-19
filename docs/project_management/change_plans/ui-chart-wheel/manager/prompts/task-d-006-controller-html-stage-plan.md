# TASK-D-006 — подготовка первого этапа реализации controller / HTML

Сначала обнови существующую ролевую ветку `dev/ui-chart-wheel` из опубликованной `change/ui-chart-wheel` через Git, сохрани несвязанные изменения / index. Чужие материалы — только Git.

Используй [Developer skill](../../../../../development_approach/skills/developer/SKILL.md), [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), AGENTS.md и [Manager §2.22](../../manager_artifact.md#222-первый-этап-controllerhtml-подготовка-ограниченного-g3).

- InputSHA: `cc4ecfff0208a15c64ae976bf5d6463cd47636ae`; TechnicalPackageV2SHA D005: `8b8c4c818147b037cb90f93a42e64eb86d809183`; AnalystContractSHA (v3 + S1): `2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`.
- Версия поручения — первый опубликованный Manager commit с §2.22 / этим промтом. Фактический HEAD / AssignmentSHA запиши отдельно.
- Источники: [D005 report](../../developer/task_d005_feasibility_report.md), [DRAFT ADR](../../developer/drawing_adr_draft.md), [план](../../developer/task_d005_implementation_plan.md), [requirements](../../analyst/requirements.md), [scenarios](../../analyst/scenarios.md), текущие src/tests. D005 передан T007/R002, повторять его эксперименты не нужно.

**Разрешено сейчас:** одна компактная подготовка конкретного первого implementation-этапа controller/HTML — объём, разбивка на work items, проверки, зависимости и собственная оценка. Результатов T007/R002 для этой независимой подготовки не жди; используй опубликованные verdict, когда они появятся, через адресную дельту. STARTED относится только к подготовке D006. Production implementation, новый geometry spike, нормативное принятие ADR и G3 этим поручением не разрешены.

Подготовь в собственном Implementation Plan один раздел / компактный связанный `developer/task_d006_controller_html_plan.md`, signed handoff в `developer_artifact.md`. Новый checker / evidence-пакет для документальной оценки не требуется.

В результате:
1. Раздели конкретные work items: accepted snapshot / once acceptance и canonical selection; revoke / local leaf failure; retained HTML points/aspects, five/all / planet-filter / независимые houses, принятый S1 и cause-specific focus. Для каждого — REQ/AS, ответственность / seam, наблюдаемый результат и существующие / необходимые проверки. Граница может быть уже, если зависимость доказана.
2. Явно отдели drawing algorithm / hit geometry / полный SVG writer и неуспешный F/E-кандидат. Не включай production-заглушки, временное ослабление критериев, новый HTTP/API, producer-provenance или преждевременный whole-wheel fallback.
3. Покажи, какие work items независимы от геометрии, какие зависят от конкретного решения R002 / принятия ADR. A006 already_applied блокирует только затронутую policy-часть; отсутствующее решение нельзя подменять значением по умолчанию. Сохрани действующие recovery / checkbox / safe-read контракты.
4. Дай собственную оценку будущей реализации / проверок: диапазон, confidence, предпосылки, срок от будущего отдельного STARTED реализации; стоимость этой подготовки укажи отдельно от runtime-работ. 6–10 часов HTML-presenter из D005 — исторический подблок внутри controller 16–24, не автоматически согласованный остаток. Не суммируй повторно D003 / D005 / design; неизвестный труд не вычитай из оценок. Полные 9–14 не подтверждены отрицательным drawing-результатом.
5. Передай короткий, конкретный пакет для решения Owner: scope первого этапа, оценка / срок, exclusions, оставшиеся зависимости. Укажи применимые approvals и DP по process.md G3. Нового выбора S1 и общей повторной Analysis не нужно.

**Reviewer / completion:** Manager — полнота, точные версии, REQ-AS-DP, отсутствие скрытого scope, ясность бюджета / зависимостей. T007/R002 уже назначены на D005 и дают применимые рекомендации без второго общего предстартового review D006. Техническое решение принимает владелец DP-O-010; scope / бюджет — Owner; допуск конкретных implementation work items — Manager после условий G3. Результат D006 — готовая оценка/план для решения, не разрешение начать код.

Оценку подготовки / confidence / возможность target ответа за один рабочий день сообщи до STARTED подготовки. Если целевой ответ невозможен — предложи обоснованный срок. Эскалация Manager → Owner через +1 рабочий день просрочки, заместителя нет. Молчание не означает approval.

Сохраняй старые handoffs / manifests / run03 / D005 evidence. Проверь scope, ссылки, таблицы и `git diff --check`; новые product tests не запускай ради одной документальной оценки. В handoff явно перечисли команды / actual / NOT RUN и следующий шаг Owner / Manager. Commit / push / PR / сообщения другим чатам — только по отдельному поручению.
