# Artifact templates

Шаблоны поддерживают [Change development process](../process.md) и распределены по владельцам смысла.

Пути заполненных требований, сценариев, findings, диаграмм и ADR определены в
[правилах требований](../../requirements/README.md). Здесь хранятся шаблоны, а материалы реального change создаются
в соответствующих предметных каталогах.

| Владелец или участники | Шаблоны |
|---|---|
| Все роли; структуру и baseline поддерживает Change Manager | [Единый реестр решений](decision-register.md) |
| Change Manager | [Change Brief, Change Plan, Final Acceptance](change-manager.md) |
| Functional Analyst | [Дельта/полная спецификация, сценарии, Finding, Handoff и карта переноса](functional-analyst.md) |
| Developer | [Implementation Plan с estimate, Development Finding и Handoff](developer.md); [промт с пояснениями, примерами и выбором подхода к разработке](developer-prompt.md) |
| Tester | [Testability Review, Test Plan, Defect, Acceptance Evidence](tester.md) |

## Правила использования

1. Копируй только нужный шаблон, а не весь файл.
2. Для каждого существенного вопроса создаётся одна строка `DP-*` в едином реестре решений. Вопрос, варианты,
   рекомендации ролей, выбор владельца и подтверждение не копируются в ролевые документы.
3. Requirements, планы и handoff указывают baseline реестра и связанные идентификаторы `DP-*`.
4. Не создавай новый документ, если существующий актуальный artifact уже владеет этой информацией.
5. Ссылка на evidence должна вести к конкретному документу, коду, тесту, комментарию или коммиту.
6. Поля `Owner`, `Status`, `Blocks` и `Closure evidence` обязательны для blocking items.
7. Таблица findings является индексом. Каждый finding, влияющий на поведение, scope, estimate, architecture, security,
   concurrency или lifecycle, получает развёрнутый раздел.
8. Архитектурное решение дополнительно оформляется ADR. Строка `DP-*` содержит ссылку на ADR и не пересказывает его.
