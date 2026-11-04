---
id: TASK-R-01
change: terms-of-use
role: reviewer
kind: code_review
gate: READY_FOR_TEST
cycle: 1
inputs: [git diff terms-of-use-approved-1..:/terms-of-use.*TASK-D-04.*test, tests/acceptance/, TASK-T-02]
origin: null
agent: null
model: claude-opus-5-5
status: DONE
resolution: needs_decision
raised_dp: [DP-R-01]
raised_bugs: [BUG-001, BUG-002, BUG-003]
changed_reqs: []
reviewed_reqs: []
commit: 9bdb3e5648e7e487bee1dcb8d87bb24835073b1d
estimate: null
---
## Задание
Ревью diff и приёмочных тестов; находки с четырьмя частями; «обязательно» и «желательно» — в bugs/; перепроверить свои исправленные баги.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

**Вердикт.** Production-изменение M1-9 в проверенных сценариях соответствует REQ-UI-03 и REQ-TERMS-01…08. Нарушений требований, ошибок обработки отказов и потери ввода при поздних ответах не найдено. Найдены:
- 1 находка «обязательно» о достоверности приёмочного теста: [BUG-001](../bugs/BUG-001.md), major;
- 2 находки «желательно»: [BUG-002](../bugs/BUG-002.md) и [BUG-003](../bugs/BUG-003.md), minor;
- 1 неясность требования: [DP-R-01](../dp/DP-R-01.md) для Analyst.

Resolution `needs_decision`: от решения DP-R-01 зависит ожидаемый результат в исправлении BUG-001. Баги уже заведены в OPEN. После решения DP ревью доделывается в apply_decisions с итогом has_bugs.

**Независимость.**
- Отдельная сессия без переписки Developer; diff, код и баги прочитаны и заведены ревьюером.
- Модель ревьюера — `claude-opus-5-5` (Anthropic).
- В TASK-D-02/03/04 поле model пустое. Следы среды Developer — «ChatGPT in-app browser» в TASK-D-02/04 и рабочие деревья Codex в `.git/worktrees`. Это указывает на модель другого поставщика. Совпадение моделей не обнаружено, но точная модель Developer в задачах не записана.

**Проверенные SHA** (ветка `change/terms-of-use`, HEAD = `origin/change/terms-of-use`):

| Роль | SHA |
| --- | --- |
| Начало diff | `fb1216591b0fd98589084155177f1bd4e41d159d` — TASK-O-02, переход 6 |
| D-02 | `d8cef05f58e39a3d9db06276448cefeeae39d564` |
| D-03 | `58aa6b956ccbb9bec9948340e955dc4ba133ce25` |
| D-04, конец diff из inputs | `6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5` |
| T-02, последний проверенный commit | `9bdb3e5648e7e487bee1dcb8d87bb24835073b1d` |

Тега `terms-of-use-approved-1` в локальном репозитории нет: нет ни `refs/tags`, ни записи в `packed-refs`. Начало diff определено по TASK-D-02 («Исходная ветка change/terms-of-use, HEAD fb12165…») и reflog: следующий commit после перехода 6 — TASK-D-02.

**Diff** `fb12165..6db88e0`, код и тесты:
- `src/exact_orb/http_api/ui/index.html`, `main.mjs`, `styles.css`;
- `tests/ui/terms.test.mjs`, `tests/ui/fixtures/dom.mjs`, `tests/http_api/test_ui_delivery.py`.

Плюс документы задач и evidence D-02/03/04. В `6db88e0..9bdb3e5` добавлены `tests/acceptance/*`, TASK-T-02, test_plan и `plans/tester_evidence/*`.

**Прочитанные файлы.**
- Процесс и роль: skill reviewer, AGENTS.md, `change-process-v3.md` (переходы, «Задача», DP, баги), шаблоны `bug.md`, `dp.md`.
- Изменение: `change.md`, `requirements.md` полностью, `terms_draft.md`, DP-A-01, `implementation_plan.md`, промты 01/02/03, `test_plan.md` (T-29/T-30, прогоны, результат), `sequences/002`, задачи D-01…D-04, T-01, T-02, O-02, A-02, `events.jsonl`, `roadmap.md`.
- Evidence: `tester_evidence/README.md`, `req-matrix.md`, `acceptance.log`, `supplemental.mjs`, `public-source.json`, `evidence/README.md`.
- Действующие требования: `docs/requirements/current/ui/birth-form-and-facts.md`, REQ-UI-03/09/11.
- Код: `main.mjs` полностью; `form.mjs`; места фокуса и resize в `facts.mjs`; `session.mjs`, `places.mjs`, `result_controller.mjs` — вызываемые части.
- Тесты: `tests/ui/terms.test.mjs`, `fixtures/dom.mjs`, `fixtures/session.mjs`, `tests/http_api/test_ui_delivery.py` (diff), все четыре файла `tests/acceptance/`.

Совпадение рабочих файлов `src/exact_orb/http_api/ui/*` и `tests/{ui,acceptance,http_api/test_ui_delivery.py}` с blob'ами HEAD `9bdb3e5` проверено `git hash-object` после нормализации CRLF.

**Проверки ревьюера.** Изолированная копия, Node v22.23.4, Linux; production не менялся.

| Команда | Результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs` | 53 pass, 0 fail |
| `node --test tests/ui/*.test.mjs` | 282 pass, 0 fail |
| `node tests/acceptance/terms_acceptance.mjs <scenario>` × 7 | PASS: roundtrips 41, isolation 8, gates 18, payload 8, current 14, recovery 20, issues 24 |
| `TERMS_BROWSER_CHANNEL=chromium node tests/acceptance/terms_browser.cjs <scenario>`, Playwright Chromium 153.0.8010.12 | presentation 1, keyboard 20, reload 12, builds 20 — PASS. targets — FAIL на `terms-back`: см. «Риски» |
| Мутации `main.mjs`, 12 вариантов, каждый с восстановлением | Выявили BUG-001/002/003. Удаление `acknowledged.checked = …`, смена `back` на снятие, отказ раскрыть редактор при возврате, удаление защиты фокуса submit (`:332`) и проверки закрытой страницы ловятся тестами |
| Probe: поздний первичный current с чтением условий и без | Основание DP-R-01 |

Python-тесты (`tests/acceptance/test_terms_contract.py`, `test_terms_ui.py`, `tests/http_api/test_ui_delivery.py`, полный pytest) не запускались: в среде ревью нет окружения проекта. Они прочитаны, их результаты взяты из TASK-T-02 и D-04 без перепроверки.

## Findings

**Обязательно**
- [BUG-001](../bugs/BUG-001.md), major. Сценарий `current` в `tests/acceptance/terms_acceptance.mjs:140-154` (T-29) не может упасть на затирании черновика поздним current: первичное заполнение уже потрачено в `mount()`, а правки сами защищают черновик. Мутации `main.mjs:83` и `:134` проходят все 7 приёмочных сценариев. Позитивного контроля восстановления нет.

**Желательно**
- [BUG-002](../bugs/BUG-002.md), minor. Ни один тест не проверяет снятие ошибки отметки после «Согласен», следующего за G2: `main.mjs:95`. Без этой строки ошибка остаётся при выбранном checkbox, а все наборы проходят.
- [BUG-003](../bugs/BUG-003.md), minor. Три недостижимые защиты `!termsOpen &&` в `main.mjs:78`, `:196`, `:197` не меняют поведения и не проверяются ни одним тестом.

**DP для Analyst**
- [DP-R-01](../dp/DP-R-01.md). REQ-UI-11 и REQ-TERMS-04/D3 расходятся для нетронутой, в том числе пустой, формы, если первичный current пришёл во время чтения условий: восстановить и свернуть форму или сохранить пустой черновик. Реализация выбрала второе по плану.

**Мелочи** (без багов)
- `index.html:15-59`: содержимое новой `<section id="birth-page">` не переиндентировано.
- `tests/http_api/test_ui_delivery.py`, `TermsContent`: сравнивается только текст `h1/h2/p/th/td`. Текст в других тегах внутри `#terms-content` хеш-проверка пропустит; полное `innerText` сравнивает браузерный `presentation`.
- `tests/ui/terms.test.mjs:235`: сообщение «accepted-once collapse stays consumed after return». Возврат раскрывает редактор независимо от collapse; фактически утверждение проверяет, что `clearFieldError` не сворачивает его повторно.

**Без замечаний**
- T1…T4: таблица `TERMS_RETURN_ACTIONS` и синхронизация DOM-checkbox.
- D1…D3: живые DOM и form, без сериализации.
- G1…G4, R1…R3: прежний coordinator; POST содержит ровно три поля.
- L1…L3: инициализация `acknowledged.checked = false`.
- Отказы build и render failure во время чтения: страница и фокус остаются, recovery доступна после возврата.
- Снятие обработчиков в `dispose`.
- Перерисовка колеса после скрытия: ResizeObserver, `|| 328`.
- Утверждённый текст: hash-тест.
- Новых зависимостей, сетевых вызовов, логов и persistence нет.

## Риски

- **Тег `terms-of-use-approved-1` отсутствует локально.** Diff посчитан от `fb12165` по записи TASK-D-02 и reflog. Оркестратору стоит создать или получить тег, чтобы следующий diff считался от него.
- **Браузерная проверка `targets` чувствительна к среде.** В Chromium 153 на Linux `#terms-back` имеет высоту ровно 44 px при дробной позиции `y = 664.328`. Проба на `+43.99 px` попадает в `.terms-actions` (46 промахов в одной строке), и сценарий падает. В Chrome 155 на Windows у Tester — PASS. Пользовательской поломки нет, поэтому это не баг; при переносе прогона на другую ОС или шрифты возможен ложный FAIL. Источник: `tests/acceptance/terms_browser.cjs:116-128`, `styles.css .terms-actions`.
- **C7, опубликованный код точной версии**, не перепроверялся: в среде ревью нет сети. Опора на `tester_evidence/public-source.json`, tree `c22ac71…` = HEAD `6db88e0`.
- **Не запускались** Python-тесты, Chrome 155 и масштаб браузера. Отчёты D-04/T-02 о них приняты как заявленные, не как проверенные ревьюером.
- **Рабочее дерево не чистое.** До ревью в нём уже были изменения оркестратора: `change.md`, `events.jsonl` и этот файл задачи в исходной редакции. `change.md` и `events.jsonl` не тронуты и в коммит ревью не входят.
