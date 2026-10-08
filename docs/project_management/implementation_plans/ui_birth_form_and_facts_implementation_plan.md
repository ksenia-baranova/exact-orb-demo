# Implementation Plan: ui-birth-form-and-facts

**Owner:** Developer. **Дата актуализации:** 2026-10-08. **Ветка:** `dev/ui-birth-form-and-facts-review`.
**Status:** **READY_FOR_TEST** — по прямому поручению владельца 2026-10-08. Реализация DEV-UI-01…08 передаётся Tester на implementation commit `f7fb34bce8de23d8c08a7491c5698a7b5ab9e4ab` с одним согласованным skip в коммите передачи, содержащем эту редакцию документов. Актуальный [Developer Handoff — раздел 25](#developer-ready-for-test) содержит версии, команды, evidence, порядок запуска и оставшиеся проверки. Последний полный pytest: **2959 passed / 1 skipped**, exit 0; DEBT-CALC-001 OPEN. Исторические результаты и PARTIAL/BLOCKED в журналах сохранены; ручные browser criteria и независимая приёмка ожидаются. Статус change/G4/G5 ведёт [Manager](../change_plans/ui-birth-form-and-facts/artifacts.md#change-brief).
**Technical assessment:** FEASIBLE; закрытые продуктовые решения повторно сверены, blocking semantic gaps Developer не обнаружены.
**Дополнение по внешнему ревью (2026-10-07):** зарегистрированы восемь bugs TEST-FIND-UI-005…012 — **найдено другой моделью**. DEV-UI-07/08 IMPLEMENTED / BROWSER RETEST PENDING, все восемь findings FIXED PENDING RETEST; исправления опубликованы в Developer-ветке @ `25e3e0f` / `f7fb34b`. Проверки 07 — [раздел 22](#dev-ui-07-execution), 08 — [раздел 23](#dev-ui-08-execution). Scope и отдельная оценка — [раздел 21](#external-model-bugs); последующий прогон с согласованным исключением — [раздел 24](#debt-calc-001-test-skip).
**Последняя ручная проверка локального стенда (2026-10-07):** отдельным исправлением прокси снят forwarding blocker штатного браузера; natal build/details/reload проверены до DEV-UI-07/08. Исходный статус BLOCKED в журнале DEV-UI-06 описывает проверку до исправления. Ручной retest исправлений 07/08 NOT RUN, стенд для них не перезапускался; см. [раздел 20](#local-proxy-fix) и актуальный handoff.
**Исключение теста (2026-10-07):** по новому поручению владельца «Поставь метку игнор падающего теста» только property-тест монотонности отмечен `pytest.mark.skip` с причиной DEBT-CALC-001. Долг OPEN, остальные тесты выполняются; фактические результаты и порядок снятия отметки — [раздел 24](#debt-calc-001-test-skip).
**Estimate Developer:** **5–8 рабочих дней / 40–64 человеко-часа**, один рабочий день = 8 часов. Уверенность средняя.
**Бюджет владельца:** DP-UI-07 текущей Manager-редакции — Analysis 4 / Development 5 / Testing 5 дней. Estimate Developer 5–8 сохраняется; относительно budget Development 5 риск составляет до +3 дней. Это не обещание выполнить верхнюю границу за 5 дней.

## 1. Baselines и разрешённый контракт

| Источник | Версия и предел |
|---|---|
| Общий `change/ui-birth-form-and-facts` | `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`, получен из `ksenia-baranova/exact-orb-demo` 2026-10-06; Developer-ветка обновлена `git merge --ff-only FETCH_HEAD`. |
| Baseline исполнения DEV-UI-01 | `082c6b9ac5c8b054c38de5f17bc673956ec058d8`, проверен новым fetch из `ksenia-baranova/exact-orb-demo`: `HEAD` = `FETCH_HEAD`, расхождение `0 0`. Нормативный контракт и версии REQ/AS/DP выше сохранились. Результат сохранён при обновлении ветки и входит в общий пакет DEV-UI-01/02. |
| Baseline исполнения DEV-UI-02 | `6fc62b9c8813b5aadfd5150ca39033664f18b777`, PR #49/50 интегрируют Tester `0f6aa82` и утверждение Manager `e4f60fb`. Получен fetch и `git merge --ff-only FETCH_HEAD` 2026-10-07. Семантика REQ/AS @ `ce25dd0` и HTTP baseline сохранены; допуск G3 подтверждён Manager. Общий пакет DEV-UI-01/02 подготовлен поверх этого HEAD; сведения о подготовке коммита — в разделе 11. |
| Baseline исполнения DEV-UI-03 | `ef75d77232e1f629540827bfd90e93c1c16977ea`: реализация DEV-UI-01/02 опубликована в `dev/ui-birth-form-and-facts-review` по отдельному поручению. `git ls-remote` 2026-10-07 подтвердил общий `change/*` @ `6fc62b9`, уже включённый в Developer HEAD. Семантика требований и G3 сохранились; браузерный критерий DEV-UI-02 остаётся pending, доступные form/transport позволяют порученную интеграцию. |
| Baseline исполнения DEV-UI-04 | `564186d1e40ee8560b6df402c51ae2ee401c38e6`: локальный коммит DEV-UI-03 и TEST-FIND-UI-004. Входное дерево/index чистые. `git ls-remote` 2026-10-07 подтвердил общий `change/*` @ `6fc62b9`, уже в истории Developer HEAD; обновление не потребовалось. G3 и смысл approved REQ/AS/DP сохранены. |
| Baseline исполнения DEV-UI-05 | `6d970f605188ad1419cbae791e8e2f83d63d67c9`: реализация DEV-UI-04 опубликована в Developer-ветке по отдельному поручению. Входное дерево/index чистые. `git ls-remote` правильного репозитория `ksenia-baranova/exact-orb-demo` 2026-10-07 подтвердил Developer HEAD и общий `change/*` @ `6fc62b9`, уже включённый в историю. G3 и approved REQ/AS/DP сохранены; браузерный gate предыдущих шагов остаётся pending. |
| Baseline исполнения DEV-UI-06 | `6d970f605188ad1419cbae791e8e2f83d63d67c9` плюс сохранённый незакоммиченный diff DEV-UI-05 (9 файлов). Входной index пуст; свои изменения предыдущего шага не откатывались и не смешивались с новым коммитом. `git ls-remote` правильного репозитория 2026-10-07 подтвердил общий `change/*` @ `6fc62b9` и remote dev @ `6d970f6`. Семантика REQ/AS/DP и G3 сохранены. Точный fingerprint поставляемых файлов — `logs/ui-dev-06/https-evidence.json` (9 SHA-256, bytes verified через HTTPS). |
| Нормативный baseline | [HTTP API](../../requirements/http_api.md) §§4–9, 11, 13; [каталог](../../requirements/component_responsibilities/exact-orb_place_catalog.md); [Build Natal](../../requirements/component_responsibilities/exact-orb_build_natal_components.md); [сессия](../../requirements/component_responsibilities/exact-orb_session_requirements.md); [stored chart](../../requirements/session/stored-chart-session-behavior.md); ADR-0008, 0029–0034, 0039–0041 @ `652bd73405db0a0611e98e81af6f3f668dd429f6`. Эти пути ещё не перенесены в `current/`. |
| Требования и сценарии change | [requirements.md](../../requirements/changes/ui-birth-form-and-facts/requirements.md), [scenarios.md](../../requirements/changes/ui-birth-form-and-facts/scenarios.md), [analysis.md](../../requirements/changes/ui-birth-form-and-facts/analysis.md) — семантика `ce25dd0`, 10 REQ / 23 AS; APPROVED FOR DEVELOPMENT этой Manager-редакцией после повторной сверки обеих ролей. |
| Единый реестр | [artifacts.md](../change_plans/ui-birth-form-and-facts/artifacts.md#decision-register), рабочая административная редакция поверх `2972e42`. DP-UI-01…09 ACCEPTED; опубликованный семантический выбор @ `64934fc`, Developer вклад `082c6b9`, Tester `0f6aa82`. Budget 4/5/5 и G3 утверждены Manager; точный commit статусов передаётся после сохранения/интеграции. |
| Tester consultation | [tester.md](../../testing/ui-birth-form-and-facts/tester.md) @ `0f6aa8256eb154ddd4871fbb734e6663a2873828`, PR #49 / `2972e42`: TESTABLE на baseline `082c6b9`, 23 AS/stack; estimate 3–5 повторно подтверждён, три findings resolved in contract. |
| Developer повторная валидация | [review](ui_birth_form_and_facts_developer_review.md#повторная-валидация-2026-10-06) опубликован @ `082c6b9`, исходный review baseline `033217d`; старый `b36b63d` — история. |

Между `652bd734` и `033217d` нет изменений `src/`, `tests/`, `pyproject.toml`. Ни merge ролевых документов, ни результаты backend tests не подтверждают готовность браузерного UI. Решения и accepted risks хранятся в реестре; таблицы ниже фиксируют их перенос/проверку и не создают второго источника выбора.

## 2. Manager summary и G3

**Текущая диспозиция Manager — 2026-10-07:** G2/alignment завершены после TESTABLE Tester `0f6aa82`; требования/scenarios и этот план утверждены, G3 подтверждён в [Change Plan](../change_plans/ui-birth-form-and-facts/artifacts.md#roadmap). Матрица ниже сохраняет историческую оценку Developer на момент подготовки `082c6b9`; её NOT MET не является текущим delivery status.

Прежние FIND-DEV-UI-001…003 закрываются **на уровне контракта и baseline**: DP-UI-05 перенесён в REQ-UI-03/10 и AS-UI-22; recovery выбран в DP-UI-09 и описан в REQ-UI-09 / AS-UI-23; для consultation зафиксирован единый вход `033217d`. Правило орбиса из TEST-FIND-UI-003 также определено в REQ-UI-04 / AS-UI-07. Browser evidence появится после реализации; Developer не меняет статусы Tester findings.

**Рекомендация Developer:** технически можно готовить переход к READY_FOR_DEVELOPMENT на этом scope. **На момент подготовки Developer-пакета G3 не был пройден**. Manager владеет change status; этот план не переводит change в новый статус и не разрешает исполнение промтов.

| Условие G3 по process.md | Оценка на `033217d` + этот Developer diff | Владелец следующего действия |
|---|---|---|
| Change Plan со статусом READY_FOR_DEVELOPMENT | NOT MET: Manager artifacts ещё ANALYSIS; согласованный Change Plan/Gantt отсутствует. | Manager |
| Утверждённые REQ/AS и точные baselines обеих частей контракта | Точные версии перечислены выше, перенос DP соответствует контракту; требуется подтвердить именно этот пакет для исполнения. Исторические «ожидает записи» в Analyst @ `ce25dd0` читаются вместе с более новым реестром @ `64934fc`. | Analyst/Manager |
| Оценки Developer и Tester зафиксированы | Developer 5–8 дней подготовлено в рабочем diff; Tester 3–5 дней уже записано, повторное заключение на 23 AS ещё не получено. | Developer — handoff плана; Tester — повторная сверка и подтверждение своего estimate |
| Blocking DP ACCEPTED с owner evidence | MET для DP-UI-01…09; повторное решение по чат-кнопке, сводке или lost-response не требуется. | Manager фиксирует baseline реестра с ролевым вкладом |
| Open non-blocking items имеют owner и условие возврата | DEBT-UI-001 имеет роли и триггер до передачи ссылки/публичного доступа; DP-UI-03 и принятые ограничения M1-6 сохраняются. Это не новая продуктовая развилка. | Manager контролирует долг и прежние ограничения |
| Gantt соответствует оценкам/зависимостям | NOT MET: target 4/2 дня не покрывает estimates 5–8/3–5. Нужны alignment бюджета, зависимости и контрольные результаты, без механического пересчёта старого roadmap. | Manager + владелец target |
| Developer знает разрешённый scope | MET технически: форма, три группы, восстановление/ошибки, закрытый gate, доступность. План и промты явно исключают смежный scope. | Developer |

**Условие начала:** административный G3 подтверждён этой Manager-редакцией. До исполнения work items получить общий HEAD `change/*`, включающий её commit, и выдать его Developer-ветке с approved scope/plan. Статус IN_DEVELOPMENT фиксируется при фактическом старте. Чистовая редакция/карта переноса Analyst и независимая browser acceptance остаются обязательными до G5.

## 3. Стоимость, уверенность и допущения

| Work item | Собственная работа Developer, дни | Часы |
|---|---:|---:|
| DEV-UI-01. Доставка страницы и HTTP client | 0,5–0,75 | 4–6 |
| DEV-UI-02. Форма и autocomplete | 1–1,5 | 8–12 |
| DEV-UI-03. Сессия, build и типизированные ошибки | 0,75–1,25 | 6–10 |
| DEV-UI-04. Reader, форматирование и действия результата | 0,75–1,25 | 6–10 |
| DEV-UI-05. Recovery и две вкладки | 1–1,5 | 8–12 |
| DEV-UI-06. Адаптивность, интеграционные проверки и handoff | 0,5–1,25 | 4–10 |
| **Базовая сумма** | **4,5–7,5** | **36–60** |
| Резерв одного небольшого цикла исправлений/сверки | 0,5 | 4 |
| **Оценка с резервом** | **5–8** | **40–64** |

В каждом work item уже учтены его Developer tests и локальная проверка. DEV-UI-06 содержит интеграционную/визуальную сверку, один финальный регрессионный прогон, синхронизацию технических документов и handoff; эти часы не прибавляются повторно. Резерв не покрывает изменение scope, новые зависимости или длительное восстановление инфраструктуры.

**Основание:** backend/DTO уже готовы, но production frontend, UI test harness и assets packaging отсутствуют. Основная стоимость — state transitions, управляемые late response/commit cases, keyboard/mobile и реальный HTTPS browser путь, а не расширение вычислительного ядра. На момент оценки target 4 дня был ниже нижней границы. Новый budget владельца 5 дней соответствует нижней границе estimate; диапазон 5–8 и риск +3 сохраняются.

**Допущения:** один Developer, 8 продуктивных часов в дне; scope трёх групп без wheel/chat/DTO delta; Node и Python доступны; существующий HTTPS стенд доступен для интеграции; один небольшой retest учтён. Ожидание решений и чужих PR отдельно. Tester/Analyst work не включены в Developer estimate.

**Отдельные роли:** Tester оценил свою работу в **3–5 дней / 24–40 часов** со средней-низкой уверенностью и подтвердил эту оценку после выбора UI stack и повторной сверки @ `0f6aa82`. Сумма записанных Developer + Tester трудозатрат — **8–13 человеко-дней / 64–104 часа**, без оставшейся работы Analyst/Manager и календарного ожидания. Историческая оценка Analyst 1,5–2,5 дня не считается автоматически новым остатком.

**Денежный расчёт:** ставка не задана. Стоимость Developer = `40…64 × ставка Developer за час`; Developer + Tester = `40…64 × ставка Developer + 24…40 × ставка Tester`. При одной ставке `R` — `64R…104R`. Валюта, ставка, налоги, стоимость LLM/API и внешней инфраструктуры не выдумываются. План не добавляет вызовов LLM; стоимость работы агента этим estimate не измерена.

**Главная неопределённость:** доставка/packaging первого UI и browser recovery на штатном HTTPS пути с известным FIND-TEST-HTTP-001. При невозможности воспроизводимой HTTPS проверки вернуть ограничение Manager/Tester; не включать попутное исправление M1-6. При требовании нового browser automation framework или изменения дизайна пересчитать estimate до расширения scope.

## 4. Технический способ поставки

Решение Developer внутри approved scope: **HTML/CSS и native ES modules**, размещённые в `src/exact_orb/http_api/ui/`; одна страница `GET /` и узкий prefix `/ui/` для assets через уже доступный Starlette/FastAPI. Существующие business routers, health ACL, OpenAPI DTO и cookie flow сохраняются; UI routes не становятся новой business API операцией. Asset delivery подключается без общего catch-all, чтобы не подменять текущие 404/405.

`pyproject.toml` получает только package-data для UI assets. Нужны отдельные проверки assets в checkout и установленном пакете: наличие файлов в исходниках не доказывает их доставку с wheel. SPA framework, npm manifest, bundler, новый сервис, сеть между внутренними компонентами и дополнительные dependencies не нужны.

Планируемые реальные модули создаются по мере своего work item, без future stubs:

- `main.mjs` — сборка страницы, DOM events/render; серверные/пользовательские строки выводятся как текст.
- `transport.mjs` — существующие fetch операции same-origin с cookie и no-store; возвращает различимые HTTP outcome / отсутствие ответа, сохраняет request ID и Retry-After для диагностики.
- `form.mjs`, `places.mjs` — минутный ввод, выбранный ID, управляемый debounce и generation запроса.
- `facts.mjs` — reader публичного DTO и pure formatting; `Math.round(orb * 60)` для неотрицательного orb, затем деление целых минут. Изменения type/category/чисел API нет.
- `session.mjs`, `recovery.mjs` — координация сессии, snapshot отправленного intent, текущей карты и черновика; устаревший read/search response не подменяет более новое состояние.

`fetch`, monotonic timer и view/DOM — листовые швы для управляемых тестов. Тесты собирают настоящие модули coordinator/transport/form/reader, заменяют сеть/таймер, а не предмет проверки. Нет общего mutable результата между экземплярами вкладок. Ограничение повторного click принадлежит локальному client intent, серверные permit/CAS/lifecycle не изменяются.

Автоматические проверки pure state/formatting выполняются через доступный **Node v24.19.0 / `node --test`**, без npm-зависимостей. Python HTTP integration и boundary tests переиспользуются. Реальный DOM, keyboard, cookie и mobile подтверждаются браузером по HTTPS; Node state tests не называются browser acceptance. Если Tester выберет отдельное browser tooling, это его обоснованный выбор с пересмотром связанных допущений, а не скрытая установка dependency.

## 5. Work items и подход

DEV-UI-01 выполнен; код и автоматические проверки DEV-UI-02–05 готовы. DEV-UI-06 выполнен частично: после исправления прокси проверен штатный browser build/details/reload, оставшиеся browser criteria и независимая приёмка Tester pending. Полный pytest при DEV-UI-03 обнаружил контрпример существующего теста конфигураций; повторные прогоны подтверждают DEBT-CALC-001, общий regression gate не объявлен PASS. Факты исполнения и границы evidence записаны в журналах Developer, актуальная проверка стенда — в разделе 20. Карточки утверждены Manager 2026-10-07; историческое DRAFT/NOT EXECUTED в промтах не переписывается. В тестовых docstrings/comments сохраняются REQ/AS IDs и ссылки на Analyst baseline; при финализации ссылки сверяются с картой переноса Analyst.

<a id="dev-ui-01"></a>
### DEV-UI-01. Страница доставляется тем же приложением

- **Статус исполнения:** COMPLETE; доставка страницы, транспорт, installed-wheel delivery, целевые/связанные/полные проверки и HTTPS smoke выполнены. См. [журнал](#9-журнал-исполнения-dev-ui-01). Это завершение work item, приёмка полного UI ещё впереди.
- **REQ/AS:** REQ-UI-01, 10; AS-UI-01, 19. **DP:** 01/02. **Dependency:** G3 и проверенный Python/Node runtime.
- **Файлы:** `src/exact_orb/http_api/app.py`, новые `ui/index.html`, `ui/styles.css`, `ui/main.mjs`, `ui/transport.mjs`; package-data в `pyproject.toml`; новый `tests/http_api/test_ui_delivery.py`, `tests/ui/transport.test.mjs`.
- **Результат:** HTML/assets доступны в том же origin, fetch client различает status/code и network failure; существующие business routes/health/error mapping не меняются.
- **Подход:** реализация → тесты. Простая транспортная сборка поверх существующей FastAPI composition; отдельный RED не снижает риск. Новые asset delivery/packaging проверки обязательны до завершения.
- **Покрытие:** `test_integration.py::test_openapi_exact_public_shapes_and_response_variants`, routing/health проверки `test_lifecycle.py`; отсутствуют UI routes и installed assets checks.
- **Наблюдаемость:** новые бизнес-события не вводятся; request IDs серверных операций сохраняются в диагностике fetch client.
- **Промт:** [01-page-and-transport](../../../prompts/2026-10-06/ui-birth-form-and-facts/01-page-and-transport.md).
- **Completion:** рабочая доставка из package resources, asset/transport tests и related HTTP tests прошли, public DTO/health/routes сохранились.

<a id="dev-ui-02"></a>
### DEV-UI-02. Пользователь вводит данные и подтверждает место

- **Статус исполнения:** IMPLEMENTED / BROWSER CHECK PENDING по поручению пользователя 2026-10-07. Node, HTTP, installed-wheel и полный pytest прошли; логика клавиатуры/выбора проверена на настоящем controller. Инструмент браузера отклонил локальный URL, поэтому реальный DOM/mouse/keyboard критерий не объявлен PASS. См. [журнал](#10-журнал-исполнения-dev-ui-02).
- **REQ/AS:** REQ-UI-02, 03, 10; AS-UI-02, 04–06, 18, 20. **DP:** 03/04/06/08. **Dependency:** DEV-UI-01.
- **Файлы:** новые `ui/form.mjs`, `ui/places.mjs`; `index.html`, `main.mjs`, `styles.css`; новые `tests/ui/form.test.mjs`, `tests/ui/places.test.mjs`.
- **Результат:** дата → место → время, обязательный ID, явная неизвестность времени, local validation и manual gate; autocomplete от трёх символов, mouse/keyboard, late responses и сброс ID.
- **Подход:** тесты → реализация для input/state/races. Таймер injected, ответы доставляются контролируемо; import/setup failure не считается behavioral RED.
- **Покрытие:** серверный prefix/normalization уже проверен `tests/test_place_search_contracts.py`, `tests/http_api/test_place_dto.py`. Новый риск — client generation/selection и keyboard; нужны самостоятельные UI checks, без копии backend normalization.
- **Наблюдаемость:** поиск сохраняет server request ID; отсутствие запроса до порога подтверждается transport spy рядом с успешным запросом/выбором.
- **Промт:** [02-form-and-places](../../../prompts/2026-10-06/ui-birth-form-and-facts/02-form-and-places.md).
- **Completion:** 2→3→4→2/очистка/late response, 00:00/12:00/23:59/null/24:00, валидный ID и gate прошли; UI selection доступен с клавиатуры.

<a id="dev-ui-03"></a>
### DEV-UI-03. Вход, явный build и ошибки

- **Статус исполнения:** IMPLEMENTED / FULL REGRESSION FAILED по поручению пользователя 2026-10-07. Client state, wiring через листовой DOM-порт, целевые/связанные HTTP проверки, installed-wheel и реальный HTTPS bootstrap/build/current прошли. Полный pytest: 2959 passed / 1 failed; контрпример воспроизведён на неизменённых baseline файлах конфигураций. Браузерная проверка и независимая Tester acceptance не заявлены. См. [журнал](#12-журнал-исполнения-dev-ui-03).
- **REQ/AS:** REQ-UI-01, 03, 08, 09; AS-UI-01, 03–06, 10–13, 15, 17, 20/21. **DP:** 02/04/08. **Dependency:** DEV-UI-01/02.
- **Файлы:** новый `ui/session.mjs`; `transport.mjs`, `main.mjs`; новый `tests/ui/session.test.mjs`; адресное дополнение HTTP integration только при действительно новом шве.
- **Результат:** bootstrap → current; screen state из ответа; build с snapshot трёх полей, запрет второго click; field issues и общий fallback; cookie/query/expected version не конструируются клиентом.
- **Подход:** тесты → реализация для state transitions и negative control; существующее серверное покрытие запускается, не дублируется.
- **Покрытие:** `test_session.py::test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation`, `test_current_projects_stale_unavailable_or_empty_without_mutation`; request-boundary и admission suites. Нет браузерной координации/field mapping.
- **Наблюдаемость:** HTTP 001/003/004 и реальные `http_message` пары ContextService/admission/Orchestrator/session_view по request/run ID; trace есть только после разрешённого POST.
- **Промт:** [03-session-and-build](../../../prompts/2026-10-06/ui-birth-form-and-facts/03-session-and-build.md).
- **Completion:** empty/ready/stale/unavailable, один explicit POST, same-origin cookie, сохранение draft и IssueDTO checks прошли. Code-specific unknown recovery завершается DEV-UI-05.

<a id="dev-ui-04"></a>
### DEV-UI-04. Читаемые факты и действия результата

- **Статус исполнения:** IMPLEMENTED / BROWSER CHECK PENDING по прямому поручению пользователя 2026-10-07. 24 новых formatting/reader/wiring checks и 103 суммарных UI checks прошли; 27 projector, 34 target projector/delivery и 346 related HTTP/boundary tests прошли. Новый модуль доставляется из installed wheel вне checkout. Полный pytest: 2959 passed / 1 failed, тот же существующий property-тест конфигураций. AS-UI-22 проверен на настоящих form/session/transport с заменой только fetch и листовым DOM-портом; browser mouse/keyboard/layout и независимая Tester acceptance не заявлены. См. [журнал](#15-журнал-исполнения-dev-ui-04).
- **REQ/AS:** REQ-UI-03–07, 10; AS-UI-07–09, 15, 19, 22. **DP:** 01/02/05. **Dependency:** DEV-UI-03; оформление может оцениваться после DEV-UI-01.
- **Файлы:** новый `ui/facts.mjs`, `main.mjs`, `styles.css`; новый `tests/ui/facts.test.mjs` и contract fixtures, полученные из existing HTTP/golden данных.
- **Результат:** точки/дома/аспекты и null/[] states, published order/IDs, позиции sign/degree/minute и orb oracle; подробности той же карты, видимый disabled chat без запросов/LLM.
- **Подход:** TDD для pure formatting и reader state; реализация → проверки для DOM composition. Отдельный TDD для CSS/цвета не нужен.
- **Покрытие:** `test_projectors.py::test_chart_dto_exact_golden_and_no_internal_fields`, `test_all_published_point_ids_have_fixed_order_and_12_sign_dictionary`, `test_cosmogram_excluded_aspects_remain_private`; нужны rendering assertions, изменение только longitude и carry/ties.
- **Наблюдаемость:** details — локальная навигация без POST; позитивный контроль reader показывает непустой факт нужной identity. Нового серверного logging нет.
- **Промт:** [04-facts-and-result-actions](../../../prompts/2026-10-06/ui-birth-form-and-facts/04-facts-and-result-actions.md).
- **Completion:** все опубликованные группы/аспекты доступны, oracle и category preservation проверены, после POST и reload действия соответствуют AS-UI-22.

<a id="dev-ui-05"></a>
### DEV-UI-05. Recovery не создаёт скрытый повтор

- **Статус исполнения:** IMPLEMENTED / BROWSER CHECK PENDING по прямому поручению пользователя 2026-10-07. 24 новых recovery checks и 126 суммарных UI checks прошли; целевые server disconnect/admission — 32 passed, связанные HTTP/boundary — 346 passed. Loss/commit failure/timeout, safe-check failure, manual retry и два coordinator с общей листовой сетью проверены детерминированно. Полный pytest: 2959 passed / 1 failed на существующем property-тесте конфигураций; browser/Tester acceptance не заявлены. Предел evidence — в [журнале](#17-журнал-исполнения-dev-ui-05).
- **REQ/AS:** REQ-UI-03, 08, 09; AS-UI-12–14, 16, 18, 23. **DP:** 04/09. **Dependency:** DEV-UI-02/03/04.
- **Файлы:** новый `ui/recovery.mjs`; `session.mjs`, `main.mjs`; новый `tests/ui/recovery.test.mjs`, общий `tests/ui/fixtures/session.mjs`; связанные session/DOM/delivery assertions. `transport.mjs` переиспользован без изменений: уже различает HTTP/network и сохраняет полученные заголовки.
- **Результат:** code-specific recovery, отказ самой сверки, потеря ответа, сохранение submitted intent отдельно от draft/current, foreground двух вкладок. DP-UI-09 применяется без обещания идемпотентности или остановки первой задачи.
- **Подход:** тесты → реализация; контролируемые responses/Event/fake clock и реальные coordinator modules. Mock самого coordinator запрещён.
- **Покрытие:** `test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation`, `test_disconnect_during_protected_commit_is_visible_after_restart`; `test_build_admission.py::test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart`, `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state`. Это server evidence; client transitions дополнены recovery tests на реальных form/coordinator/transport с управляемой сетью/clock. Реальная браузерная проверка остаётся pending.
- **Наблюдаемость:** первый/второй POST и bootstrap/current имеют разные request/run IDs; late completion не выдаётся за ответ второго POST. AS-UI-14 и AS-UI-23 различаются по реально полученному outcome.
- **Промт:** [05-recovery-and-two-tabs](../../../prompts/2026-10-06/ui-birth-form-and-facts/05-recovery-and-two-tabs.md).
- **Completion:** committed/not committed/in-progress после disconnect, отказ сверки, success old/empty и manual retry, two-tabs/CAS outcomes проходят; health остаётся внутренним, автоматического повторного POST нет.

<a id="dev-ui-06"></a>
### DEV-UI-06. Проверенный browser путь и передача Tester

- **Статус исполнения:** PARTIAL / FULL REGRESSION FAILED по прямому поручению пользователя 2026-10-07. Реальная форма на 360/768/1440 px, 0045 → 00:45, Tab/Space/focus/labels проверены. После отдельного исправления прокси штатный browser bootstrap/place selection/natal build/details/reload прошёл; HTTPS API подтвердил natal/cosmogram и восстановление одинаковых фактов с обычным source 127.0.0.1. Исходный handoff — в [журнале](#18-журнал-исполнения-dev-ui-06-и-handoff), актуальное browser evidence и оставшиеся проверки — в [разделе 20](#local-proxy-fix). Полный pytest FAILED по DEBT-CALC-001; G4 и Tester acceptance не объявлены.
- **REQ/AS:** REQ-UI-01…10, AS-UI-01…23, прежде всего AS-UI-19/22/23. **DP:** 01…09. **Dependency:** DEV-UI-01…05.
- **Файлы:** адресные UI/CSS fixes, существующий [UI/UX обзор](../../ui_ux/README.md) и техническая sequence детализация в `docs/sequence_diagrams/http_api/` только при фактической необходимости, Developer plan/handoff; тесты соответствующего дефекта/пробела.
- **Результат:** реальные HTTPS/cookie вход→выбор→build→details→reload, 360/768/1440 px, keyboard/error/loading, recovery; передача runnable setup и точного implemented commit.
- **Подход:** existing coverage + integration/manual/visual checks, затем документальные проверки. Каждый исправленный defect получает deterministic regression; полноценная приёмка принадлежит Tester.
- **Покрытие:** ранее пройденные HTTP/boundary tests не заменяют DOM/browser checks. Использовать existing natal/cosmogram fixtures; demo PNG сравнивать по композиции, не числам. Связать actual evidence с IDs, не объявлять непроверенный сценарий PASS.
- **Наблюдаемость:** сверить 001…004 и server events на real path, initiator/peer/order/outcome/correlation; INFO не расширяется до полного payload.
- **Промт:** [06-browser-checks-and-handoff](../../../prompts/2026-10-06/ui-birth-form-and-facts/06-browser-checks-and-handoff.md).
- **Completion:** целевые/связанные/полный pytest и необходимые Node tests выполнены, фактические browser checks записаны; blocking defects закрыты, limitations обозначены. Tester получает diff/setup/evidence; G4 объявляется только по выполненным gates.

## 6. Порядок, критический путь и возвраты

Один Developer выполняет `01 → 02 → 03 → 04 → 05 → 06`; DTO/визуальный анализ DEV-UI-04 можно готовить после 01, но delivery proof зависит от реального build. Промты не создают дополнительные параллельные агентные задачи. Tester может независимо готовить fixtures/план после утверждения контрактов, а acceptance выполняет на implemented commit. Эта потенциальная календарная экономия не вычитается из person-hours и не обещается без согласования Manager.

Контрольные результаты: страница/transport → валидная форма/выбор → bootstrap/build/state → три группы/действия → recovery → воспроизводимый handoff. Для серийной поставки Developer + Tester ориентир **8–13 рабочих дней после G3**, без ожидания инфраструктуры и чистового переноса; это сценарий расписания, не утверждённый Gantt. Manager решает, когда/как пересматривать target; Developer не заменяет чужие estimates и план.

| Риск / триггер | Ответ и владелец |
|---|---|
| Изменился approved REQ/AS или DP | Остановить зависимый work item, Analyst/Manager пересогласуют и Developer переоценит; независимые части продолжить. |
| Assets отсутствуют в установленном пакете | Исправить package-data/delivery seam в DEV-UI-01; не вводить отдельный deployment service. |
| В DP-UI-09 первый commit завершается после ручного повтора | Применить существующие outcome/current и сохранить accepted risk; не вводить TTL, idempotency alias или server lock. |
| Нет управляемого timer/network seam или browser environment | Разделить preparation от behavioral evidence; вернуть срок/предел Manager/Tester, не маскировать missing path успешным mock-test. |
| Новый framework/browser dependency оказался обязательным | Обосновать необходимость и согласовать scope/оценку до установки; текущая оценка строится без него. |
| Требуется передать ссылку другим людям | Manager возвращает DEBT-UI-001 в обязательный scope; closed-stand estimate не покрывает публичную поставку. |

Rollback планируемого UI ограничивается page/assets routing и package-data этого change; persistence schema, StoredChart, ChartDTO и числовой расчёт не изменяются. Способ Git rollback выбирается при конкретной поставке, команды reset/cleanup планом не разрешены.

## 7. Проверки: выполненное и планируемое

### Выполнено на исходном `033217d`

- `git merge --ff-only FETCH_HEAD` — exit 0, HEAD обновлён с `b36b63d` до `033217d`, конфликта/merge-коммита нет.
- `git diff --name-only 652bd734 HEAD -- src tests pyproject.toml` — пустой вывод.
- `python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py -q` — **27 passed in 0.69s**, exit 0.
- `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` — **339 passed in 24.62s**, exit 0; включает оба disconnect regression, routing/health и DTO/admission/session paths.
- `node --version` — `v24.19.0`; read-only bounded spike `node --input-type=module -e ...` с `Math.round(orb*60)` и assert — **7 cases PASS** (`0`, `0.008`, `0.009`, `0.999`, `1.5`, `1/120`, `3/120`). Это проверка технического способа, не production renderer test.
- Документальная проверка рабочего planning diff: `python -X utf8 -B -` — exit 0; **13 документов, 249 локальных ссылок/якорей, 44 таблицы**, 10 REQ, 23 AS, 9 ACCEPTED DP, 6 work items и 6 DRAFT промтов. Проверены арифметика 40–64 часов и пять ссылок на существующие test functions; изменения реестра ограничены полями Developer, Analyst/Tester и runtime файлы не изменены. `git diff --check` — exit 0; index пустой, новый commit не создан.

Точное воспроизведение bounded spike:

```powershell
node --input-type=module -e 'import assert from "node:assert/strict"; for (const [orb,expected] of [[0,"0°00′"],[0.008,"0°00′"],[0.009,"0°01′"],[0.999,"1°00′"],[1.5,"1°30′"],[1/120,"0°01′"],[3/120,"0°02′"]]) { const m=Math.round(orb*60); assert.equal(`${Math.floor(m/60)}°${String(m%60).padStart(2,"0")}′`,expected); } console.log("PASS: 7 cases");'
```

### Планируемые после появления файлов и допуска

```powershell
# Целевые файлы создаются соответствующим work item; отсутствующий импорт — setup, не RED поведения.
node --test tests/ui/transport.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -q
node --test tests/ui/form.test.mjs tests/ui/places.test.mjs
node --test tests/ui/session.test.mjs tests/ui/facts.test.mjs tests/ui/recovery.test.mjs
# После целевых — связанные; перед G4 при изменённом исполняемом пути — полный Python набор.
python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q
python -B -m pytest -p no:cacheprovider -q
git diff --check
```

Новые browser сценарии выполняются на закрытом HTTPS стенде по [runbook](../../runbooks/http_api_local_https.md), с cookie jar, сетью и журналом; обычный и известный обходной путь отмечаются отдельно. Node/ASGI не выдаются за live HTTPS evidence. Один и тот же approval/commit не подменяет actual checks. Полный pytest, browser/mobile acceptance, wheel/install packaging check и исполнение промтов **в этом planning задании не выполнялись**.

## 8. Handoff и границы текущей поставки

Ниже сохранён handoff этапа планирования. Актуальная передача реализованного пакета со статусом **READY_FOR_TEST** — [раздел 25](#developer-ready-for-test).

Manager утвердил этот план/estimate/зависимости 2026-10-07 после Developer `082c6b9` и Tester `0f6aa82`. Tester подтвердил testability stack/23 AS и готовит независимую проверку после реализации. Analyst подготавливает чистовую редакцию/карту переноса до G5. Административное утверждение не меняет авторские estimates, технические choices или фактический runtime evidence.

**История публикации:** Developer-пакет @ `082c6b9` опубликован по отдельному поручению владельца и включён в `change/*`; Tester review @ `0f6aa82` включён через PR #49 / `2972e42`. **Текущий допуск:** Manager G3 задан этой редакцией; её commit/merge ещё не подтверждены. После интеграции использовать фактический общий HEAD, обновлять журнал work items по выполнению. Исторические промты не редактируются; реализация в этом административном задании не выполнялась.

## 9. Журнал исполнения DEV-UI-01

**Основание:** отдельное поручение пользователя «Обновись из ветки change. Начни выполнение первого промта» от 2026-10-06. Оно разрешает исполнение DEV-UI-01 на проверенном `082c6b9`; наличие формального G3 этим журналом не утверждается. Manager status, Analyst/Tester artifacts, исторические промты и work items 02–06 не изменяются. Коммит, push и PR реализации не выполнялись.

**Исполнение:** 2026-10-06–2026-10-07, COMPLETE в рабочем diff Developer-ветки. Ссылки на executable prompt и нормативные baselines сохранены в карточке. Следующий work item — DEV-UI-02.

### Фактический результат

- `GET /` отдаёт русскую стартовую страницу; CSS и ES modules доступны только под `/ui/`. Использованы `importlib.resources.files`, `FileResponse` и существующий `StaticFiles`. UI обслуживает тот же FastAPI/Uvicorn process; новый process для UI и новые dependencies не нужны. Root исключён из OpenAPI; catch-all не добавлен.
- `transport.mjs` реализует четыре существующих операции: bootstrap, current, поиск мест и natal POST. Все запросы имеют `credentials: same-origin`, `cache: no-store`; JSON build содержит только `birth_date`, `birth_time`, `place_id`, включая явный `null`. Cookie и request ID client не конструирует; status/body/X-Request-ID/Retry-After возвращаются caller.
- Полный HTTP-ответ, в том числе ErrorDTO и текстовая ошибка прокси, отличается от network rejection/обрыва body. При обрыве сохраняются уже полученные status/headers; автоматического повтора нет. AbortSignal задаёт caller, скрытого timer нет. Entry point собирает действующий client и сам запросов не отправляет.
- Package-data содержит HTML/CSS/оба модуля. Офлайн packaging test копирует `src`/`pyproject.toml` во временную область, выполняет `pip wheel --no-deps --no-index --no-build-isolation`, затем `pip install --no-deps --no-index --target`. Новый Python process импортирует приложение из установленного wheel, проверяет четыре package resources и доставку через настоящие ASGI routes вне source checkout. Dependency downloads не выполняются; repo build/egg-info не создаются.
- Стартовая страница пока содержит заголовок и описание. Форма, автоматический bootstrap/current, reader и recovery относятся к DEV-UI-02…05; готовность полного REQ-UI-01 и browser acceptance не заявлены.

### Проверки на рабочем diff

Окружение: Python 3.14.0, Node v24.19.0, FastAPI 0.121.2, httpx 0.28.1, setuptools 80.9.0, wheel 0.45.1; существующие Caddy/mkcert и локальный GeoNames snapshot. Подход «реализация → тесты» сохранён.

| Команда / действие | Фактический результат |
|---|---|
| `git fetch https://github.com/ksenia-baranova/exact-orb-demo.git change/ui-birth-form-and-facts`; `git rev-list --left-right --count HEAD...FETCH_HEAD` | Exit 0; baseline `082c6b9`, расхождение `0 0`, merge не требовался. |
| `node --test tests/ui/transport.test.mjs` | **10 passed**, exit 0. Первое sandbox выполнение остановилось на `spawn EPERM` до исполнения тестов; после разрешённого запуска вне sandbox проверки прошли. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -q` | **7 passed in 9.82s**, exit 0, включая installed-wheel delivery. Первый sandbox запуск: 6 passed, packaging setup заблокирован `PermissionError` в системном temp pip; повтор вне sandbox прошёл. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 55.80s**, exit 0. Сохранены exact OpenAPI shapes, business routing/health, lifecycle и import boundaries. Это расширенный связанный набор, включающий оба HTTP файла из промта. |
| `python -B -m pytest -p no:cacheprovider -q` | **2960 passed in 452.07s (0:07:32)**, exit 0. Платные и сетевые LLM smoke-тесты не запускались. После реализации изменены только русские комментарии/docstrings и журнал; исполняемая логика сохранена. |
| `git diff --check`; структурная проверка `python -X utf8 -B -` | Exit 0; scope ровно **9 файлов**, UTF-8/whitespace, **23 локальные ссылки плана**, **6 work items**. Исторические промты и чужие ролевые документы не затронуты; index пустой. |

### Реальный HTTPS smoke

Запущены скрытые task-owned Uvicorn/Caddy по существующему [runbook](../../runbooks/http_api_local_https.md), с отдельной временной session DB и сертификатом mkcert вне tracked files. TLS проверен через существующий root CA; `verify=False` не использовался. Клиент — `httpx` с `trust_env=False`, таймаутом 5 секунд и cookie jar. Новых natal POST не выполнялось.

| Путь / позитивный контроль | Результат |
|---|---|
| Обычный localhost-клиент: `/`, `/ui/styles.css`, `/ui/main.mjs`, `/ui/transport.mjs` | **200**; HTML/CSS/JavaScript MIME, непустые тела, без Set-Cookie. Root request ID `02883e6b-0589-4eff-9842-db60d7affa31`. |
| Public `/health/live`, `/health/ready` | **404** от Caddy; существующий ACL сохранён. |
| Неизвестный путь; GET `/session/bootstrap` | **404 NOT_FOUND** / **405 METHOD_NOT_ALLOWED**, прежние safe errors. |
| Обычный localhost POST bootstrap | **400 FORWARDED_HEADER_INVALID**, request ID `9f16073a-177c-496d-8f23-9f89a1d3d5d8`: воспроизведён уже известный FIND-TEST-HTTP-001. Это не новый finding и не исправлялось в DEV-UI-01. |
| Контроль с исходным адресом `127.0.0.2`: явный bootstrap → current → поиск Москвы | **200 ready**, затем **200 empty** с той же cookie jar, затем **200 items** с `place_id=524901`. Request IDs: `b8256c6a-bf70-4ea2-b1f1-947e4b535c70`, `34747aac-6191-4f4c-95a1-a3fbe90cf41b`, `0685f19c-b59e-41f5-95f4-9c3e643773ea`. |
| Внутренние `http://127.0.0.1:8000/health/live`, `/health/ready` | **200**, readiness/liveness сохранены. |

В журнале сопоставлены четыре business request ID с парными `http_request_started/finished`; сохранены **20 событий** координации AdmissionControl/ContextService/session_view/PlaceCatalog для разрешённых операций. Asset delivery не создаёт application run; отдельный deterministic test подтверждает отсутствие business events с позитивным bootstrap control. Локальное evidence сохранено в ignored `logs/ui-dev-01-155e3406/https-evidence.json` и `business-events.log`; оно не является публикуемым acceptance artifact. После сохранения диагностики оба task-owned процесса остановлены (Uvicorn PID 32404, Caddy PID 17148); проверено их отсутствие. Временные сертификат/БД и диагностические файлы остаются только в ignored logs.

**Предел:** Node/ASGI/TLS delivery проверены; DOM, keyboard, 360/768/1440 px, браузерная cookie jar, построение карты и полный пользовательский recovery в этом шаге не проверялись. HTTPS бизнес-контроль с `127.0.0.2` не подтверждает исправление обычного localhost flow. Caddy сообщил sandbox отказ записи своих autosave/storage файлов, но ручная конфигурация и проверенные TLS ответы работали; restart/autosave не проверялись. Browser acceptance и G4/G5 остаются будущими gates.

## 10. Журнал исполнения DEV-UI-02

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «выполни второй промт». **Состояние:** IMPLEMENTED / BROWSER CHECK PENDING; полный completion реального browser пути и Tester acceptance не заявлены. Следующий производственный шаг — DEV-UI-03, подключение session/build coordinator; его выполнение этим журналом не начинается.

### Baseline и сохранение предыдущей работы

- Fetch обнаружил четыре новых административных commit поверх `082c6b9`: Tester PR #49 и Manager PR #50. Ветка fast-forward обновлена до `6fc62b9`; смысл требований и сценариев сохранён, G3 утверждён Manager. Другие роли и исторические промты в локальном diff не редактируются.
- Перед обновлением только локальные изменения плана сохранены в отдельный stash и ignored `logs/ui-dev-02/plan-before-update.md`. Код первого шага не убирался из рабочего дерева. После fast-forward восстановлены его карточка, baseline и весь раздел 9 с фактическими проверками; административное утверждение нового плана сохранено. После проверки сохранности свой технический stash `7423f64` удалён; резервная копия остаётся. Stash другого пользователя `pre-pull-main-overlaps-2026-10-03` не затронут.
- Работа выполняется на `dev/ui-birth-form-and-facts-review` поверх `6fc62b9`; исходный runtime/API diff DEV-UI-01 сохраняется. Коммит, push и PR реализации не создавались; index пустой.

### Что реализовано

- `form.mjs` хранит отдельный черновик и проверяет календарную `YYYY-MM-DD`, подтверждённый ID места, известное `HH:MM` либо явную неизвестность. `00:00`, `12:00`, `23:59` сохраняются строками. Пустое/некорректное время без отметки не становится неизвестным автоматически. Переключение неизвестности сохраняет дату, место и ранее введённое время; intent содержит `birth_time:null` только при явной отметке.
- Presentation checkbox исходно снят и проверяется до выдачи intent. Значение не сохраняется и не сериализуется; frozen intent содержит ровно `{birth_date,birth_time,place_id}`. Локальная проверка даты не вводит отдельное ограничение диапазона или правило часового пояса браузера: окончательные domain/gap/fold ошибки остаются серверными.
- `places.mjs` отправляет raw query от трёх введённых Unicode-символов после debounce **250 ms**; trim используется только для порога/пустого ввода. Нормализация NFKC/casefold/ранжирование остаются на сервере. Таймер и сеть заменяются только в тестовом листовом шве. Generation проверяется перед запуском и после ответа, отмена fetch не является единственной защитой. Сокращение/очистка, отменённый timer и старый response не подменяют актуальные варианты.
- Выбор мышью либо ArrowUp/ArrowDown/Enter сохраняет конкретный `place_id`; Escape закрывает подсказки, стрелки могут открыть их снова. Редактирование сразу сбрасывает подтверждённый ID, даже если текст совпадает с прежним названием. Подписи содержат название, «Регион» (`admin1_name`) и страну (`country_code`); public key не переименован. Выбор не создаёт дополнительный GET или POST.
- Пустой результат, некорректный query и временная недоступность различаются. `Retry-After` ограничивает следующий поиск; по истечении срока разрешается явный повтор, автоматического GET нет. Диагностические X-Request-ID/Retry-After доступны в состоянии поиска. Сокращение и повторный ввод во время cooldown сохраняют причину отказа и его заголовки.
- `index.html`/`main.mjs`/`styles.css` связывают форму с настоящими controller/transport: дата → место → время, видимые labels, combobox/listbox, ошибки полей, live status, активная строка, различимый focus, карточка в палитре прототипа и адаптивные размеры. Серверные строки выводятся через `textContent`. Нет имени, координат, offset, секунд, колеса, будущих числовых секций, текста/страницы условий или имитации юридического согласия.
- Submit после локальной проверки выдаёт DOM event `birth-intent` с неизменяемыми тремя полями. **HTTP POST построения пока не подключён**: это ответственность DEV-UI-03. Никакого ложного состояния «карта построена» или демонстрационных фактов в UI нет. Форма/поиск — реальные компоненты, пустые future handlers не добавлены.

### Подход, RED и GREEN

Подход TDD для manual gate и гонок: подготовлены настоящие modules/seams с базовым вводом и одиночным поиском, затем проверки наблюдаемого недостающего поведения. Ошибки импорта не учитывались как behavioral RED.

1. `node --test tests/ui/form.test.mjs tests/ui/places.test.mjs` — **30 passed / 5 failed**, exit 1: неотмеченный gate ещё допускал intent; поздний Кир заменял Киро; три поздних ответа после сокращения/очистки показывали список вместо idle. Это реальные assertions на исполняемых компонентах, сеть/timer управляемые.
2. После manual gate и post-await generation guard — **35 passed**, exit 0.
3. Новый regression `node --test --test-name-pattern 'shortening and retyping during Retry' tests/ui/places.test.mjs` — **1 failed**, exit 1: очистка видимого error теряла причину всё ещё действующего Retry-After при новом вводе. Причина устранена на ответственном controller: cooldown metadata сохраняется, ниже порога ошибка скрывается, следующий запрос не выполняется до срока. Позитивный явный retry после expiry проходит.
4. Итоговый Node набор ниже — **46 passed**: 36 новых form/place checks + 10 предыдущих transport checks. Последний GREEN использует поддержанный Node v24.19.0 `--test-isolation=none`: тесты запускаются в одном процессе внутри sandbox; production behavior и dependencies не меняются.

### Фактические проверки

| Команда / действие | Результат |
|---|---|
| `git fetch https://github.com/ksenia-baranova/exact-orb-demo.git change/ui-birth-form-and-facts`; `git merge --ff-only FETCH_HEAD` | Exit 0; `082c6b9` → `6fc62b9`, merge commit не создан, локальный runtime и журнал сохранены. |
| `node --test --test-isolation=none tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs` | **46 passed**, exit 0. |
| `python -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/http_api/test_place_dto.py -q` | **106 passed in 1.62s**, exit 0. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 27.40s**, exit 0; API schema/routing/lifecycle/boundaries сохранены. |
| `python -B -m pytest -p no:cacheprovider -q` | **2960 passed in 125.57s (0:02:05)**, exit 0. Платные/сетевые LLM smoke не запускались. |
| `python -B logs/ui-dev-02/verify_installed_assets.py` | PASS: переиспользован offline installed-wheel test; **6 ресурсов**, включая новые form.mjs/places.mjs, доставлены через настоящее установленное ASGI-приложение вне source checkout. Никаких dependency downloads. Первый запуск helper имел ошибку пути импорта tests; после setup correction проверка выполнена успешно. |
| `python -X utf8 -B -` — структурная проверка страницы | PASS: ровно пять подписанных inputs в нужном порядке, исходно снятые checkbox, ARIA targets/error references, существующие DOM selectors, text-only rendering. Это структурная проверка, не browser acceptance. |
| `node logs/ui-dev-02/live_place_flow.mjs` | PASS: **6 HTTPS ресурсов**, public health 404; К/Ки не создают запроса, Кировск создаёт **1 GET**, выбор второго реального варианта и null/known intent проходят, **0 natal POST**. Native HTTPS leaf проверяет CA/hostname, IPv4 source `127.0.0.2`; fake timer управляет debounce. Начальный bind EINVAL был setup IPv6/IPv4 mismatch и исправлен `family:4` только в test helper. |
| `git diff --check`; структурная проверка `python -X utf8 -B -` | Exit 0: **13 файлов** первого/второго промта и плана, пустой index, UTF-8/whitespace, **24 локальные ссылки**, 6 work items; исходный раздел 9 полностью сохранён, порядок 6 событий sequence 002 проверен. |

### HTTPS, sequence и предел результата

Позитивный HTTPS read использовал сохранённый mkcert certificate/root CA, существующие Uvicorn/Caddy и отдельную ignored session DB. `verify=False` не использовался. В реальном каталоге выбран второй Кировск: `place_id=705809`, регион «Луганская область», country_code `UA`; это данные DTO каталога без самостоятельной нормализации/переименования.

GET request ID **`22c87fa0-f186-4d2b-bfe5-f894d11c4255`** сопоставлен с **6 событиями** `http_request_started`, AdmissionControl send/receive, PlaceSearch send/receive, `http_request_finished` — порядок соответствует HTTP sequence 002. Ни ContextService, ни ApplicationOrchestrator для поиска не вызывались. Запрет GET до порога подтверждён leaf counter рядом с успешным запросом; выбор и валидация не отправляли natal POST.

Обычный localhost GET places по-прежнему даёт **400 FORWARDED_HEADER_INVALID**, request ID `f80a6923-8401-4ff4-af5b-1311ab47d710`; root доставляет форму с **200**. Это сохранённый FIND-TEST-HTTP-001 и согласованное пользователем ограничение. Позитивный Node/HTTPS контроль с `127.0.0.2` не выдаётся за исправление штатного browser localhost flow.

**Браузерный блок:** инструмент `cua.getTab` отклонил открытие `https://exact-orb.localhost/` политикой доступа к URL (`Browser Use rejected this action due to browser security policy`, `requested URL protocol is not allowed`). Обход через другой browser/surface/raw protocol не выполнялся. Поэтому фактические DOM mouse/keyboard, screen-reader/focus, 360/768/1440 px и визуальное соответствие макету в этом проходе **NOT VERIFIED**. Node проверки controller и структура HTML не заменяют эту проверку. DEV-UI-02 не помечен полным COMPLETE до реального browser evidence.

Локальные HTTP/packaging/sequence evidence и резервная копия предыдущего журнала находятся только в ignored `logs/ui-dev-02/`. HTTPS стенд оставлен для ручного просмотра формы: Uvicorn PID **21224**, Caddy PID **16216**, один application process обслуживает и UI, и API. Текущий этап готовит intent; actual build, восстановление сессии и отображение результата подключаются последующими заданиями.

## 11. Подготовка коммита DEV-UI-01/02

**Дата:** 2026-10-07. **Основание:** отдельное поручение пользователя «Готовь комит по двум промтам». Подготовлен один атомарный коммит в `dev/ui-birth-form-and-facts-review` поверх `6fc62b9c8813b5aadfd5150ca39033664f18b777`. Точный hash поставки определяется историей Git после сохранения; self-referential hash в документ не вносится.

**Состав:** ровно **13 файлов**: `app.py` и `pyproject.toml`; шесть ресурсов `ui/index.html`, `styles.css`, `main.mjs`, `transport.mjs`, `form.mjs`, `places.mjs`; `tests/http_api/test_ui_delivery.py` и три `tests/ui/*.test.mjs`; этот Implementation Plan. Сертификаты, session DB и диагностические файлы остаются в ignored logs. Исторические промты и артефакты других ролей не включаются.

Пакет сохраняет выполненные проверки раздела 10: **46 Node**, **106 place contracts/DTO**, **346 HTTP/boundaries**, **2960 full pytest**, installed-wheel delivery и HTTPS контроль. После этих проверок менялись только сведения о поставке в плане; исполняемый код и тесты не менялись. Перед коммитом проверяются staged scope и `git diff --cached --check`.

Браузерный критерий DEV-UI-02 остаётся **PENDING**, известный FIND-TEST-HTTP-001 сохраняется, DEV-UI-03 не начат. Этот коммит не подтверждает независимую Tester acceptance. Записи разделов 9–10 об отсутствии коммита и пустом index относятся к моменту их выполнения. Push и PR в текущем поручении не выполняются.

## 12. Журнал исполнения DEV-UI-03

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «Реализуй третий промт». **Состояние:** IMPLEMENTED / FULL REGRESSION FAILED; локальный diff поверх `ef75d77`. Исполнение разрешено отдельно от исторического DRAFT в промте. G3 Manager интегрирован в `6fc62b9`; смысл REQ/AS @ `ce25dd0` и нормативный HTTP baseline сохранён.

Пакет двух предыдущих шагов сохранён и ранее опубликован: `ef75d77` в `dev/ui-birth-form-and-facts-review` репозитория `ksenia-baranova/exact-orb-demo`. `origin` настроен на другой репозиторий, поэтому сверка общего change выполнена по точному URL. Начальное рабочее дерево и index пустые. Новый коммит, push или PR третьего шага не создавались; поручение относится к реализации.

### Реализованное поведение и границы

- Новый `session.mjs` координирует настоящие form/transport. При открытии страницы выполняется `POST bootstrap {}` → `GET current`; успешный bootstrap/version не превращается в карту. `empty`, `chart_ready` со stale true/false и `chart_unavailable` сохраняются отдельно. При `empty/unavailable` chart отсутствует; stale сохраняет исходный ChartDTO без пересчёта. Ответ без полноценной идентичности карты не объявляется committed успехом.
- Submit повторно проверяет валидность формы и ручной checkbox, сохраняет frozen intent ровно `{birth_date,birth_time,place_id}` и отправляет один POST. Busy guard устанавливается до await и действует для чтения и построения внутри этой вкладки. Нет client expected version, самодельной cookie, shared mutable результата или скрытого автоматического POST. Черновик остаётся отдельным от отправленного intent; последующее редактирование не меняет уже отправленный запрос.
- `422` сопоставляет `birth.date/time/place` с соответствующими полями. Сохраняются IssueDTO code/candidates/constraints, `user_message` и неизвестные fields для общей ошибки; отображение использует `textContent`. Двусмысленная минута требует исправления пользователем, без browser timezone или автоматического выбора UTC offset. Исправление поля снимает его server issue. Отказ не заменяет предыдущую подтверждённую карту.
- `already_applied` и `RESULT_SUPERSEDED` приводят к отдельному current. `409 SESSION_REQUIRED/EXPIRED/NOT_FOUND` восстанавливаются bootstrap → current без повторного build; повторный session 409 останавливает ограниченную сверку вместо цикла. Отказ самой сверки сохраняет подтверждённую карту/черновик и запрещает build до безопасного чтения.
- `Retry-After` сохраняется вместе с request ID и ограничивает следующее явное действие. Fake clock проверяет точную границу; истечение timer только обновляет доступность кнопки, сеть автоматически не вызывается. Network build failure, `STATE_COMMIT_FAILED`, `BUILD_TIMEOUT` и неполный `200` оставляют исход неподтверждённым и блокируют новый POST. Их code-specific сверка, restart/readiness, потерянный ответ и foreground двух вкладок остаются DEV-UI-05; для них текущий шаг не заявляет готовый recovery.
- `main.mjs` запускает координатор после сборки формы, показывает ожидание и различие состояний, связывает field errors/focus и блокировку кнопки. Сохранённый birth из current предзаполняет нетронутую форму с настоящим ID места; регион/страна, отсутствующие в BirthViewDTO, не выдумываются. Ввод во время чтения и draft при recovery не затираются. Checkbox остаётся снятым при новом открытии и не сохраняется. Stale/unavailable получают явные «Пересчитать» / «Построить заново» через тот же submit.
- Ровно четыре файла поставки: `ui/session.mjs`, `ui/main.mjs`, `tests/ui/session.test.mjs`, этот план. Transport уже покрывает нужные outcomes и AbortSignal, поэтому не изменён. Wildcard package-data уже включает новый модуль. Backend/API/расчёт/logging, другие ролевые артефакты и исторические промты не изменены. Читаемые таблицы и действия результата относятся к DEV-UI-04.

### TDD и фактические проверки

Подготовительный seam — исполняемый coordinator с базовыми bootstrap/current/успешным POST. Затем проверены недостающие переходы на настоящих form/session/transport с заменой только fetch leaf; импорт не считается RED.

1. `node --test --test-isolation=none tests/ui/session.test.mjs` — **4 passed / 15 failed**, exit 1: двойной click отправлял второй POST, build допускался до чтения, отсутствовал field mapping и required current/session recovery, incomplete success заменял подтверждённую карту.
2. После guard/mapping/recovery — **18 passed / 1 failed**: тест сразу пытался повторить safe read после `Retry-After:5`. Он уточнён по действующему ограничению и переведён на управляемый fake clock; реальное ожидание не используется.
3. Итог — **27 session checks**, включая rate/capacity, read/build overlap, отказ сверки, dispose/late response и три проверки настоящего mount через листовой DOM-порт. Вместе с предыдущими checks — **73 passed**. DOM-порт проверяет вызовы/render/focus связи, но не является browser acceptance или layout evidence.

| Команда / действие | Фактический результат |
|---|---|
| `git ls-remote --heads https://github.com/ksenia-baranova/exact-orb-demo.git change/ui-birth-form-and-facts` | Exit 0; общий HEAD `6fc62b9` уже в Developer `ef75d77`, обновление checkout не потребовалось. |
| `node --test --test-isolation=none tests/ui/session.test.mjs` | **27 passed**, exit 0. После замены микрозадачи в dispose-тесте на явный callback фактического входа в leaf выполнен весь набор ниже. |
| `node --test --test-isolation=none tests/ui/session.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs` | **73 passed**, exit 0. Node v24.19.0; новые dependencies отсутствуют. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_session.py tests/http_api/test_request_boundary.py tests/http_api/test_build_admission.py -q` | **113 passed in 3.09s**, exit 0. Переиспользованы действующие server coverage/fixtures. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 24.75s**, exit 0 вне sandbox. Первый запуск: **345 passed / 1 failed in 27.66s**, pip offline wheel setup заблокирован PermissionError системного temp; это не behavioral defect. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 125.24s**, exit 1. Ошибка существующего `test_property_configuration_count_does_not_grow_when_threshold_decreases`; полный regression gate не пройден. Платные/сетевые LLM smoke не запускались. |
| `python -B -m pytest -p no:cacheprovider tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases -q` | **1 failed in 0.86s**, exit 1; тот же Hypothesis-контрпример воспроизводится отдельно от UI. |
| `python -B logs/ui-dev-03/verify_regression_baseline.py` | Контрпример воспроизведён детерминированно на **18 Python-файлах**, совпадающих по строкам с Git @ `ef75d77`: high/low counts **0/1**. Позитивный контроль с уникальными парами даёт **1/1**. Helper диагностический, не заменяет failed regression gate. |
| `python -B logs/ui-dev-03/verify_installed_assets.py` | PASS: offline wheel/install и новое импортированное ASGI-приложение вне checkout доставляют **7 ресурсов**, включая session.mjs. Downloads отсутствуют. |
| `node logs/ui-dev-03/live_session_flow.mjs` | PASS: **7 HTTPS ресурсов**, настоящий bootstrap/current, **0 POST до manual gate**, один explicit natal POST при двойном действии; reload/current возвращает тот же ChartDTO/identity/version без дополнительного POST. TLS CA/hostname проверены, source `127.0.0.2`, отдельная cookie jar. Это API/controller evidence, не браузерная cookie jar/DOM. |
| `python -B logs/ui-dev-03/verify_sequence.py` | PASS: **6 business requests / 48 событий** координации; HTTP 001/003/004 и вложенные application pairs сопоставлены. Первое ожидание helper для поиска было уточнено с `search_places` до фактического `operation=search`; production code/diagram не менялись. |
| `git diff --check`; `python -X utf8 -B -` — структурная проверка плана/пакета | Exit 0: **4 файла** поставки, UTF-8/newline/whitespace; **25 локальных ссылок/anchors**, **6 work items**. Index пустой, HEAD остаётся `ef75d77`; исторические промты и чужие ролевые файлы не затронуты. |

### Реальное HTTPS и наблюдаемость

Использован существующий Uvicorn/Caddy стенд DEV-UI-02, его отдельная ignored session DB и сертификат mkcert; новый UI process не создавался. Пример: `1985-09-02`, `00:45`, подтверждённая Москва `524901`. Manual gate проверен настоящим form/coordinator, транспорт передал только три поля. Явный POST **`828c448f-29ed-46f3-be33-87c2c7431597`** дал `chart_identity=eo:calc:v2:f112dfae69d8d6daaf5051292bc21f78682940bb2df0fc7d7b1f027623f6b7e2`, state version **1**. После повторного bootstrap **`bd3d77e1-32bd-4d30-a078-6317a3952328`** current **`37334d4f-deb3-4977-91cd-948414102fce`** вернул ту же карту и birth.

Первый bootstrap **`b1f2eb8d-1c49-4d15-9a2f-b64d89c1bdb5`** сопоставлен с reserve/create, первый current **`f60cdac4-5ac4-4fef-ab05-fa39d2e0cc4d`** — с load/session_view и empty. В build есть admission reserve → Orchestrator.execute → ContextService.load → Handler.handle → BirthDataResolver.resolve → ensure_chart → to_stored → ContextService.save/Committed → ApplicationCommitted → release. Оба current имеют только load/session_view и request terminal, без нового Orchestrator/расчёта. Сохранены request/run correlation и 48 компактных событий в ignored `logs/ui-dev-03/sequence-events.log`; DEBUG payload туда не копировался.

### Непройденный regression gate и пределы

Новый контрпример относится к неизменённой области конфигураций: `_aspect_lists()` допускает SEXTILE и TRINE для одной пары `(p0,p1)`, а также SEXTILE и TRINE для `(p0,p4)` с orb 4 у второго TRINE. При пороге 7 bisextile finder видит две trine edges и отклоняет кандидат; при пороге 3 остаётся одна trine edge и count становится 1 вместо 0. Наличие разных типов для одной пары нарушает предпосылку монотонного oracle; вопрос согласования генератора и допустимых входов finder требует отдельной задачи расчётного слоя. Тест, генератор, алгоритм, golden и допуски не изменялись и не отключались. Полный pytest честно остаётся FAILED.

Реальные browser DOM/mouse/keyboard/360–1440 px и визуальное соответствие ещё **NOT VERIFIED**: ранее инструмент отклонил локальный URL политикой доступа, обход не выполнялся. Известный localhost `FORWARDED_HEADER_INVALID` сохранён; позитивный source `127.0.0.2` не считается его исправлением. DEV-UI-04 reader/actions и DEV-UI-05 полное recovery не выполнены; новая независимая Tester acceptance не получена. Стенд оставлен для просмотра, секреты/DB/диагностика только в ignored logs. Исторические записи об отсутствии реализации/коммита в разделах 9–11 относятся к своим моментам исполнения.

## 13. Исправление формата ввода времени

**Дата:** 2026-10-07. **Основание:** пользовательский дефект — при вводе времени `0045` оставалось одной строкой без разделителя, тогда как дата имела структурированный ввод. Исправление выполняется поверх сохранённого локального DEV-UI-03; предыдущие изменения не откатываются.

**Реестр ручного тестирования:** [TEST-FIND-UI-004](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-004), зарегистрирован по отдельному поручению пользователя. Исправление готово; ручной retest ещё NOT RUN, дефект не закрыт.

**Корневая причина:** время использовало `type=text` и placeholder `ЧЧ:ММ`; input handler передавал строку в draft без форматирования. Строгая проверка `HH:MM` действовала только перед отправкой, поэтому `0045` оставалось на экране и затем отвергалось вместо удобного ввода `00:45`.

Добавлен presentation formatter `formatTimeInput` в `form.mjs`: ровно три/четыре цифры показываются как `HH:M` / `HH:MM`. `main.mjs` применяет его на input и сохраняет границы/направление выделения при вставке двоеточия. В `index.html` задан numeric inputmode для цифровой клавиатуры. Готовое `HH:MM` и очистка сохраняются; ведущие нули не теряются. Неполное время остаётся неполным, неверный диапазон не округляется и не заменяется, неизвестность не включается автоматически. Model validation и HTTP body по-прежнему требуют `HH:MM` либо явный null; секунды/offset, серверные schema/API и расчёт не менялись.

**Regression evidence:** в существующий `session.test.mjs` добавлено шесть checks через настоящий mount/form/session/transport и листовой DOM-порт. До исправления — `node --test --test-isolation=none tests/ui/session.test.mjs`: **27 passed / 6 failed**, exit 1, в том числе точное `0045 != 00:45`. После исправления весь Node-набор: **79 passed**, exit 0. Проверены последовательный набор, вставка `0045/0000/1200/2359`, каретка/выделение, очистка, неполный ввод, секунды, неверные диапазоны, сохранность при переключении неизвестности и позитивная отправка только канонического `00:45`.

**Scope:** дополнительно изменены `form.mjs` и `index.html`; поправки `main.mjs`, regression tests и журнал встроены в уже имеющийся diff DEV-UI-03. Текущий общий пакет — шесть файлов: план, main/form/index, session.mjs и session.test.mjs. Коммит/push/PR этого исправления не создавались. Проверка настоящего browser input остаётся pending; листовой DOM-порт не подтверждает поведение мобильной клавиатуры или layout.

| Команда | Фактический результат после исправления |
|---|---|
| `node --test --test-isolation=none tests/ui/session.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs` | **79 passed**, exit 0; 33 session/mount checks и 46 предыдущих form/place/transport checks. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 24.79s**, exit 0, включая delivery из wheel. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 123.78s**, exit 1. Повторяется тот же неизменённый property-тест конфигураций с контрпримером из раздела 12; полный regression gate остаётся FAILED. |
| `git diff --check`; `python -X utf8 -B -` — структурная проверка | Exit 0: **6 файлов** текущего пакета, UTF-8/newline/whitespace, **25 локальных ссылок и anchors**. Index пустой; предыдущая реализация и посторонние файлы сохранены. |

## 14. Подготовка коммита DEV-UI-03 и исправления времени

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «готовь комит». Ветка — `dev/ui-birth-form-and-facts-review`, родитель поставки — `ef75d77232e1f629540827bfd90e93c1c16977ea`.

В единый атомарный коммит входят семь файлов: этот план, реестр ручных багов `docs/testing/ui-birth-form-and-facts/manual-test-bugs.md`, `ui/session.mjs`, `ui/main.mjs`, `ui/form.mjs`, `ui/index.html` и `tests/ui/session.test.mjs`. Пакет включает исполнение третьего промта, исправление TEST-FIND-UI-004 и его автоматические regression checks. Сообщение коммита — на русском языке. Исторические записи об отсутствии коммита и меньшем составе пакета в разделах 12–13 относятся к моментам соответствующих проверок.

После последних исполняемых изменений выполнены команды из раздела 13: **79 Node checks passed**, **346 HTTP/boundary tests passed**, полный pytest — **2959 passed / 1 failed** на существующем property-тесте конфигураций. После этих запусков изменены только записи журнала и реестр, исполняемый код не менялся. Полный regression gate остаётся FAILED; ручной retest TEST-FIND-UI-004 и независимая browser/Tester acceptance ещё не выполнены. Push и PR этого пакета не выполнялись.

## 15. Журнал исполнения DEV-UI-04

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «реализуй 4-й промт». **Baseline:** `564186d1e40ee8560b6df402c51ae2ee401c38e6`, ветка `dev/ui-birth-form-and-facts-review`; начальное дерево/index чистые. Общий `change/ui-birth-form-and-facts` подтверждён `git ls-remote` по точному URL `ksenia-baranova/exact-orb-demo` @ `6fc62b9`; уже входит в HEAD. Утверждённый смысл REQ/AS @ `ce25dd0` и DP-UI-01/02/05 сохранён. Действующее поручение разрешает реализацию, несмотря на историческое DRAFT в промте; исторический файл не изменён.

### Результат и границы

- Создан `ui/facts.mjs`: pure reader трёх публичных групп, словари 16 point IDs, пяти углов, 12 знаков, семи видов и трёх категорий аспектов. Позиции берутся только из опубликованных `sign/degree/minute`; `longitude` и `cusp_longitude` не читаются для форматирования. Градус/минута имеют вид `ДД°ММ′`, ретроградность явно подписана только при `true`; южный узел отмечен производной позицией. Точки следуют HTTP whitelist order, дома сортируются по номеру, все аспекты сохраняют порядок DTO.
- `formatOrb` округляет `orb * 60` через `Math.round`, с переносом минут и правилом half-up; отображение не меняет исходные orb/type/category. Нового tolerance, расчёта знака/категории или API поля нет. Каждое чтение создаёт новые строки без общего mutable результата.
- Натал показывает точки, дома и пять опубликованных углов внутри группы домов. У космограммы `houses/angles/house_system=null`: «Для домов нужно время рождения», у точки дом «Не определяется без времени»; положения явно описаны как позиции технического якоря, орбисы — как консервативные значения устойчивых аспектов. `aspects:[]` даёт «Аспекты не найдены», сохраняя остальные факты.
- `main.mjs` связывает текущий подтверждённый view с блоком результата после формы. Native button «Показать подробности карты» локально открывает/закрывает три группы, обновляя `aria-expanded`; второй POST/GET или LLM не требуется. Видимое «Открыть чат» имеет native disabled, исключено из tab activation, рядом объяснение недоступности. Идентичность берётся из `chart_identity`, не из state_version или черновика. Смена identity закрывает подробности и заменяет старые строки; empty/unavailable удаляет числовые факты; stale сохраняет исходный DTO с явной пометкой. Повторная публикация того же view не пересоздаёт строки и не сбрасывает локальное раскрытие.
- `styles.css` продолжает палитру, карточки и ритм Р5/Э7. Семантические таблицы имеют caption, scope и роли заголовков/строк; на узком экране строки раскладываются в две колонки с подписями ячеек и переносом длинных названий. Это подготовленная адаптивная раскладка, ещё не browser/layout evidence. Рабочий UI не добавляет wheel, заголовки/таблицы будущих групп или демонстрационные числа.
- Новые проверки используют existing `tests/http_api/golden/chart_dto.json`, `session_view.json` и `tests/fixtures/places.jsonl`. Полный `tests/ui/fixtures/natal_1985_chart_dto.json` получен через настоящий `project_chart(decode_chart_artifact(...))` из existing `tests/golden/chart_artifact_format_1_natal_1985.bin`: только публичный DTO, **16 точек / 12 домов / 46 аспектов**; исходные числа/golden не менялись. Отдельный DOM check подтверждает все строки и ретроградность, без усечения до короткого sample. DOM-порт из session tests перенесён в общую `tests/ui/fixtures/dom.mjs` и дополнен минимальными операциями настоящего reader; его переиспользуют оба набора. Предыдущие assertions сохранены, новой зависимости нет. Это необходимый test seam для блока после формы, не симуляция браузера.
- Адресно расширен `tests/http_api/test_ui_delivery.py`: прежний installed-wheel probe проверял только четыре ресурса и не подтверждал новый импорт `facts.mjs`. Теперь source/installed tests проверяют восемь реальных UI ресурсов, MIME/байты, отсутствие session/calculation и business logging при static GET с разрешённым bootstrap/current positive control. Backend production code, публичные схемы, расчёт, lifecycle, логирование, ADR и другие ролевые файлы не изменены.

### TDD и фактические проверки

Первый seam уже умел форматировать orb/позицию и читать непустые точки. Behavioral RED не основан на отсутствии файла/импорта: **9 passed / 5 failed**, exit 1 — отсутствовали канонический порядок, дома/углы, аспекты и null/empty states. После полного reader — **14 passed**, exit 0. Затем добавлены локализация всех типов и DOM/wiring checks; CSS выполнен без отдельного RED цикла согласно карточке.

| Команда | Фактический результат |
|---|---|
| `git ls-remote --heads https://github.com/ksenia-baranova/exact-orb-demo.git change/ui-birth-form-and-facts` | Exit 0 вне sandbox, общий HEAD `6fc62b9` уже в Developer истории. Первый запуск заблокирован sandbox network proxy `127.0.0.1:9`; повторена та же команда. |
| `node --test --test-isolation=none tests/ui/facts.test.mjs` | RED **9 passed / 5 failed**; GREEN pure reader **14 passed**, оба exit отражают assertions поведения. |
| `node --test tests/ui/facts.test.mjs` | **23 passed**, exit 0 вне sandbox до добавления полного natal fixture. Точная команда промта сначала получила `spawn EPERM`; это environment failure, не behavioral RED. Итоговые 24 reader checks включены в следующую команду. |
| `node --test --test-isolation=none tests/ui/facts.test.mjs tests/ui/session.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs` | **103 passed**, exit 0; 24 новых checks и 79 сохранённых UI checks, включая TEST-FIND-UI-004. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py -q` | **27 passed in 0.34s**, exit 0. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py tests/http_api/test_ui_delivery.py -q` | **34 passed in 8.40s**, exit 0 вне sandbox; установленные восемь ресурсов доставлены новым процессом вне checkout. Первый запуск: **33 passed / 1 failed**, pip wheel получил PermissionError системного temp, не behavioral defect. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 25.12s**, exit 0 вне sandbox. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 124.42s**, exit 1. Тот же `test_property_configuration_count_does_not_grow_when_threshold_decreases`, пары `(p0,p1)/(p0,p4)` с SEXTILE/TRINE, high/low counts 0/1 — см. раздел 12. Алгоритм и тест не изменены/не отключены; full regression gate FAILED. |
| `git diff --check`; `python -X utf8 -B -` — structural checks | Exit 0: **9 файлов** scope, UTF-8/newline, **27 локальных ссылок/anchors**, index пустой, HEAD `564186d`. Full natal fixture валиден через `ChartDTO.model_validate_json` и в точности совпадает с публичной проекцией исходного golden. |

После Python checks production code не менялся; добавлены только полный публичный natal fixture, его UI check и записи плана. Затем весь Node-набор повторно дал 103 passed. Полный pytest дополнительно не повторялся: эти test-only/UI JSON изменения не входят в Python collection и не меняют поставляемый код.

AS-UI-22 проверен отдельно для натала и космограммы на настоящих mount/form/session/transport: успешный POST → непустые подробности именно A, затем новое открытие/bootstrap/current → те же identity/строки; trace содержит ровно один natal POST, действия подробностей и попытки неактивного чата не добавляют сеть или dialog. Позитивные controls — реальные опубликованные строки, все aspects и корректный intent. Взаимодействие через листовой DOM-порт подтверждает wiring и native attributes, но не фактическую браузерную активацию клавишами.

### Ограничения и handoff

Реальные browser mouse/keyboard, mobile 360/768/1440 px, отсутствие горизонтального scroll и сравнение отображённой страницы с макетом — **NOT VERIFIED**. В предыдущем шаге browser tool отклонил локальный URL политикой доступа; обход/повтор через другой механизм для browser outcome не выполнялся. Просмотрены сами Р2/Р5/Э7, их demo values и wheel не перенесены. Installed ASGI/DOM checks не заменяют browser/Tester acceptance.

Следующий шаг реализации — DEV-UI-05; независимая приёмка и TEST-FIND-UI-004 manual retest остаются pending. Известное ограничение M1-6 localhost `FORWARDED_HEADER_INVALID` не исправлялось. Коммит/push/PR этого пакета не создавались; текущий diff остаётся локальным поверх `564186d`. Записи предыдущих разделов о NOT STARTED относятся к своим моментам исполнения.

### Уточнение доступности ручной проверки

После вопросов пользователя проверены работающие процессы Uvicorn/Caddy и `/health/ready`: **200**; `facts.mjs`, `main.mjs`, `styles.css` доставляются с байтами текущего worktree. Это подтверждает запуск и доставку, но не успешный сквозной сценарий браузера.

Обычный локальный HTTPS-клиент с адресом `127.0.0.1` получил на `GET /places?query=Москва` **400 FORWARDED_HEADER_INVALID**, request ID `fca10fd6-2c78-44d9-8d16-59f045b91412`. Тот же URL с исходным адресом клиента `127.0.0.2` дал **200 items**, включая Москву `524901`, request ID `143630f9-a6ce-4d6b-ac15-e9ca301ae003`. Это повторное evidence существующего FIND-TEST-HTTP-001, не новая UI-находка и не исправление дефекта. `127.0.0.2` — адрес тестового клиента; Caddy/Uvicorn слушают `127.0.0.1`, сайт в браузере открывается через `https://exact-orb.localhost/`.

**Сквозная ручная проверка штатного localhost: BLOCKED** на поиске/сессии из-за известного дефекта прокси. Без подтверждённого `place_id` форма запрещает новый POST. Можно проверять внешний вид и локальный ввод, но не заявлять ручную проверку построения/результата; браузерная приёмка DEV-UI-04 остаётся NOT VERIFIED. Сначала требуется отдельное исправление локального proxy flow и повторная проверка обычным клиентом. Предыдущая рекомендация открыть страницу и построить карту была неполной; наличие готового server process само по себе этого не доказывает. Настройки/код прокси в текущем пакете не менялись.

## 16. Подготовка коммита DEV-UI-04

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «готовь комит». Ветка — `dev/ui-birth-form-and-facts-review`, родитель — `564186d1e40ee8560b6df402c51ae2ee401c38e6`.

Один атомарный пакет содержит девять файлов: этот план; `ui/facts.mjs`, `ui/main.mjs`, `ui/styles.css`; `tests/ui/facts.test.mjs`, `tests/ui/session.test.mjs`; общие `tests/ui/fixtures/dom.mjs` и `natal_1985_chart_dto.json`; адресно расширенный `tests/http_api/test_ui_delivery.py`. Сообщение коммита — на русском языке. Historical prompt, другие ролевые файлы и production backend не изменены. Сведения раздела 15 об отсутствии коммита относятся к предыдущему моменту исполнения.

Сохраняются фактические результаты раздела 15: **103 UI checks**, **346 HTTP/boundary tests**, installed-wheel delivery; full pytest **2959 passed / 1 failed** на неизменённом property-тесте конфигураций. После проверок исполняемый код не менялся; при подготовке уточнены только журнал и ограничения evidence. Сквозной ручной сценарий localhost остаётся BLOCKED, browser/Tester acceptance не получена. Push/PR этого пакета не выполнялись.


## 17. Журнал исполнения DEV-UI-05

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «выполни 5-й промт». **Входной HEAD:** `6d970f605188ad1419cbae791e8e2f83d63d67c9`, ветка `dev/ui-birth-form-and-facts-review`; дерево/index были чистыми. Общий `change/ui-birth-form-and-facts` проверен через `git ls-remote` в правильном репозитории и остаётся `6fc62b9`. Обновление не потребовалось. Исторический промт 05, требования и решения владельцев не редактировались.

### Реализованное поведение и границы

Причина отсутствовавшего сценария: DEV-UI-03 сохранял неопределённый исход и блокировал новый POST, но ещё не выполнял code-specific сверку и не обрабатывал возврат вкладки. Новый `recovery.mjs` задаёт политику по реально полученному outcome; `session.mjs` выполняет её существующим HTTP-клиентом.

- Потеря ответа POST сохраняет замороженный исходный intent и редактируемый draft; затем выполняется bootstrap → current. Если ответ получен частично, сохранены только реально прочитанные статус/заголовки; отсутствующие ErrorDTO, request ID и Retry-After не выдумываются. Совпадение birth подтверждает **текущую** карту из GET, без утверждения, что исходный POST завершил commit. Другая карта показывается как actual current с сохранением своего draft.
- Successful old/empty показывает точное предупреждение DP-UI-09 о возможном позднем завершении. «Построить ещё раз» отправляет новый POST только по отдельному действию при действующей ручной отметке; повторный ввод неизменённых данных не нужен. Если draft исправлен, новое действие создаёт отдельный snapshot исправленных данных. Первый intent остаётся неизменным во время своей сверки и виден отдельно от редактируемых полей.
- Failed bootstrap/current сохраняет последнюю подтверждённую карту и draft, блокирует build и предлагает безопасную проверку. Retry-After failed check ограничивает это действие; истечение срока само не запускает цикл повторов. Позитивный successful check снимает запрет, без автоматического POST.
- Received `503 STATE_COMMIT_FAILED` после своего Retry-After выполняет один `GET /charts/current`; только session 409 добавляет bounded bootstrap/current. Received `504 BUILD_TIMEOUT` сохраняет отдельную политику: после Retry-After пользователь подтверждает выполненный **внешний** restart кнопкой «Проверить после перезапуска», затем bootstrap/current проверяют доступность и current. UI не запускает restart, не вызывает внутренний health и не создаёт polling. Истечение таймера/возврат вкладки до подтверждения не разрешают POST или автоматическую проверку timeout.
- `visibilitychange` при visible и `online` запускают bootstrap/current, сохраняя draft. События во время операции объединяются в одну отложенную сверку после её завершения; read/build в одном coordinator не перекрываются. Dispose снимает эти подписки, abort текущего запроса и таймер; поздний ответ не публикуется. Это не обещание отмены серверного protected commit.
- Уже существующие session 409, `RESULT_SUPERSEDED` и `already_applied` переиспользованы. Два настоящих coordinator с общей листовой сетью проверяют текущую карту B в A, отдельные intents, same-origin credentials и отсутствие клиентского expected version/Cookie. Late first commit при concurrent second POST возвращается через superseded → GET как actual first current, без выдуманного second artifact.

Изменения ограничены девятью файлами: `ui/recovery.mjs`, `ui/session.mjs`, `ui/main.mjs`; `tests/ui/recovery.test.mjs`, `tests/ui/session.test.mjs`, `tests/ui/fixtures/session.mjs`, `tests/ui/fixtures/dom.mjs`; `tests/http_api/test_ui_delivery.py`; этот план. Общий fixture вынесен из session tests для reuse, прежний network assertion заменён полными recovery assertions, incomplete 200 проверяет successful safe current. Новый ресурс включён в существующий installed-wheel test; packaging не менялся. DTO/API/CAS/lifecycle, backend, вычисления, прокси, logging, зависимости и terms page сохранены.

### TDD и фактические проверки

Первый запуск `node --test --test-isolation=none tests/ui/recovery.test.mjs` дал **2 passed / 10 failed**, exit 1: модули/fixtures загружались, но coordinator не делал safe bootstrap/current после потери ответа, GET после Retry-After и отложенный foreground. Это behavioral RED. После реализации тот же набор дал **12 passed**, exit 0. Затем дополнены существующие coverage gaps двух вкладок, late commit и подключения UI, включая lost response с другим actual current и неизвестное время. Один промежуточный wiring assertion ошибочно ожидал русское имя места из каталога вместо `Moscow` из сохранённого BirthViewDTO; oracle исправлен на фактически выбранное имя до POST, продуктовые данные не менялись.

| Команда | Фактический результат |
|---|---|
| `node --test tests/ui/recovery.test.mjs tests/ui/session.test.mjs` | **56 passed**, exit 0; из них 24 recovery. Первый sandbox запуск не выполнил тесты из-за `spawn EPERM`, exit 1; точная команда повторена с разрешённым запуском вне sandbox. Ошибка среды не считается behavioral RED. |
| `node --test tests/ui/transport.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/session.test.mjs tests/ui/facts.test.mjs tests/ui/recovery.test.mjs` | **126 passed**, exit 0; полный UI-набор вне sandbox. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation tests/http_api/test_lifecycle.py::test_disconnect_during_protected_commit_is_visible_after_restart tests/http_api/test_build_admission.py -q` | **32 passed** за 1,82 s, exit 0. Existing real ASGI/SQLite/Orchestrator/admission/Event/save barrier/supervisor coverage переиспользовано без дублирования. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed** за 55,07 s, exit 0. Installed-wheel test вне checkout доставляет все 9 UI-ресурсов, включая импортируемый `recovery.mjs`. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed** за 402,09 s, exit 1; тот же `tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases`. |
| `git diff --check` | exit 0; только штатные сообщения Git о LF → CRLF. После финальной записи журнала проверка повторяется. |

Клиентские assertions связывают received `post-1` / `partial-post` с отдельными `current-2` / `check-A`, а second POST `second-post` — с GET `late-first-read`. Отсутствующий исходный ID остаётся null. Это controlled leaf evidence, не live request/run IDs. Серверные disconnect/admission tests проверяют настоящий before-commit cancel без SQLite mutation и protected commit, видимый после restart, а также существующие HTTP/application log pairs с request/run correlation. Sequence HTTP 003/004 и session/006 сохранены; новые серверные события и схемы не потребовались.

После связанных Python checks поставляемый код не менялся; во время полного прогона дополнены только Node assertions другого actual current/unknown time и журнал, затем точные целевая и полная Node-команды повторены с результатами 56/126 passed. Python-набор не повторялся: эти test-only изменения не входят в Python collection.

Полный regression gate остаётся **FAILED** на том же неизменённом property-тесте, что в DEV-UI-03/04. Контрпример снова содержит SEXTILE и TRINE на одной паре: при orb threshold 7 результат пустой, при 3 появляется один bisextile (`1 <= 0` ложно). В этом прогоне пары `(0,1)` и `(0,4)`, последний TRINE имеет orb 4. Product configurations и этот тест не редактировались; границы/допуски/golden не ослаблялись, skip/xfail не добавлялись. Это незакрытый риск полного regression gate; его устранение не входит в UI recovery.

### Ограничения и следующий шаг

Риск позднего первого commit остаётся принятым DP-UI-09; successful old/empty не доказывает завершение первой задачи, exactly-once не обещается. Runtime tests подтверждают client state/wiring и существующий server contract; настоящий browser cookie/две вкладки/DOM/keyboard/layout 360–1440 px и независимая Tester acceptance — **NOT VERIFIED**.

Известный FIND-TEST-HTTP-001 (`FORWARDED_HEADER_INVALID` у обычного localhost-клиента) остаётся вне scope промта 05. Сквозная ручная проверка штатного стенда по-прежнему **BLOCKED**. Прокси и процессы стенда этим шагом не менялись; новое live/browser evidence не заявляется. Исправление прокси требует отдельного поручения; доступные локальные поля/оформление не заменяют полный ручной build/recovery.

Следующий work item — DEV-UI-06; TEST-FIND-UI-004 manual retest остаётся pending. Текущая реализация — незакоммиченный рабочий diff поверх `6d970f6`, индекс не заполнялся; коммит/push/PR DEV-UI-05 не создавались. Исторические записи предыдущих разделов отражают состояние на момент своих проверок; DEV-UI-04 был опубликован отдельным поручением до начала этого шага. Manager G4 и Tester acceptance не заполняются от имени Developer.


## 18. Журнал исполнения DEV-UI-06 и handoff

**Дата:** 2026-10-07. **Основание:** прямое поручение пользователя «реализуй 6-й промт». **Ветка:** `dev/ui-birth-form-and-facts-review`. **Implementation commit:** отдельный commit DEV-UI-05/06 пока **не создан**; проверен рабочий diff поверх `6d970f605188ad1419cbae791e8e2f83d63d67c9`. Входные девять файлов DEV-UI-05 сохранены. `change/*` @ `6fc62b9`, требования/scenarios @ `ce25dd0`, решения DP @ `64934fc`, Manager G3 интегрирован; смысл approved contract не менялся.

**Developer Handoff status:** **BLOCKED для полного G4/browser acceptance**, пригоден для воспроизведения доступных частей. Эта запись не меняет Manager gate или Tester verdict. Шестой промт выполнен в доступной части, незавершённые браузерные критерии ниже указаны явно.

### Подход, результат и изменения

Использованы existing coverage → реальный browser/HTTPS integration → документальные проверки. TDD нового поведения не потребовался: в пределах UI scope новый implementation defect не установлен, исполняемый код и тесты этого шага не менялись. Known M1-6 forwarding и property configuration failure не исправлялись вне scope. Повторные regression-команды выполнены один раз как финальные обязательные checks промта 06; после них изменяются только текст/локальное evidence, лишних повторов нет.

В `docs/ui_ux/README.md` исправлен устаревший общий статус «не реализован»: документ различает черновой V2 и поставленные M1-7 форму/три группы, ссылается на approved change contract и этот handoff. Полный перенос прототипа, wheel illustration, имя, чат и demo values не добавлялись. Исторические промты, Analyst/Manager/Tester артефакты, requirements/ADR, source/API/DTO/CAS/lifecycle/numerics/logging и proxy config сохранены.

Локальные воспроизводимые evidence-скрипты/JSON/JPG находятся только в ignored `logs/ui-dev-06/`. Они не являются новым production service/test dependency. Ключи TLS и значения cookie не публикуются; HTTPS клиент проверяет mkcert CA, не отключает проверку сертификата. Девять UI-ресурсов через HTTPS побайтно совпали с текущим `src/exact_orb/http_api/ui/`; их SHA-256 записаны в `https-evidence.json`. Это fingerprint **working tree**, не ссылка на отсутствующий implemented commit.

### Реальная браузерная проверка

Использована уже открытая вкладка `https://exact-orb.localhost/` в Codex In-app Browser, tab 2. Свежий DOM содержит `submitted-intent` из DEV-UI-05; проверен существующий текущий mount. Ранее было ограничение навигации инструментом; в этом шаге чтение и управление существующей вкладкой оказались доступны. Обход browser safety/TLS interstitial, нового браузерного транспорта или подмена ответов не применялись. Второй доступный tab с ERR_CONNECTION_REFUSED не использовался как источник состояния текущей страницы.

| Проверка | Фактический результат / граница |
|---|---|
| REQ-UI-02; ручной Developer retest TEST-FIND-UI-004 | Настоящие последовательные клавиши `0045` в поле времени дали видимое `00:45`, caret=5. Соответствующий JPG сохранён. Независимый Tester retest/закрытие его реестра не выполнялись от имени роли. |
| Keyboard/focus, REQ-UI-10 / часть AS-UI-19 | Tab из времени перевёл фокус на `time-unknown`; Space включил unknown (`disabled:true`, `required:false`) и повторный Space вернул known (`disabled:false`, `required:true`) с тем же `00:45`. Следующий Tab перевёл фокус к checkbox условий. Outline focus-visible: 2px `rgb(240,205,115)`. |
| Labels/descriptions, часть AS-UI-19 | У всех пяти input есть label; `aria-describedby` ссылается на существующие hint/error/status. Общая ошибка — role alert, состояние поиска — status. Это DOM/browser checks, без утверждения о проверке screen reader. |
| 360 px | `innerWidth=360`, document client/scroll width=345/345, form width≈304,67. Поля, текст отметок и ошибка/кнопки читаемы; горизонтального overflow формы/страницы в проверенном состоянии нет. |
| 768 px | client/scroll width=753/753, form width=560, form right≈590,72. Form screenshot сохранён. |
| 1440 px | client/scroll width=1425/1425, form width=560, form right≈760,33. Form screenshot сохранён. |
| Композиция/палитра, часть REQ-UI-10 | Сопоставлены реальные форма/карточка, тёмный фон `rgb(8,7,6)`, золотой заголовок `rgb(240,205,115)`, порядок полей/ритм и focus с Р1/Э1. Полный прототип, demo badge/name/consent/CTA chat и иллюстрация wheel не являются обязательными элементами M1-7. Числа макетов не использованы как oracle. |
| Safe check на штатном URL | Кнопка «Повторить проверку карты» реально отправила bootstrap. Ответ `400 FORWARDED_HEADER_INVALID`, request ID `e252e734-08d3-48b9-a934-9e97b41571ce`; поиск также отклонён. Build остаётся disabled, fake place_id не вводился. |
| AS-UI-10/19/22/23 полностью | **BLOCKED / NOT VERIFIED**: cookie bootstrap, успешный выбор, browser build/reload, все длинные таблицы на трёх ширинах, keyboard details/disabled chat, browser disconnect/recovery и две успешные вкладки не пройдены. Негативное отсутствие POST без позитивного browser build не считается полным PASS этих AS. |

Использовался документированный viewport override, после проверок он снят: fresh DOM снова имеет innerWidth=609/clientWidth=594. Значение времени, временно введённое для теста, возвращено к исходному пустому; unknown и checkbox условий остаются в исходном false, текст места не менялся. Полностраничный capture оказался недоступен; сохранены viewport JPG. Первый мгновенный снимок после ввода отставал от свежего DOM; после сверки текущего состояния сохранён обновлённый кадр с видимым `00:45`. Неактуальный кадр не используется как доказательство.

### Реальный HTTPS positive control и наблюдаемость

Штатный source `127.0.0.1`: `POST /session/bootstrap` снова дал **400 FORWARDED_HEADER_INVALID**, request ID `f86094a4-49c3-4f64-bf29-f14b0e1b81db`. Это существующий FIND-TEST-HTTP-001, не новая UI-находка. Uvicorn listener `127.0.0.1:8000` — PID 21224, Caddy `127.0.0.1:443` — PID 16216; процессы/конфигурация не перезапускались и не менялись. Sandbox запретил `Get-NetTCPConnection`; та же проверка с разрешённым доступом подтвердила listeners.

Изолированный Node TLS-клиент с **исходным** адресом `127.0.0.2`, настоящими form/coordinator/transport и cookie jar выполнил bootstrap → empty current → `/places?query=Москва` → выбор ID 524901 из полученного каталога → explicit build → новое открытие/bootstrap/current. Для натала и космограммы использованы разные новые сессии, дата 1985-09-02 и известное 00:45 / явное null. До отметки в модели POST нет; double submit не создаёт второй POST; ровно один успешный build на kind. После чтения опубликованный DTO структурно совпадает со всеми committed фактами; новая модель формы starts unchecked. Это **API/TLS/controller evidence**, не native browser cookie или human UI gate acceptance.

| Kind | Actual committed identity / факты | POST run/request ID | Восстановленный current request ID |
|---|---|---|---|
| natal | `eo:calc:v2:f112dfae69d8d6daaf5051292bc21f78682940bb2df0fc7d7b1f027623f6b7e2`; 16 points / 12 houses / 46 aspects; state_version=1 | `6870e638-54ab-49d9-9301-3948f11f8636` | `26971e0f-616a-4d65-b71b-d49e9cabfdfe` |
| cosmogram | `eo:calc:v2:df21a4af0fdc460ed6d1aad6ddcec1680559ffa26cae7d134e2f44a68040f452`; 15 points / houses=null / 13 aspects; state_version=1 | `9686a553-4f46-4e4f-8fc7-01adf7de336b` | `234bd420-3fc0-4705-b251-61442eadf8de` |

`verify_sequence.py` сопоставил **13 business requests / 98 compact ordered events** с HTTP 001/002/003/004. Normal rejected bootstrap не имеет ложных service receive. На create — AdmissionControl.reserve → ContextService.create; на search — reserve → PlaceSearch.search; на current — ContextService.load → session_view без Orchestrator/engine; на build — reserve → Orchestrator.execute → release, application пары load → Handler → BirthDataResolver → artifact ensure/to_stored → Handler receive → save/Committed под `run_id=request_id`. Повторный bootstrap имеет только load. Secure/HttpOnly cookie выдаётся и сохраняется jar на положительном контроле. Инициатор восстановлен по logger: HTTP = exact_orb.http_api, application load/handle/save = exact_orb.application.orchestrator, resolution/artifact = exact_orb.application.handlers.build_natal; порядок источников дополнительно проверен скриптом. Серверный поток не менялся, поэтому диаграммы не переписывались; подробные payload в компактный evidence не добавлены.

### Фактические команды и результаты

| Команда | Результат |
|---|---|
| `node --test tests/ui/transport.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/session.test.mjs tests/ui/facts.test.mjs tests/ui/recovery.test.mjs` | **126 passed**, exit 0, 221,10 ms; финальный Node-прогон этого шага. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed**, exit 0, 25,29 s; installed wheel содержит девять UI-ресурсов и не зависит от checkout. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed**, exit 1, 125,77 s; тот же `tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases`. |
| `node logs/ui-dev-06/live_session_flow.mjs` | **PASS**, exit 0; 9 exact assets, 2 committed builds, одинаковые restored facts, standard 400 отдельно. |
| `python -B logs/ui-dev-06/verify_sequence.py` | **PASS**, exit 0; 13 requests / 98 ordered events, HTTP 001…004 matched, два correlated committed run IDs. |
| `git diff --check` | exit 0 после финальной записи журнала; только штатные предупреждения Git LF → CRLF. |

Чувствительные deterministic regression tests существующего поведения: `session.test.mjs` (gate/time issues/409/current/stale/unavailable), `facts.test.mjs` (all groups, null/[], AS-UI-22, full natal fixture), `recovery.test.mjs` (loss/commit/timeout/check failure/manual repeat/two tabs/late first/dispose). Серверный disconnect before/within protected commit и admission покрыты 32 target tests DEV-UI-05, входящие в связанную коллекцию здесь; в этом шаге их не дублировали новым seam. Реальные API positive traces не проверяют controlled browser disconnect.

### Воспроизведение и передача Tester

1. Checkout — этот worktree, указанная Developer-ветка и **весь текущий diff**, включая новые recovery/fixtures. HEAD `6d970f6` сам по себе не содержит DEV-UI-05. Передача на чистом implemented commit пока невозможна без отдельно порученного коммита; source SHA-256 для текущей проверки записаны в `logs/ui-dev-06/https-evidence.json`.
2. Setup — [локальный HTTPS runbook](../../runbooks/http_api_local_https.md), текущий Caddyfile и logging config. Один Uvicorn `create_local_app` на 127.0.0.1:8000, без reload/proxy-header rewrite, один Caddy; `data/places.sqlite`, `ephe`, отдельный session SQLite и существующий mkcert CA. В браузере открывать `https://exact-orb.localhost/`, не file:// и не сайт `127.0.0.2`. Новый процесс для этих проверок не нужен.
3. Для повторного API positive control выполнить `node logs/ui-dev-06/live_session_flow.mjs`, затем `python -B logs/ui-dev-06/verify_sequence.py`. Скрипт требует существующий `%LOCALAPPDATA%/mkcert/rootCA.pem`, рабочий стенд и native loopback binding; создаёт две собственные сессии и ровно два build. `127.0.0.2` — bind клиента, не обходным браузерным URL. Ignored скрипты/JSON/снимки доступны в текущем worktree, но не придут с Git pull; при чистой передаче сохранить их отдельно либо воспроизвести стандартные pytest/ручные сценарии.
4. Cookie-preserving Postman для **штатного** пути: установить `base_url=https://exact-orb.localhost`, оставить cookie jar включённым. `POST {{base_url}}/session/bootstrap` с JSON `{}`, Origin `https://exact-orb.localhost`, Content-Type `application/json`; сейчас воспроизводится 400 forwarding и дальнейший сценарий BLOCKED. После отдельного исправления M1-6 ожидать 200 и Secure/HttpOnly cookie в jar; затем `GET /places?query=Москва`, взять фактический `place_id` из items. Один явный `POST /charts/natal` с `{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"<выбранный ID>"}`, затем `GET /charts/current` с той же jar; сверить identity/все три группы. Для unknown — отдельный явный POST с `birth_time:null`, current должен иметь houses/angles/house_system null. Значение checkbox не входит в JSON; Postman не заменяет проверку presentation gate в UI. Прямой source bind positive control выше не является доступной опцией Postman-сценария. Целевая серверная команда для disconnect/admission — точная команда раздела 17, связанные проверки — таблица выше.
5. Browser после отдельного снятия FIND-TEST-HTTP-001: bootstrap → префикс/выбор → unchecked gate → один valid build → details → reload/current, затем unknown/stale/unavailable/issues и AS-UI-23/two tabs. На каждой 360/768/1440 px проверить **все** строки points/12 houses/aspects, keyboard details, disabled chat, field error/focus/loading. Не скрывать группы и не создавать fake place_id или выдуманный результат для mobile PASS. Точное implemented commit/setup/evidence зафиксировать отдельно Tester.
6. Чистовой перенос требований в `current/ui/birth-form-and-facts.md` и карта переноса остаются Analyst-owned; approved change links/IDs сохраняются. В этом пакете чистовой контракт не создаётся от имени Analyst, independent test plan/acceptance — не от имени Tester. Handoff подготовлен здесь; сообщение в другой чат не отправлялось без отдельной авторизации.

### Оставшиеся ограничения и gates

Сквозной штатный browser build/reload/details/recovery и длинные таблицы — **BLOCKED** известным FIND-TEST-HTTP-001. Локальные поля/ошибка/адаптивность формы проверены и имеют отдельный статус PARTIAL; эту часть нельзя выдавать за полный AS-UI-19 или G4. Live SQLite restart, controlled socket loss и timeout/restart в native browser в этом шаге не выполнялись; существующие controlled backend/controller tests остаются отдельным evidence.

Полный regression gate снова **FAILED** на неизменённом property-тесте конфигураций: тот же контрпример SEXTILE/TRINE для пар (0,1)/(0,4), orb последнего TRINE=4; threshold 7 дал 0 configurations, threshold 3 дал 1 bisextile. Код конфигураций и этот тест не менялись; допуски/golden, skip/xfail не подгонялись. Решение/исправление вне UI scope, отдельный незакрытый риск формального G4. DP-UI-09 accepted late-first risk, DEBT-UI-001/M1-9 и Analyst clean transfer сохраняются; бюджет/решения/формальная приёмка не менялись. Новых blocking UI implementation findings не установлено в доступной части.

Коммит/push/PR этого шага не создавались и index не заполнялся. Для полного завершения DEV-UI-06 требуются снятие forwarding ограничения отдельным изменением, browser criteria с позитивным valid build и ясный regression gate, затем implemented commit и independent Tester handoff/acceptance. Статус остаётся PARTIAL / BLOCKED, без фиктивного COMPLETE/G4/G5.

<a id="debt-calc-001"></a>
## 19. DEBT-CALC-001 — монотонность теста и топология бисекстиля

**Дата:** 2026-10-07. **Автор evidence:** Developer. **Статус:** OPEN; исправление отдельной задачей расчётного слоя, срок и milestone не назначены.
**Основание регистрации:** прямое поручение владельца «Создавай техдолг» после диагностики одного красного теста.
**Единая запись долга и ownership:** [реестр, DEBT-CALC-001](../change_plans/ui-birth-form-and-facts/artifacts.md#technical-debt). Первоначальная регистрация не разрешала исключить тест из обязательных проверок. Последующее отдельное поручение владельца разрешает точечный skip, см. [раздел 24](#debt-calc-001-test-skip); G4/G5 этим не объявляются PASS.
**Baseline:** ветка `dev/ui-birth-form-and-facts-review`, HEAD `6d970f605188ad1419cbae791e8e2f83d63d67c9`; поверх него остаётся локальный пакет DEV-UI-05/06. `git diff ef75d77 -- tests/test_configurations.py src/exact_orb/engine/configurations src/exact_orb/engine/aspects` пуст: эти файлы не менялись в последующих UI заданиях.

### Причина и границы

В [генераторе `_aspect_lists()`](../../../tests/test_configurations.py) нет ограничения на разные типы аспектов между одной неориентированной парой точек. Поэтому property-тест монотонности использует и входы, не соответствующие Т-АСП-3: штатный aspect finder выбирает один аспект на пару. Для проверки этого свойства нужен отдельный генератор допустимых наборов; произвольные входы остальных тестов не следует молча ограничивать вместе с ним. Дубли одного типа, разрешённые Т-КНФ-3, должны сохранять отдельное покрытие.

В [bisextile finder](../../../src/exact_orb/engine/configurations/patterns/bisextile.py) проверяется число секстилей и тригонов, но не проверяется, что найденный тригон замыкает два крыла. На приведённом противоречивом входе он создаёт фигуру с повтором пары «центр — крыло» и отсутствующей парой «крыло — крыло». Это не соответствует Т-КНФ-4/11; существующая aggregate integrity-проверка такую фигуру отклоняет. Одного ограничения генератора недостаточно для закрытия этой части долга.

Источники контракта: [Т-АСП-3, Т-КНФ-3/4/11](../../requirements/component_responsibilities/exact-orb_calculation_requirements.md), [ADR-0031](../../requirements/decisions/0031-materialized-configuration-integrity.md). Изменение требований, ADR, схем, версий или числовых reference-результатов для устранения долга не предлагается. Этот контрпример не доказывает ошибку на корректной карте штатного натального пути.

### Контрпример и воспроизведение

Все точки принадлежат `natal`; объекты собраны существующим test helper `_make_aspect()`:

| Пара точек | Тип | Orb |
|---|---|---|
| `p0`, `p1` | SEXTILE | 0 |
| `p0`, `p1` | TRINE | 0 |
| `p0`, `p4` | SEXTILE | 0 |
| `p0`, `p4` | TRINE | 4 |

При `include_nested=True`, `points=None` порог 7 даёт 0 фигур, порог 3 — 1 бисекстиль; assertion `len(low) <= len(high)` падает. Роли результата: `center=p0`, `wing_1=p1`, `wing_2=p4`. Его тригон — `p0–p1`, а ребро `p1–p4` отсутствует.

Команда диагностики перед регистрацией:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases -q
```

**Фактический результат:** exit 1, **1 failed in 0.59s**, `assert 1 <= 0`, приведённый Hypothesis-контрпример. Повтор на чистом checkout без сохранённой базы Hypothesis не гарантирует выбор именно этих случайных входов; для фиксированного контрпримера выполнить из корня:

```powershell
@'
from tests.test_configurations import _make_aspect
from exact_orb.engine.aspects import AspectType
from exact_orb.engine.configurations import find_configurations, ConfigurationConfig
from exact_orb.engine.configurations.integrity import validate_configuration_tree

aspects = [
    _make_aspect((0, 1), AspectType.SEXTILE, 0.0),
    _make_aspect((0, 1), AspectType.TRINE, 0.0),
    _make_aspect((0, 4), AspectType.SEXTILE, 0.0),
    _make_aspect((0, 4), AspectType.TRINE, 4.0),
]
high = find_configurations(aspects, ConfigurationConfig(
    configuration_max_orb=7.0, include_nested=True, points=None))
low = find_configurations(aspects, ConfigurationConfig(
    configuration_max_orb=3.0, include_nested=True, points=None))
print("high/low:", len(high), len(low))
validate_configuration_tree(low[0], aspects, "configurations[0]")
'@ | python -B -
```

Выполненная до регистрации детерминированная диагностика этих данных дала **0/1** и `configurations[0].aspects[1] duplicates a participant pair`. Скрипт выше намеренно оставляет это исключение видимым; после исправления его следует заменить regression-тестом ожидаемого корректного поведения. Последний полный прогон DEV-UI-06 — **2959 passed / 1 failed**, см. раздел 18; при регистрации документа полный pytest повторно не запускался.

### Рекомендованный объём отдельной задачи и закрытие

1. Сначала закрепить фиксированный контрпример regression-тестом топологии и позитивным контролем настоящего бисекстиля с тригоном между крыльями; сопоставить с существующими integrity/reference-тестами, не дублируя их.
2. В property-тесте монотонности использовать допустимые наборы с одним типом аспекта на неориентированную пару. Не ослаблять assertion и не удалять отдельные проверки обработки дублей одного типа по Т-КНФ-3.
3. Исправить проверку замыкающего тригона на ответственном слое finder. Сохранить корректные фигуры, категории, публичные DTO, reference/golden и допуски.
4. Последовательно выполнить целевые, связанные и полные проверки и сохранить результаты на точном implementation commit:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_configurations.py -q
python -B -m pytest -p no:cacheprovider tests/test_aspects.py tests/test_natal_include_gating.py tests/test_chart_artifact_codec.py tests/test_module_boundaries.py -q
python -B -m pytest -p no:cacheprovider -q
```

Эти команды закрытия **запланированы**, а не выполнены при регистрации. Долг закрывается после исправления обеих причин, прохождения проверок и независимой сверки Tester; статус/приоритет контролирует Manager. До этого полный regression gate остаётся **FAILED**, независимая UI работа может продолжаться в согласованном scope. Реализация долга, обход gate и commit/push/PR этим поручением не запрашивались.

<a id="local-proxy-fix"></a>
## 20. Исправление локального прокси и перезапуск стенда

**Дата:** 2026-10-07. **Основание:** поручение владельца «внеси изменения и перезапусти стенд» к ранее предложенному исправлению прокси. **Developer status:** IMPLEMENTED / LOCAL HTTPS AND BROWSER FLOW VERIFIED. Это отдельная поставка исправления FIND-TEST-HTTP-001, не исправление DEBT-CALC-001 и не независимая Tester acceptance.
**Baseline:** HEAD `6d970f605188ad1419cbae791e8e2f83d63d67c9`, ветка `dev/ui-birth-form-and-facts-review`, с сохранёнными локальными изменениями DEV-UI-05/06 и карточкой долга. Коммит, push и PR не создавались.

### Причина, объём и подход

Обычный TLS-клиент и raw ASGI peer Caddy раньше имели один адрес `127.0.0.1`, включённый в trusted allowlist. Проверка по HTTP §10 отбрасывала оба trusted звена, не находила клиента и возвращала 400. Исправлен локальный composition: Caddy подключается к Uvicorn с `local_address 127.0.0.2`, приложение доверяет только `127.0.0.2/32`; браузерный клиент `127.0.0.1` остаётся untrusted client hop. URL `https://exact-orb.localhost/`, внешний bind `127.0.0.1:443`, upstream `127.0.0.1:8000` и `--no-proxy-headers` сохранены.

Изменены [local factory](../../../src/exact_orb/http_server.py), [Caddyfile](../../runbooks/http_api_local.Caddyfile), [HTTPS runbook](../../runbooks/http_api_local_https.md) и [существующий integration test](../../../tests/http_api/test_integration.py). Актуальный browser status уточнён в [UI/UX README](../../ui_ux/README.md). Общий `proxy.py`, HTTP §10, DTO, API, диаграммы HTTP 001–004 и вычислительное поведение не менялись: межкомпонентный поток остался прежним.

Подход — **тест → настройка → проверки**. Расширен существующий тест local factory/catalog; отдельный дублирующий тест не создавался. Он использует реальную factory и boundary, заменяет только листовые catalog/runtime, проверяет browser XFF `127.0.0.1` при raw peer `127.0.0.2` и негативные цепочки `127.0.0.2` / `bad-hostname`. Позитивный запрос достигает каталога, отрицательные дают 400 до его вызова. RED получен на старой настройке: доверенный peer ошибочно считался direct, отрицательный запрос дал 200 вместо 400. После смены allowlist все условия прошли; проверка заголовков не ослаблена.

### Перезапуск и фактические проверки

До остановки сохранены журнал и согласованная SQLite backup в ignored `logs/local-proxy-fix/`; исходная база `logs/ui-dev-02/sessions.sqlite3` продолжает использоваться. Старый Uvicorn PID **21224** остановлен, прежний listener проверен до запуска нового. Новый единственный Uvicorn PID **27492**, Caddy PID **16216** применил конфигурацию через reload. Проверены активная конфигурация Caddy с `local_address=127.0.0.2`, listener `127.0.0.1:8000` и внутренний `/health/ready` — **200**. Сертификат mkcert/CA не заменялся, TLS verification не отключалась.

| Команда / проверка | Фактический результат |
|---|---|
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_integration.py::test_local_factory_passes_one_open_catalog_to_runtime_and_route -q` | До настройки **1 failed in 0.72s**, ожидаемый RED; после настройки **1 passed in 0.47s**, exit 0. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 39.81s**, exit 0 вне sandbox. Первый запуск: 345 passed / 1 failed, 65.55s, из-за запрета pip записи в Temp build tracker; та же команда повторена с необходимым доступом. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 303.51s**, exit 1. Единственное падение — прежний property-тест из DEBT-CALC-001 с тем же контрпримером; полный gate остаётся FAILED. |
| `caddy validate --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile` | **Valid configuration**, exit 0, Caddy **2.11.6**, существующие cert/key. |
| `& ./logs/local-proxy-fix/restart.ps1` | Exit 0: backup, остановка старого web process, запуск нового с прежней БД; `caddy reload --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile` прошёл. Скрипт сохраняет PID и останавливает только проверенный исходный процесс; он одноразовый и не предназначен для повторного запуска с устаревшим PID. |
| `node logs/local-proxy-fix/live_session_flow.mjs` | **PASS**, exit 0. Обычный source `127.0.0.1`, bootstrap 200, 9 assets побайтово совпали; две собственные cookie jar, по одному явному natal/cosmogram POST и равенство current после повторного bootstrap. |
| `python -B logs/local-proxy-fix/verify_sequence.py` | **PASS**, exit 0: 13 business requests, 102 компактных упорядоченных событий; HTTP 001–004 и инициаторы application transitions совпали, два build завершились Committed. |

HTTPS positive control теперь использует **обычный адрес клиента `127.0.0.1`**. Старые source-`127.0.0.2` helpers и журналы DEV-UI-01…06 сохранены как исторические; с новой topology они не являются текущей инструкцией проверки. Стандартный bootstrap request ID — `f7414727-51e3-4361-8379-8c7f2093563f`. Natal POST — `6d69c15e-4539-41fb-9f69-143abe640643`, restored current — `45c914a0-b251-45d5-8602-dbbfb6af28ed`; cosmogram POST — `f8dd5ac6-581d-49c8-8162-ddb4da7e0554`, current — `5149f89d-5da5-4c7b-b95f-4b1c38654e3a`. Identity, версии и опубликованные факты совпали с предыдущими корректными positive controls.

### Браузер и границы evidence

В отдельной вкладке обычного in-app browser выполнены: bootstrap/current → дата `1985-09-02`, ввод времени `0045` с видимым `00:45` → поиск Москвы → выбор RU/Москва из настоящего каталога → попытка без отметки (видимая ошибка gate) → ручная отметка → явный build → «Натальная карта готова» → details → reload/current → details. На странице показаны 16 точек, 12 домов, 5 углов и 46 аспектов; полный текст всех четырёх таблиц до/после reload совпал. Checkbox после reload снова снят; чат disabled. Данные для проверки синтетические, существующая пользовательская форма во вкладках не редактировалась.

Снимок `logs/local-proxy-fix/browser-ready.png` и `browser-evidence.json` сохранены вместе с HTTPS manifest, request IDs и `sequence-events.log`. Эти файлы ignored: они доступны локально и не придут с Git pull. Стенд оставлен работающим; URL прежний. Для повторной ручной проверки использовать браузер или cookie-preserving Postman из обновлённого runbook, без source bind клиента к `127.0.0.2`.

Это подтверждает исправление обычного localhost flow в текущем worktree. Browser cosmogram, все recovery/error/two-tab сценарии, повторная адаптивность длинных таблиц и независимая Tester acceptance в этой задаче не проверялись. Статус Tester FIND-TEST-HTTP-001 и финальные G4/G5 не закрывались от имени другой роли. DEBT-CALC-001 остаётся OPEN, полный pytest FAILED; расчётный тест не отключён. После проверок исполняемые файлы не менялись — дополнена только документация.

<a id="external-model-bugs"></a>
## 21. Исправления по ревью другой модели

**Дата / комментарий:** 2026-10-07; **найдено другой моделью**. Владелец передал 16 замечаний, согласовал регистрацию принятых дефектов и подготовку одного или двух промтов. Подготовлены два; затем отдельными поручениями исполнены DEV-UI-07 (раздел 22) и DEV-UI-08 (раздел 23). Постановки промтов сохранены как исторические; перезапуск стенда в этих задачах исполнения не поручен.
**Baseline:** `0d5d70acfc4f1f384b2c06970b35111b411c4fc4`, `dev/ui-birth-form-and-facts-review`, входное дерево/index чистые. Это baseline ревью и будущих исправлений; исходные baselines DEV-UI-01…06 сохраняются.
**Единый источник дефектов:** [реестр TEST-FIND-UI-005…012](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#external-model-review). Оценки severity/priority предложены Developer; независимый retest и окончательная severity принадлежат Tester, priority/delivery — Manager.
**Requirements/decisions:** нормативные источники раздела 1 @ `652bd734`; семантика approved REQ-UI-01…10 / AS-UI-01…23 @ `ce25dd0`; текущие документы и реестр DP-UI-01…09 прочитаны @ `0d5d70a`. Применимы DP-UI-01/03/05/09, ADR-0034/0039/0040/0041. Продуктовые требования, Gantt и принятые строки DP не переписываются; новые API/решения не вводятся этим дополнением.
**Technical assessment:** FEASIBLE, средняя уверенность. Исправления используют текущий same-origin UI, существующие DTO и coordinator.

### Состав и диспозиция

| Баг / исходное замечание | Work item | Граница исправления |
|---|---|---|
| [TEST-FIND-UI-005](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-005) / №1 | DEV-UI-07 | Допустить регион null в корректной подсказке, сохранить политику повреждённой выдачи. |
| [TEST-FIND-UI-006](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-006) / №2 | DEV-UI-08 | Сверять неизвестный исход 5xx до нового ручного POST; сохранить известные code-specific policies. |
| [TEST-FIND-UI-007](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-007) / №3 | DEV-UI-08 | Устаревший current не подтверждает свежий результат; одинаковый ID свежей карты допустим. |
| [TEST-FIND-UI-008](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-008) / №4 | DEV-UI-08 | Объяснить восстановление сессии и необходимость нового явного действия. |
| [TEST-FIND-UI-009](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-009) / №5 | DEV-UI-07 | Явный no-cache для модулей/CSS с сохранением conditional delivery. |
| [TEST-FIND-UI-010](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-010) / №6 | DEV-UI-08 | Сводка успешного intent отдельно от редактируемого черновика, без выдуманного полного birth DTO. |
| [TEST-FIND-UI-011](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-011) / №13 | DEV-UI-07 | Проверка читаемого DTO до accept/render; видимая ошибка и safe recovery для повреждённого POST. |
| [TEST-FIND-UI-012](../../testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-012) / №14 | DEV-UI-08 | Сохранить подпись восстановленного места при focus/blur, снять ID только при редактировании. |

### Дополнительная оценка Developer

| Work item | Человеко-часы | Уверенность |
|---|---:|---|
| DEV-UI-07 — поиск, ресурсы и проверка ответов | 6–10 | Средняя: границы DTO и installed-wheel checks требуют регрессии. |
| DEV-UI-08 — recovery и обратная связь | 6–10 | Средняя: сочетания stale/5xx/session-loss/draft требуют controlled scenarios. |
| **Итого дополнение** | **12–20 часов / 1,5–2,5 рабочих дня по 8 часов** | Предварительная оценка, не фактическая стоимость. |

Оценка относится только к восьми новым багам и Developer checks. Исходные 40–64 часа/5–8 дней не заменены; влияние на delivery/budget оценивает Manager. Предполагаются доступные Node/Python, исправный локальный HTTPS и переиспользование fixtures. Независимая Tester acceptance, DEBT-CALC-001, клиентский таймаут, новые ID точек, H:MM, CSP/nosniff и refactoring вне этих дефектов исключены. Главная неопределённость — достаточная проверка повреждённых DTO и browser cache/recovery evidence.

<a id="dev-ui-07"></a>
### DEV-UI-07. Допустимые места и проверенные UI-ответы

- **Комментарий:** найдено другой моделью; TEST-FIND-UI-005/009/011, замечания №1/5/13. **Статус:** IMPLEMENTED / BROWSER RETEST PENDING; три findings FIXED PENDING RETEST, целевые/связанные checks PASS, full FAILED по прежнему DEBT-CALC-001; [фактическое исполнение](#dev-ui-07-execution). Исторический промт сохраняет исходную постановку.
- **Промт:** [07-place-assets-and-response-guards.md](../../../prompts/2026-10-07/ui-birth-form-and-facts/07-place-assets-and-response-guards.md).
- **Требования/scenarios:** REQ-UI-01/02/03/08/09/10; AS-UI-01/02/03/04/10/15/17/18/19/23; DP-UI-01/03/09. Источники и версии — baseline этого раздела.
- **Подход:** тесты → реализация в одном промте. Доказанные nullable/invalid-body расхождения и непроверенные static headers дают чувствительные regression tests до правки.
- **Components/files:** `ui/places.mjs`, `session.mjs`, `main.mjs`, `facts.mjs` и при необходимости один небольшой чистый UI-валидатор; `http_api/app.py` только доставка static headers; `tests/ui/{places,session,recovery,transport,facts}.test.mjs`, общие fixtures, `tests/http_api/test_ui_delivery.py`. DTO/backend calculations не меняются.
- **Существующее покрытие / пробелы:** places tests проверяют обычные строки/выбор; delivery tests проверяют HTML no-store и wheel assets; session тест на неполный 200 не проверяет `points:null`. Добавить nullable mixed list/выбор, headers 200/304, mounted malformed POST/current с сохранением подтверждённого view и видимой ошибкой; позитивные natal/cosmogram.
- **Behavior:** регион null отображается прочерком; модули/CSS требуют revalidation; некорректный DTO не доходит до renderer и не подтверждается как результат build. Для повреждённого 200 POST используется существующая unconfirmed-response recovery без auto POST.
- **Наблюдаемость:** сохраняются status/body/request IDs, запросы сверки имеют отдельную корреляцию; серверные logging/sequence contracts не меняются. Сверить bootstrap/current/build и place-search с HTTP sequences 001–004.
- **Dependencies / completion:** текущая реализация DEV-UI-01…05; DEV-UI-06 остаётся PARTIAL. Матрица и точные команды — в промте. После чувствительного RED и успешных target/related checks записать Developer evidence и FIXED PENDING RETEST; browser cache/recovery и независимую приёмку не объявлять выполненными без запуска.

<a id="dev-ui-08"></a>
### DEV-UI-08. Сверка неизвестного результата и понятные сообщения

- **Комментарий:** найдено другой моделью; TEST-FIND-UI-006/007/008/010/012, замечания №2/3/4/6/14. **Статус:** IMPLEMENTED / BROWSER RETEST PENDING, пять findings FIXED PENDING RETEST; historical постановка PREPARED, фактическое evidence — [раздел 23](#dev-ui-08-execution).
- **Промт:** [08-recovery-and-result-feedback.md](../../../prompts/2026-10-07/ui-birth-form-and-facts/08-recovery-and-result-feedback.md).
- **Требования/scenarios:** REQ-UI-02/03/08/09/10; AS-UI-02/03/04/10/11/12/13/14/16/19/22/23; DP-UI-03/05/09; ADR-0034/0040/0041.
- **Подход:** тесты → реализация. Сначала воспроизвести incorrect 5xx allowance, stale matched и три UI-feedback случая; tests должны показывать наблюдаемое поведение и порядок calls, не приватный алгоритм.
- **Components/files:** `ui/recovery.mjs`, `session.mjs`, `main.mjs`, минимально `places.mjs`/`facts.mjs` если нужны для связанного presentation; `tests/ui/{recovery,session,places,facts,transport}.test.mjs` и существующие fixtures. HTTP DTO/cookies/admission/commit/key/version не меняются.
- **Существующее покрытие / пробелы:** существующий 502 case разрешает повторный POST; relation tests не покрывают stale; session-loss tests не проверяют объяснение; mounted restore не проверяет подпись после focus/blur. Добавить cases из матрицы промта, переиспользовать текущие fakeClock/deferred/DOM и golden.
- **Behavior:** неизвестный 5xx и INTERNAL_FAILURE требуют safe check; stale не подтверждает свежий build, fresh same-identity допускается; восстановление сессии объясняется; сводка карты читает снимок успешного запроса или серверный birth из current; подпись восстановленного места переживает focus/blur.
- **Наблюдаемость:** порядок POST → bootstrap/current либо code-specific GET и отдельные request IDs проверяются calls/diagnostics; авто POST нет; поздний ответ/dispose не публикуют ложный результат. HTTP sequences 001/003/004 и действующие lifecycle события сохраняются.
- **Dependencies / completion:** выполнить после DEV-UI-07, проверить его actual diff/guard behavior и оставить баги pending retest. Повторить target/related/full checks по промту и ручные сценарии; raw 504 не выдавать за BUILD_TIMEOUT, внутреннюю стадию 500 не угадывать.

### Порядок, возвраты и статус подготовки

Порядок дополнения: DEV-UI-07 → DEV-UI-08 → Developer handoff → независимый Tester retest. Пересечение session/main и проверки malformed response требуют последовательного исполнения. Подготовка этих промтов не запускает их и не закрывает TEST-FIND-UI-*.

При противоречии approved REQ/AS или необходимости нового публичного исхода остановить только зависимую часть и вернуть семантику Analyst; scope/budget — Manager, architecture — Technical Reviewer. Пункт о консервативной сверке INTERNAL_FAILURE явно записан в промте, скрытая серверная стадия UI недоступна. Изменение расчётного поведения/DEBT-CALC-001 не входит в этот пакет.

Фактические результаты прежнего ревью сохранены в bug registry: 126 UI tests passed, контролируемые воспроизведения и два live GET. Они не являются RED/GREEN будущих regression tests. Проверки текущей документальной подготовки и фактическое исполнение дополнения записываются ниже отдельными записями; G4/G5 и FAILED full regression из раздела 20 сохраняют свой статус.

### Документальная подготовка — 2026-10-07

**Результат:** восемь findings OPEN зарегистрированы с происхождением «найдено другой моделью» и уточнённой диспозицией; два новых промта 07/08 подготовлены и связаны с карточками. Изменены только настоящий Implementation Plan, bug registry и два новых Markdown-файла промтов.

- Read-only проверка через `python -B -X utf8 -c` (inline validator в текущем чате): **PASS**, exit 0 — 53 локальные ссылки/якоря, парность Markdown fences, восемь уникальных findings, соответствие source/work item и два статуса PREPARED / NOT EXECUTED. Проверены новые разделы плана/реестра и оба новых промта; прежние разделы не переписывались.
- `git diff --check`: **PASS**, exit 0.
- Runtime/browser regression исправлений при подготовке документов: **NOT RUN**; исполняемые файлы и исторические промты 01…06 сохранены. Коммиты, push и перезапуск не выполнялись.

На момент завершения подготовки DEV-UI-07/08 оставались PLANNED / NOT STARTED, G4/G5 и Tester acceptance не изменялись. Последующее исполнение 07 описано отдельно ниже.

<a id="dev-ui-07-execution"></a>
## 22. Журнал исполнения DEV-UI-07 и handoff

**Дата:** 2026-10-07. **Основание:** прямое поручение владельца «Реализуй промт 7». **Developer status:** IMPLEMENTED / BROWSER RETEST PENDING. TEST-FIND-UI-005/009/011 — FIXED PENDING RETEST; независимая Tester acceptance и G4/G5 не заявлены.
**Фактический baseline:** `a2445e4494c1c8ca4e4d22f20a8a761969afa633`, dev/ui-birth-form-and-facts-review, входные дерево/index чистые. Отличие от baseline промта 0d5d70a — только четыре Markdown-файла регистрации/постановок; REQ/AS/DP и исполняемый код не менялись. Исполнение ведётся незакоммиченным diff, index не изменён.

### Корневые причины и исправления

1. **005:** UI требовал строку региона, хотя публичный PlaceSuggestionDTO допускает null. В places.mjs nullable регион теперь валиден; остальные поля и прежний отказ при повреждённой выдаче сохранены. Подсказка/выбранное место показывают «—», а явный build отправляет выбранный ID.
2. **009:** обычный StaticFiles оставлял ресурсы с постоянными URL без Cache-Control. Private `_UiStaticFiles` задаёт no-cache для модулей/CSS, включая 304. HTML/API no-store, MIME/ETag/Last-Modified, HEAD и безопасные 404/405 сохранены; новые middleware/business events не добавлены.
3. **011:** проверка только kind/identity пропускала коллекции/поля, которые renderer не может прочитать. Чистый `ui/response.mjs` проверяет build/current/bootstrap и читаемые поля ErrorDTO/IssueDTO до accept/render, без пересчёта/исправления данных. Входной current не заменяет подтверждённую карту при отказе; повреждённый POST 200 сохраняет existing unconfirmed-response → bootstrap/current и запрещает новый build при failed check.
4. Для неожиданного сбоя renderer coordinator фиксирует видимую ошибку, закрывает операцию из busy и оставляет только safe recheck через простой fallback существующих DOM-узлов. Ошибка не превращается в successful return; pending foreground не продолжает цикл после failed rendering. Cache renderer фиксируется после успешной отрисовки, поэтому safe retry не пропускает восстановление таблиц. Known BUILD_TIMEOUT сохраняет Retry-After и явное restart confirmation.

Затронуты app.py (только headers), UI places/session/main/facts и новый response.mjs, три test-файла и общий session fixture, настоящий план и три записи bug registry. Package-data wildcard уже включает *.mjs; pyproject.toml, HTTP DTO/routes/transport, engine/calculation/cache/commit, требования/ADR/server sequences не менялись. Значения расчёта и HH:MM/null сохраняются. Неподтверждённые 5xx, stale classification и feedback из DEV-UI-08 не исправлялись этим work item.

### Подход и воспроизводимая регрессия

**Тесты → реализация.** Подготовительный leaf seam: main передаёт уже существующий clock в createPlaceSearch для mounted debounce без реального ожидания; это не исправляло nullable-region bug.

- Node RED: **106 passed / 20 failed**, exit 1. Существующие tests не падали; новые assertions дошли до поиска/accept/render и воспроизвели nullable rejection, неправильно принятые/падающие ChartDTO и renderer rejection. Лог: `logs/ui-dev-07/node-red.log`.
- Python RED: **4 passed / 2 failed / 1 deselected**, exit 1; выбранный набор без wheel воспроизвёл отсутствие no-cache на GET/HEAD, а не ошибку setup. Лог: `logs/ui-dev-07/python-red.log`.
- Первоначальный target Python после исправления: 6 passed / 1 failed из-за PermissionError записи pip build tracker в Windows sandbox, не assertion поведения. Сохранён `python-target-sandbox.log`; та же pytest-команда повторена с необходимым доступом, **7 passed**, включая installed wheel вне checkout.
- Добавлены **23** UI regression/positive-control cases поверх прежних 126. Проверены mixed null/string suggestions, ручной gate/выбранный ID, 11 повреждённых POST, 4 повреждённых current, bootstrap/issues, renderer failure open/foreground/submit, повторная отрисовка и timeout/restart policy. Existing golden natal/cosmogram, formatter/unknown time, late response/dispose, no-auto-POST и two-tab tests сохранены.

### Фактические команды и результаты

Все команды выполнены из указанного worktree; Node v24.19.0, Python 3.14, Starlette 0.49.3. Логи текущего исполнения находятся в ignored `logs/ui-dev-07/`.
SHA-256 десяти проверенных source/test-файлов сохранены в `logs/ui-dev-07/fingerprint.json`; после runtime-проверок изменялись только этот план и bug registry. Документальная проверка новых ссылок/якорей/fences дала **57 links PASS**, exit 0; index остаётся пустым.

| Команда | Фактический результат |
|---|---|
| `node --test --test-isolation=none tests/ui/places.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/facts.test.mjs tests/ui/transport.test.mjs` | RED 106 passed / 20 failed; после основного исправления target GREEN **126 passed**, exit 0. Последующий positive timeout case проверен в полном Node-наборе. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -k 'not installed_wheel' -q` | RED **4 passed / 2 failed / 1 deselected**, exit 1. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -q` | После повторения вне sandbox **7 passed in 12.31s**, exit 0; 10 UI-ресурсов из installed wheel, включая response.mjs, headers 200/304 и MIME/HTML/API controls. |
| `node --test --test-isolation=none tests/ui/*.test.mjs` | **149 passed / 0 failed**, exit 0, 186.38 ms. |
| `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed in 54.36s**, exit 0. |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 122.92s**, exit 1; только прежний `test_property_configuration_count_does_not_grow_when_threshold_decreases`, DEBT-CALC-001, тот же контрпример двойных sextile/trine пар. |
| `git diff --check` | PASS, exit 0. |

### Наблюдаемость и границы handoff

Mounted tests собирают настоящие form/session/transport/renderer с листовыми network/DOM/clock. Calls подтверждают POST → bootstrap → current для повреждённого 200, отдельные original/check request IDs, failed-check block и успешный safe retry без auto POST. Same-origin credentials/cache options и published facts проверяют existing controls. HTTP integration/packaging tests подтверждают прежние серверные lifecycle/request events; assets не создают business-request events и не вызывают calculation. Server sequences 001–004 и logging contract сохранены; нового server flow нет.

**Browser retest:** NOT RUN на исправленной версии; работающий HTTPS стенд не перезапускался. Новая Python-настройка static headers требует обновления процесса перед проверкой браузера. После отдельно разрешённого обновления проверить «Гонк»/«—»/ручной выбор, ordinary-cache reload/revalidation, valid natal/cosmogram и controlled malformed recovery. Node DOM-port/ASGI/wheel не подменяют браузер или Tester.
**Оставшиеся gates:** DEBT-CALC-001 OPEN, полный pytest FAILED; G4/G5 и acceptance не закрыты. Расчётный тест не отключён и не изменён. Пять findings DEV-UI-08 OPEN, реализация 08 NOT STARTED.
**Дальше:** DEV-UI-08 получает текущий actual diff 07 и response guards; перед самостоятельной передачей сохранить проверяемую версию и ignored evidence или повторить команды. Commit/push/PR, публикация и перезапуск в этом поручении не выполнялись; historical prompts 01…08 сохранены.

<a id="dev-ui-08-execution"></a>
## 23. Журнал исполнения DEV-UI-08 и handoff

**Дата / Owner:** 2026-10-07, Developer. **Комментарий:** найдено другой моделью.
**Поручение:** «Выполни 8 промт». **Baseline исполнения:** `25e3e0fa9ce1a4ebdd50d70df72bbe771e065423`, `dev/ui-birth-form-and-facts-review`, checkout `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`; дерево и index были чистыми. DEV-UI-07 поставлен именно этим коммитом; guards malformed DTO/renderer, no-cache и nullable-region включены и проверены повторно.
**Контракт:** исходные нормы HTTP/session/stored-chart/catalog @ `652bd73405db0a0611e98e81af6f3f668dd429f6`, approved REQ-UI-02/03/08/09/10 и AS-UI-02/03/04/10/11/12/13/14/16/19/22/23 @ `ce25dd0`; применимые DP-UI-03/05/09 в реестре, прочитанном при подготовке @ `0d5d70a`, повторно сверены с текущей редакцией. Исходный выбор B @ `64934fc` сохраняется; ADR-0034/0040/0041 и server sequences 001/003/004 не менялись.
**Developer completion:** IMPLEMENTED / BROWSER RETEST PENDING. TEST-FIND-UI-006/007/008/010/012 — FIXED PENDING RETEST. Общие G4/G5, независимая приёмка и DEBT-CALC-001 не закрыты. Изменения исполнения 08 пока локальные, новый implementation commit отсутствует.

### Причины и фактическое поведение

1. Recovery распознавал только network/commit-failure/timeout/неполный 200 и пропускал неизвестные 5xx. Теперь нераспознаваемые или повреждённые ErrorDTO при 5xx и все публичные `500 INTERNAL_FAILURE` считаются неподтверждённым исходом: до успешного bootstrap/current новый POST недоступен. Учитывается только полученный Retry-After; failed check сохраняет draft/подтверждённую карту и предлагает safe recheck. Old/empty сохраняет late-commit warning и требует отдельный gated click. Matching current описывает фактическую карту, не доказывает завершение конкретной попытки. Cookie и скрытая стадия сервера не используются как доказательство.
2. Known ErrorDTO `503 STATE_COMMIT_FAILED` после задержки по-прежнему читает только current; `504 BUILD_TIMEOUT` требует внешнего restart/readiness и ручного подтверждения перед bootstrap/current. Raw proxy 504 не объявляется BUILD_TIMEOUT. Capacity/rate/shutdown/state-read/resolution/calculation failures сохраняют свои обычные отказы; code/status сверены с server mapping, новых публичных кодов нет.
3. Совпадение birth проверялось без chart_stale. Matching stale теперь имеет локальный UI-статус `stale`: старые факты, явное устаревание, «Пересчитать» и safe recheck сохранены. Fresh same-intent/same-identity допускает matched; bootstrap version не используется для доказательства POST.
4. После session 409 `accept()` очищал отказ без объяснения. Теперь успешный bootstrap/current сообщает об обновлении сессии, отклонённом build и необходимости нового нажатия. При failed read успех не объявляется; уведомление появляется после последующего успешного safe recheck. Следующий явный POST снимает прежнее уведомление; draft/gate сохраняются.
5. Committed POST не содержит birth. Coordinator хранит отдельную неизменяемую экранную сводку даты, времени/null и названия из снимка отправленного intent, привязанную к показанной chart_identity. Она не изменяется вместе с draft или после отклонённого следующего POST. Полный BirthViewDTO, timezone/offset/warnings не выдумываются; GET только ради сводки не добавлен. Current/already_applied/superseded отображают actual серверный birth.
6. Search presentation не знала восстановленное место и стирала подпись при focus/blur. Idle presentation теперь читает подтверждённое место из form; дополнительных lookup и выдуманных региона/страны нет. Edit немедленно снимает ID; новый явный выбор используется следующим POST, undefined не отображается.

Затронуты только `ui/recovery.mjs`, `session.mjs`, `main.mjs`, `tests/ui/recovery.test.mjs`, `session.test.mjs`, этот план и пять записей bug registry. HTTP DTO/routes/transport, Python-код, calculation/cache/CAS/watchdog, form/HH:MM/null, renderer/places model, requirements/ADR/Manager-артефакты и historical prompts не менялись. Новых зависимостей, endpoints, client timeout, polling или automatic POST нет.

### Подход, coverage и точные test IDs

**Тесты → реализация.** Переиспользованы real coordinator/transport/form/mount, существующие HTTP golden, fakeClock/deferred/entered и DOM-port. Первое воспроизведение после согласования assertions с датами существующего golden: **121 passed / 27 failed**, exit 1; failures дошли до ожидаемых calls/messages/selection, ошибок импорта/setup и отменённых tests нет. GREEN того же набора — **148 passed**, exit 0. Добавлен **31** case к прежним 149 UI tests; существующие already_applied/superseded/session-loss/502 cases расширены без удаления неполного 200 guard.

| Finding / REQ / AS | Фактические test IDs и чувствительное evidence |
|---|---|
| 006; REQ-UI-09, AS-UI-14/23 | `unconfirmed ${text 502/text 504/empty 503/malformed capacity DTO/unknown 503 code/unknown 599/internal 500/internal 500 with cookie} blocks POST until bootstrap/current and then permits only gated manual retry` — 8 cases; deferred bootstrap/current блокируют POST, original/bootstrap/current request IDs различаются, отсутствие proxy ID остаётся null; успешный old current и явный gate — позитивный контроль. |
| 006; REQ-UI-09, AS-UI-13/14/23 | `unconfirmed 5xx respects real Retry-After, checks once and keeps a failed check safe-read-only`; `mounted unknown 5xx failed at ${/session/bootstrap / /charts/current} preserves facts and offers a working safe check` — 2 mounted cases; `known ${status} ${code} remains an ordinary refusal with no automatic reconciliation or POST` — 6 controls. Existing STATE_COMMIT_FAILED/BUILD_TIMEOUT/capacity/429/restart tests сохранены. |
| 007; REQ-UI-08/09, AS-UI-11/23 | `mounted matching ${stale/fresh} current with unchanged identity preserves facts and honest recovery feedback` — 2 cases: точные прежние факты и четыре DOM tables; stale recheck читает без POST, fresh matching не скрывается из-за прежнего identity, пересчёт только отдельным действием. Existing different/unavailable/two-tab controls проходят. |
| 008; REQ-UI-03/09/10, AS-UI-12/19 | `${SESSION_REQUIRED/SESSION_EXPIRED/SESSION_NOT_FOUND} recovers ${empty/chart_ready} with visible new-action explanation and intact draft` — 6 mounted cases; `session-loss check failed at ${/session/bootstrap / /charts/current} never announces success and a later safe read explains the new action` — 2 failure controls. |
| 010; REQ-UI-03/08/09, AS-UI-03/04/10/16/22 | `committed ${known/unknown} time summary belongs to the submitted snapshot despite pending draft edits` — 2 cases; `a rejected later build keeps the summary of the previously displayed committed chart`; `foreground summary reads actual current birth instead of a previous successful build intent`; расширенные `${already_applied/RESULT_SUPERSEDED} reads actual current and never treats the POST as a new chart` — 2 current controls. |
| 012; REQ-UI-02/08/10, AS-UI-02/10/19 | `restored ${chart_ready/chart_unavailable}/${time_unknown} place survives focus/blur then edit and explicit new selection` — 3 cases known natal/unknown cosmogram/unavailable; focus не вызывает lookup, edit снимает ID, после реального поиска и выбора POST получает новый ID. |

### Команды, результаты и воспроизводимость

Все команды выполнялись из указанного checkout с существующими Node/Python, без установки новых зависимостей. Evidence — ignored `logs/ui-dev-08/`; SHA-256 пяти source/test файлов и baseline — `fingerprint.json`, совпадение после документальных правок подтверждено. После runtime checks менялись только документы. Проверка документации: **63 локальные ссылки/якоря**, fences Markdown, восемь уникальных findings и их source/work-item mapping — PASS, exit 0; index пуст.

| Команда | Фактический результат |
|---|---|
| `node --test --test-isolation=none tests/ui/recovery.test.mjs tests/ui/session.test.mjs tests/ui/places.test.mjs tests/ui/facts.test.mjs` | RED **121 passed / 27 failed**, exit 1 (`node-red.log`); GREEN **148 passed / 0 failed**, exit 0 (`node-target.log`). |
| `node --test --test-isolation=none tests/ui/*.test.mjs` | **180 passed / 0 failed**, exit 0, 265.59 ms (`node-all.log`). |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py tests/http_api/test_build_admission.py tests/http_api/test_session.py tests/test_module_boundaries.py -q` | **178 passed in 14.79s**, exit 0 (`python-target.log`). |
| `python -B -m pytest -p no:cacheprovider tests/http_api -q` | Первый запуск sandbox: **299 passed / 1 failed**, exit 1, PermissionError записи pip build tracker в installed-wheel test (`python-related.log`). Повторение той же pytest-команды с необходимым доступом: **300 passed in 21.57s**, exit 0 (`python-related-elevated.log`). |
| `python -B -m pytest -p no:cacheprovider -q` | **2959 passed / 1 failed in 121.30s**, exit 1 (`python-full.log`); только `tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases`, прежний DEBT-CALC-001 с тем же контрпримером sextile/trine одной пары. |
| `git diff --check` | PASS, exit 0. |

### Наблюдаемость, handoff и непроверенное

Calls сопоставлены с HTTP 003 (явный POST), 001 (bootstrap), 004 (current); retained intent не приписывается второму POST. Safe GET возвращает полный current как позитивный контроль, не запускает engine/Orchestrator. Client сохраняет реальные request IDs/Retry-After, не публикует context_status и не логирует новый payload. HTTP tests проверяют прежние load → session_view / execute → save, admission и lifecycle; серверный поток и диаграммы сохраняются.

**Ручной/браузерный retest:** NOT RUN на изменённой версии, стенд не перезапускался. После отдельно разрешённого обновления проверить known/unknown summary при редактировании, restore → focus/blur → edit → выбор, session 409 → failed/successful safe read и новое отдельное нажатие. Proxy 502/504/500 и stale recovery воспроизводить на управляемой сети/fixtures; не ломать рабочий сервер ради случайной ошибки. Node DOM-port не доказывает browser/layout; Tester должен независимо сохранить tested version/evidence.
**Оставшиеся ограничения:** вариант B сохраняет accepted risk позднего commit и повторной работы после successful old/empty check; reading matching current не идентифицирует попытку. DEBT-CALC-001 OPEN, полный regression gate FAILED без xfail/skip/изменения расчёта. Все восемь замечаний внешней модели FIXED PENDING RETEST; окончательное закрытие, G4/G5 и Manager acceptance не объявляются.
**Передача:** локальный diff от baseline + ignored logs/fingerprint позволяют повторить команды выше. Commit/push/PR, перезапуск и публикация в поручении 08 не выполнялись; historical prompts 01…08 сохранены. Для передачи между checkout нужен отдельный проверяемый commit; source/test hashes следует сверить перед использованием этого evidence.

<a id="debt-calc-001-test-skip"></a>
## 24. Временный skip теста DEBT-CALC-001

**Дата / Owner исполнения:** 2026-10-07, Developer. **Основание:** новое прямое поручение владельца «Поставь метку игнор падающего теста». Оно заменяет прежний запрет skip/xfail только для одного перечисленного теста. **Baseline:** `f7fb34bce8de23d8c08a7491c5698a7b5ab9e4ab`, `dev/ui-birth-form-and-facts-review`; дерево и index были чистыми.

На `tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases` добавлен `pytest.mark.skip` с русской причиной и ID долга. Assertion, генератор, golden и расчётный код сохранены. Исключение не распространяется на остальные property/integrity/reference tests. Нового regression-теста для самого декоратора не требуется; выборочное выполнение проверяет skip/reason, связанный набор — выполнение соседних тестов, полный pytest — остальные проверки проекта.

DEBT-CALC-001 остаётся OPEN: причина недопустимых входов генератора и топология бисекстиля требуют отдельного исправления из раздела 19. При закрытии долга снять этот skip и выполнить целевые/связанные/полные проверки без исключения; Tester подтверждает evidence, Manager закрывает долг. Результат с skipped не доказывает свойство монотонности и не является самостоятельной приёмкой G4/G5.

**Фактические проверки:** выполнены target → related → full; все команды дали exit 0. `-X utf8` сохраняет русскую reason без повреждения кодировки. Evidence — ignored `logs/debt-calc-001-skip/`.

| Команда | Результат |
|---|---|
| `python -X utf8 -B -m pytest -p no:cacheprovider tests/test_configurations.py::test_property_configuration_count_does_not_grow_when_threshold_decreases -q -rs` | **1 skipped in 0.40s**, причина DEBT-CALC-001 показана (`target.log`). |
| `python -X utf8 -B -m pytest -p no:cacheprovider tests/test_configurations.py -q -rs` | **49 passed / 1 skipped in 0.84s** (`related.log`); соседние property/integrity/reference tests выполняются. |
| `python -X utf8 -B -m pytest -p no:cacheprovider -q -rs` | **2959 passed / 1 skipped in 128.59s**, exit 0 (`full.log`); skipped только указанный тест. Запуск с необходимым доступом к временным файлам pip для installed-wheel test. |
| `git diff --check` | PASS, exit 0. |

Документальная проверка: 63 локальные ссылки/якоря разделов внешнего ревью, fences и mapping findings — PASS; отдельно три ссылки новой записи разрешаются в section 24. Тестовая правка содержит только четыре строки одного skip-декоратора; production code, source/test-файлы DEV-UI-07/08 и historical prompts не менялись. Долг OPEN, независимая приёмка и полная проверка свойства монотонности ожидаются. Commit/push/PR и перезапуск стенда этим поручением не запрошены.

<a id="developer-ready-for-test"></a>
## 25. Developer Handoff — READY_FOR_TEST

**Owner / дата:** Developer, 2026-10-08. **Status:** **READY_FOR_TEST**, по поручению владельца «переводи артефакт разработчика в ready to test». Пакет реализации и Developer checks подготовлен для независимого тестирования. Это статус Developer-артефакта; получение пакета Tester, изменение общего статуса change, формальное решение Manager по G4 и приёмка G5 здесь не объявляются.

### Версия передаваемого пакета

- **Checkout:** `C:\Users\KateUser\.codex\worktrees\c9cb\exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`.
- **Implementation commit:** `f7fb34bce8de23d8c08a7491c5698a7b5ab9e4ab`; DEV-UI-07 — `25e3e0fa9ce1a4ebdd50d70df72bbe771e065423`, DEV-UI-05/06 и локальный proxy fix — `0d5d70a`. Реализация опубликована в Developer-ветке правильного репозитория `ksenia-baranova/exact-orb-demo` предыдущими поручениями; новой проверки remote в этом документальном задании нет.
- **Коммит передачи поверх implementation commit:** четыре строки одного `pytest.mark.skip` в `tests/test_configurations.py`, запись разрешённого исключения в Manager-реестре и два текущих Developer-документа. По отдельному поручению владельца 2026-10-08 этот пакет включается в один коммит и отправляется в `dev/ui-birth-form-and-facts-review`. Воспроизводимая версия для Tester — коммит, содержащий эту редакцию handoff и skip; его полный SHA и результат push фиксируются в итоговом сообщении. Один commit `f7fb34b` без коммита передачи даст прежний красный property-тест.
- **Точная версия теста со skip:** SHA-256 `tests/test_configurations.py` = `5362920B80D5B61356C87DA84325CDCAB81BBB4CC6028EEA3FABF1E133662576`. Пять SHA-256 source/test файлов DEV-UI-08 из `logs/ui-dev-08/fingerprint.json` повторно сверены 2026-10-08 и совпали; `src/` и UI tests с момента прогонов не менялись.
- **Requirements baseline:** нормативный HTTP/backend @ `652bd73405db0a0611e98e81af6f3f668dd429f6`, смысл 10 REQ / 23 AS change @ `ce25dd0`; точные источники — раздел 1. **Decision register baseline:** [реестр](../change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) в implementation commit плюс запись исключения в коммите передачи; DP-UI-01…09 ACCEPTED, семантический выбор @ `64934fc` сохранён.

### Реализованное поведение и покрытие

| Work items / требования | Передаваемый результат и подход | Evidence |
|---|---|---|
| DEV-UI-01/02; REQ-UI-01…03/10 | Страница и assets доставляются FastAPI и installed wheel; same-origin client, форма даты/времени, явный выбор `place_id`, debounce и сброс ID при редактировании. UI обслуживает тот же web process. | Журналы 9–14, delivery/transport/form/places tests. |
| DEV-UI-03; REQ-UI-01/03/08/09 | Bootstrap/current, ручной unchecked-checkbox gate перед POST, busy и типизированные ошибки, форматирование ввода времени. | Журнал 12; session/form tests. TEST-FIND-UI-004 ожидает ручного retest. |
| DEV-UI-04; REQ-UI-03…07/10 | Три группы фактов из ChartDTO, форматирование, режим неизвестного времени, действия результата по AS-UI-22. | Журнал 15; facts/projector tests, golden natal/cosmogram. |
| DEV-UI-05/06; REQ-UI-01…10 | Recovery, foreground/two-tab, интеграция страницы и API; локальный proxy fix обеспечивает обычный браузерный путь. | Журналы 17/18/20; managed clock/transport и реальные backend integration checks. Оставшиеся visual/mobile criteria DEV-UI-06 переданы Tester, их выполнение не подтверждено. |
| DEV-UI-07; TEST-FIND-UI-005/009/011 | Nullable region, revalidation cache headers, guards DTO и видимое безопасное восстановление при отказе renderer. | [Раздел 22](#dev-ui-07-execution), чувствительный RED → GREEN, реальные installed-wheel и HTTP checks. |
| DEV-UI-08; TEST-FIND-UI-006/007/008/010/012 | Безопасная сверка неподтверждённых 5xx, честный stale/session-loss feedback, immutable сводка committed результата, сохранение восстановленной подписи места. | [Раздел 23](#dev-ui-08-execution), RED 121 passed / 27 failed → GREEN 148 passed; fake clock/deferred и реальные coordinator/transport/form с листовым DOM-port. |

Связи каждого work item с промтом, REQ/AS и тестами сохранены в разделах 5, 21–23. Исторические промты не изменены. Состав поставки: `src/exact_orb/http_api/ui/`, доставка assets, local HTTP composition/runbook, `tests/ui/`, связанные HTTP tests и Developer evidence. Публичные HTTP DTO/коды ошибок, расчётный API и серверная последовательность bootstrap/current/build сохраняются; автоматический повтор POST отсутствует. Действуют ADR-0034 и accepted вариант recovery B из DP-UI-09.

### Фактически выполненные проверки

Это результаты уже выполненных прогонов на соответствующем коде; при переводе статуса runtime tests заново не запускались. Числа пересекающихся наборов не суммируются. Логи ignored и доступны в этом checkout; для другого окружения Tester повторяет команды и сохраняет собственное evidence.

| Команда из корня checkout | Последний результат / evidence |
|---|---|
| `node --test --test-isolation=none tests/ui/*.test.mjs` | **180 passed / 0 failed / 0 skipped**, exit 0, 265.59 ms; `logs/ui-dev-08/node-all.log`. |
| `python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py tests/http_api/test_build_admission.py tests/http_api/test_session.py tests/test_module_boundaries.py -q` | **178 passed**, exit 0, 14.79 s; `logs/ui-dev-08/python-target.log`. |
| `python -B -m pytest -p no:cacheprovider tests/http_api -q` | **300 passed**, exit 0, 21.57 s; `logs/ui-dev-08/python-related-elevated.log`, включая installed wheel вне checkout. |
| `python -X utf8 -B -m pytest -p no:cacheprovider tests/test_configurations.py -q -rs` | **49 passed / 1 skipped**, exit 0, 0.84 s; `logs/debt-calc-001-skip/related.log`. |
| `python -X utf8 -B -m pytest -p no:cacheprovider -q -rs` | **2959 passed / 1 skipped**, exit 0, 128.59 s; `logs/debt-calc-001-skip/full.log`. Единственное исключение — согласованный тест DEBT-CALC-001. |

До разрешённого skip полный pytest дал 2959 passed / 1 failed, exit 1; этот результат остаётся в разделе 23. Текущий exit 0 с исключением не доказывает исправление свойства монотонности. Node v24.19.0, Python 3.14; новых зависимостей нет. На Windows для installed-wheel проверки потребовался доступ к системным временным файлам pip; первый sandbox failure и успешное повторение сохранены отдельно.

### Запуск и независимая проверка Tester

1. Зафиксировать implementation commit и коммит передачи из этого handoff. Проверить установленное окружение, `data/places.sqlite`, ephemeris path и отдельную SQLite базу сессий по [HTTPS runbook](../../runbooks/http_api_local_https.md). В существующем стенде сохранить прежнюю базу и параметры; состояние сохранённых карт входит в restore-сценарий.
2. Запускать один Uvicorn process через `exact_orb.http_server:create_local_app` с `--workers 1 --no-proxy-headers` и существующим Caddyfile; точные команды и переменные — в runbook. Проверить внутренний `/health/ready`, bootstrap/cookie и `/places` через HTTPS. Открывать `https://exact-orb.localhost/`; `file://index.html` не является запуском приложения. `127.0.0.2` — исходящий адрес Caddy.
3. Перед ручным retest обновить процесс приложения до этой версии, затем перезагрузить страницу и сверить assets/cache headers. В этом задании стенд не перезапускался; прежняя ручная проверка natal build/details/reload до DEV-UI-07/08 не является проверкой нового пакета.
4. По [23 acceptance scenarios](../../requirements/changes/ui-birth-form-and-facts/scenarios.md) независимо проверить форму, выбор места, known/unknown time, закрытый gate, build/details/reload, три группы и действия результата; ширины 360/768/1440, keyboard/focus, длинные таблицы и две вкладки. Сопоставить видимый результат, фактические запросы и журналы с сохранением версии/evidence.
5. Повторно проверить [TEST-FIND-UI-004…012](../../testing/ui-birth-form-and-facts/manual-test-bugs.md); все остаются FIXED PENDING RETEST. Для nullable region, malformed DTO, 5xx, session loss, stale и late response использовать управляемые fixtures/transport: успешный контроль, отсутствие auto-POST и новый явный gate обязательны. Случайный сетевой сбой не заменяет воспроизводимый сценарий. Статусы findings и независимое заключение ведёт Tester.

### Ограничения и следующий результат

- **DEBT-CALC-001 OPEN:** один property-тест временно исключён прямым поручением владельца. Исправление генератора/топологии и снятие skip — отдельная задача; [разделы 19](#debt-calc-001) и [24](#debt-calc-001-test-skip), [реестр долгов](../change_plans/ui-birth-form-and-facts/artifacts.md#decision-register).
- **DP-UI-09, вариант B:** после успешной сверки old/empty current допустим один ручной повтор; риск позднего commit исходной попытки принят и сохраняется. Совпадение current не идентифицирует конкретный POST.
- **DEBT-UI-001 и прежний naming debt DP-UI-03** остаются в Manager-реестре с условиями возврата. Закрытый checkbox gate не подтверждает готовность публичного доступа; требований к публичному выпуску этот handoff не меняет.
- **NOT RUN на финальной версии:** независимая browser/mobile/keyboard acceptance, визуальная сверка макета и управляемые live error/recovery проверки DEV-UI-07/08. Node DOM-port и ASGI evidence не заменяют их. Analyst чистовая редакция/карта переноса и Manager acceptance остаются действиями своих ролей.

Следующий результат — независимый Tester report на зафиксированной версии с disposition сценариев и findings. Перевод статуса выполнен отдельно от порученной затем публикации коммита; Manager/Tester-статусы сохраняются.

**Проверка этой передачи (2026-10-08):** документальные валидаторы — PASS, exit 0: 72 локальные ссылки/якоря разделов внешнего ревью, Markdown fences и mapping восьми findings; отдельно 19 ссылок/якорей актуальных заголовков и handoff, READY_FOR_TEST metadata и SHA-256 теста со skip. Пять source/test fingerprints DEV-UI-08 совпали. `git diff --check` — PASS, exit 0. В этом задании изменены только актуальные статусы и handoff двух Developer-документов; прежние skip и запись исключения сохранены.
