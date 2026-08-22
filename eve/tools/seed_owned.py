#!/usr/bin/env python3
"""Loop A — seed the corpus `owned` set from the 10 catalog games.

Runs corpus.seed_owned idempotently so the novelty gate is enforced against
the games already on the storefront (GYRE, TRUE-MEASURE, SLUICE, PLUMB,
INTERLOCK, SPIRULINE, CATENARY, THE ESCAPEMENT, VEX, THE ORACLE).

Usage:
  python3 tools/seed_owned.py           # ensure all 10 are owned (idempotent)
  python3 tools/seed_owned.py --show    # print the current owned set after
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eve import config, corpus  # noqa: E402


def _cfg():
    return config.Config.load()


def main(argv):
    cfg = _cfg()
    rows = corpus.seed_owned(cfg)
    print(f"ensured {len(rows)} catalog axes owned:")
    for r in rows:
        print(f"  - {r['mechanic']!r} / {r['theme']!r}")
    if "--show" in argv:
        sat = corpus.saturation(cfg)
        print("\nowned mechanics:", sorted(sat["owned"]["mechanics"]))
        print("owned themes:    ", sorted(sat["owned"]["themes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
