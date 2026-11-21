"""Test hộp đen v1.2 độ tươi / kho cá thể (Ticket-03) — AC-P3-01..07."""

import json
import unittest

from helpers import Workdir, events, frames, items, read_jsonl, run_headless, snapshots, write_json


def run(w, mode, ticks, scenario=None, inp=None, extra=()):
    args = ["--mode", mode, "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1", "--out", w.path("o.jsonl"), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inp is not None:
        args += ["--inputs", write_json(w.path("in.json"), inp)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else None)


def snap(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][-1]


C1 = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}


class Freshness(unittest.TestCase):
    def test_p3_01_threshold_spoiled_tick1_ticket_example(self):
        sc = {"gather": {"hold": items("ca_linh", fresh=30), "random_fish": False, "monsters": []}}
        with Workdir() as w:
            code, err, rows = run(w, "gather", 1, sc)
            self.assertEqual(code, 0, err)
            self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                             [(1, "spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"})])

    def test_p3_02_handoff_file_exact_and_count_schema_rejected(self):
        sc = {"gather": {"hold": items("ca_linh"), "random_fish": False, "monsters": []}}
        with Workdir() as w:
            inv = w.path("kho.json")
            code, err, rows = run(w, "gather", 5, sc, frames({"tick": 0, "interact": True}), ("--inventory-out", inv))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 23998 / 240}]})
            code, err, q = run(w, "quan", 0, None, None, ("--inventory", inv))
            self.assertEqual(code, 0, err)
            st = snapshots(q)[0]["stock"]
            self.assertEqual((st[0]["id"], st[0]["kind"]), ("I1", "ca_linh"))
            self.assertLessEqual(abs(st[0]["fresh"] - 23998 / 240), 0.01)
            old = write_json(w.path("old.json"), {"items": {"ca_linh": 1}})
            self.assertEqual(run(w, "quan", 0, None, None, ("--inventory", old))[0], 2)

    def test_p3_03_new_item_fresh_100_decays_from_next_step(self):
        sc = {"gather": {"player": {"pos": [12, 0]}, "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                         "random_fish": False, "monsters": []}}
        with Workdir() as w:
            code, err, rows = run(w, "gather", 3, sc, frames({"tick": 0, "interact": True}))
            self.assertEqual(code, 0, err)
            self.assertEqual(snap(rows, 1)["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])
            self.assertLessEqual(abs(snap(rows, 3)["hold"][0]["fresh"] - (100 - 4 / 240)), 0.01)

    def test_p3_04_spoiled_reservation_rereserves_freshest(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 50},
                 {"id": "I3", "kind": "ca_loc", "fresh": 40}]
        sc = {"quan": {"stock": stock, "random_customers": False, "customers": [dict(C1, reserved=["I1"])]}}
        with Workdir() as w:
            code, err, rows = run(w, "quan", 1, sc)
            self.assertEqual(code, 0, err)
            self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled")], ["I1"])
            c = snap(rows, 1)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_p3_05_spoiled_without_replacement_unfulfillable(self):
        sc = {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 30}], "random_customers": False,
                       "customers": [dict(C1, reserved=["I1"])]}}
        with Workdir() as w:
            code, err, rows = run(w, "quan", 1, sc)
            self.assertEqual(code, 0, err)
            c = snap(rows, 1)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"], c["state"]), ("unfulfillable", [], "waiting"))

    def test_p3_06_price_by_freshness(self):
        sc = {"quan": {"player": {"pos": [2, 8]}, "random_customers": False,
                       "stock": [{"id": "I7", "kind": "ca_loc", "fresh": 50}], "customers": [C1]}}
        with Workdir() as w:
            code, err, rows = run(w, "quan", 2, sc, frames({"tick": 0, "interact": True}))
            self.assertEqual(code, 0, err)
            d = events(rows, "cook_started")[0]["data"]
            self.assertEqual([i["id"] for i in d["items"]], ["I7"])
            self.assertEqual(d["base_price"], 29)  # floor(60 × (50 − 1/240) / 100)

    def test_p3_07_scenario_conflicts_exit_2(self):
        bad = [{"quan": {"stock": items("ca_loc"), "customers": [dict(C1, reserved=["I9"])]}},
               {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 20}], "customers": [dict(C1, reserved=["I1"])]}},
               {"quan": {"stock": items("bong_sung"), "customers": [dict(C1, reserved=["I1"])]}},
               {"quan": {"stock": {"ca_loc": 1}}}, {"gather": {"hold": ["ca_loc"]}}]
        with Workdir() as w:
            for sc in bad:
                mode = "gather" if "gather" in sc else "quan"
                self.assertEqual(run(w, mode, 0, sc)[0], 2, sc)

    def test_p3_day_handoff_keeps_ids_same_tick(self):
        sc = {"gather": {"hold": items("ca_loc", "bong_sung"), "random_fish": False}}
        with Workdir() as w:
            code, err, rows = run(w, "day", 2, sc, frames({"tick": 0, "interact": True}))
            self.assertEqual(code, 0, err)
            s1 = snap(rows, 1)
            self.assertEqual((s1["phase"], [i["id"] for i in s1["stock"]]), ("quan", ["I1", "I2"]))
            self.assertLessEqual(abs(s1["stock"][0]["fresh"] - 23998 / 240), 0.01)  # không hao thêm khi bàn giao


if __name__ == "__main__":
    unittest.main()
