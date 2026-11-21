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
from .fish import initial_fish, spawn_one, swim
from .monsters import make_monsters, step_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, ctx=None):
        t = tuning["gather"]
        ctx = ctx or {}  # day truyền {"day", "hp_max", "oxygen_max_s"}; mode độc lập: None
        self.day = ctx.get("day", 1)
        self.hp_max = ctx.get("hp_max", t["hp_max"])
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(ctx.get("oxygen_max_s", t["oxygen_max_s"]) * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        # Cá Sấu
        self.monsters = make_monsters(tuning, scenario, self.day)
        self.phase_tick = 0
        self.fish_active = scenario.get("random_fish", True)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = initial_fish(t, streams.get("fish_spawn"), ids)  # v1.1: 8 đàn theo seed (sim/fish.py)
        else:
            src_fish = []
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
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
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f.get("age_ticks", 0)}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in self.monsters],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
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

        # 2b. Cá Sấu: di chuyển, xét hit (sau oxy/ngạt, trước interact)
        if self.monsters:
            if step_monsters(self, events):
                return events  # vừa ngất do quái

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

        # 4. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            rad = self.t["catch_radius"]
            candidates = [
                (math.dist(self.pos, f["pos"]), id_key(f["id"]), f)
                for f in self.fish
                if math.dist(self.pos, f["pos"]) <= rad
            ]
            if candidates:
                _, _, fish = min(candidates, key=lambda x: (x[0], x[1]))
                req = int(self.t["fish_yield"][fish["kind"]])
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
        # 6. còn giờ: cá bơi rồi sinh theo lịch (v1.1, Ticket 1.1 / 4.5); random_fish=false -> cá đứng yên
        if self.fish_active:
            swim(self.t, self.fish, self.rng.get("fish_turn"))
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0 and len(self.fish) < self.t["fish_max"]:
                f = spawn_one(self.t, self.fish, self.rng.get("fish_spawn"), self.ids)
                if f is not None:
                    self.fish.append(f)  # tham gia từ bước sau
                    events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": f["pos"]}))
        return events

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
