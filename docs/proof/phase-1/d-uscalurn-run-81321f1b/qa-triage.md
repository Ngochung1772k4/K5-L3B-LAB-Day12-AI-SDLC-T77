# QA triage Phase 1 — D / uscalurn

Revision nền: 6a7f66a35e5816996fe51010ea5b20ac9098fe5c, working tree có hai file test chưa commit; hash ở [summary.json](summary.json). Các mục lấy từ log mới, không dùng báo cáo cũ. Headless exit 0 trong fixture gameplay; FAIL do assertion. Ca cố ý mâu thuẫn scenario tách riêng.

## Ví dụ tái lập

Helper Gather mặc định nodes:[], fish:[], random_fish:false, player [50,0]; Quán mặc định stock:{}, customers:[], random_customers:false. Seed mặc định **17**. Input frame k tạo event k+1. Mở method để xem đủ block/frame; stdout/stderr gốc nằm ở log tương ứng.

| Owner | Method / fixture quan trọng | Tick | Expected | Actual |
|---|---|---:|---|---|
| A | test_oxygen_decreases_one_per_underwater_step_including_sixty_steps; pos [50,1.5], oxy đầy | 1 / 60 | 1799 / 1740 | Assertion đầu: 1800 thay vì 1799 |
| A | test_surface_refill_uses_tuning_and_clamps_at_maximum; d=0.5, oxy 1787 | 1 | 1793 | 1787 |
| A | test_zero_oxygen_counts_empty_step_and_chokes_at_exact_intervals; d=1.5, oxy=1 | 1 / 60 | oxygen_empty tại 1, choke tại 60 | oxygen_empty: [], chưa tới assertion choke |
| A | test_faint_discards_hold_lifo_and_precedes_actions_and_time_end; hp=1, oxy=0, zero=59, giỏ 3, nút bật, ca còn 1 | 1 | choke → faint → gather_end(fainted), kho rỗng | Chỉ gather_end do cập bến |
| A | test_full_hold_emits_hold_full_without_changing_ready_node; hold 12 ca_loc, N1 ngay player, interact frame 0 | 1 | hold_full action gather | hold_full: [] |
| A | test_catch_accepts_whole_yield_when_free_space_is_exact; d=1.5, hold 9 bong_sung, F1 ca_linh cùng pos, catch frame 0 | 1 | fish_caught yield 3, hold 12 | fish_caught: [] |
| B | test_first_customer_arrives_at_configured_tick_with_full_patience; random=true, stock ca_loc=1 | 120 | customer_arrived C1/T1 | customer_arrived: [] |
| B | test_patience_decreases_once_on_each_waiting_tick; khách waiting P=5, reserved đúng recipe | 1 | patience=4 | 5 |
| B | test_pickup_requires_ready_and_empty_hand_then_resets_stove; assigned C1, cooking timer=2, payload khớp | 1 | cook_ticks_left=1 | 2 |
| B | test_matching_order_is_served_then_paid_only_after_full_eating_duration; assigned C1 trên tay, đứng T1, interact frame 0 | 1 | served, chuyển eating | served: [] |
| B | test_score_uses_earned_plus_multiplier_times_floor_reputation; eating C1, eat=1, giá 60, tip 12, rep 3.9 | 1 | earned 72, rep 4.1, score 472 | earned=0; chưa kết luận riêng công thức score sai |
| B | test_closing_pays_eaters_and_preserves_finished_eating_reason_on_exact_deadline; eat=1 hoặc 2, ca còn 1 | 1 | paid rồi quan_end | Chỉ quan_end |
| B/C | test_minimal_customer_fixture_receives_contract_defaults_at_tick_zero; id/table_id/dish_id, stock đủ | 0 | state waiting, order_tick 0, patience đầy, status reserved | Chỉ id/table_id/dish_id/reserved, thiếu state |
| B/C | test_snapshot_preserves_fixture_player_position_and_velocity; pos [8,5], vel [2,0] | 0 | player.vel [2,0] | Player chỉ có pos |

B/C là phối hợp contract/snapshot; nơi xuất dữ liệu thiếu là QuanSim của B. Không coi đây là validator C từ chối sai fixture. Sáu regression validator PASS, đúng exit 2 và trước khi tạo output; smoke chuyển kho PASS.

## Từng method FAIL

Một method có nhiều subtest lỗi chỉ xuất hiện một lần. Các subcase stock/seed khác (7/42), remaining/initial/location giữ nguyên trong traceback; không quy chúng về seed 17.

| Owner | Test method | Log |
|---|---|---|
| A | [test_catch_accepts_whole_yield_when_free_space_is_exact](../../../../tests/test_gather_rules.py#L351) | [gather-tests.txt](gather-tests.txt) |
| A | [test_catch_cooldown_can_be_reused_at_exact_deadline](../../../../tests/test_gather_rules.py#L371) | [gather-tests.txt](gather-tests.txt) |
| A | [test_catch_requires_underwater_inclusive_radius_and_expired_cooldown](../../../../tests/test_gather_rules.py#L312) | [gather-tests.txt](gather-tests.txt) |
| A | [test_catch_selects_nearest_school_then_numeric_id](../../../../tests/test_gather_rules.py#L362) | [gather-tests.txt](gather-tests.txt) |
| A | [test_dive_and_surface_only_when_movement_crosses_boundary](../../../../tests/test_gather_rules.py#L208) | [gather-tests.txt](gather-tests.txt) |
| A | [test_faint_discards_hold_lifo_and_precedes_actions_and_time_end](../../../../tests/test_gather_rules.py#L187) | [gather-tests.txt](gather-tests.txt) |
| A | [test_fixture_actions_produce_identical_jsonl_and_inventory_bytes](../../../../tests/test_gather_rules.py#L454) | [gather-tests.txt](gather-tests.txt) |
| A | [test_fixture_zero_oxygen_counter_continues_without_duplicate_empty_event](../../../../tests/test_gather_rules.py#L153) | [gather-tests.txt](gather-tests.txt) |
| A | [test_full_hold_emits_hold_full_without_changing_ready_node](../../../../tests/test_gather_rules.py#L267) | [gather-tests.txt](gather-tests.txt) |
| A | [test_gather_requires_surface_ready_node_and_inclusive_radius](../../../../tests/test_gather_rules.py#L229) | [gather-tests.txt](gather-tests.txt) |
| A | [test_gather_selects_nearest_ready_node_then_numeric_id](../../../../tests/test_gather_rules.py#L248) | [gather-tests.txt](gather-tests.txt) |
| A | [test_held_catch_does_not_repeat_after_cooldown_expires](../../../../tests/test_gather_rules.py#L384) | [gather-tests.txt](gather-tests.txt) |
| A | [test_held_interact_does_not_pick_second_node_until_new_rising_edge](../../../../tests/test_gather_rules.py#L303) | [gather-tests.txt](gather-tests.txt) |
| A | [test_insufficient_space_keeps_whole_fish_and_does_not_try_smaller_school](../../../../tests/test_gather_rules.py#L337) | [gather-tests.txt](gather-tests.txt) |
| A | [test_node_regrows_exactly_after_configured_delay_and_can_be_picked_that_tick](../../../../tests/test_gather_rules.py#L277) | [gather-tests.txt](gather-tests.txt) |
| A | [test_nonfatal_choke_preserves_every_item_in_hold](../../../../tests/test_gather_rules.py#L162) | [gather-tests.txt](gather-tests.txt) |
| A | [test_oxygen_decreases_one_per_underwater_step_including_sixty_steps](../../../../tests/test_gather_rules.py#L113) | [gather-tests.txt](gather-tests.txt) |
| A | [test_oxygen_empty_occurs_only_on_positive_to_zero_transition](../../../../tests/test_gather_rules.py#L133) | [gather-tests.txt](gather-tests.txt) |
| A | [test_surface_refill_uses_tuning_and_clamps_at_maximum](../../../../tests/test_gather_rules.py#L121) | [gather-tests.txt](gather-tests.txt) |
| A | [test_surfacing_on_choke_deadline_refills_and_resets_counter](../../../../tests/test_gather_rules.py#L173) | [gather-tests.txt](gather-tests.txt) |
| A | [test_underwater_docking_precedes_catch_and_uses_two_dimensional_radius](../../../../tests/test_gather_rules.py#L417) | [gather-tests.txt](gather-tests.txt) |
| A | [test_valid_gather_or_catch_on_last_tick_is_included_in_inventory](../../../../tests/test_gather_rules.py#L434) | [gather-tests.txt](gather-tests.txt) |
| A | [test_zero_oxygen_counts_empty_step_and_chokes_at_exact_intervals](../../../../tests/test_gather_rules.py#L140) | [gather-tests.txt](gather-tests.txt) |
| B | [test_closing_discards_assigned_dishes_in_stove_or_hand_without_refunding](../../../../tests/test_quan_rules.py#L604) | [quan-tests.txt](quan-tests.txt) |
| B | [test_closing_pays_eaters_and_preserves_finished_eating_reason_on_exact_deadline](../../../../tests/test_quan_rules.py#L618) | [quan-tests.txt](quan-tests.txt) |
| B | [test_closing_waiter_releases_raw_reservation_without_patience_penalty](../../../../tests/test_quan_rules.py#L589) | [quan-tests.txt](quan-tests.txt) |
| B | [test_customer_attempts_follow_exact_interval_even_in_shortened_shift](../../../../tests/test_quan_rules.py#L203) | [quan-tests.txt](quan-tests.txt) |
| B | [test_customer_selects_only_recipes_affordable_from_available_stock](../../../../tests/test_quan_rules.py#L224) | [quan-tests.txt](quan-tests.txt) |
| B | [test_expired_assigned_order_discards_cooking_ready_or_carried_dish_without_refund](../../../../tests/test_quan_rules.py#L398) | [quan-tests.txt](quan-tests.txt) |
| B | [test_first_customer_arrives_at_configured_tick_with_full_patience](../../../../tests/test_quan_rules.py#L187) | [quan-tests.txt](quan-tests.txt) |
| B | [test_held_interact_does_not_pick_ready_dish_without_a_new_edge](../../../../tests/test_quan_rules.py#L445) | [quan-tests.txt](quan-tests.txt) |
| B | [test_interaction_radius_is_inclusive_and_rejects_just_outside](../../../../tests/test_quan_rules.py#L512) | [quan-tests.txt](quan-tests.txt) |
| B | [test_matching_order_is_served_then_paid_only_after_full_eating_duration](../../../../tests/test_quan_rules.py#L523) | [quan-tests.txt](quan-tests.txt) |
| B | [test_minimal_customer_fixture_receives_contract_defaults_at_tick_zero](../../../../tests/test_quan_rules.py#L274) | [quan-tests.txt](quan-tests.txt) |
| B | [test_no_dish_when_each_recipe_lacks_at_least_one_ingredient](../../../../tests/test_quan_rules.py#L212) | [quan-tests.txt](quan-tests.txt) |
| B | [test_one_interact_picks_at_stove_before_colocated_table_without_serving](../../../../tests/test_quan_rules.py#L493) | [quan-tests.txt](quan-tests.txt) |
| B | [test_order_reserves_at_arrival_and_consumes_only_when_cooking_starts](../../../../tests/test_quan_rules.py#L247) | [quan-tests.txt](quan-tests.txt) |
| B | [test_patience_decreases_once_on_each_waiting_tick](../../../../tests/test_quan_rules.py#L356) | [quan-tests.txt](quan-tests.txt) |
| B | [test_patience_expiry_releases_reservation_and_applies_clamped_reputation](../../../../tests/test_quan_rules.py#L363) | [quan-tests.txt](quan-tests.txt) |
| B | [test_payment_tip_reputation_is_clamped_and_no_tip_leaves_reputation_unchanged](../../../../tests/test_quan_rules.py#L575) | [quan-tests.txt](quan-tests.txt) |
| B | [test_pickup_requires_ready_and_empty_hand_then_resets_stove](../../../../tests/test_quan_rules.py#L460) | [quan-tests.txt](quan-tests.txt) |
| B | [test_ready_transition_allows_pickup_in_same_tick_before_interaction](../../../../tests/test_quan_rules.py#L476) | [quan-tests.txt](quan-tests.txt) |
| B | [test_released_raw_reservation_is_available_for_next_customer](../../../../tests/test_quan_rules.py#L383) | [quan-tests.txt](quan-tests.txt) |
| B | [test_reservations_never_exceed_physical_stock_and_full_table_skips_arrivals](../../../../tests/test_quan_rules.py#L340) | [quan-tests.txt](quan-tests.txt) |
| B | [test_score_uses_earned_plus_multiplier_times_floor_reputation](../../../../tests/test_quan_rules.py#L662) | [quan-tests.txt](quan-tests.txt) |
| B | [test_seeded_order_and_cooking_fixture_produce_identical_jsonl_bytes](../../../../tests/test_quan_rules.py#L676) | [quan-tests.txt](quan-tests.txt) |
| B | [test_service_on_closing_tick_is_paid_immediately_before_quan_end](../../../../tests/test_quan_rules.py#L637) | [quan-tests.txt](quan-tests.txt) |
| B | [test_service_on_zero_patience_deadline_succeeds_before_departure](../../../../tests/test_quan_rules.py#L565) | [quan-tests.txt](quan-tests.txt) |
| B | [test_snapshot_preserves_fixture_player_position_and_velocity](../../../../tests/test_quan_rules.py#L285) | [quan-tests.txt](quan-tests.txt) |
| B | [test_stove_idle_cooking_ready_transitions_and_countdowns_are_exact](../../../../tests/test_quan_rules.py#L421) | [quan-tests.txt](quan-tests.txt) |
| B | [test_tip_threshold_uses_patience_after_decrement_and_floor_price](../../../../tests/test_quan_rules.py#L551) | [quan-tests.txt](quan-tests.txt) |
