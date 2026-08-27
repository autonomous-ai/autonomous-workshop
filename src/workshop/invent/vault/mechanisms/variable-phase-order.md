---
type: mechanism
name: "Variable Phase Order"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Variable Phase Order

## Definition
In a Variable Phase Order game, the sequence of phases making up a round is not fixed from round to round — it shifts based on player choice (such as selecting a role that determines which phase triggers next), a card, a track, or another game element. Because the sequence changes, the value of any given action depends on where it falls relative to the other phases that round, so a phase or role can't be evaluated in isolation. The tension comes from having to weigh 'what to do' against 'when it will happen relative to everything else', turning the ordering itself into a strategic resource rather than a fixed backdrop. It is frequently layered onto role-selection, where one player's pick of the next phase sets the sequence for that whole round for everyone.

## Relations
- component:: [[components/stackable-order-counter]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/silent-calc]]
- requires:: [[rule-patterns/variable-turn-order]]

## Notes
Often paired with role-selection (Puerto Rico-style) so that choosing the phase order becomes the turn's central decision.
Symmetric variants (order shifts via a track or card, affecting all players equally) sidestep the single-player-control risk that role-chosen order variants can introduce.
sources: http://www.boardgamizer.com/mechanics/definition/variable_phase_order http://www.gamelevellearn.com/game/2018/8/19/51-mechanics-variable-phase-order https://www.boardgameatlas.com/mechanic/zzsE4jtI1b/variable-phase-order https://stratsynergy.wordpress.com/game-mechanics/variable-phase-order/
