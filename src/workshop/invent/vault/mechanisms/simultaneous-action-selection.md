---
type: mechanism
name: "Simultaneous Action Selection"
created: 2026-08-21
source: manual
status: reviewed
bgg_id: null
---

# Simultaneous Action Selection

## Definition
All players secretly choose their action for the round (cards, dials, plotted orders), then reveal and resolve at once. It compresses downtime to near zero and creates read-your-opponent tension, at the price of blind collisions: two players committing to the same contested thing with no way to react.

## Relations
- component:: [[components/hidden-choice-selector]]
- conflicts-with:: [[mechanisms/follow]]
- conflicts-with:: [[mechanisms/worker-placement]]
- risks:: [[anti-patterns/luck-swing-endgame]]

## Notes
DEMO CONFLICT EDGE — mirror of the note in worker-placement: simultaneity deletes the serialized claim queue that worker placement's blocking depends on. Blind collisions late in a close game are why risks:: points at luck-swing-endgame: a coin-flip guess between two leaders reads as luck, not play.
