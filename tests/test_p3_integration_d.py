"""v1.2 file/day handoff, ID lifecycle and unchanged P1/P2 rules."""

import json
import unittest

from helpers import events
from test_p3_inventory_d import Phase3Case, GATHER_DECAY, QUAN_DECAY, customer, gather, item, quan


class IntegrationV12(Phase3Case):
    def day_fixture(self, **gather_updates):
        fixture = gather(**gather_updates)
        # day stock comes only from Gather; declaring quan.stock is invalid.
        fixture["quan"] = {"time_left_ticks": 1, "random_customers": False}
        return fixture

    def test_file_handoff_preserves_ids_kind_and_exact_post_gather_freshness(self):
        fixture = gather(hold=[item("I1", "ca_linh")], player={"pos": self.t["gather"]["dock_pos"]})
        self.run_game("gather", fixture, ticks=1, inputs=[{"tick": 0, "interact": True}], inventory_out=True)
        saved = json.loads(self.inventory_output.read_text(encoding="utf-8"))
        self.assertEqual(saved, self.one("gather_end", 1)["data"]["inventory"])
        self.assertEqual([(i["id"], i["kind"]) for i in saved["items"]], [("I1", "ca_linh")])
        self.fresh(saved["items"][0]["fresh"], 100 - GATHER_DECAY)
        source = self.inventory_output
        self.run_game("quan", inventory_source=source)
        self.assertEqual(self.snap(0)["stock"], saved["items"], "no extra decay or ID reassignment at import")

    def test_day_handoff_is_same_tick_without_second_decay(self):
        fixture = self.day_fixture(hold=[item("I7", fresh=80)], time_left_ticks=1)
        fixture["quan"]["time_left_ticks"] = 3
        self.run_game("day", fixture, ticks=2, days=1)
        ended = self.one("gather_end", 1)["data"]["inventory"]["items"]
        self.assertEqual(self.snap(1)["phase"], "quan")
        self.assertEqual(self.snap(1)["phase_tick"], 0)
        self.assertEqual(self.snap(1)["stock"], ended)
        self.fresh(ended[0]["fresh"], 80 - GATHER_DECAY)
        self.assertEqual(self.snap(2)["phase_tick"], 1)
        self.assertEqual(self.snap(2)["stock"][0]["id"], "I7")
        self.fresh(self.snap(2)["stock"][0]["fresh"], 80 - GATHER_DECAY - QUAN_DECAY)
        self.assertEqual([(e["name"], e["phase"]) for e in events(self.rows) if e["tick"] == 1],
                         [("gather_end", "gather"), ("phase_start", "quan")])

    def test_shop_raw_stock_stops_decay_while_active_or_paused(self):
        fixture = self.day_fixture(hold=[item(fresh=80)], time_left_ticks=1)
        self.run_game("day", fixture, ticks=8, days=1,
                      inputs=[{"tick": 2, "pause": True}, {"tick": 3, "pause": False},
                              {"tick": 6, "pause": True}])
        transferred = self.snap(2)["stock"]
        self.assertEqual(self.snap(2)["phase"], "shop")
        self.fresh(transferred[0]["fresh"], 80 - GATHER_DECAY - QUAN_DECAY)
        for tick in range(2, 9):
            self.assertEqual(self.snap(tick)["stock"], transferred)
        self.assertEqual(self.snap(3)["state"], "paused")
        self.assertEqual(self.snap(7)["state"], "playing")

    def test_new_ids_follow_loaded_max_and_remain_distinct_for_each_yield(self):
        fish = {"id": "F1", "kind": "ca_linh", "pos": [20, 5]}
        self.run_game("gather", gather(hold=[item("I9"), item("I2")],
                                      player={"pos": [20, 5]}, fish=[fish]),
                      ticks=1, inputs=[{"tick": 0, "catch": True}])
        count = self.t["gather"]["fish_yield"]["ca_linh"]
        self.assertEqual([v["id"] for v in self.snap(1)["hold"]],
                         ["I9", "I2"] + [f"I{i}" for i in range(10, 10 + count)])
        self.entities(self.snap(1)["hold"])

    def test_item_ids_increase_across_days_even_after_shop_discards_leftovers(self):
        node = {"id": "N1", "kind": "bong_dien_dien", "pos": [20, 0]}
        fixture = self.day_fixture(hold=[item("I7"), item("I2", "bong_sung", 80)],
                                   nodes=[node], time_left_ticks=2)
        self.run_game("day", fixture, ticks=5, days=2, inputs=[
            {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
            {"tick": 3, "shop_done": True}, {"tick": 4, "interact": True}])
        self.assertEqual([v["id"] for v in self.snap(0)["hold"]], ["I7", "I2"])
        self.assertEqual([v["id"] for v in self.snap(1)["hold"]], ["I7", "I2", "I8"])
        self.assertEqual((self.snap(4)["day"], self.snap(4)["phase"]), (2, "gather"))
        self.assertEqual(self.snap(4)["hold"], [item("I9"), item("I10", "bong_sung", 80)])
        self.assertEqual([v["id"] for v in self.snap(5)["hold"]], ["I9", "I10", "I11"])

    def test_consumed_id_is_not_reused_in_next_day_template(self):
        fixture = self.day_fixture(hold=[item("I7", fresh=70)], time_left_ticks=1)
        fixture["quan"] = {"time_left_ticks": 2, "random_customers": False,
                           "player": {"pos": [2, 8]}, "customers": [customer()]}
        self.run_game("day", fixture, ticks=4, days=2,
                      inputs=[{"tick": 1, "interact": True}, {"tick": 3, "shop_done": True}])
        self.assertEqual(self.one("cook_started", 2)["data"]["items"][0]["id"], "I7")
        self.assertEqual(self.snap(2)["stock"], [])
        self.assertEqual(self.snap(4)["hold"], [item("I8", fresh=70)])

    def test_faint_handoff_to_day_quan_has_empty_individual_stock(self):
        fixture = self.day_fixture(hold=[item()], player={"pos": [20, 5], "oxygen_ticks": 0,
                                  "zero_oxy_ticks": self.t["gather"]["choke_interval_ticks"] - 1, "hp": 1})
        self.run_game("day", fixture, ticks=1, days=1)
        self.assertEqual([e["name"] for e in events(self.rows) if e["tick"] == 1],
                         ["choke", "faint", "gather_end", "phase_start"])
        self.assertEqual(self.one("gather_end", 1)["data"]["inventory"], {"items": []})
        self.assertEqual((self.snap(1)["phase"], self.snap(1)["stock"]), ("quan", []))

    def test_deterministic_bytes_for_identical_individual_fixture_and_inputs(self):
        fixture = gather(hold=[item("I10", fresh=30.125), item("I2", fresh=80)], time_left_ticks=16)
        results = []
        for _ in range(2):
            self.run_game("gather", fixture, ticks=16, seed=42, inventory_out=True)
            self.one("spoiled", 16)
            results.append((self.output.read_bytes(), self.inventory_output.read_bytes()))
        self.assertEqual(results[0], results[1])


class UnchangedRegression(Phase3Case):
    def test_p1_underwater_oxygen_consumes_one_per_gameplay_step(self):
        self.run_game("gather", gather(player={"pos": [20, 5]}), ticks=60)
        maximum = round(self.t["gather"]["oxygen_max_s"] * self.hz)
        for tick in range(61):
            self.assertEqual(self.snap(tick)["player"]["oxygen_ticks"], maximum - tick)

    def test_p2_pause_stops_clock_and_inputs_until_resume_edge(self):
        self.run_game("gather", gather(), ticks=5, inputs=[
            {"tick": 0, "pause": True, "interact": True},
            {"tick": 1, "pause": False}, {"tick": 3, "pause": True}])
        self.assertEqual([(e["tick"], e["name"]) for e in events(self.rows)], [(1, "paused"), (4, "resumed")])
        self.assertEqual(self.snap(3)["sim_tick"], 0)
        self.assertEqual(self.snap(5)["sim_tick"], 2)
        self.assertEqual(self.snap(3)["hold"], [])

    def test_p1_dock_priority_over_harvest_keeps_individual_handoff_schema(self):
        dock = self.t["gather"]["dock_pos"]
        fixture = gather(player={"pos": dock}, nodes=[{"id": "N1", "kind": "bong_sung", "pos": dock}],
                         time_left_ticks=1)
        self.run_game("gather", fixture, ticks=1, inventory_out=True,
                      inputs=[{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in events(self.rows)], ["gather_end"])
        self.assertEqual(self.one("gather_end", 1)["data"], {"reason": "docked", "inventory": {"items": []}})

    def test_p2_four_tables_and_two_stoves_remain_in_quan_snapshot(self):
        self.run_game("quan", quan())
        self.assertEqual([s["id"] for s in self.snap(0)["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in self.snap(0)["tables"]], ["T1", "T2", "T3", "T4"])

    def test_p1_service_on_closing_tick_is_paid_before_quan_end(self):
        payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 47}
        c = customer(order_status="assigned", reserved=[], patience_ticks_left=1)
        self.run_game("quan", quan(hand=payload, customers=[c], time_left_ticks=1,
                                    player={"pos": [9, 2]}), ticks=1,
                      inputs=[{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in events(self.rows)], ["served", "paid", "quan_end"])
        self.assertEqual(self.one("paid", 1)["data"]["amount"], 47)
        self.assertEqual(self.one("paid", 1)["data"]["reason"], "closing")


if __name__ == "__main__":
    unittest.main()
