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
| AC-P4-10 Retro rà hành động P2, phản tư đủ người | [retro.md](../retro.md), `docs/members/*.md` | — | Retro đạt. Phản tư: A (hal2332004) đủ P1–P4; C (Ngochung1772k4) đủ; D (uscalurn) mới có P1; B (ducpham13) là **bản nháp do C soạn**, chờ Đức sửa và tự commit |

## Giới hạn
Vòng ngày + Shop chỉ ở headless (chưa có menu/DayIntro/Summary trong cửa sổ). Benchmark render phần mềm. Không làm mở rộng.

## Thay đổi theo QA của D (nhánh `d/phase-3-qa-uscalurn`, push 11:43)
4 test P3 của D đỏ trên code C → xử lý: (1) 3 test đòi `fresh` trong JSONL khớp đúng file kho → **sửa code**: `jsonl.py` không làm tròn `fresh` (tránh 29.9996 hiện thành 30.0); (2) giữ lại khi ươn phải **lần lượt từng đơn** → **sửa code** `quan._rereserve`; (3) test đòi version đúng "1.2" → đổi test chấp nhận 1.2/1.3 (P4 chỉ thêm bench/soak). Bỏ file rác `kho.json` ở gốc khỏi merge.

---

## Phụ lục: Kiểm chứng QA riêng của D — Phase 4

### QA Phase 4 — D / uscalurn

Ngày kiểm chứng: 21/11/2026 (Asia/Saigon). Nhánh `d/phase-4-qa-uscalurn`.
Revision nền: `c6573f3510a7d530d0565b4ceaeaf4e3b9270778`, cộng thay đổi QA chưa commit.
Nguồn yêu cầu: TICKET-04 do PO cung cấp trực tiếp trong phiên làm việc; Contract v1.3,
PRD-0, TICKET-02/03, ADR 0001 và `docs/contracts/README.md` trong repo.

**Kết luận: bộ QA của D đã hoàn thiện để bàn giao review, nhưng chưa đủ điều kiện ký nghiệm thu PASS cho sản phẩm.**
Regression Python đạt; browser regression giữ một FAIL về input khi chuyển pha. Các AC môi trường/phát hành còn giới hạn như ma trận dưới.
Không thay đổi gameplay, frontend, Contract, README, tài liệu A/B/C, Retro, commit, push, merge hay tag.

#### Kết quả thực chạy

Proof chính: [summary.json](../proof/phase-4/d-uscalurn/final-run-02/summary.json),
[regression.txt](../proof/phase-4/d-uscalurn/final-run-02/regression.txt),
[kết quả từng method](../proof/phase-4/d-uscalurn/final-run-02/regression.json).

| Kiểm tra | Kết quả |
|---|---|
| Baseline trên working tree ban đầu | 220 PASS, 0 FAIL / ERROR / SKIP |
| Regression cuối P1–P4 | **233 PASS, 0 FAIL / ERROR / SKIP; exit 0** |
| Hai module legacy | Gather 28 + Quán 39 method đều PASS; đã gỡ module skip |
| Benchmark CLI: seed 42, warmup 3 s, đo 30 s | exit 0; 8.842 khung / 30,003 s; avg **294,70 FPS**, 1% low **110,17 FPS**, load **27 ms** |
| Soak CLI: seed 7, 10 Ngày, hai lượt | exit 0 mỗi lượt; **10/10, 0 crash**; 5,255 s và 5,086 s; gameplay giống nhau sau khi bỏ `duration_s` |
| Determinism qua tiến trình độc lập | Gather JSONL + inventory, Quán JSONL, Day JSONL giống từng byte; output hợp lệ và bàn giao đúng |
| Clone sạch tương đương `git archive HEAD`, Windows | Live Day khởi động, HTTP state và Canvas trả thành công; production bytes khớp working tree |

Proof chính: [summary](../proof/phase-4/d-uscalurn/final-run-02/summary.json),
[regression](../proof/phase-4/d-uscalurn/final-run-02/regression.json),
[benchmark](../proof/phase-4/d-uscalurn/final-run-02/bench.json),
[soak lần 1](../proof/phase-4/d-uscalurn/final-run-02/soak-1.json),
[soak lần 2](../proof/phase-4/d-uscalurn/final-run-02/soak-2.json).
Benchmark: avg **294.70 FPS**, 1% low **110.17 FPS**, **8.842 khung / 30.003 s**, load **27 ms**; command exit 0.
Hai soak lần lượt **5.255 s** và **5.086 s**, command đều exit 0. QA harness exit 0.

Browser cuối: [audit](../proof/phase-4/d-uscalurn/browser-final/browser-audit.json),
[execution](../proof/phase-4/d-uscalurn/browser-final-execution.json): **25 check = 24 PASS / 1 FAIL**, exit **1**,
không có uncaught JavaScript exception. Chrome 157 headless, `--disable-gpu`, Canvas 1280×720;
làm nóng 3 s, đo 30.0106 s, 1.801 callback khung hoàn tất, avg **60.0121 FPS**, 1% low **59.5238 FPS**.
First contentful paint **76 ms** chỉ là metric trình duyệt, không thay cho `load_ms` của Contract.
Ảnh thật: [Gather tương phản cao](../proof/phase-4/d-uscalurn/browser-final/ui-gather-high-contrast.png),
[Quán tương phản cao](../proof/phase-4/d-uscalurn/browser-final/ui-quan-high-contrast.png),
[Shop](../proof/phase-4/d-uscalurn/browser-final/ui-day-shop.png).

Benchmark CLI rasterize framebuffer RGB 1280×720 bằng CPU, có bước simulation; không phải tốc độ headless simulation thuần.
Nó không mở cửa sổ, không chạy frontend và không chứng minh hiệu năng GPU/hiệu ứng của bản chơi.
Các mốc 60 FPS / 30 FPS / 10 s đều đạt ở phép đo phần mềm này, chỉ dùng để báo cáo.
Test công thức 1% low ghi lại **đồng hồ thật**, tự tính lại các khung chậm nhất sau warmup; không thay clock, render hay FPS.
`load_ms` của implementation bắt đầu ở `T0` trong module bench, sau một số import, nên chưa đo trọn chi phí khởi chạy interpreter.

Soak CLI dùng bot idle thật trong **một DaySim liên tục mỗi tiến trình**: không thu nhập/nâng cấp tự nhiên, earned 0, reputation 3, score 300.
Test fixture ngắn 10 Ngày bổ sung nhánh thu tiền thật từ khách đã ăn, mua nâng cấp, ID tăng và thứ tự event.
Fixture này không được dùng thay cho proof soak 10 Ngày mặc định. Test riêng xác nhận kế hoạch D1–D5 lặp ở Ngày 6–10.

#### Ma trận nghiệm thu

Mã AC-P4-01…10 giữ cách đánh số của báo cáo nhóm; `D-LIVE` là mục bổ sung theo yêu cầu PO.

| AC | Test / proof | Kết quả |
|---|---|---|
| 01 Contract v1.3, bench/soak command; giữ gameplay v1.2 | `test_p4_c`, toàn bộ P3; summary chính | PASS |
| 02 Benchmark command, schema, số hữu hạn, avg và 1% low, warmup | `test_p4_c`, `test_phase4_audit_d`; bench artifact | PASS phần command/JSON; PARTIAL cảnh cửa sổ/hiệu ứng và load toàn tiến trình |
| 03 Soak đủ 10 Ngày, kết thúc Shop, carry và tất định | Hai artifact soak; test 10 Ngày mặc định và fixture stateful; byte determinism Day | PASS |
| 04 Ba cảnh báo bằng chữ/biểu tượng | Chrome thật, screenshot Gather/Quán, quan sát lời gọi Canvas thật | PASS |
| 05 Tương phản cao, H, lưu preference, ba cảnh báo | Chrome query high contrast, H và tải lại không query, chữ vàng 28px/biểu tượng | PASS trong Chrome automation; chưa có đánh giá người dùng/screen reader |
| 06 Bản sạch chạy ≤3 lệnh trên macOS/Linux; README đầy đủ | Đọc README; `clean-archive-windows.json` | PARTIAL: Windows chạy được; chưa chạy macOS/Linux/remote clone |
| 07 CHANGELOG/release notes/CREDITS/LICENSE | Đọc bản hiện có: đủ phase, giới hạn, MIT, tài sản Canvas/emoji; không âm thanh | PASS kiểm tra tài liệu cục bộ; chưa kiểm toán pháp lý tài sản |
| 08 Regression P1–P3 còn hiệu lực | 233 test; legacy 67 method thực chạy; P3 53 method | PASS Python; FAIL regression input trình duyệt D-LIVE |
| 09 Release v1.0.0/package/tag cùng commit main | Proof cũ thuộc revision khác được giữ nguyên | Chưa xác minh lại GitHub Release/package của `c6573f3`; không đổi tag/release |
| 10 Retro/phản tư/quy trình | Ngoài phạm vi được giao | Không kiểm chứng và không sửa Retro/phản tư |
| D-LIVE Day Gather → Quán → Shop → Ngày kế, input, pause, restart, ngày cuối | `test_phase4_audit_d`, browser regression | Chuyển pha/carry/Shop/pause/restart/finish PASS; giữ W xuyên pha FAIL |
| Mở rộng leaderboard/SFX | Manifest `extensions` rỗng, nhóm 4 người; CREDITS không có âm thanh | Không áp dụng; không tự thêm yêu cầu mở rộng |

#### Lỗi cần bàn giao

**P1 — input W bị đảo khi giữ phím qua Gather → Quán.** Owner frontend/Live (C, phối hợp A/B).
File: `chonoi/web/index.html:32–42`, `poll():85–91`.
Seed 42, fixture `live-day` được lưu đầy đủ trong `browser-audit.json`.

1. Chạy Day với Gather ở bến; giữ W.
2. Nhấn E để cập bến, vẫn giữ W khi vào Quán.
3. Expected: W ở Quán làm z tăng từ 5. Actual trong proof lần đầu: tick 57, phase_tick 9,
   pos `[8,4.566666666666668]`, vel `[0,-4]`.
4. Assertion `Holding W across Gather → Quán continues north (+z)` FAIL; keyUp làm input được gửi lại.

Lần chạy cuối tiếp tục tái hiện: tick **55**, phase_tick **10**, pos `[8,4.500000000000002]`, vel `[0,-4]`.

Nguyên nhân: `currentInput()` đổi dấu dy theo pha, nhưng `poll()` chỉ thay `snap`.
`pushInput()` chỉ chạy khi có sự kiện bàn phím/blur, nên server tiếp tục giữ move `[0,-1]` của Gather.
Đề xuất owner gọi gửi lại input khi pha đổi sau khi nhận snapshot, xử lý queue cũ để hướng di chuyển khớp pha mới;
chạy lại regression giữ W/S và phím mũi tên qua cả hai chiều chuyển pha. D chỉ thêm test tái hiện, chưa sửa source.

**P2 — giới hạn benchmark:** framebuffer riêng không xác minh toàn cảnh Canvas/hiệu ứng mặc định trong cửa sổ;
`load_ms` chưa tính toàn thời gian từ khởi chạy process. Bàn giao owner bench/Live làm rõ hoặc đo đường chạy đầy đủ.
**P2 — thiếu proof macOS/Linux và xác nhận package/tag/release hiện hành:** cần Integrator/Release xác minh trên đúng commit bàn giao.
Không phát hiện P0 trong phạm vi đã chạy. Các mục quy trình ngoài phạm vi không được coi là PASS.

#### Migration và môi trường

`legacy_rules_view.py` chuyển fixture kho đếm/hold chuỗi sang cá thể, reserved sang ID;
chỉ chiếu output về kind/count cho assertion P1 còn hiệu lực. Không sửa file JSONL/kho thật.
Giữ assertion về tick, thứ tự, tiền, uy tín, giá và kết thúc; adapter từ chối ID trùng, reservation thiếu/chia sẻ.
Giá nấu mới đổi theo TICKET-03: hao tươi trước tick nấu, rồi floor giá theo tươi.
P3 vẫn kiểm tra trực tiếp ID, freshness, thứ tự LIFO, ngưỡng 30, reservation và giá mà không chiếu schema.

WindowsApps `python3 --version` thực tế lỗi **OSError winerror 1920**, không phải lỗi application và không giả ghi exit 9009.
`helpers.manifest_cmd()` dùng `sys.executable -B` cho entrypoint Python trong manifest, giữ nguyên module/cờ và exit code;
executable ngôn ngữ khác giữ nguyên. Không sửa PATH/manifest hoặc copy interpreter.
Test harness kiểm tra cả việc giữ nguyên mã 1/2/9009, không retry application failure.
Linux/CI dùng cùng helper với interpreter của CI; phiên này chưa chạy runner Ubuntu nên chỉ xác minh tính tương thích qua code.

Các skill [run-tests-proof](../../.agents/skills/run-tests-proof/SKILL.md) và
[check-determinism](../../.agents/skills/check-determinism/SKILL.md) được áp dụng nguyên tắc thu proof,
đếm method và so byte; fixture v1.0 được thay bằng dữ liệu hợp lệ v1.3 theo phạm vi PO cho phép.

#### Chạy lại và tập file commit D

Nên đưa vào commit D sau review: `tests/helpers.py`, `tests/legacy_rules_view.py`,
`tests/test_gather_rules.py`, `tests/test_quan_rules.py`, `tests/test_p4_c.py`,
`tests/test_phase4_audit_d.py`, `tests/test_qa_harness_d.py`,
`tools/qa_phase4_proof.py`, `tools/qa_phase4_browser.mjs`, báo cáo này và `docs/proof/phase-4/d-uscalurn/`.
Thư mục audit cũ `d-uscalurn-audit-02ba5032/` giữ nguyên, không dùng làm proof nghiệm thu revision hiện tại.
Chưa commit/push/merge/tag. Không sửa gameplay, frontend, Contract, README, Retro hay proof của thành viên khác.

**Đánh giá:** phần kiểm thử và bàn giao lỗi của D hoàn thành trong phạm vi giao;
chưa đủ điều kiện ký PASS nghiệm thu toàn Phase 4 vì lỗi P1 Live và các AC còn PARTIAL/chưa xác minh.

PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
$env:PYTHONPATH='tests;.'
python -B -m unittest discover -s tests -v
python -B tools/qa_phase4_proof.py --proof docs/proof/phase-4/d-uscalurn/run-NEW
node tools/qa_phase4_browser.mjs (Get-Command python).Source docs/proof/phase-4/d-uscalurn/browser-NEW
git diff --check
```

Linux/CI: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -B -m unittest discover -s tests -v`;
proof runner dùng `python3 -B`; browser cần Node ≥22 có WebSocket, Chrome và có thể đặt `CHROME_PATH`.
Proof directory phải mới. Trên máy hiện tại Chrome GPU process bị sandbox chặn; chạy ngoài sandbox với profile tạm riêng đã thành công.

File nên đưa vào commit D sau khi người review đọc thay đổi:

- `tests/helpers.py`, `tests/legacy_rules_view.py`, `tests/test_gather_rules.py`, `tests/test_quan_rules.py`.
- `tests/test_p4_c.py`, `tests/test_phase4_audit_d.py`, `tests/test_qa_harness_d.py`.
- `tools/qa_phase4_proof.py`, `tools/qa_phase4_browser.mjs`.
- `docs/verification/phase-4-d.md`, proof chính của D trong `docs/proof/phase-4/d-uscalurn/` theo chỉ mục proof.

Audit cũ `d-uscalurn-audit-02ba5032/` được giữ nguyên, không dùng thay proof của revision mới.
Không tự stage/commit/push. Khi owner sửa P1, phải chạy lại browser và regression trên commit tích hợp trước ký nghiệm thu PASS.
