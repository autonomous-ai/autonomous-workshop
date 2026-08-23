# overhang-relief

**Trigger:** load when the geometry has overhangs (downward-facing
surfaces, horizontal holes, deep horizontal cavities, T-shapes, etc.) and
you want to avoid support material — OR when the user complains a recent
print has sagging / hairy support scars on a critical face.

## Why this exists (the mechanics)

FDM extrudes each layer onto the one beneath it. The new bead can lean
out roughly 45° from vertical and still bond to the previous layer; past
that it droops into empty air. Slicer-generated supports work but leave
scars on the down-facing surface, waste filament, and add print time.
Many overhangs are FAKE — the same function can be achieved with a
self-supporting shape (chamfered bottoms, teardrop holes, 45° gussets).
Eliminating supports in CAD is almost always cheaper than printing with
them.

## Common reliefs

### 1. Horizontal hole → teardrop

Replace a horizontal circle with a teardrop (circle plus an apex pointing
up). The top half of a plain circular hole would otherwise hang as a 0°
overhang at its crown; the teardrop's apex is at 45°, fully
self-supporting along the entire ceiling.

### 2. Bottom of a bore → 45° chamfer

When a hole runs INTO the part from a vertical face (along Z), the top
of the bore would hang. Add a 45° chamfer on the TOP edge of the bore
mouth — `chamfer depth ≈ bore radius`, so the slope covers the full
horizontal span of the would-be ceiling. The chamfer prints as a
self-supporting sloped wall; the actual round bore starts beneath it.

### 3. T-shape under-cut → bridge or sacrificial wall

A T (or H) profile has two outward-facing horizontal undercuts. As a rule
of thumb, an unsupported bridge is reliable up to a few× nozzle width
(roughly ~5–10 mm, depending on cooling and material), so the slicer can
bridge a short span on its own. Beyond that the bridge sags — add a
sacrificial wall, a thin tab from the bottom of the undercut to the bed
that the user snips off after printing.

### 4. Long horizontal flat ceiling → tent it

A long horizontal ceiling drops in long bridges. Replace with two 45°
walls that meet in a peak, like a roof. Cosmetic only on the inside;
the outside silhouette stays unchanged if you're tenting an internal
cavity.

### 5. Sloped walls past 45° → step them

A 30°-from-vertical wall sags. Break it into a stair-step of 45° segments
(each layer offsets by ≤ layer_height). Total volume same, droop gone.

## CadQuery templates

```python
import cadquery as cq


def teardrop_hole(part, diameter, depth, axis="x"):
    """Cut a teardrop-shaped hole (apex pointing +Z) through ``part``
    along the given ``axis``.

    Sketch: a circle plus a triangular cap. The cap's sloped edges leave
    the circle tangentially at +/- 45 degrees, so every printed layer of
    the hole ceiling is supported by the layer below.
    """
    r = diameter / 2
    plane = {"x": "YZ", "y": "XZ"}[axis]
    sk = (
        cq.Workplane(plane)
        .moveTo(-r, 0)
        .threePointArc((0, -r), (r, 0))      # bottom half-circle
        .lineTo(r * 0.707, r * 0.707)        # 45 deg rise (right side)
        .lineTo(0, r * 1.414)                # peak
        .lineTo(-r * 0.707, r * 0.707)       # 45 deg fall (left side)
        .close()
    )
    return part.cut(sk.extrude(depth))


def bore_with_chamfered_top(part, diameter, depth, chamfer=None):
    """A vertical-axis bore where the top edge has a 45° chamfer that
    'opens' the mouth, making the print self-supporting at the rim.

    ``chamfer`` is the chamfer leg length. It MUST be smaller than the wall
    of material around the bore mouth — a chamfer that reaches into the part
    wall (or equals the bore radius) makes the operation fail with
    ``StdFail_NotDone``. Default is a conservative ``min(1.0, r/2)`` mm; raise
    it (up to ~the wall thickness) for a bigger lead-in. For a fully
    self-supporting *through* hole, prefer ``teardrop_hole`` instead.
    """
    r = diameter / 2
    c = chamfer if chamfer is not None else min(1.0, r / 2)
    return (
        part.faces(">Z").workplane()
        .hole(diameter, depth)
        .faces(">Z").edges("%CIRCLE").chamfer(c)
    )


def stepped_overhang(part, length, height, steps, thickness):
    """Approximate a shallow sloped wall as a stack of 45 deg steps so
    each step's overhang is at most ``length / steps`` -- safe for FDM.

    Each step is built on its own offset workplane so the staircase
    actually climbs in Z; using a 2D Y coordinate for the height would
    just smear the steps across a flat slab.
    """
    dx = length / steps
    dz = height / steps
    result = part
    for i in range(steps):
        step = (
            cq.Workplane("XY")
            .workplane(offset=i * dz)
            .moveTo(i * dx, 0)
            .rect(dx, thickness, centered=False)
            .extrude(dz)
        )
        result = result.union(step)
    return result
```

(Real CadQuery APIs used: `moveTo`, `threePointArc`, `lineTo`, `close`,
`extrude`, `cut`, `union`, `hole`, `chamfer`, `faces`, `edges`,
`workplane`. The teardrop construction is the canonical self-supporting
horizontal hole.)

## When to use which relief

Span figures below are rules of thumb tied to bridging capability (a few×
nozzle width, ~5–10 mm before a bridge sags — material- and
cooling-dependent), not hard cutoffs:

| Situation                          | Use                                       |
|------------------------------------|-------------------------------------------|
| Horizontal screw hole              | teardrop hole                             |
| Vertical hole on the underside     | chamfered bottom, OR flip the part        |
| Wide flat ceiling (past bridging limit) | tent / roof shape                    |
| Narrow slot ceiling (near bridging limit) | bridge with 1-2 sacrificial threads |
| 30° wall (past 45° from vertical)  | step into 45° increments                  |
| T-shape undercut                   | sacrificial breakaway wall                |
| Small overhang (sub-mm)            | do nothing — slicer bridges it cleanly    |

## Pitfalls

- Teardrop pointing the WRONG way: apex must point in the print's +Z
  direction, NOT the design's +Z direction. If the part is rotated 90°
  for printing, the teardrop apex must be rotated to match.
- Chamfered bore rim that's too shallow: rim is still horizontal in the
  middle. Aim for `chamfer depth ≈ bore radius` so the slope covers the
  full horizontal portion of the ceiling.
- Aggressive overhang relief is ugly on the visible face. Use slicer
  supports on cosmetic surfaces and reserve geometric reliefs for hidden
  or functional surfaces.
- A "self-supporting" 45° wall in PLA at 60 mm/s prints fine; the same
  wall in PETG at 40 mm/s droops. Material matters. PETG, TPU and most
  ABS variants are more conservative — design to 40° in tricky cases.
- Don't redesign to remove a sub-millimetre overhang — modern slicers
  bridge a fraction of a millimetre trivially. Reliefs earn their keep once
  a span approaches the bridging limit (a few× nozzle width, ~5–10 mm
  depending on cooling and material).
- Stair-stepping a sloped wall makes the cosmetic face stairstepped;
  acceptable hidden, ugly visible. Step only the non-visible faces.
- `edges("%CIRCLE")` on `faces(">Z")` picks ALL circular edges on the
  top face. If the part has multiple holes on the same face, filter
  further (by radius or position) before chamfering, or you'll chamfer
  the wrong rim.
- Combining reliefs on the SAME hole: a chamfered top + teardrop body
  works when the bore axis lies in the print's XY plane. On a vertical
  bore, only the chamfer applies — a teardrop on a vertical hole is
  meaningless.
- Sacrificial walls must be one perimeter thick (≈ 0.4 mm) and meet the
  part along a sharp edge — too thick and the user can't snap them off
  cleanly; too thin and they detach mid-print and rattle into the
  nozzle.
