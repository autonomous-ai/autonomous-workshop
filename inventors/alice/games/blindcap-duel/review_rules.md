Verdict: PASS — executable rules; blind-human review still required

# Blindcap: Duel — rules review, 2026-08-23

This review covers the current two-player rules and executable engine. It does not clear physical fit, comprehension by first-time players, fun, legal novelty or public sale.

## The decision is real

Every player has five main actions. Their inventory fixes the mix at three probes and two early crowns; no pass exists. A probe earns one public bit and leaves its marked pin on the board until harvest. A crown converts a theory about a hidden grove into a claim. The player chooses the order, so more certainty always costs earlier access to the scoring map.

The closing crown prevents perfect-information waiting. Both players seed the centre simultaneously, and the round starter alternates across all six action rounds. Each seat acts first three times and second three times.

## The physical mechanism matters to the rules

The four species form a complete two-bit code:

- deadhead: high / high
- bracket: low / high
- inkcap: high / low
- hollow: low / low

The first value is the one-dot channel; the second is the two-dot channel. The D-flat keys each buried shank so those parallel routes cannot swap.

One probe halves the possibilities. Two identify a stool. A player's three marked pins can fully identify one rival stool and sample another, or distribute information across three stools. The final tiebreaks reward useful probe placement without making probes worth points during ordinary scoring. At harvest, players record all four public probe counts, withdraw every pin completely to 34mm proud, and only then lift and invert the stools cap-down in their original cells.

## Scoring has conflict

An uncontested grove of `n` scores `n²`; a grove containing both players' crowns pays only `n` to each. Inkcap and hollow groves double. A second crown by the same player in one grove adds nothing. Large scores therefore require spatial cooperation among hidden species, while a rival can spend a scarce crown to contest a suspected grove.

## Termination and legality

Every complete game has exactly 24 applied moves:

- 2 simultaneous-modelled seed choices
- 10 plants
- 6 probes
- 4 early crowns
- 2 closing crowns

There is always a legal required action. Each player targets only the rival's six stools; twelve rival probe channels exist for three pins, and six rival stools exist for three crowns.

## Automated routing evidence

Command:

```sh
python3 board-game/tools/playtest.py board-game/ideas/blindcap-duel \
  --games 400 --ladder-games 60 --mc-budget 30 \
  --out board-game/ideas/blindcap-duel/playtest.json --deadline 300
```

Result: `PLAYTEST PASS`, zero findings.

- 400/400 competent games ended naturally.
- Every game took 24 moves.
- Competent seat split: 50.75% / 49.25% including shared-win credit.
- Best-seat 95% interval: 45.87%–55.62%.
- Shared wins: 8.5%.
- Greedy beat random in 90% of 60 rotated-seat games.
- Zero stuck states, undefined rules, hidden-information leaks or unused move types.
- Median branching: 8 legal moves; forced-turn fraction: 0%.

The earlier four-player rules failed the two-player seat gate at 85% for the later seat and often made probing irrelevant. Those rules are retired. The Duel rules do not restore a seat-order tiebreak; they use earned, seat-neutral comparisons and then allow a shared win.

## What remains unknown

- The automated competent policy is a routing heuristic, not a human deduction model.
- No blind pair has learned the game from the current rules.
- No printed set has proved tray screening or the 3.0 mm / approximately 28 mm probe reading.
- Repeated play may expose an opening pattern the 400-game model missed.

Use `content/playtest-script.md` for the minimum six-game blind protocol. Do not turn this rules PASS into a public-sale claim before that evidence exists.
