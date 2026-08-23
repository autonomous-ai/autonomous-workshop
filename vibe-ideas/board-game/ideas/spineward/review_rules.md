Verdict: PASS

# Spineward - rules-worth-playing review (fresh, 2026-08-18)

Independent judgment of the CURRENT `idea.json`, not the 2026-08-14 PASS. The
only rules change since then is `rules:turn[8]` (ROB): it now lists a fifth
precondition, "that enemy is carrying at least one pearl in its sockets," and
states that if the target carries no pearl "ROB simply is not offered as a
move - it costs you nothing, but it does nothing either." That closes the
`rules_ambiguous` finding the playtest gate raised (the old four-condition
text left the empty-target case undefined and the alternative reading moved
the numbers). Nothing else in the rules changed. I judged the current text in
full; the conclusions below apply to it as written.

Geometry checked on cube coordinates: 37 pans, 19 seed pans (r0-r2), 6 corner
landing shelves (r3), each shelf adjacent to exactly one seed pan (the r2
corner); each of the three corner diagonals runs shelf, r2, r1, centre, r1,
r2, shelf (7 pans).

## Dominant strategy: contested, not broken

The shortest credible line is the deep traverse: arm one spine down a
diagonal, one onto the corner shelf; CREEP onto the shelf, SHED the
shelf-spine (Turn 1), then TAKE-and-CREEP down the diagonal one pearl per turn
(Turns 2-6), CREEP onto the far shelf and LAND all five (Turn 7). Five pearls
at the 1.69 mean is ~8.4 points in about six genuine turns.

That line is not dominant, and the reasons are structural, not luck:

1. Time-value of banked versus unbanked points. A traverse scores nothing
   until Turn 7; a boundary shuttle (park on a shelf, TAKE the one adjacent r2
   seed pearl, LAND it next turn) banks ~1.69 points by its second turn at
   roughly 0.85 points/your-turn against the traverse's ~1.2. Banked points
   are immune to both the reef-empty trigger and to robbery; unbanked ones are
   not. "How deep do I go before I turn back" is a genuine read, not a
   calculator.
2. Reef-empty cuts deep divers. Standing pearls leave the reef on TAKE. A
   racing table empties the reef before a deep diver lands, and pearls still
   in sockets score zero (rules:win). Endgame sack losses are real.
3. A loaded urchin is maximally robbable. Five pearls + one forward spine uses
   all six sockets, so GROW (the only way to raise a shield toward a chaser)
   is illegal; the collector must SHED then GROW or spend TURNs to face the
   pursuit. Robbing nets the ~1.69 mean per single action, the best rate in
   the game, but the robber still has to walk the haul to a shelf. Worth doing
   opportunistically, not worth building around - the right shape.
4. The centre chokepoint. All three diagonals meet in the centre pan; whoever
   takes it first forces GROW-and-detour on the other two lines and, at four
   players, a collision is forced by pigeonhole.

The midgame also checks out: as the boundary seed pans near shelves empty, play
drifts inward, which is exactly where the defence/cargo socket tension and the
robbery risk live. The game's risk curve rises as the safe pearls are taken
first. That is a design, not an accident.

## Real decisions per turn

Three or more live ones every turn. The core is the socket budget: every spine
is a cargo slot given up and every pearl is a direction given up, and that is
re-allocated by GROW/SHED/TURN every single turn rather than fixed at setup.
TURN is one action to re-aim the whole rosette against SHED+GROW's two, so it
is strictly better for a 60-degree change and strictly worse for 180 - a real
choice. DROP both buys a socket back mid-reef and walls off a chaser (a
standing pearl blocks CREEP), so it is attack and defence at once. The one
deliberately fake decision is "which pearl to rob/take" - blind by design; the
hidden foot is the point, not a gap.

## Ending, length, player count

Ending is reachable and multiple-ended. Three triggers: no pearl standing on
the reef, any rack at six, and the quiet-round clause (rules:end[1]). The
playtest engine ran 400 random 2p and 400 random 4p games with zero stuck and
zero undefined - no deadlock. The quiet-round trigger is a sensible safety net
that also fires in real play if both players stall rather than contest.

Length is compatible with the 40-minute claim. Random 4p play runs long
(turns_mean 65.8, median 52) but that is churn-heavy and unrepresentative of
human play; the efficient shuttle/traverse equilibrium is ~0.7 to 0.9 pearls
landed per player-turn, so a 16-pearl, ~27-point reef resolves in roughly 35
to 45 total player-turns at four, i.e. about 40 minutes. Two players resolve
sooner (engine median 26 turns), a little under the claim, which is typical
and acceptable.

## The weakest seat count is two, and the playtest now quantifies it

At two players the reef is over-supplied (37 pans, 16 pearls, two urchins) and
contact is optional, so both players can blind-collect and land near-equal
totals near half the 27-point pot. The engine's passive competent policy
finished 75% of 2p games level through the full tiebreak chain (tie_rate
0.754, margin_mean 0.32). This is genuinely the weakest count: at two the game
leans toward a parallel race whose floor is set by the random pearl draw. Two
cautions before over-weighting it: the competent policy never robs at 2p (no
`rob` in its chosen kinds), so the "chaser" dynamic the rules make fully
available - a robber taxing the leader's haul - is what a live 2p duel is
supposed to supply, and that is an active-play tool, not a hard cap. Still,
this is the one place the current text is fragile, and the brief should give
2p something to force contact or sharpen the scoring tiebreak. It is a
tuning/design note for the brief, not a mechanical break - the 2p game does
end, every time, and it is contingent on decisions a table can make.

## The two old dead-letters survive verbatim; correct the brief's claims

Re-checked against the current text, both old findings stand unchanged because
the rework never touched them:

1. Six-pearl paralysis is unreachable. TAKE, DROP and ROB all need a spine to
   reach with, and a separate empty socket to receive into; once five pearls
   and the lone spine fill all six sockets there is no direction left that is
   both empty and not the reach-spine, so no sixth pearl can ever be acquired
   (verified: max load is five pearls + one spine). The corollary sentence at
   `rules:turn[10]` ("an urchin with six pearls cannot move, cannot reach,
   cannot defend itself and cannot even shed") and the concept/novelty
   "a fully-laden one cannot move or defend itself" both describe a state the
   rules make impossible - a five-pearl urchin can, in fact, move and defend
   in one direction. Fix the language so it says five, or the hero text
   asserts something the rules forbid.
2. The spine supply never binds. Total capacity across a full table is exactly
   24 (four shells at six), no winning build runs more than about three, and a
   six-spine turtle scores nothing by construction, so the shared tray is never
   meaningfully short. Setup's "spines can genuinely run short" and GROW's
   "if the tray is empty you cannot grow" are dead letters at every count. The
   real budget is the six sockets per shell; the text should say that and drop
   the supply-tension promise.

## Spoiler check, still clean

A player who empties the reef while holding five scores zero and cannot reach
the spine tiebreak unless every opponent is also on zero, which cannot happen
after round two. Denial is available; kingmaking by self-destruction is not.

## Bottom line

The rules are now mechanically complete (ROB fixed), the socket-tradeoff core
has no dominant line I could find across opening, midgame and endgame, the
ending is reachable with no deadlock, length sits on the 40-minute claim at
four players, and the strongest count (four) is genuinely contested. Two is
the weak count and the two dead-letter overstatements should be fixed in the
brief, but nothing in the current text makes this game unplayable or
automatic. It is a real game. PASS.
