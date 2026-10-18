# TASK-T-004 — независимая проверка evidence исследовательского пакета

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git; сохрани несвязанные изменения / index, без reset / force / очистки. Проверь фактический HEAD и [Manager §2.17](../../manager_artifact.md). Получай чужие материалы только из опубликованного Git.

Задание относится к **уже выполненному исследованию**, без повторного общего предстартового review критериев. Оно не назначает production implementation, G3 или независимое тестирование production кандидата.

- Общий ReviewInputSHA: **`030826fd4e6bfa9613ad84ba7ed32adc15fddcd9`**.
- Единственный TechnicalPackageSHA: **`d24a24e04be32d0522674735388e9d2ea3e65c93`**; merge 030826f имеет родителей 8fb2577 / d24a24e.
- Developer InputSHA / поручение: `8fb25770169166a3a4e94110eee684bd8b116474`.
- CriteriaSHA: `f6f289cda25e7f228dff064175805130cc770b63`; T006 `435337f49b200ca308ae9620efa9902adf1677f9`; A004 `5de9e66c26496880f714f61f78126972dee4fbdd`.
- Analyst v3 `2634b224894b1046113557bfe241f0a5f2d46f8c`, нормативный MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.

Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) v3 / связанные sequences, [research report](../../developer/task_d003_research_report.md), [handoff](../../developer_artifact.md), [DRAFT ADR](../../developer/drawing_adr_draft.md), [checks](../../developer/checks.md), [findings](../../developer/findings.md), [матрицу v2](../../developer/evidence/task_d003_research/matrix_v2.md), [manifest](../../developer/evidence/task_d003_research/package_manifest.json). Фактический HEAD / SHA постановки сохраняй отдельно от закреплённого TechnicalPackageSHA; движение change не подменяет предмет автоматически.

До STARTED сообщи собственную оценку / confidence / assumptions и возможность целевого ответа за **1 рабочий день после точной передачи**. Старые оценки другого задания не переноси. Если target невозможен, сразу предложи Manager конкретный срок / влияние; без выдуманного рабочего календаря. Затем зафиксируй фактический STARTED в своём handoff и выполняй назначенную работу, не ожидая verdict другой роли. Эскалация +1 рабочий день просрочки, Manager → Owner; заместителя нет.

Используй [skill Tester](../../../../../development_approach/skills/tester/SKILL.md), существующую ветку `test/ui-chart-wheel`. Это конкретизация уже созданного TASK-T-004, не новое задание с новым ID.

Цель: установить, воспроизводимы ли существенные факты / контрпримеры D003 и достаточны ли выводы **как результат ограниченного исследования**. Корректный отрицательный кандидат может быть принят как исследовательский результат; требовать полного drawing PASS / реализации всех будущих checks ради DONE исследования не нужно.

Сформируй независимые expected из требований / принятых G/L/F/H и source evidence до доверия runner verdict. Проверь:

1. Состав manifest / pinned SHA, authoritative **run03** с fixtures/spec v2 против exploratory run01 / run02, source snapshots / отдельные followup02. Не суммируй попытки как одну matrix. Проверь scope исправления F3 (angles наследуются из F1), отдельный close-angle F3-max; пороги / радиусы не подгонялись под actual.
2. 24 клетки, 25 screenshots и фактическую связь criterion → record → screenshot / environment / output. Чувствительные samples: sparse360 Q44 8/16, F3-max360 3/20 и 68/340 неверных native probes; positive wide / no-overlay / clip и keyboard retained-pair. Сводные 7 446 / 1 679 native и 438 / 0 keyboard должны соответствовать данным, не означают общий PASS.
3. Границу geometry: ранний runner не проверял fixed↔fixed, drawing_audit_v2 учитывает это. Проверь independent true anchors / C0 / component bounds / clip / font metrics / минимальность; 0,25px witness отвергает excessive placement, STEP_PASS не доказывает весь LOCAL_TIGHT.
4. Scope native hit / actual event target / keyboard / focus versus model records; half-open Q / integer click versus fractional pointerdown. Отдели browser controls от универсального containment proof / generic curved-path verifier / actual touch и mounted production.
5. T003-G01…04: B-fault HTML / image retirement / late callback / alternate renderer, normal producer versus modified-codec duplicate / reverse, repeated source=build / immutable submitted snapshot / two-tab recovery gap. Отдели реальные existing components от моделей и перечисленных NOT RUN async/dispose / integration ветвей.
6. Достаточность остановки по контрпримерам / timebox, honest forecast assumptions и будущие acceptance gaps. Числа 16/12/44 не ослабляются; не объявляй model-specific FAIL глобальной невозможностью или готовностью нового fallback.

Можно повторить существующие безопасные source/post-audit scripts после чтения кода и выборочно воспроизвести сохранённый harness на записанном environment при доступности. Новую раскладку / дополнительный layout tuning не разрабатывай; отсутствие нужной среды или непроведённый replay запиши как предел evidence. Новый фактический запуск не приписывай старому SHA без входов / команды / результатов.

Результат веди в существующем tester_artifact.md и при необходимости новом tester/task_t004_review.md / своём evidence. Одна адресная матрица T003-G01…05 / REQ-AS → independent expected → actual evidence → достаточность / остаток. Не переписывай Developer / прежние T003/T005/T006 reports.

Явный итог: исследовательский результат достаточен в перечисленном проверенном предмете с границами; либо конкретный возврат D003 по недостаточному / ошибочному evidence. Непригодность heuristic при корректных измерениях — существенный результат, а не причина потребовать сделать его PASS. TEST-FIND-WHEEL-002 закрывается только по своему полному критерию, автоматически не закрывай.

Выход — подписанный адресный handoff: TaskId / автор / source SHA, рассмотренные REQ / AS / DP, expected / actual / evidence, явный вывод с основанием, конкретные остатки / owners / условие исправления, команды / реальные результаты / NOT RUN, estimate impact и изменённые пути. Reviewer отчёта — Codex / Manager по полноте / версиям / traceability; авторский verdict не заменяется решением Manager.

Действующий контракт / Owner choices / Manager-сводку / gates / бюджет / чужие материалы не меняй. Не создавай дубли findings по уже зафиксированным DEV-FIND-WHEEL-002/003 / TEST-FIND-WHEEL-002; source evidence / прежние JSON / manifests сохраняй. Не представляй контрпример изменённого artifact как воспроизведённый normal production bug без поддерживаемого сценария.

Проверь собственные ссылки / anchors / таблицы / Git scope и git diff --check. Полный Developer audit_package.py привязан к precommit dev-worktree / HEAD 8fb2577, не является универсальным gate в твоей ветке; asserts ради запуска не меняй, исторические validation JSON под новый HEAD не пересчитывай. Manifest использует LF для текста и raw для PNG; при CRLF checkout проверяй исходный Git blob / заявленную нормализацию, не переписывая evidence.

Commit / push / PR / внешние сообщения требуют отдельного поручения. До публикации честно обозначь локальный результат; после отдельно разрешённой публикации передай точный OutputSHA Manager. Подготовленный промт не означает STARTED / выполненное review. После адресных выводов Manager собирает следующие конкретные work items / решения и согласование бюджета перед отдельным G3; старый предстартовый цикл не возобновляется.
