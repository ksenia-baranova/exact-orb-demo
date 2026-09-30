# Change plan: HTTP API and Session Middleware

- **Статус:** проект анализа переработан после review; ожидает Developer/Tester review и Lead approval.
- **Change:** `change/http-api-and-session-middleware`.
- **Roadmap:** M1-6, `feat/http-api-and-session-middleware`.
- **Исходный `main`:** `e337f5107d7a3092983f1d920aac45040c2df6ed`.
- **Стартовый commit `change/*`:** `acc0a7671d52676e0e230e76497d59f769ec4fa8`.
- **Текущая ветка:** `analysis/http-api-and-session-middleware`.
- **Владелец плана:** Technical Change Lead.
- **Календарный план:** [http-api-and-session-middleware.puml](http-api-and-session-middleware.puml).

## 1. Цель change

Добавить HTTP API для уже реализованного приложения. Через него клиент сможет:

1. создать новую анонимную сессию или восстановить существующую;
2. отдельным запросом прочитать текущую сохранённую карту;
3. найти населённый пункт;
4. передать данные рождения и получить рассчитанную натальную карту.

HTTP-слой принимает запросы, вызывает существующие компоненты приложения и возвращает ответы клиенту. Он не создаёт отдельную реализацию расчётов, сессий или каталога мест.

Также приложение должно корректно запускать и останавливать используемые компоненты и ограничивать слишком частые или одновременные запросы на расчёт.

## 2. Что входит в change

- Создание FastAPI-приложения.
- Подготовка приложения к работе до начала приёма HTTP-запросов: открытие каталога мест и запуск необходимых фоновых задач.
- Корректная остановка приложения: прекращение приёма новых запросов, завершение уже начатых запросов и закрытие ресурсов.
- Периодическое удаление истёкших сессий через готовый `ApplicationRuntime`.
- Работа с анонимной сессией через защищённую cookie: создание новой сессии и восстановление сохранённого состояния.
- HTTP API для создания или восстановления сессии без карты в ответе.
- Отдельный HTTP API чтения текущей сохранённой карты.
- Предложение Analysis к расширению scope, ожидающее решения Lead:
  ограниченное расширение чистой `application/session_view` — проекция birth
  из уже загруженного snapshot без I/O, resolver, cache, engine и новых
  application ports (FIND-HTTP-001/019).
- HTTP API поиска населённых пунктов на основе готового `PlaceSearch` и `SqlitePlaceCatalog`.
- HTTP API построения натальной карты через существующий `ApplicationOrchestrator`.
- Форматы HTTP-запросов, успешных ответов и ошибок для этих операций.
- Ограничения частоты запросов и количества одновременно выполняемых расчётов.
- Журналирование основных переходов между HTTP-слоем и компонентами приложения.
- Автоматизированные и ручные проверки HTTP-сценариев.

## 3. Что не входит в change

- Пользовательский интерфейс, autocomplete в браузере и отрисовка карты — M1-7.
- Настройка production-сервера, публичное развёртывание и доставка файла каталога мест — M1-12.
- Интерпретации, LLM, Selection API, Message API и SSE.
- Регистрация, учётные записи и подписки.
- Публичные endpoint полного reset и удаления сессии; component contract ADR-0009 сохраняется.
- Изменения расчётного движка, Session Store, `ContextService`,
  `ApplicationRuntime` или `ApplicationOrchestrator`. Предложенное в §2
  расширение чистой `session_view` станет единственным исключением только после
  решения Lead; до этого оно не считается утверждённой частью scope.
- Отдельные инфраструктурные работы. Если они понадобятся, Lead дополнит границы change и назначит отдельную работу.

## 4. Принятые входные артефакты

Первая рабочая роль получает состояние `change/*` после принятия
подготовительного PR. Источниками являются текущие документы, код и тесты;
`prompts/**` остаётся историческим журналом.

| Артефакт | Для чего используется |
|---|---|
| [Roadmap](../roadmap.md), M1-6 | scope change и связь с предыдущими этапами |
| [HTTP requirements](../../requirements/http_api.md) | единый draft публичного контракта, limits и acceptance scenarios |
| [Overview](../../requirements/overview.md) и [scenarios](../../requirements/scenarios.md) | границы системы и пользовательские сценарии |
| [ADR-0006](../../requirements/decisions/0006-application-orchestrator.md) | transport/session и Orchestrator boundary |
| [ADR-0009](../../requirements/decisions/0009-context-yes-profiles-later.md) | cookie session, TTL, reset/delete |
| [ADR-0012](../../requirements/decisions/0012-bootstrap-request-response-streaming.md) | request/response build и границы streaming |
| [ADR-0013](../../requirements/decisions/0013-token-abuse-protection.md) | admission и session build limits |
| [ADR-0032](../../requirements/decisions/0032-unknown-birth-time-aspect-semantics.md) | cosmogram и устойчивые аспекты |
| [ADR-0036](../../requirements/decisions/0036-application-orchestrator-coordination-info-events.md), [ADR-0037](../../requirements/decisions/0037-context-boundary-and-handler-coordination-logs.md) | обязательные межкомпонентные события |
| [ADR-0039](../../requirements/decisions/0039-https-in-all-environments.md) | HTTPS и Secure cookie в local/test/production |
| [ADR-0040](../../requirements/decisions/0040-session-bootstrap-and-current-chart.md) | bootstrap без карты и отдельный current GET |
| [ADR-0041](../../requirements/decisions/0041-stored-chart-in-session.md) | persisted StoredChart и restore без расчёта |
| [Session requirements](../../requirements/component_responsibilities/exact-orb_session_requirements.md) и [stored chart](../../requirements/session/stored-chart-session-behavior.md) | aggregate lifecycle, projection и recovery |
| [Place catalog](../../requirements/component_responsibilities/exact-orb_place_catalog.md) | search contract и typed outcomes |
| `src/exact_orb/application/`, `tests/application/` | реализованные interfaces/results/cancellation semantics |
| `tests/test_module_boundaries.py` | обязательные architecture invariants |

## 5. Журнал change

Журнал — это отдельный файл с краткой хронологией работы над change. Он не повторяет требования и change plan, а показывает, что фактически происходило и на каком состоянии репозитория.

В журнал записываются:

- дата и событие;
- роль и рабочая ветка;
- commit, от которого роль начала работу;
- созданный результат и ссылка на Pull Request;
- решения Lead;
- найденные проблемы, возвраты на доработку и blockers;
- выполненные проверки и их фактические результаты;
- переход change на следующий этап.

Журнал хранится в [experiment-002-log.md](../experiments/experiment-002-log.md) и обновляется при передаче работы между ролями или принятии решения, влияющего на change.

## 6. Этапы работы

| Этап и ветка | Результат | Статус |
|---|---|---|
| Подготовка Lead — `lead/http-api-and-session-middleware` | протокол, change plan, журнал и список входных артефактов | принято в `change/*` PR #36 |
| Анализ — `analysis/http-api-and-session-middleware` | требования к HTTP API, примеры запросов и ответов, ошибки, acceptance scenarios, критерии приёмки и sequence diagrams | проект готов к review |
| Разработка — `dev/http-api-and-session-middleware` | план реализации, код, автоматизированные тесты и результаты review | ожидает review и утверждения анализа |
| Тестирование — `test/http-api-and-session-middleware` | ручная и исследовательская проверка, необходимые regression tests и evidence | ожидает завершения разработки |
| Финальная приёмка Lead | решение о готовности change к merge в `main` или возврат на доработку | ожидает завершения тестирования |

Каждая роль начинает работу от актуального состояния `change/*`. Результат роли возвращается в `change/*` через Pull Request.

## 7. Что необходимо определить до начала разработки

| ID | Вопрос | Предложение Analysis | Статус |
|---|---|---|---|
| DP-HTTP-01 | endpoints, DTO, statuses, errors | bootstrap, current chart, places, build и internal health по HTTP requirements; retry semantics и exact `Retry-After` определены | FIND-HTTP-011, 014–016 исправлены; затем review Developer/Tester и approval Lead |
| DP-HTTP-02 | admission limits | create 300/час/IP; build 20/час и 100/сутки/session, 300/час и 1500/сутки/IP; 5 active; places 120/мин/IP | пересчитано для NAT/CGNAT; требуется review/approval |
| DP-HTTP-03 | trusted proxy/client IP | строгий XFF/XFP algorithm и CIDR allowlist по HTTP §10 | Developer security review и Lead approval |
| DP-HTTP-04 | deadline, timeout, shutdown ownership | body 5с, build 30с, shutdown grace 30с; bounded leaf operations обязательны; варианты A–D в HTTP §15.2 | Developer выбирает вариант и доказывает deterministic tests; остаётся blocker |
| DP-HTTP-05 | sequence coverage | четыре HTTP diagrams; session 001–003 и 006 синхронизированы | требуется Lead approval |
| DP-HTTP-06 | scope и оценка после роста контракта | Analysis предлагает pure `session_view` expansion и базовую оценку development 4 дня / testing 2 дня | ожидает выбора Developer по DP-HTTP-04 и решения Lead; FIND-HTTP-019 открыт |

## 8. Условия перехода между этапами

### Подготовка → анализ

- change plan и файл журнала созданы;
- входные артефакты перечислены;
- подготовительный PR принят в `change/*`;
- commit, от которого начинает работу Functional Analyst, записан в журнале.

### Анализ → разработка

- описаны четыре business-сценария: bootstrap, current chart, поиск места и build;
- для каждого сценария определены запрос, успешный ответ и ошибки;
- описаны правила cookie, ограничения запросов и необходимые события журнала;
- подготовлены позитивные и негативные acceptance scenarios;
- sequence diagrams соответствуют предложенному поведению;
- Developer и Tester выполнили review, Lead утвердил результат;
- нет открытых вопросов, блокирующих реализацию.

### Разработка → тестирование

- реализованы утверждённые требования;
- пройдены целевые, связанные и полные автоматизированные тесты;
- результаты review зафиксированы;
- нет незакрытых блокирующих замечаний.

### Тестирование → финальная приёмка

- Tester проверил acceptance scenarios и основные ошибочные пути;
- команды и фактические результаты проверок записаны;
- блокирующие дефекты закрыты;
- известные ограничения перечислены.

### Готовность к merge в `main`

- требования, код, тесты и sequence diagrams согласованы между собой;
- все обязательные проверки прошли;
- нет открытых блокирующих замечаний;
- Lead принял change и присвоил статус `READY FOR MAIN`.

## 9. Текущее состояние

- Подготовка Lead: принята в `change/*` PR #36, merge commit `27ae072`.
- Analysis: проект требований и sequence diagrams подготовлен; замечания
  второго review FIND-HTTP-011…019 отражены в контракте и плане. Формулировку
  provenance ADR-0040 по FIND-HTTP-010/012 Lead сверяет до commit.
- Development и Testing: не начаты.
- Текущие gates: DP-HTTP-04 (FIND-HTTP-004/009) требует доказанного
  bounded ownership timeout/native/commit задач; DP-HTTP-06 (FIND-HTTP-019)
  требует решения Lead о расширении scope и базовой оценке 4/2 дня после
  уточнения Developer. DP-HTTP-03 и численные DP-HTTP-02/04 также ожидают
  Developer review и финальный approval Lead.
- FIND-HTTP-007 закрыт разделением ADR-0040: build не требует birth-проекции,
  полное сохранённое представление читает явный `GET /charts/current`.
- Текущие findings: перечислены в [HTTP requirements, §15](../../requirements/http_api.md#15-findings-и-ограничения).
- Финальный статус: не присвоен.
