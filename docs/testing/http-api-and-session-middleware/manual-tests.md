# Ручные тесты HTTP API и session middleware

**Роль:** Tester<br>
**Контракт:** [HTTP requirements](../../requirements/http_api.md) @ `5df58a0`<br>
**Состояние:** M-01…M-14 повторно выполнены 2026-10-02 на полном локальном каталоге через реальный HTTPS; вызовы всех endpoint записаны в [отдельный журнал прогона](../../../logs/http-api/manual-20261002T203646Z/run.log). Тестовый клиент привязан к `127.0.0.2`; обычный localhost-путь блокируется `FIND-TEST-HTTP-001`. Ниже отдельно приведены ожидаемые шаги Postman и фактическое evidence скриптового live-прогона.<br>
**Среда:** один локальный Uvicorn за Caddy по [runbook](../../runbooks/http_api_local_https.md); для повторения шагов вручную — Postman Desktop либо Postman Web с Desktop Agent.

## 1. Подготовить данные и инструменты

1. Откройте PowerShell в `C:\Users\KateUser\.codex\worktrees\http-api-change\exact-orb-recovered`. Убедитесь, что это ветка `change/http-api-and-session-middleware` и проверяемый commit: `git branch --show-current`; `git rev-parse HEAD`.
2. Проверьте инструменты и входные файлы:

   ```powershell
   python --version
   Get-Command caddy,mkcert
   Test-Path .\data\places.sqlite
   Test-Path (Join-Path $env:LOCALAPPDATA 'exact-orb-http-manual\places-fixture.sqlite')
   Test-Path .\ephe
   ```

   Для прогона нужны Caddy, mkcert, `ephe` и каталог мест. В исходном checkout инструменты и `data/places.sqlite` отсутствовали; первый прогон 2026-10-02 использовал каталог из `tests/fixtures/place_catalog` в `%LOCALAPPDATA%\exact-orb-http-manual\places-fixture.sqlite` (5 мест, 13 имён). Для M-12…M-14 полный ранее собранный GeoNames-каталог скопировали из `C:\Users\KateUser\PycharmProjects\exact-orb-recovered\data\places.sqlite` в `data/places.sqlite` этой ветки (16 329 мест, 36 648 имён; SHA-256 `afa097af657805c420449393b1e3c561c6c3170a3a1084b0189386a37abba0dd`). В текущей ревизии этот же снимок входит в Git. Caddy v2.11.6 и mkcert v1.4.4 установлены через winget. Winget установил исполняемые файлы в `%LOCALAPPDATA%\Microsoft\WinGet\Packages`; в текущем PowerShell `Get-Command` их ещё не находит, поэтому команды ниже разрешают путь сами. Инструкции установки: [Caddy](https://caddyserver.com/docs/install), [mkcert](https://github.com/FiloSottile/mkcert).
3. Если Python-зависимости не установлены, установите проект из этой рабочей копии: `python -m pip install -e '.[dev]'`. Каталог приходит вместе с checkout; проверьте его SHA-256 по [описанию снимка](../../../data/README.md):

   ```powershell
   (Get-FileHash .\data\places.sqlite -Algorithm SHA256).Hash
   ```

   Для нового выпуска получите три локальных GeoNames-файла и выполните [сборку каталога](../../requirements/component_responsibilities/exact-orb_place_catalog.md#26-локальная-сборка):

   ```powershell
   python scripts/build_place_catalog.py --cities cities/cities1000.txt --admin1 cities/admin1CodesASCII.txt --alternate-names cities/alternateNamesV2.txt --out data/places.sqlite
   ```

   Для M-12…M-14 ожидается SHA-256 `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD`; если хэш иной, зафиксируйте версию каталога и пересмотрите ожидаемые имена этих data-specific проверок.

   Сборщик не скачивает входные файлы. Для настоящего расчёта в `ephe` должны быть эфемериды; путь в следующем шаге указывает именно на эту папку.

## 2. Запустить локальный HTTPS-стенд

1. В первом PowerShell из корня репозитория задайте окружение для отдельной ручной базы сессий:

   ```powershell
   $repoRoot = (Get-Location).Path
   $localDir = Join-Path $env:LOCALAPPDATA 'exact-orb-http-manual'
   New-Item -ItemType Directory -Force -Path $localDir | Out-Null
   New-Item -ItemType Directory -Force -Path 'logs/http-api' | Out-Null
   $env:EXACT_ORB_LOCAL_CERT = Join-Path $localDir 'exact-orb.localhost.pem'
   $env:EXACT_ORB_LOCAL_KEY = Join-Path $localDir 'exact-orb.localhost-key.pem'
   $mkcertExe = (Get-Command mkcert -ErrorAction SilentlyContinue).Source
   if (-not $mkcertExe) { $mkcertExe = (Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\FiloSottile.mkcert_*') -Filter mkcert.exe -File -Recurse | Select-Object -First 1).FullName }
   if (-not $mkcertExe) { throw 'mkcert.exe не найден' }
   & $mkcertExe -install
   & $mkcertExe -cert-file $env:EXACT_ORB_LOCAL_CERT -key-file $env:EXACT_ORB_LOCAL_KEY exact-orb.localhost
   $env:EXACT_ORB_HTTP_ORIGIN = 'https://exact-orb.localhost'
   $env:EXACT_ORB_PLACES_DB = Join-Path $repoRoot 'data/places.sqlite'
   $env:EXACT_ORB_SESSION_DB = Join-Path $localDir 'sessions-manual.sqlite3'
   $env:EXACT_ORB_EPHEMERIS_PATH = Join-Path $repoRoot 'ephe'
   $env:EXACT_ORB_SELENA_METHOD = 'true_perigee'
   $env:EXACT_ORB_HTTP_EXPOSE_SCHEMA = '0'
   $env:WEB_CONCURRENCY = '1'
   ```

   Сохраните этот `EXACT_ORB_SESSION_DB` для теста восстановления. Не удаляйте и не заменяйте чужую SQLite-базу.
2. В том же терминале запустите единственный web process. Терминал должен остаться открытым:

   ```powershell
   python -m uvicorn exact_orb.http_server:create_local_app --factory --app-dir src --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers --lifespan on --no-access-log --log-config docs/runbooks/http_api_local_logging.json
   ```

   Если startup завершается ошибкой, устраните указанную причину (каталог, эфемериды, настройки) до HTTP-проверок; не засчитывайте 404 от другого процесса как успех.
   Указанный `http_api_local_logging.json` включает DEBUG только для локального стенда. Полная карта ищется в `logs/http-api/local.log*` по `component_message direction=out operation=build_natal` и `run_id`; подтверждённая запись state + chart — по `session_sqlite_cas_committed` с тем же `calculation_key`. Для удалённого M1-профиля действует INFO.
3. Откройте второй PowerShell в том же корне. Переменные окружения первого терминала сюда не переходят, поэтому повторите пути к сертификату и запустите Caddy:

   ```powershell
   $localDir = Join-Path $env:LOCALAPPDATA 'exact-orb-http-manual'
   $env:EXACT_ORB_LOCAL_CERT = Join-Path $localDir 'exact-orb.localhost.pem'
   $env:EXACT_ORB_LOCAL_KEY = Join-Path $localDir 'exact-orb.localhost-key.pem'
   $caddyExe = (Get-Command caddy -ErrorAction SilentlyContinue).Source
   if (-not $caddyExe) { $caddyExe = (Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\CaddyServer.Caddy_*') -Filter caddy.exe -File -Recurse | Select-Object -First 1).FullName }
   if (-not $caddyExe) { throw 'caddy.exe не найден' }
   & $caddyExe validate --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile
   & $caddyExe run --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile
   ```

   `caddy validate` должен завершиться успешно; `caddy run` остаётся запущенным.

## 3. Настроить Postman и cookie

1. Создайте локальную environment-переменную `base_url = https://exact-orb.localhost`. Все business-запросы ниже отправляйте на этот адрес через Caddy, без завершающего `/` в переменной. **На tested commit стандартное подключение с `127.0.0.1` отвечает `400 FORWARDED_HEADER_INVALID` на bootstrap**; см. `FIND-TEST-HTTP-001` в [Tester artifact](tester.md). Обычный Postman-прогон возможен после исправления этой локальной proxy-конфигурации. Пройденный live-прогон использовал `127.0.0.2` как исходный адрес клиента.
2. Оставьте проверку TLS-сертификата включённой. Если Postman не доверяет локальному CA, в Settings → Certificates включите CA certificates и укажите `rootCA.pem` из каталога, который выводит `mkcert -CAROOT` ([инструкция Postman](https://learning.postman.com/docs/use/send-requests/authorization/certificates)). Для Postman Web нужен Desktop Agent. Если проверка сертификата выключена, отметьте TLS validation как NOT VERIFIED.
3. Перед новым прогоном удалите cookie для `exact-orb.localhost` в Postman Cookies. Для всех business-запросов, кроме отрицательного теста чужого Origin, задайте `Origin: {{base_url}}`. Для POST задайте `Content-Type: application/json`; body выбирайте `raw → JSON`.
4. После первого bootstrap проверьте `Set-Cookie` и фактически отправляемый `Cookie` в следующем запросе через Postman Console/Headers. Должна уходить ровно одна `__Host-exact_orb_session`. Postman документирует ограниченную поддержку `SameSite` и префикса `__Host-` ([cookies](https://learning.postman.com/docs/use/send-requests/response-data/cookies)); поэтому его cookie jar не является проверкой браузерной политики. Если jar не отправляет cookie, скопируйте только значение из `Set-Cookie` в локальную переменную `session_cookie_value`, удалите cookie домена из jar и добавьте к запросам заголовок `Cookie: __Host-exact_orb_session={{session_cookie_value}}`. Не смешивайте автоматическую и ручную cookie и не сохраняйте её значение в общем workspace/экспорте коллекции.

## 4. Пошаговые сценарии

В каждом ответе приложения проверяйте `Cache-Control: no-store` и `X-Request-ID`. Статусы ниже — **ожидаемые** для пошагового Postman-прогона; фактические результаты отдельного HTTPS-прогона приведены в §5.

| ID | Действие в Postman | Ожидаемый результат |
| --- | --- | --- |
| M-01 | `GET http://127.0.0.1:8000/health/live`, затем `/health/ready`; отдельно `GET {{base_url}}/health/live`. | Два внутренних `200`; публичный Caddy отвечает `404` для health. Внешний health-ответ создан proxy, поэтому не требуйте от него app `X-Request-ID`. |
| M-02 | Без прежней cookie: `POST {{base_url}}/session/bootstrap`, raw body `{}`. | `200`, ровно `{"status":"ready","state_version":0}`. Один `Set-Cookie` с `__Host-exact_orb_session`, `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=604800`, без `Domain`. Сохраните значение cookie локально. |
| M-03 | С той же cookie: `GET {{base_url}}/charts/current`. | `200`, `status=empty`, `state_version=0`, `birth=null`, `chart=null`, `chart_stale=null`; cookie обновляется, значение session ID не меняется. |
| M-04 | `GET {{base_url}}/places?query=Москва&limit=10` через Params Postman. | `200`, `items` непустой при полном каталоге GeoNames. Найдите Москву, сохраните её `place_id` в локальной переменной Postman `place_id` (для утверждённого полного каталога — `524901`). У item только `place_id`, `display_name`, `admin1_name`, `country_code`; нет координат и `tz_id`. Поиск не обновляет cookie. |
| M-05 | `POST {{base_url}}/charts/natal`, raw body `{"birth_date":"1990-09-02","birth_time":"14:30","place_id":"{{place_id}}"}`. | `200`, `status=chart_ready`, `chart.kind=natal`, `state_version` увеличился, есть `chart.chart_identity`. Сохраните `state_version` и `chart_identity`. Если вместо этого пришла typed 422/503, сохраните код и проверьте каталог/эфемериды; успех не засчитывайте. |
| M-06 | `GET {{base_url}}/charts/current` с той же cookie. | `200`, `status=chart_ready`; `state_version` и `chart.chart_identity` совпадают с M-05, `birth.birth_time="14:30"`, `chart_stale=false` при неизменной CalculationVersion. Скрытых координат и внутренних полей в DTO нет. |
| M-07 | `POST {{base_url}}/charts/natal` с body `{"birth_date":"1990-09-02","birth_time":null,"place_id":"{{place_id}}"}`; затем `GET {{base_url}}/charts/current`. | `200`, `chart.kind=cosmogram`; `house_system`, `angles`, `houses`, все `points[].house` равны `null`. Current показывает новую карту и `birth.birth_time=null`, `birth.utc_offset_seconds=null`. Сохраните идентичность и версию этой последней карты для M-11. |
| M-08 | `GET /places?query=Москва&limit=010`; затем повторите M-04 с `limit=10`. | Невалидный limit: `422 INVALID_REQUEST`, `detail_code=LIMIT_INVALID`. Позитивный контроль: `200` и тот же найденный `place_id`. |
| M-09 | `GET /charts/current` с `Origin: https://invalid.example`; затем без этого Origin повторите M-06 для текущей карты. | Первый ответ `403 ORIGIN_NOT_ALLOWED`; второй `200` и прежняя идентичность карты. Чужой Origin не меняет session state. |
| M-10 | `POST {{base_url}}/charts/natal` с body `{"birth_date":"1990-02-30","birth_time":null,"place_id":"{{place_id}}"}`; затем `GET {{base_url}}/charts/current`. | `422 INVALID_REQUEST` с issue `birth.date`; карта и версия из M-07 не изменились. |
| M-11 | Штатно остановите Uvicorn через Ctrl+C, дождитесь исчезновения listener `127.0.0.1:8000`, затем повторите команду из §2.2 с теми же `EXACT_ORB_SESSION_DB` и `EXACT_ORB_PLACES_DB`. Caddy и Postman cookie оставьте прежними. Выполните `POST /session/bootstrap` с `{}`, затем `GET /charts/current`. | После нового ready bootstrap вернёт `ready` с сохранённой версией, а current — `chart_ready` с `chart_identity` из M-07. Восстановление не должно запускать новый расчёт; по журналу проверьте отсутствие build-перехода у этих двух запросов. Новый POST не отправляйте. |
| M-12 — 1 символ | На полном каталоге отправьте `GET {{base_url}}/places?query=Н` без `limit` и cookie. | `200`, ровно 10 разных `place_id` (default limit); среди них `Нальчик` `523523`, `Нижний Новгород` `520555`, `Новосибирск` `1496747`. У каждого item только четыре поля §6.3, `Set-Cookie` отсутствует. |
| M-13 — 2 символа | Отправьте `GET {{base_url}}/places?query=Но` без `limit` и cookie. | `200`, ровно 10 разных `place_id`; среди них `Новосибирск` `1496747`, `Новокузнецк` `1496990`, `Новомосковск` `518557`, `Носовка` `699917`. `Нижний Новгород` из M-12 больше не подходит. У item только четыре поля, `Set-Cookie` отсутствует. |
| M-14 — 3 символа | Отправьте `GET {{base_url}}/places?query=Нов` без `limit` и cookie. | `200`, ровно 10 разных `place_id`; точное имя `Нов` `1514856` идёт первым, далее как минимум два разных города `Новосибирск` `1496747` и `Новокузнецк` `1496990`. `Носовка` из M-13 больше не подходит. У item только четыре поля, `Set-Cookie` отсутствует. |

Для M-09 в отдельном запросе измените только `Origin`, сохранив ту же cookie; после проверки верните `Origin: {{base_url}}`. Для M-10 подставьте тот же `place_id` из M-04. Отсутствующая cookie на current должна дать `409 SESSION_REQUIRED`; этот дополнительный контроль выполняйте отдельным запросом с Postman Settings → Disable cookie jar и без ручного `Cookie` header, чтобы не испортить основной сценарий.

Не пытайтесь вручную доказать точную границу 5/30 секунд, конкурентный release permit или результат потерянного commit случайными задержками: их детерминированные проверки находятся в `tests/http_api`. Здесь проверяется реальный HTTPS/процессный путь.

## 5. Фактическое evidence и завершение стенда

1. Для каждого M-01…M-11 запишите PASS/FAIL/NOT RUN, время, HTTP status, важные поля ответа и `X-Request-ID`. В `logs/http-api/local.log*` найдите по `request_id` пару `http_request_started`/`http_request_finished` и существенные `http_message` send/receive. Например: `Select-String -Path 'logs/http-api/local.log*' -SimpleMatch "request_id=<UUID>"`. Для health и unmatched routes request events не ожидаются.
2. В сохранённом evidence редактируйте cookie/session ID и персональные данные рождения. Не прикладывайте приватный ключ CA/host certificate и саму session SQLite. Отмечайте отдельно ответ приложения и ответ Caddy: у proxy timeout/404 может не быть app DTO и `X-Request-ID`.
3. После проверки остановите Caddy и Uvicorn через Ctrl+C. Если Uvicorn не выходит из-за retained work, выполняйте порядок из [runbook](../../runbooks/http_api_local_https.md#после-504-unhealthy-или-fail-fast-shutdown-без-supervisor): сохраните диагностику, завершите старый PID, убедитесь, что listener исчез, и только затем запускайте новый process.

На `5df58a0` использованы Python `httpx` с доверенным `mkcert/rootCA.pem`, сохранением cookie и `HTTPTransport(local_address="127.0.0.2")`; TLS verification оставалась включённой. Повторяемый helper: [live_https_checks.py](live_https_checks.py), команды `python docs/testing/http-api-and-session-middleware/live_https_checks.py phase1`, после штатного перезапуска Uvicorn с той же session SQLite — `python docs/testing/http-api-and-session-middleware/live_https_checks.py phase2`, затем `python docs/testing/http-api-and-session-middleware/live_https_checks.py supplemental`. Для полного каталога и трёх новых проверок: `python -X utf8 docs/testing/http-api-and-session-middleware/live_https_checks.py place_prefixes`. Между фазами cookie и идентичность карты сохраняются только в `%LOCALAPPDATA%\exact-orb-http-manual\smoke-state.json`; после прогона удалите этот файл, не добавляйте его в Git. В этом проходе файл удалён. Это API-прогон, не запуск Postman UI или браузера. Журнал: `logs/http-api/local.log` (локальный, в Git не добавлен).

| ID | Фактический результат 2026-10-02 | Request ID | Статус |
| --- | --- | --- | --- |
| M-01 | Внутренние live/ready `200/200`; внешний health `404` от Caddy. | `d7ded64f`, `0dc7f918`; у Caddy 404 нет app ID | PASS |
| M-02 | Bootstrap `200`, `ready`, version `0`; одна Secure/HttpOnly/`SameSite=Lax` cookie. | `46c2e842` | PASS с `127.0.0.2` |
| M-03 | Current `200`, `empty`, version `0`; дополнительный контроль подтвердил продление той же cookie. | `ea455704`; контроль `bea8d1ef` | PASS с `127.0.0.2` |
| M-04 | Поиск `200`, Москва `place_id=524901`, whitelist полей; cookie не обновлена. | `2c3a62fd` | PASS на fixture-каталоге |
| M-05 | Natal build `200`, `chart_ready`, `kind=natal`, version `1`. | `a6ebb9f9` | PASS |
| M-06 | Current `200`, identity/version совпали с M-05, `birth_time=14:30`, `chart_stale=false`. | `7bde22a7` | PASS |
| M-07 | Cosmogram build/current `200/200`, version `2`; timed fields `null`, сохранена identity. | `788c265e`, `6f187ed1` | PASS |
| M-08 | `limit=010` → `422 LIMIT_INVALID`; `limit=10` → `200` и Москва. | `fe76185c`, `7af78980` | PASS |
| M-09 | Чужой Origin → `403 ORIGIN_NOT_ALLOWED`; допустимый → `200`, прежняя карта. | `acf66abe`, `41b28505` | PASS |
| M-10 | Невалидная дата → `422` с `birth.date`; current `200`, прежние version/identity. | `7dee965c`, `e1d13268` | PASS |
| M-11 | После штатной остановки PID `27768` и старта PID `25592`: bootstrap/current `200/200`, version `2` и identity совпали с M-07; в журнале нет нового execute. | `158937d7`, `311daa95` | PASS |
| Доп. контроль | Current без cookie → `409 SESSION_REQUIRED`; отдельный current продлил одну cookie с тем же ID. | `75481333`, `bea8d1ef` | PASS |

**Отрицательный контроль стенда:** обычный клиент с исходным `127.0.0.1` повторно получил `400 FORWARDED_HEADER_INVALID` на `POST /session/bootstrap`, `X-Request-ID: d1868dab-fe18-4ddf-b465-edcbfce73716`; тот же запрос с источника `127.0.0.2` дал `200`. В `http_server.py` доверен `127.0.0.1/32`, и цепочка из адресов клиента и Caddy на localhost не содержит недоверенного адреса. Это блокирует описанный выше стандартный Postman-путь до исправления `FIND-TEST-HTTP-001`.

### Полный каталог: M-12…M-14

На том же `5df58a0` после подключения `data/places.sqlite` с SHA-256 `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD` запущены один Uvicorn и Caddy. Каталог открыт текущим адаптером, `GET /places` выполнен через настоящий HTTPS с проверкой локального CA и источником `127.0.0.2`. Использовался `EXACT_ORB_SESSION_DB=logs/http-api/sessions-prefix.sqlite3`; каждый запрос отправлен без cookie и без `limit`, так что проверяется default 10. Три сценария ссылаются на [HTTP requirements §6.3](../../requirements/http_api.md#63-get-places) и [place catalog §4.3](../../requirements/component_responsibilities/exact-orb_place_catalog.md#43-поиск-и-ранжирование).

| ID | Фактический ответ, первые имена в порядке выдачи | Request ID | Статус |
| --- | --- | --- | --- |
| M-12 `Н` | `200`, 10 уникальных мест; `Нью-Йорк`, `Новосибирск`, `Нижний Новгород`, …, `Нальчик` | `bb960151-67ec-41f9-8d2f-a833a3a2c801` | PASS |
| M-13 `Но` | `200`, 10 уникальных мест; `Новосибирск`, `Новокузнецк`, `Нортгемптон`, `Новомосковск`, …, `Носовка` | `82982754-3b38-48ec-b455-a83be66d31c5` | PASS |
| M-14 `Нов` | `200`, 10 уникальных мест; точное `Нов`, затем `Новосибирск`, `Новокузнецк`, `Новомосковск`, … | `275c7749-869c-41ee-88df-bff8005f1bad` | PASS |

Во всех трёх ответах соблюдён whitelist полей и отсутствует `Set-Cookie`. В `logs/http-api/local.log` для каждого request ID есть `http_request_started`, передача к `PlaceSearch`, ответ `PlaceSuggestions` и `http_request_finished status=200`. Это три выполненных API-сценария, не ручное нажатие в Postman.

**Граница ожиданий по примерам:** `Нарьян-Мар`, `Новороссийск`, `Новочеркасск`, `Новошахтинск` есть в полном каталоге и находятся по полному имени (`200`), но в первые 10 и даже первые 20 подсказок широких запросов `Н`, `Но`, `Нов` соответственно не попадают. Текущий контракт ограничивает `limit` значением 20 и ранжирует preferred alias выше других актуальных имён; `items` не обещает показать все города на префикс. Решение о другом ранжировании или UX при широком префиксе относится к владельцу требований.

### Повторный полный прогон: журнал вызовов M-01…M-14

2026-10-02 на ветке `change/http-api-and-session-middleware`, commit `5df58a0be6aeaab577664d6bfd6248f908dadbf7`, M-01…M-14 повторно пройдены одним сценарием с перезапуском Uvicorn в M-11. Использован полный `data/places.sqlite` с SHA-256 `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD`, настоящий Caddy/mkcert HTTPS, проверка доверенного CA и исходный адрес клиента `127.0.0.2`. Это скриптовый ручной API-прогон по шагам выше; Postman UI и браузер не запускались.

- [run.log](../../../logs/http-api/manual-20261002T203646Z/run.log) — последовательность всех 25 HTTP-вызовов: метод, URL, статус, `X-Request-ID`, результат каждого шага и итоговая проверка. Значения session cookie в файл не записаны.
- [app.log](../../../logs/http-api/manual-20261002T203646Z/app.log) — отдельный DEBUG-журнал приложения для этого прогона: `http_request_started`/`finished`, межкомпонентные переходы, два полных результата `build_natal` и два события `session_sqlite_cas_committed`. Этот локальный файл содержит данные сессии и карты.

Команды helper: `python -u -X utf8 docs/testing/http-api-and-session-middleware/live_https_checks.py phase1`; после штатной остановки и перезапуска Uvicorn с той же SQLite — `phase2`; затем `supplemental`, `place_prefixes`, `proxy_control`. Вывод каждой команды добавлен в `run.log` через `Tee-Object -Append`. Оба процесса завершены, listener на `80`, `443`, `8000` отсутствует; временный файл cookie удалён. Оба журнала находятся в игнорируемом Git каталоге `logs/` и сохранены только в этой рабочей копии.

Итог: **M-01…M-14 PASS**; 25 HTTP-вызовов, 22 бизнес-запроса и 22 соответствующих `http_request_finished` в `app.log`. Два внутренних health-запроса обходят бизнес-журнал, внешний health `404` сформирован Caddy. Отрицательный контроль обычного `127.0.0.1` снова дал ожидаемый `400 FORWARDED_HEADER_INVALID` (`request_id=edd7fb53-810b-4b48-a54f-953ba996719d`); это воспроизведение открытого `FIND-TEST-HTTP-001`, а не успешный стандартный Postman-путь.

### Уточнение читаемости журнала поиска мест, 2026-10-03

В исходном `run.log` URL содержит стандартную UTF-8 percent-encoding: `%D0%9D` означает `Н`, `%D0%9D%D0%BE` — `Но`, `%D0%9D%D0%BE%D0%B2` — `Нов`. Прежний вывод helper показывал у подсказок только `display_name`, хотя фактический ответ `/places` содержит также `place_id`, `admin1_name` и `country_code`. Это недостаток тестового журнала, не отсутствие страны в HTTP DTO.

Helper обновлён: рядом с закодированным URL печатается исходный `query`, а каждый результат выводится с ID, регионом и кодом страны. На том же полном каталоге повторены M-12…M-14 через Caddy/mkcert HTTPS: [читаемый run.log](../../../logs/http-api/place-readable-20261003T113439Z/run.log) и [DEBUG app.log](../../../logs/http-api/place-readable-20261003T113439Z/app.log). Все три сценария PASS; 3 HTTP-вызова имеют 3 соответствующих `http_request_finished`, выведены 30 подсказок с `country_code`. Первый результат для `Н` — `Нью-Йорк`, `place_id=5128581`, `admin1_name=Нью-Йорк`, `country_code=US`. Это глобальный каталог, поэтому результат допустим по текущему контракту; UI должен различать одноимённые места регионом и страной согласно [UI requirements](../../ui_ux/requirements.md). Старый журнал сохранён как свидетельство первоначального прогона. Новые файлы также локальны и игнорируются Git; процессы остановлены, порты `80`, `443`, `8000` свободны.
