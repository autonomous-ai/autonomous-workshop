# Prepared targeted current dimensions

No CAD command has been executed by this preparation task. All files are outside product. Current assembly SHA-256 is `088f5713abcaead93cae05310bbb32e18028aeff3645060681ce69f6556c08ff`.

Run from workspace root, after the Manager frees a CAD slot:

```bash
bash artifacts/make/r0001/visual-repair-dimensions/run-native.sh
```

This checks bindings, runs one native inspect batch of 81 frame/measure requests, then summarizes actual returned values. It includes 14 planet face widths, bore axes, matched carrier posts, radial journal differences and face standoffs; seven planet tip<HOME> radii; sun/orange gap and thickness; sun tip<HOME>, bezel OD/ID, stem and pedestal radii. The summary computes all14mesh distances, seven180-degree center correspondences, and scoped continuous radial envelopes from measured centers/radii. It does not label motion passed.

`selector-audit.json` records actual selector rows read from the existing native STEP_topology package. Discovery used cylinder radius/axis/origin and planar area/normal predicates. The old `212+6z` face formula was corroborated only after discovery. The original raw STEP identity matches the native package. The native batch itself is still needed for returned frame/measure evidence.

For actual BRep volume/centre of mass, complete print-pose bounds and exported gear-profile measurements, run separately:

```bash
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/visual-repair-dimensions/actual-step-audit.py > artifacts/make/r0001/visual-repair-dimensions/actual-step-audit.log 2>&1
```

The optional script imports only exact STEP files, never product source. It reports all44solid volume/COM, rotating32solid COM and separate black/gold rotating groups. Eight actual top-face outer wires supply tip<HOME> circle radii and actual tip-arc counts. Five actual window wires supply public nearest-boundary distances. A continuous radial rim bound is reported only when every window edge is a line: convex radial norm then has its maximum at an exported vertex. Curved window edges produce an explicit unsupported bound, not a guessed pass. It also records all21master print-pose BRep bounds. This script is prepared and syntax-checked, not execution-tested.

`unchanged-intrinsic-bridge.json` verifies12exact current-master/historical STEP matches and pins existing intrinsic measurement reports. This allows reuse of sun, orange, bezel, stem and pedestal intrinsic facts. Old assembly placements, motion or gear16/24 dimensions do not transfer; current placements are requested again.

The summary keeps2e-5mm arithmetic tolerance explicit because native table coordinates are rounded. Actual gear backlash/pitch-circle flank thickness remains outside the prepared audit; source thinning and contact qualification need separate reconciliation. No physical balance, print, friction, coasting, function or full motion claim is produced by these scripts.
