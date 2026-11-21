"""Benchmark có render (Ticket-04 mục 1): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (độ tươi, cá bơi, Cá Sấu), Út Sen đứng yên ở bến. Mỗi khung: 1 bước sim (60 Hz) +
rasterize toàn cảnh vào framebuffer 1280×720 (RGB, chỉ thư viện chuẩn: nền, mặt nước, dải độ sâu, nút,
đàn cá, Cá Sấu, người chơi, HUD oxy/Máu/giỏ). Làm nóng 3 s rồi đo `--duration` giây (đồng hồ thực).
Xuất {avg_fps, p1_low_fps, frames, measured_s, load_ms}.

Giới hạn: render bằng phần mềm (không GPU/cửa sổ) để chạy được headless trên máy chấm; bản chơi thật vẽ
bằng canvas trong trình duyệt (`chonoi.live`).
"""

import argparse
import json
import math
import sys
import time

T0 = time.perf_counter()

from .contract import load_contract  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

W, H = 1280, 720
WARMUP_S = 3.0


class Frame:
    def __init__(self):
        self.buf = bytearray(W * H * 3)

    def clear(self, rgb):
        self.buf[:] = bytes(rgb) * (W * H)

    def rect(self, x, y, w, h, rgb):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(W, int(x + w)), min(H, int(y + h))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(rgb) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.buf[i:i + len(row)] = row

    def disc(self, cx, cy, r, rgb):
        for dy in range(-int(r), int(r) + 1):
            half = int(math.sqrt(max(0.0, r * r - dy * dy)))
            self.rect(cx - half, cy + dy, 2 * half + 1, 1, rgb)


def render(fr, snap, tuning):
    g = tuning["gather"]
    sx = W / g["bounds"]["x"][1]
    top = 120
    sd = (H - top - 60) / g["bounds"]["d"][1]
    fr.clear((207, 234, 245))
    fr.rect(0, top, W, H - top, (40, 110, 160))
    for d in range(5, 31, 5):
        fr.rect(0, top + d * sd, W, 1, (60, 130, 180))
    for n in snap["nodes"]:
        fr.disc(n["pos"][0] * sx, top + n["pos"][1] * sd, 8, (242, 194, 48) if n["ready"] else (120, 120, 90))
    for f in snap["fish"]:
        fr.disc(f["pos"][0] * sx, top + f["pos"][1] * sd, 9, (214, 230, 242))
    for m in snap.get("monsters", []):
        fr.disc(m["pos"][0] * sx, top + m["pos"][1] * sd, 16, (59, 31, 79))
    p = snap["player"]
    fr.disc(p["pos"][0] * sx, top + p["pos"][1] * sd, 12, (255, 138, 61))
    fr.rect(20, 20, 300 * p["oxygen_ticks"] / p["oxygen_max_ticks"], 20, (79, 195, 247))
    for i in range(p["hp"]):
        fr.rect(340 + i * 26, 20, 20, 20, (255, 107, 129))
    for i, it in enumerate(snap["hold"]):
        fr.rect(20 + i * 34, H - 50, 30, 30, (124, 154, 82))
        fr.rect(20 + i * 34, H - 22, 30 * it["fresh"] / 100, 4, (102, 187, 106))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chonoi.bench")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("--duration phải > 0\n")
        return 2
    tuning = load_contract()["tuning"]
    sess = Session("gather", tuning, {}, a.seed)  # mặc định: đứng ở bến, cá bơi, Cá Sấu M1, độ tươi
    idle = InputState((0.0, 0.0), {}, set())
    fr = Frame()
    times = []
    load_ms = None
    t_start = time.perf_counter()
    measuring = False
    t_measure = None
    while True:
        f0 = time.perf_counter()
        if sess.done:  # ca 180 s kết thúc trước khi đo xong -> dựng lại cảnh (cùng seed)
            sess = Session("gather", tuning, {}, a.seed)
        sess.step(idle)
        render(fr, sess.snapshot(), tuning)
        f1 = time.perf_counter()
        if load_ms is None:
            load_ms = round((f1 - T0) * 1000)
        if not measuring and f1 - t_start >= WARMUP_S:
            measuring, t_measure = True, f1
            continue
        if measuring:
            times.append(f1 - f0)
            if f1 - t_measure >= a.duration:
                break
    measured_s = time.perf_counter() - t_measure
    frames = len(times)
    k = max(1, math.ceil(0.01 * frames))
    slow = sorted(times, reverse=True)[:k]
    out = {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(k / sum(slow), 2),
           "frames": frames, "measured_s": round(measured_s, 3), "load_ms": load_ms}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
