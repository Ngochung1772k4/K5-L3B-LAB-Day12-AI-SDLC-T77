"""Core ingredient reservations (not the optional reservations extension).

TICKET-03: reserve individual IDs, re-reserve once after spoilage, consume
those IDs, freeze floor(list price * mean freshness / 100), tip that price.
"""

import math
import unittest
from fractions import Fraction

from helpers import events
from test_p3_inventory_d import Phase3Case, QUAN_DECAY, customer, item, quan


class ReservationPriceV12(Phase3Case):
    def stove(self, tick, ident="B1"):
        found = [s for s in self.snap(tick)["stoves"] if s["id"] == ident]
        self.assertEqual(len(found), 1)
        return found[0]

    def price(self, dish_id, initial_freshness, elapsed=1):
        # Fraction avoids reproducing an implementation's binary rounding.
        mean = sum(Fraction(str(v)) - elapsed * QUAN_DECAY for v in initial_freshness) / len(initial_freshness)
        return math.floor(self.menu[dish_id]["price"] * mean / 100)

    def test_automatic_reservation_chooses_freshest_kind_then_numeric_id(self):
        stock = [item("I10", fresh=90), item("I2", fresh=90), item("I1", fresh=50),
                 item("I3", "bong_sung", 100)]
        self.run_game("quan", quan(stock=stock, customers=[customer()]))
        self.assertEqual(self.waiting(0)["reserved"], ["I2"])
        self.assertEqual(self.entities(self.snap(0)["stock"]), {v["id"]: v for v in stock})
        self.assertEqual(self.waiting(0)["order_status"], "reserved")

    def test_allocation_priority_is_order_tick_then_table_id_without_overbooking(self):
        for later_tick, expected in ((0, {"C1": "I2", "C2": "I10"}),
                                      (1, {"C1": "I10", "C2": "I2"})):
            with self.subTest(c1_order_tick=later_tick):
                # D allows nonnegative fixture order_tick; it is the order's
                # sorting key, not a request to advance phase_tick.
                clients = [customer("C2", "T2", order_tick=0), customer(order_tick=later_tick)]
                self.run_game("quan", quan(stock=[item("I10", fresh=70), item("I2", fresh=90)],
                                            customers=clients))
                for ident, reserved in expected.items():
                    self.assertEqual(self.waiting(0, ident)["reserved"], [reserved])
                claimed = [i for c in self.snap(0)["customers"] for i in c["reserved"]]
                self.assertEqual(len(claimed), len(set(claimed)))

    def test_invalid_reserved_ids_are_rejected_with_valid_fixture_control(self):
        stock = [item("I1"), item("I2", "bong_sung"), item("I3", fresh=29)]
        self.run_game("quan", quan(stock=stock, customers=[customer(reserved=["I1"])]))
        for ids in (["missing"], ["I2"], ["I3"], ["I1", "I1"]):
            with self.subTest(reserved=ids):
                self.rejected("quan", scenario=quan(stock=stock, customers=[customer(reserved=ids)]))

    def test_two_orders_cannot_reserve_same_physical_item(self):
        stock = [item("I1"), item("I2")]
        clients = [customer(reserved=["I1"]), customer("C2", "T2", reserved=["I2"])]
        self.run_game("quan", quan(stock=stock, customers=clients))
        clients[1]["reserved"] = ["I1"]
        self.rejected("quan", scenario=quan(stock=stock, customers=clients))

    def test_spoiled_raw_items_cannot_create_an_affordable_order(self):
        first = self.t["quan"]["first_customer_tick"]
        self.run_game("quan", quan(stock=[item(fresh=29)], random_customers=True), ticks=first)
        self.assertEqual(self.one("no_dish", first)["data"], {})
        self.assertEqual(self.snap(first)["customers"], [])
        self.assertEqual([i["id"] for i in self.snap(first)["stock"]], ["I1"])

    def test_reserved_items_decay_and_are_replaced_when_they_spoil(self):
        stock = [item("I1", fresh=30), item("I2", fresh=80)]
        self.run_game("quan", quan(stock=stock, customers=[customer(reserved=["I1"])]), ticks=1)
        self.assertEqual(self.one("spoiled", 1)["data"],
                         {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
        self.assertEqual(self.waiting(1)["reserved"], ["I2"])
        self.assertEqual(self.waiting(1)["order_status"], "reserved")
        physical = self.entities(self.snap(1)["stock"])
        self.assertEqual(set(physical), {"I1", "I2"})
        self.fresh(physical["I1"]["fresh"], 30 - QUAN_DECAY)
        self.fresh(physical["I2"]["fresh"], 80 - QUAN_DECAY)

    def test_spoilage_releases_entire_recipe_before_reselecting(self):
        stock = [item("I1", "bong_sung", 30), item("I2", "bong_sung", 60),
                 item("I3", "bong_sung", 90)]
        c = customer(dish="goi_bong_sung", reserved=["I1", "I2"])
        self.run_game("quan", quan(stock=stock, customers=[c]), ticks=1)
        self.assertCountEqual(self.waiting(1)["reserved"], ["I2", "I3"])
        self.assertEqual(self.waiting(1)["order_status"], "reserved")
        self.assertEqual(len(self.snap(1)["stock"]), 3)

    def test_failed_replacement_waits_unfulfillable_until_patience_expiry(self):
        c = customer(reserved=["I1"], patience_ticks_left=2)
        self.run_game("quan", quan(stock=[item(fresh=30)], customers=[c]), ticks=2)
        self.assertEqual(self.waiting(1)["order_status"], "unfulfillable")
        self.assertEqual(self.waiting(1)["reserved"], [])
        self.assertEqual(self.waiting(1)["state"], "waiting")
        self.assertEqual(self.one("customer_left", 2)["data"]["reason"], "patience")
        self.assertEqual(len(self.snap(2)["stock"]), 1)

    def test_affected_orders_retry_once_in_priority_order_after_all_spoiled_events(self):
        # C1 needs fish; C2 holds a fresh fish and a flower which spoils.
        # If C1 is first, it cannot use C2's fish yet and gets one failed try.
        # C2 then frees that fish but cannot replace its flower. C1 must not be
        # retried again that tick or on an unrelated following tick.
        for c1_tick, c1_status in ((0, "unfulfillable"), (1, "reserved")):
            with self.subTest(c1_order_tick=c1_tick):
                stock = [item("I1", fresh=30), item("I2", fresh=80),
                         item("I3", "bong_dien_dien", 30)]
                clients = [customer("C2", "T2", "canh_chua_ca_loc", reserved=["I2", "I3"], order_tick=0),
                           customer(reserved=["I1"], order_tick=c1_tick)]
                self.run_game("quan", quan(stock=stock, customers=clients), ticks=2)
                self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in events(self.rows, "spoiled")],
                                 [(1, "I1"), (1, "I3")])
                for tick in (1, 2):
                    self.assertEqual(self.waiting(tick)["order_status"], c1_status)
                    self.assertEqual(self.waiting(tick)["reserved"], ["I2"] if c1_status == "reserved" else [])
                    self.assertEqual(self.waiting(tick, "C2")["order_status"], "unfulfillable")
                    self.assertEqual(self.waiting(tick, "C2")["reserved"], [])

    def test_all_spoiled_events_precede_replacement_and_cooking_on_same_tick(self):
        stock = [item("I10", "bong_sung", 30), item("I2", fresh=30), item("I3", fresh=80)]
        self.run_game("quan", quan(stock=stock, customers=[customer(reserved=["I2"])],
                                    player={"pos": [2, 8]}), ticks=1,
                      inputs=[{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in events(self.rows)], ["spoiled", "spoiled", "cook_started"])
        self.assertEqual([e["data"]["item_id"] for e in events(self.rows, "spoiled")], ["I2", "I10"])
        used = self.one("cook_started", 1)["data"]["items"]
        self.assertEqual([i["id"] for i in used], ["I3"])
        self.assertEqual(self.waiting(1)["reserved"], [])
        self.assertEqual(self.waiting(1)["order_status"], "assigned")

    def test_cooking_consumes_reserved_ids_even_if_another_item_is_fresher(self):
        self.run_game("quan", quan(stock=[item("I1", fresh=50), item("I2", fresh=100)],
                                    customers=[customer(reserved=["I1"])], player={"pos": [2, 8]}),
                      ticks=1, inputs=[{"tick": 0, "interact": True}])
        started = self.one("cook_started", 1)["data"]
        self.assertEqual([i["id"] for i in started["items"]], ["I1"])
        self.fresh(started["items"][0]["fresh"], 50 - QUAN_DECAY)
        self.assertEqual(started["base_price"], self.price("ca_loc_nuong_trui", [50]))
        self.assertEqual([i["id"] for i in self.snap(1)["stock"]], ["I2"])

    def test_price_floors_after_tick_decay_and_uses_each_individual_in_mean(self):
        cases = [
            ("ca_loc_nuong_trui", [item(fresh=80)]),
            ("lau_ca_linh_dien_dien", [item("I10", "ca_linh", 100), item("I2", "ca_linh", 100),
                                       item("I3", "ca_linh", 100), item("I4", "bong_dien_dien", 40)]),
        ]
        for dish, stock in cases:
            with self.subTest(dish=dish):
                c = customer(dish=dish, reserved=[i["id"] for i in stock])
                self.run_game("quan", quan(stock=stock, customers=[c], player={"pos": [2, 8]}),
                              ticks=1, inputs=[{"tick": 0, "interact": True}])
                started = self.one("cook_started", 1)["data"]
                expected = self.price(dish, [v["fresh"] for v in stock])
                self.assertEqual(started["base_price"], expected)
                self.assertEqual(self.stove(1)["dish"]["base_price"], expected)
                self.assertEqual(self.waiting(1)["base_price"], expected)
                self.assertEqual(self.snap(1)["stock"], [])
                expected_order = sorted(stock, key=lambda i: (i["kind"], int(i["id"][1:])))
                self.assertEqual([i["id"] for i in started["items"]], [i["id"] for i in expected_order])

    def test_ready_dish_payload_and_frozen_price_do_not_decay(self):
        payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 47}
        c = customer(order_status="assigned", reserved=[])
        stove = {"id": "B1", "state": "ready", "dish": payload, "ready_ticks": 0, "cook_ticks_left": 0}
        self.run_game("quan", quan(stock=[item("I2", fresh=80)], customers=[c], stoves=[stove]), ticks=60)
        self.assertEqual(self.stove(60)["dish"], payload)
        self.assertEqual(self.stove(60)["ready_ticks"], 60)
        self.fresh(self.snap(60)["stock"][0]["fresh"], 79.75)

    def test_tip_uses_discounted_payload_price_at_patience_boundary(self):
        patience = round(self.t["quan"]["patience_s"] * self.hz)
        threshold = math.ceil(patience * self.t["quan"]["tip_min_patience_ratio"])
        for remaining in (threshold, threshold - 1, 0):
            with self.subTest(remaining_after_decrement=remaining):
                payload = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 47}
                c = customer(order_status="assigned", reserved=[], patience_ticks_left=remaining + 1)
                self.run_game("quan", quan(customers=[c], hand=payload, player={"pos": [9, 2]}), ticks=1,
                              inputs=[{"tick": 0, "interact": True}])
                served = self.one("served", 1)["data"]
                tip = math.floor(47 * self.t["quan"]["tip_rate"]) if remaining >= threshold else 0
                self.assertEqual((served["base_price"], served["tip"], served["patience_ticks_left"]),
                                 (47, tip, remaining))
                self.assertEqual(self.waiting(1)["state"], "eating")
                self.assertEqual(events(self.rows, "customer_left"), [])

    def test_complete_cook_pick_serve_pay_chain_keeps_discounted_price_and_score(self):
        dish = "ca_loc_nuong_trui"
        cook = round(self.menu[dish]["cook_s"] * self.hz)
        eat = round(self.t["quan"]["eat_s"] * self.hz)
        served_tick = cook + 32
        price = self.price(dish, [80])
        tip = math.floor(price * self.t["quan"]["tip_rate"])
        self.run_game("quan", quan(stock=[item(fresh=80)], customers=[customer(reserved=["I1"])],
                                    player={"pos": [2, 8]}, tables=[{"id": "T1", "pos": [2, 6]}]),
                      ticks=served_tick + eat, inputs=[
                          {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                          {"tick": cook, "interact": True},
                          {"tick": cook + 1, "interact": False, "move": [0, -1]},
                          {"tick": cook + 31, "move": [0, 0], "interact": True}])
        self.assertEqual(self.one("cook_started", 1)["data"]["base_price"], price)
        self.one("dish_ready", cook + 1)
        self.one("dish_picked", cook + 1)
        self.assertEqual(self.one("served", served_tick)["data"]["tip"], tip)
        paid = self.one("paid", served_tick + eat)["data"]
        self.assertEqual((paid["base_price"], paid["tip"], paid["amount"], paid["reason"]),
                         (price, tip, price + tip, "finished_eating"))
        final = self.snap(served_tick + eat)
        self.assertEqual((final["money"], final["earned"]), (price + tip, price + tip))
        rep = min(self.t["quan"]["reputation_max"], self.t["quan"]["reputation_initial"] + self.t["quan"]["tip_reputation"])
        self.assertAlmostEqual(final["reputation"], rep, delta=0.01)
        self.assertEqual(final["score"], price + tip + self.t["score"]["reputation_multiplier"] * math.floor(rep))


if __name__ == "__main__":
    unittest.main()
