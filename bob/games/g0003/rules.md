# CLEARANCE

*A limbo contest for solid objects. 2–4 players, 14+, 20–35 minutes (typically 25). About 5 minutes to teach.*

---

## 1. Overview

A printed gantry stands in the middle of the table with a loose rod resting across it — the **bar**. Every round the player who is losing screws the bar down by a secret amount, and then everybody, at the same instant, commits one block from their own stock to pass under it. Blocks are unmarked and no two are the same height; the tallest block that gets through without touching the bar wins the round, and a block that touches is thrown out of the game for good. Your score is a line of the blocks you have won, laid end to end on the table — the longest line at the end wins, so a win with a tall block is worth more than a win with a stub.

The whole game is two physical questions asked over and over: *how tall is that gap, really,* and *how tall is my third-best block, really.* Neither has a number on it. The one convention you already know is trick-taking: everyone commits in secret, all reveal together, highest takes the round.

---

## 2. Components bill

Every component is a printed physical object. Nothing is a card, a chit, or an abstraction.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `column_screw` | **Detent screw** ⭐ | 1 | ⌀16 × 118 (2.0 mm pitch thread; ⌀44 × 14 knob integral at top; detent crown of 4 ramped notches on the collar at its base) | **THE LOAD-BEARING MECHANISM.** One quarter-turn = one *click* = exactly 0.5 mm of bar travel, felt and heard but not seen. The whole game is that a click is a countable, repeatable, invisible unit of height. |
| `detent_leaf` | Detent leaf spring | 1 | 34 × 12 × 4 | Printed cantilever with a rounded nub; snaps into `gantry_base` and rides the screw's detent crown. Replaceable so the click can be re-tuned by reprinting one small part. |
| `gantry_base` | Gantry base | 1 | 220 × 110 × 12 | Flat top face is the **runway** — the datum every bar height is measured from. Carries both post sockets, the detent leaf socket, a scrap well at the rear, and the setter's ritual reminder embossed on the front skirt. |
| `post_guide` | Guide post | 1 | ⌀12 × 112 | Smooth post opposite the screw. Stops the yoke from rotating so turning the knob raises and lowers it. |
| `yoke` | Bar yoke | 1 | 170 × 24 × 16 (bridge), with two end brackets that drop to bar height | Rides the screw. The bridge sits high, clear of the lane; the two end brackets carry the V-saddles that the bar rests in, leaving a **130 mm clear lane** with nothing in it but the bar. |
| `bar_rod` | The bar | 1 | ⌀8 × 158 (hollow, ≤6 g) | Lies loose in the two saddles. It is not fastened. If a block touches it, it rocks or rolls visibly — that is the bust detector, and it needs no judge. |
| `knob_hood` | Knob hood | 1 | ⌀78 × 66, with a 60 × 45 hand port on one side | Drops over the knob so the setter's hand and wrist work out of sight. Hides the *direction* of every turn. |
| `rail_01`–`rail_04` | Stock rail | 4 | 178 × 32 × 12, six 21 × 21 × 4 pockets on 28 mm centres | One per player. Holds your six blocks standing up, in the open, in whatever order you like. Its front edge is the straightedge you lay your score line against. |
| `cup_01`–`cup_04` | Commit cup | 4 | 30 × 30 × 44 (walls 2.5) | One per player. Opaque. Your committed block goes under it, and all four lift together at the reveal. |
| `piece_a1`–`e6` | Stock block | 30 | 20 × 20 × H, where H is that block's own height | Five sets of six (`a`…`e`), each set marked with its own embossed symbol on a **side** face — circle, square, triangle, cross, bar. Top and bottom faces are flat, bare and parallel: they are what the bar judges. |

**Block heights.** `H` is drawn from a 42-rung ladder: 12.25, 12.75, 13.25 … 32.75 mm, in 0.5 mm steps. Each set of six is drawn at random *without replacement within the set*; different sets are drawn independently and may share heights. Each set must contain at least one block above 28 mm and at least one below 17 mm, and no two blocks within a set may be closer than 1.0 mm.

Three rules for whoever prints this:
- **No height is ever printed, stamped, or engraved on a block.** The moment a group can read the numbers, the game is arithmetic.
- **Every copy gets a fresh random draw.** A fixed set of thirty heights gets written down once and the estimate is dead.
- Height tolerance ±0.05 mm, measured flat face to flat face. Bar heights sit on the 0.5 mm grid; block heights sit on that grid **plus 0.25 mm**, so a block is never exactly level with the bar — the smallest possible margin, either way, is 0.25 mm.

Everything prints on a 256 mm bed. Total: 44 parts, roughly 350 g of filament.

---

## 3. Setup

1. Put the **gantry base** in the middle of the table, long edge facing the players, with room in front of it for four score lines to lie side by side.
2. Fit the **guide post**, the **detent leaf**, and the **detent screw** into the base. Hang the **yoke** on both posts and lay the **bar** loose in its two saddles. Never fasten the bar.
3. **Turn the knob up until the screw stops.** That hard top stop is the starting gap: 33.0 mm, just above the tallest block that can exist. Do not count anything; the stop does it for you. The bottom stop, 31 clicks below, is 17.5 mm.
4. Give each player a **stock rail** and a **commit cup**.
5. The **first setter** is the player who most recently used a ruler or tape measure for real. If nobody remembers, the youngest player.
6. Starting with the player to the first setter's left and going clockwise, each player picks one **set** of six blocks and stands it in their rail. The first setter picks last. Unused sets go back in the box.
7. You may pick up, stand together and compare **your own** blocks whenever you like, all game. You may **never** touch another player's blocks, and you may never hold any block against the gantry.
8. The first setter takes the **knob hood**. Play begins.

---

## 4. Turn structure

There are no individual turns. The game is a series of **rounds**, and every round has the same five steps in this order. Each step finishes for everybody before the next one starts.

1. **The Set** — the setter alone lowers the bar.
2. **The Commit** — all players at once, mandatory.
3. **The Reveal** — all cups lift together.
4. **The Pass** — blocks slide one at a time, in order.
5. **The Take** — the round is scored, and a player with an empty rail may salvage.

**Who is the setter.** At the start of every round the setter is the player with the **shortest score line** — the one who is losing. If two or more are tied for shortest, the setter is whichever of them has been setter the fewest times this game; if still tied, the first of them going clockwise from the previous setter's left. In round 1 it is the first setter chosen at setup.

**Order of play within a round** — for The Pass — is by score line, **shortest first, longest last**, using the same tiebreakers. The setter always slides first. The leader always slides last, which is where the noise comes from.

---

## 5. Actions

### 5.1 The Set (setter only, mandatory)

The setter drops the knob hood over the knob, puts a hand in through the port, and turns **eight clicks in total**:

> **Down 5, then up 3.** &nbsp;·&nbsp; **Down 6, then up 2.** &nbsp;·&nbsp; **Down 7, then up 1.**

The bar therefore ends **2, 4, or 6 clicks lower** than it started — 1.0, 2.0, or 3.0 mm. Which of the three is the setter's private information, and the only private information in the game. Everyone else hears eight clicks and can see the gap; nobody else knows where in those eight the turn reversed.

- Turn at a steady rate. Do not pause at the reversal. You may pause anywhere else.
- The hood comes off the moment the eight clicks are done, and nobody touches the knob again until the next Set.
- The bar never goes up on balance and never goes above where it started, so the top stop can never be hit during a Set.
- **If the screw hits the bottom stop during the Set**, the setter stops immediately, leaves the bar sitting on the stop, lifts the hood and says **"Bottom."** The bar stays at 17.5 mm for this round, and **this round is the last round of the game.**
- Anyone may check a "Bottom" call after the round by trying to turn the knob down. If it turns, the call was false and the caller loses their whole score line.
- **If the setter loses count or the screw jams**, they say so and start a fresh eight-click Set from wherever the bar now stands. They still know the total drop; the table still does not.

### 5.2 The Commit (all players, mandatory, simultaneous)

Every player with at least one block in their rail **must** commit exactly one.

Hold your cup above your rail. Somebody counts *three, two, one, commit* — and on "commit" every player, at the same instant, takes one block from their rail and puts it on the table under their cup. Watch your own rail while you do it.

- Once your cup is down, your choice is final.
- The empty pocket in your rail is public. Everyone can see **which** block you took. Nobody knows **how tall** it is.
- If anyone thinks the commits were not simultaneous, every player lifts their cup, returns their block to the rail, and the count is run again.
- **If you expose your block early**, you must put it back and commit the shortest block remaining in your rail instead.

### 5.3 The Reveal

On a count of three, all cups lift together. The committed blocks stand in the open in front of their owners. Look, compare, judge the gap, and suffer. No decisions are made here — everyone is already committed.

### 5.4 The Pass (one block at a time, in play order)

Stand your block flat on the runway in front of the gantry and push it, with one finger, in one direction, straight through the lane and out the far side.

- **No lifting, no tilting, no rocking, no spinning.** The block stays flat on the runway the whole way.
- You may stop and keep pushing, as long as you keep going the same way. You may not pull it back out.
- Slowly is fine. There is no speed rule.

**Outcomes.**

- **Clears** — the block passes fully out the far side and **the bar does not move.** Set it in front of you; it is still in the running for the round.
- **Scrapped** — the bar rocks, rolls, lifts or falls at any moment during the pass. The block is out of the game permanently and goes in the scrap well at the back of the base. Replace the bar in its saddles.
- **Failed execution.** If you lift, tilt, rock or reverse the block: **scrapped**, exactly as if it had touched. If you push it into a bracket or off the side of the runway without touching the bar, no harm — put it back at the start and push again.
- **Gantry knocked.** If the gantry itself is shoved or slides, that block is **scrapped**. Slide the gantry back into place; the bar height is unchanged, because the screw holds its setting.
- **Outside interference.** If the bar is disturbed by a bump, a sneeze, or a sleeve while no block is under it, replace the bar and carry on. Nothing is scrapped.

### 5.5 Comparing two blocks (the fingernail test)

The game turns on 0.5 mm differences, so here is the ruling, and it is the only ruling: **stand the two blocks touching, side by side, on a flat surface, and drag a fingernail across the joint.** The step tells you which is taller. If the table genuinely cannot feel a step, the two blocks are **tied**.

You may use this on **your own stock at any time**, and on **revealed blocks after a Reveal**. Never on another player's rail.

### 5.6 The Take (scoring the round)

Among the blocks that **cleared**, the **tallest** wins the round. Use the fingernail test if it is close.

The winner takes, into their score line:

1. their own winning block, **and**
2. the **tallest block that was scrapped this round**, if any block was scrapped.

All other scrapped blocks stay in the scrap well, out of the game. Every block that cleared but did not win goes back into its owner's rail, at no cost.

Lay your score line on the table in front of you: blocks on their sides, butted end to end in one straight run, the first one flush against the front edge of your rail. The line is your score. It is always public.

- **If two or more clearing blocks tie for tallest**, all of the tied blocks are scrapped, nobody wins the round, and nobody takes anything — including the scrapped blocks.
- **If nothing clears**, nobody wins the round and every block that was passed is scrapped.

### 5.7 Salvage (optional, only with an empty rail)

If your rail is empty at the end of The Take and the game is not over, you may **take the shortest block out of your own score line and put it back in your rail.** That block is yours to play again; your line gets shorter by exactly that much.

You may decline and simply sit out the remaining rounds with your line intact — sometimes that is the right call. If your rail *and* your line are both empty, you are out of the game and cannot score again.

---

## 6. End & winning

**The game ends at the end of the round in which the setter says "Bottom"** — the round played with the bar sitting on its bottom stop at 17.5 mm.

That ending is reachable and forced. The bar starts 31 clicks above the bottom stop and every single Set moves it 2, 4, or 6 clicks down; it never moves up on balance. Even if every setter for the whole game chooses the smallest drop, the bar is on the stop within 15 rounds; at the most common drop it is 8 or 9 rounds; at the largest, 6. There is no way to stall, because The Set is mandatory and always descends.

The Bottom round is worth playing hard: with the bar at 17.5 mm, only your stubbiest blocks get through, most of the table gets scrapped, and the winner sweeps the tallest wreck into their line on top of their own win.

**The winner is the player with the longest score line.**

To compare at the end: lift each line off the table, lay the lines directly against one another, side by side and touching, all flush at one end. Look at the far ends. If two lines are too close to call by eye, fingernail-test the far ends.

**Worked scoring example.** Players never see these numbers — this is only to show that the aggregation is a plain sum of heights, not a count of wins.

| | wins taken (mm) | line |
|---|---|---|
| Ana | 31.75 + 24.25 + 16.75 | 72.75 mm, 3 blocks |
| Ben | 30.25 + 29.75 | 60.00 mm, 2 blocks |
| Cal | 26.75 + 22.25 + 18.75 + 13.25 | 81.00 mm, 4 blocks |

Cal wins with four modest wins over Ben's two big ones. Note what the aggregation does to play: a round won with a 30 mm block is worth two rounds won with a 15 mm stub, so a player who plays safe every round grinds forward slowly and a player who plays tall wins hard or feeds the leader a scrapped monster. That trade is the game.

---

## 7. Tiebreak

If two or more lines cannot be separated, in order until one player remains:

1. **Fewer blocks in the score line.** Same length off fewer wins is better play.
2. **More blocks remaining in the rail.** You wasted less.
3. **Fewer times as setter.** You spent less of the game losing.
4. **Closest going clockwise from the last setter, starting with the last setter.** Seats are distinct, so this always resolves.

There is no shared victory. This game is not cooperative.

---

## 8. Edge cases

**A player has exactly one block left.** They must commit it. If it is scrapped, their rail is empty and they may Salvage at the end of The Take.

**A player's rail and line are both empty.** They are out. They stop committing, they cannot win, and they are skipped for setter and for play order. The game still runs to the Bottom round.

**Everyone's rail is empty, or only one player can still commit.** Play the round anyway with whoever can commit; a single committed block that clears wins the round. The game still ends only at Bottom.

**The setter's rail is empty and they decline Salvage.** They still Set. Setting is a duty of last place, not a privilege of playing.

**Two players tie for shortest line at the start of a round.** Setter tiebreakers in §4, in order. They always resolve.

**A block clears but the bar rocks a second later.** If the block was fully out of the lane and no longer touching anything when the bar moved, it clears. If there is any doubt, it is scrapped — the bar gets the benefit.

**Two players call contact differently.** They cannot: the bar is loose. Either it moved or it did not. If it is genuinely unclear because someone bumped the table at the same moment, replace the bar and slide that block again; the second slide is final.

**The bar rolls out of a saddle while nothing is under it.** Replace it. Nothing is scrapped, the setting is unchanged.

**Two clearing blocks tie for tallest and a third block cleared shorter.** The tied blocks are scrapped, nobody wins, and the shorter clearing block goes back to its owner's rail untouched. Third place does not inherit the round.

**Every block is scrapped and the round produced no winner.** No line grows. The scrapped blocks are gone. Play continues to the next round.

**Two blocks tie for tallest among the scrapped.** The round's winner picks either one; the other stays in the scrap well.

**The winner's own block was the only one scrapped.** Impossible — a scrapped block cannot win. If the winner's block cleared and every other block was scrapped, they take their own block plus the tallest scrapped block, which is somebody else's.

**A player claims "Bottom" and the knob still turns down.** The call was false. That player's entire score line is scrapped and the game continues from the bar's actual position. Do not argue about intent; check the knob.

**The screw hits the bottom stop on the very first click of a Set.** Same ruling: bar stays on the stop, say "Bottom," this is the last round.

**Somebody counts the clicks.** Let them. Eight clicks is eight clicks whichever way the setter chose; the count carries no information. What they *can* do is look hard at the gap and judge whether it dropped one millimetre or three. That is the intended skill, and it is a fair fight.

**A player writes down what cleared and what got scrapped.** Allowed, and encouraged. The bar never goes back up, so a block that cleared at a given gap will clear anything above it, and a block that was scrapped is gone anyway. Memory is part of the game; secret notes are not — keep any notes face up.

**A block will not stand up on the runway.** Check the bottom face for a print blob and scrape it flat. A block that cannot stand square is out of tolerance and should be reprinted before play, not ruled on mid-game.
