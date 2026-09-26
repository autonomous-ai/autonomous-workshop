"""Write one exact-state STEP per named position.

The product is shown in three exact states rather than three camera angles, so
each one has to be a real assembly of the real parts. This writes them; the
state sheet is rendered from the files it leaves behind.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import export_step

from assemblies.product import product_compound, triptych
from positions import POSITIONS


def write_state(name: str, target: Path, with_trays: bool = True) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    export_step(product_compound(name, with_trays), str(target))
    return target


def write_triptych(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    export_step(triptych(), str(target))
    return target


if __name__ == "__main__":
    where = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    for name in POSITIONS:
        print("%s -> %s" % (name, write_state(name, where / ("antisol-%s.step" % name))))
        print("%s -> %s" % (name, write_state(
            name, where / ("board-%s.step" % name), with_trays=False)))
