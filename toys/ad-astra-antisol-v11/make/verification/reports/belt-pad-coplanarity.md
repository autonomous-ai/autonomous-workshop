# The belt tile's landing face, measured

A world stands on a Ø34.00 disc and a belt tile is 33.50 mm square, so
the disc overhangs the tile on every side and whatever the tile
presents at the field datum is what carries it. Three things decide
whether it can rock: whether anything stands proud of the datum,
how much face lies exactly in it, and whether that face is one plane
or several heights. All three are measured on the exact solid
`parts/belt.py` builds.

| measure | value |
|---|---|
| field datum, the tile's own top | Z = 6.00 mm |
| the built tile's highest point | Z = 6.0000 mm |
| standing proud of the datum | 0.0000 mm |
| the smooth landing pad | 530.93 mm2, Ø26.00 |
| the nominal Ø26.00 pad, for comparison | 530.93 mm2 |
| rubble crests reaching the datum exactly | 4 |
| each of them | 0.5032, 0.5032, 0.5032, 0.5032 mm2 |
| **total coplanar contact** | **532.9 mm2** |
| crests within 0.10 mm below the datum, touching nothing | 4, at Z = 5.978 |
| rubble floor, below the datum | Z = 4.00 mm |

Every contact face is at Z = 6.0000 exactly, so the landing pad and the
4 crests that reach it are **one plane, not 5 heights**: a seated
disc meets all of them at once and cannot rock on any of them. The
4 crests that stop 0.022 mm short are clearance rather than contact
and are listed so nobody has to wonder whether they were counted.

Nothing stands above the field datum. The tile is trimmed to its
own envelope after the rubble is fused, so every crest that would
have risen past the datum is cut off level with it.

Measured by `measure/belt_pad_coplanarity.py` on the exact solid
`parts/belt.py` builds.
