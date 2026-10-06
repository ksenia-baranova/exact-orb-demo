# Functional Analysis: ui-birth-form-and-facts

**Статус:** REVIEW REVISION; это позиция Functional Analyst, не разрешение на разработку или изменение ADR. **Входной commit:** `652bd73405db0a0611e98e81af6f3f668dd429f6` — фактический local/tracking/remote HEAD `change/ui-birth-form-and-facts` после manager PR #42 на 2026-10-04. Ветка роли — `analysis/ui-birth-form-and-facts`.
**Артефакты:** [requirements.md](requirements.md) и [scenarios.md](scenarios.md) (AS-UI-01…21). **Реестр решений:** `docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register`; действующие `DP-UI-01/03` приняты, `DP-UI-02/04/05` открыты в последней проверенной редакции реестра. Комментарии владельца в [PR #43](https://github.com/ksenia-baranova/exact-orb-demo/pull/43) задают направление review, но Manager ещё не синхронизировал их с реестром.
**Нормативный baseline:** `docs/requirements/http_api.md` §§4–9, 13; component requirements и ADR, перечисленные в [requirements.md](requirements.md), действующий код и тесты на входном commit. Макеты содержат демонстрационные числа и не являются oracle.

## Вывод для Manager и владельца

Владелец [сузил M1-7](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179357890) до **трёх публичных групп: точки, дома, аспекты**. Они уже входят в `ChartDTO`, который возвращается после committed POST и при восстановленном GET current. Новых endpoint, расчёта в браузере и расширения публичного DTO для этого объёма не требуется. Внутренний движок уже рассчитывает конфигурации и силу, в том числе degree flags; их отсутствие в текущем публичном DTO не следует путать с отсутствием расчёта. Прежнее предложение `REQ-API-UI-01…03` о публикации трёх дополнительных групп снято с объёма M1-7. До допуска Developer Manager должен привести принятый шестигрупповой `DP-UI-01`, открытый `DP-UI-02`, roadmap и задания ролям к новому решению владельца. Analyst не меняет записи других ролей.

Владелец уточнил порядок для **закрытого стенда**: checkbox исходно снят; POST возможен после **ручной** отметки и до готовности отдельной страницы; страницу нужно поставить до распространения ссылки другим людям. Это ответ владельца от 2026-10-05 на прямой вопрос после [комментариев 1](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179344108) и [2](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179370676). Последнее уточнение владельца: **ADR-0034 не менять, страницу внести в технический долг**. §2 ADR требует ручную отметку до POST, но подготовку и проверку отдельной страницы относит к M1-9 как условие до публичного трафика. Прежний вывод Analysis о запрете каждого build до страницы и необходимости ревизии ADR был чрезмерным. AS-UI-20 проверяет checkbox gate, AS-UI-21 — закрытый этап и возврат к долгу страницы. Отметка остаётся presentation gate, а не юридическим согласием.

**Вопросы для G2:** (1) Manager оформляет изменение `DP-UI-01/02` и roadmap для трёх групп; (2) Manager фиксирует решение владельца в `DP-UI-04` и назначает технический долг страницы M1-9 с контрольной границей до распространения ссылки; (3) владелец закрывает `DP-UI-05` по имени и кнопке. Обозначение предмета ознакомления до страницы уточняется в review. `admin1_name` остаётся по `DP-UI-03` с экранной подписью «регион». Утверждённой стоимости и даты Developer/Tester пока нет.

**Бюджет Analysis:** исходный целевой 1 рабочий день был достаточен для первичного G1 draft при готовом пакете чтения. Review, смена scope, оформление долга и чистовой перенос требуют отдельного времени Analyst; прежняя оценка 1,5–2,5 дня собственной работы остаётся ориентиром, а не обещанным сроком. Календарное ожидание решений владельца и Manager отдельно.

## Сложность реализации и срок

В репозитории есть FastAPI `bootstrap`, `places`, `build`, `current`, но нет production браузерного экрана: `docs/ui_ux/README.md` называет `web-prototype.html` демонстрацией, а `src/exact_orb/http_api/app.py` подключает API routers. Владелец [увеличил целевой бюджет Development до 4 рабочих дней](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179346983). Это **владелецкий target**, не estimate Developer и не изменение Manager-owned плана. Сужение до трёх групп убирает публичную DTO-дельту, но не устраняет работу по форме, сессии, поиску, recovery и адаптивному экрану.

| Драйвер | Минимальная работа в M1-7 | Нужная оценка/evidence |
|---|---|---|
| Браузерная интеграция | Подключить реальную страницу к существующим API и cookie flow; отделить bootstrap от current и committed от `already_applied`. | Developer указывает стек, work items, диапазон, confidence и критический путь; Tester проверяет HTTPS/browser evidence. |
| Форма и место | Дата → место → время; GET начиная с трёх букв, debounce, актуальный ответ, фиксация `place_id`, известное/неизвестное время. | Проверить выбор клавиатурой и мышью, ошибочный и пустой поиск, запрет POST без ID. |
| Факты и восстановление | Три группы из текущего `ChartDTO`, `ДД°ММ′`, natal/cosmogram, empty/stale/unavailable, две вкладки и неопределённый исход build. | Tester связывает POST/current по `chart_identity`, проверяет ошибки и 360 px; никакого нового API блока. |
| Gate условий и долг страницы | ADR-0034 требует снятый по умолчанию checkbox и ручную отметку до POST; страницу предусматривает в M1-9 до публичного трафика. | Закрытый этап проверяется по AS-UI-20/21; Manager записывает `DP-UI-04` и технический долг страницы с границей до распространения ссылки другим людям. |
| Имя и действия | POST принимает только три поля; имя и чат в макете не поддерживаются этим контрактом. | `DP-UI-05` фиксирует финальный состав; не добавлять неработающую кнопку чата. |

**Подписанная рекомендация Functional Analyst — 2026-10-05:** планировать M1-7 как минимальный работающий путь формы и трёх таблиц на текущем API. Developer оценивает 4-дневный target по перечисленным work items и отдельно указывает риск браузерной интеграции; Tester независимо оценивает приёмку checkbox gate и срок возврата к странице. Manager сопоставляет оценки с планом. Колесо остаётся M1-8, полный перенос прототипа — M1-8.1, чат — M2. Новые группы и стихии требуют отдельного будущего scope/контракта; заранее можно продумать их место в макете, без пустых секций в работающем M1-7.

## Уточнение поиска и текста действий

По [r4179366994](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179366994) GET начинается после **третьего введённого символа** и повторяется для изменённого префикса длиной не менее трёх символов после debounce. Для 1–2 символов UI не делает GET, хотя API их принимает; поздний ответ на старый префикс не заменяет актуальные подсказки. REQ-UI-02 и AS-UI-02 содержат проверяемую последовательность.

В [r4179362074](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179362074) владелец спросил о CTA. **CTA = Call to Action, видимая кнопка или призыв к действию** (например, «Построить карту», «Пересчитать»). Это не client agreement и не checkbox условий. В требованиях далее используется «кнопка действия»; окончательный текст и вопрос имени остаются в `DP-UI-05`.

## Трассировка и наблюдаемое поведение

| Требования | Источник | Сценарии | Sequence / проверка |
|---|---|---|---|
| REQ-UI-01, 08 | HTTP §§6.1–6.2; ADR-0040/0041 | AS-UI-01, 10, 11 | `http_api/001`, `004`; `session/002`; нет browser restore evidence |
| REQ-UI-02 | HTTP §§6.3–6.4; place catalog; решение о трёх буквах | AS-UI-02, 04–06, 18 | `http_api/002`; `place_catalog/001`; нет browser selection evidence |
| REQ-UI-03, 09 | HTTP §§4, 8–9; ADR-0034/0040/0041 | AS-UI-03, 06, 12–14, 16, 17, 20, 21 | `http_api/003`, `004`; `session/006`; AS-UI-21 требует закрытого доступа и контроля долга |
| REQ-UI-04–06 | HTTP §7.2; ADR-0029/0030/0032 | AS-UI-07–09, 15, 16 | `http_api/003`, `004`; текущие `test_projectors.py` без браузерных таблиц |
| REQ-UI-07, 10 | UI/UX draft и owner review | AS-UI-02, 19 | Место будущих секций только в макете; browser/mobile evidence ожидается |

1. **Вход и восстановление:** браузер → `POST /session/bootstrap {}` → `ContextService.load/create` → `ready`; браузер → `GET /charts/current` → `ContextService.load` → `session_view` → `empty/ready/stale/unavailable`. Чтение не вызывает engine/cache и не пересчитывает карту.
2. **Поиск и выбор:** после трёх символов → `GET /places` → admission → `PlaceSearch.search` → подсказки → локальный выбор `place_id`. Cookie не требуется; сборка использует ID, а не строку.
3. **Build:** после действующего gate → transport validation/cookie/admission → `ApplicationOrchestrator.execute(run_id=request_id)` → `ContextService.load` → `BuildNatalHandler.handle` → resolver → artifact/to_stored → `ContextService.save` → committed `ChartDTO`. `already_applied` требует отдельный current GET.
4. **Recovery:** `RESULT_SUPERSEDED`/`already_applied` → current; `SESSION_* 409` → bootstrap → current; `STATE_COMMIT_FAILED` → current после `Retry-After`; `BUILD_TIMEOUT` → readiness/restart → bootstrap → current после `Retry-After`. Автоматического второго POST нет.

Существующие sequence diagrams `docs/sequence_diagrams/http_api/001`…`004`, `place_catalog/001`, `session/002/006` описывают серверный путь; новая публичная схема и её изменение в диаграммах для M1-7 не предлагаются. Существенные переходы должны наблюдаться как связанные `http_message send/receive` или terminal/error с request/run ID по действующим ADR логирования; полного payload на INFO не требуется. UI-действия подтверждаются browser evidence, не каждым нажатием в серверном журнале.

## Findings Intake и рекомендации к решениям

### FIND-UI-001. В публичном DTO нет трёх ранее подтверждённых групп

**Type:** requirement gap после прежнего шестигруппового `DP-UI-01`. **Severity/impact:** blocking для согласованности scope и передачи Developer, но не требует новой схемы для трёх групп. **Owner:** Manager для синхронизации scope, владелец для решений `DP-UI-01/02`. **Status:** OPEN до обновления реестра; после этого не блокирует сокращённый M1-7.

`http_api.md` §7.2 и whitelist projector публикуют точки, дома и аспекты; внутренний artifact содержит конфигурации/силу/флаги, но не отдаёт их UI. Прежний G1 предложил DTO-дельту, потому что тогда действовал шестигрупповой scope. Новый [комментарий владельца](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179357890) выбирает три группы и исключает дельту из M1-7. **Рекомендация Functional Analyst:** Manager обновляет `DP-UI-01/02`, roadmap и роли; Developer использует только текущий `ChartDTO`; будущие группы получают отдельное решение с POST/current parity. **Закрытие:** записанный owner scope и синхронизированный план; не объявлять finding закрытым по одному комментарию.

### FIND-UI-002. Нужна фиксация этапа страницы условий

**Type:** staging/debt tracking gap. **Severity/impact:** не блокирует build на закрытом стенде при ручной отметке; блокирует распространение ссылки до поставки страницы и формальный handoff, пока Manager не запишет решение. **Owner:** владелец (`DP-UI-04`), Manager (реестр и долг M1-9). **Status:** OPEN до записи и проверки условий.

ADR-0034 §2 предусматривает отдельную страницу M1, однако прямо оставляет её подготовку и проверку M1-9 как условие до публичного трафика; до POST требует ручную отметку. В review сначала прозвучало «отжатую», затем «не отжатый», а в прямом ответе владелец уточнил: checkbox снят, POST после ручной отметки, страница до распространения ссылки. Последнее указание владельца — ADR не менять, страницу отложить как технический долг. **Рекомендация Functional Analyst:** Manager записывает в `DP-UI-04` этап закрытого стенда, отдельный долг страницы с составом ADR §2, ответственным и условием возврата до распространения ссылки; Tester проверяет AS-UI-20/21. Предмет ознакомления в закрытой форме должен быть понятен пользователю и уточняется в review. **Закрытие finding:** запись решения и долга, evidence checkbox gate для закрытого этапа; сам долг закрывается позже поставкой и проверкой страницы.

**Предложение Analysis для промежуточного текста:** до отдельной страницы показать рядом с checkbox краткую сводку пунктов ADR-0034 §2 прямо в форме, чтобы ручная отметка относилась к видимой информации. Не использовать формулировку макета «согласие на обработку персональных данных». Точную копию, контакт и ссылку на исходный код согласовать в `DP-UI-04/05`; это предложение не заменяет долг отдельной страницы.

**Кандидат долга для регистрации Manager — `DEBT-UI-001`:** отдельная страница «Условия использования сервиса» в M1-9, доступная из формы; содержание — минимум ADR-0034 §2, без подмены юридического согласия. В карточке долга нужны владелец, связь с `DP-UI-04`/ADR-0034, проверка доступности и содержимого Tester, а также stop condition: не распространять ссылку другим людям и не открывать публичный трафик, пока страница не поставлена и не проверена. Это предложение Analysis, не созданная Manager-owned запись.

### FIND-UI-003. Макеты содержат неподтверждённые поля, кнопки и числа

**Type:** draft/source conflict. **Severity/impact:** blocking для окончательного состава формы; ложное обещание чата или дополнительное поле нарушит проверяемый UI/API flow. **Owner:** владелец (`DP-UI-05`), UI/UX для макета. **Status:** OPEN.

Р1 ставит время перед местом и содержит имя/чат; Э4 показывает offset и лунный диапазон при неизвестном времени; Р5/Э7 содержат демо-цифры. `ui_ux/decisions.md` использует устаревшие `ChartDTO/issues`. Владелец [подтвердил](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178774177) порядок дата → место → время. **Рекомендация Functional Analyst:** сохранить только действующие POST поля, пересобрать макет по выбранному порядку, исключить обещание чата и числовые примеры как данные пользователя; объяснить CTA как кнопку действия. **Закрытие:** решение `DP-UI-05`, обновлённый макет и проверка реального UI.

### FIND-UI-004. Черновик UI и будущие группы

**Type:** scope/visual gap. **Severity/impact:** blocking для согласованной визуальной приёмки M1-7, без требования нового HTTP блока. **Owner:** Manager для scope, UI/UX для композиции, Analyst для требований. **Status:** OPEN до синхронизации решения.

Первоначальный `ui_ux/requirements.md` описывал только точки, дома, аспекты и стихии, тогда как старый `DP-UI-01` требовал шесть групп. Владелец теперь [отказался от шести в M1-7](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179357890), но [просит продумать размещение будущих блоков](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4179374962). **Рекомендация Functional Analyst:** REQ-UI-07 оставляет в макете место после аспектов без пустых работающих таблиц и без обещания будущего контракта. **Закрытие:** согласованный трёхгрупповой scope в реестре, адаптированный UI/UX-макет и browser evidence трёх групп.

### Подписанные рекомендации к открытым решениям

| Решение | Рекомендация Functional Analyst, 2026-10-05 | Владелец и статус |
|---|---|---|
| `DP-UI-02` | После сокращения `DP-UI-01` не добавлять в M1-7 endpoint или поля для конфигураций/силы/особых градусов; применить существующий `ChartDTO` с одинаковой семантикой committed POST и restored GET. Возврат остальных групп решать отдельным scope и публичным контрактом. | Владелец публичной семантики; Manager обновляет реестр. OPEN до записи. |
| `DP-UI-04` | Сохранить ADR-0034: для закрытого стенда checkbox снят по умолчанию и вручную отмечается до POST; отдельную страницу с содержанием §2 оформить как долг M1-9 и закрыть до распространения ссылки другим людям и публичного трафика. Tester проверяет оба этапа. | Владелец выбрал порядок; Manager фиксирует его и долг в реестре/плане. OPEN в текущем реестре. |
| `DP-UI-05` | В M1-7 оставить дату, место, время и кнопки «Построить карту»/recovery; имя и кнопку чата не показывать без нового решения. `CTA` в старом макете означает кнопку действия, а не соглашение. | Владелец состава формы; UI/UX обновляет макет. OPEN. |

**Подпись:** Functional Analyst (`analysis/ui-birth-form-and-facts`), 2026-10-05. Эти строки являются рекомендациями, а не заменой реестра или решения владельца.

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

## Карта переноса и handoff

| Объект | Действие после утверждения и поставки | Сейчас |
|---|---|---|
| REQ-UI-01…10, AS-UI-01…21 | Перенести утверждённый UI scope в `docs/requirements/current/ui/birth-form-and-facts.md` и `scenarios.md` после сверки Tester. | Review PR #43; Manager должен записать этап в `DP-UI-04`. |
| HTTP `ChartDTO` | Сохранить действующий `docs/requirements/http_api.md` §7.2 без дельты M1-7; ссылки в UI документах ведут к нему. | Новые блоки отложены за пределы M1-7, отдельное решение потребуется при возврате. |
| ADR-0034 и Manager реестр | ADR не менять; Manager обновляет `DP-UI-01/02/04`, roadmap, сроки и задания, регистрирует отдельную страницу как долг M1-9 с триггером до распространения ссылки. | Analyst не меняет эти файлы. |

Manager получает [requirements.md](requirements.md), [scenarios.md](scenarios.md), [analysis.md](analysis.md), входной `652bd734`, четыре findings, блокирующие решения и бюджетный вывод. Для Developer/Tester передаётся только review-версия; `READY_FOR_DEVELOPMENT`, approval и merge не заявляются.

**Исторические проверки G1:** `git ls-remote origin refs/heads/change/ui-birth-form-and-facts` и `git diff --check` прошли для `101d628f83a3cdda529dc925dfdde2e370fcc6af`; тогда были 13 требований и 19 сценариев. Review-редакция в `6187fd5` добавила AS-UI-20. Проверки текущей редакции фиксируются в итоговом отчёте после запуска; pytest и browser/HTTPS acceptance для документной правки не подменяются текстом требования.
