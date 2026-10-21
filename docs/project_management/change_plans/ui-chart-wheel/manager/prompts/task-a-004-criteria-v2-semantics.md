# TASK-A-004 — смысловая сверка уточнений критериев v2

Сначала обнови свою существующую ролевую ветку из опубликованной `change/ui-chart-wheel` через Git. Сохрани несвязанные изменения / index; не используй reset / force / очистку. Fast-forward применяй, если он возможен; содержательный конфликт или изменение предмета review передай Manager, не разрешай его сменой требований.

Используй собственный skill, прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [development-approach.md](../../../../../development_approach/development-approach.md) и [Manager §2.15](../../manager_artifact.md). Результаты других ролей получай только из опубликованного Git.

Перед исполнением проверь, что §2.15 и этот промт опубликованы в change; до публикации это подготовленная постановка, передача не выполнена. Зафиксируй фактический HEAD / SHA Manager-регистрации и проверь происхождение закреплённого пакета. Если change продвинулся, оцени diff / применимость поручения; CriteriaSHA не меняй автоматически.

- Change: `ui-chart-wheel`, текущий этап ALIGNMENT, G2 подтверждён, G3 нет.
- Общий ReviewInputSHA: `8a05b73c2af2c36043f9ede04834dd3867f4a686`.
- Единственный CriteriaSHA: **`f6f289cda25e7f228dff064175805130cc770b63`**, v2 DRAFT по авторской редакции / IN_REVIEW в текущей сводке.
- Developer InputSHA: `aa067201dc509f19bbe670778a9fa9470cf0bfb0`; прежняя v1: `11a703ed6a01eb368f0f0ba23dc23f1e90fac81f`.
- Возврат Tester TASK-T-005: `71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe`; смысловой TASK-A-003: `4055a9cb2bb18919c776c9d4e8585e2408a638c7`.
- Analyst v3: `2634b224894b1046113557bfe241f0a5f2d46f8c`; нормативный MainBaseline: `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.

Прочитай [исправленный план G/L/F/H](../../developer/task_d003_implementation_plan.md), [подписанный D004 handoff](../../developer_artifact.md), [прежний T005 review](../../tester/task_t005_review.md), [его audit](../../tester/evidence/task_t005_review.json), [A003](../../analyst_artifact.md#task-a-003), [requirements v3](../../analyst/requirements.md), [scenarios v3](../../analyst/scenarios.md) и связанные behavioral sequences / нормативные ссылки. Сопоставляй v2 с v1 на записанных SHA, не только с текущим текстом.

До STARTED сообщи собственную оценку диапазоном, confidence / assumptions и подтверди возможность целевого ответа **за 1 рабочий день после точной передачи**. Старые оценки T005 / A003 не переноси автоматически. Если срок невозможен, сразу предложи Manager конкретный срок / влияние. После подтверждения возможности зафиксируй фактический STARTED и срок передачи в своём индексе; отдельного переключения сводки Manager для начала разрешённого review не жди. Рабочий календарь / абсолютный дедлайн не выдумывай. Эскалация: Manager → Owner через 1 рабочий день просрочки, заместителя нет.

Работай в существующей ветке `analysis/ui-chart-wheel`; используй [skill Functional Analyst](../../../../../development_approach/skills/functional-analyst/SKILL.md).

Цель: проверить A003-C01…C03 / смежные исправления и явно определить, применимо ли прежнее положительное смысловое заключение TASK-A-003 к точной v2. Это узкая проверка изменённых определений и их влияния; полный новый Analysis / повторный опрос Owner по неизменившимся параметрам не назначены.

Проверь обе части контракта: нормативный baseline и Analyst v3 с принятыми Owner decisions в Manager. Сохрани REQ / AS / DP traceability; затронутые направления перечислены в T003-G04 / G05 Developer-плана, включая REQ-WHEEL-02/05/06/08…11 и соответствующие AS / DP-O-010…014. Для каждого вывода укажи точный применимый пункт, не принимай весь диапазон за автоматически проверенный.

| Предмет | Смысловая проверка / различающий пример |
|---|---|
| C01 / R02, L1–L4 | No-spread default / only-conflicting / минимальность: feasibility и один шаг 1px не заменяют весь смысл. Проверь d<1, дробные позиции, fraction witness и directional-boundary certificate при frozen остальных. Не вводится ли глобальный оптимум или иное наблюдаемое обязательство? |
| C02 / R01, G1–G7 | Совместимы ли union component AABB / Euclidean gap / reference / fixed ring-return model с принятыми порядком долгот, true anchors, leader only-if-shifted и минимальным разносом только конфликтующих? Дополнительное кольцевое ограничение — DRAFT technical proposal, не автоматически принятое продуктовое правило |
| C02 / R03, F1–F2 | 16/12 определены как effective em-size; record em=16 / ink=12 проходит size predicate. Совместима ли такая трактовка с согласованным наблюдаемым смыслом размера / читаемости, разделением ink / contour / focus / fallback? Не подписывай её как ранее принятую без source evidence |
| C03 / N01, H1–H5 | Effective hit area / half-open 44×44 и cause-specific focus. Сверь retained / removed / recreated controls, same-key restoration для current, fallback / collapse и запрет программного focus-transfer / scroll при выборе планеты. Проверь, не добавлены ли новая кнопка / collapse-действие / скрытое продуктовое исключение |

Для каждой конкретизации дай один обоснованный вывод: совместима с прежним контрактом; либо требуется адресное уточнение / решение конкретного владельца. При конфликте приведи точный REQ / AS / DP, два различающихся expected results, влияние и условие исправления. Технический алгоритм размещения за Developer не выбирай. Вопросы выбора направляй в существующий реестр через Manager, не создавай дубли DP и не принимай Owner choice самостоятельно.

Разрешён подписанный раздел TASK-A-004 в [analyst_artifact.md](../../analyst_artifact.md); при необходимости собственное дополнительное analytical evidence внутри analyst/. Требования / scenarios / behavioral sequences v3 и прежние A003 / JSON / manifests в этом узком review не переписывай. Если нужна смысловая правка контракта, передай предложение Manager для отдельного назначения.

Выход: таблица «C01…C03 / смежное R → уточнённое определение @ CriteriaSHA → REQ / AS / DP source → различающий пример / expected → совместимость / остаток / owner». В конце явно подпиши применимость прежнего положительного A003 к v2 в рассмотренном предмете либо конкретный адресный возврат с условием исправления. Численные / browser measurements не подписывай вместо Tester.

Подход — документальные проверки и аналитические примеры. Сверь Git versions / сохранение истории и разрешённого scope, ссылки / IDs / anchors / таблицы; выполни git diff --check. По необходимости можно повторить Developer calibrations-only как вспомогательную сверку, не заменяя им смысловое доказательство. Полный author audit привязан к dev-ветке; assertions ради запуска в analysis-ветке не меняй. Запиши команды / actual / NOT RUN.

Сохрани числа 0,5 / 2 / 1 / 16 / 12 / 44 и подтверждённые Owner choices. Существенное противоречие покажи конкретным различающим примером и передай владельцу; не принимай новый риск / исключение и не меняй критерии ради PASS.

Это адресное документальное review с аналитическими controls. SVG/browser experiment, actual font / native hit / live focus measurements, production implementation, Node / pytest / HTTPS acceptance не назначены. Из аналитической согласованности не выводи runtime PASS, достижимость плотности или готовность G3.

Сохрани историю и прежние role-owned JSON / manifests. Общую сводку, DP / gates / бюджет / Gantt и чужие артефакты не меняй; текущие lifecycle-статусы ведёт Manager. Подпиши собственный результат и передай события / evidence для регистрации. До отдельного поручения commit / push / PR / внешние review replies / сообщения другим чатам не выполняй.

В итоговом handoff укажи TaskId, автора, точные входы / предмет, команды и actual results, таблицу рассмотренных замечаний, явный вывод с основанием, blockers / ограничения / NOT RUN, оценочное влияние и изменённые пути. Reviewer отчёта — Codex / Manager по полноте, версиям и traceability; он сохраняет авторский verdict.

Следующий шаг: отдельно разрешённая публикация результата → регистрация Manager. После двух положительных T006 / A004 Manager проверяет пригодность входов / среды и решает вопрос снятия зависимости TASK-D-003. **D003 остаётся BLOCKED / ResumeStatus=NOT_STARTED; T0 отсутствует.** Самостоятельно D004 DONE / APPROVED, D003 STARTED, G3 или поставку не объявляй. Повторный предметный возврат критериев относится к REWORK D004, а не к созданию нового корректирующего TaskId.
