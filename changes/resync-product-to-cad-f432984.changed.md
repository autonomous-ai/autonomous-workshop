- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `f432984`. `check_fit` measures a part's real extent when a freeform face is
  trimmed, so a smooth part cut flat at the bed no longer reads as below it.
  `check_mount` and `check_motion` crop an obstacle of more than 200 faces to
  the region being measured, and keep the crop only when it conserves volume.
  On a seated board in a 6000-face skin this took the check from over 30
  minutes to under 6. `render_views` meshes its source-vs-STEP drift check
  with absolute deflection and refuses a partial mesh. Its shaded views are
  sRGB-encoded, and nested assembly leaves keep their colours.
  `ref_silhouette` separates a white subject on a pale sweep.
  `check_spec_format` accepts one spec document. The wiki gains seven pages,
  for 200 in all.
- **Materialized instruction bytes changed**: the `cad`, `image-to-cad`,
  `product-design` and `wiki` fingerprints move. A run parked before this
  change must be restarted rather than resumed.
