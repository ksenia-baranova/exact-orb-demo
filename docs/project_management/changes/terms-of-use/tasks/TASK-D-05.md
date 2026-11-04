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
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: ':/terms-of-use.*TASK-D-05.*fix'
estimate: {human_hours: 1.0, agent_hours: 0.5, confidence: high}
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

Исходные ветка `change/terms-of-use` и HEAD
`833936c437307e9082226cdd257074460cdfab88` проверены. Назначение Owner из этой
задачи разрешает Developer исправить BUG-003 в общей рабочей копии. Оценка
исправления, проверок и самопроверки: 1 чч / 0.5 мч; независимое ревью сюда не входит.

Подход — существующие тесты: BUG-003 является находкой о лишнем коде, а не
нарушением пользовательского поведения. До исправления целевые тесты уже проходили.
Падающий тест на текст реализации и дубли не добавлены. Регрессии
`late initial current`, `pending build`, `safe recovery`, `automatic current` и
`render failure` проверяют реальные mount/form/coordinator/transport/result,
публичные переходы, черновик, видимый фокус и отсутствие лишнего POST.

Причина — три проверки `!termsOpen` дублировали условия принадлежности фокуса.
`openTerms` синхронно переводит его на заголовок условий; редактор, результат и
кнопка повторной проверки не содержат активный элемент во время чтения.
В `main.mjs` удалены только эти три конъюнкции из `setEditorOpen`/`renderSession`.
Все вызывающие найдены через `rg`: `setEditorOpen` используется только в композиции
`main.mjs`, `renderSession` — callback `onChange` session coordinator.

Защита `!termsOpen && issueField` после `await session.submit()` сохранена:
поздний серверный issue не зависит от положения фокуса, поэтому без guard
фокус переходил бы на скрытое поле. Необходимость подтверждена изолированной
мутацией production-модуля; рабочая копия при мутации не менялась.
BUG-003 переведён в FIXED с `fixed_in` и существующими regression-тестами.

### Фактические проверки

Команды выполнены от корня рабочей копии, Node v24.22.1, Python 3.14.0,
pytest 9.0.2. Зависимости не устанавливались.

| Команда | Фактический результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs` до исправления | 53 PASS, 0 FAIL, 0 SKIP |
| `node --test tests/ui/terms.test.mjs` после исправления | 53 PASS, 0 FAIL, 0 SKIP |
| `node --test --test-name-pattern="pending build / field error\|mounted server time issue" tests/ui/terms.test.mjs tests/ui/session.test.mjs` в изолированной копии | Guard сохранён: 3 PASS; удалён: 1 PASS / 2 ожидаемых FAIL; восстановлен: 3 PASS |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` в sandbox | Прерван без вывода и результата, exit 1; не PASS |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` вне sandbox | 347 PASS за 24.37 с, включая доставку UI / installed wheel |
| `python -m pytest` вне sandbox | 2978 PASS, 1 SKIPPED за 152.23 с; `tests/test_configurations.py:473`, DEBT-CALC-001 |
| `git diff --check` и `git diff --cached --check` | PASS |
| Проверка YAML, защищённых полей ролей и трёх разрешённых путей | PASS |
| Сверка SHA-256 файлов и исходного untracked inventory | 3847 файлов без изменений; те же 32 untracked-файла |

Для мутации во временную изолированную копию перенесены `src/exact_orb/http_api/ui`,
`tests/ui`, `tests/http_api/golden`, `tests/fixtures/places.jsonl`.
Менялось только `if (!termsOpen && issueField)` → `if (issueField)`.
Оба `pending build / field error / agree|back` падали именно на
`expected focus terms-back, got birth-time`. Позитивный контроль
`mounted server time issue appears next to time, focuses it and clears on correction`
оставался PASS во всех трёх запусках. Тесты используют deferred/fake clock, не sleep.

Первый sandbox-запуск Python-проверки не засчитан. Sandbox также запретил запись
в свой системный временный каталог при сохранении снимка; снимок успешно создан
вне sandbox. Успешные pytest-команды выполнены вне sandbox. SKIPPED не считается PASS.

### Упрощение, сложность и коммит

Diff перечитан: ровно три удаления конъюнкции без новых функций, веток, зависимостей,
таймеров или shortcut-ов. В `setEditorOpen` стало на одно логическое условие меньше,
в `renderSession` — на два. Оставлены существующие точки передачи фокуса;
большой `mountBirthForm` не перестраивался вне границ задачи.
`importlib.util.find_spec('radon')` → None; численные CC до/после — NOT RUN.
Radon не устанавливался и к JS не применяется; production Python не менялся.

Поля `commit` задачи и `fixed_in` бага используют принятую в TASK-D-02/03 Git
revision уникального сообщения единственного коммита, чтобы не включать SHA
коммита в его собственное содержимое. Разрешение:
`git rev-parse ':/terms-of-use.*TASK-D-05.*fix'`.
Полный SHA поставки приведён в итоговом сообщении. Коммит содержит только
`main.mjs`, BUG-003 и эту задачу; исходный index был пуст.

## Findings

Новых DP/багов нет. Публичные API, требования, ADR, sequences, тесты Developer и
Tester, чужие задачи, change.md и events.jsonl сохранены. DP-R-01 остаётся ON_HOLD;
эта задача не меняет семантику первичного current. Push и оркестратор не запускались.

## Риски

Нативный браузер, layout/focus-visible и отдельная независимая приёмка — NOT RUN
в этой задаче. DOM-port проверяет активный элемент и видимость всех его предков,
но не заменяет браузер. Существующий DEBT-CALC-001 остаётся SKIPPED.
FIXED у BUG-003 не означает CLOSED: закрытие — после независимой перепроверки Reviewer.

Следующий шаг: независимая перепроверка Reviewer после всех трёх bug_fix задач;
переход процесса выполняет Owner/оркестратор отдельно, не в этом запуске.
