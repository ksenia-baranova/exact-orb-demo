# DEV-WHEEL-02 — SVG подтверждённого ChartDTO с локальным отказом

После принятого build/current пользователь сразу видит колесо той же карты, что и HTML. Результат будущего шага — native SVG с истинными позициями, согласованными R/☌ и аспектами; сбой SVG сохраняет подтверждённый HTML новой карты.

**Редакция 2 / TASK-D-002, 2026-10-16:** прежняя неисполненная постановка @ `04be207627de1049deac2e069574e01b62536607` заменена для v3. **InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`; `dev/ui-chart-wheel`, worktree в [индексе](../../developer_artifact.md). [DEV-WHEEL-02](../implementation_plan.md#dev-wheel-02-svg-той-же-опубликованной-карты).
**Контракт:** нормативный UI / AS-UI / HTTP / ADR @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1` + [requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; ссылки в плане. REQ-WHEEL-01…06/09…11, AS-WHEEL-01…10/15/16/24/25 и graphical branch 28/30. DP-O-001/002/004…007/009…012/014 @ Manager/InputSHA; ADR-0029/0030/0032/0034/0040/0041 и отдельно принятый drawing ADR.

## Готовность / scope

До кода требуются DEV-WHEEL-01, approved drawing rules / уточнённый Analyst SHA, согласованные blockers и G3 на этот срез. Проверить фактический Git и разрешение, записать точные approved версии в план. Наличие этого файла не разрешает исполнение; текущая TASK-D-002 код не включает.

Разрешённые будущие файлы: новые ui/wheel*.mjs по ADR, минимальное main/facts/styles подключение; tests/ui/wheel*.test.mjs, листовые SVG DOM API / controlled fixtures, UI_RESOURCES в tests/http_api/test_ui_delivery.py. API / calculation / session/recovery алгоритм не менять. Longitudes читать из принятого ChartDTO: readChartFacts их не сохраняет. Новые зависимости / network / aliases / engine golden adjustments запрещены; чужие файлы сохранить, commit/push отдельно.

**Подход:** чистая geometry / endpoint resolver / category mapping — тесты → минимальная реализация; SVG DOM сборка — реализация → mounted integration tests. Existing facts/projector tests сохраняют данные, но SVG не покрывают. Проверять cardinal positions / IDs / coordinates, не snapshots private path builder. Import failure не является behavioral RED.

True anchors и концы аспектов используют опубликованные longitude / cusp_longitude; разнос меняет только метку с leader line. Без выбранного аспекта графически все exact/working; selected aspect ограничивает графику одной парой при сохранении всех объектов. Background даже выбранный даёт только два конца без линии / ☌. ☌ имеет подпись категории; selected contour только символа, подпись остаётся. Никаких расчётов sign/degree/minute/house/type/category/orb.

| REQ / AS | Данные / действие | Expected result / позитивный контроль |
|---|---|---|
| REQ-WHEEL-02 / AS-WHEEL-03/25 | reference+0/90/180/270, asc F1, cosmogram | Лево/низ/право/верх; natal ASC / cosmogram Aries слева, без demo ref=100 |
| REQ-WHEEL-02/04 / AS-WHEEL-04 | F0 moon→asc exact square | Опубликованный angle endpoint не потерян, оба конца реальные; dsc/ic не добавлены в аспектную сетку |
| REQ-WHEEL-02/05 / AS-WHEEL-03/09/10 | F1 / F3 / F3-max | Все IDs/R, 12 домов и 5 angles F1, true anchors неизменны; плотность по approved measured критерию |
| REQ-WHEEL-03/04 / AS-WHEEL-05…07 | Cosmogram, empty aspects, 3 категории / conjunction | Нет вымышленных углов/домов; пустой графический набор отличим от no chart; background без ☌ |
| REQ-WHEEL-06 / AS-WHEEL-07/08 | Линии / ☌ до и после выбора | Exact solid, working dashed, выбранная линия толще с тем же рисунком / цветом; у выбранного ☌ контур только символа и текст категории |
| REQ-WHEEL-04/08 / AS-WHEEL-28/30 | Selected pair; новый DTO с category=background | Только выбранная графическая пара; новые координаты / category, старая линия исчезла; controller wire — в DEV-WHEEL-03 |
| REQ-WHEEL-01/10 / AS-WHEEL-24 | Успешный / альтернативный / принудительно отказавший renderer при B после A | HTML B доступен, SVG A удалена, отказ B видим, нет POST / ожидаемого session reconciliation |

**Observability:** accepted DTO / identity → HTML / SVG → visible outcome, упорядоченные callbacks / DOM assertions, без runtime telemetry. Не подавлять отказ изображения и не оставлять частичную A рядом с B. Общий fallback неожиданных иных ошибок сохраняется.

**Команды:** `node --test tests/ui/wheel*.test.mjs` после создания targets; `node --test tests/ui/facts.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs`; затем `python -m pytest tests/http_api/test_projectors.py tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py`. Отдельно browser measurements 1440/768/360, шрифт / scale / focus. Full pytest — финальный handoff на CandidateSHA.

**Завершение:** target / related results и ограничения привязаны к фактическому SHA, geometry RED/GREEN чувствителен к mirrored / missing-angle примеру, локальный failure/replacement воспроизводим. Tester acceptance отдельно. Неопределённый контракт вернуть Analyst; недостижимый measured предел — Manager/Owner, без самовольного расширения.
