"""Test hộp đen luật Quán (PRD-0 mục F) — AC-P1-13..18. Chạy qua headless_cmd như smoke test."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

DISH = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}


def run_quan(w, scenario, ticks, inp=None):
    args = ["--mode", "quan", "--seed", "3", "--ticks", str(ticks), "--snapshot-every", "1",
            "--scenario", write_json(w.path("sc.json"), {"quan": scenario}), "--out", w.path("o.jsonl")]
    if inp is not None:
        args += ["--inputs", write_json(w.path("in.json"), inp)]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path("o.jsonl"))


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


def menu():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["menu"]


class Customers(unittest.TestCase):
    def test_ac13_first_customer_at_120_reserves_recipe(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 5, "bong_sung": 6}}, 1100)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [120])  # 1020: bàn T1 còn khách -> bỏ lượt
            d = arr[0]["data"]
            self.assertEqual(set(d), {"order_id", "table_id", "dish_id"})
            self.assertEqual(d["table_id"], "T1")
            c = snap_at(rows, 120)["customers"][0]
            self.assertEqual(c["reserved"], menu()[d["dish_id"]]["recipe"])
            self.assertEqual((c["order_tick"], c["state"], c["order_status"]), (120, "waiting", "reserved"))
            self.assertEqual(snap_at(rows, 121)["customers"][0]["patience_ticks_left"], 3599)
            self.assertEqual(snap_at(rows, 120)["stock"], {"bong_sung": 6, "ca_loc": 5})  # giữ chỗ không trừ kho

    def test_ac14_no_dish_when_stock_empty(self):
        with Workdir() as w:
            rows = run_quan(w, {}, 130)
            nd = events(rows, "no_dish")
            self.assertEqual([(e["tick"], e["data"]) for e in nd], [(120, {})])
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(snap_at(rows, 130)["customers"], [])

    def test_ac15_patience_out_left_reputation_and_stock_kept(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}}, 3725)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 120 + 3600)
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience",
                                               "reputation": 2.5})
            self.assertEqual(snap_at(rows, 3725)["stock"], {"ca_loc": 1})  # nhả giữ chỗ, kho vật lý giữ nguyên


class Kitchen(unittest.TestCase):
    def test_ac16_cook_ready_pick(self):
        sc = {"player": {"pos": [2, 8]}, "stock": {"bong_sung": 2}, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                     {"tick": 300, "interact": True})
        with Workdir() as w:
            rows = run_quan(w, sc, 305, inp)
            cs = events(rows, "cook_started")
            self.assertEqual([(e["tick"], e["data"]) for e in cs],
                             [(1, {"stove_id": "B1", "order_id": "C1", "dish_id": "goi_bong_sung",
                                   "items": ["bong_sung", "bong_sung"], "base_price": 40})])
            self.assertEqual(snap_at(rows, 1)["stock"], {})
            self.assertEqual(snap_at(rows, 1)["customers"][0]["order_status"], "assigned")
            ready = events(rows, "dish_ready")
            self.assertEqual([(e["tick"], e["data"]) for e in ready],
                             [(241, {"stove_id": "B1", "order_id": "C1", "dish_id": "goi_bong_sung"})])
            self.assertEqual(snap_at(rows, 241)["stoves"][0]["ready_ticks"], 0)
            self.assertEqual(snap_at(rows, 250)["stoves"][0]["ready_ticks"], 9)
            picked = events(rows, "dish_picked")
            self.assertEqual([e["tick"] for e in picked], [301])
            self.assertEqual(snap_at(rows, 301)["hand"], DISH)
            self.assertEqual(snap_at(rows, 301)["stoves"][0]["state"], "idle")

    def _serve(self, patience, ticks=605):
        sc = {"player": {"pos": [9, 2]}, "random_customers": False, "hand": DISH,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                             "patience_ticks_left": patience}]}
        with Workdir() as w:
            return run_quan(w, sc, ticks, frames({"tick": 0, "interact": True}))

    def test_ac16_ac17_serve_tip_pay(self):
        rows = self._serve(3600)
        self.assertEqual(events(rows, "served")[0]["data"],
                         {"order_id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                          "patience_ticks_left": 3599, "base_price": 40, "tip": 8})
        paid = events(rows, "paid")
        self.assertEqual([(e["tick"], e["data"]) for e in paid],
                         [(601, {"order_id": "C1", "table_id": "T1", "base_price": 40, "tip": 8, "amount": 48,
                                 "reason": "finished_eating"})])
        s = snap_at(rows, 601)
        self.assertEqual((s["money"], s["earned"]), (48, 48))
        self.assertAlmostEqual(s["reputation"], 3.2, places=6)
        self.assertEqual(s["score"], 48 + 300)
        self.assertEqual(s["customers"], [])

    def test_ac17_low_patience_no_tip(self):
        rows = self._serve(1000)
        self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)
        s = snap_at(rows, 601)
        self.assertEqual(s["money"], 40)
        self.assertEqual(s["reputation"], 3.0)

    def test_serve_on_tick_patience_hits_zero_is_valid(self):
        rows = self._serve(1, ticks=3)
        self.assertEqual(len(events(rows, "served")), 1)
        self.assertEqual(events(rows, "customer_left"), [])

    def test_leaving_customer_discards_dish_in_hand(self):
        sc = {"random_customers": False, "hand": DISH,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                             "patience_ticks_left": 1}]}
        with Workdir() as w:
            rows = run_quan(w, sc, 2)
            self.assertEqual(events(rows, "customer_left")[0]["tick"], 1)
            self.assertIsNone(snap_at(rows, 1)["hand"])


class Closing(unittest.TestCase):
    def test_ac18_eating_customer_pays_closing_then_quan_end(self):
        sc = {"time_left_ticks": 10, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                             "order_status": "served", "eat_ticks_left": 600, "base_price": 40, "tip": 8}]}
        with Workdir() as w:
            rows = run_quan(w, sc, 50)
            names = [e["name"] for e in events(rows) if e["tick"] == 10]
            self.assertEqual(names, ["paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            end = events(rows, "quan_end")[0]["data"]
            self.assertEqual((end["money"], end["earned"], end["shift_earned"]), (48, 48, 48))
            self.assertEqual(rows[-1]["reason"], "time")

    def test_ac18_waiting_customer_leaves_closing_without_penalty(self):
        sc = {"time_left_ticks": 10, "random_customers": False, "stock": {"bong_sung": 2},
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
        with Workdir() as w:
            rows = run_quan(w, sc, 50)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "closing",
                                               "reputation": 3.0})
            self.assertEqual(events(rows, "quan_end")[0]["data"]["reputation"], 3.0)

    def test_schedule_uses_phase_tick_even_when_shift_shortened(self):
        with Workdir() as w:
            rows = run_quan(w, {"time_left_ticks": 200, "stock": {"ca_loc": 1}}, 200)
            self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [120])


class Determinism(unittest.TestCase):
    def test_same_seed_same_bytes(self):
        sc = {"quan": {"stock": {"ca_loc": 3, "bong_sung": 6, "ca_linh": 3, "bong_dien_dien": 1}}}
        inp = frames({"tick": 0, "move": [-1, 1]}, {"tick": 200, "interact": True}, {"tick": 201, "interact": False})
        with Workdir() as w:
            outs = []
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "9", "--ticks", "3000",
                                         "--scenario", write_json(w.path("s.json"), sc),
                                         "--inputs", write_json(w.path("i.json"), inp), "--out", w.path(f"{i}.jsonl"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"{i}.jsonl"), "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
