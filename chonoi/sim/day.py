"""Vòng Ngày (Ticket-02 mục 2, 4.4, 4.5): day_start → day_plan → gather → quan → Shop → Ngày kế.

- Tiền, earned, uy tín, cấp đã mua giữ qua Ngày; giỏ làm mới, kho dư bỏ sau Shop.
- `active_upgrades` chỉ sao từ cấp đã mua khi DỰNG Ngày mới (cấp mua hôm nay có hiệu lực từ Ngày kế).
- Pha mới dựng ngay tick pha cũ kết thúc (phase_tick = 0), chạy gameplay từ bước sau.
- step() trả list (name, data, phase, day): event kết thúc mang pha cũ, event đổi pha mang pha mới.
"""

import copy

from ..contract import plan_ingredients
from ..ids import IdAllocator
from ..items import sorted_by_id, to_list
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim

SHOP_ITEMS = ("oxygen", "hp")  # lõi; weapon/net là mở rộng (chưa bật)


class ShopSim:
    """Pha Shop: mua nâng cấp bằng `buy`, đóng bằng `shop_done` hoặc sau max_ticks bước hoạt động."""

    phase = "shop"

    def __init__(self, day_sim, stock):
        self.d = day_sim
        self.stock = stock  # kho dư từ ca (chỉ hiển thị, bỏ khi đóng Shop)
        self.time_left_ticks = int(day_sim.tuning["shop"]["max_ticks"])
        self.done = False
        self.reason = None

    def step(self, inp):
        ev = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy:  # một buy trước cạnh shop_done, kể cả bước cuối
            ev.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            self.done, self.reason = True, "done"
        elif self.time_left_ticks == 0:
            self.done, self.reason = True, "time"
        if self.done:
            ev.append(("shop_end", {"reason": self.reason}))
        return ev

    def _buy(self, action):
        d = self.d
        if action not in SHOP_ITEMS:
            return "buy_failed", {"action": action, "reason": "unknown"}
        levels = d.tuning["shop"]["upgrades"][action]
        level = d.upgrades.get(action, 0) + 1
        if level > len(levels):
            return "buy_failed", {"action": action, "reason": "max_level"}
        price = levels[level - 1]["price"]
        if d.money < price:  # đủ đúng giá vẫn mua được
            return "buy_failed", {"action": action, "reason": "funds"}
        d.money -= price  # trừ money, giữ earned và điểm
        d.upgrades[action] = level
        return "bought", {"upgrade": action, "level": level, "price": price, "money": d.money}

    def snapshot(self):
        return {"stock": to_list(sorted_by_id(self.stock))}  # hàng thô ở Shop không hao tươi


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.rng = Streams(seed)
        self.ids = IdAllocator()
        self.days = days
        db = scenario.get("day", {})
        self.money = db.get("money", 0)
        self.earned = db.get("earned", 0)
        self.reputation = db.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(db.get("upgrades", {}))  # cấp đã mua
        self.active_upgrades = {}
        self.plan = self._build_plan(db.get("day_plan"))
        self.day = 1
        self.days_completed = 0
        self.done = False
        self.reason = None
        self.cur = None
        self.phase_tick = 0
        self.initial_events = []
        self._start_day(self.initial_events)

    # --- kế hoạch -----------------------------------------------------------------
    def _build_plan(self, overrides):
        plan = {p["day"]: {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
                for p in self.tuning["day_plan"]}
        for p in overrides or []:
            plan[p["day"]] = {"dishes": dict(p["dishes"]),
                              "ingredients": plan_ingredients(p["dishes"], self.tuning["menu"])}
        return plan

    # --- đổi pha ------------------------------------------------------------------
    @property
    def phase(self):
        return self.cur.phase

    def _ev(self, out, name, data):
        out.append((name, data, self.cur.phase if self.cur else "gather", self.day))

    def _start_day(self, out):
        self.active_upgrades = dict(self.upgrades)
        g = self.tuning["gather"]
        ctx = {"day": self.day, "hp_max": g["hp_max"], "oxygen_max_s": g["oxygen_max_s"]}
        for uid, key in (("hp", "hp_max"), ("oxygen", "oxygen_max_s")):
            lv = self.active_upgrades.get(uid, 0)
            if lv:
                ctx[key] = self.tuning["shop"]["upgrades"][uid][lv - 1][key]
        out.append(("day_start", {}, "gather", self.day))
        p = self.plan[self.day]
        out.append(("day_plan", {"dishes": p["dishes"], "ingredients": p["ingredients"]}, "gather", self.day))
        gsc = copy.deepcopy(self.scenario.get("gather", {}))
        if self.day > 1 and gsc.get("hold"):  # Ngày kế: id mới theo thứ tự mảng, kind/fresh ban đầu
            gsc["hold"] = [dict(it, id=self.ids.new("I")) for it in gsc["hold"]]
        self.cur = GatherSim(self.tuning, gsc, self.rng, self.ids, ctx=ctx)
        self.phase_tick = 0
        out.append(("phase_start", {}, "gather", self.day))

    def _start_quan(self, out, items):
        ctx = {"day": self.day, "dishes": list(self.plan[self.day]["dishes"]),
               "money": self.money, "earned": self.earned, "reputation": self.reputation}
        self.cur = QuanSim(self.tuning, copy.deepcopy(self.scenario.get("quan", {})), self.rng, self.ids,
                           inventory=items, ctx=ctx)
        self.phase_tick = 0
        self._ev(out, "phase_start", {})

    def _start_shop(self, out, stock):
        self.cur = ShopSim(self, stock)
        self.phase_tick = 0
        self._ev(out, "phase_start", {})

    # --- một bước -------------------------------------------------------------------
    def step(self, inp):
        out = []
        self.phase_tick += 1
        for name, data in self.cur.step(inp):
            self._ev(out, name, data)  # mang pha hiện tại (pha cũ nếu là event kết thúc)
        if not self.cur.done:
            return out
        if isinstance(self.cur, GatherSim):
            # v1.2: bàn giao cá thể cùng tick, không hao thêm (ngất: giỏ đã rỗng)
            self._start_quan(out, [dict(it) for it in self.cur.hold])
        elif isinstance(self.cur, QuanSim):
            q = self.cur
            self.money, self.earned, self.reputation = q.money, q.earned, q.reputation
            self._start_shop(out, [dict(it) for it in q.stock])
        else:  # Shop đóng: Ngày hoàn tất
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self._start_day(out)
        return out

    # --- snapshot -------------------------------------------------------------------
    def common(self):
        live = self.cur if isinstance(self.cur, QuanSim) else self
        return {"money": live.money, "earned": live.earned, "reputation": live.reputation}

    def snapshot(self):
        p = self.plan[self.day]
        s = {"day": self.day, "day_plan": {"dishes": p["dishes"], "ingredients": p["ingredients"]},
             "upgrades": dict(sorted(self.upgrades.items())),
             "active_upgrades": dict(sorted(self.active_upgrades.items()))}
        s.update(self.cur.snapshot())
        return s

    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks
