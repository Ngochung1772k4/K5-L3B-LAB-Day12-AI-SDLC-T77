# ducpham13 (B — sim/quan, Scrum) — phản tư cá nhân (≤ 200 từ)

> **BẢN NHÁP do C (Integrator) soạn từ bằng chứng trong repo.** Đức đọc lại, sửa bằng lời của mình (nhất là 2 mục cuối) rồi **tự commit** từ tài khoản `ducpham13`.

- **Tôi đã làm:**
  - P1 — luật quán: lịch khách, chọn món, giữ chỗ ([40dfb24](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/40dfb24)), kiên nhẫn, `customer_left`, `no_dish` ([0d05c98](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/0d05c98)), phục vụ, trả tiền, boa, uy tín ([660add4](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/660add4)).
  - P2 — Cá Sấu Năm Chèo `sim/monsters.py` ([04cd2b6](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/04cd2b6)), quán lọc món theo kế hoạch ngày ([6c8a726](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/6c8a726)).
- **Tôi đã review:** P3 rà 8 luật quán v1.2 trên code C, ghi bảng xác minh vào CHANGELOG ([005acb7](https://github.com/Ngochung1772k4/K5-L3B-LAB-Day12-AI-SDLC-T77/commit/005acb7)).
- **AI sai ở đâu và tôi phát hiện thế nào:** AI dùng `inp.interact` thay vì `inp.pressed("interact")` — phát hiện khi chạy test. Khi tích hợp, C tìm thêm lỗi ở nhánh của tôi: P1 khách bỏ đi làm *tăng* kho, `data` sự kiện lệch hợp đồng, sai thứ tự bước; P2 Cá Sấu hết recoil vẫn cắn ngay trong cùng bước. Tôi chưa có test riêng nên các lỗi này không tự lộ ra.
- **Điều tôi học được:** (Đức tự viết) — gợi ý: đọc kỹ mục F/thứ tự xử lý của PRD và viết test hộp đen trước khi push.
