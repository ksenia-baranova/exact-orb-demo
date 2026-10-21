# TASK-T-005 — предстартовое review критериев TASK-D-003

**Автор / подпись:** Codex / Tester, 2026-10-17.
**Вывод:** требуется исправление T005-R01…R03. Редакция критериев @ 11a703e пока не даёт однозначного основания начать измерительный эксперимент. Числа и параметры исследования уже согласованы Owner и здесь не меняются.
**Предмет:** измеримость / достаточность критериев до эксперимента. Фактическая достижимость, runtime PASS, TASK-T-004 и техническое принятие не проверялись.

## Входы, разрешение и оценка

| Источник | Точная версия |
|---|---|
| Опубликованное назначение / Owner-согласование, Manager §2.13 / DP | `50cb4cc46f76bd1430b8dfc552c1e14ed32bf65d` |
| Общий ReviewInputSHA | `49b9d7ce58be8171ee0159643f9f085afe090972` |
| Предмет — [Developer plan TASK-D-003](../developer/task_d003_implementation_plan.md) | `11a703ed6a01eb368f0f0ba23dc23f1e90fac81f` |
| Принятое [Tester-review TASK-T-003](task_t003_review.md) | `c59cc3f68e7769841134801dc125633decade032` |
| Analyst [requirements](../analyst/requirements.md) / [scenarios](../analyst/scenarios.md) / behavioral sequences | `2634b224894b1046113557bfe241f0a5f2d46f8c` |
| Нормативный baseline существующего контракта / code / tests | `535551026af6eedaf2a0aa5c0daa96fa94655ec1` |

[Manager §2.13](../manager_artifact.md) / DP-O-010…013 @ 50cb4cc содержат Owner-согласование рабочей редакции для исследования: полный объём 20–28 ч, эксперимент ≤6 ч внутри, ответ ролей за один рабочий день с подтверждением их собственной оценки. Исторические слова «кандидат / не согласованы» в плане @ 11a относятся к его публикационному snapshot; они не повод повторно запрашивать тот же Owner-выбор.

До STARTED сообщил собственную оценку **2–3 рабочих часа**, confidence средняя, и подтвердил возможность целевого ответа за один рабочий день после передачи поручения. STARTED — 2026-10-17 21:25:11 MSK (18:25:11 UTC), событие в [Tester-индексе](../tester_artifact.md). Эскалация Manager → Owner через один рабочий день просрочки. Согласование не запрашивалось повторно.

Работа ведётся в назначенном worktree / ветке test/ui-chart-wheel. HEAD до обновления c59cc3f68e7769841134801dc125633decade032; после fetch / fast-forward — 50cb4cc46f76bd1430b8dfc552c1e14ed32bf65d. До / после интеграции index и дерево чистые; прежние stash сохранены. HEAD назначения не заменяет предмет плана 11a / ReviewInputSHA 49b9.

Порог anchor ≤0,5 CSS px, gap ≥2 CSS px, локальный шаг 1 CSS px, glyph 16 / R-category 12 CSS px, zoom 100%, hit target 44×44 CSS px, матрица 1440/768/360 и предел эксперимента ≤6 ч приняты как рабочие параметры исследования. Возврат касается определения измеряемых величин, допустимых областей и чувствительных controls. Глобальный оптимум, новые числа и расширение бюджета не предлагаются.

## Проверка критериев

Каждая строка задаёт будущую проверку; эксперименты / калибровочные controls в этом review не исполнялись.

| Критерий / источник плана | Oracle | Данные и независимый control | Недостающая определённость / evidence, владелец | Вывод |
|---|---|---|---|---|
| C01 — один источник / адресуемость / anchors, строка 61; T003-G01/G02 | Исходный DTO, заранее заданные ID / пары и независимая геометрическая таблица, cardinals / истинный ASC; ноль лишних / пропущенных записей, anchor ≤0,5 CSS px | F1, A→отличимая B, natal / cosmogram, exact/working/background, selected-only; позитивно выбран реально доступный объект; отрицательно пропуск ID / смещение anchor сверх порога / зеркальное отображение | Точный CSS reference / метрика anchor error — T005-R01; настоящий независимый verifier и source-wide proof ключа — Developer, после старта / TASK-T-004 | Дизайн независимого oracle пригоден; координатное уточнение до эксперимента |
| C02 — collision / bounds / gap / clipping / displacement region, строки 62/68 | Зафиксированный screen-space geometry contract для объединения ink / R / text / contour / stroke / focus, gap ≥2, явная допустимая область / clipping; hit измеряется отдельно | Sparse default без конфликтов, независимый overlap F3, далёкая точка неизменна; отрицательные diagonal-gap / clip / forbidden-region controls R01 | Нет однозначных метрики gap / вида bounds, областей смещения и clipping — Developer + Analyst по смыслу, DP-O-011/012/013 | Требуется T005-R01 |
| C03 — локальная минимальность шагом 1 CSS px, строка 63 | Для каждого смещённого label отдельный verifier проверяет допустимое приближение на 1 CSS px и все фиксированные ограничения, не запускает placement | Реально конфликтующая исходная пара; синтетический независимый контроль boxes: 18 accepted, 20 rejected, уменьшенное 19 также rejected до минимального 18; sparse shift=0 / leaders=0 отдельно | Не определены admissible move / состояния ограничений; «уменьшенный допустимый принимается» не задаёт минимальный positive control — T005-R02; Developer, Analyst проверяет смысл локального правила | Требуется T005-R02; глобального оптимума не требую |
| C04 — glyph / R / category / contour / фактический font, строка 64 | Явно названная величина для согласованных 16/12 CSS px, actual font / fallback / missing glyph, раздельные bounds normal / selected / focused и подписи ☌ | Пять R и non-R, несколько разных ☌, пары exact/working/selected/unselected/background; отрицательные missing-glyph / clipped contour / неверный размер | Не названа метрика размера glyph/R: CSS font-size или ink height / иная величина — T005-R03; фактический font / browser фиксирует Developer при разрешённом исследовании | Требуется T005-R03; отсутствие ещё не выполненных font measurements само по себе не новый finding |
| C05 — pointer / mobile hit target, строка 65 | Эффективная активируемая область по рабочему 44×44 CSS px, после transform / clipping / overlay; ID фактического browser target | Настоящее coordinate pointer действие выбирает каждый point / ☌, другой объект и снимает выбор; отрицательный перехват off-centre, positive без перехвата, border / overlap checks | Точную hit shape / набор проб / способ фиксации попадания описать в техническом measurement contract R01; actual evidence — Developer / TASK-T-004; примечание T005-N01 | Состав действий пригоден; bbox и programmatic click не доказывают effective target |
| C06 — keyboard / живой focus / recovery, строка 66 | Accessible / connected / visible / reachable control и последующее действие, pointer-equivalent semantics, нет auto focus/scroll для point; действующие recovery gates | Сохранённая и удалённая активная строка, DTO replacement / filter / collapse; Enter/Space реально меняют состояние; разрешённый safe GET и парный ручной POST с gate; failed / Retry-After через fake clock | Конкретная focus policy — ожидаемый результат T003-G04, не готовая production реализация; evidence isolated trace и будущий mounted trace различаются; Developer, Analyst / Technical Reviewer по своему предмету | Проверяемый состав достаточен; browser evidence впереди |
| C07 — sparse / F1 / F3 / F3-max × 1440/768/360, строки 70–76 | Coverage ledger связывает fixture hash / действие / criterion / expected / actual / вывод и run metadata, не выдаёт NOT RUN за PASS | 12 базовых сочетаний, pointer и keyboard; sparse/F3 парно, seam / ties / R / несколько ☌ / close angles, natal/cosmogram cardinals; негативные контролируемые нарушения R01…R03 | Конкретные controlled copies / tie cases фиксируются до первого measurement внутри разрешённого бюджета; Developer. Истинность астрономического расчёта этими UI-копиями не проверяется | Состав матрицы достаточен; недостижимость плотности не доказана |
| C08 — T003-G01…05 и isolated / mounted граница, строки 45–53 / 100–106 | G01 port/dispose/outcome; G02 build/restore/cosmogram key proof; G03 accepted cause/snapshot/reset; G04 focus/recovery policy; G05 measured graphics. Для каждого известен предел evidence | G01 A/B / fault / live replacement; G02 существующий/исчезнувший key с новыми фактами; G03 own acceptance / repeated publish / late draft; G04 живой keyboard/recovery; G05 sparse/dense calibrated controls | Техническое обоснование / isolated evidence ещё должен дать Developer; production integration / candidate / mounted checks остаются будущими заданиями. TASK-T-004 и TASK-R-001 отдельно | Разделение корректно; незапущенное исследование и будущие mounted checks не объявляю выполненными |

## T005-R01 — не зафиксирован geometry / measurement contract

**Источники:** plan строки 61–62/65/68/74; REQ-WHEEL-02/05/06/09/10, DP-O-011/012/013/014.
**Влияние:** два независимых verifier могут дать разные исходы на одном и том же наборе координат. До положительного вывода о готовности к эксперименту нужна конкретизация.

В плане перечислены screen transform, объединение glyph/R/category/contour/stroke/focus и gap, но не зафиксированы:
- система координат / reference point каждого true anchor и label displacement, метрика ошибки ≤0,5 CSS px;
- измеряется ли union отдельных областей или её enclosing box, какая gap-функция применяется и когда граница ровно 2 считается выполненной;
- области допустимого смещения / границы кольца и какие элементы / состояния normal, selected, focused входят в constraint;
- effective clipping от SVG / viewBox / контейнеров и допустимая область hit targets; отсутствие overflow всей страницы не заменяет clipping отдельного SVG.

**Конкретные аналитические контрпримеры:** A=[0,16]×[0,16], B=[17,5;33,5]×[17,5;33,5] в CSS px. Евклидово расстояние между boxes ≈2,12 проходит gap=2; проверка пересечения boxes с axis padding даёт иной исход. Ещё пример: glyph bbox x=[292,308] умещается в странице шириной 360, но clip контейнера [0,300] скрывает 8 px. Успешный document-width check сам по себе clipping не доказывает. Это заданные геометрические схемы, не результаты браузерных измерений.

**Условие исправления:** Developer фиксирует measurement contract / допустимые области и единый формат исходных CSS anchors / bounds / clip metadata до запуска. Verifier применяет этот заранее записанный контракт; положительные ровно-допустимые и отрицательные gap / forbidden-region / clip controls имеют явный expected. Tester проверяет чувствительность. При изменении наблюдаемого обязательства — Analyst / Owner по конкретному примеру; повторное согласование тех же чисел не требуется.

## T005-R02 — локальный verifier и positive control минимальности не доопределены

**Источники:** plan строка 63 и незакрытые definitions строки 68; REQ-WHEEL-05, AS-WHEEL-09/10, DP-O-011; смысловую сверку выполняет TASK-A-003.
**Принято:** локальная проверка шагом 1 CSS px. Это не требование глобального либо субпиксельного оптимума.

**Конкретный аналитический контроль:** obstacle box=[0,16]×[0,16], default label box совпадает с ним; допустимо горизонтальное смещение вправо в области, содержащей рассматриваемые boxes. Gap=2:
- label=[18,34]×[0,16]: gap=2, шаг влево 1 даёт gap=1 — local-minimum control принимается;
- label=[20,36]×[0,16]: gap=4, шаг 1 даёт gap=3 — избыточный сдвиг отвергается;
- уменьшенный label=[19,35]×[0,16]: gap=3, шаг 1 даёт gap=2 — он допустим, но ещё избыточен и также должен отвергаться.

Фраза «уменьшенный допустимый сдвиг должен приниматься» без точного конечного control допускает принятие 19. Сама проверка feasibility ещё не подтверждает local minimality. Пример служит калибровке verifier; algorithm / SVG здесь не исполнялись.

Также шаг «к true anchor» должен быть определён относительно допустимого движения. Если допускается движение по дуге, прямой CSS шаг к anchor может выйти из разрешённой области и ошибочно выдать любой большой сдвиг за минимальный. При radius=100, anchor=(100,0), candidate=(0,100) прямой шаг даёт примерно (0,707;99,293), уже не на окружности, хотя допустимый короткий шаг по дуге мог бы уменьшить избыточное смещение. Предположение о дуге здесь — различающий пример для пока не заданной области, а не выбранный Reviewer алгоритм.

**Условие исправления / владелец:** Developer задаёт admissible probe / направление / ограничения и точные PASS/FAIL калибровочных примитивов. Остальные labels / anchors и frozen elements при пробе не перестраиваются; заново измеряются / вычисляются только заданные последствия перемещения проверяемого label для всех согласованных constraints. Independent verifier потребляет input anchors / measured geometry / contract, не вызывает и не копирует поиск placement helper. Negative over-shift должен быть отвергнут именно по возможности допустимого шага, positive граничный — принят из-за конкретного нарушаемого constraint. Субпиксельные / более короткие, чем 1 CSS px, остатки явно описать как предел рабочего критерия, не придумывая новый порог. Analyst подтверждает смысл локального правила, Tester — чувствительность controls.

## T005-R03 — для 16/12 CSS px не названа проверяемая величина

**Источники:** plan строка 64; REQ-WHEEL-05/06/10, DP-O-011/012.
Согласованные значения 16 / 12 не определяют сами по себе, проверяется CSS font-size, ink height / glyph bbox либо другая величина. Измерение actual font, glyph/R/category/contour и hit bounds должно быть раздельным.

**Конкретный различающий пример:** CSS font-size=16 при фактическом ink bbox height=12. Predicate по font-size принимает его, predicate по ink height≥16 отвергает. Аналогично nominal size и ink height R/category могут различаться. Это условный measurement record, не заявленный факт о шрифте стенда.

**Условие исправления:** Developer называет величину / размерность для каждого порога, как учитываются fallback / missing glyph, scale, выбранный contour и focus; указывает положительный record на согласованной границе и отрицательный ниже неё. Фактически выбранные font / browser / glyph bounds фиксируются при разрешённом эксперименте, а не выдумываются сейчас. Если уточнение меняет согласованный наблюдаемый смысл — адресный пример Analyst / Owner через Manager. Числа Reviewer не меняет.

## T005-N01 — чувствительный контроль effective hit target

Рабочий 44×44 CSS px сохраняется. В протоколе измерения нужно отделить enclosing bbox от фактически активируемой области и native coordinate hit testing от programmatic element.click()/dispatchEvent, которые могут обходить перекрытие.

**Контрпример для будущего negative control:** у target bbox 44×44, но работает лишь узкая полоса / центральная область, либо соседний overlay перехватывает off-centre точку. Проверка одного центра и bbox даёт ложную уверенность. Нужны declared hit shape / точки native pointer-проб, actual event target / canonical ID, проверка clipping / overlap и парный контроль того же target без перехвата. Developer определяет этот протокол в рамках R01 / T003-G04/G05; Tester проверяет его на TASK-T-004. Это не требование нового размера или нового продукта и не доказательство уже существующего UI-дефекта.

## Evidence, изолированный эксперимент и будущая production проверка

Достаточен предусмотренный состав артефактов: fixture hashes / run ID, browser/version / ОС / viewport / DPR / zoom, SVG viewBox / CSS size / screen transform, actual fonts / fallback, measured anchors / union-component bounds / contour / hit / focus / displacement / leaders, screenshots и criterion→expected→actual→вывод. Для geometry, control и изображения одного run должны совпадать данные и версии. Verifier должен быть отдельно проверяемым потребителем этих данных; декларация независимости сейчас не является выполненным proof кода, которого ещё нет.

Матрица 4 набора × 3 viewport даёт 12 базовых сочетаний; pointer и keyboard — отдельные проходы. State-pairs normal/selected/focused, R/non-R, exact/working/background, retained/disappeared selection дополняют покрытие соответствующих критериев. Фиксируются фактически выполненные / NOT RUN клетки. Неуспех / timebox ≤6 ч допускает точный counterexample и неполную матрицу; это не доказывает недостижимость неисполненных клеток и не разрешает fallback.

G01…04 должны дать техническое обоснование / policy и чувствительные controls. Isolated harness может доказать свой port / fault / focus trace и реальную графику. Он не доказывает production coordinator / collapse / HTTP recovery / mounted UI, которые не изменяются в TASK-D-003. Эти ограничения в плане разделены правильно; отсутствие будущего mounted evidence само по себе не причина возврата TASK-T-005. TASK-T-004 проверяет фактический технический пакет после исследования, TASK-R-001 — границу / проект ADR; текущая работа их не заменяет.

TEST-FIND-WHEEL-002 остаётся OPEN. Реальных измерений / выполненного эксперимента нет; критерии его closure не выполнены. Принятые handoffs / closures 001/003 / evidence TASK-T-002 и TASK-T-003 не изменены.

## Владельцы, влияние и повторная передача

| Замечание | Владелец / связи | До повторного положительного вывода |
|---|---|---|
| T005-R01 | Developer; DP-O-011/012/013, Analyst — смысл | Geometry / coordinate / gap / displacement / clipping / hit contract и различающие controls |
| T005-R02 | Developer; DP-O-011, TASK-A-003 — смысл локальной минимальности | Admissible 1 CSS px probe, независимый verifier contract, positive/negative primitives с однозначными expected |
| T005-R03 | Developer; DP-O-011/012, Analyst при смысловом конфликте | Явная метрика 16/12, правила font / glyph / contour measurements и граничные controls |
| T005-N01 | Developer; T003-G04/G05 / TASK-T-004 | Native hit / actual target controls как часть measurement protocol, без изменения 44×44 |

Уточнения входят по смыслу в предусмотренную подготовку / согласование критериев (3–4 ч Developer). Реальный расход неизвестен, изменение оценки Developer за него не назначается. 20–28 ч, ≤6 ч эксперимента и прежние 8–12 чд не суммируются и не увеличиваются этим review. Если исправления / дополнительный цикл не укладываются в допущения, Developer сообщает Manager конкретное влияние / переоценку.

**Повторная передача:** Developer публикует исправленную редакцию плана / критериев с exact SHA, ответами на R01…R03 и expected controls; Manager передаёт её Tester на адресную сверку, Analyst подтверждает свой предмет TASK-A-003. Запускать измерение для подтверждения этих недоопределённых критериев до исправления не следует. Текущий отрицательный вывод не выполняет условие положительного предстартового TASK-T-005 из Manager §2.13; статусы и условный допуск регистрирует Manager, Tester их не меняет. Пересогласование уже принятых Owner параметров не запрашивается.

## Фактические проверки

- `git fetch origin change/ui-chart-wheel test/ui-chart-wheel` — exit 0; `git merge --ff-only origin/change/ui-chart-wheel` — exit 0, c59cc3f→50cb4cc. `git status --short --untracked-files=all` до / после интеграции — пусто.
- `python -X utf8 -` — собственный read-only input audit через stdin: `TASK_T005_INPUT_AUDIT_OK`. Пять закреплённых commits доступны / предки assignment; primary plan совпадает с blob @ 11a. Исторические manifests Developer v2 @ f9c70f7 / Analyst v3 @ 2634b22 — 9/9 каждый; 42 source hashes TASK-T-003 проверены по записанным entry SHA; output hashes T003 — по c59, три preparation output hashes — по 11a. Исторический Manager-only delta проверен на material_input / manager_registration из audit, не на новом HEAD.
- Исторический Developer checker, который требует Manager @ 0083d81 и локальный preparation scope, не запускался на новом HEAD; его saved audit не перезаписывался и не подгонялся под 50cb4cc.
- `python -X utf8 -` — финальная read-only документальная сверка через stdin: `TASK_T005_REVIEW_DOC_OK`, source/output hashes, сохранность предыдущего индекса / старых Tester-файлов, scope, links / tables / required review fields.
- `git diff --check` — exit 0.

Все counterexamples выше аналитические, не runtime measurement. Pytest, Node tests, SVG / browser / font / focus / pointer эксперименты, screenshots, HTTPS smoke и PUML render не запускались. Production, Developer / Analyst / Manager и Owner решения не изменены. Commit / push / PR не выполнены: поручение на публикацию TASK-T-005 отдельное. Handoff подготовлен локально; Manager получает точный результат только после разрешённой публикации Git-ветки, не через чужой worktree или сообщение в другой чат.
