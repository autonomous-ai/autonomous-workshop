# Revision C, review round 3 — evidence, and resolution

Same critic, still primed. This round existed for one reason: in round 2 it
raised a finding it described as "the one thing I would hold the delivery on" —
that the Sun counter's eight wedges are reproportioned against
`ref/ref-02-ref-2-sun-face.png`. It measured 75 × 70 px against the reference's
46 × 130 px at matched disc scale, an aspect of 0.93 : 1 against 2.8 : 1.

The measurement was correct. The inference was not, and the Manager went and got
the evidence rather than arguing.

## The evidence put to it

1. `part_sun_counter.step` hashes `262ccc86f6e4c403…afe5f3b` in both the archive
   and this revision. The same file.
2. The archive contains its **own** renders of its **own** counter, made by the
   same renderer at the same cameras. Their sha256 match this revision's:
   `sun-plan_el90.png` `245bd93d86cd36f9…`, `sun-oblique_az-90_el22.png`
   `017525622497d206…`, and both moon frames likewise.
3. From the source, the wedges run radius 4.25 → 6.25 (2.00 mm long) at 1.8 →
   2.2 mm wide. Aspect 1.0 : 1. The built sun has square nubs and always did.

The critic was told plainly that it was not being asked to change its mind, that
if it still wanted to call it FAILS the Manager would seal it as a blocking
defect, and that it should verify the facts itself rather than take them.

## R1 — it verified, and restated

> Fact 2 holds, and harder than a hash: I loaded the archive's
> `verification/renders/counters/sun-plan_el90.png` and this revision's
> `cad/snap/counters/sun-plan_el90.png` into arrays and differenced them.
> **Max pixel difference 0, differing pixels 0.** Then I ran my own radial-profile
> method on the *archive's* file and got the identical numbers I had reported for
> the revision… The archive's own picture of its own counter has the square nubs.

> Fact 3 holds and it closes the loop on my own measurement: 0.425R and 0.625R on
> a 20 mm counter are radius 4.25 mm and 6.25 mm exactly. My pixel bands were not
> approximating the wedge footprint, they *were* the wedge footprint, to the
> millimetre.

**P10-REVISED: MATCHES**, in the form the critic chose:

> the counters in this revision are unchanged from the archive — byte-identical
> STEP and byte-identical renders — and the archive part does not match the
> reference art in ref-02, whose rays are drawn at roughly 2.8:1 against the CAD
> part's 1.0:1.

Its own account of the error, kept because it is the useful part:

> My measurement was correct and I still stand behind every number in it. My
> **inference** was wrong: I treated ref-02 as a render of the archive geometry
> because that was the premise I was handed, and from a real difference I
> concluded a frozen part had been altered in this revision. That conclusion was
> unsupported the moment a second explanation existed… I called it "the one thing
> I would hold the delivery on." It was not that.

The divergence itself is real and is recorded in `GEOMETRY-NOTES.md` C13, with
the critic's numbers, for whoever commissions the next revision.

**N8-REVISED: MATCHES.** Restated as the brief's actual constraint — every
surface flat-horizontal or square-vertical, no sloped, conical, domed or curved
field, and no rebate or ring beyond the flat rim band and the flat sunk field:

> Radial profiles at eight angles on each counter find exactly one circular band
> outside the emblem, at 0.90R, which at orthographic el90 is the disc's own
> top-edge chamfer at 0.99 mm; there is no second ring, no halo, no extra rebate,
> and the rim-band-to-field step is invisible in plan precisely because its wall
> is vertical.

## R2 — the two orientation marks

The critic checked its own coordinates and withdrew the "2.7 mm bite":

> In the 1800 px frame the marks occupy y 159–182 and the first tile row begins
> at y 184.5 — they are two pixels clear. There is no bite. I reported "a 2.7 mm
> bite out of a playing square" by reading an overlap in **x** as an intersection,
> when the two features never share a **y** range.

> **Recorded as: disclosed inherited blemish. Not blocking.** They are frozen,
> they are 0.8 mm raised marks in the margin that touch nothing and interfere
> with no counter… Worth a line for the next commissioner alongside the wedge
> divergence, with the number — one cell, 22 mm, both edges, same offset.

Recorded in `GEOMETRY-NOTES.md` C14.

## Q1 (round 2) — the re-rendered board frames at 1800 px

> Yes, it reads as a chequerboard, and more comfortably than at 1200 — at this
> scale the navy-on-pale alternation is unmistakable at a glance… Sampling all 64
> cell centres in the new empty-plan returns exactly 32 dark cells in perfect
> alternation, rank 1 reading X.X.X.X., so a1 dark and h1 light, with a cell
> pitch of 178.8 px = 21.95 mm… tile 175 px = 21.48 mm in a 22.0 mm cell.

## R3 — desirability

**Yes**, reversed from round 2, on the critic's own reasoning:

> That is a change from my last answer, and I want to be clear it is not because
> I was pressed. My "no" rested on three legs and I named the first as the worst.
> That first leg was an explicit argument that the sun was *a regression against
> the archive rather than a design choice* — I wrote those words — and the
> regression does not exist. The second leg was a 2.7 mm bite that my own
> measurements say is not there. A verdict built on two facts that turned out to
> be false does not get to survive the facts.

> …the two things this revision was asked to fix are executed to a standard I
> would be pleased with on a bought object: 6.01 mm of air on each side of a
> 30.05 mm slit, a 9.90 mm gap between the arms, the tube fused across both with
> 2.5 mm of overlap each side, and the whole roof mirror-symmetric about the slit
> plane to within one pixel at 0.18 mm.

Two reservations it attached to the yes, kept here in full because a positive
verdict must not swallow them:

1. The sun still reads as a cog rather than a sun at board size — not a
   regression, not this revision's, but a genuine weakness of the settled design,
   and the commission's own reference art shows the stronger version of the same
   idea. Twelve of the twenty-four pieces are that counter.
2. In strict side elevation the telescope's housing breaking out of the dome's
   flank makes the profile read as a teapot; that is the one angle at which the
   object stops being an observatory.

Both concern frozen geometry and both are carried into `GEOMETRY-NOTES.md`.

## R4 — blocking defects

> For the centring of the yoke arms, the symmetry of the roof, and the board's
> inlaid fit layer: **the list is still empty.** … The line I asked you to hold
> the delivery on in round 2 is withdrawn.
