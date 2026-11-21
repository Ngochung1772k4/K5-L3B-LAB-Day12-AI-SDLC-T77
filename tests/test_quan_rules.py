"""Black-box Quan rules from PRD-0, Test Contract v1.0 C--G.

Fixtures use the existing B1/T1 and maintain every order/payload/reservation
link required by D. With one table, two live orders cannot be constructed
legally: a foreign-order hand payload and simultaneous occupied hand/ready
stove are therefore not used as negative fixtures. Matching service and the
reachable hand/ready preconditions are checked below.

Run with PYTHONDONTWRITEBYTECODE=1; only Workdir contains runtime outputs.
"""

import json
import math
from fractions import Fraction
from pathlib import Path
import unittest
from legacy_rules_view import individual_fixture, quantity_rows

from helpers import (

    ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json,
)


# P4 QA: migrate fixture/quantity assertions at the schema boundary; exact
# item identity/freshness stays covered by the unprojected P3 suites.


def run_cli(*args):
    """Use the shared portable manifest adapter; preserve every application exit."""
    return run_headless(*args)


class QuanRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(Path(ROOT) / "game.contract.json", encoding="utf-8") as source:
            tuning = json.load(source)["tuning"]
        cls.q = tuning["quan"]
        cls.menu = tuning["menu"]
        cls.hz = tuning["tick_hz"]
        cls.multiplier = tuning["score"]["reputation_multiplier"]
        cls.tuning_freshness = tuning["freshness"]
        cls.patience = round(cls.q["patience_s"] * cls.hz)
        cls.eat_ticks = round(cls.q["eat_s"] * cls.hz)
        cls.stove_id = cls.q["stoves"][0]["id"]
        cls.table_id = cls.q["tables"][0]["id"]
        cls.stove_pos = cls.q["stoves"][0]["pos"]
        cls.table_pos = cls.q["tables"][0]["pos"]
        cls.dish_id = "ca_loc_nuong_trui"

    def setUp(self):
        self.work = Workdir()
        self.work.__enter__()
        self.addCleanup(self.work.__exit__, None, None, None)
        self.serial = 0

    def run_case(self, block, ticks, *input_frames, seed=17):
        self.serial += 1
        prefix = str(self.serial)
        fixture = {"stock": {}, "customers": [], "random_customers": False}
        fixture.update(block)
        fixture = individual_fixture(fixture)
        scenario = write_json(self.work.path(prefix + "-scenario.json"), {"quan": fixture})
        inputs = write_json(self.work.path(prefix + "-inputs.json"), frames(*input_frames))
        self.output = Path(self.work.path(prefix + ".jsonl"))
        code, stderr = run_cli(
            "--mode", "quan", "--seed", str(seed), "--ticks", str(ticks),
            "--scenario", scenario, "--inputs", inputs, "--snapshot-every", "1",
            "--out", str(self.output),
        )
        if code != 0:
            raise RuntimeError(
                f"Headless startup/fixture ERROR (exit {code}; 2 means Contract D "
                f"rejection, not a gameplay assertion): {stderr}"
            )
        rows = quantity_rows(read_jsonl(self.output))
        self.assertEqual(rows[-1]["type"], "end")
        self.assertEqual(sum(row["type"] == "end" for row in rows), 1)
        self.s = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(len(self.s), len(snapshots(rows)))
        self.assertEqual(sorted(self.s), list(range(rows[-1]["ticks"] + 1)))
        for tick, snap in self.s.items():
            self.assertEqual((snap["sim_tick"], snap["phase_tick"]), (tick, tick))
            self.assertEqual((snap["mode"], snap["phase"]), ("quan", "quan"))
        for event in events(rows):
            self.assertEqual(event["phase"], "quan")
            self.assertIn(event["tick"], self.s)
            self.assertGreater(event["tick"], 0)
            self.assertLess(rows.index(event), rows.index(self.s[event["tick"]]),
                            "events must precede their tick's snapshot (Contract E)")
        return rows

    def customer(self, dish_id=None, **overrides):
        dish_id = dish_id or self.dish_id
        result = {
            "id": "C1", "table_id": self.table_id, "dish_id": dish_id,
            "order_tick": 0, "state": "waiting", "patience_ticks_left": self.patience,
            "eat_ticks_left": 0, "order_status": "reserved",
            "reserved": dict(self.menu[dish_id]["recipe"]),
        }
        result.update(overrides)
        return result

    def assert_rejected_fixture(self, block):
        """Intentional Contract D contradictions must exit 2 before creating output.

        These are scenario-validation tests, separate from valid gameplay cases.
        Each caller first checks its valid control fixture at tick zero.
        """
        self.serial += 1
        prefix = f"rejected-{self.serial}"
        fixture = {"stock": {}, "customers": [], "random_customers": False}
        fixture.update(block)
        fixture = individual_fixture(fixture)
        scenario = write_json(self.work.path(prefix + "-scenario.json"), {"quan": fixture})
        inputs = write_json(self.work.path(prefix + "-inputs.json"), frames())
        output = self.work.path(prefix + ".jsonl")
        directory = Path(self.work.path("."))
        before = {path.name for path in directory.iterdir()}
        code, stderr = run_cli(
            "--mode", "quan", "--seed", "17", "--ticks", "0", "--scenario", scenario,
            "--inputs", inputs, "--out", output,
        )
        self.assertEqual(code, 2, f"Contract D must reject the contradictory fixture: {stderr}")
        self.assertTrue(stderr.strip(), "a rejected fixture needs a stderr diagnostic")
        self.assertFalse(Path(output).exists(), "validation must precede JSONL creation")
        self.assertEqual({path.name for path in directory.iterdir()}, before)

    def payload(self, dish_id=None):
        dish_id = dish_id or self.dish_id
        return {"order_id": "C1", "dish_id": dish_id, "base_price": self.menu[dish_id]["price"]}

    def newly_cooked_payload(self):
        """TICKET-03 replaces list price: initial fresh 100 decays before cook tick 1."""
        decay = Fraction(str(self.tuning_freshness["quan_decay_per_s"])) / self.hz
        return dict(self.payload(), base_price=math.floor(self.menu[self.dish_id]["price"] * (100 - decay) / 100))

    def assigned_case(self, location="hand", patience=None, **overrides):
        customer = self.customer(order_status="assigned", reserved={})
        if patience is not None:
            customer["patience_ticks_left"] = patience
        block = {"customers": [customer]}
        if location == "hand":
            block.update(player={"pos": list(self.table_pos)}, hand=self.payload())
        else:
            block.update(player={"pos": list(self.stove_pos)}, stoves=[{
                "id": self.stove_id, "state": location, "dish": self.payload(),
                "cook_ticks_left": 2 if location == "cooking" else 0, "ready_ticks": 0,
            }])
        block.update(overrides)
        return block

    def eating_case(self, remaining, tip=0, **overrides):
        customer = self.customer(
            state="eating", order_status="served", reserved={}, eat_ticks_left=remaining,
            base_price=self.menu[self.dish_id]["price"], tip=tip,
        )
        result = {"customers": [customer]}
        result.update(overrides)
        return result

    def stove(self, tick):
        return next(s for s in self.s[tick]["stoves"] if s["id"] == self.stove_id)

    def table(self, tick):
        return next(t for t in self.s[tick]["tables"] if t["id"] == self.table_id)

    def customer_at(self, tick):
        customers = self.s[tick]["customers"]
        self.assertEqual(len(customers), 1, f"expected one seated customer at tick {tick}: {customers}")
        return customers[0]

    def one_event(self, rows, name, tick, data):
        found = events(rows, name)
        self.assertEqual(len(found), 1, f"{name}: {found}")
        self.assertEqual(found[0]["tick"], tick)
        self.assertEqual(found[0]["data"], data)
        return found[0]

    def clamp_reputation(self, reputation):
        return max(self.q["reputation_min"], min(self.q["reputation_max"], reputation))

    def assert_reputation(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=0.01)

    def test_first_customer_arrives_at_configured_tick_with_full_patience(self):
        first = self.q["first_customer_tick"]
        recipe = self.menu[self.dish_id]["recipe"]
        rows = self.run_case({"random_customers": True, "stock": recipe}, first + 1)
        self.assertEqual(first, 120, "Contract A fixes first_customer_tick at 120")
        self.one_event(rows, "customer_arrived", first,
                       {"order_id": "C1", "table_id": self.table_id, "dish_id": self.dish_id})
        for tick in range(first):
            self.assertEqual(self.s[tick]["customers"], [])
        customer = self.customer_at(first)
        self.assertEqual(customer["order_tick"], first)
        self.assertEqual(customer["patience_ticks_left"], self.patience)
        self.assertEqual(customer["order_status"], "reserved")
        self.assertEqual(self.customer_at(first + 1)["patience_ticks_left"], self.patience - 1)
        self.assertEqual(self.table(first)["customer_id"], "C1")

    def test_customer_attempts_follow_exact_interval_even_in_shortened_shift(self):
        first = self.q["first_customer_tick"]
        interval = round(self.q["customer_interval_s"] * self.hz)
        last = first + 2 * interval
        rows = self.run_case({"random_customers": True, "time_left_ticks": last + 2}, last + 1)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")],
                         [(first, {}), (first + interval, {}), (last, {})])
        self.assertEqual(events(rows, "customer_arrived"), [])

    def test_no_dish_when_each_recipe_lacks_at_least_one_ingredient(self):
        # ca_loc absent; bong_sung one short; hotpot lacks its flower.
        stock = {"bong_sung": self.menu["goi_bong_sung"]["recipe"]["bong_sung"] - 1,
                 "ca_linh": self.menu["lau_ca_linh_dien_dien"]["recipe"]["ca_linh"]}
        first = self.q["first_customer_tick"]
        rows = self.run_case({"random_customers": True, "stock": stock}, first)
        self.one_event(rows, "no_dish", first, {})
        self.assertEqual(events(rows, "customer_arrived"), [])
        self.assertEqual(self.s[first]["customers"], [])
        self.assertEqual(self.s[first]["stock"], stock)
        self.assertIsNone(self.table(first)["customer_id"])

    def test_customer_selects_only_recipes_affordable_from_available_stock(self):
        first = self.q["first_customer_tick"]
        # Force each recipe independently, then allow a subset without guessing RNG internals.
        stocks = [dict(dish["recipe"]) for dish in self.menu.values()]
        subset = {}
        for ident in ("ca_loc_nuong_trui", "goi_bong_sung"):
            for kind, amount in self.menu[ident]["recipe"].items():
                subset[kind] = subset.get(kind, 0) + amount
        stocks.append(subset)
        for stock in stocks:
            for seed in (7, 42):
                with self.subTest(stock=stock, seed=seed):
                    eligible = {ident for ident, dish in self.menu.items()
                                if all(stock.get(kind, 0) >= amount
                                       for kind, amount in dish["recipe"].items())}
                    rows = self.run_case({"stock": stock, "random_customers": True}, first, seed=seed)
                    arrived = events(rows, "customer_arrived")
                    self.assertEqual(len(arrived), 1)
                    chosen = arrived[0]["data"]["dish_id"]
                    self.assertIn(chosen, eligible)
                    self.assertEqual(self.customer_at(first)["reserved"], self.menu[chosen]["recipe"])
                    self.assertEqual(self.s[first]["stock"], stock)

    def test_order_reserves_at_arrival_and_consumes_only_when_cooking_starts(self):
        first = self.q["first_customer_tick"]
        recipe = self.menu[self.dish_id]["recipe"]
        rows = self.run_case({"random_customers": True, "stock": recipe,
                              "player": {"pos": list(self.stove_pos)}}, first + 2,
                             {"tick": first - 1, "interact": True},
                             {"tick": first, "interact": False},
                             {"tick": first + 1, "interact": True})
        self.assertEqual(self.customer_at(first)["reserved"], recipe)
        self.assertEqual(self.s[first]["stock"], recipe)
        self.assertEqual(self.s[first + 1]["stock"], recipe)
        started = events(rows, "cook_started")
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0]["tick"], first + 2, "new customers cannot interact on their arrival step")
        self.assertEqual(self.s[first + 2]["stock"], {})
        self.assertEqual(self.customer_at(first + 2)["reserved"], {})
        self.assertEqual(self.customer_at(first + 2)["order_status"], "assigned")

    def test_omitted_reservation_is_inferred_from_recipe_at_tick_zero(self):
        customer = self.customer()
        del customer["reserved"]
        recipe = self.menu[self.dish_id]["recipe"]
        self.run_case({"customers": [customer], "stock": recipe}, 0)
        self.assertEqual(self.customer_at(0)["reserved"], recipe)
        self.assertEqual(self.s[0]["stock"], recipe)
        self.assertEqual(self.table(0)["customer_id"], "C1")

    def test_minimal_customer_fixture_receives_contract_defaults_at_tick_zero(self):
        customer = {"id": "C1", "table_id": self.table_id, "dish_id": self.dish_id}
        recipe = self.menu[self.dish_id]["recipe"]
        self.run_case({"customers": [customer], "stock": recipe}, 0)
        actual = self.customer_at(0)
        for key, expected in {"state": "waiting", "order_tick": 0,
                              "patience_ticks_left": self.patience, "order_status": "reserved",
                              "reserved": recipe}.items():
            self.assertIn(key, actual, f"Contract D fixture default missing: {key}")
            self.assertEqual(actual[key], expected)

    def test_snapshot_preserves_fixture_player_position_and_velocity(self):
        pos, vel = list(self.q["start_pos"]), [self.q["walk_speed"] / 2, 0]
        self.run_case({"player": {"pos": pos, "vel": vel}}, 0)
        self.assertEqual(self.s[0]["player"]["pos"], pos)
        self.assertIn("vel", self.s[0]["player"], "Contract D/E requires player.vel in Quan snapshots")
        self.assertEqual(self.s[0]["player"]["vel"], vel)

    def test_scenario_rejects_reservation_beyond_physical_stock_before_output(self):
        for dish_id, dish in self.menu.items():
            with self.subTest(dish_id=dish_id):
                stock = dict(dish["recipe"])
                customer = self.customer(dish_id)
                self.run_case({"stock": stock, "customers": [customer]}, 0)
                kind = sorted(stock)[0]
                stock[kind] -= 1
                self.assert_rejected_fixture({"stock": stock, "customers": [customer]})

    def test_scenario_rejects_reservation_different_from_order_recipe(self):
        stock = dict(self.menu[self.dish_id]["recipe"])
        stock.update(self.menu["goi_bong_sung"]["recipe"])
        self.run_case({"stock": stock, "customers": [self.customer()]}, 0)
        customer = self.customer(reserved=dict(self.menu["goi_bong_sung"]["recipe"]))
        self.assert_rejected_fixture({"stock": stock, "customers": [customer]})

    def test_scenario_rejects_assigned_order_with_missing_or_duplicate_payload(self):
        self.run_case(self.assigned_case("hand"), 0)
        with self.subTest(contradiction="missing payload"):
            self.assert_rejected_fixture(self.assigned_case("hand", hand=None))
        with self.subTest(contradiction="same order in hand and stove"):
            self.assert_rejected_fixture(self.assigned_case("ready", hand=self.payload()))

    def test_scenario_rejects_payload_for_unknown_order_or_wrong_dish(self):
        self.run_case(self.assigned_case("hand"), 0)
        with self.subTest(contradiction="unknown order"):
            payload = dict(self.payload(), order_id="C999")
            self.assert_rejected_fixture(self.assigned_case("hand", hand=payload))
        with self.subTest(contradiction="dish differs from its live order"):
            self.assert_rejected_fixture(self.assigned_case("hand", hand=self.payload("goi_bong_sung")))

    def test_scenario_rejects_eating_without_payment_fields_or_positive_timer(self):
        self.run_case(self.eating_case(1), 0)
        for field in ("base_price", "tip", "eat_ticks_left"):
            with self.subTest(missing_field=field):
                block = self.eating_case(1)
                del block["customers"][0][field]
                self.assert_rejected_fixture(block)

    def test_scenario_rejects_contradictory_stove_state_and_timer(self):
        self.run_case(self.assigned_case("cooking"), 0)
        for state, timer in (("cooking", 0), ("ready", 1), ("idle", 0)):
            with self.subTest(state=state, cook_ticks_left=timer):
                block = self.assigned_case("ready")
                block["stoves"][0].update(state=state, cook_ticks_left=timer)
                self.assert_rejected_fixture(block)

    def test_reservations_never_exceed_physical_stock_and_full_table_skips_arrivals(self):
        first = self.q["first_customer_tick"]
        interval = round(self.q["customer_interval_s"] * self.hz)
        recipe = self.menu[self.dish_id]["recipe"]
        rows = self.run_case({"random_customers": True, "stock": recipe}, first + interval)
        self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [first])
        # v1.1 có 4 bàn: lượt sau tìm được bàn trống nhưng kho đã giữ hết -> no_dish (P1 chỉ có T1 -> bỏ lượt)
        self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [first + interval])
        for tick in range(first, first + interval + 1):
            snap = self.s[tick]
            self.assertEqual(len(snap["customers"]), 1)
            self.assertEqual(snap["customers"][0]["reserved"], recipe)
            self.assertEqual(snap["stock"], recipe)
            for kind in recipe:
                reserved = sum(c["reserved"].get(kind, 0) for c in snap["customers"])
                self.assertLessEqual(reserved, snap["stock"].get(kind, 0))

    def test_patience_decreases_once_on_each_waiting_tick(self):
        self.run_case({"customers": [self.customer(patience_ticks_left=5)],
                       "stock": self.menu[self.dish_id]["recipe"]}, 3)
        for tick, snap in self.s.items():
            self.assertEqual(snap["customers"][0]["patience_ticks_left"], 5 - tick)
            self.assertEqual(snap["customers"][0]["state"], "waiting")

    def test_patience_expiry_releases_reservation_and_applies_clamped_reputation(self):
        for initial in (self.q["reputation_initial"], self.q["reputation_min"]):
            with self.subTest(initial=initial):
                recipe = self.menu[self.dish_id]["recipe"]
                rows = self.run_case({"stock": recipe, "reputation": initial,
                                      "customers": [self.customer(patience_ticks_left=2)]}, 2)
                expected_rep = self.clamp_reputation(initial + self.q["left_reputation_delta"])
                left = events(rows, "customer_left")
                self.assertEqual(len(left), 1)
                self.assertEqual((left[0]["tick"], left[0]["data"]["order_id"],
                                  left[0]["data"]["table_id"], left[0]["data"]["reason"]),
                                 (2, "C1", self.table_id, "patience"))
                self.assert_reputation(left[0]["data"]["reputation"], expected_rep)
                self.assert_reputation(self.s[2]["reputation"], expected_rep)
                self.assertEqual(self.customer_at(1)["reserved"], recipe)
                self.assertEqual(self.s[2]["stock"], recipe)
                self.assertEqual(self.s[2]["customers"], [])
                self.assertIsNone(self.table(2)["customer_id"])
                self.assertEqual(events(rows, "paid"), [])

    def test_released_raw_reservation_is_available_for_next_customer(self):
        first = self.q["first_customer_tick"]
        recipe = self.menu[self.dish_id]["recipe"]
        rows = self.run_case({"stock": recipe, "random_customers": True,
                              "customers": [self.customer(patience_ticks_left=first)]}, first)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "customer_arrived"])
        self.assertEqual([e["tick"] for e in events(rows)], [first, first])
        self.assertEqual(events(rows, "customer_left")[0]["data"]["order_id"], "C1")
        self.assertEqual(events(rows, "customer_arrived")[0]["data"],
                         {"order_id": "C2", "table_id": self.table_id, "dish_id": self.dish_id})
        customer = self.customer_at(first)
        self.assertEqual((customer["id"], customer["order_tick"]), ("C2", first))
        self.assertEqual(customer["reserved"], recipe)
        self.assertEqual(self.s[first]["stock"], recipe)

    def test_expired_assigned_order_discards_cooking_ready_or_carried_dish_without_refund(self):
        for location in ("cooking", "ready", "hand"):
            with self.subTest(location=location):
                rows = self.run_case(self.assigned_case(location, patience=1), 1)
                self.assertEqual(len(events(rows, "customer_left")), 1)
                self.assertEqual(events(rows, "customer_left")[0]["data"]["reason"], "patience")
                self.assertEqual(self.s[1]["customers"], [])
                self.assertIsNone(self.s[1]["hand"])
                self.assertEqual(self.stove(1)["state"], "idle")
                self.assertIsNone(self.stove(1)["dish"])
                self.assertEqual(self.stove(1)["cook_ticks_left"], 0)
                self.assertEqual(self.stove(1)["ready_ticks"], 0)
                self.assertEqual(self.s[1]["stock"], {})

    def test_unfulfillable_waiting_order_cannot_start_cooking(self):
        rows = self.run_case({"customers": [self.customer(order_status="unfulfillable", reserved={})],
                              "player": {"pos": list(self.stove_pos)}},
                             1, {"tick": 0, "interact": True})
        self.assertEqual(events(rows, "cook_started"), [])
        self.assertEqual(self.stove(1)["state"], "idle")
        self.assertEqual(self.s[1]["stock"], {})
        self.assertEqual(self.customer_at(1)["order_status"], "unfulfillable")

    def test_stove_idle_cooking_ready_transitions_and_countdowns_are_exact(self):
        recipe = self.menu[self.dish_id]["recipe"]
        cook = round(self.menu[self.dish_id]["cook_s"] * self.hz)
        rows = self.run_case({"stock": recipe, "customers": [self.customer()],
                              "player": {"pos": list(self.stove_pos)}}, cook + 2,
                             {"tick": 0, "interact": True}, {"tick": 1, "interact": False})
        items = [kind for kind in sorted(recipe) for _ in range(recipe[kind])]
        self.one_event(rows, "cook_started", 1,
                       {"stove_id": self.stove_id, **self.newly_cooked_payload(), "items": items})
        self.assertEqual(self.stove(0)["state"], "idle")
        for tick in range(1, cook + 1):
            self.assertEqual(self.stove(tick)["state"], "cooking")
            self.assertEqual(self.stove(tick)["cook_ticks_left"], cook - tick + 1)
            self.assertEqual(self.stove(tick)["dish"], self.newly_cooked_payload())
        self.one_event(rows, "dish_ready", cook + 1,
                       {"stove_id": self.stove_id, "order_id": "C1", "dish_id": self.dish_id})
        self.assertEqual(self.stove(cook + 1)["state"], "ready")
        self.assertEqual(self.stove(cook + 1)["cook_ticks_left"], 0)
        self.assertEqual(self.stove(cook + 1)["ready_ticks"], 0)
        self.assertEqual(self.stove(cook + 2)["ready_ticks"], 1)
        self.assertEqual(self.s[1]["stock"], {})
        self.assertEqual(self.customer_at(1)["reserved"], {})
        self.assertEqual(self.customer_at(1)["order_status"], "assigned")

    def test_held_interact_does_not_pick_ready_dish_without_a_new_edge(self):
        cook = round(self.menu[self.dish_id]["cook_s"] * self.hz)
        rows = self.run_case({"stock": self.menu[self.dish_id]["recipe"],
                              "customers": [self.customer()], "player": {"pos": list(self.stove_pos)}},
                             cook + 4, {"tick": 0, "interact": True},
                             {"tick": 1, "interact": True},
                             {"tick": cook + 2, "interact": False},
                             {"tick": cook + 3, "interact": True})
        self.assertEqual([e["tick"] for e in events(rows, "cook_started")], [1])
        self.assertEqual([e["tick"] for e in events(rows, "dish_picked")], [cook + 4])
        self.assertIsNone(self.s[cook + 3]["hand"])
        self.assertEqual(self.stove(cook + 3)["state"], "ready")
        self.assertEqual(self.s[cook + 4]["hand"], self.newly_cooked_payload())
        self.assertEqual(self.stove(cook + 4)["state"], "idle")

    def test_pickup_requires_ready_and_empty_hand_then_resets_stove(self):
        rows = self.run_case(self.assigned_case("cooking"), 3,
                             {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                             {"tick": 2, "interact": True})
        self.assertIsNone(self.s[1]["hand"])
        self.assertEqual(self.stove(1)["state"], "cooking")
        self.assertEqual(self.stove(1)["cook_ticks_left"], 1)
        self.assertIsNone(self.s[2]["hand"])
        self.assertEqual(self.stove(2)["state"], "ready")
        self.one_event(rows, "dish_picked", 3,
                       {"stove_id": self.stove_id, "order_id": "C1", "dish_id": self.dish_id})
        self.assertEqual(self.s[3]["hand"], self.payload())
        self.assertEqual(self.stove(3)["state"], "idle")
        self.assertIsNone(self.stove(3)["dish"])
        self.assertEqual((self.stove(3)["cook_ticks_left"], self.stove(3)["ready_ticks"]), (0, 0))

    def test_ready_transition_allows_pickup_in_same_tick_before_interaction(self):
        block = self.assigned_case("cooking")
        block["stoves"][0]["cook_ticks_left"] = 1
        rows = self.run_case(block, 1, {"tick": 0, "interact": True})
        self.assertEqual([(e["name"], e["tick"]) for e in events(rows)],
                         [("dish_ready", 1), ("dish_picked", 1)])
        self.assertEqual(self.s[1]["hand"], self.payload())
        self.assertEqual(self.stove(1)["state"], "idle")

    def test_occupied_hand_remains_one_payload_when_interacting_with_idle_stove(self):
        rows = self.run_case(self.assigned_case("hand", player={"pos": list(self.stove_pos)}),
                             1, {"tick": 0, "interact": True})
        self.assertEqual(self.q["carry_limit"], 1)
        self.assertEqual(self.s[1]["hand"], self.payload())
        self.assertEqual(self.stove(1)["state"], "idle")
        self.assertEqual(events(rows, "dish_picked") + events(rows, "cook_started"), [])

    def test_one_interact_picks_at_stove_before_colocated_table_without_serving(self):
        pos = list(self.stove_pos)
        block = self.assigned_case("ready", tables=[{"id": self.table_id, "pos": pos}])
        rows = self.run_case(block, 1, {"tick": 0, "interact": True})
        self.one_event(rows, "dish_picked", 1,
                       {"stove_id": self.stove_id, "order_id": "C1", "dish_id": self.dish_id})
        self.assertEqual(events(rows, "served"), [])
        self.assertEqual(self.s[1]["hand"], self.payload())
        self.assertEqual(self.customer_at(1)["state"], "waiting")

    def test_selected_idle_stove_does_not_fall_back_to_colocated_serviceable_table(self):
        pos = list(self.stove_pos)
        rows = self.run_case(self.assigned_case(
            "hand", player={"pos": pos}, tables=[{"id": self.table_id, "pos": pos}]),
            1, {"tick": 0, "interact": True})
        self.assertEqual(events(rows), [])
        self.assertEqual(self.s[1]["hand"], self.payload())
        self.assertEqual(self.customer_at(1)["state"], "waiting")

    def test_interaction_radius_is_inclusive_and_rejects_just_outside(self):
        radius = self.q["interact_radius"]
        for distance, allowed in ((radius, True), (radius + 0.001, False)):
            with self.subTest(distance=distance):
                pos = [self.stove_pos[0] + distance, self.stove_pos[1]]
                rows = self.run_case(self.assigned_case("ready", player={"pos": pos}),
                                     1, {"tick": 0, "interact": True})
                self.assertEqual(len(events(rows, "dish_picked")), int(allowed))
                self.assertEqual(self.s[1]["hand"], self.payload() if allowed else None)
                self.assertEqual(self.stove(1)["state"], "idle" if allowed else "ready")

    def test_matching_order_is_served_then_paid_only_after_full_eating_duration(self):
        price = self.menu[self.dish_id]["price"]
        tip = math.floor(price * self.q["tip_rate"])
        rows = self.run_case(self.assigned_case("hand"), self.eat_ticks + 1,
                             {"tick": 0, "interact": True})
        self.one_event(rows, "served", 1,
                       {"order_id": "C1", "table_id": self.table_id, "dish_id": self.dish_id,
                        "patience_ticks_left": self.patience - 1, "base_price": price, "tip": tip})
        customer = self.customer_at(1)
        self.assertEqual((customer["state"], customer["order_status"]), ("eating", "served"))
        self.assertEqual(customer["reserved"], {})
        self.assertEqual((customer["base_price"], customer["tip"]), (price, tip))
        self.assertIsNone(self.s[1]["hand"])
        for tick in range(1, self.eat_ticks + 1):
            self.assertEqual(self.customer_at(tick)["eat_ticks_left"], self.eat_ticks - tick + 1)
            self.assertEqual((self.s[tick]["money"], self.s[tick]["earned"]), (0, 0))
            self.assert_reputation(self.s[tick]["reputation"], self.q["reputation_initial"])
        self.one_event(rows, "paid", self.eat_ticks + 1,
                       {"order_id": "C1", "table_id": self.table_id, "base_price": price, "tip": tip,
                        "amount": price + tip, "reason": "finished_eating"})
        final = self.s[self.eat_ticks + 1]
        self.assertEqual((final["money"], final["earned"]), (price + tip, price + tip))
        self.assert_reputation(final["reputation"], self.clamp_reputation(
            self.q["reputation_initial"] + self.q["tip_reputation"]))
        self.assertEqual(final["customers"], [])
        self.assertIsNone(self.table(self.eat_ticks + 1)["customer_id"])
        self.assertEqual(events(rows, "customer_left"), [])

    def test_tip_threshold_uses_patience_after_decrement_and_floor_price(self):
        threshold = math.ceil(self.patience * self.q["tip_min_patience_ratio"])
        price = self.menu[self.dish_id]["price"]
        for remaining in (threshold, threshold - 1):
            with self.subTest(remaining_at_service=remaining):
                rows = self.run_case(self.assigned_case("hand", patience=remaining + 1),
                                     1, {"tick": 0, "interact": True})
                tip = math.floor(price * self.q["tip_rate"]) if remaining >= threshold else 0
                self.one_event(rows, "served", 1,
                               {"order_id": "C1", "table_id": self.table_id, "dish_id": self.dish_id,
                                "patience_ticks_left": remaining, "base_price": price, "tip": tip})
                self.assertEqual(self.customer_at(1)["tip"], tip)
                self.assertEqual(self.s[1]["money"], 0)

    def test_service_on_zero_patience_deadline_succeeds_before_departure(self):
        rows = self.run_case(self.assigned_case("hand", patience=1),
                             1, {"tick": 0, "interact": True})
        self.one_event(rows, "served", 1,
                       {"order_id": "C1", "table_id": self.table_id, "dish_id": self.dish_id,
                        "patience_ticks_left": 0, "base_price": self.menu[self.dish_id]["price"], "tip": 0})
        self.assertEqual(events(rows, "customer_left"), [])
        self.assertEqual(self.customer_at(1)["state"], "eating")
        self.assertEqual(self.customer_at(1)["eat_ticks_left"], self.eat_ticks)

    def test_payment_tip_reputation_is_clamped_and_no_tip_leaves_reputation_unchanged(self):
        price = self.menu[self.dish_id]["price"]
        for tip in (0, math.floor(price * self.q["tip_rate"])):
            with self.subTest(tip=tip):
                initial = self.q["reputation_max"] - self.q["tip_reputation"] / 2
                rows = self.run_case(self.eating_case(1, tip, reputation=initial), 1)
                self.one_event(rows, "paid", 1,
                               {"order_id": "C1", "table_id": self.table_id, "base_price": price,
                                "tip": tip, "amount": price + tip, "reason": "finished_eating"})
                expected = self.clamp_reputation(initial + (self.q["tip_reputation"] if tip else 0))
                self.assert_reputation(self.s[1]["reputation"], expected)
                self.assertEqual(self.s[1]["earned"], price + tip)
                self.assertEqual(self.s[1]["money"], price + tip)

    def test_closing_waiter_releases_raw_reservation_without_patience_penalty(self):
        recipe = self.menu[self.dish_id]["recipe"]
        initial = self.q["reputation_initial"]
        rows = self.run_case({"stock": recipe, "customers": [self.customer(patience_ticks_left=1)],
                              "time_left_ticks": 1}, 10)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])
        self.one_event(rows, "customer_left", 1,
                       {"order_id": "C1", "table_id": self.table_id, "reason": "closing", "reputation": initial})
        self.one_event(rows, "quan_end", 1,
                       {"reason": "time", "money": 0, "earned": 0, "shift_earned": 0, "reputation": initial})
        self.assertEqual(self.s[1]["stock"], recipe)
        self.assertEqual(self.s[1]["customers"], [])
        self.assertIsNone(self.table(1)["customer_id"])
        self.assertEqual((rows[-1]["ticks"], rows[-1]["reason"], rows[-1]["state"]), (1, "time", "finished"))

    def test_closing_discards_assigned_dishes_in_stove_or_hand_without_refunding(self):
        for location in ("cooking", "ready", "hand"):
            with self.subTest(location=location):
                rows = self.run_case(self.assigned_case(location, time_left_ticks=1), 1)
                self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "quan_end"])
                self.assertEqual(events(rows, "customer_left")[0]["data"]["reason"], "closing")
                self.assertEqual(self.s[1]["customers"], [])
                self.assertIsNone(self.s[1]["hand"])
                self.assertEqual(self.stove(1)["state"], "idle")
                self.assertIsNone(self.stove(1)["dish"])
                self.assertEqual((self.stove(1)["cook_ticks_left"], self.stove(1)["ready_ticks"]), (0, 0))
                self.assertEqual(self.s[1]["stock"], {})
                self.assert_reputation(self.s[1]["reputation"], self.q["reputation_initial"])

    def test_closing_pays_eaters_and_preserves_finished_eating_reason_on_exact_deadline(self):
        price = self.menu[self.dish_id]["price"]
        tip = math.floor(price * self.q["tip_rate"])
        for remaining, reason in ((1, "finished_eating"), (2, "closing")):
            with self.subTest(remaining=remaining):
                rows = self.run_case(self.eating_case(remaining, tip, time_left_ticks=1), 10)
                self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])
                self.one_event(rows, "paid", 1,
                               {"order_id": "C1", "table_id": self.table_id, "base_price": price,
                                "tip": tip, "amount": price + tip, "reason": reason})
                expected_rep = self.clamp_reputation(self.q["reputation_initial"] + self.q["tip_reputation"])
                end = events(rows, "quan_end")[0]
                self.assertEqual(end["tick"], 1)
                self.assertEqual((end["data"]["money"], end["data"]["earned"], end["data"]["shift_earned"]),
                                 (price + tip, price + tip, price + tip))
                self.assert_reputation(end["data"]["reputation"], expected_rep)
                self.assertEqual(self.s[1]["customers"], [])
                self.assertIsNone(self.table(1)["customer_id"])

    def test_service_on_closing_tick_is_paid_immediately_before_quan_end(self):
        price = self.menu[self.dish_id]["price"]
        rows = self.run_case(self.assigned_case("hand", patience=1, time_left_ticks=1),
                             10, {"tick": 0, "interact": True})
        self.assertEqual([(e["name"], e["tick"]) for e in events(rows)],
                         [("served", 1), ("paid", 1), ("quan_end", 1)])
        self.one_event(rows, "served", 1,
                       {"order_id": "C1", "table_id": self.table_id, "dish_id": self.dish_id,
                        "patience_ticks_left": 0, "base_price": price, "tip": 0})
        self.one_event(rows, "paid", 1,
                       {"order_id": "C1", "table_id": self.table_id, "base_price": price,
                        "tip": 0, "amount": price, "reason": "closing"})
        self.assertEqual(events(rows, "customer_left"), [])
        self.assertEqual(self.s[1]["customers"], [])
        self.assertIsNone(self.s[1]["hand"])
        self.assertEqual((rows[-1]["money"], rows[-1]["earned"], rows[-1]["reason"]), (price, price, "time"))

    def test_closing_suppresses_customer_attempt_even_when_schedule_is_due(self):
        first = self.q["first_customer_tick"]
        rows = self.run_case({"random_customers": True, "time_left_ticks": first}, first + 1)
        self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])
        self.assertEqual([e["name"] for e in events(rows)], ["quan_end"])
        self.assertEqual(events(rows, "quan_end")[0]["tick"], first)
        self.assertEqual(rows[-1]["ticks"], first)

    def test_score_uses_earned_plus_multiplier_times_floor_reputation(self):
        price = self.menu[self.dish_id]["price"]
        tip = math.floor(price * self.q["tip_rate"])
        initial = self.q["reputation_initial"] + 0.9
        rows = self.run_case(self.eating_case(1, tip, reputation=initial, time_left_ticks=2), 2)
        expected_rep = self.clamp_reputation(initial + self.q["tip_reputation"])
        expected_earned = price + tip
        self.assertEqual(self.s[0]["score"], self.multiplier * math.floor(initial))
        for tick in (1, 2):
            self.assertEqual(self.s[tick]["earned"], expected_earned)
            self.assert_reputation(self.s[tick]["reputation"], expected_rep)
            self.assertEqual(self.s[tick]["score"], expected_earned + self.multiplier * math.floor(expected_rep))
        self.assertEqual(rows[-1]["score"], expected_earned + self.multiplier * math.floor(expected_rep))

    def test_seeded_order_and_cooking_fixture_produce_identical_jsonl_bytes(self):
        first = self.q["first_customer_tick"]
        stock = {}
        for dish in self.menu.values():
            for kind, amount in dish["recipe"].items():
                stock[kind] = stock.get(kind, 0) + amount
        block = {"stock": stock, "random_customers": True, "time_left_ticks": first + 3,
                 "player": {"pos": list(self.stove_pos)}}
        results = []
        for _ in range(2):
            rows = self.run_case(block, first + 5, {"tick": first, "interact": True}, seed=42)
            self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [first])
            self.assertEqual([e["tick"] for e in events(rows, "cook_started")], [first + 1])
            self.assertEqual([e["name"] for e in events(rows)][-2:], ["customer_left", "quan_end"])
            results.append(self.output.read_bytes())
        self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
