# Сценарии приёмки: ui-chart-wheel

**Автор:** Codex / Functional Analyst, TASK-A-001; пакет v1, 2026-10-13.
**Вход:** `5188b523089acc8081585e869c482ee0d343cfba`; нормативный baseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.
**Требования:** [requirements.md](requirements.md), тот же локальный пакет; точная версия — SHA-256 manifest в корневом handoff.
**DP / сводка:** [Manager §3](../manager_artifact.md#3-единый-реестр-dp) @ InputSHA. Предложенный DP-O-014 ещё не зарегистрирован Manager; source [FIND-WHEEL-001](findings.md#find-wheel-001).

Сценарии задают expected behavior для review, не фактический test run. Условные критерии прямо обозначены: нерешённые DP не получают PASS или разрешение реализации. Общие права, схемы, cookie, X-Request-ID/Cache-Control/Retry-After и минутная точность наследуются из AS-UI baseline. Серверный trace N, локальный evidence U описаны в [источниках и наблюдаемости](sources.md#наблюдаемость).

## Проверочные данные

| Набор | Проверенный источник @ MainBaseline | Применение |
|---|---|---|
| F0 | [chart_dto.json](../../../../../tests/http_api/golden/chart_dto.json) | Natal: 3 points / 3 аспекта, все с углами; cosmogram: 2 points / 1 устойчивый аспект. Все natal аспекты exact/working. |
| F1 | [natal_1985_chart_dto.json](../../../../../tests/ui/fixtures/natal_1985_chart_dto.json) | Реальная публичная проекция: 16 points, 12 домов, 46 аспектов, все 3 категории, 15 аспектов с angles; R у jupiter/neptune/true_node/south_node/selena. |
| F2 | [session_view.json](../../../../../tests/http_api/golden/session_view.json) и [session.mjs](../../../../../tests/ui/fixtures/session.mjs) | Empty/known_ready/unknown_ready/unavailable, ready(stale), response/failure, deferred, fakeClock, harness; form snapshot до отправки. |
| F3 | Описанный ниже контролируемый DTO на основе структурной копии F1 | Только тест представления, не engine golden / реальный birth result. Developer оформляет fixture в своей задаче; исходные golden не меняются. |
| F4 | Семь public types из HTTP §7.2 и существующего facts.test.mjs | Контролируемые пары с conjunction/semisextile/sextile/square/trine/quincunx/opposition и category exact/working/background; известные endpoint IDs. Категорию UI не вычисляет. |

F3 меняет только явно названные поля копии; identity — отдельная тестовая, source помечен controlled UI fixture. Для пяти retrograde points задаются опубликованные согласованные позиции: mercury 359.70°/Pisces/29°42′; venus 359.85°/Pisces/29°51′; mars 0°/Aries/00°00′; jupiter 0.15°/Aries/00°09′; saturn 0.30°/Aries/00°18′. У всех retrograde=true, остальные F1 поля как в копии. Aspects — явно заданные API записи mercury→venus conjunction exact orb=0.15, venus→mars conjunction working orb=0.15, sun→moon conjunction background orb=5.0. Это адресуемые UI данные, не assertion допустимости физического натала или пересчёт категории. F3-max включает все 16 IDs в один сектор и разные пары ☌; численные/визуальные пределы ожидают DP-O-011, а не становятся golden по прототипу.

<a id="наследование-baseline"></a>
## Наследование baseline

[AS-UI-01…23](../../../../requirements/current/ui/scenarios.md) @ MainBaseline сохраняют свои IDs и все прежние проверки. Новые AS-WHEEL дополняют исходные сценарии; их отсутствие в новом тексте не удаляет исходные обязательства. Clean target после acceptance — тот же `docs/requirements/current/ui/scenarios.md`, без перезаписи истории M1-7.

| Исходные AS-UI | Действие / дополнение M1-8 |
|---|---|
| 01, 10, 11 | Сохранить; дополнить AS-WHEEL-02/15/17 для колеса/сводки |
| 02, 05, 06, 17, 18 | Сохранить полностью; ошибки/черновик/порог поиска не меняются, дополнительные проверки формы AS-WHEEL-18/21 |
| 03, 04, 07, 08, 09, 15 | Сохранить; дополнить AS-WHEEL-01/03/04/05/06/07/08/09/10 |
| 12, 13, 14, 16, 23 | Сохранить; дополнить AS-WHEEL-17/18/19/20/21/22 |
| 19 | Сохранить; добавить колесо/связь AS-WHEEL-16/23 |
| 20, 21 | Сохранить; gate не восстанавливается при collapse/reload, AS-WHEEL-02/12/18 |
| 22 | Сохранить; подробности остаются локальным действием, добавить AS-WHEEL-11/12/13/14 |

## Добавочные сценарии

<a id="as-wheel-01"></a>
### AS-WHEEL-01. Committed POST и неизменяемая сводка

- **Требования:** [REQ-WHEEL-01](requirements.md#req-wheel-01), [REQ-WHEEL-09](requirements.md#req-wheel-09), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-03](requirements.md#req-ui-03), [REQ-UI-11](requirements.md#req-ui-11). **Основания:** DP-O-001/002/003 @ единый реестр / предложение Analyst.
- **Предусловия:** Живая сессия после bootstrap/current; форма валидна, gate поставлен вручную. Использовать F1 и form fixture.
- **Данные и действие:** Явно отправить снимок A, удержать ответ leaf promise, изменить черновик на B; доставить committed ChartDTO A.
- **Ожидаемый ответ:** Ровно один POST с birth_date,birth_time,place_id; status=chart_ready.
- **Ожидаемое состояние:** Колесо и таблицы A доступны сразу без подробностей, сводка — снимок A, редактор сохраняет B. Без изменённого черновика первичное успешное получение сворачивает форму; поведение при B — условие DP-O-013. Tz_id/offset из POST не выдуманы.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет скрытого POST/GET ради сводки и нет подмены A черновиком B; позитивно проверить принятую identity A и совпадение таблиц с F1.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-01`.

<a id="as-wheel-02"></a>
### AS-WHEEL-02. Restore current без расчёта

- **Требования:** [REQ-WHEEL-01](requirements.md#req-wheel-01), [REQ-WHEEL-09](requirements.md#req-wheel-09), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-01](requirements.md#req-ui-01), [REQ-UI-08](requirements.md#req-ui-08), [REQ-UI-11](requirements.md#req-ui-11). **Основания:** DP-O-001/002/003 @ единый реестр / предложение Analyst.
- **Предусловия:** Живая cookie, сохранённый birth/ChartDTO F1 одной identity.
- **Данные и действие:** Reload страницы; выполнить bootstrap→current; открыть «Изменить данные».
- **Ожидаемый ответ:** 200 ready без chart, затем 200 chart_ready с birth/chart.
- **Ожидаемое состояние:** Колесо сразу, сводка из birth этого GET; без изменённого черновика форма свернута и раскрывается заполненной. Отметка условий после reload снята.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет POST build/resolver/engine при чтении; позитивно проверены два успешных HTTP ответа, identity и заполненное place_id.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-02`.

<a id="as-wheel-03"></a>
### AS-WHEEL-03. Все опубликованные точки и истинные позиции

- **Требования:** [REQ-WHEEL-02](requirements.md#req-wheel-02), [REQ-UI-04](requirements.md#req-ui-04). **Основания:** DP-O-005/011; предложенный DP-O-014 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 принят как реальная опубликованная карта.
- **Данные и действие:** Показать колесо и раскрыть HTML факты.
- **Ожидаемый ответ:** Используется исходный ChartDTO F1; локальные действия не дают HTTP.
- **Ожидаемое состояние:** Все 16 points адресуются каноническими ID, 12 куспидов и пять angles видны. Табличные sign/degree/minute/house прежние; истинные отметки соответствуют longitude. South_node — только опубликованная позиция.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет нового аспекта узлов или пересчёта знака; позитивно проверить true_node и south_node, R и существующий опубликованный аспект.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-03`.

<a id="as-wheel-04"></a>
### AS-WHEEL-04. Аспект с углом

- **Требования:** [REQ-WHEEL-02](requirements.md#req-wheel-02), [REQ-WHEEL-04](requirements.md#req-wheel-04). **Основания:** DP-O-006/008/010/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F0 natal: три аспекта, все адресуют asc/mc/vertex; первый moon→asc square exact, orb=0.4407655487941611.
- **Данные и действие:** Показать колесо, выбрать этот аспект в HTML и на графике.
- **Ожидаемый ответ:** Исходные from/to,type,category,orb неизменны; новых запросов нет.
- **Ожидаемое состояние:** Линия moon→asc не пропущена; выбор адресует строку этой пары и опубликованный asc. Аналогичный контроль для mc/vertex. Угол подсвечивается как endpoint без самостоятельного нового режима выбора угла.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет привязки к ближайшей планете/dsc/ic; позитивно увидеть конкретные три графических аспекта F0, их пары и выбранный asc.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-04`.

<a id="as-wheel-05"></a>
### AS-WHEEL-05. Космограмма с устойчивым аспектом

- **Требования:** [REQ-WHEEL-02](requirements.md#req-wheel-02), [REQ-WHEEL-03](requirements.md#req-wheel-03), [REQ-UI-08](requirements.md#req-ui-08). **Основания:** DP-O-009; предложенный DP-O-014 @ единый реестр / предложение Analyst.
- **Предусловия:** F0 cosmogram либо unknown_ready F2, houses/angles/house_system/point.house=null.
- **Данные и действие:** Получить committed cosmogram, затем восстановить тот же результат current.
- **Ожидаемый ответ:** POST с birth_time:null; current birth_time/utc_offset_seconds=null.
- **Ожидаемое состояние:** 0° Овна слева, нет домов/углов; опубликованные points и устойчивый аспект видны, пояснения якоря и максимального orb сохранены.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет выдуманных ASC/offset/диапазона Луны/time_dependent; позитивно проверить оба опубликованных points и устойчивую пару F0.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-05`.

<a id="as-wheel-06"></a>
### AS-WHEEL-06. Пустой графический набор и пустой полный список

- **Требования:** [REQ-WHEEL-03](requirements.md#req-wheel-03), [REQ-WHEEL-04](requirements.md#req-wheel-04), [REQ-UI-06](requirements.md#req-ui-06). **Основания:** DP-O-006/009 @ единый реестр / предложение Analyst.
- **Предусловия:** Две контролируемые копии F1: A aspects только существующие background; B aspects=[]. Отдельно повторить B для cosmogram.
- **Данные и действие:** Принять A, открыть полный список; затем принять B с новой identity.
- **Ожидаемый ответ:** Оба chart_ready, отличны от F2 empty.
- **Ожидаемое состояние:** A: колесо с точками без линий/☌, полный список background доступен. B: колесо с точками, «Аспекты не найдены». Состояние не выглядит отсутствием карты.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет синтеза exact/working; позитивно увидеть точки A/B, background строку A и отличное F2 empty без колеса.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-06`.

<a id="as-wheel-07"></a>
### AS-WHEEL-07. Соединения, включая фоновые

- **Требования:** [REQ-WHEEL-02](requirements.md#req-wheel-02), [REQ-WHEEL-04](requirements.md#req-wheel-04). **Основания:** DP-O-006/007/011 @ единый реестр / предложение Analyst.
- **Предусловия:** Контролируемый UI DTO F3 с exact conjunction mercury↔venus и working conjunction venus↔mars; background conjunction sun↔moon.
- **Данные и действие:** Показать маркеры, выбрать каждый через HTML; отдельно выбрать фоновой.
- **Ожидаемый ответ:** Исходные записи и orb не меняются; HTTP отсутствует.
- **Ожидаемое состояние:** Exact/working получают ☌ с однозначной связью с парой, таблица содержит точную пару; background не получает линии/☌ после выбора. Окончательное размещение нескольких ☌ условно до DP-O-011.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет искусственно удлинённой хорды и пропущенного working; позитивно адресовать обе разные отображаемые пары и выделить концы background.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-07`.

<a id="as-wheel-08"></a>
### AS-WHEEL-08. Категории, виды и легенда

- **Требования:** [REQ-WHEEL-04](requirements.md#req-wheel-04), [REQ-WHEEL-06](requirements.md#req-wheel-06), [REQ-UI-06](requirements.md#req-ui-06). **Основания:** DP-O-006/012 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 содержит exact/working/background; контролируемые записи F4 охватывают семь публичных type.
- **Данные и действие:** Прочитать легенду без выбора, выбрать exact и working, сравнить HTML.
- **Ожидаемый ответ:** Category/type/orb исходные; новых запросов нет.
- **Ожидаемое состояние:** После решения DP-O-012 exact/working различимы по принятому признаку, вид/категория/пара/орб доступны текстом, ☌ и выделение не противоречат легенде. Конкретные штрихи/цвет/толщина пока условны.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет вычисления категории из экранного orb и одного только цвета как различения; позитивно сопоставить exact и working одного type и все семь типов F4.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-08`.

<a id="as-wheel-09"></a>
### AS-WHEEL-09. Пять ретроградных меток через 0°

- **Требования:** [REQ-WHEEL-05](requirements.md#req-wheel-05), [REQ-UI-04](requirements.md#req-ui-04). **Основания:** DP-O-004/005/011 @ единый реестр / предложение Analyst.
- **Предусловия:** F3; точки mercury/venus/mars/jupiter/saturn ретроградны, долготы 359.70,359.85,0,0.15,0.30°.
- **Данные и действие:** Показать на 1440/768/360 px, последовательно выбрать каждую из HTML и колеса.
- **Ожидаемый ответ:** Контролируемый ChartDTO не меняется.
- **Ожидаемое состояние:** Для каждой точки видны R и связь с истинной отметкой; пять выборов адресуют разные IDs. Порог допустимого разнесения/overlap/fallback принимается DP-O-011, не проверяется по числам spread() прототипа.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет потери/переименования точки или сдвига числового факта; позитивно сопоставить все пять R с пятью правильными строками и точными долготами.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-09`.

<a id="as-wheel-10"></a>
### AS-WHEEL-10. Предельная скученность

- **Требования:** [REQ-WHEEL-05](requirements.md#req-wheel-05). **Основания:** DP-O-004/005/007/011 @ единый реестр / предложение Analyst.
- **Предусловия:** Контролируемая схема F3-max: все 16 points в одном секторе; retrograde true/false чередуются; несколько exact/working conjunction с различными парами.
- **Данные и действие:** Показать 360 px и увеличить текст; проверить доступ ко всем строкам/парам.
- **Ожидаемый ответ:** UI DTO как задан; не заявляется физически возможной engine-картой.
- **Ожидаемое состояние:** Каждый ID/пара остаются доступны. Визуальная пригодность и способ обработки предела пока условны: нужен Owner выбор по Developer/Tester evidence. Этот пример определяет предел review, а не разрешённое скрытие фактов.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет молчаливого удаления points/аспектов; позитивно прочитать 16 ID, каждую заданную пару и верные R в HTML.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-10`.

<a id="as-wheel-11"></a>
### AS-WHEEL-11. Выбор в обоих направлениях и background

- **Требования:** [REQ-WHEEL-04](requirements.md#req-wheel-04), [REQ-WHEEL-07](requirements.md#req-wheel-07), [REQ-UI-06](requirements.md#req-ui-06). **Основания:** DP-O-008/010/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1, раскрытый список points/aspects и чистое выделение.
- **Данные и действие:** Активировать point→строку, строку point→объект; exact/working аспект→строку и обратно; background строку→два конца.
- **Ожидаемый ответ:** Новых HTTP запросов нет.
- **Ожидаемое состояние:** Оба направления адресуют ту же identity и выбранную запись; background выделяет оба конца, включая angle при наличии, без линии/☌. Графическое обозначение exact/working соответствует записи.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет выборки по имени вместо ID и фоновой линии; позитивно пройти оба направления и видимый exact/working графический объект.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-11`.

<a id="as-wheel-12"></a>
### AS-WHEEL-12. Закрытые таблицы и заполненная форма

- **Требования:** [REQ-WHEEL-07](requirements.md#req-wheel-07), [REQ-UI-03](requirements.md#req-ui-03), [REQ-UI-11](requirements.md#req-ui-11). **Основания:** DP-O-003/008/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 видна, подробности закрыты; форма свернута без изменённого черновика.
- **Данные и действие:** Выбрать point на колесе; затем «Изменить данные», изменить время, раскрыть HTML.
- **Ожидаемый ответ:** Нет POST или GET от этих действий.
- **Ожидаемое состояние:** Подсветка относится к F1; форма содержит прежние значения до редактирования, затем новый черновик при прежней сводке. Отображение выбранной строки при закрытых таблицах и focus/scroll условны до DP-O-013.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет автоматического build и замены сводки черновиком; позитивно проверить изменённое значение в редакторе и прежнюю identity/сводку рядом.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-12`.

<a id="as-wheel-13"></a>
### AS-WHEEL-13. Снятие и переключение выделения

- **Требования:** [REQ-WHEEL-07](requirements.md#req-wheel-07), [REQ-WHEEL-08](requirements.md#req-wheel-08), [REQ-UI-06](requirements.md#req-ui-06). **Основания:** DP-O-008/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1; один point/аспект выбран, затем выбран background.
- **Данные и действие:** Активировать «Снять выделение» доступным способом; выбрать другую запись.
- **Ожидаемый ответ:** Локальные действия без HTTP.
- **Ожидаемое состояние:** После снятия ни таблица, ни колесо не содержат прежней отметки; новая выбранная запись однозначна. Повторная активация/клик вне колеса как дополнительный способ пока не утверждены.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет зависшего background endpoint или старой пары; позитивно увидеть исходное выделение и новое после снятия.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-13`.

<a id="as-wheel-14"></a>
### AS-WHEEL-14. Новая identity и повтор той же карты

- **Требования:** [REQ-WHEEL-08](requirements.md#req-wheel-08). **Основания:** DP-O-013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 A с выбором, затем подтверждённая карта B другой identity; вариант повторного current A/stale A.
- **Данные и действие:** Принять B, затем повтор той же B; отдельно изменить только ширину/stale-флаг.
- **Ожидаемый ответ:** Только разрешённые чтения baseline; resize без сети.
- **Ожидаемое состояние:** Нельзя выделить в B запись A. Рекомендация Analysis: при смене identity clear, при том же содержимом/identity сохранить выбор; это условная ветвь DP-O-013. Политика повторного чтения должна иметь принятое expected result.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет переноса индекса аспекта A в массив B; позитивно проверить полную публикацию B, выбранный ранее A и повтор того же B.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-14`.

<a id="as-wheel-15"></a>
### AS-WHEEL-15. Подтверждённые empty и unavailable

- **Требования:** [REQ-WHEEL-08](requirements.md#req-wheel-08), [REQ-UI-01](requirements.md#req-ui-01), [REQ-UI-08](requirements.md#req-ui-08). **Основания:** DP-O-001/003 @ единый реестр / предложение Analyst.
- **Предусловия:** Перед чтением показана A с выбором; следующие ответы F2 empty и known_unavailable в отдельных проходах.
- **Данные и действие:** Успешно выполнить разрешённый current.
- **Ожидаемый ответ:** 200 empty либо chart_unavailable с birth/chart:null.
- **Ожидаемое состояние:** Старые колесо, числовые таблицы и выбор убраны. Empty показывает форму; unavailable показывает сохранённый birth/отказ и доступное явное построение, без рисунка и поддельных пустых рассчитанных таблиц.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет скрытого POST; позитивно проверить успешный ответ каждого состояния и доступные данные birth unavailable.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-15`.

<a id="as-wheel-16"></a>
### AS-WHEEL-16. Композиция на 1440, 768 и 360 px

- **Требования:** [REQ-WHEEL-09](requirements.md#req-wheel-09), [REQ-WHEEL-10](requirements.md#req-wheel-10), [REQ-UI-04](requirements.md#req-ui-04), [REQ-UI-10](requirements.md#req-ui-10). **Основания:** DP-O-002/005/011/012/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 и F3; браузерные viewport управляемы, таблицы доступны.
- **Данные и действие:** Проверить каждую ширину, длинное название места и увеличенный текст.
- **Ожидаемый ответ:** От изменения ширины HTTP отсутствует.
- **Ожидаемое состояние:** 1440: колесо справа от сводки. 360: под сводкой, горизонтального overflow страницы нет; 768 допускает перенос под сводку по содержимому. R/☌/HTML читаемы; конкретный visual acceptance плотности зависит от DP-O-011/012.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет скрытых строк либо horizontal scrolling всей страницы; позитивно проверить края страницы, весь текст сводки и существующие символы/пары.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-16`.

<a id="as-wheel-17"></a>
### AS-WHEEL-17. Stale и временный отказ чтения

- **Требования:** [REQ-WHEEL-08](requirements.md#req-wheel-08), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-08](requirements.md#req-ui-08), [REQ-UI-09](requirements.md#req-ui-09). **Основания:** DP-O-001/003/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 показана; controlled current stale той же карты, затем 503 STATE_READ_FAILED.
- **Данные и действие:** Вернуться во вкладку; доставить указанные ответы, затем успешное чтение.
- **Ожидаемый ответ:** Stale=chart_ready/chart_stale:true; отказ чтения с действующим Retry-After.
- **Ожидаемое состояние:** Stale колесо/факты прежние, метка устаревания видна; отказ чтения не выдаётся за empty/unavailable и не уничтожает подтверждённую карту. Retry и сообщение доступны при свёрнутой форме.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет автоматического пересчёта или выдуманных новых чисел; позитивно сопоставить старые факты и последующее успешное чтение.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-17`.

<a id="as-wheel-18"></a>
### AS-WHEEL-18. Отказ нового build сохраняет карту и черновик

- **Требования:** [REQ-WHEEL-08](requirements.md#req-wheel-08), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-03](requirements.md#req-ui-03), [REQ-UI-09](requirements.md#req-ui-09), [REQ-UI-11](requirements.md#req-ui-11). **Основания:** DP-O-003/013 @ единый реестр / предложение Analyst.
- **Предусловия:** Подтверждённая A, пользователь открыл редактор и ввёл B.
- **Данные и действие:** Отправить B; отдельно вернуть 422 issue, 429 и pre-admission 503; затем валидный контроль.
- **Ожидаемый ответ:** Действующие ErrorDTO/issues/Retry-After; новое ChartDTO отсутствует.
- **Ожидаемое состояние:** Колесо/сводка A, черновик B и разрешённые действия доступны; ошибка поля фокусируема, gate не проставляется автоматически. Форма не скрывает отказ.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет автоматического повторного POST и обновления сводки B; позитивно доказать один явный отказавший POST и последующий успешный ручной контроль.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-18`.

<a id="as-wheel-19"></a>
### AS-WHEEL-19. Потеря POST ответа и ручной повтор B

- **Требования:** [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-03](requirements.md#req-ui-03), [REQ-UI-09](requirements.md#req-ui-09). **Основания:** DP-O-003/010/013 @ единый реестр / предложение Analyst.
- **Предусловия:** A либо empty; B отправлен, листовая сеть теряет ответ; fake clock/deferred из fixtures.
- **Данные и действие:** Доставить потерю ответа; выполнить bootstrap→current: matched/different/old_or_empty и failed-read в отдельных проходах; в разрешённой old_or_empty ветви явно повторить.
- **Ожидаемый ответ:** Нельзя выдумать status/ErrorDTO/Retry-After потерянного ответа; current фактический.
- **Ожидаемое состояние:** Показаны именно current колесо/сводка или подтверждённая A при failed-read, B сохранён отдельно. Old/empty допускает только ручной POST при действующей отметке; failed-read блокирует его. Сообщения/безопасное чтение доступны независимо от формы.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет автоматического POST/ложного утверждения о провале первого расчёта; позитивно проверить успешный safe GET и ровно один отдельный разрешённый retry.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-19`.

<a id="as-wheel-20"></a>
### AS-WHEEL-20. Commit failure и timeout

- **Требования:** [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-03](requirements.md#req-ui-03), [REQ-UI-09](requirements.md#req-ui-09). **Основания:** DP-O-003/010/013 @ единый реестр / предложение Analyst.
- **Предусловия:** A показана, B явно отправлен; управляемые Retry-After/clock.
- **Данные и действие:** Вернуть STATE_COMMIT_FAILED; после delay прочитать current. Отдельно BUILD_TIMEOUT: delay, явное подтверждение restart, bootstrap→current.
- **Ожидаемый ответ:** Сохраняются точные policy baseline; build timeout не заменяется сетевой ошибкой.
- **Ожидаемое состояние:** До сверки исход неопределён, A и B различимы; новый result только из принятого current; проверка/подтверждение restart доступны даже при ранее свёрнутой форме.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет health polling/авто-POST и обхода restart gate; позитивно подтвердить запрос safe current и соответствующую опубликованную identity.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-20`.

<a id="as-wheel-21"></a>
### AS-WHEEL-21. Черновик во время восстановления

- **Требования:** [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-09](requirements.md#req-ui-09), [REQ-UI-11](requirements.md#req-ui-11). **Основания:** DP-O-003/013 @ единый реестр / предложение Analyst.
- **Предусловия:** Initial current удержан leaf promise; пользователь редактирует дату/время/place_id и вручную gate.
- **Данные и действие:** Вернуть saved birth A/ChartDTO A после ввода B; открыть или продолжить редактор.
- **Ожидаемый ответ:** Один подтверждённый current A; редактирование само build не запускает.
- **Ожидаемое состояние:** Сводка/колесо A, редактор B; gate не восстановлен из birth. Рекомендация DP-O-013: изменённый редактор остаётся открыт; окончательный focus/collapse ожидают выбора.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет перезаписи B сохранёнными A и авто-build; позитивно увидеть A на колесе/сводке и B в полях.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-21`.

<a id="as-wheel-22"></a>
### AS-WHEEL-22. Две вкладки, superseded и поздний ответ

- **Требования:** [REQ-WHEEL-01](requirements.md#req-wheel-01), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-09](requirements.md#req-ui-09). **Основания:** DP-O-008/010/013 @ единый реестр / предложение Analyst.
- **Предусловия:** Две реальные coordinator с управляемой общей leaf persistence как recovery.test.mjs; A имеет черновик и старую карту.
- **Данные и действие:** B явно публикует карту; A foreground после/во время pending build. Отдельно already_applied/RESULT_SUPERSEDED→current и dispose→late response.
- **Ожидаемый ответ:** Foreground bootstrap/current coalesces после build; superseded/read outcome согласно baseline.
- **Ожидаемое состояние:** Колесо/HTML/сводка одной фактической identity B, черновик A не перезаписан; после dispose поздний ответ не принят. Нельзя приписать поздний первый commit второму POST.
- **Наблюдаемость:** N по фактически выполненному HTTP пути, U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет клиентского expected_version и авто-POST; позитивно увидеть committed B/current и контролируемо доставленный late response.
- **Sequence:** [Редактирование и recovery](sequence_diagrams/ui/003-edit-and-recovery.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-22`.

<a id="as-wheel-23"></a>
### AS-WHEEL-23. Клавиатура, текст и фокус

- **Требования:** [REQ-WHEEL-10](requirements.md#req-wheel-10), [REQ-UI-10](requirements.md#req-ui-10). **Основания:** DP-O-008/011/012/013 @ единый реестр / предложение Analyst.
- **Предусловия:** F1/F3; без hover; keyboard и доступное дерево браузера.
- **Данные и действие:** Открыть подробности/редактор, выбрать points и exact/working/background, снять выбор, пройти длинные имена и несколько совпадающих ☌.
- **Ожидаемый ответ:** Локальные действия без HTTP.
- **Ожидаемое состояние:** Название/описание SVG и полный HTML доступны, видимый focus, возможность выбора и снятия с клавиатуры. Конкретный focus-order/hit-target/совпадающие маркеры проверяются только после DP-O-013.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет mouse-only функции или единственного цвета как evidence; позитивно активировать каждое действие клавиатурой и прочитать пару/category/orb.
- **Sequence:** [Выбор](sequence_diagrams/ui/002-wheel-table-selection.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-23`.

<a id="as-wheel-24"></a>
### AS-WHEEL-24. Отказ и замена renderer

- **Требования:** [REQ-WHEEL-01](requirements.md#req-wheel-01), [REQ-WHEEL-10](requirements.md#req-wheel-10), [REQ-WHEEL-11](requirements.md#req-wheel-11), [REQ-UI-09](requirements.md#req-ui-09). **Основания:** DP-O-010 @ единый реестр / предложение Analyst.
- **Предусловия:** Подтверждённый F1; leaf шов изображения можно контролируемо отказать; альтернативный renderer по будущему согласованному контракту.
- **Данные и действие:** Отказать изображение при применении F1; проверить безопасное действие. Подключить альтернативное изображение на тех же данных/выборе.
- **Ожидаемый ответ:** Нет автоматического build; accepted HTTP исход и request_id сохраняются.
- **Ожидаемое состояние:** Видимый честный отказ, нет смешения частичного изображения с целой новой картой. Рекомендация Analysis: сохранить HTML при локальном отказе; ожидает DP-O-010. Замена не требует изменения transport/session/calculation, выбор/снятие и identity прежние.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Нет скрытого swallow или повторного расчёта; позитивно показать подтверждённый HTML/исход и затем успешное альтернативное изображение.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-24`.

<a id="as-wheel-25"></a>
### AS-WHEEL-25. Ориентация натала — кандидат для решения

- **Требования:** [REQ-WHEEL-02](requirements.md#req-wheel-02). **Основания:** Предложенный DP-O-014 @ единый реестр / предложение Analyst.
- **Предусловия:** F1 natal, angle asc.longitude берётся из DTO. Для независимого различения 0°/90°/180°/270° — контролируемые UI позиции.
- **Данные и действие:** После решения Owner проверить геометрию по принятому направлению; сравнить с cosmogram 0° Овна.
- **Ожидаемый ответ:** Данные DTO без изменений; сеть не требуется.
- **Ожидаемое состояние:** Рекомендация для консультации: natal ASC слева, долготы возрастают против часовой стрелки; cosmogram 0° Овна слева с тем же направлением. Это условный кандидат, не accepted expected result. Тест фиксирует четыре опорные позиции, включая отсутствие зеркального отражения.
- **Наблюдаемость:** U: упорядоченные действия, принятая identity/источник, видимые состояния DOM/SVG/HTML и сетевой счётчик; условный выбор не выдаётся за runtime evidence.
- **Негативное утверждение и позитивный контроль:** Не считать PNG или ref=100 прототипа эталоном; позитивно сопоставить фактический asc F1 и все четыре контрольные позиции после принятия DP.
- **Sequence:** [Получение и показ](sequence_diagrams/ui/001-chart-presentation.puml). **Clean target:** `docs/requirements/current/ui/scenarios.md#as-wheel-25`.

## Сопоставление с существующим покрытием

Это чтение исходников tests @ MainBaseline, не заключение Tester TESTABLE и не запуск тестов.

| Область | Уже есть в baseline | Добавка и необходимое review |
|---|---|---|
| Факты/IDs/формат | facts.test.mjs: canonical order, angles group, все type/category, formatOrb, immutable DTO, full golden | SVG истинные позиции, angle endpoints, R/☌ и состав линий: AS-WHEEL-03…10 |
| GET/POST и сводка | session.test.mjs: summary belongs to submitted snapshot, rejected later build, current actual birth, unknown/null, explicit gate | Collapse/редактор при прежней карте, колесо сразу: AS-WHEEL-01/02/12/18/21 |
| Empty/stale/unavailable | facts.test.mjs и session.test.mjs: clears old rows, unchanged stale facts, no build | Удаление/сохранение колеса и выбора: AS-WHEEL-14/15/17 |
| Recovery/late/две вкладки | recovery.test.mjs: matched/different/old_or_empty, failed read, STATE_COMMIT_FAILED, BUILD_TIMEOUT, coalescing, dispose, concurrent intents | Те же сценарии с колесом и всегда доступными действиями: AS-WHEEL-19…22; не дублировать coordinator tests без добавочной проверки |
| HTTP whitelist | test_projectors.py: golden, endpoint owner, запрещённые/dangling refs, cosmogram без angles | Renderer использует этот публичный набор, без API expansion: AS-WHEEL-03/04/05 |
| Доставка UI / границы | test_ui_delivery.py, test_module_boundaries.py; текущие пути/разрешённые imports | Developer проверяет доставку нового графического ресурса и прежние инварианты; технические изменения не предписаны Analyst |
| Выбор и доступность | baseline только details button/табличная семантика/identity reset | Двусторонний выбор, focus, снять, совпавшие маркеры: AS-WHEEL-11…14/16/23 |
| Заменяемость/отказ колеса | baseline renderer error safe read; нового wheel seam нет | Согласованный DP-O-010 и позитивный альтернативный renderer / локальный отказ: AS-WHEEL-24 |

Developer: составить технические deterministic regression checks на новых наблюдаемых границах, переиспользовать fixtures/deferred/fakeClock, не мокать сам renderer/координатор. Tester: подтвердить пригодность критериев после DP, viewport/keyboard/визуальные пределы, отдельно оценить покрытие; старый M1-7 PASS не переносится на колесо.
