# TASK-T-003 — review Developer consultation v2

**Автор / подпись:** Codex / Tester, 2026-10-17.
**Вывод:** подтверждаю наблюдаемость и проверяемость предложений в предмете Tester. Предметный возврат consultation v2 не требуется.
**Предел:** это документальное review плана; все будущие runtime / browser controls ниже — NOT RUN.

## Версии и фактическое основание

| Предмет | Точная версия |
|---|---|
| HEAD начала review / опубликованная оценка | `26b11e84884c50b6e70c62dbefaef9f90c18c827` |
| Задание / DP / последующие задания | [Manager §§2.9–2.11 / §3](../manager_artifact.md) @ `f0a58a544d358585c0a6dcee2b58bbe91fc84ff8` |
| Исторический ReviewInputSHA | `3da42d64a736cecd9996d57cc4d39e814908fcf4` |
| Developer consultation v2 | [Implementation Plan](../developer/implementation_plan.md), [DP input](../developer/decision_input.patch) @ `f9c70f75ea815b2f3bf7e01426ee5afe65b31606` |
| Контракт сопоставления, Analyst v3 | [Requirements](../analyst/requirements.md), [scenarios](../analyst/scenarios.md), [behavioral sequences](../analyst/sequence_diagrams/ui/) @ `2634b224894b1046113557bfe241f0a5f2d46f8c` |
| Прежний Tester v2 / TASK-T-002 | `7e95c0f680cc790fc8b45d9e25d69cc6e94fbc12`; InputSHA `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba` |
| Нормативный baseline чтения code / tests / общих требований | `535551026af6eedaf2a0aa5c0daa96fa94655ec1` |

Поздний HEAD не заменяет закреплённые предметы review. CandidateSHA / TestedSHA / AcceptedSHA отсутствуют. Первоначальные STARTED и согласованные сроки сохранены в [Tester-индексе](../tester_artifact.md).

Сначала из v3 выделены различающие переходы и независимые контроли, затем сопоставлены план / patch / связанные будущие промты. Code и assertions прочитаны для проверки швов; прежний PASS не переносился на новое SVG-поведение. [Evidence JSON](evidence/task_t003_review.json) хранит 42 source hashes / точные SHA и результаты статического audit. Manifests Developer и Analyst проверены 9/9 каждый. Пять строк Developer patch DP-O-010…014 относительно его собственного baseline 543b7ec меняют только колонку рекомендаций; остальные девять колонок сохранены. Дополнения уже зарегистрированы Manager @ f0a58a5; повторно patch не применялся.

Существующие нерешённые technical / measurement вопросы конкретизированы ниже. Они не объявляются новыми defects реализации и не требуют повторно выбирать принятые Owner toggle / current / collapse / оформление ☌.

## 1. Renderer и изоляция отказа — T003-G01

**Источники:** REQ-WHEEL-01/10/11, AS-WHEEL-24, DP-O-010; plan строки 35–45, 83–96.

**Oracle:** принятый DTO B / Owner fallback: HTML и summary B доступны, SVG A удалена, отказ SVG B обозначен явно. Локальный отказ изображения сам по себе не создаёт build и не включает общий safe-read-only режим; существующие ограничения recovery сохраняются.

**Данные / независимый positive control:** реально показать A, затем отличимую B успешным renderer. На том же port подключить альтернативный renderer на B / том же выборе и проверить фактическую активацию объекта и результат в HTML / SVG. В отдельном проходе отказать только leaf SVG при принятии B, подтвердив достижение fault hook и доступность HTML B / summary B / сообщения без старой SVG A. Затем успешный renderer на тех же данных восстанавливает изображение. DTO до/после неизменен. Положительный явный submit подтверждает работающий сетевой счётчик; локальная замена / ошибка дополнительных запросов не даёт.

**Что подтверждено чтением:** [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs), строки 44–56, включает requiresReconciliation при общем render exception. [Существующие tests](../../../../../tests/ui/session.test.mjs), строки 195–249, проверяют общий fallback / restart gates, не новый локальный SVG outcome. План правильно отделяет эти два исхода.

**Недостающее evidence / владелец:** Developer / TASK-D-003 — точный port, tagged outcome, lifecycle замены / dispose и trace A→B→отказ/замена; TASK-R-001 — техническое review. Нужен контроль позднего callback / старых listeners после dispose с положительной активацией живого экземпляра. Точный интерфейс Reviewer не выбирает; mounted integration evidence относится к последующей разрешённой реализации.

## 2. Aspect key, uniqueness / canonical order и reconciliation — T003-G02

**Источники:** REQ-WHEEL-04/07/08, AS-WHEEL-28/29/30, DP-O-010/013; plan строки 37–39, 98–104.

**Статические факты:** [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto) задаёт порядок коллекции aspects по engine, но отдельно не обещает лексикографическую ориентацию концов или уникальность тройки. [Projector](../../../../../src/exact_orb/http_api/projectors.py), строки 133–156, переносит from/to и порядок, проверяя опубликованные endpoints. [DTO](../../../../../src/exact_orb/http_api/dto.py) и [validChart](../../../../../src/exact_orb/http_api/ui/response.mjs), строки 17–30, не дают самостоятельного доказательства уникальности ключа.

Текущий natal путь строит точки по config.natal_points ([natal.py](../../../../../src/exact_orb/engine/charts/natal.py), строки 618–631 / 724–745); [finder](../../../../../src/exact_orb/engine/aspects/finder.py) перебирает i<j и выбирает один ближайший допустимый type на пару. [Default config](../../../../../src/exact_orb/engine/aspects/types.py) имеет различные имена; [cosmogram stability](../../../../../src/exact_orb/engine/charts/uncertainty.py), строки 94–165, проверяет уникальный одинаково упорядоченный набор snapshots и сохраняет refs. Это частичное обоснование текущего пути, а не сквозной контракт для всех поддерживаемых источников / restore.

Статический F1: 16 points / 12 houses / 46 aspects, 46 различных `(from,to,type)`, 15 angle-endpoint aspects, категории exact/working/background = 9/20/17. У 28 записей `from > to` лексикографически, например `moon→asc / square`. Порядок коллекции, направление пары и uniqueness — отдельные предпосылки. `aspect_sort_key` зависит от category / orb, поэтому row index не является устойчивым ключом.

**Oracle / данные:** заранее указанная запись DTO A сравнивается с реально разрешённой записью B. В контролируемой UI-копии B той же пары меняются identity, видимые orb / координаты, category на background; порядок меняется согласованно с новым каноническим набором. Выбор сохраняется с фактами B: одна строка / два новых конца, без старой линии / ☌. Expected берётся из входных записей, не production key / reconcile helper. Натал moon→asc → cosmogram без этой записи снимает только исчезнувший выбор и сохраняет раскрытие; failed-read не доказывает исчезновение.

**Независимые positive controls:** выбранная пара реально адресуется в A и B с различимыми фактами; другая пара остаётся адресуемой; C действительно принят и содержит другие points / аспекты. Отдельный point-selection проход. Проверяются related и unrelated переходы point→aspect, обратный aspect→point и background без графики при положительном exact/working контроле.

**Недостающее evidence / владелец:** Developer / TASK-D-003 — явное доказательство uniqueness и устойчивого направления from/to на поддерживаемых путях, связь с контрактом / assertions и правила отсутствующей, неоднозначной или иной по type записи. Reverse orientation / дубликат проверяют допустимость предпосылки, не вводят обязанность принимать произвольные DTO. Нормализацию либо обработку неоднозначности выбирает Developer в reviewed границе; смысловой конфликт передаётся Analyst через Manager. Утверждение candidate key по одному F1 недостаточно.

## 3. Reset, раскрытие таблиц и snapshot collapse — T003-G03

**Источники:** REQ-WHEEL-08/09, REQ-UI-03/09/11, AS-WHEEL-02/13/14/18…22/26/29/30; plan строки 25–30, 39/43, 103–112; DP-O-013.

| Данные / действие | Независимый oracle | Положительный контроль пути |
|---|---|---|
| Accepted новый собственный build по изменённым birth data, committed POST либо подтверждающий recovery GET | Один reset выбора / aspects / houses к 5/5 | B принята и различима в summary / HTML / SVG; собственный явный submit выполнен |
| Automatic current той же / другой identity, выбранная запись существует | Только факты B; выбор / normal expansion / houses сохранены | Выбранная запись присутствует в обоих DTO и изменила видимые значения; GET принят |
| Current без выбранной записи / failed-read отдельно | При принятой C снять только отсутствующий выбор, сохранив раскрытие; failed-read выбор не снимает | C содержит другие реальные записи; парный проход с сохраняющейся записью |
| Повторный publish / phase, old / stale / different recovery, rejected build | Нет повторного reset или выдуманного own-success | После принятия вручную раскрыть таблицы; повторный сигнал реально достигнут; новое разрешённое принятие отдельно сбрасывает |
| Point toggle / aspect toggle при normal-list=5 и all | Point→первые 5; aspect→прежнее раскрытие общего списка без point filter; houses независимы | До выбора реально видны 5 либо весь список, затем одна строка и восстановленный реальный набор |
| Resize / F5 | Resize сохраняет состояние без HTTP, F5 даёт исходное 5/5 | Карта действительно видима после каждого действия; сохранение и reset различимы |
| Submit B, текущие поля C≠B и C=B, включая edit→revert | C≠B открыт; C=B сворачивается; summary относится к B | Обе ветви выполнены, «Изменить данные» возвращает фактические текущие значения |

**Проверенный предел:** session snapshot публикуется неоднократно, source сохраняет последний accept. `source=build/current`, HTTP method или identity сами по себе не задают одноразовое принятие. [recovery.mjs](../../../../../src/exact_orb/http_api/ui/recovery.mjs) различает matched / stale / different / old_or_empty; [mounted assertions](../../../../../tests/ui/recovery.test.mjs), строки 369–387, 442–471, содержат исходные контроли matched-stale / другой вкладки / draft. Они прочитаны, не запускались.

**Недостающее evidence / владелец:** Developer — наблюдаемая связь accepted cause с submitted snapshot / recovery relation и граница однократного применения; separate fresh own result, stale matched, old/different current, already_applied / superseded / late response, repeated publish. Нельзя произвольно приписывать commit попытке только по совпадению birth или GET request_id. При недостатке existing seam Developer доказывает узкий пробел и согласует влияние с Manager. Для порядка используются deferred / fake clock / events.

Collapse сравнивает текущие birth fields с immutable submitted snapshot, включая ветвь edit→revert; historical dirty-флаг сравнение не заменяет. Поздний current не скрывает открытый отличающийся draft, summary не берётся из текущего ввода, ручной gate не подставляется. Схему события / coordinator Reviewer не выбирает.

## 4. Keyboard, focus и recovery — T003-G04

**Источники:** REQ-WHEEL-10/11, REQ-UI-09/10/11, AS-WHEEL-16/19…24/28…30, DP-O-010/013; plan строки 51–55, 74, 103–112.

**Oracle / данные:** F1 / F3 / F4; normal 5/all, point filter / одна строка, совпадающие ☌, collapsed / expanded editor, failed-read / timeout / restart. Без hover пройти keyboard выбор / замену / повтор point и aspect, оба reveal, «Изменить данные» и разрешённое recovery действие. Видимые состояния совпадают с pointer oracle, пара / type / category / orb доступны текстом. Focus видим и принадлежит живому доступному элементу; при выборе планеты нет программного переноса focus / scroll.

**Независимые positive controls:** каждое действие реально активировано клавиатурой и меняет нужные DOM/SVG данные. Background контроль дополнен exact/working графикой. При collapsed editor safe-read доступен и выполняет GET; запрещённый POST дополнен разрешённым ручным POST при действующем gate. Retry-After проходит через fake clock, restart — через явное подтверждение. SVG fault не снимает существующие recovery ограничения.

**Проверенный предел:** [DOM port](../../../../../tests/ui/fixtures/dom.mjs), строки 36–51, при удалении узла меняет parentNode, а activeElement задаёт простым присваиванием. Он не моделирует browser focus при detach, layout / SVG hit testing. Assertion на старый activeElement в этом fake не доказывает живой focus. Нужны реальные connected / visible / reachable controls и последующая активация после фильтра / удаления строки / замены DTO.

**Недостающее evidence / владелец:** Developer / TASK-D-003 — keyboard order, policy при исчезновении активной строки, focus / mobile targets и доступное размещение recovery controls вне сворачиваемых полей; TASK-R-001 — техническая граница, Analyst — смысл при конфликте. Точный DOM приём и численный hit size Reviewer не назначает.

## 5. Состав будущего SVG-spike — T003-G05

**Источники:** REQ-WHEEL-02/05/06/09/10, AS-WHEEL-07…10/16/23/25; plan строки 59–75, будущий промт DEV-WHEEL-01; DP-O-011/012/013/014.

Подтверждаю достаточность предложенного состава как основы будущего измерительного задания: sparse / F1 / F3 / F3-max, пять R через 0°, 16 IDs, несколько подписанных ☌, close angles, 1440/768/360, actual font / scale, pointer / keyboard. Manager §2.11 уже создал будущую TASK-D-003; её исполнение требует отдельного точного InputSHA, оценки / сроков и допуска. Историческое «не назначен» в Developer v2 относится к его snapshot.

**Oracle / данные:** отдельно фиксируются истинные anchors, отображаемые glyph / R / category text / selected contour / hit bounds; согласованные определения collision / minimality / readability / допустимых bounds. Порядок и ID→anchor→label/hit mapping сравниваются исходным данным, включая seam / одинаковые долготы / tie-policy. Четыре относительные стороны 0/90/180/270 = left/bottom/right/top и фактический natal ASC проверяются независимой таблицей; sign / category / orb не пересчитываются.

**Независимые positive controls:** реально отрисованный sparse имеет нулевой сдвиг / выноски; конфликтующая группа действительно пересекается по независимому bbox замеру, далёкая точка не меняется. Все пять R и разные ☌ адресуются, non-R не имеет R; exact/working/selected/unselected/background различаются парно. Реальный keyboard / pointer выбирает каждый проверяемый объект, HTML того же DTO доступен.

**Обязательное будущее evidence:** criterion→fixture→actual→вывод; воспроизводимые команды / SHA / run, browser/version, viewport / zoom/scale, фактически загруженный font, численные координаты / bbox и screenshots одного прохода, reachability / focus. Expected не копируется из placement helper либо prototype spread(). Формализацию минимальности и независимое сравнение предлагает Developer; Tester проверяет чувствительность критерия. Наблюдаемый предел / fallback при недостижимости принимает Owner через Analyst.

До 0,75 чд — предложение только для эксперимента, включённое в Developer 5–7 / 8–12 чд. Полный TASK-D-003 с критериями / ADR / sequences требует отдельной оценки. Остановка по evidence либо timebox; при неуспехе — конкретный counterexample / переоценка, без скрытия объектов или молчаливого принятия пересечений.

**TEST-FIND-WHEEL-002 остаётся OPEN:** измерений / окончательного oracle нет, условия [единственного реестра](defects.md#test-find-wheel-002) не выполнены. Состав будущего spike не является его результатом. Прежние closures 001/003 сохраняются.

## Handoff Manager, влияние и повторная передача

Подтверждение относится к проверяемости предложений v2 по v3. T003-G01…05 — условия технического пакета по существующим DP, не дублирующие TEST-FIND-*.

Developer / TASK-D-003 передаёт точный TechnicalPackageSHA с port / failure evidence, proof ключа, accepted cause / snapshot seam, focus policy, критериями / измерениями и проектом drawing ADR / technical sequences. TASK-R-001 выполняет техническое review; Analyst получает смысловой конфликт, Owner — необходимый выбор наблюдаемого предела. Затем Tester адресно проверяет этот пакет.

Открытые technical / measurement вопросы уже отражены в условиях v2. Нового противоречия scope не установлено; оценка TASK-T-003 3–4 часа сохраняется. Прежние 3–5 чд независимого тестирования здесь заново не утверждаются. Изменение предела / fallback либо недостаточность acceptance seam требует переоценки ответственной роли по новому evidence.

Manager отдельно регистрирует точную опубликованную версию и проверяет полноту / traceability в своём предмете. DONE / APPROVED / gates / runtime readiness этим review не объявляются. Автор STARTED и согласование сроков сохранены; Manager-сводка не редактируется.

## Фактические проверки и предел

- `git fetch origin change/ui-chart-wheel test/ui-chart-wheel` — exit 0; HEAD начала 26b11e8, origin/change f0a58a5, origin/test 26b11e8.
- `python -X utf8 -` — статический audit через stdin: `TASK_T003_INPUT_AUDIT_OK`, 42 source hashes, manifests 9/9 + 9/9, 5 recommendation cells; статический разбор F1 приведён выше. После исправления чтения фактического list Analyst manifest итоговая проверка прошла.
- `git diff --exit-code --quiet f9c70f75ea815b2f3bf7e01426ee5afe65b31606 HEAD -- docs/project_management/change_plans/ui-chart-wheel/developer docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md` — exit 0.
- `git diff --exit-code --quiet 2634b224894b1046113557bfe241f0a5f2d46f8c HEAD -- docs/project_management/change_plans/ui-chart-wheel/analyst docs/project_management/change_plans/ui-chart-wheel/analyst_artifact.md` — exit 0.
- `git diff --exit-code --quiet 7e95c0f680cc790fc8b45d9e25d69cc6e94fbc12 HEAD -- docs/project_management/change_plans/ui-chart-wheel/tester` — exit 0 до добавления материалов TASK-T-003; прежние файлы затем проверены отдельно.
- `git diff --exit-code --quiet 535551026af6eedaf2a0aa5c0daa96fa94655ec1 HEAD -- src tests docs/requirements docs/sequence_diagrams docs/development_approach` — exit 0.
- `python -X utf8 -` — финальная документальная проверка через stdin: source/output hashes, неизменность прежнего Tester-индекса / evidence и Manager, scope, ссылки / таблицы; `TASK_T003_REVIEW_DOC_OK`.
- `git diff --check` / `git diff --cached --check` — exit 0 перед публикацией.

Pytest, Node tests, browser / HTTPS, SVG-spike и PUML render не запускались. Future controls остаются NOT RUN. Production, tests, требования, чужие артефакты и решения Owner не изменены. Публикация отдельно разрешена Owner; её commit и успешный push подтверждаются Git, не статусом runtime.
