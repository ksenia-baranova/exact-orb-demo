# TASK-T-008 — независимая сверка переноса требований и sequences

**Автор / подпись:** Codex / Tester, 21.10.2026. Reviewer — Manager по полноте, точным версиям и traceability. Предмет — опубликованное поручение TASK-T-008, Manager §§2.28–2.29; verdict принадлежит Tester.
**Оценка до STARTED:** 2–4 рабочих часа, confidence средняя–высокая; передача 21.10 до18:00МСК. STARTED21.10 14:01МСК сообщён Owner до выполнения сверки. Допущения: опубликованные inputs доступны через Git, перенос документальный; при реальном изменении expected behavior нужен адресный retest.
**Verdict:** **TRANSFER_REWORK_REQUIRED — два адресных исправления документов, T008-R01/R02.** Состав, IDs, хеши, разделение current/archive, сохранность фактов/S1 и применимость прежнего runtime evidence подтверждены. Это не требование повторять A008 или исследование геометрии. T008-N01 — необязательное уточнение traceability, не новый дефект реализации.

## Версии, сохранность checkout и метод

| Назначение | Точная версия |
|---|---|
| TransferSHA / AssignmentSHA / HEAD сверки | c7219e485917366f67159c9a08e3c78dc4e69372 |
| SourceSHA до переноса | 883b6d3a47f7113e44ede73c9ad16b40f15bbdaf |
| Фактический RetestedSHA реализации | 99741958b4bbee8884505920f4a02f2f19dea3e3 |
| Авторский Tester OutputSHA с runtime/retest | f930c864d6a416acff8a49081585950853b931f9 |
| Analyst v3+S1 | 2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 + поздние явные Owner-решения |
| Нормативный исторический MainBaseline | 535551026af6eedaf2a0aa5c0daa96fa94655ec1 |
| Проверенный origin/main | bba8d6cfb22f586f86c3035423f2535ede158b9f; запись DEBT-UI-004 в нём отсутствует |

Worktree — C:\Users\KateUser\.codex\worktrees\ui-chart-wheel-test\exact-orb-recovered, ветка test/ui-chart-wheel. До обновления HEADf930c86, local/index чистые. git fetch origin и git merge --ff-only origin/change/ui-chart-wheel дали c7219e4; после local/index также чистые. Stash0c2eb3ba6e9b6d191830da6a0d1c132a34762679 и d936068b2806107cbe21499538b4f038780cc7fb сохранены. Reset/force/clean не использовались. Чужие worktrees/чаты не читались; удалённые исходники получены через git show SourceSHA:path. Более поздний HEAD предмет не меняет.

Основные входы: [transfer map](../analyst/transfer_map.md), [Manager manifest](../manager/transfer_manifest.json), [Manager§2.27](../manager_artifact.md#227-завершение-реализации-техдолг-и-подготовка-к-main), [§2.28](../manager_artifact.md#228-перенос-требований-и-sequences-по-прямому-поручению-owner), [§2.29](../manager_artifact.md#229-публикация-переноса-и-точный-вход-t008), [поручение](../manager/prompts/task-t-008-transfer-readiness.md).
Независимые результаты — [собственный audit](evidence/task_t008/review.json), [воспроизводимый checker](evidence/task_t008/verify_transfer.py). Manager validation не объявляется выполненной Tester: пересчёт source/target/IDs/ссылок независимый; смысл сопоставлен вручную с Owner evidence. Машинный hash блока доказывает текст/версию, семантический verdict дан в таблицах ниже.

## Ожидаемые инварианты до сверки

- Все22REQ/53AS имеют прежние IDs; исходный M1-7 сохраняется за исключением явно принятой дельты. Механический перенос не должен возвращать SVG-активацию, колонку, старые category words или общий gate подробностей.
- Все13 исходников существуют на SourceSHA и отсутствуют на TransferSHA; каждая цель доступна и соответствует записанным хешам. Пять текущих technical и три archive сохраняют исходное тело; текущие behavioral отражают поздний контракт.
- S1 считается по полному принятому DTO до subset/filter. Duplicate/reverse/category/orb не создают отдельного адреса, unique reverse и другой type остаются независимыми позитивными контролями.
- У редактора immutable B, явный live target, fresh matching и once-потребление; draft C не теряется. Source=current/identity не доказывают собственный build, RESULT_SUPERSEDED не подтверждает цель.
- Нет src/tests/HTTP/engine/golden изменений и нет превращения прежних проверок в запуск на TransferSHA. 004 закрыт;002/precision и ADR имеют собственные незавершённые условия.

## REQ → source → target → результат

Источники в этой таблице читаются на SourceSHA: A = analyst/requirements.md внутри change; B = docs/requirements/current/ui/birth-form-and-facts.md. Для A полный path/исходный hash каждого блока сохранён в audit. W = [chart-wheel.md](../../../../requirements/current/ui/chart-wheel.md), U = [birth-form-and-facts.md](../../../../requirements/current/ui/birth-form-and-facts.md) на TransferSHA. PASS здесь означает fidelity текста, не новое исполнение acceptance.

| ID | Source | Target | Сопоставленный смысл / verdict |
|---|---|---|---|
| REQ-WHEEL-01 | A, тот же ID | W#req-wheel-01 | PASS: один принятый DTO, passive leaf, HTML владеет выбором; без HTTP/пересчёта из renderer |
| REQ-WHEEL-02 | A + house rows Owner20.10 | W#req-wheel-02 | PASS:12знаков/куспидов,5опубликованных angles, source longitude и ориентация; house берётся из DTO |
| REQ-WHEEL-03 | A | W#req-wheel-03 | PASS: cosmogram без домов/углов/ложного времени; устойчивые source aspects и смысл max orb |
| REQ-WHEEL-04 | A + passive/aspect reading | W#req-wheel-04 | PASS: exact/working, background ends-only, S1 full-source; from/to/type/category/orb/order не меняются |
| REQ-WHEEL-05 | A + house rows Owner20.10 | W#req-wheel-05 | PASS: внутренние natal/cosmogram ряды вместо старого минимального разноса/колонки; ID/R/source anchors сохранены, geometry debt явный |
| REQ-WHEEL-06 | A + no-category Owner19.10 | W#req-wheel-06 | PASS:solid/dashed,цвет+текст,selected contour☌; старые SVG-слова отменены, HTML category/type/orb сохранены |
| REQ-WHEEL-07 | A + passive/aspect reading Owner20.10 | W#req-wheel-07 | PASS:HTML-only, point без focus/scroll; отдельное чтение participants/source houses, return/Escape/live origin |
| REQ-WHEEL-08 | A + accepted-once Owner20.10 | W#req-wheel-08 | PASS:repeat point→first5; aspect exit→прежние disclosures; F5/reset/ordinary current/absent/S1 различены |
| REQ-WHEEL-09 | A + first-five points Owner20.10 | W#req-wheel-09 | PASS:три независимые5/all таблицы; SVG полный, конечная ширина до draw,1440/768/360 |
| REQ-WHEEL-10 | A + passive/aspect reading/fix004 | W#req-wheel-10 | PASS:HTML Q44/focus,SVG title/description без controls;local SVG fault не уничтожает HTML;S1 warning |
| REQ-WHEEL-11 | A | W#req-wheel-11 | PASS:коррелированные реальные HTTP переходы и отдельное UI evidence;HTTP success не доказывает render |
| REQ-UI-01 | A + B | U#req-ui-01 | PASS:bootstrap→current,ready не chart;wheel/summary только принятой карты;empty/unavailable без старых фактов |
| REQ-UI-02 | B | U#req-ui-02 | PASS:тело полностью совпало;minute-only,unknown time,place_id/catalog,без координат/offset от пользователя |
| REQ-UI-03 | A + B + first-five/once | U#req-ui-03 | PASS:ручной checkbox,ровно три поляPOST,валидация/issues,один build,immutable summary/draft |
| REQ-UI-04 | A + B + first-five | U#req-ui-04 | PASS:source sign/degree/minute/R,orb half-up,[]≠null;табличные значения не вычисляются из geometry |
| REQ-UI-05 | A + B + first-five/aspect reading | U#req-ui-05 | PASS:source points/order/house/angles;normal5/all,participants вне первой пятёрки,cosmogram без вымышленных домов |
| REQ-UI-06 | A + B + late Owner | U#req-ui-06 | PASS:все исходные строки/category/orb/order и S1;point filter all,aspect one,return disclosures |
| REQ-UI-07 | B | U#req-ui-07 | PASS:тело полностью совпало;нет mock/future групп в продукте |
| REQ-UI-08 | A + B | U#req-ui-08 | PASS:stale/empty/unavailable и birth различены;current не является автоматическим build/reset |
| REQ-UI-09 | A + B + already_applied Owner20.10 | U#req-ui-09 | PASS:HTTP recovery/gates сохранены;fresh live target once;failed/stale/different/empty/superseded не подтверждают B |
| REQ-UI-10 | A + B + aspect reading/fix004 | U#req-ui-10 | PASS:доступность/узкий экран,HTML Q44;point focus неподвижен,aspect entry/exit и editor-collapse имеют явную политику |
| REQ-UI-11 | A + already_applied/aspect reading | U#req-ui-11 | PASS:summary показанной карты,POST immutable intent / GET birth;collapse только при совпадении draft,повторный current не скрывает editor |

Поздние источники: [house rows](../developer/owner_decision_house_rows_2026-10-20.md), [points five/all](../developer/owner_decision_points_disclosure_2026-10-20.md), [already_applied](../developer/owner_decision_already_applied_2026-10-20.md), [no-category evidence](../developer/owner_decision_drawing_2026-10-19.md). Aspect reading/focus — подписанный Developer-пакет06-owner-composition-aspect-view.md на SourceSHA и Manager§2.27. Эти источники читаются из опубликованного Git, не из чужой локальной сессии. Старая колонка из решения19.10 не возвращается поверх явной замены20.10.

## AS → source → target → результат

BAS = docs/requirements/current/ui/scenarios.md на SourceSHA; AAS = analyst/scenarios.md в change на SourceSHA. Все цели — [общие scenarios](../../../../requirements/current/ui/scenarios.md), одноимённый anchor as-ui-NN/as-wheel-NN. Audit содержит отдельные75 source/target block hashes, а для AS-UI-22 также hash исходной Analyst-дельты.

| ID | Source | Target anchor | Смысл / verdict переноса |
|---|---|---|---|
| AS-UI-01 | BAS | as-ui-01 | PASS:первый вход/empty;тело совпало |
| AS-UI-02 | BAS | as-ui-02 | PASS:поиск/два одноимённых места;тело совпало |
| AS-UI-03 | BAS | as-ui-03 | PASS:known-time natal;тело совпало |
| AS-UI-04 | BAS | as-ui-04 | PASS:unknown-time cosmogram;тело совпало |
| AS-UI-05 | BAS | as-ui-05 | PASS:пустое/противоречивое время;тело совпало |
| AS-UI-06 | BAS | as-ui-06 | PASS:date/time/place errors;тело совпало |
| AS-UI-07 | BAS | as-ui-07 | PASS:группы natal/форматы/source values;тело совпало |
| AS-UI-08 | BAS | as-ui-08 | PASS:cosmogram/max orb/no houses;тело совпало |
| AS-UI-09 | BAS | as-ui-09 | PASS:рассчитанный пустой aspects;тело совпало |
| AS-UI-10 | BAS | as-ui-10 | PASS:restore без расчёта;тело совпало |
| AS-UI-11 | BAS | as-ui-11 | PASS:stale/unavailable;тело совпало |
| AS-UI-12 | BAS | as-ui-12 | PASS:утрата сессии/draft;тело совпало |
| AS-UI-13 | BAS | as-ui-13 | PASS:rate/capacity admission;тело совпало |
| AS-UI-14 | BAS | as-ui-14 | PASS:commit uncertainty/timeout;тело совпало |
| AS-UI-15 | BAS | as-ui-15 | PASS:safe public projection;тело совпало |
| AS-UI-16 | BAS | as-ui-16 | PASS:две вкладки/superseded;тело совпало |
| AS-UI-17 | BAS | as-ui-17 | PASS:transport validation/issues priority;тело совпало |
| AS-UI-18 | BAS | as-ui-18 | PASS:empty search/catalog fault;тело совпало |
| AS-UI-19 | BAS | as-ui-19 | PASS:keyboard/narrow screen;тело совпало |
| AS-UI-20 | BAS | as-ui-20 | PASS:manual checkbox gate;тело совпало |
| AS-UI-21 | BAS | as-ui-21 | PASS:закрытый этап/DEBT-UI-001;тело совпало |
| AS-UI-22 | BAS + AAS MODIFY + first-five Owner20.10 | as-ui-22 | PASS:глобальный gate заменён,три независимые5/all,неактивный чат сохранён |
| AS-UI-23 | BAS | as-ui-23 | PASS:lost build response/recovery;тело совпало |
| AS-WHEEL-01 | AAS + first-five/once | as-wheel-01 | PASS:committed A при позднем draft B,одинPOST,summary A |
| AS-WHEEL-02 | AAS + first-five | as-wheel-02 | PASS:F5/restore/no selection,initial five/all,gate снят |
| AS-WHEEL-03 | AAS + first-five/internal rows | as-wheel-03 | PASS:все SVG points/source anchors,HTML раскрытие,angles |
| AS-WHEEL-04 | AAS + aspect reading | as-wheel-04 | PASS:source angle endpoint,не выдуман дом ASC,return |
| AS-WHEEL-05 | AAS | as-wheel-05 | PASS:cosmogram orientation/no houses/max orb |
| AS-WHEEL-06 | AAS | as-wheel-06 | PASS:background-only/[] отличимы от empty;точки остаются |
| AS-WHEEL-07 | AAS + no-category/passive | as-wheel-07 | PASS:unique☌/selected contour,background ends-only |
| AS-WHEEL-08 | AAS + no-category | as-wheel-08 | PASS:solid/dashed,семь типов/legend/HTML,без SVG category words |
| AS-WHEEL-09 | AAS + internal rows | as-wheel-09 | RETURN T008-R01:source seam/R сохранён по смыслу,но неверно указан F2 вместо F3 |
| AS-WHEEL-10 | AAS + internal rows/debt | as-wheel-10 | PASS:данные/typed local fault;универсальный dense/precision PASS не заявлен |
| AS-WHEEL-11 | AAS + passive/aspect reading | as-wheel-11 | PASS:HTML-only взаимоисключающий выбор,background,без HTTP |
| AS-WHEEL-12 | AAS + aspect reading/points five | as-wheel-12 | PASS:три disclosures/draft C/return/origin;participant за первой пятёркой |
| AS-WHEEL-13 | AAS | as-wheel-13 | PASS:point repeat→first5 aspects,keyboard,без общей кнопки снятия |
| AS-WHEEL-14 | AAS + once/first-five | as-wheel-14 | PASS:changed-birth commit reset,resize preserve,не reset по identity |
| AS-WHEEL-15 | AAS | as-wheel-15 | PASS:confirmed empty/unavailable удаляют numeric/image/selection |
| AS-WHEEL-16 | AAS + viewport/passive/first-five | as-wheel-16 | PASS:actual CSS width до draw,1440/768/360,no overflow |
| AS-WHEEL-17 | AAS | as-wheel-17 | PASS:stale сохраняет данные,failed read не доказывает absent |
| AS-WHEEL-18 | AAS + first-five/once | as-wheel-18 | PASS:422/429/pre-admission503 сохраняют A/draft;reset толькоaccepted new build |
| AS-WHEEL-19 | AAS + Owner already_applied/once | as-wheel-19 | PASS:lostPOST safe read/manual retry;fresh live goal отличим от ordinary current |
| AS-WHEEL-20 | AAS + Owner once | as-wheel-20 | PASS:Retry-After/restart gate/commit uncertainty,без autoPOST |
| AS-WHEEL-21 | AAS | as-wheel-21 | PASS:initial/foreground late A/B не затирают draft;summary accepted facts |
| AS-WHEEL-22 | AAS + Owner already_applied | as-wheel-22 | PASS:две coordinators/dispose/late response/superseded;source provenance не выдуман |
| AS-WHEEL-23 | AAS + passive/aspect reading/fix004 | as-wheel-23 | PASS:HTML Tab/Enter/Space/Q44,Escape/live focus,ambiguous activation безопасна |
| AS-WHEEL-24 | AAS + passive boundary | as-wheel-24 | PASS:local image fault/alternate leaf,HTML сохраняется;ADR approval не имитируется |
| AS-WHEEL-25 | AAS | as-wheel-25 | PASS:source ASC/0Aries и четыре cardinal стороны;не универсальный radial proof |
| AS-WHEEL-26 | AAS + points five | as-wheel-26 | PASS:три независимых5/all,<=5 без toggle,SVG points полный |
| AS-WHEEL-27 | AAS | as-wheel-27 | PASS:all source point aspects/background/angles/>5,пустой south_node не пустая карта |
| AS-WHEEL-28 | AAS + passive/aspect reading | as-wheel-28 | PASS по совокупности F5+REQ+AS23/30;T008-N01:уточнить явную ссылку на начальные S1 controls |
| AS-WHEEL-29 | AAS + aspect reading | as-wheel-29 | PASS:return/Escape/same-row,независимые disclosures/live origin,без старого planet-filter |
| AS-WHEEL-30 | AAS + passive/aspect reading | as-wheel-30 | PASS:0/1/>1 full-source matches,accepted/failed/current,absent/ambiguous/unique restore,draft |

22 неизменённых AS-UI сопоставлены по полному телу, не только заголовкам; REQ-UI-02/07 также полностью совпадают после удаления технических anchor-разделителей. HTTP §7.2, исходные числовые факты, DTO order, S1, minute-only input и M1-7 recovery/consent/publication restrictions не получили новой семантики. Неизменность HTTP/engine/API источников отдельно подтверждается tree equality src/tests; это не новое runtime-исполнение всех AS.

## Все11 PUML: source → target → verdict

Source ниже — удалённый path внутри change на SourceSHA; target — путь относительно docs/sequence_diagrams/. Точные хеши каждого файла находятся в собственном audit, а не выводятся из одного Manager validation.

| Source | Target | Статус / независимая сверка |
|---|---|---|
| analyst/sequence_diagrams/ui/001-chart-presentation.puml | ui/001-chart-presentation.puml | CURRENT/PASS:bootstrap/current/accepted source,full-source S1,normal/aspect mode,empty/unavailable,local fault |
| analyst/sequence_diagrams/ui/002-wheel-table-selection.puml | ui/002-wheel-table-selection.puml | CURRENT/PASS:HTML-only,full-source S1,point repeat,aspect focus/return/disclosures;SVG без intents/tab stops |
| analyst/sequence_diagrams/ui/003-edit-and-recovery.puml | ui/003-edit-and-recovery.puml | CURRENT/PASS:immutable B/draft C,committed/already_applied/recovery/superseded,once-reset/conditional collapse |
| developer/sequence_diagrams/ui/003-passive-copy-install.puml | ui/technical/003-passive-copy-install.puml | CURRENT/PASS:исходное тело сохранено;lease/revoke/clone/install/retired failures;DRAFT явно |
| developer/sequence_diagrams/ui/005-accepted-once-editor.puml | ui/technical/005-accepted-once-editor.puml | CURRENT/PASS:исходное тело сохранено;live attempt/fresh match/ordinary later current;DRAFT явно |
| developer/sequence_diagrams/ui/006-aspect-reading-mode.puml | ui/technical/006-aspect-reading-mode.puml | CURRENT/PASS:исходное тело сохранено;participants/source houses/settled guard/Escape/live origin |
| developer/sequence_diagrams/ui/007-internal-house-rows.puml | ui/technical/007-internal-house-rows.puml | CURRENT/PASS:исходное тело сохранено;source house/cusps,internal rows,no column/planet leaders |
| developer/sequence_diagrams/ui/008-viewport-legend-vectors.puml | ui/technical/008-viewport-legend-vectors.puml | CURRENT/PASS:исходное тело сохранено;final width before draw,native bounds/vector symbols,retained selection |
| developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml | research/ui-chart-wheel/001-result-renderer-lifecycle.puml | ARCHIVED/PASS:тело SourceSHA неизменно;ARCHIVED/SUPERSEDED пометка и source provenance добавлены |
| developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml | research/ui-chart-wheel/002-acceptance-selection-focus.puml | ARCHIVED/PASS:старый active-intent/A006 вариант не выдан за текущий |
| developer/sequence_diagrams/ui/004-column-layout-revision.puml | research/ui-chart-wheel/004-column-layout-revision.puml | ARCHIVED/PASS:старый column/PAV вариант не переносится в current house-row oracle |

Структура проверена отдельно для11/11: ровно один start/end, вложенность alt/opt/note/ref/end и отсутствие незаявленных include. У всех5 technical и3archive после удаления двух служебных transfer-комментариев тело совпало с Git SourceSHA. Три behavioral переписаны по позднему контракту и проверены вручную по требованиям/Owner источникам. Tracked PNG для этих11 source paths нет. PlantUML render **NOT RUN**: plantuml/java/dot в доступном PATH и PlantUML jar в репозитории не найдены. Структурная проверка не является компиляцией или визуальной оценкой диаграмм.

## Точечные возвраты и замечание

### T008-R01 — неверный fixture в AS-WHEEL-09

**Тип:** ошибка переноса тестового сценария; не implementation bug. **Ответственный:** исполнитель переноса / Analyst; Manager маршрутизирует исправление. **Влияние:** AS09 нельзя воспроизвести по указанному входу.
**Expected / oracle:** source AS-WHEEL-09 на SourceSHA явно задаёт F3 с пятью R через0°. Таблица «Проверочные данные» на TransferSHA также определяет F3 как seam/R; F2 — session_view.json/session.mjs для ready/empty/unavailable/recovery.
**Actual:** current AS09: «Исходный seam/R набор F2 из раздела проверочных данных». F2 не задаёт пятёрку359.70/359.85/0/0.15/0.30 и не является этой раскладкой.
**Контрпример / позитивный контроль:** выполняющий только F2 ready/unavailable не проверяет seam/R и не может восстановить нужный expected; заданный F3 содержит именно пять разных IDs/retrograde/долгот, а отдельный sparse служит положительной парой для читаемости.
**Условие исправления:** указать F3 (или точный опубликованный эквивалент со всеми source values), сохранить sparse paired control, internal-house-row expected и DEBT-UI-004. Не возвращать старую колонку/minimality. Повторная передача — исправленный SHA и адресная сверка AS09/F3; новый полный runtime не нужен из-за исправления имени fixture.

### T008-R02 — новая битая ссылка на удалённые behavioral sequences

**Тип:** navigation defect переноса; не production defect. **Ответственный:** Manager как владелец строки manager_artifact.md §2.3, «Обязательные материалы» (строка309 на TransferSHA).
**Expected / oracle:** навигация ведёт к трём текущим behavioral в docs/sequence_diagrams/ui/ либо к явному Git SourceSHA, если обозначена история.
**Actual:** destination ссылки «behavioral sequences» в Manager — analyst/sequence_diagrams/ui/ внутри change, но этот каталог исчез после удаления трёх PUML. На SourceSHA он существует; на TransferSHA отсутствует. Это новый broken link, отдельно от двух прежних roadmap→prompts.
**Позитивный контроль:** все три целевых файла и [current index](../../../../sequence_diagrams/ui/README.md) доступны на TransferSHA; Git-каталоги при проверке учитываются как валидные destinations, не принимаются за missing-файлы.
**Условие исправления:** заменить этот destination текущим общим каталогом/индексом или исторической ссылкой с точным SHA по назначению абзаца; повторить адресную проверку и обновить manifest/link validation владельцем. Tester чужой Manager-файл не редактирует.

### T008-N01 — явная traceability AS28 к сохранённому F5

Исходный AS28 содержал отдельные S1 controls U/R/D/V/M/L/T/P и направления pointer/keyboard, natal/cosmogram, five/all/planet-filter. Новая краткая карточка AS28 не повторяет этот список. При проверке **всего пакета** подтверждено: F5 сохраняет cases/expected, P для five/all/planet и обязательный unaffected positive; AS23 сохраняет keyboard/ambiguous non-activation, AS30 —accepted/reconcile/failed-read/point/recovery, REQ04/08/10 —full-source cardinality и локальность отказа. Поэтому потери всего S1-контракта не установлено. Рекомендуется явная ссылка из AS28 на F5+AS23/30, чтобы выполнение краткой карточки не ограничили одним unique F1. Это advisory, отдельного runtime-блокера/нового Owner choice не создаёт.

## Фактические проверки и применимость runtime evidence

| Команда / чтение | Actual |
|---|---|
| git branch --show-current; git rev-parse HEAD; git status --porcelain=v1 --untracked-files=all; git diff --cached --name-status; git stash list --format='%H %s' | До/после синхронизации test/ui-chart-wheel;f930c86→c7219e4;local/index EMPTY;оба stash сохранены |
| git fetch origin; git ls-remote https://github.com/ksenia-baranova/exact-orb-demo.git refs/heads/change/ui-chart-wheel refs/heads/test/ui-chart-wheel | change=c7219e4;test=f930c86 на момент входа;git cat-file -t AssignmentSHA=commit |
| git merge --ff-only origin/change/ui-chart-wheel | exit0,fast-forward |
| git show 883b6d3a47f7113e44ede73c9ad16b40f15bbdaf:path | Все13 удалённых sources прочитаны из закреплённого Git;не из чужого checkout |
| git diff --name-only 883b6d3a47f7113e44ede73c9ad16b40f15bbdaf c7219e485917366f67159c9a08e3c78dc4e69372 -- src tests | Пусто;дополнительно src/tests tree OID совпали и с RetestedSHA9974195 |
| python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/tester/evidence/task_t008/verify_transfer.py --write; повтор без --write | Новый собственный audit;13 source Git LF hashes +13 snapshot projections,16 target hashes,22REQ/53AS/11PUML,8current/3archive,17historical reports,2914raw evidence paths;см. raw результаты в review.json |
| Независимый link/table/anchor audit внутри verify_transfer.py |20изменённых current Markdown,1059локальных ссылок,83таблицы;2прежние roadmap ошибки и1новая T008-R02. Exit0 auditor не означает PASS переноса |
| Get-Command plantuml,java,dot -ErrorAction SilentlyContinue; rg --files -g '*plantuml*' -g '*.jar' -g AGENTS.md . | Renderer/jar не найден;единственный AGENTS корневой;render NOT RUN |
| rg по tests/src и current/sequences на удалённые paths | В src/tests нет ссылок на удалённые рабочие файлы;в PUML только явные SourceSHA-комментарии |
| git diff --check | Финальный exit0;состав только собственных Tester-материалов |

Хеши исходных snapshots в Manager manifest и source Git LF отличаются представлением переводов строк: source_git_sha256_lf независимо совпадает с git show; source_sha256/source_bytes совпали с определённой LF/CRLF проекцией для13/13. Это два явно различных поля, не ошибка содержимого. Целевые16 хешей сверены по Git LF без подгонки manifest.

Все2914 raw paths в tester/evidence и developer/evidence сохраняют прежние Git blobs между SourceSHA и TransferSHA. Все17 перечисленных исторических отчётов побайтово неизменны. Исходный retest manifest подтверждён на его SHA:40/40 payload hashes совпадают на SourceSHA. На TransferSHA39/40 остаются теми же; единственная разница — разрешённая навигационная правка tester_artifact.md. После удаления отдельного Manager-prelude и нейтрализации Markdown destinations весь прежний текст verdict/подписей совпал с SourceSHA. Это не повреждение raw evidence и не основание пересчитать исторический manifest. Первый вариант собственного checker ошибочно требовал40/40 на TransferSHA; проверка исправлена на это явное различение. Directory destinations также учитываются как Git trees; финальные2inherited+1new не включают ложных ошибок существующих каталогов.

**Применимость runtime подтверждена:** все14 LF fingerprints совпадают с9974195;src/tests tree полностью неизменны от9974195 черезSourceSHA доTransferSHA. Сохранены229UI Node /53target Python /2959pytest PASS+1known DEBT-CALC-001 skip и native Chrome/Yandex1440/768/360,6/6cases/672checks. Результаты остаются на RetestedSHA9974195/OutputSHAf930c86. Здесь suites/browser/реальный backend/HTTPS повторно **NOT RUN**. Исправление двух документационных ошибок не требует полного повторного runtime. Нового воспроизведённого расхождения реализации и принятого поведения не установлено; при его появлении нужен отдельный implementation finding с exact SHA/oracle и адресным retest.

TEST-FIND-WHEEL-004 сохраняется **CLOSED / RETEST_PASS**. TEST-FIND-WHEEL-002 и precision — **OPEN / INDETERMINATE**, разрешены к отсрочке [DEBT-UI-004](../../../technical_debt.md#debt-ui-004);это неPASS и не отменаQ44/S1/source facts. На проверенном origin/main запись004 ещё не опубликована, registry SHA не назначается. Общий technical_debt.md Tester не менял.

## Передача Manager и оставшиеся условия merge

1. Исправить T008-R01/R02 в ownership документов и передать новый документационный SHA с адресным diff; T008-N01 учитывать как traceability recommendation. Повторить только затронутую сверку сценария/ссылки, не создавать заново A008 и не запускать общее исследование геометрии.
2. Рассмотреть этот подписанный T008 по полноте/версиям/traceability после отдельно разрешённой публикации; OutputSHA пока отсутствует, результат локальный. Автоматически DONE/APPROVED/G5 Tester не объявляет.
3. Технический drawing ADR по-прежнему DRAFT; перенос5technical PUML не заменяет D008/его назначенное review и принятие ADR. Это отдельное условие интеграции, не причина отрицать подтверждённые hashes/IDs/sequences или ждать повторного переноса схем.
4. Подтвердить публикацию DEBT-UI-004 в main с точным registry SHA и допустимым scope;Owner-разрешение отсрочки уже есть, вопрос заново не задаётся. Долг не становится runtime PASS.
5. Перед отдельно разрешённым merge сверить актуальный main/Candidate и разрешение документальных modify/delete пересечений по процессу§6.1–6.2; сохранять принятый контракт, исходные подписи/raw manifests. Текущий T008 не является пробным/фактическим merge или проверкой ещё не созданного CandidateSHA.

**Изменения Tester:** этот report, подписанный handoff в tester_artifact.md, собственные checker/audit в evidence/task_t008/ и адресная запись о принятом долге в defects.md. Production/tests/requirements/Owner choices/Manager/Developer/Analyst и прежние raw evidence не менялись. Commit/push/merge/PR/сообщения другим чатам этим поручением не выполняются.

### Отдельное поручение на публикацию — 2026-10-21

Owner разрешил commit/push результата вtest и merge вchange. Предыдущие отметки «не поручены/не выполняются» фиксируют состояние до этого поручения. После fetch origin/change остаётся c7219e485917366f67159c9a08e3c78dc4e69372;origin/test=f930c864d6a416acff8a49081585950853b931f9. Публикационный scope —5 собственных Tester paths;TransferSHA/SourceSHA/RetestedSHA и отрицательный verdict переноса не меняются. Новый review.json — снимок package verification до staging,а не подтверждение ещё не выполненного push/merge. Resolver OutputSHA и порядок проверки опубликованных refs находятся в tester_artifact.md,разделе «Публикация TASK-T-008 — 2026-10-21». Итоговые SHA сообщаются после операций;R01/R02 исправляет владелец документов.
