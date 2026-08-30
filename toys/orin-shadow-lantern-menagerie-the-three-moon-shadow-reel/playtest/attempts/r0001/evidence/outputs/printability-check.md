# Printability check — exact sealed STLs

Binding: Made product artifact
`3c7abf41a4aed6005216e14ad42c5c027e7560ff8cd887f3c991917141d1f7cd`;
rear-shell STL SHA-256 `082ad8cd13cb5bdba33e0a171d9356f8627e1817fbf929ee69bef233ad66b6e1`.

## Passing digital evidence

Independent mesh inspection found each sealed STL to be one connected,
watertight, manifold, consistently wound, positive-volume shell that fits a
220 x 220 x 220 mm bed:

| part | bed footprint and height (mm) |
|---|---:|
| front shell | 108 x 123 x 9.6 |
| kickstand | 108 x 87 x 6.0 |
| rear shell | 113 x 123 x 12.7 |
| shadow reel | 114 x 114 x 3.2 |

The sealed standard 0.4 mm-nozzle reports pass a 0.8 mm wall threshold, with
medians of 2.39, 4.47, 2.38, and 3.23 mm respectively. Broad-face-down,
support-free intent is documented for all four parts.

## Reproduced failing wall evidence

The sealed fine rear-shell report (SHA-256 `98fe98e7...`) already records a
failure: 5 of 364855 surface samples across three regions, with a 0.12 mm
minimum. An independent replay on the exact sealed STL requested a 0.16 mm
voxel and again failed. The bounded grid resolved to 0.261 mm and found two
isolated regions: 0.39 mm at `(32.0, 43.4, 2.4)` and 0.13 mm at
`(37.7, 38.6, 2.4)`, both near the outer rear-shell rim. The exact generated
replay is `replay-thickness-rear-shell-fine.md` (SHA-256 `e2661f7f...`).

The affected area is small, but a failed sub-nozzle thickness gate cannot be
converted into a pass by rounding it to 0.0 percent or preferring the coarser
report.

## Result

**FAIL — implementation improvement in Make.** Repair the outer rear-shell rim
with a finite feature at least 0.8 mm wide or a suitably broad printable
fillet/chamfer, regenerate STEP and STL, then require both standard and explicit
fine thickness checks to pass. Replace contradictory stale failure evidence
only after the repaired exact mesh passes.

No slicer or physical print was run. Support behavior, successful printing,
warping, fit, snap compliance, detent strength, material performance, and cycle
life remain unverified.
