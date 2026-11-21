# Ma trận truy vết Phase 1

> D / uscalurn — nhóm T77, **Phase 1 / Test Contract v1.0**.
> Revision nền: 6a7f66a35e5816996fe51010ea5b20ac9098fe5c. Kết quả trên working tree gồm hai file test chưa được Git theo dõi, chưa phải nghiệm thu của commit/tag phát hành.
> Hash source, contract và từng file test: [summary.json](../proof/phase-1/d-uscalurn-run-81321f1b/summary.json). Hash source của hai đợt proof trùng nhau và giữ nguyên trong lúc chạy.

Mã AC-P1-01–20 lấy từ [phân công nội bộ nhóm](../plan/phase-1-chia-viec.md), đối chiếu [PRD-0 C–G](../prd/PRD-0.md). Đây là mã nhóm, không tự nhận là mã khách hàng đã phê duyệt.

## Kết quả chạy mới

| Suite | Methods | PASS | FAIL | ERROR | SKIP | Exit code | Proof |
|---|---:|---:|---:|---:|---:|---:|---|
| Gather | 28 | 5 | 23 | 0 | 0 | 1 | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) |
| Quán | 39 | 11 | 28 | 0 | 0 | 1 | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) |
| Toàn bộ unittest | 99 | 48 | 51 | 0 | 0 | 1 | [full-suite.txt](../proof/phase-1/d-uscalurn-run-81321f1b/full-suite.txt) |

Các suite chạy mới trên Python 3.11.9 / Windows, PYTHONDONTWRITEBYTECODE=1, tiến trình Python dùng -B. Log giữ stdout và stderr ở hai phần riêng, kèm argv/exit code. Unittest in verbose/traceback vào stderr là bình thường.

Có **51 method FAIL**, tương ứng **68 failure entries** khi tính cả subtest (Gather 25, Quán 43); không báo 68 method FAIL. Toàn bộ 32 test starter PASS. Sáu regression validator scenario của D PASS, kiểm công việc validator do C triển khai.

**0 ERROR không có nghĩa gameplay đạt.** Các FAIL sau CLI exit 0 là kết quả không khớp luật; fixture bị từ chối trong test gameplay sẽ là ERROR. Các ca cố ý mâu thuẫn thuộc nhóm scenario riêng, expected exit 2 và không tạo JSONL.

## AC → test → kết quả → bằng chứng

| AC | Cách kiểm chứng / test | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 — Oxy -1/tick, refill/clamp | [test_oxygen_decreases_one_per_underwater_step_including_sixty_steps](../../tests/test_gather_rules.py#L113)<br>[test_surface_refill_uses_tuning_and_clamps_at_maximum](../../tests/test_gather_rules.py#L121) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-02 — dive/surface theo ranh giới | [test_dive_and_surface_only_when_movement_crosses_boundary](../../tests/test_gather_rules.py#L208) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-03 — oxygen_empty và choke đúng tick | [test_oxygen_empty_occurs_only_on_positive_to_zero_transition](../../tests/test_gather_rules.py#L133)<br>[test_zero_oxygen_counts_empty_step_and_chokes_at_exact_intervals](../../tests/test_gather_rules.py#L140) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-04 — Nổi lên ở deadline không ngạt | [test_surfacing_on_choke_deadline_refills_and_resets_counter](../../tests/test_gather_rules.py#L173) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-05 — Faint, LIFO, inventory rỗng | [test_faint_discards_hold_lifo_and_precedes_actions_and_time_end](../../tests/test_gather_rules.py#L187) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-06 — Hái nút ready tại mép bán kính | [test_gather_requires_surface_ready_node_and_inclusive_radius](../../tests/test_gather_rules.py#L229) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-07 — Giỏ đầy, giữ nguyên nút | [test_full_hold_emits_hold_full_without_changing_ready_node](../../tests/test_gather_rules.py#L267) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-08 — Mọc lại sau 1200 tick | [test_node_regrows_exactly_after_configured_delay_and_can_be_picked_that_tick](../../tests/test_gather_rules.py#L277)<br>[test_fixture_regrowth_counts_down_once_and_emits_ready_events_in_id_order](../../tests/test_gather_rules.py#L294) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | PARTIAL: countdown fixture PASS; chuỗi hái/mọc lại FAIL |
| AC-P1-09 — Bắt cá linh nguyên yield, cooldown | [test_catch_accepts_whole_yield_when_free_space_is_exact](../../tests/test_gather_rules.py#L351)<br>[test_catch_cooldown_can_be_reused_at_exact_deadline](../../tests/test_gather_rules.py#L371) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-10 — Thiếu chỗ: giữ đàn, không cooldown | [test_insufficient_space_keeps_whole_fish_and_does_not_try_smaller_school](../../tests/test_gather_rules.py#L337) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | FAIL |
| AC-P1-11 — Không bắt trên mặt nước/ngoài tầm | [test_catch_without_a_school_does_not_set_cooldown](../../tests/test_gather_rules.py#L396)<br>[test_catch_requires_underwater_inclusive_radius_and_expired_cooldown](../../tests/test_gather_rules.py#L312) | [gather-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/gather-tests.txt) | PARTIAL: không có đàn PASS; method điều kiện tổng hợp FAIL |
| AC-P1-12 — Gather → file kho → Quán tick 0 | [test_inv_01_gather_writes_inventory_quan_reads_it](../../tests/test_smoke_p1.py#L201) | [integration.md](../proof/phase-1/d-uscalurn-run-81321f1b/integration.md) | PASS: smoke mới và starter |
| AC-P1-13 — Khách tick 120, chu kỳ 900, giữ chỗ | [test_first_customer_arrives_at_configured_tick_with_full_patience](../../tests/test_quan_rules.py#L187)<br>[test_customer_attempts_follow_exact_interval_even_in_shortened_shift](../../tests/test_quan_rules.py#L203)<br>[test_order_reserves_at_arrival_and_consumes_only_when_cooking_starts](../../tests/test_quan_rules.py#L247) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-14 — no_dish khi không đủ món | [test_no_dish_when_each_recipe_lacks_at_least_one_ingredient](../../tests/test_quan_rules.py#L212) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-15 — Kiên nhẫn, trả giữ chỗ, reputation | [test_patience_decreases_once_on_each_waiting_tick](../../tests/test_quan_rules.py#L356)<br>[test_patience_expiry_releases_reservation_and_applies_clamped_reputation](../../tests/test_quan_rules.py#L363) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-16 — Nấu → chín → bưng → phục vụ → trả tiền | [test_stove_idle_cooking_ready_transitions_and_countdowns_are_exact](../../tests/test_quan_rules.py#L421)<br>[test_pickup_requires_ready_and_empty_hand_then_resets_stove](../../tests/test_quan_rules.py#L460)<br>[test_matching_order_is_served_then_paid_only_after_full_eating_duration](../../tests/test_quan_rules.py#L523) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-17 — Tip và reputation đúng ngưỡng | [test_tip_threshold_uses_patience_after_decrement_and_floor_price](../../tests/test_quan_rules.py#L551)<br>[test_payment_tip_reputation_is_clamped_and_no_tip_leaves_reputation_unchanged](../../tests/test_quan_rules.py#L575) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-18 — Đóng ca: paid/left rồi quan_end | [test_closing_waiter_releases_raw_reservation_without_patience_penalty](../../tests/test_quan_rules.py#L589)<br>[test_closing_pays_eaters_and_preserves_finished_eating_reason_on_exact_deadline](../../tests/test_quan_rules.py#L618)<br>[test_service_on_closing_tick_is_paid_immediately_before_quan_end](../../tests/test_quan_rules.py#L637) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | FAIL |
| AC-P1-19 — JSONL và inventory giống từng byte | [test_con_02_deterministic_bytes](../../tests/test_smoke_p1.py#L48)<br>[test_fixture_actions_produce_identical_jsonl_and_inventory_bytes](../../tests/test_gather_rules.py#L454)<br>[test_seeded_order_and_cooking_fixture_produce_identical_jsonl_bytes](../../tests/test_quan_rules.py#L676) | [determinism.md](../proof/phase-1/d-uscalurn-determinism-df2e0816/determinism.md) | PASS trong 3 fixture trực tiếp; guard gameplay của D còn FAIL |
| AC-P1-20 — Scenario mâu thuẫn bị từ chối trước output | [test_scenario_rejects_reservation_beyond_physical_stock_before_output](../../tests/test_quan_rules.py#L292)<br>[test_scenario_rejects_assigned_order_with_missing_or_duplicate_payload](../../tests/test_quan_rules.py#L309)<br>[test_scenario_rejects_eating_without_payment_fields_or_positive_timer](../../tests/test_quan_rules.py#L324) | [quan-tests.txt](../proof/phase-1/d-uscalurn-run-81321f1b/quan-tests.txt) | PASS: cả 6 regression scenario của D |

## Smoke tích hợp và determinism

- Smoke PRD-0 G: **PASS**. Hai tiến trình riêng, seed 42; Gather ticks 1 cập bến với giỏ ["ca_loc","bong_sung","bong_sung"]; Quán ticks 0 đọc stock {"bong_sung":2,"ca_loc":1}. Hai exit code 0, stderr rỗng. [integration.md](../proof/phase-1/d-uscalurn-run-81321f1b/integration.md) có fixture/input, argv, expected/actual. Raw proof: [integration-gather.jsonl](../proof/phase-1/d-uscalurn-run-81321f1b/integration-gather.jsonl.txt), [integration-inventory.json](../proof/phase-1/d-uscalurn-run-81321f1b/integration-inventory.json), [integration-quan.jsonl](../proof/phase-1/d-uscalurn-run-81321f1b/integration-quan.jsonl.txt).
- Determinism trực tiếp: **PASS**, ba cặp chạy độc lập: Gather docked; Gather hết giờ có di chuyển/countdown nút; Quán có stock/input và random_customers bật. JSONL giống từng byte; cả hai ca Gather có inventory giống từng byte. [determinism.md](../proof/phase-1/d-uscalurn-determinism-df2e0816/determinism.md); hash/lệnh/input/path ở [summary.json](../proof/phase-1/d-uscalurn-determinism-df2e0816/summary.json).
- Hai method determinism của D vẫn FAIL tại guard đòi sự kiện hái/khách/nấu trước khi so byte. Đây là thiếu gameplay, chưa phải mismatch RNG. Proof trực tiếp chỉ xác nhận lặp lại của các nhánh thực sự đã chạy.

## Chạy lại

Từ gốc repo, PowerShell:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m unittest discover -s tests -p 'test_gather_rules.py' -v
$LASTEXITCODE
python -B -m unittest discover -s tests -p 'test_quan_rules.py' -v
$LASTEXITCODE
python -B -m unittest discover -s tests -v
$LASTEXITCODE
~~~

Manifest khai python3 -m chonoi.headless, nhưng alias Windows không khởi chạy được (lỗi lưu trong summary). Hai test của D có fallback cục bộ; starter không có. **Full-suite proof dùng adapter trong bộ nhớ** thay riêng executable thành Python đang chạy, không sửa manifest, PATH hoặc starter. Để tái lập đúng proof trên máy này, chạy ví dụ đã xác minh trong [run-tests-proof](../../.agents/skills/run-tests-proof/SKILL.md); ví dụ lưu log mới và thoát 1 khi suite FAIL. Có thể trích Python từ skill mà không tạo script:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$qaSkillText = Get-Content -Encoding UTF8 -Raw '.agents/skills/run-tests-proof/SKILL.md'
$qaPython = [regex]::Match($qaSkillText, "(?ms)^@'\r?\n(.*?)\r?\n'@ \| python -B -").Groups[1].Value
$qaPython | python -B -
$LASTEXITCODE
~~~

Chỉ thu proof khi quyền ghi hiện tại cho phép. Linux/macOS dùng PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest ...; cách chạy khối proof Python có trong skill. So byte bằng [check-determinism](../../.agents/skills/check-determinism/SKILL.md). Không ghi đè proof cũ.

## Phân loại lỗi và giới hạn

Danh sách đầy đủ 51 method FAIL và ví dụ fixture/seed/tick/expected/actual: [qa-triage.md](../proof/phase-1/d-uscalurn-run-81321f1b/qa-triage.md); traceback gốc trong log từng suite.

- **A — Gather:** oxy/refill, dive/surface, oxygen_empty/choke/faint; hái/bắt và yield/cooldown/cạnh lên còn thiếu. Countdown nút từ fixture PASS; chuỗi hái → 1200 tick → mọc lại chưa đạt.
- **B — Quán:** lịch khách/no_dish/giữ chỗ lúc tạo đơn; patience/timer bếp; bưng/phục vụ/ăn/trả tiền, tip/reputation/score và dọn ca. Fixture tối giản thiếu default trong snapshot; player thiếu vel.
- **C — scenario/tích hợp:** 6 regression và smoke PASS; chưa thấy mismatch schema mới qua các ca đã chạy. C cần phối hợp B về default/snapshot. TEAM.md còn placeholder A/B/D, metadata DoD cần nhóm hoàn thiện ngoài phạm vi D lần này. Validator của C không phải code do D viết.
- Fixture Quán tuân thủ liên kết khách/bàn/bếp/tay/reserved mục D. Với một bàn/một đơn, không dựng hai đơn cùng sống để thử giao nhầm hoặc tay đầy đồng thời bếp ready; fixture như vậy mâu thuẫn contract. Chỉ kiểm trạng thái hợp lệ tạo được ở Phase 1.
- PASS guard âm hoặc phép lặp lại không chứng minh nhánh dương chưa thực hiện. Chưa kiểm HUD/FPS thủ công, số commit cá nhân hay tag phát hành. Nhiệm vụ proof này giữ source/test/manifest chỉ đọc.

## Đánh giá ngắn

- AC-P1-12, 19, 20 đạt trong phạm vi fixture ghi trên; AC-P1-08 và 11 chỉ đạt một phần; 15 AC còn lại FAIL.
- **Nghiệm thu gameplay Phase 1: FAIL; phát hành BLOCKED bởi các lỗi A/B.** Không đánh dấu PASS vì smoke/determinism PASS hoặc vì không có ERROR.
- Phần QA/Harness của D có hai skill, log mới, matrix, triage, usage log và reflection. Chưa tạo commit/tag; test D vẫn chưa được Git theo dõi. Sau khi A/B sửa luật cần chạy lại, thêm proof mới trước khi nghiệm thu.


JSONL proof is retained byte-for-byte as .jsonl.txt because *.jsonl is ignored by this repository. [Artifact manifest](../proof/phase-1/d-uscalurn-run-81321f1b/artifact-manifest.json) maps original runtime proof paths to Git-visible copies and SHA-256. Original log/summary records remain unchanged.
