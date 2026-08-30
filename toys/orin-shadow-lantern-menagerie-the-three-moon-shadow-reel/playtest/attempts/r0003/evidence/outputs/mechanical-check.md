# Mechanical check — detent, closure, stops, motion, and containment

Binding: exact Made product artifact
`7670e30199d25813d015f1b36cf8962e78a01722cff02524ee3240b938793d00`;
assembled STEP SHA-256 `3e024330…`. The root Manager replayed the sealed source
from an isolated work copy, and an independent native mechanical reviewer
audited the exact source and results.

## Passing deterministic evidence

- The paired-fit audit passes all 21 conditions. The detent has a 0.95 mm tip,
  symmetric 0.70 mm-run × 0.18 mm-deep conical ramps, 0.20 mm radial
  clearance, 0.50 mm flat travel, 0.25 mm fox/owl residual travel, zero rabbit
  residual travel, and 0.25 mm rabbit-home differential.
- Hard reel parts clear all 73 steps clockwise and all 73 counterclockwise.
  The compliant front leaf is intentionally excluded from rigid collision;
  the fit audit proves nominal cam geometry, not elastic behavior.
- All four 3.0 mm-diameter, 11 mm latch-leading-face path proxies clear their
  receivers. The 3.2 × 5.0 mm leads enter 3.6 × 5.4 mm slots with 0.40 mm
  total X/Y clearance, 0.60 mm one-axis flex/positive overhang, and 0.20 mm
  opposite-side clearance. Closed-shell pullout blocks at step 1/21 with
  2.857143 mm³ overlap.
- The stand source endpoint is 112°. Deployed-to-folded travel clears all 57
  steps. Deployed overtravel blocks at step 1/11 with 0.777264 mm³ overlap;
  folded overtravel blocks at step 6/21 with 30.080143 mm³ overlap.
- The specification audit passes all 24 checks. The endpoint field records
  82.395 mm deployed depth; the sealed STEP bounding box spans 82.844649 mm in
  depth. Both satisfy the authored “about 82 mm” target, but 82.395 mm is not
  repeated as the root STEP bounding-box measurement.

The complete isolated replay passes 10/10 motion conditions. The exact motion
manifest is `cad/measure/motion.json` (`288ffcda…`), fit audit source is
`cad/measure/check_fit.py` (`4f0657d2…`), and the sealed verification report is
`cad/measure/verification-pipeline.md` (`8c27421c…`).

## Result

**PASS — bounded digital mechanical evidence.** This retires the round-two
rigid geometry and path failures. It does not prove printed detent force or
feel, elastic latch insertion force/strain, snap survival, retention force,
printer compensation, tipping/load behavior, pinch safety, strength, or cycle
life.
