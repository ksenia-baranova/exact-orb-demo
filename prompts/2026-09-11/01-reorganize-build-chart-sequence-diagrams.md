# Реорганизация sequence-диаграмм BuildNatal

## Цель

Сделать `docs/sequence_diagrams/build_natal/` единственным действующим
набором диаграмм BuildNatal, явно отделить отложенную модель `BuildAttempt`
и удалить заменённые дубликаты.

## Перед изменениями

1. Прочитай:
   - `AGENTS.md`;
   - `docs/sequence_diagrams/build_charts/README.md`;
   - `docs/sequence_diagrams/build_natal/README.md`;
   - `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`,
     особенно разделы о `BuildAttempt`, CAS и отложенных возможностях;
   - ADR-0012 и ADR-0014.
2. Проверь текущую ветку и `git status`.
3. Сохрани все пользовательские и несвязанные изменения.
4. Не изменяй существующие файлы в `prompts/**`: это исторический журнал.

## Требуемые изменения

1. Расформируй каталог:
   `docs/sequence_diagrams/build_charts/`.

2. Перенеси отложенные сценарии в новый каталог:
   `docs/sequence_diagrams/deferred/build_attempt/`.

   Перенести и при необходимости переименовать:
   - `003-exact_orb_build_chart_disconnect_reopen.puml`;
   - `007-exact_orb_build_chart_failure_reopen.puml`;
   - `009-exact_orb_build_chart_idempotency_duplicate.puml`.

3. Создай в `deferred/build_attempt/` README, который явно фиксирует:
   - это не действующий контракт MVP;
   - `BuildAttempt`, `build_revision`, статусы попытки и клиентский
     `idempotency_key` сейчас не реализуются;
   - durable recovery после reopen отложен ADR-0012;
   - актуальность результата сейчас обеспечивает CAS по `state_version`
     согласно ADR-0014;
   - вернуться к этой модели можно при устойчивом росте расчёта до нескольких
     сотен миллисекунд, появлении асинхронного build либо внешних побочных
     эффектов, требующих отдельной идемпотентности;
   - диаграммы сохранены как проектный материал, а не как описание
     работающего API.

4. Перенеси актуальный транспортный сценарий:
   `004-exact_orb_build_chart_application_unavailable.puml`

   в:
   `docs/sequence_diagrams/build_natal/008-build_natal_application_unavailable.puml`.

   Адаптируй название и пояснения к текущей терминологии BuildNatal:
   - `BuildAttempt` отсутствует;
   - handler и расчётные компоненты не запускаются;
   - состояние сессии не изменяется;
   - это отказ внешнего application/transport-контура до получения
     `BuildNatalOutcome`;
   - не выдавай целевой `ApplicationOrchestrator` или `ApplicationResult` за
     уже реализованный API;
   - не изобретай новый публичный outcome или код ошибки, если он не закреплён
     действующими требованиями.

5. Удали заменённые диаграммы:
   - `001-exact_orb_sequence_build_natal_positive.puml`;
   - `002-exact_orb_sequence_build_cosmogram_positive.puml`;
   - `005-exact_orb_build_chart_resolver_outcomes.puml`;
   - `006-exact_orb_build_chart_calculation_failure.puml`;
   - `008-exact_orb_build_chart_concurrent_latest_wins.puml`;
   - `010-exact_orb_build_chart_state_commit_failure.puml`;
   - `011-exact_orb_build_chart_session_expired.puml`.

   Их действующие аналоги уже находятся в `build_natal/`; не переносить
   устаревшие детали в актуальные диаграммы.

6. Обнови `docs/sequence_diagrams/build_natal/README.md`:
   - добавь сценарий `008 application unavailable`;
   - обозначь его как транспортный отказ до запуска handler;
   - замени ссылку на прежний `build_charts/` ссылкой на новый
     `deferred/build_attempt/`;
   - сохрани различие между реализованным `BuildNatalOutcome` и целевыми
     `ApplicationOrchestrator`, commit-flow и `ApplicationResult`.

7. Исправь ссылки на старую конкурентную диаграмму `build_charts/008`:
   - `docs/sequence_diagrams/session/README.md`;
   - `docs/sequence_diagrams/session/005-compare-and-set.puml`.

   После изменения они должны ссылаться только на:
   `../build_natal/006-build_natal_superseded_cas.puml`.

8. Исправь комментарий в:
   `docs/sequence_diagrams/build_natal/000-build_natal_end_to_end.puml`.

   Он не должен ссылаться на удаляемый README `build_charts`; укажи
   действующий README и ADR-0014.

9. Удали старый `build_charts/README.md` и пустой каталог `build_charts/`.

## Ограничения

- Не изменяй Python-код, тесты, публичные API и вычислительное поведение.
- Не выполняй попутную редактуру других документов.
- Не меняй содержание действующих ADR.
- Не возвращай `BuildAttempt`, `build_revision` или `idempotency_key` в
  текущую архитектуру.
- Не ослабляй формулировку о том, что `ApplicationOrchestrator` и внешний
  `ApplicationResult` ещё не реализованы.
- Не создавай коммит, ветку, push или PR без отдельного указания.

## Проверки

1. Через `rg` убедись, что вне нового deferred-раздела не осталось ссылок на:
   - `sequence_diagrams/build_charts`;
   - `build_charts/`;
   - удалённые имена файлов.
2. Убедись, что действующие документы не представляют `BuildAttempt` как
   текущий контракт.
3. Проверь синтаксис всех перемещённых и изменённых `.puml` доступным
   локальным PlantUML. Не скачивай новые зависимости.
4. Выполни `git diff --check`.
5. Просмотри итоговый `git diff` и `git status --short`.
6. Pytest для чисто документационного изменения не требуется.

## Итоговый отчёт

- Начни с результата.
- Перечисли перемещённые, удалённые и обновлённые файлы.
- Объясни, что `build_natal` теперь является единственным действующим набором.
- Отдельно укажи, что сохранено как deferred.
- Приведи точные команды проверок и их реальные результаты.
- Сообщи, если PlantUML-проверку выполнить не удалось.
