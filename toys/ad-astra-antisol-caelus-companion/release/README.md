# Antisol Caelus Companion

Jungle Chess played with the solar system, in two armies of eight worlds.

A planet's size on the board is the fifth root of its real measured diameter,
so rank is something you can see rather than something you have to learn:
Mercury is the smallest world in play and Jupiter the largest. The traditional
rules are followed exactly as written. Matter faces antimatter -- one army's
worlds lean their poles one way and the other army's lean the other, by each
planet's own true axial tilt, and the bases say the same thing again in white
against black.

Four of the eight worlds wear a real map: Earth its own coastlines, Mars its
own dark continents, Mercury its own smooth plains with the Caloris basin in
them, and Venus -- alone in the set -- a surface no eye has ever seen. Three
more wear their weather, and one wears nothing at all.

## What this edition changes

**Neptune's Great Dark Spot has its bright companion cloud back, on both
Neptune pieces, and nothing else in the box changes.**

The companion is one small white oval, 10 by 5 degrees of arc -- about 1.9 by
1.0 mm on Neptune's 21.89 mm globe, roughly a third of the dark spot's width
and the same two-to-one shape -- sitting just below the dark spot with a strip
of bare blue between them. It prints from the same white spool as Neptune's
three cloud bands, so the piece still uses the filaments it used before.

**Where it sits, and why that is not quite where it was asked for.** The
request was "about 8 degrees of latitude south of the spot's centre, at the
same longitude". Two measurements moved it.

- The dark spot is 14 degrees tall, so its lower rim is already 7 degrees
  below its centre. A 5-degree-tall cloud centred 8 degrees down would overlap
  the spot and come out as a crescent with horns thinner than the printer's
  0.4 mm nozzle -- which is the narrowest mark this set allows anywhere.
- Directly below the spot's centre, the lean of the Sol army's piece carries
  the cloud down onto the collar the globe stands on. The first version of
  this edition put it there, and an independent reader of the pictures saw
  only a sliver of it above the collar on that piece. That was a real fault,
  so it was moved.

It now sits 11.5 degrees south of the spot's centre and 10 degrees toward the
spot's western end -- still underneath the spot, which is 28 degrees wide --
fully visible on both pieces, with 0.53 to 0.59 mm of bare blue between it and
the spot. The size, the oval shape, the white and the "just south of the spot"
relationship are exactly as asked; the place moved by the least amount that
clears both problems. `cad/measure/neptune-companion.md` measures all of it on
the finished solids.

**Nothing else moved, and that is measured, not asserted.** No printed solid in
the set changes shape: every one of the 24 printed parts rebuilds to exactly
the same shape as the last edition, because the companion is a colour inlay
inside the globe, not a bump on it. On both Neptune pieces the dark spot, the
three bands, the base and the numeral keep their exact volume and bounding box,
and the globe gives up exactly the companion's volume. The assembled set goes
from 220 pieces to 222: the two companions and nothing else. Every picture of
the set was compared pixel by pixel with the last edition's
(`cad/measure/render-diff.md`), and the only real change anywhere is the
companion.

**One thing the pictures do that the piece does not.** The renderer lights
every scene from above, so Neptune's southern half is in shade in the level
close-ups, and white and dark gray both come out as mid greys there. The two
frames `cad/snap/worlds/neptune-sol-companion-lit.png` and
`neptune-anti-companion-lit.png` turn the exact piece toward the light, the way
you would tilt it in your hand, and show the companion white.

## The previous edition: Uranus goes bare

Uranus is the world this edition changes, and the change is unusual enough to
say plainly at the top: **nothing was broken. The owner did not like the look
of the two pale discs on it, so they are gone.**

Uranus now carries no surface marking of any kind. No hood, no cap, no band,
no spot, nothing in a quieter tone. Its globe is one undivided cyan sphere with
a single white hoop standing upright over it, and it is the only bare world in
the box.

**Why a bare world is the right answer on this one.** The reference this set is
drawn from is an almost featureless sphere -- pale, very nearly uniform, one
faint soft-edged lighter region and no stripe anywhere -- so a world with
nothing on it is closer to what Uranus looks like than anything the box could
print on it, and the identity of the piece is carried by the ring, by the size
the ladder gives it, and by the cyan.

**The ring turns white**, which is the second half of this edition and the
smaller half. It printed in the globe's own cyan for one edition, so that it
would read as relief rather than as a line drawn on the planet; the owner has
reversed that too. **Both ringed worlds now print their ring in white, and the
set's rule that rings are white holds without a footnote for the first time.**
Nothing about the ring's shape moved: not its diameter, not its thickness, not
its projection, not its lean. One existing body changed spools.

**The history, because it is worth having in one paragraph.** Uranus wore a
single upright white band around its equator, and because the planet lies on
its side that band stood on end across the face you were looking at: a tennis
ball. It then wore a broad soft polar hood above and below sixty degrees of
latitude, in the palest warm tone the box carries, at both poles -- because the
two armies lean opposite ways and one hood would have been invisible on half
the pieces. Both were argued at length and measured twice. The owner has looked
at the finished hoods and taken them out, and nothing replaced them. The whole
argument is kept, word for word, in the source that draws this world and in the
design contract, under a heading that says what happened to it. A reader a year
from now can see the case and the decision side by side and know which one won.

The outcome was named in advance by the brief that built the hoods, which
called it legitimate: *"Uranus being the one unmarked world in a set of eight is
a defensible design statement rather than an omission."* It was offered there as
the fallback if no filament measured usable against the cyan globe. The
measurement came back usable, so the hoods were drawn. The owner has taken the
fallback anyway.

**Uranus's piece now prints in three filaments where it printed in four** --
white, black and cyan, against white, black, cyan and beige. It is the first
correction in this chain to make a world simpler to print rather than more
complicated. Counting the globe and what stands on it and leaving out the base
and its numeral, which every world shares, Uranus is still a two-spool world
and the two spools are different ones: cyan plus beige has become cyan plus
white.

**One cost of this decision, stated rather than buried.** The cyan is wrong
against the reference and this edition makes that MORE visible, not less. The
filament is #00FFFF, a saturated neon; the reference is a pale desaturated ice
blue measuring 161, 200, 206. There is no pale blue anywhere in the thirteen
colours this box prints from -- the only other blue is a dark navy, further
away still. With the hoods gone there is now nothing else on the ball to look
at, so the gap is more exposed than it was. That is an honest cost of the
owner's decision, not an argument against it.

**Nothing else in the set changed.** The other fourteen worlds, the board, the
belt, the coronas, the stars and the trays come out of this run with exactly
the geometry they had, and that is measured file by file rather than asserted.
Both Uranus pieces come out BYTE-FOR-BYTE identical to the last edition's, and
that is the check rather than a coincidence: taking a marking off a globe stops
partitioning it and moves no surface, and repainting a ring moves one body from
one spool to another and moves no surface either. If either Uranus file had
changed, something had moved the ball or the hoop and it would have had to be
found before anything else in the run was worth reading. Neither did. The
assembled set goes from 224 pieces to 220, which is exactly the four hoods and
nothing else, and each globe gains back exactly the volume its two hoods held,
to fourteen ten-thousandths of a cubic millimetre.

**Neptune's three white bands from the previous edition stay as they are**, and
so does everything corrected before them: Saturn's bands came down in tone
rather than up, Jupiter's belts were put back at their own unequal latitudes,
and Earth, Mars, Mercury and Venus each wear a real map. None of that was
reopened here.

**Saturn's ring is untouched**, as it has been through every edition. It already
worked, it is what the whole set's size ladder was solved against, and not a
number in it moved. This box has two worlds with rings, and from this edition
the two rings are made of the same thing -- both are separate white pieces --
so what tells them apart is how they stand: Saturn's is a plate lying almost
flat beside its ball, Uranus's is a hoop standing on edge over its ball. Ø30.00
against Ø24.02; one wider than it is tall, the other taller than it is wide.
The colour no longer helps, and that question was put to the blind reader of
this build rather than assumed.

A cocoa-brown asteroid belt crosses the middle of the field, a star stands at
each end with two flames bursting off the board edge, and the three cells
around each star are sunken corona wells where a captured world drops out of
the light and its rank counts for nothing. You win by walking one of your
worlds onto the rival star.

## What arrives

Forty-two printed parts: sixteen worlds, a board in four panels, twelve
asteroid-belt tiles, two stars, six corona cells and two storage trays. Nothing
is glued, screwed or assembled; the tiles and stars drop into their own pockets
and the panels butt together.

## Where the eight surfaces come from

**All sixteen world pieces have now been corrected, one pair at a time, across
eight runs, and one of them has since been un-drawn.** A reader picking the set
up should be able to learn in one paragraph where each world's surface comes
from, without reading nine revision histories, so here is all eight worlds in
one line each.

- **Mercury** -- outline. Seven smooth albedo plains traced as rings, plus the
  Caloris basin as a bright floor inside a raised rim.
- **Venus** -- outline. Seven radar highland provinces led by Aphrodite Terra,
  and three lowland plains, from the Magellan mosaic.
- **Earth** -- outline. Coastlines, dry interiors and a northern ice cap.
- **Mars** -- outline plus cap. The classical albedo map, and two polar caps
  whose rims are broken by lobes so they read as ice rather than as lids.
- **Jupiter** -- band, blob and outline. Six belts at Jupiter's own unequal
  latitudes, five, seven, ten, thirteen, seven and six degrees wide; five
  bright cream zones between and beyond them; and the Great Red Spot as one
  oval, thirteen degrees of arc by nine, with a darker collar and the widest
  belt bending north around it. The two widest belts carry a slight wave rather
  than running as exact circles.
- **Saturn** -- band, cap and **ring**. Five bands at nine, fifteen, eight,
  sixteen and twelve degrees wide, unevenly spaced and not symmetric about the
  equator; four of them a mid amber and only the widest still brown, because
  this is the world in the box whose reference is softer than the build was;
  and a bright cap above fifty-eight degrees north. The ring is geometry rather
  than a marking: a flat white plate in Saturn's equatorial plane, so it lies
  almost level.
- **Uranus** -- **nothing, and a ring.** No hood, no cap, no band, no spot: one
  undivided cyan sphere, the only bare world in the box. The ring is geometry
  rather than a marking: a hoop in Uranus's equatorial plane, which on a planet
  lying on its side means it stands upright over the globe. It prints in white,
  the same spool as Saturn's ring.
- **Neptune** -- band and outline. Three closed white bands of latitude, five,
  four and three degrees of arc wide, at forty-six to forty-one south, eleven
  to fifteen north and thirty to thirty-three north; each runs the whole way
  round the planet. And the Great Dark Spot as one outline oval twice as wide
  as it is tall, with its small white companion cloud just below it.

Seven of the eight are drawn, none of them as a union of circles. The eighth is
bare on purpose.

**The useful division is not which were corrected but where each surface comes
from.** Four of these worlds have a solid surface that has really been mapped
-- Mercury, Venus, Earth and Mars -- so their markings are traced outlines, and
on Earth and Mars they are silhouettes you can check against a map you already
know. The other four are atmosphere. Jupiter, Saturn, Uranus and Neptune have
no surface to trace; what they show is weather. **Three of those four are drawn
and the fourth is not.** Jupiter, Saturn and Neptune wear bands, caps and
storms. Uranus wears nothing, because its weather is a faint diffuse
brightening near a pole and the box has no way to print a thing that fades: a
marking here is a change of filament at a line. Drawn at all, it came out as a
pale disc, and the owner would rather have the bare ball. So the honest summary
is four mapped worlds drawn from outlines, three atmospheres drawn as weather,
and one atmosphere left alone.

That last one is the whole of this edition, and it has a condition attached
that is worth naming: **bare separates Uranus from its neighbours only while it
is the only bare world in the set.**

## What Uranus now has to carry on its own

With no marking on it, everything that tells a player which piece this is comes
from three things: the ring, the size and the cyan. Each was checked against the
world that contests it rather than assumed, and the three answers are not equally
strong.

**Against Neptune**, its neighbour in rank and in colour family, size cannot
help at all: Ø22.02 against Ø21.89 is a tenth of a millimetre, less than one
nozzle width, and they are the only pair in the ladder of which that is true.
What separates them is everything else. Neptune now carries three white bands
and a dark spot on a royal blue; Uranus is bare cyan with a white hoop standing
over it. One is a marked ball, the other is a bare ball wearing a ring. The two
are rendered side by side at the product's own angle, one frame per army, in
`cad/snap/worlds/uranus-neptune-hero.png`.

**Against Saturn**, the other ringed world, the colour of the ring no longer
helps -- that is the price of this edition's second change, and it is stated
rather than hidden. What is left is orientation and size, and they are not
subtle. Measured across the ring rather than across the base, which is the same
Ø33.87 on every piece in the box: Saturn's ring is a flat plate lying almost
level at Ø30.00, wider than the 29.00 mm the piece stands tall, so it reads as a
brim beside the ball; Uranus's is a hoop standing on edge at Ø24.02, narrower
than the 25.98 mm the piece stands tall, so it reads as a band over the top of
the ball. One widens its piece and the other raises it. Saturn's ball is also
3.98 mm larger, which is ten nozzle widths and a rank the ladder shows on its
own. `cad/snap/worlds/uranus-saturn-hero.png` puts them side by side and
`cad/measure/uranus-saturn-separation.md` measures all four cues separately.

**Against Earth**, the other blue-family globe, the two are four ranks apart --
Ø22.02 against Ø16.70, a third larger -- and drawn from different spools, and
Earth carries a coastline map where Uranus carries nothing.
`cad/measure/uranus-earth-separation.md`.
## What the previous edition's blind reader said about Uranus

One independent reader was shown twenty pictures of this build and nothing
else -- not what the object is, not what had changed, not that anything had
changed. It was asked eight open questions and five specific ones, and it
answered before it knew any of it mattered. Three rounds, no repairs, and the
pictures it read cold are the pictures sealed with this box.

**It named all eight worlds.** Jupiter from its bands and its red spot, Saturn
from its ring, Neptune from its dark spot, Earth from "the shape of Africa",
Venus, Mars, Mercury -- and Uranus, from *"a featureless pale cyan sphere with
a narrow ring standing nearly vertical ... Uranus is the tipped-over planet
with a perpendicular ring plane."* It worked out that the two armies are mirror
images of each other without being told there were two armies.

**On the one thing this edition had to get right, it was unambiguous.** Asked
cold whether anything at all is drawn on the cyan ball -- a band, a patch, a
cap, a panel, a spot, a stripe, a seam, a pole marking, any change of colour:

> **"NO. Nothing at all. Confidence: very high — as high as I can be from
> images."**
>
> "all **four poles of both copies** are presented face-on and centred, and
> **all four are blank**. If there were any polar treatment at all it would be
> unmissable in those frames. There is none."

It checked its own instrument first, unprompted: *"the other pieces in this set
clearly can carry surface markings... So this is not a limitation of the
rendering or the process."*

**On telling the two ringed worlds apart**, now that the ring colour no longer
helps: *"Can I tell the two subjects apart without being told? Yes, trivially,
and I did before reading anything."* Colour of the ball first, then ring
attitude -- *"Horizontal brim vs upright band. This is the meaningful
difference and it is visible even in the tiny board-distance renders."* And:
*"Would I actually manage it across a table? Yes, easily... This is the one
piece of the design that works unambiguously at play distance."*

### The uncomfortable part, reported straight

The box was asked, in the same words a previous edition used, whether any piece
reads as a beach ball or a tennis ball. **The answer is yes, and it is this
world.** At board distance:

> "a saturated, completely flat, glossy single-colour sphere with **one bright
> white stripe running over it**. That is the exact visual grammar of an
> inflatable beach ball... Nothing in the picture says 'planet'; everything says
> 'toy ball'."

Close up the reading falls apart -- *"not a beach ball — a ball in a standing
hoop from three-quarter views"* -- because at that distance the hoop resolves
as a separate object standing off the ball, which is what it is.

Told afterwards that the previous reader's objection had two halves and that
this edition removed one of them, it did not soften, and it made the sharper
point against the box rather than for it:

> "The revision swapped one route to the toy-ball reading for another... Both
> routes end in the same place, and the second one is the one the revision
> built."

**That is recorded and not acted on.** The ring stays white, nothing was added
to the globe, nothing was tinted and nothing was softened. The owner has
decided, and the measured number belongs beside the reading rather than instead
of it: the white hoop separates **38.7 to 39.3** of 255 greyscale levels from
the cyan ball, measured by rendering one piece twice with only the ring
repainted (`cad/measure/uranus-ring-tone.md`).

**The recommendation, for the owner rather than from the box.** The reader
would not touch the ring -- the contrast is doing real work, and the same white
is already too quiet on Saturn's cream globe. Its question is narrower: *"Was
the objection to having a polar marking, or to those two pale beige discs
specifically?"* If it was the pale discs, there is an option that honours the
objection and still breaks the beach-ball grammar: the same hood at the same
sixty degrees, in **a darker tone of the globe's own cyan** rather than in
beige. No pale disc anywhere, no new colour, and a darker polar region is what
an ice giant actually does. If the objection was to having any polar marking at
all, its advice is to accept the reading: *"it is board-distance only; it
resolves correctly in the hand; and 'looks a bit like a toy ball' is a soft
failure in an object that is a toy."*

The argument it says it would actually lead with is not the beach ball at all:
this globe is now the only bare one in a set where the other fifteen are
painted.

### What it got wrong, and how that was settled

Twenty-nine defects were reported cold. **Thirteen were withdrawn on
measurement**, twelve of them from one cause the reader diagnosed itself: it
read the isometric picture as though it had depth, and turned overlaps in the
projection into collisions, cantilevers and pieces off the grid. The closest
two pieces on the board are 50.91 mm apart, which is 16.91 mm of clear air, on
a 36 mm grid; every ring sits inside the board's own footprint; and a flame and
a seated world share exactly 0.000000 mm³ on all sixteen combinations measured.
Seven more were properties of the picture -- the renderer has no ground plane
and casts no shadow, which is why the black bases look like ink and the trays
look like they are floating. **Nine findings stand, none of them blocking**,
and they are listed in the design contract rather than quietly dropped.

It also corrected the box's own paperwork, and it was right: a sentence
describing this world's hoop as running "pole-over-pole" was wrong, because the
ring lies in the planet's equatorial plane and this planet's poles point
sideways, so the hoop arches over its **equator**. The sentence was fixed; the
object was already right. Then it checked the fix against pixel coordinates it
had written down before it was given any angle, and got 8.0 ± 0.6 degrees
against a sealed 7.77.

### And the verdict

**Does the central experience arrive from the pictures alone** -- a two-player
game played with the planets, the pieces *are* planets, the sizes are ordered
rather than assorted, the two sides are the same worlds facing each other?
**Unmistakable**, with one caveat it asked to have carried: the ordering
arrives from the line-up frames and does not arrive from the board frame.

**Does the rule behind the sizes arrive** -- that each globe is the fifth root
of the real planet's diameter, and that this *is* the strength ranking? **No.**
*"The rule is elegant, it is real, and it is invisible."*

**Is it desirable?** Yes. With one thing named separately, which is the largest
risk this box carries and is in its own words:

> "That it ends up owned rather than played... rank, the one thing the game
> consists of, is the one thing the pieces will not tell you across a table."

Two of the ladder's seven steps are a tenth of a millimetre, and the rank
numeral on the base rim cannot be read at playing distance. Neither is in this
edition's scope -- the ladder is frozen and the numeral was not touched -- and
both are written down rather than answered.

The full account is in `cad/measure/signature-review-protocol.md`, and the
sealed record with every hash is `cad/snap/SIGNATURE-REVIEW.json`.

## What the previous edition could not do

**The globe's colour stays wrong, and this edition makes it more visible.**
`cyan` #00FFFF is a saturated neon; `cad/ref/uranus-sol.png` is a pale
desaturated ice blue -- its ball means 161, 200, 206 against the filament's
0, 255, 255, measured in `cad/measure/uranus-reference.md`. The thirteen PLA
colours this box prints from are the supplier's whole PLA range and none of
them is a pale blue; the only other blue is a dark navy, further away than the
cyan. With the hoods gone there is nothing else on the ball to look at, so the
gap has more room than it had. No marking makes a neon globe paler, and none
was attempted.

**The reference's one faint lighter region is not drawn.** The photograph does
carry a very faint, soft-edged, off-centre brightening. This piece has nothing
on it. The feature the box drew to stand for that brightening was the polar
hood, and the owner removed it; a flush colour inlay cannot fade out in any
case, so what the box could print for it was always a hard-edged region rather
than a brightening. The measured case for drawing it is kept in full, and the
measurement that chose its tone is carried forward under a heading saying the
feature is gone: `cad/measure/uranus-tone-separation.md`.

**The ring is not in the reference at all.** It is an owner instruction,
recorded as one here, in `product.json`, in the design contract and in
`cad/measure/uranus-ring.md`. Nothing else about the real ring system is drawn:
thirteen narrow rings at a fifth of a millimetre per degree of arc would be
grit, so what the piece carries is one solid hoop. No moons, no storms, no
banding, no shepherd gaps and no named ringlets.

**The two feet where the hoop meets the base are a small gusset rather than a
clean junction**, and that is unchanged by this edition because the ring's
geometry is unchanged. An upright hoop this small meets the flat cut at the
base top on the steep part of its own curve, past the 45 degrees the printer
holds unaided, so each foot carries a wedge at the 47.2 degree slope this box
already trusts under Saturn's ring. It is a sound joint and not a pretty one.

**And one thing that could stop being true.** Bare tells Uranus apart from its
neighbours only while it is the only bare world in the box. Nothing else in the
set is undrawn today; if a later edition un-draws another world, this one loses
a cue it now depends on.

## Before you print

Read `product.json` for the full list of limitations. Nothing here has been
printed, handled or played. Every fit, wall thickness and overhang margin is a
measurement on the exact CAD solids and a prediction for a 0.4 mm nozzle at
0.2 mm layers.

**Verification result: UNVERIFIED.** The final pipeline ran for 1216.45 s. Every fit, spec
and layout check passed, and the geometry inspection's result is UNVERIFIED:
50 of its 51 checks passed. `GEOMETRY-NOTES.md` says exactly which checks, if
any, are unverified, and why. The mounting and power checks do not apply to this
set, and motion checking is switched off, so **motion is unverified**, not
passed.

All 24 printed parts cleared the 0.80 mm wall gate and the 45-degree overhang
gate at a 0.4 mm nozzle in their own rounds. Those are measurements on the CAD
solids, and **none of it makes the set print-ready. That is not claimed.**

The CAD project under `cad/` carries its own README, the full specification in
`cad/antisol_spec.md`, and every measurement this build made under
`cad/measure/`.

<!-- workshop-geometry-disclosure -->
# Geometry inspection limitations

Geometry inspection is incomplete. This prototype is unverified and is not print-ready; see GEOMETRY-NOTES.md.

The following checks did not finish. No passing verdict is inferred from their interruption.

- interfere:assembly: geometry worker exited without a complete verdict (completed measurements: 12).
