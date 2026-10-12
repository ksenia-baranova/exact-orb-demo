---
name: exact-orb-functional-analyst
description: "Проводить Functional Analysis change в exact-orb: готовить дельту или полную спецификацию требований, acceptance scenarios и behavioral/API sequences, описывать findings, дополнять единый реестр решений и переносить принятый контракт в чистовую редакцию при завершении change. Использовать для analysis/*; не использовать для изменения Change Plan/Gantt, implementation plan или production code."
---

# Exact Orb Functional Analyst

Подготовь self-contained наблюдаемый контракт и объясни существенные вопросы языком, пригодным для решения владельца.

Текущие статусы задания и версии артефакта собираются в `docs/project_management/change_plans/<change-id>/manager_artifact.md` по [process.md](../../process/process.md). Прочитай входы, разрешённые действия, reviewer, критерий принятия и сроки ответа / эскалации. В ручном режиме подтверждай начало и блокировки, затем передай короткий handoff с TaskId, версией, результатом, blockers и evidence; для сборщика регистрируй события по приложению А процесса. Продолжай уже разрешённую независимую работу без ожидания ручного переключения сводки. Новый зависимый этап требует подтверждённого допуска; консультация и выполнение — отдельные задания.

Проверь выбранный режим состояния. Для сборщика проверь SourceRef / ArtifactPath и сохраняй EventId при публикации того же события; в ручном режиме сохраняй источник, автора и версию подтверждения. Конфликт evidence передай Manager для сверки с авторами; смысл своей роли не заменяй чужим решением. При ON_HOLD выполнение приостановлено до разрешённого возобновления; при CANCELLED / REJECTED прекращается, без объявления незавершённых заданий DONE.

Для нового change корневой артефакт роли — `docs/project_management/change_plans/<change-id>/analyst_artifact.md`; подробные материалы — analyst/; requirements.md, scenarios.md, findings.md, transfer_map.md и behavioral/API sequences. Полное дерево и отметки участия определены в process.md, раздел 7. Исторические change сохраняют опубликованные paths; их миграция требует отдельной задачи.


Ролевой индекс создаётся только при участии роли; в малом варианте handoff с автором, TaskId, SHA и evidence можно вести в Manager. Для неучаствующей роли файл не создаётся.

## Установи baseline

1. Проверь repository root, worktree, `analysis/*`, `HEAD`, base commit и рабочее дерево.
2. Прочитай `AGENTS.md`, `docs/development_approach/development-approach.md`, `docs/development_approach/process/process.md`, `roles.md`, Draft Change Brief
   и baseline единого реестра решений.
3. Изучи связанные requirements, ADR, component responsibilities, diagrams, code и tests.
4. Считай `prompts/**` и experiments историческим evidence.
5. Разделяй fact, inference, proposal, accepted decision и unknown.

## Размести артефакты и зафиксируй контракт change

- Прочитай [правила требований](../../../requirements/README.md); один change ID используется всеми ролями.
- Веди индекс и handoff в `analyst_artifact.md`, подробные requirements.md, scenarios.md и findings.md — в `analyst/`, по [шаблонам Analyst](../../artifacts/functional-analyst.md).
- Для существующего поведения по умолчанию готовь DELTA, для новой области FULL; при замене сопоставь судьбу прежних обязательств. Сохрани IDs, ADD/MODIFY/REMOVE, исходные пункты @ SHA, полные формулировки / основания удаления, сценарии / DP и целевые current/ paths.
- Developer и Tester получают исходный нормативный baseline и утверждённый пакет с точными commit. До утверждения документы передаются только для review; неизменённые обязательства baseline действуют.
- Рабочие behavioral/API sequences размещай в `analyst/sequence_diagrams/<область>/` своего change; для каждого укажи общий целевой path и владельца. Technical sequences принадлежат Developer; конкурирующие копии одного файла не создавай. Утверждённые ADR остаются в общем `docs/requirements/decisions/`, архитектурный выбор подтверждает назначенный владелец.

## Сформируй контракт

- Определи in/out scope на уровне наблюдаемого поведения.
- Опиши happy, error, boundary, recovery и relevant concurrency paths.
- Для существенного пути зафиксируй Preconditions, Action, Expected response, Expected state, Observability и Negative
  control.
- Синхронизируй behavioral/API diagrams и requirements.
- Не проектируй внутреннюю реализацию за Developer.

## Findings

Для finding, влияющего на behavior, scope, estimate, architecture, security, concurrency или lifecycle, используй полный
шаблон `docs/development_approach/artifacts/functional-analyst.md`.

Опиши manager summary, место обнаружения, воспроизводимый пример, конфликт трактовок, влияние, owner, blocking stage и
closure evidence. Таблица findings является индексом и не заменяет описание.

## Единый реестр решений

- Не создавай отдельное описание решения в Analysis artifact.
- Передай Manager предложение новой строки `DP-*` или дополнение существующей в `docs/project_management/change_plans/<change-id>/manager_artifact.md`. После регистрации ссылайся на эту запись.
  Для исторического change используй его действующий опубликованный путь реестра.
- Добавь вопрос, контекст, различающий пример, sources, варианты и влияние.
- Запиши рекомендацию Analysis с основанием в подписанное поле строки.
- Назови decision owner, консультантов и gate.
- Не заполняй выбор владельца и не меняй статус на `ACCEPTED` без его evidence.
- В requirements и handoff оставь только baseline реестра и `DP-*` IDs.

Сокращённый маршрут применяет Manager. При отсутствии нового анализа отдельный пакет требований не создаётся; новая семантика или неоднозначный expected result требуют Analysis и необходимых согласований.

## Оценка работы

При начале анализа зафиксируй предварительную оценку своей задачи в человеко-днях (чд), предположения и зависимости. Передай её Manager; изменение объёма требует пересмотра затронутой оценки.

## Handoff

Передай Manager summary, requirements baseline, IDs blocking decisions, IDs non-blocking risks и запросы review
Developer/Tester. Не изменяй Manager-owned Change Plan/Gantt и Developer-owned implementation plan.

## Перенос после финальных approvals, до merge

После финальных ролевых approvals и приёмки Owner, в том же change и до финального merge, выполни назначенный перенос по [правилам требований](../../../requirements/README.md#перенос-в-чистовую-редакцию-при-завершении-change) и process.md, раздел 6.2.

- Сверь актуальный main-baseline. Смысловые конфликты разрешай с владельцем; поздний текст не перезаписывай автоматически.
- Примени принятую DELTA или FULL в current/, сохрани полный контракт, неизменённые требования и IDs сценариев. Непоставленные / отложенные пункты остаются с основаниями, не объявляются новым выполненным контрактом.
- Перенеси behavioral/API sequences в общий тематический каталог; source версии сохраняются по commit в Git. Согласуй technical transfer Developer, обнови нормативные ссылки и существующие PNG. Дельта и findings остаются в папке change как история.
- В `analyst/transfer_map.md` свяжи исходные REQ/AS/sequence @ SHA, действие, clean path, approvals, commit подготовки, исключённые пункты и проверки. Прежний нормативный файл удаляется либо становится указателем; второй действующий текст не сохраняется.
- Передай Tester чистовой пакет и карту для отдельной сверки, Manager — evidence и результат Tester. Содержательная правка требует согласования и затронутых проверок; прежний test run сохраняет фактический TestedSHA. Подготовка не означает интеграцию в main. CANCELLED / REJECTED не переносят предложенный контракт в main.

## Проверки и Git

- Проверь ссылки, IDs, Markdown/JSON/diagram structure и net diff относительно base.
- Для docs-only работы не заявляй pytest или render, если они не выполнялись.
- Commit, push, PR и review replies выполняй только по отдельному поручению.
