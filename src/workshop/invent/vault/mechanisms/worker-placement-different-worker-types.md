---
type: mechanism
name: "Worker Placement, Different Worker Types"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Worker Placement, Different Worker Types

## Definition
Players deploy a limited pool of workers that vary in their abilities, action availability, or resource values to claim different actions on the board. The core tension arises from matching each worker's unique strengths to the most effective action slots before opponents occupy them, forcing a sequence-of-trade-offs between immediate needs and reserving specialized workers for future turns. This transforms standard worker placement from pure action scarcity into a combinatorial puzzle of worker-to-action fit.

## Relations
- component:: [[components/snap-fit-state-token]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/alpha-solve]], [[anti-patterns/first-player-advantage]], [[anti-patterns/runaway-leader]]
- variant-of:: [[mechanisms/worker-placement]]

## Notes
The Grande worker pattern (Viticulture) shows one successful implementation: a rare, multi-use exception that breaks blocking rules and rewards timing.
When multiple worker types exist but only a few are truly valuable in any given game state, the mechanism risks collapsing into predetermined deployment order rather than meaningful choice.
sources: https://www.meeplemountain.com/mechanisms/worker-placement-different-worker-types/ https://tabletopgamesblog.com/2023/11/07/working-hard-a-look-at-worker-placement-mechanisms-topic-discussion/ https://brain-games.com/en-us/blogs/board-game-explorer/ultimate-guide-to-worker-placement-strategies https://www.leagueofgamemakers.com/how-to-design-a-worker-placement-game-part-2/
