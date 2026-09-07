# CalculationVersion: отпечаток расчёта, закрывающий механизм B-7

Задача: реализовать `calculation/version.py` — детерминированный отпечаток
того, **чем** посчитана карта, входящий в `calculation_key`.

Работай в ветке:

`feat/calculation-version`

Не создавай коммит, push или PR. Сохрани пользовательские и несвязанные
изменения рабочего дерева.

Основание: ревизия ADR-0017 от 2026-09-07 (заморозка), Т-ГРН-7,
§3.1.5–3.1.6 `exact-orb_chart_artifacts.md`, §4.1
`exact-orb_build_natal_components.md`, инвариант B-7.

Не реализовывать: `bootstrap.py`, `application/`, изменение формы `ChartSpec`,
Redis, `ensure_derived`, переименование `calculate_transits`.

Документацию в `docs/**` в этой задаче не менять: синхронизация контракта,
примеров bootstrap и описания startup-вызова будет выполнена отдельной задачей.
Если действующий документ противоречит явно зафиксированному ниже контракту,
не разрешай противоречие молча и укажи его в итоговом отчёте.

## 1. Проблема и граница результата

`version` приходит в `ChartArtifactResolver` произвольной строкой, которую никто
не вычисляет. Подмена `ephe/*.se1`, обновление `swisseph`, правка дефолтных
расчётных конфигов и смена методики Селены не меняют ключ: кэш может отдать
карту, посчитанную прежней машинкой. Ошибки нет, предупреждения нет,
golden-тесты зелёные — они считают заново, а не читают кэш.

Сегодня дефект латентный: резолвер ещё не подключён к application/bootstrap,
а `cli.py` идёт мимо кэша. Эта задача реализует и интеграционно проверяет
**механизм** B-7 на уровне calculation block. Startup-вызов ровно один раз и
передача значения в application будут подключены будущим `bootstrap.py`.
До этого не утверждать, что существующее приложение уже выполняет fail-fast
на старте.

## 2. Создать `src/exact_orb/calculation/version.py`

Публичный API:

```python
CALCULATION_VERSION_SCHEMA = "v1"
UNRESOLVED_DISTRIBUTION = "<unresolved>"

class CalculationVersionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_version: str
    profiles_digest: str
    swisseph_version: str
    distribution: str
    native_module_digest: str | None
    ephemeris_files: tuple[tuple[str, str], ...]
    selena_method: str
    body_ids_digest: str
    ephemeris_flags: int

def compute_calculation_version_record(
    *,
    ephemeris_path: str | os.PathLike[str],
    selena_method: str,
    body_ids: Mapping[str, int],
    ephemeris_flags: int,
) -> CalculationVersionRecord: ...

def calculation_version_of(record: CalculationVersionRecord) -> str: ...

def compute_calculation_version(
    *,
    ephemeris_path: str | os.PathLike[str],
    selena_method: str,
    body_ids: Mapping[str, int],
    ephemeris_flags: int,
) -> str: ...

def log_calculation_version(record: CalculationVersionRecord) -> None: ...
```

`UNRESOLVED_DISTRIBUTION` входит в хэшируемый payload и является частью
контракта схемы. Его значение нельзя менять как косметический текст: для
окружений без provider mapping это инвалидирует весь расчётный кэш и требует
осознанного изменения golden, а при изменении формы/смысла — подъёма
`CALCULATION_VERSION_SCHEMA`.

Семантика функций разделена явно:

- `compute_calculation_version_record()` — сборщик startup-снимка. Он читает
  файловую систему, import metadata и импортированный native module, поэтому
  **не является чистой функцией**. Он не меняет process state и не пишет лог;
- `calculation_version_of()` — чистая функция: только стабильная сериализация
  уже собранной записи и sha256;
- `compute_calculation_version()` — удобная композиция двух предыдущих
  операций без логирования;
- `log_calculation_version()` — отдельный startup-side effect. Будущий bootstrap
  вызовет его ровно один раз для уже собранной записи.

Модуль-константу `CALCULATION_VERSION`, вычисляемую при импорте, **не создавать**.
При импорте нельзя читать каталог эфемерид, выбирать биндинг или писать лог.
Итоговая строка будет локальным значением точки композиции и затем неизменяемым
аргументом `ChartArtifactResolver`.

## 3. Контракт startup-вызова

Параметры сборщика явные, чтобы тесты могли проверить разные методики и наборы
без повторной конфигурации process-wide состояния. Это означает, что сборщик
сам по себе не доказывает соответствие аргументов замороженной конфигурации.

Будущая точка композиции обязана соблюдать такой порядок и источники значений:

```python
status = configure_ephemeris(settings.ephemeris_path)
record = compute_calculation_version_record(
    ephemeris_path=status.path,
    selena_method=get_selena_method_name(),
    body_ids=DEFAULT_BODY_IDS,
    ephemeris_flags=DEFAULT_EPHEMERIS_FLAGS,
)
version = calculation_version_of(record)
log_calculation_version(record)
artifacts = ChartArtifactResolver(..., version=version)
```

В этой задаче этот код ни в `cli.py`, ни в несуществующий `bootstrap.py`
не добавлять.

Компонента `ephemeris_flags` означает эффективное значение **аргумента**
`ephemeris_flags`, с которым `NatalTechniqueAdapter` вызывает
`calculate_natal`. Единственным источником этого значения должна стать
`DEFAULT_EPHEMERIS_FLAGS`, см. §5. Внутреннее безусловное
`ephemeris_flags | swe.FLG_SPEED` является частью алгоритма движка и покрывается
`ENGINE_VERSION` и отпечатком биндинга; post-OR значение в компоненту 9
не передавать.

Компонента `body_ids` получает именно `DEFAULT_BODY_IDS`, применяемый ядром,
когда adapter не передаёт пользовательский набор. Передача произвольного
mapping точкой композиции запрещена контрактом, хотя тесты вправе подменять
аргумент для доказательства чувствительности отпечатка.

## 4. Состав записи — ровно девять компонент

```text
1  engine_version            ENGINE_VERSION из engine/__init__.py
2  profiles_digest           sha256 канонического JSON дефолтных
                             AspectConfig.natal(), AspectConfig.transit(),
                             ConfigurationConfig(), StrengthConfig()
3  swisseph_version          swiss_backend.swe.version
4  distribution              "<имя>==<версия>" либо "<unresolved>"
5  native_module_digest      sha256 файла .pyd/.so либо None
6  ephemeris_files           отсортированный кортеж пар (имя, sha256)
7  selena_method             имя методики
8  body_ids_digest           sha256 канонического JSON отсортированных пар
                             имя -> swe_id
9  ephemeris_flags           int
```

`CalculationVersionRecord` содержит именно эти девять полей. Версия схемы
не является десятой компонентой записи: `calculation_version_of()` добавляет
её в сериализуемую полезную нагрузку по правилам §8.

`ENGINE_VERSION`, `swiss_backend.swe.version` и фабрики дефолтных профилей
читать во время вызова сборщика, а не захватывать значениями default arguments
при импорте. Это требуется и для корректного startup-снимка, и для тестов
чувствительности к каждой компоненте.

Компонента 2 нужна потому, что `aspect_config`, `configuration_config` и
`strength_config` остаются за пределами текущего `ChartSpec`. Правка чисел
в их дефолтах не меняет спеку и без этой компоненты не меняла бы ключ.
Не ссылаться на несуществующее поле `ChartSpec.orb_profile`.

Компоненты 3–5 разделены: `swisseph.version` возвращает версию библиотеки
(`2.10.03`), одинаковую у `pysweph` и `pyswisseph` при разном API. Версия
дистрибутива ловит смену обёртки, хэш native module — пересобранный или
подменённый `.pyd/.so` при неизменившейся версии.

`ephemeris_path` в запись и хэшируемую нагрузку **не входит**. Путь — свойство
развёртывания: тот же набор файлов в `/opt/ephe` и `/app/ephe` обязан давать
один ключ. Абсолютных путей в записи не должно быть ни в каком виде.

## 5. ENGINE_VERSION

Добавить в `src/exact_orb/engine/__init__.py`:

```python
ENGINE_VERSION = "1"
```

Рядом — комментарий с правилом подъёма: значение поднимается при изменении
алгоритма расчёта или дефолтных конфигов; форматирование, комментарии,
докстроки и тесты его не меняют.

Это решение использует явную константу, а не хэш исходников. Хэш исходников
обнулял бы кэш при правках, не влияющих на числа.

В `src/exact_orb/engine/ephemeris/types.py` рядом с `DEFAULT_BODY_IDS` добавить
единый источник дефолтных флагов:

```python
DEFAULT_EPHEMERIS_FLAGS: int = swiss_backend.swe.FLG_SWIEPH
```

В сигнатуре `calculate_natal()` заменить прямой дефолт
`swiss_backend.swe.FLG_SWIEPH` на `DEFAULT_EPHEMERIS_FLAGS`. Числовое
поведение не меняется. Это не попутный рефакторинг, а необходимая связь
компоненты 9 с реальным дефолтом ядра: будущая композиция и
`calculate_natal()` обязаны ссылаться на один символ. `NatalTechniqueAdapter`
по-прежнему может не передавать аргумент явно.

Транзитную технику в этой задаче не менять: текущий `ChartSpec` и
`ChartArtifactResolver` обслуживают только natal/cosmogram. Её
frozen-параметры будут включены в контракт при появлении `TransitChartSpec`.

## 6. Дефолтные профили и body ids

Для `profiles_digest` сериализовать точную структуру:

```text
{
  "aspect_natal":        AspectConfig.natal().model_dump(mode="json"),
  "aspect_transit":      AspectConfig.transit().model_dump(mode="json"),
  "configuration":       ConfigurationConfig().model_dump(mode="json"),
  "strength":            StrengthConfig().model_dump(mode="json")
}
```

Использовать общий helper канонического JSON из §8. Порядок dict в моделях
не должен влиять на результат.

Для `body_ids_digest` хэшировать JSON-массив отсортированных по имени пар:

```text
[["chiron", 15], ["jupiter", 5], ...]
```

Не хэшировать `repr(mapping)` и не полагаться на порядок вставки.

## 7. Файлы эфемерид — компонента 6

Решение для отсутствующего каталога принимается явно: **отсутствующий каталог
является отказом старта cache-enabled application**. Fallback поддерживается
только при существующем каталоге, в котором нет `.se1` или присутствует лишь
часть файлов. Это намеренно отличает непримонтированный/ошибочный deployment
path от явно подготовленного fallback-каталога.

Сегодня `configure_ephemeris()` допускает отсутствующий путь и переводит
расчёт в fallback. Данная задача `config.py` и CLI не меняет, поэтому их текущее
поведение остаётся прежним. После появления bootstrap вычисление отпечатка
сделает отсутствующий каталог fail-fast; это осознанное сужение startup-
контракта для cache-enabled приложения, которое необходимо отдельно
зафиксировать в следующей документационной задаче вместе с уточнением Т-ЭФ-5
и README.

- каталог обязан существовать и быть каталогом;
- отсутствие каталога или путь не к каталогу дают
  `EphemerisConfigurationError`, а не сырой `FileNotFoundError`,
  `NotADirectoryError` или пустой отпечаток;
- перечислять все непосредственные `*.se1` в каталоге, не рекурсивно и не
  только `REQUIRED_EPHEMERIS_FILES`;
- сортировать полным детерминированным ключом `(name.casefold(), name)`, чтобы
  имена, различающиеся только регистром, не возвращали порядок файловой системы;
- в запись класть пары `(basename, lowercase_sha256_hex)`, без каталога;
- читать обычные файлы чанками, не целиком в память;
- ошибка чтения найденного `.se1` преобразуется в
  `EphemerisConfigurationError` с именем файла, но без полного пути;
- каталог существует, но `*.se1` в нём нет или найдена только часть — это
  валидный fallback-отпечаток с найденным набором;
- отдельного поля `mode` не вводить: files/fallback различаются набором
  найденных файлов.

## 8. Точная форма значения и канонизация

Строка:

```text
eo:calcver:v1:<sha256-hex>
```

Хэшируемая полезная нагрузка — плоский объект с точной формой:

```text
{
  "schema_version": "v1",
  "engine_version": ...,
  "profiles_digest": ...,
  "swisseph_version": ...,
  "distribution": ...,
  "native_module_digest": ...,
  "ephemeris_files": ...,
  "selena_method": ...,
  "body_ids_digest": ...,
  "ephemeris_flags": ...
}
```

То есть `schema_version` объединяется с
`record.model_dump(mode="json")` на одном уровне. Не оборачивать запись в ключ
`record` и не включать префикс в JSON.

Канонический JSON для этой нагрузки, профилей и body ids:

```python
json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
```

Затем sha256 и lowercase hex длиной 64. `CALCULATION_VERSION_SCHEMA` входит
и в payload, и в префикс.

Добавить golden-тест с полностью заданным `CalculationVersionRecord`.
В тесте независимо задать ожидаемый canonical JSON, вычислить из него ожидаемый
digest и проверить точную итоговую строку; не расширять публичный API только
ради доступа к промежуточному JSON. Golden менять только при намеренном
изменении схемы вместе с подъёмом `CALCULATION_VERSION_SCHEMA`.

## 9. Биндинг и native module

Swiss Ephemeris получать только через `exact_orb.swiss_backend`; прямой
`import swisseph` запрещён.

Компоненту 3 получать только из `swiss_backend.swe.version`. При сборке записи
проверить, что атрибут существует и является непустой строкой. Отсутствующее,
`None`, нестроковое или пустое значение даёт `EphemerisConfigurationError`.
Не подставлять версию Python-дистрибутива, пустую строку или иной fallback:
это сделало бы компоненту 3 фиктивной и вернуло дефект тихой неинвалидации.

Провайдеров модуля получать через
`importlib.metadata.packages_distributions().get("swisseph", [])`.

- повторяющиеся одинаковые имена дистрибутива дедуплицировать;
- больше одного уникального имени —
  `EphemerisBindingAmbiguousError(EphemerisConfigurationError)`;
- ровно одно имя — `"<имя>==<importlib.metadata.version(имя)>"`;
- ноль имён — точный маркер `UNRESOLVED_DISTRIBUTION`, без падения;
- если имя найдено, но его version metadata прочитать невозможно, поднять
  `EphemerisConfigurationError`: это повреждённая metadata, а не случай
  отсутствующего provider mapping.

Добавить в `src/exact_orb/errors.py`:

```python
class EphemerisBindingAmbiguousError(EphemerisConfigurationError): ...
```

Имя native module брать из `swiss_backend.swe.__file__`. Хэшировать файл,
только если путь существует, является обычным файлом и имеет suffix `.pyd`
или `.so`. Путь, его parent и `repr(module)` в запись не включать.

Если `__file__` отсутствует, не является native extension либо файл нельзя
прочитать, `native_module_digest=None`. Это допустимый, но ослабленный
отпечаток; предупреждение формируется `log_calculation_version()`, а не
сборщиком записи.

## 10. Журнал

`log_calculation_version(record)` вычисляет итоговую строку через
`calculation_version_of(record)` и пишет:

1. ровно одну INFO-запись с событием `calculation_version_computed`, итоговой
   строкой и всеми девятью компонентами записи;
2. если `native_module_digest is None`, дополнительно ровно одну WARNING-запись
   `calculation_version_weakened reason=native_module_digest_unavailable`.

В журнале разрешены basename файлов и их digest. Полного или относительного
пути каталога эфемерид быть не должно. Персональных данных в этих событиях нет.

`compute_calculation_version_record()`, `calculation_version_of()` и
`compute_calculation_version()` лог не пишут.

## 11. Границы модуля

`version.py` импортирует engine-типы и Swiss Ephemeris, поэтому:

- не экспортировать его из `calculation/__init__.py`;
- существующий
  `test_calculation_package_import_keeps_artifact_payload_out_of_package_init`
  обязан остаться зелёным;
- `keys.py` и `spec.py` не трогать: они остаются swisseph-free, а version для
  них по-прежнему opaque string;
- не добавлять import-time чтение файлов, import metadata или логирование.

## 12. Запреты

- не менять `ChartSpec`, `calculation_key`, `canonical_key_payload`,
  `schema_version` ключа и префикс `eo:calc:v1:`;
- не менять сигнатуру `ChartArtifactResolver.__init__`;
- не создавать или мутировать глобальную `CALCULATION_VERSION`;
- не читать окружение и `pyproject.toml` внутри `version.py`;
- не класть `ephemeris_path` ни в запись, ни в хэш;
- не включать версию `tzdata`;
- не трогать `cli.py`, `bootstrap.py`, `application/` и `docs/**`;
- не менять `pyproject.toml` и не добавлять зависимости;
- не исправлять соседние docstring/debt-комментарии — их синхронизация входит
  в отдельную документационную задачу.

## 13. Тесты

Создать отдельные тесты `tests/test_calculation_version.py`. Помечать
`no_ephemeris_autoinit` там, где автоконфигурация не нужна. Для файловых
случаев использовать `tmp_path`; реальный project `ephe/` не изменять.

### 13.1. Запись и строка

- полностью заданная запись даёт точную golden version, независимо вычисленную
  из зафиксированного в тесте canonical JSON;
- формат: `eo:calcver:v1:` + lowercase hex длиной 64;
- один и тот же record дважды даёт одну строку;
- два вызова `compute_calculation_version()` с одинаковыми аргументами и одним
  неизменившимся каталогом в одном процессе дают одну строку;
- параметризованно изменить каждую из девяти компонент record и доказать,
  что строка меняется;
- смена `ENGINE_VERSION` меняет запись и строку;
- дефолт параметра `calculate_natal.ephemeris_flags` через
  `inspect.signature` равен `DEFAULT_EPHEMERIS_FLAGS`;
- изменение дефолтного профиля меняет `profiles_digest` и строку;
- перестановка элементов исходного `body_ids` не влияет, изменение пары влияет;
- смена `selena_method`, `body_ids` и `ephemeris_flags` меняет строку;
- в canonical JSON записи нет строки переданного каталога.

### 13.2. Файлы эфемерид

- подмена байта в `.se1` меняет отпечаток;
- разный порядок создания/перечисления файлов не влияет;
- добавление лишнего `.se1` меняет отпечаток;
- каталог без `.se1` даёт валидный отпечаток, отличный от каталога с файлами;
- отсутствующий каталог и путь к обычному файлу дают
  `EphemerisConfigurationError`;
- нечитаемый/исчезнувший во время чтения `.se1` не выпускает сырой `OSError`;
- копия идентичных файлов в другом `tmp_path` даёт ту же строку;
- `PYTHONHASHSEED=1` и `PYTHONHASHSEED=2` в двух subprocess дают одну строку.

### 13.3. Биндинг и native module

- два уникальных дистрибутива для `swisseph` дают
  `EphemerisBindingAmbiguousError`;
- повтор одного имени не считается неоднозначностью;
- один дистрибутив даёт точную строку `name==version`;
- отсутствие provider mapping даёт `UNRESOLVED_DISTRIBUTION`;
- найденный provider с недоступной version metadata даёт
  `EphemerisConfigurationError`;
- отсутствующий, пустой или нестроковый `swiss_backend.swe.version` даёт
  `EphemerisConfigurationError`, без fallback на distribution version;
- `swiss_backend.swe.__file__` монкипатчится на временный `.pyd`/`.so`
  в `tmp_path`; подмена байта только в этом тестовом файле меняет
  `native_module_digest` и version, настоящий установленный бинарник не менять;
- отсутствующий или ненативный `swe.__file__` даёт `None`.

### 13.4. Логирование

- обычная запись даёт одну INFO `calculation_version_computed`;
- `native_module_digest=None` дополнительно даёт одну WARNING
  `calculation_version_weakened`;
- лог содержит все девять компонент и итоговую строку;
- лог не содержит переданный `ephemeris_path` и его parent;
- вычислительные функции без явного `log_calculation_version()` ничего
  не логируют.

### 13.5. Интеграционный B-7

Использовать один общий cache, один считающий fake engine и **два разных**
`ChartArtifactResolver`: старый и новый. Их версии вычислить по двум каталогам
с одинаковыми именами `.se1`, но разным содержимым.

Для одного `ResolvedBirthData` и одного `ChartSpec`:

1. первый resolver получает miss, вызывает engine и пишет старый artifact;
2. второй resolver получает другой `calculation_key`, не читает старое значение
   как hit и вызывает engine второй раз;
3. ключи и `calculation_version` двух артефактов различаются;
4. `resolver.version` после создания не мутировать.

Существующий тест смены произвольной строковой версии не заменяет этот тест:
новая проверка обязана связать изменение `.se1` с реальным ключом резолвера.

## 14. Порядок проверок

Запустить поэтапно:

1. `pytest tests/test_calculation_version.py -q`
2. целевые связанные тесты ключей, resolver и module boundaries;
3. полный `pytest`.

Не запускать сетевые или платные smoke-тесты.

## 15. Приёмка

- `src/exact_orb/calculation/version.py` создан;
- `ENGINE_VERSION = "1"` добавлен в `engine/__init__.py` с правилом подъёма;
- `DEFAULT_EPHEMERIS_FLAGS` добавлен рядом с `DEFAULT_BODY_IDS` и используется
  как дефолт `calculate_natal()` и как startup-вход компоненты 9;
- `EphemerisBindingAmbiguousError` добавлен в `errors.py`;
- record содержит ровно девять компонент, schema добавляется только в payload;
- `ephemeris_path` отсутствует и в record, и в payload, и в логах;
- только `calculation_version_of(record)` объявляется чистой функцией;
- import модуля не выполняет I/O, не вычисляет version и не пишет лог;
- модульной `CALCULATION_VERSION` нет;
- `version.py` не экспортируется из `calculation/__init__.py`;
- прямого `import swisseph` нет;
- `ChartSpec`, `calculation_key`, resolver и формат `eo:calc:v1:` не изменены;
- документация и bootstrap не менялись;
- интеграционный тест связывает изменение `.se1` с miss общего cache;
- полный `pytest` зелёный.

В итоговом отчёте:

- кратко объяснить разделение I/O-сборщика, чистого хэширования и логирования;
- перечислить фактические изменения;
- привести точные команды и реальные результаты тестов;
- вывести состав отпечатка текущего окружения без абсолютных путей;
- отдельно указать, что startup wiring и синхронизация `docs/**` отложены
  в следующие задачи, поэтому application-level fail-fast пока не подключён;
- перечислить обнаруженные противоречия действующей документации, не исправляя
  их в этой ветке.

Коммит не создавай — он будет подготовлен отдельной командой после проверки
результата.
