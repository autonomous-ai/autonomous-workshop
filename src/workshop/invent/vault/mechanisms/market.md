---
type: mechanism
name: "Market"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Market

## Definition
The Market mechanism simulates economic equilibrium through dynamic pricing—a price track adjusts as players buy and sell resources, with prices rising when demand exceeds supply and falling when supply exceeds demand. This creates emergent pressure: players must balance production against consumption, timing transactions to exploit price movements while avoiding being trapped with overabundant inventory.

## Relations
- component:: [[components/socketed-component-tray]]
- component:: [[components/windowed-rotary-dial]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/rules-overhead]], [[anti-patterns/idle-player]]
- variant-of:: [[mechanisms/commodity-speculation]]
- requires:: [[mechanisms/trading]], [[mechanisms/income]]

## Notes
Mechanism only works if players are both suppliers and demanders; purely one-directional trading breaks equilibrium.
Market must create organic economic pressure tied to theme, not feel like a shallow pricing overlay.
sources: https://medium.com/theuglymonster/supply-demand-and-animal-spirits-making-a-market-in-a-board-game-c124d76d2df8 https://boardgamedesignlab.com/mechanics/ https://makecraftgame.com/2025/02/28/board-game-mechanics-an-overview/ https://sdlccorp.com/post/mastering-mechanics-key-elements-for-successful-board-game-development/
