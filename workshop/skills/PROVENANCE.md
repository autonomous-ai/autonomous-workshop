# Shared skill provenance

## `cad` and `step-parts`

- Canonical snapshot: `peterat617/text-to-3d` at
  `f18aebe4698d92ffccf07d94e2d624b08d30e667` (2026-08-21).
- Migrated from Bob on 2026-08-23 after a byte-for-byte comparison showed Bob
  already carried the complete current upstream versions.
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
