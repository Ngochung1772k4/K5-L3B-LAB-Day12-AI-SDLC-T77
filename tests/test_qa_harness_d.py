"""Guard QA adapters so portability/schema migration cannot mask app failures."""
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import mock_open, patch

from helpers import items, manifest_cmd, run_headless
from legacy_rules_view import individual_fixture, quantity_rows


class QAHarness(unittest.TestCase):
    def test_python_manifest_uses_active_interpreter_preserving_arguments(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"headless_cmd": "python3 -m chonoi.headless"}))):
            self.assertEqual(manifest_cmd(), [sys.executable, "-B", "-m", "chonoi.headless"])

    def test_non_python_manifest_command_remains_unchanged(self):
        with patch("builtins.open", mock_open(read_data=json.dumps({"headless_cmd": './game headless "two words"'}))):
            self.assertEqual(manifest_cmd(), ["./game", "headless", "two words"])

    def test_application_exit_codes_are_never_retried_or_relabelled(self):
        for code in (1, 2, 9009):
            with self.subTest(code=code), patch("helpers.subprocess.run", return_value=subprocess.CompletedProcess([], code, "", "diagnostic")) as run:
                self.assertEqual(run_headless("--mode", "gather"), (code, "diagnostic"))
                run.assert_called_once()

    def test_legacy_fixture_reservations_use_distinct_real_individuals(self):
        old = {"stock": {"ca_loc": 2}, "customers": [
            {"id": "C1", "reserved": {"ca_loc": 1}}, {"id": "C2", "reserved": {"ca_loc": 1}}]}
        original = copy.deepcopy(old)
        modern = individual_fixture(old)
        self.assertEqual(old, original)
        self.assertEqual(modern["stock"], items("ca_loc", "ca_loc"))
        self.assertEqual([c["reserved"] for c in modern["customers"]], [["I1"], ["I2"]])

    def test_legacy_output_view_preserves_non_schema_values_and_raw_output(self):
        raw = [{"type": "snapshot", "tick": 7, "stock": items("ca_loc", fresh=79),
                "customers": [{"reserved": ["I1"], "base_price": 47}], "money": 56},
               {"type": "event", "name": "cook_started", "tick": 8,
                "data": {"items": items("ca_loc", fresh=79), "base_price": 47}}]
        original = copy.deepcopy(raw)
        view = quantity_rows(raw)
        self.assertEqual(raw, original)
        self.assertEqual(view[0], {"type": "snapshot", "tick": 7, "stock": {"ca_loc": 1},
            "customers": [{"reserved": {"ca_loc": 1}, "base_price": 47}], "money": 56})
        self.assertEqual(view[1]["data"], {"items": ["ca_loc"], "base_price": 47})

    def test_legacy_view_rejects_duplicate_ids_dangling_and_shared_reservations(self):
        cases = [
            {"stock": items("ca_loc") * 2, "customers": []},
            {"stock": items("ca_loc"), "customers": [{"reserved": ["I9"]}]},
            {"stock": items("ca_loc"), "customers": [{"reserved": ["I1"]}, {"reserved": ["I1"]}]},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(AssertionError):
                quantity_rows([dict(case, type="snapshot")])
