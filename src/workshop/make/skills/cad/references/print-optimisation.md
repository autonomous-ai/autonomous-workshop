# Print optimisation

What a part costs to print is a question no other check asks. `validate` says
the solid is sound, `interfere` that nothing clashes, `check_fit` that it sits
on the bed, `check_mesh` that the artifact is sound. A wall the nozzle cannot
lay down and a solid core no one will ever see both pass all four.

```bash
python "$CAD_SKILL_ROOT/scripts/check_thickness" <part>.stl --nozzle 0.4
python "$CAD_SKILL_ROOT/scripts/check_thickness" <part>.stl --report measure/thickness.md
```

Three findings from one voxel sampling of the closed surface: surface area under
the minimum wall (**fails**), the thickness distribution, and the material
further than a given wall from any surface — what a shell would remove.

The mesh must be closed, so run `check_mesh` first; the gate refuses an open
surface rather than measuring one, because inside and outside are undefined on
it.

## `offset(solid, -wall)` does not hollow anything

This is the expensive one, because the sign reads like "shell inward" and the
result is a valid solid either way.

```python
offset(Box(20, 20, 20), -2, kind=Kind.INTERSECTION).volume    # 4096.0
```

4096 is 16 cubed. It **shrank the box**; a 2 mm shell is 3904. The same call on
a sphere returns the smaller ball, not a shell. Nothing downstream notices — the
part is closed, manifold, positive-volume and the right shape, just solid and
undersized, and every gate in the toolchain passes it.

The two forms that hollow are:

```python
import cadprint
sealed = cadprint.hollow(part, cadprint.shell_wall(0.4))          # 3904.0
opened = cadprint.open_shell(part, wall, part.faces().sort_by(Axis.Z)[-1])
```

`hollow` is `part - offset(part, -wall)`. `open_shell` is `offset` with its
`openings` argument, which is the one path where a bare `offset` shells rather
than shrinks. Both refuse rather than return something plausible when the wall
is too thick for the part: a bare `offset` on a 3 mm slab at 2 mm raises
`ValueError: Null TopoDS_Shape object`, which reads like a corrupt model.

A sealed void exports as a mesh with **two shells**, an outer and an inner.
`check_mesh` reports that, and it is correct rather than a defect.

## Derive the wall from the nozzle

```python
import cadprint
MIN_WALL = cadprint.min_wall(NOZZLE)        # 2 lines: the thinnest printable wall
SHELL    = cadprint.shell_wall(NOZZLE)      # 3 lines: a wall that also carries load
```

Below two extruded lines a slicer either drops the wall or prints two perimeters
with a gap between them, and neither shows up in any B-rep check — the STEP is
perfect and the print has a hole. A wall typed as `0.8` is the same defect
`cadfits` exists to prevent on the mating side: a number that stops being true
when the nozzle changes, with nothing to catch it. Shell at more than the
minimum, so there is a perimeter left for a fillet, a boss or a countersink.

### A repeated feature's count is a wall

The same rule reaches one step further than the wall you drew, to the material
left *between* two copies of a feature you drew nowhere. A knurl, a flute, a
vent slot, a cooling fin, a tick ring: the count is nearly always typed for
looks, and it silently sets a wall.

    web = 2 R sin(pi / n) - 2 r        # n circular flutes of radius r on a rim R

24 flutes of R2.5 on a R22 crank rim leave **0.744 mm** on a 0.800 mm minimum
wall. `validate`, `interfere`, `check_fit`, `check_mesh` and `check_overhang` all
pass it; `check_thickness` finds it after a full export and voxelisation, which
is the most expensive place in the toolchain to learn it. So solve the count
from the web rather than checking the web after choosing the count:

```python
FLUTE_WEB = 2.0 * MIN_WALL      # twice the limit: the gate reads low by a step
FLUTE_COUNT = int(math.pi / math.asin((FLUTE_WEB + 2.0 * FLUTE_R) / (2.0 * DISC_R)))
```

At 20 the same rim leaves 1.883 mm. Note the direction: the count is the
*output*. Written the other way round — count typed, web asserted — the check
restates the arithmetic and cannot fail, which is the same trap
`references/parameters.md` describes for hand-sized mates.

The pathological case is a pitch exactly equal to the feature size, where the
web goes to zero and neighbouring pockets touch at a point. That one is a
**non-manifold edge** rather than a thin wall, and `check_mesh` catches it where
`check_thickness` does not.

## Hollowing is worth less than the volume it removes

The volume that leaves the model is not the filament that stops being extruded.
The slicer was only going to put its infill fraction into that space anyway:

| | measured on the lofted body below |
|---|---|
| solid | 16.18 cm3 |
| shelled at 1.2 mm | 3.72 cm3 |
| **removed from the model** | **12.46 cm3 (77 %)** |
| filament actually saved at 15 % infill | **1.87 cm3, 2.3 g** |

`cadprint.savings()` returns both, and `check_thickness` prints both, because
reporting the first as if it were the second overstates the result by about six
times. Hollowing also adds material back — the inner surface gets its own top
and bottom skins — so treat the second number as an upper bound too.

What hollowing is actually for: weight, cooling and warp on a thick section, and
resin volume. For FDM bulk material alone, lowering infill in the slicer gets
most of the same saving with none of the modelling risk.

## When not to hollow

- **A part under load.** The shell carries it alone once the infill is gone.
- **A part with a sealed void, printed in resin.** Uncured liquid has nowhere to
  go. `open_shell`, or a drilled drain, is the fix; `check_thickness` reports how
  many separate pockets a hollow would create, and each needs its own drain.
- **A section already near the minimum wall.** Measure before choosing a wall;
  `hollow` refuses when the part is thinner than twice it, but a section at
  2.5 x wall passes and leaves a wall with no margin.
- **A thin feature the gate has already failed.** Fix that first — hollowing a
  part that has a 0.5 mm fin does not make the fin printable.

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
  expect a couple of percent either way (12.25 cm3 against a B-rep 12.46 on the
  body above). Take the volume as an estimate and the B-rep result from
  `cadprint.savings()` as the number.

Ray thickness is also bimodal by nature on a shell: a sample near an edge marches
along the wall rather than across it and legitimately reads the full span. The
median is the number to use; `max` is not a defect.

## Knife edges are walls too

A boolean can leave a mathematically valid solid whose material tapers to zero:
a round port meeting a circular chamber almost tangentially, a triangular brace
ending at one point, or a constant-width radial slot breaking through a curved
rim. `validate` and `check_mesh` pass all three; `check_thickness` correctly
finds the sub-nozzle wedge near the intersection.

Repair the construction, not the STL and not the threshold:

- replace a point contact on a brace with a finite seating edge;
- give a port a planar or otherwise non-tangent throat into the chamber;
- flare a slot mouth continuously from the guide width, then fillet the two
  outer breakthrough edges;
- fillet exposed inner and outer rim edges when the print orientation turns
  them into unsupported knife edges.

A stepped mouth merely moves the defect from the outer rim to the step. Keep
the guide region at its derived `cadfits` width, start the flare with that same
width, and widen only toward the opening. Rerun `check_mesh` and
`check_thickness` on the freshly exported part after every such repair.

## Record it

Do not call a part optimised from a volume in a chat log. `--report` writes a
markdown record next to the other verification artifacts, and a project that
ships a hollowed part should say the wall it was shelled at, beside the
`check_thickness` result that measured it.

## Which way is up — `check_overhang`

Every other gate in this toolchain is blind to the build direction. `check_fit`
puts the part on the bed, `check_mesh` closes the shell, `check_thickness`
extrudes the walls — and a part whose every feature hangs in mid-air passes all
three, because none of them knows which way is up. A model can be sound,
watertight, thick enough and impossible to print unsupported.

```bash
python "$CAD_SKILL_ROOT/scripts/check_overhang" part_x.stl --angle 45
```

It measures the down-facing surface in the pose the STL is in, drops what rests
on the bed and what sits within a layer of material below it, clusters the rest,
and splits each region two ways:

- **bridge** — short enough to span, with material on both sides of it at its
  own level. A bore ceiling, a slot roof. Reported, not a failure.
- **overhang** — neither. It **fails**: the slicer droops it or asks for
  support material.

Area cannot tell those apart, which is why the split matters: a horizontal bore
and a shelf of the same area and the same slope have completely different
answers. The span it reports is the **shorter** plan dimension, because that is
the one the slicer has to cross — a 10 x 40 mm roof is bridged across the 10.

### The fixes, in the order worth trying

- **Reorient the part.** A `part_*.step.py` entry owns its print pose; a link
  that is a plate in the assembly becomes a plate on the bed, and its bores turn
  vertical. Most overhangs are a pose problem, not a shape problem.
- **Teardrop a horizontal bore.** A round hole through a vertical wall has a
  ceiling the slicer must bridge, and above a few millimetres it sags into the
  bore. Replacing the top with two 45 deg faces meeting at an apex gives every
  layer material below it. The bore stays round where a shaft touches it.
- **Put material under the feature.** A pin whose base overhangs the disc it
  stands on has nothing to print onto; widen the disc, or add a boss under the
  pin. This one is invisible to every other gate and common in cranks and webs.
- **Taper it.** A cone under a collar, a 45 deg buttress under a shelf.

**Do not design at the limit.** A cone that flares one millimetre out per
millimetre up is a 45 deg overhang -- exactly the threshold -- and the flat
facets a tessellator lays on it land at 44.7 deg, on the wrong side. The same
goes for a 45 deg buttress or a chamfer sized to the limit. Give the angle
somewhere to go: 1.3 mm of rise per mm of flare is 52 deg and passes at any
tessellation tolerance.

What it cannot tell you: what your slicer's support settings are, whether the
material bridges well, or whether a 46 deg face will actually droop on your
machine. It answers the geometric question only.

## A wall is thin. An edge tapers. They are not the same finding

Thickness alone cannot tell a 0.5 mm panel from the rim where a hole breaks out
of a round post: both read under the minimum wall. The second one is not a
defect and cannot be designed away — any hole crossing a curved surface, any
countersink, any two faces meeting at an angle leaves material that tapers to
nothing at the boundary. A gate that fails on it fails on geometry, and the only
way to "fix" it is to delete the feature.

What separates them is how wide the sub-minimum band is across the surface,
which `check_thickness` reports per region as `band`:

- **wall** — the band is wider than one minimum wall. Real material is missing;
  fix it in the generator.
- **taper** — the band is narrower than that, so what the slicer drops at the
  edge is less than a single wall's width of material. Reported, counted against
  a 2 % surface budget, and not a failure.

A straight knife edge is always a wall: its band is `2 x min_wall / sin(2a)` for
an apex angle `2a`, which is never narrower than two minimum walls however sharp
or short the edge is. So the taper class does not excuse a knife edge, an
under-thick rib or a shrunken shell — only boundaries where a feature runs out
into a curved face. `--strict-thin` promotes tapers to failures when even those
matter.

## Every thin region, not just the thinnest point

`check_thickness` reports the sub-minimum samples **clustered into regions**,
worst first, because reporting only `thickness.min()` makes a part with several
knife edges take one round per edge -- fix the worst, re-run, meet the next, and
each round costs a rebuild, an export and a fresh voxelisation.

On a six-part pump that pattern turned an 8 s measurement into most of an hour,
and it hid the actual defect. The single reported point sat on a bore/front-face
corner at the grid floor; clustering the same run showed **33 regions**, and the
six largest were all on the hose-barb ridge crests reading 0.51 mm:

    1. 0.51 mm at (-46.5, 12.5, 26.9)   16 samples, 1.4 mm2, runs 9.2 mm
    2. 0.51 mm at ( 49.7, 13.8, 15.9)   15 samples, 1.3 mm2, runs 6.9 mm
    ... and 27 smaller region(s)

The cause was a repair for an earlier finding: a 0.5 mm flat land had been put
on each crest to remove a knife edge, and **the land was itself below the
minimum wall**. Widening it to 0.9 mm took the part from 158 sub-minimum samples
in 33 regions to 4 in 2.

Two rules follow:

- **A feature added to remove a knife edge must clear the minimum wall in its
  own right.** A land, a chamfer face or a fillet flat narrower than 2 x nozzle
  trades one finding for another, and the trade is invisible while the gate
  reports one point.
- **Read the region list before editing.** Samples within `4 x pitch` are one
  region, so a wedge running along an edge stays one finding; a count in the
  dozens means many separate places, not one bad face.
