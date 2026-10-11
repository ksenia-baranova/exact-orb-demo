# Промт 02. Минутный ввод и подтверждённый выбор места

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-02](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-02).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-02).

## 1. Результат и зачем

Дата, выбранный place_id и известное HH:MM либо явное null готовы для единственного пользовательского build; поиск актуален и доступен клавиатурой.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места), [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация), [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-03/04/06/08; выбор не копируется в отдельный реестр.
- Зависимости: DEV-UI-01 завершён, доступен transport; G3 действует.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/ui/form.mjs, places.mjs` | создать input/selection/timer state |
| `src/exact_orb/http_api/ui/index.html, main.mjs, styles.css` | поля/ошибки/listbox/focus и manual gate |
| `tests/ui/form.test.mjs, tests/ui/places.test.mjs` | создать deterministic state/timer tests |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Сопоставить input rules и existing backend query tests; не переносить нормализацию каталога в браузер.
2. Порядок дата → место → время; ни имени, ни пользовательских координат/offset/секунд. Неизвестность выбирается явно, выбранный ID сбрасывается немедленно при редактировании.
3. Поиск с трёх символов после injected debounce; ранее отправленный ответ не заменяет актуальные подсказки, в том числе после сокращения/очистки. Стрелки/Enter и mouse выбирают конкретный ID.
4. Исходно снятый checkbox запрещает POST до ручной отметки. Его значение не сериализуется/persist; текст/страница/промежуточная сводка условий не создаются.

**Подход:** Тесты → реализация: ошибки client state и late responses требуют управляемого timer/network. Import/fixture failure — preparation, не behavioral RED.
**Существующее покрытие:** tests/test_place_search_contracts.py и tests/http_api/test_place_dto.py уже проверяют backend grammar/whitelist. Client selection/races/keyboard ранее отсутствуют.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места) / [AS-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-02-префиксный-поиск-и-выбор-двух-одноимённых-мест) | К → Ки → Кир → Киро → Ки; ответ Кир приходит после Киро, затем очистка | до трёх GET нет; актуальный prefix получает GET; late response не заменяет список, ниже порога всё очищено | places.test.mjs: real module + fake clock/deferred responses |
| [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места) / [AS-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-02-префиксный-поиск-и-выбор-двух-одноимённых-мест) | два Кировска с разными ID/регионом/страной; ArrowDown/Enter, затем редактирование | выбран ID подсвеченной строки, текст отличает варианты; редактирование сбрасывает ID | state checks + browser keyboard/mouse |
| [REQ-UI-02](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места) / [AS-UI-05](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-05-пустое-или-противоречивое-время) | HH:MM 00:00, 12:00, 23:59; пусто без отметки, 24:00; отдельная отметка неизвестности | valid строки остаются known; invalid submit блокируется; явная неизвестность даёт null | form.test.mjs; позитивный валидный submit после исправления |
| [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация) / [AS-UI-20](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-20-отметка-ознакомления-не-поставлена) | валидный черновик: снятый checkbox, затем ручная отметка | первый submit не создаёт POST, второй допускает payload трёх полей без checkbox | form/transport calls и позитивный контроль |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

Сопоставить HTTP 002-place-search и PlaceSearch/admission message pairs. Запрет GET до порога доказывается browser/leaf transport evidence рядом с разрешённым поиском, не отсутствием серверного лога в пустом пути.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/form.test.mjs tests/ui/places.test.mjs
python -B -m pytest -p no:cacheprovider tests/test_place_search_contracts.py tests/http_api/test_place_dto.py -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

Input/selection/timer tests GREEN, mouse/keyboard путь проверен; новые Node imports реальны, negative controls имеют позитивную пару. Сам build соединяется DEV-UI-03.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-02](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-02) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
