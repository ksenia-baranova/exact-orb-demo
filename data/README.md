# Каталог населённых пунктов

`places.sqlite` — версионированный снимок каталога для локального HTTP-стенда и
воспроизводимых интеграционных проверок. Это read-only вход
`SqlitePlaceCatalog`; путь для локального запуска — `data/places.sqlite`.
База не включается в Python wheel. Доставку read-only каталога при deployment
по-прежнему определяет M1-12.

| Свойство | Значение |
| --- | --- |
| SHA-256 `places.sqlite` | `AFA097AF657805C420449393B1E3C561C6C3170A3A1084B0189386A37ABBA0DD` |
| Размер | 5 238 784 байта |
| Schema version | 1 |
| `places` / `place_names` | 16 329 / 36 648 |
| `tzdata_version` при сборке | `2026.3` |

Снимок создан `scripts/build_place_catalog.py` из трёх GeoNames-файлов с
параметрами сборки, сохранёнными в `catalog_metadata`. SHA-256 входов из
metadata:

| GeoNames-файл | SHA-256 |
| --- | --- |
| `cities1000.txt` | `b2f5239acc9f894f4bfd7d38bbc17a6a5c0b168d71ef14ec08c345f8fb701563` |
| `admin1CodesASCII.txt` | `590651498043f674accda2b7f46d21286cda0e290b02f8561c5005eee9a5448c` |
| `alternateNamesV2.txt` | `058c470a07b0a6cfe1c238584e0b74e1b1693ac80b22af66f421f09887a9d24a` |

Данные: [GeoNames](https://www.geonames.org/),
[GeoNames Gazetteer extract](https://download.geonames.org/export/dump/readme.txt),
лицензия [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
Эта база — преобразованная выборка GeoNames: builder фильтрует населённые
пункты, выбирает имена и регионы, нормализует координаты и строит индексы.
При показе данных пользователю сохраняйте атрибуцию GeoNames. Исходные дампы
в Git не добавлены.

Для нового выпуска каталога запустите builder по
[инструкции](../docs/requirements/component_responsibilities/exact-orb_place_catalog.md#26-локальная-сборка),
проверьте schema, metadata, полноту поиска и новый SHA-256, затем обновите
эту таблицу вместе с `places.sqlite`. Не заменяйте снимок локальным файлом без
проверки его источников и поведения.
