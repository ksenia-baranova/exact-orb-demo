---
id: TASK-T-03
change: terms-of-use
role: tester
kind: bug_fix
gate: BUG_FIX
cycle: 1
inputs: [BUG-001]
origin: TASK-R-01
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: [REQ-UI-03, REQ-UI-11, REQ-TERMS-02, REQ-TERMS-03, REQ-TERMS-04, REQ-TERMS-05]
commit: 0d6a8fc48d11f33bcf874aaf7c8d259da087e1c6
estimate: { чч: 4, мч: 1.5, confidence: medium }
---
## Задание

По прямому поручению Owner исправить [BUG-001](../bugs/BUG-001.md) в приёмочном сценарии T-29.

Удерживать первичный GET /charts/current до проверки, не завершать восстановление заранее. Проверить сохранение изменённого ввода при ответе во время чтения и после каждого возврата. Добавить позитивный контроль: без правок и открытия условий тот же ответ восстанавливает данные.

Ожидания взять из [TASK-A-03](TASK-A-03.md). Не закреплять новый нормативный оракул для нетронутой пустой формы после открытия условий: DP-R-01 остаётся ON_HOLD.

Подтвердить, что тест обнаруживает перезапись ввода при отключённой защите в изолированной копии. Рабочий production не менять. Разрешены acceptance-тесты, необходимые фикстуры, статусы проверенных карточек плана, BUG-001 и своя задача; тесты Developer не менять.

После исправления заполнить в BUG-001 status: FIXED, fixed_in и regression_test. Закрывает баг Reviewer после независимой перепроверки.

Проверки: целевые → связанные → полный pytest; NOT RUN не считать PASS. Записать краткий результат и точный SHA, сделать один коммит своих файлов. Чужие изменения сохранить; push и оркестратор не запускать.

Ручное распределение назначено Owner. Выполнять задачи по одной в общей рабочей копии; рекомендуемый порядок: TASK-D-05 → TASK-T-03 → TASK-T-04. Следующий переход — после завершения всех трёх задач и статуса FIXED у трёх багов; затем требуется независимая перепроверка Reviewer.

Правила — docs/development_approach/process/change-process-v3.md; эта задача — явно назначенное Owner исключение стандартного распределения bug_fix.

## Результат

### План до чтения реализации и тестов Developer

База: `0d6a8fc48d11f33bcf874aaf7c8d259da087e1c6`, ветка `change/terms-of-use`, рабочая копия из задания. Свежая оценка: **4 чч / 1.5 мч, confidence medium** (прогноз, не хронометраж). TASK-D-05 пока NEW; порядок в назначении рекомендательный, текущая прямая команда Owner назначает именно TASK-T-03. Чужая задача и BUG-003 не изменяются.

Корневая причина BUG-001 по входу Reviewer: T-29 проверяет повторный current после уже завершённого первичного восстановления; его PASS не доказывает защиту первичного заполнения. Исторический PASS этой части T-29 не считается новым evidence.

Независимый план, ожидаемые результаты — из [TASK-A-03](TASK-A-03.md), раздел «T-29 и BUG-001», REQ-TERMS-04/05, таблицы T и REQ-UI-03/11:

- Given первичный GET /charts/current удержан управляемым ответом, восстановление ещё не закончено; введён D, отличающийся от birth B по дате, месту и времени. Классы D: выбранное место и известное время; выбранное место и неизвестность со скрытой строкой времени; незавершённый ввод места без place_id и неполное время. Начальный checkbox — снят/выбран.
- When условия открыты; ответ B доставляется в отдельных проходах (1) во время чтения, (2) после «Согласен», (3) после «Вернуться к форме». Для ответа во время чтения проверить оба последующих возврата. Порядок задаётся deferred/barrier, без sleep; до доставки зафиксировать один незавершённый первичный GET.
- Then дата, текст места, выбранный place_id/название (либо отсутствие выбора), строка времени и неизвестность равны исходному D при доставке и после возврата; checkbox во время чтения не меняется, после «Согласен» выбран, после второго возврата равен исходному. Во время чтения условия остаются видимы и фокус на видимом элементе; после возврата раскрыт редактор с D. Карта/сводка принадлежат B; прирост POST = 0.
- Позитивный контроль: Given тот же удержанный первичный GET, без правок и без открытия условий; When доставлен B; Then форма заполнена birth B, редактор свёрнут, checkbox снят; «Изменить данные» раскрывает восстановленные значения без POST. Проверить известное и неизвестное время.
- Сохранить существующую проверку повторного current/живого выбора. Не вводить ожидание для нетронутой пустой формы после открытия условий: DP-R-01 остаётся ON_HOLD.
- В изолированной копии отключить проверку защиты при первичном заполнении, сохранив рабочий production. Новые примеры должны падать на сравнении D с birth B; позитивный контроль должен проходить. После восстановления изолированного production те же проверки должны пройти.

Проверки: целевой current через Node и pytest-wrapper → все сценарии acceptance-композиции и связанные UI/HTTP → полный pytest; затем `req_coverage.py --matrix`, `git diff --check` и проверка области коммита. Настоящий браузер и внешняя ссылка исходников не входят в исправление BUG-001; их исторические результаты не объявляются новым PASS.

### Исправление и проверка чувствительности

В `tests/acceptance/terms_acceptance.mjs` добавлены 24 примера: D1/D2/D3 × два возврата × два исходных checkbox × ответ во время чтения/после возврата. D отличается от B: дата `2000-02-29`, выбранный каталоговый `1819729` / «Гонконг» для D1/D2 либо `Го` без выбора для D3; время `23:59`, скрытое `12:00` с неизвестностью либо `12:6`. Подготовка выбранного места проходит через реальный поиск/transport и клавиатурный выбор; листовой HTTP отвечает item существующей фикстуры. Сохранённый B — существующий HTTP golden `ready()`. Все части D сверены с независимыми входами до перехода, затем при доставке и после возврата. Проверены принятие B/identity/сводка, видимость страницы и редактора, фокус, checkbox и отсутствие POST. Ещё два примера — восстановление известного/неизвестного времени без единой правки и без открытия условий; «Изменить данные» раскрывает birth B. Прежние 14 примеров повторного current/already_applied сохранены. Итого **40 примеров current**.

Реальны mount/form/places/session/transport/result; заменены только листовые HTTP, fake clock и DOM-port. В локальном адаптере acceptance добавлен отсутствующий у DOM-port `scrollIntoView`, без моделирования layout; первоначальный незавершённый запуск с `TypeError` исправлен на этом листовом шве и не считается PASS. Production и файлы Developer не изменялись.

Во время работы появились чужие изменения TASK-T-04 в общих runner/плане, wrapper, BUG-002 и TASK-T-04. Они сохраняются в рабочей копии, но исключаются из снимка проверки и коммита TASK-T-03. Итоговый снимок `logs/TASK-T-03-snapshot` получен через `git archive` точного исходного SHA и добавление только дельты TASK-T-03; это изолированная копия без ветки и без изменения рабочего production. SHA-256 acceptance-файла UTF-8/LF: `175cbc654b176e12ece63b7eb85f8da5bc992ed0bdb42126b40915f28fad03b7`.

На этом снимке трижды выполнена точная команда `node tests/acceptance/terms_acceptance.mjs current`:

| Production в изолированной копии | Результат |
| --- | --- |
| Исходный | 40 примеров PASS, exit 0 |
| В единственном условии первичного заполнения `!draftProtected && !birthRestored` заменено на `!birthRestored` | Два контроля восстановления PASS; затем exit 1, `AssertionError: initial current must preserve D: D1 agree checked=false afterReturn=false`; birth B затёр D |
| Восстановлены исходные байты | 40 примеров PASS, exit 0 |

Мутация не меняла acceptance-файл и не удаляла `birthRestored`: проверяется именно защита от первичного ответа. SHA-256 рабочего main.mjs до/после — `2ca4874ed2c55a447afb8ec1d0801d0ccf571fffd1789b9521451dab3ca3a3a1`; копии из Git с LF — `89ff045f9b3f37ef97a341060ed7b7e24a9948178231206f4db5922971c2e604`, восстановлены побайтово. Локальные `mutation-*.log` и `mutation-report.json` оставлены в ignored-каталоге снимка; воспроизводимое изменение и результат приведены здесь. Предварительная probe-копия `logs/TASK-T-03-mutation-9fb9aed7` включала параллельный, не запускаемый в current блок TASK-T-04; итоговое evidence выше повторено без него.

### Итоговые проверки

Windows, Python 3.14.0, pytest 9.0.2, Node v24.22.1. Команды ниже выполнены из `C:\Users\KateUser\PycharmProjects\exact-orb-recovered\logs\TASK-T-03-snapshot`: точный исходный commit из front matter плюс только исправленные acceptance-тесты TASK-T-03 с указанным выше hash. Зависимости не устанавливались. Связанный HTTP-прогон и полный pytest выполнены вне sandbox после прерванной диагностики окружения.

| Команда | Реальный результат |
| --- | --- |
| `node tests/acceptance/terms_acceptance.mjs current` | 40 примеров PASS, exit 0; отдельно ожидаемый mutant FAIL и restored PASS, см. выше |
| `python -m pytest 'tests/acceptance/test_terms_ui.py::test_terms_composition[current]' -q -s` | 1 PASS, 0.76 с; current — 40 примеров |
| `python -m pytest tests/acceptance/test_terms_ui.py::test_terms_composition -q -s` | 7 PASS, 1.90 с; 159 примеров |
| `node --test --test-reporter=dot tests/ui/*.test.mjs` | 282 PASS, exit 0 |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS, 32.43 с, exit 0 |
| `python -m pytest -q` | 2977 PASS, **1 SKIPPED** (`DEBT-CALC-001`), 155.08 с, exit 0 |
| `python scripts/req_coverage.py docs/project_management/changes/terms-of-use --matrix` | 9/9 REQ с тестами, 2978 собрано, пробелов нет, exit 0 |
| `git diff --check`; `git diff --cached --check` (основная копия) | PASS, exit 0; только предупреждение Git о нормализации LF/CRLF |
| `python -` (одноразовый аудит индекса через stdin, основная копия) | `STAGED_AUDIT PASS own_paths=4 tested_acceptance_bytes=EXACT assignment=UNCHANGED protected_fields=OK TASK=DONE BUG001=FIXED DP=UNCHANGED production_and_developer_tests=UNCHANGED T04=OUTSIDE_COMMIT local_links=5` |

Исправленная карточка T-29: **1 PASS, 0 FAIL, 0 NOT RUN, 0 BLOCKED**; остальные карточки не получают нового статуса из этого точечного исправления. Дополнительный ранний запуск композиции в общей копии включал чужой сценарий TASK-T-04 (8 PASS) и не подменяет итоговые 7 PASS на снимке TASK-T-03.

Матрица из `req_coverage.py --matrix`, компактное представление: сценарии колонок соответствуют `tests/acceptance/test_terms_ui.py::test_terms_composition[...]`, `::test_terms_browser[...]`; последний столбец — `tests/acceptance/test_terms_contract.py`.

| REQ | Composition | Browser | HTTP contract |
| --- | --- | --- | --- |
| REQ-UI-03 | isolation, gates, payload, current, recovery, issues | reload, builds | test_validation_before_cookie[None/acknowledged/consent_id/terms_version], test_no_consent_persistence_and_build_trace |
| REQ-TERMS-01 | roundtrips | presentation, keyboard, builds | — |
| REQ-TERMS-02 | roundtrips, payload | keyboard, reload, builds | — |
| REQ-TERMS-03 | roundtrips | keyboard | — |
| REQ-TERMS-04 | roundtrips, current | builds | — |
| REQ-TERMS-05 | roundtrips, isolation, payload, current | builds | test_no_consent_persistence_and_build_trace |
| REQ-TERMS-06 | — | presentation | — |
| REQ-TERMS-07 | gates, payload | reload | test_no_consent_persistence_and_build_trace |
| REQ-TERMS-08 | — | keyboard, targets | — |

BUG-001 переведён в FIXED, `regression_test` заполнен; CLOSED оставлен Reviewer. `fixed_in` — однозначная Git revision по уникальному заголовку единственного коммита `[terms-of-use][TASK-T-03] test: preserve draft on initial current`. Она разрешается командой `git rev-parse ':/^\[terms-of-use\]\[TASK-T-03\] test: preserve draft on initial current'`; буквальный SHA сообщается после создания коммита, без невозможной самоссылки SHA в собственное содержимое. Поле `commit` задачи — проверенная production-база, а не утверждение, что новые тесты уже были в ней. Финальная проверка разрешения ссылки выявила лишний `$` (конец всего commit message с телом); он удалён в том же единственном коммите через amend. Тестовый код не менялся, повторены проверки ссылки и области Git.

## Findings

BUG-001 — дефект приёмочного покрытия: прежний повторный current не достигал once-восстановления. Новое падение при отключении hydration guard подтверждает чувствительность T-29. Новый продуктовый дефект не найден, требований и публичных контрактов задача не меняет.

## Риски

- DP-R-01 остаётся ON_HOLD; конфликт REQ-UI-11/REQ-TERMS-04 для нетронутой пустой формы после открытия условий не разрешён и не закреплён новым тестом.
- Новый сценарий позднего первичного current проверен через DOM-port; это не новое доказательство поведения этой гонки в настоящем браузере или на live-стенде. Сетевые/платные smoke и публичный source-ref отдельно не запускались.
- Прерванные sandbox-прогоны связанных Python-тестов зависали на первом async-тесте до его результата; они не засчитаны как PASS. Повтор вне sandbox завершился: 347 PASS.
- FIXED не означает CLOSED, переход lifecycle или приёмку Owner: независимая перепроверка BUG-001 остаётся за Reviewer после всех трёх назначенных исправлений. Push и оркестратор не запускались.
