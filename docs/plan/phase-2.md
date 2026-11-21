# Phase 2 — Kế hoạch & chia việc (Ticket-02, Test Contract v1.1)

> **Đọc trước:** [TICKET-02](../prd/TICKET-02.md) (mục 1–2 luật, mục 4 contract v1.1, mục 4.5 thứ tự) · [PRD-0 mục F](../prd/PRD-0.md) (luật v1.0 vẫn giữ) · [hợp đồng](../contracts/README.md).
> **Hạn tag `phase-2`: ~11:14** (phát hành 10:19 + 55'). Bỏ mọi mục **Mở rộng** (nhóm 4 người không bắt buộc).
> Tình hình đầu phase: `phase-1` đã tag muộn, 53 test xanh. D chưa có đóng góp → kế hoạch dựa trên A, B, C; phần D là tùy chọn, C gánh phần tối thiểu.

## Ưu tiên (theo điểm test ẩn)

| # | Hạng mục | Ai | Vì sao |
|---|---|---|---|
| 1 | Contract v1.1 + 6 nguyên liệu + 6 món + B2/T2–T4 | C | Chặn việc mọi người, ít công, nhiều test |
| 2 | `--mode day` + Shop + nâng cấp + pause | C | Lõi mới của Phase 2 |
| 3 | Cá bơi + sinh cá theo lịch | A | Test gather v1.1 |
| 4 | Cá Sấu + bất tử + ngất do quái | B | Test gather v1.1 |
| 5 | Quán lọc món theo kế hoạch ngày, nhận tiền/uy tín xuyên Ngày | B | Cần cho `day` |
| 6 | Regression P1 với số chuẩn, test P2, verification | C (D nếu quay lại) | DoD |
| 7 | Menu, pause UI, HUD đầy đủ | C (nếu còn giờ) | Demo, không chấm headless |

## Giao diện chốt trước (để code song song)

### Khóa tuning v1.1 (C ghi vào `game.contract.json` — A/B dùng đúng tên này)

```jsonc
"gather": {
  "fish_initial": 8, "fish_speed": 1.5, "fish_turn_ticks": 120, "fish_max": 12,
  "fish_spawn_ticks": 360, "fish_spawn_clearance": 1.0, "fish_x": [4, 96],
  "fish_depths":       {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]},
  "fish_spawn_x":      [15, 30, 45, 60, 75, 90],
  "fish_spawn_depths": {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]},
  "fish_weights":      {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3},
  "fish_yield":        {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
  "nodes": [... N1–N4 như cũ, {"id":"N5","kind":"keo_neo","pos":[76,0]}, {"id":"N6","kind":"keo_neo","pos":[90,0]}],
  "monsters": {
    "species": {"ca_sau": {"patrol_speed": 1.0, "chase_speed": 3.0, "detect_radius": 10, "exit_radius": 16,
                           "depths": [10, 30], "hit_radius": 1.5, "recoil_ticks": 60, "recoil_dist": 2.0}},
    "spawns": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1},
               {"id": "M2", "kind": "ca_sau", "pos": [85, 18], "waypoints": [[85, 18], [89, 18]], "from_day": 3}],
    "invuln_ticks": 90, "loss_ratio": 0.5
  }
},
"quan": { "stoves": B1 [2,8], B2 [5,8]; "tables": T1 [9,2], T2 [13,2], T3 [9,6], T4 [13,6] },
"menu": { + canh_chua_ca_loc, ca_keo_nuong, lau_mam },
"day_plan": [{"day": 1, "dishes": {...}, "ingredients": {...}}, ... 5 ngày],
"shop": {"max_ticks": 600, "upgrades": {
  "oxygen": [{"level": 1, "price": 200, "oxygen_max_s": 45}, {"level": 2, "price": 400, "oxygen_max_s": 60}],
  "hp":     [{"level": 1, "price": 250, "hp_max": 4},        {"level": 2, "price": 500, "hp_max": 5}]}}
```

### Tham số khi `day` dựng từng pha (C gọi, A/B nhận)

```python
GatherSim(tuning, scenario, streams, ids, ctx=None)
QuanSim(tuning, scenario, streams, ids, inventory=None, ctx=None)
# ctx = None khi chạy mode độc lập. Trong day:
# gather: {"day": n, "hp_max": int, "oxygen_max_s": num}            -> Máu/oxy đầy theo cấp, quái theo from_day <= n
# quan:   {"day": n, "dishes": [id món kế hoạch], "money": m, "earned": e, "reputation": r}
#         -> lọc menu theo kế hoạch TRƯỚC khi lọc nguyên liệu; money/earned/reputation khởi từ ctx
```

- `streams` (RNG) và `ids` do `day` truyền vào, **dùng chung cả lượt**. Tên luồng RNG riêng: `fish_turn`, `fish_spawn`, `customer_dish` (đã có).
- Cá Sấu (B) ở file mới `chonoi/sim/monsters.py`: `make_monsters(tuning, scenario, day) -> list` và `step_monsters(sim, events) -> bool` (trả True nếu người chơi ngất, đã phát `faint` + `gather_end`). A gọi trong `GatherSim.step()` đúng chỗ ở Ticket mục 4.5.

## A — `sim/gather.py`: cá bơi + sinh cá (+ gọi Cá Sấu)

- [ ] Đầu ca (khi `random_fish` bật và scenario không khai `fish`): sinh `fish_initial` đàn ở các điểm **khác nhau** theo luật chọn loài/điểm bên dưới (RNG `fish_spawn`).
- [ ] Mỗi đàn có `age_ticks` (số bước đã bơi). Cá bơi ở **cuối bước, chỉ khi còn giờ**, sau bắt cá (bắt theo vị trí trước khi bơi).
  - Tại `age_ticks` mới = 120, 240, … đổi hướng theo seed (RNG `fish_turn`) **trước** khi di chuyển.
  - Đi `fish_speed/60` m mỗi bước theo `heading_deg`. Miền: x ∈ `fish_x`, d ∈ `fish_depths[kind]`. Tới mép: phản xạ phần quãng đường còn lại, đảo thành phần hướng vuông góc với mép; chạm góc thì đảo cả hai.
- [ ] Sinh theo lịch: tại `phase_tick = 360·k` (k ≥ 1), sau cá bơi, nếu số đàn < `fish_max`: lọc điểm (x ∈ `fish_spawn_x`, d ∈ `fish_spawn_depths[kind]`) cách **mọi** đàn đang sống > `fish_spawn_clearance`. Chọn loài theo `fish_weights` chuẩn hóa trên các loài còn điểm, rồi chọn đều một điểm, hướng theo seed. Phát `fish_spawned {id,kind,pos}`. Cấp id `self.ids.new("F")`.
- [ ] `random_fish: false` → không cá mặc định, cá fixture **đứng yên**, không sinh.
- [ ] Nhận `ctx` (Máu/oxy tối đa theo cấp). Gọi `step_monsters` sau oxy/ngạt, trước interact. Snapshot thêm `monsters[]`, `player.invuln_ticks`.
- [ ] Sửa `fish_yield` dùng đủ 3 loài; nút N5/N6 (kèo nèo) chạy sẵn từ dữ liệu.

**Commit:** `gather: cá bơi + phản xạ mép` · `gather: sinh cá theo lịch` · `gather: nối Cá Sấu + ctx day`

## B — `sim/monsters.py` (Cá Sấu) + `sim/quan.py` (kế hoạch ngày)

### Cá Sấu (Ticket 1.2)
- [ ] `make_monsters`: lấy `spawns` có `from_day ≤ day` (mode gather độc lập dùng Ngày 1), hoặc `scenario.monsters` nếu có. Trường: `id,kind,pos,waypoints,target_idx (mặc định 1),state (patrol),state_ticks_left,recoil_dir`.
- [ ] `step_monsters` theo id: `patrol` 1.0 m/s về waypoint, tới nơi đổi `target_idx` cho bước sau. Người chơi d ≥ 10 và cách ≤ 10 m → `chase` 3.0 m/s về phía người chơi; cách > 16 m hoặc người chơi lên d < 10 → patrol. Chặn biên map và `depths` của loài.
- [ ] Hit: sau khi cả hai di chuyển, cách ≤ 1.5 m, người chơi d ≥ 10, `invuln_ticks == 0` → chọn con gần nhất (hòa theo id), tối đa 1 hit/bước. `hp -= 1`; bỏ `floor(len(hold)*loss_ratio)` món theo LIFO; `invuln_ticks = 90`; phát `monster_hit {monster_id,hp,lost,pos}`.
- [ ] Con gây hit: `recoil` 60 bước **từ bước sau**, hướng xa người chơi chốt lúc chạm (trùng tâm dùng +x), mỗi bước `recoil_dist/recoil_ticks` m, không gây hit. Hết recoil → patrol.
- [ ] `hp == 0` → `faint {cause:"monster", lost:<phần giỏ còn lại LIFO>, hp:0}` rồi `gather_end(fainted)`, trả True.

### Quán (Ticket 1.3, 2)
- [ ] 2 bếp / 4 bàn / 6 món chạy từ dữ liệu (code hiện tại đã duyệt theo dữ liệu — chỉ cần kiểm).
- [ ] Nhận `ctx`: lọc `cookable` theo `ctx["dishes"]` trước khi xét nguyên liệu; khởi `money/earned/reputation` từ ctx (`shift_earned` vẫn từ 0).

**Commit:** `monsters: patrol/chase` · `monsters: hit, recoil, bất tử, ngất` · `quan: lọc món theo kế hoạch + ctx day`

## C — Contract v1.1, khung, `day`, Shop, pause (Integrator)

- [ ] **(Làm đầu tiên, push ngay)** `game.contract.json` v1.1 đầy đủ khóa ở trên; `inventory.py` 6 kind; hợp đồng `docs/contracts/README.md` thêm sự kiện v1.1.
- [ ] Sửa test P1 bị đổi bởi số chuẩn (6 → 8 đàn cá, 4 bàn…), ghi lý do trong commit.
- [ ] Khung: `inputs.py` nhận `pause`, `shop_done`, `buy`; `headless.py` nhận `--mode day`, `--days 1..5`; runner: pause (chỉ tăng tick ngoài, `sim_tick`/`phase_tick` đứng yên, `paused`/`resumed`, `state:"paused"`), vỏ event có `day`, dòng end có `days_completed`.
- [ ] `chonoi/sim/day.py`: vòng `day_start → day_plan → phase_start(gather)` → gather → `phase_start(quan)` → quán → `phase_start(shop)` → Shop (`buy`, `bought`/`buy_failed`, `shop_done`, tự đóng 600 tick, `shop_end`) → Ngày kế; `active_upgrades` chỉ cập nhật khi dựng Ngày mới; `days_complete`.
- [ ] `scenario.py`: khối `day {money,earned,reputation,upgrades,day_plan}`, cấm `quan.stock`/`quan.reputation` khi day; kiểm `gather.monsters[]`, `fish[].age_ticks`.
- [ ] Smoke tích hợp → `docs/proof/phase-2/integration.*`; smoke `day --days 1` và nhiều Ngày; `docs/verification/phase-2.md`; `docs/retro.md`; tag.
- [ ] Nếu còn giờ: màn DayIntro/EveningIntro/DayResult/Shop + pause trong `chonoi.live`.

## D — tùy chọn (nếu quay lại)

Nhận từ C: test P2 (`tests/test_p2_*.py`) theo bảng AC dưới + `docs/verification/phase-2.md`. Báo C trước khi bắt đầu để không trùng.

## AC Phase 2

| AC | Nội dung |
|---|---|
| AC-P2-01 | `contract_version` 1.1, 6 kind, 6 món, B2, T2–T4, N5/N6 |
| AC-P2-02 | Đầu ca 8 đàn ở 8 điểm khác nhau; cá bơi 1.5 m/s, đổi hướng ở bước 120/240…, phản xạ mép |
| AC-P2-03 | Sinh cá tại `phase_tick` 360·k, trần 12, khoảng cách > 1 m, `fish_spawned` |
| AC-P2-04 | Cá Sấu patrol/chase/thoát chase đúng ngưỡng; M2 chỉ từ Ngày 3 |
| AC-P2-05 | `monster_hit`: −1 Máu, mất floor(n/2) LIFO, bất tử 90, recoil 60 bước |
| AC-P2-06 | Ngất do quái: `faint cause monster`, quán vẫn mở với kho rỗng |
| AC-P2-07 | Smoke tích hợp gather → quan với số chuẩn |
| AC-P2-08 | `day --days 1`: `day_start → day_plan → phase_start` đúng thứ tự, `day_plan` đúng D1 |
| AC-P2-09 | Quán trong day chỉ gọi món của kế hoạch |
| AC-P2-10 | Shop: `bought`/`buy_failed (funds/max_level/unknown)`, trừ `money` giữ `earned`, đóng bằng `shop_done` hoặc 600 tick |
| AC-P2-11 | Cấp oxy/hp có hiệu lực từ Ngày kế (`active_upgrades`) |
| AC-P2-12 | Pause: chỉ tick ngoài tăng, timer đứng, `paused`/`resumed`, `state:"paused"` |
| AC-P2-13 | `--days 5` kết thúc `days_complete`, `days_completed: 5`; một Ngày ≤ 20 s |
| AC-P2-14 | Regression P1 với số chuẩn còn xanh |

## Lịch (giờ thực)

| Giờ | A | B | C |
|---|---|---|---|
| ngay | Đọc Ticket 1.1, 4.5 | Đọc Ticket 1.2, 1.3 | Contract v1.1 + inventory → **push** |
| +15' | Cá bơi | Cá Sấu patrol/chase | Khung pause/day/inputs |
| ~10:50 | Sinh cá → **push nhánh** | Hit/recoil/ngất + quán ctx → **push nhánh** | Smoke tích hợp, `day.py` + Shop |
| ~11:00 | Sửa theo test | Sửa theo test | Merge A, B; smoke `day`; verification |
| **11:10** | — | — | **Tag `phase-2`**, retro |

## Quy tắc (giữ như Phase 1)

- Mỗi file một chủ: `gather.py` → A · `monsters.py`, `quan.py` → B · `game.contract.json`, `chonoi/*.py` khung, `day.py`, `scenario.py`, `web/` → C · `tests/test_p2_*` → D.
- Nhánh `a/p2-...`, `b/p2-...`; trước push: `git pull --rebase origin main` + chạy test. **Chỉ C merge và tag.** Merge bằng *Create a merge commit*.
- Prompt cho AI: *"Đọc AGENTS.md, docs/prd/TICKET-02.md (mục …), docs/plan/phase-2.md (phần của tôi). Chỉ sửa file của tôi. Dùng đúng tên khóa tuning và ctx trong plan. Chạy test trước khi commit."*
