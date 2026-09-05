# Блок сессий, P3: ContextService

Работай в ветке feat/session-context.

P1 ввёл immutable-модели, outcomes, типизированные persistence errors,
чистые правила и порты SessionStore, DialogStore и SessionPersistence. P2
предоставил InMemorySessionPersistence и общий conformance-набор. P2.1 сделал
require_utc публичным контрактом и запретил потребителям контрактов
импортировать их приватные имена.

В этой задаче реализуй только ContextService — единственную границу блока
сессий и владельца семантической классификации persistence outcomes.
Application-команды, handlers, ApplicationOrchestrator, bootstrap.py, SQLite,
reaper и Research Corpus сюда не входят.

## 0. Preflight

Прочитай корневой AGENTS.md и выполни:

    git rev-parse --show-toplevel
    git branch --show-current
    git status --short
    git log -8 --oneline

Если каталог не является Git-репозиторием, .git отсутствует, активна другая
ветка либо в истории нет P1, P2 и P2.1, остановись. Не выполняй git init и не
реконструируй репозиторий.

Убедись, что существуют adapters/_time.py, adapters/in_memory.py,
tests/session/conformance.py и tests/session/test_in_memory.py, а публичный
импорт exact_orb.session.require_utc работает. Сохрани пользовательские и
несвязанные изменения.

До реализации запусти:

    python -m pytest -q tests/session tests/test_module_boundaries.py

Если baseline падает, зафиксируй падения и не исправляй посторонние дефекты.

Изучи session/__init__.py, errors.py, state.py, outcomes.py, dialog.py,
store.py, persistence.py, adapters/in_memory.py; тесты session и
test_module_boundaries.py; session requirements, build natal components,
negative corner scenarios; ADR-0009, ADR-0014 и decisions/README; session
diagrams 001–005 и их README.

prompts/** — исторический журнал. Старые промты не редактируй.

## 1. Цель и допустимые файлы

Создай:

    src/exact_orb/session/context.py
    tests/session/test_context.py

При необходимости измени только:

    src/exact_orb/session/outcomes.py
    tests/session/test_contracts.py
    tests/test_module_boundaries.py
    docs/requirements/component_responsibilities/exact-orb_session_requirements.md
    docs/requirements/component_responsibilities/exact-orb_build_natal_components.md
    docs/requirements/decisions/0009-context-yes-profiles-later.md
    docs/requirements/decisions/0014-explicit-state-mutations.md
    docs/requirements/decisions/README.md
    docs/sequence_diagrams/session/001-natal-session-lifecycle.puml
    docs/sequence_diagrams/session/002-session-restore-on-return.puml
    docs/sequence_diagrams/session/003-session-store-read-failure.puml
    docs/sequence_diagrams/session/004-session-reset-and-delete.puml
    docs/sequence_diagrams/session/005-compare-and-set.puml
    docs/sequence_diagrams/session/README.md

Не экспортируй ContextService из exact_orb.session.__init__. Корневой пакет
остаётся contract-only. Сервис импортируется из exact_orb.session.context.

P1 явно намечал load, save, reset_all, append_turn и clear_dialog. Create и
delete добавляются осознанно: ContextService является единственным владельцем
persistence на границе блока, поэтому lifecycle create/delete не обходят его.
Transport-обязанности при этом не переходят в session.

## 2. Публичный API

ContextService имеет keyword-only конструктор:

    __init__(self, *, persistence: SessionPersistence,
             clock: Callable[[], datetime])

Публичные async-методы:

    create(session_id)
      -> SessionCreated | SessionIdConflict | StateCommitFailed
    load(session_id)
      -> SessionSnapshot | SessionAbsent | StateReadFailed
    save(session_id, expected_state_version, delta)
      -> Committed | AlreadyApplied | Superseded |
         SessionAbsent | StateCommitFailed
    append_turn(session_id, turn)
      -> None | SessionAbsent | StateCommitFailed
    clear_dialog(session_id)
      -> None | SessionAbsent | StateCommitFailed
    reset_all(session_id, expected_state_version)
      -> Committed | AlreadyApplied | Superseded |
         SessionAbsent | StateCommitFailed
    delete(session_id)
      -> None | StateCommitFailed

Не вводи service Protocol, дополнительный repository/facade, новые success
outcomes, idempotency_key, BuildAttempt, auto-retry, auto-rebase или
зависимость от concrete adapter. Сервис получает один SessionPersistence, а
не два независимо созданных фасета.

## 3. Clock

Публичные методы не принимают now. Create, load, save, append_turn,
clear_dialog и reset_all на каждый отдельный публичный вызов выполняют ровно:

    now = require_utc(clock(), name="clock")

Clock читается один раз на вызов, поэтому два save в N7/N8 дают два чтения
clock, по одному на каждый save. Полученный объект передаётся persistence по
identity без нормализации и повторного чтения.

Если clock сам поднимает исключение, оно выходит без изменения. Если он
возвращает naive datetime или ненулевой offset, до persistence возникает
ошибка типа ровно ValueError; сообщение содержит clock. Не связывай тест со
всей строкой сообщения require_utc. Во всех этих ветках persistence не
вызывается.

Delete clock не читает. Default clock и скрытые datetime.now, utcnow,
time.time, monotonic или loop.time запрещены.

## 4. Routing операций

Create вызывает только persistence.sessions.create с единым now. Он не
генерирует ID, не читает conflict, не делает retry/upsert/touch и не удаляет
expired row. SessionCreated и SessionIdConflict возвращаются без изменения.

Load вызывает ровно persistence.touch. SessionSnapshot возвращается по
identity — result is snapshot — и не пересобирается из get/read. SessionAbsent
сохраняется. Старый или частичный snapshot после failed touch запрещён.

Save вызывает ровно один sessions.compare_and_set с исходными session_id,
original expected_state_version, тем же объектом delta и единым now. Нет
предварительного или последующего get, apply_delta, retry и rebase.

Append_turn вызывает только dialogs.append, передаёт исходный DialogTurn по
identity, не проверяет marker, не применяет лимиты и не вызывает CAS.
Clear_dialog вызывает только dialogs.clear и не вызывает CAS/reset/get/read.

Reset_all вызывает только aggregate reset. Его нельзя реализовывать через
clear + CAS или прямой facet CAS.

Delete вызывает только aggregate delete, не читает clock, не вызывает фасеты,
не гасит cookie и не создаёт новую сессию.

## 5. Total persistence error mapping

Лови общий SessionPersistenceError только вокруг persistence-вызова. Mapping
определяется видом публичной операции, а не подклассом исключения:

    load + любой SessionPersistenceError
      -> StateReadFailed с тем же error_code

    create/save/append_turn/clear_dialog/reset_all/delete
      + любой SessionPersistenceError
      -> StateCommitFailed с тем же error_code

Touch, поднявший StateWriteError, всё равно даёт StateReadFailed. CAS,
поднявший StateReadError, всё равно даёт StateCommitFailed. Так concrete
adapter не выпускает сырой persistence exception из-за выбора другого
подкласса.

StateReadFailed означает, что обязательный load-and-renew не завершён. Он не
различает «не удалось прочитать» и «данные прочитаны, но не подтверждено
продление TTL». Это сознательный fail-closed контракт: частичный snapshot не
выдаётся, но outcome сам по себе не доказывает, что persisted session утрачена
или уже истекла. Будущий application не сообщает об утрате сессии только на
основании StateReadFailed.

Не лови Exception, BaseException, CancelledError, ValueError или
pydantic.ValidationError. Не логируй raw exception, session_id, birth data или
dialog text.

Error code переносится без нормализации или fallback. Непустой error_code —
обязанность persistence adapter. Пустой код не маскируется; возникший при
построении outcome ValidationError выходит как нарушение adapter-контракта и
исправляется в P4.

## 6. Общая commit-классификация

Save и reset_all используют один private pure helper:

    int -> Committed(result)
    SessionAbsent -> тот же объект
    VersionConflict(actual) + matches_intent(actual, delta)
      -> AlreadyApplied(actual.state_version)
    VersionConflict(actual) + mismatch
      -> Superseded(actual)

Helper не читает clock/persistence, не меняет actual, не делает get/retry,
не подменяет expected и не строит state candidate.

AlreadyApplied.state_version меняется на ge=0. Committed остаётся ge=1.
AlreadyApplied(0) допустим только для empty fresh actual и RESET_DELTA.
Committed(0), ChartRef version 0 и DialogTurn marker 0 остаются запрещены.

Superseded означает «actual не соответствует intent», а не обязательное
доказательство проигранной гонки. Это включает fresh actual версии 0 против
populated delta с завышенным expected. Будущий application использует
нейтральное сообщение и не утверждает без доказательства, что другой запрос
успел раньше.

Save с RESET_DELTA допустим: facet CAS уже является каноническим reset-aware
путём и атомарно очищает state/dialog. Он наблюдаемо эквивалентен reset_all на
эквивалентных lifecycle. Reset_all существует ради явности application-intent
и всё равно обязан вызывать aggregate reset.

## 7. Retry N7/N8

Сервис сам retry не организует. Повторный публичный save получает ту же пару
original expected + delta.

- первый commit не состоялся: повтор может дать Committed;
- commit состоялся, ответ потерян: conflict same intent даёт AlreadyApplied;
- actual уже отражает другое intent: Superseded;
- persistence снова отказал: StateCommitFailed.

При двух одинаковых save с одним original expected версия растёт ровно на
единицу. Исторического журнала intent нет; поздний retry X после перехода к Y
даёт Superseded.

## 8. Тестовая архитектура

В tests/session/test_context.py создай детерминированные recording fakes для
aggregate SessionPersistence, SessionStore facet, DialogStore facet и clock.
Они возвращают заданный outcome или поднимают заданный SessionPersistenceError,
записывают точные аргументы, падают при неожиданном вызове и не копируют
InMemory algorithms.

Проверь runtime соответствие:

    isinstance(fake_persistence, SessionPersistence)
    isinstance(fake_persistence.sessions, SessionStore)
    isinstance(fake_persistence.dialogs, DialogStore)

Проверь inspect.signature(ContextService.__init__): ровно self, keyword-only
persistence и clock. Через inspect.signature каждого публичного метода
проверь отсутствие now. Не заменяй эти проверки косвенными вызовами.

Для total mapping параметризуй StateReadError и StateWriteError для read-like
и mutating операций. Для N7/N8 используй реальный InMemorySessionPersistence.
Один clock-read относится к одному публичному вызову; два save должны дать
два чтения.

Не используй sleep, случайные задержки, реальное время, сеть, SQLite, LLM или
engine. Нумерованные требования — assertions, а не отдельные функции; применяй
параметризацию.

P1 acceptance 1–9 покрывается P3. Пункт 10 разделён: P3 доказывает один
aggregate reset, mapping и отсутствие отдельного clear; P2 conformance
закрепляет канонический reset и conflict non-mutation; rollback SQLite при
infrastructure failure требует fault injection и остаётся P4. Не заявляй, что
recording fake доказал rollback реального adapter.

## 9. Обязательная тестовая матрица

Проверь минимум:

1. Точную сигнатуру конструктора через inspect.signature.
2. Отсутствие now во всех публичных методах через inspect.signature.
3. Runtime Protocol всех трёх fake-объектов.
4. Один clock-read на каждый now-bearing публичный вызов и identity now вниз.
5. Delete не читает clock.
6. Clock exception выходит без persistence-вызова.
7. Naive и non-zero-offset clock result дают ровно ValueError, сообщение
   содержит clock, persistence не вызван.
8. Create вызывает только sessions.create; success/conflict сохраняются;
   оба persistence error subclass дают StateCommitFailed с тем же кодом.
9. Load вызывает только touch; snapshot возвращается по identity; оба absence
   сохраняются; оба error subclass дают StateReadFailed с тем же кодом; нет
   get/read или старого snapshot.
10. Save передаёт original expected и delta по identity, CAS вызывается один
    раз, дополнительного get/apply_delta/retry/rebase нет.
11. Int/absence/same intent/different intent классифицируются в
    Committed/тот же absence/AlreadyApplied/Superseded.
12. Различие только birth_input intent не меняет.
13. Actual version 0 + RESET_DELTA даёт AlreadyApplied(0); actual version 0 +
    populated intent даёт neutral Superseded.
14. AlreadyApplied(0) валиден, отрицательная версия и Committed(0) невалидны.
15. Оба persistence error subclass CAS дают StateCommitFailed, а не conflict.
16. Два concurrent same-intent save дают один Committed и один AlreadyApplied,
    версия +1, clock вызван дважды — по разу на save.
17. Sequential retry сохраняет original expected, не делает load/rebase и
    после потерянного ответа даёт AlreadyApplied; другое intent даёт
    Superseded.
18. Append передаёт DialogTurn по identity, marker не валидируется, success /
    absence / оба error subclass классифицируются корректно, CAS не вызван.
19. Clear вызывает только facet clear; success / absence / оба error subclass
    классифицируются корректно.
20. Reset_all вызывает только aggregate reset; success/absence/conflicts/оба
    error subclass классифицируются корректно; отдельный clear не вызван.
21. Save(RESET_DELTA) и reset_all на эквивалентных lifecycle дают одинаковые
    outcomes для success, absence и обоих conflict intent. Это поведенческая
    проверка общей таблицы; запрещены assertions по имени или identity private
    helper.
22. Delete вызывает только aggregate delete, не читает clock и корректно
    отображает оба error subclass.
23. Все непустые error_code переносятся точно, str(exc)/fallback не
    используются; пустой код не маскируется.

## 10. Module boundaries

Добавь exact_orb.session.context как service-модуль, но не contract/adapter.
Discover service files по дереву, а не фильтрацией только известного списка.
Context может импортировать из проекта только exact_orb.session.* и не может
зависеть от adapters, birth, calculation, config, application, agent,
orchestration, tools, llm, cli, engine или swiss_backend.

Распространи P2.1 AST-инвариант приватных контрактных импортов на adapters и
service consumers. Разрешай relative imports через _resolve_relative. Private
helper внутри context.py допустим; импорт private contract name запрещён.
Добавь позитивный контроль для обоих consumer kinds.

Добавь exact_orb.session.context в SESSION_FORBIDDEN_AT_RUNTIME, чтобы чистый
import exact_orb.session не загружал context или adapters.

Для чистого import exact_orb.session.context нельзя использовать этот список
целиком: из него вычитается сам проверяемый service module. Введи:

    SESSION_SERVICE_FORBIDDEN_AT_RUNTIME = tuple(
        module
        for module in SESSION_FORBIDDEN_AT_RUNTIME
        if module != "exact_orb.session.context"
    )

Subprocess-тест service import использует именно этот список, имеет positive
control ContextService и запрещает swisseph, sqlite3, aiosqlite, adapters и
application/runtime слои. Статически запрети hidden clock, UUID и randomness.

## 11. Документация

Точечно синхронизируй session requirements и build natal §6.3: семь операций,
осознанные create/delete, injected clock + require_utc до persistence, routing,
total SessionPersistenceError mapping по операции, identity snapshot,
AlreadyApplied(0), neutral Superseded, save(RESET_DELTA), отсутствие
get/retry/rebase, non-empty error code contract и разделение reset rollback.

StateReadFailed документируй как fail-closed failure всей load-and-renew
операции: он может означать failure обязательного renewal после успешного
чтения и не доказывает утрату session. Будущий application не сообщает утрату
только по этому outcome.

ADR-0009 ревизуй как владельца read-and-renew: зафиксируй принятую
неоднозначность StateReadFailed, отказ от partial snapshot и нейтральную
интерпретацию application. Обнови revision и decisions/README.

ADR-0014 ревизуй: AlreadyApplied intent semantics и version 0; Committed ge=1;
Superseded как mismatch, а не доказательство winner; нейтральный future UI;
единая классификация save/reset и канонический RESET_DELTA-aware CAS. Обнови
revision и decisions/README.

Session diagrams 001–005 приведи к injected clock API: caller не передаёт now;
service один раз читает и валидирует clock; persistence получает тот же now;
invalid clock не достигает persistence; delete clock не читает; ошибки
отображаются по операции; StateReadFailed не означает доказанную утрату;
Superseded подписан как mismatch; AlreadyApplied(0) только empty reset intent.
Не переписывай соседние сценарии.

Stale bootstrap example не исправляй: wiring относится к application-задаче.

## 12. Что не входит

Не реализуй application commands/handlers/orchestrator/HTTP mapping/cookies/ID
generation/bootstrap/rename orchestration; SQLite/schema/migrations/reaper/
rollback/fault mapping/cross-process handles; P5 corpora/consent/projection.
Не добавляй зависимости и не меняй P2 adapters/conformance без выявленного
нарушения уже принятого контракта.

## 13. Проверки

Запускай поэтапно:

    python -m pytest --collect-only -q tests/session/test_context.py
    python -m pytest -q tests/session/test_context.py tests/session/test_contracts.py tests/test_module_boundaries.py
    python -m pytest -q tests/session tests/test_module_boundaries.py
    python -m pytest -q
    git diff --check

Приведи фактическое число collected tests; нулевой или неожиданно малый набор
разбери, а не подгоняй. Не запускай отсутствующие quality gates, платные,
сетевые или LLM smoke tests.

Если локальный PlantUML renderer доступен, реально отрендери изменённые
session/001–005. Не утверждай render success без запуска и не коммить
неотслеживаемые изображения.

## 14. Acceptance

P3 завершён, когда ContextService и test_context созданы; API/clock signatures
проверены механически; fakes соответствуют runtime Protocol; clock валидируется
один раз на публичный вызов до persistence; error mapping тотален по виду
операции; snapshot identity и отсутствие fallback доказаны; commit
классификация тотальна для version 0; Superseded нейтрален; save RESET_DELTA и
reset_all поведенчески эквивалентны при разном routing; N7/N8 не делают rebase;
root package остаётся contract-only; context включён в forbidden runtime и
private-import boundary; docs/ADR/diagrams синхронизированы; collect-only,
целевые, session и full pytest фактически запущены; P4/P5/application не
реализованы; коммит без отдельной команды не создан.

## 15. Итоговый отчёт

Начни с результата. Укажи публичный API; причину create/delete; clock и его
валидацию; total error mapping и принятую неоднозначность StateReadFailed;
AlreadyApplied(0) и neutral Superseded; отсутствие get/retry/rebase;
save(RESET_DELTA) против reset_all; Protocol-проверку fakes; обновлённые docs и
диаграммы; команды, результаты и collected count; факт PlantUML render;
сохранённые user changes; stale bootstrap; незакрытые SQLite rollback,
independent handles и empty error-code enforcement; ограничение, что concurrent
reset не fences уже выполняющийся dialog append.

Не называй P4, P5 или application реализованными.
