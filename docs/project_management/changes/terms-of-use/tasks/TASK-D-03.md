---
id: TASK-D-03
change: terms-of-use
role: developer
kind: implement
gate: IN_DEVELOPMENT
cycle: 1
inputs: [plans/prompts/02-terms-lifecycle.md, plans/implementation_plan.md]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: ':/terms-of-use.*TASK-D-03.*fix'
estimate: {human_hours: 5, agent_hours: 2, confidence: medium}
---
## Задание
Выполнить только [промт 02](../plans/prompts/02-terms-lifecycle.md): сохранить ввод и фокус при чтении условий, корректно начать новую загрузку формы.

Основа — результат [TASK-D-02](TASK-D-02.md), коммит `d8cef05f58e39a3d9db06276448cefeeae39d564`.

Готово, когда:

- Поздний current не затирает текущий ввод, включая полностью пустую форму. Обычное восстановление без открытия условий работает как раньше.
- Ответы build и recovery обновляют фактическую карту, сохраняя страницу условий и видимый фокус. Оба возврата сохраняют ввод и раскрывают редактор; лишнего POST нет.
- Новая инициализация формы показывает снятый checkbox после обоих способов отметки, с восстановленной картой и без неё.
- Повторный возврат и dispose не оставляют активных обработчиков; действующие правила отправки и recovery сохранены.

Менять только main.mjs и необходимые тесты/фикстуры. Проверять через реальные компоненты с управляемыми ответами, без sleep. Требования, API и статус изменения не менять. Промт 03 не выполнять.

Выполнить упрощение и проверки из промта: целевые → связанные → полный pytest. В результате кратко указать изменения, команды, результаты и ограничения; NOT RUN не считать PASS. Сделать один коммит своих файлов и указать его SHA. Push и оркестратор не запускать.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

Выполнен только промт 02, подход тест → код. Исходные ветка change/terms-of-use
и HEAD d8cef05f58e39a3d9db06276448cefeeae39d564 совпали с базой TASK-D-02.
Оценка реализации и Developer-проверок: 5 чч / 2 мч, confidence medium;
независимое ревью отдельно 0.7 чч / 0.2 мч. Это прогноз, не хронометраж.

Причина: guard первичного заполнения защищал только изменённый ввод, поэтому
открытый для чтения полностью пустой draft считался доступным для hydration.
Продолжение submit после field error также фокусировало скрытый control формы.

Изменения:
- main.mjs: единый draftProtected защищает изменённый ввод и открытый для условий
  черновик, включая пустой, и после возврата. Без открытия условий hydration сохранён.
- renderPage объединяет видимость страниц и data-page-mode; renderSession/fallback
  используют его. Фокус в скрытой форме не устанавливается во время чтения условий.
  Оба возврата раскрывают редактор и возвращают focus на ссылку.
- Реальные ответы, actual chart/summary, acceptance seq/reset/collapse и recovery
  продолжают обрабатываться штатно. Принятая цель не сворачивает редактор повторно
  после возврата; переходы/повторные возвраты не создают POST.
- terms.test.mjs: добавлено 27 тестов с реальными mount/form/places/coordinator/
  transport/result, управляемой листовой сетью, deferred и fake clock. Охвачены
  current до/после обоих возвратов, пустой/неполный draft, committed/422/already_applied/
  lost response, Retry-After/safe read и ошибка отображения, сохранение выбора и трёх
  раскрытий старой карты, dispose и новый mount после обоих способов отметки.
- DOM-port читает data-* из setAttribute, чтобы проверять фактический data-page-mode.
  Инициализация unchecked уже корректна; закреплена тестами с картой/без неё и
  исходно отмеченным DOM-control. Form/session/facts и API не изменялись.

### Фактические проверки

Все команды — от корня указанной рабочей копии. Использован системный Python 3.14
с установленными зависимостями. Локальная .venv не содержит fastapi/setuptools;
в ней pytest не запускался. Зависимости не устанавливались и не менялись.

| Команда | Фактический результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs` до production-правок | Baseline 26 PASS; после добавления regression и исправления DOM-port — 44 PASS, 6 FAIL: четыре случая перезаписи пустого draft, два случая скрытого focus |
| `node --test tests/ui/terms.test.mjs` итог | 53 PASS, 0 FAIL, 0 SKIP |
| `node --test tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/accepted_chart.test.mjs tests/ui/aspect_view.test.mjs` | 124 PASS, 0 FAIL, 0 SKIP; в том числе штатный focus field issue вне условий |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS за 34.33 с, включая installed wheel |
| `python -m pytest` | 2960 PASS, 1 SKIPPED за 247.70 с; tests/test_configurations.py:473, DEBT-CALC-001 |
| `git diff --check` | PASS |

SKIPPED и NOT RUN не считаются PASS. Новые тесты не используют sleep и реальное
ожидание для доказательства порядка. G1 дополняется фактом исходного POST; G2/G3/G4,
оба способа отметки и ровно три поля intent проверяются настоящим coordinator.
R1/R2/R3 принимают реальные управляемые ответы; recovery не подменяется UI-заглушкой.

### Упрощение и сложность

Diff перечитан: applyPageMode объединён с renderPage, повторный вызов рендера при
возврате убран; единый draftProtected использован вместо второго флага для перехода.
Guard фокуса добавлен в существующие точки передачи, новый механизм управления
фокусом не введён. Очередей, таймеров, storage, логов и отмены серверной работы нет.
Новых production-функций нет; большой mountBirthForm и существующий renderSession
оставлены в текущей структуре композиции, соседние renderer/session не перестраивались.
Radon не установлен (importlib.util.find_spec('radon') → None). Численные CC до/после
NOT RUN; Python radon неприменим к JS, production Python не изменён. Shortcut-ов нет.

Поле commit использует принятую в TASK-D-02 устойчивую Git revision уникального
сообщения: `git rev-parse ':/terms-of-use.*TASK-D-03.*fix'`. Она разрешается в SHA
единственного коммита этой задачи; полный SHA приведён в итоговом сообщении.
Это позволяет включить результат задачи в один коммит без amend/самоссылки SHA.

## Findings

Новых DP и багов вне промта нет. Независимая приёмка Tester/Reviewer не выполнялась.
Requirements, планы/промты, API, чужие задачи, change.md и events.jsonl сохранены.
До работы уже были посторонние tracked/untracked изменения; они не включены в коммит.
SHA-256 всех 3740 отслеживаемых файлов вне main/tests/DOM-fixture/этой задачи совпал
с исходным снимком. Статус изменения не менялся; push и оркестратор не запускались.

## Риски

DOM-port подтверждает значения, hidden-предков активного элемента, переходы и HTTP
вызовы, но не браузерный focus-visible, computed layout или настоящий reload.
Промт 03, reload/закрытие-повторное открытие, полная клавиатурная доступность,
computed font, 360 px и effective Q44 — NOT RUN, не PASS. Эти проверки остаются
следующей отдельной implement-задаче. DEBT-UI-001 и публичная готовность не закрыты.

Следующий шаг: остановка после единственного коммита TASK-D-03; промт 03 — отдельно
по процессу v3, без запуска оркестратора в этой задаче.
