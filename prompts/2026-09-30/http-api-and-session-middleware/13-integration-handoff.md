# Промт 13. Наблюдаемость, локальный запуск и итоговая приёмка

**Статус:** не начато. **Зависимость:** промты 05–12.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 13.

## Что и зачем делаем

Отдельные endpoint могут проходить тесты, но change готов только когда полный путь от HTTPS-запроса до component outcome воспроизводим по журналу, а запуск и остановка проверены вместе. Итоговая приёмка собирает эти свидетельства перед Development PR.

## Задача

Сверь четыре HTTP sequence и session 001–003/006 с фактическими INFO http_request_started, http_message send/receive, http_admission_rejected, http_cookie_replaced, chart_unavailable, http_request_finished, reaper и shutdown. Для каждой существенной стрелки проверь peer/operation/type/order/outcome и request_id/run_id; payload, cookie, session ID, IP и birth data не добавляй в компактные INFO. Исправь подтверждённое расхождение на ответственном слое и синхронизируй только затронутые актуальные docs/sequence.

Проверь app.openapi() exact schemas, extra forbid и response variants; production /docs,/redoc,/openapi.json дают 404, local/test flag включает schema. Подготовь локальный HTTPS proxy config/runbook с одним web process, raw peer без server proxy rewrite, internal-only health и внешним supervisor условием. Production ACL/manifest не реализуй в M1-6.

Запусти по порядку целевые tests/http_api, связанные application/session/catalog tests и tests/test_module_boundaries.py, затем полный pytest. Проверки документов: ссылки, JSON-примеры, баланс PlantUML blocks и git diff --check; рендер PlantUML заявляй только если реально запущен. Не запускай платные/сетевые smoke tests.

## Приёмка

AS-HTTP-01…29 имеют исполняемое coverage и positive controls; все обязательные команды и реальные итоги записаны в план/журнал. Назови оставшиеся ограничения, включая внешний supervisor и formal Tester review. Обнови статус только фактически выполненных промтов; не создавай commit, push или PR без отдельного указания.
