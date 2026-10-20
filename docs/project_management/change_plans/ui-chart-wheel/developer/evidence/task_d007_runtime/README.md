# TASK-D-007 — проверка фактического приложения

**Codex / Developer,20.10.2026. Локальная DRAFT-поставка, без публикации и независимой приёмки.** InputSHA / AssignmentSHA e0daa0e814d3d1fd34cadb8c17d064f19c4810f5; branch dev/ui-chart-wheel. Прежний STARTED19.10.2026 22:11:37MSK сохраняется. [Execution / FW01…06](../../full_wheel_implementation_plan.md#8-task-d-007--полный-локальный-результат-fw-0106), [Owner A006](../../owner_decision_already_applied_2026-10-20.md), [DRAFT ADR](../../drawing_adr_column_draft.md).

Это проверки настоящих main/session/form/facts/controller/layout/SVG. В browser matrix заменяется только HTTP. В mounted integration — HTTP и shim вокруг настоящего SVG leaf для controlled fault / stale callback и timing. Boundary controls заменяют leaf на минимальный альтернативный renderer только в fault-сценариях; независимый positive использует production createWheelRenderer.

## Точные команды и результаты

Workdir: C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered.

Node в командах ниже: C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe (v24.19.0). Python для pytest: python = Python314/python.exe; bundled Python подходит для самостоятельных audit scripts, но не содержит pytest. Chrome155.0.8059.40 / Windows; локальный loopback, без внешних HTTP/LLM вызовов.

~~~powershell
$nodeTests = @(rg --files tests/ui -g '*.test.mjs')
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' --test @nodeTests
# 216 PASS,0 FAIL;445,48ms, final UI sources

python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q
# 53 passed;14,54s; installed-wheel resources included

python -m pytest -q
# 2959 passed,1 skipped;145,78s
# Existing skip: tests/test_configurations.py:473, DEBT-CALC-001

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/browser.cjs run05
# 35/35 compositions +37/37 boundary controls;exit0

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/audit_native.py run05
# NATIVE_INDEPENDENT 35 /35;controls7 /7;exit0

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/integration.cjs integration06
# 3/3 widths,37 checks each=111;exit0

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_runtime/verify_package.py
git diff --check
~~~

Browser scripts отказываются перезаписывать существующий run. Для воспроизведения использовать новый label, затем передать его audit_native.py. verify_package.py по умолчанию закрепляет окончательные run05 / integration06; новый прогон не заменяет эти предметы автоматически. Source hashes в каждом actual.json нормализуют CRLF→LF. [manifest](manifest.json) отдельно содержит SHA256 всех изменённых/новых файлов пакета: text LF, PNG raw; manifest и package_checks исключены из собственной hash-схемы. [Package checks](package_checks.json) фиксируют scope/index/history/link/diagram/source соответствие и diff-check.

## Критерий → данные → actual → вывод

| Критерий / сценарии | Данные / actual | Фактический вывод |
|---|---|---|
| CSS reference /16/12/gap2/anchor0,5; REQ-WHEEL-02/05/06/09 | [run05 actual](run05/actual.json): реальные text/rect bbox, group/anchor/path coordinates, em/font/CTM, source DTO, frame/width/height; [independent audit](run05-independent.json) |35/35. CTM1 CSS unit, DPR1/2;16px point/sign/☌ em,12px R/angle/name em. Это не порог видимой высоты ink; selection contour входит в reserved bounds |
| Условная колонка C0 / frozen / cyclic0° / exact ties | sparse/F1/F3/F3-max/published-natal/cosmogram/multigroup/S1/palette/empty-cosmogram/exact-tie ×1440/768/360 +DPR2/fallback F3-max360 |35/35: только C0 points в колонке; nonconflicting default anchors frozen; 16 IDs /R не скрываются; рост H вместо font shrink |
| Локальная aux compactness / row objective | audit_native.py не вызывает layout: Fraction(actual binary64), whole-prefix blocking contact, cyclic order, contiguous ±1/64 row shifts с union-row gap2 |35/35 +7/7 независимых аналитических positive/negative controls. Нет заявления о глобальном optimum произвольной геометрии |
| Clipping / leaders / shared20,5px regression | actual path vertices/native boxes; independent clip/shared checks; wheel_layout.test.mjs crossing/touch/shared controls |35/35: imagery внутри SVG, positive-length common segments отвергаются; crossings и point touch допустимы |
| R001-01…04 / renderer boundary | [native controls](run05/actual.json): revoke/remove/HTML/dispose/draw trace, current/stale, same instance, deep freeze, alternate real leaf |37/37: stale до/после settlement, original-root mutation, current late publish, failed lease, reentrant clone, passive value whitelist, local failure и fatal partition, idempotent close |
| Accepted once / immutable submitted / A006 / editor / recovery | accepted_chart.test.mjs + [mounted integration](integration06/actual.json), POST snapshot B/draft C, fresh GET B, stale/different/failed controls, subsequent ordinary GET |12 target tests PASS; native3 widths: changed birth reset один раз, collapse iff draft=B. already_applied facts/summary только GET; RESULT_SUPERSEDED отдельный cause |
| HTML pointer/keyboard/focus44, background, S1 | integration06/case-*.json: 44 CSS square coordinates /9 native elementFromPoint probes, actual mouse clicks, overlay и clipping negative controls, Enter/Space, live enabled focus |111/111 integrated checks. Все видимые fact controls в matrix имеют bbox≥44×44; actual hit-square/coordinate click проверен для representative Sun, не только element.click. Background выделяет концы без линии/☌, не меняет layout; S1 сохраняет строки и живой focus |
| Реальные HTML B при leaf/controller fault; empty | integration06 logs + browser DOM checks |Local leaf fault оставляет новую HTML карту/summary и локальное предупреждение; owner fault ведёт в существующий safe-read; explicit positive GET восстанавливает SVG. Empty убирает SVG и возвращает focus в открытый editor |
| Доставка/архитектура/числовой baseline |53 target /2959+1 full pytest |Новые реальные .mjs доставляются приложением и installed wheel; engine/API/projector/golden/deps не менялись |

Фактические CSS frame widths страницы:720 /424 /318 для viewport1440 /768 /360; это измерение страницы с её padding/border, не подстановка исследовательских720/448/328. Выносная колонка и растущий H проверены в этих реальных рамках. Native fonts дополнительно записаны через CDP platformFonts для F3-max; fallback проверен тестовой CSS подменой sans-serif + loadingdone, затем новый measured layout. Production font-family/whitelist не ослаблялись.

[Реальная композиция360](run05/screenshots/F3-max-360-composition.png), [768](run05/screenshots/F3-max-768-composition.png), [1440](run05/screenshots/F3-max-1440-composition.png). Screenshot снимается после выбора Moon; исходные normal bbox сохранены до selection, координаты selection-only заморожены и отдельно проверены. Все screenshot paths локальные.

## Исправленные дефекты и сохранённые неуспехи

- A006: до изменения session.mjs новые согласованные ожидания дали6 FAIL при6 PASS; после —12/12. Живая цель already_applied ранее удалялась до GET. Теперь потребляется только свежим совпадением, отдельно от own_committed; policy Owner сохранена по ссылке выше.
- [boundary-regression-red](boundary-regression-red/actual.json): delayed rethrow ControllerFailure из retired A давал HTML B, пустой SVG и лишний fatal. Проверка lease в async owner-error branch исправлена; [GREEN](boundary-regression-green/actual.json), затем run05:37/37.
- Initial independent audit run03 применял pairwise component gap к пробе сдвига column rows, вместо согласованного union-row separation. Исходный auditor и run03-independent-initial.json сохранены; verifier исправлен по домену row objective. Production constraints не ослаблялись; окончательный run05 проверяет именно union-row gap≥2.
- integration01: ожидание hidden result через default visible selector ошибочно истекало. Исправлено state=attached; исходный FAIL сохранён.
- integration03/04: bbox-centred ±21,99 probes пересекали нижнюю native raster hit границу дробного bbox1440. Scan сохранил действительную область. Окончательный контроль задаёт отдельный квадрат44 CSS px, проверяет все9 actual hit points, реальный click и независимые overlay/clipping controls. Размер/стили/допуск не изменялись ради проверки; bbox и effective hit не отождествляются.
- Ранние run01…04 и integration02/05 остаются промежуточными raw версиями; их source hashes не объявляются проверкой окончательного source.
- Ошибочные Python environments сохранены в истории сеанса: bundled Python без pytest; primary .venv без fastapi/setuptools давал setup failures. Окончательные целевые/полный прогоны выполнены global Python3.14 с нужными зависимостями. Ошибки setup не выдаются за product RED.

## Профиль и пределы

В integration06 shim измеряет настоящий async leaf update (fonts/layout/paint плюс publish) и синхронный publish validate/clone/install:15 samples, total2,5–806,7ms, mean204,2ms; copy/install1,5–2,3ms, mean1,79ms. Это диагностический loopback/headless Chrome профиль, не SLA и не чистое время solver. Выбор использует cached geometry, новый DTO/width/fontRevision — новый layout. Детерминированные bound100000 search nodes и конечная route graph не доказывают latency всех карт. При поддерживаемом dense counterexample сохранять DTO/bounds/routes и адресно возвращать work item, не считать local-error принятой feature.

Не проверены Firefox/WebKit/иная ОС/реальное мобильное устройство, screen reader, browser zoom отличный от1, live HTTPS/deployment, нагрузка и универсальная осуществимость всех допустимых DTO. DPR2 и тестовый font fallback — выполнены. Нет нового performance SLA / новых quality gates. PUML проверяется структурно; render PNG не выполнялся. Платные/сетевые smoke-тесты не запускались.

Пакет локальный: index EMPTY, новый OutputSHA / CandidateSHA отсутствует. Commit/push/merge/PR и сообщения другим чатам не выполнялись. Старые D003/D005/run03 research и manifests остаются на исходных версиях. Manager/Analyst/Tester/gates не изменялись; independent review и Owner acceptance не заменяются этим evidence.
