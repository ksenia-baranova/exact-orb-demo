# Role skill drafts

Эта директория хранит versioned source drafts инструкций для ролей:

| Role | Skill |
|---|---|
| Change Manager | [exact-orb-change-manager](change-manager/SKILL.md) |
| Functional Analyst | [exact-orb-functional-analyst](functional-analyst/SKILL.md) |
| Developer | [exact-orb-developer](developer/SKILL.md) |
| Tester | [exact-orb-tester](tester/SKILL.md) |
| Reviewer | [exact-orb-reviewer](reviewer/SKILL.md) |

## Почему skills пока находятся здесь

Методология имеет статус DRAFT. Автоматически обнаруживаемые repo-scoped skills должны находиться в `.codex/skills/`,
но преждевременная активация сделает непроверенный процесс рабочей инструкцией для всех задач. Кроме того, у владельца
уже установлен user-scoped `exact-orb-functional-analyst`; одноимённую проектную копию нельзя вводить без явной миграции.

До принятия методологии skill запускается явной инструкцией:

```text
Прочитай docs/development_approach/skills/<role>/SKILL.md и выполни задачу в этой роли.
```

После успешного пробного change:

1. скорректировать role skills по фактическим отклонениям;
2. перенести принятые skills в `.codex/skills/<skill-name>/SKILL.md`;
3. синхронизировать или удалить конфликтующую user-scoped версию;
4. проверить явное `$skill-name` invocation;
5. добавить небольшой набор positive и negative invocation cases.

Skill не расширяет разрешения. Коммит своей задачи делается по правилам skill роли; ветки, push, PR, approval и merge — только по отдельному поручению.

## Процесс и артефакты

Все skills работают по [процессу работы над изменением](../process/change-process-v2.md): один запуск — одна задача `tasks/TASK-*.md` в папке `docs/project_management/changes/<change-id>/`. Роль меняет только status и resolution своей задачи и пишет только свои файлы; переходы change проверяет оркестратор. Шаблоны артефактов — в [artifacts/](../artifacts/README.md).

| Role | Виды задач | Основные артефакты |
|---|---|---|
| Change Manager | intake, apply_decisions, answer_dp по DP-M-*, escalation, summary, approve, accept | `change.md`, `roadmap.md`, `risks.md`, DP-M-* |
| Functional Analyst | analysis, apply_decisions, resolve_findings, answer_dp, transfer | `requirements.md`, `sequences/`, DP к owner'у |
| Developer | review, implement, bug_fix | `plans/implementation_plan.md`, `prompts/`, код и тесты |
| Tester | review, test | `plans/test_plan.md`, `tests/acceptance/`, `bugs/` |
| Reviewer | code_review: реализация, исправление, план рефакторинга | `bugs/`, DP |

Reviewer запускается сторонним агентом или агентом с пулом моделей, на модели, отличной от модели Developer, в отдельной сессии.
