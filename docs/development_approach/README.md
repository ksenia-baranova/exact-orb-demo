# Development approach

Эта директория описывает текущий AI-assisted подход к разработке `exact-orb`, рабочий процесс change, роли, шаблоны
артефактов и эксперименты, на которых основаны правила.

## Действующие документы

| Документ | Назначение |
|---|---|
| [Development approach](development-approach.md) | Стабильные принципы и границы метода |
| [Change development process](process.md) | Текущий рабочий цикл от намерения до принятия change |
| [Roles and ownership](roles.md) | Полномочия, ответственность и handoff ролей |
| [Artifact templates](artifacts/README.md) | Шаблоны рабочих артефактов по ролям |
| [Role skill drafts](skills/README.md) | Инструкции для агентов, реализующих роли |

## Evidence и история метода

| Раздел | Назначение |
|---|---|
| [Experiments](experiments/) | Проверяемые организационные и инженерные гипотезы |
| [Problems detected by human](problems_detected_by_human/) | Разборы дефектов, которые повлияли на метод |

Эксперименты объясняют происхождение правил, но не переопределяют действующий процесс. При расхождении используются
`development-approach.md`, `process.md` и `roles.md`.

## Изменение структуры 2026-09-30

Документ `spec-driven-development.md` был переименован в `development-approach.md` и сокращён до основных утверждений.
Название `spec-driven-development` стало узким: фактический метод охватывает обсуждение намерения, принятие решений,
role ownership, реализацию, тестирование и приёмку. Вариант `sdlc-process-approach` не выбран, потому что процесс вынесен
в отдельный документ, а `SDLC process` дублирует смысл lifecycle.

Детальные процессные правила вынесены в [process.md](process.md), роли — в [roles.md](roles.md). Историческое развитие
role-based модели сохранено в [Experiment 002](experiments/experiment-002-role-based-change-development.md).

## Карта переноса содержания

| Содержание прежнего документа | Текущий источник |
|---|---|
| Граница между предложением и решением, источники истины, переносимый контекст, executable evidence, observability, bounded prompts, review и критерии успеха | [Development approach](development-approach.md) |
| Decision gates, lifecycle change, возвраты между ролями, branching и финальная приёмка | [Change development process](process.md) |
| Распределение полномочий, запреты и handoff | [Roles and ownership](roles.md) |
| Единый реестр решений и рабочие форматы finding, estimate, plan и acceptance evidence | [Artifact templates](artifacts/README.md) |
| Ограниченные инструкции агенту для конкретной роли | [Role skill drafts](skills/README.md) |
| Примеры, хронология формирования и проверяемые гипотезы | [Experiments](experiments/) |

Такое разделение сохраняет основные утверждения прежнего документа, но не смешивает стабильные принципы с текущим
workflow, role instructions и историей экспериментов.
