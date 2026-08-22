#!/usr/bin/env python3
"""Stub claude CLI for tests — the only sanctioned way to exercise
run_agent's starved/crashed/quota classification without a real CLI call
(CONTRACTS §5: no network, no real claude in tests).

Behavior is chosen by env FAKE_MODE so the test controls the scenario while
run_agent controls the argv (exactly as it would with the real binary):

  success   — well-formed result JSON, exit 0
  starved   — subtype error_max_turns (the "71/70 turns" scram receipt)
  crashed   — subtype error_during_execution, is_error true
  quota     — error text carrying "usage limit" (the silent 08-13 death)
  quota_stderr — garbage stdout + "rate limit" on stderr, exit 1
  garbage   — unparseable stdout, exit 1
  hang      — sleep 600s (forces the overrun kill path)

It also echoes the argv it received to FAKE_ARGV_OUT (when set) so tests
can assert the exact flags run_agent shelled with.
"""
import json
import os
import sys
import time

mode = os.environ.get("FAKE_MODE", "success")

out = os.environ.get("FAKE_ARGV_OUT")
if out:
    with open(out, "w") as f:
        json.dump(sys.argv[1:], f)

if mode == "success":
    print(json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": "the canned CLI answer",
        "total_cost_usd": 0.1234, "num_turns": 7,
    }))
    sys.exit(0)

if mode == "starved":
    print(json.dumps({
        "type": "result", "subtype": "error_max_turns", "is_error": True,
        "result": "", "total_cost_usd": 0.42, "num_turns": 40,
    }))
    sys.exit(0)

if mode == "crashed":
    print(json.dumps({
        "type": "result", "subtype": "error_during_execution",
        "is_error": True, "result": "tool exploded mid-flight",
        "total_cost_usd": 0.05, "num_turns": 3,
    }))
    sys.exit(1)

if mode == "quota":
    print(json.dumps({
        "type": "result", "subtype": "error_during_execution",
        "is_error": True,
        "result": "You've reached your usage limit. Limit resets at 3pm.",
        "total_cost_usd": 0.0, "num_turns": 1,
    }))
    sys.exit(1)

if mode == "quota_stderr":
    sys.stderr.write("API Error: 429 rate limit exceeded\n")
    print("not json at all")
    sys.exit(1)

if mode == "garbage":
    print("Segmentation fault (core dumped)")
    sys.exit(139)

if mode == "hang":
    time.sleep(600)
    sys.exit(0)

sys.stderr.write("fake_claude: unknown FAKE_MODE %r\n" % mode)
sys.exit(2)
