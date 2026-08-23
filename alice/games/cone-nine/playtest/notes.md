# KILN: the Firing Dial — executable-model playtest notes

## What this model proves

The model is a rules and routing check, not evidence that the physical game
is fun. It is the authoritative gate run through the lane's own harness
(`bob/loops/playtest.py` `run_sim`, which lints the engine source, binds it by
content hash to `idea.json`, and measures the GAVEL five, the Browne
aesthetic tier, and the random<greedy<lookahead1 skill ladder).

The engine implements, exactly:

- the shared 4x4 tray of sixteen wells and the single shuffled firing dial,
- one public band revealed per placement, constraining OPEN / SHY / REGION /
  FAR placements,
- the band fall-back to any empty well when no constrained well exists
  (registered as an assumption, never guessed),
- two distinct hidden objective tiles per player, satisfied only on the
  finished tray,
- the fixed 16-placement structure that always fills the tray with exactly
  8 discs per player (structural material parity),
- region size-squared scoring plus satisfied-objective bonuses, and the
  region-only tiebreak.

## Evidence (authoritative gate, seed 7, 200 games)

Command (BOB_HOME = alice checkout, engine at
`games/kiln-firing-dial/playtest/engine.py`):

```
BOB_HOME=/Users/d/code/inventors/alice python3 /tmp/kiln_gate.py
```

Result: **`all_pass: True`** for 2 players, all nine verdicts green.

- GAVEL: balance 0.91, agency 0.879, completion 1.0, decisiveness 0.97,
  harmonic mean 0.937.
- Skill ladder (monotone staircase, all edges above the 0.15 floor):
  greedy over random +0.275, lookahead1 over greedy +0.150, lookahead1 over
  random +0.250.
- Balance: strongest-seat spread 0.030 (lookahead1 mirror 0.515/0.485); max
  seat winrate 0.545 (random), below the 0.85 runaway cap and within the
  45-55% band.
- Agency: median branching 5.0, forced fraction 12.1% (floor is 25%).
- Duration: median 16 placements (the full tray), completion 100%.
- Browne: mean lead changes 2.68, drama (winner was behind) 0.87, late
  uncertainty 0.66 — the game stays competitive into the final placements.
- Coverage is skipped: the contract exposes no board sites, so None is
  excluded from the harmonic mean, never treated as a pass.

## What this does NOT establish

- Physical printability, dial rotation feel, disc seating, and handling time.
- Whether the hidden objectives feel fair or readable to humans.
- Whether the game is fun. That requires a printed set followed by blind
  human tables; this is routing evidence for fabrication, not release
  evidence.

## Determinism

All randomness derives from the seed passed to `new_game` (dial shuffle and
objective draws). The same seed reproduces the same game. The gate ran 200
games under seed 7; the requested >=100 deterministic rounds is exceeded.
