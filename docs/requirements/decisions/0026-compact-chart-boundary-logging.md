# ADR-0026. Полный результат карты один раз; внутренние границы используют summary

Дата: 2026-09-09.
**Статус: принято.**

Частично заменяет ADR-0025: отменяется требование полного выходного payload
на каждой внутренней границе. Требование парных boundary-событий и полного
локального диагностического результата сохраняется.

## Контекст

ADR-0025 ввёл полные входящие и исходящие `component_message` для
`BuildNatalHandler`, `BirthDataResolver`, `ChartArtifactResolver`,
`EngineService` и `calculate_natal`. На успешном cache miss одна карта стала
полностью сериализоваться в DEBUG четыре раза:

```text
NatalChart
→ CalculationResult
→ ChartArtifact
→ BuildNatalSuccess
```

Эти копии составляли основную часть интеграционного журнала. На cache hit
оставались полные `ChartArtifact` и `BuildNatalSuccess`. Причина находилась в
общем logging helper: он безусловно сериализовал результат любой границы.

При этом удаление внутренних событий неприемлемо: для локальной диагностики
нужно видеть факт входа и выхода каждого компонента. Также нет необходимости
в новом идентификаторе карты: конкретный запуск уже связывает `run_id`, а
канонический расчёт и его cache hit — `calculation_key`.

## Решение

Каждая реализованная публичная граница продолжает писать парные события
`direction=in|out`, но envelope теперь различает форму payload:

```text
component_message direction=<in|out> operation=<operation>
                  run_id=<id|-> calculation_key=<full key|->
                  status=<ok|error> payload_mode=<full|summary|error>
                  message_type=<type> message=<single-line JSON>
```

Полные входные сообщения без рассчитанной карты сохраняются. Ошибки
записываются компактным полным объектом с `payload_mode=error`.

Успешные выходы распределяются так:

| Граница | Выходной payload |
|---|---|
| `BirthDataResolver.resolve` | полный малый outcome |
| `calculate_natal` | `NatalChartSummary` |
| `EngineService.calculate` | `CalculationResultSummary` |
| `ChartArtifactResolver.ensure_chart` | `ChartArtifactSummary` |
| `BuildNatalHandler.handle` | полный `BuildNatalSuccess` |

Полный `BuildNatalSuccess`, включая `ChartArtifact`, карту и `StateDelta`,
сериализуется в DEBUG ровно один раз на успешный вызов handler. Сериализация
артефакта кодеком для записи в Calculation Cache является отдельной
обязательной операцией и этим ограничением не отменяется.

Summary строится прямым чтением типизированного результата и содержит:

```text
chart_kind, warning_count, body_count, aspect_count,
configuration_count, has_houses, has_strength
```

`ChartArtifactSummary` дополнительно содержит полный `calculation_key`,
`calculation_version` и фактический `cache_outcome`. Полные `bodies`, `cusps`,
`angles`, `aspects`, `configurations`, `strength` и вложенный `chart` во
внутренний summary не входят. Полный результат не сериализуется заранее ради
последующего усечения.

Logging helper принимает явный projector и режим payload. Выбор режима не
зависит от имени класса, размера JSON или поиска полей в уже сериализованной
строке. Глобальный dedup, TTL и mutable-кэш строк не используются.

## Корреляция

`run_id` идентифицирует одну попытку прикладного запроса. Он остаётся явным
аргументом application, birth, artifact и engine границ. В
`calculate_natal()` он не добавляется: диагностический контекст не меняет API
детерминированной функции.

`calculation_key` идентифицирует канонические численно значимые входы,
`ChartSpec` и `CalculationVersion`. Полный ключ записывается отдельным полем в
artifact boundary, успешном terminal event handler и технических событиях
кэша. До вычисления ключа используется `calculation_key=-`.

Engine не получает cache identity. Его события связываются с artifact
resolver по `run_id`. На cache hit новый `run_id` связывается с прежним
`calculation_key`; при single-flight разные waiter `run_id` получают общий
ключ на выходе resolver.

Новый идентификатор результата карты не вводится. `NatalChart`,
`CalculationResult`, `ChartArtifact`, `BuildNatalSuccess`, `ChartRef`, формат
cache payload и семантика ключа не меняются.

## Граница эксплуатации

Полный финальный DEBUG-payload по-прежнему содержит birth-data, координаты,
timezone-данные и весь расчёт. Принятый ADR-0025 privacy-риск локального стенда
сохраняется; настоящее решение уменьшает объём и число копий, но не является
privacy-hardening и не снимает блокер публичного развёртывания.

## Альтернативы

**Оставить четыре полные копии** — отвергнуто: дополнительные копии не дают
новой информации, ускоряют ротацию логов и повторно сериализуют большой граф.

**Удалить внутренние boundary-события** — отвергнуто: исчезает видимость
точной границы отказа или изменения формы сообщения.

**Ввести отдельный UUID карты** — отвергнуто: `run_id` и `calculation_key`
уже покрывают поиск попытки и канонического расчёта, а новый ID потребовал бы
изменения расчётных моделей и cache payload без самостоятельной пользы.

**Передать `calculation_key` в EngineService** — отвергнуто: ключ является
cache identity артефактного слоя; движок не должен знать решение о хранении.

## Последствия

- полный результат остаётся доступен для локальной диагностики один раз;
- все пять границ сохраняют парные входные и выходные события;
- внутренние успешные выходы становятся компактными и пригодными для
  агрегации;
- cache miss, hit, stale, corrupt, put и single-flight можно искать по полному
  `calculation_key`;
- engine flow ищется по `run_id`, без нарушения модульной границы;
- публичные модели, численное поведение и формат Calculation Cache не
  изменяются;
- privacy-hardening остаётся отдельной обязательной задачей перед публичным
  развёртыванием.
