"""Unit & black-box tests cho Phase 2 Người A (sim/gather): cá bơi, phản xạ mép, sinh cá theo chu kỳ, ctx day."""

import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_p2():
    return {
        "gather": {
            "duration_s": 180,
            "bounds": {"x": [0, 100], "d": [0, 30]},
            "dock_pos": [2, 0],
            "dock_radius": 3,
            "start_pos": [2, 0],
            "start_heading_deg": 0,
            "swim_speed": 4.0,
            "ramp_max_ticks": 6,
            "surface_depth": 0.5,
            "oxygen_max_s": 30,
            "oxygen_refill_per_tick": 6,
            "choke_interval_ticks": 60,
            "hp_max": 3,
            "hold_capacity": 12,
            "interact_radius": 2.0,
            "node_yield": 1,
            "regrow_s": 20,
            "catch_radius": 2.0,
            "catch_cooldown_s": 0.5,
            "fish_initial": 8,
            "fish_speed": 1.5,
            "fish_turn_ticks": 120,
            "fish_max": 12,
            "fish_spawn_ticks": 360,
            "fish_spawn_clearance": 1.0,
            "fish_x": [4, 96],
            "fish_depths": {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]},
            "fish_spawn_x": [15, 30, 45, 60, 75, 90],
            "fish_spawn_depths": {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]},
            "fish_weights": {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3},
            "fish_yield": {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
            "nodes": [
                {"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]},
                {"id": "N2", "kind": "bong_dien_dien", "pos": [28, 0]},
                {"id": "N3", "kind": "bong_sung", "pos": [44, 0]},
                {"id": "N4", "kind": "bong_sung", "pos": [60, 0]},
                {"id": "N5", "kind": "keo_neo", "pos": [76, 0]},
                {"id": "N6", "kind": "keo_neo", "pos": [90, 0]},
            ],
            "monsters": {
                "species": {"ca_sau": {"patrol_speed": 1.0, "chase_speed": 3.0, "detect_radius": 10, "exit_radius": 16,
                                       "depths": [10, 30], "hit_radius": 1.5, "recoil_ticks": 60, "recoil_dist": 2.0}},
                "spawns": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1}],
                "invuln_ticks": 90, "loss_ratio": 0.5
            }
        },
        "quan": {
            "duration_s": 180,
            "bounds": {"x": [0, 16], "z": [0, 10]},
            "start_pos": [8, 5],
            "walk_speed": 4.0,
            "ramp_max_ticks": 6,
            "interact_radius": 1.5,
            "stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}],
            "tables": [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]},
                       {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [13, 6]}],
            "first_customer_tick": 120,
            "customer_interval_s": 15,
            "patience_s": 60,
            "eat_s": 10,
            "burn_s": None,
            "carry_limit": 1,
            "tip_rate": 0.2,
            "tip_min_patience_ratio": 0.5,
            "tip_reputation": 0.2,
            "left_reputation_delta": -0.5,
            "reputation_initial": 3.0,
            "reputation_min": 0,
            "reputation_max": 5
        },
        "menu": {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
            "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
            "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200}
        },
        "score": {"reputation_multiplier": 100}
    }


class GatherPhase2Tests(unittest.TestCase):
    def test_gather_sim_direct_fish_initial_8_and_distinct_positions(self):
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        sim = GatherSim(t, {}, Streams(42), IdAllocator())
        self.assertEqual(len(sim.fish), 8)
        positions = [tuple(f["pos"]) for f in sim.fish]
        self.assertEqual(len(set(positions)), 8, "8 đàn cá ban đầu phải ở 8 vị trí khác nhau")
        for f in sim.fish:
            self.assertIn(f["kind"], ("ca_linh", "ca_loc", "ca_keo"))
            bx = t["gather"]["fish_x"]
            bd = t["gather"]["fish_depths"][f["kind"]]
            self.assertTrue(bx[0] <= f["pos"][0] <= bx[1])
            self.assertTrue(bd[0] <= f["pos"][1] <= bd[1])

    def test_fish_turn_every_120_ticks_and_swim(self):
        from chonoi.ids import IdAllocator
        from chonoi.inputs import InputPlayer
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        scenario = {
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50.0, 10.0], "heading_deg": 0.0}]
        }
        sim = GatherSim(t, scenario, Streams(42), IdAllocator())
        f0 = dict(sim.fish[0], pos=list(sim.fish[0]["pos"]))
        pl = InputPlayer([])

        # Chạy 119 bước: chưa đổi góc ngẫu nhiên mới và không chạm mép, heading giữ nguyên 0°
        for _ in range(119):
            sim.step(pl.advance(sim.phase_tick))

        f1 = sim.fish[0]
        self.assertEqual(f0["heading_deg"], f1["heading_deg"], "chưa tới 120 tick và chưa chạm mép thì heading không đổi")
        dist_moved = math.dist(f0["pos"], f1["pos"])
        self.assertAlmostEqual(dist_moved, 119 * (1.5 / 60.0), places=3, msg="cá bơi đúng tốc độ 1.5m/s")

        # Bước thứ 120: đổi hướng ngẫu nhiên
        heading_before_120 = f1["heading_deg"]
        sim.step(pl.advance(sim.phase_tick))
        heading_after_120 = sim.fish[0]["heading_deg"]
        self.assertNotEqual(heading_before_120, heading_after_120, "bước 120 cá phải đổi hướng")

    def test_fish_bounce_bounds(self):
        from chonoi.ids import IdAllocator
        from chonoi.inputs import InputPlayer
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        # Đặt 3 đàn cá sát mép và hướng đâm thẳng ra ngoài mép
        scenario = {
            "fish": [
                {"id": "F1", "kind": "ca_linh", "pos": [4.01, 3.01], "heading_deg": 225.0},  # góc trên trái
                {"id": "F2", "kind": "ca_loc", "pos": [95.99, 10.0], "heading_deg": 0.0},    # đâm phải
                {"id": "F3", "kind": "ca_keo", "pos": [50.0, 27.99], "heading_deg": 90.0},   # đâm đáy
            ]
        }
        sim = GatherSim(t, scenario, Streams(1), IdAllocator())
        pl = InputPlayer([])

        # Chạy 50 bước, kiểm tra không con nào vượt ra ngoài biên
        for _ in range(50):
            sim.step(pl.advance(sim.phase_tick))
            for f in sim.fish:
                bx = t["gather"]["fish_x"]
                bd = t["gather"]["fish_depths"][f["kind"]]
                self.assertGreaterEqual(f["pos"][0], bx[0] - 1e-6)
                self.assertLessEqual(f["pos"][0], bx[1] + 1e-6)
                self.assertGreaterEqual(f["pos"][1], bd[0] - 1e-6)
                self.assertLessEqual(f["pos"][1], bd[1] + 1e-6)

    def test_fish_spawn_at_360_ticks(self):
        from chonoi.ids import IdAllocator
        from chonoi.inputs import InputPlayer
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        sim = GatherSim(t, {}, Streams(10), IdAllocator())
        self.assertEqual(len(sim.fish), 8)
        pl = InputPlayer([])

        all_events = []
        for _ in range(360):
            evs = sim.step(pl.advance(sim.phase_tick))
            all_events.extend(evs)

        spawn_evs = [e for e in all_events if e[0] == "fish_spawned"]
        self.assertEqual(len(spawn_evs), 1, "đúng tick 360 phải sinh thêm 1 đàn")
        self.assertEqual(len(sim.fish), 9)
        new_f_id = spawn_evs[0][1]["id"]
        new_f = next(f for f in sim.fish if f["id"] == new_f_id)
        # Điểm sinh phải cách mọi đàn còn lại > 1.0 m
        other_fish = [f for f in sim.fish if f["id"] != new_f_id]
        for of in other_fish:
            self.assertGreater(math.dist(new_f["pos"], of["pos"]), 1.0)

    def test_fish_random_false_no_swim_no_spawn(self):
        from chonoi.ids import IdAllocator
        from chonoi.inputs import InputPlayer
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        scenario = {
            "random_fish": False,
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20.0, 5.0], "heading_deg": 45.0}]
        }
        sim = GatherSim(t, scenario, Streams(1), IdAllocator())
        pl = InputPlayer([])

        all_events = []
        for _ in range(365):
            evs = sim.step(pl.advance(sim.phase_tick))
            all_events.extend(evs)

        self.assertEqual(sim.fish[0]["pos"], [20.0, 5.0], "random_fish=false cá fixture phải đứng yên")
        self.assertEqual(len([e for e in all_events if e[0] == "fish_spawned"]), 0, "không được sinh cá")

    def test_ca_keo_catch_yield_2(self):
        from chonoi.ids import IdAllocator
        from chonoi.inputs import LiveInputs
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        scenario = {
            "player": {"pos": [50.0, 24.0]},
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [50.5, 24.0]}],
        }
        sim = GatherSim(t, scenario, Streams(1), IdAllocator())
        li = LiveInputs()
        li.set(catch=True)
        evs = sim.step(li.advance())
        caught_evs = [e for e in evs if e[0] == "fish_caught"]
        self.assertEqual(len(caught_evs), 1)
        self.assertEqual(caught_evs[0][1]["yield"], 2)
        self.assertEqual(caught_evs[0][1]["kind"], "ca_keo")
        self.assertEqual(sim.hold, ["ca_keo", "ca_keo"])
        self.assertEqual(sim.catch_cd_ticks, 30)

    def test_ctx_day_hp_and_oxygen_upgrade(self):
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        t = tuning_p2()
        ctx = {"day": 3, "hp_max": 5, "oxygen_max_s": 60}
        sim = GatherSim(t, {}, Streams(1), IdAllocator(), ctx=ctx)
        snap = sim.snapshot()
        self.assertEqual(snap["player"]["hp"], 5)
        self.assertEqual(snap["player"]["hp_max"], 5)
        self.assertEqual(snap["player"]["oxygen_ticks"], 3600)
        self.assertEqual(snap["player"]["oxygen_max_ticks"], 3600)
        self.assertIn("monsters", snap)


if __name__ == "__main__":
    unittest.main()
