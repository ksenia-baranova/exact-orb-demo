# План тестирования: ui-chart-wheel

**Автор:** Codex / Tester, 2026-10-16; consultation v2 / TASK-T-002. Входы и полномочия — [tester_artifact.md](../tester_artifact.md). **InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`; **MainBaseline:** `535551026af6eedaf2a0aa5c0daa96fa94655ec1`. CandidateSHA не передан.

Контракт: нормативный UI / HTTP baseline плюс предложенный Analyst v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; [DP](../manager_artifact.md#3-единый-реестр-dp) @ InputSHA. Результаты сверки — [реестр замечаний](defects.md): 001/003 CLOSED, 002 OPEN по измерительным условиям. План не утверждает requirements.

## Область и уровни

REQ-WHEEL-01…11 и REQ-UI-01…11, в том числе сохранённые REQ-UI-02/05/07; 30 AS-WHEEL и 23 AS-UI, включая полную MODIFY AS-UI-22. Единственная [матрица покрытия](coverage_matrix.md) содержит run status и пробелы; здесь — проект сценариев.

- Component: геометрия, категории, endpoint IDs, отбор / выбор, стили, immutable DTO. Oracle геометрии — независимые направления и true anchors, не вызов production helper для вычисления expected.
- Integration: реальная страница + coordinator + transport + renderer; fake только HTTP / clock / leaf failure seam. Не подменять renderer mock-объектом при проверке его геометрии.
- Browser: настоящий SVG layout / hit testing / keyboard focus, границы labels/R/☌, отсутствие page overflow. `documentPort` этого не доказывает.
- Regression: существующие UI / HTTP / response / module-boundary checks и затронутые API integrations. На документальном review запускаются проверки документов, не продуктовая acceptance.

## Независимые сценарии

Все T-WHEEL — проект, фактического выполнения нет. Продуктовая семантика v3 сверена; условны только оставшиеся технические критерии DP-O-010…013. F0/F1/F2 — [существующие fixtures](../analyst/scenarios.md); F3/F4 пока описаны как controlled UI data, готовых wheel fixtures / tests нет. Они не заменяют engine golden.

<a id="t-wheel-01"></a>
### T-WHEEL-01. Принятая карта, сводка и черновик

REQ-WHEEL-01/09/11, REQ-UI-01/03/11; AS-WHEEL-01/02/21/22. Bootstrap→current; отдельно committed POST A с удержанным ответом, затем ввод draft B и доставка A. Проверить общую identity колеса / HTML / сводки A, отдельный draft B, отсутствие GET ради POST summary. Позитивный контроль: приняты исходные ответы, успешен один явный POST. Один bootstrap ready сам колесо не создаёт.

<a id="t-wheel-02"></a>
### T-WHEEL-02. Геометрия и опубликованные факты

REQ-WHEEL-01/02, REQ-UI-04/05; AS-WHEEL-03/04/25. F1 и controlled copy: natal anchor=ASC из DTO; cosmogram anchor=0° Овна. При принятом CCW относительные 0/90/180/270° дают слева / снизу / справа / сверху. Проверить 359.99/0/0.01°, 16 IDs, 12 куспидов / пять angles. Moon→asc/mc/vertex соединяет истинные долготы, не сдвинутые значки. Табличные sign/degree/minute/house прежние, ref=100 прототипа не oracle. Контроль запрета новых node-aspects: true_node / south_node видимы как позиции, исходные разрешённые пары сохранены.

<a id="t-wheel-03"></a>
### T-WHEEL-03. Космограмма и пустые наборы

REQ-WHEEL-03/04, REQ-UI-05/06/08; AS-WHEEL-05/06. F0 cosmogram с устойчивой парой; отдельно aspects=[] и только background. Колесо с points остаётся, graphical aspects отсутствуют только в соответствующих случаях; HTML отличает пустой рассчитанный список от houses=null. Нет выдуманных ASC / домов / диапазона Луны / birth time из технического якоря. Контроль: реальные points / пояснения видны, chart_ready отличается от empty.

<a id="t-wheel-04"></a>
### T-WHEEL-04. Категории, типы, ☌ и легенда

REQ-WHEEL-04/06/07, REQ-UI-06; AS-WHEEL-07/08/11. F4: семь типов × три категории, exact/working одного type и одинаково округлённого orb. Категория из DTO: exact сплошной, working пунктирный; выбранная линия толще с прежним цветом / штрихом. Background в HTML, при выборе два конца без линии/☌. Каждая exact/working conjunction-пара адресуется отдельно. У ☌ рядом «точный» / «рабочий»; выбранный символ получает усиленный контур только вокруг символа, подпись остаётся. При выбранном аспекте в таблице одна строка, графически только эта exact/working пара и два конца; у background только концы. Повтор снимает выбор и возвращает общий графический набор. Палитра, измеренное размещение нескольких ☌ / интервалов / толщины ещё OPEN по TEST-FIND-WHEEL-002. Контроль: видимы exact и working, доступны текстовые pair/type/category/orb и соответствующая легенда без hover / цвета.

<a id="t-wheel-05"></a>
### T-WHEEL-05. Разнос и предельная плотность

REQ-WHEEL-02/05/09/10; AS-WHEEL-07/09/10/16. Разрежённый контроль; конфликтующий кластер и далёкая точка; F3: пять R через 0°; F3-max: 16 IDs / несколько ☌. Без конфликта нет смещения / выноски; смещаются только конфликтующие элементы, выноска только при фактическом смещении к истинной отметке; циклический порядок сохранён. Проверить все ID/пары в 1440/768/360. Численный oracle минимальности / границы и предельный fallback BLOCKED по TEST-FIND-WHEEL-002; screenshot golden под реализацию не подгоняется.

<a id="t-wheel-06"></a>
### T-WHEEL-06. Первые пять, выбор и снятие планеты

REQ-WHEEL-07/08/09, REQ-UI-04/05/06; AS-WHEEL-11/12/13/14/26/27 и MODIFY AS-UI-22. 0/1/4/5/6/46 аспектов в порядке DTO: начально min(5,N), при N>5 раскрытие остальных. Natal houses: первые 5 из 12, отдельная кнопка не раскрывает аспекты. Луна с 0/1/5/6 аспектами: все и только инцидентные опубликованные пары сразу, включая angles/background. Другая планета заменяет выбор; повторная активация возвращает первые 5 общего списка. Отдельной кнопки снятия нет. Нет автопрокрутки / переноса focus при выборе планеты. Контроль нулевого отбора — другая планета с непустым набором. Все points видны сразу, опубликованные angles (включая Vertex) — отдельной компактной таблицей; cosmogram без вымышленных углов. Точные место / перестановка строк блока и неактуальное действие при <=5 не назначаются тестом.

<a id="t-wheel-07"></a>
### T-WHEEL-07. Аспект вне отбора, снятие и возврат к планете

REQ-WHEEL-07/08/10, REQ-UI-06; AS-WHEEL-11/13/23/28/29. Уровень: component state transitions → mounted controller / renderer → pointer / keyboard в реальном браузере. F4 содержит moon→asc и sun→mc exact/working; отдельно background / ☌. Выбрать Луну, затем related moon→asc и unrelated sun→mc с колеса в независимых проходах: планета / отбор сняты, таблица одна конкретная строка, графически только выбранная пара и два конца (background — без линии / ☌); сами объекты карты не исчезают. Из режима аспекта выбрать другую планету: аспект снят, все её опубликованные аспекты без лимита пяти. Отдельно начать с общего списка в состоянии пять / все, выбрать аспект и повторно активировать его линию / ☌ / строку: выбора нет, общий графический набор восстановлен, прежнее раскрытие общего списка сохранено, прежний фильтр планеты не возвращается, houses не меняются. Отдельной кнопки снятия нет. Pointer и keyboard дают тот же выбор / снятие; no scroll/focus-transfer при выборе планеты сохранён. Позитивный контроль: обе пары / планета реально выбраны до переходов, exact/working графически видимы, background адресуется через HTML; сравнить одну строку и полный восстановленный набор, identity / DTO и нулевой дополнительный HTTP. TEST-FIND-WHEEL-003 CLOSED по документам; фактическая проверка поведения NOT RUN.

<a id="t-wheel-08"></a>
### T-WHEEL-08. Карта, resize, F5 и automatic current

REQ-WHEEL-08/09, REQ-UI-01/08/09/11; AS-WHEEL-02/14/15/16/17/30. Уровень: component identity/selection reconciliation → mounted coordinator с deferred current → browser resize / reload. Выбрать планету либо moon→asc и раскрыть таблицы A; 1440→360→768 сохраняет состояние без HTTP. F5 сбрасывает выбор / раскрытие до пяти / пяти, снимает gate; первый успешный current после reload восстанавливает факты без build. Принятие собственного нового явного build по изменённым birth data также сбрасывает состояние; ввод / отказ / неопределённый исход не являются reset.

Для automatic foreground/online задать независимые ответы: A той же identity; natal B другой identity с тем же выбранным ID/аспектом и новыми фактами; B с изменённой category пары на background; cosmogram C без выбранного moon→asc; отдельный отсутствующий point и отказ чтения. A/B сохраняют адресуемый выбор / раскрытие, координаты / orb / подписи принадлежат новому DTO; background убирает старую линию / ☌, остаются только два конца. C/отсутствующий point снимают только исчезнувший выбор, сохраняют раскрытие и показывают только реальные общие строки нового DTO. Отказ чтения не доказывает исчезновение выбора. Empty/unavailable убирают числовое представление / колесо / выбор; stale сохраняет факты с отметкой. Открытый dirty draft при automatic current другой карты остаётся видимым / неизменным, сводка обновляется по actual birth ответа. Позитивный контроль: до каждого прохода A и выбор действительно видны; A/B имеют проверяемые разные значения одной пары, C действительно не содержит angle/пару; успешный GET принят, лишнего POST нет. Не подменять этот scenario полным reset по identity.

<a id="t-wheel-09"></a>
### T-WHEEL-09. Отказ build и черновик

REQ-WHEEL-08/11, REQ-UI-02/03/09/11; AS-WHEEL-12/18/21. Уровень: mounted real form/coordinator/renderer с leaf deferred и отдельный browser visibility check. При A открыть форму без HTTP, изменить B; 422/429/capacity не заменяют A / выбор / раскрытие и не прячут issue/retry. Поздний current A либо другой вкладки C не затирает B и не скрывает открытый dirty editor. Парный successful-build контроль: поля совпадают с submitted snapshot — форма сворачивается; появился отличающийся поздний draft — остаётся открытой, summary относится к принятому результату, не к draft. Gate не ставится программно, после reload снят; сохранение draft сквозь F5 не требуется. Контроль: исправленный явный POST успешен, содержит только три исходных поля. Минутный ввод / каталог place_id сохраняются.

<a id="t-wheel-10"></a>
### T-WHEEL-10. Неопределённый исход и lifecycle

REQ-WHEEL-01/11, REQ-UI-03/09/11; AS-WHEEL-19/20/22. Lost POST: matched/different/old_or_empty/failed-read; commit failure: Retry-After и current; timeout: delay + явное restart confirmation → bootstrap/current. Две реальные coordinator: B публикует, A читает current с сохранением draft; superseded/already_applied не создают карту из POST; dispose отбрасывает late reply. Порядок задают deferred / fake clock. Контроль — успешный safe GET и один разрешённый ручной repeat; сообщения и действия доступны при свёрнутой форме.

<a id="t-wheel-11"></a>
### T-WHEEL-11. Отказ и замена renderer

REQ-WHEEL-01/10/11, REQ-UI-09; AS-WHEEL-24. Реальная страница с accepted F1; сначала успешный render, затем отказ только leaf seam колеса: HTML / сводка этой карты доступны, видна ошибка изображения, auto-build нет. Затем успешное изображение / замена на тех же данных; identity / выбор прежние, transport/session/calculation не меняются. Конкретный replacement contract ещё DP-O-010, API не выдумывается. Отдельно сохранить restart/read gates при общем baseline render failure.

<a id="t-wheel-12"></a>
### T-WHEEL-12. Доступность и композиция

REQ-WHEEL-06/09/10, REQ-UI-10; AS-WHEEL-08/16/23. Реальный браузер, без мыши: point / аспект / снятие / обе кнопки таблиц / редактор; текстовые имена, видимый focus, различение без цвета. 1440: колесо справа от сводки; 360: под ней, без overflow страницы; 768 допускает перенос. Длинное имя места, увеличенный текст, пять R / несколько ☌; полные факты доступны в HTML. Hit targets, focus-order и совпавшие markers требуют DP-O-013. Viewport 360 не означает проверку физического телефона.

<a id="t-wheel-13"></a>
### T-WHEEL-13. Валидация и сохранённые границы

REQ-WHEEL-01, REQ-UI-02/03/07; AS-UI-02/05/06/17/18/20/21. Malformed/null/unknown endpoint на существующем validator seam; неподтверждённое место, неизвестное время, gate. Непринятый ответ не доходит до renderer; честная ошибка / baseline recovery. Контроль: валидный DTO принят, разрешённый ручной build успешен. Новые configurations/strength/special_degrees не показываются. Сверхточный неподдерживаемый birth input не вводится.

<a id="t-wheel-14"></a>
### T-WHEEL-14. Наблюдаемость пути

REQ-WHEEL-11; AS-WHEEL-01/02/17…22/24/28/29/30. Связать request_id / build run_id с http_request_started, фактическими http_message send/receive и http_request_finished по HTTP sequences. Отдельный integration/browser trace фиксирует source/identity → колесо и HTML → выбор/снятие/отказ: инициатор, адресат, порядок, исход. Серверный 200 сам не доказывает SVG; скриншот без identity не доказывает весь путь. Runtime-телеметрия не добавляется.

## Порядок будущего выполнения

Документальная сверка Analyst v3 / DP выполнена на InputSHA, закрытые gaps не служат blocker будущих сценариев. До выполнения нужны согласованные технические критерии / стенд / точная версия. После G4 — CandidateSHA / MainBaseline, влияние обновления базы и стенд, фактические node IDs в матрице. Целевые проверки M1-8 → связанные UI/HTTP/boundaries → полный pytest и браузер. Команды определяются реальным handoff, результаты не объявляются заранее. Затем acceptance_report.md с retest / ограничениями; после Owner acceptance — сверка переноса со стабильными IDs и фактическим TestedSHA.

## Прослеживаемость последовательностей

| Sequence Analyst v3 | Независимые проверки | Доказуемый переход / предел |
|---|---|---|
| [001 chart presentation](../analyst/sequence_diagrams/ui/001-chart-presentation.puml) | T-WHEEL-01/02/03/08/11/14 | Accepted source/identity → HTML и SVG той же карты; локальный отказ сохраняет факты; F5 и automatic current различимы |
| [002 selection](../analyst/sequence_diagrams/ui/002-wheel-table-selection.puml) | T-WHEEL-04/05/06/07/08/12/14 | Без выбора / point / aspect, одна строка / пара, повторное снятие, независимое раскрытие, связь true anchors |
| [003 editing/recovery](../analyst/sequence_diagrams/ui/003-edit-and-recovery.puml) | T-WHEEL-01/08/09/10/11/14 | Confirmed / submitted / draft, collapse по snapshot, safe read / restart gates и доступные действия при свёрнутой форме |

Все три sequences сверены чтением на ReviewSHA; рендер PUML и runtime evidence ещё NOT RUN. В матрице каждому требованию назначены T-WHEEL, классы данных / expected result, existing checks и недостающий слой; фактические node IDs новых wheel tests появятся после реализации.
