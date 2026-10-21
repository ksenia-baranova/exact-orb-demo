# A006 — прямое решение Owner для already_applied

**Codex / Developer, 20.10.2026. TASK-D-007 / DRAFT.** SourceRef: ответ Owner в текущем Developer-чате на конкретный вопрос о POST с изменённой целью B и fresh GET birth=B:

> Как fresh matched recovery: reset один раз, collapse только при draft=B

InputSHA / AssignmentSHA: e0daa0e814d3d1fd34cadb8c17d064f19c4810f5. Принятый Analyst v3+S1: 2736e2848c977ec4c770a9a4dec2a0d7c1b62a71. Это прямой дополнительный вход Owner, а не опубликованный Analyst OutputSHA, закрытие TASK-A-006 или изменение Manager DP/gates.

## Реализованное различение

| Событие | Reset / editor | Источник фактов |
|---|---|---|
| Собственный committed POST с изменённой относительно принятой A birth B | Один reset, collapse только при текущем draft=B | POST ChartDTO + immutable submitted summary B |
| POST already_applied, следующий fresh GET chart_ready birth=B и живая цель B | Один reset при changed birth; collapse только при draft=B | Только GET ChartDTO / birth; внутренний cause already_applied_target_confirmed |
| Уже та же birth, новая identity | Reset не требуется; однократный collapse при совпавшем draft | Соответствующий принятый ответ |
| GET stale B / другая birth / empty / failed | Цель не подтверждена, reset/collapse по этой цели нет | Валидные GET факты принимаются обычным сохраняющим reconcile; failed не создаёт acceptance |
| Повторный GET B после подтверждения | Обычный reconcile; выбор/раскрытия/открытый пользователем editor сохраняются | GET |
| RESULT_SUPERSEDED даже с GET B | Собственное подтверждение не выводится; сохраняющий reconcile | GET |

Attempt создаётся только при допущенном явном submit, с неизменяемой birth tuple и captured changed относительно принятой карты. Подтверждение потребляет эту живую цель; оно не восстанавливается из chart_identity, state_version, source=current, старого recovery matched или submittedIntent. Новый submit заменяет прежнюю цель. Тройка birth_date / birth_time / place_id и time_unknown согласуются через существующий intentMatchesBirth; новых расчётов нет.

Из ответа already_applied не делается вывод, что именно этот POST создал карту, и не добавляется server-producer token / HTTP поле. Recovery controls и safe GET остаются доступны при свёрнутых полях; автоматического POST нет.

## Проверяемый результат

[accepted_chart.test.mjs](../../../../../tests/ui/accepted_chart.test.mjs): fresh same/changed birth, stale/different/failed GET с последующим fresh positive, once, RESULT_SUPERSEDED, immutable B при draft C и edit→revert B. [Native evidence](evidence/task_d007_runtime/README.md) дополнительно проверяет фактическую страницу на трёх ширинах.

Первый целевой запуск до изменения session.mjs: 6 PASS / 6 FAIL, именно новые ожидания cause/reset/collapse; импорты и существующие сценарии работали. После реализации: 12 PASS / 0 FAIL. Код и Developer tests изменены в разрешённом scope; чужие артефакты и исходные goldens сохранены.
