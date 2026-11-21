# Nhật ký dùng AI (theo phase và theo người)

> Mỗi người **chỉ ghi vào mục của mình** (tránh conflict khi merge). Thêm dòng mới ở cuối bảng của mình.

## A — `sim/gather` + PO

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Antigravity AI | Cài đặt luật buổi sáng trong `chonoi/sim/gather.py`, viết bộ test `tests/test_gather_unit_a.py`, ghi `docs/clarify.md` theo Contract E & F | Chưa đo tự động | Cần đối chiếu kỹ edge-case ngạt tại tick chạm `oxy = 0` (`t+59`) và thứ tự ưu tiên ở tick cuối (`fainted` > `docked` > hái/bắt + `time`); đã kiểm chứng bằng headless test. |
| 2 | Antigravity AI | Cài đặt cá bơi 1.5 m/s, phản xạ mép x ∈ [4,96] và dải độ sâu từng loài, đổi hướng chu kỳ 120 tick (stream `fish_turn`); sinh cá chu kỳ 360 tick theo trọng số (linh 40%, lóc 30%, kèo 30%), trần 12 đàn, clearance > 1.0 m; hỗ trợ bắt cá kèo (yield = 2); tích hợp ctx (day, hp_max, oxygen_max_s) và hook quái vật `monsters.py`; viết bộ test `tests/test_gather_p2_a.py`. | Chưa đo tự động | AI ban đầu cho cá bơi trong môi trường test tĩnh Phase 1 dẫn tới cá di chuyển ra khỏi tầm với trong thời gian hồi chiêu 30 tick; phát hiện nhờ chạy regression test và khắc phục bằng điều kiện chỉ bơi khi cấu hình có `fish_speed`. |


## B — `sim/quan` + Scrum

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Sonnet 4.6) | Hoàn thiện `sim/quan.py` phần 3+4: khách, bếp, bàn, tiền, uy tín | ~15k tokens | Ban đầu dùng `inp.interact` thay vì `inp.pressed("interact")` — fix ngay sau khi chạy test. Snap đúng 32/32. |


## C — `client/ui` + Integrator

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Opus 5.5) | Đọc repo, chia việc 4 người, soạn hợp đồng `docs/contracts/README.md` | | Bản đầu đoán `data` sự kiện khi chưa có PRD-0 (sai vài chỗ: `amount` thay vì `count`, thiếu `required/free` ở `hold_full`, bắt cá thiếu chỗ không đặt hồi chiêu). Sửa lại sau khi dán PRD-0. |
| 1 | Claude Code (Opus 5.5) | Viết kiểm mâu thuẫn scenario quán (`scenario.py`), HUD quán (`index.html`), README, TEAM.md | | Kiểm bằng 32 test + 12 ca scenario tay (đúng mã 0/2). Giả định chưa rõ ghi `docs/clarify.md` #1–5. |


## D — `qa` + harness

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
