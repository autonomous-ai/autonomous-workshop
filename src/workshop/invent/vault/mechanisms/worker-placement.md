---
type: mechanism
name: "Worker Placement"
created: 2026-08-21
source: manual
status: reviewed
bgg_id: null
---

# Worker Placement

## Definition
Players take turns assigning a limited pool of worker pieces to action spaces on a shared board; an occupied space is blocked (or costlier) for everyone else until workers return. The tension comes from the serialized queue of claims: what you take, you deny. Turn order and worker count are the levers that tune it.

## Relations
- conflicts-with:: [[mechanisms/simultaneous-action-selection]]
- variant-of:: [[mechanisms/action-drafting]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/analysis-paralysis]]
- component:: [[components/worker-meeple]]

## Notes
DEMO CONFLICT EDGE (declared both sides, see the target node): worker placement's whole economy is the serialized, blocking claim queue — I see what you took before I choose. Simultaneous action selection removes the queue; with both applied to the same action pool, blocking either becomes meaningless (everyone commits blind) or non-deterministic (two workers on one space with no rule for who was first). They can coexist only in separate phases acting on separate pools, which is a different design than combining them.
