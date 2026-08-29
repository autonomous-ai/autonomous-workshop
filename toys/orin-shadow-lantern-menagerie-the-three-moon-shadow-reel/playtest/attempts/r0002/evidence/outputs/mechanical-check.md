# Mechanical check — reset, closure, stops, motion, and containment

Binding: exact Made product artifact
`28e8a417d8ffe4e4c702c5eea1ca336dab843d950149ef768fc1f5d9da66787f`;
assembled STEP SHA-256 `bb5108fe…`; CAD source SHA-256 `4ad4b159…`.
The fit and motion checks were replayed from an isolated work-area copy,
leaving every sealed Made byte unchanged.

## Passing nominal deterministic evidence

- The project fit audit passes all 17 conditions: 0.30 mm spindle radial and
  blind-end clearances; 0.30 mm front and rear axial reel gaps; 0.40 mm hook
  slot clearance on both audited axes; 0.20 mm hook lead clearance; 0.30 mm
  retained overhang on each side; 0.20 mm detent radial clearance; 0.50 mm
  flat and 0.25 mm fox/owl detent deflections; zero rabbit deflection; 0.25 mm
  rabbit-home differential; 0.35 mm stand-socket radial clearance; and a
  5.10 mm hinge setback behind the rear outer face.
- The kickstand clears its ordinary deployed-to-folded travel at all 29
  samples. Its deployed stop blocks at sample 5/11 with 0.585308 mm³ overlap;
  its folded stop blocks at sample 3/11 with 99.083983 mm³ overlap.
- The reel clears the rear shell and deployed stand throughout all 73 samples
  of a 360° cycle. Intended compliant leaf contact is explicitly outside this
  rigid-body check.
- The closed shell's rigid pullout condition blocks at sample 1/21 with
  5.485714 mm³ overlap, demonstrating modeled retained shoulders. Separate fit
  measurements establish the chamfered hook lead path; rigid collision cannot
  model elastic insertion.
- The sealed fresh verification pipeline passes layout, strict source build,
  direct project fit, STEP validity, final-pose clash inspection, mesh checks,
  and two deterministic assembled STEP generations with identical
  `bb5108fe…` hashes.

## Adversarial implementation failures

1. The 73-sample reel manifest omits the `front_shell`, explicitly excluding
   the functional detent contact. An adversarial replay that includes the front
   shell collides at sample 1/73 with 0.645482 mm³ overlap. Compliance is
   intended, but the flat cylindrical nose and vertical-walled pockets have no
   authored cam-out ramp, so the evidence does not establish that a user can
   leave and re-enter a click in either direction.
2. The chamfered hook lead face is 3.4 × 5.2 mm and the receiver is 3.6 × 5.4
   mm, but each barb then expands symmetrically to 4.2 × 6.0 mm. The fit audit
   is arithmetic and the motion condition begins after closure. Ordinary
   one-axis cantilever bending therefore does not demonstrate that this
   four-sided oversized barb can traverse the receiver. Pullout retention is
   conditional on an unproven insertion path.
3. `STAND_DEPLOY_DEG` is 108°, while the adjacent source comment and authored
   brief require 112° to yield the promised 68° deployment. The verified
   assembly depth is 94.067 mm (`maxY-minY`), not the brief's “about 82 mm.”
   Collision thresholding also permits about 4° deployed and 2° folded
   overtravel before a stop is reported.

## Result

**FAIL — implementation improvement in Make.** Add a rounded/ramped detent
nose and chamfered/ramped pockets, then verify actual compliant engagement and
a complete two-way cycle. Replace the symmetric four-sided barb with a
one-direction cantilever latch or other receiver having a demonstrable closure
path, and test insertion separately from pullout. Correct the stand angle and
footprint to the authored endpoint and rerun finer endpoint and full-arc
sweeps.

No physical snap insertion, retention force, detent feel, stand load,
center-of-mass/tipping margin, pinch safety, printer compensation, material
strength, or cycle life was tested or established.
