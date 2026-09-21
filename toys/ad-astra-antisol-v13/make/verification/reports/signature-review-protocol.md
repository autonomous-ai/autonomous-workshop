# The independent blind review of this revision

`snap/SIGNATURE-REVIEW.json` is the sealed record and its fields are
length-bounded. This is the same account at full length, so that nothing had to
be cut to fit a field. It replaces the file of the same name in the source
archive, which described the review of the Antisol Mirror (Mercury and Venus)
revision; that account is superseded here and **this run used none of it as
evidence**.

## Who reviewed it, and how the frames were handed over

ONE independent native critic, FOUR rounds, shown only eighteen canonical
renders of this build and told nothing else. It was instructed to open no
source, no spec, no report, no JSON and no directory listing, to run no shell
command, and not to guess from file names. It confirmed compliance at the end of
every round and repeated the confirmation in round four for all four rounds.

**The file names could not leak anything, because there were none.** The
eighteen frames were copied to a scratch directory as `frame-01.png` through
`frame-18.png` in a seeded shuffle before the critic was given the paths. The
previous revision asked its critic to ignore folder names; this one removed them.
The mapping is `.tmp/review-manifest.json` in the run workspace, and every
copy is byte-identical to the frame it came from, so the hashes sealed in
`SIGNATURE-REVIEW.json` are the hashes the critic read.

**The frame set was balanced, and that rule is inherited rather than invented.**
An earlier attempt in this chain could not seal because its critic was handed
twelve detail views of one corrected world and no frame in which the eight
globes could be compared at one scale. This Wish repeats that rule in two parts:
put the orthographic eight-globe rank ladder in the round-one set, and do not
let detail views of Jupiter outnumber the whole-object frames.

| | frames |
|---|---|
| whole object | `snap/iso.png`, `snap/signature.png` |
| the rank ladder, one camera and one framing box | `snap/rank-ladder-sol.png`, `snap/rank-ladder-anti.png` |
| a star with its three traps | `snap/worlds/den-and-traps.png` |
| pair frames, one pair per frame | `mercury-pair-caloris`, `venus-pair-aphrodite`, `earth-pair-atlantic`, `mars-pair-syrtis`, `jupiter-pair-spot`, `jupiter-pair-opposite`, `saturn-pair-quarter`, `neptune-pair-hero`, `uranus-pair-hero` |
| the corrected world, one piece per frame at one camera | `jupiter-sol-spot`, `jupiter-anti-spot`, `jupiter-sol-opposite`, `jupiter-anti-opposite` |

**Fourteen whole-object and pair frames against four Jupiter detail frames.**
Two further frames, `jupiter-sol-polar` and `jupiter-anti-polar`, were released
in round two and only for the latitude and belt-width questions; the critic
reported back that they are useless for the lean question, because a camera down
a piece's own spin axis nulls the lean by construction.

The ladder frames photograph the ladder and do not touch it: `LADDER_CONSTANT`,
`LADDER_EXPONENT` and every `globe_d` are read and never written.

## Round one, unprimed

Cold, with eighteen meaningless names and twelve open questions, the critic
identified the object from its own geometry:

> "It is a two-player board game whose playing pieces are planets."

It reached that from the pieces rather than from a theme: every piece stands on
a flat disc, the discs come in exactly two colours, the same planet appears on
both, and the three-panel sheet shows the same board with fewer pieces each time
— *"Pieces leave the board as play proceeds, so there is capture or removal."*
It read the terrain unprompted — plain cells, brown cells with raised bumps,
cyan and orange cells with radiating engraved lines, and two 2×2 groups each of
a raised slab carrying two cones with three ray-engraved tiles around it — and
called it *"terrain that modifies movement or scoring."*

**It did not name Dou Shou Qi cold**, and that is recorded as it happened. The
previous revision's critic did; this one did not, and nothing here claims
otherwise.

It separated what it measured from what it inferred without being asked, and it
gave a standing error bar — *"roughly ±10 px on the 900×900 frames"* — which
later turns out to be the most useful thing in the whole review.

## The decisive question, answered blind: which pairs are two different objects?

The question was put pair by pair, with the base colours excluded, and the
critic was told nothing about why it was being asked.

| pair frame | its verdict, cold | its evidence |
|---|---|---|
| **Jupiter**, `jupiter-sol-spot` vs `jupiter-anti-spot`, same camera | **(a) two different objects** | "Two different objects. **Confidence high. I would notice this swap.**" Spot at (443,552) against (598,518): "a 155-px horizontal difference against a 322-px horizontal radius: 0.48r, about 29° of longitude, plus 34 px of latitude." Silhouettes identical at 645×598, so parallax is unavailable as an excuse |
| **Jupiter**, `pair-spot` | **(a) two different objects** | "an 84-px swing, roughly 30° of longitude, and the spot is also 21 px higher in latitude on the right... I would notice this swap if the two were side by side, not if shown apart" |
| Jupiter, `pair-opposite` | (c) not decidable | "no point feature to measure" — correct: the far face carries no spot |
| Mars | (a) | polar cap −42 against +74 px, crossing the centre line |
| Saturn | (a) | white cap +50 against −95 px, crossing the centre line |
| Neptune | (c) not decidable, leaning different | spot 0.35r further toward the limb, "the direction of the shift is exactly what parallax predicts" |
| Earth | (a), confidence low-to-moderate | polar patch +15 against +48 px; continent outlines "not obviously the same shapes" |
| Venus | (c) not decidable | "the band's slope reads as rising on the left object and falling on the right, which would be a real difference, but I do not trust that slope reading" — corrected in round two to a measured mirror |
| Mercury | (b) effectively the same object | withdrawn by the critic itself in round two as a feature-matching error, see below |
| Uranus | (b) the same object | the ring crosses at −37 px against −44 px; the globe is bare and carries nothing else |

**Jupiter came back as TWO DIFFERENT OBJECTS, cold, at the highest confidence
in the review, and that is the one thing this run had to achieve.** The critic
volunteered the sentence that makes it evidence rather than an impression:
*"Same camera, no parallax available as an excuse."*

For the record, the previous revision's critic was asked the same question about
the same world and answered the opposite way — *"I cannot tell these apart and I
would not notice if you swapped them"* — but **that is the source archive's
review, it is quoted here as the defect's history and not as this run's
evidence, and no part of it was reused.**

## The second unprimed question: is anything standing up on a trap tile?

A negative requirement is the kind a picture misses, so it was asked as an open
question — *name every feature that stands up above the flat playing surface* —
rather than as a leading one. Round one, before the critic knew what a trap was,
its list contained the pieces, their discs and stems, the two rings, the belt
cells' raised bumps, the raised den slab and the four cones. **No corona tile
appears in it.** It then put the tiles' sunburst in a separate list of things cut
INTO a surface, and gave the test it had used: *"a raised feature breaks the
silhouette of whatever it stands on... a cut feature never breaks an outline."*

In round three, disclosed, it inspected all six corona cells corner by corner
and gave each one's unbroken top-face outline in pixels. *"Six corona cells
inspected across two frames. Not one of them carries anything proud of its top
face."*

## What it got wrong, and how every one of it was settled

**Eight defects were filed cold, and all eight were retired.** Four by the
critic's own re-measurement, four by deterministic gates. The critic diagnosed
the common cause itself, in round three:

> "Three of the four failed for the same underlying reason — I read a shadowless
> oblique projection as if it were a plan view."

and extended it in round four to a fourth case:

> "That is the fourth time in this review I have mistaken a render limitation
> for a fault in the object — the floating trays, the ring overhang, the
> overlapping discs, and now the numeral. All four were the same error."

| filed | what settled it | outcome |
|---|---|---|
| two paint schemes exist for one body, and one is not in the product | the critic found its own control: the same Sol disc part renders bright white in one frame and mid-grey-rimmed in the other, so the two cameras are lit differently. The polar frame then showed both colour families on one globe, and its bare orange region measures 48.6° ± 2.5° against the ±46° the design leaves bare | withdrawn |
| Mercury's pair is one object photographed twice | its own re-measurement: "the x-offsets reverse sign on both off-meridian patches, which is the mirror. In round one I paired... by where they sat in the frame" — and the residuals were a systematic +9 px of parallax, after which "the mirror is exact to within 2 px on all three features" | withdrawn, and the pair regraded as a mirror |
| the grey moon has a hole in it | three tests it chose itself: the feature never breaks the silhouette, there is no internal shadow or rim highlight, and a through-hole would show the pale background rather than white | downgraded to consistent with a flush inlay |
| the trays float | the renderer has no ground plane and casts no shadow | withdrawn |
| Saturn's ring fouls its base, its cell or the board | ring outer radius 15.00 mm inside a 17.00 mm disc inside an 18.00 mm half-cell; the critic verified the ratio independently from the ladder frame at 0.894 measured against 0.882 predicted; and the ring is not a separate body — `parts/world.build_world` unions disc, globe and ring and refuses to emit the part unless exactly one solid results | withdrawn in full: "my premise was simply wrong" |
| a piece's footprint is as large as its cell | Ø34.00 on a 36.00 pitch, 2.00 mm rim to rim; the overlap it saw is a 4.6 mm-tall disc smearing forward in an oblique view | withdrawn in full |
| a den flame's base overhangs the slab | the critic reproduced the derivation from the constants itself — 20.80/√2 = 14.708, flange edge 18.000, less the 3.00 base radius = **0.292 mm inside** — and `measure/overhang-den_plug.md` returns PASS with zero regions needing support | settled; it added the note that 0.29 mm is under one extrusion width and is the first thing to go if that constant is ever moved |
| the sphere and stem are two solids pushed together | the same single-solid assert, on all sixteen world parts, plus zero clash at any junction and 0.0% of surface below the 0.80 mm wall on all 24 | withdrawn in full |

`inspect interfere` on the exact assembly this run built: **220 occurrences,
24090 pairs, 413 tested after bounding-box rejection, 0 truncated, tolerance
1.0 mm³, clashCount 0.**

## The finding the critic raised and then withdrew itself

In round two it measured the Anti-Sol spot **33 px higher** in the image than
the Sol spot, decomposed it as ~7 px of projection plus a 26 px ≈ 5.0° residual,
and attributed the residual to the handed belt wave carrying the spot's latitude
— a cost nobody had disclosed.

It was put the measurement that answers it: a longitude reflection maps
(lon, lat) → (2C − lon, lat), latitude is not an argument to the transform, and
`measure/jupiter-mirror.md` finds the largest latitude change across 14 rings
and 308 vertices to be **0.00e+00**. The vertical movement is real and already
measured elsewhere — `measure/mirror-meridian.md` reports the spot's screen
height changing by 1.196 mm because the reflection is solved about a meridian
14.07° from that camera's own.

The critic withdrew the finding and named the weak link in its own chain:

> "What I got wrong was not the measurement... What I got wrong was the
> subtraction. That 7 px rested entirely on my estimate of the camera elevation,
> ε ≈ 11°, which I derived from an 80 px ellipse minor axis against an 820 px
> major axis — **two soft, anti-aliased edges differenced against each other,
> the single weakest measurement in this entire review.** I then treated it as
> solid enough to license a finding against the object."

It also left one loose end open rather than tidying it away: it could not
reconcile the 1.196 mm figure with the camera elevation it had inferred from the
same frames, and recorded that as **a question about the render camera, not
about the object**, since the latitude question is closed by the transform
itself. That is carried here unresolved, which is what it asked for.

Asked separately whether 1.196 mm matters: *"No, and no... 4.4% of the diameter,
and against the spot's own 3.06 mm length it is 0.39 spot-lengths — compared
with the 2.05 spot-lengths of horizontal travel that the mirror is supposed to
deliver. The thing you meant to be seen is five times larger."*

## The self-citation check, run in both directions

This chain requires it, because in an earlier run a critic fabricated a verbatim
self-citation and then withdrew it when challenged. Eight quotations attributed
to the critic's round one were put back to it for verification.

**Three of the eight were inaccurate and were corrected before anything was
sealed.** The corrected text is what `SIGNATURE-REVIEW.json` carries.

| quotation | finding |
|---|---|
| frames 03 vs 10 | materially abridged: the sentence ends "...about 29° of longitude, **plus 34 px of latitude**", and the latitude figure had been cut |
| `jupiter-pair-spot` | materially abridged twice: "**and the spot is also 21 px higher in latitude on the right**" was cut, and so was the qualifier on the verdict, "**I would notice this swap if the two were side by side, not if shown apart**" — quoted without it, the verdict reads stronger than the critic made it |
| the largest risk | **a word that is not the critic's**: the record opened "Ownership... identity is carried almost entirely by colour". The critic did not write "Ownership" anywhere in that statement, and the insertion "points the finding at the wrong target" — its point was about telling ranks apart within one army, not about telling the two armies apart |
| the other five | faithful; each drops a following sentence, none changes a meaning, and the dropped sentences are recorded in the round-four transcript |

The critic then corrected its own accounting of that check unprompted: its
round-two tally of "six verbatim, two abridged, one misattributed" sums to nine,
and *"since the whole point of this exercise is that a record should not contain
a number nobody verified, that slip belongs in the record too."* The correct
tally is five faithful, two abridged, one misattributed.

## The one verdict that moved, and why

In round three the critic answered **"Is the signature experience unmistakable?
— No"**, on the ground that rank read by size works at the ends of the ladder
and fails across the middle four, which it had measured at 155, 165, 135 and
145 px.

It was told, in round four, that a "no" would be recorded as a no, and that the
only thing being asked was which of two candidate signatures it was answering
about — the rank ladder, or matter facing antimatter. It reversed the answer,
and the reason was its own arithmetic rather than anything it was told:

> "I am not reversing because you argued well. I am reversing because **the
> number I used was wrong.**"

It re-derived the ladder from the fifth-root rule and one anchor, reproduced the
design's own figures exactly, and found the step sizes to be **−3.6%, −15.3%,
−0.6%, −23.7%, −1.0%, −11.0%, −6.3%**:

> "That is not a ladder of eight rungs. **It is four classes of two**, separated
> by 15.3%, 23.7% and 11.0%... I drew a line straight through the biggest gap in
> the set and called the result a continuum."

It also found that its round-one pixel readings had **inverted two pairs** —
reading Neptune larger than Uranus and Venus larger than Earth, where the design
has Uranus larger by 0.13 mm and Earth by 0.17 mm — and noted that its round-one
remark about positions 3/4 and 5/6 being "effectively tied" had not been noise:
*"I had detected the class structure. I found both the ladder and its pairing
cold, and misfiled the second half."*

Asked which of the two candidates is the product's signature, it chose the rank
ladder, on four grounds, the first two of which are about evidence rather than
taste: *"A is in the loop; B is not... A survived contact with an uninformed
observer; B did not. I found A cold and misread B as a defect."*

That second point is worth keeping as a finding in its own right, because it is
this review's sharpest criticism of the mirror and the critic volunteered it
while arguing for the thing the mirror serves:

> "I was shown nine pair frames in round one... I measured feature offsets on
> all nine. I did not once write 'mirror' or 'reflection'. What I wrote was
> 'marking placement is not controlled between copies.' I filed the signature as
> defect 5... It is *verifiable*. It is not *legible*."

## What stands

**One finding, kept in the critic's own corrected words, not blocking.**

> "Rank resolves cleanly into four size-classes separated by 11–24%, and which
> world you are holding is never in doubt. Within a class, size cannot order the
> pair: Uranus and Neptune differ by 0.13 mm and Earth and Venus by 0.17 mm.
> Uranus versus Neptune is the one ordering a player must learn rather than see,
> and the disc numeral that exists to settle it is the thing I was never able to
> read."

And its own deflation of it, offered once it had the real dimensions: the
numeral is about 1.7 × 3.5 mm on the printed part, *"certainly not readable
across a table, but a 3.5 mm engraved numeral is plausibly readable in the hand
— and you pick a piece up to move it, which is exactly when a Uranus/Neptune
question arises."*

**One observation carried open and explicitly out of scope.** At the pair frames
the critic could measure the mirrored lean on Mars and Saturn — polar marking at
−42 against +74 px, and +50 against −95 px, against predictions of ±50 and ±79 —
and could not measure it on Earth, Neptune or Uranus, where it read same-signed
offsets and two rings leaning the same way. It offered the innocent explanation
itself (a lean axis lying near the view direction is invisible at that camera)
and would not withdraw the finding on that account. **This revision did not touch
those three worlds and did not fix this.** The critic ranked five things that
would settle it, cheapest first, and its first is not a picture at all:

> "Read the number, do not render it. Sixteen scalars: the applied obliquity,
> signed, for each of the sixteen world parts... This is the same lesson as R3
> and R4 — a picture is the wrong instrument for a number that is sitting in the
> source, and I have now been wrong twice this review by forgetting that."

Its second is one render per piece down the piece's own disc axis, where an
obliquity of ε displaces the projected pole by R·sin ε and Earth's two armies
would separate by about 80 px.

**Two requirements a picture could not carry, and the critic said so rather than
guessing.** That Jupiter's 3.13° obliquity has not moved: *"A 3.13° tilt shortens
a circle's minor axis by cos 3.13° = 0.9985 — one part in 660... The measurement
is two orders of magnitude below my resolution."* It did rule out a gross
invented lean, measuring a 0.6° differential band tilt rather than 6.26°. And
that the Sol piece is unchanged: *"this requirement is not weakly supported by
pictures, it is structurally uncheckable from them. A picture has no
predecessor."* It named a geometry hash as the honest instrument, which is
`measure/revision-part-hashes.md`.

## And the verdict

**No blocking visual defects, and the critic said plainly that the empty list is
the truth rather than a courtesy:**

> "Everything I could see that bears on the Jupiter change is either correct or
> is a disclosed cost that measures as advertised... The four geometry defects I
> kept into this round have all been settled against me."

**The mirror arrives and it measures true.** Three independent routes to the
same number: 2.05 spot-lengths of travel; Δλ = 30.7° ± 3° from the same-camera
pair; Δλ = 33° ± 6° from the parallax-free orthographic ladders. The design's
figure is 28.46°, and it sits inside both error bars.

**On desirable it did not waver:** *"I said in round two I would pick it up in a
shop and nothing since has moved that; four of my eight concerns have been
retired by measurement and none replaced."*

Its own summary of what these four rounds were worth, which is the last thing it
wrote:

> "if any part of this review is worth carrying forward to the next one, I would
> make it that rather than any of my findings" — that reading a shadowless,
> low-resolution, obliquely-projected render as though it were the thing itself
> is the error that produced four of its eight defects.
