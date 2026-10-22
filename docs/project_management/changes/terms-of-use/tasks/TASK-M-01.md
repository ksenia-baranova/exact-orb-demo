---
id: TASK-M-01
change: terms-of-use
role: manager
kind: intake
gate: INTAKE
cycle: 0
inputs: [запрос owner'а]
origin: null
agent: null
model: null
status: IN_PROGRESS
resolution: null
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: []
commit: null
estimate: null
---
## Задание
Заполнить change.md: цель, скоуп, вне скоупа, результат, источники; создать roadmap.md с оценкой анализа 2 чд. Owner подтверждает описание.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат
Промежуточный результат на 2026-10-22: заполнен [change.md](../change.md) и создан [roadmap.md](../roadmap.md) по действующим шаблонам. Задача остаётся IN_PROGRESS / resolution: null до явного подтверждения Owner конкретной заполненной редакции.

Принятые решения Owner перенесены из текущего чата с точными цитатами в источники change.md: текстовая ссылка под checkbox; оба способа подтверждения; «Согласен» возвращает с выбранным checkbox; «Вернуться к форме» сохраняет его состояние; при обоих возвратах сохраняются дата, место и время; построение отдельно; после новой загрузки отметка снята; черновик готовит Analyst, окончательный текст утверждает Owner.

В roadmap внесена только процессная стартовая оценка анализа 2 чд / 16 чч. Оценки ролей, мч, факт и календарные обязательства не выдумывались. Gantt по мч ожидает входных данных. Исторический план M1-9 не принят за новый бюджет.

Входной baseline: C:\Users\KateUser\PycharmProjects\exact-orb-recovered, ветка change/terms-of-use, HEAD 9f36ee8c8d6b3105de0ed633c23abe7fdeac7fea. Проверки до записи:
- `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered branch --show-current` → change/terms-of-use.
- `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered rev-parse HEAD` → указанный baseline.
- `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered status --short --branch --untracked-files=all` → присутствуют исходные untracked, включая change.md и эту задачу; дерево не чистое.
- `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered diff --name-status` и `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered diff --cached --name-status` → отслеживаемых unstaged и staged изменений на входе нет.
- Git в sandbox получил Permission denied; повторная read-only проверка выполнена с разрешённым доступом к указанной копии.

Фактические проверки после записи:
- `python -X utf8 C:/Users/KateUser/AppData/Local/Temp/validate_terms_intake_m01.py` → `DOCS_OK files=3 local_links=51 sections=15 whitespace=PASS metadata=PASS protected_paths=45 open_dp=0`. Временная проверка проверяет структуру по шаблонам, ссылки, пробелы, неизменность frontmatter изменения и полей оркестратора в задаче; SHA-256 защищённых путей сверяется с входным снимком.
- `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered diff --check` → exit 0; проверяет отслеживаемые файлы. Все три untracked-документа отдельно проверены на завершающие пробелы и структуру временной проверкой выше.
- Повторены `branch --show-current`, `rev-parse HEAD`, `diff --name-status`, `diff --cached --name-status` с теми же `git --no-optional-locks -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered`: ветка и HEAD прежние, отслеживаемых unstaged и staged изменений нет.
- `git --no-optional-locks -c core.quotePath=false -C C:/Users/KateUser/PycharmProjects/exact-orb-recovered ls-files --others --exclude-standard` и сравнение с входным снимком → 36 исходных untracked сохранены; единственный новый путь — roadmap.md, всего 37. Из них изменены только ранее существовавшие change.md и TASK-M-01.md.
- SHA-256 45 защищённых путей сохранены, в том числе исходные посторонние untracked, events.jsonl, debug_log.md, отсутствие decisions.md, общие документы и ADR. Status/cycle изменения и поля оркестратора в задаче сохранены.

pytest, браузерная проверка, рендер диаграмм и юридическая проверка текста не выполнялись; код, тесты и окончательный текст в этой задаче не создаются.

Коммит пока не создан: Owner должен подтвердить заполненное описание. После подтверждения и при отсутствии OPEN DP допустимы DONE / done и один коммит только трёх файлов Manager с заданным сообщением. Push и запуск оркестратора не выполняются.

## Findings
- Существенные решения для intake уже есть в действующих источниках и подтверждениях Owner; повторные вопросы не поднимаются. Новых нерешённых развилок о проблеме, скоупе, приоритетах и сроках не найдено; DP не создавались, raised_dp: [].
- Минимальное содержание страницы и смысл checkbox взяты из ADR-0034; условие до распространения ссылки — из DEBT-UI-001 и общей дорожной карты. Публичная готовность целиком в M1-9 не включается.
- Строка DEBT-UI-001 ещё не называет погашающий change. Источник связывает её с M1-9; текущее поручение задаёт terms-of-use. Эта связь отражена в change.md; общий реестр не редактировался и долг не закрывался.
- Наличие исходных untracked — установленный baseline, а не основание применять stash, reset или clean. Посторонние файлы и журналы оркестратора сохраняются.
- Оценки ролей, контакт для итогового текста и конкретные формулировки не определены intake: оценки должны дать роли, текст готовит Analyst и утверждает Owner в последующей работе.

## Риски
- Подтверждение ознакомления нельзя представлять доказательством юридического согласия. Действующая граница ADR-0034 сохранена.
- Готовность текста и страницы не закрывает остальные юридические и эксплуатационные условия публичного запуска; это отдельные зависимости, без автоматического расширения скоупа.
- Пока оценки ролей не получены, отсутствуют основания обещать общий бюджет и дату поставки.
- До явного подтверждения данной редакции нельзя завершать TASK-M-01, делать итоговый коммит или передавать оркестратору завершённый intake.
