"""Cá Sấu Năm Chèo — tuần tra, đuổi, chạm, recoil, ngất (Ticket 1.2 / Phase 2).

API:
  make_monsters(tuning, scenario, day) -> list[dict]
  step_monsters(sim, events) -> bool   (True nếu người chơi vừa ngất do quái)

Gọi từ GatherSim.step() đúng thứ tự PRD-0 mục 4.5:
  sau oxy/ngạt, trước interact; cả hai di chuyển trước khi xét hit.
"""

import math

from ..ids import id_key
from ..items import to_list

TICK = 60.0

# --- helpers ----------------------------------------------------------------

def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _clamp_pos(pos, bounds, depths):
    x = max(bounds["x"][0], min(bounds["x"][1], pos[0]))
    d = max(depths[0], min(depths[1], pos[1]))
    return [x, d]


def _move_toward(pos, target, speed_per_tick, bounds, depths):
    """Di chuyển pos về phía target với tốc độ speed_per_tick m/tick, chặn biên."""
    dx = target[0] - pos[0]
    dd = target[1] - pos[1]
    dist = math.sqrt(dx * dx + dd * dd)
    if dist < 1e-9:
        return list(pos)
    step = min(dist, speed_per_tick)
    nx = pos[0] + dx / dist * step
    nd = pos[1] + dd / dist * step
    return _clamp_pos([nx, nd], bounds, depths)


def _unit_away(monster_pos, player_pos):
    """Vector đơn vị từ player_pos ra xa (recoil direction). Trùng tâm dùng +x."""
    dx = monster_pos[0] - player_pos[0]
    dd = monster_pos[1] - player_pos[1]
    dist = math.sqrt(dx * dx + dd * dd)
    if dist < 1e-9:
        return [1.0, 0.0]
    return [dx / dist, dd / dist]


# --- public API -------------------------------------------------------------

def make_monsters(tuning, scenario, day: int) -> list:
    """Dựng danh sách quái cho GatherSim.

    - scenario.monsters thay thế hoàn toàn danh sách mặc định nếu có.
    - Ngày 1 theo default (spawns với from_day <= day).
    - Trả list[dict] đã sắp theo id.
    """
    monsters_cfg = tuning["gather"].get("monsters", {})
    species = monsters_cfg.get("species", {})
    invuln_ticks = monsters_cfg.get("invuln_ticks", 90)
    loss_ratio = monsters_cfg.get("loss_ratio", 0.5)

    if "monsters" in scenario:
        raw = scenario["monsters"]
    else:
        raw = [s for s in monsters_cfg.get("spawns", []) if s.get("from_day", 1) <= day]

    result = []
    for s in raw:
        kind = s.get("kind", "ca_sau")
        sp = species.get(kind, {})
        m = {
            "id": s["id"],
            "kind": kind,
            "pos": [float(c) for c in s["pos"]],
            "waypoints": [[float(c) for c in wp] for wp in s.get("waypoints", [s["pos"], s["pos"]])],
            "target_idx": s.get("target_idx", 1),
            "state": s.get("state", "patrol"),
            "state_ticks_left": s.get("state_ticks_left", 0),
            "recoil_dir": s.get("recoil_dir", None),
            # species params (cached for speed)
            "_patrol_speed": sp.get("patrol_speed", 1.0) / TICK,
            "_chase_speed": sp.get("chase_speed", 3.0) / TICK,
            "_detect_radius": sp.get("detect_radius", 10.0),
            "_exit_radius": sp.get("exit_radius", 16.0),
            "_depths": sp.get("depths", [10, 30]),
            "_hit_radius": sp.get("hit_radius", 1.5),
            "_recoil_ticks": sp.get("recoil_ticks", 60),
            "_recoil_dist": sp.get("recoil_dist", 2.0),
            "_invuln_ticks": invuln_ticks,
            "_loss_ratio": loss_ratio,
        }
        result.append(m)
    result.sort(key=lambda m: id_key(m["id"]))
    return result


def step_monsters(sim, events) -> bool:
    """Cập nhật tất cả quái một bước; trả True nếu người chơi vừa ngất do quái."""
    if not sim.monsters:
        return False

    bounds = sim.t["bounds"]
    player_pos = sim.pos
    player_d = player_pos[1]
    surface_depth = sim.t["surface_depth"]

    # --- di chuyển từng quái ---
    just_recovered = set()  # hết recoil ở bước này: về patrol, xét phát hiện/chạm từ bước kế (Ticket 1.2)
    for m in sim.monsters:
        depths = m["_depths"]
        m_depths = {"x": bounds["x"], "d": [depths[0], depths[1]]}
        # bounds dạng dict cho _clamp_pos
        m_bounds = {"x": bounds["x"], "d": [depths[0], depths[1]]}

        if m["state"] == "recoil":
            m["state_ticks_left"] = max(0, m["state_ticks_left"] - 1)
            if m["recoil_dir"] is not None:
                step = m["_recoil_dist"] / m["_recoil_ticks"]
                rd = m["recoil_dir"]
                nx = m["pos"][0] + rd[0] * step
                nd = m["pos"][1] + rd[1] * step
                m["pos"] = _clamp_pos([nx, nd], bounds, depths)
            if m["state_ticks_left"] <= 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
                just_recovered.add(m["id"])
            continue
        elif m["state"] == "chase":
            # kiểm xem còn chase không
            dist_to_player = _dist(m["pos"], player_pos)
            if dist_to_player > m["_exit_radius"] or player_d < depths[0]:
                m["state"] = "patrol"
            else:
                m["pos"] = _move_toward(m["pos"], player_pos, m["_chase_speed"], bounds, depths)
        # patrol (hoặc vừa chuyển về patrol)
        if m["state"] == "patrol":
            target = m["waypoints"][m["target_idx"]]
            dist_to_wp = _dist(m["pos"], target)
            m["pos"] = _move_toward(m["pos"], target, m["_patrol_speed"], bounds, depths)
            # đến waypoint: đổi mục tiêu cho bước sau
            if dist_to_wp <= m["_patrol_speed"] + 1e-6:
                m["target_idx"] = 1 - m["target_idx"]
            # kiểm phát hiện người chơi
            if player_d >= depths[0]:
                dist_pp = _dist(m["pos"], player_pos)
                if dist_pp <= m["_detect_radius"]:
                    m["state"] = "chase"

    # --- xét hit: sau khi cả hai di chuyển ---
    if sim.invuln_ticks > 0:
        return False  # người chơi đang bất tử

    if player_d < surface_depth:  # người chơi ở mặt nước không bị hit
        return False

    # tìm con gần nhất trong hit_radius
    hittable = [(m, _dist(m["pos"], player_pos)) for m in sim.monsters
                if m["state"] != "recoil" and m["id"] not in just_recovered
                and _dist(m["pos"], player_pos) <= m["_hit_radius"]
                and player_d >= m["_depths"][0]]
    if not hittable:
        return False

    # chọn gần nhất, hòa theo id
    hittable.sort(key=lambda x: (x[1], id_key(x[0]["id"])))
    m, _ = hittable[0]

    # tính lost: floor(len(hold) * loss_ratio) theo LIFO
    n_lost = math.floor(len(sim.hold) * m["_loss_ratio"])
    lost = []
    for _ in range(n_lost):
        lost.append(sim.hold.pop())  # LIFO: pop từ cuối (cá thể)

    sim.hp = max(0, sim.hp - 1)
    sim.invuln_ticks = m["_invuln_ticks"]
    events.append(("monster_hit", {
        "monster_id": m["id"],
        "hp": sim.hp,
        "lost": to_list(lost),
        "pos": list(player_pos),
    }))

    # recoil: bắt đầu từ bước sau (state_ticks_left = recoil_ticks)
    m["recoil_dir"] = _unit_away(m["pos"], player_pos)
    m["state"] = "recoil"
    m["state_ticks_left"] = m["_recoil_ticks"]

    if sim.hp == 0:
        remaining = to_list(reversed(sim.hold))
        sim.hold = []
        events.append(("faint", {"cause": "monster", "lost": remaining, "hp": 0}))
        sim._finish("fainted", events)
        return True

    return False
