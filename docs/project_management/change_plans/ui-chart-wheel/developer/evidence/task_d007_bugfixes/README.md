# TASK-D-007 — исправления Owner bugs004…008

Codex / Developer,20.10.2026. Прямой ответ Owner: **«Исправить все баги и доработки»**. Scope:reports004…008 и2доработки007,без historical001…003. InputSHA/HEAD `e0daa0e814d3d1fd34cadb8c17d064f19c4810f5`,branch `dev/ui-chart-wheel`,index пуст. [Baseline](baseline.json),[пакет08](../../prompts/08-owner-bugfixes.md),[findings/current result](../../findings.md#owner-bugfixes-2026-10-20),[план§11](../../full_wheel_implementation_plan.md#11-task-d-007--исправление-owner-bug-reports004008),[DRAFT ADR](../../drawing_adr_column_draft.md),[sequence008](../../sequence_diagrams/ui/008-viewport-legend-vectors.puml).

## Исправления и evidence

| Report | Root cause / изменение | Проверка |
|---|---|---|
|004:Yandex,start | Форма была max560px внутри wide1440px с левым размещением. Main form mode ограничен680px и центрирован. Реальный browser50% не приложение:настройки профиля не сброшены,компенсация CSS x2 не введена | Chrome155/Yandex26.8 clean default100%,input16px/центрирование/no overflow;исходный пользовательский50% требует отдельного profile retest |
|005:Chrome,circle | Normal frame учитывал только ширину. Теперь940px/100svh−160px,aspect100svh−200px для переноса toolbar;mobile wheel передsummary. SVG CSS pixels1:1 |16native app cases,2height-only resize cases;circle fits,selection сохраняется,no extra HTTP |
|006:legend | Был только общийparagraph. Добавлены7цветныхtype samples из той же ASPECT_COLORS,☌ отдельно,solid/dashed категории. Full legend слева,aspect legend приwheel |2pureRED→GREEN;7entries,computed colors=actual palette;accessible text,no hover dependency |
|007:table alignment | top-aligned td+44px button с padding8px смещали имя. Middle alignment,button padding0,font inherit;table auto/content-sized,cells4px12px | Actual short-row text Range centers равны;row53px vs≤56expected,table489.734375px in desktop fixture;targets≥44px |
|007:Owner deltas | ИмяЮжныйузел без «(производная позиция)»,без удалениястроки/derived semantics;компактные ячейки/отступы | Exact name/source row assertion,allfacts retained,canonical source IDs/order untouched |
|008:symbols | Unicode existence не гарантирует узнаваемость. Selena○ не Р3. Chiron/ParsFortune/Selena теперь реальные векторы по указанному Р3,16-unit native geometry,getBBox,immutable definitions;whitelist толькоdata-symbol | Real visible path/circle shapes,positive source labels/all16points,35compositions+native glyph metrics,DPR2/fallback;[эталон Р3](../dev_find_wheel_008_symbols/r3-symbols-reference.png) |

Дополнительный исправленный regression:при первоначальном chart_ready snapshot мог запомнить узкую ширину form mode ещё до editor collapse,давая transient house-rows-capacity. Теперь page mode выбирается по accepted view до first snapshot через существующий callback. Прежняя once/modified-draft/editor policy не меняется. Public onDrawingEvent наблюдение подтверждает actual install-copy и отсутствие svg-unavailable на всех natal clean-start/height-resize cases;позитивный контроль проверен package audit.

## Точные команды и результаты

Рабочая папка `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered`. Ниже `node` — сокращение фактически использованного `C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`. Pytest — глобальныйPython3.14. Playwright уже bundled,новых зависимостей нет. Chrome executable155.0.8059.40;Yandex executable26.8.5.811,reported browser.version26.8.0.0.

| Команда | Actual |
|---|---|
|`node --test tests/ui/owner_feedback.test.mjs tests/ui/facts.test.mjs tests/ui/aspect_view.test.mjs`|37passed;new2tests RED before code,thenGREEN |
|PowerShell:`$nodeTests=@(rg --files tests/ui -g '*.test.mjs'); & node --test --test-reporter=dot @nodeTests`|227passed,exit0 |
|`python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q`|53passed,16.13s on final source |
|`python -m pytest -q`|[2959passed,1existing skip DEBT-CALC-001,145.08s](pytest-final.log) |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_bugfixes/browser.cjs run04`|[16/16cases](run04/actual.json),Chrome/Yandex,1882/1440/768/360,width/height1068/1000/900/800/640;centering/circle/legend/table/real vectors/targets/errors |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_bugfixes/browser.cjs resize02 --resize-only`|[2/2cases](resize02/actual.json);height900→640,selectedMoon retained,zero API calls,computed sample colors match palette,no transient failure |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_house_rows/browser.cjs ../task_d007_bugfixes/native03`|[35/35](native03/actual.json);sparse/F1/F3/F3-max/source/cosmograms/S1/multigroup/palette/empty/exact-tie,DPR2/fallback |
|`python -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_house_rows/audit.py ../task_d007_bugfixes/native03`|[35/35+5controls](native03-audit.json),independent actual bbox/source/house audit,does not call layout |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/browser.cjs ../task_d007_bugfixes/boundary03 --boundary-only`|[37/37controls](boundary03/actual.json),real leaf positive,current/late/dispose/failure ownership |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/browser.cjs ../task_d007_bugfixes/focus03`|[12/12cases,290checks](focus03/actual.json),aspect subset/source houses/close/Escape/focus/S1/recovery |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/compact.cjs ../task_d007_bugfixes/compact03`|[2/2cases,48checks](compact03/actual.json),full aspect circle+toolbar at height640 |
|`git diff --check`|exit0,only Git LF→CRLF notices |

All6 final run source LF hashes сравниваются с actual UI через package_checks.json. Browser harness добавляет в served main только **публичный onDrawingEvent observer** без изменения policy/renderer или данных:это явно отмечено instrumentation field. HTTP — контролируемый test seam;core main/session/facts/controller/leaf реальные. Raw native35/focus/compact/boundary — reused unchanged scripts с новыми output folders. Golden не переписан. Source facts geometry не вычисляется заново.

## Сохранённые RED и промежуточные результаты

- Pure2RED:missing color legend и старое имя узла. Browser[red01](red01/actual.json):нецентрированная форма,oversized circle,no legend,row offset/spacing,old name,no real vectors.
- First targeted run35/37:expected old label в прежнем test намеренно обновлён по Owner;new fake-DOM test initially used setAttribute(data-*) while fixture reads dataset. Перешли на существующую dataset дисциплину,не меняли DOM fixture и не объявляли harness issue product RED.
- run01/run02/run03 — промежуточные passes до final first-frame fix. native01/02,focus01/02,boundary01/02 сохранены;финальные authoritative folders03,app matrix run04.
- compact01 desktopRED:toolbar wrapped,SVG bottom673.09>640. Возвращён aspect-specific резерв200px,compact02/03GREEN. Контракт ошибки не расширялся.
- resize01 ChromeRED:first snapshot form width could fail;Yandex positive. Исправлен порядок accepted-view page sizing,resize02/run04GREEN. Не подавляли exception/не добавлялиdelay/TTL.

## Версия,файлы,выдача

Production delta:main.mjs,facts.mjs,styles.css,wheel_layout.mjs,wheel_svg.mjs,result_controller.mjs. Tests:owner_feedback.test.mjs новый,facts.test.mjs только concise Owner name. Own docs:пакет08,plan§11,current findings,developer_artifact,DRAFT ADR,sequence008,эта evidence folder. Session/transport/API/projector/engine/golden/cache/LLM/deps и чужие Manager/Analyst/Tester artifacts не менялись. Старые bug reports/screenshots/manifests и D003/D005/предыдущие raw сохранены.

[Live delivery](live_delivery.json):ready200,TLS normally verified,8/8assets200 и совпадают с current disk. Новый real POST/build не выполнялся,пользовательская сессия/DB не очищались. Web21460/Caddy16468 работают с прежними paths;static assets читаются с диска.

[Предпросмотр](http://127.0.0.1:8767/) открыт в браузере:полный реальный UI,явно помеченный published test DTO,без сохранения/реального POST. Helper preview.cjs,loopback only,PID25200,ignored logs/http-api/bugfix-preview.*.log. Не подмена fixture реальной пользовательской карты. Screenshot examples:[full wheel/legend](run04/Chrome-natal-1440x900.png),[Yandex start](run04/Yandex-empty-1440x900.png),[small height](run04/Chrome-natal-1440x640.png).

## Пределы и handoff

Проверены clean native Chrome155 и Yandex26.8/Windows;исходный пользовательский профиль с50% zoom/расширениями/DPI отдельно не сертифицирован и не менялся. DPR/viewport не выдаются за desktop zoom. Не гарантия arbitrary narrow house/capacity/height<640/другихOS/engines/screen-reader/performance SLA. Native text16/12 и real vector bounds сохраняются без shrink;при typed renderer failure полный HTML остаётся. Р3svg shapes сравнивались визуально,не заявляется pixel-identical raster trace.

Результат локальный,все5Developer fixes и2deltas выполнены. IndexEMPTY,нового commit/CandidateSHA нет;официальный FIXED_PENDING_RETEST/CLOSED и acceptance/gates за Tester/Manager не объявляются. Следующий шаг:Owner просмотр,отдельно порученная публикация точного CandidateSHA и независимый retest. Commit/push/merge/PR не выполнялись. PlantUML sequence008 проверен структурно,renderPNG не запускался.
