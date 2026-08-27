---
type: mechanism
name: "Hidden Victory Points"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Hidden Victory Points

## Definition
Players accumulate victory points during play that are concealed from opponents, typically hidden behind screens or tracked privately. Tension emerges from strategic uncertainty—no player knows definitively who is winning until final scoring, preventing dominant players from being targeted and keeping trailing players engaged throughout. This imperfect information forces decisions based on probability and inference rather than certainty.

## Relations
- component:: [[components/hinged-privacy-screen]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/decided-early]], [[anti-patterns/kingmaking]], [[anti-patterns/silent-calc]]

## Notes
Implementation quality matters: if players can reverse-engineer scores through deduction, tension collapses into a memory/arithmetic game.
End-game scoring must be proportionate to in-game points—oversized end-game bonuses undermine the hiding and create anticlimactic reveals.
sources: https://boardgamedesignlab.com/mechanism-master-list/ https://www.bgdf.com/forum/archive/archive-game-creation/game-design/how-make-victory-points-exciting https://forum.frontrowcrew.com/discussion/8839/board-game-design-mechanic-question-why-hide-non-secret-information https://medium.com/@BastiaanSquared/victory-points-and-board-game-design-1e9ef00f901b
