# Change plan: HTTP API and Session Middleware

- **Статус:** Analysis PR #37 принят в `change/*`; решения DP-HTTP-01…06 и FIND-HTTP-021 подтверждены. Developer подготовил implementation plan и промты в `c7e794a`; Gate A и реализация впереди.
- **Change:** `change/http-api-and-session-middleware`.
- **Roadmap:** M1-6, `feat/http-api-and-session-middleware`.
- **Исходный `main`:** `e337f5107d7a3092983f1d920aac45040c2df6ed`.
- **Стартовый commit `change/*`:** `acc0a7671d52676e0e230e76497d59f769ec4fa8`.
- **Текущая ветка:** `dev/http-api-and-session-middleware` от merge commit Analysis PR #37 `f11275c1306bf227544b10321151371852e24b28`.
- **Владелец плана:** Technical Change Lead.
- **Календарный план:** [http-api-and-session-middleware.puml](http-api-and-session-middleware.puml). Lead подтвердил исходную оценку: подготовка 0,5 дня, Analysis 1,5 дня, Development 1 день, Testing 1 день; всего 4 рабочих дня.

## 1. Цель change

Добавить HTTP API для уже реализованного приложения. Через него клиент сможет:

1. создать новую анонимную сессию или восстановить существующую;
2. найти населённый пункт;
3. передать данные рождения и получить рассчитанную натальную карту.

HTTP-слой принимает запросы, вызывает существующие компоненты приложения и возвращает ответы клиенту. Он не создаёт
отдельную реализацию расчётов, сессий или каталога мест.

Также приложение должно корректно запускать и останавливать используемые компоненты и ограничивать слишком частые или
одновременные запросы на расчёт.

## 2. Что входит в change

- Создание FastAPI-приложения.
- Подготовка приложения к работе до начала приёма HTTP-запросов: открытие каталога мест и запуск необходимых фоновых
  задач.
- Корректная остановка приложения: прекращение приёма новых запросов, завершение уже начатых запросов и закрытие
  ресурсов.
- Периодическое удаление истёкших сессий через готовый `ApplicationRuntime`.
- Работа с анонимной сессией через защищённую cookie: создание новой сессии и восстановление сохранённого состояния.
- HTTP API для создания или восстановления сессии.
- `GET /charts/current` для чтения сохранённой карты через `ContextService.load` и чистую `session_view`.
- Расширение `session_view` чистой birth-проекцией из готового snapshot для публичного `BirthViewDTO`, без нового I/O или application ports.
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
- Изменение расчётного движка, Session Store, `ContextService`, `ApplicationRuntime` или `ApplicationOrchestrator`, если
  анализ не обнаружит подтверждённую необходимость.
- Отдельные инфраструктурные работы. Если они понадобятся, Lead дополнит границы change и назначит отдельную работу.

## 4. Принятые входные артефакты

Первая рабочая роль получает состояние `change/*` после принятия подготовительного PR. Источниками требований являются
документы, код и тесты в этом commit. Переписка предыдущих ролей и исторические файлы `prompts/**` входом не являются.

| Артефакт                                                                                                                                                                                     | Для чего используется                                               |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [HTTP requirements](../../requirements/http_api.md) | согласованный HTTP-контракт и acceptance scenarios из Analysis PR #37; implementation evidence впереди |
| [Roadmap](../roadmap.md), M1-6                                                                                                                                                               | состав change и связь с предыдущими этапами                         |
| [Обзор требований](../../requirements/overview.md) и [сценарии](../../requirements/scenarios.md)                                                                                             | границы системы и пользовательские сценарии                         |
| [ADR-0006](../../requirements/decisions/0006-application-orchestrator.md)                                                                                                                    | создание и восстановление сессии, граница `ApplicationOrchestrator` |
| [ADR-0013](../../requirements/decisions/0013-token-abuse-protection.md)                                                                                                                      | ограничения расчётных запросов                                      |
| [ADR-0040](../../requirements/decisions/0040-session-bootstrap-and-current-chart.md) и [ADR-0041](../../requirements/decisions/0041-stored-chart-in-session.md)                                                                                                                     | восстановление сохранённой карты                                    |
| [Требования к сессии](../../requirements/component_responsibilities/exact-orb_session_requirements.md) и [восстановлению карты](../../requirements/session/stored-chart-session-behavior.md) | поведение сессии и представление её состояния                       |
| [Требования к каталогу мест](../../requirements/component_responsibilities/exact-orb_place_catalog.md)                                                                                       | поиск мест и известные варианты ответа                              |
| Код `src/exact_orb/application/` и тесты `tests/application/`                                                                                                                                | фактически реализованные интерфейсы и поведение                     |
| `tests/test_module_boundaries.py`                                                                                                                                                            | обязательные архитектурные границы                                  |

## 5. Журнал change

Журнал — это отдельный файл с краткой хронологией работы над change. Он не повторяет требования и change plan, а
показывает, что фактически происходило и на каком состоянии репозитория.

В журнал записываются:

- дата и событие;
- роль и рабочая ветка;
- commit, от которого роль начала работу;
- созданный результат и ссылка на Pull Request;
- решения Lead;
- найденные проблемы, возвраты на доработку и blockers;
- выполненные проверки и их фактические результаты;
- переход change на следующий этап.

Журнал хранится в [experiment-002-log.md](../experiments/experiment-002-log.md) и обновляется при передаче работы между
ролями или принятии решения, влияющего на change.

## 6. Этапы работы

| Этап и ветка                                             | Результат                                                                                                             | Статус                          |
|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|---------------------------------|
| Подготовка Lead — `lead/http-api-and-session-middleware` | протокол, change plan, журнал и список входных артефактов | PR #36 принят в `change/*` |
| Анализ — `analysis/http-api-and-session-middleware` | HTTP requirements, 29 acceptance scenarios и sequence diagrams | PR #37 принят в `change/*`; решения Lead согласованы; формальный Tester review не записан |
| Разработка — `dev/http-api-and-session-middleware` | implementation plan, код, автоматизированные тесты и review | draft implementation plan и 13 промтов в `c7e794a`; Gate A, код и тесты впереди |
| Тестирование — `test/http-api-and-session-middleware`    | ручная и исследовательская проверка, необходимые regression tests и evidence                                          | ожидает завершения разработки   |
| Финальная приёмка Lead                                   | решение о готовности change к merge в `main` или возврат на доработку                                                 | ожидает завершения тестирования |

Каждая роль начинает работу от актуального состояния `change/*`. Результат роли возвращается в `change/*` через Pull
Request.

## 7. Что необходимо определить до начала разработки

| ID         | Вопрос                                                                                             | Кто готовит решение                                            | Статус |
|------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------|--------|
| DP-HTTP-01 | Endpoint, DTO, ошибки и HTTP-статусы — [§2–8](../../requirements/http_api.md) | Functional Analyst; review Developer/Tester; Lead approval | согласовано Lead 2026-09-30; implementation schema впереди |
| DP-HTTP-02 | Численные session/IP limits и 5 active build — [§9.1](../../requirements/http_api.md#91-лимиты) | Functional Analyst и Developer; Lead | согласовано всеми ролями, решение Lead в review PR #37 |
| DP-HTTP-03 | Trusted proxy/client IP algorithm — [§10](../../requirements/http_api.md#10-client-ip-и-trusted-proxy) | Developer security review; Lead approval | Developer review выполнен; согласовано Lead 2026-09-30; код впереди |
| DP-HTTP-04 | Deadline, shutdown и ownership задач — [§9, §11](../../requirements/http_api.md) | Developer; Lead | C для M1-6 и A как target state согласованы; нижняя граница permit при shared leader подтверждена через FIND-HTTP-021; S0 и implementation evidence ожидаются |
| DP-HTTP-05 | Четыре HTTP sequence и синхронизация session diagrams — [§16](../../requirements/http_api.md#16-sequence-diagrams) | Functional Analyst; Lead approval | согласовано Lead 2026-09-30; сверка с реализацией впереди |
| DP-HTTP-06 | Чистая birth projection в `session_view` — [§7.1](../../requirements/http_api.md#71-основные-формы) | Developer review; Lead scope approval | scope согласован Lead; Developer подтвердил реализуемость; код и тесты впереди |

## 8. Условия перехода между этапами

### Подготовка → анализ

- change plan и файл журнала созданы;
- входные артефакты перечислены;
- подготовительный PR принят в `change/*`;
- commit, от которого начинает работу Functional Analyst, записан в журнале.

### Анализ → разработка

- описаны четыре business endpoint: bootstrap сессии, чтение текущей карты, поиск места и построение карты;
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

- Подготовка Lead принята в `change/*` через PR #36. Analysis PR #37 принят в `change/*` с merge commit `f11275c`.
- Developer работает в `dev/http-api-and-session-middleware`; implementation plan и код ещё не подготовлены в рамках этого обновления. Testing не начат.
- DP-HTTP-01…06 согласованы Lead 2026-09-30; для DP-HTTP-04 выбран вариант C в M1-6 и A как target state. Developer review выполнен; implementation evidence и формальный Tester review впереди.
- FIND-HTTP-019 закрыт решением Lead: чистая birth-проекция включена, исходная оценка Gantt оставлена. Для FIND-HTTP-020 старый путь ADR и scope исправлены в этом плане; изменения Lead-owned документа ещё предстоит вернуть в `change/*` по процессу ролей.
- Финальный статус не присвоен.
