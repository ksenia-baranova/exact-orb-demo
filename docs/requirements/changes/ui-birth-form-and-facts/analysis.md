# Functional Analysis: ui-birth-form-and-facts

**Статус G1:** READY FOR REVIEW, без разрешения разработки или приёмки build. **Роль:** Functional Analyst.
**Вход:** `change/ui-birth-form-and-facts` и `origin/change/ui-birth-form-and-facts` @ `652bd73405db0a0611e98e81af6f3f668dd429f6`, merge manager PR #42 (удалённый HEAD отдельно проверен `git ls-remote` 2026-10-04). Рабочая ветка `analysis/ui-birth-form-and-facts` создана от этого commit. Прежний `956a0d3` внутри manager brief — исторический baseline подготовки, не фактический вход роли.
**Нормативная база:** `docs/requirements/http_api.md` §§4–9, 13; названные в [requirements.md](requirements.md) component requirements и ADR @ входном commit. **Реестр:** `docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register` @ входном commit, с Analyst-рекомендациями текущей analysis-ветки; только `DP-UI-01/03` уже имеют решение владельца.
**Артефакты:** [requirements.md](requirements.md) (`FULL` новая UI область + предлагаемая `DELTA` HTTP), [scenarios.md](scenarios.md) (AS-UI-01…20), этот документ. Ссылки относятся к совместно версионируемым файлам ветки Analysis; до approval они предназначены для review, а не для реализации по утверждённой версии.

## Кратко для Change Manager

Цель `DP-UI-01` достижима только после публикации отсутствующих конфигураций, силы и особых градусов в типизированном `ChartDTO`. Действующие POST и current должны передавать одинаковые факты, иначе восстановление показывает меньше, чем первый build. Предлагаемый минимальный публичный срез и `null`/`[]` подробно изложены в REQ-API-UI-01…03; решение остаётся за владельцем `DP-UI-02` после Developer/Tester consultation.

Действующий ADR-0034 уже требует снятый по умолчанию presentation checkbox перед отправкой build, а roadmap ставит страницу условий в M1-9 после M1-7. Результат «работающая форма с реальным POST» не может быть принят в M1-7 при простом пропуске checkbox. В review PR #43 владелец указал желаемую альтернативу: заранее отметить checkbox и показать страницу после первого расчёта. Для неё нужны явная ревизия ADR-0034 с Technical Reviewer и обновление `DP-UI-04`; до этого действует прежний gate. Имя и CTA чата из макета не входят в текущий POST; `DP-UI-05` остаётся за пользователем. Остальные M1-6 findings, включая `FIND-TEST-HTTP-001`, этим анализом не переоткрываются.

**Блокирующие до `READY_FOR_DEVELOPMENT`:** `DP-UI-02`, `DP-UI-04`, `DP-UI-05` по manager register. **Неблокирующие:** отложенный `DP-UI-03` (`admin1_name` остаётся), известное browser evidence ограничение локального proxy. **Запрос Developer:** feasibility новой whitelist-проекции, безопасная ссылочная целостность и действующий web/HTTPS стек; диапазон 2 дней с допущениями. **Запрос Tester:** независимые negative/boundary cases и проверяемость POST/current parity, браузерного cookie flow и 360 px; диапазон 2 дней с допущениями.

**Вывод о бюджете:** 1 рабочий день реалистичен как целевой бюджет на первичный G1 draft при готовом пакете manager; он не покрывает ожидание решений `DP-UI-02/04/05`, согласование точной схемы с Developer/Tester, возможную ревизию ADR и чистовой перенос после реализации. Для полного Analysis до утверждённого контракта и последующей сверки чистовой редакции нужен ориентир **1,5–2,5 рабочих дня собственной работы Analyst**, confidence medium; календарное ожидание владельцев отдельно. Сокращать шесть групп ради 1 дня нельзя.

## Сложность и сроки: информация владельцу для G2

Оценка ниже — **вывод Functional Analyst по текущему baseline, не estimate Developer/Tester и не изменение плана Manager**. В репозитории есть действующий FastAPI с `bootstrap`, `places`, `build`, `current`, но нет production браузерного UI: `docs/ui_ux/README.md` прямо называет `web-prototype.html` демонстрацией с вымышленными данными, а `http_api/app.py` подключает только API routers. Поэтому утверждённые 2 рабочих дня Development — цель с высоким риском превышения, пока Developer не покажет способ поставки UI и разбиение работ. Из имеющихся фактов нельзя честно вывести новую точную дату.

| Драйвер | Почему влияет на срок | Наименьшая подтверждённая граница работы / нужная проверка |
|---|---|---|
| Публичные факты `DP-UI-02` | Текущий `ChartDTO` и whitelist projector публикуют точки, дома и аспекты, но не конфигурации, силу и флаги. Нужны типы, ссылочная целостность, натал/космограмма и одинаковый POST/current. | Рекомендация Analysis — расширить существующий `ChartDTO` и общий projector. Отдельный endpoint добавит ещё один contract/flow и проверки; его стоимость должен сопоставить Developer. Шесть групп остаются scope `DP-UI-01`. |
| Реальный браузерный экран | Демо-прототип не подключён к API; потребуются форма, cookie flow, выбор `place_id`, шесть групп, ошибки/recovery, доступность и 360 px. | Поставить минимальный рабочий экран формы и таблиц M1-7, без SVG-колеса M1-8, полного переноса прототипа M1-8.1, чата M2 и дополнительных CLI-блоков. Developer должен указать стек и точки интеграции, Tester — browser evidence. |
| Условия `DP-UI-04` | ADR-0034 требует страницу и снятую отметку до POST, roadmap относит самостоятельную страницу к M1-9. | Перенос необходимой части M1-9 в M1-7 меняет распределение, но не обязан дублировать её в M1-9; вариант ожидания M1-9 отложит приёмку build; изменение ADR требует отдельного решения и проверки, его экономия времени не доказана. |
| Имя и будущие CTA `DP-UI-05` | Новый ввод/хранение имени либо неработающий чат расширяют UI и тесты без поддержки текущего POST. | Для минимального M1-7 Analysis рекомендует только действующие поля build и CTA карты; выбор остаётся за владельцем. |

**Запрос на техническую консультацию:** Developer до обещания двух дней указывает для каждого драйвера work items, диапазон, confidence, assumptions и критический путь; при необходимости проводит ограниченный feasibility spike на соединение браузерного экрана с API и новую projection. Tester отдельно оценивает объём независимой приёмки. Manager сопоставляет эти оценки с целевыми 1/2/2 днями и выбранным `DP-UI-04`: перенос gate на M1-9 меняет дату приёмки M1-7, даже если код формы сделан раньше. Ускорение за счёт исключения подтверждённых трёх групп не допускается без нового решения владельца об изменении `DP-UI-01`.

## Уточнение по поиску места из review

В [r4178096178](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178096178) и [r4178749793](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178749793) владелец спросил, отправляется ли GET с первой буквы и с каждым новым префиксом. Действующий API допускает односимвольный запрос и ищет по префиксу; точный порог запуска браузерного поиска действующими требованиями не утверждён. **Вариант A:** с первого непустого символа после debounce — ранние подсказки, потенциально больше запросов к общему IP-limit 120/мин. **Вариант B:** с двух символов после debounce — меньше запросов, позже появляются подсказки. Разница реализации невелика относительно четырёх драйверов выше; рекомендация Analysis — A при подтверждении UI/UX и Developer по нагрузке. До подтверждения REQ-UI-02 и AS-UI-02 требуют актуальный префикс, отсутствие поздних устаревших ответов и выбор `place_id`, но не делают первую букву обязательной. Это UX-уточнение не является принятым `DP-UI-*` и не задерживает техническую консультацию по `DP-UI-02`.

## Подтверждённые факты и предлагаемая граница

| Вид | Утверждение | Источник @ входном commit |
|---|---|---|
| Принято владельцем | Шесть групп M1-7; прежний `admin1_name` без переименования | `DP-UI-01/03` в едином реестре |
| Нормативный факт | Bootstrap отделён от current; POST committed и GET restored используют `ChartDTO`; `already_applied` без chart | `http_api.md` §§6–7; ADR-0040/0041; `routes/session.py`, `routes/build.py` |
| Нормативный факт | Неизвестное время даёт cosmogram без домов/углов/силы; аспекты и конфигурации устойчивы по ADR-0032 | ADR-0008/0032; `engine/charts/natal.py`; golden cosmogram fixture |
| Нормативный факт | Текущий projector исключает configurations/strength; `degree_in_sign` не входит в PointDTO, но `longitude` входит | `http_api.md` §7.2; `dto.py`, `projectors.py`, `test_projectors.py` |
| Нормативный факт | ADR-0034 требует checkbox до UI build; страница условий стоит M1-9 | ADR-0034 §§2–3; `roadmap.md` M1-7/M1-9 |
| Предложение Analysis | Типизированные `configurations`, `strength`, `special_degrees` с одинаковой POST/current семантикой | REQ-API-UI-01…03, ожидает `DP-UI-02` |
| Неизвестное | Утверждённый текст условий/место в M1-7, окончательные имя и CTA, техническая стоимость полного UI | `DP-UI-04/05`, консультации Developer/Tester |

## Трассировка требования → источник → сценарий → sequence → проверка

| Требования | Источник | Сценарии | Существующий sequence | Evidence / gap |
|---|---|---|---|---|
| REQ-UI-01, 08 | HTTP §§6.1–6.2; ADR-0040/0041 | AS-UI-01, 10, 11 | `http_api/001`, `004`; `session/002` | `tests/http_api/test_session.py`; browser UI отсутствует |
| REQ-UI-02 | HTTP §§6.3–6.4; place catalog; ADR-0008 | AS-UI-02, 04–06, 18 | `http_api/002`; `place_catalog/001` | `test_place_dto.py`; нет UI selection evidence |
| REQ-UI-03, 09 | HTTP §§4, 8–9; ADR-0040/0041 | AS-UI-03, 06, 12–14, 16, 17 | `http_api/003`, `004`; `session/006` | `test_integration.py`, `test_session.py`; UI recovery отсутствует |
| REQ-UI-04, 05 | HTTP §7.2; ADR-0029/0030; `zodiac_position` | AS-UI-07–09, 15 | `http_api/003`, `004` | `test_projectors.py` покрывает текущий DTO; нет табличного UI |
| REQ-UI-06 | ADR-0031/0032; `Configuration` | AS-UI-07–09, 15 | `http_api/003`, `004` | golden artifacts имеют фигуры; публичного блока нет — FIND-UI-001 |
| REQ-UI-07 | `NatalStrength`, `DegreeFlag`, CLI formatter | AS-UI-07–09, 15 | `http_api/003`, `004` | golden natal имеет силу/flags; публичных блоков нет — FIND-UI-001 |
| REQ-UI-10 | `ui_ux` draft и макеты | AS-UI-02, 19 | пользователь → `http_api/001`…`004` | browser/mobile evidence требуется Tester |
| REQ-API-UI-01…03 | HTTP §7.2 + whitelist projector | AS-UI-07–11, 15, 16 | `http_api/003`, `004` | новая схема/тесты ожидают `DP-UI-02` и Developer |

## Поведенческие/API последовательности и журнал

1. **Вход/restore:** browser → `POST bootstrap {}` → `ContextService.load/create` → `ready`; browser → `GET current` → `ContextService.load` → `session_view` → `empty/ready/stale/unavailable`. На INFO: начало/итог каждого HTTP request, пары `http_message` у фактических переходов; safe unavailable дополнительно ERROR без payload. Ни bootstrap, ни current не обращаются к engine/cache.
2. **Поиск/выбор:** ввод → `GET /places` → admission → `PlaceSearch.search` → suggestions → локальный выбор `place_id`. Парные `http_message` для admission и search; запрос не читает cookie. Следующий build использует выбранный ID, а не строку.
3. **Build:** действие пользователя после gate → transport validation/cookie/admission → `ApplicationOrchestrator.execute(run_id=request_id)` → `ContextService.load` → `BuildNatalHandler.handle` → resolver → artifact/to_stored → `ContextService.save` → committed `ChartDTO`. В журнале существенны send/receive или terminal/error каждого перехода, не только start/finish. Первая ошибка до CAS не должна выглядеть как commit.
4. **Recovery:** `already_applied`/`RESULT_SUPERSEDED` → current; `SESSION_* 409` → bootstrap → current; `STATE_COMMIT_FAILED` → current после 1 s; `BUILD_TIMEOUT` → readiness/restart → bootstrap → current после 5 s. Ни один путь не создаёт auto POST. Логи отдельного GET имеют новый request ID; связать пользовательский intent можно по сохраняемым ответам/`chart_identity`, но не требовать публикации полного payload на INFO.

Это функциональная привязка к существующим `docs/sequence_diagrams/http_api/001`…`004`, `place_catalog/001` и `session/002/006`; внутренний порядок middleware/ownership остаётся Developer. После выбора `DP-UI-02` обновляются действующие диаграммы `003`/`004` в части новой проекции. В этом G1 дельта меняет только будущий состав ChartDTO, не действующую последовательность HTTP/сессии.

## Findings Intake: полная диспозиция

### FIND-UI-001. Три подтверждённые группы отсутствуют в публичном DTO

**Type:** requirement gap. **Detected by:** Manager intake, подтверждено Functional Analyst. **Owner:** пользователь (`DP-UI-02` — семантика), Developer (реализация после gate). **Status:** OPEN. **Blocks:** полный M1-7 contract и `READY_FOR_DEVELOPMENT`.

- **Где найдено:** `roadmap.md` M1-7 и принятое `DP-UI-01`; `http_api.md` §7.2 явно исключает strength/configurations; `dto.py`/`projectors.py` публикуют только четыре массива/блока, `test_projectors.py` закрепляет whitelist.
- **Пример:** golden natal 1985 содержит 6 конфигураций, `strength` и 31 degree flag, но `project_chart()` их не возвращает. Браузер с текущим API не покажет три группы и не должен читать внутренний artifact.
- **Почему контракт недостаточен:** неизвестны публичная вложенность, порядок, разрешение ссылок, `null`/`[]`, особые градусы и равенство двух HTTP путей.
- **Влияние:** невозможна шестигрупповая приёмка; оценка Development 2 дня без схемы недостоверна. Нельзя подменить реальный результат вычислением в UI.
- **Дальше:** решение `DP-UI-02` после консультаций; Developer уточняет типизированную projection и tests POST/current, Tester проверяет parity/negative controls.
- **Условие закрытия:** accepted строка реестра, актуальный HTTP контракт, реализация, тесты и browser evidence всех шести групп на одном tested commit. **Closure evidence:** ожидается.

### FIND-UI-002. ADR-0034 опережает roadmap M1-9

**Type:** conflict/process gate. **Detected by:** Manager intake, подтверждено Functional Analyst. **Owner:** пользователь (`DP-UI-04`), Technical Reviewer при ревизии ADR. **Status:** OPEN. **Blocks:** отправку UI build и её финальную приёмку.

- **Где найдено:** ADR-0034 §§2–3 требует отдельную страницу условий и неотмеченный checkbox до POST; `roadmap.md` назначает страницу/checkbox M1-9, после работающей формы M1-7. На Э1 есть иной текст «согласия», который не является утверждённым условием ADR.
- **Пример:** пользователь нажимает «Построить карту» в M1-7 без доступной страницы условий или с заранее отмеченным/юридически названным checkbox — UI нарушает действующий ADR.
- **Комментарий владельца на review:** [PR #43, r4178769729](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178769729) выбирает желаемую последовательность: отложить страницу до первого расчёта и заранее отметить checkbox. Это явное продуктовое намерение владельца, но оно противоречит ADR-0034 §2 и само по себе не заменяет принятое ADR. Пока Technical Reviewer/владелец не оформят явную ревизию ADR и Manager не обновит `DP-UI-04`, требования и AS-UI-20 сохраняют действующий gate; отправка build остаётся блокированной.
- **Почему контракт недостаточен:** комментарий владельца указывает желаемый staging, но Manager-owned реестр и действующий ADR не обновлены. Без явной ревизии ADR нельзя считать заранее отмеченный checkbox и позднюю страницу разрешённым build-flow. Presentation gate не является доказательством юридического согласия и не сохраняется в M1.
- **Влияние:** полный happy path и браузерный тест заблокированы; перенос работ изменит сроки/scope. Нельзя принять безусловную отправку как временную реализацию.
- **Дальше:** Manager фиксирует комментарий владельца в `DP-UI-04` и организует согласование ревизии ADR-0034 с Technical Reviewer; Developer оценивает staging, Tester — проверяемость нового gate после утверждения.
- **Условие закрытия:** запись решения владельца в реестре, явная ADR revision с нужным содержанием/порядком страницы и проверяемый тест согласованного gate перед POST. **Closure evidence:** комментарий PR есть; реестр, ADR и тест ожидаются.

### FIND-UI-003. Макеты включают неподтверждённые поля, CTA и числа

**Type:** draft/source conflict. **Detected by:** Manager intake, подтверждено Functional Analyst визуальной сверкой. **Owner:** пользователь (`DP-UI-05`), Analyst — синхронизация требований после решения. **Status:** OPEN. **Blocks:** финальный состав формы, но не анализ действующего API.

- **Где найдено:** Р1 ставит время перед местом и содержит имя/чат; Р2/Э3 содержат колесо и CTA M2; Э4 показывает offset и диапазон Луны без публичного источника; `render_review.md` отмечает предметные ошибки Р1/Р2; Р5/Э7 содержат демо-цифры. `ui_ux/decisions.md` использует устаревшие `ChartDTO` и `issues`.
- **Пример:** имя из Э1 добавлено к POST, который запрещает extra fields → 422; Э4 показывает «UTC+4» при `birth_time:null`, хотя `BirthViewDTO.utc_offset_seconds=null`.
- **Почему контракт недостаточен:** без решения пользователь может воспринять неработающий чат/имя как обещание. Композиция макета сама не устанавливает публичный API.
- **Влияние:** ложное UI обещание, некорректный request, неверные факты при неизвестном времени. Визуальная приёмка должна отделять данные от оформления.
- **Дальше:** `DP-UI-05`; убрать неутверждённые действия из G1-предложения, сохранить композицию/палитру/ритм для Tester. Действующий `IssueDTO` — `field/code/candidates?/constraints?`.
- **Комментарий владельца на review:** [PR #43, r4178774177](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178774177) подтверждает порядок дата → место → время и поручает переделать макет. REQ-UI-02 уже следует этому порядку; изменение визуального файла остаётся у UI/UX-владельца. Вопрос имени и CTA в `DP-UI-05` этим комментарием не решён.
- **Условие закрытия:** решение владельца о поле имени/CTA и проверенный UI без недействующих действий/демо-фактов. **Closure evidence:** ожидается.

### FIND-UI-004. Черновик UI не описывает полный набор таблиц

**Type:** missing requirement. **Detected by:** Manager intake, подтверждено Functional Analyst. **Owner:** Functional Analyst для текста; пользователь/Developer для открытого `DP-UI-02`. **Status:** IN REVIEW. **Blocks:** тестируемый scope M1-7 до review.

- **Где найдено:** `ui_ux/requirements.md` §6 описывает planets/houses/aspects и отдельные стихии, но не структуру конфигураций, силы и special degrees; CLI показывает текущие расчётные блоки; `ChartDTO` их не публикует.
- **Пример:** chart с бисекстилем и флагом Меркурия получает только первые три таблицы, хотя `DP-UI-01` подтвердил шесть.
- **Почему контракт недостаточен:** отсутствуют применимость к cosmogram, порядок, пустые состояния, значения позиции и проверка восстановленного GET.
- **Влияние:** Developer/Tester могли бы считать три секции готовым M1-7. Требования REQ-UI-04…07 и AS-UI-07…09 закрывают аналитический пробел для review, но публичная схема ещё не принята.
- **Дальше:** review Analysis, решение `DP-UI-02`, реализация и независимая проверка. Дополнительные CLI-блоки (интерцепции, управители, баланс, фаза, рецепции) не становятся scope без решения.
- **Комментарий владельца на review:** [PR #43, r4178776260](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178776260) подтверждает адаптацию макета к принятому объёму из шести групп. Обновлённый макет и browser evidence ещё не представлены; finding не закрыт.
- **Условие закрытия:** утверждённые requirements/scenarios с шестью группами и verified acceptance; сейчас только G1 draft. **Closure evidence:** ожидается.

## Визуальный материал и осознанные расхождения

Р1: форма, контраст и основной CTA полезны; порядок дата → место → время подтверждён владельцем в PR #43, а переделка макета ещё предстоит. Имя/чат остаются вопросом `DP-UI-05`; текст юридического согласия и предварительно отмеченный checkbox противоречат действующему ADR-0034 до его явной ревизии. Р2: использовать только пропорции и палитру; колесо M1-8, числовые и геометрические ошибки `render_review.md` не копировать. Р5/Э7: ритм секций и строки фактов применимы, но шесть групп требуют дополнения; «Стихии» и демонстрационные значения не oracle. Э1/Э2: полезны состояния выбора двух Кировсков, стрелки/Enter, ошибка невыбранного места; семантика checkbox берётся из действующего ADR-0034. Э3/Э4: карточка результата допустима, но чат/колесо вне M1-7, UTC offset и лунный диапазон Э4 при неизвестном времени исключены. Э5/Э6: stale и unavailable хорошо различены, однако факты только из `current`. Э7: на 360 px секции и строки не теряют данные; исходные цифры не проверочный эталон.

## Диспозиция review PR #43 от 2026-10-04

Проверены [общий review](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#pullrequestreview-5407511699) и все десять inline threads, включая их текущий unresolved state. Ответы и разрешение threads в GitHub не выполнялись; таблица фиксирует результат Analysis и границу другого владельца.

| Комментарий | Диспозиция | Изменение или оставшийся gate |
|---|---|---|
| [r4178058956](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178058956) | исправлено | REQ-UI-01 и AS-UI-11 называют конкретные safe причины `chart_unavailable` и отличают их от stale/`STATE_READ_FAILED`. |
| [r4178086032](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178086032) | исправлено | REQ-UI-01 прямо указывает, когда UI показывает факты и почему `state_version` bootstrap не заменяет `chart.chart_identity`. |
| [r4178096178](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178096178), [r4178749793](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178749793) | нужен ответ владельца/UX | API допускает односимвольный префикс, но комментарии спрашивают о пороге UI, а не утверждают его. REQ-UI-02 и AS-UI-02 больше не объявляют первую букву принятой; варианты, рекомендация и влияние на нагрузку приведены выше. |
| [r4178129262](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178129262) | исправлено | REQ-UI-03 показывает `already_applied` как тело `200` ответа на POST и отдельный последующий GET. |
| [r4178731223](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178731223) | исправлено как предлагаемая дельта | REQ-API-UI-02 содержит словарь каждого нового атрибута: тип, назначение, русское имя и допустимые enum; утверждение схемы остаётся за `DP-UI-02`. |
| [r4178758579](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178758579) | исправлено | Добавлен AS-UI-20 для неотмеченного checkbox условий. Он не объявляется юридическим согласием на персональные данные по ADR-0034. |
| [r4178769729](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178769729) | нужно решение владельца в нормативном контуре | Желаемое владельцем поведение записано в FIND-UI-002; оно требует явной ревизии ADR-0034 и обновления Manager-owned `DP-UI-04` перед изменением gate. |
| [r4178774177](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178774177) | учтено; UI/UX действие открыто | Порядок дата → место → время уже в REQ-UI-02; владелец подтвердил необходимость переделать макет. |
| [r4178776260](https://github.com/ksenia-baranova/exact-orb-demo/pull/43#discussion_r4178776260) | учтено; UI/UX действие открыто | Владелец подтвердил адаптацию макета к шести группам; FIND-UI-004 остаётся в review до обновления макета и проверки. |

## Карта будущего переноса в current/

| ID | Исходный пункт @ `652bd734` | Действие после approval/поставки | Целевой чистовой пункт | Сейчас |
|---|---|---|---|---|
| REQ-UI-01…10, AS-UI-01…20 | новая UI область; `ui_ux/requirements.md` остаётся draft | FULL ADD, сохранить IDs | `current/ui/birth-form-and-facts.md`, `current/ui/scenarios.md` | review PR #43; ждёт решения DP-UI-04/05 и обновления макета |
| REQ-API-UI-01…03 | `http_api.md` §§6.2, 6.4, 7.2, 13 | DELTA MODIFY/ADD без удаления иных HTTP обязательств | `current/http-api/chart-facts.md`, `current/http-api/scenarios.md`; синхронизировать прежний путь | ждёт DP-UI-02 и Developer/Tester evidence |
| ADR-0034 | действующий ADR, не дельта Analyst | не переносить как новую семантику; возможную ревизию решает владелец | оставить ссылку на ADR | DP-UI-04 открыт |

Чистовая редакция сейчас **не создана**: переносится только утверждённый и поставленный scope после сверки с целевой веткой и Tester; неутверждённые/непоставленные пункты остаются в change с ссылкой на решение. `docs/requirements/http_api.md` нельзя превращать в две противоречивые нормативные копии: при финализации Manager/Analyst согласуют миграцию прежнего пути по `docs/requirements/README.md`.

## Передача G1 и проверки

**Диспозиция review к REQ-UI-01 (2026-10-04): исправить.** Замечание о смешении документных `ADD/MODIFY` с действиями пользователя и неявном потоке открытия страницы принято. В [requirements.md](requirements.md#req-ui-01-первое-открытие-и-источник-состояния) тип изменения отделён от пользовательского действия; bootstrap, current и три варианта ответа разложены по шагам «запрос и ответ → состояние экрана». Тем же способом уточнены выбор места, build, restore и recovery; даны ссылки на соответствующие [сценарии приёмки](scenarios.md). Публичный контракт и статусы `DP-UI-02/04/05` этим review не менялись.

Manager получает три ссылки в начале документа, input commit, `DP-UI-02/04/05`, четыре finding и бюджетный вывод. Developer и Tester получают для review текущий нормативный baseline плюс эту версию, затем точный commit утверждённой версии отдельно. [Draft PR #43](https://github.com/ksenia-baranova/exact-orb-demo/pull/43) существует; `READY_FOR_DEVELOPMENT`, approval и merge здесь не заявлены.

**Выполнено на G1:** `git ls-remote origin refs/heads/change/ui-birth-form-and-facts` → входной SHA выше; `git diff --check` и `git diff 652bd73405db0a0611e98e81af6f3f668dd429f6 --check` → exit 0. Структурная проверка четырёх Markdown файлов: относительные ссылки существуют, таблицы и fences сбалансированы, JSON-примеры разбираются, 13 требований и 19 последовательных сценариев связаны, trailing whitespace не найден. G1 зафиксирован в `101d628f83a3cdda529dc925dfdde2e370fcc6af`; AS-UI-20 и эта диспозиция относятся к последующей review-редакции.

**Проверки review-редакции:** `git diff --check` → exit 0; структурная проверка трёх Analyst Markdown файлов → 56 ссылок без ошибочных якорей, семь таблиц requirements и остальные таблицы согласованы, JSON разбирается, 13 требований и 20 последовательных сценариев, без trailing whitespace или незакрытых fences. Прямой вызов `normalize_place_query("К")` → `к`, `normalize_place_query("Ки")` → `ки`, что подтверждает допустимость односимвольного префикса. Исполняемое browser evidence будущего UI не заявляется.

**Не выполнялось:** pytest, browser/HTTPS acceptance, PlantUML rendering — G1 меняет только документацию и не утверждает работоспособность будущего UI. Известный `FIND-TEST-HTTP-001` прежнего change учитывается при планировании браузерной проверки, не квалифицируется заново как defect M1-7.
