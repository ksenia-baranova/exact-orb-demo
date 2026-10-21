"""Run local regression suites once; save independent Tester command evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, platform, subprocess, sys, time
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
PIN = "0da99518ada67603b08ab4220d337e3a5e3aae60"
NODE = "C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
assert git("rev-parse", "HEAD") == PIN
assert git("branch", "--show-current") == "test/ui-chart-wheel"
assert not (HERE / "suites.json").exists(), "Refuse to overwrite evidence"
utc = lambda: datetime.now(timezone.utc).isoformat()
sha = lambda data: hashlib.sha256(data).hexdigest()
sources = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes().replace(b"\r\n", b"\n"))
           for p in (ROOT / "src/exact_orb/http_api/ui").iterdir() if p.suffix in (".mjs", ".css", ".html")}
target_node = ["tests/ui/" + x + ".test.mjs" for x in
               ("accepted_chart", "aspect_view", "chart_selection", "owner_feedback", "wheel_layout")]
all_node = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tests/ui").glob("*.test.mjs"))
py = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider"]
jobs = [
    ("node_target", [NODE, "--test", "--test-reporter=tap", *target_node]),
    ("python_target", [*py, "tests/http_api/test_ui_delivery.py", "tests/test_module_boundaries.py", "-q"]),
    ("node_all_ui", [NODE, "--test", "--test-reporter=tap", *all_node]),
    ("python_http_api", [*py, "tests/http_api", "-q"]),
    ("python_full", [*py, "-q"]),
]
record = {"tested_sha": PIN, "branch": "test/ui-chart-wheel", "author": "Codex / Tester",
          "started_utc": utc(), "python": sys.version, "platform": platform.platform(),
          "source_sha256_lf": sources, "commands": [],
          "scope": "Local regression suites; full pytest does not imply whole functional coverage"}
for name, args in jobs:
    print("START", name, flush=True)
    begin = time.perf_counter()
    result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (HERE / (name + ".log")).write_bytes(result.stdout)
    text = result.stdout.decode("utf-8", errors="replace")
    item = {"name": name, "argv": args, "exit_code": result.returncode,
            "elapsed_seconds": time.perf_counter() - begin, "finished_utc": utc(),
            "log": name + ".log", "log_sha256": sha(result.stdout), "tail": text.splitlines()[-12:]}
    record["commands"].append(item)
    (HERE / "suites.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FINISH", name, "exit=" + str(result.returncode), "\n" + "\n".join(item["tail"]), flush=True)
record["finished_utc"] = utc()
record["head_after"] = git("rev-parse", "HEAD")
record["production_delta_after"] = git("diff", "--name-only", "--", "src", "tests", "pyproject.toml")
assert record["head_after"] == PIN and not record["production_delta_after"]
(HERE / "suites.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("TESTER_REGRESSION_COMPLETE", flush=True)
sys.exit(any(c["exit_code"] for c in record["commands"]))
