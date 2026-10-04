# Сценарии приёмки: ui-birth-form-and-facts

**Статус:** READY FOR REVIEW; действие отправки зависит от `DP-UI-04`, новые блоки ответа — от `DP-UI-02`, состав формы/CTA — от `DP-UI-05`.
**Версия требований:** [requirements.md](requirements.md) в ветке `analysis/ui-birth-form-and-facts` с базой `652bd73405db0a0611e98e81af6f3f668dd429f6`; сценарии и требования версионируются одним commit Analysis. **Исходный HTTP baseline:** `docs/requirements/http_api.md` и ADR-0008, 0029–0034, 0039–0041 @ тому же входному commit. **Целевые чистовые сценарии:** `docs/requirements/current/ui/scenarios.md` и `docs/requirements/current/http-api/scenarios.md` после поставки.

Все проверки API используют HTTPS, одну настоящую cookie jar и ответы без кэша. Числа проверяются по сохранённому артефакту/контрактным fixtures, а не по PNG. Для controllable отказов и конкурентности Tester использует fake clock/barrier/Event на соответствующем шве; `sleep` не является доказательством порядка. В каждом ответе проверяются `X-Request-ID` и `Cache-Control: no-store`; для 429/503/504 — соответствующий `Retry-After` по `http_api.md` §4.4.

| Требование | Сценарии |
|---|---|
| REQ-UI-01 | AS-UI-01, AS-UI-10, AS-UI-11 |
| REQ-UI-02 | AS-UI-02, AS-UI-04, AS-UI-05, AS-UI-06, AS-UI-18 |
| REQ-UI-03 | AS-UI-03, AS-UI-06, AS-UI-12, AS-UI-13, AS-UI-14, AS-UI-17 |
| REQ-UI-04 | AS-UI-07, AS-UI-08, AS-UI-09, AS-UI-15 |
| REQ-UI-05 | AS-UI-07, AS-UI-08, AS-UI-09 |
| REQ-UI-06 | AS-UI-07, AS-UI-08, AS-UI-09, AS-UI-15, AS-UI-16 |
| REQ-UI-07 | AS-UI-07, AS-UI-08, AS-UI-09, AS-UI-15 |
| REQ-UI-08 | AS-UI-10, AS-UI-11 |
| REQ-UI-09 | AS-UI-12, AS-UI-13, AS-UI-14, AS-UI-16, AS-UI-18 |
| REQ-UI-10 | AS-UI-02, AS-UI-19 |
| REQ-API-UI-01 | AS-UI-07, AS-UI-10, AS-UI-15, AS-UI-16 |
| REQ-API-UI-02 | AS-UI-07, AS-UI-08, AS-UI-09, AS-UI-15 |
| REQ-API-UI-03 | AS-UI-07, AS-UI-09, AS-UI-15 |

Наблюдаемость существенных переходов: `http_request_started` → парные `http_message send/receive` с `request_id`, `peer`, `operation`, `message_type` для фактического ContextService/admission/PlaceSearch/Orchestrator/session_view → `http_request_finished`. Build несёт `run_id=request_id`; его application-пары продолжаются на Handler → resolver → artifact → to_stored → ContextService.save. Отказ/отмена может иметь send и terminal/error вместо ложного receive. При admission отказе есть `http_admission_rejected`, при safe unavailable — ERROR `chart_unavailable`. Клиентские события UI могут проверяться браузерным evidence; серверные журналы не обязаны логировать каждое нажатие.

### AS-UI-01. Первый вход и пустая сессия

- **Требования:** REQ-UI-01, REQ-UI-03. **Предусловия:** нет cookie, сервер готов, session create разрешён.
- **Данные и действие:** открыть UI; затем, без нажатия build, дождаться bootstrap и current.
- **Ожидаемый ответ:** `POST /session/bootstrap {}` → 200 `ready/state_version=0` и Secure cookie; `GET /charts/current` → 200 `empty`, `birth:null`, `chart:null`, `chart_stale:null`.
- **Ожидаемое состояние:** видна чистая форма, без фактов карты и без POST build.
- **Наблюдаемость:** отдельные request IDs; bootstrap `ContextService.create`, current `ContextService.load → session_view`, outcome `empty`.
- **Негативное утверждение и позитивный контроль:** нет вызова resolver/engine при входе; успешный bootstrap и current доказывают, что путь не был пропущен.
- **Sequence:** `http_api/001-session-bootstrap.puml`, `004-current-chart.puml`; `session/002-session-restore-on-return.puml`.

### AS-UI-02. Выбор двух одноимённых мест

- **Требования:** REQ-UI-02, REQ-UI-10. **Предусловия:** каталог содержит два `Кировск` с разными `place_id`, `admin1_name`/`country_code`.
- **Данные и действие:** ввести `Кировск`, дождаться GET; пройти варианты стрелками, выбрать Enter; отдельно повторить выбор мышью и отредактировать выбранный текст.
- **Ожидаемый ответ:** `GET /places?query=Кировск` → 200 `items[]` с прежним ключом `admin1_name`; каждый вариант различим по региону и стране; cookie не требуется.
- **Ожидаемое состояние:** выбран только ID подсвеченного варианта; после редактирования ID сброшен до нового выбора; фокус и выбранное состояние доступны с клавиатуры.
- **Наблюдаемость:** `AdmissionControl.reserve → PlaceSearch.search`, связанный request ID; браузерное evidence выбора.
- **Негативное утверждение и позитивный контроль:** свободный текст и невыбранный старый ID не уходят в build; после повторного выбора корректный ID уходит в AS-UI-03.
- **Sequence:** `http_api/002-place-search.puml`, `place_catalog/001-search-place-success.puml`.

### AS-UI-03. Известное время и успешный натал

- **Требования:** REQ-UI-02, 03, 05–07, REQ-API-UI-01/02. **Предусловия:** живая cookie, выбранный ID, доступна отдельная страница условий по ADR-0034, checkbox снят по умолчанию, решения DP-UI-02/04 получены.
- **Данные и действие:** дата `1985-09-02`, `14:30`, выбранный `place_id`; попытаться построить до отметки, открыть условия, активно отметить ознакомление, однократно нажать CTA построения.
- **Ожидаемый ответ:** ровно один POST с тремя полями; `200 chart_ready` с `kind:natal` и расширенным ChartDTO, если commit состоялся.
- **Ожидаемое состояние:** факты шести групп относятся к одному `chart_identity`; время известно; форма не отправляет имя/checkbox/координаты; данные формы доступны для исправления.
- **Наблюдаемость:** `http_message` admission, Orchestrator.execute, application переходы до `ContextService.save`, terminal Committed и request finished под `run_id=request_id`.
- **Негативное утверждение и позитивный контроль:** до активной отметки POST не отправляется; после неё успешный committed result доказывает выполнение, а двойной click не создаёт второй POST. Отметка не появляется в JSON запроса или сохранённом birth.
- **Sequence:** `http_api/003-build-natal.puml`.

### AS-UI-04. Явно неизвестное время и космограмма

- **Требования:** REQ-UI-02, 05–08, REQ-API-UI-02. **Предусловия:** дата/место валидны, gate отправки разрешён.
- **Данные и действие:** отметить «Точное время неизвестно», даже если раньше введено `12:00`; явно построить.
- **Ожидаемый ответ:** POST содержит `birth_time:null`; `chart.kind=cosmogram`, `house_system:null`, `angles:null`, `houses:null`, каждое `points[].house:null`, `strength:null`, `special_degrees:null`, `configurations` — рассчитанный список, возможно непустой; у восстановленного `birth` время и offset также `null`.
- **Ожидаемое состояние:** таблицы планет/устойчивых аспектов/конфигураций возможны, дома и сила названы неприменимыми; нет технического noon/offset, диапазона Луны или ASC.
- **Наблюдаемость:** build с тем же `run_id` и следующий current с отдельным request ID.
- **Негативное утверждение и позитивный контроль:** неизвестное время не превращено в natal; позитивно проверены опубликованные points и хотя бы одна поддерживаемая конфигурация из cosmogram fixture.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-05. Пустое или противоречивое время

- **Требования:** REQ-UI-02, 03. **Предусловия:** дата и место выбраны.
- **Данные и действие:** оставить время пустым без отметки; затем ввести недопустимое `24:00`; затем указать допустимое `00:00` и `12:00` в двух отдельных построениях.
- **Ожидаемый ответ:** пустое/недопустимое поле не отправляет POST до исправления; допустимые значения отправляются как строки `HH:MM` и строят natal, а не cosmogram.
- **Ожидаемое состояние:** дата и выбранный ID сохраняются между исправлениями; отметка неизвестности не меняется автоматически.
- **Наблюдаемость:** отсутствие серверного build для client validation; для позитивных запросов полный build trace.
- **Негативное утверждение и позитивный контроль:** запрет POST подтверждён сетевым наблюдением, а валидные крайние времена подтверждают рабочий путь.
- **Sequence:** `http_api/003-build-natal.puml` только для валидных действий.

### AS-UI-06. Ошибки даты, локального времени и места

- **Требования:** REQ-UI-02, 03. **Предусловия:** активная сессия; управляемые данные каталога/resolver.
- **Данные и действие:** отправить schema-invalid дату `1990-02-30`, затем валидную, но неподдерживаемую дату/локальную дату без существующих минут; отдельно известную локальную минуту в gap и fold выбранной IANA-зоны; затем ранее выбранный ID, больше не разрешимый каталогом.
- **Ожидаемый ответ:** schema case — 422 `INVALID_REQUEST`, `issues.birth.date/INVALID`; domain range — 422 `INPUT_REQUIRED`, `birth.date/UNSUPPORTED` с `constraints`; несуществующая локальная дата — `birth.date/INVALID`; gap/fold при известном времени — `INPUT_REQUIRED` с `birth.time/INVALID` либо `birth.time/AMBIGUOUS` соответственно; место — `birth.place/INVALID`. Эти результаты имеют приоритет по §4.1 и текущему resolver, а не по часовому поясу браузера.
- **Ожидаемое состояние:** прежняя карта, если была, не заменена; поля и выбор остаются для исправления, issue показан рядом с полем.
- **Наблюдаемость:** schema refusal заканчивается до Orchestrator; domain case достигает resolver через Handler.
- **Негативное утверждение и позитивный контроль:** `user_message` не подменяется Pydantic detail; рядом есть валидная дата/ID, приводящие к AS-UI-03.
- **Sequence:** `http_api/003-build-natal.puml`.

### AS-UI-07. Шесть непустых групп натала и формат

- **Требования:** REQ-UI-04–07, REQ-API-UI-01–03. **Предусловия:** контролируемый полный natal artifact с аспектом, конфигурацией, силой и истинным degree flag; допущение DP-UI-02 утверждено.
- **Данные и действие:** получить committed POST и открыть таблицы; затем прочитать current с той же cookie.
- **Ожидаемый ответ:** оба `ChartDTO` совпадают по `chart_identity`, `points`, `houses`, `aspects`, `configurations`, `strength`, `special_degrees`; конфигурация содержит разрешимые роли и канонические рёбра.
- **Ожидаемое состояние:** все шесть групп видимы; позиции `ДД°ММ′` из `degree/minute`, `R` только для true; 12 домов по номеру; точные и все аспекты доступны; сила показывает систему и готовые scores/category; особый градус показывает рассчитанный флаг без дробного `degree_in_sign`.
- **Наблюдаемость:** build trace и current `load → session_view`; два независимых request ID связываются сохранённым `chart_identity` в ответах, без требования логировать полный payload на INFO.
- **Негативное утверждение и позитивный контроль:** в отдельном UI DTO fixture изменение только `longitude` при неизменённых опубликованных degree/minute не меняет табличный текст; непустые позитивные строки доказывают чтение API, а не пустой шаблон.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-08. Космограмма с устойчивой конфигурацией

- **Требования:** REQ-UI-04–07, REQ-API-UI-01/02. **Предусловия:** `chart_artifact_format_1_cosmogram_1985.bin` или эквивалентный fixture с устойчивым T-square и без домов/силы.
- **Данные и действие:** построить без времени и восстановить карту.
- **Ожидаемый ответ:** `configurations` непустой и все его рёбра присутствуют в `aspects`; `houses/angles/strength/special_degrees` равны `null`.
- **Ожидаемое состояние:** T-square виден; секции домов, силы и градусов содержат пояснение о неприменимости, не фиктивные строки. Орбисы аспектов космограммы подписаны как консервативные значения, без заявления о точном моменте.
- **Наблюдаемость:** committed build и current projection; INFO не содержит расчётного payload.
- **Негативное утверждение и позитивный контроль:** не показаны исключённые неустойчивые пары; положительный контроль — опубликованная устойчивая конфигурация и её рёбра.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-09. Рассчитано, но результатов нет

- **Требования:** REQ-UI-04, 06, 07, REQ-API-UI-02. **Предусловия:** валидный natal fixture без конфигураций и истинных особых флагов; отдельный fixture без аспектов, если поддерживается соответствующим расчётом.
- **Данные и действие:** открыть таблицы после build/current.
- **Ожидаемый ответ:** `configurations:[]`, `special_degrees:[]`, а не `null`; `strength` остаётся объектом; рассчитанный `aspects:[]` явно пуст.
- **Ожидаемое состояние:** «Конфигурации не найдены», «Особые градусы не найдены», «Аспекты не найдены»; остальные рассчитанные группы продолжают отображаться.
- **Наблюдаемость:** нормальный build/current путь, без projector error.
- **Негативное утверждение и позитивный контроль:** пустота не маскирует отсутствие всего `chart`; видны опубликованные точки и natal дома.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-10. Восстановление без расчёта

- **Требования:** REQ-UI-01, 08, REQ-API-UI-01. **Предусловия:** сохранённый natal или cosmogram и живая SQLite-сессия; новый runtime с пустым cache.
- **Данные и действие:** reload страницы с той же cookie после restart.
- **Ожидаемый ответ:** bootstrap `ready`, затем current `chart_ready/chart_stale:false`; тот же `chart_identity` и те же факты шести групп, что committed POST.
- **Ожидаемое состояние:** прежняя карта показана, `state_version` не увеличен чтением.
- **Наблюдаемость:** `ContextService.load` на bootstrap и current, `session_view` только на current; нет Orchestrator/engine/cache.
- **Негативное утверждение и позитивный контроль:** engine не вызван; полный ответ карты и существующая cookie доказывают restore.
- **Sequence:** `http_api/001-session-bootstrap.puml`, `004-current-chart.puml`; `session/002-session-restore-on-return.puml`.

### AS-UI-11. Устаревшая и недоступная сохранённая карта

- **Требования:** REQ-UI-01, 08. **Предусловия:** две отдельные сессии: валидный StoredChart с отличающейся текущей CalculationVersion; safe decode или проверка инвариантов внутри `session_view` отказывает без нарушения структуры агрегата.
- **Данные и действие:** bootstrap → current в каждой сессии, затем только явное нажатие rebuild во второй.
- **Ожидаемый ответ:** stale — 200 `chart_ready/chart_stale:true` с прежней картой; unavailable — 200 `chart_unavailable`, `birth` сохранён, `chart:null`, `chart_stale:null`; нажатие создаёт новый POST.
- **Ожидаемое состояние:** stale показывает старые факты и «Пересчитать»; unavailable не показывает таблицы и предлагает «Построить заново»; поля birth предзаполнены.
- **Наблюдаемость:** current `load → session_view`, у unavailable ERROR `chart_unavailable(request_id,safe_reason)` без payload; build trace только после действия.
- **Негативное утверждение и позитивный контроль:** ни одно чтение не строит карту; positive — явно вызванный rebuild может вернуть `chart_ready`.
- **Sequence:** `http_api/004-current-chart.puml`, `003-build-natal.puml`.

### AS-UI-12. Утерянная сессия и сохранение черновика

- **Требования:** REQ-UI-03, 09. **Предусловия:** введённая форма, истёкшая/отсутствующая cookie, контролируемые server outcomes.
- **Данные и действие:** отправить валидный build либо current; получить 409 `SESSION_REQUIRED/EXPIRED/NOT_FOUND`; выполнить bootstrap → current.
- **Ожидаемый ответ:** 409 очищает cookie по HTTP контракту; bootstrap создаёт новую сессию, current возвращает `empty`, если чужой карты нет.
- **Ожидаемое состояние:** дата, время/отметка и ранее выбранный `place_id` остаются в черновике текущей вкладки; новая сессия не объявляется прежней картой; новый build только по действию пользователя.
- **Наблюдаемость:** 409 request, затем отдельные `ContextService.create`, `load → session_view`; нет второго `execute` без click.
- **Негативное утверждение и позитивный контроль:** auto POST отсутствует; позитивный контроль — явный click после восстановления строит карту.
- **Sequence:** `http_api/001-session-bootstrap.puml`, `003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-13. Rate и capacity до запуска build

- **Требования:** REQ-UI-03, 09. **Предусловия:** управляемый admission отвергает поиск или build до execute.
- **Данные и действие:** выполнить place search и явный build при 429; затем build при 503 `BUILD_CAPACITY_EXHAUSTED`/`SERVICE_SHUTTING_DOWN`.
- **Ожидаемый ответ:** типизированный ErrorDTO, `Retry-After` (429 вычисленный, capacity 1, shutdown 30); нет committed карты.
- **Ожидаемое состояние:** ввод и выбор сохраняются; виден таймер/условие следующего явного действия. Поиск можно повторить после срока; build не повторяется автоматически.
- **Наблюдаемость:** для rate/capacity есть `AdmissionControl.reserve` и `http_admission_rejected`; lifecycle `SERVICE_SHUTTING_DOWN` завершается до admission. Во всех случаях нет `ApplicationOrchestrator.execute`.
- **Негативное утверждение и позитивный контроль:** квота/permit не расходуется отказом; после допуска явный build проходит и даёт AS-UI-03.
- **Sequence:** `http_api/002-place-search.puml`, `003-build-natal.puml`.

### AS-UI-14. Неопределённый исход commit и timeout

- **Требования:** REQ-UI-03, 09. **Предусловия:** управляемый `StateCommitFailed` после commit attempt; отдельно watchdog build 30 секунд, unhealthy/restart.
- **Данные и действие:** один явный POST, затем сверка по code-specific правилу.
- **Ожидаемый ответ:** 503 `STATE_COMMIT_FAILED` + `Retry-After:1`, либо 504 `BUILD_TIMEOUT` + `retryable:false`, `Retry-After:5`, без `Set-Cookie`. После 503 — current после 1 секунды; после 504 — дождаться readiness/restart, bootstrap, затем current после заданного срока.
- **Ожидаемое состояние:** исходный intent остаётся видимым. Если current birth совпадает, показывается сохранённая карта; если отличается, актуальная карта/конфликт; old/empty после подтверждённого restart допускает новый **явный** POST.
- **Наблюдаемость:** retained owner и его terminal/error без ложного release при 504; отдельный request ID у recovery GET; трасса ContextService на current.
- **Негативное утверждение и позитивный контроль:** никакого автоматического второго execute; позитивный контроль — оба варианта commit (состоялся/не состоялся) дают согласованный current после управляемого завершения.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-15. Публичная проекция отказывает безопасно

- **Требования:** REQ-UI-04–07, REQ-API-UI-01–03. **Предусловия:** один валидный artifact и варианты с dangling role/edge, неверной вложенностью, несовпадающим special-degree point или внутренним неизвестным полем.
- **Данные и действие:** получить проекцию через committed POST и restored current.
- **Ожидаемый ответ:** валидный artifact даёт полный DTO; небезопасная ссылка/рассинхронизация не даёт частичных таблиц, а даёт safe `500 INTERNAL_FAILURE` по правилам соответствующего endpoint. Неизвестное внутреннее поле не публикуется.
- **Ожидаемое состояние:** UI показывает общую ошибку и сохраняет форму/ранее подтверждённую карту до выяснения текущего состояния; не отображает сомнительные строки.
- **Наблюдаемость:** projector failure завершается 500 с request ID; подробная причина остаётся внутренней. На INFO не сериализуется artifact.
- **Негативное утверждение и позитивный контроль:** raw `ChartArtifact.model_dump()` никогда не уходит клиенту; валидный контроль содержит непустые конфигурацию, силу и special degree.
- **Sequence:** `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-16. Две вкладки и superseded

- **Требования:** REQ-UI-01, 09, REQ-API-UI-01. **Предусловия:** A и B разделяют cookie и карту N; управляемые два намерения.
- **Данные и действие:** B явно строит N+1, затем A возвращается в foreground; отдельно конкурентные POST с исходным N дают `RESULT_SUPERSEDED` или `already_applied` по действующему контракту.
- **Ожидаемый ответ:** A bootstrap → current получает B `chart_identity` и факты; при superseded/already_applied текущая карта читается отдельным GET.
- **Ожидаемое состояние:** A показывает фактическую карту B, не выдаёт старую N за актуальную; draft A не отправляется сам.
- **Наблюдаемость:** отдельные request/run IDs для двух POST и current, CAS outcome в application events; порядок задаётся barrier, не `sleep`.
- **Негативное утверждение и позитивный контроль:** локальный `state_version` A не отправлен как expected; B committed result и A current доказывают обновление.
- **Sequence:** `session/006-two-tabs-rebuild-and-restore.puml`, `http_api/003-build-natal.puml`, `004-current-chart.puml`.

### AS-UI-17. Приоритет transport validation и IssueDTO

- **Требования:** REQ-UI-03. **Предусловия:** клиент с отсутствующей cookie; тестовый HTTP клиент может отправить намеренно неправильное тело и чужой Origin.
- **Данные и действие:** отправить invalid JSON/date без cookie; затем валидный JSON без cookie; затем чужой Origin с невалидным body.
- **Ожидаемый ответ:** первый — 422 `INVALID_REQUEST` и стабильные `issues`; второй — 409 `SESSION_REQUIRED`; третий — 403 `ORIGIN_NOT_ALLOWED`. `IssueDTO` допускает только `field/code/candidates?/constraints?`, не старый shape `ui_ux/decisions.md`.
- **Ожидаемое состояние:** UI корректно связывает `birth.date/time/place` с полем и не показывает internal detail.
- **Наблюдаемость:** только `http_request_started/finished` до component boundary у отклонённых запросов.
- **Негативное утверждение и позитивный контроль:** не происходит build/admission; валидный same-origin/cookie request из AS-UI-03 подтверждает, что путь работает.
- **Sequence:** `http_api/003-build-natal.puml`.

### AS-UI-18. Пустой поиск и отказ каталога

- **Требования:** REQ-UI-02, 09. **Предусловия:** управляемый каталог возвращает `items:[]`, затем `PLACE_CATALOG_UNAVAILABLE`; отдельно `InvalidPlaceQuery`.
- **Данные и действие:** искать строку без совпадений; затем повторить при отказе; затем проверить пустой/слишком длинный query.
- **Ожидаемый ответ:** 200 `items:[]`; 503 + `Retry-After:5`; 422 `INVALID_PLACE_QUERY` либо `INVALID_REQUEST/QUERY_TOO_LONG` по границе.
- **Ожидаемое состояние:** явные состояния «Место не найдено»/«Поиск временно недоступен»/ошибка ввода; ранее введённые дата и время сохранены; без выбранного ID build недоступен.
- **Наблюдаемость:** нормальный поиск проходит `PlaceSearch.search`; grammar rejection не вызывает каталог.
- **Негативное утверждение и позитивный контроль:** `items:[]` не превращается в выбранный ID; положительный контроль — валидный query даёт выбираемую подсказку AS-UI-02.
- **Sequence:** `http_api/002-place-search.puml`.

### AS-UI-19. Доступность и узкий экран

- **Требования:** REQ-UI-10 и 02, 04–07. **Предусловия:** браузер по HTTPS на ширинах 360, 768 и 1440 px; натал с длинными таблицами и ошибкой поля.
- **Данные и действие:** пройти форму, варианты места, ошибки и все секции с клавиатуры; просмотреть на каждой ширине.
- **Ожидаемый ответ:** сетевые ответы не меняют схему от размера экрана.
- **Ожидаемое состояние:** фокус различим, поле/ошибка доступны, все шесть групп читаемы без горизонтального скролла страницы; цвет не единственный индикатор ретроградности, категории или ошибки.
- **Наблюдаемость:** браузерное/визуальное evidence с указанием среды и tested commit; серверные request IDs для пройденных операций.
- **Негативное утверждение и позитивный контроль:** скрытие числового блока на 360 px не считается адаптивностью; положительно проверены все группы и доступные действия.
- **Sequence:** UI действие → соответствующие `http_api/001`…`004` без нового server lifecycle.

## Условия решения и границы проверки

AS-UI-03/04/07–09/15 описывают целевое поведение **после** решения `DP-UI-02/04`; до решения они служат review/test planning, а не зелёной приёмкой. Текущие тесты `tests/http_api/test_projectors.py`, `test_place_dto.py`, `test_session.py`, `test_integration.py` проверяют M1-6, но не браузерный M1-7 и не новые DTO блоки. Tester сначала готовит независимые контрпримеры, затем сопоставляет с существующими тестами. Локальное `FIND-TEST-HTTP-001` из предыдущего change остаётся известным ограничением browser evidence, а обход не превращает стандартный localhost путь в PASS.
