# `MARKINGS[planet]` against `markings_for(planet, side)`

Every marking lookup in `parts/world.py` now goes through
`markings_for(planet, side)`. This is the check that the change is a
refactor everywhere it is supposed to be one: for the six worlds not
named in `MAP_MIRRORED_WORLDS`, on both sides, and for the Sol piece
of the two that are, the function must return exactly what indexing
`MARKINGS` returned before.

`identical object` is the strongest form of that answer and the one
the function actually gives: in those fourteen cases it returns the
table's own list rather than a copy of it, so there is nothing that
could drift.

| planet | side | must be unchanged | equal | identical object | markings | region specs | ring vertices |
|---|---|---|---|---|---:|---:|---:|
| mercury | sol | yes | yes | yes | 3 | 3 | 153 |
| mercury | anti | no -- mirrored | no, as required | n/a | 3 | 3 | 153 |
| mars | sol | yes | yes | yes | 2 | 3 | 110 |
| mars | anti | yes | yes | yes | 2 | 3 | 110 |
| venus | sol | yes | yes | yes | 2 | 2 | 99 |
| venus | anti | no -- mirrored | no, as required | n/a | 2 | 2 | 99 |
| earth | sol | yes | yes | yes | 3 | 4 | 191 |
| earth | anti | yes | yes | yes | 3 | 4 | 191 |
| neptune | sol | yes | yes | yes | 2 | 4 | 40 |
| neptune | anti | yes | yes | yes | 2 | 4 | 40 |
| uranus | sol | yes | yes | yes | 0 | 0 | 0 |
| uranus | anti | yes | yes | yes | 0 | 0 | 0 |
| saturn | sol | yes | yes | yes | 3 | 6 | 264 |
| saturn | anti | yes | yes | yes | 3 | 6 | 264 |
| jupiter | sol | yes | yes | yes | 4 | 13 | 295 |
| jupiter | anti | yes | yes | yes | 4 | 13 | 295 |

## The shape of what comes back

A mirrored entry has to be the same structure with different
longitudes in it -- same number of markings in the same order, the
same keys, the same filaments, the same subtractions, and every ring
the same length. A transform that dropped a marking or reordered the
split would pass a longitude check and fail the piece.

| planet | markings in order | filaments | subtractions | ring lengths |
|---|---|---|---|---|
| mercury sol | plains, caloris_rim, caloris_floor | cocoa_brown, cocoa_brown, white | (); ('caloris_floor',); () | 21, 19, 16, 14, 20, 15, 12, 23, 13 |
| mercury anti | plains, caloris_rim, caloris_floor | cocoa_brown, cocoa_brown, white | (); ('caloris_floor',); () | 21, 19, 16, 14, 20, 15, 12, 23, 13 |
| venus sol | highland, lowland | beige, cocoa_brown | (); ('highland',) | 14, 15, 14, 6, 6, 6, 6, 8, 9, 8, 7 |
| venus anti | highland, lowland | beige, cocoa_brown | (); ('highland',) | 14, 15, 14, 6, 6, 6, 6, 8, 9, 8, 7 |

## Uranus's empty entry

`MARKINGS["uranus"]` is `[]`, the one world in the set with a bare
globe. `markings_for` returns that same empty list on both sides, by
the same route every other unmirrored case takes -- there is no
`if not entries` anywhere in the function, and no branch that names
Uranus. Checked here.

## Verdict

All sixteen cases behave as they must. Fourteen return the
untouched table itself; the two mirrored ones return the same
structure with reflected longitudes in it. The refactor moved no
marking on any world it was not asked to move.

Measured by `measure/markings_refactor.py`.
