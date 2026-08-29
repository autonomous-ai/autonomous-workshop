"""Fast algebraic audit; generic CAD gates own geometry and mesh facts."""

from __future__ import annotations

import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

# Both imports resolve from the copied CAD project.  In particular, cadfits.py
# is an exact vendored copy of the run-local CAD skill derivation helper, so
# this audit remains runnable inside the host's isolated product verifier.
import cadfits
import storm_reveal_lib as p


def main() -> int:
    assert abs(p.LIGHTNING_SOCKET - cadfits.slot_for(p.DRIVE_SQUARE, 0.10)) < 1e-9
    assert abs(p.GUIDE_SLOT_W - cadfits.slot_for(p.GUIDE_PIN_D, 0.20)) < 1e-9
    assert p.PIVOT_BORE_D > (2.0 ** 0.5) * p.DRIVE_SQUARE
    assert p.DRIVE_LOCAL_END_Z + p.RAINBOW_Z >= p.PIVOT_POCKET_DEPTH
    assert p.GUIDE_LOCAL_END_Z + p.LIGHTNING_Z >= p.GUIDE_SLOT_DEPTH
    assert p.RAINBOW_Z + p.MOTIF_THICKNESS <= p.LIGHTNING_Z - p.FACE_GAP + 1e-9
    assert p.LIGHTNING_Z + p.MOTIF_THICKNESS <= -p.FACE_GAP + 1e-9
    print("PASS: shared fit derivations, stack gaps, drive depth, and guide depth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
