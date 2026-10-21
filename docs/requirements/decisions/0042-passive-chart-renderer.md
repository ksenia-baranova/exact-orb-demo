# ADR-0042. Пассивный Chart Renderer и изоляция публикации SVG

Дата: 2026-10-21.

**Статус: принято Owner 21.10.2026 для текущего пассивного этапа M1-8.**
Автор: Codex / Developer, текущий сеанс после явной смены роли. InputSHA —
`72ab4e30321884ddabe4205505216a7595d8bfeb`; реализация —
`99741958b4bbee8884505920f4a02f2f19dea3e3`. Номер 0042 свободен в проверенном
реестре и опубликованном main. Источник текущего решения — ответ Owner на
предложение принять ADR: «Пассивное кольцо только сейчас потом сделаем активным
это фича». Manager зарегистрировал выбор с этим ограничением области.
Приёмка runtime и прежнее R001 r2 не выдаются за R002 approval.

## Контекст и источники

Колесо показывает опубликованный ChartDTO вместе с доступными HTML-таблицами.
После изменения принятой карты или presentation revision старая асинхронная
отрисовка не должна менять новый результат. Ошибка SVG должна сохранять HTML
той же карты. Управление выбором находится в HTML; SVG пассивен.

Пассивность относится к текущему M1-8. **Активное колесо — будущая фича**,
а не отменённая возможность и не дефект этого этапа. Она потребует отдельного
change с наблюдаемыми pointer/keyboard/focus/hit-target правилами и пересмотром
затронутых частей ADR. Срок, бюджет и старт будущей фичи сейчас не назначаются.

Основания: [REQ-WHEEL-01…11](../current/ui/chart-wheel.md),
[форма и факты](../current/ui/birth-form-and-facts.md),
[AS-WHEEL-09/23/24/28/30](../current/ui/scenarios.md),
[DP-O-008/010…013 и Owner-решения](../../project_management/change_plans/ui-chart-wheel/manager_artifact.md#3-единый-реестр-dp).
Последняя drawing-редакция — [внутренние ряды по опубликованным домам](../../project_management/change_plans/ui-chart-wheel/developer/owner_decision_house_rows_2026-10-20.md).
История предложения и отвергнутых вариантов остаётся в Git и
[Developer draft](../../project_management/change_plans/ui-chart-wheel/developer/drawing_adr_column_draft.md).

ADR дополняет UI-представление; не заменяет ADR-0040/0041 и не меняет HTTP,
engine, ChartDTO, persisted artifact, cache или числовой расчёт.

## Принятое решение текущего этапа

1. `session.mjs` остаётся единственным владельцем HTTP, recovery и acceptance.
   Принятие выпускает монотонный `acceptance.seq`, cause, неизменяемую попытку
   и submitted intent. Publish/resize/font/selection не создают принятие.
   `own_committed`, `matched_recovery` и `already_applied_target_confirmed`
   различаются: GET подтверждает живую цель, но не авторство POST.
   Changed-birth reset применяется один раз на принятую цель; collapse только
   при совпадении текущего draft со submitted. Failed/stale/different GET и
   superseded не подтверждают цель.
2. `chart_state.mjs` строит индекс по **всему** исходному списку аспектов до
   фильтров/first-five: ключ — неупорядоченные endpoint IDs плюс source type.
   Несколько строк с ключом дают неоднозначную группу S1; first-match не
   используется. Вывод сохраняет source from/to/category/orb/order. `facts.mjs`
   владеет retained HTML, выбором, раскрытиями и явными focus intents.
3. `result_controller.mjs` владеет установленным image host и revision lease.
   Порядок `present`: revoke старой lease → убрать прежнюю картинку →
   применить принятие/индекс/HTML/summary → guarded dispose прежнего экземпляра
   при замене → guarded draw. Revision меняется и при сохранённом leaf;
   acceptance token при этом не создаётся.
4. Leaf получает глубоко скопированный immutable snapshot и подключённую
   measurement surface текущей revision. Его внутренний протокол:
   `update(snapshot, publish, currentSurface): void | Promise<void>` и
   `dispose(): void`. Factory синхронна. Controller нормализует update через
   `Promise.resolve`; promise factory этим протоколом не поддерживается.
   Surface отсоединяется при revoke; доступ к live image host leaf не передаётся.
5. `publish(svg)` проверяет закрытый набор passive tags/attributes/values,
   клонирует дерево, проверяет копию и актуальность lease непосредственно
   перед синхронной установкой без `await`. Late publish отклоняется. Старые
   references могут менять только прежнюю поверхность, не live-копию.
   Запрещены script/event/focus, внешние ссылки, произвольные CSS/ID/style.
   Это внутренний протокол собственного renderer, не security sandbox для
   недоверенного JavaScript и не универсальный SVG sanitizer.
6. Sync throw factory/update и async rejection update текущего leaf дают
   локальный `svg_unavailable`; HTML и данные сохраняются. Dispose fault не
   блокирует новый HTML. Ошибка доверенного HTML/controller слоя остаётся в
   действующем safe-read пути. Retired rejection не удаляет новую картинку.
   Close идемпотентен. Технические события доступны через инъецируемый
   `onEvent` с no-op по умолчанию; новый production logger не вводится.
7. `wheel_layout.mjs` преобразует source longitude в координаты, не вычисляет
   заново дома, знаки, аспекты, категории и орбисы. Натальные glyphs размещаются
   внутренними рядами внутри **опубликованного** `points[].house`; cosmogram
   не получает дома. Сохраняются source anchors и endpoints, все ID/R и
   native text/vector bounds. Колонка, её point leaders и старое требование
   неподвижности всех неконфликтных point labels заменены решением Owner20.10.
   Capacity failure — typed local error с доступным полным HTML; произвольная
   плотность не гарантируется. Числа solver являются параметрами реализации,
   а не новыми продуктовыми обещаниями.
8. Point selection меняет подсветку и таблицу без focus/scroll. Явный вход в
   aspect reading показывает endpoints и их source houses, фокусирует область
   карты; Escape/возврат восстанавливает disclosures и живой origin control.
   Full-source S1 сохраняется до display subset. Геометрический cache включает
   полный DTO, width, font revision и aspect key; point-only selection его
   не перестраивает. Main определяет конечный page mode/width до draw.

## Альтернативы и последствия

| Вариант | Причина выбора / отказа |
|---|---|
| Revision-local surface + copy/install | Выбранная реализация: native измерения и один владелец live DOM; дополнительная память и копирование SVG |
| Live host с token только после await | Старый leaf успевает записать в DOM до проверки settlement |
| Только AbortSignal | Кооперативная отмена не отзывает сохранённый DOM reference |
| Закрытые value frames D005 | Возможная более широкая система, потребовавшая бы отдельного frame writer/measurement protocol |
| Активное SVG | Более дорогая геометрия targets/focus; Owner выбрал HTML-only selection |

Проверенные технические потоки: [copy/install](../../sequence_diagrams/ui/technical/003-passive-copy-install.puml),
[accepted once](../../sequence_diagrams/ui/technical/005-accepted-once-editor.puml),
[aspect reading](../../sequence_diagrams/ui/technical/006-aspect-reading-mode.puml),
[internal rows](../../sequence_diagrams/ui/technical/007-internal-house-rows.puml),
[viewport/legend/vectors](../../sequence_diagrams/ui/technical/008-viewport-legend-vectors.puml).
Обязанности — [компонентный документ](../component_responsibilities/exact-orb_chart_renderer.md).

## Проверка, ограничения и принятие

Существующее покрытие: `tests/ui/chart_selection.test.mjs`,
`wheel_layout.test.mjs`, `accepted_chart.test.mjs`, `aspect_view.test.mjs`,
`facts.test.mjs`, `owner_feedback.test.mjs`. Фактические результаты текущего
документального прохода и независимые исходники —
[D008 handoff](../../project_management/change_plans/ui-chart-wheel/developer/task_d008_handoff.md).

Независимый runtime/retest относится к RetestedSHA9974195; это не новый запуск
на будущем merge commit. [DEBT-UI-002/003/004](../../project_management/technical_debt.md)
сохраняют ограничения UX и плотности/точности; TEST-FIND-WHEEL-002 остаётся OPEN,
precision INDETERMINATE, TEST-FIND-WHEEL-004 CLOSED. Универсальный geometry PASS
и независимое architecture approval не заявлены.

Owner подтвердил текущую пассивную границу с явным продолжением отдельной
активной фичей. Источник и разрешённая публикация только в change зафиксированы
в [Manager §2.31](../../project_management/change_plans/ui-chart-wheel/manager_artifact.md#231-текущий-пассивный-этап-будущая-активная-фича-и-публикация).
Независимое R002 approval не получено; адресная сверка документации T009
остаётся отдельным обязательством и этим решением не объявляется выполненной.
