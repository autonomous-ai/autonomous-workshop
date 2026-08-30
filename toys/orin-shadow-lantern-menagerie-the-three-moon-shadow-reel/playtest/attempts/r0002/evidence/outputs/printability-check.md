# Printability check — exact sealed STLs

Binding: exact Made product artifact
`28e8a417d8ffe4e4c702c5eea1ca336dab843d950149ef768fc1f5d9da66787f`.
Independent replays used the exact four sealed STL hashes listed in the
canonical configuration and wrote only transient reports in the Playtest work
area.

## Passing deterministic evidence

Each STL is one connected, watertight, manifold, consistently wound,
positive-volume shell with zero slivers and fits a 220 × 220 × 220 mm bed:

| part | triangles | bed footprint and height (mm) |
|---|---:|---:|
| front shell | 1,520 | 108 × 123 × 11.0 |
| kickstand | 316 | 108 × 87 × 9.0 |
| rear shell | 1,716 | 113 × 123 × 12.7 |
| shadow reel | 3,880 | 114 × 114 × 3.2 |

Independent standard 0.4 mm-nozzle thickness replays pass the 0.8 mm minimum
on every part:

| part | below-minimum samples | total samples | median thickness (mm) |
|---|---:|---:|---:|
| front shell | 0 | 331,894 | 2.26 |
| kickstand | 0 | 147,426 | 4.55 |
| rear shell | 0 | 327,673 | 3.17 |
| shadow reel | 0 | 394,443 | 3.23 |

The explicit rear-shell replay requested a 0.16 mm voxel. Its bounded grid
resolved to 0.261 mm with ±0.130 mm thickness resolution and found 0 of 336,020
samples below 0.8 mm; 1,061 additional samples were within measurement error.
This materially repairs round one's reproducible 0.13 mm rear-rim failure.

The sealed fresh pipeline also passes source bed fit, STEP validation, zero
final-pose clashes above 1 mm³, and all four mesh and standard thickness gates.

## Result

**PASS — digital mesh/bed/wall evidence only.** “No supports intended” remains
a design intent: no pinned slicer or overhang gate was run. Short hook-barb
undersides and horizontal blind bearing-socket roofs could bridge or sag by
process, and 1,583 sub-0.8-mm reel mesh edges do not by themselves prove tuft
strength.

No successful print, slicer support decision, warping, layer adhesion, snap
survival, fit, detent feel, strength, or cycle life was tested or established.
