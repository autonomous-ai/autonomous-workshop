#!/usr/bin/env python3
"""Contract gate: CONTRACT-FORMAT limits, Trend Hook and Signature Motion.

Runs after each personality's ``design-a-toy`` Stages 1-2 draft a Design
Contract (see the brainstorm-trend skill's "Gate" step). This is
deterministic tooling only (per root ``AGENTS.md``): it checks the format a
contract must meet before it is allowed into the round robin, and reports
every failure at once. It does not judge whether a Trend Hook is genuinely
countable or pointable, or whether a Signature Motion is any fun -- only that
both sections exist and that some Interface is coupled. Those judgements
belong to the orchestrator and the judges.

The limits on assembly and per-geometry requirement counts, and the whole-
file character limit, come from ADR 0072 and are the same ones
``workshop.wish.design_contract`` enforces before a run seals a contract; this
script reuses that check rather than re-deriving it, and adds what that
module has no reason to know about: the file-length ceiling
(``design_contract`` is handed already-sealed text, not a draft to size-gate),
the two prose sections, and the rule that a trend toy moves.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from workshop.errors import ContractError
from workshop.wish.design_contract import parse_design_contract

# ADR 0072, "A correction brief is itself a Wish objective, which is limited
# to 50,000 characters" -- the contract itself is kept lower, at 40,000, per
# CONTRACT-FORMAT.md.
MAX_CONTRACT_CHARACTERS = 40_000

REQUIRED_SECTIONS = ("Trend Hook", "Signature Motion")

_FENCE_START = "```design-contract"
_HEADING = re.compile(r"^#{1,6}[ \t]", re.MULTILINE)


def _section_present(prose: str, title: str) -> bool:
    """A ``title`` heading in the prose, followed by non-blank text."""

    heading = re.compile(
        r"^#{1,6}[ \t]*%s[ \t]*$" % re.escape(title), re.IGNORECASE | re.MULTILINE
    )
    match = heading.search(prose)
    if match is None:
        return False
    after = prose[match.end():]
    next_heading = _HEADING.search(after)
    body = after[: next_heading.start()] if next_heading else after
    return bool(body.strip())


def gate_contract(text: str) -> Tuple[bool, List[str]]:
    """Check ``text`` (a whole ``CONTRACT.md``) against the gate.

    Returns ``(passed, reasons)``. ``reasons`` is empty only when ``passed``
    is true; every failure the gate can detect is reported, not just the
    first.
    """

    reasons: List[str] = []

    if len(text) > MAX_CONTRACT_CHARACTERS:
        reasons.append(
            "contract is %d characters, over the %d character limit"
            % (len(text), MAX_CONTRACT_CHARACTERS)
        )

    contract = None
    try:
        contract = parse_design_contract(text)
    except ContractError as exc:
        message = str(exc)
        prefix = "design contract: "
        if message.startswith(prefix):
            message = message[len(prefix):]
        reasons.extend(message.split("; "))

    if contract is not None and not any(
        item.kind == "coupled" for item in contract.interfaces or ()
    ):
        reasons.append("no coupled Interface: a trend toy needs a Signature Motion")

    prose = text.split(_FENCE_START, 1)[0]
    for title in REQUIRED_SECTIONS:
        if not _section_present(prose, title):
            reasons.append("no %s section found in the prose" % title)

    return (not reasons, reasons)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="path to a CONTRACT.md draft")
    args = parser.parse_args(argv)

    text = args.contract.read_text(encoding="utf-8")
    passed, reasons = gate_contract(text)
    json.dump({"pass": passed, "reasons": reasons}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
