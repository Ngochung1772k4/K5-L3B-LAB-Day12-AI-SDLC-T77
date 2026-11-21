"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm đã cài đặt luật Phase 1 (PRD mục 13.8, Contract E & F):
  - Bơi + chuyển vùng dive / surface + oxy + ngạt (zero_oxy_ticks, choke) + ngất (faint, mất giỏ LIFO, kho rỗng)
  - Hái nút ở mặt nước (gather, hold_full, regrow_ticks) và bắt cá dưới nước (fish_caught, hold_full, catch_cd_ticks)
  - Cập bến xét TRƯỚC hái; ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")

FISH_SPEED = 1.5
FISH_TURN_TICKS = 120
FISH_MAX = 12
FISH_SPAWN_TICKS = 360
FISH_SPAWN_CLEARANCE = 1.0
FISH_X = [4.0, 96.0]
FISH_DEPTHS = {"ca_linh": [3.0, 12.0], "ca_loc": [8.0, 20.0], "ca_keo": [22.0, 28.0]}
FISH_SPAWN_X = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
FISH_SPAWN_DEPTHS = {"ca_linh": [5.0, 10.0], "ca_loc": [10.0, 16.0], "ca_keo": [24.0, 27.0]}
FISH_WEIGHTS = {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3}
FISH_YIELDS = {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, ctx=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.ctx = ctx or {}
        self.day = int(self.ctx.get("day", 1))
        self.phase_tick = 0
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))

        oxygen_max_s = float(self.ctx.get("oxygen_max_s", t["oxygen_max_s"]))
        self.oxygen_max = int(round(oxygen_max_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)

        self.hp_max = int(self.ctx.get("hp_max", t["hp_max"]))
        self.hp = p.get("hp", self.hp_max)

        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.random_fish = scenario.get("random_fish", True)

        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        if "fish" in scenario:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0)),
                          "age_ticks": int(f.get("age_ticks", 0))} for f in scenario["fish"]]
        elif not self.random_fish:
            self.fish = []
        elif isinstance(t.get("fish_initial"), list):
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0)),
                          "age_ticks": int(f.get("age_ticks", 0))} for f in t["fish_initial"]]
        else:
            count = int(t.get("fish_initial", 8))
            self.fish = []
            self._spawn_initial_fish(count)

        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])

        # quái vật (Cá Sấu) — tích hợp theo Ticket 4.5 & docs/plan/phase-2.md
        try:
            from .monsters import make_monsters
            self.monsters = make_monsters(tuning, scenario, self.day)
        except (ImportError, AttributeError):
            self.monsters = list(scenario.get("monsters", []))

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _spawn_initial_fish(self, count: int):
        spawn_x = self.t.get("fish_spawn_x", FISH_SPAWN_X)
        spawn_depths = self.t.get("fish_spawn_depths", FISH_SPAWN_DEPTHS)
        weights = self.t.get("fish_weights", FISH_WEIGHTS)
        clearance = float(self.t.get("fish_spawn_clearance", FISH_SPAWN_CLEARANCE))
        rng_spawn = self.rng.get("fish_spawn")
        rng_turn = self.rng.get("fish_turn")

        for _ in range(count):
            valid_pts = {}
            for kind, d_list in spawn_depths.items():
                pts = [(x, d) for x in spawn_x for d in d_list
                       if all(math.dist([x, d], f["pos"]) > clearance for f in self.fish)]
                if pts:
                    valid_pts[kind] = pts
            if not valid_pts:
                break
            total_w = sum(weights.get(k, 0.0) for k in valid_pts)
            if total_w <= 0:
                break
            r = rng_spawn.uniform(0, total_w)
            cum = 0.0
            chosen_k = list(valid_pts.keys())[-1]
            for k in sorted(valid_pts.keys()):
                cum += weights.get(k, 0.0)
                if r <= cum:
                    chosen_k = k
                    break
            pts = valid_pts[chosen_k]
            chosen_pos = pts[rng_spawn.randrange(len(pts))]
            heading = float(rng_turn.uniform(0, 360))
            fid = self.ids.new("F")
            self.fish.append({
                "id": fid, "kind": chosen_k,
                "pos": [float(chosen_pos[0]), float(chosen_pos[1])],
                "heading_deg": heading,
                "age_ticks": 0,
            })

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        def _m_id(x):
            return x["id"] if isinstance(x, dict) else x.id

        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [m.snapshot() if hasattr(m, "snapshot") else m for m in sort_by_id(self.monsters, key=_m_id)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép + dive/surface + oxy + ngạt/ngất
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp == 0:
                        lost = list(reversed(self.hold))
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 2.5 quái vật (Cá Sấu) — sau oxy/ngạt, trước interact (Ticket 4.5)
        try:
            from .monsters import step_monsters
            if step_monsters is not None and step_monsters(self, events):
                return events
        except (ImportError, AttributeError):
            pass

        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                rad = self.t["interact_radius"]
                candidates = [
                    (math.dist(self.pos, n["pos"]), id_key(n["id"]), n)
                    for n in self.nodes
                    if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= rad
                ]
                if candidates:
                    _, _, node = min(candidates, key=lambda x: (x[0], x[1]))
                    req = int(self.t["node_yield"])
                    free = int(self.t["hold_capacity"]) - len(self.hold)
                    if free < req:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": node["id"],
                            "required": req,
                            "free": free,
                        }))
                    else:
                        self.hold.extend([node["kind"]] * req)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": node["id"],
                            "kind": node["kind"],
                            "amount": req,
                        }))

        # 4. bắt cá (vị trí trước khi cá bơi theo Ticket 4.5)
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            rad = self.t["catch_radius"]
            candidates = [
                (math.dist(self.pos, f["pos"]), id_key(f["id"]), f)
                for f in self.fish
                if math.dist(self.pos, f["pos"]) <= rad
            ]
            if candidates:
                _, _, fish = min(candidates, key=lambda x: (x[0], x[1]))
                req = int(self.t.get("fish_yield", {}).get(fish["kind"], FISH_YIELDS.get(fish["kind"], 1)))
                free = int(self.t["hold_capacity"]) - len(self.hold)
                if free < req:
                    events.append(("hold_full", {
                        "action": "catch",
                        "fish_id": fish["id"],
                        "required": req,
                        "free": free,
                    }))
                else:
                    self.hold.extend([fish["kind"]] * req)
                    self.fish = [f for f in self.fish if f["id"] != fish["id"]]
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                    events.append(("fish_caught", {
                        "fish_id": fish["id"],
                        "kind": fish["kind"],
                        "yield": req,
                    }))

        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 6. cá bơi và sinh cá theo lịch (Ticket 4.5: chỉ khi còn giờ và có cấu hình v1.1)
        if self.random_fish and self.t.get("fish_speed") is not None:
            self._step_fish(events)

        return events

    def _step_fish(self, events):
        speed = float(self.t.get("fish_speed", FISH_SPEED))
        dist_tick = speed / TICK
        bx = self.t.get("fish_x", FISH_X)
        turn_ticks = int(self.t.get("fish_turn_ticks", FISH_TURN_TICKS))
        depths_map = self.t.get("fish_depths", FISH_DEPTHS)

        for f in self.fish:
            f["age_ticks"] = f.get("age_ticks", 0) + 1
            if f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = float(self.rng.get("fish_turn").uniform(0, 360))

            rad = math.radians(f["heading_deg"])
            vx = math.cos(rad)
            vd = math.sin(rad)
            x_new = f["pos"][0] + vx * dist_tick
            d_new = f["pos"][1] + vd * dist_tick
            bd = depths_map.get(f["kind"], [0.0, 30.0])

            # Phản xạ x
            if x_new < bx[0]:
                x_final = 2.0 * bx[0] - x_new
                vx = -vx
            elif x_new > bx[1]:
                x_final = 2.0 * bx[1] - x_new
                vx = -vx
            else:
                x_final = x_new

            # Phản xạ d
            if d_new < bd[0]:
                d_final = 2.0 * bd[0] - d_new
                vd = -vd
            elif d_new > bd[1]:
                d_final = 2.0 * bd[1] - d_new
                vd = -vd
            else:
                d_final = d_new

            x_final = max(bx[0], min(bx[1], x_final))
            d_final = max(bd[0], min(bd[1], d_final))
            f["pos"] = [x_final, d_final]
            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360

        # Sinh cá theo lịch
        spawn_ticks = int(self.t.get("fish_spawn_ticks", FISH_SPAWN_TICKS))
        max_fish = int(self.t.get("fish_max", FISH_MAX))
        if self.phase_tick > 0 and self.phase_tick % spawn_ticks == 0 and len(self.fish) < max_fish:
            spawn_x = self.t.get("fish_spawn_x", FISH_SPAWN_X)
            spawn_depths = self.t.get("fish_spawn_depths", FISH_SPAWN_DEPTHS)
            weights = self.t.get("fish_weights", FISH_WEIGHTS)
            clearance = float(self.t.get("fish_spawn_clearance", FISH_SPAWN_CLEARANCE))
            rng_spawn = self.rng.get("fish_spawn")
            rng_turn = self.rng.get("fish_turn")

            valid_pts = {}
            for kind, d_list in spawn_depths.items():
                pts = [(x, d) for x in spawn_x for d in d_list
                       if all(math.dist([x, d], f["pos"]) > clearance for f in self.fish)]
                if pts:
                    valid_pts[kind] = pts

            if valid_pts:
                total_w = sum(weights.get(k, 0.0) for k in valid_pts)
                if total_w > 0:
                    r = rng_spawn.uniform(0, total_w)
                    cum = 0.0
                    chosen_k = list(valid_pts.keys())[-1]
                    for k in sorted(valid_pts.keys()):
                        cum += weights.get(k, 0.0)
                        if r <= cum:
                            chosen_k = k
                            break
                    pts = valid_pts[chosen_k]
                    chosen_pos = pts[rng_spawn.randrange(len(pts))]
                    heading = float(rng_turn.uniform(0, 360))
                    fid = self.ids.new("F")
                    new_fish = {
                        "id": fid, "kind": chosen_k,
                        "pos": [float(chosen_pos[0]), float(chosen_pos[1])],
                        "heading_deg": heading,
                        "age_ticks": 0,
                    }
                    self.fish.append(new_fish)
                    events.append(("fish_spawned", {"id": fid, "kind": chosen_k, "pos": list(new_fish["pos"])}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
