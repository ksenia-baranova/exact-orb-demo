# TASK-D-005 — drawing feasibility v2 / ревизия DRAFT ADR

**Автор / подпись:** Codex / Developer, 19.10.2026. **Результат: ограниченное исследование выполнено, новый drawing-кандидат для реализации не подходит.** Ревизия boundary / HTML / S1 подготовлена как DRAFT для T007/R002. Whole drawing / production PASS, принятый ADR и G3 отсутствуют. Пакет локальный; новый TechnicalPackageV2SHA **NOT_CREATED**, commit/push/PR этим поручением не разрешены.

## Версии, STARTED и время

| Предмет | Точная версия / источник |
|---|---|
| Фактический InputSHA / HEAD | `34f187aa81ddad7760089f54c1dc23d4d9e59d59`; dev обновлён ff из опубликованной change, прежний локальный `5eba30f74ce9af85fc13be048d3c0898f9d1a2cb` |
| AssignmentSHA / поручение | `0046ac75bd6582089b68a640f98fa65468c0607a`, [Manager D005](../manager/prompts/task-d-005-drawing-feasibility-v2.md) / §2.20 |
| Согласованная оценка / план | AssessmentSHA `5eba30f74ce9af85fc13be048d3c0898f9d1a2cb`; Owner прямо согласовал scope, 16–24 рабочих часа, experiment≤12 внутри, передачу до конца третьего рабочего дня и поручил начать |
| STARTED / срок | **19.10.2026 00:15:25 MSK → до конца 21.10.2026 Europe/Moscow**; день старта — рабочий день1, пн–пт. Час окончания дня не выдуман. [Source / baseline](evidence/task_d005_feasibility/execution_start.json) |
| AnalystContractSHA | **`2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`**, принятый v3 + S1; A007 DONE/APPROVED, без повторного ожидания |
| Неизменные исходные предметы | D003 `d24a24e04be32d0522674735388e9d2ea3e65c93`; CriteriaSHA `f6f289cda25e7f228dff064175805130cc770b63`; A005 `4057d6ed37b24e082a2a4089eb7104da80d17ee5`; T004 `ad5206e30d855e44a9535f89dced1d8fe4699d17` |
| R001 r2 / A006 | Только опубликованная [Manager-сводка](../manager/review_inputs/task-r-001-r2-summary.md) @ `0e590fa23d6c3f31d59a59cd0f7cb5be3509d160`; исходного reviewer OutputSHA нет, reported solver/tests не воспроизводились. A006 — отдельная условная already_applied policy, не блокировка геометрии |

Fetch/ff — exit0, новых материальных входов после AssessmentSHA нет: merge интегрировал саму оценку. Index и дерево перед STARTED чистые; несвязанных изменений не было, reset/force/clean/stash не применялись. Чужие материалы — только опубликованный Git. Текущие Manager/gates/DP/другие роли не редактировались.

Первичная остановка по достаточности зафиксирована19.10.2026 10:59:33,906 MSK: [исходный stop](evidence/task_d005_feasibility/experiment_stop.json). Post-audit обнаружил10 промахов без activation callback и, следовательно, без записанных delivered coordinates. Входы/модель не менялись; после исправления capture повторены те же24 клетки как **run04-delivery**, первый run04 и его [исходники](evidence/task_d005_feasibility/sources-run04-initial/harness.mjs) сохранены. Это исправление доказательства в исходном timebox, не новая поисковая итерация.

**Финальная остановка: 2026-10-19T11:12:57.167959+03:00**, [final stop](evidence/task_d005_feasibility/experiment_stop_final.json). Консервативный wall envelope STARTED→final stop **10.9589 часа <12**, включая паузы/ожидание разрешений инструментов; это **не измеренный труд**. Авторитетный browser run: `2026-10-19T08:09:33.297Z`–`2026-10-19T08:09:46.646Z`, **13.349 секунды**, без стоимости подготовки harness; первоначальный run11,555 секунды отдельно не прибавляет coverage. Труд подготовки по этапам отдельно не измерен. Подготовка оценки уже включена один раз в16–24; timestamps не дают экономию, свободный резерв или остаток D003/бюджета реализации. После финального stop новых моделей/browser runs нет, только post-audit и документы.

## Модель до actual и независимость проверки

[Spec run04-FE-v1](evidence/task_d005_feasibility/model_spec.json), SHA256 `80b73cda18ae50bd1a5b05f1cd2ddb291ce0ccda5d8549c2b73815a0e5ed9ec0`, записан до первого build. [Builder](evidence/task_d005_feasibility/build_models.py) → [24 inputs/index](evidence/task_d005_feasibility/analytic/index.json) → [независимый Fraction verifier](evidence/task_d005_feasibility/verify_models.py) / [certificates и контрпримеры](evidence/task_d005_feasibility/analytic/verification.json) → новый browser run04. Verifier не импортирует/не вызывает placement. Аналитические bounds условно переиспользуют опубликованные run03 font metrics; actual run04 измеряет их заново, point/marker ink drift **0**.

F: reference radii point0,40S / marker0,22S / angle0,11S, measured-component circumdisks и order-preserving projection128 sweeps, отдельная label-полоса углов. C0 задан на default visual union до layout; frozen объекты не двигаются, hit overlap не расширяет C0. Иная модель вместо fixed16°/40°, без повторного подбора параметров после actual. Истинные anchors, aspect endpoints и весь DTO сохранены. Полный union включает glyph/R/category/selected stroke/focus, а fixed angles входят в сравнение с другими группами.

Отличие от D004 явно объявлено: experimental annular domain, reference endpoints на новых радиусах, **straight-chord return**, Euclidean displacement/min(1,d), вместо старого fixed-radius arc. Весь prefix проверяется piecewise-quadratic rational inequalities; 1px parameter заключён точными integer-sqrt bounds. Прежние 0,5/2/1/16/12/44 не менялись. Новая path-конвенция — гипотеза для review, не принятая замена нормативного контракта.

E сохраняет visual F и тот же visible glyph-control/key/tab stop/action: Q44 смещён12px радиально наружу, visible component hit rectangles остаются в его native union. Отдельного off-glyph control или нового действия не введено, semantic stop не сработал. Q задан left/top + native width/height44; округлённые right/bottom binary64 — диагностические координаты, не подмена размера. Certificate проверяет весь Q в clip / native union с вычитанием later paint occluders; **визуальный annulus не ограничивает Q автоматически**. Native checks отдельно подтверждают delivered event/composed path/canonical outcome, не element.click().

Успех измеренной component geometry **не включает полный zodiac/sign text / palette**. Это предел данного negative candidate, не пропуск для whole drawing PASS; эти fixed labels не считаются проверенными. Не вводились solver/scipy/new app dependencies. Exact free-clip packing49/100/256 Q44 для328/448/720 — constructive **lower bound только свободного прямоугольного clip**, не optimum / continuous upper bound и не actual wheel placement. Reported Reviewer packing не присваивается.

## Actual matrix и различающие контрпримеры

Источник каждой строки — [browser audit](evidence/task_d005_feasibility/browser_audit.json) и [run04 raw index](evidence/task_d005_feasibility/run04-delivery/index.json). Geometry — только измеренный component union; Q — условный rectangle certificate для объявленной модели; pointer — wrong owner или wrong selection outcome из пяти native probes/target.

| Fixture | Frame | Component geometry F/E | Q44 F | Q44 E | Native wrong F/E | Keyboard fail F/E |
|---|---|---|---|---|---|---|
| sparse | 720 | PASS/PASS | 16/16 | 16/16 | 0/0 | 0/0 |
| sparse | 448 | PASS/PASS | 16/16 | 16/16 | 0/0 | 0/0 |
| sparse | 328 | PASS/PASS | 8/16 | 12/16 | 8/4 | 0/0 |
| F1 | 720 | FAIL/FAIL | 13/19 | 13/19 | 7/7 | 0/0 |
| F1 | 448 | FAIL/FAIL | 11/19 | 12/19 | 13/12 | 0/0 |
| F1 | 328 | FAIL/FAIL | 11/19 | 9/19 | 14/14 | 0/0 |
| F3 | 720 | PASS/PASS | 11/18 | 11/18 | 8/8 | 0/0 |
| F3 | 448 | PASS/PASS | 10/18 | 10/18 | 9/9 | 0/0 |
| F3 | 328 | FAIL/FAIL | 8/18 | 8/18 | 12/12 | 0/0 |
| F3-max | 720 | PASS/PASS | 5/20 | 5/20 | 16/16 | 0/0 |
| F3-max | 448 | PASS/PASS | 5/20 | 5/20 | 16/16 | 0/0 |
| F3-max | 328 | FAIL/FAIL | 5/20 | 5/20 | 18/19 | 0/0 |

Итог: **14/24** measured-component geometry, **241/438** условных Q certificates, **238/2190** pointer mismatch, **438/438** keyboard-проверок без потери live target / программного focus/scroll на activation. 16 IDs, R и source pairs/category labels сохранены; F3/F3-max покрывают seam0 / близкие angles. **256** initially valid moved-групп имеют допустимый положительный полный return-prefix → LOCAL_TIGHT_FAIL; это отказ данной construction, не требование глобального оптимума. Невалидные начальные группы не получают PASS minimality. Whole drawing PASS **не заявлен**, даже для четырёх sparse720/448 F/E partial клеток с прошедшими записанными predicates.

Конкретные различающие данные:

- **F1/448/F и E:** `saturn` ↔ `pars_fortune`, gap²=0 при требуемом ≥4. Это воспроизводимый gap-контрпример, не font-size или blanket viewport failure.
- **F3/328:** marker `mercury/venus/conjunction` пересекает mercury и выходит за свой объявленный outer annulus; F3-max/328 marker пересекает angle:asc и другой marker нарушает outer bound. Увеличение clip или уменьшение bbox после clipping не применялось.
- **Sparse/328:** C0 пуст, displacement/leader=0, measured visual geometry проходит; centered Q44 даёт8/16 certificates, E —12/16. Native F corner moon запросил CSS `(80,537005;543,004941)`, click доставлен `(80;543)`, topmost/path `target-2` / mercury, selection стала mercury. Requested/delivered coordinates различены; bbox44 не доказал попадание в moon. Смещение визуально свободного moon ради hit запрещено этой моделью.
- **F3/720/F/mercury:** d≈188,73291 CSS px в этой явно некомпактной construction; вся измеренная component geometry исходной клетки допустима. Exact verifier доказал допустимость полного1px visual return и положительного rational prefix длиной≤0,5px при frozen остальных. Это конкретный witness избыточности, а не вывод из одного конечного положения. Всего256 local visual-prefix witnesses, из них148 в клетках с валидным полным measured component union; остальные относятся к target-local условиям в уже дефектных клетках. Эти числа не означают256 whole-feasible карт, не доказывают H/Q во время возврата и не вводят глобальную оптимальность.

Независимые9 аналитических controls: diagonal equality gap2, below-boundary negative, zero-prefix sensitivity, clipped44/intact44 и сохранённые horizontal18/19/20/fraction calibrations. Exact coordinates/fractions и expected/actual — в verification JSON. Контрпримеры относятся к одной модели; F/E не исчерпаны, невозможность продукта / исключительность E не установлены. Screenshots [F1/448/E](evidence/task_d005_feasibility/run04-delivery/screenshots/F1-448-E.png) / [F3-max/328/F](evidence/task_d005_feasibility/run04-delivery/screenshots/F3-max-328-F.png) визуально просмотрены; чёрная рамка там — focus indicator, не selected контур категории.

## R001-01…04 и S1: критерий → данные → actual → вывод

| Замечание / REQ-AS-DP | Данные / actual | Исправление / точное место / предел |
|---|---|---|
| R001-01; REQ-WHEEL-01/10/11, AS-WHEEL-24, DP-O-010 | A pending → accepted B, dispose A throws; HTML B уже опубликован, B успешно рисуется; guard не возвращает A | [ADR порядок](drawing_adr_draft.md#r001-01--порядок-и-локальные-отказы), [sequence001](sequence_diagrams/ui/001-result-renderer-lifecycle.puml); revoke/removal/HTML до guarded dispose/draw. [Boundary controls](evidence/task_d005_feasibility/run04-delivery/boundary-controls.json) |
| R001-02; DP-O-010 | Late A publish **до и после** settlement отказан; старая C revision той же instance не пишет D | [ADR write authority](drawing_adr_draft.md#r001-0203--write-authority-до-settlement): value frames + revision sink, DOM у adapter; принцип доказан на isolated button-frame, полный SVG writer future work |
| R001-03; AS-WHEEL-24 | Factory/sync update/async rejection дают local warning и HTML актуальной карты; stale reject не заменяет D | [Boundary harness](evidence/task_d005_feasibility/boundary.mjs), sequence001. Expected leaf fault отдельно от unexpected controller fallback. Async-dispose не входит в void-контракт / не проверен |
| R001-04; REQ-WHEEL-07…11, AS-WHEEL-13/18/21/26/27, DP-O-010/013 | Same live HTML point и unique row при native Enter/Space; retained SVG при resize и последующей активации; same-key recreate отличён, model restoration cause-specific; collapse перед hide, recovery доступен | [ADR HTML/focus](drawing_adr_draft.md#r001-04--живой-html-и-focus), [raw controls](evidence/task_d005_feasibility/run04-delivery/html-focus-controls.json), [sequence002](sequence_diagrams/ui/002-acceptance-selection-focus.puml). Не mounted/cross-platform acceptance |
| S1; REQ-WHEEL-04/07/08/10, REQ-UI-06; AS-WHEEL-28/29/30; DP-O-013 | Принятый полный DTO contract @2736e28; cardinality до filters, все source rows/order/from-to/category/orb; local ambiguous-only warning/no aspect-select; 0/1/>1 reconcile, failed/unaffected | [ADR S1](drawing_adr_draft.md#s1--полный-accepted-dto-до-фильтров), sequence002; U/R/D/V/M/L/T/P — design / future tests. Runtime F5/S1 **NOT RUN**, A007 не переоткрыт |
| Drawing; REQ-WHEEL-02/05/06/09/10, AS-WHEEL-03/07…10/16/25, DP-O-011/012/014 | New F/E frames720/448/328, actual ink/font/M/clip/anchors, exact gap / local prefix / Q certificates + native mismatch | Spec / analytic / run04 / browser audit. Measured component geometry не равна полной drawing feasibility; кандидат отклонён |

В boundary12/12 и дополнительных browser controls12/12 проходят именно объявленные isolated условия. Принятый A005 fresh matched pending-goal используется без producer-provenance; A006 already_applied остаётся условной отдельной ветвью. Статусы чужих задач / DP не менялись.

## Окружение, команды и actual

Chrome **155.0.8059.40**, installed executable `C:/Program Files/Google/Chrome/Application/chrome.exe`, headless Windows10.0.26200, Nodev24.19.0, bundled Playwright. Реально resolved fonts по CDP: **Segoe UI Symbol / Segoe UI**, все per-text записи сохранены. CSS scale1, DPR1, visualViewport.scale1; actual M/translation, local+CSS coordinates, canvas ink/SVG bbox, effective em и screenshots/hashes — в каждом raw record. Max measured anchor CSS error **0,000043436 px ≤0,5**. Em-boundary реальный16/12 проходит на равенстве,15,99/11,99 и nominal16×scale0,5 отвергнуты; это не минимум ink-height. Font missing-glyph negative / увеличенный текст / иная платформа не проверялись.

Команды из корня (runtime paths передаются локальной средой):

```text
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/build_models.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/verify_models.py
node --check docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/harness.mjs
node --check docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/boundary.mjs
node --check docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/run_browser.cjs
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/run_browser.cjs
$env:D005_BROWSER_RUN = "run04-delivery"
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/run_browser.cjs
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/stop_experiment.py --final
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/analyze_browser.py
git diff --check
```

Фактический Node executable — `C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`, приведённые команды `node` запускались через него. Воспроизведение — в отдельной копии evidence и с новым run ID; старые actual не перезаписываются.

Build24, независимые controls9, Node syntax, run04 complete24/browser12/boundary12, stop и post-audit — exit0. Browser output содержит ожидаемые отрицательные drawing actual, это не crash/green acceptance. `stop_experiment.py` / browser directories single-use: повтор сохраняет новый явно named run, не перезаписывает actual.

Ошибки instrumentation/audit helpers исправлены без повторного model/browser: zero-length prefix первоначально возвращал0 вместо исходного расстояния; [первоначальный audit](evidence/task_d005_feasibility/analytic/verification_initial-helper-defect.json) сохранён, добавлен zero-prefix positive control, final verifier повторён. Первый post-audit завершился TypeError из-за затенения record переменной rectangle-bottom; исправлено только имя, повтор exit0. Финальные исходники и результаты вошли в manifest; исходный post-audit error описан здесь и не выдаётся за PASS. Первый native run также не имел общего capture для10 промахов; final run04-delivery сохраняет pointerdown/click/owner/path/coordinates **для всех2190 probes**, включая отсутствие activation. Это ошибки research helpers, не production defect и не изменённый старый evidence.

Финальные link/table/scope/hash checks и точный перечень файлов сохраняет новый [package audit](evidence/task_d005_feasibility/package_audit.json) / [manifest](evidence/task_d005_feasibility/package_manifest.json), результаты подписаны в Developer handoff. Старые preparation JSON/manifests остаются snapshot соответствующих SHA; текущие revised ADR/sequences имеют D005-авторство, исходные D003 blobs проверяются на d24a24e.

## Оценка, ограничения и передача

D005 остаётся в согласованных **16–24 часах / 2–3 чд**, experiment≤12 внутри; дополнительного расхода не запрошено, новый опыт после stop не разрешён. Из отрицательного bounded результата не вычитается elapsed из бюджета и не восстанавливается неизвестный остаток D003. Forecast9–14 чд /72–112 часов остаётся **условным неподтверждённым forecast полной реализации**, не расширенным бюджетом. D005 размещён один раз: drawing9–12, controller/ADR4–6 (HTML design1–2), docs/handoff3–6; HTML-presenter6–10 внутри controller16–24. Подготовка второй раз не начислена.

По результатам confidence: высокая для конкретных воспроизводимых counterexamples / isolated guard-принципа, **низкая для обещания полной drawing-поставки в прежнем forecast**, пока не выбрана допустимая конструкция. Эта construction rejected; дополнительная новая модель / новый радиус / иной Q-механизм требуют отдельного bounded scope и оценки через Manager. Если она меняет наблюдаемый смысл — адресный Analyst/Owner decision с конкретным примером. Ни fallback, ни расширение9–14 молча не приняты. Это точный пересмотр предпосылки прогноза, не необоснованная новая численная оценка неизвестного решения.

Не проверены: production implementation / mounted page / whole recovery HTTP / HTTPS; runtime F5/S1; полный pytest/Node product suite и reported Reviewer FAIL; cross-platform/touch/увеличенный текст/zoom/missing-glyph; полный zodiac/sign text/palette; отдельный whole-page overflow predicate; full SVG value-frame writer / hostile global-DOM bypass / async-dispose / глобальный optimum. PUML структурно проверяются, render без доступного Java/PlantUML **NOT RUN**. Old source tests использованы для анализа границ, их прежние PASS не присвоены новому пакету. Package-audit сначала ошибочно LF-нормализовал opaque `.bin` при сравнении baseline; исправлен только read-policy helper (binary сравнивается raw). Golden-файлы не изменялись; это не воспроизведение reported Reviewer test FAIL.

**Следующий шаг:** отдельное поручение на commit/push/PR нового D005-пакета → Manager закрепляет **точный новый TechnicalPackageV2SHA** → адресные **TASK-T-007 и TASK-R-002**. Manager проверяет полноту/версии/traceability и решает дальнейший маршрут geometry; роли сохраняют авторство заключений. Готовность reviewers подтверждают они; Developer даёт первый triage за1 рабочий день, эскалация Manager→Owner через+1 рабочий день просрочки, заместителя нет. Production требует отдельного **G3**; текущие статусы/gates Manager не изменены.


Финальный documentary проход: `python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d005_feasibility/audit_package.py --write`, затем без `--write`, `git diff --check`. Первый успешный результат: **D005_PACKAGE_OK payloads162 baseline604 D003_archive164 native2190 keyboard438 controls9+12+12 docs45 links1301 tables111 AST6 node3 PUML_structure2 diff_check0 indexEMPTY publicationNOT_RUN**. Записи self-metadata исключены из собственного хеширования во избежание цикла; все162 payloads перечислены в manifest,2 metadata отдельно в audit. После добавления этой строки hashes повторно проверяются; результаты initial helpers/first run не подменяют authoritative final evidence.
