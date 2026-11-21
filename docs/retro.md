# Retro

## Phase 4 — tổng kết cả buổi (rà hành động đã chốt ở P2 trước)

### Rà hành động P2

| Hành động P2 | Người nhận | Đã làm? | Vì sao |
|---|---|---|---|
| Mỗi lát push nhánh nhỏ trước phút 20, kèm ≥ 1 test | A, B | **Một phần.** P3: B push 11:26, A push 11:31 (gần hạn, sau phút 20); A có test, B chỉ có bảng rà soát (C bổ sung test làm bằng chứng). | Chờ C đẩy lõi v1.2 xong (11:22) mới sửa được fixture → phụ thuộc tuần tự. |
| D nhận test + verification từ đầu phase | D | **Hoàn thành, tích hợp muộn.** D xây dựng 53 test P3 và bằng chứng QA, push lúc 11:43 (sau tag P3, vào P4). Bộ test phát hiện các trường hợp cần điều chỉnh về làm tròn `fresh` và thứ tự giữ lại, giúp C hoàn thiện implementation v1.2. Commit `f6cf7e9` được merge vào `main` tại `18e7730`. | Xây dựng test độc lập theo TICKET-03 và kiểm tra các trường hợp nghiệp vụ; thời gian bàn giao kéo dài nên phần QA được tích hợp sau tag P3. |
| `git pull --rebase` trước khi bắt đầu/push | Cả nhóm | **Chưa đều.** Nhánh A/B ở P2 tách từ main cũ → conflict; A force-push nhánh đã merge. | Thói quen; chưa có ruleset bảo vệ nhánh. |

### Số liệu

4 tag (P1 muộn; P2, P3, P4 đúng hạn). Test: 32 → 53 → 142 → 94 chạy + 2 module skip (sau đổi schema P3) → P4 thêm 3. Commit trên main tới P4 (không tính 9 commit starter): C ~24, A 8, B 6, D 2.

**Bổ sung kết quả QA Phase 4 của D trên commit `c6573f3`:**

- Regression P1–P4: **233/233 test PASS**, 0 FAIL/ERROR/SKIP; hai module legacy đã được cập nhật và chạy lại.
- Benchmark: warmup 3 giây, đo 30 giây; FPS trung bình **294,70**, 1% low **110,17**, load **27 ms**. Kết quả đo trên framebuffer phần mềm, không đại diện trực tiếp cho FPS GPU của người chơi.
- Soak: **2 lần × 10 ngày**, đều hoàn thành 10/10 ngày, 0 crash; kết quả gameplay được đối chiếu và nhất quán.
- Browser automation trên Chrome: **24 PASS, 1 FAIL**; kiểm tra ba cảnh báo, tương phản cao, chuyển pha, Shop, mua nâng cấp, restart và kết thúc ngày cuối.
- Kiểm thử bản `git archive` sạch: Live Day khởi động và trả HTML/Canvas cùng snapshot qua HTTP trên Windows.
- Báo cáo và bằng chứng QA được lưu tại `docs/verification/phase-4-d.md` và `docs/proof/phase-4/d-uscalurn/`. Các thay đổi QA Phase 4 của D đang ở working tree, chưa được commit tại thời điểm tổng kết.

### Điều làm tốt

- Chốt hợp đồng + tên khóa + `ctx` trước khi code, ADR cho đổi schema → main luôn chạy được qua 3 lần đổi contract.
- Test hộp đen theo AC bắt lỗi thật: quán P1 (kho tăng khi khách bỏ đi), recoil Cá Sấu P2.
- Lưu PRD/Ticket vào repo để mọi agent đọc cùng nguồn.
- **D hoàn thiện QA Phase 4:** Mở rộng regression lên 233 test PASS, khôi phục hai module legacy, xây dựng QA harness và browser automation, bổ sung bằng chứng benchmark và soak.
- **D phát hiện lỗi tích hợp:** Test giữ phím `W` qua Gather → Quán tái hiện lỗi nhân vật di chuyển sai hướng. D giữ assertion FAIL, lưu proof và báo cáo cho owner frontend, không tự sửa gameplay.

### Điều cần sửa

- **Integrator (C) làm thay lát người khác và gắn tag không fetch lại:** P2 C viết cá bơi lúc 10:55 khi A trễ mốc nội bộ, A push 11:00 (trước tag 11:04) nhưng C không kiểm remote → bỏ sót đóng góp của A trong tag `phase-2`.
- Phụ thuộc tuần tự (C → A/B/D) làm các lát dồn sát hạn.
- **D:** Cần chia nhỏ và bàn giao test sớm hơn để nhóm có thêm thời gian xử lý kết quả QA trước khi chốt phase. Tiếp tục phân biệt kiểm thử mô phỏng, benchmark phần mềm và kiểm thử trình duyệt thực tế khi báo cáo nghiệm thu.

### Một lỗi AI và cách xác minh

AI (Claude, C) viết test Cá Sấu kỳ vọng `faint.lost = ["bong_sung"]`, quên rằng `monster_hit` đã làm rơi `bong_sung` trước → test đỏ; đối chiếu Ticket-02 mục 1.2 (rơi floor(n/2) LIFO rồi ngất bỏ phần còn lại) thì code đúng, test sai → sửa test. Tương tự P3: kỳ vọng giá 40 sai, đúng là 39 do hao 1 tick trước khi nấu.

**Bổ sung kiểm chứng AI từ D:** Trong Phase 4, browser automation phát hiện lỗi khi giữ `W` liên tục qua chuyển pha Gather → Quán. Snapshot ghi nhận vận tốc `[0, -4]` ở Quán, trong khi điều khiển `W` phải di chuyển theo `+z`. D kiểm tra trạng thái input, đối chiếu hướng di chuyển theo pha, giữ assertion FAIL và lưu bằng chứng tái hiện. Kết quả này được tách khỏi 233 test regression PASS để không làm sai lệch báo cáo QA.

### Hành động tiếp theo

| Hành động | Người nhận |
|---|---|
| Trước khi gắn tag: `git fetch` + liệt kê mọi nhánh cho trưởng nhóm xác nhận; không làm thay lát khi chưa hỏi | C |
| Hoàn tất rà soát diff/proof, commit và bàn giao bộ QA Phase 4; kiểm thử lại sau khi lỗi input được sửa | D |
| Thêm menu + màn vòng ngày vào cửa sổ chơi | B + A |
| Sửa lỗi giữ `W` xuyên pha Gather → Quán và xác nhận điều khiển đúng theo pha | Owner frontend; D kiểm thử lại |

---

## Phase 1 + 2 (ghi lúc gắn tag `phase-2`)

**Số liệu:** P1 tag muộn (sau 1:00); P2 tag đúng hạn. Test: 32 (khung) → 53 (P1) → 74 (P2). Commit theo người tới tag P2: A (hal2332004) 4, B (ducpham13) 5, C (Ngochung1772k4) nhiều nhất. D chưa có commit trong thống kê ban đầu; phần QA Phase 1 gồm 67 test, 2 AI Skills và bằng chứng verification được hoàn thiện muộn, sau đó tích hợp trong Phase 2 bằng commit `d0a2374`.

Lỗi bắt được khi tích hợp: 6 lỗi nặng ở quán P1 (kho tăng khi khách bỏ đi, sai `data`, sai thứ tự bước…), 1 lỗi recoil Cá Sấu P2.

**Điều tốt**

- Chốt hợp đồng sự kiện + tên khóa tuning + giao diện `ctx` trước khi code → nhánh của A/B ghép vào ít sửa.
- Lưu PRD/Ticket vào repo (`docs/prd/`) để AI của mọi người đọc cùng một nguồn.
- Test hộp đen theo AC bắt được lỗi mà smoke test cũ bỏ sót.
- **D:** Xây dựng bộ QA Phase 1 gồm 67 test, 2 AI Skills và proof kiểm thử, tạo nền tảng kiểm tra regression cho các phase tiếp theo.

**Điều vướng**

- P1: A/B push sau mốc 1:00 → tag muộn. Lỗi quán chỉ lộ ra lúc tích hợp vì chưa có test luật quán trước khi merge.
- D chưa kịp tích hợp bộ QA trước khi chốt Phase 1 nên phần test, AI Skills và verification được bàn giao trong Phase 2. A chưa push phần P2 → C gánh cá bơi/sinh.
- Nhánh B tách từ `main` cũ → conflict phần `ctx`.

**Hành động (có người nhận)**

| Hành động | Người nhận | Hạn |
|---|---|---|
| Mỗi lát push nhánh nhỏ trước phút 20 của phase, kèm ít nhất 1 test của lát mình | A, B (Scrum B nhắc) | Phase 3 |
| D nhận viết test + verification Phase 3 ngay đầu phase, báo C nếu vướng | D | Phase 3, phút 5 |
| `git pull --rebase origin main` trước khi bắt đầu và trước khi push | Cả nhóm | Ngay |