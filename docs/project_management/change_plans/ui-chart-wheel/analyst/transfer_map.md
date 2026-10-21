# ui-chart-wheel — карта переноса требований и sequences

**Поручение Owner21.10:** «перенеси все требования и сиквенсы в таргет директорию - удали из change».
**Исполнитель:** Codex / Manager; прямое разрешение физического переноса и синхронизации уже полученных Owner-решений. Это не подпись от имени Analyst/Developer/Tester, не независимое review и не новое архитектурное решение.
**SourceSHA:** `883b6d3a47f7113e44ede73c9ad16b40f15bbdaf`, поверх сохранённых локальных Manager-правок21.10. Analyst baseline — `2736e2848c977ec4c770a9a4dec2a0d7c1b62a71`. Реализация / RetestedSHA9974195 / Testerf930c86 не меняются.
**Статус:** перенос выполнен; все13 source files удалены после проверки целей, повторных копий нет. Owner разрешил публикацию: TransferSHA — commit с [Manager§2.29](../manager_artifact.md#229-публикация-переноса-и-точный-вход-t008) и этой картой; точный remote SHA передаётся после push. Независимый T008 опубликован583d635 и включён72ab4e3: TRANSFER_REWORK_REQUIRED. R01/R02 и N01 исправлены локально21.10; ожидается адресный T009, исходный verdict сохранён. Manager — [§2.28](../manager_artifact.md#228-перенос-требований-и-sequences-по-прямому-поручению-owner).
**Машинная карта:** [transfer manifest](../manager/transfer_manifest.json), source SHA256 + target SHA256. Исходники доступны в Git по SourceSHA, второй действующей копии в change нет.

## Сохранённые IDs и применение дельты

- REQ-WHEEL-01…11 — полный отдельный [chart-wheel.md](../../../../requirements/current/ui/chart-wheel.md).
- MODIFY REQ-UI-01/03/04/05/06/08/09/10 и ADD REQ-UI-11 — [полный документ формы](../../../../requirements/current/ui/birth-form-and-facts.md); REQ-UI-02/07 сохранены без смысловой правки.
- AS-WHEEL-01…30 добавлены в [общие сценарии](../../../../requirements/current/ui/scenarios.md). AS-UI-22 заменён адресной дельтой, AS-UI-01…21/23 сохранены.
- Поздние явные Owner-решения заменяют прежние формулировки: passive SVG, без category words рядом с ☌, internal house rows вместо колонки, aspect reading / return / focus, first-five points как и houses/aspects, already_applied как fresh matched live target. Product source / точные цитаты остаются в [Manager§2.27](../manager_artifact.md#227-завершение-реализации-техдолг-и-подготовка-к-main) и подписанных Owner-записях.
- S1 считает всю исходную группу до любых фильтров/лимитов; исходные from/to/category/orb/order/факты и HTTP-контракт не меняются. Старый fixed-ring/column C0/minimality не переносится как oracle внутренних рядов.
- TEST-FIND-WHEEL-004 CLOSED; TEST-FIND-WHEEL-002 / precision остаются OPEN / INDETERMINATE в [DEBT-UI-004](../../../technical_debt.md#debt-ui-004). Сам перенос их не закрывает.

## Source → target

Все source paths в таблице относительны папке change и читаются в Git на SourceSHA.

| Исходник @ SourceSHA | Целевой путь | Действие / статус |
|---|---|---|
| `analyst/requirements.md` | [цель](../../../../requirements/current/ui/chart-wheel.md) | FULL REQ-WHEEL-01…11; DELTA REQ-UI в birth-form-and-facts.md |
| `analyst/scenarios.md` | [цель](../../../../requirements/current/ui/scenarios.md) | AS-WHEEL-01…30 + MODIFY AS-UI-22, прежние остальные AS-UI сохранены |
| `analyst/sequence_diagrams/ui/001-chart-presentation.puml` | [цель](../../../../sequence_diagrams/ui/001-chart-presentation.puml) | CURRENT behavior |
| `analyst/sequence_diagrams/ui/002-wheel-table-selection.puml` | [цель](../../../../sequence_diagrams/ui/002-wheel-table-selection.puml) | CURRENT behavior |
| `analyst/sequence_diagrams/ui/003-edit-and-recovery.puml` | [цель](../../../../sequence_diagrams/ui/003-edit-and-recovery.puml) | CURRENT behavior |
| `developer/sequence_diagrams/ui/001-result-renderer-lifecycle.puml` | [цель](../../../../sequence_diagrams/research/ui-chart-wheel/001-result-renderer-lifecycle.puml) | ARCHIVED, исходное содержание сохранено |
| `developer/sequence_diagrams/ui/002-acceptance-selection-focus.puml` | [цель](../../../../sequence_diagrams/research/ui-chart-wheel/002-acceptance-selection-focus.puml) | ARCHIVED, исходное содержание сохранено |
| `developer/sequence_diagrams/ui/003-passive-copy-install.puml` | [цель](../../../../sequence_diagrams/ui/technical/003-passive-copy-install.puml) | IMPLEMENTED technical view; ADR approval не создаётся |
| `developer/sequence_diagrams/ui/004-column-layout-revision.puml` | [цель](../../../../sequence_diagrams/research/ui-chart-wheel/004-column-layout-revision.puml) | ARCHIVED, исходное содержание сохранено |
| `developer/sequence_diagrams/ui/005-accepted-once-editor.puml` | [цель](../../../../sequence_diagrams/ui/technical/005-accepted-once-editor.puml) | IMPLEMENTED technical view; ADR approval не создаётся |
| `developer/sequence_diagrams/ui/006-aspect-reading-mode.puml` | [цель](../../../../sequence_diagrams/ui/technical/006-aspect-reading-mode.puml) | IMPLEMENTED technical view; ADR approval не создаётся |
| `developer/sequence_diagrams/ui/007-internal-house-rows.puml` | [цель](../../../../sequence_diagrams/ui/technical/007-internal-house-rows.puml) | IMPLEMENTED technical view; ADR approval не создаётся |
| `developer/sequence_diagrams/ui/008-viewport-legend-vectors.puml` | [цель](../../../../sequence_diagrams/ui/technical/008-viewport-legend-vectors.puml) | IMPLEMENTED technical view; ADR approval не создаётся |

## История и проверка

Исторические prompts, авторские отчёты, raw evidence и manifests не переписываются. Их source paths разрешаются на зафиксированных source commits. Актуальные ролевые индексы и нормативные ссылки ведут в общие каталоги; ссылки на неизменённые исторические документы с удалёнными рабочими зависимостями ведут на Git snapshot, где исходники существуют.

Документальная проверка подтверждает наличие всех целей, стабильные22 REQ / 53 AS, отсутствие source-копий, корректность текущих ссылок/anchors и структуры PUML. Проверка синтаксиса не заменяет PlantUML render; локальный renderer отсутствует. Продуктовые tests / browser replay заново не запускались, независимый T008 вернул два замечания; их исправления ожидают адресного T009. Точные текущие hashes — manifest / Manager checks.

## Исправления по T008,21.10

R01: AS-WHEEL-09 F2→F3 с пятью R через0° и sparse positive control; R02: Manager navigation→tracked общий UI README. N01: AS28→F5/AS23/AS30. Код/исходные facts и13 source removals сохранены. D008 добавил proposed ADR/component document, пять technical PUML не менялись. Источник review —583d635; текущая версия локальна, independent follow-up T009 ещё не выполнен.

## Уточнение Owner§2.31

Пассивность — граница только текущего M1-8. Активное колесо остаётся будущей отдельной фичей без назначенных срока/оценки. ADR-0042 принят для текущего этапа; full REQ/AS IDs и действующее HTML-only поведение не изменены. README/roadmap/current/UI синхронизированы. Разрешена только публикация всего подготовленного пакета в change.
