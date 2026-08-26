# Shared skill provenance

## `cad` and `step-parts`

- Canonical snapshot: `peterat617/text-to-3d` at
  `40667dec4f1ae1ab630062964cb08085990b0d04` (2026-08-25).
- The reviewed snapshot includes the complete MIT-licensed `cad` and
  `step-parts` trees, including the vendored `cadgen` 0.4.19 source, bought-part
  mount tooling, run-cost guidance, and the image-derived verification runner.
- Adapted locally on 2026-08-26 only for Workshop's materialized
  `.agents/skills` layout: command examples resolve each package-owned skill
  through `workshop skills path`; CAD warm-daemon identity and staleness are
  rooted in the materialized CAD skill tree; and the CAD skill states the
  fail-closed boundary for its optional image renderer. One trailing blank line
  in `generation_runner.py` is normalized for repository whitespace checks.
  Geometry, mount,
  inspection, validation, export, and `cadgen` algorithms are otherwise the
  reviewed upstream bytes.
- Included license: MIT, copyright 2026 Thompson Labs LLC. See each skill's
  `LICENSE` and the embedded cadgen license.
- Update by importing and reviewing a new pinned upstream tree, running CAD
  characterization fixtures, and updating this ledger plus [`LOCK.json`](LOCK.json).
  CI verifies the exact canonical tree fingerprints. Never edit a vendored skill
  silently.

These scripts are diagnostics. Several current checks can pass empty or
inconclusive geometry, degrade boolean errors, or omit slicer/physical evidence.
Do not use their exit status alone as a Workshop release receipt.

The upstream `design-reference` and `image-to-cad` directories are not bundled:
neither directory contained a license file in the reviewed snapshot. The
licensed CAD runner retains its image-derived integration point, but that mode
fails closed unless a separately authorized compatible sibling renderer is
installed. Workshop's repository-authored `product-to-cad` skill remains the
in-repository workflow for image-guided product design and release evidence.

## `product-to-cad`

Authored in this repository as a clean creation workflow. It applies general
measurement-provenance, multi-view form, manufacturing, and fail-closed evidence
principles learned during the ecosystem audit without copying the unlicensed
`text-to-3d/skills/design-reference` or `text-to-3d/skills/image-to-cad` files.

The 2026-08-24 review separated AI-agent Playtest evidence from physical
production: digital CAD, simulation, and slicer checks gate Release;
exact printing and hands-on QA are recorded later by Deliver.
