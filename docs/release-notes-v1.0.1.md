# Quán Ăn Chợ Nổi — v1.0.1 (Nhóm T77) · bản vá sau giờ build

> **Bản nộp chính thức để chấm là [`v1.0.0`](release-notes-v1.0.0.md)** (tag `phase-4`, commit `8ca55cc`, công bố trước 3:00).
> `v1.0.1` làm **sau giờ build**, chỉ để demo và người chơi tải về dùng tiện. Gameplay, Test Contract v1.3, kho, JSONL không đổi.

## Điểm mới so với v1.0.0
- **Cửa sổ chơi có `--mode day`:** chơi liền **sáng → tối → Shop** qua 5 Ngày ngay trong trình duyệt (v1.0.0 chỉ có ở headless).
  - Màn **Shop**: phím **1** mua Bình oxy, **2** mua Áo phao, **Enter** đóng Shop sang Ngày kế (tự đóng sau 10 s).
  - HUD sáng: *"Má Tư cần: đã lấy/cần"* theo kế hoạch Ngày (không tính hàng ươn); HUD tối: món hôm nay.
  - Nâng cấp mua hôm nay có hiệu lực từ Ngày sau (Máu / oxy tối đa tăng).

## Cách chạy
Yêu cầu: Python 3.10+ (chỉ thư viện chuẩn), trình duyệt.
```bash
# giải nén chonoi-v1.0.1.zip (hoặc git clone repo)
cd K5-L3B-LAB-Day12-AI-SDLC-T77
python3 -m chonoi.live --mode day        # mở địa chỉ in ra; Windows: python thay cho python3
```
Điều khiển: WASD/mũi tên, E tương tác (hái / cập bến / nấu / bưng / phục vụ), Space bắt cá, 1/2/Enter ở Shop, Esc/P tạm dừng, H tương phản cao, R chơi lại.
Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (150 test OK).

## Giới hạn đã biết
- Chưa có menu chính và các màn DayIntro / EveningIntro / DayResult / Summary riêng (chuyển pha diễn ra ngay).
- Benchmark render bằng phần mềm; không làm mục mở rộng; 2 module test cũ của D còn tạm skip (fixture v1.1).
