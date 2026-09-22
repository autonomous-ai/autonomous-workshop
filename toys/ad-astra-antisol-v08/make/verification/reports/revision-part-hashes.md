# Per-part STEP hashes, this run against the published set

`make/ATTEMPTS.json` in the source archive records one accepted Make
attempt, round 1, subject
`e8aa458535ebfe91de3933a0287d4e5fafd4ca1dce31d65a07443eb0349f9f23`.
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
| `part_panel_northeast.step` | `6e271632bc346752` | `6b72fb6b87c4d2f2` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_northwest.step` | `a9a369260291a15f` | `af46270fd67bb4b0` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_southeast.step` | `2ff52ee45be65ceb` | `00e504d06c80d87c` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
| `part_panel_southwest.step` | `e17f8bca4f8a1be8` | `02586c970402827d` | 1 line differs, NEXT_ASSEMBLY_USAGE_OCCURRENCE: an exporter occurrence counter, no geometry. Every other line matches the archive copy, checked here rather than asserted |
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
| `part_world_uranus_anti.step` | `8541bfb66d4960d1` | `8541bfb66d4960d1` | identical |
| `part_world_uranus_sol.step` | `495ebfbadf5cfd3a` | `495ebfbadf5cfd3a` | identical |
| `part_world_venus_anti.step` | `a1cc7ace6f856f1e` | `a1cc7ace6f856f1e` | identical |
| `part_world_venus_sol.step` | `2727148ec7c30aa1` | `2727148ec7c30aa1` | identical |

## What changed

- **20 of the 24 printed geometries are byte-identical.**
- **4 files moved in bytes without moving in shape.** Each was
  diffed against the archive copy line by line in this run: every
  differing line is a `NEXT_ASSEMBLY_USAGE_OCCURRENCE`, the
  exporter's own per-session occurrence counter, which carries no
  geometry. The parts are `part_panel_northeast.step`, `part_panel_northwest.step`, `part_panel_southeast.step`, `part_panel_southwest.step`.
- **`part_world_neptune_sol.step`, `part_world_neptune_anti.step` are byte-identical too.**
  That is the right answer rather than a surprise: a marking in this set
  is a flush colour inlay, so it partitions the globe's volume without
  moving the printed solid's own boundary. The parts this revision
  corrects are corrected entirely in where the colour split falls, which
  is what `parts/*.step` carries and what
  `measure/occurrence-geometry.md` measures.
- **No printed geometry changed shape.** Exactly 2 printed parts
  corrected -- `part_world_neptune_sol`, `part_world_neptune_anti` -- and the correction is a colour boundary, not a
  solid.

## The production solids

`parts/*.step` cannot be compared in bytes: `production.py` writes them
through build123d's exporter, which stamps each file with the wall-clock
time of the run, so all 232 differ between any two runs whatever the
geometry does. They are compared occurrence by occurrence, on solid count,
exact volume and bounding box, in `measure/occurrence-geometry.md`.
