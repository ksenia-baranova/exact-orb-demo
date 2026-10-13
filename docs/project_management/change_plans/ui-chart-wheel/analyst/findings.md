# Findings: ui-chart-wheel

**Автор:** Codex / Functional Analyst, TASK-A-001, 2026-10-13.
**Вход:** `5188b523089acc8081585e869c482ee0d343cfba`; code/requirements/tests @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`.
**Единый реестр:** [Manager §3](../manager_artifact.md#3-единый-реестр-dp).
Это пробелы будущего M1-8 контракта; не утверждение дефекта принятого M1-7. Уже описанные DP-O-010…013 не объявляются новыми находками. Ниже их различающие примеры и один новый вопрос для регистрации Manager.

| ID | Краткое влияние | Owner смысла | Блокирует |
|---|---|---|---|
| [FIND-WHEEL-001](#find-wheel-001) | Ориентация natal / направление зодиака не приняты | Owner; Analyst, Developer, Tester input | Утверждение геометрического expected result / G3 |
| [FIND-WHEEL-002](#find-wheel-002) | Аспекты адресуют angles; модель «две планеты» неполна | Analyst — HTTP semantics; Owner — interaction | Утверждение renderer/selection contract / G3 |
| [FIND-WHEEL-003](#find-wheel-003) | Collapse может спрятать ошибки, recheck и repeat build | Owner; Analyst/Developer/Tester input | Утверждение UI interaction / G3 |

<a id="find-wheel-001"></a>
## FIND-WHEEL-001. Нет принятой ориентации натала и направления обхода

**Type:** requirement gap. **Detected by:** Analyst. **Owner:** Owner. **Status:** OPEN.
**Blocks:** геометрические сценарии / G3; независимый Analysis не заблокирован.
**Related decision:** предложенный DP-O-014; до регистрации это не строка действующего реестра.

### Кратко для Manager

В DP-O-009 принято только положение 0° Овна слева для cosmogram. У натала неизвестно, что ставить слева; направление возрастания долгот не принято ни для одного режима. Прототип предполагает ASC слева и против часовой стрелки, но brief прямо ограничивает его нормативность. Зеркальные изображения одинаково сохраняют числа DTO и поэтому требуют явного визуального expected result.

### Где найдено

[manager_artifact.md](../manager_artifact.md) §1.3 и DP-O-009 @ InputSHA; [ui_ux/requirements.md](../../../../ui_ux/requirements.md) §7; [web-prototype.html](../../../../ui_ux/web-prototype.html) `pt()`, `wheel()` @ MainBaseline. В prototype ref для natal равен демо-100°, не действительному asc пользователя.

### Пример проявления

1. F1 natal содержит определённую asc.longitude, которая не равна demo ref=100.
2. Два renderer ставят слева ASC либо 0° Овна; оба читают тот же ChartDTO.
3. Ещё два варианта зеркально меняют направление последовательности знаков.
4. Нельзя выбрать правильный по числам таблицы или по PNG; ожидается одна утверждённая геометрическая конвенция.

### Почему существующего контракта недостаточно

Brief не принимает ASC-ориентацию прототипа, а DP-O-009 не распространяет решение на natal или направление. Это вывод Analyst по источникам, не новое Owner decision.

### Влияние

- User/API: рисунок и опорные положения различаются; API без изменения.
- State/data: исходные долготы/знаки одинаковы.
- Estimate: меняются геометрические checks и последующий visual review.
- Testing: нужны четыре контрольных положения 0/90/180/270° и фактический asc F1, не golden PNG.
- Operations/security: новых изменений нет.

### Что требуется дальше

Manager регистрирует предложенную строку DP-O-014 из [decision_input.patch](decision_input.patch); Owner выбирает после Developer/Tester input. Analyst применяет только принятое решение к REQ-WHEEL-02/03 и AS-WHEEL-25 до G3.

### Closure condition / evidence

Закрытие: зарегистрированный DP с Owner evidence, согласованные требования/сценарии и проверенный geometric expected result на точной версии. Сейчас closure evidence отсутствует; finding остаётся OPEN.

<a id="find-wheel-002"></a>
## FIND-WHEEL-002. Концы аспекта не ограничены планетами

**Type:** conflict / boundary clarification. **Detected by:** Analyst.
**Owner:** Analyst — действующая HTTP semantics; Owner — доступное interaction. **Status:** OPEN.
**Blocks:** утверждение DP-O-010/013 / G3; не исследование.
**Related decision:** DP-O-010, DP-O-013.

### Кратко для Manager

HTTP §7.2 разрешает asc/mc/vertex как концы аспекта. Кандидат UI/UX говорит о хордах между планетами. Если renderer ищет endpoint только в points, он потеряет разрешённые аспекты либо выберет неверный объект. Подсветка угла как конца аспекта не означает расширение scope самостоятельным выбором всех углов/домов.

### Где найдено

[HTTP §7.2](../../../../requirements/http_api.md#72-chartdto), [dto.py](../../../../../src/exact_orb/http_api/dto.py), [facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs) `endpointName/readChartFacts`, [test_projectors.py](../../../../../tests/http_api/test_projectors.py) endpoint checks @ MainBaseline.
[chart_dto.json](../../../../../tests/http_api/golden/chart_dto.json) natal — 3/3 аспекта с angles; [F1](../../../../../tests/ui/fixtures/natal_1985_chart_dto.json) — 15/46. Эти counts проверены чтением JSON, не запуском test suite.

### Пример проявления

1. F0 natal публикует moon→asc / square / exact / orb=0.4407655487941611.
2. Renderer ищет обе точки среди points.
3. Asc отсутствует в points и находится в angles; линия теряется либо подменяется.
4. Выбор строки обязан подсветить moon и опубликованный asc той же карты; standalone выбор asc отдельно не требуется принятым brief.

### Почему существующего контракта недостаточно

HTTP однозначен; конфликт у визуального кандидата/недетализированной модели выбора. Фронтенд не вправе фильтровать все аспекты с angles как background или создавать dsc/ic аспектные endpoints. REQ-WHEEL-02/04/07 явно наследуют текущий HTTP.

### Влияние

- User/API: отсутствует существующий опубликованный аспект; API менять не нужно.
- State/data: разные namespace points/angles должны разрешаться по canonical ID.
- Estimate: Developer оценивает графическое и доступное представление angle endpoints.
- Testing: использовать реальные F0/F1 и позитивный контроль asc/mc/vertex; не только две планеты.
- Operations/security: новых изменений нет.

### Что требуется дальше

Вклад Analyst для DP-O-010/013 передаётся Manager patch; Developer подтверждает реализуемость резолвинга, Tester — управление выделением. Owner выбирает взаимодействие в пределах прежнего scope.

### Closure condition / evidence

Согласованный renderer/selection контракт использует весь публичный набор endpoint IDs; accepted DP-O-010/013 и Developer/Tester consultations на точной версии. Closure evidence сейчас отсутствует.

<a id="find-wheel-003"></a>
## FIND-WHEEL-003. Сворачивание формы затрагивает recovery и локальный черновик

**Type:** requirement gap / interaction risk. **Detected by:** Analyst.
**Owner:** Owner. **Status:** OPEN.
**Blocks:** DP-O-013 и утверждение REQ-UI-11 / G3.
**Related decision:** DP-O-003, DP-O-013; принятое намерение collapse не пересматривается.

### Кратко для Manager

В baseline сообщения сессии, отправленные данные, ошибки, безопасное чтение и build находятся внутри birth-form. Простое скрытие всей формы после успешной карты может оставить stale/recovery без видимого действия. Повторный current не должен спрятать или перезаписать уже изменённый черновик.

### Где найдено

[main.mjs](../../../../../src/exact_orb/http_api/ui/main.mjs) `mountBirthForm/renderSession`: sessionStatus/submitted/readAgain вставляются в form; [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs) `accept/publish/submit`; [session.test.mjs](../../../../../tests/ui/session.test.mjs) pending draft / rejected summary; [recovery.test.mjs](../../../../../tests/ui/recovery.test.mjs) mounted feedback и failed check @ MainBaseline.

### Пример проявления

1. Показана A; форма свернута.
2. Foreground current сообщает stale или временный STATE_READ_FAILED; либо новый B build теряет ответ.
3. Если вся форма hidden, сообщение и «Повторить проверку карты» / явный повтор недоступны.
4. Требуется сохранить доступное действие с правильными gates и различать сводку A, отправленное намерение B и текущий черновик.

Второй контроль: пользователь редактирует B, пока initial/current A ожидается; поздний A не затирает B и не скрывает его без принятой политики.

### Почему существующего контракта недостаточно

DP-O-003 задаёт сводку/раскрытие, не расположение recovery controls, focus и поведение после повторного редактирования. DP-O-013 уже содержит эти вопросы; finding конкретизирует последствия, не дублирует новую DP.

### Влияние

- User/API: доступность retry/ошибки/явного build; schemas и requests неизменны.
- State/data: сохранить независимость confirmed result, submitted intent и draft.
- Estimate: нужны UI state transitions и проверки монтажа, не перепроектирование coordinator.
- Testing: mounted сценарии AS-WHEEL-17…22 и keyboard controls, включая негативный gate и успешный safe read.
- Operations/security: действующий manual checkbox, Retry-After/restart gate сохраняются.

### Что требуется дальше

Manager дополняет DP-O-013 подписанной рекомендацией Analyst; Developer предлагает технически реализуемый показ controls, Tester проверяет все mounted branches. Не задаются конкретные DOM-модули или внутренний algorithm.

### Closure condition / evidence

Owner принял focus/collapse/retry поведение; Analyst выпустил точный expected result, Developer/Tester подтвердили его. Closure evidence отсутствует. Известные долги M1-9/logging не являются новыми findings этого пакета.
