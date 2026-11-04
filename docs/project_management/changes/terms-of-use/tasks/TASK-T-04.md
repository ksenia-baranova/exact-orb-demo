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
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: [REQ-UI-03, REQ-TERMS-02, REQ-TERMS-05]
commit: ':/terms-of-use.*TASK-T-04.*test'
estimate: {human_hours: 2, agent_hours: 0.7, confidence: high}
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

TASK-T-04 завершена: **T-31 PASS, BUG-002 FIXED; 0 FAIL, 0 NOT RUN, 0 BLOCKED в назначенном сценарии**. Независимое закрытие BUG-002 принадлежит Reviewer. Один коммит TASK-T-04 содержит только её acceptance-правки, T-31 плана, BUG-002 и этот файл. `commit` и `fixed_in` — Git revision `:/terms-of-use.*TASK-T-04.*test`, разрешаемый в точный SHA командой `git rev-parse`; это позволяет не добавлять второй коммит только ради самоссылки.

План T-31 записан до чтения production и Developer-тестов. Добавлен отдельный приёмочный сценарий `acknowledgement_error` с REQ-метками: G2 показывает ошибку и `aria-invalid="true"`; T1 возвращает видимую форму с выбранной отметкой, скрытой/очищенной ошибкой и `aria-invalid="false"`. При открытии и «Согласен» прирост POST равен нулю; отдельный G4 отправляет один POST тем же измерителем. Production, требования и Developer-тесты не менялись.

Исходная база: `change/terms-of-use` @ `0d6a8fc48d11f33bcf874aaf7c8d259da087e1c6`. Среда: Windows, Python 3.14.0, pytest 9.0.2, Node v24.22.1. Никакие зависимости не устанавливались.

### Чувствительность T-31

Python probe создал `TemporaryDirectory(prefix='terms-t04-', dir='logs')`, скопировал `src/exact_orb/http_api/ui`, `tests/ui/fixtures`, `tests/http_api/golden`, `tests/fixtures` и текущий `tests/acceptance/terms_acceptance.mjs`. В этой копии трижды выполнена точная команда `node tests/acceptance/terms_acceptance.mjs acknowledgement_error`:

| Вариант | Результат |
| --- | --- |
| Исходный production | 1 пример PASS, exit 0 |
| Удалён только `renderErrors();` между `setEditorOpen(true);` и `termsLink.focus();` в `returnFromTerms` | FAIL, exit 1: `agree must hide the existing G2 error`, `false !== true` |
| Восстановлены исходные байты main.mjs | 1 пример PASS, exit 0 |

Перед заменой проверено единственное совпадение указанного фрагмента; после probe проверено побайтовое равенство рабочего main.mjs исходному. Его SHA-256: `2ca4874ed2c55a447afb8ec1d0801d0ccf571fffd1789b9521451dab3ca3a3a1`. Временная копия удалена средствами `TemporaryDirectory`. Это ожидаемый красный контроль, а не FAIL рабочей реализации.

### Прогоны

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest 'tests/acceptance/test_terms_ui.py::test_terms_composition[acknowledgement_error]' -q -s --tb=short` | 1 PASS, 0.51 с, exit 0 |
| `python -u -m pytest tests/acceptance -q -s --tb=short --show-capture=no` (вне sandbox) | 18 PASS, 24.53 с, exit 0; 160 примеров композиции и 80 браузерных примеров, Chrome 155.0.8059.40 |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP, exit 0 |
| `python -u -m pytest tests/http_api tests/test_module_boundaries.py -q` (вне sandbox) | 347 PASS, 26.10 с, exit 0 |
| `python -u -m pytest -q` (вне sandbox) | 2978 PASS, отдельно 1 SKIPPED (`tests/test_configurations.py:473`, DEBT-CALC-001), 152.35 с, exit 0 |
| `python scripts/req_coverage.py docs/project_management/changes/terms-of-use --matrix` | 9/9 REQ с тестами, 2979 тестов собрано, пробелов нет, exit 0 |
| `git diff --check` | PASS, exit 0 |

Перед коммитом TASK-T-04 проверена база `e21e3130f2fc258299b50a1722c5fd943678eca9` (отдельный коммит TASK-T-03), индекс был пуст. Повторный целевой запуск той же команды: 1 PASS, 0.54 с, exit 0. В diff остаются только пять файлов TASK-T-04; production и Developer-тесты не затронуты.

Порядок: целевой сценарий → чувствительность в копии → приёмочные → связанные → полный pytest → req coverage. SKIPPED и прерванные sandbox-запуски не включены в PASS. Таблица матрицы ниже — сокращённая запись фактического вывода покрытия; `composition[...]` и `browser[...]` означают `tests/acceptance/test_terms_ui.py::test_terms_composition[...]` и `::test_terms_browser[...]`.

| REQ | Исполненные приёмочные сценарии |
| --- | --- |
| REQ-UI-03 | все 5 HTTP-проверок; composition[isolation/gates/acknowledgement_error/payload/current/recovery/issues]; browser[reload/builds] |
| REQ-TERMS-01 | composition[roundtrips]; browser[presentation/keyboard/builds] |
| REQ-TERMS-02 | composition[roundtrips/acknowledgement_error/payload]; browser[keyboard/reload/builds] |
| REQ-TERMS-03 | composition[roundtrips]; browser[keyboard] |
| REQ-TERMS-04 | composition[roundtrips/current]; browser[builds] |
| REQ-TERMS-05 | test_terms_contract.py::test_no_consent_persistence_and_build_trace; composition[roundtrips/isolation/acknowledgement_error/payload/current]; browser[builds] |
| REQ-TERMS-06 | browser[presentation] |
| REQ-TERMS-07 | test_terms_contract.py::test_no_consent_persistence_and_build_trace; composition[gates/payload]; browser[reload] |
| REQ-TERMS-08 | browser[keyboard/targets] |

Матрица подтверждает наличие тестов, не заменяя новый независимый аудит всех 30 исторических карточек. T-31 дополнительно проверена на контролируемой поломке. Старые статусы остальных карточек TASK-T-02 этой задачей не переобъявляются.

## Findings

Корневая причина BUG-002 — отсутствовало покрытие перехода G2 → T1: проверка выбранной отметки и нулевого POST не обнаруживала оставшуюся видимой ошибку и устаревший `aria-invalid`. По прямому поручению Owner исправлены именно acceptance-тесты, первоначально предложенный Reviewer путь `tests/ui/terms.test.mjs` не изменялся. BUG-002 закрывает Reviewer после независимой перепроверки.

## Риски

В ходе работы обнаружены параллельные правки TASK-T-03 в общем JS runner и своей задаче; они не принадлежат TASK-T-04 и должны остаться вне её коммита. При старте TASK-D-05 и TASK-T-03 были NEW; состояние чужих задач и общий lifecycle не меняются.

Первые приёмочные запуски в sandbox прерваны без завершённого результата. Диагностическая команда `python -u -m pytest 'tests/acceptance/test_terms_contract.py::test_validation_before_cookie[None]' -vv -s --tb=short -o faulthandler_timeout=25` показала зависание `socket._fallback_socketpair → asyncio.proactor_events._make_self_pipe` при подготовке event loop, до выполнения HTTP-сценария. Таймаут использован только для диагностики окружения. Эти запуски не засчитаны как PASS; итоговые приёмочные, связанные Python-проверки и полный pytest выполнены вне sandbox.

Не выполнялись: независимое ревью/закрытие BUG-002, новое подтверждение опубликованной поставки C7, удалённый сервис, screen-reader, платные/сетевые LLM smoke и Owner acceptance. Риск изменения без перерисовки теперь обнаруживается T-31. Остальные BUG/DP и переход lifecycle этой задачей не разрешаются. Push и оркестратор не запускались.
