# Experiment: does turning off parallel booleans make round-off reproducible (issue #60)

A time-boxed experiment, reported rather than wired in, per ADR 0073's aside:
"one experiment runs: whether building with OCCT's parallel boolean mode off
... makes the round-off deterministic. Its result decides whether the six
round-off parts can ever be carried; this ADR does not depend on it." **No
production code changed** for this experiment; every measurement below comes
from a scratch environment and a patched copy of a third-party dependency
outside the repository.

## Result, stated plainly

**The round-off did not reproduce.** A controlled, same-host, same-code,
back-to-back comparison of single-target and warm multi-target builds of all
24 of Antisol Companion's printed geometries found **zero** volume or
STEP-entity-count differences, for every part, with OCCT's parallel boolean
mode both at its default (on) and forced off. That includes the eleven parts
`measure/revision-part-hashes.md` reported as byte-different and the six of
those with a different entity count. Since the phenomenon ADR 0073 asked
about never showed up under either setting, this experiment cannot say
parallel-off "fixes" it — there was nothing here for it to fix. It also found
a **different, unrelated non-determinism** in the exact mechanism ADR 0073
proposes as the Carry Forward key, and a live, more parsimonious explanation
for the archived report's difference than boolean scheduling. Both are below.

## Method

`cadgen==0.4.19` (this repository's `src/workshop/make/skills/cad/scripts/packages/cadgen`,
pip-equivalent, unpinned `build123d`/`cadquery-ocp`) would not import in a
fresh install: the newest `cadquery-ocp` (8.0.1.0.0) no longer exports
`OCP.TDF.TDF_LabelSequence`, which `cadgen`'s STEP-scene loader needs, and the
newest `cadquery-ocp` compatible with that symbol (7.9.3.1.1) is too old for
`build123d`'s (and `ocp_gordon`'s) use of `OCP.collections`, added later. That
version pair not existing on the day of this experiment is itself evidence
for the third finding below.

Rather than block the whole experiment on that mismatch, it drives the toy's
own `parts/*.py` and `bool3d.py` directly — the exact OCCT boolean code path
`bool3d.py`'s `+`, `.cut()` and `.intersect()` exercise via `build123d`'s
`Shape._bool_op` — bypassing only `cadgen`'s CLI wrapper (its GLB/topology
render-package generation, entity-numbering pass and STEP timestamp
normalization). Absolute byte-for-byte STEP comparison against the archived
report is therefore out of scope; volume, STEP entity count and bounding box
are not, and are what the archived report itself used to characterise the
eleven byte-different parts as "the same solid."

- Environment: `build123d==0.13.0`, `cadquery-ocp==8.0.1.0.0`, Python 3.11, a
  throwaway venv. No root in this sandbox, so no system `libGL`; a stub
  `libGL.so.1`/`libGLU.so.1` was compiled locally exporting only the ~119 GL
  symbols `build123d`'s `TKOpenGl` needs to *load* (headless STEP generation
  never calls a real GL context).
- Parallel mode: `build123d/topology/shape_core.py`'s three
  `operation.SetRunParallel(True)` sites (`_bool_op`, `_sectional_op`, and one
  free function), patched to `False` in the scratch venv's installed copy for
  the "off" runs and reverted for "on" — never touching this repository.
- Targets: all 24 `part_*.step.py` generators of
  `toys/ad-astra-antisol-companion/make/source/cad`, called via their
  `gen_step()` function (`build_belt_cell()`, `build_world("saturn", "anti")`,
  etc.), on an unmodified copy of the toy's source.
- **Single-target**: each part built in its own fresh interpreter process.
- **Warm multi-target**: all 24 parts built in one interpreter process, in
  file order — the same "warm" state a batched `scripts/gen part_*.step.py`
  invocation leaves behind.
- Measured per part: exact volume, STEP entity count (`#N=` records in the
  exported STEP), bounding box, and (for the side investigation below) a
  `cadgen.inspection_runtime.shape_identity`-equivalent B-rep binary hash
  (`OCP.BinTools.BinTools.Write_s` + sha256).
- Host: 64 cores, no other load during the runs.

## Finding 1 — no round-off in a controlled same-host A/B, on or off

| condition | parts with a volume or entity-count difference (single vs warm multi-target) |
|---|---:|
| parallel booleans **on** (default) | 0 of 24 |
| parallel booleans **off** | 0 of 24 |

Every one of the six previously flagged parts (`part_belt_cell`,
`part_corona_cell`, `part_den_plug`, `part_panel_northwest`,
`part_world_saturn_anti`, `part_world_saturn_sol` — the highest-magnitude
subset of the eleven byte-different parts) came back with bit-identical
volume and entity count between single-target and warm multi-target, in both
conditions.

## Finding 2 — a different non-determinism, unaffected by this switch

Repeating the *identical* single-target build of `part_belt_cell` back to
back (same process shape, same code, same environment) gave a **different**
B-rep binary hash every time, while volume (`0x1.663206626e53fp+12` exactly,
every run), STEP entity count (18544, every run) and bounding box stayed
bit-identical. Diffing two such binary streams: same length, ~1% of bytes
differ — a real content difference, not a header timestamp. **This persisted
with `SetRunParallel(False)`.**

This is not the round-off ADR 0073 or this issue asked about — it never
moves volume or entity count — but it is directly relevant to ADR 0073's
Carry Forward design, which proposes exactly this B-rep binary hash
(`BinTools.Write_s` + sha256) as the "unchanged" key. If that hash is not
stable across two builds of the identical script in the identical
environment, a follow-up should establish that before relying on it, and
this switch does not fix it.

## Finding 3 — the toolchain's own version pin is loose enough to explain the archived report

`cadgen`'s declared dependencies are unpinned (`"build123d"`,
`"cadquery-ocp"`, no version bound). Resolving them fresh, on the same
requirements, in this same session, `pip` picked incompatible major pairs
depending only on which `cadquery-ocp` release it landed on that hour: 8.0.1.0.0
(needed by current `build123d`) versus 7.9.3.1.1 (needed by `cadgen`'s STEP
scene loader) do not both work together at all. The archived Correction Run's
"published" STEP and the correction's own fresh STEP were built in two
separate sessions, potentially days apart, on this same unpinned dependency
set. A silently different `build123d`/`cadquery-ocp` patch version between
those two sessions is a simpler, and now demonstrably live, candidate
explanation for entity-count and sub-1e-8-mm3 volume differences than
thread-scheduling variance inside one boolean call — and it is not excluded
by anything in `measure/source-diff.md` or `revision-part-hashes.md`, which
compare source and STEP bytes, not the toolchain that turned one into the
other.

## Finding 4 — the build-time cost, as asked for

Same 24-part warm multi-target build, same host, immediately before/after:

| | wall | per-part build time (sum) |
|---|---:|---:|
| parallel **on** | 15.1 s | 12.4 s |
| parallel **off** | 38.8 s | 36.7 s |

**2.6× slower with parallel booleans off.** Single-target sums are close to
the multi-target build-time sum in both conditions (12.8 s vs 12.4 s on;
36.8 s vs 36.7 s off) — on this product, "warm" saves negligible build time
either way, so the 2.6× cost is not offset by anything warmth buys back.

## Conclusion

**Not carriable on this experiment's evidence, and not because parallel-off
failed a test it should have passed — because the round-off it was meant to
fix did not reproduce here at all**, on or off. Recommend:

1. **Do not wire parallel-booleans-off into Make.** It cost 2.6× the build
   time in this measurement for an effect this experiment could not
   reproduce.
2. **Before attributing a future entity-count or sub-1e-8-mm3 volume
   difference to warm-vs-cold `gen`, pin and compare the exact
   `build123d`/`cadquery-ocp` versions of the two builds being compared.**
   This experiment shows that pin drifting is real, current, and reproduces
   on its own without touching parallel mode at all.
3. **Treat the B-rep binary hash (Finding 2) as a separate open question from
   this issue**, worth its own measurement before ADR 0073's Carry Forward
   leans on it further: does it stabilise under a fixed OCCT thread count
   (`OMP_NUM_THREADS=1` / `OCCT` env equivalents) or a fixed random seed, or
   is the binary BREP format itself carrying non-geometric, per-run state
   (e.g., an internal container's iteration order)?
