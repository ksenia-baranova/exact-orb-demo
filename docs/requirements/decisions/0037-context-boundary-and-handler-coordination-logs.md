# ADR-0037. DEBUG-граница ContextService и INFO-координация Handler

Дата: 2026-09-22.
**Статус: принято.**

Дополняет ADR-0025/0028 о полных локальных DEBUG-сообщениях и ADR-0036 об
INFO-событиях прямых вызовов координатора. Публичные методы и результаты
компонентов не меняются.

## Контекст

На пути Build Natal журнал показывает передачу от ApplicationOrchestrator к
`ContextService` и `BuildNatalHandler`, но не показывает фактический вход и
выход `ContextService`. Внутри Handler DEBUG-сообщения resolver и artifact
resolver есть, однако на INFO не видно, что эти вызовы отправил Handler и
получил их результаты.

## Решение

Все семь публичных async-операций `ContextService` — `create`, `load`, `save`,
`append_turn`, `clear_dialog`, `reset_all`, `delete` — пишут парные
`component_message direction=in|out` только при effective `DEBUG`. Формат
envelope совпадает с ADR-0028; `operation=context_<method>`.
Входной `message_type=Context<Method>Request` обозначает диагностическую
проекцию аргументов вызова, а не новый публичный тип. Выходной `message_type`
равен фактическому типу результата, включая `NoneType`; при исключении выход
имеет `status=error`, `payload_mode=error` и тип исключения. В `message` пишется
полный однострочный JSON входа или результата без усечения. Ниже DEBUG
проекция и сериализация не выполняются.

У `ContextService` нет параметра `RunContext`, поэтому его DEBUG-события имеют
`run_id=-`. Скрытый контекст и новый параметр ради логирования не вводятся.
При конкурентных операциях эти события нельзя однозначно привязать к `run_id`
по одному только логу ContextService; INFO-события Orchestrator сохраняют
свой `run_id` на обеих сторонах прямого вызова.

`BuildNatalHandler` пишет `application_message direction=send|receive` на
`INFO` вокруг собственных прямых вызовов `BirthDataResolver.resolve` и
`ChartArtifactResolver.ensure_chart`. На отправке `message_type` совпадает с
их DEBUG-входом: `BirthResolutionRequest` и `EnsureChartRequest`; на приёме
равен фактическому типу результата. Событие содержит только `run_id`, peer,
operation, `message_type`, `attempt=-`, без тела. При исключении или отмене
`receive` не создаётся; существующее terminal-событие Handler сохраняется.

Граница session-сервиса продолжает импортировать из project-модулей только
session contracts: общее `exact_orb.component_logging` не импортируется
из `exact_orb.session.context` из-за инварианта модулей.

## Последствия

- INFO показывает владельца вызовов resolver и artifact resolver; DEBUG
  показывает вход и фактический результат `ContextService`.
- DEBUG-выход `load` может содержать полное состояние сессии и диалог. Для
  удалённого M1-стенда действует effective `INFO` по ADR-0034; политика
  защищённого DEBUG-журнала остаётся условием публичного развёртывания.
- Расчёт, CAS, TTL, retry, отмена и типизированные результаты не меняются.
