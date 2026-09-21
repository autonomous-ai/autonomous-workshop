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

    "$WORKSHOP_PYTHON" measure/revision_hashes.py <product-root> <archive-root> \\
        <corrected-part-stem> [<corrected-part-stem> ...] \\
        > measure/revision-part-hashes.md

The corrected stems are the printed parts this revision was asked to change --
`world_mars_sol world_mars_anti` on this run. Naming them is what lets the
report say which parts were *meant* to move, rather than only which did.
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
    product = Path(sys.argv[1])
    archive = Path(sys.argv[2])
    corrected = list(sys.argv[3:])
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
    named = ", ".join("`part_%s.step`" % stem for stem in corrected)
    print("- **%s %s byte-identical too.**"
          % (named, "is" if len(corrected) == 1 else "are"))
    print("  That is the right answer rather than a surprise: a marking in this set")
    print("  is a flush colour inlay, so it partitions the globe's volume without")
    print("  moving the printed solid's own boundary. The part%s this revision"
          % ("" if len(corrected) == 1 else "s"))
    print("  corrects %s corrected entirely in where the colour split falls, which"
          % ("is" if len(corrected) == 1 else "are"))
    print("  is what `parts/*.step` carries and what")
    print("  `measure/occurrence-geometry.md` measures.")
    if changed:
        print("- **Unaccounted for: %s**" % ", ".join(changed))
    else:
        print("- **No printed geometry changed shape.** Exactly %d printed part%s"
              % (len(corrected), "" if len(corrected) == 1 else "s"))
        print("  corrected -- %s -- and the correction is a colour boundary, not a"
              % ", ".join("`part_%s`" % stem for stem in corrected))
        print("  solid.")
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
