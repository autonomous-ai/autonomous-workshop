#!/usr/bin/env python3
"""Turn the findings this pipeline already produced into evidence.jsonl.

No LLM. Every row here was written by the critic or the referee during a real
run and then thrown away when the run ended.

`catalog.json` was the only thing in this repo that remembered yesterday, and
it remembers a slug, a lane and a sentence. So four designs produced 22 critic
findings and 7 referee findings and nothing counted them: the pipeline reached
for a speech restriction to fix `alpha_solve` in two separate games and the
critic rejected it both times, three designs were `decided_early`, two shipped
a `duplicate_state` part, and design five was free to do all of it again. This
file is the read-side of that loop.

It is deliberately a CLASSIFIER and not a judge. The symptom ids come from
mechanisms.md - if a pattern here names an id that table does not define, this
script refuses to run, the same way `mech-unknown` refuses an invented
mechanism. Findings it cannot classify are written out with `"symptom": null`
and counted loudly on stdout: an unclassified finding is a hole in the
vocabulary, not a row to drop.

Run:  ./harvest.py                     -> evidence.jsonl + a rollup
      ./harvest.py --strict            -> exit 1 if anything is unclassified
      ./harvest.py --recall a,b,c      -> the block prompts.critic() pastes in
"""
import json
import re
import sys
from pathlib import Path

from consistency import lane_of, sections

HERE = Path(__file__).resolve().parent

# What a source is worth. Four people at a table outrank a model reasoning from
# a document, and both outrank anything read on the internet - the critic
# predicts failures, it does not observe them. Never let a `critic` row
# outrank a `table` row: a graph fed by the critic and then read back by the
# critic is the machine agreeing with itself, which is the failure this repo's
# whole architecture exists to avoid.
WEIGHT = {"table": 4, "referee": 3, "critic": 2, "reading": 1}

SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}

# The referee's five kinds are already ids; they just never had a home.
REFEREE_KIND = {
    "CONTRADICTION": "contradiction",
    "DEAD STATE": "dead_state",
    "UNREACHABLE": "unreachable",
    "ILLEGAL TURN": "illegal_turn",
    "MISSING INFO": "missing_info",
}

# Ordered, most specific first. The FIRST match names the row; the rest ride
# along in `also`, because roughly a third of these findings are honestly two
# symptoms in one sentence - a part that duplicates a counter AND costs no
# decision - and picking one silently loses the other.
PATTERNS = [
    ("duplicate_state", r"duplicat\w+ the (?:exact )?[\w–-]+ ?\w* ?state"
                        r"|already shown by|already shows|count already shown"
                        r"|never gates or changes a rule"),
    ("dead_range",      r"unreachable spaces|cannot be reached|no legal play"
                        r"|at most \d+ per (?:session|campaign|round)"),
    ("decided_early",   r"result cannot change|cannot change,|already fixed the"
                        r"|do(?:es)? not end the campaign|fixed the campaign result"
                        r"|one failed [\w ]{0,25}can end|the initial [\w ]{0,30}"
                        r"(?:deal|draw|hand)|decided before"),
    ("spiral",          r"spiral|snowball|more likely before|compound\w*"
                        r"|turn one mistake into"),
    ("silent_calc",     r"silent duplicate|duplicate calculation|always optimal"
                        r"|already covers|identical \d-player|same public information"
                        r"|reduces cooperation to|no real choice"),
    ("alpha_solve",     r"alpha[- ]player|out loud|dictat\w+|prescrib\w+ the next"
                        r"|muzzle|no-suggestion|speech restriction"
                        r"|forbid[\w ]{0,20}coordinat"),
    ("seat_advantage",  r"first player|starting player|turn order|acting last"
                        r"|lowest-numbered|extra turn|seat advantage"),
    ("count_break",     r"\bat (?:two|three|four|five|six|\d) players\b"
                        r"|\b\d-player\b|player count"),
    ("idle_player",     r"cannot use|no legal move|\bidle\b|eliminat\w+"
                        r"|consolati\w+|rest of the session"),
    ("runaway_leader",  r"runaway|early leader|catch-up|trailer at"),
    ("legacy_flattens", r"collapsing later sessions|one-note play|later sessions into"),
    ("legacy_seat_penalty", r"strictly worse for one|worse for one seat"),
    ("dominant_action", r"dominant strateg\w+|weakly dominates|strictly dominates"
                        r"|always gives more|always beats|never wrong to"
                        r"|is safer deliberately|pointless"),
    ("trap_option",     r"never (?:worth|correct) tak\w+|no informed player"),
    ("kingmaker",       r"kingmak\w+|chooses who wins"),
    ("teach_overrun",   r"teach time|glossary|cannot be taught"),
    ("decoration",      r"cost(?:s)? the game no decision|would cost no decision"
                        r"|add handling and|\bdecoration\b"),
]


def symptom_vocab(mech_md: str) -> set:
    """Every id defined under `## SYMPTOM`, and nothing else in the file.

    Scoped the same way consistency.collide_pairs scopes COLLIDE: mechanisms.md
    now holds four tables and a global findall would blend them.
    """
    body = mech_md.split("## SYMPTOM", 1)[-1].split("## MITIGATE", 1)[0]
    return set(re.findall(r"^\| `([a-z_]+)` \|", body, re.M))


def mitigations(mech_md: str) -> dict:
    """{symptom: [{fix, costs, evidence}]} out of the MITIGATE table."""
    body = mech_md.split("## MITIGATE", 1)[-1]
    out = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        m = re.fullmatch(r"`([a-z_]+)`", cells[0])
        if not m:
            continue
        out.setdefault(m.group(1), []).append(
            {"fix": cells[1], "costs": cells[2], "evidence": cells[3]})
    return out


_VOCAB = None


def vocab() -> set:
    """The SYMPTOM ids, read once. mechanisms.md is the only source."""
    global _VOCAB
    if _VOCAB is None:
        _VOCAB = symptom_vocab((HERE / "mechanisms.md").read_text(encoding="utf-8"))
    return _VOCAB


def classify(text: str) -> tuple:
    """(best symptom or None, [other symptoms that also matched])."""
    hits = [sid for sid, pat in PATTERNS if re.search(pat, text, re.I)]
    return (hits[0] if hits else None), hits[1:]


def _mechs(out_dir: Path) -> list:
    f = out_dir / "mechanisms.json"
    if not f.is_file():
        return []
    try:
        return sorted(json.loads(f.read_text(encoding="utf-8")).get("chosen") or [])
    except json.JSONDecodeError:
        return []


def from_critic(out_dir: Path) -> list:
    """critic.json rows. `resolved` is not a severity - it is a revised row."""
    f = out_dir / "critic.json"
    if not f.is_file():
        return []
    try:
        items = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"  ! {out_dir.name}/critic.json is not valid JSON, skipped")
        return []
    rows = []
    for it in items:
        sev = str(it.get("severity", "")).lower()
        if sev not in SEVERITY_RANK or it.get("resolved"):
            continue
        claim = str(it.get("issue", "")).strip()
        if not claim:
            continue
        best, also = classify(claim + " " + str(it.get("fix", "")))
        # Since 2026-08-20 the critic names its own symptom id. Where it does,
        # that wins: the author of the finding knows what it is better than a
        # regex does. The patterns stay for the runs that predate the field,
        # and `labelled` says which of the two produced the id, so a rollup can
        # be re-read later without trusting the classifier retroactively.
        declared = str(it.get("symptom", "")).strip().lower()
        labelled = "pattern"
        if declared in vocab():
            if best and best != declared:
                also = [best] + [a for a in also if a != declared]
            best, labelled = declared, "critic"
        rows.append({"source": "critic", "severity": sev, "symptom": best,
                     "also": also, "labelled": labelled,
                     "declared": declared or None, "claim": claim,
                     "where": str(it.get("where", "")).strip(),
                     "fix_tried": str(it.get("fix", "")).strip()})
    return rows


def from_referee(out_dir: Path) -> list:
    """The `## Findings` blocks of referee.md. A CLEAN verdict yields none."""
    f = out_dir / "referee.md"
    if not f.is_file():
        return []
    body = sections(f.read_text(encoding="utf-8")).get("Findings", "")
    rows = []
    for block in re.split(r"^###\s+", body, flags=re.M)[1:]:
        head, _, rest = block.partition("\n")
        kind = re.split(r"\s*[—-]\s*", head.strip(), 1)
        sid = REFEREE_KIND.get(kind[0].strip().upper())
        title = kind[1].strip() if len(kind) > 1 else head.strip()
        detail = next((ln.strip() for ln in rest.splitlines() if ln.strip()), "")
        rows.append({"source": "referee", "severity": "high", "symptom": sid,
                     "also": [], "labelled": "referee", "declared": None,
                     "claim": f"{title} - {detail}"[:400],
                     "where": "", "fix_tried": ""})
    return rows


def from_table(out_dir: Path) -> list:
    """table_notes.md - what four people actually found, one bullet per finding:
    `- symptom_id: what was seen`. The only weight-4 source. Written by a HUMAN
    after a real night; nothing generated ever writes this file, which is the
    entire reason it outranks everything that does."""
    f = out_dir / "table_notes.md"
    if not f.is_file():
        return []
    rows = []
    for m in re.finditer(r"^-\s*`?([a-z_]+)`?\s*:\s*(.+)$",
                         f.read_text(encoding="utf-8"), re.M):
        declared, claim = m.group(1).strip().lower(), m.group(2).strip()
        best, also, labelled = declared, [], "table"
        if declared not in vocab():
            best, also = classify(claim)
            labelled = "pattern"
        rows.append({"source": "table", "severity": "high", "symptom": best,
                     "also": also, "labelled": labelled, "declared": declared,
                     "claim": claim[:400], "where": "", "fix_tried": ""})
    return rows


def harvest(root: Path, include_scratch: bool = False) -> list:
    """Every finding on disk, one row each, newest-slug order irrelevant."""
    out = []
    for d in sorted((root / "out").iterdir()):
        # `_discover`, `_p1test`, `_overcommit_rules`: scratch and re-runs.
        # Counting a re-run as a second design would inflate every hit rate.
        if not d.is_dir() or (d.name.startswith("_") and not include_scratch):
            continue
        mechs, lane = _mechs(d), lane_of(d)
        # Per-round snapshots first, then the live files. A symptom the reviser
        # was handed and did NOT fix is stronger evidence than one found once:
        # it means the fix that was tried does not work, which is exactly what
        # the MITIGATE table is for.
        seen_rounds = {}
        rounds = sorted((d / "rounds").glob("r*"), key=lambda p: p.name) \
            if (d / "rounds").is_dir() else []
        for rd in rounds:
            n = rd.name.lstrip("r")
            for row in from_critic(rd) + from_referee(rd):
                row.update(slug=d.name, lane=lane, mechs=mechs, round=n,
                           weight=WEIGHT[row["source"]])
                seen_rounds.setdefault(row["symptom"], set()).add(n)
                out.append(row)
        for row in from_critic(d) + from_referee(d) + from_table(d):
            row.update(slug=d.name, lane=lane, mechs=mechs,
                       round=row.get("round", "final"),
                       weight=WEIGHT[row["source"]])
            # A finding identical to one already taken from a snapshot is the
            # same finding, not a second sighting.
            if row["symptom"] and row["symptom"] in seen_rounds \
                    and any(r["claim"] == row["claim"] for r in out):
                continue
            out.append(row)
        for row in out:
            if row.get("slug") == d.name and row.get("symptom") in seen_rounds:
                row["survived_rounds"] = len(seen_rounds[row["symptom"]])
    for n, row in enumerate(out, 1):
        row["id"] = f"ev-{n:04d}"
    return out


def rollup(rows: list) -> list:
    """[(symptom, n_designs, n_findings, [slugs])] worst first."""
    by = {}
    for r in rows:
        by.setdefault(r["symptom"], set()).add(r["slug"])
    counts = {}
    for r in rows:
        counts[r["symptom"]] = counts.get(r["symptom"], 0) + 1
    return sorted(((s, len(sl), counts[s], sorted(sl)) for s, sl in by.items()),
                  key=lambda t: (-t[1], -t[2], str(t[0])))


def recall(mechs: list, rows: list, mits: dict, limit: int = 10) -> str:
    """The evidence block prompts.critic() pastes in for a locked mechanism set.

    Retrieval is a FILTER, not a model: rows whose mechanisms overlap the lock
    rank first, then anything that has hit two or more designs, because a
    failure that recurs across unrelated games is about this pipeline rather
    than about one box. Cap it - handing the critic the same ten edges every
    run will make it find those ten things and stop looking.
    """
    want = set(mechs)
    seen, groups = set(), []
    for sym, n_designs, n_find, slugs in rollup(rows):
        if sym is None:
            continue
        hits = [r for r in rows if r["symptom"] == sym]
        overlap = max((len(want & set(r["mechs"])) for r in hits), default=0)
        if not overlap and n_designs < 2:
            continue
        groups.append((overlap, n_designs, sym, hits, slugs))
    groups.sort(key=lambda g: (-g[0], -g[1]))

    lines = []
    for overlap, n_designs, sym, hits, slugs in groups[:limit]:
        worst = max(hits, key=lambda r: (SEVERITY_RANK.get(r["severity"], 0),
                                         r["weight"]))
        seen.add(sym)
        scope = f"{n_designs} design{'s' if n_designs > 1 else ''}"
        if overlap:
            scope += f", {overlap} shared mechanism{'s' if overlap > 1 else ''}"
        lines.append(f"- `{sym}` [{scope}; source {worst['source']}] "
                     f"{worst['claim']}")
        for m in mits.get(sym, [])[:2]:
            lines.append(f"    TRIED: {m['fix']}  COSTS: {m['costs']}  "
                         f"({m['evidence']})")
    if not lines:
        return ""
    return ("EVIDENCE from previous designs of this pipeline. These are not\n"
            "hypotheticals - each one was found in a game that was actually\n"
            "built. Check this design for every one of them before looking for\n"
            "anything new, and say so explicitly if it is clear:\n\n"
            + "\n".join(lines))


def main() -> int:
    argv = sys.argv[1:]
    rows = harvest(HERE, include_scratch="--include-scratch" in argv)
    mech_md = (HERE / "mechanisms.md").read_text(encoding="utf-8")

    # NOT a local named `vocab` - that shadowed the module-level vocab()
    # helper added later, and the shadow only bit at the very end of main()
    # AFTER evidence.jsonl had already been written, so the run looked fine
    # and exited nonzero. Use the one function everywhere.
    unknown = {sid for sid, _ in PATTERNS} - vocab()
    if unknown:
        print(f"harvest: {sorted(unknown)} not defined under `## SYMPTOM` in "
              f"mechanisms.md - add the row or drop the pattern", file=sys.stderr)
        return 2

    if "--recall" in argv:
        mechs = argv[argv.index("--recall") + 1].split(",")
        print(recall([m.strip() for m in mechs], rows, mitigations(mech_md))
              or "(no evidence yet)")
        return 0

    dest = HERE / "evidence.jsonl"
    dest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                            for r in rows), encoding="utf-8")

    designs = sorted({r["slug"] for r in rows})
    print(f"harvest: {len(rows)} findings from {len(designs)} designs "
          f"-> {dest.name}")
    for sym, n_designs, n_find, slugs in rollup(rows):
        if sym is None:
            continue
        print(f"  {n_designs}/{len(designs)}  {n_find:2}x  {sym:<20} {slugs}")
    bogus = sorted({r["declared"] for r in rows
                    if r.get("declared") and r["declared"] not in vocab()})
    if bogus:
        print(f"\n  the critic named {len(bogus)} id(s) `## SYMPTOM` does not "
              f"define: {bogus}\n  add the row, or the finding keeps landing on "
              f"whatever the patterns guess")
    loose = [r for r in rows if r["symptom"] is None]
    if loose:
        print(f"\n  {len(loose)} UNCLASSIFIED - the vocabulary has a hole here:")
        for r in loose:
            print(f"    [{r['slug']}] {r['claim'][:96]}")
    return 1 if loose and "--strict" in argv else 0


if __name__ == "__main__":
    sys.exit(main())
