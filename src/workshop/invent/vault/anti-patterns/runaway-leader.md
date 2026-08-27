---
type: anti-pattern
name: "Runaway Leader"
created: 2026-08-21
source: manual
status: reviewed
---

# Runaway Leader

## Definition
An early lead compounds into an uncatchable one: the leader's position generates more resources which generate more position. Mid-game the outcome is decided; the table just hasn't stopped playing yet.

## Relations
- mitigated-by:: [[rule-patterns/diminishing-returns]]
- mitigated-by:: [[rule-patterns/catch-up-mechanism]], [[rule-patterns/hidden-scoring]]

## Notes
Diagnose by simulation: if win probability at 1/3 game time exceeds ~80% for the current leader, you have one.

- [yt:z7_s7KdrtpA] medium: Runaway leaders mainly hurt long, low-interaction games; in short games (<45 min) or 2-player abstracts, an early sensed winner doesn't matter since the game ends before it drags. (Adam in Wales - Board Game Design 2016)
