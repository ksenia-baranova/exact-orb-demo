# Tester: ревью документов ui-birth-form-and-facts

**Роль:** Tester. **Дата:** 2026-10-06.
**Ветка:** `test/ui-birth-form-and-facts-review`.
**Проверенный baseline документов:** `9ae1abc71e6876d5440f20541996f489a387e1cb`.
**Область:** ревью документов Manager и Functional Analyst, testability consultation.
**Статус:** TESTABLE WITH CLARIFICATIONS.
**Обоснование статуса:** основной поток трёх групп фактов имеет наблюдаемые ответы и состояния;
все 10 требований связаны с 21 сценарием. TEST-FIND-UI-001 требует переноса принятого состава
действий в Analyst-контракт, TEST-FIND-UI-002 — сценариев потери ответа POST,
TEST-FIND-UI-003 — точного правила отображения орбиса. Исполняемые UI-проверки не выполнялись;
это заключение о документах, не acceptance evidence реализации. Следующий шаг — уточнения
Analyst/Developer и согласование G2 Manager.

## Baselines и источники

- Исходный нормативный baseline — `652bd73405db0a0611e98e81af6f3f668dd429f6`:
  [HTTP API](../../requirements/http_api.md) §§4–9, 13;
  [каталог мест](../../requirements/component_responsibilities/exact-orb_place_catalog.md);
  [Build Natal](../../requirements/component_responsibilities/exact-orb_build_natal_components.md);
  [сессия](../../requirements/component_responsibilities/exact-orb_session_requirements.md);
  [сохранённая карта](../../requirements/session/stored-chart-session-behavior.md);
  ADR-0008, 0029–0034, 0039–0041.
- Черновая Analyst-редакция — `dbee8880ae00f65aac7660936e69b906900ae216`:
  [requirements.md](../../requirements/changes/ui-birth-form-and-facts/requirements.md),
  [scenarios.md](../../requirements/changes/ui-birth-form-and-facts/scenarios.md),
  [analysis.md](../../requirements/changes/ui-birth-form-and-facts/analysis.md).
- Manager-редакция и единый реестр — `ad8892fd7ed8bd3f0998202c32bbcc05f31020f9`:
  [artifacts.md](../../project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register),
  [roadmap.md](../../project_management/roadmap.md).
- Общий review HEAD `9ae1abc` содержит обе редакции: merge PR #44 — `ea0678d`,
  merge PR #43 — `9ae1abc`. Исторические входные commits авторов не подменяются этим HEAD;
  факт интеграции не означает утверждения требований или готовности к разработке.
- Применены [Tester skill](../../development_approach/skills/tester/SKILL.md),
  [процесс](../../development_approach/process.md),
  [ownership](../../development_approach/roles.md) и
  [шаблон Tester](../../development_approach/artifacts/tester.md).

## Вывод для Manager

Ключевой незавершённый возврат — согласование интегрированного Analyst-контракта с текущим
реестром. Manager уже перечислил необходимые изменения Analyst в задании роли; первое
замечание ниже фиксирует их невыполнение на review HEAD, не создаёт новый продуктовый выбор.
Исторические формулировки Analyst об открытых DP-UI-02/04/05 нужно сверить с актуальным реестром.
Неопределённые результаты потери соединения требуют отдельного UI recovery-сценария.

Независимая подготовка fixtures, проверок API и сценариев формы может продолжаться.
Этот отчёт не завершает G2 и не меняет статус change.

**Связанные решения:** DP-UI-01…08.
**Обновления реестра:** не выполнены. Пользователь поручил ревью и последующее сохранение
его результата коммитом; документы Manager/Analyst и строки решений не изменялись.
Manager получает findings и estimate из этого отчёта для собственного alignment.

## Замечания

Все замечания относятся к документам и основаниям проверки. Подтверждённых багов реализации
в этом review нет; Severity — N/A. Priority предложен Tester и не подтверждён Manager.

<a id="test-find-ui-001"></a>
### TEST-FIND-UI-001. Состав действий не перенесён в Analyst-контракт

**Тип:** requirement/source alignment gap; существующий возврат Analyst.
**Owner:** Functional Analyst.
**Связь:** DP-UI-05; REQ-UI-03, REQ-UI-10; AS-UI-03, AS-UI-07, AS-UI-19.
**Severity:** N/A — ревью требований, не баг реализации.
**Priority:** P2, PROPOSED — согласовать до завершения G2 и допуска соответствующего UI work item.
**Blocks:** подтверждение согласованного контракта экрана готовности и его полных acceptance criteria.
**Статус:** OPEN.
**Обоснование статуса:** на `9ae1abc` решение есть в реестре, но требование и сценарий двух действий
не представлены; нужна новая согласованная редакция Analyst и повторная сверка Tester.

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
**Blocks:** подтверждение полноты recovery-контракта и последующая проверка потери ответа.
**Статус:** OPEN.
**Обоснование статуса:** REQ-UI-09/AS-UI-14 перечисляют полученные HTTP 503/504;
ожидаемые действия браузера при отсутствии ответа не определены. Требуется уточнение Analyst.

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
**Blocks:** точную проверку отображения орбиса; независимые работы не блокирует.
**Статус:** OPEN.
**Обоснование статуса:** REQ-UI-04 разрешает единообразное форматирование градусов/минут,
но правило округления и граничные expected strings не записаны; нужен воспроизводимый oracle.

- **Различающий пример:** для `orb=0.999` усечение даёт `0°59′`, округление до ближайшей
  минуты — `1°00′`. Из действующей формулировки нельзя выбрать единственный expected string.
- **Ожидается:** Developer фиксирует правило и примеры, включая переход через 60 минут;
  Analyst отражает их в сценариях. Это уточнение форматирования, не разрешение менять числа API.
- **Позитивный контроль:** орбис с целым числом минут отображается по тому же правилу;
  `category` всегда берётся из DTO, даже когда округлённый текст пересекает границу категории.
- **Условие закрытия:** Tester получает правило и expected strings для обычного значения,
  нулевого орбиса и обеих сторон границы округления.

## Сценарии и план оценки покрытия

Таблица учитывает все требования review scope и перечисляет планируемое evidence.
Это не итоговая матрица выполненных тестов: у всех UI-проверок результат NOT RUN;
наличие API-теста не означает достаточного покрытия браузерного требования.

| Требование | Сценарии и классы данных | Ожидаемый результат / oracle | Уровень и планируемое evidence | Пробел и Owner |
|---|---|---|---|---|
| REQ-UI-01 | AS-UI-01/10/11: empty, ready, stale, unavailable; reload/foreground | bootstrap перед current; экран определяется GET; чтение не строит карту | Integration/API, browser HTTPS/cookie/network; `test_session.py::test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation` | Нет UI evidence — Developer/Tester |
| REQ-UI-02 | AS-UI-02/04–06/18: 2→3→4→2, поздний ответ после очистки; одноимённые места; gap/fold; 00:00/23:59/24:00 | актуальные подсказки, отдельный place_id, неверный ввод не отправляет build, известное время не превращается в null | Управляемый UI timer/network, real catalog fixtures, browser keyboard/mouse | Нужны независимые UI cases и валидный контроль после отказа — Tester |
| REQ-UI-03 | AS-UI-03/06/12–14/17/20/21: валидный build, invalid date/ID, снятый gate, double click | один POST с тремя полями после явного действия; IssueDTO связан с полями | UI network/DOM, HTTP integration, журнал по request/run ID | TEST-FIND-UI-001/002 — Analyst; UI evidence — Tester |
| REQ-UI-04 | AS-UI-07–09/15: degree=0/29, minute=0/59, обе ретроградности, null/[], изменение только longitude | опубликованные позиции и категории; нет пересчёта по longitude или demo-чисел | UI DTO fixtures/DOM, API golden; `test_projectors.py::test_chart_dto_exact_golden_and_no_internal_fields` | TEST-FIND-UI-003; отображение ещё не проверено — Developer/Analyst/Tester |
| REQ-UI-05 | AS-UI-07–09/15: полный natal, cosmogram, отсутствующая опубликованная точка | порядок точек, 12 домов по номеру; null не заменён техническими домами | Golden/renderer, POST/current parity; `test_projectors.py::test_all_published_point_ids_have_fixed_order_and_12_sign_dictionary` | Нужны UI assertions для обеих разновидностей карты — Tester |
| REQ-UI-06 | AS-UI-07–09/15/16: exact/working/background, пустой полный список, устойчивые и исключённые пары | все опубликованные аспекты доступны; исключённые пары не восстановлены | API/renderer, browser reader; `test_projectors.py::test_cosmogram_excluded_aspects_remain_private` | TEST-FIND-UI-003 и UI reader evidence — Developer/Analyst/Tester |
| REQ-UI-07 | AS-UI-19: работающий reader и обновлённый макет | работающий UI не имитирует будущие группы; композиция макета проверяется отдельно | DOM negative assertion с положительным контролем трёх групп; визуальная сверка макета | Нет UI/обновлённого макета для сверки — Developer/UI/UX/Tester |
| REQ-UI-08 | AS-UI-10/11/12: restart, stale, safe unavailable, потерянная сессия | та же карта из current, явный rebuild, отсутствие выдуманных домов/offset | Real SQLite restart + browser; `test_session.py::test_restart_uses_same_sqlite_file_with_new_runtime_and_empty_cache` | UI restore evidence отсутствует — Tester |
| REQ-UI-09 | AS-UI-12–14/16/18: 409/429/503/504, два intent, disconnect до/во время commit | code-specific безопасная сверка, сохранение черновика, отсутствие auto POST; для disconnect oracle уточняется | Barrier/Event/fake clock, новые runtime, browser network с позитивным явным build | TEST-FIND-UI-002 — Analyst; UI integration evidence — Tester |
| REQ-UI-10 | AS-UI-02/07/19: клавиатура, ошибки/загрузка, длинные таблицы; 360/768/1440 px | доступные подписи/ошибки/focus; все три группы читаемы без скролла страницы | Browser/manual/визуальные снимки на точном implemented commit | TEST-FIND-UI-001; accessibility/visual evidence отсутствует — Analyst/Tester |

В ссылках на существующие tests выше `test_session.py` и `test_projectors.py` находятся
в [tests/http_api](../../../tests/http_api/). Assertions выбранных тестов прочитаны,
но запуск и исчерпывающий аудит всего набора M1-6 не выполнялись.

**Вывод о достаточности:** документная прослеживаемость охватывает все REQ-UI-01…10;
для функциональной приёмки каждого требования ещё нужно UI evidence. Сценарии действия
после build и потери ответа требуют уточнений, точный текст орбиса — oracle.
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
невыбранный UI/test stack и доступность обычного browser HTTPS пути с известным ограничением стенда.
Target DP-UI-07 сам по себе не является оценкой; два дня недостаточно закладывать как
подтверждённую длительность всего перечисленного объёма. Календарь и критический путь сводит Manager.

## Выполненные проверки и ограничения

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

**Readiness recommendation:** TESTABLE WITH CLARIFICATIONS для consultation.
Финальная приёмка не выполнялась; необходимы согласованный контракт, implemented commit,
реальные проверки UI и последующая сверка чистовой редакции.
