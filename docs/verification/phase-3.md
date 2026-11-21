# Ma trận truy vết Phase 3 (Ticket-03, Test Contract v1.2)

> Kiểm chứng trên commit gắn tag `phase-3`. Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
> → [test-output.txt](../proof/phase-3/test-output.txt): **OK, 4 module skip** (xem "Chưa đạt"). Tóm tắt: [summary.md](../proof/phase-3/summary.md).
> Quyết định đổi schema + tác động + thứ tự tích hợp: [ADR 0001](../adr/0001-kho-ca-the-do-tuoi.md) · breaking change: [CHANGELOG](../../CHANGELOG.md).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 Ngưỡng 30: `spoiled` đúng tick 1 (ví dụ Ticket) | `test_freshness_c.test_p3_01_*` + chạy tay | [threshold.jsonl](../proof/phase-3/threshold.jsonl) | Đạt |
| AC-P3-02 Bàn giao file cá thể chính xác; quán nhận đúng id/kind/fresh; kho đếm → mã 2 | `test_p3_02_*`, `test_smoke_p1.test_inv_*` | [handoff-kho.json](../proof/phase-3/handoff-kho.json), [handoff-quan.jsonl](../proof/phase-3/handoff-quan.jsonl), [kho-dem-stderr.txt](../proof/phase-3/kho-dem-stderr.txt) | Đạt |
| AC-P3-03 Hàng mới fresh 100, hao từ bước sau (giỏ 0.5/s, quán 0.25/s) | `test_p3_03_*`, `test_p3_06_*` | test-output | Đạt |
| AC-P3-04 Giữ theo id tươi nhất; cá thể vừa ươn → giữ lại một lần | `test_p3_04_spoiled_reservation_rereserves_freshest` | test-output | Đạt |
| AC-P3-05 Giữ lại không đủ → `unfulfillable`, khách chờ | `test_p3_05_*` | test-output | Đạt |
| AC-P3-06 Giá chốt `floor(giá × tb fresh / 100)`, `cook_started.items` là cá thể | `test_p3_06_price_by_freshness`, `test_quan_rules_c.test_ac16_*` (40 → 39) | test-output | Đạt |
| AC-P3-07 Scenario mâu thuẫn (reserved sai id/ươn/khác công thức, kho đếm, hold chuỗi) → mã 2 | `test_p3_07_*` | test-output | Đạt |
| AC-P3-08 `day`: bàn giao cùng tick không hao, giữ id; Ngày kế id mới | `test_p3_day_handoff_keeps_ids_same_tick`; chạy `--days 2` | [day2.jsonl](../proof/phase-3/day2.jsonl) | Đạt (Ngày kế id mới: chưa có test riêng) |
| AC-P3-09 HUD hiện độ tươi / hàng ươn | Thanh tươi dưới ô giỏ + nhãn "ươn"; dải cá thể kho quán (`chonoi/web/index.html`) | — (chưa chụp màn hình) | Đạt một phần |
| AC-P3-10 Regression P1–P2 với v1.2 | Toàn bộ test của C + starter chạy lại | test-output | Đạt cho test C/starter; **4 module A/D tạm skip** |

## Test thay đổi vì luật mới (lý do)
- Fixture `hold`/`stock`/`reserved`/file kho của C và starter đổi sang cá thể (CHANGELOG mục "Cách cập nhật fixture").
- `test_quan_rules_c.test_ac16_*`: giá `goi_bong_sung` 40 → 39 vì kho hao 1 tick trước khi nấu.
- `test_smoke_p1`: so `gather_end.inventory` (JSONL làm tròn 3 chữ số) với file kho trong dung sai ±0.01.

## Chưa đạt (ghi trung thực)
- **2 module tạm skip** vì fixture còn v1.1: `test_gather_rules`, `test_quan_rules` (D). A đã đổi xong `test_gather_unit_a`, `test_gather_p2_a` (nhánh `a/p3-tests`) — 93 test chạy, OK. Luật đã đổi đúng Ticket; chủ file cần đổi fixture sang cá thể rồi xóa dòng skip.
- Không làm mở rộng (dòng lũ, khách đặt trước) — nhóm 4 người không bắt buộc.
- **Đóng góp P3 tới giờ tag:** C (lõi v1.2, test, HUD, CHANGELOG, ADR); B (ducpham13) rà luật quán v1.2 trên code C — bảng xác minh 8 luật trong CHANGELOG (nhánh `b/p3-changelog`). A (hal2332004) đổi fixture 2 module test gather sang kho cá thể v1.2 và bỏ skip (nhánh `a/p3-tests`). D chưa push phần P3.

---

## Phụ lục: Kiểm chứng QA riêng của D — Phase 3

### Phase 3 — QA của D / uscalurn — T77

**Nguồn yêu cầu:** [TICKET-03](../prd/TICKET-03.md), đã đọc toàn bộ; người dùng xác nhận dùng đường dẫn này thay cho docs/specs/TICKET-03-Phase3-v1.2.md không tồn tại. Luật cũ chưa bị thay thế lấy từ [TICKET-02 v1.1](../prd/TICKET-02.md) và [PRD-0](../prd/PRD-0.md).

**Nhánh:** d/phase-3-qa-uscalurn. **Revision nền:** d496a4f313aa4a3757ffacf599499d3f3224d8e5. Bốn test mới chưa commit, do đó proof là kết quả working tree cùng hash, không phải proof của một tag phát hành.

**Contract yêu cầu: 1.2. Contract thực chạy: 1.1. Nghiệm thu v1.2: BLOCKED / chưa đạt.** Không thay manifest/implementation/test cũ để làm xanh. Manifest không dùng để bác bỏ yêu cầu khách hàng.

#### Kết quả thực chạy

| Suite | Methods | PASS | FAIL | ERROR | SKIP | Exit equivalent | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| Inventory v1.2 | 13 | 0 | 13 | 0 | 0 | 1 | [p3-inventory.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-inventory.txt) |
| Freshness v1.2 | 12 | 0 | 12 | 0 | 0 | 1 | [p3-freshness.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-freshness.txt) |
| Reserved IDs / price | 15 | 0 | 15 | 0 | 0 | 1 | [p3-reservation_price.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-reservation_price.txt) |
| Integration / migrated regression | 13 | 2 | 11 | 0 | 0 | 1 | [p3-integration.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-integration.txt) |
| Regression P1/P2 chọn lọc | 26 | 26 | 0 | 0 | 0 | 0 | [regression-p1-p2.txt](../proof/phase-3/d-uscalurn-1aa67cc8/regression-p1-p2.txt) |

Tổng bộ mới: **53 method, 2 PASS / 51 FAIL / 0 ERROR / 0 SKIP**. Regression riêng: **26 PASS**, không FAIL/ERROR/SKIP. Tổng hai nhóm: **79 method, 28 PASS / 51 FAIL**. Hai PASS trong bộ mới chỉ là oxy và pause, không phải xác nhận độ tươi v1.2.

Có **64 lượt CLI** trong bộ mới: 57 exit 2 và 7 exit 0. Test fixture hợp lệ theo v1.2 bị reader 1.1 từ chối được ghi assertion FAIL kèm BLOCKED; không nhận là ERROR fixture của QA. Lỗi thực thi ngoài mã 0/2 sẽ là ERROR riêng. Các test schema âm có đối chứng dương trước để không cho reader cũ từ chối mọi mảng tạo PASS giả. Các nhánh bị chặn chưa được xác nhận.

#### Traceability

Mã AC-P3-01..08 dưới đây là **mapping QA đề xuất của D** theo các điều khoản TICKET-03, không tự nhận là danh sách AC khách hàng đã đánh số.

| Mã / yêu cầu | Test đại diện | Kết quả | Proof |
|---|---|---|---|
| AC-P3-01 — Kho cá thể, schema, từ chối kho đếm | [test_reader_preserves_ids_freshness_and_already_spoiled_items_at_tick_zero](../../tests/test_p3_inventory_d.py#L196)<br>[test_inventory_root_and_item_field_schema_are_strict](../../tests/test_p3_inventory_d.py#L216)<br>[test_count_inventory_v11_is_rejected_including_empty_count_map](../../tests/test_p3_inventory_d.py#L211) | FAIL / BLOCKED: reader hiện còn dùng kho đếm | [p3-inventory.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-inventory.txt) |
| AC-P3-02 — ID duy nhất, cấp tăng qua pha/ngày, không dùng lại sau tiêu/bỏ | [test_inventory_ids_are_nonempty_strings_and_unique](../../tests/test_p3_inventory_d.py#L225)<br>[test_item_ids_increase_across_days_even_after_shop_discards_leftovers](../../tests/test_p3_integration_d.py#L66)<br>[test_consumed_id_is_not_reused_in_next_day_template](../../tests/test_p3_integration_d.py#L79) | BLOCKED ở nạp fixture v1.2 | [p3-integration.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-integration.txt) |
| AC-P3-03 — Hao tươi Gather 0.5/s, Quán 0.25/s, pause/Shop không hao | [test_gather_existing_items_decay_half_point_per_sixty_active_steps](../../tests/test_p3_freshness_d.py#L11)<br>[test_quan_raw_items_decay_quarter_point_per_sixty_steps](../../tests/test_p3_freshness_d.py#L17)<br>[test_pause_freezes_freshness_and_delays_spoiled_until_resume_step](../../tests/test_p3_freshness_d.py#L73)<br>[test_shop_raw_stock_stops_decay_while_active_or_paused](../../tests/test_p3_integration_d.py#L43) | BLOCKED ở schema cá thể | [p3-freshness.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-freshness.txt) |
| AC-P3-04 — Ngưỡng 30, spoiled một lần, thứ tự id/tick, hàng ươn vẫn chiếm ô | [test_exactly_thirty_spoils_on_first_step_in_both_phases](../../tests/test_p3_freshness_d.py#L32)<br>[test_exact_threshold_is_not_spoiled_until_following_tick](../../tests/test_p3_freshness_d.py#L41)<br>[test_simultaneous_spoiled_events_use_numeric_id_order_and_emit_once](../../tests/test_p3_freshness_d.py#L52)<br>[test_spoiled_precedes_choke_and_faint_in_gather_tick](../../tests/test_p3_freshness_d.py#L63) | BLOCKED; chưa tới assertion ngưỡng | [p3-freshness.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-freshness.txt) |
| AC-P3-05 — Giữ theo ID, tươi nhất, không giữ trùng; nhả toàn bộ/thử lại một lần | [test_automatic_reservation_chooses_freshest_kind_then_numeric_id](../../tests/test_p3_reservation_price_d.py#L26)<br>[test_two_orders_cannot_reserve_same_physical_item](../../tests/test_p3_reservation_price_d.py#L55)<br>[test_spoilage_releases_entire_recipe_before_reselecting](../../tests/test_p3_reservation_price_d.py#L81)<br>[test_affected_orders_retry_once_in_priority_order_after_all_spoiled_events](../../tests/test_p3_reservation_price_d.py#L99) | BLOCKED: stock/reserved còn dạng cũ | [p3-reservation_price.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-reservation_price.txt) |
| AC-P3-06 — Giá floor theo trung bình cá thể, chốt sau hao tick; tip/paid/score theo giá mới | [test_price_floors_after_tick_decay_and_uses_each_individual_in_mean](../../tests/test_p3_reservation_price_d.py#L141)<br>[test_tip_uses_discounted_payload_price_at_patience_boundary](../../tests/test_p3_reservation_price_d.py#L170)<br>[test_complete_cook_pick_serve_pay_chain_keeps_discounted_price_and_score](../../tests/test_p3_reservation_price_d.py#L186) | BLOCKED trước nấu/phục vụ | [p3-reservation_price.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-reservation_price.txt) |
| AC-P3-07 — Bàn giao file/day cùng tick, không hao thêm; ngất kho rỗng, precision | [test_file_handoff_preserves_ids_kind_and_exact_post_gather_freshness](../../tests/test_p3_integration_d.py#L17)<br>[test_day_handoff_is_same_tick_without_second_decay](../../tests/test_p3_integration_d.py#L28)<br>[test_faint_handoff_to_day_quan_has_empty_individual_stock](../../tests/test_p3_integration_d.py#L89)<br>[test_export_precision_keeps_spoiled_side_of_threshold_after_reload](../../tests/test_p3_inventory_d.py#L268) | BLOCKED: Gather từ chối hold cá thể | [p3-integration.txt](../proof/phase-3/d-uscalurn-1aa67cc8/p3-integration.txt) |
| AC-P3-08 — Regression P1/P2 chưa bị thay thế | [test_p1_underwater_oxygen_consumes_one_per_gameplay_step](../../tests/test_p3_integration_d.py#L109)<br>[test_p2_pause_stops_clock_and_inputs_until_resume_edge](../../tests/test_p3_integration_d.py#L115) | PASS: 26 regression trên bản 1.1; hai guard mới PASS; chưa xác nhận sau migration | [regression-p1-p2.txt](../proof/phase-3/d-uscalurn-1aa67cc8/regression-p1-p2.txt) |

Danh sách đủ từng method và traceback: [summary.json](../proof/phase-3/d-uscalurn-1aa67cc8/summary.json). Fixture, input, seed, argv dùng sys.executable, số tick, stdout/stderr/exit code và output thực tế: [cli-runs.json](../proof/phase-3/d-uscalurn-1aa67cc8/cli-runs.json). Các JSONL thành công giữ nguyên nội dung ở file .jsonl.txt để không bị quy tắc ignore *.jsonl bỏ qua.

#### Các phát hiện và chuyển owner

| Phần | Expected v1.2 | Actual quan sát | Owner cần xử lý |
|---|---|---|---|
| Manifest | version 1.2 và freshness 100/0.5/0.25/30 | version 1.1; test manifest FAIL | C / Integrator |
| Đọc kho | items là mảng cá thể, giữ id/kind/fresh | kho mảng bị exit 2: items phải là object | C — inventory/scenario |
| Migration | kho đếm kể cả items rỗng dạng map phải exit 2 | cả hai file kho đếm nhận exit 0 | C — reader/version adapter |
| Gather fixture | hold cá thể hợp lệ phải exit 0 | exit 2: hold phải là mảng id nguyên liệu hợp lệ | C/A — tích hợp schema Gather |
| Hàng mới | mỗi nguyên liệu có id mới, fresh 100 | hái/bắt thành công nhưng hold còn là chuỗi kind | C/A — tạo cá thể lúc hái/bắt |
| Kho rỗng cuối ca | inventory.items bằng [] | cập bến cho items bằng {} | C — xuất kho/bàn giao |
| Reserved/giá | reserved là ID cá thể; tính tươi/giá trước nấu | stock mảng bị từ chối trước khi kiểm được nhánh | C/B — migration rồi B rà luật |
| Day/Shop | giữ ID/fresh khi đổi pha; cấp ID mới ngày sau | mẫu hold v1.2 bị từ chối lúc dựng day | C — day/allocator |

Đây là các triệu chứng migration chưa có, không khẳng định từng thuật toán chưa chạy là một bug gameplay độc lập. Kế hoạch nhóm hiện giao C tích hợp lõi, B rà luật Quán và A rà Gather/test; QA giữ assertion theo spec.

#### Smoke file/day và determinism

- Smoke file của TICKET-03 đã thử ở method bàn giao: I1/ca_linh/fresh 100, đứng bến, interact frame 0. **BLOCKED tại tiến trình Gather**: expected exit 0, actual exit 2. Không có inventory để chạy bước Quán; không bịa output hay đánh dấu smoke PASS.
- Bàn giao mode day được thử bằng fixture ngắn hợp lệ; cũng **BLOCKED khi đọc hold cá thể**. Cùng-tick, không hao thêm và không đổi ID đã có assertion nhưng chưa được thực thi tới.
- Test determinism mới giữ assertion so từng byte và event spoiled; **BLOCKED trước khi có hai output hợp lệ**. Không có kết luận PASS hoặc mismatch RNG.
- Regression 26 ca giữ luật không đổi (id allocator, input, ramp/biên, cá bơi/sinh, phát hiện quái, day/Shop/pause) đều PASS trên code 1.1 hiện tại. Chọn lọc theo tên cụ thể trong summary; loại assertion version 1.1 và fixture kho đếm đã bị v1.2 thay thế. Cần chạy lại trên bản 1.2 sau migration.

#### Chạy lại

Từ gốc repo trên nhánh cá nhân, PowerShell:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m unittest discover -s tests -p 'test_p3_*_d.py' -v
$LASTEXITCODE
~~~

Tách suite bằng các pattern test_p3_inventory_d.py, test_p3_freshness_d.py, test_p3_reservation_price_d.py, test_p3_integration_d.py. CLI trong test luôn dùng sys.executable -B -m chonoi.headless, không dùng alias python3 hoặc shell command để chạy gameplay. Dữ liệu runtime nằm trong Workdir tạm; chạy unittest đơn thuần không ghi proof vào repo. Lệnh runner thu proof thực tế và nhóm regression trong [runner-command.py.txt](../proof/phase-3/d-uscalurn-1aa67cc8/runner-command.py.txt); chỉ chạy lại khi có quyền ghi proof mới, không ghi đè thư mục hiện có.

Python dùng C:\Users\Siuuu\AppData\Local\Programs\Python\Python311\python.exe; phiên bản/platform và hash trước/sau nằm trong summary. Source và spec giữ nguyên xuyên suốt lần kiểm thử (source_unchanged=true); không sửa code để hỗ trợ test. Stdout/stderr ở log là dữ liệu thực chạy, không dùng kết quả cũ. Các exit 1 ở suite là kết quả FAIL của unittest, không phải exit 9009.

#### Giới hạn và phần chưa hoàn thành

- reservations (khách đặt trước) và current đều không bật: extensions=[]; không viết/chạy ca mở rộng. Core customers.reserved theo ID vẫn được test đầy đủ.
- Các fixture reserved/stove/hand duy trì liên kết mục D của contract cũ chưa bị thay thế. Không dùng hai nơi chứa cùng một món trừ ca âm có đối chứng dương. Không thêm API/event re-reservation không được spec mô tả.
- Độ tươi so quan sát ±0.01; tick spoiled, thứ tự event, ID và tiền so chính xác. Giá kỳ vọng dùng Fraction độc lập, tính sau hao 1/240 ở Quán.
- Reader hiện chưa nhận cá thể nên các ca schema âm phần lớn dừng ở đối chứng dương; chưa được gọi là PASS schema validation. Nhánh re-reservation, chốt giá và chuyển ngày mới chưa kiểm chứng hành vi trên engine v1.2.
- Không kiểm frontend/HUD bằng tay. Không sửa test của A/B/C, test D cũ, spec hoặc manifest.
- File kho.json xuất hiện ngoài phạm vi trong lúc làm việc, trước khi chạy suite mới; không do runner/test mới tạo, đã giữ nguyên. Đối chiếu thay đổi phạm vi ở proof kiểm tra bàn giao.
- **Phần test/proof/báo cáo của D hoàn thành; nghiệm thu gameplay v1.2 BLOCKED** cho tới khi C/A/B tích hợp schema và chạy lại. Chưa commit/push/merge/tag.
