# Локальный HTTP API через Caddy и mkcert

Это M1-6 стенд с одним Uvicorn web process. Caddy завершает HTTPS на
`https://exact-orb.localhost`, Uvicorn слушает только `127.0.0.1:8000`.
Внешний supervisor, production ACL и deployment manifest относятся к M1-12.
Каталог, runtime и их executor открывает один lifespan через
`exact_orb.http_server:create_local_app`; один каталог передаётся и
маршруту `/places`, и `build_application_runtime(places=…)`.

## Подготовка

Установите зависимости проекта, Caddy и mkcert. Запускайте команды из корня
репозитория в PowerShell. `data/places.sqlite` должен быть заранее собран из
локальных GeoNames-файлов по [инструкции каталога](../requirements/component_responsibilities/exact-orb_place_catalog.md);
generated artifact не входит в Git. Каталог читается без записи. Для сессий
укажите отдельный файловый SQLite path в существующем каталоге.

```powershell
$repoRoot = (Get-Location).Path
$localDir = Join-Path $env:LOCALAPPDATA 'exact-orb-http'
New-Item -ItemType Directory -Force -Path $localDir | Out-Null
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
python -m uvicorn exact_orb.http_server:create_local_app --factory --app-dir src --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers --lifespan on --no-access-log
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

## После 504 или unhealthy без supervisor

`504 BUILD_TIMEOUT` переводит прежний web process в unhealthy; оба health
endpoint возвращают 503. Сохраните диагностический журнал и PID, принудительно
завершите **старый** Uvicorn process (`Stop-Process -Id <PID> -Force`), затем
убедитесь, что listener на `127.0.0.1:8000` исчез. Только после этого
запустите один новый process той же командой. Повторное открытие Caddy не
создаёт новую application runtime.

После нового ready восстановите существующую cookie через
`POST /session/bootstrap` и выполните `GET /charts/current`. Сравните
сохранённый birth intent и chart с исходным запросом; новый `POST /charts/natal`
возможен только как явное действие пользователя после этой сверки. Нельзя
автоматически повторять POST или считать 503 автоматическим восстановлением.

## Проверенное и ограничение стенда

На рабочем Python проверены `FastAPI 0.121.2`, `Uvicorn 0.38.0`,
`httpx 0.28.1` и наличие опций `--factory`, `--workers`,
`--no-proxy-headers`, `--lifespan`. Запуск Caddy, mkcert и сетевой smoke в
этом окружении не проверены: их исполняемые файлы отсутствуют. Синтаксис
конфигурации основан на [reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[tls](https://caddyserver.com/docs/caddyfile/directives/tls),
[bind](https://caddyserver.com/docs/caddyfile/directives/bind) и
[mkcert](https://github.com/FiloSottile/mkcert).
