# KICK

A pushing game for 2–4 players. About 20 minutes. Ages 14+.

---

## 1. Overview

Kick is an abstract pushing game played on one printed rail. Every tile you own
carries a small metal disc in one end. Only you know whether that disc is a
magnet with its **north** pole out, a magnet with its **south** pole out, or a
plain steel slug that is not a magnet at all — the three discs look the same and
weigh the same.

On your turn you slide one tile into an open end of the rail and drive it home
with a finger. In the last few millimetres you feel what is going to happen
before anybody else does, and then it happens out loud: the line either snaps
shut around your tile, or a hidden pair of like poles blows apart and throws
every tile past the break out of the far end of the rail and into your tray.

Tiles you throw out are your score. Your own tiles are worth nothing to you, so
the fat, tempting line is only worth detonating if it is fat with somebody
else's colour. When every hand is empty, the player who has captured the most
tiles that are not their own colour wins.

---

## 2. Components bill

Every component is a printed part unless the role says "purchased".

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `rail_01` | Rail | 1 | 240 × 30 × 16 | The board. A straight open channel 240 × 18.4 × 10.4 mm, divided by printed tick marks on the top edges into **10 slots** of 24 mm, numbered 1–10. Both ends are open. Clearance around a tile is 0.3–0.4 mm on every face so a tile slides freely. |
| `tile_01`–`tile_48` | **Pole tile** | 48 (12 per player) | 24 × 18 × 10 | **THE LOAD-BEARING PART.** A blind pocket ⌀6.15 × 3.5 mm is sunk in the centre of ONE end face; the disc that goes in it sits 0.5 mm below the surface and is held by friction alone, no glue. That end is the **head** and is marked by a printed notch on the top face. The other end is the **tail**: bare plastic. The top face also carries the owner's colour and a number 1–12. |
| `magnet_01`–`magnet_32` | N35 disc magnet | 32 (8 per player) | ⌀6 × 3 | Purchased. Nickel-plated neodymium. Goes in a tile's head pocket either way round. Mass 0.64 g. |
| `slug_01`–`slug_16` | Steel slug | 16 (4 per player) | ⌀6 × 3 | Purchased. Plain mild steel, not magnetised. Same finish, mass 0.67 g — indistinguishable from a magnet by eye or by hand. This is the bluff. |
| `rack_01`–`rack_04` | Player rack | 4 (1 per player) | 96 × 86 × 22 | Three labelled troughs that hold tiles standing on edge: **N** (8 slots), **S** (8 slots), **STEEL** (4 slots). The rack is your memory — a tile's trough tells you what is inside it. |
| `screen_01`–`screen_04` | Screen | 4 (1 per player) | 150 × 80 × 24 | L-profile: a 2.4 mm panel on a 150 × 24 mm foot. Hides your rack. |
| `tray_01`–`tray_04` | Score tray | 4 (1 per player) | 90 × 70 × 22 | Open well. Holds captured tiles. Contents are public at all times. |
| `catch_01`–`catch_02` | Catch tray | 2 | 96 × 60 × 18 | Clips onto an end of the rail. Its floor sits 1 mm below the channel floor, so a tile leaving the rail drops in and stays. |
| `probe_01` | Probe wand | 1 | 110 × 14 × 12 | A handle with a pocket at the tip for one magnet. One long face is printed **N**, the other **S**, matching the pole that faces out on each side of the tip magnet. |
| `probe_magnet_01` | Probe magnet | 1 | ⌀6 × 3 | Purchased. N35, seated in the wand tip at the factory and marked. |
| `chip_01`–`chip_12` | Probe chip | 12 (3 per player) | ⌀16 × 3 | Spent to take the Probe action. |
| `card_01`–`card_04` | Joint card | 4 (1 per player) | 88 × 56 × 1.6 | The joint table from section 5, printed. Public reference. |

Everything prints on a 256 mm bed; the rail at 240 mm is the only long part.

---

## 3. Setup

1. Clip a **catch tray** to each end of the rail. Put the rail in the middle of
   the table, long axis across the table so both ends are reachable.
2. Each player takes one colour: 12 pole tiles, 8 magnets, 4 steel slugs, a
   rack, a screen, a score tray, 3 probe chips, and a joint card. Put the
   screen up. Everything behind it stays private except the score tray, which
   sits in front of the screen, contents up.
3. **Load your tiles, behind your screen.** Press one disc into the head pocket
   of each of your 12 tiles. You must use all 8 magnets and all 4 steel slugs,
   one per tile. For each magnet you choose which pole faces out. Then stand
   each tile in the rack trough that matches what you put in it: **N**, **S**,
   or **STEEL**. You may split your 8 magnets between N and S however you like,
   including all 8 one way.
4. Put the probe wand on the table where anyone can reach it. Keep your 3 probe
   chips in front of your screen, face up — probe chips are public.
5. **Hand size by player count.** Return tiles you will not use to the box, from
   whichever troughs you choose, but keep the discs in them and keep the count
   honest — put back whole loaded tiles, not discs.
   - **2 players:** 12 tiles each.
   - **3 players:** 10 tiles each.
   - **4 players:** 9 tiles each.
6. **Start player.** Each player stands one tile from their rack on the table,
   number up. Highest number goes first. Re-do it if the highest is tied.
   Return the tiles to their troughs afterwards. Play proceeds clockwise.
7. The rail starts empty.

---

## 4. Turn structure

There are no phases. On your turn you take exactly one action:

- **Push** (section 5.1), or
- **Probe** (section 5.2).

Then your turn ends and the player on your left takes a turn.

You must take an action if you can. You may always Push while you have a tile
in your rack, so you can never be stuck.

**When your rack is empty you are out of the game.** You take no more turns,
you cannot Probe, and your score tray is locked. The other players keep going
until their racks are empty too.

---

## 5. Actions

### The three kinds of joint

Whenever two tiles come into contact in the rail, the two faces that touch make
a **joint**. There are exactly three kinds, and the discs decide which — always,
immediately, and without anybody's opinion.

|  | N face | S face | steel face | bare face |
|---|---|---|---|---|
| **N face** | **KICK** | CLAMP | CLAMP | slack |
| **S face** | CLAMP | **KICK** | CLAMP | slack |
| **steel face** | CLAMP | CLAMP | slack | slack |
| **bare face** | slack | slack | slack | slack |

- **KICK** — two like poles meet. They fly apart. This is the only thing that
  captures tiles.
- **CLAMP** — the two tiles snap together, loudly. They are now welded: they
  move as one tile for the rest of the game and that joint can never kick.
  Mark it by leaving them touching; a clamped pair does not come apart on the
  table.
- **slack** — the faces touch and nothing happens.

A joint's kind is public the moment it forms. Everyone hears a clamp and
everyone sees a kick. There is nothing to argue about and no reveal.

### 5.1 Push

**Cost:** one tile from your rack. The tile is spent whatever happens.

**Procedure.**

1. Announce which end of the rail you are pushing into. That is the **near
   mouth**; the other end is the **far mouth**. Slot 1 is the slot at the near
   mouth and slot 10 is the slot at the far mouth. (These flip depending on
   which end you push into. Everything below is written from the near mouth
   outward.)
2. Take a tile from behind your screen. Choose which end goes in first: **head
   first** (disc leading, into the rail) or **tail first** (bare end leading,
   which leaves your disc facing out of the mouth). Everyone can see which you
   chose, because the head is notched.
3. **Commitment.** Once the tile crosses the mouth of the rail you must
   complete this push with this tile in this orientation into this end. You may
   not hover a tile near the rail to feel what is inside it. If you bring a
   tile within a hand's width of the rail, it is committed.
4. Drive the tile in with one finger:
   - **If slot 1 is empty:** the tile slides in and you drive it until it
     touches the first tile it meets, and stop there. Nothing else moves. If
     the rail is completely empty, drive it all the way to slot 10 and leave it
     there.
   - **If slot 1 is occupied:** there is no room, so your tile drives the block
     in front of it. Shift the tile in slot 1 and every tile in unbroken
     contact with it one slot toward the far mouth. Any tile shoved past slot
     10 leaves the rail, drops into the catch tray, and goes to your score
     tray. Tiles beyond a gap do not move. Your tile takes slot 1.
   Push all the way home. Do not release early and do not flick — force does
   nothing here, and shoving harder changes no outcome.
5. **Resolve.** Look at every joint in the rail that has just come into
   contact — the joint your tile made, and any joint made by a gap closing in
   front of it. Scan them starting from the near mouth and moving outward.
   Find the **first KICK**.
   - **No kick:** the push is over. New clamps are welded, new slack joints do
     nothing.
   - **A kick:** it fires. The tile on the far side of that joint, and every
     tile in unbroken contact with it, is **launched** — it slides toward the
     far mouth until its leading tile either leaves the rail or hits the next
     tile, then stops. Every tile that leaves the rail goes to **your** score
     tray, however many that is. Tiles on the near side of the kick, including
     your own tile, stay exactly where they are.
   - **Only one kick fires per push.** If the launch closes another gap and
     makes a second kick joint, it does not fire; those two tiles sit against
     each other as a live kick joint, and the next push that squeezes them will
     set it off.

**Worked push.** The rail from the left mouth reads: slot 1 empty, slot 2 an
orange tile head-left, slot 3 a blue tile head-right (so slots 2 and 3 are
head-to-head), slot 4 empty, slots 5–7 a green block, slots 8–10 empty. You
push from the left, head first, with an **N** tile.

Slot 1 is empty, so your tile slides in and stops at slot 1 touching orange at
slot 2. Nothing else moves. One new joint: your **N** head against orange's
head. Orange is **N** too — KICK. Orange and blue are in unbroken contact, so
both launch right. They slide until blue hits the green block at slot 5: orange
lands in slot 3, blue in slot 4. Nothing left the rail, so you capture nothing —
but you have shunted two tiles onto the green block, and blue's tail now sits
against green's head as an untouched joint that the next push from the left will
squeeze.

Had the green block not been there, orange and blue would have slid the length
of the rail and dropped out the far mouth into your tray: two tiles, one of
which was blue's, worth one point.

**Physical rulings.**

- **A tile that will not go in.** If the channel is blocked because a tile is
  sitting crooked, straighten it with a finger first, then push. This is
  maintenance, not a move.
- **A tile that jumps out of the rail sideways, or off the table.** It has left
  the rail. It goes to the score tray of the player whose push moved it.
- **A launched block that stalls short of the mouth.** If a block was clearly
  launched at the far mouth and stops with a tile hanging over the lip, slide
  it out with one finger. What the physics decides is *where the break is*, not
  how far anything travels; the finger only finishes the delivery.
- **A disc that falls out of its pocket.** Press it back in the same way round.
  If nobody can say which way round it was, its owner decides, in private,
  and the game continues.
- **A clamped pair that comes apart** by mishandling: put it back together. It
  is still one welded tile.
- **You may never re-load a tile once setup is finished.** The discs stay where
  you put them for the whole game.

### 5.2 Probe

**Cost:** one probe chip. Return it to the box; it is gone.

**Procedure.** Name one mouth of the rail. Take the probe wand and touch its
**N** face to the outward-facing end face of the tile sitting in that mouth
slot. Say out loud what happened. Then turn the wand over and touch its **S**
face to the same face and say what happened. Everyone watches both touches.

| N face of wand | S face of wand | the mouth face is |
|---|---|---|
| pushes away | pulls in | **N** |
| pulls in | pushes away | **S** |
| pulls in | pulls in | **steel** |
| nothing | nothing | **bare** |

The result is public and binding. Write nothing down; the table remembers.

You may probe the same mouth as often as you like across the game, and probing
does not move any tile. If the rail is empty, or the mouth slot you named is
empty, you may not probe that mouth — choose the other one or take a Push.

**The probe wand may not touch the rail at any other time.** It is the only
thing besides a pushed tile that is allowed to come near a tile in the rail.

---

## 6. End & winning

The game ends the moment the **last player's rack is empty**. Finish resolving
that final push completely — launches, captures and all — and then stop.
Whatever is still sitting in the rail stays there.

The end is reachable and the count is fixed: every Push spends exactly one tile
from a rack and no action ever returns a tile to a rack, so the game lasts
exactly as many Pushes as there are tiles in play — 24 at two players, 30 at
three, 36 at four — plus at most 3 Probes per player. No loop can extend it.

**Scoring.** Count the tiles in your score tray:

- Each tile **that is not your colour**: **1 point.**
- Each tile **of your own colour**: **0 points.** Getting your own tiles back
  is not an achievement.

Nothing else scores. Tiles left in the rail score for nobody.

**Worked scoring.** Four players. Orange's tray holds 9 tiles: 3 orange, 4 blue,
1 green, 1 purple. Orange scores **6**. Blue's tray holds 7 tiles: 0 blue, 5
green, 2 purple. Blue scores **7** and beats Orange, despite having captured
fewer tiles — Orange spent two of those detonations blowing up her own line.

**Most points wins.**

---

## 7. Tiebreak

Apply in order until exactly one player is left.

1. **Fewest tiles of your own colour still in the rail.** You left less on the
   table.
2. **Fewest tiles of your own colour in other players' score trays.** You fed
   the table less.
3. **Most probe chips unspent.** You read the rail with less help.
4. **Seating.** The tied player nearest to the start player's left, going
   clockwise from the start player, wins. This always resolves.

---

## 8. Edge cases

**Empty rail.** A Push into an empty rail slides all the way to the far mouth
slot and stops there. It does not fall out. There is no joint and nothing
resolves.

**Full rail.** The rail holds 10 tiles. If slot 1 is occupied when you push,
your tile drives the contiguous block ahead of it one slot and whatever is
shoved past slot 10 is yours. This is the only capture that does not need a
kick, and it is exactly one tile per welded body shoved out.

**A welded body shoved out.** If a clamped pair or longer chain is shoved or
launched past the far mouth, it leaves as one piece and every tile in it counts
separately for scoring. Break it apart in the tray at the end of the game.

**Two kicks at once.** Cannot happen. Joints are scanned in one order — from
the near mouth outward — and the first kick in that order is the only one that
fires. If a launch creates another kick joint, it waits.

**A kick joint that never fires.** Two like poles left resting against each
other stay live for the whole game. Any push that squeezes them from the near
mouth side will set them off, and everyone at the table saw where they are.

**A kick at the mouth joint.** The tile on the far side of the joint is the
whole line, so the whole line launches. If the rail was packed the whole line
leaves and you capture all of it. Your own tile stays in slot 1, alone.

**Nothing to capture.** Most pushes capture nothing. This is normal. The game
is won on three or four good detonations, not on a steady drip.

**Empty rack mid-round.** You are out immediately. You do not take a final
Probe with leftover chips, and leftover chips still count for tiebreak 3.

**Two players out, one left.** The last player keeps pushing alone until their
rack is empty. Their pushes still capture normally. If that looks like a
formality, it is not: a packed rail full of other people's tiles is worth a lot
to whoever gets the last four pushes, which is why hand sizes are equal.

**Probing an empty mouth.** Not allowed. See 5.2.

**A player who forgets what is in their own tile.** Their problem. The rack
troughs are the record and nobody else may look at them.

**Touching the rail out of turn.** Any tile you disturb in the rail on somebody
else's turn: put it back and, if it moved a full slot, the player whose turn it
is may take their turn back and choose again.

**Running out of probe chips.** You simply cannot Probe any more. You can
always still Push.

**A magnet that has lost its grip** and rattles in its pocket: swap the tile
for an unused one of your colour from the box and load it the same way, in
private, at the end of your turn.

**Exact-count ending.** The final push resolves in full: the shove, the
overflow out of the far mouth, and the kick and launch if there is one. Every
tile that leaves the rail during it belongs to the player who pushed. Score
after the rail has stopped moving, not before.
