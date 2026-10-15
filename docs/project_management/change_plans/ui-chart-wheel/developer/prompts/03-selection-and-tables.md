# DEV-WHEEL-03 — связать выбор колеса и HTML

Пользователь выбирает объект или опубликованный аспект и видит соответствующие факты той же карты. Результат — один согласованный локальный выбор и предсказуемое раскрытие таблиц без HTTP.

**План:** [DEV-WHEEL-03](../implementation_plan.md#dev-wheel-03-согласованный-выбор-колеса-и-таблиц), TASK-D-001 / consultation v1. Ветка `dev/ui-chart-wheel`; worktree в [индексе](../../developer_artifact.md); исходный SHA `2b846077b317e33dd892565419942c4db8517b1e`.
**Контракт:** нормативные UI/AS-UI/HTTP @ `535551026af6eedaf2a0aa5c0daa96fa94655ec1` + Analyst [requirements](../../analyst/requirements.md)/[scenarios](../../analyst/scenarios.md) v1 @ `683bdd0c1f5a0e65735f4e48127d408300ec697c` и более поздний [DP registry](../../manager_artifact.md) @ InputSHA. REQ-WHEEL-04/07/08/10/11, REQ-UI-04/06/10; AS-WHEEL-04/07/11…15/23/24; DP-O-008/010/012/013. Исходные ADR и drawing ADR наследуются по плану.

## Готовность / scope

Перед кодом требуются DEV-WHEEL-02 и G3, утверждённый Analyst SHA с устранённым DEV-FIND-WHEEL-001 и окончательная семантика DP-O-013. Зафиксировать точные версии в плане; не придумывать aspect toggle/same-current policy. Отдельная кнопка «Снять выделение» уже отклонена Owner — не добавлять её по старой sequence.

Разрешены локальный result/selection port в ui/*.mjs по ADR, facts.mjs/styles.css, новый tests/ui/selection.test.mjs и точечные assertions в facts.test.mjs, листовой DOM port. Не менять transport/session/calculation, canonical data/IDs, существующий порядок API aspects. Для aspect key использовать ссылку на запись принятого DTO в рамках identity; не предполагать уникальность только пары, если в accepted port это не доказано. Новая схема API для ключа не нужна. Git-публикация не поручена.

**Подход:** сначала тесты state transitions, затем реализация. Existing facts.test.mjs покрывает immutable DTO / порядок / identity removal, но не selection. Mounted checks используют реальный controller и renderer, fake только DOM/network seams; label parsing вместо IDs не допускается.

| REQ / AS | Действие / данные | Expected result / контроль |
|---|---|---|
| REQ-WHEEL-07 / AS-WHEEL-11 | Выбрать Moon → Sun → Sun | Аспекты Moon → все аспекты Sun → первые 5 общего списка; single selection, повтор снимает; опубликованный порядок сохраняется |
| REQ-WHEEL-07 / AS-WHEEL-11/12 | Выбрать point row и glyph | Одна и та же точка; все её опубликованные аспекты сразу, без лимита 5; строка доступна по утверждённой композиции |
| REQ-WHEEL-04/07 / AS-WHEEL-04/11 | Выбрать background с endpoint angle | Оба опубликованных конца выделены; линия / ☌ отсутствуют; exact/working positive control показывает графику |
| REQ-WHEEL-08 / AS-WHEEL-13/14 | Aspect toggle, same identity current, changed current | Результат только из обновлённого DP-O-013; если не определён — вернуть Analyst до кода |
| REQ-WHEEL-08/09 / AS-WHEEL-14/16 | Новый accepted build с изменённым birth; resize | Новый build сбрасывает выбор/раскрытие до 5/5; resize сохраняет выбор/раскрытие. Простое редактирование не является new chart |
| REQ-WHEEL-07/10 / AS-WHEEL-12/23 | «Показать все» каждой таблицы; keyboard activation | Аспекты / дома раскрываются независимо; no auto scroll/focus при выборе, видимый focus; без дополнительной кнопки снятия |
| REQ-WHEEL-11 / AS-WHEEL-11…14 | Выбор/снятие/resize | Нет HTTP; позитивный контроль явного валидного build создаёт один POST через реальный coordinator |

**Observability:** initiator (wheel/row/keyboard), identity и canonical selected key → controller → оба представления; логический порядок доказан assertions/событиями листового порта, не sleep. Пересоздание rows при stale/update не должно незаметно сбрасывать focus/selection в нарушение утверждённой политики.

**Команды:** `node --test tests/ui/selection.test.mjs tests/ui/facts.test.mjs`; затем `node --test tests/ui/*.test.mjs`. Добавить browser evidence pointer/keyboard/no-hover на 360/768/1440: DOM port layout не проверяет. Полный pytest — в финальном срезе до G4.

**Завершение:** каждый approved REQ/AS имеет воспроизводимый check, results привязаны к фактической версии и scope; невыбранная продуктовая ветвь возвращена Analyst/Owner. Нет посторонних API/engine изменений и заявления независимого PASS. Сохранить несвязанные файлы; commit/push отдельно.
