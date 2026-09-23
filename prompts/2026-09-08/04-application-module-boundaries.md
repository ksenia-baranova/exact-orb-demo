# Application-слой, P4: граница прямых импортов `build_natal.py`

Работай в ветке `feat/build-natal-handler` — той же, что и P1.

Не создавай коммит, не делай push и не включай изменения из других веток.
Сохрани пользовательские и несвязанные изменения рабочего дерева.

`prompts/**` — исторический журнал. Не редактируй старые промты.

## Что уже сделано

P1–P3.2 дали контракты, handler, журнал, unit- и интеграционное покрытие.
Граница импортов до сих пор соблюдалась вручную и ничем не проверялась.

Источник истины — `docs/requirements/exact_orb_build_natal_handler_requirements.md`
(R4): §10.1, §10.2, §12.5 п. 19, BH-12, BH-13, BH-14.

## Цель

Сделать §10.1 механически проверяемым инвариантом — так же, как это уже сделано
для `session/`, `calculation/` и `research/`.

## Ключевое отличие от соседних границ

Запрет адресуется **одному модулю**, а не пакету:

```text
exact_orb.application.handlers.build_natal
```

Общий запрет для всего `application` был бы неверен: `application/results.py`
обязан импортировать `exact_orb.calculation.types`, потому что Pydantic-модель
`BuildNatalSuccess` содержит настоящий `ChartArtifact` и разрешает аннотацию в
рантайме (§10.2). Через него в import-граф пакета неизбежно попадают
`engine.charts` и `swisseph`. Это принятое следствие контракта, а не дефект.

Отсюда второе следствие: проверка анализирует **объявленные импорты** модуля
через AST, а не runtime-граф. Не пиши для этой границы тест в стиле
`test_session_package_import_keeps_runtime_and_edge_modules_out`, который
поднимает подпроцесс и смотрит `sys.modules`, — он заведомо провалится и
провалится правильно.

## Перед изменениями

1. Проверь Git и сохрани все пользовательские и несвязанные изменения.
2. Изучи в `tests/test_module_boundaries.py`:
   - хелперы `_declared_imports`, `_module_name` и `_violates`;
   - константы `SESSION_SERVICE_FORBIDDEN_IMPORTS`,
     `CALCULATION_ARTIFACTS_FORBIDDEN`, `CALCULATION_ENGINE_FORBIDDEN` — образцы
     денилистов по объявленным импортам;
   - тесты `test_calculation_artifacts_declares_no_edge_imports` и
     `test_session_service_declares_no_adapter_clock_id_or_edge_imports` —
     образцы формы теста и текста assert-сообщения;
   - как в файле устроены позитивные контроли: тест обязан ломаться, если
     проверяемый файл не был найден или не разобран.
3. Изучи §10.1 требований R4 и фактические импорты
   `application/handlers/build_natal.py`.

## Изменить

```text
tests/test_module_boundaries.py
```

Больше ничего.

## Константа

```python
APPLICATION_BUILD_NATAL_FORBIDDEN_DIRECT_IMPORTS: tuple[str, ...] = (
    "exact_orb.birth.resolver",
    "exact_orb.calculation.artifacts",
    "exact_orb.calculation.cache",
    "exact_orb.calculation.codec",
    "exact_orb.calculation.engine",
    "exact_orb.calculation.keys",
    "exact_orb.calculation.version",
    "exact_orb.cli",
    "exact_orb.config",
    "exact_orb.engine",
    "exact_orb.ephemeris_runtime",
    "exact_orb.intent",
    "exact_orb.interpretation",
    "exact_orb.llm",
    "exact_orb.orchestration",
    "exact_orb.session.adapters",
    "exact_orb.session.context",
    "exact_orb.session.persistence",
    "exact_orb.session.store",
    "exact_orb.swiss_backend",
    "exact_orb.tools",
)
```

Разместить рядом с остальными константами границ, в том же стиле и с тем же
порядком объявления, что у соседей.

Пояснения, которые стоит зафиксировать комментарием в коде:

- сравнение префиксное, поэтому `exact_orb.engine` покрывает
  `exact_orb.engine.charts`, а `exact_orb.session.adapters` — все адаптеры;
  отдельные подмодули в список не выносятся;
- `exact_orb.birth.resolver` и `exact_orb.calculation.artifacts` — конкретные
  реализации портов. Без первого порт `BirthDataResolverPort` был бы защищён
  только с одной стороны: прямой импорт артефактного резолвера запрещён, а
  прямой импорт birth-резолвера — нет. Обе реализации приходят в handler через
  конструктор;
- `exact_orb.calculation.types` в списке **отсутствует намеренно**. Handler в
  нём не нуждается — тип артефакта выводится из порта, — но и вреда прямой
  импорт для аннотации не несёт: `application/results.py` импортирует этот
  модуль в любом случае (§10.2), и никакой дополнительной связности не
  возникает.

## Тест

Форма — как у `test_calculation_artifacts_declares_no_edge_imports`:

- найти файл `src/exact_orb/application/handlers/build_natal.py`;
- получить объявленные импорты через `_declared_imports`;
- проверять каждый импорт существующим `_violates(imported, forbidden)`, чтобы
  префикс совпадал только с самим модулем или его подмодулем, а не с модулем с
  похожим именем;
- в assert-сообщение вывести и нарушенное правило, и фактический импорт.

**Позитивный контроль обязателен.** Тест не должен проходить из-за того, что
файл не найден или разобран пустым. Минимум:

- утверждать, что файл существует;
- утверждать, что множество объявленных импортов непусто и содержит хотя бы
  один заведомо ожидаемый — например, `exact_orb.application.ports`.

Без этого тест останется зелёным, если кто-то переименует модуль.

Отдельным тестом закрепи разрешённое: `application/results.py` **имеет право**
объявлять `exact_orb.calculation.types`. Это фиксирует §10.2 как решение, а не
как случайность, и предупреждает будущую попытку распространить денилист на
весь пакет.

## Чего здесь не делать

- не добавляй проверку runtime-графа для `application` — она противоречит §10.2;
- не расширяй существующие константы `SESSION_*`, `CALCULATION_*`,
  `RESEARCH_*` и не ослабляй ни один существующий тест: AGENTS.md называет этот
  файл архитектурным инвариантом;
- не добавляй `exact_orb.application` в чужие денилисты — он там уже есть
  (`RESEARCH_FORBIDDEN_IMPORTS`, `SESSION_FORBIDDEN_AT_RUNTIME`,
  `SESSION_ADAPTER_FORBIDDEN_IMPORTS`, `SESSION_SERVICE_FORBIDDEN_IMPORTS`);
  убедись в этом и отметь в отчёте;
- не заводи параллельный `tests/application/test_boundaries.py`: источник
  истины по границам один.

## Если тест сразу красный

Значит P2 или P3 нарушил §10.1. Не ослабляй константу, не добавляй исключение и
не изменяй handler в рамках P4. Назови нарушенный импорт в отчёте; исправление
модуля — отдельная задача.

## Ограничения

- не изменяй `application/*`, `birth/`, `calculation/`, `session/`, `engine/`;
- не изменяй тесты P1.1, P2.1, P3.1, P3.2;
- не создавай коммит, push или PR.

## Проверки

```text
pytest tests/test_module_boundaries.py -q
pytest tests/application -q
pytest -q
```

## Итоговый отчёт

- приведи фактический список объявленных импортов
  `application/handlers/build_natal.py`;
- покажи, какие позитивные контроли стоят в новом тесте и от какого ложного
  прохождения каждый защищает;
- подтверди, что ни одна существующая константа и ни один существующий тест не
  ослаблены;
- назови точные команды проверок и их реальные результаты;
- отдельно укажи, что не проверялось, и оставшийся риск.
