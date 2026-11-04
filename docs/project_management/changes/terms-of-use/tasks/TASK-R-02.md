---
id: TASK-R-02
change: terms-of-use
role: reviewer
kind: code_review
gate: READY_FOR_TEST
cycle: 1
inputs: [git diff 9bdb3e5648e7e487bee1dcb8d87bb24835073b1d..fd291097825777263e88ca4506b02ef7b586130f, tests/acceptance/, requirements.md, plans/test_plan.md, TASK-R-01, TASK-A-03, TASK-D-05, TASK-T-03, TASK-T-04, BUG-001, BUG-002, BUG-003, DP-R-01]
origin: null
agent: null
model: claude-opus-5-5
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: fd291097825777263e88ca4506b02ef7b586130f
estimate: null
---
## Задание

Повторное ревью исправлений после [TASK-R-01](TASK-R-01.md). Выполнить в отдельной сессии на сторонней модели: проверить независимость по skill Reviewer и записать фактическую модель.

Прочитать весь diff `9bdb3e5648e7e487bee1dcb8d87bb24835073b1d..fd291097825777263e88ca4506b02ef7b586130f`, затронутый код и приёмочные тесты. Проверяемая версия — `fd291097825777263e88ca4506b02ef7b586130f`.

- [BUG-001](../bugs/BUG-001.md): T-29 удерживает первичный current, сохраняет изменённый ввод и имеет позитивный контроль восстановления.
- [BUG-002](../bugs/BUG-002.md): G2 → условия → «Согласен» очищает ошибку и aria-invalid без нового POST.
- [BUG-003](../bugs/BUG-003.md): удалены три лишние проверки; необходимая защита фокуса после submit сохранена.

Самостоятельно перепроверить три бага и чувствительность регрессионных тестов. Успешно проверенные баги перевести в CLOSED, неуспешные — в OPEN. Новые находки в diff оформить по шаблону бага.

Оракулы — [TASK-A-03](TASK-A-03.md). [DP-R-01](../dp/DP-R-01.md) остаётся ON_HOLD; не разрешать отложенный конфликт новым ожиданием теста.

Код, тесты, требования и завершённые задачи не менять. В результате указать проверенный commit, команды, фактические результаты и ограничения; чужие PASS не считать своими, NOT RUN не считать PASS.

Завершить задачу и сделать один коммит своих файлов: `[terms-of-use][TASK-R-02] docs: повторно проверить исправления`. Push и оркестратор не запускать.

Правила: [skill Reviewer](../../../../development_approach/skills/reviewer/SKILL.md), [процесс v3](../../../../development_approach/process/change-process-v3.md), переход 12.

## Результат

**Вердикт.** Все три исправления подтверждены независимо: [BUG-001](../bugs/BUG-001.md), [BUG-002](../bugs/BUG-002.md), [BUG-003](../bugs/BUG-003.md) → CLOSED. В diff исправления новых находок уровня «обязательно» и «желательно» нет. Resolution — `done`. [DP-R-01](../dp/DP-R-01.md) остаётся ON_HOLD: новых ожиданий для нетронутой формы ревью не вводит.

**Независимость.**
- Отдельная сессия без переписки Developer и Tester. Diff, код и тесты прочитаны ревьюером, все проверки запущены им же.
- Модель ревьюера — `claude-opus-5-5` (Anthropic), та же, что в TASK-R-01. Перепроверку своих багов выполняет их автор, как требует процесс.
- В TASK-D-05, TASK-T-03 и TASK-T-04 поле `model` пустое. Признаки среды исполнителей указывают на Codex (OpenAI): «sandbox / вне sandbox» в TASK-D-05, `refs/codex/*` в репозитории, незакоммиченная строка `debug_log.md` «ручной шаг: Codex, модель не зафиксирована». Совпадения с моделью ревьюера не обнаружено, но точная модель исполнителей в задачах не записана.

**Проверенная версия.** Ветка `change/terms-of-use`, HEAD = `fd291097825777263e88ca4506b02ef7b586130f` (TASK-D-05). `origin/change/terms-of-use` = `0d6a8fc…`: три bug_fix-коммита не запушены.

| Коммит диапазона | Что |
| --- | --- |
| `5e90824` | TASK-R-01, баги и DP |
| `1202571`, `0d6a8fc` | маршрут к Analyst, отложенный DP-R-01, назначение bug_fix (оркестратор/Owner) |
| `f7229ef` | TASK-A-03 |
| `b4879ed` | TASK-T-03, fixed_in BUG-001 |
| `833936c` | TASK-T-04, fixed_in BUG-002 |
| `fd29109` | TASK-D-05, fixed_in BUG-003 |

Revision из `fixed_in` разрешены по сообщениям коммитов: `b4879edc011669d8d46072ef4e0871e6a4a1229f`, `833936c437307e9082226cdd257074460cdfab88`, `fd291097825777263e88ca4506b02ef7b586130f`. Литеральные SHA записаны в «Перепроверках» багов.

**Как получена версия.** Терминал на компьютере Owner в этой сессии недоступен: управление компьютером отклонено. Поэтому объекты git (pack и 120 loose-объектов коммитов и изменённых деревьев) скопированы в изолированный контейнер. Diff и деревья считаны там `git 2.43.0`. 33 рабочих файла, на которых выполнялись тесты, совпали с blob'ами дерева `fd29109` после нормализации CRLF: `src/exact_orb/http_api/ui/*` — 14, `tests/ui/**` — 15, `tests/acceptance/*` — 4. Ещё 4 фикстуры вне diff взяты из рабочей копии без сверки хеша: `tests/http_api/golden/{chart_dto,session_view}.json`, `tests/fixtures/places.jsonl`, `terms_draft.md`. В diff они не менялись; хеш утверждённого текста `terms_draft.md` проверяет сам `terms_browser.cjs` (PASS).

**Diff `9bdb3e5..fd29109`**, 18 файлов, +991/−7:
- код: `src/exact_orb/http_api/ui/main.mjs` — три удалённые конъюнкции;
- тесты: `tests/acceptance/terms_acceptance.mjs` (+141), `tests/acceptance/test_terms_ui.py` (+1 сценарий);
- документы: BUG-001…003, DP-R-01, TASK-R-01/A-03/D-05/T-03/T-04, `test_plan.md` (T-29, T-31, прогоны), `change.md`, `events.jsonl`, `debug_log.md`, `review_summary.md`, `risks.md`.

**Прочитанные файлы.**
- Процесс и роль: skill reviewer, `change-process-v3.md` (переходы 11–13, «Задача», «Баги»), `AGENTS.md`.
- Изменение и задачи: TASK-R-01, TASK-D-05, TASK-T-03, TASK-T-04, TASK-A-03 (поля), BUG-001…003, DP-R-01, `change.md`, `events.jsonl`, `debug_log.md`, `review_summary.md`, `risks.md`, diff `test_plan.md`.
- Код: `main.mjs` полностью; места фокуса в `facts.mjs`; `index.html` (страницы и заголовок условий).
- Тесты: diff и helpers `terms_acceptance.mjs`, `test_terms_ui.py`, начало `terms_browser.cjs`.

**Проверки ревьюера.** Изолированная копия: Linux, Node v22.23.4, Python 3.13.18, pytest 9.1.1, Playwright 1.63.0 / Chromium 153.0.8010.12. Production и тесты в репозитории не менялись.

| Команда | Фактический результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs` | 53 pass, 0 fail |
| `node --test tests/ui/*.test.mjs` | 282 pass, 0 fail |
| `node tests/acceptance/terms_acceptance.mjs <s>` × 8 | все exit 0, PASS: roundtrips 41, isolation 8, gates 18, acknowledgement_error 1, payload 8, current 40, recovery 20, issues 24 |
| `python3 -m pytest -q tests/acceptance/test_terms_ui.py -k composition` | 8 passed. Окружение урезано: без conftest/pyproject проекта, маркеры не зарегистрированы |
| `TERMS_BROWSER_CHANNEL=chromium node tests/acceptance/terms_browser.cjs <s>` | presentation 1, keyboard 20, reload 12, builds 20 — PASS. targets — FAIL на `terms-back` (`y=664.328`, 46 промахов), как в TASK-R-01; см. «Риски» |

**Мутации `main.mjs`.** Каждая выполнялась на изолированной копии и откатывалась; SHA-256 файла после серии совпал с исходным.

| Мутация | terms / все UI | Приёмка `terms_acceptance.mjs` | Вывод |
| --- | --- | --- | --- |
| убрать `!draftProtected &&` в hydration (`:134`) | 8 FAIL / 9 FAIL | `current` FAIL: «initial current must preserve D: D1 agree checked=false afterReturn=false»; pytest `[current]` FAIL | BUG-001: приёмка теперь ловит затирание D |
| выключить hydration целиком | 3 FAIL / 52 FAIL | `current` FAIL в позитивном контроле, плюс 6 других сценариев | BUG-001: позитивный контроль работает |
| hydration без `form.setDate` | 6 FAIL / 53 FAIL | `current` и 5 других FAIL | то же |
| снять обе защиты черновика (`:83` и `:220`) | 8 FAIL / 9 FAIL | `current` FAIL | BUG-001 |
| только `openTerms` без `draftProtected = true` (`:83`) | 4 FAIL / 4 FAIL | все PASS | ожидаемо: случай нетронутой формы при чтении отложен в DP-R-01 |
| только `edited()` без `draftProtected = true` (`:220`) | 0 / 1 FAIL | все PASS | вне T-29: условия в примерах всегда открыты до ответа |
| удалить `renderErrors()` в `returnFromTerms` (`:95`) | 0 / 0 FAIL | `acknowledgement_error` FAIL: «agree must hide the existing G2 error»; pytest `[acknowledgement_error]` FAIL | BUG-002 закрыт только приёмкой |
| `if (issueField)` вместо `!termsOpen && issueField` (`:332`) | 2 FAIL / 2 FAIL | все PASS; browser keyboard и builds PASS | BUG-003: сохранённый guard защищён тестами Developer |
| вернуть три удалённые `!termsOpen &&` | 0 / 0 FAIL | все PASS | BUG-003: удалённый код поведения не менял |
| убрать `!birthRestored` в hydration (`:134`) | 0 / 0 FAIL | все PASS | вне diff исправления; см. «Риски» |

**Проверка по багам.**
- BUG-001: причина — тест тратил первичное восстановление в `mount()`. Исправлена в самом приёмочном runner: `mountPendingCurrent` удерживает первый GET, проверяет `phase === 'reading'` и `view === null` до правок. Ответ доставляется и во время чтения, и после каждого возврата. Есть позитивный контроль без правок, по одному примеру на известное и неизвестное время. Production не менялся.
- BUG-002: сценарий T-31 проверяет G2 → «Согласен»: ошибку, `aria-invalid` и отсутствие POST. Позитивный контроль G4 — один POST. Без `renderErrors()` сценарий падает.
- BUG-003: удалены ровно три конъюнкции. Фокус при открытых условиях находится на видимой странице (`openTerms` → `#terms-page-heading`, `tabindex=-1`). Необходимый guard `:332` сохранён и защищён двумя тестами.

## Findings

**Обязательно** — нет.

**Желательно** — нет.

**Мелочи** (без багов):
- В TASK-T-03 `commit: 0d6a8fc…` — production-база, а не коммит задачи `b4879ed`. Поле `commit` других задач указывает собственную поставку.
- `fixed_in` и `commit` задач заданы плавающими revision `:/<regex>`: git берёт самый молодой подходящий коммит. Любой будущий коммит с совпадающей строкой сообщения, например «…TASK-T-04…test», тихо переназначит ссылку. Литеральные SHA зафиксированы в «Перепроверках» и выше.
- В `mountPendingCurrent` (`terms_acceptance.mjs:23-24`) тест подменяет `document.createElement` и добавляет пустой `scrollIntoView`. Это локальная адаптация листового DOM-порта, production она не трогает. В браузерных сценариях прокрутку проверяет настоящий Chromium.

**Без замечаний:** diff `main.mjs`; новая дельта `terms_acceptance.mjs` и регистрация сценария в `test_terms_ui.py`; записи T-29/T-31 и таблица прогонов в `test_plan.md` совпадают с фактическим числом примеров (40 и 1).

## Риски

- **Полный pytest и Python-тесты проекта — NOT RUN** (`tests/acceptance/test_terms_contract.py`, `tests/http_api`, `tests/test_module_boundaries.py`, полный набор). В контейнере нет окружения проекта, а терминал Owner в этой сессии недоступен. Результаты 347 PASS и 2978 PASS / 1 SKIPPED из TASK-D-05/T-04 приняты как заявленные, не как проверенные. `test_terms_composition` запущен в урезанном окружении без conftest проекта.
- **Браузер:** Chrome 155 на Windows, масштаб и экранный диктор не проверялись. `targets` в Chromium 153 на Linux падает на `#terms-back`: та же дробная позиция `y=664.328`, что в TASK-R-01. `styles.css` в diff не менялся, пользовательской поломки нет.
- **DP-R-01 ON_HOLD.** Защиту нетронутой формы, открытой для чтения условий (`main.mjs:83`), проверяют только тесты Developer: 4 FAIL при мутации, приёмка — PASS. До решения DP это сознательный пробел приёмки. Переход 13 надо сверить с этим риском в `risks.md`.
- **`!birthRestored` (`main.mjs:134`) не защищён ни одним тестом.** Без него повторный current переписал бы нетронутую восстановленную форму новым birth. Нормативного ожидания для этого нет, ветка вне diff исправления, поэтому это не баг. При следующем изменении hydration нужен DP или тест.
- **Рабочее дерево не чистое.** Незакоммиченные правки оркестратора — переход 12: `change.md` (`READY_FOR_TEST`), `events.jsonl`, `debug_log.md`. Они не тронуты и в коммит ревью не входят.
- Push не выполнялся: локальная ветка опережает `origin` на три bug_fix-коммита и этот коммит.

Следующий шаг: переход 13 READY_FOR_TEST → DONE. Его выполняет оркестратор или Owner после проверки условия «нет багов в OPEN и FIXED» с учётом DP-R-01 ON_HOLD в `risks.md`. Затем TASK-M «Сводка поставки».
