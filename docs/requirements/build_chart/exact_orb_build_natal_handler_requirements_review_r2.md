# Проверка исправленной версии требований к `BuildNatalHandler`

**Предмет:** редакция «исправленная версия по результатам ревью», 2026-09-08
**Сверено с кодом:** `exact-orb-recovered`, рабочее дерево на 2026-09-08
**Итог:** все 23 замечания первого ревью (A-1…A-8, B-1…B-15) закрыты. Ниже —
подтверждение закрытия и восемь новых замечаний, три из которых блокируют
реализацию.

---

## 1. Закрытые замечания

| № первого ревью | Где закрыто | Оценка |
|---|---|---|
| A-1 недостижимость §8.3 | §8.3 переписан: граница handler + признание `ENGINE_UNEXPECTED` замаскированным дефектом | закрыто по существу |
| A-2 запрет `engine.charts` невыполним | §10.1 + §12.4 п.13: «прямые объявления импортов», транзитивность разрешена явно | закрыто, но список неполон — см. N-3 |
| A-2 несуществующий `exact_orb.agent` | заменён на `intent`/`interpretation`/`llm`/`orchestration`/`tools`/`cli`/`config` | закрыто |
| A-3 конкретные классы вместо портов | §3.2: `BirthDataResolverPort`, `ChartArtifactPort`, `Handler`, `Command` | закрыто, детали — N-8 |
| A-4 префикс `calculation_key` | `eo:calc:v1:` в контракте и в примере `BuildNatalSuccess` | закрыто |
| A-5 `session_id` в команде | §8, расхождение 1 | закрыто |
| A-6 нота диаграммы про `AMBIGUOUS` | §8, расхождение 2 + §7.1 | закрыто |
| A-7 дубль `RunContext` | §3.1: остаётся в `exact_orb.run_context` | закрыто |
| A-8 тавтологичный BH-10 | BH-10 переформулирован через `apply_delta`/`touched`/`ChartRef`; тест 14 | закрыто |
| B-1 размещение типов | §3.1 таблица; имя `BuildNatalResult` снято явно | закрыто |
| B-2 нет `Command`/`Handler` | §3.2 | закрыто |
| B-3 кто держит BH-7/BH-8 | §5 + §9 распределение | закрыто, уточнение — N-1, N-2 |
| B-4 судьба `warnings` | §6 шаг 5 | закрыто |
| B-5 исключения резолвера | §7.3 + тест 7 | закрыто |
| B-6 исход → событие | §11 таблица уровней и полей | закрыто, пробел — N-5 |
| B-7 политика геоданных | BH-16, §11, §14.3 | закрыто |
| B-8 тайм-ауты и отмена | §8.4 | закрыто |
| B-9 handler не валидирует state | §4.2 | закрыто |
| B-10 `matches_intent` | §14.1 | закрыто |
| B-11 слабые тесты spec | §12.1 «spec целиком равна канонической» | закрыто |
| B-12 достижимость `EPHEMERIS_UNAVAILABLE` | §12.3 п.9 и п.12 | закрыто, но см. N-6 |
| B-13 зеркальная константа | §12.4 п.18 | закрыто |
| B-14 «непустой» `issues` | контракт `InputRequired` + оговорка в §7.1 | закрыто |
| B-15 недостижимый `MISSING` | §7.1 и таблица `Issue.code` | закрыто |

Дополнительно перепроверено по коду и подтверждено:

- сигнатуры `BirthDataResolver.resolve` и `ChartArtifactResolver.ensure_chart`
  совпадают с объявленными портами **посимвольно**, включая
  `run: RunContext | None = None` в первом и keyword-only `run: RunContext`
  во втором — структурная совместимость реальна, менять соседей не нужно;
- `NatalChartSpec(chart_kind=...)` даёт канонический include (повторно проверено прогоном);
- маркер-класс `Command` совместим с pydantic: `class BuildNatalCommand(Command, BaseModel)`
  собирается, метакласс разрешается в `ModelMetaclass` (проверено прогоном).

---

## 2. Новые замечания

### N-1. Валидатор `BuildNatalSuccess`: порядок проверок влияет на тип ошибки

§5 задаёт два условия:

```text
artifact.spec == delta.base_chart_spec
artifact.chart_kind == delta.base_chart_spec.chart_kind
```

`delta.base_chart_spec` имеет тип `ChartSpec | None`, и `StateDelta` сам по себе
допускает all-None (`RESET_DELTA`). Если реализация выполнит второе условие
первым, при пустой дельте произойдёт разыменование `None.chart_kind`.
Проверено прогоном: pydantic оборачивает в `ValidationError` только
`ValueError`/`AssertionError`; `TypeError`/`AttributeError` из
`model_validator` уходят наружу сырыми.

```
порядок из документа        → ValidationError   (первое условие ловит None)
обратный порядок проверок   → TypeError         (наружу, мимо ValidationError)
```

**Правка.** Записать в §5 первым требованием: валидатор требует полностью
заполненную дельту (`birth_input`, `birth_resolved`, `base_chart_spec` — все
не `None`), и только затем сравнивает спеки. Это заодно закрывает дыру, о
которой документ молчит: сейчас из двух условий не следует, что
`delta.birth_input` и `delta.birth_resolved` заполнены, хотя §5 и BH-9 этого
требуют.

### N-2. Второе условие валидатора производно

`ChartArtifact._validate_identity` уже гарантирует
`artifact.chart_kind == artifact.spec.chart_kind`. Вместе с первым условием
(`artifact.spec == delta.base_chart_spec`) второе выводится автоматически.
Оставлять его как defense-in-depth можно, но BH-8 тогда стоит пометить как
производный инвариант — иначе тест 16 будет считаться покрытием независимого
свойства, которого нет.

### N-3. Список запрещённых прямых импортов не покрывает BH-13 *(блокирующее)*

§3.4 запрещает handler-у обращаться к `CalculationCache`, `CalculationEnginePort`,
`EngineService`, `calculate_natal()`, функциям `calculation_key` и codec
артефактов. Список §10.1 / §12.4 п.13 ни одного из этих модулей не содержит:

```text
отсутствуют: exact_orb.calculation.cache
             exact_orb.calculation.codec
             exact_orb.calculation.engine
             exact_orb.calculation.keys
             exact_orb.calculation.artifacts
             exact_orb.swiss_backend
             exact_orb.ephemeris_runtime
```

Значит зеркальная константа `APPLICATION_FORBIDDEN_DIRECT_IMPORTS` нарушение
BH-13 не поймает: `from exact_orb.calculation.keys import calculation_key`
пройдёт проверку.

Раз §3.2 вводит порты, туда же логично добавить запрет прямых импортов
конкретных реализаций — `exact_orb.birth.resolver` и
`exact_orb.calculation.artifacts` — и дополнить session-часть
(`exact_orb.session.persistence`, `exact_orb.session.adapters`; сейчас только
`store` и `context`).

**Важно:** запрет должен адресоваться модулю
`exact_orb.application.handlers.build_natal`, а не пакету `application`
целиком — `results.py` обязан импортировать `exact_orb.calculation.types`
(см. N-4). В `tests/test_module_boundaries.py` это естественно ложится на
существующий стиль: там уже есть отдельные константы для пакета, адаптеров и
сервиса (`SESSION_*_FORBIDDEN_IMPORTS`).

### N-4. Решение §5 жёстко предопределяет §10.1 — это стоит записать *(важное)*

Цепочка следствий, которую документ оставляет неявной:

```text
BuildNatalSuccess — pydantic-модель с полем artifact: ChartArtifact
    → results.py обязан разрешить аннотацию на этапе построения модели
    → runtime-импорт exact_orb.calculation.types
    → (докстринг самого модуля) «imports the native calculation stack transitively»
    → exact_orb.engine.charts.natal → engine.ephemeris.calc
    → exact_orb.swiss_backend → import swisseph
```

Проверено по коду: `swiss_backend.py` — это буквально `import swisseph as swe`,
`engine/ephemeris/calc.py` импортирует его на уровне модуля.

Следствие: **любой** импорт `exact_orb.application.results`, включая
unit-тесты handler, поднимает native-стек. `if TYPE_CHECKING` здесь не спасает —
pydantic разрешает аннотации в рантайме. То есть разрешение из §10.1 не
«уступка», а прямое следствие §5.

**Правка.** Записать это в §10.1 одной фразой. Иначе следующая попытка
«облегчить application-слой» упрётся в ту же стену и снова начнётся с
переписывания §10.1. Если цена окажется неприемлемой, единственная
альтернатива — `BuildNatalSuccess` как frozen dataclass с ленивыми
аннотациями и проверкой в `__post_init__`, ценой расхождения со стилем
остальных сообщений.

### N-5. Нет terminal event для нештатного завершения *(блокирующее)*

§7.3, §8.3 и §8.4 штатно предусматривают, что handler пропускает наверх
исключения резолвера, неизвестные исключения и `asyncio.CancelledError`.
§11 при этом описывает ровно два события, и `build_natal_completed` пишется
«при типизированном завершении».

Итог: при нештатном завершении terminal event не пишется вообще, а
`build_natal_started` живёт на DEBUG. В production-логах на INFO прогон
исчезает бесследно — при том что это ровно тот класс событий, ради которого
нужен `run_id`.

**Правка.** Третье событие `build_natal_failed`, уровень ERROR, поля
`run_id`, `outcome=unhandled_exception`, `exception_type`, `duration_ms`,
без traceback и без значений аргументов. Ровно так уже сделано в
`EngineService._log_failure` — есть образец в кодовой базе. Реализуется как
`except BaseException: <лог>; raise`, что не нарушает §8.3 (маскировки нет) и
корректно покрывает `CancelledError`. Альтернатива — явно записать в §11, что
отсутствие terminal event при нештатном завершении допустимо; но тогда это
осознанное решение, а не умолчание.

### N-6. §12.3 п.12 требует тест, который уже существует

Пункт просит «отдельный integration-тест calculation-блока, проверяющий
преобразование `EphemerisConfigurationError` в `EPHEMERIS_UNAVAILABLE`».
Он есть:

```
tests/test_calculation_engine.py::test_engine_error_mapping_does_not_expose_source_messages
    (EphemerisNotInitializedError, CalculationUnavailableError, "EPHEMERIS_UNAVAILABLE")
    (EphemerisPathMismatchError,   CalculationUnavailableError, "EPHEMERIS_UNAVAILABLE")
```

**Правка.** Переформулировать пункт как ссылку на существующее покрытие,
иначе при реализации появится дубль.

### N-7. Пробелы в §12

- **BH-15** (один и тот же `RunContext` передан в оба порта) не покрыт ни
  одним тестом — при том что это единственный инвариант про телеметрию,
  который вообще можно проверить на стабах.
- Отображение «исход → уровень логирования» из §11 не покрыто; тест 17
  проверяет только отсутствие ПДн и `tz_id`. Уровень ERROR для
  `ENGINE_UNEXPECTED` — существенная часть §8.3 и стоит теста.
- Сквозной проброс `InputRequired` с **пустым** `issues` документ разрешает
  явно (контракт `InputRequired`), но тестом не закрепляет.

### N-8. Точечные неточности

1. **Место `Command`.** Таблица §3.1 помещает `Command` в
   `exact_orb.application.commands`, а код-блок §3.2 объявляет `class Command`
   внутри раздела «Порты handler», то есть визуально в `ports.py`. Нужно одно
   место; логичнее `commands.py`, тогда `ports.py` импортирует его для
   `TypeVar(bound=Command)` — цикла не возникает.
2. **Frozen для команд.** Не сказано, что `BuildNatalCommand` (и базовый
   `Command`) — frozen-модель. Все остальные сообщения в коде объявлены
   `ConfigDict(frozen=True)`. Заодно стоит решить форму `Command`: маркер-класс
   даёт множественное наследование `class BuildNatalCommand(Command, BaseModel)`
   (работает, проверено), но чище сделать сам `Command` frozen `BaseModel`.
3. **`@runtime_checkable` для портов.** Решение не принято. В коде есть
   осознанная асимметрия: `SessionPersistence` и `TechniqueAdapter` помечены,
   а `CalculationEnginePort` — намеренно нет, и это зафиксировано тестом
   `test_technique_adapter_is_runtime_checkable_but_engine_port_is_not`.
   Значит для новых портов выбор нужно сделать явно.
4. **Усечённые примеры `ChartSpec`.** В таблицах `ChartRef.spec`,
   `ChartArtifact.spec` и `StateDelta.base_chart_spec` спека по-прежнему
   показана как `{"technique":"natal","chart_kind":"natal"}`. После §12.1
   («spec целиком равна канонической») это читается как противоречие — стоит
   хотя бы один раз показать полную спеку со всеми шестью полями.
5. **Алерт по `ENGINE_UNEXPECTED`.** §8.3 требует его от «observability-слоя»,
   которого в проекте нет. Требование за границей документа — ему место в §14
   как открытому вопросу, иначе критерий готовности §13 формально не выполним.

---

## 3. Порядок правок

1. **N-3** и **N-5** — блокируют реализацию: без первого BH-13 не проверяем,
   без второго теряется наблюдаемость нештатных завершений.
2. **N-1** — одна фраза в §5, но без неё валидатор может падать мимо
   `ValidationError`.
3. **N-4** — одна фраза в §10.1, фиксирующая уже принятое решение.
4. **N-6**, **N-7** — правка блока тестов.
5. **N-2**, **N-8** — уточнения формулировок и примеров.

После этих правок документ можно считать готовым к реализации: контракты
соседей проверены и менять их действительно не требуется.
