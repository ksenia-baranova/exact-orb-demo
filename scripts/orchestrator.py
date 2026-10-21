"""Оркестратор процесса работы над изменением v3 для ручного режима.

Скрипт делает бухгалтерию оркестратора: проверяет переходы по таблице,
создаёт файлы задач, пишет events.jsonl и статус в change.md. Агентов
запускает человек, коммиты тоже делает человек.

Использование::

    python scripts/orchestrator.py new ui-chart-wheel "Колесо карты" [--type refactor]
    python scripts/orchestrator.py next ui-chart-wheel [--dry-run] [--skip-coverage]
    python scripts/orchestrator.py status ui-chart-wheel
    python scripts/orchestrator.py fix ui-chart-wheel TASK-A-01 "У REQ-UI-03 нет source"
    python scripts/orchestrator.py cancel ui-chart-wheel
    python scripts/orchestrator.py log ui-chart-wheel TASK-A-01 --agent X --model Y --hours 1.5

``next`` идемпотентен: состояние каждый раз собирается заново из файлов
задач, DP, багов и events.jsonl, поэтому повторный запуск ничего не задваивает.
Правила — docs/development_approach/process/change-process-v3.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGES = REPO_ROOT / "docs" / "project_management" / "changes"
PROCESS = "docs/development_approach/process/change-process-v3.md"

ROLE_LETTER = {"owner": "O", "manager": "M", "analyst": "A", "developer": "D", "tester": "T", "reviewer": "R"}
LETTER_ROLE = {v: k for k, v in ROLE_LETTER.items()}
FINAL = {"done", "needs_decision", "has_bugs", "cancelled"}
BUILD = {"IN_DEVELOPMENT", "READY_FOR_TEST", "BUG_FIX"}
NO_SUBFLOW_KINDS = {"review", "code_review", "approve", "escalation", "accept", "answer_dp", "resolve_findings"}

TASK_TEXT = {
    "intake": "Заполнить change.md: цель, скоуп, вне скоупа, результат, источники; создать roadmap.md с оценкой анализа 2 чд. Owner подтверждает описание.",
    "analysis": "Написать requirements.md с источниками и sequences; дать оценку в чч и мч.",
    "answer_dp": "Owner отвечает на DP из inputs. Каждый DP — в ACCEPTED, DECLINED или ON_HOLD с решением словами owner'а.",
    "apply_decisions": "Учесть решения DP из inputs в своих документах или коде и продолжить исходную задачу.",
    "resolve_findings": "Решить каждый DP из inputs или отправить owner'у.",
    "review": "Ревью требований; план и оценка в чч и мч; reviewed_reqs заполнен.",
    "escalation": "Owner выбирает: accept_risk, reduce_scope или cancel. Выбор — в поле choice.",
    "summary": "Обновить roadmap.md и подготовить сводку для owner'а.",
    "approve": "Owner утверждает план или возвращает замечания как DP.",
    "implement": "Выполнить промт из inputs, включая шаг упрощения; target → related → full pytest; указать commit.",
    "test": "Приёмочные автотесты по тест-плану, прогон, баги; scripts/req_coverage.py без пробелов; перепроверить свои исправленные баги.",
    "code_review": "Ревью diff и приёмочных тестов; находки с четырьмя частями; «обязательно» и «желательно» — в bugs/; перепроверить свои исправленные баги.",
    "bug_fix": "Исправить баги из inputs; у каждого regression-тест, status FIXED и fixed_in.",
    "transfer": "Перенести требования и sequences изменения в current/.",
    "accept": "Owner принимает изменение или называет дефект (баг со слов owner'а).",
}


# --- файлы с frontmatter ---------------------------------------------------

def _value(raw: str):
    raw = raw.strip()
    if raw in ("", "null", "~"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
    return raw.strip("'\"")


def _strip_comment(raw: str) -> str:
    depth = 0
    for i, ch in enumerate(raw):
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "#" and depth == 0 and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i].rstrip()
    return raw.rstrip()


def read_doc(path: Path) -> tuple[dict, str]:
    """Frontmatter (плоские ключи, inline- и блочные списки) и тело файла."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    meta: dict = {}
    key = None
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1] in " \t" and key is not None and meta.get(key) is None and not stripped.startswith("- "):
            meta[key] = stripped          # вложенный YAML: значение есть, подробности не разбираем
            continue
        if stripped.startswith("- ") and key is not None:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(_strip_comment(stripped[2:]).strip("'\""))
            continue
        m = re.match(r"^([A-Za-z_][\w]*):(.*)$", line)
        if m:
            key = m.group(1)
            meta[key] = _value(_strip_comment(m.group(2)))
    return meta, "\n".join(lines[end + 1:])


def set_fields(path: Path, values: dict) -> None:
    """Заменить значения ключей frontmatter, сохранив комментарии; недостающие ключи дописать."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    done = set()
    for i in range(1, end):
        m = re.match(r"^([A-Za-z_][\w]*):(\s*)(.*)$", lines[i])
        if m and m.group(1) in values:
            k = m.group(1)
            comment = ""
            rest = m.group(3)
            stripped = _strip_comment(rest)
            if len(stripped) < len(rest.rstrip()):
                comment = "  " + rest[len(stripped):].strip()
            lines[i] = f"{k}: {_fmt(values[k])}{comment}"
            done.add(k)
    extra = [f"{k}: {_fmt(v)}" for k, v in values.items() if k not in done]
    lines[end:end] = extra
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def template(name: str) -> str:
    """Заготовка из шаблона артефакта: первый блок ```markdown в docs/development_approach/artifacts/<name>."""
    text = (REPO_ROOT / "docs" / "development_approach" / "artifacts" / name).read_text(encoding="utf-8")
    m = re.search(r"```markdown\n(.*?)\n```", text, re.S)
    if not m:
        raise SystemExit(f"В шаблоне {name} нет блока ```markdown")
    return m.group(1) + "\n"


# --- модель -----------------------------------------------------------------

@dataclass
class Task:
    id: str
    meta: dict
    path: Path

    @property
    def role(self) -> str: return self.meta.get("role") or LETTER_ROLE.get(self.id.split("-")[1], "?")
    @property
    def kind(self) -> str: return self.meta.get("kind") or ""
    @property
    def status(self) -> str: return self.meta.get("status") or "NEW"
    @property
    def resolution(self): return self.meta.get("resolution")
    @property
    def origin(self): return self.meta.get("origin")
    def lst(self, key: str) -> list: return list(self.meta.get(key) or [])
    @property
    def closed(self) -> bool: return self.status == "DONE" and self.resolution in FINAL


@dataclass
class Change:
    id: str
    dir: Path
    status: str
    cycle: int
    type: str
    tasks: dict[str, Task]
    order: list[str]                 # задачи в порядке создания
    events: list[dict]
    dps: dict[str, dict]
    bugs: dict[str, dict]
    entered_at: int = 0              # индекс в order, с которого начался текущий статус
    entry: dict = field(default_factory=dict)


def load(change_id: str) -> Change:
    d = CHANGES / change_id
    if not (d / "change.md").exists():
        raise SystemExit(f"Нет {d / 'change.md'}")
    meta, body = read_doc(d / "change.md")
    events = []
    if (d / "events.jsonl").exists():
        events = [json.loads(x) for x in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    tasks = {}
    for p in sorted((d / "tasks").glob("TASK-*.md")):
        m, _ = read_doc(p)
        tasks[p.stem] = Task(p.stem, m, p)
    order = [t for e in events for t in e.get("created", []) if t in tasks]
    unknown = [t for t in tasks if t not in order]
    if unknown:
        print(f"Внимание: задачи не созданы оркестратором и не учитываются: {', '.join(unknown)}")
    dps = {p.stem: read_doc(p)[0] for p in sorted((d / "dp").glob("DP-*.md"))}
    bugs = {p.stem: read_doc(p)[0] for p in sorted((d / "bugs").glob("BUG-*.md"))}
    ctype = "refactor" if re.search(r"^Тип:\s*refactor\b", body, re.M) else "feature"
    ch = Change(change_id, d, meta.get("status") or "INTAKE", int(meta.get("cycle") or 0), ctype,
                tasks, order, events, dps, bugs)
    count = 0
    for e in events:
        if e.get("n") is not None:
            ch.entered_at, ch.entry = count, e
        count += len([t for t in e.get("created", []) if t in tasks])
    return ch


# --- действия -----------------------------------------------------------------

class Plan:
    """Накопленные действия одного шага оркестратора."""

    def __init__(self, ch: Change, dry: bool):
        self.ch, self.dry = ch, dry
        self.created: list[str] = []
        self.messages: list[str] = []
        self.errors: list[str] = []
        self.transition = None

    def task(self, role: str, kind: str, inputs: list[str], origin: str | None = None, extra: dict | None = None) -> str:
        ch = self.ch
        letter = ROLE_LETTER[role]
        nums = [int(t.split("-")[2]) for t in list(ch.tasks) + self.created if t.split("-")[1] == letter]
        tid = f"TASK-{letter}-{max(nums, default=0) + 1:02d}"
        meta = {
            "id": tid, "change": ch.id, "role": role, "kind": kind, "gate": ch.status, "cycle": ch.cycle,
            "inputs": inputs, "origin": origin, "agent": None, "model": None, "status": "NEW", "resolution": None,
            "raised_dp": [], "raised_bugs": [], "changed_reqs": [], "reviewed_reqs": [], "commit": None, "estimate": None,
        }
        meta.update(extra or {})
        text = "---\n" + "\n".join(f"{k}: {_fmt(v)}" for k, v in meta.items()) + "\n---\n"
        text += f"## Задание\n{TASK_TEXT.get(kind, kind)}\n\nПравила — {PROCESS}, раздел «Задача (Task)».\n\n"
        text += "## Результат\n\n## Findings\n\n## Риски\n"
        path = ch.dir / "tasks" / f"{tid}.md"
        if not self.dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        ch.tasks[tid] = Task(tid, meta, path)
        ch.order.append(tid)
        self.created.append(tid)
        return tid

    def go(self, number: int, to: str, cycle: int | None = None, data: dict | None = None):
        ch = self.ch
        frm = ch.status if number != 1 else "—"
        ch.status = to
        if cycle is not None:
            ch.cycle = cycle
        ch.entered_at = len(ch.order)
        ch.entry = {"n": number, "from": frm, "to": to, "data": data or {}}
        self.transition = (number, frm, to)
        self.messages.append(f"Переход {number}: {frm} → {to} (cycle {ch.cycle})")

    def commit(self):
        ch = self.ch
        if self.dry or (not self.created and not self.transition):
            return
        event = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n": self.transition[0] if self.transition else None,
            "from": self.transition[1] if self.transition else ch.status,
            "to": ch.status, "cycle": ch.cycle, "created": self.created,
            "data": ch.entry.get("data", {}) if self.transition else {},
        }
        with (ch.dir / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        set_fields(ch.dir / "change.md", {"status": ch.status, "cycle": ch.cycle})
        ch.events.append(event)


# --- правила ----------------------------------------------------------------

def since_entry(ch: Change) -> list[Task]:
    return [ch.tasks[t] for t in ch.order[ch.entered_at:]]


def children(ch: Change, tid: str) -> list[Task]:
    return [ch.tasks[t] for t in ch.order if ch.tasks[t].origin == tid]


def effective(ch: Change, t: Task) -> str:
    """Итог «слота» задачи: её resolution или итог задачи, которая её продолжает."""
    for c in reversed(children(ch, t.id)):
        if c.role == t.role:
            return effective(ch, c)
    if not t.closed:
        return "pending"
    return "pending" if t.resolution == "needs_decision" else t.resolution


def validate_closed(ch: Change, t: Task) -> list[str]:
    errs = []
    if t.status == "DONE" and t.resolution not in FINAL:
        errs.append(f"{t.id}: DONE без resolution из словаря")
    if t.resolution == "needs_decision" and not t.lst("raised_dp"):
        errs.append(f"{t.id}: needs_decision без raised_dp")
    if t.resolution == "has_bugs" and not t.lst("raised_bugs"):
        errs.append(f"{t.id}: has_bugs без raised_bugs")
    if t.resolution == "has_bugs" and t.kind not in ("test", "code_review", "accept", "apply_decisions"):
        errs.append(f"{t.id}: has_bugs допустим только для test, code_review и accept")
    for dp in t.lst("raised_dp"):
        if dp not in ch.dps:
            errs.append(f"{t.id}: нет файла dp/{dp}.md")
    for bug in t.lst("raised_bugs"):
        if bug not in ch.bugs:
            errs.append(f"{t.id}: нет файла bugs/{bug}.md")
    return errs


def subflows(ch: Change, p: Plan) -> bool:
    """needs_decision вне ALIGNMENT и APPROVAL: вопросы к owner'у и Analyst, затем apply_decisions или переход 17."""
    handled = {e.get("data", {}).get("origin") for e in ch.events} | {ch.entry.get("data", {}).get("origin")}
    for tid in list(ch.order):
        t = ch.tasks[tid]
        if (t.resolution != "needs_decision" or t.kind in NO_SUBFLOW_KINDS or tid in handled
                or ch.status in ("CANCELLED", "ACCEPTED")):
            continue
        kids = children(ch, tid)
        if any(k.role == t.role for k in kids) or not t.lst("raised_dp"):
            continue                      # задачу уже продолжает та же роль (apply_decisions или fix)
        flow = [k for k in kids if k.kind in ("answer_dp", "resolve_findings")]
        if not flow:
            dps = t.lst("raised_dp")
            early = t.meta.get("gate") in ("INTAKE", "ANALYSIS")
            to_owner = [d for d in dps if ch.dps.get(d, {}).get("addressed_to") != "analyst" or early]
            to_analyst = [d for d in dps if d not in to_owner]
            if to_owner:
                p.task("owner", "answer_dp", to_owner, origin=tid)
            if to_analyst:
                p.task("analyst", "resolve_findings", to_analyst, origin=tid)
            return True
        if any(not k.closed for k in flow) or any(k.role == t.role for k in kids):
            continue
        dps = [d for k in flow for d in k.lst("inputs")]
        still_open = [d for d in dps if ch.dps.get(d, {}).get("status") == "OPEN"]
        if still_open:
            p.errors.append(f"DP всё ещё OPEN после ответа: {', '.join(still_open)}")
            continue
        changing = [d for d in dps if ch.dps[d].get("status") == "ACCEPTED" and ch.dps[d].get("changes_reqs")]
        if changing and ch.status in BUILD:
            p.go(17, "ANALYSIS", cycle=0, data={"dp": changing, "origin": tid})
            p.task("analyst", "apply_decisions", changing)
            return True
        p.task(t.role, "apply_decisions", t.lst("inputs") + dps, origin=tid)
        return True
    return False


def open_dp(ch: Change) -> list[str]:
    return [d for d, m in ch.dps.items() if m.get("status") == "OPEN"]


def check_change_md(ch: Change) -> list[str]:
    _, body = read_doc(ch.dir / "change.md")
    errs = []
    for name in ("Цель", "Результат", "Скоуп", "Вне скоупа", "Источники"):
        m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
        text = (m.group(1) if m else "").strip()
        if not text or re.fullmatch(r"(-\s*)?<[^>]*>", text):
            errs.append(f"change.md: раздел «{name}» не заполнен")
    return errs


def check_requirements(ch: Change) -> list[str]:
    path = ch.dir / "requirements.md"
    if not path.exists():
        return ["нет requirements.md"]
    errs, cur, has_source = [], None, False
    for line in path.read_text(encoding="utf-8").splitlines() + ["## END"]:
        if line.startswith("## "):
            if cur and not has_source:
                errs.append(f"{cur}: нет source")
            m = re.match(r"^## (REQ-[A-Z0-9-]+)", line)
            cur, has_source = (m.group(1) if m else None), False
        elif re.match(r"^source:\s*\S", line):
            has_source = True
    return errs


def prompts(ch: Change) -> list[str]:
    d = ch.dir / "plans" / "prompts"
    return [f"plans/prompts/{p.name}" for p in sorted(d.glob("*.md"))] if d.exists() else []


def prompt_done(ch: Change, prompt: str) -> bool:
    return any(effective(ch, ch.tasks[t]) == "done" for t in ch.order
               if ch.tasks[t].kind == "implement" and prompt in ch.tasks[t].lst("inputs"))


def advance(ch: Change, p: Plan, skip_coverage: bool) -> bool:
    """Один шаг по таблице переходов. True — что-то изменилось."""
    s = ch.status
    cur = since_entry(ch)
    main = [t for t in cur if not t.origin]

    def last(kind, role=None):
        found = [t for t in main if t.kind == kind and (role is None or t.role == role)]
        return found[-1] if found else None

    if s == "INTAKE":
        t = last("intake")
        if not t or effective(ch, t) != "done":
            return False
        errs = check_change_md(ch) + [f"OPEN DP: {d}" for d in open_dp(ch)]
        if errs:
            p.errors += errs
            return False
        p.messages.append("Проверьте сами: owner подтвердил описание в change.md.")
        if ch.type == "refactor":
            p.go(16, "ALIGNMENT", cycle=ch.cycle + 1)
            p.task("developer", "review", ["change.md"])
            p.task("reviewer", "code_review", ["change.md", "plans/implementation_plan.md", "plans/prompts/"])
        else:
            p.go(2, "ANALYSIS")
            p.task("analyst", "analysis", ["change.md"])
        return True

    if s == "ANALYSIS":
        t = main[-1] if main else None
        if not t or effective(ch, t) != "done":
            return False
        errs = check_requirements(ch) + [f"OPEN DP: {d}" for d in open_dp(ch)]
        if not any(x.meta.get("estimate") for x in ch.tasks.values() if x.role == "analyst"):
            errs.append("у Analyst не заполнена оценка")
        if errs:
            p.errors += errs
            return False
        prev = [x for x in (ch.tasks[i] for i in ch.order[: ch.entered_at])
                if x.kind in ("review", "code_review") and not x.origin and x.meta.get("gate") == "ALIGNMENT"
                and int(x.meta.get("cycle") or 0) == ch.cycle]
        changed = {r for x in cur if x.role == "analyst" for r in x.lst("changed_reqs")}
        reviewers = [("developer", "review"), ("tester", "review") if ch.type == "feature" else ("reviewer", "code_review")]
        if ch.cycle >= 1 and prev:
            reviewers = [(x.role, x.kind) for x in prev
                         if x.resolution == "needs_decision" or set(x.lst("reviewed_reqs")) & changed]
        p.go(3, "ALIGNMENT", cycle=ch.cycle + 1)
        for role, kind in dict.fromkeys(reviewers):
            p.task(role, kind, ["change.md", "requirements.md"])
        if not reviewers:
            p.messages.append("Повторное ревью никому не нужно: ревью прошлого цикла остаются done.")
        return True

    if s == "ALIGNMENT":
        esc = last("escalation")
        if esc:
            if not esc.closed:
                return False
            choice = esc.meta.get("choice")
            if choice == "accept_risk":
                return to_approval(ch, p, risk=True)
            if choice == "reduce_scope":
                p.go(4, "ANALYSIS", cycle=0, data={"escalation": esc.id})
                p.task("analyst", "resolve_findings", review_dps(ch, main))
                return True
            if choice == "cancel":
                p.errors.append("Owner выбрал отмену: выполните команду cancel.")
                return False
            p.errors.append(f"{esc.id}: в поле choice нужен accept_risk, reduce_scope или cancel")
            return False
        reviews = [t for t in main if t.kind in ("review", "code_review")]
        if any(not t.closed for t in reviews):
            return False
        if any(t.resolution == "needs_decision" for t in reviews):
            if ch.cycle >= 2:
                p.task("owner", "escalation", review_dps(ch, main), extra={"choice": None})
                p.messages.append("cycle = 2 и новые DP: эскалация owner'у")
                return True
            p.go(4, "ANALYSIS")
            p.task("analyst", "resolve_findings", review_dps(ch, main))
            return True
        return to_approval(ch, p, risk=False)

    if s == "APPROVAL":
        summ, appr = last("summary"), last("approve")
        if not summ:
            p.task("manager", "summary", ["roadmap.md", "risks.md"])
            return True
        if effective(ch, summ) != "done":
            return False
        if not appr:
            p.task("owner", "approve", ["roadmap.md", "requirements.md", "plans/"])
            return True
        if not appr.closed:
            return False
        if appr.resolution == "needs_decision":
            p.go(7, "ANALYSIS", cycle=0)
            p.task("analyst", "apply_decisions", appr.lst("raised_dp"))
            return True
        todo = [x for x in prompts(ch) if not prompt_done(ch, x)]
        if not todo:
            p.errors.append("нет промтов в plans/prompts/")
            return False
        tag = f"{ch.id}-approved-{1 + sum(1 for e in ch.events if e.get('n') == 6)}"
        p.go(6, "READY_FOR_DEVELOPMENT", data={"tag": tag})
        p.messages.append(f"Поставьте git-тег утверждённого плана: git tag {tag}. От него Reviewer считает diff.")
        p.task("developer", "implement", [todo[0], "plans/implementation_plan.md"])
        return True

    if s == "READY_FOR_DEVELOPMENT":
        if any(t.kind == "implement" and t.status != "NEW" for t in cur):
            p.go(9, "IN_DEVELOPMENT")
            return True
        return False

    if s == "IN_DEVELOPMENT":
        impl = [t for t in ch.order if ch.tasks[t].kind == "implement"]
        if impl and effective(ch, ch.tasks[impl[-1]]) != "done":
            return False
        todo = [x for x in prompts(ch) if not prompt_done(ch, x)]
        if todo:
            p.task("developer", "implement", [todo[0], "plans/implementation_plan.md"])
            return True
        missing = [t for t in impl if effective(ch, ch.tasks[t]) == "done" and not latest_of(ch, ch.tasks[t]).meta.get("commit")]
        if missing:
            p.errors += [f"{t}: не указан commit" for t in missing]
            return False
        p.go(10, "READY_FOR_TEST", data={"need_test": True})
        return True

    if s == "READY_FOR_TEST":
        need_test = ch.entry.get("data", {}).get("need_test", True)
        test, cr = last("test"), last("code_review")
        if need_test and not test:
            p.task("tester", "test", ["plans/test_plan.md", "requirements.md"] + ch.entry.get("data", {}).get("bugs", []))
            return True
        if test and effective(ch, test) == "pending":
            return False
        if not cr:
            p.task("reviewer", "code_review", [f"git diff {review_range(ch)}", "tests/acceptance/"]
                   + ch.entry.get("data", {}).get("bugs", []) + ([test.id] if test else []))
            return True
        if effective(ch, cr) == "pending":
            return False
        results = [effective(ch, x) for x in (test, cr) if x]
        bugs = [b for b, m in ch.bugs.items() if m.get("status") == "OPEN"]
        if "has_bugs" in results or bugs:
            errs = check_bugs(ch, bugs)
            if errs:
                p.errors += errs
                return False
            p.go(11, "BUG_FIX", data={"bugs": bugs})
            p.task("developer", "bug_fix", bugs)
            return True
        errs = [f"баг {b} в {m.get('status')}" for b, m in ch.bugs.items() if m.get("status") in ("OPEN", "FIXED")]
        if (ch.dir / "requirements.md").exists() and not skip_coverage:
            r = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "req_coverage.py"), str(ch.dir)],
                               capture_output=True, text=True, cwd=REPO_ROOT)
            if r.returncode == 1:
                errs.append("req_coverage.py нашёл пробелы:\n" + r.stdout.strip())
            elif r.returncode != 0:
                errs.append("req_coverage.py не смог собрать тесты:\n" + (r.stderr or r.stdout).strip()[-2000:])
        if errs:
            p.errors += errs
            return False
        p.go(13, "DONE")
        p.task("manager", "summary", ["roadmap.md", "risks.md", "plans/test_plan.md"])
        if (ch.dir / "requirements.md").exists():
            p.task("analyst", "transfer", ["requirements.md", "sequences/"])
        return True

    if s == "BUG_FIX":
        t = last("bug_fix")
        if not t or effective(ch, t) != "done":
            return False
        bugs = t.lst("inputs")
        errs = [] if latest_of(ch, t).meta.get("commit") else [f"{latest_of(ch, t).id}: не указан commit"]
        errs += [f"{b}: статус {ch.bugs.get(b, {}).get('status')}, нужен FIXED" for b in bugs
                if ch.bugs.get(b, {}).get("status") != "FIXED"]
        errs += [f"{b}: нет regression_test" for b in bugs if ch.bugs.get(b, {}).get("status") == "FIXED"
                 and not ch.bugs[b].get("regression_test")]
        if errs:
            p.errors += errs
            return False
        need_test = any(str(ch.bugs[b].get("raised_by", "")).startswith(("TASK-T", "TASK-M")) for b in bugs)
        p.go(12, "READY_FOR_TEST", data={"need_test": need_test, "bugs": bugs})
        return True

    if s == "DONE":
        summ, tr, acc = last("summary"), last("transfer"), last("accept")
        if any(x and effective(ch, x) != "done" for x in (summ, tr)):
            return False
        if not acc:
            p.task("owner", "accept", ["roadmap.md", "risks.md"])
            return True
        if not acc.closed:
            return False
        if acc.resolution == "has_bugs":
            p.go(15, "BUG_FIX", data={"bugs": acc.lst("raised_bugs")})
            p.task("developer", "bug_fix", acc.lst("raised_bugs"))
            return True
        if acc.resolution == "done":
            p.go(14, "ACCEPTED")
            p.messages.append("Слейте рабочую ветку в main и поставьте тег.")
            return True
    return False


def review_range(ch: Change) -> str:
    """Что смотрит Reviewer: после реализации — от тега перехода 6, после bug_fix — от прошлого code_review."""
    entry = ch.entry
    before = [ch.tasks[t] for t in ch.order[: ch.entered_at]]
    if entry.get("n") == 12:
        prev = [t for t in before if t.kind == "code_review"]
        fix = [t for t in before if t.kind == "bug_fix"]
        base = latest_of(ch, prev[-1]).meta.get("commit") if prev else None
        if not base:
            code = [t for t in before[:-1] if t.kind in ("implement", "bug_fix") and latest_of(ch, t).meta.get("commit")]
            base = latest_of(ch, code[-1]).meta.get("commit") if code else None
        head = latest_of(ch, fix[-1]).meta.get("commit") if fix else None
    else:
        tags = [e["data"]["tag"] for e in ch.events if e.get("n") == 6 and e.get("data", {}).get("tag")]
        impl = [t for t in before if t.kind == "implement"]
        base = tags[-1] if tags else None
        head = latest_of(ch, impl[-1]).meta.get("commit") if impl else None
    return f"{base or '<база>'}..{head or '<commit>'}"


def latest_of(ch: Change, t: Task) -> Task:
    for c in reversed(children(ch, t.id)):
        if c.role == t.role:
            return latest_of(ch, c)
    return t


def review_dps(ch: Change, main: list[Task]) -> list[str]:
    return [d for t in main for d in t.lst("raised_dp")]


def check_bugs(ch: Change, bugs: list[str]) -> list[str]:
    errs = []
    for b in bugs:
        meta = ch.bugs.get(b, {})
        body = (ch.dir / "bugs" / f"{b}.md").read_text(encoding="utf-8")
        if not meta.get("req"):
            errs.append(f"{b}: нет req или места в коде")
        if meta.get("severity") not in ("critical", "major", "minor"):
            errs.append(f"{b}: нет severity")
        if "## Шаги" not in body and "## Сценарий поломки" not in body:
            errs.append(f"{b}: нет шагов или сценария поломки")
    return errs


def to_approval(ch: Change, p: Plan, risk: bool) -> bool:
    errs = []
    if not (ch.dir / "plans" / "implementation_plan.md").exists():
        errs.append("нет plans/implementation_plan.md")
    if ch.type == "feature" and not (ch.dir / "plans" / "test_plan.md").exists():
        errs.append("нет plans/test_plan.md")
    errs += [f"DP {d} всё ещё OPEN: решите или переведите в ON_HOLD" for d in open_dp(ch)]
    reviews = [ch.tasks[t] for t in ch.order if ch.tasks[t].kind == "review"]
    errs += [f"{t.id}: нет оценки" for t in reviews if not latest_of(ch, t).meta.get("estimate") and not t.meta.get("estimate")]
    if errs:
        p.errors += errs
        return False
    p.go(5, "APPROVAL", data={"accepted_risk": risk})
    p.task("manager", "summary", ["roadmap.md", "risks.md"])
    return True


# --- команды ----------------------------------------------------------------

def cmd_next(args) -> int:
    ch = load(args.change)
    if ch.status in ("ACCEPTED", "CANCELLED"):
        print(f"{ch.id} в {ch.status}: шагов нет.")
        return 0
    continued = {t.origin for t in ch.tasks.values() if t.origin and t.role == ch.tasks.get(t.origin, t).role}
    errs = [e for t in ch.tasks.values() if t.status == "DONE" and t.id not in continued for e in validate_closed(ch, t)]
    if errs:
        print("Задачи закрыты с ошибками, переход не засчитывается:")
        print("\n".join(f"- {e}" for e in errs))
        print("Исправьте поле или создайте задачу на исправление: команда fix.")
        return 1
    p = Plan(ch, args.dry_run)
    for _ in range(20):
        if subflows(ch, p):
            continue
        if not advance(ch, p, args.skip_coverage):
            break
        if p.errors:
            break
    p.commit()
    print("\n".join(p.messages) or f"Статус {ch.status}: перехода нет.")
    if p.created:
        print("Создано: " + ", ".join(p.created))
    if p.errors:
        print("Условие перехода не выполнено:")
        print("\n".join(f"- {e}" for e in p.errors))
        return 1
    if args.dry_run:
        print("(dry-run: файлы не изменены)")
    if not p.created and not p.transition and not any(t.status != "DONE" for t in ch.tasks.values()):
        print("Нестандартная ситуация: скрипт не знает следующего шага, а открытых задач нет.")
        print(f"Решите шаг вручную по {PROCESS} и запишите в debug_log.md, что произошло.")
        return 3
    print_waiting(ch)
    return 0


def print_waiting(ch: Change) -> None:
    open_tasks = [ch.tasks[t] for t in ch.order if ch.tasks[t].status != "DONE"]
    if open_tasks:
        print("Ждём: " + ", ".join(f"{t.id} ({t.role}, {t.kind}, {t.status})" for t in open_tasks))


def cmd_status(args) -> int:
    ch = load(args.change)
    print(f"{ch.id} · {ch.type} · {ch.status} · cycle {ch.cycle}")
    for tid in ch.order:
        t = ch.tasks[tid]
        print(f"  {t.id:<10} {t.role:<9} {t.kind:<16} {t.meta.get('gate') or '':<22} {t.status:<11} {t.resolution or ''}")
    for name, items in (("DP", ch.dps), ("Баги", ch.bugs)):
        opened = [f"{k} {v.get('status')}" for k, v in items.items() if v.get("status") not in ("ACCEPTED", "DECLINED", "CLOSED")]
        if opened:
            print(f"{name}: " + ", ".join(opened))
    print_waiting(ch)
    return 0


CHANGE_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+){1,5}$")


def check_change_id(change_id: str) -> None:
    """id изменения — смысловое имя в kebab-case: минимум два слова с буквами, не номер."""
    words = [w for w in change_id.split("-") if re.search(r"[a-z]", w)]
    if not CHANGE_ID.match(change_id) or len(words) < 2:
        raise SystemExit(
            f"«{change_id}» не подходит: id изменения — смысловое имя в kebab-case латиницей, "
            "2–6 слов про область и суть, например ui-chart-wheel или session-sqlite-retention. Номера вида CH-042 не используются."
        )


def cmd_new(args) -> int:
    check_change_id(args.change)
    d = CHANGES / args.change
    if d.exists():
        raise SystemExit(f"{d} уже есть")
    active = []
    for other in CHANGES.glob("*/change.md") if CHANGES.exists() else []:
        status = read_doc(other)[0].get("status")
        if status not in ("ACCEPTED", "CANCELLED"):
            active.append(f"{other.parent.name} ({status})")
    if active and not args.force:
        raise SystemExit("В работе одно изменение за раз. Активно: " + ", ".join(active) + ". Флаг --force — только по решению owner'а.")
    (d / "tasks").mkdir(parents=True)
    for sub in ("dp", "bugs", "plans/prompts", "sequences"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    change = template("change.md").replace("<change-id>", args.change).replace("<название>", args.title)
    change = re.sub(r"^Тип: \w+", f"Тип: {args.type}", change, count=1, flags=re.M)
    (d / "change.md").write_text(change, encoding="utf-8")
    set_fields(d / "change.md", {"status": "INTAKE", "cycle": 0})
    (d / "debug_log.md").write_text(template("debug-log.md").split("| <YYYY-MM-DD>")[0]
                                    .replace("<change-id>", args.change), encoding="utf-8")
    ch = load(args.change)
    p = Plan(ch, False)
    p.go(1, "INTAKE")
    p.task("manager", "intake", ["запрос owner'а"])
    p.commit()
    print(f"Создано {d.relative_to(REPO_ROOT)}; {p.created[0]} для Manager.")
    return 0


def cmd_fix(args) -> int:
    ch = load(args.change)
    t = ch.tasks.get(args.task)
    if not t:
        raise SystemExit(f"Нет задачи {args.task}")
    p = Plan(ch, False)
    tid = p.task(t.role, t.kind, t.lst("inputs") + [t.id], origin=t.id)
    p.commit()
    path = ch.dir / "tasks" / f"{tid}.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "## Задание\n", f"## Задание\nИсправить результат {t.id}: {args.error}\n\n", 1), encoding="utf-8")
    print(f"Создана {tid} на исправление {t.id}.")
    return 0


def cmd_cancel(args) -> int:
    ch = load(args.change)
    if ch.status in ("ACCEPTED", "CANCELLED"):
        print(f"{ch.id} уже в {ch.status}: отменять нечего.")
        return 1
    for t in ch.tasks.values():
        if t.status != "DONE":
            set_fields(t.path, {"status": "DONE", "resolution": "cancelled"})
    p = Plan(ch, False)
    p.go(8, "CANCELLED")
    p.commit()
    print(f"{ch.id} → CANCELLED; открытые задачи закрыты с cancelled.")
    folder = ch.dir.relative_to(REPO_ROOT).as_posix()
    print("Откатите код, тесты и current/ этого изменения; папка изменения остаётся как история:")
    print(f"  git revert --no-commit $(git log --grep '\\[{ch.id}\\]\\[TASK-' --format=%H)")
    print(f"  git checkout HEAD -- {folder}")
    print(f'  git commit -m "[{ch.id}] revert: отмена изменения"')
    return 0


def cmd_log(args) -> int:
    path = CHANGES / args.change / "debug_log.md"
    row = (f"| {datetime.now().date()} | {args.task} | {args.agent}, {args.model} | {args.hours} | "
           f"{args.prompt_version} | {args.issue} | {args.fix} |\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(row)
    print(f"Записано в {path.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Оркестратор процесса изменения v3 (ручной режим).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("new", help="переход 1: папка изменения и задача intake")
    a.add_argument("change", help="смысловое имя в kebab-case, например ui-chart-wheel"); a.add_argument("title"); a.add_argument("--type", choices=["feature", "refactor"], default="feature")
    a.add_argument("--force", action="store_true", help="создать при другом активном изменении")
    a.set_defaults(func=cmd_new)
    a = sub.add_parser("next", help="проверить закрытые задачи, выполнить переход, создать следующие задачи")
    a.add_argument("change"); a.add_argument("--dry-run", action="store_true"); a.add_argument("--skip-coverage", action="store_true")
    a.set_defaults(func=cmd_next)
    a = sub.add_parser("status", help="статус, задачи, открытые DP и баги")
    a.add_argument("change"); a.set_defaults(func=cmd_status)
    a = sub.add_parser("fix", help="задача на исправление результата той же роли")
    a.add_argument("change"); a.add_argument("task"); a.add_argument("error"); a.set_defaults(func=cmd_fix)
    a = sub.add_parser("cancel", help="переход 8: отмена изменения")
    a.add_argument("change"); a.set_defaults(func=cmd_cancel)
    a = sub.add_parser("log", help="строка в debug_log.md")
    a.add_argument("change"); a.add_argument("task"); a.add_argument("--agent", required=True); a.add_argument("--model", required=True)
    a.add_argument("--hours", required=True); a.add_argument("--prompt-version", default="—")
    a.add_argument("--issue", default="—"); a.add_argument("--fix", default="—")
    a.set_defaults(func=cmd_log)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
