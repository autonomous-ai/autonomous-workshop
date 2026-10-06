#!/usr/bin/env python3
"""Seeded personality draw for brainstorm-trend.

The seed fixes one shuffled order of the whole pool. The first five are the
contest's personalities; each replacement for a gate-rejected contract is the
next one in that order, so no personality is ever drawn twice and a run can
be replayed from its seed alone. Deterministic tooling only, per root
``AGENTS.md``: no model calls and no agent orchestration.

    draw_personalities.py [--seed N]                 the first five
    draw_personalities.py --seed N --replacement K   replacement K (1-5)
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
CONTESTANTS = 5
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
    if len(pool) < CONTESTANTS + MAX_REPLACEMENTS:
        raise DrawError(
            "pool needs at least %d personalities" % (CONTESTANTS + MAX_REPLACEMENTS)
        )
    return pool


def order(pool: Sequence[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    """The whole pool in the order ``seed`` fixes."""

    shuffled = list(pool)
    random.Random(seed).shuffle(shuffled)
    return shuffled


def draw(pool: Sequence[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    return order(pool, seed)[:CONTESTANTS]


def replacement(pool: Sequence[Dict[str, Any]], seed: int, number: int) -> Dict[str, Any]:
    """Replacement ``number`` (1-based) for the contest ``seed`` drew."""

    if not 1 <= number <= MAX_REPLACEMENTS:
        raise DrawError("replacement must be 1 to %d" % MAX_REPLACEMENTS)
    return order(pool, seed)[CONTESTANTS + number - 1]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Draw brainstorm-trend personalities.")
    parser.add_argument("--seed", type=int, help="omit to draw a fresh seed")
    parser.add_argument("--replacement", type=int, help="1-5; needs --seed")
    parser.add_argument("--pool", type=Path, default=POOL_PATH)
    args = parser.parse_args(argv)

    try:
        pool = load_pool(args.pool)
        if args.replacement is not None:
            if args.seed is None:
                raise DrawError("--replacement needs the contest's --seed")
            result: Dict[str, Any] = {
                "seed": args.seed,
                "replacement": args.replacement,
                "personality": replacement(pool, args.seed, args.replacement),
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
