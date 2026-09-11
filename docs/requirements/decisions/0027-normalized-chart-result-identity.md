# ADR-0027. Нормализованный результат карты и сквозные инварианты идентичности

Дата: 2026-09-11.
**Статус: принято.**

Дополняет ADR-0017: способ вычисления `calculation_key` и граница opaque
`bytes` Calculation Cache сохраняются, а настоящее решение определяет
канонические источники данных внутри результата и обязательные проверки их
согласованности.

## Контекст

До нормализации один результат расчёта хранил одни и те же значения в
нескольких независимо задаваемых полях. `chart_kind` присутствовал в
`ChartSpec`, `ChartArtifact` и `NatalChart`; `warnings` — в `ChartArtifact` и
`NatalChart`; `CalculationResult` повторял оба значения рядом с `chart`.
Параметры расчётного входа одновременно находились в
`StateDelta.birth_resolved` и `ChartArtifact.chart`, но итоговая модель
проверяла только часть связей.

Поэтому можно было собрать типизированный `BuildNatalSuccess`, в котором
разрешённые время и место относились к одному рождению, карта — к другому, а
`calculation_key` не доказывал тождество всей конструкции. Такой объект был
формально допустим и мог перейти к сохранению состояния.

Дублирование само по себе не всегда является ошибкой. Спецификация запроса,
результат расчёта, состояние сессии и storage envelope имеют разных
потребителей. Ошибка возникает, когда одинаковое значение можно независимо
задать в нескольких местах и модель не устанавливает направление зависимости
или сквозной инвариант.

## Решение

### Канонические источники

| Значение | Места хранения | Классификация | Канонический источник | Итоговое решение |
|---|---|---|---|---|
| `chart_kind` | `ChartSpec.chart_kind`, `NatalChart.chart_kind`, `StateDelta.base_chart_spec.chart_kind` через spec; ранее также wrapper-поля | 3 — разные bounded context | запрос — `ChartSpec`; факт — `NatalChart` | Верхнеуровневые дубликаты удалены, spec и chart обязаны совпадать |
| предупреждения разрешения | `ResolvedBirthData.warnings` | значение отдельной стадии | `ResolvedBirthData.warnings` | Не объединять с предупреждениями расчёта и не сравнивать с ними |
| предупреждения расчёта | `NatalChart.warnings`; ранее также `CalculationResult.warnings` и `ChartArtifact.warnings` | 1 — необоснованные независимые источники истины | `NatalChart.warnings` | Wrapper-дубликаты удалены |
| `ChartSpec` | `StateDelta.base_chart_spec`, `ChartArtifact.spec` | 3 — разные bounded context | оба представления в своих контекстах | Сохранить и требовать точного равенства в `BuildNatalSuccess` |
| UTC-время и координаты | `ResolvedBirthData`, `NatalChart` | 2 — производное материализованное представление | разрешённый вход — `calculation_input_from(ResolvedBirthData)`; аудит карты — `calculation_input_from_chart(NatalChart)` | Сохранить оба и сравнивать после нормализации; UTC-время engine проверяет также точно |
| `calculation_key` | `ChartArtifact`, cache address и logging envelope | identity плюс 4 — технические ссылки | хранимая identity — `ChartArtifact.calculation_key`; значение задаёт чистая функция от `CalculationInput`, `ChartSpec`, `CalculationVersion` | Пересчитывать, а технические копии сравнивать с результатом функции |
| аспекты | `NatalChart.aspects`, сериализованный cache payload | каноническое значение и 4 — техническая копия | `NatalChart.aspects` | Не дублировать в wrapper-моделях |
| конфигурации | `NatalChart.configurations`, сериализованный cache payload | каноническое значение и 4 — техническая копия | `NatalChart.configurations` | Не дублировать в wrapper-моделях |
| позиции | `NatalChart.bodies`, сериализованный cache payload | каноническое значение и 4 — техническая копия | `NatalChart.bodies` | Не дублировать в wrapper-моделях |
| производные позиции | элементы `NatalChart.bodies` и derived-модели внутри карты | 2 — производное материализованное представление | `NatalChart` | Сохранить как часть результата |
| `CalculationVersion` | runtime resolver и `ChartArtifact.calculation_version` | 3 — разные bounded context | runtime-конфигурация при расчёте; audit-копия в артефакте | Сохранять и проверять |
| сериализованный артефакт | валидированная модель и gzip JSON `bytes` | 4 — техническая копия | валидированная модель | Calculation Cache остаётся opaque `bytes` |

`CalculationResult` содержит только `chart`. `ChartArtifact` содержит ровно
`calculation_key`, `spec`, `calculation_version` и `chart`. Публичный
`NatalChart` остаётся полным материализованным результатом расчёта, а
`ArtifactNatalChart` отличается только artifact-safe представлением статуса
эфемерид.

### Локальные инварианты

`EngineService` принимает `ChartSpec` и `ResolvedBirthData` и до возврата
проверяет:

1. `chart.chart_kind == spec.chart_kind`;
2. нормализованные house system карты и спецификации равны;
3. присутствие `bodies`, `cusps`/`angles`, `house_rulers`/`interceptions`,
   `aspects`, `configurations` и `strength` в точности соответствует
   `spec.include`;
4. `chart.datetime_utc == resolved.utc_datetime`;
5. нормализованная проекция времени и координат карты равна
   `calculation_input_from(resolved)`.

`ChartArtifact` при создании и декодировании проверяет первые три инварианта и
требует:

```text
artifact.calculation_key == calculation_key(
    calculation_input_from_chart(artifact.chart),
    artifact.spec,
    artifact.calculation_version,
)
```

Модели результата и артефакта immutable и запрещают неизвестные поля там, где
envelope является storage-контрактом. Удалённые поля нельзя незаметно вернуть
как игнорируемый input.

### Сквозные инварианты application result

Успешный `BuildNatalSuccess` допускает только полностью заполненный
`StateDelta`: `birth_input`, `birth_resolved` и `base_chart_spec` присутствуют
вместе. Затем проверяются:

1. `artifact.spec == delta.base_chart_spec`;
2. `base_chart_spec.chart_kind` равен `cosmogram` при `time_unknown=true` и
   `natal` иначе;
3. отсутствие `birth_input.birth_time` равносильно
   `birth_resolved.time_unknown`;
4. нормализованные время и координаты `artifact.chart` равны
   `delta.birth_resolved`;
5. `artifact.calculation_key` заново вычисляется из
   `delta.birth_resolved`, `delta.base_chart_spec` и
   `artifact.calculation_version`.

Тем самым локально корректный артефакт нельзя соединить с чужим delta.
Нарушение, обнаруженное при сборке результата handler, становится
`pydantic.ValidationError`; handler пишет `build_natal_failed` с этапом
`build_result`, а boundary logger — полный error payload. Противоречивый
success наружу не выпускается.

### Проверка Calculation Cache

У кэша остаются два уровня защиты:

1. кодек декодирует opaque `bytes` в строгий `ChartArtifact`, поэтому
   повреждённая или несовместимая форма считается `cache_corrupt`;
2. resolver после декодирования сравнивает ключ запроса, текущие
   `ChartSpec` и `CalculationVersion`, а также `CalculationInput`,
   восстановленный из карты. Несовпадение считается `cache_stale`.

Corrupt и stale записи обрабатываются fail-open как промах: расчёт выполняется
заново, валидный артефакт возвращается вызывающему и предпринимается обычная
запись в кэш.

### Отсутствие `artifact_schema_version`

Отдельное поле `artifact_schema_version` не вводится. Оно не доказывает
семантическую согласованность полей и потребовало бы ручного увеличения при
каждом несовместимом изменении модели. Предыдущая запись всё равно может стать
невалидной из-за строгой схемы Pydantic и должна безопасно перейти в
`cache_corrupt`/пересчёт.

Версия `v1` в префиксе `calculation_key` имеет другую ответственность: это
версия канонической сериализации входа ключа, а не версия JSON-схемы
артефакта. `CalculationVersion` описывает численно значимую реализацию
расчёта. Ни одно из этих значений не дублируется новым version-полем.

## Альтернативы

**Сохранить дубликаты и добавить попарные validators** — отвергнуто: число
связей растёт вместе с числом копий, а каждой новой модели пришлось бы знать
обо всех старых представлениях.

**Оставить `CalculationResult` самостоятельным snapshot с kind и warnings** —
отвергнуто: у этих полей нет потребителя или ответственности вне вложенного
`NatalChart`.

**Считать `calculation_key` достаточным доказательством** — отвергнуто: строку
ключа можно было передать независимо от payload; доверие появляется только
после пересчёта из проверенных данных.

**Ввести `artifact_schema_version = 2`** — отвергнуто: это усложняет envelope
и ключ без устранения рассинхронизации; прежние несовместимые записи уже
безопасно инвалидируются строгим декодированием.

## Последствия

- у каждого значения задан источник и направление материализации;
- синтетически противоречивый `BuildNatalSuccess` отклоняется до сохранения;
- cache hit доказывает соответствие актуальному запросу, а не только
  декодируемость payload;
- старые payload с удалёнными полями могут быть признаны corrupt и
  пересчитаны; миграция Calculation Cache не требуется;
- публичная форма `CalculationResult` и storage-форма `ChartArtifact`
  намеренно несовместимо сужены;
- численный алгоритм, нормализация входов и формат `calculation_key` не
  изменены;
- новые производные копии допускаются только с указанным потребителем,
  ответственностью и проверкой связи с каноническим значением.
