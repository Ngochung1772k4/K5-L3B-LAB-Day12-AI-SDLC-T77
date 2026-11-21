# Ma trận truy vết Phase 2 (Ticket-02, Test Contract v1.1)

> Kiểm chứng trên commit gắn tag `phase-2`. Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
> → [test-output.txt](../proof/phase-2/test-output.txt) (**142 test, OK** — gồm 67 test P1 của D).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 v1.1, 6 kind, 6 món, B2, T2–T4, N5/N6 | `test_day_shop_c.test_p2_01_contract_and_data`; `contract.py` kiểm khóa + day_plan khớp công thức | test-output | Đạt |
| AC-P2-02 8 đàn đầu ca ở 8 điểm khác nhau; bơi 1.5 m/s, đổi hướng bước 120, phản xạ mép | `test_p2_02_initial_fish_*`, `test_fish_c.FishSwim` | test-output | Đạt |
| AC-P2-03 Sinh tại phase_tick 360·k, trần 12, `fish_spawned` | `test_fish_c.test_p2_03_spawn_every_360_up_to_cap` | test-output; [day1.jsonl](../proof/phase-2/day1.jsonl) | Đạt |
| AC-P2-04 Cá Sấu patrol/chase theo ngưỡng; M2 từ Ngày 3 | `test_monsters_c.test_p2_04_*` | test-output | Đạt (chưa có test riêng cho M2 xuất hiện ở Ngày 3 trong `day`) |
| AC-P2-05 `monster_hit`: −1 Máu, mất floor(n/2) LIFO, bất tử 90, recoil 60 | `test_p2_05_hit_loses_half_lifo_invuln_recoil` | test-output | Đạt |
| AC-P2-06 Ngất do quái → `faint cause monster`, kho rỗng | `test_p2_06_faint_by_monster` | test-output | Đạt |
| AC-P2-07 Smoke tích hợp gather → quan (số chuẩn, kind mới) | 2 lệnh headless seed 42 | [integration.txt](../proof/phase-2/integration.txt), `integration-*.json(l)` | Đạt |
| AC-P2-08 `day --days 1`: `day_start → day_plan → phase_start`, kế hoạch D1, đổi pha cùng tick | `test_p2_08_*` | test-output; [day1.jsonl](../proof/phase-2/day1.jsonl) | Đạt |
| AC-P2-09 Quán trong day chỉ gọi món kế hoạch | `test_p2_09_quan_in_day_only_plan_dishes` | test-output | Đạt |
| AC-P2-10 Shop: `bought` / `buy_failed` (funds, max_level, unknown), trừ money giữ earned, đóng `shop_done` / 600 tick | `test_p2_10_*` | test-output; [day-upgrade.jsonl](../proof/phase-2/day-upgrade.jsonl) | Đạt |
| AC-P2-11 Cấp oxy/hp hiệu lực từ Ngày kế | `test_p2_10_11_*`, `test_p2_10_max_level_and_oxygen_upgrade` | day-upgrade.jsonl (tick 6: `active_upgrades {"hp":1}`, `hp_max 4`) | Đạt |
| AC-P2-12 Pause: chỉ tick ngoài tăng, `paused`/`resumed`, `state paused` | `test_p2_12_pause_freezes_sim` | test-output | Đạt (headless); UI có Esc/P + màn mờ |
| AC-P2-13 `--days 5` → `days_complete`, `days_completed 5`; 1 Ngày ≤ 20 s | `test_p2_13_five_days_complete_and_fast` | [day5-end.json](../proof/phase-2/day5-end.json); [day1-time.txt](../proof/phase-2/day1-time.txt) 0.6 s, [day5-time.txt](../proof/phase-2/day5-time.txt) 3.2 s | Đạt |
| AC-P2-14 Regression P1 với số chuẩn | Toàn bộ test P1 (của A, C, D) chạy lại trên v1.1 | test-output | Đạt — 5 test đổi có lý do (xem dưới) |
| Menu chính, DayIntro / EveningIntro / DayResult / Summary, HUD đủ mục | — | — | **Chưa đạt** (chưa làm UI vòng ngày; `chonoi.live` chưa có `--mode day`) |

## Test thay đổi vì luật mới (lý do)
- `test_smoke_p1.test_gather_snapshot_has_gather_fields`: 6 đàn cố định → `fish_initial` (8) đàn sinh theo seed.
- `test_smoke_p1.test_con_03_*`: `day` không còn bị từ chối (v1.1); thêm kiểm `--days` sai miền / sai mode → 2.
- `test_quan_rules_c.test_ac13_*`: có 4 bàn nên khách 2 vào T2 ở tick 1020 (trước bỏ lượt vì chỉ có T1).
- `test_gather_unit_a` (fixture bắt cá): thêm `random_fish:false` — v1.1 cá khai trong scenario vẫn bơi khi cờ bật.
- `test_quan_rules` (D) `test_reservations_never_exceed_*`: 4 bàn nên lượt 2 có bàn trống nhưng kho đã giữ hết → `no_dish` (P1 chỉ T1 → bỏ lượt).
- `test_team_check.test_template_is_rejected`: starter đọc TEAM.md của repo và đòi bị từ chối (bản mẫu). Fork đã điền đủ → tách thành test bản mẫu (chuỗi trong test) + test TEAM.md của nhóm hợp lệ.

## Đánh giá ngắn
- **Đạt:** toàn bộ luật headless lõi của Ticket-02 (số chuẩn, cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn/6 món, day, Shop, nâng cấp, pause).
- **Chưa đạt:** UI vòng ngày (menu, các màn Intro/Result/Summary, HUD danh sách cần lấy, "Thủy quái!"). Không làm mở rộng (nhóm 4 người không bắt buộc).
- **Đóng góp:** B (ducpham13) Cá Sấu + lọc món theo kế hoạch (nhánh `b/p2-monsters-quan`); C contract v1.1, khung day/Shop/pause, cá bơi/sinh, merge + test. D (uscalurn) bộ test P1 67 test + 2 skill harness (merge lúc tag P2). A chưa push phần Phase 2 trước giờ tag.
