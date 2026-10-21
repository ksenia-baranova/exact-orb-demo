# TASK-D-007 — композиция v2 и режим выбранного аспекта

**Codex / Developer,20.10.2026, DRAFT / локально.** Owner source: feedback с двумя screenshots в текущем чате и уточнение «Да: две планеты и только их дома». InputSHA/HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, branch dev/ui-chart-wheel. Прежние изменения/индекс/STARTED сохранены. [План §9](../../full_wheel_implementation_plan.md#9-task-d-007--исправления-композиции-по-owner2010), [пакет06](../../prompts/06-owner-composition-aspect-view.md), [ADR](../../drawing_adr_column_draft.md), [sequence006](../../sequence_diagrams/ui/006-aspect-reading-mode.puml).

## Что исправлено

1. В старом SVG не было house numbers; теперь source houses1…12 имеют отдельный пояс, номера и source cusp boundaries. Midpoint между последовательными опубликованными cusp_longitude служит reference подписи, не новым вычислением принадлежности точки дому. Aspect circle больше прежних0,27R на широком рисунке; zodiac получает360 делений.
2. Композиция использует до1440px страницы, колесо до940px, на≤1024px блоки складываются. Для выбранного аспекта ширина зависит и от доступной высоты; SVG остаётся1 CSS unit, шрифты не уменьшаются viewBox scale.
3. Aspect action переносит focus на HTML region колеса и прокручивает к нему. Текущая SVG-публикация завершает scroll после reflow только при том же key/activeElement. Selected mode показывает одну строку аспекта, его endpoint point rows и distinct source houses. SVG оставляет соответствующие endpoints и house sectors; Escape/кнопка восстанавливают полный вид, прежние раскрытия и живой originating control.
4. Углам и unknown-time points дом не назначается. Full-DТО S1 остаётся до display subset, source rows не дедуплицируются. Automatic invalid/ambiguous address закрывает выбранный вид и показывает полный источник. Planet action сохраняет no-focus/no-scroll. Recovery controls доступны и при скрытой форме.

Второй Owner screenshot явно показывает browser zoom50%. Это причина уменьшенного всего интерфейса; Ctrl+0 возвращает100%. App не меняет пользовательский Yandex-профиль и не компенсирует настройку удвоением CSS. Native проверки ниже выполнены при zoom1, widths1440/768/360, heights1000 и640.

## Команды и actual

Workdir C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered.
Node = C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe; Python pytest = global Python3.14. Chrome155.0.8059.40 / Windows.

~~~powershell
node --test tests/ui/aspect_view.test.mjs tests/ui/chart_selection.test.mjs tests/ui/wheel_layout.test.mjs
#20 PASS,0 FAIL; сначала новые mounted tests дали3 FAIL на существующем приложении

$nodeTests = @(rg --files tests/ui -g '*.test.mjs')
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' --test @nodeTests
#220 PASS,0 FAIL;494,13ms на окончательном UI

python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q
#53 passed;18,77s, включая installed-wheel delivery
python -m pytest -q
#2959 passed,1 skipped;150,32s
#skip: существующий DEBT-CALC-001, tests/test_configurations.py:473

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/browser.cjs ../task_d007_composition_v2/native03
#35/35 compositions +37/37 boundary controls,exit0
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/audit_geometry.py native03
#35/35 independent native audits +7/7 analytic controls,exit0

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/browser.cjs focus05
#12/12 cases,290/290 assertions;1440/768/360,height1000
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/compact.cjs compact01
#2/2 cases,49/49 assertions;height640
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/angles.cjs angle01
#2/2 cases,53/53 assertions;one source point +one source angle

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/audit_package.py
git diff --check
~~~

## Критерий → данные → actual

| Критерий | Данные / witness | Actual |
|---|---|---|
| Номера/границы домов, ruler, orientation / все source points/R | [native03](native03/actual.json), [focus05](focus05/actual.json), source DTO и native bbox/anchors/CTM/font;35 fixtures включая empty/cosmogram/S1/palette/exact-tie/DPR2/fallback |35/35 compositions. Natal12 numbered houses/12 source cusps, cosmogram0;360 ticks. На широкой композиции aspect circle>0,55R |
| Gap2, clipping, C0/frozen, column order, local contact, no shared leader segments | [independent audit](native03-independent.json), Fraction actual binary64; house references независимо из source cusp midpoints |35/35+7 controls. Verifier не вызывает layout. Virtual house reference не выдаётся за астрономическую point; её номер/границы только из source |
| Selected view / source two endpoints и их дома | focus05 12 cases; compact01 2; angle01 2 |16/16 cases,392/392 assertions:1 visible aspect row; ровно point endpoints и их distinct published house numbers; SVG subset согласован. Angle case1 point+1 angle, без выдуманного house |
| Focus и scroll / whole wheel fits | native activeElement=chart-wheel, getBoundingClientRect wheel/toolbar/viewport, sticky return, Escape/close native action |Весь выбранный SVG внутри viewport, toolbar не закрывает его; focus возвращается на live source button, формы/summary/intro скрыты только когда не нужен recovery |
| Recovery/S1/restore | Controlled HTTP error→manual safe GET, later reversed source duplicate; действительные main/session/facts/controller/leaf |Recovery доступен, focus живой после скрытия recheck. S1 снимает неоднозначный выбор, все source rows сохранены. По выбору/снятию HTTP не добавляется |
| Renderer lifecycle | native03 boundary, прежний leaf-independent harness без изменения исходных файлов |37/37 current/stale/replace/dispose/copy/whitelist/fatal controls; тот же protocol |
| Доставка / архитектура / baseline |53 target Python,full2959+1 |Текущие index/UI modules доставляются и в установленном wheel. Engine/API/projector/golden/dependencies не менялись |

Selected/cosmogram positive control использует существующий tests/http_api/golden/chart_dto.json cosmogram с2 source points и1 aspect. Пустая cosmogram из research data отдельно сохранена в native35; в неё аспекты не добавляются ради теста. Natal/F3-max/palette source fixtures берутся из прежнего column_full_composition_v1/data.json. Вся сеть в browser controls листовая контролируемая; настоящие UI/state/layout/renderer не мокались.

Полные screenshot: [обычная карта1440](focus05/published-natal-1440-full.png), [обычная карта360](focus05/published-natal-360-full.png), [выбранный аспект1440](focus05/published-natal-1440-selected.png), [360](focus05/published-natal-360-selected.png), [высота640](compact01/published-natal-1440-selected.png). Финальные normal/selected просмотрены визуально. Source LF SHA256 в каждом actual.json; [package audit](audit.json) сверяет их с текущими UI-файлами.

## RED / промежуточные результаты и пределы

-3 новых mounted tests сначала упали на старом поведении focus/full tables, затем3/3 GREEN. Новый house-sector test проверяет wrap350°→20°=5° midpoint и исходные source numbers, без определения домов точек.
- Initial scroll попадал до появления нового SVG: native focus01 показал wheel top111px и нецелый круг. Теперь scroll завершается после текущей публикации и учитывает toolbar; guarded continuation не возвращает ушедший focus.
- focus01/02 пытались нажимать скрытый show-all у F3 с≤5 строками; исправлен harness, продуктовый контракт не менялся. Research cosmogram без aspects не была позитивным fixture для выбора: вместо добавления фактов использован существующий public golden cosmogram. Raw прежних попыток сохранены.
- native01:35/35 compositions, но загрузка controls page истекла до boundaryReady. Отдельный boundary01 и окончательные native02/native03 дали37/37,exit0. Это не hidden runtime PASS первого job.
- Предыдущие task_d007_runtime и task_d007_dark_theme файлы/JSON/manifests не перезаписаны; baseline закрепляет их raw SHA256. Старые manifests не объявляются версией текущего кода.

Не проверены другие engines/ОС/real mobile/screen reader, произвольные browser zoom и полная universal geometry/SLA. PUML — structural check, без render. Нормативный перенос/independent Tester acceptance не выполнялся. На live HTTPS проверена доставка актуальных assets/готовность, отдельный расчёт POST этим заданием не запускался.

Локальный index EMPTY, HEAD прежнийe0daa0e, новый CandidateSHA/OutputSHA отсутствует. Commit/push/merge/PR не выполнялись.
