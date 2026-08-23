# Armillary — build brief

One board (`plinth_ring`), three identical-profile rotating masks
(`mask_disc_a/b/c`), three identical-geometry tile families
(`star_tile`/`moon_tile`/`void_tile`, 30 tiles total), a tile silo
(`reserve_column`), and four player racks (`score_rail`). Everything fits the
246 x 246 x 251mm bed as a single tile each — nothing needs splitting.

## The one rule that overrides everything else here

`star_tile`, `moon_tile` and `void_tile` share **one** geometry: 22mm round,
6mm thick, a 10mm-diameter/9mm-tall knurled knob centred on the back — bit
for bit identical outline, thickness, rim and back across all three
families. The only geometry that is allowed to differ is the 1.2mm relief
carved into the face that lies face-down against the well floor (star,
crescent, or eclipse). No other feature — chamfer, weight, texture, print
orientation — may diverge, because the whole hidden-information mechanic
depends on a face-down tile being unidentifiable by feel, sound or silhouette
until someone turns it over. This brief does not touch that constraint; it
only carries it through into three part entries with identical `bbox_mm`.

## Parts

### `plinth_ring` (qty 1, board, 216mm dia x 70mm tall)

A 216mm-diameter, 30mm-tall drum with a chamfered skirt, plus a central
24mm-diameter axle post rising a further 40mm from the top face (30 + 40 =
70mm combined bbox height — idea.json states these as two separate numbers;
I summed them, see Unstated below).

Owns three numbers everything else derives from: **well diameter 24mm**,
**well depth 6mm**, **axle diameter 24mm**. Ten wells on an 80mm-radius ring
at 36deg spacing, each with a thumb scallop (use `blocks.cut_wells`, which
defaults to exactly this). Wells at index 0, 4 and 7 carry a 1.2mm raised
sunburst collar marking them zenith wells. Rim carries ten 1.2mm index
grooves; top face carries 1.2mm constellation relief.

A mechanical note for the builder, not a dimension change: the 6mm well
depth puts a seated tile's flat top face flush with the ledge the mask discs
rest on, so a resting tile's 9mm knob rises 3mm past what a single 6mm-thick
mask disc can clear locally when un-aligned. Cut a shallow (~3mm) relief
undercut into the underside of `mask_disc_a` along the window-track annulus
(outside the through-windows themselves, which already clear it) so a
resting knob never fouls a rotating disc. Well diameter, well depth, tile
height and axle length are unchanged by this.

Prints skirt-down; wells and axle post are both plain vertical features from
the flat top face (pockets, one upstanding cylinder) — no overhangs, no
supports.

### `mask_disc_a` / `mask_disc_b` / `mask_disc_c` (qty 1 each, loose_piece, 232 x 216 x 9mm)

Three discs sharing one 216mm/6mm(9mm rim band)/25mm-bore profile, told apart
only by grip-tab shape (paddle / fin / double-prong, each projecting 16mm
past the rim — the source of the 232mm bbox x-extent, 216+16, a sum idea.json
never states directly). 25mm centre bore rides `plinth_ring`'s 24mm axle —
0.5mm clearance per side, derived from the axle diameter the plinth owns,
never restated per disc. Six 38mm windows each, on the same 80mm-radius ring
plinth's wells use, at index sets {0,1,2,3,4,6} / {0,1,2,3,6,7} /
{0,1,3,5,6,8} — generate that ring's position list once and reuse it for the
wells and all three window sets (see Print plan).

Print flat, rim-down, windows as plain vertical through-holes — no supports.

### `star_tile` / `moon_tile` / `void_tile` (qty 12 / 10 / 8, loose_piece, 22 x 22 x 15mm)

22mm round, 6mm thick, 10mm-dia/9mm-tall knurled knob on the back, 15mm total
resting height (6mm body + 9mm knob). Face carries a 1.2mm raised star,
crescent, or eclipse — the only difference between the three families. Fits
`plinth_ring`'s 24mm/6mm-deep wells with 1.0mm clearance per side and 9mm of
knob standing proud above the rim (the intended pinch point).

Print relief-face DOWN, knob UP — the tile's actual resting/game orientation,
not a print-specific one, so the print process leaves no tell distinguishing
one family from another before it's turned face-up.

### `reserve_column` (qty 1, container, 70 x 70 x 150mm)

Square obelisk, 150mm tall, tapering from a 70mm base to a 46mm shaft
(bbox_mm uses the wider 70mm figure for both x/y, conservative — idea.json
doesn't state which end is which). 24mm bore holds tiles stacked knob-up,
deriving its clearance from the same 22mm tile diameter the plinth's wells
use. A 9mm-wide slot runs the full 150mm height down one face: a visible
game-clock and a finger-access channel at any stack depth, not just the top
mouth — which is why retrieval here isn't a straight top-down pinch and this
part carries no `recesses` block (see Interfaces).

Prints standing on its 70mm base, tapering ~9deg to the 46mm shaft —
self-supporting; the bore is an open channel (the side slot removes the
enclosed roof), no internal supports.

### `score_rail` (qty 4, container, 130 x 30 x 20mm)

One per seat. Two parallel 6.6mm-wide, 11mm-deep slots stand tiles ON EDGE: a
plain front slot and a raised rear (zenith) slot carrying the 1.2mm sunburst
motif. A standing tile presents its 6mm body to the 6.6mm slot (0.3mm
clearance per side — tight, inherited unchanged from idea.json's own stated
6.6mm, see Unstated) and its 22mm diameter sinks 11mm into the slot (half
buried, 11mm proud). Four end-finials (triangular/square/pentagonal/hexagonal
prism) tell the four rails apart by seat, within the stated 130mm length.

Prints flat on the 130x30 face, slots open upward as plain vertical pockets
— no supports.

## Interfaces

1. **`star_tile` seats into `plinth_ring`** (representative for all three
   tile families — identical bbox). Board owns 24mm well diameter / 6mm well
   depth; tile's 22mm diameter derives its 1.0mm/side clearance from that.
   Runs through `ergonomics_check`'s `recesses` formula directly (tile sits
   flat, its primary orientation) — this is the pairing the gate actually
   checks.

2. **`star_tile` seats into `reserve_column`** (representative). Bore
   diameter (24mm) derives from the same 22mm tile diameter. Deliberately
   **not** an ergonomics `recesses` entry: the check assumes a single
   top-down pocket, but retrieval here is via the chamfered top mouth *plus*
   a full-height side slot reaching the stack at any depth — the worst case
   (last tile, bottom of a full column) is reachable from the side, not by a
   straight pinch down the bore, which the formula can't represent.

3. **`star_tile` seats into `score_rail`** (representative for star/moon —
   void is never banked). Tile stands on edge: 6mm body into 6.6mm slot width
   (0.3mm/side, tighter than this pipeline's usual 0.4mm minimum — kept as
   idea.json states it, flagged rather than silently widened); 22mm diameter
   into 11mm slot depth (half buried, 11mm proud). Applies identically to
   both slots (front and raised rear). Not an ergonomics `recesses` entry:
   standing-on-edge isn't the tile's primary table-resting bbox the formula
   assumes.

4. **`mask_disc_a`/`b`/`c` join `plinth_ring`**. One shared 25mm bore riding
   the plinth's 24mm axle, 0.5mm/side clearance, loose rotating fit. 3 discs
   x 6mm bore-region thickness = 18mm of the axle's 40mm length engaged,
   leaving 22mm exposed above the top disc with no stated retaining cap —
   none added; held by gravity and the snug bore fit.

5. **`mask_disc_a`/`b`/`c` stack** on `plinth_ring`'s outer rim ledge, a then
   b then c. Max 3, on a 216mm-diameter footprint against a 27mm combined
   stack height — far too wide to topple.

## Print plan

- `min_wall_mm`: 1.6
- No part exceeds the 246 x 246 x 251mm bed. Largest footprint: 232mm
  (`mask_disc_*`, rim + grip-tab). Tallest: 70mm (`plinth_ring`, drum +
  axle). Every part is a single tile — no dovetail joins needed anywhere.
- No supports anywhere: every part's stated print orientation (above, per
  part) is self-supporting — pockets and straight vertical cylinders on
  `plinth_ring`, plain through-holes on the discs, relief-face-down/knob-up
  tiles, a gently-tapering `reserve_column` with an open-channel bore, and a
  flat-printed `score_rail`.
- Use `blocks.cut_wells` directly for `plinth_ring`'s ten wells (default
  thumb-scallop cutter matches idea.json's stated scallop).
- The ten-position, 80mm-radius, 36deg ring that both `plinth_ring`'s wells
  and all three discs' window sets are drawn from must be generated **once**
  and reused for all four cuts plus the plinth's index grooves and each
  disc's witness notch — the `shared_positions` lesson. Note `blocks.py`'s
  `shared_positions` itself is a rectangular cols x rows x pitch grid
  generator, not a radial one, so this needs an equivalent hand-rolled
  "generate once, reuse everywhere" radial list rather than a literal call to
  that block.
- `seated_pair` is not used for the tile/well fit: idea.json already states
  both the 24mm well and the 22mm tile as fixed numbers, not one derived from
  the other by a default clearance formula; recomputing either through
  `seated_pair`'s free-fit default (22.8mm) would silently override a stated
  dimension.

## Unstated in spec

See `brief.json`'s `unstated_in_spec` array for the authoritative list; in
short:

1. `plinth_ring`'s 70mm total height is my sum of two numbers idea.json
   states separately (30mm drum + 40mm axle rise) and never combines.
2. The well-floor / ledge relationship admits more than one reading; I took
   the well's stated 6mm depth as the same 6mm step idea.json describes
   relative to the ledge (not a second, unstated nested recess), which
   leaves a small (~3mm) knob/disc interference I flag as a relief-undercut
   fix rather than silently deepening the well or shrinking the knob.
3. `mask_disc_*`'s 232mm bbox x-extent is a direct sum (216 + 16mm tab) of
   two separately-stated numbers, not itself a stated figure — and it's the
   number the 246mm bed-fit check actually depends on.
4. No retaining cap is stated for the axle once three discs are stacked on
   it (22mm of axle exposed above the top disc); none invented, held by
   gravity and the bore fit alone.
5. `reserve_column`'s "46mm across a 70mm base" is read as a tapered
   obelisk; I used the wider 70mm figure for both x/y of its bbox as the
   conservative bound.
6. `reserve_column`'s 150mm height and 20-tile capacity don't reconcile
   cleanly against any single stacking pitch idea.json gives (9mm-knob pitch
   needs 180mm; 6mm-body pitch needs 120mm) — flagged unresolved rather than
   picking a pitch that silently changes either stated number.
7. `score_rail`'s stated 6.6mm slot width against a 6mm tile gives 0.3mm
   clearance per side, under this pipeline's usual 0.4mm minimum — kept as
   idea.json states it rather than widened, and flagged.
8. `score_rail`'s slot length / per-tile pitch (accounting for a standing
   tile's sideways knob) isn't stated anywhere; left as a builder-level
   layout detail within the stated 130mm rail length.
9. No scallop width/depth is given for the wells; the well's own clearance
   already clears the retrieval formula without it, so no separate scallop
   dimension is asserted — carve it via `blocks.cut_wells`'s default.
