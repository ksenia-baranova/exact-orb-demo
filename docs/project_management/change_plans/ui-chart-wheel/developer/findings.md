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


## DEV-FIND-WHEEL-004. Yandex: стартовая страница выглядит уменьшенной и не использует окно

**Тип:** пользовательский bug report / UI layout & browser scaling. **Статус:** OPEN — зарегистрирован со слов Owner и по screenshot, независимое воспроизведение и корневая причина ещё не подтверждены. **Обнаружение / регистрация:**20.10.2026; сообщил Owner, оформил Codex / Developer в рамках TASK-D-007. **Ответственный слой для triage:** frontend layout/browser integration; Developer — диагностика, Tester — независимое воспроизведение и retest. Приоритет/влияние на допуски Manager не назначены; текущие task/change/gate states не меняются. Это Developer-вход для Tester, не присвоение TEST-FIND или закрытие чужого дефекта.

### Окружение и версия

- URL: `https://exact-orb.localhost/`; браузер **Яндекс Браузер**, точная версия неизвестна. Windows по предоставленному screenshot; build/DPI/масштаб ОС/расширения/настройки профиля неизвестны.
- Размер файла screenshot1920×1200 физических пикселей; это не измерение CSS viewport. В панели браузера явно показан **масштаб50%**. Исходное открытие при100%, выбранный default zoom и автоматическое/ручное происхождение50% не установлены.
- Экран до ввода данных, пустая форма и сообщение «Сохранённой карты пока нет»; к SVG-геометрии колеса наблюдение не относится.
- Локальная ветка dev/ui-chart-wheel, HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5 + незакоммиченные UI-изменения. Snapshot источников регистрации — [manifest](evidence/dev_find_wheel_004_yandex/manifest.json); соответствие конкретного screenshot точному CandidateSHA пока не подтверждено.

### Шаги пользователя

1. Открыть Яндекс Браузер, окно на весь экран.
2. Перейти на `https://exact-orb.localhost/` в сессии без сохранённой карты.
3. Не вводя данные, оценить стартовую страницу. На предоставленном снимке браузер показывает50%.

**Actual:** заголовок, текст и форма воспринимаются сильно уменьшенными; форма занимает небольшой блок в левой части центральной области, большая часть окна пустует. Owner сообщает: «стартовая страница не масштабирована — это баг», отдельно указал Yandex.

**Expected по обращению Owner:** стартовая страница должна иметь читаемый размер формы и текста и корректную адаптивную композицию в Яндекс Браузере. Проверка на нормальном100% должна отличать дефект CSS/layout от уменьшения, вызванного настройкой браузера. На50% элементы естественно становятся меньше; это значение само по себе не доказывает ошибку приложения. Приложение не должно самопроизвольно менять выбранный browser zoom. Численное требование растягивать форму на всю ширину/компенсировать50% удвоением CSS не вводится.

Связано с REQ-UI-10 ([доступность и визуальная сверка](../../../../requirements/current/ui/birth-form-and-facts.md#req-ui-10-доступность-и-визуальная-сверка)) и текущей стартовой композицией UI. Источник expected — текущий Owner report; точная требуемая композиция, если не следует из принятого прототипа, уточняется до реализации. Browser-specific root cause не подтверждена сравнением с другим браузером.

### Evidence и дальнейшая проверка

[Оригинальный screenshot Owner](evidence/dev_find_wheel_004_yandex/yandex-start-page-owner.png) скопирован без редактирования, SHA256 исходного и сохранённого файла совпадают; [manifest](evidence/dev_find_wheel_004_yandex/manifest.json). Сообщение и screenshot достаточны для регистрации OPEN, но самостоятельный Yandex runtime run в этой задаче не выполнялся.

Проверить на одной версии приложения и одном окне: Yandex100% (Ctrl+0), затем50%; зафиксировать innerWidth/clientWidth/devicePixelRatio/visualViewport.scale, computed font-size и bbox формы/контейнера. Сравнить с Chromium/Chrome при тех же условиях, отдельно проверить чистый профиль и настройки zoom для сайта/default zoom. Изменение DPR/OS scale и desktop browser zoom не подменять только viewport emulation или CSS transform. Не очищать пользовательскую сессию и не менять настройки профиля без соответствующей задачи.

**Корневая причина:** не установлена. Видимые факторы — browser zoom50% и существующий max-width формы; это гипотезы для проверки, не доказанное исправление. **Критерий закрытия:** Tester подтвердил ожидаемую стартовую композицию/читаемость на воспроизводимой версии в Yandex и разделение layout с пользовательским zoom; при подтверждённом дефекте есть scoped fix/regression evidence, при ином исходе — подтверждённое основание решения. Сейчас FIXED/CLOSED/REJECTED не объявляются.

**Scope регистрации:** только этот Developer finding, evidence и собственный handoff; production code, tester/defects.md, чужие артефакты и статусы не менялись. Commit/push не поручены.


## DEV-FIND-WHEEL-005. Chrome: круг карты не вписывается в высоту видимой области

**Тип:** пользовательский bug report / chart composition & viewport sizing. **Статус:** OPEN — зарегистрирован по сообщению и screenshot Owner, независимое воспроизведение ещё не выполнено. **Дата / автор:**20.10.2026, Codex / Developer; сообщил Owner: «заведи баг для браузера chrome — не масштабированный круг». **Контекст:** TASK-D-007. Ответственный слой для диагностики — frontend composition/renderer sizing; Tester подтверждает воспроизведение и retest. Приоритет, блокировка gates и task/change states этой регистрацией не назначаются. Это Developer-вход для Tester, не новый TEST-FIND и не подтверждённое закрытие.

### Окружение и версия

Google Chrome, `https://exact-orb.localhost/`. Точная версия браузера, ОС/build, масштаб браузера и ОС, DPR и CSS viewport неизвестны; видимого числового zoom-индикатора на screenshot нет,100% не предполагается автоматически. Размер исходного PNG указан в [manifest](evidence/dev_find_wheel_005_chrome/manifest.json); физические пиксели screenshot не подменяют CSS-размер viewport.

Видна готовая натальная карта: summary слева, SVG справа; обычный режим полного колеса, не отдельный просмотр выбранного аспекта. HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5,dev/ui-chart-wheel + local uncommitted UI. Snapshot source hashes на дату регистрации в manifest; screenshot ещё не связан независимой проверкой с точным CandidateSHA.

### Шаги воспроизведения по обращению

1. Открыть `https://exact-orb.localhost/` в Google Chrome.
2. Получить состояние chart_ready с натальной картой: построить карту из собственных данных либо восстановить сохранённую карту.
3. Открыть обычный полный вид карты в окне, соответствующем screenshot; не включать aspect reading mode.
4. Проверить, помещается ли полный круг в доступную видимую область окна.

**Actual:** круг занимает очень большую площадь справа; видна только верхняя часть и середина, нижняя часть уходит ниже нижней границы screenshot/видимой области. Полный круг на экране одновременно не показан. Скриншот не доказывает SVG clipping: нужно различить выход ниже viewport с обычной прокруткой,обрезку контейнером и возможный browser zoom/DPI.

**Expected по текущему Owner report:** в обычном desktop-виде круг должен адаптироваться к доступным ширине **и высоте** окна так,чтобы его можно было увидеть целиком без ручного уменьшения browser zoom или просмотра круга по частям. Сохраняются круглая форма1:1,читаемость glyph/домов/R и точные данные; конкретная реализация fit/перекомпоновки этим bug report не назначается. Связано с [REQ-WHEEL-09: композиция и адаптивность](../analyst/requirements.md#req-wheel-09). Это адресное требование Owner к viewport fit,не доказательство,что прежние width-only проверки уже проверяли этот критерий.

### Evidence, гипотеза и диагностика

[Исходный screenshot Owner](evidence/dev_find_wheel_005_chrome/chrome-wheel-viewport-owner.png) скопирован побайтно без редактирования; SHA256 исходного и сохранённого файла совпадают,размер и hash — [manifest](evidence/dev_find_wheel_005_chrome/manifest.json).

**Корневая причина:** не подтверждена runtime-воспроизведением. Наблюдение по текущему [styles.css](../../../../../src/exact_orb/http_api/ui/styles.css): обычная chart-composition ограничивает ширину wheel-panel940px,а явное ограничение через100svh−200px применяется только к data-aspect-focus=true. Это кандидат причины отсутствия fit по высоте в обычном режиме,не готовое исправление. Размер screenshot/крупный текст не позволяют самостоятельно определить zoom/DPI.

Следующая проверка: воспроизвести в реальном Chrome на точной версии/том же DTO;снять innerWidth/innerHeight/clientWidth/devicePixelRatio/visualViewport.scale,computed sizing и boundingClientRect wheel-panel/SVG. Проверить обычный и aspect режимы,разные desktop-высоты/resize и100% контроль после фиксации исходного zoom;отдельно проверить CSS clipping против обычного scroll. CSS viewport emulation не выдавать за desktop browser zoom. Старые1440/768/360 width checks и green bbox audit не доказывают,что круг целиком умещается в текущую высоту viewport обычного режима.

**Критерий закрытия:** независимый Tester на воспроизводимой версии Chrome подтверждает целый круг в согласованной доступной области и сохранение читабельности/формы1:1/source facts;при подтверждённом code defect — scoped fix и regression на desktop height/resize. Сейчас FIXED/CLOSED/REJECTED не объявляются. Реальный новый build/Chrome runtime retest в задаче регистрации не запускались.

**Связь с другими сообщениями:** отдельный от DEV-FIND-WHEEL-004 (Yandex,уменьшенная стартовая форма,видимый zoom50%): здесь другой браузер,chart_ready и слишком большое колесо относительно видимой высоты. Общая причина не доказана,duplicate не назначается.

Scope:только Developer finding,evidence и собственный handoff;production code/tester/Manager artifacts/gates не меняются. Commit/push не поручены.


## DEV-FIND-WHEEL-006. Нет цветовой легенды аспектов возле колеса

**Тип:** пользовательский bug report / UI discoverability & aspect legend. **Статус:** OPEN. **Обнаружение / регистрация:**20.10.2026, сообщил Owner, оформил Codex / Developer; источник: «нет легенды по линиям аспектов не понятно что значат цвета». Контекст TASK-D-007. Ответственный слой — frontend presentation; Developer диагностирует/исправляет по назначению,Tester подтверждает retest. Это собственный Developer-вход,без присвоения TEST-FIND,смены Manager gates/task states или назначения приоритета.

### Условия и версия

URL `https://exact-orb.localhost/`,готовая карта с цветными графическими аспектами. Конкретный браузер этим сообщением не ограничен: это отдельный report от Yandex004 и Chrome005. InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5,dev/ui-chart-wheel + local uncommitted UI;новый published CandidateSHA отсутствует. Новый screenshot в этом обращении не приложен;прошлый Chrome005 показывает верхнюю часть карты и сам по себе не доказывает отсутствие пояснений ниже viewport.

### Шаги

1. Открыть приложение и получить chart_ready с несколькими типами графических аспектов.
2. Посмотреть на разноцветные линии/символы на колесе.
3. Найти рядом с колесом объяснение,какому типу аспекта соответствует каждый цвет.

**Actual:** пользователь не может по доступной легенде сопоставить цвет с названием аспекта. В текущем facts.mjs есть текст о сплошных/пунктирных линиях,символе☌ и ссылка на числовые факты в таблице;**цветовых образцов с названиями типов нет**. Поэтому bug относится к отсутствию цветовой расшифровки,а не к полному отсутствию любых пояснений.

**Expected по Owner report:** рядом с колесом видна понятная легенда «образец фактического цвета/обозначения → название типа»:соединение☌,полусекстиль,секстиль,квадрат,тригон,квинконс,оппозиция. У соединения показывается символ☌,не вводится новая искусственная линия. Дополнительно сохраняется расшифровка сплошной линии(exact/точный) и пунктирной(working/рабочий);цвет обозначает тип,рисунок — категорию. Пояснение доступно текстом без hover/распознавания только цвета,читабельно и доступно при адаптивной композиции;selected line сохраняет свой цвет/рисунок. Подписи категорий рядом с каждым SVG☌,ранее убранные Owner,этим не возвращаются.

Связано с [REQ-WHEEL-06: различение категорий и типов](../analyst/requirements.md#req-wheel-06) и доступностью REQ-WHEEL-10. Исходный текст REQ06 допускает пояснение в легенде/HTML-таблице;**явная цветовая легенда возле колеса — конкретизация текущего Owner**,а не утверждение,что прежние tests уже требовали swatches. Легенда должна соответствовать реальному renderer;цвета/тип/категория/числа DTO не меняются.

### Evidence и причина

[Manifest кодовой сверки](evidence/dev_find_wheel_006_legend/manifest.json) содержит hashes фактических UI-файлов,существующие legend строки facts.mjs и7 значений palette. [facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs) строит только текстовый p.wheel-legend;[wheel_layout.mjs](../../../../../src/exact_orb/http_api/ui/wheel_layout.mjs) экспортирует ASPECT_COLORS,который использует[wheel_svg.mjs](../../../../../src/exact_orb/http_api/ui/wheel_svg.mjs). В текущем legend нет связи sample/color→type. Это подтверждено code inspection;независимый browser retest в задаче регистрации не запускался.

**Предварительная причина по коду:** палитра используется SVG-отрисовкой,а HTML legend не выводит её образцы и имена типов. Предположение о browser-specific сбое этим не делается.

**Критерий закрытия:** Tester подтверждает на воспроизводимой версии,что пользователь может сопоставить каждый из7 типов с реальным цветом/символом без раскрытия и поиска строк таблицы;solid/dashed/selected/☌ значения не смешаны,цветовой sample и текст доступны в desktop/mobile композициях. После исправления нужен regression на соответствие legend реальной palette;green проверки наличия общего paragraph недостаточны. Сейчас FIXED/CLOSED не объявляются.

Scope:регистрация finding,evidence и собственный handoff. Production code,requirements/чужие артефакты,статусы и palette не менялись. Commit/push не поручены.


## DEV-FIND-WHEEL-007. Таблицы: текст одной строки не выровнен по горизонтали

**Тип / статус:** UI bug report,OPEN;сообщил Owner20.10.2026,оформил Codex / Developer. Контекст TASK-D-007. В этой записи **отдельно** перечислены две Owner-доработки:название Южного узла и компактность таблиц;они не выдаются за доказанные дефекты прежнего контракта. Ответственный слой — frontend facts table layout/presentation. Tester подтверждает независимое воспроизведение/retest,Manager приоритет/назначение;их статусы/gates не меняются и TEST-FIND не присваивается.

### Окружение и evidence

`https://exact-orb.localhost/`,chart_ready,таблица «Планеты и точки». По browser chrome на приложенном screenshot — Яндекс Браузер,видимый zoom50%;точная версия/OS scale/DPR/CSS viewport неизвестны. Размер исходного PNG и SHA256 — [manifest](evidence/dev_find_wheel_007_tables/manifest.json). [Screenshot Owner](evidence/dev_find_wheel_007_tables/tables-alignment-density-owner.png) сохранён побайтно,включая красную пользовательскую отметку на строке Венеры,без редактирования.

Версия локальной регистрации:HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5,dev/ui-chart-wheel + uncommitted UI. Screenshot не привязан независимым воспроизведением к новому CandidateSHA. Источник — текущее сообщение Owner,не новая программная команда из изображения.

### Баг: выравнивание значений

**Шаги:** открыть готовую карту;прокрутить до таблицы «Планеты и точки»;сравнить в одной короткой строке название планеты с соседними значениями «Знак / Положение / Дом / Движение». Пример Owner — Венера;аналогично видны другие строки.

**Actual:** название планеты в первой ячейке визуально находится ниже соседних значений;текст в колонках одной строки не лежит на общей горизонтали. Область названия имеет собственные отступы,а между значениями много пустого пространства.

**Expected:** короткие значения одной desktop-строки выровнены по общей визуальной горизонтали;название/знак/положение/дом/движение имеют согласованную вертикальную привязку. Заголовки и содержимое колонок также имеют согласованные горизонтальные отступы. Многострочные значения не должны ломать эту систему;на мобильной двухстрочной/card композиции применяются её правила,не искусственный запрет всех переносов.

**Кодовое наблюдение / кандидат причины:** в[styles.css](../../../../../src/exact_orb/http_api/ui/styles.css) th/td имеют vertical-align:top и padding12px8px,а[название в facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs) находится в .fact-select со своим padding8px,min-width44px/min-height44px. Соседние plain-text ячейки такого вложенного padding не имеют. Это согласуется со screenshot,но причинность и точные bbox/baselines ещё не проверены отдельным runtime run. Связано с REQ-WHEEL-09/10 и табличным представлением REQ-UI-05/06.

### Отдельные Owner-доработки

1. **Название Южного узла:** вместо «Южный узел (производная позиция)» показывать **«Южный узел»**. По текущему screenshot «убрать надпись» трактуется как убрать только parenthetical «(производная позиция)»,сохранив само имя. Не удалять строку,source ID south_node,R,знак,координаты,дом или derived semantics;не добавлять самостоятельные аспекты южного узла. Прежний нормативный смысл производной позиции сохраняется;меняется visible label. Текущее длинное имя задано в pointNames в facts.mjs. Основание изменения подписи — прямое Owner-поручение,не попытка изменить engine/API.
2. **Компактность таблиц:** сделать ячейки уже,уменьшить лишние межколоночные промежутки и вертикальные отступы;таблицы не должны растягивать короткие значения в чрезмерно широкие равные колонки. Учитывать весь фактический контент,включая R/длинные подписи,сохранять читаемость и полные данные. При уплотнении нельзя незаметно уменьшить принятый44CSSpx target для интерактивных элементов или сломать keyboard focus,selection/five-all/доступную мобильную композицию. Точные новые padding/column widths здесь не утверждаются;это последующая scoped layout работа.

### Проверка и закрытие

При отдельном назначении исправления снять в одном runtime screenshot/bbox/computed padding названия и соседних ячеек,проверить Yandex100% и исходные50%,контрольChrome и desktop/mobile ширины. Изменение zoom не считать доказательством исправленного alignment. Regression должен проверять наблюдаемое выравнивание/компактность,а не наличие конкретного CSS декларатора. Для подписи — «Южный узел» при сохранении source facts/row;для уплотнения — keyboard targets≥44CSSpx и отсутствие горизонтального page overflow на360px.

Критерий закрытия бага — Tester подтвердил согласованное выравнивание на исправленной версии. Две доработки принимаются отдельно по своим expected,не закрываются автоматически вместе с alignment. Причина runtime не установлена,FIXED/CLOSED не объявлены. Текущая задача — регистрация:production code,requirements,чужие артефакты и palette не менялись,runtime tests не запускались. Commit/push не поручены.


## DEV-FIND-WHEEL-008. Хирон и Парс Фортуны не видны; символ Селены не соответствует Р3

**Тип / статус:** UI glyph/rendering bug report,OPEN. Сообщил Owner20.10.2026,оформил Codex / Developer;контекст TASK-D-007. Источник:«на диаграмме нет хирона и парса фартуны … docs/ui_ux/renders/r3-symbols.png … и селена неверный знак имеет». Ответственный слой — frontend point symbols/font/layout,не вычисление карты. Tester подтверждает независимое воспроизведение и retest;приоритет/смена gates или task/change states этим не назначаются,TEST-FIND не присваивается.

### Окружение, версия и evidence

URL `https://exact-orb.localhost/`,полное натальное колесо. На screenshot только фрагмент страницы без browser chrome:браузер/версия/zoom/DPR/CSS viewport не установлены и из прежних Yandex/Chrome сообщений не переносятся. HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5,dev/ui-chart-wheel + local uncommitted UI;независимая привязка screenshot к CandidateSHA отсутствует.

[Исходный screenshot Owner](evidence/dev_find_wheel_008_symbols/chart-symbols-owner.png),[копия указанного эталона Р3](evidence/dev_find_wheel_008_symbols/r3-symbols-reference.png),[manifest размеров/SHA256/source hashes](evidence/dev_find_wheel_008_symbols/manifest.json). Оба PNG скопированы побайтно без изменения. Исходный[справочник символов](../../../../ui_ux/renders/r3-symbols.png) визуально просмотрен:Р3 содержит Хирон,Парс Фортуны и Селену. Р3 — справочник символов,не экран с расчётными данными;остальные его палитры/секции не становятся новым scope этого бага.

### Шаги и actual

1. Открыть готовую натальную карту с points[].id chiron,pars_fortune,selena в принятом ChartDTO.
2. Найти их обозначения на полном колесе и сопоставить с названиями/source rows.
3. Сравнить три символа с `docs/ui_ux/renders/r3-symbols.png`.

**Actual по обращению Owner:** на диаграмме не удаётся найти/распознать Хирон и Парс Фортуны;Селена обозначена неверным знаком. Маленький screenshot сам по себе не отличает отсутствие элемента от неподходящего font glyph/малого масштаба/перекрытия,поэтому отсутствие source rows/DOM не объявляется доказанным.

**Кодовая сверка:** текущий POINT_GLYPHS в[wheel_layout.mjs](../../../../../src/exact_orb/http_api/ui/wheel_layout.mjs) уже содержит chiron=⚷(U+26B7),pars_fortune=⊗(U+2297),selena=○(U+25CB). Поэтому для первых двух нужно проверить именно actual rendered label/font/bbox/visibility,а не предположительно добавить дублирующие точки. [wheel_svg.mjs](../../../../../src/exact_orb/http_api/ui/wheel_svg.mjs) выводит текстовые glyph с native font metrics. Наличие data-label/source ID ещё не доказывает визуальную узнаваемость знака. В Р3 Селена — **полумесяц с небольшим крестом вверху справа**,не пустой круг;расхождение текущего mapping с указанным Owner-эталоном подтверждено визуальной/code сверкой.

### Expected

- Если принятый DTO содержит chiron/pars_fortune/selena,каждая точка имеет на колесе видимое,узнаваемое обозначение,соответствующее Р3 и однозначно сопоставимое с её HTML-строкой. Для Хирона — знак ключа из справочника,для Парса Фортуны — окружность с диагональным крестом,для Селены — указанный полумесяц с крестом. Это не требование добавлять отсутствующие в DTO точки.
- Символы не теряются из-за font fallback,tofu/пустого bbox,clipping/перекрытия,слияния с true anchor или R;сохраняются читаемость и различение Селены/Солнца/Луны/Парса Фортуны. Выбор/подсветка и aspect mode сохраняют семантику:в отдельном выбранном аспекте не обязаны быть видны все16точек.
- Рисуется только принятое представление:longitude,house,retrograde,исходные IDs/порядок/числа DTO и engine/API не меняются. Наблюдаемая видимость symbol проверяется отдельно от cardinality меток.

Основание — текущий прямой Owner report с конкретным Р3;связано с[REQ-WHEEL-02](../analyst/requirements.md#req-wheel-02),REQ-WHEEL-05/09/10. Конкретная замена Unicode на вектор/другой glyph этим заданием регистрации не реализуется;новые зависимости не добавляются.

### Диагностика и закрытие

Для воспроизведения зафиксировать полный принятый DTO/три source rows,точную версию,браузер/zoom/OS scale/font/platform fallback. На actual SVG проверить отдельно наличие трёх data-label,computed font/getBBox и screen bbox/контур/контраст/clipping/перекрытия;сопоставить native screenshot с Р3,включая нормальный100% и narrow-width контроль. Независимые позитивные контроли:канонические Солнце/Луна/узлы и реальное отображение каждой из трёх проблемных точек;проверки count16/непустого textContent недостаточно. Не компенсировать проблему подменой source IDs/чисел или искусственным новым расчётом Селены.

**Причина:** для Селены подтверждено несоответствие выбранного glyph эталону;для невидимых/нераспознаваемых Хирона и Парса Фортуны runtime-причина пока не установлена. **Закрытие:** Tester на исправленной воспроизводимой версии подтверждает видимость и соответствие всех трёх символов Р3 с сохранением остальных symbols/source facts;Developer даёт scoped regression и version/evidence. Сейчас FIXED/CLOSED/REJECTED не объявляются.

Текущая задача только регистрация:runtime/browser retest/новый build не запускались,production code/requirements/Manager/Tester artifacts/gates не менялись. Commit/push не поручены.


<a id="owner-bugfixes-2026-10-20"></a>
## Текущий результат Developer — исправления004…008 по Owner20.10

Codex / Developer:после уточнения Owner «Исправить все баги и доработки» реализация выполнена локально. Предыдущие OPEN-записи — исходные сообщения/evidence;они не переписываются как успешный retest. InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5+local UI,dev/ui-chart-wheel. [Пакет08](prompts/08-owner-bugfixes.md),[команды/actual/хэши](evidence/task_d007_bugfixes/README.md),[план§11](full_wheel_implementation_plan.md#11-task-d-007--исправление-owner-bug-reports004008).

| Report | Текущий Developer результат | Что остаётся |
|---|---|---|
|004 / Yandex | Стартовая форма центрирована,нормальные CSS fonts;chart mode выбран до первого snapshot,убран intermediate capacity failure | Пользовательский zoom50% не сбрасывался/не компенсировался;независимая проверка исходного профиля100/50 отдельно |
|005 / Chrome | Полный круг fit по width+height в обычном/aspect view,без SVG/font shrink;resize сохраняет selection | Публикация версии и независимый retest |
|006 / legend |7color/type samples+solid/dashed,цвета из фактической palette;видна сбоку полного колеса | Публикация и retest доступности/визуальной сверки |
|007 / alignment | Общее выравнивание коротких текстов,content-based width,меньше cell spacing;44px controls сохранены | Публикация и retest |
|007 /2Ownerдоработки | «Южный узел» без parenthetical;таблицы компактнее,source semantics/числа не изменены | Owner просмотр и отдельная приёмка этих изменений |
|008 /symbols | Хирон/ПарсФортуны/Селена — реальные R3 vector shapes;явная видимость и source association проверены | Публикация и независимый visual retest |

Текущий технический результат — локальное исправление,ожидание публикации/retest. Нового commit нет,поэтому официальный переход FIXED_PENDING_RETEST/CLOSED и TEST-FIND-IDs за Tester не объявляются. Manager/Tester artifacts/gates не менялись. Runtime/browser/evidence и фактические source fingerprints — в README;live HTTPS выдача отдельно от mock HTTP/research. Матрица проверяет clean native Chrome/Yandex;не выдаётся за изменение настройки существующего пользовательского профиля.


<a id="dev-find-wheel-009"></a>
## DEV-FIND-WHEEL-009. Поле даты позволяет набрать шестизначный год

**Статус:** OPEN, исправление отложено по прямому решению Owner от 20.10.2026: «заведи баг и в тех долг положи». **DebtId:** [DEBT-UI-002](../../../technical_debt.md#debt-ui-002). Оформил Codex / Developer. Предварительная severity — minor / P3: дефект ввода и обратной связи; успешный расчёт неподдерживаемой даты не доказан. Независимый retest Tester не выполнен.

**Версия:** dev/ui-chart-wheel, InputSHA `0da99518ada67603b08ab4220d337e3a5e3aae60`; screenshot Owner не имеет независимой привязки к served commit. URL обращения `https://exact-orb.localhost/`. Браузер, версия, zoom, DPR неизвестны: в изображении нет browser chrome. Не переносим Yandex/Chrome из других обращений.

**Evidence:** [исходный screenshot](evidence/dev_find_wheel_009_date/date-six-digit-year-owner.png), [manifest с SHA256 и размерами](evidence/dev_find_wheel_009_date/manifest.json). PNG сохранён без изменения. Видна дата `20.03.146464`, выделен шестизначный год; рядом сохранены Москва/00:45 и прежняя сводка карты 1985-09-02. Прежняя сводка сама по себе не доказывает отправку или расчёт новой даты.

**Шаги по обращению:** открыть форму рождения; выбрать сегмент года в дате; ввести `146464` при дне/месяце `20.03`. Нативное поведение клавиатуры/paste в конкретном браузере требует независимого воспроизведения.

**Actual:** контрол показывает шестизначный год как редактируемое значение. В статической разметке [index.html](../../../../../src/exact_orb/http_api/ui/index.html) это `input type=date required` без min/max; верхняя граница/ограничение сегмента года не заданы. Это фактор UX, а не доказательство отсутствия submit-валидации.

**Expected:** ввод даты даёт понятную границу поддерживаемого четырёхзначного года либо явную обратную связь о неподдерживаемом значении; нельзя молча обрезать `146464` до другого года и строить карту по изменённой дате. Неподдерживаемое значение не формирует intent. Сохраняются календарная проверка, точные остальные поля и согласованный серверный контракт. Выбор точного поведения native control/момента сообщения относится к погашающей задаче; новый узкий диапазон вроде 1900–2100 этим report не вводится.

**Кодовая сверка:** [form.mjs](../../../../../src/exact_orb/http_api/ui/form.mjs), calendarDate, уже требует ровно YYYY-MM-DD и год не 0000. Чистая [диагностическая проба](evidence/dev_find_wheel_009_date/date_validation_probe.mjs) с выбранным местом, корректным временем и ручным acknowledgement проверяет `146464-03-20` → ok=false, date error, intent отсутствует; позитивные контроли `1985-09-02`, `0001-01-01`, `9999-12-31` → ok=true. [Actual](evidence/dev_find_wheel_009_date/date_validation_actual.json). Это проверка формы, не реальный POST/browser reproduction. Связаны REQ-UI-02/03, AS-UI-06 и существующий tests/ui/form.test.mjs; новый диапазон и исправление не реализованы.

**Последствия / границы долга:** допускается отложить улучшение ввода и обратной связи в закрытом текущем UI. Перенос не разрешает принимать шестизначную дату на сервере, ослаблять validation, менять расчёты или считать баг исправленным. Статусы/gates Manager и чужие артефакты не меняются. Полный причинный анализ browser-specific поведения и оценка погашения — при постановке исправления; оценка реализации сейчас не согласована.

**Закрытие:** Tester на точном исправленном commit проверил ввод с клавиатуры, paste/замену сегмента и календарь в поддерживаемых Chrome/Yandex; год из контрпримера ограничивается либо получает явную ошибку до расчёта без усечения/лишнего POST. Позитивная дата и разрешённые четырёхзначные границы сохраняются; чувствительная regression, соответствие API и отсутствие потери остальных полей подтверждены. До этого bug остаётся OPEN. Погашающий change пока не назначен.

Общее Owner-решение записано в едином реестре; публикация Manager отдельным документальным PR в main и published registry SHA ещё отсутствуют. Это не новое исключение для gates. Production code, требования и тесты не изменены; browser/HTTP-проверки и исправление не выполнялись. Commit/push не поручены.


<a id="dev-find-wheel-010"></a>
## DEV-FIND-WHEEL-010. Значки планет на колесе слишком мелкие

**Статус:** OPEN; визуальный UX bug report / доработка читаемости, исправление отложено в [DEBT-UI-003](../../../technical_debt.md#debt-ui-003). Источник Owner20.10.2026: «заведи техдолг баг - увелисить значки планет». Оформил Codex / Developer. Предварительно minor / P3; это рекомендация для triage, не утверждённый Owner приоритет. Новое нарушение минимального размера действующих критериев не заявляется.

**Версия и evidence:** dev/ui-chart-wheel, InputSHA `0da99518ada67603b08ab4220d337e3a5e3aae60` + сохранённые локальные изменения таблиц. [Manifest](evidence/dev_find_wheel_010_symbol_size/manifest.json) содержит исходное поручение и hashes ответственных модулей. Новый screenshot и точные browser/version/viewport/zoom/DPR не переданы; прежние browser-specific сообщения не считаются новыми данными этого обращения. Независимое воспроизведение и реальные измерения для нового долга не выполнялись.

**Сценарий:** открыть готовую карту, найти значки планет на колесе и сопоставить их с таблицей. **Actual по Owner:** значки выглядят слишком маленькими, требуется увеличить их. **Кодовая сверка:** [wheel_layout.mjs](../../../../../src/exact_orb/http_api/ui/wheel_layout.mjs),pointparts, задаёт основному текстовому glyph размер16,маркеру R —12; [wheel_svg.mjs](../../../../../src/exact_orb/http_api/ui/wheel_svg.mjs) выводит measured parts и отдельные native vector symbols. Font-size/native coordinate units не равны измеренному видимому bbox и не доказывают читаемость в конкретном браузере. Причина визуального неудобства в конкретном окружении пока не установлена; browser zoom и вся композиция этим report не признаются неисправными автоматически.

**Expected:** значки планет на колесе крупнее текущих и легко различимы; применимый размер native vector/text обозначений согласован в погашающей задаче. Точный новый CSSpx-размер и изменение других подписей Owner пока не задавал. Нельзя просто увеличить только текстовый слой, забыв измерение vector/bbox и layout. Сохраняются соответствие source ID,сами символы Р3,точные данные таблиц и исходные отметки положения. Увеличенные glyph/R не перекрывают друг друга,числа домов/границы и другие обязательные обозначения,не обрезаются;условия размещения внутри опубликованных домов сохраняются. Размер зодиака,таблиц и всего SVG не входит в текущее поручение регистрации.

**Погашение / критерий закрытия:** выбрать с Owner проверяемый целевой размер и область применения,переизмерить реальные text/vector bounds и перепроверить размещение. На согласованных desktop/mobile frames (предложение Developer:1440/768/360CSSpx) проверить sparse и скученные карты,узкие дома,несколько рядов,R,полный вид/выбор аспекта и соответствие точным данным. Есть screenshots+browser/font/scale и независимые позитивные контроли узнаваемости;regression чувствителен к потере размера/перекрытию,а не только к числу в font-size. Tester подтвердил exact commit,Owner принял читаемость,исправление интегрировано. При недостатке места предъявить контрпример и варианты,не уменьшать молча другие принятые критерии.

**Решение о переносе:** прямое поручение Owner принимается как выбор отложенного исправления читаемости. Баг остаётся OPEN;это не FIXED/CLOSED и не новое gate-исключение. Developer UI — ответственный слой;Manager назначает конкретного исполнителя/приоритет/условие возврата и публикует общий реестр в main;Tester проверяет результат. ПриоритетP3 и возврат при следующей итерации читаемости колеса — предложения Developer,не выдуманные согласованные сроки. Погашающий change и оценка пока не назначены.

Текущий scope — только запись bug/debt/собственный handoff. Production code,размеры16/12,тесты,engine/API/golden,Manager/Analyst/Tester artifacts и gates не менялись;browser/runtime/full pytest не запускались. Проверены источники,уникальность IDs,ссылки и git diff --check. Commit/push не поручены.


<a id="tester-004-developer-response"></a>
## Ответ Developer — TEST-FIND-WHEEL-004

Codex / Developer,20.10.2026. По текущему прямому Owner-поручению после Git-only update3c2744e→3b95934c884caa9f40ea70e935991457058b87b9 изучен [опубликованный Tester возврат](../tester/defects.md#test-find-wheel-004),OutputSHA1cfbe3156761da1cfba1ef66133febd7c7bae265. Это одна новая подтверждённая runtime-находка;исторические001/003 CLOSED,002 — открытый requirement gap,не новый implementation defect.

На обновлённой базе reproduced lower native aperture41.75/42.75/41.25 при height44 на1440/768/360. Исправлен styles.css:fact-select rectangle с min46 и внутренним Q44. Native positive pointer controls теперь достигают владельца;keyboard/focus/Owner first-five иcompactness сохранены. [Пакет10](prompts/10-tester-hit-area.md),[before/after/regression](evidence/task_d007_tester004/README.md). Собственный результат — локальное исправление,ожидает публикации и независимого Tester retest;официальный TEST-FIND status не переписан.

Отдельное Tester наблюдение зазора gap=1.9999923706054688 остаётся INDETERMINATE:без независимого precision budget нельзя выдать PASS или новый численный порог. Geometry/опубликованные координаты не менялись;TEST-FIND-WHEEL-002/gates не закрываются. Старые Owner debts009/010 не погашаются CSS-исправлением HTML target. Изменений glyph size/даты этим не сделано. [Scope/исходные hashes](evidence/task_d007_tester004/baseline.json).
