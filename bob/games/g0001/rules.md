# CRANK

*A gear-routing race for 2–4 players. 25–35 minutes. Ages 10+.*

---

## 1. Overview

There is one machine on the table and one handle on it. On your turn you bolt a single gear onto the shared peg plate, then you turn the handle one full revolution — three clicks — and every dial around the table moves at once.

Your dial only moves if a live run of teeth reaches it from the crank. How *fast* it moves depends on the gear sitting under your dial, and on whether anybody has routed you through a compound hub, which is a sealed gearbox whose ratio nobody knows until it turns. Which *way* it moves is decided by the colour of the gear under your dial: black climbs, white falls.

You never add anything up. You crank, and the machine tells you what you built. First dial to reach **30** wins on the spot.

The catch, and the whole game: **anybody may place the gear under your dial.**

---

## 2. Components bill

Every part is printed. The **Compound Hub** is the load-bearing part — a print-in-place planetary stack with a captive carrier, sealed in a bridge body. It is the reason this game cannot be a deck of cards.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plate_01` | Peg Plate | 1 | 168 × 168 × 11 (field 160 × 160 × 5, rim 3 wide × 6 tall) | 39 × 39 grid of ⌀2.2 holes at 4 mm pitch. Every gear stands on this. |
| `crank_01` | Crank Post | 1 | ⌀34 × 96 | Stands in the exact centre hole (column 20, row 20). One-way ratchet, three detents per revolution. |
| `crank_02` | Crank Handle | 1 | 66 × 18 × 22 | Presses onto the Crank Post shaft. This is the handle. |
| `drive_01` | Drive Gear (13 teeth, black) | 1 | ⌀30 × 8 | Fixed to the crank shaft at gear height. Delivers 13 teeth per turn of the handle. Never removed. |
| `gear_11` | Gear 11 (white) | 8 | ⌀26 × 14 | Plain gear, 11 teeth. |
| `gear_13` | Gear 13 (black) | 8 | ⌀30 × 14 | Plain gear, 13 teeth. |
| `gear_17` | Gear 17 (black) | 7 | ⌀38 × 14 | Plain gear, 17 teeth. |
| `gear_19` | Gear 19 (white) | 7 | ⌀42 × 14 | Plain gear, 19 teeth. |
| `gear_23` | Gear 23 (white) | 5 | ⌀50 × 14 | Plain gear, 23 teeth. |
| `gear_29` | Gear 29 (black) | 5 | ⌀62 × 14 | Plain gear, 29 teeth. |
| `hub_01`–`hub_06` | **Compound Hub** ★ | 6 | 80 × 42 × 16 | Two 17-tooth black ends, 40 mm apart, joined by a sealed planetary train. Outsides identical; the ratio inside is one of ×2, ×2, ×3, ×4, ÷2, ÷3 and is not marked. Locked until it is seated on the plate. |
| `tower_01` | Hub Tower | 1 | 52 × 52 × 132 | Opaque magazine. Holds the six hubs stacked; dispenses only the bottom one. |
| `dial_01`–`dial_04` | Dial Unit | 4 (one per player) | 96 × 46 × 62 | Clamps to the plate rim and slides along it. Arm reaches in over one gear; a follower rides that gear's track and steps the counter one number per revolution, either way. Counter reads −5 to 35. |
| `ring_01`–`ring_06` | Reading Ring | 6 | ⌀46 × 5 | Marked ×2, ×2, ×3, ×4, ÷2, ÷3. Dropped over a hub end once the table has worked that hub out. |
| `pull_01` | Pull Token | 16 (four per player) | ⌀18 × 4 | Spent to take a gear off the plate. |
| `tray_01` | Gear Tray | 1 | 186 × 74 × 24 | Six open wells, one per tooth count. This is the supply and it is public. |
| `tray_02` | Scrap Tray | 1 | 92 × 74 × 24 | Where pulled gears and pulled hubs go. Nothing ever comes back out. |

**Two facts about the printed gears that the rules lean on:**

- Every plain gear has a ⌀2.0 × 6 mm spigot underneath — it drops straight into a plate hole and spins there. No separate pins.
- Every plain gear has a ⌀20 mm follower track on its top face with one notch in it. The Dial Unit reads that notch. The track is the same size on all six gears, so a Dial Unit can read any gear.

---

## 3. Setup

1. Put the **Peg Plate** flat in the middle of the table, one edge facing each player.
2. Push the **Crank Post** into the centre hole and press the **Crank Handle** onto its shaft. The **Drive Gear** is already on the post. This is the only gear that starts on the plate.
3. Each player takes one **Dial Unit** and clamps it to the rim on the edge facing them, anywhere along that edge. Set every counter to **0**.
   - **2 players:** use opposite edges.
   - **3 players:** use the north, east and west edges. Nobody docks on the south edge; gears may still be placed there.
   - **4 players:** one edge each.
4. Each player takes **4 Pull Tokens**.
5. Shuffle the six **Compound Hubs** face down without looking at their undersides and drop them into the **Hub Tower** in that order. Stand the Tower beside the plate. Put the six **Reading Rings** face up next to it.
6. Tip all 40 plain gears into the **Gear Tray**, one tooth count per well. Everyone can see the supply all game. Put the empty **Scrap Tray** beside it.
7. The youngest player goes first. Play passes to the left.

---

## 4. Turn structure

A turn is two steps, in this order. Both always happen.

**Step 1 — Act.** Do exactly one of the five actions in section 5. If you can do none of them, say so and do nothing.

**Step 2 — Crank.** You, the player whose turn it is, take the handle and turn it **clockwise exactly three clicks** — one full revolution. It only turns one way; it will not go back. Do not stop halfway; three clicks or nothing.

Then everyone looks at their dial. Dials move during the crank, on their own. Nobody adds anything up.

- Any dial that reaches **30** — that player wins immediately. Stop.
- Any dial that reaches **−5** locks (section 6).

Then the turn passes to the left.

There are no phases inside a turn and no reactions. Between turns, nothing happens.

---

## 5. Actions

Pick exactly one.

### 5a. Place a gear

Take any one plain gear from the Gear Tray and drop it onto an empty hole.

**It must mesh at least one gear already on the plate** (the Drive Gear counts). It may mesh several.

**When do two gears mesh?** Look up the pair on the Mesh Table. That number is how many holes apart they must sit, counted straight along a row or column.

| | 11 (white) | 19 (white) | 23 (white) |
|---|---|---|---|
| **13 (black)** | 6 | 8 | 9 |
| **17 (black)** | 7 | 9 | **10** ◹ |
| **29 (black)** | **10** ◹ | 12 | **13** ◹ |

Three rules follow from that table and they are worth saying out loud once:

- **A black gear only ever meshes a white gear.** Two gears of the same colour can never sit at a meshing distance on this plate. You do not have to check.
- **Exactly that far apart = they mesh. Farther apart = they do not. Closer together = illegal**, because the teeth foul and the gear will not turn. The plate is the referee: if it does not drop in and spin freely, it is not a legal placement.
- **Three pairs also mesh on a diagonal** — the ones marked ◹. A 10 goes six holes across and eight holes along; a 13 goes five across and twelve along. No other pair meshes diagonally.

**Which way things turn.** The Drive Gear is black and turns clockwise seen from above. Every gear meshed to it turns the other way, and so on down the line. Because a mesh always joins a black to a white:

> **Every black gear on the plate turns clockwise. Every white gear turns anticlockwise. Always.**

**Failed placement.** If the gear will not seat, fouls a neighbour, fouls a Dial Unit, or the crank will not turn afterwards (see *Jams*, section 9), the placement is illegal. Take the gear straight back and place it somewhere else, or choose a different action. There is no penalty and it is not your turn wasted — but once you have started cranking, everything on the plate stands.

### 5b. Draw and place a hub

Instead of a plain gear, take the **bottom hub from the Hub Tower** — you do not get to choose which — and place it on the plate in one motion. It spans two holes exactly **10 holes apart**, in a row or a column, and at least one of its two 17-tooth ends must mesh a gear already on the plate. Its ends are black, so they mesh white gears only, at 7 (to an 11), 9 (to a 19) or 10 (to a 23).

Seating the hub on the plate releases its internal lock. **Do not spin a hub in your hand.** You find out what is inside it by cranking, and that is the game.

Both ends of a hub turn the same way as each other, so a hub never changes any direction anywhere. What it changes is how many teeth come out the far end: two, three or four times as many, or a half or a third as many. That multiplies the speed of every dial downstream of it.

**One hub per run.** No dial may be driven through more than one hub. If placing a hub here would put two hubs between the crank and any player's dial, you may not place it there.

### 5c. Pull

Spend one **Pull Token** (put it in the Scrap Tray) and take **any one plain gear or any one hub** off the plate. It goes to the Scrap Tray and is out of the game for good — pulled gears do not return to the supply and pulled hubs do not return to the Tower.

You may pull a gear that somebody's dial is reading, including your own. You may not pull the Drive Gear.

Gears left hanging off the plate with no live path back to the crank simply stop turning. Leave them where they are.

### 5d. Re-dock

Slide your Dial Unit to any other position on your edge, and set its arm to read any hole **within five holes of your edge**. The hole may be empty or may already have a gear on it. Your counter keeps its number.

You may not dock over a hole another Dial Unit is already reading.

### 5e. Reset

Only if your dial is locked at −5. Lift the Dial Unit's arm out, set the counter to **0**, and drop the arm back. Your dial is live again from the next crank.

### If you can do nothing

If the supply is empty, you have no Pull Tokens, you have nowhere legal to re-dock and your dial is not locked, you take no action. You still crank.

---

## 6. How dials move

You do not need this section to play — the machine does it — but you need it to plan.

One full turn of the handle pushes **13 teeth** into the machine, because the Drive Gear has 13 teeth. Teeth do not multiply or vanish as they run along plain gears: 13 teeth in, 13 teeth out, all the way down the line. A big gear turns slowly and a small gear turns quickly, but the same teeth pass.

Your Dial Unit steps its counter **one number for each full revolution of the gear it is reading**, and it steps whichever way that gear is turning. So:

| gear under your dial | colour | numbers per turn of the handle |
|---|---|---|
| 11 | white | 1.18 **down** |
| 13 | black | 1.00 **up** |
| 17 | black | 0.76 **up** |
| 19 | white | 0.68 **down** |
| 23 | white | 0.57 **down** |
| 29 | black | 0.45 **up** |

Those are not fractions you ever work out. The follower carries the leftover round with it, so some turns your dial clicks twice and some turns it does not click at all. Watch it; it will tell you.

A hub in your run multiplies all of it. A ×3 hub feeding a 13-tooth black gear gives you 3 numbers per turn. A ÷3 hub feeding a 29-tooth black gear gives you one number roughly every seven turns.

**Worked example.** Amara's run, from the middle outwards: Drive Gear (13, black) → Gear 23 (white, 9 holes away) → hub, in at its 17-tooth end (10 holes away) → out at the other end → Gear 11 (white, 7 holes away) → Gear 13 (black, 6 holes away), and that last black 13 is what her Dial Unit reads.

The hub turns out to be a ×2. So 13 teeth go in, 26 come out of the hub, and a 13-tooth gear turns twice. Her dial gains **2 a turn, upwards**, because the gear under it is black. Thirty turns of the handle after that — everybody's turns, not just hers — she wins. Unless somebody pulls the 23 out of the middle of her run, which costs them one Pull Token and one turn.

**A dial at −5 locks.** It stops there, stops counting, and stays stopped until its owner spends a turn on **Reset**. A locked dial cannot win.

---

## 7. End & winning

The game ends the moment any one of these happens.

1. **A dial reaches 30 during a crank.** That player wins immediately. The crank finishes, nothing else happens, the game is over. A dial cannot pass 30; it stops there.
2. **The supply runs dry.** If the last plain gear leaves the Gear Tray and the Hub Tower is empty, finish that turn's crank and the game ends. Highest dial wins.
3. **Nobody builds for a full round.** If a complete round goes by — every player takes one turn — in which no gear or hub is placed and no Pull is spent, the game ends after the last crank of that round. Highest dial wins.

**The end is reachable, and here is the arithmetic.** Every turn removes one item from a finite pile: a Place takes one gear or hub out of the supply for good, a Pull takes one token out of your hand and one part off the plate for good. There are 40 gears, 6 hubs and 16 tokens — at most 62 turns before ending 3 must fire even if nobody ever scores. In real play ending 1 arrives first: a player wired to a plain black 13 gains 1 a turn, and every player's crank feeds every dial, so 30 arrives roughly 30 turns after they connect, and connecting takes two placements. Expect **25 to 40 turns, 25 to 35 minutes**, at any player count — the game length is set by turns of the handle, not by how many people are sitting down.

---

## 8. Tiebreak

If endings 2 or 3 fire, or if one crank pushes two dials to 30 at once, work down this list until one player is left. It always resolves.

1. **Highest number on the dial.** The counter reads past 30 for exactly this reason.
2. **Most unspent Pull Tokens.**
3. **Shortest run.** Count the gears and hubs between the Drive Gear and the gear your dial reads, not counting the Drive Gear and counting a hub as one. Fewest wins. A dial with no live run to the crank counts as the longest and loses this step to everybody.
4. **Turn order.** Of the players still tied, the one who would take their turn soonest, starting from the player to the left of whoever cranked last.

---

## 9. Edge cases

**Jams.** Gears are rigid. If your placement closes a loop that asks two runs of teeth to disagree — an odd loop of plain gears, or a loop with a hub in it so the two ways round want different speeds — the machine locks and the handle will not move. That placement was illegal: take the gear back off and place it somewhere else, or take a different action. You find this out by trying to crank, which is fine; a jam before the first click costs nothing. **You may not jam the machine on purpose, because a jam is never a legal placement.**

**A gear you cannot legally place.** If you can find nowhere on the plate for any gear in the supply, you may still Pull, Re-dock or Reset. If you can do none of those, take no action and crank.

**The well you want is empty.** Too bad. Take a different tooth count or take a different action. Gears never come back from the Scrap Tray.

**Somebody put a white gear under my dial.** That is legal and it is the point. Your dial now runs down. Fix it by re-docking somewhere else, by placing a black gear on a hole you can then dock over, or by pulling the white one out.

**Somebody docked over the gear I wanted.** First come, first served. Corner holes belong to both neighbouring edges, same rule.

**Two dials reading the same gear.** Not allowed — one Dial Unit per hole.

**Placing a gear on a hole that is already under a Dial Unit's arm.** Legal. Anybody may do it, and it becomes that player's dial gear at the next crank.

**A dial with no gear under it.** It sits at whatever it reads and does not move. That is not a loss; at the end it is scored as it stands, and it loses tiebreak step 3.

**Two things happen on one crank.** Check for 30 first and stop the game. Only if nobody hit 30 do you apply locks at −5.

**A dial at −5 that nobody resets.** It stays dead. It can still lose ties on step 3 and it can never win. Resetting is always available on your turn and costs only the action.

**A hub whose far end drives nothing.** Legal and useless. It reveals nothing until something downstream of it reaches a dial.

**Two hubs in a row.** Never legal (section 5b). If a *Pull* somewhere else on the plate would leave two hubs in one dial's run, that Pull is still legal — the restriction only ever blocks placing a hub. In that case the second hub counts and the two ratios multiply, and everybody has to live with it.

**We cannot agree what a hub is.** Then do not put a Reading Ring on it. The rings are bookkeeping; they change nothing. The machine keeps doing what it does whether or not you have worked it out.

**Spinning a hub in your hand to peek.** Don't. It is locked in the Tower and it is meant to go from the Tower to the plate in one motion.

**Cranking fewer or more than three clicks.** Three clicks, every turn, no exceptions — not two if you are behind, not six if you are ahead. If somebody miscranks, finish the revolution to the next click and carry on; the machine has already moved and there is no rewind.
