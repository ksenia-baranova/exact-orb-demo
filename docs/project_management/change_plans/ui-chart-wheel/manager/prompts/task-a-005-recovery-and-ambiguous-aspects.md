# TASK-A-005 — два адресных вопроса поведения по фактам исследования

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git; сохрани несвязанные изменения / index, без reset / force / очистки. Проверь фактический HEAD и [Manager §2.17](../../manager_artifact.md). Получай чужие материалы только из опубликованного Git.

Задание относится к **уже выполненному исследованию**, без повторного общего предстартового review критериев. Оно не назначает production implementation, G3 или независимое тестирование production кандидата.

- Общий ReviewInputSHA: **`030826fd4e6bfa9613ad84ba7ed32adc15fddcd9`**.
- Единственный TechnicalPackageSHA: **`d24a24e04be32d0522674735388e9d2ea3e65c93`**; merge 030826f имеет родителей 8fb2577 / d24a24e.
- Developer InputSHA / поручение: `8fb25770169166a3a4e94110eee684bd8b116474`.
- CriteriaSHA: `f6f289cda25e7f228dff064175805130cc770b63`; T006 `435337f49b200ca308ae9620efa9902adf1677f9`; A004 `5de9e66c26496880f714f61f78126972dee4fbdd`.
- Analyst v3 `2634b224894b1046113557bfe241f0a5f2d46f8c`, нормативный MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.

Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) v3 / связанные sequences, [research report](../../developer/task_d003_research_report.md), [handoff](../../developer_artifact.md), [DRAFT ADR](../../developer/drawing_adr_draft.md), [checks](../../developer/checks.md), [findings](../../developer/findings.md), [матрицу v2](../../developer/evidence/task_d003_research/matrix_v2.md), [manifest](../../developer/evidence/task_d003_research/package_manifest.json). Фактический HEAD / SHA постановки сохраняй отдельно от закреплённого TechnicalPackageSHA; движение change не подменяет предмет автоматически.

До STARTED сообщи собственную оценку / confidence / assumptions и возможность целевого ответа за **1 рабочий день после точной передачи**. Старые оценки другого задания не переноси. Если target невозможен, сразу предложи Manager конкретный срок / влияние; без выдуманного рабочего календаря. Затем зафиксируй фактический STARTED в своём handoff и выполняй назначенную работу, не ожидая verdict другой роли. Эскалация +1 рабочий день просрочки, Manager → Owner; заместителя нет.

Используй [skill Functional Analyst](../../../../../development_approach/skills/functional-analyst/SKILL.md), существующую ветку `analysis/ui-chart-wheel`. Это новое задание по двум конкретным semantic cases D003; не новая полная Analysis / повторный опрос по C01…C03.

Цель: установить observable expected и влияние на принятые требования. Если действующий контракт уже задаёт ответ, обоснуй его без нового Owner-вопроса. Если остаётся реальная развилка, подготовь **один сводный вопрос Owner** с вариантами / различающими scenarios / рекомендацией, а не общий цикл пересогласования.

| Предмет / sources | Конкретный trace / что определить |
|---|---|
| G03: fresh matched recovery после lost POST; REQ-WHEEL-08 / REQ-UI-09, применимые AS / DP-O-013, report / source_controls / recovery.mjs | Карта A показана, локально отправлена изменённая B, ответ потерян; fresh GET B / matched. История 1: завершился этот POST; история 2: другая вкладка записала ту же B, локальный POST не победил. Публичные наблюдения одинаковы. Установи, достаточно ли подтверждения результата локальной pending цели для одноразового reset / collapse / once-per-attempt без утверждения server authorship; automatic current без pending, stale / different / old, поздний изменённый draft и повтор publish должны остаться различимыми |
| G02: validation-admissible duplicate / reversed duplicate saved aspects; REQ-WHEEL-07/08, применимые AS / DP-O-010/013, report / source_audit / orientation_audit | Normal producer unique, но modified-copy codec/projector допускает natal 47/46 keys и cosmogram14/13; endpoints имеют не lexical direction. Для ambiguity определить ожидаемые HTML facts / выбор пары / marker / сообщение / снятие selection. Не выдавай modified artifact за normal web bug; не выбирай новую API валидацию или потерю фактов по умолчанию. Technical Reviewer независимо проверяет lookup / boundary |

Сверь baseline UI / Analyst v3 / behavioral sequences и Owner choices. Не смешивай подтверждение данных намерения, chart_identity, автора server commit, request_id / attemptId и once token. Подготовь различающие сценарии для двух историй / pending versus automatic / same versus different birth / disappeared versus ambiguous key / natal versus cosmogram.

Developer рекомендует once-per-pending-attempt target confirmation для G03 без нового API; для G02 наблюдаемая policy ещё не принята. Это предложения для оценки совместимости, не новый Owner choice. Сравни альтернативы и влияние на current / selection / reset / collapse / доступность / technical scope; посоветуй минимальное решение внутри действующего контракта, если оно возможно.

Разрешено дополнить собственный analyst_artifact.md подписанным разделом TASK-A-005, при необходимости собственные findings / сценарные proposals внутри analyst/. Принятые requirements / sequences / normative current/ / ADR / Owner decisions без решения владельца не переписывай. Новую DP не дублируй: используй существующие DP-O-010/013 через Manager; отдельный ID предложи только при доказанной новой несводимой развилке.

Выход: две адресные карточки REQ / AS / DP → concrete trace → existing expected либо неопределённость → варианты / recommendation / влияние / owner / closure condition. Для уже определённого поведением случая дай вывод применимости; для нового выбора — один готовый вопрос Owner и предложенная дельта после решения. Численные SVG thresholds / approved C01…C03 повторно не согласовывай, layout / native evidence за Tester не принимай.

Работай параллельно T004 / R001 на одном пакете. Отметь существенную зависимость конкретного вывода от technical recommendation, если она есть, и продолжай независимую часть. Это не означает ждать всех reviewers перед чтением / своим STARTED.

Выход — подписанный адресный handoff: TaskId / автор / source SHA, рассмотренные REQ / AS / DP, expected / actual / evidence, явный вывод с основанием, конкретные остатки / owners / условие исправления, команды / реальные результаты / NOT RUN, estimate impact и изменённые пути. Reviewer отчёта — Codex / Manager по полноте / версиям / traceability; авторский verdict не заменяется решением Manager.

Действующий контракт / Owner choices / Manager-сводку / gates / бюджет / чужие материалы не меняй. Не создавай дубли findings по уже зафиксированным DEV-FIND-WHEEL-002/003 / TEST-FIND-WHEEL-002; source evidence / прежние JSON / manifests сохраняй. Не представляй контрпример изменённого artifact как воспроизведённый normal production bug без поддерживаемого сценария.

Проверь собственные ссылки / anchors / таблицы / Git scope и git diff --check. Полный Developer audit_package.py привязан к precommit dev-worktree / HEAD 8fb2577, не является универсальным gate в твоей ветке; asserts ради запуска не меняй, исторические validation JSON под новый HEAD не пересчитывай. Manifest использует LF для текста и raw для PNG; при CRLF checkout проверяй исходный Git blob / заявленную нормализацию, не переписывая evidence.

Commit / push / PR / внешние сообщения требуют отдельного поручения. До публикации честно обозначь локальный результат; после отдельно разрешённой публикации передай точный OutputSHA Manager. Подготовленный промт не означает STARTED / выполненное review. После адресных выводов Manager собирает следующие конкретные work items / решения и согласование бюджета перед отдельным G3; старый предстартовый цикл не возобновляется.
