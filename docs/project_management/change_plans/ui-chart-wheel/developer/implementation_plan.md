# Implementation Plan: ui-chart-wheel

**Автор:** Codex / Developer, `TASK-D-001`, 2026-10-15; consultation v1, предварительный план.
**InputSHA / реестр:** `2b846077b317e33dd892565419942c4db8517b1e`, [Manager](../manager_artifact.md) §3. Применимы DP-O-001…014. Вклад в строки DP-O-010…014 подготовлен в [patch](decision_input.patch), в реестр ещё не внесён.
**Сводка состояния:** [manager_artifact.md](../manager_artifact.md); начало реализации не назначено.
**Исходный нормативный контракт:** [UI](../../../../requirements/current/ui/birth-form-and-facts.md), [AS-UI-01…23](../../../../requirements/current/ui/scenarios.md), [HTTP §7.2](../../../../requirements/http_api.md#72-chartdto), ADR-0029/0030/0032/0034/0040/0041 @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1`; по scoped diff эти источники не изменены в InputSHA.
**Контракт change для консультации:** [requirements](../analyst/requirements.md), [scenarios](../analyst/scenarios.md), [findings](../analyst/findings.md), [sequences](../analyst/sequence_diagrams/ui/) v1 @ `683bdd0c1f5a0e65735f4e48127d408300ec697c`, интеграция `bc9a4fbf169e43fbfc42d530b870cf6371c72fbf`. Пакет ещё без approvals и не синхронизирован с поздними DP; это не approved input для кода.
**Заключение:** FEASIBLE WITH DECISIONS. **Estimate:** 8–12 чд Developer; уверенность ниже средней до измерения плотности и закрытия interaction-вопросов.

## Оценка и её основание

| Состав Developer-работы | Чд | Что включено |
|---|---|---|
| Графическая часть и её интеграция | 5–7 | Уточнение границы, bounded spike, drawing ADR и technical sequences; чистая геометрия, SVG natal/cosmogram, endpoints angles, R/☌, раскладка, легенда, локальный отказ, Developer checks |
| Двусторонний выбор и страница | 3–5 | Общее локальное состояние, фильтрация аспектов / раскрытие таблиц, keyboard, сводка / редактор, draft/recovery интеграция, автоматическая регрессия и воспроизводимый handoff |
| Всего | 8–12 | Один Developer; без суммирования повторно одних и тех же checks |

Допущения: сохраняются vanilla ES modules и native SVG, нет новых зависимостей / API / renderer framework; текущий состав 16 point IDs и five angles достаточен; Owner не расширяет scope; Analyst своевременно выдаёт согласованный expected result. Документальная подготовка текущего пакета отдельно не измерялась и не объявляется фактическими чд.

Исключены из оценки: Analyst rework, независимый Tester и Owner acceptance, ожидание решений / review, полный M1-8.1, deployment / HTTPS setup и M1-9. Тестер может выявить дефекты: адресные исправления входят в обычную разработку, существенный пересмотр контракта требует переоценки. Диапазон — трудозатраты, не календарный срок и не бюджет Owner. Roadmap 5 дней — исторический ориентир для менее детализированного scope, не подтверждённый текущей оценкой. Верхняя граница 12 не является обязательством при неразрешимой плотности: после spike нужна повторная оценка.

Главная неопределённость — читаемость 16 близких точек с R/☌/углами и достижимыми целями на 360 px при сохранении истинных позиций. Одних численных координат и fake DOM для этого недостаточно.

## Проверенные технические зависимости

| Источник | Вывод и следствие |
|---|---|
| [facts.mjs](../../../../../src/exact_orb/http_api/ui/facts.mjs), readChartFacts / mountChartResult | HTML mapper сохраняет опубликованные значения, но исключает longitude/cusp_longitude. SVG должен читать подтверждённый ChartDTO, а не восстанавливать долготы из округлённых строк. При обновлении таблицы создаются заново: выбор и фокус нужно сохранять явно. |
| [main.mjs](../../../../../src/exact_orb/http_api/ui/main.mjs), renderSession | Уже разделены current birth, committed submitted summary и draft. Status/recheck/errors расположены внутри формы: сворачивать только редактор, оставив feedback и recovery доступными. |
| [session.mjs](../../../../../src/exact_orb/http_api/ui/session.mjs), publish | Любой проброшенный render exception ставит requiresReconciliation. Ожидаемый локальный отказ SVG нужно отобразить внутри presentation boundary, сохранив успешные HTML факты той же identity; общий обработчик иных сбоев сохраняется. |
| [HTTP](../../../../requirements/http_api.md#72-chartdto), F0/F1 | Аспекты адресуют points либо asc/mc/vertex. Резолвить endpoints по canonical IDs; dsc/ic только опубликованные позиции. Данных достаточно без расширения API. |
| [test_ui_delivery.py](../../../../../tests/http_api/test_ui_delivery.py), app.py, pyproject.toml | Native .mjs уже доставляются как package resources с no-cache; новые renderer modules добавить в проверяемый набор UI_RESOURCES. Новая runtime-служба не нужна. |
| [DOM port](../../../../../tests/ui/fixtures/dom.mjs) | Есть монтаж/события/фокус, нет SVG namespace, шрифтов и layout. Дополнить только требуемые листовые DOM API; визуальные утверждения вынести в реальный browser evidence. |

Существующее покрытие прочитано, но в этой консультации не запускалось: facts.test.mjs (immutable DTO, порядок, angles, full golden, stale/identity); session.test.mjs (manual gate, summary, pending draft, mounted errors); recovery.test.mjs (lost response, timeout, safe read, two tabs); HTTP projector / delivery и module boundaries. Новые графические и selection-сценарии этим не доказаны.

## Необходимый bounded spike

| Вопрос | Метод | Предел / результат |
|---|---|---|
| Помещаются ли glyph+R+☌ и доступные цели на 360 px? | На F1, F3 и F3-max из AS-WHEEL-09/10 сравнить исходные истинные позиции и разнос только конфликтующих меток. Измерить реальные bbox шрифта, 0° seam, углы, клавиатуру, SVG viewBox и viewport 1440/768/360. Геометрия отдельно от DOM. | До 0,75 чд внутри 5–7 чд графики; после отдельного назначения DEV-WHEEL-01. Выход: screenshots/размеры/контрпримеры и рекомендация DP-O-011/013. Не удлинять исследование молча; при неуспехе вернуть Owner варианты и estimate. |

Сейчас spike не выполнялся. Прототип spread() не служит доказательством, а ослабление требований или скрытие точек не допускаются. До него estimate остаётся предварительным; исполняемая feasibility консультация на финальной версии не подтверждена.

## Решения и вопросы владельцам

- DP-O-010: Developer предлагает локальный renderer port и selection у page/result controller; подписанная рекомендация и failure seam — в patch. Не утверждены имя / интерфейс; транспорт и coordinator менять для renderer не требуется.
- DP-O-011: уточнить критерий успешного разноса и fallback при фактической невозможности; требуется spike. Принятые правила Owner уже учитываются, повторного выбора ориентации нет.
- DP-O-012: согласовать палитру / легенду, а также вид категории / выбора для ☌; обычная толщина выбранной линии не описывает маркер соединения.
- DP-O-013: уточнить point/aspect toggle, same-identity current, новый current другой вкладки, углы / точки в композиции, редактирование при повторном успехе, keyboard / hit targets. Подтверждённые лимиты и отсутствие кнопки снятия не переоткрываются.
- DP-O-014: выбор принят; требуется перенос в Analyst и drawing ADR с геометрическим контролем, а не новое решение Owner.

Вопросы и closure evidence — [findings](findings.md). Существенное содержание рекомендаций передаётся один раз в patch к реестру; accepted решения и статусы Developer не меняет.

## Инварианты и границы

Только принятый committed/current ChartDTO одной identity; immutable данные; никаких расчётов знаков/домов/категорий/orb, aliases или синтеза неизвестного времени. Только геометрический перевод опубликованной долготы. Background не получает линию или ☌ даже при выборе. Нет автоматического POST от выбора, resize, раскрытия формы, отказа SVG; manual unchecked gate, Retry-After/restart, draft protection и поздние ответы сохраняются. Нет новых сетевых логгеров, библиотек и услуг. Фактические DOM переходы доказываются локальным UI evidence; серверный журнал не доказывает render.

## Work items

Это предлагаемые срезы, не разрешённая разработка. Промты фиксируют исходный consultation baseline; перед запуском каждый должен получить точную утверждённую версию по G3, либо отдельное разрешение на ограниченный spike / ADR до реализации.

### DEV-WHEEL-01. Проверенная граница и drawing rules

- REQ-WHEEL-01/02/05/06/10/11; AS-WHEEL-03/04/09/10/16/23/24/25; DP-O-010…014; исходные ADR выше. [Промт 01](prompts/01-renderer-decisions-and-spike.md).
- Подход: документальные проверки + bounded browser spike, без production code. Основание: ещё требуется уточнение expected result; тесты не выбирают продуктовый контракт.
- Материалы: developer/ spike evidence / technical sequences, предложение нового drawing ADR в docs/requirements/decisions/ с номером по актуальному реестру. Не менять Analyst-owned sequences.
- Existing coverage: F0/F1 и тесты API подтверждают доступность данных только после своего запуска; плотность не покрыта. Добавить отчёт с измерениями, не новый fixture engine golden.
- Проверки: links/PUML structure/render, реальный viewport/fonts; геометрический контроль сторон; вход/выход renderer, выбор и видимый отказ прослеживаются в sequence.
- Зависимость / завершение: отдельное назначение spike; решения, reviewers и опубликованные ADR / рекомендации; затем повторная оценка и G3 до кода.

### DEV-WHEEL-02. SVG той же опубликованной карты

- REQ-WHEEL-01…06/09…11; AS-WHEEL-01…10/15/16/24/25; DP-O-001/002/004…007/009…012/014. [Промт 02](prompts/02-svg-renderer.md).
- Подход: тесты → реализация для чистой геометрии / endpoint resolver / категории; DOM сборка → integration tests. Риск зеркальности, 0°, потерянных angles и ложных линий требует чувствительных численных assertions, не snapshots реализации.
- Files: новые `ui/wheel*.mjs` (имена уточнить в ADR), точечные facts/main/styles, новые tests/ui/wheel*.test.mjs и листовые fixture API; UI_RESOURCES в delivery test. Покрытие baseline см. выше; SVG отсутствует.
- Проверки: F0 moon→asc, F1 16/12/46 и 15 angle endpoints, F3 R/☌; число линий выводится из опубликованных категорий. Четыре стороны при ref+0/90/180/270, published asc, empty/cosmogram. Команды — промт 02, затем связанные Node / HTTP checks.
- Observability: accepted DTO → HTML / SVG той же identity → результат / локальный отказ, доступный message, no network; alternate renderer positive control.
- Завершение: согласованные drawing rules, target/related checks и browser измерения; отсутствие частичных старых фактов при замене карты. DEV-WHEEL-01 и G3 обязательны.

### DEV-WHEEL-03. Согласованный выбор колеса и таблиц

- REQ-WHEEL-04/07/08/10/11; REQ-UI-04/06/10; AS-WHEEL-04/07/11…15/23/24; DP-O-008/010/012/013. [Промт 03](prompts/03-selection-and-tables.md).
- Подход: тесты → реализация state transitions; реальный result controller, листовой renderer/DOM/network. Baseline facts tests не покрывают selection; переиспользовать canonical order и immutable DTO tests.
- Files: локальное result/selection соединение в ui/*.mjs, facts.mjs, styles.css; tests/ui/selection.test.mjs (новый), facts.test.mjs и DOM port по необходимости.
- Проверки: point→aspect rows и обратное; angles endpoint; background без графического обозначения; 5/all/selected/toggle; selection/reset/resize по окончательному DP; keyboard/focus и no HTTP с позитивным контролем явного build.
- Observability: initiator + identity + canonical key → controller → оба представления, в порядке действий. Нет обязательной runtime телеметрии.
- Завершение: exact input/DP, чувствительные tests, доступность без hover и реальная browser проверка; DEV-WHEEL-02 и утверждённый DP-O-013.

### DEV-WHEEL-04. Сводка, редактор и recovery в новом представлении

- REQ-WHEEL-01/08/09/11; REQ-UI-01/03/08/09/10/11; AS-WHEEL-01/02/12/14…22/24; DP-O-001…003/010/013. [Промт 04](prompts/04-page-form-and-recovery.md).
- Подход: сборка существующих компонентов → mounted tests; сначала чувствительный regression для конкретного подтверждённого дефекта, если найден. Coordinator recovery уже покрыт — добавлять только assertions нового UI.
- Files: main.mjs/facts.mjs/index.html/styles.css; session/recovery production code лишь при доказанной необходимости и отдельной оценке влияния. tests/ui/session.test.mjs, recovery.test.mjs, facts.test.mjs; delivery resources.
- Проверки: submitted A / draft B / current C, collapse/reveal, rejected build, failed read, timeout/restart, two tabs/late responses и dispose; свёрнутый редактор не скрывает feedback / safe read. Target Node → все Node → HTTP delivery/projectors/boundaries → полный pytest перед G4 на CandidateSHA.
- Observability: существующие HTTP sequence и request_id / run_id + локальная передача принятого outcome в представления. UI controls и их gates доступны и коррелируют с actual chart.
- Завершение: все work items, commands/results/SHA, runtime limitations и handoff; независимый Tester и Owner acceptance остаются отдельными заданиями.

## Порядок интеграции, проверка и возврат

Manager/Analyst синхронизация → назначенный DEV-WHEEL-01 → утверждённые DP/контракт/план и G3 → 02 → 03 → 04 → Developer checks на CandidateSHA → Manager G4 → независимый Tester. Параллельные ролевые консультации назначает Manager; в этой сессии другие агенты / роли не запускались.

При render failure сохраняются подтверждённые данные и видимый локальный отказ. При неприемлемой плотности или неясном expected result вернуть затронутый work item владельцу DP, продолжая только независимо разрешённую работу. Возврат к статичной картинке без выбора или скрытие точек не являются согласованным rollback. Публикация Developer-пакета разрешена отдельным поручением Owner по корневому индексу; Git rollback / merge не поручены. Чистовой перенос требований и technical sequences — после acceptance по назначению Manager.
