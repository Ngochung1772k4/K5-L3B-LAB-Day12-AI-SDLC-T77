"""TICKET-03 core: decay, exact spoiled ticks/order, pause and LIFO payloads."""

import json
import unittest

from helpers import events
from test_p3_inventory_d import Phase3Case, GATHER_DECAY, QUAN_DECAY, gather, item, quan


class FreshnessV12(Phase3Case):
    def test_gather_existing_items_decay_half_point_per_sixty_active_steps(self):
        self.run_game("gather", gather(hold=[item(fresh=80)]), ticks=60)
        for tick in range(61):
            self.fresh(self.entities(self.snap(tick)["hold"])["I1"]["fresh"], 80 - tick * GATHER_DECAY)
        self.fresh(self.snap(60)["hold"][0]["fresh"], 79.5)

    def test_quan_raw_items_decay_quarter_point_per_sixty_steps(self):
        self.run_game("quan", quan(stock=[item(fresh=80)]), ticks=60)
        for tick in range(61):
            self.fresh(self.entities(self.snap(tick)["stock"])["I1"]["fresh"], 80 - tick * QUAN_DECAY)
        self.fresh(self.snap(60)["stock"][0]["fresh"], 79.75)

    def test_freshness_clamps_at_zero_in_both_phases(self):
        for mode, fixture, key in (("gather", gather(hold=[item(fresh=0.125)]), "hold"),
                                   ("quan", quan(stock=[item(fresh=0.125)]), "stock")):
            with self.subTest(mode=mode):
                self.run_game(mode, fixture, ticks=60)
                self.assertEqual(self.snap(60)[key][0]["fresh"], 0)
                self.assertEqual(len(self.snap(60)[key]), 1, "spoiled items still occupy storage")
                self.assertEqual(events(self.rows, "spoiled"), [], "initially spoiled is not a crossing")

    def test_exactly_thirty_spoils_on_first_step_in_both_phases(self):
        for mode, fixture, location in (("gather", gather(hold=[item(fresh=30)]), "hold"),
                                        ("quan", quan(stock=[item(fresh=30)]), "stock")):
            with self.subTest(mode=mode):
                self.run_game(mode, fixture, ticks=3)
                self.assertEqual(self.one("spoiled", 1)["data"],
                                 {"item_id": "I1", "kind": "ca_loc", "location": location})
                self.assertLess(self.snap(1)[location][0]["fresh"], 30)

    def test_exact_threshold_is_not_spoiled_until_following_tick(self):
        # 30.125 is exactly representable; after 15/30 ticks it is exactly 30.
        for mode, fixture, key, boundary in (
            ("gather", gather(hold=[item(fresh=30.125)]), "hold", 15),
            ("quan", quan(stock=[item(fresh=30.125)]), "stock", 30),
        ):
            with self.subTest(mode=mode):
                self.run_game(mode, fixture, ticks=boundary + 2)
                self.fresh(self.snap(boundary)[key][0]["fresh"], 30)
                self.assertEqual(self.one("spoiled", boundary + 1)["data"]["item_id"], "I1")

    def test_simultaneous_spoiled_events_use_numeric_id_order_and_emit_once(self):
        values = [item("I10", fresh=30), item("I2", fresh=30), item("I1", fresh=29)]
        for mode, fixture, location in (("gather", gather(hold=values), "hold"),
                                        ("quan", quan(stock=values), "stock")):
            with self.subTest(mode=mode):
                self.run_game(mode, fixture, ticks=5)
                self.assertEqual([(e["tick"], e["data"]) for e in events(self.rows, "spoiled")],
                                 [(1, {"item_id": "I2", "kind": "ca_loc", "location": location}),
                                  (1, {"item_id": "I10", "kind": "ca_loc", "location": location})])
                self.assertEqual(len(self.snap(5)[location]), 3)

    def test_spoiled_precedes_choke_and_faint_in_gather_tick(self):
        block = gather(hold=[item(fresh=30)], player={"pos": [20, 5], "oxygen_ticks": 0,
                       "zero_oxy_ticks": self.t["gather"]["choke_interval_ticks"] - 1, "hp": 1},
                       time_left_ticks=1)
        self.run_game("gather", block, ticks=1, inventory_out=True)
        self.assertEqual([e["name"] for e in events(self.rows)],
                         ["spoiled", "choke", "faint", "gather_end"])
        self.assertEqual(self.one("faint", 1)["data"]["lost"][0]["id"], "I1")
        self.assertEqual(json.loads(self.inventory_output.read_text(encoding="utf-8")), {"items": []})

    def test_pause_freezes_freshness_and_delays_spoiled_until_resume_step(self):
        inputs = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 3, "pause": True}]
        for mode, fixture, key in (("gather", gather(hold=[item(fresh=30)]), "hold"),
                                   ("quan", quan(stock=[item(fresh=30)]), "stock")):
            with self.subTest(mode=mode):
                self.run_game(mode, fixture, ticks=5, inputs=inputs)
                for tick in (1, 2, 3):
                    self.assertEqual(self.snap(tick)["state"], "paused")
                    self.assertEqual(self.snap(tick)["sim_tick"], 0)
                    self.assertEqual(self.snap(tick)[key][0]["fresh"], 30)
                self.one("spoiled", 4)
                self.assertEqual(self.snap(5)["sim_tick"], 2)

    def test_new_harvest_starts_at_one_hundred_then_decays_from_next_step(self):
        node = {"id": "N1", "kind": "bong_sung", "pos": [20, 0]}
        self.run_game("gather", gather(nodes=[node]), ticks=2,
                      inputs=[{"tick": 0, "interact": True}])
        self.one("gather", 1)
        first = self.entities(self.snap(1)["hold"])
        self.assertEqual(first, {"I1": item("I1", "bong_sung")})
        self.fresh(self.snap(2)["hold"][0]["fresh"], 100 - GATHER_DECAY)

    def test_new_fish_yield_gets_distinct_ids_and_no_same_tick_decay(self):
        fish = {"id": "F1", "kind": "ca_linh", "pos": [20, 5], "heading_deg": 0}
        self.run_game("gather", gather(player={"pos": [20, 5]}, fish=[fish]), ticks=2,
                      inputs=[{"tick": 0, "catch": True}])
        amount = self.t["gather"]["fish_yield"]["ca_linh"]
        self.assertEqual(self.one("fish_caught", 1)["data"]["yield"], amount)
        self.assertEqual(self.snap(1)["hold"], [item(f"I{i + 1}", "ca_linh") for i in range(amount)])
        for value in self.snap(2)["hold"]:
            self.fresh(value["fresh"], 100 - GATHER_DECAY)

    def test_spoiled_items_still_fill_hold_and_block_harvesting(self):
        capacity = self.t["gather"]["hold_capacity"]
        values = [item(f"I{i+1}", fresh=29) for i in range(capacity)]
        self.run_game("gather", gather(hold=values, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}]),
                      ticks=1, inputs=[{"tick": 0, "interact": True}])
        self.assertEqual(self.one("hold_full", 1)["data"],
                         {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
        self.assertEqual(self.snap(1)["hold_count"], capacity)
        self.assertEqual(events(self.rows, "gather"), [])

    def test_monster_hit_and_faint_lost_payloads_are_items_in_lifo_order(self):
        values = [item(f"I{i+1}", fresh=80) for i in range(5)]
        monster = {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}
        self.run_game("gather", gather(hold=values, player={"pos": [60, 24], "hp": 1},
                                      monsters=[monster]), ticks=1, inventory_out=True)
        hit = self.one("monster_hit", 1)["data"]
        faint = self.one("faint", 1)["data"]
        self.assertEqual([i["id"] for i in hit["lost"]], ["I5", "I4"])
        self.assertEqual([i["id"] for i in faint["lost"]], ["I3", "I2", "I1"])
        for value in hit["lost"] + faint["lost"]:
            self.fresh(value["fresh"], 80 - GATHER_DECAY)
        self.assertEqual(faint["cause"], "monster")
        self.assertEqual(self.one("gather_end", 1)["data"]["inventory"], {"items": []})


if __name__ == "__main__":
    unittest.main()
