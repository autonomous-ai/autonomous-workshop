# CONE NINE — executable-model playtest notes

## Current verdict: HOLD

The prototype is coherent and substantially improved, but it is not cleared
for fabrication or publication. The authoritative 1,600-game gate passes eight
of nine checks and fails the strongest-policy seat-bias check by one percentage
point: lookahead mirror win credit is 55.5% / 44.5%, a spread of 0.110 against
the 0.100 ceiling. `sim_report.json` is the binding receipt; `all_pass` is
honestly `false`.

This is deterministic digital-model evidence only. It is not a human expert
panel, a human playtest, proof of fun, or physical evidence.

## Invalid prior receipt

The inherited 200-game report could not be trusted. The saved engine was left
mid-edit: it removed `OBJ_BONUS` but still referenced it in `scores()`, so a
fresh run crashed. Its objective definitions also disagreed with `idea.json`
and the rules. This iteration discarded that report as stale, repaired the
model, rebound `IDEA_SHA`, and regenerated every number below.

## Evidence-backed changes

- Renamed **KILN** to **CONE NINE** after finding the existing nestorgames
  pottery board game.
- Replaced a physically impossible “shuffle printed dial bands, then load
  them” setup with one fixed printed cycle and a random starting click.
- Replaced six all-or-nothing goals with eight per-cell glaze maps. The maps
  form one full rotation/reflection family; every map has eight targets: two
  corners, two centres, and four other edge wells.
- Deal maps without replacement, so all four active maps are distinct.
- Added legal-move rejection and fixed seat-safe observation labels.
- Added a second-player exact-tie win after both total and region-only scores
  tie. The rule removes unresolved draws and partially compensates for the
  first placement; it does not fully clear the strongest-policy seat gate.

## Authoritative gate

`sim_report.json` — seed 29, 1,600 deterministic games through
`bob/loops/playtest.py run_sim`:

- overall: **8/9 gates pass; `all_pass: false`**;
- completion 1.000; decisiveness 1.000;
- random seat credit 0.471875 / 0.528125; balance score 0.94375;
- agency 0.887305; forced-turn fraction 0.112695; median branching 5;
- skill edges: greedy>random +0.2125, lookahead>greedy +0.1125,
  lookahead>random +0.290625;
- strongest mirror 0.555 / 0.445, spread 0.110 (**only failing gate**);
- median duration 16 placements; mean lead changes 4.0875; drama 0.89375;
- GAVEL harmonic mean 0.955427 (coverage unmeasured and excluded, not passed).

## Fixed-draw and map-value audit

`objective_audit.json` controls every ordered pair of disjoint two-map hands
at all 16 dial starts: 6,720 deterministic own-score-greedy games. It also
checks 600 setup seeds.

- all eight map ceilings: exactly 8;
- appearances per map: exactly 3,360;
- realized mean map bonus: 4.9929–5.0491, spread **0.05625**;
- fixed-draw seat credit: 0.530804 / 0.469196;
- unresolved wins: 0%;
- duplicate active maps, nondeterministic setup, or non-rotational dial: 0.

The previous semantic-map candidate produced a 3.003-point realized bonus
spread (HEART 7.3125 versus 4.3094–5.4208). The symmetry-family change reduced
that spread by 98.1%; it is retained.

## Seat stability check

`seat_stability.json` holds the rules fixed and expands only the lookahead
mirror: 1,600 games across seeds 29, 101, 307, and 911. Aggregate seat credit
is 0.54125 / 0.45875 (spread 0.0825). Seat 0's Wilson 95% interval is
[0.51676, 0.56554], which still includes outcomes beyond the 10-point spread
line. This explains why the canonical sample is borderline; it does not turn
the failed authoritative receipt into a pass.

## Next iteration

Test one structural opening change at a time against the same three receipts:
fixed-draw matrix, multi-seed lookahead stability, then authoritative gate.
The leading experiment is a symmetric two-disc setup before the dial begins,
not a score credit fitted to one seed. Keep the current version held unless a
rule clears the gate across rotated starts without breaking random balance,
agency, or the skill ladder.

Physical dial feel, disc seating, map legibility behind screens, rules
comprehension, and fun remain untested. No Factory draft should be created
until the digital hold clears and a print coupon is measured.
