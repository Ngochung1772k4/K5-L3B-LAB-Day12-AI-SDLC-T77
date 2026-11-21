"""Test hộp đen Cá Sấu (Ticket-02 mục 1.2) — AC-P2-04..06."""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json

CROC = {"id": "M1", "kind": "ca_sau", "pos": [61, 20], "waypoints": [[60, 20], [64, 20]]}


def run_gather(w, scenario, ticks):
    sc = write_json(w.path("sc.json"), {"gather": dict({"random_fish": False}, **scenario)})
    code, err = run_headless("--mode", "gather", "--seed", "2", "--ticks", str(ticks), "--snapshot-every", "1",
                             "--scenario", sc, "--out", w.path("o.jsonl"))
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path("o.jsonl"))


class Crocodile(unittest.TestCase):
    def test_p2_04_default_layout_day1_only_m1(self):
        with Workdir() as w:
            rows = run_gather(w, {}, 0)
            self.assertEqual([m["id"] for m in snapshots(rows)[0]["monsters"]], ["M1"])  # M2 từ Ngày 3

    def test_p2_04_chase_when_player_deep_and_close(self):
        sc = {"player": {"pos": [55, 24]}, "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24],
                                                          "waypoints": [[60, 24], [64, 24]]}]}
        with Workdir() as w:
            rows = run_gather(w, sc, 3)
            self.assertEqual(snapshots(rows)[-1]["monsters"][0]["state"], "chase")

    def test_p2_04_no_chase_when_player_shallow(self):
        sc = {"player": {"pos": [58, 5]}, "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 12],
                                                         "waypoints": [[60, 12], [64, 12]]}]}
        with Workdir() as w:
            rows = run_gather(w, sc, 3)
            self.assertEqual(snapshots(rows)[-1]["monsters"][0]["state"], "patrol")

    def test_p2_05_hit_loses_half_lifo_invuln_recoil(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "ca_linh", "keo_neo"]
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [60, 20]}, "hold": hold, "monsters": [CROC]}, 5)
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1)  # bất tử 90 tick -> không hit tiếp
            d = hits[0]["data"]
            self.assertEqual((hits[0]["tick"], d["monster_id"], d["hp"], d["lost"]), (1, "M1", 2, ["keo_neo", "ca_linh"]))
            s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual((s1["player"]["invuln_ticks"], s1["hold"]), (90, hold[:3]))
            self.assertEqual((s1["monsters"][0]["state"], s1["monsters"][0]["state_ticks_left"]), ("recoil", 60))

    def test_p2_06_faint_by_monster(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [60, 20], "hp": 1}, "hold": ["ca_loc", "bong_sung"],
                                  "monsters": [CROC]}, 3)
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names[-3:], ["monster_hit", "faint", "gather_end"])
            self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], ["bong_sung"])  # floor(2/2) LIFO
            self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": ["ca_loc"], "hp": 0})
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})


if __name__ == "__main__":
    unittest.main()
