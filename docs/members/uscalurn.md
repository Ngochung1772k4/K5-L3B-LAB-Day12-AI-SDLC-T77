# uscalurn — Nguyễn Minh Nhân — QA Lead / AI Harness

**Vai trò:** Thành viên D — thiết kế test theo Acceptance Criteria, QA harness, kiểm thử hồi quy, tính tất định và bằng chứng nghiệm thu. **Công cụ AI:** Codex (không xác nhận model cụ thể). **Token / chi phí / thời gian AI:** Không đo được; không tự ước tính.

## Phase 1 — Xây dựng QA theo PRD-0

Tôi dùng Codex đọc PRD-0 và Test Contract v1.0, thiết kế **67 test methods**: 28 Gather trong [`tests/test_gather_rules.py`](../../tests/test_gather_rules.py) và 39 Quán trong [`tests/test_quan_rules.py`](../../tests/test_quan_rules.py). Bổ sung 6 regression kiểm tra validator do C triển khai; tôi không viết validator. Đồng thời tạo hai AI Skills [`run-tests-proof`](../../.agents/skills/run-tests-proof/SKILL.md) và [`check-determinism`](../../.agents/skills/check-determinism/SKILL.md), hỗ trợ lưu lệnh chạy, exit code, snapshot và so byte.

**Bằng chứng tại thời điểm kiểm tra ban đầu:** 99 methods, **48 PASS / 51 FAIL / 0 ERROR / 0 SKIP** trên revision `6a7f66a` khi gameplay chưa tích hợp đầy đủ. Đây là trạng thái lịch sử của bản đang phát triển, **không phải kết quả cuối Phase 1 hoặc Phase 2**. Các phép smoke và so byte với fixture đã chạy đạt; không dùng determinism để suy ra gameplay đúng. Xem [summary](../proof/phase-1/d-uscalurn-run-81321f1b/summary.json), [smoke](../proof/phase-1/d-uscalurn-run-81321f1b/integration.md) và [determinism](../proof/phase-1/d-uscalurn-determinism-df2e0816/determinism.md).

**Tiến độ:** Bộ QA chưa kịp tích hợp trước mốc chốt Phase 1; được bàn giao và merge trong Phase 2. **Bài học:** Viết test theo contract giúp phát hiện sớm hành vi còn thiếu, nhưng cần gửi fixture, seed, tick và expected/actual cho owner kịp thời, không chỉ báo số FAIL.

## Phase 2 — Bàn giao và tích hợp QA Phase 1

Tôi hoàn thiện bộ 67 test và hai AI Skills, bổ sung verification/proof để nhóm chạy lại khi triển khai Contract v1.1. Công việc được commit tại **`d0a2374`**, sau đó merge vào `main` qua **`b613a69`**. Bộ test của D được đưa vào regression Phase 2; báo cáo nhóm ghi nhận **142 test PASS**, bao gồm 67 test của D, trên commit/tag kiểm chứng Phase 2. Xem [verification Phase 2](../verification/phase-2.md).

**Phạm vi đóng góp:** QA và harness; không nhận công triển khai cá bơi, quái vật, Day/Shop hoặc frontend của thành viên khác. **Bài học:** Hoàn thành test chưa đồng nghĩa hoàn tất bàn giao; cần tích hợp sớm và chạy lại trên phiên bản đã merge.

## Phase 3 — QA Contract v1.2

Tôi dùng Codex xây dựng **53 test methods mới trong 4 file** `tests/test_p3_*_d.py`, bao phủ kho cá thể theo ID, độ tươi/`spoiled`, giữ chỗ theo ID, tính giá và chuyển dữ liệu Gather → Quán → Day. Chạy thêm 26 regression P1/P2; lưu CLI, fixture, exit code, traceback và traceability. Không sửa implementation để làm xanh test.

**Kiểm chứng ban đầu:** **2 PASS / 51 FAIL** trong 53 test mới, 26 regression PASS vì engine thời điểm đó còn v1.1, chưa nhận schema v1.2. Tôi phân loại đây là **BLOCKED tại thời điểm chạy**, không khẳng định 51 lỗi gameplay riêng biệt. Xem [QA report](../verification/phase-3.md) và [proof](../proof/phase-3/d-uscalurn-1aa67cc8/summary.json).

**Bàn giao:** Commit **`f6cf7e9`** được merge vào `main` ở **`18e7730`**, sau tag Phase 3. Bộ test góp phần làm rõ và kiểm chứng cách làm tròn độ tươi trong JSONL và thứ tự giữ lại khi nguyên liệu ươn; C sửa implementation khi tích hợp. **Bài học:** Test độc lập theo yêu cầu có giá trị, nhưng bàn giao sau mốc tag khiến nhóm ít thời gian phản hồi; cần gửi blocker và tiến độ sớm hơn.

## Phase 4 — QA release và kiểm chứng end-to-end

Tôi dùng Codex rà TICKET-04/Contract v1.3, cập nhật hai module test legacy 28 Gather + 39 Quán từ fixture v1.1 sang kho cá thể, giữ các assertion nghiệp vụ; cải thiện helper dùng interpreter Python hiện tại trên Windows để không nhầm lỗi alias `python3` với lỗi application. Bổ sung test bàn giao kho, freshness, pause/restart, mua nâng cấp, Shop, test harness, và browser automation. Không chỉnh sửa gameplay/frontend hoặc thay assertion để che lỗi.

**Kết quả trên nền `c6573f3` cộng các thay đổi QA chưa commit:**

| Hạng mục | Kết quả / bằng chứng |
|---|---|
| Regression P1–P4 | **233/233 PASS, 0 FAIL/ERROR/SKIP**, gồm 67 legacy methods đã chạy lại; [regression](../proof/phase-4/d-uscalurn/final-run-02/regression.txt) |
| Benchmark phần mềm | Warmup 3 s, đo 30,003 s; **294,70 FPS trung bình**, **110,17 FPS 1% low**, load **27 ms**; đây là framebuffer CPU, không phải GPU gameplay; [bench](../proof/phase-4/d-uscalurn/final-run-02/bench.json) |
| Soak | Hai lần chạy liên tục **10/10 ngày, 0 crash**, cùng seed, trạng thái gameplay nhất quán khi loại thời gian thực thi; [lần 1](../proof/phase-4/d-uscalurn/final-run-02/soak-1.json), [lần 2](../proof/phase-4/d-uscalurn/final-run-02/soak-2.json) |
| Tính tất định | Gather/Quán/Day JSONL và file kho giống từng byte trong các cặp chạy độc lập; [summary](../proof/phase-4/d-uscalurn/final-run-02/summary.json) |
| Chrome thực tế | **24 PASS, 1 FAIL**, exit 1; kiểm tra 3 cảnh báo, tương phản cao, Gather → Quán → Shop, nâng cấp, restart và ngày cuối; [browser audit](../proof/phase-4/d-uscalurn/browser-final/browser-audit.json) |
| Bản sạch trên Windows | `git archive` khởi động Live Day, HTTP trả HTML/Canvas và snapshot; chưa chứng minh macOS/Linux; [QA bổ sung](../verification/phase-4.md) |

**Bug được tìm thấy và bàn giao:** Giữ phím **W** xuyên chuyển pha Gather → Quán làm server tiếp tục dùng input Gather, nhân vật đi theo **−z** thay vì **+z** (ví dụ snapshot `vel=[0,-4]`). Tôi giữ assertion **FAIL** và ảnh/trace, đề xuất owner frontend gửi lại input khi phase thay đổi; **không tự sửa frontend**. Đây là **1 FAIL browser riêng**, không được tính vào 233 test Python PASS. Xem [browser proof](../proof/phase-4/d-uscalurn/browser-final/browser-audit.json).

**Giới hạn trước nghiệm thu sản phẩm:** Benchmark phần mềm không xác nhận toàn bộ hiệu năng GPU; chưa kiểm chứng clone trên macOS/Linux, tag/package/release theo revision mới; bug input chưa được owner khắc phục. Bộ QA đủ để bàn giao review, **chưa tuyên bố toàn sản phẩm Phase 4 PASS**. Báo cáo, test và proof tại thời điểm lập còn ở working tree của nhánh `d/phase-4-qa-uscalurn`, **chưa xác nhận commit/push/merge**; xem [ma trận Phase 4 và phụ lục D](../verification/phase-4.md).

## Tổng kết cá nhân

Tôi phụ trách tạo bộ kiểm thử và bằng chứng kiểm chứng thay vì triển khai gameplay. Điểm mạnh là test theo Contract, phát hiện bất thường tích hợp qua kiểm tra độc lập, giữ minh bạch PASS/FAIL/BLOCKED và lưu lại khả năng tái hiện. Việc tích hợp test Phase 1 và bàn giao test Phase 3 chưa đúng mốc cho thấy tôi cần chia nhỏ đầu việc, báo tiến độ và chuyển test/blocker đến owner sớm hơn. Ở Phase 4, việc kết hợp unittest, soak, benchmark và Chrome giúp phát hiện lỗi điều khiển mà regression Python không chạm tới. Các kết luận AI đều cần kiểm tra bằng log, trạng thái và bằng chứng thực chạy.

**Commit cá nhân đã xác minh trên main tới `c6573f3`:** `d0a2374` (QA Phase 1 tích hợp trong Phase 2), `f6cf7e9` (QA Phase 3 tích hợp trong Phase 4). Phần QA Phase 4 cần được review và commit riêng sau khi rà diff/proof.
