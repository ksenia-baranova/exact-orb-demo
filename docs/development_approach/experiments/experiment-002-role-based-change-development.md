# Experiment 002. Role-based Change Development

- **Статус:** DRAFT v2 / WORK IN PROGRESS
- **Редакция:** v2 — учтены замечания ревью: режим single operator, критерии успеха, градация gates, primary metrics,
  независимость Tester, связь с Experiment 001
- **Объект эксперимента:** `change/http-api-and-session-middleware`
- **Тип эксперимента:** организационная модель AI-assisted разработки enterprise-приложения
- **Предыдущий эксперимент:** Experiment 001 — атомарные промты и порядок «тест раньше кода»

Текущий запуск: [change plan](../../project_management/change_plans/http-api-and-session-middleware.md)
и [журнал](../../project_management/experiments/experiment-002-log.md).

> Этот документ сохраняет постановку и evidence Experiment 002. Текущие правила метода вынесены в
> [Development approach](../development-approach.md), [Change development process](../process.md) и
> [Roles and ownership](../roles.md). При расхождении эксперимент не переопределяет действующий процесс.

---

## 1. Контекст

Теперь представим, что мы разрабатываем enterprise-приложение.

Реальность такова, что универсальных специалистов, одинаково хорошо владеющих системным анализом, архитектурой,
разработкой, тестированием, эксплуатацией и техническим управлением, на данный момент немного.

В распоряжении enterprise-команды обычно находятся достаточно строго специализированные специалисты:

- функциональные аналитики;
- разработчики;
- тестировщики;
- технические лидеры;
- при необходимости — DevOps / Platform / SRE специалисты.

Следующее направление, которое я хочу исследовать, — можно ли медленно, но управляемо раздвигать границы этих
специализаций с помощью LLM-агентов.

Цель не состоит в том, чтобы превратить каждого участника команды в универсального инженера.

Цель — дать каждой роли немного более широкую область ответственности, сохранив понятные границы ownership и эскалации:

```text
Functional Analyst
    → требования
    → acceptance scenarios
    → acceptance criteria
    → endpoints и DTO semantics
    → behavioral sequence draft

Developer
    → implementation plan
    → управление coding agent
    → production code
    → unit/component/integration tests
    → application delivery boundary

Tester
    → ранняя проверка требований
    → тестируемость и negative paths
    → ручное и exploratory testing
    → acceptance
    → дополнение regression autotests

Technical Change Lead
    → координация change
    → управление зависимостями
    → decision gates
    → approval
    → final acceptance
```

При этом значительная часть непосредственного производства инженерных артефактов делегируется LLM:

- агент помогает аналитику исследовать систему;
- агент формирует draft требований;
- агент формирует draft acceptance scenarios;
- агент строит draft sequence diagrams;
- coding agent пишет production code;
- coding agent пишет автоматизированные тесты;
- отдельная модель выполняет cross-review;
- агент помогает тестировщику формировать дополнительные сценарии и regression tests.

Человек остаётся владельцем результата своей роли.

Ключевой принцип эксперимента:

> **Агент может генерировать артефакт, но ответственность за его смысл, корректность, проверку и принятие остаётся за
человеком соответствующей роли.**

В рамках Experiment 002 я последовательно пройду путь каждой определённой ниже роли и проверю, насколько такая модель
работы оказывается удобной, понятной, управляемой и переносимой на enterprise-команду.

---

## 2. Что проверяет Experiment 002

Experiment 002 не проверяет новую модель хранения требований.

Requirement delta management намеренно остаётся за пределами данного эксперимента и должен быть исследован отдельно,
чтобы не смешивать несколько независимых изменений процесса.

Experiment 002 проверяет:

1. ролевое разделение AI-assisted разработки;
2. ownership инженерных артефактов;
3. change branch как единицу интеграции одной задачи;
4. работу через короткоживущие role branches;
5. передачу ответственности между ролями через Pull Request;
6. возврат задачи предыдущей роли при обнаружении новой неоднозначности;
7. возможность частично расширить границы специализаций без превращения специалистов в универсальных инженеров;
8. влияние такой модели на управляемость, rework, cycle time и фактические трудозатраты change.

## 2.1. Режим проведения: single operator с изоляцией ролей

Experiment 002 проводится одним человеком (оператором эксперимента), который последовательно выполняет все роли:
Technical Change Lead, Functional Analyst, Developer, Tester.

Такой режим не даёт реальных handoff'ов между людьми. Чтобы всё же получить полезный сигнал, вводится **изоляция ролей
**:

1. Каждая роль выполняется в отдельной сессии агента с чистым контекстом.
2. Входом роли являются только артефакты репозитория на зафиксированном commit `change/*` и явные инструкции роли.
   Переписка, рассуждения и промпты предыдущих ролей входом не являются.


Ключевая измеряемая величина single-operator режима — **самодостаточность артефактов**: сколько раз следующая роль не
смогла продолжить работу без внешнего контекста.

### Матрица моделей и контекстов

Для каждой роли до старта фиксируется в каком контексте используется. Требования:

- Coding Agent, Review Agent и агент Tester по возможности используют разные модели или разные семейства моделей;
- агент Tester не должен видеть промпты и переписку Coding Agent;
- Review Agent (cross-model review) не должен быть той же моделью, что писала код.

| Роль                     | Видимый контекст                                                      |
|--------------------------|-----------------------------------------------------------------------|
| Functional Analyst       | репозиторий @ commit                                                  |
| Developer / Coding Agent | approved requirements + implementation plan                           |
| Review Agent             | diff + approved requirements                                          |
| Tester / Test Agent      | requirements + acceptance scenarios + код; без переписки Coding Agent |

## 2.2. Границы применимости выводов

В single-operator режиме эксперимент **может** дать ответы на вопросы:

- достаточны ли артефакты (requirements, acceptance scenarios, sequence, implementation plan) для передачи работы
  следующей роли;
- работают ли ownership-правила и правило возврата через новую analysis branch;
- насколько тяжёл Git/PR-overhead role branches;
- как часто возникают findings, возвраты и decision points;
- какие gates полезны, а какие избыточны;
- какую долю работы реально выполняют агенты.

Он **не может** надёжно ответить на вопросы:

- достаточно ли Junior/Middle уровня для роли Functional Analyst или Tester;
- будет ли Lead или Senior Developer bottleneck в реальной команде;
- какова реальная стоимость координации между людьми;
- дешевле ли команда в деньгах.

Выводы о skill mix и экономике остаются гипотезой до отдельного эксперимента с несколькими участниками (см.
раздел 38).

## 2.3. Как оцениваем ход эксперимента

В этом прогоне нет контрольного change. Фактические трудозатраты, cycle time и время ожидания gates фиксируются как
диагностические данные без порогов и без вывода о выигрыше или проигрыше по скорости и стоимости.

В §33.0 перечислены пять основных показателей. Считаем фактические события за весь change: сколько передач между
ролями вернули на доработку, сколько решений принял Lead, сколько было возвратов к анализу и сколько времени заняли
gates. Например, один возврат из двух передач даёт P1 = 50%; три решения Lead за весь change дают P2 = 3.

Числа в §33.0 уже зафиксированы как ориентиры для итогового разбора. Они не требуют отдельного подтверждения перед
началом анализа и не останавливают эксперимент автоматически. Если во время прогона меняется определение показателя
или ориентир, записываем изменение и причину в журнал.

Если review вернул артефакт или открыт blocking finding, зависимая работа ждёт исправления. Lead может приостановить
весь эксперимент для разбора процесса; причину паузы он записывает в журнал.

---

## 3. Базовая единица работы — Change

Единицей работы является **change**, а не отдельная branch конкретного специалиста.

Для текущего эксперимента:

```text
change/http-api-and-session-middleware
```

Change branch — интеграционная ветка одного изменения.

Она хранит **последнее согласованное состояние change**.

Ни одна роль не должна использовать `change/*` как постоянную персональную рабочую ветку.

Работа выполняется в короткоживущих role branches:

```text
lead/*
analysis/*
dev/*
test/*
platform/*   # только если в scope появляется отдельная platform/infrastructure работа
```

После создания `change/*` Technical Change Lead создаёт от неё короткую `lead/*-setup`. Протокол, change plan, журнал и
принятые входные артефакты готовятся в этой ветке и возвращаются в `change/*` через Pull Request. Commit результата
merge
фиксируется как вход первой role branch. Исключения для прямой работы роли в `change/*` нет.

Каждая role branch:

1. создаётся от актуального состояния `change/*`;
2. содержит работу одной роли или одного конкретного возврата;
3. проходит review;
4. возвращается в `change/*` через Pull Request;
5. после merge может быть удалена.

Модель состояния:

```text
main
    = принятое состояние продукта

change/*
    = последнее согласованное состояние конкретного изменения

role branch
    = незавершённая работа конкретной роли
```

---

## 4. Состав команды

Базовая команда одного change в Experiment 002 состоит из четырёх ролей:

```text
1 Technical Change Lead
1 Functional Analyst
1 Developer
1 Tester
```

Отдельная роль архитектора в эксперименте не вводится.

Functional Analyst обнаруживает функциональные противоречия и вопросы, для которых требуется техническое решение.
Технический и архитектурный анализ распределяется между Developer и Technical Change Lead.

При этом существенные архитектурные решения не должны приниматься разработчиком неявно.

Они должны быть вынесены в decision point и пройти approval Technical Change Lead.

Отдельный DevOps / Platform Engineer также не вводится в базовый состав команды.

Граница Developer расширяется до **application delivery boundary**, но не до полного ownership
enterprise-инфраструктуры.

Если change начинает включать существенную platform/infrastructure работу, отдельная роль DevOps / Platform / SRE должна
быть добавлена явно.

---

## 5. Предполагаемый skill mix

Одна из гипотез эксперимента состоит в том, что AI-assisted процесс может изменить необходимый skill mix команды.

Предварительная модель:

| Роль                       | Предполагаемый уровень                                                       |
|----------------------------|------------------------------------------------------------------------------|
| Technical Change Lead      | Senior / Lead                                                                |
| Developer                  | Senior                                                                       |
| Functional Analyst         | Middle / Strong Junior                                                       |
| Tester                     | Junior / Middle                                                              |
| DevOps / Platform Engineer | отдельная роль при необходимости; уровень зависит от инфраструктурного scope |

Это гипотеза, а не заранее доказанный вывод.

В single-operator режиме (см. 2.1–2.2) эта гипотеза не проверяется: оператор не является представителем Junior/Middle
уровня. В таком режиме фиксируется только то, какие задачи роли потребовали экспертизы выше целевого уровня.

---

# 6. Technical Change Lead

## 6.1. Назначение роли

Technical Change Lead — технический владелец change.

Термин `PM` намеренно не используется, потому что роль требует достаточной технической компетенции.

Technical Change Lead должен понимать:

- архитектуру приложения;
- границы компонентов;
- системные зависимости;
- содержание требований;
- implementation plan;
- технические риски;
- результаты тестирования;
- смысл acceptance evidence;
- последствия принимаемых решений.

Он не обязан самостоятельно создавать все технические артефакты.

Его задача — удерживать изменение целиком.

---

## 6.2. Ответственность при старте change

Technical Change Lead:

- создаёт `change/*`;
- фиксирует исходный commit `main`;
- определяет цель change;
- фиксирует scope;
- фиксирует out of scope;
- определяет роли;
- определяет необходимые role branches;
- задаёт зависимости между работами;
- определяет обязательные артефакты;
- определяет gates;
- задаёт критерий готовности change к merge в `main`;
- создаёт и поддерживает change plan в `project_management`.

Пример:

```text
Change:
change/http-api-and-session-middleware

Исходный commit:
main @ <commit>

Required branches:
- analysis/http-api-initial
- dev/http-api-and-session-middleware
- test/http-api-and-session-middleware

Optional branches:
- lead/http-api-plan-...       # отдельное изменение change plan или решение Lead
- analysis/http-api-find-XXX-...
- platform/http-api-...       # только если возникает отдельный infrastructure scope
```

---

## 6.3. Project Management

В `docs/project_management` должен существовать отдельный план change.

Рекомендуемая структура:

```text
docs/project_management/
└── change_plans/
    └── http-api-and-session-middleware.md
```

Change plan содержит:

- идентификатор change;
- исходный commit `main`;
- текущий статус;
- scope;
- out of scope;
- список ролей;
- список dependent branches;
- зависимости;
- статусы веток;
- blockers;
- findings;
- decision points;
- required artifacts;
- acceptance gates;
- final status.

Change plan является управленческим артефактом Technical Change Lead.

Начальная версия change plan создаётся в setup-ветке Lead и попадает в `change/*` через Pull Request. Следующие
изменения
scope, зависимостей, gates, статусов и решений также выполняются через короткую `lead/*`. Если изменение статуса
непосредственно вызвано role PR, оно может входить в этот PR, но смысл изменения change plan подтверждает Lead. `lead/*`
не является долгоживущей персональной веткой.

---

## 6.4. Работа с решениями

Если любая роль обнаруживает существенную развилку, она не должна выбирать вариант самостоятельно.

Формируется decision point.

Например:

```text
Decision required:

A. Остановить periodic runtime до HTTP draining.
B. Сначала завершить HTTP requests.
C. Выполнять обе стадии конкурентно.

Known consequences:
...

Affected requirements:
...

Affected sequence:
...

Affected implementation cards:
...
```

Technical Change Lead принимает решение либо возвращает вопрос на дополнительный анализ.

---

## 6.5. Approval

Technical Change Lead является последним approver:

- требований;
- значимых архитектурных решений;
- scope implementation plan;
- исключений из первоначального плана;
- итогового change перед merge в `main`.

---

# 7. Functional Analyst

## 7.1. Требуемый профиль

Functional Analyst отвечает за наблюдаемое поведение и публичный контракт change.

Он должен уметь:

- восстанавливать пользовательские и API-сценарии по требованиям, ADR и публичным контрактам;
- описывать назначение endpoints и семантику DTO;
- анализировать наблюдаемое взаимодействие клиента, HTTP boundary и application use cases;
- находить неизвестные и противоречия;
- формулировать функциональные требования;
- описывать happy path, error paths и boundary cases;
- формулировать acceptance scenarios;
- формулировать проверяемые acceptance criteria;
- читать и строить поведенческие sequence diagrams;
- обнаруживать вопросы, требующие технического или архитектурного решения;
- понимать, когда решение выходит за пределы его полномочий.

От Functional Analyst не требуется самостоятельно проектировать component boundaries, middleware ordering, concurrency
или runtime lifecycle. Эти вопросы принадлежат Developer и Technical Change Lead.

Ему необходимо уметь **обнаружить решение, которое требуется принять**, а не обязательно самостоятельно знать правильный
вариант.

---

## 7.2. Работа с агентом

Значительную часть артефактов генерирует LLM.

Модель:

```text
Human Functional Analyst
        ↓
задаёт контекст, ограничения и вопросы
        ↓
Analysis Agent
        ↓
генерирует:
- requirements draft
- acceptance scenario drafts
- behavioral sequence draft
- alternatives
- impact observations
        ↓
Human Functional Analyst
        ↓
проверяет
корректирует
эскалирует decision points
принимает артефакт своей роли
```

Следовательно, формулировка «аналитик пишет требования» означает **ownership требований**, а не обязательное ручное
написание каждого предложения.

---

## 7.3. Ответственность аналитика

Functional Analyst отвечает за:

- выявление требований;
- уточнение поведения;
- happy path;
- error paths;
- negative scenarios;
- acceptance scenarios;
- acceptance criteria;
- draft behavioral/API sequence diagrams;
- impact analysis на уровне наблюдаемого поведения и публичных взаимодействий;
- выявление вопросов, требующих технического или архитектурного решения;
- фиксацию вопросов;
- подготовку вариантов для decision gate;
- исправление требований при возврате с development/test stages.

---

# 8. Acceptance scenarios

Functional Analyst описывает проверяемые сценарии в свободном структурированном формате, без отдельного исполняемого
слоя спецификаций. Для каждого существенного пути фиксируются:

| Поле              | Содержание                                                  |
|-------------------|-------------------------------------------------------------|
| Preconditions     | исходное состояние сессии и runtime                         |
| Request / action  | method, endpoint, headers и body либо lifecycle event       |
| Expected response | HTTP status и response DTO                                  |
| Expected state    | что изменилось или гарантированно не изменилось             |
| Observability     | обязательные события журнала и доступная корреляция         |
| Negative control  | как доказать, что проверяемый путь действительно выполнялся |

Acceptance scenarios уточняют requirements, раскрывают happy path, error paths и boundary cases, служат входом для
sequence diagrams и автоматизированных тестов. Functional Analyst владеет смыслом сценария; Developer и Tester
проверяют техническую реализуемость и тестируемость.

---

# 9. Sequence diagrams

Functional Analyst создаёт draft sequence diagrams наблюдаемого API-поведения. Они показывают взаимодействие клиента,
HTTP boundary и application use cases без самостоятельного проектирования внутренних component boundaries.

Developer уточняет и проверяет технические sequence для middleware ordering, lifecycle, concurrency и shutdown.
Архитектурные развилки передаются Technical Change Lead.

Sequence используется не только как документация, но и как инструмент проектирования.

Процесс:

```text
requirements
    ↓
acceptance scenarios
    ↓
draft sequence
    ↓
обнаружена недостающая развилка?
    ├── нет → review
    └── да
          ↓
      decision point
          ↓
      requirement clarification
          ↓
      sequence update
```

Ключевое правило:

> **Sequence diagram не имеет права самостоятельно вводить новое поведение.**

Если для продолжения диаграммы необходимо выбрать неизвестное поведение, работа останавливается и создаётся decision
point.

На практике агенты нарушают это правило регулярно, поэтому каждый случай введения нового поведения в sequence
фиксируется как agent deviation (см. 33.9). То же относится к implementation plan (раздел 12).

Functional Analyst готовит:

```text
HTTP request lifecycle
Session Middleware
Build API
Place Search API
```

Developer готовит или уточняет технические sequence:

```text
Graceful shutdown
Periodic runtime lifecycle
```

После review и approval sequence становится частью входа разработки.

---

# 10. Approval требований

Requirements не передаются Developer непосредственно после первого draft.

Используется последовательное review:

```text
Functional Analyst
      ↓
requirements + acceptance scenarios + sequence
      ↓
Developer review
      ↓
Tester review
      ↓
Technical Change Lead approval
      ↓
APPROVED
```

---

## 10.1. Developer review

Developer отвечает на вопрос:

> Можно ли это однозначно, безопасно и интегрируемо реализовать?

Проверяет:

- техническую однозначность;
- completeness;
- API contracts;
- ownership состояния;
- lifecycle;
- concurrency;
- error handling;
- интеграционные зависимости;
- нарушение существующих архитектурных границ.

Developer не должен переписывать requirement под удобство реализации.

---

## 10.2. Tester review

Tester отвечает на вопрос:

> Можно ли доказать выполнение этих требований?

Проверяет:

- наблюдаемость expected result;
- negative cases;
- boundary cases;
- тестируемость;
- полноту acceptance criteria;
- покрытие acceptance scenarios;
- требования вида «этого не должно происходить»;
- возможность false-positive проверки.

---

## 10.3. Technical Change Lead review

Technical Change Lead отвечает на вопрос:

> Это действительно то изменение, которое требуется системе, и все ли существенные решения принадлежат человеку, а не
> были неявно добавлены агентом?

После approval requirements и sequence считаются входом разработки.

---

# 11. Developer

## 11.1. Требуемый профиль

Developer в этой модели должен обладать высокой технической компетенцией.

Причина в том, что production code пишет coding agent, а человек-разработчик отвечает прежде всего за:

- корректную декомпозицию;
- implementation strategy;
- интеграцию;
- архитектурные границы;
- технические sequence diagrams;
- review agent diff;
- корректность тестов;
- выявление скрытых решений;
- concurrency/lifecycle;
- application delivery;
- техническую приёмку результата coding agent.

Developer не является просто оператором prompts.

---

## 11.2. Работа с coding agent

Модель:

```text
Human Developer
       ↓
implementation plan
       ↓
implementation prompts
       ↓
Coding Agent
       ↓
production code
automated tests
       ↓
Cross-model review
       ↓
Human Developer
       ↓
validation / correction / acceptance
```

Код агента остаётся зоной ответственности Developer.

---

# 12. Implementation Plan

После approved requirements Developer создаёт implementation plan в `dev/*`. Его изменения возвращаются в `change/*`
в составе Development PR. При возврате из analysis Developer обновляет план в той же активной `dev/*` либо в новой
короткой `dev/*`, если предыдущая уже merged.

Implementation plan должен содержать:

- decomposition;
- порядок работ;
- зависимости;
- allowed scope;
- forbidden scope;
- файлы/компоненты;
- критерии завершения карточек;
- обязательные тесты;
- integration gates;
- blockers;
- связи с findings/decisions.

Ключевое правило:

> **Implementation plan может определять способ реализации, но не имеет права вводить новое системное поведение.**

Если для составления implementation plan требуется принять новое продуктовое или архитектурное решение, работа
возвращается на analysis/decision stage.

Technical Change Lead проверяет implementation plan как минимум на уровне:

- scope;
- dependencies;
- соответствия approved requirements;
- отсутствия неявного расширения change.

---

# 13. Тесты Developer

Coding agent под управлением Developer пишет:

- unit tests;
- component tests;
- integration tests;
- architecture/boundary tests;
- другие автоматизированные проверки, относящиеся к реализации.

Developer отвечает не только за наличие тестов, но и за то, действительно ли они проверяют approved contract.

## 13.1. Связь с Experiment 001: порядок «тест раньше кода»

Experiment 001 проверял порядок «тест раньше кода». В Experiment 002 этот порядок сохраняется как значение по умолчанию:

1. на основе approved requirements и acceptance scenarios coding agent под управлением Developer создаёт исполняемые
   acceptance/component tests **до**
   production code;
2. тесты фиксируются отдельным коммитом в состоянии «красные» до начала реализации;
3. Tester проверяет эти тесты на соответствие requirements и acceptance scenarios до начала реализации (короткий
   review-gate внутри dev stage);
4. production code пишется до прохождения этих тестов; изменение теста ради прохождения без возврата к требованию
   запрещено и фиксируется как agent deviation.

Тем самым Tester после разработки (раздел 16.2) дополняет покрытие, а не создаёт его впервые.

Это решение по умолчанию. Если оператор выбирает другой порядок, отказ от test-first фиксируется в журнале до старта,
иначе результаты Experiment 001 и 002 будут несопоставимы.

---

# 14. Application Delivery Boundary Developer

В Experiment 002 Developer частично расширяет границу ответственности в сторону DevOps, но **не становится полноценным
DevOps Engineer**.

Developer отвечает за application-level delivery concerns:

- application startup/shutdown;
- runtime configuration;
- environment variables на уровне приложения;
- health/readiness behavior;
- локальный контейнерный запуск, если нужен;
- Dockerfile / compose, если они относятся к change;
- CI checks, связанные с кодом change;
- application logging;
- application metrics hooks;
- graceful shutdown semantics;
- migrations/initialization, если они принадлежат приложению;
- требования к deployment environment;
- минимальный runbook на уровне приложения.

Это называется **application delivery boundary**.

---

## 14.1. Что не входит автоматически в ответственность Developer

Developer не получает автоматически ownership:

- Kubernetes cluster;
- ingress;
- load balancers;
- Terraform;
- cloud accounts;
- secrets platform;
- enterprise networking;
- IAM platform;
- central observability stack;
- capacity planning;
- production deployment platform;
- SRE/on-call processes;
- platform-wide CI/CD.

Эти области относятся к отдельной специализации.

Ключевой принцип:

> **Граница Developer расширяется до application delivery, но не до полного platform/infrastructure ownership.**

---

# 15. Когда появляется отдельный DevOps / Platform Engineer

Отдельная роль добавляется, если change требует существенной работы с инфраструктурой.

Например:

```text
Kubernetes deployment
Ingress
TLS
Secrets
Autoscaling
Infrastructure as Code
Production observability
Production CI/CD
IAM
Network policies
```

В этом случае состав команды расширяется:

```text
Technical Change Lead
Functional Analyst
Developer
Tester
DevOps / Platform Engineer
```

Platform Engineer получает свою короткоживущую branch:

```text
platform/http-api-deployment
```

или:

```text
platform/http-api-runtime
```

и работает по тем же правилам:

```text
change/*
    ↓
platform/*
    ↓
PR
    ↓
review
    ↓
merge into change/*
```

Platform Engineer отвечает только за свой infrastructure/platform scope.

Developer при этом остаётся владельцем application contract.

---

# 16. Tester

Tester участвует в change как минимум дважды.

## 16.1. До разработки

Tester выполняет review:

- requirements;
- acceptance scenarios;
- acceptance criteria;
- negative scenarios;
- boundary conditions;
- testability.

Его задача — обнаружить требования, которые невозможно проверить или которые позволяют ложноположительный тест.

---

## 16.2. После разработки

После интеграции dev branch Tester получает отдельную branch.

Tester:

- выполняет ручное тестирование;
- выполняет exploratory testing;
- проверяет happy path;
- проверяет negative paths;
- проверяет boundary conditions;
- проверяет lifecycle;
- проверяет cancellation/shutdown;
- валидирует automated tests Developer;
- добавляет недостающие regression tests;
- проверяет чувствительность тестов;
- формирует acceptance evidence.

---

## 16.3. Разделение ответственности за autotests

Developer:

```text
unit
component
integration
architecture/boundary checks
```

Tester:

```text
acceptance scenarios
manual validation
exploratory testing
missing regression coverage
independent validation
```

Tester не должен просто переписывать тесты Developer.

Его основная задача:

> искать то, что Developer и coding agent не проверили.

## 16.4. Независимость Tester от coding agent

Независимость Tester означает не только другого человека, но и другой источник ошибок.

Требования:

- агент Tester использует модель/семейство, отличающееся от Coding Agent, где это возможно; если это невозможно, это
  фиксируется как ограничение evidence (раздел 29);
- агент Tester не получает промпты, переписку и рассуждения Coding Agent;
- Tester формирует список negative и boundary сценариев из requirements и acceptance scenarios **до** чтения кода
  реализации и только
  затем сверяет его с кодом и тестами Developer;
- совпадение сценариев Tester с тестами Developer не считается независимой проверкой само по себе: фиксируется, какие
  сценарии Tester не были покрыты тестами Developer.

---

# 17. Ownership артефактов

Основное правило:

> **Обнаружение проблемы в артефакте другой роли не даёт права молча изменить его смысл.**

### Functional Analyst владеет:

```text
requirements
acceptance scenarios
acceptance criteria
behavioral/API sequence drafts
analysis findings
```

### Developer владеет:

```text
technical sequence diagrams
implementation plan
implementation prompts
production code
developer automated tests
application delivery artifacts
```

### Tester владеет:

```text
acceptance evidence
manual/exploratory scenarios
test findings
additional regression coverage
```

### Technical Change Lead владеет:

```text
change plan
scope
dependencies
decision gates
approval state
final acceptance
```

### Platform Engineer, если введён:

```text
infrastructure implementation
deployment configuration
platform-specific tests/checks
infrastructure evidence
```

---

# 18. Модель branching

## 18.1. Создание change

```text
main
  │
  └── change/http-api-and-session-middleware
              │
              └── lead/http-api-setup
                         │
                    setup artifacts
                         │
                         PR
                         │
                         ▼
              change/http-api-and-session-middleware
```

Technical Change Lead создаёт `change/*` от зафиксированного `main`, затем выполняет начальную подготовку в
`lead/*-setup`. После merge setup PR отдельные изменения change plan и решения Lead выполняются так:

```text
change/*
    ↓
lead/*
    ↓
Pull Request
    ↓
change/*
```

---

## 18.2. Initial analysis branch

```text
change/http-api-and-session-middleware
            │
            └── analysis/http-api-initial
```

В ветке создаются:

- requirements;
- acceptance scenarios;
- acceptance criteria;
- draft sequence;
- findings;
- decision points.

После завершения:

```text
analysis/*
    ↓
push
    ↓
Pull Request
    ↓
Developer review
    ↓
Tester review
    ↓
Technical Change Lead approval
    ↓
merge
    ↓
change/*
```

После merge branch может быть удалена.

---

## 18.3. Development branch

Development branch создаётся от change branch, содержащей approved requirements.

```text
change/http-api-and-session-middleware
            │
            └── dev/http-api-and-session-middleware
```

Developer выполняет:

```text
implementation plan
    ↓
prompts
    ↓
coding agent
    ↓
code + automated tests
    ↓
cross-model review
    ↓
human developer validation
    ↓
push
    ↓
PR
    ↓
merge into change/*
```

---

## 18.4. Test branch

После интеграции разработки:

```text
change/http-api-and-session-middleware
            │
            └── test/http-api-and-session-middleware
```

Tester выполняет:

```text
manual testing
exploratory testing
test review
regression additions
acceptance evidence
    ↓
push
    ↓
PR
    ↓
merge into change/*
```

---

## 18.5. Optional platform branch

Если появляется отдельный platform scope:

```text
change/http-api-and-session-middleware
            │
            └── platform/http-api-deployment
```

Она также возвращается в `change/*` только через PR.

---

# 19. Возврат между ролями

Процесс не является линейным waterfall.

Передача задачи Developer не означает, что Functional Analyst навсегда завершил участие в change.

Если новая неоднозначность обнаруживается во время разработки, Developer не должен самостоятельно выбирать поведение.

Пример:

```text
Approved requirements:
HTTP requests должны корректно завершаться при shutdown.

Implementation finding:
не определён порядок между periodic runtime shutdown
и HTTP request draining.
```

Developer создаёт Development Finding.

---

# 20. Development Finding

Рекомендуемый формат:

```text
FIND-HTTP-003

Detected by:
Developer

Detected during:
DEV-06 Graceful shutdown implementation

Type:
Missing requirement / architectural decision

Description:
Ordering between periodic runtime shutdown
and HTTP draining is undefined.

Affected requirements:
REQ-HTTP-...

Affected sequence:
graceful_shutdown.puml

Affected implementation cards:
DEV-06
DEV-07

Status:
DECISION REQUIRED
```

Зависимые implementation cards переходят в:

```text
BLOCKED / FIND-HTTP-003
```

Независимая работа может продолжаться.

---

# 21. Повторная Analysis Branch

Старая analysis branch не восстанавливается.

Она уже была принята и merged.

Создаётся новая короткоживущая branch **от актуального `change/*`**:

```text
change/http-api-and-session-middleware
            │
            └── analysis/http-api-find-003-shutdown-order
```

Критически важно:

> **Новая analysis branch создаётся от `change/*`, а не от `dev/*`.**

Причина: незавершённый production code не должен становиться неявным источником требований.

В новой analysis branch:

- исследуется finding;
- уточняются requirements;
- обновляются acceptance scenarios;
- обновляется sequence;
- формируются decision alternatives.

После этого снова выполняется:

```text
Developer review
    ↓
Tester review
    ↓
Technical Change Lead approval
    ↓
merge into change/*
```

Developer затем синхронизирует свою branch с обновлённым `change/*`.

Объём review при повторной analysis branch определяется тиром finding (см. 26.1): полный цикл выше обязателен для T3;
для T1 и T2 применяется соответствующий облегчённый путь.

---

# 22. Обновление Implementation Plan после возврата

Если новое решение изменяет реализацию, Developer обновляет implementation plan.

Последовательность:

```text
development finding
    ↓
analysis return
    ↓
approved requirement clarification
    ↓
sequence update
    ↓
merge into change/*
    ↓
Developer sync
    ↓
implementation plan update
    ↓
coding agent continues
```

Functional Analyst не должен самостоятельно менять implementation plan.

Developer не должен самостоятельно менять semantic requirements.

Ownership сохраняется даже при циклическом процессе.

---

# 23. Возврат с Testing Stage

Если Tester обнаруживает проблему, маршрут зависит от её типа.

### Implementation defect

```text
Tester
    ↓
implementation defect
    ↓
Developer
```

### Missing/ambiguous requirement

```text
Tester
    ↓
requirement finding
    ↓
new analysis branch
```

### Architectural decision

```text
Tester
    ↓
decision required
    ↓
Analysis + Technical Change Lead
```

Таким образом, ownership определяется не стадией процесса, а типом найденной проблемы.

---

# 24. Общий Feedback Loop

```text
ANALYSIS
    ↓
requirements
acceptance scenarios
sequence
    ↓
APPROVAL
    ↓
DEVELOPMENT
    ↓
finding?
    ├── no → continue
    └── yes
          ↓
      classify finding
          ↓
      ANALYSIS RETURN / DECISION / DEV FIX
          ↓
      approval if semantics changed
          ↓
      development continues
          ↓
TESTING
    ↓
finding?
    ├── implementation → Developer
    ├── requirement → Functional Analyst
    └── decision → Lead
```

Передача работы следующей роли не означает окончательного выхода предыдущей роли из change.

---

# 25. Полный Git Workflow

```text
                               MAIN
                                 │
                          create change
                                 │
                                 ▼
              change/http-api-and-session-middleware
                                 │
                     lead/http-api-setup
                                 │
                 protocol / change plan / journal
                                 │
                                PR
                                 │
                         CHANGE BRANCH
                                 │
               fix input commit for Functional Analyst
                                 │
                                 ▼
                      analysis/http-api-initial
                                 │
            requirements / acceptance scenarios / sequence
                                 │
                               PUSH
                                 │
                                 ▼
                                PR
                                 │
                   Developer technical review
                                 │
                     Tester testability review
                                 │
                       Lead final approval
                                 │
                               MERGE
                                 │
                                 ▼
                         CHANGE BRANCH
                    approved requirements
                                 │
                                 ▼
                   dev/http-api-and-session-middleware
                                 │
                      implementation plan
                                 │
                       coding agent work
                                 │
                     automated tests
                                 │
                     cross-model review
                                 │
                               PUSH
                                 │
                                PR
                                 │
                               MERGE
                                 │
                                 ▼
                         CHANGE BRANCH
                                 │
                                 ▼
                  test/http-api-and-session-middleware
                                 │
                   manual / exploratory testing
                                 │
                   automated test validation
                                 │
                     additional regression
                                 │
                               PUSH
                                 │
                                PR
                                 │
                               MERGE
                                 │
                                 ▼
                      CHANGE READY FOR MAIN
                                 │
                          final Pull Request
                                 │
                                 ▼
                                MAIN
```

Отдельное изменение плана или решение Lead после initial setup:

```text
change/*
   │
   └── lead/http-api-plan-...
              │
             PR
              │
            merge
              │
           change/*
```

Возврат:

```text
dev/*
   │
   │ FIND-HTTP-003
   ▼
change/*
   │
   └── analysis/http-api-find-003-...
              │
            review
              │
            merge
              │
           change/*
              │
       synchronize dev/*
```

---

# 26. Правила Merge

## Role branch → change branch

Каждая role branch попадает в `change/*` только через Pull Request.

Прямой merge без review не используется как штатный процесс эксперимента.

### Lead PR требует:

- описание причины изменения change plan или решения;
- список затронутых role branches и blockers;
- подтверждение Lead;
- возврат в analysis, если меняется наблюдаемое поведение или requirements.

### Analysis PR требует:

- Developer review;
- Tester review;
- Technical Change Lead approval.

### Development PR требует:

- проверку соответствия approved requirements;
- успешные обязательные automated checks;
- review реализации;
- отсутствие незакрытого blocking finding;
- Technical Change Lead или назначенный технический approval в соответствии с планом change.

### Test PR требует:

- acceptance evidence;
- отсутствие незакрытых blocking defects;
- фиксацию известных ограничений;
- Technical Change Lead approval на завершение test stage.

## 26.1. Градация gates по типу изменения

Требования раздела 26 к Analysis PR описывают полный путь (первичный analysis и T3). Прогонять полный цикл (новая
branch, Developer review, Tester review, Lead approval) для любой мелкой неоднозначности слишком дорого: это создаёт
overhead и искажает метрики P2 и P5. Поэтому возврат и правка requirements классифицируются по тиру.

| Tier                      | Что меняется                                                                                        | Путь                                | Approval                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------|--------------------------------------------------------------------------------------|
| T1. Clarification         | формулировка, пример, опечатка; наблюдаемое поведение и контракт не меняются                        | короткая analysis branch, лёгкий PR | review одной затронутой роли (Developer или Tester) + асинхронное подтверждение Lead |
| T2. Behavior change       | меняется наблюдаемое поведение внутри одного компонента; архитектурные границы и scope не затронуты | analysis branch, PR                 | Developer review + Tester review + Lead approval                                     |
| T3. Architectural / scope | межкомпонентное поведение, lifecycle, concurrency, scope, существенное решение                      | analysis branch, decision point, PR | полный путь (раздел 21), решение Lead фиксируется явно                               |

Правила классификации:

- тир предлагает роль, обнаружившая finding;
- Lead может повысить тир без объяснений; понижение тира требует подтверждения Lead;
- сомнение между двумя тирами разрешается в сторону более высокого;
- ошибки классификации (finding оказался выше заявленного тира) фиксируются в журнале и учитываются диагностически.

Правила ownership из раздела 17 действуют на всех тирах: лёгкий путь не даёт права молча менять смысл чужого артефакта.

---

# 27. Final Pull Request

Финальный PR:

```text
change/* → main
```

является не обычным code review, а **Change Acceptance PR**.

На этом этапе должны быть доступны:

- approved requirements;
- acceptance scenarios;
- актуальные sequence diagrams;
- implementation plan;
- production code;
- automated tests;
- cross-review results;
- manual/exploratory test evidence;
- known limitations;
- accepted exclusions;
- закрытые findings;
- список открытых non-blocking findings, если такие разрешены;
- итоговое решение Technical Change Lead.

---

# 28. Критерий закрытия Change Branch

Change получает статус:

```text
READY FOR MAIN
```

только если выполнены все обязательные условия:

- все approved requirements реализованы;
- отсутствуют незакрытые blocking requirements;
- отсутствуют незакрытые blocking findings;
- sequence соответствует фактическому потоку;
- implementation plan выполнен либо содержит явно принятые исключения;
- обязательные automated checks проходят;
- unit/component/integration tests проходят в заявленной области;
- Tester завершил manual/exploratory acceptance;
- cross-model review завершён;
- отсутствуют незаявленные архитектурные решения;
- application delivery requirements выполнены;
- документация синхронизирована с реализацией;
- известные ограничения явно зафиксированы;
- Technical Change Lead выполнил final acceptance.

---

# 29. Evidence и предел доказательства

Каждое evidence должно содержать предел своего доказательства.

Например:

```text
2500 tests passed
```

означает:

> определённый набор тестов прошёл в указанном окружении и на указанном commit.

Это не означает:

> система доказанно корректна.

То же относится к:

- cross-model review;
- manual test pass;
- static analysis;
- performance measurements;
- integration checks.

---

# 30. Предполагаемая экономическая модель

Основная экономическая гипотеза состоит не в полной замене специалистов LLM.

Предположение другое:

> **Формализованный AI-assisted процесс может позволить сконцентрировать дорогую инженерную экспертизу в небольшом числе
ролей, а значительную часть производства артефактов делегировать агентам под контролем специалистов более низкого
уровня.**

Предполагаемая дорогая часть команды:

```text
Technical Change Lead
Strong Senior Developer
```

Потенциально более дешёвая часть:

```text
Middle / Strong Junior Functional Analyst
Junior / Middle Tester
```

Но это должно быть доказано экспериментально.

---

# 31. Где должна возникать экономия

Экономический эффект может появиться из двух независимых источников.

## 31.1. Skill mix

Снижается средняя стоимость команды за счёт того, что не каждая роль требует Senior уровня.

## 31.2. Throughput

Агенты берут на себя значительную часть производства:

```text
requirements drafts
acceptance scenario drafts
sequence drafts
implementation
autotests
documentation
cross-review
```

Если команда закрывает больше change за тот же период, стоимость одного принятого change уменьшается.

---

# 32. Риск экономической модели

Более дешёвые роли могут увеличить coordination cost.

Плохой сценарий:

```text
Junior Functional Analyst
       ↓
много вопросов
       ↓
Technical Change Lead

Junior Tester
       ↓
много вопросов
       ↓
Technical Change Lead

Coding Agent
       ↓
сомнительный implementation
       ↓
Senior Developer
       ↓
architecture issue
       ↓
Technical Change Lead
```

В таком случае дорогие роли становятся bottleneck, а потенциальная экономия исчезает.

Поэтому цель эксперимента:

> **не построить максимально junior-команду, а определить минимальный достаточный уровень каждой роли, при котором
стоимость координации и переделок не уничтожает выигрыш от AI-assisted производства.**

---

