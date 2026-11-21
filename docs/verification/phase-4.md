# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3)

> Kiểm chứng trên commit gắn tag `phase-4` = Release `v1.0.0`. Lệnh test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
> → [test-output.txt](../proof/phase-4/test-output.txt).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 Contract v1.3 khai `bench_cmd`, `soak_cmd`; gameplay v1.2 | `test_p4_c.test_p4_01_*` | [game.contract.json](../../game.contract.json) | Đạt |
| AC-P4-02 `bench_cmd --seed 42 --duration 30` tạo `bench.json` đủ 5 trường | Chạy đủ 30 s + `test_p4_03_*` | [bench.json](../proof/phase-4/bench.json): avg 360.33 FPS, 1% low 171.68, 10811 khung / 30.003 s, load 30 ms | Đạt (vượt mốc 60 / 30 / 10 s) |
| AC-P4-03 `soak_cmd --seed 7 --days 10`: `days_completed = days`, `crashes = 0`, kết quả tất định | Chạy 10 Ngày + `test_p4_02_*` (chạy 2 lần so `results`) | [soak.json](../proof/phase-4/soak.json) | Đạt |
| AC-P4-04 Ba cảnh báo có chữ + biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) | `chonoi/web/index.html` hàm `alerts()` — đọc snapshot | — | Đạt về mã; **chưa có ảnh chụp chơi thử** |
| AC-P4-05 Chế độ tương phản cao (H / `?contrast=high`) | Như trên | — | Đạt về mã; **chưa chơi thử cả ba cảnh báo ở chế độ này** |
| AC-P4-06 Clone sạch chạy ≤ 3 lệnh; README đủ môi trường/điều khiển/test/headless/bench/soak | README mục "Chạy game"; zip `git archive` của commit tag | [README](../../README.md) | Đạt (thử từ thư mục sạch trên Windows, chưa thử macOS/Linux) |
| AC-P4-07 CHANGELOG theo phase, release notes, LICENSE, CREDITS | — | [CHANGELOG](../../CHANGELOG.md), [release notes](../release-notes-v1.0.0.md), [LICENSE](../../LICENSE), [CREDITS](../../CREDITS.md) | Đạt |
| AC-P4-08 Regression P1–P3 | Toàn bộ suite | test-output | Đạt cho test chạy; **2 module của D (`test_gather_rules`, `test_quan_rules`) còn skip** (fixture v1.1) |
| AC-P4-09 Tag `phase-4` + Release `v1.0.0` cùng commit trên main | `git ls-remote --tags` | — | Tag do C đẩy; **Release tạo trên web GitHub** (máy không có `gh`) |
| AC-P4-10 Retro rà hành động P2, phản tư đủ người | [retro.md](../retro.md), `docs/members/*.md` | — | Retro đạt; phản tư: A, D có; C nháp; **B chưa có** |

## Giới hạn
Vòng ngày + Shop chỉ ở headless (chưa có menu/DayIntro/Summary trong cửa sổ). Benchmark render phần mềm. Không làm mở rộng.
