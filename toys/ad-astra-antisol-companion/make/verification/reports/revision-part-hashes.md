# Per-part STEP hashes, this run against the published set

`make/ATTEMPTS.json` in the source archive records one accepted Make
attempt, round 1, subject
`98ab48ca581f6416a288621266bafe90f4080864c0b36efd0dd097b749ff310e`.
That subject is `make/made.json`'s `made_sha256`, and that file's
`product_manifest` carries the sha256 of every file of the accepted tree.
Those are the published hashes below.

Both runs write `cad/part_*.step` through `cadgen`, which stamps a fixed
`1970-01-01T00:00:00` header, so identical geometry gives identical bytes.

## The 24 printed geometries

| printed part | published sha256 | this run | |
|---|---|---|---|
| `part_belt_cell.step` | `712b091c10f15660` | `ab46409a4c7ffd13` | **changed** |
| `part_corona_cell.step` | `484a16ba92e26ad4` | `b024dd7566cb5b20` | **changed** |
| `part_den_plug.step` | `9deef093613da52a` | `8aaabc3540b958f9` | **changed** |
| `part_orbit_tray.step` | `551a58339e6cf395` | `551a58339e6cf395` | identical |
| `part_panel_northeast.step` | `6e271632bc346752` | `92dccd0aa8d28dfd` | **changed** |
| `part_panel_northwest.step` | `a9a369260291a15f` | `d2b22a3f712aec31` | **changed** |
| `part_panel_southeast.step` | `2ff52ee45be65ceb` | `d8e86ed6d4d1fa4c` | **changed** |
| `part_panel_southwest.step` | `e17f8bca4f8a1be8` | `e1dd29a28e482545` | **changed** |
| `part_world_earth_anti.step` | `c8ff2f83e08155fa` | `c8ff2f83e08155fa` | identical |
| `part_world_earth_sol.step` | `c000a046626ff440` | `c000a046626ff440` | identical |
| `part_world_jupiter_anti.step` | `b84c4eade585d0e5` | `b84c4eade585d0e5` | identical |
| `part_world_jupiter_sol.step` | `75b09a7a2e32cf4c` | `75b09a7a2e32cf4c` | identical |
| `part_world_mars_anti.step` | `701aa22c961623ee` | `701aa22c961623ee` | identical |
| `part_world_mars_sol.step` | `1ae25fa65cc6e3d2` | `1ae25fa65cc6e3d2` | identical |
| `part_world_mercury_anti.step` | `5dc8f8b3af871208` | `5dc8f8b3af871208` | identical |
| `part_world_mercury_sol.step` | `b360242a03b93ea0` | `b360242a03b93ea0` | identical |
| `part_world_neptune_anti.step` | `c8b6c1213f10c762` | `c8b6c1213f10c762` | identical |
| `part_world_neptune_sol.step` | `38970c1ac956ff0d` | `38970c1ac956ff0d` | identical |
| `part_world_saturn_anti.step` | `fc1fffad990e33d1` | `722450d7bc7a4b79` | **changed** |
| `part_world_saturn_sol.step` | `edee4ad4f1341581` | `5b2b9a0462ccb5fb` | **changed** |
| `part_world_uranus_anti.step` | `d993913622975638` | `cbd76401b3ff19a9` | **changed** |
| `part_world_uranus_sol.step` | `7eccfab310b21fef` | `b47c381ba8116a4b` | **changed** |
| `part_world_venus_anti.step` | `a1cc7ace6f856f1e` | `a1cc7ace6f856f1e` | identical |
| `part_world_venus_sol.step` | `2727148ec7c30aa1` | `2727148ec7c30aa1` | identical |

## What changed

- **13 of the 24 printed geometries are byte-identical.**
- **Unaccounted for: `part_belt_cell.step`, `part_corona_cell.step`, `part_den_plug.step`, `part_panel_northeast.step`, `part_panel_northwest.step`, `part_panel_southeast.step`, `part_panel_southwest.step`, `part_world_saturn_anti.step`, `part_world_saturn_sol.step`, `part_world_uranus_anti.step`, `part_world_uranus_sol.step`**

## The two statements, and which one the hashes support

A marking in this set is a flush colour inlay: it partitions the globe's
volume without moving the printed solid's own boundary, so a correction
that only changes a marking lands entirely in `parts/*.step`, which
`measure/occurrence-geometry.md` measures, and leaves `cad/part_*.step`
byte-identical. That is the FIRST statement, and it is what every run in
this chain except the Uranus one has expected of its own corrected parts.

The SECOND statement is the Uranus run's: a ring is added material, so
its two parts had to change in bytes and byte-identical would have meant
the ring did not get built.

**This run expects the first statement, and the hashes support
it: `part_world_neptune_sol.step`, `part_world_neptune_anti.step` byte-identical to the published set's.**

That is the check rather than a formality, and on this run it
is the check the whole correction turns on. This revision adds
ONE new marking to Neptune -- the dark spot's bright companion
cloud -- and takes a scallop out of the dark spot to make room
for it. Both of those are colour boundaries inside the globe's
own volume: `parts/world.build_world` fuses the disc, the globe
and the ring and never a marking, so adding a marking cannot
move the printed solid's own surface. If it had -- a cut gone
deeper than `RELIEF_DEPTH`, a seat re-cut, a globe rebuilt at a
different diameter -- these two hashes would have moved with it.
They did not. The printed solid the shop receives is the same
solid it was, and the whole revision is in which spool prints
which part of it.
`measure/occurrence-geometry.md` measures the other half on the
colour solids directly: which occurrences appeared, which
changed volume, and that nothing outside Neptune did either.

## The byte-different parts, measured

Eleven printed parts outside the correction came back with
different bytes, and a hash comparison cannot say whether that
is a changed solid or a differently written one. So they are
measured. Each STEP is imported from both trees and compared on
exact volume and on bounding box.

| part | published mm3 | this run mm3 | difference mm3 | bounding box |
|---|---:|---:|---:|---|
| `part_belt_cell.step` | 5731.126559 | 5731.126559 | 1.82e-12 | identical to 1e-9 mm |
| `part_corona_cell.step` | 3414.677717 | 3414.677717 | 3.64e-12 | identical to 1e-9 mm |
| `part_den_plug.step` | 9855.773817 | 9855.773817 | 3.64e-12 | identical to 1e-9 mm |
| `part_panel_northeast.step` | 206087.597110 | 206087.597110 | 0.00e+00 | identical to 1e-9 mm |
| `part_panel_northwest.step` | 159870.624221 | 159870.624221 | 8.73e-11 | identical to 1e-9 mm |
| `part_panel_southeast.step` | 171439.104221 | 171439.104221 | 0.00e+00 | identical to 1e-9 mm |
| `part_panel_southwest.step` | 136776.691332 | 136776.691332 | 0.00e+00 | identical to 1e-9 mm |
| `part_world_saturn_anti.step` | 14215.322357 | 14215.322357 | 1.13e-08 | identical to 1e-9 mm |
| `part_world_saturn_sol.step` | 14211.332363 | 14211.332363 | 1.59e-09 | identical to 1e-9 mm |
| `part_world_uranus_anti.step` | 9998.528214 | 9998.528214 | 7.40e-10 | identical to 1e-9 mm |
| `part_world_uranus_sol.step` | 9994.455542 | 9994.455542 | 7.66e-10 | identical to 1e-9 mm |

**Every one of them is the same solid.** The largest volume
difference anywhere in the table is 1.13e-08 mm3, which is
boolean round-off rather than geometry, and every bounding
box agrees to a nanometre. What moved is the serialisation:
this project's generator does not write identical STEP bytes
for these parts between a warm multi-target generation and a
single-target one -- six of the eleven come out with a
different entity count for the same shape. It is a property
of the writer, not of the design, and none of it is in
`measure/source-diff.md`, which is the whole difference
between the two source trees and holds five files, none of
them these parts' generators.

## The production solids

`parts/*.step` cannot be compared in bytes: `production.py` writes them
through build123d's exporter, which stamps each file with the wall-clock
time of the run, so all 222 differ between any two runs whatever the
geometry does. They are compared occurrence by occurrence, on solid count,
exact volume and bounding box, in `measure/occurrence-geometry.md`.
