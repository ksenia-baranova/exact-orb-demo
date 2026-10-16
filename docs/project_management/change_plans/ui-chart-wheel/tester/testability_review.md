# Проверка тестируемости и оценка: ui-chart-wheel

**Автор:** Codex / Tester, 2026-10-16; consultation v2 / TASK-T-002. Назначение / прямое поручение Owner, reviewers и сроки — в [индексе](../tester_artifact.md).

**Версия требований:** действующие [REQ-UI-01…10](../../../../requirements/current/ui/birth-form-and-facts.md), [AS-UI-01…23](../../../../requirements/current/ui/scenarios.md), [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto) @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`; предложенные [requirements](../analyst/requirements.md) / [scenarios](../analyst/scenarios.md) Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, включая MODIFY AS-UI-22 и три behavioral sequences. Это review чернового контракта, не approval.

**Версия реестра:** [Manager §3](../manager_artifact.md#3-единый-реестр-dp) @ InputSHA `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`.

**Статус:** TESTABLE WITH CLARIFICATIONS.

**Обоснование статуса:** Analyst v3, 30 AS-WHEEL / MODIFY AS-UI-22 и три sequences сверены с зарегистрированными решениями Owner. Документальные gaps TEST-FIND-WHEEL-001/003 устранены; 002 остаётся OPEN только по измерительным условиям. Источник DTO, выбор / снятие, automatic current и независимый draft имеют определённый expected result. Для окончательного TESTABLE нужны технические критерии DP-O-010…013: замена / изоляция renderer, минимальный разнос / плотность / fallback, измеренное размещение ☌, mobile targets / keyboard order / recovery layout. Новых блокирующих противоречий не найдено. Реализация / CandidateSHA ещё не переданы; runtime-проверок нет.

## Вывод для Manager

Задача ограничена представлением, но её главный риск — согласованность подтверждённой карты, черновика, выбранной планеты / аспекта, раскрытия таблиц, ошибок и восстановления. Отдельный тест SVG не докажет M1-8. Нужны геометрические component tests, mounted-интеграция с реальными coordinator / transport и браузерная проверка плотности, клавиатуры / focus.

В v3 продуктовая семантика достаточна для продолжения согласования технических критериев и условного плана. В AS-WHEEL-28/29 взаимоисключающие состояния, строка / графическая пара и доступное повторное снятие согласованы с REQ-WHEEL-07/08 и sequence 002. AS-WHEEL-30 сохраняет адресуемый выбор по новым фактам, снимает только исчезнувший, сохраняет раскрытие / dirty draft и отличается от F5 / нового явного build. После successful build collapse зависит от совпадения текущих полей со snapshot. Оформление ☌: подпись категории и контур только выбранного символа; эти правила больше не OPEN.

Manager регистрирует авторский результат и назначенные reviewers проверяют точную опубликованную версию. Готовность G1 / G3 и разрешение implementation этим заключением не подтверждаются. Прежний Developer v1 @ `04be207627de1049deac2e069574e01b62536607` не считается повторной консультацией v3; нового результата TASK-D-002 на входе нет.

## Недостающие основания

| Замечание | Влияние | Адресат |
|---|---|---|
| [TEST-FIND-WHEEL-001](defects.md#test-find-wheel-001) | CLOSED: v3 / реестр согласованы; это документальное closure evidence, не PASS реализации | Tester, 2026-10-16; Manager регистрирует handoff |
| [TEST-FIND-WHEEL-002](defects.md#test-find-wheel-002) | OPEN: минимальность / предел / fallback, реальные bbox / R / несколько ☌; подпись и контур символа уже приняты | Developer; Analyst / Owner по наблюдаемому пределу |
| [TEST-FIND-WHEEL-003](defects.md#test-find-wheel-003) | CLOSED: AS-WHEEL-28/29 определяют оба перехода / снятие без возврата фильтра | Tester, 2026-10-16; runtime ещё NOT RUN |

Остаток DP-O-010…013: replacement seam, измерительная геометрия / dense fallback, палитра / размещение, mobile targets / keyboard order / recovery layout и точная композиция блока углов. Новых DP нет. DP-O-014 уже ACCEPTED и перенесён в v3; drawing ADR / геометрические проверки ещё впереди. Смысловые правила same/different current и формы больше не считаются невыбранными. Findings Analyst / Developer самостоятельно не закрывались.

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

Сравнение нормативного MainBaseline с InputSHA подтвердило неизменность src / tests / requirements / процесса. Опубликованный main @ `bba8d6cfb22f586f86c3035423f2535ede158b9f` имеет то же Git tree, что нормативный `5355510`; это совпадение дерева, не принятие M1-8. Отсутствие wheel tests — работа будущего этапа. Матрица охватывает 22 требования, 30 AS-WHEEL и 23 AS-UI, включая MODIFY AS-UI-22; наличие сценария не даёт SUFFICIENT.

## Оценка повторной консультации

TASK-T-002: 0,5–0,75 чд, средняя уверенность; сверка 30 AS / DELTA / трёх sequences / реестра, документальное closure 001/003, актуализация плана / матрицы / evidence. Предположения: один стабильный InputSHA, без нового технического пакета, runtime и дополнительных циклов Owner decisions. Сроки исполнения / reviewer / эскалации по-прежнему согласует Manager; это не измеренное elapsed time.

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

Baseline Manager @ InputSHA; связанные DP-O-010…014. В [decision_input.patch](decision_input.patch) подготовлен новый подписанный вклад TASK-T-002: закрытые gaps не повторяются как открытые, принятые подпись / контур ☌ и automatic current сохраняются. Только добавление в колонку рекомендаций; Manager-файл не изменён, регистрация нового результата ожидается. Owner choices / статусы DP / gates не изменяются. Предыдущая consultation v1 и её evidence доступны на `9dd8b96` в Git history.
