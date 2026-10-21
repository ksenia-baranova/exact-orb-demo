# Исполняемый пакет05 — полное пассивное колесо с условной колонкой

**DRAFT / Codex, Developer,19.10.2026. Подготовлен, не запущен.** Пользователь должен получить одно согласованное представление accepted карты: полный SVG и живые HTML facts/selection, с читаемой колонкой при скученности и локальным отказом изображения. [Work items FW01…06 / оценка](../full_wheel_implementation_plan.md), [drawing/boundary rules](../column_renderer_design_v1.md), [DRAFT ADR](../drawing_adr_column_draft.md).

## Паспорт и обязательная сверка перед STARTED

Change ui-chart-wheel; существующий checkout `C:/Users/KateUser/.codex/worktrees/ui-chart-wheel-dev/exact-orb-recovered`, branch dev/ui-chart-wheel. План подготовлен на07bb56ba5d49ec76de64df41ad80d175fbe90a2d. Fetch опубликованного change и проверка HEAD/index/изменений обязательны; не reset/clean/force, несвязанные изменения и staged entries сохранить. Чужие роли читать только через опубликованный Git.

Нормативная часть: UI requirements/scenarios и HTTP §7.2 @ MainBaseline535551026af6eedaf2a0aa5c0daa96fa94655ec1, ADR-0029/0030/0032/0034/0040/0041. Change baseline: [requirements](../../analyst/requirements.md)/[scenarios](../../analyst/scenarios.md)@2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 и поздние прямые Owner решения в [source](../owner_decision_drawing_2026-10-19.md); [Manager DP/gates](../../manager_artifact.md). Этот исторический SHA не подменяет новый TargetContractSHA. Перед исполнением Manager должен закрепить конкретные approved contract/technical versions, Owner scope/40–64ч/≤8 рабочих дней и применимый G3. Если этого нет — передать зависимость, не начинать код по одному этому файлу. Независимая уже разрешённая работа продолжается в своём scope.

## Разрешённые будущие области

После допуска: `src/exact_orb/http_api/ui/{main,session,facts,styles,index}` в их фактических расширениях; новые реально используемые UI modules `chart_state.mjs`, `result_controller.mjs`, `wheel_layout.mjs`, `wheel_svg.mjs`; `tests/ui/*.test.mjs` и узкие helpers/новые controls; `tests/http_api/test_ui_delivery.py` для новых module-resource expectations. Собственные Developer plan/checks/ADR/sequences/handoff по факту. Новые файлы сейчас отсутствуют, не заводить интерфейсы на будущее или no-op renderer. App routing/package-data уже доставляют ui/*.mjs; менять HTTP/engine/projector/golden/deps/серверные logging policies не требуется.

## FW-01 — state и HTML

Выполнить [D006 CH01…05](../task_d006_controller_html_plan.md) в пределах14–22ч уже включённых в полный план. Начать source index/selection и retained HTML. TDD на full-DТО cardinality0/1/>1, unique reverse/type, source rows/direction/order, absent/ambiguous reconcile и once accepted event; сначала проверить existing facts/session/recovery coverage. Accepted-cause/attempt/submitted snapshot не выводить из одного source=build или HTTP method. A006 already_applied не заменять выдуманной policy. Новые HTML controls остаются live при select/filter/reveal/resize; planet action без focus()/scroll, H5 и recovery доступны. Существующие детали глобального hide/reset обновить только по новому approved contract.

## FW-02 — полный SVG

Чистая layout-функция получает только published facts + measured geometry и выдаёт координаты/owners либо конкретный layout failure. Рендерить12 signs, все source points/R, natal12 cusps/5 angles, exact/working и все7 типов/☌, background endpoints без линии, S1 suppression только ambiguous group. Сначала sensitive geometry controls на2px equality/below, diagonal, forbidden/clip, fractional coordinates,0° cyclic order/frozen labels/несколько групп и действительно совпадающие долготы. Не вычислять signs/degrees/houses/orbs/DSC/IC/stability. Затем настоящий SVG и native measurements для16/12 effective em, fonts, contour и paint order.

Column C0/row objective/new domain должны совпасть с принятыми критериями, не молча заменить old annular return. Aux test1px должен проверять допустимость всего prefix; конечная точка сама по себе не доказательство. Regression для shared route: ранний Sun/Moon20,5px segment должен быть отвергнут, crossing и endpoint touch должны остаться допустимыми. Никакого уменьшения em/gap, удаления R/IDs, дедупликации source rows или изменения golden ради результата. Research scripts — источник witnesses, не готовая production библиотека.

## FW-03 — boundary

TDD с deferred promises и реальным DOM: revoke→removeA→HTMLB→guarded dispose→guarded draw; factory/sync/async failure, same-instance revision, stale write до/после settlement, retained original root mutation, current late publish, failed lease revoke, reentrant clone invalidation, idempotent close и positive alternate renderer. Live host закрыт у controller, copy root не возвращать leaf. Surface держать до revoke; deep readonly snapshot не является shared mutable state. Закрытый production tag/attr/value whitelist должен исключать внешние IDs/href/url/on*/interactive/focus/positioning. Простой token после await недостаточен.

## FW-04 / FW-05 / FW-06 — wiring, проверки, передача

Собрать реальные main/session/form/controller/HTML/leaf. Мокать только transport/clock и листовой fault. На accepted B сразу доступны B facts/summary; stale A/fault не запускает HTTP и не удерживает старую картинку. Empty/unavailable убирает imagery/selection по approved contract, draft и existing recovery gates не выдумываются заново. Width/font/selection создают presentation revision без нового acceptanceSeq. Текст категории убран из SVG-меток; HTML published category/orb остаются.

Команды по этапам — [план §5](../full_wheel_implementation_plan.md#5-существующее-покрытие-пробелы-и-команды): targeted Node→related/full UI; delivery+module boundaries→full pytest; реальный browser1440/768/360 с pointer/keyboard/live-focus/44px coordinate hit/resize/font/selection/background/S1 и typed local SVG error. Записать exact baseline/CandidateSHA/команды/actual/NOT RUN. Paid/network smoke, новые quality gates, PR/commit/push/merge без отдельного поручения не выполнять.

Готовность результата: approved scope реализован, обязательные Developer checks выполнены на фактической версии, источник/переход/исход восстанавливаются из ordered browser/integration evidence и существующей HTTP correlation; нормальные данные B видимы отдельно от local SVG failure. Сообщить все ограничения и valid counterexamples. Reviewer/Tester acceptance и gates не объявлять за них. При semantic gap — Analyst, architecture — technical owner, scope/срок/40–64ч риск — Manager до превышения. Handoff с точным опубликованным SHA после разрешённой публикации; локальная готовность не равна READY_FOR_REVIEW в Manager.
