---
id: TASK-T-04
change: terms-of-use
role: tester
kind: bug_fix
gate: BUG_FIX
cycle: 1
inputs: [BUG-002]
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

По прямому поручению Owner исправить [BUG-002](../bugs/BUG-002.md) в приёмочных тестах Tester.

Проверить последовательность: попытка построения без отметки (G2) → открытие условий → «Согласен». До возврата ошибка видна и aria-invalid=true; после возврата checkbox выбран, ошибка скрыта и aria-invalid=false. Переход не создаёт POST.

Подтвердить, что новый тест падает без перерисовки ошибок после «Согласен» в изолированной копии. Рабочий production не менять. Разрешены acceptance-тесты, необходимые фикстуры, статусы проверенных карточек плана, BUG-002 и своя задача; тесты Developer не менять.

После исправления заполнить в BUG-002 status: FIXED, fixed_in и regression_test. Закрывает баг Reviewer после независимой перепроверки.

Проверки: целевые → связанные → полный pytest; NOT RUN не считать PASS. Записать краткий результат и точный SHA, сделать один коммит своих файлов. Чужие изменения сохранить; push и оркестратор не запускать.

Ручное распределение назначено Owner. Выполнять задачи по одной в общей рабочей копии; рекомендуемый порядок: TASK-D-05 → TASK-T-03 → TASK-T-04. Следующий переход — после завершения всех трёх задач и статуса FIXED у трёх багов; затем требуется независимая перепроверка Reviewer.

Правила — docs/development_approach/process/change-process-v3.md; эта задача — явно назначенное Owner исключение стандартного распределения bug_fix.

## Результат

## Findings

## Риски
