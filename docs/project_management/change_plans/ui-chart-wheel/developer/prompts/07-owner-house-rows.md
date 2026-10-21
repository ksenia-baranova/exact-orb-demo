# TASK-D-007 — внутренние ряды планет вместо колонки

Codex / Developer, 20.10.2026. Прямое поручение Owner: убрать выносную колонку, размещать значки внутри опубликованного дома, разрешить несколько радиальных рядов и визуальное смещение градусов. Точные данные сохранить; показать результат в браузере. STARTED — исполнение этой итерации; исходный D007 STARTED сохраняется.

InputSHA e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, dev/ui-chart-wheel. Accepted v3+S1 2736e2848c977ec4c770a9a4dec2a0d7c1b62a71 + текущая Owner delta. Старое правило C0/колонка/замороженные неконфликтные point-подписи заменяется только для planet glyph placement. REQ-WHEEL-01/02/04/05/09/10, текущий DRAFT ADR и sequence004; API/engine/golden/deps/foreign artifacts не меняются.

Разрешённые production files: wheel_layout.mjs, wheel_svg.mjs, result_controller.mjs (закрытый whitelist диагностических attrs), при доказанной необходимости styles.css. Собственные tests, документальные материалы, новые evidence. Исторические raw/manifests не переписывать. Commit/push не поручены.

Подход: чувствительные regression tests геометрии, существующее state/lifecycle покрытие, реальный native SVG/browser. Собственные дома только points[].house; cusp sectors — геометрические границы, не новая классификация. Для космограммы нет домов: круговая раскладка без присвоения house. Font16/12, bbox gap2, точные исходные отметки и source aspect endpoints, passive SVG, полный S1 сохраняются. Ряды должны учитывать весь bbox, в том числе R/контур, и wrap0°. При невозможной вместимости — явный local error и сохранённый HTML, не скрытие значков/смена дома/сжатие шрифта.

Проверки: pure deterministic order/house containment/no column/rows/no mutation/source endpoints; Node tests/ui/*.test.mjs; реальные1440/768/360 + DPR/font; исходная source cardinality/S1/selection/focus/recovery; independent bbox audit без вызова layout. Target53 Python и full pytest по AGENTS. Live HTTPS delivery и показ через браузер. Не подменять fake HTTP доказательством реального POST.
