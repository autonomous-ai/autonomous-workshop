# TOGGLE — The Hidden Detent

A hidden-state bluffing game for **2–4 players**. About **20 minutes**. **Ages 12+**.

---

## 1. Overview

Every player owns one **Toggle** — a single printed living-hinge lever that clicks
into either of two stable positions, **UP** or **DOWN**, and holds its state with a
spring. Nobody on the other side of the table can tell from looking whether your
lever is resting up or down; only your thumb feels the detent click. That hidden,
mechanical bit is the whole game. You claim the round's hidden truth, neighbour
sets their own toggle to trust you, and every turn ends the same way: somebody has
to *reveal*, and the printed detent tells the truth.

The game is Coup's trust-or-challenge in a physically real envelope: you can only
lie with the mechanism, and you can only be caught by the mechanism.

---

## 2. Components bill

Every component is a printed part unless the role says "purchased".

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `toggle_01`–`toggle_04` | **Toggle** | 4 (1 per player) | 88 × 24 × 14 | **THE LOAD-BEARING PART.** A single uni-body piece: a 2.4 mm living-hinge film joins a 60 mm lever to a 28 mm base, with a printed detent hump under the fulcrum so the lever is bi-stable in **UP** and **DOWN**. The base's underside carries a printed `▲` pointer that points to a stamped **A** or **B**; the pointer is only readable from underneath, in your own palm. |
| `keystone_01` | Keystone | 1 | 42 × 24 × 16 | A printed living-hinge wedge with two faces, **A** and **B**, that settles in the cradle. Only one face shows at a time. |
| `cradle_01` | Cradle | 1 | 72 × 40 × 22 | A printed shell that holds the Keystone with a low wall so only the active player can peek the face. |
| `truth_card_01` | Truth card | 1 | 88 × 56 × 1.6 | The reference table printed on card: it shows `your toggle = ▲side / Keystone = ▲side` → **truthful** or **bluffing**, plus scoring. Public. |
| `suit_tile_01`–`suit_tile_06` | Suit tiles | 6 | 18 dia × 2.6 | Printed discs: **SUN · MOON · STAR · COG · ARROW · KEY**. The six suits of the round track. |
| `suit_board_01` | Suit board | 1 | 160 × 70 × 20 | A printed board with 6 wells for the suit tiles and a 6-space round track with a `△` start marker. |
| `role_card_01`–`role_card_06` | Role cards | 6 (1 per player) | 88 × 56 × 1.6 | Printed two-sided tiles, one per suit, that secretly name each player's scoring suit. |
| `point_01`–`point_24` | Point tokens | 24 (12 × 2 colours) | 14 dia × 2.2 | Printed discs used for the pot and scores. |
| `pawn_01` | Round marker | 1 | 20 × 12 × 24 | A printed pawn that marks the current round on the track. |

**Total printed parts:** 7 types, **44 discs/tokens** in the kit. Prints on a 256 mm bed;
the Toggle at 88 mm and the Suit board at 160 mm are the only long parts.

---

## 3. Setup

1. Put the **Suit board** in the centre with all 6 **suit tiles** in their wells and the
   **pawn** on round 1. Put the **Cradle** with the **Keystone** beside it, and the
   **Truth card** open where everyone can read it.
2. Shuffle the **6 role cards**, deal one face-down to each player, and return the rest
   to the box unseen. Your role is secret. It names the one suit you'd like the round's
   truth to be — a tie-break and a hint, not the game itself.
3. Each player takes one **Toggle** and lays it flat in front of them, `.b-side` down so
   the pointer is hidden underhand. Put the **point tokens** in a pool.
4. The eldest player is the first **Forger**.

---

## 4. The hidden truth (each round)

Each round has one hidden truth: **A** or **B**, alive in two places at once —

* the **Keystone** in the cradle is showing face **A** or **B** (nobody may peek it but
  whoever does, and only one player at a time);
* each **Toggle**, in its owner's hands, is set to **A** or **B** by which way the lever
  is flicked.

A player is **truthful** this round if the side their Toggle is set to **equals the
Keystone's showing face**. Otherwise they are **bluffing**.

The Keystone face is the *shared* truth; your Toggle is the *private* claim that it
matches it. You never change the Keystone — you only decide, privately, whether your
Toggle will claim to match it or not.

---

## 5. Playing a round

**The Forger** is the eldest player in round 1. After that the Forger seat rotates
**one place clockwise every round**, no matter who scored — so across a full game every
player Forges the same number of rounds and the hidden-information edge spreads evenly
around the table (no one seat gets the bite of the bluff twice in a row). Everyone
therefore always knows whose Forge it is.

1. **Seal.** The Forger gives the Keystone a shake in its cradle so neither face is
   readable, then privately peeks the showing face and sets it down. They now know the
   round's truth: **A** or **B**. Only the Forger knows it.
2. **Choose (secret).** The Forger decides, privately, whether to play the round **true**
   or **bluff**, and sets their own Toggle to match that choice — flick it to the true
   side to play true, or to the opposite side to bluff. Nobody across the table can read
   which way the lever sits; that hidden detent is the whole game.
3. **Claim.** The Forger announces one side, **"A"** or **"B"**, as their claimed truth
   (a truthful Forger names the true side; a bluffing Forger names the other). Going
   clockwise from the Forger, each remaining player in turn either **trusts** or
   **challenges**:
   - **Trust.** Set your Toggle to the side the Forger just claimed, without peeking the
     Keystone. Say "trusted".
   - **Challenge.** Say "I call it". The Forger reveals their Toggle (upends it in the
     open). Resolve per §6 and end the round.
4. The round ends when a Challenge is resolved, **or** when every other player has
   trusted. If nobody challenged, the round banks (§6).

There is no talking after a reveal: the mechanism either matched the Keystone or it did
not, and everyone sees the pointer before the round is cleared.

---

## 6. Resolution & scoring

When a player is revealed, compare their Toggle's side to the Keystone's face (the
Forger finally shows it to everyone).

* **The challenger was right** — the Forger was bluffing (their revealed Toggle did not
  match the Keystone). The challenger takes the whole **pot**.
* **The challenger was wrong** — the Forger was truthful (their revealed Toggle matched
  the Keystone). The challenger pays one point token to the Forger, and the pot stays
  banked. A challenge is only available to a player who holds at least one point
  token; a token-less player must trust or pass. There is never a debt a player
  cannot pay.
* **Nobody challenged** — the round banks, and what it pays depends on whether the
  Forger was truthful:
  - **Forger truthful** — the Forger set their Toggle to match the Keystone, so every
    player who trusted (also set to that side) matches too: **each truster scores 1**,
    and the pot **banks** (grows +2 onto the next round). Playing true is the safe,
    reliable play.
  - **Forger bluffing** — the Forger claimed the wrong side and *nobody dared call it*.
    Their Toggle is the wrong way for everyone, so **no truster scores**; instead the
    Forger's risk pays: **the Forger takes the whole pot** and a fresh pot of 2 starts
    the next round. An uncalled bluff is the only way to win the pot outright.

The **pot** starts at 2 points in round 1 and grows by 2 each round it banks
unchallenged. A **successful challenge** (the Forger was bluffing) or an **uncalled
bluff** empties the pot to its winner; a **final bank** empties the surviving pot to the
game winner as a bonus. So the Forger weighs the safe +1-per-trust bank against risking
the whole pot on being believed — the bluff is only worth it when the pot is big enough
and the table reads as unlikely to call.

**Winning:** after 6 rounds the player with the most point tokens wins. Ties break by,
in order: (1) **most pot-wins** — the rounds in which you personally took the whole pot;
(2) **most successful challenges** (correct calls); (3) **eldest player**. Every breaker
is a number anyone can count on the table, so a tie never hangs on a hidden card.

---

## 7. Why the detent makes it a game

The bluff lives entirely in the mechanism. You cannot look at a Toggle and read its
state across the table, but *you* always know yours — so trust is a real decision you
can make with your thumb, and a reveal is a real, physical act. The printed living-hinge
detent is not decoration: it is the only source of hidden information in the game, and
it is exactly the part that only 3D printing can make as one toleranced, spring-loaded
piece.

---

## 8. Print & play notes

* Print the Toggle with a 0.3 mm layer height; the 2.4 mm hinge film bridges cleanly on
  a 0.4 mm nozzle and flexes for tens of thousands of cycles. Use PETG or PLA.
* Orient the Toggle with the hinge film vertical (build the lever pointing up) so no
  support touches the film. The detent hump is a 0.8 mm bump under the fulcrum; a tight
  first layer makes the click satisfying.
* The Keystone's hinge is the same recipe in miniature. Slide-fit the two halves on the
  printed nubs — no glue.
