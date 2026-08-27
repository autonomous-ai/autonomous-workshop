---
type: mechanism
name: "Action Points"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Action Points

## Definition
Action Points give each player a fixed budget of generic tokens per turn that can be spent across a shared menu of distinct action types (move, build, trade, attack, etc.), with each action carrying its own point cost. The tension comes from optimizing an unequal, interacting menu of options against a hard budget: players must weigh opportunity cost between actions rather than just executing a single fixed move, and the 'one more point' feeling of always wanting slightly more budget than available drives the strategic squeeze. Because the pool resets or partially carries over each turn, it also shapes pacing by capping how much any single player can accomplish before turn transfer.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/idle-player]], [[anti-patterns/multiplayer-solitaire]]

## Notes
Paralysis scales with the number and value-inequality of available actions per point, not with the raw point total, so trimming the action menu is a more effective fix than trimming points.
Serial single-active-player implementations create spectator downtime for others; simultaneous or short-fuse variants trade that for less deliberate optimization.
sources: https://www.bert.games/post/strategic-allocation-unpacking-action-points-in-board-games https://islaythedragon.com/guides/where-the-actions-at-a-guide-to-action-point-allowance/ https://www.bgdf.com/blog/bg-mechanics-4-action-points https://www.universityxp.com/blog/2022/10/25/what-is-analysis-paralysis
