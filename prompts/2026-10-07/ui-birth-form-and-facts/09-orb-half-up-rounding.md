# Промт 09. Округление орбиса на половине минуты вверх

Пользователь должен видеть орбис с точностью до угловой минуты по утверждённому правилу. Сейчас допустимый `orb:1.025` отображается как `1°01′` вместо `1°02′` из-за погрешности умножения в JavaScript. Исправить экранное форматирование и закрепить границу тестами; исходные числа карты и категория аспекта сохраняются.

**Дата подготовки:** 2026-10-08. **Owner:** Developer.
**Change / work item:** ui-birth-form-and-facts / [DEV-UI-09](../../../docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-09).
**Источник:** найдено Tester при независимом ревью — [TEST-FIND-UI-013](../../../docs/testing/ui-birth-form-and-facts/manual-test-bugs.md#test-find-ui-013).
**Состояние постановки:** PREPARED / NOT EXECUTED. **Основание:** поручение владельца подготовить промт и включить его в Implementation Plan; исполнение отдельно.
**Estimate Developer:** 2–4 часа / 0,25–0,5 рабочего дня по 8 часов; уверенность высокая. Включены исправление, regression checks и handoff; независимый Tester retest и обновление стенда в оценку не входят.

## 1. Baseline и готовность

- Checkout: `C:/Users/KateUser/.codex/worktrees/c9cb/exact-orb-recovered`; ветка `dev/ui-birth-form-and-facts-review`; baseline подготовки **84410f17304d6ca2a06d3ac2e8e04b3c529b29f0**, получен fast-forward из `change/ui-birth-form-and-facts` 2026-10-08. Реализация 01…08, handoff `ab072ec`, Manager G4 и находка Tester включены в этот HEAD.
- Исходный нормативный baseline **652bd73405db0a0611e98e81af6f3f668dd429f6**: [HTTP API](../../../docs/requirements/http_api.md) §7.2, публичные `ChartDTO.aspects[]` и порядок аспектов. Сверить текущую редакцию на baseline исполнения.
- Approved семантика change **ce25dd0**, текущие административные редакции @ `84410f1`: [REQ-UI-04](../../../docs/requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов) и [AS-UI-07](../../../docs/requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-07-три-группы-натала-и-формат). Точная половина минуты округляется вверх; это только экранное представление. Существующих требований достаточно, нового выбора Analyst не требуется.
- [Единый реестр](../../../docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `84410f1`: применимы DP-UI-01/02 о публичном scope и использовании существующего DTO. Новый DP/ADR не требуется; DEBT-CALC-001 OPEN / NON-BLOCKING для M1-7, согласованный skip сохраняется.
- Прочитать AGENTS.md, [Developer skill](../../../docs/development_approach/skills/developer/SKILL.md), [process](../../../docs/development_approach/process.md), карточку finding, [facts.mjs](../../../src/exact_orb/http_api/ui/facts.mjs), [facts.test.mjs](../../../tests/ui/facts.test.mjs), существующие DOM/session fixtures и [HTTP sequences](../../../docs/sequence_diagrams/http_api/README.md) 003/004.
- Перед исполнением записать фактический HEAD, состояние дерева/index и изменения от baseline подготовки; сохранить несвязанные изменения. Если исправление уже пришло из change, проверить его и покрытие вместо искусственного повторения правки.

## 2. Scope и инварианты

| Файл / область | Разрешённое изменение |
|---|---|
| `src/exact_orb/http_api/ui/facts.mjs` | Только округление `formatOrb` и необходимый комментарий к причине выбора алгоритма. |
| `tests/ui/facts.test.mjs` | Дополнить существующие cases округления и добавить чувствительную mounted regression TEST-FIND-UI-013; переиспользовать текущие fixtures/helpers. |
| Implementation Plan | Обновить фактический способ форматирования в разделе 4, карточку DEV-UI-09 и добавить журнал исполнения/handoff с RED/GREEN и командами. |
| `docs/testing/ui-birth-form-and-facts/manual-test-bugs.md` | Дополнить только TEST-FIND-UI-013 Developer evidence и состоянием FIXED PENDING RETEST после успешных проверок; сохранить исходную находку Tester и его независимое заключение. |

Сохранить исходные `orb`, `type`, `category`, порядок аспектов, DTO/HTTP contracts, расчётный код, позиции точек/домов, known/unknown time, recovery и ручной gate ADR-0034. Минуты всегда двумя цифрами, перенос через 60 минут обязателен. Не вводить ограничение диапазона DTO, epsilon, предварительное обрезание дроби, новые зависимости, изменение golden/допусков или дополнительный HTTP-запрос ради форматирования.
Manager/Analyst/Tester acceptance documents и статусы change не менять. Исторические промты 01…08 сохраняются. Commit/push/PR, запуск и перезапуск стенда, платные/сетевые smoke checks не входят в это задание без отдельного поручения.

## 3. Дефект и подход к исправлению

1. Повторить сценарий из TEST-FIND-UI-013 на текущем коде. Валидный natal DTO проходит `validChart`, реальные mount/form/session/transport/renderer создают непустую строку аспектов, но при `orb:1.025` она содержит `1°01′`. Ожидается `1°02′`; `1.024`, `1.026`, `0.999` — положительные контроли. Заменены только листовые сеть, clock и DOM-порт.
2. Причина подтверждена Developer: `Math.round(orb * 60)` получает для `1.025` число `61.49999999999999`. Имеющиеся семь cases округления проходят и не ловят этот дефект. Диагностика на baseline дала **24 passed** в facts-наборе и **3 passed / 1 failed** в дополнительном mounted сценарии; это результаты до исправления.
3. Предпочтительный вариант: определить нижнюю целую минуту и сравнить исходный `orb` с границей её половины в градусах, `(lowerMinute + 0.5) / 60`. Это сохраняет half-up для `1.025`, `1/120`, `3/120` и различает ближайшие представимые значения по сторонам границы без epsilon. Допустим эквивалентный минимальный алгоритм, если он проходит независимые expected strings и не меняет инварианты.
4. Выбор **тесты → реализация** в одном промте: сначала дополнить существующую параметризацию и mounted regression, получить чувствительный RED, затем минимальное исправление и GREEN того же набора. Отказ загрузки, setup failure или пустая таблица не являются доказательством RED этого дефекта.

## 4. Матрица regression и позитивных контролей

Все строки относятся к REQ-UI-04 / AS-UI-07; сохранить IDs и ссылки в комментариях/tests. Exact test IDs записать при исполнении в handoff.

| Данные / действие | Expected result | Проверка |
|---|---|---|
| `1.025` | `1°02′` | Дополнить существующую параметризацию `formatOrb`; RED до правки. |
| `1.0249999999999997`, `1.0250000000000001` — ближайшие Number ниже/выше `1.025` | `1°01′`, `1°02′` | Позитивные контроли различения соседей; oracle — явные строки, без копирования алгоритма production в тест. |
| `1.024`, `1.026` | `1°01′`, `1°02′` | Сохранить обычное округление. |
| `0.9916666666666666`, `59.5/60`, `0.999` | `0°59′`, `1°00′`, `1°00′` | Нижняя сторона границы, точная половина и перенос минуты в градус. |
| Имеющиеся `0`, `0.008`, `0.009`, `1.5`, `1/120`, `3/120` | Прежние strings, включая `0°01′` и `0°02′` на половинах | Переиспользовать текущие cases; не заменять их новыми входами ради GREEN. |
| Допустимый current natal DTO, только `aspects[0].orb=1.025`; открыть подробности через настоящий `mountBirthForm` | Непустая таблица «Все опубликованные аспекты», соответствующая ячейка `1°02′`; показанная категория соответствует DTO | Mounted regression с существующими session/DOM helpers; `validChart` и непустая строка — позитивные контроли выполнения пути. |
| До/после чтения и открытия подробностей сравнить исходный DTO и число HTTP calls | Числа, type/category и порядок неизменны; открытие подробностей не создаёт запрос | Дополнить mounted case и переиспользовать текущие immutability/no-extra-request tests. |
| Existing natal/cosmogram, категории и golden | Предыдущее поведение сохраняется | Существующий facts/UI-набор; отдельный дублирующий cosmogram mount только ради того же formatter не требуется. |

Диагностический кандидат до реализации прошёл 15 контролей и 32 400 проверок half-boundary/соседей в диапазоне 0…180°. Это bounded spike, а не production regression или новая допустимая граница API. Полный такой перебор не обязателен для закрепления конкретного дефекта; достаточно чувствительного существующего набора с явными expected strings.

## 5. Наблюдаемость

`formatOrb` — чистое экранное преобразование. Новых межкомпонентных переходов и logging events нет; HTTP 003/004 и server load → session_view / build → save сохраняются. Mounted scenario должен действительно прочитать current и отрисовать его факты; непустая таблица и calls подтверждают путь. После открытия подробностей запросы не добавляются, исходная chart identity/category сохраняются. Новые события или payload logs, изменение sequence diagrams и серверной orchestration не нужны.

## 6. Команды проверок

Из корня указанного checkout с существующими Node/Python. Целевая команда выполняется до правки для RED, затем после правки для GREEN. После GREEN — полный UI-набор, связанные HTTP delivery/projector checks и полный pytest по AGENTS.md.

~~~powershell
node --test --test-isolation=none tests/ui/facts.test.mjs
node --test --test-isolation=none tests/ui/*.test.mjs
python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py tests/http_api/test_ui_delivery.py -q
python -X utf8 -B -m pytest -p no:cacheprovider -q -rs
git diff --check
~~~

На RED failures должны относиться к ожиданиям округления, на GREEN — exit 0 и выполнение положительных контролей. Installed-wheel проверки запускать вне checkout по существующему test setup; при sandbox PermissionError сохранить failure и повторить только нужную команду с необходимым доступом. Не добавлять новый skip/xfail для получения GREEN. Полный pytest сохраняет согласованное единственное исключение DEBT-CALC-001; отдельно указать количество skipped и причину, не объявлять долг исправленным. Ссылки/якоря обновлённых документов проверить, новые quality gates не вводить.

## 7. Завершение и handoff

- `1.025` и соседние значения отображаются по матрице; целевые и связанные checks реально выполнены, RED/GREEN подтверждены. Исходный DTO и прежнее поведение сохраняются.
- Записать фактический baseline/состав diff, выбранный алгоритм и причину, test IDs, точные команды/результаты/exit codes, состояние дерева, непроверенное и ограничения evidence в DEV-UI-09 execution journal. Исторический промт не переписывать.
- После исправления TEST-FIND-UI-013 получает **FIXED PENDING RETEST**, окончательное закрытие делает Tester на точной исправленной версии. Node DOM-port не подтверждает live browser/layout, G5 или acceptance; ручной retest зафиксировать отдельно, если он действительно запускался.
- Существующая формулировка REQ-UI-04 достаточна. Если при исполнении обнаружится существенное противоречие expected behavior — вопрос Analyst; расширение scope/delivery — Manager. До разрешения продолжать только независимые проверки. Регистрация промта сама по себе не запускает исправление.
