"""T-24/25 evidence controls. No production execution or legal acceptance."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
SHA = "6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5"
CHANGE = "docs/project_management/changes/terms-of-use/"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def source_verdict(evidence):
    assert evidence["status"] == "PASS"
    assert evidence["anonymous"] and not evidence["private"]
    assert evidence["deployment_sha"] == SHA
    assert evidence["tree"] == git("rev-parse", SHA + "^{tree}").strip()


published = json.loads((HERE / "public-source.json").read_text(encoding="utf-8"))
source_verdict(published)
controls = []
for key, value in [("status", "BLOCKED"), ("private", True), ("deployment_sha", "0" * 40)]:
    try:
        source_verdict({**published, key: value})
    except AssertionError:
        controls.append({"changed": key, "rejected": True})
    else:
        raise AssertionError("Source control unexpectedly accepted: " + key)

unapproved = "a362a9eb236cca59c01d3fcb885ca74faf57c448"
old_draft = git("show", unapproved + ":" + CHANGE + "terms_draft.md")
old_tasks = git("ls-tree", "-r", "--name-only", unapproved, CHANGE + "tasks")
old_dp = git("show", unapproved + ":" + CHANGE + "dp/DP-A-01.md")
assert "status: ACCEPTED" in old_dp
assert "Owner полный текст условий не утверждал" in old_draft
assert "TASK-O-02.md" not in old_tasks
approval = git("show", SHA + ":" + CHANGE + "tasks/TASK-O-02.md")
assert "status: DONE" in approval and "02cbd17e33ceffe52d465bdf6b8faf1d3c76864c" in approval
draft = git("show", "02cbd17e33ceffe52d465bdf6b8faf1d3c76864c:" + CHANGE + "terms_draft.md")
q = draft.split("## Текст для страницы после утверждения Owner\n", 1)[1].split("## Сверка Analyst", 1)[0].strip() + "\n"
digest = sha256(q.encode("utf-8")).hexdigest()
assert digest == "ee474d44cd2d8231660e3d5ab5a7d9946b72084ddabad7f22a0686281d7840a0" and digest in approval
debt = git("show", SHA + ":docs/project_management/technical_debt.md")
row = next(line for line in debt.splitlines() if line.startswith("| `DEBT-UI-001`"))
assert "CLOSED" not in row and "поставка интегрирована" in row
result = {"status": "PASS", "source_negative_controls": controls,
          "unapproved_packet": unapproved, "contact_accepted_without_text_approval": True,
          "approved_packet": "02cbd17e33ceffe52d465bdf6b8faf1d3c76864c", "approved_text_sha256": digest,
          "debt_closed_by_tester": False, "runtime_sha": SHA}
(HERE / "document-audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
