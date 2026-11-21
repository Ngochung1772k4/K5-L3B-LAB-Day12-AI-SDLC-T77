"""Sinh đàn cá v1.1 (Ticket-02 mục 1.1) — dùng chung cho đầu ca và sinh theo lịch.

Luật một lần sinh: lọc điểm (x ∈ fish_spawn_x, d ∈ fish_spawn_depths[loài]) cách MỌI đàn đang sống
> fish_spawn_clearance; chọn loài theo fish_weights chuẩn hóa trên các loài còn điểm; chọn đều một điểm
của loài; hướng ban đầu theo seed. Hết điểm thì bỏ lượt (trả None).
"""

import math

from ..contract import FISH_KINDS
from ..ids import id_key


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


def _reflect(v, lo, hi):
    """Phản xạ phần quãng đường vượt mép; trả (vị trí, có đảo hướng không)."""
    flipped = False
    for _ in range(4):  # quãng đường mỗi bước rất nhỏ so với miền; vài lần là đủ
        if v > hi:
            v, flipped = hi - (v - hi), not flipped
        elif v < lo:
            v, flipped = lo + (lo - v), not flipped
        else:
            break
    return v, flipped


def swim(t, fish, rng):
    """Một bước bơi cho mọi đàn (theo id): đổi hướng ở bước bơi thứ fish_turn_ticks·k trước khi di chuyển,
    đi fish_speed/60 m, phản xạ mép miền x ∈ fish_x, d ∈ fish_depths[loài] (chạm góc đảo cả hai)."""
    step = t["fish_speed"] / 60.0
    xlo, xhi = t["fish_x"]
    for f in sorted(fish, key=lambda f: id_key(f["id"])):
        f["age_ticks"] = f.get("age_ticks", 0) + 1
        if f["age_ticks"] % t["fish_turn_ticks"] == 0:
            f["heading_deg"] = rng.random() * 360.0
        h = math.radians(f["heading_deg"])
        vx, vd = math.cos(h), math.sin(h)
        dlo, dhi = t["fish_depths"][f["kind"]]
        x, fx = _reflect(f["pos"][0] + vx * step, xlo, xhi)
        d, fd = _reflect(f["pos"][1] + vd * step, dlo, dhi)
        if fx:
            vx = -vx
        if fd:
            vd = -vd
        if fx or fd:
            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0
        f["pos"] = [x, d]
