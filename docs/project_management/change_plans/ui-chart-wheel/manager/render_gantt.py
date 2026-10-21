"""Render the Manager-owned Gantt snapshot as a standalone SVG.

Documentation export only; Python standard library, no application dependency.
Dates are calendar observations in Europe/Moscow; estimates are role-owned
person-days. Update the Manager artifact and this snapshot together.
"""
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).with_name("gantt.svg")
TZ = timezone(timedelta(hours=3))
G1_DATE = date(2026, 10, 17)
DEV_ESTIMATE = (8, 12)
TEST_ESTIMATE = (3, 5)
PREPARATION_ESTIMATE = (2.5, 3.5)
EXPERIMENT_MAX_HOURS = 6
PACKAGE_DEADLINE_WORKING_DAY = 4
SOURCES = {
    "manager_start": "427658aaff74f21585196c8d3f95a926b81828b6",
    "analyst_first": "683bdd0c1f5a0e65735f4e48127d408300ec697c",
    "analyst_v3": "2634b224894b1046113557bfe241f0a5f2d46f8c",
    "developer_estimate": "f9c70f75ea815b2f3bf7e01426ee5afe65b31606",
    "tester_estimate": "7e95c0f680cc790fc8b45d9e25d69cc6e94fbc12",
    "preparation_estimate": "11a703ed6a01eb368f0f0ba23dc23f1e90fac81f",
    "preparation_integration": "49b9d7ce58be8171ee0159643f9f085afe090972",
    "prestart_analyst_review": "4055a9cb2bb18919c776c9d4e8585e2408a638c7",
    "prestart_tester_review": "71aa21cb79b046d25c77f68c6e87a9e48bd4c7fe",
    "criteria_v2": "f6f289cda25e7f228dff064175805130cc770b63",
    "criteria_v2_integration": "8a05b73c2af2c36043f9ede04834dd3867f4a686",
    "research_tester_review": "435337f49b200ca308ae9620efa9902adf1677f9",
    "research_analyst_review": "5de9e66c26496880f714f61f78126972dee4fbdd",
    "research_input": "8fb25770169166a3a4e94110eee684bd8b116474",
    "technical_package": "d24a24e04be32d0522674735388e9d2ea3e65c93",
    "technical_package_integration": "030826fd4e6bfa9613ad84ba7ed32adc15fddcd9",
    "a005_review": "4057d6ed37b24e082a2a4089eb7104da80d17ee5",
    "t004_review": "ad5206e30d855e44a9535f89dced1d8fe4699d17",
    "post_research_integration": "072fc291f8b0db24aaa34ad7a29abc96b472162a",
    "analyst_contract_s1": "2736e2848c977ec4c770a9a4dec2a0d7c1b62a71",
    "d005_assessment": "5eba30f74ce9af85fc13be048d3c0898f9d1a2cb",
    "d005_package": "8b8c4c818147b037cb90f93a42e64eb86d809183",
    "d005_integration": "cc4ecfff0208a15c64ae976bf5d6463cd47636ae",
    "table_only_manager_baseline": "dff5757e1b7b4896f8e1e9395fe61aaaaa4327e3",
    "table_only_publication": "07bb56ba5d49ec76de64df41ad80d175fbe90a2d",
    "full_wheel_first_publication": "5fdc4771d97307b2803fbe0f20a4833abfec645b",
    "full_wheel_package": "502589dbadd382fbe39e3cf1fd763abb52ffc620",
    "implementation_candidate": "883b6d3a47f7113e44ede73c9ad16b40f15bbdaf",
    "implementation_retested": "99741958b4bbee8884505920f4a02f2f19dea3e3",
    "implementation_tester_output": "f930c864d6a416acff8a49081585950853b931f9",
    "main_for_merge_preparation": "bba8d6cfb22f586f86c3035423f2535ede158b9f",
}

def published_date(sha):
    stamp = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "-s", "--format=%cI", sha],
        text=True, encoding="utf-8",
    ).strip()
    return datetime.fromisoformat(stamp).astimezone(TZ).date()

def render():
    start = published_date(SOURCES["manager_start"])
    analyst_start = published_date(SOURCES["analyst_first"])
    analyst_end = published_date(SOURCES["analyst_v3"])
    manager = (OUT.parent.parent / "manager_artifact.md").read_text(encoding="utf-8")
    assert "G1 | Подтверждён Manager 2026-10-17" in manager
    assert start == analyst_start == date(2026, 10, 13)
    assert analyst_end == date(2026, 10, 16)
    assert (G1_DATE - start).days == 4
    assert tuple(a+b for a,b in zip(DEV_ESTIMATE, TEST_ESTIMATE)) == (11, 17)

    xml = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1778" viewBox="0 0 1440 1778" role="img" aria-labelledby="title desc">',
        '<title id="title">ui-chart-wheel — факт, согласованная подготовка и условные оценки</title>',
        '<desc id="desc">Факт G1:13–17 октября, фактический труд отдельно не измерен. Исторические research и оценки сохранены. Реализация D007 завершена, AcceptedSHA883b6d3 по Owner21.10 с DEBT-UI-004. Tester Retested9974195:6/6 native cases,672/672 checks,229 UI tests,2959 Python passed и1 legacy skip;004 CLOSED,002/precision OPEN/INDETERMINATE. Перенос22REQ/53AS/11PUML выполнен; A008 ready for review, T008 ещё не выполнен. Формальные G3/G4/G5 не восстановлены, реестр долга ещё не опубликован в main, поставка нет.</desc>',
        '<style>text{font-family:"Segoe UI","DejaVu Sans",sans-serif;fill:#172536} .muted{fill:#586879} .small{font-size:16px} .label{font-size:18px} .section{font-size:23px;font-weight:650} .grid{stroke:#dce4ec;stroke-width:1} .estimate{stroke:#215dc2;stroke-dasharray:6 4;stroke-width:2}</style>',
        '<rect width="1440" height="1778" fill="#f1f5f9"/>',
    ]
    def text(x, y, value, size=18, color=None, weight=None, anchor=None):
        attrs = f'x="{x}" y="{y}" font-size="{size}"'
        if color: attrs += f' style="fill:{color}"'
        if weight: attrs += f' font-weight="{weight}"'
        if anchor: attrs += f' text-anchor="{anchor}"'
        xml.append(f'<text {attrs}>{escape(value)}</text>')
    def rect(x, y, width, height, fill, stroke=None, dash=False):
        attrs = f'x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" rx="6" fill="{fill}"'
        if stroke: attrs += f' stroke="{stroke}" stroke-width="2"'
        if dash: attrs += ' stroke-dasharray="6 4"'
        xml.append(f'<rect {attrs}/>')
    def line(x1, y1, x2, y2, color="#dce4ec", dash=False):
        tail = ' stroke-dasharray="5 4"' if dash else ""
        xml.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}"{tail}/>')
    def diamond(x, y, fill):
        xml.append(f'<path d="M{x:.2f},{y-9} l9,9 l-9,9 l-9,-9 z" fill="{fill}"/>')

    text(40, 48, "M1-8 · ui-chart-wheel", 30, weight="700")
    text(40, 79, "Факт до G1 · подготовка · оценки ролей · актуализация 21 октября 2026", 19, color="#586879")
    rect(28, 104, 1384, 332, "#ffffff")
    text(50, 139, "ФАКТ · календарные даты до зарегистрированного G1", 23, weight="650")
    text(50, 167, "13–17 октября: 4 дня между датами; 5 календарных дат включительно. Точность — день.", 17, color="#586879")
    left, right = 435.0, 1325.0
    def actual_x(day):
        return left + (day-start).days / (G1_DATE-start).days * (right-left)
    for offset in range(5):
        day = start + timedelta(days=offset)
        x = actual_x(day)
        line(x, 185, x, 361)
        text(x, 384, day.strftime("%d.%m"), 16, color="#586879", anchor="middle")
    facts = [
        ("Период Manager + Analyst до G1", start, G1_DATE, 199, "#215dc2", "4 календарных дня между датами"),
        ("Manager · координация / регистрация", start, G1_DATE, 255, "#506681", "13–17 октября"),
        ("Analyst · до публикации v3", analyst_start, analyst_end, 311, "#b37415", "13–16 октября"),
    ]
    for label, begin, end, y, color, inside in facts:
        text(50, y+25, label, 18)
        x, end_x = actual_x(begin), actual_x(end)
        rect(x, y, end_x-x, 38, color)
        text(x+14, y+25, inside, 17, color="#ffffff", weight="600")
        diamond(end_x, y+19, color)
    text(right+16, 224, "G1", 17, color="#215dc2", weight="700")
    text(actual_x(analyst_end)+16, 337, "v3 · 00:01 MSK", 16, color="#8c5b11")
    text(50, 414, "Окна ролей перекрываются. Часы / фактические чд Manager и Analyst отдельно не учитывались.", 17, color="#586879")

    rect(28, 456, 1384, 334, "#ffffff")
    text(50, 492, "РЕЗУЛЬТАТ ИССЛЕДОВАНИЯ · TASK-D-003 · пакет на review", 23, weight="650")
    text(50, 520, "T004 / A005 приняты; исходный R001 r2 ожидается через Git. Следующие задания показаны ниже.", 17, color="#9a580b")
    def preparation_x(value):
        return left + value / PACKAGE_DEADLINE_WORKING_DAY * (right-left)
    for value in range(5):
        x = preparation_x(value)
        line(x, 544, x, 702)
        text(x, 728, str(value), 16, color="#586879", anchor="middle")
    text(50, 582, "Полный труд · чд оценки", 18)
    rect(left, 555, preparation_x(PREPARATION_ESTIMATE[1])-left, 38, "#d5eee4", "#16795d", dash=True)
    rect(left, 555, preparation_x(PREPARATION_ESTIMATE[0])-left, 38, "#16795d")
    text(left+15, 580, "2,5–3,5 чд / 20–28 ч", 17, color="#ffffff", weight="650")
    text(50, 652, "Срок пакета · рабочие дни от T0", 18)
    line(left, 645, right, 645, "#16795d")
    diamond(right, 645, "#16795d")
    text(right-18, 633, "до конца 4-го рабочего дня", 17, color="#16795d", anchor="end")
    text(left, 681, "T0 = 18.10.2026 15:17:04 MSK; пакет d24a24e опубликован. Рабочий календарь не указан.", 16, color="#586879")
    text(50, 756, "Полный труд включает оценочную подготовку; это не измеренный остаток после T0. Эксперимент ≤6 ч внутри.", 16, color="#586879")
    text(50, 778, "Сеанс research: 1,9473 elapsed ч; spike: 0,6023 ч. Полный фактический труд подготовки отдельно неизвестен.", 16, color="#586879")


    rect(28, 816, 1384, 354, "#ffffff")
    text(50, 852, "РЕАЛИЗАЦИЯ · историческая оценка Developer · TASK-D-007", 23, weight="650")
    text(50, 880, "FW-01…06 · 40–64 часа / 5–8 чд · medium · реализация завершена; actual труд неизвестен.", 17, color="#9a580b")
    def estimate_x(value):
        return left + value/64*(right-left)
    for value in [0, 8, 16, 32, 40, 48, 64]:
        x = estimate_x(value)
        line(x, 896, x, 1110)
        text(x, 1138, str(value), 16, color="#586879", anchor="middle")
    estimates = [
        ("План роли · нижняя оценка", 40, 908, "#e6efff", "#215dc2", "40 рабочих часов"),
        ("План роли · верхняя оценка", 64, 974, "#e6efff", "#215dc2", "64 рабочих часа"),
    ]
    for label, duration, y, fill, color, inside in estimates:
        text(50, y+25, label, 18)
        x, end_x = estimate_x(0), estimate_x(duration)
        rect(x, y, end_x-x, 36, fill, color, dash=True)
        text((x+end_x)/2, y+24, inside, 16, color=color, weight="650", anchor="middle")
    text(50, 1065, "Исходный срок · от STARTED", 18)
    line(left, 1058, right, 1058, "#738297", dash=True)
    diamond(right, 1058, "#738297")
    text(left+14, 1046, "Историческое предложение: до конца восьмого рабочего дня", 17, color="#586879")
    text(left, 1094, "CH-02/03: 7–10 ч внутри FW-01. D006: 14–22 ч внутри полного объёма.", 16, color="#586879")
    text(50, 1206, "Прошлые исследования / подготовка повторно не начисляются. Независимый Tester в 40–64 ч не входит.", 17)
    text(50, 1235, "Исходные Developer 8–12 / Tester 3–5 чд и прогноз 9–14 сохранены для истории своих версий.", 17)
    text(50, 1264, "Owner21.10 завершает реализацию с долгом; фактический труд и отсутствующие gates не выдуманы.", 16, color="#586879")
    rect(28, 1290, 1384, 460, "#ffffff")

    text(50, 1326, "ПОДГОТОВКА К MAIN · принятый результат 883b6d3 · поставка нет", 23, weight="650")
    text(50, 1362, "Owner21.10 · завершить change; открытый остаток002 отложить в общий техдолг.", 18, color="#16795d")
    text(50, 1392, "A008 · READY_FOR_REVIEW · 22REQ / 53AS перенесены; source-копии удалены.", 18)
    text(50, 1422, "11 sequences перенесены: 8 текущих / 3 архивных; D008 остаётся для ADR.", 18)
    text(50, 1452, "T008 · NOT_STARTED · независимая сверка будущих точных A008 / D008 SHA.", 18)
    text(50, 1482, "D007 · DONE / APPROVED · реализация принята с исключением DEBT-UI-004.", 18, color="#16795d")
    text(50, 1512, "Tester · 6/6 native случаев · 672/672 checks · 229 UI / 2959 Python + 1 skip.", 18)
    text(50, 1542, "004 CLOSED; 002 / geometry precision OPEN / INDETERMINATE → DEBT-UI-004.", 18)
    text(50, 1572, "Owner: внутренние ряды по домам, first-five всех таблиц, passive SVG.", 18)
    text(50, 1608, "Труд отдельно не измерен. Исторические оценки / исследования не начисляются повторно.", 17, color="#586879")
    text(50, 1638, "Main bba8d6c: 21 документальное modify/delete пересечение из-за прежнего revert.", 17, color="#586879")
    text(50, 1668, "Поставка: нет. Перенос выполнен; независимая сверка / ADR / публикация долга ещё впереди.", 17, color="#586879")
    text(50, 1698, "Manager §2.29 / Plan v16 / Gantt v15. Owner разрешил commit/push; merge не выполнен.", 17, color="#586879")
    text(50, 1728, "Owner-завершение не превращает неполный oracle / отсутствующие formal gates в PASS.", 17, color="#586879")
    metadata = {
        "timezone": "Europe/Moscow",
        "calendar_actual": {"start": start.isoformat(), "g1_registration": G1_DATE.isoformat(), "analyst_v3_publication": analyst_end.isoformat(), "date_difference_days": 4, "inclusive_dates": 5},
        "actual_person_days": None,
        "role_estimates": {"developer_person_days": DEV_ESTIMATE, "tester_person_days": TEST_ESTIMATE, "serial_scenarios": [11, 17], "calendar_start": None, "developer_includes_pre_g3_preparation": True},
        "technical_preparation": {"task": "TASK-D-003", "person_days": PREPARATION_ESTIMATE, "hours": [20, 28], "includes_estimation_preparation": True, "owner_approved_date": "2026-10-17", "experiment_max_hours": EXPERIMENT_MAX_HOURS, "deadline_end_working_day": PACKAGE_DEADLINE_WORKING_DAY, "t0": "2026-10-18T15:17:04+03:00", "status": "READY_FOR_REVIEW", "resume_status": None, "previous_status": "BLOCKED", "research_authorized_date": "2026-10-18", "start_authorization": "Owner explicit instruction", "correction_task": "TASK-D-004", "correction_status": "DONE", "criteria_artifact_status": "APPROVED", "criteria_approval_scope": "definitions_for_bounded_research", "criteria_sha": SOURCES["criteria_v2"], "correction_estimate_hours": [3, 4], "correction_estimate_inside_preparation": True, "blocking_remarks": [], "resolved_definition_remarks": ["T005-R01", "T005-R02", "T005-R03"], "preflight_tasks": ["TASK-T-006", "TASK-A-004"], "preflight_status": "DONE", "preflight_repeats_required": False, "research_review_tasks": ["TASK-T-004", "TASK-R-001"], "technical_package_sha": SOURCES["technical_package"], "research_package_artifact_status": "IN_REVIEW", "research_session_elapsed_hours": 1.9473019444444446, "experiment_elapsed_hours": 0.6022752205555556, "semantic_review_task": "TASK-A-005", "post_research_review_status": "T004_DONE_R001_AWAITING_GIT", "semantic_review_status": "DONE", "semantic_review_artifact_status": "APPROVED", "semantic_followup_task": "TASK-A-006", "not_added_to_developer_total": True},
        "role_estimates_status": "historical_conditional_reestimate_after_research",
        "developer_forecast_proposal": {"person_days": [9, 14], "replaces_historical": [8, 12], "includes_preparation": True, "owner_approved": False, "source_sha": SOURCES["technical_package"]},
        "registered_reviews": {
            "TASK-T-004": {"task_status": "DONE", "artifact_status": "APPROVED", "source_sha": SOURCES["t004_review"]},
            "TASK-A-005": {"task_status": "DONE", "artifact_status": "APPROVED", "source_sha": SOURCES["a005_review"]},
            "TASK-A-007": {"task_status": "DONE", "artifact_status": "APPROVED", "source_sha": SOURCES["analyst_contract_s1"], "approval_scope": "S1_contract_delta_completeness_versions_traceability", "started": "2026-10-18T22:20:49+03:00", "role_estimate_hours": 4, "actual_effort_hours": None},
        },
        "received_external_review": {"task": "TASK-R-001", "revision": "r2", "source": "Owner message; Manager summary", "task_status": "IN_PROGRESS", "artifact_status": "DRAFT", "source_output_sha": None, "source_package_published": False, "manager_summary_path": "manager/review_inputs/task-r-001-r2-summary.md"},
        "next_tasks": {
            "TASK-A-006": {"status": "NOT_STARTED", "subject": "historical Analyst task; semantics resolved directly by Owner20.10, transfer in A008"},
            "TASK-A-008": {"status": "READY_FOR_REVIEW", "artifact_status": "IN_REVIEW", "executor_for_transfer": "Codex / Manager, direct Owner21.10", "subject": "final contract delta and clean transfer: passive SVG, internal house rows, first-five, aspect view, already_applied", "input_sha": SOURCES["implementation_candidate"], "published_output_sha": None},
            "TASK-D-006": {"status": "DONE", "artifact_status": "APPROVED", "approval_scope": "preparation_completeness_only", "subject": "controller HTML plan and own estimate", "source_sha": SOURCES["full_wheel_package"], "started": "2026-10-19T13:01:09+03:00", "preparation_estimate_hours": [0.5, 1.5], "implementation_authorized": False, "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
            "TASK-D-007": {"status": "DONE", "artifact_status": "APPROVED", "approval_scope": "delivered implementation accepted by Owner21.10 with DEBT-UI-004", "accepted_sha": SOURCES["implementation_candidate"], "actual_effort_hours": None, "resume_status": None, "started": "2026-10-19T22:11:37+03:00", "subject": "full passive wheel implementation FW-01 to FW-06", "input_sha": SOURCES["full_wheel_package"], "implementation_authorized": True, "authorization": "Owner direct process exception, Manager section 2.25", "g3_confirmed": False},
            "TASK-T-007": {"status": "NOT_STARTED", "previous_status": "BLOCKED", "dependency_resolved": True, "technical_package_sha": SOURCES["full_wheel_package"], "review_input_sha": SOURCES["full_wheel_package"], "previous_assignment_sha": SOURCES["table_only_publication"], "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
            "TASK-D-008": {"status": "NOT_STARTED", "subject": "remaining technical ADR / responsibilities; sequences already transferred by Manager", "input_sha": SOURCES["implementation_candidate"], "requires_new_geometry_research": False},
            "TASK-T-008": {"status": "NOT_STARTED", "subject": "independent clean-transfer fidelity and evidence applicability", "input_sha": SOURCES["implementation_candidate"], "depends_on_exact_outputs": ["TASK-A-008", "TASK-D-008"]},
            "TASK-R-002": {"status": "NOT_STARTED", "previous_status": "BLOCKED", "dependency_resolved": True, "technical_package_sha": SOURCES["full_wheel_package"], "review_input_sha": SOURCES["full_wheel_package"], "previous_assignment_sha": SOURCES["table_only_publication"], "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
        },
        "completion_registration": {
            "change_status": "ACCEPTED", "accepted_sha": SOURCES["implementation_candidate"],
            "retested_sha": SOURCES["implementation_retested"], "tester_output_sha": SOURCES["implementation_tester_output"],
            "owner_decision_date": "2026-10-21", "formal_g3_g4_g5_confirmed": False,
            "delivery_integrated": False, "merge_sha": None, "deferred_debt": "DEBT-UI-004",
            "tester_004": "CLOSED", "tester_002": "OPEN / precision INDETERMINATE",
            "registry_published_in_main": False,
            "documentary_transfer_completed": True, "source_files_removed": 13, "target_requirement_ids": 22, "target_scenario_ids": 53, "target_sequence_files": 11, "independent_transfer_review": False, "native_cases_pass": [6, 6], "native_checks_pass": [672, 672],
            "ui_tests_pass": 229, "pytest_pass": 2959, "pytest_legacy_skip": 1,
            "actual_effort_hours": None,
            "transfer_tasks": {"TASK-A-008": "READY_FOR_REVIEW", "TASK-D-008": "NOT_STARTED", "TASK-T-008": "NOT_STARTED"},
            "main_tree_equals_original_baseline": True, "main_is_ancestor": False,
            "merge_probe_documentary_modify_delete": 21, "merge_probe_mutates_index_or_worktree": False,
            "integration_resolution": "retain current change versions of the 21 reverted documentary paths; verify actual merge separately",
        },
        "d005_research": {
            "task_status": "READY_FOR_REVIEW", "artifact_status": "IN_REVIEW",
            "assessment_sha": SOURCES["d005_assessment"], "technical_package_sha": SOURCES["d005_package"],
            "integration_sha": SOURCES["d005_integration"], "role_estimate_hours": [16, 24],
            "owner_approved_hours": [16, 24], "approval_source": "Owner quote in signed Developer execution_start.json at D005 package",
            "experiment_hours_cap": 12, "browser_harness_hours_cap": 4, "analytics_hours_cap": 4,
            "started": "2026-10-19T00:15:25+03:00", "deadline_end_date": "2026-10-21",
            "final_stop": "2026-10-19T11:12:57.167959+03:00", "wall_envelope_hours": 10.9589,
            "actual_effort_hours": None, "candidate_accepted": False, "full_drawing_pass": False,
            "reported_actual": {"component_geometry_pass": [14, 24], "q44_certificates": [241, 438], "pointer_mismatch": [238, 2190], "keyboard_pass": [438, 438], "local_return_witnesses": 256},
            "independent_manager_browser_replay": False, "full_forecast_confirmed": False,
        },
        "limited_g3_preparation": {"task": "TASK-D-006", "status": "DONE", "artifact_status": "APPROVED", "scope": "HTML selection to passive SVG plan and own estimate only", "implementation_authorized": False, "g3_confirmed": False, "estimate_received": True, "future_hours": [14, 22], "independent_subset_hours": [7, 10], "subset_included_in_future_hours": True, "included_in_full_implementation": True},
        "manager_registration_publication": {"status": "OWNER_AUTHORIZED", "source": "Owner21.10 requested commit/push to change then Tester prompt; Manager section2.29", "transfer_sha_selector": "commit containing Manager section2.29 and this T008 assignment", "previous_registration_sha": "e0daa0e814d3d1fd34cadb8c17d064f19c4810f5"},
        "full_implementation_proposal": {"task": "TASK-D-007", "source_sha": SOURCES["full_wheel_package"], "work_items": ["FW-01", "FW-02", "FW-03", "FW-04", "FW-05", "FW-06"], "hours": [40, 64], "person_days": [5, 8], "confidence": "medium", "deadline_end_working_day": 8, "started": "2026-10-19T22:11:37+03:00", "owner_approved": False, "owner_question_pending": False, "start_authorization_independent_of_budget_approval": True, "includes_d006_controller_html": True, "previous_research_added_again": False, "independent_tester_included": False},
        "owner_column_decision": {"accepted": True, "source_sha": SOURCES["full_wheel_package"], "source_path": "developer/owner_decision_drawing_2026-10-19.md", "decision_refs": ["DP-O-011", "DP-O-012"], "conditional_column": True, "historical_superseded_by": "Owner20.10 internal house rows", "svg_category_text": False, "numeric_layout_approved_by_owner": False},
        "column_preparation": {"source_sha": SOURCES["full_wheel_package"], "run": "run07-ports", "studied_configurations_pass": [29, 29], "isolated_boundary_pass": [28, 28], "elapsed_minutes": 71.8126, "actual_effort_hours": None, "production_pass": False, "independent_manager_replay": False},
        "reviewer_feasibility_v2_guidance": {"person_days": [1.25, 2.25], "owner_approved": False, "developer_estimate_received": True, "status": "historical reviewer guidance; own D005 estimate registered separately", "source": "R001 r2 via Owner; arithmetic of reviewer blocks"},
        "owner_table_only_selection": {"accepted": True, "decision_ref": "DP-O-008 / Manager section 2.23", "source": "Owner: Да принимаем такое решение; current chat 2026-10-19", "svg_selectable": False, "html_selection_updates_svg": True, "svg_pointer_q44_required": False, "svg_keyboard_controls_required": False, "html_accessibility_required": True, "visual_requirements_preserved": True},
        "pending_analyst_contract_update": {"task": "TASK-A-008", "published_baseline_sha": SOURCES["analyst_contract_s1"], "target_contract_sha": None, "blocks_clean_delivery": True, "blocks_final_g3_on_affected_scope": False, "blocks_direct_owner_start": False, "blocks_independent_preparation_or_historical_reviews": False},
        "process_notes_added": {"item": 9, "subject": "propose lower-cost alternatives and explicit compromises", "actual_skill_files_modified": False},
        "analyst_contract_sha": SOURCES["analyst_contract_s1"],
        "snapshot_version": 15,
        "owner_ambiguity_choice": "S1",
        "owner_ambiguity_choice_source": "Owner message S1; Manager section 2.19",
        "manager_registration_date": "2026-10-21",
        "sources": SOURCES,
    }
    xml.append("<metadata>"+escape(json.dumps(metadata, ensure_ascii=False))+"</metadata>")
    xml.append("</svg>")
    OUT.write_text("\n".join(xml)+"\n", encoding="utf-8")
    print(f"GANTT_RENDER_OK actual_date_difference=4 inclusive_dates=5 preparation=2.5-3.5_person_days experiment_max_hours=6 deadline_end_working_day=4 t0=2026-10-18T15:17:04+03:00 package=d24a24e snapshot=15 full_wheel_hours=40-64_REFERENCE d006=DONE d007=DONE accepted=883b6d3 retested=9974195 delivery=false owner_direct_start=true formal_g3=false output={OUT}")

if __name__ == "__main__":
    render()
