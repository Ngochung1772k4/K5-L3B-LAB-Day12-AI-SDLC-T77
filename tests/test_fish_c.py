"""Test hộp đen cá bơi / sinh cá v1.1 (Ticket-02 mục 1.1) — AC-P2-02, 03."""

import unittest

from helpers import Workdir, close, events, read_jsonl, run_headless, snapshots, write_json


def run_gather(w, gather, ticks, every=1):
    sc = write_json(w.path("sc.json"), {"gather": gather})
    code, err = run_headless("--mode", "gather", "--seed", "4", "--ticks", str(ticks), "--snapshot-every", str(every),
                             "--scenario", sc, "--out", w.path("o.jsonl"))
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path("o.jsonl"))


def fish_at(rows, tick, fid):
    s = [x for x in snapshots(rows) if x["tick"] == tick][-1]
    return next(f for f in s["fish"] if f["id"] == fid)


class FishSwim(unittest.TestCase):
    def test_p2_02_swim_speed_and_age(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 5], "heading_deg": 0}]}, 60)
            f = fish_at(rows, 60, "F1")
            self.assertTrue(close(f["pos"][0], 51.5, 0.01), f)
            self.assertEqual(f["age_ticks"], 60)

    def test_p2_02_reflect_at_edge(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 5], "heading_deg": 0}]}, 1)
            f = fish_at(rows, 1, "F1")
            self.assertTrue(close(f["pos"][0], 95.985, 0.001), f)
            self.assertEqual(f["heading_deg"], 180)

    def test_p2_02_turn_at_swim_step_120(self):
        with Workdir() as w:
            rows = run_gather(w, {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 5], "heading_deg": 0}]}, 120)
            self.assertEqual(fish_at(rows, 119, "F1")["heading_deg"], 0)
            self.assertNotEqual(fish_at(rows, 120, "F1")["heading_deg"], 0)

    def test_random_fish_false_keeps_fixture_still(self):
        with Workdir() as w:
            rows = run_gather(w, {"random_fish": False, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 10]}]}, 400)
            self.assertEqual(fish_at(rows, 400, "F1")["pos"], [30, 10])
            self.assertEqual(events(rows, "fish_spawned"), [])


class FishSpawn(unittest.TestCase):
    def test_p2_03_spawn_every_360_up_to_cap(self):
        with Workdir() as w:
            rows = run_gather(w, {}, 2200, every=100)
            sp = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in sp], [360, 720, 1080, 1440])  # 8 -> trần 12
            self.assertEqual(set(sp[0]["data"]), {"id", "kind", "pos"})
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 12)


if __name__ == "__main__":
    unittest.main()
