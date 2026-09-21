# Sequence diagrams — каталог мест

Две независимые группы потоков над одним офлайн-каталогом:

1. HTTP endpoint вызывает `PlaceSearch.search(text)` для подсказок UI.
2. `BirthDataResolver` вызывает `PlaceCatalog.lookup(place_id)` внутри
   Build Natal application-flow.

Диаграммы фиксируют целевой контракт M1-5 `feat/place-catalog` и границу
с будущими M1-6/M1-7, не объявляя HTTP endpoint и UI уже реализованными.
Нормативные модели, исходы и ограничения описаны в
[`docs/requirements/component_responsibilities/exact-orb_place_catalog.md`](../../requirements/component_responsibilities/exact-orb_place_catalog.md).

Текущий реализованный build-путь уже содержит
`BirthDataResolver → PlaceCatalog.lookup(place_id)`. `PlaceSearch`,
`SqlitePlaceCatalog`, HTTP boundary и форма с подсказками остаются целевыми
компонентами до выполнения соответствующих веток.

## 1. Endpoint → каталог мест

В этих потоках нет `ApplicationOrchestrator`, `BuildNatalHandler` и
`BirthDataResolver`: построение карты ещё не запущено.

| Файл | Сценарий | Исход |
|---|---|---|
| `001-search-place-success.puml` | Поиск «Москва» | `PlaceSuggestions` с `place_id="524901"` |
| `002-search-place-invalid-query.puml` | После нормализации в запросе нет букв или цифр | `InvalidPlaceQuery`; SQL не выполняется |
| `003-search-place-not-found.puml` | Корректное название не найдено | `PlaceSuggestions(items=())`; `place_id` не возникает |

## 2. BirthDataResolver → lookup(place_id)

В этих потоках `place_id` уже выбран, входит в `BirthInput` и повторно
проверяется внутри реального application-flow.

| Файл | Сценарий | Исход |
|---|---|---|
| `004-resolve-place-id-success.puml` | Выбранный ID найден | `ResolvedPlace` с координатами и `tz_id` |
| `005-resolve-place-id-not-found.puml` | ID неизвестен или устарел | `InputRequired { birth.place, INVALID }` |
| `006-place-catalog-unavailable.puml` | SQLite-каталог недоступен | `ResolutionUnavailable`, затем `ApplicationResolutionFailure` |

Общие инварианты:

- поиск и `lookup` выполняет один экземпляр `SqlitePlaceCatalog` над одним
  неизменяемым выпуском `places.sqlite`;
- UI получает название и стабильный `place_id`, но не становится источником
  координат или `tz_id`;
- `BirthDataResolver` повторно проверяет недоверенный `place_id` через
  `PlaceCatalog.lookup`;
- структурно невалидный запрос отличается от корректного запроса без
  совпадений;
- `utc_offset_seconds` в каталоге не хранится: его вычисляет timezone-слой
  по `tz_id`, дате и местному времени рождения.

Сфокусированные lookup-диаграммы не заменяют более широкие существующие
потоки. Полный успешный резолв даты, времени и места показан в
[`../birth_resolution/001-resolve_date_time_place.puml`](../birth_resolution/001-resolve_date_time_place.puml),
а существующий сценарий неизвестного ID — в
[`../birth_resolution/003-resolve_place_not_found.puml`](../birth_resolution/003-resolve_place_not_found.puml).

## Рендер

```text
java -jar plantuml.jar -tpng -o out *.puml
```
