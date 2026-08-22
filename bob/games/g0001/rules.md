# CRANK

*A gear-routing race for 2–4 players. About 30 minutes. Ages 10+.*

---

## 1. Overview

There is one machine on the table and one handle on it. On your turn you bolt a
single gear onto the shared peg plate, then you turn the handle three clicks —
one full revolution — and every dial around the table moves at once.

Your dial only moves if a live run of teeth reaches it from the handle. How
**fast** it moves is set by the size of the gear sitting under it. Which **way**
it moves is set by one thing and one thing only: **how many meshes lie between
the handle and that gear.** Even, and your dial climbs. Odd, and it falls. That
is not a card that says "reverse" — it is what a line of gears actually does, and
you can see it in the red index teeth.

You never add anything up. You crank, and the machine tells you what you built.
**First dial to reach 20 wins on the spot.**

The catch, and the whole game: **the plate is shared.** The hole your dial reads
is an empty hole until somebody fills it, and that somebody does not have to be
you.

---

## 2. Components bill

Every part is printed. All gears use a 3 mm module and every hole on the plate is
3 mm from the next, which is why every mesh distance in this game is a whole
number of holes.

The **Compound Hub** is the load-bearing part. It is a print-in-place planetary
stack with a captive carrier, sealed inside a bridge body. Its two ends are
identical from outside. What is inside changes both the speed and the direction
of everything past it, and the only way to find out is to crank. It is the reason
this game cannot be a deck of cards.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plate_01`–`plate_04` | Plate Quadrant | 4 | 122 × 122 × 10 | Dovetail together into one 244 × 244 plate with a 240 × 240 field and a 2 mm rim. Grid of ⌀1.8 holes at 3 mm pitch: **81 columns × 81 rows**, numbered 1–81 left to right and 1–81 near to far. |
| `crank_01` | Crank Post | 1 | ⌀30 × 84 | Seats in the one oversized ⌀5 hole, at **column 34, row 46** — off-centre on purpose. One-way ratchet, three detents per revolution. |
| `crank_02` | Crank Handle | 1 | 62 × 16 × 20 | Presses onto the Crank Post shaft. This is the handle. |
| `drive_01` | Drive Gear | 1 | ⌀45 × 8 | 13 teeth, fixed to the crank shaft at gear height. Pushes 13 teeth into the machine per revolution of the handle. Never removed, never pulled. |
| `gear_11` | Gear 11 | 6 | ⌀39 × 10 | 11 teeth. Spoked. The fastest gear in the box and the scarcest. |
| `gear_13` | Gear 13 | 8 | ⌀45 × 10 | 13 teeth. Spoked. |
| `gear_17` | Gear 17 | 8 | ⌀57 × 10 | 17 teeth. Spoked. |
| `gear_19` | Gear 19 | 7 | ⌀63 × 10 | 19 teeth. Spoked. |
| `gear_23` | Gear 23 | 6 | ⌀75 × 10 | 23 teeth. Spoked. |
| `gear_29` | Gear 29 | 5 | ⌀93 × 10 | 29 teeth. Spoked. Slow, and it swallows a quarter of a quadrant. |
| `hub_01`–`hub_06` | **Compound Hub** ★ | 6 | 87 × 39 × 14 | Two 11-tooth ends, centres **16 holes** apart, joined by a sealed planetary train. Each end carries a red index tooth. Inside is one of six pairings of speed and direction (§5b) — unmarked, unguessable, identical from outside. |
| `mag_01` | Hub Magazine | 1 | 96 × 50 × 104 | Opaque stack. Holds all six hubs; dispenses only the bottom one. |
| `dial_01`–`dial_04` | Dial Unit | 4 (one per player) | 90 × 58 × 58 | Clamps anywhere on the plate rim and slides along it. Arm reaches over any hole **1 to 14 holes in from that rim**. A follower rides the read gear's top track and steps the counter one number per revolution of that gear, either way. Counter reads −5 to 25. |
| `ring_01`–`ring_06` | Reading Ring | 6 | ⌀52 × 4 | Marked ×2 same, ×3 same, ÷3 same, ×2 flip, ×3 flip, ÷2 flip. Dropped over a hub end once the table has read that hub. Bookkeeping only. |
| `token_01` | Spanner Token | 16 (four per player) | ⌀18 × 4 | Spent to pull a part off the plate. |
| `tray_01` | Gear Tray | 1 | 186 × 74 × 22 | Six open wells, one per tooth count, each well marked. This is the supply and it is public all game. |
| `tray_02` | Scrap Tray | 1 | 92 × 74 × 22 | Where pulled parts go. Nothing ever comes back out. |

**Three facts about the printed gears that the rules lean on:**

- Every gear has a ⌀1.7 × 5 mm spigot underneath. It drops straight into a plate
  hole and spins there. There are no separate pins and no assembly step.
- Every gear has a ⌀20 mm follower track on its top face with one notch in it.
  The track is identical on all six gears, so any Dial Unit can read any gear.
- Every gear has one **red index tooth**, so you can see which way anything is
  turning at a glance.

---

## 3. Setup

1. Dovetail the four **Plate Quadrants** into one square plate in the middle of
   the table. Column 1 is on the left and row 1 is nearest the player who will go
   first; agree that orientation now and do not move the plate again.
2. Push the **Crank Post** into the one oversized hole — it is the only hole it
   fits, and it is deliberately not in the middle. Press the **Crank Handle** onto
   its shaft. The **Drive Gear** is already on the post. This is the only gear
   that starts on the plate.
3. Tip all 40 gears into the marked wells of the **Gear Tray**. Put the empty
   **Scrap Tray** beside it. Both stay in everyone's reach all game.
4. Without turning them over and **without spinning either end**, stack all six
   **Compound Hubs** into the **Hub Magazine** in any order. Stand the Magazine
   beside the plate and lay the six **Reading Rings** face up next to it.
5. **First player:** whoever most recently turned a real crank, spanner or hand
   drill. If nobody has, the youngest player. Play passes to the left.
6. **Docking, in reverse turn order.** The last player in turn order clamps their
   Dial Unit first; the first player clamps last. Clamp anywhere on any of the
   four rims and set the arm over any hole 1 to 14 holes in from that rim. No two
   Dial Units may read the same hole.
   - **2 players:** the two Dial Units must clamp on different sides of the plate.
   - **3 and 4 players:** no further restriction. Sides are not owned; two players
     may dock on the same side.
7. Set every counter to **0**. Each player takes **4 Spanner Tokens**.

---

## 4. Turn structure

A turn is two steps, in this order. Both always happen. There are no phases
inside a turn, no reactions, and nothing happens between turns.

**Step 1 — Act.** Do exactly one of the four actions in §5. If none of the four is
legal for you, you **Pass** — and Pass is only ever forced. You may not choose it
while any of the four is still open to you.

**Step 2 — Crank.** You, and only you, take the handle and turn it **clockwise
exactly three clicks** — one full revolution. It ratchets; it will not go back.
Three clicks every turn: not two because you are behind, not six because you are
ahead.

Then everybody looks at their own dial. Dials move during the crank, driven by
the machine. Nobody adds anything up and nobody moves a counter by hand.

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

**When do two gears mesh?** One rule, no lookup table:

> **Two gears mesh when their holes are exactly (my teeth + their teeth) ÷ 2
> holes apart.** Every tooth count in this box is odd, so that sum is always even
> and the answer is always a whole number of holes.

The Drive Gear has 13 teeth. Hub ends have 11 teeth. So a Gear 17 meshes the
Drive Gear at (17 + 13) ÷ 2 = **15 holes**, and meshes a hub end at
(17 + 11) ÷ 2 = **14 holes**.

Measure straight along a row or straight along a column. There are also **six
slants** that land two holes a whole number apart, so they can mesh too:

| offset | holes apart on the slant |
|---|---|
| 5 across, 12 along | 13 |
| 9 across, 12 along | 15 |
| 8 across, 15 along | 17 |
| 12 across, 16 along | 20 |
| 10 across, 24 along | 26 |
| 20 across, 21 along | 29 |

**A slant works either way round.** "5 across, 12 along" also means "12 across, 5
along", and either direction counts — up or down, left or right. Six offsets, four
mirror images each: twenty-four holes at 13 from any given hole, and so on down the
table.

A slant only meshes if the number in the right-hand column happens to be that
pair's mesh number. Two holes 20 across and 21 along are 29 apart; a Gear 29 and
a Gear 29 mesh at 29, so those two mesh — a Gear 11 and the Drive Gear mesh at 12,
so at 29 apart they never touch. Any offset not on this list and not straight
along a row or column is not a whole number of holes apart, so it either misses
or fouls, and the plate will tell you which.

> **No two gears may ever sit closer than their mesh number.** The teeth foul and
> the gear will not seat. The plate is the referee — if it does not drop in and
> spin freely, it is not a legal placement.

That last rule is a weapon. A **Gear 29** is ⌀93 mm and needs 20 holes of
clearance from a Gear 11. Parked in the right place it does not just take a hole,
it makes a whole neighbourhood unusable — including the hole somebody's dial is
waiting on.

**Which way it turns.** The Drive Gear turns clockwise, seen from above. Every
mesh reverses. So:

> **Count the meshes from the Drive Gear to the gear under your dial. Even, and
> that gear turns clockwise, and your dial climbs. Odd, and it turns
> anticlockwise, and your dial falls.**

Count before you build. A route that bends — out along a column, then across a
row — is usually two meshes and climbs. A route that reaches a hole in one long
hop is one mesh and drains. The count is a fact about the plate, not about the
gear: the same Gear 11 climbs on one hole and falls on another.

**Failed placement.** If the gear will not seat, fouls a neighbour, fouls a Dial
Unit arm, or the handle will not turn afterwards (§9, *Jams*), the placement is
illegal. Take the gear straight back and put it somewhere else, or switch to a
different action. No penalty and no turn lost. But once you have started
cranking, everything on the plate stands.

### 5b. Draw and place a hub

Instead of a gear, take the **bottom hub from the Hub Magazine** — you do not get
to choose which — and place it on the plate in one motion, both spigots into
holes exactly **16 holes apart** along a row or a column. At least one of its two
ends must mesh a part already on the plate. Either end may mesh, or both.

Hub ends have 11 teeth, so a hub end meshes a Gear 11 at 11 holes, a Gear 13 or
the Drive Gear at 12, a Gear 17 at 14, a Gear 19 at 15, a Gear 23 at 17, a Gear
29 at 20.

Seating a hub on the plate releases its internal lock. **Do not spin a hub in
your hand and do not spin one in the Magazine.** You find out what is inside by
cranking, and that is the game.

Inside each hub is one of these six, and each of the six is in the box exactly
once:

| speed | direction |
|---|---|
| ×2 | keeps it — **same** |
| ×3 | keeps it — **same** |
| ÷3 | keeps it — **same** |
| ×2 | reverses it — **flip** |
| ×3 | reverses it — **flip** |
| ÷2 | reverses it — **flip** |

**A flip hub counts as one extra mesh** for everything past it. A same hub counts
as none. That is the only thing you ever fold into the count in §5a.

**How you read a hub.** Crank, and watch the red index tooth on each of the hub's
two ends. Which way the far end goes against the near end tells you same or flip.
How much farther the far end travels than the near end tells you the speed. One
crank answers both. When the table agrees, drop the matching **Reading Ring** over
the far end so nobody has to remember.

**A hub is the only part in the box that changes speed**, and the only part that
can turn a whole branch around after it is built. A ×3 hub feeding a Gear 11
gives 3.5 numbers a crank — twice as fast as anything plain. A ÷3 hub on the same
gear gives you 0.4. You do not get to choose which one you are holding.

**One hub per run.** No dial may be driven through more than one hub. If placing a
hub here would put two hubs between the handle and any player's read gear, you may
not place it there.

### 5c. Pull

Spend one **Spanner Token** — put it in the Scrap Tray — and take **any one gear
or any one hub** off the plate. It goes to the Scrap Tray and is out of the game
for good. Pulled gears never return to the supply and pulled hubs never return to
the Magazine.

You may pull a gear that a Dial Unit is reading, including your own. You may not
pull the Drive Gear.

Parts left with no live path back to the handle simply stop turning. Leave them
where they are; they still fill their holes and they still foul their neighbours.
A dead branch can be reconnected later — by a gear, or by a hub bridging across to
it — and whoever reconnects it decides what mesh count it comes back on.

Pulling the gear a rival's dial reads costs you one token and one turn, empties
that hole, and hands the next player the choice of what goes back into it.

### 5d. Re-dock

Slide your Dial Unit anywhere along any rim and set its arm over any hole 1 to 14
holes in from that rim. The hole may be empty or may already have a gear on it.
Your counter keeps its number. You may not dock over a hole another Dial Unit is
already reading.

Re-dock is free. It costs only your turn, and it is the answer to a hole that has
gone bad.

### 5e. Pass — forced only

If no gear in the Gear Tray has a legal hole, the Magazine has no hub that will
seat, you have no Spanner Tokens and every re-dock is blocked, you Pass: take no
action. You still crank. Passing is never a choice — while any of 5a–5d is legal,
you must take one of them. Re-dock is nearly always legal, so a real Pass is rare.

---

## 6. How dials move

You do not need this section to play — the machine does it — but you need it to
plan.

One revolution of the handle pushes **13 teeth** into the machine. Teeth do not
multiply or vanish along plain gears: 13 in, 13 out, all the way down the line. A
small gear spins fast, a big gear spins slowly, and the same teeth pass through
both.

Your Dial Unit steps its counter **one number for every full revolution of the
gear it is reading**, in whichever direction that gear is turning.

| gear under your dial | numbers per crank, plain run |
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

Through a hub, multiply the whole line by that hub's speed. Everything else is
unchanged.

### Worked example — the two-mesh bend

Amara docks on the **left rim at row 67**, arm 13 holes in, over hole **(column
14, row 67)**. That hole is a long way from the Crank Post at (34, 46) — 20
columns across and 21 rows along, which the slant table says is 29 holes. Nothing
in the box meshes the Drive Gear at 29, so no single gear will ever reach her hole
in one hop. Whatever gets there has to bend.

**Her turn 1.** She places a **Gear 29** at (34, 67) — 21 holes straight up the
column from the Crank Post. (29 + 13) ÷ 2 = 21, so it meshes the Drive Gear. One
mesh, so that Gear 29 turns anticlockwise. Her own hole is still empty and her
dial is still on 0.

**Her turn 2.** She places a **Gear 11** at (14, 67) — 20 holes straight across
the row from her Gear 29. (11 + 29) ÷ 2 = 20, so it meshes. That is **two
meshes** from the handle. Even. Clockwise. Her dial climbs at 1.18 a crank, on
**everybody's** crank, not only her own. Twenty numbers is about 17 turns of the
handle.

**Now Ben's problem, and his answer.** Ben cannot reach into her run: her Gear 11
is a leaf, and adding a gear past it changes nothing for her. Splicing a gear
between her two gears is impossible — they are already touching, and there is no
room between meshed teeth. What he can do is take one of them away.

**Ben's turn.** He spends a Spanner Token and pulls the **Gear 29 at (34, 46+21)**
out of the middle of her run. Her Gear 11 goes dead where it stands and her dial
holds at 8. It cost him one token and one turn. It costs her a gear that is now
in the Scrap Tray for good — and there were only five Gear 29s in the box.

**Her turn 3.** She can spend a turn putting another Gear 29 back and be climbing
again next crank, which is the cheap fix; or she can put a **hub** in that gap.
The hub's near end meshes the Drive Gear at 12 holes, its far end lands 16 holes
further out, and if it is a ×3 same she is suddenly on 3.5 a crank and the game is
nearly over. If it is a ÷2 flip, she is falling at 0.6 a crank from 8, and −5 is
twenty cranks away — survivable, and slow, and it is her own fault.

That is the game: build the bend, defend the bend, and decide when the sealed box
is worth the gamble.

### The one that costs a game

Ben's other line, if he sees Amara's dock before she builds: two turns of his own.
First a **Gear 11 at (34, 58)** — 12 holes up from the Crank Post, one mesh. Then
a **Gear 29 at (14, 58)** — 20 holes across, two meshes, climbing for him at 0.45.
Her hole at (14, 67) is now nine holes from a Gear 29. Nothing in the box meshes a
Gear 29 at nine holes; everything fouls it. **Her hole is dead, permanently**, and
she has to re-dock and start over.

He has to be first, though. Once her Gear 29 is up at (34, 67), his Gear 11 at
(34, 58) is only nine holes below it and fouls — that whole corridor holds one
player's route or the other's, not both. Look at where people have clamped before
you decide where the metal goes.

### The −5 freeze

A dial that reaches −5 stops there. It does not go lower and it does not move
again — not on anybody's crank — until the end of its owner's **next** turn, at
which point it comes back to life still reading −5. You get one turn of grace,
frozen, to fix your route or re-dock somewhere kinder.

---

## 7. End & winning

The game ends the moment either of these happens.

1. **A dial reaches 20 during a crank.** That player wins immediately. Finish the
   revolution, then stop; nothing else resolves.
2. **A round with no building.** If a complete round goes by — every player takes
   one turn — in which no gear and no hub is placed and no Spanner Token is spent,
   the game ends after the last crank of that round. Highest dial wins.

**The end is reachable, and here is the arithmetic.** Every Place takes one part
out of a finite supply for good. Every Pull takes one token out of a hand for
good. There are 40 gears, 6 hubs and 16 tokens: **62 turns at the absolute
outside** before nobody can build or pull at all, and then ending 2 must fire
inside one more round. Hard ceiling **66 turns of the handle**, even if not one
dial ever moves. In practice the plate fills long before the tray empties — gears
have to sit at least their mesh number apart, so a 240 × 240 field takes somewhere
between twelve and eighteen of them depending on how many big ones go down — so
ending 2 is a real ending, not a formality.

Ending 1 normally arrives first. A player wired to a Gear 11 on an even mesh count
gains 1.18 a crank, and **every player's crank feeds every dial**, so 20 arrives
about 17 cranks after they connect. Connecting takes two or three of their own
turns. Interference — a pull, a dead hole, a re-dock, a hub that came out
backwards — typically costs each player four to eight cranks of progress. Expect
**30 to 40 turns of the handle**, which is **25 to 40 minutes** including the
teach.

The length is measured in cranks, not rounds, so two players and four players play
about the same number of cranks to the same finish. At two players each person
simply takes more of them, so a two-player game runs at the short end of that
range and a four-player game at the long end.

---

## 8. Tiebreak

If ending 2 fires, or if one crank pushes two dials to 20 in the same revolution,
work down this list until one player is left. It always resolves.

1. **Highest number on the counter.** This is why it reads past 20.
2. **Most unspent Spanner Tokens.**
3. **Shortest run.** Count the parts between the Drive Gear and the gear your dial
   reads, not counting the Drive Gear, counting a hub as one part. If the plate
   offers more than one route, count the route with the fewest parts. Fewest wins.
   A dial with no live run to the handle counts as longer than any run and loses
   this step to everybody.
4. **Turn order.** Of the players still tied, the one who would take their turn
   soonest, starting from the player to the left of whoever cranked last.

---

## 9. Edge cases

**Jams.** Gears are rigid, so some placements ask the machine to do two things at
once and it simply locks. Two rulings cover every case:

- **A closed ring of parts jams if the mesh count round the ring is odd.**
  (A flip hub counts as one mesh, a same hub as none.)
- **A closed ring containing any hub jams**, always, because the two ways round
  the ring want different speeds.

A placement that jams the machine is illegal. You find out by trying to crank,
which is fine — a jam before the first click costs nothing. Take the part back off
and place it elsewhere, or switch to a different action. **You cannot jam the
machine on purpose, because a jam is never a legal placement.**

**Closing a ring through a hub nobody has read yet.** You may try it. If it locks,
your placement is void and you take it back — but the whole table just learned
something about that hub for free.

**You cannot legally place any gear anywhere.** You may still Pull or Re-dock. If
neither of those is available either, take no action and crank.

**The well you want is empty.** Too bad. Take a different tooth count or a
different action. Nothing comes back from the Scrap Tray.

**Somebody killed my hole.** Whether they filled it, fouled it with a big gear, or
pulled the run that fed it — that is legal and it is the point. Your answers are:
Re-dock somewhere with an even count, Pull the offending gear, or build a new bend
to a better hole and then Re-dock onto it.

**Somebody docked over the hole I wanted.** First come, first served, and docking
happens in reverse turn order for exactly this reason. Corner holes count as
belonging to both rims that meet there, same rule.

**Placing a gear on a hole that already has a Dial Unit arm over it.** Legal.
Anybody may do it. It becomes that player's read gear at once, so it drives them on
the crank that ends the very turn it was placed — including when the placer was
somebody else.

**A dial with no gear under it.** It holds at whatever it reads and does not move.
That is not a loss — it scores as it stands, and it loses tiebreak step 3.

**A dial that would pass 20 in one crank.** The game stops the instant a counter
shows 20 or more during a crank. If it jumps from 19 to 21, you have won at 21,
and 21 is the number used for tiebreaks. The counter reads to 25.

**Two dials reach 20 in the same crank.** Go to §8.

**Two dials freeze at −5 in the same crank.** Both freeze; each thaws at the end
of its own owner's next turn.

**One dial hits 20 and another hits −5 in the same crank.** The 20 wins the game
and the −5 never matters.

**A frozen dial whose read gear is pulled while it is frozen.** It still thaws on
schedule. It then reads nothing and holds at −5 until its owner re-docks.

**A hub whose far end drives nothing.** Legal, and useless until something
downstream exists. You can still read it — with no load, both index teeth still
move, and comparing the two ends is the whole method.

**Two hubs in one run.** You may never *place* a hub that creates this (§5b).
Everything else that creates it is legal: a **Pull** elsewhere that re-routes a
dial through two hubs, or a **Re-dock** onto a hole that already sits past two of
them. The two speeds multiply, the two directions combine, and the table lives
with it. The restriction is on the hub-placing action alone, not on the shape of
the machine.

**We cannot agree what is inside a hub.** Then do not put a Reading Ring on it.
The rings are bookkeeping and change nothing. The machine keeps doing what it does
whether or not you have worked it out.

**Somebody spun a hub in their hand.** Ask them not to. A hub out of the Magazine
has both ends locked, so it tells them nothing — but it is the one place in this
box where a player can look like they are cheating, so keep hubs going
Magazine-to-plate in one motion.

**Miscranking.** Finish the revolution to the next click and carry on. The machine
has already moved and there is no rewind. If somebody cranks on another player's
turn, the same applies: the crank counts, and the turn's owner does not get a
replacement.

**A quadrant shifts mid-game.** Push it back and carry on. If a gear has been
knocked out of its hole, put it back in the hole it came from; if nobody can agree
which hole, put it in the Scrap Tray and refund nothing. Clamp the quadrants
before the first crank if your table is slippery.
