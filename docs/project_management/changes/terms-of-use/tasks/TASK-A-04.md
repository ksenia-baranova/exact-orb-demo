---
id: TASK-A-04
change: terms-of-use
role: analyst
kind: transfer
gate: DONE
cycle: 1
inputs: [requirements.md, sequences/]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: [REQ-UI-03, REQ-TERMS-01, REQ-TERMS-02, REQ-TERMS-03, REQ-TERMS-04, REQ-TERMS-05, REQ-TERMS-06, REQ-TERMS-07, REQ-TERMS-08]
reviewed_reqs: []
commit: null
estimate: { чч: 3, мч: 0.7, confidence: medium }
---
## Задание
Перенести требования и sequences изменения в current/.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

2026-11-03: принятый инкремент перенесён по `action`, `base`, `target` без нового продуктового решения. Задача завершена как `DONE / done`. ID сохранены; REMOVE в инкременте нет. `changed_reqs` перечисляет перенесённую дельту действующей редакции, а не новые изменения утверждённых требований.

### Вход и границы

- Git-база: опубликованный `origin/change/terms-of-use` = `0807cd05cedc457434149b4479ee4c6262a88dec`. Чистый выделенный worktree: `C:\Users\KateUser\.codex\worktrees\c7fb\exact-orb-recovered`, detached HEAD; новая ветка не создавалась.
- Локальный вход оркестратора: эта задача и переход 13 `READY_FOR_TEST → DONE` от `2026-11-03T18:23:42+00:00` в исходной рабочей копии `C:\Users\KateUser\PycharmProjects\exact-orb-recovered`. Они ещё не опубликованы. В исходной копии `change.md` имеет DONE; в опубликованной базе остался BUG_FIX. Сам Analyst статус изменения и events не меняет и не переносит в свой коммит.
- [Требования](../requirements.md), три исходных sequences, [DP-R-01](../dp/DP-R-01.md) и [риски](../risks.md) исходной копии совпадают с опубликованной базой после нормализации LF/CRLF. Утверждённый пакет — `02cbd17e33ceffe52d465bdf6b8faf1d3c76864c`, [TASK-O-02](TASK-O-02.md). Позднее решение Owner C по DP-R-01 сохраняется.
- Прочитаны правила transfer, действующие UI requirements/scenarios, ADR-0034, обязанности Chart Renderer, код переходов `main.mjs`, существующее покрытие `terms.test.mjs`, `terms_acceptance.mjs` и границ HTTP. Код не использовался вместо нормативного источника.
- Оценка до переноса: **3 чч / 0.7 мч, confidence medium**, прогноз, не хронометраж. Реализация, повторная приёмка, публикация и оркестрация в оценку не входят.

### Перенос

| Инкремент | Результат в действующей редакции |
| --- | --- |
| MODIFY REQ-UI-03 | [Полная замена пункта формы](../../../../requirements/current/ui/birth-form-and-facts.md#req-ui-03), таблицы G1…G4 и R1…R3; оба способа отметки, отдельный POST |
| ADD REQ-TERMS-01…08 | [Условия использования](../../../../requirements/current/ui/terms-of-use.md), глоссарий, таблицы T/D/C/L; поля переноса удалены |
| AS-TERMS-01…18 | [Сценарии](../../../../requirements/current/ui/terms-of-use.md#сценарии-given--when--then) перенесены вместе с новыми требованиями, Given/When/Then и контролями |
| MODIFY AS-UI-20/21 | [Существующие сценарии](../../../../requirements/current/ui/scenarios.md#as-ui-20), ID и заголовок AS-UI-21 сохранены; заменён также явно указанный общий абзац «Условия решения и границы проверки» |
| sequence 001 → target 009 | [Чтение и два возврата](../../../../sequence_diagrams/ui/009-terms-roundtrip.puml) |
| sequence 002 → target 010 | [Черновик и новая загрузка](../../../../sequence_diagrams/ui/010-terms-draft-lifecycle.puml) |
| sequence 003 → target 011 | [Граница явного построения](../../../../sequence_diagrams/ui/011-terms-build-boundary.puml) |

Вводный текст формы и индексы [current](../../../../requirements/current/README.md) / [sequences](../../../../sequence_diagrams/ui/README.md) синхронизированы с поставкой M1-9. Относительные ссылки перебазированы, у действующих сценариев указаны номера диаграмм 009…011. Остальные 10 REQ-UI и 21 AS-UI сохранены без изменений; REQ-UI-11 не переписан.

Редакционные пометки об ожидаемом approval заменены только в целевых документах на уже состоявшееся решение TASK-O-02. Нормативный состав C1…C8 сохранён. SHA-256 утверждённого текста UTF-8/LF с одним завершающим LF сверён: `ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`. Исторические requirements.md, terms_draft.md и sequences изменения не переписаны. Их ранние пометки о статусе текста читаются с учётом более позднего TASK-O-02.

### Проверки

- `python -` — документальный аудит: все 9 REQ, 18 AS-TERMS и 2 замены AS-UI сверены с инкрементом; остальные 10 REQ-UI и 21 AS-UI равны базе; нормативные таблицы и тела диаграмм сохранены. Проверены локальные ссылки и anchors, Markdown tables/fences, непрерывность ID, отсутствие полей переноса в новом чистовом документе, парность блоков PlantUML и ссылки REQ. PASS; новых или унаследованных битых ссылок в проверенных файлах не найдено.
- `python -` — отдельная проверка входа Owner и границ: неизменность задания и полей оркестратора, DP-R-01 ON_HOLD / `changes_reqs: []`, hash утверждённого текста и отсутствие чужих артефактов в diff. PASS.
- `git diff --check`, `git diff 0807cd05cedc457434149b4479ee4c6262a88dec --check`, `git diff --cached --check` — PASS.
- `git diff --cached --name-only` / `git diff --cached --stat` — только 9 файлов этой задачи: текущие UI-требования и сценарии, два индекса, три целевых PUML и TASK-A-04. Код, тесты, ADR, инкремент, планы, чужие задачи и процессные файлы в коммит не включены.

Проверки реализации, pytest, независимая приёмка, browser/live и внешние ссылки — NOT RUN: перенос документации не изменяет поведение. Исторические PASS не объявляются новым evidence. Рендер PlantUML — NOT RUN: `Get-Command java,plantuml -ErrorAction SilentlyContinue` не нашёл Java или PlantUML в PATH; выполнена структурная сверка и сравнение с исходными diagrams. Новых PNG нет; tracked PNG у этих target отсутствовали.

## Findings

Новых DP и багов нет. Ранее известное противоречие REQ-UI-11 и REQ-TERMS-04/D3 при позднем первичном current сохранено в [явной оговорке текущей редакции](../../../../requirements/current/ui/terms-of-use.md#отложенное-противоречие-dp-r-01). Owner выбрал C, DP-R-01 ON_HOLD, `changes_reqs: []`: transfer не выбирает A/B, не вводит нового оракула для нетронутой формы и не объявляет конфликт решённым.

## Риски

- Пустая нетронутая форма после чтения условий может остаться пустой и раскрытой при показанной сохранённой карте; срок возврата к DP-R-01 Owner не назначил. Действует [ранее принятый риск](../risks.md), без его расширения.
- DONE задачи transfer не равно ACCEPTED изменения, merge, независимой сверке Tester или закрытию DEBT-UI-001. Исходная рабочая копия содержит чужие локальные изменения; они не изменяются и не попадают в коммит Analyst. Push, PR и оркестратор не запускались.

Следующий шаг: Manager завершает сводку поставки TASK-M-03; после summary и transfer оркестратор создаёт TASK-O accept, решение о приёмке принимает Owner.
