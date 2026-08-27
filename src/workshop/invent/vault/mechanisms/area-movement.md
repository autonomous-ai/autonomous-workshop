---
type: mechanism
name: "Area Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Area Movement

## Definition
Area movement replaces exact-distance movement with a map divided into connected regions of varying size and shape, where pieces move between areas rather than along measured paths or grid squares. Multiple units typically stack in the same area, and conflict is triggered when opposing forces share or contest a region. The tension comes from committing limited forces to open borders: a player must choose between massing strength for a breakthrough or spreading thin to hold ground, all while every adjacent area is a potential avenue of attack.

## Relations
- risks:: [[anti-patterns/kingmaking]], [[anti-patterns/turtling]], [[anti-patterns/runaway-leader]], [[anti-patterns/deadlock]]
- variant-of:: [[mechanisms/point-to-point-movement]]

## Notes
Abstracting distance into area adjacency trades simulation precision for faster, less fiddly play, but can make combat swings feel arbitrary since area size doesn't reflect real distance.
Wide-open borders between many areas create multi-front exposure, making it hard to defend everything and rewarding opportunistic strikes over sustained plans.
sources: https://en.wikipedia.org/wiki/Area_movement https://bombardgames.com/board-game-mechanics-area-movement/ https://en.wikiversity.org/wiki/Game_mechanics/Area_Movement https://www.skeletoncodemachine.com/p/kingmaking
