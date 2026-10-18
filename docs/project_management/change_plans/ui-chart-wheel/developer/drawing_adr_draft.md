# DRAFT — Chart Renderer: граница, identity и drawing policy

**Автор:** Codex / Developer, TASK-D-003,18.10.2026. **Статус: DRAFT, не принятое архитектурное решение.** Реестр [ADR](../../../../requirements/decisions/README.md) на InputSHA 8fb2577 заканчивается0041. **0042 — кандидат номера**, не резервирование и не окончательный нормативный path; перепроверить перед публикацией ADR. Документ размещён только в Developer scope. [Исследование/evidence](task_d003_research_report.md), [Manager](../manager_artifact.md), CriteriaSHA f6f289c / Analyst2634b22 остаются входами review.

## Контекст и инварианты

Текущий HTML renderer / coordinator не реализует колесо. Изменение должно отобразить один подтверждённый ChartDTO и сохранить все HTML facts при ожидаемом локальном отказе SVG. Frontend преобразует опубликованную longitude в геометрию; не пересчитывает signs / houses / categories / orb / aspects / unknown-time stability. ADR-0029/0030/0032/0034/0040/0041 действуют. Общий render exception / HTTP recovery не подменяется успехом leaf wheel. Наблюдаемые selection, collapse, source/current semantics заданы Analyst v3, а не выбранной библиотекой.

Измеренный однокольцевой heuristic не удовлетворяет полной matrix: sparse360 визуально свободен, но centered Q44 перекрывается; F3/F3-max сохраняют наложения, fixed angle collisions и/или избыточность displacement. Это основание отказаться от данного кандидата, не от согласованного поведения.

## Предлагаемая техническая граница

ResultController владеет immutable accepted envelope, selection, normal-aspects expansion, houses expansion, current draft vs submitted snapshot и focus cause policy. HTML presenter и WheelPort читают один snapshot и canonical intent. Geometry не берётся из сокращённого textual readChartFacts, где longitude отсутствует.

```ts
// Проект внутренних presentation типов; не HTTP/API addition.
type Intent = { kind: "point"; id: string }
  | { kind: "aspect"; endpointIds: readonly [string, string]; type: string };
type DrawOutcome = { kind: "rendered"; instance: number; revision: number }
  | { kind: "svg_unavailable"; instance: number; revision: number; reason: string };
interface WheelInstance {
  update(snapshot: ReadonlyPresentationSnapshot): DrawOutcome | Promise<DrawOutcome>;
  dispose(): void; // idempotent; revoke listeners/callback ownership first
}
// Factory receives dedicated host + guarded canonical activation callback.
```

1. Accept B updates confirmed envelope; retire A imagery and publish HTML B / summary B before drawing B. Refuse stale callbacks by **instance + revision**, including font/async update settlement from an earlier B revision.
2. Factory/mount/update exceptions within SVG leaf become explicit svg_unavailable with recorded reason, empty retired image host and HTML B. Expected fault does not set coordinator requiresReconciliation. Unexpected HTML/controller failure still uses baseline fallback/safe-read.
3. Replace revokes generation before dispose; double dispose must be harmless. Disposal exception must be visible in technical outcome and must not restore stale A or prevent HTML B; production regression required. A late native callback cannot mutate a new controller state even if a detached node retained an old closure.
4. Renderers send canonical intents, never selection ownership / HTTP calls. Ordinary selection updates retained point controls; it does not remount the focused node. Canonical update/reconciliation may restore the same live key without scroll only for its allowed cause.

Alternatives: hardwire SVG into main render (simple, but leaf failure becomes global reconciliation); let wheel own selection/expansion (state diverges from HTML); separate proposed controller/port (recommended for review, more explicit seams). Isolated two-factory browser control supports the port idea; full update/async/dispose fault coverage is still required in implementation.

## Identity и accepted cause

Candidate aspect lookup: unordered endpoint IDs + published type. Keep original DTO orientation/order for facts and table; category/orb/identity changes are new facts of the same pair. Current default producer has unique pairs and stable orientation, but persisted validators do not enforce uniqueness. Duplicate/reversed duplicate lookup must report ambiguous, not choose first; observable ambiguity handling awaits review and creates no new API validation rule here.

Create internal acceptance event at the existing accept-owner: local monotonic acceptanceSeq, attemptId, cause, submitted snapshot, previous confirmed birth, actual accepted chart. Repeated publish / phase / resize does not reapply reset. Own committed changed-birth acceptance resets once; automatic current only reconciles selection against new DTO and preserves expansion/draft. Snapshot equality, including edit→revert, controls collapse.

**Unresolved, specific G03 case:** fresh matched recovery after lost POST is intent correspondence, not server-producer provenance. Two tabs submitting identical B give indistinguishable public current. Recommendation is once-per-pending-attempt target confirmation for presentation, with truthful wording; Analyst / Manager → Owner must confirm compatibility with “собственное построение”. No provenance API or unconditional GET reset is chosen.

## Drawing / focus / bounds

Working G/L/F/H definitions atf6f289c are measurement hypotheses accepted for research. Keep CSS frame / full M / true anchors separate from display origins; union component AABBs across normal/selected/focused, Euclidean gap≥2, fixed C0, containment in declared annulus/clip, cyclic order and leaders iff displacement. Size16/12 is effective em; ink, contour, focus and native H/Q44 are distinct. 1px full-prefix return is a local test, fractional witness can disprove tightness; no global optimum requirement. Recorded binary64 / ink-metric uncertainty is stated, not absorbed by anchor0.5 or a new gap epsilon.

Current fixed-ring16°/40° heuristic is **REJECTED AS A CANDIDATE**, and no new drawing algorithm is accepted here. Options for a further version: alternate declared movement domain / conflict lanes; independent angle label placement preserving anchors; nonoverlapping target geometry with canonical owner that retains visual default. Keep nonconflicting visual labels fixed; hit overlap alone does not expand C0. All new variants require fresh input metadata and actual independent verification; one model's failure is not global impossibility. No hidden IDs / shortened R / removed categories / reduced fonts / HTML-only fallback is approved.

Keyboard groups use preserved canonical point order / DTO aspect order, with accessible HTML background rows. Planet activation retains same live target and uses no programmatic focus/scroll. Current/reconcile replacement may restore same canonical key; removed-key fallback follows agreed H5 live initiator → edit → recovery → enabled birth field, with cause recorded. Collapse checks active field before hiding and keeps recovery controls outside hidden fields. Production must verify native pointer focus as well as keyboard, filtering/reveal/reset and timeout/restart gates; isolated browser tests do not establish those mounted contracts.

## Evidence / consequences / adoption conditions

[Technical report](task_d003_research_report.md) and [numeric matrix](evidence/task_d003_research/matrix_v2.md) contain exact sources / data / commands / failures. Sequences [001](sequence_diagrams/ui/001-result-renderer-lifecycle.puml) / [002](sequence_diagrams/ui/002-acceptance-selection-focus.puml) are technical proposals, linked to Analyst behavioral001/002/003 without rewriting them. Trace events in harness are permitted research evidence, not new production/server log contracts. Existing request/run correlation and ADR logging boundaries remain.

Consequences: an explicit controller/port adds a small lifecycle seam and enables renderer substitution; native-retained DOM requires keyed updates rather than unconditional replaceChildren; geometry and hit feasibility remain delivery risks. Proposed9–14chd full Developer forecast replaces prior8–12 only after Manager/Owner budgeting; D003 20–28 unchanged. No candidate SHA, gate approval or implementation is created by this draft.

Adoption requires TASK-R-001 on exact published package, TASK-T-004 evidence review, resolution of concrete semantic/budget consequences by their owners, a feasible drawing proposal, and Manager's separate G3. Recheck ADR number and final path then; do not copy this DRAFT into normative registry as accepted.
