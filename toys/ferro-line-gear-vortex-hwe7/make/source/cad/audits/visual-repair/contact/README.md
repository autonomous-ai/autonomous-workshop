# Seven-gear loaded tooth-contact diagnostic — prepared, not executed

This adapts the preserved `../mesh-contact/measure_contact.py` and its seventeen-sample extension to the accepted seven-gear design. The old diagnostic and all old results are untouched. Only the non-CAD `--plan` preparation was run here. There are no new contact measurements or motion-pass claims in this prepared package.

The exact current source is copied into `snapshot/` (params, gear builder, gearing and thread features, package initializers). `source-bindings.json` records each snapshot's matching product path and SHA256, plus the accepted qualification, design handoff, assembly placement and historical-method references. Before and after measurement, the script fails closed if any bound live or snapshot bytes have changed. A later legitimate source change requires an explicit refreshed snapshot/binding and a new run; do not silently run this historical snapshot as current evidence.

## Run after other CAD jobs, sequentially

Run from the workspace root with the materialized Python interpreter. This command is preparation only; it imports no CAD:

```bash
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/visual-repair-mesh-contact/measure_contact.py --plan
```

For the root Manager to measure both arms,238 actual samples:

```bash
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/visual-repair-mesh-contact/measure_contact.py --arm all --run all17-r1
```

If the Manager deliberately chooses one-arm representative evidence,119 actual samples:

```bash
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/visual-repair-mesh-contact/measure_contact.py --arm 1 --run arm1-17-r1
```

Arm2 can be measured separately using `--arm 2 --run arm2-17-r1`. Do not call119 measurements238 measurements: opposite-arm tooth contact is analytically equivalent under the exact180° gear duplication and the even36T sun, but only the selected arms are measured. The sun is shared and its asymmetric hub/spokes are not half-turned; the arm2 planet solids and their full spoke patterns are half-turned exactly.

After an external interruption, reuse the exact same command with `--resume` appended. Resume verifies the bound identity, retains recorded rows without modification and measures only missing deterministic samples. No phase adjustment, interpolation, optimization or failed-sample omission occurs. It refuses completed runs, source mismatches, duplicate sample keys or a prior recorded kernel error. A complete error row is preserved; diagnose it and start a differently named run. A truncated JSONL line is not silently repaired or accepted. No timeout override, process detachment or additional worker is created.

## Fixed sampling and unchanged limits

Each selected arm has seven exact pitch-center pairs:36/14,14/15,15/18,18/20,20/22,22/23,23/26. Initial planet phase is the current `PHASES[i]+LOADED_PHASE_OFFSETS[i]`; sun initial phase is zero. Every planet's complete current solid is used, including teeth, spokes, hub and bore. For each pair andj=0..16:

- Driver increment is `d=2*pi*j/(16*z_driver)`.
- Follower increment is `-d*z_driver/z_follower`.
- Centers remain exactly the accepted unrounded source centers.
- Arm2 occurrences add the complete180° arm transform, while the shared sun retains its own world orientation before the diagnostic increment.

This covers one full driver tooth period, including both endpoints. It is a fixed-center pair diagnostic, not the product's operating cycle. In the actual sculpture the sun stays fixed and the carrier moves; this diagnostic's spinning sun in pair36/14 is only a relative mesh geometry test and must never be presented as an operating animation.

The kernel operations are unchanged: `shape.distance_to(other)` for minimum BRep distance, `shape.intersect(other)` for common volume. Distance must be ≤**1e-6 mm** and common-volume magnitude ≤**0.001 mm³** at every measured sample. Signed raw volume is retained; absolute volume comparison prevents a negative orientation artifact from evading the old overlap threshold. No tolerance is relaxed. Kernel zero is numerical zero, not exact real-number arithmetic or physical fit.

The17sample interval gives maximum pointwise tip arc travel0.330287977643034 mm (14T), below0.35 mm; its chord bound is0.330277149824895 mm. `PLAN.json` records both gears' angular and tip-travel bounds for every pair. This bound describes sampling density; it is not continuous-contact proof.

The analytical loaded-offset equation is checked without optimization: for zero-based planeti, `z_parent*delta_parent+z_i*delta_i=(-1)^(i+1)*4*BACKLASH_FLANK/M`, withsun offset zero. The current offsets are fixed input. No result-driven phase correction is permitted in this script.

## Outputs and status

A new run owns only `runs/<name>/` below this diagnostic folder:

- `run-identity.json`: bound plan, script/binding hashes and Python version.
- `contact-results.jsonl`: each measurement immediately appended, including failures/errors.
- `contact-results.json`: completed rows and per-pair results; written only after every requested sample and final source recheck.
- `summary.json`: compact PASS/FAIL for this discrete contact scope only, result hash and per-pair extrema.

Exit0 means all completed samples pass this diagnostic. Exit2 means one or more completed measurements fail. Exit3 means a preserved kernel exception. Any other interruption or source failure leaves the diagnostic incomplete/UNVERIFIED; partial passing rows do not imply a completed pass. Root still owns all Workshop verification and lifecycle decisions.

## Analytical applicability and limits

At preparation, live params exactly equal the accepted robust candidate:14/15/18/20/22/23/26, sun36, module1.5,20°,0.85m addendum,0.18 mm/flank thinning,5 mm faces, five2.6 mm nominal swept webs and3 mm root rims. The current gear builder uses negative hand at index0 and alternates; the accepted centers, phases and offsets match exactly. Thus the seven-gear source-level qualification remains applicable. The historical six-gear analytic/contact results do not apply to this new chain.

New14T lies below the matching-rack undercut threshold14.53 but uses the existing directly printed root/involute source. The accepted ideal active-roll minima are positive and minimum contact ratio1.28819; those analytical statements are not actual spline-BRep contact measurements. This diagnostic is what tests the sampled BReps without altering them.

No whole-assembly collisions, journal excursions, carrier/stand clearances, insertion/retention paths, torque transfer, coasting, physical balance, successful print or print readiness are established here. Both drive-direction loaded states are not claimed: these are the saved positive-carrier loaded phases, sampled over one pair tooth period. Reversal consumes backlash. Existing formal assemblyr3 motion status remains UNVERIFIED, not passed, and this diagnostic does not replace or manually compensate for any skipped/failed host motion gate. Run it only under the Manager's current authorized verification policy.
