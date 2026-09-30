# `render_set` cache check against the Antisol Companion (issue #63)

The acceptance check for issue #63: run the reference whole-set render script
(`src/workshop/make/skills/cad/scripts/render_set`) against the real
222-occurrence Antisol Companion assembly and confirm that repeated cameras on
one scene, and occurrences unmoved across board states, are cache hits through
`render_review`'s occurrence tessellation cache -- never a private routine.
Not part of CI; run by hand, following the same real-asset practice as
`docs/RENDER_PHASE_BENCHMARK.md` (issue #58).

Per the issue's "Update from #60", `part_belt_cell` gets a different B-rep
hash on every build until issue #74 lands, so its occurrences miss the cache
across processes. This run avoids that gap the way the issue allows: both
board states are built and rendered inside **one process**, one `render_set`
invocation, using the board-only assembly (`product_compound(position,
with_trays=False)`), so the check is not sensitive to belt_cell's known
cross-process instability.

## What ran

`write_scenes`/`render_scenes` (the two functions `render_set`'s CLI calls)
were driven directly, with a counting wrapper around `build123d.Shape.
tessellate` to see every real tessellation regardless of the disk cache, for
the `opening` and `endgame` positions from
`toys/ad-astra-antisol-companion/make/source/cad/positions.py`, two cameras
(`iso`, `front`) each, `tolerance=0.08`, default angular tolerance, one
process:

```
opening build                          269.3s
opening tessellate+render (2 cameras)  230.3s   tessellate calls: 220
endgame build                          268.9s
endgame tessellate+render (2 cameras)   81.6s   NEW tessellate calls: 84
```

## Reading it

- **Repeated cameras on one scene are a cache hit.** The opening scene has
  220 occurrences; two cameras produced exactly 220 tessellate calls, not
  440. `render_scenes` tessellates a scene once and rasterises it from every
  named camera, matching `tests/make/test_render_set.py::
  test_one_scene_rendered_from_two_cameras_tessellates_once`'s synthetic
  case on the real assembly.
- **Occurrences unmoved across board states are a cache hit.** The endgame
  position moves most worlds to new cells and removes four per side to the
  trays (`positions.py`'s `ENDGAME`), so it is not a small edit of the
  opening state -- yet only 84 of its occurrences needed a fresh tessellation
  in the same process, not another 220. The remainder (the four board
  panels, the corona and den geometry, and the worlds that end up on a cell
  they also occupied, or an equivalent location, in the opening layout) hit
  the persistent on-disk cache `render_review.tessellate_occurrences` reads
  and writes, the same cache the CLI's own `--view` loop uses, not a private
  routine.
- **Build, not tessellation, dominates real wall clock here** (269s vs 230s
  for the first state's two-camera render): consistent with
  `docs/RENDER_PHASE_BENCHMARK.md`'s reading that rebuilding the assembly
  from source is a comparable-or-larger cost to tessellating it, on this
  asset.
- Host: this sandbox, 64 usable cores, shared load (`load1` 6.9-8.7 during
  the run). Wall clock for both states plus their renders: about 15 minutes.

## Follow-up

A full `docs/RENDER_PHASE_BENCHMARK.md`-style run with trays, all three
positions, and multiple cameras per state would give a rounder headline
number, but was not repeated here given that benchmark's own recorded
71-minute wall clock; this run isolates the two properties issue #63 asks
for with real geometry and one order of magnitude less time. `bench_
render_phases.py` remains the tool for a fuller timing pass once issue #64
seals the B-rep identity and issue #74 stabilizes `part_belt_cell`, removing
the reason to avoid a cross-process, tray-inclusive run.
