# Uranus's ring, measured on the solid

Redone in 3D on the exact body `parts/world.py` builds. The brief's own
table treated the rim as a plain cylindrical band standing straight up
and ignored the 7.77 degree lean; both are reported below and where they
differ the measured figure is the one used.

## What it is

| | value | |
|---|---:|---|
| globe diameter | Ø22.02 mm | unchanged |
| ring inner diameter | Ø22.02 mm | tangent to the equator |
| ring outer diameter | Ø24.02 mm | |
| projection per side | 1.00 mm | against Saturn's 2.00 |
| ring thickness | 1.00 mm | against Saturn's 1.40 |
| obliquity | 97.77 deg | so the ring plane stands 7.77 deg past vertical |

Saturn's ring is a near-horizontal plate at 26.73 degrees and Uranus's is
a hoop on edge. **The two are not confusable in silhouette even before
size enters it**: one is a brim projecting sideways past the globe, the
other a band standing up over it. Size then separates them again --
Ø30.00 against Ø24.02.

## How far it reaches

| | X mm | Y mm | Z mm |
|---|---|---|---|
| ring, sol | -1.73 to 2.12 | -12.01 to 12.01 | 5.00 to 25.98 |
| ring, anti | -2.12 to 1.73 | -12.01 to 12.01 | 5.00 to 25.98 |
| whole piece, sol | -16.94 to 16.94 | -16.94 to 16.94 | 0.00 to 25.98 |
| whole piece, anti | -17.00 to 17.00 | -17.00 to 17.00 | 0.00 to 25.98 |
| disc | -17.00 to 17.00 | -17.00 to 17.00 | 0.00 to 5.00 |

**In plan the ring adds nothing.** Its greatest reach from the axis is
12.01 mm and the disc's is 17.00, so the piece's footprint is the disc's,
exactly as it was before this correction. In height it adds 0.96 mm:
the globe's crown was 25.02 mm and the hoop's is 25.98. The brief
predicted 25.91, which is where the hoop's mid-plane reaches; the crown
is the outer corner of a 1.00 mm band leaning 7.77 degrees and stands
0.07 mm above that. The measured figure is the one used.

## How steep it is

The 45 degree gate, run facet by facet over the finished ring at 0.02 mm
of chord. A vertical wall is 0 degrees and a flat ceiling is 90.

| army | steepest downward-facing | where | area over the gate mm2 |
|---|---:|---|---:|
| sol | 44.3 deg | on the hoop at Z 5.68, plan radius 8.66 | 0.0000 |
| anti | 44.3 deg | on the hoop at Z 5.68, plan radius 8.66 | 0.0000 |

Excluded by name: 52.18 mm2, on both armies alike -- the flat footprint
the two feet stand on, lying exactly on the disc's top face at Z 5.00,
and the hoop's inner boundary, which is the globe's own sphere at
radius 11.01 from the globe centre and is what the ring is seated
against the whole way round. Both point downward somewhere and neither
is a surface once the part is fused: there is solid under every square
millimetre of both. `check_overhang` measures the fused part and never
sees them.

**The 45 degree gate passes on the ring itself**, and it passes on the
whole printed part: `measure/overhang-world_uranus_sol.md` and its
Anti-Sol twin report 0 unsupported regions, 0 bridges and 0 samples
needing support over the whole 35.1 cm2 of surface.

### Why it needed a foot

`_ring_body` cuts everything below the disc top away, and an upright
hoop meets that flat cut on the steep part of its own curve. Measured in
closed form on the real hoop:

| | measured in 3D | the brief's own table |
|---|---|---|
| rim overhang where it leaves the disc top | 48.6 deg | 48.6 deg |
| height where the rim first clears the gate | Z 5.52 mm | not given |
| plan radius there | 8.49 mm | not given |

The brief's figure is right to a tenth of a degree, and that is not
luck: the rim's downward slope at the cut works out to
`(centre height - cut height) / outer radius` whichever way the ring
leans, because the lean enters the height and the normal in the same
proportion and cancels. Two more figures fall out of the same algebra
and neither is in the brief: the rim clears the gate at
`Z = centre - R cos(45)` = 5.52 mm, and its plan radius there is
`R sin(45)` = 8.49 mm. So the offending strip is 0.52 mm tall.

Growing the ring until the cut lands somewhere shallower is the
resolution the brief ruled out -- it takes the projection back to
Saturn's own 2.00 mm. The junction is wedged instead, at
`RING_WEB_SLOPE` = 1.08, which is 47.2 degrees from horizontal and
42.8 from vertical -- the angle this set already trusts under Saturn's
ring for exactly this problem. The wedge stands 1.30 mm proud of the
hoop where it leaves the disc and is gone 1.50 mm further up, inside the
globe, so it adds a small gusset at each of the two feet and nothing
anywhere else. The projection stayed at 1.00 mm.

## The ladder

| | diameter | |
|---|---:|---|
| Saturn, ring included | Ø30.00 mm | the widest world in the set |
| Uranus, ring included | Ø24.02 mm | |
| Jupiter, the widest globe | Ø26.97 mm | |

`LADDER_CONSTANT` is 13.785 and `LADDER_EXPONENT` 0.2, both unmoved:
every globe diameter in `params.PLANETS` still satisfies
`13.785 * (D / 4879) ** 0.2` to the hundredth of a millimetre it is
written at.

| planet | d km | ladder mm | sealed mm | |
|---|---:|---:|---:|---|
| mercury | 4879 | 13.79 | 13.78 | matches |
| mars | 6779 | 14.72 | 14.72 | matches |
| venus | 12104 | 16.53 | 16.53 | matches |
| earth | 12742 | 16.70 | 16.70 | matches |
| neptune | 49244 | 21.89 | 21.89 | matches |
| uranus | 50724 | 22.02 | 22.02 | matches |
| saturn | 116460 | 26.00 | 26.00 | matches |
| jupiter | 139820 | 26.97 | 26.97 | matches |

## The heights, against rank

| rank | planet | piece height mm | what sets it |
|---|---|---:|---|
| 1 | mercury | 16.78 | the globe's crown |
| 2 | mars | 17.72 | the globe's crown |
| 3 | venus | 19.53 | the globe's crown |
| 4 | earth | 19.70 | the globe's crown |
| 5 | neptune | 24.89 | the globe's crown |
| 6 | uranus | 25.98 | the ring's crown |
| 7 | saturn | 29.00 | the globe's crown; the ring is lower |
| 8 | jupiter | 29.97 | the globe's crown |

**The piece heights still climb with rank, all eight of them.** The
ring takes Uranus from 25.02 mm to 25.98, which is past Neptune's 24.89
and still well under Saturn's 29.00.

## What it can touch

Every clearance is measured as shared volume between the exact placed
solids; anything over 1e-06 mm3 is a real interpenetration.

| what | measured | |
|---|---|---|
| the Ø34.40 tray socket | ring reaches 12.01 mm from the axis | clear by 5.19 mm |
| the corona well, sol | 0.000000 mm3 shared | clear |
| the den flange and its flames, sol | 0.000000 mm3 shared | clear |
| the corona well, anti | 0.000000 mm3 shared | clear |
| the den flange and its flames, anti | 0.000000 mm3 shared | clear |
| the 18.00 mm flares, worst neighbouring cell | 0.000000 mm3 shared | clear |

**The flares are the one thing in the set that reaches the ring's
height and they are checked explicitly.** A flare's tip stands at
Z 27.00 in the board frame and a Uranus piece on a neighbouring cell
carries its hoop to Z 31.98, so the two share 15.80 mm of height --
from Z 11.20 up to the flare's own tip. They do not share any of it in
plan: the flare bases sit inside a
Ø20.80 diagonal on the den's own flange, the ring never leaves the
disc's own Ø34.00 footprint, and the cells are 36.00 mm apart. Every one
of the eight cells around each den was placed and measured, on both
armies, and the largest shared volume anywhere was 0.000000 mm3.

## The mirror

| | Sol | Anti-Sol | |
|---|---:|---:|---|
| ring volume mm3 | 54.8305 | 54.8305 | mirrored |
| ring X reach mm | 2.1191 | 2.1191 | mirrored |
| ring Y reach mm | 12.0100 | 12.0100 | mirrored |
| ring crown Z mm | 25.9773 | 25.9773 | mirrored |

Sol leans toward +X and Anti-Sol toward -X, so the Sol ring's greatest
+X reach is the Anti-Sol ring's greatest -X reach; that is the row above
and it is what a mirror means here. `measure/uranus-mirror.md` carries
the same test over every body of both pieces.

## The colour, reversed by the owner and measured again

This ring prints in `white`.

It has printed in two filaments across this chain and the history is
worth having in one place, because the second change reverses the
first.

The Uranus edition took `white` first -- the tone Saturn's ring already
wears, because in this set rings are white -- and then moved off it on
a measured reading. An independent reviewer, shown the board cold and
not told what the set was, named both Uranus pieces as tennis balls,
twice, and gave the mechanism in his own words: 'a bold white curved
line arcing down one side of a saturated-colour ball, and a large pale
panel on the opposite side'. `gray` was tried and measured WORSE in
use -- quieter as a number, a more convincing seam to the eye, because
a tennis seam is a dark curve on a bright ball -- so the ring was given
the globe's own `cyan` and stopped being a marking at all.

**The owner has reversed that, and the ring is `white` again.** The
appearance of the toy is his to decide and an argument from a reference
photograph does not outrank him. The geometry did not move by so much
as a micron: this is one existing body changing spools.

Read the reviewer's mechanism again, because it has two halves and this
revision removes one of them. The pale panel was the polar hood, and
there is no hood on this world any more -- there is no marking on it at
all. Whether a white hoop ALONE on a bare `cyan` ball still reads as a
seam is a different question from the one that reviewer answered, and
it is not assumed here in either direction: it is put to this build's
blind review as its own question, unprimed, and whatever comes back is
recorded in `snap/SIGNATURE-REVIEW.json` beside the number.

The number is in `measure/uranus-ring-tone.md`, measured the same way:
one piece built once and rendered twice at one camera with only the
ring repainted, so the pixels that move are the hoop's and nothing
else moves at all.

**What the reversal gains.** Both ringed worlds now print their ring in
`white`, which is what `RING_COLOUR` holds as this set's default. The
'rings are white' rule holds without a footnote for the first time, and
the two rings are the same KIND of part again: a separate white piece
on each, told apart by how it stands rather than by what it is made of.

**What it costs.** Uranus's piece drops from four spools to three and
its globe-and-what-stands-on-it count from three to two, because the
`beige` hoods went with the same decision. The ring is now the loudest
single boundary on the piece, on a world whose reference is the
quietest in the folder, and it is the only thing on the globe at all.
Saturn's ring is untouched and still prints `white`.

## What was considered and left out

No moons, no storms, no banding, no shepherd gaps and no individual
named ringlets. Uranus really has thirteen rings; at Ø22.02 mm one
degree of arc is 0.192 mm and the whole ring system would be grit under
a 0.4 mm nozzle. The ring is one solid hoop.

## Verdict

The gate passes on the ring and on the whole part, the ladder is
unmoved, the heights still climb with rank, nothing collides with
anything, and the two pieces are mirrors.

Measured by `measure/uranus_ring.py` on the built solids.
