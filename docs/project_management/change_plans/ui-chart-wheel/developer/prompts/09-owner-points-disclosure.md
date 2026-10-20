# TASK-D-007 — Owner: первые пять планет

Codex / Developer. Исполнено по прямому поручению Owner20.10.2026; [точная дельта контракта](../owner_decision_points_disclosure_2026-10-20.md). InputSHA `0da99518ada67603b08ab4220d337e3a5e3aae60`,branch dev/ui-chart-wheel. [Нормативный baseline](../../analyst/requirements.md) REQ-UI-03/04/05, REQ-WHEEL-07/08/09/10/11 и принятый S1 сохраняются кроме явной Owner-дельты all-points → first-five table. Текущий scope не затрагивает renderer geometry,engine/API/golden/dependencies или регистрацию предыдущего долга.

Результат: три независимых five/all раскрытия; остальные source points retained; aspect participants bypass table limit; automatic acceptance preserve / existing accepted-birth reset once; native keyboard/focus и dispose.

Разрешённые файлы: src/exact_orb/http_api/ui/chart_state.mjs,facts.mjs; tests/ui/chart_selection.test.mjs,aspect_view.test.mjs; собственные Developer plan/handoff/Owner evidence/этот prompt. Подход — TDD: существующие mounted tests проверяют раскрытие houses/aspects и сохранённый DOM; обновить намеренно изменённое ожидание all-points, добавить две чувствительные регрессии points disclosure/reset/focus и использовать реальный app с контролируемым HTTP leaf в Chrome/Yandex.

| Сценарий | Expected / контроль |
|---|---|
| Начальный natal/cosmogram | min(5,count) канонических source строк; count≤5 скрывает кнопку |
| Reveal/collapse | Независимо от houses/aspects,aria-controls/expanded,Enter/Space,no HTTP;16/5 на published fixture |
| Aspect с поздней точкой | Source participants видны вне лимита,кнопка скрыта;close возвращает раскрытие |
| Automatic/new acceptance | Preserve раскрытия;reset новой birth once;повтор того же event не reset |
| Focus/dispose | Planet selection остаётся в native control;скрытый active row получает живую кнопку;dispose снимает listener |
| SVG | Все16точек полного колеса остаются,лимит только в HTML |

Проверки: node --test tests/ui/chart_selection.test.mjs tests/ui/aspect_view.test.mjs; весь tests/ui; Python UI delivery+module boundaries,затем pytest -q; browser.cjs run02;git diff --check. Raw RED и ошибочное ожидание harness остаются отдельно. Точные команды/результаты — [evidence](../evidence/task_d007_points_disclosure/README.md). Commit/push отдельно не поручены.
