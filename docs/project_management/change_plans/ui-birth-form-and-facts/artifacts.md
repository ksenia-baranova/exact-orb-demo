# M1-7: артефакты Change Manager

Единый файл изменения `ui-birth-form-and-facts`: черновое описание, реестр решений и задания ролям. Согласованный план и итоговая приёмка добавляются сюда после соответствующих ролевых результатов и проверок.

<a id="change-brief"></a>
## Черновое описание изменения

**Статус изменения:** DRAFT (Intake; это не Change Plan и не разрешение разработки).
**Руководитель изменения:** агент Change Manager в `manager/ui-birth-form-and-facts`.
**Интеграционная ветка:** `change/ui-birth-form-and-facts`.
**Исходный HEAD интеграционной ветки и main:** `956a0d3acbb1536e57535c4689aee57efe607381` (проверен 2026-10-03).
**Единый реестр:** [раздел «Единый реестр решений»](#decision-register), рабочая версия поверх `956a0d3`; собственного commit ещё нет.
**Задания ролям:** [раздел «Задания ролям»](#role-tasks).
**Связанные строки:** `DP-UI-01`…`DP-UI-05`.
**Версия исходных материалов:** все пути ниже проверены в checkout `956a0d3`; изображения просмотрены визуально. После нового commit `change/*` роли повторяют проверку baseline.

### Потребность и подтверждённые рамки

Пользователь хочет ввести дату, выбрать место из подсказок, указать время или явно отметить его неизвестным, построить карту и прочитать её факты в таблицах. Сейчас HTTP API реализован, но web UI отсутствует. Пользователь 2026-10-03 подтвердил **полный набор M1-7 из roadmap**: планеты и точки, дома, аспекты, конфигурации, сила, особые градусы. Подтверждена связка формы с действующими HTTP endpoint и чтение готовых значений карты; UI не пересчитывает астрологические долготы или знаки.

Целевой результат: в браузере человек вводит поддерживаемые данные, видит подсказки места и выбирает `place_id`, выполняет явное построение и читает факты своей карты. После обновления страницы тот же результат восстанавливается по session cookie и `GET /charts/current`, пока сессия жива. Значения таблиц происходят из реального результата API, а не из демонстрационных чисел макетов.

Показанная пользователем длинная дробь `degree_in_sign` относится к внутреннему расчётному объекту: нынешний `PointDTO` уже не передаёт это поле, а публикует целые `degree`/`minute` и числовую `longitude`. UI должен показывать градусы и минуты без длинной дроби; необходимость оставлять `longitude` в расширяемом публичном DTO и влияние на будущий M1-8 уточняются в `DP-UI-02`. Обрезание внутреннего результата расчёта здесь не требуется.

Подтверждение полного набора — `DP-UI-01`. Отложенное переименование `admin1_name` — `DP-UI-03`; эта строка не меняет статус и остальные findings M1-6.

### Входные материалы первичного анализа

| Категория | Фактически прочитанный путь | Почему относится к M1-7 | Версия |
|---|---|---|---|
| Правила | `AGENTS.md` | границы роли, тестирования и архитектуры | `956a0d3` |
| Процесс | `docs/development_approach/skills/change-manager/SKILL.md`; `docs/development_approach/process.md`; `docs/development_approach/roles.md`; `docs/development_approach/development-approach.md` | ownership, gates и ролевой handoff | `956a0d3` |
| Шаблоны | `docs/development_approach/artifacts/change-manager.md`; `docs/development_approach/artifacts/decision-register.md` | формат brief и одного реестра | `956a0d3` |
| Требования | `docs/requirements/README.md`; `docs/requirements/current/README.md`; `docs/requirements/changes/README.md` | где лежит нормативный baseline и куда Analyst переносит change | `956a0d3` |
| Порядок работ | `docs/project_management/roadmap.md` §3.3, M1-6–M1-9 | scope M1-7, границы M1-8/M1-8.1/M1-9 | `956a0d3` |
| Статус смежного change | `docs/project_management/change_plans/http-api-and-session-middleware.md`; `docs/testing/http-api-and-session-middleware/tester.md`; `docs/requirements/overview.md` §2.1 | реализованный API, известный статус `PARTIAL` и `FIND-TEST-HTTP-002` | `956a0d3` |
| Публичный контракт | `docs/requirements/http_api.md` §§6–9, 13 | bootstrap/current, places, build, DTO, ошибки и recovery | `956a0d3` |
| UI, статус | `docs/ui_ux/README.md`; `docs/ui_ux/render_review.md`; `docs/ui_ux/decisions.md` | прототип — черновик; ошибки рендеров и открытые предложения | `956a0d3` |
| UI, поведение | `docs/ui_ux/requirements.md` §§4–6, 9–13 | форма, таблицы, состояния, клавиатура и mobile | `956a0d3` |
| Визуальный просмотр | `docs/ui_ux/renders/r1-input.png`; `r2-chart-ready.png`; `r5-chart-detail.png` | композиция формы, готовой карты и таблиц | `956a0d3` |
| Визуальный просмотр | `docs/ui_ux/mobile/e1-input.png`; `e2-place-suggestions.png`; `e3-chart-ready.png`; `e4-time-unknown.png`; `e5-chart-stale.png`; `e6-chart-unavailable.png`; `e7-chart-detail.png` | мобильная форма, поиск, готовность, неизвестное время, восстановление и таблицы | `956a0d3` |
| ADR | `docs/requirements/decisions/README.md`; `0008-cosmogram-and-hard-slots.md`; `0029-canonical-chart-point-identifiers.md`; `0030-lunar-node-axis-representative.md`; `0031-materialized-configuration-integrity.md`; `0032-unknown-birth-time-aspect-semantics.md`; `0033-unified-dignity-and-dispositor-system.md` | допустимые факты натала/космограммы и идентичность отношений | `956a0d3` |
| ADR | `docs/requirements/decisions/0034-birth-data-and-terms-of-use.md`; `0039-https-in-all-environments.md`; `0040-session-bootstrap-and-current-chart.md`; `0041-stored-chart-in-session.md` | условия формы, HTTPS/cookie, восстановление | `956a0d3` |
| Компоненты | `docs/requirements/component_responsibilities/exact-orb_place_catalog.md`; `exact-orb_build_natal_components.md`; `exact-orb_session_requirements.md` | выбор ID места, расчётный путь и состояние | `956a0d3` |
| Диаграммы | `docs/sequence_diagrams/http_api/README.md` и `001-session-bootstrap.puml`…`004-current-chart.puml`; `docs/sequence_diagrams/place_catalog/001-search-place-success.puml`; `docs/sequence_diagrams/session/002-session-restore-on-return.puml` | последовательности для сценариев и журнала | `956a0d3` |
| Код | `src/exact_orb/http_api/dto.py`; `projectors.py`; `routes/session.py`; `routes/places.py`; `routes/build.py`; `src/exact_orb/application/session_view.py` | фактическая форма HTTP DTO и вызовов | `956a0d3` |
| Код | `src/exact_orb/engine/ephemeris/calc.py`; `src/exact_orb/cli.py` | уже рассчитанные градусы и текущий human-readable CLI | `956a0d3` |
| Проверки | `tests/http_api/test_projectors.py`; `test_place_dto.py`; `test_session.py`; `test_integration.py`; `tests/test_edge_cases.py`; `tests/test_module_boundaries.py` | whitelist DTO, поиск, lifecycle и архитектурные инварианты | `956a0d3` |

`docs/requirements/current/` пока содержит только README; до переноса действуют зафиксированные прежние нормативные пути. Полный ролевой пакет с точными путями и приоритетом чтения находится в [заданиях](#role-tasks).

### Что показали макеты

- Р1 и Э1 задают тёмную палитру, форму и крупный основной CTA; Э2 показывает два одноимённых города с регионом и страной, ошибку невыбранного места и управление стрелками/Enter.
- Р5 и Э7 задают визуальный ритм секций и табличных строк; нарисованное колесо относится к M1-8, общий перенос экрана — к M1-8.1. Э3–Э6 показывают ожидаемые пользовательские состояния, но их данные и тексты требуют сверки с действующим DTO.
- Макеты содержат демо-значения, имя, CTA чата и варианты текста согласия. Они не являются test oracle. `render_review.md` фиксирует ошибки Р1/Р2. В Э4 показаны числовое смещение и диапазон Луны, которых действующий публичный контракт при неизвестном времени не обещает; их нельзя копировать как факты.
- Нормативные для поведения API/ADR имеют приоритет над демонстрационным `decisions.md`. В нём, например, предложен старый вид `ChartDTO` и `issues`, который расходится с реализованным контрактом.

### Findings Intake

| ID | Подтверждённое наблюдение | Влияние и следующий владелец |
|---|---|---|
| `FIND-UI-001` | Roadmap M1-7 требует конфигурации, силу и особые градусы; `http_api.md` §7.2 и `test_projectors.py` сейчас исключают силу/конфигурации из `ChartDTO`. | Полный результат нельзя показать из текущего API. Analyst задаёт наблюдаемый контракт, Developer оценивает публикацию и проверку; `DP-UI-02`. |
| `FIND-UI-002` | ADR-0034 требует presentation checkbox до отправки build; roadmap ставит страницу условий в M1-9 после M1-7. | Стадирование работ и acceptance build-flow требуют явного согласования без молчаливого исключения из ADR; `DP-UI-04`. |
| `FIND-UI-003` | `ui_ux` — черновик; Р1 меняет порядок полей, Э1 содержит имя/согласие, Р2/Э3 содержат будущий чат/колесо; Э4 показывает значения вне действующего публичного контракта. | Analyst отделяет визуальное направление от утверждённого M1-7 поведения; `DP-UI-05` и требования change. |
| `FIND-UI-004` | `ui_ux/requirements.md` §6 перечисляет планеты, дома, аспекты, но не описывает строки полного набора M1-7; CLI показывает дополнительные блоки. | Analyst готовит дельту требований и сценариев для подтверждённого `DP-UI-01`, включая натал/космограмму и пустые состояния. |

### Предварительные границы

**Входит как подтверждённая цель:** работающая форма даты/места/времени, autocomplete с выбранным `place_id`, отображение шести групп фактов из `DP-UI-01`, чтение сохранённой карты и явное построение через существующий HTTP flow. Наблюдаемые состояния и пустые блоки уточняет Analyst; UI получает вычисленные факты из API. Для полного набора необходима ревизия публичного DTO (`DP-UI-02`).

**Не входит:** SVG-колесо M1-8, перенос всех экранов и демо-прототипа M1-8.1, чат/интерпретация M2, страница условий M1-9 как самостоятельный результат, deployment M1-12/13, новые расчётные методики и изменение внутренней модели карты. Переименование `admin1_name` отложено (`DP-UI-03`). Это разделение не отменяет требование ADR-0034 к разрешённости отправки build request (`DP-UI-04`).

**Открыто для Analysis и решения владельца:** точный публичный срез конфигураций/силы/особых градусов (`DP-UI-02`); место имени и неработающих элементов прототипа в форме (`DP-UI-05`); последовательность реализации условия/checkbox M1-9 и M1-7 без нарушения ADR-0034 (`DP-UI-04`). Рекомендация роли не является решением владельца.

### Ожидаемый результат на приёмке — предварительный контур

Это ожидания Manager, не замена `requirements.md`/`scenarios.md` Analyst и evidence Tester.

1. В работающем браузере по HTTPS первый вход создаёт/восстанавливает cookie через bootstrap и получает фактическое состояние через current. Пустая сессия показывает форму; демо-данные не показываются как результат расчёта.
2. Пользователь выбирает место из подсказок; одноимённые варианты различимы. В build уходит выбранный `place_id`, дата и `HH:MM` либо `birth_time:null`. Невыбранная строка города, неверная дата и ошибки API объясняются у соответствующего поля; введённые значения сохраняются.
3. После явного успешного build отображаются реальные таблицы планет/точек, домов, аспектов, конфигураций, силы и особых градусов в поддерживаемом натале. Представление использует опубликованные ID/знак/градус/минуту; длинная дробь `degree_in_sign` человеку не показывается. Список и смысл полей согласованы в `DP-UI-02`.
4. При неизвестном времени строится космограмма. Отсутствующие дома, углы и сила не выдаются за рассчитанные; конфигурации показываются только если опубликованы в результате. Техническое полуденное время и выдуманный диапазон Луны не показываются.
5. Обновление страницы с живой cookie даёт ту же `chart_identity` и те же факты из `GET /charts/current`. `chart_stale` сохраняет карту с пометкой и явным rebuild; `chart_unavailable` сохраняет birth input и предлагает явное построение. Неопределённый исход, 409 и лимиты обрабатываются по HTTP-контракту без автоматического повторения POST.
6. Форма и таблицы доступны с клавиатуры и читаемы на узком экране; проверка опирается на реальные ответы/контрактные fixtures и сравнение с макетами только по композиции, палитре и ритму.
7. Tester фиксирует среду, baseline, сценарии, фактические результаты, ограничения и соответствие чистовой редакции требований. Final acceptance Manager возможна только после устранения или явного решения blocking `DP-*` и ролевого evidence.

Отправка build из UI остаётся зависимой от `DP-UI-04`: этот черновик не разрешает обходить ADR-0034 ради демонстрации. M1-7 acceptance не означает публичный запуск.

### Плановый бюджет и состояние

Пользователь 2026-10-03 задал ориентир: **Analysis — 1 рабочий день, Development — 2, Testing — 2; всего 5**. Это целевой бюджет, а не оценки Developer/Tester с confidence и assumptions; календарные даты и Change Plan пока не утверждены. Каждая роль должна сообщить, укладывается ли полный scope, и обосновать отклонение. Статус остаётся `DRAFT` до фактического начала Analysis; тогда Manager переводит его в `ANALYSIS`.

Артефакты зафиксированы в manager-ветке; включение в `change/*` и запуск ролевых агентов пока не подтверждены. Перед фактической выдачей задач нужен доступный им commit `change/*` с этими артефактами и новый общий input HEAD.

<a id="decision-register"></a>
## Единый реестр решений

**Владелец структуры и baseline:** Change Manager.
**Интеграционная ветка:** `change/ui-birth-form-and-facts`.
**Исходный commit:** `956a0d3acbb1536e57535c4689aee57efe607381`.
**Baseline этой редакции:** commit manager-ветки, содержащий этот файл, поверх `956a0d3`; при handoff заменить на фактический HEAD `change/*`, содержащий реестр.
**Статус change:** DRAFT; строки `OPEN` ниже не являются разрешением менять контракт.

Вопрос, варианты, рекомендации и выбор хранятся в одной строке. Ролевые документы ссылаются только на ID и baseline. `ACCEPTED` ниже подтверждены словами владельца в этой задаче; отсутствие консультации не выдаётся за согласие ролей.

| ID | Статус и gate | Вопрос, контекст и различающий пример | Связанные источники | Владелец и консультанты | Варианты и влияние | Рекомендации ролей | Решение владельца и основание | Последствия, обновления и evidence |
|---|---|---|---|---|---|---|---|---|
| `DP-UI-01` | **ACCEPTED**; scope M1-7. | **Вопрос:** какие группы фактов входят в таблицы M1-7?<br>**Пример:** натал содержит рассчитанную конфигурацию и силу, но UI показывает только планеты/дома/аспекты. | `roadmap.md` M1-7; `FIND-UI-001/004`; `cli.py`; `http_api.md` §7.2 @ `956a0d3`. | **Владелец:** пользователь как владелец объёма.<br>**Консультанты для детализации:** Analyst, Developer, Tester. | **A:** только поля текущего DTO — быстрее, но не выполняет roadmap.<br>**B:** полный набор roadmap — требуется расширение публичного контракта и UI-сценариев. | **Analyst/Developer/Tester:** ещё не консультировались; пустота не означает согласие. | **Выбрано:** B. **Правило:** M1-7 включает планеты/точки, дома, аспекты, конфигурации, силу и особые градусы в применимых видах карт.<br>**Основание:** прямое подтверждение пользователя 2026-10-03: «да, подтверждаю». | **Последствия:** `DP-UI-02` определяет недостающий контракт; Analyst описывает содержимое/пустые состояния, Developer и Tester оценивают полный объём. **Evidence:** сообщение пользователя в этой задаче от 2026-10-03. **ADR:** для самого выбора объёма не требуется. |
| `DP-UI-02` | **OPEN**; блокирует `READY_FOR_DEVELOPMENT`. G1 может завершиться с вопросом, вариантами и рекомендацией Analyst. | **Вопрос:** какие типизированные публичные поля и структура передают конфигурации, силу и особые градусы для натала/космограммы?<br>**Пример:** внутренний `ChartArtifact` содержит `strength.degree_flags`, а текущий `ChartDTO` этого не публикует; браузер не должен читать сырой artifact или вычислять флаги. | `FIND-UI-001/004`; `http_api.md` §7.2; `dto.py`, `projectors.py`, `test_projectors.py`; ADR-0029–0033 @ `956a0d3`. | **Владелец публичной семантики:** пользователь после Analysis и технических консультаций.<br>**Консультанты:** Analyst, Developer, Tester; Technical Reviewer при предложении новой архитектурной границы. | **A:** расширить whitelist `ChartDTO` типизированными блоками; оба пути POST/current возвращают одинаковую карту.<br>**B:** отдельная публичная операция фактов; новый contract/flow и отдельная оценка. Сырой `model_dump` внутреннего artifact не является допустимым вариантом по действующему HTTP-контракту. | **Analyst:** не получена.<br>**Developer:** не получена.<br>**Tester:** не получена.<br>**Reviewer:** не запрошен. | **Выбрано:** не принято.<br>**Нужно установить:** поля, вложенность/порядок, идентичность ссылок, применимость при неизвестном времени, отсутствие блока против пустого блока, человекочитаемое представление и стабильность для восстановления. | **Последствия:** до решения нельзя утверждать полный API/UI contract и оценку 2 дня. **Обновить после выбора:** `docs/requirements/changes/ui-birth-form-and-facts/`, `http_api.md`, DTO/projector/tests, нужные diagrams. **Evidence/ADR:** ожидаются; если меняется архитектурное решение — ADR по правилам проекта. |
| `DP-UI-03` | **ACCEPTED**; не блокирует M1-7. | **Вопрос:** переименовывать ли публичное техническое поле `admin1_name` в этой работе?<br>**Пример:** два Кировска различаются регионом и страной, но API использует имя поля GeoNames. | `FIND-TEST-HTTP-002` в `docs/testing/http-api-and-session-middleware/tester.md`; `http_api.md` §6.3; `ui_ux/requirements.md` §4; `dto.py` @ `956a0d3`. | **Владелец:** пользователь.<br>**Консультанты для будущего change:** Analyst, Developer, Tester. | **A:** переименовать сейчас — затронуть API, тесты и клиентов, расширив M1-7.<br>**B:** оставить текущий ключ, выводить человеку регион/страну и перенести переименование в отдельный технический долг. | **Analyst/Developer/Tester:** для M1-7 не запрошены; это не рекомендация от их имени. | **Выбрано:** B. **Правило:** `admin1_name` остаётся публичным ключом M1-7; переименование не критично для этого change и выполняется отдельной задачей технического долга без пока выбранного нового имени.<br>**Основание:** сообщения пользователя «оставь как есть», «переименование возьмем в тех долг» и поручение добавить решение, 2026-10-03. | **Последствия:** UI использует действующий ключ, но подписывает значение человеческим словом «регион»; новая строка/alias в DTO сейчас не вводится. **Возврат к долгу:** отдельная постановка изменения API naming с оценкой миграции. **Evidence:** сообщения пользователя в этой задаче. **Ограничение:** это решение не закрывает прочие findings, статус `PARTIAL` или final acceptance M1-6. |
| `DP-UI-04` | **OPEN**; блокирует acceptance отправки build из M1-7 и `READY_FOR_DEVELOPMENT` для этого пути. | **Вопрос:** как поэтапно собрать работающий M1-7 build-flow, если ADR-0034 требует checkbox ознакомления до POST, а страница условий запланирована на M1-9?<br>**Пример:** кнопка формы отправляет реальный `POST /charts/natal` без утверждённой страницы условий. | `FIND-UI-002`; ADR-0034 §§2–3; `roadmap.md` M1-7/M1-9; `ui_ux/mobile/e1-input.png` @ `956a0d3`. | **Владелец:** пользователь после Analyst/Developer/Tester consultation.<br>**Консультант по границе ADR:** Technical Reviewer. | **A:** согласовать необходимую часть условий/checkbox раньше и включить в M1-7 — меняет распределение scope/оценки.<br>**B:** собрать M1-7 внутренне без финальной приёмки отправки до M1-9 — задерживает acceptance.<br>**C:** предложить пересмотр ADR отдельным архитектурным решением — требует явного решения, не следует из макета. | **Analyst/Developer/Tester/Reviewer:** не получены. | **Выбрано:** не принято. **Действующий контракт:** ADR-0034 остаётся в силе; черновик не разрешает обход gate. | **Последствия:** Analyst описывает варианты и влияние на пользовательский сценарий; Developer оценивает staging, Tester — проверяемость. Manager не объявляет M1-7 готовым при неразрешённом blocking вопросе. **Evidence/ADR:** ожидаются. |
| `DP-UI-05` | **OPEN**; блокирует окончательный состав формы, но не анализ текущего API. | **Вопрос:** показывать ли поле «Имя» и будущие CTA в форме M1-7?<br>**Пример:** Э1 содержит имя и «открыть чат», но `POST /charts/natal` принимает только дату, время и `place_id`; чат — M2. | `FIND-UI-003`; `ui_ux/render_review.md` Р1; `ui_ux/decisions.md` №5; `ui_ux/requirements.md` §4; `http_api.md` §6.4; `roadmap.md` M1-7/M2 @ `956a0d3`. | **Владелец:** пользователь.<br>**Консультанты:** Analyst, Developer, Tester. | **A:** убрать имя и будущие CTA из M1-7 — соответствует текущему API, меньше ложных обещаний.<br>**B:** хранить имя только на клиенте — отдельная UX-семантика/срок жизни.<br>**C:** расширить публичный API — изменение контракта и обработки данных, требует отдельного основания. | **Analyst:** не получена; в черновом `ui_ux/decisions.md` есть рекомендация A, она ещё не решение.<br>**Developer/Tester:** не получены. | **Выбрано:** не принято. Будущий чат не считается поставленным только потому, что нарисован в макете. | **Последствия:** Analyst предлагает наблюдаемое поведение и точный текст действия формы; Manager получает выбор владельца до утверждения UI requirements. **Evidence:** ожидается. |

<a id="role-tasks"></a>
## Задания ролям

**Change:** `ui-birth-form-and-facts`. **Manager status:** DRAFT.
**Общий исходный commit для консультаций:** `956a0d3acbb1536e57535c4689aee57efe607381` — текущий HEAD `change/ui-birth-form-and-facts` при подготовке этого пакета.
**Manager artifacts:** [brief](#change-brief) и [единый реестр](#decision-register) в этом зафиксированном файле.
**Правило выдачи:** при фактическом запуске отдельных ролевых веток Manager обновляет единый input commit на HEAD `change/*`, содержащий эти артефакты. Никакой ролью не предполагается, что незакоммиченный manager worktree виден из её checkout.

Пользователь задал **целевой бюджет**: Analysis 1 день, Development 2 дня, Testing 2 дня. Это ограничение для проверки реализуемости, а не готовая оценка соответствующей роли. Роли возвращают собственные range, confidence, assumptions и зависимости; урезать подтверждённый `DP-UI-01` молча нельзя.

### Обязательный пакет чтения

Порядок важен: действующий контракт и код выше чернового прототипа. Все пути относятся к `956a0d3`. Файлы `prompts/**` и материалы экспериментов не входят в пакет; открывать их только при адресном пробеле происхождения решения.

| Порядок | Материал | Для чего читать | Роли |
|---|---|---|---|
| 1 | `AGENTS.md`; `docs/development_approach/process.md`; `docs/development_approach/roles.md`; `docs/development_approach/skills/functional-analyst/SKILL.md`, `docs/development_approach/skills/developer/SKILL.md` или `docs/development_approach/skills/tester/SKILL.md` соответственно | полномочия, gates, запреты и handoff | все |
| 2 | этот brief, этот реестр и `docs/project_management/roadmap.md` §3.3 M1-6–M1-9 | подтверждённый объём, blocking `DP-*` и границы соседних этапов | все |
| 3 | `docs/requirements/README.md`; `docs/requirements/current/README.md`; `docs/requirements/changes/README.md`; `docs/requirements/http_api.md` §§6–9, 13 | нормативный baseline, форматы change-требований, реальные endpoint/DTO/recovery | все |
| 4 | `docs/requirements/decisions/README.md`; `docs/requirements/decisions/0008-cosmogram-and-hard-slots.md`; `0029-canonical-chart-point-identifiers.md`; `0030-lunar-node-axis-representative.md`; `0031-materialized-configuration-integrity.md`; `0032-unknown-birth-time-aspect-semantics.md`; `0033-unified-dignity-and-dispositor-system.md`; `0034-birth-data-and-terms-of-use.md`; `0039-https-in-all-environments.md`; `0040-session-bootstrap-and-current-chart.md`; `0041-stored-chart-in-session.md` (последние имена — в том же каталоге) | космограмма, ID/отношения, сила, условия, HTTPS/cookie, восстановление | все; Developer/Analyst читают связанные решения целиком |
| 5 | `docs/requirements/component_responsibilities/exact-orb_place_catalog.md`; `exact-orb_build_natal_components.md`; `exact-orb_session_requirements.md`; `docs/requirements/session/stored-chart-session-behavior.md` | что уже вычисляют каталог, application и сессия | Analyst, Developer; Tester — затронутые сценариями разделы |
| 6 | `docs/sequence_diagrams/http_api/001-session-bootstrap.puml`, `002-place-search.puml`, `003-build-natal.puml`, `004-current-chart.puml`; `docs/sequence_diagrams/place_catalog/001-search-place-success.puml`; `docs/sequence_diagrams/session/002-session-restore-on-return.puml`, `006-two-tabs-rebuild-and-restore.puml` | порядок вызовов, recovery и события журнала | все по своему сценарию |
| 7 | `src/exact_orb/http_api/dto.py`, `projectors.py`, `routes/session.py`, `routes/places.py`, `routes/build.py`; `src/exact_orb/application/session_view.py` | фактический HTTP путь и граница публичной проекции | все |
| 8 | `src/exact_orb/engine/ephemeris/calc.py` `zodiac_position`; `src/exact_orb/cli.py` `format_human` и formatting helpers; `src/exact_orb/engine/strength/types.py`; `src/exact_orb/engine/configurations/types.py` | уже рассчитанные факты и ориентир human-readable CLI; не копировать внутренний artifact в API | Analyst, Developer; Tester для oracle/проверки |
| 9 | `tests/http_api/test_projectors.py`, `test_place_dto.py`, `test_session.py`, `test_integration.py`; `tests/test_module_boundaries.py`; `tests/test_edge_cases.py` | существующий whitelist, позитивные контроли, lifecycle и границы | все; Tester сначала формирует независимые сценарии |
| 10 | `docs/ui_ux/README.md`; `docs/ui_ux/requirements.md` §§4–6, 9–13; `docs/ui_ux/render_review.md`; `docs/ui_ux/decisions.md` | черновое визуальное направление и известные расхождения с нормативным API | все, с явной пометкой DRAFT |
| 11 | `docs/ui_ux/renders/r1-input.png`, `r2-chart-ready.png`, `r5-chart-detail.png`; `docs/ui_ux/mobile/e1-input.png`, `e2-place-suggestions.png`, `e3-chart-ready.png`, `e4-time-unknown.png`, `e5-chart-stale.png`, `e6-chart-unavailable.png`, `e7-chart-detail.png` (сокращённые имена — в указанном каталоге); при необходимости `docs/ui_ux/web-prototype.html` | композиция/палитра/ритм, mobile states и поведение выбора места; числа демо не oracle | все |
| 12 | `docs/project_management/change_plans/http-api-and-session-middleware.md`; `docs/testing/http-api-and-session-middleware/tester.md` | статус зависимости M1-6 и границы доказанного HTTPS-прогона | все, без повторного review всего M1-6 |

`docs/requirements/current/` сейчас содержит только README. Поэтому `http_api.md` и указанные component requirements используются как прежние нормативные пути до переноса. Проектный `ui_ux/decisions.md` содержит предложения и старую форму DTO; при расхождении с `http_api.md`, ADR, кодом и тестами он не меняет действующий контракт.

**Ограничитель макетов:** Р1 задаёт визуальный язык формы, Э2 — выбор среди одноимённых мест, Р5/Э7 — расположение фактов. SVG-колесо — M1-8; полный перенос Э1–Э7 — M1-8.1; чат — M2; страница условий — M1-9. Демо-имя, CTA чата, округления и значения на картинках не становятся требованиями или эталонами. Э4 не доказывает числовой диапазон Луны или UTC offset при неизвестном времени.

### Задание Functional Analyst — Analysis, целевой бюджет 1 день

**Исходная точка:** общий commit и пакет выше; `DP-UI-01`/`03` приняты пользователем, `DP-UI-02`/`04`/`05` открыты; `FIND-UI-001`…`004` из brief. Начать с наблюдаемого поведения и публичного контракта. Не менять production code, Manager plan, Developer-owned implementation plan и чужие решения.

1. Создать `docs/requirements/changes/ui-birth-form-and-facts/requirements.md`, `scenarios.md` и `analysis.md` по правилам `docs/requirements/README.md`: выбрать `DELTA`/`FULL`, указать исходные нормативные пути и commit, стабильные IDs и целевые пути чистовой редакции. Не восстанавливать обязательный BDD/Gherkin слой.
2. Разложить `DP-UI-01` на проверяемый состав шести групп фактов. Для каждой указать источник в существующем расчёте, видимые поля/порядок/названия, применимость к наталу и космограмме, `null` против пустого списка, неизвестное время, ретроградность и формат градусов/минут. CLI — ориентир для перечисленных roadmap групп, но дополнительные CLI-разделы не попадают в scope автоматически. Не выводить расчётные показатели на клиенте из `longitude`. В `DP-UI-02` отдельно оценить, нужны ли нынешние сырые `longitude`/`cusp_longitude` в публичном DTO; `degree_in_sign` в нём уже отсутствует.
3. Для `DP-UI-02` описать наблюдаемую публичную схему недостающих блоков и варианты, включая одинаковую семантику в committed `POST /charts/natal` и restored `GET /charts/current`; показать конкретный пример карты с непустой конфигурацией, силой и special degree и космограммы без домов/силы. Не считать сырой `ChartArtifact.model_dump()` допустимым публичным DTO. Объяснить, как изменятся `docs/requirements/http_api.md` и действующие сценарии M1-6, не редактируя их до утверждения scope.
4. Описать форму: дата, выбранный `place_id` из `GET /places`, известное время либо `birth_time:null`, приоритет validation/`issues`, keyboard/mouse selection, одинаковые названия мест, сохранение введённого при отказе. Сверить с действующим `IssueDTO`, а не старым предложением в `ui_ux/decisions.md`. Для `DP-UI-05` дать понятные пользователю варианты поля имени и текста CTA, не обещая чат M2.
5. Описать behavioral/API sequences: bootstrap → current; place search; явный build; restore; stale/unavailable; 409, 429, 503, 504 и неопределённый исход без auto POST. Для существенных переходов сопоставить sequence diagrams с ожидаемыми событиями журнала и корреляцией. `DP-UI-04` про gate условий/checkbox эскалировать как конфликт staging с действующим ADR-0034; не выбирать исключение самостоятельно.
6. Просмотреть макеты Р1/Р2/Р5, Э1–Э7 и `render_review.md`; записать только относящиеся к M1-7 факты и осознанные расхождения. Сценарии acceptance должны различать расчётные данные и демо-подписи. В `analysis.md` дать manager summary, findings с влиянием и вопросами владельцу, карту будущего переноса в `current/`; обновить только Analyst-рекомендации в существующих `DP-UI-*` через согласованный handoff.

**Условие завершения G1:** требования и сценарии покрывают happy/error/boundary/recovery, `FIND-UI-001`…`004` классифицированы, blocking `DP-*` перечислены, утверждённые и предлагаемые положения разделены, версии/пути указаны. Передать Manager ссылки и честный вывод об укладывании в 1 день; полный UI/ADR gap не скрывать ради срока.

### Задание Developer — consultation, затем implementation после gate

**Целевой бюджет Development:** 2 рабочих дня по указанию пользователя. Сначала техническая консультация после G1 от того же HEAD `change/*` и Analyst baseline; до `READY_FOR_DEVELOPMENT` не менять production code. Владелец технической реализации и developer tests — Developer.

1. Сверить `requirements.md`/`scenarios.md` Analyst с существующим `ChartArtifact`, `ChartDTO`, whitelist projector, `BuildReadyDTO` и `SessionReadyDTO`. Для `DP-UI-02` оценить минимальное типизированное представление конфигураций, силы и special degrees, порядок/ссылочную целостность/отсутствующие блоки, safe failure. Указать, нужны ли ADR/Technical Reviewer; не возвращать internal fields wholesale и не менять расчёт ради presentation.
2. Проверить место и способ сборки первого UI в существующем модульном монолите, требуемые зависимости и HTTPS/cookie/browser boundary. Если стек не задан, предложить ограниченный вариант и стоимость. Не вводить сервис, отдельную сеть между компонентами или зависимость без обоснования.
3. Разбить будущую реализацию на проверяемые work items: публичный DTO и тесты обоих путей POST/current; форма и autocomplete; reader/formatting шести групп; bootstrap/current/build и recovery; адаптивность/доступность; интеграционные проверки. Выявить зависимость от `DP-UI-04` и известное ограничение локального proxy `FIND-TEST-HTTP-001`, не исправляя M1-6 попутно.
4. Подготовить начальную часть `docs/project_management/implementation_plans/ui_birth_form_and_facts_implementation_plan.md`: feasibility, диапазон с confidence, assumptions/dependencies, bounded spike если без него 2 дня не проверить, risks и технические рекомендации в `DP-UI-02/04/05`. По каждому work item указать существующее покрытие и нужные проверки, не плодить дубликаты.
5. После утверждённого плана и blocking решений реализовать только согласованный scope. Синхронизировать изменённые текущие HTTP requirements/diagram и OpenAPI contract, сохранить модульные инварианты и публичные ошибки, запускать target → related → full `pytest`. Для UI-пути не заявлять browser acceptance на основании только ASGI тестов.

**Условие завершения consultation G2:** Manager получил Implementation Plan с честной оценкой полного `DP-UI-01`, техническими вариантами и рисками; решение пользователя не подменено. **Условие будущего handoff Tester:** commit реализации, diff summary, среда запуска, exact test commands/results, открытые limitations.

### Задание Tester — consultation, затем независимая приёмка

**Целевой бюджет Testing:** 2 рабочих дня по указанию пользователя. Сначала testability review после G1 от того же HEAD `change/*` и Analyst baseline; независимые negative/boundary scenarios сформировать до чтения Developer tests, затем сверить с существующим покрытием. Tester не меняет требования ради прохода теста и не объявляет acceptance до actual run.

1. Подготовить `docs/testing/ui-birth-form-and-facts/test-plan.md` или краткий эквивалент с матрицей requirement → scenario → planned evidence. Проверить наблюдаемость всех шести групп `DP-UI-01`, обеих форм ChartDTO (POST/current), пустых блоков, космограммы без времени, долготы против показанных градусов, отсутствия демо-чисел. Позитивный контроль добавить к каждому существенному негативному утверждению.
2. Независимо проверить форму и поиск: невыбранный текст места не отправляется; два одноимённых места различимы; выбранный `place_id` идёт в build; клавиатура, Enter, мышь, invalid date/time и `issues`; значения сохраняются после ошибок. Уточнить, какой accepted текст/CTA и gate условий нужен по `DP-UI-04/05`.
3. Проверить session/recovery: первый bootstrap/current, успешный build, reload с той же картой, stale/unavailable, 409 session restore, 429/503 `Retry-After`, 504/unknown outcome без автоматического повторения POST, две вкладки. Проверить, что request/event logs позволяют сопоставить ключевые HTTP → component переходы по request ID.
4. Для браузерного evidence использовать поддерживаемый HTTPS путь и настоящую cookie jar. `FIND-TEST-HTTP-001` прежнего change остаётся известным ограничением стандартного localhost-пути: если он мешает, зафиксировать blocker и обход отдельно; обход не выдавать за обычный браузерный PASS. Не запускать платные или внешние smoke без отдельного указания.
5. После реализации получить конкретный tested commit и провести автоматические, браузерные и визуальные проверки на desktop и mobile ширине 360 px. Сравнивать макеты по композиции/палитре/ритму, а численные факты — с API/контрактными fixtures. Проверить keyboard/focus, читаемость таблиц и пустые состояния; приложить evidence без пользовательских секретов.
6. Перед финальным handoff сверить подготовленную Analyst чистовую редакцию и карту переноса с утверждённым и проверенным контрактом. Передать `docs/testing/ui-birth-form-and-facts/tester.md`: среда, точные команды, actual results, matrix, findings, ограничения и readiness recommendation. Оценку 2 дня вернуть диапазоном/confidence после testability review.

**Условие завершения consultation G2:** testability/оценка и blocking вопросы переданы Manager. **Условие будущей приёмки:** воспроизводимое evidence на точном commit, без переноса `PARTIAL` M1-6 в «PASS» по умолчанию.

### Условный Technical Reviewer

Подключается к `DP-UI-04`, если варианты требуют изменения ADR-0034 или security boundary; к `DP-UI-02`, если технический вариант меняет ownership публичной проекции, вводит новый service/network boundary либо исключение из архитектурного инварианта. Reviewer даёт рекомендацию в ту же строку, владелец решения остаётся указанным в реестре.

### Manager handoff и итоговая приёмка

Manager после G1/G2 собирает Change Plan из результатов трёх ролей, реестра и целевого бюджета; не выдаёт указанные пользователем 1/2/2 дня за подтверждённые ролевые estimates. `READY_FOR_DEVELOPMENT` возможен только после решения blocking `DP-UI-02/04/05` с evidence и результатов ролей. Ожидаемый пользовательский результат и предварительный перечень проверок находятся в brief `«Ожидаемый результат на приёмке»`. Финальное решение Manager требует implemented baseline, независимого Tester evidence, карты переноса Analyst, чистовых требований и явного перечня открытых ограничений.
