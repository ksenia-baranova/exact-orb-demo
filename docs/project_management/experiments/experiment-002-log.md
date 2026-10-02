# Журнал change: HTTP API and Session Middleware

- **Статус:** Analysis PR #37 принят в `change/*`; решения DP-HTTP-01…06 и FIND-HTTP-021 подтверждены пользователем. Developer сохранил draft implementation plan и промты коммитом `c7e794a`; связанные requirement/Lead/UI/diagram правки включены в отдельный документационный коммит текущей ветки. Tester review Analysis/test design ранее имел вердикт «принять с доработками»; Gate Analysis → Development открыт до технического evidence S0 и проверки исправленного тест-дизайна. HTTP-код и тесты ещё не написаны.
- **Change:** `change/http-api-and-session-middleware`.
- **Исходный `main`:** `e337f5107d7a3092983f1d920aac45040c2df6ed`.
- **Стартовый commit `change/*`:** `acc0a7671d52676e0e230e76497d59f769ec4fa8`.
- **Текущая ветка:** `dev/http-api-and-session-middleware` от `f11275c1306bf227544b10321151371852e24b28`.
- **Начало журнала:** 2026-09-29 11:30 +03:00.
- **Change plan:** [http-api-and-session-middleware.md](../change_plans/http-api-and-session-middleware.md).
- **Календарный план:** [http-api-and-session-middleware.puml](../change_plans/http-api-and-session-middleware.puml).
- **Setup PR:** #36, принят в `change/*`, merge commit `27ae072`.
- **Analysis PR:** #37, принят в `change/*`, merge commit `f11275c`.

## 1. Как вести журнал

Журнал содержит только фактические события change. Новая запись добавляется:

- в начале или при завершении работы роли;
- при создании или принятии Pull Request;
- при передаче работы следующей роли;
- при решении Lead;
- при появлении finding, blocker или возврата на доработку;
- при выполнении проверки, которая используется как evidence.

Requirements, планы и подробные технические обоснования в журнал не копируются. Для них указывается ссылка на
соответствующий артефакт.

## 2. Хронология

| Дата и время          | Роль | Событие                                 | Ветка / commit / PR                                              | Результат                                                                               |
|-----------------------|------|-----------------------------------------|------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 2026-09-28            | Lead | Начата подготовка change                | `lead/http-api-and-session-middleware` от `change/*` @ `acc0a76` | Проверены ветка и исходные commits                                                      |
| 2026-09-28            | Lead | Подготовлен первый черновик change plan | рабочее дерево `lead/*`                                          | Зафиксированы цель, границы, роли, входные артефакты и условия перехода между этапами   |
| 2026-09-29            | Lead | Change plan переработан после review    | рабочее дерево `lead/*`                                          | Упрощены формулировки; отдельно описаны HTTP API сессии, поиска мест и построения карты |
| 2026-09-29            | Lead | Уточнено назначение журнала             | рабочее дерево `lead/*`                                          | В change plan добавлены состав журнала и правило его обновления                         |
| 2026-09-29            | Lead | Добавлен календарный план               | рабочее дерево `lead/*`                                          | Принята рабочая оценка 4 дня без резерва на возвраты и исправления                      |
| 2026-09-29            | Lead | Создан этот журнал                      | рабочее дерево `lead/*`                                          | Комплект setup-артефактов подготовлен к итоговой проверке перед commit                  |
| 2026-09-29 12:47 +03:00 | Lead | Подготовка Lead завершена             | рабочее дерево `lead/*`                                          | Change plan, Gantt и журнал готовы к commit и setup PR                                  |
| 2026-09-29            | Lead | Setup PR принят                         | PR #36 → `change/http-api-and-session-middleware` @ `27ae072`    | Зафиксирован входной commit для Functional Analyst                                      |
| 2026-09-29            | Functional Analyst | Начат Analysis              | `analysis/http-api-and-session-middleware` от `change/*` @ `27ae072` | Проверены requirements, ADR, sequence, код и application tests                       |
| 2026-09-29            | Functional Analyst | Подготовлен первый проект анализа | рабочее дерево `analysis/*`                                  | HTTP requirements, 18 scenarios и 3 transport sequence переданы на review               |
| 2026-09-29            | Functional Analyst | Уточнена граница build response | рабочее дерево `analysis/*`                                  | Зафиксирован FIND-HTTP-007 и предложена самодостаточная birth-проекция без второго session load |
| 2026-09-29            | Reviewer / owner | Analysis возвращён на доработку | рабочее дерево `analysis/*`                                  | Зафиксированы ADR collision, creation-limit/deadline gaps, error precedence, lifecycle и missing acceptance coverage |
| 2026-09-29            | Functional Analyst | Проект переработан после review | рабочее дерево `analysis/*`                                  | Восстановлены ADR-0039/0040, stored-chart перенумерован 0041; 29 scenarios и 4 HTTP sequence |
| 2026-09-29            | Reviewer / owner | Второй раунд review Analysis | рабочее дерево `analysis/*`                                  | Первый раунд в основном закрыт; новые FIND-HTTP-011…019 и варианты закрытия FIND-HTTP-009 записаны в [HTTP requirements §15](../../requirements/http_api.md#15-findings-и-ограничения) |
| 2026-09-29            | Reviewer / owner | Анализ передан Lead на решения | рабочее дерево `analysis/*`, без commit                      | Нужны решения по FIND-HTTP-004/009, 010, 011, 012, 017, 018, 019; FA параллельно закрывает 013–016 |
| 2026-09-29            | Functional Analyst | Предложены scope и базовая оценка после второго review | рабочее дерево `analysis/*`, без commit          | Pure `session_view` expansion и development/testing 4/2 дня переданы Developer/Lead; решения Lead нет |
| 2026-09-29            | Functional Analyst | Закрыты замечания второго review | рабочее дерево `analysis/*`, без commit                 | Определены retry/recovery, Origin GET, cookie action, Retry-After, spoofed XFF, health exposure и low-risk read boundary |
| 2026-09-30            | Reviewer / owner | Найдена процессная ошибка атрибуции | рабочее дерево `analysis/*`, без commit                    | Предложения Analysis были ошибочно записаны как решения Lead |
| 2026-09-30            | Functional Analyst | Исправлена атрибуция scope и оценки | рабочее дерево `analysis/*`, без commit                  | Ошибочная атрибуция удалена; FIND-HTTP-019 снова открыт до решения Lead |
| 2026-09-30            | Lead | Проведён review PR #37                  | пять inline comments и процессное замечание                    | DP-HTTP-02 согласован всеми ролями; для M1-6 выбран вариант C, target state — A; Lead-owned plan/Gantt возвращены владельцу |
| 2026-09-30            | Functional Analyst | Выполнены замечания review PR #37 | рабочее дерево `analysis/*`, без commit                     | Уточнён resumable scope, выровнены таблицы, синхронизированы fail-fast requirements/AS/diagram; изменения plan/Gantt исключены |
| 2026-09-30 | — | Analysis PR #37 принят в `change/*` | merge commit `f11275c` | HTTP requirements и sequence доступны в интеграционной ветке; отдельное evidence всех approval в документах ещё не записано |
| 2026-09-30 | Developer | Начата подготовка Development | `dev/http-api-and-session-middleware` от `f11275c` | Сверяются решения и входные документы; открытые scope/approval не закрываются неявно |
| 2026-09-30 | Lead | Приняты решения по scope и оценке | DP-HTTP-06 / FIND-HTTP-001/019 | Чистая birth-проекция `session_view` включена в M1-6; исходная оценка Gantt 0,5+1,5+1+1=4 дня сохранена |
| 2026-09-30 | Developer | Завершён технический review | `dev/http-api-and-session-middleware` | DTO/mapping, trusted proxy и чистая birth-проекция реализуемы; при disconnect shielded calculation leader требует отдельного ownership до освобождения permit; lifecycle evidence впереди |
| 2026-09-30 | Lead | Согласованы оставшиеся содержательные решения | DP-HTTP-01/03/05; FIND-HTTP-002/005/010/012/017/018 | HTTP-контракт, trusted proxy, sequence, ограничения M1 и восстановленная ревизия ADR-0040 приняты; реализация и тесты не объявлены завершёнными |
| 2026-09-30 | Developer | Подготовлены implementation plan и промты 01–13 | рабочее дерево dev/http-api-and-session-middleware, без commit | Четыре test-first промта, Tester gate и девять implementation/acceptance промтов; особый owner test для shielded calculation leader |
| 2026-09-30 | Tester | Review Analysis и тест-дизайна; вердикт «принять с доработками» | текст review передан пользователем; [ответ Developer в implementation plan §7](../implementation_plans/http_api_and_session_middleware_implementation_plan.md#7-полученный-tester-review-analysis-и-тест-дизайна) | AS-HTTP-01…29 распределены без пропусков; четыре блокера T-A1…T-A4: управляемый timer, контракт per-request permit, внешний capacity oracle, restart на той же SQLite; исполняемых HTTP-тестов ещё нет, это не Gate T |
| 2026-09-30 | Developer | Уточнён Development Finding по результатам проверки кода и согласования вариантов пользователем | [implementation plan §8](../implementation_plans/http_api_and_session_middleware_implementation_plan.md#8-development-finding-для-повторной-analysis), рабочее дерево `dev/*`, без commit | Выбран консервативный snapshot активных resolver leaders для отменённого waiter; DTO и серверные oracle AS-HTTP-17/19 описаны для Analysis. Только правило permit зависит от S0; требования и Gate A пока не утверждены повторно |
| 2026-09-30 | Developer | Выполнен промежуточный read-only проход S0 по cancellation seam | [implementation plan §4](../implementation_plans/http_api_and_session_middleware_implementation_plan.md#4-порядок-и-зависимости), рабочее дерево `dev/*`, без commit | `runtime.drain()` видит активные resolver leaders, но не удерживает отменённые `run_in_executor` futures SQLite session load и catalog lookup; нужен узкий internal leaf seam и deterministic barrier tests. T-A2/Gate A остаются открыты |
| 2026-09-30 | Developer | Implementation plan и промты 01–13 сохранены локальным коммитом | `dev/http-api-and-session-middleware` @ `c7e794a` | В коммите 14 Developer-owned Markdown-файлов; push/PR не выполнялись, тесты не запускались |
| 2026-09-30 | Владелец change | Подтверждены все связанные решения и разрешён общий документационный коммит | указание пользователя 2026-09-30; FIND-HTTP-021 | Уточнения permit, DTO и разделения HTTP/UI-приёмки внесены в requirements, UI acceptance и build sequence; это approval контракта, но не исполненное доказательство S0/Tester |
| 2026-09-30 | Developer | Синхронизированы и сохранены связанные документы change | отдельный документационный коммит `dev/http-api-and-session-middleware` | Change plan, журнал, HTTP requirements, ADR-0040/реестр, UI-приёмка, build sequence и обновление implementation plan; без кода и исполняемых тестов |

Подготовка Lead: 0,5 чд. Фактическое время Analysis агентом не измерялось.

## 3. Решения Lead

| ID            | Дата       | Решение                                                                                                                                                  | Основание                                       | Затронутые артефакты                                              |
|---------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------|-------------------------------------------------------------------|
| LEAD-HTTP-001 | 2026-09-28 | В change входят HTTP API сессии, поиска мест и построения натальной карты, запуск и остановка приложения, ограничения расчётных запросов и наблюдаемость | M1-6 roadmap и действующие требования           | [change plan](../change_plans/http-api-and-session-middleware.md) |
| LEAD-HTTP-002 | 2026-09-29 | Начальная рабочая оценка: подготовка — 0.5 дня, Analysis — 1.5 дня, разработка — 1 день, тестирование — 1 день                                           | Решение setup-этапа; Analysis предложил пересмотр; Lead сохранил исходную оценку в LEAD-HTTP-006 | [Gantt](../change_plans/http-api-and-session-middleware.puml) |
| LEAD-HTTP-003 | 2026-09-30 | Численные admission limits DP-HTTP-02 согласованы всеми ролями                                                                           | [inline comment PR #37](https://github.com/ksenia-baranova/exact-orb-demo/pull/37#discussion_r4143352523) | [HTTP requirements](../../requirements/http_api.md#3-decision-points-и-значения-по-умолчанию) |
| LEAD-HTTP-004 | 2026-09-30 | Для M1-6 выбран вариант C — fail-fast restart web process; target state — отдельный calculation worker/process (вариант A)                | [inline comment PR #37](https://github.com/ksenia-baranova/exact-orb-demo/pull/37#discussion_r4143470793) | [HTTP requirements §15.2](../../requirements/http_api.md#152-решение-по-find-http-009--dp-http-04) |
| LEAD-HTTP-005 | 2026-09-30 | Чистая birth-проекция `session_view` из готового snapshot входит в M1-6 для `GET /charts/current`; без новых I/O и application ports | решение владельца change 2026-09-30; DP-HTTP-06 | [HTTP requirements §7.1](../../requirements/http_api.md#71-основные-формы), [change plan](../change_plans/http-api-and-session-middleware.md) |
| LEAD-HTTP-006 | 2026-09-30 | Сохранена исходная оценка: Lead 0,5 дня, Analysis 1,5 дня, Development 1 день, Testing 1 день; всего 4 рабочих дня | решение владельца change 2026-09-30; предложение Analysis 4/2 дня не принято | [Gantt](../change_plans/http-api-and-session-middleware.puml), [change plan](../change_plans/http-api-and-session-middleware.md) |
| LEAD-HTTP-007 | 2026-09-30 | Согласованы DP-HTTP-01/03/05, ограничения FIND-HTTP-002/005/017/018 и восстановленная ревизия ADR-0040 по FIND-HTTP-010/012 | подтверждение владельца change 2026-09-30; технический review Developer | [HTTP requirements](../../requirements/http_api.md), [ADR-0040](../../requirements/decisions/0040-session-bootstrap-and-current-chart.md) |

## 4. Передача между ролями

| Передача                       | Входной commit                                       | Результат предыдущей роли                                                 | Статус           | Время ожидания gate |
|--------------------------------|------------------------------------------------------|---------------------------------------------------------------------------|------------------|---------------------|
| Lead → Functional Analyst      | `27ae072`                                            | протокол, change plan, Gantt, журнал и принятые входные артефакты         | завершено        | не измерялось       |
| Functional Analyst → Developer | `f11275c` + незакоммиченные правки | HTTP requirements, 29 acceptance scenarios, sequence diagrams и Tester review Analysis/test design | Tester review получен с доработками; Gate A открыт до T-A1…T-A4, точных DTO и интеграции Lead-owned правок | не измерялось |
| Developer → Tester             | —                                                    | реализация, автоматизированные тесты и review evidence                    | не начато        | —                   |
| Tester → Lead                  | —                                                    | acceptance evidence, findings и известные ограничения                     | не начато        | —                   |

## 5. Findings и blockers

| ID | Тип | Описание | Владелец | Статус |
|---|---|---|---|---|
| FIND-HTTP-001 | Finding | `session_view` не публикует весь BirthViewDTO | Developer / Lead | Lead включил чистую birth-проекцию в M1-6; реализация и тесты ожидаются |
| FIND-HTTP-002 | Limitation | session не хранит admin1/country для restore | Lead | суженный M1 DTO принят Lead |
| FIND-HTTP-003 | Decision | client IP/trusted proxy | Developer / Lead | Developer review выполнен; алгоритм согласован Lead; реализация впереди |
| FIND-HTTP-004 | Decision | bounded deadline/shutdown task ownership | Developer / Lead | Lead выбрал C для M1-6 и A для target state; требуется implementation evidence |
| FIND-HTTP-005 | Limitation | limiter process-local; один worker/version | Lead | ограничение M1 принято Lead |
| FIND-HTTP-006 | UI alignment | split flow и ChartDTO расходились с UI docs | Functional Analyst | исправлено в draft |
| FIND-HTTP-007 | Former blocker | build result не содержит birth projection | Functional Analyst | закрыто ADR-0040 revision: birth читает current GET |
| FIND-HTTP-008 | Scope | reset/delete endpoint отсутствует | Lead | явно deferred; component contract сохранён |
| FIND-HTTP-009 | Risk | неотменяемый native call может пережить HTTP timeout | Developer / Lead | решение C/A принято; acceptance ждёт deterministic evidence |
| FIND-HTTP-010 | Provenance | ADR-0039 recovered from reflog commit; exact ADR-0040 file unavailable | Lead | восстановленная формулировка согласована Lead |
| FIND-HTTP-011 | Retry semantics | transient flag отделён от same-request retry; 504=false, unchanged cookie, current recovery | Functional Analyst / Lead | исправлено; DP-HTTP-01 согласован |
| FIND-HTTP-012 | Provenance | реестр 24.09 сохраняет C; ADR-0040 имеет отдельную ревизию 29.09 C → D после ADR-0041 | Lead | ревизия согласована Lead |
| FIND-HTTP-013 | Acceptance gap | spoofed XFF от untrusted peer и независимые peer buckets | Functional Analyst | закрыто AS-HTTP-29 |
| FIND-HTTP-014 | Contract gap | Origin у GET | Functional Analyst | закрыто: present Origin проверяется на всех business endpoint |
| FIND-HTTP-015 | Mismatch | clear old cookie при absent + create refusal | Functional Analyst | закрыто в §5/AS-04; diagram согласована |
| FIND-HTTP-016 | Contract gap | exact `Retry-After` | FA / Developer | значения согласованы; реализация и проверка впереди |
| FIND-HTTP-017 | Risk, low | чтение по живой cookie не лимитируется | Lead | риск controlled M1 принят Lead; proxy limit до public M1-12 |
| FIND-HTTP-018 | Deployment | экспозиция health endpoint | Developer / Lead | internal-only принято Lead; ACL/manifest в M1-12 |
| FIND-HTTP-019 | Scope/estimate | `session_view` и оценка | Developer / Lead | решение Lead: projection входит в M1-6; исходная оценка 4 дня сохранена |
| FIND-HTTP-020 | Process gate | Lead-owned plan/Gantt | Lead | старый ADR path и scope исправлены в рабочем плане; Gantt сохраняет подтверждённую оценку; интеграция Lead-owned правок в `change/*` ожидается |

Текущие предложения и решения перечислены в разделе 15
[HTTP requirements](../../requirements/http_api.md#15-findings-и-ограничения).
Lead-owned change plan и Gantt Analysis не изменяет.

## 6. Проверки и evidence

| Дата       | Что проверялось                | Команда или способ проверки                                                 | Результат                                                 | Предел evidence                                                        |
|------------|--------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------|------------------------------------------------------------------------|
| 2026-09-28 | Ветка и исходное состояние     | `git branch --show-current`; `git log -1 --format='%H %s'`                  | `lead/http-api-and-session-middleware`; HEAD `acc0a76`    | Подтверждает только локальное состояние worktree на момент проверки    |
| 2026-09-29 | Ссылки и пробелы в setup-документах | локальная проверка относительных путей и окончаний строк                | отсутствующие ссылки и trailing whitespace не найдены     | Не проверяет смысл документов                                          |
| 2026-09-29 | Структура Gantt                | проверены `@startgantt`, `@endgantt`, даты и отсутствие trailing whitespace | структура согласована с существующими Gantt репозитория   | Диаграмма не была отрендерена: Java и PlantUML отсутствуют в окружении |
| 2026-09-29 | Ветка и входной commit Analysis | `git branch --show-current`; `git rev-parse HEAD`                         | `analysis/http-api-and-session-middleware`; `27ae072e5e99cea72f7575cd35ef45ca3eeb829e` | Подтверждает локальный worktree до commit Analysis |
| 2026-09-29 | Первый проект HTTP requirements | локальный PowerShell: секции, scenarios, findings, fences и `ConvertFrom-Json` | на первом проекте: секции 1–17, AS-HTTP-01…18, FIND-HTTP-001…007, 22 fence markers; 7 JSON-примеров разобраны | Исторический результат до возврата Analysis на доработку |
| 2026-09-29 | Первый проект sequence       | локальный PowerShell: 7 Markdown-файлов и 6 `.puml`                     | на первом проекте все relative targets существовали; блоки были сбалансированы | Исторический результат до возврата Analysis на доработку |
| 2026-09-29 | Переработанные HTTP requirements и sequence | локальный Python validator: links, fences, JSON, PlantUML blocks, scenario IDs | 29 scenarios по порядку; новые links существуют; JSON/fences и изменённые PlantUML blocks сбалансированы | Статическая проверка, без выполнения приложения и рендера PlantUML |
| 2026-09-29 | Запись проверенной staged-копии | `git diff --no-index --quiet -- <worktree>/docs <staging>/docs` | exit code 0; записанные документы побайтово совпали с проверенной копией | Не подтверждает runtime-поведение |
| 2026-09-29 | Происхождение ADR-0039/0040 | `git log --all --reflog -- <paths>`; `git fsck --full --unreachable --no-reflogs`; scan blobs | ADR-0039 найден в reflog commit `cf16d41`; среди 384 unreachable blobs отдельного split ADR-0040 нет | Не находит объекты, уже удалённые Git GC |
| 2026-09-29 | Чистота документационного diff | `git diff --check`                                                        | exit code 0; whitespace errors не найдены                   | Не проверяет смысл контрактов |
| 2026-09-29 | Исправления второго review | локальный Python validator: changed files, links, fences, JSON, AS/FIND IDs, PlantUML/Gantt blocks; `git diff --check` | `OK existing_changed_files=37` + 1 deleted path; `text_files=37 json_blocks=5 scenarios=29`; exit code 0 | Статическая проверка; не исполняет приложение и не рендерит PlantUML |
| 2026-09-30 | Процессная атрибуция scope и оценки | локальный Python validator; `rg` по фиктивным Lead ID и прежней формулировке варианта A; `git diff --check` | `OK status_paths=38 existing=37 deleted=1 json_blocks=5 scenarios=29 findings=19`; совпадений нет; exit code 0 | Статическая проверка; решение Lead и выбор Developer по-прежнему требуются |
| 2026-09-30 | Замечания review PR #37 | Conversation + 5 inline comments; локальный Python validator; `git diff <base> --name-status`; `git diff --check` | `OK working_paths=5 pr_paths=35 json_blocks=5 scenarios=29 findings=20 tables=13 lead_decisions=4`; plan/Gantt отсутствуют в PR diff; exit code 0 | Статическая проверка; старый ADR path в Lead-owned plan зафиксирован FIND-HTTP-020 |
| 2026-09-29 | Доступность рендера PlantUML   | `Get-Command java`; `Get-Command plantuml`; поиск `*plantuml*.jar`          | Java, PlantUML command и jar отсутствуют                    | Диаграммы не отрендерены |
| 2026-09-29 | Автоматизированные тесты       | не запускались                                                              | документационные изменения не затрагивают исполняемый код | Поведение приложения не проверялось                                    |
| 2026-09-30 | Новый implementation plan и промты 01–13 | PowerShell: relative links и trailing whitespace для 14 новых Markdown-файлов; git diff --check | 14 файлов, 0 отсутствующих ссылок, 0 trailing whitespace; git diff --check exit 0 | Статическая проверка; HTTP-код, pytest и PlantUML rendering не выполнялись |

## 7. Текущие показатели

| Показатель                          | Значение |
|-------------------------------------|---------:|
| Завершённые передачи между ролями   |        1 |
| Передачи, возвращённые на доработку |        1 |
| Зафиксированные решения Lead        |        7 |
| Возвраты к Analysis                 |        1 |
| Раунды review Analysis              |        4 |
| Открытые blocking findings          |        2 |
| Открытые блокеры Tester для Gate A  |        4 |

## 8. Следующий шаг

**Lead** согласовал содержательные решения DP-HTTP-01…06, ограничения M1 и восстановленную ревизию ADR-0040 (LEAD-HTTP-003…007). Пользователь подтвердил также FIND-HTTP-021 и разрешил коммит всех связанных файлов. Это ещё не возврат документов в `change/*`. Полученный Tester review Analysis/test design имел вердикт «принять с доработками»; это не закрывает Gate A и не является review ещё не написанных исполняемых тестов.

**Developer** передаёт [implementation plan](../implementation_plans/http_api_and_session_middleware_implementation_plan.md)
на review после закрытия S0/G0 и T-A1…T-A4. FIND-HTTP-021 уже отражён в §9.3/AS-HTTP-24, DTO §7.2/AS-HTTP-28, серверных oracle AS-HTTP-17/19 и приёмке UI M1-7. Контрактный выбор подтверждён пользователем; техническое удержание SQLite/catalog futures, deterministic tests и проверка Tester остаются. После Gate A промты 01–04 создают исполняемые contract tests; до production code их отдельно сверяет Tester на Gate T. Реализация fail-fast restart и evidence пока не выполнены.

**Tester** проверяет AS-HTTP-01…29, включая spoofed XFF, unknown outcome и
fail-fast supervisor restart. Формальный review и acceptance evidence ещё не записаны.
