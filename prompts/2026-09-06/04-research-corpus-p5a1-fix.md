# FIX — Блок Research, P5a.1: независимые тесты, нейтральный conformance, безопасная диагностика и float digest

Работай в ветке `feat/session-context`.

Это точечное исправление P5a. P5b, SQLite, consented corpus, transit и
application wiring не входят в задачу. Старые файлы в `prompts/**` не
редактируй. Не создавай commit, push или PR без отдельной команды.

## 0. Preflight

Прочитай корневой `AGENTS.md`, затем выполни:

```text
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log -8 --oneline
python -m pytest -q tests/research tests/test_module_boundaries.py
python -c "import sys, pydantic; print(sys.version); print(pydantic.VERSION)"
```

Ожидаемый baseline: 159 Research-тестов и 36 boundary-тестов. Расхождение
зафиксируй, не подгоняй. Сохрани пользовательские и несвязанные изменения.

Изучи модели, projection, root exports, Research conformance и три concrete
test modules, golden fixture, `tests/conftest.py`, Research requirements и
ADR-0023. `tests/test_module_boundaries.py` и `tests/conftest.py` не меняй.

## 1. Разрешённая область

Разрешены только необходимые изменения в:

```text
src/exact_orb/research/models.py
src/exact_orb/research/projection.py
src/exact_orb/research/__init__.py
tests/research/conformance.py
tests/research/test_models.py
tests/research/test_projection.py
tests/research/test_in_memory.py
tests/research/golden/research_digest_v1.json
docs/requirements/component_responsibilities/exact-orb_research_corpus.md
docs/requirements/decisions/0023-research-corpora-and-consent.md
```

`docs/requirements/decisions/README.md` не меняй: статус и смысл строки
ADR-0023 остаются прежними. Не меняй corpus ports, outcomes, error codes,
adapters, calculation, engine, session, fixtures, diagrams и boundary tests.

Единственное намеренное изменение публичного API — удаление ошибочно
экспортированного и нигде не используемого `QualityKind`. Сигнатуры порта,
outcomes, коды ошибок и состав `ChartFeatures` остаются прежними.

## 2. Research-тесты не зависят от Swiss Ephemeris

Добавь на уровне модулей
`pytestmark = pytest.mark.no_ephemeris_autoinit` в:

```text
tests/research/test_models.py
tests/research/test_projection.py
tests/research/test_in_memory.py
```

`conformance.py` сам не собирается pytest, поэтому маркер там недостаточен.

Докажи независимость безопасным экспериментом с конкретным файлом
`ephe/sepl_18.se1`:

1. проверь, что исходный файл существует, а временное имя свободно;
2. переименуй его в `ephe/sepl_18.se1.p5a1-disabled`;
3. в `try/finally` прогони `python -m pytest -q tests/research`;
4. в `finally` восстанови исходное имя;
5. после восстановления явно проверь наличие исходного и отсутствие
   временного файла, затем повторно прогони Research-тесты.

Не оставляй `ephe/` изменённым даже при падении pytest.

## 3. Generic conformance не знает об адаптерах

Перенеси `make_in_memory_factory()` из `tests/research/conformance.py` в
`tests/research/test_in_memory.py`. Вместе с фабрикой перенеси private backend
import, `asynccontextmanager` и комментарий, объясняющий единственное
санкционированное создание `_InMemoryResearchBackend`.

После переноса `conformance.py` содержит только общие builders/types/helpers и
`ResearchCorpusConformance`; он не импортирует и не конструирует InMemory или
SQLite ни на одном уровне вложенности. Удали устаревший export фабрики.

Добавь AST-тест, который:

- разбирает именно существующий `tests/research/conformance.py`;
- позитивно подтверждает наличие `ResearchCorpusConformance`;
- проверяет отсутствие `Import`/`ImportFrom` из
  `exact_orb.research.adapters` во всём AST, включая тела функций.

Обнови private-backend guard: единственное создание
`_InMemoryResearchBackend()` во всём Research source/test tree находится в
`test_in_memory.py`. Позитивный контроль должен подтвердить, что найден ровно
один вызов, а не позволить пустому результату пройти.

Зафиксируй существующую conformance-поверхность: concrete suite наследует
ровно 12 `test_*`-методов, что даёт 16 collected cases с параметризацией.
Concrete-класс по-прежнему переопределяет только `make_factory`.

## 4. Безопасная диагностика projection failure

Публичное поведение не меняется: любой перехваченный `ValidationError`
превращается в
`ResearchProjectionError("RESEARCH_PROJECTION_UNSUPPORTED_VALUE")`, а
`str(exc)` равен только этому коду.

Добавь один module logger через stdlib `logging`. Перед преобразованием ошибки
записывай ровно один warning с постоянным сообщением и structured `extra`:

```text
error_code = RESEARCH_PROJECTION_UNSUPPORTED_VALUE
validation_errors = tuple[(loc, type), ...]
```

`loc` берётся без искусственного перестроения projection и без обещания
полного пути от `ChartFeatures`: для неизвестного body sign допустим локальный
путь `sign`, для нарушения уникальности — `bodies`. Этого достаточно, чтобы
причины различались. Не меняй модель построения projection только ради
косметического префикса.

Извлекай ошибки через:

```python
exc.errors(include_input=False, include_context=False, include_url=False)
```

В message, args и пользовательских `extra` не должны попадать `input`, `msg`,
artifact content, birth data, идентификаторы, значения полей или пути из
пользовательских/backend-данных. Стандартные поля `LogRecord.pathname` и
`filename`, указывающие на исходник места логирования, из запрета исключены.

Тесты через `caplog.records`, а не только отформатированный текст, доказывают:

- ровно один warning на отказ;
- одинаковый публичный код и разные пары `(loc, type)` для неизвестного sign и
  duplicate body;
- отсутствие poisoned значений в message, args и custom diagnostics.

Не добавляй новые error codes, исключения, публичные diagnostics API или
метрики.

## 5. Удалить мёртвый `QualityKind`

Удали `QualityKind` из `models.py`, его `__all__` и root `research/__init__.py`.
Источником закрытого vocabulary остаются четыре `Literal` discriminator в
event-моделях.

Тест должен программно:

1. снять внешний `Annotated` с `ResearchQualityEvent`;
2. получить члены union;
3. для каждого event model взять annotation поля `kind`;
4. получить значения `Literal`;
5. сравнить множество с
   `{"rating", "regenerate", "copy", "reading_time"}`.

Не добавляй вторую production-константу. Отдельно проверь отсутствие
`QualityKind` в `exact_orb.research.models` и `exact_orb.research`.

## 6. Зафиксировать сериализацию float в digest format v1

Уточни действующий формат: finite float сериализуется тем же Python
`json.dumps`, который использует общий digest helper, то есть shortest
round-trip representation (`0.1 + 0.2` становится
`0.30000000000000004`). Будущие адаптеры обязаны вызывать общий digest helper,
а не реализовывать собственную сериализацию.

Не меняй существующие record/event canonical JSON и hashes. Добавь отдельный
golden record, созданный обычной валидацией `ResearchRecord`, с:

```text
latency_ms = 0.1 + 0.2
cost_usd = 1 / 3
```

Зафиксируй его canonical JSON и SHA-256 и независимо проверь строку, hash и
`record_content_digest`. Текущее нормативное правило уже покрывает exponent
notation; отдельный exponent golden в этом фиксе не требуется.

Diagnostic metadata golden-файла не является digest input. Сверь фактические
версии; если они остаются Python `3.14.0` и Pydantic `2.12.4`, не меняй их.

## 7. Документация

Точечно обнови:

- requirements §3.4: vocabulary задают четыре `Literal` discriminator;
- requirements §7: Python `json.dumps` float representation и обязательность
  общего helper для адаптеров;
- requirements §8: warning содержит безопасные `loc`/`type`, без входных
  значений и artifact content;
- requirements §11: InMemory factory живёт в concrete test module, generic
  conformance не импортирует адаптеры;
- ADR-0023: добавь float-правило в canonical format и дополни существующую
  ревизию 2026-09-06 этим уточнением, не меняя исходную дату принятия.

README решений и диаграммы не меняй.

## 8. Проверки

```text
python -m pytest --collect-only -q tests/research
python -m pytest -q tests/research/test_models.py tests/research/test_projection.py
python -m pytest -q tests/research/test_in_memory.py
python -m pytest -q tests/research
python -m pytest -q tests/research tests/test_module_boundaries.py
python -m pytest -q tests/session tests/research tests/test_module_boundaries.py
python -m pytest -q
git diff --check
git status --short
```

Не используй sleep, случайные задержки, сеть, платные smoke tests и
отсутствующие Ruff/mypy/coverage gates.

## 9. Acceptance

P5a.1 завершён, когда:

1. 159 исходных Research cases сохранены, новые regression cases добавлены.
2. Research проходит при временно отсутствующем `ephe/sepl_18.se1`, файл
   гарантированно восстановлен.
3. Generic conformance не импортирует и не создаёт адаптеры; 12 inherited
   методов/16 параметризованных cases сохранены.
4. Private InMemory backend создаётся ровно один раз в concrete test factory.
5. Projection warning безопасно различает два типа отказа, публичная ошибка не
   изменилась.
6. `QualityKind` удалён как единственное намеренное изменение exports, а
   vocabulary выводится из union.
7. Float format нормативно описан и закреплён новым golden; пять прежних
   digest остаются прежними.
8. Требования и ADR синхронизированы; README, диаграммы, boundary tests и
   несвязанные пользовательские файлы не затронуты.
9. Полный pytest и перечисленные проверки фактически выполнены.
10. P5b, consented corpus, transit и application не объявлены реализованными.

В итоговом отчёте начни с результата, перечисли фактические изменения,
команды и числа тестов, новый SHA-256, подтверждение прежних digest, версии
Python/Pydantic, восстановление ephemeris-файла и сохранённые несвязанные
изменения.
