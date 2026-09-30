"""Every occurrence of an assembly STEP, by label, with its exact measure.

`parts/*.step` cannot be compared byte for byte across runs: `production.py`
writes them through build123d's own exporter, which stamps the file with the
wall-clock time it ran.  The combined `antisol.step` is written by `cadgen`,
which stamps a fixed epoch, but one changed body renumbers every entity after
it, so a line diff of that file says nothing either.

What does compare is the geometry.  This dumps label -> (solid count, volume,
bounding box) for one assembly STEP, so two runs of the set can be checked
occurrence by occurrence.

    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py <assembly.step> > out.json
    "$WORKSHOP_PYTHON" measure/occurrence_geometry.py --compare <was.json> <now.json> \\
        <occurrence-prefix> [<occurrence-prefix> ...]

The prefixes are the occurrence families this revision was asked to change --
`mars_sol_ mars_anti_` on this run. Anything that gained, lost or moved a solid
outside them is a finding, not a result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: mm3 and mm.  A boolean run on the same source is reproducible to far better
#: than this; anything above it is a real difference in the solid.
VOLUME_TOLERANCE = 1e-4
BOX_TOLERANCE = 1e-6


def measure(path: Path) -> dict:
    from build123d import Compound, import_step

    shape = import_step(str(path))
    found: dict[str, dict] = {}

    def walk(node):
        children = list(getattr(node, "children", ()) or ())
        if children:
            for child in children:
                walk(child)
            return
        label = getattr(node, "label", "") or "<unlabelled>"
        solids = list(node.solids())
        if not solids:
            return
        box = node.bounding_box()
        found.setdefault(label, {
            "solids": 0, "volume": 0.0,
            "min": [box.min.X, box.min.Y, box.min.Z],
            "max": [box.max.X, box.max.Y, box.max.Z],
        })
        entry = found[label]
        entry["solids"] += len(solids)
        entry["volume"] += sum(solid.volume for solid in solids)
        entry["min"] = [min(a, b) for a, b in zip(entry["min"], [box.min.X, box.min.Y, box.min.Z])]
        entry["max"] = [max(a, b) for a, b in zip(entry["max"], [box.max.X, box.max.Y, box.max.Z])]

    walk(shape)
    return {"source": path.name, "occurrences": found}


def compare(was: dict, now: dict, allowed: tuple[str, ...]) -> int:
    left, right = was["occurrences"], now["occurrences"]
    gone = sorted(set(left) - set(right))
    fresh = sorted(set(right) - set(left))
    moved = []
    for name in sorted(set(left) & set(right)):
        a, b = left[name], right[name]
        if a["solids"] != b["solids"]:
            moved.append((name, "solid count %d -> %d" % (a["solids"], b["solids"])))
            continue
        if abs(a["volume"] - b["volume"]) > VOLUME_TOLERANCE:
            moved.append((name, "volume %.6f -> %.6f mm3" % (a["volume"], b["volume"])))
            continue
        drift = max(
            abs(p - q)
            for key in ("min", "max")
            for p, q in zip(a[key], b[key])
        )
        if drift > BOX_TOLERANCE:
            moved.append((name, "bounding box moved by %.2e mm" % drift))
    print("# Occurrence geometry, this run against the published set")
    print()
    print("`%s` -> `%s`. Compared by label: solid count, exact volume and"
          % (was["source"], now["source"]))
    print("bounding box, at %g mm3 and %g mm." % (VOLUME_TOLERANCE, BOX_TOLERANCE))
    print()
    print("A repeated geometry -- the twelve belt tiles, the six corona cells, the")
    print("two trays -- is stored once and instanced, so the reader returns all of")
    print("its copies under one label. The count and the volume below are the")
    print("label's whole family, which is why %d labels carry %d solids."
          % (len(left), sum(item["solids"] for item in left.values())))
    print()
    print("- labels published: %d, carrying %d solids"
          % (len(left), sum(item["solids"] for item in left.values())))
    print("- labels in this run: %d, carrying %d solids"
          % (len(right), sum(item["solids"] for item in right.values())))
    print("- identical in geometry: %d" % (len(set(left) & set(right)) - len(moved)))
    print()
    for label, rows in (("Gone", gone), ("New", fresh)):
        print("## %s" % label)
        print()
        print("\n".join("- `%s`" % name for name in rows) if rows else "None.")
        print()
    print("## Changed geometry")
    print()
    if moved:
        for name, why in moved:
            print("- `%s` — %s" % (name, why))
    else:
        print("None.")
    print()
    strays = [
        name for name in gone + fresh + [item[0] for item in moved]
        if not name.startswith(allowed)
    ]
    where = " and ".join("`%s*`" % prefix for prefix in allowed)
    print("## Verdict")
    print()
    if strays:
        print("**Outside %s: %s**" % (where, ", ".join(sorted(set(strays)))))
        return 1
    print("Nothing outside %s gained, lost or moved a solid." % where)
    return 0


def main() -> int:
    if sys.argv[1] == "--compare":
        was = json.loads(Path(sys.argv[2]).read_text())
        now = json.loads(Path(sys.argv[3]).read_text())
        allowed = tuple(sys.argv[4:])
        if not allowed:
            raise SystemExit("name the occurrence prefixes this revision corrects")
        return compare(was, now, allowed)
    print(json.dumps(measure(Path(sys.argv[1])), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
