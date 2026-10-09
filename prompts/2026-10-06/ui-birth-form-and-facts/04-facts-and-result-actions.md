# Промт 04. Три группы фактов и действия результата

**Дата:** 2026-10-06. **Change / work item:** `ui-birth-form-and-facts` / [DEV-UI-04](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-04).
**Owner:** Developer. **Состояние постановки:** DRAFT / NOT EXECUTED.
**Основание исполнения:** сейчас поручены planning/estimate/revalidation; production выполнение начнётся только по действующему поручению и после G3 Manager. Подготовка файла не означает допуск.
**Текущий статус work item:** [Implementation Plan](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-04).

## 1. Результат и зачем

Показать реальные опубликованные факты в читаемом формате; details открывает карту той же identity, неактивный чат не создаёт эффекта.

## 2. Источники и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`, ветка `dev/ui-birth-form-and-facts-review`; общий planning HEAD `033217db41aed65d2cd6fadcc1cd1adc7c06d4c9`.
- Нормативный baseline @ `652bd73405db0a0611e98e81af6f3f668dd429f6`: [HTTP API](../../../docs/requirements/http_api.md) §§4–9, 11, 13; component contracts и ADR из [паспорта плана](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#1-baselines-и-разрешённый-контракт).
- Требования change @ `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`: [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация), [REQ-UI-04](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов), [REQ-UI-05](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-05-планеты-точки-и-дома), [REQ-UI-06](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-06-аспекты), [REQ-UI-07](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-07-размещение-будущих-групп), [REQ-UI-10](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-10-доступность-и-визуальная-сверка); [AS](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md) той же версии.
- [Реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `64934fc33b8c04191e7a1b40a40d84b232d948f3`: DP-UI-01/02/05; выбор не копируется в отдельный реестр.
- Зависимости: DEV-UI-03 завершён; committed/current ChartDTO доступны; G3 действует.
- Перед исполнением проверить фактический HEAD/index и наличие предыдущих результатов; если approved baseline отличается, сверить смысл и обновить текущую карточку плана. Не переписывать исторический промт и не откатывать несвязанные файлы.

## 3. Разрешённые файлы и инварианты

| Файл / область | Изменение |
|---|---|
| `src/exact_orb/http_api/ui/facts.mjs` | создать pure formatting и публичный reader |
| `src/exact_orb/http_api/ui/main.mjs, styles.css` | группы и навигация готовности/details |
| `tests/ui/facts.test.mjs и адресные UI fixtures` | создать assertions из existing ChartDTO/golden fixtures |

Существующие HTTP schema/default/error/CAS/lifecycle, расчётный путь, logging levels и `tests/test_module_boundaries.py` сохраняются. Новые client modules создаются только со своим реальным поведением, без future stubs. Wheel, chat/LLM, новые DTO/endpoint/service/dependency, terms text/page, переименование admin1_name и исправление M1-6 вне scope. Не вводить общий mutable результат, TTL-заплатку или global lock. Коммит/push/PR не разрешены подготовкой промта; пользовательские изменения сохранить.

## 4. Действия и подход

1. Использовать sign/degree/minute DTO, порядок ID и домов, orb/type/category; не вычислять положение из longitude и не передавать внутренний artifact.
2. Для неотрицательного orb округлить orb*60 до целого Math.round, затем degree=floor(total/60), minute=total%60 с padStart(2). Half-up/carry задаёт REQ-UI-04, epsilon/новый tolerance не нужен.
3. Показывать null как неприменимость, [] как рассчитанную пустую группу. Космограмма без домов/углов/offset технического полудня, только опубликованные устойчивые аспекты.
4. После committed/current результат даёт два действия по DP-UI-05. Disabled chat видим, исключён из активации; details читает именно текущий DTO. Будущие группы/wheel/chat не имитируются.

**Подход:** TDD для pure formatting/reader; реализация → browser checks для DOM composition. CSS не требует отдельного RED цикла.
**Существующее покрытие:** test_projectors.py exact golden, fixed order и excluded cosmogram aspects. Existing backend tests не проверяют новый DOM/format helper; fixtures переиспользовать.
Тесты вызывают настоящие проверяемые компоненты, заменяют только листовую сеть/таймер/внешний ввод. Если seam/файл отсутствует, сначала подготовить среду и test seam; ошибку импорта не считать проверкой поведения и не скрывать через skip/xfail. REQ/AS IDs и ссылки сохранить в docstring/comments новых тестов.

## 5. Сценарии с oracle

| REQ / AS | Данные / действие | Expected response/state/effects | Проверка |
|---|---|---|---|
| [REQ-UI-04](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов) / [AS-UI-07](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-07-три-группы-натала-и-формат) | orb 0, 0.008, 0.009, 0.999, 1.5, 1/120, 3/120 | 0°00′; 0°00′; 0°01′; 1°00′; 1°30′; 0°01′; 0°02′; category/type не изменены | facts.test.mjs, pure helper + DTO reader |
| [REQ-UI-04](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов) / [AS-UI-07](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-07-три-группы-натала-и-формат) | изменить только longitude при тех же sign/degree/minute; degree=0/29, minute=0/59, обе retrograde | табличные позиции неизменны; нули/границы и R по DTO | facts.test.mjs с непустыми строками как позитивным контролем |
| [REQ-UI-05](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-05-планеты-точки-и-дома) / [AS-UI-08](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-08-космограмма-с-устойчивыми-аспектами) | cosmogram fixture с points и устойчивым аспектом, houses/angles=null | нет фиктивных домов/ASC/offset; points/aspect присутствуют | existing golden + renderer checks |
| [REQ-UI-03](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация) / [AS-UI-22](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-22-действия-после-построения-и-подробности-карты) | chart_identity=A после build и после reload; попытка chat, затем details | chat не отправляет запрос/не открывает диалог; details показывает непустой факт A без POST | transport trace + browser mouse/keyboard |

Для каждого существенного запрета есть разрешённый позитивный контроль. Время/конкурентность задаются управляемым clock/Event/barrier или deferred response; timeout только защищает от зависания. Runtime-тесты и planned файлы этого work item ещё не выполнялись/не созданы при подготовке промта.

## 6. Наблюдаемость

Открытие details является локальным UI переходом, нового server lifecycle/logging нет. Positive control по identity и непустым фактам обязателен рядом с отсутствием chat/POST effects.
Server diagrams: [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md). Чтение/форматирование в UI не добавляют расчёт в browser; сервер не обязан логировать каждый click.

## 7. Проверки

Рабочий каталог — указанный checkout. На planning baseline Python имеет pytest/FastAPI/httpx и Node v24.19.0; `.venv` в worktree отсутствует. Перед новым исполнением проверить runtime, не устанавливать зависимости автоматически.

```powershell
node --test tests/ui/facts.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py -q
git diff --check
```

Команды относятся к будущему исполнению после появления файлов. Для TDD записать behavioral RED и GREEN; для остальных — фактический результат каждой обязательной проверки. Новые backend/browser assertions дополняют только пробелы. Browser setup: [HTTPS runbook](../../../docs/runbooks/http_api_local_https.md); Node/ASGI результат не подтверждает browser cookie/DOM/mobile.

## 8. Завершение, возвраты и отчёт

Formatting/reader tests прошли, оба типа карты и пустые состояния доступны; AS-UI-22 проверен после build/current. Полноценная visual/browser acceptance остаётся Tester.

Смысловой конфликт вернуть Analyst, scope/срок Manager, architecture/security Reviewer только по фактической эскалации. Независимые части продолжить. Записать в [DEV-UI-04](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-04) actual поведение, файлы, commit/состояние дерева, точные команды/exit code/results, причины RED/GREEN при TDD, request/run evidence, непроверенное и следующий шаг. Accepted decisions и Tester acceptance не заполнять от имени владельца.
