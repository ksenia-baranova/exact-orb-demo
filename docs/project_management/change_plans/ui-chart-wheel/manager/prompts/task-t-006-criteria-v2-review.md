# TASK-T-006 — адресное review исправленных критериев v2

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

Работай в существующей ветке `test/ui-chart-wheel`; используй [skill Tester](../../../../../development_approach/skills/tester/SKILL.md).

Цель: независимо установить, устранены ли T005-R01…R03 / N01 и достаточно ли точно определены критерии для последующего ограниченного исследования. Новая постановка не является TASK-T-004 review результата исследования или независимым тестированием продукта.

Определи expected из исходного контракта и прежнего возврата до использования Developer controls. Самостоятельно проверь чувствительность положительных, отрицательных и граничных примеров; готовые 50/50 Developer — источник для сверки, не независимый oracle.

| Предмет | Проверка / различающий control |
|---|---|
| R01 / C02, G1–G7 | CSS frame / affine mapping / reference / Euclidean anchor error, состав union bounds / gap / равенство, допустимые движения и frozen elements, ring bounds / clipping. Проверь diagonal gap 1,5 / 1,5, равенство gap=2 и ниже, union-not-envelope, forbidden inner/outer, SVG clip отдельно от page overflow |
| R02 / C01, L1–L4 | Согласованность допустимой траектории / probe min(1,d), frozen geometry / без placement helper. Раздельные FEASIBLE / LOCAL_STEP / LOCAL_TIGHT, fractional / subpixel / arc-vs-chord controls и предел certificate. [18,34] accepted; [20,36] / [19,35] rejected; fraction witness может пройти один шаг, сохраняя избыточность. Отсутствующий general curved-path verifier не объявляй готовым |
| R03 / C02, F1–F2 | Что означает effective em-size 16/12 после transform; границы / ниже порога, scale, missing glyph / fallback, em=16 / ink=12. Проверь, не подменяют ли nominal font / contour / focus фактическую величину. Смысловой вопрос направь Analyst, не выбирай значение за Owner |
| N01 / C03, H1–H5 | Containment half-open Q≥44×44 в effective native hit area, clipping / overlap / actual canonical target. Bbox / center-only / element.click не являются достаточным evidence. Проверь retained/recreated/removed focus по cause и парные положительные controls; model record не является live DOM trace |

Сверь влияние исправлений на остальные ранее подтверждённые части; повторный полный Analysis / новый общий scope не требуется. Покажи точный остаток и владельца, если определения всё ещё неоднозначны, требуют неописанного oracle или противоречат друг другу.

Разрешены собственный подписанный раздел в [tester_artifact.md](../../tester_artifact.md), при необходимости новый review / evidence внутри tester/. Прежний T005 review и его отрицательный verdict / DONE сохраняются; Developer-план не исправляй. Ожидается одна адресная таблица: замечание → новая формулировка / control → independent expected → actual / evidence → устранено / остаток → owner / условие возврата. Не создавай вторую конкурирующую матрицу для того же предмета.

Применимые проверки:

```text
python -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d004_controls.py --calibrations-only
git diff --check
```

Полный task_d004_controls.py author audit проверяет именно dev-ветку; не запускай его в test-ветке как готовый универсальный gate и не ослабляй assert ради зелёного результата. Независимо сверь записанные payload / source hashes и scope средствами чтения Git. Сохрани свои команды / фактические SHA / результаты, проверь ссылки / anchors / таблицы изменённых документов. Не исполнявшиеся проверки обозначь NOT RUN.

Критерий результата: по каждому R01…R03 / N01 дан проверяемый вывод и рассмотрено влияние на прежние подтверждения. В конце явно подпиши один из фактических исходов: пригодность исправленных определений для ограниченного исследования подтверждена в указанном предмете; либо перечислены конкретные блокирующие остатки / условия исправления. Это заключение о критериях, не PASS будущего эксперимента. Чужого A004 для своего вывода не жди.

Сохрани числа 0,5 / 2 / 1 / 16 / 12 / 44 и подтверждённые Owner choices. Существенное противоречие покажи конкретным различающим примером и передай владельцу; не принимай новый риск / исключение и не меняй критерии ради PASS.

Это адресное документальное review с аналитическими controls. SVG/browser experiment, actual font / native hit / live focus measurements, production implementation, Node / pytest / HTTPS acceptance не назначены. Из аналитической согласованности не выводи runtime PASS, достижимость плотности или готовность G3.

Сохрани историю и прежние role-owned JSON / manifests. Общую сводку, DP / gates / бюджет / Gantt и чужие артефакты не меняй; текущие lifecycle-статусы ведёт Manager. Подпиши собственный результат и передай события / evidence для регистрации. До отдельного поручения commit / push / PR / внешние review replies / сообщения другим чатам не выполняй.

В итоговом handoff укажи TaskId, автора, точные входы / предмет, команды и actual results, таблицу рассмотренных замечаний, явный вывод с основанием, blockers / ограничения / NOT RUN, оценочное влияние и изменённые пути. Reviewer отчёта — Codex / Manager по полноте, версиям и traceability; он сохраняет авторский verdict.

Следующий шаг: отдельно разрешённая публикация результата → регистрация Manager. После двух положительных T006 / A004 Manager проверяет пригодность входов / среды и решает вопрос снятия зависимости TASK-D-003. **D003 остаётся BLOCKED / ResumeStatus=NOT_STARTED; T0 отсутствует.** Самостоятельно D004 DONE / APPROVED, D003 STARTED, G3 или поставку не объявляй. Повторный предметный возврат критериев относится к REWORK D004, а не к созданию нового корректирующего TaskId.
