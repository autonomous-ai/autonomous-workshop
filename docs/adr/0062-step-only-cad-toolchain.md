# ADR 0062: STEP is the only geometry Workshop writes

**Status:** accepted (2026-09-10). Supersedes the print-ready half of ADR 0027,
ADR 0052 and the full/non-print-ready tier split introduced alongside them.

## Context

The `cad`, `image-to-cad`, `design-reference`, `electromechanical-integration`
and `step-parts` skills under `src/workshop/make/skills/` are vendored from
`autonomous-ai/autonomous-product-to-cad`. Upstream's
`cad/drop-assembly-glb-export` branch (`39a63f7`) is a single coherent
capability removal: STEP becomes the only format the toolchain writes.

It deletes `scripts/export`, `meshlib.py`, `cadprint.py`, `repair_mesh`, the
`check_mesh`, `check_thickness` and `check_overhang` gates, cadgen's STL and
3MF writers, `verify_project --exports`, and the `supported-exports.md`,
`repair-loop.md` and `print-optimisation.md` references. Its `SKILL.md` states
that a request for an STL, a 3MF, a GLB or any sliced mesh has no workflow
here, and that an output must never be called print-ready.

Every non-deletion hunk in that branch is prose or validation following from
the removal. There is no independent improvement to cherry-pick, so the choice
was binary: adopt the removal, or fork the mesh half permanently.

Workshop's Make stage was built on the half being removed. The host shelled
`scripts/export <source.step> --stl`, rendered product images from the exported
STL, required `state-0/1/2.stl` signature evidence and `assembled.stl`,
packaged `parts/<occurrence>.stl` per occurrence, normalized `check_thickness`
and overhang reports across the sealed-tree comparison, and gated Release on
full-tier, thickness-checked, print-ready CAD evidence.

## Decision

Adopt the removal in full. STEP is the only geometry format Workshop writes,
seals, or ships, and **no Workshop stage may call a product printable or
print-ready**, because nothing in the toolchain measures a wall, a mesh or an
overhang any more.

## Consequences

**Presentation keeps working; it changes its input.** `render_product` and
`motion_presentation.py` tessellate the exact STEP in memory (the same
`build123d` path upstream's `render_review` uses) instead of reading an STL.
Its `--state-stl` flag becomes `--state-source`; motion evidence states are
`.step` and its schema goes 1 -> 2. No mesh reaches disk.

**The cheap print preflight is gone.** Workshop's local `--print-preflight`
mode, its `measure/print-preflight.md` record, and the `print_preflight_sha256`
binding in the signature review are removed; the review schema goes 6 -> 7.
`make-round` reports a per-part *build* verdict where it reported a wall
verdict, and no longer takes `--nozzle`.

**The CAD gate has one tier.** `digitally-verified-not-print-ready` is the only
tier the host can produce. A Made artifact must declare it twice — the product
status *and* a literal `final_pipeline.print_ready_claim: false` — and a
product still claiming print readiness is refused rather than downgraded.
`thickness_gate_required` and `print_ready_eligible` are always false, the
legacy full-tier replay path is retired (it would rerun a verifier that no
longer exists), and `require_print_ready=True` always fails closed with
`cad-not-print-ready`. The verifier command loses `--exports`.

**Release stops asserting printability.** Forge and Quest Release previously
required full-tier print-ready evidence, which can no longer exist; Release now
requires passing not-print-ready evidence and publishes a digitally verified
exchange solid whose printability is unverified.

**Sealed products carry solids.** `assembled.stl` leaves the required root
files; multi-part products seal `parts/<name>.step` per occurrence; build
groups address `parts/<key>.step`; the public archive and Factory handoff ship
STEP. A Made manifest carrying `.stl`, `.3mf` or `.glb` is now refused.

**Two host consumers still need triangles, and tessellate for themselves.** The
pinned three.js renderer and the Factory viewer's part keying both work on
triangles. Both now tessellate the sealed STEP into throwaway staging bytes
(`renders.step_triangle_mesh`). Those meshes are renderer scaffolding: nothing
writes them to a deliverable, ships them, or reads them as a printability
claim.

**Frozen runs are untouched.** Skills are materialized once at run creation, so
a frozen run keeps its own skill bytes. The deep-v5..v9 proof-turn instructions
and the `deep-economics-v1..v13` profiles are left exactly as they were; new
runs freeze `deep-economics-v14`, which drops v13's wall-thickness repair
routing because there is no preflight report to route from.

## Not decided here

The Factory service accepts `.step`/`.stp` uploads, so the transport format is
viable, but the shop-side sidecar schema is renamed (`stlPath` -> `stepPath`,
`production_stls` -> `production_steps`) and that wire contract has not been
confirmed against the live service.
