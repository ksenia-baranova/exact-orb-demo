---
id: TASK-D-04
change: terms-of-use
role: developer
kind: implement
gate: IN_DEVELOPMENT
cycle: 1
inputs: [plans/prompts/03-terms-accessibility.md, plans/implementation_plan.md]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: ":/terms-of-use.*TASK-D-04.*test"
estimate: {implementation: "4 чч / 1.5 мч", code_review: "0.5 чч / 0.2 мч", confidence: medium}
---
## Задание
Выполнить [промт 03](../plans/prompts/03-terms-accessibility.md): проверить доступность страницы условий в настоящем браузере и исправить найденные дефекты.

Основа — [TASK-D-03](TASK-D-03.md), коммит `58aa6b956ccbb9bec9948340e955dc4ba133ce25`.

Проверить:

- Клавиатуру, видимый фокус, совпадение шрифта ссылки с пояснением неизвестного времени; чтение без горизонтальной прокрутки на desktop и 360 px.
- Эффективные области ссылки и обеих кнопок ≥44 × 44 CSS px: доверенный указатель, фактический получатель нажатия, положительный контроль и отрицательные контроли уменьшения, перекрытия и обрезания. Одного bounding box недостаточно.
- Оба возврата сохраняют ввод без нового POST; отдельное построение работает. Reload и закрытие/повторное открытие снимают отметку после обоих способов выбора, с картой и без неё.
- Текст C1…C8 совпадает с утверждённой редакцией из TASK-O-02; ссылка открывает полный исходный код используемой версии. Если версия не опубликована, отметить C7 как NOT RUN; push не выполнять.

Сохранить команды, браузер, размеры экрана, SHA поставки/исходников, снимки и результаты контролей в [plans/evidence/](../plans/evidence/). При необходимости создать этот каталог. Исправления ограничить страницей и её связью с формой; каждый дефект закрепить тестом.

Выполнить упрощение и проверки из промта: целевые → связанные → полный pytest. Требования, API и статус изменения не менять. В результате кратко указать выполненные проверки и ограничения; NOT RUN не считать PASS. Сделать один коммит своих файлов и указать SHA. Оркестратор и push не запускать.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

Выполнен только промт 03 в роли Developer, процесс v3. Ветка change/terms-of-use,
delivery/source baseline `58aa6b956ccbb9bec9948340e955dc4ba133ce25`.
Подход: существующие `terms.test.mjs`/delivery тесты плюс настоящая браузерная
проверка наблюдаемого результата. Дефектов страницы и связи с формой не обнаружено;
production HTML/CSS/JS и тесты не изменены. Утверждённые требования и API сохранены.

Оценка реализации с Developer-проверками: 4 чч / 1.5 мч, confidence medium;
независимое ревью отдельно 0.5 чч / 0.2 мч. Это прогноз, не хронометраж.

### Браузер и доказательства

Настоящий ChatGPT in-app browser / Chromium 156.0.0.0 на Windows, desktop 1280×900
и 360×740 CSS px; финальный desktop snapshot 1280×740. Реальные package assets,
настоящие mount/form/session/transport; HTTP leaf заменён существующими golden.
Команды, минимальный harness, все snapshots, raw результаты и ограничения —
[plans/evidence/README.md](../plans/evidence/README.md).

- Tab/Enter, видимый heading/link/button focus и оба возврата — PASS; скрытые
  контролы не попадают в порядок Tab. Computed family/size/weight совпадают:
  system-ui, sans-serif / 13px / 400. Начало и конец текста без горизонтального
  overflow на desktop и 360 px; таблица и действия доступны.
- 6 сочетаний target/viewport: Q44 hit-test сеткой 1936 точек, 54 trusted pointer
  clicks с фактическим event.target и переходом. Все PASS. Для всех трёх targets
  на двух viewport обнаружены 18 сочетаний уменьшения 43×43, overlay и clipping
  той же проверкой; trusted получатель совпал с elementFromPoint.
- 12 roundtrip случаев: known/unknown/incomplete draft × оба исходных checkbox
  × оба возврата. Date/place/time/unknown и фокус сохранены, новых POST нет после
  начального bootstrap. Ручной checkbox и открытие ссылки различают действия.
- Два отдельных валидных построения после manual/agree: по одному POST /charts/natal
  с birth_date/birth_time/place_id. API intent не расширен.
- Reload и настоящее close/reopen после manual/agree, с картой и без: 8 PASS,
  после каждого готового открытия отметка снята; восстановленная карта сохранена.
- Текст DOM браузера побайтно совпал с редакцией из утверждённого Git-пакета
  `02cbd17e33ceffe52d465bdf6b8faf1d3c76864c`, SHA-256
  `ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`.
  C1…C6/C8, exact_orb@mail.ru и отсутствие редакционных меток — PASS.

### Фактические проверки

Команды из корня указанной рабочей копии, системный Python 3.14.0 с уже
установленными зависимостями; .venv не содержит FastAPI. Ничего не устанавливалось.

| Команда | Реальный результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs` | 53 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api/test_ui_delivery.py -q` | 8 PASS за 7.53 с, включая installed wheel |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS за 26.86 с |
| `python -m pytest` | 2960 PASS, 1 SKIPPED за 132.15 с; DEBT-CALC-001, tests/test_configurations.py:473 |
| `node --check docs/project_management/changes/terms-of-use/plans/evidence/browser-probes.js` | PASS |
| `git diff --check`, `git diff --cached --check` | PASS |

SKIPPED/NOT RUN не считаются PASS. Полный pytest выполнен после целевых и связанных.
Платные/LLM smoke не запускались. Браузерный harness остановлен, вкладки закрыты,
viewport override сброшен.

### Упрощение, сложность и Git

CSS/handlers перечитаны: общий font rule, returnFromTerms и renderPage уже
реализуют простую композицию; новых изменений production не требуется.
Тесты публичного поведения не переписывались. Radon не установлен
(`importlib.util.find_spec('radon')` → None), CC до/после — NOT RUN;
production Python не изменён, Python radon неприменим к HTML/CSS/JS.
Новых shortcut и зависимостей нет. Изменены только эта задача и plans/evidence/.

Поле commit использует устойчивую Git revision по уникальному сообщению:
`git rev-parse ':/terms-of-use.*TASK-D-04.*test'`. После единственного коммита
она разрешается в его SHA; полный SHA дан в итоговом сообщении. Это сохраняет
один коммит без amend и самоссылки на ещё не созданный SHA.

## Findings

Новых production-дефектов и DP нет. C7 в части exact source delivery — **NOT RUN**:
публичный root repository открывается, main показывает
`9f36ee8c8d6b3105de0ed633c23abe7fdeac7fea`, но GitHub fetch_commit для поставки
`58aa6b956ccbb9bec9948340e955dc4ba133ce25` возвращает 422 No commit found for SHA.
Код точной используемой версии ещё не опубликован; разрешённое промтом ограничение
зафиксировано без push. Доступный root URL не объявлен соответствием поставке.

## Риски

Независимая test/code_review и приёмка, transfer, интеграция, публикация exact
source и DEBT-UI-001 остаются за следующими действиями процесса. C7 нужно
перепроверить после отдельной публикации. Проверялся browser UI с golden HTTP,
не live HTTPS/серверный расчёт. Сокращённый golden ChartDTO использует HTML fallback
колеса; полнота SVG не входит в эту проверку. Только Chromium, другие движки — NOT RUN.

Все 3744 ранее отслеживаемых файла сверены с исходными SHA-256 и сохранены,
включая чужие изменения change.md/events.jsonl. Посторонние untracked сохранены
и не включены в коммит. Требования, ADR, API, чужие задачи и статус изменения
не менялись. Оркестратор и push не запускались.

Следующий шаг: остановка после единственного коммита; дальнейший переход и
независимые test/code_review — отдельный запуск процесса.
