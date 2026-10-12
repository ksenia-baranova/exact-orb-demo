# Artifact templates

Шаблоны поддерживают [Change development process](../process/process.md) и распределены по владельцам смысла.

Пути заполненных требований, сценариев, findings, диаграмм и ADR определены в
[правилах требований](../../requirements/README.md). Здесь хранятся шаблоны, а материалы реального change создаются
в одной папке `docs/project_management/change_plans/<change-id>/` по process.md, раздел 7: manager_artifact.md и индексы участвующих ролей и подпапки ролей. [Учебный пример manager_artifact.md](examples/example-limit-boundary/manager_artifact.md) иллюстрирует минимальный ручной режим и обновление базы; его данные вымышлены и не являются evidence реального change.

| Владелец или участники | Шаблоны |
|---|---|
| Все роли; структуру и baseline поддерживает Change Manager | [Единый реестр решений](decision-register.md) |
| Change Manager | [Единый manager_artifact.md: Brief, состояния, DP, Change Plan, журнал и приёмка](change-manager.md) |
| Functional Analyst | [Дельта/полная спецификация, сценарии, Finding, Handoff и карта переноса](functional-analyst.md) |
| Developer | [Implementation Plan с estimate, Development Finding и Handoff](developer.md); [промт с пояснениями, примерами и выбором подхода к разработке](developer-prompt.md) |
| Tester | [Testability Review, Test Plan, Defect, Acceptance Evidence](tester.md) |

Для нового change оба шаблона Change Manager заполняют разделы одного
`docs/project_management/change_plans/<change-id>/manager_artifact.md`; отдельные файлы brief,
реестра, плана или приёмки не создаются.

## Правила использования

1. Копируй только нужный шаблон, а не весь файл. Manager ведёт один `docs/project_management/change_plans/<change-id>/manager_artifact.md`; реестр DP — его раздел. Текущие состояния change, заданий и версий артефактов записываются только в сводке этого файла. Analyst, Developer и Tester ведут краткие корневые индексы по новым разделам своих шаблонов; подробные материалы находятся в подпапках ролей.
2. Для каждого существенного вопроса создаётся одна строка `DP-*` в едином реестре решений. Вопрос, варианты,
   рекомендации ролей, выбор владельца и подтверждение не копируются в ролевые документы.
3. Requirements, планы и handoff указывают baseline реестра и связанные идентификаторы `DP-*`.
4. Не создавай новый документ, если существующий актуальный artifact уже владеет этой информацией.
5. Ссылка на evidence должна вести к конкретному документу, коду, тесту, комментарию или коммиту.
6. Поля `Owner`, `Status`, `Blocks` и `Closure evidence` обязательны для blocking items.
7. Таблица findings является индексом. Каждый finding, влияющий на поведение, scope, estimate, architecture, security,
   concurrency или lifecycle, получает развёрнутый раздел.
8. Архитектурное решение дополнительно оформляется ADR. Строка `DP-*` содержит ссылку на ADR и не пересказывает его.
9. Reviewer, критерий принятия и сроки ответа / эскалации задаются до начала задания. Короткий handoff содержит TaskId, версию, результат, blockers и ссылки на подробное evidence; запись ведётся по разделу 1.1 процесса, для сборщика — по приложению А.
10. Выбор полного, сокращённого маршрута или его малого варианта фиксируется Manager. Создаются только назначенные задания и необходимые материалы; состояния отсутствующего документа не заполняются.

11. Gates определены только в process.md, раздел 3.1; в заполненном manager_artifact.md хранятся их подтверждения. Ручному режиму достаточно handoff и записи в журнале; для сборщика регистрируются источники и устойчивый EventId. Приёмка и поле «Поставка: интегрирована / нет» связываются через MainBaseline, CandidateSHA, фактический TestedSHA и MergeSHA; обновление базы классифицируется по разделу 6.1.

После финальных approvals и приёмки Owner изменённые требования / sequences переносятся в общие каталоги и сверяются по process.md, раздел 6.2. Если перенос не требуется, достаточно подтверждения Tester на G5. Малый вариант допускает один файл Manager с ролевыми заключениями; фиктивные документы и approvals не создаются.
