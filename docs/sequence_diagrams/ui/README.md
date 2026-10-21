# UI: поведение и технические sequences

Текущий контракт M1-8: [колесо](../../requirements/current/ui/chart-wheel.md), [форма и факты](../../requirements/current/ui/birth-form-and-facts.md), [сценарии](../../requirements/current/ui/scenarios.md). Перенос выполнен Codex / Manager21.10 по прямому поручению Owner; source versions / точное соответствие — [transfer map](../../project_management/change_plans/ui-chart-wheel/analyst/transfer_map.md). Он не означает нового runtime-run или независимого approval архитектурного ADR.

## Поведение

| Схема | Область |
|---|---|
| [001 — получение и показ](001-chart-presentation.puml) | Один принятый DTO, source facts / passive SVG, initial/current/empty/unavailable, местный отказ |
| [002 — HTML-выбор и возврат](002-wheel-table-selection.puml) | Полный S1 index, point-filter, aspect reading/focus/return и независимые first-five/all |
| [003 — draft и recovery](003-edit-and-recovery.puml) | Исходный HTTP-контракт, immutable submit, fresh live target, once-reset/collapse |

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
