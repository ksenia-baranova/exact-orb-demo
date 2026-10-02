# Промт 13a. Поправки после независимого ревью реализации 12–13

**Статус:** исполнен 2026-10-02; результаты — §25 implementation plan.
**Зависимость:** промты 12–13,
коммит `7de962a`. **Источник:** замечания ревью другой моделью, сверенные
Developer с текущим кодом и контрактом 2026-10-02. Принятые и частично
принятые замечания записаны в §24
[implementation plan](../../../docs/project_management/implementation_plans/http_api_and_session_middleware_implementation_plan.md).

## Цель и границы

Закрыть подтверждённые расхождения shutdown, локального журнала и гонки
watchdog, восстановить зелёный полный pytest. Для частично принятых замечаний
сначала проверить конкретный сценарий и решить, нужен ли код, уточнение
контракта либо запись ограничения. Действуют `http_api.md` §4.1, §9.3,
§11.1–11.4, §12, DP-HTTP-04, change plan и тесты. При конфликте с ними не
изобретай новое публичное правило: подготовь конкретное решение для
Analysis/Lead и продолжай независимые исправления. Старые файлы `prompts/**`
не редактируй. Не расширяй M1-6 до production ACL/manifest, отдельного
worker process или автоматического `os._exit`.

## Подтверждённые исправления

1. **Shutdown после grace.** В `http_api.app` выполни шаги 5–7 §11.3:
   отмена ещё отменяемых request/owner tasks после grace, учёт их terminal
   outcome и повторная оценка active owners/retained futures до закрытия
   ресурсов. Если после отмены достигнута нулевая активность, закрой runtime,
   затем каталог/executor. Если protected/native работа либо submitted future
   остаётся без terminal outcome, сохрани ownership и ресурсы и перейди в
   fail-fast. Не закрывай занятый executor и не называй освобождённым permit,
   пока жив его leaf. Уточни в актуальных sequence diagrams лишь фактически
   изменившиеся переходы. Напиши два управляемых теста: (a) работа отменяется
   на grace и даёт обычный `aclose()` в правильном порядке; (b) зависший
   leaf/commit переживает отмену и остаётся открытым до внешней остановки.
   Используй fake scheduler/Event/barrier без `sleep`; проверь сохранение
   корреляции и отсутствие двойного terminal log. **Решение для M1-6:**
   после grace нет дополнительного срока. Отмени задачи и дай уже готовым
   отменам отработать через конечный checkpoint event loop, не ожидая
   `runtime.drain()` сверх grace. `aclose()` после grace допустим только если
   все owners и retained futures стали terminal на этом checkpoint;
   build owner, ожидающий живой resolver leader, приводит к fail-fast.
   Тест (a) должен использовать действительно мгновенно отменяемую работу,
   а тест (b) — живой retained leaf. Не вводи новый таймер или скрытое
   бесконечное ожидание и не обещай освобождения permit до terminal outcome.

2. **Завершение fail-fast process.** Зафиксируй в требованиях к внешнему
   supervisor и в локальном runbook, что обычный выход Uvicorn с retained
   task/executor не гарантирует завершение в конечное время. После истечения
   grace и сохранения диагностики supervisor должен принудительно завершить
   старый PID и только затем запустить один новый web process. В runbook
   опиши эту процедуру для любого `outcome=fail_fast`, включая обычную
   остановку с живой native работой, а не только 504. Сам HTTP process не
   вызывает `os._exit`; локальный пример остаётся ручным, production
   supervisor/ACL/manifest относятся к M1-12. Не обещай, что `pop_all()` сам
   завершает OS process.

3. **Реальный локальный журнал.** Настрой logging при запуске
   `exact_orb.http_server:create_local_app` с уровнем **INFO для всего
   `exact_orb`**, а не только `exact_orb.http_api`, так, чтобы INFO
   `exact_orb.http_api` и WARNING/ERROR надёжно попадали в названный
   диагностический файл. Используй существующий logging subsystem либо
   минимальную явную конфигурацию без дублирующего logging-сервиса; сохрани
   уже утверждённые уровни §12, включая INFO для
   `http_shutdown_finished`. Не включай DEBUG для component logging: на этом
   уровне он пишет полные входы/выходы, включая данные рождения. Укажи path,
   ротацию/закрытие handler и способ
   сохранить журнал перед принудительным завершением в runbook. Проверь
   изолированным локальным запуском logging configuration без сетевого smoke:
   `http_request_started`, `http_message`, `http_request_finished` и
   `http_shutdown_finished outcome=fail_fast` видны на INFO; ни в одном
   INFO-событии `exact_orb` нет DEBUG-payload; cookie, session ID, IP,
   query/body, birth data и ChartDTO в компактные HTTP-события не попадают.
   Не утверждай, что Caddy/HTTPS запущены, если их нет.

4. **Гонка watchdog и owner.** Детерминированным тестом воспроизведи оба
   порядка: owner завершился до deadline; watchdog уже перевёл процесс в
   unhealthy, затем owner завершился до обработки waiter. Во втором случае
   ответ — **`504 BUILD_TIMEOUT`, `Retry-After: 5`, без `Set-Cookie`**,
   даже если owner успел завершиться; итог клиент сверяет через current
   после перезапуска. Соблюдай §9.3 и один terminal response. Не меняй
   семантику точной ничьей без явной фиксации её в контракте.

5. **Изоляция logging-тестов и gate.** Воспроизведи пару
   `test_cli_writes_general_and_debug_logs` →
   `test_tzdata_version_mismatch_warns_once_and_allows_open`. Устрани
   оставленное CLI-тестом глобальное состояние `exact_orb` logger на
   ответственном тестовом шве; не ослабляй проверку warning каталога и не
   меняй production logging ради порядка pytest. Закрепи восстановление
   handlers/level/propagate регрессионной проверкой, затем добейся зелёного
   полного `pytest` либо оформи явное решение владельца change об исключении
   до передачи «Разработка → тестирование». Историческое 2931 passed,
   1 failed не выдавай за пройденный gate.

## Частично принятые замечания: проверка перед изменением

- **Non-build зависание.** Подтверди управляемым зависшим SQLite load и
  catalog search, что bootstrap/current/places не имеют deadline и health
  остаётся 200. Представь Analysis/Lead конкретный выбор: scheduler-based
  deadline с сохранением ownership submitted futures и правилом unhealthy
  либо явно принятое M1-6 ограничение. До решения не добавляй произвольный
  timeout. Отдельно объясни `sqlite_max_workers=1`; не повышай число workers
  как замену исправления зависания.
- **Disconnect и `uncancel()`.** Проверь, существует ли в текущей задаче
  воспроизводимый сбой следующего await/`asyncio.timeout`/`TaskGroup` после
  перевода `CancelledError` в `ClientDisconnected`. Если сценарий есть,
  исправь его на уровне task ownership и закрепи тестом; без сценария
  оставь счётчик и разные listeners GET/bootstrap и build без рефакторинга.
- **Bootstrap create после disconnect.** Доказательно опиши возможную
  persisted запись без доставленной cookie и потраченную quota; сверь с
  §9.3 и reaper. При необходимости добавь короткое ограничение в актуальные
  requirements/runbook и недостающий тест с реальной SQLite. Не откатывай
  успешно сохранённую сессию и не возвращай quota задним числом.
- **Unhealthy response.** Code `SERVICE_SHUTTING_DOWN` и
  `Retry-After: 30` уже установлены §4.4/§8; явно уточни их применение к
  состоянию unhealthy после watchdog и проверь существующие response tests.
  Значения без нового решения не меняй.
- **404/405 и lifecycle events.** Сверь §4.1 (route resolution до pipeline)
  с фразой §12 «terminal event ровно один». Зафиксируй с Analysis/Lead,
  охватывает ли §12 unmatched routes, health и локальный schema route или
  только совпавшие business routes. Лишь после решения добавляй события и
  тесты, сохраняя `X-Request-ID`, JSON ErrorDTO и отсутствие session touch.
- **OpenAPI и boundary.** Добавь компактную контрактную проверку общих
  accepted/rejected build inputs для `BuildNatalRequestDTO` и
  `RequestBoundary`, включая дату, `birth_time=null`, длину `place_id` и
  лишнее поле. Если JSON Schema не может выразить календарную валидность,
  явно отдели schema-level формат от runtime validation; не объявляй
  ложного полного совпадения.
- **Локальный proxy и версии.** Сохрани loopback CIDR как ограничение
  локального стенда; зафиксируй для M1-12 зависимость от ACL и настраиваемого
  trusted proxy, не создавая production manifest в этом промте. Уточни,
  что в `pyproject.toml` уже есть верхние границы `<1`/`<0.29`, но нет
  lock-файла; запиши выбранные для локального воспроизведения версии и
  отдельный вопрос о lock/pin для deployment. Не меняй зависимости
  автоматически.

## Проверка и отчёт

Сначала ищи существующее покрытие, не добавляй дублирующие тесты. Запусти
целевые shutdown/watchdog/logging/OpenAPI тесты, затем `tests/http_api`,
связанные application/session/catalog и `tests/test_module_boundaries.py`,
потом полный `python -m pytest -q`. Проверь `git diff --check`, актуальные
ссылки, JSON-примеры и баланс PlantUML blocks; рендер заявляй только после
реального запуска. Сетевые и платные smoke-тесты не запускай без отдельного
указания. В implementation plan запиши команды и фактические результаты,
раздели исправленные дефекты, принятые ограничения и вопросы Analysis/Lead.
Формальный Tester review ранее отменён пользователем; не восстанавливай его
как обязательный gate. Не создавай commit, push или PR без отдельного запроса.
