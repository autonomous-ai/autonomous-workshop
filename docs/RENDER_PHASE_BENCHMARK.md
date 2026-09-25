# Render phase benchmark (issue #58)

The first measurement of the occurrence tessellation cache
(`d853a382`, `render_review.tessellate_occurrences`) that landed after the
[Baseline Correction Run](BASELINE_CORRECTION_RUN.md). Run by hand with
`tools/bench_render_phases.py` against the real 222-occurrence Antisol
Companion assembly (`toys/ad-astra-antisol-companion`), never a synthetic
mesh: the earlier 50 µs-per-triangle figure came from a synthetic mesh and
had to be walked back as "the size of the prize, not a promise"
(`BASELINE_CORRECTION_RUN.md`). Not part of CI; asserts no timing.

```
"$WORKSHOP_PYTHON" tools/bench_render_phases.py
```

## First output, on current code

- Code: branch `sandcastle/issue-58` at `771e8cf6`.
- Host: 64 cores (64 usable), shared with other workloads
  (`load1=9.40 load5=8.44 load15=8.22`) — like the baseline host, timings
  below carry that noise.
- Entry: `toys/ad-astra-antisol-companion/make/source/cad/antisol.step.py`,
  `tolerance=0.08`, `angular_tolerance=None`, `size=900`.

```
=== phase by phase: single view, tessellation cache cold vs. warm ===
  cold: build=267.53s tessellate=408.52s rasterise=1.24s total=677.30s (occurrences=222 triangles=943007)
  warm: build=265.08s tessellate=395.75s rasterise=1.43s total=662.26s (occurrences=222 triangles=943027)

=== multi-camera: one scene, several cameras, cache warm ===
  build=266.10s tessellate=391.55s (once)
  rasterise[iso]=1.28s
  rasterise[front]=1.14s
  rasterise[top]=1.26s
  rasterise[rear_iso]=1.25s
  rasterise total (4 cameras)=4.94s

=== multi-state: several board states, cache warm across states ===
  opening: build=265.59s tessellate=407.01s (occurrences=222 triangles=943007)
  midgame: build=265.06s tessellate=412.31s (occurrences=222 triangles=943027)
  endgame: build=265.54s tessellate=415.20s (occurrences=222 triangles=943025)
```

Wall clock for the whole run: 71 minutes.

## Reading it

- **Rasterisation is still nearly free.** 1.1–1.4 s per view, 4.94 s for four
  cameras once a scene is tessellated — consistent with the baseline's "3.9 s
  for 3 views" figure and the batched rasteriser doing its job.
- **The occurrence tessellation cache did not make the warm pass
  meaningfully faster here.** 395.75 s warm vs. 408.52 s cold is within this
  host's noise band (compare the ±3 s spread across the three, unrelated
  multi-state builds), not a cache win. `du -sh` on the cache directory this
  run wrote shows **131 MB across 617 entries** for one 222-occurrence,
  943k-triangle assembly. Two concrete costs explain the flat result:
  - `Measurements.run` (`cadgen/inspection_runtime.py:164`) only reads a
    cache entry whose file is **≤1,000,000 bytes**; larger ones are always a
    silent miss, recomputed and rewritten every call. **18 of the 617 files
    this run wrote are over that cap** (up to 3.16 MB) — almost certainly the
    largest, most expensive-to-tessellate occurrences (the worlds and board
    panels), which is exactly where a hit would matter most.
  - For everything under the cap, reading and JSON-deserialising the
    triangle/point arrays back is itself comparable in cost to recomputing
    them from the B-rep, so even a real hit buys little.
  The cache is real (confirmed from the entry count and file layout under
  `tessellation-v1`), it is just not currently a speed win on this asset.
  Later tickets in this set
  (`docs/adr/0073-carry-forward-compares-geometry-not-step-bytes.md` and
  issue #61/#64) should read this before assuming the cache pays for itself,
  and a follow-up should raise or remove the 1 MB cap before trusting a warm
  pass on a large assembly.
- **Build is the more stable cost**: 265–267 s in every case, whether cold,
  warm, part of the multi-camera case, or any of the three board states —
  rebuilding the 222-occurrence assembly from source dominates neither more
  nor less than tessellation does.
- **Multi-state reuse did not show up either.** `opening`, `midgame` and
  `endgame` tessellate at 407–415 s each, not meaningfully faster than the
  single-view cold case, even though occurrences that do not move between
  states are expected to be tessellated once. Dou Shou Qi positions move
  most pieces between states (see `positions.py`), so few placements are
  actually shared; a state pair with more overlap would be a better probe of
  this path.
- **Triangle counts vary slightly run to run** (943,007 / 943,027 / 943,025)
  even for nominally the same `opening` position and tolerance — evidence of
  the same non-deterministic boolean round-off ADR 0073 already named for
  STEP export, now visible in tessellation counts too.
