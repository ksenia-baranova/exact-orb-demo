from pathlib import Path
import argparse, hashlib, json, subprocess

B = Path(__file__).resolve().parent
R = B.parents[6]
BASE = "07bb56ba5d49ec76de64df41ad80d175fbe90a2d"
META = B / "publication_2026-10-19.json"
rel = lambda p: p.relative_to(R).as_posix()
EXCLUDED = {rel(META), rel(B / "manifest.json"), rel(B / "validation.json")}

def git(*args, input=None):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=R, input=input)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def representation(raw, name):
    # These are the explicitly inventoried package extensions; PNG stays binary.
    if name.endswith(".png"):
        return raw, []
    assert b"\0" not in raw, name
    parts = raw.split(b"\n")
    crlf = [i for i, line in enumerate(parts[:-1]) if line.endswith(b"\r")]
    clean = b"\n".join(line[:-1] if i in set(crlf) else line for i, line in enumerate(parts))
    return clean, crlf

def oid(b):
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

parser = argparse.ArgumentParser(description="Verify Git LF payloads and reconstruct historic raw SHA without rewriting evidence.")
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--prepare", action="store_true")
mode.add_argument("--index", action="store_true")
mode.add_argument("--commit")
args = parser.parse_args()
if args.prepare:
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert not git("diff", "--cached", "--name-only").strip()
    paths = set(git("diff", "--name-only", "HEAD", "-z").decode().split("\0"))
    paths.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    paths.discard("")
    assert all(n.startswith("docs/project_management/change_plans/ui-chart-wheel/developer/") or n == "docs/project_management/change_plans/ui-chart-wheel/developer_artifact.md" for n in paths)
    entries = {}
    for name in sorted(paths - EXCLUDED):
        raw = (R / name).read_bytes()
        clean, lines = representation(raw, name)
        entries[name] = {"raw_sha256": sha(raw), "git_lf_sha256": sha(clean), "git_blob_oid": oid(clean), "crlf_line_indices": lines}
    result = {"author": "Codex / Developer", "baseline": BASE, "purpose": "Publication audit only; historic raw manifests remain unchanged. Git text=auto normalizes CRLF to LF. Raw bytes can be reconstructed in memory using zero-based crlf_line_indices before each LF; PNG is binary.", "excluded_self_and_generated_metadata": sorted(EXCLUDED), "entries": entries}
    META.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    print(f"PUBLICATION_PREPARED payloads={len(entries)} CRLF_files={sum(bool(e['crlf_line_indices']) for e in entries.values())}; no staging or runtime tests")
else:
    data = json.loads(META.read_text(encoding="utf8"))
    entries = data["entries"]
    target = args.commit
    if target:
        changed = set(git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", data["baseline"], target).decode().split("\0"))
        listing = git("ls-tree", "-r", "-z", target)
        blobs = {r.split(b"\t", 1)[1].decode(): r.split(b"\t", 1)[0].split()[2].decode() for r in listing.split(b"\0") if r}
    else:
        changed = set(git("diff", "--cached", "--name-only", "-z").decode().split("\0"))
        listing = git("ls-files", "--stage", "-z")
        blobs = {r.split(b"\t", 1)[1].decode(): r.split(b"\t", 1)[0].split()[1].decode() for r in listing.split(b"\0") if r}
    changed.discard("")
    assert changed == set(entries) | EXCLUDED, sorted(changed ^ (set(entries) | EXCLUDED))
    for name, e in entries.items():
        assert blobs[name] == e["git_blob_oid"], ("unexpected Git blob", name)
    requests = b"".join((blobs[n] + "\n").encode() for n in entries)
    content = git("cat-file", "--batch", input=requests)
    offset = 0
    for name, e in entries.items():
        end = content.index(b"\n", offset)
        header = content[offset:end].split()
        assert header[0].decode() == blobs[name] and header[1] == b"blob", name
        size = int(header[2])
        clean = content[end+1:end+1+size]
        offset = end+size+2
        assert sha(clean) == e["git_lf_sha256"], name
        lines = clean.split(b"\n")
        for i in e["crlf_line_indices"]:
            assert i < len(lines)-1, name
            lines[i] += b"\r"
        assert sha(b"\n".join(lines)) == e["raw_sha256"], ("raw reconstruction", name)
    assert offset == len(content)
    # Self and the two generated package metadata files have no embedded self-hash.
    # Compare their Git blobs with the normalized working bytes explicitly.
    for name in EXCLUDED:
        clean, _ = representation((R / name).read_bytes(), name)
        assert blobs[name] == oid(clean), ("generated metadata", name)
    print(f"PUBLICATION_OK target={target or 'INDEX'} changed={len(changed)} payloads={len(entries)} raw_SHA_reconstruction={len(entries)}/{len(entries)} metadata=3/3; scoped paths only")
