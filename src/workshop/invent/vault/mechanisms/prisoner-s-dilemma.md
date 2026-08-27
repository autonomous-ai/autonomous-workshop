---
type: mechanism
name: "Prisoner's Dilemma"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Prisoner's Dilemma

## Definition
Each player simultaneously chooses between cooperation and defection in a single decision point, with a payoff structure where mutual cooperation yields the best collective outcome, yet defection is individually rational regardless of the opponent's choice. The mechanism creates deliberate tension: optimal self-interest leads all players to the outcome that's worse for everyone than if they'd all cooperated, trapping rational actors in a suboptimal equilibrium.

## Relations
- conflicts-with:: [[mechanisms/solo-solitaire-game]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/decided-early]], [[anti-patterns/deadlock]], [[anti-patterns/runaway-leader]]
- requires:: [[mechanisms/simultaneous-action-selection]]

## Notes
- conflicts with solo-solitaire-game: A prisoner's dilemma requires independent simultaneous choices by at least two participants, which solitaire cannot supply.
Iterated repetition with visible history can break the dominant strategy equilibrium (Tit-for-Tat and similar strategies emerge); single-shot versions are prone to mutual defection regardless of player preferences.
Real players cooperate far more than the mechanism predicts, making it a poor model of human behavior without strong social enforcement or repeated interaction.
sources: https://www.sciencedirect.com/topics/physics-and-astronomy/prisoner-dilemma https://medium.com/blagenflorble/a-prisoners-dilemma-cheat-sheet-4d85fe289d87 https://arxiv.org/pdf/1506.05148 https://www.wiris.com/en/blog/jprisoners-dilemma-math-game-theory/
