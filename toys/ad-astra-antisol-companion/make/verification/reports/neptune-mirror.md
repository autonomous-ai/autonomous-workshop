# The two Neptune pieces against each other

Measured on the exact colour bodies `parts/world.py` builds, at
0.0001 mm3. The two armies share one marking description and lean the
opposite way under it; this is what that produces.

## Body for body

| role | filament | solids Sol / Anti | volume Sol mm3 | volume Anti mm3 | difference mm3 | |
|---|---|---:|---:|---:|---:|---|
| `disc` | `white` | 1 / 1 | 4389.3147 | 4393.3048 | +3.9901 | the draft, by design |
| `numeral` | `black` | 2 / 2 | 7.8059 | 7.8059 | -0.0000 | identical |
| `globe` | `blue` | 1 / 1 | 5419.5122 | 5419.5122 | +0.0001 | identical |
| `spot` | `dark_gray` | 1 / 1 | 10.5113 | 10.5113 | +0.0000 | identical |
| `bands` | `white` | 3 / 3 | 10.8043 | 10.8043 | +0.0000 | identical |
| `companion` | `white` | 1 / 1 | 1.5059 | 1.5059 | +0.0000 | identical |

## The white bodies, one by one

Neptune carries 2 white markings on this revision: `bands`, `companion`. The split
order is not the table order, so the two armies' lists are paired
by MATCHING rather than by position: every Sol body is paired with
the Anti-Sol body nearest it in volume, and a pair inside 0.0001 mm3
is the same body on both armies.

### `bands`

| | volume Sol mm3 | volume Anti mm3 | |
|---:|---:|---:|---|
| 1 | 1.6341 | 1.6341 | identical |
| 2 | 4.4625 | 4.4625 | identical |
| 3 | 4.7077 | 4.7077 | identical |

**3 of the 3 `bands` bodies come out at exactly the same volume
on both pieces**, and `bands` as a whole differs by +0.0000 mm3
between the two armies.

### `companion`

| | volume Sol mm3 | volume Anti mm3 | |
|---:|---:|---:|---|
| 1 | 1.5059 | 1.5059 | identical |

**1 of the 1 `companion` bodies come out at exactly the same volume
on both pieces**, and `companion` as a whole differs by +0.0000 mm3
between the two armies.

A closed latitude band cannot be clipped differently on the two
armies. It is a surface of revolution about the globe's own polar
axis, so mirroring the piece in X maps each band onto ITSELF rather
than onto some other longitude of it, and the disc's cut takes the
same arc out of it on both armies. The three bands pair exactly.

The companion CAN be, and this is the check that it is not.
`parts/world.py` cuts the globe level with the disc's top face, and
that plane sits in a different half-space of the PLANET's frame on
the two armies, so a short marking that reaches far enough south is
clipped by the disc on one piece and clears it on the other. That
is what happened to the two deepest of the eight cloud streaks an
earlier build of this globe drew, `s1` at latitude -52 and `s2` at
-37, and cost that build 12.98 mm3 of white on one army. The
disc's cut is a plane, so in the PLANET's frame it is a great
circle tilted by the obliquity rather than a parallel: a marking
survives it or not by longitude as well as by latitude. So it is
measured on the companion's own ring, vertex by vertex, on both
armies -- the lowest the ring reaches in the PIECE's frame against
the -54.8 degrees the cut sits at there.

| army | companion's lowest ring vertex, piece frame | cut at | clears by |
|---|---:|---:|---:|
| Sol | -41.1 | -54.8 | 13.7 degrees |
| Anti-Sol | -18.7 | -54.8 | 36.1 degrees |

The table above is the measurement of the result rather than the
argument for it.

## The dark spot against the build this revision corrects

The owner's standing instruction across two revisions is that the
dark spot does not move, and this revision does not move it: its
ring, its latitude, its longitude, its half-axes, its 40 vertices
and its `dark_gray` filament are byte-identical in the source --
`measure/source-diff.md` is the whole difference and the spot is
not in it -- and `measure/neptune-facing.md` reproduces its
archived dot products at every frame.

Its BODY is nonetheless smaller than the archive's, and by more
than the companion's own area. The companion has to stand one
nozzle width of bare globe clear of the spot -- an independent
reader of the touching version called the pair a notched
figure-eight -- so the spot is cut back to a KEEP-OUT, the
companion's oval grown by 2.30 degrees of arc, which is never drawn
and never printed. The bay that leaves in the spot's southern rim
is a real change to the Great Dark Spot and this section is where
it is disclosed rather than a check quietly retargeted.

The archived build measured the `spot` body at **11.9319 mm3** on both
armies (`make/verification/reports/neptune-mirror.md` in
`revision-source.zip`).

| army | archived mm3 | this run mm3 | difference mm3 |
|---|---:|---:|---:|
| Sol | 11.9319 | 10.5113 | -1.4206 |
| Anti-Sol | 11.9319 | 10.5113 | -1.4206 |

Two measurements decide whether that difference is the keep-out
or a fault, and both are taken on the region solids rather than on
the split bodies:

| quantity | mm3 |
|---|---:|
| the spot's own region, BEFORE the companion is subtracted from it | 11.9319 |
| the archive's sealed `spot` body | 11.9319 |
| the companion's own region, which is what is PRINTED white | 1.5059 |
| where the spot and the companion's KEEP-OUT overlap | 1.4206 |
| what the `spot` body actually lost | 1.4206 |

**The spot's own region reproduces the archived figure to a
ten-thousandth of a cubic millimetre: the spot did not move.**
And what the body lost is that overlap, to the same tolerance:
every cubic millimetre of the difference is the bare globe the
companion needs around it. Nothing else came off the spot.

Both armies lose the same amount, which is the other half of the
statement: the companion is drawn once and the two pieces are the
same description mirrored.

## Verdict

The two pieces carry the same roles, the same filaments and the same
number of solids in every role. 4 of the 4 white bodies and the
dark spot on one army is identical in volume to the same body on
the other, to 0.0001 mm3.
**The disc is the only difference between them**, and it is the
ownership cue: a Sol disc flares as it rises and an Anti-Sol disc
tapers, which costs exactly 3.99 mm3.
