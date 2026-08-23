# Multi-part designs with `cq.Assembly`

**Trigger:** load when the design has **physically separate parts** —
lid + base, hinge halves, removable cover, screw-on cap, robot chassis +
wheels, PCB + enclosure, body + button + dial. Anything the user prints
as multiple pieces and assembles after.

For a single-piece print (one solid that comes off the bed in one go), do
NOT use Assembly — just `.union()` everything into a single solid and return
it from `gen_step()`. Assembly is for parts that should ship as separate solids.

For parts that share a **moving** joint or form a closed loop (a four-bar
walking leg, crank + rocker, scissor lift), placement is not a fixed offset —
the shared joint must be *solved* so the pins coincide. See
`references/kinematic-placement.md` (and the `four-bar-linkage` pattern) before
posing a linkage; eyeballing each link's angle leaves the joints apart and trips
`disconnected_bodies`.

## Why `cq.Assembly`, not `union` for these

A unioned multi-part model:

- exports as one fused STL that the user must split in the slicer (lossy,
  loses tolerance, breaks parametric clearances);
- can't have **interference fits, clearances, or motion** between parts
  because they're literally one solid;
- buries the per-part logic in a single chain.

`cq.Assembly` keeps each part as its own solid with its own placement,
exports each piece separately (or together), preserves color/material
metadata, and renders the assembled view for visual QC.

## Canonical pattern

```python
import cadquery as cq

# --- Parts: each is a plain Workplane built around its own origin ---

def make_base(p):
    """Box with floor, screw bosses, port cutouts. Built at origin, lid
    side at +Z."""
    base = (
        cq.Workplane("XY")
        .box(p.length, p.width, p.height)
        .faces(">Z").shell(-p.wall)
    )
    base = add_screw_bosses(base, p)
    base = add_port_cutouts(base, p)
    return base

def make_lid(p):
    """Matching lid. Built at origin, mating side at -Z."""
    lid = (
        cq.Workplane("XY")
        .box(p.length, p.width, p.lid_thickness)
    )
    lid = add_lid_lip(lid, p)            # tongue that fits the base shell
    lid = add_lid_screw_holes(lid, p)
    return lid

# --- Assembly: place parts in the assembled-product frame ---

def make_assembly(p):
    assy = cq.Assembly()
    assy.add(make_base(p), name="base", color=cq.Color("gray"))
    assy.add(
        make_lid(p),
        name="lid",
        loc=cq.Location(cq.Vector(0, 0, p.height + p.lid_gap)),
        color=cq.Color("steelblue"),
    )
    return assy

# --- Entry point: return the Assembly straight from gen_step() ---

def gen_step():
    """cadpy ingests a cq.Assembly natively — no compound, no manual
    export. It walks the named children into the STEP (each part keeps its
    name + color + placement) and meshes the assembled scene to the STL."""
    return make_assembly(Params())
```

Do **not** flatten the Assembly with `result = cq.Workplane().add(assy.toCompound())`,
and do **not** hand-export per-part STLs with `cq.exporters` — `import os` /
file writes are blocked by the sandbox, and they are unnecessary: returning the
`cq.Assembly` (or a `{"children": [...]}` envelope / a `list` of parts) is the
supported contract (in the Panda repo: `docs/panda-interfaces.md` §1).

What you get on disk after `scripts/cad`. Run it with ``--stem
<project>_assembled`` so the combined-all-parts file is self-describing (the STL
is always the assembled scene — the name should say so):

- `<project>_assembled.step` — **the archival deliverable.** Each part is
  preserved as its own named, colored solid (XCAF labels), so it opens in FreeCAD
  / Fusion / the slicer as separable bodies — not one fused lump.
- `<project>_assembled.stl` — the assembled scene as a single mesh: the viewer's
  preview and the printable mesh. cadpy writes **one** STL (the whole scene), not
  one per part.
- `<project>_assembled.step.json` — source hash, `is_solid`, `volume_mm3`, mesh
  tolerances.

(A single-part design combines nothing — keep the plain ``<project>`` stem.)

Because the STL is the *assembled* scene, parts stacked in assembled position
(lid on top of base) are not laid out for printing. If the user needs each part
on the bed, either (a) tell them to separate the bodies from the STEP / split
the STL in their slicer, or (b) build a flat **print-layout** assembly that
places the parts side-by-side on `Z=0` instead of in assembled position, and
hand that off as the printable file.

## `cq.Location` placement

```python
cq.Location(cq.Vector(x, y, z))                       # translate only
cq.Location(cq.Vector(x, y, z), cq.Vector(0, 0, 1), 90)  # translate + rotate 90° about Z
```

The lid sits `p.lid_gap` above the base in the assembled view (typically
0.3–0.5 mm for FDM clearance). The exported lid STL is at the origin,
*not* at `z = height + gap` — the user only sees the assembled position in
the preview.

## When to split into separate parts (decision rule)

| Situation | Single solid (`union`) | Assembly |
|---|---|---|
| Part has no moving / removable pieces | ✓ | |
| Lid that opens / removes | | ✓ |
| Hinge with two halves | | ✓ |
| Snap-fit cover | | ✓ |
| Press-fit insert (printed) | | ✓ |
| Wheels / gears on a shaft | | ✓ |
| Decorative attached features | ✓ | |
| Robot chassis + motors + arms | | ✓ |

The rule: **if the user expects to print, hold, and assemble two pieces in
their hands, those are two parts.** If the model comes off the bed and is
done, it's one solid.

## Mating clearances are non-negotiable

When the design has parts that touch, plug in, or slide into each other,
the gap must be parameterised:

```python
class Params:
    lid_gap         = 0.4       # vertical clearance (lid sits this far above base rim)
    lid_lip_clear   = 0.3       # horizontal clearance (lip-to-shell on each side)
    shaft_clear     = 0.2       # for printed shafts in printed holes
    snap_clear      = 0.15      # snap-fit cantilever / catch
```

Each clearance gets bigger as the parts get bigger and on softer materials
(PETG, TPU). See `references/hobbyist-defaults.md` and the relevant
`references/patterns/*.md` for fit-specific values.

## Coordinate-frame discipline

Two frames coexist and getting them mixed is the #1 Assembly bug:

1. **Part-local frame** — each `make_*` builds at the origin with a clear
   convention (e.g., base sits with floor at -Z, mating face at +Z; lid
   sits with mating face at -Z). The exported STL uses this frame.
2. **Assembly frame** — `cq.Location(...)` places each part in the
   assembled product. The preview render and the assembled-STEP use this
   frame.

Never do "build the lid in assembled position then move it back to the
origin." Always build in the part-local frame; let the Assembly do the
placement.

## Per-part orientation for printing

The same part may want a different orientation in the assembled view vs.
on the print bed. Conventionally:

- The Assembly view shows the **assembled** orientation (lid on top, hinge
  pin axis horizontal, etc.).
- Each exported STL is in the **part-local** frame the `make_*` returned.
  The user re-orients in their slicer.

If a part has a strongly-preferred print orientation (e.g., threaded boss
axis must be vertical — see `references/patterns/print-orientation.md`),
build it in *that* frame so the exported STL is print-ready. The Assembly
then rotates it into the assembled view.

## Pitfalls

- **Forgetting clearances** → printed parts won't mate. Always parameterise
  the gap, never bake in 0.
- **Mating two parts whose mating faces are both at +Z** → they collide in
  the assembled view. One part's mating face needs to be at -Z, or
  rotate it 180° in the Assembly `Location`.
- **Putting hardware (M3 nuts, bearings) in the Assembly** as separate
  parts → useful for visual reference but they won't print. Mark them
  clearly: `assy.add(nut, name="m3_nut_REFERENCE_ONLY", color=cq.Color("gold"))`.
- **Asymmetric parts that look symmetric** (e.g., a lid with a single
  notch) → user can install them backwards. Add a visual cue (asymmetric
  chamfer, embossed arrow) or break the symmetry geometrically.
- **Exploded view ≠ assembly position.** If you want an exploded view for
  the user, render that separately; the canonical Assembly should always
  be in the *assembled* position so a sanity-check render shows the
  product as it will be.
