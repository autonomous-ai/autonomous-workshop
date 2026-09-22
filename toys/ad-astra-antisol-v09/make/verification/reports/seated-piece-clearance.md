# A seated world against the star and the corona tongues

The state sheet shows captured worlds standing in corona wells and,
in the endgame, a world walking onto a star. At board scale a flame
and a globe overlap in projection whether or not they touch, so this
asks the solids instead of the picture.

Each world is placed at the exact height the assembly gives it --
6.00 mm in a corona well, 11.20 mm on a star, both measured from the
bed datum -- beside the exact corona tile and star plug, and the
volume the two share is measured. Anything above 1e-06 mm3 is a real
interpenetration; the parts are meant to stand beside each other and
never inside each other.

| world | globe Ømm | in a corona well mm3 | on a star mm3 |
|---|---|---|---|
| mercury | 13.78 | 0.000000 | 0.000000 |
| mars | 14.72 | 0.000000 | 0.000000 |
| venus | 16.53 | 0.000000 | 0.000000 |
| earth | 16.70 | 0.000000 | 0.000000 |
| neptune | 21.89 | 0.000000 | 0.000000 |
| uranus | 22.02 | 0.000000 | 0.000000 |
| saturn | 26.00 | 0.000000 | 0.000000 |
| jupiter | 26.97 | 0.000000 | 0.000000 |

## Verdict

Nothing shares volume with anything. A captured world drops into
a corona well without touching either of that tile's raised
tongues, and a winning world stands on a star without touching
either of its flames, on all eight worlds -- including Jupiter,
the widest globe in the set. What a board-scale render shows at
these cells is two parts overlapping in projection, not in space.

Measured by `measure/seated_clearance.py` on the built solids.
