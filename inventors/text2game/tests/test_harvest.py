#!/usr/bin/env python3
"""Fixtures for harvest.py - the parsers must survive what the agents actually
write, and the classifier must not quietly invent a symptom id.

Every string below is copied from a real critic.json or referee.md in out/.

    python3 tests/test_harvest.py
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import harvest  # noqa: E402

MECH_MD = (HERE / "mechanisms.md").read_text(encoding="utf-8")

# claim -> the id it must land on. Real sentences, real designs.
CLAIMS = [
    ("The 5-word, no-numbers muzzle on non-active keepers only applies 'during "
     "this whole turn,' so nothing stops the table from openly dictating the "
     "exact play.", "alpha_solve"),
    ("The open board and deterministic two-slug threat let a confident player "
     "prescribe the next move during Handoff.", "alpha_solve"),
    ("The fragment ratchet duplicates the exact 0-6 damage state already shown "
     "by the mandatory ordered wedges, so removing it would cost no decision.",
     "duplicate_state"),
    ("rank_track never gates or changes a rule - it only totals a number the "
     "harbour headcount already shows at every dawn.", "duplicate_state"),
    ("The 0-120 influence track contains 54 unreachable spaces.", "dead_range"),
    ("Six successful dives do not end the campaign, so once the crew reaches 6 "
     "the dominant strategy is to stop playing.", "decided_early"),
    ("Gain's guaranteed 2 influence weakly dominates Move.", "dominant_action"),
    ("A fragment lowers capacity on the very next turn, which can turn one "
     "mistake into an uncontrollable march to fragment 6.", "spiral"),
    ("The lowest-numbered pawn starts every dive and therefore repeatedly "
     "receives the extra turn whenever the alarm count is not divisible by the "
     "player count.", "seat_advantage"),
    ("At four players the largest opening total that cannot overload the "
     "minimum demand is 6.", "count_break"),
    ("A player reduced to zero markers cannot use Move or Press and may spend "
     "the rest of the session taking consolation points.", "idle_player"),
    ("an early leader can afford repeated attacks while a trailer at 0 or 1 "
     "cannot attack at all", "runaway_leader"),
]

REFEREE_MD = """# Referee Report

## Game 1
turn 1: A winds 3.

## Findings

### CONTRADICTION - flare rescue count on an inverted tile
Rule 4.2 says the flare rescues 2; rule 7.1 says 1.

### MISSING INFO - no component tracks the campaign-wide rescue tally
Win/lose needs a number nothing on the table carries.

## Verdict

FINDINGS: 2
"""


def case(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  <- {detail}"))
    return ok


def main() -> int:
    r = []

    # --- the guard that makes mechanisms.md the single source of truth -----
    vocab = harvest.symptom_vocab(MECH_MD)
    unknown = {sid for sid, _ in harvest.PATTERNS} - vocab
    r.append(case("every pattern id is defined under ## SYMPTOM",
                  not unknown, sorted(unknown)))
    r.append(case("the mechanism vocabulary is NOT pulled in as symptoms",
                  "ratchet_dial" not in vocab and "alpha_solve" in vocab,
                  sorted(vocab)[:6]))

    # consistency.py reads the same file for a different table; the SYMPTOM
    # rows open with | `id` | exactly like the vocabulary rows do.
    import consistency
    mech_vocab = set(__import__("re").findall(
        r"^\| `([a-z_]+)` \|",
        MECH_MD.split("## Vocabulary", 1)[-1].split("## Permanent change", 1)[0],
        __import__("re").M))
    r.append(case("mechanism vocab excludes every symptom id",
                  not (mech_vocab & vocab), sorted(mech_vocab & vocab)))
    r.append(case("COLLIDE parsing is unaffected by the new tables",
                  frozenset({"blind_bag_draw", "gravity_magazine"})
                  in consistency.collide_pairs(MECH_MD)))

    # --- classification ---------------------------------------------------
    for claim, want in CLAIMS:
        got, _ = harvest.classify(claim)
        r.append(case(f"{want:<16} <- {claim[:46]}...", got == want, got))

    # --- MITIGATE -----------------------------------------------------------
    mits = harvest.mitigations(MECH_MD)
    r.append(case("MITIGATE rows parse", "alpha_solve" in mits, sorted(mits)))
    empty = [(s, m["fix"]) for s, ms in mits.items() for m in ms if not m["costs"]]
    r.append(case("no fix ships with an empty costs cell", not empty, empty))
    r.append(case("every mitigated symptom exists in SYMPTOM",
                  not (set(mits) - vocab), sorted(set(mits) - vocab)))

    # --- parsers ------------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "critic.json").write_text(json.dumps([
            {"severity": "high", "issue": CLAIMS[0][0], "where": "Turn", "fix": "x"},
            {"severity": "resolved", "issue": "already fixed", "where": "", "fix": ""},
            {"severity": "low", "issue": "", "where": "", "fix": ""},
        ]), encoding="utf-8")
        rows = harvest.from_critic(d)
        r.append(case("critic: resolved and empty rows are dropped",
                      len(rows) == 1 and rows[0]["symptom"] == "alpha_solve",
                      rows))

        (d / "referee.md").write_text(REFEREE_MD, encoding="utf-8")
        ref = harvest.from_referee(d)
        r.append(case("referee: both Findings blocks, kinds mapped",
                      [x["symptom"] for x in ref] == ["contradiction", "missing_info"],
                      [x["symptom"] for x in ref]))
        r.append(case("referee: turn logs are not harvested as findings",
                      all("turn 1" not in x["claim"] for x in ref)))

        (d / "referee.md").write_text("## Findings\n\n## Verdict\n\nCLEAN\n",
                                      encoding="utf-8")
        r.append(case("referee: a CLEAN verdict yields nothing",
                      harvest.from_referee(d) == []))

    # --- recall -------------------------------------------------------------
    rows = harvest.harvest(HERE)
    r.append(case("harvest finds the runs on disk", len(rows) > 0, len(rows)))
    r.append(case("scratch dirs and re-runs are excluded",
                  not any(x["slug"].startswith("_") for x in rows)))
    block = harvest.recall(["ratchet_dial", "blind_bag_draw"], rows, mits)
    r.append(case("recall names a symptom and the cost of its fix",
                  "COSTS:" in block and "`" in block, block[:80]))
    r.append(case("recall is capped", block.count("\n- ") <= 10,
                  block.count("\n- ")))

    # --- the wiring into prompts.critic() -----------------------------------
    import os
    import importlib
    import prompts

    d = HERE / "out" / "the-hull-remembers"
    text = prompts.critic(d)
    r.append(case("critic prompt carries the SYMPTOM vocabulary",
                  "## SYMPTOM" in text and "## MITIGATE" in text))
    r.append(case("critic.json contract asks for a symptom id",
                  '"symptom": "one id from the PLAY table"' in text))
    r.append(case("critic prompt carries evidence and its costs",
                  "EVIDENCE from previous designs" in text and "COSTS:" in text))
    # The one that matters: a design must never be handed its own findings as
    # though another game had produced them.
    r.append(case("a design is never shown its own findings",
                  "The open board and deterministic two-slug threat" not in text))
    # Asserting one specific claim string was brittle: the corpus grew to 35
    # findings and the top-10 cap pushed that exact line out, failing a test
    # about a property that still held. Check the property.
    block = text.split("EVIDENCE from previous designs", 1)[-1]
    bullets = [ln for ln in block.splitlines() if ln.startswith("- `")]
    r.append(case("several other designs' findings are shown",
                  len(bullets) >= 3, f"{len(bullets)} bullets"))
    r.append(case("every bullet names a symptom id from the vocabulary",
                  all(any(f"`{v}`" in b for v in vocab) for b in bullets),
                  bullets[:2]))
    r.append(case("MECHANISM LOCK does not get the SYMPTOM tables",
                  "## SYMPTOM" not in prompts.mechanism(d)))

    with tempfile.TemporaryDirectory() as td:
        quiet = prompts.critic(Path(td))
        r.append(case("no mechanisms.json degrades instead of erroring",
                      "no evidence available" not in quiet
                      and "EVIDENCE from previous" in quiet))

    os.environ["CRITIC_EVIDENCE"] = "off"
    importlib.reload(prompts)
    r.append(case("CRITIC_EVIDENCE=off removes the block",
                  "EVIDENCE from previous designs" not in prompts.critic(d)))
    os.environ.pop("CRITIC_EVIDENCE")
    importlib.reload(prompts)

    r.append(case("recall with no rows is empty, not a bare header",
                  harvest.recall([], [], {}) == ""))

    # --- the critic's own label wins over the regex --------------------------
    with tempfile.TemporaryDirectory() as td:
        d2 = Path(td)
        (d2 / "critic.json").write_text(json.dumps([
            {"severity": "high", "symptom": "kingmaker",
             "issue": "Gain weakly dominates Move but the real problem is that "
                      "the loser picks the winner.", "where": "x", "fix": "y"},
            {"severity": "low", "symptom": "not_a_real_id",
             "issue": "an early leader can afford repeated attacks",
             "where": "x", "fix": "y"},
        ]), encoding="utf-8")
        got = harvest.from_critic(d2)
        r.append(case("a declared id beats the pattern match",
                      got[0]["symptom"] == "kingmaker"
                      and got[0]["labelled"] == "critic"
                      and "dominant_action" in got[0]["also"], got[0]))
        r.append(case("an invented id falls back to the pattern",
                      got[1]["symptom"] == "runaway_leader"
                      and got[1]["labelled"] == "pattern"
                      and got[1]["declared"] == "not_a_real_id", got[1]))

    # --- per-round snapshots -------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "out" / "toy"
        (d / "rounds" / "r1").mkdir(parents=True)
        (d / "rounds" / "r2").mkdir(parents=True)
        claim = ("an early leader can afford repeated attacks while a trailer "
                 "at 0 or 1 cannot attack at all")
        for rd in ("r1", "r2"):
            (d / "rounds" / rd / "critic.json").write_text(json.dumps(
                [{"severity": "high", "issue": claim, "where": "x", "fix": "y"}]),
                encoding="utf-8")
        # the live file is round 2's, already captured by the r2 snapshot
        (d / "critic.json").write_text(json.dumps(
            [{"severity": "high", "issue": claim, "where": "x", "fix": "y"}]),
            encoding="utf-8")
        rows = harvest.harvest(root)
        r.append(case("findings are read out of every round snapshot",
                      len(rows) == 2, [(x.get("round"), x["symptom"]) for x in rows]))
        r.append(case("the live file is not counted twice",
                      sum(1 for x in rows if x["claim"] == claim) == 2, len(rows)))
        r.append(case("a symptom the reviser never fixed is marked",
                      all(x.get("survived_rounds") == 2 for x in rows),
                      [x.get("survived_rounds") for x in rows]))
        r.append(case("rows carry the round they came from",
                      sorted(x["round"] for x in rows) == ["1", "2"],
                      [x.get("round") for x in rows]))

    # --- table notes: the weight-4 source, added 2026-08-22 -----------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "out" / "toy"
        d.mkdir(parents=True)
        (d / "table_notes.md").write_text(
            "# Table notes - first night, 4 players\n"
            "- fiddly_reset: repacking the tower took longer than round one\n"
            "- `unsatisfying_action`: the flip landed and nobody looked up\n"
            "- made_up_id: an early leader can afford repeated attacks while "
            "a trailer at 0 or 1 cannot attack at all\n", encoding="utf-8")
        got = harvest.from_table(d)
        r.append(case("table bullets become weight-4 rows",
                      len(got) == 3 and got[0]["symptom"] == "fiddly_reset"
                      and got[0]["labelled"] == "table", got))
        r.append(case("a backticked id still parses",
                      got[1]["symptom"] == "unsatisfying_action", got[1]))
        r.append(case("an unknown table id falls back to the pattern",
                      got[2]["symptom"] == "runaway_leader"
                      and got[2]["labelled"] == "pattern"
                      and got[2]["declared"] == "made_up_id", got[2]))
        rows = harvest.harvest(root)
        r.append(case("harvest carries table rows at weight 4",
                      len(rows) == 3 and all(x["weight"] == 4 for x in rows),
                      [(x["source"], x.get("weight")) for x in rows]))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
