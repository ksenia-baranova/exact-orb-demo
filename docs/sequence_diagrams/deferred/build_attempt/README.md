# Sequence diagrams — отложенная модель `BuildAttempt`

**Статус:** отложено; не является действующим контрактом MVP.

Диаграммы в этом каталоге сохраняют проект модели durable execution:
`BuildAttempt` со статусами попытки, `build_revision`, восстановление
незавершённого расчёта после повторного открытия страницы и клиентский
`idempotency_key`. Эти механизмы сейчас не реализуются.

Действующий BuildNatal-flow описан в [`../../build_natal/`](../../build_natal/README.md).
Детерминированный расчёт выполняется как обычный request/response, а
актуальность записи обеспечивает compare-and-set по `state_version` внутри
`SessionStore`. Durable recovery после reconnect требует отдельного протокола
и архитектурного решения.

Основания:

- [ADR-0012](../../../requirements/decisions/0012-bootstrap-request-response-streaming.md)
  откладывает background execution, polling и durable recovery;
- [ADR-0014](../../../requirements/decisions/0014-explicit-state-mutations.md)
  закрепляет CAS по `state_version`;
- [ответственности BuildNatal](../../../requirements/component_responsibilities/exact-orb_build_natal_components.md)
  фиксируют условия возврата к отложенным механизмам.

| Файл | Отложенный сценарий |
|---|---|
| `001-build_attempt_disconnect_reopen.puml` | Продолжение незавершённого build после закрытия и повторного открытия страницы |
| `002-build_attempt_failure_reopen.puml` | Восстановление формы и сведений о неуспешной попытке |
| `003-build_attempt_idempotency_duplicate.puml` | Дедупликация повторной доставки через клиентский `idempotency_key` |

## Условия возврата

- `BuildAttempt`, статусы попытки, `build_revision`, reaper и восстановление
  после reopen рассматриваются снова, если расчёт устойчиво занимает несколько
  сотен миллисекунд либо становится асинхронным.
- Отдельный клиентский `idempotency_key` рассматривается при появлении операции
  с внешним побочным эффектом, который нельзя безопасно закрыть расчётным кэшем
  и CAS.

Диаграммы намеренно сохраняют детали ранее рассмотренного проекта и могут
содержать устаревшие относительно текущей реализации имена. Их нельзя
использовать как описание работающего API или как источник текущего контракта.
