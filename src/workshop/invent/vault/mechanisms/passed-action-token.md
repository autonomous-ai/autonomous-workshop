---
type: mechanism
name: "Passed Action Token"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Passed Action Token

## Definition
A player can forfeit their turn or action phase to receive a token that accumulates and can be spent in later turns for enhanced effects—typically stronger plays, flexible card options, or additional resources. The tension emerges from a timing trade-off: pass now to build flexibility later, or act immediately while competitors build their token advantage.

## Relations
- component:: [[components/snap-fit-state-token]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/decided-early]], [[anti-patterns/alpha-solve]]
- conflicts-with:: [[mechanisms/real-time]]
- variant-of:: [[mechanisms/advantage-token]]
- requires:: [[mechanisms/action-points]]

## Notes
Token accumulation can create asymmetric board states where early passers dominate mid-game.
Works best when the token's future value is uncertain enough that early passing remains a genuine choice rather than an obvious optimization path.
sources: https://oneboardfamily.com/pass-review/ https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/ https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-2/ https://boardgamedesignlab.com/mechanism-master-list/
