"""Buổi tối — Mở Quán (PRD-0 mục F, Quán).

Nhóm B (PhamMinhDuc) dựng khách/bếp/bàn/tiền; C (Integrator) sửa lại cho đúng thứ tự một bước và `data`
sự kiện theo hợp đồng (docs/contracts/README.md). Thứ tự một bước:
  1. tăng phase_tick, giảm timer ca / nấu / ăn / kiên nhẫn; ready_ticks chỉ tăng cho bếp đã ready đầu bước
  2. bếp theo id: nấu xong -> ready (ready_ticks = 0), dish_ready
  3. di chuyển rồi tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id)
  4. khách theo id bàn: ăn xong trả tiền; còn giờ thì khách chờ hết kiên nhẫn rời; hết ca thì dọn rồi quan_end
  5. còn giờ: lượt khách theo lịch (first_customer_tick + k * interval)
"""

import math

from ..ids import id_key, sort_by_id
from ..items import UNITS, decay, freshest, from_dict, is_spoiled, sorted_by_id, to_list, units_per_tick
from ..scenario import validate_quan_links
from .ramp import ramp_velocity

TICK = 60.0


def _ticks(seconds):
    return int(round(seconds * TICK))


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, ctx=None):
        t = tuning["quan"]
        ctx = ctx or {}  # day truyền {"day", "dishes", "money", "earned", "reputation"}; mode độc lập: None
        # trong day chỉ gọi món của kế hoạch; quán chạy riêng dùng cả thực đơn
        self.dishes = sorted(ctx["dishes"]) if "dishes" in ctx else sorted(tuning["menu"])
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # v1.2: kho VẬT LÝ là mảng cá thể {id, kind, u} (gồm cả hàng đang giữ và hàng ươn)
        self.tuning = tuning
        if inventory is not None:
            self.stock = [dict(it) for it in inventory]
        else:
            self.stock = [from_dict(it) for it in scenario.get("stock", [])]
        for it in self.stock:
            ids.reserve(it["id"])
        self._decay = units_per_tick(tuning["freshness"]["quan_decay_per_s"])
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = ctx.get("reputation", scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.patience_full = _ticks(t["patience_s"])
        self.eat_full = _ticks(t["eat_s"])
        self.interval = _ticks(t["customer_interval_s"])
        self.phase_tick = 0  # lịch khách tính theo phase_tick, kể cả khi rút ngắn ca
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        reserved = validate_quan_links(scenario, tuning, self.stock)
        self.customers = [dict(c, reserved=reserved[c["id"]]) for c in scenario.get("customers", [])]
        for c in self.customers:
            ids.reserve(c["id"])
            c.setdefault("state", "waiting")
            c.setdefault("order_status", "reserved")
            c.setdefault("patience_ticks_left", self.patience_full)
            c.setdefault("eat_ticks_left", 0)
            c.setdefault("order_tick", 0)
            c.setdefault("base_price", self.menu[c["dish_id"]]["price"])
            c.setdefault("tip", 0)
        self.money = ctx.get("money", 0)
        self.earned = ctx.get("earned", 0)
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    CUSTOMER_FIELDS = ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                       "eat_ticks_left", "order_status", "reserved", "base_price", "tip")

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": to_list(sorted_by_id(self.stock)),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{k: c[k] for k in self.CUSTOMER_FIELDS} for c in sort_by_id(self.customers)],
        }

    # --- một bước -------------------------------------------------------------------
    def step(self, inp):
        ev = []
        # 1. đồng hồ và timer
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 1b. v1.2: hao tươi kho thô, phát hết spoiled theo id, rồi xử lý giữ chỗ bị ươn
        spoiled = decay(self.stock, self._decay, self.tuning, "stock")
        ev.extend(spoiled)
        if spoiled:
            self._rereserve({d["item_id"] for _, d in spoiled})
        # 2. bếp theo id: nấu xong -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                ev.append(("dish_ready", self._dish_data(s)))
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(ev)
        # 4. khách theo id bàn
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:
                    self._pay(c, "finished_eating", ev)
                elif closing:
                    self._pay(c, "closing", ev)
            elif closing:
                self._leave(c, "closing", ev)
            elif c["patience_ticks_left"] == 0:
                self._leave(c, "patience", ev)
        if closing:
            self.done = True
            self.reason = "time"
            ev.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                    "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return ev
        # 5. lượt khách theo lịch
        first = self.t["first_customer_tick"]
        pt = self.phase_tick
        if self.random_customers and pt >= first and (pt - first) % self.interval == 0:
            self._spawn(ev)
        return ev

    # --- tương tác ------------------------------------------------------------------
    def _interact(self, ev):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda x: x[:3])
        # đối tượng được chọn không tương tác được -> bỏ lượt (không thử đối tượng khác)
        if kind == "stove":
            self._interact_stove(obj, ev)
        else:
            self._interact_table(obj, ev)

    def _interact_stove(self, s, ev):
        if s["state"] == "idle":
            orders = [c for c in self.customers if c["order_status"] == "reserved"]
            if not orders:
                return
            c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            used_ids = set(c["reserved"])  # tiêu đúng các id đang giữ
            used = [it for it in self.stock if it["id"] in used_ids]
            self.stock = [it for it in self.stock if it["id"] not in used_ids]
            used.sort(key=lambda it: (it["kind"], id_key(it["id"])))
            items = to_list(used)
            # chốt giá theo tươi: floor(giá × trung bình fresh / 100), tính bằng số nguyên u = fresh × 240
            price = self.menu[c["dish_id"]]["price"] * sum(it["u"] for it in used) // (len(used) * 100 * UNITS)
            c.update(reserved=[], order_status="assigned", base_price=price)
            s.update(state="cooking", dish={"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price},
                     cook_ticks_left=_ticks(self.menu[c["dish_id"]]["cook_s"]), ready_ticks=0)
            ev.append(("cook_started", dict(self._dish_data(s), items=items, base_price=price)))
        elif s["state"] == "ready" and self.hand is None:
            data = self._dish_data(s)
            self.hand = s["dish"]
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
            ev.append(("dish_picked", data))

    def _interact_table(self, tb, ev):
        if self.hand is None:
            return
        c = next((x for x in self.customers if x["table_id"] == tb["id"]), None)
        if c is None or c["state"] != "waiting" or c["id"] != self.hand["order_id"]:
            return
        price = self.hand["base_price"]
        ratio = c["patience_ticks_left"] / self.patience_full
        tip = math.floor(price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_full, base_price=price, tip=tip)
        self.hand = None
        ev.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                              "patience_ticks_left": c["patience_ticks_left"], "base_price": price, "tip": tip}))

    # --- khách rời bàn ----------------------------------------------------------------
    def _pay(self, c, reason, ev):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:  # boa dương cộng uy tín khi thu tiền
            self._add_reputation(self.t["tip_reputation"])
        self.customers.remove(c)
        ev.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                            "tip": c["tip"], "amount": amount, "reason": reason}))

    def _leave(self, c, reason, ev):
        if reason == "patience":  # đóng ca không trừ uy tín
            self._add_reputation(self.t["left_reputation_delta"])
        # nhả phần giữ (chỉ bỏ giữ, stock vật lý không đổi); bỏ món của đơn trên bếp / tay
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers.remove(c)
        ev.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                     "reputation": self.reputation}))

    def _add_reputation(self, delta):
        self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta))

    # --- khách mới --------------------------------------------------------------------
    def _spawn(self, ev):
        occupied = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in occupied]  # self.tables đã sắp theo id
        if not free:
            return  # không còn bàn: bỏ lượt
        table = free[0]
        cookable = [d for d in self.dishes if self._pick(d) is not None]
        if not cookable:
            ev.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_dish").choice(cookable)
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_full, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": self._pick(dish_id),
            "base_price": self.menu[dish_id]["price"], "tip": 0,
        })
        ev.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # --- giữ chỗ theo id (v1.2) -----------------------------------------------------------
    def _available(self):
        held = {i for c in self.customers for i in c["reserved"]}
        return [it for it in self.stock if it["id"] not in held and not is_spoiled(it, self.tuning)]

    def _pick(self, dish_id, pool=None):
        """Mỗi loại trong công thức lấy cá thể khả dụng tươi nhất (hòa theo id); thiếu -> None."""
        pool = self._available() if pool is None else pool
        out = []
        for kind, n in sorted(self.menu[dish_id]["recipe"].items()):
            cand = freshest([it for it in pool if it["kind"] == kind])
            if len(cand) < n:
                return None
            out.extend(it["id"] for it in cand[:n])
        return out

    def _rereserve(self, spoiled_ids):
        """Đơn có cá thể vừa ươn: nhả toàn bộ phần giữ, thử giữ lại đúng một lần (theo order_tick rồi id bàn)."""
        hit = [c for c in self.customers if c["order_status"] == "reserved" and spoiled_ids & set(c["reserved"])]
        # lần lượt từng đơn theo (order_tick, id bàn): nhả phần giữ của đơn đó rồi thử giữ lại ngay một lần
        # (đơn sau chưa nhả thì đơn trước không lấy được hàng của nó — theo test QA của D, Ticket-03)
        for c in sorted(hit, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = []
            got = self._pick(c["dish_id"])
            if got is None:
                c["order_status"] = "unfulfillable"  # khách chờ tới hạn
            else:
                c["reserved"] = got

    @staticmethod
    def _dish_data(s):
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
