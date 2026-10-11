# Roles and ownership

**Статус:** DRAFT / WORK IN PROGRESS
**Дата:** 2026-10-11

Документ описывает полномочия ролей. Порядок стадий находится в [process.md](process/process.md), общие принципы — в
[development-approach.md](development-approach.md).

## 1. Общие правила

1. Роль владеет смыслом своих артефактов и отвечает за их handoff.
2. Finding в чужом артефакте не разрешает молча менять его смысл.
3. Рекомендация роли записывается в её поле единого реестра и становится решением только после действия decision owner.
4. Роль подтверждает только свою область ответственности.
5. Один человек может выполнять несколько ролей, но обязан явно обозначить смену роли.
6. При single-operator режиме новая роль получает репозиторий на зафиксированном commit и явную задачу, а не скрытую
   переписку предыдущей роли.
7. Роль продолжает участвовать после handoff, если новый finding относится к принадлежащему ей смыслу.
8. Роль регистрирует события и evidence в своих материалах. Служебная сводка обновляется по правилам процесса; допуски и решения подтверждают назначенные уполномоченные участники.

## 2. Owner

### Назначение

Owner определяет пользовательское намерение, принимает продуктовые решения и подтверждает итоговую приёмку.

### Владеет

- пользовательским намерением, приоритетом и критериями успеха change;
- подтверждением brief и исходного scope (G0);
- подтверждением scope, бюджета и принятых исключений при допуске реализации (G3);
- продуктовыми решениями в строках `DP-*`, для которых назначен decision owner, включая перенос в техдолг;
- решениями `ON_HOLD`, `CANCELLED` и `REJECTED`;
- итоговой приёмкой либо явным делегированием её Manager.

### Обязан

- подтверждать решения явно, с датой и evidence: молчание не означает approval, приёмку или принятие риска;
- называть границы делегирования Manager и уполномоченного заместителя;
- при совмещении с ролью Manager явно подписывать решения ролью Owner.

### Не уполномочен самостоятельно

- подтверждать test evidence или readiness вместо Tester;
- выбирать внутреннюю реализацию вместо Developer;
- превращать разрешённое исключение в `PASS`.

Совмещение Owner и Manager не считается вторым независимым approval; независимое evidence Tester сохраняется.

## 3. Change Manager

### Назначение

Change Manager является единой точкой обсуждения намерения с Owner и владельцем delivery-процесса change.

### Владеет

- единым `docs/project_management/change_plans/<change-id>/artifacts.md`: brief, сводкой заданий и артефактов, DP, оценками, Change Plan, журналом переходов и приёмкой;
- согласованным delivery plan и его календарём;
- координацией согласованных scope, priorities и dependencies в границах решений Owner;
- единым реестром решений change, его структурой и baseline;
- правилами и корректностью сборки текущих состояний change, заданий и версий артефактов по `process.md`;
- назначением reviewers, критериев принятия, сроков ответа / эскалации, источников по выбранному режиму и допусков по единой таблице gates;
- координацией синхронизации main, классификацией влияния обновления базы и подтверждением отдельного поля поставки; кодовые конфликты и checks назначаются Developer, retest — Tester;
- созданием и ведением общего `docs/project_management/technical_debt.md`, публикацией его изменений отдельными документальными PR в main;
- организацией role consultations;
- организацией final acceptance и фиксацией решения Owner либо явно делегированного Manager;
- отдельной фиксацией разрешённой финальной интеграции.

При завершении change Manager проверяет, что Analyst подготовил чистовые требования, Tester подтвердил их соответствие
проверенному контракту и финальный PR включает этот перенос. Фактическая интеграция подтверждается Git evidence.

### Обязан

- сохранить пользовательское намерение без технической подмены;
- передавать вопросы ролей Owner и фиксировать ответы;
- отделять гипотезы, рекомендации и решения владельца;
- обеспечивать одну строку `DP-*` на вопрос без копий в ролевых артефактах;
- получить оценки от Developer и Tester до утверждения сроков;
- получить необходимые подтверждения по наблюдаемому контракту; для сокращённого маршрута обосновать применимость действующего baseline;
- поддерживать plan как краткий delivery-документ со ссылками на подробные артефакты;
- разрешать продолжение независимой работы при локальном blocker;
- явно фиксировать accepted risk и deferred work.

### Не уполномочен самостоятельно

- определять отсутствующую продуктовую семантику вместо Analyst / Owner;
- подтверждать brief, scope, бюджет и приёмку без явного делегирования Owner;
- выбирать внутреннюю реализацию вместо Developer;
- придумывать оценки разработки и тестирования;
- подтверждать test evidence вместо Tester;
- выдавать recommendation за принятое решение.

### Handoff

Передаёт Analyst утверждённый brief (G0), baseline `change/*` и известные `DP-*`. Передаёт Developer утверждённые
requirements, сценарии, Change Plan и разрешённые work items (G3); Implementation Plan готовит и ведёт сам Developer.
Передаёт Tester requirements, accepted limitations, delivery expectations и проверяемый CandidateSHA (G4). Получает от
каждой роли manager summary и evidence.

## 4. Functional Analyst

### Назначение

Functional Analyst отвечает за наблюдаемое поведение и публичный контракт change.

### Владеет

- functional requirements;
- дельтой или полной спецификацией change и переносом принятого контракта в чистовые требования;
- endpoint/DTO semantics и пользовательскими сценариями;
- acceptance criteria и structured acceptance scenarios;
- behavioral/API sequence drafts;
- analysis findings;
- вопросами, наблюдаемыми вариантами и рекомендациями Analysis в строках единого реестра;
- impact analysis на уровне поведения.

### Обязан

- изучить действующие ADR, requirements, diagrams, code и tests;
- отделить факт, вывод, предложение, решение и неизвестное;
- описать happy, error, boundary, recovery и relevant concurrency scenarios;
- объяснить каждый существенный finding языком, понятным Manager;
- привести конкретный пример проявления;
- добавить варианты, влияние и рекомендацию Analysis в соответствующую строку `DP-*`;
- назвать decision owner и blocking impact;
- синхронизировать наблюдаемые requirements, scenarios и diagrams.

Размещает требования, сценарии и findings по [правилам требований](../requirements/README.md), фиксирует исходный
baseline и целевые пункты. До финальной приёмки подготавливает `current/` и карту переноса со стабильными IDs,
сохраняя неизменённые обязательства и решения об исключениях.

### Не уполномочен самостоятельно

- изменять Change Plan или Gantt;
- утверждать scope, сроки и архитектурные решения;
- выбирать implementation strategy за Developer;
- менять production code и Developer tests в Analysis task;
- записывать предложение как решение Manager/Developer.

### Handoff

Передаёт Manager краткий вывод, readiness status, IDs blocking строк `DP-*` и рисков. Передаёт Developer и Tester approved
requirements, acceptance scenarios и behavioral sequence.

## 5. Developer

### Назначение

Developer отвечает за техническую реализуемость, внутренний дизайн и поставку работающей реализации в рамках approved
contract.

### Владеет

- technical choices внутри approved contract; существенные choices фиксируются строками `DP-*`;
- development estimate и confidence;
- планом реализации и исполняемыми промтами work items;
- выбором порядка разработки и проверок: через тесты или с иной достаточной проверкой;
- technical sequence diagrams;
- production code;
- developer automated tests;
- implementation evidence и development findings.

### Обязан

- проверить требования против текущей архитектуры и кода;
- выявить dependencies, migration и lifecycle risks;
- провести bounded spike, если без него оценка недостоверна;
- дать Manager диапазон оценки, допущения и confidence;
- добавить техническое evidence и рекомендацию Developer в соответствующую строку `DP-*`;
- связать work items с requirements, промтами и tests;
- обосновать для каждого work item выбор TDD или другого подхода через риск и существующее покрытие;
- задать в промте данные, expected result и критерий завершения; избежать лишних тестовых этапов и дубликатов;
- реализовать минимальный scope на ответственном слое;
- добавить regression test для исправленного дефекта;
- по заданию разрешать конфликты кода / Developer tests / конфигурации и выполнять обязательные checks на актуальном CandidateSHA;
- эскалировать новую семантику Analyst, scope Manager, architecture Technical Reviewer.

### Не уполномочен самостоятельно

- менять пользовательское поведение вне approved requirements;
- расширять scope под удобство реализации;
- редактировать Analysis artifact так, чтобы скрыть finding;
- подтверждать acceptance вместо Tester;
- выдавать техническую гипотезу за решение Manager.

### Handoff

До development передаёт Manager Implementation Plan с оценкой реализуемости, dependencies, risks и estimate.
После реализации передаёт Tester diff summary,
reproduction/setup, выполненные checks, ограничения и открытые non-blocking findings.

## 6. Tester

### Назначение

Tester отвечает за независимую проверку testability и evidence соответствия реализации approved contract.

### Владеет

- testability review;
- test estimate и confidence;
- independent test plan;
- manual/exploratory scenarios;
- acceptance evidence;
- test findings и defects;
- дополнительное regression coverage в согласованной области.

### Обязан

- сформировать negative и boundary scenarios до чтения Developer tests, где это возможно;
- проверить, что acceptance criteria наблюдаемы и воспроизводимы;
- отличить collection от успешного test run;
- проверить positive control для существенных негативных утверждений;
- зафиксировать environment, команды и фактические результаты;
- классифицировать проблему по владельцу смысла;
- добавить testability evidence и рекомендацию Tester в соответствующую строку `DP-*`;
- назвать непроверенное и предел evidence;
- вести единый реестр дефектов change в tester.md и выбирать необходимый retest после пересечения обновления базы с поставкой.

Перед финальной приёмкой сверяет чистовую редакцию требований и сценариев с утверждённым и проверенным контрактом,
поддерживает ссылки в матрице и тестах и фиксирует результат сверки в acceptance evidence.

### Не уполномочен самостоятельно

- менять requirement, чтобы реализация прошла;
- подгонять golden data или допуски под текущий результат;
- исправлять production code в роли Tester;
- принимать scope/deferred risk вместо Manager;
- объявлять change принятым без требуемого evidence.

### Handoff

До development передаёт Manager testability review и estimate. После testing передаёт acceptance matrix, команды,
результаты, defects, limitations и readiness recommendation.

## 7. Technical Reviewer

Technical Reviewer — условная роль, подключаемая по эскалации. Она не образует обязательный gate каждого change.

Подключается, когда решение затрагивает:

- архитектурные границы нескольких компонентов;
- security boundary;
- ownership конкурентных или фоновых задач;
- durable processing, network boundary или новый service;
- необратимую migration;
- исключение из действующего ADR или архитектурного invariant.

Reviewer сравнивает варианты и добавляет technical recommendation в строку `DP-*`. Выбор и evidence заполняет только
явно названный decision owner; Change Manager поддерживает baseline реестра.

## 8. Platform Engineer

Platform Engineer вводится только при самостоятельной infrastructure области: deployment, CI/CD, secrets, runtime
supervisor, reverse proxy, observability backend или production operations. Пока эта работа остаётся частью application
delivery boundary, ею владеет Developer.

## 9. Матрица ответственности

| Область | Владелец смысла | Consulted | Approval / evidence |
|---|---|---|---|
| Пользовательское намерение и priority | Owner | Change Manager | Owner; brief ведёт Manager (G0) |
| Change scope и бюджет | Owner | Change Manager, Analyst, Developer, Tester | Owner (G0 / G3) |
| Delivery plan | Change Manager | Analyst, Developer, Tester | Manager; scope и бюджет — Owner |
| Наблюдаемое поведение | Functional Analyst | Developer, Tester, Manager, Owner | Developer — реализуемость; Tester — тестируемость; Owner — продуктовые решения ([process.md §3.2](process/process.md)) |
| Техническая реализация | Developer | Analyst, Tester, Technical Reviewer при эскалации | Implementation Plan — Manager и назначенный reviewer; реализация — Developer evidence |
| Development estimate | Developer | Manager | Developer |
| Подход к разработке и Developer checks | Developer | Tester при необходимости; Manager при влиянии на delivery | implementation plan и промт с обоснованием |
| Стратегия независимого тестирования и test estimate | Tester | Analyst, Developer, Manager | Tester |
| Существенное решение | назначенный decision owner | Manager и затронутые роли | строка `DP-*` со статусом `ACCEPTED`; для архитектуры — связанный ADR |
| Acceptance evidence | Tester | Developer, Analyst | Tester |
| Final acceptance | Owner | Manager, Analyst, Developer, Tester | Owner либо явно делегированный Manager; совмещение ролей явно подписано |

## 10. Role skills и шаблоны

| Роль | Skill draft | Artifact templates |
|---|---|---|
| Owner | — | решения фиксируются в [artifacts.md Manager](artifacts/change-manager.md) |
| Change Manager | [skill](skills/change-manager/SKILL.md) | [templates](artifacts/change-manager.md) |
| Functional Analyst | [skill](skills/functional-analyst/SKILL.md) | [templates](artifacts/functional-analyst.md) |
| Developer | [skill](skills/developer/SKILL.md) | [templates](artifacts/developer.md) |
| Tester | [skill](skills/tester/SKILL.md) | [templates](artifacts/tester.md) |
