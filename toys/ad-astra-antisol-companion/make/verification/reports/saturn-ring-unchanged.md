# Saturn's ring did not move

The ring is a solid rather than a colour inlay, so `occurrence-
geometry.md`'s verdict -- *nothing outside the two Saturn pieces
changed* -- does not cover it: the ring is inside those two pieces and
a change to it would pass that test rather than fail it. This asks the
question of the ring by name.

## The ring block of `params.py`

| value | published | this build | |
|---|---:|---:|---|
| `RING_INNER_D` | 26.00 | 26.00 | unchanged |
| `RING_OUTER_D` | 30.00 | 30.00 | unchanged |
| `RING_THICKNESS` | 1.40 | 1.40 | unchanged |
| `RING_GLOBE_BITE` | 1.00 | 1.00 | unchanged |
| `RING_WEB_SECTORS` | 96 | 96 | unchanged |
| `RING_WEB_INNER_R` | 5.00 | 5.00 | unchanged |
| `RING_WEB_OVERLAP` | 0.45 | 0.45 | unchanged |
| `RING_WEB_DROP` | 0.30 | 0.30 | unchanged |
| `RING_WEB_SLOPE` | 1.08 | 1.08 | unchanged |

**Every value in the ring block is the one the published set had.**

## The built solids, occurrence by occurrence

Solid count, exact volume and bounding box, from the same two dumps
`measure/occurrence_geometry.py` writes, at 0.0001 mm3 and 1e-06 mm.

| occurrence | solids | published mm3 | this run mm3 | box drift mm | |
|---|---:|---:|---:|---:|---|
| `saturn_sol_ring_white` | 1 | 574.192167 | 574.192167 | 0.00e+00 | identical |
| `saturn_anti_ring_white` | 1 | 574.192096 | 574.192096 | 0.00e+00 | identical |
| `saturn_sol_disc_white` | 1 | 4393.336636 | 4393.336636 | 0.00e+00 | identical |
| `saturn_anti_disc_black` | 1 | 4397.326696 | 4397.326696 | 0.00e+00 | identical |
| `saturn_sol_numeral1_black` | 1 | 1.411201 | 1.411201 | 0.00e+00 | identical |
| `saturn_sol_numeral2_black` | 1 | 1.411201 | 1.411201 | 0.00e+00 | identical |
| `saturn_sol_numeral3_black` | 1 | 0.480807 | 0.480807 | 0.00e+00 | identical |
| `saturn_sol_numeral4_black` | 1 | 0.480807 | 0.480807 | 0.00e+00 | identical |
| `saturn_anti_numeral1_white` | 1 | 1.411223 | 1.411223 | 0.00e+00 | identical |
| `saturn_anti_numeral2_white` | 1 | 1.411223 | 1.411223 | 0.00e+00 | identical |
| `saturn_anti_numeral3_white` | 1 | 0.480784 | 0.480784 | 3.31e+01 | renumbered |
| `saturn_anti_numeral4_white` | 1 | 0.480784 | 0.480784 | 3.31e+01 | renumbered |

**Renumbered, not moved: `saturn_anti_numeral3_white`, `saturn_anti_numeral4_white`.**
`assemblies/product.place()` numbers the separate solids of one
colour region in whatever order the kernel hands them back, and
that order is not stable between runs. These labels came back
carrying the same SET of solids under a different assignment of
numbers: every (solid count, volume, bounding box) in the family
appears the same number of times in both runs, which is the test
applied here and the same one `measure/occurrence-geometry.md`
applies to the whole assembly. Nothing was widened to let this
pass: a family that gained, lost or moved a solid still fails.

**Every held occurrence is identical on all three measures.** The ring
is one solid on each army, at the same volume, in the same box as the
published set to 0.0001 mm3 and 1e-06 mm -- and so are the disc and the four
numeral strokes beside it. This revision changed where
the colour boundary falls on the globe and nothing else on the piece.

Measured by `measure/saturn_ring_unchanged.py`.
