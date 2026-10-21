# Chart Renderer: обязанности компонентов

Документальный пакет TASK-D-008, 21.10.2026, Codex / Developer.
Описывает реализацию @ `99741958b4bbee8884505920f4a02f2f19dea3e3`,
неизменную на InputSHA `72ab4e30321884ddabe4205505216a7595d8bfeb`.
Принятое для текущего пассивного M1-8 архитектурное решение — [ADR-0042](../decisions/0042-passive-chart-renderer.md);
Owner21.10 / Manager§2.31. Активное колесо — отдельная будущая фича.

| Компонент | Ответственность | Граница |
|---|---|---|
| `session.mjs` | HTTP/recovery, immutable submitted attempt, accepted view/seq/cause | Не управляет SVG/раскладкой; current GET не считается авторством POST |
| `main.mjs` | Композиция страницы, editor policy once, final width/page mode, подключение facts | Не пересчитывает доменные факты; resize не создаёт принятие |
| `chart_state.mjs` | Полный source S1 index, canonical point/aspect selection, независимые disclosures | Ключ включает endpoints+type; неоднозначность не устраняется фильтром или first-match |
| `facts.mjs` | Retained HTML, source tables/summary, renderer snapshot, aspect focus/return, resize/font lifecycle | Передаёт одну принятую карту; ошибка leaf сохраняет HTML; source DTO не изменяется |
| `result_controller.mjs` | Private image host, revoke/revision lease, immutable copy, passive validation и synchronous clone/install | Leaf не получает live image host; ошибки leaf и trusted owner различаются |
| `wheel_svg.mjs` | Пассивное SVG текущей surface, native измерение, cache и publish | Нет HTTP/selection handlers/tab controls, доменного пересчёта или записи в установленную копию |
| `wheel_layout.mjs` | Source-longitude geometry, native bounds, source house rows, markers/routing | Не выводит принадлежность дому; capacity failure типизирован, полный HTML остаётся доступен |

Порядок замены: revoke → remove imagery → accepted state/index/HTML → guarded
dispose → draw → validate/clone/current guard/install. Старый async publish
отклоняется. Текущий update rejection локален; retired rejection не очищает B.
`close()` отзывает surface и listeners, dispose вызывается идемпотентно.

Наблюдаемый контракт: [wheel](../current/ui/chart-wheel.md),
[UI](../current/ui/birth-form-and-facts.md), [сценарии](../current/ui/scenarios.md).
Потоки и архив прошлых вариантов: [UI sequences](../../sequence_diagrams/ui/README.md).
Оставшиеся ограничения: [общий реестр долга](../../project_management/technical_debt.md).
