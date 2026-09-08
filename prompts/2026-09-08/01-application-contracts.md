# Application-слой, P1: контракты команд, портов и результата

Работай в ветке `feat/build-natal-handler`.

Ветка одна на все девять промтов серии. Если она уже существует, продолжай
в ней; иначе создай от текущей ветки. Не создавай коммит, не делай push и не
включай изменения из других веток. Сохрани пользовательские и несвязанные
изменения рабочего дерева.

`prompts/**` — исторический журнал. Не редактируй старые промты.

## Контекст серии

| Этап | Содержание |
|---|---|
| P1 | `commands.py`, `ports.py`, `results.py` — контракты application-слоя |
| P1.1 | контрактные тесты: frozen-команды, валидатор результата, порты, сигнатуры |
| P2 | `handlers/build_natal.py` — алгоритм §6–§8 **без журнала** |
| P2.1 | unit-тесты handler и позитивный контроль с реальным резолвером |
| P3 | наблюдаемость: три события, `except BaseException` |
| P3.1 | тесты журнала |
| P3.2 | интеграционные тесты полного пути с настоящим Swiss Ephemeris |
| P4 | граница импортов в `tests/test_module_boundaries.py` |
| P5 | синхронизация диаграмм и старой документации с R4 |

Источник истины серии — `docs/requirements/exact_orb_build_natal_handler_requirements.md`
(ревизия R4). Дальше по тексту ссылки вида «§5», «BH-7» указывают на этот документ.

`ApplicationOrchestrator`, `bootstrap.py` и transport-слой в серию не входят.
Граница проходит по `BuildNatalOutcome`: handler его производит, оркестратор
потребляет.

В P1 нет ни handler, ни журнала, ни граничных тестов. Здесь фиксируются только
типы, которые P2 и P3 реализуют без изменений.

## Цель

- отдельный пакет `exact_orb.application` с явной внутренней структурой;
- frozen-команды и marker-тип `Command` как ключ маршрутизации;
- структурные `Protocol`-порты вместо конкретных классов соседних модулей;
- выходная модель `BuildNatalSuccess`, которая сама не допускает
  рассогласованный `{artifact, delta}`;
- ацикличный граф модулей пакета;
- ни одной заглушки будущей функциональности.

## Перед изменениями

1. Проверь Git и сохрани все пользовательские и несвязанные изменения.
2. Перейди на `feat/build-natal-handler` либо создай её.
3. Изучи:
   - `docs/requirements/exact_orb_build_natal_handler_requirements.md` — §3, §5,
     §10.1, §10.2 и раздел «Контракты» целиком;
   - контрактные разделы `exact-orb_build_natal_components.md` (§3.6, §7.1);
   - ADR-0006, ADR-0008, ADR-0014, ADR-0017, ADR-0020;
   - `sequence_diagrams/build_natal/000`–`005`;
   - `birth/types.py`, `calculation/spec.py`, `calculation/errors.py`,
     `calculation/types.py`, корневой `outcomes.py`, `run_context.py`,
     `session/state.py`;
   - `session/__init__.py` и `session/persistence.py` как образец стиля
     `Protocol`-портов;
   - `tests/test_module_boundaries.py`.
4. Существенные противоречия не разрешай молча: назови конфликт в отчёте.
5. Не расширяй задачу на handler, журнал, оркестратор и граничные тесты.

## Создать пакет

```text
src/exact_orb/application/
    __init__.py
    commands.py
    ports.py
    results.py
    handlers/
        __init__.py
```

`handlers/build_natal.py` в P1 не создаётся. `handlers/__init__.py` пустой:
пакет нужен, чтобы P2 не начинался с создания структуры.

## Пустые `__init__.py`

`application/__init__.py` и `application/handlers/__init__.py` не выполняют
реэкспорт. Импорт идёт по полным путям: `from exact_orb.application.commands
import BuildNatalCommand`.

Причина не стилистическая. `results.py` обязан импортировать
`exact_orb.calculation.types` (см. «Транзитивный native import»), а реэкспорт
в `__init__.py` затащил бы native-стек в импорт всего пакета — включая те
модули, которым он не нужен. `exact_orb/session/__init__.py` делает реэкспорт
именно потому, что весь session-пакет свободен от native-стека; здесь это не так.

## Ацикличный граф модулей

```text
commands.py  → (birth.types)
ports.py     → commands.py, birth.types, calculation.spec, calculation.types,
               session.state, run_context, outcomes
results.py   → calculation.types, session.state, outcomes
```

- `commands.py` не импортирует ни один другой модуль пакета;
- `ports.py` импортирует `commands.py` ради `TypeVar(bound=Command)`;
- `results.py` не импортирует `ports.py` и `commands.py`;
- обратных рёбер нет.

Не обходи циклы через `TYPE_CHECKING`, строковые forward references, локальные
импорты или порядок импорта в `__init__.py`. Ацикличность должна следовать из
AST объявленных импортов.

## `application/commands.py`

```python
class Command(BaseModel):
    model_config = ConfigDict(frozen=True)


class BuildNatalCommand(Command):
    birth_input: BirthInput
```

Требования:

- `Command` — frozen Pydantic-модель без собственных полей. Это одновременно
  верхняя граница типа для `TypeVar` и ключ registry маршрутизации
  `Mapping[type[Command], Handler]`;
- `frozen=True` объявляется один раз на `Command` и наследуется конкретными
  командами. Не дублируй `model_config` в `BuildNatalCommand`;
- в команду не входят `session_id`, `state_version`, `run_id`, настройки кэша,
  параметры движка и технические параметры сохранения состояния (§4.1).
  `session_id` приходит в оркестратор отдельным доверенным аргументом;
- `birth_input` — существующий `exact_orb.birth.types.BirthInput`. Не создавай
  собственную копию модели и не валидируй её повторно.

## `application/ports.py`

```python
CommandT = TypeVar("CommandT", bound=Command, contravariant=True)
OutcomeT = TypeVar("OutcomeT", covariant=True)


class Handler(Protocol[CommandT, OutcomeT]):
    async def handle(
        self,
        command: CommandT,
        state: SessionState,
        run: RunContext,
    ) -> OutcomeT:
        ...


class BirthDataResolverPort(Protocol):
    async def resolve(
        self,
        birth_input: BirthInput,
        *,
        run: RunContext | None = None,
    ) -> ResolvedBirthData | InputRequired | ResolutionUnavailable:
        ...


class ChartArtifactPort(Protocol):
    async def ensure_chart(
        self,
        spec: ChartSpec,
        resolved: ResolvedBirthData,
        *,
        run: RunContext,
    ) -> ChartArtifact:
        ...
```

Требования:

- сигнатуры портов повторяют реализованные `BirthDataResolver.resolve` и
  `ChartArtifactResolver.ensure_chart` **посимвольно**, включая kind параметров
  и значение по умолчанию. Обрати внимание на асимметрию: у резолвера `run`
  необязательный, у артефактного порта — обязательный keyword-only. Это не
  опечатка в требованиях, а факт существующего кода;
- порты **не** помечаются `@runtime_checkable`. Система не выполняет
  `isinstance(..., Protocol)`; совместимость держат контрактные тесты P1.1.
  Это намеренное решение (§3.2), а не пропущенный декоратор. В проекте уже есть
  такая же асимметрия: `TechniqueAdapter` помечен, `CalculationEnginePort` — нет,
  и это закреплено тестом
  `test_technique_adapter_is_runtime_checkable_but_engine_port_is_not`;
- вариантность `TypeVar` обязательна: `CommandT` стоит в позиции параметра,
  `OutcomeT` — в позиции возврата;
- реализованные `BirthDataResolver` и `ChartArtifactResolver` изменению не
  подлежат. Порты подстраиваются под них, а не наоборот.

## `application/results.py`

```python
class BuildNatalSuccess(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact: ChartArtifact
    delta: StateDelta

    @model_validator(mode="after")
    def _result_must_be_consistent(self) -> Self:
        delta = self.delta

        # Проверка выполняется первой: успешный build не принимает RESET_DELTA.
        if (
            delta.birth_input is None
            or delta.birth_resolved is None
            or delta.base_chart_spec is None
        ):
            raise ValueError(
                "successful build requires a fully populated StateDelta"
            )

        if self.artifact.spec != delta.base_chart_spec:
            raise ValueError("artifact.spec must equal delta.base_chart_spec")

        if self.artifact.chart_kind != delta.base_chart_spec.chart_kind:
            raise ValueError(
                "artifact.chart_kind must equal delta.base_chart_spec.chart_kind"
            )

        return self


BuildNatalOutcome = (
    BuildNatalSuccess | InputRequired | ResolutionUnavailable | CalculationFailed
)
```

Требования:

- **порядок проверок обязателен.** Pydantic оборачивает в `ValidationError`
  только `ValueError` и `AssertionError`; `TypeError` и `AttributeError` из
  `model_validator` уходят наружу сырыми. Если сравнение `chart_kind` выполнить
  раньше проверки на `None`, пустая дельта даст сырой `TypeError` вместо
  `ValidationError`;
- третья проверка производна: `ChartArtifact._validate_identity` уже
  гарантирует `artifact.chart_kind == artifact.spec.chart_kind`, поэтому вместе
  со второй проверкой равенство следует автоматически. Она остаётся как
  defense-in-depth; отметь это комментарием в коде, чтобы её не приняли за
  независимый инвариант (BH-8);
- `BuildNatalSuccess` frozen;
- `InputRequired`, `ResolutionUnavailable` и `CalculationFailed` берутся из
  корневого `exact_orb.outcomes`. Новых типов исхода не создавай;
- `BuildNatalOutcome` — union-алиас без собственных атрибутов.

## Транзитивный native import

Поле `artifact: ChartArtifact` обязывает `results.py` импортировать
`exact_orb.calculation.types` в рантайме: Pydantic разрешает аннотацию при
построении схемы, и `TYPE_CHECKING` эту цепочку не устраняет.

```text
BuildNatalSuccess → ChartArtifact → exact_orb.calculation.types
→ exact_orb.engine.charts.natal → exact_orb.swiss_backend → swisseph
```

Это ожидаемое следствие принятого контракта (§10.2), а не дефект. Не пытайся
его обойти лениво импортируемым свойством, строковой аннотацией,
`model_rebuild()` по требованию или подменой типа на `Any`. Полная изоляция
application-слоя потребовала бы отдельного DTO вместо `ChartArtifact` и
находится вне этой серии.

Ограничение действует только на `results.py` и `ports.py`. Модуль
`handlers/build_natal.py` в P2 получает собственный, более узкий список
запрещённых прямых импортов.

## Зафиксировать, но не реализовывать в P1

- `ApplicationResult` — контракт `ApplicationOrchestrator`. Не создавай:
  AGENTS.md запрещает заглушки будущей функциональности. Строка в таблице §3.1
  требований будет помечена в P5;
- `ApplicationOrchestrator`, реестр handlers и `bootstrap.py`;
- `BuildNatalHandler` — P2;
- журнал и `except BaseException` — P3;
- `APPLICATION_BUILD_NATAL_FORBIDDEN_DIRECT_IMPORTS` — P4;
- второй `RunContext` внутри `application`. Существующий остаётся в
  `exact_orb.run_context`.

## Ограничения

- не изменяй `birth/`, `calculation/`, `session/`, `engine/`, `outcomes.py`,
  `run_context.py`, `domain.py`;
- не изменяй `BirthDataResolver`, включая журналирование `tz_id` на уровне
  `INFO`: это принятый отложенный долг общей политики логирования birth-блока
  (§14.3 требований и раздел про logging/privacy в AGENTS.md), а не дефект
  этой задачи;
- не изменяй и не ослабляй существующие тесты, в том числе
  `tests/test_module_boundaries.py`;
- не добавляй зависимости, сетевые вызовы, compatibility aliases;
- не выполняй попутный рефакторинг соседних модулей;
- не создавай коммит, ветку помимо указанной, push или PR.

## Проверки

Запускай поэтапно и приводи фактический вывод:

```text
python -c "import exact_orb.application.commands, exact_orb.application.ports, exact_orb.application.results"
pytest tests/test_module_boundaries.py -q
pytest -q
```

Первая команда должна проходить без ошибок разрешения аннотаций. Полный прогон
обязателен: новый пакет не должен ломать существующие граничные тесты.

Тестов в P1 не пишется — они целиком в P1.1.

## Итоговый отчёт

- перечисли созданные файлы и объявленные типы;
- покажи фактический граф импортов трёх модулей и обоснуй его ацикличность;
- назови точные команды проверок и их реальные результаты;
- отдельно укажи, что не проверялось, и оставшиеся ограничения;
- если нашёл противоречие между требованиями R4 и текущим кодом — назови его,
  не разрешая молча.
