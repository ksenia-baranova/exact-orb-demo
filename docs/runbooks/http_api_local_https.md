# Локальный HTTP API через Caddy и mkcert

Это M1-6 стенд с одним Uvicorn web process. Caddy завершает HTTPS на
`https://exact-orb.localhost`, Uvicorn слушает только `127.0.0.1:8000`.
Внешний supervisor, production ACL и deployment manifest относятся к M1-12.
Каталог, runtime и их executor открывает один lifespan через
`exact_orb.http_server:create_local_app`; один каталог передаётся и
маршруту `/places`, и `build_application_runtime(places=…)`.

## Подготовка

Установите зависимости проекта, Caddy и mkcert. Запускайте команды из корня
репозитория в PowerShell. Проверенный `data/places.sqlite` приходит с checkout;
для нового выпуска его можно пересобрать из локальных GeoNames-файлов по
[инструкции каталога](../requirements/component_responsibilities/exact-orb_place_catalog.md).
Параметры снимка и атрибуция указаны в [data/README.md](../../data/README.md).
Каталог читается без записи. Для сессий
укажите отдельный файловый SQLite path в существующем каталоге.

```powershell
$repoRoot = (Get-Location).Path
$localDir = Join-Path $env:LOCALAPPDATA 'exact-orb-http'
New-Item -ItemType Directory -Force -Path $localDir | Out-Null
New-Item -ItemType Directory -Force -Path 'logs/http-api' | Out-Null
$env:EXACT_ORB_LOCAL_CERT = Join-Path $localDir 'exact-orb.localhost.pem'
$env:EXACT_ORB_LOCAL_KEY = Join-Path $localDir 'exact-orb.localhost-key.pem'
mkcert -install
mkcert -cert-file $env:EXACT_ORB_LOCAL_CERT -key-file $env:EXACT_ORB_LOCAL_KEY exact-orb.localhost

$env:EXACT_ORB_HTTP_ORIGIN = 'https://exact-orb.localhost'
$env:EXACT_ORB_PLACES_DB = Join-Path $repoRoot 'data/places.sqlite'
$env:EXACT_ORB_SESSION_DB = Join-Path $localDir 'sessions.sqlite3'
$env:EXACT_ORB_EPHEMERIS_PATH = Join-Path $repoRoot 'ephe'
$env:EXACT_ORB_SELENA_METHOD = 'true_perigee'
$env:EXACT_ORB_HTTP_EXPOSE_SCHEMA = '0'
$env:WEB_CONCURRENCY = '1'
```

Храните mkcert key вне репозитория. `EXACT_ORB_HTTP_EXPOSE_SCHEMA=1` временно
включает только `/openapi.json` для локальной проверки; `/docs` и `/redoc`
не регистрируются. При значении `0` все три URL отвечают 404.

## Запуск и проверка одного процесса

В первом терминале запустите Uvicorn без reload и без его proxy-header rewrite:

```powershell
python -m uvicorn exact_orb.http_server:create_local_app --factory --app-dir src --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers --lifespan on --no-access-log --log-config docs/runbooks/http_api_local_logging.json
```

Во втором терминале с теми же `EXACT_ORB_LOCAL_CERT` и
`EXACT_ORB_LOCAL_KEY` запустите Caddy:

```powershell
caddy validate --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile
caddy run --config docs/runbooks/http_api_local.Caddyfile --adapter caddyfile
```

Проверка PID владельца единственного Uvicorn listener и его команды:

```powershell
$listeners = @(Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8000 -State Listen)
$webPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
if ($webPids.Count -ne 1) { throw 'Ожидался ровно один web process на 127.0.0.1:8000' }
Get-CimInstance Win32_Process -Filter "ProcessId = $($webPids[0])" |
    Select-Object ProcessId, CommandLine
```

`http://127.0.0.1:8000/health/live` и `/health/ready` доступны только с
локального host. Caddy отвечает 404 на внешний `/health/*`. Для обычных
запросов Caddy задаёт ровно по одному `X-Forwarded-For` с адресом TLS-клиента
и `X-Forwarded-Proto: https`; приложение доверяет только loopback peer Caddy.
Raw ASGI peer остаётся адресом Caddy, поскольку Uvicorn запущен с
`--no-proxy-headers`.

Локальный Caddy ждёт заголовки ответа от Uvicorn не более 35 секунд после
отправки upstream-запроса. Это ограничение прокси для зависшего запроса,
а не watchdog приложения. Его часы начинаются раньше 30-секундного build
watchdog, который запускается после проверок и admission, поэтому 35 секунд
не гарантируют, что `504 BUILD_TIMEOUT` приложения всегда придёт первым.
Ответ, созданный самим Caddy при timeout, не является `ErrorDTO` приложения
и может не содержать `X-Request-ID`.

[Logging configuration](http_api_local_logging.json) устанавливает DEBUG для
`exact_orb` на **локальном** стенде. События пишутся в
`logs/http-api/local.log` в корне репозитория, с ротацией по 10 MiB и пятью
архивными файлами. После `POST /charts/natal` найдите по `run_id`
`component_message direction=out operation=build_natal` с полной картой в
`BuildNatalSuccess`. DEBUG-события с `operation=context_save` показывают
вызов и итог сохранения, а `session_sqlite_cas_committed` подтверждает
успешный атомарный commit `session_states` и `session_charts`: он содержит
`state_version`, `chart_action` и `calculation_key`. У SQLite-события нет
`run_id`; сопоставьте его с build по `calculation_key` и версии. Бинарный
`StoredChart.payload` в DEBUG не выводится согласно ADR-0041. На конфликте,
откате или неподтверждённом commit событие `session_sqlite_cas_committed` не
пишется. Удалённый M1-профиль сохраняет effective INFO по ADR-0034.
Серверные события Uvicorn идут в stderr. Перед принудительной
остановкой скопируйте `logs/http-api/local.log*` в отдельный каталог
диагностики и сохраните вывод терминала. При штатном выходе Python закрывает
logging handlers через `logging.shutdown()`; принудительная остановка этого
не гарантирует, поэтому копирование делается заранее.

## После 504, unhealthy или fail-fast shutdown без supervisor

`504 BUILD_TIMEOUT` переводит прежний web process в unhealthy; оба health
endpoint возвращают 503. Тот же порядок требуется при
`http_shutdown_finished outcome=fail_fast` во время обычной остановки:
retained native/executor работа может не позволить Uvicorn завершиться самому.
Сохраните диагностический журнал и PID, принудительно завершите **старый**
Uvicorn process (`Stop-Process -Id <PID> -Force`), затем
убедитесь, что listener на `127.0.0.1:8000` исчез. Только после этого
запустите один новый process той же командой. Повторное открытие Caddy не
создаёт новую application runtime.

В deployment внешний supervisor обязан после grace сохранить доступную
диагностику, принудительно завершить старый PID и запустить один новый web
process. Конкретный supervisor и ACL относятся к M1-12. Сохранение ресурсов
через `pop_all()` само по себе не завершает процесс.

После нового ready восстановите существующую cookie через
`POST /session/bootstrap` и выполните `GET /charts/current`. Сравните
сохранённый birth intent и chart с исходным запросом; новый `POST /charts/natal`
возможен только как явное действие пользователя после этой сверки. Нельзя
автоматически повторять POST или считать 503 автоматическим восстановлением.

## Зависший non-build запрос

В M1-6 у bootstrap, current и places нет application watchdog. Возможный
признак зависшего запроса: клиент получил ошибку от прокси без
`X-Request-ID` (её статус зависит от версии и причины; возможен 504) или
продолжает ждать ответ, а прямые проверки
`http://127.0.0.1:8000/health/live` и `/health/ready` дают 200. Публичный
Caddy закрывает `/health/*` ответом 404, поэтому проверяйте внутренний
Uvicorn listener. Proxy 504 не равен `504 BUILD_TIMEOUT` приложения.

В `logs/http-api/local.log*` найдите `http_request_started` и проверьте,
появился ли `http_request_finished` с тем же `request_id`. Например, подставьте
UUID из строки начала и сравните timestamp записей:

```powershell
$requestId = '<UUID из http_request_started>'
Select-String -Path 'logs/http-api/local.log*' -SimpleMatch "request_id=$requestId"
```

Начало без завершения старше 30 секунд — сигнал для диагностики, но одна
непарная запись сама по себе не доказывает постоянное зависание. Сохраните
журнал, включая архивы, и PID Uvicorn. Для восстановления примените тот же
порядок, что при fail-fast: `Stop-Process -Id <PID> -Force`, убедитесь, что
listener `127.0.0.1:8000` исчез, запустите ровно один новый процесс, затем
выполните bootstrap и current для сверки состояния. Не запускайте второй
Uvicorn рядом с зависшим процессом.

## Проверенное и ограничение стенда

На рабочем Python проверены `FastAPI 0.121.2`, `Starlette 0.49.3`,
`Pydantic 2.12.4`, `Uvicorn 0.38.0`, `httpx 0.28.1` и наличие опций `--factory`, `--workers`,
`--no-proxy-headers`, `--lifespan`. Запуск Caddy, mkcert и сетевой smoke в
этом окружении не проверены: их исполняемые файлы отсутствуют. Синтаксис
конфигурации основан на [reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[tls](https://caddyserver.com/docs/caddyfile/directives/tls),
[bind](https://caddyserver.com/docs/caddyfile/directives/bind) и
[mkcert](https://github.com/FiloSottile/mkcert).
В `pyproject.toml` есть верхние границы FastAPI/Uvicorn `<1` и httpx `<0.29`,
но нет lock-файла. Для M1-12 требуется решение о pin/lock при deployment;
локально приведены только фактически проверенные версии. Loopback CIDR
доверяет только локальному Caddy; production trusted proxy и ACL относятся к M1-12.
