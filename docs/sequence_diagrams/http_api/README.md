# Sequence diagrams — HTTP API и Session Middleware

Диаграммы показывают transport boundary M1-6 и дополняют component sequences.

| № | Файл | Сценарий |
|---|---|---|
| 001 | `001-session-bootstrap.puml` | create/restore cookie и compact bootstrap без карты |
| 002 | `002-place-search.puml` | query grammar, IP limit и typed `PlaceSearch` outcomes |
| 003 | `003-build-natal.puml` | validation, deadline, admission, Orchestrator и cookie по outcome |
| 004 | `004-current-chart.puml` | отдельный load + `session_view`, stale/unavailable/read failure |

Источник публичного контракта —
[`docs/requirements/http_api.md`](../../requirements/http_api.md). ADR-0040
разделяет bootstrap и current chart; ADR-0041 определяет хранение карты.
Детали touch/CAS находятся в `../session/`, расчёта — в `../build_natal/` и
`../chart_artifacts/`.
