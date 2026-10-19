# DRAFT — пассивный Chart Renderer с условной выносной колонкой

**Codex / Developer,19.10.2026. Статус:DRAFT.** Ревизия technical proposal по прямому поручению Owner. Кандидат ADR-0042: [реестр](../../../../requirements/decisions/README.md) на InputSHA07bb56ba5d49ec76de64df41ad80d175fbe90a2d заканчивается0041; номер не резервируется, нормативный ADR не создаётся. Перед переносом проверить реестр повторно. [Прежний проект D005](drawing_adr_draft.md) и его SHA8b8c4c8 сохраняются; принятые ADR не заменяются этим draft.

## Контекст и область

Owner выбрал управление через HTML и условную колонку для скученных point-меток; SVG пассивно отображает selection. [Source решения](owner_decision_drawing_2026-10-19.md), [Manager DP-O-010…013](../manager_artifact.md#3-единый-реестр-dp). Изменяются проект внутренней границы renderer и drawing domain; HTTP/engine/ChartDTO/cache/golden не затрагиваются. Input: accepted v3+S1@2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 + поздние Owner delta. Новый TargetContractSHA ожидает узкой синхронизации Analyst; решение владельца DP-O-010/011/012 ещё не принято на этот draft.

## Предлагаемое решение

1. Session остаётся accept-owner/HTTP/recovery. ResultController владеет accepted envelope, once acceptanceSeq/attempt/cause, index по полному DTO, selection/expansion и живыми HTML controls. HTML и SVG читают одну snapshot; leaf не инициирует HTTP и не пересчитывает доменные факты. A006 already_applied остаётся отдельной узкой policy-зависимостью.
2. Выбрать **revision-local connected measurement surface + guarded deep copy/install**. Renderer не получает живой image host или установленную SVG-копию. Snapshot скопирована глубоко и заморожена. Surface живёт до revoke, не до promise settlement. Current callbacks могут предложить новую копию; retired reference — только detached дерево.
3. Внутренний протокол: `renderer.update(readonlySnapshot, revisionSurface, publish): void|Promise<void>`, `renderer.dispose():void`; `publish(svg)` возвращает committed/revoked. Это внутренний protocol draft, не новый public API. На accepted B порядок R001-01: revoke→removeA→full-B index/once/reconcile→HTML/summaryB→guarded dispose retired once→guarded drawB.
4. Adapter проверяет passive tag/attr/value set, копирует SVG и повторно проверяет instance+revision+acceptance непосредственно перед синхронной install без await. Запрещены внешние/активные nodes/references, on*, interaction/focus, произвольное positioning и external CSS/ID access. В production whitelist должен проверять также размеры/viewBox, numeric values и внешние ID references. Harness проверяет принцип/основные tag/event/style случаи, не является законченным sanitizer. Глобальный document доступен same-origin JS, поэтому дисциплина проверяется кодом/тестами; security sandbox не заявляется.
5. Factory/update sync throw и async rejection текущей lease → revoke failed lease, clear imagery, typed local `svg_unavailable(reason)`; HTML B доступен. Dispose fault retired leaf не мешает B. Stale rejection/late publish лишь диагностируются с retired token. HTML/controller fault идёт в действующий safe-read путь. Close idempotent. Surface cleanup и listeners замкнуты на lifecycle.
6. Drawing — [правила и измеримые predicates](column_renderer_design_v1.md): default source-longitude, measured C0, только конфликтующие point-метки в общей упорядоченной колонке, growing H при сохранении em16/12/gap2/anchor0,5; aux локальны. Для column domain отдельная row objective вместо старого annular chord return. Локальная aux1px проверка требует целого начального prefix; exact contact/closing derivative блокирует и смещение<1px. Глобальный geometry optimum не вводится.
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

**Принятие:** technical owner по DP-O-010/011/012 и назначенные reviewers проверяют exact опубликованную версию и узкую дельту критериев. Manager регистрирует итог и G3; до этого этот проект остаётся DRAFT. [План40–64ч](full_wheel_implementation_plan.md), [lifecycle sequence003](sequence_diagrams/ui/003-passive-copy-install.puml), [drawing sequence004](sequence_diagrams/ui/004-column-layout-revision.puml). Старые diagram001/002 сохраняют исторический D005 active-SVG предмет и не применяются к новому scope автоматически.
