# Tester: ревью документов ui-birth-form-and-facts

**Роль:** Tester. **Дата:** 2026-10-06.
**Ветка:** `test/ui-birth-form-and-facts-review`.
**Проверенный baseline документов:** `082c6b9ac5c8b054c38de5f17bc673956ec058d8`.
**Область:** повторное ревью артефакта Manager, исправленного Analyst-контракта,
Implementation Plan и шести промтов Developer; testability consultation.
**Статус:** TESTABLE.
**Обоснование статуса:** все 10 требований связаны с 23 сценариями; TEST-FIND-UI-001…003
устранены на уровне контракта. Промты предусматривают наблюдаемые expected results,
управляемые timer/network швы и позитивные контроли. Существенных новых блокеров
тестируемости не найдено. Исполняемые UI-проверки не выполнялись; это заключение
о документах, не acceptance evidence реализации. Следующий шаг — Manager alignment
оценок, зависимостей и G3; промты остаются DRAFT / NOT EXECUTED.

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

Manager `artifacts.md` §§«Черновое описание»/«Плановый бюджет» ещё сообщает об отсутствии
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
Target DP-UI-07 сам по себе не является оценкой; два дня недостаточно закладывать как
подтверждённую длительность всего перечисленного объёма. Календарь и критический путь сводит Manager.

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

**Readiness recommendation:** TESTABLE для consultation и Manager alignment.
Прежние TEST-FIND-UI-001…003 сняты на уровне контракта, estimate Tester 3–5 дней подтверждён.
Допуск промтов требует актуализации Manager-плана и G3. Финальная приёмка не выполнялась;
implemented commit, реальные UI проверки и сверка чистовой редакции ещё необходимы.
