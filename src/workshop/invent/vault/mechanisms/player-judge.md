---
type: mechanism
name: "Player Judge"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Player Judge

## Definition
One player designated as judge evaluates submissions from other players—typically cards or answers—and selects which best fits a given criterion, with the judge's subjective choice determining the round's outcome and scoring. The tension emerges from players predicting the judge's taste while remaining unaware of competing submissions, and from the judge's outsized power to decide winners based on personal preference rather than rules.

## Relations
- conflicts-with:: [[mechanisms/solo-solitaire-game]]
- risks:: [[anti-patterns/kingmaking]], [[anti-patterns/seat-advantage]], [[anti-patterns/idle-player]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/voting]]
- requires:: [[mechanisms/hidden-roles]]

## Notes
- conflicts with solo-solitaire-game: Player-judge requires one player to evaluate another player's contribution, which cannot occur with a single participant.
Anonymous submission mitigates but does not eliminate judge bias toward specific players.
Subjective disagreement about judge decisions is often a feature (social humor/tension) rather than a flaw in party-game contexts.
sources: https://boardgamegeek.com/boardgamemechanic/2865/player-judge https://www.meeplemountain.com/mechanisms/player-judge/ http://www.phantomknightgames.com/news/making-an-impressive-impress-the-judge-game/
