---
type: anti-pattern
name: "Fiddly Reset"
created: 2026-08-24
source: agent
status: reviewed
---

# Fiddly Reset

## Definition
Packing up or resetting for the next round takes longer than playing one.

## Relations
- mitigated-by:: [[rule-patterns/play-ready-component-trays]], [[rule-patterns/reset-in-place]]

## Notes
- Measure the complete hands-off-to-ready interval during testing; overlooked retrieval and reorientation usually dominate the reset.
- A storage-efficient insert is not necessarily a play-efficient reset system.
- sources: https://boardgamegeek.com/blog/12035/blogpost/183959/designing-a-3d-printed-insert https://herotime1.com/academy/pieces/how-to-design-your-board-games-insert-for-best-results/ https://www.theboardgamefamily.com/2017/07/karuba-game-insert/
