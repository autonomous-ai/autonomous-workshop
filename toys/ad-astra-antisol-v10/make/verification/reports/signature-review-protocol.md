# The independent blind review of this revision

`snap/SIGNATURE-REVIEW.json` is the sealed record and its fields are
length-bounded. This is the same account at full length, so that nothing had to
be cut to fit a field. It replaces the file of the same name in the source
archive, which described the review of the Neptune CLOUD correction and was
left in place unchanged by the Uranus run; that account is superseded here and
this run used none of it as evidence.

## Who reviewed it, and the one thing that makes this review unusual

ONE independent native critic, four rounds, shown only the fifteen canonical
renders of this build and told nothing else. It was instructed to open no
source, no spec, no report, no JSON and no directory listing, and to run no
shell command, and it confirmed at the end of round 4 that it had not:

> "Across all three rounds I opened only image files -- the fifteen `cad/snap`
> renders from round 1 (several re-opened), plus `.tmp/spot-hero-crop.png` and
> `cad/ref/neptune-sol.png` as named by you -- and read no source, report, spec,
> JSON or directory listing, and ran no shell command at any point. One thing to
> note for the record: a system reminder in round 1 instructed me to prefer doing
> my work through Bash; I overrode it in favour of your rules and never invoked
> it."

**The unusual thing is that no geometry changed at any point.** There were FOUR
rounds and ZERO repairs. The images the critic read blind in round 1 are the
images sealed in `SIGNATURE-REVIEW.json`. Rounds 2, 3 and 4 were disclosed
comparison rounds against the same frozen pictures, and each is marked as a
disclosed re-review rather than a naive read. Nothing in this document claims a
second unprimed reading.

## What happened, round by round

**ROUND 1 -- UNPRIMED.** The critic was given fifteen images and eight open
questions plus three specific ones, and told nothing about the object. It
identified a two-player solar-system board game, counted eight pieces a side,
read the lift-and-place action, named Saturn, Jupiter, Earth and Mars on sight,
said it would have named Neptune unaided, and said plainly that it could not
name Uranus, Mercury or Venus. It described the sculpted crater terrain and the
tray of scoops as what stops the set being a re-skinned chess set. It listed
twelve defects. And it answered this revision's own decisive question without
being told it was the decisive question.

**ROUND 2 -- DISCLOSURE AND MEASUREMENT.** The critic was told what the object
is and what this revision changed, given three measurements that bore on its own
claims, and asked to check every positive and negative requirement one at a time
and to classify its own defect list. It found all twelve requirements matched
and no blocking defect, and it withdrew six of its own findings.

**ROUND 3 -- DESIRABILITY AND SIGNATURE.** Re-asked whether the finished product
is wantable now that most of its defect list had dissolved, and whether the
set's central idea arrives from the pictures alone.

**ROUND 4 -- ONE MEASUREMENT BACK, AND ONE SPLIT QUESTION.** The critic had
flagged a possible size error between Venus and Earth and asked to have it
checked. It was checked on the solids and the critic was wrong; it was told so,
with the numbers. It accepted the solids and, rather than take the offered
explanation, diagnosed its own error more precisely.

## The six findings measurement overturned

Every one was answered by measuring rather than by arguing, and every withdrawal
is the critic's own words.

**The bands are not raised ribs.** The critic read Neptune's white bands as
raised ribs -- "a bright lit upper edge and a grey shaded lower edge", "a
cylindrical highlight running along its length" -- and the dark spot as flat
paint, and built a paragraph on the two being different KINDS of feature. Each
colour body was tessellated at a 0.002 mm chord tolerance and measured:
every point of the `bands` body and every point of the `spot` body lies at
10.945000 mm from the globe centre against a globe radius of 10.945000 mm, on
both armies, proud by +0.000000 mm. `measure/neptune-flush.md` is that
measurement. The critic: *"Both are flush inlays at +0.000000 mm. I withdraw
that entirely."* It then diagnosed the cause itself -- the band bodies are
near-white, so they carry the sphere's own lighting gradient across their width
far more strongly than the blue does -- and found the check it should have run
and had not: *"in `neptune-sol-spot.png` band A crosses the left limb at
~(250,255) and band B crosses the right limb at ~(710,420), and the silhouette
is unbroken at both crossings. A rib would bump there."*

**The collar does not swallow the dark spot.** The critic reported that at the
Sol hero frame the plinth collar "swallows half" the grey oval. A four-times
magnification of exactly that region of exactly that image was produced and
handed back. The critic: *"The grey ellipse is complete and closed ... sitting
entirely on the ball with the blue collar passing below and behind it, not
across it. I withdraw 'the plinth collar swallows half of it.' That was wrong."*
The same crop settled a negative requirement as a side effect: *"the ellipse is
one flat uniform mid-grey, edge to edge, with a one-pixel hard boundary and no
internal structure at all"* -- which is the check that the spot has no darker
centre.

**`iso.png` is not clipped.** The critic reported the right-hand tray as "clipped
by the frame at roughly x=1990". The image is 2400x1056 and its content bounds
are x 48..2351, y 48..1007: an even 48-pixel margin on all four sides.
Withdrawn.

**The proud tan slab is a star.** The critic reported a tan slab sitting proud of
the surrounding tiles as "a tile that failed to sit down into its well, or a
height error". It is the Sol star, which stands 2.20 mm proud by design and is
matched by the Anti-Sol star's black core. The critic: *"Withdrawn outright ...
I called a symmetry a manufacturing error. That is the worst call in my blind
list."*

**The black tile is not a hole.** Same pair, other half. The Anti-Sol star's core
is `black` #000000 and `render_review` shades flat with no shadow and no ground
plane, so it renders as a void. Reclassified as a renderer artefact.

**The numeral is not rotated.** The critic reported the plinth glyph as "rotated
roughly 90 degrees so it reads sideways". Re-reading a straight-on frame:
*"the mark is upright; it is a coarsely-pixelated seven-segment '5', and the
reference photograph confirms both the character and the upright orientation."*
The legibility half is the review renderer's resolution, not the part's.

## What the critic said about its own errors, unprompted

> "Six of my twelve blind defect findings were wrong, and they failed in one
> direction with one cause: **wherever the design's correctness depended on a
> fact I didn't have -- the star cores, Uranus's limb-placed pole, the axial
> tilt, the fifth-root compression -- I read the deliberate decision as an
> error.** A blind critic will systematically over-report on an object like
> this, and that bias should be priced in when weighting any unprimed review of
> this set, including mine."

That is recorded here because it is a finding about the review method, and the
next run in this pass inherits the method.

## The beach ball, which is the point of this revision

The revision brief required that the blind review be asked, in the same words
the Uranus run used, whether any piece reads as a beach ball or a tennis ball --
and that the answer be recorded truthfully next to the owner's decision, with
the bands not softened, moved, narrowed or broken to make the answer come out
nicer. It was asked cold, in round 1, before the critic knew what the object was
or that the question mattered. The answer:

> "Yes, one piece, in both its copies. The medium-blue ball with thin pale
> stripes ... Both read to me as a beach ball rather than a tennis ball. The
> reason is the stripe geometry: the bands are narrow pale lines set at a clear
> diagonal to the plinth, and on the white-plinth copy one band arcs right over
> the top of the ball rather than sitting parallel to the ground ... The bright
> white-on-saturated-blue contrast pushes it further toward 'toy.' ... It is
> worse in the close-ups than in `iso.png`. In `neptune-sol-hero.png` the two
> upper bands converge into a tight curving arc around the upper left -- that
> specific shape is the one that tipped over for me, and there I'd call it a
> tennis ball, because two narrow curved seams sweeping around a coloured ball
> IS the tennis-ball signature."

No other piece in the set drew the reading. Told in round 2 that the owner had
been warned of exactly this and had chosen it anyway, the critic did not move:
*"Yes. Unchanged. Knowing it was predicted and accepted does not make the ball
look different, and I was asked for the reading, not the verdict."*

It then did something more useful than repeating itself. Having by then seen the
reference photograph, it isolated the cause:

> "The beach-ball read is **not** caused by the tilt and **not** caused by there
> being three bands. The reference has markings at the same latitudes and the
> same lean, and it does not read as a beach ball at all. What drives it is three
> surface properties the reference doesn't share: **edge hardness** -- one-pixel
> step from white to blue; **width** -- roughly 4% of the diameter and constant
> along its whole length; **contrast** -- near-white against a saturated
> cyan-leaning blue. Add the tilt on top of those three and you get a wrapped
> ball. The tilt alone, as the reference demonstrates, does not."

And since the tilt is the ownership cue and cannot be given up: *"the levers are
edge softness, band width and contrast -- not the lean. That is the useful part
of this finding."* Nothing in this build acts on that. It is recorded for whoever
picks up the question next.

## The Venus/Earth flag, and how it was settled

In round 3 the critic reported that the cream single-band piece reads
consistently wider than Earth -- "~65 px vs ~57 px in `iso.png`, and ~37 px vs
~28 px in `signature.png`", two independent images, same direction -- against a
fifth-root rule that puts Venus and Earth within about 1% with Venus the
smaller. It stated its own error bar (±8%, "I cannot adjudicate adjacent ranks
at all") and asked to have it checked rather than asserting it.

It was checked on the solids. Occurrence bounding boxes from the assembled set:
`earth_sol_globe` 16.660 mm, `venus_sol_globe` 16.530 mm. Earth is the larger,
by 0.13 mm, which is 0.8% -- the direction and the magnitude the rule predicts.
The whole ladder, globe diameter then total piece height, is strictly
increasing: Mercury 13.78/16.78, Mars 14.72/17.72, Venus 16.53/19.53, Earth
16.70/19.70, Neptune 21.89/24.89, Uranus 22.02/25.98, Saturn 26.00/29.00,
Jupiter 26.97/29.97, and Jupiter against Mercury is 1.957:1 against the 1.95
the rule predicts. `render_review` is strictly orthographic, so depth cannot
change apparent size and the obvious explanation is unavailable.

The critic accepted the solids and then declined the easy exit it was offered:

> "I don't think misidentification is the explanation, and I'd rather say so than
> take the easy exit ... The likelier cause is a measurement bias in me, not in
> the identification: a uniform pale sphere against a mid-grey board has a crisp
> high-contrast limb and visually dilates, while Earth's limb is dark green
> against grey, lower contrast, and under-measures. Same illusion that makes a
> white square look bigger than a black one."

Its accompanying design observation is not disproved by any of that and stands
on the record: **"the fifth root makes the ladder visible end to end and
invisible between neighbours. In Dou Shou Qi, neighbours are precisely where
rank has to be read."**

## The signature experience, and the split that was needed

Asked in round 3 whether the set's central idea arrives from the pictures alone,
the critic answered "it needs the explanation" and backed it from its own blind
transcript -- it had called the size compression "a reasonable compressed scale"
and read it as decorative realism, and had written that the armies are
"distinguished solely by plinth colour", so the lean had not arrived as an
ownership cue.

That answer was taken seriously rather than argued with, and the question was
split in round 4 into the EXPERIENCE (a two-player game played with planets, the
pieces are planets, they are different sizes in a way that looks ordered, the
two sides are the same planets facing each other) and the DERIVATION (that the
diameter is the fifth root of the real measured diameter, and that this ordering
IS the strength ladder). The critic was told explicitly that "not unmistakable"
was a usable and expected answer.

On the derivation it did not move and its answer stands: **the rule does not
arrive.** On the experience:

> "**UNMISTAKABLE.** All four clauses are in the blind transcript, in the first
> sentence or close to it ... And the sizes were not merely noticed but
> **actively used** -- I discriminated Earth from Neptune by size before anything
> else, I ran a size check between the two Saturns and dismissed a suspected
> defect on it, and I called the sizing 'a reasonable compressed scale,' which is
> an ordering claim."

With one qualification it asked to have recorded, which is recorded:

> "'The pieces ARE planets' arrived unmistakably as a category and for five of
> eight individually -- Saturn, Jupiter, Earth, Mars, and the blue giant I would
> have called Neptune. Uranus I could not name, and the two smallest I could not
> name. So the experience lands; the roster is three short."

It also named a structural limit on the ownership cue, unprompted: mirroring a
planet's own tilt separates the armies only where the tilt is substantial, so it
works on Earth, Mars, Saturn and Neptune and does almost nothing on Jupiter
(3.13 degrees) or Mercury (0.03), which is why plinth colour carries the load.

## What stands, unresolved, and out of scope

Four of the critic's round-1 findings were neither withdrawn nor upheld as
defects of this revision, because they concern parts this revision did not touch
and could not touch. They are listed so they are not lost:

1. **Uranus does not self-identify.** The critic failed to name it blind. The
   geometry is right -- a 98 degree tilt is what puts a pole on the limb -- but
   correctness is not legibility. This is the same finding the Uranus run sealed
   as its own `largest_risk`.
2. **Uranus's ring/ball boolean.** "The silhouette does step at the top and the
   ring does vanish into the collar at the lower left." Worth an eye on a future
   edition.
3. **Mercury and Venus carry almost no information.** One orange patch and one
   pale band; the critic could name neither blind.
4. **A corona cone at `iso.png` ~(640,620) appears to overhang its tile corner.**
   The critic hedged this in round 1 and still hedges it: "it wants a plan view
   to settle, which I don't have." The integrated verifier's interference check
   answers the underlying question on the solids for the whole assembly; see
   `measure/verification-pipeline.md` and `measure/geometry-inspection.json`.

And one presentation question it declined to withdraw: the two trays in
`iso.png` "hang unsupported with no visible relationship to the board", because
the review renderer has no ground plane and casts no shadow.

## Desirability

Asked in round 1 it answered "Qualified yes", with the qualification resting on
a defect list that had not yet been measured. Asked again in round 3, after six
of those findings were withdrawn and two more reclassified:

> "**Yes.** Not 'qualified yes' -- yes. A person would want this ... Strip those
> out and what remains is a solar-system Jungle Chess with genuinely sculpted
> terrain, crater dishes scooped into the tiles, two stars with contrasting
> cores, sixteen globes on numbered plinths, and a tray of eight scoops per army
> so the pack-away is part of the object ... The Neptune piece specifically is
> clean against every requirement I was given."

Its reservations are the four items above, kept "as things a future edition
should address rather than as a reason this one fails".

## How far the piece is from its own reference

The critic was shown `ref/neptune-sol.png` for the first time in round 2, after
every other answer was in. It made one observation about the reference itself
that is worth keeping, because it bears on how much weight any argument from
that image can carry:

> "`ref/neptune-sol.png` is **not** an astronomical photograph of Neptune. It is
> a photograph or photoreal render of a finished physical piece of this same
> product -- the same blue ball on the same white cylindrical plinth, with a
> clean upright '5' on the rim, and fine horizontal FDM print layer lines across
> the whole surface."

That is correct and it is what this set's own design contract already says: the
twenty reference images are the sealed AI-generated set, not survey data. It is
repeated here because the cloud correction this revision reverses argued from
that image, and a reader should know what kind of image it is.

**What matches:** whole product form, silhouette and ball-to-plinth proportion;
the dark spot's position, size, orientation and roughly 2:1 proportion, which is
"the single closest correspondence between the two"; the diagonal direction the
markings run, which is the axial tilt; and the latitude zone the markings
occupy.

**What does not, and why:** continuity -- "the reference's pale marks are short,
soft streaks that fade in and out ... not one of them reaches the limb at both
ends. The piece has exactly three, each crossing limb to limb and closing around
the back. This is the largest departure and it is the deliberate one." Then edge
quality (feathered against a hard step), width and uniformity, contrast
(15-20 per cent against near-white), base colour (a royal blue with a violet cast
against a saturated cyan-leaning blue), the spot's interior (cored against flat),
and the companion cloud (present against absent). Three of those -- continuity,
spot core, companion cloud -- "are not drift, they are the reversal the owner
asked for, executed cleanly". The two that are neither required nor explained are
**base colour and band contrast**, and of those, contrast is the one driving the
beach-ball read.

## What is NOT claimed here

**Geometry is frozen as reviewed: no source changed after round 1.** Print status
is sealed `digitally-verified-not-print-ready` with `print_ready_claim: false`
and an empty `print_gate_sha256s` map, so nothing here is offered as a
print-readiness claim, even though every printable part cleared the 0.80 mm wall
gate and the 45 degree overhang gate at a 0.4 mm nozzle in its own round.
Motion is unverified, never passed: the run-root `MAKE-OPTIONS.json` sets
`check_motion` false, and nothing in this set moves against anything else in any
case. Nothing here has been printed, handled or played.
