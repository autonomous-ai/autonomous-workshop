- Resync the vendored `cad`, `design-reference`, `electromechanical-integration`,
  `image-to-cad`, and `step-parts` skills to
  `autonomous-ai/autonomous-product-to-cad` `1e56c14`, refreshing `LOCK.json`
  and the provenance ledger. `design-reference`,
  `electromechanical-integration` and `step-parts` are byte-identical to the
  previous snapshot; `cadgen` remains pinned at 0.4.19.
- `check_overhang` is a new CAD gate and the only one that knows which way is
  up: it measures down-facing surface off every exported printable and splits
  it into spannable bridges and failing overhangs, so a part whose every
  feature hangs in mid-air can no longer pass `check_fit`, `check_mesh` and
  `check_thickness` on its way to the bed.
- `check_spec_numbers` is a new CAD gate that holds a backticked constant
  quoted in a `*_spec.md` to the value its module defines, at the precision the
  spec wrote it. `verify_project` runs it in every mode wherever a `*_spec.md`
  exists and records a skipped row where there is none.
- `check_motion` poses every mover from the project's own kinematics for a
  coupled sweep, re-runs it once per driven part, treats a coupled condition
  with no `obstacle_parts` key as inconclusive rather than sweeping the movers
  against each other alone, reports its own step so a sweep too coarse to see a
  collision cannot read as clear, and validates a declared `retention` chain
  down to a genuine fixed frame.
- `check_thickness` classifies each sub-minimum region as a wall, a taper or a
  spot from the width of the band rather than from its thinnest point, so a
  hole breaking out of a curved surface is reported and budgeted instead of
  failing the part; `--strict-thin` restores the old behavior. Material entry
  now needs two consecutive occupied samples, and a one-pitch band beside a
  genuine mesh crease is not sampled.
- `render_review` renders shaded PNGs without a browser, and
  `image-to-cad`'s `render_views.py` gains the matching `--shaded` output: a
  silhouette can hide every interior part of an exposed mechanism, and is now
  reserved for outline and likeness claims. The CAD skill's tool listing
  resolves the new runner through `workshop skills path`.
- The CAD skill declares `Pillow>=10,<13` beside its `cadgen` pin. Workshop's
  own `pillow` dependency is tightened to the same range, and
  `tools/verify_skill_locks.py` now requires every requirement the skill
  declares to be pinned identically by the Workshop rather than requiring the
  skill to depend on `cadgen` alone.
- **Materialized instruction bytes changed**: the `cad` and `image-to-cad`
  fingerprints are new, so a run parked before this change must be restarted
  rather than resumed; resume fails closed on the materialized-instruction-hash
  mismatch.
