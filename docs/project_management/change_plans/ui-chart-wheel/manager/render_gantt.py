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
SOURCES = {
    "manager_start": "427658aaff74f21585196c8d3f95a926b81828b6",
    "analyst_first": "683bdd0c1f5a0e65735f4e48127d408300ec697c",
    "analyst_v3": "2634b224894b1046113557bfe241f0a5f2d46f8c",
    "developer_estimate": "f9c70f75ea815b2f3bf7e01426ee5afe65b31606",
    "tester_estimate": "7e95c0f680cc790fc8b45d9e25d69cc6e94fbc12",
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
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="940" viewBox="0 0 1440 940" role="img" aria-labelledby="title desc">',
        '<title id="title">ui-chart-wheel — Gantt: факт до G1 и оценки ролей</title>',
        '<desc id="desc">Календарный период до регистрации G1: 13–17 октября 2026. Наблюдаемое окно Analyst заканчивается публикацией v3 16 октября. Фактические человеко-дни не измерены. Будущие оценки: Developer 8–12 чд, Tester 3–5 чд, условная последовательная цепочка 11–17 рабочих дней без календарной даты старта.</desc>',
        '<style>text{font-family:"Segoe UI","DejaVu Sans",sans-serif;fill:#172536} .muted{fill:#586879} .small{font-size:16px} .label{font-size:18px} .section{font-size:23px;font-weight:650} .grid{stroke:#dce4ec;stroke-width:1} .estimate{stroke:#215dc2;stroke-dasharray:6 4;stroke-width:2}</style>',
        '<rect width="1440" height="940" fill="#f1f5f9"/>',
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
    text(40, 79, "Факт до G1 и оценочный Gantt оставшегося объёма · срез 17 октября 2026", 19, color="#586879")
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

    rect(28, 456, 1384, 354, "#ffffff")
    text(50, 492, "ОЦЕНКИ РОЛЕЙ · условные рабочие дни оставшейся цепочки", 23, weight="650")
    text(50, 520, "День 0 — начало оставшегося Developer-объёма. Календарная дата старта не назначена.", 17, color="#586879")
    def estimate_x(value):
        return left + value/17*(right-left)
    for value in [0, 4, 8, 11, 12, 17]:
        x = estimate_x(value)
        line(x, 536, x, 750)
        text(x, 778, str(value), 16, color="#586879", anchor="middle")
    estimates = [
        ("Нижний сценарий · Developer", 0, 8, 548, "#e6efff", "#215dc2", "Developer · 8 чд"),
        ("Нижний сценарий · Tester", 8, 3, 598, "#e1f2ec", "#16795d", "Tester · 3 чд"),
        ("Верхний сценарий · Developer", 0, 12, 664, "#e6efff", "#215dc2", "Developer · 12 чд"),
        ("Верхний сценарий · Tester", 12, 5, 714, "#e1f2ec", "#16795d", "Tester · 5 чд"),
    ]
    for label, begin, duration, y, fill, color, inside in estimates:
        text(50, y+25, label, 18)
        x, end_x = estimate_x(begin), estimate_x(begin+duration)
        rect(x, y, end_x-x, 36, fill, color, dash=True)
        text((x+end_x)/2, y+24, inside, 16, color=color, weight="650", anchor="middle")
    line(estimate_x(8), 584, estimate_x(8), 598, "#738297", dash=True)
    line(estimate_x(12), 700, estimate_x(12), 714, "#738297", dash=True)
    text(estimate_x(11)+14, 623, "Σ 11", 16, color="#16795d", weight="650")
    text(estimate_x(17)+14, 739, "Σ 17", 16, color="#16795d", weight="650")
    text(50, 846, "Developer 8–12 чд включает подготовку / ADR / spike до 0,75 чд; время spike не прибавляется повторно.", 17)
    text(50, 875, "Реализация — после G3; тестирование — после G4. Верхняя оценка Developer условна до измерений.", 17)
    text(50, 904, "Не включены Manager / Analyst / Technical Reviewer, ожидания, дополнительные reviews, приёмка и чистовой перенос.", 16, color="#586879")
    metadata = {
        "timezone": "Europe/Moscow",
        "calendar_actual": {"start": start.isoformat(), "g1_registration": G1_DATE.isoformat(), "analyst_v3_publication": analyst_end.isoformat(), "date_difference_days": 4, "inclusive_dates": 5},
        "actual_person_days": None,
        "role_estimates": {"developer_person_days": DEV_ESTIMATE, "tester_person_days": TEST_ESTIMATE, "serial_scenarios": [11, 17], "calendar_start": None, "developer_includes_pre_g3_preparation": True},
        "sources": SOURCES,
    }
    xml.append("<metadata>"+escape(json.dumps(metadata, ensure_ascii=False))+"</metadata>")
    xml.append("</svg>")
    OUT.write_text("\n".join(xml)+"\n", encoding="utf-8")
    print(f"GANTT_RENDER_OK actual_date_difference=4 inclusive_dates=5 analyst_v3=2026-10-16 estimates=8-12/3-5 totals=11-17 output={OUT}")

if __name__ == "__main__":
    render()
