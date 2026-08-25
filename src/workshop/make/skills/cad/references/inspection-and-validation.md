# Inspection and validation

Read this file for every generated STEP artifact and whenever the user asks for geometry facts, references, dimensions, mating, diffing, or frame inspection.

## Principle

Deterministic geometry checks decide pass/fail, and they are the only evidence this toolchain produces — there is no renderer, so a semantic error the checks do not encode goes unseen. Scale the deterministic checks to the user's spec: every dimension, clearance, or relationship the user specified — including dimensions taken from a technical drawing — must be verified with `measure`, `align`, or `frame`. The facts/planes/positioning baseline runs for every generated artifact regardless of spec.

During quick iteration, rerun the checks affected by the current edit. The full
sequence below is the final verification gate and runs after the source has
stabilized; it need not be repeated after an unrelated colour or documentation
change.

## Tool

The launcher lives in the CAD skill directory:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" {refs|diff|frame|measure|align|worker|batch} ...
```

Inspection targets resolve from the command cwd; prefer cwd-relative target paths. Absolute paths are accepted when they point under the command cwd (they are relativized); an absolute path outside the cwd fails with an explicit error — run the command from the workspace that owns the artifact. Common data-output flags: `--format json|text` (default is machine-readable), `--quiet`, `--verbose`.

## Batch several inspections; do not parallelize warm clients

`scripts/inspect batch` reads one JSON request per line and emits one response
per line. Use it for independent refs, validate, and targeted measurement calls
that would otherwise start several CLIs. It runs sequentially in one process,
paying the OCP import once and avoiding warm-daemon queue contention.

```bash
printf '%s\n' \
  '{"id":"refs","argv":["refs","<project-dir>/<name>.step.py","--facts","--planes","--positioning"]}' \
  '{"id":"validate","argv":["validate","<project-dir>/<name>.step.py"]}' \
  '{"id":"width","argv":["measure","<project-dir>/<name>.step.py","--from","#f12","--to","#f18","--axis","x"]}' \
  | CADGEN_WARM=1 python "$CAD_SKILL_ROOT/scripts/inspect" batch
```

Batch/worker consume stdin and intentionally bypass the daemon even when
`CADGEN_WARM=1`; the single batch process is already the warm process. Check
each response's `ok` and `exitCode` rather than relying only on the outer
process exit code.

Accepted target forms:

```text
path/to/entry
path/to/entry.step
path/to/entry.step.py
```

A `<name>.step.py` generator target resolves to the same entry as its logical `<name>.step`, and keeps resolving to the generator entry even when a same-stem exported `.step` file exists beside it.

Selector-backed queries (`refs --facts`, planes, measures) on generated assemblies extract whole-model topology on demand and cache it as `topology.glb` inside the entry's render package; repeat queries read the cache (seconds instead of a full re-extraction) until the package is rebuilt, which invalidates the sidecar.

Selector refs are local to the STEP/CAD entry target passed to the command:

```text
#o1.2
#o1.2.f1
#f1
```

Pass selector refs as `#...` tokens. The STEP/CAD file path or entry target is a separate CLI argument.

## Validation sequence

1. Generation completed and the STEP/STP file exists.
2. `refs --facts --planes --positioning` confirms scale, labels, major planes, and placement-ready references. Run this for every generated artifact.
3. `validate` confirms the geometry is sound: valid topology, closed shells, no self-intersection, and positive volume on every solid. Run this for every generated artifact.
4. `interfere` confirms no two parts occupy the same space. Run this for every assembly.
5. Spec-driven checks: `measure` for every user-specified dimension, offset, or clearance; `align` for interfaces that should be flush or centered; `frame` for orientation and occurrence-placement expectations; `diff` for modifications that could affect unrelated geometry.

Steps 3 and 4 are the completion gate. A `validate` finding on geometry that was
meant to be solid, or a clash from `interfere`, blocks the work from being called
done: repair the source and rerun the check that failed. Neither question can be
answered by reading the generator or by looking at a render.

### `refs --facts` "ok" is not a geometry claim

`refs --facts` reports counts, bounds, labels and references. Its `ok` field is
a command-success flag: it is true when every requested ref resolved, and it
says nothing about whether the geometry is sound. A five-face open box reports
`"ok": true` with `"faceCount": 5`, and a solid with inverted orientation —
which renders as a hole in the world — reports `"ok": true` as well.

Use `validate` for that question:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" validate <project-dir>/<name>.step.py
python "$CAD_SKILL_ROOT/scripts/inspect" validate <project-dir>/<name>.step.py --refs o1.2      # one subassembly
python "$CAD_SKILL_ROOT/scripts/inspect" validate <project-dir>/<name>.step.py --allow-open   # surfaces intended
```

It reports, per occurrence, any of `invalidTopology`, `openShell`,
`nonPositiveVolume`, `noSolid`, `selfIntersecting`, and exits non-zero when any
occurrence fails.

Two subtleties worth knowing. `BRepCheck_Analyzer` returns **true** for a
reversed solid, so topological validity alone cannot catch an inverted body —
only the sign of the volume can. And volume is measured per solid, never
aggregated: a `+1000` and a `-1000` inside one compound sum to zero, so any
check reading a compound's total volume sees nothing wrong.

Pass `--skip-self-intersection` on large assemblies if the boolean test
dominates runtime.

A local project audit should check shared fit equations and connector-ledger
assertions, not rebuild the same solids solely to repeat body-count or
positive-volume checks owned by `check_fit` and `validate`. Keep the final
per-artifact validation sequence above; make it cheap through one batch process,
not by silently dropping a geometry gate.

## Interference checks

Nothing else in the toolchain answers "do any two parts occupy the same space?".
`refs` reports per-shape facts, and no per-shape fact can establish the
*absence* of a clash — least of all one buried inside the assembly.

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" interfere <project-dir>/<name>.step.py
python "$CAD_SKILL_ROOT/scripts/inspect" interfere <project-dir>/<name>.step.py --refs o1.1,o1.7
python "$CAD_SKILL_ROOT/scripts/inspect" interfere <project-dir>/<name>.step --tolerance 25
```

It boolean-intersects every candidate pair of leaf occurrences and reports
`clashCount` plus a `clashes` array — each entry naming both occurrences by ref
and label, with the intersection volume and its bounding box, largest first.
`ok` is false and the exit code is 2 when anything clashed.

**Touching is not overlapping.** Neighbouring parts share faces by design, and
the kernel returns hairline slivers for those, so an intersection below
`--tolerance` counts as contact rather than a clash. The default is 1.0 mm³:
real interpenetrations on printable parts are orders of magnitude larger. Raise
it for a model whose parts are meant to share broad faces; a raised tolerance is
an assumption to report, not a way to silence a finding.

A world-space bounding-box reject runs before the boolean, so the pairwise test
stays tractable on assemblies with hundreds of occurrences. `--max-pairs` caps
the boolean count on top of that and reports what it truncated — a truncated run
has not cleared the assembly. `--refs` restricts the check to one subtree.

An interference check is only as honest as the assembly it runs on: parts
boolean-unioned into a single solid cannot clash with each other by
construction. Keep separately printable parts as separate occurrences (see
`project-structure.md`) or this check has nothing to compare.

## Reference discovery

Compact facts and planes:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" refs path/to/model.step \
  --facts --planes --positioning
```

Detailed selector inspection:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" refs path/to/model.step '#selector' \
  --detail --positioning
```

Topology enumeration, only when needed:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" refs path/to/model.step --topology
```

Plane options:

```bash
--plane-coordinate-tolerance FLOAT
--plane-min-area-ratio FLOAT
--plane-limit INT
```

Use lower plane limits and compact facts for normal validation. Use topology enumeration only for selector discovery, complex debugging, or when a feature cannot be verified through facts/planes/measurements; it can be expensive on large models.

Filter plane groups before opening detailed selectors. Once selectors for a
spec dimension are known and topology has not changed, run the targeted
`measure` directly; enumerating every candidate face again is duplicate work.

## Measurement checks

Use `measure` for bounding distances, clearances, offsets, part spacing, plate thickness, hole-to-face distances, and alignment verification.

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" measure path/to/model.step \
  --from '#selector_a' \
  --to '#selector_b' \
  --axis x
```

Axis may be inferred when possible, but specify `x`, `y`, or `z` for deterministic checks.

## Alignment checks

Use `align` when two exported STEP references should be flush or centered. It returns a translation delta between the selected refs; apply any required correction in the build123d source (see `positioning.md`), regenerate, and re-inspect.

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" align path/to/assembly.step \
  --moving '#moving_selector' \
  --target '#target_selector' \
  --mode flush \
  --axis z
```

## Frame inspection

Use `frame` to validate occurrence transforms and selected-reference world frames:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" frame path/to/model.step '#selector'
```

Frame output is useful for assemblies, part-local-to-world conversion, and placement debugging.

## Diff checks

For modification tasks, compare before and after artifacts:

```bash
python "$CAD_SKILL_ROOT/scripts/inspect" diff path/to/before.step path/to/after.step --planes
```

Use diff when a repair, feature addition, or source edit could affect unrelated geometry.

## Validation report content

Report only checks that were actually run or directly supported by tool output. If an important selector was inspected, return the local selector ref beside the file it belongs to.

Use this structure:

```text
Validation:
- STEP generation: passed/partial/failed
- Solids/assembly: <counts and labels>
- Bounding box: <dimensions and units>
- Major planes/refs: <summary>
- Positioning: <frame/measure/align results if relevant>
- Feature checks: <holes, cutouts, bosses, etc.>
```

Do not claim:

- structural safety
- process certification
- tolerance compliance
- manufacturability beyond geometric plausibility
unless the relevant analysis or manufacturing data was explicitly performed.
