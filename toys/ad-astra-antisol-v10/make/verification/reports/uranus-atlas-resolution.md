# Uranus's surface and ring, against the 0.4 mm nozzle

Uranus's globe is Ø22.02 mm, so its radius is 11.010 mm and one degree of
arc is 0.1922 mm. The nozzle is 0.40 mm, which is the narrowest colour
boundary the printer can lay down and 2.08 degrees of arc here.

A degree of arc on a great circle is `pi * d / 360`, not `pi * d / 180`.
The brief's own 0.192 mm is the correct figure and agrees with this to
the third decimal. Two figures in this set's sealed archive do not, and
the last section says which.

## The polar hoods

Two `cap` regions, one at each pole, boundary at latitude 60.

| | degrees | mm | nozzle widths |
|---|---:|---:|---:|
| hood, pole to boundary (angular radius) | 30.00 | 5.76 | 14.4 |
| hood, printed extent across the surface | 60.00 | 11.53 | 28.8 |
| hood, chord across its own boundary circle | -- | 11.01 | 27.5 |
| boundary circle, circumference | -- | 34.59 | 86.5 |
| bare globe between the two hoods | 120.00 | 23.06 | 57.6 |
| colour boundary transition, as drawn | 0.00 | 0.00 | 0.0 |
| colour boundary transition, as printed | 2.08 | 0.40 | 1.0 |
| inlay depth `RELIEF_DEPTH` | -- | 1.20 | 3.0 |

**The hood's printed extent is 11.53 mm across the surface**, 29 nozzle
widths, on a globe 22.02 mm across. It is not a feature the nozzle has
any difficulty with; nothing about it is near the limit.

**The boundary transition is the one number that is at the limit, and
it is at the limit by construction rather than by choice.** A flush
colour inlay has no transition at all: the boundary is a hard edge
between two filaments, drawn as an exact circle of latitude. What the
printer actually lays down there is one bead, 0.40 mm, 2.08 degrees of
arc on this globe. So the softness the reference shows -- a brightening
that fades out rather than stopping -- **cannot be reproduced**, and
lowering the contrast is the available substitute rather than a
preference. `measure/uranus-tone-separation.md` is that substitute,
measured.

No lobed rim. The Earth correction's lesson about lids was about a small
bright cap read edge-on against a dark globe; this is a wide soft
brightening read face-on, and `ref/uranus-sol.png` shows no rim
structure at all. A lobe on this boundary would be a feature the
reference does not carry.

## The ring

| | mm | nozzle widths |
|---|---:|---:|
| projection past the globe, per side | 1.00 | 2.5 |
| thickness through the plate | 1.00 | 2.5 |
| outer diameter | 24.02 | 60.0 |
| how far it bites into the globe before the globe is cut out | 0.80 | 2.0 |
| the foot's reach past the hoop at the disc top | 1.30 | 3.2 |
| the foot's rise before it is inside the globe | 1.50 | 3.8 |

The thinnest section anywhere on the ring is its own 1.00 mm plate,
2.5 nozzle widths and 0.20 mm over the 0.80 mm minimum wall this set
holds. `measure/thickness-world_uranus_sol.md` measures the whole part.

Thirteen real rings were considered and refused. One degree of arc is
0.192 mm here and the whole Uranian ring system spans about 1.8 planet
radii; the widest ring, epsilon, is about 100 km on a planet 51118 km
across, which is 0.0431 mm at this scale -- a four-hundredth of a nozzle.
Printed at the width the printer can lay down they would be forty times
too fat and read as grit. **The ring is one solid hoop.**

## The filaments this piece loads

| role | filament |
|---|---|
| `disc` | `white` |
| `numeral` | `black` |
| `globe` | `cyan` |
| `hood_north` | `beige` |
| `hood_south` | `beige` |
| `ring` | `cyan` |

**4 filaments on the Sol piece and 4 on the Anti-Sol piece**: `beige`, `black`, `cyan`, `white`, and
`beige`, `black`, `cyan`, `white`. The two differ only in which of `white` and `black` is the disc and
which is the numeral, which is the set's own ownership cue. Every one is
already loaded for this set: the hood's `beige` is Earth's dryland and
Jupiter's and Saturn's zones, and the ring's `white` is Saturn's ring.
**This correction loads no new spool.**

Two counts are in use across this set's documents and they are not the
same count. The 4 above is every spool this PIECE loads, disc and
numeral included. The tally the design contract and the READMEs keep --
`Earth, Jupiter and Saturn four; Mercury, Mars, Venus, Neptune and
Uranus three` -- counts the globe and its markings only, and leaves out
the disc and the numeral because every world in the set shares those.
By that count Uranus is three: `cyan`, `beige` and `white`, where before
this correction it was two.

## Where this set's own numbers disagree with each other

The brief asks for every cross-world figure in it to be checked against
that world's own report rather than taken on trust. Done, and one
disagreement is real and is in the sealed archive rather than in the
brief.

| claim | where | measured | verdict |
|---|---|---|---|
| Saturn's ring projects 2.00 mm per side | the brief | `RING_OUTER_D` 30.00 less Ø26.00, halved: 2.00 mm | agrees |
| Saturn is Ø30.00 and the widest world | the brief | `RING_OUTER_D` 30.00 against Uranus's 24.02 | agrees |
| Neptune's piece is 24.89 mm tall | the brief | 24.89 mm | agrees |
| Saturn's piece is 29.00 mm tall | the brief | 29.00 mm | agrees |
| Uranus's piece was 25.02 mm tall | the brief | 25.02 mm | agrees |
| Uranus's ring will reach about 25.91 mm | the brief | 25.98 mm | **0.07 mm low**; see `measure/uranus-ring.md` |
| Saturn's bands are 3.63 to 7.26 mm | `measure/neptune-atlas-resolution.md` | Saturn's own report measures the narrowest at **1.82 mm** | **wrong by a factor of two** |

`measure/neptune-atlas-resolution.md` went into the sealed archive
saying Saturn's band system runs 3.63 to 7.26 mm. Saturn's own
`measure/saturn-atlas-resolution.md` measures the narrowest band, the
Equatorial Band, at 8.0 degrees and **1.82 mm**. 3.63 is exactly twice
1.82: the Neptune run caught the factor of two in its own width figure
and then repeated the owner's companion figures for Saturn and Jupiter
without recomputing them. The same line's Jupiter figures, 2.35 to
6.12 mm, carry the same doubling.

The same two figures are quoted in the product README's Neptune
paragraph, which this revision rewrites, and the corrected ones go in
with the rewrite.

### Older per-world reports still describe Uranus's band

`measure/jupiter-atlas-resolution.md`, `measure/jupiter-tone-separation.md`
and `measure/venus-tone-separation.md` each mention Uranus's `white`
band or count it as a two-filament world. Those are the sealed reports
of the Jupiter and Venus corrections and they were true when they were
written; this set's convention is to leave each run's own record as it
stands rather than back-date it, which is why the design contract's
items 19, 20 and 21 also keep their own filament tallies. The tally as
it now stands is in the section above and in `README.md`. Nothing in
those three reports is used as evidence by this run.

**Nothing in this run depends on either figure** -- no marking on this
piece is sized against another world's bands -- and the sealed Neptune
report is finished work that this correction does not reopen. It is
recorded here because this is the last run of the chain and the brief
asked for anything left wrong to be said in one place.

## What else was considered and refused

- **A second, brighter core inside each hood.** The reference's lighter
  region is soft-edged and single-toned; a core would need a fourth
  surface filament and would reintroduce exactly the structure this
  correction is removing.
- **Banding.** `ref/uranus-sol.png` shows none, and a band on this
  planet is the feature this correction exists to take off.
- **Moons.** Not on the reference, not printable at this scale, and not
  a surface.
- **Shepherd gaps and named ringlets.** Refused on the arithmetic above.
- **A pale blue globe.** `cyan` #00FFFF is a saturated neon and the
  reference is a pale desaturated ice blue. There is no pale blue in the
  13 filaments this set stocks, so the gap cannot be closed inside two
  printed parts. Acquiring one would reach the belt, the corona flames
  and the Anti-Sol flames, which is well outside this correction; it is
  recorded as a recommendation for a future revision instead.

Measured by `measure/uranus_atlas_resolution.py` on the built solids and
on `params.py`.
