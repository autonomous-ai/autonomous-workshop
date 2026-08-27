---
type: constraint
name: "FDM-Printed Components Only"
created: 2026-08-21
source: manual
status: reviewed
---

# FDM-Printed Components Only

## Definition
Every component in the product must be FDM-printable: no cards, no paper money, no stickers, no dice with printed pips finer than the nozzle can carve. Engraved text is coarse (single words, >=8 mm letters). This is the the Workshop production reality — a mechanism whose play loop lives on shuffled card text cannot ship through this pipeline.

## Relations
- conflicts-with:: [[mechanisms/hand-management]], [[mechanisms/deck-bag-and-pool-building]]

## Notes
The two conflicts-with edges name the canonical card-driven mechanisms as stand-ins for the class. "Conflict" here means: as normally implemented (a hand/deck of unique card texts). A designer can sometimes re-house the mechanism in printed tiles — that redesign is exactly the conversation this edge is meant to force.
