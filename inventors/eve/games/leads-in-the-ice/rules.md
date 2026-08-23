# Leads in the Ice

**2–4 players · 15–25 minutes · ages 10+**

Pack ice is never still. It squeezes shut and it pulls apart, and the open channels
that appear between the floes are called *leads*. Seals live and die by them: a
lead that is wide enough to swim is not always wide enough to hold onto, and a
lead that shuts takes back whatever was in it.

The whole board is one printed sheet of floes that opens and closes **all at
once**. There is a single slider on the frame, shared by everyone. Move it one
notch and every hole on the board changes size on the same click — for you, for
your opponents, for pieces already in the water. Nobody owns the ice.

---

## 1. Components

| # | Part | Notes |
|---|------|-------|
| 1 | **Ice sheet** (printed in place, one piece) | 5×5 grid of square floes joined corner-to-corner by living hinges, inside a frame. Turning the floes opens 16 holes between them — the **nodes**. |
| 1 | **Aperture slider** | Runs in the frame rail with a two-way detent. Four stops, marked **0 · 1 · 2 · 3**. It clicks; the click is the move. |
| 16 | **Seal pegs** | 4 per player: **2 bulls** (thick) and **2 pups** (thin). Both are cones — a shrinking hole lifts them straight out. |
| 12 | **Floats** | 3 per player. A float has a springy collar that grips a node at any aperture. |

Player colours: white, slate, rust, moss.

### The ice sheet in one paragraph

The floes are hinged at their corners, so they cannot move alone. Push the
slider and all 25 floes rotate together, the sheet grows in both directions at
the same time, and 16 diamond-shaped holes open between them. Pull the slider
back and every hole shrinks together. The corners around each node are chamfered
by different amounts, so the holes do **not** all open the same. Each node
carries a printed threshold, **1**, **2** or **3**, moulded into the ice around
it and also stamped on the frame margin.

### Node map

Columns **A–D** left to right, rows **1–4** top to bottom. The number is the
node's threshold.

```
      A     B     C     D
1     2     1     3     2
2     3     2     2     1
3     1     2     2     3
4     2     3     1     2
```

The map is the same after any quarter turn, so every edge of the board is worth
exactly the same: each edge holds one **1**, two **2**s and one **3**.

---

## 2. What "open" means

Read this once and the whole game follows from it.

Let **A** be the current aperture (0, 1, 2 or 3) and **t** be a node's threshold.

- A node is open to a **pup** when **A ≥ t**.
- A node is open to a **bull** when **A ≥ t + 1**.
- A node is **tight** for a pup when **A = t** exactly — the pup fits, and the ice
  has it by the shoulders. This is the only state in which a pup can plant.
- A **bull can never enter a threshold-3 node.** There is no aperture 4.
- At **A = 0** no node is open to anything.

You never have to remember this. Try the peg in the hole. If it drops to its
collar, it is in; if it stands proud, it is not.

Nodes hold **one piece only** — one peg or one float.

---

## 3. Setup

1. Seat players on different edges of the frame.
   - **2 players:** opposite edges (North = row 1, South = row 4).
   - **3 players:** North, East (column D), South.
   - **4 players:** all four edges. West is column A.
2. Each player takes their 4 pegs and 3 floats into their **reserve** (in front
   of them, in the open).
3. Set the slider to **aperture 2**.
4. Youngest player goes first, then clockwise.

A corner node belongs to both edges that touch it. Two players may both enter
there — whoever gets there first.

---

## 4. Your turn

Take **exactly one** of these four actions. There is no "pass"; Crank is always
available.

### A. Crank
Move the slider **one notch**, up or down.

> **Reversal ban.** You may not crank in the direction that exactly undoes the
> crank taken on the previous turn by any player. (If the last crank was 1→2,
> the next crank cannot be 2→1. It may be 2→3, and a Crank after any non-Crank
> turn is unrestricted.)

If you cranked **down**, resolve **the Squeeze** immediately (§5).

### B. Enter
Take a peg from your reserve and place it on an unoccupied node in **your home
line** that is open to that peg.

### C. Swim
Move one of your pegs on the board **one step** to an orthogonally adjacent node
(no diagonals) that is open to that peg and unoccupied.

**Shoulder.** A bull may instead move onto an adjacent node that is open to the
bull and holds an **enemy pup**. The pup is lifted out and returned to its
owner's reserve; the bull takes the node. Bulls cannot shoulder bulls, cannot
shoulder your own pieces, and nothing shoulders a float.

### D. Plant
If one of your **pups** sits on a node where **t = the current aperture** (a tight
node), take the pup back into your reserve and set one of your **floats** in that
node.

That node is **claimed**. It is blocked to every piece for the rest of the game,
it never squeezes out, and it counts as a point for you.

Bulls never plant. A pup on a node where the aperture is *above* the threshold is
swimming, not gripping — it must wait for the ice to come back to it, or move.

---

## 5. The Squeeze

Whenever the aperture drops one notch, the holes shrink on that click and the
cones are pushed up out of anything too small for them. Resolve it physically,
right then:

> **Every peg standing on a node that is no longer open to it is ejected** —
> lifted off and returned to its owner's reserve. Floats stay.

The board does this for you: after a downward click, sweep a finger across the
sheet, and every peg that has risen is out. Bulls go first and go often — a bull
sits in a hole one size larger than a pup needs.

A crank down to **aperture 0** shuts the whole sheet and ejects **every peg on the
board**, including your own. It is legal, it is sometimes correct, and it is the
one move that can undo a table full of position at once.

---

## 6. Winning

- **2 players:** first to plant **3 floats** wins, immediately.
- **3 or 4 players:** first to plant **2 floats** wins, immediately.

**Long-game stop.** If sixty turns pass in total with no float planted at all, the
ice has won: the player with the most floats takes it, tie broken by most pegs on
the board, then by fewest pegs in reserve, then the game is a draw between those
tied. (In play this almost never fires — cranking down is too cheap a weapon for
the board to stay quiet.)

---

## 7. Worked opening

Aperture 2. North enters a pup on **B1** (t = 1). B1 is open to pups at A ≥ 1, so
the pup drops in — but it is not tight, so North cannot plant yet.

South cranks **down to 1**. Squeeze: at aperture 1 a bull needs a threshold-0 node
and there is no such thing, so every bull on the board would be ejected — none are
out yet, so nothing happens. But North's pup on B1 is now at **A = t = 1**. Tight.

East, seeing it, cranks — but cannot crank **up** to 2? They can: the reversal ban
only blocks undoing the *previous* crank, and the previous crank was 2→1, so 1→2
is exactly the reversal. It is banned. East must crank **down to 0** (shutting the
whole sheet and ejecting North's pup) or do something else entirely.

East cranks to **0**. The ice shuts. North's pup is ejected to reserve. Nobody has
planted; everyone starts from an empty board with the aperture at the bottom, and
North has learned to plant on the turn they earn the tight node, not one turn
later.

---

## 8. Notes for the table

- **The slider is the real board.** Pegs are cheap — they come back. The aperture
  is the only thing all four players share, and the reversal ban means whoever
  cranks last hands the next player a direction they cannot take back.
- **Threshold-3 nodes are pup country.** No bull can ever stand there. If you want
  a quiet corner to plant in, that is where it is — but planting there needs the
  aperture wide open, which is the state everybody else also wants.
- **Threshold-1 nodes are the knife.** They are claimable at aperture 1, one notch
  above shut, and at aperture 1 almost nothing else on the board survives.
- **Bulls do not score. Bulls decide who scores.** Two bulls parked on your
  opponent's tight nodes cost them a full lap of the aperture.
- **Count the notches before you commit a pup.** Getting a pup to a node is easy.
  Getting the aperture to sit exactly on that node's number, on your turn, with
  three other people holding the slider, is the game.
