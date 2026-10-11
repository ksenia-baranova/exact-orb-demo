# Developer artifact templates

Существенные вопросы и рекомендации Developer записываются в
[единый реестр решений](decision-register.md). Ролевые артефакты ссылаются на baseline и `DP-*` IDs без копирования содержания решений.

Для отдельного задания используй [шаблон промта Developer](developer-prompt.md): он содержит подробное описание
разделов, примеры, выбор подхода к разработке и заготовку для копирования.

Текущие состояния задания и версии артефакта собираются в `docs/project_management/change_plans/<change-id>/artifacts.md` по [process.md](../process.md). В ручном режиме достаточно ссылки на сводку, TaskId, короткого handoff, точной версии и evidence. При выборе сборщика добавляются устойчивые EventIds и зарегистрированные SourceRef / ArtifactPath по приложению А процесса; источники доступны до merge. Reviewer, критерий принятия и сроки ответа / эскалации задаются при назначении. Заключения, findings и результаты проверок относятся к своему предмету и версии; короткий handoff ссылается на подробные материалы.

## 1. Implementation Plan

```markdown
# Implementation Plan: <change>

**Owner:** Developer
**Requirements baseline:** `<исходные нормативные пути @ commit + требования/scenarios change @ commit>`
**Decision register baseline:** `<путь и commit>`
**Applicable decisions:** `<DP-* IDs>`
**State summary:** `docs/project_management/change_plans/<change-id>/artifacts.md` — <task ID and plan version>
**Technical assessment:** FEASIBLE / FEASIBLE WITH DECISIONS / NOT FEASIBLE
**Estimate:** <range and confidence>

## Manager summary
<Что можно реализовать, что мешает и как это влияет на delivery.>

## Technical dependencies and risks
- ...

## Required spikes
| Question | Method | Timebox | Output |
|---|---|---|---|
| ... | ... | ... | evidence / estimate / DP row update |

## Estimate basis
- Assumptions: ...
- Excluded work: ...
- Main uncertainty: ...

## Blocking decisions and register updates
- <DP-* ID — блокирующее влияние и какие поля строки дополнены; либо нет>

## Invariants and forbidden changes
- ...

## Work items

### DEV-NN. <Observable result>
- Requirements/scenarios: <ссылки, IDs и baseline>
- Промт: <путь к заданию этого work item>
- Подход к разработке: <тесты → реализация / реализация → тесты / существующее покрытие / документальные проверки>
- Основание выбора: <риск, готовность контракта, польза или избыточность отдельного TDD-цикла>
- Существующее покрытие и пробелы: <точные тесты/сценарии; что добавить либо почему достаточно>
- Components/files: ...
- Behavior change: ...
- Tests: <данные, expected result, REQ/AS и команды; ссылка на матрицу промта>
- Observability: ...
- Dependencies: ...
- Completion evidence: ...

## Integration order
- ...

## Risks and rollback
- ...

## Verification
- Target checks: ...
- Related checks: ...
- Full regression condition: ...
```

## 2. Development Finding

Используй развёрнутый [Finding template Analyst](functional-analyst.md#2-развёрнутый-finding), указывая:

- конкретный work item;
- код или тест, где обнаружена проблема;
- является ли вопрос semantic, technical, scope или test;
- какая независимая работа может продолжаться;
- требуется ли возврат Analyst, Manager или Technical Reviewer;
- строку `DP-*`, если finding требует выбора.

## 3. Development Handoff

```markdown
## Developer Handoff

**State summary:** `docs/project_management/change_plans/<change-id>/artifacts.md` — <task ID and handoff version>
**Implementation commit:** `<sha>`
**MainBaseline / CandidateSHA:** <база и кандидат после синхронизации; фактические проверки привязаны к версии>
**Обновление базы / конфликты:** <класс влияния, diff, решение конфликтов кода / tests / конфигурации; выполненные повторные checks или N/A>
**Decision register baseline:** `<путь и commit>`

### Implemented behavior
- ...

### Changed files and contracts
- ...

### Подход и покрытие
- <work item → промт → выбранный подход и причина его изменения, если менялся>
- <REQ/AS → тесты и сценарии; границы доказанного>

### Checks performed
- <проверенный commit и состояние дерева; команда — фактический результат и exit code>
- <для TDD: причина RED, затем результат GREEN; для остальных — предусмотренные проверки>

### Reproduction/setup
- ...

### Known limitations
- <FIND/DP IDs и ссылки>

### Open non-blocking findings
- ...

### Not verified
- ...
```

## 4. Промт Developer

[Подробный шаблон промта](developer-prompt.md) применяется к одному work item или одному проверяемому срезу.
Developer выбирает подход до исполнения: разработка через тесты нужна там, где ранний тест снижает риск;
для уже покрытых или документальных изменений достаточно обоснованных адресных проверок.
Шаблон содержит пояснение и пример каждого раздела, критерии избыточности TDD и блок для копирования.
