# Промт 3. Сквозная приёмка bootstrap composition и финальные статусы

**Дата:** 2026-09-21.

**Ветка:** `chore/bootstrap-composition`.

**База:** `955ecb0a0ec8048c8f7b7dbb179ad059be1015e4`.

**Статус:** выполнен 2026-09-21.

**План:** [`bootstrap_composition_implementation_plan.md`](../../../docs/project_management/implementation_plans/bootstrap_composition_implementation_plan.md), §9.3.

## Для менеджмента: что и зачем мы делаем

Первые два шага создали lifecycle-примитив расчётного слоя и собрали
process-local `ApplicationRuntime`. Отдельные component-тесты уже доказали
правильность настроек, фактической версии расчёта, открытия SQLite, очистки
частично созданных ресурсов и штатного закрытия. Для завершения ветки нужно
проверить поведение всей собранной цепочки, которое нельзя подтвердить по
частям.

В этом шаге мы запускаем реальную пользовательскую команду через публичный
runtime: создаём SQLite-сессию, разрешаем данные рождения, рассчитываем карту,
сохраняем состояние и повторяем ту же команду. Первый вызов должен рассчитать
и положить артефакт в кэш, второй — получить его из кэша и выполнить новый
последовательный commit актуальной версии сессии.

Отдельно проверяем безопасную остановку при отменённом запросе. Расчёт уже
работает в calculation executor и продолжает жить как single-flight leader.
Runtime обязан дождаться его и только затем закрыть owned resources. Для
детерминизма calculator удерживается thread-safe barrier; реального ожидания и
случайных задержек в тесте нет.

После этого M1-5.1 считается завершённой. FastAPI-ветка M1-6 получает готовый
runtime и отвечает за HTTP/lifespan, прекращение приёма запросов, ожидание
request tasks и расписание reaper. Production fallback/DEBUG policy остаётся
M1-12.

## 1. Предмет доказательства

Промт закрывает только два оставшихся критерия ветки:

- **AC-2:** реальный Build Natal через публичный runtime, SQLite и cache
  miss → hit;
- **AC-9:** отменённый waiter, живой thread-backed leader и ожидание его
  завершения в `runtime.aclose()`.

Startup validation, partial-start cleanup и normal no-active shutdown не
дублировать: они принадлежат тестам промта 2.

## 2. Сквозной Build Natal

Добавить `tests/application/test_application_bootstrap_integration.py`.
Первый тест использует:

- реальный `build_application_runtime()`;
- реальный `LocalPlaceCatalog` из существующего fixture JSONL;
- реальный `BirthDataResolver`, `EngineService`, `calculate_natal`, artifact
  cache, SQLite persistence, `ContextService` и `ApplicationOrchestrator`;
- autouse ephemeris configuration процесса (`repo/ephe`, `true_perigee`);
- отдельный SQLite-файл из `tmp_path`;
- UTC fake clock без реального времени.

Сценарий и точные ожидания:

1. Создать одну сессию и подтвердить `state_version == 0`.
2. Выполнить `BuildNatalCommand` для `1990-09-02 14:30`, Москва `524901`.
3. Первый результат — `ApplicationCommitted(state_version=1)`.
4. После первого результата: `misses == 1`, `put_ok == 1`, `hits == 0`.
5. Повторить ту же команду для той же сессии новым `RunContext`.
6. Второй `execute()` сам загружает snapshot версии 1.
7. Второй результат — `ApplicationCommitted(state_version=2)`, не
   `ApplicationAlreadyApplied`.
8. Оба результата имеют одинаковые calculation key/version; после повтора
   `hits == 1`, `misses == 1`, `put_ok == 1`.
9. Финальный SQLite snapshot имеет `state_version == 2` и согласованные
   birth/chart fields.

## 3. Отменённый waiter и живой calculation leader

Второй тест собирает runtime через публичный `natal_calculator` override.
Calculator остаётся синхронным и выполняется настоящим `EngineService` в
calculation executor. Он:

- сообщает event loop о входе через `call_soon_threadsafe`;
- блокируется на `threading.Event`;
- после освобождения возвращает валидный `NatalChart`, согласованный с
  аргументами адаптера;
- фиксирует завершение и идентификатор worker thread.

Последовательность:

1. Создать сессию и запустить `runtime.orchestrator.execute()`.
2. Дождаться входа calculator в worker thread.
3. Отменить request waiter и подтвердить `CancelledError`.
4. Подтвердить, что состояние сессии осталось версией 0: commit не начался.
5. Запустить `runtime.aclose()` и через event-loop checkpoint доказать, что
   close не завершился, пока calculator удерживается barrier.
6. Освободить barrier и дождаться `aclose()`.
7. Подтвердить завершение calculator, работу вне event-loop thread и
   `misses == 1`, `put_ok == 1`, `hits == 0`.

Не использовать `sleep`. Timeout разрешён только как защита теста от
зависания. Не заменять calculator seam присваиванием
`runtime.artifacts.engine`: тест обязан оправдать публичный override фабрики.

Identity custom calculator не входит в `CalculationVersion`; тест использует
отдельный per-runtime in-memory cache. Shared cache для такого override без
отдельного versioning запрещён действующим docstring-контрактом.

## 4. Документация и статусы

После прохождения тестов:

1. Отметить промт 3 и всю ветку выполненными в implementation plan.
2. В roadmap отметить M1-5.1 выполненной, не объявляя готовыми M1-6/M1-12.
3. В overview/scenarios и актуальных calculation/artifact/Build Natal
   requirements заменить остаток «сквозная runtime-приёмка» фактическим
   подтверждением AC-2/AC-9.
4. Не объявлять реализованными HTTP, session middleware, request-task
   tracking, периодический reaper или production deployment guards.
5. В фактическом результате промта 1 уточнить историю ветки: `drain()` был
   единственным изменением поведения calculation-компонента именно в первом
   шаге; промт 2 затем добавил заранее оговорённый cancellation cleanup того
   же seam и сузил только docstring `engine.py`.
6. Записать точные результаты целевых, связанных и полного pytest.

## 5. Разрешённые файлы

- `prompts/2026-09-21/bootstrap-composition/03-bootstrap-integration-acceptance-and-status.md`
- `prompts/2026-09-21/bootstrap-composition/01-bootstrap-contract-and-resolver-drain.md`
- `tests/application/test_application_bootstrap_integration.py`
- `docs/project_management/bootstrap_composition_implementation_plan.md`
- `docs/project_management/roadmap.md`
- `docs/requirements/overview.md`
- `docs/requirements/scenarios.md`
- `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`
- `docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md`
- `docs/requirements/component_responsibilities/exact-orb_calculation_requirements.md`

Production-код не должен меняться. Если тест выявит дефект, сначала
зафиксировать корневую причину и только затем явно расширить allowlist.

## 6. Запреты

- Не добавлять FastAPI, HTTP, cookie, SSE, UI или CLI.
- Не добавлять background reaper, scheduler, gate или admission control.
- Не менять runtime/cache/SQLite/application outcomes ради теста.
- Не подменять предмет проверки fake orchestrator, fake persistence или fake
  artifact resolver.
- Не использовать другой session ID для cache-hit шага AC-2.
- Не ожидать `ApplicationAlreadyApplied` во втором последовательном вызове.
- Не использовать `sleep`, случайные задержки или polling loop.
- Не ослаблять module-boundary tests.
- Не создавать коммит, push или PR.

## 7. Проверки

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap_integration.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_chart_artifact_resolver.py tests/test_calculation_version.py tests/test_ephemeris_runtime_config.py tests/session -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
git diff --check
git status --short
```

Для изменённых Markdown-файлов проверить локальные ссылки. Полный pytest
запускать только после целевого и связанного наборов.

## 8. Итоговый отчёт исполнителя

Отчёт должен назвать:

- точные outcomes и cache counters AC-2;
- доказанный порядок AC-9 и способ thread-safe синхронизации;
- фактические команды и результаты проверок, включая полный pytest;
- итоговый статус M1-5.1 и оставшиеся обязанности M1-6/M1-12;
- отсутствие production-code изменений либо обоснование расширения;
- сохранённые unrelated-файлы рабочего дерева.

## 9. Фактический результат

Промт выполнен без изменений production-кода.

- **AC-2 закрыт.** Через публичный `ApplicationRuntime` выполнены два
  последовательных Build Natal для одной SQLite-сессии. Первый вызов вернул
  `ApplicationCommitted(state_version=1)`, второй —
  `ApplicationCommitted(state_version=2)`. После первого вызова счётчики кэша
  равны `misses=1`, `put_ok=1`, `hits=0`; после второго — `misses=1`,
  `put_ok=1`, `hits=1`. Финальный snapshot имеет `state_version=2` и
  согласованные birth/chart fields.
- **AC-9 закрыт.** Публичный `natal_calculator` override удерживает синхронный
  расчёт в calculation executor через `threading.Event`, а вход в worker
  сообщается event loop через `call_soon_threadsafe`. После отмены waiter
  состояние сессии остаётся версией 0. `runtime.aclose()` не завершается до
  освобождения barrier, затем дожидается leader; detached расчёт завершает
  cache put. `sleep` и polling не использовались.
- Статус M1-5.1 синхронизирован как выполненный. M1-6 по-прежнему владеет
  FastAPI/lifespan, request-task tracking и расписанием reaper; production
  fallback/DEBUG policy остаётся M1-12.

Фактические проверки:

```text
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application/test_application_bootstrap_integration.py -q
2 passed in 0.84s

.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/application tests/test_chart_artifact_resolver.py tests/test_calculation_version.py tests/test_ephemeris_runtime_config.py tests/session -q
1572 passed in 34.37s

.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_module_boundaries.py -q
36 passed in 2.83s

.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
2448 passed in 74.96s (0:01:14)

Markdown links: 10 branch-changed files checked, all local targets exist
git diff --check: passed
```

Unrelated untracked-файлы рабочего дерева не изменялись и не включались в
объём промта.
