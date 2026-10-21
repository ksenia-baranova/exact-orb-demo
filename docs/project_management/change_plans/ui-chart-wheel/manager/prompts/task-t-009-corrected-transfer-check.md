# TASK-T-009 — адресная сверка исправленного переноса

Сначала обнови `test/ui-chart-wheel` из опубликованной
`origin/change/ui-chart-wheel`, сохрани несвязанные изменения. Используй Tester
skill. AssignmentSHA — первый опубликованный commit с этим файлом; запиши его
полный SHA, а также фактический HEAD. Input исходного пакета —
`72ab4e30321884ddabe4205505216a7595d8bfeb`.

Это проверка исправлений **T008-R01/R02** и необязательного **T008-N01**.
Предыдущий независимый T008 @ `583d635559862edc25e271f68053038c38fe088d`
завершён правильно с `TRANSFER_REWORK_REQUIRED`; его отчёт/evidence не переписывай.
Начни с `manager/session_closure_checks.json`, `manager/transfer_manifest.json`,
`analyst/transfer_map.md` и Manager §2.30. Проверку Manager за собственное
независимое evidence не выдавай.

Проверь только затронутую дельту:

1. AS-WHEEL-09 ссылается на F3 с пятью retrograde points через 0°, сохранил
   sparse positive control и текущий internal-house-row expected; F2 остаётся
   набором состояний сессии. Старый column/C0/minimality oracle не возвращён.
2. Ссылка «Обязательные материалы» Manager ведёт на tracked общий UI README.
   Проверяй Git-tree, включая directory links: пустая локальная папка не
   доказывает существования каталога в commit.
3. AS-WHEEL-28 явно связан с F5/S1, AS23/30; U/R/D/V/M/L/T/P и уникальный
   paired control, pointer/keyboard, natal/cosmogram, five/all сохранены.
4. Обновлённый target hash scenarios/UI README, 22 REQ/53 AS/11 PUML, 13 удалённых
   источников, исходные from/to/type/category/orb/order и raw evidence сохранены.
5. Сверь ADR-0042/component responsibilities с текущими схемами и реализацией
   в пределах документального соответствия. ADR принят Owner21.10 для текущего
   пассивного M1-8; активное колесо — будущая отдельная фича, Manager §2.31.
   Проверь эту границу; R002 approval и выполнение будущей фичи не выдумываются.

Если src/tests не менялись, полный runtime/browser повтор не назначается;
старый RetestedSHA9974195 и его ограничения остаются. Если найдено настоящее
изменение поведения, опиши точное пересечение и необходимый адресный retest.
TEST-FIND-WHEEL-002/precision не превращать в PASS; DEBT-UI-004 OPEN, bug004 CLOSED.

Результат: `tester/corrected_transfer_review.md` и необходимое собственное
evidence с SourceSHA/AssignmentSHA/OutputSHA, actual/expected и verdict
`TRANSFER_APPROVED` либо адресный `TRANSFER_REWORK_REQUIRED`. Reviewer результата
— Manager по комплектности. Используй существующий bounded documentary scope;
до STARTED сообщи свою оценку/срок, при выходе за прежний слот T008 2–4ч передай
Manager влияние, не запускай общий цикл согласований.

Регистрируй авторство и фактические команды. Новые продуктовые требования,
geometry research, правки чужих conclusions, commit/push/PR/merge и сообщения
другим чатам этим текстом не разрешены; Git-публикация по отдельному поручению.
