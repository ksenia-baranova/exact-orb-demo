# DEV-WHEEL-04 — сводка / редактор и причины принятия результата

После build/current пользователь получает колесо и сводку actual карты; редактор остаётся доступным и сохраняет поздний draft. Результат будущего шага — новый presentation с прежними ручным gate / recovery / late-response guarantees.

**Редакция 2 / TASK-D-002, 2026-10-16:** неисполненная версия v1 сохранена @ `04be207627de1049deac2e069574e01b62536607`. **InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`, `dev/ui-chart-wheel`, worktree в [индексе](../../developer_artifact.md). [DEV-WHEEL-04](../implementation_plan.md#dev-wheel-04-сводка-редактор-и-recovery-в-новом-представлении).
**Контракт:** исходные UI / AS-UI / HTTP / ADR @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1` и [Analyst requirements](../../analyst/requirements.md)/[scenarios](../../analyst/scenarios.md) v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, ссылки в плане. REQ-WHEEL-01/08/09/11, REQ-UI-01/03/08/09/10/11; AS-WHEEL-01/02/12/14…22/24/30 и MODIFY AS-UI-22. DP-O-001…003/010/013 @ Manager/InputSHA, ADR-0034/0040/0041 и reviewed drawing rules.

## Вход / scope

DEV-WHEEL-02/03 завершены на назначенных версиях, approved входы / blockers и G3 разрешают срез. Проверить Git, current Manager и точные approved SHA, зафиксировать в плане. TASK-D-002 и сохранение этого промта реализацию не назначают.

Будущие файлы: main/facts/index/styles, mounted session/recovery/facts tests и delivery resources. Recovery алгоритм сохраняется. Если существующий acceptance seam недостаточен, сначала доказать конкретный root cause / отсутствующую информацию и согласовать узкую правку session/recovery с Manager; обычное подключение колеса не требует перепроектирования coordinator. Не добавлять API fields, services, dependencies, M1-8.1 / M1-9 / chat, не менять golden.

**Подход:** соединение существующих компонентов → mounted tests, реальные form / coordinator / transport / result; fake network/clock и текущие fixtures. Existing session/recovery coverage дополняется assertions нового UI. Исправленный defect требует deterministic regression; не тестировать повторно leaf fake вместо реального пути.

1. Вынести доступные status / submitted intent / recovery / safe-read controls из сворачиваемых полей. Изображение может отказать локально, HTML и actual summary сохраняются; не подавлять видимый исход и не прятать действия whole-form hidden.
2. Summary committed — существующий immutable submitted snapshot + подтверждённое имя места; summary current — birth того же GET. Текущий draft не заменяет их; POST не дополнять вымышленным BirthViewDTO или лишним GET ради summary.
3. Collapse после successful build только при совпадении текущих birth fields со snapshot; отличающийся поздний draft открыт. Initial ready без dirty draft сворачивается; повторный automatic current даже другой identity не уничтожает и не скрывает открытый изменённый draft. Reload сбрасывает ручную отметку.
4. Отличать own changed-birth acceptance от automatic current, включая recovery через GET. Не считать любой GET причиной preserve либо любую новую identity причиной reset. Reset выполняется один раз на подтверждённый новый результат своего изменённого intent; repeated publish / unrelated foreground / failed read не повторяют reset. Использовать проверяемые existing snapshot / request_id / source / recovery relations без TTL / задержек.
5. Проверить mounted branches и собрать handoff. До G4 Manager назначает актуальный MainBaseline / CandidateSHA и проверки; InputSHA этой консультации не становится автоматически кандидатом реализации.

| REQ / AS | Действие / данные | Expected result / позитивный контроль |
|---|---|---|
| REQ-UI-01/11 / AS-WHEEL-01/02 | Committed A / F5 current A, без позднего draft | SVG/HTML/summary A сразу, initial 5/5 и collapsed editor; current не считает карту; ручной gate после reload снят |
| REQ-UI-03/11 / AS-WHEEL-01/18/21 | Submit B, во время запроса draft C; парный контроль C=B | Summary B; C≠B остаётся открытым, C=B сворачивается, без автоподстановки gate |
| REQ-WHEEL-08 / AS-WHEEL-14/19…22/30 | Новый own changed-birth результат через committed и recovery GET; unrelated foreground отдельно | Own acceptance reset к 5/5 один раз; automatic current сохраняет существующий key / expansion и читает новые факты; failed / old current не выдаётся за own success |
| REQ-UI-08/09 / AS-WHEEL-15/17/19 | Empty/unavailable, lost POST / failed read | Подтверждённые no-chart исходы убирают numeric/SVG; failed read сохраняет actual карту и selection, feedback / safe recheck доступны, auto POST нет |
| REQ-UI-09 / AS-WHEEL-20 | STATE_COMMIT_FAILED / BUILD_TIMEOUT | Действующие Retry-After / explicit restart gates, controls доступны при collapse; fakeClock/events, без sleep |
| REQ-UI-09/11 / AS-WHEEL-21/22 | Late current другой вкладки, draft, late first commit / dispose | Сводка/HTML/SVG actual ответа, draft открыт; первый commit не назван вторым intent, после dispose DOM не меняется |
| REQ-WHEEL-09/10 / AS-WHEEL-16/23 и AS-UI-22 | 1440/768/360, keyboard / reveal / resize | Desktop справа от summary, mobile ниже, нет page overflow; controls/focus доступны, все points / отдельные angles, независимые tables |
| ADR-0034 / baseline AS-UI-20/21 | Выбор/resize/reveal/local failure; явный валидный submit | Нет HTTP build от локальных действий; позитивный control даёт один ручной POST |

**Observability:** HTTP bootstrap/current/build и существующие request_id/run_id + локальный ordered evidence acceptance reason / intent / identity → оба представления → visible result/failure. Серверный terminal не доказывает render; новой telemetry нет.

**Команды поэтапно:** `node --test tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/facts.test.mjs`; `node --test tests/ui/*.test.mjs`; `python -m pytest tests/http_api/test_ui_delivery.py tests/http_api/test_projectors.py tests/test_module_boundaries.py`; `python -m pytest` на назначенном CandidateSHA до G4. Доступность Node / skips фиксировать реально; browser evidence отдельно, paid/network smoke не запускать.

**Завершение:** exact SHA/состояние дерева/команды/results/непроверенное в checks и корневом handoff, границы переносимых technical sequences после Owner acceptance. Независимый Tester, review Manager / G4 / acceptance и Git-поставка остаются отдельными действиями. Неясный новый expected result передать Analyst, не закреплять тестом по удобству текущего кода.
