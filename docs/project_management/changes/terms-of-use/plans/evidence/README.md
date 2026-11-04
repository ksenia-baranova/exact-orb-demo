# TASK-D-04 — browser evidence промта 03

Developer-проверка 2026-11-01…02 (Europe/Moscow), без независимой приёмки.
Рабочая копия: `C:\Users\KateUser\PycharmProjects\exact-orb-recovered`, ветка
`change/terms-of-use`. Delivery/source baseline:
`58aa6b956ccbb9bec9948340e955dc4ba133ce25`. Production assets не изменены;
их SHA-256 и проверка сохранности 3744 ранее tracked файлов — [verification.json](verification.json).
Файл задачи и эта папка — весь пакет TASK-D-04. Чужие изменения сохранены.

## Окружение и граница проверки

Настоящий ChatGPT in-app browser, Chromium `156.0.0.0`, Windows 10 x64;
полный User-Agent записан в [browser-results.json](browser-results.json).
CSS viewport: desktop 1280×900, mobile 360×740; финальный desktop snapshot
1280×740. Browser viewport override сброшен после проверки; временные вкладки закрыты.
Это проверка package HTML/CSS/modules в браузере, не DOM-port.

[server.py](server.py) отдаёт исходные UI assets из `src/exact_orb/http_api/ui`.
HTML получает только дополнительный test instrumentation script перед production
module; `index.html` на диске не меняется. [fixture.js](fixture.js) наблюдает fetch и
trusted click capture, пишет результаты в скрытый `<pre>`. Production mount,
form/places/session/transport/result используются настоящие. Заменён только HTTP
leaf: bootstrap/current/build возвращают существующие golden fixtures; `/places`
использует существующий fixture. Это не проверка расчётного движка или live HTTPS.
Golden ChartDTO содержит сокращённый набор точек/домов, поэтому колесо использует
штатный HTML fallback; проверено восстановление принятой карты и редактора,
полнота SVG этим harness не подтверждается. Новых production endpoints нет.

## Фактически выполненные команды

Из корня указанной рабочей копии, системный Python 3.14.0, pytest 9.0.2,
FastAPI 0.121.2. `.venv` не содержит FastAPI; зависимости не устанавливались.

| Команда | Результат |
| --- | --- |
| `python docs/project_management/changes/terms-of-use/plans/evidence/server.py` | localhost `http://127.0.0.1:8874`, затем остановлен |
| `node --test tests/ui/terms.test.mjs` | 53 PASS, 0 FAIL, 0 SKIP |
| `python -m pytest tests/http_api/test_ui_delivery.py -q` | 8 PASS за 7.53 с; approved text и installed wheel |
| `node --test tests/ui/*.test.mjs` | 282 PASS, 0 FAIL, 0 SKIP; [log](node-related.log) |
| `python -m pytest tests/http_api tests/test_module_boundaries.py -q` | 347 PASS за 26.86 с; [log](pytest-related.log) |
| `python -m pytest` | 2960 PASS, 1 SKIPPED за 132.15 с; [log](pytest-full.log) |
| `node --check docs/project_management/changes/terms-of-use/plans/evidence/browser-probes.js` | PASS |
| `git diff --check`, затем `git diff --cached --check` | PASS |

Python-команды выполнялись после целевых/связанных проверок в указанном порядке.
При запуске через PowerShell stdout связанных/full прогонов перенаправлен в
соответствующий `.log` в этой папке; итоговые native process exit codes — 0.
Единственный SKIPPED: `tests/test_configurations.py:473`, DEBT-CALC-001;
SKIPPED не считается PASS. `importlib.util.find_spec('radon')` → `None`.
Production Python не менялся; Python radon неприменим к HTML/CSS/JS.

## Браузерные команды и результаты

Использован `mcp__cua_repl.js`. [browser-probes.js](browser-probes.js) сохраняет
исходники фактически выполненных функций; параметр вкладки сделан явным для
повторного использования после её закрытия. Это код для `cua_repl.js`, не Node CLI.
Повтор: запустить сервер, выбрать браузер `cua.getBrowser`, создать вкладку
`cua.createBrowserTab`, вставить определения probe-функций, затем выполнить:

```javascript
let viewport = await browser.capabilities.get('viewport');
for (const [width, height] of [[1280, 900], [360, 740]]) {
  await viewport.set({ width, height });
  await tab.goto('http://127.0.0.1:8874/');
  await readyPage(tab, 0);
  await pointerCheck(tab, 'terms-link');
  await tab.playwright.locator('#terms-link').click();
  await pointerCheck(tab, 'terms-agree');
  await pointerCheck(tab, 'terms-back');
  await negative(tab, width);
}
```

**Клавиатура/фокус — PASS.** На обоих размерах `#terms-acknowledged.press('Tab')`
→ `#terms-link`; `tab.pressKey(null, 'Return')` → heading условий, focus-visible
с золотой рамкой 2 px. Tab от heading проходит контакт, ссылку исходников,
`terms-agree`, `terms-back`; скрытая форма не попадает в этот порядок.
Enter на back и agree возвращает focus на видимую ссылку в раскрытом редакторе.
После возврата Tab проходит к построению, скрытые кнопки условий недоступны.
Ссылка и `.check small`: computed family `system-ui, sans-serif`, size `13px`,
weight `400` на обоих размерах. Ссылка открывает страницу, сохраняя отметку;
ручной checkbox переключает только отметку.

**Чтение — PASS.** В начале и конце документа `scrollWidth === clientWidth`,
`scrollX === 0` на desktop/360 px. Таблица 320 px на mobile помещается в страницу;
полный текст, ссылки и обе кнопки доступны. Снимки: [desktop-full.png](desktop-full.png),
[mobile-full.png](mobile-full.png), [mobile-table.png](mobile-table.png),
[mobile-bottom.png](mobile-bottom.png), [mobile-agree-focus.png](mobile-agree-focus.png).
Текстовые DOM snapshots сохранены рядом со снимками. Начальные desktop PNG при
viewport height 900 ограничены видимой поверхностью host; полный документ сохранён
отдельно, финальный desktop viewport height 740 помещается целиком.

**Q44 — PASS для 6 сочетаний control/viewport.** Для каждого target проверен
центрированный квадрат 44×44 CSS px, а не только bbox: сетка из 1936 точек
`document.elementFromPoint` с шагом 1 CSS px; каждый hit принадлежит target.
Дополнительно девять pointer clicks по углам/серединам/центру с `event.isTrusted`
и точным `event.target.id`, каждый активирует нужный переход. Всего 54 trusted
положительных клика. Bounding box и координаты каждого Q44 сохранены в JSON.

Отрицательные контроли для всех трёх targets на обоих viewport — **18 разных
сочетаний, обнаружены** той же функцией q44 и проверены trusted pointer:

- `small`: target 43×43, overflow скрыт; квадрат Q44 отклонён, click вне target.
- `overlay`: покрытие 8×8 в центре; bbox прежний, hit/click получает `negative-overlay`.
- `clip`: clip-path обрезает правую часть Q44; bbox прежний, hit/click получает фон.

JSON содержит 19 negative records: small/desktop повторён при калибровке probe.
Первая pointer-проба на дробной границе overlay дала click на ссылке из-за
округления координат ввода; она не засчитана PASS. Финальный negative probe выбирает
целочисленную внутреннюю точку overlay/clip и сравнивает её elementFromPoint с
реальным получателем trusted click. Это исправление измерительного harness,
production-дефект из него не выводился.

**Возвраты — 12 PASS.** При `/?saved=1&draft=known|unknown|incomplete` открыть
`#birth-edit`, изменить дату на `2000-02-29`; время `23:59` либо `12:6`, для unknown
выбрать `#time-unknown`, для incomplete заменить место на невыбранную строку.
Для каждого draft и обоих исходных checkbox выполнить открытие ссылки и back/agree.
Сравнены date/place/time/unknown до и после, ожидаемая отметка, focus и число всех POST
после завершения исходного открытия. Значения и принятая карта сохранены, новых POST нет.

**Позитивный контроль сети — 2 PASS.** Для manual/agree открыть saved fixture,
выбрать ознакомление и отдельно нажать «Построить карту». В каждом документе ровно
один POST `/charts/natal`; три поля intent:
`{"birth_date":"2000-02-29","birth_time":"23:59","place_id":"524901"}`.
Фактический серверный журнал — [requests.json](requests.json), всего два build.

**Reload/закрытие — 8 PASS.** Для saved=0/1 и manual/agree выполнены настоящие
`tab.reload()` и `tab.close()` → новая `cua.createBrowserTab` с тем же URL и cookies.
Перед каждым reload/close отметка выбрана, после готового current и открытия
редактора она снята. При saved=1 восстановлены дата/place/time и принятая карта.
В первом close/reopen устарел runtime handle; вкладка найдена заново и проверка
продолжена с явным параметром tab, без подмены закрытия новым mount.

## Утверждённый текст и исходники

Owner TASK-O-02 утвердил пакет `02cbd17e33ceffe52d465bdf6b8faf1d3c76864c`.
Публикуемый раздел извлечён именно через `git show` этого коммита. [browser-terms.html](browser-terms.html)
сохранён из DOM настоящего браузера; существующий `TermsContent` восстановил Markdown
с таблицей, заголовками, strong и href. Побайтное равенство и SHA-256 UTF-8/LF с одним
конечным LF подтверждены:
`ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0`.
C1…C6/C8, точный контакт `exact_orb@mail.ru`, отсутствие редакционных меток — PASS.
Видимый C7 link/href также совпадает с утверждённым текстом.

**C7: NOT RUN в части полного кода точной поставки.** Ссылка открывает без входа
публичный [репозиторий](https://github.com/ksenia-baranova/exact-orb-demo);
его main показывает `9f36ee8c8d6b3105de0ed633c23abe7fdeac7fea`.
GitHub connector `fetch_commit(repo_full_name='ksenia-baranova/exact-orb-demo',
commit_sha='58aa6b956ccbb9bec9948340e955dc4ba133ce25')` вернул HTTP 422
`No commit found for SHA`. [source-check.json](source-check.json),
[source-page.txt](source-page.txt), [source-page.png](source-page.png).
Корневой URL и его доступность не подтверждают соответствие поставке. Source commit
используемой версии локально — `58aa6b9`; опубликованного exact source URL не получено.
Публикация запрещена поручением: push не выполнялся. NOT RUN не превращён в PASS.

## Решение Developer

Наблюдаемых дефектов страницы и связи с формой в проверенном объёме нет.
Production-код и тесты публичного поведения не менялись; использовано существующее
детерминированное покрытие terms/delivery. CSS/handlers перечитаны: общие font rules,
один returnFromTerms, единый renderPage уже дают простое решение. Упрощение не требует
правок. Новых shortcut, зависимостей, timers или production logging нет.
Независимая test/code_review, transfer, интеграция и DEBT-UI-001 остаются вне этой задачи.
