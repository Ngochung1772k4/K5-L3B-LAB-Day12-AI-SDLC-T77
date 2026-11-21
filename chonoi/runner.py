"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    if mode == "day":
        return DaySim(tuning, scenario, seed, days)
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end.

    v1.1: pause chung cho mọi mode (Ticket-02 mục 4.2) — bước vào/đang pause chỉ tăng tick ngoài;
    sim_tick, phase_tick, timer đứng yên. Mode day: vỏ event thêm `day`, dòng end thêm `days_completed`.
    """

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _phase_tick(self):
        return self.sim.phase_tick if self.mode == "day" else self.sim_tick

    def _common(self, state):
        sim = self.sim
        vals = sim.common() if self.mode == "day" else {"money": sim.money, "earned": sim.earned,
                                                        "reputation": sim.reputation}
        mult = self.tuning["score"]["reputation_multiplier"]
        return {
            "type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode, "phase": sim.phase,
            "phase_tick": self._phase_tick(), "state": state, "time_left_ticks": sim.time_left_ticks,
            "money": vals["money"], "earned": vals["earned"], "reputation": vals["reputation"],
            "score": vals["earned"] + mult * math.floor(vals["reputation"]),
        }

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if self.paused else "playing")
        s = self._common(state)
        s.update(self.sim.snapshot())
        return s

    def _row(self, ev):
        if len(ev) == 4:  # day: (name, data, phase, day)
            name, data, phase, day = ev
            return {"type": "event", "tick": self.tick, "phase": phase, "day": day, "name": name, "data": data}
        name, data = ev
        return {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}

    def initial_rows(self) -> list:
        """Event ở tick 0 (day: day_start → day_plan → phase_start), ghi trước snapshot tick 0."""
        return [self._row(e) for e in getattr(self.sim, "initial_events", [])]

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if inp.pressed("pause"):  # xét cạnh pause trước
            self.paused = not self.paused
            ev = ("paused" if self.paused else "resumed", {})
            rows.append(self._row(ev + (self.sim.phase, self.sim.day) if self.mode == "day" else ev))
            if self.paused:
                return rows
        elif self.paused:
            return rows  # bỏ qua cạnh hành động và buy
        self.sim_tick += 1
        rows.extend(self._row(e) for e in self.sim.step(inp))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        c = self._common("")
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": c["money"], "earned": c["earned"], "reputation": c["reputation"], "score": c["score"]}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            before = (getattr(sess.sim, "day", None), sess.sim.phase)
            for row in sess.step(inp):
                w.write(row)
            changed = (getattr(sess.sim, "day", None), sess.sim.phase) != before  # snapshot đổi pha (v1.1)
            if sess.tick % snapshot_every == 0 or sess.done or changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
