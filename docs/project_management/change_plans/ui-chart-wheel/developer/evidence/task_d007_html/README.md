# TASK-D-007 — первый HTML-участок / native evidence

Автор: Codex / Developer,19.10.2026; InputSHA502589dbadd382fbe39e3cf1fd763abb52ffc620 плюс локальная реализация CH-02/03. Это Developer regression evidence, не независимая приёмка и не SVG experiment.

Запуск из корня репозитория:

~~~text
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_html/browser.cjs
~~~

Нужен уже установленный Playwright и Chrome; app dependencies не добавлены. По умолчанию используются имеющиеся локальные runtime / Chrome paths; другой путь задаётся WHEEL_PLAYWRIGHT / WHEEL_BROWSER. Script поднимает временный loopback server только на время проверки, загружает настоящие UI modules/index/styles, подменяет только HTTP leaf опубликованными fixtures и закрывает browser/server в finally. Интернет / платный LLM не вызываются.

[actual.json](actual.json) содержит raw SHA-256 и source_lf_sha256 (переводы строк CRLF→LF) фактически проверенных UI modules / fixtures / browser script и PASS по трём ширинам1440/768/360, Chrome155.0.8059.40 / Windows. Screenshots: [1440](html-1440.png), [768](html-768.png), [360](html-360.png). Последнее состояние после automatic S1 update с общим раскрытым списком, поэтому PNG намеренно длинные.

Проверены начальные five/all /16 points, нативные Enter/Space, сохранённый HTML node / active focus и отсутствие программного focus/scroll при planet activation,24 видимые HTML-цели ≥44×44 на каждой ширине, resize без запросов, accepted source reorder / reversal / новая category/orb, S1 по полному DTO, source rows, zero page errors / horizontal overflow. Позитивные network controls — boot/current и две явные online-сверки; никаких POST от выбора / раскрытия.

Sandbox-запуск браузера остановился ERR_NETWORK_ACCESS_DENIED для loopback; разрешённый повтор вне sandbox и повтор после source-order сценария — PASS. Product engine/API/DTO fixtures не менялись. Эти три browser cells не доказывают SVG geometry, весь birth-reset/recovery путь, независимую приёмку, другие браузеры / ОС или live HTTPS.
