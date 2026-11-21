# Nhật ký dùng AI (theo phase và theo người)

> Mỗi người **chỉ ghi vào mục của mình** (tránh conflict khi merge). Thêm dòng mới ở cuối bảng của mình.

## A — `sim/gather` + PO

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Antigravity AI | Cài đặt luật buổi sáng trong `chonoi/sim/gather.py`, viết bộ test `tests/test_gather_unit_a.py`, ghi `docs/clarify.md` theo Contract E & F | Chưa đo tự động | Cần đối chiếu kỹ edge-case ngạt tại tick chạm `oxy = 0` (`t+59`) và thứ tự ưu tiên ở tick cuối (`fainted` > `docked` > hái/bắt + `time`); đã kiểm chứng bằng headless test. |
| 2 | Antigravity AI | Cài đặt cá bơi 1.5 m/s, phản xạ mép x ∈ [4,96] và dải độ sâu từng loài, đổi hướng chu kỳ 120 tick (stream `fish_turn`); sinh cá chu kỳ 360 tick theo trọng số (linh 40%, lóc 30%, kèo 30%), trần 12 đàn, clearance > 1.0 m; hỗ trợ bắt cá kèo (yield = 2); tích hợp ctx (day, hp_max, oxygen_max_s) và hook quái vật `monsters.py`; viết bộ test `tests/test_gather_p2_a.py`. | Chưa đo tự động | AI ban đầu cho cá bơi trong môi trường test tĩnh Phase 1 dẫn tới cá di chuyển ra khỏi tầm với trong thời gian hồi chiêu 30 tick; phát hiện nhờ chạy regression test và khắc phục bằng điều kiện chỉ bơi khi cấu hình có `fish_speed`. |
| 3 | Antigravity AI | Di chuyển toàn bộ fixture và assertion trong `tests/test_gather_unit_a.py` và `tests/test_gather_p2_a.py` sang schema kho cá thể v1.2 (`items`, `stock_of`, `counts`); bổ sung test `test_gather_hold_freshness_decay_and_spoiled_event`; cập nhật clarify PO và phản tư cá nhân. | Chưa đo tự động | AI ban đầu so sánh `faint.lost` trực tiếp dạng string, cần đổi sang kiểm tra mảng cá thể `[it["kind"] for it in lost]` và `[it["id"] for it in lost]` (LIFO I3, I2, I1) theo Contract v1.2. |


## B — `sim/quan` + Scrum

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Sonnet 4.6) | Hoàn thiện `sim/quan.py` phần 3+4: khách, bếp, bàn, tiền, uy tín | ~15k tokens | Ban đầu dùng `inp.interact` thay vì `inp.pressed("interact")` — fix ngay sau khi chạy test. Snap đúng 32/32. |
| 2 | Claude Code (Sonnet 4.6) | `sim/monsters.py` (patrol/chase/hit/recoil/faint) + `sim/quan.py` ctx day | ~12k tokens | Không lỗi logic nào khi test smoke; bắt đúng hit_radius và LIFO. *Ghi chú C (Integrator) khi merge `f4ba76c`: phải sửa 2 lỗi — Cá Sấu hết recoil vẫn di chuyển/chạm ngay trong cùng bước (Ticket 1.2: từ bước kế) và snapshot `monsters[]` thiếu `waypoints/target_idx/recoil_dir`.* |
| 3 | Claude Code (Sonnet 4.6) | Rà luật quán v1.2 (hao tươi, spoiled, giữ chỗ theo id, giữ lại, giá theo tươi); viết CHANGELOG.md | ~8k tokens | Luật C cài đặt chính xác, không cần sửa. Thêm bảng xác minh vào CHANGELOG. |


## C — `client/ui` + Integrator

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|
| 1 | Claude Code (Opus 5.5) | Đọc repo, chia việc 4 người, soạn hợp đồng `docs/contracts/README.md` | | Bản đầu đoán `data` sự kiện khi chưa có PRD-0 (sai vài chỗ: `amount` thay vì `count`, thiếu `required/free` ở `hold_full`, bắt cá thiếu chỗ không đặt hồi chiêu). Sửa lại sau khi dán PRD-0. |
| 1 | Claude Code (Opus 5.5) | Viết kiểm mâu thuẫn scenario quán (`scenario.py`), HUD quán (`index.html`), README, TEAM.md | | Kiểm bằng 32 test + 12 ca scenario tay (đúng mã 0/2). Giả định chưa rõ ghi `docs/clarify.md` #1–5. |
| 2 | Claude Code (Opus 5.5) | Plan P2, contract v1.1, khung day/Shop/pause, cá bơi/sinh, merge B + D, test day/shop/fish/monsters, verification, retro | | AI viết nhầm test kỳ vọng (faint do quái: quên rằng monster_hit đã làm rơi đồ trước) — test đỏ, đối chiếu Ticket thì code đúng, sửa test. Ghi file bằng heredoc làm vỡ chuỗi `
| 3 | Claude Code (Opus 5.5) | ADR 0001, lõi v1.2 kho cá thể + độ tươi, HUD tươi, CHANGELOG, test P3, verification | | Chèn dòng skip vào giữa câu import nhiều dòng của test (vỡ import) — phát hiện khi chạy suite, dời xuống trước class. Kỳ vọng giá 40 trong test cũ sai sau v1.2 (đúng là 39 do hao 1 tick) — đối chiếu Ticket rồi sửa test. |
` trong test — phát hiện qua lỗi import, sửa bằng Edit. |


## D — `qa` + harness

| Phase | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|


### Phase 1 — D / uscalurn — QA & AI Harness

| Phase | Công cụ / model | Việc của D | Token / chi phí / thời gian AI | Kiểm tra lại / bằng chứng |
|---|---|---|---|---|
| 1 | Codex; không xác nhận model cụ thể | Đọc PRD-0/Test Contract v1.0; sinh và hoàn thiện 67 methods (28 Gather, 39 Quán) trong nhiệm vụ trước | Không đo được | [Gather](../tests/test_gather_rules.py), [Quán](../tests/test_quan_rules.py); giữ hai file chỉ đọc trong nhiệm vụ proof |
| 1 | Codex | Kiểm fixture và tương thích validator do C viết; 6 regression scenario từ nhiệm vụ test trước | Không đo được | [Log mới](proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt): 6 regression PASS; D không triển khai validator |
| 1 | Codex | Chạy lại unittest, phân tích FAIL; phân biệt method với subtest và lỗi luật với ERROR | Không đo được | [Full suite](proof/phase-1/d-uscalurn-run-81321f1b/full-suite.txt): 99 methods, 48 PASS/51 FAIL/0 ERROR/0 SKIP; [triage](proof/phase-1/d-uscalurn-run-81321f1b/qa-triage.md) |
| 1 | Codex + skill-creator | Tạo hai skill, đăng ký phần Skills/hooks của AGENTS.md | Không đo được | [run-tests-proof](../.agents/skills/run-tests-proof/SKILL.md), [check-determinism](../.agents/skills/check-determinism/SKILL.md); qua quick_validate và chạy chính ví dụ thực |
| 1 | Codex | Smoke hai tiến trình, so byte JSONL/inventory qua 3 cặp fixture | Không đo được | [Integration PASS](proof/phase-1/d-uscalurn-run-81321f1b/integration.md), [determinism PASS](proof/phase-1/d-uscalurn-determinism-df2e0816/determinism.md); lặp lại không thay thế đúng luật |
| 1 | Codex | Viết verification, proof và reflection; giữ nội dung A/B/C | Không đo được | [Verification](verification/phase-1.md), [reflection](members/uscalurn.md). Revision nền 6a7f66a35e5816996fe51010ea5b20ac9098fe5c; working tree/test chưa commit |

Chạy lại từ gốc repo: tắt bytecode, dùng lệnh unittest và khối proof trong hai skill. Trên Windows, full-suite proof thay riêng alias python3 bị hỏng bằng Python hiện tại trong bộ nhớ; không đổi manifest/helper. [summary.json](proof/phase-1/d-uscalurn-run-81321f1b/summary.json) lưu executable, exit code, hash source/test, trạng thái từng method. Guard của hai test determinism D còn FAIL do chưa có sự kiện gameplay; phép so byte trực tiếp PASS trong fixture đã chạy. Không dùng log cũ làm proof mới; chưa commit/push.
