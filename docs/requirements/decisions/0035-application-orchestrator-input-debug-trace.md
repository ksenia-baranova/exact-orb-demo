# ADR-0035. Входное DEBUG-сообщение ApplicationOrchestrator

Дата: 2026-09-22.
**Статус: принято.**

Частично изменяет ADR-0006 в части запрета на повторную запись входного
payload Handler в журнале ApplicationOrchestrator. Парные сообщения пяти
расчётных границ по ADR-0025/0028 не меняются.

## Контекст

`application_operation_started` показывает `run_id` и тип команды, но не
показывает значения, с которыми вызван `execute(command, session_id, run)`.
Следующая полная входная запись принадлежит `BuildNatalHandler.handle`, поэтому
по DEBUG-журналу нельзя увидеть, какую именно команду получил координатор до
маршрутизации и загрузки сессии.

## Решение

Сразу после компактного `application_operation_started`, до выбора Handler и
`ContextService.load`, каждый вызов `execute()` пишет одно полное входное
сообщение через существующий `component_logging`:

```text
component_message direction=in operation=application_execute
                  run_id=<id> calculation_key=- status=ok payload_mode=full
                  message_type=ApplicationExecuteRequest message=<single-line JSON>
```

`message` содержит `command_type`, полную типизированную `command`, доверенный
`session_id` и переданный `run`. Так один `run_id` связывает фактический вход
Orchestrator с последующим входом Handler. На входе Orchestrator ещё нет
загруженного `SessionState` и вычисленного `calculation_key`; они не добавляются
в сообщение. `ApplicationExecuteRequest` — имя диагностической проекции, а не
новая публичная модель команды.

Запись создаётся только при effective `DEBUG`; при `INFO` payload не
сериализуется. Компактные lifecycle-события, их уровни, количество и поля не
меняются. Отдельное полное `direction=out` для Orchestrator не вводится: его
фактический исход уже записывает `application_operation_finished`, включая
отмену до commit. Парный контракт ADR-0025/0028 продолжает применяться к пяти
перечисленным там границам.

## Последствия

- DEBUG-журнал показывает, с каким входом Orchestrator вызвал Handler, и
  позволяет сравнить обе записи по `run_id` и содержимому команды.
- Локальный DEBUG-журнал теперь также содержит полный `session_id` на границе
  Orchestrator. Действующее ограничение ADR-0034 для удалённого стенда —
  effective `INFO` — остаётся обязательным; новый путь не расширяет серверный
  INFO-журнал.
- `RunContext`, маршрутизация, состояние сессии, результаты и расчётное
  поведение не меняются.
