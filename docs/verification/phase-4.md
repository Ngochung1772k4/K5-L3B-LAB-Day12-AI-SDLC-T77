# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3)

> Kiểm chứng trên commit gắn tag `phase-4` = Release `v1.0.0`. Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
> → [test-output.txt](../proof/phase-4/test-output.txt): **150 test OK**, 2 module cũ của D skip.

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 Contract v1.3 khai `bench_cmd`, `soak_cmd`; gameplay v1.2 | `test_p4_c.test_p4_01_*` | [game.contract.json](../../game.contract.json) | Đạt |
| AC-P4-02 `bench_cmd --seed 42 --duration 30` tạo `bench.json` đủ 5 trường | Chạy đủ 30 s + `test_p4_03_*` | [bench.json](../proof/phase-4/bench.json): avg 360.33 FPS, 1% low 171.68, 10811 khung / 30.003 s, load 30 ms | Đạt (vượt mốc 60 / 30 / 10 s) |
| AC-P4-03 `soak_cmd --seed 7 --days 10`: `days_completed = days`, `crashes = 0`, kết quả tất định | Chạy 10 Ngày + `test_p4_02_*` (chạy 2 lần so `results`) | [soak.json](../proof/phase-4/soak.json) | Đạt |
| AC-P4-04 Ba cảnh báo có chữ + biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) | `chonoi/web/index.html` hàm `alerts()` — đọc snapshot | — | Đạt về mã; **chưa có ảnh chụp chơi thử** |
| AC-P4-05 Chế độ tương phản cao (H / `?contrast=high`) | Như trên | — | Đạt về mã; **chưa chơi thử cả ba cảnh báo ở chế độ này** |
| AC-P4-06 Clone sạch chạy ≤ 3 lệnh; README đủ môi trường/điều khiển/test/headless/bench/soak | README mục "Chạy game"; zip `git archive` của commit tag | [README](../../README.md) | Đạt — clone sạch từ GitHub (commit 18e7730): headless day + soak chạy; `chonoi.live` lỗi in tiếng Việt khi stdout không UTF-8 (Windows) → sửa `live.py` ép UTF-8, chạy lại gather/quan khởi động OK. Chưa thử macOS/Linux |
| AC-P4-07 CHANGELOG theo phase, release notes, LICENSE, CREDITS | — | [CHANGELOG](../../CHANGELOG.md), [release notes](../release-notes-v1.0.0.md), [LICENSE](../../LICENSE), [CREDITS](../../CREDITS.md) | Đạt |
| AC-P4-08 Regression P1–P3 | Toàn bộ suite, gồm 4 file test P3 mới của D (`test_p3_*_d.py`, 53 test) | test-output | Đạt; 2 module P1 cũ của D (`test_gather_rules`, `test_quan_rules`) còn skip (fixture v1.1) |
| AC-P4-09 Tag `phase-4` + Release `v1.0.0` cùng commit trên main | `git ls-remote --tags` | — | Tag do C đẩy; **Release tạo trên web GitHub** (máy không có `gh`) |
| AC-P4-10 Retro rà hành động P2, phản tư đủ người | [retro.md](../retro.md), `docs/members/*.md` | — | Retro đạt; phản tư: A, D có; C nháp; **B chưa có** |

## Giới hạn
Vòng ngày + Shop chỉ ở headless (chưa có menu/DayIntro/Summary trong cửa sổ). Benchmark render phần mềm. Không làm mở rộng.

## Thay đổi theo QA của D (nhánh `d/phase-3-qa-uscalurn`, push 11:43)
4 test P3 của D đỏ trên code C → xử lý: (1) 3 test đòi `fresh` trong JSONL khớp đúng file kho → **sửa code**: `jsonl.py` không làm tròn `fresh` (tránh 29.9996 hiện thành 30.0); (2) giữ lại khi ươn phải **lần lượt từng đơn** → **sửa code** `quan._rereserve`; (3) test đòi version đúng "1.2" → đổi test chấp nhận 1.2/1.3 (P4 chỉ thêm bench/soak). Bỏ file rác `kho.json` ở gốc khỏi merge.
