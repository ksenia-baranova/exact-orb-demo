# exact-orb

## О проекте

**exact-orb — R&D-проект об управляемой разработке с AI-агентами.** Он исследует, насколько далеко специалист с сильными навыками управления, системного анализа и тестирования может продвинуть разработку программного продукта, делегируя агентам написание кода и часть технической проработки.

Цель проекта — показать не только результат такой разработки, но и инженерные механизмы, необходимые для сохранения контроля над ней: формализацию требований, архитектурные решения, явные контракты и границы ответственности компонентов, проектирование сценариев, автоматизированные тесты и последовательную проверку результатов работы агентов.

Предметная область выбрана не случайно. Расчёт астрологических карт позволяет на конкретном примере соединить два принципиально разных типа обработки:

* точные, воспроизводимые и проверяемые детерминированные расчёты;
* вероятностный слой интерпретации естественного языка с использованием LLM.

Это делает проект удобным полигоном для исследования архитектуры систем, в которых языковая модель не является источником фактов, а работает только в пределах подготовленного и проверяемого контекста.

Проект остаётся открытым: выбранная предметная область позволяет публиковать исходный код, требования, архитектурные решения, тестовые сценарии и результаты экспериментов без раскрытия корпоративных данных или внутренней бизнес-логики.

> Предметная область используется как инженерный case study. Проект не исследует научную валидность астрологии; интерес представляет архитектурная задача разделения вычислимого источника фактов и вероятностного слоя их интерпретации.

---

## Что исследует проект

У проекта две связанные исследовательские линии.

### Детерминированное ядро + LLM

Главный архитектурный принцип:

> **LLM не является источником расчётных фактов.**

Положения небесных тел, дома, аспекты, конфигурации и другие вычисляемые показатели появляются только в результате детерминированного расчёта.

Языковая модель может работать поверх подготовленного evidence:

```text
structured input
      │
      ▼
deterministic resolution
      │
      ▼
deterministic calculation
      │
      ▼
validated chart artifact
      │
      ▼
evidence selection
      │
      ▼
LLM interpretation
```

LLM может интерпретировать и объяснять рассчитанные данные, но не должна самостоятельно достраивать отсутствующие факты карты.

### Управляемая разработка с AI-агентами

Вторая линия эксперимента — процесс создания самого проекта.

LLM используется как инструмент анализа и исполнения в нескольких ограниченных ролях:

* исследование архитектурных альтернатив и проверка их последствий;
* помощь в выявлении и разборе corner cases;
* проверка выбранного решения на противоречия и скрытые последствия;
* формализация принятых владельцем решений в требования, ADR и диаграммы;
* подготовка implementation tasks на основе утверждённых контрактов;
* написание кода в заданных архитектурных и функциональных границах;
* отдельный review реализации против требований;
* помощь в проектировании regression-сценариев для найденных дефектов.

**LLM расширяет пространство анализа и ускоряет реализацию, но не определяет продуктовую семантику и не принимает архитектурные решения.** Владелец проекта формулирует проблему и ограничения, выбирает между альтернативами, определяет допустимое поведение в спорных и пограничных сценариях, утверждает спецификацию и принимает итоговую реализацию.

Подробное описание процесса:

[`docs/development_approach/spec-driven-development.md`](docs/development_approach/spec-driven-development.md)

Коротко:

```text
архитектурное обсуждение
    → решение владельца
    → ADR / требования / диаграммы
    → implementation task
    → реализация
    → LLM-review
    → детерминированная проверка
    → коммит
```

---

## Инженерные принципы

* **Детерминированное ядро.** Одинаковый вход, версия расчёта и набор эфемерид должны давать одинаковый результат.
* **LLM работает с evidence.** Вероятностный слой объясняет подготовленные системой факты, но не создаёт их.
* **Явные границы компонентов.** Resolution, calculation, artifact/cache lifecycle, application coordination, session state и agent execution разделены.
* **Типизированные контракты.** На границах используются commands, outcomes, ports, specifications и state deltas.
* **Архитектурные правила по возможности исполняемы.** Существенные dependency boundaries закрепляются тестами.
* **Дефект становится regression-тестом.** Исправление должно превращать найденный сценарий ошибки в воспроизводимую проверку.
* **Минимальный scope изменения.** Implementation task не является разрешением на сопутствующий рефакторинг.

---

## Текущее состояние

Проект находится в активной R&D-разработке.

Первый детерминированный application-сценарий уже проходит через реальные компоненты:

```text
birth input
    → birth-data resolution
    → natal / cosmogram decision
    → chart artifact resolution
    → cache / version validation
    → deterministic engine
    → chart artifact
    → StateDelta
```

### Состояние компонентов

| Компонент                                           | Состояние                                                                                                                     |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `engine/`                                           | **Реализован** — натальная карта, космограмма, транзиты, аспекты, конфигурации, сила и структура                              |
| `birth/`                                            | **Реализован** — birth-data normalization, place и historical timezone resolution                                             |
| `calculation/`                                      | **Реализован** — `ChartSpec`, calculation version/key, engine adapter, codec, cache и artifact resolution                     |
| `session/`                                          | **Реализована основа** — state contracts, `ContextService`, persistence contracts, in-memory и SQLite adapters                |
| `research/`                                         | **Частично реализован** — модели, projection и in-memory corpus; persistence и дальнейший application wiring ещё не завершены |
| `application/commands.py`, `ports.py`, `results.py` | **Реализованы** типизированные application-контракты                                                                          |
| `BuildNatalHandler`                                 | **Реализован и интеграционно протестирован**                                                                                  |
| Application Orchestrator                            | **Следующий этап** — lifecycle пользовательской операции, freshness/idempotency и state commit                                |
| `cli.py`                                            | **Работает** — human-readable и JSON output                                                                                   |
| `llm/gateway.py`                                    | **Работает как транспортный слой**, без расчётной бизнес-логики                                                               |
| Agent Orchestrator / interpretation flow            | Контракты и каркас; полный runtime ещё не реализован                                                                          |
| UI / публичный API                                  | Не входят в текущий реализованный срез                                                                                        |

Для integration-коммита `5406306`, вошедшего в `main` через PR #20, в истории проекта зафиксирован полный локальный прогон:

```text
pytest -q
1423 passed in 39.26s
```

Количество тестов само по себе не считается метрикой качества проекта. Важнее, какие контракты, отказные сценарии, concurrency-инварианты и архитектурные границы они различают.

---

## Application flow

`BuildNatalHandler` — первый реализованный application handler.

```text
BuildNatalCommand
        │
        ▼
BuildNatalHandler
        │
        ├── BirthDataResolver
        │
        ├── chart_kind
        │      ├── natal
        │      └── cosmogram
        │
        └── ChartArtifactPort
                  │
                  ▼
          ChartArtifactResolver
                  │
          ┌───────┼────────┐
          │       │        │
        cache   codec   EngineService
                           │
                           ▼
                         engine/
```

Handler намеренно не владеет:

* calculation cache lifecycle;
* calculation key;
* codec;
* прямым вызовом расчётного движка;
* persistence Session State;
* application-level idempotency и revision lifecycle.

При успехе он возвращает chart artifact и `StateDelta`, но не применяет изменение состояния самостоятельно.

Следующий шаг — `Application Orchestrator`, который должен замкнуть:

```text
request
    → context load
    → operation registration
    → handler selection
    → handler execution
    → result / StateDelta
    → freshness checks
    → state commit
    → response
```

---

## Два уровня оркестрации

В целевой архитектуре разделены два уровня coordination:

```text
                         ┌─ BuildNatalHandler
                         │
API → Application ───────┼─ InterpretSelectionHandler
      Orchestrator       │
                         └─ InterpretMessageHandler
                                      │
                                      ▼
                              Agent Orchestrator
                                / Agent Runtime
                                      │
                              Planner / Tools
                                      │
                                      ▼
                                 EngineService
```

### Application Orchestrator

Управляет пользовательской операцией целиком:

* context load/save;
* выбором handler по типу команды;
* lifecycle операции;
* idempotency;
* revision/freshness;
* применением `StateDelta`;
* формированием результата.

Он не является агентом и не выполняет agent loop.

### Agent Orchestrator / Agent Runtime

Используется внутри операций, которым требуется LLM/agent execution:

* planning;
* выбор разрешённых tools;
* выполнение tools;
* сбор evidence;
* построение контекста;
* вызов LLM.

Ключевая граница:

> **Application Orchestrator управляет пользовательской операцией.
> Agent Orchestrator управляет agent-сценарием.**

Существующий `orchestration/Orchestrator` пока является каркасом будущего interpretation flow и не заменяет Application Orchestrator.

---

## Расчётное ядро

Детерминированное ядро находится в `engine/`.

| Пакет                    | Назначение                                                            |
| ------------------------ | --------------------------------------------------------------------- |
| `engine/ephemeris/`      | позиции тел, дома, Julian day, производные точки, таблицы управителей |
| `engine/charts/`         | `calculate_natal()`, `calculate_transit()`                            |
| `engine/aspects/`        | аспекты и дифференцированные орбисы                                   |
| `engine/configurations/` | конфигурации аспектов                                                 |
| `engine/strength/`       | достоинства, диспозиторы, рецепции, элементы структуры карты          |

Движок не знает о:

* LLM;
* prompts;
* agent runtime;
* HTTP;
* session state;
* пользовательском диалоге.

Пример прямого использования:

```python
from datetime import datetime, timedelta, timezone

from exact_orb.engine.charts.natal import calculate_natal
from exact_orb.engine.charts.transit import calculate_transit

natal = calculate_natal(
    datetime(
        1985,
        9,
        2,
        0,
        45,
        tzinfo=timezone(timedelta(hours=4)),
    ),
    latitude=55.7522,
    longitude=37.6155,
    chart_kind="natal",
)

transits = calculate_transit(
    natal,
    datetime.now(timezone.utc),
)
```

Все результаты представлены типизированными моделями и могут сериализоваться в JSON.

---

## Calculation artifacts

Между application-слоем и низкоуровневым engine существует отдельный calculation layer.

Он разделяет два понятия:

```text
"получить такую карту"
```

и

```text
"снова выполнить физический расчёт"
```

Слой содержит:

```text
ChartSpec
CalculationVersion
calculation key
codec
cache
ChartArtifactResolver
EngineService adapter
```

Значимый параметр, изменяющий числовой результат, должен участвовать либо в `ChartSpec`, либо в `CalculationVersion`.

Artifact resolver отвечает за cache hit/miss, version binding, serialization и необходимость повторного engine calculation.

Для concurrent miss одного ключа используется single-flight, при этом разные вызывающие не получают общий изменяемый объект результата.

---

## Birth data resolution

Пользовательский input отделён от расчётного input.

Пользователь может передавать:

```text
date
time
place
```

а calculation layer получает уже разрешённые значения:

```text
UTC datetime
coordinates
timezone information
time-known / time-unknown semantics
```

Исторический UTC offset вычисляется backend-компонентом, а не LLM.

Если время рождения неизвестно, строится отдельный:

```text
chart_kind="cosmogram"
```

а не натал с фиктивными домами.

---

## Установка

Требуется Python ≥ 3.11.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Установка:

```bash
pip install -e ".[dev]"
```

Основные зависимости:

* `pysweph`;
* `pydantic` v2;
* `litellm`;
* `tzdata`.

Dev-набор:

* `pytest`;
* `pytest-asyncio`;
* `hypothesis`.

---

## Быстрый старт

```bash
exact-orb "2.09.1985 00.45 gmt+4" \
  --place "Москва" \
  --lat 55.7522 \
  --lon 37.6155
```

Эквивалентно:

```bash
python -m exact_orb \
  "2.09.1985 00.45 gmt+4" \
  --place "Москва" \
  --lat 55.7522 \
  --lon 37.6155
```

CLI принимает явный UTC offset. Historical timezone resolution относится к отдельному `birth/` path.

Фрагмент вывода:

```text
НАТАЛЬНАЯ КАРТА
2 сентября 1985, 00:45 (+04:00) · Москва 55.75N 37.62E · Плацидус

ПЛАНЕТЫ
  Солнце      Дева        09°20'27"    4 дом
  Луна        Овен        07°39'54"   11 дом
  ...

ДОМА
  1 (ASC)    Рак         08°06'21"    упр. Луна (11 дом)
  ...
```

Полный эталонный вывод:

```text
tests/golden/natal_1985_human.txt
```

### CLI-флаги

| Флаг               | По умолчанию         | Назначение                                           |
| ------------------ | -------------------- | ---------------------------------------------------- |
| `--lat`, `--lon`   | `55.7522`, `37.6155` | широта и долгота                                     |
| `--place`          | `Москва`             | название места в выводе                              |
| `--house-system`   | `P`                  | система домов; сейчас поддерживается только Плацидус |
| `--rulership`      | `combined`           | `combined`, `modern`, `traditional`                  |
| `--ephe-path`      | —                    | каталог файлов эфемерид                              |
| `--format`         | `human`              | `human` или `json`                                   |
| `--max-aspect-orb` | `7.0`                | максимальный орбис аспекта                           |
| `--planets-only`   | выкл.                | скрыть производные точки                             |
| `--no-aspects`     | выкл.                | не выводить аспекты и конфигурации                   |
| `--no-warnings`    | выкл.                | скрыть предупреждения Swiss Ephemeris                |

Input можно передать и через stdin:

```bash
echo "2.09.1985 00.45 gmt+4" | exact-orb
```

Коды возврата:

* `0` — успех;
* `2` — ошибка разбора input или расчёта.

---

## Эфемериды и воспроизводимость

Файлы Swiss Ephemeris хранятся в:

```text
ephe/
```

В частности:

```text
ephe/sepl_18.se1
ephe/semo_18.se1
ephe/seas_18.se1
```

После `git clone` базовый test suite не требует отдельной загрузки файлов.

Контрольные суммы и происхождение ресурсов описаны в:

[`ephe/README.md`](ephe/README.md)

Путь к эфемеридам разрешается по приоритету:

```text
--ephe-path
    → EXACT_ORB_EPHE_PATH
    → [tool.exact_orb].ephemeris_path
    → default
```

Замена расчётно значимых ресурсов должна изменять `CalculationVersion`, а не незаметно переиспользовать старый artifact.

---

## Конфигурация

Общий принцип:

```text
явный аргумент
    → environment
    → [tool.exact_orb] в pyproject.toml
    → default в коде
```

Текущий project config:

```toml
[tool.exact_orb]
ephemeris_path = "ephe"
selena_method = "true_perigee"
llm_timeout = 60
llm_retries = 2
```

### Переменные окружения

| Переменная                | Ключ `[tool.exact_orb]` | По умолчанию                 | Назначение                         |
| ------------------------- | ----------------------- | ---------------------------- | ---------------------------------- |
| `EXACT_ORB_EPHE_PATH`     | `ephemeris_path`        | `data/ephe`                  | каталог Swiss Ephemeris            |
| `EXACT_ORB_SELENA_METHOD` | `selena_method`         | `mean_perigee`               | метод расчёта Селены               |
| `EXACT_ORB_LOG_LEVEL`     | `log_level`             | `DEBUG`                      | уровень логирования                |
| `EXACT_ORB_LOG_DIR`       | `log_dir`               | `logs/`                      | каталог логов                      |
| `EXACT_ORB_LOG_MAX_BYTES` | `log_max_bytes`         | 10 MiB                       | размер файла до ротации            |
| `EXACT_ORB_LLM_MODEL`     | `llm_model`             | `deepseek/deepseek-v4-flash` | модель LiteLLM                     |
| `EXACT_ORB_LLM_TIMEOUT`   | `llm_timeout`           | `60`                         | timeout запроса                    |
| `EXACT_ORB_LLM_RETRIES`   | `llm_retries`           | `2`                          | число retries после первой попытки |

API keys моделей берутся только из environment провайдера, например:

```text
DEEPSEEK_API_KEY
```

Передача `api_key` непосредственно в gateway не поддерживается.

`.env` находится в `.gitignore`.

---

## Логирование

`init_logging()` создаёт три output channel:

```text
logs/general/<timestamp>Z.log
logs/debug/<timestamp>Z.log
stderr
```

Назначение:

* `general/` — INFO и выше;
* `debug/` — полный debug-поток;
* `stderr` — WARNING и выше.

Временные метки файлов — UTC.

Каждая строка файлового лога содержит явную метку компонента и полный logger,
например:

```text
component=application.handlers.build_natal logger=exact_orb.application.handlers.build_natal
```

`component` — путь компонента без служебного префикса `exact_orb.`. Логи также
содержат session/run correlation information, необходимую для анализа
выполнения сценариев.

На реализованном пути Build Natal каждая публичная граница дополнительно пишет
на `DEBUG` входящее и исходящее сообщение. Envelope явно показывает полный
payload, summary или ошибку:

```text
component_message direction=in operation=ensure_chart run_id=... calculation_key=- status=ok payload_mode=full message_type=EnsureChartRequest message={...}
component_message direction=out operation=ensure_chart run_id=... calculation_key=eo:calc:v1:... status=ok payload_mode=summary message_type=ChartArtifactSummary message={...}
```

Поле `message` — однострочный JSON. Полные входы сохраняются, но внутренние
выходы `NatalChart`, `CalculationResult` и `ChartArtifact` представлены
счётчиками и метаданными без повторной сериализации карты. Полный
`BuildNatalSuccess`, включая `ChartArtifact` и натальную карту, записывается
ровно один раз на выходе handler. `run_id` связывает конкретный запуск, полный
`calculation_key` — артефакт и cache-события. Для просмотра используйте
`logs/debug/*.log` или `pytest --log-cli-level=DEBUG`.

LLM gateway маскирует типовые secrets в error messages, включая значения переменных с `KEY`, `TOKEN`, `SECRET` и `PASSWORD` в имени.

Финальный полный DEBUG-ответ содержит birth-data, координаты, timezone-данные
и результат расчёта. Это намеренный режим локальной диагностики по ADR-0025
и ADR-0026; текущий проект не следует рассматривать как готовый
production-сервис для обработки персональных данных.

---

## Тестирование

Основной запуск:

```bash
pytest
```

Тестовая стратегия включает несколько видов проверок.

### Unit и contract tests

Проверяют отдельные компоненты и типизированные границы.

### Golden/reference tests

Используются эталонные числовые и текстовые результаты:

```text
tests/fixtures/
tests/golden/
```

### Property-based tests

`hypothesis` проверяет инварианты на классах входов.

### Boundary tests

```text
tests/test_module_boundaries.py
```

закрепляет существенную часть разрешённых зависимостей между модулями.

Для agent-assisted разработки это принципиально: важная архитектурная граница по возможности должна быть исполняемой, а не существовать только в документации.

### Integration tests

Integration tests собирают реальные компоненты проверяемого пути.

Для Build Natal проверяется цепочка:

```text
BuildNatalHandler
→ BirthDataResolver
→ ChartArtifactResolver
→ CalculationCache
→ codec
→ EngineService
→ Swiss Ephemeris
```

### Concurrency tests

Для concurrent-сценариев используются управляемые fake components, `asyncio.Event`, barriers и другие детерминированные примитивы.

`sleep` и случайная задержка не считаются доказательством корректного порядка выполнения.

Timeout используется как защита от зависания теста, а не как доказательство синхронизации.

---

## Ручной LLM smoke-test

Сетевой LLM smoke-test намеренно не входит в обычный `pytest`, поскольку выполняет реальный запрос к провайдеру.

Windows:

```bash
set DEEPSEEK_API_KEY=...
python scripts/llm_smoke_test.py
```

Linux / macOS:

```bash
export DEEPSEEK_API_KEY=...
python scripts/llm_smoke_test.py
```

Данные карты для smoke-test берутся из фактического deterministic output, а не из вручную скопированного примера.

---

## Как разрабатывается проект

Рабочий метод — **AI-assisted specification-driven development**.

Архитектурное обсуждение и implementation разделены.

Владелец проекта задаёт исходную проблему, продуктовые и доменные ограничения, определяет спорную семантику и принимает архитектурные решения. LLM используется для расширения анализа: предлагает альтернативы, помогает находить дополнительные corner cases, проверять последствия и формализовывать уже выбранное решение.

После выбора решение фиксируется в долгоживущем источнике истины:

```text
ADR
requirements
component responsibilities
sequence diagrams
boundary tests
```

Только после этого создаётся ограниченная implementation task.

История таких задач хранится в:

```text
prompts/
```

Агент реализует задачу в заданных границах. После реализации отдельный review-проход сопоставляет diff с контрактом и пытается найти сценарий, в котором реализация его нарушает.

Затем выполняется детерминированная приёмка:

```text
targeted regression
    → component tests
    → integration / boundary tests
    → full pytest
    → documentation checks
```

Таким образом разделяются три разные ответственности:

```text
владелец проекта
    → определяет, что и почему должно быть построено

LLM / coding agent
    → помогает анализировать и реализует ограниченную задачу

исполняемые проверки
    → проверяют наблюдаемое поведение и архитектурные инварианты
```

Подробное описание метода:

[`docs/development_approach/spec-driven-development.md`](docs/development_approach/spec-driven-development.md)

Правила, которые получает coding agent непосредственно в репозитории:

[`AGENTS.md`](AGENTS.md)

---

## Источники истины

Для implementation/review действует следующий приоритет:

```text
текущая явная задача
    → действующие ADR и требования
    → актуальные тесты и реализация
    → исторические prompts
    → свободное архитектурное обсуждение
```

Свободный architectural discussion — исследовательский материал и может содержать отвергнутые варианты.

Долгоживущий контракт должен находиться в требованиях, ADR или исполняемой проверке.

---

## Структура репозитория

```text
src/exact_orb/
  application/       application commands, ports, outcomes и handlers
  birth/             birth-data, place и timezone resolution
  calculation/       specs, versioning, cache, codec, artifacts, engine adapter
  engine/            детерминированное расчётное ядро
  session/           state, ContextService и persistence adapters
  research/          research models, projection и corpus
  intent/            interpretation planning contracts
  interpretation/    evidence selection и prompt construction
  orchestration/     agent-orchestration skeleton
  tools/             tool ports и registry
  llm/               LLM transport gateway
  cli.py             standalone deterministic CLI
  config.py          project configuration
  logging_setup.py   logging

docs/
  development_approach/
    spec-driven-development.md
  project_management/
    roadmap.md
  requirements/
    overview.md
    scenarios.md
    component_responsibilities/
    decisions/
  architecture/
  sequence_diagrams/

prompts/              датированные implementation tasks
scripts/              ручные и сетевые smoke-checks
tests/                unit, contract, integration, boundary и golden tests
ephe/                 Swiss Ephemeris files
AGENTS.md              правила работы coding agents
```

---

## Документация

### Архитектура и инварианты

[`docs/requirements/overview.md`](docs/requirements/overview.md)

### Сквозные сценарии

[`docs/requirements/scenarios.md`](docs/requirements/scenarios.md)

### Ответственности компонентов

[`docs/requirements/component_responsibilities/`](docs/requirements/component_responsibilities/)

В частности:

```text
exact-orb_applicationOrchestrator_agentOrchestrator.md
exact-orb_birth_data_resolution.md
exact-orb_build_natal_components.md
exact-orb_calculation_requirements.md
exact-orb_chart_artifacts.md
exact-orb_research_corpus.md
exact-orb_session_requirements.md
```

### Архитектурные решения

[`docs/requirements/decisions/`](docs/requirements/decisions/)

ADR фиксируют:

```text
контекст
→ решение
→ альтернативы
→ последствия
```

Решение действует, пока явно не заменено.

### Sequence diagrams

[`docs/sequence_diagrams/`](docs/sequence_diagrams/)

### История implementation tasks

[`prompts/`](prompts/)

### Метод разработки

[`docs/development_approach/spec-driven-development.md`](docs/development_approach/spec-driven-development.md)

---

## Известные ограничения

На текущем этапе:

* `Application Orchestrator` ещё не реализован, поэтому первый application flow пока не замкнут общей lifecycle/state coordination;
* interpretation handlers и полный Agent Runtime ещё не реализованы;
* `research/` пока использует in-memory corpus; persistence и дальнейшее wiring остаются следующими этапами;
* UI и публичный HTTP API отсутствуют;
* натальный engine поддерживает только систему домов `P` — Плацидус;
* free-form пользовательский dialog не входит в текущий demo-flow;
* соляр и синастрия ещё не реализованы;
* сетевые LLM smoke-tests не входят в основной test suite;
* privacy-hardening логов пока не завершён.

Это R&D-проект: открытый вопрос допустим, если его границы и последствия зафиксированы явно.

---

## Ближайший этап

Следующая архитектурная цель — полностью замкнуть первый пользовательский сценарий:

```text
structured birth input
    → Application Orchestrator
    → BuildNatalHandler
    → BirthDataResolver
    → ChartArtifactResolver
    → deterministic calculation
    → StateDelta
    → freshness / revision validation
    → session commit
    → response
```

После этого interpretation flow сможет строиться поверх уже проверенного application path, а не смешиваться с расчётной логикой.

---

## Лицензия

exact-orb распространяется под **GNU Affero General Public License v3.0**.

Полный текст:

[`LICENSE`](LICENSE)

Обоснование:

[`ADR-0022`](docs/requirements/decisions/0022-project-license-agpl.md)

Проект использует `pysweph` / Swiss Ephemeris, распространяемый по двойной модели лицензирования. В exact-orb используется AGPL-совместимый вариант.

Подробнее о файлах эфемерид и copyright notices:

[`ephe/README.md`](ephe/README.md)

Pull request'ы с кодом на текущем этапе не принимаются; issues и обсуждения приветствуются.

Подробнее:

[`CONTRIBUTING.md`](CONTRIBUTING.md)
