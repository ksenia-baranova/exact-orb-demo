# Промт 06. Адаптивность, реальные проверки и передача Tester

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-06](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-06).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-06).

## 1. Результат и зачем

Подтвердить реальный browser путь, доступность и отсутствие регрессий, затем дать Tester точную версию/setup/evidence с явными пределами.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния), [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места), [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация), [REQ-UI-04](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов), [REQ-UI-05](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-05-планеты-точки-и-дома), [REQ-UI-06](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-06-аспекты), [REQ-UI-07](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-07-размещение-будущих-групп), [REQ-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-08-восстановление-stale-и-unavailable), [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки), [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-01…09; выбор не копируется в отдельный реестр.
- Зависимости: DEV-UI-01…05 завершены, закрытый HTTPS стенд доступен; G3 действует.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/ui/` | только адресные accessibility/responsive/defect fixes |
| `tests/ui/ и tests/http_api/test_ui_delivery.py` | только meaningful gaps/regression tests |
| `docs/ui_ux/README.md; docs/sequence_diagrams/http_api/` | актуальная техническая документация при реально изменённом потоке; demo numbers не oracle |
| `docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md` | карточки/actual журнал/handoff; acceptance Tester не подменять |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Выполнить целевые tests изменённого поведения, затем related HTTP/boundary и full pytest; повторять только после новых правок/проблем.
2. По existing runbook поднять закрытый HTTPS browser путь; проверить настоящую cookie, bootstrap/places/build/current, natal/cosmogram, issues и recovery. Зафиксировать standard path и известный обход FIND-TEST-HTTP-001 отдельно, не исправлять M1-6 попутно.
3. Проверить 360/768/1440 px, keyboard, focus/errors/loading, длинные таблицы и published facts; сравнить композицию/палитру/ритм с draft макетами. Не скрывать значения для прохождения mobile check.
4. Сверить server sequence/events, сохранить request/run IDs и tested commit; Analyst передаёт карту будущего чистового переноса, Tester выполняет независимую сверку/приёмку.

**Подход:** Existing coverage + integration/manual/visual checks, затем документальные проверки; выявленный defect всегда получает deterministic regression.
**Существующее покрытие:** Полный набор Node state tests и existing HTTP/module boundaries; backend results ранее 339 passed, browser evidence новый. Финальный independent test plan/evidence принадлежит Tester.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-01](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-01-первое-открытие-и-источник-состояния) / [AS-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-10-восстановление-без-расчёта) | real HTTPS build, reload с живой cookie и SQLite restart | та же identity/facts без расчёта на GET, draft/empty/stale/unavailable states корректны | browser network + real app + server logs |
| [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка) / [AS-UI-19](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-19-доступность-и-узкий-экран) | 360/768/1440 px; длинная natal таблица; keyboard и field error | все три группы читаемы без горизонтального скролла страницы; focus/labels/errors различимы | manual browser snapshots/checklist с точным commit |
| [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация) / [AS-UI-22](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-22-действия-после-построения-и-подробности-карты) | result actions после build/current | disabled chat без эффекта, active details той же карты без повторного POST | real browser + network positive control |
| [REQ-UI-09](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-09-recovery-и-две-вкладки) / [AS-UI-23](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-23-потерян-ответ-build) | controlled disconnect и failed safe check, затем successful recovery/manual repeat | actual поведение совпадает с AS-UI-23; client tests не выданы за real HTTPS evidence | browser evidence и существующие Event/barrier швы |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

Сопоставить HTTP 001…004 и фактические ContextService/admission/PlaceSearch/Orchestrator/session_view пары, инициатор/peer/порядок/outcome/request/run ID. Нового INFO payload logging нет.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/transport.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/session.test.mjs tests/ui/facts.test.mjs tests/ui/recovery.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q
python -B -m pytest -p no:cacheprovider -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

Blocking implementation defects закрыты, реальные checks и ограничения записаны, воспроизводимый handoff передан Tester. G4 только при выполненных gates; final acceptance/G5/G3 status не присваиваются чужой роли.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-06](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-06) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
