# Hợp đồng tích hợp — Phase 1

> Chủ file: **C (Integrator)**. Nguồn: [PRD-0](../prd/PRD-0.md) mục D, E, G. Đổi hợp đồng thì báo cả nhóm trước và ghi lý do vào "Lịch sử thay đổi".

## 1. File kho (PRD-0 mục G)

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Chỉ có khóa gốc `items`: kind → số nguyên ≥ 0. Kind vắng = 0; khi ghi thì bỏ khóa có lượng 0. Kho rỗng: `{"items":{}}`.
- Kind hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Sai schema / kind lạ / số âm → mã 2.
- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end`, khớp `inventory` trong event đó. Ngất → `{"items":{}}`. Chạm `--ticks` trước khi buổi sáng kết thúc → **không** tạo/ghi đè file. Ghi file tạm rồi thay thế nguyên tử (khung đã làm).
- `quan --inventory` đọc file. Khai cả `--inventory` lẫn `scenario.quan.stock` → mã 2. Thiếu cả hai → kho rỗng. Trần giỏ không áp lên kho quán.
- Mẫu: [`inventory.sample.json`](inventory.sample.json).

## 2. Sự kiện (PRD-0 mục E)

Dòng: `{"type":"event","tick":k,"phase":"gather|quan","name":...,"data":{...}}`, ghi theo thứ tự xử lý, sau đó tới snapshot. `items`, `lost` là mảng kind.

### Gather — A phát

| name | data | Ví dụ |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển | `{"pos":[20.0,0.6]}` |
| `oxygen_empty` | `oxygen_ticks: 0` | `{"oxygen_ticks":0}` |
| `choke` | `hp` sau khi trừ | `{"hp":2}` |
| `faint` | `cause:"choke"`, `lost` (LIFO: nhặt sau bỏ trước), `hp:0` | `{"cause":"choke","lost":["bong_sung","ca_loc"],"hp":0}` |
| `gather` | `node_id, kind, amount` | `{"node_id":"N1","kind":"bong_dien_dien","amount":1}` |
| `node_regrown` | `node_id` | `{"node_id":"N1"}` |
| `fish_caught` | `fish_id, kind, yield` | `{"fish_id":"F1","kind":"ca_linh","yield":3}` |
| `hold_full` | `action` (`gather`/`catch`), `node_id` hoặc `fish_id`, `required, free` | `{"action":"catch","fish_id":"F1","required":3,"free":1}` |
| `gather_end` | `reason` (`time`/`docked`/`fainted`), `inventory` theo G | `{"reason":"docked","inventory":{"items":{"ca_loc":1}}}` |

### Quán — B phát

| name | data |
|---|---|
| `customer_arrived` | `order_id, table_id, dish_id` |
| `no_dish` | `{}` (có bàn trống nhưng không món nào đủ nguyên liệu) |
| `cook_started` | `stove_id, order_id, dish_id, items` (mảng kind, sắp theo kind), `base_price` |
| `dish_ready` | `stove_id, order_id, dish_id` |
| `dish_picked` | `stove_id, order_id, dish_id` |
| `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` |
| `paid` | `order_id, table_id, base_price, tip, amount, reason` (`finished_eating`/`closing`) |
| `customer_left` | `order_id, table_id, reason` (`patience`/`closing`), `reputation` |
| `quan_end` | `reason:"time", money, earned, shift_earned, reputation` |

`order_id` = id khách.

## 3. Snapshot — trường UI đọc (PRD-0 mục D, E)

**Chung (runner lo):** `type, tick, sim_tick, mode, phase, phase_tick, state (playing/finished), time_left_ticks, money, earned, reputation, score`. Điểm = `earned + 100 × floor(reputation)`.

**Gather (A giữ, khung đã đủ):**
- `player`: `pos, vel, heading_deg, oxygen_ticks, hp, zero_oxy_ticks, catch_cd_ticks, oxygen_max_ticks, hp_max, at_surface`
- `hold` (theo thứ tự nhặt, mới nhất cuối), `hold_count`, `hold_capacity`
- `nodes[]`: `id, kind, pos, regrow_ticks, ready` · `fish[]`: `id, kind, pos, heading_deg`

**Quán (B giữ):**
- `player`: `pos, vel`
- `stock`: kho **vật lý** (gồm cả phần đang giữ chỗ)
- `hand`: `null` hoặc `{order_id, dish_id, base_price}`
- `stoves[]`: `id, pos, state (idle/cooking/ready), dish, cook_ticks_left, ready_ticks`. `dish` dùng cùng payload món `{order_id, dish_id, base_price}`.
- `tables[]`: `id, pos, customer_id` (trống → `null`)
- `customers[]` (chỉ khách còn ngồi): `id, table_id, dish_id, order_tick, state (waiting/eating), patience_ticks_left, eat_ticks_left, order_status (reserved/assigned/unfulfillable/served), reserved {kind: số}, base_price, tip`

Mọi mảng thực thể sắp theo id (`ids.sort_by_id`), tọa độ làm tròn 3 chữ số (khung lo).

## 4. Lệnh UI gửi vào sim

Chỉ qua input chuẩn (`chonoi/inputs.py`): `move [x, y]`, `interact` (E), `catch` (Space, chỉ gather). Nút chỉ có tác dụng ở cạnh lên. UI **không** sửa trạng thái sim.

## 5. Điểm còn mơ hồ (A hỏi Anh Năm, ghi `docs/clarify.md`)

- `stoves[].dish`: payload món hay chỉ `dish_id`? (Tạm chọn payload để thống nhất với `hand`.)
- Đơn chuyển sang `unfulfillable` khi nào ở Phase 1 (không có cháy món)?
- `customer_left.reputation`: uy tín **sau** khi trừ? (Tạm chọn: sau.)


## 6. Thay đổi v1.1 (Phase 2 — [TICKET-02](../prd/TICKET-02.md) mục 4)

- **Kho:** 6 kind (`ca_keo`, `keo_neo` mới). Schema không đổi. `day` bàn giao kho trong bộ nhớ.
- **CLI:** `--mode day`, `--days 1..5` (chỉ với day). Nút mới `pause` (cả 3 mode), `shop_done`; `buy` là chuỗi (`oxygen`/`hp`).
- **Giao diện `day` → pha** (C giữ): `GatherSim(..., ctx={"day","hp_max","oxygen_max_s"})`, `QuanSim(..., ctx={"day","dishes","money","earned","reputation"})`. `streams`/`ids` dùng chung cả lượt.
- **Vỏ event mode day:** `{"type","tick","phase","day","name","data"}`. Event kết thúc mang pha cũ; `phase_start` mang pha mới, cùng tick.

| name | data | Ai phát |
|---|---|---|
| `day_start`, `phase_start` | `{}` | day |
| `day_plan` | `dishes, ingredients` | day |
| `fish_spawned` | `id, kind, pos` | gather (sim/fish.py) |
| `monster_hit` | `monster_id, hp, lost (LIFO), pos` (vị trí người chơi) | gather (sim/monsters.py) |
| `faint` | `cause: "choke"\|"monster", lost, hp: 0` | gather |
| `paused`, `resumed` | `{}` | runner (mọi mode) |
| `bought` | `upgrade, level, price, money` | shop |
| `buy_failed` | `action, reason` (`funds`/`max_level`/`unknown`) | shop |
| `shop_end` | `reason` (`done`/`time`) | shop |

- **Snapshot:** `state` thêm `"paused"`. Gather thêm `monsters[]` (`id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir`), `fish[].age_ticks`, `player.invuln_ticks`. Mode day thêm `day, day_plan, upgrades, active_upgrades`; `phase` ∈ gather/quan/shop; Shop có `stock` dư và `time_left_ticks`. Có snapshot ở tick đổi pha (`phase_tick: 0`).
- **End mode day:** thêm `days_completed`; xong đủ Ngày → `reason: "days_complete"`.

## 7. Thay đổi v1.2 (Phase 3 — [TICKET-03](../prd/TICKET-03.md), [ADR 0001](../adr/0001-kho-ca-the-do-tuoi.md))

- **File kho = kho cá thể** `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`, sắp theo id; kho rỗng `{"items":[]}`. Kho đếm cũ, kind lạ, id trùng/rỗng, `fresh` ngoài [0,100] → **mã 2**. Id `I1, I2…` cấp theo thứ tự vào giỏ, tăng xuyên pha và Ngày.
- **Scenario:** `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là **mảng id** (cá thể chưa ươn trong kho, đúng công thức, không dùng chung).
- **Snapshot:** `hold`, `stock` (quán, Shop), `customers[].reserved` theo schema mới; `fresh` xuất đủ chính xác (không làm tròn 3 chữ số).
- **Sự kiện:** mới `spoiled {item_id, kind, location: hold|stock}`; `cook_started.items`, `monster_hit.lost`, `faint.lost` là mảng cá thể; `base_price` = `floor(giá × trung bình fresh / 100)`.
- **Nội bộ (C giữ):** `chonoi/items.py` — `u = fresh × 240` (gather −2/tick, quán −1/tick, ngưỡng 7200).

## 8. Thay đổi v1.3 (Phase 4 — Ticket-04)
- Manifest thêm `bench_cmd` (`python3 -m chonoi.bench --seed --duration --out`) → `{avg_fps,p1_low_fps,frames,measured_s,load_ms}` và `soak_cmd` (`python3 -m chonoi.soak --seed --days --out`) → `{days,days_completed,crashes,results[],duration_s}`. Gameplay, kho, JSONL giữ v1.2.
- Cửa sổ chơi: `--mode day` (sau giờ build); client gửi thêm `pause`, `shop_done`, `buy` qua `POST /input`.

## Lịch sử thay đổi

| Thời điểm | Thay đổi | Lý do | Ai |
|---|---|---|---|
| Phase 1, kickoff | Bản đầu, theo PRD-0 mục D/E/G | | C |
| Phase 2 | v1.1: 6 kind, day/Shop/pause, sự kiện mới, ctx day | Ticket-02 đổi contract | C |
| Phase 3 | v1.2: kho cá thể + độ tươi (breaking) | Ticket-03, ADR 0001 | C |
| Phase 4 | v1.3: bench_cmd, soak_cmd | Ticket-04 | C |
