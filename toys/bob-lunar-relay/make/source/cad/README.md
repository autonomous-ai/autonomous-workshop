# Lunar Relay CAD project

`moon_relay.step.py` assembles every part in the neutral, locked pose. The three `part_*.step.py` files are the actual print targets and each places its part on Z=0.

Print envelope: `--bed 120x120x120`

| Entry | Print stance | Supports |
|---|---|---|
| `part_lunar_base.step.py` | base plate on bed | none |
| `part_moon_rocker.step.py` | broad rocker underside on bed | none |
| `part_quarter_turn_axle.step.py` | broad axle head on bed | none; locking tab grows on sloped shoulders |

Assembly: place the rocker between the two pivot cheeks. Align the axle's far tab horizontally with all three keyways, slide the axle through the near cheek, rocker, and far cheek, then rotate the head 90° until the far tab is vertical. The vertical tab is wider than the bearing opening and blocks straight withdrawal. Reverse those steps for service.

Operation: put the base on a level desk. Press the top of either cratered moon; the other rises. Release or press the raised side to return. Keep fingers above the crater rims and out of the mechanism gaps.

The `measure/motion.json` sweep checks the declared ±8° rocker motion, the axle's clear quarter-turn space, and blocked axial withdrawal in the locked orientation. It is rigid digital evidence only; it does not model friction, printer shrinkage, applied force, fatigue, or wear.

Rebuild from the workspace root with the materialized CAD tools. Run `verify_project` with `--fresh --exports --strict-fit`; no powered-system gate applies.

The generators normally import the Workshop's canonical `cadfits` helper. For
standalone host audits, where only a relocated copy of this project is placed
on `PYTHONPATH`, `moon_relay_lib.py` falls back to the project-contained
`cadfits_fallback.py`. That compatibility subset is pinned to the canonical
helper's SHA-256 in its module docstring and covers only the two fit functions
used by this design. No workspace-relative import path is required.

The combined assembly STEP intentionally carries labels and placements but no
per-child colors. Open CASCADE can permute multiple assembly style records
between fresh processes even when geometry is identical, changing the declared
STEP bytes. The individual printable-part entries retain their colors, and the
assembled STL render review supplies the intended product palette separately.
