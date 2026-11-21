# Ngochung1772k4 (C — client/ui, Integrator) — phản tư cá nhân

> Bản nháp do AI (Claude) soạn từ lịch sử commit — **Hùng cần đọc lại và sửa bằng lời của mình**.

- **Tôi đã làm:** chia việc + hợp đồng P1 (`d9e57e2`), kiểm scenario quán (`788a2cb`), sửa luật quán khi tích hợp (`2bf06ba`); P2 contract v1.1 + day/Shop/pause (`a550a0b`, `94b5e94`), cá bơi/sinh (`2dde123`); P3 ADR + lõi v1.2 độ tươi (`330ee4a`); P4 bench/soak, cảnh báo + tương phản cao, phát hành.
- **Đã giúp ai:** merge và sửa nhánh B (quán P1, Cá Sấu P2), giữ test/tài liệu của A (`dc1baf5`), merge test + skill của D (`b613a69`), viết bằng chứng cho bảng rà soát của B.
- **AI sai ở đâu:** kỳ vọng test sai (faint.lost, giá 40/39), chèn dòng skip vào giữa import — phát hiện nhờ chạy toàn bộ test và đối chiếu Ticket.
- **Bài học:** Integrator không nên làm thay lát người khác; trước khi gắn tag phải fetch lại remote (bỏ sót bản A nộp kịp ở P2).
