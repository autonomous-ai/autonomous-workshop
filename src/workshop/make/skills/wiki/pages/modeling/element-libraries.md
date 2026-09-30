---
title: Gear and standard-element libraries
tags: [gear, library, bd-warehouse, py-gearworks, cadquery, backlash, mesh-to, bevel]
aliases: [bd_warehouse, py_gearworks, SpurGear, mesh_to, cq_gears, cq-electronics, gear library]
sources:
  - skills/cad/references/standard-elements.md (gear-library and unreachable-library sections; before the move)
  - skills/cad/scripts/stdpart --self-check (asserts the backlash behaviour below)
  - "toolchain: build123d with cadquery-ocp 7.9; measured on an m1.5 12/23 pair"
related: [gears, operation-families]
updated: 2026-09-23
---

# Gear and standard-element libraries

How to use the libraries is `skills/cad/references/standard-elements.md`;
what makes a mesh run is [[gears]]. This page is the library behaviour behind
both.

## Two gear libraries, and which one

They overlap on exactly one shape and diverge everywhere else, and **both
export a class called `SpurGear`** — `stdpart sizes SpurGear` prints both rows
for that reason.

| you need | library | why |
|---|---|---|
| a lone straight spur gear | either | `bd_warehouse`'s is a plain build123d object that drops straight into a `BuildPart`; `py_gearworks`' needs `build_part()` |
| helical, herringbone, bevel, cycloid, internal ring, rack, planetary | `py_gearworks` | `bd_warehouse` has spur only |
| profile shift, undercut control, root/tip fillet, crowning | `py_gearworks` | not exposed by `bd_warehouse` |
| a meshed **pair** or a train | `py_gearworks` | `mesh_to` solves the centre distance *and* the tooth phase; keep one library across a train |

`py_gearworks` takes **angles in radians** (`pgw.DEG2RAD` converts) where
`bd_warehouse` takes degrees, and builds through `gear.build_part()` rather
than by constructing a build123d object directly. It hands back the datums the
rest of the model needs — `pitch_radius`, `r_base`, `dedendum_radius`,
`max_outside_radius`, and `center_location_top` / `_middle` / `_bottom` and
`face_location_*` as build123d `Location`s, so the bore is cut at a location
the gear owns rather than at a coordinate you retype. A `bd_warehouse` gear
reports `pitch_radius`, `base_radius` and `root_radius`, so a centre distance
is `g1.pitch_radius + g2.pitch_radius`.

Worm, hypoid and face gears are in neither library: `py_gearworks` lists them
as unsupported.

`bd_warehouse`'s `HeatSetNut` fails with `TypeError: Unable to create Shell,
invalid input type` (from `make_nut`) when it is constructed while a
`BuildPart` context is open — even with `mode=Mode.PRIVATE` — and builds
cleanly outside one. Construct the insert first, then open the builder and
pass it to `InsertHole`.

## Placing a pair with mesh_to

`mesh_to` solves the position, so do not also type it:

```python
import numpy as np
import py_gearworks as pgw          # never `from py_gearworks import *`

pinion = pgw.SpurGear(number_of_teeth=Z_PINION, module=MODULE, height=FACE,
                      backlash=TOOTH_BACKLASH)
wheel  = pgw.SpurGear(number_of_teeth=Z_WHEEL,  module=MODULE, height=FACE,
                      backlash=TOOTH_BACKLASH)
pinion.mesh_to(wheel, target_dir=pgw.UP)        # position AND tooth phase

centre = float(np.linalg.norm(np.asarray(pinion.center) - np.asarray(wheel.center)))
assert abs(centre - MODULE * (Z_PINION + Z_WHEEL) / 2) < 1e-6, f"centre {centre}"

part = pinion.build_part()
part -= pinion.center_location_top * Hole(radius=BORE_R, depth=FACE)
```

## The two backlash arguments

They do opposite things. The constructor's thins the tooth; `mesh_to`'s moves
the centres — and only the first is allowed, because pushing the centres apart
shortens contact ([[gears#printed-tooth-choices]]). Measured on an m1.5 12/23
pair (nominal centre distance 26.25 mm), with the overlap read by
`inspect interfere`:

| constructor `backlash` | `mesh_to(backlash=)` | centre distance | flanks |
|---|---|---|---|
| `0.2` | **omitted** | **26.2500 (nominal)** | **clear** |
| `0` | omitted | 26.2500 (nominal) | touching |
| `0` | `0.2` | 26.6651 (+0.42) | clear, centres wrong |
| `0.2` | `0.0` | 25.1726 (**−1.08**) | **8.17 mm³ of clash** |

The last row is the trap: `backlash=0.0` is not the same as leaving the
argument out. It tells `mesh_to` to close the centres onto teeth that were
already thinned, and the pair it returns fails `interfere` while looking
correctly specified in source. **Thin the teeth in the constructor and omit
`mesh_to`'s `backlash`.** `stdpart --self-check` asserts this behaviour and
fails if an upgrade changes it.

## Build cost and print gates by gear type

Gear geometry is cheap; the bevel is the one that is not, and the one that
does not print flat:

| | build | print gates at 0.4 mm nozzle |
|---|---|---|
| spur m1.5 z12, bored | 0.27 s | mesh, overhang, thickness all pass |
| helical 20°, herringbone | 0.43 / 0.55 s | all pass — its thin samples are tapers at feature edges, inside the gate's budget |
| bevel, 45° cone | 2.33 s | **fails overhang** (one 198 mm² region needs support) **and thickness** (a 0.13 mm wall) printed axis-up |

Every type builds as **one valid solid**, so a gear needs neither fusing nor
labelling the way a bearing or a modelled thread does.

## Never star-import py_gearworks

`from py_gearworks import *` exports names that collide with build123d's, and
the worst is silent: build123d's `IN` is `25.4` (the inch), `py_gearworks`'s
`IN` is the direction vector `[0, 0, -1]`, so a star-import turns `2 * IN`
from a length into a vector. `Curve` and `copy` collide too.
`import py_gearworks as pgw` and the collision cannot happen.

## CadQuery libraries that do not apply

The CadQuery ecosystem has close equivalents, and none of them is reachable
from a build123d toolchain pinned to `cadquery-ocp` 7.9:

| library | why not |
|---|---|
| `cq-electronics` (PCBs, headers, Raspberry Pi boards) | pins `cadquery-ocp==7.7.2`; installing it would downgrade the kernel build123d runs on. Use `$step-parts` for boards and connectors. |
| `cq_gears`, `cq-kit`, `cadquery-plugins` | not published on PyPI, and CadQuery-only. `py_gearworks` covers the gear types `cq_gears` has except worm. |
| `cadquery` itself | installs cleanly beside build123d, but drags in ~26 packages (numba, llvmlite, casadi, trame) for a kernel no generator here uses. |

If a CadQuery-only library is genuinely the only source for a part, that is a
recorded miss plus a `$step-parts` search, not a second kernel.
