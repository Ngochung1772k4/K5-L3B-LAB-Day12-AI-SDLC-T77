# Retro

## Phase 4 — tổng kết cả buổi (rà hành động đã chốt ở P2 trước)

### Rà hành động P2
| Hành động P2 | Người nhận | Đã làm? | Vì sao |
|---|---|---|---|
| Mỗi lát push nhánh nhỏ trước phút 20, kèm ≥ 1 test | A, B | **Một phần.** P3: B push 11:26, A push 11:31 (gần hạn, sau phút 20); A có test, B chỉ có bảng rà soát (C bổ sung test làm bằng chứng). | Chờ C đẩy lõi v1.2 xong (11:22) mới sửa được fixture → phụ thuộc tuần tự. |
| D nhận test + verification từ đầu phase | D | **Muộn nhưng có giá trị.** D push 53 test P3 + bằng chứng QA lúc 11:43 (sau tag P3, vào P4); 4 test đỏ lộ ra 2 lỗi/điểm mơ hồ thật của C (làm tròn `fresh`, thứ tự giữ lại) → C sửa code. | Làm test độc lập từ Ticket nên mất thời gian; không báo tiến độ giữa chừng. |
| `git pull --rebase` trước khi bắt đầu/push | Cả nhóm | **Chưa đều.** Nhánh A/B ở P2 tách từ main cũ → conflict; A force-push nhánh đã merge. | Thói quen; chưa có ruleset bảo vệ nhánh. |

### Số liệu
4 tag (P1 muộn; P2, P3, P4 đúng hạn). Test: 32 → 53 → 142 → 94 chạy + 2 module skip (sau đổi schema P3) → P4 thêm 3. Commit trên main tới P4 (không tính 9 commit starter): C ~24, A 8, B 6, D 2.

### Điều làm tốt
- Chốt hợp đồng + tên khóa + `ctx` trước khi code, ADR cho đổi schema → main luôn chạy được qua 3 lần đổi contract.
- Test hộp đen theo AC bắt lỗi thật: quán P1 (kho tăng khi khách bỏ đi), recoil Cá Sấu P2.
- Lưu PRD/Ticket vào repo để mọi agent đọc cùng nguồn.

### Điều cần sửa
- **Integrator (C) làm thay lát người khác và gắn tag không fetch lại:** P2 C viết cá bơi lúc 10:55 khi A trễ mốc nội bộ, A push 11:00 (trước tag 11:04) nhưng C không kiểm remote → bỏ sót đóng góp của A trong tag `phase-2`.
- Phụ thuộc tuần tự (C → A/B/D) làm các lát dồn sát hạn.

### Một lỗi AI và cách xác minh
AI (Claude, C) viết test Cá Sấu kỳ vọng `faint.lost = ["bong_sung"]`, quên rằng `monster_hit` đã làm rơi `bong_sung` trước → test đỏ; đối chiếu Ticket-02 mục 1.2 (rơi floor(n/2) LIFO rồi ngất bỏ phần còn lại) thì code đúng, test sai → sửa test. Tương tự P3: kỳ vọng giá 40 sai, đúng là 39 do hao 1 tick trước khi nấu.

### Hành động tiếp theo
| Hành động | Người nhận |
|---|---|
| Trước khi gắn tag: `git fetch` + liệt kê mọi nhánh cho trưởng nhóm xác nhận; không làm thay lát khi chưa hỏi | C |
| Đổi fixture 2 module test còn skip sang v1.2, bỏ skip | D |
| Thêm menu + màn vòng ngày vào cửa sổ chơi | B + A |


## Phase 1 + 2 (ghi lúc gắn tag `phase-2`)

**Số liệu:** P1 tag muộn (sau 1:00); P2 tag đúng hạn. Test: 32 (khung) → 53 (P1) → 74 (P2). Commit theo người tới tag P2: A (hal2332004) 4, B (ducpham13) 5, C (Ngochung1772k4) nhiều nhất, D 0. Lỗi bắt được khi tích hợp: 6 lỗi nặng ở quán P1 (kho tăng khi khách bỏ đi, sai `data`, sai thứ tự bước…), 1 lỗi recoil Cá Sấu P2.

**Điều tốt**
- Chốt hợp đồng sự kiện + tên khóa tuning + giao diện `ctx` trước khi code → nhánh của A/B ghép vào ít sửa.
- Lưu PRD/Ticket vào repo (`docs/prd/`) để AI của mọi người đọc cùng một nguồn.
- Test hộp đen theo AC bắt được lỗi mà smoke test cũ bỏ sót.

**Điều vướng**
- P1: A/B push sau mốc 1:00 → tag muộn. Lỗi quán chỉ lộ ra lúc tích hợp vì chưa có test luật quán trước khi merge.
- D chưa có commit; A chưa push phần P2 → C gánh cá bơi/sinh.
- Nhánh B tách từ `main` cũ → conflict phần `ctx`.

**Hành động (có người nhận)**
| Hành động | Người nhận | Hạn |
|---|---|---|
| Mỗi lát push nhánh nhỏ trước phút 20 của phase, kèm ít nhất 1 test của lát mình | A, B (Scrum B nhắc) | Phase 3 |
| D nhận viết test + verification Phase 3 ngay đầu phase, báo C nếu vướng | D | Phase 3, phút 5 |
| `git pull --rebase origin main` trước khi bắt đầu và trước khi push | Cả nhóm | Ngay |
