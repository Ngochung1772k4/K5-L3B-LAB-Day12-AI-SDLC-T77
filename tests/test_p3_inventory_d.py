"""D's black-box v1.2 inventory tests and shared, test-local CLI support.

Authority: docs/prd/TICKET-03.md, confirmed by the user. New freshness
constants are requirements from that ticket, never inferred from v1.1 code.
No gameplay imports. Runtime files are confined to Workdir. RUN_EVIDENCE is
in-memory data which an external QA runner may retain under its allowed proof
directory; running unittest alone creates no reports in the repository.
"""

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest
from fractions import Fraction

from helpers import ROOT, Workdir, events, frames, read_jsonl, snapshots, write_json


INITIAL = 100
SPOILED_BELOW = 30
GATHER_DECAY = Fraction(1, 120)  # 0.5 / 60, TICKET-03 section 1.
QUAN_DECAY = Fraction(1, 240)    # 0.25 / 60.
RUN_EVIDENCE = []


def item(ident="I1", kind="ca_loc", fresh=INITIAL):
    return {"id": ident, "kind": kind, "fresh": fresh}


def gather(**updates):
    block = {"player": {"pos": [20, 0]}, "hold": [], "nodes": [],
             "fish": [], "random_fish": False, "monsters": []}
    block.update(updates)
    return {"gather": block}


def quan(**updates):
    block = {"stock": [], "customers": [], "random_customers": False}
    block.update(updates)
    return {"quan": block}


def customer(ident="C1", table="T1", dish="ca_loc_nuong_trui", **updates):
    result = {"id": ident, "table_id": table, "dish_id": dish}
    result.update(updates)
    return result


class Phase3Case(unittest.TestCase):
    """Shared support without test methods, so imports do not duplicate tests."""

    @classmethod
    def setUpClass(cls):
        with open(Path(ROOT) / "game.contract.json", encoding="utf-8") as stream:
            cls.contract = json.load(stream)
        cls.t = cls.contract["tuning"]
        cls.menu = cls.t["menu"]
        cls.hz = cls.t["tick_hz"]

    def setUp(self):
        self.work = Workdir()
        self.work.__enter__()
        self.addCleanup(self.work.__exit__, None, None, None)
        self.serial = 0

    def invoke(self, mode, scenario=None, ticks=0, inputs=None, inventory=None,
               inventory_source=None, inventory_out=False, existing_output=None,
               days=None, seed=17, every=1):
        self.serial += 1
        prefix = str(self.serial)
        out = Path(self.work.path(prefix + ".jsonl"))
        inventory_path = Path(self.work.path(prefix + "-out-inventory.json"))
        if existing_output is not None:
            inventory_path.write_bytes(existing_output)
        # This is the Python entry point declared by the current manifest.
        # sys.executable avoids Windows python3 aliases/exit 9009.
        argv = [sys.executable, "-B", "-m", "chonoi.headless", "--mode", mode,
                "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", str(out)]
        if scenario is not None:
            argv += ["--scenario", write_json(self.work.path(prefix + "-scenario.json"), scenario)]
        if inputs is not None:
            argv += ["--inputs", write_json(self.work.path(prefix + "-inputs.json"), frames(*inputs))]
        if inventory is not None:
            self.assertIsNone(inventory_source)
            inventory_source = write_json(self.work.path(prefix + "-in-inventory.json"), inventory)
        if inventory_source is not None:
            argv += ["--inventory", str(inventory_source)]
        if inventory_out:
            argv += ["--inventory-out", str(inventory_path)]
        if days is not None:
            argv += ["--days", str(days)]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        process = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=60)
        evidence = {"test": self.id(), "mode": mode, "seed": seed, "ticks": ticks,
                    "days": days, "snapshot_every": every, "argv": argv,
                    "scenario": scenario, "inputs": inputs,
                    "inventory_input": json.loads(Path(inventory_source).read_text(encoding="utf-8"))
                    if inventory_source is not None else None,
                    "exit_code": process.returncode,
                    "stdout": process.stdout.decode("utf-8", errors="replace"),
                    "stderr": process.stderr.decode("utf-8", errors="replace"),
                    "jsonl": out.read_text(encoding="utf-8") if out.exists() else None,
                    "inventory_output": inventory_path.read_text(encoding="utf-8")
                    if inventory_path.exists() else None}
        RUN_EVIDENCE.append(evidence)
        self.output, self.inventory_output = out, inventory_path
        self.evidence = evidence
        return process.returncode, evidence["stderr"]

    def run_game(self, mode, scenario=None, ticks=0, **kwargs):
        code, stderr = self.invoke(mode, scenario, ticks, **kwargs)
        if code not in (0, 2):
            raise RuntimeError(f"CLI execution ERROR (exit {code}): {stderr}")
        blocked = ("BLOCKED: implementation contract " + self.contract["contract_version"]
                   + " has not migrated to required v1.2. ") if self.contract["contract_version"] not in ("1.2", "1.3") else ""
        self.assertEqual(code, 0, blocked + "A fixture valid under TICKET-03 was rejected: " + stderr)
        rows = read_jsonl(self.output)
        self.assertTrue(rows)
        self.assertEqual(rows[-1]["type"], "end")
        self.assertEqual(sum(r["type"] == "end" for r in rows), 1)
        snaps = snapshots(rows)
        self.assertEqual(len(snaps), len({s["tick"] for s in snaps}))
        self.assertEqual(snaps[0]["tick"], 0)
        self.assertEqual(snaps[-1]["tick"], rows[-1]["ticks"])
        for event in events(rows):
            matching = [s for s in snaps if s["tick"] == event["tick"]]
            if matching:
                self.assertLess(rows.index(event), rows.index(matching[0]))
        self.rows = rows
        return rows

    def rejected(self, mode, **kwargs):
        code, stderr = self.invoke(mode, **kwargs)
        self.assertEqual(code, 2, "Expected a Contract v1.2 schema rejection: " + stderr)
        self.assertTrue(stderr.strip())
        self.assertFalse(self.output.exists(), "validate before creating JSONL")
        self.assertFalse(self.inventory_output.exists())

    def inventory_control(self):
        # Positive control prevents an old reader rejecting *every* item array
        # from making all negative-schema tests appear to pass.
        self.run_game("quan", inventory={"items": [item()]})

    def snap(self, tick, rows=None):
        found = [s for s in snapshots(self.rows if rows is None else rows) if s["tick"] == tick]
        self.assertEqual(len(found), 1, f"expected one snapshot at tick {tick}")
        return found[0]

    def one(self, name, tick=None, rows=None):
        found = events(self.rows if rows is None else rows, name)
        self.assertEqual(len(found), 1, f"expected exactly one {name}, got {found}")
        if tick is not None:
            self.assertEqual(found[0]["tick"], tick)
        return found[0]

    def entities(self, values):
        self.assertIsInstance(values, list, "v1.2 requires an item array")
        for value in values:
            self.assertIsInstance(value, dict)
            self.assertEqual(set(value), {"id", "kind", "fresh"})
            self.assertIsInstance(value["id"], str)
            self.assertTrue(value["id"])
            self.assertIsInstance(value["fresh"], (int, float))
            self.assertNotIsInstance(value["fresh"], bool)
            self.assertTrue(math.isfinite(value["fresh"]))
            self.assertTrue(0 <= value["fresh"] <= INITIAL)
        self.assertEqual(len(values), len({value["id"] for value in values}))
        return {value["id"]: value for value in values}

    def fresh(self, actual, expected):
        self.assertAlmostEqual(actual, float(expected), delta=0.01)

    def waiting(self, tick, ident="C1"):
        found = [c for c in self.snap(tick)["customers"] if c["id"] == ident]
        self.assertEqual(len(found), 1)
        return found[0]


class InventoryV12(Phase3Case):
    def test_manifest_declares_v12_and_required_freshness_values(self):
        # P4 nâng contract lên 1.3 (chỉ thêm bench/soak, gameplay giữ v1.2) -> chấp nhận 1.2 và 1.3
        self.assertIn(self.contract["contract_version"], ("1.2", "1.3"), "BLOCKED: v1.2 migration pending")
        expected = {"initial": 100, "gather_decay_per_s": 0.5,
                    "quan_decay_per_s": 0.25, "spoiled_below": 30}
        # The ticket names the block but does not prescribe root vs tuning.
        # Check its values without inventing a container-path requirement.
        blocks = [container["freshness"] for container in (self.contract, self.t)
                  if "freshness" in container]
        self.assertTrue(blocks, "required freshness data is missing")
        for block in blocks:
            self.assertEqual(block, expected)

    def test_reader_preserves_ids_freshness_and_already_spoiled_items_at_tick_zero(self):
        values = [item("I2", fresh=0), item("I10", "ca_keo", 29.5), item("raw-id", "keo_neo", 100)]
        self.run_game("quan", inventory={"items": values})
        self.assertEqual(self.entities(self.snap(0)["stock"]), {v["id"]: v for v in values})
        self.assertEqual(events(self.rows, "spoiled"), [])

    def test_empty_individual_inventory_is_accepted(self):
        self.run_game("quan", inventory={"items": []})
        self.assertEqual(self.snap(0)["stock"], [])

    def test_quan_inventory_is_not_limited_by_gather_capacity(self):
        values = [item(f"I{i + 1}") for i in range(self.t["gather"]["hold_capacity"] + 3)]
        self.run_game("quan", inventory={"items": values})
        self.assertEqual(len(self.entities(self.snap(0)["stock"])), len(values))

    def test_count_inventory_v11_is_rejected_including_empty_count_map(self):
        for old in ({"items": {}}, {"items": {"ca_loc": 1}}):
            with self.subTest(inventory=old):
                self.rejected("quan", inventory=old)

    def test_inventory_root_and_item_field_schema_are_strict(self):
        self.inventory_control()
        invalid = [{}, {"items": None}, {"items": [], "extra": 1}, [],
                   {"items": [{"id": "I1", "kind": "ca_loc"}]},
                   {"items": [dict(item(), extra=1)]}]
        for value in invalid:
            with self.subTest(inventory=value):
                self.rejected("quan", inventory=value)

    def test_inventory_ids_are_nonempty_strings_and_unique(self):
        self.inventory_control()
        for value in ([item("")], [item(1)], [item(True)], [item(), item()]):
            with self.subTest(items=value):
                self.rejected("quan", inventory={"items": value})

    def test_inventory_freshness_is_finite_numeric_and_within_bounds(self):
        self.inventory_control()
        for value in (-0.001, 100.001, float("nan"), float("inf"), -float("inf"), None, "50", True):
            with self.subTest(fresh=value):
                self.rejected("quan", inventory={"items": [item(fresh=value)]})

    def test_inventory_unknown_kind_is_rejected(self):
        self.inventory_control()
        self.rejected("quan", inventory={"items": [item(kind="unknown_kind")]})

    def test_scenario_rejects_duplicate_physical_ids_in_hold_or_stock(self):
        self.run_game("gather", gather(hold=[item()]))
        self.rejected("gather", scenario=gather(hold=[item(), item()]))
        self.run_game("quan", quan(stock=[item()]))
        self.rejected("quan", scenario=quan(stock=[item(), item()]))

    def test_gather_export_sorts_ids_but_hold_retains_acquisition_order(self):
        self.run_game("gather", gather(hold=[item("I10"), item("I2")], time_left_ticks=1),
                      ticks=1, inventory_out=True)
        self.assertEqual([i["id"] for i in self.snap(1)["hold"]], ["I10", "I2"])
        saved = json.loads(self.inventory_output.read_text(encoding="utf-8"))
        self.assertEqual(set(saved), {"items"})
        self.assertEqual([i["id"] for i in saved["items"]], ["I2", "I10"])
        self.assertEqual(saved, self.one("gather_end", 1)["data"]["inventory"])

    def test_tick_limit_does_not_create_or_replace_inventory(self):
        for sentinel in (None, b"pre-existing inventory bytes\n"):
            with self.subTest(preexisting=sentinel is not None):
                self.run_game("gather", gather(hold=[item()], time_left_ticks=3), ticks=1,
                              inventory_out=True, existing_output=sentinel)
                self.assertEqual(self.rows[-1]["reason"], "tick_limit")
                self.assertEqual(events(self.rows, "gather_end"), [])
                if sentinel is None:
                    self.assertFalse(self.inventory_output.exists())
                else:
                    self.assertEqual(self.inventory_output.read_bytes(), sentinel)

    def test_export_precision_keeps_spoiled_side_of_threshold_after_reload(self):
        self.run_game("gather", gather(hold=[item(fresh=30.125)], time_left_ticks=16),
                      ticks=16, inventory_out=True)
        self.one("spoiled", 16)
        saved = json.loads(self.inventory_output.read_text(encoding="utf-8"))
        self.assertLess(saved["items"][0]["fresh"], SPOILED_BELOW)
        source = self.inventory_output
        self.run_game("quan", inventory_source=source)
        self.assertEqual(self.snap(0)["stock"], saved["items"])
        self.assertLess(self.snap(0)["stock"][0]["fresh"], SPOILED_BELOW)


if __name__ == "__main__":
    unittest.main()
