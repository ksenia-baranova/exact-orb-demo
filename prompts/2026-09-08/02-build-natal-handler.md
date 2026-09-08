# Application-слой, P2: `BuildNatalHandler` без журнала

Работай в ветке `feat/build-natal-handler` — той же, что и P1.

Не создавай коммит, не делай push и не включай изменения из других веток.
Сохрани пользовательские и несвязанные изменения рабочего дерева.

`prompts/**` — исторический журнал. Не редактируй старые промты.

## Что уже сделано

P1 создал `exact_orb.application` с `commands.py`, `ports.py`, `results.py`.
P1.1 закрыл их контрактными тестами. `handlers/build_natal.py` не существует,
`handlers/__init__.py` пустой.

Источник истины — `docs/requirements/exact_orb_build_natal_handler_requirements.md`
(R4). Ссылки «§6», «BH-9» указывают на него.

## Цель

Реализовать координатор одного use case: от `BirthInput` до
`{ChartArtifact, StateDelta}`, с типизированными исходами вместо исключений на
границе. Единственное предметное решение модуля — выбор между натальной картой
и космограммой.

## Граница P2 и P3: журнала в этом промте нет

**В `build_natal.py` не должно быть ни одного обращения к `logging`.** Ни
`LOGGER = logging.getLogger(__name__)`, ни импорта `logging`, ни единого вызова.
Журнал целиком принадлежит P3.

Из этого следует второе, менее очевидное: **в P2 не должно быть
`except BaseException`**. Единственная причина его существования — записать
terminal event перед повторным поднятием (§11). Пустой `except BaseException:
raise` без журнала не делает ничего и является заглушкой будущей
функциональности, которую AGENTS.md прямо запрещает.

Поэтому P2 реализует только узкие `except` из §8.1–8.2, а P3 обернёт метод
внешним обработчиком и добавит три события. Не пытайся «подготовить место» для
P3 пустыми блоками, комментариями-заглушками или неиспользуемыми переменными
`stage` и `started_at`.

Инвариант BH-19 и критерий §13 «каждый прогон имеет terminal event» в P2 не
проверяются: без журнала их нечем удовлетворить.

## Перед изменениями

1. Проверь Git и сохрани все пользовательские и несвязанные изменения.
2. Изучи:
   - §4, §6, §7, §8, §9 и §10 требований R4;
   - `sequence_diagrams/build_natal/001`–`005`;
   - ADR-0008 (правило natal/cosmogram) и ADR-0014;
   - созданные в P1 `application/{commands,ports,results}.py`;
   - `birth/resolver.py` — какие ровно исходы он производит;
   - `calculation/artifacts.py` — какие ровно исключения поднимает
     `ensure_chart`;
   - `calculation/errors.py`, `calculation/spec.py`, `domain.py`
     (`normalize_include`, `DEFAULT_INCLUDE_BY_CHART_KIND`);
   - `session/state.py` — `StateDelta`.
3. Существенные противоречия не разрешай молча: назови конфликт в отчёте.

## Создать

```text
src/exact_orb/application/handlers/build_natal.py
```

Больше ничего. Тесты — P2.1.

## Контракт модуля

```python
class BuildNatalHandler:
    def __init__(
        self,
        *,
        resolver: BirthDataResolverPort,
        artifacts: ChartArtifactPort,
    ) -> None:
        ...

    async def handle(
        self,
        command: BuildNatalCommand,
        state: SessionState,
        run: RunContext,
    ) -> BuildNatalOutcome:
        ...
```

Зависимости — только два порта из `application/ports.py`. Никаких значений по
умолчанию, никакой ленивой сборки зависимостей внутри, никакого доступа к
глобальному состоянию.

## Алгоритм

### Шаг 1. Разрешить данные рождения

```python
resolution = await self._resolver.resolve(command.birth_input, run=run)
```

- `InputRequired` и `ResolutionUnavailable` возвращаются **тем же объектом**,
  без пересборки, копирования, дополнения полей и изменения типа (§7.1, §7.2);
- различай исходы через `isinstance`, а не через утиные проверки полей;
- при неуспешном резолве артефактный порт не вызывается вообще (BH-2). Это
  должно следовать из структуры кода — ранний возврат, а не флаг.

### Шаг 2. Определить вид карты

```python
chart_kind = "cosmogram" if resolution.time_unknown else "natal"
```

Источник решения — `resolved.time_unknown`, установленный резолвером.
`command.birth_input.birth_time` повторно не проверяется (BH-3, BH-4, BH-6).
Отсутствие времени — завершённый ввод, а не повод для `InputRequired` (BH-5).

### Шаг 3. Построить спецификацию

```python
spec = NatalChartSpec(chart_kind=chart_kind)
```

Канонический `include` приходит из существующего контракта `NatalChartSpec`
через `DEFAULT_INCLUDE_BY_CHART_KIND`. Не перечисляй блоки руками, не вызывай
`normalize_include` и не дублируй правила «`rulers` требует `houses`».
Проверяется итоговое значение спецификации, а не способ её создания (§6 шаг 3).

### Шаг 4. Получить артефакт

```python
try:
    artifact = await self._artifacts.ensure_chart(spec, resolution, run=run)
except (ChartCalculationError, CalculationUnavailableError) as error:
    return CalculationFailed(error_code=error.code)
```

- `except` охватывает **только** вызов `ensure_chart`, а не весь метод;
- ловятся ровно два класса, а не общий базовый `ArtifactError`: базовый класс
  проглотил бы будущие подтипы, которые по §8.3 обязаны оставаться видимыми;
- оба преобразуются одинаково — `CalculationFailed(error_code=error.code)`.
  Не переписывай код ошибки, не добавляй `retryable`, не расширяй outcomes;
- cache hit и cache miss неразличимы для handler (BH-17). Не пытайся их
  выяснить по счётчикам резолвера или по времени вызова.

### Шаг 5. Сформировать дельту

```python
delta = StateDelta(
    birth_input=command.birth_input,
    birth_resolved=resolution,
    base_chart_spec=spec,
)
```

Только после успешного получения артефакта (BH-9). В дельту не входят
`calculation_key`, сам артефакт, рассчитанная карта, байты кэша, `state_version`
и `ChartRef` (§6 шаг 5).

### Шаг 6. Вернуть исход

```python
return BuildNatalSuccess(artifact=artifact, delta=delta)
```

Согласованность пары проверяет валидатор модели из P1. Не дублируй его
отдельными `if` внутри handler (§5).

## Предупреждения не трогаются

`ResolvedBirthData.warnings` уезжают внутри `delta.birth_resolved`,
`ChartArtifact.warnings` — внутри `artifact`. Handler их не читает, не
объединяет, не переводит и не выносит в отдельное поле (§6 шаг 5).

## `state` не используется

Параметр `state` присутствует ради единого интерфейса `Handler` и будущих
проверок. В P2 handler:

- не читает его поля;
- не проверяет `expires_at`, `hard_expires_at`, `state_version`, `base_chart`;
- не сравнивает `state.birth_input` с командой;
- не вызывает `apply_delta`, `touched`, не создаёт `SessionState` и `ChartRef`;
- не передаёт `state` ни в один нижележащий вызов (BH-10, BH-11, §4.2).

Имя параметра остаётся `state` — оно часть протокола `Handler`. Не переименовывай
в `_state` и не добавляй `del state`.

## Тайм-ауты и отмена

- handler не устанавливает собственный timeout ни на `resolve`, ни на
  `ensure_chart`: ни `asyncio.wait_for`, ни `asyncio.timeout`, ни ручных
  таймеров (§8.4);
- `asyncio.CancelledError` в P2 не перехватывается вообще — узкий `except` из
  шага 4 его не ловит, потому что `CancelledError` наследуется от
  `BaseException`;
- handler не пытается отменить single-flight leader внутри
  `ChartArtifactResolver`. Продолжение защищённой задачи после отмены waiter —
  ожидаемая семантика `asyncio.shield`, а не утечка.

## Исключения резолвера

Любое исключение из `BirthDataResolverPort.resolve` в P2 просто уходит наверх:
`try` вокруг шага 1 не ставится. Оно не преобразуется ни в `InputRequired`, ни
в `ResolutionUnavailable`, ни в `CalculationFailed` (§7.3).

## Прямые импорты модуля

Разрешено импортировать:

```text
exact_orb.application.commands
exact_orb.application.ports
exact_orb.application.results
exact_orb.outcomes
exact_orb.run_context
exact_orb.session.state
exact_orb.calculation.spec
exact_orb.calculation.errors
```

Запрещено объявлять прямые импорты из `exact_orb.calculation.artifacts`,
`.cache`, `.codec`, `.engine`, `.keys`, `.version`, `exact_orb.birth.resolver`,
`exact_orb.engine`, `exact_orb.swiss_backend`, `exact_orb.ephemeris_runtime`,
`exact_orb.session.store`, `.context`, `.persistence`, `.adapters`,
`exact_orb.intent`, `.interpretation`, `.llm`, `.orchestration`, `.tools`,
`.cli`, `.config` (§10.1).

Обрати внимание на `exact_orb.birth.resolver` и `exact_orb.calculation.artifacts`:
конкретные реализации портов приходят через конструктор, импортировать их в
модуле handler нельзя. `exact_orb.calculation.types` намеренно не запрещён, но
handler в нём не нуждается: тип артефакта выводится из порта.

Автоматическая проверка этого списка появится в P4. В P2 соблюдай его вручную.

## Зафиксировать, но не реализовывать в P2

- журнал, `except BaseException`, `stage`, `duration_ms` — P3;
- любые тесты — P2.1;
- `APPLICATION_BUILD_NATAL_FORBIDDEN_DIRECT_IMPORTS` — P4;
- `ApplicationOrchestrator`, commit, CAS, `ChartRef`, классификация
  `AlreadyApplied`/`Superseded` — вне серии (§10).

## Ограничения

- не изменяй `birth/`, `calculation/`, `session/`, `engine/`, `outcomes.py`,
  `run_context.py`, `domain.py`;
- не изменяй `BirthDataResolver`, включая журналирование `tz_id` на уровне
  `INFO`: принятый отложенный долг (§14.3 и раздел про logging/privacy в
  AGENTS.md), а не дефект этой задачи;
- не изменяй `application/{commands,ports,results}.py`. Если чего-то не хватает,
  назови это в отчёте — возможно, ошибка в P1;
- не изменяй и не ослабляй существующие тесты;
- не выполняй попутный рефакторинг соседних модулей;
- не создавай коммит, push или PR.

## Проверки

```text
python -c "import exact_orb.application.handlers.build_natal"
pytest tests/application -q
pytest tests/test_module_boundaries.py -q
pytest -q
```

Тесты `tests/application` на этом шаге — контрактные из P1.1; они должны
остаться зелёными.

## Итоговый отчёт

- покажи итоговую структуру `handle()` и объясни, почему при неуспешном резолве
  артефактный порт недостижим по потоку управления;
- перечисли фактические прямые импорты модуля и сверь со списком выше;
- подтверди отдельной строкой, что в модуле нет ни `logging`, ни
  `except BaseException`, ни `wait_for`/`timeout`;
- назови точные команды проверок и их реальные результаты;
- отдельно укажи, что не проверялось, и оставшийся риск.
