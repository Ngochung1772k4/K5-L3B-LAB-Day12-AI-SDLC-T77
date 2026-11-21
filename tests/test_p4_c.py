"""Test v1.3 (Ticket-04): contract khai bench_cmd/soak_cmd; soak tất định; bench xuất đúng 5 trường. AC-P4-01..03."""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def run_cmd(key, *args):
    p = subprocess.run([*shlex.split(contract()[key]), *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr


class P4(unittest.TestCase):
    def test_p4_01_contract_v13_declares_commands(self):
        c = contract()
        self.assertEqual(c["contract_version"], "1.3")
        self.assertTrue(c["bench_cmd"] and c["soak_cmd"])
        self.assertIn("freshness", c["tuning"])  # gameplay v1.2 giữ nguyên

    def test_p4_02_soak_days_complete_no_crash_deterministic(self):
        with Workdir() as w:
            outs = []
            for i in (1, 2):
                code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "6", "--out", w.path(f"s{i}.json"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"s{i}.json"), encoding="utf-8") as f:
                    outs.append(json.load(f))
            s = outs[0]
            self.assertEqual(set(s), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((s["days"], s["days_completed"], s["crashes"]), (6, 6, 0))
            self.assertEqual([r["day"] for r in s["results"]], [1, 2, 3, 4, 5, 6])
            self.assertEqual(set(s["results"][0]), {"day", "earned", "reputation", "score"})
            self.assertEqual(outs[0]["results"], outs[1]["results"])  # bỏ duration_s khi so

    def test_p4_03_bench_writes_five_fields(self):
        with Workdir() as w:
            code, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "0.3", "--out", w.path("b.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("b.json"), encoding="utf-8") as f:
                b = json.load(f)
            self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(b["frames"], 0)
            self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], delta=1)


if __name__ == "__main__":
    unittest.main()
