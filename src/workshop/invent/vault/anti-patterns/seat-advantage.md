---
type: anti-pattern
name: "Seat Advantage"
created: 2026-08-21
source: agent
status: reviewed
---

# Seat Advantage

## Definition
A player's seat determines who picks, acts, or scores first, and in games with fixed rotation or setup order that structural edge doesn't average out over play. Evidence spans several shapes: a lap or round count that doesn't divide evenly by player count keeps handing certain seats more first turns, a fixed setup pick-order gives early seats the best options, and an end-of-game trigger firing mid-round can let an earlier seat win before later seats get equal turns. The usual fix is to make turn or pick order respond to game state (reverse it, or let whoever is behind choose) instead of staying fixed by seat.

## Relations
- mitigated-by:: [[rule-patterns/catch-up-mechanism]]
- mitigated-by:: [[rule-patterns/variable-turn-order]]

## Notes
