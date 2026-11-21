# Phase 4 — Phát hành v1.0.0 (Ticket-04, v1.3) · hạn 3:00 (~11:59)

| Vai (Ticket-04 mục 4) | Người | Đã làm |
|---|---|---|
| Đóng gói | C | Thử clone sạch (tìm và sửa lỗi in tiếng Việt của `chonoi.live`), README ≤ 3 lệnh, zip `git archive` |
| Bench/QA | C (D bổ sung test P3) | `bench.json`, `soak.json`, 150 test, [verification phase-4](../verification/phase-4.md) |
| Release/Integrator | C | CHANGELOG, release notes, tag `phase-4` + `v1.0.0` (cùng `8ca55cc`), Release công bố 11:53 |
| Điều phối retro | C | [retro.md](../retro.md) rà hành động P2 |
| Phản tư cá nhân | Mỗi người tự viết | `docs/members/<handle>.md` |

Thực tế: phần lớn P4 do C làm vì sát giờ; A cập nhật phản tư + verification, D push 53 test P3 (bắt 2 lỗi code). Sau giờ build: `--mode day` trong cửa sổ chơi (Release `v1.0.1`).
