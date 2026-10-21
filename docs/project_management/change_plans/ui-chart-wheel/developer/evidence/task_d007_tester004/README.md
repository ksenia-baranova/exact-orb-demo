# TEST-FIND-WHEEL-004 — Developer исправление native hit-area

Codex / Developer,20.10.2026. Прямое поручение Owner обновить change и исправить Tester bugs. [Baseline](baseline.json): dev HEAD3c2744ee2ecfe64ebe1d2f5b306a23d008d5064d → fast-forward опубликованной change до InputSHA3b95934c884caa9f40ea70e935991457058b87b9; деревo/index чисты до и после. Опубликованный Tester OutputSHA1cfbe3156761da1cfba1ef66133febd7c7bae265,его TestedSHA0da99518ada67603b08ab4220d337e3a5e3aae60. Более новый HEAD не приписан старому test run. [Bug/expected](../../../tester/defects.md#test-find-wheel-004),[runtime report](../../../tester/runtime_review_2026_10_20.md),[план§13](../../full_wheel_implementation_plan.md#tester-hit-area-004),[пакет10](../../prompts/10-tester-hit-area.md).

## Причина и исправление

На current InputSHA воспроизведён прежний дефект: Sun bbox50.0625×44, border-radius8px, нижняя native hit aperture на offset43 равна41.75/42.75/41.25px для1440/768/360. Центр иkeyboard работают;край требуемого Q44 не принадлежит владельцу. См.[before/actual](before/actual.json).

Изменён **только production styles.css**, правило .facts-table .fact-select: rectangle,border-radius0,min-width46/min-height46. Требуемый Q44 выбирается по центру bbox;имеет минимум1px отступа от каждой границы минимального target,поэтому не зависит от крайних fractional pointer samples. Порог44,смысл H и допуски не менялись. Label font/padding,source DTO,engine/API,golden,JS/state/selection иSVG geometry не менялись. Альтернатива сохранения radius8 требовала бы более крупного target и менее компактных строк;дополнительные pointer handlers/оверлеи не нужны. На desktop текущая строка55px (раньше53),в пределах уже проверявшихся56;mobile сохраняет card layout без page overflow.

## Native evidence и независимые контроли

[tester's original probe](tester_probe_source.cjs) сохранён побайтно с SHA256 в baseline. [replay_hit_area.cjs](replay_hit_area.cjs) меняет только авторство/Input label/output namespace,не measurement. Его legacy possible44 при height>44 — диагностическая эвристика,**не самостоятельный certificate**;после исправления положительный результат обоснован собственной явной Q44 и фактическими owner/outcome пробами ниже. Scan длины включают native quantization и не выдаются за точную непрерывную ширину bbox.

[native_hit_area.cjs](native_hit_area.cjs) использует настоящие index/main/session/facts/controller/SVG/styles,controlled API leaf и опубликованный F1 DTO. Ни layout solver,ни renderer mock,ни Developer geometry verifier в oracle не вызываются. Для каждого enabled visible HTML point/aspect задаётся конкретный centered Q44 в CSS-координатах,записывается bbox/radius/clip и529 двумерных native elementFromPoint проб (включая off-centre и близкие к границе внутренние точки). Проверяется принадлежность владельцу. Геометрическая предпосылка положительного случая — прямоугольный target без скругления с запасом от границы;sampling сам по себе не заявлен доказательством произвольной формы/всех возможных overlays.

Отдельные реальные mouse клики в центре и четырёх углах внутри Q44 должны toggle Sun;записываются event.isTrusted и coordinates. Enter/Space сохраняют действующее поведение и живой focus. Off-centre click аспекта переводит в выбранный режим с HTML wheel focus;Q44 выбранной строки измеряется повторно. Раскрытие,выбор иclose не создают HTTP. Позитивный независимый solid44,отрицательный43,отдельный bbox44 с перекрытием иclip до43 калибруют ширину,owner/перекрытие иclipping — center/bbox не достаточны.

- [before](before/actual.json):Tester probe reproduced3/3 негативных результатов на актуальном input.
- [red01](red01/actual.json):первый собственный прогон остановлен после одного записанного случая;краевой click не открыл aspect mode,а harness ожидал возможность нажать скрытый close. Это следствие дефекта плюс ошибка порядка harness,не отдельный product bug. Все bytes/results сохранены.
- [red02](red02/actual.json):исправлен только порядок проверки;после неудачной corner активации отдельный center positive открывает aspect mode,чтобы calibration была реально достигнута. Продуктовые hit failures сохранены;exit1.
- [green01](green01/actual.json):**6/6cases,484/484checks,372 enabled source control measurements**,дополнительно6 selected-aspect измерений и paired controls. Chrome155/Yandex26.8,1440/768/360,Windows. Конкретные Q/bbox/failed coords/исходные source hashes находятся в actual JSON.
- [after](after/actual.json):legacy Tester probe после fix3/3positive,solid44/43 calibration сохранена;actual Sun height46,width50.0625,radius0.

## Команды и результаты

Cwd `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered`. `node` — фактически bundled C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe,Python3.14 — C:/Users/KateUser/AppData/Local/Programs/Python/Python314/python.exe. Новых dependencies нет.

| Команда | Actual |
|---|---|
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_tester004/replay_hit_area.cjs before`|3 negative cases,exit0 означает запись diagnostic,не product PASS |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_tester004/native_hit_area.cjs red02 --red`|Native RED,exit1;контроли достигнуты |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_tester004/native_hit_area.cjs green01`|6/6,484checks,exit0 |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_tester004/replay_hit_area.cjs after`|3 positive diagnostic,44/43 calibration |
|PowerShell:`$nodeTests=@(rg --files tests/ui -g '*.test.mjs'); & node --test --test-reporter=dot @nodeTests`|229passed,exit0 |
|`python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q`|53passed,14.84s |
|`python -m pytest -q`|[2959passed,1existing skip DEBT-CALC-001,312.24s](pytest.log) |
|`git diff --check`|exit0,только LF→CRLF предупреждение;проверено перед handoff |

[Live HTTPS delivery](live_delivery.json):styles.css200,совпадает с текущим source,TLS verified. Backend restart не требовался. Новый real POST/build и пользовательская серверная сессия не затрагивались;native API seam контролируемый,это не live full-flow acceptance.

## Оставшееся и handoff

Одна новая подтверждённая Tester implementation-находка исправлена локально. Tester/Manager/Analyst artifacts не редактировались,официальный TEST-FIND-WHEEL-004 остаётся OPEN до публикации точного SourceSHA и независимого retest. Собственный результат не объявлен acceptance/G4/G5. Новый commit/push/PR этим поручением не разрешён;index сохранён пустым.

Наблюдение gap=1.9999923706054688 в трёх Tester cases остаётся **INDETERMINATE**. Технический precision/radial oracle должен быть адресно уточнён;здесь не расширен допуск и не поставлен PASS/geometry fix. Исторический TEST-FIND-WHEEL-002 не закрывается. Ранее принятые Owner долги009/010 не исправлялись этой CSS-правкой.

Проверены native desktop Chrome/Yandex на названных frames/F1,калибровки/keyboard/focus/compactness. Реальный touch/screen-reader,другаяOS/engine/пользовательский zoom,DPR/font fallback variants,все допустимые DTO иindependent Tester retest не выполнены. Full prior geometry matrices не выдаются за новые прогоны;SVG/числа не менялись. Следующий шаг:публикация по отдельному поручению с exact SourceSHA,затем адресный Tester retest004;остальные formal decisions у назначенных владельцев.


[Финальный audit](verification.json):19 локальных ссылок,14 current UI fingerprints,foreign sources3/3 unchanged,RED positive controls reached иbefore/after provenance проверены. Source version до публикации: InputSHA3b95934c884caa9f40ea70e935991457058b87b9 + styles.css LF SHA256 `e4b4539fbe051e66c9f8226bc6834828e925eb3b12aea6f93e6fdfa20d53bfec`. Это не новый опубликованный SourceSHA.


Подготовка публикации:в собственном replay helper исправлены повторные CR при переводе строк,обнаруженные git diff --cached --check. Нормализация только LF,логика не менялась;побайтная копия исходного Tester script и все raw run данные сохранены.
