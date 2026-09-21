# A seated world against the star and the trap tile

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

| world | side | globe Ømm | widest feature Ømm | in a corona well mm3 | on a star mm3 |
|---|---|---:|---:|---:|---:|
| mercury | sol | 13.78 | 33.87 | 0.000000 | 0.000000 |
| mercury | anti | 13.78 | 34.00 | 0.000000 | 0.000000 |
| mars | sol | 14.72 | 33.87 | 0.000000 | 0.000000 |
| mars | anti | 14.72 | 34.00 | 0.000000 | 0.000000 |
| venus | sol | 16.53 | 33.87 | 0.000000 | 0.000000 |
| venus | anti | 16.53 | 34.00 | 0.000000 | 0.000000 |
| earth | sol | 16.70 | 33.87 | 0.000000 | 0.000000 |
| earth | anti | 16.70 | 34.00 | 0.000000 | 0.000000 |
| neptune | sol | 21.89 | 33.87 | 0.000000 | 0.000000 |
| neptune | anti | 21.89 | 34.00 | 0.000000 | 0.000000 |
| uranus | sol | 22.02 | 33.87 | 0.000000 | 0.000000 |
| uranus | anti | 22.02 | 34.00 | 0.000000 | 0.000000 |
| saturn | sol | 26.00 | 33.87 | 0.000000 | 0.000000 |
| saturn | anti | 26.00 | 34.00 | 0.000000 | 0.000000 |
| jupiter | sol | 26.97 | 33.87 | 0.000000 | 0.000000 |
| jupiter | anti | 26.97 | 34.00 | 0.000000 | 0.000000 |

The widest feature column is the piece's own footprint, and on every
one of the sixteen it is the DISC rather than anything standing on it:
Ø33.87 on a Sol piece, whose wall flares outward to Ø34.00 and is then
rounded 0.60 at the top, and Ø34.00 on an Anti-Sol piece, whose wall
tapers inward from a Ø34.00 bed face. That includes the two ringed
worlds -- Saturn's plate is Ø30.00 and lies wholly inside its disc,
and Uranus's hoop is Ø24.02 and stands upright over its ball rather
than reaching out -- so no part of any world overhangs the 33.50 mm
tile it stands on, let alone touches anything on it.

## The trap tile has nothing left to touch

Before the owner's second pass, the tightest thing on a trap tile was
the gap between its two raised tongues: 0.70 mm of clearance to a
seated disc, at a 20.20 mm diagonal. That constraint no longer
exists, because the feature it constrained no longer exists.

What is left is a plane. The tile's highest surface is now its own
top face, and that face IS the floor the world stands on:

| | mm from the bed datum |
|---|---:|
| the trap tile's highest point | 6.0000 |
| the seat a world stands at in a well | 6.0000 |

They are the same plane. Nothing on a trap tile stands above the
surface a world's own bed face rests on, so no part of any world --
its disc, its globe, Saturn's ring or Uranus's hoop -- can reach
anything on that tile other than the floor it is standing on. The
booleans above measure that on the solids: zero shared volume on all
sixteen pieces, both armies.

## The well itself is untouched

Both numbers the well is made of are derived here from the same
constants the board and the tile are built from, rather than quoted:

| | derivation | mm |
|---|---|---:|
| the drop a trapped world takes | `POCKET_DEPTH` 6.00 - `CORONA_TILE_H` 3.00 | 3.00 |
| `CORONA_WELL_DROP`, as the set states it | -- | 3.00 |
| slip per side | (`POCKET_SIZE` 34.80 - `DISC_NOMINAL_D` 34.00) / 2 | 0.40 |

3.00 mm of drop and 0.40 mm of slip per side, exactly as before. The
tile's own height is `CORONA_TILE_H` = 3.00 and the board's pocket is
`POCKET_DEPTH` = 6.00; neither moved, and the tongues never entered
either number.

## The star's flames, unchanged

This run's part two exists to make the star's flames the only raised
flames on the board, so damaging them would be the one way to fail
it completely. Measured on the built body rather than read off the
constants:

| | value |
|---|---:|
| flames on one star | 2 |
| `FLARE_BASE_D` mm | 6.00 |
| `FLARE_HEIGHT` above field datum mm | 18.00 |
| `FLARE_TIP_R` mm | 0.75 |
| `FLARE_LEAN_DEG` from vertical | 12.0 |
| `FLARE_DIAGONAL` mm | 20.80 |
| highest point above the bed datum mm | 24.0000 |
| the same, above field datum mm | 18.0000 |
| total volume mm3 | 401.6462 |

Two bodies, reaching exactly 18.00 mm above the field.
`measure/revision-part-hashes.md` carries the same statement in
bytes: `part_den_plug.step` is byte-identical to the published set's.

## Verdict

Nothing shares volume with anything. A captured world drops into
a corona well and stands on a flat floor with nothing on it; a
winning world stands on a star without touching either of its
flames; on all eight worlds of both armies, including Jupiter,
the widest globe in the set, Saturn with its ring and Uranus with
its hoop. What a board-scale render shows at these cells is two
parts overlapping in projection, not in space.

Measured by `measure/seated_clearance.py` on the built solids.
