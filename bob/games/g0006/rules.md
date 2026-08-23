# FOLD LINE

*A race across a map that anyone at the table can bend out from under you.*

2–4 players · 20–30 minutes · ages 14+

---

## 1. Overview

Fold Line is a race on a map made of six square plates joined in a row by five
stiff hinges. Each player has one runner that walks from plate to plate, must
reach the three shrines named on their quest tile, and must get back to the
plate it started on. That part is an ordinary route game — a pawn, a connected
map, a list of places to visit.

The map is not ordinary. A hinge clicks between two settings: **flat**, where
its two plates lie edge to edge and a runner can walk across, and **bent**,
where the two plates stand at a right angle and the seam becomes a cliff no
runner can cross. Bend three hinges in a row and the four plates close into a
square box — and where the box shuts, two keyed posts on one plate snap into
two sockets on a plate three positions away. That click is a bridge. Two plates
that were far apart are now next to each other, and the plates walled up inside
the box are cut off from everything else.

Any player can do this, to any hinge, on their turn. The feeling the game is
after is vertigo: you plan two hops ahead, someone folds, and the plate you are
standing on connects to nothing. You are not sent home. You are just stuck
there until somebody folds it back.

Folding is not free. Each fold costs one **brace** from your own supply of
five, and the brace drops into that hinge's **well**. A hinge whose well holds
three braces is **jammed** for the rest of the game — whoever spent the third
brace has frozen that part of the world in the shape they chose. The map can
therefore change at most fifteen times, ever. It settles, and then it is a
footrace.

**First runner to stand on its own home plate with all three of its shrines
claimed wins.**

---

## 2. Components bill

Everything is a printed plastic part. Plate numbers 1–6 are engraved large on
the underside of each plate; hinge numbers 1–5 are engraved on each hinge
knuckle.

| id | name | qty | size (mm) | role |
|---|---|---|---|---|
| `plate_01` | Terrain plate 1 — Shrine 1 | 1 | 100 × 100 × 12 | Ribbed shell, 2.5 mm walls. Numeral **1** in raised relief at centre of the top face = Shrine 1. Runner socket ⌀10 × 10 at (50, 20) in the top face; home-marker hole ⌀6 × 8 at (50, 80). Left and right edges mitred 45° from the top face. **Clasp posts**, keyed triangle, 12 × 12 × 10 with 0.2 mm interference, on the LEFT mitre at y = 20 and y = 80. Side faces carry hinge-knuckle clip holes on the right end only. |
| `plate_02` | Terrain plate 2 — Shrine 2 | 1 | 100 × 100 × 12 | As plate 1. Relief numeral **2** = Shrine 2. Clasp posts keyed **square** on the LEFT mitre. Hinge clip holes at both ends. |
| `plate_03` | Terrain plate 3 — no shrine | 1 | 100 × 100 × 12 | As plate 2, blank top face. Clasp posts keyed **round** (⌀12 × 10) on the LEFT mitre. |
| `plate_04` | Terrain plate 4 — Shrine 4 | 1 | 100 × 100 × 12 | Relief numeral **4** = Shrine 4. **Clasp sockets**, keyed triangle, 12.2 × 12.2 × 11, on the RIGHT mitre at y = 20 and y = 80, each rimmed with an engraved triangle. Left mitre plain. Hinge clip holes at both ends. |
| `plate_05` | Terrain plate 5 — no shrine | 1 | 100 × 100 × 12 | Blank top face. Clasp sockets keyed **square** on the RIGHT mitre, rims engraved square. |
| `plate_06` | Terrain plate 6 — Shrine 6 | 1 | 100 × 100 × 12 | Relief numeral **6** = Shrine 6. Clasp sockets keyed **round** on the RIGHT mitre, rims engraved round. Hinge clip holes at the left end only. |
| `hinge_01` | **Detent hinge knuckle (front) — SIGNATURE PART** | 5 | 62 × 16 × 16 | The whole game. Two leaves and a barrel; each leaf clips to the side face of one plate so the barrel axis lies on the plane of the plates' top faces, **outboard of the 100 mm plate width** — so the plate edges themselves stay completely clear for clasps. Hard detents at 0° (flat) and 90° (bent) and nothing in between, stiff enough to hold a 100 mm plate upright against its own weight without creeping. The left leaf carries the **well**: three ⌀8.2 × 14 sockets in a row on its outer face. |
| `hinge_02` | Detent hinge knuckle (rear) | 5 | 62 × 16 × 16 | Identical to `hinge_01` without the well. One per seam, on the far side of the strip. Two knuckles per seam make one hinge. |
| `pin_01` | Hinge detent pin | 10 | ⌀5 × 18 | One per knuckle. Presses into the barrel, carries the detent cam, meant to stay in. |
| `runner_01` | Runner | 4 | ⌀14 × 32 | One per player, four colours. A ⌀9.8 × 10 foot peg plugs into a plate's runner socket, leaving **22 mm standing above the plate**, so four runners still clear one another when four plates close into a box. Friction fit holds it when its plate stands on edge or hangs upside down. |
| `brace_01` | Brace | 20 | ⌀8 × 18 | Five per player, in player colour. Spent to fold; dropped into a hinge well, standing 4 mm proud so a full well is obvious across the table. |
| `peg_01` | Claim peg | 12 | ⌀6 × 14 | Three per player, in player colour. Plugged into your quest tile when your runner reaches a shrine. |
| `home_01` | Home marker | 4 | ⌀14 × 10 | One per player, in player colour. ⌀6 stem plugs into a plate's home-marker hole to show whose home that plate is. |
| `quest_01` | Quest tile | 4 | 70 × 40 × 5 | Four different tiles, each naming three of the four shrine numbers, each numeral beside a ⌀6.2 × 8 peg hole. Tile A: 1, 2, 4. Tile B: 1, 2, 6. Tile C: 1, 4, 6. Tile D: 2, 4, 6. |
| `track_01` | Round track | 1 | 180 × 30 × 8 | Sixteen ⌀8.2 notches numbered 1–16. |
| `marker_01` | Round marker | 1 | ⌀8 × 16 | Sits in the round track. |

72 parts. Largest part is 180 mm; everything prints on a 256 mm bed.

**How the strip is built (once, out of the box).** Lay the plates in a row in
order 1–6, shrine faces up, engraved numerals underneath reading left to right.
At each seam clip one `hinge_01` (well side) onto the near side faces of the
two plates and one `hinge_02` onto the far side faces, and press a pin into
each barrel. That is hinge 1 between plates 1 and 2, hinge 2 between plates 2
and 3, and so on to hinge 5 between plates 5 and 6. The strip only assembles
one way: clasp **posts** live on the left mitres of plates 1, 2 and 3, and
clasp **sockets** on the right mitres of plates 4, 5 and 6. Leave the strip
assembled between games.

**Which way a hinge bends.** Every hinge bends the same way and only that way:
the two shrine faces rotate **toward** each other, so the strip curls upward
off the table. A bent hinge is at a hard 90° stop; there is no other angle. A
closed box therefore has its shrine faces on the inside, and runners stand
inside the box, in plain view from either open end.

---

## 3. Setup

1. Lay the strip flat on the table with plate 1 on the left and plate 6 on the
   right. Click **every hinge to flat (0°)**.
2. Each player takes a colour and its parts: 1 runner, 5 braces, 3 claim pegs,
   1 home marker. Braces sit in front of you, in the open, all game.
3. Shuffle the four quest tiles face down. Deal one **face up** to each player
   and return the unused tiles to the box unseen. Your tile names the three
   shrines you must reach; the fourth shrine is nothing to you.
4. **Turn order:** the youngest player goes first, then clockwise.
5. **Homes, in REVERSE turn order** — the last player in turn order chooses
   first and the first player chooses last. On your choice, plug your runner
   into any plate that holds no runner, and plug your home marker into that
   same plate's home-marker hole. That plate is your **home** for the whole
   game and it never changes. Two players may not choose the same plate. (This
   reversal is the compensation for going later: the first player moves first,
   but takes whatever plate is left.)
6. If the plate you started on carries a shrine that is on your tile, plug a
   claim peg into that numeral's hole right now.
7. Put the round marker in notch 1 of the round track. The first player takes
   the first turn.

---

## 4. Turn structure

Play goes clockwise. **On your turn you take exactly one action: Step or
Fold.** There are no phases and no other choices. The turn passes the moment
your action is finished.

Taking an action is **mandatory**. If a legal Step exists you may take it; if a
legal Fold exists you may take it; you choose between them freely. Only if
**neither** is legal for you do you **pass**, and the turn passes.

A **round** is one turn by every player. When the last player in turn order
finishes their turn, advance the round marker one notch. **If the marker would
leave notch 16, the game ends instead and is scored** (section 6B).

---

## 5. Actions

### 5.1 What "connected" means

Everything in this game hangs on which plates are connected right now. There
are exactly two ways, and no others.

**A. Along the strip.** Two neighbouring plates are connected if the hinge
between them is **flat**. If that hinge is **bent**, they are not connected —
the seam is a cliff.

**B. Across a clasp.** Three specific pairs of plates can clasp. Each clasp
exists exactly when its three hinges are all bent:

| Clasp | Key | Exists when | What happens |
|---|---|---|---|
| plates **1 ↔ 4** | triangle | hinges 1, 2, 3 all bent | plates 1, 2, 3, 4 close into a box; plate 1's posts snap into plate 4's sockets |
| plates **2 ↔ 5** | square | hinges 2, 3, 4 all bent | plates 2, 3, 4, 5 close into a box; plate 2's posts snap into plate 5's sockets |
| plates **3 ↔ 6** | round | hinges 3, 4, 5 all bent | plates 3, 4, 5, 6 close into a box; plate 3's posts snap into plate 6's sockets |

Distance along the strip means nothing on its own. Only hinges and clasps.

The click you hear when a clasp seats is the confirmation, but the *rule* is
the hinge settings: if the three hinges of a clasp are bent, that clasp is a
connection, full stop. If it will not physically seat, see section 8.

**The collision rule: four hinges in a row may never all be bent at the same
time.** The strip would run into itself. This is a hard limit on what you may
fold, and it means **at most one clasp can exist at any moment**.

A plate with no connection at all is **stranded**. A runner on a stranded plate
cannot Step. It stays where it is — not sent home, not removed, simply stuck
until the map changes.

### 5.2 Action: Step

Move your runner from its plate to any plate **connected** to it (section 5.1).
One plate per Step. You may not Step to an unconnected plate, and you may not
Step and stay put.

**If the target plate already holds another player's runner, the two runners
swap plates.** Your runner ends on the target; theirs ends on the plate you
just left. Swapping is always legal and can never be refused. It is not a turn
for that player and it does not use their action.

Then, for **every** runner that moved (yours, and any runner you swapped): if
that runner is now on a plate whose shrine number appears on its owner's quest
tile and that shrine is not yet claimed, its owner plugs a claim peg into that
numeral's hole immediately. A claimed shrine stays claimed for the rest of the
game, even if that plate is later stranded or never visited again.

*Physical rulings.* A runner is either plugged into a plate's runner socket or
in your hand mid-Step; there is no in-between. If a runner is knocked loose or
falls out, plug it back into the plate it was on. If you lift a runner and then
find you cannot legally place it, put it back where it was and take a different
action — nothing has happened.

### 5.3 Action: Fold

Take one brace from your supply, drop it into the **well** of one hinge, then
click that hinge to its **other** setting — flat becomes bent, bent becomes
flat. One hinge, one brace, one click.

You may **not** Fold a hinge if:

- that hinge's well already holds **three braces** — the hinge is **jammed**
  and can never be folded again by anyone; or
- you have no braces left; or
- the fold would put **four hinges in a row** all bent (the collision rule).

You may Fold a hinge no matter who is standing where. Runners do not protect
hinges and hinges do not protect runners. A fold that strands somebody —
including you — is a completely legal move.

*Physical rulings.* A hinge is at a detent or it is not: click it all the way
over. If you have dropped the brace and then find the fold was illegal, take
the brace back and choose again; the fold never happened. If a hinge will not
hold its detent, see section 8. If the folded strip topples or slides on the
table, stand it back up without changing a single detent — the *shape* of the
strip is the map; its pose on the table is not.

**Because of the wells, the map can change at most 5 × 3 = 15 times in the
whole game.** When every hinge is jammed, or when no player has a brace left,
the map is **frozen** and nobody can ever change it again.

---

## 6. End & winning

The game ends the instant one of these happens.

**A. Somebody gets home.** The moment a runner stands on its owner's home plate
with all three claim pegs plugged into that owner's quest tile, that player
wins immediately. This can happen on that player's own Step, or because
somebody else's Step swapped their runner onto their home. Check for it the
moment any runner lands anywhere.

**B. Round 16 ends.** If the round marker would leave notch 16 with nobody
home, the game ends at once and is scored:

1. Most **claim pegs** on your quest tile wins.
2. If tied: **fewest Steps from your runner's plate to your home plate** along
   the connections that exist right now. Count the shortest route, ignoring
   where other runners are standing (a swap is a normal Step). A player whose
   home cannot be reached at all places below every player whose home can.
3. If still tied: **most braces still unspent in your supply.**
4. If still tied: the player **latest in turn order** wins.

Nothing else ends the game. A player who is stranded and out of braces simply
passes every turn until one of the two endings arrives.

**Why this ends.** Folds are capped at fifteen for the whole table, so the map
provably settles. Steps never stall anyone out, because a runner cannot block a
plate — arriving swaps. And even if every runner ends up stranded on a frozen
map with no braces left, round 16 arrives and the game is scored. There is no
position from which play continues forever.

**Worked scoring example (ending B).** Four players. Ama has 3 pegs but her
runner sits on plate 5 and her home is plate 1; hinges 1, 2 and 3 are bent, so
the live map is 1 ↔ 4 (clasp), 4–5, 5–6, with plates 2 and 3 stranded inside
the box. Ama's route home is 5 → 4 → 1: **2 Steps**. Ben also has 3 pegs; his
runner is on plate 6 and his home is plate 4, so 6 → 5 → 4: **2 Steps**. Cy has
3 pegs but his home is plate 2, which is stranded: **unreachable**. Dai has 2
pegs. Dai is out on rule 1. Cy loses to Ama and Ben on rule 2. Ama and Ben are
still tied, so rule 3: Ama holds 1 brace, Ben holds 0. **Ama wins.**

---

## 7. Tiebreak

The list in section 6B *is* the tiebreak, and it is a total order: claim pegs,
then Steps home, then unspent braces, then turn-order position. Turn-order
position is unique to each player, so exactly one player always wins. **There
is no shared victory in this game.**

Ending A cannot produce a tie except in one case, ruled in section 8.

---

## 8. Edge cases

**Two players finish on the same action.** Your Step swaps a rival's runner
onto their home and completes their three pegs, and the same Step lands you on
your own home with your three pegs. **The active player wins** — your action
resolves for you first.

**Your home plate is stranded.** Nothing special happens. You cannot finish
until someone folds it back into the map. If nobody ever does, you are scored
under 6B with an unreachable home.

**You are stranded.** You must Fold if a legal Fold is open to you; that is
your only action. If you have no braces, or every fold is jammed or blocked by
the collision rule, you pass. You stay on that plate. You are never sent home,
never removed, and you keep every claim peg you already have.

**A stranded runner cannot be swapped with.** Swapping happens only as part of
a legal Step, and a legal Step needs a connection. If a plate is stranded,
nobody can reach the runner on it.

**Someone camps on my home.** They cannot block it. When you Step onto your
home you swap them off it.

**Somebody swaps me onto a shrine I need.** You claim it. Claiming triggers for
any runner that moves, for any reason, on anybody's turn.

**Somebody swaps me off a plate I wanted.** That is the game. There is no
compensation and no reaction.

**Two claims at once.** A single Step can move two runners onto shrines. Both
owners claim. Order does not matter — they are different plates.

**Runners inside a closed box.** All four runners can end up inside one closed
box. They stand 22 mm proud on plates 100 mm apart, so they clear each other
and clear the opposite wall. Reach in from either open end of the box to move
them. If a box is too tight for your fingers, unclip nothing and fold nothing —
tip the whole strip on its end and work from the open face.

**The clasp will not seat.** If the three hinges of a clasp are all bent, the
connection exists by rule whether or not the posts have clicked home. Ease the
strip square and press the seam; it is meant to take a firm push. If it still
will not seat, the plates are in the wrong order — posts belong on the left
mitres of plates 1, 2 and 3, sockets on the right mitres of plates 4, 5 and 6,
and the two keys at a seam must match (triangle with triangle, square with
square, round with round).

**A hinge that will not hold its detent.** Prop the plate with anything to hand
and play on: the hinge's *setting* is what the rules read, not whether it sags.
Replace that knuckle before the next game.

**A hinge well is full.** That hinge is jammed forever and holds whatever
setting it was left in. Nobody may fold it — not to flat, not to bent, not even
if every runner on the table is stranded because of it. Announce a jam out loud
when you cause one; it is the most decisive move in the game. Note that five
braces is one short of jamming two hinges, so **no single player can lock two
seams alone** — it takes a second player choosing to help.

**No braces left.** You may only Step, or pass if you cannot Step. You cannot
borrow, trade, or take braces back out of a well. Spent is spent.

**Every hinge jammed, or every brace spent.** The map is frozen. Play continues
as a pure race until somebody gets home or round 16 ends.

**Attempting a fourth bent hinge in a row.** Illegal. Not "allowed with a
penalty" — the action cannot be taken and you must do something else.

**Can two plates be connected twice?** No. A clasp always joins plates three
apart; a hinge always joins plates one apart. They never overlap, so there is
never a doubled or contested connection.

**Can two clasps exist at once?** No. Any two clasps would need four bent
hinges in a row, which the collision rule forbids.

**A plate that is both a shrine and somebody's home.** Perfectly normal. Plates
1, 2, 4 and 6 can each be somebody's home and still be a shrine for anyone
whose tile lists it, including that player — who claims it at setup, step 6.

**Fewer than four players.** Deal only as many quest tiles as there are
players, chosen at random from the four, and return the rest to the box unseen.
Everything else — six plates, five hinges, five braces each, sixteen rounds,
homes in reverse turn order — is unchanged. At two players the whole table
holds only ten braces, so the map settles early and the game is more puzzle
than brawl; at four players it is the fifteen-fold cap that ends the folding,
and somebody will be left holding braces they can never spend.

**How long this really takes.** A finished route is six to ten Steps plus three
to five Folds, so eleven to fifteen turns per player. Two players: about
twenty-six turns, fifteen to twenty minutes including the teach. Four players:
about fifty turns, twenty-five to thirty minutes. The sixteen-round cap is a
backstop, not a target — at four players it allows sixty-four turns, well more
than a finished game needs.
