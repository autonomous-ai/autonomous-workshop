# Per-part STEP hashes, this run against the published set

`make/ATTEMPTS.json` in the source archive records one accepted Make
attempt, round 1, subject
`0b1f5ba62960467b939afee5d60250b2768ea165fdce72443bd14212fd562713`.
That subject is `make/made.json`'s `made_sha256`, and that file's
`product_manifest` carries the sha256 of every file of the accepted tree.
Those are the published hashes below.

Both runs write `cad/part_*.step` through `cadgen`, which stamps a fixed
`1970-01-01T00:00:00` header, so identical geometry gives identical bytes.

## The 24 printed geometries

| printed part | published sha256 | this run | |
|---|---|---|---|
| `part_belt_cell.step` | `712b091c10f15660` | `712b091c10f15660` | identical |
| `part_corona_cell.step` | `484a16ba92e26ad4` | `484a16ba92e26ad4` | identical |
| `part_den_plug.step` | `9deef093613da52a` | `9deef093613da52a` | identical |
| `part_orbit_tray.step` | `551a58339e6cf395` | `551a58339e6cf395` | identical |
| `part_panel_northeast.step` | `ac7020703c5a4a6b` | `6e271632bc346752` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_northwest.step` | `4fa18b74a91c1d73` | `a9a369260291a15f` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_southeast.step` | `5f5a70165ef551dd` | `2ff52ee45be65ceb` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_southwest.step` | `82c9c898cfa3a2a2` | `e17f8bca4f8a1be8` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
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
| `part_world_saturn_anti.step` | `fc1fffad990e33d1` | `fc1fffad990e33d1` | identical |
| `part_world_saturn_sol.step` | `edee4ad4f1341581` | `edee4ad4f1341581` | identical |
| `part_world_uranus_anti.step` | `d993913622975638` | `d993913622975638` | identical |
| `part_world_uranus_sol.step` | `7eccfab310b21fef` | `7eccfab310b21fef` | identical |
| `part_world_venus_anti.step` | `a1cc7ace6f856f1e` | `a1cc7ace6f856f1e` | identical |
| `part_world_venus_sol.step` | `2727148ec7c30aa1` | `2727148ec7c30aa1` | identical |

## What changed

- **20 of the 24 printed geometries are byte-identical.**
- **4 files moved in bytes without moving in shape.** Each was
  diffed against the archive copy line by line in this run: every
  differing line is a `NEXT_ASSEMBLY_USAGE_OCCURRENCE`, the
  exporter's own per-session occurrence counter, which carries no
  geometry. The parts are `part_panel_northeast.step`, `part_panel_northwest.step`, `part_panel_southeast.step`, `part_panel_southwest.step`.
- **Nothing moved that was not asked to.** Every printed part
  outside `part_world_uranus_sol.step`, `part_world_uranus_anti.step` is the same geometry the published set carries, and the 4 listed above are the same shape written with a different occurrence counter.

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
it: `part_world_uranus_sol.step`, `part_world_uranus_anti.step` byte-identical to the published set's.**

That is the check rather than a formality, and on this run it
is the check the whole correction turns on. Both of Uranus's
polar hoods were taken off the globe and the ring was moved
from `cyan` to `white`. Removing a flush inlay REMOVES A
BOUNDARY: the globe stops being partitioned and gets its own
volume back, and no surface anywhere moves. Repainting the ring
moves one existing solid from one spool to another and moves no
surface either. If either of those had touched the ball or the
hoop -- a cut gone deeper than `RELIEF_DEPTH`, a ring rebuilt at
a different diameter, a seat re-cut -- these two hashes would
have moved with it. They did not. The printed solid the shop
receives is the same solid it was, and the whole revision is in
which spool prints which part of it.
`measure/uranus-bare.md` measures the same statement on the
solids directly: the globe's volume now is its published volume
plus both hoods, and the ring's volume and bounding box are
unchanged to nine decimal places.

## The production solids

`parts/*.step` cannot be compared in bytes: `production.py` writes them
through build123d's exporter, which stamps each file with the wall-clock
time of the run, so all 220 differ between any two runs whatever the
geometry does. They are compared occurrence by occurrence, on solid count,
exact volume and bounding box, in `measure/occurrence-geometry.md`.
