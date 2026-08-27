---
type: mechanism
name: "Enclosure"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Enclosure

## Definition
Enclosure is a spatial control mechanism where players place or move pieces to surround contiguous areas on a gridded board, claiming territory that scores based on its size. The core tension emerges from players balancing territorial expansion (which increases point potential) against strengthening and defending already-held regions—larger enclosures are worth more but require more boundary maintenance, making players vulnerable while expanding.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/turtling]], [[anti-patterns/kingmaking]]
- variant-of:: [[mechanisms/area-majority-influence]]
- requires:: [[mechanisms/grid-coverage]]

## Notes
Enclosure differs from area-majority by having players dynamically create regions during play rather than fighting over static zones; Go is the canonical exemplar.
Scoring tied directly to enclosed area size creates inherent tension but also rewards cautious play and risks runaway leaders.
sources: https://www.bgdf.com/forum/archive/archive-game-creation/game-design/game-mechanic-area-enclosure https://spielbound.org/game-tags/area-enclosure https://boardgame.tips/the-best-games-in-which-you-can-enclose-a-territory-or-area https://medium.com/theuglymonster/analysis-paralysis-how-smart-game-design-can-keep-everyone-happy-6e97f2e72b10
