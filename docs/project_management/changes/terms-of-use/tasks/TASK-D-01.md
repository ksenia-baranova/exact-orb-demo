---
id: TASK-D-01
change: terms-of-use
role: developer
kind: review
gate: ALIGNMENT
cycle: 1
inputs: [change.md, requirements.md]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: [REQ-UI-03, REQ-TERMS-01, REQ-TERMS-02, REQ-TERMS-03, REQ-TERMS-04, REQ-TERMS-05, REQ-TERMS-06, REQ-TERMS-07, REQ-TERMS-08]
commit: a362a9eb236cca59c01d3fcb885ca74faf57c448
estimate: { чч: 17, мч: 6, confidence: medium }
---
## Задание
Ревью требований; план и оценка в чч и мч; reviewed_reqs заполнен.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

TASK-D-01 выполнена как Developer / review: DONE / done. NEW → IN_PROGRESS → DONE; change.md остаётся ALIGNMENT / cycle 1. Рабочая копия `C:\Users\KateUser\PycharmProjects\exact-orb-recovered`, ветка `change/terms-of-use`. Поле commit содержит проверенный входной SHA требований и кода, а не SHA создаваемого коммита артефактов review. Последний сообщается после коммита и определяется командой `git log -1 --format=%H --fixed-strings --grep='[terms-of-use][TASK-D-01]'`.

Подготовлены [план со «Структурой кода»](../plans/implementation_plan.md) и три последовательных промта: [чтение и два возврата](../plans/prompts/01-terms-roundtrip.md), [жизненный цикл](../plans/prompts/02-terms-lifecycle.md), [доступность и содержание поставки](../plans/prompts/03-terms-accessibility.md). Каждый задаёт наблюдаемый результат, подход к тестированию, точки изменения, проверки и шаг упрощения. Production-код и тесты не менялись; реализация не начата.

Основание решения: форма уже хранит текущие raw значения, place_id и acknowledged, а form/session обеспечивают явное построение и recovery. Достаточно добавить второе состояние страницы в существующую композицию и сохранить живой draft. Новая серверная модель, route, зависимость, consent storage и переработка renderer не нужны. Способ навигации и элемент фокуса явно отданы Developer в REQ-TERMS-08 и заключении requirements.md, поэтому это технические решения плана, не DP.

### Проверенные источники

- Inputs: [change.md](../change.md), [requirements.md](../requirements.md); дополнительно [terms_draft.md](../terms_draft.md), принятый [DP-A-01](../dp/DP-A-01.md), TASK-A-02/TASK-O-01, sequences 001…003.
- Действующие [требования формы](../../../../requirements/current/ui/birth-form-and-facts.md), [сценарии](../../../../requirements/current/ui/scenarios.md), [HTTP §12](../../../../requirements/http_api.md), [обязанности Chart Renderer](../../../../requirements/component_responsibilities/exact-orb_chart_renderer.md), ADR-0009/0022/0034/0042 и technical accepted-once sequence 005. В этой задаче их контракт не меняется.
- `src/exact_orb/http_api/ui/index.html`, `styles.css` и модули `{main,form,session,places,facts}.mjs` того же каталога; вызывающие mount/submit/renderSession, form.acknowledge/prepareSubmission, восстановление и focus. `http_api/app.py`, package-data в pyproject.toml и `tests/http_api/test_ui_delivery.py` задают существующую доставку без business-вызовов.
- Для состава текста сверены `session/state.py` (7/30 дней), `http_api/cookie.py` (604800 секунд), `application/bootstrap.py` (SQLite и process-local cache), `calculation/cache.py` (opaque bytes и отдельный optional TTL), `logging_setup.py`/`component_logging.py` (локальный DEBUG и отдельная ротация), отсутствие Research/LLM в M1 composition. Это сверка локальной реализации, не удалённого стенда и не юридическое заключение.
- Прочитаны `tests/ui/form.test.mjs`, session/recovery/accepted_chart/aspect_view и fixtures/dom/session; для визуального контроля план не подменяет браузер этим DOM-port. Известный отложенный privacy-риск не оформляется повторной находкой.

### Ревью каждого требования

Стоимость указана через промты и не суммируется повторно между REQ; численные оценки промтов приведены ниже.

| REQ | Реализуемость и проверяемое основание | Плановая стоимость | Неясности / решение |
| --- | --- | --- | --- |
| REQ-UI-03 | Существующие prepareSubmission/coordinator различают G1…G4 и R1…R3; оба способа отметки используют один gate, payload из трёх полей | 01/02 | Новых кодов/полей нет; позитивный submit дополняет запреты |
| REQ-TERMS-01 | Отдельная секция, нативная ссылка вне label; вычисляемый шрифт совпадает с `.check small`; чтение не валидирует поля | 01/03 | URL и механизм перехода — технический выбор, без reload |
| REQ-TERMS-02 | form.acknowledge(true) при agree; T1/T2 и повторный проход | 01 | Явный результат однозначен |
| REQ-TERMS-03 | back не меняет acknowledged; T3/T4 и проход после ручного снятия | 01 | Не восстанавливать старое «Согласен» |
| REQ-TERMS-04 | Сохраняются live DOM и draft; D1/D2/D3 включают raw time, query, place_id/name и пустые значения | 01/02 | Поздний initial current требует защиты draft; технически решаемо в main |
| REQ-TERMS-05 | Open/return не вызывают coordinator.submit и не заменяют accepted result; повторное действие идемпотентно | 01/02 | Реальные ответы прежнего build/recovery продолжают приниматься, чтение не объявляется их причиной |
| REQ-TERMS-06 | Статический утверждённый текст C1…C8; контакт exact_orb@mail.ru принят; проверка точной версии source при поставке | 01/03 | Полный текст ещё черновик; штатное утверждение Owner на APPROVAL — предусловие, не новая неопределённость |
| REQ-TERMS-07 | Новый mount уже unchecked; storage и API-поле не добавляются; L1/L2/L3 после обоих способов отметки | 02/03 | Browser reload/закрытие нужно проверить отдельно от remount |
| REQ-TERMS-08 | Нативные ссылка/кнопки, видимый focus, 360 px и effective 44 × 44; скрытая страница исключается из Tab | 01/02/03 | Конкретный focus выбран в плане; layout/Q44 — только native browser evidence |

### Оценка

Frontmatter estimate — будущая реализация с независимым ревью кода: **17 чч / 6 мч, confidence medium**. Промты: 01 — 6/2; 02 — 5/2; 03 — 4/1.5; сумма реализации и Developer-проверок 15 чч / 5.5 мч. Отдельно code_review — 2 чч / 0.5 мч. Текущий review/план оценивается отдельно в 3 чч / 1 мч и в эту сумму не входит. Оценка не является фактически затраченным временем и не назначает бюджет/календарный срок.

Допущения: утверждён текст в текущем scope, доступны объявленные зависимости и браузер; нет нового продуктового выбора; одна небольшая итерация code_review. Внешние ожидания, восстановление окружения, приёмка Tester, transfer, push, интеграция и юридическая/эксплуатационная готовность не оценены как реализация.

### Самопроверка

Фактически выполнено:

```powershell
node --test tests/ui/form.test.mjs tests/ui/session.test.mjs tests/ui/recovery.test.mjs tests/ui/accepted_chart.test.mjs tests/ui/aspect_view.test.mjs
.venv/Scripts/python.exe -m pytest tests/http_api/test_ui_delivery.py -q -p no:cacheprovider --basetemp=C:/Users/KateUser/.codex/visualizations/2026/10/22/01a164bb-ddc3-7da0-a12b-ae87cdae4903/terms-review-pytest
python C:/Users/KateUser/.codex/visualizations/2026/10/22/01a164bb-ddc3-7da0-a12b-ae87cdae4903/terms-review/check_review.py --verify
git diff --check
git diff --cached --check
git diff --cached --name-only
```

- Node: **146 passed / 0 failed**, exit 0. Это существующее покрытие, не PASS новых AS-TERMS.
- Pytest: первый sandbox-запуск не дал вывода и прерван (exit 1); повтор вне sandbox завершён: **7 failed in 2.01s**, exit 1. Шесть tests не вошли в проверяемое поведение из-за `ModuleNotFoundError: No module named 'fastapi'`; wheel test завершился `BackendUnavailable: Cannot import 'setuptools.build_meta'`. Это ограничение `.venv`, не установленный дефект UI; зависимости не устанавливались.
- `check_review.py --verify`: проверяет комплект из пяти файлов, девять reviewed_reqs, таблицу структуры, три промта до 60 строк с первыми четырьмя строками по шаблону, ссылки, арифметику оценки, владение diff и неизменность остальных отслеживаемых файлов. Это локальная самопроверка документов, не новый quality gate проекта.
- Git diff checks: exit 0; в index только пять файлов этой задачи. Посторонние исходные untracked сохранены, дерево целиком не объявляется чистым.

Полный pytest, весь Node suite, новые AS-TERMS, browser/layout/реальный reload, screen reader, доставка M1-9 из wheel, удалённый HTTPS, доступность email, публичный исходный код будущей поставки и юридическая проверка не выполнялись. Оркестратор, push, переход гейта и закрытие долга не запускались.

Production-функции не менялись; сложность до/после и radon не измерялись и для documentation review неприменимы. Плановое упрощение — общий обработчик возвратов и единая видимость вместо копирования черновика; реализованным оно не объявляется. Shortcut'ы и временные обходы в код не добавлялись. Spike не проводился.

## Findings

Открытых DP нет: все девять требований реализуемы в согласованных границах. DP-A-01 остаётся ACCEPTED и не переоткрывается. Противоречия, требующего изменения ADR или выбора Owner сверх уже предусмотренного утверждения текста, не обнаружено.

Утверждение текста на APPROVAL, техническая реализация, независимые test/code_review, перенос требований и интеграция — отдельные этапы. Готовность review не означает одобрения текста, принятия M1-9 либо погашения DEBT-UI-001. Статус Tester review в этой задаче не меняется.

## Риски

- Защита draft/focus от поздних ответов должна закрыть пустой initial draft, активный POST и recovery; иначе чтение может скрыть возвращаемую форму. Ответственный — Developer implement 02, проверки deferred с позитивным обычным восстановлением.
- До утверждения Owner полный текст публиковать нельзя; по C7 нужно evidence полного кода используемой версии. Ответственные — Owner (текст), Developer (поставка/сверка), Tester (независимая проверка).
- Существующее `.venv` не позволяет подтвердить HTTP/wheel delivery; до implement требуется рабочее окружение с объявленными зависимостями. Это ограничивает проверку baseline, не создаёт новое продуктовое требование.
- Нативные области нажатия, focus, font и overflow требуют браузера; `documentPort` их не моделирует. Ответственный — Developer implement 03, затем Tester.

Следующий шаг: завершить TASK-T-01; при обоих review DONE / done и выполнении условий перехода 5 оркестратор отдельно создаёт Manager summary и Owner approve. В этой сессии после одного коммита остановиться.
