# Application-слой, P6: согласованные исправления по ревью реализации

Работай в `fix/build-natal-handler-review`. Перед изменениями убедись, что это
текущая ветка; если нет — остановись. Исторические промты не изменяй.

Не создавай коммит, не делай push и не включай изменения из других веток.
Сохрани пользовательские и несвязанные изменения рабочего дерева.

`prompts/**` — исторический журнал. Не редактируй старые промты.

## Что уже сделано

P1–P4 реализовали `exact_orb.application`, `BuildNatalHandler`, журнал,
unit- и интеграционное покрытие и границу прямых импортов.

Источник истины —
`docs/requirements/exact_orb_build_natal_handler_requirements.md` (R4).

## Цель

Явно зафиксировать статус недостижимой при текущих инвариантах защитной
проверки `BuildNatalSuccess` и привести async-тесты application-слоя к
действующей конфигурации pytest. Поведение продуктового кода не меняется.

## Перед изменениями

1. Выполни `git branch --show-current` и убедись, что текущая ветка —
   `fix/build-natal-handler-review`. Если это не так, остановись.
2. Выполни `git status --short` и сохрани все пользовательские и несвязанные
   изменения.
3. Зафиксируй исходное число тестов командой
   `pytest tests/application --collect-only -q`.
4. Изучи:
   - `src/exact_orb/application/results.py`;
   - `src/exact_orb/calculation/types.py` — валидатор
     `ChartArtifact._validate_identity`;
   - `tests/application/test_contracts.py`;
   - `pyproject.toml`, секцию `[tool.pytest.ini_options]`;
   - `tests/test_chart_artifact_resolver.py`,
     `tests/test_calculation_block_integration.py`,
     `tests/test_calculation_engine.py` и `tests/session/**` — стиль async-тестов.

## Правка 1: статус защитной ветки валидатора

В `src/exact_orb/application/results.py` проверка

```python
if self.artifact.chart_kind != delta.base_chart_spec.chart_kind:
```

недостижима через валидированную конструкцию `ChartArtifact`: предыдущая
проверка уже установила `artifact.spec == delta.base_chart_spec`, а
`ChartArtifact._validate_identity` обеспечивает
`artifact.chart_kind == artifact.spec.chart_kind`.

Проверку оставь как защиту на случай будущего ослабления инварианта
`ChartArtifact`. Измени только комментарий рядом с ней. Комментарий должен
точно утверждать, что ветка недостижима через валидированную конструкцию
`ChartArtifact`, и объяснять назначение defense-in-depth. Не утверждай, что
ветку технически невозможно покрыть тестом.

Отдельный тест через `model_construct`, подмену `__dict__`, отключение
валидации или иной способ сборки заведомо невалидного `ChartArtifact` не
добавляй: это не поддерживаемое наблюдаемое поведение публичного контракта.

## Правка 2: убрать избыточный `@pytest.mark.asyncio`

В `pyproject.toml` задано `asyncio_mode = "auto"`, поэтому явный маркер не
меняет режим выполнения. Удали все вхождения `@pytest.mark.asyncio` из файлов:

```text
tests/application/test_build_natal_handler.py
tests/application/test_build_natal_logging.py
tests/application/test_build_natal_integration.py
```

Там, где маркер соседствует с `@pytest.mark.parametrize` или
`@pytest.mark.no_ephemeris_autoinit`, удаляй только строку с `asyncio`.
Остальные декораторы и их порядок сохрани.

`@pytest.mark.no_ephemeris_autoinit` не изменяй: он объявлен в
`tests/conftest.py` и несёт отдельную семантику.

После удаления маркеров снова выполни
`pytest tests/application --collect-only -q`. Число тестов должно совпасть с
исходным: эта задача не добавляет и не удаляет тестовые сценарии.

## Short-circuit integration-тесты не добавлять

Не добавляй в `test_build_natal_integration.py` новые сценарии неизвестного
места, даты вне диапазона и неизвестной таймзоны. Они уже покрыты в
`test_build_natal_handler.py` с настоящими `LocalPlaceCatalog` и
`BirthDataResolver`; `artifacts.calls == 0` непосредственно доказывает BH-2.
Настоящий, но не вызываемый `ChartArtifactResolver` не создаёт дополнительного
интеграционного доказательства.

## Дополнительные ограничения

- Не переноси импорт `ChartArtifact` в `ports.py` под `TYPE_CHECKING`:
  `tests/application/test_contracts.py::test_implemented_dependencies_match_port_signatures`
  использует `get_type_hints(port_method)` и требует имя в globals модуля.
- Не изменяй `handlers/build_natal.py`, `commands.py`, `ports.py`, сигнатуры и
  контракты.
- Не изменяй `birth/`, `calculation/`, `session/`, `engine/`.
- Не изменяй существующие тесты иначе, чем удалением маркеров из правки 2.
- Не изменяй общие фикстуры, `tests/conftest.py` и
  `tests/test_module_boundaries.py`.
- Не добавляй coverage, mypy, Ruff и другие quality gates.
- Не создавай коммит, push или PR.

## Проверки

```text
pytest tests/application --collect-only -q
pytest tests/application -q
pytest tests/test_module_boundaries.py -q
pytest -q
```

## Итоговый отчёт

- приведи исходное и итоговое число собранных application-тестов;
- подтверди, что удаление маркеров не изменило набор сценариев;
- опиши уточнённый комментарий защитной ветки и подтверди отсутствие теста,
  создающего невалидный `ChartArtifact` в обход валидации;
- подтверди, что новые short-circuit integration-тесты не добавлялись;
- подтверди, что `handlers/build_natal.py`, порты и контракты не изменялись;
- назови точные команды проверок и их реальные результаты;
- отдельно укажи, что не проверялось, существующие предупреждения и
  оставшийся риск.
