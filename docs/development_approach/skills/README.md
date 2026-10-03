# Role skill drafts

Эта директория хранит versioned source drafts инструкций для ролей:

| Role | Skill |
|---|---|
| Change Manager | [exact-orb-change-manager](change-manager/SKILL.md) |
| Functional Analyst | [exact-orb-functional-analyst](functional-analyst/SKILL.md) |
| Developer | [exact-orb-developer](developer/SKILL.md) |
| Tester | [exact-orb-tester](tester/SKILL.md) |

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

Skill не расширяет разрешения: commit, push, PR, review reply, approval и merge выполняются только по отдельному поручению.
