# TASK-T-02 — независимая проверка M1-9

2026-11-02, Tester. ProductionSHA / локальная проверенная поставка:
`6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5`.

**30 карточек PASS; 0 FAIL, 0 NOT RUN, 0 BLOCKED. Новых BUG/DP нет.**
Это результат проверки Tester; интеграция и приёмка Owner не выполнялись.
Единственный SKIPPED полного pytest — существующий DEBT-CALC-001,
он не включён в PASS.

## База и методика

Исходный worktree `C:/Users/KateUser/.codex/worktrees/f7fa/exact-orb-recovered`
был чистым на detached `9f36ee8`. После чтения задания из основной рабочей копии
переключён на указанный в нём опубликованный коммит `6db88e0` без создания ветки.
TASK-T-02 был untracked в основной копии; перенесён только этот файл задания.
Её чужие change.md, events.jsonl и untracked-файлы не изменялись.
В опубликованной базе change.md ещё содержит исторический APPROVAL;
явное задание Owner и TASK-T-02 задают проверку READY_FOR_TEST. Tester не менял
статус изменения и не запускал оркестратор.

До чтения production-кода и Developer-тестов прочитаны готовый тест-план,
инкремент, действующие требования, ADR-0034, три sequence и TASK-O-02.
Источники ожидаемого остались прежними. Затем сопоставлено существующее покрытие:

- `tests/ui/terms.test.mjs`: поздний initial/current/build, пустой draft, recovery,
  retained DOM, фокус и disclosures; повторно выполнен в общем UI-прогоне.
- `tests/ui/session.test.mjs`, `form.test.mjs`: HTTP/recovery, candidates/constraints,
  ошибки полей, Retry-After, explicit retry, исходные gate и HH:MM/null.
- `tests/ui/facts.test.mjs` и остальные UI-тесты: full golden, первые пять строк,
  раскрытия, natal/cosmogram, сохранение выбора и формы, отказ изображения.
- `tests/http_api`: доставка, schema-validation, installed wheel, HTTP DTO,
  correlation/admission, сессия и application-путь. PASS этих тестов получен
  собственным запуском, из отчёта Developer не переносился.

Новые проверки находятся в `tests/acceptance/`. Переиспользованы только общие
`tests/ui/fixtures/dom.mjs`, `session.mjs`, HTTP goldens, общий HTTP client stand
и `tests/fixtures/application.py`. Реальны mount/form/places/session/transport/result,
а в HTTP-проверке также API, application, resolver, engine, cache и persistence.
В браузере заменена только HTTP-сеть фиксированными публичными DTO и каталогом;
HTML/CSS/modules отдаются с диска без модификации. DOM-port не используется
как доказательство браузерной геометрии или клавиатуры.

Свежая оценка: 16 чч / 3 мч, confidence medium; ожидание исправлений не включено.

## Окружение и команды

Windows, Python 3.14.0 / pytest 9.0.2, Node 24.22.1,
настоящий Google Chrome **155.0.8059.40**, headless, Playwright из существующего
bundled runtime. Новые зависимости не устанавливались. Browser runner использует
обычный Chrome (`TERMS_BROWSER_CHANNEL` позволяет выбрать другой установленный channel).
Нет `sleep`; concurrency управляется deferred/barrier и fake clock;
ожидания browser DOM/HTTP — readiness, timeout служит защитой от зависания.

Команды из корня worktree, native exit code везде 0:

| Команда | Результат | Evidence |
| --- | --- | --- |
| `python -m pytest tests/acceptance -q -s --tb=short --show-capture=no` | 17 PASS, 23.45 с | [acceptance.log](acceptance.log) |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP | [node-related.log](node-related.log) |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS, 36.40 с | [pytest-related.log](pytest-related.log) |
| `python -m pytest -q` | 2977 PASS, 1 SKIPPED, 174.33 с | [pytest-full.log](pytest-full.log) |
| `python scripts/req_coverage.py docs/project_management/changes/terms-of-use --matrix` | 9/9 REQ, 2978 тестов собрано, пробелов нет | [req-matrix.md](req-matrix.md) |
| `python docs/project_management/changes/terms-of-use/plans/tester_evidence/verify_public_source.py` | PASS, анонимный public ref и exact tree | [public-source.json](public-source.json) |
| `python docs/project_management/changes/terms-of-use/plans/tester_evidence/audit_documents.py` | PASS, approval и отрицательные контроли C7 | [document-audit.json](document-audit.json) |
| `node docs/project_management/changes/terms-of-use/plans/tester_evidence/supplemental.mjs` | 24 PASS, явные сочетания T-02/08/15/16 | [supplemental.log](supplemental.log) |

Для сохранения browser JSON/PNG при целевом прогоне был задан
`TERMS_EVIDENCE_DIR=<absolute path to this directory>`. Без этой переменной
pytest использует свой временный каталог; повторный полный прогон не переписывает
сохранённые evidence. Сначала выполнены приёмочные, затем связанные, затем полный
pytest, затем req coverage. Ранние ошибки собственного harness исправлены до этого
зелёного цикла: невалидный current fixture, опечатка selector и неверное имя peer;
продуктовыми дефектами они не считались. Sandbox блокировал localhost браузера
и DNS, поэтому итоговые runtime/сетевые проверки выполнены вне sandbox.

## Браузер и Q44

80 примеров: 1 сверка текста/оформления, 20 keyboard/viewport,
27 trusted-pointer probes, 12 новых загрузок, 20 native-input/build.
[presentation.json](presentation.json), [keyboard.json](keyboard.json),
[targets.json](targets.json), [reload.json](reload.json), [builds.json](builds.json).

У ссылки и пояснения совпали computed font family/size/style/weight:
Arial/sans-serif, 13 px, normal, 400. Ширины 359/360/361/768/1440 CSS px:
overflow 0; на 360 px доступны полный текст и обе кнопки, Tab/Shift+Tab,
Enter/Space, focus-visible и четыре строки T. Ссылка и checkbox действуют раздельно.
Реальный `maxlength=5` оставляет от `-00:01` строку `-00:0`; build с ней запрещён.
Невалидная native date проверена как доступное пустое поле, без инъекции
невозможной даты в приватное состояние браузера. DOM-port отдельно проверил
календарный отказ `2025-02-30`.

Q44 измеряется после прокрутки цели в центр viewport. Проверяется прямоугольник
44×44 CSS px внутри её bbox: сетка 44×44 точек с шагом 1 px плюс пробы .01/43.99
по всем краям. Каждый hit должен принадлежать именно цели или её потомку.
Дополнительно 9 trusted mouse clicks на каждой цели проверяют `isTrusted`,
получателя, фактический переход и checkbox. Размер bbox не подменяет hit-testing.
Контроль 44×44 проходит; 43×44, 44×43, overlay и clipped отвергаются.
Trusted click по overlay получает перекрывающий button. Контроль clipping
потребовал проб у субпиксельных краёв; midpoint-only sweep был недостаточен.
Первый замер ссылки у нижнего края viewport был неопределён из-за clipping
самим viewport; центральный замер исключил этот артефакт без изменения порога.

Скриншоты [страницы 360 px](terms-mobile.png),
[возврата «Согласен»](keyboard-agree.png), [возврата без согласия](keyboard-back.png)
просмотрены визуально. Полная страница длинная; таблица и весь текст доступны
вертикальной прокруткой. Screen-reader не проверялся.

## Утверждение текста и C7

Q взят из утверждённого пакета `02cbd17e33ceffe52d465bdf6b8faf1d3c76864c`;
hash UTF-8/LF `ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`.
Browser innerText совпал после нормализации только пробелов и Markdown-разметки,
с сохранением всех слов, строк таблицы, контакта и ссылок. Сами href сверены отдельно.

Без token/cookie/credential helper проверены public GitHub repository,
`refs/heads/change/terms-of-use` → ProductionSHA и commit tree
`c22ac718625d53610a36239b006b9256527dec06`. Tree равен локальному Git tree:
это соответствие полного набора исходников, а не одной доступной главной страницы.
Также raw index.html, main.mjs, styles.css и LICENSE побайтно равны Git blobs.
Ссылка со страницы — `https://github.com/ksenia-baranova/exact-orb-demo`,
без оплаты/авторизации; HTML страницы получен анонимным HTTPS.
Контроли evidence со статусом BLOCKED, private=true и другим SHA отвергаются.
Они проверяют измеритель; недоступность реального сервиса не инсценировалась.

T-25 выполнен документально на историческом пакете
`a362a9eb236cca59c01d3fcb885ca74faf57c448`: DP-A-01 уже ACCEPTED,
полный текст ещё явно не утверждён, TASK-O-02 отсутствует. Этот пакет не засчитан
утверждённой поставкой. Позитивный контроль — отдельное позднейшее решение
TASK-O-02 и exact hash Q. DEBT-UI-001 не закрыт Tester.

## Чувствительность тестов

`TERMS_BAD_ORACLE=1 node tests/acceptance/terms_acceptance.mjs <scenario>`:
roundtrips, gates, payload, current, recovery — каждый exit 1
на контролируемо неверном ожидаемом checkbox / числе POST / birth_time.
[red-controls.log](red-controls.log).

`TERMS_BAD_ORACLE=1 python -m pytest 'tests/acceptance/test_terms_ui.py::test_terms_browser[presentation]' -q --tb=short`:
exit 1 на неверном ожидаемом email; [red-content.log](red-content.log).
Production и Q не менялись, переменная действовала только в отдельных процессах.
Обычный приёмочный/полный прогон после контроля — зелёный.
Q44 положительные/отрицательные контроли выполняются при каждом запуске targets.

<a id="coverage"></a>
## Карта evidence по карточкам

Все строки таблиц и заданные произведения примеров PASS. Где контракт сохраняет
старое поведение, результат складывается из новых проверок связи с условиями
и собственного повторного запуска существующих подробных проверок компонента.
Существующие тесты не переписывались и не копировались.

| Карточки | Собственная проверка / повторно исполненное покрытие |
| --- | --- |
| T-01 | browser presentation: текстовая ссылка под checkbox, 4 computed font свойства |
| T-02 | roundtrips: D1/D2/D3 × оба возврата × оба checkbox, без валидационного запрета чтения |
| T-03 | browser builds: check/uncheck без чтения и POST, отдельный explicit build |
| T-04/05 | roundtrips: T1…T4, полный D, видимый editor/focus, 0 POST |
| T-06 | roundtrips: повтор после ручного снятия и изменения на 23:59 |
| T-07 | roundtrips: 00:00/12:00/23:59 × 2 возврата × 2 checkbox + explicit HH:MM |
| T-08 | roundtrips: пустое/12:00 × 2 × 2, unknown отдельно, explicit null; session/form regression — снятие unknown |
| T-09 | roundtrips: все 5 D3 × 2 × 2, ID/название/query/raw отдельно, changed D при A |
| T-10 | isolation: empty/A × 2 × 2, повторная активация; payload/builds — положительный POST-контроль |
| T-11/12 | gates: 4 G1, 2 G2, удержанный первый ответ и сохранение D |
| T-13 | gates: 6 invalid × 2 способа; browser builds — native controls и реальный place selection |
| T-14 | payload: 4 времени × 2 способа, exact 3 keys, ожидание и D; browser builds |
| T-15 | payload/builds: committed после обоих способов; facts/full UI regression — full DTO, первые 5/раскрытия, чат, natal/cosmogram, collapse/draft |
| T-16 | current: ready/empty/unavailable × 2 способа, барьер перед current; session regression — actual B/facts и отсутствие гипотетической карты |
| T-17 | recovery: 20 примеров, оба способа, session-loss/429/503/504/lost/read-failed, fake clock, безопасный recheck и explicit retry; подробные ветви дополнены session/terms regression |
| T-18 | issues: 6 fields × 4 issue codes; 4 HTTP validation-before-cookie; session/HTTP regression — candidates/constraints и приоритеты |
| T-19/20/21 | browser reload: none/manual/page × reload/reopen × empty/A, retained browser context, checkbox=false и 0 POST |
| T-22 | exact payload + real snapshot/decoded artifact после реального build; schema без consent, нет persistence route; reload |
| T-23 | browser presentation: Q целиком, C1…C8, hrefs, отсутствие метаданных Analyst |
| T-24 | public-source.json + document-audit.json, anonymous exact tree и отрицательные контроли |
| T-25 | document-audit.json: пакет без approval против пакета с отдельным approval; долг не закрыт |
| T-26/27 | browser keyboard: 20 проходов, 5 ширин × 2 возврата × 2 checkbox |
| T-28 | browser targets: плотный hit-testing, 27 trusted probes, 5 размерных/overlay/clipping контролей |
| T-29 | current: 8 проходов, late B после обоих возвратов/checkbox, same/different identity; terms regression — выбор и 3 disclosures |
| T-30 | isolation + реальный API/application build trace: request_id=run_id, admission/orchestrator send/receive, load→handle→save, один terminal; current имеет собственный request_id |

Дополнительные 24 прогона в `supplemental.mjs`: одновременно частичное время
и невыбранный текст места (T-02); наблюдение скрытой строки после снятия unknown
для всех 8 сочетаний (T-08); committed natal/cosmogram после каждого способа
отметки, unchanged/edited draft, полные таблицы >5 и disabled chat (T-15);
actual ready B/empty/unavailable после обоих способов и барьера current (T-16).
Отличимая opaque identity B задана до выполнения, числовые факты взяты из golden.
Это дополнение к 17 pytest-проверкам; после полного pytest production и файлы
собираемых pytest-тестов не менялись.

Документация: 30 статусов PASS, таблицы согласованы, локальные ссылки существуют,
поля оркестратора сохранены — [document-check.json](document-check.json).
`git diff --check` и `git diff --cached --check` — PASS после удаления
концевых пробелов из сокращённой выдержки red-content.log.

## Ограничения

Проверена локальная поставка exact SHA. Удалённый развёрнутый сервис,
его конфигурация, screen-reader, browser zoom, юридическая достаточность,
доставка email, эксплуатационная готовность, интеграция и Owner acceptance
не проверялись. Эти проверки вне обязательных 30 карточек либо явно исключены
планом. Нет нового расчётного oracle. Существующий privacy-долг не переоткрывался.
Push, оркестратор, чужие задачи, requirements и production-код не изменялись.
