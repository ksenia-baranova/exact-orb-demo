---
id: TASK-T-02
change: terms-of-use
role: tester
kind: test
gate: READY_FOR_TEST
cycle: 1
inputs: [plans/test_plan.md, requirements.md]
origin: null
agent: null
model: null
status: DONE
resolution: done
raised_dp: []
raised_bugs: []
changed_reqs: []
reviewed_reqs: [REQ-UI-03, REQ-TERMS-01, REQ-TERMS-02, REQ-TERMS-03, REQ-TERMS-04, REQ-TERMS-05, REQ-TERMS-06, REQ-TERMS-07, REQ-TERMS-08]
commit: 6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5
estimate: {human_hours: 16, agent_hours: 3, confidence: medium}
---
## Задание
Независимо проверить M1-9 по [тест-плану](../plans/test_plan.md): 30 карточек, REQ-UI-03 и REQ-TERMS-01…08. База — коммит `6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5`, результаты [TASK-D-04](TASK-D-04.md). PASS Developer не переносить в свой отчёт.

Проверить:

- Оба способа отметки и оба возврата, сохранение ввода, поздние ответы/recovery, сброс отметки после reload и отдельное построение с прежним API.
- В настоящем браузере: клавиатуру, фокус, шрифт, 360 px и эффективные области 44 × 44 с положительными/отрицательными контролями из плана.
- Полный текст по редакции, утверждённой в [TASK-O-02](TASK-O-02.md), и соответствие публичного исходного кода точной версии поставки (C7). У Developer C7 остался NOT RUN; перепроверить текущую доступность. При отсутствии доказательств указать NOT RUN/BLOCKED с причиной, без push.

После чтения готового плана сопоставить его с существующим покрытием и переиспользовать фикстуры. Добавить независимые тесты в tests/acceptance/ с REQ-метками и Given/When/Then. Для высокорисковых тестов подтвердить падение на контрольной ошибке.

Запустить приёмочные → связанные → полный pytest, затем `python scripts/req_coverage.py docs/project_management/changes/terms-of-use --matrix`. Покрыть все 9 REQ; матрицу включить в результат задачи. Обновить статусы всех карточек и примеров, записать команды и точный SHA. На FAIL завести BUG по шаблону; свои исправленные баги перепроверить при наличии.

Production-код, требования, тесты Developer, чужие задачи и статус изменения не менять. Один коммит своих файлов. Итог кратко: PASS/FAIL/NOT RUN/BLOCKED, баги, ограничения и SHA. Оркестратор и push не запускать.

Правила — docs/development_approach/process/change-process-v3.md, раздел «Задача (Task)».

## Результат

Независимая проверка завершена 2026-11-02: **30 карточек PASS, 0 FAIL, 0 NOT RUN, 0 BLOCKED; BUG/DP нет**. Проверен production-коммит `6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5`; новые приёмочные тесты находились в рабочем дереве поверх него. Поле commit — проверенная версия реализации, не само-ссылка на коммит отчёта.

План, requirements, ADR, sequences и решение Owner прочитаны до реализации и Developer-тестов. Затем покрытие сопоставлено с существующими наборами. Добавлены независимые `tests/acceptance/test_terms_ui.py`, `test_terms_contract.py` и два JS runner; переиспользованы общие fixtures/goldens, production и Developer-тесты не изменялись. Обновлены статусы всех карточек и строк примеров в [плане](../plans/test_plan.md). Все 9 REQ проверены.

| Команда | Фактический результат |
| --- | --- |
| `python -m pytest tests/acceptance -q -s --tb=short --show-capture=no` | 17 PASS, 23.45 с; 133 примера композиции, 80 браузерных примеров, 5 HTTP-проверок |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS, 36.40 с |
| `python -m pytest -q` | 2977 PASS, отдельно 1 SKIPPED DEBT-CALC-001, 174.33 с |
| `python scripts/req_coverage.py docs/project_management/changes/terms-of-use --matrix` | 9 REQ / 9 с тестами; 2978 собрано; пробелов нет |
| `python docs/project_management/changes/terms-of-use/plans/tester_evidence/verify_public_source.py` | PASS: public exact ref/tree и побайтное соответствие assets/LICENSE |
| `python docs/project_management/changes/terms-of-use/plans/tester_evidence/audit_documents.py` | PASS: approval Q, отрицательный исторический пакет без approval и контроли C7 |
| `node docs/project_management/changes/terms-of-use/plans/tester_evidence/supplemental.mjs` | 24 PASS: явные сочетания T-02/08/15/16; production/pytest-тесты после полного прогона не менялись |
| `git diff --check`, `git diff --cached --check` | PASS; таблицы, ссылки и поля оркестратора также проверены |

Все перечисленные команды завершились с exit 0. Полные команды, журналы, сопоставление каждой карточки с новым/повторно исполненным покрытием и скриншоты — [evidence Tester](../plans/tester_evidence/README.md). Сначала приёмочные, затем связанные, затем полный pytest и coverage. NOT RUN и SKIPPED в PASS не переносились.

Настоящий Chrome 155.0.8059.40: keyboard/focus, font, 360 px и соседние/desktop ширины. Q44 подтверждён hit-testing сеткой с пробами у краёв, 27 trusted clicks с получателем и переходом; 44×44 положительный, 43 px/overlay/clipping отрицательные контроли. Видимый текст полностью совпал с утверждённым Q из `02cbd17e33ceffe52d465bdf6b8faf1d3c76864c`, hash `ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`.

C7 теперь PASS: без авторизации доступны репозиторий, `refs/heads/change/terms-of-use` → `6db88e0` и полный tree `c22ac718625d53610a36239b006b9256527dec06`, равный локальному. Страница исходного кода и raw files получены анонимным HTTPS. Это проверка точной локальной поставки и её опубликованного исходного кода, не утверждение о версии удалённого сервиса.

Проверки «на падение»: `TERMS_BAD_ORACLE=1 node tests/acceptance/terms_acceptance.mjs <scenario>` для roundtrips/gates/payload/current/recovery — каждый exit 1. Контроль неверного ожидаемого email: `TERMS_BAD_ORACLE=1 python -m pytest 'tests/acceptance/test_terms_ui.py::test_terms_browser[presentation]' -q --tb=short` — exit 1. Production/Q не менялись; переменная локальна отдельному процессу. Полный обычный прогон после контролей зелёный. Q44 и C7 имеют собственные позитивные/негативные контроли.

Матрица из фактического вывода `req_coverage.py`:

| REQ | Тесты |
| --- | --- |
| REQ-UI-03 | tests/acceptance/test_terms_contract.py::test_validation_before_cookie[None]<br>tests/acceptance/test_terms_contract.py::test_validation_before_cookie[acknowledged]<br>tests/acceptance/test_terms_contract.py::test_validation_before_cookie[consent_id]<br>tests/acceptance/test_terms_contract.py::test_validation_before_cookie[terms_version]<br>tests/acceptance/test_terms_contract.py::test_no_consent_persistence_and_build_trace<br>tests/acceptance/test_terms_ui.py::test_terms_composition[isolation]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[gates]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[payload]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[current]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[recovery]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[issues]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[reload]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[builds] |
| REQ-TERMS-01 | tests/acceptance/test_terms_ui.py::test_terms_composition[roundtrips]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[presentation]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[keyboard]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[builds] |
| REQ-TERMS-02 | tests/acceptance/test_terms_ui.py::test_terms_composition[roundtrips]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[payload]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[keyboard]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[reload]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[builds] |
| REQ-TERMS-03 | tests/acceptance/test_terms_ui.py::test_terms_composition[roundtrips]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[keyboard] |
| REQ-TERMS-04 | tests/acceptance/test_terms_ui.py::test_terms_composition[roundtrips]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[current]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[builds] |
| REQ-TERMS-05 | tests/acceptance/test_terms_contract.py::test_no_consent_persistence_and_build_trace<br>tests/acceptance/test_terms_ui.py::test_terms_composition[roundtrips]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[isolation]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[payload]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[current]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[builds] |
| REQ-TERMS-06 | tests/acceptance/test_terms_ui.py::test_terms_browser[presentation] |
| REQ-TERMS-07 | tests/acceptance/test_terms_contract.py::test_no_consent_persistence_and_build_trace<br>tests/acceptance/test_terms_ui.py::test_terms_composition[gates]<br>tests/acceptance/test_terms_ui.py::test_terms_composition[payload]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[reload] |
| REQ-TERMS-08 | tests/acceptance/test_terms_ui.py::test_terms_browser[keyboard]<br>tests/acceptance/test_terms_ui.py::test_terms_browser[targets] |

REQ в инкременте: 9; с тестами: 9; в «Не тестируем»: 0; тестов собрано: 2978
Пробелов нет.

## Findings

Функциональных расхождений с источниками не воспроизведено, новых BUG/DP нет. Старый Developer NOT RUN по C7 снят независимой текущей проверкой опубликованного кода. Подробности и контрольные результаты сохранены в evidence.

Файл задания был untracked в основной копии; опубликованная база ещё содержит исторический APPROVAL в change.md. Выполнено явное задание Owner на указанной базе. Статус изменения, events.jsonl и чужие задачи не изменены; ветка не создавалась, push и оркестратор не запускались. Ошибки собственного harness и ограничения sandbox разобраны в evidence и не объявлены дефектами продукта.

## Риски

Удалённый развёрнутый сервис и его конфигурация, screen-reader и browser zoom не проверены; подробные исключения исходного плана сохраняются. Не проверялись юридическая достаточность, доставка email и эксплуатационная готовность; интеграция, закрытие DEBT-UI-001 и Owner acceptance не выполнялись. Результат ограничен точной локальной поставкой и публичным кодом этой версии. Существующий DEBT-CALC-001 остаётся SKIPPED.

Следующий шаг: отдельная задача Reviewer code_review на том же проверенном production-коммите и коммите Tester; переход выполняет оркестратор отдельно.
