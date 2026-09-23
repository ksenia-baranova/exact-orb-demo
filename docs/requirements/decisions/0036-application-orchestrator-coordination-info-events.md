# ADR-0036. INFO-события прямых сообщений ApplicationOrchestrator

Дата: 2026-09-22.
**Статус: принято.**

Дополняет observability-решение ADR-0006 и входную DEBUG-запись ADR-0035.
Четыре существующих вида lifecycle-событий не заменяются.

## Контекст

Полные DEBUG-сообщения показывают внутренний путь `BuildNatalHandler` через
resolver и artifact resolver. Компактный журнал ApplicationOrchestrator
показывает начало, завершённые стадии и commit outcome, но не показывает,
когда координатор отправил вызов и получил ответ от своих прямых компонентов.
По общему логу трудно отличить координацию от самостоятельной цепочки вызовов.

## Решение

ApplicationOrchestrator пишет компактное событие уровня `INFO` на отправку
каждого фактически начатого прямого вызова и на его нормальный возврат:

```text
application_message direction=<send|receive> run_id=<id>
                    peer=<actual component class> operation=<load|handle|save>
                    message_type=<request or response type> attempt=<1|2|->
```

Прямые адресаты — `ContextService.load`, выбранный `Handler.handle` и
`ContextService.save`. На отправке `message_type` называет диагностическую
проекцию входа принимающего компонента: `ContextLoadRequest`,
`BuildNatalRequest` для текущей команды и `ContextSaveRequest`. Для другого
типа команды Handler сохраняется её фактическое имя класса. Это имена событий,
а не новые публичные модели. На приёме `message_type` — фактический тип
возвращённого объекта, включая типизированный отказ. `attempt` используется
только для save. В событии нет тела сообщения, `session_id`, данных рождения,
состояния сессии или артефакта.

`send` пишется непосредственно перед вызовом load/handle и после успешного
создания задачи save. `receive` пишется только после фактического возврата.
Исключение или отмена без ответа не создаёт ложного `receive`; существующие
exception-, cancellation- и terminal-события сохраняют классификацию исхода.
Повторный save имеет собственные `send` и `receive` с `attempt=2`.

Orchestrator не пишет сообщения от имени `BirthDataResolver`,
`ChartArtifactResolver` или engine: их напрямую вызывает Handler или следующий
компонент. Их собственные boundary-события сохраняются без изменений.

## Последствия

- На уровне INFO видна последовательность координации без сериализации payload.
- `application_operation_started`, `application_stage_finished`,
  `application_commit_attempt_finished` и `application_operation_finished`
  сохраняют уровни, поля и смысл; новые события не используются для подсчёта
  завершённых операций или commit attempts.
- Маршрутизация, результаты, retry, отмена и расчётное поведение не меняются.
