# Blindcap: Duel

2 players · 25 minutes

Twelve mushrooms share one species-neutral silhouette while hiding four tunnel patterns beneath a cracked field. You know the six you plant; your rival does not. Three probes buy public bits of truth that remain visible until harvest. Three crowns turn theories into points. Every question delays a claim.

## In the box

- 2 loam tiles, each a 3 × 3 socket grid
- 12 mushrooms: 4 deadheads, 4 brackets, 2 inkcaps, 2 hollows
- 6 crowns and 6 probes, 3 per player
- 2 screened trays
- 1 printed reader and harvest-record aid, plus a pencil

Each player gets 2 deadheads, 2 brackets, 1 inkcap and 1 hollow. One or two marks on each cap, crown, probe and tray show its owner, never its species.

## The buried code

Every socket has a one-dot and a two-dot channel. An open tunnel lets a probe rest **low**, 3 mm proud. Solid shank stops it **high**, about 28 mm proud (27.63 mm digital reference).

| Species | One dot | Two dots |
| --- | --- | --- |
| Deadhead | high | high |
| Bracket | low | high |
| Inkcap | high | low |
| Hollow | low | low |

One probe halves the possibilities. Both identify a mushroom.

## Setup

1. Join the tiles into a 6 × 3 field. Shared edges make neighbours; diagonals do not. Each player's seed socket is the middle-row socket on their tile immediately beside the centre join.
2. Take your marked tray, six mushrooms, three probes and three crowns. Keep shanks facing you behind the screen.
3. Choose the first-round starter at random.
4. Secretly choose one mushroom. On three, both players plant into their own seed socket at once.

Before the first game, feel both probe results on the fit coupon without a live mushroom.

## Five main rounds

The starter takes a turn, then the other player. Swap the starter each round.

On your turn:

1. **Plant:** conceal one shank and seat that mushroom in any empty socket.
2. **Act:** probe or crown. You cannot pass.

### Probe

Insert one of your remaining probes into an empty one-dot or two-dot channel beneath a rival mushroom. Leave it where it stops until harvest. Its height is public; its mark records who earned the information. You may test both channels of one mushroom or spread probes across several. Never probe your own mushroom or an occupied channel.

### Crown

Place one of your crowns on an uncrowned rival mushroom. It never moves. You may use at most two crowns during the five main rounds; reserve the third.

Your five main actions will therefore be exactly three probes and two crowns, in the order you choose.

## Closing and harvest

After round five, each player has planted all six mushrooms. Play one closing round in the same order: each player must place the reserved crown on an uncrowned rival mushroom. Do not plant or probe.

Before touching a probe, agree and write four counts for each player on the harvest-record aid: rival mushrooms personally tested in both channels; distinct rival mushrooms personally probed; your probes beneath mushrooms bearing your crown; and your probes resting low. Then withdraw all six probes completely and return them to their owners.

Lift each mushroom and set it cap-down in its original cell with the shank visible. Rest any crown flat on the now-upward shank, preserving its owner and position. A **grove** is a maximal orthogonally connected group of one species; a lone mushroom is a grove of one. Tile joins count. Uncrowned groves score nothing.

## Scoring

Each crowned grove pays once per crown owner, not once per crown.

- If one player owns every crown in a grove of size `n`, that player scores `n × n`.
- If both players have a crown there, each scores `n`.
- Inkcap and hollow groves score double.
- Extra crowns from the same player in one grove add nothing.

Highest score wins. Break a tie by:

1. larger single uncontested grove;
2. more rival mushrooms personally tested in both channels;
3. more distinct rival mushrooms personally probed;
4. the recorded count of your probes beneath mushrooms bearing your crown;
5. the recorded count of your probes that rested low.

If still tied, share the win.

## Print gate

Print the fit coupon first. Low and high must be obvious without looking beneath a cap; one channel must never leak into the other; after probes are removed, every keyed mushroom must lift and sit cap-down cleanly in its cell. Digital geometry checks do not replace this physical test.
