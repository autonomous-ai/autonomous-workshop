# CRANK

*A gear-routing race for 2–4 players. About 30 minutes. Ages 10+.*

---

## 1. Overview

There is one machine on the table and one handle on it. On your turn you bolt a
single gear onto the shared peg plate, then you turn the handle three clicks —
one full revolution — and every dial around the table moves at once.

Your dial only moves if a live run of teeth reaches it from the handle. How
**fast** it moves is set by the size of the gear sitting under it. Which **way**
it moves is set by one thing only: how many meshes are between the handle and
that gear. An even number of meshes and your dial climbs. An odd number and it
falls. That is not a card that says "reverse" — it is what a line of gears
actually does.

You never add anything up. You crank, and the machine tells you what you built.
**First dial to reach 20 wins on the spot.**

The catch, and the whole game: **the plate is shared, and anybody may place the
gear under your dial.** One gear spliced onto your run in the right place turns
your engine into a drain.

---

## 2. Components bill

Every part is printed. All gears use a 3 mm module, and every hole on the plate
is 3 mm from the next, which is why every mesh distance in this game is a whole
number of holes.

The **Compound Hub** is the load-bearing part. It is a print-in-place planetary
stack with a captive carrier, sealed inside a bridge body. Both of its ends look
identical from outside; what is inside changes both the speed and the direction
of everything past it, and you find out by cranking. It is the reason this game
cannot be a deck of cards.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plate_01` | Peg Plate | 1 | 184 × 184 × 10 | Playing field 174 × 174, ribbed underside, 5 mm rim. 59 × 59 grid of ⌀1.8 holes at 3 mm pitch. Columns 1–59 left to right, rows 1–59 near to far. |
| `crank_01` | Crank Post | 1 | ⌀30 × 84 | Seats in the one oversized ⌀5 hole, at **column 22, row 34** — off-centre on purpose. One-way ratchet, three detents per revolution. |
| `crank_02` | Crank Handle | 1 | 62 × 16 × 20 | Presses onto the Crank Post shaft. This is the handle. |
| `drive_01` | Drive Gear | 1 | ⌀45 × 8 | 13 teeth, fixed to the crank shaft at gear height. Pushes 13 teeth into the machine per revolution of the handle. Never removed, never pulled. |
| `gear_11` | Gear 11 | 8 | ⌀39 × 10 | 11 teeth. Spoked. |
| `gear_13` | Gear 13 | 8 | ⌀45 × 10 | 13 teeth. Spoked. |
| `gear_17` | Gear 17 | 7 | ⌀57 × 10 | 17 teeth. Spoked. |
| `gear_19` | Gear 19 | 7 | ⌀63 × 10 | 19 teeth. Spoked. |
| `gear_23` | Gear 23 | 5 | ⌀75 × 10 | 23 teeth. Spoked. |
| `gear_29` | Gear 29 | 5 | ⌀93 × 10 | 29 teeth. Spoked. |
| `hub_01`–`hub_06` | **Compound Hub** ★ | 6 | 87 × 39 × 14 | Two 11-tooth ends, centres **16 holes** apart, joined by a sealed planetary train. Each end carries one red index tooth. Inside is one of six pairings of speed and direction (§5b) — unmarked, unguessable, identical from outside. |
| `mag_01` | Hub Magazine | 1 | 96 × 50 × 104 | Opaque stack. Holds all six hubs; dispenses only the bottom one. |
| `dial_01`–`dial_04` | Dial Unit | 4 (one per player) | 90 × 52 × 58 | Clamps anywhere on the plate rim and slides along it. Arm reaches over any hole **1 to 12 holes in from that rim**. A follower rides the read gear's top track and steps the counter one number per revolution of that gear, either way. Counter reads −5 to 25. |
| `ring_01`–`ring_06` | Reading Ring | 6 | ⌀52 × 4 | Marked ×2 same, ×3 same, ÷3 same, ×2 flip, ×3 flip, ÷2 flip. Dropped over a hub end once the table has read that hub. Bookkeeping only. |
| `pull_01` | Pull Token | 12 (three per player) | ⌀18 × 4 | Spent to take a part off the plate. |
| `tray_01` | Gear Tray | 1 | 186 × 74 × 22 | Six open wells, one per tooth count, each well marked. This is the supply and it is public all game. |
| `tray_02` | Scrap Tray | 1 | 92 × 74 × 22 | Where pulled parts go. Nothing ever comes back out. |

**Three facts about the printed gears that the rules lean on:**

- Every gear has a ⌀1.7 × 5 mm spigot underneath. It drops straight into a plate
  hole and spins there. There are no separate pins and no assembly.
- Every gear has a ⌀20 mm follower track on its top face with one notch in it.
  The track is the same size on all six gears, so any Dial Unit can read any gear.
- Every gear has one **red index tooth**. That is how you see which way a gear is
  turning without staring at it.

---

## 3. Setup

1. Put the **Peg Plate** flat in the middle of the table.
2. Push the **Crank Post** into the one oversized hole — it is the only hole it
   fits, and it is not in the middle. Press the **Crank Handle** onto its shaft.
   The **Drive Gear** is already on the post. This is the only gear that starts
   on the plate.
3. Tip all 40 gears into the marked wells of the **Gear Tray**. Put the empty
   **Scrap Tray** beside it. Both stay in reach of everyone all game.
4. Without turning them over and **without spinning either end**, stack all six
   **Compound Hubs** into the **Hub Magazine** in any order. Stand the Magazine
   beside the plate and lay the six **Reading Rings** face up next to it.
5. **First player:** whoever most recently turned a real crank, spanner or hand
   drill. If nobody has, the youngest player. Play passes to the left.
6. **Docking, in reverse turn order** — the last player in turn order clamps
   their Dial Unit first, the first player clamps last. Clamp anywhere on any of
   the four rims and set the arm over any hole 1 to 12 holes in from that rim.
   No two Dial Units may read the same hole.
   - **2 players:** the two Dial Units must clamp on different sides of the plate.
   - **3 and 4 players:** no restriction beyond the above. Sides are not owned;
     two players may share a side.
7. Set every counter to **0**. Each player takes **3 Pull Tokens**.

---

## 4. Turn structure

A turn is two steps, in this order. Both always happen. There are no phases
inside a turn, no reactions, and nothing happens between turns.

**Step 1 — Act.** Do exactly one of the four actions in §5. If none of them is
legal for you, do nothing and say so.

**Step 2 — Crank.** You, and only you, take the handle and turn it **clockwise
exactly three clicks** — one full revolution. It ratchets; it will not go back.
Three clicks every turn: not two because you are behind, not six because you are
ahead.

Then everybody looks at their own dial. Dials move during the crank, driven by
the machine. Nobody adds anything up and nobody moves anybody's counter by hand.

- Any dial that reaches **20** — that player wins immediately. Stop the game.
- Any dial that reaches **−5** stops there and freezes (§6).

Then the turn passes to the left.

---

## 5. Actions

Pick exactly one.

### 5a. Place a gear

Take any one gear from the Gear Tray and drop it onto an empty hole. **It must
mesh at least one part already on the plate** — the Drive Gear counts, a hub end
counts. It may mesh several.

**When do two gears mesh?** One rule, no table:

> **Two gears mesh when the holes they sit in are exactly (my teeth + their
> teeth) ÷ 2 holes apart.** Every tooth count in this box is odd, so that sum is
> always even and the answer is always a whole number of holes.

Drive Gear = 13 teeth. Hub ends = 11 teeth. So a Gear 17 meshes the Drive Gear
at (17 + 13) ÷ 2 = **15 holes**, and meshes a hub end at (17 + 11) ÷ 2 = **14
holes**.

Measure straight along a row or straight along a column. **Six mesh numbers also
work on a slant**, because the plate grid happens to allow it — these are real
meshes, whether you meant them or not:

| mesh number | also meshes at |
|---|---|
| 13 | 5 across and 12 along |
| 15 | 9 across and 12 along |
| 17 | 8 across and 15 along |
| 20 | 12 across and 16 along |
| 26 | 10 across and 24 along |
| 29 | 20 across and 21 along |

Any other slant is either farther apart than the mesh number, in which case the
teeth never touch, or nearer, in which case:

> **No two gears may ever sit closer than their mesh number.** The teeth foul and
> the gear will not seat. The plate is the referee — if it does not drop in and
> spin freely, it is not a legal placement.

**Which way it turns.** The Drive Gear turns clockwise, seen from above. Every
mesh reverses. So:

> **Count the meshes from the Drive Gear to the gear under your dial. Even, and
> that gear turns clockwise, and your dial climbs. Odd, and it turns
> anticlockwise, and your dial falls.**

The shortest possible run — one gear straight off the Drive Gear — is one mesh.
It runs you **backwards**. Climbing takes at least two.

**Failed placement.** If the gear will not seat, fouls a neighbour, fouls a Dial
Unit arm, or the handle will not turn afterwards (§9, *Jams*), the placement is
illegal. Take the gear straight back and put it somewhere else, or switch to a
different action. No penalty, no turn lost. But once you have started cranking,
everything on the plate stands.

### 5b. Draw and place a hub

Instead of a gear, take the **bottom hub from the Hub Magazine** — you do not get
to choose which — and place it on the plate in one motion, both spigots into
holes exactly **16 holes apart** along a row or a column.

**Exactly one of a hub's two ends may mesh something already on the plate.** The
other end must, at the moment you place it, mesh nothing at all. (This is why a
hub can never lock the machine on the turn it goes down.)

Hub ends have 11 teeth, so a hub end meshes a Gear 11 at 11 holes, a Gear 13 or
the Drive Gear at 12, a Gear 17 at 14, a Gear 19 at 15, a Gear 23 at 17, a Gear
29 at 20.

Seating a hub on the plate releases its internal lock. **Do not spin a hub in
your hand, and do not spin one in the Magazine.** You find out what is inside it
by cranking, and that is the game.

Inside every hub is one of these six, and each of the six is in the box exactly
once:

| what it does to speed | what it does to direction |
|---|---|
| ×2 | keeps it — **same** |
| ×3 | keeps it — **same** |
| ÷3 | keeps it — **same** |
| ×2 | reverses it — **flip** |
| ×3 | reverses it — **flip** |
| ÷2 | reverses it — **flip** |

**How you read a hub.** Crank, and watch the red index tooth on each of the hub's
two ends. Which way the far end goes against the near end tells you same or flip.
How much farther the far end travels than the near end tells you the speed. One
crank answers both. When the table agrees, drop the matching **Reading Ring**
over the far end so nobody has to remember.

**A flip hub counts as one extra mesh** for everything past it. A same hub counts
as none. That is the only thing you ever have to fold into the count in §5a.

**One hub per run.** No dial may be driven through more than one hub. If placing
a hub here would put two hubs between the handle and any player's dial gear, you
may not place it there.

### 5c. Pull

Spend one **Pull Token** — put it in the Scrap Tray — and take **any one gear or
any one hub** off the plate. It goes to the Scrap Tray and is out of the game for
good. Pulled gears never return to the supply and pulled hubs never return to the
Magazine.

You may pull a gear that a Dial Unit is reading, including your own. You may not
pull the Drive Gear.

Parts left with no live path back to the handle simply stop turning. Leave them
where they are; they still occupy their holes and they still block. A dead branch
can be reconnected later, at whatever mesh count the reconnecting player chooses.
That is the sharpest weapon in the box: pull one gear out of the middle of a run,
then next turn re-connect the orphaned tail with the parity you want it to have.

### 5d. Re-dock

Slide your Dial Unit anywhere along any rim and set its arm over any hole 1 to 12
holes in from that rim. The hole may be empty or may already have a gear on it.
Your counter keeps its number. You may not dock over a hole another Dial Unit is
already reading.

### If you can do nothing

If the Gear Tray is empty, the Magazine is empty, you have no Pull Tokens and
every re-dock is blocked, take no action. You still crank.

---

## 6. How dials move

You do not need this section to play — the machine does it — but you need it to
plan.

One revolution of the handle pushes **13 teeth** into the machine. Teeth do not
multiply or vanish as they run along plain gears: 13 in, 13 out, all the way
down the line. A small gear spins fast, a big gear spins slowly, and the same
teeth pass through both.

Your Dial Unit steps its counter **one number for every full revolution of the
gear it is reading**, in whichever direction that gear is turning.

| gear under your dial | numbers per crank, on a plain run |
|---|---|
| 11 | 1.18 |
| 13 | 1.00 |
| 17 | 0.76 |
| 19 | 0.68 |
| 23 | 0.57 |
| 29 | 0.45 |

You never work those fractions out. The follower carries the remainder with it,
so some cranks your dial clicks twice and some cranks it does not click at all.
Watch it; it will tell you.

**Direction** comes from the mesh count, always, and never from the gear itself.
The same Gear 13 that climbed for you all game runs you down the moment somebody
adds a mesh ahead of it.

**A hub multiplies the speed and may flip the direction** of everything past it.

### Worked example

Amara docks on the left rim, arm over column 9, row 34 — 13 holes dead left of
the Crank Post at column 22, row 34.

**Turn 1.** She drops a Gear 13 on that hole. (13 + 13) ÷ 2 = 13, so it meshes
the Drive Gear. One mesh — odd. Her dial runs **down** at 1.00 a crank. She knew
that; she wanted the hole.

**Turn 2.** She has slipped to −2. She places a Gear 11 twelve holes above the
Crank Post at column 22, row 46, then re-docks? No — she cannot do both in one
turn. She places the Gear 11 and lets the dial keep falling. −3.

**Turn 3.** She pulls her own Gear 13 out of column 9, row 34, for one token. Her
dial now reads nothing and holds at −3.

**Turn 4.** She drops a Gear 23 at column 9, row 34. Is it meshed? To the Drive
Gear the distance is 13, but a 23 needs 18 — no mesh. To the Gear 11 at column
22, row 46: 13 across and 12 along, which is not one of the six slants — no mesh.
Illegal. She takes it back and drops a Gear 11 there instead: (11 + 11) ÷ 2 = 11
from the Gear 11 at row 46? That is 13 across and 12 along again. Still no.

She re-reads the plate and does it properly: she puts a **Gear 11 at column 10,
row 46**, which is 12 holes straight along from the Gear 11 at column 22, row 46
— wrong, (11 + 11) ÷ 2 = 11, so she puts it at **column 11, row 46**. Now the run
is Drive Gear → Gear 11 (12 holes up) → Gear 11 (11 holes across). Two meshes.
Even. Clockwise. Climbing.

**Turn 5.** She re-docks her arm over column 11, row 46 — twelve holes in from
the far rim, legal. From −3 she now climbs 1.18 a crank, on **everybody's**
crank, not just her own. Twenty numbers of climb from −3 means 23 numbers, about
20 turns of the handle.

**Turn 9, and it is not her turn.** Ben places a Gear 19 at column 11, row 27 —
(19 + 11) ÷ 2 = 15 holes straight down from Amara's read gear. That does not
touch her. But then he places a Gear 17 fifteen holes from the Drive Gear on the
slant, 8 across and 15 along, landing at column 30, row 49 — and it also sits 19
holes from her first Gear 11. Not a mesh number for 17 and 11 (that would be 14),
so no. Ben cannot reach her that way.

What Ben does instead: he spends a token and **pulls Amara's first Gear 11** out
of column 22, row 46. Her tail goes dead at 8. Next turn he places a **Gear 13**
at column 22, row 46 — 12 holes from the Drive Gear, a legal mesh — and Amara's
read gear is now three meshes from the handle. Odd. She has spent two turns
building and now she runs **down** at 1.18 a crank, from 8, and −5 is five cranks
away. It cost Ben one token and two turns. It costs Amara her whole route.

That is the game.

**The −5 freeze.** A dial that reaches −5 stops there. It does not go lower and
it does not move again — not on anybody's crank — until the end of its owner's
next turn, at which point it comes back to life still reading −5. You get one
turn of grace, frozen, to fix your route or re-dock somewhere kinder.

---

## 7. End & winning

The game ends the moment any one of these happens.

1. **A dial reaches 20 during a crank.** That player wins immediately. Finish the
   revolution, then stop; nothing else resolves. A dial cannot pass 20 for the
   purpose of winning, but the counter reads to 25 so ties can be broken.
2. **A round with no building.** If a complete round goes by — every player takes
   one turn — in which no gear and no hub is placed and no Pull Token is spent,
   the game ends after the last crank of that round. Highest dial wins.

**The end is reachable, and here is the arithmetic.** Every Place takes one part
out of a finite supply for good; every Pull takes one token out of a hand for
good. There are 40 gears, 6 hubs and 12 tokens: 58 turns, at the absolute
outside, before nobody can build or pull at all, and then ending 2 must fire
inside one more round. Hard ceiling: **62 turns of the handle**, even if not one
dial ever moves.

In real play ending 1 arrives long before that. A player wired to a plain Gear 11
on an even mesh count gains 1.18 a crank, and **every player's crank feeds every
dial**, so 20 arrives about 17 cranks after they connect. Connecting takes two or
three turns. Interference — a pull, a re-dock, a spliced mesh — typically costs
each player four to eight cranks of progress. Expect **30 to 40 turns of the
handle**, which is **25 to 40 minutes** with teaching, at any player count.

Note that the length is measured in cranks, not rounds. Two players and four
players play the same number of cranks to the same finish; at two players each
person simply gets more of them.

---

## 8. Tiebreak

If ending 2 fires, or if one crank pushes two dials to 20 in the same revolution,
work down this list until one player is left. It always resolves.

1. **Highest number on the counter.** This is why it reads past 20.
2. **Most unspent Pull Tokens.**
3. **Shortest run.** Count the parts between the Drive Gear and the gear your
   dial reads, not counting the Drive Gear, counting a hub as one part. Fewest
   wins. A dial with no live run to the handle counts as longer than any run and
   loses this step to everybody.
4. **Turn order.** Of the players still tied, the one who would take their turn
   soonest, starting from the player to the left of whoever cranked last.

---

## 9. Edge cases

**Jams.** Gears are rigid, so some placements ask the machine to do two things at
once and it simply locks. Two rulings cover every case:

- **A closed ring of parts jams if the mesh count round the ring is odd.**
  (Remember a flip hub counts as one mesh and a same hub as none.)
- **A closed ring containing any hub jams**, always, because the two ways round
  the ring want different speeds.

A placement that jams the machine is illegal. You find out by trying to crank,
which is fine — a jam before the first click costs nothing. Take the part back
off and place it elsewhere or switch actions. **You cannot jam the machine on
purpose, because a jam is never a legal placement.**

**Closing a ring through a hub nobody has read yet.** You may try it. If it locks,
the placement is void and you take it back — but the table has now learned
something about that hub for free, and everyone saw it.

**You cannot legally place any gear anywhere.** You may still Pull or Re-dock. If
none of those is available either, take no action and crank.

**The well you want is empty.** Too bad. Take a different tooth count or a
different action. Nothing comes back from the Scrap Tray.

**Somebody spliced a mesh into my run and now I fall.** That is legal and it is
the point. Your fixes are: re-dock somewhere with an even count, pull the added
gear out, or add another mesh past it and flip yourself back.

**Somebody docked over the hole I wanted.** First come, first served. Corner
holes count as belonging to both rims that meet there, same rule.

**Placing a gear on a hole that already has a Dial Unit arm over it.** Legal.
Anybody may do it, and it becomes that player's read gear from the next crank.

**A dial with no gear under it.** It holds at whatever it reads and does not move.
That is not a loss — it scores as it stands and it loses tiebreak step 3.

**A dial that hits 20 and −5 in the same crank.** Impossible; a counter cannot
reach both in one revolution. If two different dials hit 20 and −5 in the same
crank, the 20 wins the game and the −5 is irrelevant.

**Two dials reach 20 in the same crank.** Go to §8.

**Two dials freeze at −5 in the same crank.** Both freeze; each thaws at the end
of its own owner's next turn.

**A frozen dial whose read gear is pulled while it is frozen.** It still thaws on
schedule. It then reads nothing and holds at −5 until its owner re-docks.

**A hub whose far end drives nothing.** Legal, and useless until something
downstream of it exists. It reveals nothing, because with nothing on its far end
there is no load and both index teeth still move — read it the same way, by
comparing the two ends.

**Two hubs in one run.** You may never *place* a hub that creates this (§5b). But
if a **Pull** somewhere else re-routes a dial through two hubs, that Pull is still
legal, the two speeds multiply, the two directions combine, and the table lives
with it.

**We cannot agree what is inside a hub.** Then do not put a Reading Ring on it.
The rings are bookkeeping and change nothing. The machine keeps doing what it
does whether or not you have worked it out.

**Somebody spun a hub in their hand.** Ask them not to. It tells them nothing
useful — a hub out of the Magazine has both ends locked — but it is the one
place in this box where a player can look like they are cheating, so keep hubs
going Magazine-to-plate in one motion.

**Miscranking.** Finish the revolution to the next click and carry on. The
machine has already moved and there is no rewind. If somebody cranks on another
player's turn, the same applies: the crank counts, and the turn's owner does not
get a replacement crank.

**Reaching 20 exactly versus overshooting.** The counter physically stops at 25,
but the game stops the instant a counter shows 20 or more during a crank. If your
dial jumps from 19 to 21 in one revolution, you have won at 21, and 21 is the
number used for tiebreaks.
