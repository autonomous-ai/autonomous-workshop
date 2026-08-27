---
type: mechanism
name: "Increase Value of Unchosen Resources"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Increase Value of Unchosen Resources

## Definition
When players choose actions or resources, any options not selected accumulate in value, typically through added currency or bonuses. This creates a tension between immediate gain and the promise of greater rewards later, ensuring all available choices remain strategically viable and forcing players to weigh opportunity cost against future payoff.

## Relations
- component:: [[components/indexed-ratchet-wheel]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]], [[anti-patterns/first-player-advantage]]
- variant-of:: [[mechanisms/automatic-resource-growth]]

## Notes
Works best in turn-order or role-selection systems where certain resources naturally go unchosen each cycle.
Requires clear visibility of accumulation to function; hidden or difficult-to-track values undermine the mechanism's intended psychological tension.
sources: https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/ https://medium.com/theuglymonster/analysis-paralysis-how-smart-game-design-can-keep-everyone-happy-6e97f2e72b10 https://brandonthegamedev.com/where-does-analysis-paralysis-come-from/ https://boardgame.tips/the-best-games-where-unchosen-resources-increase-in-value
