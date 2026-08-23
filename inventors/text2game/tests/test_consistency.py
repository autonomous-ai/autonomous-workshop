#!/usr/bin/env python3
"""Fixtures for consistency.py - the checks must FAIL the documents an agent
actually produces, not just pass a clean one. Every case below is a mistake
text2cad's agents made in some form.

    python3 tests/test_consistency.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import consistency  # noqa: E402

GOOD_GDD = """# G

## Overview
Keepers pass one lamp down a line.

## First minute
Wind your dial, sweep the beam, save ships. On turn 1: turn `winder_dial` 3
clicks, then rotate `beam_disc` toward the nearest ship.

## Components
- `beam_disc` x1 - the sweeping beam with snap-off facet tabs
- `winder_dial` x4 - per-keeper spring tension

## Setup
Place `beam_disc` on the tower and give each keeper a `winder_dial`.

## Turn structure
1. Wind: turn `winder_dial` up to 3 clicks.
2. Sweep: rotate `beam_disc` 60 degrees per click spent.

## Action economy
Each keeper spends 3 clicks per turn on `winder_dial`; each click buys 60
degrees of `beam_disc` rotation.

## Win/lose
Save 6 ships before the 12th dawn tick. Losing 3 ships ends the game.

## Legacy
Snapping a tab off `beam_disc` removes 60 degrees of reach permanently.

## Edge cases
On a tie the keeper holding the lamp wins.

## Glossary
Sweep: one rotation of `beam_disc`.
"""

GOOD_COMPS = [
    {"id": "beam_disc", "qty": 1, "role": "sweeps the beam", "class": "functional",
     "duty": "tab snaps at hand force and cannot reseat", "tolerance_mm": 0.3,
     "target_bbox_mm": [120, 120, 8], "mates_with": ["winder_dial"],
     "stores_in": "self", "rules_carrier": True, "signature": True},
    {"id": "winder_dial", "qty": 4, "role": "stores spring tension", "class": "functional",
     "duty": "holds 2N reverse torque without slipping", "tolerance_mm": 0.2,
     "target_bbox_mm": [30, 30, 12], "mates_with": ["beam_disc"],
     "stores_in": "beam_disc"},
]

# The baseline was ["snap_off_tab", "ratchet_dial"] until 2026-08-19: two
# permanent-change ids, no interaction, so the reference "clean" document was
# itself an example of the solitaire failure this suite now checks for.
GOOD_MECH = {"chosen": ["snap_off_tab", "hand_off"],
             "interaction": "the keeper holding the lamp is the only one who may "
                            "act, and acting snaps a tab off it for everyone.",
             "notes": ""}


def write(d: Path, gdd=GOOD_GDD, comps=None, mech=None):
    (d / "gdd.md").write_text(gdd, encoding="utf-8")
    (d / "components.json").write_text(
        json.dumps(GOOD_COMPS if comps is None else comps), encoding="utf-8")
    (d / "mechanisms.json").write_text(
        json.dumps(GOOD_MECH if mech is None else mech), encoding="utf-8")


def codes(d: Path) -> set:
    return {i["code"] for i in consistency.check(d, HERE)}


def case(name, expect_code=None, expect_clean=False, **kw):
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        write(d, **kw)
        got = codes(d)
        if expect_clean:
            ok = not got
            detail = f"expected clean, got {sorted(got)}"
        else:
            ok = expect_code in got
            detail = f"expected {expect_code}, got {sorted(got)}"
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  <- {detail}"))
        return ok


def main() -> int:
    os.environ.setdefault("SCULPT_MAX", "3")
    os.environ.setdefault("PLATE_MM", "160")
    r = []
    r.append(case("clean document passes", expect_clean=True))

    r.append(case("hedged quantity is caught",
                  gdd=GOOD_GDD.replace("3 clicks per turn", "several clicks per turn"),
                  expect_code="unbound"))
    r.append(case("'many' alone is still a hedge",
                  gdd=GOOD_GDD.replace("3 clicks per turn", "many clicks per turn"),
                  expect_code="unbound"))
    r.append(case("'how many' / 'as many as' are not hedges",
                  gdd=GOOD_GDD.replace("Each keeper spends 3 clicks per turn",
                                       "The choice is how many clicks you risk, as many as "
                                       "3; each keeper spends 3 clicks per turn"),
                  expect_clean=True))

    only_setup = GOOD_GDD.replace("turn `winder_dial` up to 3 clicks", "turn the crank 3 times") \
                         .replace("spends 3 clicks per turn on `winder_dial`", "spends 3 clicks per turn")
    r.append(case("part that only appears in Setup is decoration",
                  gdd=only_setup, expect_code="decoration"))

    extra = GOOD_COMPS + [{"id": "ghost_token", "qty": 2, "role": "x", "class": "functional",
                           "duty": "x", "tolerance_mm": 0.2, "target_bbox_mm": [10, 10, 5],
                           "mates_with": [], "stores_in": "self"}]
    r.append(case("manifest part missing from gdd Components",
                  comps=extra, expect_code="manifest-orphan"))

    r.append(case("gdd names a part the manifest lacks",
                  gdd=GOOD_GDD.replace("- `winder_dial` x4", "- `winder_dial` x4\n- `lamp_relay` x1"),
                  expect_code="gdd-orphan"))

    big = json.loads(json.dumps(GOOD_COMPS))
    big[0]["target_bbox_mm"] = [200, 120, 8]
    r.append(case("part wider than the plate", comps=big, expect_code="plate"))

    sculpty = json.loads(json.dumps(GOOD_COMPS))
    for c in sculpty:
        c["class"] = "sculptural"
    sculpty += [dict(c, id=c["id"] + "_b", mates_with=[]) for c in sculpty]
    r.append(case("sculptural budget enforced", comps=sculpty, expect_code="sculpt-budget"))

    r.append(case("COLLIDE pair rejected",
                  mech=dict(GOOD_MECH, chosen=["blind_bag_draw", "gravity_magazine",
                                               "snap_off_tab"]),
                  expect_code="mech-collide"))

    # A doc with no discover.md has no lane, so it is not a legacy game and is
    # no longer required to carry permanent change. Before 2026-08-20 the rule
    # was inverted - every lane BUT family - and this case passed by default,
    # which is exactly how a campaign layer got into games nobody asked one of.
    r.append(case("no permanent-change, no lane -> not a campaign failure",
                  mech=dict(GOOD_MECH, chosen=["blind_bag_draw", "hand_off"]),
                  expect_clean=True))

    r.append(case("mechanism outside the vocabulary rejected",
                  mech=dict(GOOD_MECH, chosen=["worker_placement", "snap_off_tab"]),
                  expect_code="mech-unknown"))

    bad_mate = json.loads(json.dumps(GOOD_COMPS))
    bad_mate[0]["mates_with"] = ["no_such_part"]
    r.append(case("mate pointing at a missing part", comps=bad_mate,
                  expect_code="mate-missing"))

    # --- interaction, added 2026-08-19 ----------------------------------
    # 19 of 23 vocabulary ids carry no player-to-player content, so the lock
    # could satisfy every other rule and still produce solitaire-at-one-table.
    print("\ninteraction")
    r.append(case("two solo mechanisms rejected",
                  mech=dict(GOOD_MECH, chosen=["gravity_magazine", "snap_off_tab"]),
                  expect_code="mech-solitaire"))
    os.environ["MECH_SOLITAIRE"] = "allow"
    r.append(case("MECH_SOLITAIRE=allow is the owner's override for a solo race",
                  mech=dict(GOOD_MECH, chosen=["gravity_magazine", "snap_off_tab"]),
                  expect_clean=True))
    os.environ.pop("MECH_SOLITAIRE")
    r.append(case("an interaction mechanism satisfies it",
                  mech=dict(GOOD_MECH, chosen=["hand_off", "snap_off_tab"]),
                  expect_clean=True))
    # bistable_snap/shape_change joined the permanent group with this change
    r.append(case("shape_change counts as permanent change",
                  mech=dict(GOOD_MECH, chosen=["hand_off", "shape_change"]),
                  expect_clean=True))

    # --- complexity budgets, added 2026-08-19 ---------------------------
    # The panel had four axes and all four pulled toward MORE. These are the
    # same argument made where it cannot be talked around. Every case below is
    # a real measurement of keep-the-light-relay, the game that exposed the gap.
    print("\ncomplexity budgets")
    r.append(case("rules over the word budget",
                  gdd=GOOD_GDD.replace("## Turn structure\n",
                                       "## Turn structure\n" + ("filler word " * 2000) + "\n"),
                  expect_code="gdd-too-long"))
    # The read-aloud and the parts list have their own budgets; they do not
    # count against the rules budget (dead-stop 2026-08-22).
    r.append(case("a long First minute does not spend the rules budget",
                  gdd=GOOD_GDD.replace("## First minute\n",
                                       "## First minute\n" + ("filler word " * 2000) + "\n"),
                  expect_code="first-minute-long"))

    glossary = GOOD_GDD + "\n\n## Glossary\n" + "\n".join(
        f"- **Term{i}** - a word the table must learn first." for i in range(9))
    r.append(case("a private vocabulary is caught", gdd=glossary,
                  expect_code="gdd-glossary"))

    formula = GOOD_GDD.replace(
        "## Win/lose",
        "## Win/lose\n- Quota is intact facets plus 2 minus 1 per inverted tile.\n")
    r.append(case("an arithmetic win condition is caught", gdd=formula,
                  expect_code="gdd-arithmetic"))

    # --- a part is a rule, and a rule is teaching time --------------------
    # Nothing enforced the parts budget until 2026-08-20: DISCOVER scores a
    # candidate on it, the winner states a number, and then no phase checked it.
    os.environ["PARTS"] = "6-10"
    many = [dict(GOOD_COMPS[0], id=f"filler_{i}") for i in range(9)]
    r.append(case("11 printed designs over a 6-10 budget",
                  comps=GOOD_COMPS[:2] + many,
                  gdd=GOOD_GDD + "\n## Extra\n"
                  + "\n".join(f"`filler_{i}` x1 - does a thing in Turn structure"
                               for i in range(9)),
                  expect_code="comp-count"))

    # Inside the hard budget but above what the panel picked the game on -
    # overcommit was chosen at 7 parts and written at 10.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        write(d)
        (d / "discover.md").write_text(
            "WINNER: x\n\nMechanism: a thing - 1 parts.\n", encoding="utf-8")
        got = {i["code"] for i in consistency.check(d, HERE)}
        ok = "comp-drift" in got and "comp-count" not in got
        print(f"  {'PASS' if ok else 'FAIL'}  drift from the promised count is a "
              f"medium, not a budget failure" + ("" if ok else f"  <- {sorted(got)}"))
        r.append(ok)

    for text, want in (("Mechanism: a thing - 7 parts.", "7"),
                       ("Mechanism: a thing \u2014 12 parts.", "12"),
                       ("Mechanism: a thing with no count.", ""),
                       ("", "")):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            if text:
                (d / "discover.md").write_text(text + "\n", encoding="utf-8")
            got = consistency.promised_parts(d)
            print(f"  {'PASS' if got == want else 'FAIL'}  promised_parts({text[:28]!r}) -> {got!r}")
            r.append(got == want)

    for dial, want in (("6-10", (6, 10)), ("6 - 14", (6, 14)),
                       ("garbage", (6, 10)), ("", (6, 10))):
        os.environ["PARTS"] = dial
        got = consistency.parts_budget()
        print(f"  {'PASS' if got == want else 'FAIL'}  parts_budget({dial!r}) -> {got}")
        r.append(got == want)
    os.environ["PARTS"] = "6-10"

    # --- numbers in the RULES, not in the parts list ----------------------
    # Density was tried first and ranks these backwards; the absolute count in
    # the rules sections tracks the readers' teach score. Components is
    # excluded on purpose - qty and millimetres are manufacturing.
    os.environ["GDD_MAX_RULE_NUMBERS"] = "10"
    dense = GOOD_GDD.replace(
        "## Turn structure",
        "## Turn structure\n" + " ".join(f"step {i} costs {i} charge." for i in range(12)))
    r.append(case("many numbers in the turn loop is caught",
                  gdd=dense, expect_code="gdd-numbers"))

    parts_heavy = GOOD_GDD.replace(
        "## Components",
        "## Components\n" + " ".join(f"`p{i}` x{i} - 12x34x{i}mm." for i in range(12)))
    got = [i for i in consistency.complexity(parts_heavy) if i[1] == "gdd-numbers"]
    ok = not got
    print(f"  {'PASS' if ok else 'FAIL'}  numbers in ## Components do not count"
          + ("" if ok else f"  <- {got}"))
    r.append(ok)
    os.environ.pop("GDD_MAX_RULE_NUMBERS")

    # --- a campaign is required only where it is the point -----------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        write(d, mech=dict(GOOD_MECH, chosen=["hand_off", "gravity_magazine"]))
        (d / "discover.md").write_text("| x | coop | 6 |\nWINNER: x\n",
                                       encoding="utf-8")
        got = {i["code"] for i in consistency.check(d, HERE)}
        ok = "mech-no-legacy" not in got
        print(f"  {'PASS' if ok else 'FAIL'}  a coop game is not forced to be a "
              f"campaign" + ("" if ok else f"  <- {sorted(got)}"))
        r.append(ok)

        (d / "discover.md").write_text("| x | legacy | 6 |\nWINNER: x\n",
                                       encoding="utf-8")
        got = {i["code"] for i in consistency.check(d, HERE)}
        ok = "mech-no-legacy" in got
        print(f"  {'PASS' if ok else 'FAIL'}  the LEGACY lane still must be a "
              f"campaign" + ("" if ok else f"  <- {sorted(got)}"))
        r.append(ok)

        (d / "discover.md").write_text("| x | family | 6 |\nWINNER: x\n",
                                       encoding="utf-8")
        ok = "mech-no-legacy" not in {i["code"] for i in consistency.check(d, HERE)}
        print(f"  {'PASS' if ok else 'FAIL'}  the family waiver still holds")
        r.append(ok)

    r.append(case("four mechanisms rejected",
                  mech=dict(GOOD_MECH, chosen=["snap_off_tab", "ratchet_dial",
                                               "gravity_magazine", "physical_timer"]),
                  expect_code="mech-count"))

    # lane_of reads the winner's row out of discover.md; without that file the
    # permanent-change rule stays on, which is the safe default.
    print("\nfamily lane waiver")
    import consistency as _c
    with tempfile.TemporaryDirectory() as td:
        d2 = Path(td)
        (d2 / "discover.md").write_text(
            "| keep-the-light-relay | legacy | 12 | 7 | 7 | 7 | 7 | 7 | 3 | x |\n"
            "\nWINNER: keep-the-light-relay\n", encoding="utf-8")
        got = _c.lane_of(d2)
        print(f"  {'PASS' if got == 'legacy' else 'FAIL'}  lane read from discover.md"
              + ("" if got == "legacy" else f"  <- got {got!r}"))
        r.append(got == "legacy")
        got = _c.lane_of(Path(td) / "nope")
        print(f"  {'PASS' if got == '' else 'FAIL'}  no discover.md -> no lane")
        r.append(got == "")

    # --- the one part this box is remembered by, added 2026-08-20 ---------
    # A shopper remembers one object. Nothing in this pipeline named one, so
    # every game came out as an evenly-weighted set of parts.
    print("\nsignature part")
    no_sig = json.loads(json.dumps(GOOD_COMPS))
    for c in no_sig:
        c.pop("signature", None)
    r.append(case("no signature part at all", comps=no_sig, expect_code="signature"))

    two_sig = json.loads(json.dumps(GOOD_COMPS))
    for c in two_sig:
        c["signature"] = True
    r.append(case("two signature parts", comps=two_sig, expect_code="signature"))

    # winder_dial appears in Turn structure too, so move the flag onto a part
    # the loop never touches to exercise the idle case.
    idle = json.loads(json.dumps(GOOD_COMPS)) + [
        {"id": "crest_badge", "qty": 1, "role": "the crest on the lid",
         "class": "sculptural", "duty": "none", "tolerance_mm": 1.0,
         "target_bbox_mm": [40, 40, 4], "mates_with": [], "stores_in": "self",
         "signature": True}]
    idle[0].pop("signature", None)
    r.append(case("a signature part no rule touches is a mascot",
                  comps=idle,
                  gdd=GOOD_GDD.replace("- `winder_dial` x4",
                                       "- `winder_dial` x4\n- `crest_badge` x1")
                              .replace("## Win/lose",
                                       "## Win/lose\nHolding `crest_badge` breaks a tie."),
                  expect_code="signature-idle"))

    # --- the shelf contract, added 2026-08-22 -----------------------------
    # The market read (text2game-ops/findings/) is unambiguous: printed games
    # are judged at the shelf - where the pieces live, where the RULES live -
    # before they are judged at the table. Storage is now part of the contract.
    print("\nshelf contract")
    homeless = json.loads(json.dumps(GOOD_COMPS))
    homeless[1]["stores_in"] = ""
    r.append(case("empty stores_in is a homeless part", comps=homeless,
                  expect_code="homeless-part"))

    lost = json.loads(json.dumps(GOOD_COMPS))
    lost[1]["stores_in"] = "no_such_box"
    r.append(case("stores_in naming a ghost id", comps=lost,
                  expect_code="stores-unknown"))

    no_rules = json.loads(json.dumps(GOOD_COMPS))
    no_rules[0].pop("rules_carrier")
    r.append(case("no rules carrier - where do you put the rules?",
                  comps=no_rules, expect_code="rules-carrier"))

    two_rules = json.loads(json.dumps(GOOD_COMPS))
    two_rules[1]["rules_carrier"] = True
    r.append(case("two rules carriers", comps=two_rules,
                  expect_code="rules-carrier"))

    r.append(case("gdd without a First minute section",
                  gdd=GOOD_GDD.replace("## First minute", "## Opening notes"),
                  expect_code="first-minute"))

    dragging = GOOD_GDD.replace(
        "Place `beam_disc` on the tower and give each keeper a `winder_dial`.",
        "\n".join(f"{i}. Place piece number {i} on spot {i}." for i in range(1, 9)))
    r.append(case("8 setup steps is a drag", gdd=dragging,
                  expect_code="setup-drag"))

    # --- the lid budget, added 2026-08-22 after dead-stop ------------------
    print("\nlid budget")
    long_fm = GOOD_GDD.replace("Wind your dial, sweep the beam, save ships.",
                               "Wind your dial. " * 230)
    r.append(case("a 460-word First minute does not fit the lid",
                  gdd=long_fm, expect_code="first-minute-long"))
    steps = GOOD_GDD.replace("2. Sweep: rotate `beam_disc` 60 degrees per click spent.",
                             "\n".join(f"{i}. Step {i}: rotate `beam_disc` 60 degrees."
                                       for i in range(2, 8)))
    r.append(case("seven turn steps is too many concepts", gdd=steps,
                  expect_code="turn-steps"))

    # --- external commodities: magnets and rubber bands only --------------
    print("\nexternal commodities")
    magnet = json.loads(json.dumps(GOOD_COMPS))
    magnet[0]["external"] = {"item": "magnet", "spec": "6x3mm N35 disc",
                             "qty_per": 2}
    r.append(case("a spec'd magnet is allowed", comps=magnet, expect_clean=True))

    vague = json.loads(json.dumps(GOOD_COMPS))
    vague[0]["external"] = {"item": "magnet"}
    r.append(case("a magnet without a spec is undocumented", comps=vague,
                  expect_code="external-unspecified"))

    ball = json.loads(json.dumps(GOOD_COMPS))
    ball[0]["external"] = {"item": "steel_ball", "spec": "8mm"}
    r.append(case("a steel ball is not on the whitelist", comps=ball,
                  expect_code="external-banned"))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
