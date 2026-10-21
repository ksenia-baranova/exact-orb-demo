# Чёрное колесо — прямая дельта Owner20.10.2026

**Codex / Developer, TASK-D-007, DRAFT.** SourceRef: текущий Developer-чат, «Есть задача сделать его черным». Реализовано в существующем dev/ui-chart-wheel, HEAD e0daa0e814d3d1fd34cadb8c17d064f19c4810f5, поверх незакоммиченной поставки FW01…06. Предыдущие изменения и index сохранены.

Основание: wheel-image, label rects и leader bridges первоначально содержали белые подложки, zodiac — светлые секторы; подписи/цвета аспектов были подобраны под этот фон. Изменены только краски:
- Фон и подложки #080706; чередующиеся секторы #111111 / #181818.
- Подписи #f3eadb, выделение и true marks #f0cd73; нейтральные кольца/куспиды #777777.
- Семь типов аспектов сохраняют разные оттенки; значения осветлены для контраста: conjunction #93b9f2, semisextile #e7b578, sextile #70c7ad, square #ef7d84, trine #79a9ed, quincunx #b1c978, opposition #d397d1.
- Точные/рабочие по-прежнему solid/dashed, выбранный аспект толще; размеры шрифтов/контуров, DOM ownership, layout/DTO, selection/once/recovery не менялись.

Затронуты src/exact_orb/http_api/ui/{wheel_svg.mjs,wheel_layout.mjs,styles.css}, дополнен собственный developer_artifact.md и создан этот evidence/. Старые prompts/ADR/requirements/Manager/foreign artifacts и все файлы task_d007_runtime сохранены; прежняя палитра в research evidence остаётся исторической.

## Проверки

~~~powershell
$nodeTests = @(rg --files tests/ui -g '*.test.mjs')
& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' --test @nodeTests
#216 PASS,0 FAIL;447,42ms

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_dark_theme/browser.cjs run01
#9/9 PASS;Chrome155.0.8059.40 /Windows, DPR1/zoom1,1440/768/360

& 'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/task_d007_dark_theme/audit.py
git diff --check
~~~

[Native actual](run01/actual.json) содержит source LF SHA256, computed fills/strokes/background, text/line contrast, фактические native bbox/origins и результаты keyboard/focus/no-network. [Baseline](baseline.json) закрепляет состояние UI до перекраски и raw SHA256 всех прежних runtime evidence; [audit](audit.json) проверяет сохранность и соответствие текущему source.

9 случаев = F3-max / palette-control / cosmogram × три ширины. Сравнение native group origins/parts с runtime/run05 — точное равенство во всех9, без допусков. Фон тёмный, белых подложек нет, все7 цветов различаются; keyboard Moon selection даёт золотой контур и живой HTML focus без HTTP. Нет горизонтального overflow/page errors. Screenshot [F3-max360](run01/F3-max-360.png) просмотрен визуально; также сохранены [1440](run01/F3-max-1440.png) и [palette360](run01/palette-control-360.png).

Номинальный sRGB contrast из computed цветов: text минимум10,03:1, palette на самом светлом секторе6,71:1, strokes3,09:1. Это инженерная проверка палитры, не полная сертификация доступности или оценка антиалиасинга.

Полный pytest повторно не запускался: дельта ограничена SVG/CSS-цветами; Python/API/ресурсные имена/поведение не изменились. Прежние2959+1 относятся к предшествующей версии FW, а не новому прогону после перекраски. Иные engines/ОС/real mobile/HTTPS/screen reader не проверялись.

Текущая палитра проверяется этим run01. Прежний task_d007_runtime/verify_package.py закрепляет старые run05/integration06 и закономерно не является проверкой нового цветового source; его manifest/raw не перезаписаны. Новые styling-тесты, повторяющие константы, не добавлялись; переиспользованы216 существующих UI tests и native-приложение.

Commit/push/merge/PR не выполнялись; Manager task/gates не менялись.
