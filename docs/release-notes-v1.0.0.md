# Quán Ăn Chợ Nổi — v1.0.0 (Nhóm T77)

Game quản lý quán ăn miền Tây: sáng Út Sen lặn bắt cá, hái rau trên sông; tối nấu và phục vụ khách trên nhà bè; cuối ngày mua nâng cấp. Test Contract **v1.3**.

## Điểm mới qua 4 phase
- **P1 (PRD-0):** lặn & hái (oxy, ngạt, Máu, ngất, hái nút, bắt cá), mở quán (khách, giữ chỗ, bếp, bưng, phục vụ, boa, uy tín), bàn giao qua file kho.
- **P2 (v1.1):** số chuẩn, 6 nguyên liệu/6 món, 2 bếp/4 bàn, cá bơi & sinh theo lịch, Cá Sấu Năm Chèo, vòng 5 Ngày (`--mode day`), Shop nâng cấp oxy/Máu, pause.
- **P3 (v1.2):** kho cá thể có độ tươi, hàng ươn, giữ chỗ theo id, giá theo độ tươi, HUD độ tươi.
- **P4 (v1.3):** benchmark có render, soak 10 Ngày, cảnh báo biểu tượng + tương phản cao, đóng gói.

## Cách chạy
Yêu cầu: Python 3.10+ (chỉ thư viện chuẩn), trình duyệt.
```bash
# từ bản đóng gói chonoi-v1.0.0.zip (hoặc git clone repo)
cd K5-L3B-LAB-Day12-AI-SDLC-T77
python3 -m chonoi.live --mode gather --inventory-out kho.json   # sáng (mở địa chỉ in ra)
python3 -m chonoi.live --mode quan --inventory kho.json         # tối
```
Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` · Bench: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` · Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.
Điều khiển: WASD/mũi tên, E tương tác, Space bắt cá, Esc/P tạm dừng, H tương phản cao, R chơi lại.

## Số đo (máy dev)
Bench 30 s: avg 360 FPS, 1% low 172 FPS, load 30 ms (render phần mềm). Soak 10 Ngày: 10/10 Ngày, 0 crash.

## Giới hạn đã biết
- Cửa sổ chơi (`chonoi.live`) chơi riêng từng buổi gather / quán; vòng **5 Ngày + Shop chỉ có ở headless** (`--mode day`), chưa có menu chính, DayIntro/EveningIntro/DayResult/Summary.
- Benchmark render bằng phần mềm (framebuffer), không đo FPS của trình duyệt.
- Bot soak không điều khiển (earned = 0) — kiểm độ bền, không kiểm chiến thuật.
- Không làm mục mở rộng (dòng lũ, khách đặt trước, leaderboard, phụ đề SFX…).
- 2 module test của D (`test_gather_rules`, `test_quan_rules`) còn tạm skip do fixture v1.1 (xem verification P3/P4).
