# Phase 3 — từng method FAIL của D

Revision d496a4f313aa4a3757ffacf599499d3f3224d8e5, branch d/phase-3-qa-uscalurn. Contract đang chạy 1.1, yêu cầu 1.2. Danh sách này là kết quả thật từ summary; không suy diễn nhánh bị reader chặn thành kết quả thuật toán.

| Method | Owner phối hợp | Log |
|---|---|---|
| [test_count_inventory_v11_is_rejected_including_empty_count_map](../../../../tests/test_p3_inventory_d.py#L211) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_empty_individual_inventory_is_accepted](../../../../tests/test_p3_inventory_d.py#L202) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_export_precision_keeps_spoiled_side_of_threshold_after_reload](../../../../tests/test_p3_inventory_d.py#L268) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_gather_export_sorts_ids_but_hold_retains_acquisition_order](../../../../tests/test_p3_inventory_d.py#L247) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_inventory_freshness_is_finite_numeric_and_within_bounds](../../../../tests/test_p3_inventory_d.py#L231) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_inventory_ids_are_nonempty_strings_and_unique](../../../../tests/test_p3_inventory_d.py#L225) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_inventory_root_and_item_field_schema_are_strict](../../../../tests/test_p3_inventory_d.py#L216) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_inventory_unknown_kind_is_rejected](../../../../tests/test_p3_inventory_d.py#L237) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_manifest_declares_v12_and_required_freshness_values](../../../../tests/test_p3_inventory_d.py#L184) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_quan_inventory_is_not_limited_by_gather_capacity](../../../../tests/test_p3_inventory_d.py#L206) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_reader_preserves_ids_freshness_and_already_spoiled_items_at_tick_zero](../../../../tests/test_p3_inventory_d.py#L196) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_scenario_rejects_duplicate_physical_ids_in_hold_or_stock](../../../../tests/test_p3_inventory_d.py#L241) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_tick_limit_does_not_create_or_replace_inventory](../../../../tests/test_p3_inventory_d.py#L256) | C | [p3-inventory.txt](p3-inventory.txt) |
| [test_exact_threshold_is_not_spoiled_until_following_tick](../../../../tests/test_p3_freshness_d.py#L41) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_exactly_thirty_spoils_on_first_step_in_both_phases](../../../../tests/test_p3_freshness_d.py#L32) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_freshness_clamps_at_zero_in_both_phases](../../../../tests/test_p3_freshness_d.py#L23) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_gather_existing_items_decay_half_point_per_sixty_active_steps](../../../../tests/test_p3_freshness_d.py#L11) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_monster_hit_and_faint_lost_payloads_are_items_in_lifo_order](../../../../tests/test_p3_freshness_d.py#L115) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_new_fish_yield_gets_distinct_ids_and_no_same_tick_decay](../../../../tests/test_p3_freshness_d.py#L95) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_new_harvest_starts_at_one_hundred_then_decays_from_next_step](../../../../tests/test_p3_freshness_d.py#L86) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_pause_freezes_freshness_and_delays_spoiled_until_resume_step](../../../../tests/test_p3_freshness_d.py#L73) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_quan_raw_items_decay_quarter_point_per_sixty_steps](../../../../tests/test_p3_freshness_d.py#L17) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_simultaneous_spoiled_events_use_numeric_id_order_and_emit_once](../../../../tests/test_p3_freshness_d.py#L52) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_spoiled_items_still_fill_hold_and_block_harvesting](../../../../tests/test_p3_freshness_d.py#L105) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_spoiled_precedes_choke_and_faint_in_gather_tick](../../../../tests/test_p3_freshness_d.py#L63) | C/A | [p3-freshness.txt](p3-freshness.txt) |
| [test_affected_orders_retry_once_in_priority_order_after_all_spoiled_events](../../../../tests/test_p3_reservation_price_d.py#L99) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_all_spoiled_events_precede_replacement_and_cooking_on_same_tick](../../../../tests/test_p3_reservation_price_d.py#L119) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_allocation_priority_is_order_tick_then_table_id_without_overbooking](../../../../tests/test_p3_reservation_price_d.py#L34) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_automatic_reservation_chooses_freshest_kind_then_numeric_id](../../../../tests/test_p3_reservation_price_d.py#L26) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_complete_cook_pick_serve_pay_chain_keeps_discounted_price_and_score](../../../../tests/test_p3_reservation_price_d.py#L186) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_cooking_consumes_reserved_ids_even_if_another_item_is_fresher](../../../../tests/test_p3_reservation_price_d.py#L131) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_failed_replacement_waits_unfulfillable_until_patience_expiry](../../../../tests/test_p3_reservation_price_d.py#L90) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_invalid_reserved_ids_are_rejected_with_valid_fixture_control](../../../../tests/test_p3_reservation_price_d.py#L48) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_price_floors_after_tick_decay_and_uses_each_individual_in_mean](../../../../tests/test_p3_reservation_price_d.py#L141) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_ready_dish_payload_and_frozen_price_do_not_decay](../../../../tests/test_p3_reservation_price_d.py#L161) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_reserved_items_decay_and_are_replaced_when_they_spoil](../../../../tests/test_p3_reservation_price_d.py#L69) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_spoilage_releases_entire_recipe_before_reselecting](../../../../tests/test_p3_reservation_price_d.py#L81) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_spoiled_raw_items_cannot_create_an_affordable_order](../../../../tests/test_p3_reservation_price_d.py#L62) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_tip_uses_discounted_payload_price_at_patience_boundary](../../../../tests/test_p3_reservation_price_d.py#L170) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_two_orders_cannot_reserve_same_physical_item](../../../../tests/test_p3_reservation_price_d.py#L55) | C/B | [p3-reservation_price.txt](p3-reservation_price.txt) |
| [test_consumed_id_is_not_reused_in_next_day_template](../../../../tests/test_p3_integration_d.py#L79) | C | [p3-integration.txt](p3-integration.txt) |
| [test_day_handoff_is_same_tick_without_second_decay](../../../../tests/test_p3_integration_d.py#L28) | C | [p3-integration.txt](p3-integration.txt) |
| [test_deterministic_bytes_for_identical_individual_fixture_and_inputs](../../../../tests/test_p3_integration_d.py#L98) | C | [p3-integration.txt](p3-integration.txt) |
| [test_faint_handoff_to_day_quan_has_empty_individual_stock](../../../../tests/test_p3_integration_d.py#L89) | C | [p3-integration.txt](p3-integration.txt) |
| [test_file_handoff_preserves_ids_kind_and_exact_post_gather_freshness](../../../../tests/test_p3_integration_d.py#L17) | C | [p3-integration.txt](p3-integration.txt) |
| [test_item_ids_increase_across_days_even_after_shop_discards_leftovers](../../../../tests/test_p3_integration_d.py#L66) | C | [p3-integration.txt](p3-integration.txt) |
| [test_new_ids_follow_loaded_max_and_remain_distinct_for_each_yield](../../../../tests/test_p3_integration_d.py#L56) | C | [p3-integration.txt](p3-integration.txt) |
| [test_shop_raw_stock_stops_decay_while_active_or_paused](../../../../tests/test_p3_integration_d.py#L43) | C | [p3-integration.txt](p3-integration.txt) |
| [test_p1_dock_priority_over_harvest_keeps_individual_handoff_schema](../../../../tests/test_p3_integration_d.py#L124) | C | [p3-integration.txt](p3-integration.txt) |
| [test_p1_service_on_closing_tick_is_paid_before_quan_end](../../../../tests/test_p3_integration_d.py#L138) | C | [p3-integration.txt](p3-integration.txt) |
| [test_p2_four_tables_and_two_stoves_remain_in_quan_snapshot](../../../../tests/test_p3_integration_d.py#L133) | C | [p3-integration.txt](p3-integration.txt) |

Mỗi lượt CLI được đánh chỉ số trong [cli-runs.json](cli-runs.json); record có đầy đủ scenario/input, seed, tick, argv, exit và stderr. Khối failures trong [summary.json](summary.json) giữ nguyên expected/actual của từng assertion/subcase.
