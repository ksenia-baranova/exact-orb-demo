# UI: поведение и технические sequences

Текущий контракт M1-8: [колесо](../../requirements/current/ui/chart-wheel.md), [форма и факты](../../requirements/current/ui/birth-form-and-facts.md), [сценарии](../../requirements/current/ui/scenarios.md). Перенос выполнен Codex / Manager21.10 по прямому поручению Owner; source versions / точное соответствие — [transfer map](../../project_management/change_plans/ui-chart-wheel/analyst/transfer_map.md). Он не означает нового runtime-run или независимого approval архитектурного ADR.

M1-9 добавляет [условия использования](../../requirements/current/ui/terms-of-use.md), замену REQ-UI-03 и AS-UI-20/21. Источник — [инкремент terms-of-use](../../project_management/changes/terms-of-use/requirements.md); перенос TASK-A-04, 2026-11-03. Противоречие первичного current и сохранения нетронутого черновика оставлено по [DP-R-01 ON_HOLD](../../project_management/changes/terms-of-use/dp/DP-R-01.md); нормативный вариант не выбран. Это перенос документов без нового runtime evidence или приёмки.

## Поведение

| Схема | Область |
|---|---|
| [001 — получение и показ](001-chart-presentation.puml) | Один принятый DTO, source facts / passive SVG, initial/current/empty/unavailable, местный отказ |
| [002 — HTML-выбор и возврат](002-wheel-table-selection.puml) | Полный S1 index, point-filter, aspect reading/focus/return и независимые first-five/all |
| [003 — draft и recovery](003-edit-and-recovery.puml) | Исходный HTTP-контракт, immutable submit, fresh live target, once-reset/collapse |
| [009 — условия и возвраты](009-terms-roundtrip.puml) | T1…T4, текст C1…C8, checkbox и видимый фокус |
| [010 — черновик условий](010-terms-draft-lifecycle.puml) | D1…D3 при обоих возвратах, L1…L3 при новой загрузке |
| [011 — построение после ознакомления](011-terms-build-boundary.puml) | G1…G4, R1…R3, HTTP/recovery и отсутствие POST при переходах |

## Техническое устройство реализации

Схемы описывают реализованный вариант, сохраняя ссылки на авторские Developer-версии. Технический [ADR-0042](../../requirements/decisions/0042-passive-chart-renderer.md) и [обязанности компонентов](../../requirements/component_responsibilities/exact-orb_chart_renderer.md) подготовлены TASK-D-008; ADR принят Owner21.10 для текущего пассивного M1-8; активное колесо — будущая отдельная фича.

| Схема | Область |
|---|---|
| [003 — passive copy/install](technical/003-passive-copy-install.puml) | Leaf boundary, lease/revision, измерительная поверхность, guard/clone/install и местный отказ |
| [005 — accepted once](technical/005-accepted-once-editor.puml) | Подтверждение живой цели / already_applied / неизменяемый draft |
| [006 — aspect reading](technical/006-aspect-reading-mode.puml) | Участники и их source houses, вход/фокус, возврат/Escape |
| [007 — внутренние ряды](technical/007-internal-house-rows.puml) | Source house и истинные anchors вместо выносной колонки |
| [008 — viewport/legend/vectors](technical/008-viewport-legend-vectors.puml) | Конечная ширина до draw, палитра, native text/vector bounds |

Заменённые исследовательские варианты001/002/004 находятся [в отдельном архивном разделе](../research/ui-chart-wheel/README.md). Они не действующий контракт. У всех current схем тот же HTML-only выбор; SVG controls/Q44 не возвращаются. DEBT-UI-004 сохраняет пределы доказательств плотности/точности.
