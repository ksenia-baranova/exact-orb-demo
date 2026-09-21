# Промт 2. Сборка `ApplicationRuntime`

**Дата:** 2026-09-21.

**Ветка:** `chore/bootstrap-composition`.

**База:** `026a470734dd432a8bdd4afc6da76069c25e1969`.

**Статус:** выполнен 2026-09-21.

**План:** [`bootstrap_composition_implementation_plan.md`](../../../docs/project_management/implementation_plans/bootstrap_composition_implementation_plan.md), §9.2.

## Для менеджмента: что и зачем мы делаем

В проекте уже есть все основные части первого сценария: разрешение данных
рождения, расчёт карты, кэш, SQLite-сессии и application orchestrator. Пока
они собираются только в отдельных тестовых стендах. У сервера ещё нет одной
готовой точки запуска, которая создаёт production-компоненты в согласованном
порядке и отвечает за их ресурсы.

В этом шаге мы создаём такой process-local runtime. Он получает явные
настройки и готовый каталог мест, фиксирует фактическую конфигурацию
эфемерид, вычисляет версию расчёта, открывает SQLite, создаёт расчётный пул и
связывает существующие компоненты. При ошибке запуска уже созданные ресурсы
освобождаются. При штатной остановке runtime сначала дожидается текущих
расчётных задач, затем закрывает пулы в безопасном порядке.

Это снимает с будущей FastAPI-ветки обязанность повторно решать, как собирать
cache, engine, SQLite и orchestrator. M1-6 сможет взять готовый runtime,
добавить HTTP/lifespan и расписание очистки сессий. Production-политика
развёртывания, включая запрет fallback-эфемерид, остаётся M1-12.

Шаг доказывает корректную сборку, startup identity, partial-start cleanup и
штатное закрытие без активной операции. Реальный пользовательский Build Natal
с cache miss → hit и остановка при живом расчёте остаются третьему промту,
чтобы не смешивать доказательство сборщика со сквозным сценарием.

## 1. Технический результат

Добавить публичный модуль `exact_orb.application.bootstrap` с именами:

```python
BootstrapSettings
ApplicationRuntime
build_application_runtime
```

Фабрика имеет следующий контракт:

```python
async def build_application_runtime(
    *,
    settings: BootstrapSettings,
    places: PlaceCatalog,
    clock: Callable[[], datetime],
    natal_calculator: Callable[..., NatalChart] = calculate_natal,
) -> ApplicationRuntime: ...
```

Экспорт из `exact_orb.application.__init__` не добавлять: инфраструктурный
bootstrap должен импортироваться явно и не утяжелять package-level import.

## 2. Строгие настройки

`BootstrapSettings` — frozen Pydantic-модель с `strict=True` и
`extra="forbid"`. Она содержит только:

- `ephemeris_path: Path`;
- `selena_method: SelenaMethodName`;
- `session_db_path: Path`;
- `sqlite_busy_timeout_ms: int` — неотрицательный, `bool` запрещён;
- `sqlite_max_workers: int` — строго положительный, `bool` запрещён;
- `min_birth_date: date`;
- `max_birth_date: date`, не раньше `min_birth_date`;
- `cache_max_entries: int` — строго положительный, `bool` запрещён;
- `cache_ttl_seconds: float | None` — `None` либо конечный и строго
  положительный, `bool` запрещён;
- `engine_slow_threshold_ms: float` — конечный и строго положительный;
- `degraded_log_interval_s: float` — конечный и строго положительный.

Проверки зеркалируют действующие component validators. SQLite path отвергает
`:memory:` и `file:` URI, но отсутствие родительского каталога не считается
ошибкой чистой валидации. Все ошибки settings и UTC clock возникают до
создания executor'ов.

`DEFAULT_BODY_IDS`, `DEFAULT_EPHEMERIS_FLAGS`, calculation pool size `2` и
`resolve_unknown_birth_time_for_migration` не становятся настройками.

## 3. Порядок сборки

Соблюсти и проверить следующий порядок:

1. Проверить settings и один вызов clock через публичный `require_utc`.
2. Вызвать `configure_ephemeris` с явными path/method.
3. Прочитать фактические `EphemerisStatus` и Selena method.
4. Вычислить `CalculationVersionRecord` из фактического status и engine
   defaults; получить строку версии и записать startup log.
5. Создать SQLite executor и немедленно зарегистрировать его cleanup.
6. Открыть `SqliteSessionPersistence` с busy timeout и production migrator.
7. Создать calculation executor с `max_workers=2` и немедленно
   зарегистрировать cleanup.
8. Создать `NatalTechniqueAdapter`, `EngineService`, cache,
   `ChartArtifactResolver`, `BirthDataResolver` и `ContextService`.
9. Вызвать существующий `build_application_orchestrator`.
10. Только после полной успешной сборки передать ownership runtime.

Для reverse cleanup использовать `AsyncExitStack` или эквивалент. Повтор с
той же process-global ephemeris-конфигурацией допустим; несовпадение пути или
метода поднимает существующую typed config error до захвата ресурсов.

## 4. Единый clock и публичный runtime

Каждый вызов исходного clock оборачивается `require_utc`. Один и тот же
проверяемый wrapper передаётся `ContextService`, orchestrator и runtime.
`BirthDataResolver.today_provider` возвращает `checked_clock().date()`, то
есть UTC-дату.

`ApplicationRuntime` предоставляет read-only свойства:

- `orchestrator`;
- `context`;
- `artifacts`;
- `ephemeris_status`;
- `calculation_version_record`;
- `calculation_version`.

Persistence и оба executor'а остаются внутренними owned resources. Runtime
реализует:

```python
async def drain(self) -> None: ...
async def reap_expired(self, *, now: datetime | None = None) -> int: ...
async def aclose(self) -> None: ...
async def __aenter__(self) -> ApplicationRuntime: ...
async def __aexit__(...) -> None: ...
```

`reap_expired()` без `now` берёт время из checked clock; явно переданный
`now` тоже проверяется через `require_utc`. `aclose()` идемпотентен и в
штатном пути выполняет `artifacts.drain()` до закрытия calculation executor,
а SQLite executor закрывает последним.

## 5. Унаследованная lifecycle-проверка

До изменения callback cleanup добавить детерминированный тест случая, когда:

1. single-flight leader заблокирован управляемым async engine;
2. waiter отменён, leader продолжает работу;
3. `runtime.aclose()` входит в `drain()` и сам отменяется;
4. leader освобождается и падает;
5. loop exception handler не получает `Task/Future exception was never
   retrieved`;
6. повторный `aclose()` корректно завершает очистку.

Не использовать `sleep`. Если наблюдаемого шума нет на текущем CPython,
production callback не менять и записать это как проверенный предел. Если
шум воспроизводится, минимально исправить lifecycle cleanup вместе с тестом.

## 6. Тесты и критерии приёмки

Добавить `tests/application/test_application_bootstrap.py` и доказать:

1. **AC-1:** фабрика возвращает runtime с реальными component types и SQLite.
2. **AC-3/AC-11:** публичные status, record и version согласованы с
   фактическими ephemeris path/method и defaults; hash не фиксируется
   литералом.
3. **AC-4:** переданный `PlaceCatalog` используется resolver по identity.
4. **AC-5:** неверные настройки, extra-поля и naive clock отвергаются до
   создания executor'а; есть positive control валидной модели.
5. **AC-6:** повторная сборка с теми же path/method успешна, mismatch даёт
   существующую typed error до ресурсов.
6. **AC-7:** `tmp_path / "missing-parent" / "session.sqlite3"` проходит
   предварительную path-проверку, затем `SqliteSessionPersistence.open()`
   поднимает `StateWriteError(error_code="SESSION_SQLITE_OPEN_FAILED")`;
   SQLite executor закрыт, calculation executor ещё не создан, исключение
   не преобразовано.
7. **AC-8:** штатное закрытие без активных задач выполняется в порядке
   calculation → SQLite, повторный `aclose()` безопасен, async context
   manager закрывает runtime. Этот тест не объявляет доказанным живой
   cancelled-waiter сценарий промта 3.
8. **AC-10:** SQLite получает
   `resolve_unknown_birth_time_for_migration`.
9. **AC-12:** runtime использует существующий composition builder и текущий
   registry `BuildNatalCommand`, не создавая второй orchestrator contract.
10. `reap_expired(now=None)` использует внедрённый clock, а явный naive
    `now` отвергается до persistence call.
11. Унаследованный случай §5 проверен через loop exception handler.

Тесты конкурентности используют `asyncio.Event`; timeout допустим только как
защита от зависания. Приватные поля проверяются лишь для wiring и
lifecycle-инвариантов, которые нельзя наблюдать через публичный API.

## 7. Документация

- Сузить устаревшую шапку `calculation/engine.py`: реальная
  `CalculationVersion` теперь поставляется bootstrap-путём, а прямые CLI и
  тестовые стенды ещё могут использовать упрощённую версию.
- В Build Natal requirements заменить target-статус bootstrap на фактически
  реализованную assembly и явно оставить сквозную приёмку промту 3.
- В birth/session/overview/scenarios менять только статусы тех seams, которые
  действительно реализованы этим промтом.
- В chart-artifact requirements записать фактический результат проверки
  отменённого `aclose() → drain()`; не объявлять AC-9 закрытым.
- Обновить журнал implementation plan фактическими тестами.

## 8. Разрешённые файлы

- `prompts/2026-09-21/bootstrap-composition/02-build-application-runtime.md`
- `src/exact_orb/application/bootstrap.py`
- `src/exact_orb/calculation/engine.py`
- `tests/application/test_application_bootstrap.py`
- `docs/project_management/bootstrap_composition_implementation_plan.md`
- `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`
- `docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md`
- `docs/requirements/component_responsibilities/exact-orb_birth_data_resolution.md`
- `docs/requirements/component_responsibilities/exact-orb_session_requirements.md`
- `docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md`
- `docs/requirements/overview.md`
- `docs/requirements/scenarios.md`

`calculation/artifacts.py` разрешено добавить только при воспроизведённом
шуме из §5 и только для минимальной правки callback cleanup. Если тест чист,
файл не менять.

## 9. Запреты

- Не реализовывать FastAPI, lifespan, HTTP, cookies, SSE или UI.
- Не добавлять фоновый reaper, admission gate или production fallback guard.
- Не загружать `PlaceCatalog` внутри bootstrap.
- Не добавлять ephemeris reset или обход frozen process config.
- Не менять calculation/cache/session semantics, SQLite schema или outcomes.
- Не писать сквозной Build Natal cache miss → hit и AC-9 тест промта 3.
- Не ослаблять module-boundary tests.
- Не редактировать старые prompt-карточки.
- Не создавать коммит, push или PR.

## 10. Проверки

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_composition.py tests/test_calculation_version.py tests/test_ephemeris_runtime_config.py tests/session/test_sqlite.py tests/test_module_boundaries.py -q
git diff --check
git status --short
```

Полный pytest принадлежит финальной сквозной приёмке промта 3. Если новый
факт требует дополнительный связанный suite, запустить его и записать точную
команду и результат.

## 11. Итоговый отчёт исполнителя

Отчёт должен назвать:

- зачем появился единый runtime;
- фактический startup/shutdown contract;
- результат inherited shield-logger проверки и менялся ли resolver;
- точные команды и результаты тестов;
- что Build Natal cache miss → hit и live-leader shutdown остаются промту 3;
- какие unrelated файлы рабочего дерева сохранены без изменений.

## 12. Фактический результат выполнения

Добавлены strict `BootstrapSettings`, публичный `ApplicationRuntime` и
`build_application_runtime()`. Фабрика проверяет настройки и UTC clock до
ресурсов, фиксирует фактические ephemeris path/Selena method, вычисляет и
логирует `CalculationVersionRecord`, открывает реальный SQLite с production
migrator и собирает существующие resolver, cache, engine, context и
orchestrator. `PlaceCatalog` остаётся внешним портом.

Runtime возвращает публичные application/artifact/metadata поля, предоставляет
one-shot reaper и владеет обоими executor'ами. Partial-start failure закрывает
уже созданный SQLite executor и поднимает исходный
`StateWriteError(SESSION_SQLITE_OPEN_FAILED)`. Штатный `aclose()` выполняет
`drain → calculation executor → SQLite executor`, идемпотентен и поддерживает
async context manager.

Унаследованный тест воспроизвёл на текущем CPython loop-context
`ChartCalculationError exception in shielded future`, когда отменённый
`aclose()` оставлял падающий leader. `ChartArtifactResolver.drain()` получил
симметричную отменную очистку уже существующего shield callback. Повторный
`aclose()` после отмены освобождает ресурсы; leader не отменяется.

Проверки:

```text
tests/application/test_application_bootstrap.py                           26 passed
tests/test_calculation_cache.py                                            25 passed
composition + CalculationVersion + ephemeris config + SQLite + boundaries 339 passed
tests/test_chart_artifact_resolver.py                                      51 passed
```

Полный pytest не запускался: он принадлежит сквозной приёмке промта 3.
Build Natal cache miss → hit и ожидание живого расчёта через настоящий
calculation executor также остаются промту 3.
