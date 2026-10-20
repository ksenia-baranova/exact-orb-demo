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


## 7. TASK-D-007 — фактическое начало / первый участок CH-02/03

**Автор / подпись: Codex, Developer, 19.10.2026.** Прямое поручение Owner в текущем чате: «Отходим от процесса / Давай стартовать разработку». Предыдущие условия ожидания G3 / A008 / T007 / R002 в §§3–6 описывают состояние до этого более позднего исключения. [Manager §2.25](../manager_artifact.md#225-прямой-старт-разработки-по-решению-owner) регистрирует прямое разрешение, не выдаёт отсутствующие approvals за полученные.

**STARTED:19.10.2026 22:11:37MSK /19:11:37UTC.** InputSHA502589dbadd382fbe39e3cf1fd763abb52ffc620, текущий detached checkout79e1; семь локальных Manager-owned путей прошлого прохода сохранены. Ветка / commit / push не создавались. Первый самостоятельный участок CH-02/03 внутри FW-01 реализован в локальном дереве; весь D007 остаётся **IN_PROGRESS / DRAFT**. Ориентир первого участка7–10ч уже внутри40–64ч; его не подменяем elapsed длительностью сеанса и не выдумываем отдельное численное budget approval.

**Основание / источники:** фактические facts.mjs / main.mjs / session.mjs, tests/ui/facts / session / recovery / fixture DOM, test_ui_delivery; Analyst v3+S1@2736e28 REQ-WHEEL-04/07/08/09/10, AS-WHEEL-11/12/13/16/23/28/29/30 и baseline current UI / ADR-0029 / component boundaries. Источники domain data не пересчитываются. Техническая behavioral sequence002 сохраняет источник; её SVG-activation / category-text заменены принятыми более поздними Owner-дельтами, сами Analyst-файлы не редактировались.

**Реализовано:**

- Реально используемый внутренний chart_state.mjs: индекс unordered endpoints + опубликованный type по полному DTO до five/all / planet-filter; 0/1/>1 matches. S1 не объединяет строки; одинаковый / reversed / category / orb duplicate блокирует лишь неоднозначный адрес. Остальные point / aspect controls действуют.
- Взаимоисключающие point / aspect toggles. Планета показывает все связанные source rows, включая background / angles / ambiguous, в DTO order; другая заменяет прежнюю. Повтор планеты возвращает общий список первых5; повтор аспекта сохраняет прежнее general five/all и не восстанавливает planet-filter. Background сохраняет свои опубликованные факты.
- Retained HTML: все points / первые5 aspects / первые5 houses видны сразу, отдельные native show-all, компактная таблица angles. Общая details-кнопка удалена по изменённому контракту AS-UI-22. Кнопки / строки сохраняются по ключу, источник / source occurrence не превращаются в API identity. Текст обновляется через textContent, не HTML. CSS targets ≥44px / visible focus; planet activation без программного focus / scroll.
- Automatic accepted update сохраняет только адресуемый выбор, использует новые category/orb/направление; absent/ambiguous снимает только affected selection и сохраняет раскрытие. Подтверждённый empty/unavailable удаляет числовые строки. Dispose / удаление строки отключают старые callbacks; main использует реальный result.dispose.
- Новый модуль включён в проверку HTTP / installed-wheel delivery. Engine/API/projector/golden, зависимости и HTTP/cause/recovery semantics не изменены. SVG leaf / placeholder не добавлялись.

**Выбранный подход / чувствительность:** три первые mounted-проверки нового поведения сначала дали RED на существующем корректно загруженном приложении: глобально скрытые facts / отсутствующие disclosure и selection controls, затем GREEN после реализации. Formatting/source/golden/HTTP assertions переиспользованы. Старые tests глобального details gate намеренно изменены только для принятой Owner-дельты. Новые state/mounted controls проверяют U/R/D/V/M/L/T/P через уникальность / reverse / duplicates / variants / mode / loss / type / point. В существующих safe-read tests DOM fault перенесён с создания таблицы на реальный retained-control patch: таблицы больше не пересоздаются при каждой identity. Assertions safe-read / submit prohibition не ослаблены; добавлены числовые rows и равенство UI identity принятому ответу.

**Технический regression:** неуспешный частичный DOM patch должен инвалидировать прежний render-cache. Иначе возврат safe-read к прежней A мог пропустить восстановление после partial B из-за совпадения старого cache key. Cache инвалидируется до patch и отмечается успешным только после завершения; positive recovery и три controlled fault сценария проверены.

| Команда / проверка | Фактический результат |
|---|---|
| node --test tests/ui/chart_selection.test.mjs | 12 PASS /0 FAIL; реальные public source fixtures, state и mounted main/session |
| node --test --test-reporter=spec tests/ui/*.test.mjs | **200 PASS /0 FAIL** |
| python -m pytest tests/test_module_boundaries.py -q | **46 passed**, sandbox |
| python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q | **53 passed**,14,75с, повтор вне sandbox; включает installed wheel |
| python -m pytest -q | **2959 passed,1 skipped**,143,91с; skip только существующий DEBT-CALC-001 |
| node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_html/browser.cjs | **D007_HTML_BROWSER_OK**: Chrome155.0.8059.40 / Windows, widths1440/768/360; Enter/Space,24 видимые native targets ≥44×44 по каждой ширине, same-node/live-focus / source reorder / automatic category update / S1 / resize / отсутствие horizontal overflow |
| Browser activation / network positive controls | Только boot/current на bootstrap и двух явно вызванных online updates. Выбор / раскрытие / resize не добавляют HTTP; реальный main/session/form/facts, листовая контролируемая сеть |

**Среда / пределы:** sandbox блокировал loopback браузера и Windows asyncio socketpair (faulthandler: _fallback_socketpair→accept при создании event loop). Разрешённые повторы вне sandbox прошли; три собственных зависших sandbox pytest-процесса остановлены по проверенным PID, процесс успешного прогона не затронут. Это не product failure / не основание менять код event loop. Native checks — Windows Chrome на трёх ширинах, не независимый Tester / другие ОС/engine / HTTPS.

**Что ещё не реализовано / следующий код:** CH-01/04 — accepted-event once / собственный changed-birth reset / сводка / collapse editor и полная recovery integration; already_applied policy не выбрана по предположению. Текущий facts.update выполняет обычный сохраняющий reconcile принятого ChartDTO; отдельная причина собственного build будет подключена в CH-01/04, поэтому целиком REQ-WHEEL-08 / full FW-01 не объявляются готовыми. Следующий независимый участок — реальный passive renderer / boundary FW-03 и SVG FW-02 по опубликованному column design, затем cause wiring / FW-04. Ни G4, ни готовность всего колеса / CandidateSHA / independent acceptance не заявлены.

**Публикация:** NOT RUN, index не изменялся, OutputSHA / CandidateSHA отсутствуют. Исходные D003/D005/v3/column research raw и их manifests не пересчитаны. [Native evidence / команды](evidence/task_d007_html/README.md); handoff дополняется по факту следующего участка. Оценки остаются ориентирами; до прогнозируемого превышения сообщать Owner влияние.

## 8. TASK-D-007 — полный локальный результат FW-01…06

**Codex / Developer,20.10.2026. DRAFT, реализация и Developer checks завершены локально.** InputSHA / HEAD / AssignmentSHA e0daa0e814d3d1fd34cadb8c17d064f19c4810f5; dev/ui-chart-wheel. Исходный STARTED19.10.2026 22:11:37MSK / resume19.10 20:51:23UTC сохранён. Прямое исключение Owner «пропускаем все апрувелы просто выполняем помты» и Manager §§2.25–2.26 снимает прежнее ожидание G3/A008/T007/R002 для этого исполнения; формальные approvals не выдумываются. Новый источник A006 — [конкретное решение Owner20.10](owner_decision_already_applied_2026-10-20.md). Manager status/gates чужой роли не менялись.

### Фактические work items

| FW / основание | Выполнено / ответственный слой | Evidence / подход |
|---|---|---|
| FW-01, REQ-WHEEL-07/08/09/10; AS11…16/18…23/28…30 | Переданный chart_state/retained HTML переиспользован. session — acceptanceSeq/immutable attempt/once cause; facts — once reset/reconcile; main — summary/editor iff draft match, recovery outside fields. S1 по полному accepted DTO, source rows неизменны |200 прежних UI tests +новые accepted_chart tests. A006: sensitive RED6 FAIL→GREEN12/12 на прямом контракте Owner |
| FW-02, REQ02…06/09/10; AS01…10/16/22/25/26/28/30 | Реальные wheel_layout/wheel_svg:12 signs,16 source IDs/R, published cusps/angles,7 colors/type/category, source-only chords и☌, selected/background/S1. Measured conditional C0 column, frozen unaffected labels, cyclic tie order, PAV rows/growing H, local auxiliary contact, owner routes |Pure predicates и shared20,5px regression; native35 compositions, independent35/35 +7 controls; production geometry не импортирует research |
| FW-03, REQ01/10/11; AS01/02/22/24 | Приватный live host, revision-local connected surface, deep copied/frozen snapshot, validate/clone/recheck/install, revoke/replace/dispose, stale/current/fatal partition |37 native controls, включая independent real leaf positive. Delayed owner failure retired A: RED→GREEN, B сохраняется |
| FW-04, REQ01/08…11; AS01/02/04/17…22/24/26 | Реальные facts/main/session/form соединены с SVG; ResizeObserver/font revisions/geometry cache; full fractional DTO render cache; local SVG warning сохраняет актуальные HTML. Empty/unavailable и удалённый/disabled/hidden focus восстанавливаются в живой HTML control |Mounted integration на трёх ширинах, реальные источники страницы/HTTP correlation, fake только HTTP и leaf fault shim |
| FW-05 | Full UI / target Python /full pytest, installed-wheel resources, widths1440/768/360, DPR2/font fallback, pointer/keyboard/live focus/background/S1/reset/recovery/fault |216 Node PASS;53 target passed;2959 passed+1 existing skip; native35/35, boundary37/37, integrated111/111 |
| FW-06 | DRAFT ADR фактического протокола, technical sequences003/004/005, Owner A006 source, команды/данные/ограничения и подписанный handoff |[Runtime evidence/README](evidence/task_d007_runtime/README.md), package/source/link/structure audit и git diff --check; нормативный перенос/acceptance отдельно |

Выбранный в §1 подход сохранён: существующее покрытие переиспользовано; для state/acceptance/geometry/lifecycle — чувствительные regression controls, для сборки — реальное приложение и листовая контролируемая сеть. Native getBBox / CTM / font data не заменены fake DOM. Исправленные implementation defects и различающие controls перечислены в evidence, в том числе invalid leaf interface не отравляет будущий dispose, async stale owner failure не очищает B, принятие полного fractional DTO не теряет изменения longitude.

Новые реально используемые модули: result_controller.mjs, wheel_layout.mjs, wheel_svg.mjs. Дополнены facts/main/session/styles и resource expectations; chart_state.mjs из переданного участка не переписан. HTTP/schema/engine/API/projector/golden/LLM/deps/logging policies не менялись.

### Версия / проверки / остатки

Точные команды, source LF hashes, реальные bbox/координаты/screenshots/font/scale, raw промежуточных FAIL и окончательные actual — [runtime evidence](evidence/task_d007_runtime/README.md). Все окончательные native checks сверяются с локальными UI-файлами через verify_package.py; Git HEAD сам по себе не является версией незакоммиченного source. CandidateSHA / OutputSHA до отдельной публикации отсутствует.

DRAFT protocol: renderer.update(snapshot,publish,currentSurface), dispose(); Session единственный accept owner, facts/chart_state — selection owner, drawing controller — только revision/live-host owner. [ADR](drawing_adr_column_draft.md), [sequence003](sequence_diagrams/ui/003-passive-copy-install.puml), [004](sequence_diagrams/ui/004-column-layout-revision.puml), [005](sequence_diagrams/ui/005-accepted-once-editor.puml). Registry в текущем baseline заканчивается0041;0042 остаётся кандидатом, нормативный ADR не создан.

Ориентир40–64ч /5–8чд и передача до конца восьмого рабочего дня от исходного STARTED сохраняются как оценка Developer, без приписанного численного budget approval. Этот результат закрывает разрешённый локальный код/checks FW01…06; внешнее ожидание review/публикации не считается coding effort. Подготовка/D003/D005/D006/первый CH02/03 повторно не начисляются. Неизвестный исторический effort/остаток D003 не вычислялся; достоверного timesheet для total lifetime budget нет. Нового расхода сверх оценки не добавлено.

Пределы: Windows Chrome155, реальные CSS frames720/424/318. Другие engines/ОС/real mobile/screen reader/zoom/HTTPS/performance SLA и универсальная geometry feasibility не подтверждены. Локальный renderer failure сохраняет данные, но не заменяет исправление систематического valid counterexample. Измеренный async render total2,5–806,7ms и copy1,5–2,3ms — diagnostic samples, не гарантия времени.

**Передача:** локальная DRAFT-поставка готова, новый commit/push/merge/PR требуют отдельного поручения. После разрешённой публикации передать точный CandidateSHA Manager и назначенным reviewers. Независимый Tester / technical review / Owner acceptance остаются отдельными действиями; прошлые research approvals не выдаются за проверку этой реализации. Первичный triage≤1 рабочего дня, Manager→Owner escalation+1 день просрочки. Исторические секции этого плана и Developer index сохранены append-only, старые D003/D005/raw/manifests и чужие артефакты не изменялись.

## 9. TASK-D-007 — исправления композиции по Owner20.10

**Codex / Developer,20.10.2026. DRAFT, локальная корректирующая поставка.** SourceRef: текущий Owner feedback с двумя приложенными screenshot и ответ «Да: две планеты и только их дома». InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, branch dev/ui-chart-wheel; исходный STARTED D007 сохранён. [Пакет06](prompts/06-owner-composition-aspect-view.md), [evidence](evidence/task_d007_composition_v2/README.md). Это прямое изменение наблюдаемого поведения Owner, применённое вместо прежних условий only-aspect focus/always-all-houses; чужие нормативные тексты и статусы не переписывались.

Оперативная оценка этой корректирующей дельты4–8ч, medium confidence: numbering/composition1,5–3ч, aspect mode/focus1,5–3ч, checks/evidence1–2ч. Это оценка итерации, не автоматически прибавленные часы к40–64; численный Owner budget approval не выдумывается и неизвестный исторический timesheet не выводится. Выполнение разрешено прямым поручением; сверхплановое изменение total Manager сопоставляет с фактом.

| Work item / подход | Основание / ответственное изменение | Фактическое evidence |
|---|---|---|
| Нумерация домов и геометрия | REQ-WHEEL-02/05/09: отдельный пояс1…12 по source cusp sectors, source midpoint как reference, degree ruler360 ticks; увеличенный aspectR=max(0,27R,pointR−55), прежние16/12/gap2/true marks и local solver bounds | Pure sector wrap-around regression,35 real compositions, independent Fraction audit35/35+7 controls; native source/metrics без вызова layout verifier |
| Отдельный aspect mode | Прямая дельта REQ-WHEEL-07/08 / REQ-UI-05/06: full-DТО S1 до subset; одна строка аспекта, source endpoints и distinct published house numbers, только relevant graphic; scalar house membership не вычисляется |3 новых mounted tests RED3→GREEN3; current/full selection tests адаптированы только к новой семантике. Native full/mode/close/S1/cosmogram/angle checks |
| Focus / viewport / recovery | REQ-UI-10: HTML wheel region tabindex−1, явный gesture focus, guarded scroll after current frame, sticky return, Escape, восстановление live original control; planet action без focus/scroll, recovery вне скрытой формы | Height1000 и640; полный SVG виден, toolbar не перекрывает, fresh GET restore, S1 exit и отсутствие дополнительных HTTP по действиям |
| Проверки / docs | Реальное приложение, fake только HTTP;200 прежних+16 прошлого прироста+4 текущих UI tests переиспользованы; normative/API/golden не менялись |220 Node PASS;53 target Python passed;full2959+1 skip;35 native +37 boundary;16 aspect-mode cases/392 assertions; собственные ADR/sequence006/handoff |

Последовательность mapping: facts/chart_state владеют selection; main скрывает нерелевантные области и сохраняет recovery; drawing controller всё так же один владелец live host. Focus получает HTML region, SVG остаётся пассивным. Point-only selection переиспользует layout; aspect mode получает отдельный layout key и display subset, сохраняя source DTO/index полными. При выходе сохраняются исходные раскрытия, при повторной planet activation — прежний reset к пяти.

**Root causes:** в SVG вообще не было номеров домов; aspect circle был фиксирован0,27R и оставлял большую пустую площадь. Композиция summary+wheel не использовала широкое окно, а на Owner screenshot browser zoom50% дополнительно уменьшал всё. Первый scroll aspect action выполнялся до появления нового SVG и мог оставить колесо ниже viewport; теперь повторяется после текущего frame только при сохранённом намерении пользователя. Focus recheck фиксируется до скрытия control, чтобы после recovery попадать в живое wheel region в aspect mode.

Точная версия и команды — [README/actual/source LF](evidence/task_d007_composition_v2/README.md). Сохранены все прежние runtime/dark-theme raw/manifests и role index prefix. Нет отдельного нового Manager TaskId/gate/acceptance, нового commit/OutputSHA/CandidateSHA. Следующий шаг — Owner просмотр текущего приложения и отдельно порученная публикация/независимая проверка. 100% browser zoom восстанавливается Ctrl+0; настройка чужого Yandex-профиля из app не менялась.


## 10. TASK-D-007 — внутренние ряды по Owner20.10

**Codex / Developer,20.10.2026. STARTED и локальное исполнение в текущей сессии; исходный STARTED D007 сохранён.** Прямое [решение Owner](owner_decision_house_rows_2026-10-20.md) и [пакет07](prompts/07-owner-house-rows.md) заменяют прежний колонный point-домен в FW02/§9. InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, dev/ui-chart-wheel; index сохранён пустым. Никакого fetch/reset/clean/переноса чужих локальных артефактов в эту итерацию не требовалось. Scope только presentation geometry, closed SVG data attrs и пояснение под изображением, собственные tests/docs/evidence. Другие локальные правки сохранены.

Root cause: любой конфликт point переводился в колонку с резервированием ширины; внутри дома кандидаты даже не искались. Новый домен прямо разрешает визуальное угловое смещение. Подход реализация→regression tests и native controls: существующие state/HTML/recovery/lifecycle tests переиспользованы, добавлены5 pure tests (720/448/328, wrap0°, R, source-only membership, cosmogram, multiple rows, permutation stability). Полный bbox и R входят в house sector, planet leaders/column удалены. Радиальная R заменила слишком широкую боковую пару в узком доме; native01 counterexample сохранён. Точные числа/HTTP/API/engine/golden/deps не изменены.

Проверки:225 Node tests,53 target Python,full2959 passed+1 прежний skip;35/35 native compositions, независимый house/bbox/source audit35/35+5 калибровок;12 aspect-view cases/290 assertions. [Команды/actual/source hashes](evidence/task_d007_house_rows/README.md). Нет нового published CandidateSHA/OutputSHA, формального gate/Manager status/acceptance. Изменены4 UI modules: wheel_layout/wheel_svg/result_controller/facts,1 test file; собственный DRAFT ADR/sequence007/Owner source/пакет07/handoff и новое evidence.

Старые оценки40–64ч и отдельные исторические итерации не суммируются автоматически. Эта геометрическая переработка — новая Owner delta; фактического timesheet для пересчёта total нет, утверждение нового budget не выводится. Неизвестный остаток D003 не вычисляется. Универсальная вместимость произвольного узкого дома/любого количества точек не доказана, при нехватке — честный локальный отказ с сохранением HTML. Независимый Tester/technical review и публикация отдельно. В браузере открыт явно помеченный preview на опубликованном DTO без записи в пользовательскую сессию/POST; основное приложение получает те же текущие source assets.


## 11. TASK-D-007 — исправление Owner bug reports004…008

Codex / Developer,20.10.2026. STARTED текущей корректирующей итерации по прямому уточнению Owner **«Исправить все баги и доработки»**. InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5,dev/ui-chart-wheel+local UI;исходный STARTED D007 не меняется. [Пакет08](prompts/08-owner-bugfixes.md),[evidence](evidence/task_d007_bugfixes/README.md). Scope:5reports004…008+две доработки007;historical001…003 не объявляются новыми багами/закрытыми рисками. Локальная реализация выполнена,публикация/независимый retest отдельно.

| Work item / подход | Реализация / root cause | Evidence |
|---|---|---|
|004 / regression→code | Initial page centered,width680px. Browser50% is external;no profile/zoom reset. Accepted chart gets full page width before immutable drawing snapshot,not after editor collapse | Chrome/Yandex startup100% default clean contexts;initial transient capacity regression identified by resize01 and onDrawingEvent observer,then no errors |
|005 / regression→code | Normal wheel was width-only. Native CSS frame fit by viewport height;aspect reserves200px for toolbar wrap. Mobile summary below wheel | Width1882/1440/768/360,height1068/1000/900/800/640;compact01RED→compact02/03GREEN;height-only resize preserves choice and no HTTP |
|006 / regression→code | Paragraph had no color samples. Shared ASPECT_COLORS→7accessible color/type entries,solid/dashed,☌,desktop side legend | Pure RED missing legend→GREEN;actual computed sample colors checked in Chrome/Yandex;no palette mutation |
|007 +2deltas / regression→code | Top-aligned plain td vs padded44px button caused offset. Content-based table width,middle alignment,4px12px cells,44px controls;concise node label | Text Range centers align,short row53px/table489.734375px in desktop fixture;derived facts/IDs/source rows preserved;native mobile controls |
|008 / code+native visual regression | Existing Unicode mapping did not ensure recognizable font rendering;Selena○ differs from R3. Three explicit vector stencils,immutable definitions/native bbox,closed metadata | Real visible path/circle bounds,all16points,R3 screenshot comparison,35 compositions/DPR2/font fallback;no engine/API/golden/deps change |

Подход текущих bugs — чувствительные RED-first regression (pure2tests,browser2cases),reuse остальных state/boundary tests,затем реализация/native matrices. Ранние ошибки harness/data-attrs и expected old label исправлены явно,не выданы за product RED. Наблюдаемая пользовательская семантика только по Owner;browser zoom не подменён viewport/DPR.

Реальные production files:main.mjs,facts.mjs,styles.css,wheel_layout.mjs,wheel_svg.mjs,result_controller.mjs;tests/ui/owner_feedback.test.mjs новый и facts.test.mjs (только подпись). Свои DRAFT ADR/sequence008/plan/findings/handoff/пакет08/evidence. Scope Session/HTTP/engine/projector/cache/golden/LLM/new dependencies не менялся. Старые evidence и незакоммиченные изменения сохранены,index остаётся пуст.

Оперативная оценка корректирующей дельты4–8ч,medium confidence;это Developer forecast,не новое численное Owner budget approval и не автоматическая сумма к40–64. Неизвестный historical effort/D003 остаток не вычислялся. Новой даты передачи/TaskId/Manager gate самостоятельно не назначено. Точные финальные commands/results/source hashes/ограничения — evidence README. Нового commit/OutputSHA/CandidateSHA нет;официальный FIXED_PENDING_RETEST требует опубликованной исправленной версии,поэтому текущий Developer результат — **локальное исправление,ожидание публикации и независимого retest**.
