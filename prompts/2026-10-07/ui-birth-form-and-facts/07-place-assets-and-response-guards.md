# Промт 07. Допустимые места, актуальные ресурсы и проверка ответов UI

**Дата подготовки:** 2026-10-07. **Owner:** Developer.
**Change / work item:** ui-birth-form-and-facts / [DEV-UI-07](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-07).
**Комментарий:** **найдено другой моделью** — замечания №1, 5, 13; [TEST-FIND-UI-005/009/011](../../../docs/testing/ui-birth-form-and-facts/manual-test-bugs.md#external-model-review).
**Состояние постановки:** PREPARED / NOT EXECUTED.
**Основание подготовки:** владелец поручил зарегистрировать принятые баги и написать промты. Исполнение этого файла начинается по отдельному поручению; текущий статус хранится в Implementation Plan.

## 1. Результат

Пользователь может выбрать корректное место без названия региона; обновление UI требует проверки свежести ресурсов; повреждённый ответ сервера не ломает страницу и не выдаётся за подтверждённый результат. Это исправление трёх конкретных дефектов без изменения вычислений или публичного API.

## 2. Baseline и источники

- Checkout: C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered; ветка dev/ui-birth-form-and-facts-review; исходный HEAD **0d5d70acfc4f1f384b2c06970b35111b411c4fc4**.
- Исходный нормативный baseline **652bd73405db0a0611e98e81af6f3f668dd429f6**: [HTTP API](../../../docs/requirements/http_api.md) §§4.4, 6, 7, 9; [PlaceCatalog](../../../docs/requirements/component_responsibilities/exact-orb_place_catalog.md); [stored chart](../../../docs/requirements/session/stored-chart-session-behavior.md). Сверить также текущие редакции этих источников на исходном HEAD.
- Approved семантика change **ce25dd0**: [requirements](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md) REQ-UI-01/02/03/08/09/10; [scenarios](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) AS-UI-01/02/03/04/10/15/17/18/19/23. Административные статусы прочитаны на 0d5d70a.
- [Единый реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) на 0d5d70a, DP-UI-01/03/09; [ADR-0034](../../../docs/requirements/decisions/0034-birth-data-and-terms-of-use.md), [ADR-0039](../../../docs/requirements/decisions/0039-https-in-all-environments.md), [ADR-0040](../../../docs/requirements/decisions/0040-session-bootstrap-and-current-chart.md), [ADR-0041](../../../docs/requirements/decisions/0041-stored-chart-in-session.md).
- [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md) 001–004; действующие DTO/projector и UI-код; tests/ui fixtures/session.mjs и fixtures/dom.mjs, HTTP golden.
- Перед правкой прочитать AGENTS.md, skill Developer, process и указанные sources; проверить git status/HEAD, что существующий transport/form/coordinator доступен. При изменившемся baseline сверить поведение заново, сохранить пользовательский diff; автоматически ветки не переключать.

## 3. Разрешённая область

| Область | Назначение |
|---|---|
| src/exact_orb/http_api/ui/places.mjs, main.mjs | Разрешить nullable регион в подсказке и проверить выбор. |
| src/exact_orb/http_api/ui/session.mjs, facts.mjs, main.mjs | Проверка response до accept/render и видимое состояние ошибки. При необходимости разрешён один новый небольшой чистый UI-модуль проверки DTO; включить его в проверки wheel. |
| src/exact_orb/http_api/app.py | Только cache headers доставки UI-ресурсов. |
| tests/ui/{places,session,recovery,transport,facts}.test.mjs, tests/ui/fixtures | Адресные deterministic regression cases; переиспользовать fixtures/golden. |
| tests/http_api/test_ui_delivery.py | Headers 200/304 и реальная доставка установленного wheel вне checkout. |
| Implementation Plan и bug registry | Только карточка DEV-UI-07, три findings и фактическое evidence; исторические промты не редактировать. |

Инварианты: same-origin и существующие credentials/cache options API; debounce/порог поиска; обязательный подтверждённый place_id; HH:MM/null; ручной checkbox; 16 ID точек; расчётные числа; DTO, error codes, admission, commit и server watchdog. Не добавлять зависимости, API, алиасы, новые сервисы, клиентский таймаут, CSP/nosniff, фильтрацию каталога ради сокрытия null или отбрасывание повреждённых элементов по новой политике.
Commit/push/PR и перезапуск стенда требуют отдельного поручения; несвязанные файлы/index сохранить.

## 4. Исправления

1. **TEST-FIND-UI-005:** places принимает admin1_name как string либо null, остальные обязательные поля проверяются по действующему DTO. null отображается как «—». Live «Гонк» вернул 200 с ID 1819729 и null-регионом, пользователь увидел ошибку поиска; это известное воспроизведение, не отсутствие места. Смешанный корректный список сохраняется целиком. Не менять прежний отказ при действительно повреждённом ответе.
2. **TEST-FIND-UI-009:** задать **Cache-Control: no-cache** для модулей/CSS с постоянными URL, включая успешную conditional выдачу 304. Сохранить ETag/Last-Modified, MIME, no-store HTML/API и пакетную доставку. Не вводить versioned build pipeline. Подтверждены отсутствующие заголовки; смешение версий в браузере при ревью ещё не воспроизводилось.
3. **TEST-FIND-UI-011:** проверить DTO на границе принятия ответа, прежде чем renderer читает коллекции/поля. Известный example: 200 chart_ready с корректными kind/identity/state_version, но points:null, проходит минимальную проверку и даёт TypeError без form-error. Покрыть повреждённые POST/current/bootstrap на полях, которые UI реально использует, и совместимость nullable natal/cosmogram по контракту. Проверка не пересчитывает факты и не исправляет данные догадками.
4. Некорректный POST 200 направляется в существующую **unconfirmed_response → безопасный bootstrap/current** policy, без auto POST. Повреждённый current не заменяет последнюю подтверждённую карту и блокирует build до успешной безопасной проверки. Показать понятную ошибку, сохранить черновик и request ID; не создавать выдуманный ErrorDTO.
5. Promise handlers mount/open/foreground/submit должны давать видимый отказ при неожиданном UI-сбое и выход из busy. Сначала устранить корневую причину повреждённого response; пустой catch, сокрытие исключения как успеха или слепой retry запрещены. Не превращать dispose/поздний ответ в новую ошибку пользователя.

## 5. Подход и матрица

**Тесты → реализация в одном промте.** До правки добавить чувствительные tests отсутствующих условий, получить RED по nullable rejection/нехватке headers/TypeError, затем минимально исправить и получить GREEN. Import/setup failure не считается RED.
Existing: places tests на string-регион/выбор; session test «text proxy error and incomplete success cannot masquerade as a committed chart»; transport tests HTTP/text/body-read; facts tests natal/cosmogram; delivery tests root no-store и installed wheel. Не дублировать их; дополнить непокрытые ветки.

| REQ / AS и finding | Данные / действие | Expected result | Планируемая проверка |
|---|---|---|---|
| [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места), AS-UI-02/18/19; 005 | Корректная выдача с null-регионом, затем mixed null/string; выбрать Гонконг | Список доступен, регион «—», выбор ID 1819729; build только после click/gate | places.test.mjs + mounted session case; positive string-регион |
| REQ-UI-02/10, AS-UI-18; 005 | Повреждённый обязательный place_id/тип поля | Прежний безопасный отказ; null не приравнивается к повреждению | Дополнить существующие malformed search cases |
| [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния), AS-UI-01/10; 009 | GET CSS/module 200 и If-None-Match 304 | no-cache на ресурсах, валидаторы сохранены; HTML/API no-store | test_ui_delivery.py, установленный wheel, conditional request |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки), AS-UI-15/17/23; 011 | POST points:null, некорректные коллекции/необходимые типы; safe read failed/successful | Нет принятия повреждённой карты, unhandled rejection или auto POST; сообщение и draft; только safe recovery | session/recovery mounted cases, real coordinator/transport |
| REQ-UI-08/09/10, AS-UI-10/15/17; 011 | Повреждённый current/bootstrap после подтверждённого view | Видимый отказ, прежний view/draft сохранены; новый POST заблокирован до valid safe read | Deferred fetch и DOM port, контролируемый положительный valid read |
| REQ-UI-03/08, AS-UI-03/04/10 | Валидные natal/cosmogram и already-disposed response | Прежние факты/числа; dispose не публикует поздний результат; successful build достижим | Existing golden/facts/session/transport tests |

Во вновь добавленных tests указать REQ/AS и TEST-FIND IDs. Использовать реальные modules и только leaf fake network/clock/DOM, управляемые deferred/events; sleep и случайные задержки не доказывают поведение.

## 6. Наблюдаемость

Сохранить status, body, X-Request-ID и Retry-After. Сверка имеет отдельные request IDs, calls подтверждают порядок POST → bootstrap → current. GET places соответствует HTTP sequence 002; safe read — 001/004. Не добавлять расчёт/логи полного payload в browser и не менять действующий server logging. Кэш/валидация меняют UI boundary, серверный межкомпонентный поток сохраняется.

## 7. Проверки и завершение

Из указанного checkout; проверить доступные Node/Python и зависимости, не устанавливать новые автоматически. .venv в worktree на baseline отсутствует.

~~~powershell
node --test --test-isolation=none tests/ui/places.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/facts.test.mjs tests/ui/transport.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_ui_delivery.py -q
node --test --test-isolation=none tests/ui/*.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q
python -B -m pytest -p no:cacheprovider -q
git diff --check
~~~

Target → related → full, после target GREEN. Полный pytest обязателен для handoff исполняемой правки. На baseline последний полный прогон 2959 passed / 1 failed: DEBT-CALC-001, test_property_configuration_count_does_not_grow_when_threshold_decreases. Повторный failure честно записать; не менять/отключать этот тест и не объявлять full/G4/G5 PASS.

Ручные проверки после разрешённого обновления стенда: выбрать «Гонк»; reload с обычным browser cache и проверкой headers/revalidation; valid natal/cosmogram и controlled malformed recovery. Если необходимые изменения/перезапуск вне поручения, записать browser checks NOT RUN и передать готовый diff.
Готово: root causes исправлены, deterministic regressions чувствительны, target/related прошли, full фактически выполнен и описан, три findings FIXED PENDING RETEST с evidence. Независимая Tester acceptance этим не подменяется.
Противоречие контракта → Analyst; scope/estimate → Manager; новая архитектурная граница → Technical Reviewer. Продолжать независимые пункты.
В журнал DEV-UI-07 внести actual baseline/diff, RED/GREEN cases, команды/exit codes, изменённые файлы, непроверенное и handoff DEV-UI-08; настоящий промт остаётся постановкой.
