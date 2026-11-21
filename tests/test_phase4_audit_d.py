"""Release acceptance checks from supplied TICKET-04 and inherited v1.2.

These tests observe the real renderer/day engine. Short validated fixtures
exercise boundaries; the separate soak CLI runs ten full, default days.
"""

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from chonoi.bench import Frame, H, W, render
from chonoi import bench
from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState
from chonoi.live import LiveGame
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.sim.day import DaySim
from helpers import ROOT, Workdir, write_json, items


def live_fixture(tuning, **gather):
    """Validated day scenario; simulation and snapshots are never patched."""
    fixture = {"day": {"money": 1000, "earned": 1000},
               "gather": {"time_left_ticks": 1, "hold": items("ca_loc", fresh=80),
                          "nodes": [], "fish": [], "monsters": [], "random_fish": False},
               "quan": {"time_left_ticks": 2, "random_customers": False}}
    fixture["gather"].update(gather)
    with Workdir() as work:
        return load_scenario(write_json(work.path("day.json"), fixture), "day", tuning)


def stateful_ten_days(seed=7):
    """One DaySim, real income and purchases, every phase, monotonically new IDs.

    The short valid fixtures provide an already-eating customer's frozen price
    each evening. This exercises payment/carry across ten days, not a strategy
    bot or an assertion that the idle soak CLI earned money.
    """
    tuning = load_contract()["tuning"]
    fixture = {
        "day": {"money": 2000, "earned": 2000, "reputation": 3,
                "upgrades": {"oxygen": 1},
                "day_plan": [{"day": day, "dishes": {"ca_loc_nuong_trui": 1}} for day in range(1, 6)]},
        "gather": {"hold": [{"id": "I9", "kind": "ca_loc", "fresh": 80}],
                   "time_left_ticks": 1, "random_fish": False, "fish": [], "nodes": [], "monsters": []},
        "quan": {"time_left_ticks": 2, "random_customers": False,
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "state": "eating", "order_status": "served", "reserved": [],
                                "eat_ticks_left": 1, "base_price": 47, "tip": 9}]},
    }
    with Workdir() as work:
        validated = load_scenario(write_json(work.path("fixture.json"), fixture), "day", tuning)
    sim = DaySim(tuning, validated, seed, days=10)
    identity = id(sim)
    trace, events = [], []
    start = sim.snapshot()
    trace.append(dict(start, phase=sim.phase, phase_tick=sim.phase_tick, **sim.common()))
    frame_list = []
    for day in range(1, 11):
        frame_list.append({"tick": 4 * (day - 1), "shop_done": False})
        action = {"tick": 4 * (day - 1) + 3, "shop_done": True}
        if day <= 3:
            action["buy"] = ("hp", "oxygen", "hp")[day - 1]
        frame_list.append(action)
    player = InputPlayer(frame_list)
    tick = 0
    while not sim.done and tick < 50:
        emitted = sim.step(player.advance(tick))
        tick += 1
        events.extend({"tick": tick, "name": name, "data": data, "phase": phase, "day": day}
                      for name, data, phase, day in emitted)
        trace.append(dict(sim.snapshot(), phase=sim.phase, phase_tick=sim.phase_tick,
                          **sim.common(), tick=tick))
        assert id(sim) == identity
    return {"ticks": tick, "days_completed": sim.days_completed, "reason": sim.reason,
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
            "upgrades": sim.upgrades, "trace": trace, "events": events}


class Phase4Audit(unittest.TestCase):
    def test_benchmark_formula_uses_real_slowest_one_percent_after_warmup(self):
        """Record real clock calls; never substitute timing or render results."""
        clock = bench.time.perf_counter
        samples = []

        def observe():
            value = clock()
            samples.append(value)
            return value

        with Workdir() as work:
            output = work.path("measured.json")
            with patch.object(bench.time, "perf_counter", side_effect=observe):
                self.assertEqual(bench.main(["--seed", "42", "--duration", "0.05", "--out", output]), 0)
            result = json.loads(Path(output).read_text(encoding="utf-8"))
        self.assertEqual(bench.WARMUP_S, 3)
        self.assertEqual(len(samples) % 2, 0)  # t_start, frame pairs, final timestamp
        pairs = list(zip(samples[1:-1:2], samples[2:-1:2]))
        boundary = next(i for i, (_, end) in enumerate(pairs) if end - samples[0] >= 3)
        measured = [end - start for start, end in pairs[boundary + 1:]]
        self.assertTrue(measured and all(dt > 0 for dt in measured))
        elapsed = samples[-1] - pairs[boundary][1]
        self.assertEqual(result["frames"], len(measured))
        self.assertEqual(result["measured_s"], round(elapsed, 3))
        self.assertEqual(result["avg_fps"], round(len(measured) / elapsed, 2))
        slow = sorted(measured)[-max(1, math.ceil(len(measured) * 0.01)):]
        self.assertEqual(result["p1_low_fps"], round(1 / (sum(slow) / len(slow)), 2))

    def test_benchmark_paints_a_real_full_size_frame_and_dynamic_scene(self):
        tuning = load_contract()["tuning"]
        sess = Session("gather", tuning, {}, 42)
        frame = Frame()
        self.assertEqual((W, H), (1280, 720))
        self.assertEqual(len(frame.buf), 1280 * 720 * 3)
        render(frame, sess.snapshot(), tuning)
        first = bytes(frame.buf)
        self.assertGreaterEqual(len(set(first[n:n+3] for n in range(0, len(first), 3))), 8)
        for _ in range(10):
            sess.step(InputState((0, 0), {}, set()))
        render(frame, sess.snapshot(), tuning)
        self.assertNotEqual(bytes(frame.buf), first, "fish movement must change rasterized pixels")

    def test_one_ten_day_session_preserves_real_income_upgrades_ids_and_order(self):
        result = stateful_ten_days()
        self.assertEqual((result["ticks"], result["days_completed"], result["reason"]), (40, 10, "days_complete"))
        self.assertEqual((result["money"], result["earned"]), (1410, 2560))
        self.assertAlmostEqual(result["reputation"], 5, places=6)
        self.assertEqual(result["upgrades"], {"oxygen": 2, "hp": 2})
        starts = [s for s in result["trace"] if s["phase"] == "gather" and s["phase_tick"] == 0]
        self.assertEqual([s["hold"][0]["id"] for s in starts], [f"I{i}" for i in range(9, 19)])
        self.assertEqual(starts[0]["active_upgrades"], {"oxygen": 1})
        self.assertEqual(starts[1]["active_upgrades"], {"oxygen": 1, "hp": 1})
        self.assertEqual(starts[2]["active_upgrades"], {"oxygen": 2, "hp": 1})
        self.assertEqual(starts[3]["active_upgrades"], {"oxygen": 2, "hp": 2})
        for day in range(1, 11):
            sequence = [(e["name"], e["phase"]) for e in result["events"] if e["day"] == day
                        and not (e["phase"] == "gather" and e["name"] in ("day_start", "day_plan", "phase_start"))]
            expected = [("gather_end", "gather"), ("phase_start", "quan"),
                        ("paid", "quan"), ("quan_end", "quan"), ("phase_start", "shop")]
            self.assertEqual(sequence[:5], expected)
            self.assertIn(("shop_end", "shop"), sequence)

    def test_stateful_ten_day_gameplay_trace_is_deterministic(self):
        self.assertEqual(stateful_ten_days(7), stateful_ten_days(7))

    def test_live_cli_accepts_day_mode_for_inherited_full_day_demo(self):
        process = subprocess.run([sys.executable, "-B", "-m", "chonoi.live", "--mode", "day", "--help"],
                                 cwd=ROOT, capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8", errors="replace"))
        self.assertIn(b"{gather,quan,day}", process.stdout)
        self.assertIn(b"--days", process.stdout)

    def test_live_day_snapshot_has_phase_metadata(self):
        tuning = load_contract()["tuning"]
        try:
            snapshot = json.loads(LiveGame("day", tuning, {}, 42).state_json())
        except Exception as exc:
            self.fail(f"Live day cannot produce the browser state payload: {type(exc).__name__}: {exc}")
        self.assertEqual(snapshot["mode"], "day")
        self.assertEqual(snapshot["phase"], "gather")
        self.assertEqual(snapshot["meta"]["bounds"], tuning["gather"]["bounds"])

    def test_live_day_transfers_exact_items_then_shop_without_extra_decay(self):
        t = load_contract()["tuning"]
        game = LiveGame("day", t, live_fixture(t), 42)
        read = lambda: json.loads(game.state_json())
        self.assertEqual([e["name"] for e in read()["events"]], ["day_start", "day_plan", "phase_start"])
        game._tick_once()
        q = read()
        end = next(e for e in q["events"] if e["name"] == "gather_end")
        self.assertEqual((q["mode"], q["phase"], q["phase_tick"], q["sim_tick"]), ("day", "quan", 0, 1))
        self.assertEqual(q["stock"], end["data"]["inventory"]["items"])
        self.assertEqual(q["stock"][0]["id"], "I1")
        self.assertAlmostEqual(q["stock"][0]["fresh"], 80 - t["freshness"]["gather_decay_per_s"] / t["tick_hz"])
        self.assertEqual(q["meta"], t["quan"])
        self.assertEqual([(e["name"], e["phase"], e["tick"]) for e in q["events"][-2:]],
                         [("gather_end", "gather", 1), ("phase_start", "quan", 1)])
        game._tick_once()
        game._tick_once()
        s = read()
        self.assertEqual((s["phase"], s["phase_tick"], s["state"]), ("shop", 0, "playing"))
        self.assertEqual(s["meta"], t["shop"])
        self.assertEqual(s["shop_upgrades"], t["shop"]["upgrades"])
        self.assertAlmostEqual(s["stock"][0]["fresh"], q["stock"][0]["fresh"] - 2 * t["freshness"]["quan_decay_per_s"] / t["tick_hz"])
        game._tick_once()
        self.assertEqual(read()["stock"], s["stock"])

    def test_live_pause_discards_actions_and_restart_clears_input_events_upgrades(self):
        t = load_contract()["tuning"]
        game = LiveGame("day", t, live_fixture(t), 42)
        initial = json.loads(game.state_json())
        game.set_input({"pause": True, "interact": True, "buy": "hp", "shop_done": True})
        for _ in range(3):
            game._tick_once()
        paused = json.loads(game.state_json())
        for key in ("sim_tick", "time_left_ticks", "hold", "player", "money", "upgrades"):
            self.assertEqual(paused[key], initial[key], key)
        self.assertEqual(paused["state"], "paused")
        game.set_input({"pause": False})
        game._tick_once()
        game.set_input({"pause": True})
        game._tick_once()
        self.assertEqual(json.loads(game.state_json())["phase"], "quan")
        game.restart()
        self.assertEqual(json.loads(game.state_json()), initial)
        game._tick_once()
        self.assertEqual(json.loads(game.state_json())["phase"], "quan")

    def test_live_shop_purchase_then_close_applies_upgrade_only_next_day(self):
        t = load_contract()["tuning"]
        game = LiveGame("day", t, live_fixture(t), 42, days=2)
        for _ in range(3):
            game._tick_once()
        game.set_input({"buy": "oxygen"})
        game._tick_once()
        bought = json.loads(game.state_json())
        self.assertEqual((bought["upgrades"], bought["active_upgrades"]), ({"oxygen": 1}, {}))
        self.assertEqual(bought["money"], 1000 - t["shop"]["upgrades"]["oxygen"][0]["price"])
        self.assertEqual((bought["earned"], bought["score"]), (1000, 1300))
        game.set_input({"shop_done": True})
        game._tick_once()
        new = json.loads(game.state_json())
        self.assertEqual((new["day"], new["phase"], new["phase_tick"]), (2, "gather", 0))
        self.assertEqual(new["active_upgrades"], {"oxygen": 1})
        self.assertEqual(new["player"]["oxygen_max_ticks"], t["shop"]["upgrades"]["oxygen"][0]["oxygen_max_s"] * t["tick_hz"])
        self.assertEqual(new["hold"], items("ca_loc", fresh=80, start=2))

    def test_live_held_shop_done_is_not_a_new_edge_in_next_shop(self):
        t = load_contract()["tuning"]
        game = LiveGame("day", t, live_fixture(t), 42, days=2)
        for _ in range(3):
            game._tick_once()
        game.set_input({"shop_done": True})
        game._tick_once()
        for _ in range(4):
            game._tick_once()
        self.assertEqual(json.loads(game.state_json())["phase"], "shop")
        self.assertFalse(game.session.done)
        game.set_input({"shop_done": False})
        game._tick_once()
        game.set_input({"shop_done": True})
        game._tick_once()
        end = json.loads(game.state_json())
        self.assertTrue(end["finished"])
        self.assertEqual((end["state"], end["reason"], game.session.sim.days_completed), ("finished", "days_complete", 2))
        before = game.state_json()
        game._tick_once()
        self.assertEqual(game.state_json(), before)

    def test_ten_day_default_plan_repeats_and_every_phase_has_valid_invariants(self):
        t = load_contract()["tuning"]
        sim = DaySim(t, live_fixture(t), 7, days=10)
        plans = []
        for day in range(1, 11):
            self.assertEqual(sim.day, day)
            plans.append(sim.snapshot()["day_plan"])
            self.assertEqual(plans[-1], {k: t["day_plan"][(day - 1) % 5][k] for k in ("dishes", "ingredients")})
            for phase in ("gather", "quan", "quan", "shop"):
                self.assertEqual(sim.phase, phase)
                s = sim.snapshot()
                physical = s.get("hold", s.get("stock", []))
                self.assertEqual(len({it["id"] for it in physical}), len(physical))
                self.assertTrue(all(math.isfinite(it["fresh"]) and 0 <= it["fresh"] <= 100 for it in physical))
                common = sim.common()
                self.assertTrue(0 <= common["money"] <= common["earned"])
                self.assertTrue(t["quan"]["reputation_min"] <= common["reputation"] <= t["quan"]["reputation_max"])
                sim.step(InputState((0, 0), {}, {"shop_done"} if phase == "shop" else set()))
        self.assertEqual(plans[:5], plans[5:])
        self.assertEqual((sim.done, sim.reason, sim.days_completed), (True, "days_complete", 10))


if __name__ == "__main__":
    unittest.main()
