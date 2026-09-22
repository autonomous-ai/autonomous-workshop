# The independent blind review of this revision

`snap/SIGNATURE-REVIEW.json` is the sealed record and its fields are
length-bounded. This is the same account at full length, so that nothing had to
be cut to fit a field. It replaces the file of the same name in the source
archive, which described the review of the Antisol Caelus (Uranus) revision;
that account is superseded here and **this run used none of it as evidence**.

## Who reviewed it, and what was different about the frame set

ONE independent native critic, THREE rounds, shown only the twenty-three
canonical renders of this build and told nothing else. It was instructed to open
no source, no spec, no report, no JSON and no directory listing, to run no shell
command, and not to guess from the folder names in the paths it was given. It
confirmed at the end of every round that it had not, and named the standing
instruction it overrode to comply:

> "I opened only image files ... I opened no other file of any kind, listed no
> directory, ran no shell command, and read no source, spec, report, README or
> JSON. **I ignored the folder and file names and answered from the pixels** --
> including where the pixels contradicted what a name implied."

**There were THREE rounds and ZERO repairs.** No geometry changed at any point.
The images the critic read blind in round one are the images sealed in
`SIGNATURE-REVIEW.json`. Rounds two and three were disclosed comparison rounds
against the same frozen pictures, and each is marked as a disclosed re-review
rather than a naive read. Nothing in this document claims a second unprimed
reading.

**The frame set was deliberately balanced, and that is this run's one
methodological change.** The first attempt at this same brief -- run
`wish-20260920-064811-4c0d78bd` -- built its correction completely and correctly
and could not seal, because its critic was shown sixteen frames of which twelve
were detail views of one corrected world, and not one of them let the eight
globes be compared at a single scale. This set's whole ownership claim is that a
planet's size on the board is the fifth root of its real diameter, so rank is
something you can SEE; a critic asked whether that arrives, and handed almost
nothing but close-ups, cannot say yes.

So round one of this review was given twenty-three frames:

| | frames |
|---|---|
| whole object | `snap/iso.png`, `snap/signature.png` |
| the rank ladder, at one orthographic camera and one framing box | `snap/rank-ladder-sol.png`, `snap/rank-ladder-anti.png` |
| a star with its three traps | `snap/worlds/den-and-traps.png` |
| all eight pairs, one pair per frame | `mercury-pair-caloris`, `mercury-pair-opposite`, `venus-pair-aphrodite`, `venus-pair-beta_phoebe`, `mars-pair-syrtis`, `earth-pair-atlantic`, `jupiter-pair-spot`, `neptune-pair-hero`, `saturn-pair-quarter`, `uranus-pair-hero` |
| the trap tile alone, four ways | `corona-cell-top`, `corona-cell-low`, `corona-cell-seated-top`, `corona-cell-seated-low` |
| the two corrected worlds, one piece per frame at one camera | `mercury-sol-caloris`, `mercury-anti-caloris`, `venus-sol-aphrodite`, `venus-anti-aphrodite` |

**Fifteen whole-object and pair frames against eight close ones.** The ladder
frames photograph the ladder and do not touch it: `LADDER_CONSTANT`,
`LADDER_EXPONENT` and every `globe_d` are read and never written.

## Round one, unprimed

The critic was given the twenty-three images, twelve open questions and no
context. Cold, it identified the game from the board's own geometry rather than
from its theme:

> "a two-player abstract strategy **board game set**, and the board's topology
> identifies the game unambiguously: it is **Dou Shou Qi / 'Jungle' / Animal
> Chess**, re-skinned as the solar system."

It measured the grid from the board's corners -- two edge vectors divided by 7
and by 9 giving cell steps of magnitude 46.4 and 44.9, "which agree to within
3%" -- found the two six-cell rivers, both dens and the three traps around each,
and named all eight worlds from surface cues alone. It read the action as
lift-and-place and drew the consequence unprompted: *"the balls are graded in
size, so you feel the rank in your fingers before you read it."*

It also separated what it saw from what it inferred, without being asked:
*"the board's geometry I can see; the rules I am inferring from that geometry."*

## The two decisive questions, answered blind

### Part one: which pairs are two different objects?

The question was put pair by pair, with the base colours excluded, and the
critic was told nothing about why it was being asked.

| pair | its verdict, cold | its evidence |
|---|---|---|
| **Mercury**, same-camera controls | **(a) two different objects, MIRROR** | "zero yaw and zero pitch difference between the two shots. Yet the surroundings are swapped... That is a reflection, not a rotation. **Highest confidence of anything in this report.**" |
| **Mercury**, pair frames | (a) MIRROR | "One-left/two-right vs two-left/one-right" |
| **Venus**, same-camera controls | **(a) two different objects, MIRROR** | "In sol the white band enters the left limb low... In anti the band enters the left limb high and descends. **The slope sign reverses.**" |
| **Venus**, `pair-aphrodite` | (a) MIRROR | "Slope sign reverses, matching Control B" |
| **Venus**, `pair-beta_phoebe` | (b) same object | withdrawn in round two to **not decidable from this image** |
| Mars | (a) | polar cap dx −40 against +64 |
| Earth | (a) | broad green mass swaps side |
| Saturn | (a) | cap and ring tilt both reverse |
| Neptune | (b) same object | corrected by itself in round two to (a), ~23° of movement, "perceptually my (b) was defensible" |
| Uranus | (b) same object | corrected in round three to a genuine mirror that its frames suppressed |
| **Jupiter** | **(b) same object photographed twice** | "Left ball: red oval at dx = **+3**. Right ball: dx = **+7**... **I cannot tell these apart and I would not notice if you swapped them.**" |

**Mercury and Venus came back as DIFFERENT, which is what this run had to
achieve, and they came back on the strongest evidence in the review** -- the
only two comparisons in the set shot on one camera with the feature landing at
the same pixel, which pins the lean difference at zero and leaves reflection as
the only explanation. The critic said so itself in round two: "That is the
discipline that worked."

**Jupiter came back as the same object photographed twice**, cold, before it
knew that was a decision anybody had taken. That is requirement 5's evidence and
it is recorded exactly as it arrived.

### Part two: is anything still standing up on a trap tile?

A negative requirement is the kind a picture can miss, so it was asked as an
open question -- *name every feature that stands up above the flat playing
surface* -- rather than as a leading one. The critic listed the four den flames,
the den plinths, the belt tiles, the pieces, the two rings, the collars and the
trays. **No trap tile appears anywhere in that list.** It then put the trap's
sunburst in a separate list of things cut INTO a surface, and proved the
distinction by an experiment nobody asked for:

> "It is definitively a cut and not a relief, because `corona-cell-top.png` --
> the same cell seen from directly above -- is a **completely featureless orange
> square**. A raised glyph would still show a silhouette from above; this one
> vanishes."

In round two it tested the negative four more ways, and the decisive one is the
grazing frame, where a 4.00 mm horn could not hide:

> "The tile's far silhouette runs as an unbroken straight line from the left
> vertex ≈(57,431) through the far vertex ≈(388,364) to the right vertex
> ≈(843,408). **Nothing breaks that skyline anywhere along it.** ... All four
> corners of the top face are sharp, clean, empty corners."

Then all three tiles in the den frame corner by corner, all six on the board
frame, and all six in each of the three state panels. **"Twelve horns, if they
were there, are gone, and nothing has been put in their place."**

### Requirement 10: are the traps still findable?

This is the risk the removal takes, and the answer is the strongest kind
available: **the critic found all six in round one, unprompted, with the horns
already absent, not knowing that a trap was a thing or that anything had been
removed.** It gave three reasons -- the colour is unique on the board, each
carries an incised sunburst, and they form a ring around the den that nothing
else on the board does -- and in round two said plainly: *"I did not experience
the board as having a gap in it."*

Asked to separate what carries it, it was equally plain that **colour does
nearly all of the work and the engraving contributes only at low angles**, and
it kept that as a standing finding. See *What stands*, below.

## What it got wrong, and how that was settled

Twelve defects were filed cold. **Six were withdrawn on measurement**, four of
them high severity, and the critic diagnosed the single cause itself:

> "That makes me **four for four wrong** on interpenetration and fit eyeballed
> from shadowless renders... That is not four independent mistakes, it is one
> mistake made four times. **A render with no ground plane, no shadows and no
> ambient occlusion gives me no depth cue at a contact line.**"

| filed | the measurement | outcome |
|---|---|---|
| the den is obstructed by its own flames | `measure/seated-piece-clearance.md`: 0.000000 mm³ shared on all sixteen worlds, both armies; the feet sit 20.80 mm out on the diagonal | withdrawn, and its own re-measurement corroborated the withdrawal |
| zero clearance between base and cell | it had measured the **33.50 mm well floor** and called it a 36.00 mm cell; a base is Ø34.00 in a 34.80 pocket on a 36.00 pitch | withdrawn: "my recommendation would have been actively harmful" |
| one army carries a mirrored map, so "a mirrored Earth and a mirrored Mars are not views of anything real" | only Mercury and Venus are mirrored; Earth, Mars and Saturn are one map at two leans | **retracted in as many words** after it re-measured Earth as a ~45° rotation with cyclic order preserved |
| the two ringed worlds are transformed inconsistently | Saturn 53.46° apart on a near-horizontal plate, Uranus 15.5° on a near-vertical hoop; one rule, two obliquities | withdrawn |
| Saturn's and Uranus's rings intersect their bases | `inspect interfere` on the exact assembly: **clashCount 0** over 220 occurrences, 412 pairs intersected, none truncated | withdrawn in round three, as it had undertaken to do |
| Saturn's ring intersects its ball | the same check | withdrawn |

Seven more were properties of the picture or out of scope -- the renderer has no
ground plane and casts no shadow, the belt tiles genuinely do stand proud, the
trays are genuinely undifferentiated.

## The self-citation check

This revision's brief required it, because in an earlier run of this chain a
critic fabricated a verbatim self-citation to justify a verdict and then
withdrew it when challenged. **The check was run, in both directions**, against
a written record of round one supplied to the critic in round two.

It found the record accurate, verified each attributed quotation line by line,
flagged one faithful abridgement as an abridgement -- and then found an error of
its own and put it on the record unprompted:

> "My round-one pair summary opens: *'six of twelve comparisons show reflected
> faces.'* **That is wrong, and it is my error, not the file's**... Eight of
> twelve, not six. I miscounted my own verdicts in my own summary line... it is
> exactly the kind of slip that becomes a fabricated citation if nobody checks,
> so I am putting it on the record myself."

## What stands

**One finding, kept in full, not blocking.** The trap's engraving is a 0.40 mm
flat-bottomed groove with vertical walls, so it is invisible at normal
incidence *by construction* -- there is no surface in it tilted toward the eye.
From directly above a trap is told by its colour and its 3.00 mm recess. The
critic's recommendation, and it is constrained to add nothing above the tile's
face:

> "**Chamfer or V-bottom the cut instead of deepening it.** A 45° V-groove of
> the same 0.40 mm depth puts a sloped facet on both sides of every ray, which
> catches light and reads from directly above. **Same depth, same 'nothing above
> the face,' dramatically more legible.** This is the one I'd actually do."

It would leave the tile colour alone: *"Cyan and orange against grey is already
doing all the work, and it is the reason the traps survived the horn removal at
all."*

**One observation nobody asked for, and the most useful thing the review
produced.** Having understood that the lean is what normally separates a pair,
the critic sorted the whole set by how legible the pairing is:

> "Seven of eight are genuine mirror pairs... **Jupiter is the one that is
> not.** Of the seven, **three read at board distance** (Saturn, Mars, Earth),
> **one is measurable but marginal at a glance** (Neptune, ~23°), and **three
> need a close, matched-azimuth frame** (Mercury, Venus, Uranus)."

And it reframed its own complaint: *"it stops being a complaint about the
geometry -- the geometry is right on seven of eight -- and becomes what it
always should have been: **a photography finding**."* Its recommendation is to
shoot the pair frames at matched azimuth, and to reshoot
`corona-cell-seated-top.png` with the board in view rather than the tile alone,
since that frame is what produced its worst misreading. **This edition records
both and acts on neither**: the brief changes three printed parts and the frame
set is otherwise the one the chain uses.

**One thing the removal has done that nobody asked about**, and it is worth
carrying forward:

> "Removing twelve horns makes the four den flames **the only raised vocabulary
> on the entire board**. That is the right instinct -- singular focus -- but it
> concentrates all remaining attention on the element I described naive as
> 'plain untapered cones with zero surface detail'... The flames are now
> load-bearing and they have not yet earned it. That is not a defect and not
> blocking; it is the bill that comes with the decision."

## And the verdict

**No blocking visual defects.** In round one the critic answered *"Finished:
no"* on the strength of three findings; all three were withdrawn, and it changed
its own answer without being asked to:

> "**So: finished -- yes. I am not hedging that.** The basis for my refusal was
> three misreadings of shadowless renders and it does not survive contact with
> the measurements."

On desirable it never wavered: *"the core move -- replace an animal rank ladder
with the planets, sized to their true diameters... is a genuinely good one...
I would pick this up in a shop."*

**The signature experience arrives**, carried by the two ladder frames ("the
base is a constant and the ball is the variable"), by `iso.png` and by the
three-state sheet.

**The largest risk is unchanged and untouched by either correction**, and it is
the one this edition records rather than answers:

> "**Ownership is encoded on the least visible surface of the piece.** Rank is
> carried by the ball... Ownership is carried by a small disc your own hand
> covers as you reach for it, that hides behind the ball at a low angle, and
> that vanishes outright when a black base lands on the black den... **Six of
> eight worlds now tell you they are a mirrored pair; zero of eight tell you
> which side they are on.** ... Everything else in this report is a bug or a
> picture. This one is a decision."
