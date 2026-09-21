"""Write one production STEP per occurrence into the product tree.

The shop receives the set as addressable, colourable solids: one file per
occurrence, named for the part and the spool that prints it.  Each file holds
that occurrence's own local geometry in its own print orientation -- the
assembly package carries where it sits.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import export_step

from assemblies.product import occurrences
from colors import filament


def write_parts(target: Path) -> int:
    target.mkdir(parents=True, exist_ok=True)
    seen = set()
    for item in occurrences():
        name = item["name"]
        if name in seen:
            raise ValueError("duplicate occurrence name %r" % name)
        seen.add(name)
        shape = item["shape"]
        shape.color = filament(item["colour"])
        shape.label = name
        export_step(shape, str(target / ("%s.step" % name)))
    return len(seen)


if __name__ == "__main__":
    where = Path(sys.argv[1] if len(sys.argv) > 1 else "../parts")
    print("wrote %d production parts to %s" % (write_parts(where), where))
