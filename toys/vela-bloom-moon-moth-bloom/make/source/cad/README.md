# Moon-Moth Bloom

Moon-Moth Bloom is a three-part hand-powered reveal toy.  Counter-rotating the
two geared wings opens a moth-like pair of crescent petals and uncovers six
star apertures.  The left wing's scalloped outer edge is the one-handed control;
the complete equal gears synchronize the right wing.

Normal operation is planar from q=0 to q=82 degrees with both wings seated.
Service assembly is deliberate and two-handed: load each keyhole over its
7.4 mm chassis flange at q=118, leave both wings raised at Z=5.7, mesh them,
counter-rotate through the 82 degree stop under the high hood, lower both by
1.2 mm at q=78, and continue seated beneath the low roof.  Reverse those steps
for disassembly.  Do not force the wings upward during normal operation.

## Fit/print audit

The project-specific audit is `measure/check_fit.py`. It checks the three
printable entry names; the shared 18.0 mm axis-spacing and module-1 gear-pitch
base dimension; the source-derived 5.0/5.6 mm journal post/running bore,
7.4/7.8 mm mushroom flange/keyhole lobe, and 5.0/6.0 mm post/keyhole throat
interfaces; the two 0.5 mm roof gaps; and the named service order below. The
audit uses only Python's standard library and files inside this CAD project,
so the host can execute it after copying the project into isolation. It reads
the source AST, requires the real `cadfits.slot_for(...)` calls, and
independently recomputes their values and clearance bands. Run:

```text
python measure/check_fit.py
```

The connector IDs, identical to those asserted in source, are:

1. `left-journal-post-to-running-bore`
2. `right-journal-post-to-running-bore`
3. `left-mushroom-flange-to-keyhole-lobe`
4. `right-mushroom-flange-to-keyhole-lobe`
5. `module-1-eighteen-tooth-external-gear-pair`

The assembly sequence IDs, in their required physical order, are:

1. `load-keyhole-lobes-over-flanges-at-q118`
2. `seat-both-wings-raised-at-z5.7`
3. `counter-rotate-under-high-hood-to-q82`
4. `drop-both-wings-1.2mm-at-q78`
5. `continue-seated-beneath-low-roof`

Printable entries are `part_chassis.step.py`, `part_left_wing.step.py`, and
`part_right_wing.step.py`.  `moon_moth_bloom.step.py` is the labeled combined
assembly in the q=41 operating pose.  Dimensions and all handed transformations
live in `moon_moth_bloom_lib.py`.

CAD source intentionally assigns no per-child colors. OpenCascade serializes
three colored child presentations in hash-dependent order, causing otherwise
identical clean builds to change the combined STEP bytes. Labels and geometry
remain in STEP; the inspected chromatic presentation is `snap/iso.png`.

The source and verifier do not claim a successful print or physical fit.
