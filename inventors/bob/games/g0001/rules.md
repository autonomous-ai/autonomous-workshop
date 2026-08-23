# CRANK

*A gear-routing race for 2–4 players. About 30 minutes. Ages 10+.*

---

## 1. Overview

There is one machine on the table and one handle on it. On your turn you bolt a
single gear onto the shared peg plate, then you turn the handle three clicks —
one full revolution — and every dial around the table moves at once.

Your dial only moves if a live line of teeth reaches it from the handle. How
**fast** it moves is set by the size of the gear sitting under it. Which **way**
it moves is set by one thing and one thing only: **how many meshes lie between
the handle and that gear.** Even, and your dial climbs. Odd, and it falls. That
is not a card that says "reverse" — it is what a line of gears actually does, and
you can watch it happen on the red index teeth.

You never add anything up. You crank, and the machine tells you what you built.
**First dial to reach 20 wins on the spot.**

The catch, and the whole game: **the plate is shared.** The hole your dial reads
is an empty hole until somebody fills it, and that somebody does not have to be
you.

---

## 2. Components bill

Every part is printed. All gears use a **3 mm module** and every hole on the
plate is **3 mm from the next**, which is why every mesh distance in this game is
a whole number of holes.

The **Compound Hub** is the load-bearing part. It is a print-in-place planetary
stack with a captive carrier, sealed inside a bridge body. Its two ends are
identical from outside. What is inside changes both the speed and the direction
of everything past it, and the only way to find out is to crank. It is the reason
this game cannot be a deck of cards.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plate_01`–`plate_04` | Plate Quadrant | 4 | 122 × 122 × 10 | Dovetail into one 244 × 244 plate. Each quadrant carries a **40 × 40** grid of ⌀2.0 holes at 3 mm pitch, first hole 3.5 mm from its two outer edges and 1.5 mm from its two seam edges, so the pitch runs unbroken across the joint. Assembled: **80 columns × 80 rows**, columns 1–80 left to right, rows 1–80 near to far. The seams fall *between* columns 40 and 41 and *between* rows 40 and 41 — no hole sits on a joint. Column and row numbers are engraved along the outer edges. |
| `crank_01` | Crank Post | 1 | ⌀30 × 84 | Seats in the one oversized ⌀5 hole, at **column 34, row 27** — off-centre on purpose. One-way ratchet, three detents per revolution. |
| `crank_02` | Crank Handle | 1 | 62 × 16 × 20 | Presses onto the Crank Post shaft. This is the handle. |
| `drive_01` | Drive Gear | 1 | ⌀45 × 8 | 13 teeth, fixed to the crank shaft at gear height. Pushes 13 teeth into the machine per revolution of the handle. Never removed, never pulled, never read. |
| `gear_11` | Gear 11 | 6 | ⌀39 × 10 | 11 teeth. Spoked. The fastest gear in the box and the scarcest. |
| `gear_13` | Gear 13 | 8 | ⌀45 × 10 | 13 teeth. Spoked. |
| `gear_17` | Gear 17 | 8 | ⌀57 × 10 | 17 teeth. Spoked. |
| `gear_19` | Gear 19 | 7 | ⌀63 × 10 | 19 teeth. Spoked. |
| `gear_23` | Gear 23 | 6 | ⌀75 × 10 | 23 teeth. Spoked. |
| `gear_29` | Gear 29 | 5 | ⌀93 × 10 | 29 teeth. Spoked. Slow, and it sterilises a neighbourhood. |
| `hub_01`–`hub_06` | **Compound Hub** ★ | 6 | 87 × 39 × 14 | Two 11-tooth ends, spigot centres **16 holes** apart, joined by a 20 mm-wide deck standing 10–14 mm above the plate. Each end carries a red index tooth; each end's top boss is the sealed carrier, so **a Dial Unit can never read a hub end**. Inside is one of six pairings of speed and direction (§5b) — unmarked, unguessable, identical from outside. |
| `mag_01` | Hub Magazine | 1 | 96 × 50 × 104 | Opaque stack. Holds all six hubs; dispenses only the bottom one. |
| `dial_01`–`dial_04` | Dial Unit | 4 (one per player) | 90 × 58 × 58 | Clamps anywhere on the plate rim. Its arm runs **straight in from the clamp, square to that rim**, as a gantry 22 mm above the plate — it bridges clear over every gear and every hub. Only the follower reaches down, and only at the read hole, which may be **1 to 14 holes in from that rim**. Counter reads −5 to 25. |
| `ring_01`–`ring_06` | Reading Ring | 6 | ⌀36 × 4 | Six discs, engraved ×2 same, ×3 same, ÷3 same, ×2 flip, ×3 flip, ÷2 flip. Drops over a hub end's carrier boss and rests on the hub deck at 14 mm, clear of every gear. Bookkeeping only. |
| `token_01` | Spanner Token | 16 (four per player) | ⌀18 × 4 | Spent to pull a part off the plate. |
| `tray_01` | Gear Tray | 1 | 186 × 74 × 22 | Six open wells, one per tooth count, each well marked. This is the supply and it is public all game. |
| `tray_02` | Scrap Tray | 1 | 92 × 74 × 22 | Where pulled parts go. Nothing ever comes back out. |

**Five facts about the printed parts that the rules lean on:**

- Every gear has a ⌀1.7 × 8 mm spigot underneath and a ⌀12 × 1 mm bearing pad
  around it. The spigot drops into a plate hole and locates; the pad rides the
  plate and carries the load. No separate pins, no assembly step.
- Every gear has a ⌀20 mm follower track on its top face with one drive pin
  standing in it. The track is identical on all six gears, so any Dial Unit can
  read any gear.
- The Dial Unit's follower is a slotted star wheel. The pin enters the slot once
  per revolution of the read gear and carries the counter one number — forward if
  that gear is turning clockwise, back if anticlockwise. It works in both
  directions and it carries the remainder for you.
- Every gear and every hub end has one **red index tooth**, so you can see which
  way anything is turning at a glance.
- The tightest thing in the box is the 1.0 mm wall between plate holes. Print the
  quadrants first and check one before committing to the other three.

---

## 3. Setup

1. Dovetail the four **Plate Quadrants** into one square plate in the middle of
   the table, matching the engraved numbers so column 1 is on the left and row 1
   is nearest the player who will go first. Agree that orientation now and do not
   move the plate again.
2. Push the **Crank Post** into the one oversized hole — it is the only hole it
   fits, at column 34, row 27, and it is deliberately not in the middle. Press the
   **Crank Handle** onto its shaft. The **Drive Gear** is already on the post.
   This is the only gear that starts on the plate.
3. Tip all 40 gears into the marked wells of the **Gear Tray**. Put the empty
   **Scrap Tray** beside it. Both stay in everyone's reach all game.
4. Stack all six **Compound Hubs** into the **Hub Magazine** in any order, without
   turning them over. Stand the Magazine beside the plate and lay the six
   **Reading Rings** face up next to it. A hub off the plate has both ends locked,
   so handling one tells you nothing.
5. **First player:** whoever most recently turned a real crank, spanner or hand
   drill. If nobody has, the youngest player. Play passes to the left.
6. **Dock, in reverse turn order.** The last player in turn order clamps their
   Dial Unit first; the first player clamps last. Clamp anywhere on any of the
   four rims and set the arm 1 to 14 holes in. Two rules: no two Dial Units may
   read the same hole, and two clamps may not physically overlap — the plate is
   the referee. Sides are not owned; players may share a rim.
   > **Why reverse order:** the first player gets the first build and the first
   > crank, so the last player gets first pick of the plate. The crank sits nearer
   > the near rim and the left rim than the other two, so those holes are shorter
   > to reach and mostly run **backwards**; the far and right rims are two gears
   > away and mostly run **forwards**. Where you clamp is the first real decision
   > in this game.
7. Set every counter to **0**. Each player takes **4 Spanner Tokens**.

---

## 4. Turn structure

A turn is two steps, in this order. Both always happen. There are no phases
inside a turn, no reactions, and nothing happens between turns.

**Step 1 — Act.** Do exactly one of the four actions in §5a–5d. If none of the
four is legal for you, you **Pass** (§5e) — and Pass is only ever forced.

**Step 2 — Crank.** You, and only you, take the handle and turn it **clockwise
exactly three clicks** — one full revolution. It ratchets; it will not go back.
Three clicks every turn: not two because you are behind, not six because you are
ahead.

Then everybody looks at their own dial. Dials move during the crank, driven by
the machine. Nobody adds anything up and nobody moves a counter by hand.

- Any dial that reaches **20 or more** — that player wins immediately. Stop.
- Any dial that reaches **−5** stops there and freezes (§5f).

Then the turn passes to the left.

---

## 5. Actions

Pick exactly one of 5a–5d. 5e only if none of them is available.

### 5a. Place a gear

Take any one gear from the Gear Tray and drop it onto an empty hole. **It must
mesh at least one part already on the plate** — the Drive Gear counts, a hub end
counts, a dead gear counts. It may mesh several.

**Two numbers govern every placement.** For any two gears, their **mesh number**
is

> **M = (my teeth + their teeth) ÷ 2, counted in holes.**

Every tooth count in this box is odd, so that sum is always even and M is always
a whole number. The Drive Gear is 13 teeth; a hub end is 11 teeth and behaves in
every geometric way like a Gear 11.

Now measure **d**, the straight-line distance between the two holes, in holes.
Then exactly one of three things is true:

| d | what happens |
|---|---|
| **d = M exactly** | They **mesh**. Teeth interleave, both spin. |
| **M < d < M + 3**, or **d < M** | They **foul**. The teeth collide, the gear will not seat. **Illegal.** |
| **d ≥ M + 3** | They **clear**. Neither knows the other is there. |

There is no fourth case. If it drops in and spins freely, it was legal.

**Where can d be a whole number?** Straight along a row, straight along a column,
and on exactly six slants:

| offset | d |
|---|---|
| 5 across, 12 along | 13 |
| 9 across, 12 along | 15 |
| 8 across, 15 along | 17 |
| 12 across, 16 along | 20 |
| 10 across, 24 along | 26 |
| 20 across, 21 along | 29 |

A slant works either way round and in any direction: "5 across, 12 along" is also
"12 across, 5 along", up or down, left or right. Six offsets, four mirror images
each — twenty-four holes at exactly 13 from any given hole, and so on down the
table. Anywhere else, d is not a whole number, so nothing meshes there; it either
clears or fouls, and the clearance rule above still decides which.

> **The Gear 29 is a weapon.** It needs 20 holes of daylight from a Gear 11 to
> mesh, and 23 to clear. Parked in the right place it does not just take a hole —
> it makes a whole neighbourhood unusable, including the hole somebody's dial is
> waiting on.

**Which way it turns.** The Drive Gear turns clockwise, seen from above, and is
**mesh count 0**. Every mesh reverses. So:

> **Count the meshes from the Drive Gear out to the gear under your dial. Even,
> and that gear turns clockwise, and your dial climbs. Odd, and it turns
> anticlockwise, and your dial falls.** A flip hub in the line counts as **one
> extra mesh**; a same hub counts as none.

Count before you build. A gear that meshes the Drive Gear directly is count 1 and
**drains**. A gear one further out is count 2 and **climbs**. The count is a fact
about the route, not about the gear: the same Gear 11 climbs on one hole and
falls on another.

**Rings.** A gear may mesh two or more parts and close a loop. Two rulings, and
between them they cover every loop:

- **A loop whose mesh count round the ring is odd jams.** The two ways round want
  opposite directions and the machine locks.
- **A loop containing any hub jams**, always, because the two ways round want
  different speeds.

A placement that jams the machine is **illegal** — the handle simply will not
turn. Take the part back off and place it elsewhere or switch actions; a jam
discovered before the first click costs nothing. Even-count, hub-free loops are
fine and turn happily. That is also why your mesh count is never ambiguous: if
two routes reached your gear with different parities, they would form an odd
loop, and an odd loop is not a legal plate.

**One hub to a run.** No part may ever be driven through two hubs. If you follow
the meshes out from the Drive Gear to any part, you may pass **at most one hub**.
A gear placement that would link a hub-carrying dead branch into a run that
already holds a hub is illegal. (§5b keeps hub placements on the right side of
this too. Pulling can only ever shorten a run, so it can never break this rule.)

**Failed placement.** If the gear will not seat, fouls a neighbour, or jams the
machine, the placement is illegal. Take it straight back and put it somewhere
else, or switch to a different action. No penalty and no turn lost. But once you
have started cranking, everything on the plate stands.

### 5b. Draw and place a hub

Instead of a gear, take the **bottom hub from the Hub Magazine** — you do not get
to choose which — and place it on the plate in one motion, both spigots into
holes exactly **16 holes apart along a row or a column** (16 is not on the slant
table, so hubs never go diagonally). Seating both spigots releases the internal
lock.

A hub placement is legal only if all three of these hold:

1. **Exactly one** of its two ends meshes an existing part. The other end must
   land on an empty hole and mesh nothing. (This is why a hub can never close a
   loop.)
2. That existing part is on a **live run from the Drive Gear**, and **no hub is
   already on that run**.
3. Both ends clear every other part by the §5a table, treating each end as an
   11-tooth gear.

The end that meshes is the **near end**; the other is the **far end**. Hub ends
mesh a Gear 11 at 11 holes, a Gear 13 or the Drive Gear at 12, a Gear 17 at 14, a
Gear 19 at 15, a Gear 23 at 17, a Gear 29 at 20. Nothing can sit under the hub's
deck — anything there would already be inside 14 holes of an end and fouling it.

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

**How you read a hub.** Crank, and watch the red index tooth on each of the hub's
two ends. Which way the far end goes against the near end tells you same or flip.
How much further the far end travels than the near end tells you the speed. One
crank answers both, and it works even with nothing downstream. When the table
agrees, drop the matching **Reading Ring** over the far end so nobody has to
remember.

**A hub is the only part in the box that changes speed**, and the only part that
can turn a whole branch around after it is built. A ×3 hub feeding a Gear 11
gives 3.5 numbers a crank — three times anything plain. A ÷3 hub on the same gear
gives you 0.4. You do not get to choose which one you are holding.

### 5c. Pull

Spend one **Spanner Token** — put it in the Scrap Tray — and take **any one gear
or any one hub** off the plate. It goes to the Scrap Tray and is out of the game
for good. Pulled gears never return to the supply and pulled hubs never return to
the Magazine.

You may pull a gear that a Dial Unit is reading, including your own. You may not
pull the Drive Gear.

Parts left with no live path back to the handle simply stop turning. Leave them
where they are; they still fill their holes and they still foul their neighbours.
A dead branch can be reconnected later — by a gear, or by a hub — and **whoever
reconnects it decides what mesh count it comes back on.** That is the sharpest
knife in the box: pull one gear out of the middle of a rival's run, spend a turn
rebuilding the route one gear longer than it was, and their dial now runs
backwards on every crank including their own.

Pulling the gear a rival's dial reads costs you one token and one turn, empties
that hole, and hands the next player the choice of what goes back into it.

### 5d. Re-dock

Slide your Dial Unit anywhere along any rim, square to that rim, and set its arm
over any hole 1 to 14 holes in. The hole may be empty or may already have a gear
on it. Your counter keeps its number.

Two restrictions: you may not dock over a hole another Dial Unit is already
reading, and **you must end up over a different hole than the one you were
reading** — re-dock is a move, not a stall.

Re-dock costs no token. It costs your turn, and it is the answer to a hole that
has gone bad.

### 5e. Pass — forced only

If no gear in the Gear Tray has a legal hole, the Magazine has no hub that will
seat, you have no Spanner Tokens, and every re-dock is blocked, you Pass: take no
action. You still crank. Passing is never a choice — while any of 5a–5d is legal,
you must take one of them. Re-dock is legal in almost every position, so a real
Pass is close to impossible.

### 5f. How dials move (reference)

You do not need this to play — the machine does it — but you need it to plan.

One revolution of the handle pushes **13 teeth** into the machine. Teeth do not
multiply or vanish along plain gears: 13 in, 13 out, all the way down the line. A
small gear spins fast, a big gear spins slowly, and the same teeth pass through
both. **Only the gear under your dial sets your speed.** Every gear between it
and the handle is routing, nothing more.

| gear under your dial | numbers per crank, plain run |
|---|---|
| 11 | 1.18 |
| 13 | 1.00 |
| 17 | 0.76 |
| 19 | 0.68 |
| 23 | 0.57 |
| 29 | 0.45 |

You never work those fractions out. The star wheel carries the remainder with it,
so some cranks your dial clicks twice and some cranks it does not click at all.
Watch it; it will tell you.

Through a hub, multiply the whole line by that hub's speed. Nothing else changes.

**The −5 freeze.** A dial that reaches −5 stops there. It does not go lower and it
does not move again — not on anybody's crank — until the end of its owner's
**next** turn, at which point it comes back to life still reading −5. You get one
turn of grace, frozen, to fix your route or re-dock somewhere kinder.

### 5g. Worked examples

**The two-mesh bend.** Amara clamps on the **near rim at column 17**, arm 9 holes
in, reading hole **(17, 9)**. The Crank Post is at **(34, 27)**. From her hole to
the post is 17 across and 18 along — not a whole number of holes, so *nothing* in
the box will ever mesh the Drive Gear from her hole in one hop. Whatever gets
there has to bend.

- **Her turn 1.** Gear 23 at **(34, 9)** — 18 holes straight down the column from
  the post. M(23,13) = 18, so it meshes the Drive Gear. **Mesh count 1**, so it
  turns anticlockwise. Her hole is still empty; her dial is still on 0.
- **Her turn 2.** Gear 11 at **(17, 9)** — 17 holes straight along the row from
  her Gear 23. M(11,23) = 17, so it meshes. It is 24.8 holes from the Drive Gear
  and M(11,13) = 12, so it clears the post comfortably. **Mesh count 2.** Even.
  Clockwise. Her dial now climbs 1.18 a crank on **everybody's** crank, not just
  hers. Twenty numbers is about 17 turns of the handle.

**The block that costs a game.** Ben can see her clamp. Her Gear 23 at (34, 9) is
live at count 1, and M(29,23) = 26, so on his turn he puts a **Gear 29 at
(8, 9)** — 26 holes along row 9 from her Gear 23. It meshes; it clears the Drive
Gear (31.6 holes, needs 24). And it sits **9 holes** from her hole at (17, 9).
The smallest mesh number anything has with a Gear 29 is 20, so nothing will ever
seat at (17, 9) again. **Her hole is dead, permanently.** She has to re-dock.

His Gear 29 is count 2, so it climbs for him at 0.45, and (8, 9) is inside both
the near band and the left band — he can dock on it himself.

He has to be first, though. Once her Gear 11 is down at (17, 9), his Gear 29 at
(8, 9) is 9 holes from it and M(11,29) = 20, so it fouls and will not seat. That
corridor holds one player's route or the other's, never both. **Look at where
people have clamped before you decide where the metal goes.**

**The hub swing.** Ben builds right instead. Hub near end at **(46, 27)** — 12
holes along row 27 from the post, M(11,13) = 12, so it meshes the Drive Gear. Far
end lands at **(62, 27)**, 16 holes further out, meshing nothing. Next turn,
Gear 11 at **(73, 27)** — 11 holes on, M(11,11) = 11, so it meshes the far end.
Column 73 is 8 holes in from the right rim, so he can dock on it.

Count: Drive → near end is 1 mesh, far end → Gear 11 is another, so **2 meshes
plus whatever the hub does.**

- Hub reads **×3 same**: 2 meshes, even, and 1.18 × 3 = **3.55 a crank, climbing**.
  Six cranks and he is done.
- Hub reads **×3 flip**: 3 meshes, odd — 3.55 a crank *the wrong way*. Two cranks
  to −5 and a freeze.
- Hub reads **÷3 same**: 0.39 a crank. He has spent two turns building a treacle
  pump.

He found out by cranking. That is the game.

---

## 6. End & winning

The game ends the moment either of these happens.

1. **A dial reaches 20 or more during a crank.** That player wins immediately.
   Finish the revolution, then stop; nothing else resolves.
2. **A round with no building.** If a complete round goes by — every player takes
   one turn — in which no gear and no hub is placed and no Spanner Token is spent,
   the game ends after the last crank of that round. Highest dial wins.

**The end is reachable, and here is the arithmetic.** Every Place takes one part
out of a finite supply for good. Every Pull takes one token out of a hand for
good. There are 40 gears, 6 hubs and 16 tokens: **62 turns at the absolute
outside** in which anyone can build or pull at all, after which ending 2 must fire
inside one more round. Hard ceiling **66 turns of the handle**, even if not one
dial ever moves. In practice the plate saturates long before the tray empties —
parts must sit either exactly at their mesh number or three holes clear of it, so
an 80 × 80 field takes somewhere between twenty and thirty of them depending on
how many big ones go down — so ending 2 is a real ending, not a formality.

Ending 1 normally arrives first. A player reading a Gear 11 or Gear 13 on an even
count gains 1.0–1.18 a crank, and **every player's crank feeds every dial**, so 20
arrives 17 to 20 cranks after they connect. Connecting takes two of their own
turns. Interference — a pull, a dead hole, a re-dock, a hub that came out
backwards — typically costs each player four to eight cranks. Expect **26 to 34
turns of the handle**, at roughly a minute a turn including the placement hunt:
**25 to 35 minutes**, plus about five to teach.

A lucky ×3 hub can end it in twenty minutes. A table that keeps pulling each other
apart runs to forty. Thirty is the middle and it is where most games land.

**Player counts.** The length is measured in *cranks*, not rounds, so two players
and four players play about the same number of cranks to the same finish — at two
players each person simply takes more of them. Nothing in the rules changes with
the count, and there is no variant to remember: the gear supply (40) and the plate
(6400 holes) are far larger than any count needs, docking in reverse turn order
pays back the first player's tempo at every count, and 4 tokens each is the same
deal for everyone. Two players is the sharpest, because every gear you place is
placed in front of exactly one opponent.

---

## 7. Tiebreak

If ending 2 fires, or if one crank pushes two dials to 20 or more in the same
revolution, work down this list until one player is left. It always resolves.

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

## 8. Edge cases

**You cannot legally place any gear anywhere.** You may still Pull or Re-dock. If
neither is available either, take no action and crank.

**The well you want is empty.** Too bad. Take a different tooth count or a
different action. Nothing comes back from the Scrap Tray.

**Somebody killed my hole.** Whether they filled it, fouled it with a big gear, or
pulled the run that fed it — that is legal and it is the point. Your answers are:
Re-dock somewhere with an even count, Pull the offending gear, or build a new bend
to a better hole and then Re-dock onto it.

**Somebody docked over the hole I wanted.** First come, first served, and docking
happens in reverse turn order for exactly this reason. A corner hole belongs to
both rims that meet there, same rule.

**Placing a gear on a hole a Dial Unit is already reading.** Legal, and anybody
may do it. It becomes that player's read gear at once, so it drives them on the
crank that ends the very turn it was placed — including when the placer was
somebody else, and including when the route reaching it is odd and drains them.

**A dial with no gear under it, or over a dead gear.** It holds at whatever it
reads and does not move. That is not a loss — it scores as it stands, and it
loses tiebreak step 3.

**A dial over a hub end.** Not possible. The carrier boss fills the follower
track; there is nothing for the star wheel to grip. If a hub end lands under a
docked arm, that dial reads nothing until its owner re-docks.

**A dial over the Drive Gear.** Not possible either. The Crank Post is 27 holes
from the nearest rim and no arm reaches past 14.

**A dial that would pass 20 in one crank.** The game stops the instant a counter
shows 20 or more during a crank. If it jumps 19 → 21, you have won at 21, and 21
is the number used for tiebreaks. The counter reads to 25.

**Two dials reach 20 in the same crank.** Go to §7.

**Two dials freeze at −5 in the same crank.** Both freeze; each thaws at the end
of its own owner's next turn.

**One dial hits 20 and another hits −5 in the same crank.** The 20 wins the game
and the −5 never matters.

**A frozen dial whose read gear is pulled while it is frozen.** It still thaws on
schedule. It then reads nothing and holds at −5 until its owner re-docks.

**A frozen dial still takes its turn.** Freezing stops the counter, not the
player. Act and crank as normal.

**A dial that is already at −5 and thaws onto a backward run.** It goes straight
back to −5 on the next crank and freezes again. That is the punishment for not
using the free turn to re-dock.

**Closing a loop through a hub nobody has read yet.** A hub can never close a loop
(§5b rule 1), but a *gear* can close one onto a hub. It always jams, so your
placement is void and you take it back — and it costs the table nothing, because
every hub jams every loop.

**A gear that meshes three or four parts at once.** Legal, as long as every loop
it closes is even and hub-free. Check each loop separately.

**A hub whose far end drives nothing.** That is the only legal way to place one.
It stays useless until something downstream exists — and you can still read it,
because with no load both index teeth still move and comparing the two ends is the
whole method.

**A hub whose near end gets pulled out from under it.** The hub goes dead where it
stands, still fouling its neighbours, and its ends stay locked in whatever
position they stopped in. Reconnect it later like any dead part — and remember
that whichever end gets meshed first becomes the new near end, which may not be
the end you read it on. The Reading Ring's speed still holds; the direction it
records is relative to the near end, so if the other end becomes the near end,
same is still same and flip is still flip.

**Two hubs in one run.** Never happens. §5a and §5b between them block every
action that could create it, and no Pull can, because pulling only ever shortens a
run.

**We cannot agree what is inside a hub.** Then do not put a Reading Ring on it.
The rings are bookkeeping and change nothing. The machine keeps doing what it does
whether or not you have worked it out.

**Somebody spun a hub in their hand.** A hub off the plate has both ends locked
solid, so it tells them nothing. It is still the one place in this box where a
player can *look* like they are cheating, so keep hubs going Magazine-to-plate in
one motion.

**Miscranking.** Finish the revolution to the next click and carry on. The machine
has already moved and there is no rewind. If somebody cranks on another player's
turn, the same applies: the crank counts, and the turn's owner does not get a
replacement.

**Cranking backwards.** You cannot. The Crank Post has a one-way ratchet. If the
handle will not turn forwards, something on the plate is jammed — find the loop.

**A quadrant shifts mid-game.** Push it back and carry on. If a part has been
knocked out of its holes, put it back where it came from; if nobody can agree
where, put it in the Scrap Tray and refund nothing. Clamp the quadrants before the
first crank if your table is slippery.

**Everybody re-docks and nobody builds.** Then the game ends after that round
(§6, ending 2) and the highest dial wins. That is a legitimate way for a table to
call it — but it takes every player agreeing, and anyone behind just places a gear
instead.
