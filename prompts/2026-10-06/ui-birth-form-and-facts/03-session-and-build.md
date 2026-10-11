# Промт 03. Вход, явный build и состояния карты

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-03](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-03).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-03).

## 1. Результат и зачем

Bootstrap/current определяют состояние, а единственное явное действие пользователя отправляет ровно один build; ошибки сохраняют draft и связаны с нужным полем.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния), [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация), [REQ-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-08-восстановление-stale-и-unavailable), [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-02/04/08; выбор не копируется в отдельный реестр.
- Зависимости: DEV-UI-01/02 завершены; transport и валидный form snapshot доступны; G3 действует.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/ui/session.mjs` | создать реальный session/build coordinator |
| `src/exact_orb/http_api/ui/transport.mjs, main.mjs` | связать existing API outcomes с экраном |
| `tests/ui/session.test.mjs` | создать controlled client transitions; backend tests переиспользовать |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Реализовать bootstrap {} → current при входе/reload, без auto build. Ready bootstrap/version не означают наличия карты.
2. Перед submit сохранить immutable intent трёх полей; busy guard предотвращает второй click в этой вкладке. Не отправлять client expected_version.
3. Отделить chart_ready/current stale/unavailable/empty; сохранить доступный draft при отказах. Ошибки IssueDTO field показать рядом с полем, unknown field/user_message — в общей области.
4. Для already_applied и superseded прочитать current; восстановление session 409 — bootstrap/current. Не принимать результат повторного POST без chart за новую карту. Остальное recovery завершает следующий work item.

**Подход:** Тесты → реализация client state; запуск existing server coverage без дублирования. Никакой правки server contract ради client tests.
**Существующее покрытие:** test_session.py::test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation, test_current_projects_stale_unavailable_or_empty_without_mutation; request-boundary/admission tests. Client coordinator новый.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния) / [AS-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-01-первый-вход-и-пустая-сессия) | нет cookie; bootstrap ready/version=0, current empty | чистая форма без chart/demo; нет POST natal; оба safe requests реально выполнены | session.test.mjs + real HTTP session positive control |
| [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация) / [AS-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-03-известное-время-и-успешный-натал) | 1985-09-02, 14:30, выбранный ID и manual checkbox; double click | один POST с ровно тремя полями; chart_ready содержит принятый chart_identity | deferred network response и calls assertions |
| [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация) / [AS-UI-06](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-06-ошибки-даты-локального-времени-и-места) | получить 422 birth.time/AMBIGUOUS, затем исправить валидным known временем | field error не исправляется browser timezone, draft сохранён; позитивный build проходит | leaf response fixtures и real coordinator |
| [REQ-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-08-восстановление-stale-и-unavailable) / [AS-UI-11](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-11-устаревшая-и-недоступная-сохранённая-карта) | current chart_stale=true; отдельный chart_unavailable с birth | stale facts сохраняются; unavailable без чисел с явным rebuild; read не строит карту | session.test.mjs; real server test_session.py |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

Сверить HTTP 001/003/004: ContextService/admission/Orchestrator/session_view send/receive или terminal/error с request/run ID. До local gate серверного build trace нет, после positive control есть.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/session.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_session.py tests/http_api/test_request_boundary.py tests/http_api/test_build_admission.py -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

Bootstrap/current/build/error state checks прошли; поля/code/schema server сохранены. UI reader/actions и unknown outcome переходят в DEV-UI-04/05.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-03](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-03) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
