# Замечания Tester: ui-chart-wheel

**Автор:** Codex / Tester. Первоначальное обнаружение — 2026-10-15, TASK-T-001 / review `2b846077b317e33dd892565419942c4db8517b1e`. Повторная документальная сверка — 2026-10-16, TASK-T-002 / InputSHA `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`, Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`. Это review документов, не TestedSHA реализации. Окружение: Windows, Git / Markdown / PUML / JS; runtime / browser не запускались. Реестр: [Manager §3](../manager_artifact.md#3-единый-реестр-dp) @ новом InputSHA.

Это единственный Tester-реестр находок. На историческом documentary baseline T001/T002 подтверждённых `bug (implementation defect)` не было: CandidateSHA не передан, production M1-8 не реализован на том baseline. Severity S1–S4 для нижних requirement gaps неприменима; priority — предложение порядка уточнения, не подтверждение Manager. Уже зарегистрированные DP и принятый долг не объявляются новыми багами. **Runtime-дополнение20.10.2026:** на TestedSHA0da99518ada67603b08ab4220d337e3a5e3aae60 подтверждён TEST-FIND-WHEEL-004; его evidence / severity / retest отделены от исторических gap001…003.

| ID | Тип / источник | Severity | Priority | Статус | Blocks сейчас | Ответственный |
|---|---|---|---|---|---|---|
| [TEST-FIND-WHEEL-001](#test-find-wheel-001) | requirement gap: рассогласование версий после Owner decisions | N/A | P2, PROPOSED исторически | CLOSED | Нет по этому gap; полные gates отдельно | Tester подтвердил; Manager регистрирует результат |
| [TEST-FIND-WHEEL-002](#test-find-wheel-002) | requirement gap: измерительные критерии в DP-O-011/012 | N/A | P2, PROPOSED | OPEN | Окончательный oracle плотности / размещения / fallback и затронутая acceptance | Developer + Analyst / Owner |
| [TEST-FIND-WHEEL-003](#test-find-wheel-003) | requirement gap: переходы выбора внутри DP-O-013 | N/A | P2, PROPOSED исторически | CLOSED | Нет по этому gap; runtime tests ещё NOT RUN | Tester подтвердил; Manager регистрирует результат |
| [TEST-FIND-WHEEL-004](#test-find-wheel-004) | implementation defect: effective HTML hit-area меньше Q44 | S3 | P2, PROPOSED | CLOSED | Нет по004;002/общие gates отдельно | Tester / Codex retest9974195 PASS;Developer fix9974195 |

Закрытие requirement gap означает проверенный текст expected result и зарегистрированный источник, не исправление runtime bug / PASS продукта. Priority не подтверждался Manager. Исходные примеры / условия ниже сохранены; актуальные результаты сверки добавлены с автором, датой и точными версиями.

<a id="test-find-wheel-001"></a>
## TEST-FIND-WHEEL-001. Пакет v1 ещё не отражает актуальные решения

**Статус:** CLOSED.

**Обоснование статуса:** Tester / Codex, повторная документальная сверка 2026-10-16: Analyst v3, REQ-WHEEL-02/03/05…10, REQ-UI-04/05/06/11, AS-WHEEL-01/02/07/08/12/13/14/24…30, MODIFY AS-UI-22 и три sequences сверены с Owner evidence, зарегистрированным Manager @ 543b7ec. Разрыв версии v1 устранён; ролевые approvals и runtime evidence этим не подтверждаются.

### Историческое обнаружение @ 2b84607

**Первоначальное основание OPEN:** статически сопоставлены Manager @ InputSHA и Analyst v1; явная актуализация предусмотрена самим Manager, новой версии пока нет. Это ожидаемая незавершённая передача, не нарушение реализации и не повторный вопрос Owner о принятом выборе.

**Требования / сценарии:** [REQ-WHEEL-02/03/05/06/07/08/09/10](../analyst/requirements.md), [AS-WHEEL-08/09/10/12/13/14/24/25](../analyst/scenarios.md), [sequence 001](../analyst/sequence_diagrams/ui/001-chart-presentation.puml), [sequence 002](../analyst/sequence_diagrams/ui/002-wheel-table-selection.puml). **Связанные решения:** DP-O-010…014. **Сценарий Tester:** [T-WHEEL-06](test_plan.md#t-wheel-06), также 02/04/05/08/11.

### Воспроизводимое сопоставление

1. Читать решения Owner от 15 октября в Manager §3 @ InputSHA.
2. Сопоставить Analyst v1: AS-WHEEL-25 всё ещё условный кандидат; AS-WHEEL-24 называет локальный HTML fallback рекомендацией; AS-WHEEL-08 не утверждает штрих категорий.
3. AS-WHEEL-12 / sequence 002 предполагают общий закрытый блок подробностей; AS-WHEEL-13 / sequence 002 описывают явное «Снять выделение»; сценарии не фиксируют новый отбор всех аспектов одной планеты и начальные пять строк.
4. Expected: следующая согласованная версия явно применяет зарегистрированные решения, сохраняет baseline obligations / IDs и отделяет оставшиеся OPEN части. Actual: v1 остаётся прежней, содержит условные критерии и устаревшее действие.

### Позитивный контроль / предел

В Manager есть фактическое решение по DP-O-014 и детальные Owner evidence по DP-O-010…013; Analyst-файлы доступны и имеют прежние manifest hashes. Отсутствие новой версии проверяется по доступным refs после fetch; гипотетические непубликовавшиеся изменения не оценивались.

### Передача и закрытие

Analyst актуализирует FULL / DELTA / scenarios / sequences на текущих решениях; Manager фиксирует точную версию и reviewers. Снятие отдельной кнопки не означает исключение доступного снятия аспекта: см. TEST-FIND-WHEEL-003. Закрытие — повторная сверка Tester новой опубликованной версии с реестром, без потери исходных REQ-UI / AS-UI. **Retest при первоначальном review:** не выполнен, исправленная версия не передана. **Priority confirmation:** ожидается Manager. **Условие следующей проверки:** handoff Analyst с точным SHA.

### Closure evidence — TASK-T-002, 2026-10-16

Проверены Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c` и регистрация DP-O-010…014 / назначения в Manager @ `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`: orientation, локальный SVG fallback, условный разнос, line styles, ☌, five/all, point/aspect toggle, automatic current / draft. Прежняя отдельная кнопка снятия не возвращается; остающиеся измерительные вопросы отделены и не препятствуют закрытию именно разрыва версий.

**Фактический результат:** document review PASS; manifest Analyst 9/9 и source payload подтверждены. Закрытие автором Tester / Codex; [review.json](evidence/review.json). Следующий шаг — регистрация нового Tester package / review назначенными участниками, без присвоения чужих approvals. Повторно открыть при выявлении расхождения между новой утверждаемой версией и зарегистрированными решениями.

<a id="test-find-wheel-002"></a>
## TEST-FIND-WHEEL-002. Для плотности и ☌ ещё нет окончательного oracle

**Статус:** OPEN.

**Обоснование статуса:** на повторной сверке 2026-10-16 DP-O-011/012 ещё не имеют измерительных критериев минимальности / плотности / fallback и реального размещения нескольких R / ☌. Подпись категории и контур только выбранного символа уже зарегистрированы и отражены в v3; они больше не часть открытого выбора. Новый DP не создаётся.

### Историческое обнаружение @ 2b84607

**Требования / сценарии:** [REQ-WHEEL-05/06/09/10](../analyst/requirements.md), [AS-WHEEL-07…10/16](../analyst/scenarios.md); [T-WHEEL-04](test_plan.md#t-wheel-04), [T-WHEEL-05](test_plan.md#t-wheel-05). **Решения:** DP-O-011/012. **Blocks:** воспроизводимый verdict минимальности / предельной плотности / различения category и selection у ☌; простые правила Owner уже можно готовить к проверке.

### Различающий пример

1. Взять разрежённый контроль, конфликтующую группу через 0° с пятью R и отдельную далёкую точку; затем 16 IDs в секторе на 360px и несколько conjunction-пар.
2. Сравнить два варианта: оба не теряют данные и сохраняют порядок, но расходятся по величине / направлению смещения и читаемости. Без определения пересечения и допустимого предела нельзя воспроизводимо оценить «минимальный».
3. Exact/working у обычных линий имеют выбранный штрих. ☌ не является хордой: пока не определено, как на самом маркере показать категорию / выбор и различить совпавшие пары.
4. Expected для окончательной acceptance: согласованный измеримый критерий и наблюдаемый исход при недостижимой плотности; actual: критерии ещё открыты. Это не воспроизведение бага renderer.

### Рекомендация и позитивный контроль

Developer определяет измеряемые bounds / collision / seam и детерминированный oracle без переноса чисел prototype spread(). Owner принимает наблюдаемый предел и fallback по Analyst / Developer / Tester evidence. Проверять: отсутствие смещения / выноски без конфликта; неизменность неконфликтующих элементов; выноски только для смещённых, true anchor и циклический порядок через 0°; доступ всех ID / пар и чтение текста. Контроль — разрежённая карта читаема, конфликтующая группа действительно содержит все заданные IDs, exact и working адресуются как разные исходные записи. Ни дополнительный ряд, ни скрытие, ни минимальные пиксели этим review не утверждаются.

**Закрытие:** Developer criterion / drawing ADR + принятый наблюдаемый предел в соответствующих DP, Analyst scenarios и повторный review Tester. **Retest:** не выполнен. **Priority confirmation:** ожидается Manager. **Следующая проверка:** версия критериев и данные переданы; задача независимой подготовки не остановлена.

### Повторная сверка — TASK-T-002, 2026-10-16

REQ-WHEEL-06 / AS-WHEEL-07/08 / sequence 002 и DP-O-012 @ `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba` определяют подпись «точный» / «рабочий» и усиленный контур только выбранного ☌ с сохранением подписи. Этот смысловой остаток устранён. Текст первоначального примера выше сохранён как история, не как актуальный вопрос Owner.

Остаются OPEN: критерий bbox/collision/minimality, допустимые интервалы / bounds, placement нескольких R / ☌, палитра / legend layout и принятый наблюдаемый fallback при недостижимой плотности. Нового технического пакета TASK-D-002 и real SVG/font/browser evidence нет. Developer consultation v1 @ `04be207` содержит предложение отдельного bounded spike, не результат измерений и не допуск его исполнения.

**Результат:** закрытие всего TEST-FIND-WHEEL-002 не подтверждено, статус OPEN. Условия закрытия сохраняются: проверяемые Developer критерии / drawing ADR, согласованный наблюдаемый предел / fallback в существующих DP, соответствующие AS и независимое evidence. Priority P2 остаётся PROPOSED; негативные сценарии и разрежённый positive control — [T-WHEEL-05](test_plan.md#t-wheel-05).

<a id="test-find-wheel-003"></a>
## TEST-FIND-WHEEL-003. Переход от фильтра планеты к аспекту и снятие аспекта

**Статус:** CLOSED.

**Обоснование статуса:** Tester / Codex, повторная документальная сверка 2026-10-16: REQ-WHEEL-07/08/10, REQ-UI-06, AS-WHEEL-28/29 и sequence 002 согласованно задают взаимоисключающие режимы, переход к unrelated aspect, одну строку / пару, повторное снятие через графику / HTML / keyboard и возврат прежнего раскрытия без фильтра планеты. Expected result определён; runtime не запускался.

### Историческое обнаружение @ 2b84607

**Первоначальное основание OPEN:** составлен контрпример взаимодействия двух правил; в доступном контракте нет определённого исхода для обеих ветвей ниже. Требуется уточнение DP-O-013, не самостоятельный выбор поведения Tester.

**Требования / сценарии:** [REQ-WHEEL-07/08/10](../analyst/requirements.md), REQ-UI-06, [AS-WHEEL-11/13/23](../analyst/scenarios.md), [sequence 002](../analyst/sequence_diagrams/ui/002-wheel-table-selection.puml); [T-WHEEL-07](test_plan.md#t-wheel-07). **Решение:** DP-O-013. **Обнаруживший:** Tester / Codex, этот review. **Blocks:** утверждение соответствующих interaction branches / G3; независимые ветви остаются доступны.

### Воспроизведение пробела контракта

1. Использовать controlled UI DTO F4 с аспектами Луна→ASC и Солнце→MC; обе exact/working пары видны на колесе.
2. Выбрать Луну: по принятому правилу таблица содержит все и только её аспекты.
3. Выбрать на колесе Солнце→MC: REQ-WHEEL-07 требует связанную конкретную строку. Она отсутствует в текущем отборе. Не определено, сбрасывается ли выбор планеты / фильтр, изменяется ли выбранная планета или применяется другой явно выбранный переход.
4. Отдельно выбрать аспект через HTML без выбранной планеты, затем попытаться снять выбор клавиатурой. Owner отклонил отдельную кнопку и подтвердил повторную активацию именно планеты. Применение этого жеста к аспекту не принято.
5. Actual: expected result этих переходов не определён; runtime не проверялся. Expected: явный переход, конкретная доступная выбранная строка / пара и доступное снятие aspect-only без добавления отклонённой кнопки.

### Позитивный контроль и рекомендация

Контрпример использует два разрешённых типа действия и адресуемые разные пары одной карты; он не требует нового выбора angles. До фильтра обе строки присутствуют. Рекомендация Tester для рассмотрения Analyst / Owner: выбор аспекта вне текущего отбора переводит UI в явно определённое состояние, где видна именно эта пара; для aspect-only описать одно доступное действие снятия с pointer / keyboard и его связь с отбором. Конкретный вариант и новый UX не утверждаются этим review.

**Ответственный:** Analyst формулирует варианты / expected result в DP-O-013; Owner выбирает, Developer подтверждает реализуемость. **Закрытие:** решение зарегистрировано, requirements / AS / sequence согласованы и повторно сверены Tester. **Retest при первоначальном review:** не выполнен, новый контракт не передан. **Priority confirmation:** ожидается Manager. **Повторное открытие:** новый контрпример против согласованной версии сохраняется с исходным evidence.

### Closure evidence — TASK-T-002, 2026-10-16

На Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, Manager @ `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba` проверены оба контрпримера: Луна → sun→mc снимает point/filter, оставляет одну aspect row / graphic pair; повторная активация линии/☌/строки (включая keyboard и background через HTML) снимает аспект, возвращает прежнее раскрытие общего списка, не восстанавливает фильтр Луны. Aspect → другая планета даёт полный отбор её published aspects. Это AS-WHEEL-28/29 и REQ-WHEEL-07/08/10; подпись/контур ☌ — REQ-WHEEL-06.

**Фактический результат:** document review PASS; TEST-FIND-WHEEL-003 закрыт автором Tester / Codex. [T-WHEEL-07](test_plan.md#t-wheel-07) и матрица актуализированы; исполнение / regression tests всё ещё NOT RUN. Повторно открыть, если новая версия потеряет этот expected result; нарушение реализацией описать по фактическому CandidateSHA, не приписывая текущему документальному closure runtime PASS.

<a id="test-find-wheel-004"></a>
## TEST-FIND-WHEEL-004. Rounded HTML button не содержит effective Q44

**Тип / автор:** bug (implementation defect), обнаружил Codex / Tester,20.10.2026, прямой runtime test Owner. **Статус CLOSED / независимый retest9974195 PASS20.10.2026**;первоначальный OPEN / воспроизведён на0da9951 сохранён ниже. **Severity S3** — исторически край активного элемента не выполнял действие, основной путь через центр / keyboard был доступен; данные не терялись. **Priority P2 PROPOSED**, подтверждает Manager. **Owner исправления:** Developer / TASK-D-007. **Blocks сейчас:** нет по004;002/общие gates остаются отдельными.

**Требование / источник:** REQ-UI-10, REQ-WHEEL-10, AS-WHEEL-16/23; effective native H / half-open Q≥44×44 по [T006, строка H1–H5](task_t006_review.md) / [Developer criteria H](../developer/task_d003_implementation_plan.md#d004-hit-focus). Поздний Owner007 compactness сохраняет44px targets; правило не заменялось одним bbox. **TestedSHA:**0da99518ada67603b08ab4220d337e3a5e3aae60. Chrome155.0.8059.40 / Windows / CSS scale1 / viewport1440,768,360.

**Данные / воспроизведение:**

1. Получить F1 из опубликованного column_full_composition_v1/data.json через controlled current в настоящей странице. Запуск: node docs/project_management/change_plans/ui-chart-wheel/tester/evidence/runtime_2026_10_20/hit_area_probe_v2.cjs с Node executable из [runtime report](runtime_review_2026_10_20.md). Скрипт пишет новый probe02 и отказывается переписывать существующий; повторять из изолированной копии собственного каталога, с явным новым output namespace.
2. Прокрутить HTML Sun control в viewport; измерить actual bbox и native hit horizontal sections. Не заменять native target проверкой element.click / только min-height.
3. Нажать native mouse в центре — Sun выбирается, isTrusted=true. Затем native mouse в bbox corner(left+1,top+1) — выбранное состояние не меняется, событие до Sun не доходит.
4. Негативное доказательство Q44: bbox высотой ровно44. На y=top+43 effective horizontal aperture уже **41.75 /42.75 /41.25px**, меньше44; horizontal step0.25. Независимые straight-rectangle44/43 calibration controls дают44/43 тем же методом. Не использовать крайние fractional boundary rows как единственное доказательство.

**Expected:** весь half-open axis-aligned Q44 внутри effective owner/outcome H, плюс рабочая pointer / keyboard активация. **Actual:** bbox50.0625×44 проходит поверхностную проверку размеров, а rounded effective H не содержит Q44; center и keyboard работают. Это один дефект на24 sampled fixture/width cases, не24 бага.

**Корневая причина:** [styles.css](../../../../../src/exact_orb/http_api/ui/styles.css) оставляет .fact-select border-radius8px при min-height44px, а compact table rule убирает padding. Sun достигает только44px высоты; скруглённые top/bottom sections уже требуемого квадрата. Не предлагается уменьшать44 / менять Owner choice. Нужен достаточный native target, выбор конкретного CSS-исправления — Developer.

**Evidence:** [probe02 actual / все raw sections и trusted events](evidence/runtime_2026_10_20/probe02/actual.json), [native02](evidence/runtime_2026_10_20/native02/actual.json), [screenshot360](evidence/runtime_2026_10_20/probe02/target-360.png). Позитивный контроль — живой центр Sun / клавиатура и независимый solid44; negative control — solid43. Получение карты и путь controls фактически выполнялись; отсутствие действия не выведено из невыполненного пути.

**Условие закрытия / retest:** Developer передаёт точный исправленный SourceSHA, deterministic regression и actual native H evidence. Tester повторяет effective44 containment / trusted coordinate outcome на affected controls и трёх widths, с44/43 paired controls и сохранением live focus / source rows / компактности / отсутствия overflow. До этого OPEN; весь TEST-FIND-WHEEL-002 и Manager gates не закрываются автоматически.

### Retest closure — 2026-10-20, RetestedSHA9974195

**Codex / Tester,23:03:56MSK /20:03:56UTC: CLOSED / RETEST PASS.** Опубликованное исправление **99741958b4bbee8884505920f4a02f2f19dea3e3**, styles LF SHA256e4b4539fbe051e66c9f8226bc6834828e925eb3b12aea6f93e6fdfa20d53bfec, изменяет rounded44 на rectangle min46 с Q44 inset≥1. Полный исходный контрпример0da9951 / его raw evidence выше сохраняются; это новая проверка,не переписывание старого FAIL.

[Адресный отчёт](retest_2026_10_20_004.md),[native green02](evidence/retest_2026_10_20_004/green02/actual.json):Chrome155.0.8059.40 / Yandex26.8.0.0 ×1440/768/360,**6/6cases,672/672checks**. Проверены372 normal+36 selected HTML controls:явные Q44,actual box/radii,ancestor clips/paint partition и121 native owner probes на запись;независимые44/43/overlay/clip/thin-overlay+paired removal controls.30trusted pointer toggles Sun и12 Enter/Space,connected visible focus/scroll,source IDs/first-five/all,desktop55≤56 иno horizontal overflow — PASS. First-five/current/changed-goal once regressions также проходят;результат не подменён Developer self-check.

[Старый CSS sensitivity](evidence/retest_2026_10_20_004/red03/actual.json) на текущем UI даёт ожидаемый RED;все независимые калибровки достигнуты. Исходный собственный probe повторён в новом namespace с обновлённой metadata;legacy possible44 не принят как самостоятельный certificate. Ранние ошибки классификации paint в новом harness исправлены адресно,все промежуточные runs сохранены.

Regression:targeted UI41PASS/all UI229PASS;Python delivery/boundaries53PASS;fullpytest2959PASS+1known DEBT-CALC-001 skip. **Blocks сейчас:** нет по004;PriorityP2 остаётся PROPOSED,Manager не приписано её подтверждение. TEST-FIND-WHEEL-002 / gap2 native precision остаются OPEN/INDETERMINATE;global Candidate/G4/G5 / Owner acceptance не объявлены. Повторно открыть004 при подтверждённой потере Q44/owner/outcome в новой версии с exact SHA и paired control.
