> **Текущий допуск исполнения D005:** Owner согласовал assessment v1 / 16–24 часа / experiment ≤12 часов внутри и срок до конца третьего рабочего дня. **STARTED 19.10.2026 00:15:25 MSK; передача до конца 21.10.2026 (Europe/Moscow)**, день старта — день 1. InputSHA `34f187aa81ddad7760089f54c1dc23d4d9e59d59`, AssignmentSHA `0046ac75bd6582089b68a640f98fa65468c0607a`. Источник / журнал — [execution start](evidence/task_d005_feasibility/execution_start.json), подпись Developer — в [handoff](../developer_artifact.md#task-d-005--started-после-согласования-owner). Ниже сохранена оценка assessment v1 как исторический snapshot до допуска; её условия начала выполнены этим явным поручением. Production по-прежнему требует отдельного G3.

# TASK-D-005 — оценка и план drawing feasibility v2

**Автор / подпись:** Codex / Developer. **Редакция:** assessment v1, DRAFT до согласования исполнения. Сейчас поручены только оценка, план и собственный handoff. **STARTED D005 не объявлен; spike, run04 и ревизия ADR / sequences не выполнялись.** [Постановка Manager](../manager/prompts/task-d-005-drawing-feasibility-v2.md), [§2.20](../manager_artifact.md#220-регистрация-a007-и-точная-редакция-s1-во-входах-следующих-заданий).

**Собственная оценка всего D005: 16–24 рабочих часа / 2–3 чд** при 8 часах в чд. Confidence **средняя** для ограниченного пакета с корректным положительным либо отрицательным результатом; **ниже средней** для нахождения подходящего drawing / Q44 на 328. Эксперимент **≤12 часов внутри**, в том числе browser + его harness **≤4 часов**. Пакет — **до конца 3-го рабочего дня от отдельного STARTED D005**. Это предложение Developer, ещё не согласованный бюджет / срок и не заимствованный ориентир Reviewer 1,25–2,25 чд.

## 1. Git baseline и точные предметы

| Поле | Значение / происхождение |
|---|---|
| Worktree / branch | `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered` / `dev/ui-chart-wheel` |
| Исходный HEAD | `d24a24e04be32d0522674735388e9d2ea3e65c93` |
| Фактический HEAD после fetch / ff | **`0046ac75bd6582089b68a640f98fa65468c0607a`**; `git fetch origin change/ui-chart-wheel`, `git merge --ff-only FETCH_HEAD`, exit 0 |
| AssignmentSHA текущей редакции D005 | **`0046ac75bd6582089b68a640f98fa65468c0607a`**; последняя опубликованная ревизия промта с §2.20. Совпадает с фактическим HEAD сейчас, но остаётся отдельным полем |
| История постановки | Общий InputSHA §2.18 `072fc291f8b0db24aaa34ad7a29abc96b472162a`; первое назначение D005 `0e590fa23d6c3f31d59a59cd0f7cb5be3509d160`; не подменяют текущую редакцию |
| AnalystContractSHA (v3 + S1) | **`2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`**, [requirements](../analyst/requirements.md), [scenarios / F5 S1](../analyst/scenarios.md#f5-s1), behavioral [001](../analyst/sequence_diagrams/ui/001-chart-presentation.puml) / [002](../analyst/sequence_diagrams/ui/002-wheel-table-selection.puml) / [003](../analyst/sequence_diagrams/ui/003-edit-and-recovery.puml). A007 DONE / APPROVED по Manager §2.20 |
| Owner S1 / исходный нормативный baseline | S1 — `b4418ae1c531ff4726be2769422056d8b059b96d`, §2.19 / DP-O-013. MainBaseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`; Analyst v3 `2634b224894b1046113557bfe241f0a5f2d46f8c` сохранён как история |
| D003 / criteria | TechnicalPackageSHA `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; [report](task_d003_research_report.md), [run03](evidence/task_d003_research/run03/browser_matrix.json) — неизменные исходные данные |
| Принятые reviews | A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17`, [review](../tester/task_t004_review.md). A005 уже конкретизировал active pending-goal recovery; этот вопрос заново Owner не задаётся |
| Вход R001 r2 | [Manager-сводка](../manager/review_inputs/task-r-001-r2-summary.md), опубликована в `0e590fa23d6c3f31d59a59cd0f7cb5be3509d160`, сохранена в AssignmentSHA. **Reviewer OutputSHA отсутствует**; исходные reviewer scripts/logs не получены. Reported числа упаковки и проверки не являются моими измерениями / oracle |

До обновления дерево и index были чистыми; после fast-forward также чистые. Несвязанных изменений не обнаружено, reset / force / clean / stash / staging не применялись. Новые опубликованные изменения — reviews, Manager-поручения и принятая S1-дельта; `src/`, `tests/`, нормативные requirements / ADR / общие sequences / process не менялись относительно d24a24e. Единственный новый содержательный контракт для проектирования — pinned S1; чужие материалы читались только из fetched Git. При следующем старте новый HEAD сверяется отдельно: существенный diff входов передаётся Manager с влиянием, pinned предметы не заменяются автоматически.

## 2. Диапазон, допущения, срок и timebox

| Блок D005 | Часы | Состав и граница |
|---|---|---|
| Предстартовая подготовка / формализация входов и новых моделей | 3–4 | Эта оценка входит в подготовку D005, не оплачивается второй раз отдельным слотом. После допуска — точный frame/path/clip/font/C0 protocol, traceability, source/spec hashes; без нового общего согласования критериев |
| Аналитическое сравнение F/E | 3–4 | Certificates / контрпримеры по объявленной геометрии; полный fixed+movable verifier, Q44, prefix-return. Не exhaustive global solver |
| Изолированный run04 и browser harness | 3–4 | Подготовка harness / controlled data, font/bounds/native owner/keyboard/resize/lifecycle controls и screenshots включены, а не спрятаны за лимитом |
| DRAFT ADR / technical sequences: R001-01…04 и S1 | 4–6 | Порядок lifecycle, write ownership async revision, sync/async failure, retained HTML controls; **1–2 часа внутри этого блока — дизайн HTML-presenter / S1**, не runtime F5 |
| Evidence / итоговый план и forecast / signed handoff | 3–6 | Связи критерий→данные→actual→вывод, ограничения и файлы; один ограниченный авторский ответ на конкретные review-замечания включён. Новое исследование не называется текстовым ответом |
| **Всего** | **16–24** | **2–3 чд**, оценка полного этапа, не восстановленный фактический остаток |

**Единый experiment timebox ≤12 часов** включает первые три блока: подготовку / спецификацию эксперимента, аналитические проверки, данные, harness и реальные измерения. Вложенные пределы: аналитический проход ≤4 часов, browser+harness ≤4 часов; эти интервалы входят в 12, не прибавляются к ним. Ранее выполненная подготовка оценки учитывается один раз; при STARTED фиксируется доступный фактический журнал D005 без выдумывания прежнего timesheet. До допуска работает только документальная подготовка, экспериментальный счётчик не запускается. Это новый предлагаемый лимит D005, **не расширение исторического лимита D003 ≤6 часов**.

Срок полного результата — до конца **третьего рабочего дня от отдельного STARTED** при одном Developer и 8-часовом дне; это верхний календарный envelope 24 часов, не четвёртый дополнительный чд. Абсолютную дату / рабочий календарь Owner ещё не задавал. **Target полного исполнения за один рабочий день не подтверждаю**: 16–24 часов требуют 2–3 чд. Предстартовый ответ на текущий запрос подготовлен сейчас; в ходе выполнения статус / первый конкретный риск передаётся не позднее первого рабочего дня. После точной передачи T007/R002 авторский первый ответ / triage возможен за один рабочий день; готовность и труд самих reviewers подтверждают они, не Developer.

Эскалация — Manager → Owner через **+1 рабочий день просрочки**, заместитель не назначен. В ходе работы о прогнозе выхода за scope / 12 часов эксперимента / 24 часа всего / срок сообщить Manager **до** превышения с выполненными данными и вариантами: передать ограниченный пакет; сузить ещё не выполненный вариант явным решением; согласовать новый расход. Молчание не approval. Ожидание ответа по E / A006 / внешнему reviewer пакету не записывается как Developer effort и не служит разрешением продлить timebox.

### Предпосылки и исключения

- Один Developer, один ограниченный цикл F/E без бесконечного подбора; корректный контрпример конкретной construction допустим как результат. Positive feasibility всех 12 базовых клеток не обещается заранее. Если факты требуют иной архитектуры / scope — явное влияние Manager.
- Native ES modules / Python standard library и уже установленный Chrome / bundled Playwright. Read-only проверено наличие Chrome `155.0.8059.40` и Playwright; браузер сейчас не запускался. При исполнении записываются фактические версии, resolved fonts, DPR/zoom, CSS M и viewport. Нет автоматической установки solver/scipy/шрифтов/новых app dependencies.
- Источники доступны в опубликованном Git. Публикация исходного R001 r2 позволит сверить его provenance отдельно; сейчас достаточно разрешённой Manager-сводки. Новая отличающаяся рецензия требует impact check, а не молчаливой подмены предмета.
- A007 уже принят; S1 не требует повторного approval. A006 (delivered already_applied) — отдельная условная policy-ветвь; её отсутствие не блокирует F/E / S1-дизайн / R001-01…04. A005 fresh matched active pending-goal применяется по принятой версии, не переоткрывается.
- Исключены production code / S1 implementation, runtime F5 acceptance, engine/API/golden/current requirements, новые зависимости, deployment/HTTPS, полный product regression, cross-platform/touch/accessibility certification, непрерывная глобальная оптимальность, принятие fallback, финальная нормативная публикация ADR. Исполнение D005 не заменяет G3.

## 3. Включение в 9–14 чд, HTML-presenter и отсутствие двойного счёта

Действующий общий прогноз **9–14 чд / 72–112 часов** — условное предложение, Owner его пока не утвердил. D005 **включается в его блоки**, а не добавляется сверху и не прибавляется к историческим 8–12. Согласование отдельного D005 не означает approval всей реализации.

| Родительский блок прогноза | Ёмкость, часы | Предлагаемая доля D005 |
|---|---|---|
| D003 technical preparation целиком | 20–28 | **0 новых часов D005.** D004 и старый SVG-spike уже внутри D003; его результат / бюджет / elapsed не переписываются |
| Drawing / измеренное размещение / native hit / Developer geometry checks | 28–44 | **9–12 часов D005**: подготовка моделей, аналитика F/E и run04. Это часть drawing, не повторное начисление D003 |
| Controller / identity / accepted cause / HTML-presenter / focus / recovery и automated tests | 16–24 | **4–6 часов D005**: проект границы / ADR / sequences, включая **1–2 часа HTML-presenter/S1 design** |
| Integration / regression / technical docs / Developer handoff | 8–16 | **3–6 часов D005**: новый evidence / forecast / передача и один ограниченный авторский ответ |
| **Общий прогноз** | **72–112** | **D005 16–24 уже внутри**, а не 72–112 +16–24 |

**Явный подблок HTML-presenter — 6–10 часов внутри controller 16–24**, включая D005 design 1–2 часа. Он включает проектирование и будущую реализацию retained keyed points/unique-aspect controls, source-row-preserving HTML для duplicates, локальные S1 warnings, five/all/planet-filter и cause-specific live focus с целевыми tests. Остальная реализация этого подблока выполняется только после G3; её нельзя считать уже выполненной D005 или дополнительно прибавлять к controller / drawing. Это оценочное распределение, не обещание runtime S1 в research.

Таблица показывает плановое размещение работ, **не доступный денежный резерв и не фактический остаток**. Достоверный суммарный труд D003 / прежней подготовки неизвестен: 0,6023 часа старого spike и 1,9473 часа одного сеанса не дают остаток 20–28 и не вычитаются из него. Не объявляю доступными «20–28 минус elapsed» либо произвольный запас на D005. Если будущая реализация не поместится в parent-блок после новых фактов, нужна новая общая переоценка Owner через Manager; автоматическое увеличение 9–14 сейчас не предлагается.

## 4. План ревизии ADR / sequences — только после допуска

Ни [существующий DRAFT ADR](drawing_adr_draft.md), ни technical sequences [001](sequence_diagrams/ui/001-result-renderer-lifecycle.puml) / [002](sequence_diagrams/ui/002-acceptance-selection-focus.puml) в этой подготовке не изменяются. Следующая ревизия получает D005-авторство / pinned sources, сохраняет ссылку на d24a24e, не переписывает report / run03 / manifests D003. Номер будущего нормативного ADR перепроверяется по [реестру](../../../../requirements/decisions/README.md), не резервируется оценкой.

| Review / предмет | Запланированное исправление и инвариант | Чувствительные controls / evidence после допуска |
|---|---|---|
| **R001-01**; REQ-WHEEL-10/11, AS-WHEEL-24, DP-O-010 | Единственный порядок: **revoke → удаление A imagery из live DOM → HTML/summary B → guarded dispose A → guarded draw B**. Controller владеет live host; cleanup callback не должен блокировать B. Исправить ADR и sequence001, где dispose ещё стоит перед HTML | A→B, dispose throw / pending dispose, повтор dispose; HTML B виден до cleanup, SVG A отсутствует, late A callback отвергнут. Парный исправный dispose + live action B доказывает достижение пути. Failure внутри leaf локален, общий HTML/controller сбой сохраняет baseline reconciliation |
| **R001-02**; same-instance async revision | Проверка generation/revision только после Promise недостаточна: старый renderer может записать в DOM раньше settlement. Сравнить отмену и эквивалентную **изоляцию write-authority**: per-revision staging host / controller-only commit в current live host. Все writes / callbacks должны иметь действующую revision-capability | Управляемый deferred старой revision пытается писать после принятия B: live B не меняется. Негативный naive settlement-only guard действительно портит DOM; актуальная revision успешно пишет / активируется. Cancellation/AbortSignal — вариант, не уже принятый обязательный интерфейс |
| **R001-03**; sync/async local failure | Один явный local outcome для sync throw / async reject текущей leaf; stale reject не заменяет B ошибкой A. Guarded dispose имеет отдельную диагностируемую ветвь и не возвращает stale imagery. Уточнить интерфейс / sequence001 вместе с ownership write | Sync factory/update fault; deferred async rejection; stale rejection; dispose fault; все дополнены успешным paint на тех же B. Не вызывать общий requiresReconciliation от ожидаемого leaf fault и не ослаблять действующие restart/Retry-After gates. Полная mounted production связь остаётся за G3 |
| **R001-04**; HTML-presenter | Keyed retained controls требуются и в HTML. Point key сохраняет тот же DOM node при выборе / resize. Unique aspect control сохраняется при обычном toggle. Source rows duplicates не дедуплицируются; ordinal строки — identity только внутри accepted snapshot, не стабильный aspect key между DTO | F1 unique: keyboard point/row → filter/reveal/toggle, независимые houses, native pointer + next keyboard action, connected/visible focus и отсутствие запрещённых focus/scroll. При новом DTO удалённый control получает только разрешённую cause-policy; recreate с тем же key не считается сохранённым node |

В sequence002 предусмотреть cardinality до reconcile / filters и принятый S1. Убрать устаревшее «ambiguity ждёт Owner» только при будущей ревизии по закреплённому контракту. Active pending-goal recovery по A005 уточняется без доказательства server-producer provenance. **R001-05 / already_applied не решается Developer**: ссылка на опубликованный A006 либо явная условная ветвь, не блокирующая независимый результат D005.

## 5. F/E и certificates для 720 / 448 / 328

Первый будущий артефакт эксперимента — versioned model/input record **до первого расчёта / измерения конкретного опыта**. SVG CSS frames **720 / 448 / 328**, а не скрытое повторение 720/720/328 из D003. Предлагаемая стендовая связь viewport1440/768/360 → frame720/448/328 — исследовательская гипотеза, не новый продуктовый breakpoint. C=(S/2,S/2), SVG viewport / overflow clips, полный M, фактический font/fallback и em, allowed domains/paths/radii, angle-label constraints и paint order фиксируются явно. Точные радиусы выбираются после допуска и фиксируются до actual, не запрашивают нового общего предстартового review.

- **F — радиусы / новая order-preserving construction.** Исследовать новый default radius по рамке и допустимые lanes/path только для исходно конфликтующих label-групп; отдельную конструкцию angle labels с неподвижными true anchors. Это новая техническая модель, **не доработка fixed-ring 16°/40°**. Изменения относительно G6 фиксируются явно: откуда берётся default, какие objects movable, какие radial/tangential пути разрешены и как проверяется возврат. Смена номинального radius между объявленными F-моделями не является скрытым смещением неконфликтующих labels внутри одной модели.
- **E — effective target geometry.** Сравнить Q44 в H_i с actual clip / topmost owner / handler outcome. Q не ограничивается автоматически визуальным annulus. Зафиксировать native shapes, paint order / исключаемые overlaps и полный containment; bbox и несколько кликов не certificate. Одно hit-overlap не расширяет visual C0 и не разрешает двигать неконфликтующие glyphs.
- Default C0 определяется **до placement из полного visual union** normal/selected/focused с point/R, ☌/подписью/контуром, angle labels и фиксированными препятствиями. Для новой angle-label модели отдельно объявить movable/frozen set; не вычислять C0 задним числом после удачного разноса. Проверить movable↔movable, movable↔fixed и fixed↔fixed. True anchors / aspect endpoints / DTO факты не меняются.
- Сохраняются 0,5 / 2 / 1 / 16 / 12 / 44. Независимая формула true anchor с published ASC либо cosmogram0; cyclic order / seam0 / canonical tie; leader iff ненулевой displacement. При новой path-модели заранее задать непрерывный admissible return path к default и пробу min(1,d), включая d<1. Один endpoint/grid optimum не доказывает допустимость всего prefix / continuous local minimality; fractional witness может отвергнуть кандидат.

| Базовая matrix | Запланированные независимые predicates | Что допускается заключить |
|---|---|---|
| sparse/F1/F3/F3-max × 720/448/328: **12 базовых клеток**, F и E сравниваются отдельными вариантами | Все IDs / R / опубликованные пары / category text, close angles, bounds / gap / clip, C0/frozen set, cyclic order / leaders, Q containment, local return. F3 точно наследует неназванные F1 fields; F3-max сохраняет DSC/IC напротив ASC/MC. Controlled UI data не становится golden | Полный constructive witness с независимой проверкой — feasibility данной модели / клетки. Успешная packing раскладка даёт **lower bound**, не максимум. Одна неудача эвристики — только candidate FAIL |
| Аналитический certificate | Исходные координаты / bounds / допущения, точные прямоугольные inequalities; для кривых — объявленный path и error bounds / prefix proof. Verifier не вызывает placement helper | Невозможность только в явно объявленной модели и лишь при соответствующем аналитическом bound. Дискретный optimum / таймлимит / MILP report не является continuous upper bound |
| Контрпример | Минимальная конкретная fixture / frame / model / нарушенная inequality, independent positive control и альтернативный допустимый случай | Можно отвергнуть construction или record. Нельзя из этого заключать невозможность продукта / единственность E / принятие fallback |
| Недостаточно доказательства | Неизвестные font bounds, interval у границы, unsupported clip, непройденный prefix, исчерпанный timebox | **UNPROVEN / NOT RUN** и точная причина; не PASS и не утверждение недостижимости всей рамки |

**E semantic stop:** если E сохраняет существующий видимый target / canonical action и меняет только его подтверждаемую native geometry, это обычная техническая гипотеза исследования. Если вместо выбора glyph / линии / ☌ требуется новый отдельный off-glyph control, дополнительный шаг или меняется предусмотренное keyboard/selection поведение — записать различающий action/coordinate пример и остановить **только browser-часть E** до адресного Analyst/Owner решения. Аналитическое сравнение E, F и независимые boundary/HTML части продолжаются в том же timebox. S1 при этом не переоткрывается. При отсутствии ответа к сроку E явно остаётся NOT RUN, без молчаливого внедрения нового поведения.

После аналитического прохода — bounded **run04** в новом `developer/evidence/task_d005_feasibility/`: числовые records, native requested/delivered coordinates, event.target/composed path/key/outcome, actual font / bbox / M / clip, keyboard order/live focus, resize на сфокусированном target и последующая активация, screenshots / hash / commands. Sparse/default и independent positive-negative controls обязательны. Уже измеренный run03 / авторские T004 replay не переписываются и не называются run04. **Runtime F5 / production S1 в run04 не включаются**; retained HTML native controls используют обычный unique F1 и проверяют R001-04 в isolated harness.

### Stop conditions

1. Достаточный сравнительный пакет: по рамкам/вариантам есть независимые certificates либо конкретные candidate/model контрпримеры с корректным пределом, обязательные позитивные controls и явно оставленное UNPROVEN; продолжать подбор ради green verdict не требуется.
2. При достижении ≤4 часов аналитики / ≤4 часов browser или общего ≤12 часов эксперимента остановить соответствующий поиск / run. Непокрытые клетки помечаются NOT RUN / UNPROVEN; остаток общего 16–24 используется для честного ADR/report/handoff, а не для скрытого продления spike.
3. Новая гипотеза получает новый заранее зафиксированный spec/run ID. Не менять параметры после actual под тот же вход. Если недостаточность evidence ставит под угрозу обещанный состав результата — сообщить Manager до лимита, без объявления недостижимости по исчерпанному поиску.
4. Semantic stop E локален. Отсутствующий A006 или исходный R001 OutputSHA не останавливает независимые части; изменившиеся опубликованные входы оцениваются адресно.

## 6. S1 — принятое ограничение проектирования

Источник — AnalystContractSHA2736e28, REQ-WHEEL-04/07/08/10 и REQ-UI-06; AS-WHEEL-28/29/30 / F5 U/R/D/V/M/L/T/P. В D005 это **документальный дизайн / future-test mapping**, не реализация S1 или исполнение F5 runtime.

| Предмет | Планируемый invariant / expected будущей реализации |
|---|---|
| Cardinality | При принятии DTO сохранить полный source rows array и индекс `unordered endpoints + published type → source row ordinals`. Построить его **до** graphical category eligibility, five/all и planet-filter. Одинаковые source rows считаются дважды; category/orb не разделяют key |
| HTML-presenter | Каждая source row сохраняется с from/to/category/orb и DTO order. Five/all считает строки, не уникальные groups. Например duplicate на source rows1/6 должен блокировать affected key и показывать warning уже в первых пяти; скрытая шестая строка не делает первую unique. Planet-filter показывает все исходные строки без лимита пяти |
| Locality | Только >1 matches group лишена линии/☌ и aspect-select; accessible warning называет пару/type/несколько записей/сохранность строк и локальное ограничение. Warning доступен без hover и без раскрытия всех строк, отличим от leaf renderer fault; не скрывает карту и корректные пары, не создаёт HTTP/build |
| Попытка выбрать ambiguous row | Нет aspect activation; присутствующий point либо другой unique aspect, expansion/draft/focus policy сохраняются. Числа не «исправляются», first/best/exact match не выбирается |
| Accepted reconcile | 0=absent;1=тот же адрес с новыми фактами/направлением;>1=S1. Unique→accepted ambiguous снимает только выбранный aspect, возвращает общий список с прежним five/all, сохраняет houses expansion/draft, не возвращает старый planet-filter. Присутствующий selected point остаётся и показывает все source rows |
| Непринятые ответы | Failed / rejected read не меняет индекс последнего accepted DTO, не снимает выбор и не вводит неподтверждённый warning. Уже accepted ambiguity после failed read сохраняет свой warning / строки |
| Unaffected / восстановление | U и один reverse R unique; другой type T — другой key. D/V/M включая background всё ещё >1; L блокирует только эту линию. Unique background сохраняет HTML select и два конца. Другая unique пара / point работают. Следующий accepted unique восстанавливает возможность выбора, но не восстанавливает снятый selection автоматически. Натал / cosmogram без синтеза углов / домов |

В будущей sequence002 отметить индексирование / eligibility / warning и unaffected-positive controls до reconcile. Для HTML rows различать identity отображаемого source occurrence в пределах snapshot и canonical selection address; index/row ordinal не используется как меж-DТО аспектный ключ. Повторные публикации не должны пересоздавать активный point-control ради новой S1-проверки. Конкретный DOM / ARIA-механизм будет обоснован в ADR после допуска; screen-reader acceptance не приписывается документам.

## 7. Work items, покрытие и состав передачи

Исполняемое назначение — [Manager prompt @ AssignmentSHA0046ac7](../manager/prompts/task-d-005-drawing-feasibility-v2.md). До Owner-допуска это план, не разрешение выполнить перечисленные карточки.

| Work item | Подход / основание | Существующее покрытие / пробел и completion evidence |
|---|---|---|
| D005-01 frame/F/E certificates, DP-O-011/012/014; REQ-WHEEL-02/05/06/09/10, AS-WHEEL-03/07…10/16/25 | Аналитические certificates до browser; известный контрпример важнее подбора. Новая isolated модель только после STARTED | D003/run03 и T004 дают источники / negative baseline, не доказательство другой модели. Нужны независимые fixed+movable/Q/prefix records для frames720/448/328 и честный предел каждого verdict |
| D005-02 boundary/HTML, DP-O-010/013; REQ-WHEEL-10/11, AS-WHEEL-24 и REQ-UI-09/11 | Контролируемые deferred/fault controls перед proposed guard mechanism; затем isolated native trace. Это research seam, не production defect fix | `session.test.mjs` общий render fallback / dispose и `recovery.test.mjs` delay/restart полезны; fake DOM не доказывает live HTML focus / async write prevention. Новые controls и ADR/sequences адресуют R001-01…04 |
| D005-03 S1 design / HTML-presenter, DP-O-013; REQ-WHEEL-04/07/08/10, REQ-UI-06, AS-WHEEL-28…30 | Документальная traceability принятого контракта, без нового Owner-выбора и runtime F5 | `facts.test.mjs` сохраняет order / all types/categories / immutable DTO, но не full-DТО cardinality, warning и keyed retention. В ADR/sequence/planned tests отдельно U/R/D/V/M/L/T/P и accepted vs failed controls |
| D005-04 run04 / package / re-estimate | Адресные browser measurements после certificates, затем documentary checks / hashes / handoff | Новое evidence отдельно от run03; browser не доказывает всё mounted production. Report фиксирует environment/commands/actual/ограничения, mapping R001/S1 и оценочное влияние |

Будущие разрешённые outputs: `developer/task_d005_feasibility_report.md`, новый `developer/evidence/task_d005_feasibility/**`, ревизии собственных `drawing_adr_draft.md` / technical sequences / Implementation Plan и appended handoff. Старые D003 report/JSON/manifests/run03 immutable. Shared current requirements/ADR/Manager/Analyst/Tester и production не редактируются. После разрешённой публикации новый OutputSHA / TechnicalPackageV2SHA фиксируется отдельно, не становится d24a24e.

Целостный результат: pinned inputs и новый spec/model diff к D004/D003; таблица R001-01…04/S1→изменение→evidence; F/E matrix frames720/448/328 с certificate/counterexample/UNPROVEN; native/browser records и screenshots либо точная причина NOT RUN; DRAFT ADR/sequences; findings/варианты/обновлённый прогноз и signed handoff. Предлагаемые после исполнения команды / runtimes документируются в report; сейчас Node/pytest/browser/solver/F5/PlantUML **не запускались** и результаты D003/Reviewer не присваиваются.

## 8. Проверки этой подготовки и решение Owner

Сейчас изменяются ровно четыре собственных пути: этот план; appended `developer_artifact.md`; [documentary checker](evidence/task_d005_preparation_check.py); его новый [JSON audit](evidence/task_d005_preparation.json). Команды:

```text
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_preparation_check.py --write
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_preparation_check.py
git diff --check
```

Checker проверяет текущую ветку/HEAD и пустой сохранённый index, AssignmentSHA/pins/contract hashes, неизменность всего прежнего Developer/D003 payload и Manager/чужих/production файлов, source references, links/anchors/tables/scope и арифметику оценки. Он **не выполняет F/E / S1 / SVG эксперимент**. Точные actual counters появляются в JSON и handoff после запуска. Старые preparation audits/manifests не пересчитываются под новый контракт.

**Конкретное решение Owner для старта:** согласовать scope этой версии плана, **16–24 часа / 2–3 чд**, единый эксперимент **≤12 часов внутри** (аналитика ≤4, browser+harness ≤4), передачу **до конца 3-го рабочего дня от отдельного STARTED**, и явно поручить **«Начинай TASK-D-005»**. Затем Developer фиксирует фактический STARTED / source approval / срок и исполняет согласованный scope. Пока разрешение не получено, D005 research / ADR revision не начинается. Повторного решения по S1 или ожидания A007 для этого нет.

Следом после результата и отдельно разрешённой публикации — **T007 и R002** на одном TechnicalPackageV2SHA, закреплённом Manager. A006 подключается только к своей ветви уже опубликованным результатом; production — после отдельного G3. Commit/push/PR/сообщения другим чатам этой подготовкой не выполняются.


## 9. Фактическое исполнение D005 и пересмотр предпосылок

Owner отдельно согласовал assessment v1 и поручил начать19.10.2026; STARTED/срок зафиксированы выше и в корневом handoff. [Результат](task_d005_feasibility_report.md) / [findings](task_d005_findings.md) являются выходом, не пересогласованием S1. D005-01: новая F/E модель,24 клетки,9 exact controls, конкретные negative witnesses; candidate не принят. D005-02:12 boundary controls, guarded value-frame proposal и revised sequence001. D005-03: принятый S1/source rows/index/reconcile в ADR/sequence002, **runtime F5 NOT RUN**. D005-04: run04-delivery24 клетки/2190 probes/438 keyboard и12 HTML/focus controls, полный evidence/post-audit/локальный handoff.

14/24 measured component geometry и438/438 keyboard не дают whole drawing PASS:241/438 conditional Q,238 native mismatch,256 positive return witnesses. Zodiac/sign text/palette не моделируются. Новый источник/спецификация определены до расчёта; повтор browser после initial stop исправил только global delivery capture для10 промахов, сохранив первый run и inputs. [Финальный stop](evidence/task_d005_feasibility/experiment_stop_final.json) завершает experiment≤12; дальнейшие действия — обработка evidence/документы. Исторические D003 report/run03/manifests/criteria и consultation v2 не переписываются.

Оценка D00516–24 остаётся согласованным bounded scope, не новым расходом сверх forecast; unknown actual effort/остаток D003 не вычислены. HTML-presenter6–10 внутри controller, design1–2 внутри D0054–6. По результату **общая drawing implementation9–14 пока не подтверждена**, confidence низкая до выбора допустимой конструкции. Это пересмотр предпосылки, не самовольное расширение бюджета. Следующий дополнительный model / другой radius/domain/Q механизм требует отдельного bounded задания/оценки Manager; изменение смысла — Analyst/Owner. Current candidate rejected, fallback/нормативный ADR/G3 не приняты.

Локальный пакет после проверок требует отдельного поручения commit/push/PR; новый TechnicalPackageV2SHA не создан. Manager закрепляет точную опубликованную версию для T007/R002, затем решает дальнейший маршрут и G3. Чужие статусы/gates не меняются.


Фактические финальные documentary checks: `python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/audit_package.py --write`, повтор без `--write`, `git diff --check`. Audit фиксирует162 payloads +2 self-metadata, baseline604 / D003 archive164, controls9+12+12 / full native2190 / live keyboard438, docs45 / links1301 / tables111, AST6 / Node syntax3 / PUML structure2; exact актуальные hashes/counters в package JSON. Programmatic focus/scroll в activation проверяются по before/after; targeted external-current/collapse causes отделены. Старый preparation checker привязан к prepublication HEAD/EMPTY snapshot и не запускается как validator новой ревизии.
