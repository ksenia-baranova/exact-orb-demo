# TASK-R-001 — техническое review полученного исследования и DRAFT ADR

**Текущий шаг после r2:** содержательный результат уже передан Owner текстом. Для завершения существующего R001 используй [поручение Git-передачи](task-r-001-publication-handoff.md); повтор исследования не назначается. Ниже сохранён предмет исходного review и его Git-параметры.

Сначала обнови назначенную ролевую копию из опубликованной `change/ui-chart-wheel` через Git; сохрани несвязанные изменения / index, без reset / force / очистки. Проверь фактический HEAD и [Manager §2.17](../../manager_artifact.md). Получай чужие материалы только из опубликованного Git.

## Git-параметры для внешнего reviewer

- Репозиторий (актуальный HTTPS URL): `https://github.com/ksenia-baranova/exact-orb-demo.git`.
- Интеграционная ветка: `change/ui-chart-wheel`; опубликованная постановка / **AssignmentSHA: f6c555c39e3371c8ed925b980cd0ce480e521dbf**.
- Ветка источника исследования: `dev/ui-chart-wheel`; закреплённый **TechnicalPackageSHA: d24a24e04be32d0522674735388e9d2ea3e65c93**.
- **ReviewInputSHA: 030826fd4e6bfa9613ad84ba7ed32adc15fddcd9** — интеграция пакета до Manager-регистрации; AssignmentSHA дополнительно содержит задания / промты.
- **DeveloperInputSHA: 8fb25770169166a3a4e94110eee684bd8b116474** — исходный commit для сравнения изменений исследования.
- Область diff: `8fb25770169166a3a4e94110eee684bd8b116474..d24a24e04be32d0522674735388e9d2ea3e65c93`, 165 Developer paths, включая manifest. Требования / текущий код читаются как контекст.
- Корень change: `docs/project_management/change_plans/ui-chart-wheel/`; постановка Manager — `manager_artifact.md`, §2.17.
- Главный отчёт: `developer/task_d003_research_report.md`; доказательства: `developer/evidence/task_d003_research/`; authoritative matrix: `run03/browser_matrix.json` внутри evidence.
- Выход Reviewer: `docs/project_management/change_plans/ui-chart-wheel/manager/technical_review.md`.

Адрес репозитория и обе ветки проверены через `git ls-remote` 18.10.2026: change на AssignmentSHA, dev на TechnicalPackageSHA. Локально проверена достижимость пакета из AssignmentSHA. Последующее движение веток не меняет закреплённый предмет review.

Для новой отдельной reviewer-копии:

```sh
git clone --branch change/ui-chart-wheel https://github.com/ksenia-baranova/exact-orb-demo.git exact-orb-ui-chart-wheel-review
git -C exact-orb-ui-chart-wheel-review checkout --detach f6c555c39e3371c8ed925b980cd0ce480e521dbf
git -C exact-orb-ui-chart-wheel-review merge-base --is-ancestor d24a24e04be32d0522674735388e9d2ea3e65c93 HEAD
git -C exact-orb-ui-chart-wheel-review diff --stat 8fb25770169166a3a4e94110eee684bd8b116474 d24a24e04be32d0522674735388e9d2ea3e65c93
```

После clone / обновления проверь HEAD / рабочее дерево и прочитай полное поручение ниже. Для уже существующей копии сохраняй её изменения и следуй безопасному обновлению из первого абзаца.

Задание относится к **уже выполненному исследованию**, без повторного общего предстартового review критериев. Оно не назначает production implementation, G3 или независимое тестирование production кандидата.

- Общий ReviewInputSHA: **`030826fd4e6bfa9613ad84ba7ed32adc15fddcd9`**.
- Единственный TechnicalPackageSHA: **`d24a24e04be32d0522674735388e9d2ea3e65c93`**; merge 030826f имеет родителей 8fb2577 / d24a24e.
- Developer InputSHA / поручение: `8fb25770169166a3a4e94110eee684bd8b116474`.
- CriteriaSHA: `f6f289cda25e7f228dff064175805130cc770b63`; T006 `435337f49b200ca308ae9620efa9902adf1677f9`; A004 `5de9e66c26496880f714f61f78126972dee4fbdd`.
- Analyst v3 `2634b224894b1046113557bfe241f0a5f2d46f8c`, нормативный MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.

Прочитай AGENTS.md, [process.md](../../../../../development_approach/process/process.md), [roles.md](../../../../../development_approach/roles.md), [requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) v3 / связанные sequences, [research report](../../developer/task_d003_research_report.md), [handoff](../../developer_artifact.md), [DRAFT ADR](../../developer/drawing_adr_draft.md), [checks](../../developer/checks.md), [findings](../../developer/findings.md), [матрицу v2](../../developer/evidence/task_d003_research/matrix_v2.md), [manifest](../../developer/evidence/task_d003_research/package_manifest.json). Фактический HEAD / SHA постановки сохраняй отдельно от закреплённого TechnicalPackageSHA; движение change не подменяет предмет автоматически.

До STARTED сообщи собственную оценку / confidence / assumptions и возможность целевого ответа за **1 рабочий день после точной передачи**. Старые оценки другого задания не переноси. Если target невозможен, сразу предложи Manager конкретный срок / влияние; без выдуманного рабочего календаря. Затем зафиксируй фактический STARTED в своём handoff и выполняй назначенную работу, не ожидая verdict другой роли. Эскалация +1 рабочий день просрочки, Manager → Owner; заместителя нет.

Используй роль **Technical Reviewer** по roles.md §7, в отдельном ролевом сеансе от автора Developer-пакета. Это уже назначенный адресный review данного change; нового обязательного gate для всех изменений не вводи. Работай в назначенной reviewer-копии / checkout; не переключай чужую ветку и не выдавай самооценку Developer за независимый review.

Цель: дать конкретное заключение по предлагаемой технической границе, ограничениям исследовательского доказательства и следующему Developer work item. Review готового исследования не должен превращаться в новый общий предстартовый круг.

Проверь по действующим ADR / component responsibilities / коду / тестам:

1. Leaf WheelPort / ResultController versus alternatives: immutable ChartDTO / один accepted snapshot для HTML и SVG; локальный fault B сохраняет HTML B / summary B и удаляет A; общий failure path / recovery gates сохраняются. Canonical intents, listener ownership, mount/update/dispose, generation **и** revision, async same-instance settlement, dispose throw / идемпотентность и предел реально выполненного isolated evidence.
2. Unordered endpoints+published type как lookup с исходным DTO direction/order для вывода. Раздели unique normal default producer и validation-admissible persisted duplicate / reverse. Оцени explicit ambiguous outcome / наблюдаемую policy вместе с A005; новое API / persistence validation не выбирай молча.
3. acceptanceSeq / attemptId / submitted snapshot / once-reset / draft policy. Source=build повторён трижды на один POST, identity не once token. У fresh matched recovery двух вкладок нет доказательства server-producer provenance; техническая рекомендация должна отделять подтверждение локальной цели от авторства commit и не менять observable правило без владельца.
4. Retained keyed DOM и focus causes, независимый true-anchor/measurement boundary, соблюдение only-conflicting / order / leaders / fonts / Q44. Конкретная fixed-ring construction не прошла dense / hit / minimality; это не глобальная невозможность. Сравни предложенные допустимые варианты (другая movement model / conflict lanes / angle-label placement / target geometry) и их последствия.
5. DRAFT ADR и две technical sequences: соответствие source / report, ownership и transition order / local outcomes / доступная корреляция; research trace не вводит новый production logger. Сохраняй детерминированный расчёт / LLM boundary, modular monolith / public API / существующие module boundary tests.
6. Замещающий forecast 9–14: проверь assumptions / непересечение подготовки / будущих блоков и uncertainty. Reviewer даёт техническое влияние / рекомендацию; Owner budget / риск и окончательное принятие ADR не подписывает.

Не требуй полной реализации / будущих mounted regression checks для принятия корректного исследовательского отчёта. Раздели: ошибка доказательства / несогласованность пакета; документированное ограничение; необходимый будущий implementation check; новое semantic / product решение.

Выход — новый **manager/technical_review.md** с подписью Technical Reviewer, TaskId / точным package SHA, таблицей «область → проверенный source / факт → ограничение / риск → рекомендация / owner / next evidence». Прежние role reports / Manager summary не редактируй. Дай явный verdict по technical proposal / пригодности research package либо адресный возврат с условиями.

Обязательно предложи конкретный следующий Developer work item: что исследовать / реализовать, допустимый вариант, входы / инварианты / completion evidence / риски / оценочное влияние. Покажи, какие решения действительно блокируют его, а какая независимая работа возможна. Это рекомендация Manager, не разрешение production / нового исследования сверх согласованных границ. По новому выбору, требующему архитектурного владельца, обозначь его явно; не превращай DRAFT ADR в ACCEPTED.

Выход — подписанный адресный handoff: TaskId / автор / source SHA, рассмотренные REQ / AS / DP, expected / actual / evidence, явный вывод с основанием, конкретные остатки / owners / условие исправления, команды / реальные результаты / NOT RUN, estimate impact и изменённые пути. Reviewer отчёта — Codex / Manager по полноте / версиям / traceability; авторский verdict не заменяется решением Manager.

Действующий контракт / Owner choices / Manager-сводку / gates / бюджет / чужие материалы не меняй. Не создавай дубли findings по уже зафиксированным DEV-FIND-WHEEL-002/003 / TEST-FIND-WHEEL-002; source evidence / прежние JSON / manifests сохраняй. Не представляй контрпример изменённого artifact как воспроизведённый normal production bug без поддерживаемого сценария.

Проверь собственные ссылки / anchors / таблицы / Git scope и git diff --check. Полный Developer audit_package.py привязан к precommit dev-worktree / HEAD 8fb2577, не является универсальным gate в твоей ветке; asserts ради запуска не меняй, исторические validation JSON под новый HEAD не пересчитывай. Manifest использует LF для текста и raw для PNG; при CRLF checkout проверяй исходный Git blob / заявленную нормализацию, не переписывая evidence.

Commit / push / PR / внешние сообщения требуют отдельного поручения. До публикации честно обозначь локальный результат; после отдельно разрешённой публикации передай точный OutputSHA Manager. Подготовленный промт не означает STARTED / выполненное review. После адресных выводов Manager собирает следующие конкретные work items / решения и согласование бюджета перед отдельным G3; старый предстартовый цикл не возобновляется.
