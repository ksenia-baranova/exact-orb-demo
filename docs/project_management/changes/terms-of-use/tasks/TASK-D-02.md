---
id: TASK-D-02
change: terms-of-use
role: developer
kind: implement
gate: READY_FOR_DEVELOPMENT
cycle: 1
inputs: [plans/prompts/01-terms-roundtrip.md, plans/implementation_plan.md]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: ':/terms-of-use.*TASK-D-02.*feat'
estimate: {human_hours: 6, agent_hours: 2, confidence: medium}
---
## Задание
Выполнить промт из inputs, включая шаг упрощения; target → related → full pytest; указать commit.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

Выполнен только промт 01. Подход: тест → код; до реализации 22 прежних теста PASS,
26 новых — ожидаемый FAIL на отсутствии перехода. После реализации исправлен
листовой DOM-port: getElementById должен находить и корневой main. Итоговые проверки ниже.

Основание решения: сохранить живые DOM и form/places/session/result вместо сериализации
черновика. Статическая секция условий соседствует с birth-page; ссылка вне label,
обе кнопки type=button вне form. «Согласен» использует form.acknowledge(true),
«Вернуться к форме» сохраняет отметку; оба раскрывают редактор и фокусируют ссылку.
Переходы не создают бизнес-запросов; ручная отметка и API intent из трёх полей сохранены.
Новые listeners снимаются в dispose; повторный возврат после закрытия — no-op.

Текст взят только из публикуемого раздела terms_draft.md, утверждённого TASK-O-02
(пакет 02cbd17e33ceffe52d465bdf6b8faf1d3c76864c). Восстановление Markdown из фактического
HTML, включая заголовки, таблицу и ссылки, даёт SHA-256 UTF-8/LF с одним конечным LF:
`ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`.
Служебные разделы Analyst не опубликованы. Installed-wheel probe сравнивает страницу
с точным digest проверенного index.html; действующие MIME/cache/no-business-events проверки сохранены.

Изменены index.html, main.mjs, styles.css; добавлены 26 mounted UI-тестов в
terms.test.mjs, расширены fixtures/dom.mjs и test_ui_delivery.py; заполнена эта задача.
Production Python, form/session/facts, HTTP DTO, требования и чужие задачи не менялись.
Исходная ветка change/terms-of-use, HEAD fb1216591b0fd98589084155177f1bd4e41d159d.
Оценка: реализация и Developer-проверки 6 чч / 2 мч, confidence medium;
независимое ревью отдельно 0.7 чч / 0.2 мч. Это оценка, не фактический хронометраж.

### Фактические проверки

Команды выполнялись от корня указанной рабочей копии. Использован системный
Python 3.14 с уже установленными зависимостями; локальная .venv не содержит fastapi
и setuptools. Установка зависимостей и изменение dependency-файлов не требовались.

| Проверка | Результат |
| --- | --- |
| `node --test tests/ui/terms.test.mjs tests/ui/form.test.mjs` | 48 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api/test_ui_delivery.py -q` | 8 PASS, включая installed wheel |
| `node --test tests/ui/*.test.mjs` | 255 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS за 66.21 с |
| `python -m pytest` | 2960 PASS, 1 SKIPPED за 130.91 с; DEBT-CALC-001, tests/test_configurations.py:473 |
| Браузерный smoke | PASS в ChatGPT in-app browser: реальная ссылка, текст до конца и обе кнопки, focus, сохранение 2000-02-29 / «Тест» / 12:6; back сохраняет false и true, agree выбирает true; 0 POST /charts/natal |
| `git diff --check` | PASS |

Полный pytest завершён после связанных проверок; ранее запущенная попытка остановлена
до выполнения тестов, её результат не засчитывался. SKIPPED не считается PASS.
Node regression-покрытие использует настоящий mountBirthForm/form/coordinator/transport
и листовой fetch harness: T1…T4, D1 00:00/12:00/23:59, D2 пусто/12:00 с неизвестностью,
D3 пусто/12:6/место без ID/изменённый draft при карте — каждый с обоими возвратами.
Нулевой build дополняется позитивным контролем явного submit после ручной отметки
и после «Согласен»: ровно один POST с birth_date/birth_time/place_id.

Smoke: временный локальный leaf HTTP-harness на http://127.0.0.1:8872 доставлял те же
production UI-файлы; bootstrap/current заменены golden-ответами. Это проверка UI в
браузере, не live-проверка серверного окружения. DOM и screenshots осмотрены; журнал
harness зафиксировал отсутствие /charts/natal. Вкладка закрыта, harness остановлен.

### Упрощение и сложность

Diff перечитан: оба возврата сведены в returnFromTerms с таблицей TERMS_RETURN_ACTIONS,
видимость — в renderPage, стили шрифта ссылки и пояснения общие. Snapshot/storage,
второе состояние checkbox и новый JS-модуль не добавлялись. Новые обработчики короткие;
существующий большой mountBirthForm оставлен композицией без перестройки соседей.
Radon не установлен (importlib.util.find_spec('radon') → None); численные CC до/после
NOT RUN. Production Python не изменён, Python radon неприменим к изменённому UI JS.
Shortcut-ов нет.

Поле commit содержит устойчивую Git revision по уникальному сообщению этого коммита:
`git rev-parse ':/terms-of-use.*TASK-D-02.*feat'`.
Она разрешается в SHA единственного коммита после его создания; сам SHA указан в
итоговом отчёте. Это позволяет включить результат задачи в тот же коммит без amend.

## Findings

Новых DP и багов вне согласованного объёма не заведено. Текущий прогон не является
независимой приёмкой Tester/Reviewer. Публикация и связь полного кода точной версии
с поставкой (C7) в этой задаче не проверялись; push запрещён поручением.

## Риски

Промты 02 и 03 — NOT RUN: отдельные проверки позднего current/build/recovery,
reload, полной клавиатурной доступности, computed font, 360 px и эффективных Q44
с отрицательными контролями не выполнены и не объявляются PASS.
DEBT-UI-001 не закрыт. Независимая приёмка, transfer, интеграция и публичный запуск
остаются за следующими задачами. Requirements, TASK-O-02, change.md и events.jsonl
сверены по исходным SHA-256 и сохранены; посторонние изменения не включаются в коммит.
Оркестратор и push не запускались.

Следующий шаг: остановка после единственного коммита; промт 02 — отдельная задача процесса.
