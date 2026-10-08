- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad`, `product-design`,
  `step-parts` and `wiki` skills to `autonomous-ai/autonomous-product-to-cad`
  `8488b44`. `check_mount` reads a clearance equal to its floor as that floor
  rather than failing it on float rounding, and the bought-parts reference adds
  one mount row per assembly state a part is checked in. `cadmount.seat_for`
  documents that the mouth is on the +insert side. `ref_silhouette` gains an
  opt-in `--ground tint` rule that separates a coloured subject from its own
  dark contact shadow. `render_views --compare-step` accepts scattered edge
  jitter of at most 2 px on at most 10 % of the outline, and still fails a
  moved or missing shape. The wiki gains two pages, for 202 in all.
- **Materialized instruction bytes changed**: the `cad`, `image-to-cad` and
  `wiki` fingerprints move. A run parked before this change must be restarted
  rather than resumed.
