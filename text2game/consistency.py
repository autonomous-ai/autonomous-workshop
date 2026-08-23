#!/usr/bin/env python3
"""Machine checks over gdd.md + components.json + mechanisms.json.

No LLM. Everything here is a rule an agent kept breaking in text2cad, made
falsifiable: an agent asked to self-check its own document will report it clean.

Run:  ./consistency.py <out_dir>   ->  consistency.json, exit 1 if any `high`.
"""
import json
import os
import re
import sys
from pathlib import Path

# Sections where a component must appear to count as LOAD-BEARING. Being listed
# in Setup or Components only means it is on the table, not that it changes a
# decision - taste_boardgame.md: "if removing a component costs the game no
# decision, it was decoration".
DECISION_SECTIONS = ("Turn structure", "Action economy", "Win/lose", "Legacy")

# GameGrammar earns its keep here: its whole pitch against a raw LLM is that it
# says "6 observation points per turn" where the LLM says "resource management".
# These are the words that let a rule pretend to be specific.
# `many` is a hedge ("many crates") but "how many" / "as many as" are questions
# and comparisons, not unbound quantities - dead-stop r2 2026-08-22 was failed
# on "the choice is how many pieces you put at risk". Negative lookbehind.
HEDGES = r"\b(some|several|a few|a number of|multiple|various|limited|enough|" \
         r"appropriate|reasonable|sufficient|(?<!how )(?<!as )many|plenty|" \
         r"roughly|about|approximately|as needed|or so)\b"

REQUIRED_KEYS = ("id", "qty", "role", "class", "duty", "tolerance_mm",
                 "target_bbox_mm", "mates_with", "stores_in")

# The two commodities a design may embed besides printed plastic, decided
# 2026-08-22 from the market read (text2game-ops/findings/): magnets carry most
# of the printed games people actually buy. Anything else is banned, and both
# need an exact spec — an external part without one is `undocumented_build`.
EXTERNAL_OK = ("magnet", "rubber_band")


def parts_budget() -> tuple:
    """(lo, hi) distinct printed designs, from the PARTS dial. Default 6-10."""
    m = re.match(r"\s*(\d+)\s*-\s*(\d+)", os.environ.get("PARTS", "6-10"))
    return (int(m.group(1)), int(m.group(2))) if m else (6, 10)


def promised_parts(out_dir: Path) -> str:
    """What the DISCOVER winner said its part count would be, for the message."""
    f = out_dir / "discover.md"
    if not f.is_file():
        return ""
    m = re.search(r"^Mechanism:.*?[-\u2014]\s*(\d+)\s*parts\.", 
                  f.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


RULE_SECTIONS = ("Setup", "Turn structure", "Action economy",
                 "Win/lose", "Legacy", "Edge cases")


def sections(md: str) -> dict:
    """Split a markdown doc into {heading: body} on ## headings."""
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def collide_pairs(mech_md: str) -> set:
    """Parse the COLLIDE table of mechanisms.md into a set of frozensets."""
    body = mech_md.split("## COLLIDE", 1)[-1].split("## Rule", 1)[0]
    pairs = set()
    for line in body.splitlines():
        ids = re.findall(r"`([a-z_]+)`", line)
        if len(ids) == 2:
            pairs.add(frozenset(ids))
    return pairs


def lane_of(out_dir: Path) -> str:
    """The DISCOVER lane the winner came from, out of discover.md's table."""
    f = out_dir / "discover.md"
    if not f.is_file():
        return ""
    text = f.read_text(encoding="utf-8")
    m = re.search(r"^WINNER:\s*([a-z0-9-]+)", text, re.M)
    if not m:
        return ""
    row = re.search(rf"^\|\s*{re.escape(m.group(1))}\s*\|\s*([a-z]+)\s*\|",
                    text, re.M)
    return row.group(1).strip().lower() if row else ""


# Words that turn a win condition into a sum a player must compute every round.
ARITHMETIC = re.compile(r"\b(plus|minus|per|times|divided|floor|cap(?:ped)?|"
                        r"rounded|remainder)\b", re.I)


def complexity(gdd: str) -> list:
    """Is this teachable? Three checks, all deterministic.

    The panel had four axes and every one of them pulled toward MORE - novelty
    rewards going somewhere strange, craft rewards a decision every turn, the
    parts dial rewarded a fuller box. Nothing scored whether a stranger could be
    taught the thing. keep-the-light-relay cleared every axis at 3,788 words,
    376 numbers and an 11-term glossary. A `teach` axis now argues the other
    side in DISCOVER; these are the same argument made where it cannot be
    talked around.
    """
    out = []
    max_words = int(os.environ.get("GDD_MAX_WORDS", "1800"))
    # The RULES, not the document: Overview plus the rule sections. First minute
    # has its own budget (FIRST_MINUTE_MAX_WORDS), Components is a parts list
    # (budgeted by PARTS) and Glossary is budgeted by GDD_MAX_GLOSSARY; counting
    # them here charged the read-aloud twice - dead-stop 2026-08-22: 1128 words
    # of document, 756 of rules, failed at 900 for a section that fits the lid.
    # Same scoping the numbers check below has used since 2026-08-19.
    counted = "".join(body for head, body in re.findall(
        r"^##\s+(.+?)\s*$(.*?)(?=^##\s|\Z)", gdd, re.M | re.S)
        if head.strip() in RULE_SECTIONS or head.strip().startswith("Overview"))
    words = len(counted.split())
    if words > max_words:
        out.append(("high", "gdd-too-long",
                    f"the rules are {words} words (Overview + Setup / Turn structure "
                    f"/ Action economy / Win-lose / Legacy / Edge cases), budget is "
                    f"{max_words} - cut a subsystem, do not compress the prose"))

    max_terms = int(os.environ.get("GDD_MAX_GLOSSARY", "5"))
    # findall, not search: an author who writes the glossary in two blocks (or
    # repeats the heading) would otherwise have only the first one counted, and
    # the budget would silently pass. Found by its own test 2026-08-19.
    terms = [term
             for body in re.findall(r"^##\s+Glossary\s*$(.*?)(?=^##\s|\Z)",
                                    gdd, re.M | re.S)
             for term in re.findall(r"^\s*[-*]\s*\*\*(.+?)\*\*", body, re.M)]
    if len(terms) > max_terms:
        out.append(("high", "gdd-glossary",
                    f"{len(terms)} invented terms ({', '.join(terms[:6])}...) - "
                    f"a private vocabulary is learned before the first turn; "
                    f"budget is {max_terms}"))

    # NUMBERS IN THE RULES. Every number in a rule is a threshold a player has
    # to remember or look up mid-turn.
    #
    # This started as a DENSITY check and density is WRONG - measured over the
    # three games this pipeline has produced, numbers per 100 words ranks them
    # backwards (overcommit 14.0 at teach 6, keep-the-light-relay 9.9 at
    # teach 4) because a long document dilutes its own numbers with prose. The
    # ABSOLUTE count in the rules sections tracks the readers' teach score
    # exactly: 249 -> teach 4, 157 -> teach 6, 104 -> teach 8. Components and
    # Overview are excluded: qty and millimetres are manufacturing, not rules.
    max_nums = int(os.environ.get("GDD_MAX_RULE_NUMBERS", "140"))
    rules = "".join(body for head, body in re.findall(
        r"^##\s+(.+?)\s*$(.*?)(?=^##\s|\Z)", gdd, re.M | re.S)
        if head.strip() in RULE_SECTIONS)
    nums = re.findall(r"\b\d+\b", rules)
    if len(nums) > max_nums:
        out.append(("high", "gdd-numbers",
                    f"{len(nums)} numbers in the rules sections ({len(set(nums))} "
                    f"distinct), budget is {max_nums} - every one is a threshold "
                    f"to hold or look up; delete a subsystem, do not round them"))

    for body in re.findall(r"^##\s+Win/lose\s*$(.*?)(?=^##\s|\Z)", gdd, re.M | re.S):
        for line in body.splitlines():
            hits = sorted({h.lower() for h in ARITHMETIC.findall(line)})
            if len(hits) >= 2:
                out.append(("medium", "gdd-arithmetic",
                            f"the win condition is a formula ({', '.join(hits)}): "
                            f"{line.strip()[:120]}"))
                return out
    return out


def check(out_dir: Path, here: Path) -> list:
    issues = []

    def bad(sev, code, msg):
        issues.append({"severity": sev, "code": code, "message": msg})

    gdd_f, comp_f, mech_f = (out_dir / "gdd.md", out_dir / "components.json",
                             out_dir / "mechanisms.json")
    for f in (gdd_f, comp_f, mech_f):
        if not f.exists():
            bad("high", "missing-file", f"{f.name} was not produced")
    if issues:
        return issues

    gdd = gdd_f.read_text(encoding="utf-8")
    for sev, code, msg in complexity(gdd):
        bad(sev, code, msg)
    try:
        comps = json.loads(comp_f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        bad("high", "bad-json", f"components.json does not parse: {e}")
        return issues
    if isinstance(comps, dict):
        comps = comps.get("components", [])

    # --- how many parts is how many rules ---------------------------------
    # Nothing checked this until 2026-08-20. DISCOVER scores candidates on a
    # PARTS budget and the winner states a number, then the gdd author writes
    # `## Components` freely and the manifest is forbidden from dropping any of
    # them - so the promise was made in one phase and enforced in none.
    # keep-the-light-relay promised 12 and shipped 13 at teach 4; overcommit 7
    # and shipped 10 at teach 6; one-way-ratchet shipped 6 at teach 8. Of every
    # deterministic quantity available, this one tracks the readers' teach
    # score most cleanly, and it is the earliest one that can be enforced: a
    # part is a rule, and a rule is teaching time.
    lo, hi = parts_budget()
    said = promised_parts(out_dir)
    if len(comps) > hi:
        bad("high", "comp-count",
            f"{len(comps)} distinct printed designs, budget is {lo}-{hi}"
            + (f" and the panel picked this game on {said}" if said else "")
            + " - delete a part and the rule that came with it, do not merge "
              "two parts into one that carries both jobs")
    elif said and len(comps) > int(said):
        # Inside the hard budget but above what the game was CHOSEN on.
        # overcommit was picked at 7 parts and written at 10, and every one of
        # those three came with rules nobody had scored the game on.
        bad("medium", "comp-drift",
            f"{len(comps)} printed designs, but the panel picked this game on "
            f"{said} - the {len(comps) - int(said)} extra part(s) arrived after "
            f"the decision, with the rules they carry")

    # --- mechanisms -------------------------------------------------------
    mech = json.loads(mech_f.read_text(encoding="utf-8"))
    chosen = mech.get("chosen", [])
    if not 2 <= len(chosen) <= 3:
        # Was 2-4 until 2026-08-19. Four subsystems is four things a player
        # holds at once: keep-the-light-relay locked all four and needed 3,788
        # words of rules to explain them.
        bad("high", "mech-count", f"MECHANISM LOCK chose {len(chosen)}, must be 2-3")
    # Scoped to `## Vocabulary` since 2026-08-20. The SYMPTOM and MITIGATE
    # tables added that day open their rows the same way - | `alpha_solve` | -
    # and a findall over the whole file silently admitted every symptom id into
    # the mechanism vocabulary, so MECHANISM LOCK could have chosen one and
    # mech-unknown would have passed it.
    mech_md = (here / "mechanisms.md").read_text(encoding="utf-8")
    vocab = set(re.findall(r"^\| `([a-z_]+)` \|",
                           mech_md.split("## Vocabulary", 1)[-1]
                                  .split("## Permanent change", 1)[0], re.M))
    for m in chosen:
        if m not in vocab:
            bad("high", "mech-unknown", f"`{m}` is not in the mechanisms.md vocabulary")
    permanent = {"snap_off_tab", "bolted_module", "ratchet_dial",
                 "sealed_compartment", "socket_swap", "bistable_snap",
                 "shape_change"}
    # Interaction group, added 2026-08-19. Of the 23 vocabulary ids, 19 carried
    # no player-to-player content, so a lock picking the two strongest ids picked
    # two solo ones - keep-the-light-relay's rebuild lost the lamp relay and its
    # design evaluation fell from social 9 to 3, while every deterministic check
    # here said CLEAN. A game whose mechanisms never touch another player is
    # several people doing solitaire at one table.
    interaction = {"hand_off", "blocking_claim", "physical_bid",
                   "shared_push_track", "opaque_sleeve", "peephole_screen"}
    # MECH_SOLITAIRE=allow is the OWNER's override for a design that is a
    # dexterity race by intent (dead-stop 2026-08-23: every throw is solo, the
    # table shares one track and a score race). It is an .env line, never a
    # default, so the doctrine stays the default and the exception is on record.
    if not interaction & set(chosen) and \
            os.environ.get("MECH_SOLITAIRE", "").strip().lower() != "allow":
        bad("high", "mech-solitaire",
            f"no interaction mechanism chosen ({sorted(chosen)}) - nothing here "
            f"makes one player's move matter to another; pick one of "
            f"{sorted(interaction)}")
    if not permanent & set(chosen) and lane_of(out_dir) == "legacy":
        # INVERTED 2026-08-20. This used to fire for every lane except
        # `family`, which meant two of the three lanes were forced to be
        # campaign games and the third still had to write a `## Legacy`
        # section. Every game this pipeline has ever produced came from the
        # legacy lane - zero coop, zero family - and a campaign layer is a
        # second rules system stacked on the base game: what persists, what
        # triggers the change, what the change does, how it ends. That is the
        # single largest block of rules a player has to learn, and it was
        # imposed by the pipeline rather than chosen by the design. It is now
        # required only where it is the point.
        bad("high", "mech-no-legacy",
            "no permanent-change mechanism chosen - nothing makes this worth printing")
    for pair in collide_pairs((here / "mechanisms.md").read_text(encoding="utf-8")):
        if pair <= set(chosen):
            bad("high", "mech-collide", f"COLLIDE pair chosen together: {sorted(pair)}")
    if not (mech.get("interaction") or "").strip():
        bad("high", "mech-no-interaction",
            "no interaction sentence - unrelated mechanisms in one box")

    # --- component schema -------------------------------------------------
    ids = []
    for i, c in enumerate(comps):
        missing = [k for k in REQUIRED_KEYS if k not in c]
        if missing:
            bad("high", "comp-schema", f"component #{i} missing keys: {missing}")
            continue
        ids.append(c["id"])
        if c["class"] not in ("functional", "sculptural"):
            bad("high", "comp-class", f"{c['id']}: class must be functional|sculptural")
        if not isinstance(c["qty"], int) or c["qty"] < 1:
            bad("high", "comp-qty", f"{c['id']}: qty must be a positive integer")
        bb = c.get("target_bbox_mm") or []
        if len(bb) != 3 or not all(isinstance(x, (int, float)) for x in bb):
            bad("high", "comp-bbox", f"{c['id']}: target_bbox_mm must be [x,y,z]")
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        bad("high", "comp-dupe", f"duplicate component ids: {sorted(dupes)}")

    # --- the one part this box is remembered by ---------------------------
    # Added 2026-08-20. taste_boardgame.md tells DISCOVER that "elaborate is
    # the target" and nothing anywhere told any phase that a shopper remembers
    # ONE object - the little metal dog, not the other 47 pieces. Every game
    # this pipeline has made is a set of equally-weighted parts, which is a
    # parts bin with rules. Exactly one component carries the flag, and it has
    # to be one the turn loop runs on: a signature part the rules never touch
    # is a mascot, and this pipeline has no budget for mascots.
    sig = [c.get("id", f"#{i}") for i, c in enumerate(comps)
           if c.get("signature") is True]
    turn = " ".join(v for k, v in sections(gdd).items()
                    if k.startswith("Turn structure"))
    if len(sig) != 1:
        bad("high", "signature",
            f"{len(sig)} components marked \"signature\": true, need exactly 1"
            + (f" ({sig})" if sig else " - nothing here is what the box is "
                                        "remembered by"))
    elif sig[0] not in turn:
        bad("medium", "signature-idle",
            f"`{sig[0]}` is the signature part but no rule in `## Turn "
            f"structure` touches it - the object the box is sold on is not the "
            f"object the game is played with")

    # --- sculptural budget ------------------------------------------------
    smax = int(os.environ.get("SCULPT_MAX", "3"))
    sculpt = [c["id"] for c in comps if c.get("class") == "sculptural"]
    if len(sculpt) > smax:
        bad("high", "sculpt-budget",
            f"{len(sculpt)} sculptural parts but SCULPT_MAX={smax} "
            f"(HF ZeroGPU allows ~2-3 runs/day): {sculpt}")

    # --- the shelf: where the game lives between games --------------------
    # Added 2026-08-22 from the market read: the recurring verdict on printed
    # games is "where do you put the rules?" — storage is judged at the shelf,
    # and a game that cannot put itself away loses there before it is played.
    idset = set(ids)
    for c in comps:
        if any(k not in c for k in REQUIRED_KEYS):
            continue  # comp-schema already fired
        home = str(c.get("stores_in") or "").strip()
        if not home:
            bad("high", "homeless-part",
                f"{c['id']}: stores_in is empty - every piece needs a printed "
                f"home between games (another component's id, or \"self\")")
        elif home != "self" and home not in idset:
            bad("high", "stores-unknown",
                f"{c['id']} stores in `{home}` which is not a component id "
                f"(use \"self\" for a part that is its own home)")
    carriers = [c.get("id") for c in comps if c.get("rules_carrier") is True]
    if len(carriers) != 1:
        bad("high", "rules-carrier",
            f"{len(carriers)} components marked \"rules_carrier\": true, need "
            f"exactly 1 - the rules ride ON a part (engraved, or a slot that "
            f"holds the one printed rules plate)"
            + (f" ({carriers})" if carriers else ""))

    # --- external parts: the two allowed commodities ----------------------
    for c in comps:
        ext = c.get("external")
        if not ext:
            continue
        if not isinstance(ext, dict):
            bad("high", "external-shape",
                f"{c.get('id', '?')}: external must be an object with item/spec")
            continue
        item = str(ext.get("item", "")).strip().lower()
        if item not in EXTERNAL_OK:
            bad("high", "external-banned",
                f"{c.get('id', '?')} embeds `{item or '?'}` - only "
                f"{list(EXTERNAL_OK)} are allowed, and only when load-bearing")
        if not str(ext.get("spec", "")).strip():
            bad("high", "external-unspecified",
                f"{c.get('id', '?')}: external `{item or '?'}` has no exact "
                f"spec (e.g. \"6x3mm N35 disc\", \"size #32 band\") - an "
                f"unspecified external part is an unbuildable document")

    # --- mates ------------------------------------------------------------
    for c in comps:
        for m in c.get("mates_with") or []:
            if m not in idset:
                bad("high", "mate-missing", f"{c['id']} mates with unknown `{m}`")
            elif c["id"] not in (next(x for x in comps if x["id"] == m).get("mates_with") or []):
                bad("warn", "mate-asymmetric",
                    f"{c['id']} lists `{m}` but `{m}` does not list it back")

    # --- gdd <-> manifest -------------------------------------------------
    secs = sections(gdd)
    # The cold open. Game 1 of the referee run and the only rules a stranger
    # actually reads: without this section the cold-open test silently plays
    # from nothing. Added 2026-08-22 with the shelf contract.
    if not any(k.startswith("First minute") for k in secs):
        bad("high", "first-minute",
            "gdd.md has no `## First minute` section - the one-sentence pitch "
            "plus turn 1, written to be read aloud; the referee plays game 1 "
            "from it alone")
    # Setup drag: quick to play means quick to START. Counted, not judged.
    max_setup = int(os.environ.get("SETUP_MAX_STEPS", "6"))
    setup_steps = re.findall(r"^\s*(?:\d+[.)]|[-*])\s+",
                             secs.get("Setup", ""), re.M)
    if len(setup_steps) > max_setup:
        bad("medium", "setup-drag",
            f"{len(setup_steps)} setup steps, budget is {max_setup} - a table "
            f"that takes longer to set than to play round one has already "
            f"lost half its nights")
    # The lid budget. dead-stop 2026-08-22: three critic rounds bought agency +1
    # with seats, lanes, spares, a seed and a rotation rule, and the read-aloud
    # grew to 520 words - inside GDD_MAX_WORDS, unreadable on a box lid. The
    # market's own criterion is "rules fit a quarter sheet"; this is that, in
    # numbers, on the one section a stranger actually reads.
    fm_max = int(os.environ.get("FIRST_MINUTE_MAX_WORDS", "220"))
    fm = " ".join(v for k, v in secs.items() if k.startswith("First minute"))
    if fm and len(fm.split()) > fm_max:
        bad("high", "first-minute-long",
            f"## First minute is {len(fm.split())} words, budget is {fm_max} - "
            f"it has to fit the box lid and be read aloud in one breath; cut a "
            f"rule, do not compress the prose")
    # Turn steps are concepts a player holds at once. Four is a full hand.
    ts_max = int(os.environ.get("TURN_MAX_STEPS", "4"))
    turn_steps = re.findall(r"^\s*\d+[.)]\s+", secs.get("Turn structure", ""), re.M)
    if len(turn_steps) > ts_max:
        bad("medium", "turn-steps",
            f"{len(turn_steps)} numbered steps in ## Turn structure, budget is "
            f"{ts_max} - every step is a concept the table holds at once")
    listed = set(re.findall(r"`([a-z0-9_]+)`", secs.get("Components", "")))
    if not listed:
        bad("high", "gdd-no-components",
            "gdd.md has no `## Components` section listing component ids in backticks")
    for extra in listed - idset:
        bad("high", "gdd-orphan", f"gdd.md names `{extra}` but components.json has no such id")
    for missing in idset - listed:
        bad("high", "manifest-orphan",
            f"components.json has `{missing}` but gdd.md `## Components` does not list it")

    decision_text = " ".join(v for k, v in secs.items()
                             if any(k.startswith(d) for d in DECISION_SECTIONS))
    for cid in idset:
        if cid not in decision_text:
            bad("high", "decoration",
                f"`{cid}` never appears in {DECISION_SECTIONS} - it changes no decision")

    # --- unbound quantities ----------------------------------------------
    for name, body in secs.items():
        if not any(name.startswith(d) for d in DECISION_SECTIONS):
            continue
        for n, line in enumerate(body.splitlines(), 1):
            if re.search(HEDGES, line, re.I):
                bad("high", "unbound",
                    f"[{name}] hedged quantity, needs a number: {line.strip()[:90]}")

    # --- plate budget -----------------------------------------------------
    plate = float(os.environ.get("PLATE_MM", "160"))
    for c in comps:
        bb = c.get("target_bbox_mm") or [0, 0, 0]
        if len(bb) == 3 and max(bb[0], bb[1]) > plate:
            bad("high", "plate",
                f"{c['id']} footprint {bb[0]}x{bb[1]}mm exceeds the {plate}mm plate")
    return issues


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    issues = check(out_dir, here)
    (out_dir / "consistency.json").write_text(json.dumps(issues, indent=2), encoding="utf-8")
    highs = [i for i in issues if i["severity"] == "high"]
    for i in issues:
        print(f"  [{i['severity']:4}] {i['code']}: {i['message']}")
    print(f"consistency: {len(highs)} high, {len(issues) - len(highs)} warn")
    return 1 if highs else 0


if __name__ == "__main__":
    sys.exit(main())
