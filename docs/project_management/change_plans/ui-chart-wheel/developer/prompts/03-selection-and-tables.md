# DEV-WHEEL-03 — единый выбор и независимое раскрытие таблиц

Пользователь связывает колесо с HTML и получает факты именно выбранного объекта / пары. Результат будущего шага — локальные states none / point / aspect, согласованный 5/all/one/filter и перенос допустимого выбора на новый DTO.

**Редакция 2 / TASK-D-002, 2026-10-16:** неисполненные постановки v1 сохранены @ `04be207627de1049deac2e069574e01b62536607`. **InputSHA:** `543b7ec726ee96c951dc0abbf1067ca6ad47a1ba`, `dev/ui-chart-wheel`, worktree в [индексе](../../developer_artifact.md). [DEV-WHEEL-03](../implementation_plan.md#dev-wheel-03-согласованный-выбор-колеса-и-таблиц).
**Контракт:** нормативный baseline `535551026af6eedaf2a0aa5c0daa96fa94655ec1` + [requirements](../../analyst/requirements.md)/[scenarios](../../analyst/scenarios.md) v3 @ `2634b224894b1046113557bfe241f0a5f2d46f8c`, ссылки в плане. REQ-WHEEL-04/07/08/09/10/11, REQ-UI-04/05/06/10; AS-WHEEL-04/07/11…15/23/26…30 и MODIFY AS-UI-22. DP-O-008/010/012/013 @ Manager/InputSHA, исходные ADR и отдельно принятый drawing ADR по плану.

## Вход / границы

Нужны результат DEV-WHEEL-02, approved port / технические criteria и G3; записать точные утверждённые SHA в план. Toggle / preserve current / один аспект уже выбраны Owner: не возвращать их как открытые вопросы. До разрешения этот промт не исполняется.

Будущий scope: local result/selection ui modules по port, facts/styles, новый tests/ui/selection.test.mjs, точечные facts.test.mjs / leaf DOM API. Coordinator / transport / API / engine не менять. Candidate aspect key `(from,to,type)` утвердить после проверки public canonical order / uniqueness; category/orb/row index/identity не являются ключом сохранения. Данные при каждом accepted update заново разрешаются в новом DTO, общей mutable ссылки на старую карту нет.

**Подход:** тесты → implementation переходов; реальные controller/renderer, fake только DOM/network. Переиспользовать immutable / canonical order assertions existing facts tests; новое поведение не доказано прежним PASS.

| REQ / AS | Действие / данные | Expected result / контроль |
|---|---|---|
| REQ-WHEEL-07/08 / AS-WHEEL-11/13/27 | Moon → Sun → Sun; south_node с нулём аспектов | Один point; все его from/to в DTO order, включая background / angle endpoints; повтор → первые 5 общего списка; пустой фильтр не означает пустую карту |
| REQ-WHEEL-07 / AS-WHEEL-28 | Moon filter → related moon→asc либо unrelated sun→mc с колеса | Point/filter снят, таблица одна строка, только её graphic / два конца; любой следующий point заменяет аспект |
| REQ-WHEEL-04/07 / AS-WHEEL-04/07/11/28 | Выбрать background через HTML | Одна строка / два конца; ни линии, ни ☌, остальные аспекты скрыты; positive exact/working control показывает графику |
| REQ-WHEEL-08 / AS-WHEEL-29 | Выбрать / повторить аспект при normal expansion=5 и all | None, общий список с прежним раскрытием, без возврата point filter; houses независимы; keyboard эквивалентен pointer |
| REQ-WHEEL-08 / AS-WHEEL-30 | Current A → B с другой identity / orb / category=background | Существующий key сохраняется с новыми фактами; нет старой линии/координат/row index; expansion сохранён |
| REQ-WHEEL-08 / AS-WHEEL-30 | Natal moon→asc → cosmogram без этой пары; failed read отдельно | Исчезнувший selection снят, expansion сохранён, старых angles нет; ошибка чтения не снимает существующий выбор |
| REQ-WHEEL-08/09 / AS-WHEEL-02/14/16 | F5; принятый собственный changed-birth build; resize | F5 / подтверждённый новый own build reset к 5/5, resize сохраняет; событие reset задаётся причиной acceptance в DEV-WHEEL-04, не identity alone |
| REQ-WHEEL-09 / AS-WHEEL-26/AS-UI-22 | Первоначальное состояние / отдельные «Показать все» | Все points сразу, отдельные published angles, 5 aspects / 5 houses, независимое раскрытие; старый global hidden gate не возвращается |
| REQ-WHEEL-10/11 / AS-WHEEL-23 | Keyboard activation / повтор / re-render и local actions | Нет отдельной кнопки снятия, видимый focus, no auto scroll/focus для point; zero HTTP с positive valid explicit build control |

Controller хранит normal-aspects expansion отдельно от текущей одной строки / point filter и отдельно от houses. Point toggle сбрасывает normal expansion к пяти; aspect toggle и исчезновение выбора при current возвращают сохранённое normal expansion. При замене DTO не удерживать focus на удалённом узле: применить reviewed keyboard / focus policy, не подменять её sleep / программной прокруткой по умолчанию.

**Observability:** initiator / canonical key / source / actual identity → controller → wheel и HTML, в проверяемом порядке. Нового runtime logger нет. Event / fake clock для времени; timeout только от зависания.

**Команды:** `node --test tests/ui/selection.test.mjs tests/ui/facts.test.mjs`, затем `node --test tests/ui/*.test.mjs`; real browser pointer/keyboard/no-hover на 1440/768/360. Full pytest в финальном handoff. Snapshot private state не заменяет наблюдаемый DOM/SVG outcome; программный defect закрепить deterministic regression.

**Завершение:** каждый REQ/AS строки связан с чувствительным check, exact SHA и результатом, normal/filtered/single outcomes различимы. Любой новый semantic counterexample вернуть Analyst через Manager; ordinary internal details внутри reviewed port выбирает Developer. Публикация и независимый Tester отдельно.
