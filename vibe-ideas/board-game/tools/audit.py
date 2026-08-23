#!/usr/bin/env python3
"""audit.py — what the pipeline could still do to itself, now that it has no
score to inflate.

    python3 board-game/tools/audit.py
    python3 board-game/tools/audit.py --baseline    # re-record the thresholds

The old audit had ten checks. Seven of them existed because a remote service
produced the artifacts and a rubric produced a number, so provenance and
score-consistency had to be proven. Neither is true any more: builds happen
here, git records who changed what, and nothing is scored. Keeping those
checks would have been theatre.

Eight risks survive the change, and four of them are new. The last four share
one blind spot, which a checker that only asks whether a fix EXISTS cannot
see: a fix can be real, verified, and still not doing the work.

1. GATE EROSION (new, and the important one). With acceptance reduced to a
   deterministic gate, the cheapest way to make everything pass is to move
   the gate. This compares the live thresholds against a recorded baseline
   and flags any LOOSENING — direction matters, so tightening is silent.
2. SHIPPED WITHOUT MEASUREMENT. Nothing may reach `shipped` without a
   `gate.json` that actually passed. This is the one invariant the whole
   rebuild rests on. A gate that passed while a check reached no verdict
   counts here too: `unmeasured` may be spent, but only by a human, and only
   with a reason on the record.
3. DEGENERACY. Optimising for pass rate rewards proposing simpler games. If
   part families, piece counts, and relief depths drift down over time, the
   loop is getting better at the metric rather than at board games.
4. PROMPT BLOAT. Agents that rewrite their own instructions grow them without
   limit; a Learned Heuristics section that doubles is one nobody reads.
5. GRADUATION ROT (new). A lesson that becomes code leaves the build prompts.
   If the code it became is later deleted, the lesson is neither enforced nor
   remembered, and lessons.md goes on claiming otherwise. Delegated to
   graduation_check.py, which holds every marker to the tree.
6. FIX TIER (new). A marker can be entirely true and still weak. `gate.py`
   really does catch the blanket fillet, and every build still writes it,
   still fails, and still spends a repair round undoing it. Nothing is lying;
   the pipeline just pays that cost forever, because the fix landed at the
   layer that detects rather than the layer that prevents. A check is a smoke
   alarm: it works, and the house burns on schedule. AMBER, never RED — check
   is sometimes the only honest tier, and the marker can say so with a
   `| ceiling:` clause. Also flags a block nothing calls.
7. A GRADUATION THAT DOES NOT REACH THE BUILD (new). `blocks.py` is COPIED
   into each project, not imported, so a fix landed in the canonical file
   reaches only builds that take a fresh copy. An in-flight project holding a
   stale or hand-edited copy is running without the graduation while
   graduation_check.py reads canonical and reports green. Shipped projects are
   left alone: their files are the record of what was printed.
8. COMPOSITION DEBT (new). The same question asked of the blocks themselves.
   They are tested one at a time, and a brief may legally ask for two at once.
   test_checks.py fails outright on a composition nobody has accounted for,
   because answering that costs one line. It cannot fail on one accounted for
   as BROKEN: paying that debt means changing geometry in blocks/, which is
   human-approved and PR-only. So the debt is carried here, where it stays in
   view and can only shrink.

Exit 0 green, 1 amber, 2 red.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "board-game" / "tools"
AGENTS = REPO_ROOT / ".claude" / "agents"
IDEAS = REPO_ROOT / "board-game" / "ideas"
QUEUE = REPO_ROOT / "board-game" / "QUEUE.json"
BASELINE = TOOLS / "thresholds_baseline.json"
BLOCKS = REPO_ROOT / "board-game" / "blocks" / "blocks.py"
#: Where a build keeps its own copy of blocks.py. `draft` counts: a draft that
#: predates a graduation is what the owner approves the shape from.
BUILD_DIRS = ("project", "draft")

GREEN, AMBER, RED = "GREEN", "AMBER", "RED"

# Which direction is a loosening for each threshold. "up" means raising the
# number makes the gate easier to pass.
LOOSER = {
    "BED_X_MM": "up", "BED_Y_MM": "up", "BED_Z_MM": "up",
    "BED_MARGIN_MM": "down",
    "OVERHANG_FAIL_PCT": "up", "BRIDGE_SPAN_MAX_MM": "up",
    "MIN_BODY_VOLUME_MM3": "up",
    "MIN_GRASP_MM": "down", "MIN_PROTRUSION_MM": "down",
    "FINGER_ROOM_MM": "down", "MIN_SEAT_CLEARANCE_MM": "down",
    "MAX_STACK_ASPECT": "up", "MIN_RELIEF_MM": "down",
    "REPAIR_BUDGET": "up",
}

HEURISTICS_WORD_CAP = 1200


def live_thresholds() -> dict:
    sys.path.insert(0, str(TOOLS))
    import ergonomics_check
    import gate
    import pipeline_queue as queue_mod

    values = {}
    for module in (gate, ergonomics_check, queue_mod):
        for name in LOOSER:
            if hasattr(module, name):
                values[name] = getattr(module, name)
    return values


def check_gate_erosion(findings: list) -> None:
    live = live_thresholds()
    if not BASELINE.is_file():
        findings.append((AMBER, "erosion", "no threshold baseline recorded — run "
                                           "--baseline once so drift becomes visible"))
        return
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    for name, value in sorted(live.items()):
        if name not in base:
            findings.append((AMBER, "erosion", f"{name} is new since the baseline"))
            continue
        was, direction = base[name], LOOSER[name]
        if (direction == "up" and value > was) or (direction == "down" and value < was):
            findings.append((RED, "erosion",
                             f"{name} moved {was} -> {value}, which makes the gate "
                             f"EASIER to pass. A threshold may only be loosened by a "
                             f"human through a PR, with a reason"))
        elif value != was:
            print(f"  note: {name} tightened {was} -> {value}")


def check_shipped_were_measured(findings: list) -> None:
    if not QUEUE.is_file():
        return
    sys.path.insert(0, str(TOOLS))
    import pipeline_queue  # one owner of "what did the gate fail to measure"

    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    for slug, item in sorted(data.get("ideas", {}).items()):
        if item.get("state") != "shipped":
            continue
        report = IDEAS / slug / "project" / "gate.json"
        if not report.is_file():
            findings.append((RED, "unmeasured",
                             f"{slug} is shipped with no gate.json at all"))
            continue
        gate_report = json.loads(report.read_text(encoding="utf-8"))
        if not gate_report.get("pass"):
            findings.append((RED, "unmeasured",
                             f"{slug} is shipped but its gate.json says it failed"))
        # A pass with something it could not measure is a different object from
        # a clean pass, and `pipeline_queue.py ship` will not take one without
        # a stated acceptance. This is the check that the refusal was not gone
        # around — by an edit to QUEUE.json, or by a re-run of the gate after
        # the ship that quietly turned a clean pass into an incomplete one.
        skipped = pipeline_queue.gate_unmeasured(slug)
        if skipped and not item.get("unmeasured_accepted"):
            findings.append((RED, "unmeasured",
                             f"{slug} is shipped with {len(skipped)} gate check(s) "
                             f"that never reached a verdict and no recorded "
                             f"acceptance — first: {skipped[0]}"))


def check_graduations(findings: list) -> None:
    """Every `[GRADUATED -> ...]` marker in lessons.md, held to the tree.

    Graduating a lesson is what takes it OUT of the build prompts, so a marker
    whose code has since been deleted leaves the lesson neither enforced nor
    remembered. That is the worst of the three states an insight can be in, and
    the only one that is invisible without asking.
    """
    sys.path.insert(0, str(TOOLS))
    import graduation_check

    broken, checked, prose = graduation_check.verify()
    for entry in broken:
        findings.append((RED, "graduation", entry))
    if not broken:
        print(f"  note: {checked} graduation(s) verified, {prose} lesson(s) "
              f"still prose")


def _idea_dirs() -> list[Path]:
    if not IDEAS.is_dir():
        return []
    return sorted(p for p in IDEAS.iterdir() if p.is_dir())


def _queue_states() -> dict[str, str]:
    if not QUEUE.is_file():
        return {}
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    return {slug: item.get("state", "")
            for slug, item in data.get("ideas", {}).items()}


def _block_callers(symbol: str) -> list[str]:
    """Ideas whose build code actually reaches for a block helper.

    The copied blocks.py is skipped: it defines the symbol inside every
    project whether or not one line of that project ever calls it, so counting
    it would make every block look universally adopted.
    """
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    callers = set()
    for idea in _idea_dirs():
        for sub in BUILD_DIRS:
            for path in (idea / sub).glob("**/*.py"):
                if path.name == "blocks.py":
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if pattern.search(text):
                    callers.add(idea.name)
    return sorted(callers)


def check_fix_tier(findings: list) -> None:
    """Not whether a graduation is real — check_graduations answers that — but
    how far upstream it got, and whether anything downstream uses it.

    Both findings here are AMBER on purpose. A check-tier fix is sometimes the
    only honest one, and a rule that forced an upstream landing would buy
    fake planner constraints written to clear an audit. What the pipeline
    cannot afford is the question going unasked.
    """
    sys.path.insert(0, str(TOOLS))
    import graduation_check

    good, broken, _ = graduation_check.scan()
    if broken:
        return  # check_graduations owns those; do not stack a second finding
    mine: list[tuple[str, str, str]] = []
    tally: dict[str, int] = {}
    for entry in good:
        tally[entry["tier"]] = tally.get(entry["tier"], 0) + 1
        where = ", ".join(t["text"] for t in entry["targets"])
        if entry["rank"] == graduation_check.CHECK_TIER and not entry["ceiling"]:
            mine.append((AMBER, "fix-tier",
                         f'"{entry["lesson"]}…" landed check-only, in {where}. '
                         f'The gate catches it, which means every build still '
                         f'writes it and still spends a repair round undoing '
                         f'it. Land it in blocks.py (right by construction) or '
                         f'the brief-writer template (never designed in), or '
                         f'add `| ceiling: <why nothing upstream can catch '
                         f'this>` to the marker'))
        for target in entry["targets"]:
            if target["module"] != "blocks" or not target["symbol"]:
                continue
            if not _block_callers(target["symbol"]):
                mine.append((AMBER, "fix-tier",
                             f'{target["text"]} is a block-tier graduation no '
                             f'build calls. A block prevents the defect only '
                             f'in the builds that reach for it, so this one '
                             f'currently prevents nothing'))
    findings.extend(mine)
    if good:
        # Printed even when there are findings: the findings are the numerator
        # and this is the denominator, and reading one without the other is how
        # two amber lines get mistaken for a pipeline in trouble.
        ladder = ", ".join(f"{n} {tier}" for tier, n in sorted(tally.items()))
        print(f"  note: graduations by tier: {ladder}")


def check_block_copies(findings: list) -> None:
    """blocks.py is copied into each build, so a graduation is only landed for
    the builds holding a current copy.

    Shipped ideas are exempt and must stay exempt: their files are the record
    of what was actually printed, and rewriting them to match a later fix
    would falsify that record. This is also why the finding lives here and not
    in graduation_check.py — as a hard failure it would deadlock `improve.py`,
    which lands a fix in canonical blocks.py and is forbidden from touching
    board-game/ideas/ to bring the copies along.
    """
    if not BLOCKS.is_file():
        findings.append((RED, "block-reach",
                         f"{BLOCKS.name} is missing — every build copies it"))
        return
    canonical = BLOCKS.read_bytes()
    states = _queue_states()
    for idea in _idea_dirs():
        if states.get(idea.name) == "shipped":
            continue
        for sub in BUILD_DIRS:
            copy = idea / sub / "blocks.py"
            if not copy.is_file() or copy.read_bytes() == canonical:
                continue
            findings.append((AMBER, "block-reach",
                             f"{idea.name}/{sub}/blocks.py differs from "
                             f"board-game/blocks/blocks.py — that build is not "
                             f"getting whatever has graduated into the block "
                             f"library since it was copied. Re-copy it before "
                             f"the next build step, or if the difference is a "
                             f"local edit, land it in the library instead"))


def check_composition_debt(findings: list) -> None:
    """Block pairings that are legal, reachable, and not right yet.

    The tier ladder above asks how far upstream a fix landed. This asks the
    neighbouring question about the blocks themselves: two of them that have
    never been run together are untested space a brief can reach.

    The seam case is the one to keep in mind while reading these. A seat cut in
    half by a tile boundary prints clean on both sides and returns GATE PASS, so
    the debt is not something a build will ever surface. If it stops being
    printed here it stops existing anywhere.
    """
    sys.path.insert(0, str(TOOLS))
    import test_checks

    carried = [(pair, reason)
               for pair, (kind, reason) in sorted(test_checks.COMPOSITIONS.items())
               if kind == "broken"]
    for (producer, consumer), reason in carried:
        findings.append((AMBER, "composition", f"{producer} -> {consumer}: {reason}"))
    if not carried:
        print(f"  note: {len(test_checks.COMPOSITIONS)} block compositions "
              f"accounted for, none carried as broken")


def _complexity(idea: dict) -> dict:
    components = idea.get("components") or []
    return {
        "families": len(components),
        "pieces": sum(int(c.get("qty", 0)) for c in components),
    }


def check_degeneracy(findings: list) -> None:
    """Compare the newest third of proposals against the oldest third. Not a
    strict rule — designs vary — but a sustained shrink in both families and
    piece count while the gate keeps passing is the signature of a loop
    learning to win rather than to design."""
    ideas = []
    for path in sorted(IDEAS.glob("*/idea.json")):
        try:
            ideas.append(_complexity(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    if len(ideas) < 6:
        return
    third = max(2, len(ideas) // 3)
    old, new = ideas[:third], ideas[-third:]
    for key in ("families", "pieces"):
        was = sum(i[key] for i in old) / len(old)
        now = sum(i[key] for i in new) / len(new)
        if was and now < was * 0.6:
            findings.append((AMBER, "degeneracy",
                             f"average {key} per idea fell {was:.1f} -> {now:.1f} "
                             f"across the queue's history — check that the ideator "
                             f"is not simply proposing easier builds"))


def check_prompt_bloat(findings: list) -> None:
    for path in sorted(AGENTS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"#+\s*Learned Heuristics(.*)$", text,
                          re.S | re.I)
        if not match:
            continue
        words = len(match.group(1).split())
        if words > HEURISTICS_WORD_CAP:
            findings.append((AMBER, "bloat",
                             f"{path.name}: Learned Heuristics is {words} words "
                             f"(cap {HEURISTICS_WORD_CAP}) — an agent that keeps "
                             f"appending eventually reads none of it"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--baseline", action="store_true",
                    help="record the current thresholds as the baseline")
    args = ap.parse_args()

    if args.baseline:
        values = live_thresholds()
        BASELINE.write_text(json.dumps(values, indent=2, sort_keys=True),
                            encoding="utf-8")
        print(f"recorded {len(values)} thresholds to {BASELINE.name}")
        return 0

    findings: list[tuple[str, str, str]] = []
    check_gate_erosion(findings)
    check_shipped_were_measured(findings)
    check_graduations(findings)
    check_fix_tier(findings)
    check_block_copies(findings)
    check_composition_debt(findings)
    check_degeneracy(findings)
    check_prompt_bloat(findings)

    if not findings:
        print("AUDIT GREEN")
        return 0
    level = RED if any(f[0] == RED for f in findings) else AMBER
    print(f"AUDIT {level}")
    for lvl, check, detail in findings:
        print(f"  [{lvl}] {check}: {detail}")
    return 2 if level == RED else 1


if __name__ == "__main__":
    sys.exit(main())
