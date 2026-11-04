"""Explicit TASK-T-02 C7 check, anonymous HTTPS; excluded from offline pytest."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[6]
SHA = "6db88e0ea07c65db9e7aaa79731e5ab54c2f66c5"
REPO = "ksenia-baranova/exact-orb-demo"


def get(url):
    # No token, cookie, git credential helper, or authenticated browser context.
    with urlopen(Request(url, headers={"User-Agent": "exact-orb-independent-tester"}), timeout=30) as response:
        return response.status, response.url, response.read()


status, url, body = get(f"https://api.github.com/repos/{REPO}")
repository = json.loads(body)
assert status == 200 and repository["private"] is False
_, _, body = get(f"https://api.github.com/repos/{REPO}/git/ref/heads/change/terms-of-use")
ref = json.loads(body)
assert ref["object"]["sha"] == SHA
_, _, body = get(f"https://api.github.com/repos/{REPO}/git/commits/{SHA}")
commit = json.loads(body)
local_tree = subprocess.check_output(["git", "rev-parse", SHA + "^{tree}"], cwd=ROOT, text=True).strip()
assert commit["sha"] == SHA and commit["tree"]["sha"] == local_tree
status, final_url, html = get(f"https://github.com/{REPO}")
assert status == 200 and b"Sign in" in html
assets = {}
for relative in ["src/exact_orb/http_api/ui/index.html", "src/exact_orb/http_api/ui/main.mjs", "src/exact_orb/http_api/ui/styles.css", "LICENSE"]:
    _, _, public = get(f"https://raw.githubusercontent.com/{REPO}/{SHA}/{relative}")
    committed = subprocess.check_output(["git", "show", f"{SHA}:{relative}"], cwd=ROOT)
    assert public == committed, relative
    assets[relative] = sha256(public).hexdigest()
result = {"status": "PASS", "deployment_sha": SHA, "public_ref": ref["ref"], "tree": local_tree,
          "anonymous": True, "private": repository["private"], "repository_url": final_url, "assets": assets}
Path(__file__).with_name("public-source.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
