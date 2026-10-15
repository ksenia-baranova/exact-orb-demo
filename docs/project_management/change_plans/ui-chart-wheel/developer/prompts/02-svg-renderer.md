# DEV-WHEEL-02 — показать SVG из опубликованного ChartDTO

После принятого build/current пользователь сразу видит колесо той же карты, что и HTML. Результат шага — native SVG с опубликованными точками, домами/углами и допустимыми аспектами, с видимым локальным отказом при сбое изображения.

**План:** [DEV-WHEEL-02](../implementation_plan.md#dev-wheel-02-svg-той-же-опубликованной-карты), TASK-D-001 / consultation v1. Ветка `dev/ui-chart-wheel`, worktree как в [индексе](../../developer_artifact.md), исходный HEAD `2b846077b317e33dd892565419942c4db8517b1e`.
**Источники:** обе части контракта и точные SHA в плане: нормативный baseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`, Analyst requirements/scenarios v1 `683bdd0c1f5a0e65735f4e48127d408300ec697c`; эти версии ещё consultation input. REQ-WHEEL-01…06/09…11; AS-WHEEL-01…10/15/16/24/25. DP-O-001/002/004…007/009…012/014 @ Manager/InputSHA; ADR-0029/0030/0032/0034/0040/0041 и будущий drawing ADR из DEV-WHEEL-01.

## Перед запуском

Требуются результат DEV-WHEEL-01, approved drawing rules, синхронизированный Analyst с точным опубликованным SHA и назначение G3 на этот work item. Проверить Git, Manager и применимые DP; записать новые утверждённые SHA / approvals в план до кода. Если этих входов нет, вернуть Manager недостающее; наличие этого промта не даёт разрешения на реализацию.

**Scope:** новые renderer/geometry modules в src/exact_orb/http_api/ui/ по принятому ADR, минимальное подключение в main.mjs/facts.mjs/styles.css; tests/ui/wheel*.test.mjs и нужный листовой DOM API/controlled fixtures; UI_RESOURCES в tests/http_api/test_ui_delivery.py. Схемы API, расчёт, session/recovery и транспорт не менять. Долготы читать из принятого DTO: readChartFacts их не сохраняет. Не менять golden и допуски. Не вводить dependencies или новую сеть. Сохранить чужие изменения; commit/push не поручены.

## Реализация и подход

Чистая геометрия / endpoint resolver / состав линий: тесты → минимальная реализация. Прямые assertions сторон, IDs и координат дают чувствительность к зеркальности/округлению/потерянным angles; snapshots самих generated paths недостаточны. DOM сборка — реализация → mounted integration tests на реальных компонентах. Сначала проверить существующие facts/projectors tests, не дублировать их целиком.

True positions и окончания аспектов следуют longitude / cusp_longitude; разнос изменяет только label position и связывается leader line по принятому алгоритму. Ни знак, ни дом, ни orb/type/category браузер не рассчитывает. Cosmogram не синтезирует дома/углы. Background не получает линии или ☌. Сбой wheel не оставляет прежнюю SVG identity рядом с новыми HTML и не включает session reconciliation из-за ожидаемой локальной ошибки.

| REQ / AS | Данные / действие | Expected result и способ проверки |
|---|---|---|
| REQ-WHEEL-02 / AS-WHEEL-03/25 | longitude=reference+0/90/180/270 и asc F1 | Лево/низ/право/верх, ASC natal слева; отдельно cosmogram 0 Aries слева; origin и радиус заданы тестом |
| REQ-WHEEL-02/04 / AS-WHEEL-04 | F0 natal moon→asc square exact | Линия связывает point с опубликованным angle, не пропущена; позитивный контроль обеих координат |
| REQ-WHEEL-02/05 / AS-WHEEL-03/09/10 | F1 и F3/F3-max | 16 F1 points, 12 домов, пять angles; R только по флагу; истинные отметки не смещены; density по approved критерию |
| REQ-WHEEL-03/04 / AS-WHEEL-05/06/07 | Cosmogram и пустой aspects, exact/working/background ☌ | Нет придуманных домов/углов; empty отличим от no chart; ☌ только разрешённых категорий |
| REQ-WHEEL-06 / AS-WHEEL-08 | Все семь public types, exact/working | Тип / категория / выделение / legend по принятому DP, не только цвета; background line sample не обещает существующую линию |
| REQ-WHEEL-01/10 / AS-WHEEL-24 | Alternate renderer; forced wheel failure на B после A | Замена ограничена port; HTML B сохранён, отказ виден, SVG A нет; нет POST, успешный renderer является позитивным контролем |
| REQ-WHEEL-09/10 / AS-WHEEL-16/23 | Browser 1440/768/360 + keyboard | Размеры / читабельность / focus проверяются браузером, а не fake DOM |

**Observability:** упорядоченное deterministic evidence accepted DTO → HTML / SVG → visible result/failure с одной identity. Не добавлять runtime logging service. Ошибку изображения не подавлять: сделать видимой в согласованной границе.

**Команды из root:** `node --test tests/ui/wheel*.test.mjs` (после создания этих тестов); `node --test tests/ui/facts.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs`; затем `python -m pytest tests/http_api/test_projectors.py tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py`. Browser измерения — отдельные commands / screenshots. Не запускать отсутствующий target и не считать import failure RED поведения. Full pytest — в общем handoff DEV-WHEEL-04 на CandidateSHA.

**Завершение:** точные SHA, чувствительный RED/GREEN чистой логики, actual target/related results и browser пределы в checks; scope / known blockers записаны. Независимая приёмка Tester не объявляется. Неподготовленный expected result вернуть Analyst; невозможность density — Manager/Owner через DP-O-011.
