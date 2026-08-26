# Shared skill provenance

## `cad`, `design-reference`, `image-to-cad`, and `step-parts`

- Canonical snapshot: `autonomous-ai/autonomous-product-to-cad` at
  `0403039457603002739359f620f8c780a2c829dc` (2026-08-26).
- The reviewed snapshot includes the complete upstream trees for all four
  skills. `cad` includes the vendored `cadgen` 0.4.19 source, bought-part mount
  tooling, run-cost guidance, and the strengthened image-derived verification
  runner. The image workflow includes clipped-reference rejection, reference
  silhouette preparation, and stored-camera replay for lower-cost iteration.
- Adapted locally on 2026-08-26 only for Workshop's materialized
  `.agents/skills` layout: command examples resolve each package-owned skill
  through `workshop skills path`; the image renderer prints the absolute
  materialized likeness-checker path; the design-reference cache is rooted in
  the writable invocation workspace rather than the immutable skill tree; its
  HTTP user agent uses the renamed repository identity; CAD warm-daemon
  identity and staleness are rooted in the materialized CAD skill tree; and the
  CAD skill documents the now-present sibling image workflow.
  One trailing blank line in `generation_runner.py` and one in
  `catalog-schema.md` are normalized for repository whitespace checks.
  Geometry, measurement, catalog, inspection, validation, export, and `cadgen`
  algorithms are otherwise the reviewed upstream bytes.
- `cad` and `step-parts` include MIT licenses, copyright 2026 Thompson Labs
  LLC. The embedded cadgen source also includes its MIT license.
- `design-reference` and `image-to-cad` do not contain standalone license files
  in the pinned upstream snapshot. They were migrated together at the
  repository owner's direction; this ledger does not infer an MIT grant for
  those two trees. The external Fusion 360 Gallery dataset indexed by
  `design-reference` is separately restricted to non-commercial research and
  is downloaded only on explicit skill use with its own license and provenance.
- Update by importing and reviewing a new pinned upstream tree, running CAD
  characterization fixtures, and updating this ledger plus [`LOCK.json`](LOCK.json).
  CI verifies the exact canonical tree fingerprints. Never edit a vendored skill
  silently.

These scripts are diagnostics. Several current checks can pass empty or
inconclusive geometry, degrade boolean errors, or omit slicer/physical evidence.
Do not use their exit status alone as a Workshop release receipt.

## `product-to-cad`

Authored in this repository as a clean creation workflow. It applies general
measurement-provenance, multi-view form, manufacturing, and fail-closed evidence
principles and remains a distinct workflow for product-design briefs rather
than direct reference-image reconstruction.

The 2026-08-24 review separated AI-agent Playtest evidence from physical
production: digital CAD, simulation, and slicer checks gate Release;
exact printing and hands-on QA are recorded later by Deliver.
