---
type: mechanism
name: "Voting"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Voting

## Definition
Voting creates collective decision-making where players' expressed preferences determine outcomes, with each player contributing influence proportional to their resources or position. Tension arises from the voter's dilemma—choosing between voting for personal interest or strategically shaping who wins—compounded by swing-player dynamics where non-leaders gain kingmaking power. Secret voting obscures coalition logic and forces silent calculation; open voting makes incentives transparent but invites negotiation-based social advantage.

## Relations
- conflicts-with:: [[mechanisms/solo-solitaire-game]]
- risks:: [[anti-patterns/kingmaking]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/idle-player]]

## Notes
- conflicts with solo-solitaire-game: Voting requires multiple independent player preferences to be aggregated, which is impossible with one player.
Kingmaking severity depends on whether coalitions are structurally guided by game state (controlled) or require open negotiation (amplifies charisma/social capital unfairly).
Secret voting prevents coalition coordination but increases calculation burden; open voting enables table negotiation at the cost of transparency-based manipulation.
sources: https://www.bgdf.com/forum/archive/archive-game-creation/game-design/voting-game-mechanism https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-kingmaking-common-problem-2 https://www.diva-portal.org/smash/get/diva2:1876522/FULLTEXT01.pdf https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/
