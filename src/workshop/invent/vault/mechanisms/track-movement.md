---
type: mechanism
name: "Track Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Track Movement

## Definition
Track Movement confines all player pieces to progression along a predefined linear path, creating a shared race condition where position on the track is the primary strategic axis. Tension arises from the conflict between randomized movement (which feels unfair but prevents optimization) and strategic movement choices (which enable planning but can favor leading players). The confined pathway creates meaningful position advantage while limiting players' freedom compared to free-form spatial movement.

## Relations
- component:: [[components/detented-slider-track]]
- risks:: [[anti-patterns/dead-range]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/point-to-point-movement]]

## Notes
Separating track movement from other player actions concentrates tension and prevents mechanical bloat.
Mixing random and deterministic movement (dice + optional paid choices) addresses the strategic fairness problem without purely random outcomes.
sources: https://www.meeplemountain.com/mechanisms/track-movement/ https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics https://boardgamedesigncourse.com/game-mechanics-how-to-create-tension-in-your-game/ https://playthistonight.com/posts/some-thoughts-on-roll-and-moves/
