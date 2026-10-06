# Промт 01. Страница и HTTP client в существующем приложении

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-01](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-01).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-01).

## 1. Результат и зачем

Открытие GET / доставляет страницу и её assets из того же приложения; UI HTTP client различает полученный ErrorDTO и отсутствие ответа. Business endpoint, health и public schemas сохраняются.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния), [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-01/02; выбор не копируется в отдельный реестр.
- Зависимости: G3; DEV-UI-01 ещё не выполнен. Проверить доступность Python/Node и отсутствие production UI.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/app.py` | GET / и узкий /ui/ asset prefix; без catch-all и изменений business/lifecycle |
| `src/exact_orb/http_api/ui/index.html, styles.css, main.mjs, transport.mjs` | создать реальные page/client assets этого шага, без future stubs |
| `pyproject.toml` | только package-data для доставки assets, без dependencies |
| `tests/http_api/test_ui_delivery.py, tests/ui/transport.test.mjs` | создать адресные delivery/client tests |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Прочитать app.py/RequestBoundary и текущие routing/health tests; подключить HTML/assets после существующих маршрутов, сохранив safe 404/405.
2. Реализовать leaf fetch client для существующих URL, credentials same-origin и cache no-store; status/body/request ID/Retry-After доступны caller; network rejection имеет отдельный исход.
3. Проверить файл assets через package resources как в checkout, так и в локально установленном пакете без сетевого скачивания; зафиксировать packaging method и окружение. Нет файловой доставки — шаг не завершён.

**Подход:** Реализация → тесты: простая сборка существующего transport; новые delivery/packaging tests обязательны, отдельный RED не требуется.
**Существующее покрытие:** tests/http_api/test_integration.py::test_openapi_exact_public_shapes_and_response_variants; test_lifecycle.py routing/health. Assets/installed distribution ещё не покрыты.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния) / [AS-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-01-первый-вход-и-пустая-сессия) | HTTPS same-origin: открыть / и указанные HTML assets | 200 HTML и загружаемые ES modules/CSS; нет автоматического build; UI delivery не читает session/engine | планируемый test_ui_delivery.py и HTTPS smoke после сборки |
| [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния) / [AS-UI-12](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-12-утерянная-сессия-и-сохранение-черновика) | transport получает 409 ErrorDTO, затем намеренно отклонённую fetch Promise | HTTP code и network failure различаются; cookie client не конструируется; второго POST нет | планируемый transport.test.mjs; leaf network fake, реальный transport |
| [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка) / [AS-UI-19](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-19-доступность-и-узкий-экран) | неизвестный route, business method и /health/* через public proxy | текущие 404/405/health ACL сохраняются; assets не перехватывают API | existing test_lifecycle.py + новый delivery test |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

UI asset delivery не создаёт application run. Для бизнес-запросов сохраняются существующие X-Request-ID; HTTP sequence 001/004 и http_request_started/finished относятся только к реальным business операциям.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/transport.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -q
python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py tests/http_api/test_integration.py -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

HTML/assets доставляются из установленного пакета, transport и targeted/related tests прошли. Runtime behavior остальных work items и browser acceptance этим шагом не объявляются.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-01](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-01) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
