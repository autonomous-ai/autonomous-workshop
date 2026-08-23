# nut-trap

**Trigger:** load when the user asks for a nut trap, embedded nut, captive nut,
hex pocket, "trap an M3 nut", or any "screws threading into a standard nut
that's hidden inside the print".

## Why this exists (the mechanics)

A standard hex nut is dropped into a hex-shaped pocket inside the print, then a
screw inserted from the opposite side threads into the nut. The pocket walls
prevent the nut from spinning while the screw is tightened, so torque transfers
into the captured nut instead of stripping the plastic. Way cheaper than
heat-set inserts (a 100-pack of M3 nuts is around $3), no soldering iron
needed, and it works in any plastic since no heat is applied. Common in printer
parts, drone frames, modular hardware, and any joint that will be assembled and
disassembled repeatedly.

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper cuts the hex
pocket (recessed so the nut sits flush below the surface) at `pocket_face` and
a coaxial screw clearance hole entering from the opposite `screw_face`, in one
call:

```python
from cadlib.mounting import add_nut_trap

part = add_nut_trap(
    part,
    positions=[(0, 0)],     # nut centres in the pocket_face plane
    nut_size="M3",          # key into NUT_TABLE
    pocket_face=">Z",       # face the nut drops into (top-drop or below-roof)
    screw_face="<Z",        # opposite face the screw enters from
)
```

Nut dimensions (`flat`, `thick`, `pocket_flat`, `pocket_h`, `screw_clear`) are
owned by `cadlib/tables.py::NUT_TABLE` and keyed by `nut_size`; the helper reads
them for you. `Read` that file if you need the raw numbers — don't transcribe
them. The pocket flats follow the generic FDM rule `pocket_flat = nominal +
0.2 mm`, so the nut drops in without forcing. The helper raises `ValueError` for
an unknown `nut_size`.

This covers the standard top-drop (`pocket_face=">Z"`) and below-roof
(`pocket_face="<Z"`) insertion modes. The side-slide slot variant is not in
the helper — see "Beyond the helper".

## Insertion approaches

There are three ways to get the nut into the pocket:

1. **Top-drop with bridging** (helper, `pocket_face=">Z"`, `screw_face="<Z"`):
   pocket opens up, screw enters from below. The slicer must bridge over the
   nut once it's inserted, so **pause the print** at the right layer, drop in
   the nut, resume. Reliable but manual.
2. **Below-the-pocket roof** (helper, `pocket_face="<Z"`, `screw_face=">Z"`):
   pocket opens downward; layers BRIDGE over the empty pocket as it prints.
   Drop the nut in from below before screwing. Needs good bridging settings.
3. **Side-slide slot** (not in cadlib — see below): pocket opens to a side
   face via a slot. Slide the nut in horizontally after printing. No print
   pause, but the slot leaves a visible seam.

## Beyond the helper

The side-slide slot is **not in cadlib** — it is the cleanest insertion mode
(no bridging, no print pause) and a candidate to promote into `add_nut_trap`
as a `slot_face=` option. The idea: cut the same hex pocket, then a
rectangular channel the width of the pocket flats running from a side face in
to the pocket, so the nut slides in laterally.

```python
import cadquery as cq
from cadlib.tables import NUT_TABLE

def custom_nut_trap_slot(part, *, positions, nut_size="M3",
                         pocket_face=">Z", screw_face="<Z", slot_face=">X"):
    """Hex nut trap with a side-slide channel (not in cadlib).

    Adds, to the standard pocket + screw clearance, a slot from ``slot_face``
    into each pocket so the nut pushes in horizontally instead of dropping.
    """
    n = NUT_TABLE[nut_size]
    for (x, y) in positions:
        # Hex pocket from the pocket face.
        part = (
            part.faces(pocket_face).workplane()
            .pushPoints([(x, y)])
            .polygon(6, n["pocket_flat"], circumscribed=False)
            .cutBlind(-n["pocket_h"])
        )
        # Coaxial screw clearance from the opposite face.
        part = (
            part.faces(screw_face).workplane()
            .pushPoints([(x, y)])
            .hole(n["screw_clear"])
        )
        # Slide-in channel: a slot the pocket's flat width, cut from the side
        # face through to the pocket so the nut can be pushed in laterally.
        part = (
            part.faces(slot_face).workplane()
            .pushPoints([(x, y)])
            .rect(n["pocket_h"], n["pocket_flat"])
            .cutThruAll()
        )
    return part
```

Make the slot at least as wide as `pocket_flat`; a hair wider eases the slide
at the cost of a looser-looking seam.

## Pitfalls

- Pocket too tight: nut won't seat without forcing — risks splitting walls.
  Stick to `pocket_flat = nominal + 0.2 mm` (already in the table).
- Pocket too loose: nut spins under torque, screw turns forever. Tighten
  the pocket by 0.1 mm if it spins.
- Pocket too shallow: nut sits proud, mating surface doesn't sit flat. The
  table's `pocket_h` is `nut_thick + 0.2 mm`.
- For top-drop: the slicer must bridge >= `pocket_flat` distance over the
  nut. PETG bridges worse than PLA — widen the pocket ~1 mm for PETG.
- Print orientation: hex pocket walls are vertical, so no overhang issues
  from the pocket itself. The screw hole through it may show a bridging step
  depending on orientation.
- Don't use a wing nut or square nut here — the hex pocket is sized for ISO
  metric hex only. For other shapes, build a custom pocket.
