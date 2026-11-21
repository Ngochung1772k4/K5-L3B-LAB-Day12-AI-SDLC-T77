---
name: check-determinism
description: So sánh từng byte JSONL và inventory qua hai lần chạy Phase 1 cùng revision, seed, fixture và inputs; lưu hash và chẩn đoán mismatch.
---

# check-determinism — Phase 1

Dùng sau thay đổi RNG/seed, timer, thứ tự xử lý/event hoặc khi cần xác minh tái lập. Nguồn: PRD-0 / Test Contract v1.0 E–G. Chỉ thực hiện trong phạm vi được giao; không sửa mô phỏng, contract hay test. Nếu manifest khác `1.0`, báo khác biệt trước khi dùng các fixture này.

Hai lượt phải cùng working tree/code revision, interpreter, môi trường, mode, seed, số tick và snapshot interval. Nội dung scenario/inputs phải giống từng byte; chỉ đường dẫn tạm và đường dẫn output khác nhau. Kiểm HEAD và hash source trước/sau, vì HEAD không phản ánh test hoặc code chưa commit.

Ví dụ thực thi từ gốc repo, PowerShell; mọi file runtime nằm trong hai thư mục tạm tách biệt. Proof có thư mục mới và được mở exclusive để không ghi đè dữ liệu khác.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
@'
import hashlib, json, os, platform, shlex, subprocess, sys, tempfile, uuid
from pathlib import Path

root = Path.cwd()
contract = json.loads((root / 'game.contract.json').read_text(encoding='utf-8'))
assert contract['contract_version'] == '1.0', 'Only Phase 1 contract 1.0 is supported'
proof = root / 'docs/proof/phase-1' / ('d-uscalurn-determinism-' + uuid.uuid4().hex[:8])
proof.mkdir(parents=True, exist_ok=False)
print('PROOF_DIR=' + proof.relative_to(root).as_posix(), flush=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
configured = shlex.split(contract['headless_cmd'])
effective, adapter = configured[:], None
if os.name == 'nt' and configured[0] in ('python3', 'python3.exe'):
    try:
        subprocess.run([configured[0], '-B', '--version'], capture_output=True, check=True, env=env)
    except OSError as exc:
        if exc.errno not in (2, 13) and getattr(exc, 'winerror', None) not in (2, 5, 1920):
            raise
        effective = [sys.executable, '-B', *configured[1:]]
        adapter = repr(exc)

def save(name, data):
    with (proof / name).open('xb') as stream:
        stream.write(data if isinstance(data, bytes) else data.encode('utf-8'))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fingerprint():
    paths = [root / 'game.contract.json', *sorted((root / 'chonoi').rglob('*.py')),
             *sorted((root / 'tests').glob('*.py'))]
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in paths}

revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
source_hashes = fingerprint()
first = contract['tuning']['quan']['first_customer_tick']
stock = {}
for dish in contract['tuning']['menu'].values():
    for kind, amount in dish['recipe'].items():
        stock[kind] = stock.get(kind, 0) + amount
cases = [
    ('gather-docked', 'gather', {'gather': {'hold': ['ca_loc', 'bong_sung', 'bong_sung']}},
     {'frames': [{'tick': 0, 'interact': True}]}, 1, 'docked'),
    ('gather-time', 'gather', {'gather': {'player': {'pos': [20, 0]}, 'hold': ['ca_loc', 'bong_sung'],
      'nodes': [{'id': 'N1', 'kind': 'bong_dien_dien', 'pos': [20, 0], 'regrow_ticks': 2}],
      'fish': [], 'random_fish': False, 'time_left_ticks': 8}},
     {'frames': [{'tick': 0, 'move': [1, 0], 'interact': True}, {'tick': 1, 'interact': False},
                 {'tick': 2, 'interact': True}, {'tick': 3, 'move': [0, 0]}]}, 8, 'time'),
    ('quan', 'quan', {'quan': {'stock': stock, 'random_customers': True, 'time_left_ticks': first + 3,
      'player': {'pos': contract['tuning']['quan']['stoves'][0]['pos']}}},
     {'frames': [{'tick': first, 'interact': True}]}, first + 3, 'time'),
]
results = []
for label, mode, scenario, inputs, ticks, reason in cases:
    scenario_bytes = json.dumps(scenario, sort_keys=True).encode('utf-8')
    input_bytes = json.dumps(inputs, sort_keys=True).encode('utf-8')
    runs, blobs = [], []
    with tempfile.TemporaryDirectory(prefix='t77-det-a-') as a, tempfile.TemporaryDirectory(prefix='t77-det-b-') as b:
        for number, directory in enumerate((a, b), 1):
            work = Path(directory)
            sc, inp, out, inv = [work / name for name in ('scenario.json', 'inputs.json', 'out.jsonl', 'inventory.json')]
            sc.write_bytes(scenario_bytes)
            inp.write_bytes(input_bytes)
            argv = effective + ['--mode', mode, '--seed', '42', '--scenario', str(sc), '--inputs', str(inp),
                                '--ticks', str(ticks), '--snapshot-every', '1', '--out', str(out)]
            if mode == 'gather':
                argv += ['--inventory-out', str(inv)]
            process = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=120)
            run = {'argv': argv, 'exit_code': process.returncode, 'scenario_sha256': sha(sc.read_bytes()),
                   'inputs_sha256': sha(inp.read_bytes()), 'stdout': process.stdout.decode('utf-8', errors='replace'),
                   'stderr': process.stderr.decode('utf-8', errors='replace')}
            output = {}
            for kind, path in [('jsonl', out)] + ([('inventory', inv)] if mode == 'gather' else []):
                if path.exists():
                    data = path.read_bytes()
                    artifact = f'{label}-{number}-{kind}.' + ('jsonl.txt' if kind == 'jsonl' else 'json')
                    save(artifact, data)
                    output[kind] = data
                    run[kind] = {'source_path': str(path), 'artifact': artifact, 'bytes': len(data), 'sha256': sha(data)}
            runs.append(run)
            blobs.append(output)
    valid = all(run['exit_code'] == 0 for run in runs)
    valid = valid and all('jsonl' in output and (mode != 'gather' or 'inventory' in output) for output in blobs)
    if valid:
        for output in blobs:
            rows = [json.loads(line) for line in output['jsonl'].splitlines()]
            valid = valid and rows[0]['type'] == 'snapshot' and rows[0]['tick'] == 0
            valid = valid and rows[-1]['type'] == 'end' and rows[-1]['reason'] == reason
            if mode == 'gather':
                ends = [r for r in rows if r.get('name') == 'gather_end']
                valid = valid and len(ends) == 1 and ends[0]['data']['inventory'] == json.loads(output['inventory'])
    same_inputs = all(run['scenario_sha256'] == sha(scenario_bytes) and run['inputs_sha256'] == sha(input_bytes) for run in runs)
    comparisons = {kind: blobs[0].get(kind) == blobs[1].get(kind) for kind in ('jsonl', 'inventory') if kind == 'jsonl' or mode == 'gather'}
    status = 'ERROR' if not valid or not same_inputs else 'PASS' if all(comparisons.values()) else 'FAIL'
    result = {'case': label, 'mode': mode, 'seed': 42, 'ticks': ticks, 'snapshot_every': 1,
              'scenario': scenario, 'inputs': inputs, 'runs': runs, 'same_input_bytes': same_inputs,
              'valid_complete_outputs': valid, 'byte_equal': comparisons, 'status': status}
    results.append(result)
    print(label + ': ' + status + ' ' + json.dumps(comparisons), flush=True)

unchanged = fingerprint() == source_hashes and subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip() == revision
status = 'ERROR' if not unchanged or any(r['status'] == 'ERROR' for r in results) else 'PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL'
report = {'revision': revision, 'contract_version': contract['contract_version'], 'python': sys.version,
          'platform': platform.platform(), 'headless_configured': configured, 'headless_effective': effective,
          'windows_alias_error': adapter, 'source_sha256': source_hashes, 'source_unchanged': unchanged,
          'status': status, 'cases': results}
save('summary.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
lines = ['# Determinism Phase 1', '', 'Revision: `' + revision + '` plus working-tree source hashes in summary.json.',
         '', '**' + status + '** for the three fixtures below. Runtime directories were separate and are cleaned.', '',
         '| Case | JSONL byte equal | Inventory byte equal | Result |', '|---|---|---|---|']
for result in results:
    lines.append('| ' + result['case'] + ' | ' + str(result['byte_equal']['jsonl']) + ' | '
                 + str(result['byte_equal'].get('inventory', 'n/a')) + ' | ' + result['status'] + ' |')
lines += ['', 'Exact commands, fixture/input contents, stderr, exit codes, original temporary paths, retained artifact paths and SHA-256 values are in [summary.json](summary.json).',
          '', 'Repeatability is not gameplay correctness. These fixtures do not certify unimplemented harvesting, fishing, customer selection or payment branches.', '']
save('determinism.md', '\n'.join(lines))
print('DETERMINISM=' + status, flush=True)
sys.exit(0 if status == 'PASS' else 1)
'@ | python -B -
$LASTEXITCODE
```

Linux/macOS: chạy cùng phần Python bằng `PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'` … `PY`. Không cần cài dependency hoặc tạo script trong repo.

## Chẩn đoán mismatch

Kiểm exit code/stderr và tính hợp lệ của output trước; hai file rỗng hoặc hai lượt cùng bị từ chối không phải PASS. So byte trực tiếp; SHA-256 phục vụ truy vết. Không làm tròn, sắp lại JSON hay bỏ event trước khi so.

Proof JSONL dùng đuôi `.jsonl.txt` để không bị quy tắc ignore `*.jsonl` của repo bỏ qua; byte và hash giữ nguyên. Không sửa `.gitignore` hoặc stage file ngoài nhiệm vụ.

Nếu source hash, interpreter, môi trường, tham số hoặc hash input khác, đánh dấu ERROR của phép kiểm và chạy lại đúng điều kiện; chưa kết luận lỗi RNG. Nếu các điều kiện giống nhau mà JSONL/inventory khác, đánh dấu FAIL, xác định byte/dòng/tick đầu tiên khác và chuyển owner kèm hai artifact. Không tự chỉnh mô phỏng để làm mất mismatch.

Khi bàn giao, dẫn `determinism.md` và `summary.json`; ghi revision nền, tình trạng working tree, từng cặp hash/path và phạm vi fixture. PASS chỉ xác nhận tính lặp lại đã quan sát, không thay thế kiểm thử luật hoặc nghiệm thu toàn Phase 1.
