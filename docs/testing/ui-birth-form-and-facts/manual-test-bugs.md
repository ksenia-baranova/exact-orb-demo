# Баги UI: ручное тестирование и независимое ревью

**Change:** `ui-birth-form-and-facts`. **Дата начала реестра:** 2026-10-07.
**Текущий retest Tester — 2026-10-08:** exact commit `a8b45dbbda5378e598eb75b15f81e1445a75020e`, реальный HTTPS / Chromium 154. TEST-FIND-UI-004…012 **CLOSED**, 013 остаётся **CLOSED**; фактические controls и границы — [ниже](#tester-full-retest-a8b45db). Общий verdict **REVORK** из-за native foreground NOT RUN и отсутствующей чистовой редакции Analyst для G5, не из-за этих закрытых bugs. [Acceptance matrix](acceptance-a8b45db.md).
**Источник наблюдений:** ручные проверки пользователя на локальном стенде, ревью другой модели, переданное владельцем 2026-10-07, и независимое ревью Tester 2026-10-08. Источник и предел подтверждения указаны в каждой записи.
**Developer handoff — 2026-10-08:** исправления TEST-FIND-UI-004…012 интегрированы в Developer package PR #51 / `0c893f0`; на момент передачи все записи имели FIXED PENDING RETEST, independent results NOT RUN. Manager подтвердил G4 и READY_FOR_TEST; DEBT-CALC-001 остаётся OPEN / NON-BLOCKING для M1-7.
**Первичная находка Tester — 2026-10-08:** на `1af6e45` независимо воспроизведён TEST-FIND-UI-013, статус на момент регистрации OPEN. Существующий UI-набор дал 180 passed; дополнительная проверка границы округления — 3 passed / 1 failed. Исходное evidence сохранено ниже.
**Исправление Developer — 2026-10-08:** TEST-FIND-UI-013 исправлен в DEV-UI-09 поверх `84410f1`, **FIXED PENDING RETEST**. Target RED 30 passed / 2 failed → GREEN 32 passed, весь UI 188 passed, полный pytest 2959 passed / 1 skipped. По отдельному поручению владельца исправление, tests, промт и документы включаются в один коммит передачи; версия для Tester — коммит с этой редакцией. Независимый retest/browser evidence NOT RUN; [Developer handoff](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-09-execution). Исходная находка Tester и её evidence сохранены.
**Независимый retest Tester — 2026-10-08:** исправление `a576253` проверено на общем `6f44404`, TEST-FIND-UI-013 **CLOSED**. Исходная команда — 4 passed; facts — 32 passed; UI — 188 passed; HTTP/границы модулей — 346 passed; полный pytest — 2959 passed / 1 skipped (прежний DEBT-CALC-001). [Отчёт и матрица Tester](tester.md#tester-orb-fix-retest). Остальные findings и общий acceptance status этим retest не закрываются.
**Регистрация:** Developer — TEST-FIND-UI-004…012; Tester — TEST-FIND-UI-013, по прямому поручению пользователя.

Реестр использует общую нумерацию `TEST-FIND-UI-*`: номера 001–003 относятся к ранее выполненному ревью документов в [Tester-артефакте](tester.md). Здесь фиксируются наблюдения реализации. Запись об исправлении Developer не означает успешный ручной retest или независимую Tester acceptance. Severity 004…013 назначена Tester после независимой проверки; исторические оценки Developer сохранены в описании происхождения. Priority остаётся PROPOSED и подтверждается Change Manager по [шаблону дефекта](../../development_approach/artifacts/tester.md#3-дефект-или-замечание-тестирования-defect-or-test-finding).

| ID | Дефект | Severity | Priority | Состояние исправления | Ручной retest |
|---|---|---|---|---|---|
| [TEST-FIND-UI-004](#test-find-ui-004) | Ввод `0045` не отображается как `00:45` | S3, Tester | P3, PROPOSED | CLOSED; DEV-UI-03 | PASS @ a8b45db: typing/paste/edit/toggle/API |
| [TEST-FIND-UI-005](#test-find-ui-005) | Допустимый `admin1_name:null` ломает всю выдачу мест | S2, Tester | P2, PROPOSED | CLOSED; DEV-UI-07 | PASS: real Hong Kong null region/select/build |
| [TEST-FIND-UI-006](#test-find-ui-006) | После неподтверждённого 5xx разрешён POST без сверки | S2, Tester | P2, PROPOSED | CLOSED; DEV-UI-08 | PASS: raw502/504, typed500, failed check/recovery/manual |
| [TEST-FIND-UI-007](#test-find-ui-007) | Устаревшая карта получает recovery-статус `matched` | S3, Tester | P2, PROPOSED | CLOSED; DEV-UI-08 | PASS: actual stale + fresh same-identity positive |
| [TEST-FIND-UI-008](#test-find-ui-008) | Нет объяснения повторного действия после восстановления сессии | S3, Tester | P3, PROPOSED | CLOSED; DEV-UI-08 | PASS: cookie expiry, visible message/manual positive |
| [TEST-FIND-UI-009](#test-find-ui-009) | Ресурсы с постоянными URL не имеют явной политики кэша | S2, Tester | P2, PROPOSED | CLOSED; DEV-UI-07 | PASS: no-cache200/304/wheel/browser reload |
| [TEST-FIND-UI-010](#test-find-ui-010) | После committed POST отсутствует сводка данных построенной карты | S3, Tester | P3, PROPOSED | CLOSED; DEV-UI-08 | PASS: known/unknown summary, pending draft edit |
| [TEST-FIND-UI-011](#test-find-ui-011) | Повреждённый успешный ответ вызывает исключение без сообщения UI | S2, Tester | P2, PROPOSED | CLOSED; DEV-UI-07 | PASS: malformed POST/current + valid safe read |
| [TEST-FIND-UI-012](#test-find-ui-012) | Фокус стирает подпись восстановленного места | S3, Tester | P3, PROPOSED | CLOSED; DEV-UI-08 | PASS: actual reload/focus/blur/edit/reselect |
| [TEST-FIND-UI-013](#test-find-ui-013) | Орбис на половине минуты округляется вниз | S3, Tester | P2, PROPOSED | CLOSED; DEV-UI-09 | Mounted PASS @6f44404; live DTO boundaries PASS @a8b45db |

<a id="test-find-ui-004"></a>
## TEST-FIND-UI-004. Поле времени не поддерживает формат при вводе цифр

**Тип:** баг реализации, удобство ввода формы.
**Обнаружил:** пользователь при ручном тестировании 2026-10-07.
**Ответственный за исправление:** Developer.
**Ответственный за retest:** пользователь или Tester; повторное подтверждение ещё не получено.
**Требования:** [REQ-UI-02](../../requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-02-дата-время-и-выбор-места), [REQ-UI-03](../../requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-03-явное-построение-и-валидация); формат API остаётся `HH:MM`. Ожидаемое форматирование четырёх введённых цифр уточнено текущим сообщением пользователя.
**Связанные сценарии:** [AS-UI-05](../../requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-05-пустое-или-противоречивое-время), [AS-UI-19](../../requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-19-доступность-и-узкий-экран).
**Baseline:** `ef75d77232e1f629540827bfd90e93c1c16977ea`, ветка `dev/ui-birth-form-and-facts-review`; наблюдение относится к локальной реализации DEV-UI-03 поверх этого HEAD. Исправление включено в единый коммит пакета DEV-UI-03 с этим baseline в качестве родителя, добавляющий настоящий реестр и regression checks. Для ручного retest нужно зафиксировать фактически проверяемый хеш из Git.
**Окружение наблюдения:** локальный HTTPS стенд `https://exact-orb.localhost/`, Windows. Версия браузера и размер экрана не зафиксированы.
**Severity:** **S3, PROPOSED Developer** — ограниченное нарушение удобства ввода; обходной путь — вручную поставить двоеточие. Нет подтверждённого искажения числового результата или сохранённых данных. Окончательная оценка Tester ожидается.
**Priority:** **P3, PROPOSED** — локальное исправление поведения поля; исправление уже подготовлено по сообщению пользователя. Подтверждение Change Manager ещё не получено.
**Blocks:** закрытие этого дефекта требует ручного retest; влияние на общий gate приёмки оценивает Tester. Проверки остальных сценариев можно продолжать.
**Статус:** **CLOSED** — independent browser retest @ `a8b45db`; [actual/expected и controls](#tester-full-retest-a8b45db). Исходное описание и Developer handoff ниже сохранены как история.

### Воспроизведение до исправления

1. Открыть локальную UI-страницу. Оставить «Точное время неизвестно» снятым, чтобы поле времени было доступно.
2. Ввести в «Время рождения» четыре цифры `0045` без двоеточия.
3. **Фактически:** на экране остаётся единая строка `0045`, формат времени не поддерживается при вводе.
4. **Ожидается:** поле показывает `00:45`; ведущий ноль сохраняется, дата/место и отметка неизвестности не меняются. При разрешённом явном build отправляется `birth_time:"00:45"`.

**Исходное свидетельство пользователя:** «в случае с вводом даты сохраняется формат но в случае с вводом времени формат не соблюдается 0045 - в единую строку».

Наблюдение относится к самому вводу. Ручная отправка build при этом сообщении не зафиксирована. По коду необработанная строка `0045` не проходит строгую проверку `HH:MM` перед отправкой.

### Причина, исправление и автоматические доказательства

Причина — `type=text` с placeholder `ЧЧ:ММ` без форматирования в input handler; валидация происходила только перед отправкой.

- В `form.mjs` добавлен presentation formatter: `004` → `00:4`, `0045` → `00:45`.
- `main.mjs` применяет его при вводе/вставке и сохраняет каретку/выделение; `index.html` задаёт цифровую клавиатуру через numeric inputmode.
- Неполное время не дополняется до допустимого, неверные часы/минуты не подменяются, секунды не разрешены. Неизвестность времени по-прежнему задаётся только вручную.
- До исправления `node --test --test-isolation=none tests/ui/session.test.mjs` дал **27 passed / 6 failed**, exit 1; assertions воспроизвели `0045 != 00:45` и отсутствие разделителя при наборе.
- После исправления `node --test --test-isolation=none tests/ui/session.test.mjs tests/ui/form.test.mjs tests/ui/places.test.mjs tests/ui/transport.test.mjs` дал **79 passed**, exit 0, включая шесть regression checks.

Точные проверки в [session.test.mjs](../../../tests/ui/session.test.mjs):

- `typing four time digits inserts the separator, preserves caret and sends HH:MM`;
- `pasted time 0045 displays 00:45 without losing leading zeroes` и варианты `0000`, `1200`, `2359`;
- `time formatting keeps editing/clearing and rejects partial, seconds and invalid ranges`.

**Позитивный контроль:** после форматирования и ручной отметки gate настоящий transport отправляет ровно один POST с `birth_time:"00:45"`; до явной отправки запросов build нет. Полное описание реализации и сопутствующие проверки — [журнал Developer](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#13-исправление-формата-ввода-времени).

Автоматические checks используют настоящий mount/form/session/transport и листовой DOM-порт. Они не являются ручным retest в настоящем браузере и не подтверждают работу мобильной клавиатуры.

### Ручная повторная проверка и условие закрытия

После публикации исправления зафиксировать точный проверяемый commit, браузер и дату retest:

1. Обновить страницу, снять отметку неизвестности и последовательно набрать `0045`; убедиться, что отображается `00:45`.
2. Вставить `0045`, затем проверить `0000`, `1200`, `2359`: ожидаются `00:45`, `00:00`, `12:00`, `23:59`.
3. Исправить часы/минуты и очистить поле; проверить удобство положения курсора. Переключить неизвестность и обратно — введённое `00:45` должно сохраниться.
4. Проверить, что неполное или неверное время не становится допустимым автоматически; канонический `HH:MM` остаётся единственным форматом известного времени в intent/API.

**Результат ручного retest:** PASS @ `a8b45db`: набор, clipboard paste, `0000/1200/2359`, редактирование/очистка, сохранение при unknown toggle и канонический API intent подтверждены. [Evidence](#tester-full-retest-a8b45db). Общая приёмка UI этим дефектом не подтверждается.

<a id="external-model-review"></a>
## Ревью другой модели — 2026-10-07

**Происхождение:** найдено другой моделью. Имя/версия модели не сообщены. Владелец передал список из 16 замечаний и поручил Developer зарегистрировать принятые баги и подготовить промты. Исходный материал — вложение «Вставленный текст.txt» в текущем чате; ниже сохранены номера и самостоятельные воспроизводимые описания.
**Baseline проверки:** `0d5d70acfc4f1f384b2c06970b35111b411c4fc4`, `dev/ui-birth-form-and-facts-review`. **Дата проверки:** 2026-10-07.
**Ownership:** исправление — Developer; независимая проверка и окончательная severity — Tester; priority/delivery — Change Manager. После DEV-UI-07/08 все восемь записей 005…012 — FIXED PENDING RETEST. Ручной retest исправлений NOT RUN; независимая приёмка не подтверждена.
**Подтверждение:** Developer сверил код/approved requirements и воспроизвёл указанные ниже случаи на настоящих UI-модулях с существующими fixtures и листовыми fake network/clock/DOM. Команда `node --test --test-isolation=none tests/ui/*.test.mjs` при ревью дала 126 passed / 0 failed; эти зелёные тесты не покрывают найденные условия. Live HTTPS GET отдельно подтвердил №1 и заголовки ресурсов №5. Это не независимая Tester acceptance.
**План исправления:** [DEV-UI-07/08 — найдено другой моделью](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#external-model-bugs).
**Предел scope:** зарегистрированы №1, 2, 3, 4, 5, 6, 13, 14 в уточнённой формулировке. №7, 11 не нарушают текущий контракт; №8–10 — предложения UX; №12 связан с уже принятым FIND-HTTP-023 и предложением клиентского таймаута; №15–16 — предложения очистки. Новыми багами они не объявляются.

<a id="test-find-ui-005"></a>
## TEST-FIND-UI-005. Место без названия региона нельзя выбрать

- **Источник:** найдено другой моделью, замечание №1; пользователь подтвердил сообщение «Поиск временно недоступен» для «Гонк» скриншотом.
- **Тип / оценка / blocks:** implementation defect; S2/P2 PROPOSED — часть допустимого каталога недоступна для выбора, основной сценарий для этих мест блокируется до поставки исправления; остальные сценарии можно продолжать. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-07.
- **Контракт:** REQ-UI-02/10, AS-UI-02/18/19; [PlaceSuggestion](../../requirements/component_responsibilities/exact-orb_place_catalog.md), [PlaceSuggestionDTO](../../../src/exact_orb/http_api/dto.py) допускают `admin1_name:null`.
- **Воспроизведение / actual:** ввести «Гонк». Live `GET /places?query=Гонк` вернул 200 и `{"items":[{"place_id":"1819729","display_name":"Гонконг","admin1_name":null,"country_code":"HK"}]}`, request ID `d454c88c-74ba-4d7a-8d0c-419073e67bbb`. UI отвергает всю выдачу. В локальном `data/places.sqlite` read-only SQL подтвердил 37/16329 мест с отсутствующим названием региона.
- **Причина / expected:** [places.mjs](../../../src/exact_orb/http_api/ui/places.mjs) требует строку для всех четырёх полей. Допустимый `null` должен доходить до подсказки «Гонконг / — / HK» и выбора подтверждённого ID. В смешанном списке остальные корректные места также доступны.
- **Регрессия / закрытие:** `places.test.mjs` и mounted проверка выбора/явного POST с `place_id:"1819729"`; позитивный контроль региона-строки. Политика удаления повреждённых элементов отдельно не меняется. Закрытие после автоматических проверок и ручного retest выбора.
- **Developer fix, 2026-10-07:** nullable регион принят, в смешанном списке элементы сохранены; mounted тест проверяет «—», выбор ID и один POST только после ручного checkbox. Tests `a nullable region preserves the entire mixed result and confirmed selection` и `mounted nullable-region selection renders a dash and sends only the selected ID after the gate` прошли. [Фактические проверки DEV-UI-07](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-07-execution). Рабочий стенд не перезапускался, browser retest NOT RUN.

<a id="test-find-ui-006"></a>
## TEST-FIND-UI-006. Неподтверждённый 5xx не запускает сверку

- **Источник:** найдено другой моделью, замечание №2. **Тип / оценка / blocks:** implementation defect восстановления; S2/P2 PROPOSED — возможен повтор build при неизвестном исходе первого сохранения; затронут gate recovery/error acceptance. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-08.
- **Контракт:** REQ-UI-09, AS-UI-14/23, DP-UI-09; [HTTP API §9](../../requirements/http_api.md). Применяется безопасная сверка неизвестного исхода, сохраняются кодовые политики известных ErrorDTO.
- **Воспроизведение / actual:** открыть coordinator, вернуть на POST текстовые 502 и 504 либо `500 INTERNAL_FAILURE`. В контролируемом воспроизведении остались только bootstrap → current → POST, `recovery:null`, `canSubmit:true`. [session.test.mjs](../../../tests/ui/session.test.mjs), тест `text proxy error and incomplete success cannot masquerade as a committed chart`, также допускает второй POST после 502.
- **Причина / expected:** [planRecovery](../../../src/exact_orb/http_api/ui/recovery.mjs) распознаёт четыре исхода и пропускает эти 5xx. POST с неопределённым результатом требует безопасного bootstrap/current до нового явного build; failed check блокирует build, успешный old/empty check сохраняет предупреждение о позднем завершении и ручной gate.
- **Уточнение:** внутренний `COMMIT_FAILED` может отображаться сервером в публичный `500 INTERNAL_FAILURE`, но UI не получает `context_status`. Для такого 500 нужна консервативная сверка; нельзя определять стадию по cookie или публиковать внутренний контекст. Фактический поздний commit после 502 в live-стенде не воспроизводился.
- **Регрессия / закрытие:** planned cases в `recovery.test.mjs`/`session.test.mjs` на 502/504 без ErrorDTO, неизвестный 5xx, 500 INTERNAL_FAILURE, failed/successful check; позитивные контроли известного 503 capacity и 504 BUILD_TIMEOUT. Проверить порядок запросов и отсутствие автоматического POST.
- **Developer fix, 2026-10-07:** неизвестные 5xx и все публичные `500 INTERNAL_FAILURE` запускают bootstrap/current; до успешного чтения build заблокирован. Raw 504 не требует restart. Реальный Retry-After соблюдается, failed check сохраняет карту/черновик и не создаёт цикл повторов; old/empty получает предупреждение о позднем commit и только gated manual retry. Tests `unconfirmed … blocks POST until bootstrap/current …` (8), `unconfirmed 5xx respects real Retry-After …`, `mounted unknown 5xx failed at …` (2) и сохранённые known policies прошли. [Фактические проверки DEV-UI-08](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08-execution). Live proxy/late commit и независимый retest NOT RUN.

<a id="test-find-ui-007"></a>
## TEST-FIND-UI-007. Recovery считает устаревшую карту совпавшим результатом

- **Источник:** найдено другой моделью, замечание №3; принято частично. **Тип / оценка / blocks:** implementation defect статуса recovery; S3/P2 PROPOSED — сводка может создавать впечатление подтверждённого пересчёта; маркировка устаревания и действие пересчёта сохраняются. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-08.
- **Контракт:** REQ-UI-08/09, AS-UI-11/14/23, DP-UI-09.
- **Воспроизведение / actual:** показать current с `chart_stale:true`; повторить то же намерение и потерять ответ POST; сверка вернула ту же устаревшую карту. `recoveredStatus` возвращает `matched`, сообщение «Текущая карта соответствует отправленным данным», повторная безопасная проверка скрывается.
- **Причина / expected:** совпадение birth проверяется до устаревания. Старые факты остаются видны, но свежий результат не подтверждается; recovery объясняет это и допускает только разрешённые safe check/явный пересчёт.
- **Уточнение:** сам `chart_identity === previousIdentity` не доказывает отсутствие свежего результата: ID — calculation key, а не уникальный ID попытки. Для `chart_stale:false` и совпавшего намерения одинаковый ID допустим; локальная версия bootstrap также не доказывает результат POST.
- **Регрессия / закрытие:** planned stale+lost-response mounted/coordinator case и позитивный fresh same-identity case; проверить текст, старые факты, safe check и gate. Ручной recovery retest после исправления.
- **Developer fix, 2026-10-07:** matching stale current получает локальный UI-статус `stale`, сохраняет факты, «Пересчитать» и safe recheck; сообщение не подтверждает свежий build. Fresh same-identity по-прежнему допускает matched. Два mounted cases `mounted matching stale/fresh current with unchanged identity preserves facts and honest recovery feedback` прошли; safe recheck действительно читает current без POST, ручной пересчёт — отдельное действие. [Evidence](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08-execution). Browser retest NOT RUN.

<a id="test-find-ui-008"></a>
## TEST-FIND-UI-008. Восстановление сессии не объясняет отклонённый build

- **Источник:** найдено другой моделью, замечание №4. **Тип / оценка / blocks:** дефект обратной связи; S3/P3 PROPOSED — требуется новое действие, причина пользователю не названа; основной build доступен. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-08.
- **Контракт:** REQ-UI-03/09/10, AS-UI-12/19.
- **Воспроизведение / actual:** POST вернул 409 SESSION_EXPIRED/NOT_FOUND; bootstrap/current успешны и current пуст. `accept()` очищает исходную ошибку, экран сообщает только «Сохранённой карты пока нет». Черновик сохраняется, автоматического POST нет — эта часть правильна.
- **Expected:** сообщить об обновлении сессии и необходимости нового явного нажатия; показать действительный current, сохранить дату/время/ID и ручной gate. При отказе safe read сохранить ошибку и блокировку.
- **Регрессия / закрытие:** расширить существующие session-loss tests mounted assertions на видимое сообщение и один POST до отдельного нажатия; позитивный контроль успешного ручного build. Ручной retest после исправления.
- **Developer fix, 2026-10-07:** только успешный current после session 409 показывает «Сессия обновлена», объясняет отклонённое построение и отдельное нажатие; следующий явный build снимает уведомление. При failed bootstrap/current нет ложного успеха; последующий safe recheck объясняет восстановление. Шесть `${SESSION_CODE} recovers ${empty/chart_ready} with visible new-action explanation and intact draft` и два `session-loss check failed at …` passed, draft/gate и один POST до явного действия сохранены. [Evidence](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08-execution). Ручной retest NOT RUN.

<a id="test-find-ui-009"></a>
## TEST-FIND-UI-009. Обновление UI может смешивать версии ресурсов

- **Источник:** найдено другой моделью, замечание №5. **Тип / оценка / blocks:** дефект доставки ресурсов, подтверждённая конфигурация с риском обновления; S2/P2 PROPOSED — несовместимые версии модулей могут нарушать работу после обновления; конкретное смешение версий в браузере NOT RUN. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-07.
- **Контракт:** REQ-UI-01/10, AS-UI-01/10/19; same-origin packaged UI. Явная политика кэширования ресурсов — технический выбор Developer внутри этого способа доставки.
- **Воспроизведение / actual:** live HTTPS GET `/ui/main.mjs` вернул 200, ETag и Last-Modified, без Cache-Control; [app.py](../../../src/exact_orb/http_api/app.py) монтирует обычный StaticFiles. HTML имеет no-store. Постоянные URL ресурсов допускают эвристическую свежесть и использование прежнего кода.
- **Expected:** для `/ui/*.mjs` и CSS задать `Cache-Control:no-cache`, сохранив ETag/Last-Modified и корректные conditional 304; HTML/API сохраняют no-store. Новые URL/hash build pipeline не нужны для этого исправления.
- **Регрессия / закрытие:** `tests/http_api/test_ui_delivery.py` проверяет 200/304 и установленный wheel вне checkout. После обновления повторить browser reload с обычным кэшем, зафиксировать версии/сетевое evidence. CSP/nosniff не включены в этот баг.
- **Developer fix, 2026-10-07:** private StaticFiles subclass добавляет no-cache модулям/CSS, включая conditional 304; ETag/Last-Modified/MIME, HTML/API no-store и безопасные 404/405 сохранены. Расширены существующие delivery и installed-wheel tests; **7 passed**, wheel доставляет **10** UI-ресурсов вне checkout. [Evidence](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-07-execution). Live cache/reload после обновления NOT RUN.

<a id="test-find-ui-010"></a>
## TEST-FIND-UI-010. Результат POST не имеет сводки данных рождения

- **Источник:** найдено другой моделью, замечание №6; принято как дефект обратной связи. **Тип / оценка / blocks:** S3/P3 PROPOSED — у построенной карты отсутствует сводка; при последующем редактировании формы результат трудно связать с отправленными данными. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-08.
- **Контракт:** REQ-UI-03/08, AS-UI-03/04/10/22; [BuildReadyDTO и BirthViewDTO](../../../src/exact_orb/http_api/dto.py).
- **Воспроизведение / actual:** после валидного committed POST coordinator принимает view с `birth:null`; в статусе отсутствуют дата, место и время. Контрольный пример подтвердил, что сама форма сохраняет эти данные. Неправильной схемой GET это не является: источник view — build.
- **Expected:** показать отправленные дату, название места и время/явную неизвестность рядом с результатом, привязав их к неизменяемому снимку успешного запроса. Изменённый во время ожидания черновик не становится сводкой прежней карты. После GET источником сводки становится серверный birth.
- **Уточнение / регрессия:** нельзя создавать полный BirthViewDTO из intent — tz_id/offset/warnings неизвестны. Не требуется новый GET только ради сводки. Planned known/unknown-time и draft-edit-during-build tests с настоящим mount/session; отдельный actual-current контроль already_applied/superseded. Ручной retest после исправления.
- **Developer fix, 2026-10-07:** успешный POST сохраняет отдельную неизменяемую экранную сводку, связанную с chart_identity; дата/время/название взяты из отправленного снимка, не изменённого draft. Не создаются tz_id/offset/warnings, новый GET не добавлен. Current, already_applied и superseded читают actual birth. Cases `committed known/unknown time summary belongs to the submitted snapshot despite pending draft edits`, `a rejected later build keeps the summary …`, `foreground summary reads actual current birth …` и два прежних current-control tests passed. [Evidence](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08-execution). Browser retest NOT RUN.

<a id="test-find-ui-011"></a>
## TEST-FIND-UI-011. Некорректный успешный ответ ломает отрисовку

- **Источник:** найдено другой моделью, замечание №13; подтверждён контролируемый случай повреждённого ответа. **Тип / оценка / blocks:** implementation defect UI boundary; S2/P2 PROPOSED — отрисовка прекращается без объяснения, результат не подтверждён; затронута error/recovery acceptance. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-07.
- **Контракт:** REQ-UI-03/08/09/10, AS-UI-15/17/23; публичные ChartDTO/current по [HTTP API](../../requirements/http_api.md).
- **Воспроизведение / actual:** вернуть `200 chart_ready`, корректные kind/identity/state_version и `chart.points:null` в настоящем mounted coordinator. `session.submit()` отклоняется с `TypeError: Cannot read properties of null (reading 'map')`; form-error пуст, phase idle. Обычные сетевые ошибки уже ловятся; реальные корректные DTO не дали этой ошибки.
- **Причина / expected:** минимальная проверка chart допускает объект, который renderer не может читать, а ошибка отрисовки не превращается в видимое состояние отказа. Повреждённый DTO не принимается как подтверждённая карта; сохраняются черновик/последняя подтверждённая карта, отображается ошибка и выполняется соответствующая safe recovery policy для POST.
- **Регрессия / закрытие:** mounted malformed POST/current cases, валидные natal/cosmogram и deferred dispose controls; исключение не подавляется пустым catch, цифры/типы не исправляются догадками. Проверено отсутствие необработанного rejection и автоматического POST. Ручной retest после исправления ожидается.
- **Developer fix, 2026-10-07:** `response.mjs` проверяет DTO перед accept; повреждённый POST 200 запускает только safe bootstrap/current, плохой current сохраняет подтверждённый view и блокирует build. Ошибка renderer даёт видимый fallback и read-only recovery; render cache фиксируется после успешного построения DOM, поэтому повторная проверка действительно отрисовывает таблицы. Mounted cases `malformed POST …` (11), `malformed foreground current …` (4), `unexpected renderer failure during …` (open/foreground/submit), malformed bootstrap/issues и positive BUILD_TIMEOUT/restart прошли. Весь UI — **149 passed**. [Evidence и команды](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-07-execution). Ручной/независимый retest NOT RUN.

<a id="test-find-ui-012"></a>
## TEST-FIND-UI-012. Подпись восстановленного места исчезает при фокусе

- **Источник:** найдено другой моделью, замечание №14. **Тип / оценка / blocks:** дефект отображения выбора; S3/P3 PROPOSED — исчезает подтверждение восстановления, но ID и основной build сохраняются. **Статус:** CLOSED — независимый retest @ `a8b45db`, [evidence](#tester-full-retest-a8b45db). **Work item:** DEV-UI-08.
- **Контракт:** REQ-UI-02/08/10, AS-UI-02/10/19.
- **Воспроизведение / actual:** открыть страницу с saved birth; появилась подпись «Сохранённое место: Moscow». Без редактирования сфокусировать поле места: `renderPlaces(idle)` стирает подпись. Контроль подтвердил, что form.place.place_id остался тем же.
- **Причина / expected:** восстановление меняет form/DOM, но search state остаётся idle. Фокус/blur без редактирования сохраняют подпись и подтверждённый ID. Начало редактирования снимает выбор по прежнему правилу; регион/страна отсутствуют в BirthViewDTO и не выдумываются.
- **Регрессия / закрытие:** planned mounted restore → focus → blur и restore → edit → select cases; после явного выбора новый ID используется в POST. Ручной retest после исправления.
- **Developer fix, 2026-10-07:** idle search presentation сохраняет подтверждённое место из form при focus/blur; недоступные регион/страна не выдумываются. Edit по-прежнему снимает ID; поиск и явный выбор устанавливают новый ID, который уходит в POST. Три `restored ${chart_ready/chart_unavailable}/${time_unknown} place survives focus/blur then edit and explicit new selection` passed, дополнительных lookup при focus нет и undefined не отображается. [Evidence](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-08-execution). Ручной retest NOT RUN.

<a id="test-find-ui-013"></a>
## TEST-FIND-UI-013. Орбис на половине минуты округляется вниз

**Тип:** баг реализации (implementation defect), форматирование опубликованного орбиса.
**Обнаружил / дата:** Tester, независимое ревью 2026-10-08.
**Ответственный за исправление:** Developer. **Ответственный за retest:** Tester.
**Требование:** [REQ-UI-04](../../requirements/changes/ui-birth-form-and-facts/requirements.md#req-ui-04-представление-общих-фактов), семантика @ `ce25dd0`: ближайшая целая угловая минута, точная половина округляется вверх.
**Связанный сценарий:** [AS-UI-07](../../requirements/changes/ui-birth-form-and-facts/scenarios.md#as-ui-07-три-группы-натала-и-формат).
**Проверенный commit:** `1af6e45f9f9f1507149b74e786037d17cf0c73b8`, ветка `test/ui-birth-form-and-facts-review`; production UI из `f7fb34b` интегрирован через PR #51. Во время воспроизведения tracked-дерево чистое.
**Окружение:** Windows, PowerShell, Node.js v24.19.0; настоящий `mountBirthForm` / form / session / transport / renderer, существующие HTTP golden fixtures. Заменены только листовые сеть, таймер и DOM-порт; браузер и layout этим сценарием не проверяются.
**Severity:** **S3, назначена Tester** — в таблице показано неверное значение орбиса с отклонением на одну угловую минуту. Расчёт, исходный DTO и category не изменяются; основной build доступен.
**Priority:** **P2, PROPOSED** — исправить нарушение обязательного правила форматирования до приёмки M1-7.
**Подтверждение приоритета:** ожидается от Change Manager.
**Blocks:** блокер этого дефекта снят успешным retest; общая готовность M1-7 к G5 требует отдельной полноты acceptance evidence.
**Статус:** **CLOSED**.
**Обоснование статуса:** Tester независимо проверил исправление `a576253` на `6f44404`: исходная команда теперь даёт 4 passed, настоящий mounted UI показывает `1°02′`; ближайшие значения по обе стороны половины, перенос минуты, неизменность DTO/category и отсутствие дополнительных запросов подтверждены. Facts 32 passed, UI 188 passed, связанные HTTP/архитектурные проверки 346 passed; полный pytest 2959 passed / 1 skipped с прежним DEBT-CALC-001. Условия закрытия выполнены; live-browser DTO/layout этим retest не проверялись.
**Связанное решение:** нет; ожидаемое поведение уже определено утверждённым требованием, новый выбор семантики не требуется.

### Воспроизведение и причина на исходной версии

1. В существующем валидном natal `ChartDTO` изменить только `aspects[0].orb` на `1.025`; `validChart` подтверждает допустимость fixture. Остальные опубликованные поля и category сохраняются.
2. Передать этот DTO как успешный current через настоящий transport/coordinator, смонтировать форму и открыть «Показать подробности карты».
3. **Фактически:** первая строка таблицы «Все опубликованные аспекты» содержит `1°01′`.
4. **Ожидается:** `1.025° = 61.5′`; половина округляется вверх до `62′`, то есть `1°02′`, по REQ-UI-04. Категория берётся из DTO и не пересчитывается.

Причина в [facts.mjs](../../../src/exact_orb/http_api/ui/facts.mjs), `formatOrb`: `Math.round(orb * 60)`.
Для опубликованного значения `1.025` умножение в JavaScript даёт `61.49999999999999`, после чего округление выбирает 61 минуту.
Это дефект экранного форматирования, а не повод менять расчётный орбис или публичный контракт.

### Доказательства и позитивные контроли

- Независимая команда в предыдущем ревью: PowerShell here-string → `node --input-type=module`; **3 passed / 1 failed**, exit 1. Точный сценарий для повторения приведён ниже.
- При регистрации 2026-10-08 код из этой карточки повторно извлечён и выполнен через `node --input-type=module`: **3 passed / 1 failed**, exit 1; воспроизведение подтверждено. Незакоммиченные изменения при этом затрагивают только этот Markdown-реестр, production code и tests не изменены.
- Валидный DTO проходит `validChart`, настоящий mounted renderer создаёт непустую строку; исключение вызвано assertion ожидаемого текста, а не отказом загрузки UI.
- Контроли: `1.024` → `1°01′`, `1.026` → `1°02′`, `0.999` → `1°00′` — PASS. Последний проверяет перенос минуты в градус.
- `node --test --test-isolation=none tests/ui/*.test.mjs` на том же commit дал **180 passed**. В [facts.test.mjs](../../../tests/ui/facts.test.mjs) есть семь cases округления, включая `1/120` и `3/120`; они не проверяют случай `1.025`.

Команда из корня checkout; ожидаемый результат на дефектной версии — exit 1:

```powershell
@'
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {formatOrb} from './src/exact_orb/http_api/ui/facts.mjs';
import {mountBirthForm} from './src/exact_orb/http_api/ui/main.mjs';
import {documentPort} from './tests/ui/fixtures/dom.mjs';
import {harness,ready,response,currentPath} from './tests/ui/fixtures/session.mjs';
import {validChart} from './src/exact_orb/http_api/ui/response.mjs';
for (const [orb, expected] of [[1.024,'1°01′'],[1.026,'1°02′'],[0.999,'1°00′']]) {
  test(`positive control orb ${orb}`, () => assert.equal(formatOrb(orb), expected));
}
test('REQ-UI-04 / AS-UI-07: orb 1.025 rounds half-up in mounted UI', async () => {
  const h = harness(), doc = documentPort(), saved = ready();
  saved.chart.aspects[0].orb = 1.025;
  assert.equal(validChart(saved.chart), true);
  const category = saved.chart.aspects[0].category;
  h.queue(currentPath, response(saved));
  const ui = mountBirthForm(doc, {apiClient:h.apiClient, clock:h.clock});
  try {
    assert.equal(await ui.ready, true);
    doc.getElementById('chart-details-button').click();
    const table = doc.getElementById('chart-facts').querySelectorAll('table')
      .find(t => t.querySelector('caption').textContent === 'Все опубликованные аспекты');
    const row = table.querySelector('tbody').children[0];
    assert.ok(row.textContent);
    assert.equal(saved.chart.aspects[0].category, category);
    console.log(JSON.stringify({orb:1.025, actual:row.children[4].textContent, expected:'1°02′'}));
    assert.equal(row.children[4].textContent, '1°02′');
  } finally {
    ui.dispose();
  }
});
'@ | node --input-type=module
```

### Условие закрытия и повторная проверка

- Developer добавляет детерминированный case `orb:1.025` в существующее покрытие REQ-UI-04 / AS-UI-07 и исправляет форматирование на ответственном UI-слое.
- На исправленном commit воспроизводящий сценарий и UI-набор проходят; значения непосредственно ниже/выше границы и перенос минуты сохраняются, исходные `orb`, `type`, `category` не изменяются.
- Tester фиксирует точный исправленный commit, команду и фактический результат retest. Общая приёмка других требований этой записью не подтверждается.

### Developer evidence DEV-UI-09 — 2026-10-08

Baseline исполнения `84410f17304d6ca2a06d3ac2e8e04b3c529b29f0`, ветка `dev/ui-birth-form-and-facts-review`, локальный diff. В `facts.mjs` нижняя целая минута определяется через floor, половинная граница сравнивается с исходным orb в градусах; epsilon и обрезание дроби не используются. `1.025` → `1°02′`, ближайшее меньшее Number → `1°01′`, сосед сверху → `1°02′`; прежние половины и перенос минуты сохранены.

Добавлены семь cases в существующую параметризацию и один mounted regression `REQ-UI-04 / AS-UI-07 / TEST-FIND-UI-013: mounted current orb 1.025 rounds half-up without changing DTO or requests`. Реальные mount/form/session/transport/renderer с заменой только leaf network/clock/DOM; validChart, непустая строка, unchanged category/source/snapshot DTO и отсутствие запросов при открытии подтверждают выполнение пути.

- `node --test --test-isolation=none tests/ui/facts.test.mjs`: **30 passed / 2 failed** до исправления, оба assertion неверного текста; затем **32 passed**, exit 0.
- `node --test --test-isolation=none tests/ui/*.test.mjs`: **188 passed**, exit 0.
- `python -B -m pytest -p no:cacheprovider tests/http_api/test_projectors.py tests/http_api/test_ui_delivery.py -q`: **34 passed**, exit 0 при повторении с доступом к системным временным файлам pip; initial sandbox 33 passed / 1 failed — PermissionError installed-wheel setup, сохранён отдельно.
- `python -X utf8 -B -m pytest -p no:cacheprovider -q -rs`: **2959 passed / 1 skipped**, exit 0; только согласованный DEBT-CALC-001.

Ignored logs/fingerprint — `logs/ui-dev-09/`; точный состав и handoff — [журнал Developer](../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md#dev-ui-09-execution). Исходные `orb`, `type`, `category`, порядок DTO и расчётное поведение сохраняются. Severity/priority и независимое evidence Tester не переопределяются.

### Независимый retest Tester — 2026-10-08

**Проверенный commit:** `6f44404e6ba9e9f1eb8a529978b5e076d8af1bf2`, merge PR #54; исправление — `a576253c4e132498ae394c67237a6f29d3e0c4ee`. Ветка `test/ui-birth-form-and-facts-review` обновлена fast-forward с `f23ed53`; production code/tests и expected values Tester не менял.
**Окружение:** Windows, Node.js v24.19.0, Python 3.14.0; те же реальные UI-модули и управляемые листовые fixtures. Все runtime commands выполнены до этих документных изменений.
**Результат:** **PASS** — код исходного воспроизведения из этой карточки извлечён и выполнен через `node --input-type=module`: **4 passed / 0 failed**, exit 0; actual/expected для `1.025` одинаковы — `1°02′`. Контроли `1.024`, `1.026`, `0.999` сохранились.

Проверены фактические assertions нового mounted regression: валидный current, непустая строка, категория «Точный», исходный и snapshot DTO неизменны, открытие подробностей не добавляет запрос. Параметризация различает ближайший Number ниже `1.025` и сосед сверху, а также половину с переносом градуса; искусственного epsilon нет. Независимый integer oracle дополнительно проверил 180 001 значение с шагом 0.001° на диагностическом диапазоне 0…180° — PASS; это не новая граница API.

Точные команды остальных прогонов, матрица покрытия, skip и предел acceptance — [отчёт Tester](tester.md#tester-orb-fix-retest). Полный pytest имеет только прежний DEBT-CALC-001; этот долг не закрывается. Controlled live-browser DTO/layout и общий G5 NOT RUN в данном историческом retest @6f44404. **Итог этого раунда Tester:** условия закрытия TEST-FIND-UI-013 выполнены, дефект CLOSED; остальные findings тогда сохраняли свои отдельные статусы.

<a id="tester-full-retest-a8b45db"></a>
## Независимый полный retest — exact a8b45db, 2026-10-08

**Environment:** закрытый HTTPS `exact-orb.localhost:8443`, реальный Chromium154 IAB, Windows11/Python3.14/Node24.19; production exact commit `a8b45dbbda5378e598eb75b15f81e1445a75020e`. [Команды, матрица и JSON evidence](acceptance-a8b45db.md). Предыдущие записи «Developer fix / NOT RUN» — фактическая история соответствующих handoff, не текущая диспозиция.

| Finding / требование | Воспроизводимые действия на исправленной версии | Expected / actual, позитивный контроль | Закрытие |
|---|---|---|---|
| 004 / REQ02, AS05 | Набрать/вставить0045, проверить0000/1200/2359, edit/delete, unknown on/off, explicit build | Формат00:45/00:00/12:00/23:59; cursor/edit и прежнее время сохраняются; invalid empty/24:00 без POST. Real00:00/12:00 natal — positive; только HH:MM в API | PASS → CLOSED; S3/P3 proposed |
| 005 / REQ02, AS02/03 | Найти реальный Hong Kong1819729 с admin1_name:null, открыть подсказку, выбрать, manual gate/build | Регион «—», нет падения выдачи; выбранный ID1819729 ушёл в actual POST, natal готов. Не только renderer fixture | PASS → CLOSED; S2/P2 proposed |
| 006 / REQ03/09, AS14/23 | Raw502, hold bootstrap, fail current503, safe repeat; затем actual manual build. Typed500 after real commit; raw504 | До завершения safe read POST заблокирован; old/draft сохранены, warning читаем, no replay. После разрешённого ручного действия новый actual natal; typed500 находит committed2005, raw504 не требует фиктивного restart | PASS → CLOSED; S2/P2 proposed |
| 007 / REQ08/09, AS11/23 | Actual Selena version changed → stale; fresh-connection abort того же intent, safe GET; затем positive fresh same identity | Stale не matched, показан неподтверждённый результат и сохранены exact old rows. Safe read noPOST; real explicit recalc fresh и matching fresh current показывают matched | PASS → CLOSED; S3/P2 proposed |
| 008 / REQ09, AS12 | Controlled409 SESSION_EXPIRED + cookie removal; real bootstrap/current; explicit gate/build | Draft сохранён, «Сессия обновлена…нажмите кнопку ещё раз», no hidden POST; ручной POST positive завершает карту | PASS → CLOSED; S3/P3 proposed |
| 009 / delivery, REQ01/10 | Actual cache reload нового checkout, проверить wire200/304 модули/CSS и wheel вне checkout | no-cache у assets включая304, HTML/API no-store. 8ESmodules+CSS revalidated; wheel10resources delivered. Реальный прежний mixed-version incident не воспроизводился/не заявляется | PASS → CLOSED по policy closure; S2/P2 proposed |
| 010 / REQ03/08, AS03/04/10/22 | Event-held unknown build1985HK; во время ожидания draft1990known00:45; release/commit; отдельный known build | Summary1985/unknown/HK принадлежит sent snapshot; draft1990/00:45 остаётся и не становится прежней summary. Known summary также содержит sent date/time/place; no GET только ради сводки | PASS → CLOSED; S3/P3 proposed |
| 011 / REQ03/09, AS15/23 | Valid confirmed current; malformedPOST200 points:null, malformedcurrent, затем valid safe check | Нет uncaught TypeError/console error, confirmed facts/draft сохранены, recovery visible и safe-only; valid GET снимает failure. 11POST/4current malformed shapes и renderer fallback также PASS в Node | PASS → CLOSED; S2/P2 proposed |
| 012 / REQ02/08, AS10/11 | Real reload selected HK; focus/blur, known/unknown controls; edit Moscow then select keyboard/build | Saved label и ID сохраняются на focus/blur, лишнего lookup нет. Edit сбрасывает старый ID; после явного выбора actual POST524901. Unavailable/unknown variants автоматикой также PASS | PASS → CLOSED; S3/P3 proposed |
| 013 / REQ04/06, AS07 | Separate valid current DTO fixture; orbs1.025/1.024/1.026/0.999, Enter details | Actual1°02′/1°01′/1°02′/1°00′; category «Точный» из DTO сохранена; реальный page rendering, no goldens changed. Прежний mounted regression188 UI PASS | PASS; CLOSED сохранён; S3/P2 proposed |

**Ownership:** Developer fixes остаются DEV-UI-03/07/08/09; closure и окончательная severity — Tester; priority/delivery — Manager, proposed priorities не утверждены этим документом. Ни один из004…013 больше не блокирует по исходному closure criterion.

**Общий verdict:** **REVORK**. AS-UI-16 native foreground — environment limitation / NOT RUN, Analyst clean transfer/current сверка — существующий G5 BLOCKED. Они записаны в общей матрице как собственные пробелы, а не переоткрытие исправленных bugs. После ordinary browser foreground и Analyst clean commit требуется завершить соответствующее Tester evidence; финальную acceptance утверждает Manager.
