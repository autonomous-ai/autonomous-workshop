# ADR 0026: Preserve Wish-critical form through Make repair

- Status: Accepted
- Date: 2026-08-30
- Owners: Make, product-run instruction, CAD skill, and native finalizer maintainers
- Relates to: ADR 0022 (blind review), ADR 0023 (bounded Spark), ADR 0025 (form-bound review)
- Supersedes for new runs: ADR 0025's schema-v4 signature review

## Context

Tempest Lull was a real published Spark run. The Wish explicitly required a
fully volumetric pillow-like cloud and prohibited a constant-depth extrusion.
The first exact draft was sculptural but failed wall thickness. Make spent two
review rounds before the full printability result, then repaired the geometry
into a common-depth relief. The final review and compact Spark concept both
named that deviation while still claiming the form matched.

The session also submitted a locally passing report that omitted the failed
thickness check. The trusted host's isolated full-tier gate rejected it, but a
cheap run-local finalizer could have prevented the proposal and rebuild.

## Decision

New materialized runs use signature-review schema v5. After the blind read and
Wish reveal, the one critic enumerates every explicit positive and negative
held-form constraint in `critical_form_requirements`, cites visible blind
evidence for each, and sets each `matches: true`. Any remaining visible
requirement failure belongs in `blocking_visual_defects`; the array must be
empty before Make can finalize.

Make runs narrow mesh and thickness checks against the fresh draft export before
spending a visual-review round. Any geometry change after review invalidates the
review and requires regenerated images plus a fresh blind read. Spark's compact
Invented packet remains subordinate to the exact Wish and cannot normalize a
contradictory repair by rewriting concept prose.

The run-local finalizer parses the current verification record. It requires
final mode, a passing headline, a successful `check_thickness` row, and no
`--skip-thickness`. Prior preserved records do not count. The trusted host still
performs the independent isolated full-tier rebuild.

## Consequences

- Printability failures are found before the bounded visual-review spend.
- A critic must confront each explicit Wish form constraint instead of hiding a
  contradiction behind one aggregate boolean.
- Omitting thickness fails locally before another host rebuild and native turn.
- No host-side vision model, score, extra critic, or Python reasoning loop is
  introduced.
- Frozen older runs retain their materialized protocol and review schema.

## Verification

- Finalizer tests reject a failed critical form check, nonempty blocking defect,
  missing thickness row, and a current failure followed by a preserved pass.
- CAD tests reject blocking schema-v5 evidence before geometry work.
- Deterministic Spark, Forge, and Quest fixtures submit schema-v5 review evidence
  and a current passing full-tier report.
