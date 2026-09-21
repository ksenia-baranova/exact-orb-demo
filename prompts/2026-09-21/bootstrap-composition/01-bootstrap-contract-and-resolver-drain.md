# Промт 1. Bootstrap contract и `ChartArtifactResolver.drain()`

**Дата:** 2026-09-21.

**Ветка:** `chore/bootstrap-composition`.

**База:** `74b8423b63179b413763a4e4a03734627ebe24d8`.

**Статус:** выполнен 2026-09-21.

**План:** [`bootstrap_composition_implementation_plan.md`](../../../docs/project_management/implementation_plans/bootstrap_composition_implementation_plan.md), §9.1.

## Для менеджмента: что и зачем мы делаем

Расчётный, сессионный и application-слои уже существуют, но перед созданием
HTTP-сервера нужно закрепить одного владельца их общей сборки. Сейчас roadmap
одновременно оставляет production bootstrap будущему серверному этапу и содержит
отдельную ветку composition. Если это не исправить заранее, FastAPI-ветка начнёт
сама создавать cache, engine, SQLite и orchestrator, а затем те же обязанности
появятся во второй точке запуска.

Есть и практическая проблема остановки. Расчёт артефакта защищён от отмены
клиентского ожидания: пользовательский запрос может завершиться, а общая
single-flight задача продолжит расчёт и запись в кэш. Это правильное поведение,
но будущий runtime должен уметь дождаться такой задачи перед закрытием executor.
Сейчас публичного способа сделать это нет.

В этом шаге мы:

1. однозначно разделяем ответственность между новой runtime composition,
   FastAPI/lifespan и deployment-конфигурацией;
2. добавляем в артефактный резолвер маленький публичный `drain()`, который ждёт
   уже начатые single-flight leader-задачи;
3. доказываем lifecycle-контракт детерминированным тестом без реального ожидания;
4. фиксируем UTC-дату для верхней границы даты рождения и владельца запуска
   session reaper.

После шага серверная команда получает ясную границу: M1-6 будет потреблять
готовый runtime, учитывать request tasks и планировать reaper. Полная сборка
runtime появится во втором промте. Этот шаг ещё не создаёт FastAPI, settings,
executor'ы или SQLite wiring.

## 1. Технический контекст

- [`application/composition.py`](../../../src/exact_orb/application/composition.py)
  уже собирает минимальный `ApplicationOrchestrator` из готовых зависимостей.
- [`ChartArtifactResolver`](../../../src/exact_orb/calculation/artifacts.py)
  создаёт process-local leader task и ждёт её через `asyncio.shield`.
- После отмены всех waiter'ов leader продолжает работу и может обратиться к
  calculation executor и cache.
- `_inflight` очищается самой leader task в `finally`; runtime не должен читать
  или менять этот словарь напрямую.
- SQLite уже предоставляет one-shot `reap_expired(now=...)`, но production
  scheduler отсутствует.
- `BirthDataResolver` по умолчанию использует локальную `date.today()`. Будущий
  bootstrap передаст `today_provider`, выведенный из единого UTC clock.

## 2. Результат промта

После выполнения:

- в roadmap есть отдельная runtime-composition задача между M1-5 и M1-6;
- M1-6 явно потребляет готовый runtime и владеет request tracking и расписанием
  reaper;
- M1-12 явно владеет production fail-fast для ephemeris fallback и DEBUG guard;
- актуальные requirements описывают UTC-date semantics и разделение one-shot
  reaper/scheduler;
- `ChartArtifactResolver.drain()` ждёт текущих leader tasks;
- тест доказывает ожидание живого leader после отмены waiter;
- поведение расчёта, cache и single-flight не меняется.

## 3. Обязательные изменения

### 3.1. Документация и roadmap

1. Оставить M1-3 завершённой минимальной application composition.
2. Добавить отдельную runtime-composition задачу после M1-5 и до M1-6.
3. Удалить из M1-5 обязанность подключать каталог внутри server composition:
   bootstrap принимает готовый `PlaceCatalog` через порт.
4. Уточнить M1-6:
   - FastAPI/lifespan получает готовый `ApplicationRuntime`;
   - транспорт прекращает приём и ждёт начатые request tasks, включая отменённые;
   - M1-6 периодически вызывает one-shot `runtime.reap_expired()`.
5. Уточнить M1-12:
   - production startup отвергает `EphemerisStatus.mode != "files"`;
   - сохраняется проверяемый guard от случайного DEBUG.
6. В birth-data requirements записать, что server bootstrap выводит
   `today_provider` из проверенного UTC clock. Это намеренная UTC-дата, а не
   локальная дата хоста.
7. В session requirements и ADR-0024 разделить владельцев:
   persistence предоставляет one-shot reaper, runtime предоставляет one-shot
   вызов, M1-6 владеет периодическим расписанием.
8. В chart-artifact requirements добавить lifecycle-контракт `drain()` и
   приёмочный тест.
9. Согласовать target bootstrap в Build Natal requirements с новым планом:
   внешний `PlaceCatalog`, SQLite runtime и готовый `ApplicationRuntime`; не
   объявлять это реализованным до второго промта.
10. Обновить текущие overview/scenarios только в местах, где они назначают
    lifecycle executors или reaper неопределённой будущей composition.

### 3.2. `ChartArtifactResolver.drain()`

Добавить публичный async-метод:

```python
async def drain(self) -> None: ...
```

Контракт:

- метод делает snapshot leader tasks, находящихся в single-flight на момент
  вызова;
- ждёт их фактического завершения;
- не отменяет leader tasks;
- не поднимает их расчётные исключения вызывающему drain;
- корректно обрабатывает success, exception и cancellation leader task;
- немедленно завершается при отсутствии активных задач;
- не вводит gate и не запрещает новые `ensure_chart()`;
- не меняет cache counters, результаты waiter'ов или cleanup `_inflight`.

Конкретная приватная структура не является контрактом. Дополнительный task set
не вводить, если текущий `_inflight` и детерминированный тест уже доказывают
требуемое поведение.

Сузить module docstring `artifacts.py`: `CalculationVersion` уже существует.
Нужно указать, что будущий `ApplicationRuntime` является владельцем реальной
версии, а прямые CLI/тестовые callers по-прежнему передают готовую строку.

### 3.3. Тесты

В `tests/test_chart_artifact_resolver.py` добавить детерминированное покрытие:

1. Создать resolver с управляемым async engine на `asyncio.Event`.
2. Запустить `ensure_chart()` и дождаться входа engine.
3. Отменить waiter и подтвердить `CancelledError`.
4. Сохранить ссылку на component-owned leader task только для существенного
   lifecycle-инварианта.
5. Запустить `drain()` и через event-loop checkpoint доказать, что он уже
   получил управление, но не завершился до освобождения engine.
6. Освободить engine и дождаться `drain()`.
7. Проверить `leader_task.done()`, запись в cache и отсутствие `_inflight`.
8. Добавить простой случай без активных задач.

Не использовать `sleep` или случайные задержки. Timeout допустим только как
защита теста от зависания. Не заменять async `CalculationEnginePort`
синхронным calculator: calculator seam относится к интеграционному промту 3.

## 4. Разрешённые файлы

- `prompts/2026-09-21/bootstrap-composition/01-bootstrap-contract-and-resolver-drain.md`
- `src/exact_orb/calculation/artifacts.py`
- `tests/test_chart_artifact_resolver.py`
- `docs/project_management/roadmap.md`
- `docs/project_management/roadmap_remote_ui_and_interpretation_plan.puml`
- `docs/project_management/bootstrap_composition_implementation_plan.md`
- `docs/requirements/component_responsibilities/exact-orb_chart_artifacts.md`
- `docs/requirements/component_responsibilities/exact-orb_birth_data_resolution.md`
- `docs/requirements/component_responsibilities/exact-orb_session_requirements.md`
- `docs/requirements/component_responsibilities/exact-orb_build_natal_components.md`
- `docs/requirements/decisions/0024-sqlite-storage-implementation.md`
- `docs/requirements/overview.md`
- `docs/requirements/scenarios.md`

PNG календаря можно перегенерировать только при наличии рабочего локального
PlantUML. Отсутствие renderer нужно записать в отчёте; подменять PNG вручную
нельзя.

## 5. Запреты

- Не создавать `ApplicationRuntime`, `BootstrapSettings` или
  `build_application_runtime`.
- Не менять `engine.py`; сужение его `Known debt` принадлежит промту 2.
- Не менять `application/composition.py` и публичные application outcomes.
- Не добавлять gate, resolver close, cancel-all или новую background task.
- Не менять cache/codec/key semantics и расчётные значения.
- Не добавлять FastAPI, HTTP, cookie, UI, CLI, LLM, admission или deployment
  implementation.
- Не ослаблять module-boundary tests.
- Не редактировать старые prompt-карточки.
- Не создавать коммит, push или PR.

## 6. Критерии приёмки

1. Все изменения находятся в allowlist.
2. Roadmap больше не назначает runtime assembly M1-6 или M1-5.
3. M1-6 и M1-12 имеют точные владельческие обязанности из §3.1.
4. UTC-date и reaper ownership записаны без объявления ещё не реализованного
   runtime готовым.
5. `drain()` ждёт текущего leader после отмены waiter и возвращает только после
   `leader_task.done()`.
6. Успешная detached работа по-прежнему записывает артефакт в cache.
7. Empty drain безопасен.
8. Существующие single-flight, cancellation и exception tests проходят.
9. Module-boundary tests проходят без ослабления.
10. `git diff --check` чист.

## 7. Проверки

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_chart_artifact_resolver.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_module_boundaries.py -q
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_chart_artifact_resolver.py tests/test_chart_artifact_codec.py tests/test_calculation_cache.py tests/test_calculation_version.py -q
git diff --check
git status --short
```

Если PlantUML доступен, проверить source и перегенерировать соответствующий PNG
штатным способом проекта. Если недоступен, выполнить структурную проверку `.puml`
и явно оставить PNG непроверенным визуально.

## 8. Итоговый отчёт исполнителя

Отчёт должен назвать:

- зачем добавлен lifecycle seam;
- фактические code/document changes;
- точные команды и результаты проверок;
- был ли перегенерирован календарный PNG;
- что полный runtime и сквозной shutdown остаются промтам 2–3;
- какие unrelated файлы рабочего дерева сохранены без изменений.

## 9. Фактический результат выполнения

Добавлен `ChartArtifactResolver.drain()`: метод делает snapshot текущих
single-flight leader tasks, ждёт их через `asyncio.shield` и принимает success,
exception или cancellation без отмены общей работы и без проброса её ошибки
вызывающему drain. Gate и отдельный task registry не понадобились.

Детерминированный параметризованный тест подтверждает все три исхода leader.
Для success дополнительно доказано, что после отмены waiter артефакт всё равно
попадает в cache, а drain возвращается только после `leader_task.done()`.
Отдельный тест закрепляет empty drain.

Roadmap обновлён до v3.4: M1-5.1 стоит между каталогом и FastAPI, оценён в два
рабочих дня, а зависимые даты календарного source сдвинуты. M1-6 потребляет
готовый runtime и владеет request tasks/reaper schedule; M1-12 владеет
production fallback/DEBUG guards. Requirements синхронизированы по UTC-date,
runtime wiring, resolver drain и reaper ownership.

Проверки:

```text
tests/test_chart_artifact_resolver.py                                      51 passed
tests/test_module_boundaries.py                                            36 passed
resolver + codec + cache + CalculationVersion                             153 passed
local Markdown links                                                       passed
PlantUML structural check: 30 aliases, 11 property references              passed
git diff --check                                                           passed
```

Локальные `plantuml` и `java` недоступны, поэтому PNG календаря не
перегенерирован и визуально не проверен. Полный pytest не запускался: промт
ограничен resolver lifecycle, затронутые calculation suites и module
boundaries прошли. Полный runtime, owned executors и сквозной runtime shutdown
остаются промтам 2–3.

Итоговая синхронизация ветки: `drain()` был единственным изменением поведения
существующего calculation-компонента именно в промте 1. Промт 2 затем добавил
заранее оговорённый cancellation cleanup того же lifecycle seam и уточнил
только module docstring `engine.py`; расчётные, cache и artifact semantics не
расширялись.
