# DEV-WHEEL-04 — встроить колесо, сводку и редактор с сохранением recovery

При построении и восстановлении пользователь получает колесо со сводкой; форма доступна по «Изменить данные». Результат — новый presentation при сохранении подтверждённой карты, локального ввода, ручного gate и доступных recovery controls.

**План:** [DEV-WHEEL-04](../implementation_plan.md#dev-wheel-04-сводка-редактор-и-recovery-в-новом-представлении), TASK-D-001 / consultation v1. `dev/ui-chart-wheel`, worktree в [индексе](../../developer_artifact.md), исходный HEAD `2b846077b317e33dd892565419942c4db8517b1e`.
**Контракт:** UI/AS-UI/HTTP/ADR @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1` и Analyst v1 @ `683bdd0c1f5a0e65735f4e48127d408300ec697c`, обе части со ссылками в плане. Применимы REQ-WHEEL-01/08/09/11, REQ-UI-01/03/08/09/10/11, AS-WHEEL-01/02/12/14…22/24, DP-O-001…003/010/013 @ Manager/InputSHA; ADR-0034/0040/0041 и технические drawing rules.

## Вход / границы

DEV-WHEEL-02/03 завершены на назначенных версиях, G3 разрешает срез; Analyst актуализировал collapse/focus/recovery expected results и Manager записал точный approved SHA. Проверить рабочее дерево и изменения с InputSHA, зафиксировать фактические версии в плане. Прежние результаты проверки не переносить на новый кандидат без основания.

Разрешены main.mjs/facts.mjs/index.html/styles.css, mounted assertions в session.test.mjs/recovery.test.mjs/facts.test.mjs и package delivery resources. Внутренний session/recovery алгоритм сохраняется; если требуется его менять, сначала доказать root cause и передать Manager оценку расширения. API, схемы/ошибки, engine/cache и новое сервисное состояние не входят. Не реализовывать M1-8.1 / чат / terms page. Сохранить чужую работу, commit/push/PR отдельно.

**Подход:** реализация соединения → mounted tests, используя реальные форму/coordinator/transport/result; fake network/clock и текущие fixtures. Existing session/recovery tests уже покрывают retry/late/coalescing; дополнять их проверкой колеса, сводки, editor и видимости controls. Если найден программный defect, сначала deterministic reproduction, затем regression; import error не считается RED.

1. Отделить сворачиваемые поля редактора от status/recovery/submitted intent и доступных действий. Не прятать всю форму, если это скрывает feedback или safe-read.
2. Сводку committed POST строить из существующего immutable submitted summary, current — из birth принятого ответа. Не брать её из текущего draft. Первичный ready без изменённого draft сворачивает редактор; прочие ветви по утверждённому Analyst, не молчаливой эвристике.
3. Раскрытие сохраняет заполненные значения и ручной checkbox; reload не восстанавливает отметку. Выбор/resize/reveal/render failure не вызывает POST. Wheel и HTML всегда одной принятой identity; отказ чтения не превращается в empty.
4. Проверить mounted branches и собрать Developer handoff. Manager синхронизирует main и назначает checks на CandidateSHA до G4; текущий InputSHA не объявлять кандидатом без этого назначения.

| REQ / AS | Данные / действие | Expected result / позитивный контроль |
|---|---|---|
| REQ-UI-01/11 / AS-WHEEL-01/02 | Committed A и current A | Wheel+HTML+summary A сразу; current не запускает расчёт; primary ready без dirty draft сворачивает редактор |
| REQ-UI-03/09/11 / AS-WHEEL-18/21 | Отправлен A, draft B; late current C / отказ B | Подтверждённая actual карта / сводка не равны произвольному draft; B не затёрт, не скрыт без принятого правила |
| REQ-UI-08/09 / AS-WHEEL-15/17/19 | Empty/unavailable, failed read, lost POST | Подтверждённые empty/unavailable удаляют wheel/numeric facts; failed read сохраняет прежние; безопасное чтение доступно; автоматического POST нет |
| REQ-UI-09 / AS-WHEEL-20 | STATE_COMMIT_FAILED / BUILD_TIMEOUT | Существующий Retry-After / explicit restart gate; controls доступны при collapse; fakeClock/events, без sleep |
| REQ-WHEEL-08/11 / AS-WHEEL-22 | Две вкладки / late first commit / dispose | Actual current не приписан второму intent; после dispose late accept не меняет DOM; серверная отмена не заявляется |
| REQ-WHEEL-09/10 / AS-WHEEL-16/23 | 1440/768/360, keyboard | Desktop wheel справа от сводки, mobile ниже; no page overflow; focus/error controls достижимы |
| ADR-0034 / baseline AS-UI-20/21 | Reveal/resize/selection и явный build | Нет POST от локальных действий; валидный ручной gate + submit даёт один POST |

**Наблюдаемость:** порядок существующих bootstrap/current/build и request_id/run_id не изменён; дополнить локальным evidence принятия карты и передачи в HTML/SVG. Серверный terminal event не доказывает render. Новый logger/telemetry не вводить.

**Команды поэтапно:** `node --test tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/facts.test.mjs`; `node --test tests/ui/*.test.mjs`; `python -m pytest tests/http_api/test_ui_delivery.py tests/http_api/test_projectors.py tests/test_module_boundaries.py`; затем `python -m pytest` на назначенном CandidateSHA. Полный pytest может включать Node через test_ui_delivery.py — записать фактическую доступность Node и skip. Не запускать платный/сетевой LLM smoke.

**Завершение:** в checks точные команды, SHA/состояние дерева, числа passed/skip/fail и browser evidence; в корневом handoff changed contracts/files, ограничения, DP/findings и source→target technical sequences для будущего переноса. Tester выполняет независимую проверку после G4; Owner acceptance и Git поставка отдельны. Без ясного editor/selection outcome вернуть Analyst, не подгонять тест под код.
