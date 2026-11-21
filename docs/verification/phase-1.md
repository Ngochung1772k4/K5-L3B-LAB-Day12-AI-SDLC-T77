# Ma trận truy vết Phase 1

> Kiểm chứng trên commit gắn tag `phase-1` (gắn **muộn**, sau hạn 1:00 — xem "Đánh giá ngắn").
> Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` → [test-output.txt](../proof/phase-1/test-output.txt) (53 test, OK).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 Oxy −1/tick dưới nước, +6/tick mặt nước | `test_gather_unit_a.test_oxygen_drain_and_refill` | [test-output.txt](../proof/phase-1/test-output.txt) | Đạt |
| AC-P1-02 `dive`/`surface` chỉ khi đổi phía | `test_dive_and_surface_events` | như trên | Đạt |
| AC-P1-03 `oxygen_empty`, `choke` lần đầu ở t+59 | `test_oxygen_empty_and_first_choke_at_t_plus_59` | như trên | Đạt |
| AC-P1-04 Nổi lên đúng bước ngạt → không ngạt | `test_choke_from_zero_oxy_59_and_surface_cancels_choke` | như trên | Đạt |
| AC-P1-05 Ngất: `lost` LIFO, `fainted`, kho rỗng | `test_faint_drops_hold_lifo_and_writes_empty_inventory` | như trên | Đạt |
| AC-P1-06..08 Hái đúng mép, `hold_full`, mọc lại 1200 tick | `test_harvest_regrow_and_tiebreak` | như trên | Đạt |
| AC-P1-09..11 Bắt cá, yield, hồi 30 tick, thiếu chỗ không hồi | `test_catch_yield_cooldown_tiebreak_and_hold_full` | như trên | Đạt |
| AC-P1-12 Smoke 2 tiến trình (PRD G) | Chạy tay đúng 2 lệnh PRD G | [gather.jsonl](../proof/phase-1/gather.jsonl), [catch.json](../proof/phase-1/catch.json), [quan.jsonl](../proof/phase-1/quan.jsonl): `stock {"bong_sung":2,"ca_loc":1}` ở tick 0 | Đạt |
| AC-P1-13 Khách đầu ở tick 120, giữ đúng công thức, bàn đầy bỏ lượt | `test_quan_rules_c.test_ac13_*` | test-output | Đạt |
| AC-P1-14 Kho rỗng → `no_dish {}` | `test_ac14_no_dish_when_stock_empty` | test-output | Đạt |
| AC-P1-15 Hết kiên nhẫn → `customer_left patience`, uy tín 2.5, kho vật lý giữ nguyên | `test_ac15_*` | test-output | Đạt |
| AC-P1-16 Nấu → chín → bưng → phục vụ → trả tiền | `test_ac16_cook_ready_pick`, `test_ac16_ac17_serve_tip_pay` | test-output | Đạt |
| AC-P1-17 Boa floor(giá×0.2) khi ≥ 50% kiên nhẫn, +0.2 uy tín lúc thu; < 50% boa 0 | `test_ac16_ac17_*`, `test_ac17_low_patience_no_tip` | test-output | Đạt |
| AC-P1-18 Đóng ca: `paid closing`, `customer_left closing` không trừ uy tín, `quan_end` | `test_ac18_*` | test-output | Đạt |
| AC-P1-19 Tất định từng byte | `test_con_02_deterministic_bytes`, `test_gather_determinism_*`, `test_quan_rules_c.Determinism` | test-output | Đạt |
| AC-P1-20 Scenario quán mâu thuẫn → mã 2 | 12 ca chạy tay khi viết `scenario.py` (commit 788a2cb) + `test_quan_fixture_khong_hop_le_exit_2` | commit 788a2cb | Đạt một phần (chưa có test tự động cho từng ca) |
| HUD / chơi được 2 buổi | Chạy `python3 -m chonoi.live --mode gather|quan` | — | Chưa có ảnh chụp bằng chứng |

## Bằng chứng QA của D (uscalurn)
- D viết thêm `tests/test_gather_rules.py` (28) và `tests/test_quan_rules.py` (39) theo AC-P1-01..20, cùng 2 skill `.agents/skills/run-tests-proof`, `check-determinism`.
- Lần chạy đầu của D: [d-uscalurn-run-81321f1b](../proof/phase-1/d-uscalurn-run-81321f1b/summary.json) trên revision `6a7f66a` — **trước khi** luật gather/quán được merge, nên 51 method FAIL là đúng lúc đó (lịch sử, không phải kết quả commit tag).
- Sau khi merge vào `main` (luật P1 + v1.1): các test của D chạy lại xanh, trừ 1 test giả định chỉ có bàn T1 — đã sửa theo v1.1 (4 bàn), xem commit merge.

## Đánh giá ngắn
- **Trễ hạn:** luật gather (A) và quán (B) push sau mốc 1:00, nên tag `phase-1` gắn muộn (trong Phase 2) trên commit đã tích hợp. Tại mốc 1:00, `main` mới chỉ có khung + hợp đồng + kiểm scenario.
- **Lỗi phát hiện khi tích hợp nhánh quán (B):** khách bỏ đi làm *tăng* kho (cộng lại phần giữ vào kho vật lý), `data` sự kiện sai hợp đồng (`customer_id` thay `order_id`…), sai thứ tự bước (khách rời/sinh trước interact), thiếu đóng ca, `no_dish` tạo khách, boa dùng `round` và cộng uy tín lúc phục vụ. C sửa trong một commit (`Co-authored-by` B) và thêm 12 test quán.
- **Điều cần chỉnh cho phase sau:** viết test hộp đen *trước* khi merge (test smoke cũ không chạm luật quán nên lỗi lọt qua); D (QA) chưa có đóng góp — cần nhận việc test ngay từ Phase 2; merge sớm hơn thay vì dồn cuối.
