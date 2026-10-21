"""Read-only source/document audit; --write records this audit, never runs an SVG spike."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
R = 'docs/project_management/change_plans/ui-chart-wheel/'
PINS = {
    'before_sync': '8921e9d81d416f6ae49c401600c600d24e46c316',
    'manager_registration': '0083d81151f3af649feee9e7737ec6469c35cf1e',
    'material_input': '6c4607165085d7297f044cef026353f36f6c842f',
    'developer_v2': 'f9c70f75ea815b2f3bf7e01426ee5afe65b31606',
    'analyst_v3': '2634b224894b1046113557bfe241f0a5f2d46f8c',
    'tester_v2': '7e95c0f680cc790fc8b45d9e25d69cc6e94fbc12',
    'tester_review': 'c59cc3f68e7769841134801dc125633decade032',
    'analyst_review': '2f5579677114ea2dc86c66cf0fd656fdb5910df5',
    'main_baseline': '535551026af6eedaf2a0aa5c0daa96fa94655ec1',
}

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).replace(b'\r\n', b'\n')

def blob(sha, path):
    return git('show', f'{sha}:{path}')

def sha256(value):
    return hashlib.sha256(value.replace(b'\r\n', b'\n')).hexdigest()

def current(path):
    return (ROOT / path).read_bytes().replace(b'\r\n', b'\n')

base = PINS['manager_registration']
for pin in PINS.values():
    git('merge-base', '--is-ancestor', pin, base)
delta = git('diff', '--name-only', PINS['material_input'], base).decode().splitlines()
assert delta == [R + 'manager_artifact.md'], delta
shared = ['AGENTS.md', 'src', 'tests', 'docs/requirements', 'docs/sequence_diagrams', 'docs/development_approach', 'pyproject.toml']
assert not git('diff', '--name-only', PINS['main_baseline'], base, '--', *shared).strip()
assert not git('diff', '--name-only', base, '--', *shared).strip()
manager = current(R + 'manager_artifact.md')
assert manager == blob(base, R + 'manager_artifact.md')
dp = lambda value: [line for line in value.decode().splitlines() if re.match(r'^\| `DP-O-\d+` \|', line)]
input_dp = dp(blob(PINS['material_input'], R + 'manager_artifact.md'))
dp_delta = []
assert len(dp(manager)) == len(input_dp) == 14
for old, new in zip(input_dp, dp(manager)):
    a, b = old.split('|'), new.split('|')
    changed_columns = [i for i, pair in enumerate(zip(a, b)) if pair[0] != pair[1]]
    assert set(changed_columns) <= {8, 10}, (a[1], changed_columns)
    if changed_columns:
        item = {'id': a[1].strip().strip('`'), 'changed_columns': ['recommendations', 'evidence'], 'details': {}}
        for i in changed_columns:
            old_value, new_value = a[i].strip(), b[i].strip()
            item['details'][str(i)] = new_value[len(old_value):].strip() if new_value.startswith(old_value) else new_value
        dp_delta.append(item)
if '--details' in sys.argv:
    print(json.dumps(dp_delta, ensure_ascii=False, indent=2))
manifests = {}
for role, pin in [('developer', PINS['developer_v2']), ('analyst', PINS['analyst_v3'])]:
    manifest_path = R + role + '/package_manifest.json'
    assert current(manifest_path) == blob(pin, manifest_path)
    manifest = json.loads(blob(pin, manifest_path))
    entries = manifest['files']
    pairs = [(x['path'], x['sha256']) for x in entries] if isinstance(entries, list) else [(R + k, v) for k, v in entries.items()]
    assert len(pairs) == 9
    for path, expected in pairs:
        assert sha256(blob(pin, path)) == expected, path
        if path == R + role + '_artifact.md':
            assert current(path).startswith(blob(pin, path)), path
        else:
            assert current(path) == blob(pin, path), path
    manifests[role] = '9/9'
for role, pin in [('analyst', PINS['analyst_review']), ('tester', PINS['tester_review'])]:
    path = R + role + '_artifact.md'
    assert current(path) == blob(pin, path), path
tester_v2_paths = git('ls-tree', '-r', '--name-only', PINS['tester_v2'], '--', R + 'tester', R + 'tester_artifact.md').decode().splitlines()
assert len(tester_v2_paths) == 9
for path in tester_v2_paths:
    if path == R + 'tester_artifact.md':
        assert current(path).startswith(blob(PINS['tester_v2'], path)), path
    else:
        assert current(path) == blob(PINS['tester_v2'], path), path
for path in [R + 'tester/task_t003_review.md', R + 'tester/evidence/task_t003_review.json']:
    assert current(path) == blob(PINS['tester_review'], path), path
review = json.loads(current(R + 'tester/evidence/task_t003_review.json'))
for entry in review['sources']:
    assert sha256(blob(entry['sha'], entry['path'])) == entry['sha256_lf'], entry['path']
old_index = blob(PINS['developer_v2'], R + 'developer_artifact.md')
assert current(R + 'developer_artifact.md').startswith(old_index)
new_index = current(R + 'developer_artifact.md')[len(old_index):]
plan_path = R + 'developer/task_d003_implementation_plan.md'
report_path = R + 'developer/evidence/task_d003_preparation.json'
audit_path = R + 'developer/evidence/task_d003_preparation_check.py'
allowed = {R + 'developer_artifact.md', plan_path, report_path, audit_path}
changed = set(git('diff', '--name-only', base).decode().splitlines()) | set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
assert changed <= allowed, changed - allowed
report = {
    'task': 'TASK-D-003', 'phase': 'estimate_and_start_preparation',
    'pins': PINS, 'sync': 'fast-forward; initial tree clean; no reset/force',
    'input_to_registration_changed_paths': delta,
    'material_drift': 'pinned payloads/shared contract unchanged; Manager appends signed review recommendations/evidence to 5 DP rows; Owner choice/status preserved',
    'dp_registration_delta': dp_delta,
    'manifests': manifests, 'tester_review_source_hashes': len(review['sources']),
    'tester_v2_historical_files_preserved': len(tester_v2_paths),
    'developer_v2_index_prefix': 'PRESERVED', 'developer_v2_payload': 'UNCHANGED',
    'manager_and_14_dp_rows': 'UNCHANGED', 'shared_contract_code_tests': 'UNCHANGED',
    'runtime_tests': 'NOT_RUN', 'svg_spike': 'NOT_RUN', 'browser_font_measurements': 'NOT_RUN',
    'drawing_adr_and_technical_sequences': 'NOT_CREATED', 'task_start_event': 'NOT_EMITTED',
    'publication': 'NOT_PERFORMED', 'historical_evidence_replayed_as_new_run': False,
}
if '--inputs-only' not in sys.argv:
    assert '## TASK-D-003 — оценка и подготовка старта'.encode() in new_index
    assert 'STARTED не подтверждается'.encode() in new_index
    text = current(plan_path).decode()
    assert '2,5–3,5 чд' in text and all(f'T003-G0{i}' in text for i in range(1, 6))
    assert current(audit_path) == Path(__file__).read_bytes().replace(b'\r\n', b'\n')
    assert changed | {report_path} == allowed
    for path in [plan_path, R + 'developer_artifact.md']:
        content = current(path).decode()
        assert all(line == line.rstrip() for line in content.splitlines()), path
        widths = None
        for line in content.splitlines():
            if line.startswith('|'):
                n = len(re.split(r'(?<!\\)\|', line))
                assert widths is None or n == widths, (path, 'table width')
                widths = n
            else:
                widths = None
        for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)', content):
            if re.match(r'^[a-zA-Z]+:', dest):
                continue
            part = dest.split('#', 1)[0]
            destination = ((ROOT / path).parent / part).resolve()
            pending_report = '--write' in sys.argv and destination == (ROOT / report_path).resolve()
            assert destination.exists() or pending_report, (path, dest)
    report['preparation_outputs_sha256_lf'] = {p: sha256(current(p)) for p in [R + 'developer_artifact.md', plan_path, audit_path]}
    if '--write' in sys.argv:
        (ROOT / report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        assert json.loads(current(report_path)) == report
git('diff', '--check')
assert not git('diff', '--cached', '--name-only').strip()
print('TASK_D003_INPUT_OK Developer_manifest=9/9 Analyst_manifest=9/9 Tester_review_source_hashes=' + str(len(review['sources'])) + ' Owner_choices=14/14_UNCHANGED DP_registration_additions=5 shared=UNCHANGED drift=MANAGER_ONLY')
if '--inputs-only' not in sys.argv:
    print('TASK_D003_PREPARATION_OK changed_paths=4 old_index_prefix=PRESERVED old_payload=UNCHANGED STARTED=NOT_EMITTED SPIKE=NOT_RUN PUBLICATION=NOT_PERFORMED')
