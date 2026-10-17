# Developer: ui-chart-wheel

**Автор:** Codex / Developer, 2026-10-16. **Редакция:** consultation v2 по Analyst v3; `TASK-D-002`.
**Назначение / сводка:** [Manager §§2.6–2.7](manager_artifact.md#27-task-d-002--повторная-developer-consultation-по-analyst-v3) @ `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`. Ручную сводку состояния и общий реестр ведёт Manager.
**Текущий InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`; resolver задания §2.6 подтверждает именно этот опубликованный commit. Ветка `dev/ui-chart-wheel` обновлена fast-forward из `origin/change/ui-chart-wheel`, исходный worktree чистый.
**Вход Analyst:** v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, интеграция PR #69 @ `859718ae9e209ee18a0e24e44f765e24e58b4045`; payload 9/9 совпадает с InputSHA. Нормативный MainBaseline — `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.
**Worktree:** `C:\Users\KateUser\.codex\worktrees\ui-chart-wheel-dev\exact-orb-recovered`.
**Основание текущей записи:** Owner поручил обновиться из change и выполнить Developer review, затем прямо разрешил «Внеси изменения в нужные документы если требуется». Developer подтверждает начало разрешённой документальной актуализации на InputSHA; это не начало реализации / spike / ADR. G1 и переходы Manager здесь не объявляются выполненными.
**Reviewer результата:** Codex / Change Manager — полнота и пригодность для G2; Codex / Tester — проверяемость технических критериев, по назначению §2.6. Technical Reviewer для существенной границы renderer ещё требуется отдельно до G3.
**Заключение:** **FEASIBLE WITH DECISIONS** на InputSHA с Analyst v3. Новых противоречий публичному ChartDTO не найдено; графическая читаемость и окончательный технический контракт не доказаны.
**Estimate:** предварительно **8–12 чд Developer**, графика 5–7 и interaction / форма / recovery 3–5; уверенность ниже средней до измерений. Повторная консультация / документальная актуализация отдельно оценена в 0,5–0,75 чд, это не согласованный срок и не фактические затраты; подробности в [плане](developer/implementation_plan.md).
**Implementation commit / CandidateSHA / TestedSHA:** отсутствуют. Публикационная версия v2 определяется по resolver ниже; [manifest](developer/package_manifest.json) фиксирует девять payload-файлов.

| Материал | Предмет новой редакции | Review |
|---|---|---|
| [Implementation Plan](developer/implementation_plan.md) | V3 → work items / критерии / estimate, предложение renderer port и отдельного spike | Manager; Tester в своём предмете; approvals пока нет |
| [Findings](developer/findings.md) | Повторная сверка DEV-FIND-WHEEL-001…003 с сохранением исходного evidence | Разрыв требований устранён в документальной части; технические остатки не закрыты |
| [DP input](developer/decision_input.patch) | Подписанная рекомендация TASK-D-002 к DP-O-010…014 @ InputSHA | Предложение Manager; реестр и Owner decisions не изменены |
| [Промты 01…04](developer/prompts/) | Неисполненные постановки синхронизированы с v3, AS-WHEEL-28…30 и MODIFY AS-UI-22 | Условия будущего запуска сохранены; исполнение не поручено |
| [Checks](developer/checks.md) | Baseline / ссылки / hashes / scope и границы evidence | Документальные результаты; runtime / browser NOT RUN |

## Повторная консультация TASK-D-002

Проверены требования, 30 AS-WHEEL, MODIFY AS-UI-22 и три behavioral sequences Analyst v3 против Manager / исходного UI / публичного DTO / существующего покрытия. V3 задаёт выбор «нет / point / аспект», одну строку и одну графическую пару выбранного аспекта, повторное снятие, сохранение допустимого выбора при automatic current, collapse по совпадению snapshot, все points и отдельные angles, подпись категории / контур выбранного ☌. Эти Owner decisions повторно не выносятся на выбор.

Обновлены план, findings, будущие промты и вклад в DP: state у result controller; перенос выбора на новый DTO без старых фактов; локальный видимый SVG failure с HTML той же карты; конкретные доказательства для density / keyboard / recovery. Это технические предложения для review, не принятый интерфейс или drawing ADR. Общий реестр остаётся единственным.

**Прежние findings:** DEV-FIND-WHEEL-001 — документальная причина на v3 устранена; полный closure не заявляется за Tester / reviewers. DEV-FIND-WHEEL-002 — риск port / focus / recovery сохраняется до ADR и integration evidence. DEV-FIND-WHEEL-003 — измерения и предел плотности отсутствуют. Прежние Tester findings не закрываются Developer.

**Дальнейшие условия:** Manager регистрирует актуальный результат и после отдельной публикации — точный package SHA; Tester сверяет новые критерии на этой версии. DP-O-010…013 требуют оставшихся технических решений, отдельно назначенных spike / ADR и approvals до G3. Чистовой перенос требований / sequences — после Owner acceptance, сейчас не выполняется.

Срок исполнения, ответа reviewer / Owner и эскалации в назначении не согласованы. Они не подставлены из оценки; адресат — Manager → Owner, заместитель не назначен. Прямое разрешение Owner позволяет текущую независимую документальную работу; оно не заменяет согласование полей назначения / G1 в Manager. Новые READY_FOR_REVIEW / IN_REVIEW / DONE / APPROVED не устанавливаются в ролевом индексе. Первоначальное поручение было документальным; отдельное разрешение commit / push этой редакции приведено ниже, PR не поручен.

## История и версии

Consultation v1 / TASK-D-001 сохранена в Git @ `04be207627de1049deac2e069574e01b62536607`, исходный InputSHA `2b846077b317e33dd892565419942c4db8517b1e`, Analyst v1 @ `683bdd0c1f5a0e65735f4e48127d408300ec697c`. Owner отдельно разрешил и получил commit / push именно v1; его remote parity подтверждена в том проходе. Manager зарегистрировал этот пакет и его рекомендации; исходные пометки о неназначенных reviewers / нерегистрации являются историей.

Текущая редакция заменяет рабочие Developer-материалы для v3, сохраняя v1 по указанному commit. Её публикационная версия — первый commit, добавляющий заголовок «Повторная консультация TASK-D-002» в этот файл; resolver сохранён в manifest. До отдельного разрешения и успешного commit / push SourceRef `origin/dev/ui-chart-wheel` не считается содержащим новую редакцию. Публикация документов не означает approval / readiness / реализацию.

## Разрешение публикации TASK-D-002

Owner отдельно поручил в текущем чате: «Комит и пуш в ветку dev». По контексту разрешён атомарный commit / push consultation v2 в `dev/ui-chart-wheel`: только десять подготовленных Developer-файлов. Это не разрешение реализации, spike / ADR, PR / merge либо изменения Manager / Analyst / Tester.

Точный commit определяется resolver выше / в manifest, без самоссылочного SHA в payload. Успех push подтверждается равенством local HEAD, upstream и `git ls-remote origin refs/heads/dev/ui-chart-wheel`; фактические SHA и результат передаются в чате. Состояние TASK-D-002 / версии и применимость к G2 регистрирует Manager после публикации; Developer не устанавливает их вместо него. Результаты документальной подготовки сохраняют свой InputSHA, текущая публикация не превращает их в runtime / browser evidence.

## TASK-D-003 — оценка и подготовка старта

**Автор:** Codex / Developer, 2026-10-17. Предыдущий handoff consultation v2 / TASK-D-002 выше и его payload / manifest сохранены. Новый материал — оценка v1 отдельного задания; это не переиздание v2 и не результат технического исследования.

**Сводка / назначение:** [Manager §§2.11–2.12 / Change Plan](manager_artifact.md) @ `0083d81151f3af649feee9e7737ec6469c35cf1e`; материальный InputSHA `6c4607165085d7297f044cef026353f36f6c842f`. Принятые TASK-T-003 @ `c59cc3f68e7769841134801dc125633decade032` / TASK-A-002 @ `2f5579677114ea2dc86c66cf0fd656fdb5910df5` и консультации f9c70f7 / 2634b22 / 7e95c0f остаются закреплёнными предметами. Общий статус / gates / ролевые состояния ведёт Manager.

В существующем worktree выполнен fetch и fast-forward `dev/ui-chart-wheel`: **`8921e9d81d416f6ae49c401600c600d24e46c316` → `0083d81151f3af649feee9e7737ec6469c35cf1e`**. Исходное дерево / индекс чистые, несвязанных изменений не было. Reset / force не применялись. InputSHA→registration меняет только Manager-файл: добавляет регистрацию reviews / G2, рекомендации и evidence пяти DP; прежние Owner-choice / статусы сохранены. Влияние / точная разница переданы в новом плане и audit; предметы не заменены HEAD автоматически.

**Полная оценка TASK-D-003:** **2,5–3,5 чд / 20–28 рабочих часов**, средняя уверенность для ограниченного пакета / контрпримера, ниже средней для достижимости F3-max на 360 px. Состав: критерии 3–4 ч; предпосылки 6–8 ч; эксперимент 4–6 ч; проект ADR / sequences 4–6 ч; evidence / план / передача 3–4 ч. Эксперимент до 0,75 чд входит в эту оценку и прежние общие 8–12; повторное прибавление не предлагается. Зависимости, exclusions, необходимая среда и пять направлений T003-G01…05 подробно описаны в [отдельном Implementation Plan TASK-D-003](developer/task_d003_implementation_plan.md).

**Предложение сроков:** пакет до конца 4-го рабочего дня от отдельно согласованного T0; ответ на критерии / точный будущий пакет — до 1 рабочего дня, готовность и оценки reviewers согласует Manager с ними; эскалация Manager → Owner через 1 рабочий день просрочки. Ожидания и труд reviewers вне чд Developer. Кандидаты измеримых критериев, включая определения минимальности / bounds / font / hit targets, находятся в плане для review; числа не утверждены. Условие старта — явное согласование критериев / сроков и отдельное поручение начать. **STARTED не подтверждается**, эксперимент не выполняется.

**Handoff оценки Manager:** принять диапазон и условия для согласования, передать точную редакцию критериев Tester / при необходимости Analyst / Technical Reviewer, назначить сроки и T0 отдельным решением. После будущего исполнения адресаты результата — Manager, Tester TASK-T-004 и Technical Reviewer TASK-R-001; TechnicalPackageSHA появится только после отдельного разрешения публикации. Техническая граница / drawing ADR, наблюдаемый fallback, G3 и независимая acceptance этой оценкой не принимаются.

**Проверки:** [статический audit JSON](developer/evidence/task_d003_preparation.json), воспроизводимая команда `python -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d003_preparation_check.py`; исторические manifests Developer / Analyst 9/9 каждый, 42 source hashes review, сохранённый префикс этого индекса / прежние payload, Git scope / ссылки / таблицы / whitespace. Pytest / Node tests, browser/font/focus measurements, SVG-spike, screenshots, ADR / sequences и production implementation не выполнялись. Нового commit / push / PR нет; это локальная оценка, не опубликованный technical package. Manager / чужие артефакты / DP в этом проходе не редактируются.

## TASK-D-004 — STARTED, исправление предстартовых критериев

**Автор / подпись:** Codex / Developer. **Фактический STARTED:** 2026-10-17 19:35:11 UTC / **2026-10-17 22:35:11 MSK**. Источник времени — clock в начале текущего разрешённого прохода, не timestamp commit.

**Разрешение Owner:** «Как Owner согласовываю оценку TASK-D-004: 3–4 рабочих часа, передача результата в течение одного рабочего дня от STARTED»; «Начинай TASK-D-004, зафиксируй STARTED и срок передачи». Оценка относится к слоту критериев 3–4 часа внутри 20–28, без автоматического увеличения. Confidence — средняя; предыдущий фактический расход неизвестен. При прогнозе превышения — влияние / переоценка Manager до расширения работы.

**Срок передачи:** не позднее одного рабочего дня от указанного STARTED, как согласовал Owner. Рабочие интервалы проекта календарно не заданы; произвольный UTC-дедлайн / выходной вместо рабочего дня не подставляется. Результат будет передан в текущем рабочем сеансе при выполнении проверок. Это STARTED только D004; T0 D003 не наступает.

**Вход:** `aa067201dc509f19bbe670778a9fa9470cf0bfb0` — опубликованная Manager-регистрация §2.14; перед предыдущим этапом intake существующая dev-ветка обновлена fast-forward `11a703ed6a01eb368f0f0ba23dc23f1e90fac81f` → `aa067201dc509f19bbe670778a9fa9470cf0bfb0`. Текущий fetch origin/change/ui-chart-wheel подтвердил тот же SHA; начальные дерево / индекс чистые. Материальная база поручения `67fd9dbf25fb5cb6a4dafbce65582078917bb1a3` остаётся исторической базой Manager, не подменяется новым предметом review.

**Закреплённые предметы:** возвращённый план v1 @ `11a703ed6a01eb368f0f0ba23dc23f1e90fac81f`; Tester TASK-T-005 @ `71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe`; Analyst TASK-A-003 @ `4055a9cb2bb18919c776c9d4e8585e2408a638c7`; Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; исходный нормативный baseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`. Источники других ролей получены только из опубликованного Git.

**Границы:** документальные определения / аналитические controls в собственных материалах. TASK-D-003 остаётся BLOCKED; нет SVG/browser experiment, алгоритма размещения, production / API / engine / golden / dependency changes. Manager, gates, чужие артефакты и прежние JSON / manifests не редактируются. Публикация отдельно разрешена Owner-поручением «Комит пуш» в текущей цепочке D004 и выполняется после готового проверенного handoff только для исправления критериев; ранний push передал исходный fast-forward aa06720, нового пакета тогда не было. PR / merge и снятие блокировки не поручены.

## TASK-D-004 — передача исправленных критериев v2

**Автор / подпись:** Codex / Developer, 2026-10-17. **Предмет:** v2 DRAFT [плана / измерительных критериев](developer/task_d003_implementation_plan.md); фактический InputSHA `aa067201dc509f19bbe670778a9fa9470cf0bfb0`. STARTED / Owner-согласование / срок зафиксированы выше. Срок — один рабочий день от 17.10.2026 22:35:11 MSK; локальная передача готовится в том же рабочем сеансе, без объявления произвольной календарной даты вместо согласованного рабочего интервала.

**Исходные версии:** возвращённая v1 @ `11a703ed6a01eb368f0f0ba23dc23f1e90fac81f`; T005 @ `71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe`; A003 @ `4055a9cb2bb18919c776c9d4e8585e2408a638c7`; Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`. v1 / её source SHA-256 и старые JSON / manifests сохранены; они не перезаписываются и не объявляются audit нового плана. Manager, gates, DP / Owner choices и чужие результаты не редактируются.

Корневая причина возврата — перечисленные в v1 размеры / ограничения не задавали единый predicate; feasibility смешивалась с минимальностью, а номинальный размер / bbox / fake focus могли дать ложноположительный control. V2 разделяет эти predicates и их предел evidence, сохраняя 0,5 / 2 / 1 / 16 / 12 / 44, продуктовый scope и состав будущей matrix.

| Замечание | Исправление / analytical control | Точное место |
|---|---|---|
| T005-R01 / A003-C02 | Viewport CSS frame / affine mapping; independent true/display reference; Euclidean anchor error; union component AABB всех состояний; Euclidean gap≥2 с равенством; frozen set / annulus / circle-return / clipping. G-diagonal-gap проходит с squared gap 4,5; forbidden inner/outer отвергаются; SVG clip=[0,300] отвергает [292,308], но принимает [284,300] | [План G1–G7 и G-controls](developer/task_d003_implementation_plan.md#d004-geometry); task_d004_controls.py: G-* |
| T005-R02 / A003-C01 | Проба min(1,d) по объявленному допустимому пути, frozen others, no placement call; отдельные FEASIBLE / LOCAL_STEP / LOCAL_TIGHT. [18,34] принимается; [20,36] / [19,35] отвергаются. Дробный 18,5 проходит 1px-проверку, но отвергается boundary witness 0,5; d<1 проверяется полным возвратом, не округляется | [План L1–L4 / L-controls](developer/task_d003_implementation_plan.md#d004-locality); task_d004_controls.py: L-* |
| T005-R03 / A003-C02 | 16/12 — effective em-size после transform, отдельно от ink / contour / focus. Положительные records на 16/12, отрицательные 15,99/11,99, scale=0,5 и missing-glyph; em=16 / ink=12 различает predicates. Реальный font неизвестен до будущего measurement | [План F1–F2 / F-controls](developer/task_d003_implementation_plan.md#d004-font); task_d004_controls.py: F-* |
| T005-N01 / A003-C03 | Half-open Q≥44×44 должен целиком лежать в effective native hit area; coordinate / target / clip / overlap controls вместо bbox / element.click(). Retained / recreated / removed focus и collapse разделены по cause; planet-activation сохраняет тот же live node без focus()/scroll. Wrong fallback / detached / скрытый control отвергаются | [План H1–H5 / H-controls / focus policy](developer/task_d003_implementation_plan.md#d004-hit-focus); task_d004_controls.py: H-* / K-* |

**Проверяемые новые интерпретации для Analyst / Technical Reviewer:** union component AABB / Euclidean gap; фиксированный ring-return model; effective em-size; cause-specific focus policy. Это DRAFT-конкретизация открытых definitions, не принятый drawing ADR. Если такая конкретизация меняет наблюдаемое обязательство, передать конкретный differing control Manager → Owner; положительное заключение за TASK-A-004 / TASK-T-006 не подписывается Developer. Для current/reconcile пересозданного control разрешено восстановление только того же key без scroll; это правило не маскирует detach при planet activation.

**Команды и фактический предел:**

- `python -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d004_controls.py --write` — генерация нового analytical / documentary audit; повтор без `--write` сверяет его содержимое / output hashes. `--calibrations-only` — ровно математические / моделируемые controls, без Git audit / renderer. Зафиксировано 50/50 аналитических controls; точные inputs / expected / actual — [task_d004_controls.json](developer/evidence/task_d004_controls.json).
- Полный запуск проверяет 16 source hashes T005 на их записанных SHA, исторические manifests Analyst / Developer 9/9 каждый, v1 plan @ 11a703e, префикс прежнего индекса, все прежние Developer-файлы кроме разрешённого плана, scope четырёх файлов, ссылки / anchors / таблицы / whitespace. Полный успешный output — `TASK_D004_CONTROLS_OK` / `TASK_D004_AUDIT_OK`; повторяемые команды / данные находятся в репозитории.
- `git diff --check` — отдельная проверка whitespace. Структурные проверки документов не являются browser / runtime evidence.

**Непроверенное / ограничения:** реальные SVG/font/bbox/hit/focus measurements, screenshots и native pointer / keyboard actions, общий curved-path certificate verifier, renderer replacement / mounted coordinator / recovery, Node / pytest / HTTPS и PUML render — NOT RUN. K-controls проверяют только согласованность model records, не живой DOM. Нет алгоритма размещения / production implementation / engine / API / golden / новых dependencies / drawing ADR. Калибровка local return не доказывает глобальную минимальность или достижимость плотности; bounding sizes / 100% zoom не отменяют требования доступности / увеличенного текста.

**Влияние на оценку:** согласованная оставшаяся оценка D004 3–4 ч относится к ранее предусмотренному слоту критериев внутри 20–28. Прогноз автоматического увеличения диапазона не заявлен; прошлый фактический расход неизвестен, текущий проход не выдаётся за timesheet всего слота. При новом цикле / прогнозе превышения — адресное влияние Manager; предел будущего эксперимента ≤6 ч и прежние 8–12 чд не пересуммированы.

**Изменённые файлы — только четыре Developer paths:**

1. [developer/task_d003_implementation_plan.md](developer/task_d003_implementation_plan.md) — v2 DRAFT / definitions / calibrated expected results; v1 доступна по 11a703e.
2. [developer_artifact.md](developer_artifact.md) — добавленные STARTED / согласованный срок / этот подписанный handoff; прежний индекс сохранён префиксом.
3. [developer/evidence/task_d004_controls.py](developer/evidence/task_d004_controls.py) — независимые аналитические primitives / document audit, без размещения объектов.
4. [developer/evidence/task_d004_controls.json](developer/evidence/task_d004_controls.json) — новый отчёт с исходными pins / hashes / expected / actual / limitations.

**Локальное состояние передачи:** собственный v2 DRAFT / handoff подготовлены поверх aa06720; до commit это изменённые / новые файлы, не опубликованный CriteriaSHA. Отдельное Owner-поручение «Комит пуш» в текущей цепочке D004 разрешает последующую публикацию только этого исправления в dev/ui-chart-wheel; ранний push передал лишь исходный fast-forward, исправления тогда ещё не было. PR / merge / снятие блокировки не поручены.

**Resolver CriteriaSHA после разрешённой публикации:** первый commit, добавляющий заголовок «TASK-D-004 — передача исправленных критериев v2» в этот файл: `git log --reverse --format=%H -G '^## TASK-D-004 — передача исправленных критериев v2$' -- docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md`. До успешного commit / push никакой output SHA не выдумывается; local / remote SHA сверяются через Git и передаются Manager в итоговом сообщении.

**Обязательный следующий шаг:** Manager регистрирует точный опубликованный CriteriaSHA / комплект изменений для **TASK-T-006 и TASK-A-004**. После двух положительных адресных reviews Manager проверяет входы / среду и решает вопрос снятия блокировки. **TASK-D-003 остаётся BLOCKED, T0 не наступает**; Developer не меняет это состояние по результатам своего D004 и не запускает исследование / эксперимент.

**Локальная передача содержательной редакции готова:** 2026-10-17 20:01:32 UTC / 23:01:32 MSK, тот же рабочий сеанс после STARTED. Проверки сохранённой редакции: 50/50 analytical controls; 23 Markdown-файла / 817 локальных ссылок / 72 таблицы и anchors, git diff --check — PASS. Это отметка события готовности, не timesheet / фактические чд всего слота. При публикации exact CriteriaSHA / remote parity передаются отдельно; T006 / A004 и решение Manager ещё впереди.
