# Шаблоны артефактов процесса v2

Каждый артефакт изменения создаётся по своему шаблону. Skill'ы и `process/change-process-v2.md` ссылаются сюда, а не повторяют шаблоны у себя.

Все пути артефактов даны относительно папки изменения `docs/project_management/changes/<change-id>/`.

| Шаблон | Артефакт | Кто пишет | Когда |
| --- | --- | --- | --- |
| [change.md](change.md) | `change.md` | Manager | intake |
| [roadmap.md](roadmap.md) | `roadmap.md` | Manager | intake, summary |
| [task.md](task.md) | `tasks/TASK-<R>-<nn>.md` | оркестратор создаёт, исполнитель закрывает | каждый шаг |
| [dp.md](dp.md) | `dp/DP-<R>-<nn>.md` | роль, поднявшая вопрос; решение — Manager или Analyst | когда появился вопрос |
| [requirements.md](requirements.md) | `requirements.md`, `sequences/*.puml` | Analyst | analysis, apply_decisions, resolve_findings, transfer |
| [implementation-plan.md](implementation-plan.md) | `plans/implementation_plan.md` | Developer | review |
| [prompt.md](prompt.md) | `plans/prompts/<NN>-<тема>.md` | Developer | review |
| [test-plan.md](test-plan.md) | `plans/test_plan.md` | Tester | review, test |
| [bug.md](bug.md) | `bugs/BUG-<NNN>.md` | Tester, Reviewer, Manager | test, code_review, accept |
| [risks.md](risks.md) | `risks.md` | Manager | когда DP в ON_HOLD, баг в DEFERRED или owner принял риск |
| [debug-log.md](debug-log.md) | `debug_log.md` | оркестратор | после каждого запуска агента в ручном режиме |

Примеры в шаблонах иллюстрируют формат, а не требования проекта.
