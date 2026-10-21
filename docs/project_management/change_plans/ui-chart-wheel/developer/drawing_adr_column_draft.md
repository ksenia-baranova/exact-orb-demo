# DRAFT — пассивный Chart Renderer с внутренними рядами планет

**Codex / Developer,19.10.2026. Статус:DRAFT.** Ревизия technical proposal по прямому поручению Owner. Кандидат ADR-0042: [реестр](../../../../requirements/decisions/README.md) на InputSHA07bb56ba5d49ec76de64df41ad80d175fbe90a2d заканчивается0041; номер не резервируется, нормативный ADR не создаётся. Перед переносом проверить реестр повторно. [Прежний проект D005](https://github.com/ksenia-baranova/exact-orb-demo/blob/883b6d3a47f7113e44ede73c9ad16b40f15bbdaf/docs/project_management/change_plans/ui-chart-wheel/developer/drawing_adr_draft.md) и его SHA8b8c4c8 сохраняются; принятые ADR не заменяются этим draft.

## Контекст и область

Owner выбрал управление через HTML и условную колонку для скученных point-меток; SVG пассивно отображает selection. [Source решения](owner_decision_drawing_2026-10-19.md), [Manager DP-O-010…013](../manager_artifact.md#3-единый-реестр-dp). Изменяются проект внутренней границы renderer и drawing domain; HTTP/engine/ChartDTO/cache/golden не затрагиваются. Input: accepted v3+S1@2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 + поздние Owner delta. Новый TargetContractSHA ожидает узкой синхронизации Analyst; решение владельца DP-O-010/011/012 ещё не принято на этот draft.

## Предлагаемое решение

1. Session остаётся единственным accept-owner/HTTP/recovery: создаёт acceptanceSeq, immutable submitted attempt и cause. facts.mjs + chart_state.mjs потребляют acceptance один раз и владеют full-DTO S1 index, selection/expansion и retained HTML. main.mjs однократно применяет editor policy к текущему draft. result_controller.mjs владеет только presentation revision/leaf/surface и приватным image host. HTML и SVG читают одно принятое состояние; leaf не инициирует HTTP и не пересчитывает доменные факты. A006 уточнён прямым решением Owner20.10, см. execution section ниже.
2. Выбрать **revision-local connected measurement surface + guarded deep copy/install**. Renderer не получает живой image host или установленную SVG-копию. Snapshot скопирована глубоко и заморожена. Surface живёт до revoke, не до promise settlement. Current callbacks могут предложить новую копию; retired reference — только detached дерево.
3. Внутренний протокол: `renderer.update(readonlySnapshot, publish, revisionSurface): void|Promise<void>`, `renderer.dispose():void`; `publish(svg)` возвращает committed/revoked. Это внутренний protocol draft, не новый public API. На accepted B порядок R001-01: revoke→removeA→full-B index/once/reconcile→HTML/summaryB→guarded dispose retired once→guarded drawB.
4. Adapter проверяет passive tag/attr/value set, копирует SVG и повторно проверяет instance+revision+acceptance непосредственно перед синхронной install без await. Запрещены внешние/активные nodes/references, on*, interaction/focus, произвольное positioning и external CSS/ID access. Реализованный whitelist проверяет конечные bounded numeric values, размеры/viewBox, translate-only transform, literal font family/12/16 sizes и paint; ID/style/href/url/active/focus/event attributes отклоняются. Native controls содержат позитивные и негативные случаи. Это закрытый protocol для собственного leaf, не универсальный SVG sanitizer. Глобальный document доступен same-origin JS, поэтому дисциплина проверяется кодом/тестами; security sandbox не заявляется.
5. Factory/update sync throw и async rejection текущей lease → revoke failed lease, clear imagery, typed local `svg_unavailable(reason)`; HTML B доступен. Dispose fault retired leaf не мешает B. Stale rejection/late publish лишь диагностируются с retired token. HTML/controller fault идёт в действующий safe-read путь. Close idempotent. Surface cleanup и listeners замкнуты на lifecycle.
6. Drawing — [правила и измеримые predicates](https://github.com/ksenia-baranova/exact-orb-demo/blob/883b6d3a47f7113e44ede73c9ad16b40f15bbdaf/docs/project_management/change_plans/ui-chart-wheel/developer/column_renderer_design_v1.md): default source-longitude, measured C0, только конфликтующие point-метки в общей упорядоченной колонке, growing H при сохранении em16/12/gap2/anchor0,5; aux локальны. Для column domain отдельная row objective вместо старого annular chord return. Локальная aux1px проверка требует целого начального prefix; exact contact/closing derivative блокирует и смещение<1px. Глобальный geometry optimum не вводится.
7. Одна непрерывная линия к каждой moved метке; shared positive-length centerline запрещён. Разрешены crossing bridges; выделяется owner выбранной HTML-строки. Только точные source endpoints, без искусственной aspect-хорды для ☌. Семь типов/published categories/S1/source rows сохранены. Preview palette и численные размеры — часть технического предложения, не принятие всего эскиза Owner.

## Почему этот вариант

| Вариант | Достаточность / стоимость |
|---|---|
| Revision-local SVG + clone/install — рекомендован | Пассивному SVG не нужны live handlers/tab order. Измерения остаются native, live DOM принадлежит одному adapter.28 isolated controls включают настоящие SVG копии |
| Закрытые value frames D005 | Допустимая альтернатива, но нужен ещё полный SVG frame writer/measurement protocol. При passive SVG эта дополнительная generic система не нужна для принятого scope; экономия в часах без реализации не заявлена |
| Live host + token только после await | Недостаточно: old leaf пишет до settlement через сохранённый host, даже если completion позже отвергнута |
| AbortSignal без write guard | Может экономить работу, но не отзывает сохранённый DOM reference и не доказывает запрет late write. Не самостоятельная boundary |

## Проверка и последствия

[Native audit](evidence/column_full_composition_v1/run07-ports-audit.json):29/29 полных изученных SVG compositions,13 native controls,4 analytic controls. [Independent post-audit](evidence/column_full_composition_v1/run07-ports-post-audit.json):C0/order/row/leader clipping/no shared segments29/29,3 route controls. [Boundary](evidence/column_full_composition_v1/run07-ports/boundary.json):28/28, including current/stale positive/negative controls. Это feasibility evidence, не accepted ADR / production tests / full browser support.

Copy/install держит одновременно current measurement root и live clone, значит есть дополнительная память/копирование. Старые surfaces снимаются при revoke; retained old references не публикуются. Resize/font/selection дают новую revision, acceptance token не mint-ится. Native HTML focus находится вне SVG и сохраняется keyed patch; planet activation не вызывает focus/scroll.

Production реализация должна профилировать layout/copy, проверять полный attr whitelist, убирать чужие ID references, actual session/once causes, recovery/HTML44/focus/доставку ресурсов. Нет утверждения о допустимости всех возможных DTO или любых браузеров. Систематический dense failure не закрывается одним local error message.

**Принятие:** technical owner по DP-O-010/011/012 и назначенные reviewers проверяют exact опубликованную версию и узкую дельту критериев. Manager регистрирует итог и G3; до этого этот проект остаётся DRAFT. [План40–64ч](full_wheel_implementation_plan.md), [lifecycle sequence003](../../../../sequence_diagrams/ui/technical/003-passive-copy-install.puml), [drawing sequence004](../../../../sequence_diagrams/research/ui-chart-wheel/004-column-layout-revision.puml). Старые diagram001/002 сохраняют исторический D005 active-SVG предмет и не применяются к новому scope автоматически.

## D007 — фактическая ревизия по коду,20.10.2026

Прямое Owner-исключение Manager §§2.25–2.26 разрешило реализацию FW01…06 без ожидания прежних approvals; это не перевод этого ADR в ACCEPTED. InputSHA e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, новый CandidateSHA до отдельного commit отсутствует. Исторический feasibility baseline и ссылки выше сохранены. Фактический production protocol и ownership уточнены в §§1–5 этого draft.

Layout кешируется по полному DTO/width/fontRevision: selection-only не вызывает повторное размещение; дробная longitude при неизменной identity не теряется. Resize/fonts дают новую presentation revision, не новую acceptance. Измеряется и рисуется только внутри текущей connected surface; кеш старой detached surface не используется как host. Late owner failure после async rethrow тоже проверяет current lease перед clear/fatal. Regression RED воспроизвёл исчезновение SVG B; GREEN сохраняет B и не вызывает safe-read для retired A.

[A006 Owner source / policy](owner_decision_already_applied_2026-10-20.md): fresh GET, подтвердивший живую submitted B после already_applied, применяет changed-birth reset один раз; collapse только при draft=B. Cause отличен от own_committed, факты и summary только GET. [Accepted sequence005](../../../../sequence_diagrams/ui/technical/005-accepted-once-editor.puml).

[Фактические команды, native bbox/font/CTM, whole-path и ограничения](evidence/task_d007_runtime/README.md), [execution plan §8](full_wheel_implementation_plan.md#8-task-d-007--полный-локальный-результат-fw-0106). Исторические числа29/28 выше относятся только к исследованию, новые проверки отдельно. Нормативный registry/requirements/foreign artifacts не менялись; финальное принятие ADR и независимая проверка остаются у владельцев.

## Owner20.10 — номера домов, композиция и отдельный просмотр аспекта

Прямое Owner-поручение и уточнение «Да: две планеты и только их дома» изменяют только presentation/interaction scope; [execution §9](full_wheel_implementation_plan.md#9-task-d-007--исправления-композиции-по-owner2010), [пакет06](prompts/06-owner-composition-aspect-view.md). ADR остаётся DRAFT, нормативный реестр/чужие approvals не менялись.

Номера1…12 — source house.number, reference между последовательными source cusp_longitude; midpoint дуги — координата подписи, не вычисление принадлежности планеты дому. House labels участвуют в общей collision/auxiliary модели; неподвижные и moved references проверяются отдельно. Видимая полоска домов и degree ruler отделяют houses от zodiac. AspectR=max(0,27R,pointR−55), house label reference=aspectR+12; исходные point marks и em/gap predicates сохранены.

Уточнение предыдущего cache statement: **point-only** selection сохраняет geometry; **aspect reading mode** имеет новый key selectedAspectKey вместе с full DTO/width/fontRevision. Full-source S1 index остаётся полным до display subset, поэтому hidden/background duplicates по-прежнему блокируют адрес. В режиме аспекта рисуются только endpoints и опубликованные дома их point rows; при angle/null house ничего не вычисляется. Снятие возвращает исходную композицию.

HTML host имеет region label и программный focus вне пассивного SVG. Controller protocol update(snapshot,publish,currentSurface) не меняется. Явный aspect gesture фокусирует region и прокручивает к нему, current frame settlement может завершить scroll только при том же key и activeElement; delayed stale work и уход пользователя не вызывают jump. Escape/кнопка — возврат к живому source control. Recovery доступен при скрытых нерелевантных областях; resize/automatic accept не создают focus intent. [Sequence006](../../../../sequence_diagrams/ui/technical/006-aspect-reading-mode.puml), [native evidence](evidence/task_d007_composition_v2/README.md).


## Owner20.10 — внутренние ряды вместо колонки (текущая drawing-редакция)

[Прямое решение Owner](owner_decision_house_rows_2026-10-20.md) заменяет point-домен §2.6 и старые C0/frozen-point/PAV/column-leader правила: glyphs размещаются внутри своего опубликованного дома, допускается угловое смещение и несколько рядов. Старые секции — история, прежние certificates не объявляются evidence нового домена. Candidate ADR0042 остаётся DRAFT, нормативные ADR и чужие статусы не изменены.

Граница renderer не меняется: update(snapshot,publish,currentSurface), dispose; full DTO/width/fontRevision/aspect-view key; приватный live host и ревизионные guards. Source house только points[].house; доменные факты не выводятся из геометрии. Космограмма не получает дома. Полные bbox-компоненты glyph16/R12/контур лежат в source cusp wedge и вне house-number band; внешний радиус R−28. Измеренный R размещается радиально внутрь с gap2. Детерминированные кандидаты radial step4 CSS px / angle step1° плюс точный preferred offset; MRV search ≤50000 nodes на пробу. Начальный aspectInset66, затем86/106/146/206/306/506, aspectR≥0,22R: расширяется только внутренний drawing domain. Внутри одного занятого radial lane сохраняется source order; tie — canonical ID. Глобальный оптимум/неподвижность всех неконфликтных point labels больше не обещаются. Aux contact/routing остаётся отдельным прежним алгоритмом, point leaders отсутствуют.

Истинная отметка point на radius R−31 соответствует source longitude; линии аспектов — прежние source endpoints на aspectR, независимо от сдвига glyph. Никакой правки исходных чисел/house/типов/порядка таблиц нет. При capacity failure сохраняется typed local error + полный HTML, без смены дома или уменьшения шрифта. Произвольная плотность/экстремально узкий дом математически не гарантируются. [Sequence007](../../../../sequence_diagrams/ui/technical/007-internal-house-rows.puml), [native evidence35 + independent audit](evidence/task_d007_house_rows/README.md). Предыдущая sequence004 теперь историческая column-редакция, новая схема применима к текущему source.


## Owner20.10 — исправления004…008: размер кадра,легенда,векторные символы

[Пакет08](prompts/08-owner-bugfixes.md) и[sequence008](../../../../sequence_diagrams/ui/technical/008-viewport-legend-vectors.puml) фиксируют прямое поручение Owner «Исправить все баги и доработки». ADR остаётся DRAFT0042candidate,нормативный реестр/Manager gates/чужие approvals не менялись.

Drawing snapshot получает уже окончательную ширину режима chart_ready:main выбирает CSS page mode по принятому view **до** вызова drawingSnapshot из facts callback. Видимость heading/editor всё ещё определяется прежним accepted cause/modified draft,а не новым sizing rule. Это устраняет промежуточный snapshot узкой формы,который мог дать house-rows-capacity до следующего ResizeObserver. Main не инициирует новый HTTP/не меняет once/recovery semantics.

Normal image frame ограничен940px/100svh−160px,aspect frame940px/100svh−200px с местом под перенос toolbar. Нативные SVG CSS единицы1:1,без масштабирования font/viewBox. При height-only resize изменяется фактическая ширина host,прежний ResizeObserver создаёт новую ревизию при сохранённом selection. На≤1024px колесо идёт перед summary. Browser zoom — внешняя настройка:50% не сбрасывается и не компенсируется CSS x2.

Chiron/Pars Fortune/Selena получают локальные векторные stencils из указанного Owner Р3;их16-unit drawing system и реальные bounds измеряются тем же native getBBox,а contours/selection/R входят в прежние predicates. Текстовые font16/12 остаются для остальных symbols/R. Векторы не зависят от font fallback,source IDs/числа неизменны. Model definitions deep-frozen. Passive whitelist расширен только data-symbol;SVG активных элементов/handlers/CSS/сетевых ссылок не получает.

HTML legend и SVG читают один ASPECT_COLORS;7 color/type samples,☌ отдельно,solid/dashed отдельно. Full-view legend рядом с summary,aspect-view рядом с wheel при скрытой summary. Таблицы content-sized с согласованным middle alignment,44px controls,точная подпись «Южный узел». Это presentation delta Owner,derived facts/аспекты south_node не меняются. Evidence и ограничения — [пакет](evidence/task_d007_bugfixes/README.md).
