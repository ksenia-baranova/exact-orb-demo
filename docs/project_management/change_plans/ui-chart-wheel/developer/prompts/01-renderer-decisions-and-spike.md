# DEV-WHEEL-01 — проверить границу renderer и плотность до реализации

Пользователь должен различать все опубликованные точки и аспекты на небольшом экране. Сейчас нет измерений плотности и принятой технической границы замены renderer. Результат этого задания — воспроизводимый отчёт и drawing ADR, позволяющие оценить и утвердить реализацию.

**План / версия:** [DEV-WHEEL-01](../implementation_plan.md#dev-wheel-01-проверенная-граница-и-drawing-rules), consultation v1, TASK-D-001. Worktree `C:\Users\KateUser\.codex\worktrees\ui-chart-wheel-dev\exact-orb-recovered`, ветка `dev/ui-chart-wheel`; исходный HEAD `2b846077b317e33dd892565419942c4db8517b1e`.
**Контракт:** нормативные UI/AS-UI/HTTP и ADR @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`, все ссылки в плане; Analyst [requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) @ `683bdd0c1f5a0e65735f4e48127d408300ec697c` — исходный consultation input, без approvals. REQ-WHEEL-01/02/05/06/10/11, AS-WHEEL-03/04/09/10/16/23/24/25, DP-O-010…014 @ [Manager](../../manager_artifact.md), InputSHA.

## Вход и границы

Подготовка файла не запускает spike. Перед исполнением требуется отдельное назначение Manager / Owner с пределом до 0,75 чд и согласованным предметом. Проверить git HEAD/status и актуальный реестр. Если Analyst уже обновлён, записать точный SHA в план и сверить только затронутые expected results; старую постановку не переписывать. Для production code необходим G3.

Разрешённые результаты: developer/evidence/ для scratch SVG/HTML и измерений, developer/sequence_diagrams/ui/ для технической последовательности, обновление плана/checks, проект нового drawing ADR в docs/requirements/decisions/ с номером после проверки актуального реестра. Scratch отделён от delivery assets и не импортируется production-кодом. Не менять Analyst, Manager, golden, engine, API и session runtime. Commit/push/PR отдельно не поручены.

## Выполнение и проверяемый результат

1. Сопоставить readChartFacts, mountChartResult, main.renderSession, session.publish и DOM port. Предложить минимальный port: accepted ChartDTO + identity + selection → local view; canonical intents обратно; ожидаемый render failure локален. Протокол не содержит HTTP/session/cache. Альтернативный renderer должен подключаться на этом же шве; конкретный API утвердить ADR, не генерировать будущие заглушки.
2. Предложить геометрию, учитывающую принятый DP-O-014: при d=(longitude-reference) mod 360 использовать x=cx-r*cos(d), y=cy+r*sin(d), где d переведён в радианы. Контроль d=0/90/180/270 даёт лево/низ/право/верх в SVG. Данные знака/градуса/orb не пересчитывать.
3. Проверить F1 и явно описанные F3/F3-max из AS-WHEEL-09/10. Критерий overlaps/доступности согласовать до объявления успеха; измерить bbox реального шрифта, glyph+R/☌ и close angles, положение 0°, сохранение порядка и leader lines только при смещении. Не выбирать скрытие объектов вместо Owner.
4. Сохранить 1440/768/360 viewport, устройство/шрифт/масштаб, реальные размеры / screenshots, критерий / actual / вывод; различать glyph bounds и pointer targets. Fake DOM не доказывает layout. При исчерпании timebox с нерешённой плотностью вернуть контрпример Owner, не расширять scope.
5. Technical sequence связывает accepted result, controller, wheel, HTML и отказ/выбор с локальным evidence; не добавлять телеметрию или серверные события локальных действий. Представить ADR и подписанные рекомендации DP-O-010…014 через Manager, пересчитать estimate.

**Подход:** документальные проверки и bounded spike; engine golden и уже покрытые recovery paths не требуют нового RED. Это исследование технического решения, не acceptance реализации.

| Требование / AS | Контроль | Expected result / evidence |
|---|---|---|
| REQ-WHEEL-02 / AS-WHEEL-25 | Четыре d + фактический asc F1 | Правильные стороны / counterclockwise, без demo ref=100 |
| REQ-WHEEL-05 / AS-WHEEL-09/10 | F3 пять R у 0°, F3-max 16 IDs | Измеренный результат по согласованным критериям; не голословный PASS |
| REQ-WHEEL-01/10 / AS-WHEEL-24 | Port с alternate renderer и локальным отказом | Изолированная замена / HTML доступны; план чувствительного integration check |
| REQ-WHEEL-10 / AS-WHEEL-23 | Keyboard / совпадающие цели | У каждого объекта достижимое действие; спорный expected result вернуть Analyst |

**Проверки:** `git diff --check`; документальные ссылки; структура и фактический render новых PUML с указанием команды/версии доступного renderer. Browser commands и версии сохранить в checks; отсутствие renderer явно отметить. Pytest/Node не подменяют размеры; платные/сетевые smoke не запускать.

**Завершение:** report с фактами, draft ADR / sequence, рекомендации в единственный DP и новая оценка переданы назначенному reviewer на точной версии. Пока результата нет, допуск к DEV-WHEEL-02 отсутствует. Продуктовую неоднозначность вернуть Analyst/Owner, schedule — Manager.
