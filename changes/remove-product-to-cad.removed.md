- Remove the repository-authored `product-to-cad` skill. The Concept stage now
  owns the build spec, the frozen visual target, and the researched physical
  facts that skill restated, and Make reaches CAD through the materialized
  `cad`, `image-to-cad`, `design-reference`, and `step-parts` skills directly.
- **Materialized instruction bytes changed**: `product-to-cad` is no longer
  materialized into a product run, the vendored `cad/SKILL.md` no longer points
  at it, and every Inventor's `<id>-inventor/SKILL.md` plus the
  `autonomous-workshop` workflow skill name the sibling skills instead. Any run
  parked mid-flight before this change must be restarted rather than resumed;
  resume fails closed on the materialized-instruction-hash mismatch by design.
