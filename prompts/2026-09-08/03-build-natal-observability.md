# Application-слой, P3: наблюдаемость `BuildNatalHandler`

Работай в ветке `feat/build-natal-handler` — той же, что и P1.

Не создавай коммит, не делай push и не включай изменения из других веток.
Сохрани пользовательские и несвязанные изменения рабочего дерева.

`prompts/**` — исторический журнал. Не редактируй старые промты.

## Что уже сделано

P2 реализовал `handlers/build_natal.py` — алгоритм §6–§8 без единого обращения
к `logging` и без `except BaseException`. P2.1 закрыл поведение тестами.

Источник истины — `docs/requirements/exact_orb_build_natal_handler_requirements.md`
(R4), раздел §11 и BH-16, BH-19.

## Цель

Дать операции наблюдаемость, не меняя ни одного исхода: после P3 те же входы
дают те же значения `BuildNatalOutcome` и те же исключения, что и после P2.
Все тесты P2.1 обязаны остаться зелёными без правок.

## Почему `except BaseException` появляется именно здесь

В P2 его не было намеренно: без журнала он не делал бы ничего, кроме
`raise`, и был бы заглушкой. Теперь у него появляется работа — записать
terminal event перед повторным поднятием.

Это единственная причина его существования. Он **не** превращает исключения в
исходы, не подавляет отмену и не меняет то, что уходит наверх.

## Перед изменениями

1. Проверь Git и сохрани все пользовательские и несвязанные изменения.
2. Изучи:
   - §8.3, §8.4, §11, BH-16, BH-19 и §13 требований R4;
   - `birth/resolver.py` — функции `_log_start`, `_log_resolved`,
     `_log_input_required`, `_log_resolution_unavailable`, `_elapsed_ms`:
     это образец стиля;
   - `calculation/engine.py::EngineService._log_failure` — образец записи отказа
     с `exception_type` и без traceback;
   - `calculation/artifacts.py` — что именно уже журналирует артефактный слой;
   - `logging_setup.py`.

## Изменить

```text
src/exact_orb/application/handlers/build_natal.py
```

Больше ничего. Тесты — P3.1.

## Стиль записи

Плоские `%`-строки, как у всех соседей:

```python
LOGGER.info(
    "build_natal_completed run_id=%s outcome=%s chart_kind=%s duration_ms=%.3f",
    run_id,
    outcome,
    chart_kind,
    duration_ms,
)
```

Не вводи `extra={...}`, JSON-логгер и второй формат записи. §11 называет запись
«structured event» в смысле «набор именованных полей», а не в смысле
`logging`-механизма; весь существующий код проекта — плоские `%`-строки, и
тесты журнала будут написаны под них через `caplog` в P3.1.

`LOGGER = logging.getLogger(__name__)` на уровне модуля. Форматирование
аргументов оставляй логгеру: никаких f-строк и конкатенации в вызове.

## Три события

```text
build_natal_started      DEBUG, перед вызовом резолвера
build_natal_completed    типизированный BuildNatalOutcome
build_natal_failed       исключение или отмена
```

За каждым `build_natal_started` следует ровно один terminal event — по любой
ветке, включая исключение и отмену (BH-19).

### `build_natal_completed`

| Исход | Уровень | `outcome` | `chart_kind` |
|---|---|---|---|
| `BuildNatalSuccess` | `INFO` | `success` | обязательно |
| `InputRequired` | `INFO` | `input_required` | отсутствует |
| `ResolutionUnavailable` | `WARNING` | `resolution_unavailable` | отсутствует |
| `CalculationFailed` кроме `ENGINE_UNEXPECTED` | `WARNING` | `calculation_failed` | обязательно |
| `CalculationFailed("ENGINE_UNEXPECTED")` | `ERROR` | `calculation_failed` | обязательно |

Поля: `run_id`, `outcome`, `duration_ms` — обязательны; `chart_kind` — только
после успешного резолва. `error_code` присутствует у
`ResolutionUnavailable` и `CalculationFailed`, отсутствует у
`BuildNatalSuccess` и `InputRequired`.

`ERROR` для `ENGINE_UNEXPECTED` не косметика. По §8.3 этот код означает
замаскированный технический дефект: `EngineService` уже свёл в него любое
неизвестное исключение расчётного стека и сохранил фактический `exception_type`
в своём `calculation_failed`. Уровень `ERROR` — то, по чему дефект вообще можно
найти. Требования к алертингу лежат вне handler (§14.4).

### `build_natal_failed`

| Ситуация | Уровень | Дальнейшее действие |
|---|---|---|
| Неизвестное исключение на любом шаге | `ERROR` | повторно поднять |
| `asyncio.CancelledError` | `WARNING` | повторно поднять отмену |

Поля: `run_id`, `stage`, `exception_type`, `duration_ms`, `cancelled`.

Отмена журналируется на `WARNING`, потому что чаще всего означает закрытое
клиентское соединение, а не аварию системы.

## Перехват — `except BaseException`

```python
except BaseException as exc:
    self._log_failed(run, stage, exc, started_at)
    raise
```

`asyncio.CancelledError` наследуется от `BaseException`, поэтому
`except Exception` его не поймает и terminal event записан не будет.

Это осознанно противоположно решению в `EngineService.calculate`, где
`except Exception` выбран именно чтобы **не** касаться отмены. Не переноси
оттуда шаблон механически.

`raise` без аргументов обязателен во всех ветках. Не логируй и не глотай, не
возвращай `CalculationFailed`, не подменяй тип исключения.

`cancelled` вычисляется как `isinstance(exc, asyncio.CancelledError)`, уровень
выбирается по этому же признаку. В плоскую `%`-строку значение передаётся как
строчная строка `"true"` или `"false"`: передача объекта `bool` через `%s`
дала бы `True`/`False` и разошлась бы с контрактом §11 и тестами P3.1.

## Порядок обработчиков

```python
try:
    ... resolve и build_spec ...
    try:
        artifact = await artifacts.ensure_chart(...)
    except (ChartCalculationError, CalculationUnavailableError) as error:
        outcome = CalculationFailed(error_code=error.code)
        LOGGER: build_natal_completed
        return outcome
    ... build_delta и build_result ...
    LOGGER: build_natal_completed
    return outcome
except BaseException as exc:
    LOGGER: build_natal_failed
    raise
```

Узкий `except` из §8.1–8.2 обязан остаться там, где он стоял в P2: только
вокруг вызова `ensure_chart`, внутри внешнего `try` с `except BaseException`.
Не расширяй его на весь алгоритм: если `ChartCalculationError` неожиданно
поднимет resolver, построение spec, delta или результата, P2 пропускает его
наверх и P3 не должен менять это поведение. При такой вложенности штатный
расчётный отказ всегда даёт `build_natal_completed`, а всё остальное —
`build_natal_failed`.

## `stage`

Локальная переменная, обновляемая перед каждым шагом. Допустимые значения:

```text
resolve  build_spec  ensure_chart  build_delta  build_result
```

Не заводи пять отдельных `try/except` вокруг каждого шага — это размножит
одинаковый обработчик. `build_result` покрывает случай, когда валидатор
`BuildNatalSuccess` отклоняет пару `{artifact, delta}`: это дефект, он уходит
наверх как `ValidationError` и попадает в `build_natal_failed`.

## `duration_ms`

`perf_counter()` перед `build_natal_started`, разница в миллисекундах в каждом
terminal event. Образец — `_elapsed_ms` в `birth/resolver.py`. Не используй
`run.started_at`: он относится к началу всей операции в транспорте, а не к
работе handler.

## Что запрещено журналировать

Дату и время рождения, `place_id`, название места, координаты, `tz_id`,
`canonical_place`, `utc_datetime`, UTC offset, полные `BirthInput`,
`ResolvedBirthData` и `ChartArtifact` (BH-16).

Отдельно: **не записывай `str(exception)`**. Сообщение неизвестного исключения
может содержать персональные входные данные. Пиши только
`type(exc).__name__`. Traceback в structured event не попадает.

`issues[].field` и `issues[].code` из `InputRequired` в событие тоже не
выносятся: перечень проблемных полей — это косвенный слепок ввода, а §11
разрешает только `outcome`.

Cache hit/miss журналирует сам `ChartArtifactResolver`. Не дублируй.

Существующий `BirthDataResolver` пишет `tz_id` на уровне `INFO`. Это принятый
отложенный долг общей политики журналирования birth-блока (§14.3 требований и
раздел про logging/privacy в AGENTS.md). Не исправляй его в этой задаче и не
подавляй чужой логгер.

## Поведение не меняется

После P3:

- те же входы дают те же `BuildNatalOutcome`;
- те же исключения уходят наверх теми же типами;
- отмена по-прежнему не подавляется;
- handler по-прежнему не ставит собственный timeout;
- все тесты P2.1 проходят без правок. Если какой-то из них пришлось изменить —
  это сигнал, что журнал изменил поведение; назови это в отчёте.

## Ограничения

- не изменяй `application/{commands,ports,results}.py`;
- не изменяй `birth/`, `calculation/`, `session/`, `engine/`, `logging_setup.py`;
- не изменяй `BirthDataResolver` и его журнал;
- не изменяй существующие тесты, включая P2.1;
- не пиши тесты журнала — это P3.1;
- не добавляй метрики, счётчики, sampling и алертинг;
- не создавай коммит, push или PR.

## Проверки

```text
pytest tests/application -q
pytest tests/test_module_boundaries.py -q
pytest -q
```

## Итоговый отчёт

- покажи итоговую структуру `handle()` с расположением обработчиков;
- перечисли, какое событие и какой уровень даёт каждая из шести веток
  (четыре исхода, исключение, отмена);
- подтверди отдельной строкой, что ни один тест P2.1 не потребовал правки;
- назови точные команды проверок и их реальные результаты;
- отдельно укажи, что не проверялось, и оставшийся риск.
