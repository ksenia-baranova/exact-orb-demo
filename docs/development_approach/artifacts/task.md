# Шаблон: задача

Файл: `docs/project_management/changes/<change-id>/tasks/TASK-<R>-<nn>.md`, где R — O, M, A, D, T или R. Создаёт оркестратор: поля до status и раздел «Задание». Исполнитель меняет только status, resolution, свои поля и разделы «Результат», «Findings», «Риски».

Правила:

- Из DONE задача не возвращается. Доработка — новая задача.
- resolution ставится только вместе с DONE.
- needs_decision без raised_dp и has_bugs без raised_bugs — ошибка.
- «Задание» оркестратор берёт из описания kind в процессе: что сделать и когда готово.
- В ручном режиме файл задачи создаёт `scripts/orchestrator.py next`, а не человек.

## Заготовка

```markdown
---
id: TASK-<R>-<nn>
change: <CH-id>
role: developer            # owner | manager | analyst | developer | tester | reviewer
kind: review               # intake | analysis | answer_dp | apply_decisions | resolve_findings | review | escalation | summary | approve | implement | test | code_review | bug_fix | transfer | accept
gate: ALIGNMENT            # статус изменения, в котором создана
cycle: 1
inputs: [requirements.md, DP-A-02]
origin: null               # оркестратор: задача, которую эта продолжает (apply_decisions, исправление, ответ на DP)
agent: <агент>             # заполняет оркестратор при запуске
model: <модель>            # заполняет оркестратор при запуске
status: NEW                # NEW | IN_PROGRESS | DONE
resolution: null           # done | needs_decision | has_bugs | cancelled
raised_dp: []
raised_bugs: []
changed_reqs: []           # Analyst
reviewed_reqs: []          # Developer и Tester в review
commit: null               # Developer в implement и bug_fix, Tester в test, Reviewer в code_review
estimate: null             # { чч: 40, мч: 10, confidence: medium }; чч — у человека, мч — у агента
choice: null               # только escalation: accept_risk | reduce_scope | cancel; пишет Manager со слов owner'а
---
## Задание
<что сделать и когда готово; пишет оркестратор>

## Результат
<что сделано; команды и фактический результат; что не проверялось>

## Findings
<что найдено по ходу; вопросы оформлены как DP>

## Риски
<что может пойти не так и почему>
```
