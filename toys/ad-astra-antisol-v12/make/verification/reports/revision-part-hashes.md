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
| `part_belt_cell.step` | `712b091c10f15660` | `712b091c10f15660` | identical |
| `part_corona_cell.step` | `484a16ba92e26ad4` | `4aa6f49b240ffa62` | **changed** |
| `part_den_plug.step` | `9deef093613da52a` | `9deef093613da52a` | identical |
| `part_orbit_tray.step` | `551a58339e6cf395` | `551a58339e6cf395` | identical |
| `part_panel_northeast.step` | `6e271632bc346752` | `6e271632bc346752` | identical |
| `part_panel_northwest.step` | `a9a369260291a15f` | `a9a369260291a15f` | identical |
| `part_panel_southeast.step` | `2ff52ee45be65ceb` | `2ff52ee45be65ceb` | identical |
| `part_panel_southwest.step` | `e17f8bca4f8a1be8` | `e17f8bca4f8a1be8` | identical |
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

- **23 of the 24 printed geometries are byte-identical.**
- **Nothing moved that was not asked to.** Every printed part
  outside `part_world_mercury_anti.step`, `part_world_venus_anti.step`, `part_corona_cell.step` is the same geometry the published set carries.

## The three statements, and which the hashes support

A marking in this set is a flush colour inlay: it partitions the globe's
volume without moving the printed solid's own boundary. So a correction
that only changes a marking lands entirely in `parts/*.step`, which
`measure/occurrence-geometry.md` measures, and leaves `cad/part_*.step`
byte-identical. A correction that adds or removes material does the
opposite, and byte-identical would mean it did not happen. This run
carries one of each, on disjoint parts, and a third statement about the
21 parts it was asked not to touch at all.

**On that count, and it is worth stating rather than rounding.** The
brief for this revision says "the other 22 printed geometries". This
set has 24 distinct printed geometries, and this revision names three
of them, so the number outside the correction is **21**, not 22. The
brief's figure is one out; nothing else about the statement changes,
and every one of the 21 is checked below.

### 1. The two mirrored worlds must be BYTE-IDENTICAL

`part_world_mercury_anti.step`, `part_world_venus_anti.step`. Mirroring the map on an Anti-Sol globe reflects every marking's
longitude about that piece's own facing meridian. That changes which
spool prints which piece of the ball and moves no face anywhere: the
globe is the same sphere, the seat is the same cone, the disc and the
numeral are untouched, and each inlay still bottoms out at exactly
`RELIEF_DEPTH` below the surface. If either hash had moved, something
cut deeper than a marking is allowed to, and nothing else in this run
would be worth reading.

**They did not move.** `part_world_mercury_anti.step`, `part_world_venus_anti.step` are byte-identical to the published
set's, which is the answer this correction has to give.
`measure/occurrence-geometry.md` is where the change does show:
the per-colour bodies underneath the surface are in different
places, and `measure/pair-separation.md` measures how far.

### 2. The trap tile must CHANGE

`part_corona_cell.step`. The corona cell loses two raised tongues, which is material
removed from the printed solid. Byte-identical here would mean the
tongues are still on the tile.

**It changed.** `part_corona_cell.step` carries new bytes, and what is gone from them
is two tapered flames and the 7.00 mm of height they stood in.
`measure/corona-flat.md` measures the tile before and after.

### 3. The other 21 must be byte-identical or bookkeeping-only

That is every printed geometry outside the three this run was asked
to correct -- both Sol pieces of Mercury and Venus among them, and
the den plug, whose two flames this run exists to leave alone.

**None of them moved in shape.** 21 are byte-identical; 0 differ
only in `NEXT_ASSEMBLY_USAGE_OCCURRENCE`, diffed line by line in
this run rather than carried forward as a claim.

## The production solids

`parts/*.step` cannot be compared in bytes: `production.py` writes them
through build123d's exporter, which stamps each file with the wall-clock
time of the run, so all 220 differ between any two runs whatever the
geometry does. They are compared occurrence by occurrence, on solid count,
exact volume and bounding box, in `measure/occurrence-geometry.md`.
