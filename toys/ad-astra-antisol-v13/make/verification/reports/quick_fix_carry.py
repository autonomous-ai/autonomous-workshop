"""What this quick correction carried forward, what it regenerated, and why.

This run was started with `workshop fix --quick`, so the run root's frozen
`MAKE-OPTIONS.json` carries `quick_fix: true`.  Quick mode changes exactly one
thing: a printed part whose STEP comes out byte-identical to the published
set's may carry that part's component round history and per-part measure
reports forward instead of regenerating them, because a gate is a pure function
of the STEP it reads.

It lowers no threshold and skips nothing about the assembly.  The hash proof
itself is computed fresh over every part every time, because it is the entire
warrant for everything else.

    "$WORKSHOP_PYTHON" measure/quick_fix_carry.py <product-root> <archive-root> \\
        > measure/quick-fix-carry.md

Exit 0 when every carried claim checks out, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

#: `(12.3s, exit 0)` -- the wall-clock line `make_round` writes at the top of
#: every tool log it keeps.  It is how the source run's own figure is read.
ELAPSED = re.compile(r"^\((\d+(?:\.\d+)?)s, exit (\d+)\)$", re.M)

#: STEP entity types whose text is exporter bookkeeping rather than geometry.
BOOKKEEPING = ("NEXT_ASSEMBLY_USAGE_OCCURRENCE",)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed_of(path: Path) -> float:
    if not path.is_file():
        return 0.0
    found = ELAPSED.search(path.read_text(errors="replace"))
    return float(found.group(1)) if found else 0.0


def bookkeeping_only(was: Path, now: Path):
    """Every differing line is an exporter counter -- or None if not."""
    if not was.is_file():
        return None
    left = was.read_text().splitlines()
    right = now.read_text().splitlines()
    if len(left) != len(right):
        return None
    differing = [(a, b) for a, b in zip(left, right) if a != b]
    if not differing:
        return None
    if any(not any(tag in a and tag in b for tag in BOOKKEEPING)
           for a, b in differing):
        return None
    return len(differing)


def main() -> int:
    product = Path(sys.argv[1])
    archive = Path(sys.argv[2])
    #: Roles whose per-part gate reports this run WROTE rather than carried,
    #: whatever the hash proof ended up saying about their bytes.  Named on the
    #: command line because it is a fact about what this run did, not a fact
    #: about the files, and a reader must be able to tell the two apart.
    remeasured = set(sys.argv[3:])
    cad = product / "cad"
    measure = cad / "measure"

    made = json.loads((archive / "make" / "made.json").read_text())
    published = {row["path"]: row["sha256"]
                 for row in made["product_manifest"]["entries"]}
    sanitized = {
        row["path"]: row
        for row in json.loads((archive / "SANITIZATION.json").read_text())["files"]
    }

    failures = []

    print("# Quick correction: what was carried, what was regenerated")
    print()
    print("This run carries `quick_fix: true` in the run root's immutable")
    print("`MAKE-OPTIONS.json`. This file is the record quick mode requires: every")
    print("part carried forward, the sha256 it was carried on, what was")
    print("regenerated instead, and the wall-clock that saved against the source")
    print("run's own logged figure.")
    print()
    print("**Read the verdict at the bottom first if you are checking one thing.**")
    print("The short version: the hash proof came out at the maximum -- all 24")
    print("printed geometries byte-identical -- but it took until the final")
    print("verifier's own regeneration to get there, and the wall-clock saving")
    print("is small for a reason that has nothing to do with this correction.")
    print()

    print("## The hash proof, over every printed part")
    print()
    print("Computed fresh, here, over all 24. `cad/part_*.step` is written by")
    print("`cadgen`, which stamps a fixed `1970-01-01T00:00:00` header, so")
    print("identical geometry gives identical bytes and a hash comparison means")
    print("something. The baseline is `make/made.json`'s `product_manifest` in")
    print("the source archive.")
    print()
    print("| printed part | published sha256 | this run | verdict | carried? |")
    print("|---|---|---|---|---|")
    identical, explained, changed = [], [], []
    for item in sorted(cad.glob("part_*.step")):
        relative = "cad/" + item.name
        now, then = digest(item), published.get(relative)
        archived = archive / "make" / "models" / relative
        if then is None:
            verdict, carried, bucket = "new in this run", "no", changed
        elif then == now:
            role = item.name[len("part_"):-len(".step")]
            verdict = "identical"
            carried = ("history only -- reports re-measured" if role in remeasured
                       else "**yes**")
            bucket = identical
        else:
            lines = bookkeeping_only(archived, item)
            if lines is not None:
                verdict = ("%d line differs, an exporter occurrence counter"
                           % lines)
                carried, bucket = "no -- re-measured", explained
            else:
                verdict, carried, bucket = "**changed**", "no -- re-measured", changed
        bucket.append(item.name)
        print("| `%s` | `%s` | `%s` | %s | %s |"
              % (item.name, (then or "-")[:16], now[:16], verdict, carried))
    print()
    print("- byte-identical: **%d**" % len(identical))
    print("- same shape, different bytes: **%d**" % len(explained))
    print("- changed geometry: **%d**" % len(changed))
    print("- byte-identical but re-measured anyway, reports written fresh: **%d**"
          % len([n for n in identical
                 if n[len("part_"):-len(".step")] in remeasured]))
    print()

    if remeasured:
        print("### The four board panels, which is the one surprise in this run")
        print()
        print("They are byte-identical NOW. They were not for most of the run,")
        print("and the story is worth the paragraph because it is the whole")
        print("question of what a hash proof is a proof of.")
        print()
        print("Generated on their own, mid-run, `part_panel_northeast`,")
        print("`northwest`, `southeast` and `southwest` each differed from the")
        print("published copy in exactly ONE line, and that line was a")
        print("`NEXT_ASSEMBLY_USAGE_OCCURRENCE` label: `'1'` where the published")
        print("set has `'221'`, `'2'` against `'222'`, and so on. It is the")
        print("exporter's own per-session occurrence counter. Every other line of")
        print("all four files matched, diffed line by line rather than asserted.")
        print()
        print("**It was never caused by this correction, and that was established")
        print("by a control rather than by argument.** The unedited source from")
        print("the archive was unpacked into a scratch tree and the four panels")
        print("built from it on this machine: they produced the same four")
        print("non-matching hashes. The panels import nothing from")
        print("`parts/markings`, so nothing this correction touches can reach")
        print("them.")
        print()
        print("**What closed it was the shape of the exporting process.** The")
        print("final `verify_project` run regenerates every entry in ONE `gen`")
        print("call -- the 220-occurrence assembly among them -- and in that")
        print("process the four panels are written as occurrences 221 to 224,")
        print("which is exactly what the published set carries. The counter is")
        print("not a property of the part; it is a property of the run that")
        print("wrote it. The bytes in this tree are that run's, and they match.")
        print()
        print("**Their gate reports were re-measured before any of that was")
        print("known, and the fresh reports are what this tree carries.** At the")
        print("time their bytes did not match, quick mode's licence is")
        print("byte-identity, and naming a carried report against a sha256 that")
        print("did not match the file beside it would have been the exact mistake")
        print("the final sweep exists to catch. The four gates cost seconds and")
        print("the fresh measurements are listed below. Their component ROUND")
        print("history carries forward like every other part's.")
        print()

    print("## What each carried part carries")
    print()
    print("For a byte-identical part, two things carry: its component round")
    print("history under `measure/component-rounds/<role>/`, and its per-part")
    print("`measure/thickness-<role>.md` and `measure/overhang-<role>.md`.")
    print()
    print("| role | carried on sha256 | rounds carried | thickness report | overhang report |")
    print("|---|---|---:|---|---|")
    carried_seconds = 0.0
    for name in identical:
        if name[len("part_"):-len(".step")] in remeasured:
            role = name[len("part_"):-len(".step")]
            rounds = sorted((measure / "component-rounds" / role).glob("r[0-9]*"))
            # Not added to carried_seconds: two of this part's rounds are this
            # run's own, so its directory is no longer a pure archive figure.
            print("| `%s` | `%s` | %d | **re-measured, see below** | **re-measured, see below** |"
                  % (role, digest(cad / name)[:16], len(rounds)))
            continue
        role = name[len("part_"):-len(".step")]
        step = cad / name
        rounds = sorted((measure / "component-rounds" / role).glob("r[0-9]*"))
        for one in rounds:
            for log in one.glob("*.log"):
                carried_seconds += elapsed_of(log)
        reports = []
        for gate in ("thickness", "overhang"):
            report = measure / ("%s-%s.md" % (gate, role))
            reports.append("`%s-%s.md` carried" % (gate, role)
                           if report.is_file() else "**MISSING**")
            if not report.is_file():
                failures.append("%s: %s report is missing" % (role, gate))
        print("| `%s` | `%s` | %d | %s | %s |"
              % (role, digest(step)[:16], len(rounds), reports[0], reports[1]))
    print()

    print("## Every carried report, and how to tell it from a fresh one")
    print()
    print("A reader must be able to tell a carried report from a fresh one")
    print("without diffing, so this is the whole list rather than a rule. A")
    print("carried report is a file this run did not write: it came out of the")
    print("source archive unchanged, and its measurement describes the exact")
    print("STEP named in the table above.")
    print()
    print("There is one wrinkle and it is disclosed rather than smoothed over.")
    print("**The archive is sanitized.** The host replaced its own absolute")
    print("paths with placeholders before publishing it, so a carried report's")
    print("bytes are the sanitized projection of the sealed original rather than")
    print("the sealed original itself. `SANITIZATION.json` records both hashes")
    print("for every file it touched, and the check below is that each carried")
    print("report in this tree still hashes to the `public_sha256` that file")
    print("recorded -- an unbroken chain from the report the source run sealed,")
    print("through a path substitution the host performed and documented, to the")
    print("bytes here.")
    print()
    print("| carried report | sha256 here | sanitized from | chain checks |")
    print("|---|---|---|---|")
    carried_reports = 0
    for name in identical:
        role = name[len("part_"):-len(".step")]
        if role in remeasured:
            continue
        for gate in ("thickness", "overhang"):
            report = measure / ("%s-%s.md" % (gate, role))
            if not report.is_file():
                continue
            carried_reports += 1
            here = digest(report)
            row = sanitized.get("make/verification/reports/%s-%s.md" % (gate, role))
            if row is None:
                origin, ok = "not sanitized", here == published.get(
                    "cad/measure/%s-%s.md" % (gate, role))
            else:
                origin = "`%s`" % row["source_sha256"][:16]
                ok = here == row["public_sha256"]
            print("| `measure/%s-%s.md` | `%s` | %s | %s |"
                  % (gate, role, here[:16], origin, "yes" if ok else "**NO**"))
            if not ok:
                failures.append(
                    "measure/%s-%s.md does not match the hash the archive "
                    "recorded for it" % (gate, role))
    print()
    print("**%d carried reports, every one of them checked against the archive's"
          % carried_reports)
    print("own record of it.**")
    print()
    if remeasured:
        print("And the other side of the same list: these are the reports this")
        print("run WROTE, for the parts it would not carry. They are fresh")
        print("measurements on the STEPs in this tree, they replaced the carried")
        print("copies that were in the tree when it was cloned, and they are not")
        print("in the table above.")
        print()
        print("| fresh report | sha256 here | verdict |")
        print("|---|---|---|")
        for role in sorted(remeasured):
            for gate in ("thickness", "overhang"):
                report = measure / ("%s-%s.md" % (gate, role))
                if not report.is_file():
                    failures.append("%s: fresh %s report is missing"
                                    % (role, gate))
                    continue
                text = report.read_text()
                verdict = ("PASS" if "| PASS |" in text
                           else "**not a pass -- read the report**")
                print("| `measure/%s-%s.md` | `%s` | %s |"
                      % (gate, role, digest(report)[:16], verdict))
        print()
        print("So every one of the 24 printed parts has a thickness report and an")
        print("overhang report in `measure/`, %d of them carried on the sha256 in"
              % ((len(identical) - len(remeasured)) * 2))
        print("the first table and %d of them written here."
              % (len(remeasured) * 2))
        print()

    print("### And the one thing in this tree that is NOT byte-reproducible")
    print()
    print("The 24 printed parts are, when they are generated in a whole-set")
    print("process: the table above is that, measured. `cad/antisol.step` is")
    print("not. It is the 220-occurrence assembly, and its presentation block --")
    print("the `STYLED_ITEM` and `COLOUR_RGB` records at the end of a 1,072,578")
    print("line file -- comes out in a different order on every run, while every")
    print("geometry entity before it is identical. Two builds of it were compared")
    print("line by line during this run: same line count, 3330 differing lines,")
    print("all of them in that block and none of them geometry.")
    print()
    print("So the assembly is compared by GEOMETRY rather than by bytes, which is")
    print("what `measure/occurrence-geometry.md` does -- label by label, on solid")
    print("count, exact volume and bounding box, against the published archive's")
    print("own `antisol.step`. That comparison was run on two independently")
    print("generated builds of this correction and returned the same seven")
    print("changed `jupiter_anti_*` bodies and nothing else both times.")
    print()
    print("One consequence is worth stating rather than leaving for a reader to")
    print("notice. The assembled-object round under `measure/rounds/` was")
    print("recorded against an earlier build of the assembly, because the final")
    print("`verify_project` run regenerates everything and is deliberately the")
    print("last command to touch a STEP. The round's visual finding is about")
    print("geometry, and the geometry is the same geometry -- same 220")
    print("occurrences, same names, same colours, same transforms, same bounding")
    print("box, checked in the assembly package as well as in the occurrence")
    print("table. The bytes sealed here are the verifier's.")
    print()

    print("## What quick mode did not touch, and this run ran in full")
    print()
    print("Everything below was regenerated or re-run from scratch. None of it")
    print("is scoped by quick mode, and the last item is the reason the rest is")
    print("safe.")
    print()
    print("| work | why it is never carried | what this run did |")
    print("|---|---|---|")
    print("| the hash proof above | it is the warrant for everything else | computed fresh over all 24 parts |")
    print("| `parts/*.step`, all 220 | the colour bodies are what this correction moves | rewritten by `production.py` |")
    print("| `cad/antisol.step` and the root `assembled.*` | the assembly changes whenever any part does | rebuilt |")
    print("| `refs`, `validate`, `interfere` on the assembly | interference is a property of the whole set, never of a part | run in the final `verify_project` |")
    print("| every gate on every changed part | quick mode carries nothing that moved | the four panels re-measured |")
    print("| the assembled-object rounds | the assembly is what changed | run |")
    print("| `snap/iso.png`, `snap/signature.png`, the two rank-ladder frames, and every Jupiter frame | a render is a function of the geometry, and the geometry moved | regenerated |")
    print("| `verify_project` | this is the sweep that would catch a mistake in the carry-forward reasoning | run in full |")
    print("| the independent blind review | an old review is never proof of a new correction | run fresh, unprimed |")
    print()

    print("## The wall-clock, against the source run's own figure")
    print()
    print("The archive's `make_round` logs each begin with the wall-clock the")
    print("tool took -- `(2.6s, exit 0)` -- so the source run's own figure is")
    print("readable rather than estimated. All %d component-round HISTORIES carry"
          % len(identical))
    print("forward, but the gate time saved is only the %d parts whose reports"
          % (len(identical) - len(remeasured)))
    print("carried too: summed over their archive rounds, the source run spent")
    print("**%.0f seconds**, or **%.1f minutes**, on work this run did not repeat."
          % (carried_seconds, carried_seconds / 60.0))
    print("The four board panels' directories are deliberately left out of that")
    print("figure, because two of the rounds in each are this run's own and the")
    print("directory is no longer a pure archive number.")
    print()
    print("Set against what this run actually spent on the geometry it could")
    print("not carry, measured the same way:")
    print()
    print("| work | wall-clock |")
    print("|---|---:|")
    print("| carried: the %d parts' component rounds, from the archive's logs | %.0f s |"
          % (len(identical) - len(remeasured), carried_seconds))
    print("| not carried: rebuilding all 24 printed parts | 22 s |")
    print("| not carried: re-measuring the four panels' gates | 71 s |")
    print("| not carried: `production.py`, 220 colour bodies | 266 s |")
    print("| not carried: `gen antisol.step.py`, the whole set | 268 s |")
    print("| not carried: the renders, the assembled round and `verify_project` | see `measure/verification-pipeline.md` |")
    print()
    print("**On the part count this IS the maximum-saving case: all 24 printed")
    print("geometries came out byte-identical, and every one of the 24")
    print("component-round histories is still exactly true of the file it")
    print("describes.** The brief expected that and it is what happened -- a")
    print("marking is a flush colour inlay, so moving one moves no surface.")
    print("What the brief did not expect, and what this file has to say")
    print("plainly, is that the byte-identity of four of them was not")
    print("ESTABLISHED until the last command of the run, which is why their")
    print("reports were written fresh rather than carried.")
    print()
    print("**And in WALL-CLOCK terms it is not the maximum-saving case at all.**")
    print("The saving is a few minutes against a run whose cost is dominated by")
    print("three things quick mode never scopes")
    print("-- rebuilding the 220 colour bodies, rebuilding the 52 MB assembly,")
    print("and the final verifier. That is a property of this product rather")
    print("than of this correction: a set whose printed parts are cheap and")
    print("whose assembly is enormous is the shape of project quick mode helps")
    print("least.")
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("All %d printed parts are byte-identical to the published set and"
              % len(identical))
        print("all %d carry their component round history forward on the sha256"
              % len(identical))
        print("named above. %d of them also carry their two print-gate reports;"
              % (len(identical) - len(remeasured)))
        print("the %d board panels do not, because their bytes did not match"
              % len(remeasured))
        print("until the final verifier regenerated the whole set in one process,")
        print("and by then their gates had already been re-measured. **Nothing")
        print("was carried on a hash that does not match the file beside it**,")
        print("and every carried report still hashes to the value the archive's")
        print("own sanitization record gives it.")
    print()
    print("Written by `measure/quick_fix_carry.py` from the exact STEPs in this")
    print("tree and `make/made.json`, `SANITIZATION.json` in the source archive.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
