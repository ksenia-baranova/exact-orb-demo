# Implementation Plan: ui-birth-form-and-facts

**Owner:** Developer. **Дата:** 2026-10-06. **Ветка:** `dev/ui-birth-form-and-facts-review`.
**Status:** READY_FOR_DEVELOPMENT — административное утверждение Manager по поручению владельца 2026-10-07; DEV-UI-01 COMPLETE; DEV-UI-02 IMPLEMENTED / BROWSER CHECK PENDING; оба результата включены в пакет Developer для одного коммита, остальные задания NOT STARTED. Текущий delivery status/G3 — [Manager-артефакт](../change_plans/ui-birth-form-and-facts/artifacts.md#change-brief).
**Technical assessment:** FEASIBLE; закрытые продуктовые решения повторно сверены, blocking semantic gaps Developer не обнаружены.
**Estimate Developer:** **5–8 рабочих дней / 40–64 человеко-часа**, один рабочий день = 8 часов. Уверенность средняя.
**Бюджет владельца:** DP-UI-07 текущей Manager-редакции — Analysis 4 / Development 5 / Testing 5 дней. Estimate Developer 5–8 сохраняется; относительно budget Development 5 риск составляет до +3 дней. Это не обещание выполнить верхнюю границу за 5 дней.

## 1. Baselines и разрешённый контракт

| Источник | Версия и предел |
|---|---|
| Общий `change/ui-birth-form-and-facts` | `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`, получен из `ksenia-baranova/exact-orb-demo` 2026-10-06; Developer-ветка обновлена `git merge --ff-only FETCH_HEAD`. |
| Baseline исполнения DEV-UI-01 | `082c6b9ac5c8b054c38de5f17bc673956ec058d8`, проверен новым fetch из `ksenia-baranova/exact-orb-demo`: `HEAD` = `FETCH_HEAD`, расхождение `0 0`. Нормативный контракт и версии REQ/AS/DP выше сохранились. Результат сохранён при обновлении ветки и входит в общий пакет DEV-UI-01/02. |
| Baseline исполнения DEV-UI-02 | `6fc62b9c8813b5aadfd5150ca39033664f18b777`, PR #49/50 интегрируют Tester `0f6aa82` и утверждение Manager `e4f60fb`. Получен fetch и `git merge --ff-only FETCH_HEAD` 2026-10-07. Семантика REQ/AS @ `ce25dd0` и HTTP baseline сохранены; допуск G3 подтверждён Manager. Общий пакет DEV-UI-01/02 подготовлен поверх этого HEAD; сведения о подготовке коммита — в разделе 11. |
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

Карточки 03–06 и их файлы остаются **планируемыми**. DEV-UI-01 выполнен; код и автоматические проверки DEV-UI-02 готовы, реальная браузерная проверка остаётся pending. Факт исполнения записан в журнале Developer. Карточки утверждены Manager 2026-10-07; историческое DRAFT/NOT EXECUTED в промтах не переписывается. В тестовых docstrings/comments сохраняются REQ/AS IDs и ссылки на Analyst baseline; при финализации ссылки сверяются с картой переноса Analyst.

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

- **REQ/AS:** REQ-UI-03, 08, 09; AS-UI-12–14, 16, 18, 23. **DP:** 04/09. **Dependency:** DEV-UI-02/03/04.
- **Файлы:** новый `ui/recovery.mjs`; `session.mjs`, `main.mjs`, `transport.mjs`; новый `tests/ui/recovery.test.mjs`; reuse controlled server seams из HTTP tests.
- **Результат:** code-specific recovery, отказ самой сверки, потеря ответа, сохранение submitted intent отдельно от draft/current, foreground двух вкладок. DP-UI-09 применяется без обещания идемпотентности или остановки первой задачи.
- **Подход:** тесты → реализация; контролируемые responses/Event/fake clock и реальные coordinator modules. Mock самого coordinator запрещён.
- **Покрытие:** `test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation`, `test_disconnect_during_protected_commit_is_visible_after_restart`; `test_build_admission.py::test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart`, `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state`. Это server evidence, новые browser transitions отсутствуют.
- **Наблюдаемость:** первый/второй POST и bootstrap/current имеют разные request/run IDs; late completion не выдаётся за ответ второго POST. AS-UI-14 и AS-UI-23 различаются по реально полученному outcome.
- **Промт:** [05-recovery-and-two-tabs](../../../prompts/2026-10-06/ui-birth-form-and-facts/05-recovery-and-two-tabs.md).
- **Completion:** committed/not committed/in-progress после disconnect, отказ сверки, success old/empty и manual retry, two-tabs/CAS outcomes проходят; health остаётся внутренним, автоматического повторного POST нет.

<a id="dev-ui-06"></a>
### DEV-UI-06. Проверенный browser путь и передача Tester

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
