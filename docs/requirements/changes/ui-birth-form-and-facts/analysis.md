# Functional Analysis: ui-birth-form-and-facts

**Статус:** IMPLEMENTED / READY_FOR_TEST — Analyst-семантика @ `ce25dd0` реализована в `f7fb34b`, Developer handoff `ab072ec` интегрирован PR #51 / `0c893f0`; G4 подтверждён Manager. Независимая verification и clean transfer до G5 NOT RUN — [Manager-артефакт](../../../project_management/change_plans/ui-birth-form-and-facts/artifacts.md#change-brief). **Исходный commit Analysis:** `652bd73405db0a0611e98e81af6f3f668dd429f6`; **исторический вход этой редакции Analyst:** `4a5f128`.
**Артефакты:** [requirements.md](requirements.md), [scenarios.md](scenarios.md), 10 REQ / 23 AS. **Текущий реестр:** [Manager-артефакт](../../../project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register), утверждаемая редакция поверх `2972e42`; DP-UI-01…09 ACCEPTED, DEBT-UI-001 OPEN. **Консультации:** [Developer](../../../project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md) @ `082c6b9`, [Tester](../../../testing/ui-birth-form-and-facts/tester.md) @ `0f6aa82`.
**Нормативный baseline:** `docs/requirements/http_api.md` §§4–9, 13; component requirements и ADR, перечисленные в [requirements.md](requirements.md), действующий код и тесты @ `4a5f128`. Макеты содержат демонстрационные числа и не являются oracle.

## Вывод для Manager и владельца

`DP-UI-01/02` закрепили **три публичные группы M1-7: точки, дома, аспекты**. Они уже входят в `ChartDTO`, который возвращается после committed POST и при восстановленном GET current. Новых endpoint, расчёта в браузере и расширения публичного DTO для этого объёма не требуется. Внутренний движок уже рассчитывает конфигурации и силу, в том числе degree flags; их отсутствие в текущем публичном DTO не следует путать с отсутствием расчёта. Прежнее предложение `REQ-API-UI-01…03` о публикации дополнительных групп снято с объёма M1-7. Manager синхронизировал реестр, roadmap и задания ролям; Analyst не меняет эти записи.

`DP-UI-04/08` закрепили закрытый этап: checkbox исходно снят, POST возможен после **ручной** отметки; страницы, её текста и промежуточной сводки на этом этапе нет. Текст вместе со страницей записаны как `DEBT-UI-001` M1-9 до распространения ссылки другим людям и публичного трафика. ADR-0034 не меняется: §2 требует ручную отметку до POST, а подготовку и проверку страницы относит к M1-9 как условие до публичного трафика. Прежний вывод Analysis о запрете каждого build до страницы и предложение промежуточной сводки сняты. AS-UI-20 проверяет checkbox gate, AS-UI-21 — закрытый этап и возврат к долгу страницы. Отметка остаётся presentation gate, а не юридическим согласием.

**Диспозиция G2/G3 Manager:** DP-UI-09 зарегистрирован @ `64934fc`; Developer plan и estimate 5–8 дней получены @ `082c6b9`, независимый Tester review TESTABLE и estimate 3–5 подтверждены @ `0f6aa82`. Бюджеты владельца 4/5/5, план и G3 утверждены Manager 2026-10-07; blocking contract gaps отсутствуют. Следующие действия — реализация, UI checks и чистовая редакция до G5. Имени нет, чат видим/неактивен, подробности активны; DP-UI-03 и DEBT-UI-001 сохраняются.

**Бюджет Analysis:** исходный целевой 1 рабочий день был достаточен для первичного G1 draft при готовом пакете чтения. Review, смена scope, оформление долга и чистовой перенос требуют отдельного времени Analyst; прежняя оценка 1,5–2,5 дня собственной работы остаётся ориентиром, а не обещанным сроком. Календарное ожидание решений владельца и Manager отдельно.

## Сложность реализации и срок

В репозитории есть FastAPI `bootstrap`, `places`, `build`, `current`, но нет production браузерного экрана: `docs/ui_ux/README.md` называет `web-prototype.html` демонстрацией, а `src/exact_orb/http_api/app.py` подключает API routers. `DP-UI-07` задаёт целевой бюджет Development 4 рабочих дня, **не** estimate Developer. Tester document review оценивает независимую проверку в 3–5 дней при целевом бюджете 2. Сужение до трёх групп убирает публичную DTO-дельту, но не устраняет работу по форме, сессии, поиску, recovery и адаптивному экрану. Потеря ответа POST добавляет неоднозначность повторного действия без нового server status endpoint; её влияние на срок нужно оценить отдельно.

| Драйвер | Минимальная работа в M1-7 | Нужная оценка/evidence |
|---|---|---|
| Браузерная интеграция | Подключить реальную страницу к существующим API и cookie flow; отделить bootstrap от current и committed от `already_applied`. | Developer указывает стек, work items, диапазон, confidence и критический путь; Tester проверяет HTTPS/browser evidence. |
| Форма и место | Дата → место → время; GET начиная с трёх букв, debounce, актуальный ответ, фиксация `place_id`, известное/неизвестное время. | Проверить выбор клавиатурой и мышью, ошибочный и пустой поиск, запрет POST без ID. |
| Факты и восстановление | Три группы из текущего `ChartDTO`, `ДД°ММ′`, natal/cosmogram, empty/stale/unavailable, две вкладки и неопределённый исход build. | Tester связывает POST/current по `chart_identity`, проверяет ошибки и 360 px; никакого нового API блока. |
| Gate условий и долг страницы | `DP-UI-04/08`: снятый по умолчанию checkbox, ручная отметка до POST; текст и страница — `DEBT-UI-001` M1-9. | Закрытый этап AS-UI-20/21; Manager отслеживает долг до распространения ссылки другим людям. |
| Имя и действия | Поля имени нет; после результата активные подробности трёх групп и видимый неактивный чат (`DP-UI-05`). | AS-UI-22 проверяет отсутствие второго POST и открытие именно полученной карты; будущий чат остаётся M2. |
| Потеря ответа POST | Сетевой обрыв не несёт `ErrorDTO`/`Retry-After`; после него сервер может ещё выполнять build. | Владелец выбрал вариант B: AS-UI-23 проверяет read-only сверку, предупреждение и ровно один новый POST только после явного нажатия при успешном old/empty current. Manager записывает выбор. |

**Подписанный вывод Functional Analyst — 2026-10-06:** планировать M1-7 как путь формы и трёх таблиц на текущем API с действиями `DP-UI-05`. Developer оценивает 4-дневный target по work items и риску браузерной интеграции; Tester сопоставляет 2-дневный target со своим ориентиром 3–5 дней. Manager согласует реалистичный календарь после этих оценок. Колесо остаётся M1-8, полный перенос прототипа — M1-8.1, чат — M2. Новые группы и стихии требуют отдельного будущего scope/контракта; место в макете не означает пустые работающие секции M1-7.

## Уточнение поиска и текста действий

По [r4179366994](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179366994) GET начинается после **третьего введённого символа** и повторяется для изменённого префикса длиной не менее трёх символов после debounce. Для 1–2 символов UI не делает GET, хотя API их принимает; поздний ответ на старый префикс не заменяет актуальные подсказки. REQ-UI-02 и AS-UI-02 содержат проверяемую последовательность.

В [r4179362074](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179362074) владелец спросил о CTA. **CTA = Call to Action, видимая кнопка или призыв к действию**. Это не client agreement и не checkbox условий. Итоговые действия после результата определены `DP-UI-05` и описаны в REQ-UI-03/AS-UI-22.

## Трассировка и наблюдаемое поведение

| Требования | Источник | Сценарии | Sequence / проверка |
|---|---|---|---|
| REQ-UI-01, 08 | HTTP §§6.1–6.2; ADR-0040/0041 | AS-UI-01, 10, 11 | `http_api/001`, `004`; `session/002`; нет browser restore evidence |
| REQ-UI-02 | HTTP §§6.3–6.4; place catalog; решение о трёх буквах | AS-UI-02, 04–06, 18 | `http_api/002`; `place_catalog/001`; нет browser selection evidence |
| REQ-UI-03, 09 | HTTP §§4, 8–9; ADR-0034/0040/0041; DP-UI-04/05/08 | AS-UI-03, 06, 12–14, 16, 17, 20–23 | `http_api/003`, `004`; `session/006`; AS-UI-23 требует UI evidence и записи выбора владельца Manager |
| REQ-UI-04–06 | HTTP §7.2; ADR-0029/0030/0032 | AS-UI-07–09, 15, 16, 22 | `http_api/003`, `004`; `test_projectors.py` не проверяет браузерные таблицы/округление |
| REQ-UI-07, 10 | UI/UX draft; DP-UI-05 | AS-UI-02, 19, 22 | Место будущих секций только в макете; browser/mobile evidence ожидается |

1. **Вход и восстановление:** браузер → `POST /session/bootstrap {}` → `ContextService.load/create` → `ready`; браузер → `GET /charts/current` → `ContextService.load` → `session_view` → `empty/ready/stale/unavailable`. Чтение не вызывает engine/cache и не пересчитывает карту.
2. **Поиск и выбор:** после трёх символов → `GET /places` → admission → `PlaceSearch.search` → подсказки → локальный выбор `place_id`. Cookie не требуется; сборка использует ID, а не строку.
3. **Build:** после действующего gate → transport validation/cookie/admission → `ApplicationOrchestrator.execute(run_id=request_id)` → `ContextService.load` → `BuildNatalHandler.handle` → resolver → artifact/to_stored → `ContextService.save` → committed `ChartDTO`. `already_applied` требует отдельный current GET.
4. **Recovery:** `RESULT_SUPERSEDED`/`already_applied` → current; `SESSION_* 409` → bootstrap → current; `STATE_COMMIT_FAILED` → current после `Retry-After`; `BUILD_TIMEOUT` → readiness/restart → bootstrap → current после `Retry-After`. Потеря ответа без HTTP status → восстановление связи → bootstrap → current; old/empty не доказывает завершение исходного build. Автоматического второго POST нет.

Существующие sequence diagrams `docs/sequence_diagrams/http_api/001`…`004`, `place_catalog/001`, `session/002/006` описывают серверный путь; новая публичная схема и её изменение в диаграммах для M1-7 не предлагаются. Существенные переходы должны наблюдаться как связанные `http_message send/receive` или terminal/error с request/run ID по действующим ADR логирования; полного payload на INFO не требуется. UI-действия подтверждаются browser evidence, не каждым нажатием в серверном журнале.

## Findings Intake и рекомендации к решениям

### FIND-UI-001. В публичном DTO нет трёх ранее подтверждённых групп

**Type:** прежний requirement gap. **Severity/impact:** расширение публичного DTO требовалось для старого шестигруппового объёма. **Owner:** владелец/Manager. **Status:** RESOLVED IN SCOPE по `DP-UI-01/02`; browser evidence трёх групп остаётся задачей Tester.

`http_api.md` §7.2 и whitelist projector публикуют точки, дома и аспекты; внутренний artifact содержит конфигурации/силу/флаги, но не отдаёт их UI. `DP-UI-01/02` выбрали три группы и текущий DTO, Manager синхронизировал scope. Developer подтвердил техническую возможность reuse в document review; это не доказательство готового UI. Возврат остальных групп потребует отдельного owner scope и POST/current контракта.

### FIND-UI-002. Нужна фиксация этапа страницы условий

**Type:** staging/debt tracking. **Severity/impact:** не блокирует build на закрытом стенде при ручной отметке; распространение ссылки зависит от закрытия долга. **Owner:** владелец (`DP-UI-04/08`), Manager (`DEBT-UI-001`). **Status:** RESOLVED FOR CLOSED STAGE по реестру; `DEBT-UI-001` OPEN, browser evidence gate ожидается.

ADR-0034 §2 предусматривает отдельную страницу M1, подготовку и проверку относит к M1-9 как условие до публичного трафика; до POST требует ручную отметку. `DP-UI-04/08` закрепили ручной gate без текста и страницы на закрытом этапе. `DEBT-UI-001` содержит текст и страницу, ответственных и срок до распространения ссылки. Tester проверяет AS-UI-20/21 на реализованном UI; Manager контролирует долг отдельно.

**Диспозиция прежнего предложения Analysis:** промежуточная сводка условий в форме **снята** решением `DP-UI-08`; не включать её в M1-7 и не считать условием его приёмки. Полный текст согласуется с владельцем вместе со страницей по `DEBT-UI-001`. Не использовать формулировку макета «согласие на обработку персональных данных».

**Долг Manager — `DEBT-UI-001`:** в реестре уже зарегистрированы полный текст и отдельная страница «Условия использования сервиса» M1-9, ответственные и проверка Tester. До её поставки и проверки ссылка другим людям не распространяется и публичный трафик не открывается.

### FIND-UI-003. Макеты содержат неподтверждённые поля, кнопки и числа

**Type:** draft/source conflict. **Severity/impact:** лишнее поле или активный чат нарушит утверждённый UI/API flow. **Owner:** владелец (`DP-UI-05`), UI/UX для макета. **Status:** RESOLVED IN REQUIREMENTS; обновление макета и browser evidence ожидаются.

Р1 ставит время перед местом и содержит имя/чат; Э4 показывает offset и лунный диапазон при неизвестном времени; Р5/Э7 содержат демо-цифры. `ui_ux/decisions.md` использует устаревшие `ChartDTO/issues`. `DP-UI-05` принял дату → место → время, без имени, с видимым неактивным «Открыть чат» и активным «Показать подробности карты». Analyst перенёс это в REQ-UI-03/AS-UI-22; UI/UX обновляет макет, Tester проверяет реальный экран.

### FIND-UI-004. Черновик UI и будущие группы

**Type:** scope/visual gap. **Severity/impact:** визуальная приёмка трёх групп без нового HTTP блока. **Owner:** UI/UX для композиции, Tester для evidence. **Status:** RESOLVED IN SCOPE по `DP-UI-01/02`; макет и browser evidence ожидаются.

Первоначальный `ui_ux/requirements.md` описывал точки, дома, аспекты и стихии, тогда как старый `DP-UI-01` требовал шесть групп. Реестр теперь закрепил три группы и композиционное место будущих блоков. REQ-UI-07 не допускает пустых работающих таблиц или обещания будущего контракта; адаптированный макет и browser evidence ещё нужны.

### FIND-UI-005. Потеря ответа build и критерий повтора

**Type:** recovery requirement gap по `FIND-DEV-UI-002` / `TEST-FIND-UI-002`. **Severity/impact:** P2; влияет на повтор после обрыва, риск конкурентных build сохранён в DP-UI-09. **Owner:** владелец — выбор, Manager — регистрация/допуск, Analyst — REQ/AS. **Status:** RESOLVED IN CONTRACT — ACCEPTED RISK. Административная диспозиция Manager 2026-10-07: выбор B зарегистрирован @ `64934fc`, контракт подтверждён Developer `082c6b9` и Tester `0f6aa82`; проверка реализации ещё NOT RUN. Историческое OWNER CHOICE RECEIVED @ `ce25dd0` не является текущим ожиданием регистрации.

При потере ответа браузер не получает HTTP status, `ErrorDTO` и `Retry-After`. HTTP §§9.2–9.3 и серверные tests показывают два возможных исхода: отмена до commit либо завершение защищённого commit после разрыва. Поэтому bootstrap → current может показать старую/пустую карту, пока исходный build ещё выполняется; такой GET не доказывает отказ. Сработавший commit обнаруживается как карта исходного намерения. Серверный `BUILD_TIMEOUT` отличается: он содержит 504 и правило restart/readiness. Нового endpoint статуса в M1-7 не принято.

**Исходные варианты и выбор владельца — 2026-10-06:** A — разрешить ручной повтор только после подтверждённого завершения без commit или restart/readiness и повторного current; это уменьшает риск дублирования, но существующий публичный API не сообщает браузеру о завершении задачи, поэтому UI может остаться заблокированным. B — после успешного bootstrap → current со старой/пустой картой показать предупреждение и разрешить **отдельный ручной** POST; это не требует нового API, но первый расчёт может завершиться позже, вызвать лишнюю работу, расход квоты или конфликт/повторное сохранение. Владелец выбрал **B** и предложил текст «Что-то пошло не так, попробуйте сначала». Analysis уточняет его для точности: «Что-то пошло не так. Новый результат пока не появился. Введённые данные сохранены. Вы можете построить карту ещё раз; предыдущий расчёт может завершиться позже». Это не объявляет первый расчёт неудачным и не заставляет заново вводить форму. До успешной сверки показывается «Не удалось получить ответ о построении карты. Проверяем текущую карту»; при отказе сверки доступно только её повторение. Ни один повторный POST не автоматический; прежний checkbox gate сохраняется. Правило и риск зафиксированы в DP-UI-09 @ `64934fc`; Developer/Tester подтвердили контракт, UI evidence получают после реализации.

### Диспозиция принятых решений

| Решение | Ранее подписанная рекомендация Functional Analyst | Текущее решение и перенос |
|---|---|---|
| `DP-UI-02` | 2026-10-05: не добавлять endpoint или поля для дополнительных групп; применять текущий `ChartDTO` с одинаковой семантикой POST/current. | **ACCEPTED**; REQ-UI-04–06 и AS-UI-07–10 используют текущий DTO. |
| `DP-UI-04` | 2026-10-05: checkbox снят по умолчанию, ручная отметка до POST; текст и страницу отложить в M1-9 до распространения ссылки. | **ACCEPTED**; `DEBT-UI-001` зарегистрирован. REQ-UI-03 и AS-UI-20/21 отделяют закрытый этап от долга. |
| `DP-UI-05` | 2026-10-05: без имени; прежнее предложение не показывать чат заменено выбором владельца. | **ACCEPTED**: активные подробности той же карты и видимый неактивный чат после результата. REQ-UI-03 и AS-UI-22 обновлены. |
| `DP-UI-08` | Промежуточная сводка была предложена Analyst до уточнения владельца. | **ACCEPTED**: сводки нет; предложение снято, полный текст с отдельной страницей в `DEBT-UI-001`. |

**Подпись:** Functional Analyst (`analysis/ui-birth-form-and-facts`), 2026-10-06. Источник решения — Manager-owned реестр; таблица фиксирует перенос в Analyst артефакты.

## Диспозиция замечаний PR #43

Проверены review и все доступные inline threads. «Исправлено» означает изменение Analyst-документов; статус thread в GitHub и утверждение владельца этим не меняются.

| Комментарий | Диспозиция Functional Analyst |
|---|---|
| [r4178058956](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178058956), [r4178086032](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178086032) | В REQ-UI-01 и AS-UI-11 разложены bootstrap/current, `chart_unavailable` и отсутствие карты. |
| [r4178096178](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178096178), [r4178749793](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178749793), [r4179366994](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179366994) | Порог подтверждён: три буквы. REQ-UI-02 и AS-UI-02 проверяют каждый новый префикс, debounce и поздний ответ. |
| [r4178129262](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178129262) | `already_applied` показан как POST 200 без `chart` с отдельным GET. |
| [r4178731223](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178731223) | Словарь будущих DTO-полей был подготовлен в `6187fd5`; owner сократил scope, поэтому DTO-дельта из текущих requirements снята и остаётся только в истории. |
| [r4178758579](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178758579) | AS-UI-20 сохраняет действующий ADR gate и объясняет значение checkbox. |
| [r4178769729](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178769729), [r4179344108](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179344108), [r4179370676](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179370676) | После последнего уточнения владельца REQ-UI-03/AS-UI-20/21 оставляют ADR без изменений: checkbox снят, POST после ручной отметки; страница — долг M1-9 до распространения ссылки. Manager записывает `DP-UI-04`. |
| [r4178774177](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178774177) | Порядок дата → место → время есть в REQ-UI-02; изменение визуального файла у UI/UX. |
| [r4178776260](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178776260), [r4179357890](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179357890), [r4179374962](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179374962) | Более позднее решение сужает M1-7 до трёх групп; REQ-UI-04…07 и AS-UI-07…09/19 обновлены, для будущих групп оставлена композиционная возможность. Manager синхронизирует прежний `DP-UI-01/02`. |
| [r4179346983](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179346983) | Четыре дня указаны как target владельца, ожидает оценки Developer и обновления плана Manager. |
| [r4179362074](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179362074) | CTA расшифровано как Call to Action, кнопка действия; это не соглашение клиента. |

Замечание пользователя к первому diff о смешении операций документа и действий пользователя учтено: в [requirements.md](requirements.md) документный `ADD` отделён от таблиц «действие → запрос/ответ → экран», рядом есть ссылки на [сценарии](scenarios.md). Ответы в GitHub и разрешение threads требуют отдельной коммуникации в review; таблица не выдаёт их за выполненные.

## Диспозиция консультаций Developer и Tester

| Замечание | Решение Functional Analyst и проверка |
|---|---|
| `FIND-DEV-UI-001`, `TEST-FIND-UI-001` | Принятый `DP-UI-05` перенесён в REQ-UI-03/10 и AS-UI-03/07/22: нет имени; активные подробности открывают три группы той же `chart_identity` без второго POST; видимый неактивный чат не открывает диалог и не отправляет запрос. Реальный UI ещё не проверен. |
| `FIND-DEV-UI-002`, `TEST-FIND-UI-002` | REQ-UI-09 и AS-UI-23 покрывают потерю ответа без status/ErrorDTO, сохранение черновика, read-only сверку, два серверных исхода и выбранный владельцем ручной повтор B. Manager записывает решение; Tester проверяет оба исхода управляемыми Event/barrier и browser evidence. |
| `FIND-DEV-UI-003` | Статус и baseline Analyst документов сверены с `change/*` @ `4a5f128`, `DP-UI-01…08` и `DEBT-UI-001`. Предложение промежуточной сводки снято по `DP-UI-08`; этот перенос не закрывает G2 и не заменяет browser evidence. |
| `TEST-FIND-UI-003` | REQ-UI-04 и AS-UI-07 фиксируют ближайшую минуту, перенос через градус (`0.999°` → `1°00′`) и сохранение API category. CLI `_format_orb` уже округляет обычные значения к ближайшей минуте; правило точной половины задано как UI oracle, Developer выбирает устойчивую реализацию. |

## Карта переноса и handoff

| Объект | Действие после утверждения и поставки | Сейчас |
|---|---|---|
| REQ-UI-01…10, AS-UI-01…23 | Перенести утверждённый UI scope в `docs/requirements/current/ui/birth-form-and-facts.md` и `scenarios.md` после реализации и сверки Tester. | IMPLEMENTED: Developer package/handoff `0c893f0`; independent verification и clean transfer PENDING. |
| HTTP `ChartDTO` | Сохранить действующий `docs/requirements/http_api.md` §7.2 без дельты M1-7; ссылки в UI документах ведут к нему. | Новые блоки отложены за пределы M1-7, отдельное решение потребуется при возврате. |
| ADR-0034 и Manager реестр | ADR не менять; принятые `DP-UI-01…08` и `DEBT-UI-001` использовать как источник решений. Выбор B и риск зарегистрированы DP-UI-09; budgets 4/5/5 и диапазоны 5–8 / 3–5 согласованы Manager для G3. | Analyst не меняет эти файлы. |

**Текущий handoff:** требования/scenarios `ce25dd0` реализованы и интегрированы в `0c893f0`; поведение REQ/AS этой административной правкой не меняется. Analyst следующий раз обновляет clean requirements и карту переноса после independent Tester evidence к G5. DEBT-CALC-001 остаётся принятым OPEN / NON-BLOCKING долгом расчётного слоя для M1-7; это не новая семантика UI и не блокер G4 этого change.

**Исторические проверки G1:** `git ls-remote origin refs/heads/change/ui-birth-form-and-facts` и `git diff --check` прошли для `101d628f83a3cdda529dc925dfdde2e370fcc6af`; тогда были 13 требований и 19 сценариев. Review-редакция в `6187fd5` добавила AS-UI-20. Проверки этой редакции фиксируются в итоговом отчёте после запуска; pytest и browser/HTTPS acceptance документной правкой не подменяются.
