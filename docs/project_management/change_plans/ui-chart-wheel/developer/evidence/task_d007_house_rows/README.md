# TASK-D-007 — планеты внутри опубликованных домов

Codex / Developer,20.10.2026. Локальный DRAFT поверх InputSHA/HEAD `e0daa0e814d3d1fd34cadb8c17d064f19c4810f5`, branch `dev/ui-chart-wheel`, index пуст. [Прямое Owner-решение](../../owner_decision_house_rows_2026-10-20.md), [пакет07](../../prompts/07-owner-house-rows.md), [план§10](../../full_wheel_implementation_plan.md#10-task-d-007--внутренние-ряды-по-owner2010), [sequence007](../../sequence_diagrams/ui/007-internal-house-rows.puml). Старый Owner-домен колонки заменён только для point glyphs. Research D003/run03, D005, прежние raw/manifests не перезаписывались. Новый published CandidateSHA отсутствует.

## Что изменено

Root cause: measured collision автоматически выделял ширину колонки и переводил point-метки наружу. Теперь измеренные glyph16/R12/контур размещаются в sector по **points[].house**, границы по source cusp_longitude; несколько радиальных рядов, угловое смещение разрешено. Номер дома из долготы не выводится. Радиальная R ближе к центру даёт вместимость узкого сектора. Космограмма остаётся без домов, с круговой внутренней раскладкой. Source longitude/sign/degree/minute/house/retrograde/aspect/type/category/orb и HTML source rows не меняются. Истинные точки на R−31 и aspect endpoints остаются source geometry; point leaders удалены. Доступный текст поясняет визуальное смещение.

Production files этой итерации: wheel_layout.mjs, wheel_svg.mjs, result_controller.mjs (closed diagnostic data attrs), facts.mjs (legend). CSS, Session/HTTP/API/engine/cache/golden/deps в этой итерации не менялись. Tests: tests/ui/wheel_layout.test.mjs,5 новых regression tests, всего10 в файле. Собственные docs: Owner source, пакет07, plan§10, DRAFT ADR revision, sequence007, Developer handoff, эта evidence-папка. Начальные hashes — [baseline.json](baseline.json). Предыдущие незакоммиченные изменения сохранены.

## Команды и фактический результат

Рабочая папка: `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered`. Node: `C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`; команды ниже используют `node` как сокращение этого **реально использованного** пути. Native Playwright уже установлен в bundled dependencies, Chrome155 Windows; новых зависимостей нет. Pytest запускался глобальным `python`3.14.

| Проверка / точная команда (node = путь выше) | Фактический результат |
|---|---|
| `node --test tests/ui/wheel_layout.test.mjs` |10 PASS;720/448/328, wrap0°, entire glyph/R/contour bounds, multiple radial rows, stable permutations, no source mutation, source-only membership, cosmogram |
| PowerShell: `$nodeTests = @(rg --files tests/ui -g '*.test.mjs'); & node --test --test-reporter=dot @nodeTests` |225 tests,exit0; existing state/S1/acceptance/recovery/focus/controller coverage reused |
| `python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q` |53 passed,20.84s |
| `python -m pytest -q` |2959 passed,1 existing skip DEBT-CALC-001,394.45s |
| `node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_house_rows/browser.cjs native03` |[35/35](native03/actual.json),real composition + point keyboard selection;1440/768/360,DPR2,font fallback;bbox/CTM/font/platformFonts/source data/screenshots |
| `python -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_house_rows/audit.py native03` |[35/35+5 controls](native03-audit.json);independent rendered bbox containment/gap/clipping/source anchors/chord endpoints;does not import layout |
| `node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_composition_v2/browser.cjs ../task_d007_house_rows/focus01` |[12/12 cases,290/290 checks](focus01/actual.json);single aspect/two endpoints/source houses,Escape/restored focus,background,S1,fresh-read recovery,zero extra build |
| `node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/browser.cjs ../task_d007_house_rows/boundary01 --boundary-only` |[37/37](boundary01/actual.json);real passive leaf positive control,retired callbacks/dispose/replace/local and fatal ownership |
| `node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_house_rows/preview_check.cjs` |[PASS](preview-check.json):16points,no column,whole circle visible at1265×712;resize319×604 сохраняет16points и не даёт page overflow;[screenshot](preview.png) |
| `git diff --check` |exit0;only Git LF→CRLF notices |

Native35 fixtures: sparse,F1,F3,F3-max,published-natal,cosmogram,multigroup-control,S1-control,palette-control,empty-cosmogram,exact-tie;each1440/768/360,+F3-max mobile DPR2/fallback. Exact-tie/modified clusters are **synthetic stress**: inherited published house facts may differ from the longitude's geometric sector. Renderer deliberately trusts source house, never recomputes it. `published-natal` is the published DTO fixture, not a new calculation for the current user.

Independent audit uses exact Fraction squared distances for rendered bbox comparisons, with1e−8 CSS² serialization allowance only for native floating bbox boundary arithmetic. Required gap remains2 CSS px. House containment is checked from rendered complete bbox corners and published sector boundaries, with no angular tolerance. True-mark reference error is Euclidean CSS coordinates against direct source trigonometry, threshold **existing0.5 CSS px**; maximum actual **0.00008982403538049876 CSS px**. Positive equality0.5/negative0.500001 controls preserve boundary. Aspect source angle error checked independently<0.00001°,not based on moved glyph centers. All native source fingerprints match current UI; focus/boundary fingerprints checked too.

## Промежуточные результаты сохранены

- native01:32/35;R справа делала bundle слишком широким в узком доме при mobile,включая DPR2. HTML сохранялся, wheel error не был выдан за PASS. Решение:R радиально внутрь и более плотные кандидаты радиуса;native02 затем35/35.
- native03:окончательная проверка после усиления nearest-point distance от полного rect до внутреннего кольца и пояснения в legend. Source hashes именно этой версии.
- native03-audit-initial.json:ошибочная проверка DOM bbox center с порогом0.00001 CSS px вместо согласованных0.5 давала false failures. Audit исправлен по **исходному** нормативному threshold,не по текущему observed maximum;добавлены независимые пограничные калибровки. Старый FAIL сохранён.
- Pure tests добавлены после реализации;TDD RED не заявляется.
- В узкой панели отдельный preview наивно сохранял старый широкий SVG после capacity failure. Подключён существующий production drawing controller вместо обхода его guards,уменьшены только preview margins и добавлен resize319×604 regression. Первое подключение выявило ошибку preview callback onUnavailable(null),которая удаляла успешный SVG;callback исправлен,окончательный preview_check exit0. Production modules после полного pytest не менялись.

## Показ и выдача

[Live delivery](live_delivery.json):HTTPS `https://exact-orb.localhost/`,обычная TLS validation,ready200;8/8 source assets200 и точное LF-normalized совпадение с текущим source. Сервер Uvicorn26320/Caddy14752 продолжает прежнюю сессию;пользовательская DB/cookies не очищались,новый реальный POST `/charts/natal` не выполнялся. Static assets читаются с диска,backend restart для них не требуется.

[Локальный предпросмотр](http://127.0.0.1:8766/) открыт и визуально проверен во встроенном браузере:реальный renderer и production drawing controller с **явной пометкой опубликованного тестового DTO**,без Session/POST и без персональных данных текущего пользователя. Preview server `preview.cjs`,loopback only;PID22424,stdout/stderr в ignored logs/http-api/house-rows-preview.*.log. Перезапущен только собственный preview process после проверки identity;основной сервер не останавливался. Screenshot preview.png снят отдельной real-browser QA-командой того же preview. Общие пользовательские данные не подменялись fixture.

## Ограничения

Chrome155/Windows и указанные fixtures/frames;не универсальная вместимость произвольно узкого дома/неограниченной плотности и не performance SLA. При недостижимой вместимости typed local renderer failure сохраняет полный HTML,без смены house/уменьшения font/скрытия planet. Другие engines/ОС/реальный mobile/screen-reader не проверены. Sequence007 проверена структурно,PNG/PlantUML render не запускался. Runtime/browser tests используют контролируемый HTTP и опубликованные fixtures;live GET delivery не доказывает новый пользовательский build. Нет нового commit/push/merge/PR/формального acceptance или смены Manager gates;последующая публикация и независимый review отдельно.
