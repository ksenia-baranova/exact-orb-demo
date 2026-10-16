# DEV-WHEEL-01 — проверить renderer boundary и плотность до реализации

Пользователь должен различать опубликованные points / R / ☌ на 360 px. Результат будущего шага — измеренный report, рекомендации DP и reviewed drawing rules; этот файл их ещё не создаёт.

**Редакция 2, TASK-D-002 / 2026-10-16:** неисполненная постановка синхронизирована с Analyst v3; прежняя версия TASK-D-001 сохранена @ `04be207627de1049deac2e069574e01b62536607`.
**InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`; `dev/ui-chart-wheel`, worktree по [индексу](../../developer_artifact.md). [Карточка DEV-WHEEL-01](../implementation_plan.md#dev-wheel-01-проверенная-граница-и-drawing-rules).
**Контракт:** исходные UI / AS-UI / HTTP / ADR @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1` и [Analyst requirements](../../analyst/requirements.md) / [scenarios](../../analyst/scenarios.md) v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`; прямые нормативные ссылки — в плане. REQ-WHEEL-01/02/05/06/10/11, AS-WHEEL-03/04/07…10/16/23/24/25, DP-O-010…014 @ [Manager](../../manager_artifact.md) / InputSHA; ADR-0029/0030/0032/0034/0040/0041.

## Условия запуска и scope

TASK-D-002 разрешает только документальную консультацию. Spike, создание / принятие ADR и technical sequence требуют отдельного назначения Manager / Owner, timebox и reviewers; сейчас их нет. Перед будущим запуском проверить Git / точные источники / критерии, записать назначение в план. Изменение baseline требует impact review, не автоматического reset / checkout.

Будущий scope: developer/evidence/ для изолированного scratch SVG/HTML / measurements, developer/sequence_diagrams/ui/ и проект drawing ADR в docs/requirements/decisions/ с проверенным актуальным номером — только согласно отдельному назначению. Scratch не импортируется production. Analyst-owned sequences / Manager / engine / API / golden / runtime не менять. Git publication отдельно.

## Метод и expected result

1. Проверить port из плана: controller владеет selection / expansion, wheel — geometry / SVG / canonical intents. Уточнить update / dispose / локальный typed failure, замена renderer не касается HTTP/session/cache. Существенную ownership boundary передать назначенному Technical Reviewer; не считать имена port утверждёнными.
2. Зафиксировать geometry по DP-O-014: d=(longitude-reference) mod 360, x=cx-r*cos(d), y=cy+r*sin(d), d в радианах; reference — опубликованный asc natal либо 0 cosmogram. Прямые cardinals: 0/90/180/270 → лево/низ/право/верх. Не вычислять sign/degree/minute/house/orb/category из geometry.
3. До объявления успеха согласовать collision / readability / hit criteria с Analyst / Tester. Sparse/F1/F3/F3-max сравнить при реальном шрифте и viewport 1440/768/360: default строго по долготам, только конфликтующее минимальное смещение, порядок через 0°, leader lines только при сдвиге, R / close angles / несколько ☌.
4. Для ☌ правило Owner уже принято: рядом «точный» / «рабочий», при выборе усиленный контур только символа, подпись сохраняется. Не заменять его общей рамкой или штрихом хорды. Измерить bounds символа, подписи, обводки и целей отдельно; palette / legend placement остаются техническими вариантами для review.
5. Timebox до 0,75 чд внутри графических 5–7. Остановиться при получении evidence либо по timebox; при неуспехе вернуть Owner конкретный counterexample / варианты предела, обновить estimate, не скрывать точки и не продлевать исследование молча.

**Подход:** документальные проверки + bounded browser spike после назначения; tests не выбирают отсутствующую продуктовую семантику. Existing F0/F1/projector data полезны, fake DOM не доказывает layout.

| REQ / AS | Контроль | Expected evidence |
|---|---|---|
| REQ-WHEEL-02 / AS-WHEEL-25 | Четыре стороны / фактический asc F1 / 0° seam | Прямые численные checks принятой конвенции, без prototype ref=100 |
| REQ-WHEEL-05/06 / AS-WHEEL-07…10 | Sparse, 5 R, 16 IDs, несколько подписанных ☌ | Критерий→actual, реальные bbox / screenshots; без молчаливого acceptance плотности |
| REQ-WHEEL-10 / AS-WHEEL-16/23 | 360/768/1440, pointer / keyboard | Достижимость canonical объектов, focus / hit bounds; указаны шрифт / scale / browser |
| REQ-WHEEL-01/11 / AS-WHEEL-24 | Alternate renderer / visible local failure | Проект проверяемого seam и sequence accepted DTO → HTML / SVG → исход |

**Проверки:** `git diff --check`, local links, структура новых PUML и фактический render с точной командой / версией инструмента; browser methods / measurements сохранить в checks. Не заявлять render или PASS по структуре / наличию SVG. Paid/network smoke не запускать.

**Завершение:** отдельный report с результатами / ограничениями, подписанный input в единственный DP, reviewed port / drawing ADR на точной версии и повторная оценка. Это не G3 само по себе. Продуктовый предел — Analyst/Owner, delivery/timebox — Manager; скрытая новая зависимость не допускается.
