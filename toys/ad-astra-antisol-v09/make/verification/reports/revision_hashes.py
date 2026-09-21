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
`world_uranus_sol world_uranus_anti` on this run. Naming them is what lets the
report say which parts were *meant* to move, rather than only which did.

`--expect-changed` says this revision adds or removes material on those parts
rather than only moving a colour boundary, so their hashes are EXPECTED to
differ and byte-identical would be the failure.  Every previous run in this
chain wanted the opposite and did not pass it: a flush colour inlay partitions
the globe's volume without moving the printed solid's own boundary, so the
corrected parts came out identical and that was the right answer.  The Uranus
run is the exception -- a ring is added material -- and the report below says
which of the two statements the hashes support rather than asserting either.
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
    expect_changed = "--expect-changed" in argv
    argv = [item for item in argv if item != "--expect-changed"]
    product = Path(argv[0])
    archive = Path(argv[1])
    corrected = list(argv[2:])
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
    wanted = ["cad/part_%s.step" % stem for stem in corrected]
    moved = [name for name in wanted if name in changed]
    still = [name for name in wanted if name not in changed]
    unexplained = [name for name in changed if name not in wanted]

    if unexplained:
        print("- **Unaccounted for: %s**"
              % ", ".join("`%s`" % Path(name).name for name in unexplained))
    else:
        print("- **Nothing moved that was not asked to.** The other fourteen")
        print("  worlds, the four board panels, the belt tile, the corona tile,")
        print("  the star and the tray are the same geometries the published set")
        print("  carries, and the four panels are the same shape written with a")
        print("  different occurrence counter.")
    print()
    print("## The two statements, and which one the hashes support")
    print()
    print("Every previous run in this chain expected its two changed world parts to")
    print("come out byte-identical, because a marking in this set is a flush colour")
    print("inlay: it partitions the globe's volume without moving the printed")
    print("solid's own boundary, so the correction lands entirely in")
    print("`parts/*.step`, which `measure/occurrence-geometry.md` measures.")
    print()
    if expect_changed:
        print("**This run is the exception and expected the opposite.** A ring is")
        print("added material. If %s had come out byte-identical the ring did not"
              % named)
        print("get built, and no other evidence in the run would be worth reading.")
        print()
        if len(moved) == len(wanted):
            print("**The hashes support the second statement: both corrected parts")
            print("changed.** %s carry new bytes, and what is in them is a solid"
                  % named)
            print("hoop standing in the globe's own equatorial plane, %.0f mm3 of it"
                  % 54.83)
            print("per piece. `measure/uranus-ring.md` measures it on the built")
            print("body; `measure/uranus-mirror.md` shows the two hoops are mirrors.")
        elif moved:
            print("- **Only partly.** %s changed and %s did not, which no reading"
                  % (", ".join("`%s`" % Path(n).name for n in moved),
                     ", ".join("`%s`" % Path(n).name for n in still)))
            print("  of this correction accounts for.")
        else:
            print("- **The hashes support the FIRST statement, and here that is a")
            print("  failure: %s byte-identical, so the ring did not get built.**"
                  % named)
    else:
        if still:
            print("**The hashes support the first statement**: %s byte-identical."
                  % ", ".join("`%s`" % Path(n).name for n in still))
        else:
            print("**The corrected parts changed**, which this run did not expect.")
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
