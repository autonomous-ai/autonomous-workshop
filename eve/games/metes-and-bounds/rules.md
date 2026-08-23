# Metes and Bounds

**2–4 players · 15–25 minutes · ages 10+**

One printed folding rule. Nine hinges. Every player bends the same fence.

---

## 1. What the game is

You are surveyors on the same open ground. There is exactly one boundary in
play — a ten-segment printed folding rule anchored to the board. Its shape is
the entire board state.

On your turn you bend the rule at **one hinge**. That one bend swings every
segment past it, so the fence leaves some parcels and wraps others. Then you
drive a stake into a parcel the fence now wraps, and you score for every stake
of yours the fence is wrapping *at that moment*.

The next player bends the fence somewhere else. Your stakes stay where they
are. Your points do not.

The whole game is: build a cluster of stakes that a single bend can wrap, and
leave the fence somewhere the next player can't cheaply bring it back from.

---

## 2. Components

| Part | Count | Notes |
|---|---|---|
| Folding rule | 1 | 10 rigid segments, 9 print-in-place hinges, each hinge clicks into **L / S / R** |
| Survey board | 1 | 7 × 7 grid of **nodes** (36 mm pitch), forming 6 × 6 **parcels** between them |
| Stakes | 24 | 6 per player, each player a distinct printed top glyph |
| Score rail + pegs | 5 | 0–40 track, one peg per player |

**Nodes** are the grid intersections — each has a small socket hole.
**Parcels** are the square cells *between* four nodes — each has a centre dimple
for a stake.

Nodes are lettered **A–G** left to right and numbered **1–7** bottom to top.
A parcel is named by its bottom-left node: parcel **C4** is the square whose
corners are C4, D4, C5, D5.

---

## 3. The rule (the physical part)

The rule is one printed piece. Ten rigid segments, each exactly one node pitch
long, joined by nine hinges. Every hinge has three detent positions and clicks
audibly into each:

- **L** — the next segment turns 90° left
- **S** — the next segment continues straight
- **R** — the next segment turns 90° right

A hinge is always in exactly one of these three. There are no in-between
angles; the detent will not hold one.

The rule's **root end** (the free end of segment 1) drops into a node socket.
That socket and the direction segment 1 points are the rule's **station**.
Station plus nine hinge letters fully describes the fence — nothing else on the
board moves.

The rule traces a path of ten board edges across eleven nodes.

### 3.1 Legal shapes

A rule shape is legal only if:

1. **On the board** — every one of the ten segments lies on a grid edge inside
   the 7 × 7 node field.
2. **Self-avoiding** — the path visits no node twice.

Both are enforced by the plastic. An off-board bend has nothing to rest on; a
self-crossing bend cannot be made flat, because the segments are wider than the
gap they would have to share. If the rule will not lie flat on the board, the
shape is illegal — put it back.

Stakes sit at parcel centres and never block the rule.

---

## 4. Parcels the fence wraps

Every parcel has four sides. A side is "fenced" if a rule segment lies on it.

- A parcel with **2 or more fenced sides** is a **corner lot**.
- A parcel with exactly 1 fenced side is **roadside**.
- A parcel with 0 fenced sides is **open ground**.

Only corner lots matter. A straight run of fence past a parcel is not enough —
the fence has to turn around it.

---

## 5. Setup

1. Put the board between the players.
2. Set every hinge to **S**. Seat the rule's root end in node **D4** (the centre)
   pointing right (toward E4). The rule now runs straight across four nodes,
   off the right edge — which is illegal, so before play begins the starting
   player bends hinges freely (no scoring, no stakes) until the rule is legal
   and entirely on the board. Any legal starting shape is fine.
3. Each player takes 6 stakes of one glyph and puts a scoring peg at 0.
4. Youngest player goes first; play passes to the left.

---

## 6. A turn

On your turn, in this order:

### Step 1 — Move the fence (mandatory)

Do exactly one of:

- **BEND** — change exactly one hinge from its current letter to a different
  letter. Only one hinge; only one change.
- **RESTATION** — lift the rule's root end out of its node socket and drop it
  into any other node socket, facing any of the four directions. Do not change
  any hinge.

The resulting shape must be legal (§3.1). If it is not, the move is not
allowed — undo it and choose another. You may not leave the fence exactly as
it was.

If you have no legal BEND and no legal RESTATION, you pass this step.

### Step 2 — Drive a stake (optional)

If you have stakes left, you may place one in any **empty corner lot**. One
stake per parcel, ever. Stakes are never removed or moved for the rest of the
game.

### Step 3 — Score (mandatory)

Count **your own** stakes that are sitting in corner lots right now. Score
**1 point each**. Advance your peg.

Nobody else scores on your turn. A stake in a roadside parcel or open ground
scores nothing this turn — but it is not lost; a later bend of yours can wrap
it again.

---

## 7. End of the game

The game lasts a fixed number of rounds. A round is one turn for each player.

- **2 players:** 12 rounds
- **3 players:** 9 rounds
- **4 players:** 8 rounds

Use the score rail's round track, or set the unused stakes aside as a counter.
After the last player's turn of the final round, the game ends immediately.
There is no end-of-game scoring — every point was already taken on the turn it
was earned.

**Highest score wins.** Tie-break, in order:

1. Most stakes standing in corner lots at the final position.
2. Most stakes placed.
3. Shared win.

---

## 8. Worked example

Four players. Round 3. The fence currently runs:

```
  D4 → E4 → E5 → F5 → F6 → E6 → E7 → D7 → D6 → C6 → C5
```

Station D4 facing right; hinges read **L R L L S L L R L** from the root.

Corner lots right now: **D4** (sides D4–E4 and D4–D5? no — only one fenced),
so check properly. The turns are at E4, E5, F5, F6, E6, E7, D7, D6, C6.
Each 90° turn fences two sides of the parcel inside the elbow. The elbows at
E5/F5 both bound parcel **E5**; the elbows at F6/E6 both bound parcel **E6**;
the elbows at E7/D7/D6 bound parcel **D6**. So **E5, E6, D6** are corner lots,
and **D6** has three fenced sides.

Dee has a stake in **E6** and a stake in **D5**.

It is Dee's turn. She scores 1 right now if she does nothing useful — only E6
is a corner lot. Instead she changes hinge 1 from **L** to **R**. Segment 2
now swings down instead of up, and the whole tail follows:

```
  D4 → E4 → E3 → D3 → D2 → C2 → C3 → B3 → B4 → C4 → C5
```

Now the elbows at D3/D2/C2 bound parcel **C2**, and the elbows at B3/B4/C4
bound parcel **B3**, and the elbows at C4/C5 plus the segment C4–D4… she checks
parcel **C4**: sides C4–D4 (yes), C4–C5 (yes) — corner lot, and it is empty.

But her stakes at E6 and D5 are now both open ground. She scores **0** this
turn. She drives her third stake into **C4** and passes.

The lesson she learns: her stakes were spread across the board. Three turns
later she has C4, C3 and D5 — a tight cluster the fence can wrap with one
bend — and she starts scoring 2 and 3 a turn while the others chase.

---

## 9. Why one hinge is the whole game

Nine hinges, three positions each: 19 683 shapes, most of them illegal because
the rule would run off the board or cross itself. From any legal shape you can
reach at most 18 others by a single bend, usually far fewer.

That is the pressure. You never get to place the fence where you want it — you
get to place it one hinge away from where the last player left it. A cluster of
stakes near the root end is easy to serve and easy for others to strand,
because a root-side bend swings everything. A cluster near the free end is
served by a cheap tail bend that barely disturbs anyone — but the free end is
also where self-avoidance bites hardest, and a tail that has painted itself
into a corner has no legal bends at all.

RESTATION is the reset when the fence has drifted to the wrong half of the
board. It costs a whole turn's bend and usually a turn's points, and it hands
the next player a fence in a shape you chose — so it is a concession, not a
free move.

---

## 10. Edge cases

- **A hinge change that is legal but pointless is allowed.** You must move the
  fence; you do not have to improve it.
- **Two segments touching at a node is illegal**, not merely discouraged — the
  path is strictly self-avoiding. If both knuckles want the same node, the
  plastic will tell you.
- **A parcel can hold only one stake**, regardless of owner.
- **Corner lots with an opponent's stake are still corner lots** — you just
  can't stake them, and you don't score for them.
- **Running out of stakes is normal.** After your sixth stake you still bend
  every turn and still score your six stakes; the endgame is pure fence-fighting.
- **Passing** (no legal bend, no legal restation) still lets you score Step 3.
  It should almost never happen; RESTATION is legal from nearly every position.
- **Detent drift.** If a hinge no longer clicks firmly, that hinge is worn.
  Play it as printed — a hinge that will not hold a position is treated as
  having only the positions it will hold.

---

## 11. Two-player variant: the closed traverse

For a sharper two-player game, add one rule: **the fence may not visit the same
parcel's interior corner twice** — that is, no parcel may ever have more than
two fenced sides. This bans the tight U-shapes that make cheap triple corner
lots, and turns the game into a long, open traverse across the board. Play 12
rounds as normal.
