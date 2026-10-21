# Подготовка интеграции ui-chart-wheel в main

Проверенная база `bba8d6cfb22f586f86c3035423f2535ede158b9f`, change `72ab4e30321884ddabe4205505216a7595d8bfeb`, merge-base `9dd8b96fe25f6644b7820c03a784ce04aa33cf87`.
Main tree равен исходному5355510; кодовых пересечений нет. Никакой настоящий merge не выполнялся.

После разрешённой публикации исправлений, адресного T009, решения ADR и отдельного registry PR:

1. Повторить fetch; при движении main заново классифицировать пересечение и обновить этот план.
2. В согласованном change checkout интегрировать main; сохранить актуальные версии следующих16 документов вместо удалений прежнего revert.
3. Сохранить опубликованный main-реестр (не вернуть его устаревшую копию); сравнить итоговый tree с проверенным change и registry SHA.
4. Зафиксировать CandidateSHA, выполнить нужные проверки; старые runtime results остаются на9974195, применимость подтверждается diff.
5. После разрешённого final PR/merge проверить main tree, записать PR/MergeSHA; только затем «Поставка: интегрирована».

| Путь | Сохранить Git blob change |
|---|---|
| `docs/project_management/change_plans/ui-chart-wheel/analyst/decision_input.patch` | `868ab870603d82ef054c1ef3d3a065bd2f7387f9` |
| `docs/project_management/change_plans/ui-chart-wheel/analyst/findings.md` | `800fc3ea5a764ec6c10f417901e6c85a3e01f7c0` |
| `docs/project_management/change_plans/ui-chart-wheel/analyst/package_manifest.json` | `6f69e4d2cf78bd01e7fa7845d27f0fa91afd3cd1` |
| `docs/project_management/change_plans/ui-chart-wheel/analyst/sources.md` | `3d018e1fb5188422d2b7cb75eef90944abc923be` |
| `docs/project_management/change_plans/ui-chart-wheel/analyst_artifact.md` | `9de7b28f73dfd07f87707335c5eed527ada6f041` |
| `docs/project_management/change_plans/ui-chart-wheel/manager_artifact.md` | `6c1d719238d3567c449dbcc2eb7dbcbf0305a0c4` |
| `docs/project_management/change_plans/ui-chart-wheel/process_notes.md` | `177d9fdba94fc82d98e341d902384553682eccf4` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/coverage_matrix.md` | `3088349e562b47aed87ebc1fcc7cbb76b7b6027e` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/decision_input.patch` | `8e2759f132cad5d1f69d797b7450e5ac637b9c62` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/defects.md` | `b76ad1d5a9c1daa6fe608d34481ad0b71b54c71f` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/evidence/review.json` | `2cf95f688041751504bc9464ec4be751fa43aae2` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/evidence/validate_review.py` | `8c898929aeb1a682756f1c342380c258cfe1e01a` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/evidence/validation.txt` | `ef66d00d04487054035cae0fb5a3e1e1a0b5d484` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/test_plan.md` | `544141155623119fb48ee0f0fc2b12a9697b85e2` |
| `docs/project_management/change_plans/ui-chart-wheel/tester/testability_review.md` | `d8a54c364dfa1a4ea82daceccf4080c038727e4e` |
| `docs/project_management/change_plans/ui-chart-wheel/tester_artifact.md` | `c2f701ecd9f35d7afdc25ffb0503ca1dabaef7e1` |

Для уже изменённых в этой сессии документов сохранить новую опубликованную редакцию; blob выше фиксирует исходный72ab4e3, не разрешает откат локальных исправлений.
