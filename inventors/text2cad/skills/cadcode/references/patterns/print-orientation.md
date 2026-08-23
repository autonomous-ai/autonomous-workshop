# print-orientation

**Trigger:** load when the user asks "how should I print this", complains
about a part being weak in one direction, mentions layer lines / layer
adhesion, asks about supports, OR when the design has cantilevers,
threads, snap-fits, or anything load-bearing.

## Why this exists (the mechanics)

FDM prints in horizontal layers (XY) stacked vertically (Z). Strength is
anisotropic: in-plane (X/Y) the load runs through continuous filament,
while across layers (Z) it pulls on the bond between extruded layers, which
fails first. The in-plane/cross-layer ratio is typically ~2–4× (a rough
figure that shifts with material, temperature, and print settings — treat
it as "noticeably weaker in Z", not a hard constant). Overhangs and bridges also
constrain orientation (see `overhang-relief.md` for the 45° self-support
rule and bridging-span limits). Top surfaces are visibly rougher than
bottom (build-plate) surfaces. DESIGN the part in CadQuery so when sliced
with +Z up, layer lines run PERPENDICULAR to the load AND most surfaces
print self-supporting.

## The orientation rules

1. **Load direction**: orient so load runs ACROSS layer lines (in the XY
   plane), not parallel to them (vertical, in Z). A vertical post pulled
   sideways breaks at the weakest layer. Print it lying down.
2. **Threaded holes / press-fits**: orient the hole's axis along Z. Z
   gives the roundest holes (XY have stair-stepping; Z is layer-direction
   round).
3. **Overhangs / bridges**: rotate the part so overhangs face UP, not
   DOWN, and so open spans stay short. The 45° rule and the bridging-span
   limit live in `overhang-relief.md`; here it's a reason to reorient
   before you reach for supports.
4. **Cosmetic face down**: the build-plate side is glass-smooth. Put the
   user-visible face DOWN. (Trade-off: bottom face is sometimes also the
   one that needs holes, ribs, etc. — pick carefully.)

## CadQuery template (orient before exporting)

```python
import cadquery as cq

def orient_for_printing(part, p):
    """Apply a rotation so the natural CadQuery axes match the slicer's
    expected build orientation: +Z is UP, +X is "front-right", +Y is
    "back" (toward user).

    Required params:
      strongest_axis   - "x" | "y" | "z" (load direction in the part's design frame)
      print_face_down  - face name to put on the build plate ("bottom"|"front"|"left")
    """
    # If the strongest axis should run across layers (XY), rotate so
    # strongest_axis lies in the print's XY plane.
    if p.strongest_axis == "z":
        # Currently vertical in the design - lay it down.
        # .rotate(centre, axis, deg) - rotate 90 deg about +X to lay Z onto Y.
        part = part.rotate((0, 0, 0), (1, 0, 0), 90)

    # Put the chosen cosmetic face on the build plate.
    if p.print_face_down == "front":
        part = part.rotate((0, 0, 0), (1, 0, 0), -90)
    elif p.print_face_down == "left":
        part = part.rotate((0, 0, 0), (0, 1, 0), 90)

    # Drop the part so its lowest point sits on Z=0 (build plate).
    bb = part.val().BoundingBox()
    part = part.translate((0, 0, -bb.zmin))
    return part
```

(Uses real CadQuery APIs: `.rotate(centre, axis, deg)`, `.translate(vec)`,
`.val().BoundingBox()`.)

## Common orientation choices for specific parts

| Part | Best orientation | Why |
|---|---|---|
| Tall cantilever / lever arm | flat — beam axis horizontal | layer lines run across load |
| Threaded post / boss for a screw | hole axis vertical (along Z) | round hole; thread pulls across layers |
| Living hinge | hinge axis horizontal (perp to layer dir) | hinge web stays unbroken across layers |
| Snap-fit cantilever | beam axis horizontal | beam bends across layers, not along them |
| Gear (face cogs) | flat (rotation axis along Z) | clean cogs, support-free, round teeth |
| Long shaft / pin | flat — long axis horizontal | length-wise has no support issues; accept stair-stepping on round profile |
| Box with lid | lid open-side down on plate | best bottom finish + no support for inside |
| L-bracket | open side of L down OR rotated 45 deg | avoid overhang under one arm |
| Tall thin wall | wall plane vertical, length along X | avoid printing as a tall skinny tower |
| Hook / J-shape | open side of hook up | the curve self-supports under 45 deg |
| Threaded knob | flat — knob axis along Z | grip ridges print as concentric rings, hole is round |
| Phone stand / wedge | sloped face UP | the sloped surface is the overhang; flip it |

## Pitfalls

- Threaded hole printed sideways: threads come out as stair-steps, the
  screw won't engage. Always orient threaded/press-fit holes vertical.
- Lever arm printed standing up: snaps off cleanly along the weakest
  layer on first use. Lay it flat.
- "I'll just rotate it in the slicer": the slicer rotation is mechanical,
  but YOUR CadQuery code defines what +Z means. Picking a bad +Z hides
  the orientation decision from the user and from downstream review.
- Cosmetic vs functional trade-off: sometimes the cosmetic face is the
  one that needs supports. Add the supports or accept the rough texture —
  don't silently sacrifice strength to get a smooth top.
- Don't orient AFTER finishing the geometry — bake the orientation into
  the design from the start. Other patterns (cantilever reliefs, rib
  stiffeners, hinge axes) reference axes; rotating last invalidates
  those choices.
- Forgetting to drop the part to Z=0 after rotating: the slicer will
  accept floating parts but it confuses preview and bed-adhesion logic.
  Always translate so `bb.zmin == 0` after the final rotation.
- Rotating a `Workplane` with active tagged faces: tags survive rotation
  but their world coords change. If downstream code uses
  `.faces(">Z")`, that selector now picks a different face. Re-run
  selectors AFTER the orientation step.
