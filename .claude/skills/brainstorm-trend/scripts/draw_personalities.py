#!/usr/bin/env python3
"""Seeded personality draw for brainstorm-trend.

The pool has two leans, ``mechanism`` and ``form``. The seed fixes one
shuffled order of each lean. A contest draws the first three of each; a
gate-rejected contract is replaced by the next one of the same lean, so no
personality is ever drawn twice, the contest keeps three of each lean, and a
run can be replayed from its seed alone. Deterministic tooling only, per root
``AGENTS.md``: no model calls and no agent orchestration.

    draw_personalities.py [--seed N]                            the six
    draw_personalities.py --seed N --lean L --replacement K     replacement K of lean L
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

POOL_PATH = Path(__file__).resolve().parents[1] / "personalities.json"
LEANS = ("mechanism", "form")
PER_LEAN = 3
MAX_REPLACEMENTS = 5


class DrawError(ValueError):
    """A malformed pool or an impossible draw."""


def load_pool(path: Path = POOL_PATH) -> List[Dict[str, Any]]:
    pool = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(pool, list) or not pool:
        raise DrawError("personality pool must be a non-empty JSON list")
    ids = [entry.get("id") for entry in pool if isinstance(entry, dict)]
    if len(ids) != len(pool) or not all(isinstance(item, str) and item for item in ids):
        raise DrawError("every personality needs a non-empty id")
    if len(set(ids)) != len(ids):
        raise DrawError("personality ids must be unique")
    for entry in pool:
        if entry.get("leans") not in LEANS:
            raise DrawError("personality %r must lean mechanism or form" % entry["id"])
    for lean in LEANS:
        # Every replacement could fall on one lean.
        if sum(1 for entry in pool if entry["leans"] == lean) < PER_LEAN + MAX_REPLACEMENTS:
            raise DrawError(
                "pool needs at least %d %s personalities" % (PER_LEAN + MAX_REPLACEMENTS, lean)
            )
    return pool


def order(pool: Sequence[Dict[str, Any]], seed: int) -> Dict[str, List[Dict[str, Any]]]:
    """Each lean's personalities in the order ``seed`` fixes."""

    rng = random.Random(seed)
    ordered = {}
    for lean in LEANS:
        members = [entry for entry in pool if entry["leans"] == lean]
        rng.shuffle(members)
        ordered[lean] = members
    return ordered


def draw(pool: Sequence[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    ordered = order(pool, seed)
    return [entry for lean in LEANS for entry in ordered[lean][:PER_LEAN]]


def replacement(
    pool: Sequence[Dict[str, Any]], seed: int, lean: str, number: int
) -> Dict[str, Any]:
    """Replacement ``number`` (1-based, counted within ``lean``) for the
    contest ``seed`` drew."""

    if lean not in LEANS:
        raise DrawError("lean must be mechanism or form")
    if not 1 <= number <= MAX_REPLACEMENTS:
        raise DrawError("replacement must be 1 to %d" % MAX_REPLACEMENTS)
    return order(pool, seed)[lean][PER_LEAN + number - 1]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Draw brainstorm-trend personalities.")
    parser.add_argument("--seed", type=int, help="omit to draw a fresh seed")
    parser.add_argument("--lean", choices=LEANS, help="the rejected personality's lean")
    parser.add_argument("--replacement", type=int, help="1-5 within the lean; needs --seed and --lean")
    parser.add_argument("--pool", type=Path, default=POOL_PATH)
    args = parser.parse_args(argv)

    try:
        pool = load_pool(args.pool)
        if args.replacement is not None:
            if args.seed is None or args.lean is None:
                raise DrawError("--replacement needs the contest's --seed and the --lean")
            result: Dict[str, Any] = {
                "seed": args.seed,
                "lean": args.lean,
                "replacement": args.replacement,
                "personality": replacement(pool, args.seed, args.lean, args.replacement),
            }
        else:
            seed = args.seed if args.seed is not None else secrets.randbelow(2**31)
            result = {"seed": seed, "personalities": draw(pool, seed)}
    except DrawError as exc:
        print("draw-personalities: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
