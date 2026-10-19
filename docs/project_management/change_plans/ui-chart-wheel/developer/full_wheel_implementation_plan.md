# Полное колесо — Implementation Plan и оценка оставшейся реализации

**DRAFT / Codex, Developer, 19.10.2026.** Результат прямого поручения Owner о колонке, полной композиции и renderer. InputSHA/HEAD **07bb56ba5d49ec76de64df41ad80d175fbe90a2d**; Assignment — прямое сообщение, без отдельного AssignmentSHA в Git. Нового implementation STARTED нет. [Технический проект/measurements](column_renderer_design_v1.md), [DRAFT ADR](drawing_adr_column_draft.md), [единый реестр/сводка](../manager_artifact.md). Статусы/gates принадлежат Manager.

## 1. Собственная оценка и включение прежней подготовки

**Оставшаяся реализация всего принятого scope:40–64 рабочих часа /5–8 чд при8ч/день. Confidence — средняя.** Включены controller/HTML, реальный passive SVG, колонка, lifecycle, wiring, Developer regressions/browser checks и актуализация итогового technical package. Цель передачи — **до конца восьмого рабочего дня от отдельного STARTED реализации**, если к старту доступны применимые contract/technical decisions, а A006 получен не позднее начала затронутой интеграции. Это предложение Owner, не уже согласованный бюджет.

| Work item | Часы | Наблюдаемый результат / подход | REQ / AS / DP | Ответственные места / checks |
|---|---:|---|---|---|
| FW-01 — canonical state и retained HTML |14–22 | Полный S1 index, point/aspect toggle, five/all, accepted once cause, draft/summary/editor/recovery и live focus. TDD для state/cause; keyed patch→mounted/native checks для HTML | REQ-WHEEL-04/07/08/09/10/11; REQ-UI-01…11; AS-WHEEL-11…24/26…30; DP-O-008/010/013 | session/main/facts + фактически используемый controller/state module; [D006 CH-01…05](task_d006_controller_html_plan.md), tests/ui facts/session/recovery/form |
| FW-02 — полный SVG и условная колонка |12–18 | Зодиак, source points/R/cusps/angles, exact/working/☌/S1, palette/legend, C0/row layout/leader ports/resize. TDD для чистых геометрических predicates и lifecycle-independent layout; реальный SVG→native measurements для fonts/paint | REQ-WHEEL-01…06/09/10; AS-WHEEL-01…10/16/22/25/26/28/30; DP-O-004/007/011/012/014 | Новые `wheel_layout.mjs`, `wheel_svg.mjs` только с реальным использованием; существующие DTO fixtures и новые SVG checks; не копировать research harness в production целиком |
| FW-03 — renderer boundary |4–6 | Revision-local surface, guarded clone/install, factory/sync/async failure, dispose/replace/reentrant guard/late callbacks. TDD на управляемых deferred promises, current/stale и alternate controls | REQ-WHEEL-01/10/11; AS-WHEEL-01/02/22/24; DP-O-010, R001-01…04 | Внутренний result controller; native DOM seam и реальный leaf; изолированный research28 не становится regression suite приложения автоматически |
| FW-04 — подключение настоящего SVG к странице |2–4 | Main соединяет already accepted state/HTML FW01 с настоящим leaf FW02/03; измерение host width, font revision, empty/unavailable, локальный SVG error. Реализация→интеграционные проверки | REQ-WHEEL-01/08/09/10/11; AS-WHEEL-01/02/04/17…22/24/26 | main/controller/styles/index; реальные session/form/facts, fake только network/clock; это SVG-добавка, не повтор FW01 HTML wiring |
| FW-05 — проверки полного пути и пакета |6–10 | Целевые→связанные→full pytest; browser widths1440/768/360, selection/background/S1, native pointer+keyboard HTML44/focus, resize/font/late faults, installed resources. Достаточное старое покрытие переиспользуется | Все строки; AS-UI-22 и AS-WHEEL-01…30 по применимости | tests/ui + tests/http_api/test_ui_delivery.py + module boundaries; production CandidateSHA только после разрешённой публикации |
| FW-06 — фактические ADR/sequences/evidence/handoff |2–4 | Актуализированный по реализованному поведению DRAFT/принятый владельцем technical decision, команды/ограничения/передача reviewers. Документальные checks | REQ-WHEEL-11; DP-O-010…013; G4/G5 по процессу | Собственные Developer artifacts/sequences; чистовой нормативный перенос после acceptance — отдельное назначение |
| **Всего** | **40–64** | **5–8чд** | **Полный implementation scope** | **Независимый Tester effort и ожидание review не включены** |

FW-01 **уже включает** D00614–22 и HTML-presenter; повторно его не прибавлять. Независимый первый CH-02/03 поднабор7–10ч находится внутри FW-01, а не поверх40–64. FW-04 включает лишь SVG-wiring, FW-05 — добавочные full-wheel проверки, не повтор HTML checks FW-01. FW-06 — будущая синхронизация по факту кода; текущая исследовательская подготовка уже выполнена и второй раз не начисляется. D00516–24, D00320–28 и предыдущие эксперименты не включаются заново. Wall71,8126мин текущего исследования не является timesheet.

Прежний9–14чд — исторический условный forecast, не новый согласованный остаток.40–64ч — новая оценка **будущей реализации** по выбранному пассивному SVG/колонке. Без фактического учёта уже затраченного времени нельзя вычислить полный lifetime budget change, экономию или неизвестный остаток D003. Manager сопоставляет прогноз с фактом и передаёт Owner влияние; автоматического увеличения/уменьшения прежнего бюджета нет.

## 2. Что именно станет готовым

После подтверждённого ChartDTO сразу показываются SVG и birth summary, все points, первые5 source aspects и5 houses с независимыми show-all и compact angles. Только HTML controls выбирают point/aspect; SVG пассивно отражает выбор, в том числе фоновые endpoints без линии. Local S1 warning не скрывает исходные строки/направление/порядок/category/orb. Collapse editor не мешает recovery; submitted snapshot/once cause не заменяются проверкой identity или source=build. SVG fault не убирает актуальный HTML и не отправляет запрос.

Контракт — исходный нормативный UI/HTTP/ADR baseline5355510 плюс [change requirements/scenarios](../analyst/requirements.md) v3+S1@2736e28 и явно принятые более поздние Owner delta из [source decision](owner_decision_drawing_2026-10-19.md). Их точная целевая Analyst revision ещё должна быть опубликована; Developer не исправляет чужие требования сам. В частности старые SVG activation и adjacent ☌ category text заменены более поздним Owner-выбором; новая column minimality/domain ещё DRAFT. [Сводка §2.23](../manager_artifact.md#223-owner-выбор-только-через-таблицы-и-адресная-дельта-a008) и DP-O-010/011/012/013 — single source of lifecycle/decisions, не этот план.

## 3. Последовательность и допуск

1. После публикации этого конкретного пакета Manager регистрирует Owner delta в существующих DP, закрепляет точный новый TargetContractSHA и applicable technical approval. Узкий Analyst/Tester review меняет только затронутые definitions/expectations; принятие S1/A007 повторно не открывается.
2. Owner согласует40–64ч / полный scope / срок≤8 рабочих дней / исключения. Manager назначает work items и подтверждает G3 для разрешённого объёма. Прямое поручение текущего прохода разрешает подготовку, не production.
3. Первым выполнить CH-02/03 внутри FW-01: index/selection и реальные retained tables. Это7–10ч, независимо от A006 и готовности SVG. Затем FW-03 real boundary и FW-02 real renderer; никаких fake/no-op renderer в приложении ради промежуточного статуса.
4. После применимой A006 policy закрыть оставшийся FW-01 и FW-04; провести FW-05, обновить FW-06 и передать точную версию. HTML/controller unexpected failures должны по-прежнему использовать действующий safe-read.

Один Developer: ориентир D1–D3 — FW01 и начало boundary; D3–D5 — SVG/boundary; D6–D8 — реальная SVG-интеграция, проверки и handoff. Это относительный delivery target, не фиксированная дата до STARTED. Отсутствие external answer не считается Developer effort и не гарантирует прежний календарный срок.

Все FW связаны с [одним исполняемым постановочным пакетом05](prompts/05-full-wheel-passive-column.md) с разделами FW01…06; исторические prompts01…04 сохраняются. Пакет не исполняется до конкретного разрешения реализации и применимого G3.

## 4. Зависимости, окружение и исключения

| Условие | Влияние |
|---|---|
| A008 / последующая узкая дельта колонки и подписи категории | Для финального G3 нужен exact accepted target; текущие source decisions достаточно конкретны для этой подготовки. Новый общий Analysis не требуется |
| A006 already_applied | Только затронутый accepted-cause путь FW01/04. Не выдумывать default reset/preserve или server-producer provenance. CH-02/03 и независимые SVG/geometry не ждут его; полная интеграция требует решения |
| Владелец DP-O-010, applicable Technical Reviewer | Принять конкретный copy/install protocol и responsibility boundary. Старые T007/R002 на8b8c4c8 не считаются review этого нового SHA автоматически |
| DP-O-011/012 technical criteria | Подтвердить column domain/row objective, order/leader/aux predicates и палитру после адресной Analyst/Tester сверки; old annular criteria не переносятся молча |
| Среда | Существующие Python/pytest, Node24, локальный браузер/Playwright runtime, доступные fonts. Сейчас проверен Chrome155/Windows, CSS widths и DPR1/2. Для production native checks нужен согласованный набор браузеров; иная ОС/engine — отдельная проверка применимости и возможное влияние |

Нет новых app dependencies/framework/service/API/engine/golden/calculation/logging semantics. Не входят M1-8.1/V2 whole screen redesign, LLM/чат, export/print/sharing, deployment/публичная приёмка и независимый Tester effort. Нормативный чистовой перенос и merge в main — отдельные назначения. В оценке есть регрессии и оговорённые responsive/browser checks; произвольная сертификация всех браузеров/устройств не подразумевается.

## 5. Существующее покрытие, пробелы и команды

Сопоставлены текущие `facts.test.mjs` (source facts/order/immutability, full golden natal), `session.test.mjs` (submitted intent/draft/summary/caret), `recovery.test.mjs` (manual/restart/late/concurrency), form/places/transport и `test_ui_delivery.py` (доставка module resources, installed wheel). Действующая package-data уже включает ui/*.mjs; новые модули требуют добавить delivery expectations, а не менять engine/API или заводить dependency.

Фактически в подготовке запущено:

```text
node --test tests/ui/facts.test.mjs tests/ui/form.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs
188 PASS,0 FAIL, exit0 — baseline существующего приложения
```

Это не тесты будущего колеса. Новый state/cause/S1 и renderer необходимо закрепить чувствительными regression-тестами. Expected RED — отсутствие нового поведения/конкретный дефект, не отсутствие импорта или сломанный fixture. Не подменять предмет моками; inject только network/clock/управляемый leaf fault. Native focus/координатное попадание44px проверяются реальным browser, DOM fake недостаточен. H5 — live node/visible/enabled/focus transitions, не detached clone с тем же key. При planet activation focus()/scroll не вызываются.

Будущие команды, NOT RUN в этой подготовке:

```text
node --test tests/ui/<целевые новые файлы>.test.mjs
node --test tests/ui/*.test.mjs
python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q
python -m pytest
```

На Windows shell перечислить файлы, если glob не поддерживается. Native browser сценарии: real session/main/form/controller + fake HTTP только на листовом шве, ordered events accepted→revoke/remove→HTMLB→dispose/draw→install/error; once policy/resize/selection no HTTP; positive normal B и alternate renderer вместе с fault/late negatives. Не вводить runtime logger/telemetry: REQ-WHEEL-11 допускает browser/integration evidence и существующую request/run correlation. Для верификации raw research доступны команды [README](evidence/column_full_composition_v1/README.md); после final_stop новые исследования этого сеанса не запускаются.

## 6. Риски, stop/escalation и передача

Bounded full-SVG predicates, including branches, подтверждены29/29; это достаточная техническая основа для адресного допуска. Универсальная осуществимость для всех DTO / произвольного числа ☌ не доказана. При новом valid counterexample сохранить source/actual/expected, остановить лишь затронутый work item, предложить исправление/пересмотр с оценкой и передать Manager. Нельзя превращать систематический FAIL в принятую feature через local-error path.

Performance SLA не установлен. Browser job0,14–2,56с включает goto/font CDP/screenshot; это не измерение времени layout и не обещание responsive latency. FW02/05 профилируют реальный путь и переиспользуют font metrics/исключают лишнее layout work без изменения predicates. Новые Worker/solver/deps не включать молча. Если контрольный counterexample, иной browser/font или A006 меняют диапазон/календарь, сообщить Manager **до** прогнозируемого превышения, с различающим примером и новой оценкой; не автоматически добавлять резерв.

Предлагаемый ответ назначенных technical/criteria reviewers на exact package —1 рабочий день; они подтверждают свои сроки. Первичный Developer triage возврата —1 рабочий день. Эскалация Manager→Owner через+1 рабочий день просрочки, заместитель не назначен; ожидание не равно approval. G4/G5/acceptance независимы от этого плана.

**Следующее конкретное решение Owner:** принять предложенный полный scope40–64ч и передачу≤8 рабочих дней от отдельного STARTED, с указанными зависимостями/исключениями. Для технического допуска Manager закрепляет target contract и applicable DP/ADR approvals. Продуктовый выбор колонки/table-only повторять не нужно. Commit/push/PR/merge не выполнялись и требуют отдельного поручения; до публикации Criteria/TechnicalPackage/CandidateSHA нового результата отсутствуют.
