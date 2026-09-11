# Промт 5 — полные сообщения всех компонентных границ только в DEBUG

## Контекст

Продолжается поэтапное устранение архитектурной проблемы, выявленной через компонентное логирование `build_natal`.

На предыдущих этапах:

1. исследованы повторяющиеся источники истины;
2. `CalculationResult` нормализован до канонического `chart`;
3. усилены инварианты `EngineService`;
4. нормализован `ChartArtifact`;
5. усилены проверки артефакта, кэша и `calculation_key`;
6. `BuildNatalSuccess` стал агрегатной границей, связывающей:
   - разрешённые данные рождения;
   - спецификацию;
   - рассчитанную карту;
   - версию расчёта;
   - `calculation_key`.

Теперь необходимо завершить компонентную часть работы: обеспечить полный DEBUG-журнал всех сообщений на границах компонентов.

Текущая реализация использует два режима успешного payload:

- `payload_mode=full`;
- `payload_mode=summary`.

В частности, полные результаты внутренних расчётных границ заменяются объектами:

- `NatalChartSummary`;
- `CalculationResultSummary`;
- `ChartArtifactSummary`.

Это мешает диагностировать рассинхронизацию данных непосредственно на той границе, где она появилась. Итоговый `BuildNatalSuccess` показывает конечное противоречие, но summary внутренних сообщений не позволяет точно установить, какой объект фактически вернул каждый компонент.

## Явное изменение решения

Для локального диагностического режима принимается следующее правило:

> Если для component logger включён уровень `DEBUG`, каждое входящее и успешное исходящее `component_message` содержит полный объект сообщения соответствующей публичной границы без summary-проекции и усечения.

Это намеренное изменение требования ADR-0026 о компактных исходящих сообщениях внутренних границ.

Полное логирование разрешено исключительно на уровне `DEBUG`.

На уровнях `INFO`, `WARNING` и `ERROR` полные component payload не должны сериализоваться или записываться.

Документальное оформление замены ADR-0026 будет выполнено отдельным следующим промтом. В рамках текущего этапа разрешена временная рассинхронизация реализации и документации, поскольку пользователь явно разделил компонентные изменения и последующую синхронизацию ADR/requirements.

## Цель

Обеспечить возможность восстановить по DEBUG-журналу полный поток объектов:

```text
BuildNatalCommand
→ ResolvedBirthData
→ NatalChart
→ CalculationResult
→ ChartArtifact
→ BuildNatalSuccess
```

Для каждой публичной границы должны быть видны:

- полный вход;
- полный успешный выход;
- полный структурированный объект ошибки при исключении;
- `run_id`, если он входит в контракт границы;
- `calculation_key`, когда он уже известен;
- фактический тип сообщения.

## Границы компонентов

Полные парные `component_message` должны сохраняться для:

1. `BuildNatalHandler.handle`;
2. `BirthDataResolver.resolve`;
3. `ChartArtifactResolver.ensure_chart`;
4. `EngineService.calculate`;
5. `calculate_natal`.

Для каждой границы должны существовать события:

```text
component_message direction=in ...
component_message direction=out ...
```

## Целевые успешные сообщения

### `BuildNatalHandler.handle`

Вход:

```text
message_type=BuildNatalRequest
payload_mode=full
```

Payload содержит полный `BuildNatalCommand` и `RunContext`. Не добавлять `SessionState` в сообщение и не читать его ради логирования.

Успешный выход:

```text
message_type=BuildNatalSuccess
payload_mode=full
```

Payload содержит полный `BuildNatalSuccess`, `ChartArtifact`, `NatalChart`, `StateDelta`, `BirthInput`, `ResolvedBirthData` и `ChartSpec`.

### `BirthDataResolver.resolve`

Вход использует `message_type=BirthResolutionRequest`, `payload_mode=full` и содержит полный `BirthInput` и доступный `RunContext`.

Успешный выход должен содержать полный фактический outcome: `ResolvedBirthData`, `InputRequired` или `ResolutionUnavailable`. Не заменять `ResolvedBirthData` сокращённым представлением.

### `calculate_natal`

Вход использует `message_type=NatalCalculationRequest`, `payload_mode=full`.

Успешный выход:

```text
message_type=NatalChart
payload_mode=full
```

Payload содержит полный `NatalChart`, включая позиции, дома, управителей, перехваты, аспекты, конфигурации, strength, предупреждения и фактические параметры расчёта.

Удалить использование `NatalChartSummary`.

`run_id` для этой границы остаётся `-`. Не добавлять `run_id` в API детерминированной функции и не использовать скрытое mutable-состояние.

### `EngineService.calculate`

Вход использует `message_type=CalculationRequest`, `payload_mode=full`.

Успешный выход:

```text
message_type=CalculationResult
payload_mode=full
```

Payload содержит полный `CalculationResult`, то есть полный вложенный `chart`.

Удалить использование `CalculationResultSummary`. Не добавлять `calculation_key` в расчётный движок: ключ принадлежит артефактному слою.

### `ChartArtifactResolver.ensure_chart`

Вход использует `message_type=EnsureChartRequest`, `payload_mode=full`.

Успешный выход:

```text
message_type=ChartArtifact
payload_mode=full
```

Payload содержит полный публичный `ChartArtifact`: `calculation_key`, `spec`, `calculation_version` и `chart`.

Не записывать вместо публичного результата внутренний `_EnsuredChart`. Внутренний `_EnsuredChart` может оставаться техническим результатом реализации, но logging projector, если он необходим, должен извлекать полный `ChartArtifact`, а не создавать summary.

Удалить использование `ChartArtifactSummary`. Полный `calculation_key` сохранить в envelope отдельным полем.

Полный артефакт должен логироваться при cache miss, cache hit и результате single-flight waiter. Не менять cache hit/miss/single-flight семантику ради логирования.

## Ошибки

Если компонент завершился исключением, исходящее событие сохраняет:

```text
direction=out
status=error
payload_mode=error
```

Payload ошибки должен содержать полный доступный структурированный объект: `exception_type`, строковое сообщение, `code` и `run_id`, если они существуют.

Не подавлять исключение после логирования. Не преобразовывать runtime-исключения в новые публичные outcomes только ради журнала. Не добавлять traceback внутрь JSON component message.

## Семантика DEBUG

Полный payload разрешено сериализовать только при:

```python
logger.isEnabledFor(logging.DEBUG)
```

Если DEBUG выключен:

- `serialize_component_message` не вызывается;
- полный результат не сериализуется;
- result projector для логирования не вызывается;
- `result_calculation_key` для component message не вычисляется;
- `component_message` не создаётся;
- вычислительное поведение компонента остаётся неизменным.

Не добавлять дополнительный environment flag для полного component logging.

Явным переключателем режима является действующий эффективный уровень логирования `EXACT_ORB_LOG_LEVEL=DEBUG` или эквивалентная программная настройка logger.

Не менять `DEFAULT_LOG_LEVEL`, настройку файловых handlers, ротацию, retention и формат обычных INFO/WARNING/ERROR-событий.

## Envelope

Сохранить однострочный формат:

```text
component_message direction=<in|out>
                  operation=<operation>
                  run_id=<id|->
                  calculation_key=<key|->
                  status=<ok|error>
                  payload_mode=<full|error>
                  message_type=<type>
                  message=<single-line JSON>
```

Для успешного входа и выхода используется `payload_mode=full`, для исключения — `payload_mode=error`.

Режим `payload_mode=summary` больше не должен использоваться в component logging.

Если после изменений он нигде не нужен, удалить `summary` из `PayloadMode` и из публичных параметров logging helpers. Не оставлять мёртвый compatibility-параметр `result_payload_mode`, если все успешные результаты теперь всегда полные.

## Logging helpers

Адаптировать `log_async_component_call`, `log_sync_component_call` и `log_component_message`.

Предпочтительный контракт:

- request всегда логируется полностью;
- успешный result всегда логируется полностью;
- error всегда логируется с `payload_mode=error`;
- необязательный `result_projector` допускается только для преобразования внутреннего результата реализации в полный объект публичной границы;
- projector не должен использоваться для summary или усечения.

Для `ChartArtifactResolver.ensure_chart` допустимо:

```python
result_projector=lambda ensured: ensured.artifact
```

Это не summary, а проекция внутреннего технического wrapper на полный публичный результат метода. `message_type` после такой проекции должен быть `ChartArtifact`.

Для `EngineService.calculate` и `calculate_natal` логировать непосредственно возвращаемые объекты без projector.

## Сериализация

Сохранить следующие свойства `serialize_component_message`:

- детерминированный JSON;
- одна физическая строка;
- `ensure_ascii=False`;
- стабильная сортировка ключей;
- отсутствие усечения;
- поддержка Pydantic-моделей;
- поддержка dataclass;
- поддержка `Enum`, даты, времени, `Path`, `bytes`, множеств и исключений.

Не добавлять ручные списки разрешённых полей. Не маскировать и не удалять поля из полного DEBUG-payload в рамках этого этапа. Не использовать `repr()` вместо структурированной сериализации для поддерживаемых объектов.

## Удаление summary-кода

После перевода границ на полные сообщения удалить ставшие неиспользуемыми функции:

- `_natal_chart_summary`;
- `_calculation_result_summary`;
- `_chart_artifact_summary`;

а также связанные вспомогательные функции, если они больше нигде не используются.

Перед удалением проверить все ссылки через `rg`.

Не удалять обычные компактные INFO-события и CLI summary: это другой вид журналирования, не `component_message`.

Не изменять `_chart_summary` CLI, если он используется для пользовательского или технического INFO/DEBUG-события вне component boundary.

## Обязательные ограничения

В рамках этого этапа:

- не менять расчётные модели;
- не менять `CalculationResult`;
- не менять `ChartArtifact`;
- не менять `BuildNatalSuccess`;
- не менять `StateDelta`;
- не добавлять `artifact_schema_version`;
- не менять `calculation_key`;
- не менять формат cache payload;
- не менять cache hit/miss/corrupt/stale/single-flight поведение;
- не менять численные результаты;
- не менять `ChartSpec`;
- не менять публичные error codes;
- не добавлять зависимости;
- не добавлять сервисы, очереди или сетевые вызовы;
- не менять ADR, requirements, component responsibilities и диаграммы;
- не выполнять privacy-hardening;
- не выполнять попутный рефакторинг;
- не редактировать старые файлы в `prompts/**`;
- не создавать коммит без отдельной команды пользователя.

Сохранить все несвязанные пользовательские изменения и untracked-файлы.

## Обязательные тесты logging helper

Обновить `tests/test_logging.py`.

Проверить:

1. Полный вход сериализуется в однострочный JSON.
2. Полный успешный результат сериализуется без summary projector.
3. `payload_mode=full`.
4. `message_type` соответствует полному результату.
5. Вложенные поля результата действительно присутствуют.
6. Полный `calculation_key` записывается в envelope, если доступен.
7. При выключенном DEBUG сообщения отсутствуют, сериализатор, projector и callback вычисления ключа не вызываются.
8. Исключение записывается с `status=error`, `payload_mode=error`, полным типом и сообщением.
9. Исключение пробрасывается без изменения.

Удалить или переписать тест, утверждающий, что summary не сериализует полный результат: это больше не является действующим контрактом.

## Обязательные тесты `calculate_natal`

Проверить, что успешный выход содержит `payload_mode=full`, `message_type=NatalChart` и полный JSON карты с полями `chart_kind`, `datetime_utc`, `latitude`, `longitude`, `bodies`, `aspects`, `configurations`, `strength` и `warnings`.

Не ограничиваться проверкой отсутствия строки `Summary`.

## Обязательные тесты `EngineService`

Проверить `payload_mode=full`, `message_type=CalculationResult` и наличие полного `chart` с глубокими полями из разных вычислительных блоков.

Удалить ожидания `CalculationResultSummary` и `payload_mode=summary`. Сохранить тесты ошибок и корреляции `run_id`.

## Обязательные тесты `ChartArtifactResolver`

Для cache miss и cache hit проверить `payload_mode=full`, `message_type=ChartArtifact`, полный `calculation_key`, `calculation_version`, `spec`, `chart` и вложенные вычислительные блоки.

Проверить, что в payload не просочился внутренний `_EnsuredChart` как тип публичного сообщения. Сохранить отдельный `calculation_key` в envelope.

Обновить ожидания single-flight, если они проверяют summary, не меняя саму семантику single-flight.

## Обязательные integration-тесты `build_natal`

Для успешного cache miss проверить полные исходящие результаты всех границ:

1. `calculate_natal` → полный `NatalChart`;
2. `calculate_chart` → полный `CalculationResult`;
3. `ensure_chart` → полный `ChartArtifact`;
4. `build_natal` → полный `BuildNatalSuccess`.

Для `BirthDataResolver` проверить полный `ResolvedBirthData`.

Проверить, что UTC datetime, latitude, longitude, `chart_kind`, `house_system`, `calculation_key`, предупреждения и хотя бы один вложенный расчётный блок проходят через последовательность границ без исчезновения.

Для cache hit проверить, что `calculate_natal` и `EngineService.calculate` не вызываются, `ensure_chart` логирует полный кэшированный `ChartArtifact`, handler логирует полный `BuildNatalSuccess`, а cache hit семантика не меняется.

## Положительный контроль исходного дефекта

Добавить тест, доказывающий практическую пользу полного потока. Он должен позволить сравнить `ResolvedBirthData`, `NatalChart`, `CalculationResult.chart`, `ChartArtifact.chart`, `BuildNatalSuccess.artifact.chart` и `BuildNatalSuccess.delta.birth_resolved`.

Проверить одинаковые UTC datetime и координаты в согласованном сценарии. Не создавать противоречивые production-модели ради этого теста.

## Архитектурные границы

Сохранить:

- отсутствие LLM в детерминированном расчётном пути;
- доступ к `swisseph` только через `exact_orb.swiss_backend`;
- отсутствие зависимости `session.state` от `ChartArtifact`;
- отсутствие application imports в расчётном слое;
- opaque `bytes` на границе cache port;
- неизменность публичных расчётных API;
- отсутствие `run_id` в `calculate_natal`.

Не ослаблять `tests/test_module_boundaries.py`.

## Порядок работы

1. Проверить ветку и `git status --short`.
2. Убедиться, что коммит этапа 4 присутствует.
3. Изучить `component_logging.py`, `logging_setup.py`, все пять инструментированных границ, summary helpers, logging tests, integration tests, ADR-0025 и ADR-0026 только как контекст.
4. Найти все использования `payload_mode=summary`, `result_payload_mode`, `result_projector`, `NatalChartSummary`, `CalculationResultSummary` и `ChartArtifactSummary`.
5. Сначала обновить regression-тест, ожидающий полный внутренний результат.
6. Запустить его и подтвердить, что текущая summary-реализация не выполняет новое требование.
7. Минимально изменить logging helper и вызовы компонентов.
8. Удалить только ставший неиспользуемым summary-код.
9. Запустить целевые logging-тесты.
10. Запустить связанные component и integration-тесты.
11. Запустить архитектурные тесты.
12. Запустить полный `pytest`.
13. Выполнить `git diff --check`.
14. Проверить итоговый `git status --short`.
15. Не создавать коммит без отдельной команды.

## Проверки

Запускать поэтапно:

1. `tests/test_logging.py`;
2. тесты `calculate_natal`;
3. `tests/test_calculation_engine.py`;
4. `tests/test_calculation_engine_integration.py`;
5. `tests/test_chart_artifact_resolver.py`;
6. `tests/application/test_build_natal_logging.py`;
7. `tests/application/test_build_natal_integration.py`;
8. `tests/test_calculation_block_integration.py`;
9. `tests/test_module_boundaries.py`;
10. полный `pytest`;
11. `git diff --check`.

Не запускать сетевые или платные smoke-тесты. Не объявлять успешными проверки, которые фактически не запускались.

## Критерии готовности

Работа завершена, когда:

- все пять публичных границ имеют парные DEBUG-сообщения;
- все входящие и успешные исходящие сообщения полные;
- `NatalChartSummary`, `CalculationResultSummary` и `ChartArtifactSummary` больше не используются;
- `payload_mode=summary` отсутствует в component logging;
- успешные сообщения используют `payload_mode=full`;
- ошибки используют `payload_mode=error`;
- полный объект сериализуется только при включённом DEBUG;
- при выключенном DEBUG отсутствуют сериализация, projector и вычисление logging-only ключа;
- `ChartArtifactResolver` логирует публичный `ChartArtifact`, а не внутренний wrapper;
- `run_id` и `calculation_key` сохраняют действующую корреляционную семантику;
- cache hit/miss/single-flight поведение не меняется;
- расчётные модели и численные результаты не меняются;
- `artifact_schema_version` не вводится;
- документация в этом этапе не изменяется;
- целевые, связанные, архитектурные и полные тесты проходят.

## Итоговый отчёт

В конце предоставить:

1. корневую причину недостаточной наблюдаемости;
2. список границ, переведённых с summary на full;
3. окончательный контракт `payload_mode`;
4. подтверждение, что полная сериализация выполняется только при DEBUG;
5. описание полного payload каждой границы;
6. поведение ошибок;
7. поведение cache hit и cache miss;
8. список удалённых summary helpers;
9. список изменённых файлов;
10. точные команды тестов и фактические результаты;
11. что не проверялось;
12. оставшиеся ограничения;
13. подтверждение, что модели, ключ, кэш, ADR и requirements не изменялись;
14. явное указание, что синхронизация ADR-0025, ADR-0026, requirements и диаграмм отложена до отдельного документационного этапа.
