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


## TASK-D-003 — фактический STARTED / T0 исследования

**Автор / подпись:** Codex / Developer. **STARTED / T0:** 2026-10-18T12:17:04+00:00 / **2026-10-18T15:17:04+03:00 MSK**; системное UTC-время в момент записи начала разрешённой работы, не время старого commit или D004.

**Разрешение:** прямое поручение Owner в текущем чате «обнови ветку; блокировка снята начинай исследование» и опубликованный [Manager §2.16 / промт исследования](manager/prompts/task-d-003-research-start.md) @ `8fb25770169166a3a4e94110eee684bd8b116474`. Повторного предстартового согласования нет. Сводка Manager, gates и чужие артефакты не редактируются; прежние BLOCKED / NOT_OCCURRED ниже относятся к историческим версиям.

**Git-вход:** существующий worktree `ui-chart-wheel-dev/exact-orb-recovered`, `dev/ui-chart-wheel`; `git fetch origin change/ui-chart-wheel` и `git merge --ff-only FETCH_HEAD`, exit 0: `f6f289cda25e7f228dff064175805130cc770b63` → `8fb25770169166a3a4e94110eee684bd8b116474`. Дерево / index до и после чистые; несвязанных изменений нет. Reset / force / очистка не применялись. Материальный вход Manager — `7d11c41875fe1fbcfe0d6e72925f1240570c4b83`; HEAD добавляет только разрешение / оформление Manager, не подменяет критерии и контракт.

**Предметы:** CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; T006 `435337f49b200ca308ae9620efa9902adf1677f9`; A004 `5de9e66c26496880f714f61f78126972dee4fbdd`; Analyst v3 `2634b224894b1046113557bfe241f0a5f2d46f8c`; MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`. Источники других ролей взяты из опубликованного Git.

**Срок / бюджет:** целостный пакет до конца **4-го рабочего дня от указанного T0**; рабочий календарь не задан, абсолютный дедлайн не выдумывается. 20–28 рабочих часов всего включая подготовку; весь SVG-spike / harness / данные / измерения ≤6 часов внутри. Неизвестный прежний расход не вычитается как точный остаток; 2,5–3,5 чд не прибавляются к 8–12 чд реализации. Фактическое elapsed исследования будет записано отдельно от неизвестного timesheet; прогноз превышения — Manager до расширения.

**Scope / выход:** T003-G01…05, isolated controls / SVG / реальные доступные измерения, evidence / ограничения, DRAFT drawing ADR / technical sequences, findings / варианты / оценка. Production / engine / API / golden / принятые ADR / нормативные требования / новые зависимости не меняются. После результата назначены TASK-T-004 / TASK-R-001; TechnicalPackageSHA появится после отдельно разрешённой публикации. Commit / push / PR текущего исследования не выполняются без отдельного поручения.


## TASK-D-003 — локальный DRAFT technical package, результат исследования

**Автор / подпись:** Codex / Developer, 18.10.2026. **InputSHA:** `8fb25770169166a3a4e94110eee684bd8b116474`. Фактический STARTED / T0 — **15:17:04 MSK**, авторское событие выше. CriteriaSHA `f6f289c` и принятые для исследования T006 `435337f` / A004 `5de9e66` не заменены новым HEAD.

Материалы: [технический report](developer/task_d003_research_report.md), [план D003](developer/task_d003_implementation_plan.md), [DRAFT drawing ADR](developer/drawing_adr_draft.md), technical sequences [001](developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml) / [002](developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml), [checks](developer/checks.md), [findings](developer/findings.md).

**Результат T003-G01…05:** proposed leaf boundary сохраняет HTML points/aspects B при SVG-fault, блокирует поздний callback A и допускает альтернативный живой renderer. Реальный coordinator подтвердил повтор `source=build` и immutable submitted B при позднем draft C. Source/codec proof отделил уникальность нормального producer от validation-admissible дубликатов и направления пары. В authoritative browser matrix — **24 клетки, 25 снимков, 7 446 native probes / 1 679 неверных owner/outcome, 438 keyboard targets / 0 ошибок**. Дополнительно: 50 аналитических калибровок, 26 source controls, 8 codec/source records, 4 orientation records, 127 независимых arc-return records. Проверенный dense heuristic не прошёл; полного drawing или production PASS нет.

Данные / actual coordinates / fonts / bounds / errors / screenshots: [матрица v2](developer/evidence/task_d003_research/matrix_v2.md), [inputs/spec v2](developer/evidence/task_d003_research/inputs_manifest_v2.json), [drawing post-audit](developer/evidence/task_d003_research/drawing_audit_v2.json). История partial run01 и exploratory run02 сохранена; authoritative run03 исправляет отклонение F3 fixture без изменения порогов / радиусов / heuristic. Полные факты и ограничения — в report.

**Timebox / срок:** spike остановлен по достаточному evidence через **0,6023 elapsed часа** от 12:25:09 UTC; probe, harness, данные, исправления и измерения включены, лимит ≤6 часов соблюдён. [Stop record](developer/evidence/task_d003_research/experiment_stop.json). Это elapsed текущего опыта, не timesheet всей подготовки. Итоговый [session record](developer/evidence/task_d003_research/research_session.json) фиксирует длительность текущего сеанса отдельно. Пакет оформлен до конца четвёртого рабочего дня от T0; произвольный календарный дедлайн не назначен. Согласованные 20–28 часов D003 с прежней подготовкой сохранены, неизвестный расход не вычитается как точный остаток.

**Оценка / вопросы Manager:** report предлагает заменить предварительный общий прогноз 8–12 на **9–14 чд**. Confidence средняя по controller / ниже средней по графике; непересекающаяся декомпозиция уже включает D003 2,5–3,5 чд и SVG timebox. Это предложение, не утверждённое увеличение бюджета и не прибавление к старой оценке. Конкретные новые вопросы: G03 fresh matched recovery двух вкладок — подтверждение локальной цели при неизвестном авторе commit; G02 policy для неоднозначной persisted pair. Drawing/Q44 варианты не являются принятым fallback. Адресаты и различающие примеры записаны в report / ADR; сообщения другим чатам не отправлялись, DP не редактировались.

**Checks:** existing Node tests **141/141**, pytest projector/codec **66 passed**, остальные команды и фактические результаты — в checks. Full pytest, mounted production browser/HTTPS, полный zodiac/palette/styles, zoom/device, PlantUML render и непроверенные lifecycle/recovery ветви явно NOT RUN. Номер ADR не зарезервирован: реестр заканчивается 0041, кандидат 0042 проверяется заново перед нормативной публикацией.

**Изменённые пути:** только developer_artifact.md; developer/task_d003_implementation_plan.md, implementation_plan.md, findings.md, checks.md; новые developer/task_d003_research_report.md, drawing_adr_draft.md, две sequences в developer/sequence_diagrams/ui/ и isolated developer/evidence/task_d003_research/**. Полный перечень и hashes — [package manifest](developer/evidence/task_d003_research/package_manifest.json). Старые handoffs / JSON / manifests, Manager / Analyst / Tester, gates, production и golden сохранены.

**Публикация / следующий шаг:** пакет **локальный DRAFT, commit / push / PR не выполнялись**, TechnicalPackageSHA пока отсутствует. Прежние Git-поручения завершили D004; текущая задача разрешает обновление ветки и исследование. После отдельного разрешения публикации передать точный TechnicalPackageSHA Manager → уже назначенные **TASK-T-004 и TASK-R-001** на одной версии; Analyst адресно по новому G03 случаю, затем решение Manager перед G3. Самостоятельных регистраций READY / APPROVED / DONE, production, принятия fallback или закрытия DP / TEST-FIND-WHEEL-002 нет.


## TASK-D-003 — публикационная версия технического пакета

**Автор / подпись:** Codex / Developer, 18.10.2026. **Отдельное поручение Owner:** «Комит пуш в dev/ui-chart-wheel; merge в change». Разрешены commit / push этой версии и Git-интеграция в change/ui-chart-wheel. Scope остаётся собственным техническим пакетом TASK-D-003; поручение не принимает DRAFT ADR / оценку / fallback, не меняет Manager-owned статусы / gates и не разрешает production implementation.

**Точная версия TechnicalPackageSHA** — commit, впервые добавляющий этот заголовок. Однозначный Git-resolver после создания коммита:

```text
git log --reverse --format=%H -G '^## TASK-D-003 — публикационная версия технического пакета$' -- docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md
```

Исходные `local / NOT_CREATED / EMPTY index` в предыдущем handoff, package manifest и validation JSON описывают snapshot перед публикацией и сохраняются как evidence; они не подменяют фактические commit/push/merge. Публикационный проход пересчитывает hashes после добавления этой записи, проверяет точный staged scope / LF-or-binary blobs и передаёт фактические SHA / parity в итоговом Git-handoff. MergeSHA интеграции фиксируется отдельно от TechnicalPackageSHA и не является approval исследовательских выводов.

**После публикации:** Manager получает [report / состав / ограничения / оценку](developer/task_d003_research_report.md) на точном TechnicalPackageSHA; следующие предметные проверки — TASK-T-004 и TASK-R-001 на одной версии, Analyst адресно по новому G03 случаю. В этом Developer-проходе сводка Manager / DP / чужие артефакты не редактируются.


## TASK-D-005 — оценка и план до допуска исполнения

**Автор / подпись:** Codex / Developer. Текущее поручение выполнено в предмете собственной оценки / плана: [assessment v1](developer/task_d005_implementation_plan.md). **STARTED D005 не объявлен**, новое исследование / run04 / ADR revision не выполнялись. Manager-owned статусы / gates / чужие артефакты сохранены.

**Git:** исходный HEAD `d24a24e04be32d0522674735388e9d2ea3e65c93`; `git fetch origin change/ui-chart-wheel`, `git merge --ff-only FETCH_HEAD` — exit 0 / fast-forward. **Фактический HEAD `0046ac75bd6582089b68a640f98fa65468c0607a`**; отдельно **AssignmentSHA `0046ac75bd6582089b68a640f98fa65468c0607a`** — текущая опубликованная ревизия промта / §2.20. До и после обновления рабочее дерево и index чистые; несвязанных изменений не было, reset / очистка / stash / staging не применялись. Материалы других ролей получены только из опубликованного Git.

**Contract / предметы:** AnalystContractSHA **`2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`** = принятый v3 + S1; A007 DONE / APPROVED, ожидать его или повторять Owner-выбор S1 не требуется. D003 `d24a24e` / CriteriaSHA `f6f289c` / A005 `4057d6e` / T004 `ad5206e` сохранены отдельно. R001 r2 — опубликованная Manager-сводка @ `0e590fa`, **исходного reviewer OutputSHA нет**; чужие reported solver / test результаты не называются моими проверками. A005 active pending-goal recovery применим; A006 по already_applied отдельный, независимую геометрию не блокирует.

**Собственная оценка:** **16–24 рабочих часа / 2–3 чд**; confidence средняя для bounded evidence / ниже средней для успешного drawing на 328. Предел всего эксперимента **12 часов внутри**, включая подготовку моделей, аналитику и browser/harness; аналитика ≤4, browser/harness ≤4. Срок — **до конца 3-го рабочего дня от отдельного STARTED**. Полный пакет за один рабочий день не обещаю; первый статус / риск и первый адресный авторский ответ возможны за рабочий день. Target / estimates reviewers остаются их собственными. Эскалация Manager → Owner через +1 рабочий день просрочки, заместителя нет, абсолютный календарь не назначен.

**Budget mapping:** в proposal 9–14 чд D005 размещён один раз: drawing 9–12 часов, controller/ADR 4–6, evidence/handoff 3–6 = 16–24. HTML-presenter явно выделен в controller: 6–10 часов общего подблока, в том числе D005 design 1–2 часа; будущая production реализация только после G3. Эти доли не прибавляются сверх parent-блоков / 9–14 и не означают approval общего бюджета. Неизвестный остаток D003 / 20–28 не вычислялся из старого elapsed и не назначался новому этапу. Reviewer 1,25–2,25 чд — ориентир, не моя оценка / утверждённый расход.

**План исполнения после допуска:** R001-01 revoke→removal→HTML B→guarded dispose→guarded draw; R001-02 write-authority изоляция старой async revision, а не только settlement guard; R001-03 sync/async local outcomes / stale reject; R001-04 retained keyed HTML controls. F/E сравнение с аналитическими certificates / точными construction-counterexamples для frames720/448/328, затем ограниченный run04; visual annulus не ограничивает Q автоматически, grid optimum не считается continuous upper bound. E с новым наблюдаемым действием останавливает только E-browser до адресного semantic решения; F/аналитика/boundary продолжаются. Пороги 0,5/2/1/16/12/44 сохранены, fixed-ring16°/40° не дорабатывается.

**S1 в проектировании:** cardinality по полному accepted DTO до filters, source rows/order/from-to/category/orb без dedup; только ambiguous группа без graphic/aspect-select и с доступным local warning. Unique reverse/другой type/unaffected point/pair и accepted0/1/>1 reconcile различены; failed read не обновляет индекс; восстановление unique не выбирает снятый aspect автоматически. F5 U/R/D/V/M/L/T/P включены как future expected mapping, **runtime F5 / production S1 не исполняются в D005**.

**Проверки / локальное состояние:** documentary commands / scope / hashes / links / tables / `git diff --check` — [новый preparation audit](developer/evidence/task_d005_preparation.json), [checker](developer/evidence/task_d005_preparation_check.py). Точные результаты после запуска дописываются ниже. D003/run03/старые manifests, ADR и sequences сохранены неизменными. Node/pytest/browser/SVG/solver/PlantUML и новые experimental data не запускались / не создавались. OutputSHA оценки пока отсутствует, локальные четыре Developer-файла; commit / push / PR не выполнялись.

**Следующий конкретный шаг:** Owner согласует scope assessment v1, **16–24 часа / 2–3 чд**, эксперимент **≤12 часов** внутри (browser/harness ≤4), срок **до конца третьего рабочего дня от отдельного STARTED** и явно поручает начать D005. Тогда Developer записывает фактический STARTED / источник допуска и выполняет согласованное исследование. После результата / отдельно разрешённой публикации Manager закрепляет TechnicalPackageV2SHA → T007 / R002; G3 production остаётся отдельным решением.


**D005 — фактические проверки подготовки:** `python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_preparation_check.py --write`, затем та же команда без `--write` — **D005_PREPARATION_OK**, exit 0: paths=4, docs=43, links=1247, tables=107, source_hashes=29, contract=5/5, D003=164/164_UNCHANGED, index=EMPTY, STARTED=NO, spike=NOT_RUN, ADR_revision=NOT_RUN. `git diff --check` — exit 0. Первый запуск нового checker остановился на PNG из-за ошибочной LF-нормализации бинарных данных; исправлен только новый checker, PNG сравниваются raw, повтор подтвердил неизменность прежнего evidence. Это ошибка documentary helper, не изменение D003 и не runtime defect. После добавления этой записи JSON audit обновляется и повторно сверяется по текущим hashes; прежние audit/manifests не переписываются. Четыре локальных пути — plan, appended index, preparation checker и его новый JSON; stage/commit/push отсутствуют.


## TASK-D-005 — публикация оценки и плана

**Автор / подпись:** Codex / Developer. Основание отдельной публикации — прямое поручение Owner в этом чате: «Выполни комит пуш в dev потом merge в change». Публикуются только четыре пути подготовки assessment v1, перечисленные в предыдущем handoff. Scope исполнения / оценка / timebox / срок D005 остаются предложением до явного согласования Owner; **STARTED D005 не объявлен**, spike / run04 / ревизия ADR не выполняются. Статусы Manager, gates и чужие артефакты не меняются.

**AssessmentSHA:** коммит, впервые добавивший этот заголовок; воспроизводимый resolver:

```text
git log --reverse --format=%H -G '^## TASK-D-005 — публикация оценки и плана$' -- docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md
```

Это версия оценки / плана, **не TechnicalPackageV2SHA** будущего исполнения. Commit/push dev и MergeSHA change проверяются отдельно; точные SHA и remote parity передаются в итоговом Git-handoff. Исходные local / NOT_CREATED / EMPTY index в preparation JSON и предыдущем handoff сохраняют snapshot до публикации. После добавления этой записи новый preparation audit пересчитывает hashes текущего пакета до staging; прежние D003 audits/manifests остаются неизменными. Разрешение на публикацию не заменяет требуемое решение Owner о начале D005.


## TASK-D-005 — STARTED после согласования Owner

**Автор / подпись:** Codex / Developer. Источник допуска — прямое сообщение Owner в этом чате 19.10.2026: «Как Owner согласовываю scope и оценку TASK-D-005: 16–24 часа, эксперимент до 12 часов внутри оценки, передача до конца третьего рабочего дня от STARTED. Начинай TASK-D-005, зафиксируй STARTED и срок передачи».

**STARTED: 19.10.2026 00:15:25 MSK (UTC+03:00). Срок передачи: до конца 21.10.2026, Europe/Moscow**, третий рабочий день, считая 19.10 днём 1 (пн–пт; час окончания рабочего дня не задан). Согласованы assessment v1 / 16–24 рабочих часа / 2–3 чд, единый эксперимент ≤12 часов внутри, вложенные лимиты аналитики ≤4 и browser+harness ≤4. Подготовка учитывается один раз внутри оценки; достоверный суммарный труд до STARTED и остаток D003 не вычисляются. При прогнозе превышения — конкретное влияние Manager до лимита; эскалация Manager → Owner через +1 рабочий день просрочки.

**InputSHA / фактический HEAD:** `34f187aa81ddad7760089f54c1dc23d4d9e59d59`; прежний локальный HEAD `5eba30f74ce9af85fc13be048d3c0898f9d1a2cb`, fetch и fast-forward — exit 0. **AssignmentSHA:** `0046ac75bd6582089b68a640f98fa65468c0607a`; **AssessmentSHA:** `5eba30f74ce9af85fc13be048d3c0898f9d1a2cb`; **AnalystContractSHA:** `2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`. Новый merge не изменил существенные входы. Index и дерево до начала чистые, несвязанных изменений нет. A007 принят; A006 / отсутствующий reviewer OutputSHA не блокируют независимую работу. Исторические «не начат / требуется согласование» относятся к snapshot оценки, superseded этим Owner-допуском.

Начато исполнение ограниченного исследования / ревизии DRAFT ADR по §2.20 и плану. [Исходный журнал](developer/evidence/task_d005_feasibility/execution_start.json) фиксирует источник, сроки и хеши baseline. D003/run03/старые manifests остаются неизменными. Это авторское подтверждение; сводка Manager / gates / чужие материалы не редактируются, G3 / production не разрешены. Новый результат остаётся локальным до отдельного поручения commit/push/PR.


## TASK-D-005 — результат ограниченного исполнения, локальный DRAFT

**Автор / подпись:** Codex / Developer, 19.10.2026. Owner scope/16–24/experiment≤12/третий рабочий день согласовал прямым сообщением; STARTED **19.10.2026 00:15:25 MSK**, передача **до конца21.10.2026 Europe/Moscow**. Предыдущий STARTED / assessment handoff сохранены, время commit не использовано как STARTED.

**InputSHA:** `34f187aa81ddad7760089f54c1dc23d4d9e59d59`; **AssignmentSHA:** `0046ac75bd6582089b68a640f98fa65468c0607a`; **AssessmentSHA:** `5eba30f74ce9af85fc13be048d3c0898f9d1a2cb`; **AnalystContractSHA:** `2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`. D003d24a24e/run03/report/старые manifests сохранены; текущий DRAFT ADR/sequences явно ревизированы для D005, исходные D003 версии остаются на d24a24e. Source R001r2 только Manager summary, исходного reviewer OutputSHA нет. A007 принят, A005 использован, A006 already_applied условный отдельный вход.

**Результат:** [report / критерий→данные→actual→вывод](developer/task_d005_feasibility_report.md), [новые findings](developer/task_d005_findings.md), [ревизия DRAFT ADR](developer/drawing_adr_draft.md), [sequence001](developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml) / [002](developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml), [обновлённый план](developer/task_d005_implementation_plan.md). Revoke→removal→HTML B→guarded dispose→draw; revision-scoped value-frame sink до settlement; sync/async local faults; retained HTML и принятие S1 по полному DTO до filters. Runtime S1/F5 не выполнялись; no producer-provenance claim.

**Drawing negative:**24 F/E клетки720/448/328,14/24 measured-component geometry,241/438 conditional Q certificates,238/2190 native owner/outcome mismatch;438/438 keyboard-проверок без потери active target.256 full positive return-prefix witnesses отклоняют compactness projection. Новая модель явно отличается от D004 chord path/radii/movable angles, thresholds0,5/2/1/16/12/44 сохранены. Zodiac/sign text/palette не моделировались, partial успех не whole drawing PASS. Текущий candidate не рекомендуется к реализации, глобальная невозможность / исключительность E не доказаны.

**Evidence:** [raw final run04-delivery](developer/evidence/task_d005_feasibility/run04-delivery/index.json), [independent actual audit](developer/evidence/task_d005_feasibility/browser_audit.json), analytic exact controls9, isolated boundary12/12 и browser/HTML/focus controls12/12, все2190 native deliveries записаны глобальным capture. Первый run04 и исходники сохранены; повтор тех же inputs исправил отсутствие delivered coordinates у10 промахов, без изменения model spec. Helper zero-prefix/variable-shadowing исправления и исходный partial audit честно описаны в report. Реальные Segoe UI Symbol/Segoe UI, M/scale/DPR1, coordinates/bbox/screenshots/hashes сохранены. Parent experiment окончательно stopped `2026-10-19T11:12:57.167959+03:00`, wall bound10.9589h<12 включает ожидания и не является effort/timesheet; новые эксперименты после final stop не выполняются.

**Оценка / ограничения:** дополнительного расхода не запрошено; D005 включён один раз в9–14 proposal, HTML-presenter6–10 внутри controller, D005 design1–2. Полная реализация9–14 **не подтверждена** без принятого drawing, confidence низкая; конкретные контрпримеры подтверждены с высокой уверенностью. Неизвестный остаток D003 не вычислен. Следующий новый model/scope требует адресной постановки/оценки через Manager; семантика — Analyst/Owner. Full production/mounted HTTP/HTTPS, runtime F5/S1, cross-platform/touch/zoom/full overflow, full product tests и PUML render NOT RUN.

**Публикация / следующий шаг:** новый TechnicalPackageV2SHA **NOT_CREATED**, результат локальный, index сохранён пустым, commit/push/PR не выполнялись. Точный перечень путей/hash/scope/командных actual — [manifest](developer/evidence/task_d005_feasibility/package_manifest.json) / [package audit](developer/evidence/task_d005_feasibility/package_audit.json). После отдельного поручения публикации Manager закрепляет один TechnicalPackageV2SHA → **TASK-T-007 / TASK-R-002**, затем решение по следующей геометрии и отдельный G3 для production. Manager-owned task statuses / gates / DP / чужие артефакты не изменены. Developer first triage за1 рабочий день; escalation Manager→Owner через+1 рабочий день просрочки.


**D005 — фактические проверки исполнения:** `python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/audit_package.py --write`, затем без `--write` и `git diff --check` — итоговый проверяемый проход. Первый успешный package audit: **D005_PACKAGE_OK**, payloads162 (ещё2 self-metadata отдельно), baseline604 unchanged, D003 archive164/164, native2190 / keyboard438, controls9+12+12, docs45 / links1301 / tables111, Python AST6 / Node syntax3 / PUML structure2, diff_check0 / indexEMPTY / publicationNOT_RUN. После этой записи audit/manifest пересчитываются и повторно сверяются. Binary `.bin`/PNG сравниваются raw, text — LF; первоначальная ошибочная нормализация golden остановила helper, сам golden не изменён. Structural PUML не называется render PASS. Локальные OutputSHA/TechnicalPackageV2SHA по-прежнему NOT_CREATED.


## TASK-D-005 — публикационная версия результата

**Автор / подпись:** Codex / Developer. Основание — отдельное прямое поручение Owner в этом чате: «Комит пуш в dev затем merge в сhangs»; существующая интеграционная ветка — `change/ui-chart-wheel`, ролевая — `dev/ui-chart-wheel`. Публикуется только проверенный результат TASK-D-005: восемь собственных документов и новое task_d005_feasibility evidence, без изменений Manager/gates/чужих артефактов/production. InputSHA до публикации `34f187aa81ddad7760089f54c1dc23d4d9e59d59`; AssignmentSHA0046ac7 / AnalystContractSHA2736e28 остаются закреплёнными предметами.

**TechnicalPackageV2SHA:** коммит, впервые добавивший этот заголовок. Воспроизводимый resolver:

```text
git log --reverse --format=%H -G '^## TASK-D-005 — публикационная версия результата$' -- docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md
```

Это новый результат исполнения D005, **не AssessmentSHA5eba30f и не D003d24a24e**. MergeSHA интеграции фиксируется отдельно и не означает принятия drawing/ADR/G3. Фактические commit/push/merge и remote parity передаются в итоговом Git-handoff после выполнения. Локальные NOT_CREATED / publicationNOT_RUN / EMPTY index в report, audit и прежнем handoff — сохранённый snapshot до этой публикации, superseded её проверенным Git-результатом. Manifest/audit перед staging пересчитываются только для текущей записи; raw research runs/spec/старые manifests остаются неизменными. Staged scope и каждый blob сверяются с manifest до коммита, опубликованные refs — после push.

**После публикации:** Manager закрепляет этот TechnicalPackageV2SHA для адресных TASK-T-007 / TASK-R-002. Конкретный drawing-кандидат остаётся отрицательным результатом, DRAFT ADR не становится принятым, следующий geometry-route / G3 решаются отдельно. Developer не изменяет статусы этих reviews, сводку Manager и чужое авторство.


## TASK-D-006 — подготовка первого controller/HTML этапа

**Автор / подпись:** Codex / Developer, 19.10.2026. До начала сообщены оценка подготовки **0,5–1,5 ч**, confidence высокая и target ответа за 1 рабочий день. **STARTED подготовки: 19.10.2026 13:01:09 MSK** (clock10:01:09UTC); план передаётся в этом проходе 19.10.2026. Это не STARTED runtime implementation. Источник — Manager §2.22/2.23 и прямой запрос Owner «Обновись / И давай найдем уже решение и начнем реализацию».

**Git/input:** исходный8b8c4c818147b037cb90f93a42e64eb86d809183 → fetch/ff **InputSHA 07bb56ba5d49ec76de64df41ad80d175fbe90a2d**, exit0. Отдельно **AssignmentSHA 07bb56ba5d49ec76de64df41ad80d175fbe90a2d**, историческое назначениеdff5757. До начала index/дерево чистые, несвязанных изменений нет. Старый AnalystContractSHA2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 сохраняет свой предмет; новая Owner-дельта DP-O-008 принята @07bb56b, A008 exact contract пока отсутствует. Материалы ролей только Git; ls-remote показал analysis2736e28 / testad5206e, новые verdict T007/R002 в полученном change не опубликованы.

**Готовый результат:** [конкретный план CH-01…05 / зависимости / оценки](developer/task_d006_controller_html_plan.md). Рекомендуется односторонний HTML→selection→passive SVG; первый scope — реальный canonical state/accepted event/retained HTML/S1/editor/recovery integration, **14–22 ч /1,75–2,75чд**, confidence средняя, до конца третьего рабочего дня от отдельного STARTED при готовых входах. CH-01-P already_applied не реализуется по default до A006; это не blocker независимых CH-02/03. CH-SVG/geometry/full writer исключены, production placeholders не предлагаются. Для R002 дан более простой passive-root copy/install вариант, а не принятие D005 generic writer; количественная экономия не заявлена.

**Бюджет:** подготовка 0,5–1,5 ч отдельно от future14–22; прежний HTML6–10/controller16–24 не считается остатком; D003/D005/design не начисляются повторно. Полные9–14чд остаются неподтверждённым forecast, неизвестный труд/остаток не вычислен. Новый scope/14–22/срок пока предложение для конкретного Owner-решения, не самовольный G3.

**Изменения:** только новый developer/task_d006_controller_html_plan.md, appended собственный implementation_plan.md и этот handoff. Production/src/tests, Manager/DP/gates/чужие артефакты, D003/D005 evidence/manifests/ADR не изменены. Старые role indexes сохраняют историю prefix. Новых repo-checker/evidence/spike нет; product Node/pytest/browser/geometry/PUML NOT RUN. Документальные команды / actual приведены ниже; новый OutputSHA пока NOT_CREATED, commit/push/PR/сообщения другим чатам не выполнялись.

**Следующее конкретное решение:** Owner согласует CH-01…05 на 14–22 ч/до 3 рабочих дней и исключения; Manager закрепляет A008 exact contract, адресно применяет T007/R002/DP-O-010 к выбранным work items, разрешает ограниченный G3 и назначает реализацию. Для подготовки эти verdict не ожидались. Новый STARTED кода фиксируется только для реально допущенного объёма; G3/общие статусы здесь не меняются. Developer triage за 1 рабочий день; escalation Manager→Owner через +1 рабочий день просрочки.


**D006 — фактические проверки / подпись Codex, Developer, 19.10.2026:** `python -B -X utf8 C:/Users/KateUser/AppData/Local/Temp/task_d006_validate.py` — exit 0, **D006_DOCUMENTS_OK**: paths=3, docs=48, local links/anchors=1367, tables=115; D005 archive=162/162, current=160 unchanged + 2 append-only собственных индекса. Проверены пустой index, точные HEAD/ветка/AssignmentSHA, scope, сумма нижней/верхней оценок, сохранность старых sections и отсутствие production/Manager/чужих изменений. Это временная read-only документальная проверка вне репозитория; новый checker или evidence-пакет в change не добавлялись. Первоначальная неверная ссылка нового плана на §3.1 исправлена, повторный проход зелёный. Запуск внутри sandbox остановлен ограничением доступа linked Git, разрешённый повтор — exit 0; это не product failure.

`git diff --check` — exit 0 без замечаний; новая untracked Markdown-редакция отдельно проверена на trailing whitespace / таблицы / ссылки тем же документальным проходом. `git diff -- <два собственных tracked пути>` просмотрен: только дополнения D006, CRLF-конверсия Git не меняет сохранённую LF-историю. После этой записи тот же read-only проход и diff-check повторяются для окончательного состояния. Node/pytest, browser/native focus, SVG/font/geometry, PUML render **NOT RUN**: исполняемое поведение этим заданием не менялось. Результат подготовки готов локально; index EMPTY, OutputSHA NOT_CREATED, публикация не выполнялась. Независимые CH-02 + CH-03 — **7–10 часов внутри 14–22**, рекомендуемый первый поднабор для ограниченного G3 после текущего контракта A008; ожидание A006/геометрии для них не требуется.


## Геометрия v3 — handoff прямого поручения Owner

**Автор / подпись:** Codex / Developer,19.10.2026. Источник: «Переработай и предложи альтернативные варианты если они есть». InputSHA/HEAD **07bb56ba5d49ec76de64df41ad80d175fbe90a2d**; fetch change exit0, опубликованный HEAD тот же, merge не требовался. Assignment — это прямое поручение, без присвоения нового Manager TaskId / STARTED реализации. STARTED исследования `2026-10-19T10:44:01.302465+00:00`, STOP `2026-10-19T11:27:48.942725+00:00`, wall43.794мин <90, не effort. D005 stop / package8b8c4c8 / D003d24a24e и текущий D006 сохранены.

**Результат:** [переработка / альтернативы / ограничения](developer/drawing_geometry_v3.md), [result summary](developer/evidence/drawing_geometry_v3/result_summary.json), [exact verifier](developer/evidence/drawing_geometry_v3/verification.json), [native final audit](developer/evidence/drawing_geometry_v3/actual_final_audit.json). BASE+A…H108 models /108 browser records/screenshots;10 exact controls и8 controls в каждом из3browser runs. H geometry12/12, native coordinate/component identity12/12, tight108/110 / whole studied predicates10/12. F3/720 Jupiter и F3-max/720 true_node — **FAIL**, оба допускают full0,5px return и не проходят1px probe. Высокая confidence этих фактов; whole drawing / full zodiac / production не подтверждены.

**Рекомендация:** взять H как техническую основу, адресно закрыть2desktop witnesses и добавить не измеренные fixed zodiac/legend labels до принятия drawing. Дешёвые one-ring / radial / CSP seeds сравнены; внешние callout-колонки / taller canvas — NOT RUN и отдельное domain/composition решение Owner/Analyst, не fallback по умолчанию. Новая физическая SVG reference-конвенция / straight-chord path явно вынесены на technical review, не приняты этим handoff. Legacy SVG Q44/focus исключены Owner, HTML44px здесь не проверялся.

**Scope / бюджет:** только новый developer/drawing_geometry_v3.md, evidence/drawing_geometry_v3/ и append собственных index/plan. Не начислять D003/D005 повторно и не прибавлять wall-time к D00614–22/условным9–14чд. Controller/HTML остаётся независимым work item; production требует своего назначения/G3. Runtime Node/pytest product suites / mounted UI / HTTPS / S1/recovery / cross-platform/zoom NOT RUN; исследовательские browser/font/geometry проверки выполнены, команды/actual в report. В процессе исправлены документированные helper defects с сохранением промежуточных результатов; старые published evidence не подменены.

**Локальное состояние:** index EMPTY, новый OutputSHA NOT_CREATED; commit/push/PR/merge/сообщения другим чатам не выполнялись. Manager/gates/DP/чужие материалы и прежний D006 plan не менялись. Следующий шаг — отдельно разрешённая публикация → Manager назначает адресную сверку нового proposal/версии; старые T007/R002 не переадресуются самовольно. Фактический финальный package audit / diff-check подписываются ниже.


**Геометрия v3 — фактические финальные проверки / подпись Codex, Developer:** `python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/audit_package.py --write` — exit0, **V3_PACKAGE_OK**: payloads368; models/native records/screenshots108; exact controls10, browser controls24; H geometry12/12, tight108/110, full studied cells10/12 /2FAIL. D005 archive162/162 / current160 unchanged+2 append-only; D006 hash/prefix preserved. Docs49 / links1381 / tables117, Python AST14 / Node syntax6; diff-check0, indexEMPTY, Manager/foreign/productionUNCHANGED. После этой записи self-manifest пересчитывается и проверяется тем же audit без `--write`; исторические research raw не меняются. Прямой `git diff --check` повторяется для финального состояния. Product Node/pytest / mounted UI / HTTPS NOT RUN, вывод research checks им не присваивается. Все фактические commands/limitations и2concrete prefix witnesses сохранены в report / result_summary; новые модели после STOP не запускались. Результат локальный, нового OutputSHA нет.


## Решение Owner — условная выносная колонка, 19.10.2026

**Автор решения:** Owner, прямое «да, хорошо записывай финальное решение» после обсуждения условий применения колонки. **Записал / подпись:** Codex, Developer. [Подтверждённый выбор, дословное evidence и адресная дельта существующих DP](developer/owner_decision_drawing_2026-10-19.md). Это зафиксированное решение Owner, не новая рекомендация / запрос повторного согласования.

InputSHA/HEAD07bb56ba5d49ec76de64df41ad80d175fbe90a2d / dev/ui-chart-wheel; index EMPTY, прежние локальные D006/v3/preview сохранены. Для регистрации Manager указан тот же DP-O-011/012 и затронутые контрактные пункты; единый реестр / статусы / gates / чужие материалы не редактировались. Узкая актуализация Analyst/technical domain ещё впереди; G3 / production и geometry PASS нового layout не объявлены. Старое предложение выносной колонки в v3/preview теперь имеет подтверждённый Owner-выбор в этом scope; старые measurements/manifests сохраняют историческую версию.

Документальные проверки / фактический diff-check записываются после проверки. Commit/push/PR/сообщения другим чатам не выполнялись. Новый OutputSHA NOT_CREATED.


**Owner drawing decision — проверки записи** / Codex, Developer: `python -B -X utf8 C:/Users/KateUser/AppData/Local/Temp/wheel_validate_owner_decision.py` — exit0 / **OWNER_DECISION_DOC_OK**. Проверены4 собственных документа, все51 Markdown в change /1397 links/anchors /118 tables; прежний v3 payload366 unchanged+2 append-only, preview3 renders unchanged, все предыдущие sections preserved. `git diff --check` — exit0 без whitespace errors; runtime/product/browser tests NOT RUN для документального изменения. Index EMPTY; Manager/foreign/production/gates unchanged; публикация NOT RUN. После подписи тот же read-only validator и diff-check повторяются для итогового состояния.


## Полное колесо — подготовка колонки и renderer,19.10.2026

**Подпись:Codex / Developer.** Прямое поручение Owner: «Проработай правила выносной колонки, проверь полную композицию и границу renderer. Подготовь план и оценку реализации всего колеса». InputSHA/HEAD до/после fetch **07bb56ba5d49ec76de64df41ad80d175fbe90a2d**, dev/ui-chart-wheel; published change тот же, интеграция не нужна. AssignmentSHA отдельного commit нет, источник — это сообщение. Исходные AnalystContract2736e28/v3+S1, Manager§2.23 и прямой Owner выбор колонки сохранены. Нового TaskId/production STARTED/G3 не создаю. STARTED подготовки19:12:00MSK, final STOP20:23:49MSK /71,8126мин wall≤90; post-audit выявил shared branch после первого stop и адресно исправлен внутри прежнего timebox, оба события сохранены.

**Результат:** [измеримые правила и полная композиция](developer/column_renderer_design_v1.md), [DRAFT ADR](developer/drawing_adr_column_draft.md), [FW01…06/план/оценка](developer/full_wheel_implementation_plan.md), [исполняемая постановка05](developer/prompts/05-full-wheel-passive-column.md), technical sequences003/004 по ссылкам ADR; [evidence/команды/ошибки/пределы](developer/evidence/column_full_composition_v1/README.md). Рекомендация: conditional measured column + revision-local surface/guarded copy-install. Старый D005 value-frame draft/sequence001/002 не переписаны.

**Факты:** final run07-ports29/29 full measured SVG configurations, gap≥2px, max anchor error0,010848716508144922px, IDs/R/source facts/frozen labels сохранены. Independent C0/order/row/leader clip/no shared centerline29/29;13/13 native threshold/clip/scale controls,4/4 rational gap+3/3 route controls;28/28 isolated boundary с реальным SVG и retained live HTML focus, late/current/reentrant/error/dispose controls. Auxiliary observations92 exact native contacts+12 unmoved+3 hidden-mode exemptions, не107 видимых измерений.29 configurations не означают29 независимых domain charts; исходные/current/native материалы сохранены. Shared-route run05 report ожидаемо negative, run06 finite graph failure не доказательство невозможности.

**Оценка/срок:** future implementation40–64 рабочих часа /5–8чд, medium confidence,≤8 рабочих дней от отдельного STARTED; FW01 уже включает D00614–22/HTML-presenter и поднабор7–10. Подготовка/D003/D005 не начисляются повторно; unknown остаток не выводится. Это предложение Owner, не принятый бюджет. Нужны exact target narrow contract/применимые technical decisions и G3; A006 касается только affected cause wiring, не независимого HTML/геометрии. Срок ответа reviewers предлагается1 рабочий день, Manager→Owner escalation+1 день просрочки, без выдуманного заместителя.

**Проверки:** browser.cjs run07-ports exit0; audit.py run07-ports exit0; postaudit_final.py run07-ports exit0, run05-final exit1 expected negative. Существующие Node UI suites188 PASS/0 FAIL exit0; это baseline, не feature tests будущего кода. Ссылки/syntax/сохранность/diff-check подписываются финальным аудитом ниже. Runtime production integration/HTTPS/full pytest/другие ОС и браузеры/zoom/PlantUML rendering NOT RUN. Ограничения: bounded fixtures, нет universal arbitrary-DTO или unlimited-☌ feasibility/performance SLA; самостоятельного принятия нового fallback нет.

**Изменённые области:** новые собственные design/ADR/plan/prompt/2sequences/evidence; append только собственных implementation_plan.md и developer_artifact.md. Старые D003/D005/v3/preview/Owner source decision/D006 plan и чужие Manager/Analyst/Tester/production сохранены. Index EMPTY; новый OutputSHA/CandidateSHA NOT_CREATED. Commit/push/PR/merge/сообщения другим чатам NOT RUN. Следующий шаг: отдельная публикация → Manager закрепляет новый SHA/адресные reviews/target contract; Owner решает scope40–64ч/≤8 дней; после применимого G3 отдельный STARTED реализации. Продуктовый выбор колонки/S1/table-only повторно не согласовывается.


**Финальная проверка пакета / подпись Codex, Developer:** `python docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/validate_package.py --write` — exit0 / COLUMN_PACKAGE_OK; затем тот же validator без `--write` сверяет manifest. Проверены1456 прежних payloads unchanged+2 собственных index append-only, весь index byte-for-byte unchanged и EMPTY; frozen source/screenshot hashes,7 Markdown/2 PUML structures, local links/таблицы и Node/Python syntax. Точные финальные счётчики — [validation.json](developer/evidence/column_full_composition_v1/validation.json), [checks/NOT RUN](developer/evidence/column_full_composition_v1/checks.json). `git diff --check` exit0. Native final29/29, boundary28/28, unique controls20/20; baseline UI188 PASS. Production/golden/Manager/foreign roles неизменны. Full pytest/production HTTPS/PlantUML render NOT RUN; commit/push/PR/merge NOT RUN, новый OutputSHA отсутствует.


## Публикация подготовки полного колеса — отдельное поручение Owner

**Codex / Developer, 19.10.2026.** Owner разрешил commit/push в dev, затем merge в change. Fetch origin dev/ui-chart-wheel change/ui-chart-wheel — exit0; Developer HEAD / published change:07bb56ba5d49ec76de64df41ad80d175fbe90a2d, remote dev:8b8c4c818147b037cb90f93a42e64eb86d809183. Developer index EMPTY; integration worktree change HEADcc4ecfff0208a15c64ae976bf5d6463cd47636ae, index EMPTY, дерево чистое. Старые NOT_RUN/NOT_CREATED и baseline/index assertions исследовательских checkers сохраняются как снимки до публикации.

Scope: D006 plan, geometry v3 с отрицательными controls, prototype, подтверждённый Owner выбор колонки и новый full composition/renderer/implementation plan. До staging повторён validate_package.py:29/29 SVG,28/28 boundary,20/20 calibrations. Product baseline188 PASS получен ранее при подготовке, заново не запускался. Production, Manager/DP/gates и чужие артефакты вне scope.

Git policy text=auto нормализует index в LF, часть raw payloads содержит CRLF. Старые JSON/manifests/source/screenshot bytes не переписываются. [Publication audit](developer/evidence/column_full_composition_v1/publication_audit.py) и [карта raw/Git LF SHA](developer/evidence/column_full_composition_v1/publication_2026-10-19.json) проверяют каждый публикуемый blob и восстанавливают исходные байты в памяти по zero-based CRLF line indices. Три self/generated metadata проверяются отдельно. Frozen hashes не являются хешами произвольного checkout. Это Git-проверка, не новое runtime evidence.

Команды: publication_audit.py --prepare; validate_package.py --write и без --write до staging; publication_audit.py --index; git diff --cached --check; после коммита publication_audit.py --commit <TechnicalPackageSHA>. Точный commit/push/integration SHA и реальные исходы передаются итоговым Git-handoff; эта запись не объявляет будущие команды выполненными. Версия записи определяется через git log --format=%H -G '^## Публикация подготовки полного колеса' -- docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md.

Следующий шаг: Manager закрепляет TechnicalPackageSHA для адресной проверки/target contract и применимых решений; Owner решает scope40–64ч/≤8 рабочих дней; после применимого G3 — отдельный STARTED реализации. Публикация/merge не подтверждают approval, G3 или STARTED production.


**Публикационный audit — исправление / Codex, Developer:** первый package commit5fdc4771d97307b2803fbe0f20a4833abfec645b опубликован в обе ветки fast-forward. В дополнительной проверке CRLF-checkout выявлена квадратичная операция создания множества для каждой строки; собственный read-only процесс остановлен, изменения runtime отсутствуют. Нормализация заменена одним проходом bytes.replace; --index сверяет весь index с InputSHA baseline, поэтому применим и к публикационному follow-up. Raw/Git LF карта и текущий package manifest обновлены только для этого audit/подписи; research sources, старые manifests, screenshots и frozen runs не менялись. Повторные Git audit --index/--commit и check после CRLF-checkout выполняются до итогового отчёта; их реальные исходы и окончательный SHA передаются отдельно. Старые validate_package.py HEAD/index assertions и validation.json остаются pre-publication snapshot; новое runtime evidence не заявляется.
