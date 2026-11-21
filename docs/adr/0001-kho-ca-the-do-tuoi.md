# ADR 0001 — Kho cá thể + độ tươi (Ticket-03, contract v1.2)

**Trạng thái:** Chấp nhận (Phase 3, C/Integrator) · **Nguồn:** [TICKET-03](../prd/TICKET-03.md)

## Bối cảnh
Kho đếm theo loại `{"items":{kind:n}}` → kho cá thể `{"items":[{id,kind,fresh}]}`; giữ chỗ theo id; giá theo tươi; hàng ươn (< 30). Breaking change cho file kho, scenario (`gather.hold`, `quan.stock`, `customers[].reserved`), snapshot và nhiều test.

## Quyết định
1. **Một lần chuyển, không chạy song song hai schema:** `contract_version` = 1.2, file kho đếm → mã 2. Lý do: còn ~20 phút, hai đường code dễ lệch.
2. **Độ tươi lưu số nguyên `u` = fresh × 240** (gather −2/tick, quán −1/tick, ngưỡng 7200) → so ngưỡng và `floor` chính xác; xuất `fresh = u/240`.
3. **Id cá thể `I1, I2…` cấp bằng `IdAllocator` dùng chung** (xuyên pha và Ngày trong `day`); id trong scenario được `reserve`.
4. **Module chung `chonoi/items.py`** (C): tạo/hao/ươn/chọn tươi nhất/serialize — gather, quán, day, inventory cùng dùng.
5. **Thứ tự tích hợp (main luôn chạy):** C đẩy lõi (items + inventory + gather + quán + day + scenario + contract) trong **một commit** kèm sửa test của C → các chủ test sửa fixture của mình trên main mới → C merge, chạy regression, tag.

## Tác động

| Module | File | Test bị ảnh hưởng | Người |
|---|---|---|---|
| Adapter kho + contract | `chonoi/items.py` (mới), `inventory.py`, `contract.py`, `game.contract.json`, `scenario.py`, `runner.py` | `test_smoke_p1`, `test_python_starter_units` | C |
| Lặn | `sim/gather.py`, `sim/monsters.py` (lost là cá thể) | `test_gather_unit_a`, `test_gather_p2_a` (A) · `test_gather_rules` (D) · `test_monsters_c` (C) | C code · **A sửa test của A** |
| Quán | `sim/quan.py` (hao tươi, spoiled, giữ theo id, giữ lại, giá theo tươi) | `test_quan_rules` (D) · `test_quan_rules_c` (C) | C code · **B rà luật quán + ghi CHANGELOG** |
| day | `sim/day.py` (bàn giao cùng tick, id mới các Ngày kế) | `test_day_shop_c` (C) | C |
| HUD | `web/index.html` (thanh/nhãn độ tươi, hàng ươn) | `test_live` | C (A hỗ trợ nếu xong sớm) |
| QA | `tests/test_p3_*.py`, `docs/verification/phase-3.md`, `docs/proof/phase-3/` | AC-P3-01..08 | **D** |

## Hệ quả
- Mọi fixture `hold` dạng chuỗi và `stock` dạng map phải đổi sang mảng cá thể (ghi trong CHANGELOG + lý do trong commit).
- Mở rộng (dòng lũ, khách đặt trước) **không làm** — nhóm 4 người không bắt buộc.
