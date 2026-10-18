# Developer findings: ui-chart-wheel

**Автор:** Codex / Developer; исходное обнаружение TASK-D-001 / 2026-10-15, повторная сверка TASK-D-002 / 2026-10-16.
**Текущий предмет:** Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, Manager / code / tests на InputSHA `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`.
**Историческое evidence:** полная консультация v1 @ `04be207627de1049deac2e069574e01b62536607`, исходный вход `2b846077b317e33dd892565419942c4db8517b1e`. Это риски будущего M1-8, не дефекты реализованного M1-7 / отсутствующего renderer.
**Единый реестр / сводка:** [Manager](../manager_artifact.md); новый подписанный вклад — [DP patch](decision_input.patch). Чужие findings и role/task states не меняются.

| ID | Повторная сверка на InputSHA | Что осталось / адресат |
|---|---|---|
| DEV-FIND-WHEEL-001 | Документальная причина устранена в v3 и текущих Developer-материалах | Полный closure review не заявлен за Tester / Manager; новые рабочие Developer SHA после публикации ещё впереди |
| DEV-FIND-WHEEL-002 | Наблюдаемое interaction/failure поведение определено, технический риск сохраняется | Port / keys / focus / acceptance cause / integration evidence; Developer, Technical Reviewer и Tester |
| DEV-FIND-WHEEL-003 | Измерений / предельного fallback по-прежнему нет | Отдельно назначенный spike, DP-O-011/012/013, Developer / Tester / Owner |

## DEV-FIND-WHEEL-001. Analyst v1 расходился с поздними решениями Owner

**Type:** contract version conflict. **Владелец смысла:** Analyst; Manager координирует, Developer подтверждает свою повторную сверку. **Связано:** DP-O-010…014. **Полное закрытие:** не объявлено; документальная причина устранена.

### Исходное evidence TASK-D-001

На 2b84607 Manager уже содержал поздние Owner decisions, но Analyst v1 @ 683bdd0 оставлял ориентацию / стили / fallback неопределёнными и sequence 002 предлагала отдельное «Снять выделение», отклонённое Owner. Исполнение этой версии создало бы лишнюю кнопку и устаревший глобальный hidden gate таблиц. Исходные точные пути: analyst/requirements.md, scenarios.md и sequence_diagrams/ui/002-wheel-table-selection.puml @ 683bdd0; полное описание / контрпример сохранены в Developer v1 @ 04be207. API / engine при этом не требовали изменения.

### Повторная сверка TASK-D-002

V3 включает REQ-WHEEL-02/03/05…10, UI DELTA, AS-WHEEL-01…30 и MODIFY AS-UI-22; три behavioral sequences отражают принятые DP. Ориентация, default без разноса / смещение конфликтов, local HTML fallback, линии exact/working, подпись и контур ☌, single point/aspect selection, разные toggle outcomes, automatic current, collapse и positions/angles описаны. Отдельной кнопки снятия нет. Новых противоречий ChartDTO не найдено.

Текущий Developer-план / промты синхронизированы с этими правилами: старые вопросы о toggle, same-current, выбранном виде ☌ и collapse не возвращаются Owner. Указанный первоначальный разрыв input устранён по содержанию; v1 @ 04be207 сохраняется как история.

**Closure condition сохранён:** единая прослеживаемая версия без противоречащей кнопки, Manager registration / назначения и повторная сверка затронутыми ролями. **Текущее evidence:** Analyst v3 @ 2634b22, Manager @ 543b7ec и эта Developer-сверка; независимый результат TASK-T-002 / review текущего Developer-пакета ещё отсутствуют. Их закрытие не выполняет Developer. Отсутствие geometric evidence не называется новым конфликтом требований, оно остаётся в технических findings.

## DEV-FIND-WHEEL-002. Табличный renderer требует явной result boundary

**Type:** technical integration risk. **Владелец:** Developer; Technical Reviewer — существенная граница, Analyst — изменение смысла при новом контрпримере. **Связано:** DP-O-010/013, прежние Analyst FIND-WHEEL-002/003. **Состояние:** риск сохраняется, implementation / integration closure evidence отсутствует.

### Исходное evidence TASK-D-001

[facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs) readChartFacts не сохраняет longitude / cusp_longitude, renderFacts делает replaceChildren; [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs) publish переводит общий render exception в requiresReconciliation; [main.mjs](../../../../../src/exact_orb/http_api/ui/main.mjs) вставляет status / submitted / readAgain в birth-form. Контрпример будущего наивного соединения: принята B, SVG бросает исключение, остаётся HTML / SVG A либо ожидаемый SVG failure блокирует session как отказ всего ответа. Это не воспроизведённый bug текущего M1-7.

### Повторная сверка TASK-D-002

REQ-WHEEL-01/07/08/10, REQ-UI-09/11 и AS-WHEEL-24/28…30 определяют наблюдаемый результат. Прежние semantic questions сняты: aspect toggle, переход вне фильтра, automatic current другой карты и late dirty draft больше не требуют нового Owner choice. Новый аспект на same/different identity должен читаться из нового DTO, включая сменившуюся category=background; row index и ссылка на прежний DTO недостаточны.

**Рекомендация:** controller владеет selection и независимыми expansion states; wheel читает immutable ChartDTO и canonical intent. Кандидат aspect key `(from,to,type)` проверяется против публичного порядка / уникальности, без category/orb/identity. Причину принятия own build / automatic current различать по подтверждённому событию, не по HTTP GET и не по каждому render. Collapse — сравнение текущего draft со snapshot; feedback / safe read вне сворачиваемых полей. Ожидаемый SVG failure видим локально при HTML B и удалённом SVG A, не подавляется и не вызывает общий reconciliation. Подписанный proposal передан в DP input; он не принят как API / ADR.

**Что остаётся:** точный port / typed outcomes, key / acceptance-event seam, focus при пересоздании / исчезновении строк, keyboard order / hit targets и доступное recovery layout. Ordinary helpers выбирает Developer внутри будущего approved contract; существенную границу Manager передаёт Technical Reviewer. Готовить ещё один продуктовый вопрос без различающего примера не требуется.

**Closure condition:** reviewed port / drawing ADR, согласованный interaction contract и integration checks на реальных controller / renderer: успешный / альтернативный / отказавший renderer, HTML B без SVG A, текущие факты сохранённой пары / исчезновение ASC-пары, preserved focus и safe-read controls при collapse. Tester подтверждает своё evidence отдельно. Консультация / планирование не блокируются ожиданием реализации.

## DEV-FIND-WHEEL-003. Читаемость 16 точек на 360 px не доказана

**Type:** feasibility / estimate uncertainty внутри существующих DP-O-011/012/013. **Владелец исследования:** Developer; Tester — проверяемость, Owner — наблюдаемый предел / fallback. **Состояние:** открытый технический риск; новых Owner решений о плотности нет.

### Исходное evidence TASK-D-001

[AS-WHEEL-09/10](../analyst/scenarios.md) задают F3 с пятью retrograde points через 0° и F3-max с 16 IDs; [DOM port](../../../../../tests/ui/fixtures/dom.mjs) не измеряет реальный bbox / шрифт / SVG focus / viewport. Числа 359,70 / 359,85 / 0 / 0,15 / 0,30 могут пройти numeric / fake DOM checks при фактическом наложении glyph+R / ☌ и недоступных pointer targets. Полное исходное evidence — @ 04be207.

### Повторная сверка TASK-D-002

V3 уточнил default без разноса, минимальное смещение только конфликтов, выноски только при сдвиге, циклический порядок, подпись категории ☌ и усиленный контур только символа. Численные collision / minimality / hit bounds, предел / fallback, palette / контраст и измеренное размещение нескольких ☌ остаются открытыми. Оформление ☌ больше не называется непринятым; его физическая читаемость по-прежнему не проверена.

**Следующее действие:** отдельно назначить spike до 0,75 чд по [плану](implementation_plan.md#предлагаемое-отдельное-задание-spike). Данные — sparse/F1/F3/F3-max; viewports 1440/768/360, настоящий шрифт / glyph / R / подписи / контур / близкие углы и keyboard. До объявления успеха согласовать критерий с Analyst / Tester. По timebox остановиться, передать counterexample / варианты Owner и пересмотреть estimate; не скрывать точки и не подгонять golden.

**Closure condition:** воспроизводимые реальные размеры / screenshots и критерий→actual, согласованный предел / fallback, technical recommendation DP-O-011/012/013, обновлённый estimate и назначенные независимые checks. Сейчас нет ни измерений, ни ADR, ни runtime / browser PASS. Поэтому 8–12 чд сохраняются предварительными, upper bound условен; отдельный spike в этой документальной задаче не выполнялся.


## TASK-D-003 — факты к существующим DEV-FIND-WHEEL-002 / 003, 18.10.2026

**Автор:** Codex / Developer, InputSHA 8fb2577. [Report](task_d003_research_report.md) / [DRAFT ADR](drawing_adr_draft.md) / [source and measured evidence](evidence/task_d003_research/matrix_v2.md). Это уточнение существующих technical integration / feasibility risks, не новые baseline production defects и не самостоятельное закрытие finding/DP.

- **DEV-FIND-WHEEL-002 / T003-G01:** proposed isolated leaf boundary сохраняет HTML points/aspects B при fault и игнорирует late A callback; alternate live renderer toggles canonical sun. Production controller/port отсутствуют; async revision / dispose throw / full HTML mounted evidence осталось условием реализации. Technical Reviewer проверяет предложение.
- **DEV-FIND-WHEEL-002 / T003-G02:** normal default producer unique, но modified-copy restore допускает duplicate (47/46 natal,14/13 cosmogram); direction следует config, не lexical comparator. Empty configurations позволяет reversed refs в обеих моделях; старые configurations отклоняли именно рассогласованные materialized refs. Предлагается unordered lookup+type с исходными direction/order для вывода. Ambiguity outcome / наблюдаемая policy требует review, новое API правило не введено.
- **DEV-FIND-WHEEL-002 / T003-G03:** actual source=build повторён3 раза на1 POST. Требуется internal once token у accept-owner. Новый точный semantic gap: fresh matched recovery B после lost POST не различает own late winner и другая вкладка с той же B; конкретный двухисторный пример / варианты в report, Analyst / Manager→Owner. Независимые ветви исследования выполнены без ожидания; критерии в целом не возвращаются на новый цикл.
- **DEV-FIND-WHEEL-003 / T003-G04/05:** sparse360 визуально свободен, centered Q44 только8/16; F3max360 candidate3/20. Кандидат16°/40° не проходит плотность / order / минимальность; fixed close angle labels перекрываются и не исправляются движением point groups. Это непригодность объявленной construction, не недостижимость всех layouts. Другая movement/target model / angle label placement — ещё не измеренные варианты внутри существующего обязательства; fallback / скрытие / shrink не приняты.

Контрпримеры, связанные expected→actual, старые неуспешные research попытки и limits сохранены в report/JSON. Runtime mounted M1-8 / independent acceptance / G3 отсутствуют. Прежние closure conditions сохраняются; TEST-FIND-WHEEL-002 остаётся у Tester, DP registry — у Manager. Оценочное следствие передано как новый условный общий прогноз9–14 чд вместо8–12, без автоматического изменения бюджета или прибавления D003 вторично.
