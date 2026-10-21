# Условная колонка: полный SVG и isolated renderer boundary

**Codex / Developer,19.10.2026. Локальное research evidence.** [Правила/вывод](../../column_renderer_design_v1.md), [план40–64ч](../../full_wheel_implementation_plan.md), [DRAFT ADR](../../drawing_adr_column_draft.md). InputSHA07bb56ba5d49ec76de64df41ad80d175fbe90a2d, прямое поручение Owner. Production не изменена.

## Итоговая версия и границы

Authoritative measured candidate — **run07-ports** с собственными source hashes/snapshots. [Native audit](run07-ports-audit.json):29/29 конфигураций,92 native exact-contact observations+12 unmoved+3 hidden-mode exemptions,13 native controls,4 rational controls. [Independent post-audit](run07-ports-post-audit.json):C0/order/row/clip/no-shared-centerline29/29,3 route controls. [Boundary28/28](run07-ports/boundary.json), [metadata](run07-ports/index.json), [screenshots](run07-ports/screenshots/F3-max-328-normal-none-dpr1.png). Количество конфигураций не означает29 независимых карт: source labels, widths, selections, DPR и font cases различаются; provenance replay существующего natal fixture не является новой domain fixture.

Начало/потолок — [spec](spec.json), [sources](sources.json), [data](data.json). Полная исходная матрица:7 labels×3frames720/448/328 (viewport1440/768/360), fallback+point/conjunction/aspect/background selections и DPR2, S1/palette/empty controls. Оригинальные7 source objects неизменны при добавлении3 явно synthetic controls. Исследовательские synthetic facts не считаются golden/API validation examples и не переносятся в приложение автоматически.

Реально измерены bbox/CTM/CSS coordinates и CDP platform fonts, native SVG/chart-source stability, foreign-label/anchor gap, frozen labels, clipping и source eligible aspect set. Root1:1 CSS, zoom1; Chrome155.0.8059.40/Windows, Node24, fonts Segoe UI Symbol/UI/Emoji + Arial/Cambria Math. Не запускались production page/HTTPS/full pytest, иной browser/OS/device, zoom/accessibility acceptance или performance benchmark. Numeric path ownership/bridge не заменяет человеческую читаемость.

## История без подмены результатов

- run01:15/26 static; anchor occlusion и asymmetric row bounds проявились в fallback.
- variant02 / run02:26/26 static; column/default radius/true anchors исправлены,4 fallback aux certificates UNPROVEN.
- variant03 / run03:29/29 static; independent aux contacts доопределены. Real-SVG boundary positive FAIL: CSSOM expands overflow shorthand, helper allowlist ошибочно отвергал его. Record сохранён.
- variant04 / run04-boundary:28/28 после явного allowlist fix и current-late-positive.
- variant05 / run05-final:paint order якорей исправлен,29/29 static. Поздний exact branch audit **только11/29** без shared segment. [Negative report](run05-final-post-audit.json) сохранён; прежний stop не объявляется полным PASS.
- variant06 / run06-routes:23/29 после запрета shared edges; слишком бедный граф дал отсутствующие routes.
- variant07 / run07-ports:original safe corners+ports/detour graph,29/29 статических и branch predicates,28/28 boundary.

[Первая остановка](stop.json), [корректирующее продолжение](variant06.json) в исходном90мин потолке и [окончательная остановка](final_stop.json) сохранены. Wall71,8126мин — не Developer effort. После final_stop модели/browser не запускаются. Partial PowerShell date-metadata error сохранён в final_stop_initial.json и исправлен ISO Python parsing, timestamp остановки не изменён.

## Команды фактических проверок

Из корня репозитория, Node/Python — существующие bundled runtime, Playwright и Chrome уже установлены; новые dependencies не добавлены:

```text
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/browser.cjs run07-ports
python docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/audit.py run07-ports
python docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/postaudit_final.py run05-final
python docs/project_management/change_plans/ui-chart-wheel/developer/evidence/column_full_composition_v1/postaudit_final.py run07-ports
```

Browser exit0; final audits exit0. run05-final post-audit ожидаемо exit1 — preserved negative control shared routes, не ошибка финального кандидата.13 native calibrations включают2px equality/below, diagonal, forbidden region, clipping, em16/12 и scale;4 rational gap controls и3 route controls имеют независимые positive/negative expected. Непроведённый runtime не маркируется PASS.

`browser.cjs` не перезаписывает существующие run directories и проверяет исходный deadline; replay после stop не выполнялся. Для назначенного независимого replay скопировать нужный frozen sources snapshot в новый evidence-root, сохранить source hashes, отдельно зарегистрировать новый run/deadline и указать факт изменения orchestration metadata. Не менять первоначальные specs или старый deadline ради replay. Скрипты используют абсолютный путь текущего bundled Playwright/Chrome как требование окружения, не приложение dependency.

Audit scripts проверяют сохранённые records без browser/placement. Исходные `audit_v1.py`, `audit_v2.py`, `audit_v3_initial.py` и старый post-audit сохранены; финальный auditor различает endpoint feasibility и legal full-prefix probe. Source/native evidence D003/D005/v3/preview и index сохранены по before.json; final package validation дописывается в handoff. Publication NOT RUN, нового OutputSHA нет.
