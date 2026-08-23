"""Phase 1 prompts. One agent, one artifact, one job.

Split into specialists rather than one GDD author on GameGrammar's evidence
(MechanicsArchitect / ComponentDesigner / DetailsArchitect / BalanceCritic) and
on text2cad commit eb5aec1: a single agent scoring its own shortlist
rationalises instead of reviewing.
"""
import json
import os
import re
from pathlib import Path

import harness
from harness import HEADLESS

HERE = Path(__file__).resolve().parent
UTF8 = "utf-8"


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding=UTF8)


def _upto(name: str, heading: str) -> str:
    """A doc truncated at `heading`, so one file can serve two jobs.

    mechanisms.md carries the SYMPTOM and MITIGATE tables since 2026-08-20.
    MECHANISM LOCK must not see them: its job is to name what the seed already
    IS in this vocabulary, and a list of ways games break is an invitation to
    redesign the seed instead. The critic gets those tables; the lock does not.
    """
    return _read(name).split(heading, 1)[0].rstrip() + "\n"


def _from(name: str, heading: str) -> str:
    """A doc from `heading` to the end - the half `_upto` leaves behind."""
    return heading + _read(name).split(heading, 1)[-1]


def _evidence(out_dir: Path) -> str:
    """What previous designs of this pipeline already broke on, if anything.

    Added 2026-08-20. The critic used to reason from a blank page every run, so
    the same failures came back: a speech restriction reached for twice to fix
    `alpha_solve` and rejected by the critic both times, three designs
    `decided_early`, two shipping a `duplicate_state` part. None of it survived
    the run that found it.

    Two rules keep this from becoming the machine agreeing with itself. The
    current design is EXCLUDED - otherwise round 2 is handed round 1's own
    findings as though another game had produced them. And the block is capped,
    because a critic given the same ten edges every run will find those ten
    things and stop looking. Kill switch: CRITIC_EVIDENCE=off.
    """
    if os.environ.get("CRITIC_EVIDENCE", "").lower() == "off":
        return ""
    try:
        import harvest
        rows = [r for r in harvest.harvest(HERE) if r["slug"] != out_dir.name]
        if not rows:
            return ""
        f = out_dir / "mechanisms.json"
        # No lock yet is not an error: recall then falls back to whatever has
        # hit two or more designs, which is the part that is not about
        # mechanisms anyway.
        mechs = (json.loads(f.read_text(encoding=UTF8)).get("chosen") or []
                 if f.is_file() else [])
        block = harvest.recall(mechs, rows,
                               harvest.mitigations(_read("mechanisms.md")))
        return f"\n{block}\n" if block else ""
    except Exception as e:                                   # never kill a phase
        return f"\n(no evidence available: {type(e).__name__}: {e})\n"


_TAXONOMY = {}


def _taxonomy() -> list:
    """Display names of every mechanism node in the vault, [] without one.

    Fed to MECHANISM LOCK so the taxonomy bridge is declared at the source -
    the agent that just read the seed knows what the mechanism IS, and mapping
    there beats difflib guessing at the far end of the pipeline. Cached per
    vault path; the list changes when the vault gains nodes, which is rare
    enough that a process restart is an acceptable refresh.
    """
    root = str(Path(os.environ.get("GAMEVAULT", "/root/gamevault")))
    if root not in _TAXONOMY:
        names = []
        for f in sorted(Path(root).glob("vault/mechanisms/*.md")):
            m = re.search(r"^name:\s*(.+)$", f.read_text(encoding=UTF8), re.M)
            if m:
                raw = m.group(1).strip()
                try:
                    names.append(json.loads(raw))
                except json.JSONDecodeError:
                    names.append(raw.strip('"'))
        _TAXONOMY[root] = names
    return _TAXONOMY[root]


def _taxonomy_rule() -> str:
    """The bgg_taxonomy field in MECHANISM LOCK's contract, '' without a vault."""
    names = _taxonomy()
    if not names:
        return ""
    return f"""
--- taxonomy bridge ---
The ids above are this pipeline's private vocabulary. The design vault indexes
known failure modes by the PUBLIC BGG taxonomy instead, so also fill
`bgg_taxonomy`: for each chosen id, 0-2 names from this list that genuinely
describe the same mechanism, spelled exactly as printed. [] is a correct
answer - do NOT force a match, a wrong bridge poisons every downstream lead
with another mechanism's failure modes.
{", ".join(names)}
"""


def _vault(out_dir: Path) -> str:
    """Machine-checked leads from the design vault (/root/gamevault).

    Added 2026-08-21. Third knowledge source after the SYMPTOM tables and
    _evidence, and different in kind from both: the vault is a typed link
    graph (mechanism -> anti-pattern -> recorded fix), and this block is
    check_compatibility() output COMPUTED for this draft's mechanisms - zero
    LLM calls, zero cost, same doctrine as slice ("numbers from the machine,
    not the model"). The critic gets leads with node paths, not opinions.

    The soft spot is the name bridge: mechanisms.json `chosen` holds this
    pipeline's own vocabulary (ratchet_dial, peephole_screen), not BGG
    taxonomy. difflib at 0.75 maps what genuinely matches and drops the rest -
    a miss must stay visible (WARNING), never silent, but an invented-vocab
    design legitimately maps to nothing and the critic then simply runs
    without this block. The production constraint node rides along in every
    check, so a draft that maps onto a card-driven mechanism collides with
    "FDM only" straight from the graph.

    Kill switch: CRITIC_VAULT=off. Vault location: $GAMEVAULT.
    """
    if os.environ.get("CRITIC_VAULT", "").lower() == "off":
        return ""
    root = Path(os.environ.get("GAMEVAULT", "/root/gamevault"))
    if not (root / "vault_tools.py").is_file():
        print(f"  WARNING: no design vault at {root} - critic runs without "
              f"vault leads (set GAMEVAULT or CRITIC_VAULT=off)", flush=True)
        return ""
    try:
        import difflib
        import sys
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        import vault_tools as vt

        f = out_dir / "mechanisms.json"
        data = json.loads(f.read_text(encoding=UTF8)) if f.is_file() else {}
        chosen = data.get("chosen") or []
        if not chosen:
            print("  WARNING: mechanisms.json has no `chosen` - vault check "
                  "has nothing to map", flush=True)
            return ""

        # Three bridges, in order of trust: the taxonomy MECHANISM LOCK
        # declared while it still had the seed in front of it, then the
        # vault's slug/alias/fuzzy resolve(), then (old vault copies without
        # resolve) bare difflib. A name that clears none of them is reported,
        # never rounded to the nearest node.
        def _resolve(name):
            r = getattr(vt, "resolve", None)
            if r is not None:
                return r(name)
            tails = [p.split("/", 1)[1] for p in vt.all_nodes()
                     if p.startswith("mechanisms/")]
            hit = difflib.get_close_matches(
                str(name).lower().replace("_", "-"), tails, n=1, cutoff=0.75)
            return f"mechanisms/{hit[0]}" if hit else None

        declared = data.get("bgg_taxonomy") or {}
        mapped, unmapped = [], []
        for c in chosen:
            hits = []
            for nm in declared.get(str(c)) or []:
                r = _resolve(nm)
                if r:
                    hits.append(r)
                else:
                    print(f"  WARNING: MECHANISM LOCK declared taxonomy "
                          f"{nm!r} for {c!r} but the vault has no such "
                          f"node", flush=True)
            if not hits:
                r = _resolve(str(c))
                if r:
                    hits = [r]
            if hits:
                mapped.extend(h for h in hits if h not in mapped)
            else:
                unmapped.append(str(c))
        if unmapped:
            print(f"  WARNING: vault has no taxonomy match for {unmapped} - "
                  f"leads cover only {mapped or 'nothing'}", flush=True)
        if not mapped:
            return ""
        constraint = "constraints/fdm-printed-components-only"
        probe = mapped + ([constraint]
                          if (root / "vault" / f"{constraint}.md").is_file()
                          else [])
        lines = []
        for v in vt.check_compatibility(probe):
            if v["kind"] == "conflict":
                lines.append(f"CONFLICT: {' x '.join(v['nodes'])} - declared "
                             f"conflicts-with, cannot coexist in one ruleset")
            elif v["kind"] == "unmet-requirement":
                lines.append(f"MISSING: {v['nodes'][0]} requires "
                             f"{v['nodes'][1]}, which this design lacks")
            else:
                fixes = "; ".join(v["suggested_fixes"])
                lines.append(f"RISK: {v['nodes'][0]} -> {v['nodes'][1]} "
                             f"(recorded fix: {fixes})")
        body = "\n".join(lines) if lines else (
            "no declared conflicts or recorded risks for "
            + ", ".join(mapped))
        return f"""
--- the design vault says (machine-checked, not opinion) ---
mechanisms mapped to the vault taxonomy: {', '.join(mapped)}
{body}
Each line above is a LEAD, not a verdict: confirm it against THIS gdd. A
confirmed lead becomes an issue citing the vault node in `where`; a lead
that does not apply here, dismiss in one line of `issue` saying why.
"""
    except Exception as e:                                   # never kill a phase
        print(f"  WARNING: vault check failed ({type(e).__name__}: {e}) - "
              f"critic runs without vault leads", flush=True)
        return ""


def _seed(out_dir: Path) -> str:
    """Whatever DISCOVER already decided, verbatim. Never re-litigated here."""
    bits = []
    for name in ("seed.md", "brief.md"):
        p = out_dir / name
        if p.exists():
            bits.append("--- " + name + " ---\n" + p.read_text(encoding=UTF8))
    return "\n\n".join(bits) if bits else "(no seed on disk)"



def _title(out_dir: Path) -> str:
    """The NAME the DISCOVER panel put on the box, '' if it wrote none.

    The slug is a directory name. `switchyard-slit-scan` and `blind-bone-dig`
    are both real panel output and neither is a name anyone says out loud, so
    the name is now chosen where the game is chosen and carried from there
    rather than being whatever the slug happened to be.
    """
    f = out_dir / "discover.md"
    if not f.is_file():
        return ""
    m = re.search(r"^Name:\s*(.+)$", f.read_text(encoding=UTF8), re.M)
    if not m or m.group(1).strip().startswith("NOT "):
        return ""
    return m.group(1).strip()


def _box_face(out_dir: Path) -> str:
    """The box line and the first object out of the box, for the phases that
    have to keep faith with what the buyer was promised."""
    f = out_dir / "discover.md"
    if not f.is_file():
        return ""
    text = f.read_text(encoding=UTF8)
    bits = []
    for key in ("Box face", "First look"):
        m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        if m and not m.group(1).strip().startswith("NOT "):
            bits.append(f"{key}: {m.group(1).strip()}")
    return "\n".join(bits)


def skill(job: str, name: str = "cadcode") -> str:
    """How this job's agent gets the CAD handbook.

    Claude Code loads a skill by NAME - "Use the cadcode skill" is enough. Codex
    has no such mechanism, so on that provider the same sentence is a no-op and
    the session builds nothing. It is only the instructions that are missing,
    not the capability: SKILL.md is a plain CadQuery handbook with no
    Claude-specific content (checked 2026-08-19 - the only "claude" in it is the
    install path), and its interface is shell scripts codex can run. So point
    codex at the file instead of naming it.
    """
    if harness.provider_for(job) != "codex":
        return f"Use the {name} skill."
    root = Path.home() / ".claude" / "skills" / name
    return (f"""Read {root}/SKILL.md IN FULL before you write any geometry - it is
the CAD handbook for this job and you do not have it loaded. It links deeper
references under {root}/references/; read the ones it sends you to. Its scripts
run like this:

    uv run --python 3.12 --with cadquery python3 {root}/scripts/cad <file.py>
    uv run --python 3.12 --with cadquery python3 {root}/scripts/check <file.py>
    uv run --python 3.12 --with cadquery python3 {root}/scripts/measure <file.step> --gaps

Do not invent a different toolchain: the gate downstream runs these exact
scripts against what you export.""")



def lane_of(out_dir: Path) -> str:
    """The DISCOVER lane the winner came from, out of discover.md's table."""
    f = out_dir / "discover.md"
    if not f.is_file():
        return ""
    text = f.read_text(encoding=UTF8)
    m = re.search(r"^WINNER:\s*([a-z0-9-]+)", text, re.M)
    if not m:
        return ""
    row = re.search(rf"^\|\s*{re.escape(m.group(1))}\s*\|\s*([a-z]+)\s*\|",
                    text, re.M)
    return row.group(1).strip().lower() if row else ""


def _legacy_rule(out_dir: Path) -> str:
    """The permanent-change requirement, waived for the family lane.

    It exists so a printed game is worth owning rather than downloading. But
    applied to every lane it makes every game a legacy game, including the one
    lane whose whole brief is "rules a stranger learns in five minutes" - a
    campaign that remembers what happened is the opposite of that.
    """
    if lane_of(out_dir) == "family":
        return (" - WAIVED for this game: it came from the `family` lane, where a "
                "campaign that remembers previous sessions works against a game a "
                "stranger can be taught in five minutes. Pick one only if it "
                "genuinely makes the game better.")
    return ""


def mechanism(out_dir: Path) -> str:
    return f"""You are MECHANISM LOCK, phase 1.0 of a board game pipeline.

{_seed(out_dir)}

--- taste_boardgame.md ---
{_read("taste_boardgame.md")}

--- mechanisms.md ---
{_upto("mechanisms.md", "## SYMPTOM")}

Choose the 2-3 mechanism ids this game is actually built on. Rules:
- ids MUST come from the mechanisms.md vocabulary table, spelled exactly
- ZERO pairs from the COLLIDE table
- at least one from the permanent-change group{_legacy_rule(out_dir)}
- at least one from the INTERACTION group (`hand_off`, `blocking_claim`,
  `physical_bid`, `shared_push_track`, `opaque_sleeve`, `peephole_screen`).
  Without one, nothing a player does matters to anyone else and the game is
  several people playing solitaire at the same table. Measured 2026-08-19: a
  lock that picked the two strongest ids picked two solo ones, and the design's
  social score fell from 9 to 3 while every structural check still read clean.
- with both groups mandatory a two-id game is exactly one permanent-change and
  one interaction. THREE is the ceiling, not the target: a third id buys a
  randomiser or a physical-state mechanism and must earn it. The last game
  locked four and its rules ran to 3,788 words.
- you must be able to say in ONE sentence how the chosen ids interact to
  produce a decision a player agonises over. If you cannot, you picked wrong.

The seed above already won a judge panel - your job is to name what it IS in
this vocabulary, not to redesign it. If the seed's mechanism has no id here,
pick the closest and say so in `notes`.
{_taxonomy_rule()}
WRITE {out_dir}/mechanisms.json exactly:
{{"chosen": ["id1","id2"], "interaction": "one sentence", "notes": "optional"{', "bgg_taxonomy": {"id1": ["Taxonomy Name"], "id2": []}' if _taxonomy() else ""}}}

{HEADLESS}

Write the file. Do not print it and stop."""


def _legacy_section(out_dir: Path) -> str:
    """The `## Legacy` heading, only for the lane that is about legacy.

    It was mandatory for every lane, so every game got a campaign whether its
    design wanted one or not - and an empty mandatory section does not stay
    empty, something arrives to fill it. Non-legacy lanes now do not have the
    heading at all rather than being told to write "None".
    """
    if lane_of(out_dir) == "legacy":
        return ("## Legacy            - what changes permanently and what "
                "triggers it\n")
    return ("(NO `## Legacy` section. This game is not a campaign: nothing "
            "carries over between sessions, nothing is destroyed, no component "
            "is consumed for good. If the design genuinely needs permanent "
            "change to work, say so in your reply and stop - do not add a "
            "campaign layer quietly, it is the largest block of rules a player "
            "has to learn.)\n")


def _tone(role: str) -> str:
    """DISCOVER's run tone, carried into the two phases that can delete it.

    The tone is a property of WHAT to make, so it belongs with the seed and the
    box face, not with the build lessons. It has to travel: DISCOVER can pick a
    funny game and phase 1.4 will then sand the comedy off it over three
    rounds, because the reviser optimises for a clean referee and a high craft
    score and nothing anywhere tells it the joke was the point.

    Single source of truth is discover.tone_block(); imported lazily because
    discover pulls in trends and the BGG index at module scope.
    """
    try:
        import discover
        block = discover.tone_block()
    except Exception:
        return ""
    if not block:
        return ""
    return block + f"\n\nThis is why this game was picked over the others on the "\
                   f"shortlist. As the {role} you may not quietly trade it away: a "\
                   f"change that fixes a finding and removes the tone is not a fix, "\
                   f"and if the only correct fix does remove it, say so instead of "\
                   f"making it silently.\n"


def gdd(out_dir: Path) -> str:
    locked = (out_dir / "mechanisms.json").read_text(encoding=UTF8)
    title = _title(out_dir) or "<the game's name>"
    face = _box_face(out_dir)
    promised = ("\n" + face + "\n\nThat is what the buyer was promised before any "
                "of these rules existed, and it is the only description of this "
                "game a stranger will ever read. You may not contradict it: if "
                "the design has moved somewhere those lines no longer describe, "
                "say so in your reply rather than quietly writing past them.\n"
                ) if face else ""
    return f"""You are the GDD author, phase 1.1. Write the game design document.

{_seed(out_dir)}
{_tone('GDD author')}

--- the mechanisms this game is locked to ---
{locked}

--- taste_boardgame.md ---
{_read("taste_boardgame.md")}

WRITE {out_dir}/gdd.md. Its FIRST line is `# {title}`
- the name the panel put on the box, unchanged. Do not rename the game and do
not turn the name back into a description of its mechanism.
{promised}
Then EXACTLY these `##` sections, in this order:

## Overview          - what the players are doing, 3 sentences
## Players and time  - exact player counts and minutes
## First minute      - the one-sentence pitch, then turn 1, written to be read
                       ALOUD: a stranger plays their first turn correctly from
                       this section alone, without opening the rest. The
                       referee will play game 1 from it and nothing else, and
                       a checker fails a document that lacks it.
## Components        - every distinct printed design as `snake_case_id` in
                       backticks, one per line, with its qty and one-line job.
                       This list is the contract; nothing later may invent a part.
## Setup             - how the table starts, by component id
## Turn structure    - named phases in order, what a player may do in each
## Action economy    - the numbers: how much of what, per turn, per player
## Win/lose          - exact conditions and values
{_legacy_section(out_dir)}## Edge cases        - ties, exhausted supply, last round, a player who cannot act
## Glossary          - any term you invented. Aim for ZERO: every entry here is
                       a word the table has to learn before the first turn, and
                       a checker fails this document above 5.

PARTS BUDGET: {os.environ.get("PARTS", "6-10")} DISTINCT printed designs (30
identical tokens is ONE design), and a checker enforces the upper bound. Aim at
the LOW end. A part is a rule and a rule is teaching time: this was never
checked until 2026-08-20, and the game that shipped 13 designs was read at
teach 4 out of 10 while the one that shipped 6 was read at 8.

NUMBERS BUDGET: {int(os.environ.get("GDD_MAX_RULE_NUMBERS", "140"))} numbers
across Setup / Turn structure / Action economy / Win-lose / Legacy / Edge
cases, counted by a checker. Read that together with the rule below: the way
to spend fewer numbers is FEWER RULES, never vaguer ones. Rounding "3 clicks"
to "a few clicks" fails the vagueness check instead, and both checks are
enforced in the same pass.

BUDGET: {int(os.environ.get("GDD_MAX_WORDS", "1800"))} words for the whole
document, and a checker enforces it. This is not a style note - the last game
this pipeline wrote ran to 3,788 words with an 11-term glossary and arithmetic
in its win condition, and nobody could teach it. Spend the budget on the turn
loop. If the rules do not fit, the GAME is too big: cut a subsystem and say in
your reply which one you cut, rather than compressing the prose.

THE ONE RULE THAT MATTERS: every rule carries a NUMBER. A checker will fail this
document on the words: some, several, a few, a number of, multiple, various,
limited, enough, appropriate, reasonable, sufficient, many, plenty, roughly,
about, approximately, as needed, or so.

  REJECTED: "the beam sweeps a limited arc"
  ACCEPTED: "the beam sweeps 60 degrees per winder click, 3 clicks per keeper"

Every component id you list in `## Components` MUST also appear in at least one
of Turn structure / Action economy / Win/lose / Legacy. A part that only appears
in Setup is decoration and the checker will fail it.

No cards. No cardboard. No bought dice. No app, screen or battery. Every
component is FDM printed and no part exceeds 160x160x180mm. Two commodity
exceptions, only when load-bearing: neodymium disc magnets and standard rubber
bands, each with an exact spec and a printed pocket that holds it.

ONE RULE, ONE PLACE. State each rule exactly once - in `## Turn structure` or
`## Win/lose` - and have `## First minute` and `## Edge cases` QUOTE that sentence
verbatim or point at it; never paraphrase a rule in a second section. Measured on
dead-stop 2026-08-22: every CONTRADICTION the referee found, across five passes,
was one rule (what happens to a landed crate; when the game ends) phrased three
or four ways in three or four sections. A rule that exists in two wordings is
two rules, and the referee will find the turn on which they disagree.

THE RULES FIT THE LID. `## First minute` is at most
{int(os.environ.get("FIRST_MINUTE_MAX_WORDS", "220"))} words and `## Turn
structure` at most {int(os.environ.get("TURN_MAX_STEPS", "4"))} numbered steps
- both checked by a machine. PHYSICS FIRST: this is a physical game, so the
trade-off lives in the object - a heavier load spills wilder, a taller stack
wobbles more - and the decision each turn may be ONE number. If the only way to
make a choice matter is a price table, a seat menu, a spare pool or a second
scoring axis, the OBJECT is wrong, not the rules: say so instead of writing it.

THE GAME PUTS ITSELF AWAY. Every component must have a printed home between
games — nesting, stacking, a lidded part, the board itself — and the rules must
ride ON a part: engraved, or a slot holding the one printed rules plate. Design
the home now; the manifest will be forced to name where every part lives, and
a checker fails a homeless part.

{HEADLESS}

Write the file. Do not print it and stop."""


def manifest(out_dir: Path) -> str:
    face = _box_face(out_dir)
    signature_note = ("\n\nThe panel already named the object it expected to "
                      "carry this game:\n" + face + "\nUse it unless a rule you "
                      "have since read makes it the wrong part, and say so if "
                      "you overrule it.") if face else ""
    return f"""You are the COMPONENT DESIGNER, phase 1.2.

Read {out_dir}/gdd.md. Turn its `## Components` section into a printable
contract. You may NOT add a component that gdd.md does not list, and you may
NOT drop one it does.

WRITE {out_dir}/components.json - a JSON array, one object per DISTINCT printed
design (30 identical tokens is ONE design with qty 30). The budget is
{os.environ.get("PARTS", "6-10")} designs and a checker enforces it - if
gdd.md lists more than that, do NOT silently write them all: write the file and
say in your reply that the GDD is over budget and which part earns its rules
least.

[{{
  "id": "beam_disc",                 exactly the id used in gdd.md
  "qty": 1,
  "role": "one line - what it does in play",
  "class": "functional" | "sculptural",
  "duty": "the PHYSICAL requirement, testable: 'holds 2N reverse torque
           without slipping', 'snaps at hand force and cannot reseat'",
  "tolerance_mm": 0.3,               the clearance its job survives
  "target_bbox_mm": [120, 120, 8],   x,y,z - x and y must be <= 160
  "mates_with": ["winder_dial"],     ids it physically touches; be symmetric
  "stores_in": "beam_disc",          where this part LIVES between games:
                                     another component's id, or "self"
  "rules_carrier": true,             EXACTLY ONE component - the part the rules
                                     ride on (engraved, or a slot holding the
                                     one printed rules plate)
  "external": {{"item": "magnet",     ONLY if the part embeds one of the TWO
    "spec": "6x3mm N35 disc",        allowed commodities (magnet|rubber_band).
    "qty_per": 2}},                   spec is EXACT; a checker fails a vague or
                                     missing one, and bans everything else
  "signature": true                  EXACTLY ONE component in the game
}}]

STORAGE IS PART OF THE CONTRACT. Every component names its home (`stores_in` -
a checker fails a homeless part), and exactly one component carries the rules
(`rules_carrier`). If gdd.md never designed a home, that is a finding about
the GDD - say so in your reply rather than inventing storage it cannot hold.

THE SIGNATURE PART. Mark exactly one component `"signature": true` and leave the
key off every other one. It is the object this game is remembered BY: the thing
in the photo, the thing a player picks up first, the thing someone describes to
a friend when they cannot remember the name. Monopoly's gameplay was overtaken
decades ago and the little metal dog, the money and GO still sell it - what a
box owns is one recognisable object, not thirteen good ones.

Choose it by what a stranger would point at, and it MUST be a part the turn loop
actually runs on: a signature part that no rule in `## Turn structure` touches is
a mascot, and a checker fails it. If the honest answer is that nothing here is
memorable, say so in your reply - that is a finding about the design, not a
field to fill in.{signature_note}

class rules - this decides which pipeline builds it in phase 2:
- "functional" = anything that mates, clicks, ratchets, snaps, holds tolerance,
  or has to fit another part. Built parametrically in CadQuery. MOST PARTS.
- "sculptural" = pure look, touches nothing, tolerance irrelevant (a figurine,
  a themed marker). Built from a concept image through TRELLIS, which returns
  shell-soup meshes - useless for anything that must fit.
  HARD CAP: at most 3 sculptural parts in the whole game. The image route runs
  on HF ZeroGPU at ~2-3 runs per DAY. Spend that budget on the parts where
  likeness actually sells the box.

If unsure, mark it "functional". A wrongly sculptural part cannot be repaired
later - it comes back as a mesh that will not mate.

{HEADLESS}

Write the file. Do not print it and stop."""


def todo(out_dir: Path) -> str:
    return f"""You are the BUILD PLANNER, phase 1.3.

Read {out_dir}/components.json and {out_dir}/gdd.md.

WRITE {out_dir}/todo.md - the implementation order for phase 2. Group the
components into build phases and order them so that:
- a part is never built before the part it mates with is dimensioned
- parts that share a mating interface are built adjacent, never far apart
- the part the most other parts reference is built FIRST

For each build phase write:
  ### Phase N - <name>
  parts: `id`, `id`
  depends on: <earlier phase or "nothing">
  exit criteria: the concrete, checkable thing that must be true to move on
                 (e.g. "winder_dial and beam_disc mate with 0.3mm clearance
                  measured by scripts/measure --gaps")

Exit criteria must be measurable by a machine, not judged by eye.

The measuring machine is ONE command and it has exactly THREE switches:

  scripts/measure <file.step>            per-part name, bbox, volume, colour
  scripts/measure <file.step> --gaps     pairwise clearance and overlap
  scripts/measure <file.step> --part ID  restrict to one part
  scripts/measure <file.step> --near N   only pairs closer than N mm

There is nothing else. Do NOT invent a switch. Measured 2026-08-20 on
`precedent`: this prompt named `--gaps` once and left the rest to be guessed,
and the todo.md that came back cited `--all-copies`, `--bbox`, `--load`,
`--two-sided`, `--require`, `--mouths`, `--interfaces`, `--cycles`, `--trials`
and `--sockets` - ten switches that do not exist. The build agent then spent
its own turns discovering that, one at a time, inside a session that has no
turns to spare.

An exit criterion you cannot phrase with those four forms is not measurable
here. Phrase it as a bbox, a clearance or an overlap - those are what the tool
returns - or drop it and say in the phase what a human has to look at instead.

{HEADLESS}

Write the file. Do not print it and stop."""


def _campaign_rule(out_dir: Path) -> str:
    """For a game with a `## Legacy` section, one complete game IS the campaign.

    Measured 2026-08-20 on `precedent`: the referee wrote `## Game 1/2/3` -
    three single nights - and returned CLEAN three rounds running. The design
    ships 9 `gate` pieces, bolts 4 at setup and runs a campaign of up to 6
    nights installing one per night: 4 + 6 = 10, and there are 9. The build
    agent found it in phase 2, while making the parts, because building forces
    you to count them. "Play 3 complete games" reads as three sessions when the
    product is a campaign, and the last night is exactly where a supply runs
    out.
    """
    f = out_dir / "gdd.md"
    if not f.is_file() or "## Legacy" not in f.read_text(encoding=UTF8):
        return ""
    return """

THIS IS A CAMPAIGN. `gdd.md` has a `## Legacy` section, so one COMPLETE GAME
means the campaign played from the first session to its stated end - not one
session. Play each of them all the way through, carrying every permanent change
forward, and keep the running count of every component that is consumed,
installed or destroyed.

Then check the supply explicitly, because this is where a campaign breaks and a
single session never will: for every component the campaign consumes, does its
`qty` in components.json actually cover setup PLUS every session to the end? If
it does not, that is a MISSING INFO finding and you must show the arithmetic."""


def referee(out_dir: Path, n_games: int) -> str:
    return f"""You are the REFEREE, phase 1.4b. You are NOT a critic and NOT a
playtester - GameGrammar is right that no algorithm simulates four people at a
table, and you are not pretending to. You are a RULES EXECUTOR looking for
states the document cannot resolve.

Read ONLY {out_dir}/gdd.md and {out_dir}/components.json. Do not read any other
file, do not read the taste guide, do not judge whether the game is fun.

Play {n_games} complete games, move by move, at the stated player count.{_campaign_rule(out_dir)} Keep an
explicit state after every turn (what is where, who holds what, every counter).
Play them DIFFERENTLY: one cautious, one aggressive, one that deliberately
targets whatever the rules leave loosest.

GAME 1 IS THE COLD OPEN. Play it from the `## First minute` section plus the
component list ALONE, the way a stranger handed the box would. Open the rest of
the document only when that section fails to answer a situation game 1 actually
reaches - and every time it fails, that is a MISSING INFO finding naming
exactly what the stranger lacked. Games 2 onward use the full document.

Report ONLY these five failure kinds:
1. CONTRADICTION - two rules give different answers to the same situation
2. DEAD STATE     - a legal position from which no legal move exists
3. UNREACHABLE    - a win condition that cannot be reached from setup
4. ILLEGAL TURN   - a turn that cannot be legally ended as written
5. MISSING INFO   - a rule needs information no listed component can carry
                    (e.g. tracking a number with nothing to track it on)

WRITE {out_dir}/referee.md:
  ## Game 1 .. ## Game {n_games}   - the turn log, terse, one line per turn
  ## Findings                      - one `### <KIND>` block each, with the exact
                                     turn it occurred and the rule text at fault
  ## Verdict                       - the single line `CLEAN` if all {n_games}
                                     games completed with zero findings,
                                     otherwise `FINDINGS: <n>`

If a game cannot be completed, that is itself a finding - say where it stopped.

YOU PLAY THE GAMES. You have no subagents and nothing will report back to you:
there is no background worker, no /loop, no completion notification, no second
session. Measured 2026-08-19: two referee runs spent 2363s and 2521s ($6.46
between them) waiting for background agents that were never spawned, and wrote
no file at all, so the round was scored on the PREVIOUS round's referee.md.
Play turn 1 of game 1 in your next turn, on your own, in this session.

{HEADLESS}

Write the file. Do not print it and stop."""


def critic(out_dir: Path) -> str:
    return f"""You are the BALANCE CRITIC, phase 1.4c.

Read {out_dir}/gdd.md and {out_dir}/components.json.

Find what is BROKEN about this design as a game, not as a document.

--- the failure vocabulary ---
{_from("mechanisms.md", "## SYMPTOM")}
Every issue you report MUST name one `symptom` id from the PLAY table above.
The ids are the whole point: they are what makes this round comparable to the
last one and to every game this pipeline has built. If nothing fits, use the
closest id and say in `issue` that it does not really fit - that is a hole in
the vocabulary and worth knowing about.

The MITIGATE table is the part that is easy to get wrong. Every fix has a
price, and a fix whose price is worse than the symptom is not a fix. If you
propose something that table already lists, you are expected to pay its cost
too - say so in `fix`.
{_evidence(out_dir)}{_vault(out_dir)}
Rate every issue and give the FIX, not the complaint. A severity is a claim
about the play experience, so justify it in the same line.

PHYSICS FIRST. This pipeline builds PHYSICAL games. Before you file
`dominant_action` or `trap_option`, ask whether the OBJECT already prices the
choice - a heavier hull spills wilder, a taller stack wobbles more. If it
plausibly does, that is not a rules finding: file it as `physics_untested` at
severity `low` and let the table answer it. A fix that adds a price list, a
currency, a seat menu, a spare pool or a second scoring axis is NOT an accepted
fix for a physical game - propose a change to the PART (mass, rail height,
spill geometry) or propose nothing. Measured 2026-08-22 on dead-stop: three
rounds of exactly those fixes bought agency +1 and cost replayability -2, five
contradictions and a 520-word read-aloud.

WRITE {out_dir}/critic.json:
[{{"severity": "high"|"medium"|"low",
   "symptom": "one id from the PLAY table",
   "issue": "one sentence",
   "where": "the section or component id",
   "fix": "the concrete change - a number to move, a rule to add"}}]

`high` means the game is not worth printing until it is fixed. Use it only for
that. Two highs on a design this early is normal; ten means you are padding.

{HEADLESS}

Write the file. Do not print it and stop."""



# GameGrammar's Design Evaluator, minus the parts that do not survive an
# unattended pipeline. Their six dimensions are kept verbatim because they are
# a published, reasoned set; `teach` is added because it is the axis this
# pipeline was shipping badly, and DISCOVER can only score it on a PITCH.
DIMENSIONS = ("depth", "tension", "agency", "replayability", "social",
              "elegance", "teach")


def evaluate(out_dir: Path, round_n: int, dest: str = "evaluate.json") -> str:
    return f"""You are the DESIGN EVALUATOR, phase 1.4d, round {round_n}.

Read ONLY {out_dir}/gdd.md and {out_dir}/components.json. Do not read the taste
guide, do not read the seed, do not read the other reviewers' files. You are
scoring the design AS WRITTEN, not the idea it came from.

You cannot play this game and you are not pretending to. You are recognising
design patterns that tend to produce experiences - hidden information tends to
produce tension, a real choice every turn tends to produce agency - and saying
how strongly this document shows them.

Score 0-10 on each, with ONE sentence of evidence quoting the rule that decides
the score:

- depth        - do decisions have consequences a player can plan around, or is
                 the outcome mostly delivered by the randomiser?
- tension      - is there a moment each turn where the table cares what happens?
- agency       - can a player change their own outcome, or only watch it arrive?
- replayability- is the tenth game different from the second, and WHY - by the
                 rules, not by hope?
- social       - do players interact, or play solitaire next to each other? For
                 a co-op, score whether one confident player can solve it aloud.
- elegance     - rules per decision. 10 = few rules generating many decisions;
                 1 = many rules generating few.
- teach        - minutes to teach a stranger. 10 = under 5 and the first turn is
                 played right; 4 = 20 minutes or a reference stays open; 1 = a
                 private vocabulary must be learned first.

SCORE WHAT IS THERE, not what could be added, and not what the pitch promised.
A number you cannot point at a rule for is a number you invented.

`one_change` IS AN INSTRUCTION, not an observation. The reviser is told to apply
it unless it contradicts a `high` finding or a locked mechanism, so a change
this pipeline cannot build costs a whole round. Two constraints on it, and on it
only - keep SCORING blind, as above:

1. EVERY component is FDM 3D printed. There are no cards, no paper, no
   cardboard, no printed sheets, no bought dice, and engraved text is coarse -
   a few words or icons, never a paragraph. Measured on coach-party round 1: a
   reader prescribed "add a one-card walkthrough", the reviser had to spend its
   reply explaining that cards do not exist here, and that reader's turn bought
   the design nothing.

2. If `teach` is the weakest dimension, the fix is REMOVING RULES - fold two
   exceptions into one always-legal action, delete an action category, cut a
   number. It is NOT a player aid, a reference card, a summary tile or a
   scripted demonstration. Read your own rubric: `teach` 4 IS "a reference stays
   open on the table". Prescribing a reference to raise teach argues for the
   score you just gave. Measured on coach-party rounds 1 and 2: four of six
   reads named teach weakest and then asked for an aid, teach did not move
   either round, and `social` fell 9 -> 8 while it did not.

WRITE {out_dir}/{dest} exactly:
{{"round": {round_n},
  "scores": {{{", ".join(f'"{d}": 0' for d in DIMENSIONS)}}},
  "evidence": {{"depth": "the rule that decides this score", "...": "..."}},
  "weakest": "the dimension name that scores lowest",
  "one_change": "the single concrete change that would raise it most"}}

{HEADLESS}

Write the file. Do not print it and stop."""


def revise(out_dir: Path, round_n: int) -> str:
    return f"""You are the REVISER, phase 1.4, round {round_n}.
{_tone('reviser')}

FOUR checkers ran against the design:
- {out_dir}/consistency.json - machine checks, every `high` MUST be resolved
- {out_dir}/referee.md       - rules-execution failures
- {out_dir}/critic.json      - balance issues, only `high` blocks
- {out_dir}/evaluate.json    - three independent readers SCORED the design

READ evaluate.json FIRST and act on its `weakest` dimension before anything
else. Each of the three reads also wrote `evaluate_r{round_n}_*.json` carrying
a `one_change`: the single concrete change that reader thinks would raise the
weakest score most. Those are the only instructions here written by someone who
read the rules as a PLAYER rather than as a checker, and until 2026-08-20 the
reviser was never shown them - keep-the-light-relay was told, three times, that
its weakest axis was `teach` and that the fix was to delete the double watches
and the cradle's three-use exception. Nobody read it and it shipped at teach 4.

Apply the `one_change` unless it contradicts a `high` finding, contradicts a
locked mechanism, or asks for something this pipeline cannot print - the readers
score the rules blind and have twice now prescribed a paper card. Saying why in
revisions.md is enough; you do not have to invent a printed substitute for an
aid the design should not need. If you do not apply it, say why in revisions.md - "I disagreed" is
an answer, silence is not.

A `spread` of 3 or more on a dimension is not noise: three readers of the same
document disagreeing that far means the rules do not SAY whether the game has
that property. Fix the writing, not the score.

Fix {out_dir}/gdd.md, and {out_dir}/components.json where a fix changes a part.
Rules:
- keep the locked mechanisms in mechanisms.json - if a fix truly requires
  changing them, do NOT: write `## Blocked` at the end of gdd.md saying why, and
  stop. That is a decision for a human.
- a `decoration` finding means the part earns a decision or it LEAVES. Deleting
  it from both files is the preferred fix; do not invent a token rule to save it.
- exactly one component keeps `"signature": true`. If a fix deletes the part
  that had it, move the flag to whatever the game is now recognisable by - do
  not leave the box with no face, and do not flag two.
- an `unbound` finding means choose the number. Choose it, do not rephrase.
- ONE RULE, ONE PLACE. When you change a rule, change it in the one section
  that owns it and re-quote it verbatim wherever it is repeated - a fix that
  leaves an older wording behind in `## First minute` or `## Edge cases` has
  manufactured a CONTRADICTION for the next referee (dead-stop, five passes).
- NEVER ADD A SUBSYSTEM. One-in-one-out: a fix that adds a numbered rule
  deletes one. A fix that needs a new currency, a price table, a seat menu, a
  spare pool or a second scoring axis is REFUSED and logged in revisions.md -
  for a physical game the trade-off lives in the part (mass, rail height,
  spill geometry); change the part in components.json or leave the question
  to the table. `## First minute` stays under the lid budget and `## Turn
  structure` under the step budget; a checker fails both.
- keep every gdd.md section heading exactly as it was.
- do not fix a `medium` or `low` if it costs you a `high`.

WRITE the revised files, then append to {out_dir}/revisions.md a `## Round
{round_n}` section: one line per issue with what you changed, and one line per
issue you deliberately did NOT change, with why.

{HEADLESS}

Write the files. Do not print them and stop."""


def priorart(out_dir: Path) -> str:
    return f"""You are PRIOR ART, phase 1.5. One job: find this game for sale.

Read {out_dir}/gdd.md and {out_dir}/mechanisms.json.

WebSearch for a published or listed game that is the SAME PRODUCT - same core
mechanism doing the same job - on BoardGameGeek, Kickstarter, Gamefound, Amazon,
Etsy, Printables, MakerWorld, Thingiverse. Run at least 6 distinct searches:
the mechanism combination in plain words, the theme plus the mechanism, and the
physical gimmick on its own.

"Same product" is NOT "same category". A co-op game is not a match. A lighthouse
game is not a match. A game where players pass ONE limited-reach light down a
line against a one-way clock IS a match. Without this line every candidate dies.

WRITE {out_dir}/priorart.json:
{{"verdict": "clear" | "exists",
  "nearest": "the closest thing you found, one line",
  "nearest_url": "url or empty",
  "evidence": [{{"query": "...", "found": "...", "url": "..."}}]}}

verdict "exists" REQUIRES a real url of the actual product. A suspicion with no
url is `clear` with the suspicion recorded in `nearest` - not finding something
is weak evidence, finding it is positive evidence, so only a finder gets to kill.

{HEADLESS}

Write the file. Do not print it and stop."""


# ---------------------------------------------------------------- phase 2

def _mating_pairs(out_dir: Path) -> str:
    """Which DIFFERENT components touch, computed in Python rather than guessed.

    art_direction picks one colour per id and never saw which ids sit against
    each other. On `precedent` 2026-08-20 it gave `gate` and `evidence_hopper`
    one hex and `verdict_pan` and `bench_half` another, reasoning in the doc
    that "repetition is deliberate - shared colours make separate prints read
    as one apparatus". The coherence lens then returned 4/10 for exactly that:
    the parts collapse into one shell. Both agents were arguing about pairs
    neither of them had been shown.
    """
    f = out_dir / "components.json"
    if not f.is_file():
        return ""
    try:
        comps = json.loads(f.read_text(encoding=UTF8))
    except json.JSONDecodeError:
        return ""
    if isinstance(comps, dict):
        comps = comps.get("components", [])
    pairs, seen = [], set()
    for c in comps:
        a = c.get("id")
        for b in c.get("mates_with") or []:
            if a == b or frozenset((a, b)) in seen:
                continue
            seen.add(frozenset((a, b)))
            pairs.append(f"{a} <-> {b}")
    if not pairs:
        return ""
    return ("\n\nTHESE PAIRS TOUCH IN THE ASSEMBLY (from mates_with):\n  "
            + "\n  ".join(pairs) +
            "\n\nThese pairs are the WORST place to repeat a hex, not the only "
            "one. Every DISTINCT component id gets a colour a player can tell "
            "apart from every other id across a table. Two copies of the SAME "
            "part may share a colour - two bench halves clipping together "
            "should - but two different ids may not, touching or otherwise.\n\n"
            "This paragraph used to end 'repetition can still unify the box: "
            "repeat a colour across parts that are NOT in this list', and "
            "coach-party 2026-08-20 followed it exactly - `through_hut` and "
            "`bell_ratchet_church` both #183B56, the doc explaining that 'ink "
            "blue repeats only on the non-touching hut and church to bind the "
            "architecture together'. The lens came back 3/10: 'the through "
            "huts and bell-ratchet church are hard to distinguish at a glance "
            "because both collapse into nearly black-blue'. The lens is not "
            "looking at what touches. It is looking at ONE PHOTOGRAPH, where "
            "two blue buildings are two blue buildings. Unify the box with "
            "value, finish and family instead - a palette that shares a "
            "temperature, not parts that share a hex.")


def _lens_feedback(out_dir: Path) -> str:
    """The coherence verdict from a previous attempt, if there was one."""
    f = out_dir / "lens_coherence.md"
    if not f.is_file():
        return ""
    text = f.read_text(encoding=UTF8).strip()
    return ("\n\nA PREVIOUS PALETTE WAS ALREADY JUDGED. This is what the "
            "coherence lens said about it - the score is out of 10 and "
            "anything under 6 stops the run:\n\n" + text[:1400] +
            "\n\nYou are rewriting the palette BECAUSE of that verdict. Fix "
            "what it named. Do not re-argue it.")


def art_direction(out_dir: Path) -> str:
    return f"""You are ART DIRECTION, phase 2.0.

Read {out_dir}/gdd.md and {out_dir}/components.json.

Thirteen printed designs have to read as ONE product on a table, not as a
parts bin. Lock the look once, here, so every later render and every colour
in part_colors.json comes from the same decision.{_mating_pairs(out_dir)}{_lens_feedback(out_dir)}

WRITE {out_dir}/art_direction.md:

## Palette
One colour per component id, as hex, with the filament it stands for. Rules
learned the hard way on this box: warm hues 25-65 degrees merge with PLA-grey
under render lighting, so do not put two load-bearing parts in that band; and
a part a player must FIND in a hurry gets the highest contrast in the box.

## Signature
The component carrying `"signature": true` in components.json is what this box
is remembered by. Say how the palette makes it the first thing an eye lands on
in a photo of the assembled game, and give it the strongest treatment in the
box - colour, contrast or finish, whichever the silhouette can carry. Nothing
else may compete with it.

## Silhouette
What the assembled game looks like from across the room, in two sentences.

## Finish
Matte FDM with visible layer lines. Say which parts get a texture and why.

## Per part
One line each: `id` - colour - the one visual job it does.

{HEADLESS}

Write the file. Do not print it and stop."""


def stage_layout(out_dir: Path) -> str:
    idx = out_dir / "parts_index.json"
    sizes = ""
    if idx.is_file():
        try:
            d = json.loads(idx.read_text(encoding=UTF8))
            sizes = "\n".join(
                f"  {k:24} qty {v.get('qty'):>3}   bbox {v.get('bbox')} mm"
                for k, v in d.items())
        except json.JSONDecodeError:
            pass
    return f"""You are the STAGER, phase 2.4. Put the game out on the table.

Read {out_dir}/gdd.md - the `## Setup` section first, then `## Turn structure`
for anything Setup leaves implicit - and write ONE file that says where each
piece goes. Nothing else in this pipeline knows this. `assembled.step` holds
every part at whatever coordinate the build agent left it at, which is an
assembly reference: on coach-party it had four street tiles that were never
clipped into a square and four huts lying in a row beside the board instead of
mounted on it. The coherence lens read that picture and returned 3/10.

THE PARTS AND THEIR REAL SIZES (millimetres, measured off the built meshes):
{sizes or "  (no parts_index.json - read components.json instead)"}

WRITE {out_dir}/stage.json, exactly this shape:

{{"units": "mm",
  "source": "one line naming the Setup steps you followed",
  "items": [{{"part": "<id>", "at": [x, y, z], "rot": 0, "tilt": 0}}, ...]}}

  `at`   the piece's FOOTPRINT CENTRE in x and y, and its BASE in z - the
         bottom face, not the middle. z = 0 is the table. A piece resting on
         an 8mm-thick tile has z = 8.
  `rot`  degrees about the vertical axis. Use it to face a part somewhere:
         a hut whose front door must face the middle of the board.
  `tilt` degrees about X, for anything that stands up or bolts onto a vertical
         face. Omit it (or 0) for a piece lying on the table.

RULES:

1. ONE ENTRY PER PHYSICAL PIECE. Nine villager pawns are nine entries. Use the
   qty above; do not place more of a part than the box contains.
2. USE THE REAL SIZES. Two 150mm tiles clipped edge to edge have centres 150mm
   apart, so a 2x2 square of them is 300x300 and its tile centres are at +-75.
   Pieces may not overlap: work out the extents from the bboxes above.
3. FOLLOW SETUP LITERALLY. If it says the tower goes in the centre, it goes at
   the centre - it is usually there because it BLOCKS SIGHT between the seats,
   and putting it anywhere else changes the game.
4. IT IS A PHOTOGRAPH OF A GAME BEING PLAYED, not of a box being unpacked. If
   the first thing that happens is a spill, some of what spilled is on the
   board. A piece that lives inside a container at setup stays inside it and is
   not placed loose on the table - that would be a lie about the setup.
5. NOTHING MAY STAND BETWEEN THE CAMERA AND THE BOARD. The camera looks down
   from above the +x,-y corner. A tall dispenser parked along the -y edge hides
   the entire game behind it; park it along +x or +y instead.
6. LEAVE OUT what the rules keep out of sight, and say so in `source`.

Write the file. Do not print it and stop.

{HEADLESS}"""


def video_qa(out_dir: Path, sheet: str, rule: str) -> str:
    """Judge one generated clip against the parts and against the rule.

    There was no gate on the video at all until 2026-08-21. Measured on
    coach-party beat 1 by pulling four frames afterwards: the coach is a closed
    box at t=1 and an open see-through cage at t=4; the rules spill exactly five
    visitors and by t=10 there are visibly more; the pawns grow through the
    clip; they settle leaning on the church, which nothing could roll to from
    the ramp. Every one of those is a picture of a product nobody will receive,
    which is the failure howto_anim.py wrote down a month ago and nothing was
    watching for.

    The reference cell is the STAGED render - the real meshes, the locked
    colours, the count the box actually contains - so "is this the same object"
    is a question with an answer rather than an impression.
    """
    verdict = sheet.replace(".png", ".json")
    # Name every part's colour. The judge reasons in colour words - "the yellow
    # pawns never move" - and on 2026-08-21 it inverted two of them, calling the
    # chartreuse villagers "visitors" and the ivory visitors "villagers". Six of
    # its nine findings were then about the wrong pieces. The reference cell
    # alone is not enough: it shows which colours EXIST, not which id each one
    # belongs to.
    legend = ""
    try:
        pc = json.loads((out_dir / "part_colors.json").read_text(encoding=UTF8))
        # The colour WORD, not just the hex - a vision judge matches "warm
        # ivory" against a picture and cannot match #F1E9D7 against anything.
        # art_direction.md already writes one per part.
        try:
            ad = (out_dir / "art_direction.md").read_text(encoding=UTF8)
        except OSError:
            ad = ""
        words = dict(re.findall(
            r"`([a-z0-9_]+)`[^`]{0,12}`#[0-9A-Fa-f]{6}`[^a-zA-Z]*([^\n.]{0,40})",
            ad))
        rows = "\n".join(
            f"  {(k[:-4] if k.endswith('.stl') else k):24} {v}"
            f"  {words.get(k[:-4] if k.endswith('.stl') else k, '').strip()}"
            for k, v in pc.items())
        legend = ("\n\nWHICH COLOUR IS WHICH PART. Use these names; do not infer "
                  "them from the picture:\n" + rows + "\n")
    except (OSError, json.JSONDecodeError):
        pass
    return f"""You are the VIDEO QA judge. VISUAL ONLY.

WRITE {out_dir}/{verdict} AS YOUR VERY FIRST ACTION, before you study anything.
Open the sheet once, write the file with your first impression, and only then
look closely and REWRITE it with what you find. A file must exist when you
stop, whatever happens.

This is not advice. Measured twice on 2026-08-21, this judge spent 21 turns and
then 31 turns examining one sheet and wrote NOTHING both times - $2.10 for two
verdicts that never existed. Raising the turn cap did not help; it only bought
more looking. So the file comes first and gets better, instead of being perfect
and absent.

Look at {out_dir}/{sheet}.{legend}
The FIRST cell is the REFERENCE: a render of the real
printed parts, in their locked colours, in the quantity the box actually
contains. Every other cell is a frame from a generated clip of those same parts,
in time order.

THE RULE THIS CLIP IS SUPPOSED TO SHOW:
{rule}

The generator is an image model. It does not know what a part is, so it will
happily reshape one, breed more of them, or grow them - and a clip that does
that advertises a product nobody will receive. Answer five questions, each one
about a failure that has actually happened here:

1. SAME PARTS? Does every object in the frames match the reference in SHAPE?
   Name any part that changes between frames - a closed body becoming an open
   one, a wall gaining or losing structure, a silhouette that morphs.
2. SAME COUNT? Count the loose pieces in each frame. The rule above says how
   many there should be. Do NOT accept "about right": if the rule says five and
   a frame shows eight, that is a fail, and say which frame.
3. SAME SIZE? Do the pieces hold their size relative to the board across the
   frames, or do they grow?
4. POSSIBLE PLACES? Are the pieces where the rule could actually put them, or
   have they appeared somewhere nothing could reach?
5. RIGHT ACTION? Is the action in these frames the one the rule describes - or
   a different, plausible-looking one?

A clip fails on ANY of the five. Being photoreal is not a defence and neither
is looking good.

REWRITE {out_dir}/{verdict} with your final answers, exactly:

{{"verdict": "PASS" | "FAIL",
  "same_parts": true|false, "same_count": true|false, "same_size": true|false,
  "possible_places": true|false, "right_action": true|false,
  "issues": ["one sentence each, naming the frame time and the part"],
  "fix": "the ONE change to the video prompt most likely to stop the worst of
          these - phrased as an instruction to the generator"}}

REMINDER: the file was supposed to exist from your first turn. If you have
refined your answers, rewrite it. If you are running out of turns, rewrite it
now with what you have and say in `issues` which cells you did not reach. A
verdict from partial evidence beats silence - the DISCOVER judges carry the
same instruction, for the same reason, after a panel died the same way.

{HEADLESS}

Write the file. Do not print it and stop."""


def build_group(out_dir: Path, title: str, body: str, n_groups: int) -> str:
    return f"""You are BUILD, phase 2.2, for ONE group of parts only.

--- your group, from todo.md ---
### {title}
{body}

--- the contract you may not break ---
{(out_dir / "parts_index.json").read_text(encoding="utf-8")}

Read {out_dir}/gdd.md for what each part must DO, and
{out_dir}/art_direction.md for its colour.

{skill('build')} Build ONLY the parts named in this group. Other parts
exist or will exist; do not touch their files.

Rules:
- {out_dir}/parts/<id>.py already exists with QTY, TOL, BBOX, MATES and DUTY as
  constants taken from the contract. Fill in build(). Do not edit the constants
  - if one is wrong, say so in your reply and stop, that is a phase 1 error.
- export each part to {out_dir}/fe_parts/<id>.stl in PRINT orientation, and the
  group's solids into the shared STEP, and record colours in
  {out_dir}/part_colors.json (merge, never overwrite other parts' entries)
- respect BBOX. A part over 160mm in x or y fails the gate.
- respect TOL on every interface named in MATES. The harness measures this
  AFTER your session ends, against the contract, not by eye - and if it misses,
  a repair session is spent on it. You can run the same check yourself instead,
  and these are the only two commands that exist:

    uv run --python 3.12 --with cadquery python3 \
      {harness.text2cad_dir()}/skills/cadcode/scripts/measure <file.step> --gaps
    {harness.text2cad_py()} {harness.text2cad_dir()}/gate.py <out_dir> --no-slice

  measure takes ONLY --part, --gaps and --near. `scripts/measure` and
  `scripts/gate` are not executables and there is no `scripts/gate` at all.
  Measured 2026-08-20 on `precedent`: three build sessions in a row reported
  the tools "unavailable" or missing switches they had invented, each one
  spending its own turns finding that out, in a session with a turn budget and
  nobody to ask.

EXIT CRITERIA for this group is written above. Meet it before you finish.

You are one of {n_groups} groups; the parts you mate with may already be
built - read their .py files rather than re-deriving their interfaces.

{HEADLESS}"""


def repair_group(out_dir: Path, title: str, issues: str) -> str:
    return f"""You are REPAIR, phase 2.2, for the group "{title}".

The group was built and then measured. It failed:

{issues}

{skill('repair')}

Read the failing parts' files under {out_dir}/parts/, fix the geometry, and
re-export. Rules:
- a `too-tight` or `interference` finding is a real dimension error. Fix the
  geometry, do not widen the tolerance in the contract.
- a `no-gap` finding means two declared mates were modelled as one solid or
  never placed apart.
- if the fix requires changing a number in parts_index.json / components.json,
  do NOT change it. Say which number and why in your reply and stop - the
  contract is phase 1's and a human owns it.

RE-EXPORT EVERYTHING BEFORE YOU FINISH. Not only the parts you touched.

  uv run --python 3.12 --with cadquery python3 \
    {harness.text2cad_dir()}/skills/cadcode/scripts/cad <out_dir>

The gate fails a build whose sources are newer than its exports, and it
compares against the OLDEST export, so editing main.py invalidates every STL in
the run - including ones you did not touch and did not break. Measured
2026-08-20 on `precedent`: repair-g4-1 edited main.py at 13:33 and re-exported
only its own parts. The oldest STL was from 13:20, and the gate returned
`stale_stl(main.py 778s newer than exports)`. That is a TIMESTAMP, not a
geometry error - a full re-export afterwards came back clean and solid - and it
cost the second repair attempt and then stopped phase 2.

You can check your own work with the two commands that exist:

  uv run --python 3.12 --with cadquery python3 \
    {harness.text2cad_dir()}/skills/cadcode/scripts/measure <file.step> --gaps
  {harness.text2cad_py()} {harness.text2cad_dir()}/gate.py <out_dir> --no-slice

measure takes ONLY --part, --gaps and --near. `scripts/measure` and
`scripts/gate` are not executables and there is no `scripts/gate` at all.

{HEADLESS}"""


def coherence(out_dir: Path) -> str:
    shot = ("renders/staged.png" if (out_dir / "renders" / "staged.png").is_file()
            else "renders/assembled.png")
    return f"""You are the COHERENCE lens, phase 2.5. VISUAL ONLY.

Look at {out_dir}/{shot} and hold it against the art direction this pipeline
locked for itself:

--- art_direction.md ---
{(out_dir / "art_direction.md").read_text(encoding="utf-8")}

Do not read gdd.md, do not read components.json, do not open trimesh, do not
reason about tolerances. Look at the picture.

Answer three questions, in this order:

1. ONE PRODUCT OR A BIN OF PARTS? Does the assembled game read as a single
   designed object from across a table, or as unrelated pieces that happen to
   touch? This is the question that decides the score.
2. CAN A PLAYER TELL THE PARTS APART? Name any two parts that are hard to
   distinguish at a glance. A part the rules make you find in a hurry and that
   does not stand out is a real failure, not a nitpick.
3. DID THE PALETTE SURVIVE? Does what you see match the colours art_direction
   locked? Flag any two load-bearing parts sitting in the warm 25-65 degree
   band, where they merge with PLA grey.

Write your verdict FIRST, then the reasoning:

    VERDICT: <n>/10
    CONCEPT: still | drifted - one sentence
    <three short paragraphs, one per question>

10 = a photograph of a finished retail product. 5 = clearly one game, but two
parts fight each other or a colour went missing. 1 = a pile of grey blocks.

The CONCEPT line is a NOTE, not part of the score. {out_dir}/concept.png was
generated from a one-line pitch before this game had rules or a part list, so
it cannot outrank the art direction - say whether the build still looks like
the game that was picked, and leave it at that.

{HEADLESS}

Write {out_dir}/lens_coherence.md. Do not print it and stop."""


# ---------------------------------------------------------------- phase 3

def rulebook(out_dir: Path) -> str:
    return f"""You are the RULEBOOK editor, phase 3.3.

Read {out_dir}/gdd.md. Turn it into a rulebook a stranger can learn the game
from, printed on paper, no screen.

WRITE {out_dir}/rulebook.md:
- open with the 3-sentence pitch and the box contents, by component id AND by
  the plain name a player would use ("the amber disc")
- Setup as a numbered list a player follows while looking at the table
- one page for the turn, in play order, with the numbers inline
- Legacy on its own page, with the warning that it cannot be undone
- Edge cases as a reference table at the back
- drop the Glossary if every term is already explained in place

Change no rule and no number. If gdd.md is ambiguous somewhere, do not resolve
it silently - list it under `## Needs a ruling` at the end.

{HEADLESS}

Write the file. Do not print it and stop."""


def video_spec(out_dir: Path) -> str:
    return f"""You are the VIDEO DIRECTOR, phase 3.4.

--- the beats, derived from gdd.md, not invented ---
{(out_dir / "storyboard.json").read_text(encoding="utf-8")}

--- the locked look ---
{(out_dir / "art_direction.md").read_text(encoding="utf-8")}

The first frame is a REAL render of the built game at
{out_dir}/renders/assembled.png. Every part in it exists as an STL.

WRITE {out_dir}/howto.json in the schema gen_howto_video.py expects:
{{"frame": "renders/assembled.png", "seed": 11, "durations": [12,10,6],
  "out": "howto_game.mp4", "i2i_prompt": "...", "video_prompt": "...",
  "caption": "..."}}

i2i_prompt: make the render photoreal. Name every part by the colour it has in
art_direction.md. Keep geometry, viewpoint, proportions and part count exactly.
Real matte FDM print, fine layer lines, studio backdrop, soft contact shadow.

video_prompt: one beat per storyboard beat, in order, hands entering low and
LEAVING frame between beats. Say what the hand does in the rules' own terms.
End on the irreversible act and hold on it.

caption: three numbered lines, one per beat, in plain language.

Do NOT write that no STL exists - one does now. {HEADLESS}

Write the file and stop."""
