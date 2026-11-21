"""Black-box Gather rules from PRD-0, Test Contract v1.0 C--G.

Run with PYTHONDONTWRITEBYTECODE=1; all runtime files live in Workdir.
An exit code other than zero is a test/fixture or startup ERROR, not a
successful run whose rule assertions have failed. Do not weaken assertions
while the gameplay TODOs are being implemented.
"""

import json
import os
from collections import Counter
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from helpers import (

    ROOT, Workdir, events, frames, headless_cmd, read_jsonl, run_headless, snapshots, write_json,
)


# TẠM SKIP (Phase 3, C/Integrator): fixture còn schema v1.1 (hold chuỗi, stock map, kho đếm).
# v1.2 đổi sang kho cá thể {id, kind, fresh} — xem docs/adr/0001-kho-ca-the-do-tuoi.md, CHANGELOG.md.
# Chủ file D (uscalurn): đổi fixture bằng helpers.items(...)/stock_of(...)/counts(...) rồi XÓA 2 dòng dưới.
raise unittest.SkipTest("fixture v1.1 chờ D (uscalurn) chuyển sang kho cá thể v1.2 (ADR 0001)")


def run_cli(*args):
    """Keep the manifest command; replace only an unusable Windows python3 alias.

    The patch lasts for this subprocess call; helpers.py and PATH stay intact.
    Nonzero CLI exits and unrelated executable errors are never retried.
    """
    try:
        return run_headless(*args)
    except OSError as error:
        command = headless_cmd()
        missing_alias = error.errno in (2, 13) or getattr(error, "winerror", None) in (2, 5, 1920)
        if os.name != "nt" or command[0] not in ("python3", "python3.exe") or not missing_alias:
            raise
        with patch("helpers.headless_cmd", return_value=[sys.executable, "-B", *command[1:]]):
            return run_headless(*args)


class GatherRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(Path(ROOT) / "game.contract.json", encoding="utf-8") as source:
            tuning = json.load(source)["tuning"]
        cls.g = tuning["gather"]
        cls.hz = tuning["tick_hz"]
        cls.oxygen_max = round(cls.g["oxygen_max_s"] * cls.hz)

    def setUp(self):
        self.work = Workdir()
        self.work.__enter__()
        self.addCleanup(self.work.__exit__, None, None, None)
        self.serial = 0
        self.x = sum(self.g["bounds"]["x"]) / 2
        self.deep = self.g["surface_depth"] + 1

    def run_case(self, block, ticks, *input_frames, seed=17):
        self.serial += 1
        prefix = str(self.serial)
        fixture = {
            "player": {"pos": [self.x, 0]},
            "nodes": [], "fish": [], "random_fish": False,
        }
        fixture.update(block)
        scenario = write_json(self.work.path(prefix + "-scenario.json"), {"gather": fixture})
        inputs = write_json(self.work.path(prefix + "-inputs.json"), frames(*input_frames))
        self.output = Path(self.work.path(prefix + ".jsonl"))
        self.inventory = Path(self.work.path(prefix + "-inventory.json"))
        code, stderr = run_cli(
            "--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
            "--scenario", scenario, "--inputs", inputs, "--snapshot-every", "1",
            "--out", str(self.output), "--inventory-out", str(self.inventory),
        )
        if code != 0:
            raise RuntimeError(
                f"Headless startup/fixture ERROR (exit {code}; 2 means Contract D "
                f"rejection, not a gameplay assertion): {stderr}"
            )
        rows = read_jsonl(self.output)
        self.assertEqual(rows[-1]["type"], "end")
        self.assertEqual(sum(row["type"] == "end" for row in rows), 1)
        self.s = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(len(self.s), len(snapshots(rows)))
        self.assertEqual(sorted(self.s), list(range(rows[-1]["ticks"] + 1)))
        for tick, snap in self.s.items():
            self.assertEqual((snap["sim_tick"], snap["phase_tick"]), (tick, tick))
            self.assertEqual((snap["mode"], snap["phase"]), ("gather", "gather"))
            self.assertEqual(snap["hold_count"], len(snap["hold"]))
            self.assertLessEqual(snap["hold_count"], self.g["hold_capacity"])
        for event in events(rows):
            self.assertEqual(event["phase"], "gather")
            self.assertIn(event["tick"], self.s)
            self.assertGreater(event["tick"], 0)
            self.assertLess(rows.index(event), rows.index(self.s[event["tick"]]),
                            "events must precede their tick's snapshot (Contract E)")
        return rows

    def node(self, ident="N1", x=None, regrow=0, kind="bong_sung"):
        return {"id": ident, "kind": kind, "pos": [self.x if x is None else x, 0],
                "regrow_ticks": regrow}

    def fish(self, ident="F1", x=None, depth=None, kind="ca_linh"):
        return {"id": ident, "kind": kind,
                "pos": [self.x if x is None else x, self.deep if depth is None else depth],
                "heading_deg": 0}

    def one_event(self, rows, name, tick, data):
        found = events(rows, name)
        self.assertEqual(len(found), 1, f"{name}: {found}")
        self.assertEqual(found[0]["tick"], tick)
        self.assertEqual(found[0]["data"], data)
        return found[0]

    def test_oxygen_decreases_one_per_underwater_step_including_sixty_steps(self):
        self.run_case({"player": {"pos": [self.x, self.deep]}}, 60)
        for tick, snap in self.s.items():
            self.assertEqual(snap["player"]["oxygen_ticks"], self.oxygen_max - tick)
            self.assertEqual(snap["player"]["zero_oxy_ticks"], 0)
            self.assertFalse(snap["player"]["at_surface"])
        self.assertEqual(self.s[60]["player"]["oxygen_ticks"], self.oxygen_max - 60)

    def test_surface_refill_uses_tuning_and_clamps_at_maximum(self):
        refill = self.g["oxygen_refill_per_tick"]
        initial = self.oxygen_max - 2 * refill - 1
        rows = self.run_case({"player": {"pos": [self.x, self.g["surface_depth"]],
                                         "oxygen_ticks": initial}}, 4)
        for tick, snap in self.s.items():
            self.assertEqual(snap["player"]["oxygen_ticks"],
                             min(self.oxygen_max, initial + tick * refill))
            self.assertEqual(snap["player"]["zero_oxy_ticks"], 0)
            self.assertTrue(snap["player"]["at_surface"])
        self.assertEqual(events(rows), [])

    def test_oxygen_empty_occurs_only_on_positive_to_zero_transition(self):
        rows = self.run_case({"player": {"pos": [self.x, self.deep], "oxygen_ticks": 2}}, 5)
        self.one_event(rows, "oxygen_empty", 2, {"oxygen_ticks": 0})
        for tick, snap in self.s.items():
            self.assertEqual(snap["player"]["oxygen_ticks"], max(0, 2 - tick))
            self.assertEqual(snap["player"]["zero_oxy_ticks"], max(0, tick - 1))

    def test_zero_oxygen_counts_empty_step_and_chokes_at_exact_intervals(self):
        interval = self.g["choke_interval_ticks"]
        rows = self.run_case({"player": {"pos": [self.x, self.deep], "oxygen_ticks": 1}},
                             2 * interval)
        self.one_event(rows, "oxygen_empty", 1, {"oxygen_ticks": 0})
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "choke")],
                         [(interval, {"hp": self.g["hp_max"] - 1}),
                          (2 * interval, {"hp": self.g["hp_max"] - 2})])
        for tick in range(1, 2 * interval + 1):
            self.assertEqual(self.s[tick]["player"]["zero_oxy_ticks"], tick % interval)
            self.assertEqual(self.s[tick]["player"]["hp"], self.g["hp_max"] - tick // interval)
        self.assertEqual(events(rows, "faint"), [])

    def test_fixture_zero_oxygen_counter_continues_without_duplicate_empty_event(self):
        interval = self.g["choke_interval_ticks"]
        rows = self.run_case({"player": {"pos": [self.x, self.deep], "oxygen_ticks": 0,
                                         "zero_oxy_ticks": interval - 2}}, 2)
        self.assertEqual(self.s[1]["player"]["zero_oxy_ticks"], interval - 1)
        self.assertEqual(self.s[2]["player"]["zero_oxy_ticks"], 0)
        self.one_event(rows, "choke", 2, {"hp": self.g["hp_max"] - 1})
        self.assertEqual(events(rows, "oxygen_empty"), [])

    def test_nonfatal_choke_preserves_every_item_in_hold(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        rows = self.run_case({"hold": hold, "player": {
            "pos": [self.x, self.deep], "oxygen_ticks": 0,
            "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1,
        }}, 1)
        self.one_event(rows, "choke", 1, {"hp": self.g["hp_max"] - 1})
        self.assertEqual(self.s[1]["hold"], hold)
        self.assertEqual(events(rows, "faint") + events(rows, "gather_end"), [])
        self.assertFalse(self.inventory.exists())

    def test_surfacing_on_choke_deadline_refills_and_resets_counter(self):
        pos = [self.x, self.g["surface_depth"] + 0.001]
        rows = self.run_case({"player": {"pos": pos, "vel": [0, -self.g["swim_speed"]],
                                         "oxygen_ticks": 0, "hp": 1,
                                         "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1}},
                             1, {"tick": 0, "move": [0, -1]})
        player = self.s[1]["player"]
        self.assertTrue(player["at_surface"])
        self.assertEqual(player["oxygen_ticks"], self.g["oxygen_refill_per_tick"])
        self.assertEqual((player["hp"], player["zero_oxy_ticks"]), (1, 0))
        self.one_event(rows, "surface", 1, {"pos": player["pos"]})
        for name in ("choke", "faint", "oxygen_empty"):
            self.assertEqual(events(rows, name), [])

    def test_faint_discards_hold_lifo_and_precedes_actions_and_time_end(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        pos = [self.g["dock_pos"][0], self.g["surface_depth"] + 0.01]
        rows = self.run_case({
            "player": {"pos": pos, "oxygen_ticks": 0, "hp": 1,
                       "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1},
            "hold": hold, "fish": [self.fish(x=pos[0], depth=pos[1])],
            "time_left_ticks": 1,
        }, 20, {"tick": 0, "interact": True, "catch": True})
        self.assertEqual([(e["name"], e["tick"]) for e in events(rows)],
                         [("choke", 1), ("faint", 1), ("gather_end", 1)])
        self.one_event(rows, "choke", 1, {"hp": 0})
        self.one_event(rows, "faint", 1, {"cause": "choke", "lost": hold[::-1], "hp": 0})
        self.one_event(rows, "gather_end", 1,
                       {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(self.s[1]["hold"], [])
        self.assertEqual(self.s[1]["player"]["hp"], 0)
        self.assertEqual((rows[-1]["ticks"], rows[-1]["reason"], rows[-1]["state"]),
                         (1, "fainted", "finished"))
        self.assertEqual(json.loads(self.inventory.read_text(encoding="utf-8")), {"items": {}})

    def test_dive_and_surface_only_when_movement_crosses_boundary(self):
        rows = self.run_case({"player": {"pos": [self.x, self.g["surface_depth"]],
                                         "vel": [0, self.g["swim_speed"]]}}, 24,
                             {"tick": 0, "move": [0, 1]}, {"tick": 4, "move": [0, -1]})
        expected = []
        for tick in range(1, 25):
            before = self.s[tick - 1]["player"]["at_surface"]
            after = self.s[tick]["player"]["at_surface"]
            if before != after:
                expected.append(("dive" if before else "surface", tick,
                                 {"pos": self.s[tick]["player"]["pos"]}))
        self.assertEqual([entry[0] for entry in expected], ["dive", "surface"])
        self.assertEqual(expected[0][1], 1)
        self.assertEqual([(e["name"], e["tick"], e["data"]) for e in events(rows)], expected)

    def test_stationary_player_emits_no_boundary_crossing_events(self):
        for depth in (self.g["surface_depth"], self.deep):
            with self.subTest(depth=depth):
                rows = self.run_case({"player": {"pos": [self.x, depth]}}, 3)
                self.assertEqual(events(rows, "dive") + events(rows, "surface"), [])

    def test_gather_requires_surface_ready_node_and_inclusive_radius(self):
        radius = self.g["interact_radius"]
        cases = [(0, radius, 0, True), (self.g["surface_depth"] + 0.01, 0, 0, False),
                 (0, 0, 2, False), (0, radius + 0.001, 0, False)]
        for depth, distance, regrow, allowed in cases:
            with self.subTest(depth=depth, distance=distance, regrow=regrow):
                node = self.node(x=self.x + distance, regrow=regrow)
                rows = self.run_case({"player": {"pos": [self.x, depth]}, "nodes": [node]},
                                     1, {"tick": 0, "interact": True})
                if allowed:
                    self.one_event(rows, "gather", 1,
                                   {"node_id": "N1", "kind": node["kind"],
                                    "amount": self.g["node_yield"]})
                    self.assertEqual(self.s[1]["hold"], [node["kind"]] * self.g["node_yield"])
                else:
                    self.assertEqual(events(rows, "gather"), [])
                    self.assertEqual(self.s[1]["hold"], [])
                    self.assertEqual(self.s[1]["nodes"][0]["regrow_ticks"], max(0, regrow - 1))

    def test_gather_selects_nearest_ready_node_then_numeric_id(self):
        nodes = [self.node("N10"), self.node("N2"), self.node("N1", x=self.x + 1),
                 self.node("N0", regrow=2)]
        rows = self.run_case({"nodes": nodes}, 1, {"tick": 0, "interact": True})
        self.one_event(rows, "gather", 1, {"node_id": "N2", "kind": "bong_sung",
                                          "amount": self.g["node_yield"]})
        self.assertEqual([n["id"] for n in self.s[1]["nodes"]], ["N0", "N1", "N2", "N10"])
        remaining = {n["id"]: n["regrow_ticks"] for n in self.s[1]["nodes"]}
        self.assertEqual(remaining, {"N0": 1, "N1": 0, "N2": round(self.g["regrow_s"] * self.hz),
                                     "N10": 0})

    def test_gather_radius_uses_depth_as_well_as_horizontal_distance(self):
        rows = self.run_case({"player": {"pos": [self.x, self.g["surface_depth"]]},
                              "nodes": [self.node(x=self.x + self.g["interact_radius"])]},
                             1, {"tick": 0, "interact": True})
        self.assertEqual(events(rows, "gather") + events(rows, "hold_full"), [])
        self.assertEqual(self.s[1]["hold"], [])
        self.assertEqual(self.s[1]["nodes"], self.s[0]["nodes"])

    def test_full_hold_emits_hold_full_without_changing_ready_node(self):
        hold = ["ca_loc"] * self.g["hold_capacity"]
        rows = self.run_case({"hold": hold, "nodes": [self.node()]},
                             1, {"tick": 0, "interact": True})
        self.one_event(rows, "hold_full", 1,
                       {"action": "gather", "node_id": "N1", "required": self.g["node_yield"], "free": 0})
        self.assertEqual(self.s[1]["nodes"], self.s[0]["nodes"])
        self.assertEqual(self.s[1]["hold"], hold)
        self.assertEqual(events(rows, "gather"), [])

    def test_node_regrows_exactly_after_configured_delay_and_can_be_picked_that_tick(self):
        delay = round(self.g["regrow_s"] * self.hz)
        rows = self.run_case({"nodes": [self.node()]}, delay + 1,
                             {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                             {"tick": delay - 2, "interact": True},
                             {"tick": delay - 1, "interact": False},
                             {"tick": delay, "interact": True})
        self.assertEqual([e["tick"] for e in events(rows, "gather")], [1, delay + 1])
        self.one_event(rows, "node_regrown", delay + 1, {"node_id": "N1"})
        self.assertEqual(self.s[1]["nodes"][0]["regrow_ticks"], delay)
        self.assertEqual(self.s[delay]["nodes"][0]["regrow_ticks"], 1)
        self.assertFalse(self.s[delay]["nodes"][0]["ready"])
        self.assertEqual(self.s[delay + 1]["nodes"][0]["regrow_ticks"], delay)
        self.assertEqual(self.s[delay + 1]["hold_count"], 2 * self.g["node_yield"])
        self.assertEqual([e["name"] for e in events(rows) if e["tick"] == delay + 1],
                         ["node_regrown", "gather"])

    def test_fixture_regrowth_counts_down_once_and_emits_ready_events_in_id_order(self):
        rows = self.run_case({"nodes": [self.node("N10", regrow=3), self.node("N2", regrow=3)]}, 4)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "node_regrown")],
                         [(3, {"node_id": "N2"}), (3, {"node_id": "N10"})])
        for tick in range(5):
            for node in self.s[tick]["nodes"]:
                self.assertEqual(node["regrow_ticks"], max(0, 3 - tick))
                self.assertEqual(node["ready"], tick >= 3)

    def test_held_interact_does_not_pick_second_node_until_new_rising_edge(self):
        rows = self.run_case({"nodes": [self.node("N2"), self.node("N1")]}, 5,
                             {"tick": 0, "interact": True}, {"tick": 1, "interact": True},
                             {"tick": 3, "interact": False}, {"tick": 4, "interact": True})
        self.assertEqual([(e["tick"], e["data"]["node_id"]) for e in events(rows, "gather")],
                         [(1, "N1"), (5, "N2")])
        self.assertEqual(self.s[4]["hold_count"], self.g["node_yield"])
        self.assertEqual(self.s[5]["hold_count"], 2 * self.g["node_yield"])

    def test_catch_requires_underwater_inclusive_radius_and_expired_cooldown(self):
        radius = self.g["catch_radius"]
        cases = [(self.deep, radius, 0, True), (self.g["surface_depth"], 0, 0, False),
                 (self.deep, radius + 0.001, 0, False), (self.deep, 0, 2, False),
                 (self.deep, 0, 1, True)]
        for depth, distance, cooldown, allowed in cases:
            with self.subTest(depth=depth, distance=distance, cooldown=cooldown):
                fish = self.fish(x=self.x + distance,
                                 depth=max(depth, self.g["surface_depth"] + 0.01))
                rows = self.run_case({"player": {"pos": [self.x, depth], "catch_cd_ticks": cooldown},
                                      "fish": [fish]}, 1, {"tick": 0, "catch": True})
                if allowed:
                    amount = self.g["fish_yield"][fish["kind"]]
                    self.one_event(rows, "fish_caught", 1,
                                   {"fish_id": "F1", "kind": fish["kind"], "yield": amount})
                    self.assertEqual(self.s[1]["fish"], [])
                    self.assertEqual(self.s[1]["hold"], [fish["kind"]] * amount)
                    self.assertEqual(self.s[1]["player"]["catch_cd_ticks"],
                                     round(self.g["catch_cooldown_s"] * self.hz))
                else:
                    self.assertEqual(events(rows, "fish_caught"), [])
                    self.assertEqual(self.s[1]["fish"], self.s[0]["fish"])
                    self.assertEqual(self.s[1]["hold"], [])
                    self.assertEqual(self.s[1]["player"]["catch_cd_ticks"], max(0, cooldown - 1))

    def test_insufficient_space_keeps_whole_fish_and_does_not_try_smaller_school(self):
        amount = self.g["fish_yield"]["ca_linh"]
        free = amount - 1
        hold = ["bong_sung"] * (self.g["hold_capacity"] - free)
        rows = self.run_case({"player": {"pos": [self.x, self.deep]}, "hold": hold,
                              "fish": [self.fish(), self.fish("F2", x=self.x + 0.5, kind="ca_loc")]},
                             1, {"tick": 0, "catch": True})
        self.one_event(rows, "hold_full", 1,
                       {"action": "catch", "fish_id": "F1", "required": amount, "free": free})
        self.assertEqual(self.s[1]["hold"], hold)
        self.assertEqual(self.s[1]["fish"], self.s[0]["fish"])
        self.assertEqual(self.s[1]["player"]["catch_cd_ticks"], 0)
        self.assertEqual(events(rows, "fish_caught"), [])

    def test_catch_accepts_whole_yield_when_free_space_is_exact(self):
        amount = self.g["fish_yield"]["ca_linh"]
        hold = ["bong_sung"] * (self.g["hold_capacity"] - amount)
        rows = self.run_case({"player": {"pos": [self.x, self.deep]},
                              "hold": hold, "fish": [self.fish()]},
                             1, {"tick": 0, "catch": True})
        self.one_event(rows, "fish_caught", 1, {"fish_id": "F1", "kind": "ca_linh", "yield": amount})
        self.assertEqual(self.s[1]["hold"], hold + ["ca_linh"] * amount)
        self.assertEqual(self.s[1]["hold_count"], self.g["hold_capacity"])
        self.assertEqual(self.s[1]["fish"], [])

    def test_catch_selects_nearest_school_then_numeric_id(self):
        rows = self.run_case({"player": {"pos": [self.x, self.deep]},
                              "fish": [self.fish("F10"), self.fish("F2"),
                                       self.fish("F1", x=self.x + 1)]},
                             1, {"tick": 0, "catch": True})
        self.one_event(rows, "fish_caught", 1,
                       {"fish_id": "F2", "kind": "ca_linh", "yield": self.g["fish_yield"]["ca_linh"]})
        self.assertEqual([f["id"] for f in self.s[1]["fish"]], ["F1", "F10"])

    def test_catch_cooldown_can_be_reused_at_exact_deadline(self):
        delay = round(self.g["catch_cooldown_s"] * self.hz)
        rows = self.run_case({"player": {"pos": [self.x, self.deep]},
                              "fish": [self.fish("F1"), self.fish("F2")]}, delay + 1,
                             {"tick": 0, "catch": True}, {"tick": 1, "catch": False},
                             {"tick": delay - 2, "catch": True},
                             {"tick": delay - 1, "catch": False}, {"tick": delay, "catch": True})
        self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")],
                         [(1, "F1"), (delay + 1, "F2")])
        self.assertEqual(self.s[1]["player"]["catch_cd_ticks"], delay)
        self.assertEqual(self.s[delay]["player"]["catch_cd_ticks"], 1)
        self.assertEqual(self.s[delay + 1]["player"]["catch_cd_ticks"], delay)

    def test_held_catch_does_not_repeat_after_cooldown_expires(self):
        delay = round(self.g["catch_cooldown_s"] * self.hz)
        rows = self.run_case({"player": {"pos": [self.x, self.deep]},
                              "fish": [self.fish("F1"), self.fish("F2")]}, delay + 4,
                             {"tick": 0, "catch": True}, {"tick": delay, "catch": True},
                             {"tick": delay + 2, "catch": False},
                             {"tick": delay + 3, "catch": True})
        self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in events(rows, "fish_caught")],
                         [(1, "F1"), (delay + 4, "F2")])
        self.assertEqual(len(self.s[delay + 2]["fish"]), 1)
        self.assertEqual(self.s[delay + 2]["player"]["catch_cd_ticks"], 0)

    def test_catch_without_a_school_does_not_set_cooldown(self):
        rows = self.run_case({"player": {"pos": [self.x, self.deep]}},
                             1, {"tick": 0, "catch": True})
        self.assertEqual(events(rows), [])
        self.assertEqual(self.s[1]["player"]["catch_cd_ticks"], 0)
        self.assertEqual(self.s[1]["hold"], [])

    def test_docking_at_radius_on_last_tick_precedes_gather_and_writes_exact_inventory(self):
        pos = [self.g["dock_pos"][0] + self.g["dock_radius"], self.g["dock_pos"][1]]
        hold = ["ca_loc", "bong_sung", "ca_loc"]
        rows = self.run_case({"player": {"pos": pos}, "hold": hold,
                              "nodes": [self.node(x=pos[0])], "time_left_ticks": 1},
                             10, {"tick": 0, "interact": True})
        expected = {"items": dict(Counter(hold))}
        self.assertEqual([e["name"] for e in events(rows)], ["gather_end"])
        self.one_event(rows, "gather_end", 1, {"reason": "docked", "inventory": expected})
        self.assertEqual(self.s[1]["nodes"], self.s[0]["nodes"])
        self.assertEqual(self.s[1]["hold"], hold)
        self.assertEqual(json.loads(self.inventory.read_text(encoding="utf-8")), expected)
        self.assertEqual((rows[-1]["ticks"], rows[-1]["reason"]), (1, "docked"))

    def test_underwater_docking_precedes_catch_and_uses_two_dimensional_radius(self):
        radius = self.g["dock_radius"]
        for distance, docked in ((radius, True), (radius + 0.001, False)):
            with self.subTest(distance=distance):
                pos = [self.g["dock_pos"][0], self.g["dock_pos"][1] + distance]
                rows = self.run_case({"player": {"pos": pos}, "time_left_ticks": 1,
                                      "fish": [self.fish(x=pos[0], depth=pos[1])]},
                                     1, {"tick": 0, "interact": True, "catch": True})
                caught = not docked
                expected = {"items": {"ca_linh": self.g["fish_yield"]["ca_linh"]} if caught else {}}
                self.assertEqual([e["name"] for e in events(rows)],
                                 ["gather_end"] if docked else ["fish_caught", "gather_end"])
                self.one_event(rows, "gather_end", 1,
                               {"reason": "docked" if docked else "time", "inventory": expected})
                self.assertEqual(len(self.s[1]["fish"]), int(docked))
                self.assertEqual(json.loads(self.inventory.read_text(encoding="utf-8")), expected)

    def test_valid_gather_or_catch_on_last_tick_is_included_in_inventory(self):
        for action in ("gather", "catch"):
            with self.subTest(action=action):
                if action == "gather":
                    block = {"nodes": [self.node()]}
                    button, event_name, kind, amount = (
                        "interact", "gather", "bong_sung", self.g["node_yield"])
                else:
                    block = {"player": {"pos": [self.x, self.deep]}, "fish": [self.fish()]}
                    button, event_name, kind, amount = (
                        "catch", "fish_caught", "ca_linh", self.g["fish_yield"]["ca_linh"])
                block["time_left_ticks"] = 1
                rows = self.run_case(block, 1, {"tick": 0, button: True})
                expected = {"items": {kind: amount}}
                self.assertEqual([e["name"] for e in events(rows)], [event_name, "gather_end"])
                self.one_event(rows, "gather_end", 1, {"reason": "time", "inventory": expected})
                self.assertEqual(json.loads(self.inventory.read_text(encoding="utf-8")), expected)
                self.assertEqual(rows[-1]["reason"], "time")
                self.assertEqual(self.s[1]["hold"], [kind] * amount)

    def test_fixture_actions_produce_identical_jsonl_and_inventory_bytes(self):
        block = {"nodes": [self.node("N2"), self.node("N1")], "time_left_ticks": 5}
        inputs = ({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": 2, "interact": True})
        results = []
        for _ in range(2):
            rows = self.run_case(block, 10, *inputs, seed=42)
            self.assertEqual([e["tick"] for e in events(rows, "gather")], [1, 3])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "time")
            results.append((self.output.read_bytes(), self.inventory.read_bytes()))
        self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
