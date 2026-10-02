# Промт 13b. Сроки non-build запросов и охват событий §12

**Статус:** исполнен 2026-10-02; результаты — §26 implementation plan.
**Зависимость:** 13a.1.
**Основание:** открытые вопросы Analysis/Lead из §25 implementation plan;
решение владельца change от 2026-10-02 после ревью другой моделью.

## Цель и границы

Закрой два открытых решения без изменений production code в `src/`:
принятое ограничение по срокам non-build запросов M1-6 и точный охват
request events §12. Сохрани исторические промты. Не создавай commit,
push или PR без отдельного запроса.

## Решение 1. Срок есть только у build

1. В `docs/requirements/http_api.md` добавь FIND-HTTP-023 типа
   `accepted M1 limitation`: в M1-6 30-секундный watchdog есть только у
   `POST /charts/natal`; зависший `ContextService` или `PlaceSearch` в
   bootstrap/current/places удерживает запрос и executor, health остаётся
   200. Автоматическое обнаружение — условие M1-12. Уточни §9.3, §14 и
   добавь датированную классификацию после исторического §15.1.
2. В Lead-owned change plan запиши как решение владельца change условия
   M1-12: scheduler-based watchdog для всех принятых business requests с
   переводом процесса в unhealthy без изменения публичных ответов; supervisor
   реагирует на `/health/live` 503 и после SIGTERM принудительно завершает
   старый PID в пределах shutdown grace 30 с плюс запас; session SQLite
   лежит на локальной ФС, не NFS/SMB; мониторинг сообщает о
   `http_request_started` без парного `http_request_finished` старше 30 с.
   `HEALTHCHECK` или `Restart=always` без реакции на health недостаточно.
   Сохрани процессный FIND-HTTP-020 до возврата правок в `change/*`.
   Обнови устаревшие сведения о готовности разработки в затронутом плане,
   не объявляя переход «Разработка → тестирование» состоявшимся.
3. В локальном Caddyfile добавь под `reverse_proxy`:
   `transport http { response_header_timeout 35s }`, сохрани `header_up`.
   Сверь синтаксис с официальной документацией. 35 с — срок ожидания
   заголовков upstream после отправки запроса; он **не гарантирует**, что
   application `504 BUILD_TIMEOUT` всегда придёт раньше proxy timeout,
   поскольку application watchdog стартует позже. Это локальное поведение
   прокси, а его ответ не является `ErrorDTO` приложения.
4. В runbook добавь диагностику зависшего non-build запроса: возможный proxy
   timeout/504 без `X-Request-ID` или зависший клиент при health 200;
   проверка журнала `logs/http-api/local.log*` по `request_id` и отсутствию
   парного terminal event старше 30 с; сохранение журнала и PID,
   `Stop-Process -Force`, проверка исчезновения listener, запуск ровно одного
   нового процесса, затем bootstrap/current. Health проверяй напрямую через
   `127.0.0.1:8000`: публичный Caddy блокирует `/health/*`. Укажи, что один
   непарный event — сигнал диагностики, не доказательство вечного зависания.

## Решение 2. §12 относится к совпавшим business-маршрутам

1. В §12 `http_api.md` закрепи, что `http_request_started`, `http_message`,
   `http_admission_rejected`, `http_cookie_replaced`, `chart_unavailable` и
   `http_request_finished` относятся только к совпавшим business routes
   (bootstrap, current, places, build). Правило «ровно один terminal event»
   действует в этой области. Unmatched 404/405, `/health/*` и локальный
   `/openapi.json` сохраняют `X-Request-ID`, но request events не пишут;
   route resolution идёт до §4.1. Переходы health также отражаются событиями
   watchdog, reaper failure и shutdown. Добавь FIND-HTTP-024 типа
   `contract clarification`; расширение на 404/405 с `route=unmatched` без
   сырого path — кандидат для M1-12.
2. Сначала проверь текущее тестовое покрытие. Если отрицательная проверка
   отсутствует, добавь один компактный тест в `tests/http_api/test_lifecycle.py`:
   `GET /nope`, неверный метод для `/session/bootstrap` и
   `GET /health/ready` имеют `X-Request-ID`, но не имеют событий начала и
   завершения с этими ID; успешный `GET /places` даёт ровно одну пару.

## Проверка и отчёт

Проверь, что `src/` не менялся. Если тест добавлен: целевой тест, затем
`python -m pytest tests/http_api -q`, затем полный `python -m pytest -q`.
Выполни `git diff --check`, проверку относительных ссылок и наличие Caddy;
`caddy validate` и сетевой smoke заявляй только после фактического запуска.
В §26 implementation plan запиши два решения, FIND-HTTP-023/024, изменённые
файлы, точные команды и результаты, перенесённые в M1-12 условия.
