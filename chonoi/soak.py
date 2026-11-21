"""Soak headless (Ticket-04 mục 2): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Một tiến trình chạy N Ngày liên tục (gather → quan → shop), kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, earned,
uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt. Bot tất định: không điều khiển (sáng hết giờ,
quán không phục vụ, Shop tự đóng) — cùng seed cho cùng kết quả gameplay.
Xuất {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .inputs import InputState
from .sim.day import DaySim


def soak(seed, days, tuning):
    idle = InputState((0.0, 0.0), {}, set())
    sim = DaySim(tuning, {}, seed, days)
    mult = tuning["score"]["reputation_multiplier"]
    results, done_before = [], 0
    while not sim.done:
        sim.step(idle)
        if sim.days_completed > done_before:  # Shop vừa đóng
            done_before = sim.days_completed
            results.append({"day": done_before, "earned": sim.earned, "reputation": sim.reputation,
                            "score": sim.earned + mult * math.floor(sim.reputation)})
    return sim.days_completed, results


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chonoi.soak")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--days", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("--days phải >= 1\n")
        return 2
    t0 = time.perf_counter()
    crashes, completed, results = 0, 0, []
    try:
        completed, results = soak(a.seed, a.days, load_contract()["tuning"])
    except Exception:  # đếm crash, vẫn ghi báo cáo
        crashes = 1
        traceback.print_exc()
    out = {"days": a.days, "days_completed": completed, "crashes": crashes, "results": results,
           "duration_s": round(time.perf_counter() - t0, 3)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in ("days", "days_completed", "crashes", "duration_s")}))
    return 0 if crashes == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
