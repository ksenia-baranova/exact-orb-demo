# Промт 08. Безопасная сверка и понятный результат построения

**Дата подготовки:** 2026-10-07. **Owner:** Developer.
**Change / work item:** ui-birth-form-and-facts / [DEV-UI-08](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08).
**Комментарий:** **найдено другой моделью** — замечания №2, 3, 4, 6, 14; [TEST-FIND-UI-006/007/008/010/012](../../../docs/testing/ui-birth-form-and-facts/manual-test-bugs.md#external-model-review).
**Состояние постановки:** PREPARED / NOT EXECUTED.
**Основание подготовки:** поручение владельца подготовить исправления принятых багов; запуск отдельно. Фактическое исполнение записывается в Implementation Plan.

## 1. Результат

После ответа с неизвестным исходом пользователь видит безопасную сверку, а после успешного build — данные именно построенной карты. Устаревшая карта не подтверждает свежий пересчёт; обновление сессии объясняется; восстановленный выбор места остаётся понятным при фокусе. Автоматического повторного POST нет.

## 2. Baseline, источники и зависимость

- Checkout: C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered; ветка dev/ui-birth-form-and-facts-review; baseline подготовки **0d5d70acfc4f1f384b2c06970b35111b411c4fc4**.
- Перед исполнением должен быть выполнен [DEV-UI-07](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-07). Проверить его actual commit/diff, guards и checks, сохранить незакоммиченные изменения. Исходный HEAD исполнения записать в журнал, не подменять baseline подготовки фиктивным будущим SHA.
- Исходные нормы **652bd73405db0a0611e98e81af6f3f668dd429f6**: [HTTP API](../../../docs/requirements/http_api.md) §§4.4, 6.1–6.4, 7–9; [сессия](../../../docs/requirements/component_responsibilities/exact-orb_session_requirements.md), [stored chart](../../../docs/requirements/session/stored-chart-session-behavior.md), [каталог](../../../docs/requirements/component_responsibilities/exact-orb_place_catalog.md). Сверить текущие редакции на baseline исполнения.
- Approved семантика change **ce25dd0**: [requirements](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md) REQ-UI-02/03/08/09/10; [scenarios](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) AS-UI-02/03/04/10/11/12/13/14/16/19/22/23. [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) прочитан @ 0d5d70a, применимы DP-UI-03/05/09; исходный выбор B @ 64934fc.
- [ADR-0034](../../../docs/requirements/decisions/0034-birth-data-and-terms-of-use.md), [ADR-0040](../../../docs/requirements/decisions/0040-session-bootstrap-and-current-chart.md), [ADR-0041](../../../docs/requirements/decisions/0041-stored-chart-in-session.md); [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md) 001/003/004.
- Прочитать AGENTS.md, Developer skill/process, recovery/session/main, BuildReadyDTO/BirthViewDTO/ErrorDTO, server build error mapping и соответствующие existing tests. Baseline и scope сверить до правки; новые публичные исходы не вводить.

## 3. Scope и инварианты

Разрешены src/exact_orb/http_api/ui/recovery.mjs, session.mjs, main.mjs; минимальные связанные presentation-изменения places.mjs/facts.mjs; tests/ui/{recovery,session,places,facts,transport}.test.mjs и существующие fixtures. Дополнить только карточку DEV-UI-08, связанные пять findings и фактическое handoff.

Сохранить DTO/HTTP status/error codes/cookies, debounce/HH:MM/null, ручной checkbox ADR-0034, server CAS/admission/lifecycle/watchdog, calculation_key/CalculationVersion/числа, поведение двух вкладок. Не добавлять endpoints, polling, повторные POST, слепой restart, client timeout/новые зависимости или серверные стадии в публичный DTO. Метаданные региона/страны отсутствуют в восстановленном BirthViewDTO и не выдумываются.
Несвязанный diff/index сохранить. Commit/push/PR, запуск/перезапуск стенда и внешние действия — только при отдельном поручении.

## 4. Задача

1. **TEST-FIND-UI-006:** POST с 5xx без валидного/распознаваемого ErrorDTO либо с **500 INTERNAL_FAILURE** считать неподтверждённым исходом. До безопасной сверки новый build недоступен. Для этих случаев выполнить bootstrap → current; применить реальный Retry-After, если он есть, не выдумывать задержку. Failed check сохраняет draft/последнюю карту и разрешает только безопасную проверку. После successful old/empty — предупреждение о позднем завершении и отдельный ручной retry при действующем checkbox. Matching current показывается как актуальное состояние, не как доказательство завершения конкретной попытки.
2. Сохранить известные policies: STATE_COMMIT_FAILED после Retry-After читает **только current**; подтверждённый ErrorDTO BUILD_TIMEOUT требует принятого restart/readiness и bootstrap/current; capacity/429/pre-admission failures остаются своими отказами. Текстовый **504 прокси не равен BUILD_TIMEOUT**. UI не получает внутренний context_status: для публичного INTERNAL_FAILURE используется консервативная сверка всех таких 500, без угадывания стадии по cookie/Retry-After.
3. **TEST-FIND-UI-007:** совпавшее birth при **chart_stale:true** не обозначать как подтверждённый свежий результат. Сохранить факты, явную пометку stale, безопасную проверку и явный пересчёт. **chart_stale:false + тот же intent + прежний chart_identity допускает matched**: identity — ключ расчёта, а не идентификатор попытки. Не использовать bootstrap state_version как доказательство успешного POST.
4. **TEST-FIND-UI-008:** после POST 409 SESSION_REQUIRED/EXPIRED/NOT_FOUND и успешного bootstrap/current показать, что сессия обновлена, запрос build был отклонён и требуется отдельное нажатие. Действительный current и draft сохраняются. При failed bootstrap/current показать отказ, не объявлять восстановление успешным. Не повторять исходный POST автоматически.
5. **TEST-FIND-UI-010:** для committed POST показать дату, время/явную неизвестность и название места из **неизменяемого снимка отправленного intent/названия**. Сводка описывает показанную chart_identity, а не текущий редактируемый draft. Не собирать фиктивный полный BirthViewDTO: timezone/offset/warnings из intent неизвестны; дополнительный GET только ради сводки не требуется. После current/already_applied/superseded сводка читает actual серверный birth, не intent отклонённой попытки.
6. **TEST-FIND-UI-012:** подпись подтверждённого восстановленного места остаётся после focus/blur без изменения текста. Можно согласовать presentation search/form на существующем слое; дополнительный lookup не нужен. Редактирование снимает старый place_id по прежнему правилу; новый выбор фиксирует новый ID. Не отображать undefined в подписи.

## 5. Подход и матрица

**Тесты → реализация.** Existing recovery tests уже покрывают network loss, old/empty manual retry, commit delay, restart timeout и two-tab; session tests — session loss, unknown time, late response/dispose и malformed response. Они не покрывают принимаемые 5xx/stale/feedback случаи; 502 test сейчас разрешает второй POST. Расширить чувствительные tests, не удаляя проверку неполного 200 из DEV-UI-07.
До реализации получить RED по наблюдаемым расхождениям; затем минимальная правка и GREEN. Существующие guards, fixtures/session.mjs fakeClock/deferred, fixtures/dom.mjs и HTTP golden переиспользовать. Реальные coordinator/transport/form/mount, подмена только leaf network/clock/DOM; no sleep/random delays.

| REQ / AS и finding | Данные / действие | Expected result | Планируемая проверка |
|---|---|---|---|
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки), AS-UI-14/23; 006 | Текстовые 502/504, 503 без ErrorDTO, unknown 5xx, 500 INTERNAL_FAILURE | До safe response build заблокирован; POST → bootstrap/current, никогда auto POST; request IDs отдельные | recovery/session: deferred safe response, параметризованные outcomes |
| REQ-UI-09, AS-UI-14/23; 006 | Safe read failed, затем успешный old/empty или matching current | Failed: только recheck; successful old/empty: late-commit warning + manual/gated retry; matching: actual current | Positive successful read/manual click и отрицательный unacknowledged gate |
| REQ-UI-09, AS-UI-13/14; 006 | Known capacity/429, STATE_COMMIT_FAILED, BUILD_TIMEOUT | Прежние code-specific queries/Retry-After/restart; raw proxy 504 не включает выдуманный restart | Существующие tests с fakeClock как позитивные контроли |
| [REQ-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-08-восстановление-stale-и-unavailable), AS-UI-11/23; 007 | Lost response; same-birth stale current с прежним identity; отдельно fresh same identity | Stale не подтверждает свежую попытку, видны старые факты/пересчёт/recheck; fresh допускается как matched | recovery + mounted assertions; также different birth и unavailable |
| REQ-UI-03/09/10, AS-UI-12/19; 008 | POST session 409, восстановление empty/ready; отдельно failed safe read | Объяснение необходимости нового действия, draft сохранён, автоматического POST нет; failure виден | Дополнить существующие session-loss cases mounted message assertions |
| REQ-UI-03/08, AS-UI-03/04/10/22; 010 | Committed known/unknown time; draft меняется, пока POST deferred | Сводка снимка построенного intent, null не превращается в полдень; отредактированная форма сохранена | Mount/session; positive valid successful build |
| REQ-UI-08/09, AS-UI-10/16; 010 | already_applied/superseded/current другой вкладки | Actual серверные birth и identity, не прежний submitted intent; чтение без build | Существующие golden/two-coordinator cases |
| REQ-UI-02/08/10, AS-UI-02/10/19; 012 | Restore birth → focus → blur; затем edit → choose | Подпись/ID сохраняются до редактирования; edit снимает ID; явный выбор нового места используется в POST | Mounted DOM-port checks + positive new selection |

Пути/IDs requirements/scenarios из раздела 2 и TEST-FIND IDs сохранить в комментариях новых tests. Planned test names определить при реализации и записать точные node IDs в handoff. Проверять публичные сообщения, calls/order, draft и actual facts; приватную классификацию не делать единственным oracle.

## 6. Наблюдаемость

Сопоставить calls с HTTP 003 (POST), 001 (bootstrap), 004 (current) и действующими server событиями load → session_view / handler → save. Recovery не создаёт engine/Orchestrator через GET; наличие полного current — позитивный контроль фактического чтения. Server X-Request-ID исходного POST, bootstrap и current различаются, отсутствие ID у прокси сохраняется как отсутствие. Retained первый commit не выдается за ответ второго POST. Logging contract/полные payload не расширять.
Поскольку меняется UI reaction на имеющиеся ответы, серверные sequences и архитектура сохраняются. Если выяснится необходимость менять серверный поток, вернуть вопрос владельцу и не расширять scope молча.

## 7. Проверки и handoff

Из указанного checkout с проверенными Node/Python; не устанавливать новые зависимости автоматически.

~~~powershell
node --test --test-isolation=none tests/ui/recovery.test.mjs tests/ui/session.test.mjs tests/ui/places.test.mjs tests/ui/facts.test.mjs
node --test --test-isolation=none tests/ui/*.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_lifecycle.py tests/http_api/test_build_admission.py tests/http_api/test_session.py tests/test_module_boundaries.py -q
python -B -m pytest -p no:cacheprovider tests/http_api -q
python -B -m pytest -p no:cacheprovider -q
git diff --check
~~~

Target → related → full. Проверка legacy full gate обязательна; известное baseline падение DEBT-CALC-001 честно записать без xfail/skip/изменения расчёта. Target/related новых исправлений должны проходить; полный FAILED не становится G4/G5 PASS.
Ручные сценарии после разрешённого обновления стенда: restore focus/blur, сводка natal/cosmogram, session-loss notification и recovery на контролируемых proxy/stale исходах. Не ломать рабочий сервер ради случайной ошибки и не использовать sleep как доказательство commit order. Если browser setup/разрешение отсутствует — явно NOT RUN и reproducible handoff.

Критерий Developer completion: пять дефектов исправлены и закреплены чувствительными tests; safe reads/gate/diagnostics сохранены; команды реально выполнены; registry получает FIXED PENDING RETEST с фактическим evidence. Tester закрывает после независимой проверки; общий acceptance/DEBT-CALC-001 не закрываются этим заданием.
Неоднозначность публичного recovery contract → Analyst, scope/budget → Manager, architecture → Technical Reviewer; независимые feedback-пункты продолжать. В journal DEV-UI-08 записать baseline/diff, причины RED/GREEN, точные команды/exit codes, test IDs, непроверенное и остаточные gates. Исторические промты не переписывать.
