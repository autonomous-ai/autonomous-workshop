# Print optimisation

What a part costs to print is a question no other check asks. `validate` says
the solid is sound, `interfere` that nothing clashes, `check_fit` that it sits
on the bed, `check_mesh` that the artifact is sound. A wall the nozzle cannot
lay down and a solid core no one will ever see both pass all four.

```bash
python "$CAD_SKILL_ROOT/scripts/check_thickness" <project>/part_<role>.step.py --nozzle 0.4
python "$CAD_SKILL_ROOT/scripts/check_thickness" <project>/part_<role>.step.py --report measure/thickness.md
```

Three findings from one voxel sampling of the closed surface: surface area under
the minimum wall (**fails**), the thickness distribution, and the material
further than a given wall from any surface — what a shell would remove.

The mesh must be closed, so run `check_mesh` first; the gate refuses an open
surface rather than measuring one, because inside and outside are undefined on
it.

## Hollow with `cadprint`, never a bare `offset`

`offset(solid, -wall)` shrinks the solid instead of shelling it, and every gate
passes the undersized result. Hollow with `cadprint.hollow(part, wall)` (sealed)
or `cadprint.open_shell(part, wall, face)` (opened), and take walls from
`cadprint.min_wall(NOZZLE)` / `cadprint.shell_wall(NOZZLE)`, never a typed
number. `cadprint.savings()` reports both the volume removed and the filament
actually saved. A sealed void exports as two mesh shells, which `check_mesh`
reports correctly.

The design rules — why the offset shrinks, deriving walls from the nozzle, a
repeated feature's count as a wall, what hollowing is worth, when not to hollow,
repairing knife edges, and why a knife-edge fix must itself clear the minimum
wall: `skills/wiki/pages/printing/wall-thickness-and-hollowing.md`
(`wiki show wall-thickness-and-hollowing`).

## What the measurement cannot tell you

Thickness is measured by marching inward along each sample's own normal until
the ray leaves the material, on a voxel grid whose pitch the gate prints. Two
consequences:

- **A reading is quantised to half the pitch, and biased low by about one step**
  on any surface that does not line up with the grid. Measured on a 1.20 mm
  shell: 1.10 mm at a 0.2 mm pitch, 1.15 mm at 0.1 mm, converging from below,
  while an axis-aligned 2.00 mm wall read exact at every pitch. The gate fails
  only on what is below the limit by more than one step, and says so in the row
  label. Pass a finer `--voxel` when the margin matters.
- **The grid is bounded by memory, not by the part.** 11.3 M cells peaked at
  1.09 GB resident and 4.6 s; the pitch is coarsened automatically to stay
  inside that, so a large part is measured on a coarse grid. The pitch used is
  printed on the first line — read it before trusting a tenth of a millimetre.

- **The hollow volume is a voxel count, and the distance transform measures to
  the centre of the nearest outside cell** — about half a pitch beyond the
  surface. Left uncorrected that insets by less than the wall and over-reports
  the void: measured against the closed form on a 20 mm cube at a 1.2 mm wall,
  +14.3 % at a 0.4 mm pitch, +7.0 % at 0.2, +3.4 % at 0.1. The gate carries the
  half pitch in its threshold, which lands exact at all three; on a curved body
  expect a couple of percent either way (12.25 cm3 against a B-rep 12.46 on the lofted
  body in `wiki show wall-thickness-and-hollowing#hollowing-is-worth-less-than-the-volume-it-removes`). Take the volume as an estimate and the B-rep result from
  `cadprint.savings()` as the number.

Ray thickness is also bimodal by nature on a shell: a sample near an edge marches
along the wall rather than across it and legitimately reads the full span. The
median is the number to use; `max` is not a defect.

A knife edge left by a boolean is a real wall finding, not noise; repair the
construction, not the mesh or the threshold
(`wiki show wall-thickness-and-hollowing#knife-edges-are-walls-too`), then rerun
`check_mesh` and `check_thickness` on the freshly exported part.

## Record it

Do not call a part optimised from a volume in a chat log. `--report` writes a
markdown record next to the other verification artifacts, and a project that
ships a hollowed part should say the wall it was shelled at, beside the
`check_thickness` result that measured it.

## A multi-colour entry is gated as its union — `gen_print_union()`

A print entry whose `gen_step()` returns colour regions as separate solids (an
inlaid face, a two-colour emblem) is a plate the slicer wants and the mesh
gates cannot read: the shared faces are non-manifold edges to `check_mesh` and
flip the inside/outside count in `check_overhang` and `check_thickness`.
Define a second module-level function in the same entry,

```python
def gen_print_union():
    return the_part_as_one_solid()     # built from the primitives, not by fusing the regions
```

and `printlib` builds that for every mesh gate (`check_mesh`,
`check_overhang`, `check_thickness`, `repair_mesh`), while `gen_step()` stays
what `gen --write` exports. Build the union from the primitives -- the body
before its inlay cuts -- not by fusing the regions back together, which can
leave a sliver (`wiki show fdm-multi-material-design`).

In Workshop the union must also be the plate's own material: `printlib`
refuses a `gen_print_union()` whose volume differs from the regions' summed
volume (beyond 1e-5 of it, or 0.001 mm3) or whose bounding box sits more than
0.01 mm off theirs. The mesh gates, and the host's print-ready rerun, then
never measure a stand-in that prints more easily than the object that ships.

## Which way is up — `check_overhang`

Every other gate in this toolchain is blind to the build direction. `check_fit`
puts the part on the bed, `check_mesh` closes the shell, `check_thickness`
extrudes the walls — and a part whose every feature hangs in mid-air passes all
three, because none of them knows which way is up. A model can be sound,
watertight, thick enough and impossible to print unsupported.

```bash
python "$CAD_SKILL_ROOT/scripts/check_overhang" <project>/part_x.step.py --angle 45
```

It measures the down-facing surface in the pose the entry builds in, drops what rests
on the bed and what sits within a layer of material below it, clusters the rest,
and splits each region three ways:

- **bridge** — short enough to span, with material on both sides of it at its
  own level. A bore ceiling, a slot roof. Reported, not a failure.
- **ledge** — standing less than `--ledge` (1 mm) out from the material beside
  it. A rim, a step, the flat under a small boss. Reported, not a failure.
- **overhang** — neither. It **fails**: the slicer droops it or asks for
  support material.

Area cannot tell those apart, which is why the split matters: a horizontal bore
and a shelf of the same area and the same slope have completely different
answers. Two numbers decide it. **Span** is the **shorter** plan dimension,
because that is the one the slicer has to cross — a 10 x 40 mm roof is bridged
across the 10. **Reach** is how far the region stands out from anything at its
own level: half the span for a bore ceiling, the whole protrusion for a shelf.

The flank probe starts at the region's edge rather than the centre, so a
**cap on a stem** (a disc on a peg, a part printed key-down) is reported as the
overhang it is instead of as a bridge over its own stem.

What an overhang is, the cap-on-a-stem shape, the fixes in the order worth
trying, and why not to design at exactly 45°:
`skills/wiki/pages/printing/overhangs-and-print-orientation.md`
(`wiki show overhangs-and-print-orientation`).

**A verdict may not depend on which way round the part is.** The probe walks
outward one voxel at a time from the region's edge, and the cell it starts in
is not the same count in both directions: the grid origin is the centre of
cell 0, so the last cell at or before the edge is `floor((edge - origin) /
pitch)` -- the first cell past the edge going up, and that same cell going
down. Counting from one both ways skips a cell on the way down, and mirroring
a part turns every upward probe into a downward one. That single cell is enough
to turn a `bridge` into an `overhang`, so a part whose mirrored features are
geometrically identical can have them classified differently. When two
mirror-image features disagree, suspect the grid before the geometry.

## A wall is thin. An edge tapers. They are not the same finding

Thickness alone cannot tell a 0.5 mm panel from the tapered rim where a hole
breaks out of a curved face; `check_thickness` separates them by the width of
the sub-minimum band, which it reports per region as `band`:

- **wall** — the band is wider than one minimum wall. Fails; fix it in the
  generator.
- **taper** — narrower than that. Reported, counted against a 2 % surface
  budget, and not a failure. `--strict-thin` promotes tapers to failures.

Why a straight knife edge is always a wall, never a taper:
`wiki show wall-thickness-and-hollowing#a-wall-is-thin-an-edge-tapers-not-the-same-finding`.

## Every thin region, not just the thinnest point

`check_thickness` reports the sub-minimum samples **clustered into regions**,
worst first, because reporting only `thickness.min()` makes a part with several
knife edges take one round per edge -- fix the worst, re-run, meet the next, and
each round costs a rebuild, a tessellation and a fresh voxelisation.

Read the region list before editing. Samples within `4 x pitch` are one
region, so a wedge running along an edge stays one finding; a count in the
dozens means many separate places, not one bad face — often a repair feature
that is itself below the minimum wall
(`wiki show wall-thickness-and-hollowing#a-fix-for-a-knife-edge-must-clear-the-minimum-wall-itself`).
