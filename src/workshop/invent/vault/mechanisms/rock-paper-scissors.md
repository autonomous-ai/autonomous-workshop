---
type: mechanism
name: "Rock-Paper-Scissors"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Rock-Paper-Scissors

## Definition
Players simultaneously select from three options, each cyclically dominant over one choice and subordinate to another, creating inherent balance through intransitive relationships. Tension emerges from the blind commitment combined with prediction and the need to outread opponent behavior across repeated plays.

## Relations
- component:: [[components/hidden-choice-selector]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/degenerate-strategy]]
- requires:: [[mechanisms/simultaneous-action-selection]]

## Notes
Balance is structurally fragile: any divergence from perfect 1-beats-1-loses-to-1 breaks into solved degenerate play.
Expanding to five options (Lizard-Spock) maintains equilibrium if each new choice beats exactly two and loses to exactly two others.
sources: https://80.lv/articles/how-strategy-games-apply-the-rock-paper-scissors-mechanic https://www.gamedeveloper.com/design/rock-paper-scissors---a-method-for-competitive-game-play-design https://www.gamedeveloper.com/design/rock-paper-scissors---and-why-games-don-t-really-get-it https://blog.darkwood.com/article/rock-paper-scissors-a-minimal-model-of-balance-and-strategy
- [yt:av5Hf7uOu-o] medium: Despite feeling skill-driven, simultaneous-choice duels like Rock-Paper-Scissors sit in a genuine middle zone between luck and skill, not cleanly at either end. (IGDA Denmark 2013)
- [yt:F_1YcCcBVfY] low: In an attack-vs-defense matching game, players preferred committing first (full self-knowledge) over choosing second against a hidden pick, even though both options are informationally equivalent. (GDC Festival of Gaming 2018)
