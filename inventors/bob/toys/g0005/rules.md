# KICK

A pushing game for 2–4 players. About 20 minutes. Ages 14+.

---

## 1. Overview

Kick is an abstract pushing game played on one printed rail. Every tile you own
carries a small metal disc buried in one end. Only you know which of three discs
is in there: a magnet with its **north** pole facing out, a magnet with its
**south** pole facing out, or a plain steel slug that is not magnetised at all.
The three discs look identical, weigh the same, and are sealed in the tile.

On your turn you slide one tile into an open end of the rail and drive it home.
In the last few millimetres you feel what is coming before anybody else does,
and then it happens out loud. Two like poles meeting is a **kick**: they blow
apart and throw every tile past the break out of the far end of the rail and
into your tray. Opposite poles, or a magnet meeting steel, **clamp**: the two
tiles weld together and that joint is dead forever. A bare plastic end meeting
anything does nothing at all — which is why a steel tile is the bluff. It looks
like a loaded gun and it can never fire.

Tiles you throw out of the rail are your score, but **only tiles that are not
your own colour**. The fat, tempting line is worth detonating only when it is
fat with somebody else's tiles. The game ends when the first player runs out of
tiles; most points wins.

---

## 2. Components bill

Every component is a printed part unless the role says "purchased".

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `rail_01` | Rail | 1 | 240 × 30 × 16 | The board. A straight channel 240 × 18.4 × 10.4 mm, open at both ends, clearance 0.3–0.4 mm on every face so a tile slides freely. The channel floor carries **10 seating scallops** 0.4 mm deep at 24 mm pitch; a sliding tile rides over them and settles into one when it stops. These are the **slots**, numbered 1–10 on both top edges. A tile is always in exactly one slot, never between two. |
| `tile_01`–`tile_48` | **Pole tile** | 48 (12 per player) | 23 × 18 × 10 | **THE LOAD-BEARING PART.** A blind pocket ⌀6.15 × 3.5 mm is sunk in the centre of ONE end face, loaded through a ⌀6.4 snap port in the bottom face; the disc sits 0.5 mm below the end surface and is held by friction and two 0.25 mm barbs, no glue. That end is the **head**, marked by a printed notch on the top face. The other end is the **tail**: bare plastic. The top face also carries the owner's colour and a number 1–12. |
| `magnet_01`–`magnet_32` | N42 disc magnet | 32 (8 per player) | ⌀6 × 3 | Purchased. Nickel-plated neodymium. Goes in a tile's head pocket either way round. Mass 0.64 g. Two of these head to head through 1.0 mm of plastic each pull or push with about 0.6 N — sixty times the friction on a 5.6 g tile, so the rail is never in doubt. |
| `slug_01`–`slug_16` | Steel slug | 16 (4 per player) | ⌀6 × 3 | Purchased. Plain mild steel, not magnetised. Same plating, mass 0.67 g — indistinguishable from a magnet by eye or by hand. |
| `rack_01`–`rack_04` | Player rack | 4 (1 per player) | 96 × 86 × 22 | Three labelled troughs that hold tiles standing on edge: **N** (8 slots), **S** (8 slots), **STEEL** (4 slots). The rack is your memory — a tile's trough tells you what is inside it. |
| `screen_01`–`screen_04` | Screen | 4 (1 per player) | 150 × 80 × 24 | L-profile: a 2.4 mm panel on a 150 × 24 mm foot. Hides your rack. |
| `tray_01`–`tray_04` | Score tray | 4 (1 per player) | 90 × 70 × 22 | Open well. Holds captured tiles. Contents are public at all times. |
| `catch_01`–`catch_02` | Catch tray | 2 | 96 × 60 × 18 | Clips onto an end of the rail. Its floor sits 1 mm below the channel floor, so a tile leaving the rail drops in and stays. |
| `pin_01`–`pin_04` | Load pin | 4 (1 per player) | ⌀5 × 60 | Pushes a disc out of a tile through the snap port during setup. Not used once play starts. |
| `chip_01`–`chip_12` | Probe chip | 12 (3 per player) | ⌀16 × 3 | Spent to take the Probe action. Public. |
| `card_01`–`card_04` | Joint card | 4 (1 per player) | 88 × 56 × 1.6 | The joint table from section 5, printed. Public reference. |

Ten tiles at 23 mm fill 230 mm of the 240 mm channel, so a full rail still has
10 mm to shove into. Everything prints on a 256 mm bed; the rail at 240 mm is
the only long part.

---

## 3. Setup

1. Clip a **catch tray** to each end of the rail. Put the rail in the middle of
   the table, long axis across the table, so both ends are reachable by
   everyone. The rail starts empty.
2. Each player takes one colour: 12 pole tiles, 8 magnets, 4 steel slugs, a
   rack, a screen, a score tray, a load pin, 3 probe chips, and a joint card.
   Stand your screen up. Everything behind it is private except your score
   tray, which sits in front of the screen with its contents face up, and your
   probe chips, which sit in front of the screen too.
3. **Hand size and disc mix, by player count.** This is public — everybody
   knows exactly how many steel tiles everybody else is holding.

   | players | tiles each | magnets | steel |
   |---|---|---|---|
   | 2 | 12 | 8 | 4 |
   | 3 | 10 | 7 | 3 |
   | 4 | 9 | 6 | 3 |

   Return your unused tiles and discs to the box before loading.
4. **Load your tiles, behind your screen.** Press one disc into the head pocket
   of every tile in your hand, one disc per tile, using exactly the mix in the
   table. For each magnet you choose which pole faces out; you may split your
   magnets between N and S however you like, including all of them one way.
5. **Sort your rack.** Stand each loaded tile in the trough that matches what
   you put in it: **N**, **S**, or **STEEL**. From here on the rack is your
   only record. Nobody else may look at it, and you may look at it whenever you
   like.
6. **Start player.** The youngest player goes first. Play proceeds clockwise.

---

## 4. Turn structure

There are no phases. On your turn you take exactly one action:

- **Push** (section 5.1), or
- **Probe** (section 5.2).

Then your turn ends and the player on your left takes a turn.

You must take an action. You may always Push while you have a tile in your
rack, so you can never be stuck. If your rack is empty you may only Probe, and
if you have no chips either you pass.

**The game ends at the end of the round in which any player's rack goes empty**
— see section 6. Everybody gets the same number of turns, so spending turns on
Probes costs you pushes you will never get back.

---

## 5. Actions

### The three kinds of joint

Whenever two tiles touch inside the rail, the two faces that touch make a
**joint**. There are exactly three kinds, and the discs decide which — always,
immediately, and without anybody's opinion.

|  | N face | S face | steel face | bare face |
|---|---|---|---|---|
| **N face** | **KICK** | CLAMP | CLAMP | slack |
| **S face** | CLAMP | **KICK** | CLAMP | slack |
| **steel face** | CLAMP | CLAMP | slack | slack |
| **bare face** | slack | slack | slack | slack |

- **KICK** — two like poles meet. They fly apart. This is the only thing that
  captures tiles by force.
- **CLAMP** — the two tiles snap together, loudly. They are now **welded**:
  they move as one body for the rest of the game, they leave the rail as one
  body, and that joint can never kick.
- **slack** — the faces touch and nothing happens.

**Only touching faces matter.** A disc has no effect on anything it is not
directly against. A magnet head one tile away, or across a gap, does nothing.

A joint's kind is public the moment it forms. Everyone hears a clamp and
everyone sees a kick. There is nothing to argue about and no reveal.

### 5.1 Push

**Cost:** one tile from your rack. The tile is spent whatever happens, and it
stays in the rail.

**Procedure.**

1. Announce which end of the rail you are pushing into. That is the **near
   mouth**; the other end is the **far mouth**. For this turn only, slot 1 is
   the slot at the near mouth and slot 10 is the slot at the far mouth.
   Everything below is written from the near mouth outward.
2. Take a tile from behind your screen. Choose which end goes in first: **head
   first** (disc leading, into the rail) or **tail first** (bare end leading,
   which leaves your disc facing out of the mouth). Everyone can see which you
   chose, because the head is notched.
3. **Commitment.** Once the tile crosses the mouth of the rail you must
   complete this push, with this tile, in this orientation, into this end. You
   may not hover a tile near the rail to feel what is inside it. If you bring a
   tile within a hand's width of the rail outside of a Probe, it is committed.
4. **Drive it home with one finger.** Force changes nothing here; shoving
   harder cannot change any outcome. Two cases:
   - **Slot 1 is empty.** Your tile slides in until it touches the first tile
     it meets, and stops in the slot next to it. Nothing else in the rail
     moves. If the rail is completely empty, drive your tile all the way to
     slot 10 and leave it there.
   - **Slot 1 is occupied.** There is no room, so your tile drives what is in
     front of it. Shift the tile in slot 1, and every tile in unbroken contact
     with it, one slot toward the far mouth. Tiles beyond a gap do not move.
     Any tile shoved past slot 10 leaves the rail, drops into the catch tray,
     and goes to **your** score tray. Your tile takes slot 1.
5. **Resolve.** Scan every joint in the rail, starting at the near mouth and
   moving outward, and find the **first KICK**.
   - **No kick:** the push is over. Any new clamp welds; any new slack joint
     does nothing.
   - **A kick:** it fires. The tile on the far side of that joint, and every
     tile in unbroken contact with it, is **launched**. The launched body
     slides toward the far mouth until its leading tile either leaves the rail
     or comes to rest in the slot next to the next tile. Every tile that leaves
     the rail goes to **your** score tray, however many that is. Nothing on the
     near side of the kick moves, including your own tile.
   - **Only one kick fires per push.** If the launch presses two like poles
     together, that joint does not fire now. It sits there live, everybody saw
     it, and the next push that squeezes it from the near side will set it off.

**Worked push.** Reading the rail from the left mouth: slot 1 empty; slot 2 an
orange tile with its **head facing left**; slot 3 a blue tile with its **head
facing right** (so the joint between them is tail against tail — slack); slot 4
empty; slots 5–7 a welded green body; slots 8–10 empty. You push from the left,
head first, with an **N** tile.

Slot 1 is empty, so your tile slides in and stops in slot 1 against orange in
slot 2. Nothing else moves. Scanning outward, the first joint is your **N** head
against orange's head. Orange is **N** as well — KICK. Orange is in unbroken
contact with blue, so both are launched to the right. They slide until blue
reaches the slot next to the green body: blue stops in slot 4, orange in slot 3.
Nothing left the rail, so you capture nothing — but you have shunted two tiles
onto the green body, and blue's **head** now sits against green's slot-5 face as
a live joint that the next push from the left will squeeze. Your own tile sits
alone in slot 1 with a gap in slot 2.

Had the green body not been there, orange and blue would have slid the length of
the rail and dropped out the far mouth into your tray: two tiles, and if either
of them was not your colour it was worth a point.

**Physical rulings.**

- **A tile that will not go in.** If the channel is blocked because a tile sits
  crooked, straighten it with a finger first, then push. This is maintenance,
  not a move.
- **A tile that jumps out of the rail sideways, or off the table.** It has left
  the rail. It goes to the score tray of the player whose push moved it.
- **A launched body that stalls short of the mouth.** If a body was launched at
  the far mouth and stops with a tile hanging over the lip, slide it out with
  one finger. The physics decides *where the line breaks*, not how far anything
  travels; the finger only finishes the delivery.
- **A welded body over the lip.** A welded body leaves the rail whole as soon as
  any part of it clears the far mouth. Both tiles score separately.
- **A disc that falls out of its pocket.** Press it back in the same way round,
  in private. If nobody can say which way round it was, its owner decides, in
  private, and play continues.
- **A clamped pair pulled apart by mishandling:** put it back together. It is
  still one welded body.
- **You may never re-load a tile once setup is finished.** The discs stay where
  you put them for the whole game.

### 5.2 Probe

**Cost:** one probe chip. Return it to the box; it is gone. Probing is your
whole turn.

**Procedure.** Name one mouth of the rail. Take **one or two tiles from your own
rack** and touch each one, head first, against the outward-facing end face of
the tile sitting in that mouth slot. Bring each tile up slowly and take it back;
do not release it. Then return your tiles to your rack. They are not spent.

You say nothing. The table watches each touch and sees it **pull**, **push**, or
**do nothing** — but nobody except you knows which tiles you used, so nobody
except you can turn that into an answer. Here is your answer key:

| you touched with | it pulled | it pushed | nothing happened |
|---|---|---|---|
| an **N** head | face is **S** or **steel** | face is **N** | face is **bare** |
| an **S** head | face is **N** or **steel** | face is **S** | face is **bare** |
| a **steel** head | face is **N** or **S** | — | face is **bare** or **steel** |

One touch can leave you with two candidates; a second touch with a different
kind of tile always settles it. That is what the second tile is for.

If the mouth tile shifts under the probe, slide it back against its neighbour.
Nothing else changes and no joint resolves — a probe never makes a joint.

You may probe either mouth, as often as your chips allow. If the rail is empty,
or the mouth slot you named is empty, you may not probe there; probe the other
mouth or take a Push instead.

**Nothing may touch a tile in the rail at any other time**, except a tile you
are pushing and a finger doing the maintenance listed in 5.1.

---

## 6. End & winning

**The game ends at the end of the round in which any player's rack goes empty.**
Finish that round so every player has taken the same number of turns, resolve
the last push in full — shove, overflow, kick, launch and all — and then stop.
Whatever is still in the rail stays there.

The end is reachable and the count is fixed. Every Push spends exactly one tile,
every Probe spends exactly one chip, no action ever returns a tile to a rack,
and every player holds the same number of tiles. So the game runs for **at most
as many rounds as a starting hand has tiles**: 12 rounds at two players (24
pushes), 10 at three (30 pushes), 9 at four (36 pushes). Probes only make it
shorter for the prober. No loop can extend it.

**Scoring.** Count the tiles in your score tray:

- Each tile **that is not your colour**: **1 point.**
- Each tile **of your own colour**: **0 points.** Getting your own tiles back is
  not an achievement.

Nothing else scores. Tiles left in the rail and tiles left in a rack score for
nobody.

**Worked scoring.** Four players. Orange's tray holds 9 tiles: 3 orange, 4 blue,
1 green, 1 purple. Orange scores 4 + 1 + 1 = **6**. Blue's tray holds 7 tiles:
0 blue, 5 green, 2 purple. Blue scores 5 + 2 = **7**, and beats Orange despite
capturing two fewer tiles — Orange spent two detonations blowing up her own
line.

**Most points wins.**

---

## 7. Tiebreak

Apply in order until exactly one player is left.

1. **Fewest tiles of your own colour still in the rail.** You left less on the
   table.
2. **Fewest tiles of your own colour in other players' score trays.** You fed
   the table less.
3. **Most probe chips unspent.** You read the rail with less help.
4. **Seating.** Of the players still tied, the one who sits furthest clockwise
   from the start player wins. This always resolves, because no two players
   share a seat.

---

## 8. Edge cases

**Empty rail.** A Push into an empty rail slides all the way to slot 10 and
stops there. It does not fall out. There is no joint and nothing resolves.

**Full rail.** The rail holds 10 tiles. If slot 1 is occupied when you push,
your tile drives the contiguous run in front of it one slot toward the far
mouth, and whatever is shoved past slot 10 is yours. This is the only capture
that does not need a kick.

**Two kicks at once.** Cannot happen. Joints are scanned in one fixed order —
from the near mouth outward — and the first kick in that order is the only one
that fires. Anything the launch creates waits.

**A kick joint that never fires.** Two like poles left resting against each
other stay live for the whole game. Any push that squeezes them from the near
side sets them off, and everybody at the table saw where they are.

**A kick at the mouth joint on a packed rail.** Everything past slot 1 is one
unbroken run with nowhere to go, so the whole line launches out of the far mouth
and you take all of it. Your own tile sits alone in slot 1. This is the biggest
turn in the game and it needs both a packed rail and a correct read.

**A kick that captures nothing.** Common. If the launched body runs into another
tile it just shunts and no tile leaves the rail. You still spent your tile. Most
pushes capture nothing; the game is won on three or four good detonations.

**A launched body that is already at the far mouth.** It leaves the rail
entirely. Every tile in it is yours.

**Steel against steel.** Slack. Two unmagnetised slugs do nothing to each other.
A steel tile can never kick anything and can never be kicked at its head, which
is exactly why it is worth holding.

**Empty rack, round not finished.** You take no more Pushes. You may still Probe
if you have chips, or pass. The round finishes and the game ends.

**Two or more racks go empty in the same round.** Normal. The round finishes and
the game ends, exactly as if one had.

**Probing an empty mouth.** Not allowed. Choose the other mouth or Push. See
5.2.

**Running out of probe chips.** You simply cannot Probe any more. You can always
still Push.

**A player who forgets what is in their own tile.** Their problem. The rack
troughs are the record and nobody else may look at them.

**Touching the rail out of turn.** Put back whatever you disturbed. If a tile
moved a full slot, the player whose turn it is may take their turn back and
choose again.

**A disc that rattles loose in its pocket.** At the end of your turn, in
private, move that disc into an unused tile of your colour from the box and use
that tile instead. Load it the same way round.

**Exact-count ending.** The final push resolves in full: the shove, the overflow
out of the far mouth, and the kick and launch if there is one. Every tile that
leaves the rail during it belongs to the player who pushed. Score only after the
rail has stopped moving.
