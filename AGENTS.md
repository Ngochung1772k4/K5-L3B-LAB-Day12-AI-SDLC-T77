# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl [--days 1..5]`
- Bench / soak (v1.3): `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` · `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`
- Chơi trên trình duyệt: `python3 -m chonoi.live --mode day` (hoặc `gather` / `quan`; WASD, E, Space, P/Esc, H, 1/2/Enter ở Shop, R)
- Windows: không có `python3` thì copy `python.exe` thành `python3.exe` (test gọi `headless_cmd`).

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py` (A), `chonoi/sim/quan.py` + `chonoi/sim/monsters.py` (B), `chonoi/sim/day.py`, `chonoi/sim/fish.py`, `chonoi/items.py` (C — vòng Ngày, cá bơi/sinh, kho cá thể + độ tươi), `chonoi/bench.py`, `chonoi/soak.py`.
- Đọc theo thứ tự trước khi code: `docs/prd/` (PRD-0, TICKET-02..04) → `docs/contracts/README.md` → `docs/adr/` → `docs/plan/phase-n.md` (phần của mình).
- Fixture test v1.2: dùng `tests/helpers.py` `items(...)`, `stock_of(...)`, `counts(...)`.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Bài học quy trình (cập nhật qua retro)
- Integrator trước khi gắn tag: `git fetch` + liệt kê mọi nhánh, xác nhận với trưởng nhóm; không làm thay lát của người khác khi chưa hỏi.
- Mỗi nhánh tách từ `main` mới nhất (`git pull --rebase origin main`), merge bằng merge commit (giữ commit từng người); không force-push nhánh đã merge.
- Đổi contract/schema: viết ADR + CHANGELOG, đổi test cũ phải ghi lý do trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- D / QA: [`run-tests-proof`](.agents/skills/run-tests-proof/SKILL.md) — dùng sau thay đổi gameplay hoặc khi cần proof Phase 1; chạy Gather, Quán, toàn bộ unittest và smoke hai tiến trình, lưu log/exit code/revision thật vào thư mục proof mới.
- D / QA: [`check-determinism`](.agents/skills/check-determinism/SKILL.md) — dùng khi đổi RNG, seed, timer hoặc thứ tự event; chạy hai lần cùng dữ liệu trong hai thư mục tạm, so JSONL và inventory từng byte.
- Khi FAIL, báo owner A/B/C cùng fixture/input, seed, tick, expected/actual và proof. Không tự sửa contract hoặc assertion để làm xanh; không sửa file ngoài phạm vi đang được giao.
- Tắt bytecode khi chạy QA; không ghi đè proof cũ. Đây là hướng dẫn thao tác cho agent, chưa cài hook tự chạy. Cách gọi: yêu cầu dùng `$run-tests-proof` hoặc `$check-determinism`, hoặc đọc trực tiếp `SKILL.md` tương ứng.
