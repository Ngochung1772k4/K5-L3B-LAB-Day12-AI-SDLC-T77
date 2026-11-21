# CHANGELOG

## v1.2 — Phase 3 "Mùa Nước Nổi" (Ticket-03) · BREAKING CHANGE

**Kho đếm theo loại → kho cá thể có độ tươi.** Quyết định và tác động: [ADR 0001](docs/adr/0001-kho-ca-the-do-tuoi.md).

### Breaking
- `game.contract.json`: `contract_version` **1.2**, thêm `freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.
- **File kho** `{"items": {kind: n}}` → `{"items": [{"id","kind","fresh"}]}` (sắp theo id). Kho đếm cũ, kind lạ, id trùng/rỗng, fresh ngoài [0,100] → **mã 2**.
- **Scenario:** `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là **mảng id** (trỏ tới cá thể chưa ươn trong kho, đúng công thức, không dùng chung).
- **Snapshot/JSONL:** `hold`, `stock` (quán, Shop), `customers[].reserved` theo schema mới; `cook_started.items`, `monster_hit.lost`, `faint.lost` là mảng cá thể; `gather_end.inventory` cùng schema file.
- **Giá:** `base_price = floor(giá niêm yết × trung bình fresh / 100)` lúc bắt đầu nấu; boa tính trên giá đã chốt.

### Mới
- Event `spoiled {item_id, kind, location: hold|stock}` — đúng một lần khi qua ngưỡng 30, theo id.
- Giỏ hao 0.5/s, kho quán 0.25/s (kể cả hàng đang giữ); pause dừng hao; món chín không hao. Lưu nội bộ `u = fresh × 240` để so ngưỡng/floor chính xác.
- Giữ chỗ theo id (tươi nhất, hòa theo id); cá thể vừa ươn → nhả toàn bộ phần giữ và thử giữ lại một lần, không đủ → `unfulfillable`.
- `day`: bàn giao cá thể cùng tick không hao thêm; Ngày kế cấp id mới cho mẫu `gather.hold`. Id `I1, I2…` tăng xuyên pha và Ngày.

### Rà soát luật quán v1.2 (B — PhamMinhDuc)

Các luật sau đã được xác minh chạy đúng trên code C:

| Luật | Kết quả |
|---|---|
| Hao tươi kho quán: −0.25/s = −1 u/tick, kẹp 0 | ✅ |
| `spoiled` phát đúng một lần khi u đi từ ≥ 7200 xuống < 7200, theo id | ✅ |
| `_rereserve`: nhả toàn bộ phần giữ khi cá thể ươn, thử lại theo order_tick→id bàn | ✅ |
| Nếu còn cá thể tươi → giữ lại thành công (`reserved` cập nhật) | ✅ |
| Không đủ cá thể tươi → `unfulfillable`, khách chờ tới hết kiên nhẫn | ✅ |
| Giá: `floor(giá niêm yết × sum(u) / (n × 100 × 240))` = `floor(price × avg_fresh / 100)` | ✅ |
| Boa tính trên `base_price` đã chốt theo tươi, không phải giá niêm yết | ✅ |
| `cook_started.items` = mảng cá thể sắp theo kind rồi id | ✅ |

Đơn `unfulfillable` không nhận `no_dish` — khách tiếp tục chờ tới hết kiên nhẫn rồi rời.

### Cách cập nhật fixture
```jsonc
// cũ (v1.1)                         // mới (v1.2)
"hold": ["ca_loc", "bong_sung"]      "hold": [{"id":"I1","kind":"ca_loc","fresh":100}, {"id":"I2","kind":"bong_sung","fresh":100}]
"stock": {"ca_loc": 1}               "stock": [{"id":"I1","kind":"ca_loc","fresh":100}]
"reserved": {"ca_loc": 1}            "reserved": ["I1"]
{"items": {"ca_loc": 1}}  (file)     {"items": [{"id":"I1","kind":"ca_loc","fresh":100}]}
```
Trong test: `tests/helpers.py` có `items(*kinds, fresh=100)`, `stock_of({kind: n})`, `counts(list)`.

## v1.1 — Phase 2 (Ticket-02)
Số chuẩn, 6 nguyên liệu/6 món, 2 bếp/4 bàn, cá bơi/sinh, Cá Sấu, `--mode day`, Shop, nâng cấp, pause. Xem [verification phase-2](docs/verification/phase-2.md).

## v1.0 — Phase 1 (PRD-0)
Gather + Quán + file kho đếm. Xem [verification phase-1](docs/verification/phase-1.md).
