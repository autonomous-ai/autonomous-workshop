# Shared skill provenance

## `cad` and `step-parts`

- Canonical snapshot: `peterat617/text-to-3d` at
  `54804a8da4b462ab055c522d46c1a3f099bc21e2` (2026-08-24).
- Migrated from Bob on 2026-08-23 after a byte-for-byte comparison showed Bob
  already carried the complete current upstream versions.
- Updated `cad` on 2026-08-24 to pull print-cost measurement, hollowing, and
  mesh-repair additions (`f18aebe..54804a8`); `step-parts` was unchanged in
  that range.
- Adapted `cad` and `step-parts` locally on 2026-08-26 for the
  component-oriented installed layout: command guidance resolves each
  package-owned skill through `workshop skills path`, and CAD warm-daemon
  identity and staleness are rooted in the installed CAD skill rather than a
  deleted repository-level `skills/` tree. Geometry and validation algorithms
  are unchanged.
- Included license: MIT, copyright 2026 Thompson Labs LLC. See each skill's
  `LICENSE` and the embedded cadgen license.
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
principles learned during the ecosystem audit without copying the unlicensed
`text-to-3d/skills/image-to-cad` files.

The 2026-08-24 review separated AI-agent Playtest evidence from physical
production: digital CAD, simulation, and slicer checks gate Release;
exact printing and hands-on QA are recorded later by Deliver.
