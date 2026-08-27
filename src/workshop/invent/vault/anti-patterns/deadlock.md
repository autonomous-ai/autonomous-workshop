---
type: anti-pattern
name: "Deadlock"
created: 2026-08-21
source: manual
status: reviewed
aliases: [dead_state]
---

# Deadlock

## Definition
A state where no player can act, or where every legal action makes its actor strictly worse off, so all players stall and the game stops progressing without ending.

## Relations
- mitigated-by:: [[rule-patterns/forced-engagement]]

## Notes
A termination proof is the real cure: some resource must monotonically deplete every round. Simulation catches this as games that never end.
