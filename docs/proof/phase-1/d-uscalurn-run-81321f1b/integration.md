# Smoke integration Phase 1

Revision: `6a7f66a35e5816996fe51010ea5b20ac9098fe5c` (working tree; see source hashes in summary.json).

Result: **PASS**. Two separate headless processes; temporary runtime paths are cleaned.

```json
{
  "status": "PASS",
  "expected": {
    "items": {
      "bong_sung": 2,
      "ca_loc": 1
    }
  },
  "actual": {
    "inventory": {
      "items": {
        "bong_sung": 2,
        "ca_loc": 1
      }
    },
    "gather_end": [
      {
        "reason": "docked",
        "inventory": {
          "items": {
            "bong_sung": 2,
            "ca_loc": 1
          }
        }
      }
    ],
    "quan_tick_zero_stock": [
      {
        "bong_sung": 2,
        "ca_loc": 1
      }
    ]
  },
  "errors": [],
  "scenario": {
    "gather": {
      "hold": [
        "ca_loc",
        "bong_sung",
        "bong_sung"
      ]
    }
  },
  "inputs": {
    "frames": [
      {
        "tick": 0,
        "interact": true
      }
    ]
  },
  "processes": [
    {
      "argv": [
        "C:\\Users\\Siuuu\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
        "-B",
        "-m",
        "chonoi.headless",
        "--mode",
        "gather",
        "--seed",
        "42",
        "--scenario",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\dock.json",
        "--inputs",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\inputs.json",
        "--ticks",
        "1",
        "--out",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\gather.jsonl",
        "--inventory-out",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\inventory.json"
      ],
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    {
      "argv": [
        "C:\\Users\\Siuuu\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
        "-B",
        "-m",
        "chonoi.headless",
        "--mode",
        "quan",
        "--seed",
        "42",
        "--inventory",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\inventory.json",
        "--ticks",
        "0",
        "--out",
        "C:\\Users\\Siuuu\\AppData\\Local\\Temp\\t77-smoke-h08pi2iw\\quan.jsonl"
      ],
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    }
  ]
}
```

Retained raw-byte copies: [Gather JSONL](integration-gather.jsonl.txt), [Quan JSONL](integration-quan.jsonl.txt). See [artifact-manifest.json](artifact-manifest.json); the original .jsonl paths in the record are also present locally but ignored by Git.
