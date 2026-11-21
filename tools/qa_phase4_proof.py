"""Run real P1-P4 regression, full benchmark/soak and byte determinism.

python -B tools/qa_phase4_proof.py --proof docs/proof/phase-4/d-uscalurn/<new-run>
Only a new proof directory is written. No source patch, clock or RNG override.
"""
import argparse
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))
from helpers import manifest_cmd, items


def fingerprint():
    paths = [ROOT / "game.contract.json"]
    for folder in ("chonoi", "tests", "tools"):
        paths += [p for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".html", ".mjs")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


class MethodResult(unittest.TextTestResult):
    """Count methods once, including failures within subtests."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = {}

    def startTest(self, test):
        self.methods[test.id()] = "PASS"
        super().startTest(test)

    def addFailure(self, test, err):
        self.methods[test.id()] = "FAIL"
        super().addFailure(test, err)

    def addError(self, test, err):
        self.methods[test.id()] = "ERROR"
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.methods[test.id()] = "SKIP"
        super().addSkip(test, reason)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            status = "FAIL" if issubclass(err[0], test.failureException) else "ERROR"
            if self.methods[test.id()] != "ERROR":
                self.methods[test.id()] = status
        super().addSubTest(test, subtest, err)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proof", required=True)
    args = ap.parse_args()
    os.chdir(ROOT)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    proof = Path(args.proof).resolve()
    proof.mkdir(parents=True, exist_ok=False)

    def save(name, data):
        with (proof / name).open("xb") as out:
            out.write(data if isinstance(data, bytes) else
                      (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    def capture(argv, timeout=180):
        start = time.perf_counter()
        try:
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout)
            return {"argv": argv, "exit_code": p.returncode, "wall_s": time.perf_counter() - start,
                    "stdout": p.stdout.decode("utf-8", errors="replace"), "stderr": p.stderr.decode("utf-8", errors="replace")}
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"argv": argv, "exit_code": None, "wall_s": time.perf_counter() - start, "environment_error": repr(exc)}

    revision = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    summary = {"revision": revision, "contract_version": contract["contract_version"],
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "git_status": subprocess.check_output(["git", "status", "--short"]).decode(),
        "source_sha256": fingerprint(), "commands": {key: {"configured": contract[key], "effective": manifest_cmd(key)}
            for key in ("headless_cmd", "bench_cmd", "soak_cmd")}}
    # Probe the configured Python alias separately: never mask it as application failure.
    summary["configured_python_probe"] = capture([shlex.split(contract["headless_cmd"])[0], "--version"], timeout=10)
    save("start.json", summary)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    with contextlib.redirect_stdout(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=MethodResult).run(suite)
    save("regression.txt", log.getvalue().encode("utf-8"))
    summary["regression"] = {"tests_run": result.testsRun, "methods": result.methods,
        "counts": {s: list(result.methods.values()).count(s) for s in ("PASS", "FAIL", "ERROR", "SKIP")},
        "failures": [{"test": str(t), "traceback": trace} for t, trace in result.failures],
        "errors": [{"test": str(t), "traceback": trace} for t, trace in result.errors],
        "skipped": [(str(t), reason) for t, reason in result.skipped],
        "exit_code": int(not result.wasSuccessful())}
    print("regression: " + json.dumps(summary["regression"]["counts"]), flush=True)
    save("regression.json", summary["regression"])
    with tempfile.TemporaryDirectory(prefix="t77-p4-proof-") as temp:
        work = Path(temp)
        for label, key, flags in (
            ("bench", "bench_cmd", ["--seed", "42", "--duration", "30"]),
            ("soak-1", "soak_cmd", ["--seed", "7", "--days", "10"]),
            ("soak-2", "soak_cmd", ["--seed", "7", "--days", "10"])):
            output = work / (label + ".json")
            run = capture([*manifest_cmd(key), *flags, "--out", str(output)])
            if output.exists():
                save(label + ".json", output.read_bytes())
                run["artifact_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
                run["result"] = json.loads(output.read_text(encoding="utf-8"))
            summary[label] = run
            save(label + "-execution.json", run)
            print(label + " exit=" + str(run["exit_code"]), flush=True)

        scenario = {"gather": {"hold": items("ca_loc", "bong_sung", "bong_sung"),
            "time_left_ticks": 4, "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 2, "random_customers": False}}
        summary["determinism"] = []
        for mode in ("gather", "quan", "day"):
            fixture = scenario if mode == "day" else ({"gather": scenario["gather"]} if mode == "gather" else {"quan": scenario["quan"]})
            fixture_bytes = json.dumps(fixture, sort_keys=True).encode()
            input_bytes = json.dumps({"frames": [{"tick": 0, "interact": True}]}).encode()
            outputs, processes = [], []
            for repeat in (1, 2):
                directory = work / f"{mode}-{repeat}"
                directory.mkdir()
                sc, inp, out, inv = [directory / n for n in ("scenario.json", "inputs.json", "out.jsonl", "inventory.json")]
                sc.write_bytes(fixture_bytes)
                inp.write_bytes(input_bytes)
                command = [*manifest_cmd(), "--mode", mode, "--seed", "42", "--ticks", "8",
                           "--snapshot-every", "1", "--scenario", str(sc), "--out", str(out)]
                if mode == "gather":
                    command += ["--inputs", str(inp), "--inventory-out", str(inv)]
                elif mode == "quan":
                    command += ["--inventory", str(work / "gather-1/inventory.json")]
                else:
                    command += ["--days", "1"]
                run = capture(command)
                blobs = {"jsonl": out.read_bytes()} if out.exists() else {}
                if inv.exists():
                    blobs["inventory"] = inv.read_bytes()
                for kind, data in blobs.items():
                    save(f"{mode}-{repeat}-{kind}." + ("jsonl.txt" if kind == "jsonl" else "json"), data)
                run["hashes"] = {k: hashlib.sha256(v).hexdigest() for k, v in blobs.items()}
                run["scenario_sha256"] = hashlib.sha256(sc.read_bytes()).hexdigest()
                run["inputs_sha256"] = hashlib.sha256(inp.read_bytes()).hexdigest()
                processes.append(run)
                outputs.append(blobs)
            required = {"jsonl", "inventory"} if mode == "gather" else {"jsonl"}
            valid = all(p["exit_code"] == 0 for p in processes) and all(set(o) == required for o in outputs)
            if valid:
                for output in outputs:
                    rows = [json.loads(line) for line in output["jsonl"].splitlines()]
                    valid &= rows[-1]["type"] == "end" and sum(r["type"] == "end" for r in rows) == 1
                    if mode == "gather":
                        inv = json.loads(output["inventory"])
                        valid &= rows[-1]["reason"] == "docked" and inv["items"] != []
                        valid &= next(r for r in rows if r.get("name") == "gather_end")["data"]["inventory"] == inv
                    elif mode == "quan":
                        valid &= rows[0]["stock"] == json.loads((work / "gather-1/inventory.json").read_text())["items"]
                    else:
                        valid &= {r.get("phase") for r in rows} >= {"gather", "quan", "shop"}
            summary["determinism"].append({"mode": mode, "status": "PASS" if valid and outputs[0] == outputs[1] else "FAIL",
                "valid_outputs": bool(valid), "runs": processes, "scenario": fixture,
                "inputs": json.loads(input_bytes) if mode == "gather" else None})
    b = summary.get("bench", {}).get("result", {})
    summary["benchmark_valid"] = (set(b) == {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}
        and all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in b.values())
        and b["frames"] > 0 and b["measured_s"] >= 30 and summary["bench"]["wall_s"] >= 33
        and abs(b["avg_fps"] - b["frames"] / b["measured_s"]) <= 0.05)
    summary["benchmark_thresholds_report_only"] = {"avg_ge_60": b.get("avg_fps", 0) >= 60,
        "p1_low_ge_30": b.get("p1_low_fps", 0) >= 30, "load_le_10000_ms": b.get("load_ms", math.inf) <= 10000,
        "measurement": "Software framebuffer 1280x720; no window/GPU/frontend effects"}
    soaks = [summary.get(label, {}).get("result", {}) for label in ("soak-1", "soak-2")]
    summary["soak_valid"] = all(s.get("days") == s.get("days_completed") == 10 and s.get("crashes") == 0
        and [r["day"] for r in s.get("results", [])] == list(range(1, 11)) for s in soaks)
    summary["soak_gameplay_equal"] = ({k: v for k, v in soaks[0].items() if k != "duration_s"}
                                      == {k: v for k, v in soaks[1].items() if k != "duration_s"})
    summary["source_unchanged"] = summary["source_sha256"] == fingerprint()
    summary["revision_unchanged"] = revision == subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    summary["status"] = "PASS" if (result.wasSuccessful() and summary["benchmark_valid"] and summary["soak_valid"]
        and summary["soak_gameplay_equal"] and summary["source_unchanged"] and summary["revision_unchanged"]
        and all(summary[k]["exit_code"] == 0 for k in ("bench", "soak-1", "soak-2"))
        and all(d["status"] == "PASS" for d in summary["determinism"])) else "FAIL"
    save("summary.json", summary)
    print("PROOF=" + str(proof) + " STATUS=" + summary["status"], flush=True)
    return int(summary["status"] != "PASS")


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
