# Notes on actual CLI evidence

All CLI records are post-run observations. A CLI exit 0 is not a test PASS when the assertion expected a v1.2 rejection or item payload.

| Record | Test | Exit | Actual output |
|---|---|---|---|
| 1 | test_p3_inventory_d.InventoryV12.test_count_inventory_v11_is_rejected_including_empty_count_map | 0 | {"reason": "tick_limit", "hold": null, "stock": {}} |
| 2 | test_p3_inventory_d.InventoryV12.test_count_inventory_v11_is_rejected_including_empty_count_map | 0 | {"reason": "tick_limit", "hold": null, "stock": {"ca_loc": 1}} |
| 23 | test_p3_freshness_d.FreshnessV12.test_new_fish_yield_gets_distinct_ids_and_no_same_tick_decay | 0 | {"reason": "tick_limit", "hold": ["ca_linh", "ca_linh", "ca_linh"], "stock": null} |
| 24 | test_p3_freshness_d.FreshnessV12.test_new_harvest_starts_at_one_hundred_then_decays_from_next_step | 0 | {"reason": "tick_limit", "hold": ["bong_sung"], "stock": null} |
| 60 | test_p3_integration_d.UnchangedRegression.test_p1_dock_priority_over_harvest_keeps_individual_handoff_schema | 0 | {"reason": "docked", "hold": [], "stock": null} |
| 62 | test_p3_integration_d.UnchangedRegression.test_p1_underwater_oxygen_consumes_one_per_gameplay_step | 0 | {"reason": "tick_limit", "hold": [], "stock": null} |
| 64 | test_p3_integration_d.UnchangedRegression.test_p2_pause_stops_clock_and_inputs_until_resume_edge | 0 | {"reason": "tick_limit", "hold": [], "stock": null} |

The tick-limit subcase pre-creates an ASCII sentinel at its inventory output path before launching headless. Its retained inventory artifact is the existing sentinel, not evidence that headless created a file after exiting 2. The current v1.1 reader blocks the gameplay assertion before preservation can be accepted.

Runner Python: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]. Every new CLI uses sys.executable and -B with PYTHONDONTWRITEBYTECODE=1. Concurrent cpython-315.pyc files observed outside scope were not produced by this Python 3.11 runner. Their origin is not otherwise established; no external file was removed.

Source-before/source-after fingerprints are identical. The in-memory adapter used for 26 legacy regression cases changes only the Python executable, not schema, assertions or implementation.
