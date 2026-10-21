# TASK-D-007 — первые пять планет в таблице

Codex / Developer,20.10.2026. InputSHA `0da99518ada67603b08ab4220d337e3a5e3aae60`,dev/ui-chart-wheel. [Owner-дельта](../../owner_decision_points_disclosure_2026-10-20.md), [план§12](../../full_wheel_implementation_plan.md#owner-points-disclosure), [пакет09](../../prompts/09-owner-points-disclosure.md), [manifest](manifest.json).

Причина прежнего поведения — исходное нормативное all-points правило: chart_state не имел pointsExpanded, facts не ограничивал points и не создавал кнопку. Owner явно меняет только обычную HTML-таблицу: первые5 в каноническом порядке,собственная «Показать все» / «Показать первые 5». Все source rows сохранены в retained DOM. SVG по-прежнему показывает все опубликованные точки;данные/API/engine/golden не менялись.

Состояние раскрытия независимо от houses/aspects;automatic current сохраняет его,существующий accepted-birth reset сбрасывает однократно. Aspect-only view показывает все опубликованные endpoints вне лимита пяти,кнопка скрыта;close возвращает прежнее раскрытие. Native aria/keyboard/focus,удаление/скрытие строки и dispose проверены.

## Команды и actual

Рабочая папка: `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered`. Node — bundled `C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`,Python — `C:/Users/KateUser/AppData/Local/Programs/Python/Python314/python.exe`.

| Команда | Actual |
|---|---|
|`node --test tests/ui/chart_selection.test.mjs tests/ui/aspect_view.test.mjs`|[RED](red.log):13pass/4fail до production fix;GREEN17/17 после. Две новые regression и намеренно обновлённые прежние ожидания по Owner |
|PowerShell:`$nodeTests = @(rg --files tests/ui -g '*.test.mjs'); & node --test --test-reporter=dot @nodeTests`|229/229 passed,exit0 |
|`python -m pytest tests/http_api/test_ui_delivery.py tests/test_module_boundaries.py -q`|53passed,18.06s |
|`python -m pytest -q`|[2959passed,1existing skip DEBT-CALC-001,222.68s](pytest.log) |
|`node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_points_disclosure/browser.cjs run02`|[4/4cases,68/68checks](run02/actual.json):real Chrome155/Yandex26.8,1440/360px;Enter/Space,5/16 rows,independence,late endpoint/no-focus,aspect bypass/close,automatic update preserve,no extra HTTP from interactions,full SVG16 |
|`git diff --check`|exit0,только предупреждения LF→CRLF |

Browser HTTP leaf контролируемый,данные из опубликованных public fixtures;app/main/session/facts/controller/SVG настоящие. run01 сохранён:4cases проверяли поведение успешно до последнего ошибочного ожидаемого счётчика запроса;online штатно делает bootstrap+current,а harness ожидал один current. Исправлен только expected-positive-control,run02GREEN. Это не product failure и не изменение transport. 14source LF hashes закреплены в каждом actual;final consistency audit сравнивает их с текущими файлами.

[HTTPS delivery](live_delivery.json):оба изменённых модуля200 и совпадают с текущим диском,TLS проверен обычным способом. Production-сервис не перезапускался:static files читаются с диска. Новый реальный POST/build не выполнялся,пользовательская сессия/DB не менялись. Уже открытая страница получает новые модули после обновления.

## Scope и ограничения

Изменены только chart_state.mjs,facts.mjs,два существующих UI test файла,собственный plan§12/sequence006/Owner-решение/пакет09/evidence и Developer handoff. Локальная предыдущая регистрация DEV-FIND-WHEEL-009/DEBT-UI-002 сохранена без исправления/переноса статусов. Manager/Analyst/Tester документы и gates не переключались. Normative all-points текст не переписан чужой ролью;конкретная текущая Owner-дельта передана ответственным для последующей синхронизации.

Независимая acceptance,другие ОС/браузеры/assistive technology и реальный новый build не проверены. Существующий renderer/geometry не менялся;старые browser matrices не объявлены новыми прогонами. Sequence006 синхронизирован текстом,PlantUML PNG render не запускался. Commit/push/нового CandidateSHA нет,index сохранён пустым.


Подготовка публикации: git diff --cached --check обнаружил два пробельных пустых ряда в Node RED stdout. [Исходные байты лога](red.raw.log.gz) сохранены в gzip без потерь,decoded SHA256 в manifest;в red.log удалены только завершающие пробелы для текстового просмотра. Test results/production source не менялись.
