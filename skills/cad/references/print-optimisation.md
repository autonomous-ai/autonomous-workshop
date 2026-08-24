# Print optimisation

What a part costs to print is a question no other check asks. `validate` says
the solid is sound, `interfere` that nothing clashes, `check_fit` that it sits
on the bed, `check_mesh` that the artifact is sound. A wall the nozzle cannot
lay down and a solid core no one will ever see both pass all four.

```bash
python skills/cad/scripts/check_thickness <part>.stl --nozzle 0.4
python skills/cad/scripts/check_thickness <part>.stl --report measure/thickness.md
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

## Record it

Do not call a part optimised from a volume in a chat log. `--report` writes a
markdown record next to the other verification artifacts, and a project that
ships a hollowed part should say the wall it was shelled at, beside the
`check_thickness` result that measured it.
