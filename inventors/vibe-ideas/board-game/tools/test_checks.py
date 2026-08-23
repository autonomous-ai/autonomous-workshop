#!/usr/bin/env python3
"""test_checks.py — regression fixtures for gates R1 (rules) and R2 (ergonomics),
and for what the golden blocks do to each other.

    python3 board-game/tools/test_checks.py

No CAD is built here, so this runs in a second or two; the cost is importing
`blocks`, which pulls in cadquery. Prints ALL PASS or the failures.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
# blocks.py imports cadlib.fits, and cadcode is vendored at the repo root, so
# the golden blocks are importable here without a built project around them.
sys.path.insert(0, str(REPO_ROOT / "cadcode"))
sys.path.insert(0, str(REPO_ROOT / "board-game" / "blocks"))

import blocks  # noqa: E402
from cadlib.fits import FIT_TABLE  # noqa: E402
from ergonomics_check import MIN_SEAT_CLEARANCE_MM  # noqa: E402
from ergonomics_check import check as ergo_check  # noqa: E402
from rules_check import check as rules_check  # noqa: E402


def _idea(**over) -> dict:
    idea = {
        "slug": "fixture", "title": "Fixture", "playtime_min": 30,
        "players": {"min": 2, "max": 4},
        "components": [{"name": "board", "qty": 1},
                       {"name": "token", "qty": 20, "per_player": 5}],
        "rules": {
            "setup": [{"text": "Lay out the board.", "uses": ["board"]}],
            "turn": [{"text": "Place a token.", "uses": ["token", "board"]}],
            "end": [{"text": "Ends when tokens run out.", "uses": ["token"]}],
            "win": {"text": "Most tokens placed wins.", "uses": ["token"]},
        },
    }
    idea.update(over)
    return idea


def _contract(max_rule_words: int = 100, max_action_types: int = 2) -> dict:
    return {
        "core_experience": "Make consequential spatial choices.",
        "core_mechanism": "Shared placement.",
        "must_preserve": ["Direct interaction."],
        "anti_goals": ["Scripted openings."],
        "complexity_budget": {
            "max_rule_words": max_rule_words,
            "max_action_types": max_action_types,
        },
        "kill_criteria": ["The opening remains forced after a structural change."],
    }


RULES_CASES = [
    ("clean_game", _idea(), []),
    (
        "rule_reaches_for_a_piece_that_is_not_in_the_box",
        _idea(rules={**_idea()["rules"],
                     "turn": [{"text": "Draw a stick.", "uses": ["tally_stick"]}]}),
        ["not in the component bill"],
    ),
    (
        "piece_in_the_box_that_no_rule_uses",
        _idea(components=[*_idea()["components"], {"name": "spare_dial", "qty": 1}]),
        ["no rule ever uses it"],
    ),
    (
        # "Each player takes 5" against a bill that only makes 12.
        "per_player_quantity_does_not_survive_a_full_table",
        _idea(components=[{"name": "board", "qty": 1},
                          {"name": "token", "qty": 12, "per_player": 5}]),
        ["needs 20", "only makes 12"],
    ),
    (
        "no_win_condition",
        _idea(rules={k: v for k, v in _idea()["rules"].items() if k != "win"}),
        ["rules:win: missing"],
    ),
    (
        "step_without_a_uses_list",
        _idea(rules={**_idea()["rules"], "turn": [{"text": "Do something."}]}),
        ["no `uses` list"],
    ),
    (
        "schema_v2_requires_a_design_contract",
        _idea(schema_version=2),
        ["schema_version 2 requires a design contract"],
    ),
    (
        "declared_complexity_budget_bites",
        _idea(schema_version=2, action_types=["PLACE"],
              design_contract=_contract(max_rule_words=5)),
        ["rules use", "declared maximum 5"],
    ),
    (
        "complete_design_contract_passes",
        _idea(schema_version=2, action_types=["PLACE"],
              design_contract=_contract()),
        [],
    ),
]


def _brief(**over) -> dict:
    brief = {"parts": [
        {"name": "token", "kind": "loose_piece", "bbox_mm": [20, 20, 10]},
        {"name": "board", "kind": "board", "bbox_mm": [200, 200, 6],
         "recesses": [{"holds": "token", "width_mm": 22, "depth_mm": 6, "count": 12}]},
    ]}
    brief.update(over)
    return brief


ERGO_CASES = [
    ("comfortable_game", _brief(), []),
    (
        # Turn 15, Sluice Row, verbatim: 7mm seeds on the floor of 26mm-wide,
        # 16mm-deep wells. Every geometric check passed at the time.
        "piece_sunk_out_of_finger_reach",
        {"parts": [
            {"name": "seed", "kind": "loose_piece", "bbox_mm": [20, 20, 7]},
            {"name": "board", "kind": "board", "bbox_mm": [240, 120, 16],
             "recesses": [{"holds": "seed", "width_mm": 26, "depth_mm": 16}]}]},
        ["retrieve", "below the rim"],
    ),
    (
        "piece_too_small_to_pick_up",
        {"parts": [{"name": "chip", "kind": "loose_piece", "bbox_mm": [6, 6, 2]}]},
        ["grasp"],
    ),
    (
        "press_fit_seat",
        {"parts": [
            {"name": "peg", "kind": "loose_piece", "bbox_mm": [12, 12, 20]},
            {"name": "board", "kind": "board", "bbox_mm": [200, 200, 8],
             "recesses": [{"holds": "peg", "width_mm": 12.2, "depth_mm": 6}]}]},
        ["drop in rather than press in"],
    ),
    (
        # Graduated from CAD_GRAMMAR: sub-millimetre relief keeps being
        # modelled faithfully and then being invisible.
        "relief_too_shallow_to_see",
        {"parts": [{"name": "board", "kind": "board", "bbox_mm": [200, 200, 6],
                    "relief_mm": 0.5}]},
        ["relief"],
    ),
    (
        "tall_piece_topples",
        {"parts": [{"name": "obelisk", "kind": "loose_piece",
                    "bbox_mm": [10, 10, 60], "stackable": True}]},
        ["topples"],
    ),
]


def run(label: str, fn, cases) -> list:
    failures = []
    for name, payload, needles in cases:
        findings = fn(payload)
        blob = " ".join(findings).lower()
        expect_pass = not needles
        if bool(findings) == expect_pass:
            failures.append(f"{label}/{name}: expected "
                            f"{'PASS' if expect_pass else 'FAIL'}, got {findings}")
        elif missing := [n for n in needles if n.lower() not in blob]:
            failures.append(f"{label}/{name}: verdict right but reason missing "
                            f"{missing} in {findings}")
        else:
            print(f"  ok  {label}/{name}")
    return failures


def check_no_stdlib_shadowing() -> list:
    """No tool may be named after a stdlib module.

    Python puts a script's own directory at sys.path[0], so `tools/queue.py`
    shadowed the stdlib `queue` for every script in that directory. networkx
    does `from queue import PriorityQueue`, so the whole CAD gate died with an
    ImportError that named neither the queue nor the gate. Cheap to check,
    very expensive to debug.
    """
    import sys as _sys

    stdlib = getattr(_sys, "stdlib_module_names", frozenset())
    clashes = [p.name for p in Path(__file__).resolve().parent.glob("*.py")
               if p.stem in stdlib]
    return [f"shadowing/{name}: shadows a stdlib module for every script in "
            f"this directory — rename it" for name in sorted(clashes)]


def check_graduation_checker_bites() -> list:
    """The graduation checker's own sentinel.

    A checker that cannot fail is indistinguishable from one that works, right
    up to the day something breaks and it prints ALL PASS anyway. So: one claim
    that is true, and one for each way a claim can be false, run against the
    real tree through a substituted lessons file.
    """
    import tempfile

    import graduation_check as gc

    filler = " " + "x" * 60  # lessons.md only reads lines over 40 chars
    good = "- [GRADUATED -> blocks.shared_positions]" + filler
    false_claims = [
        ("missing_symbol", "- [GRADUATED -> gate.no_such_function]" + filler),
        ("unknown_module", "- [GRADUATED -> nowhere.MIN_RELIEF_MM]" + filler),
        ("absent_literal", '- [GRADUATED -> gate:"no-such-lint-rule"]' + filler),
        ("prose_not_target", "- [GRADUATED -> gate.py lint]" + filler),
    ]

    findings = []
    original = gc.LESSONS
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "lessons.md"
        try:
            gc.LESSONS = path
            path.write_text(good + "\n", encoding="utf-8")
            broken, checked, _ = gc.verify()
            if broken or checked != 1:
                findings.append(f"graduation/landed_claim: a graduation that IS in "
                                f"the tree was reported broken ({broken})")
            for label, line in false_claims:
                path.write_text(line + "\n", encoding="utf-8")
                broken, _, _ = gc.verify()
                if not broken:
                    findings.append(f"graduation/{label}: a false claim passed — "
                                    f"the checker is blind to this kind of rot")
        finally:
            gc.LESSONS = original
    return findings


# --- composition: what the golden blocks do to each other --------------------
#
# testbench.py builds each block on its own, and a brief may legally ask for two
# of them at once. The defects that live only in the composition are invisible
# to a fixture that exercises one block, and — as `compose_tiled_wells` records
# — sometimes invisible to the gate as well. Two things live here: the
# arithmetic cases, and the claim that the table naming them is COMPLETE, so a
# sixth block cannot be added without saying where it composes.


def compose_wells(piece_mm: float, pitch: float, depth: float, board_t: float,
                  *, fit: str = "free", well_d: float | None = None) -> list:
    """seated_pair -> shared_positions -> cut_wells, and what breaks.

    Findings in the shape rules_check and ergonomics_check return them, derived
    from the library's own numbers rather than from numbers restated here.
    """
    piece_d, seat_d = blocks.seated_pair(piece_mm, fit)
    well_d = seat_d if well_d is None else well_d
    findings = []
    if abs(well_d - seat_d) > 1e-9:
        findings.append(
            f"seat: the well is {well_d}mm while seated_pair derives {seat_d}mm "
            f"from a {piece_d}mm piece — two numbers that should be one, which "
            f"is the drift seated_pair exists to stop")
    # cut_wells puts a FINGER_NOTCH_MM scallop centred at x + well_d/2, so it
    # reaches well_d/2 + FINGER_NOTCH_MM/2 past the seat centre, while the next
    # seat's rim starts at pitch - well_d/2.
    reach = well_d / 2.0 + blocks.FINGER_NOTCH_MM / 2.0
    rim = pitch - well_d / 2.0
    if reach > rim:
        findings.append(
            f"pitch: at {pitch}mm the finger notch reaches {reach:.1f}mm from "
            f"the seat centre, past the {rim:.1f}mm where the next seat's rim "
            f"starts — the seats merge into one trough and neither holds a piece")
    if depth >= board_t:
        findings.append(
            f"depth: a {depth}mm well in a {board_t}mm board is a hole, not a "
            f"well — nothing is left under the piece to hold it up")
    return findings


def compose_tiled_wells(width: float, depth: float, thickness: float,
                        cols: int, rows: int, pitch: float,
                        well_d: float) -> list:
    """tiled_board -> cut_wells: seats against the seams they cannot see.

    tiled_board takes board dimensions only, so it splits where the bed says and
    never where the seats are. A seat centred on a seam is cut in half, and both
    halves are ordinary manifold geometry: verified 2026-08-17 on a 500x300
    board with `shared_positions(4, 3, 100)`, whose whole middle row lands on
    the y seam. It returns GATE PASS with an empty `fails`. There is no
    measurement downstream of this that catches it, so arithmetic here is the
    only place it can be caught at all.
    """
    tiles = blocks.tiled_board(width, depth, thickness)
    centres = (sorted({t["x"] for t in tiles}), sorted({t["y"] for t in tiles}))
    findings = []
    for x, y, _ in blocks.shared_positions(cols, rows, pitch):
        for axis, value, line in (("x", x, centres[0]), ("y", y, centres[1])):
            seams = [(a + b) / 2.0 for a, b in zip(line, line[1:])]
            for seam in seams:
                if abs(value - seam) < well_d / 2.0:
                    findings.append(
                        f"seam: the seat at {axis}={value:.1f} is within "
                        f"{well_d / 2.0:.1f}mm of the tile seam at {seam:.1f}, so "
                        f"the well is cut in half — and each half prints clean, "
                        f"which is why the gate will not say so")
    return findings


def compose_tiled_pieces(width: float, depth: float, thickness: float,
                         cols: int, rows: int, pitch: float) -> list:
    """tiled_board -> add_piece_family: pieces placed off the board entirely.

    shared_positions centres its grid on the origin and knows nothing about the
    board it is for, so `cols * pitch` wider than the board puts named assembly
    children in mid-air beside it. gate.py counts those children and finds the
    bill satisfied, because a piece floating next to the board is still a piece.
    """
    tiles = blocks.tiled_board(width, depth, thickness)
    findings = []
    for x, y, _ in blocks.shared_positions(cols, rows, pitch):
        if not any(abs(x - t["x"]) <= t["w"] / 2.0 and abs(y - t["y"]) <= t["d"] / 2.0
                   for t in tiles):
            findings.append(
                f"origin: the seat at ({x:.1f}, {y:.1f}) falls on no tile of a "
                f"{width:.0f}x{depth:.0f} board — shared_positions sizes its "
                f"grid from cols and pitch alone and never sees the board")
    return findings


#: The seat a 20mm piece gets, from the library rather than from this file. The
#: cases below need the number, and writing 20.8 here would be the very drift
#: `seat_stated_instead_of_derived` exists to catch.
SEAT_20 = blocks.seated_pair(20.0)[1]

COMPOSITION_CASES = [
    ("wells_that_compose",
     lambda: compose_wells(20.0, pitch=40.0, depth=5.0, board_t=8.0), []),
    ("seat_stated_instead_of_derived",
     # 26.0 is what testbench's WELLS fixture stated for a 20mm token until this
     # went in: 3.0mm per side, against the 0.40mm the library hands out.
     lambda: compose_wells(20.0, pitch=40.0, depth=5.0, board_t=8.0, well_d=26.0),
     ["two numbers that should be one"]),
    ("notch_merges_into_the_next_seat",
     lambda: compose_wells(20.0, pitch=24.0, depth=5.0, board_t=8.0),
     ["merge into one trough"]),
    ("well_deeper_than_the_board_is_a_hole",
     lambda: compose_wells(20.0, pitch=40.0, depth=8.0, board_t=8.0),
     ["hole, not a"]),
    # 4x2 at 100mm clears every seam of a 500x300 board; 4x3 puts the whole
    # middle row on the y seam. The two are one pitch apart in the brief.
    ("seats_clear_of_every_tile_seam",
     lambda: compose_tiled_wells(500.0, 300.0, 8.0, 4, 2, 100.0, SEAT_20), []),
    ("tile_seam_cuts_a_seat_in_half",
     lambda: compose_tiled_wells(500.0, 300.0, 8.0, 4, 3, 100.0, SEAT_20),
     ["tile seam", "the gate will not say so"]),
    ("grid_that_fits_the_board",
     lambda: compose_tiled_pieces(500.0, 300.0, 8.0, 4, 3, 100.0), []),
    ("grid_wider_than_the_board_it_is_for",
     lambda: compose_tiled_pieces(500.0, 300.0, 8.0, 4, 3, 200.0),
     ["falls on no tile"]),
]

#: Every ordered pair of golden blocks, as "the output of A is fed to B".
#: `covered` the pairing is pinned. The detail lists what pins it, comma
#:           separated: `case:<COMPOSITION_CASES entry>` for the arithmetic
#:           here, `fixture:<testbench.CASES entry>` for one built for real.
#:           A pairing may have both, and the ones that matter do.
#: `n/a`     the signatures make the pairing impossible; the reason says why.
#: `broken`  legal, reachable, and nothing makes it come out right yet. Carried
#:           as debt and reported AMBER by audit.py, never silently.
#: A pair in none of these fails, so adding a block forces the question rather
#: than letting it be answered by nobody.
COMPOSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("add_piece_family", "cut_wells"):
        ("n/a", "add_piece_family returns an Assembly; cut_wells takes a board"),
    ("add_piece_family", "seated_pair"):
        ("n/a", "seated_pair takes one nominal length, not an assembly"),
    ("add_piece_family", "shared_positions"):
        ("n/a", "shared_positions takes cols/rows/pitch, not an assembly"),
    ("add_piece_family", "tiled_board"):
        ("n/a", "tiled_board takes board dimensions, not an assembly"),
    ("cut_wells", "add_piece_family"):
        ("covered", "fixture:cut_wells"),
    ("cut_wells", "seated_pair"):
        ("n/a", "the live direction is seated_pair -> cut_wells; a cut board is "
                "not a nominal length"),
    ("cut_wells", "shared_positions"):
        ("n/a", "shared_positions takes cols/rows/pitch, not a board"),
    ("cut_wells", "tiled_board"):
        ("n/a", "tiled_board takes scalars, so it cannot be handed a board that "
                "already has wells in it — the same blindness recorded against "
                "(tiled_board, cut_wells), reached from the other side"),
    ("seated_pair", "add_piece_family"):
        ("covered", "case:wells_that_compose, fixture:tiled_wells"),
    ("seated_pair", "cut_wells"):
        ("covered", "case:seat_stated_instead_of_derived, fixture:tiled_wells"),
    ("seated_pair", "shared_positions"):
        ("covered", "case:notch_merges_into_the_next_seat"),
    ("seated_pair", "tiled_board"):
        ("n/a", "tiled_board is sized by the board, never by a piece"),
    ("shared_positions", "add_piece_family"):
        ("covered", "fixture:add_piece_family"),
    ("shared_positions", "cut_wells"):
        ("covered", "fixture:cut_wells"),
    ("shared_positions", "seated_pair"):
        ("n/a", "seated_pair takes one nominal length, not a position list"),
    ("shared_positions", "tiled_board"):
        ("broken", "tiled_board cannot be told where the seats are, so it splits "
                   "through them; handing it the position list and letting it "
                   "move a seam is the block-tier fix, and it is not written"),
    ("tiled_board", "add_piece_family"):
        ("covered", "case:grid_wider_than_the_board_it_is_for, "
                    "fixture:tiled_wells"),
    ("tiled_board", "cut_wells"):
        ("covered", "case:tile_seam_cuts_a_seat_in_half, fixture:tiled_wells"),
    ("tiled_board", "seated_pair"):
        ("n/a", "seated_pair takes one nominal length, not a tile descriptor"),
    ("tiled_board", "shared_positions"):
        ("n/a", "shared_positions takes cols/rows/pitch, not tile descriptors"),
}

KINDS = ("covered", "n/a", "broken")
#: Short enough to be a shrug rather than a reason. Same floor the ship refusal
#: puts on --accept-unmeasured: the cost is spendable, but only out loud.
MIN_REASON_CHARS = 30


def _golden_blocks() -> list:
    """The public callables blocks.py itself defines.

    `__module__` filters out peg_for/slot_for, which blocks.py imports from
    cadlib and does not own; a re-export is not a golden block.
    """
    return sorted(name for name, obj in vars(blocks).items()
                  if inspect.isfunction(obj)
                  and obj.__module__ == "blocks"
                  and not name.startswith("_"))


def check_composition_closure() -> list:
    """The table above, held to blocks.py and to the fixtures it names.

    This is the part that makes the section a closure claim rather than a pile
    of tests. Coverage is a claim like any other, so a pair naming a fixture or
    a case that does not exist fails exactly as loudly as an unnamed pair.
    """
    import testbench

    names = _golden_blocks()
    legal = {(a, b) for a in names for b in names if a != b}
    cases = {name for name, _, _ in COMPOSITION_CASES}
    fixtures = {case[0] for case in testbench.CASES}

    findings = []
    for pair in sorted(legal - set(COMPOSITIONS)):
        findings.append(
            f"closure/{pair[0]}->{pair[1]}: a legal composition nothing accounts "
            f"for — pin it with a case or a fixture, or declare it n/a or broken "
            f"with a reason. An untested composition is not the same as one that "
            f"works")
    for pair in sorted(set(COMPOSITIONS) - legal):
        findings.append(
            f"closure/{pair[0]}->{pair[1]}: the table names a pair blocks.py no "
            f"longer has — a stale entry is a covered-looking hole")
    known = {"case": cases, "fixture": fixtures}
    for pair, (kind, detail) in sorted(COMPOSITIONS.items()):
        where = f"closure/{pair[0]}->{pair[1]}"
        if kind not in KINDS:
            findings.append(f"{where}: unknown kind {kind!r}, expected one of "
                            f"{', '.join(KINDS)}")
        elif kind == "covered":
            for ref in (r.strip() for r in detail.split(",")):
                tier, _, name = ref.partition(":")
                if tier not in known:
                    findings.append(f"{where}: {ref!r} is not a case: or "
                                    f"fixture: reference")
                elif name not in known[tier]:
                    findings.append(f"{where}: names {tier} {name!r}, which does "
                                    f"not exist")
        elif len(detail) < MIN_REASON_CHARS:
            findings.append(f"{where}: {kind!r} needs a reason of at least "
                            f"{MIN_REASON_CHARS} characters, got {detail!r}")
    return findings


def check_closure_checker_bites() -> list:
    """The closure check's own sentinel.

    The same argument as check_graduation_checker_bites: a table that is never
    seen to fail is indistinguishable from a table that covers everything. This
    one matters more, because the closure check is the only thing standing
    between "20 compositions accounted for" and "20 lines someone typed".
    """
    global COMPOSITIONS

    original = dict(COMPOSITIONS)
    victim = next(iter(original))
    long_enough = "a reason comfortably past the minimum length"
    broken_tables = [
        ("undeclared_pair", {k: v for k, v in original.items() if k != victim}),
        ("stale_pair", {**original,
                        ("cut_wells", "deleted_block"): ("n/a", long_enough)}),
        ("missing_case", {**original, victim: ("covered", "case:no_such_case")}),
        ("missing_fixture", {**original,
                             victim: ("covered", "fixture:no_such_fixture")}),
        ("unlabelled_ref", {**original, victim: ("covered", "wells_that_compose")}),
        ("shrug_for_a_reason", {**original, victim: ("n/a", "obviously")}),
        ("unknown_kind", {**original, victim: ("todo", long_enough)}),
    ]

    findings = []
    try:
        for label, table in broken_tables:
            COMPOSITIONS = table
            if not check_composition_closure():
                findings.append(
                    f"closure/{label}: a table with this hole in it was reported "
                    f"complete — the closure claim is decorative")
    finally:
        COMPOSITIONS = original
    return findings


def check_seated_pair_agrees_with_r2() -> list:
    """The one number seated_pair and ergonomics_check are supposed to share.

    seated_pair's docstring says its `free` fit is the same 0.40mm as
    ergonomics_check.MIN_SEAT_CLEARANCE_MM — "one number, two places that must
    not disagree" — and nothing has ever checked that they still do. Two-sided,
    so it stays honest in both directions: the default fit must clear R2, and
    the next class tighter must not, or R2 has stopped biting and the first half
    proves nothing.
    """
    findings = []
    if FIT_TABLE["free"] != MIN_SEAT_CLEARANCE_MM:
        findings.append(
            f"seated_pair/one_number: the free fit is {FIT_TABLE['free']}mm per "
            f"side while R2 requires {MIN_SEAT_CLEARANCE_MM}mm — the two numbers "
            f"seated_pair promises are one have drifted apart")

    def seat_brief(fit: str) -> dict:
        piece_d, seat_d = blocks.seated_pair(20.0, fit)
        return {"parts": [
            {"name": "token", "kind": "loose_piece", "bbox_mm": [piece_d, piece_d, 10]},
            {"name": "board", "kind": "board", "bbox_mm": [200, 200, 8],
             "recesses": [{"holds": "token", "width_mm": seat_d, "depth_mm": 5}]}]}

    default = inspect.signature(blocks.seated_pair).parameters["fit"].default
    if ergo_check(seat_brief(default)):
        findings.append(
            f"seated_pair/default: the {default!r} fit it hands out by default "
            f"builds a seat R2 rejects, so every seat derived from the block is "
            f"a repair round")
    if not ergo_check(seat_brief("slip")):
        findings.append(
            "seated_pair/sentinel: R2 accepted a 0.20mm-per-side seat, so the "
            "check above passes for no reason — MIN_SEAT_CLEARANCE_MM has been "
            "loosened or the recess check has stopped reading widths")
    return findings


def check_fix_tier_ladder_bites() -> list:
    """The tier ladder's own sentinel.

    The ladder is only worth anything if it reads a weak graduation as weak.
    Two ways it could go quietly wrong: scoring a lesson by its worst target
    instead of its best (so pairing a block with a gate check would look like
    a check), and accepting any ceiling clause at all (so `| ceiling: no` would
    buy silence forever).
    """
    import tempfile

    import graduation_check as gc

    filler = " " + "x" * 60
    long_reason = "the print bed is a fixed physical size and no upstream tier can change it"
    cases = [
        # (label, marker body, expected tier or None if it must be rejected,
        #  expected ceiling truthiness)
        ("check_only", 'gate:"blanket-fillet"', "check", False),
        ("best_of_several", "gate.check_bill, blocks.add_piece_family",
         "block", False),
        ("ceiling_accepted", f'gate:"blanket-fillet" | ceiling: {long_reason}',
         "check", True),
        ("ceiling_too_short", 'gate:"blanket-fillet" | ceiling: n/a', None, False),
        ("ceiling_malformed", 'gate:"blanket-fillet" | because reasons', None, False),
    ]

    findings = []
    original = gc.LESSONS
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "lessons.md"
        try:
            gc.LESSONS = path
            for label, body, tier, has_ceiling in cases:
                path.write_text(f"- [GRADUATED -> {body}]{filler}\n", encoding="utf-8")
                good, broken, _ = gc.scan()
                if tier is None:
                    if not broken:
                        findings.append(f"fix-tier/{label}: a ceiling clause that "
                                        f"says nothing was accepted — the escape "
                                        f"valve is free")
                    continue
                if broken or len(good) != 1:
                    findings.append(f"fix-tier/{label}: expected one graduation, "
                                    f"got {len(good)} and {broken}")
                    continue
                entry = good[0]
                if entry["tier"] != tier:
                    findings.append(f"fix-tier/{label}: scored {entry['tier']}, "
                                    f"expected {tier}")
                if bool(entry["ceiling"]) != has_ceiling:
                    findings.append(f"fix-tier/{label}: ceiling was "
                                    f"{entry['ceiling']!r}")
        finally:
            gc.LESSONS = original

    untiered = sorted(set(gc.MODULES) - set(gc.TIERS))
    if untiered:
        findings.append(f"fix-tier/every_module_has_a_tier: {untiered} can be "
                        f"graduated into but has no tier, so audit.py cannot "
                        f"say how far upstream it is")
    return findings


def main() -> int:
    failures = run("rules", rules_check, RULES_CASES)
    failures += run("ergo", ergo_check, ERGO_CASES)
    failures += run("composition", lambda thunk: thunk(), COMPOSITION_CASES)

    # These assert against the tree rather than against a fixture, so they have
    # no case list to be counted from. They used to run without being counted at
    # all, which made the printed total quietly smaller than the number of
    # things that could fail.
    standalone = [
        ("tools/no_stdlib_shadowing", check_no_stdlib_shadowing),
        ("tools/graduation_checker_bites", check_graduation_checker_bites),
        ("tools/fix_tier_ladder_bites", check_fix_tier_ladder_bites),
        ("blocks/composition_closure", check_composition_closure),
        ("blocks/closure_checker_bites", check_closure_checker_bites),
        ("blocks/seated_pair_agrees_with_r2", check_seated_pair_agrees_with_r2),
    ]
    for label, check in standalone:
        found = check()
        failures += found
        if not found:
            print(f"  ok  {label}")


    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  -", f)
        return 1
    total = (len(RULES_CASES) + len(ERGO_CASES) + len(COMPOSITION_CASES)
             + len(standalone))
    carried = sorted(p for p, e in COMPOSITIONS.items() if e[0] == "broken")
    print(f"\nALL PASS ({total} cases, {len(COMPOSITIONS)} block compositions "
          f"accounted for, {len(carried)} carried as broken)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
