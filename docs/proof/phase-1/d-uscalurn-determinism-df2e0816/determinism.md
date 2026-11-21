# Determinism Phase 1

Revision: `6a7f66a35e5816996fe51010ea5b20ac9098fe5c` plus working-tree source hashes in summary.json.

**PASS** for the three fixtures below. Runtime directories were separate and are cleaned.

| Case | JSONL byte equal | Inventory byte equal | Result |
|---|---|---|---|
| gather-docked | True | True | PASS |
| gather-time | True | True | PASS |
| quan | True | n/a | PASS |

Exact commands, fixture/input contents, stderr, exit codes, original temporary paths, retained artifact paths and SHA-256 values are in [summary.json](summary.json).

Repeatability is not gameplay correctness. These fixtures do not certify unimplemented harvesting, fishing, customer selection or payment branches.

Git-visible .jsonl.txt copies preserve all original bytes. Mapping and SHA-256: [artifact manifest](../d-uscalurn-run-81321f1b/artifact-manifest.json). Original summary artifact paths refer to the unchanged .jsonl files retained locally.
