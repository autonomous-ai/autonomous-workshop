---
type: mechanism
name: "Network and Route Building"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Network and Route Building

## Definition
Players extend a network by laying track/pipe/road pieces or drawing lines across a shared map to physically connect nodes such as cities or resources, with the connections themselves (not just the endpoints) counting as the built asset. Most implementations make individual edges or spaces exclusive to one player, so the map is a shrinking shared resource: routes score for length, connectivity, or completing specific origin-destination goals. The core tension is spatial - every claimed link forecloses that path for rivals and reveals part of your plan, so players must race for contested corridors while timing when to tip their hand.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/kingmaking]], [[anti-patterns/first-player-advantage]]

## Notes
Exclusive-edge claiming (only one player may occupy a given connection) is what generates both the blocking tension and the kingmaking risk when a non-contending player's block decides who wins.
Route claims are public and irreversible, so information leakage about a player's destination goals grows every turn, rewarding delayed commitment over early efficiency.
sources: https://www.meeplemountain.com/mechanisms/network-and-route-building/ https://www.thedarkimp.com/blog/2021/02/10/what-is-a-network-building-game/ http://www.gamelevellearn.com/game/2018/4/16/51-mechanics-route-building https://everythingisagame.com/ticket-to-ride-route-planning/
