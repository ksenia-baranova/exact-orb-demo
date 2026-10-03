# Change development process

**Статус:** DRAFT / WORK IN PROGRESS

**Дата:** 2026-09-30
**Область:** role-based разработка change с участием AI-агентов.

Этот документ описывает рабочий процесс. Принципы метода находятся в
[development-approach.md](development-approach.md), полномочия ролей — в [roles.md](roles.md).

## 1. Цель процесса

Процесс должен:

- сохранить единую точку обсуждения пользовательского намерения;
- не позволить предложению роли незаметно стать решением;
- получить требования, оценку разработки и стратегию тестирования до обещания сроков;
- дать каждой роли собственные артефакты и branch;
- позволить продолжать независимую работу при локальном blocker;
- оставить в репозитории достаточный контекст для следующей роли.

Процесс оптимизируется по качеству handoff и числу предотвращённых ошибок. Количество gates и документов не является
самостоятельной ценностью.

## 2. Базовые понятия

### Change

Change — единица поставки от намерения до принятия. Для неё существуют:

- integration branch `change/*`;
- Change Manager;
- согласованный scope;
- requirements и acceptance scenarios;
- estimates и рабочий план;
- implementation и test evidence;
- единый реестр решений, findings и принятых ограничений.

### Чистовые требования и требования change

Размещение артефактов, форматы `DELTA`/`FULL` и перенос в чистовую редакцию определены в
[правилах требований](../requirements/README.md). Analyst ведёт материалы change в
`docs/requirements/changes/<change-id>/`, чистовой контракт — в `docs/requirements/current/`.
До переноса контракт активного change состоит из зафиксированного нормативного baseline и утверждённых требований
и сценариев change. Developer и Tester получают ссылки на обе части с точными commit.

### Finding

Finding фиксирует наблюдаемую проблему, противоречие, неизвестное или процессный gap. Он объясняет, где проблема найдена,
каким сценарием проявляется и на что влияет. Finding сам по себе не является решением.

### Строка единого реестра решений

Один вопрос хранится в одной строке `DP-*` от статуса `OPEN` до принятого, отложенного, заменённого или отменённого
решения. В этой же строке находятся контекст, варианты, подписанные рекомендации ролей, выбор владельца, основание,
последствия и evidence. Requirements, планы и handoff ссылаются на baseline реестра и `DP-*`, не копируя содержание.

Только строка со статусом `ACCEPTED` и подтверждением владельца может использоваться планом как принятое решение. Для
архитектурного выбора дополнительно требуется связанный ADR.

### Gate

Gate — небольшой набор проверяемых условий перехода. Gate не требует закрывать все вопросы change: только вопросы,
помеченные `blocking` для следующего этапа.

## 3. Состояния change

```text
INTAKE
    ↓
DRAFT
    ↓
ANALYSIS
    ↓
ALIGNMENT
    ↓
READY_FOR_DEVELOPMENT
    ↓
IN_DEVELOPMENT
    ↓
READY_FOR_TEST
    ↓
IN_TEST
    ↓
READY_FOR_ACCEPTANCE
    ↓
ACCEPTED
```

Дополнительные состояния:

- `REVORK` — результат review возвращён ответственной роли с причиной, требуемым исправлением и условием повторной
  передачи;
- `BLOCKED` — следующий обязательный шаг невозможен;
- `PARTIALLY_BLOCKED` — заблокирована часть работ, независимая часть продолжается;
- `DEFERRED` — change отложен с зафиксированным состоянием продолжения;
- `REJECTED` — намерение или результат отклонены владельцем.

## 4. Этап 1. Intake и Draft Change Brief

Change Manager обсуждает намерение с пользователем естественным языком и создаёт Draft Change Brief.

Агент в роли Manager сам читает связанные документы, код и tests, заполняет служебные поля и готовит отдельные задания
Analyst, Developer и Tester. Пользователь сообщает намерение, отвечает на содержательные вопросы и принимает решения, но
не заполняет процессные таблицы вручную. Если делегирование агентам не разрешено или недоступно, Manager передаёт
пользователю готовые ролевые задания для запуска в отдельных задачах.

Минимальное содержание:

- проблема или возможность;
- ожидаемый пользовательский результат;
- предполагаемые границы;
- известные ограничения;
- затронутые части системы;
- неизвестные;
- критерий успеха;
- роли, от которых требуется консультация.

На этом этапе допускаются диапазоны и гипотезы. Точные даты разработки и тестирования не фиксируются без оценок
Developer и Tester.

Если другие роли обнаруживают вопросы к пользовательскому намерению, они передают их Manager. Manager задаёт вопросы
пользователю и сохраняет ответы. Он не заполняет продуктовый пробел собственным предположением.

### Gate G0 — Draft готов к Analysis

- намерение и ожидаемый результат записаны;
- исходный commit `change/*` зафиксирован;
- гипотезы явно отделены от решений;
- названы Analysis-owned deliverables.

## 5. Этап 2. Functional Analysis

Functional Analyst создаёт или уточняет:

- наблюдаемые requirements;
- public/API contract;
- happy, error, boundary и recovery paths;
- acceptance scenarios;
- behavioral/API sequence drafts;
- findings и новые или обновлённые строки `DP-*` в едином реестре;
- impact на существующие сценарии.

Требования записываются в `requirements.md`, сценарии — в `scenarios.md`, findings и handoff — в `analysis.md`
папки `docs/requirements/changes/<change-id>/`. Analyst выбирает `DELTA` или `FULL`, фиксирует исходные нормативные
пути/commit и целевые чистовые пункты. Диаграммы и ADR размещаются в существующих предметных каталогах по
[карте артефактов](../requirements/README.md#размещение-артефактов).

Finding, способный изменить поведение, scope, оценку или архитектуру, описывается развёрнуто по
[шаблону Analyst](artifacts/functional-analyst.md). Короткая строка в индексе findings служит ссылкой, а не заменой объяснения.

Analyst не изменяет Change Plan, Gantt, implementation plan и решение другой роли. В handoff он передаёт Manager:

- manager summary;
- готовые требования;
- идентификаторы blocking строк `DP-*` и baseline единого реестра;
- список non-blocking рисков;
- вопросы Developer и Tester.

### Gate G1 — Analysis готов к консультации

- существенные наблюдаемые пути описаны;
- формат требований, исходный baseline, стабильные IDs и целевые чистовые пути указаны;
- сценарии имеют ожидаемый response, state и observability;
- найденные конфликты оформлены;
- рекомендации подписаны в строках `DP-*`, а поля выбора владельца не заполнены без evidence;
- Analysis artifacts готовы к Developer и Tester review.

## 6. Этап 3. Developer и Tester consultation

После G1 Developer и Tester выполняют независимые review. Их работа может идти параллельно.

### Developer consultation

Developer:

- проверяет реализуемость requirements;
- выявляет технические зависимости и риски;
- предлагает технические варианты;
- проводит необходимые bounded spikes;
- даёт оценку разработки диапазоном и указывает confidence;
- добавляет технические варианты, evidence и рекомендацию в соответствующие строки `DP-*`;
- определяет, какие строки блокируют implementation plan.

Developer не выбирает новую продуктовую семантику и не изменяет requirements молча.

### Tester consultation

Tester:

- проверяет тестируемость требований;
- независимо ищет negative и boundary cases;
- определяет требуемые уровни проверки;
- выявляет недоказуемые acceptance criteria;
- даёт оценку тестирования диапазоном и указывает confidence;
- добавляет testability evidence и рекомендацию в соответствующие строки `DP-*`.

Tester не подтверждает корректность реализации до появления evidence.

### Gate G2 — готово к Manager alignment

- Developer зафиксировал в Implementation Plan оценку реализуемости, dependencies, risks и estimate;
- Tester дал testability review и estimate;
- замечания классифицированы как requirement, technical, test или scope finding;
- для каждого blocking вопроса известен decision owner;
- независимые участки работ отмечены как доступные для продолжения.

## 7. Этап 4. Alignment и утверждение плана

Change Manager собирает Analysis, Developer и Tester input. Он:

1. проверяет, что каждый существенный вопрос представлен одной строкой `DP-*`;
2. собирает в этой строке подписанные рекомендации и передаёт её decision owner;
3. считает выбор принятым только при наличии owner evidence и обновляет статус той же строки;
4. обновляет scope и зависимости ссылками на принятые `DP-*`;
5. принимает оценки ролей без самостоятельной подмены;
6. строит roadmap/Gantt по согласованным контрольным результатам;
7. отмечает confidence, допущения и contingency;
8. получает подтверждение ролей только в их области ответственности.

Согласование не означает единогласное approval каждой строки:

- Analyst подтверждает корректность наблюдаемого контракта;
- Developer подтверждает реализуемость и оценку разработки;
- Tester подтверждает тестируемость и оценку тестирования;
- Manager принимает scope, приоритет, зависимости и delivery plan;
- Technical Reviewer подключается только к явно эскалированному решению.

### Gate G3 — Ready for Development

- Change Plan имеет статус `READY_FOR_DEVELOPMENT`;
- исходные нормативные требования и утверждённые требования/scenarios change имеют согласованные пути и baseline commits;
- оценки Developer и Tester зафиксированы;
- все blocking строки `DP-*` имеют `ACCEPTED` и owner evidence в зафиксированном baseline реестра;
- open non-blocking items имеют владельца и срок пересмотра;
- Gantt соответствует оценкам и зависимостям;
- Developer знает разрешённый scope.

## 8. Этап 5. Development

Developer создаёт implementation plan и выполняет change небольшими проверяемыми шагами.

Implementation plan содержит:

- связь work item с requirement/scenario;
- затрагиваемые компоненты и файлы;
- порядок зависимостей;
- подход к разработке каждого work item и основание выбора: тесты → реализация, реализация → тесты, существующее покрытие или документальные проверки;
- ссылку на исполняемый промт с данными и expected result проверяемых сценариев;
- Developer checks, существующее покрытие и пробелы;
- проверки и критерий завершения;
- известные риски и запреты.

Developer самостоятельно выбирает порядок разработки в рамках согласованного scope и явных указаний пользователя.
Критерии и примеры находятся в [skill Developer](skills/developer/SKILL.md) и
[шаблоне промта](artifacts/developer-prompt.md). TDD не обязателен для каждого work item: выбор должен объяснять,
какой риск снижает ранний тест либо почему достаточно другого способа проверки. Исправленный программный дефект
закрепляется regression-тестом при любом подходе. Если тесты вынесены в следующий промт, work item не готов
к передаче Tester до выполнения обязательных проверок. Независимым test plan и acceptance evidence владеет Tester.

При новом вопросе Developer определяет тип:

| Тип | Действие |
|---|---|
| Implementation defect | исправляет в `dev/*` и добавляет regression test |
| Технический выбор внутри approved contract | принимает и фиксирует Developer |
| Неоднозначное наблюдаемое поведение | создаёт finding для Analyst |
| Изменение scope, оценки или delivery | передаёт Manager |
| Архитектурная/security развилка | эскалирует Manager и Technical Reviewer |

Независимая работа продолжается, если finding блокирует только отдельный work item.

### Gate G4 — Ready for Test

- implementation соответствует baseline requirements;
- Developer checks фактически выполнены;
- diff и ограничения описаны;
- blocking development findings закрыты;
- документация контракта синхронизирована;
- Tester получил reproducible handoff.

## 9. Этап 6. Independent Testing

Tester сначала формирует проверяемые сценарии из требований и acceptance scenarios, затем сравнивает их с реализацией и
Developer tests.

Tester проверяет:

- happy path;
- error, boundary и recovery paths;
- state transitions;
- observability;
- регрессии;
- заявленные ограничения;
- отсутствие ложноположительных tests.

Найденное классифицируется:

- implementation defect → Developer;
- missing/ambiguous requirement → Analyst;
- scope/delivery issue → Manager;
- architectural/security issue → Manager + Technical Reviewer.

До G5 Analyst подготавливает чистовые требования и сценарии в рамках того же change по
[порядку переноса](../requirements/README.md#перенос-в-чистовую-редакцию-при-завершении-change).
Tester сверяет их с утверждённым и проверенным контрактом, проверяет прослеживаемость IDs и ссылок и записывает evidence.
Новая семантика возвращается Analyst и проходит затронутые проверки до повторной передачи на приёмку.

### Gate G5 — Ready for Acceptance

- acceptance evidence связано с requirements;
- обязательные проверки имеют фактические результаты;
- blocking defects закрыты;
- known limitations и accepted risks перечислены;
- непроверенное названо явно;
- чистовая редакция подготовлена, карта переноса Analyst и сверка Tester относятся к её проверенной версии;
- Manager получил итоговый handoff.

## 10. Этап 7. Final Acceptance

Change Manager проверяет соответствие результата согласованному intent и delivery plan. Он не повторяет техническое
тестирование, а проверяет полноту evidence и статус обязательств.

Change получает статус `ACCEPTED`, если:

- scope поставлен либо исключения явно приняты;
- blocking findings отсутствуют;
- решения и риски имеют владельцев;
- Analyst, Developer и Tester завершили handoff;
- перенос требований в `current/` и связанные изменения входят в финальный PR; отложенные пункты явно исключены по решениям владельца;
- change может быть объяснён по артефактам репозитория;
- разрешён final PR `change/* → main`.

Статус `ACCEPTED` и разрешение PR не подтверждают состоявшийся merge. Завершая поставку change, Manager проверяет Git
evidence: в `main` вместе попали реализация, тесты, чистовые требования и связанные документы. Перенос требований не
оставляется отдельной работой после закрытия ветки; при отклонении или отмене change его дельта не применяется к `main`.

## 11. Branching и worktrees

```text
main
  └── change/<change-name>
        ├── manager/<change-name>-...
        ├── analysis/<change-name>-...
        ├── dev/<change-name>-...
        └── test/<change-name>-...
```

Правила:

1. Каждая role branch создаётся от актуального `change/*`.
2. Незавершённая branch другой роли не становится неявным baseline.
3. Role branch возвращается в `change/*` через PR.
4. Один review round исправляется в той же открытой branch/PR.
5. После merge существенное изменение выполняется в новой короткоживущей role branch.
6. Branch показывает происхождение diff, но не заменяет role attribution внутри решения.
7. Commit, push, PR, review reply, approval и merge являются отдельными действиями и отдельно подтверждаются evidence.

## 12. Возврат между ролями

Возврат выполняется к владельцу смысла:

```text
requirement semantics → Functional Analyst
technical implementation → Developer
test evidence → Tester
scope / schedule / delivery decision → Change Manager
architecture / security escalation → Technical Reviewer
```

Minor clarification можно закрыть коротким role PR. Изменение поведения, scope, architecture, concurrency или lifecycle
требует полного review затронутых ролей.

## 13. Журнал и текущий статус

Experiment log хранит хронологию и метрики. Он не дублирует полное содержание requirements, findings и plan.

Текущий статус хранится у владельца:

- delivery status и Gantt — Change Plan;
- requirements status — `docs/requirements/changes/<change-id>/requirements.md`; findings и карта переноса — `analysis.md` рядом;
- implementation status — implementation plan;
- acceptance status — Tester evidence;
- вопрос и принятое решение — одна строка `DP-*` в едином реестре; архитектурный контракт — связанный ADR.

Если два документа заявляют разный текущий статус, это finding. Manager устраняет дублирование либо явно назначает один
источник истины.

## 14. Шаблоны и role skills

- [Artifact templates](artifacts/README.md)
- [Role skill drafts](skills/README.md)
- [Roles and ownership](roles.md)
