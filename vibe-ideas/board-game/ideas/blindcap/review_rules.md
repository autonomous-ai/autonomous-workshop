Verdict: PASS

# Blindcap — independent rules-worth-playing review, 2026-08-18

Fresh judgment of the CURRENT `idea.json` only, after the contested-grove scoring
resolution. No brief, no CAD, no component/dimension judgement. The prior 2026-08-14
PASS was not trusted; this restates the case on the delivered text.

## The contested-grove resolution holds

The win rule now reads cleanly and I could not break it:

- Grove with crowns all one owner: that owner scores n x n, once.
- Grove with crowns of 2+ owners (contested): EACH owner scores n, once per owner.
- inkcap / hollow grove pays double; crowned-scarce is a big swing either way.
- A second of your own crowns in any grove is wasted — "pays once per owner"

The contested case is the right incentive shape, not a degenerate one. A rival who
contests your n=4 grove earns n=4 while denying you n^2 - n = 12: a real spoiler
decision with a real crown cost and a real information bar (you must identify the
grove before harvest). Against a scarce double-grove the stakes are even higher (deny
24 from a 32), which is exactly the drama the scarce species are for. The "wasted
second crown" rule removes any incentive to over-stuff your own grove, so every crown
must find a new value source. No double-counting, no monotonicity break, no dominant
"never crown" collapse.

## Dominant strategy: none found

Walked openings at 2p and 4p.

- **Spread out / stay unreadable.** Six non-adjacent stools = six groves of 1, worth
  1-2 each, 3-6 total with three crowns. Self-defeating; adjacency is forced to score.
- **Solo pair only.** Each player owns at most 2 of any species (2/2/1/1 common/scarce),
  so acting alone the ceiling is a 2-grove = 4 (8 if scarce). Any grove of size 3+
  necessarily mixes two or more players' hidden species — you cannot score big without
  depending on material you must buy, and buying it publicly. This structural fact is
  what keeps the game non-degenerate: the biggest scores are exactly the ones loaded
  with hidden information.
- **Chase the biggest n.** Deadhead is most common (8 on board at 4p) but an orthodox
  8-grove needs all four players' deadheads connected and one player to own every crown —
  unreachable. Achievable groves are 2-4, where the scarce x2 is competitive (inkcap
  pair 8 vs common 3-grove 9). Scoring curve is not degenerate at achievable n.
- **Hoard every crown to the last round.** Unavailable: one action in the closing round,
  so at most one crown can be held to the end; the other two must land by rounds 5-6.
  The action economy forces commitment and prevents a pure pass-until-reveal.

## Real decisions per turn

A turn is plant + one free action. Real choices: which stool to plant (roughly four
distinct species, and holding your single scarce stool to place against a rival's is a
genuine timing play), which socket (placement both builds and denies — 18 sockets for
12 stools at 2p, so blocking matters), whether to probe which rival socket's which band
(upper splits {bracket,hollow}|{deadhead,inkcap}, lower splits the scarce pair off, so
one probe gives partial truth and full identity needs two scarce pins — a real probe
budget), or crown which stool on thinnest information. Three real choices a turn, not
fake options.

## Reaching an ending

Fixed six rounds + one closing round + harvest. Plant is mandatory while stools remain,
nothing can stall termination: an empty pin heap only retires the probe action; crown
and pass stay legal. All 12 crowns are placeable in the action budget. Total-order win
with two tiebreaks. Ending guaranteed and reachable.

## Length

2p = 14 turns, 3p = 21, 4p = 28, plus a harvest that is a genuine 3-5 minute group-
resolution at 4p. At 45-75s per turn once deduction bites, 2p lands near 20 min and 4p
near 35-40 including harvest. `playtime_min: 30` is a fair nominal, mildly optimistic at
4p, not mis-specified.

## Player count

Works at both ends; 2p is arguably the sharpest, the reverse of the usual degenerate
case. At 2p the entire unknown is one rival's assignment of a known composition to six
known-owned sockets, cut down by probes plus supply deduction — a clean closed puzzle,
and interaction is real (blocking, contesting, spoiling). At 4p the probe-leak
public-goods tension (a probe informs every other seat) replaces the tight puzzle. Not
solitaire at either end.

Count-dependent watch items, carried forward, not failures:

- The 16-pin supply is only tight at 4p (max 8 probes at 2p, 12 at 3p).
- PASS is near-dominated at 2p (probing a sole rival's stool leaks them nothing they
  don't know), but earns its place at 3-4p where a probe informs the next seat first.
- Last-seat gets the final closing word AND the tiebreak — two compensations for one
  small disadvantage; worth measuring in playtest.

## Not judged here

Pin sink/proud legibility, groove depth, socket pitch, the clearance contract, tray
sightlines, crown diameter vs pitch. Those belong to the object lens.
