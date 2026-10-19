# Переработка геометрии пассивного SVG — v3

**Автор / подпись:** Codex / Developer, 19.10.2026. **Локальный DRAFT технического предложения, не production / accepted ADR / G3.** Основание — прямое поручение Owner: «Переработай и предложи альтернативные варианты если они есть». Это новое разрешение на ограниченную геометрическую проработку; прежняя остановка D005 не отменяется и D006 не становится STARTED реализации.

**Результат:** новый кандидат **V3-H** проходит геометрию измеренных points / R / подписанных ☌ / angle labels на **12/12** наборах: sparse / F1 / F3 / F3-max × frames720/448/328 (viewports1440/768/360). Строгая локальная компактность **108/110** смещённых меток / **10/12** полных клеток. Оставшиеся два контрпримера — конкретные FAIL, не rounding tolerance и не утверждение о невозможности продукта. Это существенный прогресс к решению, **полная drawing feasibility ещё не подтверждена**: кроме двух FAIL не моделировались весь zodiac / sign text / palette.

## 1. Входы, сохранность и timebox

- `dev/ui-chart-wheel`, InputSHA / фактический HEAD **07bb56ba5d49ec76de64df41ad80d175fbe90a2d**. `git fetch origin change/ui-chart-wheel` — exit0, опубликованный change остался на том же SHA; merge не требовался. Index сохранён пустым.
- Исходные роли только из опубликованного Git. D0058b8c4c8 / D003d24a24e / исследовательский AnalystContractSHA2736e28 сохраняют свои предметы. Принятое Owner table-only selection / passive SVG @07bb56b применяется к новой модели. A008 target SHA пока отсутствует в полученном change; S1 повторно не согласовывается.
- До начала сохранены hashes локальных D006-документов в [spec](evidence/drawing_geometry_v3/spec.json). D003 / D005 runs, fixtures, manifests и ADR не переписываются; собственные индексы дополняются после прежнего D006. Новые файлы только в `developer/` и handoff.
- Исследование STARTED **2026-10-19T10:44:01.302465+00:00**; предложенный технический предел90мин, остановка по достаточности **2026-10-19T11:27:48.942725+00:00** / 43.794мин wall. Это не timesheet / трудозатраты. [Остановка](evidence/drawing_geometry_v3/stop.json) запрещает новые placement/browser итерации этого опыта; далее только post-audit и документы. Остаток D003 и общий бюджет из timestamps не выводятся.

## 2. Корневые причины прежнего отказа и новая конструкция

В D005 `build_models.py` заменял реальную component geometry circumscribed disks, затем отдельно проектировал points, markers и angles. Такая достаточная оценка расстояний слишком груба, особенно для длинной подписи категории, а независимые проходы не исключают столкновений разных групп. Ограниченные128 sweeps не подтверждали ни осуществимость всех ограничений, ни достаточную компактность. Отдельно scope SVG-controls добавлял focus envelope и Q44. Их удаление — принятое Owner изменение, **не исправление старых FAIL задним числом**.

Переработка использует все действительные component AABB совместно: normal ink + усиленный контур только glyph0,75px, R / category text отдельными компонентами, angle labels как реальные препятствия. Шрифты16/12 и gap≥2 не уменьшаются. Сначала вычисляется исходный C0, остальные labels замораживаются. Никакой новый расчет знаков, houses, аспектов, categories или orb не выполняется; исходные DTO/IDs/order/числа сохраняются.

V3-H — один детерминированный маршрут с ограниченными альтернативными seeds:

1. Проверка реальных bounds на исходных кольцах; для конфликтующих labels допустимы радиальные seed-дорожки внутри тех же D005 annuli. Размещение проверяется сразу против **всех** уже учитываемых групп, не по независимым слоям.
2. Beam96 — быстрый seed; при неуспехе / недостаточных certificates адресный finite-domain CSP с forward checking и MRV. Перебор конечный, caps/лимиты записаны до каждого шага. Невыполненный поиск означает bounded failure, не геометрическую невозможность.
3. Точность renderer учитывается **до проверки placement**: физический default reference `Af32` соответствует измеренному SVG binary32 origin; ideal A хранится отдельно. Grid1/1024 CSS px применяется при построении seed, не к уже доказанному результату. Максимальное отклонение физического reference от идеального **0.000034600px <0,5**. C0 membership всех клеток осталось тем же; неподвижные элементы совпадают с физическим default.
4. Локальный возврат / axis contacts; при необходимости смещается только связанная C0-группа с сохранением уже существующих exact-contact ограничений. Дополнительная коррекция ограничена8px/coordinate; применяется к тем же movable labels, не к новым неконфликтным объектам. Конечный набор проверяется заново независимо.
5. Независимый verifier использует Fraction, exact component gap / clip / annulus / порядок и полный prefix возврата. Exact closing axis gap=2 с положительным orthogonal overlap доказывает отсутствие любого допустимого положительного возврата. Это **локальная directional компактность одного label**, без требования глобального оптимума и без обещания меньшего движения всей карты.

Уточнение физического reference / пути возврата — **явное technical proposal для review**, а не молчаливая замена принятого контракта. Как в D005, return path — прямой chord к reference внутри annulus, а не исходная D004 fixed-radius arc. Все0,5/2/1/16/12 сохранены;44 остаётся требованием HTML-controls и здесь не проверяется. Другие масштабы/шрифты требуют новой измеренной mapping; этот опыт доказан при M=1:1, DPR1 / zoom1.

## 3. Альтернативы и tradeoffs

Буквы ниже относятся только к **V3**, не переименовывают D005-F/E. Исходные specs A/B и последующие адресные спецификации C…H сохранены до генерации соответствующих данных.

| Вариант | Суть / цена сложности | Analytic geometry | Native geometry | Полные клетки с compactness | Вывод |
|---|---|---|---|---|---|
| V3-A | Реальные boxes, один seed-ring, joint beam |9/12|9/12|5/12|Простой seed для разреженных / обычных карт, плотный F3 не покрывает |
| V3-B | Дополнительные radial seed lanes внутри annuli |10/12|10/12|5/12|Плотный F3-max размещает, но beam теряет допустимые F3 варианты |
| V3-C | MRV / forward-checking CSP |9/12|8/12|7/12|Находит пропущенные beam варианты; прежний cap-stop не покрывает F3-max, стоимость поиска выше |
| V3-D | Лучший допустимый A/B/C seed + возврат |12/12|8/12|8/12|Показал отдельную проблему SVG-rounding, не рекомендован |
| V3-E | Округление D после размещения |9/12|9/12|7/12|Округление после proof ломает gaps/order; отклонён |
| V3-F | Precision-aware placement до проверки |12/12|12/12|8/12|Решены пересечения/границы/rounding;12 local witnesses |
| V3-G | Сохранение exact-contact certificates при коррекции |12/12|12/12|10/12|6 local witnesses, разрешённые invariants не ослаблены |
| **V3-H** | G + одна альтернативная CSP seed там, где не хватило certificate |**12/12**|**12/12**|**10/12**|**Рекомендуемая техническая основа;2 точных FAIL до принятия полного drawing** |
| Внешние callout-колонки / более высокий canvas | Читаемые подписи скученной группы вне нынешнего annulus, истинные отметки остаются |NOT RUN|NOT RUN|NOT RUN|Продуктовая альтернатива, требует адресного Owner/Analyst решения о композиции/domain. Не принят fallback и не гарантия реализуемости |

CSP15сек/cell — исследовательский upper stop, **не подтверждённая latency production**. В коде приложения алгоритм не запускался. Реальная UI-latency / выбор минимального необходимого поиска оцениваются после технического review; новые зависимости или сторонний solver не вводились.

## 4. Финальная матрица H и сохранившиеся контрпримеры

| Fixture | Frame CSS px | Реальные gap / clip / annulus / order | Tight labels / moved | Все изученные predicates клетки | Max displacement CSS px |
|---|---|---|---|---|---|
| sparse | 720 | PASS | 0/0 (нет смещений) | PASS | 0.000 |
| sparse | 448 | PASS | 0/0 (нет смещений) | PASS | 0.000 |
| sparse | 328 | PASS | 0/0 (нет смещений) | PASS | 0.000 |
| F1 | 720 | PASS | 3/3 | PASS | 8.157 |
| F1 | 448 | PASS | 6/6 | PASS | 8.295 |
| F1 | 328 | PASS | 8/8 | PASS | 8.279 |
| F3 | 720 | PASS | 5/6 | FAIL | 31.639 |
| F3 | 448 | PASS | 9/9 | PASS | 24.978 |
| F3 | 328 | PASS | 8/8 | PASS | 28.150 |
| F3-max | 720 | PASS | 20/21 | FAIL | 55.772 |
| F3-max | 448 | PASS | 24/24 | PASS | 77.742 |
| F3-max | 328 | PASS | 25/25 | PASS | 125.028 |

Sparse не получает ни смещения, ни leader. Для H native CTM origins и реальные component bounds **побитово эквивалентны** точным данным модели; это отдельно сверено для всех12 клеток. Фактические bbox / ink / M / font / anchor coordinates сохранены в raw records, screenshots связаны hash. Сводка — [result_summary.json](evidence/drawing_geometry_v3/result_summary.json), [exact verification](evidence/drawing_geometry_v3/verification.json), [native final audit](evidence/drawing_geometry_v3/actual_final_audit.json).

**Не закрыто:** F3/720 **jupiter** и F3-max/720 **true_node**. Для каждого независимый verifier доказал допустимость **всего возврата0,5 CSS px** при замороженных остальных; полный1px probe также даёт `LOCAL_STEP_FAIL`. Исходные P/A и точные рациональные параметры приведены в `H_residual_counterexamples` сводки. Например Jupiter P=(403,84765625;46,2490234375), reference=(399,861419677734375;74,77190399169921875). Эти два FAIL нельзя скрыть точностью округления, заменить UNPROVEN или объявить решёнными изображением. Это отказ текущего bounded compactor на конкретных данных, не доказательство невозможности выполнить критерий.

Все frame448/328, включая F3-max, проходят **и** объявленную geometry **и** directional compactness. Из108 позитивных certificates110 moved records нельзя выводить покрытие произвольных DTO или всего продукта. Длинный leader125,028px в F3-max/328 — фактический результат; local tightness не доказывает глобальную оптимальность / визуальную удобность этой композиции. Callout alternative может улучшить читаемость, но пока не измерена.

Снимки: [F1/448/H](evidence/drawing_geometry_v3/browser-run03/screenshots/F1-448-H.png), [F3/328/H](evidence/drawing_geometry_v3/browser-run03/screenshots/F3-328-H.png), [F3-max/328/H](evidence/drawing_geometry_v3/browser-run03/screenshots/F3-max-328-H.png), [F3-max/720/H](evidence/drawing_geometry_v3/browser-run03/screenshots/F3-max-720-H.png). Они показывают исследуемые компоненты без полного zodiac / палитры; рисунок не выдаётся за финальный дизайн.

## 5. Evidence, controls и воспроизводимость

**108 моделей /108 browser records/screenshots:** BASE + V3-A…H, каждый4fixtures×3frames. Реальный установленный Chrome155.0.8059.40 / Windows, Node24.19.0, bundled Playwright; fonts по CDP **Segoe UI Symbol / Segoe UI**, M1:1 / DPR1 / zoom1. Ни API, ни engine, ни LLM / paid-smoke не вызывались. Локальный loopback server обслуживал только isolated harness.

Независимые exact controls **10/10**: equality/below diagonal-gap, исходные18/19/20, exact tight / tiny slack, независимый unrelated-ray case, clip equality / negative. Browser controls **8/8 в каждом из трёх запусков**:16/12 на равенстве и15,99/11,99 ниже, отсутствие SVG tabindex/button, наличие текста и неизменность DTO. Негативный glyph-missing / иной font / zoom не проверялись.

Первый `verification_initial_empty_order_bug.json` содержит ошибочный helper verdict для пустых marker/angle sets sparse; исправлена только empty-set проверка. Первичная сводка не учитывала C и это исправлено без изменения моделей. После exact-string serialization helper diagnostic displacement потребовал float-conversion; TypeError исправлен только в диагностике.

`actual_audit.json` сохраняет первоначальную decimal-интерпретацию native binary64, давшую в том числе искусственные пограничные FAIL порядка10⁻¹⁴. `actual_native_audit.json` пересчитывает те же исходные run01 по **точным IEEE-значениям**, без tolerance: реальные under-gap1,9999847412109375 и order FAIL остаются. H проверен той же native-политикой. До уточнения sufficient exact-axis certificate сохранён `verification_H_before_axis_priority.json`: неопределённость reused path-helper при collinear/opposite ray не отменяет самостоятельное closing-gap доказательство, когда вся исходная geometry независимо валидна. Отдельный контроль подтверждает это; никакие placement/raw inputs не менялись ради helper PASS.

Все первоначальные A…G / negative results сохраняются. Остановки per-distance CSP / constructor limits записаны, не называются непрерывной невозможностью. Post-audit не выполняет новый поиск. Для повторного исследования нужен новый output directory/run ID; single-use constructors/browser runners отказываются перезаписывать эти actual.

Команды из repo root (имя `node` ниже — установленный bundled executable, путь указан после блока):

```text
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/build.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/csp.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/portfolio.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/stable.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/final_model.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/contacts.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/complete.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/verify.py
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/browser.cjs
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/browser_stable.cjs
node docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/browser_final.cjs
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/actual_audit_native.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/actual_audit_stable.py
python -B -X utf8 docs/project_management/change_plans/ui-chart-wheel/developer/evidence/drawing_geometry_v3/actual_audit_final.py
git diff --check
```

Фактический executable Node — `C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`. Все перечисленные генерации / final verification / native audits завершились exit0; промежуточные отказы helper описаны выше. Это chronology нескольких bounded адресных уточнений specs, **не универсальный replay recipe поверх готовых данных**: portfolio требует предыдущего verification, single-use specs/outputs записывались до зависимых шагов. Сохранённые `sources-browser-run01/` — исходный harness до integer-origin уточнения; run02/03 используют текущий `geometry.html`. Итоговый read-only package audit проверяет hashes, сохранность baseline, ссылки/таблицы, syntax и scope; его actual подписываются в handoff после запуска.

## 6. Рекомендация и влияние на дальнейшую работу

**Рекомендую V3-H как техническую основу следующего drawing work item.** Границы и реальные зазоры теперь проверяемы на всей матрице; для минимальности остаются два локальных desktop-контрпримера. Перед принятием полного drawing нужно закрыть именно их и добавить отсутствующие fixed zodiac/sign labels, legend/palette и соответствующие native measurements. Отказ geometry / неполнота certificates не превращаются в разрешение скрыть факты или принять HTML-only fallback.

Внешние callout-подписи / более высокий canvas — отдельная альтернатива для Owner, если важнее сократить длинные leaders и упростить плотные случаи. Она меняет допустимую область и композицию; до адресного решения не реализуется. Нельзя автоматически уменьшить16/12 или gap2, скрыть R / ☌ либо разрешить полное смещение всех объектов.

**Бюджет:** прежние D003/D005 не открываются заново и повторно не начисляются. Этот опыт разрешён отдельно прямым Owner-запросом; его wall interval не равен effort и не добавляется автоматически к D00614–22 или полному9–14чд. D006 runtime scope/оценка пока прежнее предложение, HTML/controller независим от этих двух geometry findings. Новая полная оценка SVG / остатка проекта не вычислялась из неизвестных трудозатрат. Confidence высокая для данной матрицы / двух контрпримеров; средняя для технической основы, низкая для общей полноты drawing вне проверенного scope.

**NOT RUN:** production implementation / mounted UI / HTTP/HTTPS / browser acceptance, source Node/pytest product suites, runtime S1/F5/recovery, SVG→selection (исключено Owner), HTML44px/focus интеграция, полный zodiac / palette / whole visual design, cross-platform / touch / enlarged text / zoom / missing-glyph, runtime placement latency, generic adversarial DOM / renderer gateway. Engine/API/golden/new dependencies не менялись. Отсутствие product tests не заменяет их будущую проверку по назначенному implementation work item.

Далее Manager получает этот **новый** proposal / точные версии после отдельно разрешённой публикации и определяет адресную technical/test review применимость. Старые T007/R002 на D005 не получают нового предмета молча. Два остаточных FAIL — адресное продолжение, не новая общая Analysis и не пересогласование S1. Для кода остаются актуальный контракт / применимые technical решения / Owner конкретный scope-бюджет / ограниченный G3. Manager-owned статусы, gates, DP и чужие артефакты здесь не менялись. Commit/push/PR/сообщения другим чатам не выполнялись.
