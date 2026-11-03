---
id: TASK-D-05
change: terms-of-use
role: developer
kind: bug_fix
gate: BUG_FIX
cycle: 1
inputs: [BUG-003]
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

Исправить [BUG-003](../bugs/BUG-003.md): убрать три лишних проверки `!termsOpen` в setEditorOpen/renderSession. Нужную защиту фокуса в продолжении submit сохранить.

Если защита достижима, обосновать её сценарием и тестом вместо удаления. Проверить публичное поведение фокуса, поздних ответов и возвратов; использовать существующие регрессионные тесты, не проверять текст реализации.

Менять только main.mjs, необходимые Developer-тесты, BUG-003 и свою задачу. Приёмочные тесты Tester и требования не менять.

После исправления заполнить в BUG-003 status: FIXED, fixed_in и regression_test. Закрывает баг Reviewer после независимой перепроверки.

Проверки: целевые → связанные → полный pytest; NOT RUN не считать PASS. Записать краткий результат и точный SHA, сделать один коммит своих файлов. Чужие изменения сохранить; push и оркестратор не запускать.

Ручное распределение назначено Owner. Выполнять задачи по одной в общей рабочей копии; рекомендуемый порядок: TASK-D-05 → TASK-T-03 → TASK-T-04. Следующий переход — после завершения всех трёх задач и статуса FIXED у трёх багов; затем требуется независимая перепроверка Reviewer.

Правила — docs/development_approach/process/change-process-v3.md; эта задача — явно назначенное Owner исключение стандартного распределения bug_fix.

## Результат

## Findings

## Риски
