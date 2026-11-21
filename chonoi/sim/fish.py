"""Sinh đàn cá v1.1 (Ticket-02 mục 1.1) — dùng chung cho đầu ca và sinh theo lịch.

Luật một lần sinh: lọc điểm (x ∈ fish_spawn_x, d ∈ fish_spawn_depths[loài]) cách MỌI đàn đang sống
> fish_spawn_clearance; chọn loài theo fish_weights chuẩn hóa trên các loài còn điểm; chọn đều một điểm
của loài; hướng ban đầu theo seed. Hết điểm thì bỏ lượt (trả None).
"""

import math

from ..contract import FISH_KINDS


def spawn_one(t, fish, rng, ids):
    """Trả đàn mới {id,kind,pos,heading_deg,age_ticks} hoặc None. `fish` là danh sách đàn đang sống."""
    clear = t["fish_spawn_clearance"]
    points = {}
    for kind in FISH_KINDS:  # thứ tự cố định
        pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
               if all(math.dist([x, d], f["pos"]) > clear for f in fish)]
        if pts:
            points[kind] = pts
    if not points:
        return None
    kinds = list(points)
    total = sum(t["fish_weights"][k] for k in kinds)
    r = rng.random() * total
    kind = kinds[-1]
    for k in kinds:
        r -= t["fish_weights"][k]
        if r < 0:
            kind = k
            break
    pos = rng.choice(points[kind])
    heading = rng.random() * 360.0
    return {"id": ids.new("F"), "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": 0}


def initial_fish(t, rng, ids):
    """Đầu ca: fish_initial đàn ở các điểm khác nhau."""
    fish = []
    for _ in range(int(t["fish_initial"])):
        f = spawn_one(t, fish, rng, ids)
        if f is None:
            break
        fish.append(f)
    return fish
