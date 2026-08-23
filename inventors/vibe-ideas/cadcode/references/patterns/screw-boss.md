# screw-boss

**Trigger:** load when the user asks for a screw boss, mounting post, M2/M3/M4
screw hole with a post, PCB standoff, "screw it into the base", or any
threaded fastener that needs a printed post for the screw to bite into.

## Why this exists (the mechanics)

A bare hole in a flat surface only has as much pull-out strength as one wall
thickness's worth of plastic. A boss extends the engagement length (typ 2-3x
screw diameter) and concentrates material around the fastener. For self-tap
into plastic the pilot hole equals the screw's minor diameter (smaller than the
clearance hole); for a machine-screw pass-through use the standard clearance
diameter. A counter-bored or countersunk top lets the head sit flush. Tall
bosses also want radial ribs (3-4 fins at 45 degrees) so the post doesn't snap
off when side-loaded — see "Beyond the helper" below.

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper extrudes the
posts at each position, then cuts the pilot/clearance hole with optional
counter-bore or countersink head treatment in one call:

```python
from cadlib.mounting import add_screw_post

part = add_screw_post(
    part,
    positions=[(0, 0)],     # boss centres in the open_face plane
    screw_size="M3",        # key into SCREW_TABLE
    boss_height=8.0,        # how tall the post rises from the surface
    boss_od=None,           # None → auto from the OD-sizing rule below
    hole_type="self_tap",   # "self_tap" (taps into plastic) | "clearance" (through-bolt)
    countersink=None,       # None | "cbore" | "csink"
    cbore_depth=3.0,        # head recess depth when countersink="cbore"
    open_face=">Z",         # face the bosses stand up from
)
```

Screw dimensions (clearance / self_tap / cap_head_dia / cap_head_h) are owned by
`cadlib/tables.py::SCREW_TABLE` and keyed by `screw_size`; the helper reads them
for you. `Read` that file if you need the raw numbers — don't transcribe them
into your model. The helper raises `ValueError` for an unknown `screw_size`. For
`countersink="cbore"` the helper sizes the head recess from `cap_head_dia` plus a
fit margin — don't restate a separate number, defer to the helper.

## Boss diameter sizing rule

If you pass `boss_od=None` the helper sizes it for you; pass an explicit value
only to override. The rule is `boss OD = 2 x screw_clearance + 2 x wall`, with
`wall >= 1.5 mm`. Worked example: an M3 clearance hole of 3.4 mm gives
`OD >= 3.4 + 3.0 = 8.8 mm` (round up to ~10 mm in practice).

## Pull-out strength rule

For self-tap into PLA/PETG, `engagement length ≈ 2 x screw-Ø`. Make `boss_height`
at least this or the screw strips on first fastening — e.g. an M3 wants ~6 mm
engaged, an M5 ~10 mm.

## Beyond the helper

Radial ribs are **not** in `add_screw_post` — a tall, unribbed boss
(height > 1.5x OD) snaps off when side-loaded. This is a candidate to promote
into the helper. Until then, add 4 thin fins radiating from each boss after the
helper call:

```python
import cadquery as cq

def custom_screw_post_ribs(part, *, positions, boss_od, rib_height,
                           rib_thickness=1.8, rib_count=4, base_z=0.0):
    """Add radiating stiffening ribs around each boss (not in cadlib)."""
    for (x, y) in positions:
        for i in range(rib_count):
            angle = i * (360.0 / rib_count)
            rib = (
                cq.Workplane("XY")
                .box(boss_od / 2.0, rib_thickness, rib_height,
                     centered=(False, True, False))
                .translate((x, y, base_z))
                .rotate((x, y, 0), (x, y, 1), angle)
            )
            part = part.union(rib)
    return part
```

Make `rib_height` ~0.5x `boss_height`. This is a candidate to promote into
`add_screw_post` as a `ribs=` option.

## Pitfalls

- Self-tap hole too big -> screw spins free; too small -> cracks the boss.
  Let the helper supply the self_tap diameter from `SCREW_TABLE`.
- No ribs on tall bosses (height > 1.5x OD) -> boss snaps off when
  side-loaded. The helper has none — add them (see "Beyond the helper").
- Cap-head counter-bore: `cbore_depth` must be deeper than `cap_head_h` or the
  screw sits proud.
- Print orientation: if the boss is parallel to layer lines, pull-out
  strength drops 50%. Orient so the screw axis is vertical (boss extrudes
  from the build plate upward).
- For PCB standoffs: separate the boss top from the PCB face by 0.5 mm
  using a tiny shoulder, so the screw clamps the PCB cleanly against the
  shoulder, not against a slightly-domed boss top.
- "Heat set insert" is a different pattern - see heat-set-insert-pocket.md.
