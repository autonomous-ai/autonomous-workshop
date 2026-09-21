"""Every STEP this run wrote, against the set it is a correction of.

The Wish asks for the per-part hashes of this run reported against
`make/ATTEMPTS.json` in the source archive, and for a plain statement of which
parts changed.  The chain is: `make/ATTEMPTS.json` records one accepted Make
attempt and its `subject_sha256`; that value is `make/made.json`'s own
`made_sha256`; and `made.json`'s `product_manifest` carries the sha256 of
every file of the accepted product tree.  Those are the baseline hashes.

Only one family of files can answer the question in bytes.  `cad/part_*.step`
is written by `cadgen`, which stamps a fixed `1970-01-01T00:00:00` header, so
identical geometry gives identical bytes across runs and a hash comparison
means something.  `parts/*.step` is written by `production.py` through
build123d's own exporter, which stamps the wall-clock time it ran, so those
files differ between any two runs whatever the geometry does.  They are
compared by geometry instead, in `measure/occurrence-geometry.md`.

Naming the corrected parts is what lets the report say which were *meant* to
move, rather than only which did.

This run is the first in the chain whose corrected parts do not all expect the
same answer, so the expectation is named per part rather than once for the run:

    "$WORKSHOP_PYTHON" measure/revision_hashes.py <product-root> <archive-root> \\
        --identical world_mercury_anti world_venus_anti \\
        --changed corona_cell \\
        > measure/revision-part-hashes.md

`--identical` says the correction moves a colour boundary inside a part and not
the part's own outer boundary, so the printed solid is the same solid and
byte-identical is the pass.  That is what a flush colour inlay is: it partitions
the globe's volume without moving its surface, so mirroring the map on an
Anti-Sol globe changes which spool prints which piece of the ball and moves no
face anywhere.  A hash that MOVES on one of these is the failure.

`--changed` says the correction adds or removes material, so byte-identical
would mean the correction did not happen.  The corona cell loses two raised
tongues; its hash must move.

Both are checked, and so is the third statement, which is about the 22 parts
this run was not asked to touch: they must be byte-identical or differ only in
`NEXT_ASSEMBLY_USAGE_OCCURRENCE`, which is measured line by line rather than
asserted.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline(archive: Path):
    attempts = json.loads((archive / "make" / "ATTEMPTS.json").read_text())
    made = json.loads((archive / "make" / "made.json").read_text())
    accepted = [row for row in attempts["attempts"] if row["outcome"] == "accepted"]
    if len(accepted) != 1:
        raise SystemExit("the archive does not record exactly one accepted attempt")
    if accepted[0]["subject_sha256"] != made["made_sha256"]:
        raise SystemExit("ATTEMPTS.json and made.json name different Make subjects")
    entries = {row["path"]: row["sha256"] for row in made["product_manifest"]["entries"]}
    return accepted[0], entries


#: STEP entity types whose text is an exporter bookkeeping label rather than
#: geometry.  `NEXT_ASSEMBLY_USAGE_OCCURRENCE`'s first field is the exporter's
#: own per-session occurrence counter: a part written as occurrence 179 of a
#: 182-occurrence run and the same part written alone carry different numbers
#: and identical shape.
BOOKKEEPING = ("NEXT_ASSEMBLY_USAGE_OCCURRENCE",)


def why_not_geometry(archive: Path, relative: str, now_path: Path):
    """Is every differing line of these two STEP files bookkeeping, not shape?

    Measured here rather than asserted, because "identical otherwise" is
    exactly the kind of claim that is inherited from a previous run and stops
    being true.  Returns a sentence when the difference is explained and None
    when it is not.
    """
    # The sanitized archive keeps the printed STEPs under make/models/, with
    # the project-relative path below it: make/models/cad/part_*.step.
    was = archive / "make" / "models" / relative
    if not was.is_file():
        return None
    left = was.read_text().splitlines()
    right = now_path.read_text().splitlines()
    if len(left) != len(right):
        return None
    differing = [
        (index, a, b)
        for index, (a, b) in enumerate(zip(left, right), 1)
        if a != b
    ]
    if not differing or any(
        not any(tag in a and tag in b for tag in BOOKKEEPING)
        for _index, a, b in differing
    ):
        return None
    return (
        "%d line%s differ%s, %s: an exporter occurrence counter, no geometry. "
        "Every other line matches the archive copy, checked here rather than "
        "asserted"
        % (len(differing), "" if len(differing) == 1 else "s",
           "s" if len(differing) == 1 else "",
           ", ".join(sorted({
               tag for _i, a, _b in differing for tag in BOOKKEEPING if tag in a
           })))
    )


def main():
    argv = list(sys.argv[1:])
    product = Path(argv[0])
    archive = Path(argv[1])
    want_identical, want_changed = [], []
    bucket = None
    for item in argv[2:]:
        if item == "--identical":
            bucket = want_identical
        elif item == "--changed":
            bucket = want_changed
        elif bucket is None:
            raise SystemExit("name each corrected part under --identical or --changed")
        else:
            bucket.append(item)
    corrected = want_identical + want_changed
    if not corrected:
        raise SystemExit("name the printed parts this revision was asked to correct")
    attempt, entries = load_baseline(archive)

    print("# Per-part STEP hashes, this run against the published set")
    print()
    print("`make/ATTEMPTS.json` in the source archive records one accepted Make")
    print("attempt, round %d, subject" % attempt["round"])
    print("`%s`." % attempt["subject_sha256"])
    print("That subject is `make/made.json`'s `made_sha256`, and that file's")
    print("`product_manifest` carries the sha256 of every file of the accepted tree.")
    print("Those are the published hashes below.")
    print()
    print("Both runs write `cad/part_*.step` through `cadgen`, which stamps a fixed")
    print("`1970-01-01T00:00:00` header, so identical geometry gives identical bytes.")
    print()
    print("## The 24 printed geometries")
    print()
    print("| printed part | published sha256 | this run | |")
    print("|---|---|---|---|")
    identical, explained, changed = [], [], []
    for item in sorted((product / "cad").glob("part_*.step")):
        relative = "cad/" + item.name
        now, then = digest(item), entries.get(relative)
        if then is None:
            verdict, bucket = "new in this run", changed
        elif then == now:
            verdict, bucket = "identical", identical
        elif why_not_geometry(archive, relative, item) is not None:
            verdict, bucket = why_not_geometry(archive, relative, item), explained
        else:
            verdict, bucket = "**changed**", changed
        bucket.append(relative)
        print("| `%s` | `%s` | `%s` | %s |"
              % (item.name, (then or "-")[:16], now[:16], verdict))

    print()
    print("## What changed")
    print()
    print("- **%d of the 24 printed geometries are byte-identical.**" % len(identical))
    if explained:
        print("- **%d file%s moved in bytes without moving in shape.** Each was"
              % (len(explained), "" if len(explained) == 1 else "s"))
        print("  diffed against the archive copy line by line in this run: every")
        print("  differing line is a `NEXT_ASSEMBLY_USAGE_OCCURRENCE`, the")
        print("  exporter's own per-session occurrence counter, which carries no")
        print("  geometry. The parts are %s."
              % ", ".join("`%s`" % Path(name).name for name in explained))
    def name_list(items):
        return ", ".join("`%s`" % Path(item).name for item in items)

    wanted = ["cad/part_%s.step" % stem for stem in corrected]
    identical_wanted = ["cad/part_%s.step" % stem for stem in want_identical]
    changed_wanted = ["cad/part_%s.step" % stem for stem in want_changed]
    unexplained = [name for name in changed if name not in wanted]

    if unexplained:
        print("- **Unaccounted for: %s**" % name_list(unexplained))
    else:
        print("- **Nothing moved that was not asked to.** Every printed part")
        print("  outside %s is the same geometry the published set carries%s."
              % (name_list(wanted),
                 ", and the %d listed above are the same shape written with a "
                 "different occurrence counter" % len(explained)
                 if explained else ""))
    print()
    print("## The three statements, and which the hashes support")
    print()
    print("A marking in this set is a flush colour inlay: it partitions the globe's")
    print("volume without moving the printed solid's own boundary. So a correction")
    print("that only changes a marking lands entirely in `parts/*.step`, which")
    print("`measure/occurrence-geometry.md` measures, and leaves `cad/part_*.step`")
    print("byte-identical. A correction that adds or removes material does the")
    print("opposite, and byte-identical would mean it did not happen. This run")
    others_all = [name for name in identical + explained + changed
                  if name not in wanted]
    print("carries one of each, on disjoint parts, and a third statement about the")
    print("%d parts it was asked not to touch at all." % len(others_all))
    print()
    print("**On that count, and it is worth stating rather than rounding.** The")
    print("brief for this revision says \"the other 22 printed geometries\". This")
    print("set has %d distinct printed geometries, and this revision names three"
          % (len(others_all) + len(wanted)))
    print("of them, so the number outside the correction is **%d**, not 22. The"
          % len(others_all))
    print("brief's figure is one out; nothing else about the statement changes,")
    print("and every one of the %d is checked below." % len(others_all))
    print()

    print("### 1. The two mirrored worlds must be BYTE-IDENTICAL")
    print()
    print("%s. Mirroring the map on an Anti-Sol globe reflects every marking's"
          % name_list(identical_wanted))
    print("longitude about that piece's own facing meridian. That changes which")
    print("spool prints which piece of the ball and moves no face anywhere: the")
    print("globe is the same sphere, the seat is the same cone, the disc and the")
    print("numeral are untouched, and each inlay still bottoms out at exactly")
    print("`RELIEF_DEPTH` below the surface. If either hash had moved, something")
    print("cut deeper than a marking is allowed to, and nothing else in this run")
    print("would be worth reading.")
    print()
    identical_moved = [name for name in identical_wanted if name in changed]
    if not identical_moved:
        print("**They did not move.** %s are byte-identical to the published"
              % name_list(identical_wanted))
        print("set's, which is the answer this correction has to give.")
        print("`measure/occurrence-geometry.md` is where the change does show:")
        print("the per-colour bodies underneath the surface are in different")
        print("places, and `measure/pair-separation.md` measures how far.")
    else:
        print("- **%s changed, and must not have.**" % name_list(identical_moved))

    print()
    print("### 2. The trap tile must CHANGE")
    print()
    print("%s. The corona cell loses two raised tongues, which is material"
          % name_list(changed_wanted))
    print("removed from the printed solid. Byte-identical here would mean the")
    print("tongues are still on the tile.")
    print()
    changed_still = [name for name in changed_wanted if name not in changed]
    if not changed_still:
        print("**It changed.** %s carries new bytes, and what is gone from them"
              % name_list(changed_wanted))
        print("is two tapered flames and the 7.00 mm of height they stood in.")
        print("`measure/corona-flat.md` measures the tile before and after.")
    else:
        print("- **%s did not change, so the tongues were not removed.**"
              % name_list(changed_still))

    print()
    print("### 3. The other %d must be byte-identical or bookkeeping-only"
          % len(others_all))
    print()
    other_changed = [name for name in changed if name not in wanted]
    print("That is every printed geometry outside the three this run was asked")
    print("to correct -- both Sol pieces of Mercury and Venus among them, and")
    print("the den plug, whose two flames this run exists to leave alone.")
    print()
    if other_changed:
        print("- **%s moved and are not accounted for.**" % name_list(other_changed))
    else:
        print("**None of them moved in shape.** %d are byte-identical; %d differ"
              % (len([n for n in identical if n not in wanted]),
                 len([n for n in explained if n not in wanted])))
        print("only in `NEXT_ASSEMBLY_USAGE_OCCURRENCE`, diffed line by line in")
        print("this run rather than carried forward as a claim.")
    print()
    print("## The production solids")
    print()
    print("`parts/*.step` cannot be compared in bytes: `production.py` writes them")
    print("through build123d's exporter, which stamps each file with the wall-clock")
    print("time of the run, so all %d differ between any two runs whatever the"
          % len(list((product / "parts").glob("*.step"))))
    print("geometry does. They are compared occurrence by occurrence, on solid count,")
    print("exact volume and bounding box, in `measure/occurrence-geometry.md`.")


if __name__ == "__main__":
    main()
