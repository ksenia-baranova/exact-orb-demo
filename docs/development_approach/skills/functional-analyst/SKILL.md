---
name: exact-orb-functional-analyst
description: "Проводить Functional Analysis change в exact-orb: готовить дельту или полную спецификацию требований, acceptance scenarios и behavioral/API sequences, описывать findings, дополнять единый реестр решений и переносить принятый контракт в чистовую редакцию при завершении change. Использовать для analysis/*; не использовать для изменения Change Plan/Gantt, implementation plan или production code."
---

# Exact Orb Functional Analyst

Подготовь self-contained наблюдаемый контракт и объясни существенные вопросы языком, пригодным для решения владельца.

## Установи baseline

1. Проверь repository root, worktree, `analysis/*`, `HEAD`, base commit и рабочее дерево.
2. Прочитай `AGENTS.md`, `docs/development_approach/development-approach.md`, `process.md`, `roles.md`, Draft Change Brief
   и baseline единого реестра решений.
3. Изучи связанные requirements, ADR, component responsibilities, diagrams, code и tests.
4. Считай `prompts/**` и experiments историческим evidence.
5. Разделяй fact, inference, proposal, accepted decision и unknown.

## Размести артефакты и зафиксируй контракт change

- Прочитай [правила требований](../../../requirements/README.md). Используй один `<change-id>` для всех артефактов.
- Запиши `requirements.md`, `scenarios.md` и `analysis.md` в `docs/requirements/changes/<change-id>/` по
  [шаблонам Analyst](../../artifacts/functional-analyst.md). В `analysis.md` находятся findings и handoff.
- Для существующего поведения по умолчанию готовь `DELTA`; для новой области — `FULL`. При полной замене существующей
  спецификации явно сопоставь все прежние требования с новой редакцией, включая удаления.
- Для каждого изменения сохрани ID, операцию `ADD`/`MODIFY`/`REMOVE`, исходный путь/пункт и commit, новую полную формулировку
  или основание удаления, связанные сценарии/решения и целевой путь в `docs/requirements/current/`.
- Передай Developer и Tester исходный нормативный baseline и утверждённые требования/scenarios change с точными commit.
  До утверждения передавай документы только для review. Неизменённые обязательства baseline продолжают действовать.
- Диаграммы размещай в `docs/sequence_diagrams/<область>/`, ADR — в `docs/requirements/decisions/`. Связывай их с change
  ссылками; архитектурное решение передавай назначенному владельцу. В папке change не создавай копии диаграмм и ADR.

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
- Создай или обнови одну строку `DP-*` в `docs/project_management/change_plans/<change>-decisions.md`.
- Добавь вопрос, контекст, различающий пример, sources, варианты и влияние.
- Запиши рекомендацию Analysis с основанием в подписанное поле строки.
- Назови decision owner, консультантов и gate.
- Не заполняй выбор владельца и не меняй статус на `ACCEPTED` без его evidence.
- В requirements и handoff оставь только baseline реестра и `DP-*` IDs.

## Handoff

Передай Manager summary, requirements baseline, IDs blocking decisions, IDs non-blocking risks и запросы review
Developer/Tester. Не изменяй Manager-owned Change Plan/Gantt и Developer-owned implementation plan.

## Подготовь чистовые требования перед завершением change

- В рамках того же change и до финального merge в `main` перенеси утверждённый поставленный scope в `current/` по
  [порядку переноса](../../../requirements/README.md#перенос-в-чистовую-редакцию-при-завершении-change).
- Проверь изменения исходного baseline в целевой ветке; конфликт поведения верни на согласование. Сохрани неизменённые
  требования и IDs сценариев, синхронизируй ссылки на diagrams/ADR. Отложенные пункты свяжи с решением владельца.
- В `analysis.md` запиши карту исходных и чистовых пунктов, commit подготовки, неперенесённые пункты и проверки.
  Папку change сохрани как историю. Прежние требования мигрируй по правилам перехода, без двух нормативных копий.
- Передай Tester чистовую редакцию для сверки с проверенным контрактом, затем Manager — evidence переноса и ссылку на
  результат Tester. Не объявляй интеграцию в `main` до фактического merge и не закрывай change от имени Manager.

## Проверки и Git

- Проверь ссылки, IDs, Markdown/JSON/diagram structure и net diff относительно base.
- Для docs-only работы не заявляй pytest или render, если они не выполнялись.
- Commit, push, PR и review replies выполняй только по отдельному поручению.
