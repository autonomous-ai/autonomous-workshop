Verdict: FAIL A tile seated knob-up in a well stands 9mm proud of the plinth's top face while the bottom mask's underside clears only 3mm, so every knob not currently under a `mask_disc_a` window jams the disc — "TURN THE SKY", the first rule of every turn, cannot be performed on the built object.

# Armillary — playability review

## 1. The blocking finding: the knobs and `mask_disc_a` occupy the same 3mm

Measured from `build/armillary_parts/*.stl`, not from Params:

- `plinth_ring` top face is flat at **z=30** across the whole disc footprint
  (well-ring band r 66–72, outer band r 92–100 and rim r 104–109 all report
  z=30.0). There is **no 6mm recessed well ring** — idea.json's "the well ring
  is recessed 6mm below … the outer rim ledge that the disc stack rests on"
  was not built. Well floors are at z=24.
- A seated knob-up tile: 6mm body fills the 6mm well (top flush at z=30), knob
  occupies **z=30 → 39**.
- `mask_disc_a` rests bottom-at-z=30 on that flat face. Its window-track web,
  after the 3mm undercut, spans **z=33 → 36** at the well radius (radial z
  profile: only z=3 and z=6 vertices for r=10…95, i.e. a 3mm web floating 3mm
  above the disc datum).

So the knob passes clean through the web's whole thickness and stands 3mm
above it. Interference is **6mm**, not zero.

The arithmetic error is visible in `validation.py:63`:

```python
assert p.knob_h - p.well_depth == 3.0, (
    "the ~3mm knob/disc interference the disc_a undercut exists to relieve"
)
```

The knob is not partly buried in the well — the 6mm **body** is. Protrusion
above the plinth face is `tile_thickness + knob_h - well_depth` = 6+9-6 =
**9mm**. The 3mm undercut relieves a third of it.

Consequence in play, turn by turn:

- **Setup** already fails. All ten wells get a tile; `disc_a` has six windows.
  The four covered knobs hold the disc 6mm off its seat, and the whole 27mm
  three-disc stack sits cocked on four plastic pegs.
- **Every turn** then fails at step 1. Rotating `disc_a` one index groove
  drags its 3mm web sideways into 10mm-diameter knobs. It does not turn; it
  shears knobs or lifts.
- `disc_b`/`disc_c` are fine (webs at z=42–45 and 51–54) — but they only ever
  move relative to `disc_a`, and the rules make `disc_a` a legal, and often
  the correct, choice.

There is a second, related seating problem the rules depend on: a **face-up**
tile (after a bust) lies knob-down on the well floor, body top at z=39, i.e.
9mm above the plinth face. Those wells hold face-up tiles for the rest of the
game and are explicitly *not* refilled — so from the first bust onward there
is a permanent 9mm obstruction under the stack. Even with the knob problem
fixed, the BUST rule as written needs the discs to clear a face-up tile, and
they cannot.

## 2. The reserve column cannot hold the reserve

`reserve_column`'s bore measures z=0 → ~147mm. Tiles stack knob-up: a flat
face lands on the 9mm knob below, so the real pitch is **15mm** (13.8mm at
best, if the knob drops into the 1.2mm relief pocket). Capacity is **9–10
tiles**. Setup requires **20** (`column_reserve_tiles = 20`).
`params.py:column_tile_pitch = 6.0` is the body thickness alone and is
physically unreachable — the brief flags this as "unresolved" and the build
shipped it anyway. Half the reserve has no home, REFILL runs dry early, and
the obelisk's read-slot game-clock reads a stack that is only ever half the
game.

## 3. Score rail: the standing tile does not sink 11mm

Standing on edge, the tile's knob points sideways out of a face and the slot
is 6.6mm wide. The knob centre is at the tile centre, 11mm up — exactly the
slot mouth — so the knob's lower half (5mm) fouls the rail top before the tile
is 11mm in. Real insertion is ~6mm, tile stands ~16mm proud, engaged by a
circular segment rather than half its diameter. Workable but wobblier than the
10.95mm figure implies, and per-tile pitch becomes 15mm — 7 tiles per slot,
which is about what a winner banks (sim: 8–12 tiles), so the rail is at
capacity by the end of a good game.

## 4. The rules on their own — playable, but thinner than advertised

Taking `rules_check.py` as given, I ran the aperture combinatorics and a
400-game simulation per player count.

**The aperture math is sound.** Over all 1000 disc positions,
|open wells| distributes {1: 140, 2: 580, 3: 260, 4: 20} — never 0, never >4,
exactly as idea.json claims. The board never jams and never blows open.

**The advertised tactical layer is near-inert.** The pitch is that "the disc
you leave badly turned is the sky the next player has to work with". But the
next player rotates *before* reading. From every state, their best reply is
≥3 open wells in **980 of 1000** states, and in **660 of 1000** you cannot
push their best below 3 no matter which of your 18 moves you take. In the 340
states where you can hold them to 2, it costs you 2–3 of your own open wells
in 320 of them. Denial is a rare, expensive, one-well nudge, not a lever. The
rotation is still a real decision — it sets *your own* reach cap and picks
which zenith wells you touch, with 12–15 distinct open-sets reachable per turn
— but it is a solvable "take the max" visual puzzle, not an attack.

**The push decision is mostly automatic.** With 8 voids in 30 tiles, break-even
catch value is ~4.2 points against an average pull of 1.55. You are capped at
1–4 pulls by the aperture, and 3 pulls average 4.6 points — so "push
everything" is correct on the large majority of turns. The genuine decisions
that survive are ordering ones, and they are real: pull the zenith well
**first** (a zenith bust costs a banked tile whether your catch is empty or
not, so take it while the catch is worth nothing), and take already-face-up
free tiles **last** (they join your catch and are lost with it). Two real
choices a turn, one of them near-solved.

**Length and ending are fine.** No stall: the CLEAR rule is a working valve
and the sim never ran long (max 32 turns of 400 trials). Medians: 2p 18 turns,
3p 26, 4p 27; 1.2–1.8 pulls per turn; ~30% bust rate. At 4p that is ~7 turns
each and lands near the claimed 30 minutes. At 2p it is ~9 turns each and more
like 12–18 minutes — under-length, and with denial inert it plays as two
alternating solitaires linked only by the fact that your spilled catch is
free candy for the one opponent. That is a genuine interaction at 2p, so 2p
works; it is just short.

## 5. Legibility, if the mechanics were fixed

- **Alignment reads perfectly.** An open well is a 38mm hole you can see the
  well floor through, three layers deep. Best thing about the object.
- **Everything else on the board is invisible.** 6–9 of the 10 wells are under
  solid web at all times, so which wells hold dead voids and which hold free
  face-up star/moons is unreadable from any seat. The rules treat that as
  public information (free takes, CLEAR from "any well, open or shut", and the
  "every well holds a face-up tile" end condition), but the object converts it
  into an unaided memory task with no marker anywhere. Recommend index-visible
  state — e.g. voids removed to a visible cairn, or a rim marker per dead well.
- **Tiles are correctly indistinguishable** knob-up, which is the point; and
  the three grip tabs sit at three different heights (0–9 / 9–18 / 18–27mm) so
  a hand finds the right layer without looking. Both good.
- **Handling of the discs will not be pleasant.** The web built at 3mm (not
  the 6mm the art direction calls a minimum) across a 216mm span pierced by
  six 38mm holes, driven by a 16mm tab at the rim, will flex before it
  indexes; combined with 0.5mm/side bore slop on the axle, a "one groove"
  rotation is a wobble-and-eyeball, not a click. Detents or a stiffer web
  would turn 25 rotations a game from a chore into the pleasure the concept
  is selling.

## What would clear this

1. Either sink the well ring 9mm below the disc ledge, or shorten the knob to
   ≤3mm proud, or take the undercut on `disc_a` to 9mm+ (and then also clear
   the 9mm face-up tile, which needs the ledge raised regardless). Fix
   `validation.py:63` to assert `tile_thickness + knob_h - well_depth`.
2. Reserve column: 20 tiles at a real 15mm pitch needs ~300mm of bore, or
   split the reserve, or reduce the tile count.
3. Then re-check the rail's standing-tile insertion against the sideways knob.
