# Sequence diagrams — построение натальной карты

Диаграммы совмещают реализованный application core с целевыми transport/client
участками, зафиксированными в
`docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`
и [требованиях ApplicationOrchestrator](../../requirements/component_responsibilities/exact-orb_application_orchestrator_requirements.md),
а также ADR-0006, 0012, 0014, 0017, 0020. `ApplicationOrchestrator`, commit-flow,
один точный retry, cancellation/lifecycle semantics и внешний
`ApplicationResult` реализованы и подтверждены тестами. HTTP API, session
bootstrap, client rendering и production admission остаются целевым контуром.

Ключевое отличие от [отложенной модели](../deferred/build_attempt/README.md):
`BuildAttempt`, `build_revision` и статусы попытки не используются.
Актуальность результата обеспечивается compare-and-set по `state_version`
внутри `SessionStore` (ADR-0014), durable recovery незавершённого build
отложена (ADR-0012).

| № | Файл | Сценарий | Исход |
|---|---|---|---|
| 000 | `000-build_natal_end_to_end.puml` | Сквозной путь одной операции | `ApplicationCommitted`; HTTP/client участки остаются целевыми |
| 001 | `001-build_natal_positive_cache_miss.puml` | Первое построение, промах кэша | `ApplicationCommitted` |
| 002 | `002-build_natal_cache_hit.puml` | Повтор с теми же данными | `ApplicationCommitted`, движок не вызван |
| 003 | `003-build_cosmogram_time_unknown.puml` | Пустое поле времени | `ApplicationCommitted`, `chart_kind = cosmogram`, устойчивые аспекты + `time_uncertainty` |
| 004 | `004-build_natal_input_required.puml` | Неизвестный `place_id`; несуществующее или удвоенное локальное время | `ApplicationInputRequired` |
| 005 | `005-build_natal_technical_failures.puml` | Отказ зависимости резолва; отказ движка | `ApplicationResolutionFailure`, `ApplicationCalculationFailure` |
| 006 | `006-build_natal_superseded_cas.puml` | Два конкурентных построения в одной сессии | `ApplicationSuperseded` |
| 007 | `007-build_natal_commit_failure_and_session_expired.puml` | Store недоступен при commit; session исчезла при commit | `ApplicationStateCommitFailure`, `SESSION_LOST_DURING_OPERATION` |
| 008 | `008-build_natal_application_unavailable.puml` | Routing или load отказал до запуска handler | `ApplicationInternalFailure`; `BuildNatalOutcome` не получен |
| 009 | `009-build_natal_commit_cancellation.puml` | Отмена request после начала commit | Commit классифицируется и логируется до `CancelledError` |
| 010 | `010-build_natal_application_observability.puml` | Lifecycle-события Orchestrator | Started, stage/commit-attempt events и ровно один terminal event |

Диаграммы `000`–`010` показывают реализованные ветви `ApplicationResult` и
защищённого commit-flow. `000` соединяет их с ещё целевыми HTTP/client
участками, а остальные файлы разбирают отдельные application-сценарии.
Транспортная диаграмма `008` заканчивается отказом до запуска handler и поэтому
не получает `BuildNatalOutcome`. Реализованный контракт handler заканчивается
на `BuildNatalOutcome`.

Routing выполняется до load. `007` показывает не более одного точного повтора
после `StateCommitFailed` с original expected и той же delta; отмена или
истёкший deadline запрещают начинать повтор. `009` фиксирует observable
порядок защищённой commit-стадии; одного `asyncio.shield()` без ожидания inner
task недостаточно. `010` фиксирует observability-поток: Orchestrator пишет
события только о стадиях application-flow, не копирует payload компонентов и
не хранит registry активных `run_id` между вызовами.

## Общие инварианты действующего BuildNatal-flow

- **Agent Runtime не запускается.** `Planner`, `ScenarioRegistry`,
  `ToolExecutor` и LLM на build-пути отсутствуют (ADR-0012, ADR-0020).
- **Техническая ошибка не становится `InputRequired`** — инвариант B-1.
- **`Success` только после подтверждённого commit** — успешный расчёт
  не равен успешной пользовательской операции (ADR-0006).
- **`Calculation Cache` не является пользовательским состоянием:**
  корректный, но устаревший для сессии артефакт остаётся в кэше (ADR-0017).
- **Движок возвращает `CalculationResult`, а кэш хранит `bytes`:**
  `ChartArtifact` собирает только `ChartArtifactResolver`.
- **Boundary-журнал показывает полный сквозной объектный поток:** по
  ADR-0025/0028 все пять границ пишут полные входы и фактические выходы только
  на DEBUG. Конкретный запуск ищется по `run_id`, артефакт и cache hit — по
  полному `calculation_key`; ниже DEBUG payload не сериализуется.
- **Orchestrator пишет lifecycle-события:** один started, завершённые стадии,
  каждую начатую commit attempt и ровно один terminal event. Эти компактные
  записи не содержат command payload, артефакт или полный `session_id`.
- **Результат нормализован:** `CalculationResult` содержит только chart, а
  `ChartArtifact` — key, spec, calculation version и chart. Сквозной validator
  связывает resolved birth data, spec, chart, key и итоговый delta (ADR-0027).

## Рендер

```
java -jar plantuml.jar -tpng -o out *.puml
```

Базовый набор ранее проверен на PlantUML 1.2024.7. Статусные изменения 10.8
не меняют последовательности сообщений; структурная проверка выполнена.
Java и PlantUML jar в окружении 10.8 не найдены, поэтому повторный рендер и
визуальная проверка PNG не выполнялись.
