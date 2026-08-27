# Shared skill provenance

## `cad`, `design-reference`, `electromechanical-integration`, `image-to-cad`, and `step-parts`

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `5d1e24a6dcdac2626ddef8f74b55130f20094cee` (2026-08-27), resynced from
  `0403039457603002739359f620f8c780a2c829dc` (2026-08-26).
- The reviewed snapshot includes the complete upstream trees for all five
  skills. `cad` includes the vendored `cadgen` 0.4.19 source, bought-part mount
  tooling, run-cost guidance, and the strengthened image-derived verification
  runner. The image workflow includes clipped-reference rejection, reference
  silhouette preparation, and stored-camera replay for lower-cost iteration.
- The 2026-08-27 resync takes upstream's hardened gates: `verify_project` grows
  its own `--self-check` fixture suite over the refusals that decide whether a
  gate runs at all, plus an explicit `--powered`/`--unpowered` classification
  that `--image-derived` final runs must now declare; `check_thickness` steps
  only the rays still in flight and reports every thin region rather than the
  thinnest point; `check_fit`, `check_layout`, `check_mount` and `check_motion`
  close gaps that let an inconclusive result pass as a skip. The image workflow
  gains a likeness-gate history with audited acceptance for a stalled loop, and
  splits its oversized `SKILL.md` into `references/likeness-gate.md`,
  `references/high-likeness-organic.md` and `references/repeated-scene.md`.
  `cadgen` stays at 0.4.19 and both `requirements.txt` files are unchanged.
- `electromechanical-integration` was added to the locked tree in the same
  2026-08-27 resync that introduced it upstream. It carries the powered-system
  research and specification workflow, `references/power-manifest.md`'s
  schema 3 declaration, `references/lighting-discovery.md`, and the
  `check_power` gate that the reviewed `cad`, `design-reference`, and
  `image-to-cad` bytes already name as `$electromechanical-integration`.
  `verify_project` resolves that gate as a sibling materialized tree, so the
  cross-skill reference now lands on a present skill rather than a missing
  one. The gate still runs only for a project that declares
  `measure/power.json`; a project without one records a skip.
- Adapted locally on 2026-08-26 only for Workshop's materialized
  `.agents/skills` layout: command examples resolve each package-owned skill
  through `workshop skills path`; the image renderer prints the absolute
  materialized likeness-checker path; the design-reference cache is rooted in
  the writable invocation workspace rather than the immutable skill tree; its
  HTTP user agent uses the renamed repository identity; CAD warm-daemon
  identity and staleness are rooted in the materialized CAD skill tree, with a
  compact portable byte-bounded socket path inside the private temp root; and
  the CAD skill documents the now-present sibling image workflow and no longer
  points at the removed repository-authored `product-to-cad` skill.
  Re-applied on 2026-08-27 to the command examples the resync introduced: the
  `meshlib.py` and `design_refs.py` self-checks, the `design-reference` test
  path, and the `step-parts` download, `verify_project` and `check_motion`
  calls the image workflow now makes. `image-to-cad/SKILL.md` declares the
  sibling `cad` and `step-parts` roots it resolves alongside the two it
  already had; the two cross-skill calls that the previous snapshot left
  unadapted are corrected with them. `electromechanical-integration`
  resolves its own `check_power` through `workshop skills path` and points
  at the materialized CAD runner rather than a checkout path, and the CAD
  skill's own `check_power` pointer is resolved the same way.
  One trailing blank line in `generation_runner.py` and one in
  `catalog-schema.md` are normalized for repository whitespace checks.
  Geometry, measurement, catalog, inspection, validation, export, and `cadgen`
  algorithms are otherwise the reviewed upstream bytes.
- Adapted locally on 2026-08-27 in the canonical `cadgen` STEP writer to apply
  the STEP header only after Open CASCADE transfer and to set its `FILE_NAME`
  timestamp to the fixed ISO-8601 value `1970-01-01T00:00:00`. This preserves
  the intended model name and originating-system metadata while making fresh,
  equivalent exports byte-identical. A real build123d solid round-trip test
  covers both reproducibility and valid geometry.
- `cad` and `step-parts` include MIT licenses, copyright 2026 Thompson Labs
  LLC. The embedded cadgen source also includes its MIT license.
- `design-reference`, `electromechanical-integration`, and `image-to-cad` do
  not contain standalone license files in the pinned upstream snapshot. They
  were migrated at the repository owner's direction; this ledger does not
  infer an MIT grant for those three trees. The external Fusion 360 Gallery dataset indexed by
  `design-reference` is separately restricted to non-commercial research and
  is downloaded only on explicit skill use with its own license and provenance.
- Update by importing and reviewing a new pinned upstream tree, running CAD
  characterization fixtures, and updating this ledger plus [`LOCK.json`](LOCK.json).
  CI verifies the exact canonical tree fingerprints. Never edit a vendored skill
  silently.

These scripts are diagnostics. Several current checks can pass empty or
inconclusive geometry, degrade boolean errors, or omit slicer/physical evidence.
Do not use their exit status alone as a Workshop release receipt.

## Removed trees

The repository-authored `product-to-cad` skill was removed on 2026-08-26. The
Invent now owns the build spec, selected visual direction, and researched
physical facts it used to restate, and Make reaches CAD through the `cad`,
`image-to-cad`, `design-reference`, and `step-parts` skills directly.
