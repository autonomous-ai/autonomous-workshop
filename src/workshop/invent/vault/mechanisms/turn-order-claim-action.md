---
type: mechanism
name: "Turn Order: Claim Action"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Turn Order: Claim Action

## Definition
Turn order for the next round is set by which action a player claims this round, rather than by fixed seating or a die roll. Actions that are stronger tend to carry a worse future turn position, while weaker or leftover actions push the claimant toward going first next time, so every choice is really two choices bundled together: what you get now versus where you sit later. The tension comes from valuing an immediate payoff against a positional payoff that only pays off next round, forcing players to price the two against each other with each pick.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/spiral]], [[anti-patterns/trap-option]], [[anti-patterns/kingmaking]]
- variant-of:: [[mechanisms/variable-phase-order]]

## Notes
Frequently doubles as an implicit catch-up mechanism when the strongest actions are paired with the worst future turn position (Kingdomino, Broom Service).
Works best when a turn is a bundle of several small actions rather than one big action, since a single-action turn leaves no room for the position trade-off to matter.
sources: https://circlejgames.com/irregular-turn-order/ https://www.gamesprecipice.com/turn-order/ https://www.bgdf.com/forum/game-creation/mechanics/worker-placement-and-variable-turn-order
