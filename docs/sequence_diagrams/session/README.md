# Sequence diagrams — состояние сессии

Диаграммы фиксируют модель MVP. `SessionState` — состояние анонимной
TTL-сессии, а не пользовательский профиль. Отдельная сохраняемая сущность
`SessionContext` не вводится: `ContextService` загружает и сохраняет
`SessionState` через фасет `SessionStore`. Согласованный read-and-renew
возвращает frozen `SessionSnapshot { state, dialog, chart }` через агрегат
`SessionPersistence`; фасетные `get`/`read` read-only.

Семь пользовательских сценариев, компонентный bootstrap и таблицы сообщений
описаны в [требованиях к поведению сессии с картой](../../requirements/session/stored-chart-session-behavior.md).

`ContextService` получает один aggregate и явный clock. Публичные create,
load, save, append_turn, clear_dialog и reset_all не принимают `now`: каждый
вызов читает clock ровно один раз и передаёт проверенное UTC-значение вниз.
Naive или non-zero-offset результат даёт `ValueError` до persistence. Delete
clock не читает. Любой persistence error отображается по операции: load — в
`StateReadFailed`, мутации — в `StateCommitFailed`, независимо от error
subclass.

Успешные CAS, append и clear являются write-and-renew. Append продлевает
parent state и dialog одним deadline; clear продлевает state и очищает
dialog, сохраняя предметные поля и `state_version`. `touch` остаётся
единственным read-and-renew.

В `SessionState` нет полной карты и `calculation_key`. Он хранит
пользовательский ввод, разрешённые данные рождения, ссылку на текущую
натальную карту и версию состояния. Сериализованный `ChartArtifact` в виде
`StoredChart` хранится отдельной дочерней записью агрегата сессии по ADR-0040;
форматом и проверкой карты владеет артефактный слой. Компонентный контракт
M1-5.2 реализован; HTTP bootstrap и cookie относятся к M1-6.

**Ходы диалога хранятся отдельной записью** через `DialogStore`, а не внутри
`SessionState`. Иначе каждая запись карты через CAS переписывала бы весь
диалог, а добавление хода конкурировало бы с изменением карты за одну версию.
Обоснование — `component_responsibilities/exact-orb_session_requirements.md`
§3.1, контракт — §3.2.

`session_id` всегда генерирует доверенный server transport. HttpOnly cookie
используется только как lookup key; команды и query не принимают ID из
body/query/path. Отсутствующий или истёкший ключ не переиспользуется для
create — transport гасит cookie и генерирует свежий ID.

Create и restore при bootstrap транспорт выполняет через `ContextService`
напрямую, без `ApplicationOrchestrator` (ADR-0006, ред. 2026-09-15): так
нарисованы 001, 002 и первая ветка 003. Команды над уже загруженной сессией —
построение, reset, delete — проходят через Orchestrator.

Межзаписные touch/reset/delete принадлежат одному `SessionPersistence`.
Полный reset агрегат только делегирует фасетному CAS с `RESET_DELTA`;
RESET_DELTA-aware CAS сам очищает диалог и карту в общей backend-секции.

`StateReadFailed` — fail-closed результат незавершённого обязательного
load-and-renew: он не различает отказ чтения и отказ продления после чтения и
сам по себе не означает утрату сессии. `Superseded` также читается нейтрально
как mismatch actual и intent, а не как доказанная победа другой операции.

Sequence намеренно сворачивают внутренности расчётного и интерпретационного
конвейеров. Их подробности остаются в `../build_natal/` и
`../chart_artifacts/`.

| № | Файл | Сценарий | Исход |
|---|---|---|---|
| 001 | `001-natal-session-lifecycle.puml` | Первая карта → интерпретация → явное изменение данных через форму | Диалог доступен только для успешно сохранённой текущей карты |
| 002 | `002-session-restore-on-return.puml` | Возврат после рестарта с пустым расчётным кэшем; живая пустая сессия; сессии нет | `chart_ready`, `chart_stale`, `chart_unavailable`, `empty` либо `SessionAbsent` |
| 003 | `003-session-store-read-failure.puml` | Отказ required touch; exact retry после неподтверждённого commit | `StateReadFailed`; N8 без rebase |
| 004 | `004-session-reset-and-delete.puml` | Очистка диалога, атомарный reset/delete, гашение cookie | `RESET_DELTA` и один aggregate lifecycle |
| 005 | `005-compare-and-set.puml` | Механизм CAS и три исхода записи | `Committed`, `Superseded`, `AlreadyApplied` |
| 006 | `006-two-tabs-rebuild-and-restore.puml` | Две вкладки: B перестраивает карту, A обновляется позднее | Общая серверная версия; без автоматической синхронизации вкладок |
| 007 | `007-first-build-fails-then-return.puml` | Первое построение остановилось до CAS; повторный вход | Пустая сессия, прежний ввод не восстанавливается |

Диаграмма 005 объясняет механизм, а не пользовательский сценарий:
прикладная ветка конкурентного построения нарисована в
`../build_natal/006-build_natal_superseded_cas.puml`.

`derived_chart`, `active_view` и команда `SetActiveView` в MVP отсутствуют:
транзиты не входят в первый срез, поэтому активный вид всегда `base`.
Сужение временное и снимается вместе с транзитами (ревизия ADR-0016).

Изменение данных рождения из диалога и будущий agent tool `build_natal`
находятся за границей MVP. В текущем потоке используется только tool
`ensure_natal`, который материализует уже выбранную в сессии карту и не
меняет `SessionState`. Показанная в 001 M2-интерпретация пока вызывает
`ensure_natal` по spec и после ADR-0040 может получить карту другой версии,
чем сохранённая. Её контракт нужно пересмотреть до реализации M2; первая
ветка хранения карты этот поток не меняет.

## Рендер

```
java -jar plantuml.jar -tpng -o out *.puml
```
