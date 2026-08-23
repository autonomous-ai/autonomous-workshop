# BOARD — Lessons Learned

This file is the persistent memory of the `/goal` self-improvement loop for
`board-game-ideator`. `board-game-evaluator` appends to it every turn;
`board-game-ideator` reads it every turn and, in revise mode, folds it into
its own standing "Learned Heuristics" section
(`.claude/agents/board-game-ideator.md`).

## Pivot (before Turn 5)

The product category changed: this pipeline used to ideate **3D-printed
accessories for existing games** (organizers, dials, trays), scored on a
Demand/55 + Differentiation/15 + Margin/15 + Producibility/15 rubric.

As of Turn 5 it ideates **complete, original, manufacturable board games**
— each idea must be a whole playable game (concept, full rules, full
component/manufacturing bill), not a part or add-on. Anything that isn't a
complete playable game now scores a flat zero. The rubric is now
**Differentiation/40 + Demand/20 + Fun factor/20 + Producibility/20**
(margin was dropped; producibility no longer scores rulebook production,
only physical CAD-printable components), with a hard rule capping
style-only reskins at 2 per batch of 10 (any beyond that score 0/40 on
differentiation).

Turns 1-4 below are retained for provenance but scored a different product
category under a different rubric — **their numbers are not comparable to
Turn 5 onward**, and `board-game-ideator`'s Learned Heuristics section was
reset accordingly (see the "Pivot note" at the top of its Learned
Heuristics). The Score History table below starts a fresh block for the
new rubric.

## Score History

### Archived — old accessory rubric (Demand/55, Differentiation/15, Margin/15, Producibility/15)

| Turn | Avg Total /100 | Avg Demand /55 | Avg Differentiation /15 | Avg Margin /15 | Avg Producibility /15 |
|------|-----------------|-----------------|---------------------------|------------------|--------------------------|
| 1 | 67.2 | 36.7 | 7.6 | 11.8 | 11.1 |
| 2 | 64.8 | 35.4 | 5.6 | 11.5 | 12.3 |
| 3 | 61.4 | 30.0 | 8.7 | 10.5 | 12.2 |
| 4 | 71.3 | 36.4 | 11.5 | 11.1 | 12.3 |

### Current — complete board game rubric (Differentiation/40, Demand/20, Fun/20, Producibility/20)

| Turn | Avg Total /100 | Avg Differentiation /40 | Avg Demand /20 | Avg Fun /20 | Avg Producibility /20 |
|------|-----------------|----------------------------|------------------|---------------|--------------------------|
| 5 | 70.1 | 26.0 | 13.5 | 15.3 | 15.3 |
| 6 | 70.8 | 24.0 | 15.1 | 14.8 | 16.9 |
| 7 | 75.4 | 27.3 | 13.7 | 16.4 | 18.0 |
| 8 | 70.1 | 27.4 | 12.3 | 15.6 | 14.8 |
| 9 | 75.2 | 26.0 | 16.0 | 15.0 | 18.2 |
| 10 | 67.0 | 20.7 | 15.4 | 15.7 | 15.2 |

### Archived — CAD-build rubric with Buyability (Differentiation/50, Producibility/40, Buyability/10)

Turns 11-13 scored under this rubric. Producibility and Buyability were no
longer text-based estimates — they came entirely from a real CAD build
(submitted to the production text-to-CAD pipeline) and a real 20-persona
purchase-intent panel, for whichever 3 ideas the ideator named in
`cad_build_picks`. The other 7 ideas each turn still got a
Differentiation/50 score for lessons-learned purposes but never a
Total/100.

| Turn | Avg Total /100 (over completed builds) | Avg Differentiation /50 (of the 3 built) | Avg Producibility /40 (0 for non-done) | Avg Buyability /10 (0 for non-done) | Builds completed |
|------|-------------------------------------------|---------------------------------------------|--------------------------------------------|-----------------------------------------|-------------------|
| 11 | 52.0 | 37.0 | 7.3 | 0.0 | 1/3 |
| 12 | 51.0 | 34.0 | 7.0 | 0.0 | 1/3 |
| 13 | 56.9 | 35.7 | 7.6 | 0.0 | 1/3 |

**Why Buyability was dropped (2026-08-11):** all three turns above
produced a unanimous 0/20 purchase-intent verdict on the single completed
build each turn, and the panel's stated reasons were overwhelmingly about
the *photo* (unpainted/monochrome prototype, fused/missing parts) rather
than the underlying game concept — i.e. the panel was mostly re-detecting
the same fidelity defects Producibility's own concept-fidelity score
already caught, not adding independent desirability signal. The panel is
paused (not deleted) until CAD-build fidelity improves enough to produce a
photo worth judging; `board-game/tools/customer_personas.json` and the
`/goal` step that spawns the 20 persona agents both still exist for when
it's re-enabled.

### Archived — never used (Differentiation/50, Producibility/50)

Defined for Turn 14 but superseded before any turn ran under it, by the
vision-fidelity rubric below.

Producibility absorbed Buyability's former 10 points (0-25
Printability + 0-25 Concept fidelity, both scaled up from /20 each). "Avg
Differentiation (built)" below is the average Differentiation score of the
3 `cad_build_picks` specifically (not all 10); "Avg Producibility"
averages in a 0 for any pick that didn't reach `status: done`, per the
hard gate; "Avg Total" is computed **only** over builds that reached
`status: done` (see each turn's SCORES.md for the exact reasoning) — these
are two different denominators by design, both reported so the
CAD-pipeline pass rate is never hidden inside a diluted average.

| Turn | Avg Total /100 (over completed builds) | Avg Differentiation /50 (of the 3 built) | Avg Producibility /50 (0 for non-done) | Builds completed |
|------|-------------------------------------------|---------------------------------------------|--------------------------------------------|-------------------|

### Current — vision fidelity (Fidelity/60 + Reliability/25 + Ambition/15)

From Turn 14. The loop stopped asking "would this sell?" and started asking
"did the built object match the vision it was designed from?" — because
turns 11-13 showed the binding constraint was the vision→CAD gap, not idea
quality: 5 of 9 builds parked on clarifying questions and scored zero, and
the ones that finished came back with parts fused and components missing.

Three ideas per turn (one `new`, one `twist`, one `reskin`), all built.
Differentiation is now a one-search pass/fail gate, not a scored axis.
Colour is gone entirely from the pipeline — the CAD stack has no
colour-assignment step, so distinction must be carried by geometry.

"First-shot survival" is the headline number: the rank-weighted fraction of
each idea's five `must_survive` conditions that the **first** build
satisfied, before any repair round. The stopping condition is two
consecutive turns with every idea at ≥80%, not an average — an average lets
one clean reskin carry two failures, and what is being proven is
reliability.

| Turn | Avg Total /100 | Avg Ambition /15 | First-shot survival | Builds completed | Questions asked |
|------|-----------------|--------------------|----------------------|-------------------|------------------|
| 14 | 80.68 (1 counted idea) | 11.3 (all 3) | 80% (counted idea); 27% (all 3, incl. 2 pre-build failures) | 1/3 | 3 (1 per idea, all only reached concept-selection) |
| 15 | 62.23 (1 counted idea) | 10.0 (all 3) | 53% (counted idea); 18% (all 3, incl. 2 pre-build failures) | 1/3 | 3 (1 per idea; idea 3 needed a 2nd submission) |

## Lessons Learned

_Turns 1-4 below were written for the retired accessory-product pipeline
and are kept for provenance only — `board-game-ideator`'s Learned
Heuristics no longer draw on them (see the Pivot note above). Turn 5
onward reflects the current complete-board-game rubric._

### Turn 1

**Differentiation is the systemic weak point, not demand.** Average differentiation
landed at 7.6/15 — the lowest-scoring category by a wide margin, and 6 of the 10
ideas scored 6/15 or lower there. In almost every one of those cases, a direct
targeted search (not just a category search) turned up an existing product doing
essentially the same thing: a "Pro" no-cube player board for Terraforming Mars, a
BGHQ token upgrade set for Root, magnetic modular MTG deck boxes already sold on
Etsy, magnet-ready miniature bases as a saturated Etsy category, lazy-Susan poker
chip caddies as an established (if usually non-printed) product, and multiple
existing "catapult" dice towers. Pattern: verifying *demand* for a named game/trend
is not the same as verifying that *this specific mechanism* is unclaimed — before
finalizing an idea, search for the mechanism/feature itself (e.g. "magnetic
modular deck box," "catapult dice tower," "Root token upgrade"), not just the
game name plus "accessory" or "organizer." A demand search proves people buy in
this category; a differentiation search has to independently prove nobody's
already selling this exact angle.

**Rationale claims need to survive a direct search, not just sound plausible.**
Idea 4's core demand claim (a TikTok/Instagram-driven cribbage resurgence) and
idea 6's core demand claim (Root's cardboard tokens are a "frequently cited
complaint") both failed verification — in idea 6's case, the search evidence
actively contradicted the claim (reviews described Root's components as good
quality). Per the rubric, unverifiable trend claims cap demand at 25/55, and both
ideas landed in the bottom three as a result. Going forward: if a rationale cites
a "trend" or "frequently cited complaint" as its main demand evidence, that's
the single highest-value thing to pre-verify before finalizing the idea, because
it's an all-or-nothing gate on the biggest scoring category.

**What the top scorers did right, worth repeating:** Ideas 1 (Catan dial tray, 80)
and 2 (Wingspan birdhouse sorter, 75) both anchored demand in a specific,
independently-verifiable fact (an active, named Etsy search category / a
documented aftermarket-upgrade fanbase for that exact title) rather than a general
"this genre is popular" claim, and both proposed a genuinely narrow, checkable
feature gap (rotating bonus-card dials; a closable birdhouse roof) rather than
reinventing an entire product category. Idea 5 (accessibility card holder, 74)
had the cleanest producibility profile in the set — one part, no assembly, exactly
one dimension flagged as critical — which is the template for producibility
scoring: fewer parts and an explicit, narrow tolerance call-out beats an elaborate
multi-part mechanism every time on this axis.

**Producibility risk to watch: printed-only mechanisms replacing hardware.** Idea
3's printed-flexure "torsion spring" catapult (no metal spring) and idea 9's
220mm rotating disc on a printed friction pivot (no bearing) both took on real
reliability risk to avoid a hardware part. When a mechanism's function depends on
a single thin, fatigue-prone printed feature or a bare plastic-on-plastic bearing
surface at a large diameter, either spec a hardware insert (spring, bearing,
elastic band) or size the risky feature with a wide safety margin and say why —
don't just declare a critical dimension and move on.

### Turn 2

**Differentiation got worse, not better (7.6 → 5.6/15), despite Turn 1's explicit
warning to search the mechanism, not just the game/category.** This is the most
important regression to fix. Six of ten ideas this turn made a confident,
specific differentiation claim ("Search confirms every existing X requires Y" /
"no existing design combines A and B") that a direct search *directly
contradicted* — not just found adjacent competitors, but found the near-exact
product already shipping free:
- Idea 1 claimed existing Everdell prints are storage-only; MakerWorld's free
  "Everdell - resource holders" set already includes a literal tree-trunk resource
  holder, and Printables' card holders are already in-play browsing aids.
- Idea 3 claimed all folding dice towers require glued-in magnets; multiple
  existing print-in-place towers ship with zero magnets and zero hardware already
  ("Collapsible Dice Tower" literally advertises "no magnets, no clips").
- Idea 6 claimed no card holder combines two racks with a privacy divider;
  MakerWorld's "Playing card holder (divideable)" is already described as exactly
  that ("curved... so other players cannot see your cards").
- Idea 7 claimed every dungeon-tile system needs user-installed magnets/pins;
  OpenLOCK's clip system is an established, actively-used magnet-free connector
  standard in that exact hobby.
- Idea 10 claimed existing deck-box systems are fixed-capacity, not expandable;
  MakerWorld's "Stack Box Infinite" uses nearly identical marketing language
  ("combine with any number of others — as tall, as wide, and as colorful as you
  want") to what the idea itself proposes as its innovation.
Pattern: these searches were confidently *asserted* in the rationale text but
evidently either not run against the specific mechanism/wording, or run and their
top hits not read closely enough to notice the near-exact match. Going forward:
before writing "search confirms no existing design does X," the search actually
has to be for that specific claim in a form that would surface the counterexample
(e.g. "dice tower no magnets", "modular deck box expandable", "dungeon tile clip
no magnet") — and if a close match turns up, either drop the idea or reframe the
differentiation around the narrower thing that's genuinely still missing (see
idea 2 below for how to do this correctly).

**Unverifiable trend claims are still slipping through as the primary demand
hook.** Idea 8's rationale leaned on "2026 cozy/filler-game coverage repeatedly
highlighting" a growth segment for small-box filler games — a search for that
specific claim turned up nothing supporting it, and it became the lowest score
of the turn (55) as a direct result. This is the same failure mode flagged in
Turn 1 (idea 4's cribbage TikTok claim, idea 6's Root complaint claim): a
plausible-sounding trend citation is not evidence. If a genre-wide "coverage
highlights this" claim can't be traced to an actual named article/list, cut it
and lean on a narrower, independently-checkable fact instead (an active Etsy
search category, a documented fanbase, confirmed publisher revenue) the way
idea 2 did with the cozy-game trend.

**What the top scorer (idea 2, Cozy Games Nesting Hex Canister Set, 72) did
right: it scoped differentiation narrowly enough to survive contact with
search.** Its claim wasn't "no hex token storage exists" (false — HexNest and
hex stacking bowls already exist) but implicitly the more specific "closed-lid,
graduated-size, nest-to-one-volume travel format" — a real, narrower gap that
search did not contradict. The lesson from Turn 1 ("verify the mechanism, not
just the category") needs a companion rule: **the narrower and more specific
the differentiation claim, the more likely it survives a search** — broad
absolute claims ("every existing design requires...", "no existing product
combines...") are the ones getting falsified. Idea 9 (turn-order carousel, 67)
also avoided contradiction by claiming differentiation on a specific *combination*
of features (fold-away arm count + dual current/next indicator) rather than
the whole product category, and its claim held up under search.

**Producibility watch-item this turn: idea count of independent risky joints,
not just presence of one.** Idea 9's 6 separate print-in-place hinge-and-detent
joints on a single build (vs. idea 3's 4 hinges or idea 1's single friction-fit)
is a materially higher-risk mechanism than anything flagged in Turn 1, and the
producibility_notes didn't call out the compounding risk of needing all 6 to
print cleanly. When a design has N repeated risky joints, the failure
probability compounds — call out N explicitly and consider whether a
lower-joint-count alternative gets 90% of the value.

### Turn 3

**Differentiation improved on average (5.6 → 8.7/15) but two ideas still made
absolute "nobody does this" claims that a single direct search falsified —
both landed in the bottom three as a result.** Idea 4 claimed no turn-order
tracker lets a buyer add/remove player-count segments on a shared hub; Etsy's
"Modular D&D Initiative Tracker" already does exactly that (snap-together
segments, described by the seller as scaling from solo to 8-player). Idea 10
claimed existing con-badge attachments are fabric/paper ribbons only, not rigid
3D printed charms; Etsy already sells a "3D Printed Meeple Lanyard Name Badge
... Personalised" explicitly marketed for "gaming shows and conventions," plus
D20 dice charms and meeple lanyard charms in the same space. Both failures
follow the exact Turn 2 pattern: a confident absolute claim ("no result
offered...", "existing badge ribbons are... not rigid 3D printed charms")
that a search *for that specific product type* (not the game/genre name)
immediately contradicts. The fix from Turn 2 — narrow the claim to a specific
sub-feature, and if a close match turns up, either drop the idea or reframe
around the genuinely-missing sliver — is being applied inconsistently: 8 of
10 ideas this turn did scope narrowly and survived search (see idea 1's
clip-retrofit vs. full-deck-replacement framing, or idea 9's institutional-
audit framing vs. hobbyist organizers), but the 2 that didn't scope narrowly
still slipped through to the prompt-writing stage instead of being caught
before finalizing.

**A verified true fact is not the same as a verified demand link — check the
argument, not just the citation.** Idea 4's rationale cited a real, checkable
fact (Rebirth won Kennerspiel des Jahres 2026, confirmed via ICv2/BGG/
wericmartin.com) but used it to support an unrelated claim (that a cyclical-
theme award winner creates demand for a generic turn-order-wheel accessory).
The fact-check passed; the argument it was supposed to support didn't follow
from it. Going forward, when citing a trend/award/fact as demand evidence,
the question to ask isn't just "is this fact true" but "does a person who
knows this fact actually become more likely to buy this specific product" —
if the link is inferential rather than direct (award-winner's mechanic vs.
a generic accessory, rather than e.g. a documented fanbase for that
accessory type), treat it as weak evidence even though it's a true citation.

**Margin declined this turn (11.5 → 10.5/15), concentrated in three
institutional/epic ideas with long print times relative to price: idea 7
(140g/5hr for $27), idea 9 (180g/6hr for $32), and idea 5 (90g+hardware/4hr
for $24).** None of these ideas' margin_case sections did the arithmetic of
print-hours-to-price the rubric asks for explicitly — idea 7 justified its
price against the *base game's* $80-100 price point rather than against its
own 5-hour print cost, and idea 9 assumed a $32/unit institutional price
without accounting for the bulk-discount expectations of institutional
buyers. Pattern: when a margin_case cites the buyer's general willingness to
pay (for the base game, for the category) instead of a print-time-vs-price
ratio for *this specific object*, that's a sign the price hasn't actually
been stress-tested against the object's own cost — flag it explicitly when
print time exceeds ~3 hours.

**What the top scorers did right, worth repeating:** Idea 1 (Tactile Suit-
Rank Corner Clips, 66) scoped its differentiation claim to one narrow
mechanism (a detachable per-corner retrofit clip, not accessible card
products broadly) and it survived multiple direct searches intact — the
model for how to phrase a differentiation claim so it's falsifiable and
still true. Idea 9's institutional-audit framing (library/game-cafe piece-
count verification, not permanent home-storage optimization) similarly
carved out real unclaimed territory in an otherwise saturated organizer-
insert space by picking a different buyer and use case, not just a different
shape. On producibility, ideas 1, 6, and 8 continue the pattern from Turns
1-2: many small identical parts or a single flex joint, with one explicit
critical tolerance called out per part type, consistently scores 12-13/15 —
this is now a proven, repeatable template and should stay the default shape
for new ideas rather than an occasional choice.

### Turn 4

**Demand jumped sharply (30.0 → 36.4/55) because this batch mostly cited
independently-checkable, hard numbers instead of trend language — but two
ideas still slipped back into the exact failure modes Turns 1-3 warned
about.** Eight of ten ideas grounded demand in a verifiable fact that
search actually confirmed: Catan's 32-45M copies sold (NPR/publisher),
Monopoly's 275M-copy Guinness record, Terraforming Mars's BGG top-10 rank,
Splendor's 2014 SdJ nomination, Ticket to Ride's 2004 SdJ win, Root's
active expansion line, and Dominion's real 2023-24 Rising Sun expansion
all checked out exactly as claimed. This is a real, measurable improvement
in citation discipline and should be reinforced as the default. But idea 6
(Pandemic) cited "well over 8 million units sold" when the only verifiable
figure (Z-Man's own 2021 release) is 5 million — a specific, checkable
number that was simply inflated, the same failure class as Turn 1-3's
trend claims, just with a fabricated statistic instead of a fabricated
trend. And idea 10 (playmat wind clips) built its demand case on a search
engine's own hedge ("may still be a niche product opportunity") — treating
an admission of inconclusive evidence as if it were supporting evidence,
rather than applying the cap the rubric calls for when a search is
inconclusive. Rule to add: before citing a specific number (sales figures,
unit counts, membership counts) as demand evidence, that number itself
needs a direct search hit, not just the game/publisher name — a real
publisher and a real game don't guarantee the specific figure attached to
them is real.

**A verified fact can still support the wrong kind of demand link — watch
for indirect-audience mismatches, not just false facts.** Idea 4 (chess
capture tray) cited real, current, well-sourced numbers (Chess.com's 200M+
registered users, the confirmed Queen's Gambit signup spike), but those
numbers describe *online* chess growth being used to justify demand for a
*physical, over-the-board* accessory — the same "true fact, weak argument"
gap flagged in Turn 3 with the Rebirth/turn-order-wheel case. Going
forward, when a demand citation is about digital/online engagement, treat
it as only partial evidence for a physical-accessory product unless the
rationale also cites physical-accessory buying behavior specifically (as
idea 4 separately did with the $15-200 chess-set market, which is why it
wasn't scored down further).

**Margin regressed to its lowest point yet (11.5 → 11.1/15), and the cause
is now a clearly repeating pattern across three separate ideas rather than
an isolated case.** Ideas 7 (Root, 5hr/$28 four-pack), 8 (Monopoly, 5hr/
$26), and 9 (Dominion randomizer, 5hr/$27) all have print times over 3
hours and all justify their price exclusively by citing the buyer
segment's general willingness to pay for the *category* (Etsy upgrade
accessories, banker-tray accessories, organizer boxes) rather than doing
the print-time-to-price arithmetic for *this specific object* that Turn 3
explicitly asked for. This is the single most important miss this turn:
Turn 3's lesson named this exact pattern and it was not applied in the
following turn's revise pass. Standing heuristic to make non-optional
going forward: any idea with a print time over 3 hours must state its
per-hour revenue (price ÷ print hours) explicitly in the margin_case and
argue why that rate is acceptable, not just cite what similar accessories
sell for.

**Producibility's one low score (idea 9, Dominion randomizer, 9/15) is the
same unmitigated printed-mechanism risk flagged in Turn 1 and still
unresolved three turns later.** A 150mm drum rotating on a bare printed
axle-in-housing bearing (no hardware insert) plus a 1mm spring pawl
expected to survive repeated engagement against 40 notches is exactly the
"printed-only mechanism replacing hardware" pattern Turn 1 said needs
either a hardware insert or an explicit wide-safety-margin justification —
neither was provided here. This should be treated as a hard rule now, not
a repeated observation: any drum/wheel over ~100mm diameter on a printed
bearing surface either specs a hardware insert or is downgraded.

**What the top scorers did right, worth repeating:** Idea 8 (Monopoly
carousel, 82) and idea 2 (Catan tray, 82) both paired a top-tier,
independently-confirmed mass-market demand fact with a differentiation
claim narrow enough to survive search intact (search explicitly reported
"no rotating carousel found" for idea 8), continuing the Turn 3 lesson
that specificity is what makes a claim falsifiable-and-true rather than
falsifiable-and-false. Idea 3 (Splendor privacy shield, 75) and idea 4
(chess tray, 70) both kept producibility near-ideal with 1-2 jointless or
single-hinge parts and one explicit critical tolerance — this remains the
most reliable path to a high producibility score and should stay the
default shape rather than something only some ideas reach for.

### Evaluator Reliability Check (ad-hoc, post-Turn 4)

**Correction: idea 2's Turn 4 score (Catan Probability Rack, 82) overstated
differentiation because the original search missed direct prior art.** An
ad-hoc test re-scored Turn 4 ideas 2 and 8 three times independently, same
inputs, same rubric, fresh WebSearch each time. All 3 reruns converged on a
materially lower differentiation score for idea 2 (7-8/15 vs. the recorded
9/15) because every rerun's search — phrased around the literal claimed
mechanic ("Longest Road Largest Army tracker") rather than the original
search's generic phrasing ("Catan harbor tile rack flip lock") — surfaced
existing prior art the Turn 4 evaluation missed: Cults3D's "Longest Road &
Largest Army" tracker and MakerWorld's "Compact Catan - Fixed Largest Army
& Longest Road." Idea 8 also reran 7-10/15 vs. the recorded 13/15, though
less conclusively contradicted (no single named competitor found, just a
generally more crowded banker-tray category than the Turn 4 note implied).
Total scores for both ideas landed 13-18 points *lower* than recorded, in
every rerun — a consistent, one-directional gap, not random noise.

**The lesson: for this pipeline, search-query phrasing is the dominant
source of score inconsistency, not sampling randomness in the scoring
step itself.** Three independent reruns of the same idea, same rubric,
landed within a tighter band of each other (diff spread ~1-3/15, total
spread ~5-8/100) than any of them landed versus the original Turn 4 score
— because they all happened to search the specific named mechanic, while
the original search used a broader/different phrase and never surfaced
the counterexample. A single search miss is enough to inflate a
differentiation score by several points and the total by well over 10.
Standing rule added to `board-game-evaluator.md`: for every
differentiation claim, search the literal named mechanic/feature
combination from the idea itself (not a generic category phrase), and run
at least two differently-worded queries per claim before concluding "not
found."

### Turn 5

**First turn under the new complete-board-game rubric: differentiation
averaged 26.0/40 (65%), and the two lowest-differentiation ideas both
failed for the exact reason the Turn-4 Evaluator Reliability Check
predicted — a single-phrasing search missed prior art that a differently-
worded query on the claim's own terms found immediately.** Idea 4 (Depth
Chase)'s search for "hidden movement board game modular board sonar dial
tracker" missed **Specter Ops** (Plaid Hat Games), a shipped hidden-
movement pursuit game with an explicitly modular board — found instantly
by rephrasing to "hidden movement pursuit game rotating dial zone
tracker." Idea 8 (Cairn Climbers)'s search for "shared tilting platform
multiple personal towers stacking dexterity board game" missed **Gravity
Warfare**, a shipped dexterity game with a shared spin/tilt platform and
individually-owned player pieces — found by the *same query wording*,
just run independently rather than accepted from the idea's own claim.
Both ideas ran only their stated search and didn't verify with a second,
differently-angled query before writing "not an existing shipped
product." This is the identical failure mode the post-Turn-4 reliability
check diagnosed in the ideator's own search discipline, not just the
evaluator's — the ideator needs to internalize "run 2+ differently-worded
queries per claim" as a hard step in its own idea-finalization process,
not something only the evaluator does after the fact.

**Demand's lowest score this turn came from a checkable fact simply being
wrong, not from vagueness or an inflated trend.** Idea 2 (Gearform) stated
"Azul won the 2017 Spiel des Jahres" — it won in 2018 — and additionally
described Sagrada and Calico as being "across its line" with Azul, when
both are unrelated games by different designers/publishers merely sharing
a genre. Neither error was hard to catch (both resolved on the first
search), which means this wasn't a case of unverifiable trend language
slipping through (the Turn 1-4 recurring failure) but a plain factual
error in an easily-checkable, specific, named claim. Standing heuristic to
add: award/year claims and "same product line" claims are exactly as
checkable as sales figures and need the same one-search verification
before being written into a demand_case — don't reserve fact-checking
rigor for numbers alone.

**What the top scorers did right, worth repeating:** Idea 5 (Aqueduct
Alley, 77) and idea 6 (Embercraft, 76) both scoped their differentiation
claims to a specific structural mechanism (two-level marble routing;
fully-simultaneous per-trick reveal) rather than a whole product category,
and both survived two differently-worded searches intact — continuing the
Turn 2-3 lesson that narrow, falsifiable claims are the ones that hold up.
Both also paired that with demand citations anchored to real, checkable
facts about the base game/genre (Tsuro's active Calliope Games retail
status; trick-taking's enormous documented player base) rather than
invented statistics. On producibility, ideas 9 and 10 (the two reskins)
scored highest (19/20 each) by having zero moving joints and a single
token geometry — reinforcing the Turns 1-4 pattern that fewer parts and
no repeated joints is the most reliable path to a strong producibility
score, though reskins inherently cap lower on differentiation and fun
since they add no new mechanism.

**Producibility's new failure mode under this rubric: an idea can give
concrete numeric mitigations for a risky component and still admit the
core mechanism is unvalidated.** Idea 8's Wobble Plate pivot-joint notes
specify a real starting dimension (3cm dome radius) but explicitly say it
"should be physically prototyped and iterated before the STL is locked" —
i.e., the idea's own text admits the central mechanism (whether the plate
tips predictably enough to be a fair, playable game) is unresolved, not
just risky. This is a step beyond the Turn 1-4 "compounding joint count"
pattern: a single unvalidated joint that the entire game's fairness
depends on should be treated as more serious than N repeated joints of a
type with known FDM behavior (peg-in-hole, hinge). Standing heuristic to
add: when a producibility_notes section says a component "should be
prototyped before locking the STL" for a mechanism the *core game rule*
depends on (not just a cosmetic or secondary part), treat that as an
open reliability question the idea hasn't actually answered yet, not as
an already-mitigated risk.

### Turn 6

**Differentiation dropped again (26.0 → 24.0/40), and both of the two
worst-hit ideas failed because the idea's own search targeted the wrong
neighborhood entirely, not just the wrong phrasing of the right
neighborhood.** Idea 3 (Fortress Echo, Battleship + elevation) searched
"Battleship hidden fortress elevation arc trajectory board game" and missed
**Sub Search** (Milton Bradley, 1973) — a commercially shipped Battleship
variant with ships hidden across three underwater levels plus a surface
level, found instantly by rephrasing to "Battleship variant vertical layers
submarine surface hidden grid game." Idea 4 (Monsoon Route, nautical
pickup-and-deliver with a shared wind dial) is a more instructive failure:
its search was aimed at *desert caravan* comparables (Caravan, Through the
Desert) — the wrong genre for a nautical wind game — and a search actually
aimed at the claim's own domain ("sailing trade game wind compass shared
movement modifier") immediately found **Cartolan: Trade Winds**, a shipped
tile-laying exploration game with an expanding map and a wind mechanic that
grants bonus movement to anyone moving with it. Both ideas ran only one
search each, and in idea 4's case the one search wasn't even about the
right kind of game. Standing heuristic to add, sharper than "run 2+
differently-worded queries": **the search terms must describe the idea's
own theme and mechanism, not a mechanically-similar game from a different
theme** — searching "desert caravan" comparables for a sailing game finds
the wrong prior art entirely and will always miss the real competitor.

**Demand's one bad score this turn was, again, a plain factual error on an
easily-checkable claim — the fourth turn in a row this exact failure mode
has appeared.** Idea 8 (Market Tides) stated High Society "remains in print
with a 2023 reprint"; Osprey Games' reprint was 2018, not 2023, confirmed
on the first search. This is the same class of error as Turn 4's inflated
Pandemic sales figure and Turn 5's wrong Azul award year — a specific,
checkable claim (a date, a number, an award year) that simply wasn't
verified before being written down. Given this is now a four-turn pattern
with a different specific fact each time (sales figure → award year →
reprint year), the standing heuristic from Turns 4-5 ("verify award/year/
number claims with one search before writing them") is clearly not being
applied consistently enough — it needs to become a mechanical last-step
checklist item for every demand_case before finalizing, not a general
awareness.

**New failure mode this turn: citing an unverifiable comparable as
evidence undercuts an otherwise-valid claim, even when the claim itself
survives search.** Idea 2 (Gearlock Derby)'s core "new" claim (crank-driven
meshing-gear race) held up fine across two searches, but one of its two
supporting citations — a game called "Gear Towers" — could not be located
in two separate targeted searches and reads as possibly fabricated or
misremembered. Unlike Turns 1-5's pattern of a false *absence* claim, this
is a false (or unverifiable) *presence* claim used as supporting evidence.
Distinguish these when writing rationale: a claim that "X doesn't exist" is
falsified by finding X; a claim that leans on "here's what does exist
nearby" is undercut just as badly if the cited nearby thing can't be
verified to exist at all — every named comparable, not just the absence
claim, needs to survive a search.

**What the top scorers did right, worth repeating:** Idea 1 (Hexfall
Kingdoms, 84) and idea 5 (Chrono Loop, 83) both ran genuinely
differently-angled searches that stayed on-theme (hex kingdom-building
scarcity mechanics; tabletop rewind/collision racers) and both paired that
with an independently-confirmed hard fact (Kingdomino's real 2017 SdJ win;
RoboRally's real three-publisher, three-decade edition history) — the
template from Turns 1-5 of narrow claim + verified fact continues to be
the reliable path to a high score. Idea 6 (Aurora Peak, 83) and idea 7
(Crystal Cavern, 80) both named specific comparable games in their
fun_case (Junk Art's end-of-game-only scoring vs. this design's mid-game
summit checkpoint; Blokus/Go's area-majority tension) rather than
asserting "this will be fun," continuing the Turn 5 lesson on what makes a
fun_case actually gradeable. On producibility, ideas 7, 9, and 10 (4 or
fewer part types, zero moving joints) again scored highest — this is now a
five-turn-consistent pattern and should be the default shape the ideator
reaches for, not an occasional choice.

### Turn 7

**Overall average rose to a new high (70.8 → 75.4/100), driven mainly by
differentiation (24.0 → 27.3/40) and producibility (16.9 → 18.0/20) — but
one idea repeated an almost identical failure to its own past self, which
is a more concerning signal than the average improving.** "Cairn Climbers"
(idea 1, this turn's lowest score at 66) claimed its shared central stack
was novel "rather than a personal tower" as found in Junk Art — but a
direct search found Junk Art's "Mad Art" mode already has players
"working together on a single or combined plinth." This is functionally
the same failure class BOARD.md flagged for a **same-titled Turn 5
idea**: Turn 5's Cairn Climbers missed Gravity Warfare's shared spin/tilt
platform; this turn's Cairn Climbers missed Junk Art's own shared-plinth
mode. Standing heuristic to make explicit: **when reusing or iterating on
a previously-scored idea/title across turns, the ideator must re-verify
every named comparable's *full rule set including alternate/party modes*,
not just its headline mechanic** — Junk Art is not one ruleset, it's 12
city-variants with materially different structures, and citing it as
"personal stacking only" without checking its other modes is exactly the
kind of surface-level comparable-check that keeps recurring in this
specific idea across turns.

**Demand's average held roughly flat (15.1 → 13.7/20) not because of false
claims this time, but because of an unverifiable-search-tool limitation
that hit three separate ideas the same way — this is a new failure
pattern, distinct from Turns 4-6's plain factual errors.** Ideas 5, 6, and
9 each cited a specific BGG ratings-count figure for a real, well-known
game (Skull King/The Crew "hundreds of thousands of copies," Tzolk'in
"25,000+ ratings," For Sale "20,000+ ratings") and in all three cases
WebSearch returned the game's actual BGG ratings page as a link but never
surfaced the number itself in the snippet — the searches were inconclusive
rather than contradicted, so the rubric's cap for inconclusive verification
was applied to all three. This is worth flagging as a distinct pattern from
past turns' fabricated/wrong numbers: **BGG's live rating/rank counts are
frequently not retrievable via WebSearch snippets at all**, so citing a
precise current ratings-count figure as demand evidence is inherently hard
to verify with the tools available to both the ideator and the evaluator.
Standing heuristic to add: prefer demand evidence that doesn't require a
live, frequently-changing count (an award win, a reprint history, a
publisher's own stated sales figure, an active BGG mechanic-tag count that
search snippets do reliably surface) over a specific "X,000+ ratings"
number for a single game, since the latter is the hardest category of claim
to actually confirm with this pipeline's tools.

**What the top scorer did right, worth repeating:** Whistleblower (idea 2,
86 — highest score across all turns to date under this rubric) didn't just
search for its named comparable (Suspicion by Wonder Forge) and confirm it
existed — it fetched the comparable's actual component list and turn
structure (cards, dice, pencils, a deduction pad) and confirmed the
specific mechanism claimed (a rotating dual-layer physical vote-reveal)
was genuinely absent from it. This is a stronger, more reliable form of
differentiation verification than a category search returning "no exact
match found," and should become the default step whenever an idea names a
specific existing product as its nearest comparable, not just when a
category search is ambiguous. Riverworks (idea 4, 79) and Spice Route
Caravan (idea 7, 78) both handled partial prior art correctly by narrowing
their claim to the specific combination still missing once an adjacent
match turned up (an old price-wheel patent; general canal-lock physics) —
continuing the Turn 3/6-established pattern that narrowing beats
abandoning or overclaiming. On producibility, the pivot-disc-with-detents
joint family was independently reused across three ideas this turn
(Whistleblower, Foundry Row, Spice Route Caravan) with each one scoring
17-18/20 — reusing one well-understood joint type across multiple ideas in
a batch, rather than inventing a new mechanism each time, continues to be
the most reliable path to a strong producibility score.

### Turn 9

**Overall average continued its recovery (70.1 → 75.2/100), with demand
(12.3 → 16.0/20) and producibility (14.8 → 18.2/20) both jumping — this is
the first turn since the pivot with zero producibility scores capped at
10 or below, meaning the four-turn-running "unvalidated core mechanism"
failure (Turns 5-8) did not recur at all this batch.** Every idea's
producibility_notes either had no risky joint (flat engraved tiles, static
peg tracks — ideas 3, 5, 6, 10) or explicitly defused an apparently-risky
feature by reasoning from proven external geometry/behavior instead of
promising to prototype-and-see: idea 8's gear-shaped workers stated as
non-meshing decorative silhouettes (sidestepping tooth-tolerance risk
entirely rather than taking it on), and idea 9's wedge-stacking geometry
argued as identical to Tetra Tower/Cheese Wedge's already-shipped balance
profile rather than a novel mechanism needing validation. This is the
template Turn 8's "Signal Fire" set (geometry proven deterministic by
construction, not by future testing) and it's now visible across most of
a full batch rather than one standout idea — worth reinforcing explicitly
as the default move whenever a component looks risky: cite proven
external geometry or argue structural impossibility of failure, don't
promise a print-and-test pass.

**Differentiation held flat (27.4 → 26.0/40) and two ideas repeated the
exact "search your own claim's literal wording, not a paraphrase" miss
BOARD.md has now flagged in Turns 4, 5, 6, and 8.** Vault Breakers'
own differentiation text says it searched "Cryptex"-branded phrasing and
concluded no shipped game uses a physical player-facing combination dial
for vault-cracking; a search on the claim's own core words ("combination
dial heist board game crack the code") immediately surfaced **Heist**
(Fundex Games, BGG #40886), a shipped card game whose entire premise is a
physical combination dial players spin to crack a vault code. Orchard
Order's text says it searched "lazy susan" phrasing and patent filings and
found nothing; a search on its own core words ("rotating carousel drafting
board game pockets spin") immediately surfaced **Let's Learn Carousel**
(Tactic Games), a shipped game literally built around a rotating carousel
disc with spinning pockets. In both cases the idea's overall structure
survives (the specific combination of features remains distinct), so
these weren't zeroed, but the "no shipped product does anything like
this" framing in the rationale was measurably overconfident in exactly the
way four prior turns' lessons already named. This confirms the pattern is
not self-correcting from repetition of the lesson alone — it may need to
become a literal pre-finalization checklist step ("search the concept's
own headline noun phrase verbatim, not a related/broader phrase") rather
than a stated principle the ideator is expected to internalize.

**New nuance this turn: a search can produce a genuinely inconclusive
partial hit rather than a clean confirm/deny, and that should be treated
as partial evidence, not ignored.** Rune Trick's claim that trump
dynamically resets every trick (rather than staying fixed for a hand) is
weakened but not falsified by a real BGG listing for a game literally
named **Trump Change**, described only as "a trick-taking game... where
the Trump continues to change" — too thin a description to confirm or
deny a match, but concrete enough to show the general concept of
mid-hand trump changes isn't unprecedented in trick-taking. This is
distinct from a full contradiction (Vault Breakers, Orchard Order above)
and from a clean pass (Guild Hollow, Sundial Market below) — it's the
rubric's "if a search is inconclusive, say so and apply the relevant cap"
case in its purest form this turn, and it was scored as a moderate
partial deduction rather than either a full pass or a full zero.

**What the top scorers did right, worth repeating:** Guild Hollow (82,
this turn's highest) ran multiple differently-worded searches for its
specific mechanic ("adjacent slot bonus shared with opponent," "gear mesh
adjacency worker placement") and none turned up a contradiction — the
correct amount of search effort for a claim this central to the idea's
pitch. Sundial Market (80) and Tidal Kingdoms/Freight Line (79 each) all
found loosely-adjacent comparables (Cyclades' non-resetting bid tracks;
High Tide's physical tile-stacking; Tsuro's shared-board movement) and
correctly reasoned through *why* each one doesn't actually match the
specific claimed mechanism, rather than either ignoring the near-miss or
treating proximity as disqualifying — this is the right level of rigor
the rubric asks for and should stay the default. Demand this turn was
unusually clean: no idea leaned on an unverifiable trend or an inflated
number, and two claims (Texas 42's 2011 State Domino Game designation;
Spaceship Morris's existence on TheGameCrafter) were independently
confirmed via direct fetch rather than taken on the idea's word — this is
the single most reliable way to award a high demand score under this
rubric and should keep being the first move when a demand_case names a
specific, checkable institutional fact.

**Process note: WebSearch hit a session budget limit partway through this
evaluation, which forced a fallback to WebFetch-against-search-engine-HTML
for roughly half the searches, and this had a measurable capability
cost.** Google and Bing fetches through WebFetch returned localized/
non-English error or dictionary-definition pages with no usable game
results, and only DuckDuckGo's HTML endpoint (`html.duckduckgo.com`)
returned usable snippets. This is worth flagging as an evaluator-tooling
risk rather than an ideator lesson: if WebSearch budget runs out again in
a future evaluation, `html.duckduckgo.com` is the fallback that actually
works, and any claim checked only through that fallback should be treated
as lower-confidence than a claim checked with full WebSearch (as was done
explicitly for ideas 5 and 6's theme-uniqueness claims this turn, which
could not be re-verified and were scored at moderate rather than full
confidence as a result).

### Turn 8

**Differentiation's worst score this turn (Stratum, 8/40) came from the
idea's own stated search query, run verbatim, immediately surfacing the
prior art it claimed didn't exist — this is the sharpest version yet of
the failure BOARD.md has been tracking since the post-Turn-4 reliability
check.** Stratum's differentiation text says it searched "order-locked
drafting rack positional slot scoring board game" and found nothing; that
exact phrase, searched independently, returns **Rack-O** (a 1956
mass-market game whose defining rule — cards locked into fixed rack slots,
"without rearranging any of them" — is precisely the "rather than a
free-form hand or tableau" mechanic Stratum markets as its original hook)
as the literal first result. Unlike prior turns' misses (wrong phrasing,
wrong genre neighborhood), this one didn't even need a *different* query —
the idea's own words, taken at face value, found the counterexample. This
also surfaced a related honesty problem worth naming as its own
heuristic: Stratum combines two well-known existing mechanics (Rack-O's
locked rack + Sushi Go's pass-the-tray draft) and labels the result
`"new"` rather than `"twist"` — when an idea's "original" claim rests on a
component that, searched on its own terms, turns out to be a classic
game's entire premise, that's a signal the idea is actually an undeclared
mashup and should be classified (and scored) as a twist/combination, not
as new. Standing heuristic to add: **before finalizing a differentiation
claim, search the literal defining-rule phrase as if it were pitched as
its own product idea** ("cards/pieces lock into fixed slots and can't be
reordered" is a pitch, not just a rules detail) — mechanics framed as
incidental structural choices are exactly the ones that turn out to be
another game's entire premise.

**A repeat of the exact Turn 4-6 "plain factual error on an easily-checked
claim" pattern, this time a designer misattribution rather than a number,
date, or award year.** Auction House: Curios cited For Sale as designed by
"Alan R. Moon" (who designed Ticket to Ride); the real designer, Stefan
Dorra, turned up on the very first search for "For Sale board game 1997
designer." This is now a five-turn-recurring failure mode with a different
specific fact each time (sales figure → award year → reprint year →
designer name), which means the standing heuristic ("verify award/year/
number claims with one search") has been too narrowly scoped — it named
*numbers and dates* as the risk category, but this turn shows *any* named
person/entity attached to a comparable game (designer, publisher, studio)
is exactly as checkable and exactly as likely to be wrong. Broaden the
checklist item: every specific, named fact in a demand_case or
differentiation section — number, date, award, or name — gets one
verification search before the idea is finalized, with no exceptions
carved out by fact type.

**Producibility's cluster of low scores (Cascade Works 10, Warren 10,
Auction House: Curios 8, Orbital Drift 9) all trace to the same root
cause the rubric now needs to treat as a hard, not soft, cap: a
producibility_notes section that explicitly says a core-game-dependent
mechanism "should be" validated, print-and-tested, or confirmed reliable
before locking the STL is describing an unresolved risk, not a mitigated
one, regardless of how precise the numbers around it sound.** Four
different mechanisms triggered this across the batch — marble-flow
clearance through every pipe seam (Cascade Works), a hand-cranked
single-chip dispenser baffle (Warren), a gravity-fed chip hopper (Auction
House: Curios), and a bare-printed-bearing turntable pivot over the
Turn-4-established 100mm diameter threshold with no hardware insert
(Orbital Drift, also reused uncredited in Auction House: Curios's wheel).
This is the fourth turn in a row this exact pattern has appeared (Turns
5-8) and it is not improving turn over turn — it should be promoted from
a "heuristic to watch" to a flat rule: **any mechanism the core turn
loop depends on every single turn, where the idea's own notes call for
physical print-and-test validation before the STL is locked, caps
producibility at 10/20 regardless of how well-specified the surrounding
tolerances are** — a precise number next to an admittedly-unvalidated
mechanism is not the same as a validated mechanism.

**What the top scorer did right, worth repeating:** Signal Fire (85, the
highest score this turn) paired a differentiation claim that survived two
on-theme searches with a demand claim that was independently *confirmed*
rather than merely unfalsified — Santorini's #88 ranking on Meeple
Mountain's "100 Most Important Games of the 2010s" list was checked
directly and matched the claim exactly, the strongest form of demand
evidence available under this rubric. Its producibility_notes also modeled
the right way to defuse a would-be risky component: rather than asking for
physical validation, it argued the sighting gauges are deterministic
*by construction* (notch heights computed directly from fixed, known board
geometry, with no player-facing tolerance to get wrong) — the correct
response to a component that looks risky is either a hardware-backed
mitigation or a proof that the geometry makes failure structurally
impossible, not a promise to test it later. Dune Runner (81) and Cascade
Works' differentiation section (33/40, undermined only by its separate
producibility admission) both continued the Turn 3/6 pattern of narrowing
a twist claim to the specific rule-level change versus the named base
game, rather than claiming a whole new category.

### Turn 10

**Both scores this turn's biggest drop since the pivot (75.2 → 67.0/100),
and the cause is a genuine tooling failure, not a reasoning failure: the
ideator's own WebSearch budget was exhausted before it could verify a
single differentiation claim, and every one of its self-flagged "I could
not complete live search verification this session" caveats turned out to
hide real, findable prior art.** All 10 of this turn's differentiation
rationales carried the same disclosed-uncertainty caveat, and re-running
the ideator's own literal claim wording (via WebFetch against
`html.duckduckgo.com`, since the evaluator's own WebSearch budget was
*also* pre-exhausted this turn — a first) surfaced direct, close, or
exact prior art for 6 of 10 ideas: Beacon Watch's "novel rotating beam
disc catches a smuggler" hook is Haba's shipped **Insel der Schmuggler**'s
entire premise; Silo Stack's stacking-plus-bust-curve hook is closely
prefigured by KOSMOS's **PUSH**; Dome of Kings' "genuinely new" wraparound
connection-game claim is undercut by **"Spherical Go"** already existing
as an established, independently-implemented concept (just not physically
manufactured); Volcano Climbers' "distinct mountain-climb styling" is
undercut by Playte Games already selling mountain-themed Can't Stop
editions including a Mount Fuji edition; and Beehive Harvest's bee/
honeycomb Mancala reskin turned out to be an almost word-for-word match
to an already-shipped, multi-retailer product (**Beehive Mancala: A
Nature Board Game**, Laurence King Publishing / Kew Gardens shop /
Walmart). Standing rule to make explicit and non-negotiable: **when the
ideator's own search tooling is unavailable, it must say so and hold the
idea back from being finalized as "verified," not finalize it anyway with
a disclosed-but-unresolved caveat** — a caveat is not a substitute for
verification, and this turn proves the caveats were, without exception,
flagging real gaps rather than false alarms. If WebSearch is unavailable,
the ideator should still attempt the same WebFetch-against-
`html.duckduckgo.com` fallback the evaluator used successfully this turn
and Turn 9, rather than shipping the idea unverified.

**Producibility recorded its second-lowest average since the pivot (18.2
→ 15.2/20), driven by three separate ideas (Silo Stack, Rune Forge,
Clockwork Court) independently repeating the exact Turn 8 "should be
tested" hard-cap pattern in the same batch — the first time this pattern
has hit 3 of 10 ideas in one turn rather than 1-2.** All three
producibility_notes sections attach a precise, confidence-inspiring
tolerance number (0.3-0.5mm) to a mechanism the entire core game loop
depends on every single turn, and all three then say, in effect, "test
this before locking the STL": Silo Stack's wobble-tray pivot ("a physical
test-and-tune pass before locking dimensions"), Rune Forge's 5x5
notch-profile pairing matrix ("validating all 5x5 notch-profile pairings
on a physical test print before locking the full 60-tile geometry"), and
Clockwork Court's gear-mesh tooth pitch ("physically testing all gear
pairs before locking geometry, since this is the core information-
delivery mechanism of the game"). Turn 8 already named this exact
sentence-pattern as a hard, not soft, cap — a precise number next to an
admittedly-unvalidated mechanism is not a validated mechanism — but this
turn shows the pattern recurring at scale rather than shrinking. The
common thread across all three: each is a *novel, unprecedented* physical
joint (a wobble tray tuned to topple unpredictably; 25 distinct notch-tab
pairs that must reject 24 combinations and accept 1; two gear tooth
families that must mesh/refuse purely by feel), unlike the "known joint
type, just needs a dimension chosen" cases that pass (Terraform Ridge's
score dials, Current Drop's lazy-susan bearing, Prism Duel's Connect-Four
channel extension). Standing heuristic to sharpen: before finalizing a
new joint type nobody has validated before, either drop it for a
known-joint-type alternative or find a way to argue the geometry is
deterministic *by construction* (Turn 8/9's "Signal Fire" template) — a
promise to physically iterate is not a producibility answer, it's an
admission the idea isn't finished.

**What the top scorer did right, worth repeating:** Terraform Ridge (81,
this turn's highest) paired a differentiation claim that survived two
on-theme searches with an independently re-verified hard fact (Kingdomino's
2017 Spiel des Jahres win, checked directly rather than taken on the
idea's word) and a producibility risk (3mm elevation steps) that came with
a concrete, already-decided fallback (a 4mm base) rather than a promise to
test and see — the correct response to a tight-but-plausible tolerance,
distinct from this turn's three "should be tested" failures above. Current
Drop (76) and Prism Duel (71) both reasoned their one flagged risky joint
(a lazy-susan bearing under load; a double-depth drop channel) as a direct,
well-understood extension of an already-proven mechanism rather than a
novel one needing validation — this is the reliable dividing line this
turn between producibility scores in the high teens and scores capped at
10.

**Reinforcing the reskin-cap bookkeeping continues to work correctly:**
both reskins this turn (Volcano Climbers, Beehive Harvest) were counted
in `id` order and scored on their own merits since both fell within the
first-2 allowance — worth noting only because it means Beehive Harvest's
5/40 this turn is a genuine differentiation failure (near-exact prior art
found), not a cap artifact, and should be read by the ideator as a real
signal that the specific bee/honeycomb Mancala niche is saturated, not as
routine reskin-cap noise to ignore.

**CAD Reality Check (1/3 built):** Terraform Ridge, this turn's highest
text score (81/100), converted only 4/20 on the purchase-intent panel — a
sharp gap between paper differentiation/fun scores and actual buy intent
that's worth tracking as its own signal going forward. The panel's NO
majority didn't dispute the elevation-adjacency rule twist itself; it
converged on execution details the rubric's text-only scoring doesn't
weight as heavily: perceived complexity/teach-time mismatch against the
stated casual/family audience, and a monochromatic color scheme that
actively undercuts the terrain-color scoring it's built on (raised
independently by both aesthetics-focused and clarity-focused personas).
A minority of YES votes did track the paper score's stated strengths
(calculable optimization puzzle, minimalist design-object appeal), so the
differentiation claim isn't being rejected outright — but a genuinely
novel rule twist is necessary, not sufficient, for purchase intent if the
color/complexity presentation fights against the game's own audience
framing. Standing note to carry forward: when an idea's demand_case names
a specific audience (here, casual/family), its producibility_notes and
component color/finish choices should be checked for consistency with
that audience's stated tolerance for complexity and need for visual
legibility, not just scored independently on manufacturability.

### Turn 11

**First turn under the fully-real-build rubric (Differentiation/50,
Producibility/40, Buyability/10 — Demand and Fun retired as text-scored
categories), and the CAD pipeline's actual pass rate this turn was 1/3, not
3/3 — 2 of the 3 `cad_build_picks` (Lock & Current, Fox & Lantern) parked
on `awaiting_questions` and never produced a scoreable build at all,
despite both having the two highest Differentiation scores in the entire
batch (40 and 41/50) and producibility_notes that, on paper, looked like
exactly the low-risk template this pipeline has praised for ten turns
running (small pivot-disc-with-detents joints, simple slide-fit trays, no
component over ~100mm).** This is the first time a park has hit the
ideator's *best*-scoring picks rather than a middling one, and it means
"the joint type is a proven, reused pattern" is necessary but not
sufficient for a `cad_prompt` to build without a clarifying question —
something else in those two prompts (not diagnosable from this side of the
gate, since a parked job produces no manifest/error detail at all) made
the real pipeline stop and ask rather than build. Standing note: a parked
build is currently a total information black hole for this evaluator —
neither `board-game-evaluator` nor `BOARD.md` has any visibility into
*what question the job asked*, which is exactly the diagnostic signal that
would tell the ideator what to fix in future `cad_prompt`s. This is worth
flagging as a pipeline gap, not just an ideator lesson (see PAIN_POINTS.md
Evaluator entry this turn).

**The one completed build (Cargo Hold) is the most severe concept-fidelity
failure this pipeline has produced to date, and it's a different failure
mode from every prior turn's fidelity gaps: not a dropped or merged
component here or there, but essentially all 4 specified part types
(4 separate blue grid boards, 5 white dice, 60 four-colored polyomino
tiles, a two-piece navy/white box) collapsed into one single fused,
monochrome-teal block with the grid and a couple of piece shapes merely
engraved into its lid.** Printability scored a perfect 10/10 specifically
*because* of this collapse — a single simple solid is trivially printable
— which is the sharpest illustration yet of the standing "easy to print is
not evidence of a good build" risk: extreme part-consolidation actively
*maximizes* the printability sub-score while destroying the fidelity
sub-score, so a future idea whose build looks great on printability alone
should be treated with more suspicion, not less, until fidelity is
separately confirmed against the actual `cad_prompt` part list. The
20-persona purchase-intent panel independently and unanimously (0/20)
converged on exactly this same defect from the customer side, without any
prompting toward it — "plain teal box," "no dice, no distinct minis," "no
colorful pieces" appeared across at least a third of the 20 reasons — which
is a strong signal this is a real, customer-visible failure and not just
an evaluator's harsh reading. Cargo Hold's `cad_prompt` was one of the most
verbose and explicitly multi-part specs in this turn's batch (4 named part
types, exact dimensions, 4 named colors, explicit "no glue/joint" framing
for looseness) — the takeaway is not "write a more detailed cad_prompt,"
which this one already was, but that **very high part-count, multi-color,
all-loose-component designs (4+ distinct types, 60+ total pieces across 4
colors) appear to carry a real risk of the generation pipeline collapsing
them into a single simplified solid even when individually well-specified**
— worth treating as a new watch-item alongside the existing joint-risk
heuristics: high part-type-count and color-count, not just joint
complexity, is itself a fidelity risk factor to weigh when choosing
`cad_build_picks`, and a design that reduces total part *types* (even if
counts within a type stay high, e.g. "60 identical-shape tiles in 4
colors" vs. "5 different part types") may be safer to pick for a build than
one that reads well on paper's part-count-and-joint-count producibility
heuristic alone.

**Differentiation's one serious miss this turn (Caravan Ledger, 22/50) is
a fresh instance of the oldest and most-repeated failure in this file's
history — not searching the idea's own literal name/title against its
closest same-named comparable.** Caravan Ledger's differentiation text
checked Express Route, Cargo Empire, and Xia, but never checked a game
literally titled **Caravan** (Rio Grande Games, BGG #269789) — whose real,
shipped "steal a visible good by landing your camel on an opponent's"
mechanic is functionally the same action Caravan Ledger's "Toll" rule
claims as part of its novel combination. This is the same pattern named in
Turns 4-9 (Vault Breakers/Heist, Orchard Order/Let's Learn Carousel,
Stratum/Rack-O) but with an even more obvious tell this time: the
comparable's name is a near-exact match of the idea's own title. Standing
heuristic to sharpen once more: **before finalizing, search the idea's own
title/name itself as a plain board-game-title query, not just its
mechanic/theme phrasing** — a title this close to an existing game's name
is itself a signal worth a dedicated check, independent of the mechanic
search.

**What went right this turn, worth reinforcing:** Fox & Lantern's
differentiation claim (a fixed Lantern-marker pit that triggers a mid-sow
direction reversal in Kalah mancala) was the narrowest and best-surviving
claim of the batch — two searches confirmed the general "reverse sowing"
rule family in mancala literature is a *structural* rule (direction flips
based on landing in an occupied vs. empty pit), genuinely distinct from a
designated marker-pit trigger. This is exactly the "narrow, specific claim
survives search" pattern this file has praised since Turn 2-3, and it's a
reminder that a strong Differentiation score is still fully achievable even
under this turn's harsh build-completion realities — the build pipeline's
pass rate, not the idea quality, was this turn's binding constraint.

### Turn 12

**The CAD pipeline's pass rate stayed at 1/3 for a second consecutive turn,
and this time it hit both a "should build clean" pick and the batch's
single lowest-risk pick at once.** Reef Bloom (flat hex tiles, loose
slip-fit pegs, open trays — the exact zero-joint template this file has
praised as the safest shape since Turn 1) timed out with no manifest ever
produced. Gumdrop Row — explicitly reasoned by the ideator as "the single
lowest-risk design in the batch," a single continuously-molded board plus
loose spheres, no assembly, no joints at all — parked on
`awaiting_questions`, the exact same outcome Turn 11 dealt its two
highest-differentiation picks. Between Turn 11 and Turn 12, four of six
`cad_build_picks` have now failed to complete despite every one of them
matching the "known joint type / few parts / no novel mechanism" template
this file has spent eleven turns establishing as low-risk. Standing
conclusion to promote from observation to hard rule: **producibility_notes
predicting a clean build (few parts, proven joint types, no novel
mechanism) is evidence about print/structural risk, not about whether the
real text-to-CAD pipeline will complete the job at all** — parking and
timeout are a distinct failure mode this rubric still cannot see inside
(no manifest, no error, no clarifying-question text survives), and picking
3 "safe" ideas per turn is not yet a reliable way to guarantee even 1
usable build, let alone 3.

**The one completed build (Circuit Mill) is the most severe concept-fidelity
collapse this pipeline has produced to date — worse than Turn 11's Cargo
Hold, not just a repeat of it.** The `cad_prompt` specified two richly
detailed, clearly separate parts (a 250x250mm circuit-board plate with
engraved concentric "trace" squares, connector "wires," and 24 raised node
bumps in a dark-green/copper finish; 18 red/blue cylindrical resistor
pieces) plus a box. The actual build — checked across `photo.jpg`,
`assembled.png`, and all six `qa.png` orthographic views, all fully
consistent with each other — is a single plain closed rectangular box in a
uniform brown/slate color: no board pattern, no engraved lines, no node
bumps, and no loose pieces of any kind survive anywhere in the model. Turn
11's Cargo Hold at least kept a faint engraved grid motif and a couple of
piece-shaped ridges after its collapse; this turn's collapse left literally
nothing recognizable behind. Printability scored a perfect 10/10 again,
for the identical reason Turn 11 named: a single plain solid is trivially
printable, so **printability and fidelity now have two consecutive turns of
demonstrated inverse correlation on this pipeline's worst failures** — a
future evaluator or ideator should treat a suspiciously perfect
printability score on a multi-part design as a prompt to look harder at
fidelity, not as confirmation the build went well. The 20-persona panel
independently converged on the identical defect from the customer side
without prompting (a strong majority of all 20 reasons independently
described "just a plain box, no board/pieces visible") and voted 0/20 would
buy — this is now the second consecutive turn a real purchase-intent panel
has unanimously zeroed a build purely on fidelity grounds, before even
weighing in on the underlying game design.

**Differentiation's clearest miss this turn (Lantern Drift, 24/50) is a
fresh instance of the Turn 6 "search your own mechanism, not an adjacent
theme" failure, not a new failure mode.** The idea's own differentiation
text searched wind/kite-themed comparables ("wind gust market disruption...
kite") for a game whose actual claimed novelty is a die-driven forced
market-row shift plus a must-ascend personal run that busts on a
non-conforming draft — searching the theme instead of the mechanism missed
**Up or Down?** (Capstone Games, BGG #428058, a currently-published game),
whose core personal-column mechanic — build a strictly ascending or
descending run, discard the whole row and start over the moment a card
doesn't fit — is a close structural echo of half of Lantern Drift's pitch.
Salt Road Bazaar (32/50) shows the same gap in a milder form: it checked
"Salt Road"-branded and salt-themed titles but never checked the generic,
structurally-adjacent **Caravan** (Rio Grande Games) by name despite heavy
thematic overlap (caravans, city goods delivery, changing prices) — this
turned out not to be a real mechanism match on closer inspection (Caravan's
cities want one fixed good each and its price shifts are scheduled, not
per-purchase), but it should have been checked and named, not skipped.
Standing heuristic to sharpen once more: **before finalizing, search the
idea's own mechanism using words drawn from the idea's own rules text, and
separately check the closest same-genre named comparable (by title, not
just by branded phrase) even when a quick read suggests the mechanism will
turn out different** — Salt Road Bazaar did the second check correctly
this time (post-hoc, in this evaluation) and survived; Lantern Drift did
neither and lost half its differentiation credit as a result.

**What went right this turn, worth reinforcing:** Texture Trail (42/50) and
Reef Bloom (42/50) both ran two genuinely differently-angled searches aimed
squarely at their own claimed mechanism (chain-flip push-your-luck memory;
molded-arrow forced-outward hex growth) and both came back clean — the
correct level of diligence this file has been asking for since Turn 2.
Gumdrop Row's differentiation write-up also modeled good practice on a
smaller but still-important axis: rather than taking its own cited
comparables (Beehive Mancala, Space Walk) on faith, this evaluation
independently re-verified both (Beehive Mancala's real Laurence King/Kew
Gardens listing; Space Walk's real 1999 Ravensburger/Rüdiger Dorn
attribution) and both checked out exactly as claimed — continuing the
Turn 5/8 lesson that named comparables need the same fact-check rigor as
absence claims, applied correctly here.

### Turn 13

**The CAD pipeline's pass rate dropped to its worst yet (1/3, same raw
count as Turns 11-12 but this time 2 of 3 picks parked instead of 1, and
the parked picks were the two ideas explicitly reasoned as lowest-risk in
the batch).** Cipher Row's own producibility_notes called out "only
single-depth peg-in-hole joints... no ambiguous or optional-sounding
geometry for the CAD pipeline to misinterpret" and Threshing Floor's
called its stacking mechanic "deterministic by construction" with "zero
player-facing tolerance risk" — both are exactly the kind of low-risk,
proven-joint-type reasoning this file has praised for thirteen turns
running, and both still parked on `awaiting_questions` with zero
diagnostic artifacts. Combined with Turns 11-12, that's now 5 of 9
`cad_build_picks` across three turns failing to complete, with the
"safe on paper" ideas failing at the same rate as everything else.
Standing conclusion, now reinforced a third time: **producibility_notes
quality is not predictive of whether the real text-to-CAD pipeline will
finish the job** — pick diversification (3 genuinely different geometry
styles per turn, not 3 variations on "few parts, proven joints") may be a
better hedge against a 1/3 pass rate than trying to out-reason the parking
behavior from the text side, since this file has no visibility into what
actually triggers a park.

**The one completed build (Foghorn) is a new, distinct failure mode from
Turns 11-12's "everything fused into one blob": parts DID separate this
time, but the two components carrying the game's entire mechanical and
color identity did not.** The 4 sawtooth racks, box, and lid all printed
as correct, distinct, roughly-right-shaped pieces — real, measurable
progress on the part-separation problem named in the last two turns'
lessons. But the trump dial fused to its base plaque into one static
non-rotating piece (destroying the literal core "spin the dial to set
next trump" mechanic, not just its finish) and the 48 individually
numbered suit tiles fused into one continuous ~40-cell mat rather than 48
loose, holdable chips (destroying the ability to hold and play a hand of
tiles — basic to any trick-taking game). Every part that was supposed to
carry one of the `cad_prompt`'s 4+ distinct colors (dial quadrants, suit
tiles, player racks) instead printed in one uniform monochrome terracotta,
and the trick collection tray specified in `components` is entirely
absent from the build. The 20-persona panel converged on the same defect
independently and unanimously (0/20 would buy), with ~17 of 20 reasons
citing the unpainted/uncolored, unfinished-prototype look specifically —
this is now the third consecutive turn a real purchase-intent panel has
near-unanimously zeroed a build on a production/fidelity defect rather
than weighing in on the underlying game design at all. New heuristic to
add alongside Turns 11-12's "part-type/color-count fidelity risk": **when
a design's core twist mechanism lives specifically in a component's color
(here: 4 colored trump-dial quadrants, 4 colored suit-tile sets) rather
than just its shape, that color-coding is not a cosmetic nice-to-have —
losing it can simultaneously destroy legibility, gameplay function, and
purchase intent in one stroke, and should be weighed as seriously as a
joint-tolerance risk when choosing `cad_build_picks`.**

**Differentiation's clearest miss this turn (Seam Works, 14/50) is the
sharpest version yet of the "check the closest structural comparable, not
just the closest thematic one" failure this file has tracked since Turn
6.** Seam Works' own text checked Gold Mine (a maze/collection game) and
Fault! (a contract-economy game) — both mining-themed, neither a real
structural match — but never checked Indigo (Reiner Knizia, 2003), a
non-mining connection game whose actual rule ("a tile placed by one player
can benefit another... a strategic placement by one player could complete
a route that delivers a gem to an opponent's edge, allowing that opponent
to claim it," confirmed via direct fetch) is close to a word-for-word
match of Seam Works' claimed novel hook, just with gems-to-edges instead
of ore-to-entrance. This is the same "wrong neighborhood" failure Turn 6
named for Monsoon Route (searching desert-caravan comparables for a
sailing game) but in a subtler form: Seam Works searched the right
*theme* (mining) but the wrong *mechanism family* (maze/collection and
contract-economy instead of connection games) — a reminder that "search
the mechanism, not the theme" needs a second half: identify which
*mechanism family* (connection game, worker placement, drafting, etc.) the
claimed hook actually belongs to before picking comparables, since a
theme-matched search can still miss the real prior art if it stays within
the wrong family.

**What went right this turn, worth reinforcing:** Lantern Keepers (40/50)
and Thistlewood Market (38/50) both ran two genuinely differently-angled
searches squarely aimed at their own claimed mechanism (single shared
rotating beacon triage; fixed non-negotiable per-shape recess trays) and
both came back clean, continuing the pattern this file has asked for since
Turn 2. Foghorn's differentiation write-up also modeled a good instinct
worth naming explicitly: it named and correctly distinguished its single
closest comparable (Sea Change) in enough rule-level detail to make the
distinction falsifiable — the miss wasn't in that reasoning, it was in
not also checking two other obvious classics (Fox in the Forest, Trumps)
by name given how central "dynamic trump" is to the pitch; a purchase-
intent panelist raised exactly this gap independently, which is itself
worth noting as a new source of differentiation-relevant signal alongside
search — panel reasons sometimes name prior art the text-only research
missed.

### Turn 14

**First turn under the new Vision Fidelity/60 + Reliability/25 +
Ambition/15 rubric, and the build pass rate collapsed to 1/3 for a reason
that has nothing to do with vision, spec quality, or CAD translation at
all: two of three ideas failed before a single line of CAD geometry was
generated.** Idea 1 (Keyhold)'s job returned `llm_error` ("couldn't
produce a plan") four minutes after concept selection, and idea 3
(Eclipse)'s concept-phase worker died ~35 minutes into round-2 style
generation with `worker_error` ("response exceeded the 32000 output token
maximum"). Both `cad_prompt`s were fully specified (5/5 `must_survive`
ranks covered per `CAD_PROMPTS.json`'s own coverage blocks) and both had
ambition scores well above the 8/15 floor (13 and 9). **Attribution: pure
pipeline limitation, not a translation or vision failure** — there is
nothing in either idea's text, geometry request, or complexity that
predicts this outcome, and nothing for `board-game-ideator` or
`board-game-cad-writer` to change in response. This is worth escalating as
an infrastructure question (plan-generation reliability; whether
`CLAUDE_CODE_MAX_OUTPUT_TOKENS` needs raising for concept-phase workers on
richly-specified ideas) rather than folded into either agent's design
heuristics.

**The one build that finished (Twin Deck Solitaire) exposed a second,
unrelated pipeline limitation: the scoring harness itself, not the CAD
build, was unable to verify 4 of 5 `must_survive` ranks.** `score_build.py`'s
`compile_conditions()` only reads `geometric.get("inputs")`, a key this
turn's `IDEAS.json` schema never populates (it writes `"parts"` and
`"thresholds"` instead) — so `part_clearance`, `opening_presence`,
`axis_alignment`, and `cylindrical_fit` are structurally unable to resolve
for any idea built against this turn's schema, independent of whether the
underlying geometry is correct. **Attribution: pipeline limitation in the
audit tooling, not in the ideator's schema choice or the CAD build** —
reading `project/main.py` directly confirmed all four conditions were in
fact satisfied exactly as specified (30.0mm gap against a 25-35mm
threshold; 0.0mm hole-alignment offset because both boards are built from
one shared `cross_positions()` function; 0.3mm radial peg clearance,
`PEG_D=11.4` against `HOLE_D=12.0`, an exact match). The evaluator rubric
still only credits `inconclusive` at 0.5 rather than upgrading it to a
pass, so `geometric_fidelity` = 0.6 stands as the correct, rubric-honest
number even though the true build is closer to a full pass — this is the
system working as designed (the evaluator doesn't get to override a
broken measurement with its own judgment on the geometric axis), but the
schema/harness mismatch itself should be fixed before the next turn so
future scores don't need this manual reconciliation.

**What the one completed build did right, worth repeating:** Twin Deck
Solitaire reused known joint types (peg-in-cylindrical-hole, pin-in-bore)
at a generously specified clearance (0.3mm radial) rather than inventing a
new mechanism, and — the more important move — generated both boards'
hole positions from a single shared function (`cross_positions()`) instead
of independently specifying two coordinate lists, which makes vertical
alignment correct *by construction* rather than by luck or by a tolerance
check. This is the same "deterministic by construction" template Turns
8-9 praised for risky joints, applied here to a cross-part alignment
requirement instead of a single mechanism — worth generalizing: whenever a
spec asks for two or more parts to share a position/pattern exactly (grid
layouts, aligned hole pairs, matched sockets), instruct
`board-game-cad-writer` to generate that pattern once and reuse it, not
restate matching coordinates twice. The one real miss on this build was
smaller and purely a CAD-writer→build translation gap: the `cad_prompt`
asked for blind 15mm bores at the post insertion points and got
through-bores instead (pins protrude ~3mm past each board's face) —
**attribution: pipeline limitation** (the CAD agent silently substituted a
simpler feature for the one requested), not a spec ambiguity, since the
depth and "blind" wording were both stated plainly.

### Turn 15

**The pre-build pipeline failure from Turn 14 recurred, later and with less
diagnostic signal, and is now a two-turn pattern.** 2 of 3 ideas (Lockstep
Canals, Tidepool Stones) never produced a first-shot build again this turn.
Unlike Turn 14 — where both failures died *before* a CAD job started
(`llm_error` at plan-generation, `worker_error` at concept-phase, each with
at least a diagnostic string) — both Turn 15 failures cleared concept
selection and died 35-47 minutes later, mid-CAD-generation, with a bare
`terminal: failed` event and zero error text. Tidepool Stones failed twice
on the identical prompt (once in ~80s pre-park, once ~47 minutes after a
successful concept selection on resubmission), which rules out attributing
it to a one-off transient blip for that idea. Both `cad_prompt`s were fully
specified (5/5 `must_survive` ranks covered, per `CAD_PROMPTS.json`'s own
coverage blocks) and both cleared the 8/15 ambition floor (12 and 9).
**Attribution: pure pipeline limitation, not translation or vision** —
there is nothing in either idea's prompt content, part count, or geometric
complexity that distinguishes it from Sluice Row, the one idea that
finished. Per `CAD_GRAMMAR.md`'s standing note, this has moved from
"noted" to "recurring" and is worth escalating to the user as an
infrastructure question rather than treating each turn's instance as
isolated.

**The one build that finished (Sluice Row) surfaces a real, generalizable
CAD-translation limit: subtractive detail cut into a single monolithic
board is invisible to a checker that expects a separately-named part, even
when the model faithfully attempted it.** 3 of the 4 non-rank-1
`must_survive` ranks came back geometric `fail` with "no geometry could be
bound to the named part(s)." Reading `project/main.py` shows two of those
three (capacity rings, store wells) *are* genuinely modeled — cut as
boolean subtractions into the single `trough_board` solid — just never
exposed as separately-named parts, so the part-name-prefix checker
correctly reports them absent even though the intended geometry exists.
**Attribution: pipeline limitation** (a subtractive feature on a monolithic
board is architecturally unable to satisfy a checker built around named
top-level parts, no matter how the CAD-writer models it) — this is a
sharper, more specific case of the same class Turn 12's "engraved traces on
a single plate" row already named, and `CAD_GRAMMAR.md` now has two new
rows generalizing it. One consequence worth naming for the ideator: don't
spend a high-ranked `must_survive` check on a feature that is inherently a
cut into a shared body (a ring, a pocket, a pit) unless the visual instruction
alone can carry it — the geometric half of that rank is structurally
unwinnable under the current checker. The third failed rank (seed_small
diameter count) looks like a different problem entirely: the parts *are*
present as 16 correctly-named, separate top-level bodies in both
`content.json` and the STEP manifest, and are clearly distinguishable in
every render — this reads as a scorer defect, not a modeling failure, and
is flagged in `SCORES.json`/`PAIN_POINTS.md` for the tooling to investigate
rather than folded into either agent's heuristics.

**What the one completed build did right, worth repeating:** Sluice Row's
`main.py` calls a single `small_centers()` function once to place both the
12 well cavities in the board *and* the corresponding hero-placed
seed-weights, so well/seed alignment is correct by construction rather than
by two independently-typed coordinate lists — the same "generate the shared
pattern once, reuse it" discipline Turn 14 praised for `cross_positions()`,
now confirmed as a repeatable good habit rather than a one-off. The build
also has an explicit `validate()` function that asserts the loose-fit
radial clearance (`gap >= 3.0`) before ever emitting geometry, catching
tolerance problems at build time instead of leaving them for the evaluator
to discover — worth noting the independent scorer's rank-5 clearance check
still measured 0.0mm against this same assertion, a divergence neither this
build nor prior turns have fully explained and worth watching for a pattern
across future clearance checks.
