# Printability check — exact sealed STL replay

Binding: exact Made product artifact
`7670e30199d25813d015f1b36cf8962e78a01722cff02524ee3240b938793d00`.
All replays used exact manifest-matching STL copies in the transient Playtest
work area and left sealed Made bytes unchanged.

## Passing mesh and standard-wall evidence

All four meshes have zero slivers, boundary edges, non-manifold edges, pinched
vertices, and flipped-neighbour edges; each has positive volume, exactly one
connected shell, and fits the 220 × 220 × 220 mm bed:

| part | exact SHA-256 | triangles | volume | bed bounds mm |
|---|---|---:|---:|---:|
| front shell | `05f5954f…` | 1,354 | 23.13 cm³ | 108 × 123 × 11.0 |
| kickstand | `8a68cbdc…` | 316 | 8.34 cm³ | 108 × 76.5 × 9.0 |
| rear shell | `30cc8104…` | 1,252 | 32.49 cm³ | 114 × 123 × 12.7 |
| shadow reel | `eaec8678…` | 4,876 | 12.30 cm³ | 114 × 114 × 3.2 |

Standard 0.4 mm-nozzle thickness replays pass the 0.8 mm threshold:

| part | below / samples | grid mm | median mm |
|---|---:|---:|---:|
| front shell | 0 / 330,383 | 0.251 | 2.26 |
| kickstand | 0 / 151,551 | 0.197 | 4.53 |
| rear shell | 0 / 332,183 | 0.264 | 3.17 |
| shadow reel | 0 / 393,911 | 0.170 | 3.23 |

## Exact fine-wall failure

The sealed `cad/measure/thickness-rear_shell-fine.md` is not evidence for the
current rear STL: it explicitly names
`artifacts/make/r0003/product-candidate/cad/part_rear_shell.stl`, SHA-256
`323e44fd…`, while the sealed rear STL is `30cc8104…`.

An independent exact-file replay ran:

```text
check_thickness part_rear_shell.stl --nozzle 0.4 --voxel 0.16
```

It **failed**: 1 of 340,717 samples is below 0.80 mm, with thinnest reading
0.26 mm at `(-53.6, -37.9, 3.2) mm` in one 0.1 mm², one-sample region. The
bounded grid is 0.261 mm, thickness resolution is ±0.130 mm, and 1,359 more
samples are within measurement error of the threshold. The deterministic gate
therefore reports `WALL BELOW MINIMUM`; a standard coarse pass cannot override
the explicit fine failure.

## Result

**FAIL — implementation repair in Make.** Repair the rear-shell knife edge at
the cited location in source, regenerate the exact rear STEP/STL, and bind a
passing fine report to that new sealed STL before Playtest.

No slicer, support analysis, successful print, warping, layer adhesion,
physical fit, snap compliance, detent feel, strength, or cycle test was
performed or established.
