---
type: anti-pattern
name: "Degenerate Strategy"
created: 2026-08-21
source: manual
status: reviewed
aliases: [dominant_action]
---

# Degenerate Strategy

## Definition
One line of play dominates everything else, and the game collapses into executing it faster than your neighbour. All other content becomes decoration.

## Relations
- mitigated-by:: [[rule-patterns/diminishing-returns]]

## Notes
Greedy-bot-vs-random simulation finds these embarrassingly fast; if one policy wins ~100%, the policy IS the game.
