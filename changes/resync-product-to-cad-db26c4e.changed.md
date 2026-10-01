- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `db26c4e`. Only one wiki page moved upstream. In
  `modeling/element-libraries.md`, the "CadQuery libraries that do not apply"
  table now rules out `cq-gridfinity`, `argus-diff` and `dl4to4ocp`, and says
  why for each. It also gives `cq-kit` its own row and corrects the old claim
  that `cq-kit` is not on PyPI.
- **Materialized instruction bytes changed**: the `wiki` fingerprint moves. A
  run parked before this change must be restarted rather than resumed.
