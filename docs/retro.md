# Retro

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
