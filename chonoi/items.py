"""Cá thể nguyên liệu + độ tươi (Ticket-03, contract v1.2) — dùng chung gather, quán, day, file kho.

Nội bộ: {"id", "kind", "u"} với u = fresh × 240 (số nguyên) -> so ngưỡng 30 và floor chính xác.
Gather −0.5/s = −2 u/tick, quán −0.25/s = −1 u/tick (60 tick/s). Xuất {"id","kind","fresh": u/240}.
"""

from .ids import id_key

UNITS = 240
FRESH_MAX = 100 * UNITS


def units_per_tick(per_s):
    return int(round(per_s * UNITS / 60))


def spoiled_below_units(tuning):
    return int(round(tuning["freshness"]["spoiled_below"] * UNITS))


def new_item(ids, kind, tuning):
    return {"id": ids.new("I"), "kind": kind, "u": int(round(tuning["freshness"]["initial"] * UNITS))}


def from_dict(d):
    return {"id": d["id"], "kind": d["kind"], "u": int(round(float(d["fresh"]) * UNITS))}


def to_dict(it):
    return {"id": it["id"], "kind": it["kind"], "fresh": it["u"] / UNITS}


def to_list(items):
    return [to_dict(it) for it in items]


def sorted_by_id(items):
    return sorted(items, key=lambda it: id_key(it["id"]))


def is_spoiled(it, tuning):
    return it["u"] < spoiled_below_units(tuning)


def decay(items, per_tick, tuning, location):
    """Hao tươi một bước; trả event spoiled (theo id) cho cá thể đi từ >= ngưỡng xuống < ngưỡng."""
    lim = spoiled_below_units(tuning)
    crossed = []
    for it in items:
        before = it["u"]
        it["u"] = max(0, before - per_tick)
        if before >= lim > it["u"]:
            crossed.append(it)
    return [("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location})
            for it in sorted_by_id(crossed)]


def freshest(items):
    """Tươi nhất trước, hòa theo id nhỏ."""
    return sorted(items, key=lambda it: (-it["u"], id_key(it["id"])))
