# Промт 12. Ownership, deadline и graceful shutdown

**Статус:** не начато. **Зависимость:** закрытый Gate A, release condition из S0 и промты 05, 10–11.
**План:** [M1-6 implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md), карточка 12.

## Что и зачем делаем

Ответ 504 и отключение клиента не останавливают уже начатую native или protected commit работу. Process-local capacity остаётся честной только если HTTP владеет этой работой до реального завершения либо до принудительной замены процесса.

## Задача

Расширь обычный owner task build из промта 11 до registry **всех принятых requests**: bootstrap, current, places и build. Только build удерживает capacity permit. Shutdown ждёт non-build owners и отправленные ими SQLite/catalog executor futures до закрытия runtime/catalog (§11.3); обычное terminal release build из 11 сохраняется.

Реализуй owner task/registry для каждого admitted build, независимый от send response, по правилу нижней границы release из §9.3/AS-HTTP-24 после S0. При disconnect до commit отмени execute, затем удерживай permit, пока не завершится работа, к которой запрос присоединился, включая shared single-flight leader. Для выбранного консервативного варианта используй доказанный в S0 snapshot всех активных resolver leaders; unrelated leader вправе задержать release. Один leader может обслуживать несколько запросов; каждый permit освобождается ровно один раз. `runtime.drain()` допустим как общий snapshot только после доказательства, что он захватывает нужного leader и не оставляет невидимой retained work. После начала protected commit дождись inner task по действующему Orchestrator contract. Отправленные в executor SQLite/catalog операции, переживающие отмену await, не должны стать невидимой работой перед close; если существующий leaf не удерживает future, исправь только этот seam с regression test. Не отменяй native thread с ложным утверждением, что он остановлен.

Через единый injected `now()/wait_until(deadline)` scheduler из G0 на 30 сек закрывай admission, выставляй live/ready 503 и отдавай 504 с Retry-After:5 и unchanged cookie, если соединение доступно. Не используй `asyncio.wait_for` как источник application deadline: fake scheduler должен разбудить watchdog без `sleep` или patch event loop. Permit в старом process не объявляй свободным, пока owner не терминален. Shutdown: stop admission → stop/wait reaper → wait всех принятых owners 30 сек → cancel допустимых pre-commit → wait protected work и surviving leaf futures; runtime.aclose и каталог закрывать только при нулевой активности, иначе fail-fast restart и внешний supervisor. Не пытайся синхронно закрыть executor под зависшим thread.

## Приёмка

AS-HTTP-19/22/24/26 и existing cancelled-waiter integration проходят с fake scheduler, Event/barrier: после cancel execute leader ещё жив, permit отменённого запроса занят; дополни до пяти занятых permits и проверь отказ шестому `503 BUILD_CAPACITY_EXHAUSTED`; два запроса с одним leader удерживают свои permit до завершения общего расчёта и освобождают каждый ровно по разу. Отдельный unrelated leader может задержать release отменённого запроса; тест проверяет нижнюю границу, а не точный момент. После завершения всех удерживаемых snapshot работ и фактического release следующий build допускается. Принятые bootstrap/current/places не обрываются закрытием SQLite/catalog; их surviving futures удерживают shutdown. При зависании unhealthy и fake supervisor restart поверх той же SQLite-базы; no commit до commit-stage cancel; confirmed protected commit виден после restart. Запиши точные команды, возможные внешние supervisor ограничения и evidence.
