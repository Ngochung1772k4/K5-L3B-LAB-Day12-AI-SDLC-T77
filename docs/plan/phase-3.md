# Phase 3 — Kho cá thể + độ tươi (Ticket-03, v1.2) · hạn tag ~11:34

Đọc: [TICKET-03](../prd/TICKET-03.md) · [ADR 0001](../adr/0001-kho-ca-the-do-tuoi.md) (bảng tác động + thứ tự tích hợp). **Không làm mở rộng.**

| Người | Việc | Khi nào |
|---|---|---|
| **C** | Lõi v1.2: `items.py`, inventory, gather, quán, day, scenario, contract + sửa test của C | push ~11:22 |
| **A** | Sau khi C push: sửa fixture `tests/test_gather_unit_a.py`, `tests/test_gather_p2_a.py` sang `hold` cá thể (`{"id","kind","fresh"}`), assertion `hold` so theo `kind`/`id` | push nhánh `a/p3-tests` ~11:28 |
| **B** | Rà luật quán v1.2 (giữ theo id, giữ lại khi ươn, giá `floor(giá × tb fresh / 100)`) trên code C; viết **CHANGELOG.md** (breaking change, schema mới, cách đổi fixture) | push `b/p3-changelog` ~11:28 |
| **D** | Sửa fixture `tests/test_gather_rules.py`, `tests/test_quan_rules.py`; test mới `tests/test_p3_freshness_d.py` (ngưỡng 30 → `spoiled` tick 1, smoke bàn giao file, kho đếm → mã 2); `docs/verification/phase-3.md` | push `d/p3-qa` ~11:28 |

Mẫu cá thể: `{"id":"I1","kind":"ca_linh","fresh":100}` · kho file `{"items":[...]}` sắp theo id · `customers[].reserved` = mảng id.
