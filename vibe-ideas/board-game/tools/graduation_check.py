#!/usr/bin/env python3
"""graduation_check.py — every lesson that claims to have become code, checked
against the code, and told where it landed.

    .venv/bin/python board-game/tools/graduation_check.py

`lessons.md`'s rule is that a lesson which has cost two builds stops being
prose and becomes a lint rule, a threshold, a block, or a constraint in an
agent's template, and is then marked `[GRADUATED -> ...]`. That marker is a
claim, and until now nothing has ever checked it.

An unchecked claim rots two ways that look identical from outside: a refactor
deletes the rule and leaves the marker behind, or the marker was optimistic the
day it was written. Both end the same place — lessons.md says the pipeline is
protected against something it is not, and the lesson is not in the build
prompts either, because graduating it is exactly what took it out of them. A
graduated lesson that was never landed is worse than one that never graduated.

This is also what makes `improve.py` safe to run unattended. That session can
edit `gate.py` and rewrite `lessons.md` in the same run, so it is able to
un-land a graduation and keep the marker without ever meaning to.

The grammar. One marker, one or more targets, separated by commas, and an
optional ceiling clause after a pipe:

    - [GRADUATED -> ergonomics_check.MIN_RELIEF_MM] ...
    - [GRADUATED -> gate:"blanket-fillet"] ...
    - [GRADUATED -> gate.check_bill, blocks.add_piece_family] ...
    - [GRADUATED -> gate:"bed-size" | ceiling: the bed is 256mm, and no amount of planning makes a part fit one that is not] ...

A marker is read one line at a time and never wraps, however long it gets.

  `module.SYMBOL`  SYMBOL must be defined at the top level of that module:
                   `def SYMBOL(`, `class SYMBOL`, or `SYMBOL = `.
  `module:"..."`   the literal text must appear in that file. This is the form
                   for anything that is not a definition — a lint rule's id, a
                   sentence added to an agent's template — and it is why lint
                   rules carry ids: `gate.LINT_RULES` would stay true after the
                   one rule that mattered was deleted.

A target naming a module this file does not know is a FAILURE, not a skip. A
checker that cannot check something must never report it green; that is the
same rule `gate.py` follows with `unmeasured`.

WHERE A LESSON LANDS also matters, and is the second thing this file reports.
A true marker can still be a weak one: `gate.py` really does catch the blanket
fillet, and every build still writes it, still fails, and still spends a repair
round undoing it. Nothing is lying. The pipeline just pays that cost forever,
because the fix landed at the layer that detects rather than the layer that
prevents. A check is a smoke alarm; the alarm works and the house still burns
on schedule.

So each module carries a TIER, ordered by how many non-deterministic hops sit
between the fix and the geometry:

  1 planner  ideator, rules_check   the defect is never proposed
  2 block    blocks                 one hop (the builder calls it), then the
                                    geometry is right by construction
  3 brief    brief_writer           two hops: the writer obeys the template,
                                    then the builder obeys the brief
  4 prompt   builder                two hops and nothing verifies compliance
  5 check    gate, ergonomics_check, interference, pipeline_queue
                                    zero hops, but only after the build is
                                    already paid for

A lesson takes the BEST tier among its targets, which is what makes
`gate.check_bill, blocks.add_piece_family` read correctly: a block-tier fix
that also kept its smoke alarm.

A low tier is not a failure here and never fails this suite. Sometimes check
is the only honest answer, and forcing a fake upstream fix would be worse than
the smoke alarm. It is `audit.py` that raises it, as AMBER, and the ceiling
clause is how you spend that: a sentence saying why nothing upstream can catch
this. A reason under MIN_CEILING_CHARS characters does not count, so "n/a"
cannot buy it.

Prints ALL PASS (improve.py greps for exactly that) or the broken claims.
Exit 0/1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LESSONS = REPO_ROOT / "board-game" / "lessons.md"
AGENTS = REPO_ROOT / ".claude" / "agents"

#: Where a lesson is allowed to land. Adding a row is how you sanction a new
#: destination; a marker pointing anywhere else fails rather than being
#: ignored, so a typo cannot quietly become an unverified graduation.
MODULES: dict[str, Path] = {
    "gate": HERE / "gate.py",
    "ergonomics_check": HERE / "ergonomics_check.py",
    "rules_check": HERE / "rules_check.py",
    "interference": HERE / "interference.py",
    "pipeline_queue": HERE / "pipeline_queue.py",
    "blocks": REPO_ROOT / "board-game" / "blocks" / "blocks.py",
    "ideator": AGENTS / "board-game-ideator.md",
    "brief_writer": AGENTS / "board-game-brief-writer.md",
    "builder": AGENTS / "board-game-builder.md",
}

#: module -> (rank, name). See the tier ladder in this file's docstring. Lower
#: rank is further upstream, which is better. Every key in MODULES needs a row;
#: a module with no tier fails rather than being scored generously.
TIERS: dict[str, tuple[int, str]] = {
    "ideator": (1, "planner"),
    "rules_check": (1, "planner"),
    "blocks": (2, "block"),
    "brief_writer": (3, "brief"),
    "builder": (4, "prompt"),
    "gate": (5, "check"),
    "ergonomics_check": (5, "check"),
    "interference": (5, "check"),
    "pipeline_queue": (5, "check"),
}

CHECK_TIER = 5

#: A ceiling has to be an argument, not an acknowledgement. Long enough that
#: "no upstream fix" does not clear it, short enough that one real sentence does.
MIN_CEILING_CHARS = 40

MARKER = re.compile(r"\[GRADUATED\s*->\s*([^\]]+)\]")
TARGET = re.compile(r'(\w+)(?:\.(\w+)|:"([^"]*)")')
CEILING = re.compile(r"^\s*ceiling\s*:\s*(\S.*?)\s*$", re.S)
#: What may legally sit between two targets. Anything else in a marker means
#: it was written in prose, and prose is what this file exists to stop being
#: mistaken for a fix.
SEPARATORS = re.compile(r"^[\s,+]*$")


def _defines(text: str, symbol: str) -> bool:
    return re.search(rf"^(?:def|class)\s+{re.escape(symbol)}\b"
                     rf"|^{re.escape(symbol)}\s*(?::[^=\n]+)?=",
                     text, re.M) is not None


def check_target(module: str, symbol: str | None, literal: str | None) -> str | None:
    """None if the claim holds, else why it does not."""
    path = MODULES.get(module)
    if path is None:
        return (f"'{module}' is not a place a lesson can land — known: "
                f"{', '.join(sorted(MODULES))}")
    if module not in TIERS:
        return (f"'{module}' has no tier in graduation_check.TIERS — every "
                f"landing place must say how far upstream it is")
    if not path.is_file():
        return f"{module} points at {path.relative_to(REPO_ROOT)}, which does not exist"
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(REPO_ROOT)
    if symbol is not None:
        if _defines(text, symbol):
            return None
        hint = (' — .md targets need the module:"literal" form'
                if path.suffix == ".md" else "")
        return f"{rel} defines no `{symbol}`{hint}"
    if literal in text:
        return None
    return f'{rel} does not contain "{literal}"'


def _split_ceiling(body: str) -> tuple[str, str | None, str | None]:
    """(targets, ceiling reason, why the clause is malformed)."""
    head, pipe, tail = body.partition("|")
    if not pipe:
        return body, None, None
    found = CEILING.match(tail)
    if not found:
        return head, None, (f"the clause after `|` is not a ceiling — write "
                            f"`| ceiling: <why nothing upstream can catch this>`")
    reason = found.group(1)
    if len(reason) < MIN_CEILING_CHARS:
        return head, None, (f'ceiling "{reason}" is {len(reason)} characters; a '
                            f'ceiling is an argument for why no tier above this '
                            f'one can hold the fix, and needs at least '
                            f'{MIN_CEILING_CHARS}')
    return head, reason, None


def scan() -> tuple[list[dict], list[str], int]:
    """(graduations that hold, broken claims, lessons still prose).

    A graduation record: the lesson text, its targets, the best tier among
    them, and its ceiling reason if it declares one. Only lessons whose every
    target resolved are recorded, so a broken claim produces exactly one
    finding rather than a second one about where it failed to land.
    """
    if not LESSONS.is_file():
        return [], [f"{LESSONS} is missing"], 0
    good: list[dict] = []
    broken: list[str] = []
    prose = 0
    for line in LESSONS.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("-") or len(line) <= 40:
            continue
        found = MARKER.search(line)
        if not found:
            prose += 1
            continue
        body = found.group(1)
        lesson = line.split("]", 1)[-1].strip()[:70]
        head, ceiling, malformed = _split_ceiling(body)
        if malformed:
            broken.append(f'"{lesson}…": {malformed}')
            continue
        targets = list(TARGET.finditer(head))
        leftover = TARGET.sub("", head)
        if not targets or not SEPARATORS.match(leftover):
            broken.append(f'"{lesson}…": marker `{head.strip()}` is prose, not a '
                          f'target — see the grammar in this file')
            continue
        reasons = [why for match in targets
                   if (why := check_target(match.group(1), match.group(2),
                                           match.group(3)))]
        if reasons:
            broken.extend(f'"{lesson}…": {why}' for why in reasons)
            continue
        rank, tier = min(TIERS[m.group(1)] for m in targets)
        good.append({
            "lesson": lesson,
            "targets": [{"text": m.group(0), "module": m.group(1),
                         "symbol": m.group(2), "literal": m.group(3)}
                        for m in targets],
            "rank": rank,
            "tier": tier,
            "ceiling": ceiling,
        })
    return good, broken, prose


def verify() -> tuple[list[str], int, int]:
    """(broken claims, graduations verified, lessons still prose)."""
    good, broken, prose = scan()
    return broken, len(good), prose


def main() -> int:
    good, broken, prose = scan()
    if broken:
        print("GRADUATIONS BROKEN — a lesson claims to be code and is not:")
        for entry in broken:
            print(f"  - {entry}")
        print("\nEither land the fix again, or take the marker off and put the "
              "lesson back in the prompts. Leaving it is the one option that "
              "protects nothing while looking like it does.")
        return 1
    tally: dict[str, int] = {}
    for entry in good:
        tally[entry["tier"]] = tally.get(entry["tier"], 0) + 1
    ladder = ", ".join(f"{tally[name]} {name}" for _, name in sorted(set(TIERS.values()))
                       if name in tally)
    # Not a failure: a lesson that has only cost one build belongs in prose,
    # and a check-tier fix is sometimes the only honest one. Both numbers are
    # printed because they are the honest denominators — how much of what these
    # builds taught is still advice an agent has to remember every time, and
    # how much of what graduated only detects the defect after paying for it.
    # audit.py is what argues about the second number.
    print(f"ALL PASS ({len(good)} graduation(s) verified [{ladder or 'none'}], "
          f"{prose} lesson(s) still prose in the prompts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
