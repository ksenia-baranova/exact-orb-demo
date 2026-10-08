# Developer review: ui-birth-form-and-facts

**Роль и дата:** Developer, 2026-10-06.
**Ветка:** `dev/ui-birth-form-and-facts-review`.
**Статус первого review @ `b36b63d`:** DOCUMENT REVIEW COMPLETE / OPEN FINDINGS; исходное заключение и findings ниже сохраняются как история.
**Текущий статус Developer (2026-10-08):** **READY_FOR_TEST** — по поручению владельца; реализация DEV-UI-01…08 и актуальные Developer checks передаются в [Implementation Plan / Developer Handoff](ui_birth_form_and_facts_implementation_plan.md#developer-ready-for-test) на implementation commit `f7fb34b` с одним согласованным skip DEBT-CALC-001 в коммите передачи, содержащем эту редакцию документов. Долг OPEN, независимая browser acceptance ожидается. Подготовительная сверка REVALIDATED / FEASIBLE @ `082c6b9`, review baseline `033217d`, и исходные findings ниже сохранены как история. Общий delivery status/G4/G5 ведёт [Manager](../change_plans/ui-birth-form-and-facts/artifacts.md#change-brief).
**Технический вывод:** три группы реализуемы на существующем API; контракт действий/recovery повторно сверён Developer и независимым Tester `0f6aa82`, blocking semantic gaps отсутствуют. Ниже сохранены историческое первое review и последующая авторская валидация.

## Проверенный baseline

| Объект | Проверенная версия |
|---|---|
| Общий исходный HEAD `change/ui-birth-form-and-facts` | `9ae1abc71e6876d5440f20541996f489a387e1cb`; Developer-ветка создана от этого commit. |
| [Manager artifacts и единый реестр](../change_plans/ui-birth-form-and-facts/artifacts.md#decision-register), [roadmap M1-7/M1-9](../roadmap.md) | Manager commit `ad8892fd7ed8bd3f0998202c32bbcc05f31020f9`, интегрирован через [PR #44](https://github.com/ksenia-baranova/exact-orb-demo/pull/44), merge `ea0678da1546bff15493239372e27b32726e7086`. |
| [requirements.md](../../requirements/changes/ui-birth-form-and-facts/requirements.md), [scenarios.md](../../requirements/changes/ui-birth-form-and-facts/scenarios.md), [analysis.md](../../requirements/changes/ui-birth-form-and-facts/analysis.md) | Analyst commit `dbee8880ae00f65aac7660936e69b906900ae216`, интегрирован через [PR #43](https://github.com/ksenia-baranova/exact-orb-demo/pull/43), merge `9ae1abc71e6876d5440f20541996f489a387e1cb`. |
| Нормативный вход Analyst | `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../requirements/http_api.md), component requirements и ADR из Analyst-пакета. Этот исторический вход не переписывается новым HEAD. |
| Код и существующие тесты | `9ae1abc`; между `652bd734` и этим HEAD нет изменений `src/`, `tests/` и `pyproject.toml`. |

Merge обоих PR подтверждён Git ancestry и read-only GitHub metadata 2026-10-06. Это evidence интеграции документов, а не завершения G2/G3 или приёмки UI. Исходная версия реестра — `artifacts.md` @ `ad8892f`; в этом Developer diff дополнены только собственные рекомендации в DP-UI-02/04/05/08. Выбор владельца, статусы решений, Manager brief/roadmap и Analyst-документы не исправляются от имени других ролей. После интеграции Developer-коммита Manager фиксирует новый baseline реестра.

## Вывод для Manager: историческое первое review @ `b36b63d`

Причина расхождений пакета — независимая интеграция Manager и Analyst документов без последующей сверки текущих статусов и переноса принятых решений в наблюдаемые требования/сценарии. Ниже разделены возвраты к владельцам документов и вопрос, для которого ещё нужен контракт. Существенные решения остаются в едином реестре; этот документ содержит Developer findings и условия их закрытия.

FIND-DEV-UI-001 блокирует реализацию/приёмку экрана готовности и навигации; FIND-DEV-UI-002 — окончательный контракт клиентского восстановления после потери ответа. FIND-DEV-UI-003 блокирует выдачу согласованного baseline для финального плана. Независимое чтение кода, оценка формы, поиска и форматирования DTO могут продолжаться. Общий допуск к разработке по-прежнему определяется Manager и gates G2/G3.

Оценка разработки и исполняемые промты не подготовлены этим review. Target из DP-UI-07 не становится estimate Developer; этот коммит не завершает полную консультацию G2.

## Комментарии к существующим требованиям

| Требование / сценарий | Комментарий Developer | Действие и ссылка |
|---|---|---|
| REQ-UI-01, 08; AS-UI-01, 10, 11 | Разделение bootstrap/current, `empty`, stale и unavailable соответствует существующим DTO/routes. `state_version` не заменяет `chart_identity`; read path не должен вызывать build. Серверное покрытие существует, browser restore ещё не проверен. | Сохранить контракт; при реализации связать UI checks с `tests/http_api/test_session.py`. |
| REQ-UI-02; AS-UI-02, 04–06, 18 | Порог UI, сброс выбранного ID и подавление позднего ответа реализуются без изменения catalog/API. Пустое поле UI не отправляет GET. Прямой `query=` даёт `422 INVALID_PLACE_QUERY/EMPTY`; корректный query без совпадений — `200 items:[]`. AS-UI-18 здесь не является дефектом. | Сохранить контракт и DP-UI-03/06. Browser timer/order проверки дополнить при реализации; серверную нормализацию не переносить в браузер. |
| REQ-UI-03; AS-UI-03, 07, 19 | В требованиях/сценариях нет полного наблюдаемого поведения выбранного DP-UI-05. Одного запрета дополнительных полей POST недостаточно для состава экрана и действий. | Возврат Analyst: FIND-DEV-UI-001; выбор остаётся в DP-UI-05. |
| REQ-UI-03; AS-UI-20/21; FIND-UI-002 | Представление ручного gate реализуемо локально в форме. Промежуточное предложение `analysis.md` о сводке условий не отмечено как снятое после DP-UI-08. | Возврат Analyst: FIND-DEV-UI-003. Ссылаться на DP-UI-04/08 и DEBT-UI-001; не добавлять страницу/сводку в обязательный scope закрытого M1-7. |
| REQ-UI-04–06; AS-UI-07–09, 15 | Нужные публичные группы уже проецируются через общий `project_chart`. `sign/degree/minute`, null semantics и POST/current parity не требуют DTO-дельты. UI formatting и browser evidence ещё отсутствуют. | Техническая рекомендация добавлена в DP-UI-02. Не подставлять demo-числа и не пересчитывать позиции из longitude. |
| REQ-UI-07, 10; AS-UI-19 | Будущая композиция макета не требует работающих пустых секций. Keyboard и 360 px проверки относятся к новому browser UI; существующие backend tests их не доказывают. | Сохранить границы M1-7/M1-8/M1-8.1/M2; готовить браузерные проверки после согласованного контракта. |
| REQ-UI-09; AS-UI-12–14, 16 | Recovery задан по полученному HTTP outcome. Потеря ответа POST без ErrorDTO не описана отдельным UI путём; неизвестен наблюдаемый критерий допуска нового явного build. | Открытый вопрос Analyst/Manager: FIND-DEV-UI-002. Серверный lifecycle из HTTP §§9.2–9.3 сохраняется. |

## FIND-DEV-UI-001. Нет требований и сценариев по принятому DP-UI-05

**Type:** requirement / acceptance gap. **Priority:** P1. **Status:** OPEN.
**Owner:** Functional Analyst; UI/UX уточняет макет, Tester сверяет будущие сценарии.
**Blocks:** реализацию и приёмку экрана готовности/перехода к подробностям; не блокирует независимую техническую оценку формы и DTO.
**Источники:** `requirements.md` REQ-UI-03, абзац после таблицы build; `analysis.md` рекомендация DP-UI-05; AS-UI-03/07/19 @ `dbee888`; DP-UI-05 @ `ad8892f`.

**Проявление:** исполнитель, читающий только FULL requirements и AS-UI-01…21, может сразу вывести таблицы и не создать выбранные действия экрана готовности. Tester не получает сценария видимости/неактивности чата и позитивного контроля подробностей. Принятый выбор уже существует; повторно спрашивать владельца о составе кнопок не требуется.

**Комментарий и вопрос Developer:** в каких REQ/AS будет закреплён весь observable flow DP-UI-05, включая состав формы и переход к подробностям после committed result и восстановления? Варианты навигации, не меняющие контракт, Developer выберет при реализации; отсутствие принятого поведения в требованиях таким выбором не закрывается.

**Условие закрытия:** Analyst обновляет требования и acceptance scenarios со ссылкой на DP-UI-05; негативное утверждение об отсутствии эффекта неактивной кнопки дополняется позитивным контролем открытия фактов той же `chart_identity` без повторного POST. Передаётся точный Analyst commit. Developer и Tester сопоставляют обновлённый пакет со своими work items/checks.

## FIND-DEV-UI-002. Потерянный ответ POST без HTTP outcome

**Type:** observable recovery gap / technical dependency. **Priority:** P2. **Status:** OPEN.
**Owner:** Functional Analyst — наблюдаемый контракт; Manager — строка нового вопроса в едином реестре и delivery impact; Developer — техническая рекомендация; Tester — контрпримеры.
**Blocks:** финальный контракт и оценку work item browser recovery; независимые форма/поиск/таблицы могут оцениваться отдельно.
**Источники:** REQ-UI-09; AS-UI-14 @ `dbee888`; `http_api.md` §§9.2–9.3, 11.1; `tests/http_api/test_build_admission.py` тесты `test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart`, `test_timeout_is_one_execute_and_restarts_against_same_sqlite_state`, `test_disconnect_sends_no_headers_and_keeps_owned_permit_until_work_finishes` @ `9ae1abc`.

**Проявление:** POST принят, protected commit уже начат, но соединение прервано до ответа. Браузер получает сетевую ошибку без `code`, `Retry-After` и `state_version`. Commit может завершиться после ухода клиента. Таблица REQ-UI-09 и AS-UI-14 проверяют ответы 503/504, поэтому не определяют экран и восстановление этого случая. Успешный current со старой картой до завершения удерживаемой работы сам по себе не доказывает остановку исходного POST. Публичный `/health/*` также не является браузерным сигналом: HTTP §11.1 оставляет health внутренним.

**Открытые вопросы Developer:**

1. Как UI показывает неопределённый исход и сохраняет отправленный intent/черновик, если ErrorDTO не получен?
2. Какая безопасная последовательность существующих bootstrap/current запросов и пользовательских действий разрешена при восстановлении соединения, включая ошибку самой сверки?
3. Какой доступный клиенту факт разрешает новый явный build, если current остался old/empty, а остановка прежней задачи не подтверждена? Отсутствие status endpoint — уже принятая граница M1; новый endpoint, polling policy или механизм restart не предлагаются как принятые решения.

**Предварительная техническая позиция Developer:** не объявлять исходный POST неуспешным только по сетевой ошибке и не повторять его автоматически; сохранить intent, использовать существующую read-only сверку и явно различать подтверждённую карту и неопределённый исход. Это input к решению, а не новый утверждённый контракт.

**Возврат:** Manager регистрирует новый semantic question с назначенным decision owner в едином реестре; новый DP-ID здесь не присваивается и выбор владельца не заполняется. После регистрации роль переносит варианты/evidence/рекомендацию в эту строку, а этот finding оставляет её ID и ссылки.

**Условие закрытия:** Analyst передаёт точные требования/AS для потери ответа, успешной/неуспешной сверки и допуска нового действия в принятой границе API; решение, если требуется новая семантика, фиксируется владельцем в реестре. Проверки управляют disconnect/commit через Event/barrier: commit состоялся, не состоялся, ещё не завершён; позитивный контроль подтверждает доступность корректного build после разрешённого восстановления. Ни один из перечисленных тестов в этом review не запускался.

## FIND-DEV-UI-003. Несинхронизированные текущие статусы и handoff

**Type:** requirement baseline / delivery documentation gap. **Priority:** P2. **Status:** OPEN.
**Owners:** Manager — текущий статус/интеграция/реестр; Analyst — собственные статусы, findings и диспозиции.
**Blocks:** выдачу согласованного baseline для финального Implementation Plan; не блокирует документную консультацию по явно указанным версиям.
**Источники:** `artifacts.md` вводные поля и раздел «Плановый бюджет и состояние» @ `ad8892f`; первые абзацы `requirements.md`/`scenarios.md`/`analysis.md`, предложение промежуточного текста в FIND-UI-002 и рекомендации DP-UI-02/04/05 @ `dbee888`; PR #43/#44 и ancestry `9ae1abc`.

**Проявление:** Manager одновременно хранит принятые DP-UI-01…08 и утверждение, что Analysis ещё не интегрирован. Analyst ссылается на старую редакцию реестра, продолжает ожидать решения по scope/gate и содержит промежуточное предложение до уточнения DP-UI-08. Новый исполнитель получает разные ответы о том, что действительно открыто. Формальный G2/G3 при этом всё равно не завершён: merge документов не заменяет консультации/оценки и допуск.

**Комментарий и вопрос Developer:** какие точные commits Manager назначит действующим входом финальной консультации после синхронизации Analyst? Исходный нормативный `652bd734` сохраняется как исторический baseline, текущий реестр и обновлённый requirements package указываются отдельно.

**Условие закрытия:** Manager обновляет сведения об интеграции и точный baseline реестра; Analyst обновляет ссылки/статусы и диспозиции связанных FIND-UI/DP, отмечает судьбу промежуточного предложения по DP-UI-08 и переносит DP-UI-05 в требования/AS. Открытый долг DEBT-UI-001 не объявляется выполненным; статус M1-6 и его принятые ограничения не меняются. Developer получает непротиворечивый handoff на точном commit.

## Проверки и границы evidence

Подход этого изменения — документальные проверки: новых runtime tests, production code и изменения требований не выполняются. Для проверки использованы чтение HTTP DTO/routes/projectors, component contracts, соответствующих sequence diagrams и перечисленного существующего test coverage. Это статический review, не результат выполнения backend/browser сценариев.

- На исходном `9ae1abc`: `git diff --check` — exit 0; `git status --short` — чистое дерево.
- На исходном пакете: `python -B -` с read-only проверкой Markdown — четыре документа, отсутствующие локальные цели ссылок не найдены; 10 последовательных REQ и 21 последовательный AS, незакрытых fenced blocks и trailing whitespace нет. Эта проверка не подтверждает внешние ссылки и будущие чистовые пути.
- `git diff --name-only 652bd734..9ae1abc -- src tests pyproject.toml` — пустой вывод; проверки этого review не приписываются новой реализации.
- Для Developer diff: `python -X utf8 -B -` — exit 0; проверены пять документов, 63 локальные ссылки/якоря и 19 таблиц; три последовательных finding ID, 10 REQ и 21 AS, ошибок нет. Сравнение с `9ae1abc` подтвердило изменения только четырёх полей рекомендаций DP и неизменность текста Analyst/решений владельца. Первое сравнение raw bytes столкнулось с LF/CRLF рабочего дерева; итоговая проверка сравнивает нормализованные строки.
- `git diff --check` — exit 0. После staging выполняется `git diff --cached --check`, после коммита — `git show --check --oneline HEAD`; фактический результат включается в commit/handoff.
- Не запускались pytest, browser/HTTPS acceptance, рендер PlantUML и сетевые smoke tests. Оценка четырёхдневного target, полный Implementation Plan и G2/G3 остаются отдельной работой.

**Handoff:** Manager и Analyst получают этот review commit через текущую Developer-ветку. Публикация в `change/*`, push, PR и коммуникация в другие задачи этим документом не подтверждаются.

## Повторная валидация 2026-10-06

**Административная диспозиция Manager — 2026-10-07:** Tester `0f6aa82` независимо подтвердил TESTABLE и контрактные диспозиции; G2/alignment и G3 завершены в Manager-артефакте. Авторский снимок Developer @ `082c6b9` ниже сохраняет прежние ожидания как историю, не текущие blockers.

**Вход:** `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`, фактический `change/ui-birth-form-and-facts` после PR #48. Developer-ветка обновлена fast-forward. **Реестр:** `artifacts.md` @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`; **Analyst:** `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`, 10 REQ и 23 AS. Это отдельная проверка новой версии; исходные требования/статусы и ожидаемые действия первого review не переписываются задним числом.

Проверены все закрытые DP-UI-01…09, диспозиции FIND-UI-001…005 и ответы на FIND-DEV-UI-001…003 / TEST-FIND-UI-001…003. В реестре присутствуют ACCEPTED и owner evidence; runtime/UI evidence различается явно. Ни один уже принятый выбор не открывается повторно только из-за отсутствия готового UI.

| Решение | Сверенный перенос / техническое evidence | Developer conclusion |
|---|---|---|
| DP-UI-01 | REQ-UI-04–07, AS-UI-07–09/19; current ChartDTO и whitelist. | PASS CONTRACT: scope и публикация согласованы, новые API-блоки не нужны. |
| DP-UI-02 | REQ-UI-04–06 / AS-UI-07–10/15, `project_chart`, golden/current tests. | PASS CONTRACT + BACKEND BASELINE: повторное использование подтверждено, отображение ещё предстоит. |
| DP-UI-03 | REQ-UI-02, AS-UI-02/18, PlaceSuggestionDTO и place whitelist tests. | PASS CONTRACT: naming decision учтён без API alias; прежний долг сохраняется. |
| DP-UI-04 | REQ-UI-03, AS-UI-03/20/21, ADR-0034, DEBT-UI-001. | PASS CONTRACT: закрытый gate и контроль долга разведены; UI evidence позже. |
| DP-UI-05 | REQ-UI-03/10, AS-UI-22, позитивный контроль details нужной identity. | PASS CONTRACT: прежний missing-observable-flow устранён. |
| DP-UI-06 | REQ-UI-02, AS-UI-02: контролируемый timer/late response и сброс ID. | PASS CONTRACT: client threshold не меняет грамматику/нормализацию backend. |
| DP-UI-07 | Owner evidence реестра и отдельные estimates Developer/Tester. | PASS AS TARGET: target не объявлен estimate; [план](ui_birth_form_and_facts_implementation_plan.md#3-стоимость-уверенность-и-допущения) фиксирует отклонение и alignment. |
| DP-UI-08 | REQ-UI-03 / AS-UI-20/21; снятие прежнего предложения в FIND-UI-002. | PASS CONTRACT: промежуточное предложение снято, долг не объявлен закрытым. |
| DP-UI-09 | REQ-UI-09 / AS-UI-23, HTTP §§9.2–9.3; ветви commit/no commit/in progress/failed read и два server disconnect regression. | PASS CONTRACT: ответ на прежний открытый вопрос получен, accepted risk сохранён; browser evidence позже. |

### Закрытие Developer findings

| Finding | Новая диспозиция Developer | Evidence и граница |
|---|---|---|
| FIND-DEV-UI-001 | **RESOLVED IN CONTRACT** | REQ-UI-03/10 и AS-UI-22 @ `ce25dd0` соответствуют DP-UI-05; реализуемость на текущем DTO подтверждена. Отсутствие browser evidence не означает повторного открытия продуктового выбора. |
| FIND-DEV-UI-002 | **RESOLVED IN CONTRACT — ACCEPTED RISK** | DP-UI-09 @ `64934fc` фиксирует owner choice/evidence; REQ-UI-09 и AS-UI-23 задают наблюдаемые исходы и негативный/позитивный контроль. Прежняя более консервативная рекомендация Developer не подменяет принятый выбор B. |
| FIND-DEV-UI-003 | **RESOLVED FOR CONSULTATION BASELINE** | Manager PR #48 интегрирован в `033217d`; новый план задаёт отдельно нормативный вход, текущий реестр и Analyst package. Старые «ожидает записи» в снимке Analyst имеют явную диспозицию по новому реестру. Формальное утверждение пакета и G3 принадлежат Manager. |

FIND-UI-001/004 проверены как resolved in scope, FIND-UI-002 — resolved for closed stage, FIND-UI-003 — resolved in requirements. Выбор FIND-UI-005 зарегистрирован DP-UI-09, поэтому ожидание регистрации на историческом Analyst commit выполнено. Developer не закрывает их future UI checks вместо Tester.

Для TEST-FIND-UI-001/002 изменения Analyst достаточны для Developer-плана: AS-UI-22/23 наблюдаемы и воспроизводимы через leaf transport/timer и управляемый commit. Для TEST-FIND-UI-003 REQ-UI-04 / AS-UI-07 содержат oracle обычных/граничных значений и half-up; bounded Node spike подтвердил семь случаев, включая перенос через 60 минут и половину. **Статусы Tester findings не изменяются**: независимая повторная сверка Tester @ `ce25dd0` ещё требуется.

### Evidence и handoff

- `python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py -q` — **27 passed in 0.69s**, exit 0.
- `python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` — **339 passed in 24.62s**, exit 0; включает обе реальные серверные ветви disconnect и защищённого commit. Эти числа не складываются в число уникальных тестов: projector tests входят во второй запуск.
- Проверочный эксперимент `node --input-type=module -e ...` — **7 cases PASS**, exit 0; точная команда в [плане](ui_birth_form_and_facts_implementation_plan.md#7-проверки-выполненное-и-планируемое). Production helper/renderer не создан.
- [Implementation Plan](ui_birth_form_and_facts_implementation_plan.md) содержит шесть work items, подход, зависимости, coverage gaps, промты, Developer estimate **5–8 дней / 40–64 часа**, confidence и G3 matrix.
- Документальная проверка рабочего пакета `python -X utf8 -B -` — exit 0: 13 документов, 249 локальных ссылок/якорей, 44 таблицы; последовательность 10 REQ / 23 AS, 9 ACCEPTED DP и 6 промтов; арифметика оценки и границы ролевых изменений корректны. `git diff --check` — exit 0. Backend/code, Analyst/Tester, owner choices/status не изменены; index пустой.
- Backend evidence не подтверждает UI/browser/mobile, чистовую редакцию или final acceptance. Полный pytest и исполнение промтов не выполнялись. На этапе planning документы были подготовлены в рабочем diff без поручения на публикацию; затем пользователь отдельно разрешил коммит и push в `change/ui-birth-form-and-facts`. Их фактический исход подтверждается Git evidence в handoff.

**Developer recommendation @ `082c6b9` — история:** продуктовых развилок нет; завершить Tester review/alignment и formal G3 у Manager. **Текущая диспозиция Manager:** эти консультации получены, budgets/plan утверждены, G3 подтверждён; собственный REVALIDATED/FEASIBLE Developer не подменяется implementation evidence.
