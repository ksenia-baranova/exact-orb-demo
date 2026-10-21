"""Покрытие требований изменения тестами по маркеру ``req``.

Использование::

    python scripts/req_coverage.py docs/project_management/changes/<change-id>
    python scripts/req_coverage.py docs/project_management/changes/<change-id> --matrix

Что проверяется:

1. У каждого REQ инкремента с action ADD или MODIFY есть хотя бы один тест
   с ``@pytest.mark.req("<REQ>")``, если REQ не перечислен в разделе
   «Не тестируем» тест-плана.
2. У каждого теста в ``tests/acceptance/`` есть маркер ``req``.
3. Маркер ссылается на существующий REQ: из инкремента или из
   ``docs/requirements/``; ссылка на REQ с action REMOVE — ошибка.

Тесты не запускаются: скрипт только собирает их через pytest.
Код возврата: 0 — пробелов нет, 1 — есть пробелы, 2 — ошибка входных данных
или сбора тестов.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REQ_ID = re.compile(r"\bREQ-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
REQ_HEADING = re.compile(r"^## (REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b")
ACTION_LINE = re.compile(r"^action:\s*(ADD|MODIFY|REMOVE)\b")
ACCEPTANCE_DIR = "tests/acceptance/"


@dataclass
class Increment:
    active: list[str] = field(default_factory=list)  # ADD и MODIFY, в порядке файла
    removed: set[str] = field(default_factory=set)
    without_action: list[str] = field(default_factory=list)


def read_increment(path: Path) -> Increment:
    """REQ инкремента по заголовкам «## REQ-…» и строке action под ними."""
    inc = Increment()
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = REQ_HEADING.match(line)
        if heading:
            if current is not None:
                inc.without_action.append(current)
            current = heading.group(1)
            continue
        action = ACTION_LINE.match(line)
        if action and current is not None:
            if action.group(1) == "REMOVE":
                inc.removed.add(current)
            else:
                inc.active.append(current)
            current = None
    if current is not None:
        inc.without_action.append(current)
    return inc


def read_not_tested(path: Path) -> set[str]:
    """REQ из первой ячейки строк таблицы в разделе «## Не тестируем» тест-плана.

    Колонка «Почему» не учитывается: упоминание REQ в причине не исключает его из проверки.
    """
    if not path.exists():
        return set()
    ids: set[str] = set()
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Не тестируем"
            continue
        if inside and line.lstrip().startswith("|"):
            first_cell = line.strip().strip("|").split("|", 1)[0]
            ids.update(REQ_ID.findall(first_cell))
    return ids


def known_req_ids(requirements_dir: Path) -> set[str]:
    """Все REQ, упомянутые в docs/requirements/ (действующие и прежние документы)."""
    ids: set[str] = set()
    for md in requirements_dir.rglob("*.md"):
        ids.update(REQ_ID.findall(md.read_text(encoding="utf-8")))
    return ids


class _Collector:
    def __init__(self) -> None:
        self.items: dict[str, list[tuple[str, ...]]] = {}

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            self.items[item.nodeid] = [tuple(m.args) for m in item.iter_markers("req")]


def collect_tests(tests_path: Path) -> dict[str, list[tuple[str, ...]]]:
    collector = _Collector()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = pytest.main(
            ["--collect-only", "-q", "-p", "no:cacheprovider", str(tests_path)],
            plugins=[collector],
        )
    if code not in (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED):
        sys.stderr.write(output.getvalue())
        print(f"Сбор тестов завершился с кодом {int(code)}: это ошибка сбора, а не пробел покрытия.", file=sys.stderr)
        raise SystemExit(2)
    return collector.items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Покрытие REQ изменения тестами по маркеру req.")
    parser.add_argument("change_dir", type=Path, help="папка изменения: docs/project_management/changes/<id>")
    parser.add_argument("--tests", type=Path, default=REPO_ROOT / "tests", help="где собирать тесты")
    parser.add_argument("--matrix", action="store_true", help="напечатать матрицу REQ → тесты")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    args = parser.parse_args(argv)

    requirements = args.change_dir / "requirements.md"
    if not requirements.exists():
        print(f"Нет {requirements}: у изменения нет инкремента требований.", file=sys.stderr)
        return 2

    inc = read_increment(requirements)
    not_tested = read_not_tested(args.change_dir / "plans" / "test_plan.md")
    known = known_req_ids(REPO_ROOT / "docs" / "requirements") | set(inc.active)
    tests = collect_tests(args.tests)

    covered: dict[str, list[str]] = {}
    problems: list[str] = []
    for nodeid, markers in tests.items():
        rel = nodeid.replace("\\", "/")
        if not markers and (rel.startswith(ACCEPTANCE_DIR) or f"/{ACCEPTANCE_DIR}" in rel):
            problems.append(f"Тест без маркера req: {nodeid}")
        for marker_args in markers:
            if not marker_args:
                problems.append(f"Маркер req без ID: {nodeid}")
            for req in marker_args:
                if req in inc.removed:
                    problems.append(f"Тест проверяет удалённый {req}: {nodeid}")
                elif req not in known:
                    problems.append(f"Неизвестный {req} (опечатка?): {nodeid}")
                covered.setdefault(req, []).append(nodeid)

    for req in inc.without_action:
        problems.append(f"У {req} нет строки action: ADD, MODIFY или REMOVE")
    for req in inc.active:
        if req not in covered and req not in not_tested:
            problems.append(f"{req} без тестов и не указан в «Не тестируем»")

    if args.matrix:
        print("| REQ | Тесты |")
        print("| --- | --- |")
        for req in inc.active:
            if req in not_tested and req not in covered:
                cell = "не тестируем — см. тест-план"
            else:
                cell = "<br>".join(covered.get(req, [])) or "—"
            print(f"| {req} | {cell} |")
        print()

    tested = sum(1 for req in inc.active if req in covered)
    print(
        f"REQ в инкременте: {len(inc.active)}; с тестами: {tested}; "
        f"в «Не тестируем»: {len(set(inc.active) & not_tested - covered.keys())}; "
        f"тестов собрано: {len(tests)}"
    )
    if problems:
        print(f"Пробелы: {len(problems)}")
        for line in problems:
            print(f"- {line}")
        return 1
    print("Пробелов нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
