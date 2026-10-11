# Промт 05. Неопределённый результат и два client intent

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-05](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-05).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-05).

## 1. Результат и зачем

Применить принятый recovery контракт, сохраняя draft и отсутствие автоматического POST; чужой/поздний результат не выдаётся за ответ текущего intent.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация), [REQ-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-08-восстановление-stale-и-unavailable), [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-04/09; выбор не копируется в отдельный реестр.
- Зависимости: DEV-UI-02/03/04 завершены; DP-UI-09 ACCEPTED в согласованном baseline; G3 действует.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/ui/recovery.mjs` | создать outcome-specific recovery |
| `src/exact_orb/http_api/ui/session.mjs, transport.mjs, main.mjs` | связать intent/current/foreground/кнопку повторения |
| `tests/ui/recovery.test.mjs` | создать deterministic response/race tests; existing backend seams переиспользовать |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Разделить полученные 503 STATE_COMMIT_FAILED / 504 BUILD_TIMEOUT и fetch rejection без HTTP response. Retry-After сохранять по реально полученному ответу; отсутствующее значение не выдумывать.
2. При сетевом отказе сохранить intent/draft, восстановить bootstrap/current; successful old/empty разрешает только отдельный ручной retry с gate и предупреждением DP-UI-09. При failed check build недоступен, повторять можно только safe check.
3. При received BUILD_TIMEOUT сохранить отдельную HTTP policy restart/readiness; не ходить browser к внутреннему /health/* и не вводить новый polling/restart mechanism. Bootstrap/current после восстановленной доступности выполняет safe сверку; исходный POST не повторяется автоматически.
4. Две вкладки: foreground current является серверным источником истины, draft не auto submit. Suppressed stale read/search response и snapshot intent не должны подменять ответ второго POST; server CAS/lifecycle/permit не меняются.

**Подход:** Тесты → реализация. Реальные transport/coordinator modules, leaf network/fake timer/Event/barrier; sleep не является доказательством порядка.
**Существующее покрытие:** test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation и test_disconnect_during_protected_commit_is_visible_after_restart; test_build_admission.py lost_commit_ack/timeout/concurrent intent. Client recovery ранее отсутствует.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-23](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-23-потерян-ответ-build) | ответ POST потерян; первый commit уже состоялся, current содержит исходное намерение | показана подтверждённая карта; нет auto POST; request IDs recovery отдельные | recovery.test.mjs + controlled real server disconnect test |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-23](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-23-потерян-ответ-build) | первый commit не состоялся либо ещё удерживается; успешный current old/empty; затем явный retry | предупреждение о позднем commit; без click/gate POST нет, после них ровно один новый POST; late first не становится ответом second | Event/barrier и fake transport, реальный coordinator |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-23](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-23-потерян-ответ-build) | bootstrap/current сверка даёт ошибку; отдельно manual checkbox снят | build недоступен; draft сохранён; safe check можно повторить; позитивный successful check разрешает ручной build | calls/state assertions без mock предмета проверки |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-14](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-14-неопределённый-исход-commit-и-timeout) | получен 503 STATE_COMMIT_FAILED либо 504 BUILD_TIMEOUT с Retry-After | применена code-specific safe сверка, нет авто POST и нет выдуманного readiness health route | fake clock и реальные outcome fixtures |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-16](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-16-две-вкладки-и-superseded) | B построила карту B; A вернулась; concurrent superseded/already_applied | A показывает actual current B, хранит доступный draft; current GET вместо выдуманного artifact | два coordinator экземпляра + shared leaf response seam |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

Первый/второй POST и recovery current имеют разные request/run IDs; protected commit виден в существующем server trace. Cancellation/terminal допускают send + error вместо ложного receive. Sequence HTTP 003/004 и session/006.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/recovery.test.mjs tests/ui/session.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation tests/http_api/test_lifecycle.py::test_disconnect_during_protected_commit_is_visible_after_restart tests/http_api/test_build_admission.py -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

Все ветви outcome/check/manual repeat/two-tabs имеют actual assertions и позитивные контроли. Риск позднего первого commit остаётся accepted, гарантия exactly-once или новый API не объявляются.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-05](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-05) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
