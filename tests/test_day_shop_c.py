"""Test hộp đen v1.1: contract, vòng Ngày, Shop, nâng cấp, pause (Ticket-02 mục 2, 4). AC-P2-01, 08..13."""

import json
import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def contract():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)


def run(w, mode, ticks, scenario=None, inp=None, days=None, every=1):
    args = ["--mode", mode, "--seed", "5", "--ticks", str(ticks), "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inp is not None:
        args += ["--inputs", write_json(w.path("in.json"), inp)]
    if days is not None:
        args += ["--days", str(days)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else None)


def snap(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][-1]


# Ngày rút gọn: sáng 1 tick, tối 1 tick -> Shop mở ở tick 2, bước Shop đầu đọc frame tick 2
FAST = {"gather": {"time_left_ticks": 1}, "quan": {"time_left_ticks": 1, "random_customers": False}}


class ContractV11(unittest.TestCase):
    def test_p2_01_contract_and_data(self):
        c = contract()
        t = c["tuning"]
        self.assertEqual(c["contract_version"], "1.1")
        self.assertEqual(len(t["menu"]), 6)
        self.assertEqual([s["id"] for s in t["quan"]["stoves"]], ["B1", "B2"])
        self.assertEqual([x["id"] for x in t["quan"]["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual({n["kind"] for n in t["gather"]["nodes"]}, {"bong_dien_dien", "bong_sung", "keo_neo"})
        self.assertEqual(t["gather"]["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})

    def test_p2_02_initial_fish_8_distinct_spawn_points(self):
        g = contract()["tuning"]["gather"]
        with Workdir() as w:
            code, err, rows = run(w, "gather", 0)
            self.assertEqual(code, 0, err)
            fish = snapshots(rows)[0]["fish"]
            self.assertEqual(len(fish), g["fish_initial"])
            self.assertEqual(len({tuple(f["pos"]) for f in fish}), len(fish))
            for f in fish:
                self.assertIn(f["pos"][0], g["fish_spawn_x"])
                self.assertIn(f["pos"][1], g["fish_spawn_depths"][f["kind"]])


class DayLoop(unittest.TestCase):
    def test_p2_08_day_start_order_and_plan(self):
        with Workdir() as w:
            code, err, rows = run(w, "day", 0)
            self.assertEqual(code, 0, err)
            ev = [(e["tick"], e["phase"], e["day"], e["name"]) for e in events(rows)]
            self.assertEqual(ev, [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                  (0, "gather", 1, "phase_start")])
            self.assertEqual(events(rows, "day_plan")[0]["data"], {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                                                                   "ingredients": {"ca_loc": 3, "bong_sung": 6}})
            s = snapshots(rows)[0]
            self.assertEqual((s["mode"], s["phase"], s["day"], s["upgrades"], s["active_upgrades"]),
                             ("day", "gather", 1, {}, {}))
            self.assertEqual(rows[0]["type"], "event")  # event tick 0 trước snapshot tick 0

    def test_p2_08_phase_changes_same_tick_and_snapshot(self):
        with Workdir() as w:
            code, err, rows = run(w, "day", 3, FAST, every=100)
            self.assertEqual(code, 0, err)
            ev = [(e["tick"], e["phase"], e["name"]) for e in events(rows) if e["tick"] > 0]
            self.assertEqual(ev[:2], [(1, "gather", "gather_end"), (1, "quan", "phase_start")])
            self.assertIn((2, "quan", "quan_end"), ev)
            self.assertIn((2, "shop", "phase_start"), ev)
            s1 = snap(rows, 1)  # snapshot đổi pha dù snapshot-every = 100
            self.assertEqual((s1["phase"], s1["phase_tick"]), ("quan", 0))

    def test_p2_09_quan_in_day_only_plan_dishes(self):
        sc = {"gather": {"hold": ["ca_loc", "ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"], "random_fish": False}}
        inp = frames({"tick": 0, "interact": True})  # đứng ở bến -> cập bến ngay
        with Workdir() as w:
            code, err, rows = run(w, "day", 1100, sc, inp, every=500)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            arr = events(rows, "customer_arrived")
            self.assertEqual([(e["tick"], e["data"]["dish_id"]) for e in arr], [(121, "ca_loc_nuong_trui")])
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [1021])  # lẩu đủ đồ nhưng ngoài kế hoạch


class Shop(unittest.TestCase):
    def test_p2_10_11_buy_funds_unknown_done_and_upgrade_next_day(self):
        sc = dict(FAST, day={"money": 300, "earned": 300})
        inp = frames({"tick": 2, "buy": "hp"}, {"tick": 3, "buy": "hp"}, {"tick": 4, "buy": "pho"},
                     {"tick": 5, "shop_done": True})
        with Workdir() as w:
            code, err, rows = run(w, "day", 6, sc, inp, days=2)
            self.assertEqual(code, 0, err)
            got = [(e["tick"], e["name"], e["data"]) for e in events(rows) if e["phase"] == "shop" and e["name"] != "phase_start"]
            self.assertEqual(got, [
                (3, "bought", {"upgrade": "hp", "level": 1, "price": 250, "money": 50}),
                (4, "buy_failed", {"action": "hp", "reason": "funds"}),
                (5, "buy_failed", {"action": "pho", "reason": "unknown"}),
                (6, "shop_end", {"reason": "done"})])
            s3 = snap(rows, 3)
            self.assertEqual((s3["money"], s3["earned"], s3["upgrades"], s3["active_upgrades"]), (50, 300, {"hp": 1}, {}))
            s6 = snap(rows, 6)  # Ngày 2 dựng ngay tick Shop đóng
            self.assertEqual((s6["day"], s6["phase"], s6["active_upgrades"]), (2, "gather", {"hp": 1}))
            self.assertEqual((s6["player"]["hp"], s6["player"]["hp_max"]), (4, 4))
            self.assertEqual([(e["tick"], e["day"], e["name"]) for e in events(rows) if e["tick"] == 6][-3:],
                             [(6, 2, "day_start"), (6, 2, "day_plan"), (6, 2, "phase_start")])

    def test_p2_10_max_level_and_oxygen_upgrade(self):
        sc = dict(FAST, day={"money": 1000, "earned": 1000, "upgrades": {"hp": 2, "oxygen": 1}})
        inp = frames({"tick": 2, "buy": "hp"}, {"tick": 3, "buy": "oxygen"}, {"tick": 4, "shop_done": True})
        with Workdir() as w:
            code, err, rows = run(w, "day", 5, sc, inp, days=2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "hp", "reason": "max_level"})
            self.assertEqual(events(rows, "bought")[0]["data"], {"upgrade": "oxygen", "level": 2, "price": 400, "money": 600})
            s = snap(rows, 5)
            self.assertEqual((s["player"]["oxygen_max_ticks"], s["player"]["hp_max"]), (3600, 5))

    def test_p2_10_shop_auto_close_600(self):
        with Workdir() as w:
            code, err, rows = run(w, "day", 700, FAST, every=1000)
            self.assertEqual(code, 0, err)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "shop_end")], [(602, {"reason": "time"})])
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 1))


class Pause(unittest.TestCase):
    def test_p2_12_pause_freezes_sim(self):
        inp = frames({"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 5, "pause": True})
        with Workdir() as w:
            code, err, rows = run(w, "gather", 7, None, inp)
            self.assertEqual(code, 0, err)
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(1, "paused"), (6, "resumed")])
            s3 = snap(rows, 3)
            self.assertEqual((s3["state"], s3["sim_tick"], s3["phase_tick"], s3["time_left_ticks"]), ("paused", 0, 0, 10800))
            s6 = snap(rows, 6)
            self.assertEqual((s6["state"], s6["sim_tick"], s6["time_left_ticks"]), ("playing", 1, 10799))
            self.assertEqual((rows[-1]["ticks"], rows[-1]["sim_tick"]), (7, 2))


class FullRun(unittest.TestCase):
    def test_p2_13_five_days_complete_and_fast(self):
        with Workdir() as w:
            t0 = time.time()
            code, err, rows = run(w, "day", 200000, days=5, every=1000)
            elapsed = time.time() - t0
            self.assertEqual(code, 0, err)
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"], end["ticks"]), ("days_complete", 5, 5 * 22200))
            self.assertEqual([e["data"]["dishes"] for e in events(rows, "day_plan")][2],
                             {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2})
            self.assertLess(elapsed, 5 * 20)  # mỗi Ngày <= 20 s


class ScenarioDay(unittest.TestCase):
    def test_day_scenario_conflicts_exit_2(self):
        bad = [{"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}},
               {"day": {"money": 100, "earned": 50}}, {"day": {"upgrades": {"hp": 3}}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}}, {"river": {}}]
        with Workdir() as w:
            for sc in bad:
                code, _, _ = run(w, "day", 0, sc)
                self.assertEqual(code, 2, sc)


if __name__ == "__main__":
    unittest.main()
