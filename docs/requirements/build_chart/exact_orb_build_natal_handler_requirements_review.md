# Ревью требований к `BuildNatalHandler`

**Предмет ревью:** `exact_orb_build_natal_handler_requirements.md` (первая версия, 2026-09-08)
**Сверено с кодом:** `exact-orb-recovered`, рабочее дерево на 2026-09-08
**Метод:** построчная сверка контрактов документа с реализованными модулями
`birth/`, `calculation/`, `session/`, `outcomes.py`, `run_context.py`,
`domain.py`, `tests/test_module_boundaries.py`, а также с диаграммами
`docs/sequence_diagrams/build_natal/` и `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`.

Целевого модуля `src/exact_orb/application/handlers/build_natal.py` в дереве нет;
пакета `exact_orb.application` тоже нет. Документ проектирует ещё не написанный
модуль поверх уже реализованных соседей — поэтому ниже отделены расхождения
документа с кодом (A) от незакрытых мест самого документа (B).

---

## A. Противоречия

### A-1. §8.3 недостижимо на реальной проводке

Документ требует, чтобы неизвестные программные ошибки «оставались видимыми
как дефекты». Ниже границы handler это уже не так.

`calculation/engine.py`, `EngineService.calculate`:

```python
except Exception as exc:
    exception_type = type(exc).__name__
    mapped = _map_engine_error(exc, run_id)
    ...
    raise mapped from None
```

а `_map_engine_error` заканчивается безусловным
`return ChartCalculationError("ENGINE_UNEXPECTED", run_id=run_id)`.

Любой дефект внутри расчёта (AttributeError, KeyError, ошибка в адаптере)
приходит в handler уже как доменный код `ENGINE_UNEXPECTED` и по §8.1
превращается в `CalculationFailed`. Тест §12.3 п.9 («неизвестное исключение
не маскируется») проверит только поведение stub-а, а не системы.

**Что решить.** Либо переформулировать инвариант как «handler не добавляет
собственной маскировки» (границей маскировки признан `EngineService`), либо
завести требование: `ENGINE_UNEXPECTED` трактуется как замаскированный дефект
и обязателен к логированию с `exception_type` (`EngineService` это уже делает
в `calculation_failed`), плюс отдельный алерт.

### A-2. §12.4 п.11 (запрет импортов) невыполним в заявленном виде

Запрещён импорт `exact_orb.engine.charts`. Но:

- `BuildNatalSuccess.artifact: ChartArtifact` → `exact_orb.calculation.types`
  → `from exact_orb.engine.charts.natal import NatalChart`;
- `artifacts: ChartArtifactResolver` → `exact_orb.calculation.artifacts`
  → `.engine` → `exact_orb.engine.charts.natal` → native-стек.

То есть транзитивно `engine.charts` (и swisseph) попадают в import-граф
handler всегда. Требование выполнимо только как «нет прямого объявления
импорта».

Существующий `tests/test_module_boundaries.py` уже различает эти две вещи —
списки объявленных импортов (`SESSION_SERVICE_FORBIDDEN_IMPORTS`) и запреты
на runtime-граф (`SESSION_FORBIDDEN_AT_RUNTIME`, куда как раз входят
`exact_orb.calculation.types`, `.artifacts`, `.engine`, `.codec`). Документ
должен говорить в тех же терминах и отдельно ответить: допускается ли
swisseph в import-графе application-слоя.

Кроме того, `exact_orb.agent` в списке запрещённых **не существует**.
Фактические соседи, которые надо запрещать: `exact_orb.intent`,
`exact_orb.interpretation`, `exact_orb.llm`, `exact_orb.orchestration`,
`exact_orb.tools`, `exact_orb.cli`, `exact_orb.config`.

### A-3. Зависимости типизированы конкретными классами, а не портами

§3 объявляет `resolver: BirthDataResolver`, `artifacts: ChartArtifactResolver`.
Весь остальной код держит порты протоколами: `PlaceCatalog`,
`CalculationEnginePort`, `TechniqueAdapter`, `SessionStore`, `DialogStore`,
`SessionPersistence`. Конкретные аннотации не только ломают стиль, но и
усиливают A-2: аннотация `ChartArtifactResolver` тянет engine на import-time.

**Что решить.** Ввести порты (`BirthDataResolverPort`, `ChartArtifactPort`)
или импортировать типы под `if TYPE_CHECKING` с `from __future__ import annotations`.

### A-4. Пример `calculation_key` не проходит валидацию

Документ: `"exact-orb:chart:v1:89f…"`.
Код (`calculation/keys.py`): `SCHEMA_VERSION = "v1"`, `KEY_PREFIX = "eo:calc:v1:"`,
и `ChartArtifact._calculation_key_must_have_prefix` отвергает всё остальное.
Пример в таблице контракта надо заменить на `"eo:calc:v1:89f…"`.

### A-5. `session_id` в команде: документ против диаграммы

§4.1 (и components-doc §3.6) — `session_id` в команду не входит.
`000-build_natal_end_to_end.puml`:

```
API -> Orch : BuildNatalCommand(session_id, birth_input)
```

Документ прав, диаграмма устарела. Раздел §8 уже фиксирует одно расхождение
с диаграммами (`CalculationFailed`) — это второе, его стоит зафиксировать там же.

### A-6. Нота диаграммы 000 отрицает `AMBIGUOUS`, который реален

Нота: «Свободный текст места не принимается (ADR-0005), поэтому AMBIGUOUS
на этом пути не возникает». Но `AMBIGUOUS` в текущем коде рождается не из
места, а из времени — `birth/resolver.py`:

```python
elif isinstance(tz_resolution, TzAmbiguous):
    if not time_unknown:
        outcome = InputRequired(issues=(Issue(field="birth.time",
                                              code="AMBIGUOUS",
                                              candidates=tz_resolution.offsets),))
```

§7.1 документа описывает это корректно. Нота диаграммы вводит в заблуждение
и должна быть исправлена, иначе следующий читатель уберёт ветку `AMBIGUOUS`
из обработки.

### A-7. Дубль `RunContext`

Components-doc §2 размещает `RunContext` в `application/run_context.py`.
В коде он уже в `exact_orb/run_context.py` и зафиксирован в
`tests/test_module_boundaries.py` (`CONTRACT_MODULES`,
`SESSION_RUNTIME_KNOWN_TRANSITIVE_DEBT`). Новый документ ссылается на
`RunContext` как на данность, не называя модуль. При создании пакета
`application` это гарантированно породит второй `RunContext`.
Нужно явно записать: остаётся в `exact_orb.run_context`, в `application` не переносится.

### A-8. BH-10 проверяет тавтологию

`SessionState` — `model_config = ConfigDict(frozen=True)`. «Handler не изменяет
переданный `SessionState`» выполняется физически, тест §12.4 п.12 ничего не
доказывает. Осмысленная формулировка: handler не строит производного состояния,
не вызывает `apply_delta`/`touched` и не передаёт `state` в нижележащие вызовы.

---

## B. Упущенные места

### B-1. Не задано размещение `BuildNatalCommand`, `BuildNatalSuccess`, `BuildNatalOutcome`

Целевой модуль указан один — `handlers/build_natal.py`. Components-doc §2
разносит: `application/commands.py` (команда) и `application/results.py`.
Там же имя результата — **`BuildNatalResult`**, тогда как §7.1 того же
документа и весь новый документ используют **`BuildNatalSuccess`**.
Нужно одно имя и один адрес для каждого из трёх типов.

### B-2. Нет протокола `Handler` и базового типа `Command`

`ApplicationOrchestrator` по components-doc держит
`Mapping[type[Command], Handler]`. Ни `Command`, ни `Handler` документ не
вводит. Пока handler один, это незаметно; на втором контракт придётся
изобретать задним числом, ломая сигнатуру оркестратора.

### B-3. Не сказано, кто держит BH-7 и BH-8

Фактически оба инварианта уже гарантированы ниже handler:

- BH-8 — `ChartArtifact._validate_identity` (`chart_kind == spec.chart_kind`
  и `== chart.chart_kind`);
- BH-7 — `ChartArtifactResolver._get_valid_hit` отбрасывает попадание кэша
  при `artifact.spec != spec`, поэтому вернуть артефакт с чужой спекой нельзя.

Стоит записать явно: handler инварианты не перепроверяет, а тесты §12 не
дублируют чужие. Либо, наоборот, обязать `BuildNatalSuccess` быть pydantic-моделью
с `model_validator`, проверяющим `artifact.spec == delta.base_chart_spec` —
это дёшево и делает BH-7/BH-8 неразрушимыми на границе.

### B-4. Не описана судьба `warnings`

`ResolvedBirthData.warnings` (`pre_1970_offset_unverified`, `noon_anchor_adjusted`,
`noon_anchor_ambiguous`) и `ChartArtifact.warnings` по диаграмме 000 и И-7
должны доходить до пользователя/промпта. В §5–§6 handler их не трогает — это
верно (они едут внутри `delta.birth_resolved` и внутри артефакта), но не сказано.
Нужен явный non-responsibility, иначе на ревью появится соблазн собирать
их в отдельное поле исхода.

### B-5. Нет требований к исключениям из резолва

§8 описывает только расчётный блок. Между тем `BirthDataResolver.resolve`
может поднять `TypeError` (ветка `else: raise TypeError(f"Unexpected timezone
resolution: ...")`), а `PlaceCatalog.lookup` — любое исключение, кроме
`PlaceCatalogUnavailableError` (у будущего сетевого каталога это норма).
Нужна симметричная §8.3 формулировка: исключения из резолвера не
перехватываются и не превращаются в `ResolutionUnavailable`.

### B-6. §11 не задаёт отображение «исход → событие»

Пять событий на четыре исхода. Не определено:

- `InputRequired` — это `build_natal_completed` с `outcome=input_required`
  или `build_natal_failed`?
- логируется ли `build_natal_resolve_completed` при неуспешном резолве;
- уровни логирования (в соседях: `birth_resolution` — INFO,
  `calculation_failed` — WARNING);
- что `chart_kind` физически отсутствует в событиях до шага 2 — значит поля
  надо пометить как опциональные.

### B-7. Политика ПДн в логах шире одного handler

BH-16 запрещает handler-у логировать координаты и полный `ResolvedBirthData`.
При этом сосед уже пишет на INFO:

```python
LOGGER.info("birth_resolution run_id=%s outcome=resolved tz_id=%s duration_ms=%.3f", ...)
```

`tz_id` в запретном списке §11 отсутствует, но это квазигеоданные. Либо
признать `tz_id` допустимым и записать это, либо распространить политику
на блок целиком — иначе BH-16 соблюдается в handler и обходится рядом.

### B-8. Ничего про тайм-ауты и семантику отмены

§8.3 запрещает подавлять `CancelledError`, но не сказано, что handler не
ставит собственный тайм-аут на `ensure_chart`. Это существенно, потому что
`ChartArtifactResolver._ensure_singleflight` использует `asyncio.shield`:
отмена присоединившегося вызова **не** останавливает расчёт лидера. Без
явной записи это всплывёт на ревью как «утечка задачи».

### B-9. Не сказано, что handler не валидирует `state`

Раз §4.2 объявляет `state` неиспользуемым, стоит зафиксировать и обратное:
handler не проверяет `state.expires_at`, не сверяет `state.state_version`
и не сравнивает `state.birth_input` с командой. Истечение проверяется
в `session.state._reject_expired` / `ContextService`.

### B-10. BH-18 на системном уровне неполон

`session/state.py::matches_intent` сравнивает только `birth_resolved` и
`base_chart_spec`; `birth_input` в сравнение **не входит**. Следствие: команда,
дающая тот же `ResolvedBirthData` и ту же спеку, но иной `BirthInput`,
классифицируется оркестратором как `AlreadyApplied`, и сохранённый в состоянии
`birth_input` не обновится, хотя дельта его несёт. Handler здесь ни при чём,
но §5 обосновывает состав дельты — следствие надо назвать явно или вынести
в `docs/requirements/session/open-questions.md`.

### B-11. Тесты §12.1 сформулированы слабее, чем позволяет код

«`include` содержит дома, управителей и strength» — проверяемо строже.
`normalize_include` возвращает отсортированный дедуплицированный tuple,
поэтому спека детерминирована. Проверено прогоном:

```
NatalChartSpec(chart_kind="natal")
  == NatalChartSpec(chart_kind="natal",
                    include=("aspects","configurations","houses","positions","rulers","strength"),
                    house_system="P", rulership="combined",
                    near_interception_threshold=1.0)     # True
NatalChartSpec(chart_kind="cosmogram").include
  == ("aspects", "configurations", "positions")           # True
```

Тест стоит формулировать как равенство спек целиком — это ровно то, чего
требует §3, шаг 3 («критично проверять итоговое значение спецификации»).

### B-12. Достижимость `EPHEMERIS_UNAVAILABLE` в unit-тестах

§13 требует, чтобы все четыре исхода были достижимы и покрыты. В реальном
стеке `CalculationUnavailableError("EPHEMERIS_UNAVAILABLE")` рождается только
из `EphemerisConfigurationError` внутри `_map_engine_error`. В unit-тестах
handler он достижим лишь через stub `ensure_chart`. Стоит записать это прямо,
чтобы «покрыт» не путали с «воспроизведён на реальном движке».

### B-13. Зеркальный тест границ для `application` не заведён

`exact_orb.application` уже фигурирует как запрещённый импорт в
`RESEARCH_FORBIDDEN_IMPORTS`, `SESSION_FORBIDDEN_AT_RUNTIME`,
`SESSION_ADAPTER_FORBIDDEN_IMPORTS`, `SESSION_SERVICE_FORBIDDEN_IMPORTS` —
то есть пакет ожидается кодовой базой. Обратного списка («что запрещено самому
application») нет. §12.4 п.11 — его заготовка; надо оформить константой
`APPLICATION_FORBIDDEN_IMPORTS` в `tests/test_module_boundaries.py` в том же
стиле и с учётом A-2.

### B-14. «Непустой набор `Issue`» моделью не обеспечен

Контракт `InputRequired` в документе: «Непустой набор `Issue`».
Код: `issues: tuple[Issue, ...]` без `min_length`. Раз handler обязан
пробрасывать объект без изменений, либо усилить модель, либо снять слово
«непустой» из документа.

### B-15. `Issue.code = MISSING` недостижим текущим резолвером

Пустой `place_id` даёт `PlaceNotFound` → `INVALID`; отсутствующая дата
отсекается pydantic на входе `BirthInput`. Список «возможных примеров» в §7.1
стоит пометить как исчерпывающий **для текущей реализации резолвера**.

---

## C. Что сверено и сходится

- сигнатуры коллабораторов: `BirthDataResolver.resolve(birth_input, *, run=None)`,
  `ChartArtifactResolver.ensure_chart(spec, resolved, *, run)` — совпадают с §6;
- три исхода резолва ровно те, что описаны, и `ResolutionUnavailable` несёт
  `retryable=True` для `PLACE_CATALOG_UNAVAILABLE` и `False` для `UNKNOWN_TIMEZONE`;
- коды ошибок расчёта совпадают с `calculation/errors.py` один в один
  (4 + 1), `ArtifactError.code` доступен как атрибут — `CalculationFailed(error_code=error.code)` корректен;
- `NatalChartSpec(chart_kind=...)` действительно даёт канонический `include`
  через `DEFAULT_INCLUDE_BY_CHART_KIND` — §3 шаг 3 подтверждён прогоном;
- `StateDelta` в `session/state.py` имеет ровно три поля и инвариант
  all-set / all-None; `ChartRef` и новая версия присваиваются в `apply_delta`,
  а не в handler — §5 и BH-11 согласуются с кодом;
- `InputRequired`, `ResolutionUnavailable`, `CalculationFailed` уже существуют
  в `exact_orb/outcomes.py` — новых типов исхода заводить не требуется;
- cache hit / miss, single-flight, corrupt/stale и fail-open полностью скрыты
  внутри `ChartArtifactResolver` — §3.2 и BH-17 держатся;
- `asyncio.CancelledError` не перехватывается ни `EngineService` (`except Exception`),
  ни `ChartArtifactResolver` (перехватывает и пробрасывает) — BH и §8.3 в этой
  части реализуемы.

---

## D. Предлагаемый порядок правок документа

1. A-4, A-5, A-6 — фактические ошибки, правятся точечно.
2. A-2 + A-3 + B-13 — один связанный блок: переписать §12.4 п.11 в терминах
   «прямые импорты / runtime-граф», ввести порты, зафиксировать судьбу swisseph
   в application-слое.
3. A-1 — решение по маскировке дефектов; влияет на §8.3 и на тест §12.3 п.9.
4. B-1, B-2, A-7 — решение о структуре пакета `application` до написания кода.
5. B-4, B-5, B-6, B-8, B-9 — дописать явные non-responsibility и журнал.
6. B-3, B-11, B-14 — усилить тесты и модели.
7. B-10 — вынести в open-questions сессии.
