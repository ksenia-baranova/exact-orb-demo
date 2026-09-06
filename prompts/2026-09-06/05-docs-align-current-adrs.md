# Синхронизация документации с действующими ADR

Исправь противоречия внутри документации проекта exact-orb.

Работай только с документацией. Код, тесты, конфигурацию и `prompts/**` не
изменяй, кроме сохранения настоящего файла постановки. Не создавай коммит,
ветку, push или PR. Сохрани все пользовательские и несвязанные изменения
рабочего дерева.

Полностью исключены из задачи — не открывай для редактирования и не изменяй:

- все `docs/architecture/*.puml`;
- `docs/sequence_diagrams/build_charts/test.puml`;
- `docs/requirements/component_responsibilities/exact-orb_applicationOrchestrator_agentOrchestrator.md`.

Файл `docs/requirements/decisions/README.md` входит в задачу и должен быть
синхронизирован с внесёнными изменениями.

Источники истины в порядке приоритета:

1. действующие ревизии ADR;
2. `docs/requirements/component_responsibilities/exact-orb_session_requirements.md`
   для session-контрактов;
3. актуальная реализация и тесты;
4. остальные рабочие документы.

Не создавай новый ADR и не меняй принятые архитектурные решения. Задача —
привести документацию к уже принятым решениям.

## 1. Актуализировать модель сессии

В документах встречается отменённая модель:

- `SessionProfile`;
- `ProfileService`;
- `profile_version`;
- `ContextDelta`;
- `derived_chart`;
- `active_view`;
- `SetActiveView` как часть MVP.

Приведи включённую в задачу документацию к ADR-0009, ADR-0014, ADR-0016 и
`exact-orb_session_requirements.md`:

- `SessionState` вместо `SessionProfile`/`SessionContext`;
- `StateDelta` вместо `ContextDelta`;
- `state_version` вместо `profile_version`;
- `ChartRef.state_version` вместо `ChartRef.profile_version`;
- отдельного `ProfileService` нет;
- применение `StateDelta` и CAS принадлежат `SessionStore`/`ContextService`;
- в первом срезе есть только `base_chart`;
- `derived_chart`, `active_view` и `SetActiveView` в MVP отсутствуют;
- dialog хранится отдельно и не изменяет `state_version`.

Проверь и при необходимости исправь:

- `docs/requirements/overview.md`;
- `docs/requirements/scenarios.md`;
- `docs/requirements/decisions/README.md`;
- `docs/sequence_diagrams/build_natal/README.md`;
- все `docs/sequence_diagrams/build_natal/*.puml`;
- связанные комментарии и подписи в
  `docs/sequence_diagrams/chart_artifacts/*.puml`;
- другие не исключённые документы, представляющие старую модель как действующую.

Не выполняй механическую замену терминов без проверки смысла. Исторические
описания переименований сохраняй и явно обозначай как исторические.

Не изменяй исключённые файлы. Оставшиеся в них старые термины перечисли в
итоговом отчёте как намеренно не исправленные по ограничению задачи.

## 2. Отделить BuildAttempt от действующего MVP

Согласно ADR-0012 и `exact-orb_build_natal_components.md`:

- Build Chart в MVP работает как обычный request/response;
- актуальность записи обеспечивается CAS по `state_version`;
- `BuildAttempt`, `build_revision`, durable recovery, reaper, polling и
  клиентский idempotency key отложены;
- `run_id` — только correlation identifier, не handle возобновления.

Проверь все включённые документы и диаграммы. Сохрани полезное описание будущей
модели, но везде однозначно пометь её как deferred/post-MVP.

Для `docs/sequence_diagrams/build_charts/**`:

- сохрани установленную README-классификацию legacy/deferred;
- не переписывай отложенные сценарии так, будто они входят в MVP;
- не изменяй `docs/sequence_diagrams/build_charts/test.puml`;
- файлы не удаляй.

Не пытайся устранить это противоречие в исключённом документе про
Application/Agent Orchestrator. Укажи его в остаточных ограничениях итогового
отчёта.

## 3. Удалить отменённый backend-контракт подстановки города

В `docs/requirements/scenarios.md` приведи сценарий отсутствующего города к
актуальной ревизии ADR-0005:

- Build API принимает только `place_id`;
- backend не принимает `place_text`;
- `place_substituted` и `place_input_text` отсутствуют;
- warning при отклонении более 0.5° отменён как невычислимый;
- если города нет в каталоге подсказок, форма предлагает пользователю
  самостоятельно выбрать ближайший известный город;
- backend не подбирает ближайший город;
- неизвестный или устаревший `place_id` даёт `InputRequired` для `birth.place`
  с кодом `INVALID`.

Не изменяй отдельно отложенный сценарий повторного использования устаревшего
`place_id` после обновления каталога.

Обнови соответствующую строку или пояснение ADR-0005 в
`docs/requirements/decisions/README.md`, если индекс решений всё ещё отражает
отменённые поля или backend-подстановку.

## 4. Актуализировать статусы реализации

Проверь фактическое состояние по текущему рабочему дереву и исправь устаревшие
утверждения:

- `docs/requirements/roadmap.md` больше не должен утверждать, что package
  `session` отсутствует;
- session contracts, in-memory и SQLite adapters, `ContextService` и связанные
  тесты реализованы;
- application package, `BuildNatalHandler`, `ApplicationOrchestrator` и
  bootstrap по-прежнему отсутствуют;
- `CalculationVersion` по-прежнему отсутствует;
- в `exact-orb_research_corpus.md` укажи, что P5a реализован: contracts,
  projection и InMemory adapter;
- P5b с SQLite research adapter и application producer/wiring остаётся
  отдельной незавершённой задачей;
- в `exact-orb_chart_artifacts.md` убери из текущего списка незакрытого
  утверждение, что `CalculationFailed` отсутствует;
- не утверждай, что в текущем окружении установлены два дистрибутива
  `swisseph`: сейчас используется только `pysweph 2.10.3.6`;
- историческое описание старого benchmark-окружения не переписывай, если оно
  явно обозначено как историческое.

Roadmap можно актуализировать на 2026-09-06. Сохрани обоснования, порядок работ и
оценки; меняй только фактический статус.

Синхронизируй `docs/requirements/decisions/README.md`:

- проверь статусы всех затронутых ADR;
- отрази актуальные ревизии ADR-0005, ADR-0009, ADR-0012, ADR-0014 и ADR-0016;
- сохрани указание, что ADR-0010 заменён ADR-0023;
- проверь статус ADR-0023 и границу P5a/P5b;
- проверь статус ADR-0024 с учётом реализованного SQLite session storage;
- используй актуальные имена `SessionState`, `StateDelta` и `state_version`;
- не представляй `BuildAttempt`, derived state или free-form путь как часть
  текущего MVP;
- не меняй смысл самих решений ради согласования README.

Учитывай, что `docs/requirements/decisions/README.md` уже содержит
пользовательские изменения. Не перезаписывай несвязанные правки.

## 5. Уточнить статус ensure_derived

`docs/sequence_diagrams/chart_artifacts/006-ensure_derived_composition.puml` и
запись о ней в README не должны выглядеть как обязательная часть первого
MVP-среза.

Согласно ADR-0016:

- transits, `derived_chart`, `active_view` и `SetActiveView` исключены из
  первого среза;
- `ensure_derived` относится к последующему multi-chart/derived этапу.

Не удаляй диаграмму. Добавь однозначную пометку «после MVP» или «отложено» в
README и самой диаграмме. Не меняй будущую семантику порядка `bases` или
композиции артефактов.

## Ограничения

- не исправляй кодовые несоответствия C-01–C-11;
- не расширяй задачу до privacy/logging;
- не меняй явно отложенные продуктовые решения;
- не редактируй другие файлы `prompts/**`;
- не редактируй `docs/architecture/*.puml`;
- не редактируй `docs/sequence_diagrams/build_charts/test.puml`;
- не редактируй документ про Application/Agent Orchestrator;
- не выполняй попутный редакторский рефакторинг;
- не удаляй документы и диаграммы.

## Проверки после изменений

1. Через `rg` найди оставшиеся `SessionProfile`, `ProfileService`,
   `profile_version` и `ContextDelta` во включённых документах.
2. Для каждого совпадения определи, является ли оно историческим описанием,
   явно отложенной моделью или ошибочным текущим контрактом.
3. Не считай совпадения в исключённых файлах ошибкой этой задачи.
4. Убедись, что `active_view`, `derived_chart` и `SetActiveView` не представлены
   как поля первого MVP.
5. Проверь, что `place_substituted`, `place_input_text` и порог 0.5° упоминаются
   только как отменённое решение.
6. Проверь, что `BuildAttempt` во включённых документах явно отложен.
7. Проверь согласованность `docs/requirements/decisions/README.md` с
   действующими ADR.
8. Проверь согласованность README и всех изменённых sequence diagrams.
9. Запусти `git diff --check`.
10. Покажи diff только по изменённой документации.
11. Убедись через diff, что три группы исключённых файлов не изменились.

Тесты запускай только если изменение затронуло исполняемые примеры или
проверяемые документальные контракты. Иначе явно укажи, что pytest не запускался
из-за docs-only изменения.

В итоговом отчёте перечисли изменённые документы, устранённые противоречия
D-01–D-05, реальные результаты проверок и оставшиеся намеренные
historical/deferred-упоминания. Отдельно укажи, что D-02 нельзя полностью
устранить из-за запрета менять документ про Application/Agent Orchestrator.
Подтверди, что код, tests, прочие prompts, `docs/architecture/*.puml`,
`build_charts/test.puml` и исключённый component-responsibilities документ не
изменялись.
