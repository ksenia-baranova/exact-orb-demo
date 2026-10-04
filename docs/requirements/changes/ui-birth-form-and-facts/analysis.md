# Functional Analysis: ui-birth-form-and-facts

**Статус G1:** READY FOR REVIEW, без разрешения разработки или приёмки build. **Роль:** Functional Analyst.
**Вход:** `change/ui-birth-form-and-facts` и `origin/change/ui-birth-form-and-facts` @ `652bd73405db0a0611e98e81af6f3f668dd429f6`, merge manager PR #42 (удалённый HEAD отдельно проверен `git ls-remote` 2026-10-04). Рабочая ветка `analysis/ui-birth-form-and-facts` создана от этого commit. Прежний `956a0d3` внутри manager brief — исторический baseline подготовки, не фактический вход роли.
**Нормативная база:** `docs/requirements/http_api.md` §§4–9, 13; названные в [requirements.md](requirements.md) component requirements и ADR @ входном commit. **Реестр:** `docs/project_management/change_plans/ui-birth-form-and-facts/artifacts.md#decision-register` @ входном commit, с Analyst-рекомендациями текущей analysis-ветки; только `DP-UI-01/03` уже имеют решение владельца.
**Артефакты:** [requirements.md](requirements.md) (`FULL` новая UI область + предлагаемая `DELTA` HTTP), [scenarios.md](scenarios.md) (AS-UI-01…19), этот документ. Ссылки относятся к совместно версионируемым файлам ветки Analysis; до approval они предназначены для review, а не для реализации по утверждённой версии.

## Кратко для Change Manager

Цель `DP-UI-01` достижима только после публикации отсутствующих конфигураций, силы и особых градусов в типизированном `ChartDTO`. Действующие POST и current должны передавать одинаковые факты, иначе восстановление показывает меньше, чем первый build. Предлагаемый минимальный публичный срез и `null`/`[]` подробно изложены в REQ-API-UI-01…03; решение остаётся за владельцем `DP-UI-02` после Developer/Tester consultation.

Действующий ADR-0034 уже требует снятый по умолчанию presentation checkbox перед отправкой build, а roadmap ставит страницу условий в M1-9 после M1-7. Результат «работающая форма с реальным POST» не может быть принят в M1-7 при простом пропуске checkbox. `DP-UI-04` требует решения пользователя и проверки Technical Reviewer, если меняется ADR/security boundary. Имя и CTA чата из макета не входят в текущий POST; `DP-UI-05` остаётся за пользователем. Остальные M1-6 findings, включая `FIND-TEST-HTTP-001`, этим анализом не переоткрываются.

**Блокирующие до `READY_FOR_DEVELOPMENT`:** `DP-UI-02`, `DP-UI-04`, `DP-UI-05` по manager register. **Неблокирующие:** отложенный `DP-UI-03` (`admin1_name` остаётся), известное browser evidence ограничение локального proxy. **Запрос Developer:** feasibility новой whitelist-проекции, безопасная ссылочная целостность и действующий web/HTTPS стек; диапазон 2 дней с допущениями. **Запрос Tester:** независимые negative/boundary cases и проверяемость POST/current parity, браузерного cookie flow и 360 px; диапазон 2 дней с допущениями.

**Вывод о бюджете:** 1 рабочий день реалистичен как целевой бюджет на первичный G1 draft при готовом пакете manager; он не покрывает ожидание решений `DP-UI-02/04/05`, согласование точной схемы с Developer/Tester, возможную ревизию ADR и чистовой перенос после реализации. Для полного Analysis до утверждённого контракта и последующей сверки чистовой редакции нужен ориентир **1,5–2,5 рабочих дня собственной работы Analyst**, confidence medium; календарное ожидание владельцев отдельно. Сокращать шесть групп ради 1 дня нельзя.

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
- **Почему контракт недостаточен:** текущее планирование не устанавливает, включается ли необходимая часть M1-9 в M1-7, задерживается ли acceptance build или пересматривается ADR. Presentation gate не является доказательством юридического согласия и не сохраняется в M1.
- **Влияние:** полный happy path и браузерный тест заблокированы; перенос работ изменит сроки/scope. Нельзя принять безусловную отправку как временную реализацию.
- **Дальше:** Manager передаёт пользователю `DP-UI-04`; Developer оценивает staging, Tester — проверяемость, Technical Reviewer — границу ADR при варианте пересмотра.
- **Условие закрытия:** выбранный владельцем вариант с evidence, необходимые утверждённые тексты/ADR revision и тест gate перед POST. **Closure evidence:** ожидается.

### FIND-UI-003. Макеты включают неподтверждённые поля, CTA и числа

**Type:** draft/source conflict. **Detected by:** Manager intake, подтверждено Functional Analyst визуальной сверкой. **Owner:** пользователь (`DP-UI-05`), Analyst — синхронизация требований после решения. **Status:** OPEN. **Blocks:** финальный состав формы, но не анализ действующего API.

- **Где найдено:** Р1 ставит время перед местом и содержит имя/чат; Р2/Э3 содержат колесо и CTA M2; Э4 показывает offset и диапазон Луны без публичного источника; `render_review.md` отмечает предметные ошибки Р1/Р2; Р5/Э7 содержат демо-цифры. `ui_ux/decisions.md` использует устаревшие `ChartDTO` и `issues`.
- **Пример:** имя из Э1 добавлено к POST, который запрещает extra fields → 422; Э4 показывает «UTC+4» при `birth_time:null`, хотя `BirthViewDTO.utc_offset_seconds=null`.
- **Почему контракт недостаточен:** без решения пользователь может воспринять неработающий чат/имя как обещание. Композиция макета сама не устанавливает публичный API.
- **Влияние:** ложное UI обещание, некорректный request, неверные факты при неизвестном времени. Визуальная приёмка должна отделять данные от оформления.
- **Дальше:** `DP-UI-05`; убрать неутверждённые действия из G1-предложения, сохранить композицию/палитру/ритм для Tester. Действующий `IssueDTO` — `field/code/candidates?/constraints?`.
- **Условие закрытия:** решение владельца о поле имени/CTA и проверенный UI без недействующих действий/демо-фактов. **Closure evidence:** ожидается.

### FIND-UI-004. Черновик UI не описывает полный набор таблиц

**Type:** missing requirement. **Detected by:** Manager intake, подтверждено Functional Analyst. **Owner:** Functional Analyst для текста; пользователь/Developer для открытого `DP-UI-02`. **Status:** IN REVIEW. **Blocks:** тестируемый scope M1-7 до review.

- **Где найдено:** `ui_ux/requirements.md` §6 описывает planets/houses/aspects и отдельные стихии, но не структуру конфигураций, силы и special degrees; CLI показывает текущие расчётные блоки; `ChartDTO` их не публикует.
- **Пример:** chart с бисекстилем и флагом Меркурия получает только первые три таблицы, хотя `DP-UI-01` подтвердил шесть.
- **Почему контракт недостаточен:** отсутствуют применимость к cosmogram, порядок, пустые состояния, значения позиции и проверка восстановленного GET.
- **Влияние:** Developer/Tester могли бы считать три секции готовым M1-7. Требования REQ-UI-04…07 и AS-UI-07…09 закрывают аналитический пробел для review, но публичная схема ещё не принята.
- **Дальше:** review Analysis, решение `DP-UI-02`, реализация и независимая проверка. Дополнительные CLI-блоки (интерцепции, управители, баланс, фаза, рецепции) не становятся scope без решения.
- **Условие закрытия:** утверждённые requirements/scenarios с шестью группами и verified acceptance; сейчас только G1 draft. **Closure evidence:** ожидается.

## Визуальный материал и осознанные расхождения

Р1: форма, контраст и основной CTA полезны; порядок поля места исправлен относительно draft, имя/чат открыты, текст согласия и предварительно отмеченный checkbox не принимаются. Р2: использовать только пропорции и палитру; колесо M1-8, числовые и геометрические ошибки `render_review.md` не копировать. Р5/Э7: ритм секций и строки фактов применимы, но шесть групп требуют дополнения; «Стихии» и демонстрационные значения не oracle. Э1/Э2: полезны состояния выбора двух Кировсков, стрелки/Enter, ошибка невыбранного места; семантика checkbox берётся из ADR-0034. Э3/Э4: карточка результата допустима, но чат/колесо вне M1-7, UTC offset и лунный диапазон Э4 при неизвестном времени исключены. Э5/Э6: stale и unavailable хорошо различены, однако факты только из `current`. Э7: на 360 px секции и строки не теряют данные; исходные цифры не проверочный эталон.

## Карта будущего переноса в current/

| ID | Исходный пункт @ `652bd734` | Действие после approval/поставки | Целевой чистовой пункт | Сейчас |
|---|---|---|---|---|
| REQ-UI-01…10, AS-UI-01…19 | новая UI область; `ui_ux/requirements.md` остаётся draft | FULL ADD, сохранить IDs | `current/ui/birth-form-and-facts.md`, `current/ui/scenarios.md` | ждёт review и решения DP-UI-04/05 |
| REQ-API-UI-01…03 | `http_api.md` §§6.2, 6.4, 7.2, 13 | DELTA MODIFY/ADD без удаления иных HTTP обязательств | `current/http-api/chart-facts.md`, `current/http-api/scenarios.md`; синхронизировать прежний путь | ждёт DP-UI-02 и Developer/Tester evidence |
| ADR-0034 | действующий ADR, не дельта Analyst | не переносить как новую семантику; возможную ревизию решает владелец | оставить ссылку на ADR | DP-UI-04 открыт |

Чистовая редакция сейчас **не создана**: переносится только утверждённый и поставленный scope после сверки с целевой веткой и Tester; неутверждённые/непоставленные пункты остаются в change с ссылкой на решение. `docs/requirements/http_api.md` нельзя превращать в две противоречивые нормативные копии: при финализации Manager/Analyst согласуют миграцию прежнего пути по `docs/requirements/README.md`.

## Передача G1 и проверки

**Диспозиция review к REQ-UI-01 (2026-10-04): исправить.** Замечание о смешении документных `ADD/MODIFY` с действиями пользователя и неявном потоке открытия страницы принято. В [requirements.md](requirements.md#req-ui-01-первое-открытие-и-источник-состояния) тип изменения отделён от пользовательского действия; bootstrap, current и три варианта ответа разложены по шагам «запрос и ответ → состояние экрана». Тем же способом уточнены выбор места, build, restore и recovery; даны ссылки на соответствующие [сценарии приёмки](scenarios.md). Публичный контракт и статусы `DP-UI-02/04/05` этим review не менялись.

Manager получает три ссылки в начале документа, input commit, `DP-UI-02/04/05`, четыре finding и бюджетный вывод. Developer и Tester получают для review текущий нормативный baseline плюс эту версию, затем точный commit утверждённой версии отдельно. `READY_FOR_DEVELOPMENT`, push, PR, approval и merge здесь не заявлены.

**Выполнено на G1:** `git ls-remote origin refs/heads/change/ui-birth-form-and-facts` → входной SHA выше; `git diff --check` и `git diff 652bd73405db0a0611e98e81af6f3f668dd429f6 --check` → exit 0. Структурная проверка четырёх Markdown файлов: относительные ссылки существуют, таблицы и fences сбалансированы, JSON-примеры разбираются, 13 требований и 19 последовательных сценариев связаны, trailing whitespace не найден. Перед commit проверяется staged snapshot именно этого реестра и трёх Analyst файлов.

**Не выполнялось:** pytest, browser/HTTPS acceptance, PlantUML rendering — G1 меняет только документацию и не утверждает работоспособность будущего UI. Известный `FIND-TEST-HTTP-001` прежнего change учитывается при планировании браузерной проверки, не квалифицируется заново как defect M1-7.
