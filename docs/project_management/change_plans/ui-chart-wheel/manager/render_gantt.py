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
        '<desc id="desc">Факт до G1: 13–17 октября 2026, фактический труд отдельно не измерен. TASK-D-003 передал исследование d24a24e / merge 030826f. T0 18.10.2026 15:17:04 MSK, текущий сеанс 1,9473 elapsed часа, SVG-spike 0,6023 часа внутри 6; это не полный timesheet подготовки. Измеренный heuristic не прошёл dense / native hit / минимальность. T004 / A005 / A007 приняты; контракт v3 + S1 закреплён на 2736e28. Исходный R001 r2 ожидается через Git. D005 опубликован на 8b8c4c8, текущая F/E construction отклонена. Owner принял пассивное SVG с управлением только из HTML; A008 готовит новую адресную редакцию, старые measurement FAIL не становятся PASS. T007/R002 разблокированы; D006 готовит первый scope controller/HTML. D00516–24 и experiment≤12 согласованы по handoff; общий бюджет / G3 не утверждены. Согласованные 20–28 ч сохранены; Developer предлагает 9–14 чд вместо 8–12, Owner новый бюджет ещё не согласовал. Нового предстартового круга нет.</desc>',
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
    text(40, 79, "Факт до G1 · подготовка · оценки ролей · актуализация 19 октября 2026", 19, color="#586879")
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
    text(50, 852, "ИСХОДНЫЕ ОЦЕНКИ РОЛЕЙ · условный полный объём до переоценки", 23, weight="650")
    text(50, 880, "Исторический сценарий 8–12 + 3–5 чд; подготовка отдельно не прибавляется. Даты поставки нет.", 17, color="#586879")
    def estimate_x(value):
        return left + value/17*(right-left)
    for value in [0, 4, 8, 11, 12, 17]:
        x = estimate_x(value)
        line(x, 896, x, 1110)
        text(x, 1138, str(value), 16, color="#586879", anchor="middle")
    estimates = [
        ("Нижний сценарий · Developer", 0, 8, 908, "#e6efff", "#215dc2", "Developer · 8 чд"),
        ("Нижний сценарий · Tester", 8, 3, 958, "#e1f2ec", "#16795d", "Tester · 3 чд"),
        ("Верхний сценарий · Developer", 0, 12, 1024, "#e6efff", "#215dc2", "Developer · 12 чд"),
        ("Верхний сценарий · Tester", 12, 5, 1074, "#e1f2ec", "#16795d", "Tester · 5 чд"),
    ]
    for label, begin, duration, y, fill, color, inside in estimates:
        text(50, y+25, label, 18)
        x, end_x = estimate_x(begin), estimate_x(begin+duration)
        rect(x, y, end_x-x, 36, fill, color, dash=True)
        text((x+end_x)/2, y+24, inside, 16, color=color, weight="650", anchor="middle")
    line(estimate_x(8), 944, estimate_x(8), 958, "#738297", dash=True)
    line(estimate_x(12), 1060, estimate_x(12), 1074, "#738297", dash=True)
    text(estimate_x(11)+14, 983, "Σ 11", 16, color="#16795d", weight="650")
    text(estimate_x(17)+14, 1099, "Σ 17", 16, color="#16795d", weight="650")
    text(50, 1206, "TASK-D-003 входит в подготовку исходного Developer-плана; 8–12 + 2,5–3,5 и вычитание остатка не обоснованы.", 17)
    text(50, 1235, "Developer предлагает 9–14 чд вместо 8–12, подготовка внутри; Owner новый бюджет ещё не согласовал.", 17)
    text(50, 1264, "В исходной сумме нет Manager / Analyst / Technical Reviewer, ожиданий, дополнительных reviews, приёмки и переноса.", 16, color="#586879")
    rect(28, 1290, 1384, 460, "#ffffff")
    text(50, 1326, "СЛЕДУЮЩИЕ ШАГИ · Owner выбрал управление только через таблицы", 23, weight="650")
    text(50, 1362, "Owner · ACCEPTED · SVG пассивно, выбор в HTML; подсветка колеса сохраняется.", 18, color="#16795d")
    text(50, 1392, "A008 · NOT_STARTED · узкая дельта требований / AS / sequences, новый SHA ожидается.", 18)
    text(50, 1422, "T007 / R002 · NOT_STARTED · D005 по старому контракту + применимость к новому scope.", 18)
    text(50, 1452, "D006 · NOT_STARTED · обновлённая оценка / план HTML → selection → пассивное SVG.", 18)
    text(50, 1482, "D005 · READY_FOR_REVIEW / IN_REVIEW · 8b8c4c8; прежние actual / FAIL сохранены.", 18, color="#9a580b")
    text(50, 1512, "D00516–24 ч / experiment ≤12; STARTED / stop / прежний бюджет не переписаны.", 18)
    text(50, 1542, "A006 · NOT_STARTED · отдельная already_applied-policy; независимая работа доступна.", 18)
    text(50, 1572, "A007 · DONE / APPROVED · 2736e28 — прежний контракт v3 + S1, не возврат Analyst.", 18, color="#16795d")
    text(50, 1608, "SVG hit-Q44 / отдельная SVG навигация исключены; доступные HTML controls сохраняются.", 17, color="#586879")
    text(50, 1638, "Visual gap / шрифты / долготы / минимальный разнос / R / ☌ / S1 остаются обязательными.", 17, color="#586879")
    text(50, 1668, "Экономия и новый срок ещё не оценены. Актуальные версии / approvals нужны перед G3.", 17, color="#586879")
    text(50, 1698, "Owner разрешил commit / push регистрации; роли получают новый вход через Git.", 17, color="#586879")
    text(50, 1728, "Notes №9: предлагать более дешёвые альтернативы / компромиссы; skills пока не менялись.", 17, color="#586879")
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
            "TASK-A-006": {"status": "NOT_STARTED", "subject": "already_applied semantics"},
            "TASK-A-008": {"status": "NOT_STARTED", "subject": "table-only selection contract delta", "input_sha": SOURCES["table_only_manager_baseline"], "published_output_sha": None},
            "TASK-D-006": {"status": "NOT_STARTED", "subject": "controller HTML stage scope and own estimate", "implementation_authorized": False, "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
            "TASK-T-007": {"status": "NOT_STARTED", "previous_status": "BLOCKED", "dependency_resolved": True, "technical_package_sha": SOURCES["d005_package"], "review_input_sha": SOURCES["d005_integration"], "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
            "TASK-R-002": {"status": "NOT_STARTED", "previous_status": "BLOCKED", "dependency_resolved": True, "technical_package_sha": SOURCES["d005_package"], "review_input_sha": SOURCES["d005_integration"], "analyst_contract_sha": SOURCES["analyst_contract_s1"]},
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
        "limited_g3_preparation": {"task": "TASK-D-006", "status": "NOT_STARTED", "scope": "HTML selection to passive SVG plan and own estimate only", "implementation_authorized": False, "g3_confirmed": False, "estimate_received": False},
        "manager_registration_publication": {"status": "OWNER_AUTHORIZED", "source": "Owner: Комит пуш и распечатай промты", "registration_commit": "first commit adding Manager section 2.23 and DP-O-008 revision", "remote_verification": "performed after push; exact SHA reported in Git handoff", "previous_registration_sha": SOURCES["table_only_manager_baseline"]},
        "reviewer_feasibility_v2_guidance": {"person_days": [1.25, 2.25], "owner_approved": False, "developer_estimate_received": True, "status": "historical reviewer guidance; own D005 estimate registered separately", "source": "R001 r2 via Owner; arithmetic of reviewer blocks"},
        "owner_table_only_selection": {"accepted": True, "decision_ref": "DP-O-008 / Manager section 2.23", "source": "Owner: Да принимаем такое решение; current chat 2026-10-19", "svg_selectable": False, "html_selection_updates_svg": True, "svg_pointer_q44_required": False, "svg_keyboard_controls_required": False, "html_accessibility_required": True, "visual_requirements_preserved": True},
        "pending_analyst_contract_update": {"task": "TASK-A-008", "published_baseline_sha": SOURCES["analyst_contract_s1"], "target_contract_sha": None, "blocks_final_g3_on_affected_scope": True, "blocks_independent_preparation_or_historical_reviews": False},
        "process_notes_added": {"item": 9, "subject": "propose lower-cost alternatives and explicit compromises", "actual_skill_files_modified": False},
        "analyst_contract_sha": SOURCES["analyst_contract_s1"],
        "snapshot_version": 11,
        "owner_ambiguity_choice": "S1",
        "owner_ambiguity_choice_source": "Owner message S1; Manager section 2.19",
        "manager_registration_date": "2026-10-19",
        "sources": SOURCES,
    }
    xml.append("<metadata>"+escape(json.dumps(metadata, ensure_ascii=False))+"</metadata>")
    xml.append("</svg>")
    OUT.write_text("\n".join(xml)+"\n", encoding="utf-8")
    print(f"GANTT_RENDER_OK actual_date_difference=4 inclusive_dates=5 preparation=2.5-3.5_person_days experiment_max_hours=6 deadline_end_working_day=4 t0=2026-10-18T15:17:04+03:00 package=d24a24e forecast=9-14_PROPOSED estimates=8-12/3-5 totals=11-17 output={OUT}")

if __name__ == "__main__":
    render()
