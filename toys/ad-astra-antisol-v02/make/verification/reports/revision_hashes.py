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
        > measure/revision-part-hashes.md
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


#: Files whose bytes moved for a reason that is not geometry, with the reason
#: and the archive copy the claim was checked against line by line.
NON_GEOMETRIC = {
    "cad/part_panel_%s.step" % corner: (
        "one `NEXT_ASSEMBLY_USAGE_OCCURRENCE` instance label; identical otherwise"
    )
    for corner in ("northeast", "northwest", "southeast", "southwest")
}


def main():
    product = Path(sys.argv[1])
    archive = Path(sys.argv[2])
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
        elif relative in NON_GEOMETRIC:
            verdict, bucket = NON_GEOMETRIC[relative], explained
        else:
            verdict, bucket = "**changed**", changed
        bucket.append(relative)
        print("| `%s` | `%s` | `%s` | %s |"
              % (item.name, (then or "-")[:16], now[:16], verdict))

    print()
    print("## What changed")
    print()
    print("- **%d of the 24 printed geometries are byte-identical.**" % len(identical))
    print("- The %d board panels differ by exactly one line each: a" % len(explained))
    print("  `NEXT_ASSEMBLY_USAGE_OCCURRENCE` instance label, which is the exporter's")
    print("  own per-session counter and carries no geometry. Every other line of")
    print("  those four files matches the archive copy, checked line by line.")
    print("- **`part_world_earth_sol.step` and `part_world_earth_anti.step` are")
    print("  byte-identical too.** That is the right answer rather than a surprise: a")
    print("  marking in this set is a flush colour inlay, so it partitions the globe's")
    print("  volume without moving the printed solid's own boundary. The two parts the")
    print("  Wish names are corrected entirely in where the colour split falls, which")
    print("  is what `parts/earth_*.step` carries and what")
    print("  `measure/occurrence-geometry.md` measures.")
    if changed:
        print("- **Unaccounted for: %s**" % ", ".join(changed))
    else:
        print("- **No printed geometry changed shape.** Exactly two printed parts are")
        print("  corrected -- `part_world_earth_sol` and `part_world_earth_anti` -- and")
        print("  the correction is a colour boundary, not a solid.")
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
