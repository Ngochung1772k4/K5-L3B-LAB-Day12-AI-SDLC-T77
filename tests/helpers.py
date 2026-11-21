"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


def manifest_cmd(key="headless_cmd"):
    """Read the real command; use this interpreter for Python entry points.

    This avoids unusable WindowsApps python3 aliases without editing the
    contract, PATH, simulation, arguments or subprocess results. Other
    languages/executables retain their manifest command unchanged.
    """
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        command = shlex.split(json.load(f)[key])
    executable = os.path.basename(command[0])
    if re.fullmatch(r"python(?:\d+(?:\.\d+)*)?(?:\.exe)?", executable, flags=re.IGNORECASE):
        return [sys.executable, "-B", *command[1:]]
    return command


def headless_cmd():
    """Manifest headless entry point, with portable Python interpreter selection."""
    return manifest_cmd()


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def snapshots(rows):
    return [r for r in rows if r["type"] == "snapshot"]


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def close(a, b, tol=0.1):
    return abs(a - b) <= tol


def dist(p, q):
    return math.dist(p, q)


class Workdir:
    """Thư mục tạm tự dọn: with Workdir() as w: w.path('x.json')."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *a):
        self._d.cleanup()

    def path(self, name):
        return os.path.join(self._d.name, name)


# --- v1.2: kho cá thể (Ticket-03) -------------------------------------------------
def items(*kinds, fresh=100, start=1):
    """Mảng cá thể {id, kind, fresh} với id I<start>, I<start+1>, ... theo thứ tự."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def stock_of(counts, fresh=100):
    """{kind: n} -> mảng cá thể (kind sắp theo tên)."""
    return items(*[k for k in sorted(counts) for _ in range(counts[k])], fresh=fresh)


def counts(item_list):
    """Mảng cá thể -> {kind: n}."""
    out = {}
    for it in item_list:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return out
