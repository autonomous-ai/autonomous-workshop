# Make

Owns mechanical and 3D creation, CAD verification, maker provenance, Make
contracts, and the Workshop's single locked skill tree in `skills/`. Forge and
Quest consume the exact sealed Invent result; Spark seals its concept inside
Make.

Public API: `workshop.make`.

New CLI products select `--make print` (the default) or `--make mixed`.
Print mode keeps product components within 3D printing; mixed mode adds stock,
handcraft and purchased components plus the required private manufacturing
manifest and complete public presentation. Mixed is Spark-only in this MVP.
The selection is frozen for the run, while existing unselected runs keep their
historical behavior. Both modes share CAD tools and Make's engineering checks.

Reusable Codex-native creation capabilities live once in `skills/`. The host
materializes their exact locked bytes into each private product run; Inventors
use those shared capabilities without copying or wrapping them in Python.

The `cad`, `design-reference`, `electromechanical-integration`,
`image-to-cad`, and `step-parts` skills are reviewed snapshots of
`autonomous-ai/autonomous-product-to-cad`. `LOCK.json` binds
their canonical trees to an exact upstream revision, while `PROVENANCE.md`
records local path adaptations and the distinct license status of each
upstream tree.

## Creation capabilities

The native Make path accepts parametric build123d CAD, not a fixed vocabulary
of boxes and cylinders. Its reusable skills cover:

- Single parts and labeled multipart assemblies: enclosures, brackets,
  fixtures, holes, slots, ribs, shells, fillets, mating datums and joints.
- Image-derived reconstruction: measured proportions, scale assumptions,
  component decomposition, lofted organic forms and reference-view comparison.
- Mechanical integration: insertion/removal paths, hinges, latches, retention
  and coupled mechanisms checked against declared motion samples.
- Bought-part and electromechanical integration: catalog STEP sourcing,
  component seats, motors, servos, lights, power paths, wiring envelopes and
  service access.

These are toolkit capabilities, not a promise that every design will converge
or operate physically. Wish, Inventor and Daydream policies may deliberately
choose a narrower product scope; they are not the CAD geometry grammar.

## Outputs and verification

STEP is the only sealed geometry deliverable. Make also hands off source,
manifests, renders and verification evidence. `NativeMade` rejects STL, 3MF
and GLB artifacts; render meshes are temporary tool data, not shop deliverables.
Make does not produce slicer jobs, G-code or CAM toolpaths.

The [integrated CAD verifier](skills/cad/scripts/verify_project) checks source
layout, applicable spec audits, solid validity, fit and assembly interference.
Mount, power, motion and image-derived checks apply when their contracts
require them. Print readiness additionally requires a passing
`verify_project --print-gates --nozzle <mm>` run: the mesh, overhang and
wall-thickness gates tessellate source B-reps internally without exporting a
mesh. Digital verification alone is not print verification.

Forge and Quest retain an independent host rerun. Its full tier requires both
product status `full-with-thickness` and a literal `print_ready_claim: true`
in the bound receipt; the current host rerun uses a 0.4 mm nozzle. The lower
tier is `digitally-verified-not-print-ready`. Spark preserves Make's own
verification and exact output bytes without a duplicate host CAD rebuild or
acceptance pass; see [ADR 0061](../../../docs/adr/0061-spark-make-owned-verification.md)
and [ADR 0063](../../../docs/adr/0063-print-gates-on-source.md).

## Evidence limits

- Motion gates check sampled rigid-body collisions, retention and necessary
  contact evidence. They do not establish force transmission, sustained
  contact, friction, elasticity, snap-fit compliance or physical operation.
- Electrical gates check declared ratings, paths, provenance and integration
  evidence. They do not certify circuits, batteries, thermal behavior, EMI or
  optical performance. Physical fit needs tests with the actual hardware.
- Silhouette likeness measures outline agreement, not color, absolute
  placement or complete visual correctness. Native visual inspection and
  independent review provide judgments the deterministic tools cannot prove.
- Passing CAD and print gates is not evidence of manufacture, successful
  assembly, durability, play value or safety certification. Those claims need
  the corresponding physical evidence; physical Operations follow Workshop.

See the [CAD skill](skills/cad/SKILL.md),
[image-to-CAD skill](skills/image-to-cad/SKILL.md) and
[electromechanical skill](skills/electromechanical-integration/SKILL.md) for
the supported workflows and their detailed boundaries.
