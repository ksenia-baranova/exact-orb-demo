# Пакет06 — исправление композиции и режима аспекта по Owner

**Codex / Developer,20.10.2026. Исполненный корректирующий пакет TASK-D-007, DRAFT.** Прямое поручение Owner в Developer-чате: дома неразличимы, колесо должно следовать приложенному образцу; при выборе аспекта переносить focus к колесу и оставлять относящиеся к нему факты. Явное уточнение Owner: «Да: две планеты и только их дома». Screenshot браузера показывает50% zoom; app не компенсирует это CSS zoom.

InputSHA e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, существующий dev/ui-chart-wheel/worktree; предыдущие FW/чёрная тема и index сохраняются. Contract base v3+S1@2736e28 + более поздние Owner delta; выбранный аспект — новая адресная дельта REQ-WHEEL-02/07/08, REQ-UI-05/06/10. Старое отсутствие переноса focus относится теперь только к planet activation; независимые five/all возвращаются при выходе из aspect view. Без изменения source DTO, HTTP, engine/projector/golden/deps.

Разрешённые UI пути: facts/main/index/styles/wheel_layout/wheel_svg/result_controller и соответствующие Node tests/собственный Developer evidence. Manager/Analyst/Tester/gates не меняются. Runtime остаётся passive; focus получает HTML region, а не SVG control.

1. Рисовать отдельный пояс source houses1…12 и границы между опубликованными соседними cusp_longitude; номер помещать в midpoint сектора как геометрию представления. Не вычислять принадлежность points дому.
2. Увеличить полезную область аспектов, добавить угловую шкалу; сохранить source anchors, em16/12, gap2, локальные auxiliary certificates и условную колонку. Проверить native wide/tablet/mobile; не принимать систематический FAIL через local warning.
3. Для выбранного unique аспекта full-source index остаётся исходным; SVG display subset содержит только endpoints и их published houses, HTML — одну строку аспекта, endpoint point rows и distinct source house numbers. Angle/unknown-time house не синтезировать.
4. Фокус/scroll только по явному aspect action; после текущего SVG settlement scroll допускается лишь при той же selection и focus на wheel. Escape/кнопка восстанавливают полную карту и раскрытия, focus — к живому исходному control. Resize/fonts/automatic current не создают новый focus intent.
5. Избежать дублирующей свёрнутой формы; recovery остаётся видимым при error/reconciliation. Выбранное колесо и возврат должны помещаться в viewport; CSS width→layout, без уменьшения SVG fonts/viewBox scale.
6. Чувствительные Node tests сначала RED на старом поведении, затем target/full UI; native real app с HTTP leaf fake, source coordinates/rows/focus/viewport/S1/recovery,53 Python delivery/boundaries→full pytest. Приёмка Tester/Owner отдельно; commit/push/merge/PR по отдельному поручению.

[Фактический план §9](../full_wheel_implementation_plan.md#9-task-d-007--исправления-композиции-по-owner2010), [команды/actual/ограничения](../evidence/task_d007_composition_v2/README.md), [sequence006](../sequence_diagrams/ui/006-aspect-reading-mode.puml).
