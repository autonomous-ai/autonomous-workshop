# Canonical renders against the source archive's

Pixels whose largest channel difference exceeds 8 of 255, against the
image of the same name in `revision-source.zip`. Box is (x0, y0, x1, y1).

| render | size | changed px | changed % | box of change |
|---|---|---:|---:|---|
| `iso.png` | 2400x1056 | 213 | 0.0084 | (365, 330, 1521, 879) |
| `signature.png` | 3600x800 | 183 | 0.0064 | (208, 167, 3390, 617) |
| `rank-ladder-sol.png` | 2544x324 | 0 | 0.0000 | none |
| `rank-ladder-anti.png` | 2544x324 | 35 | 0.0042 | (1038, 196, 1043, 203) |
| `worlds/neptune-sol-hero.png` | 900x900 | 286 | 0.0353 | (294, 542, 332, 566) |
| `worlds/neptune-anti-hero.png` | 900x900 | 565 | 0.0698 | (406, 523, 445, 542) |
| `worlds/neptune-sol-spot.png` | 900x900 | 636 | 0.0785 | (381, 554, 421, 579) |
| `worlds/neptune-anti-spot.png` | 900x900 | 690 | 0.0852 | (516, 501, 555, 527) |
| `worlds/neptune-sol-opposite.png` | 900x900 | 0 | 0.0000 | none |
| `worlds/neptune-anti-opposite.png` | 900x900 | 0 | 0.0000 | none |
| `worlds/neptune-sol-polar.png` | 900x900 | 0 | 0.0000 | none |
| `worlds/neptune-anti-polar.png` | 900x900 | 0 | 0.0000 | none |
| `worlds/neptune-pair-hero.png` | 900x900 | 291 | 0.0359 | (191, 404, 614, 607) |
| `worlds/neptune-pair-spot.png` | 900x900 | 477 | 0.0589 | (331, 496, 599, 560) |
| `worlds/neptune-pair-opposite.png` | 900x900 | 0 | 0.0000 | none |
| `worlds/neptune-earth-hero.png` | 900x900 | 98 | 0.0121 | (191, 559, 212, 573) |
| `worlds/neptune-earth-hero-anti.png` | 900x900 | 192 | 0.0237 | (256, 547, 278, 558) |
| `worlds/uranus-neptune-hero.png` | 900x900 | 95 | 0.0117 | (528, 414, 549, 427) |
| `worlds/uranus-neptune-hero-anti.png` | 900x900 | 194 | 0.0240 | (592, 403, 614, 414) |

Magenta marks every changed pixel in `measure/render-diff/<name>`.

## Reading the change

Clustered (connected changed pixels, 3 px dilation), every cluster whose
difference exceeds 60 of 255 lies on a Neptune globe, at the companion
oval's place just south of the dark spot -- except scattered specks of 1 to
25 pixels along the silhouettes of the thin flame and tongue cones by the
stars and corona wells. Those specks repeat identically in all three panels
of `signature.png`, i.e. on geometry that is the same in every state, and
the parts that carry them (`part_den_plug`, `part_corona_cell`) rebuild to
the source's exact B-rep identity (`measure/quick-fix-carry.md`). The
source archive's renders were made on a different platform (its round state
records `darwin`); these are rasterization differences of the same shapes
at silhouette edges, not geometry. The Neptune opposite-face and polar
frames, which cannot see the companion, and the Sol rank ladder, where it
is behind the limb, are pixel-identical.
