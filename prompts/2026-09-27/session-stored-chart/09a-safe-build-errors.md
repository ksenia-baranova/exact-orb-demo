# Промт 09a. Безопасная классификация ошибок подготовки карты

**Дата:** 2026-09-27.

**Ветка:** `feat/session-stored-chart`.

**План:** [M1-5.2](../../../docs/project_management/implementation_plans/session_stored_chart_implementation_plan.md), исправления после ревью.
**Статус:** выполнен 2026-09-27.

## Человеческое описание: что и зачем мы делаем

При сохранении построенной карты приложение кодирует её и собирает результат
Handler. Сейчас разные сбои этого пути выглядят одинаково: неожиданная ошибка
порта маскируется под ошибку кодирования, а нарушение идентичности результата
маскируется под ошибку конверта. Нужно вернуть точные внутренние причины и
сохранить безопасный журнал: трассировка Orchestrator не должна раскрывать
сообщение исходного исключения или байты карты.

## Задача

Выполни только исправления классификации ошибок. Перед правкой сверь ADR-0027,
ADR-0040, §7–8 `stored-chart-session-behavior.md`, текущий codec, resolver,
Handler, Orchestrator и существующие тесты. Сохрани несвязанные изменения.

1. В `ChartArtifactResolver.to_stored` ожидаемые отказы сериализации, определённые
   по реальному `encode_chart_artifact`, переводи в `ChartArtifactEncodingError`
   с безопасным `cause_type` (имя типа без исходного сообщения и payload).
   Остальные исключения resolver не маскирует.
2. Handler переводит `ChartArtifactEncodingError` в `StoredChartPreparationError`
   с `reason=ENCODE_FAILED`, а любое другое `Exception` из `to_stored` — с
   новой причиной `ENCODE_UNEXPECTED`. Обе причины получают `cause_type` и
   создаются через `from None`. `MemoryError` и исключения `BaseException`
   вне `Exception` не перехватываются. Текст новой ошибки содержит только
   `reason` и `cause_type`; исходный текст и payload в неё не входят.
3. Событие `build_natal_failed` получает явные поля `reason=` и `cause_type=`.
   Для отказов без этих атрибутов используй безопасное отсутствие значения.
   Проверь полный форматированный traceback на реальном пути Handler →
   Orchestrator, включая чувствительный маркер исходного исключения.
4. Верни поведение ADR-0027: только валидация `StoredChart`/`StateDelta`
   относится к `ENVELOPE_INVALID`. `ValidationError` от `BuildNatalSuccess`
   выходит исходным типом, а Handler фиксирует `stage=build_result`. Новое ADR
   не нужно. Тест полного traceback на текущем Pydantic должен подтверждать,
   что маркерный payload и `input_value` не попали в журнал.
5. Обнови текущие тесты, включая прежние ожидания `RuntimeError → ENCODE_FAILED`
   и `ENVELOPE_INVALID` для нарушения идентичности. Закрепи детерминированными
   regression-тестами оба класса отказа resolver, обе причины Handler и
   безопасность журнала. Не меняй тесты вне этой причинной цепочки.
6. Синхронизируй `StoredChartPreparationReason`, таблицу отказов §7 и текст §8
   спецификации: добавь `ENCODE_UNEXPECTED`, `cause_type` и различие между
   ожидаемым кодированием и неожиданным исключением порта. Уточни лишь те
   фразы, которым противоречит возврат к ADR-0027. Добавь строку 09a в §8
   плана с фактическими проверками и пределами свидетельства.

## Приёмка

Запусти сначала целевые тесты resolver/Handler/Orchestrator и traceback,
затем связанные application и module-boundary тесты, затем полный локальный
`pytest`. Не запускай сетевой или платный smoke. Проверь `git diff --check`.
Запиши точные команды и реальные результаты в план и сюда после выполнения.
Не редактируй промты 01–08. Не создавай коммит, ветку, push или PR.

## Выполнение

- Resolver классифицирует `PydanticSerializationError`, `UnicodeEncodeError`
  и `zlib.error`; другие исключения сохраняют исходный тип до Handler.
- Handler различает `ENCODE_FAILED` и `ENCODE_UNEXPECTED` с безопасным
  `cause_type`; `BuildNatalSuccess` снова выпускает `ValidationError` на
  этапе `build_result` по ADR-0027.
- Целевые тесты: 108 passed; связанный набор вне песочницы: 1040 passed;
  полный локальный набор: 2652 passed. В песочнице связанный набор дал
  1036 passed, 4 errors из-за отказа доступа к системному temp; повтор с
  `--basetemp` внутри checkout также не смог прочитать temp при cleanup.
- Команды и пределы свидетельств указаны в §8 плана. Сетевые и платные
  smoke-тесты не запускались.
