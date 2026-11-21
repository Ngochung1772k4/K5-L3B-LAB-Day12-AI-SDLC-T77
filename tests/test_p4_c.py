"""Test v1.3 (Ticket-04): contract khai bench_cmd/soak_cmd; soak tất định; bench xuất đúng 5 trường. AC-P4-01..03."""

import json
import os
import math
import subprocess
import unittest

from helpers import ROOT, Workdir, manifest_cmd


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def run_cmd(key, *args):
    p = subprocess.run([*manifest_cmd(key), *args], cwd=ROOT, capture_output=True, text=True, timeout=180)
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
                code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "10", "--out", w.path(f"s{i}.json"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"s{i}.json"), encoding="utf-8") as f:
                    outs.append(json.load(f))
            s = outs[0]
            self.assertEqual(set(s), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((s["days"], s["days_completed"], s["crashes"]), (10, 10, 0))
            for report in outs:
                self.assertEqual([r["day"] for r in report["results"]], list(range(1, 11)))
                self.assertTrue(math.isfinite(report["duration_s"]) and report["duration_s"] > 0)
                previous = 0
                q = contract()["tuning"]["quan"]
                for row in report["results"]:
                    self.assertEqual(set(row), {"day", "earned", "reputation", "score"})
                    self.assertIs(type(row["earned"]), int)
                    self.assertGreaterEqual(row["earned"], previous)
                    previous = row["earned"]
                    self.assertTrue(q["reputation_min"] <= row["reputation"] <= q["reputation_max"])
                    self.assertEqual(row["score"], row["earned"] + contract()["tuning"]["score"]["reputation_multiplier"] * math.floor(row["reputation"]))
            self.assertEqual({k: v for k, v in outs[0].items() if k != "duration_s"},
                             {k: v for k, v in outs[1].items() if k != "duration_s"})

    def test_p4_03_bench_writes_five_fields(self):
        with Workdir() as w:
            code, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "0.3", "--out", w.path("b.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("b.json"), encoding="utf-8") as f:
                b = json.load(f)
            self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(b["frames"], 0)
            self.assertIs(type(b["frames"]), int)
            self.assertIs(type(b["load_ms"]), int)
            for key in b:
                self.assertIsNot(type(b[key]), bool)
                self.assertTrue(math.isfinite(b[key]), key)
                self.assertGreaterEqual(b[key], 0)
            self.assertGreaterEqual(b["measured_s"], 0.3)
            self.assertGreater(b["p1_low_fps"], 0)
            self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] * 1.05)
            # measured_s is rounded to milliseconds by this implementation.
            self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"],
                                   delta=0.01 + b["frames"] * 0.0005 / (b["measured_s"] * (b["measured_s"] - 0.0005)))

    def test_nonpositive_duration_and_days_rejected_without_artifact(self):
        with Workdir() as w:
            for key, flag in (("bench_cmd", "--duration"), ("soak_cmd", "--days")):
                for value in ("0", "-1"):
                    with self.subTest(key=key, value=value):
                        output = w.path("invalid.json")
                        code, err = run_cmd(key, "--seed", "7", flag, value, "--out", output)
                        self.assertEqual(code, 2, err)
                        self.assertTrue(err.strip())
                        self.assertFalse(os.path.exists(output))


if __name__ == "__main__":
    unittest.main()
