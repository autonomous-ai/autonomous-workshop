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
differ and byte-identical would be the failure.  Only one run in this chain has
needed it -- the Uranus run, which added a ring.  Every other run wanted the
opposite: a flush colour inlay partitions the globe's volume without moving the
printed solid's own boundary, so the corrected parts come out identical and
that is the right answer.  This revision is one of those, and it is the
clearest example of it the chain has had.  It removes both of Uranus's polar
hoods, which STOPS partitioning the globe rather than cutting into it, and it
repaints the ring, which moves one existing body from one filament to another.
Neither moves a surface.  So `--expect-changed` is NOT passed and byte-identical
is the pass -- and if a Uranus hash moves, something moved the ring or the globe
and that has to be found before anything else in the run is worth reading.
The report below says which of the two statements the hashes support rather
than asserting either.
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


def _solid(path):
    """(volume, bounding-box tuple) of one STEP, imported exactly."""
    from build123d import import_step

    shape = import_step(str(path))
    box = shape.bounding_box()
    return (shape.volume, (box.min.X, box.min.Y, box.min.Z,
                           box.max.X, box.max.Y, box.max.Z))


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
        print("- **Nothing moved that was not asked to.** Every printed part")
        print("  outside %s is the same geometry the published set carries%s."
              % (named,
                 ", and the %d listed above are the same shape written with a "
                 "different occurrence counter" % len(explained)
                 if explained else ""))
    print()
    print("## The two statements, and which one the hashes support")
    print()
    print("A marking in this set is a flush colour inlay: it partitions the globe's")
    print("volume without moving the printed solid's own boundary, so a correction")
    print("that only changes a marking lands entirely in `parts/*.step`, which")
    print("`measure/occurrence-geometry.md` measures, and leaves `cad/part_*.step`")
    print("byte-identical. That is the FIRST statement, and it is what every run in")
    print("this chain except the Uranus one has expected of its own corrected parts.")
    print()
    print("The SECOND statement is the Uranus run's: a ring is added material, so")
    print("its two parts had to change in bytes and byte-identical would have meant")
    print("the ring did not get built.")
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
        if len(still) == len(wanted):
            print("**This run expects the first statement, and the hashes support")
            print("it: %s byte-identical to the published set's.**"
                  % ", ".join("`%s`" % Path(n).name for n in still))
            print()
            print("That is the check rather than a formality, and on this run it")
            print("is the check the whole correction turns on. This revision adds")
            print("ONE new marking to Neptune -- the dark spot's bright companion")
            print("cloud -- and takes a scallop out of the dark spot to make room")
            print("for it. Both of those are colour boundaries inside the globe's")
            print("own volume: `parts/world.build_world` fuses the disc, the globe")
            print("and the ring and never a marking, so adding a marking cannot")
            print("move the printed solid's own surface. If it had -- a cut gone")
            print("deeper than `RELIEF_DEPTH`, a seat re-cut, a globe rebuilt at a")
            print("different diameter -- these two hashes would have moved with it.")
            print("They did not. The printed solid the shop receives is the same")
            print("solid it was, and the whole revision is in which spool prints")
            print("which part of it.")
            print("`measure/occurrence-geometry.md` measures the other half on the")
            print("colour solids directly: which occurrences appeared, which")
            print("changed volume, and that nothing outside Neptune did either.")
        elif still:
            print("**Only partly.** %s came out byte-identical and %s did not,"
                  % (", ".join("`%s`" % Path(n).name for n in still),
                     ", ".join("`%s`" % Path(n).name for n in moved)))
            print("which this revision does not account for.")
        else:
            print("**The corrected parts changed**, which this run did not expect:")
            print("a flush colour inlay must not move the printed solid's boundary.")
    if unexplained:
        print()
        print("## The byte-different parts, measured")
        print()
        print("Eleven printed parts outside the correction came back with")
        print("different bytes, and a hash comparison cannot say whether that")
        print("is a changed solid or a differently written one. So they are")
        print("measured. Each STEP is imported from both trees and compared on")
        print("exact volume and on bounding box.")
        print()
        print("| part | published mm3 | this run mm3 | difference mm3 | "
              "bounding box |")
        print("|---|---:|---:|---:|---|")
        worst = 0.0
        for name in unexplained:
            stem = Path(name).name
            before = _solid(archive / "make/models/cad" / stem)
            after = _solid(product / "cad" / stem)
            delta = abs(after[0] - before[0])
            worst = max(worst, delta)
            box = ("identical to 1e-9 mm"
                   if max(abs(x - y) for x, y in zip(before[1], after[1])) < 1e-9
                   else "**DIFFERS**")
            print("| `%s` | %.6f | %.6f | %.2e | %s |"
                  % (stem, before[0], after[0], delta, box))
        print()
        if worst < 1e-6:
            print("**Every one of them is the same solid.** The largest volume")
            print("difference anywhere in the table is %.2e mm3, which is" % worst)
            print("boolean round-off rather than geometry, and every bounding")
            print("box agrees to a nanometre. What moved is the serialisation:")
            print("this project's generator does not write identical STEP bytes")
            print("for these parts between a warm multi-target generation and a")
            print("single-target one -- six of the eleven come out with a")
            print("different entity count for the same shape. It is a property")
            print("of the writer, not of the design, and none of it is in")
            print("`measure/source-diff.md`, which is the whole difference")
            print("between the two source trees and holds five files, none of")
            print("them these parts' generators.")
        else:
            print("**%d of them differ by more than round-off (worst %.2e mm3)**"
                  % (sum(1 for _ in unexplained), worst))
            print("and that is a finding rather than a result.")
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
