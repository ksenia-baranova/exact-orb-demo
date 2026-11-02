---
id: TASK-A-03
change: terms-of-use
role: analyst
kind: resolve_findings
gate: READY_FOR_TEST
cycle: 1
inputs: [DP-R-01]
origin: TASK-R-01
agent: null
model: null
status: NEW
resolution: null
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: null
estimate: null
---
## Задание

Разобрать [DP-R-01](../dp/DP-R-01.md): что показывать в нетронутой, включая пустую, форме после чтения условий, если первичный current пришёл с сохранённой картой.

Сопоставить REQ-UI-11, REQ-TERMS-04/D3, AS-TERMS-10, утверждённый план и [решение Owner](TASK-O-02.md). Установить ожидаемый результат для T-29 и [BUG-001](../bugs/BUG-001.md): ответ во время чтения и после обоих возвратов; контроль — восстановление без открытия условий.

Уточнение без изменения поведения решить по источникам. Продуктовый выбор обсудить с Owner. Рекомендация Reviewer не является принятым решением.

Заполнить «Решение» и changes_reqs в DP, changed_reqs и результат задачи. Если решение меняет требования, явно указать это для перехода 17 и нового APPROVAL.

Production-код, тесты, current/, чужие задачи и статус изменения не менять. Один коммит своих файлов; push и оркестратор не запускать. Итог кратко: решение, основания, затронутые REQ и следующий шаг.

Правила — docs/development_approach/process/change-process-v3.md, разделы «Задача (Task)», «DP и правила ALIGNMENT» и переход 17.

## Результат

## Findings

## Риски
