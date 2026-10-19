# DRAFT — Chart Renderer: владение записью, HTML и drawing feasibility v2

**Автор / подпись:** Codex / Developer, TASK-D-005, 19.10.2026. **DRAFT; архитектурное решение не принято.** Эта ревизия заменяет текущий проект D003 для следующего review; исходный проект неизменяемо доступен в TechnicalPackageSHA `d24a24e04be32d0522674735388e9d2ea3e65c93`. D003 report / run03 / старые manifests не переписываются. InputSHA `34f187aa81ddad7760089f54c1dc23d4d9e59d59`, AssignmentSHA `0046ac75bd6582089b68a640f98fa65468c0607a`, AnalystContractSHA **`2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`** (v3 + принятый S1). [Отчёт D005](task_d005_feasibility_report.md), [план](task_d005_implementation_plan.md), [Manager §2.20](../manager_artifact.md#220-регистрация-a007-и-точная-редакция-s1-во-входах-следующих-заданий).

Реестр [ADR](../../../../requirements/decisions/README.md) перепроверен на InputSHA: последний номер **0041**, 0042 отсутствует. **0042 остаётся кандидатом**, без резервирования / создания нормативного ADR. Действующие ADR-0029/0030/0032/0034/0040/0041 не изменяются. Перед будущим нормативным переносом номер проверяется снова.

## Контракт и ответственность

Только accepted ChartDTO и опубликованные факты. ResultController владеет immutable accepted envelope, once-acceptance policy, canonical selection, five/all aspects, независимыми houses, draft/submitted comparison и cause-specific focus. HTML-presenter и WheelPort читают одну новую snapshot. Leaf не владеет HTTP/session/build/recovery, не пересчитывает sign/house/aspect/category/orb/unknown-time stability. Координатор остаётся accept-owner; повторная публикация состояния не создаёт нового принятия.

HTML-presenter — явная часть controller-блока оценки: 6–10 часов общего forecast, из них D005 design 1–2 внутри 4–6 часов ADR/sequences. Здесь runtime S1 не реализован. `readChartFacts` не содержит longitude; геометрия читает исходный accepted DTO, а HTML сохраняет опубликованные текстовые факты.

## R001-01 — порядок и локальные отказы

Для принятой B последовательность обязательна:

1. Отозвать write/intent authority прежней instance **и revision**, включая progress/font callbacks, ещё до любого потенциально падающего leaf cleanup.
2. Удалить прежнее imagery A / запретить его повторное присоединение.
3. Проиндексировать полный B и применить once policy / reconcile; опубликовать HTML/summary **B** с актуальными фактами и source rows.
4. Вызвать синхронный idempotent `dispose()` retired instance внутри guard; fault диагностируется с retired token, не возвращает A и не блокирует draw B.
5. Создать новую lease / вызвать mount/update B; принимать только её допустимые frames/intents. HTML B остаётся доступен при leaf fault.

При замене только presentation revision внутри той же instance прежняя revision отзывается; HTML обновляется keyed patch, dispose instance не требуется. При полном закрытии controller отзыв и удаление выполняются однократно; повторный dispose wrapper не вызывает leaf второй раз. Async-dispose не входит в предлагаемый контракт `dispose(): void`; его возможное добавление потребовало бы отдельной проверки.

Factory throw, update sync throw и async rejection **актуальной lease** дают typed local `svg_unavailable(reason)` и пустой image host / доступный HTML B. Это не coordinator `requiresReconciliation` и не успешное новое HTTP-чтение. Ошибка HTML/controller остаётся unexpected и следует действующему safe-read/fallback, не подавляется leaf-guard. Stale rejection — diagnostic retired revision, не ошибка новой карты; новый B warning не перезаписывается.

## R001-02/03 — write authority до settlement

Одной проверки generation после `await update()` недостаточно: старый renderer может записать A, пока его promise ещё pending. Рекомендуется **revision-scoped publish gateway с владением DOM у presentation adapter**. Leaf не получает живой host, DOM nodes, mutable указатель `this.currentHost` или произвольную функцию записи в него. Он предлагает копируемые value frames и canonical keys; adapter измеряет шрифты по узкому read-only measurement port и возвращает только числа. Механизм не требует AbortSignal и не объявляет его уже принятым решением.

```ts
// DRAFT internal presentation protocol, не HTTP/API schema.
type RevisionToken = Readonly<{instance: number; revision: number; acceptanceSeq: number}>;
type PublishResult = {kind: "committed"} | {kind: "revoked"};
interface RevisionSink {
  publish(frame: ReadonlyWheelFrame): PublishResult;
}
interface WheelRenderer {
  update(snapshot: ReadonlyPresentationSnapshot, sink: RevisionSink): void | Promise<void>;
  dispose(): void;
}
type DrawOutcome = {kind: "rendered" | "svg_unavailable" | "revoked";
                    token: RevisionToken; reason?: string};
```

`ReadonlyWheelFrame` — закрытые value descriptions допустимых рисунков / attributes / canonical target keys, без DOM/callback/on* payload. Adapter копирует/проверяет frame до применения, повторно проверяет текущий token **непосредственно перед синхронной DOM-транзакцией**, не делает `await` внутри patch, сохраняет keyed controls. Ошибка writer — controller fault, не произвольный leaf success. Мутация автором ранее переданного object после publish не меняет уже опубликованный DOM. Binding native intent принадлежит adapter: live node/capability, текущий token и существующий key проверяются до передачи canonical intent в controller. Detached old callback не активирует новую selection.

Это дисциплина внутренних компонентов в одном origin, **не sandbox для недоверенного JavaScript**. Leaf, который сам обращается к глобальному `document`, нарушает контракт; future implementation/review должны проверить отсутствие обходов gateway. Ограниченный [boundary harness](evidence/task_d005_feasibility/boundary.mjs) проверяет принцип на копируемом frame кнопки, не реализует полный SVG frame writer. Альтернатива — уникальная detached render surface с неизменным per-revision владельцем и копированием в live DOM; простое переназначение общей `host` после `await` проблему не решает. Abort/cancel может экономить работу, но не заменяет write guard и revoke.

## R001-04 — живой HTML и focus

Point-control key — canonical point ID; unique aspect-control key — unordered endpoints + published type. В пределах accepted snapshot каждая source occurrence имеет собственную identity строки; ordinal не становится меж-DТО аспектным ключом. При обычных select/filter/reveal/resize сохраняется **тот же connected DOM node**, его handlers и tab position. Не делать `replaceChildren()` контейнера таблицы или повторный append уже правильно стоящего focused control. Меняются текст / visibility остальных строк и attributes; selection policy не зависит от layout.

Planet activation не вызывает `focus()`/scroll, активный живой point остаётся доступным. Unique aspect toggle сохраняет активную строку, обычное five/all и независимое houses. При внешнем accepted reconcile сохранившийся key сначала patch-ится без пересоздания. Если пересоздание неизбежно, это **не retention**: восстановить тот же доступный key без scroll можно только при разрешённой external-current cause и действительно прежнем active target. При удалении/disable key применить принятую H5 цепочку доступных live controls (инициатор → Edit → recovery → enabled birth field), проверив connected/visible/enabled; скрытый/disabled элемент не focus target. При collapse сворачиваемого active поля focus уходит в существующий Edit **до** hide; recovery controls остаются вне hidden fields и сохраняют действующие gates. Полный mounted/cross-platform порядок ещё предстоит проверить после G3.

Новый run04 подтвердил retained point/row, отличил detached same-key clone, проверил cause-specific restoration model, resize focused SVG target и последующее native действие. В отдельных screenshot чёрная рамка вокруг ☌/категории — **focus indicator всей группы**, не selected contour; усиленный selected contour остаётся только у символа.

## S1 — полный accepted DTO до фильтров

S1 уже принят; ожидание A007 / повторный Owner-выбор удалены. При accepted B построить индекс `unordered endpoints + published type → source occurrences` **по всем исходным строкам**, до category eligibility / five-all / planet filter. Category/orb не входят в разрешение ambiguity. HTML сохраняет каждую строку, направление from/to, DTO order, category/orb и значения; одинаковые строки не дедуплицируются.

0 matches = absent; 1 = unique с новыми фактами / направлением; >1 = ambiguous. Только ambiguous группа лишена линии/☌ и aspect-select, получает локальный доступный warning без hover/раскрытия all; это отдельный исход от отказа renderer, не исчезновение всей карты. Unique reverse / другой type / другая пара / присутствующий point продолжают работать. Background unique сохраняет выбор двух концов без линии.

Unique→accepted ambiguous снимает только aspect, возвращает общий список с прежним five/all, сохраняет houses/draft и не возвращает старый planet filter. Выбранный присутствующий point сохраняется со всеми source rows без лимита пяти. Failed/rejected read не индексируется и не снимает выбор / не создаёт неподтверждённый warning. После accepted ambiguity следующий unique возвращает возможность выбора без автоматического восстановления снятого selection. Реальные F5 U/R/D/V/M/L/T/P — future test mapping, **не выполненный runtime D005**.

## Accepted cause и отдельный A006

В accept-owner внутренний монотонный acceptanceSeq и attemptId + immutable submitted snapshot / previous confirmed birth / accepted cause. `source=build`, identity и очередной publish не являются once token. Own committed changed-birth reset применяется один раз; collapse только при равенстве текущего draft submitted snapshot, включая edit→revert. Automatic current обновляет факты/reconcile и сохраняет expansion/draft, снимая лишь absent / S1 ambiguous selection.

Принятый A005 @ `4057d6ed37b24e082a2a4089eb7104da80d17ee5`: fresh matched recovery активного pending goal может подтвердить **результат локального намерения** один раз на attempt, без заявления об авторе серверного commit. Ветка больше не ожидает общего Owner-ответа. `target_confirmed_already_applied` / R001-05 остаётся отдельным TASK-A-006; его новая политика здесь не выдумывается и независимая геометрия не блокируется. До опубликованного адресного решения эта ветвь явно условная, не runtime PASS.

## Drawing v2: результат и предел модели

[Заранее зафиксированный spec](evidence/task_d005_feasibility/model_spec.json): frames720/448/328, viewport1440/768/360, радиусы point0,40S / marker0,22S / angle0,11S; measured component circumdisks → order-preserving projection128 sweeps, angle labels в независимой полосе. C0 фиксируется по visual union до размещения; hit overlap не расширяет C0. True anchors / endpoints / DTO не меняются. Это другая конструкция, без fixed16°/40°.

Явное отличие от D004: новый experimental annular domain и **прямой chord return** `P+u(A-P)`, Euclidean CSS displacement / min(1,d), а не старая дуга фиксированного радиуса. Независимый Fraction verifier проверяет всю prefix-траекторию, не вызывает placement. Это названная гипотеза, не молчаливая замена принятого критерия. Пороги **0,5 / 2 / 1 / 16 / 12 / 44** сохранены. Em16/12, ink, contour, focus, effective hit и native delivery записаны отдельно.

F использует centered Q44; E смещает Q на12 CSS px наружу в том же glyph-control, оставляя native hit rectangles самого glyph и один key/tab stop/action. Доступность всех glyphs этим ещё не доказана: occlusion/hit failures отклоняют эту конструкцию. Отдельного off-glyph control / дополнительного действия не введено; поэтому semantic stop не потребовался. При будущем предложении такого нового действия остановить только E-browser и адресно передать различающий пример Analyst/Owner.

**Кандидат v2 отклоняется для реализации:** 14/24 клеток проходят только измеренную component geometry; 241/438 target occurrences имеют условный exact rectangle certificate, 238/2190 native probes не подтвердили owner/outcome; 256 moved-групп с допустимыми начальными visual constraints имеют положительный полный visual return-prefix (LOCAL_TIGHT_FAIL). Из них148 принадлежат клеткам с валидным полным измеренным component union; это не256 whole-feasible карт и не H/Q certificate движения. Sparse328 без visual конфликта демонстрирует отдельный Q44 провал; hit не разрешает раздвинуть эти glyphs. Нет whole drawing PASS, глобальной невозможности или исключительности E. Zodiac/sign text и полная palette не моделировались; успешные partial клетки не доказывают всю drawing feasibility. SVG/font measurements из run04-delivery подтверждают фактические bounds отдельно от reused run03 inputs.

## Evidence и условия дальнейшего решения

[Report](task_d005_feasibility_report.md) / [findings](task_d005_findings.md) / [browser audit](evidence/task_d005_feasibility/browser_audit.json) / [sequences001](sequence_diagrams/ui/001-result-renderer-lifecycle.puml) / [002](sequence_diagrams/ui/002-acceptance-selection-focus.puml). Boundary12 и browser/control12 — isolated observations; 438 keyboard traces не заменяют production acceptance. Research trace не добавляет новых server logs и не расширяет действующие ADR logging payload.

Рекомендация для DP-O-010 — рассмотреть guarded value-frame port / retained HTML с указанными ограничениями на R002. DP-O-011/012 — текущий drawing candidate **не принимать**; следующий новый spec/радиус/домен/Q-механизм требует явного решения о следующем bounded work item, а semantic изменение — Analyst/Owner. DP-O-013 — применить принятый S1 при future implementation. Нормативные DP/gates этим текстом не изменены.

D005 16–24 часа согласован внутри условного forecast9–14 чд; фактический остаток D003 неизвестен. Эксперимент остановлен по достаточности evidence, нового расхода не запрошено. Полная реализация9–14 **не подтверждена**, пока нет принятого drawing-кандидата; из elapsed нельзя выводить остаток или бюджет следующего исследования. Следом после отдельной публикации — T007 / R002 на одном закреплённом Manager TechnicalPackageV2SHA; далее адресное решение о geometry и отдельный G3. Номер0042 перепроверить при нормативном переносе, DRAFT не публиковать как принятый ADR.
