---
name: run-tests-proof
description: Chạy unittest và smoke tích hợp Phase 1 của T77, lưu proof thật cùng revision, exit code và kết quả theo test method.
---

# run-tests-proof — Phase 1

Dùng sau thay đổi gameplay hoặc khi cần bằng chứng QA cho PRD-0 / Test Contract v1.0. Đọc `game.contract.json`, `tests/helpers.py`, các test liên quan và runner trước khi chạy. Nếu manifest khác `1.0`, báo khác biệt; không tự đổi contract, luật hay test.

Chỉ ghi proof khi phạm vi hiện tại cho phép. Tạo thư mục mới, không ghi đè log cũ. Fixture và đầu ra runtime nằm trong thư mục tạm; chỉ sao chép bằng chứng cần giữ vào `docs/proof/phase-1/`. Tắt bytecode. Không sửa implementation hoặc assertion để làm xanh test.

## Lệnh kiểm thử riêng

Từ gốc repo, PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m unittest discover -s tests -p 'test_gather_rules.py' -v
$LASTEXITCODE
python -B -m unittest discover -s tests -p 'test_quan_rules.py' -v
$LASTEXITCODE
python -B -m unittest discover -s tests -v
$LASTEXITCODE
```

Linux/macOS dùng `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest ...` và đọc `$?` ngay sau từng lệnh. `unittest -v` thường ghi kết quả vào **stderr**; stderr không rỗng tự nó không phải lỗi.

Trên Windows, hai test của D có fallback cho alias `python3` bị hỏng. Starter tests vẫn đọc `headless_cmd` nguyên bản. Khối thu proof dưới đây chỉ thay executable Python trong bộ nhớ khi alias không khởi chạy được; không sửa manifest, PATH hay `helpers.py`. Mọi CLI exit khác 0 vẫn được ghi nhận.

## Thu log và smoke hai tiến trình

Khối sau chạy lại cả ba suite, lưu stdout/stderr/exit code và thống kê **method** (một method có nhiều subtest lỗi vẫn chỉ tính một FAIL). Chạy từ gốc repo. Nó thoát 1 nếu có suite FAIL/ERROR hoặc smoke không PASS; proof vẫn được lưu.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
@'
import hashlib, json, os, platform, shlex, subprocess, sys, tempfile, uuid
from pathlib import Path

root = Path.cwd()
contract = json.loads((root / 'game.contract.json').read_text(encoding='utf-8'))
assert contract['contract_version'] == '1.0', 'Only Phase 1 contract 1.0 is supported'
proof = root / 'docs/proof/phase-1' / ('d-uscalurn-run-' + uuid.uuid4().hex[:8])
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

def capture(argv):
    return subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=120)

def fingerprint():
    paths = [root / 'game.contract.json', *sorted((root / 'chonoi').rglob('*.py')),
             *sorted((root / 'tests').glob('*.py'))]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

revision = capture(['git', 'rev-parse', 'HEAD']).stdout.decode().strip()
source_hashes = fingerprint()
metadata = {'revision': revision, 'contract_version': contract['contract_version'],
            'python': sys.version, 'platform': platform.platform(),
            'execution_start_git_status': capture(['git', 'status', '--short']).stdout.decode('utf-8'),
            'headless_configured': configured, 'headless_effective': effective,
            'windows_alias_error': adapter, 'source_sha256': source_hashes}

runner = r'''
import contextlib, json, sys, unittest
from unittest.mock import patch
sys.path.insert(0, 'tests')
import helpers
pattern, command = sys.argv[1], json.loads(sys.argv[2])
suite = unittest.defaultTestLoader.discover('tests', pattern=pattern)
def ids(node):
    return [i for child in node for i in ids(child)] if isinstance(node, unittest.TestSuite) else [node.id()]
all_ids = set(ids(suite))
context = patch.object(helpers, 'headless_cmd', return_value=command) if command != helpers.headless_cmd() else contextlib.nullcontext()
with context:
    result = unittest.TextTestRunner(verbosity=2).run(suite)
def parent(test):
    return getattr(test, 'test_case', test).id()
failed = {parent(test) for test, _ in result.failures}
errored = {parent(test) for test, _ in result.errors}
skipped = {parent(test) for test, _ in result.skipped}
methods = {i: 'ERROR' if i in errored else 'FAIL' if i in failed else 'SKIP' if i in skipped else 'PASS' for i in sorted(all_ids)}
counts = {status: list(methods.values()).count(status) for status in ('PASS', 'FAIL', 'ERROR', 'SKIP')}
print(json.dumps({'tests_run': result.testsRun, 'counts': counts, 'methods': methods,
                  'failure_entries_including_subtests': len(result.failures), 'error_entries': len(result.errors)}))
sys.exit(0 if result.wasSuccessful() else 1)
'''

summaries = {}
for label, pattern in [('gather-tests', 'test_gather_rules.py'), ('quan-tests', 'test_quan_rules.py'), ('full-suite', 'test*.py')]:
    argv = [sys.executable, '-B', '-c', runner, pattern, json.dumps(effective)]
    process = capture(argv)
    summary = json.loads(process.stdout.decode('utf-8'))
    summary['exit_code'] = process.returncode
    summaries[label] = summary
    header = json.dumps({'revision': revision, 'argv': argv, 'exit_code': process.returncode,
                         'headless_effective': effective}, ensure_ascii=False, indent=2)
    save(label + '.txt', header + '\n\n--- STDOUT (raw) ---\n' + process.stdout.decode('utf-8', errors='replace')
         + '\n--- STDERR (raw) ---\n' + process.stderr.decode('utf-8', errors='replace'))
    print(label + ': ' + json.dumps(summary['counts']), flush=True)

with tempfile.TemporaryDirectory(prefix='t77-smoke-') as temporary:
    work = Path(temporary)
    scenario, inputs = work / 'dock.json', work / 'inputs.json'
    scenario.write_text(json.dumps({'gather': {'hold': ['ca_loc', 'bong_sung', 'bong_sung']}}), encoding='utf-8')
    inputs.write_text(json.dumps({'frames': [{'tick': 0, 'interact': True}]}), encoding='utf-8')
    gather, inventory, quan = work / 'gather.jsonl', work / 'inventory.json', work / 'quan.jsonl'
    commands = [effective + ['--mode', 'gather', '--seed', '42', '--scenario', str(scenario), '--inputs', str(inputs),
                            '--ticks', '1', '--out', str(gather), '--inventory-out', str(inventory)],
                effective + ['--mode', 'quan', '--seed', '42', '--inventory', str(inventory), '--ticks', '0', '--out', str(quan)]]
    processes = [capture(command) for command in commands]
    expected = {'items': {'bong_sung': 2, 'ca_loc': 1}}
    actual, errors = {}, []
    for name, path in [('gather', gather), ('inventory', inventory), ('quan', quan)]:
        if path.exists():
            save('integration-' + path.name + ('.txt' if path.suffix == '.jsonl' else ''), path.read_bytes())
        else:
            errors.append('missing ' + name)
    if not errors and all(p.returncode == 0 for p in processes):
        grows = [json.loads(line) for line in gather.read_text(encoding='utf-8').splitlines()]
        qrows = [json.loads(line) for line in quan.read_text(encoding='utf-8').splitlines()]
        ends = [r for r in grows if r.get('name') == 'gather_end']
        snapshots = [r for r in qrows if r['type'] == 'snapshot' and r['tick'] == 0]
        actual = {'inventory': json.loads(inventory.read_text(encoding='utf-8')),
                  'gather_end': [r['data'] for r in ends], 'quan_tick_zero_stock': [r['stock'] for r in snapshots]}
        ok = actual['inventory'] == expected and actual['gather_end'] == [{'reason': 'docked', 'inventory': expected}] and actual['quan_tick_zero_stock'] == [expected['items']]
    else:
        ok = False
    smoke = {'status': 'PASS' if ok else 'ERROR' if errors or any(p.returncode != 0 for p in processes) else 'FAIL',
             'expected': expected, 'actual': actual, 'errors': errors,
             'scenario': json.loads(scenario.read_text(encoding='utf-8')), 'inputs': json.loads(inputs.read_text(encoding='utf-8')),
             'processes': [{'argv': command, 'exit_code': p.returncode,
                            'stdout': p.stdout.decode('utf-8', errors='replace'), 'stderr': p.stderr.decode('utf-8', errors='replace')}
                           for command, p in zip(commands, processes)]}

assert fingerprint() == source_hashes, 'Source/test content changed during execution'
assert capture(['git', 'rev-parse', 'HEAD']).stdout.decode().strip() == revision
metadata['suites'], metadata['integration'] = summaries, smoke
save('summary.json', json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
save('integration.md', '# Smoke integration Phase 1\n\nRevision: `' + revision + '` (working tree; see source hashes in summary.json).\n\n'
     + 'Result: **' + smoke['status'] + '**. Two separate headless processes; temporary runtime paths are cleaned.\n\n'
     + '```json\n' + json.dumps(smoke, ensure_ascii=False, indent=2) + '\n```\n')
print('INTEGRATION=' + smoke['status'], flush=True)
sys.exit(1 if any(s['exit_code'] for s in summaries.values()) or smoke['status'] != 'PASS' else 0)
'@ | python -B -
$LASTEXITCODE
```

Để chạy khối Python này trên Linux/macOS, giữ nguyên phần từ `import` đến `sys.exit`, đặt giữa `PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'` và dòng `PY`; không cần tạo script trong repo.

## Đọc và bàn giao kết quả

- PASS: assertion đáp ứng; FAIL: assertion không khớp; ERROR: lỗi thực thi/import/fixture/môi trường; SKIP: chưa kiểm, kèm lý do. Không dùng tổng số failure entries thay cho số method vì subtest có thể làm số này lớn hơn.
- CLI headless: 0 là chạy hợp lệ, 2 là sai cờ/dữ liệu/fixture, 1 là lỗi chạy/ghi. Exit 0 không chứng minh luật gameplay đúng. Tách lỗi fixture khỏi FAIL sau một lượt chạy hợp lệ.
- Log chứa raw stdout/stderr, argv, exit code; `summary.json` chứa HEAD, hash source/test, adapter Windows và kết quả từng method. Test chưa commit phải được ghi rõ, không gọi đây là proof chỉ của HEAD hoặc tag.
- JSONL lưu proof có đuôi `.jsonl.txt` vì repo ignore `*.jsonl`; nội dung vẫn nguyên byte, không chuyển định dạng. Không sửa `.gitignore` hoặc tự stage file để vượt quy tắc này.
- Cập nhật `docs/verification/phase-1.md` nếu được phép: mỗi dòng `AC → test hoặc smoke → PASS/FAIL/PARTIAL → proof`. Mã AC-P1-01–20 trong `docs/plan/phase-1-chia-viec.md` là mã nội bộ nhóm; PRD-0 là nguồn luật.
- Khi FAIL, bàn giao owner A/B/C cùng fixture/input, seed, tick, expected/actual và đường dẫn traceback. Không sửa contract/test hoặc file ngoài phạm vi. Gameplay chưa đạt thì nghiệm thu FAIL/BLOCKED dù không có ERROR.
