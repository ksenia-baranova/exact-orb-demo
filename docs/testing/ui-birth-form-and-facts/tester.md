# Tester: ревью и независимые проверки ui-birth-form-and-facts

**Последняя независимая проверка:** 2026-10-09, завершение Tester acceptance на `063c8439de3392c888383913fabffa336bd0c44e`; автоматическая регрессия и остальные browser checks выполнены 2026-10-08 на `a8b45dbbda5378e598eb75b15f81e1445a75020e`.
**Итоговый verdict:** **READY_FOR_ACCEPTANCE** — рекомендация Tester для закрытого M1-7. TEST-FIND-UI-004…013 CLOSED; все 23 AS — PASS на зафиксированных уровнях, все 10 REQ — SUFFICIENT.
**Обоснование:** живой foreground AS-UI-16 выполнен пользователем в Яндекс.Браузере и подтверждён Tester по двум скриншотам, полным DTO и server/wire events: карта B показана в A, черновик A сохранён, скрытого POST нет. Чистовая редакция Analyst `879a4ee` сверена: 10 REQ /23 AS и 33 transfer IDs без semantic delta; 167 links/62 anchors/7 diagrams PASS. Production code/tests совпадают с проверенным `a8b45db`, старые test runs не приписываются новому commit. [Актуальная матрица, baselines, команды, ограничения и handoff](acceptance-a8b45db.md#tester-completion-063c843); [новый JSON evidence](acceptance-063c843.json). Manager решает G5 и final acceptance; ACCEPTED/merge/publication этим verdict не объявлены. Исторические раунды ниже сохраняются.

## Историческое ревью документов @ `082c6b9`

**Роль:** Tester. **Дата:** 2026-10-06.
**Ветка:** `test/ui-birth-form-and-facts-review`.
**Проверенный baseline документов:** `082c6b9ac5c8b054c38de5f17bc673956ec058d8`.
**Область:** повторное ревью артефакта Manager, исправленного Analyst-контракта,
Implementation Plan и шести промтов Developer; testability consultation.
**Статус:** TESTABLE — авторский независимый verdict @ `0f6aa82`, review baseline `082c6b9`.
**Административная диспозиция Manager — 2026-10-08:** Developer handoff `ab072ec` интегрирован PR #51 / `0c893f0`; общий change получил READY_FOR_TEST, G4 подтверждён. DEBT-CALC-001 остаётся OPEN / NON-BLOCKING для M1-7. Budget Testing 5 дней сохраняется; Tester execution, retest TEST-FIND-UI-004…012 и acceptance остаются NOT RUN.
**Обоснование статуса:** все 10 требований связаны с 23 сценариями; TEST-FIND-UI-001…003
устранены на уровне контракта. Промты предусматривают наблюдаемые expected results,
управляемые timer/network швы и позитивные контроли. Существенных новых блокеров
тестируемости не найдено. Исполняемые UI-проверки не выполнялись; это заключение
о документах, не acceptance evidence реализации. Исторический Manager alignment/G3 выполнен;
последующая Developer implementation интегрирована в `0c893f0`. Этот Tester-отчёт ещё
не содержит execution evidence новой версии; фактическая независимая проверка не началась.

## Baselines и источники

- Исходный нормативный baseline — `652bd73405db0a0611e98e81af6f3f668dd429f6`:
  [HTTP API](../../requirements/http_api.md) §§4–9, 13;
  [каталог мест](../../requirements/component_responsibilities/exact-orb_place_catalog.md);
  [Build Natal](../../requirements/component_responsibilities/exact-orb_build_natal_components.md);
  [сессия](../../requirements/component_responsibilities/exact-orb_session_requirements.md);
  [сохранённая карта](../../requirements/session/stored-chart-session-behavior.md);
  ADR-0008, 0029–0034, 0039–0041.
- Текущая черновая Analyst-редакция — `ce25dd0bebf5eb3b6d41fe933d1809005e5779ab`:
  [requirements.md](../../requirements/changes/ui-birth-form-and-facts/requirements.md),
  [scenarios.md](../../requirements/changes/ui-birth-form-and-facts/scenarios.md),
  [analysis.md](../../requirements/changes/ui-birth-form-and-facts/analysis.md).
- Manager-редакция — `64934fc33b8c04191e7a1b40a40d84b232d948f3`;
  единый реестр сверяется в общем `082c6b9`, содержащем также подписанный вклад Developer:
  [artifacts.md](../../project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register),
  [roadmap.md](../../project_management/roadmap.md).
- Developer-пакет — `082c6b9ac5c8b054c38de5f17bc673956ec058d8`:
  [Implementation Plan](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md),
  [повторная валидация Developer](../../project_management/implementation_plans/ui_birth_form_and_facts_developer_review.md),
  промты `01`…`06` в `prompts/2026-10-06/ui-birth-form-and-facts/`.
- Общий review HEAD `082c6b9` содержит Analyst PR #47 / `a6c4d6f`, Manager PR #48 / `033217d`
  и Developer-пакет. Ветка Tester обновлена fast-forward с `81624f8` до `082c6b9`.
  Первичное review `81624f8` относилось к `9ae1abc`, Analyst `dbee888`, Manager `ad8892f`
  и 21 AS; его фактические baselines и проверки сохраняются ниже как история.
  Факт интеграции не означает утверждения требований или готовности к разработке.
- Применены [Tester skill](../../development_approach/skills/tester/SKILL.md),
  [процесс](../../development_approach/process.md),
  [ownership](../../development_approach/roles.md) и
  [шаблон Tester](../../development_approach/artifacts/tester.md).

## Вывод для Manager

С точки зрения Tester исправленный контракт и Developer-пакет готовы к Manager alignment.
AS-UI-22 задаёт действия результата, AS-UI-23 — потерю ответа и выбранный DP-UI-09,
REQ-UI-04 / AS-UI-07 — oracle округления орбиса. Уточнения прежнего review выполнены;
повторного продуктового выбора по этим вопросам не требуется.

**Исторический возврат Manager на review baseline `082c6b9`:** `artifacts.md` §§«Черновое описание»/«Плановый бюджет» ещё сообщал об отсутствии
Developer estimate и Implementation Plan. На `082c6b9` они уже опубликованы: 5–8 дней,
40–64 часа, включая резерв. Manager должен актуализировать вход G3, согласовать отличие
оценок от target, зависимости и Change Plan/Gantt. Это следующий этап alignment после
поступления Developer-пакета, не новая неоднозначность UI-контракта.

Tester подтверждает собственный estimate 3–5 рабочих дней при заявленных условиях среды;
план Developer эту оценку не заменяет. Все шесть промтов сохраняют DRAFT и допуск через G3.
Этот отчёт не меняет статус change и не разрешает их исполнение.

**Связанные решения:** DP-UI-01…09.
**Обновления реестра:** не выполнены. Пользователь поручил ревью и последующее сохранение
его результата коммитом; документы Manager/Analyst и строки решений не изменялись.
Manager получает findings и estimate из этого отчёта для собственного alignment.

## Замечания: первоначальное наблюдение и повторная диспозиция

Все замечания относятся к документам и основаниям проверки. Подтверждённых багов реализации
в этом review нет; Severity — N/A. Priority предложен Tester и не подтверждён Manager.

<a id="test-find-ui-001"></a>
### TEST-FIND-UI-001. Состав действий не перенесён в Analyst-контракт

**Тип:** requirement/source alignment gap; существующий возврат Analyst.
**Owner:** Functional Analyst.
**Связь:** DP-UI-05; REQ-UI-03, REQ-UI-10; AS-UI-03, AS-UI-07, AS-UI-19.
**Severity:** N/A — ревью требований, не баг реализации.
**Priority:** P2, PROPOSED — согласовать до завершения G2 и допуска соответствующего UI work item.
**Blocks:** больше не блокирует контракт экрана готовности; UI acceptance ещё не выполнялась.
**Статус:** RESOLVED IN CONTRACT.
**Обоснование статуса:** на `082c6b9` REQ-UI-03/10 и AS-UI-22 @ `ce25dd0`
согласованы с DP-UI-05; Tester повторно сверил оба действия и позитивный контроль.
Прежний разрыв `9ae1abc` устранён. Browser evidence требуется после реализации.

- **Воспроизведение:** сопоставить Manager `artifacts.md` строку DP-UI-05 и задание Analyst
  со строкой 78 `requirements.md`, строками 27/90 `analysis.md` и AS-UI-03/07/19.
- **Фактически:** Analyst ещё ожидает окончательного состава действий; подписанная рекомендация
  о кнопке чата предшествует решению. Сценария двух действий после расчёта нет.
- **Ожидается:** Analyst переносит принятый наблюдаемый состав в requirements/scenarios
  и явно отделяет прежнюю рекомендацию от текущего решения. Дополнительный выбор владельца не нужен.
- **Позитивный контроль будущей проверки:** активные подробности открывают факты той же
  `chart_identity` без повторного POST; рядом проверяется отсутствие запросов и навигации
  при действиях мышью/клавиатурой над неактивной кнопкой чата.
- **Условие закрытия:** требования, сценарий и диспозиция соответствуют DP-UI-05;
  Tester сверил новую редакцию. Browser retest относится к последующей реализации.

<a id="test-find-ui-002"></a>
### TEST-FIND-UI-002. Нет UI-сценария потери ответа POST

**Тип:** requirement/testability gap.
**Owner:** Functional Analyst; Developer предоставляет управляемый шов для дальнейшей проверки.
**Связь:** REQ-UI-03/09, AS-UI-14; HTTP §9.3 и AS-HTTP-24.
**Severity:** N/A — поведение реализации не проверялось.
**Priority:** P2, PROPOSED — отсутствие ответа не доказывает отсутствие сохранённой карты.
**Blocks:** больше не блокирует recovery-контракт; будущая проверка реализации остаётся обязательной.
**Статус:** RESOLVED IN CONTRACT — ACCEPTED RISK.
**Обоснование статуса:** на `082c6b9` REQ-UI-09 и AS-UI-23 @ `ce25dd0`
сверены с принятым DP-UI-09. Есть исходы commit/no commit/in progress, отказ сверки,
отдельный ручной повтор и позитивные контроли. Поздний commit первой задачи остаётся
принятым риском. Серверные tests и промт 05 дают основу setup; UI evidence ещё отсутствует.

- **Воспроизведение контрпримера:** принять валидный POST; управляемо разорвать соединение
  до commit либо во время защищённого commit. Во втором случае сервер может сохранить карту,
  хотя браузер не получил HTTP response и Retry-After.
- **Фактически в документах:** code-specific recovery не определяет этот вход;
  серверный сценарий HTTP §9.3 прямо допускает завершение commit после disconnect.
- **Ожидается:** Analyst задаёт сообщение, сохранение черновика, безопасную последовательность
  сверки, условие разрешения нового явного POST и отсутствие автоматического второго POST.
  Tester не выбирает недостающую семантику вместо Analyst.
- **Позитивный контроль:** в варианте с состоявшимся commit bootstrap/current показывают
  сохранённую карту; в варианте без commit проверяется исходное состояние после управляемого
  завершения работы или restart. Event/barrier управляют порядком, sleep не доказывает его.
- **Существующая основа:** `tests/http_api/test_lifecycle.py::test_disconnect_before_commit_cancels_without_sqlite_mutation`
  и `tests/http_api/test_lifecycle.py::test_disconnect_during_protected_commit_is_visible_after_restart`
  проверяют серверную сторону, но не действия браузера; в этом review они не запускались.
- **Условие закрытия:** оба варианта имеют однозначный UI expected result и управляемый setup;
  Tester сверил дополненный контракт. Исполняемое UI evidence требуется после реализации.

<a id="test-find-ui-003"></a>
### TEST-FIND-UI-003. Не зафиксирован oracle форматирования орбиса

**Тип:** testability clarification.
**Owner:** Developer — техническое правило форматирования; Analyst — ожидаемые примеры.
**Связь:** REQ-UI-04/06; AS-UI-07/08.
**Severity:** N/A — дефект отображения не воспроизводился.
**Priority:** P3, PROPOSED — уточнить до точных assertions табличного текста.
**Blocks:** больше не блокирует выбор expected strings; исполняемая проверка renderer ещё требуется.
**Статус:** RESOLVED IN CONTRACT.
**Обоснование статуса:** на `082c6b9` REQ-UI-04 / AS-UI-07 фиксируют ближайшую целую
минуту, точную половину вверх и перенос через 60 минут. Промт 04 и план Developer
используют это правило без изменения orb/type/category DTO. Production renderer не создан,
его исполняемые проверки ещё требуются.

- **Различающий пример:** для `orb=0.999` усечение даёт `0°59′`, округление до ближайшей
  минуты — `1°00′`. Из действующей формулировки нельзя выбрать единственный expected string.
- **Ожидается:** Developer фиксирует правило и примеры, включая переход через 60 минут;
  Analyst отражает их в сценариях. Это уточнение форматирования, не разрешение менять числа API.
- **Позитивный контроль:** орбис с целым числом минут отображается по тому же правилу;
  `category` всегда берётся из DTO, даже когда округлённый текст пересекает границу категории.
- **Условие закрытия:** Tester получает правило и expected strings для обычного значения,
  нулевого орбиса и обеих сторон границы округления.

## Сценарии и план оценки покрытия: повторная сверка

Таблица учитывает все требования review scope и перечисляет планируемое evidence.
Это не итоговая матрица выполненных тестов: у всех UI-проверок результат NOT RUN;
наличие API-теста не означает достаточного покрытия браузерного требования.

| Требование | Сценарии и классы данных | Ожидаемый результат / oracle | Уровень и планируемое evidence | Пробел и Owner |
|---|---|---|---|---|
| REQ-UI-01 | AS-UI-01/10/11: empty, ready, stale, unavailable; reload/foreground | bootstrap перед current; экран определяется GET; чтение не строит карту | Integration/API, browser HTTPS/cookie/network; `test_session.py::test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation` | Нет UI evidence — Developer/Tester |
| REQ-UI-02 | AS-UI-02/04–06/18: 2→3→4→2, поздний ответ после очистки; одноимённые места; gap/fold; 00:00/23:59/24:00 | актуальные подсказки, отдельный place_id, неверный ввод не отправляет build, известное время не превращается в null | Управляемый UI timer/network, real catalog fixtures, browser keyboard/mouse | Нужны независимые UI cases и валидный контроль после отказа — Tester |
| REQ-UI-03 | AS-UI-03/06/12–14/17/20–23: валидный build, invalid date/ID, снятый gate, double click, действия результата, потеря ответа | один POST с тремя полями после явного действия; IssueDTO связан с полями; чат неактивен, подробности той же identity | UI network/DOM, HTTP integration, журнал по request/run ID; промты 03/04/05 | TEST-FIND-UI-001/002 resolved in contract; UI evidence — Developer/Tester |
| REQ-UI-04 | AS-UI-07–09/15/22: degree=0/29, minute=0/59, обе ретроградности, null/[], изменение только longitude, half-up/carry orb | опубликованные позиции и категории; REQ-UI-04 oracle; нет пересчёта по longitude или demo-чисел | UI DTO fixtures/DOM, API golden; `test_projectors.py::test_chart_dto_exact_golden_and_no_internal_fields`; промт 04 | TEST-FIND-UI-003 resolved in contract; отображение ещё не проверено — Developer/Tester |
| REQ-UI-05 | AS-UI-07–09/15: полный natal, cosmogram, отсутствующая опубликованная точка | порядок точек, 12 домов по номеру; null не заменён техническими домами | Golden/renderer, POST/current parity; `test_projectors.py::test_all_published_point_ids_have_fixed_order_and_12_sign_dictionary` | Нужны UI assertions для обеих разновидностей карты — Tester |
| REQ-UI-06 | AS-UI-07–09/15/16: exact/working/background, пустой полный список, устойчивые и исключённые пары | все опубликованные аспекты доступны; исключённые пары не восстановлены; категория не меняется из-за округления | API/renderer, browser reader; `test_projectors.py::test_cosmogram_excluded_aspects_remain_private`; промт 04 | Oracle определён; UI reader evidence — Developer/Tester |
| REQ-UI-07 | AS-UI-19: работающий reader и обновлённый макет | работающий UI не имитирует будущие группы; композиция макета проверяется отдельно | DOM negative assertion с положительным контролем трёх групп; визуальная сверка макета | Нет UI/обновлённого макета для сверки — Developer/UI/UX/Tester |
| REQ-UI-08 | AS-UI-10/11/12: restart, stale, safe unavailable, потерянная сессия | та же карта из current, явный rebuild, отсутствие выдуманных домов/offset | Real SQLite restart + browser; `test_session.py::test_restart_uses_same_sqlite_file_with_new_runtime_and_empty_cache` | UI restore evidence отсутствует — Tester |
| REQ-UI-09 | AS-UI-12–14/16/18/23: 409/429/503/504, два intent, disconnect до/во время commit, отказ сверки и ручной повтор | code-specific безопасная сверка, сохранение черновика, отсутствие auto POST; при успешном old/empty разрешён отдельный ручной POST по DP-UI-09 | Barrier/Event/fake clock, новые runtime, browser network с позитивным явным build; промт 05 | TEST-FIND-UI-002 resolved in contract с accepted risk; UI integration evidence — Developer/Tester |
| REQ-UI-10 | AS-UI-02/07/19/22: клавиатура, ошибки/загрузка, длинные таблицы, действия результата; 360/768/1440 px | доступные подписи/ошибки/focus; все три группы читаемы без скролла страницы; подробности активны, чат различимо неактивен | Browser/manual/визуальные снимки на точном implemented commit; промты 04/06 | TEST-FIND-UI-001 resolved in contract; accessibility/visual evidence отсутствует — Developer/Tester |

В ссылках на существующие tests выше `test_session.py` и `test_projectors.py` находятся
в [tests/http_api](../../../tests/http_api/). Assertions выбранных тестов прочитаны,
но запуск и исчерпывающий аудит всего набора M1-6 не выполнялись.

**Вывод о достаточности:** документная прослеживаемость охватывает все REQ-UI-01…10;
для функциональной приёмки каждого требования ещё нужно UI evidence. Сценарии действий
после build и потери ответа, а также oracle орбиса теперь определены и сверены Tester.
Повторять достаточные серверные тесты отдельными дублирующими unit-тестами не требуется;
нужен новый проверяемый браузерный путь, его границы и реальные межкомпонентные проверки.

## Оценка тестирования

**Диапазон:** 3–5 рабочих дней собственной работы Tester после согласования требований
и передачи готовой реализации. **Уверенность:** средняя-низкая.

| Работа | Рабочие дни |
|---|---|
| План/fixtures/oracle и подготовка среды | 0,5–1 |
| Автоматические UI-проверки и аудит reuse | 0,75–1,25 |
| Integration, browser HTTPS/cookie/recovery | 0,75–1,25 |
| Клавиатурные и визуальные проверки 360/768/1440 px | 0,5–0,75 |
| Один цикл retest и оформление evidence | 0,5–0,75 |

Допущения: существующие API/goldens переиспользуются; есть управляемые timer/network швы,
стабильный HTTPS-стенд и возможность контролировать SQLite/restart. Исправление дефектов,
дополнительные циклы retest и ожидание решений не входят в диапазон. Главная неопределённость —
доступность обычного browser HTTPS пути с известным ограничением стенда и воспроизводимость
управляемых browser recovery проверок. Developer выбрал native ES modules и Node state tests;
реальный DOM/keyboard/cookie подтверждается отдельными браузерными проверками.
Исторический target Testing 2 дня не покрывал этот диапазон. Текущий budget Testing 5
принят владельцем в DP-UI-07; estimate Tester 3–5 и средняя-низкая уверенность сохраняются.
Календарь/зависимости — в Manager Change Plan.

## Выполненные проверки и ограничения

### Первичное ревью @ `9ae1abc`

- На `9ae1abc` проверены 44 локальные Markdown-ссылки на файлы четырёх review-документов:
  отсутствующих целей нет. HTML-якоря в предыдущем проходе не проверялись.
- Найдены 10 уникальных REQ-UI и 21 уникальный AS-UI; все требования есть в таблице сценариев.
- `git diff --check 652bd734 HEAD -- docs/requirements/changes/ui-birth-form-and-facts docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md docs/project_management/roadmap.md` — exit 0.
- При подготовке отчёта PowerShell-проверка разрешила все 15 локальных ссылок и явных якорей,
  проверила наличие 7 упомянутых test functions и 10 строк требований. Отсутствующих целей нет.
- Проверки whitespace и состава staged diff выполняются перед коммитом;
  фактические команды и результат сохранения фиксируются в commit handoff.
- `pytest`, browser HTTPS/cookie, визуальная приёмка и платные/сетевые smoke не запускались:
  задача ограничена документным review и его сохранением.
- Чистовая редакция UI в `current/` не представлена для acceptance-сверки.
- DEBT-UI-001, FIND-TEST-HTTP-001 и PARTIAL M1-6 сохраняются как известные обязательства;
  они не объявляются новыми багами этого review. Manager/Analyst документы и production code не изменены.

### Повторная сверка @ `082c6b9`

- `git merge --ff-only 082c6b9ac5c8b054c38de5f17bc673956ec058d8` — exit 0,
  ветка Tester обновлена с `81624f8`; конфликтов и merge-коммита нет.
- PowerShell-проверка 13 документов review-пакета — PASS: **249 локальных ссылок,
  159 якорей**, 10 REQ, 23 AS; все требования представлены в таблице сценариев.
  Эти числа относятся к пакету до сохранения повторного вердикта в этом файле.
- Все шесть промтов содержат DRAFT / NOT EXECUTED и условие G3; их REQ/AS,
  expected results, разрешённые файлы, подход и проверки прочитаны.
- Проверены ссылки на существующие серверные disconnect/commit/timeout test functions.
  Наличие этих функций не выдаётся за запуск тестов.
- Арифметика шести work items Developer — PASS: база 4,5–7,5 дня / 36–60 часов;
  резерв 0,5 дня / 4 часа; итог 5–8 дней / 40–64 часа. Tester work не включена в эту сумму.
- `git diff --check 81624f8 HEAD` и `git show --check --oneline HEAD` — exit 0
  при HEAD `082c6b9`; staged diff нового отчёта проверяется отдельно перед его коммитом.
- `git diff --name-only 652bd734 HEAD -- src tests pyproject.toml` — пустой вывод;
  Developer planning commit не содержит production реализации.
- На этом этапе `pytest`, Node runtime tests, browser HTTPS/cookie/mobile и исполнение
  промтов не выполнялись. Числа 27/339 passed и 7 cases из Developer-плана — его evidence
  на указанном там baseline, а не результаты запуска Tester.
- Перед сохранением повторного отчёта проверены его 17 локальных ссылок, явный якорь,
  7 упомянутых test functions, 10 строк требований и три статуса RESOLVED IN CONTRACT;
  отсутствующих целей и несогласованности статусов не найдено. `git diff --check` — exit 0.

**Readiness recommendation исторической консультации:** TESTABLE сохраняется как авторский verdict консультации.
Прежние TEST-FIND-UI-001…003 сняты на уровне контракта, estimate Tester 3–5 дней подтверждён.
Текущий execution input — `0c893f0`; Manager подтвердил G4 и передал change в READY_FOR_TEST.
Финальная приёмка не выполнялась: нужны actual UI/browser results, retest TEST-FIND-UI-004…012,
учёт DEBT-CALC-001 и сверка чистовой редакции.

<a id="tester-orb-fix-retest"></a>
## Независимая регрессия и retest TEST-FIND-UI-013 — 2026-10-08

**Роль:** Tester. **Проверенный commit:** `6f44404e6ba9e9f1eb8a529978b5e076d8af1bf2` (merge PR #54).
**Исправление Developer:** `a576253c4e132498ae394c67237a6f29d3e0c4ee`; ветка Tester обновлена с `f23ed53` через `git merge --ff-only 6f44404e6ba9e9f1eb8a529978b5e076d8af1bf2`, exit 0.
**Статус:** **PASS** для выполненной регрессии и закрытия [TEST-FIND-UI-013](manual-test-bugs.md#test-find-ui-013).
**Обоснование статуса:** исходный failing case теперь проходит; ближайшие значения ниже/выше половины различаются, перенос минуты сохранён. Assertions настоящего mounted UI подтверждают текст, category, неизменность source/snapshot DTO и отсутствие дополнительных запросов. Все перечисленные регрессионные команды дали exit 0, кроме отсутствующих запусков, явно указанных ниже; единственное исключение полного pytest — согласованный DEBT-CALC-001.
**Область:** REQ-UI-04 / AS-UI-07, связанные представления аспектов REQ-UI-06, существующий UI-набор M1-7 и HTTP/архитектурная/полная Python регрессия. Это отдельное evidence retest, а не PASS всех browser acceptance scenarios.
**Requirements baseline:** нормативный HTTP/backend @ `652bd734`, утверждённая семантика 10 REQ / 23 AS @ `ce25dd0`; [requirements.md](../../requirements/changes/ui-birth-form-and-facts/requirements.md) и [scenarios.md](../../requirements/changes/ui-birth-form-and-facts/scenarios.md) на tested commit сохраняют правило half-up.
**Реестр решений:** [DP-UI-01…09 и долги](../../project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register) @ `6f44404`; решения не изменены.
**Окружение:** Windows / PowerShell, Node.js v24.19.0, Python 3.14.0. Actual runtime checks выполнены на чистом tracked-дереве; после них изменены только Tester evidence и bug registry. Для installed-wheel checks разрешён доступ к временным файлам pip. Стенд не запускался и не перезапускался, браузер в этом раунде не использовался.

### Фактические команды

| Команда из корня checkout | Результат Tester |
|---|---|
| Исходный PowerShell here-string из [карточки бага](manual-test-bugs.md#test-find-ui-013), извлечённый и переданный `node --input-type=module` | **4 passed / 0 failed**, exit 0; actual/expected `1°02′`. |
| `node --test --test-isolation=none tests/ui/facts.test.mjs` | **32 passed / 0 failed / 0 skipped**, exit 0, 168.53 ms. |
| `node --test --test-isolation=none tests/ui/*.test.mjs` | **188 passed / 0 failed / 0 skipped**, exit 0, 319.88 ms. |
| `python -X utf8 -B -m pytest -p no:cacheprovider tests/http_api tests/test_module_boundaries.py -q` | **346 passed**, exit 0, 25.68 s; includes installed-wheel delivery вне checkout. |
| `python -X utf8 -B -m pytest -p no:cacheprovider -q -rs` | **2959 passed / 1 skipped**, exit 0, 148.35 s; skip только `test_property_configuration_count_does_not_grow_when_threshold_decreases` по DEBT-CALC-001. |
| Дополнительный `node --input-type=module`, integer oracle ниже | **180 001 values PASS**, exit 0; диапазон диагностический, API не меняется. |
| `git diff --check f23ed53 HEAD`; `git status --short` перед сохранением evidence | exit 0; tracked-дерево чистое. |

Наборы пересекаются, числа не суммируются. Порядок проверки: исходное воспроизведение / целевые facts → весь UI и связанные HTTP/архитектурные → полный pytest.

### Матрица покрытия retest

| Требование / сценарий | Данные и expected result | Конкретная проверка | Покрытие / запуск |
|---|---|---|---|
| REQ-UI-04 / AS-UI-07 | `1.025` → `1°02′`; ближайший Number ниже → `1°01′`, сверху → `1°02′` | [facts.test.mjs](../../../tests/ui/facts.test.mjs), cases `REQ-UI-04 orb 1.025 rounds half-up with minute carry to 1°02′`, `1.0249999999999997`, `1.0250000000000001` в той же параметризации | SUFFICIENT для найденной границы / PASS |
| REQ-UI-04 / AS-UI-07 | Обычные значения, ноль, прежние половины; `0.999` и `59.5/60` переносят минуту в `1°00′` | Та же параметризация `REQ-UI-04 orb ${orb} rounds half-up with minute carry to ${expected}`; explicit expected strings, независимое воспроизведение с тремя контролями | SUFFICIENT / PASS |
| REQ-UI-04/06 / AS-UI-07 | Валидный current, непустая строка с `1°02′`; category остаётся «Точный», DTO/calls неизменны | `REQ-UI-04 / AS-UI-07 / TEST-FIND-UI-013: mounted current orb 1.025 rounds half-up without changing DTO or requests` | SUFFICIENT для интеграции formatter/renderer / PASS |
| REQ-UI-04–06 / AS-UI-07–09/22 | Натал/космограмма, опубликованные позиции и полный список аспектов, null/empty, POST/current и открытие подробностей без POST | Existing facts suite: `all aspect rows retain endpoint/type/category and DTO order without recalculation`, `cosmogram displays only published points/stable aspects and inapplicable houses`, `empty calculated aspects are distinct from missing/unavailable chart`, `AS-UI-22 natal/cosmogram: build and reload details show the same identity/facts without chat or extra requests` | SUFFICIENT на этом UI integration уровне / PASS |
| REQ-UI-01…10, существующие регрессионные сценарии | Сохранить форму, места, сессию, recovery и DTO после локальной смены formatter | `tests/ui/*.test.mjs`; HTTP/module-boundary и полный pytest по командам выше | PASS выполненных наборов; это не замена live-browser coverage всех 23 AS |
| REQ-UI-10 / AS-UI-19 и управляемый live-browser retest | HTTPS/browser/layout/keyboard на новой версии | В этом раунде NOT RUN; прежний browser run не переносится на новый commit | PARTIAL для полной acceptance / NOT RUN |
| DEBT-CALC-001 | Монотонность расчётных конфигураций | Прежний согласованный property-test skip | EXCLUDED / NOT RUN; долг OPEN, решение не менялось |

Дополнительный integer oracle не повторяет production half-boundary comparison; expected вычисляется из целого числа тысячных долей:

```powershell
@'
import assert from 'node:assert/strict';
import {formatOrb} from './src/exact_orb/http_api/ui/facts.mjs';
for (let units = 0; units <= 180000; units++) {
  const minute = Math.floor((units * 120 + 1000) / 2000);
  const expected = `${Math.floor(minute / 60)}°${String(minute % 60).padStart(2, '0')}′`;
  assert.equal(formatOrb(units / 1000), expected, `orb=${units}/1000`);
}
console.log('180001 values PASS');
'@ | node --input-type=module
```

### Вывод и handoff

TEST-FIND-UI-013 **CLOSED**: воспроизведение исправлено на фактически проверенном commit, чувствительный regression проверяет наблюдаемый текст и реальные UI-компоненты, ближайшие соседние значения и прежние случаи сохранены. Дополнительный дублирующий тест для этого дефекта Tester не добавлял: новое Developer coverage достаточно для сформулированного условия закрытия.

**Readiness recommendation:** bug fix и выполненная автоматическая регрессия PASS; **общий M1-7 ещё не READY_FOR_FINAL_ACCEPTANCE**. Live browser/error/recovery acceptance и окончательный retest остальных findings остаются отдельными обязательствами; чистовая редакция `current/ui/` и карта переноса Analyst не представлены для сверки. DEBT-CALC-001, DEBT-UI-001, DP-UI-03 и принятый риск позднего commit DP-UI-09 не закрываются этим результатом. Production code, Developer tests, Manager/Analyst decisions и historical prompts Tester не изменены; commit/push/PR в этом поручении не выполнялись.
