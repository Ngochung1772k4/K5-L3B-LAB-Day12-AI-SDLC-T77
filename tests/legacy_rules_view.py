"""Migrate D's P1 quantity/order checks to the v1.2 individual-item boundary.

Only schema properties superseded by TICKET-03 are projected: items -> kinds,
stock/reserved IDs -> kind counts. All events, ticks, timers, prices, money,
reputation, reasons and entity IDs remain actual output. Raw files are never
rewritten. P3 tests separately assert exact item IDs/freshness and serialization.
Assertions here reject malformed modern output rather than hiding it.
"""

import copy
import json

from helpers import counts, items, stock_of


def individual_fixture(block):
    block = copy.deepcopy(block)
    if "hold" in block and all(isinstance(k, str) for k in block["hold"]):
        block["hold"] = items(*block["hold"])
    if isinstance(block.get("stock"), dict):
        block["stock"] = stock_of(block["stock"])
    stock = block.get("stock", [])
    allocated = set()
    for customer in block.get("customers", []):
        reserved = customer.get("reserved")
        if not isinstance(reserved, dict):
            continue
        selected = []
        for kind, amount in sorted(reserved.items()):
            candidates = [it["id"] for it in stock if it["kind"] == kind and it["id"] not in allocated]
            for n in range(amount):
                ident = candidates[n] if n < len(candidates) else f"missing-{customer['id']}-{kind}-{n}"
                selected.append(ident)
                allocated.add(ident)
        customer["reserved"] = selected
    return block


def item_kinds(values):
    assert isinstance(values, list), "v1.2 item array required"
    assert all(isinstance(v, dict) and set(v) == {"id", "kind", "fresh"} for v in values), values
    assert len({v["id"] for v in values}) == len(values), "duplicate physical ID"
    return [v["kind"] for v in values]


def inventory_counts(value):
    assert set(value) == {"items"}, value
    item_kinds(value["items"])
    return {"items": counts(value["items"])}


def saved_counts(path):
    return inventory_counts(json.loads(path.read_text(encoding="utf-8")))


def quantity_rows(raw_rows):
    """Read-only semantic view of the actual v1.2 JSONL for old P1 assertions."""
    rows = copy.deepcopy(raw_rows)
    for row in rows:
        if row["type"] == "snapshot":
            if "hold" in row:
                row["hold"] = item_kinds(row["hold"])
            if "stock" in row:
                physical = row["stock"]
                item_kinds(physical)
                by_id = {it["id"]: it for it in physical}
                claimed = []
                for c in row["customers"]:
                    ids = c["reserved"]
                    assert isinstance(ids, list), "v1.2 reserved IDs must be a list"
                    assert all(ident in by_id for ident in ids), ids
                    claimed.extend(ids)
                    c["reserved"] = counts([by_id[ident] for ident in ids])
                assert len(claimed) == len(set(claimed)), "reservation overbooking"
                row["stock"] = counts(physical)
        if row["type"] == "event":
            if row["name"] == "gather_end":
                row["data"]["inventory"] = inventory_counts(row["data"]["inventory"])
            if row["name"] in ("faint", "monster_hit"):
                row["data"]["lost"] = item_kinds(row["data"]["lost"])
            if row["name"] == "cook_started":
                row["data"]["items"] = item_kinds(row["data"]["items"])
    return rows
