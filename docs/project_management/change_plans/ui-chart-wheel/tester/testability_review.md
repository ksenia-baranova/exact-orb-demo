# Проверка тестируемости и оценка: ui-chart-wheel

**Автор:** Codex / Tester, 2026-10-15; v1, консультация по поручению Owner. Предлагаемый TaskId и полномочия — в [индексе](../tester_artifact.md).

**Версия требований:** действующие [REQ-UI-01…10](../../../../requirements/current/ui/birth-form-and-facts.md), [AS-UI-01…23](../../../../requirements/current/ui/scenarios.md), [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto) @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`; предложенные [requirements](../analyst/requirements.md) / [scenarios](../analyst/scenarios.md) Analyst v1 @ `683bdd0c1f5a0e65735f4e48127d408300ec697c`. Это review чернового контракта, не approval.

**Версия реестра:** [Manager §3](../manager_artifact.md#3-единый-реестр-dp) @ InputSHA `2b846077b317e33dd892565419942c4db8517b1e`.

**Статус:** TESTABLE WITH CLARIFICATIONS.

**Обоснование статуса:** источник ChartDTO, категории, принадлежность карте, safe-read/recovery и неизменность расчётных фактов имеют наблюдаемый oracle. Для финальных графических и interaction checks недостаточны критерии DP-O-010…013. Analyst v1 / sequences ещё не включают решения Owner от 15 октября. TEST-FIND-WHEEL-001…003 ограничивают соответствующие проверки; независимую подготовку можно продолжать. Кода M1-8 и CandidateSHA нет, проверка реализации не выполнялась.

## Вывод для Manager

Задача ограничена представлением, но её главный риск — согласованность подтверждённой карты, черновика, выбранной планеты / аспекта, раскрытия таблиц, ошибок и восстановления. Отдельный тест SVG не докажет M1-8. Нужны геометрические component tests, mounted-интеграция с реальными coordinator / transport и браузерная проверка плотности, клавиатуры / focus.

Analyst v1 пригоден для консультации, но утверждать всю версию для реализации преждевременно. Analyst выпускает согласованную редакцию по реестру, Tester повторно проверяет затронутые обязательства. Manager регистрирует участие, TaskId, reviewer, критерий и сроки. Этот review не подтверждает G1 / G3.

## Недостающие основания

| Замечание | Влияние | Адресат |
|---|---|---|
| [TEST-FIND-WHEEL-001](defects.md#test-find-wheel-001) | Уже принятые решения всё ещё условны в v1; сценарий снятия описывает отклонённую отдельную кнопку | Analyst; Manager сверяет версию |
| [TEST-FIND-WHEEL-002](defects.md#test-find-wheel-002) | Минимальный разнос, предел плотности и категория / выбор у ☌ не имеют окончательного воспроизводимого oracle | Developer; Analyst / Owner по наблюдаемому пределу |
| [TEST-FIND-WHEEL-003](defects.md#test-find-wheel-003) | Не определён переход от выбранной планеты к чужому аспекту и снятие самостоятельного аспекта | Analyst / Owner в DP-O-013 |

Остальные вопросы уже в DP-O-010…013: повторный current той же карты, форма, hit targets / focus-order, композиция углов и replacement contract. Здесь не создаётся второй реестр решений. DP-O-014 уже ACCEPTED: нового выбора ориентации не требуется, нужны актуализация и проверки. Findings Analyst самостоятельно не закрывались.

## Данные и независимые проверки

[T-WHEEL-01…14](test_plan.md#независимые-сценарии) выделены по требованиям / решениям до чтения Developer tests; затем assertions сопоставлены в [матрице](coverage_matrix.md).

- Валидные данные: F0 natal / cosmogram, F1; committed POST / current; 16 points, 12 домов, пять angles; endpoints points и asc/mc/vertex; семь типов × три категории; пустой aspects / только background; retrograde true / false.
- Границы геометрии: относительные 0/90/180/270°, 359.99/0/0.01°; разрежённые точки, конфликтующая группа и далёкая точка, пять R через 0°, 16 IDs и несколько ☌. Это контролируемые опубликованные UI-данные, не новый путь пользовательского ввода.
- Порог таблиц: 0/1/4/5/6/46 аспектов, планета с 0/1/5/6 аспектами; natal houses — 12, первые 5 / все; cosmogram houses=null. Невалидный natal с четырьмя домами ради UI-порога не требуется.
- Негативные: malformed / null / unknown endpoint на существующем response-validator seam; неверная форма, неподтверждённый place_id, снятый gate. Renderer получает только принятый DTO; новые error codes не выбираются.
- Recovery / lifecycle: карта A, черновик B, pending reply; 422/429/capacity; lost POST, commit failure, timeout/restart; две вкладки, superseded, already_applied и dispose/late response; empty/unavailable/stale. Управляемые deferred / fake clock, без реальных задержек.
- Позитивные контроли запретов: успешные исходные GET и принятая identity; один разрешённый явный POST; успешный render до отказа; реальный выбор до очистки. Нулевой счётчик без работающего пути недостаточен.

Пользовательские секунды / микросекунды, координаты точнее 0.01°, новые расчётные группы и полный V2 вне scope. Принятый долг не объявляется новой находкой; исключений новых требований без решения Owner нет.

## Аудит существующего evidence

Проверены чтением assertions `facts.test.mjs`: опубликованные позиции вместо пересчёта из longitude, порядок IDs / домов / аспектов, пять углов, семь type / три category, неизменность DTO, cosmogram, очистка empty/unavailable и сохранение stale. Mounted orb=1.025 проверяет transport, исходный DTO и отсутствие лишних HTTP, но не SVG.

В `session.test.mjs` прочитаны immutable submitted summary при pending draft, birth из current, прежняя сводка после отказа и fallback с timeout/restart gate. В `recovery.test.mjs` проверен сценарий двух реальных coordinator с общим листовым persistence и сохранением draft. `documentPort` не доказывает layout, hit testing или настоящий SVG focus. Полный аудит всех старых data classes ещё не выполнен; collection / test run не проводились. Старые результаты M1-7 не приписываются InputSHA.

MainBaseline…InputSHA содержит только 12 документов change; production code / tests / конфигурация не изменены. Отсутствие wheel tests — работа будущего этапа, не дефект принятого M1-7. Матрица охватывает 22 требования, 25 AS-WHEEL и 23 AS-UI. Наличие сценария не даёт SUFFICIENT.

## Оценка независимого тестирования

| Работа после согласованного контракта / G4 | Чд |
|---|---|
| Уточнение плана / fixtures / traceability и review обновлённой версии | 0.5–0.75 |
| Недостающие component checks геометрии / отбора / стилей, аудит Developer coverage | 0.75–1.25 |
| Mounted-интеграция coordinator / renderer, failure и recovery | 0.75–1.25 |
| Браузер: 1440/768/360, keyboard/focus, плотность / легенда, HTTPS smoke | 0.5–1 |
| Один цикл retest, regression, матрица / evidence | 0.5–0.75 |
| **Всего** | **3–5** |

Уверенность средняя. Условия: один Tester, стабильный CandidateSHA после G4; актуальные approved requirements / drawing ADR; fault-injection / replacement seam; воспроизводимый HTTPS-стенд без LLM / платных сервисов; один согласованный Chromium-браузер, viewport mobile без обещания физического телефона; fixtures / каталог доступны; один цикл исправлений. Браузеры и масштабирование согласуются до G4. Массовая переработка, дополнительные устройства / браузеры и новые решения требуют пересмотра. Ожидание ответов / стенда в чд не включено. Это трудозатраты Tester, не бюджет change, не оценка Developer и не календарный срок.

Acceptance, полный pytest и сверка чистового переноса сейчас не выполнялись. После Owner acceptance изменённых требований потребуется сверка с Analyst transfer_map с сохранением фактического TestedSHA.

## Вклад в реестр

Baseline Manager @ InputSHA; связанные DP-O-010…014. Подписанные рекомендации — в [decision_input.patch](decision_input.patch), только добавление в колонку рекомендаций. Действующий Manager-файл не обновлялся; регистрация ожидается. Owner choices, статусы DP и gates не изменяются.
