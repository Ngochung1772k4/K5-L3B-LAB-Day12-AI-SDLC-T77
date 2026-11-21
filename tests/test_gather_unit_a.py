"""Unit & black-box headless tests cho Phase 1 Người A (sim/gather)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherRulesA(unittest.TestCase):
    def test_dive_and_surface_events(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0.4]}, "random_fish": False}})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 20, "move": [0, -1]},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dive_ev = events(rows, "dive")
            surf_ev = events(rows, "surface")
            self.assertEqual(len(dive_ev), 1)
            self.assertEqual(len(surf_ev), 1)
            self.assertIn("pos", dive_ev[0]["data"])
            self.assertGreater(dive_ev[0]["data"]["pos"][1], 0.5)
            self.assertIn("pos", surf_ev[0]["data"])
            self.assertLessEqual(surf_ev[0]["data"]["pos"][1], 0.5)
            self.assertLess(dive_ev[0]["tick"], surf_ev[0]["tick"])

    def test_oxygen_drain_and_refill(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 5]}, "random_fish": False}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--out", w.path("o1.jsonl"))
            self.assertEqual(code, 0, err)
            s_under = snapshots(read_jsonl(w.path("o1.jsonl")))
            self.assertEqual(s_under[0]["player"]["oxygen_ticks"], 1800)
            self.assertEqual(s_under[-1]["player"]["oxygen_ticks"], 1740)

            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [20, 0], "oxygen_ticks": 1790},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--scenario", sc2, "--snapshot-every", "1", "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            s_surf = {r["tick"]: r["player"]["oxygen_ticks"] for r in snapshots(read_jsonl(w.path("o2.jsonl")))}
            self.assertEqual(s_surf[1], 1796)
            self.assertEqual(s_surf[2], 1800)
            self.assertEqual(s_surf[3], 1800)

    def test_oxygen_empty_and_first_choke_at_t_plus_59(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 1, "zero_oxy_ticks": 0},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "65",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty_ev = events(rows, "oxygen_empty")
            choke_ev = events(rows, "choke")
            self.assertEqual(len(empty_ev), 1)
            self.assertEqual(empty_ev[0]["tick"], 1)
            self.assertEqual(empty_ev[0]["data"], {"oxygen_ticks": 0})
            self.assertEqual(len(choke_ev), 1)
            self.assertEqual(choke_ev[0]["tick"], 60)
            self.assertEqual(choke_ev[0]["data"], {"hp": 2})

    def test_choke_from_zero_oxy_59_and_surface_cancels_choke(self):
        with Workdir() as w:
            sc1 = write_json(w.path("sc1.json"), {"gather": {
                "player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "random_fish": False,
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc1, "--snapshot-every", "1", "--out", w.path("o1.jsonl"))
            self.assertEqual(code, 0, err)
            rows1 = read_jsonl(w.path("o1.jsonl"))
            chokes = events(rows1, "choke")
            self.assertEqual(len(chokes), 1)
            self.assertEqual(chokes[0]["data"], {"hp": 2})
            last_p1 = snapshots(rows1)[-1]["player"]
            self.assertEqual(last_p1["hp"], 2)
            self.assertEqual(last_p1["zero_oxy_ticks"], 0)

            sc2 = write_json(w.path("sc2.json"), {"gather": {
                "player": {"pos": [20, 0.51], "vel": [0, -4.0], "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "random_fish": False,
            }})
            inp2 = write_json(w.path("in2.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc2, "--inputs", inp2, "--snapshot-every", "1",
                                     "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(len(events(rows2, "choke")), 0)
            self.assertEqual(len(events(rows2, "surface")), 1)
            last_p2 = snapshots(rows2)[-1]["player"]
            self.assertEqual(last_p2["hp"], 3)
            self.assertEqual(last_p2["oxygen_ticks"], 6)
            self.assertEqual(last_p2["zero_oxy_ticks"], 0)

    def test_faint_drops_hold_lifo_and_writes_empty_inventory(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "hold": ["ca_loc", "bong_sung", "bong_dien_dien"],
                "random_fish": False,
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([r["name"] for r in events(rows)], ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows, "choke")[0]["data"], {"hp": 0})
            self.assertEqual(events(rows, "faint")[0]["data"], {
                "cause": "choke",
                "lost": ["bong_dien_dien", "bong_sung", "ca_loc"],
                "hp": 0,
            })
            self.assertEqual(events(rows, "gather_end")[0]["data"], {
                "reason": "fainted",
                "inventory": {"items": {}},
            })
            self.assertEqual(rows[-1]["ticks"], 1)
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_harvest_regrow_and_tiebreak(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [22, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [18, 0]},
                ],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 2, "interact": True},
                {"tick": 3, "interact": False},
                {"tick": 1200, "interact": True},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1201",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g_evs = events(rows, "gather")
            r_evs = events(rows, "node_regrown")
            self.assertEqual(len(g_evs), 3)
            self.assertEqual(g_evs[0]["tick"], 1)
            self.assertEqual(g_evs[0]["data"], {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1})
            self.assertEqual(g_evs[1]["tick"], 3)
            self.assertEqual(g_evs[1]["data"], {"node_id": "N10", "kind": "bong_sung", "amount": 1})
            self.assertEqual(len(r_evs), 1)
            self.assertEqual(r_evs[0]["tick"], 1201)
            self.assertEqual(r_evs[0]["data"], {"node_id": "N2"})
            self.assertEqual(g_evs[2]["tick"], 1201)
            self.assertEqual(g_evs[2]["data"]["node_id"], "N2")

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 1]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o.jsonl")), "gather"), [])

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "hold": ["ca_loc"] * 12,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20.5, 0]}],
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_catch_yield_cooldown_tiebreak_and_hold_full(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "fish": [
                    {"id": "F10", "kind": "ca_loc", "pos": [22, 5]},
                    {"id": "F2", "kind": "ca_linh", "pos": [18, 5]},
                ],
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 29, "catch": True},
                {"tick": 30, "catch": False},
                {"tick": 31, "catch": True},
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "32",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            fc = events(rows, "fish_caught")
            self.assertEqual(len(fc), 2)
            self.assertEqual(fc[0]["tick"], 1)
            self.assertEqual(fc[0]["data"], {"fish_id": "F2", "kind": "ca_linh", "yield": 3})
            self.assertEqual(fc[1]["tick"], 32)
            self.assertEqual(fc[1]["data"], {"fish_id": "F10", "kind": "ca_loc", "yield": 1})
            last_snap = snapshots(rows)[-1]
            self.assertEqual(last_snap["hold"], ["ca_linh", "ca_linh", "ca_linh", "ca_loc"])
            self.assertEqual(last_snap["fish"], [])

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows), [])
            self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 5]}],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows), [])
            self.assertEqual(snapshots(rows)[-1]["player"]["catch_cd_ticks"], 0)

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5]},
                "hold": ["bong_sung"] * 11,
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [20.5, 5]},
                    {"id": "F2", "kind": "ca_loc", "pos": [21.5, 5]},
                ],
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 1})
            self.assertEqual(events(rows, "fish_caught"), [])
            last_snap = snapshots(rows)[-1]
            self.assertEqual(len(last_snap["fish"]), 2)
            self.assertEqual(last_snap["player"]["catch_cd_ticks"], 0)

    def test_last_tick_priority_dock_harvest_catch_and_faint(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [5, 0]},
                "hold": ["ca_loc"],
                "time_left_ticks": 1,
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            self.assertEqual(rows[-1]["reason"], "docked")

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                "time_left_ticks": 1,
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--inventory-out", inv,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([r["name"] for r in events(rows)], ["gather", "gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1}})

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [2, 0.6], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "hold": ["ca_loc"],
                "time_left_ticks": 1,
                "random_fish": False,
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--inventory-out", inv,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_gather_determinism_with_interact_and_catch(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [12, 0]},
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False, "move": [0, 1]},
                {"tick": 75, "move": [1, 0], "catch": True},
                {"tick": 76, "catch": False},
                {"tick": 120, "move": [-1, -1]},
            ))
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "99", "--ticks", "180",
                                         "--scenario", sc, "--inputs", inp,
                                         "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
